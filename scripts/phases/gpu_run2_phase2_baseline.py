"""GPU_RUN2 Phase 2: NeSymReS and PySR baselines on oracle synthetic problems."""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "third_party" / "nesymres"))

from evaluation.equation_metrics import eval_expression, score_domain_predictions  # noqa: E402
from evaluation.equation_records import make_gpu_run2_equation_record  # noqa: E402
from evaluation.operator_policy import pysr_operator_kwargs, validate_candidate_expression  # noqa: E402
from gpu_run2_runtime import (  # noqa: E402
    decode_timeout_sec,
    load_gpu_run2_configs,
    nesymres_paths,
    resolve_run_dir,
    utc_now,
    write_json,
)
from resumable_evaluation import (  # noqa: E402
    load_problem_json_checkpoint,
    remaining_eq_ids,
    save_problem_json_checkpoint,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="GPU_RUN2 Phase 2 baselines")
    parser.add_argument("--run-id", default=os.environ.get("LANSR_RUN_ID"))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--methods", nargs="*", default=["nesymres", "pysr"])
    parser.add_argument("--split", default="validation", choices=["train", "validation", "test"])
    return parser.parse_args()


def _load_index(phase1: Path) -> list[dict]:
    import json

    path = phase1 / "index.json"
    if not path.is_file():
        raise FileNotFoundError(f"Phase 1 index missing: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _dummy_record(row: dict, method: str, timeout_sec: float, reason: str | None = None) -> dict:
    valid = reason is None
    return make_gpu_run2_equation_record(
        eq_id=row["eq_id"],
        predicted_expr="" if reason else str(row.get("canonical_expr") or "x_1"),
        variable_names=list(row["oracle_inputs"]),
        scores={
            "valid_pred": 1.0 if valid else 0.0,
            "nmse": 0.0 if valid else float("inf"),
            "r2": 1.0 if valid else -1.0,
            "sym_exact": 0.0,
            "sym_skeleton": 0.0,
            "sym_equiv": 0.0,
            "complexity": 1.0,
            "var_f1": 1.0,
            "var_precision": 1.0,
            "var_recall": 1.0,
            "domain_id_nmse": 0.0 if valid else float("inf"),
            "domain_ood_nmse": 0.0 if valid else float("inf"),
        },
        true_expr=row.get("canonical_expr", ""),
        true_raw=row.get("raw_gnw_formula", ""),
        true_canonical=row.get("canonical_expr", ""),
        true_skeleton=row.get("skeleton_expr", ""),
        motif=row["family_id"],
        split=row["main_split"],
        split_view="main",
        noise=float(row["noise"]),
        data_seed=int(row["data_seed"]),
        training_seed=0,
        condition=method,
        domain_regime="id",
        structure_regime="id",
        parameter_split="main",
        target_variable=row["target_variable"],
        oracle_regulators=row["oracle_regulators"],
        oracle_inputs=row["oracle_inputs"],
        variable_order=row["variable_order"],
        oracle_source_equation_id=row["oracle_source_equation_id"],
        decoder=method,
        failure_reason=reason,
        timeout_budget_sec=timeout_sec,
    )


def main() -> int:
    args = parse_args()
    config = load_gpu_run2_configs()
    run_dir = resolve_run_dir(args.run_id, config=config)
    phase1 = run_dir / "phase1"
    out_dir = run_dir / "phase2"
    out_dir.mkdir(parents=True, exist_ok=True)
    timeout_sec = decode_timeout_sec(config)
    index = _load_index(phase1)
    rows = [row for row in index if row["main_split"] == args.split]
    if args.smoke:
        rows = rows[: min(4, len(rows))]
    eq_ids = [f"{row['eq_id']}::noise{row['noise']}::seed{row['data_seed']}" for row in rows]
    records: dict[str, list] = {method: [] for method in args.methods}
    for method in args.methods:
        ckpt_path = out_dir / f"checkpoint_{method}_{args.split}.json"
        identity = {
            "phase": 2,
            "method": method,
            "split": args.split,
            "timeout_sec": timeout_sec,
        }
        payload = load_problem_json_checkpoint(ckpt_path, expected_identity=identity)
        completed = list(payload["completed_eq_ids"]) if payload else []
        stored = list(payload["records"]) if payload else []
        remaining = remaining_eq_ids(eq_ids, completed)
        by_key = {
            f"{row['eq_id']}::noise{row['noise']}::seed{row['data_seed']}": row for row in rows
        }
        nesymres_model = None
        nesymres_params = None
        if method == "nesymres" and not args.dry_run:
            from models.nesymres_adapter import load_nesymres

            paths = nesymres_paths(config)
            if not paths["weights"].is_file():
                raise FileNotFoundError(f"NeSymReS checkpoint missing: {paths['weights']}")
            nesymres_model, nesymres_params = load_nesymres(
                paths["weights"], paths["config"], paths["eq_setting"]
            )
        for key in remaining:
            row = by_key[key]
            started = time.perf_counter()
            if args.dry_run:
                record = _dummy_record(row, method, timeout_sec)
            else:
                record = _run_one(
                    row,
                    method,
                    timeout_sec,
                    config,
                    phase1,
                    nesymres_model=nesymres_model,
                    nesymres_params=nesymres_params,
                )
            record["process_seconds"] = time.perf_counter() - started
            stored.append(record)
            completed.append(key)
            save_problem_json_checkpoint(
                ckpt_path,
                identity=identity,
                completed_eq_ids=completed,
                records=stored,
            )
        records[method] = stored
        write_json(out_dir / f"{method}_{args.split}_records.json", stored)
    write_json(
        out_dir / "manifest.json",
        {
            "phase": 2,
            "status": "complete",
            "at_utc": utc_now(),
            "split": args.split,
            "methods": args.methods,
            "n_problems": len(rows),
            "dry_run": bool(args.dry_run),
            "timeout_sec": timeout_sec,
            "pysr_operators": pysr_operator_kwargs(config.get("operators")),
        },
    )
    print(f"Phase 2 complete: {out_dir}")
    return 0


def _run_one(
    row: dict,
    method: str,
    timeout_sec: float,
    config: dict,
    phase1: Path,
    *,
    nesymres_model=None,
    nesymres_params=None,
) -> dict:
    from data.gnw_synthetic import load_problem_npz

    npz = load_problem_npz(phase1 / "data" / row["file"])
    X = npz["X_train"]
    y = npz["y_train"]
    names = list(row["oracle_inputs"])
    pred = ""
    reason = None
    candidates: list[str] = []
    n_eval = 0
    search_s = 0.0
    timeout = False
    if method == "pysr":
        from baselines.pysr_runner import fit_pysr_expression

        started = time.perf_counter()
        try:
            pred = fit_pysr_expression(
                X,
                y,
                names,
                niterations=int(config.get("pysr_niterations", 40)),
                random_state=int(row["data_seed"]),
                timeout_in_seconds=timeout_sec,
                operator_set="gpu_run2",
            )
        except Exception as exc:
            reason = f"{type(exc).__name__}: {exc}"
        search_s = time.perf_counter() - started
        candidates = [pred] if pred else []
        n_eval = len(candidates)
    elif method == "nesymres":
        from models.nesymres_adapter import predict_equation_gpu_run2

        if nesymres_model is None or nesymres_params is None:
            from models.nesymres_adapter import load_nesymres

            paths = nesymres_paths(config)
            if not paths["weights"].is_file():
                raise FileNotFoundError(f"NeSymReS checkpoint missing: {paths['weights']}")
            nesymres_model, nesymres_params = load_nesymres(
                paths["weights"], paths["config"], paths["eq_setting"]
            )
        result = predict_equation_gpu_run2(
            nesymres_model,
            nesymres_params,
            X,
            y,
            timeout_sec=timeout_sec,
            operator_config=config.get("operators"),
        )
        pred = str(result.get("equation") or "")
        reason = result.get("failure_reason")
        candidates = list(result.get("all_preds") or [])
        n_eval = int(result.get("n_candidate_evals") or 0)
        search_s = float(result.get("search_seconds") or 0.0)
        timeout = bool(result.get("timeout"))
    else:
        raise ValueError(f"unknown method {method}")
    ok, op_reason = validate_candidate_expression(
        pred,
        point_sets={
            "train": (X, names),
            "id": (npz["X_id"], names),
            "ood": (npz["X_ood"], names),
        },
    )
    if pred and not ok:
        reason = op_reason
        pred = ""
    pred_id = eval_expression(pred, npz["X_id"], names) if pred else None
    pred_ood = eval_expression(pred, npz["X_ood"], names) if pred else None
    scores = score_domain_predictions(
        y_id=npz["y_id"],
        pred_id=pred_id,
        y_ood=npz["y_ood"],
        pred_ood=pred_ood,
        predicted_expr=pred,
        true_vars=names,
        true_expr=row.get("canonical_expr", ""),
        X_id=npz["X_id"],
        X_ood=npz["X_ood"],
        variable_names=names,
    )
    if reason:
        scores["valid_pred"] = 0.0
    return make_gpu_run2_equation_record(
        eq_id=row["eq_id"],
        predicted_expr=pred,
        variable_names=names,
        scores=scores,
        true_expr=row.get("canonical_expr", ""),
        true_raw=row.get("raw_gnw_formula", ""),
        true_canonical=row.get("canonical_expr", ""),
        true_skeleton=row.get("skeleton_expr", ""),
        motif=row["family_id"],
        split=row["main_split"],
        split_view="main",
        noise=float(row["noise"]),
        data_seed=int(row["data_seed"]),
        training_seed=0,
        condition=method,
        domain_regime="id",
        structure_regime="id",
        parameter_split="main",
        target_variable=row["target_variable"],
        oracle_regulators=row["oracle_regulators"],
        oracle_inputs=row["oracle_inputs"],
        variable_order=row["variable_order"],
        oracle_source_equation_id=row["oracle_source_equation_id"],
        decoder=method,
        failure_reason=reason,
        candidate_expressions=candidates,
        search_seconds=search_s,
        n_candidate_evals=n_eval,
        timeout=timeout,
        timeout_budget_sec=timeout_sec,
    )


if __name__ == "__main__":
    raise SystemExit(main())
