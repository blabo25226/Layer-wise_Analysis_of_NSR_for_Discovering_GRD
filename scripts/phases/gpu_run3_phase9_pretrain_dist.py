"""GPU_RUN3 Phase 9: optional pretraining-distribution nearest-TED analysis.

The catalog is sampled from the official ND2 formula grammar
(``GDExpr.random_fill_expr``), i.e. the pretraining distribution, not the full
1M-sample archive. The metric is therefore reported as ``retrieved_nearest_ted``
per plan section 12, never as an exact nearest-neighbour distance.
"""

from __future__ import annotations

import math
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from gpu_run3.cli import (  # noqa: E402
    common_parser,
    dummy_phase_output,
    phase_budget,
    require_previous,
    write_phase_manifest,
)
from gpu_run3.corpus import build_analysis_corpus, corpus_kwargs_from_budget, sample_official_prefixes  # noqa: E402
from gpu_run3.formulas import formula_views  # noqa: E402
from gpu_run3.ted import ted_metrics  # noqa: E402
from gpu_run3_runtime import (  # noqa: E402
    load_gpu_run3_configs,
    require_python_310,
    resolve_run_dir,
    seed_everything,
    write_json,
)


def parse_args():
    parser = common_parser("GPU_RUN3 Phase 9 pretraining-distribution TED")
    parser.add_argument("--catalog-size", type=int, default=None)
    return parser.parse_args()


def _mean(values) -> float:
    finite = [float(v) for v in values if v is not None and math.isfinite(float(v))]
    return float(sum(finite) / len(finite)) if finite else float("nan")


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
    budget = phase_budget(config, smoke=args.smoke)
    seed = int(args.seed) or int((config.get("seed_bundles") or [{"data_seed": 101}])[0]["data_seed"])
    seed_everything(seed)
    corpus = build_analysis_corpus(seed=seed, **corpus_kwargs_from_budget(budget))
    queries = [row for row in corpus["records"] if row["split"] != "analysis_train"]
    catalog_size = int(args.catalog_size or budget.get("pretrain_catalog_size", 200))
    length_range = budget.get("corpus_length_range") or [5, 16]
    # Catalog seed is offset so the catalog is never the corpus itself.
    catalog_items = sample_official_prefixes(
        catalog_size,
        seed=seed + 900_000,
        length_range=(int(length_range[0]), int(length_range[1])),
    )
    catalog = []
    for item in catalog_items:
        views = formula_views(item["prefix"])
        catalog.append(
            {
                "prefix": item["prefix"],
                "canonical_expr": views["canonical_expr"],
                "size": len(item["prefix"]),
            }
        )
    write_json(
        out_dir / "catalog.json",
        {"n": len(catalog), "seed": seed + 900_000, "formulas": [c["canonical_expr"] for c in catalog]},
    )

    started = time.time()
    rows = []
    size_window = int(budget.get("pretrain_size_window", 4))
    for query in queries:
        query_size = len(query["prefix"])
        # Cheap prefilter by tree size before the quadratic TED pass.
        candidates = [c for c in catalog if abs(c["size"] - query_size) <= size_window] or catalog
        best = float("inf")
        best_raw = float("inf")
        best_ref = None
        n_compared = 0
        failures = 0
        for ref in candidates:
            if ref["canonical_expr"] == query["canonical_expr"]:
                continue
            metrics = ted_metrics(query["prefix"], ref["prefix"], variable_aware=False)
            n_compared += 1
            distance = metrics["ted_skeleton"]
            if metrics["failure_reason"] or distance != distance:
                failures += 1
                continue
            if distance < best:
                best = distance
                best_raw = metrics["ted_raw"]
                best_ref = ref["canonical_expr"]
        rows.append(
            {
                "problem_id": query["problem_id"],
                "formula_id": query["formula_id"],
                "split": query["split"],
                "formula": query["raw_expr"],
                "tree_size": query_size,
                "retrieved_nearest_ted_skeleton": None if best == float("inf") else best,
                "retrieved_nearest_ted_raw": None if best_raw == float("inf") else best_raw,
                "nearest_formula": best_ref,
                "n_compared": n_compared,
                "n_ted_failures": failures,
                "metric_name": "retrieved_nearest_ted",
            }
        )
    summary = {
        "phase": 9,
        "status": "complete",
        "provenance": "layer_analysis",
        "seed": seed,
        "n_queries": len(rows),
        "catalog_size": len(catalog),
        "catalog_source": "GDExpr.random_fill_expr (official pretraining grammar)",
        "size_window": size_window,
        "mean_retrieved_nearest_ted_skeleton": _mean([r["retrieved_nearest_ted_skeleton"] for r in rows]),
        "mean_retrieved_nearest_ted_raw": _mean([r["retrieved_nearest_ted_raw"] for r in rows]),
        "wall_time": time.time() - started,
        "note": (
            "Approximate retrieval over a sampled catalog from the official formula "
            "grammar, not the full 1M-sample pretraining archive; reported as "
            "retrieved_nearest_ted per plan section 12."
        ),
    }
    write_json(out_dir / "nearest_ted.json", rows)
    write_json(out_dir / "summary.json", summary)
    write_phase_manifest(out_dir, summary)
    print(f"Phase 9 complete: {out_dir / 'summary.json'} (n={len(rows)}, catalog={len(catalog)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
