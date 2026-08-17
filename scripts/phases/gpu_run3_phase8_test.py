"""GPU_RUN3 Phase 8: frozen-method test evaluation and integrated reports.

Everything read here (layer ranking, selective-FT conditions, MCTS budget) was
frozen on validation in Phases 4-7. ``analysis_test`` is touched exactly once,
in this script.
"""

from __future__ import annotations

import json
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
from gpu_run3.records import dummy_formula_record  # noqa: E402
from gpu_run3.search import run_mcts  # noqa: E402
from gpu_run3.training import clone_model, evaluate_records, train_policy_multi_problem  # noqa: E402
from gpu_run3_runtime import (  # noqa: E402
    configure_nd2_logging,
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
    parser = common_parser("GPU_RUN3 Phase 8 final test / integrated analysis")
    parser.add_argument("--skip-mcts", action="store_true")
    return parser.parse_args()


def _read(path: Path):
    if not path.is_file():
        return {"status": "missing", "path": str(path)}
    return json.loads(path.read_text(encoding="utf-8"))


def _mean(values) -> float:
    finite = [float(v) for v in values if v is not None and math.isfinite(float(v))]
    return float(sum(finite) / len(finite)) if finite else float("nan")


def main() -> int:
    args = parse_args()
    require_python_310()
    config = load_gpu_run3_configs()
    run_dir = resolve_run_dir(args.run_id, config=config)
    out_dir = run_dir / "phase8"
    out_dir.mkdir(parents=True, exist_ok=True)
    if args.dry_run:
        dummy_phase_output(
            out_dir,
            8,
            extra={
                "result_a": "nd2_reproduction",
                "result_b": "ndformer_layer_analysis",
                "records": [dummy_formula_record("phase8_dummy")],
            },
        )
        print(f"Phase 8 dry-run: {out_dir}")
        return 0
    require_previous(run_dir, "phase0/preflight.json")
    conditions_path = require_previous(run_dir, "phase7/conditions.json")
    frozen = json.loads(conditions_path.read_text(encoding="utf-8"))
    if frozen.get("frozen_on_split") != "analysis_validation":
        raise RuntimeError("layer ranking was not frozen on analysis_validation")
    configure_nd2_logging(out_dir / "nd2.log")
    budget = phase_budget(config, smoke=args.smoke)
    paths = nd2_paths(config)
    device = select_device(allow_cpu=args.allow_cpu)
    model = load_ndformer(paths["checkpoint"], device=device)
    inventory = inventory_ndformer(model)
    seed = int(frozen.get("seed") or args.seed or 101)
    seed_everything(seed)
    corpus = build_analysis_corpus(seed=seed, **corpus_kwargs_from_budget(budget))
    train_records = [r for r in corpus["records"] if r["split"] == "analysis_train"]
    test_rows = [r for r in corpus["records"] if r["split"] == "analysis_test"]
    if not test_rows:
        raise RuntimeError("analysis_test split is empty")
    max_examples = int(budget.get("probe_examples", 16))
    ft_steps = int(budget.get("ft_steps", 2))

    # Result A: the untouched official checkpoint on the held-out test formulas.
    baseline_test = evaluate_records(model, test_rows, max_examples_per_problem=max_examples)

    # Result B: the frozen selective-FT conditions, re-trained with the frozen
    # recipe and evaluated once on analysis_test.
    conditions = frozen.get("conditions") or {}
    mcts_panel = select_fixed_panel(
        corpus["records"], split="analysis_test", n=int(budget.get("mcts_panel_problems", 2))
    )
    condition_results = []
    for name, selected in conditions.items():
        candidate = clone_model(model)
        if name == "full":
            param_info = set_trainable_layers(candidate, None, train_all=True)
        elif name == "frozen":
            param_info = set_trainable_layers(candidate, [], train_all=False)
        else:
            param_info = set_trainable_layers(candidate, list(selected or []), train_all=False)
        train_info = (
            {"steps": 0, "losses": [], "wall_time": 0.0, "trainable_parameters": 0}
            if name == "frozen"
            else train_policy_multi_problem(
                candidate, train_records, steps=ft_steps, seed=seed, max_examples_per_problem=max_examples
            )
        )
        metrics = evaluate_records(candidate, test_rows, max_examples_per_problem=max_examples)
        entry = {
            "condition": name,
            "layers": selected,
            **param_info,
            **{k: v for k, v in metrics.items() if k != "per_problem"},
            "per_problem": metrics.get("per_problem"),
            "train": train_info,
        }
        if not args.skip_mcts:
            records = [
                run_mcts(
                    model=candidate,
                    Xv=row["Xv"],
                    Xe=row["Xe"],
                    A=row["A"],
                    G=row["G"],
                    Y=row["Y"],
                    vars_node=row["vars_node"],
                    vars_edge=row["vars_edge"],
                    true_prefix=row["prefix"],
                    episode_limit=int(budget.get("mcts_episode_limit", 3)),
                    time_limit_sec=float(budget.get("mcts_time_limit_sec_ft", 30)),
                    mcts_config=config["mcts"],
                    random_state=seed,
                    problem_id=f"phase8_{name}_{row['problem_id']}",
                    system_name=row["system_id"],
                    split="analysis_test",
                    condition=name,
                )
                for row in mcts_panel
            ]
            entry["mcts"] = records
            entry["mcts_summary"] = {
                "n": len(records),
                "n_valid": sum(1 for r in records if r.get("valid")),
                "n_exact": sum(1 for r in records if r.get("exact") == 1.0),
                "mean_ted_raw": _mean([r.get("ted_raw") for r in records]),
                "mean_fit_error": _mean([r.get("fit_error") for r in records]),
            }
        condition_results.append(entry)
        del candidate
        import gc

        import torch

        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        print(f"  {name}: test CE={entry.get('cross_entropy')} top1={entry.get('top1_accuracy')}")

    phase1 = _read(run_dir / "phase1" / "summary.json")
    phase2 = _read(run_dir / "phase2" / "summary.json")
    phase3 = _read(run_dir / "phase3" / "summary.json")
    phase4 = _read(run_dir / "phase4" / "summary.json")
    phase5 = _read(run_dir / "phase5" / "summary.json")
    phase6 = _read(run_dir / "phase6" / "summary.json")
    phase7 = _read(run_dir / "phase7" / "summary.json")
    report = {
        "phase": 8,
        "status": "complete",
        "seed": seed,
        "architecture": {
            "ranking_layers": inventory["ranking_layers"],
            "n_encoder_transformer_layers": inventory["n_encoder_transformer_layers"],
            "n_decoder_transformer_layers": inventory["n_decoder_transformer_layers"],
            "total_parameters": inventory["total_parameters"],
        },
        "result_a_nd2_reproduction": {
            "policy_validation": phase1,
            "pipeline": phase2,
            "synthetic_benchmark": phase3,
        },
        "result_b_layer_analysis": {
            "probes_gradient_cka": {
                k: v for k, v in phase4.items() if k in {"probe_minus_control", "gradient_norm", "probe_rank_next_symbol", "gradient_rank"}
            },
            "decoderlens": {
                k: v for k, v in phase5.items() if k in {"encoder_layer_summary", "decoder_layer_summary", "decoderlens_rank"}
            },
            "causal": {
                k: v for k, v in phase6.items() if k in {"iole_ce", "iole_rank", "ablation_rank", "intervention_rank", "update_sensitivity_rank", "layer_effects"}
            },
            "frozen_conditions": frozen,
            "selective_ft_validation": phase7.get("results"),
            "test_baseline_policy": {k: v for k, v in baseline_test.items() if k != "per_problem"},
            "test_conditions": [{k: v for k, v in row.items() if k != "mcts"} for row in condition_results],
        },
        "test_n_problems": len(test_rows),
        "test_n_mcts_problems": len(mcts_panel) if not args.skip_mcts else 0,
        "note": "analysis_test evaluated once after ranking, conditions and budgets were frozen on validation.",
    }
    write_json(out_dir / "test_conditions.json", condition_results)
    write_json(out_dir / "report.json", report)
    write_json(
        out_dir / "summary.json",
        {
            "phase": 8,
            "status": "complete",
            "test_n": len(test_rows),
            "test_baseline_ce": baseline_test.get("cross_entropy"),
            "test_baseline_top1": baseline_test.get("top1_accuracy"),
            "conditions": {row["condition"]: row.get("cross_entropy") for row in condition_results},
        },
    )
    write_phase_manifest(out_dir, {"phase": 8, "status": "complete", "test_n": len(test_rows), "seed": seed})
    print(f"Phase 8 complete: {out_dir / 'report.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
