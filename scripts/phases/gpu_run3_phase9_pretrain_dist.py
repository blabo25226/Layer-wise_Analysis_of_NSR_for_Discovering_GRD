"""GPU_RUN3 Phase 9: optional pretraining-distribution nearest-TED analysis."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from gpu_run3.cli import common_parser, dummy_phase_output, require_previous, write_phase_manifest  # noqa: E402
from gpu_run3.corpus import build_analysis_corpus  # noqa: E402
from gpu_run3.ted import ted_metrics  # noqa: E402
from gpu_run3_runtime import load_gpu_run3_configs, require_python_310, resolve_run_dir, seed_everything, write_json  # noqa: E402


def parse_args():
    return common_parser("GPU_RUN3 Phase 9 pretraining-distribution TED").parse_args()


def main() -> int:
    args = parse_args()
    require_python_310()
    config = load_gpu_run3_configs()
    run_dir = resolve_run_dir(args.run_id, config=config)
    out_dir = run_dir / "phase9"
    out_dir.mkdir(parents=True, exist_ok=True)
    if args.dry_run:
        dummy_phase_output(out_dir, 9, extra={"metric": "retrieved_nearest_ted"})
        print(f"Phase 9 dry-run: {out_dir}")
        return 0
    require_previous(run_dir, "phase0/preflight.json")
    seed_everything(args.seed)
    corpus = build_analysis_corpus(seed=args.seed)
    catalog = [row for row in corpus["records"] if row["split"] == "analysis_train"]
    queries = [row for row in corpus["records"] if row["split"] != "analysis_train"]
    rows = []
    for query in queries:
        best = None
        best_ref = None
        for ref in catalog:
            if ref["formula_id"] == query["formula_id"]:
                continue
            metrics = ted_metrics(query["prefix"], ref["prefix"], variable_aware=False)
            distance = metrics["ted_skeleton"]
            if best is None or (distance == distance and distance < best):
                best = distance
                best_ref = ref["formula_id"]
        rows.append(
            {
                "problem_id": query["problem_id"],
                "formula_id": query["formula_id"],
                "retrieved_nearest_ted": best,
                "nearest_formula_id": best_ref,
                "metric_name": "retrieved_nearest_ted",
            }
        )
    summary = {
        "phase": 9,
        "status": "complete",
        "n_queries": len(rows),
        "note": "Distances are against the analysis-train catalog, not the full 1M pretrain set.",
    }
    write_json(out_dir / "nearest_ted.json", rows)
    write_json(out_dir / "summary.json", summary)
    write_phase_manifest(out_dir, summary)
    print(f"Phase 9 complete: {out_dir / 'summary.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
