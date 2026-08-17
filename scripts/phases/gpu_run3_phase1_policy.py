"""GPU_RUN3 Phase 1: NDformer policy reproduction (teacher forcing)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from gpu_run3.cli import common_parser, dummy_phase_output, phase_budget, require_previous, write_phase_manifest  # noqa: E402
from gpu_run3.corpus import build_analysis_corpus  # noqa: E402
from gpu_run3.policy import teacher_forcing_metrics  # noqa: E402
from gpu_run3_runtime import (  # noqa: E402
    load_gpu_run3_configs,
    load_json,
    load_ndformer,
    nd2_paths,
    require_python_310,
    resolve_run_dir,
    seed_everything,
    select_device,
    write_json,
)


def parse_args():
    return common_parser("GPU_RUN3 Phase 1 policy reproduction").parse_args()


def main() -> int:
    args = parse_args()
    require_python_310()
    config = load_gpu_run3_configs()
    run_dir = resolve_run_dir(args.run_id, config=config)
    out_dir = run_dir / "phase1"
    out_dir.mkdir(parents=True, exist_ok=True)
    if args.dry_run:
        dummy_phase_output(out_dir, 1, extra={"note": "dry-run policy metrics only"})
        print(f"Phase 1 dry-run: {out_dir}")
        return 0
    require_previous(run_dir, "phase0/preflight.json")
    seed_everything(args.seed)
    budget = phase_budget(config, smoke=args.smoke)
    paths = nd2_paths(config)
    device = select_device(allow_cpu=args.allow_cpu)
    model = load_ndformer(paths["checkpoint"], device=device)
    corpus = build_analysis_corpus(
        seed=args.seed,
        n_nodes=int(budget.get("n_nodes", 6)),
        n_edges=int(budget.get("n_edges", 10)),
        n_time=int(budget.get("simulate_steps", 24)),
    )
    split = "analysis_validation" if args.split in {"validation", "analysis_validation"} else args.split
    records = [row for row in corpus["records"] if row["split"] == split]
    if args.smoke:
        records = records[: max(1, int(budget.get("n_policy_examples", 8)) // 4)]
    write_json(out_dir / "corpus_index.json", {"split": split, "n": len(records), "formula_ids": [r["formula_id"] for r in records]})
    all_rows = []
    aggregates = []
    for row in records:
        examples = row["teacher_forcing"][: int(budget.get("n_policy_examples", 8))]
        model.set_data(Xv=row["Xv"], Xe=row["Xe"], A=row["A"], G=row["G"], Y=row["Y"], root_type=row["root_type"], cache_data_emb=True)
        metrics = teacher_forcing_metrics(model, examples)
        metrics["problem_id"] = row["problem_id"]
        metrics["formula_id"] = row["formula_id"]
        metrics["system_id"] = row["system_id"]
        metrics["prefix_length"] = len(row["prefix"])
        aggregates.append({k: v for k, v in metrics.items() if k != "rows"})
        for item in metrics["rows"]:
            all_rows.append({**item, "problem_id": row["problem_id"], "formula_id": row["formula_id"]})
    summary = {
        "phase": 1,
        "status": "complete",
        "split": split,
        "n_problems": len(records),
        "n_examples": len(all_rows),
        "valid_rate": sum(1 for r in all_rows if r.get("valid")) / max(len(all_rows), 1),
        "mean_ce": _mean([a.get("cross_entropy") for a in aggregates]),
        "mean_top1": _mean([a.get("top1_accuracy") for a in aggregates]),
        "mean_topk": _mean([a.get("topk_accuracy") for a in aggregates]),
        "mean_rank": _mean([a.get("mean_true_symbol_rank") for a in aggregates]),
        "mean_true_prob": _mean([a.get("mean_true_symbol_probability") for a in aggregates]),
        "mean_entropy": _mean([a.get("mean_policy_entropy") for a in aggregates]),
        "provenance": "upstream_reproduction",
    }
    write_json(out_dir / "policy_rows.json", all_rows)
    write_json(out_dir / "problem_aggregates.json", aggregates)
    write_json(out_dir / "summary.json", summary)
    write_phase_manifest(out_dir, summary)
    print(f"Phase 1 complete: {out_dir / 'summary.json'}")
    return 0


def _mean(values: list) -> float:
    import math

    finite = [float(v) for v in values if v is not None and math.isfinite(float(v))]
    return float(sum(finite) / len(finite)) if finite else float("nan")


if __name__ == "__main__":
    raise SystemExit(main())
