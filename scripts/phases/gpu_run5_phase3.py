"""GPU_RUN5 Phase 3: frozen GRN generation and validation-only reranking."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np
from scipy import stats

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from gpu_run2_runtime import git_info, sha256_file, write_json  # noqa: E402
from gpu_run4.inference import fit_and_collect, integrate_candidate  # noqa: E402
from gpu_run4.trajectories import corrupt_trajectory, r2_score  # noqa: E402
from gpu_run4_runtime import (  # noqa: E402
    candidate_infix,
    load_odeformer_model,
    make_symbolic_regressor,
    select_device,
)
from gpu_run5.config import (  # noqa: E402
    budget,
    load_config,
    phase_dir,
    read_json,
    run_dir,
    sanitize_nonfinite,
    write_manifest,
)
from gpu_run5.evaluation import (  # noqa: E402
    formula_metrics,
    formula_selection_key,
    robust_median,
    select_candidate,
    trajectory_nrmse,
)
from gpu_run5.seeding import stable_problem_seed  # noqa: E402


RULES = (
    "official_reconstruction",
    "input_robust",
    "selection_ic",
    "multi_ic",
    "multi_ic_complexity",
    "structural_oracle",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", default=os.environ.get("LANSR_RUN_ID"))
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--allow-cpu", action="store_true")
    parser.add_argument("--limit-cells", type=int, default=None, help="diagnostic only; makes the phase incomplete")
    return parser.parse_args()


def _cell_id(system_id: str, bundle_index: int, sigma: float, rho: float) -> str:
    return f"{system_id}_b{bundle_index}_n{sigma:g}_r{rho:g}".replace(".", "p")


def _candidate_hash(infixes: list[str | None]) -> str:
    return hashlib.sha256(json.dumps(infixes, ensure_ascii=True, separators=(",", ":")).encode()).hexdigest()


def _trajectory_groups(row: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    return {
        role: sorted(
            [item for item in row["trajectories"] if item["role"] == role],
            key=lambda item: int(item["role_index"]),
        )
        for role in ("input", "selection", "generalization")
    }


def _evaluate_candidate(
    row: dict[str, Any], tree: Any, raw: str, index: int, regressor: Any, *, penalty: float
) -> dict[str, Any]:
    formula = formula_metrics(row["teacher_infix"], raw)
    trajectory_metrics: dict[str, list[Any]] = {
        "input_nrmse": [], "selection_nrmse": [], "generalization_nrmse": [],
        "input_r2": [], "selection_r2": [], "generalization_r2": [],
        "input_failures": [], "selection_failures": [], "generalization_failures": [],
    }
    for role, trajectories in _trajectory_groups(row).items():
        for trajectory in trajectories:
            times = np.asarray(trajectory["times"], dtype=float)
            truth = np.asarray(trajectory["trajectory"], dtype=float)
            predicted, failure = integrate_candidate(
                regressor, times, trajectory["initial_condition"], tree, timeout_sec=10.0
            )
            trajectory_metrics[f"{role}_nrmse"].append(trajectory_nrmse(truth, predicted, penalty=penalty))
            value = r2_score(truth, predicted)
            trajectory_metrics[f"{role}_r2"].append(value if math.isfinite(value) else None)
            trajectory_metrics[f"{role}_failures"].append(failure)
    return {
        "candidate_index": int(index),
        "candidate_formula_raw": raw,
        **formula,
        "trajectory_metrics": trajectory_metrics,
    }


def _run_cell(
    row: dict[str, Any], *, model: Any, config: dict[str, Any], bundle: dict[str, Any],
    bundle_index: int, sigma: float, rho: float, beam_size: int, penalty: float,
) -> dict[str, Any]:
    system_id = str(row["system_id"])
    condition = f"frozen_n{sigma:g}_r{rho:g}"
    candidate_seed = stable_problem_seed(
        int(bundle["candidate_seed"]), system_id=system_id, condition=condition,
        noise_sigma=sigma, subsample_rho=rho, sampling_replicate=bundle_index,
    )
    corruption_seed = stable_problem_seed(
        int(bundle["corruption_seed"]), system_id=system_id, condition=condition,
        noise_sigma=sigma, subsample_rho=rho, sampling_replicate=bundle_index,
    )
    input_trajectory = _trajectory_groups(row)["input"][0]
    times, observed = corrupt_trajectory(
        np.asarray(input_trajectory["times"], dtype=float),
        np.asarray(input_trajectory["trajectory"], dtype=float),
        sigma=float(sigma), rho=float(rho), seed=corruption_seed,
    )
    protocol = config["paper_protocol"]
    regressor = make_symbolic_regressor(
        model, rescale=bool(protocol["rescale"]), beam_size=beam_size,
        beam_temperature=float(protocol["beam_temperature"]), beam_type=str(protocol["beam_type"]),
        generation_seed=candidate_seed,
    )
    fit = fit_and_collect(regressor, times, observed, permutation_seed=candidate_seed)
    candidates = [
        _evaluate_candidate(row, tree, raw or "", index, regressor, penalty=penalty)
        for index, (tree, raw) in enumerate(zip(fit["trees"], fit["infixes"]))
    ]
    return sanitize_nonfinite({
        "cell_id": _cell_id(system_id, bundle_index, sigma, rho),
        "system_id": system_id, "family": row["family"], "dimension": row["dimension"],
        "split": "validation", "bundle_index": bundle_index,
        "seed_bundle": bundle, "noise_sigma": sigma, "subsample_rho": rho,
        "candidate_seed": candidate_seed, "corruption_seed": corruption_seed,
        "candidate_set_hash": _candidate_hash(fit["infixes"]),
        "n_candidates": len(candidates), "decode_wall_time_sec": fit["wall_time"],
        "input_trajectory_checksum": input_trajectory["checksum"],
        "true_formula": row["teacher_infix"], "true_prefix": row["teacher_prefix"],
        "true_structure": row["structure"], "candidates": candidates,
        "status": "complete",
    })


def _choose_lambda(cells: list[dict[str, Any]], lambdas: list[float], penalty: float) -> tuple[float, list[dict[str, Any]]]:
    audit = []
    for value in lambdas:
        rows = []
        for cell in cells:
            index = select_candidate(cell["candidates"], "multi_ic_complexity", penalty=penalty, complexity_lambda=value)
            if index is not None:
                rows.append(cell["candidates"][index])
        key = formula_selection_key(rows)
        audit.append({"lambda": value, "selection_key": list(key), "n_groups": len(rows)})
    chosen = max(audit, key=lambda row: (*row["selection_key"], -float(row["lambda"])))
    return float(chosen["lambda"]), audit


def _paired_p6(selections: list[dict[str, Any]], penalty: float) -> dict[str, Any]:
    by_key: dict[tuple[Any, ...], dict[str, dict[str, Any]]] = {}
    for row in selections:
        key = (row["system_id"], row["bundle_index"], row["noise_sigma"], row["subsample_rho"])
        by_key.setdefault(key, {})[row["selection_rule"]] = row
    per_system: dict[str, list[float]] = {}
    raw = []
    for key, rules in by_key.items():
        if "official_reconstruction" not in rules or "multi_ic" not in rules:
            continue
        official = robust_median(rules["official_reconstruction"]["trajectory_metrics"]["generalization_nrmse"], penalty=penalty)
        multi = robust_median(rules["multi_ic"]["trajectory_metrics"]["generalization_nrmse"], penalty=penalty)
        improvement = official - multi
        raw.append(improvement)
        per_system.setdefault(str(key[0]), []).append(improvement)
    clustered = np.asarray([np.mean(values) for values in per_system.values()], dtype=float)
    mean = float(np.mean(clustered)) if len(clustered) else None
    if len(clustered) >= 2:
        sem = float(stats.sem(clustered))
        half = float(stats.t.ppf(0.975, len(clustered) - 1) * sem)
        interval = [mean - half, mean + half]
    else:
        interval = [None, None]
    return {
        "estimand": "official_minus_multi_generalization_failure_aware_nrmse",
        "positive_means_multi_ic_improves": True, "n_cells": len(raw), "n_system_clusters": len(clustered),
        "mean_clustered_improvement": mean, "student_t_95_ci": interval,
        "prediction_P6": "supported" if interval[0] is not None and interval[0] > 0 else "not_supported",
    }


def _aggregate(cells: list[dict[str, Any]], config: dict[str, Any], out: Path, penalty: float) -> dict[str, Any]:
    chosen_lambda, lambda_audit = _choose_lambda(cells, [float(x) for x in config["selection"]["complexity_lambdas"]], penalty)
    selected = []
    groups = []
    failures = Counter()
    for cell in cells:
        candidates = cell["candidates"]
        selected_by_rule = {}
        for rule in RULES:
            index = select_candidate(candidates, rule, penalty=penalty, complexity_lambda=chosen_lambda)
            if index is None:
                failures["generation_empty"] += 1
                continue
            record = {key: cell[key] for key in (
                "cell_id", "system_id", "family", "dimension", "split", "bundle_index",
                "noise_sigma", "subsample_rho", "candidate_set_hash", "candidate_seed",
            )}
            record.update(candidates[index])
            record["selection_rule"] = rule
            record["selected"] = True
            record["diagnostic_oracle"] = rule == "structural_oracle"
            selected.append(record)
            selected_by_rule[rule] = index
        exact_in_beam = any(row["exponent_aware_skeleton_exact"] == 1.0 for row in candidates)
        if not exact_in_beam:
            failures["generation_failure"] += 1
        elif selected_by_rule.get("official_reconstruction") is not None and not candidates[selected_by_rule["official_reconstruction"]]["exponent_aware_skeleton_exact"]:
            failures["selection_failure_official"] += 1
        for row in candidates:
            for role in ("input", "selection", "generalization"):
                failures[f"{role}_integration_failure"] += sum(reason is not None for reason in row["trajectory_metrics"][f"{role}_failures"])
        unique_curve = []
        for k in (1, 10, 25, 50):
            subset = candidates[:k]
            finite = [float(row["normalized_ted"]) for row in subset if row.get("normalized_ted") is not None]
            unique_curve.append({
                "budget": k, "actual_candidates": len(subset),
                "unique_skeletons": len({row["candidate_formula_skeleton"] for row in subset if row.get("valid")}),
                "oracle_normalized_ted": min(finite) if finite else 1.0,
            })
        groups.append({
            "cell_id": cell["cell_id"], "system_id": cell["system_id"], "family": cell["family"],
            "bundle_index": cell["bundle_index"], "noise_sigma": cell["noise_sigma"], "subsample_rho": cell["subsample_rho"],
            "candidate_set_hash": cell["candidate_set_hash"], "n_candidates": len(candidates),
            "true_exponent_aware_skeleton_in_beam": exact_in_beam,
            "selected_indices": selected_by_rule, "budget_curve": unique_curve,
        })
    p6 = _paired_p6(selected, penalty)
    write_json(out / "all_candidates.json", sanitize_nonfinite([
        {**{key: cell[key] for key in ("cell_id", "system_id", "family", "dimension", "bundle_index", "noise_sigma", "subsample_rho", "candidate_set_hash")}, **candidate}
        for cell in cells for candidate in cell["candidates"]
    ]))
    write_json(out / "selected.json", sanitize_nonfinite(selected))
    write_json(out / "beam_groups.json", sanitize_nonfinite(groups))
    write_json(out / "lambda_selection.json", sanitize_nonfinite({"chosen_lambda": chosen_lambda, "audit": lambda_audit, "split": "validation"}))
    write_json(out / "p6_validation.json", sanitize_nonfinite(p6))
    write_json(out / "failure_funnel.json", dict(failures))
    return {
        "n_cells": len(cells), "n_candidates": sum(len(cell["candidates"]) for cell in cells),
        "n_selected_records": len(selected), "chosen_complexity_lambda": chosen_lambda,
        "true_exponent_aware_skeleton_in_beam_rate": float(np.mean([row["true_exponent_aware_skeleton_in_beam"] for row in groups])) if groups else 0.0,
        "failure_funnel": dict(failures), "p6_validation": p6,
    }


def main() -> int:
    args = parse_args()
    config = load_config()
    root = run_dir(args.run_id)
    phase2_manifest = read_json(root / "phase2" / "manifest.json", {})
    if phase2_manifest.get("status") != "complete":
        raise RuntimeError("Phase 2 is not complete")
    validation = read_json(root / "phase2" / "validation.json")
    if not isinstance(validation, list):
        raise RuntimeError("Phase 2 validation corpus missing")
    out = phase_dir(args.run_id, 3)
    cells_dir = out / "cells"
    cells_dir.mkdir(exist_ok=True)
    chosen_budget = budget(config, args.smoke)
    n_seeds = int(chosen_budget["n_seeds"])
    beam_size = int(chosen_budget["beam_size"])
    penalty = float(config["selection"]["trajectory_nrmse_failure_penalty"])
    device = select_device(allow_cpu=args.allow_cpu)
    model = load_odeformer_model(ROOT / str(config["odeformer_checkpoint"]), device=device)
    corruptions = [(float(sigma), float(rho)) for sigma in config["corruptions"]["noise_sigmas"] for rho in config["corruptions"]["subsample_rhos"]]
    jobs = [(row, bundle_index, sigma, rho) for bundle_index in range(n_seeds) for row in validation for sigma, rho in corruptions]
    limited = args.limit_cells is not None
    if limited:
        jobs = jobs[: int(args.limit_cells)]
    completed = []
    for job_index, (row, bundle_index, sigma, rho) in enumerate(jobs, 1):
        path = cells_dir / f"{_cell_id(row['system_id'], bundle_index, sigma, rho)}.json"
        cached = read_json(path)
        if isinstance(cached, dict) and cached.get("status") == "complete":
            completed.append(cached)
            continue
        cell = _run_cell(
            row, model=model, config=config, bundle=config["seed_bundles"][bundle_index],
            bundle_index=bundle_index, sigma=sigma, rho=rho, beam_size=beam_size, penalty=penalty,
        )
        write_json(path, cell)
        completed.append(cell)
        print(f"Phase3 cell {job_index}/{len(jobs)} {cell['cell_id']} candidates={cell['n_candidates']}", flush=True)
    summary = _aggregate(completed, config, out, penalty)
    expected = len(validation) * n_seeds * len(corruptions)
    go = {
        "all_validation_cells_complete": len(completed) == expected and not limited,
        "candidates_saved": summary["n_candidates"] > 0,
        "same_candidate_set_shared_by_rules": summary["n_selected_records"] == len(completed) * len(RULES),
        "test_not_accessed": True,
        "component_and_system_metrics_saved": summary["n_candidates"] > 0,
        "failure_funnel_saved": (out / "failure_funnel.json").is_file(),
    }
    status = "complete" if all(go.values()) else "incomplete"
    write_json(out / "summary.json", sanitize_nonfinite({**summary, "status": status, "go_conditions": go}))
    write_json(out / "go.json", go)
    write_manifest(
        out, 3, status, go_conditions=go, summary=summary, git=git_info(),
        phase2_validation_sha256=sha256_file(root / "phase2" / "validation.json"),
        test_accessed=False, beam_size=beam_size, n_seeds=n_seeds, corruption_cells=corruptions,
    )
    print(f"GPU_RUN5 Phase 3 {status}: cells={len(completed)}/{expected} candidates={summary['n_candidates']}")
    return 0 if status == "complete" else 1


if __name__ == "__main__":
    raise SystemExit(main())
