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
from time import perf_counter
from typing import Any

import numpy as np
from scipy import stats

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from gpu_run2_runtime import fingerprint_json, git_info, sha256_file, utc_now, write_json  # noqa: E402
from gpu_run3_runtime import software_versions  # noqa: E402
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


def _observed_trajectories(
    row: dict[str, Any], *, sigma: float, rho: float, bundle: dict[str, Any], bundle_index: int
) -> dict[str, list[dict[str, Any]]]:
    """Corrupt input/selection observations; leave generalization ICs evaluation-only."""
    output: dict[str, list[dict[str, Any]]] = {role: [] for role in ("input", "selection", "generalization")}
    for role, trajectories in _trajectory_groups(row).items():
        for trajectory in trajectories:
            seed = stable_problem_seed(
                int(bundle["corruption_seed"]), system_id=str(row["system_id"]),
                condition=f"{role}_{trajectory['role_index']}", noise_sigma=sigma,
                subsample_rho=rho, sampling_replicate=bundle_index,
            )
            true_times = np.asarray(trajectory["times"], dtype=float)
            true_values = np.asarray(trajectory["trajectory"], dtype=float)
            if role in {"input", "selection"}:
                times, values = corrupt_trajectory(
                    true_times, true_values, sigma=sigma, rho=rho, seed=seed
                )
            else:
                times, values = true_times, true_values
            output[role].append({
                "role": role, "role_index": trajectory["role_index"], "seed": seed,
                "times": times.tolist(), "observed_trajectory": values.tolist(),
                "initial_condition": values[0].tolist() if role in {"input", "selection"} else trajectory["initial_condition"],
                "source_checksum": trajectory["checksum"],
                "corrupted": role in {"input", "selection"},
            })
    return output


def _evaluate_candidate(
    row: dict[str, Any], observations: dict[str, list[dict[str, Any]]], tree: Any,
    raw: str, index: int, regressor: Any, *, penalty: float
) -> dict[str, Any]:
    formula = formula_metrics(row["teacher_infix"], raw)
    trajectory_metrics: dict[str, list[Any]] = {
        "input_nrmse": [], "selection_nrmse": [], "generalization_nrmse": [],
        "input_r2": [], "selection_r2": [], "generalization_r2": [],
        "input_failures": [], "selection_failures": [], "generalization_failures": [],
    }
    for role, trajectories in observations.items():
        for trajectory in trajectories:
            times = np.asarray(trajectory["times"], dtype=float)
            truth = np.asarray(trajectory["observed_trajectory"], dtype=float)
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
    cache_identity: dict[str, Any],
) -> dict[str, Any]:
    system_id = str(row["system_id"])
    condition = str(config["selection"]["candidate_seed_namespace"])
    candidate_seed = stable_problem_seed(
        int(bundle["candidate_seed"]), system_id=system_id, condition=condition,
        noise_sigma=sigma, subsample_rho=rho, sampling_replicate=bundle_index,
    )
    observations = _observed_trajectories(
        row, sigma=sigma, rho=rho, bundle=bundle, bundle_index=bundle_index
    )
    input_trajectory = observations["input"][0]
    times = np.asarray(input_trajectory["times"], dtype=float)
    observed = np.asarray(input_trajectory["observed_trajectory"], dtype=float)
    protocol = config["paper_protocol"]
    regressor = make_symbolic_regressor(
        model, rescale=bool(protocol["rescale"]), beam_size=beam_size,
        beam_temperature=float(protocol["beam_temperature"]), beam_type=str(protocol["beam_type"]),
        generation_seed=candidate_seed,
    )
    fit = fit_and_collect(regressor, times, observed, permutation_seed=candidate_seed)
    candidates = [
        _evaluate_candidate(row, observations, tree, raw or "", index, regressor, penalty=penalty)
        for index, (tree, raw) in enumerate(zip(fit["trees"], fit["infixes"]))
    ]
    return sanitize_nonfinite({
        "cell_id": _cell_id(system_id, bundle_index, sigma, rho),
        "system_id": system_id, "family": row["family"], "dimension": row["dimension"],
        "split": "validation", "bundle_index": bundle_index,
        "seed_bundle": bundle, "noise_sigma": sigma, "subsample_rho": rho,
        "candidate_seed": candidate_seed,
        "candidate_set_hash": _candidate_hash(fit["infixes"]),
        "n_candidates": len(candidates), "decode_wall_time_sec": fit["wall_time"],
        "input_trajectory_checksum": input_trajectory["source_checksum"],
        "observations": observations,
        "true_formula": row["teacher_infix"], "true_prefix": row["teacher_prefix"],
        "true_structure": row["structure"], "candidates": candidates,
        "cache_identity": cache_identity, "status": "complete",
    })


def _choose_lambda(cells: list[dict[str, Any]], lambdas: list[float], penalty: float) -> tuple[float, list[dict[str, Any]]]:
    audit = []
    for value in lambdas:
        rows = []
        for cell in cells:
            index = select_candidate(cell["candidates"], "multi_ic_complexity", penalty=penalty, complexity_lambda=value)
            if index is not None:
                rows.append({
                    **cell["candidates"][index], "system_id": cell["system_id"],
                    "bundle_index": cell["bundle_index"], "noise_sigma": cell["noise_sigma"],
                    "subsample_rho": cell["subsample_rho"],
                })
            else:
                n_components = int(cell["dimension"])
                rows.append({
                    "system_id": cell["system_id"], "bundle_index": cell["bundle_index"],
                    "noise_sigma": cell["noise_sigma"], "subsample_rho": cell["subsample_rho"],
                    "component_exponent_aware_skeleton_exact": [0.0] * n_components,
                    "component_normalized_variable_aware_ted": [1.0] * n_components,
                    "component_valid": [False] * n_components,
                    "empty_candidate_placeholder": True,
                })
        key = formula_selection_key(rows)
        audit.append({
            "lambda": value, "selection_key": list(key), "n_cells": len(rows),
            "n_empty_candidate_placeholders": sum(bool(row.get("empty_candidate_placeholder")) for row in rows),
        })
    chosen = max(audit, key=lambda row: (*row["selection_key"], -float(row["lambda"])))
    return float(chosen["lambda"]), audit


def _paired_p6(selections: list[dict[str, Any]], cells: list[dict[str, Any]], penalty: float) -> dict[str, Any]:
    by_key: dict[tuple[Any, ...], dict[str, dict[str, Any]]] = {}
    for row in selections:
        key = (row["system_id"], row["bundle_index"], row["noise_sigma"], row["subsample_rho"])
        by_key.setdefault(key, {})[row["selection_rule"]] = row
    per_system: dict[str, list[float]] = {}
    per_family: dict[str, dict[str, list[float]]] = {}
    per_seed: dict[int, list[float]] = {}
    raw = []
    for cell in cells:
        key = (cell["system_id"], cell["bundle_index"], cell["noise_sigma"], cell["subsample_rho"])
        rules = by_key.get(key, {})
        official_row = rules.get("official_reconstruction")
        multi_row = rules.get("multi_ic")
        official = (
            robust_median(official_row["trajectory_metrics"]["generalization_nrmse"], penalty=penalty)
            if official_row is not None else float(penalty)
        )
        multi = (
            robust_median(multi_row["trajectory_metrics"]["generalization_nrmse"], penalty=penalty)
            if multi_row is not None else float(penalty)
        )
        registered_difference = multi - official
        detail = {
            "system_id": str(key[0]), "bundle_index": int(key[1]),
            "noise_sigma": float(key[2]), "subsample_rho": float(key[3]),
            "family": cell["family"], "missing_candidate_pair": official_row is None or multi_row is None,
            "multi_ic_nrmse": multi, "official_reconstruction_nrmse": official,
            "multi_ic_minus_single_ic": registered_difference,
        }
        raw.append(detail)
        per_system.setdefault(str(key[0]), []).append(registered_difference)
        family = str(detail["family"])
        per_family.setdefault(family, {}).setdefault(str(key[0]), []).append(registered_difference)
        per_seed.setdefault(int(key[1]), []).append(registered_difference)
    clustered = np.asarray([np.mean(values) for values in per_system.values()], dtype=float)
    mean = float(np.mean(clustered)) if len(clustered) else None
    if len(clustered) >= 2:
        sem = float(stats.sem(clustered))
        half = float(stats.t.ppf(0.975, len(clustered) - 1) * sem)
        interval = [mean - half, mean + half]
    else:
        interval = [None, None]
    return {
        "estimand": "multi_ic_minus_single_ic_generalization_failure_aware_nrmse",
        "comparator": "official_reconstruction", "negative_means_multi_ic_improves": True,
        "n_cells": len(raw), "n_system_clusters": len(clustered),
        "mean_clustered_difference": mean, "student_t_95_ci": interval,
        "ci95_upper": interval[1],
        "prediction_P6": "supported" if interval[1] is not None and interval[1] < 0 else "not_supported",
        "paired_cell_differences": raw,
        "per_system_mean_difference": {key: float(np.mean(value)) for key, value in per_system.items()},
        "per_family_macro_difference": {
            family: float(np.mean([np.mean(values) for values in systems.values()]))
            for family, systems in per_family.items()
        },
        "per_seed_mean_difference": {str(key): float(np.mean(value)) for key, value in per_seed.items()},
    }


def _aggregate(cells: list[dict[str, Any]], config: dict[str, Any], out: Path, penalty: float) -> dict[str, Any]:
    chosen_lambda, lambda_audit = _choose_lambda(cells, [float(x) for x in config["selection"]["complexity_lambdas"]], penalty)
    selected = []
    groups = []
    failures = Counter()
    failure_records = []
    for cell in cells:
        candidates = cell["candidates"]
        selected_by_rule = {}
        if not candidates:
            failures["generation_empty"] += 1
            failure_records.append({
                "cell_id": cell["cell_id"], "system_id": cell["system_id"], "family": cell["family"],
                "bundle_index": cell["bundle_index"], "noise_sigma": cell["noise_sigma"],
                "subsample_rho": cell["subsample_rho"], "stage": "generation_failure",
                "reason": "empty_candidate_set", "component_index": None,
            })
        shortfall = max(int(cell["cache_identity"]["beam_size"]) - len(candidates), 0)
        if shortfall:
            failures["candidate_return_shortfall"] += shortfall
            failure_records.append({
                "cell_id": cell["cell_id"], "system_id": cell["system_id"], "family": cell["family"],
                "bundle_index": cell["bundle_index"], "noise_sigma": cell["noise_sigma"],
                "subsample_rho": cell["subsample_rho"], "stage": "generation_failure",
                "reason": "candidate_return_shortfall", "shortfall": shortfall, "component_index": None,
            })
        for rule in RULES:
            index = select_candidate(candidates, rule, penalty=penalty, complexity_lambda=chosen_lambda)
            if index is None:
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
        component_support = [
            any(
                component_index < len(candidate.get("component_exponent_aware_skeleton_exact", []))
                and candidate["component_exponent_aware_skeleton_exact"][component_index] == 1.0
                for candidate in candidates
            )
            for component_index in range(int(cell["dimension"]))
        ]
        for component_index, supported in enumerate(component_support):
            if not supported:
                failures["component_generation_failure"] += 1
                failure_records.append({
                    "cell_id": cell["cell_id"], "system_id": cell["system_id"], "family": cell["family"],
                    "bundle_index": cell["bundle_index"], "noise_sigma": cell["noise_sigma"],
                    "subsample_rho": cell["subsample_rho"], "stage": "generation_failure",
                    "reason": "true_component_exponent_aware_skeleton_absent",
                    "component_index": component_index,
                })
            else:
                for rule, selected_index in selected_by_rule.items():
                    values = candidates[selected_index].get("component_exponent_aware_skeleton_exact", [])
                    if component_index >= len(values) or values[component_index] != 1.0:
                        failures[f"component_selection_failure_{rule}"] += 1
                        failure_records.append({
                            "cell_id": cell["cell_id"], "system_id": cell["system_id"], "family": cell["family"],
                            "bundle_index": cell["bundle_index"], "noise_sigma": cell["noise_sigma"],
                            "subsample_rho": cell["subsample_rho"], "stage": "selection_failure",
                            "reason": "true_component_in_beam_but_not_selected", "selection_rule": rule,
                            "candidate_index": selected_index, "component_index": component_index,
                        })
        if not exact_in_beam:
            failures["generation_failure"] += 1
            failure_records.append({
                "cell_id": cell["cell_id"], "system_id": cell["system_id"], "family": cell["family"],
                "bundle_index": cell["bundle_index"], "noise_sigma": cell["noise_sigma"],
                "subsample_rho": cell["subsample_rho"], "stage": "generation_failure",
                "reason": "true_exponent_aware_skeleton_absent", "component_index": None,
            })
        else:
            for rule, index in selected_by_rule.items():
                if not candidates[index]["exponent_aware_skeleton_exact"]:
                    failures[f"selection_failure_{rule}"] += 1
                    failure_records.append({
                        "cell_id": cell["cell_id"], "system_id": cell["system_id"], "family": cell["family"],
                        "bundle_index": cell["bundle_index"], "noise_sigma": cell["noise_sigma"],
                        "subsample_rho": cell["subsample_rho"], "stage": "selection_failure",
                        "reason": "truth_in_beam_but_not_selected", "selection_rule": rule,
                        "component_index": None,
                    })
        for row in candidates:
            if row.get("normalized_ted") is None:
                failures["metric_failure"] += 1
                failure_records.append({
                    "cell_id": cell["cell_id"], "system_id": cell["system_id"], "family": cell["family"],
                    "bundle_index": cell["bundle_index"], "noise_sigma": cell["noise_sigma"],
                    "subsample_rho": cell["subsample_rho"], "stage": "metric_failure",
                    "reason": row.get("failure_reason") or "nonfinite_metric",
                    "candidate_index": row["candidate_index"], "component_index": None,
                })
            for component_index, component_valid in enumerate(row.get("component_valid", [])):
                component_metric = row.get("component_normalized_variable_aware_ted", [])
                if not component_valid or component_index >= len(component_metric) or component_metric[component_index] is None:
                    failures["component_metric_failure"] += 1
                    reasons = row.get("component_failure_reason", [])
                    failure_records.append({
                        "cell_id": cell["cell_id"], "system_id": cell["system_id"], "family": cell["family"],
                        "bundle_index": cell["bundle_index"], "noise_sigma": cell["noise_sigma"],
                        "subsample_rho": cell["subsample_rho"], "stage": "metric_failure",
                        "reason": reasons[component_index] if component_index < len(reasons) else "missing_component_metric",
                        "candidate_index": row["candidate_index"], "component_index": component_index,
                    })
            for role in ("input", "selection", "generalization"):
                for trajectory_index, reason in enumerate(row["trajectory_metrics"][f"{role}_failures"]):
                    if reason is not None:
                        failures[f"{role}_integration_failure"] += 1
                        failure_records.append({
                            "cell_id": cell["cell_id"], "system_id": cell["system_id"], "family": cell["family"],
                            "bundle_index": cell["bundle_index"], "noise_sigma": cell["noise_sigma"],
                            "subsample_rho": cell["subsample_rho"], "stage": "integration_failure",
                            "reason": reason, "candidate_index": row["candidate_index"],
                            "trajectory_role": role, "trajectory_index": trajectory_index,
                            "component_index": None,
                        })
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
            "candidate_set_hash": cell["candidate_set_hash"], "candidate_seed": cell["candidate_seed"],
            "n_candidates": len(candidates),
            "true_exponent_aware_skeleton_in_beam": exact_in_beam,
            "component_true_exponent_aware_skeleton_in_beam": component_support,
            "selected_indices": selected_by_rule, "budget_curve": unique_curve,
        })
    p6 = _paired_p6(selected, cells, penalty)
    write_json(out / "all_candidates.json", sanitize_nonfinite([
        {**{key: cell[key] for key in (
            "cell_id", "system_id", "family", "dimension", "split", "bundle_index",
            "noise_sigma", "subsample_rho", "candidate_set_hash", "candidate_seed",
            "true_formula", "true_prefix",
        )}, **candidate}
        for cell in cells for candidate in cell["candidates"]
    ]))
    write_json(out / "selected.json", sanitize_nonfinite(selected))
    write_json(out / "beam_groups.json", sanitize_nonfinite(groups))
    write_json(out / "lambda_selection.json", sanitize_nonfinite({"chosen_lambda": chosen_lambda, "audit": lambda_audit, "split": "validation"}))
    write_json(out / "p6_validation.json", sanitize_nonfinite(p6))
    write_json(out / "failure_funnel.json", dict(failures))
    write_json(out / "failure_funnel_records.json", sanitize_nonfinite(failure_records))
    return {
        "n_cells": len(cells), "n_candidates": sum(len(cell["candidates"]) for cell in cells),
        "n_selected_records": len(selected), "chosen_complexity_lambda": chosen_lambda,
        "true_exponent_aware_skeleton_in_beam_rate": float(np.mean([row["true_exponent_aware_skeleton_in_beam"] for row in groups])) if groups else 0.0,
        "failure_funnel": dict(failures), "n_failure_records": len(failure_records), "p6_validation": p6,
    }


def main() -> int:
    started_utc = utc_now()
    started_clock = perf_counter()
    args = parse_args()
    config = load_config()
    root = run_dir(args.run_id)
    phase2_manifest_path = root / "phase2" / "manifest.json"
    phase2_manifest = read_json(phase2_manifest_path, {})
    validation_path = root / "phase2" / "validation.json"
    if phase2_manifest.get("status") != "complete" or not all(phase2_manifest.get("go_conditions", {}).values()):
        raise RuntimeError("Phase 2 is not complete with every Go condition true")
    if phase2_manifest.get("git", {}).get("status_short"):
        raise RuntimeError("Phase 2 provenance is dirty")
    if phase2_manifest.get("artifact_sha256", {}).get("validation.json") != sha256_file(validation_path):
        raise RuntimeError("Phase 2 validation hash does not match its manifest")
    validation = read_json(validation_path)
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
    checkpoint = ROOT / str(config["odeformer_checkpoint"])
    checkpoint_sha = sha256_file(checkpoint)
    model = load_odeformer_model(checkpoint, device=device)
    git = git_info()
    if git["status_short"]:
        raise RuntimeError(f"authoritative Phase 3 requires a clean worktree: {git['status_short']}")
    environment = software_versions()
    cache_identity = {
        "schema_version": "gpu_run5_phase3_cell_v2_observed_reranking",
        "git_commit": git["commit"], "git_status_short": git["status_short"],
        "config_fingerprint": fingerprint_json(config), "checkpoint_sha256": checkpoint_sha,
        "phase2_validation_sha256": sha256_file(validation_path),
        "beam_size": beam_size, "beam_temperature": float(config["paper_protocol"]["beam_temperature"]),
        "beam_type": str(config["paper_protocol"]["beam_type"]),
        "rescale": bool(config["paper_protocol"]["rescale"]), "failure_penalty": penalty,
        "candidate_seed_namespace": str(config["selection"]["candidate_seed_namespace"]),
        "device": device, "environment_fingerprint": fingerprint_json(environment),
    }
    corruptions = [(float(sigma), float(rho)) for sigma in config["corruptions"]["noise_sigmas"] for rho in config["corruptions"]["subsample_rhos"]]
    jobs = [(row, bundle_index, sigma, rho) for bundle_index in range(n_seeds) for row in validation for sigma, rho in corruptions]
    limited = args.limit_cells is not None
    if limited:
        jobs = jobs[: int(args.limit_cells)]
    completed = []
    for job_index, (row, bundle_index, sigma, rho) in enumerate(jobs, 1):
        path = cells_dir / f"{_cell_id(row['system_id'], bundle_index, sigma, rho)}.json"
        cached = read_json(path)
        if isinstance(cached, dict) and cached.get("status") == "complete" and cached.get("cache_identity") == cache_identity:
            completed.append(cached)
            continue
        cell = _run_cell(
            row, model=model, config=config, bundle=config["seed_bundles"][bundle_index],
            bundle_index=bundle_index, sigma=sigma, rho=rho, beam_size=beam_size, penalty=penalty,
            cache_identity=cache_identity,
        )
        write_json(path, cell)
        completed.append(cell)
        print(f"Phase3 cell {job_index}/{len(jobs)} {cell['cell_id']} candidates={cell['n_candidates']}", flush=True)
    summary = _aggregate(completed, config, out, penalty)
    expected = len(validation) * n_seeds * len(corruptions)
    candidate_schema_keys = {
        "component_exponent_aware_skeleton_exact", "component_normalized_variable_aware_ted",
        "component_valid", "component_failure_reason", "normalized_variable_aware_ted",
        "trajectory_metrics", "candidate_formula_raw",
    }
    schema_ok = all(candidate_schema_keys.issubset(candidate) for cell in completed for candidate in cell["candidates"])
    cache_ok = all(cell.get("cache_identity") == cache_identity for cell in completed)
    go = {
        "all_validation_cells_complete": len(completed) == expected and not limited,
        "candidate_sets_saved_including_empty": all(
            isinstance(cell.get("candidates"), list) and isinstance(cell.get("candidate_set_hash"), str)
            for cell in completed
        ),
        "each_cell_decoded_once_and_rules_share_candidate_hash": cache_ok,
        "test_not_accessed": True,
        "component_and_system_metrics_saved": schema_ok,
        "p6_includes_every_expected_cell": summary["p6_validation"]["n_cells"] == expected,
        "failure_funnel_saved": (out / "failure_funnel.json").is_file() and (out / "failure_funnel_records.json").is_file(),
    }
    status = "complete" if all(go.values()) else "incomplete"
    write_json(out / "summary.json", sanitize_nonfinite({**summary, "status": status, "go_conditions": go}))
    write_json(out / "go.json", go)
    artifact_names = [
        "all_candidates.json", "selected.json", "beam_groups.json", "lambda_selection.json",
        "p6_validation.json", "failure_funnel.json", "failure_funnel_records.json", "summary.json", "go.json",
    ]
    write_json(out / "config_snapshot.json", config)
    artifact_names.append("config_snapshot.json")
    finished_utc = utc_now()
    write_manifest(
        out, 3, status, go_conditions=go, summary=summary, git=git_info(),
        started_utc=started_utc, finished_utc=finished_utc, wall_time_sec=perf_counter() - started_clock,
        cache_identity=cache_identity, phase2_manifest_sha256=sha256_file(phase2_manifest_path),
        phase2_validation_sha256=sha256_file(validation_path), checkpoint={"path": str(checkpoint), "sha256": checkpoint_sha},
        config_fingerprint=fingerprint_json(config), environment=environment, device=device,
        test_accessed=False, beam_size=beam_size, n_seeds=n_seeds, corruption_cells=corruptions,
        selection_rules=list(RULES), failure_penalty=penalty,
        artifact_sha256={name: sha256_file(out / name) for name in artifact_names},
    )
    print(f"GPU_RUN5 Phase 3 {status}: cells={len(completed)}/{expected} candidates={summary['n_candidates']}")
    return 0 if status == "complete" else 1


if __name__ == "__main__":
    raise SystemExit(main())
