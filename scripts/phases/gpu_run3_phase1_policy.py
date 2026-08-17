"""GPU_RUN3 Phase 1: NDformer policy reproduction (teacher forcing).

Evaluates the official checkpoint on the analysis-validation split of the
ND2-distribution corpus, for every configured seed. Failures (invalid prefix,
out-of-vocabulary symbol) are stored, not dropped.
"""

from __future__ import annotations

import math
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from gpu_run3.cli import (  # noqa: E402
    common_parser,
    dummy_phase_output,
    phase_budget,
    require_previous,
    seed_bundles,
    write_phase_manifest,
)
from gpu_run3.corpus import build_analysis_corpus, corpus_kwargs_from_budget  # noqa: E402
from gpu_run3.policy import teacher_forcing_metrics  # noqa: E402
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
    return common_parser("GPU_RUN3 Phase 1 policy reproduction").parse_args()


def _mean(values) -> float:
    finite = [float(v) for v in values if v is not None and math.isfinite(float(v))]
    return float(sum(finite) / len(finite)) if finite else float("nan")


def _std(values) -> float:
    finite = [float(v) for v in values if v is not None and math.isfinite(float(v))]
    if len(finite) < 2:
        return float("nan")
    mean = sum(finite) / len(finite)
    return float((sum((v - mean) ** 2 for v in finite) / (len(finite) - 1)) ** 0.5)


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
    budget = phase_budget(config, smoke=args.smoke)
    paths = nd2_paths(config)
    device = select_device(allow_cpu=args.allow_cpu)
    model = load_ndformer(paths["checkpoint"], device=device)
    split = "analysis_validation" if args.split in {"validation", "analysis_validation"} else args.split
    max_examples = int(budget.get("n_policy_examples", 8))
    corpus_kwargs = corpus_kwargs_from_budget(budget)

    all_rows = []
    aggregates = []
    per_seed = []
    corpus_stats = []
    for seed in seed_bundles(config, budget, base_seed=args.seed):
        seed_everything(seed)
        corpus = build_analysis_corpus(seed=seed, **corpus_kwargs)
        corpus_stats.append(
            {
                "seed": seed,
                "n_records": corpus["n_records"],
                "n_failures": corpus["n_failures"],
                "split_counts": corpus["split_counts"],
                "failures": corpus["failures"],
            }
        )
        records = [row for row in corpus["records"] if row["split"] == split]
        seed_aggregates = []
        for row in records:
            examples = [ex for ex in row["teacher_forcing"]][:max_examples]
            model.set_data(
                Xv=row["Xv"],
                Xe=row["Xe"],
                A=row["A"],
                G=row["G"],
                Y=row["Y"],
                root_type=row["root_type"],
                cache_data_emb=True,
            )
            metrics = teacher_forcing_metrics(model, examples)
            aggregate = {k: v for k, v in metrics.items() if k != "rows"}
            aggregate.update(
                {
                    "seed": seed,
                    "problem_id": row["problem_id"],
                    "formula_id": row["formula_id"],
                    "system_id": row["system_id"],
                    "prefix_length": len(row["prefix"]),
                    "complexity": row["complexity"],
                    "n_network_ops": sum(tok in {"aggr", "rgga", "sour", "targ"} for tok in row["prefix"]),
                    "root_operator": row["prefix"][0] if row["prefix"] else None,
                }
            )
            aggregates.append(aggregate)
            seed_aggregates.append(aggregate)
            for item in metrics["rows"]:
                all_rows.append(
                    {
                        **item,
                        "seed": seed,
                        "problem_id": row["problem_id"],
                        "formula_id": row["formula_id"],
                        "prefix_length": len(row["prefix"]),
                    }
                )
        per_seed.append(
            {
                "seed": seed,
                "n_problems": len(records),
                "n_examples": sum(a["n_examples"] for a in seed_aggregates),
                "mean_ce": _mean([a.get("cross_entropy") for a in seed_aggregates]),
                "mean_top1": _mean([a.get("top1_accuracy") for a in seed_aggregates]),
                "mean_topk": _mean([a.get("topk_accuracy") for a in seed_aggregates]),
                "valid_rate": _mean([a.get("valid_rate") for a in seed_aggregates]),
            }
        )

    by_length = defaultdict(list)
    for row in all_rows:
        if row.get("valid"):
            by_length[len(row.get("prefix") or [])].append(row)
    length_table = {
        str(length): {
            "n": len(rows),
            "mean_ce": _mean([r["ce"] for r in rows]),
            "mean_top1": _mean([float(r["top1"]) for r in rows]),
            "mean_rank": _mean([r["rank"] for r in rows]),
        }
        for length, rows in sorted(by_length.items())
    }
    by_target = defaultdict(list)
    for row in all_rows:
        if row.get("valid"):
            by_target[str(row.get("target"))].append(row)
    target_table = {
        symbol: {
            "n": len(rows),
            "mean_ce": _mean([r["ce"] for r in rows]),
            "mean_top1": _mean([float(r["top1"]) for r in rows]),
        }
        for symbol, rows in sorted(by_target.items(), key=lambda kv: -len(kv[1]))
    }
    failures = defaultdict(int)
    for row in all_rows:
        if not row.get("valid"):
            failures[str(row.get("failure_reason"))] += 1

    summary = {
        "phase": 1,
        "status": "complete",
        "split": split,
        "seeds": [item["seed"] for item in per_seed],
        "n_problems": len(aggregates),
        "n_examples": len(all_rows),
        "valid_rate": sum(1 for r in all_rows if r.get("valid")) / max(len(all_rows), 1),
        "mean_ce": _mean([a.get("cross_entropy") for a in aggregates]),
        "mean_top1": _mean([a.get("top1_accuracy") for a in aggregates]),
        "mean_topk": _mean([a.get("topk_accuracy") for a in aggregates]),
        "mean_rank": _mean([a.get("mean_true_symbol_rank") for a in aggregates]),
        "mean_true_prob": _mean([a.get("mean_true_symbol_probability") for a in aggregates]),
        "mean_entropy": _mean([a.get("mean_policy_entropy") for a in aggregates]),
        "std_ce_across_problems": _std([a.get("cross_entropy") for a in aggregates]),
        "per_seed": per_seed,
        "failure_counts": dict(failures),
        "by_prefix_length": length_table,
        "by_true_symbol": target_table,
        "provenance": "upstream_reproduction",
    }
    write_json(out_dir / "policy_rows.json", all_rows)
    write_json(out_dir / "problem_aggregates.json", aggregates)
    write_json(out_dir / "corpus_index.json", corpus_stats)
    write_json(out_dir / "summary.json", summary)
    write_phase_manifest(out_dir, {k: v for k, v in summary.items() if k not in {"by_true_symbol", "by_prefix_length"}})
    print(
        f"Phase 1 complete: {out_dir / 'summary.json'} "
        f"(n={summary['n_examples']}, CE={summary['mean_ce']:.4f}, top1={summary['mean_top1']:.4f})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
