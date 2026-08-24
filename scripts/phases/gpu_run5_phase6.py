"""GPU_RUN5 Phase 6: fair GRN adaptation grid and validation-only freeze.

This phase deliberately opens only the Phase 2 train/validation views and the
Phase 4 official-train/reduced-panel artifacts.  Sealed GRN outcomes are not
named or discovered here.  Every trainable condition receives the same LR x
snapshot-step grid, and every decode is written as an atomic identity-bearing
cell so an interrupted run can resume without changing the experiment.
"""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import math
import os
import sys
from pathlib import Path
from time import perf_counter
from typing import Any, Mapping, Sequence

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from gpu_run2_runtime import (  # noqa: E402
    fingerprint_json,
    git_info,
    sha256_file,
    utc_now,
    write_json as _write_json,
)
from gpu_run3_runtime import software_versions  # noqa: E402
from gpu_run4.architecture import inventory_odeformer  # noqa: E402
from gpu_run4.inference import fit_and_collect, integrate_candidate  # noqa: E402
from gpu_run4.training import teacher_forcing_loss  # noqa: E402
from gpu_run4.trajectories import corrupt_trajectory  # noqa: E402
from gpu_run4_runtime import (  # noqa: E402
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
from gpu_run5.evaluation import formula_metrics, select_candidate, trajectory_nrmse  # noqa: E402
from gpu_run5.phase6 import (  # noqa: E402
    PHASE3_COMPLEXITY_LAMBDA,
    PHASE3_SELECTION_RULE,
    TRAINABLE_CONDITIONS,
    VIEWS,
    artifact_index,
    audit_data_views,
    build_trial_identity,
    candidate_seed_map,
    candidate_seed_map_sha256,
    cell_cache_identity,
    corruption_grid,
    coverage_audit,
    delta_identity,
    expected_phase6_counts,
    freeze_phase3_selection,
    hyperparameter_grid,
    load_cached_cell,
    phase3_cell_filename,
    validation_cell_id,
    verify_holdout_selection_artifact,
    write_cached_cell,
)
from gpu_run5.training import (  # noqa: E402
    adapt_input_training_records,
    apply_delta_checkpoint,
    formula_score_vector,
    load_delta_checkpoint,
    make_delta_checkpoint,
    model_state_sha256,
    restore_parameter_state,
    save_delta_checkpoint,
    select_formula_candidate,
    train_adam_with_snapshots,
    training_order,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", default=os.environ.get("LANSR_RUN_ID"))
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--allow-cpu", action="store_true")
    return parser.parse_args()


def write_json(path: Path, payload: Any) -> Path:
    """Write interoperable strict JSON through the repository atomic writer."""
    return _write_json(path, sanitize_nonfinite(payload))


def _candidate_hash(infixes: Sequence[str | None]) -> str:
    normalized = [value or "" for value in infixes]
    return hashlib.sha256(
        json.dumps(normalized, ensure_ascii=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _input_row(row: Mapping[str, Any]) -> Mapping[str, Any]:
    values = [item for item in row["trajectories"] if item.get("role") == "input"]
    if len(values) != 1:
        raise ValueError(f"{row.get('system_id')} must have exactly one input trajectory")
    return values[0]


def _condition_layers(condition: str, decoder_layers: Sequence[str]) -> set[str] | None:
    if condition in {"official_continued_full", "grn_full"}:
        return None
    if condition == "grn_decoder_all":
        return set(decoder_layers)
    raise ValueError(f"unknown trainable condition: {condition}")


def _condition_corpus(
    condition: str,
    *,
    official_train: Sequence[Mapping[str, Any]],
    grn_train: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    source = official_train if condition == "official_continued_full" else grn_train
    return [dict(row) for row in source]


def _panel_rows(
    rows: Sequence[Mapping[str, Any]], count: int
) -> list[dict[str, Any]]:
    ordered = sorted((dict(row) for row in rows), key=lambda row: str(row["system_id"]))
    if int(count) <= 0 or len(ordered) < int(count):
        raise ValueError(f"requested panel {count} exceeds available rows {len(ordered)}")
    return ordered[: int(count)]


def _variants_per_family(
    rows: Sequence[Mapping[str, Any]], count: int
) -> list[dict[str, Any]]:
    """Take a deterministic per-family prefix for an explicitly smoke-only budget."""
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in sorted(rows, key=lambda item: str(item["system_id"])):
        grouped.setdefault(str(row["family"]), []).append(dict(row))
    if int(count) <= 0 or any(len(values) < int(count) for values in grouped.values()):
        raise ValueError("per-family smoke budget exceeds an available family")
    return [row for family in sorted(grouped) for row in grouped[family][: int(count)]]


def _observed_selection_trajectories(
    row: Mapping[str, Any],
    *,
    sigma: float,
    rho: float,
    bundle: Mapping[str, Any],
    bundle_index: int,
) -> dict[str, list[dict[str, Any]]]:
    """Return only corrupted input/selection ICs; generalization is unopened."""
    stable_problem_seed = __import__(
        "gpu_run5.seeding", fromlist=["stable_problem_seed"]
    ).stable_problem_seed
    output: dict[str, list[dict[str, Any]]] = {"input": [], "selection": []}
    for role in output:
        sources = sorted(
            [item for item in row["trajectories"] if item.get("role") == role],
            key=lambda item: int(item["role_index"]),
        )
        expected = 1 if role == "input" else 2
        if len(sources) != expected:
            raise ValueError(
                f"{row.get('system_id')} requires {expected} {role} trajectories"
            )
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


def _make_regressor(model: Any, config: Mapping[str, Any], beam_size: int, seed: int) -> Any:
    protocol = config["paper_protocol"]
    return make_symbolic_regressor(
        model,
        rescale=bool(protocol["rescale"]),
        beam_size=int(beam_size),
        beam_temperature=float(protocol["beam_temperature"]),
        beam_type=str(protocol["beam_type"]),
        generation_seed=int(seed),
    )


def _failed_formula(row: Mapping[str, Any], reason: str) -> dict[str, Any]:
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


def _evaluate_candidate_trajectories(
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
        "input_nrmse": [],
        "selection_nrmse": [],
        "input_failures": [],
        "selection_failures": [],
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
                trajectory_nrmse(
                    np.asarray(trajectory["trajectory"], dtype=float),
                    predicted,
                    penalty=penalty,
                )
            )
            trajectory_metrics[f"{role}_failures"].append(failure)
    return {
        "candidate_index": int(index),
        "candidate_formula_raw": raw,
        **metrics,
        "trajectory_metrics": trajectory_metrics,
    }


def _decode_cell(
    row: Mapping[str, Any],
    *,
    model: Any,
    config: Mapping[str, Any],
    bundle_index: int,
    sigma: float,
    rho: float,
    beam_size: int,
    candidate_seed: int,
    cache_identity: Mapping[str, Any],
    selection_rule: str,
    complexity_lambda: float,
) -> dict[str, Any]:
    bundle = config["seed_bundles"][int(bundle_index)]
    observations = _observed_selection_trajectories(
        row,
        sigma=sigma,
        rho=rho,
        bundle=bundle,
        bundle_index=bundle_index,
    )
    input_observation = observations["input"][0]
    times = np.asarray(input_observation["times"], dtype=float)
    trajectory = np.asarray(input_observation["trajectory"], dtype=float)
    source_checksum = str(input_observation["source_checksum"])
    if str(cache_identity["input_trajectory_checksum"]) != source_checksum:
        raise RuntimeError("cache identity input checksum mismatch")
    started = perf_counter()
    generation_failure: str | None = None
    try:
        regressor = _make_regressor(model, config, beam_size, candidate_seed)
        fit = fit_and_collect(regressor, times, trajectory, permutation_seed=candidate_seed)
        infixes = list(fit["infixes"])
        trees = list(fit["trees"])
        decode_wall = float(fit["wall_time"])
    except torch.cuda.OutOfMemoryError:
        raise
    except RuntimeError as exc:
        if "out of memory" in str(exc).lower():
            raise
        generation_failure = f"{type(exc).__name__}:{exc}"
        infixes, trees, decode_wall = [], [], perf_counter() - started
    except Exception as exc:
        generation_failure = f"{type(exc).__name__}:{exc}"
        infixes, trees, decode_wall = [], [], perf_counter() - started

    penalty = float(config["selection"]["trajectory_nrmse_failure_penalty"])
    candidates = [
        _evaluate_candidate_trajectories(
            row,
            raw=raw or "",
            tree=tree,
            index=index,
            regressor=regressor,
            observations=observations,
            penalty=penalty,
        )
        for index, (tree, raw) in enumerate(zip(trees, infixes))
    ]
    selected_index = select_candidate(
        candidates,
        selection_rule,
        penalty=penalty,
        complexity_lambda=complexity_lambda,
    )
    selected = (
        dict(candidates[selected_index])
        if selected_index is not None
        else _failed_formula(row, generation_failure or "EmptyCandidateSet")
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
            "input_trajectory_checksum": source_checksum,
            "true_formula": str(row["teacher_infix"]),
            "true_prefix": row["teacher_prefix"],
            "variable_to_gene": dict(row.get("variable_to_gene") or {}),
            "candidate_set_hash": _candidate_hash(infixes),
            "n_candidates": len(candidates),
            "candidate_shortfall": max(int(beam_size) - len(candidates), 0),
            "generation_failure": generation_failure,
            "decode_wall_time_sec": decode_wall,
            "selection_rule": str(selection_rule),
            "complexity_lambda": float(complexity_lambda),
            "selection_trajectory_contract": "corrupted_input_plus_selection_ic_only",
            "generalization_trajectory_accessed": False,
            "observation_provenance": {
                role: [
                    {
                        "role_index": item["role_index"],
                        "corruption_seed": item["corruption_seed"],
                        "source_checksum": item["source_checksum"],
                        "n_points": len(item["times"]),
                    }
                    for item in observations[role]
                ]
                for role in ("input", "selection")
            },
            "selected": selected,
            "candidates": candidates,
        }
    )


def _validation_cell_ce(
    model: Any,
    rows: Sequence[Mapping[str, Any]],
    *,
    config: Mapping[str, Any],
    bundle_indices: Sequence[int],
) -> tuple[float, list[dict[str, Any]]]:
    """Compute CE on the exact paired corrupted input of every formula cell."""
    values: list[dict[str, Any]] = []
    model.eval()
    with torch.no_grad():
        for bundle_index in sorted(int(value) for value in bundle_indices):
            bundle = config["seed_bundles"][bundle_index]
            for row in sorted(rows, key=lambda item: str(item["system_id"])):
                for sigma, rho in corruption_grid(config):
                    observations = _observed_selection_trajectories(
                        row,
                        sigma=sigma,
                        rho=rho,
                        bundle=bundle,
                        bundle_index=bundle_index,
                    )
                    source = observations["input"][0]
                    cell_id = validation_cell_id(
                        system=str(row["system_id"]),
                        bundle_index=bundle_index,
                        noise_sigma=sigma,
                        subsample_rho=rho,
                    )
                    try:
                        loss = teacher_forcing_loss(
                            model,
                            np.asarray(source["times"], dtype=float),
                            np.asarray(source["trajectory"], dtype=float),
                            list(row["tree_encoded"]),
                        )
                        numeric = float(loss.detach().cpu())
                        if not math.isfinite(numeric):
                            raise ValueError("non-finite CE")
                        failure = None
                    except torch.cuda.OutOfMemoryError:
                        raise
                    except Exception as exc:
                        numeric = float("inf")
                        failure = f"{type(exc).__name__}:{exc}"
                    values.append(
                        {
                            "cell_id": cell_id,
                            "system_id": str(row["system_id"]),
                            "bundle_index": bundle_index,
                            "noise_sigma": sigma,
                            "subsample_rho": rho,
                            "input_trajectory_checksum": str(source["source_checksum"]),
                            "ce": numeric,
                            "failure": failure,
                        }
                    )
    finite = [float(row["ce"]) for row in values]
    mean = (
        float(np.mean(finite))
        if finite and all(map(math.isfinite, finite))
        else float("inf")
    )
    return mean, values


def _decode_panel(
    *,
    model: Any,
    rows: Sequence[Mapping[str, Any]],
    config: Mapping[str, Any],
    out: Path,
    campaign_identity_sha256: str,
    stage: str,
    view: str,
    condition: str,
    delta_sha256: str | None,
    beam_size: int,
    bundle_indices: Sequence[int],
    seed_maps: Mapping[int, Mapping[str, int]],
    selection_protocol: Mapping[str, Any],
    selection_artifact_sha256: str,
) -> tuple[list[dict[str, Any]], list[Path]]:
    cells: list[dict[str, Any]] = []
    paths: list[Path] = []
    for bundle_index in sorted(int(value) for value in bundle_indices):
        seed_map = seed_maps[bundle_index]
        for row in sorted(rows, key=lambda item: str(item["system_id"])):
            source_checksum = str(_input_row(row)["checksum"])
            for sigma, rho in corruption_grid(config):
                cell_id = validation_cell_id(
                    system=str(row["system_id"]),
                    bundle_index=bundle_index,
                    noise_sigma=sigma,
                    subsample_rho=rho,
                )
                candidate_seed = int(seed_map[cell_id])
                identity = cell_cache_identity(
                    campaign_identity_sha256=campaign_identity_sha256,
                    stage=stage,
                    view=view,
                    condition=condition,
                    delta_sha256=delta_sha256,
                    beam_size=beam_size,
                    cell_id=cell_id,
                    candidate_seed=candidate_seed,
                    input_trajectory_checksum=source_checksum,
                    candidate_selection_sha256=selection_artifact_sha256,
                )
                path = out / "cells" / stage / view / condition / f"{cell_id}.json"
                cached = load_cached_cell(path, identity)
                if cached is None:
                    cached = _decode_cell(
                        row,
                        model=model,
                        config=config,
                        bundle_index=bundle_index,
                        sigma=sigma,
                        rho=rho,
                        beam_size=beam_size,
                        candidate_seed=candidate_seed,
                        cache_identity=identity,
                        selection_rule=str(selection_protocol["selection_rule"]),
                        complexity_lambda=float(selection_protocol["complexity_lambda"]),
                    )
                    write_cached_cell(path, cached)
                cells.append(cached)
                paths.append(path)
    return cells, paths


def _selected_rows(
    cells: Sequence[Mapping[str, Any]], ce_rows: Sequence[Mapping[str, Any]]
) -> list[dict[str, Any]]:
    ce_by_cell = {str(row["cell_id"]): float(row["ce"]) for row in ce_rows}
    cell_ids = [str(cell["cell_id"]) for cell in cells]
    if sorted(ce_by_cell) != sorted(cell_ids):
        raise RuntimeError("CE coverage does not exactly match formula-cell coverage")
    return [
        {
            "cell_id": str(cell["cell_id"]),
            "system_id": str(cell["system_id"]),
            "bundle_index": int(cell["bundle_index"]),
            "validation_teacher_forcing_ce": ce_by_cell[str(cell["cell_id"])],
            **dict(cell["selected"]),
        }
        for cell in cells
    ]


def _restore_base(model: torch.nn.Module, base_state: Mapping[str, torch.Tensor]) -> None:
    model.load_state_dict(base_state, strict=True)
    model.eval()
    for parameter in model.parameters():
        parameter.requires_grad = False


def _save_current_delta(
    model: torch.nn.Module,
    *,
    out_path: Path,
    parameter_keys: Sequence[str],
    identity: Mapping[str, Any],
    layers: set[str] | None,
    base_sha: str,
    persist: bool,
) -> dict[str, Any]:
    checkpoint = make_delta_checkpoint(
        model,
        allowed_parameter_keys=parameter_keys,
        identity=identity,
        trainable_layers=layers,
        base_model_state_sha256=base_sha,
    )
    saved = save_delta_checkpoint(out_path, checkpoint) if persist else {
        "file_sha256": None,
        "delta_sha256": checkpoint["delta_sha256"],
    }
    return {
        "path": out_path.as_posix() if persist else None,
        "persisted": bool(persist),
        **saved,
        "checkpoint_sha256": checkpoint["checkpoint_sha256"],
        "base_model_state_sha256": checkpoint["base_model_state_sha256"],
        "parameter_keys": list(parameter_keys),
        "parameter_count": int(
            sum(dict(model.named_parameters())[key].numel() for key in parameter_keys)
        ),
        "identity": dict(identity),
    }


def _validate_inputs(root: Path) -> dict[str, Any]:
    phase2_manifest = read_json(root / "phase2" / "manifest.json", {})
    phase3_manifest = read_json(root / "phase3" / "manifest.json", {})
    phase4_manifest = read_json(root / "phase4" / "manifest.json", {})
    phase5_manifest = read_json(root / "phase5" / "manifest.json", {})
    for phase, manifest in (
        (2, phase2_manifest),
        (3, phase3_manifest),
        (4, phase4_manifest),
        (5, phase5_manifest),
    ):
        if manifest.get("status") != "complete" or not all(manifest.get("go_conditions", {}).values()):
            raise RuntimeError(f"Phase {phase} is not complete with all Go conditions true")
    if phase2_manifest.get("test_accessed") is not False:
        raise RuntimeError("Phase 2 test-firewall provenance is invalid")
    if phase3_manifest.get("test_accessed") is not False:
        raise RuntimeError("Phase 3 test-firewall provenance is invalid")
    if phase4_manifest.get("grn_test_accessed") is not False:
        raise RuntimeError("Phase 4 GRN test-firewall provenance is invalid")
    if phase5_manifest.get("test_accessed") is not False:
        raise RuntimeError("Phase 5 test-firewall provenance is invalid")

    # This allowlist is intentionally exhaustive.  Phase 6 must not discover
    # any extra Phase 2 JSON file based on its filename.
    paths = {
        "main_train": root / "phase2" / "train.json",
        "main_validation": root / "phase2" / "validation.json",
        "holdout_train": root / "phase2" / "family_holdout_train.json",
        "holdout_validation": root / "phase2" / "family_holdout_validation.json",
        "official_train": root / "phase4" / "official_train.json",
        "reduced_main": root / "phase4" / "fixed_grn_validation_panel.json",
        "phase3_lambda_selection": root / "phase3" / "lambda_selection.json",
    }
    manifest_by_key = {
        "main_train": phase2_manifest,
        "main_validation": phase2_manifest,
        "holdout_train": phase2_manifest,
        "holdout_validation": phase2_manifest,
        "official_train": phase4_manifest,
        "reduced_main": phase4_manifest,
        "phase3_lambda_selection": phase3_manifest,
    }
    names = {
        "main_train": "train.json",
        "main_validation": "validation.json",
        "holdout_train": "family_holdout_train.json",
        "holdout_validation": "family_holdout_validation.json",
        "official_train": "official_train.json",
        "reduced_main": "fixed_grn_validation_panel.json",
        "phase3_lambda_selection": "lambda_selection.json",
    }
    for key, path in paths.items():
        expected = manifest_by_key[key].get("artifact_sha256", {}).get(names[key])
        if not expected or expected != sha256_file(path):
            raise RuntimeError(f"authorized input artifact hash mismatch: {key}")
    return {
        "paths": paths,
        "phase2_manifest": phase2_manifest,
        "phase3_manifest": phase3_manifest,
        "phase4_manifest": phase4_manifest,
        "phase5_manifest": phase5_manifest,
        "phase3_manifest_path": root / "phase3" / "manifest.json",
    }


def _odebench_path_check(config: Mapping[str, Any]) -> dict[str, Any]:
    """Check the secondary forgetting source only after the protocol freeze."""
    source = ROOT / str(config["gpu_run4_source_run"])
    candidates = source / "phase2" / "all_candidates.json"
    selected = source / "phase2" / "selected.json"
    manifest = source / "phase2" / "manifest.json"
    paths = [manifest, candidates, selected]
    return {
        "purpose": "post-freeze_path_check_only_not_model_selection",
        "available": all(path.is_file() for path in paths),
        "artifacts": [
            {
                "path": path.relative_to(ROOT).as_posix(),
                "sha256": sha256_file(path) if path.is_file() else None,
                "bytes": path.stat().st_size if path.is_file() else None,
            }
            for path in paths
        ],
        "outcomes_read": False,
    }


def main() -> int:
    args = parse_args()
    started_utc, started_clock = utc_now(), perf_counter()
    config = load_config()
    root = run_dir(args.run_id)
    chosen_budget = budget(config, args.smoke)
    inputs = _validate_inputs(root)
    git = git_info()
    if git["status_short"]:
        raise RuntimeError(f"authoritative Phase 6 requires a clean worktree: {git['status_short']}")

    out = phase_dir(args.run_id, 6)
    device = select_device(allow_cpu=args.allow_cpu)
    checkpoint_path = ROOT / str(config["odeformer_checkpoint"])
    raw_checkpoint_sha = sha256_file(checkpoint_path)
    if raw_checkpoint_sha != str(config["odeformer_checkpoint_sha256"]):
        raise RuntimeError("checkpoint SHA256 does not match frozen GPU_RUN5 config")
    environment = software_versions()
    model = load_odeformer_model(checkpoint_path, device=device)
    inventory = inventory_odeformer(model)
    decoder_layers = [
        name for name in inventory["ranking_layers"] if str(name).startswith("decoder_")
    ]
    if len(decoder_layers) != 12:
        raise RuntimeError("GRN decoder-all requires the released checkpoint's 12 decoder blocks")
    base_sha = model_state_sha256(model)
    base_state = {key: value.detach().cpu().clone() for key, value in model.state_dict().items()}

    loaded = {key: read_json(path) for key, path in inputs["paths"].items()}
    phase3_selection = freeze_phase3_selection(loaded.pop("phase3_lambda_selection"))
    if any(not isinstance(value, list) for value in loaded.values()):
        raise RuntimeError("an authorized Phase 6 corpus artifact is not a list")
    view_audit = audit_data_views(
        main_train=loaded["main_train"],
        main_validation=loaded["main_validation"],
        holdout_train=loaded["holdout_train"],
        holdout_validation=loaded["holdout_validation"],
        holdout_train_families=config["family_holdout"]["train_families"],
        holdout_selection_family=str(config["family_holdout"]["selection_family"]),
    )
    if not view_audit["pass"]:
        raise RuntimeError(f"Phase 6 data-view audit failed: {view_audit['pass_flags']}")
    holdout_prestage_dir = root / "phase6_holdout_prestage"
    holdout_prestage_manifest_path = holdout_prestage_dir / "manifest.json"
    holdout_selection_path = holdout_prestage_dir / "selection.json"
    holdout_prestage_manifest = read_json(holdout_prestage_manifest_path, {})
    if (
        holdout_prestage_manifest.get("status") != "complete"
        or not all(holdout_prestage_manifest.get("go_conditions", {}).values())
        or holdout_prestage_manifest.get("test_accessed") is not False
        or holdout_prestage_manifest.get("git", {}).get("commit") != git["commit"]
        or holdout_prestage_manifest.get("git", {}).get("status_short")
        or holdout_prestage_manifest.get("selection_artifact_sha256")
        != sha256_file(holdout_selection_path)
    ):
        raise RuntimeError("signed R06-only selection pre-stage is not complete")
    holdout_selection_artifact = read_json(holdout_selection_path)
    holdout_systems = sorted(
        str(row["system_id"]) for row in loaded["holdout_validation"]
    )
    holdout_expected_cells = [
        phase3_cell_filename(
            system=system,
            bundle_index=bundle_index,
            noise_sigma=sigma,
            subsample_rho=rho,
        ).removesuffix(".json")
        for bundle_index in range(len(config["seed_bundles"]))
        for system in holdout_systems
        for sigma, rho in corruption_grid(config)
    ]
    phase3_config_snapshot_path = root / "phase3" / "config_snapshot.json"
    holdout_selection_protocol = verify_holdout_selection_artifact(
        holdout_selection_artifact,
        expected_cell_ids=holdout_expected_cells,
        expected_system_ids=holdout_systems,
        expected_phase2_manifest_sha256=sha256_file(root / "phase2" / "manifest.json"),
        expected_phase3_config_snapshot_sha256=sha256_file(
            phase3_config_snapshot_path
        ),
        expected_holdout_validation_sha256=sha256_file(
            inputs["paths"]["holdout_validation"]
        ),
        source_root=root,
    )
    holdout_selection_sha = sha256_file(holdout_selection_path)
    expected_prestage_sources = {
        "phase2_manifest_sha256": sha256_file(root / "phase2" / "manifest.json"),
        "family_holdout_validation_sha256": sha256_file(
            inputs["paths"]["holdout_validation"]
        ),
        "phase3_config_snapshot_sha256": sha256_file(phase3_config_snapshot_path),
    }
    if (
        holdout_prestage_manifest.get("safe_sources") != expected_prestage_sources
        or holdout_prestage_manifest.get("selection_signature_sha256")
        != holdout_selection_artifact.get("signature_sha256")
        or holdout_prestage_manifest.get("source_system_ids_sha256")
        != holdout_selection_artifact.get("source_system_ids_sha256")
        or holdout_prestage_manifest.get("source_cell_ids_sha256")
        != holdout_selection_artifact.get("source_cell_ids_sha256")
        or holdout_selection_artifact.get("git", {}).get("commit") != git["commit"]
    ):
        raise RuntimeError("R06-only selection pre-stage provenance mismatch")
    selection_protocols = {
        "main": phase3_selection,
        "family_holdout": holdout_selection_protocol,
    }
    selection_artifact_sha256 = {
        "main": sha256_file(inputs["paths"]["phase3_lambda_selection"]),
        "family_holdout": holdout_selection_sha,
    }
    reduced_ids = {str(row["system_id"]) for row in loaded["reduced_main"]}
    validation_by_id = {str(row["system_id"]): row for row in loaded["main_validation"]}
    if not reduced_ids or not reduced_ids.issubset(validation_by_id):
        raise RuntimeError("Phase 4 reduced GRN panel is not an exact main-validation subset")

    mode = "smoke" if args.smoke else "full"
    n_bundles = int(chosen_budget["n_seeds"])
    if not 1 <= n_bundles <= len(config["seed_bundles"]):
        raise RuntimeError("invalid Phase 6 seed-bundle budget")
    learning_rates = [float(value) for value in chosen_budget["hyperparameter_learning_rates"]]
    steps = [int(value) for value in chosen_budget["hyperparameter_steps"]]
    grid = hyperparameter_grid(learning_rates, steps)
    if not args.smoke and len(grid) != 9:
        raise RuntimeError("authoritative Phase 6 requires the exact 3 x 3 grid")
    max_steps = max(steps)
    screen_beam = int(config["training"]["screening_beam_size"])
    confirmation_beam = (
        int(chosen_budget["beam_size"])
        if args.smoke
        else int(config["training"]["confirmation_beam_size"])
    )
    reduced_count = int(chosen_budget["reduced_panel"])
    screen_main = [validation_by_id[name] for name in sorted(reduced_ids)]
    if args.smoke:
        screen_main = screen_main[:reduced_count]
    elif len(screen_main) != 24:
        raise RuntimeError("authoritative main screening panel must contain exactly 24 systems")
    screen_holdout = _panel_rows(
        loaded["holdout_validation"],
        min(reduced_count, len(loaded["holdout_validation"])),
    )
    confirmation_rows = {
        "main": sorted(loaded["main_validation"], key=lambda row: str(row["system_id"])),
        "family_holdout": sorted(
            loaded["holdout_validation"], key=lambda row: str(row["system_id"])
        ),
    }
    screen_rows = {"main": screen_main, "family_holdout": screen_holdout}
    train_rows = {
        "main": loaded["main_train"],
        "family_holdout": loaded["holdout_train"],
    }
    if args.smoke:
        per_family_train = int(chosen_budget["train_variants_per_family"])
        per_family_validation = int(chosen_budget["validation_variants_per_family"])
        train_rows = {
            view: _variants_per_family(rows, per_family_train)
            for view, rows in train_rows.items()
        }
        confirmation_rows = {
            view: _variants_per_family(rows, per_family_validation)
            for view, rows in confirmation_rows.items()
        }
        loaded["official_train"] = sorted(
            loaded["official_train"], key=lambda row: str(row["problem_id"])
        )[: int(chosen_budget["official_corpus_train"])]
    panel_hashes = {
        f"{stage}:{view}": fingerprint_json(
            [str(row["system_id"]) for row in rows]
        )
        for stage, mapping in (("screening", screen_rows), ("confirmation", confirmation_rows))
        for view, rows in mapping.items()
    }
    campaign_identity = {
        "schema_version": "gpu_run5_phase6_campaign_v1",
        "git_commit": git["commit"],
        "mode": mode,
        "config_fingerprint": fingerprint_json(config),
        "raw_checkpoint_sha256": raw_checkpoint_sha,
        "base_model_state_sha256": base_sha,
        "device": device,
        "environment_fingerprint": fingerprint_json(environment),
        "authorized_input_sha256": {
            **{key: sha256_file(path) for key, path in inputs["paths"].items()},
            "phase3_manifest": sha256_file(inputs["phase3_manifest_path"]),
        },
        "screening_beam_size": screen_beam,
        "confirmation_beam_size": confirmation_beam,
        "learning_rates": learning_rates,
        "snapshot_steps": steps,
        "panel_sha256": panel_hashes,
        "candidate_selection_by_view": selection_protocols,
        "candidate_selection_artifact_sha256_by_view": selection_artifact_sha256,
        "validation_ce_policy": {
            "name": "paired_corrupted_input_trajectory_per_formula_cell",
            "coverage": "every system_x_bundle_x_noise_sigma_x_subsample_rho formula cell",
            "teacher_target": "same system teacher prefix",
            "selection_ic_used_for_ce": False,
            "role_in_model_selection": "fourth_lexicographic_tie_break_only",
        },
        "test_accessed": False,
    }
    campaign_sha = fingerprint_json(campaign_identity)
    view_campaign_identities = {
        "main": {
            "schema_version": "gpu_run5_phase6_view_campaign_v1",
            "view": "main",
            "git_commit": git["commit"],
            "mode": mode,
            "config_fingerprint": fingerprint_json(config),
            "raw_checkpoint_sha256": raw_checkpoint_sha,
            "base_model_state_sha256": base_sha,
            "selection_protocol": selection_protocols["main"],
            "selection_artifact_sha256": selection_artifact_sha256["main"],
            "authorized_inputs": {
                key: sha256_file(inputs["paths"][key])
                for key in (
                    "main_train",
                    "main_validation",
                    "official_train",
                    "reduced_main",
                    "phase3_lambda_selection",
                )
            },
        },
        "family_holdout": {
            "schema_version": "gpu_run5_phase6_view_campaign_v1",
            "view": "family_holdout",
            "git_commit": git["commit"],
            "mode": mode,
            "config_fingerprint": fingerprint_json(config),
            "raw_checkpoint_sha256": raw_checkpoint_sha,
            "base_model_state_sha256": base_sha,
            "selection_protocol": selection_protocols["family_holdout"],
            "selection_artifact_sha256": selection_artifact_sha256[
                "family_holdout"
            ],
            "authorized_inputs": {
                "holdout_train": sha256_file(inputs["paths"]["holdout_train"]),
                "holdout_validation": sha256_file(
                    inputs["paths"]["holdout_validation"]
                ),
                "official_train": sha256_file(inputs["paths"]["official_train"]),
                "phase2_manifest": sha256_file(root / "phase2" / "manifest.json"),
                "phase3_config_snapshot": sha256_file(phase3_config_snapshot_path),
                "R06_prestage_manifest": sha256_file(
                    holdout_prestage_manifest_path
                ),
                "R06_selection": holdout_selection_sha,
            },
        },
    }
    view_campaign_sha256 = {
        view: fingerprint_json(identity)
        for view, identity in view_campaign_identities.items()
    }
    write_json(out / "protocol_frozen.json", campaign_identity)
    write_json(
        out / "view_protocols_frozen.json",
        {
            "view_campaign_identities": view_campaign_identities,
            "view_campaign_identity_sha256": view_campaign_sha256,
        },
    )
    write_json(out / "data_view_audit.json", view_audit)
    write_json(out / "config_snapshot.json", config)

    screen_seed_maps = {
        view: {
            0: candidate_seed_map(rows, config=config, bundle_indices=[0])
        }
        for view, rows in screen_rows.items()
    }
    selection_payload: dict[str, Any] = {
        "schema_version": "gpu_run5_phase6_selection_freeze_v1",
        "campaign_identity_sha256": campaign_sha,
        "view_campaign_identity_sha256": view_campaign_sha256,
        "criterion": "formula_exact_then_failure_aware_ted_then_valid_then_ce",
        "candidate_selection_by_view": selection_protocols,
        "candidate_selection_artifact_sha256_by_view": selection_artifact_sha256,
        "trajectory_selection_roles": ["input", "selection"],
        "generalization_used_for_selection": False,
        "screening_bundle_indices": [0],
        "screening_beam_size": screen_beam,
        "views": {},
        "test_accessed": False,
    }
    screening_paths: list[Path] = []
    screening_delta_records: dict[tuple[str, str], dict[str, Any]] = {}

    for view in VIEWS:
        rows = screen_rows[view]
        expected_cells = sorted(screen_seed_maps[view][0])
        validation_panel_sha = panel_hashes[f"screening:{view}"]
        view_selection: dict[str, Any] = {}
        for condition in TRAINABLE_CONDITIONS:
            corpus = _condition_corpus(
                condition,
                official_train=loaded["official_train"],
                grn_train=train_rows[view],
            )
            normalized = adapt_input_training_records(corpus)
            schedule = training_order(
                normalized,
                steps=max_steps,
                seed=int(config["seed_bundles"][0]["data_seed"]),
            )
            seed_map_sha = candidate_seed_map_sha256(screen_seed_maps[view][0])
            trial_identity = build_trial_identity(
                condition=condition,
                view=view,
                bundle_indices=[0],
                base_model_state_sha256=base_sha,
                training_corpus_sha256=schedule["training_corpus_sha256"],
                training_order_sha256=schedule["order_sha256"],
                model_seed=int(config["seed_bundles"][0]["model_seed"]),
                validation_panel_sha256=validation_panel_sha,
                candidate_seed_map_sha256_value=seed_map_sha,
            )
            candidates: list[dict[str, Any]] = []
            layers = _condition_layers(condition, decoder_layers)
            for lr in learning_rates:
                _restore_base(model, base_state)
                result = train_adam_with_snapshots(
                    model,
                    corpus,
                    trainable_layers=layers,
                    lr=lr,
                    max_steps=max_steps,
                    snapshot_steps=steps,
                    data_order_seed=int(config["seed_bundles"][0]["data_seed"]),
                    model_seed=int(config["seed_bundles"][0]["model_seed"]),
                )
                if (
                    result["training_corpus_sha256"] != schedule["training_corpus_sha256"]
                    or result["order_sha256"] != schedule["order_sha256"]
                ):
                    raise RuntimeError("training helper returned an unpaired schedule identity")
                for step in steps:
                    config_row = {"lr": float(lr), "steps": int(step)}
                    if step not in result["snapshots"]:
                        candidates.append(
                            {
                                "status": "failed",
                                "failure_reason": result["failure_reason"] or "MissingExactSnapshot",
                                "config": config_row,
                                "trial_identity": trial_identity,
                                "validation_cell_ids": [],
                                "score_vector": [0.0, -1.0, 0.0, -float("inf")],
                                "training": {
                                    key: value for key, value in result.items() if key != "snapshots"
                                },
                            }
                        )
                        continue
                    restore_parameter_state(
                        model,
                        result["snapshots"][step],
                        allowed_parameter_keys=result["trainable_parameter_keys"],
                    )
                    identity = delta_identity(
                        trial_identity,
                        stage="screening",
                        lr=lr,
                        steps=step,
                        raw_checkpoint_sha256=raw_checkpoint_sha,
                        config_fingerprint=fingerprint_json(config),
                        training_source=(
                            "official_train" if condition == "official_continued_full" else f"{view}_grn_train"
                        ),
                    )
                    delta = _save_current_delta(
                        model,
                        out_path=out / "checkpoints" / "screening" / view / condition / f"lr{lr:g}_s{step}.pt",
                        parameter_keys=result["trainable_parameter_keys"],
                        identity=identity,
                        layers=layers,
                        base_sha=base_sha,
                        persist=False,
                    )
                    cells, paths = _decode_panel(
                        model=model,
                        rows=rows,
                        config=config,
                        out=out,
                        campaign_identity_sha256=view_campaign_sha256[view],
                        stage=f"screening_lr{lr:g}_s{step}",
                        view=view,
                        condition=condition,
                        delta_sha256=delta["delta_sha256"],
                        beam_size=screen_beam,
                        bundle_indices=[0],
                        seed_maps=screen_seed_maps[view],
                        selection_protocol=selection_protocols[view],
                        selection_artifact_sha256=selection_artifact_sha256[view],
                    )
                    screening_paths.extend(paths)
                    coverage = coverage_audit(
                        cells,
                        expected_cell_ids=expected_cells,
                        expected_beam_size=screen_beam,
                        expected_seed_map=screen_seed_maps[view][0],
                    )
                    if not coverage["pass"]:
                        raise RuntimeError(f"screening coverage failed: {view}/{condition}/{config_row}")
                    ce, ce_rows = _validation_cell_ce(
                        model, rows, config=config, bundle_indices=[0]
                    )
                    selected_rows = _selected_rows(cells, ce_rows)
                    score = formula_score_vector(
                        selected_rows,
                        expected_cell_ids=expected_cells,
                    )
                    candidates.append(
                        {
                            "status": "complete",
                            "failure_reason": None,
                            "config": config_row,
                            "trial_identity": trial_identity,
                            "validation_cell_ids": expected_cells,
                            "score_vector": list(score),
                            "validation_teacher_forcing_ce": ce,
                            "validation_ce_rows": ce_rows,
                            "coverage_audit": coverage,
                            "delta": delta,
                            "training": {
                                key: value for key, value in result.items() if key not in {"snapshots", "losses"}
                            },
                            "losses": result["losses"][:step],
                        }
                    )
                del result
                gc.collect()
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
            selected = select_formula_candidate(
                candidates,
                expected_count=len(grid),
                expected_lrs=learning_rates,
                expected_steps=steps,
                quantization_digits=12,
                expected_validation_cell_ids=expected_cells,
            )
            view_selection[condition] = selected
            screening_delta_records[(view, condition)] = dict(selected["selected"]["delta"])
            print(
                f"Phase6 screening {view}/{condition}: selected "
                f"lr={selected['selected']['config']['lr']:g} "
                f"steps={selected['selected']['config']['steps']}",
                flush=True,
            )
        selection_payload["views"][view] = view_selection

    # This write is the irreversible validation freeze.  Everything below may
    # confirm the frozen choices but may not alter them.
    write_json(out / "hyperparameter_freeze.json", selection_payload)
    freeze_sha = sha256_file(out / "hyperparameter_freeze.json")
    odebench_check = _odebench_path_check(config)
    write_json(out / "odebench_forgetting_path_check.json", odebench_check)

    confirmation_paths: list[Path] = []
    checkpoint_records: list[dict[str, Any]] = []
    confirmation_training_records: list[dict[str, Any]] = []
    confirmation_training_paths: list[Path] = []
    confirmation_records: dict[str, Any] = {}
    bundle_indices = list(range(n_bundles))
    for view in VIEWS:
        rows = confirmation_rows[view]
        seed_maps = {
            bundle_index: candidate_seed_map(
                rows, config=config, bundle_indices=[bundle_index]
            )
            for bundle_index in bundle_indices
        }
        expected_by_bundle = {
            bundle_index: sorted(seed_maps[bundle_index]) for bundle_index in bundle_indices
        }
        view_records: dict[str, Any] = {}

        _restore_base(model, base_state)
        frozen_cells, paths = _decode_panel(
            model=model,
            rows=rows,
            config=config,
            out=out,
            campaign_identity_sha256=view_campaign_sha256[view],
            stage="confirmation",
            view=view,
            condition="frozen",
            delta_sha256=None,
            beam_size=confirmation_beam,
            bundle_indices=bundle_indices,
            seed_maps=seed_maps,
            selection_protocol=selection_protocols[view],
            selection_artifact_sha256=selection_artifact_sha256[view],
        )
        confirmation_paths.extend(paths)
        frozen_expected = [item for bundle in bundle_indices for item in expected_by_bundle[bundle]]
        merged_seed_map = {
            key: value for bundle in bundle_indices for key, value in seed_maps[bundle].items()
        }
        frozen_coverage = coverage_audit(
            frozen_cells,
            expected_cell_ids=frozen_expected,
            expected_beam_size=confirmation_beam,
            expected_seed_map=merged_seed_map,
        )
        frozen_ce, frozen_ce_rows = _validation_cell_ce(
            model, rows, config=config, bundle_indices=bundle_indices
        )
        frozen_score = formula_score_vector(
            _selected_rows(frozen_cells, frozen_ce_rows),
            expected_cell_ids=frozen_expected,
        )
        view_records["frozen"] = {
            "score_vector": list(frozen_score),
            "validation_teacher_forcing_ce": frozen_ce,
            "validation_ce_rows": frozen_ce_rows,
            "coverage_audit": frozen_coverage,
            "cells": len(frozen_cells),
        }

        for condition in TRAINABLE_CONDITIONS:
            selected_config = selection_payload["views"][view][condition]["selected"]["config"]
            lr, selected_step = float(selected_config["lr"]), int(selected_config["steps"])
            layers = _condition_layers(condition, decoder_layers)
            corpus = _condition_corpus(
                condition,
                official_train=loaded["official_train"],
                grn_train=train_rows[view],
            )
            all_cells: list[dict[str, Any]] = []
            ce_rows_by_bundle: dict[str, Any] = {}
            for bundle_index in bundle_indices:
                _restore_base(model, base_state)
                bundle = config["seed_bundles"][bundle_index]
                result = train_adam_with_snapshots(
                    model,
                    corpus,
                    trainable_layers=layers,
                    lr=lr,
                    max_steps=selected_step,
                    snapshot_steps=[selected_step],
                    data_order_seed=int(bundle["data_seed"]),
                    model_seed=int(bundle["model_seed"]),
                )
                training_path = (
                    out
                    / "training"
                    / "confirmation"
                    / view
                    / condition
                    / f"bundle{bundle_index}.json"
                )
                training_record = {
                    "path": training_path.relative_to(out).as_posix(),
                    "view": view,
                    "condition": condition,
                    "bundle_index": bundle_index,
                    "selected_config": selected_config,
                    "checkpoint_file_sha256": None,
                    "delta_sha256": None,
                    **{
                        key: value
                        for key, value in result.items()
                        if key != "snapshots"
                    },
                }
                write_json(training_path, training_record)
                confirmation_training_paths.append(training_path)
                if result["status"] != "complete" or selected_step not in result["snapshots"]:
                    raise RuntimeError(
                        f"selected confirmation training failed: {view}/{condition}/bundle{bundle_index}: "
                        f"{result['failure_reason']}"
                    )
                restore_parameter_state(
                    model,
                    result["snapshots"][selected_step],
                    allowed_parameter_keys=result["trainable_parameter_keys"],
                )
                trial_identity = build_trial_identity(
                    condition=condition,
                    view=view,
                    bundle_indices=[bundle_index],
                    base_model_state_sha256=base_sha,
                    training_corpus_sha256=result["training_corpus_sha256"],
                    training_order_sha256=result["order_sha256"],
                    model_seed=int(bundle["model_seed"]),
                    validation_panel_sha256=panel_hashes[f"confirmation:{view}"],
                    candidate_seed_map_sha256_value=candidate_seed_map_sha256(
                        seed_maps[bundle_index]
                    ),
                )
                identity = delta_identity(
                    trial_identity,
                    stage="confirmation",
                    lr=lr,
                    steps=selected_step,
                    raw_checkpoint_sha256=raw_checkpoint_sha,
                    config_fingerprint=fingerprint_json(config),
                    training_source=(
                        "official_train" if condition == "official_continued_full" else f"{view}_grn_train"
                    ),
                )
                delta = _save_current_delta(
                    model,
                    out_path=out / "checkpoints" / "confirmation" / view / condition / f"bundle{bundle_index}.pt",
                    parameter_keys=result["trainable_parameter_keys"],
                    identity=identity,
                    layers=layers,
                    base_sha=base_sha,
                    persist=True,
                )
                adapted_state_sha = model_state_sha256(model)
                _restore_base(model, base_state)
                restored_base_sha = model_state_sha256(model)
                loaded_delta = load_delta_checkpoint(
                    Path(str(delta["path"])),
                    expected_file_sha256=str(delta["file_sha256"]),
                )
                apply_delta_checkpoint(
                    model,
                    loaded_delta,
                    allowed_parameter_keys=result["trainable_parameter_keys"],
                    expected_identity=identity,
                )
                reloaded_state_sha = model_state_sha256(model)
                delta["verification"] = {
                    "strategy": "restore_fresh_base_state_then_load_and_apply_delta",
                    "fresh_base_state_sha256": restored_base_sha,
                    "fresh_base_matches_expected": restored_base_sha == base_sha,
                    "file_sha256_verified": True,
                    "metadata_identity_verified": True,
                    "parameter_allowlist_verified": True,
                    "tensor_delta_sha256_verified": True,
                    "adapted_model_state_sha256_before_save": adapted_state_sha,
                    "adapted_model_state_sha256_after_reload": reloaded_state_sha,
                    "adapted_state_matches": reloaded_state_sha == adapted_state_sha,
                }
                verification_flags = [
                    value
                    for key, value in delta["verification"].items()
                    if key.endswith("_verified")
                    or key.endswith("_matches_expected")
                    or key == "adapted_state_matches"
                ]
                if not verification_flags or not all(verification_flags):
                    raise RuntimeError("persisted delta failed fresh-base reload verification")
                if bundle_index == 0:
                    delta["matches_selected_screening_delta"] = (
                        delta["delta_sha256"]
                        == screening_delta_records[(view, condition)]["delta_sha256"]
                    )
                    if not delta["matches_selected_screening_delta"]:
                        raise RuntimeError("bundle-0 confirmation does not reproduce selected screening delta")
                delta["training_record_path"] = training_record["path"]
                checkpoint_records.append({"view": view, "condition": condition, "bundle_index": bundle_index, **delta})
                training_record["checkpoint_file_sha256"] = delta["file_sha256"]
                training_record["delta_sha256"] = delta["delta_sha256"]
                write_json(training_path, training_record)
                confirmation_training_records.append(training_record)
                cells, paths = _decode_panel(
                    model=model,
                    rows=rows,
                    config=config,
                    out=out,
                    campaign_identity_sha256=view_campaign_sha256[view],
                    stage="confirmation",
                    view=view,
                    condition=condition,
                    delta_sha256=delta["delta_sha256"],
                    beam_size=confirmation_beam,
                    bundle_indices=[bundle_index],
                    seed_maps={bundle_index: seed_maps[bundle_index]},
                    selection_protocol=selection_protocols[view],
                    selection_artifact_sha256=selection_artifact_sha256[view],
                )
                confirmation_paths.extend(paths)
                all_cells.extend(cells)
                ce, ce_detail = _validation_cell_ce(
                    model, rows, config=config, bundle_indices=[bundle_index]
                )
                ce_rows_by_bundle[str(bundle_index)] = {"mean": ce, "rows": ce_detail}
                del result
                gc.collect()
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
            condition_coverage = coverage_audit(
                all_cells,
                expected_cell_ids=frozen_expected,
                expected_beam_size=confirmation_beam,
                expected_seed_map=merged_seed_map,
            )
            # CE is macro over paired bundle means; formula rows themselves
            # remain system->bundle->corruption for the primary score.
            condition_ce = float(
                np.mean([ce_rows_by_bundle[str(index)]["mean"] for index in bundle_indices])
            )
            condition_ce_rows = [
                row
                for index in bundle_indices
                for row in ce_rows_by_bundle[str(index)]["rows"]
            ]
            condition_score = formula_score_vector(
                _selected_rows(all_cells, condition_ce_rows),
                expected_cell_ids=frozen_expected,
            )
            view_records[condition] = {
                "selected_config": selected_config,
                "score_vector": list(condition_score),
                "validation_teacher_forcing_ce": condition_ce,
                "validation_ce_by_bundle": ce_rows_by_bundle,
                "coverage_audit": condition_coverage,
                "cells": len(all_cells),
            }
        confirmation_records[view] = view_records

    write_json(out / "confirmation_summary.json", confirmation_records)
    write_json(out / "checkpoint_index.json", checkpoint_records)
    write_json(out / "confirmation_training_index.json", confirmation_training_records)
    write_json(
        out / "confirmation_training_artifact_index.json",
        artifact_index(confirmation_training_paths, relative_to=out),
    )
    all_cell_paths = screening_paths + confirmation_paths
    cell_index = artifact_index(all_cell_paths, relative_to=out)
    write_json(out / "cell_artifact_index.json", cell_index)

    n_corruptions = len(corruption_grid(config))
    expected_counts = expected_phase6_counts(
        screen_systems={view: len(rows) for view, rows in screen_rows.items()},
        confirmation_systems={view: len(rows) for view, rows in confirmation_rows.items()},
        n_grid_candidates=len(grid),
        n_bundles=n_bundles,
        n_corruptions=n_corruptions,
    )
    observed_trainable_grid = sum(
        selection_payload["views"][view][condition]["candidate_count"]
        for view in VIEWS
        for condition in TRAINABLE_CONDITIONS
    )
    observed_confirmation = sum(
        int(confirmation_records[view][condition]["cells"])
        for view in VIEWS
        for condition in ("frozen", *TRAINABLE_CONDITIONS)
    )
    all_coverages_pass = all(
        confirmation_records[view][condition]["coverage_audit"]["pass"]
        for view in VIEWS
        for condition in ("frozen", *TRAINABLE_CONDITIONS)
    )
    all_screen_coverages_pass = all(
        trial["coverage_audit"]["pass"]
        for view in VIEWS
        for condition in TRAINABLE_CONDITIONS
        for trial in selection_payload["views"][view][condition]["trials"]
        if trial["status"] == "complete"
    )
    all_delta_verifications_pass = len(checkpoint_records) == expected_counts[
        "selected_training_trials"
    ] and all(
        row["base_model_state_sha256"] == base_sha
        and bool(row.get("matches_selected_screening_delta", True))
        and row["verification"]["fresh_base_matches_expected"]
        and row["verification"]["file_sha256_verified"]
        and row["verification"]["metadata_identity_verified"]
        and row["verification"]["parameter_allowlist_verified"]
        and row["verification"]["tensor_delta_sha256_verified"]
        and row["verification"]["adapted_state_matches"]
        for row in checkpoint_records
    )
    confirmation_training_audit_pass = len(confirmation_training_records) == expected_counts[
        "selected_training_trials"
    ] and all(
        row["status"] == "complete"
        and row["completed_steps"] == row["requested_steps"]
        and len(row["losses"]) == row["completed_steps"]
        and row["optimizer"] == "Adam"
        and row["determinism"]["deterministic_algorithms"] is True
        and row["determinism"]["cudnn_benchmark"] is False
        and row["determinism"]["cudnn_deterministic"] is True
        and math.isfinite(float(row["wall_time_sec"]))
        and "peak_gpu_memory_bytes" in row
        for row in confirmation_training_records
    )
    go = {
        "phase2_phase3_phase4_phase5_complete_and_hashed": True,
        "test_not_accessed": True,
        "main_and_family_holdout_views_separate": bool(view_audit["pass"]),
        "every_trainable_condition_received_exact_grid": observed_trainable_grid
        == len(VIEWS) * len(TRAINABLE_CONDITIONS) * len(grid),
        "one_lr_run_produced_exact_snapshots": all(
            trial["training"]["requested_steps"] == max_steps
            for view in VIEWS
            for condition in TRAINABLE_CONDITIONS
            for trial in selection_payload["views"][view][condition]["trials"]
            if trial["status"] == "complete"
        ),
        "screening_beam_and_bundle_contract_exact": all_screen_coverages_pass,
        "main_phase3_multi_ic_complexity_lambda_frozen": phase3_selection
        == {
            "selection_rule": PHASE3_SELECTION_RULE,
            "complexity_lambda": PHASE3_COMPLEXITY_LAMBDA,
            "source_split": "validation",
            "candidate_lambdas": [0.0, 0.0001, 0.001, 0.01],
        },
        "family_holdout_R06_only_selection_signed_and_frozen": (
            holdout_selection_artifact["source_family"] == "R06"
            and holdout_selection_artifact["source_cell_count"]
            == len(loaded["holdout_validation"])
            * len(config["seed_bundles"])
            * len(corruption_grid(config))
            and all(
                row["family"] == "R06"
                for row in holdout_selection_artifact["source_artifacts"]
            )
            and holdout_selection_artifact["forbidden_family_outcomes_accessed"] is False
            and holdout_selection_protocol["selection_artifact_signature_sha256"]
            == holdout_selection_artifact["signature_sha256"]
            and holdout_selection_sha
            == sha256_file(holdout_selection_path)
            and holdout_prestage_manifest["selection_signature_sha256"]
            == holdout_selection_artifact["signature_sha256"]
        ),
        "family_holdout_cache_identity_excludes_main_selection": (
            selection_artifact_sha256["main"]
            not in json.dumps(
                view_campaign_identities["family_holdout"],
                sort_keys=True,
                separators=(",", ":"),
            )
        ),
        "formula_primary_selection_frozen_before_confirmation": freeze_sha
        == sha256_file(out / "hyperparameter_freeze.json"),
        "selected_and_frozen_confirmation_exact": all_coverages_pass
        and observed_confirmation == expected_counts["confirmation_cells_total"],
        "confirmation_training_history_complete": confirmation_training_audit_pass,
        "persisted_delta_fresh_base_reload_verified": all_delta_verifications_pass,
        "paired_candidate_seed_maps_and_atomic_cell_identities_pass": all_coverages_pass
        and all_screen_coverages_pass,
        "all_formulas_failures_and_artifact_hashes_saved": len(cell_index)
        == expected_counts["all_decode_cells_total"],
        "odebench_check_is_post_freeze_path_only": odebench_check["available"]
        and odebench_check["outcomes_read"] is False,
        "git_commit_and_cleanliness_stable": git_info()["commit"] == git["commit"]
        and not git_info()["status_short"],
    }
    status = "complete" if all(go.values()) else "incomplete"
    summary = {
        "status": status,
        "mode": mode,
        "campaign_identity_sha256": campaign_sha,
        "hyperparameter_freeze_sha256": freeze_sha,
        "candidate_selection_by_view": selection_protocols,
        "candidate_selection_artifact_sha256_by_view": selection_artifact_sha256,
        "expected_counts": expected_counts,
        "observed": {
            "grid_candidates": observed_trainable_grid,
            "screening_cells": len(screening_paths),
            "confirmation_cells": observed_confirmation,
            "checkpoint_count": len(checkpoint_records),
            "confirmation_training_records": len(confirmation_training_records),
        },
        "selected_hyperparameters": {
            view: {
                condition: selection_payload["views"][view][condition]["selected"]["config"]
                for condition in TRAINABLE_CONDITIONS
            }
            for view in VIEWS
        },
        "confirmation_formula_scores": {
            view: {
                condition: confirmation_records[view][condition]["score_vector"]
                for condition in ("frozen", *TRAINABLE_CONDITIONS)
            }
            for view in VIEWS
        },
        "go_conditions": go,
        "test_accessed": False,
    }
    write_json(out / "summary.json", summary)
    write_json(out / "go.json", go)
    artifact_names = [
        "protocol_frozen.json",
        "view_protocols_frozen.json",
        "data_view_audit.json",
        "config_snapshot.json",
        "hyperparameter_freeze.json",
        "odebench_forgetting_path_check.json",
        "confirmation_summary.json",
        "checkpoint_index.json",
        "confirmation_training_index.json",
        "confirmation_training_artifact_index.json",
        "cell_artifact_index.json",
        "summary.json",
        "go.json",
    ]
    manifest_payload = sanitize_nonfinite(
        {
            "go_conditions": go,
            "summary": summary,
            "git": git_info(),
            "git_at_start": git,
            "started_utc": started_utc,
            "finished_utc": utc_now(),
            "wall_time_sec": perf_counter() - started_clock,
            "mode": mode,
            "device": device,
            "environment": environment,
            "checkpoint": {
                "path": str(checkpoint_path),
                "sha256": raw_checkpoint_sha,
                "base_model_state_sha256": base_sha,
            },
            "config_fingerprint": fingerprint_json(config),
            "campaign_identity": campaign_identity,
            "campaign_identity_sha256": campaign_sha,
            "view_campaign_identities": view_campaign_identities,
            "view_campaign_identity_sha256": view_campaign_sha256,
            "hyperparameter_freeze_sha256": freeze_sha,
            "authorized_inputs": {
                **{key: sha256_file(path) for key, path in inputs["paths"].items()},
                "phase3_manifest": sha256_file(inputs["phase3_manifest_path"]),
                "R06_prestage_manifest": sha256_file(
                    holdout_prestage_manifest_path
                ),
                "R06_selection": holdout_selection_sha,
            },
            "phase_manifests": {
                "phase2": sha256_file(root / "phase2" / "manifest.json"),
                "phase3": sha256_file(root / "phase3" / "manifest.json"),
                "phase4": sha256_file(root / "phase4" / "manifest.json"),
                "phase5": sha256_file(root / "phase5" / "manifest.json"),
            },
            "test_accessed": False,
            "odebench_outcomes_read": False,
            "artifact_sha256": {
                name: sha256_file(out / name) for name in artifact_names
            },
        }
    )
    write_manifest(out, 6, status, **manifest_payload)
    print(
        f"GPU_RUN5 Phase 6 {status}: grid={observed_trainable_grid} "
        f"screen={len(screening_paths)} confirm={observed_confirmation}",
        flush=True,
    )
    return 0 if status == "complete" else 1


if __name__ == "__main__":
    raise SystemExit(main())
