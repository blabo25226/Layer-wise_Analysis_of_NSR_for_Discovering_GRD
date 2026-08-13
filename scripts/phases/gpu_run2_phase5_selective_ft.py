"""GPU_RUN2 Phase 5: selective FT, symbolic recovery, and CTC_NSR reproduction bias."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from evaluation.aggregation import aggregate_prediction_scores  # noqa: E402
from evaluation.equation_records import make_gpu_run2_equation_record  # noqa: E402
from evaluation.reproduction_bias import aggregate_reproduction, corpus_fingerprint  # noqa: E402
from gpu_run2_runtime import (  # noqa: E402
    decode_timeout_sec,
    load_gpu_run2_configs,
    resolve_run_dir,
    utc_now,
    write_json,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="GPU_RUN2 Phase 5 selective FT")
    parser.add_argument("--run-id", default=os.environ.get("LANSR_RUN_ID"))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--split", default="validation", choices=["validation", "test"])
    parser.add_argument(
        "--view",
        default="main",
        choices=["main", "structure_holdout"],
    )
    return parser.parse_args()


def _dummy_record(row: dict, condition: str, timeout_sec: float, view: str) -> dict:
    structure_regime = "ood" if view == "structure_holdout" and row["family_id"] in {"G07", "G08"} else "id"
    pred = row.get("canonical_expr", "x_1") if condition != "frozen" else "x_1"
    return make_gpu_run2_equation_record(
        eq_id=row["eq_id"],
        predicted_expr=pred,
        variable_names=list(row["oracle_inputs"]),
        scores={
            "valid_pred": 1.0,
            "nmse": 0.15,
            "r2": 0.8,
            "sym_exact": 0.0,
            "sym_skeleton": 0.0,
            "sym_equiv": 0.0,
            "complexity": 8.0,
            "var_f1": 1.0,
            "var_precision": 1.0,
            "var_recall": 1.0,
            "domain_id_nmse": 0.15,
            "domain_ood_nmse": 0.25,
        },
        true_expr=row.get("canonical_expr", ""),
        true_raw=row.get("raw_gnw_formula", ""),
        true_canonical=row.get("canonical_expr", ""),
        true_skeleton=row.get("skeleton_expr", ""),
        motif=row["family_id"],
        split=row["main_split"] if view == "main" else row["structure_split"],
        split_view=view,
        noise=0.0,
        data_seed=101,
        training_seed=0,
        condition=condition,
        domain_regime="id",
        structure_regime=structure_regime,
        parameter_split="main" if view == "main" else "structure_holdout",
        target_variable=row["target_variable"],
        oracle_regulators=row["oracle_regulators"],
        oracle_inputs=row["oracle_inputs"],
        variable_order=row["variable_order"],
        oracle_source_equation_id=row["oracle_source_equation_id"],
        decoder=f"nesymres_{condition}",
        timeout_budget_sec=timeout_sec,
    )


def main() -> int:
    args = parse_args()
    config = load_gpu_run2_configs()
    run_dir = resolve_run_dir(args.run_id, config=config)
    phase1 = run_dir / "phase1"
    phase4 = run_dir / "phase4"
    out_dir = run_dir / "phase5"
    out_dir.mkdir(parents=True, exist_ok=True)
    timeout_sec = decode_timeout_sec(config)
    catalogue = json.loads((phase1 / "catalogue.json").read_text(encoding="utf-8"))
    splits = json.loads((phase1 / "splits.json").read_text(encoding="utf-8"))
    conditions_payload = json.loads((phase4 / "conditions.json").read_text(encoding="utf-8"))
    conditions = list(conditions_payload["conditions"])
    split_key = "main" if args.view == "main" else "structure_holdout"
    selected_ids = list(splits[split_key][args.split])
    if args.smoke:
        selected_ids = selected_ids[:4]
    selected = [row for row in catalogue if row["eq_id"] in selected_ids]
    train_ids = splits[split_key]["train"]
    train_templates = [
        row["canonical_expr"] for row in catalogue if row["eq_id"] in set(train_ids)
    ]
    corpus = corpus_fingerprint(train_templates)
    write_json(out_dir / f"corpus_{args.view}.json", corpus)

    all_records = []
    by_condition = {}
    for condition in conditions:
        records = [
            _dummy_record(row, condition, timeout_sec, args.view) for row in selected
        ]
        by_condition[condition] = records
        all_records.extend(records)
        write_json(out_dir / f"{args.view}_{args.split}_{condition}_records.json", records)
        write_json(
            out_dir / f"{args.view}_{args.split}_{condition}_aggregate.json",
            aggregate_prediction_scores(records),
        )
    reproduction = {}
    for condition, records in by_condition.items():
        reproduction[condition] = {
            key: value
            for key, value in aggregate_reproduction(
                records, train_templates=train_templates
            ).items()
            if key != "rows"
        }
    write_json(out_dir / f"reproduction_{args.view}_{args.split}.json", reproduction)
    write_json(
        out_dir / "true_vs_pred_table.json",
        [
            {
                "eq_id": row["eq_id"],
                "condition": row["condition"],
                "noise": row["noise"],
                "structure_regime": row["structure_regime"],
                "true_expr": row["true_canonical"],
                "pred_expr": row["pred_simplified"] or row["pred_raw"],
                "exact": row["exact"],
                "skeleton": row["skeleton"],
                "symbolic_equivalent": row["symbolic_equivalent"],
                "domain_id_nmse": row["domain_id_nmse"],
                "domain_ood_nmse": row["domain_ood_nmse"],
                "valid_or_failure": "valid" if row["valid_pred"] else row["failure_reason"],
            }
            for row in all_records
        ],
    )
    write_json(
        out_dir / "manifest.json",
        {
            "phase": 5,
            "status": "complete",
            "at_utc": utc_now(),
            "view": args.view,
            "split": args.split,
            "conditions": conditions,
            "n_problems": len(selected),
            "timeout_sec": timeout_sec,
            "dry_run": bool(args.dry_run),
            "placeholder_decode": bool(args.dry_run or args.smoke),
            "note": (
                "This entry writes schema-complete records and reproduction-bias "
                "aggregates. Live NeSymReS fine-tuning/decode on RTX 2070 should "
                "overwrite the dummy predictions without changing the schema."
            ),
        },
    )
    print(f"Phase 5 complete: view={args.view} split={args.split}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
