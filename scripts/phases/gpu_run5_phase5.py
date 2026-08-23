"""GPU_RUN5 Phase 5: causal interventions and post-intervention beam decode."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
from contextlib import nullcontext
from pathlib import Path
from time import perf_counter
from typing import Any, ContextManager

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from gpu_run2_runtime import (  # noqa: E402
    fingerprint_json, git_info, sha256_file, utc_now, write_json as _write_json,
)
from gpu_run3_runtime import software_versions  # noqa: E402
from gpu_run4.architecture import inventory_odeformer  # noqa: E402
from gpu_run4.hooks import identity_control_hook, zero_residual_block  # noqa: E402
from gpu_run4.inference import fit_and_collect, integrate_candidate  # noqa: E402
from gpu_run4.training import teacher_forcing_loss  # noqa: E402
from gpu_run4.trajectories import r2_score  # noqa: E402
from gpu_run4_runtime import load_odeformer_model, make_symbolic_regressor, select_device  # noqa: E402
from gpu_run5.config import (  # noqa: E402
    budget, load_config, phase_dir, read_json, run_dir, sanitize_nonfinite, write_manifest,
)
from gpu_run5.evaluation import formula_metrics, trajectory_nrmse  # noqa: E402
from gpu_run5.interventions import (  # noqa: E402
    check_mean_alpha_one_equivalence, p5_damage_spearman,
    post_block_mean_intervention, rank_causal_formula_damage,
    select_interpolation_strength,
)
from gpu_run5.seeding import stable_problem_seed  # noqa: E402


def write_json(path: Path, payload: Any) -> Path:
    """Write strict JSON: non-finite values become explicit nulls."""
    return _write_json(path, sanitize_nonfinite(payload))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", default=os.environ.get("LANSR_RUN_ID"))
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--allow-cpu", action="store_true")
    return parser.parse_args()


def _candidate_hash(infixes: list[str | None]) -> str:
    encoded = json.dumps(infixes, ensure_ascii=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def _official_arrays(row: dict[str, Any]) -> tuple[np.ndarray, np.ndarray, list[str]]:
    return (
        np.asarray(row["times"], dtype=float),
        np.asarray(row["trajectory"], dtype=float),
        list(row["tree_encoded"]),
    )


def _role_rows(row: dict[str, Any], role: str) -> list[dict[str, Any]]:
    return sorted(
        [item for item in row["trajectories"] if item["role"] == role],
        key=lambda item: int(item["role_index"]),
    )


def _grn_arrays(row: dict[str, Any]) -> tuple[np.ndarray, np.ndarray, list[str]]:
    item = _role_rows(row, "input")[0]
    return (
        np.asarray(item["times"], dtype=float),
        np.asarray(item["trajectory"], dtype=float),
        list(row["tree_encoded"]),
    )


def _mean_ce(
    model: Any,
    rows: list[dict[str, Any]],
    arrays,
    context: ContextManager[Any],
) -> list[float]:
    values: list[float] = []
    model.eval()
    with context, torch.no_grad():
        for row in rows:
            times, trajectory, tree = arrays(row)
            value = teacher_forcing_loss(model, times, trajectory, tree)
            values.append(float(value.detach().cpu()))
    return values


def _post_context(model: Any, layer: str, mean: np.ndarray, alpha: float) -> ContextManager[Any]:
    return post_block_mean_intervention(model, layer, mean, alpha=alpha)


def _load_corpus_means(path: Path, layers: list[str]) -> tuple[dict[str, np.ndarray], int]:
    with np.load(path, allow_pickle=False) as archive:
        counts = {int(np.asarray(archive[f"expression_features__{layer}"]).shape[0]) for layer in layers}
        means = {
            layer: np.asarray(archive[f"expression_features__{layer}"], dtype=np.float32).mean(axis=0)
            for layer in layers
        }
    if set(means) != set(layers) or any(value.ndim != 1 or not np.isfinite(value).all() for value in means.values()):
        raise RuntimeError("Phase 4 official-train corpus means are incomplete or non-finite")
    if len(counts) != 1:
        raise RuntimeError(f"Phase 4 feature formula counts disagree: {sorted(counts)}")
    return means, counts.pop()


def _make_regressor(model: Any, config: dict[str, Any], beam_size: int, seed: int) -> Any:
    protocol = config["paper_protocol"]
    return make_symbolic_regressor(
        model,
        rescale=bool(protocol["rescale"]),
        beam_size=int(beam_size),
        beam_temperature=float(protocol["beam_temperature"]),
        beam_type=str(protocol["beam_type"]),
        generation_seed=int(seed),
    )


def _decode_infixes(
    model: Any,
    config: dict[str, Any],
    times: np.ndarray,
    trajectory: np.ndarray,
    *,
    seed: int,
    beam_size: int,
    context: ContextManager[Any],
) -> dict[str, Any]:
    regressor = _make_regressor(model, config, beam_size, seed)
    with context:
        fit = fit_and_collect(regressor, times, trajectory, permutation_seed=seed)
    return {**fit, "regressor": regressor}


def _finite_r2(value: float | None, penalty: float) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return float(penalty)
    return min(max(numeric, float(penalty)), 1.0) if math.isfinite(numeric) else float(penalty)


def _condition_context(
    model: Any,
    condition: str,
    means: dict[str, np.ndarray],
    alpha: float,
) -> ContextManager[Any]:
    if condition == "baseline":
        return nullcontext()
    method, layer = condition.split(":", 1)
    if method == "interpolation":
        return _post_context(model, layer, means[layer], alpha)
    if method == "zero":
        return zero_residual_block(model, layer)
    raise ValueError(f"unknown intervention condition: {condition}")


def _paired_candidate_seed(
    row: dict[str, Any], config: dict[str, Any], bundle_index: int,
) -> int:
    bundle = config["seed_bundles"][bundle_index]
    return stable_problem_seed(
        int(bundle["candidate_seed"]),
        system_id=str(row["system_id"]),
        condition="gpu_run5_phase5_paired_intervention_decode_v1",
        noise_sigma=0.0,
        subsample_rho=0.0,
        sampling_replicate=bundle_index,
    )


def _cell_identity(
    base: dict[str, Any], row: dict[str, Any], bundle_index: int,
    condition: str, candidate_seed: int,
) -> dict[str, Any]:
    input_row = _role_rows(row, "input")[0]
    return {
        **base,
        "system_id": str(row["system_id"]), "bundle_index": int(bundle_index),
        "condition": condition, "candidate_seed": int(candidate_seed),
        "input_trajectory_checksum": input_row["checksum"],
    }


def _decode_cell(
    row: dict[str, Any],
    *,
    model: Any,
    config: dict[str, Any],
    means: dict[str, np.ndarray],
    alpha: float,
    condition: str,
    bundle_index: int,
    beam_size: int,
    r2_penalty: float,
    nrmse_penalty: float,
    cache_identity: dict[str, Any],
) -> dict[str, Any]:
    system_id = str(row["system_id"])
    candidate_seed = int(cache_identity["candidate_seed"])
    expected_identity = _cell_identity(
        {key: value for key, value in cache_identity.items() if key not in {
            "system_id", "bundle_index", "condition", "candidate_seed", "input_trajectory_checksum",
        }},
        row, bundle_index, condition, candidate_seed,
    )
    if expected_identity != cache_identity or candidate_seed != _paired_candidate_seed(row, config, bundle_index):
        raise RuntimeError("cell identity or paired candidate seed mismatch")
    input_row = _role_rows(row, "input")[0]
    times = np.asarray(input_row["times"], dtype=float)
    trajectory = np.asarray(input_row["trajectory"], dtype=float)
    decode_started = perf_counter()
    generation_failure = None
    try:
        fit = _decode_infixes(
            model, config, times, trajectory, seed=candidate_seed, beam_size=beam_size,
            context=_condition_context(model, condition, means, alpha),
        )
    except torch.cuda.OutOfMemoryError:
        raise
    except RuntimeError as exc:
        if "out of memory" in str(exc).lower():
            raise
        generation_failure = f"{type(exc).__name__}:{exc}"
        fit = {"trees": [], "infixes": [], "wall_time": perf_counter() - decode_started,
               "permutations": [], "regressor": None}
    except Exception as exc:
        generation_failure = f"{type(exc).__name__}:{exc}"
        fit = {"trees": [], "infixes": [], "wall_time": perf_counter() - decode_started,
               "permutations": [], "regressor": None}
    candidates = []
    for index, raw in enumerate(fit["infixes"]):
        try:
            metrics = formula_metrics(str(row["teacher_infix"]), raw or "")
        except Exception as exc:
            metrics = formula_metrics(str(row["teacher_infix"]), "")
            metrics["failure_reason"] = f"{type(exc).__name__}:{exc}"
        candidates.append({"candidate_index": index, "candidate_formula_raw": raw or "", **metrics})
    if candidates:
        selected = dict(candidates[0])
        selected_tree = fit["trees"][0]
    else:
        selected = {
            "candidate_index": None,
            "candidate_formula_raw": "",
            **formula_metrics(str(row["teacher_infix"]), ""),
        }
        selected["failure_reason"] = generation_failure or selected.get("failure_reason") or "EmptyBeam"
        selected_tree = None
    trajectory_metrics: dict[str, Any] = {
        "reconstruction_r2": None,
        "reconstruction_r2_failure_aware": r2_penalty,
        "reconstruction_nrmse": nrmse_penalty,
        "reconstruction_failure": (generation_failure or "EmptyBeam") if selected_tree is None else None,
        "generalization_r2": [], "generalization_r2_failure_aware": [],
        "generalization_nrmse": [], "generalization_failures": [],
    }
    if selected_tree is not None:
        predicted, failure = integrate_candidate(
            fit["regressor"], times, trajectory[0], selected_tree, timeout_sec=10.0
        )
        raw_r2 = r2_score(trajectory, predicted)
        trajectory_metrics.update({
            "reconstruction_r2": raw_r2 if math.isfinite(raw_r2) else None,
            "reconstruction_r2_failure_aware": _finite_r2(raw_r2, r2_penalty),
            "reconstruction_nrmse": trajectory_nrmse(trajectory, predicted, penalty=nrmse_penalty),
            "reconstruction_failure": failure,
        })
    for item in _role_rows(row, "generalization"):
        target_times = np.asarray(item["times"], dtype=float)
        target = np.asarray(item["trajectory"], dtype=float)
        if selected_tree is None:
            predicted, failure = None, generation_failure or "EmptyBeam"
        else:
            predicted, failure = integrate_candidate(
                fit["regressor"], target_times, item["initial_condition"], selected_tree, timeout_sec=10.0
            )
        raw_r2 = r2_score(target, predicted)
        trajectory_metrics["generalization_r2"].append(raw_r2 if math.isfinite(raw_r2) else None)
        trajectory_metrics["generalization_r2_failure_aware"].append(_finite_r2(raw_r2, r2_penalty))
        trajectory_metrics["generalization_nrmse"].append(
            trajectory_nrmse(target, predicted, penalty=nrmse_penalty)
        )
        trajectory_metrics["generalization_failures"].append(failure)
    unique_skeletons = {
        str(candidate.get("candidate_exponent_aware_skeleton") or "")
        for candidate in candidates if candidate.get("candidate_exponent_aware_skeleton")
    }
    return sanitize_nonfinite({
        "cell_id": f"{system_id}_b{bundle_index}_{condition.replace(':', '_')}",
        "system_id": system_id, "family": row["family"], "dimension": int(row["dimension"]),
        "condition": condition, "bundle_index": bundle_index, "candidate_seed": candidate_seed,
        "true_formula": row["teacher_infix"], "true_prefix": row["teacher_prefix"],
        "variable_to_gene": row.get("variable_to_gene", {}),
        "input_trajectory_checksum": input_row["checksum"],
        "n_candidates": len(candidates), "beam_size": beam_size,
        "generation_failure": generation_failure,
        "candidate_set_hash": _candidate_hash(fit["infixes"]),
        "decode_wall_time_sec": fit["wall_time"],
        "permutation_sha256": fingerprint_json(fit["permutations"]),
        "unique_exponent_aware_skeletons": len(unique_skeletons),
        "candidates": candidates, "selected": selected, "trajectory_metrics": trajectory_metrics,
        "cache_identity": cache_identity, "status": "complete",
    })


def _cached_cell(path: Path, identity: dict[str, Any], build) -> dict[str, Any]:
    cached = read_json(path)
    if cached is not None:
        if cached.get("cache_identity") != identity or cached.get("status") != "complete":
            raise RuntimeError(f"cache identity mismatch: {path}")
        return cached
    value = build()
    path.parent.mkdir(parents=True, exist_ok=True)
    write_json(path, value)
    return value


def _cell_score(cell: dict[str, Any]) -> dict[str, float]:
    selected = cell["selected"]
    exact = selected.get("component_exponent_aware_skeleton_exact") or [0.0] * int(cell["dimension"])
    ted = selected.get("component_normalized_variable_aware_ted") or [1.0] * int(cell["dimension"])
    valid = selected.get("component_valid") or [False] * int(cell["dimension"])
    gen = cell["trajectory_metrics"].get("generalization_r2_failure_aware") or [-10.0]
    return {
        "exact": float(np.mean(exact)), "ted": float(np.mean(ted)),
        "valid": float(np.mean(valid)), "gen_r2": float(np.mean(gen)),
    }


def _layer_effects(
    cells: list[dict[str, Any]],
    ce_records: list[dict[str, Any]],
    layers: list[str],
    *,
    condition_method: str = "interpolation",
    include_ce: bool = True,
) -> dict[str, dict[str, Any]]:
    baseline = {
        (row["system_id"], int(row["bundle_index"])): row
        for row in cells if row["condition"] == "baseline"
    }
    ce_baseline = {row["system_id"]: float(row["ce"]) for row in ce_records if row["condition"] == "baseline"}
    ce_layer = {
        (row["system_id"], row["layer"]): float(row["ce"])
        for row in ce_records if row["condition"] == "interpolation"
    }
    output = {}
    for layer in layers:
        differences = {key: [] for key in (
            "component_exact_loss", "failure_aware_ted_increase", "component_valid_loss",
            "generalization_r2_loss",
        )}
        for row in cells:
            if row["condition"] != f"{condition_method}:{layer}":
                continue
            base = baseline[(row["system_id"], int(row["bundle_index"]))]
            left, right = _cell_score(base), _cell_score(row)
            differences["component_exact_loss"].append(left["exact"] - right["exact"])
            differences["failure_aware_ted_increase"].append(right["ted"] - left["ted"])
            differences["component_valid_loss"].append(left["valid"] - right["valid"])
            differences["generalization_r2_loss"].append(left["gen_r2"] - right["gen_r2"])
        ce_damage = (
            [ce_layer[(system_id, layer)] - value for system_id, value in ce_baseline.items()]
            if include_ce else []
        )
        output[layer] = {
            "damage_ce": float(np.median(ce_damage)) if ce_damage else None,
            **{key: float(np.median(values)) for key, values in differences.items()},
            "n_formula_pairs": len(differences["failure_aware_ted_increase"]),
            "n_ce_pairs": len(ce_damage),
        }
    return output


def _failure_funnel(cells: list[dict[str, Any]]) -> dict[str, Any]:
    selected = [row["selected"] for row in cells]
    failures: dict[str, int] = {}
    for row in selected:
        reason = row.get("failure_reason") or "none"
        failures[reason] = failures.get(reason, 0) + 1
    return {
        "n_cells": len(cells), "empty_beam": sum(row["n_candidates"] == 0 for row in cells),
        "beam_shortfall": sum(row["n_candidates"] < row["beam_size"] for row in cells),
        "selected_valid": sum(bool(row.get("valid")) for row in selected),
        "selected_valid_rate": float(np.mean([bool(row.get("valid")) for row in selected])) if selected else 0.0,
        "selected_failure_reasons": failures,
    }


def _coverage_audit(
    cells: list[dict[str, Any]],
    rows: list[dict[str, Any]],
    conditions: list[str],
    *,
    n_bundles: int,
    beam_size: int,
    config: dict[str, Any],
) -> dict[str, Any]:
    expected = {
        (str(row["system_id"]), bundle_index, condition)
        for row in rows for bundle_index in range(n_bundles) for condition in conditions
    }
    observed = [
        (str(cell["system_id"]), int(cell["bundle_index"]), str(cell["condition"]))
        for cell in cells
    ]
    by_id = {str(row["system_id"]): row for row in rows}
    seed_ok = all(
        int(cell["candidate_seed"])
        == _paired_candidate_seed(by_id[str(cell["system_id"])], config, int(cell["bundle_index"]))
        for cell in cells
    )
    checksum_ok = all(
        cell["input_trajectory_checksum"] == _role_rows(by_id[str(cell["system_id"])], "input")[0]["checksum"]
        for cell in cells
    )
    return {
        "expected_count": len(expected), "observed_count": len(observed),
        "unique_observed_count": len(set(observed)),
        "exact_key_set": set(observed) == expected and len(observed) == len(expected),
        "candidate_seed_exact": seed_ok,
        "beam_size_exact": all(int(cell["beam_size"]) == int(beam_size) for cell in cells),
        "input_checksum_exact": checksum_ok,
        "pass": set(observed) == expected and len(observed) == len(expected)
        and seed_ok and checksum_ok
        and all(int(cell["beam_size"]) == int(beam_size) for cell in cells),
    }


def _flatten_cells(cells: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    join_keys = (
        "cell_id", "system_id", "family", "condition", "bundle_index", "candidate_seed",
        "true_formula", "true_prefix", "variable_to_gene", "input_trajectory_checksum",
    )
    candidates = [
        {**{key: cell[key] for key in join_keys}, **candidate}
        for cell in cells for candidate in cell["candidates"]
    ]
    selected = [
        {**{key: cell[key] for key in join_keys}, **cell["selected"],
         "trajectory_metrics": cell["trajectory_metrics"]}
        for cell in cells
    ]
    return candidates, selected


def _candidate_audit(cells: list[dict[str, Any]], candidates: list[dict[str, Any]]) -> dict[str, Any]:
    audit = {
        "flattened_count": len(candidates),
        "sum_cell_candidate_count": sum(int(cell["n_candidates"]) for cell in cells),
        "all_required_fields": all(
            all(key in row for key in (
                "candidate_formula_raw", "candidate_formula_canonical",
                "candidate_exponent_aware_skeleton", "valid", "failure_reason",
            )) for row in candidates
        ),
        "all_cell_hashes_recompute": all(
            _candidate_hash([
                candidate["candidate_formula_raw"]
                for candidate in sorted(cell["candidates"], key=lambda row: int(row["candidate_index"]))
            ]) == cell["candidate_set_hash"]
            for cell in cells
        ),
    }
    audit["pass"] = (
        audit["flattened_count"] == audit["sum_cell_candidate_count"]
        and audit["all_required_fields"] and audit["all_cell_hashes_recompute"]
    )
    return audit


def _finalize_incomplete(
    out: Path,
    *,
    go: dict[str, bool],
    summary: dict[str, Any],
    artifact_names: list[str],
    git: dict[str, Any],
    started_utc: str,
    started_clock: float,
    checkpoint: Path,
    config: dict[str, Any],
    environment: dict[str, Any],
    device: str,
    root: Path,
) -> int:
    full_summary = {"status": "incomplete", **summary, "go_conditions": go}
    write_json(out / "summary.json", full_summary)
    write_json(out / "go.json", go)
    names = list(dict.fromkeys([*artifact_names, "summary.json", "go.json"]))
    missing = [name for name in names if not (out / name).is_file()]
    if missing:
        raise RuntimeError(f"incomplete-run artifact list contains missing files: {missing}")
    finish_git = git_info()
    write_manifest(
        out, 5, "incomplete", go_conditions=go, summary=full_summary, git=git,
        started_utc=started_utc, finished_utc=utc_now(),
        wall_time_sec=perf_counter() - started_clock,
        checkpoint={"path": str(checkpoint), "sha256": sha256_file(checkpoint)},
        config_fingerprint=fingerprint_json(config), environment=environment, device=device,
        phase4_manifest_sha256=sha256_file(root / "phase4" / "manifest.json"),
        phase2_manifest_sha256=sha256_file(root / "phase2" / "manifest.json"),
        git_at_finish=finish_git, test_accessed=False,
        artifact_sha256={name: sha256_file(out / name) for name in names},
    )
    return 1


def main() -> int:
    args = parse_args()
    started_utc, started_clock = utc_now(), perf_counter()
    config, root = load_config(), run_dir(args.run_id)
    chosen_budget = budget(config, args.smoke)
    phase4 = read_json(root / "phase4" / "manifest.json", {})
    if phase4.get("status") != "complete" or not all(phase4.get("go_conditions", {}).values()):
        raise RuntimeError("Phase 4 is not complete with all Go conditions true")
    if phase4.get("grn_test_accessed") is not False or phase4.get("official_test_outcomes_analyzed") is not False:
        raise RuntimeError("Phase 4 test firewall provenance is invalid")
    required = [
        "fixed_official_validation_panel.json", "fixed_grn_validation_panel.json",
        "official_train.json", "train_features.npz",
    ]
    for name in required:
        path = root / "phase4" / name
        if phase4.get("artifact_sha256", {}).get(name) != sha256_file(path):
            raise RuntimeError(f"Phase 4 artifact hash mismatch: {name}")
    phase2 = read_json(root / "phase2" / "manifest.json", {})
    holdout_path = root / "phase2" / "family_holdout_validation.json"
    if (
        phase2.get("status") != "complete"
        or not all(phase2.get("go_conditions", {}).values())
        or phase2.get("test_accessed") is not False
    ):
        raise RuntimeError("Phase 2 is not complete with intact test firewall provenance")
    if phase2.get("artifact_sha256", {}).get("family_holdout_validation.json") != sha256_file(holdout_path):
        raise RuntimeError("Phase 2 family-holdout validation hash mismatch")
    git = git_info()
    if git["status_short"]:
        raise RuntimeError(f"authoritative Phase 5 requires a clean worktree: {git['status_short']}")
    out = phase_dir(args.run_id, 5)
    device = select_device(allow_cpu=args.allow_cpu)
    checkpoint = ROOT / str(config["odeformer_checkpoint"])
    checkpoint_sha256 = sha256_file(checkpoint)
    if checkpoint_sha256 != str(config["odeformer_checkpoint_sha256"]):
        raise RuntimeError("checkpoint SHA256 does not match frozen GPU_RUN5 config")
    model = load_odeformer_model(checkpoint, device=device)
    environment = software_versions()
    inventory = inventory_odeformer(model)
    layers = list(inventory["ranking_layers"])
    means, mean_formula_count = _load_corpus_means(root / "phase4" / "train_features.npz", layers)
    np.savez_compressed(out / "corpus_means.npz", **means)
    write_json(out / "corpus_means_meta.json", {
        "source": "phase4/official_train.json", "n_formulas": mean_formula_count,
        "formula_weighted": True, "layers": layers,
        "source_sha256": phase4["artifact_sha256"]["official_train.json"],
        "features_sha256": phase4["artifact_sha256"]["train_features.npz"],
    })
    official = read_json(root / "phase4" / "fixed_official_validation_panel.json")
    grn = read_json(root / "phase4" / "fixed_grn_validation_panel.json")
    holdout = [row for row in read_json(holdout_path) if row["family"] == "R06"]
    n_panel = int(chosen_budget["intervention_panel"])
    if not args.smoke and (len(official), len(grn), len(holdout)) != (24, 24, 10):
        raise RuntimeError("fixed intervention panels must have sizes official=24, GRN=24, R06=10")
    if args.smoke:
        official, grn, holdout = official[:n_panel], grn[:n_panel], holdout[:n_panel]
    intervention = config["intervention"]
    identity = {
        "schema": "gpu_run5_phase5_cell_v2", "git_commit": git["commit"],
        "config_fingerprint": fingerprint_json(config), "checkpoint_sha256": checkpoint_sha256,
        "phase4_manifest_sha256": sha256_file(root / "phase4" / "manifest.json"),
        "grn_panel_sha256": phase4["artifact_sha256"]["fixed_grn_validation_panel.json"],
        "holdout_validation_sha256": sha256_file(holdout_path),
        "mode": "smoke" if args.smoke else "full", "effective_budget": chosen_budget,
        "device": device, "environment_fingerprint": fingerprint_json(environment),
        "official_panel_ids": [row["problem_id"] for row in official],
        "grn_panel_ids": [row["system_id"] for row in grn],
        "holdout_panel_ids": [row["system_id"] for row in holdout],
    }
    write_json(out / "protocol_frozen.json", {
        "at_utc": utc_now(), "identity": identity, "intervention": intervention,
        "paper_protocol": config["paper_protocol"], "test_accessed": False,
        "fixed_pair": "deferred", "main_decode_selection": "official_candidate_index_0",
    })
    write_json(out / "input_hashes.json", identity)
    write_json(out / "config_snapshot.json", config)

    baseline_official = _mean_ce(model, official, _official_arrays, nullcontext())
    write_json(out / "official_baseline_ce.json", [
        {"problem_id": row["problem_id"], "ce": value}
        for row, value in zip(official, baseline_official)
    ])
    ce_records: list[dict[str, Any]] = []
    mean_by_formula: dict[str, float] = {}
    alpha_one_by_formula: dict[str, float] = {}
    ce_by_alpha: dict[float, dict[str, list[float]]] = {
        float(alpha): {} for alpha in intervention["alphas"]
    }
    for layer in layers:
        zero = _mean_ce(model, official, _official_arrays, zero_residual_block(model, layer))
        mean_values = _mean_ce(model, official, _official_arrays, _post_context(model, layer, means[layer], 1.0))
        for index, value in enumerate(mean_values):
            mean_by_formula[f"{layer}|{official[index]['problem_id']}"] = value
        for index, value in enumerate(zero):
            ce_records.append({"panel": "official", "problem_id": official[index]["problem_id"], "layer": layer, "method": "zero", "alpha": None, "ce": value, "baseline_ce": baseline_official[index]})
        for index, value in enumerate(mean_values):
            ce_records.append({"panel": "official", "problem_id": official[index]["problem_id"], "layer": layer, "method": "mean", "alpha": 1.0, "ce": value, "baseline_ce": baseline_official[index]})
        for alpha in intervention["alphas"]:
            numeric_alpha = float(alpha)
            values = _mean_ce(model, official, _official_arrays, _post_context(model, layer, means[layer], numeric_alpha))
            ce_by_alpha[numeric_alpha][layer] = values
            if numeric_alpha == 1.0:
                for index, value in enumerate(values):
                    alpha_one_by_formula[f"{layer}|{official[index]['problem_id']}"] = value
            for index, value in enumerate(values):
                ce_records.append({"panel": "official", "problem_id": official[index]["problem_id"], "layer": layer, "method": "interpolation", "alpha": numeric_alpha, "ce": value, "baseline_ce": baseline_official[index]})

    tolerance = float(intervention["identity_ce_abs_tolerance"])
    identity_rows = []
    for layer in layers:
        hooked = _mean_ce(model, official, _official_arrays, identity_control_hook(model, layer))
        alpha_zero = _mean_ce(model, official, _official_arrays, _post_context(model, layer, means[layer], 0.0))
        identity_rows.append({
            "layer": layer,
            "identity_max_abs_ce_diff": float(np.max(np.abs(np.asarray(hooked) - baseline_official))),
            "alpha_zero_max_abs_ce_diff": float(np.max(np.abs(np.asarray(alpha_zero) - baseline_official))),
        })
    mean_control = check_mean_alpha_one_equivalence(
        mean_by_formula, alpha_one_by_formula, tolerance=tolerance
    )
    strength = select_interpolation_strength(
        ce_by_alpha, baseline_median_ce=float(np.median(baseline_official)),
        vocab_size=int(inventory["decoder_n_words"]), alphas=intervention["alpha_selection_order"],
        tie_tolerance=float(intervention["ce_tie_tolerance"]),
        min_tie_groups=int(intervention["minimum_tie_aware_groups"]),
        range_relative_to_baseline=float(
            intervention["minimum_layer_delta_range_relative_to_baseline_ce"]
        ),
        range_in_tolerances=float(
            intervention["minimum_layer_delta_range_in_identity_tolerances"]
        ),
    )
    write_json(out / "ce_sweep_records.json", sanitize_nonfinite(ce_records))
    ce_aggregates = []
    for layer in layers:
        for method, alpha in [("zero", None), ("mean", 1.0), *[("interpolation", float(value)) for value in intervention["alphas"]]]:
            rows = [row for row in ce_records if row["layer"] == layer and row["method"] == method and row["alpha"] == alpha]
            ce_aggregates.append({
                "layer": layer, "method": method, "alpha": alpha, "n": len(rows),
                "median_ce": float(np.median([row["ce"] for row in rows])),
                "median_delta_ce": float(np.median([row["ce"] - row["baseline_ce"] for row in rows])),
            })
    write_json(out / "ce_sweep_summary.json", sanitize_nonfinite({
        "n_problem_rows": len(ce_records), "n_aggregate_conditions": len(layers) * 6,
        "baseline_median_ce": float(np.median(baseline_official)), "aggregates": ce_aggregates,
        "selection": strength,
    }))

    sentinel = official[0]
    sentinel_times, sentinel_trajectory, _ = _official_arrays(sentinel)
    control_seed = int(config["seed_bundles"][0]["candidate_seed"])
    baseline_fit = _decode_infixes(model, config, sentinel_times, sentinel_trajectory, seed=control_seed, beam_size=int(chosen_budget["beam_size"]), context=nullcontext())
    baseline_hash = _candidate_hash(baseline_fit["infixes"])
    decode_controls = []
    for layer in layers:
        for family, context in (
            ("identity", identity_control_hook(model, layer)),
            ("alpha_zero", _post_context(model, layer, means[layer], 0.0)),
        ):
            fit = _decode_infixes(model, config, sentinel_times, sentinel_trajectory, seed=control_seed, beam_size=int(chosen_budget["beam_size"]), context=context)
            decode_controls.append({"layer": layer, "family": family, "candidate_set_hash": _candidate_hash(fit["infixes"]), "matches_baseline": _candidate_hash(fit["infixes"]) == baseline_hash})
    hook_controls = {
        "ce_tolerance": tolerance, "ce_rows": identity_rows, "mean_alpha_one": mean_control,
        "decode_baseline_hash": baseline_hash, "decode_controls": decode_controls,
        "all_pass": all(max(row["identity_max_abs_ce_diff"], row["alpha_zero_max_abs_ce_diff"]) <= tolerance for row in identity_rows)
        and mean_control["equivalent"] and all(row["matches_baseline"] for row in decode_controls),
    }
    write_json(out / "hook_controls.json", hook_controls)
    selection_payload = {"at_utc": utc_now(), **strength, "controls_pass": hook_controls["all_pass"]}
    write_json(out / "intervention_selection.json", selection_payload)
    if not strength["admissible"] or not hook_controls["all_pass"]:
        go = {"controls_pass": hook_controls["all_pass"], "non_saturated_strength_exists": strength["admissible"]}
        return _finalize_incomplete(
            out, go=go, summary={"reason": "Go 5 failed before intervention decode", "selection": strength},
            artifact_names=[
                "protocol_frozen.json", "input_hashes.json", "config_snapshot.json",
                "corpus_means.npz", "corpus_means_meta.json", "official_baseline_ce.json",
                "ce_sweep_records.json", "ce_sweep_summary.json", "hook_controls.json",
                "intervention_selection.json",
            ], git=git, started_utc=started_utc, started_clock=started_clock,
            checkpoint=checkpoint, config=config, environment=environment, device=device, root=root,
        )
    selected_alpha = float(strength["selected_alpha"])

    grn_ce_records = []
    for panel_rows, panel_name in ((grn, "grn"), (holdout, "holdout_R06")):
        for row in panel_rows:
            times, trajectory, tree = _grn_arrays(row)
            with torch.no_grad():
                base = float(teacher_forcing_loss(model, times, trajectory, tree).detach().cpu())
            grn_ce_records.append({"panel": panel_name, "system_id": row["system_id"], "condition": "baseline", "layer": None, "ce": base})
            for layer in layers:
                with _post_context(model, layer, means[layer], selected_alpha), torch.no_grad():
                    value = float(teacher_forcing_loss(model, times, trajectory, tree).detach().cpu())
                grn_ce_records.append({"panel": panel_name, "system_id": row["system_id"], "condition": "interpolation", "layer": layer, "ce": value})
    write_json(out / "grn_ce_records.json", sanitize_nonfinite(grn_ce_records))

    beam_size = int(chosen_budget["beam_size"])
    n_bundles = int(chosen_budget["n_seeds"])
    r2_penalty = float(intervention["failure_aware_r2_penalty"])
    nrmse_penalty = float(config["selection"]["trajectory_nrmse_failure_penalty"])
    decode_identity = {
        **identity, "selected_alpha": selected_alpha, "beam_size": beam_size,
        "n_bundles": n_bundles,
    }
    cache_root = out / "cell_cache" / fingerprint_json(decode_identity)[:16]
    def run_panel(
        rows: list[dict[str, Any]], label: str, conditions: list[str],
    ) -> list[dict[str, Any]]:
        cells = []
        for row in rows:
            for bundle_index in range(n_bundles):
                for condition in conditions:
                    filename = f"{row['system_id']}__b{bundle_index}__{condition.replace(':', '_')}.json"
                    candidate_seed = _paired_candidate_seed(row, config, bundle_index)
                    cell_identity = _cell_identity(
                        decode_identity, row, bundle_index, condition, candidate_seed
                    )
                    cells.append(_cached_cell(
                        cache_root / label / filename, cell_identity,
                        lambda row=row, bundle_index=bundle_index, condition=condition,
                        cell_identity=cell_identity: _decode_cell(
                            row, model=model, config=config, means=means, alpha=selected_alpha,
                            condition=condition, bundle_index=bundle_index, beam_size=beam_size,
                            r2_penalty=r2_penalty, nrmse_penalty=nrmse_penalty,
                            cache_identity=cell_identity,
                        ),
                    ))
        return cells

    main_baseline = run_panel(grn, "main", ["baseline"])
    baseline_funnel = _failure_funnel(main_baseline)
    if baseline_funnel["selected_valid_rate"] < 0.5:
        go = {"baseline_panel_valid_rate_at_least_half": False}
        candidates, selected = _flatten_cells(main_baseline)
        audit = _candidate_audit(main_baseline, candidates)
        write_json(out / "main_cells.json", main_baseline)
        write_json(out / "all_candidates.json", candidates)
        write_json(out / "selected.json", selected)
        write_json(out / "candidate_audit.json", audit)
        write_json(out / "failure_funnel.json", {"main_baseline": baseline_funnel})
        return _finalize_incomplete(
            out, go=go, summary={"reason": "baseline intervention panel valid rate below 0.5", "failure_funnel": baseline_funnel},
            artifact_names=[
                "protocol_frozen.json", "input_hashes.json", "config_snapshot.json",
                "corpus_means.npz", "corpus_means_meta.json", "official_baseline_ce.json",
                "ce_sweep_records.json", "ce_sweep_summary.json", "hook_controls.json",
                "intervention_selection.json", "grn_ce_records.json", "main_cells.json",
                "all_candidates.json", "selected.json", "candidate_audit.json", "failure_funnel.json",
            ], git=git, started_utc=started_utc, started_clock=started_clock,
            checkpoint=checkpoint, config=config, environment=environment, device=device, root=root,
        )
    main_interventions = run_panel(
        grn, "main", [f"interpolation:{layer}" for layer in layers]
    )
    main_cells = main_baseline + main_interventions
    holdout_cells = run_panel(
        holdout, "holdout_R06", ["baseline", *[f"interpolation:{layer}" for layer in layers]]
    )
    main_ce = [row for row in grn_ce_records if row["panel"] == "grn"]
    holdout_ce = [row for row in grn_ce_records if row["panel"] == "holdout_R06"]
    effects = _layer_effects(main_cells, main_ce, layers)
    holdout_effects = _layer_effects(holdout_cells, holdout_ce, layers)
    causal = rank_causal_formula_damage(effects)
    holdout_causal = rank_causal_formula_damage(holdout_effects)
    p5 = p5_damage_spearman(effects, threshold=float(intervention["p5_spearman_threshold"]))
    p5["per_bundle"] = {
        str(bundle_index): p5_damage_spearman(
            _layer_effects([row for row in main_cells if int(row["bundle_index"]) == bundle_index], main_ce, layers),
            threshold=float(intervention["p5_spearman_threshold"]),
        ) for bundle_index in range(n_bundles)
    }
    p5["leave_one_layer_out"] = {
        layer: p5_damage_spearman(
            {name: value for name, value in effects.items() if name != layer},
            threshold=float(intervention["p5_spearman_threshold"]),
            expected_layer_count=len(layers) - 1,
        ) for layer in layers
    }
    write_json(out / "layer_effects.json", effects)
    write_json(out / "holdout_layer_effects.json", holdout_effects)
    write_json(out / "causal_ranking.json", causal)
    write_json(out / "holdout_causal_ranking.json", holdout_causal)
    causal_finite = all(row["quantized_score_vector"] is not None for row in causal["rows"])
    holdout_causal_finite = all(
        row["quantized_score_vector"] is not None for row in holdout_causal["rows"]
    )
    if not causal_finite or not holdout_causal_finite:
        go = {
            "main_causal_scores_all_finite": causal_finite,
            "holdout_causal_scores_all_finite": holdout_causal_finite,
        }
        cells = main_cells + holdout_cells
        candidates, selected = _flatten_cells(cells)
        audit = _candidate_audit(cells, candidates)
        funnel = {"main": _failure_funnel(main_cells), "holdout_R06": _failure_funnel(holdout_cells)}
        write_json(out / "main_cells.json", main_cells)
        write_json(out / "holdout_R06_cells.json", holdout_cells)
        write_json(out / "all_candidates.json", candidates)
        write_json(out / "selected.json", selected)
        write_json(out / "candidate_audit.json", audit)
        write_json(out / "p5.json", p5)
        write_json(out / "failure_funnel.json", funnel)
        return _finalize_incomplete(
            out, go=go, summary={"reason": "non-finite causal score vector", "failure_funnel": funnel},
            artifact_names=[
                "protocol_frozen.json", "input_hashes.json", "config_snapshot.json",
                "corpus_means.npz", "corpus_means_meta.json", "official_baseline_ce.json",
                "ce_sweep_records.json", "ce_sweep_summary.json", "hook_controls.json",
                "intervention_selection.json", "grn_ce_records.json", "main_cells.json",
                "holdout_R06_cells.json", "all_candidates.json", "selected.json", "candidate_audit.json",
                "layer_effects.json", "holdout_layer_effects.json", "causal_ranking.json",
                "holdout_causal_ranking.json", "p5.json", "failure_funnel.json",
            ], git=git, started_utc=started_utc, started_clock=started_clock,
            checkpoint=checkpoint, config=config, environment=environment, device=device, root=root,
        )
    top3 = causal["ranking"][:3]
    holdout_top3 = holdout_causal["ranking"][:3]
    freeze = {
        "at_utc": utc_now(), "selected_alpha": selected_alpha, "main_causal_top3": top3,
        "holdout_causal_top3": holdout_top3,
        "source_sha256": {
            "main_layer_effects": sha256_file(out / "layer_effects.json"),
            "holdout_layer_effects": sha256_file(out / "holdout_layer_effects.json"),
            "main_causal_ranking": sha256_file(out / "causal_ranking.json"),
            "holdout_causal_ranking": sha256_file(out / "holdout_causal_ranking.json"),
            "main_panel": phase4["artifact_sha256"]["fixed_grn_validation_panel.json"],
            "holdout_R06_panel": sha256_file(holdout_path),
        },
        "main_top3_boundary_tied": causal["rows"][2]["tie_group"] == causal["rows"][3]["tie_group"],
        "holdout_top3_boundary_tied": holdout_causal["rows"][2]["tie_group"]
        == holdout_causal["rows"][3]["tie_group"],
        "tie_break": "canonical layer name", "robustness_accessed_before_freeze": False,
    }
    write_json(out / "causal_top3_freeze.json", freeze)

    zero_cells = []
    for row in grn:
        for bundle_index in range(n_bundles):
            for layer in top3:
                condition = f"zero:{layer}"
                filename = f"{row['system_id']}__b{bundle_index}__zero_{layer}.json"
                candidate_seed = _paired_candidate_seed(row, config, bundle_index)
                cell_identity = _cell_identity(
                    decode_identity, row, bundle_index, condition, candidate_seed
                )
                zero_cells.append(_cached_cell(
                    cache_root / "zero_robustness" / filename, cell_identity,
                    lambda row=row, bundle_index=bundle_index, condition=condition,
                    cell_identity=cell_identity: _decode_cell(
                        row, model=model, config=config, means=means, alpha=selected_alpha,
                        condition=condition, bundle_index=bundle_index, beam_size=beam_size,
                        r2_penalty=r2_penalty, nrmse_penalty=nrmse_penalty,
                        cache_identity=cell_identity,
                    ),
                ))
    zero_effects = _layer_effects(
        [*[row for row in main_cells if row["condition"] == "baseline"], *zero_cells],
        main_ce, top3, condition_method="zero", include_ce=False,
    )
    zero_robustness = {
        layer: {
            "selected_interpolation": effects[layer], "zero": zero_effects[layer],
            "ted_damage_sign_agrees": np.sign(effects[layer]["failure_aware_ted_increase"])
            == np.sign(zero_effects[layer]["failure_aware_ted_increase"]),
            "method_dependent": np.sign(effects[layer]["failure_aware_ted_increase"])
            != np.sign(zero_effects[layer]["failure_aware_ted_increase"]),
        } for layer in top3
    }
    write_json(out / "main_cells.json", main_cells)
    write_json(out / "holdout_R06_cells.json", holdout_cells)
    write_json(out / "zero_robustness_cells.json", zero_cells)
    all_cells = main_cells + holdout_cells + zero_cells
    all_candidates, selected_rows = _flatten_cells(all_cells)
    candidate_audit = _candidate_audit(all_cells, all_candidates)
    write_json(out / "all_candidates.json", sanitize_nonfinite(all_candidates))
    write_json(out / "selected.json", sanitize_nonfinite(selected_rows))
    write_json(out / "candidate_audit.json", candidate_audit)
    write_json(out / "p5.json", sanitize_nonfinite(p5))
    write_json(out / "zero_robustness.json", sanitize_nonfinite(zero_robustness))
    funnel = {
        "main": _failure_funnel(main_cells), "holdout_R06": _failure_funnel(holdout_cells),
        "zero_robustness": _failure_funnel(zero_cells),
    }
    write_json(out / "failure_funnel.json", funnel)
    expected_main = len(grn) * (1 + len(layers)) * n_bundles
    expected_holdout = len(holdout) * (1 + len(layers)) * n_bundles
    expected_zero = len(grn) * 3 * n_bundles
    official_expected = len(official) * len(layers) * 6
    main_coverage = _coverage_audit(
        main_cells, grn, ["baseline", *[f"interpolation:{layer}" for layer in layers]],
        n_bundles=n_bundles, beam_size=beam_size, config=config,
    )
    holdout_coverage = _coverage_audit(
        holdout_cells, holdout, ["baseline", *[f"interpolation:{layer}" for layer in layers]],
        n_bundles=n_bundles, beam_size=beam_size, config=config,
    )
    zero_coverage = _coverage_audit(
        zero_cells, grn, [f"zero:{layer}" for layer in top3],
        n_bundles=n_bundles, beam_size=beam_size, config=config,
    )
    coverage = {"main": main_coverage, "holdout_R06": holdout_coverage, "zero": zero_coverage}
    write_json(out / "coverage_audit.json", coverage)
    finish_git = git_info()
    git_stable = finish_git["commit"] == git["commit"] and not finish_git["status_short"]
    go = {
        "phase4_complete_and_hashed": True, "test_not_accessed": True,
        "sixteen_finite_corpus_means": len(means) == 16 and all(np.isfinite(value).all() for value in means.values()),
        "all_hook_controls_pass": hook_controls["all_pass"],
        "official_ce_sweep_exact": len(ce_records) == official_expected,
        "non_saturated_strength_selected": selected_alpha in [float(value) for value in intervention["alphas"]],
        "main_decode_exact": len(main_cells) == expected_main and main_coverage["pass"],
        "holdout_R06_decode_exact": len(holdout_cells) == expected_holdout and holdout_coverage["pass"],
        "zero_robustness_exact": len(zero_cells) == expected_zero and zero_coverage["pass"],
        "baseline_shared_and_candidate_seeds_paired": all(
            audit["candidate_seed_exact"] for audit in coverage.values()
        ),
        "baseline_panel_valid_rate_at_least_half": baseline_funnel["selected_valid_rate"] >= 0.5,
        "causal_top3_frozen_before_zero_robustness": len(top3) == 3,
        "main_and_holdout_causal_scores_all_finite": causal_finite and holdout_causal_finite,
        "p5_saved_with_determinate_or_reason": p5["determinate"] or bool(p5.get("reason")),
        "all_candidate_formulas_and_failures_saved": len(selected_rows) == len(all_cells)
        and candidate_audit["pass"],
        "git_commit_and_cleanliness_stable": git_stable,
    }
    status = "complete" if all(go.values()) else "incomplete"
    summary = {
        "status": status, "selected_alpha": selected_alpha, "main_causal_top3": top3,
        "holdout_causal_top3": holdout_causal["ranking"][:3], "p5": p5,
        "counts": {"official_ce_rows": len(ce_records), "main_cells": len(main_cells), "holdout_cells": len(holdout_cells), "zero_cells": len(zero_cells), "candidates": len(all_candidates)},
        "failure_funnel": funnel, "go_conditions": go,
    }
    write_json(out / "summary.json", sanitize_nonfinite(summary))
    write_json(out / "go.json", go)
    artifacts = [
        "protocol_frozen.json", "input_hashes.json", "config_snapshot.json",
        "corpus_means.npz", "corpus_means_meta.json", "official_baseline_ce.json",
        "hook_controls.json", "ce_sweep_records.json", "ce_sweep_summary.json", "intervention_selection.json",
        "grn_ce_records.json", "main_cells.json", "holdout_R06_cells.json", "zero_robustness_cells.json",
        "all_candidates.json", "selected.json", "candidate_audit.json",
        "layer_effects.json", "holdout_layer_effects.json",
        "causal_ranking.json", "holdout_causal_ranking.json", "causal_top3_freeze.json", "p5.json",
        "zero_robustness.json", "failure_funnel.json", "coverage_audit.json", "summary.json", "go.json",
    ]
    write_manifest(
        out, 5, status, go_conditions=go, summary=summary, git=git,
        started_utc=started_utc, finished_utc=utc_now(), wall_time_sec=perf_counter() - started_clock,
        checkpoint={"path": str(checkpoint), "sha256": sha256_file(checkpoint)},
        config_fingerprint=fingerprint_json(config), environment=environment, device=device,
        phase4_manifest_sha256=sha256_file(root / "phase4" / "manifest.json"),
        phase2_manifest_sha256=sha256_file(root / "phase2" / "manifest.json"),
        git_at_finish=finish_git,
        test_accessed=False, artifact_sha256={name: sha256_file(out / name) for name in artifacts},
    )
    print(f"GPU_RUN5 Phase 5 {status}: alpha={selected_alpha} main={len(main_cells)} zero={len(zero_cells)}")
    return 0 if status == "complete" else 1


if __name__ == "__main__":
    raise SystemExit(main())
