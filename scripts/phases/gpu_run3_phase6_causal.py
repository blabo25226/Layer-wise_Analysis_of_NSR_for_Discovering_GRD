"""GPU_RUN3 Phase 6: IOLE, ablation, activation intervention, patching, update sensitivity.

Every analysis runs over a fixed validation panel rather than a single formula,
and each layer effect is reported as a delta against the same panel's baseline.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from gpu_run3.architecture import inventory_ndformer, set_trainable_layers  # noqa: E402
from gpu_run3.cli import (  # noqa: E402
    common_parser,
    dummy_phase_output,
    phase_budget,
    require_previous,
    write_phase_manifest,
)
from gpu_run3.corpus import build_analysis_corpus, corpus_kwargs_from_budget, select_fixed_panel  # noqa: E402
from gpu_run3.interventions import ablate_layer, capture_mean_activation, patch_activation  # noqa: E402
from gpu_run3.ranking import rank_from_scores  # noqa: E402
from gpu_run3.training import (  # noqa: E402
    clone_model,
    evaluate_records,
    parameter_update_norms,
    run_iole_sweep,
    train_policy_multi_problem,
)
from gpu_run3_runtime import (  # noqa: E402
    load_gpu_run3_configs,
    load_ndformer,
    nd2_paths,
    require_python_310,
    resolve_run_dir,
    seed_everything,
    select_device,
    write_json,
)


def parse_args():
    return common_parser("GPU_RUN3 Phase 6 causal layer analysis").parse_args()


def _mean(values) -> float:
    finite = [float(v) for v in values if v is not None and math.isfinite(float(v))]
    return float(sum(finite) / len(finite)) if finite else float("nan")


def _panel_intervention(model, layer_name, panel, *, mode, max_examples, replacement_of=None):
    """Apply one intervention across the whole panel and pool the policy metrics."""
    rows = []
    for row in panel:
        examples = [ex for ex in row["teacher_forcing"] if ex.get("target")][:max_examples]
        if not examples:
            continue
        replacement = None
        if mode == "mean":
            try:
                replacement = capture_mean_activation(model, layer_name, row, examples=examples)
            except Exception as exc:
                rows.append(
                    {
                        "problem_id": row["problem_id"],
                        "module_name": layer_name,
                        "mode": mode,
                        "valid": False,
                        "failure_reason": f"{type(exc).__name__}:{exc}",
                        "cross_entropy": float("nan"),
                    }
                )
                continue
        result = ablate_layer(model, layer_name, examples, row, mode=mode, replacement=replacement)
        rows.append({"problem_id": row["problem_id"], **result})
    return rows


def _pool(rows) -> dict[str, float]:
    valid = [r for r in rows if r.get("valid")]
    return {
        "n_problems": len(rows),
        "n_valid": len(valid),
        "cross_entropy": _mean([r.get("cross_entropy") for r in valid]),
        "top1_accuracy": _mean([r.get("top1_accuracy") for r in valid]),
        "topk_accuracy": _mean([r.get("topk_accuracy") for r in valid]),
        "mean_true_symbol_rank": _mean([r.get("mean_true_symbol_rank") for r in valid]),
        "mean_true_symbol_probability": _mean([r.get("mean_true_symbol_probability") for r in valid]),
        "mean_policy_entropy": _mean([r.get("mean_policy_entropy") for r in valid]),
        "failure_reasons": sorted({str(r.get("failure_reason")) for r in rows if r.get("failure_reason")}),
    }


def main() -> int:
    args = parse_args()
    require_python_310()
    config = load_gpu_run3_configs()
    run_dir = resolve_run_dir(args.run_id, config=config)
    out_dir = run_dir / "phase6"
    out_dir.mkdir(parents=True, exist_ok=True)
    if args.dry_run:
        dummy_phase_output(out_dir, 6, extra={"analyses": ["iole", "ablation", "intervention"]})
        print(f"Phase 6 dry-run: {out_dir}")
        return 0
    require_previous(run_dir, "phase0/preflight.json")
    budget = phase_budget(config, smoke=args.smoke)
    paths = nd2_paths(config)
    device = select_device(allow_cpu=args.allow_cpu)
    model = load_ndformer(paths["checkpoint"], device=device)
    inventory = inventory_ndformer(model)
    layers = inventory["ranking_layers"]
    seed = int(args.seed) or int((config.get("seed_bundles") or [{"data_seed": 101}])[0]["data_seed"])
    seed_everything(seed)
    corpus = build_analysis_corpus(seed=seed, **corpus_kwargs_from_budget(budget))
    train_records = [r for r in corpus["records"] if r["split"] == "analysis_train"]
    panel = select_fixed_panel(corpus["records"], split="analysis_validation", n=int(budget.get("panel_problems", 2)))
    if not train_records or not panel:
        raise RuntimeError(f"empty split: train={len(train_records)} panel={len(panel)}")
    max_examples = int(budget.get("probe_examples", 16))
    iole_steps = int(budget.get("iole_steps", 2))

    # 6A. IOLE single-layer fine-tuning (train on analysis_train, score on the panel).
    iole = run_iole_sweep(
        model,
        layer_names=layers,
        train_records=train_records,
        eval_records=panel,
        steps=iole_steps,
        seed=seed,
        max_examples_per_problem=max_examples,
    )
    write_json(out_dir / "iole.json", iole)
    iole_ce = {row["condition"]: row.get("cross_entropy") for row in iole["results"]}

    # Baseline for every intervention delta: the untouched model on the same panel.
    baseline = evaluate_records(model, panel, max_examples_per_problem=max_examples)
    write_json(out_dir / "baseline_policy.json", baseline)
    base_ce = baseline.get("cross_entropy")
    base_top1 = baseline.get("top1_accuracy")
    base_prob = baseline.get("mean_true_symbol_probability")

    # 6B-6D. Ablation and activation interventions, per layer, over the panel.
    ablation_rows = []
    intervention_rows = []
    layer_effects = {}
    for name in layers:
        effects = {}
        for mode, sink in (("skip", ablation_rows), ("zero", ablation_rows), ("mean", intervention_rows)):
            rows = _panel_intervention(model, name, panel, mode=mode, max_examples=max_examples)
            pooled = _pool(rows)
            record = {"module_name": name, "mode": mode, **pooled, "rows": rows}
            sink.append(record)
            effects[f"delta_ce_{mode}"] = (
                pooled["cross_entropy"] - base_ce if math.isfinite(pooled["cross_entropy"]) else float("nan")
            )
            effects[f"delta_top1_{mode}"] = (
                pooled["top1_accuracy"] - base_top1 if math.isfinite(pooled["top1_accuracy"]) else float("nan")
            )
            effects[f"delta_true_prob_{mode}"] = (
                pooled["mean_true_symbol_probability"] - base_prob
                if math.isfinite(pooled["mean_true_symbol_probability"])
                else float("nan")
            )
        # 6D. Activation patching between two distinct panel problems.
        if len(panel) > 1:
            target = panel[0]
            source = panel[-1]
            target_examples = [ex for ex in target["teacher_forcing"] if ex.get("target")][:max_examples]
            source_examples = [ex for ex in source["teacher_forcing"] if ex.get("target")][:max_examples]
            patched = patch_activation(
                model,
                name,
                source_data=source,
                target_data=target,
                examples=target_examples,
                source_examples=source_examples,
            )
            patched.update({"source_problem_id": source["problem_id"], "target_problem_id": target["problem_id"]})
            intervention_rows.append(patched)
            effects["delta_ce_patch"] = (
                patched.get("cross_entropy", float("nan")) - base_ce
                if patched.get("valid")
                else float("nan")
            )
        layer_effects[name] = effects
    write_json(out_dir / "ablation.json", ablation_rows)
    write_json(out_dir / "intervention.json", intervention_rows)

    # 6E. Parameter update sensitivity under a controlled full fine-tune.
    before = clone_model(model)
    full = clone_model(model)
    set_trainable_layers(full, None, train_all=True)
    full_train = train_policy_multi_problem(full, train_records, steps=iole_steps, seed=seed)
    updates = parameter_update_norms(before, full, layers)
    write_json(out_dir / "update_sensitivity.json", {"updates": updates, "train": full_train})

    summary = {
        "phase": 6,
        "status": "complete",
        "provenance": "layer_analysis",
        "seed": seed,
        "ranking_layers": layers,
        "n_train_problems": len(train_records),
        "n_panel_problems": len(panel),
        "panel_problem_ids": [row["problem_id"] for row in panel],
        "baseline": {k: v for k, v in baseline.items() if k != "per_problem"},
        "iole_ce": iole_ce,
        "iole_rank": rank_from_scores(
            {
                row["condition"]: row.get("cross_entropy", float("nan"))
                for row in iole["results"]
                if row["condition"] not in {"frozen", "full"}
            },
            higher_is_better=False,
        ),
        "layer_effects": layer_effects,
        "ablation_rank": rank_from_scores(
            {name: effects.get("delta_ce_skip", float("nan")) for name, effects in layer_effects.items()},
            higher_is_better=True,
        ),
        "intervention_rank": rank_from_scores(
            {name: effects.get("delta_ce_mean", float("nan")) for name, effects in layer_effects.items()},
            higher_is_better=True,
        ),
        "update_sensitivity_rank": rank_from_scores(
            {name: stats.get("relative_l2", float("nan")) for name, stats in updates.items()},
            higher_is_better=True,
        ),
        "update_sensitivity": updates,
        "interpretation_note": (
            "probe = linearly readable, ablation/skip = required, mean intervention = "
            "causally sensitive, IOLE = adaptable. These are reported separately and "
            "not merged into one 'importance' number."
        ),
    }
    write_json(out_dir / "summary.json", summary)
    write_phase_manifest(out_dir, {k: v for k, v in summary.items() if k != "layer_effects"})
    print(f"Phase 6 complete: {out_dir / 'summary.json'} (panel={len(panel)}, layers={len(layers)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
