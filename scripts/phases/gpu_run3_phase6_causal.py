"""GPU_RUN3 Phase 6: IOLE, ablation, activation intervention, patching, update sensitivity."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from gpu_run3.architecture import inventory_ndformer  # noqa: E402
from gpu_run3.cli import common_parser, dummy_phase_output, phase_budget, require_previous, write_phase_manifest  # noqa: E402
from gpu_run3.corpus import build_analysis_corpus  # noqa: E402
from gpu_run3.interventions import ablate_layer, baseline_policy_metrics, capture_mean_activation, patch_activation  # noqa: E402
from gpu_run3.ranking import rank_from_scores  # noqa: E402
from gpu_run3.training import clone_model, parameter_update_norms, run_iole_sweep, train_policy_steps  # noqa: E402
from gpu_run3.architecture import set_trainable_layers  # noqa: E402
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
    seed_everything(args.seed)
    budget = phase_budget(config, smoke=args.smoke)
    paths = nd2_paths(config)
    device = select_device(allow_cpu=args.allow_cpu)
    model = load_ndformer(paths["checkpoint"], device=device)
    inventory = inventory_ndformer(model)
    layers = inventory["ranking_layers"]
    corpus = build_analysis_corpus(seed=args.seed)
    records = [row for row in corpus["records"] if row["split"] == "analysis_train"]
    val_records = [row for row in corpus["records"] if row["split"] == "analysis_validation"]
    if args.smoke:
        records = records[:1]
        val_records = val_records[:1]
        layers = layers[:2]
    train_row = records[0]
    val_row = val_records[0] if val_records else train_row
    examples = [ex for ex in train_row["teacher_forcing"] if ex.get("target")]
    val_examples = [ex for ex in val_row["teacher_forcing"] if ex.get("target")]
    data = train_row
    val_data = val_row
    iole = run_iole_sweep(model, layer_names=layers, examples=examples, data=data, steps=int(budget.get("iole_steps", 2)))
    write_json(out_dir / "iole.json", iole)
    iole_ce = {row["condition"]: row.get("cross_entropy") for row in iole["results"]}
    baseline = baseline_policy_metrics(model, val_examples, val_data)
    write_json(out_dir / "baseline_policy.json", {k: v for k, v in baseline.items() if k != "rows"})
    ablation_rows = []
    intervention_rows = []
    for name in layers:
        mean_act = capture_mean_activation(model, name, val_data)
        zero = ablate_layer(model, name, val_examples, val_data, mode="zero")
        mean = ablate_layer(model, name, val_examples, val_data, mode="mean", replacement=mean_act)
        ablation_rows.append(zero)
        intervention_rows.append(mean)
        if len(val_records) > 1:
            patched = patch_activation(model, name, source_data=val_records[0], target_data=val_records[-1], examples=val_examples)
            intervention_rows.append({"mode": "patch", **patched})
    write_json(out_dir / "ablation.json", ablation_rows)
    write_json(out_dir / "intervention.json", intervention_rows)
    before = clone_model(model)
    full = clone_model(model)
    set_trainable_layers(full, None, train_all=True)
    train_policy_steps(full, examples, steps=int(budget.get("iole_steps", 2)), data=data)
    updates = parameter_update_norms(before, full, layers)
    write_json(out_dir / "update_sensitivity.json", updates)
    summary = {
        "phase": 6,
        "status": "complete",
        "provenance": "layer_analysis",
        "iole_rank": rank_from_scores(
            {row["condition"]: row.get("cross_entropy", float("nan")) for row in iole["results"] if row["condition"] not in {"frozen", "full"}},
            higher_is_better=False,
        ),
        "ablation_rank": rank_from_scores({row["module_name"]: row.get("cross_entropy", float("nan")) for row in ablation_rows}, higher_is_better=True),
        "baseline_ce": baseline.get("cross_entropy"),
        "iole_ce": iole_ce,
    }
    write_json(out_dir / "summary.json", summary)
    write_phase_manifest(out_dir, summary)
    print(f"Phase 6 complete: {out_dir / 'summary.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
