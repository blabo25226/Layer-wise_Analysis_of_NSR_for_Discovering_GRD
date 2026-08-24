"""GPU-facing, sharded evaluation helpers for GPU_RUN5 Phase 8."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from time import perf_counter
from typing import Any, Mapping, Sequence

import numpy as np
import torch

from gpu_run4.inference import fit_and_collect, integrate_candidate
from gpu_run4.trajectories import corrupt_trajectory, r2_score
from gpu_run4_runtime import make_symbolic_regressor
from gpu_run5.config import sanitize_nonfinite
from gpu_run5.evaluation import formula_metrics, select_candidate, trajectory_nrmse
from gpu_run5.phase6 import load_cached_cell, validation_cell_id, write_cached_cell
from gpu_run5.phase8 import phase8_cell_identity
from gpu_run5.seeding import stable_problem_seed


def candidate_set_sha256(infixes: Sequence[str | None]) -> str:
    encoded = json.dumps([value or "" for value in infixes], ensure_ascii=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def input_trajectory(row: Mapping[str, Any]) -> Mapping[str, Any]:
    values = [item for item in row["trajectories"] if item.get("role") == "input"]
    if len(values) != 1:
        raise ValueError(f"{row.get('system_id')} must have exactly one input trajectory")
    return values[0]


def observed_selection_trajectories(
    row: Mapping[str, Any],
    *,
    sigma: float,
    rho: float,
    bundle: Mapping[str, Any],
    bundle_index: int,
) -> dict[str, list[dict[str, Any]]]:
    """Materialize only input and selection IC observations for reranking."""
    output: dict[str, list[dict[str, Any]]] = {"input": [], "selection": []}
    for role, expected in (("input", 1), ("selection", 2)):
        sources = sorted(
            [item for item in row["trajectories"] if item.get("role") == role],
            key=lambda item: int(item["role_index"]),
        )
        if len(sources) != expected:
            raise ValueError(f"{row.get('system_id')} requires {expected} {role} trajectories")
        for source in sources:
            seed = stable_problem_seed(
                int(bundle["corruption_seed"]),
                system_id=str(row["system_id"]),
                condition=f"{role}_{int(source['role_index'])}",
                noise_sigma=float(sigma),
                subsample_rho=float(rho),
                sampling_replicate=int(bundle_index),
            )
            times, trajectory = corrupt_trajectory(
                np.asarray(source["times"], dtype=float),
                np.asarray(source["trajectory"], dtype=float),
                sigma=float(sigma),
                rho=float(rho),
                seed=int(seed),
            )
            output[role].append(
                {
                    "role": role,
                    "role_index": int(source["role_index"]),
                    "times": times,
                    "trajectory": trajectory,
                    "initial_condition": trajectory[0],
                    "corruption_seed": int(seed),
                    "source_checksum": str(source["checksum"]),
                }
            )
    return output


def make_regressor(model: Any, config: Mapping[str, Any], *, beam_size: int, seed: int) -> Any:
    protocol = config["paper_protocol"]
    return make_symbolic_regressor(
        model,
        rescale=bool(protocol["rescale"]),
        beam_size=int(beam_size),
        beam_temperature=float(protocol["beam_temperature"]),
        beam_type=str(protocol["beam_type"]),
        generation_seed=int(seed),
    )


def failed_formula(row: Mapping[str, Any], reason: str) -> dict[str, Any]:
    metrics = formula_metrics(str(row["teacher_infix"]), "")
    metrics["failure_reason"] = str(reason)
    return {
        "candidate_index": None,
        "candidate_formula_raw": "",
        **metrics,
        "generation_failure": str(reason),
        "empty_candidate_placeholder": True,
        "trajectory_metrics": {
            "input_nrmse": [],
            "selection_nrmse": [],
            "input_failures": [str(reason)],
            "selection_failures": [str(reason)],
        },
    }


def evaluate_candidate(
    row: Mapping[str, Any],
    *,
    raw: str,
    tree: Any,
    index: int,
    regressor: Any,
    observations: Mapping[str, Sequence[Mapping[str, Any]]],
    penalty: float,
) -> dict[str, Any]:
    try:
        metrics = formula_metrics(str(row["teacher_infix"]), raw)
    except Exception as exc:
        metrics = formula_metrics(str(row["teacher_infix"]), "")
        metrics["failure_reason"] = f"{type(exc).__name__}:{exc}"
    trajectory_metrics: dict[str, list[Any]] = {
        "input_nrmse": [], "selection_nrmse": [], "input_failures": [], "selection_failures": []
    }
    for role in ("input", "selection"):
        for trajectory in observations[role]:
            predicted, failure = integrate_candidate(
                regressor,
                np.asarray(trajectory["times"], dtype=float),
                np.asarray(trajectory["initial_condition"], dtype=float),
                tree,
                timeout_sec=10.0,
            )
            trajectory_metrics[f"{role}_nrmse"].append(
                trajectory_nrmse(np.asarray(trajectory["trajectory"], dtype=float), predicted, penalty=penalty)
            )
            trajectory_metrics[f"{role}_failures"].append(failure)
    return {"candidate_index": int(index), "candidate_formula_raw": raw, **metrics, "trajectory_metrics": trajectory_metrics}


def selected_clean_trajectory_metrics(
    row: Mapping[str, Any],
    *,
    prediction: Any,
    regressor: Any,
    penalty: float,
) -> dict[str, Any]:
    """Evaluate the already-selected formula on clean ICs, including generalization."""
    output: dict[str, Any] = {"candidate_selection_finished_before_generalization_access": True, "roles": {}}
    for role, expected in (("input", 1), ("selection", 2), ("generalization", 2)):
        sources = sorted(
            [item for item in row["trajectories"] if item.get("role") == role],
            key=lambda item: int(item["role_index"]),
        )
        if len(sources) != expected:
            raise ValueError(f"{row.get('system_id')} requires {expected} clean {role} trajectories")
        records = []
        for source in sources:
            truth = np.asarray(source["trajectory"], dtype=float)
            predicted, failure = integrate_candidate(
                regressor,
                np.asarray(source["times"], dtype=float),
                truth[0],
                prediction,
                timeout_sec=10.0,
            )
            try:
                r2 = float(r2_score(truth, predicted)) if predicted is not None else -10.0
            except Exception:
                r2 = -10.0
            if not math.isfinite(r2):
                r2 = -10.0
            records.append(
                {
                    "role_index": int(source["role_index"]),
                    "source_checksum": str(source["checksum"]),
                    "nrmse": trajectory_nrmse(truth, predicted, penalty=penalty),
                    "r2": r2,
                    "failure": failure,
                }
            )
        output["roles"][role] = records
    return output


def decode_cell(
    row: Mapping[str, Any],
    *,
    model: Any,
    config: Mapping[str, Any],
    selection_contract: Mapping[str, Any],
    bundle_index: int,
    sigma: float,
    rho: float,
    beam_size: int,
    candidate_seed: int,
    cache_identity: Mapping[str, Any],
    include_clean_generalization: bool,
) -> dict[str, Any]:
    bundle = config["seed_bundles"][int(bundle_index)]
    observations = observed_selection_trajectories(
        row, sigma=sigma, rho=rho, bundle=bundle, bundle_index=bundle_index
    )
    input_observation = observations["input"][0]
    if str(cache_identity["input_trajectory_checksum"]) != str(input_observation["source_checksum"]):
        raise RuntimeError("cache identity input checksum mismatch")
    started = perf_counter()
    generation_failure = None
    regressor = make_regressor(model, config, beam_size=beam_size, seed=candidate_seed)
    try:
        fit = fit_and_collect(
            regressor,
            np.asarray(input_observation["times"], dtype=float),
            np.asarray(input_observation["trajectory"], dtype=float),
            permutation_seed=candidate_seed,
        )
        infixes, trees = list(fit["infixes"]), list(fit["trees"])
        wall = float(fit["wall_time"])
    except torch.cuda.OutOfMemoryError:
        raise
    except RuntimeError as exc:
        if "out of memory" in str(exc).lower():
            raise
        generation_failure = f"{type(exc).__name__}:{exc}"
        infixes, trees, wall = [], [], perf_counter() - started
    except Exception as exc:
        generation_failure = f"{type(exc).__name__}:{exc}"
        infixes, trees, wall = [], [], perf_counter() - started
    penalty = float(config["selection"]["trajectory_nrmse_failure_penalty"])
    candidates = [
        evaluate_candidate(
            row, raw=raw or "", tree=tree, index=index, regressor=regressor,
            observations=observations, penalty=penalty,
        )
        for index, (tree, raw) in enumerate(zip(trees, infixes))
    ]
    selected_index = select_candidate(
        candidates,
        str(selection_contract["selection_rule"]),
        penalty=penalty,
        complexity_lambda=float(selection_contract["complexity_lambda"]),
    )
    selected = dict(candidates[selected_index]) if selected_index is not None else failed_formula(
        row, generation_failure or "EmptyCandidateSet"
    )
    clean_metrics = None
    if include_clean_generalization:
        prediction = (trees[selected_index] if selected_index is not None else "")
        clean_metrics = selected_clean_trajectory_metrics(
            row, prediction=prediction, regressor=regressor, penalty=penalty
        )
    return sanitize_nonfinite(
        {
            "status": "complete",
            "cache_identity": dict(cache_identity),
            "cell_id": str(cache_identity["cell_id"]),
            "stage": str(cache_identity["stage"]),
            "view": str(cache_identity["view"]),
            "condition": str(cache_identity["condition"]),
            "system_id": str(row["system_id"]),
            "family": str(row["family"]),
            "dimension": int(row["dimension"]),
            "bundle_index": int(bundle_index),
            "noise_sigma": float(sigma),
            "subsample_rho": float(rho),
            "beam_size": int(beam_size),
            "candidate_seed": int(candidate_seed),
            "input_trajectory_checksum": str(input_observation["source_checksum"]),
            "true_formula": str(row["teacher_infix"]),
            "true_prefix": row["teacher_prefix"],
            "true_structure": formula_metrics(str(row["teacher_infix"]), str(row["teacher_infix"]))["structure"],
            "variable_to_gene": dict(row.get("variable_to_gene") or {}),
            "candidate_set_hash": candidate_set_sha256(infixes),
            "n_candidates": len(candidates),
            "candidate_shortfall": max(int(beam_size) - len(candidates), 0),
            "generation_failure": generation_failure,
            "decode_wall_time_sec": wall,
            "selection_rule": str(selection_contract["selection_rule"]),
            "complexity_lambda": float(selection_contract["complexity_lambda"]),
            "selection_contract_sha256": str(cache_identity["selection_contract_sha256"]),
            "selection_trajectory_contract": "corrupted_input_plus_selection_ic_only",
            "generalization_trajectory_accessed": bool(include_clean_generalization),
            "selected": selected,
            "selected_clean_trajectory_metrics": clean_metrics,
            "candidates": candidates,
        }
    )


def decode_panel(
    *,
    model: Any,
    rows: Sequence[Mapping[str, Any]],
    config: Mapping[str, Any],
    selection_contract: Mapping[str, Any],
    selection_contract_sha256: str,
    out: Path,
    campaign_identity_sha256: str,
    stage: str,
    view: str,
    condition: str,
    checkpoint_sha256: str,
    beam_size: int,
    bundle_indices: Sequence[int],
    seed_maps: Mapping[int, Mapping[str, int]],
    final_freeze_sha256: str | None = None,
    test_open_event_id: str | None = None,
) -> tuple[list[dict[str, Any]], list[Path]]:
    cells, paths = [], []
    final = stage == "final_test"
    for bundle_index in sorted(int(value) for value in bundle_indices):
        for row in sorted(rows, key=lambda item: str(item["system_id"])):
            source_checksum = str(input_trajectory(row)["checksum"])
            for sigma in config["corruptions"]["noise_sigmas"]:
                for rho in config["corruptions"]["subsample_rhos"]:
                    cell_id = validation_cell_id(
                        system=str(row["system_id"]), bundle_index=bundle_index,
                        noise_sigma=float(sigma), subsample_rho=float(rho),
                    )
                    candidate_seed = int(seed_maps[bundle_index][cell_id])
                    identity = phase8_cell_identity(
                        campaign_identity_sha256=campaign_identity_sha256,
                        stage=stage,
                        view=view,
                        condition=condition,
                        checkpoint_sha256=checkpoint_sha256,
                        beam_size=beam_size,
                        cell_id=cell_id,
                        candidate_seed=candidate_seed,
                        input_trajectory_checksum=source_checksum,
                        selection_contract_sha256=selection_contract_sha256,
                        final_freeze_sha256=final_freeze_sha256,
                        test_open_event_id=test_open_event_id,
                    )
                    # Screening evaluates nine deltas for the same logical cell.
                    # Binding the shard path to the checkpoint avoids overwriting
                    # losing candidates while keeping resume identities exact.
                    path = (
                        out
                        / "cells"
                        / stage
                        / view
                        / condition
                        / str(checkpoint_sha256)[:16]
                        / f"{cell_id}.json"
                    )
                    cached = load_cached_cell(path, identity)
                    if cached is None:
                        cached = decode_cell(
                            row, model=model, config=config, selection_contract=selection_contract,
                            bundle_index=bundle_index, sigma=float(sigma), rho=float(rho),
                            beam_size=beam_size, candidate_seed=candidate_seed,
                            cache_identity=identity, include_clean_generalization=final,
                        )
                        write_cached_cell(path, cached)
                    cells.append(cached)
                    paths.append(path)
    return cells, paths
