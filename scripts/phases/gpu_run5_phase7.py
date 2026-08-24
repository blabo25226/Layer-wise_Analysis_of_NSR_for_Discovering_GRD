"""GPU_RUN5 Phase 7: view-separated single-block IOLE and layer freeze.

Only Phase 2 train/validation views and validation-only Phase 4--6 artifacts
are authorized.  No sealed GRN artifact is named or discovered.  Every one of
the released checkpoint's 16 Transformer blocks receives the same LR by step
grid on a reduced validation panel.  The resulting rank and layer sets are
irreversibly frozen before beam-50, three-bundle confirmation.
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
from gpu_run4.inference import fit_and_collect  # noqa: E402
from gpu_run4_runtime import load_odeformer_model, select_device  # noqa: E402
from gpu_run5.config import (  # noqa: E402
    budget,
    load_config,
    phase_dir,
    read_json,
    run_dir,
    sanitize_nonfinite,
    write_manifest,
)
from gpu_run5.evaluation import select_candidate  # noqa: E402
from gpu_run5.phase6 import (  # noqa: E402
    artifact_index,
    candidate_seed_map,
    candidate_seed_map_sha256,
    corruption_grid,
    coverage_audit,
    hyperparameter_grid,
    load_cached_cell,
    validation_cell_id,
    write_cached_cell,
)
from gpu_run5.phase7 import (  # noqa: E402
    CONFIRMATION_BEAM_SIZE,
    RANDOM_LAYER_SEED,
    SCORE_QUANTIZATION_DIGITS,
    SCREENING_BEAM_SIZE,
    VIEWS,
    confirmation_rank_stability,
    contribution_records,
    expected_phase7_counts,
    freeze_layer_sets,
    freeze_selected_hyperparameters,
    freeze_view_selection_contracts,
    phase7_cell_identity,
    phase7_delta_identity,
    phase7_trial_identity,
)
from gpu_run5.training import (  # noqa: E402
    OFFICIAL_LAYER_REGISTRY,
    adapt_input_training_records,
    formula_score_vector,
    model_state_sha256,
    restore_parameter_state,
    select_formula_candidate,
    tie_aware_vector_ranking,
    train_adam_with_snapshots,
    training_order,
)
from scripts.phases.gpu_run5_phase6 import (  # noqa: E402
    _evaluate_candidate_trajectories,
    _failed_formula,
    _input_row,
    _make_regressor,
    _observed_selection_trajectories,
    _panel_rows,
    _restore_base,
    _save_current_delta,
    _selected_rows,
    _validation_cell_ce,
    _variants_per_family,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", default=os.environ.get("LANSR_RUN_ID"))
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--allow-cpu", action="store_true")
    return parser.parse_args()


def write_json(path: Path, payload: Any) -> Path:
    """Atomically write strict interoperable JSON."""
    return _write_json(path, sanitize_nonfinite(payload))


def _candidate_hash(infixes: Sequence[str | None]) -> str:
    return hashlib.sha256(
        json.dumps(
            [value or "" for value in infixes],
            ensure_ascii=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def _decode_cell(
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
) -> dict[str, Any]:
    """Decode and persist every candidate using a view-specific lambda."""
    bundle = config["seed_bundles"][int(bundle_index)]
    observations = _observed_selection_trajectories(
        row,
        sigma=sigma,
        rho=rho,
        bundle=bundle,
        bundle_index=bundle_index,
    )
    input_observation = observations["input"][0]
    source_checksum = str(input_observation["source_checksum"])
    if str(cache_identity["input_trajectory_checksum"]) != source_checksum:
        raise RuntimeError("cache identity input checksum mismatch")
    times = np.asarray(input_observation["times"], dtype=float)
    trajectory = np.asarray(input_observation["trajectory"], dtype=float)
    started = perf_counter()
    generation_failure: str | None = None
    try:
        regressor = _make_regressor(model, config, beam_size, candidate_seed)
        fit = fit_and_collect(
            regressor, times, trajectory, permutation_seed=candidate_seed
        )
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
    rule = str(selection_contract["selection_rule"])
    complexity_lambda = float(selection_contract["complexity_lambda"])
    selected_index = select_candidate(
        candidates,
        rule,
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
            "condition": "grn_single_block",
            "layer": str(cache_identity["layer"]),
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
            "selection_rule": rule,
            "complexity_lambda": complexity_lambda,
            "selection_contract_sha256": str(
                cache_identity["selection_contract_sha256"]
            ),
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


def _decode_panel(
    *,
    model: Any,
    rows: Sequence[Mapping[str, Any]],
    config: Mapping[str, Any],
    selection_contract: Mapping[str, Any],
    out: Path,
    campaign_identity_sha256: str,
    stage: str,
    view: str,
    layer: str,
    delta_sha256: str,
    beam_size: int,
    bundle_indices: Sequence[int],
    seed_maps: Mapping[int, Mapping[str, int]],
) -> tuple[list[dict[str, Any]], list[Path]]:
    cells: list[dict[str, Any]] = []
    paths: list[Path] = []
    selection_sha = fingerprint_json(dict(selection_contract))
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
                identity = phase7_cell_identity(
                    campaign_identity_sha256=campaign_identity_sha256,
                    stage=stage,
                    view=view,
                    layer=layer,
                    delta_sha256=delta_sha256,
                    beam_size=beam_size,
                    cell_id=cell_id,
                    candidate_seed=candidate_seed,
                    input_trajectory_checksum=source_checksum,
                    selection_contract_sha256=selection_sha,
                )
                path = out / "cells" / stage / view / layer / f"{cell_id}.json"
                cached = load_cached_cell(path, identity)
                if cached is None:
                    cached = _decode_cell(
                        row,
                        model=model,
                        config=config,
                        selection_contract=selection_contract,
                        bundle_index=bundle_index,
                        sigma=sigma,
                        rho=rho,
                        beam_size=beam_size,
                        candidate_seed=candidate_seed,
                        cache_identity=identity,
                    )
                    write_cached_cell(path, cached)
                cells.append(cached)
                paths.append(path)
    return cells, paths


def _verified_artifact(
    directory: Path,
    manifest: Mapping[str, Any],
    name: str,
) -> Path:
    expected = str((manifest.get("artifact_sha256") or {}).get(name, ""))
    path = directory / name
    if len(expected) != 64 or not path.is_file() or sha256_file(path) != expected:
        raise RuntimeError(f"authorized artifact hash mismatch: {directory.name}/{name}")
    return path


def _load_selection_contract_payload(
    phase6_dir: Path,
    phase6_manifest: Mapping[str, Any],
) -> tuple[Mapping[str, Any], Path]:
    """Load the signed Phase 6 view-scoped protocol without file discovery."""
    path = _verified_artifact(phase6_dir, phase6_manifest, "protocol_frozen.json")
    payload = read_json(path)
    if not isinstance(payload.get("candidate_selection_by_view"), Mapping):
        raise RuntimeError("Phase 6 has no view-scoped candidate selection freeze")
    if not isinstance(
        payload.get("candidate_selection_artifact_sha256_by_view"), Mapping
    ):
        raise RuntimeError("Phase 6 has no view-scoped selection artifact hashes")
    return payload, path


def _validate_inputs(root: Path) -> dict[str, Any]:
    manifests = {
        phase: read_json(root / f"phase{phase}" / "manifest.json", {})
        for phase in (2, 3, 4, 5, 6)
    }
    for phase, manifest in manifests.items():
        if manifest.get("status") != "complete" or not all(
            (manifest.get("go_conditions") or {}).values()
        ):
            raise RuntimeError(f"Phase {phase} is not complete with all Go conditions true")
    firewall_fields = {
        2: "test_accessed",
        3: "test_accessed",
        4: "grn_test_accessed",
        5: "test_accessed",
        6: "test_accessed",
    }
    for phase, field in firewall_fields.items():
        if manifests[phase].get(field) is not False:
            raise RuntimeError(f"Phase {phase} test-firewall provenance is invalid")

    phase2 = root / "phase2"
    phase4 = root / "phase4"
    phase5 = root / "phase5"
    phase6 = root / "phase6"
    paths = {
        "main_train": _verified_artifact(phase2, manifests[2], "train.json"),
        "main_validation": _verified_artifact(
            phase2, manifests[2], "validation.json"
        ),
        "holdout_train": _verified_artifact(
            phase2, manifests[2], "family_holdout_train.json"
        ),
        "holdout_validation": _verified_artifact(
            phase2, manifests[2], "family_holdout_validation.json"
        ),
        "reduced_main": _verified_artifact(
            phase4, manifests[4], "fixed_grn_validation_panel.json"
        ),
        "decoder_logit_lens": _verified_artifact(
            phase4, manifests[4], "decoder_logit_lens.json"
        ),
        "causal_main": _verified_artifact(
            phase5, manifests[5], "causal_ranking.json"
        ),
        "causal_holdout": _verified_artifact(
            phase5, manifests[5], "holdout_causal_ranking.json"
        ),
        "phase6_confirmation": _verified_artifact(
            phase6, manifests[6], "confirmation_summary.json"
        ),
        "phase6_cells": _verified_artifact(
            phase6, manifests[6], "cell_artifact_index.json"
        ),
        "phase6_view_protocols": _verified_artifact(
            phase6, manifests[6], "view_protocols_frozen.json"
        ),
    }
    selection_payload, selection_path = _load_selection_contract_payload(
        phase6, manifests[6]
    )
    prestage_manifest_path = root / "phase6_holdout_prestage" / "manifest.json"
    prestage_selection_path = root / "phase6_holdout_prestage" / "selection.json"
    authorized = manifests[6].get("authorized_inputs") or {}
    if (
        str(authorized.get("R06_prestage_manifest", ""))
        != sha256_file(prestage_manifest_path)
        or str(authorized.get("R06_selection", ""))
        != sha256_file(prestage_selection_path)
        or selection_payload["candidate_selection_artifact_sha256_by_view"]["main"]
        != str(authorized.get("phase3_lambda_selection", ""))
        or selection_payload["candidate_selection_artifact_sha256_by_view"][
            "family_holdout"
        ]
        != str(authorized.get("R06_selection", ""))
    ):
        raise RuntimeError("Phase 6 R06-only pre-stage artifact hash mismatch")
    prestage_manifest = read_json(prestage_manifest_path)
    prestage_selection = read_json(prestage_selection_path)
    view_protocols = read_json(paths["phase6_view_protocols"])
    view_identities = view_protocols.get("view_campaign_identities")
    view_identity_hashes = view_protocols.get("view_campaign_identity_sha256")
    if (
        not isinstance(view_identities, Mapping)
        or set(view_identities) != set(VIEWS)
        or not isinstance(view_identity_hashes, Mapping)
        or set(view_identity_hashes) != set(VIEWS)
        or any(
            fingerprint_json(view_identities[view]) != view_identity_hashes[view]
            or view_identities[view].get("view") != view
            or view_identities[view].get("selection_protocol")
            != selection_payload["candidate_selection_by_view"][view]
            or view_identities[view].get("selection_artifact_sha256")
            != selection_payload["candidate_selection_artifact_sha256_by_view"][
                view
            ]
            for view in VIEWS
        )
        or selection_payload["candidate_selection_artifact_sha256_by_view"]["main"]
        in json.dumps(
            view_identities["family_holdout"],
            sort_keys=True,
            separators=(",", ":"),
        )
    ):
        raise RuntimeError("Phase 6 view campaign identities are not independently frozen")
    holdout_system_ids = sorted(
        str(row["system_id"]) for row in read_json(paths["holdout_validation"])
    )
    prestage_system_ids = sorted(
        {str(row.get("system_id")) for row in prestage_selection.get("source_artifacts") or []}
    )
    if (
        prestage_manifest.get("status") != "complete"
        or not all((prestage_manifest.get("go_conditions") or {}).values())
        or prestage_manifest.get("test_accessed") is not False
        or prestage_selection.get("source_family") != "R06"
        or prestage_selection.get("forbidden_family_outcomes_accessed") is not False
        or any(
            row.get("family") != "R06"
            for row in (prestage_selection.get("source_artifacts") or [])
        )
        or prestage_system_ids != holdout_system_ids
        or prestage_manifest.get("selection_signature_sha256")
        != prestage_selection.get("signature_sha256")
        or (
            selection_payload["candidate_selection_by_view"]["family_holdout"].get(
                "selection_artifact_signature_sha256"
            )
            != prestage_selection.get("signature_sha256")
        )
        or selection_payload["candidate_selection_artifact_sha256_by_view"][
            "family_holdout"
        ]
        != sha256_file(prestage_selection_path)
    ):
        raise RuntimeError("Phase 6 R06-only pre-stage firewall signature is invalid")
    return {
        "manifests": manifests,
        "paths": paths,
        "selection_payload": selection_payload,
        "selection_path": selection_path,
        "prestage_manifest_path": prestage_manifest_path,
        "prestage_selection_path": prestage_selection_path,
    }


def _phase6_ted_by_seed(
    *,
    phase6_dir: Path,
    cell_index: Sequence[Mapping[str, Any]],
    view: str,
    condition: str,
    rows: Sequence[Mapping[str, Any]],
    config: Mapping[str, Any],
    bundle_indices: Sequence[int],
    expected_beam_size: int,
) -> dict[str, float]:
    """Read only hash-indexed Phase 6 validation shards needed for C_l."""
    if condition not in {"frozen", "grn_full"}:
        raise ValueError("C_l reference condition must be frozen or grn_full")
    prefix = f"cells/confirmation/{view}/{condition}/"
    indexed = {
        str(item["path"]): str(item["sha256"])
        for item in cell_index
        if str(item.get("path", "")).startswith(prefix)
    }
    output: dict[str, float] = {}
    for bundle_index in sorted(int(value) for value in bundle_indices):
        expected = sorted(
            validation_cell_id(
                system=str(row["system_id"]),
                bundle_index=bundle_index,
                noise_sigma=sigma,
                subsample_rho=rho,
            )
            for row in rows
            for sigma, rho in corruption_grid(config)
        )
        selected_rows: list[dict[str, Any]] = []
        for cell_id in expected:
            relative = f"{prefix}{cell_id}.json"
            if relative not in indexed:
                raise RuntimeError(f"Phase 6 C_l reference shard missing: {relative}")
            path = (phase6_dir / relative).resolve()
            if phase6_dir.resolve() not in path.parents:
                raise RuntimeError("Phase 6 cell index contains path traversal")
            if not path.is_file() or sha256_file(path) != indexed[relative]:
                raise RuntimeError(f"Phase 6 C_l reference hash mismatch: {relative}")
            cell = read_json(path)
            if (
                cell.get("status") != "complete"
                or cell.get("view") != view
                or cell.get("condition") != condition
                or int(cell.get("bundle_index", -1)) != bundle_index
                or int(cell.get("beam_size", -1)) != int(expected_beam_size)
                or str(cell.get("cell_id")) != cell_id
            ):
                raise RuntimeError(f"Phase 6 C_l reference identity mismatch: {relative}")
            selected_rows.append(
                {
                    "cell_id": cell_id,
                    "system_id": str(cell["system_id"]),
                    "bundle_index": bundle_index,
                    **dict(cell["selected"]),
                }
            )
        score = formula_score_vector(
            selected_rows,
            validation_ce=0.0,
            expected_cell_ids=expected,
        )
        output[str(bundle_index)] = -float(score[1])
    return output


def _confirmation_delta(
    *,
    model: torch.nn.Module,
    base_state: Mapping[str, torch.Tensor],
    base_sha: str,
    result: Mapping[str, Any],
    selected_step: int,
    identity: Mapping[str, Any],
    layer: str,
    path: Path,
) -> dict[str, Any]:
    """Persist and verify a selected single-block state from a fresh base."""
    restore_parameter_state(
        model,
        result["snapshots"][selected_step],
        allowed_parameter_keys=result["trainable_parameter_keys"],
    )
    delta = _save_current_delta(
        model,
        out_path=path,
        parameter_keys=result["trainable_parameter_keys"],
        identity=identity,
        layers={layer},
        base_sha=base_sha,
        persist=True,
    )
    adapted_sha = model_state_sha256(model)
    _restore_base(model, base_state)
    from gpu_run5.training import apply_delta_checkpoint, load_delta_checkpoint

    checkpoint = load_delta_checkpoint(
        Path(str(delta["path"])),
        expected_file_sha256=str(delta["file_sha256"]),
    )
    apply_delta_checkpoint(
        model,
        checkpoint,
        allowed_parameter_keys=result["trainable_parameter_keys"],
        expected_identity=identity,
    )
    reloaded_sha = model_state_sha256(model)
    delta["verification"] = {
        "strategy": "restore_fresh_base_then_verify_and_apply_parameter_delta",
        "fresh_base_matches_expected": checkpoint["base_model_state_sha256"] == base_sha,
        "file_sha256_verified": True,
        "metadata_identity_verified": True,
        "parameter_allowlist_verified": True,
        "tensor_delta_sha256_verified": True,
        "adapted_model_state_sha256_before_save": adapted_sha,
        "adapted_model_state_sha256_after_reload": reloaded_sha,
        "adapted_state_matches": adapted_sha == reloaded_sha,
    }
    if not all(
        value
        for key, value in delta["verification"].items()
        if key.endswith("_verified")
        or key.endswith("_matches_expected")
        or key == "adapted_state_matches"
    ):
        raise RuntimeError("Phase 7 persisted delta verification failed")
    return delta


def main() -> int:
    args = parse_args()
    started_utc, started_clock = utc_now(), perf_counter()
    config = load_config()
    root = run_dir(args.run_id)
    chosen_budget = budget(config, args.smoke)
    inputs = _validate_inputs(root)
    git = git_info()
    if git["status_short"]:
        raise RuntimeError(
            f"authoritative Phase 7 requires a clean worktree: {git['status_short']}"
        )

    out = phase_dir(args.run_id, 7)
    device = select_device(allow_cpu=args.allow_cpu)
    checkpoint_path = ROOT / str(config["odeformer_checkpoint"])
    raw_checkpoint_sha = sha256_file(checkpoint_path)
    if raw_checkpoint_sha != str(config["odeformer_checkpoint_sha256"]):
        raise RuntimeError("checkpoint SHA256 does not match frozen GPU_RUN5 config")
    environment = software_versions()
    model = load_odeformer_model(checkpoint_path, device=device)
    inventory = inventory_odeformer(model)
    layers = tuple(str(value) for value in inventory["ranking_layers"])
    if layers != OFFICIAL_LAYER_REGISTRY:
        raise RuntimeError("Phase 7 requires the released 4 encoder + 12 decoder blocks")
    base_sha = model_state_sha256(model)
    base_state = {
        key: value.detach().cpu().clone() for key, value in model.state_dict().items()
    }

    loaded = {key: read_json(path) for key, path in inputs["paths"].items()}
    list_inputs = (
        "main_train",
        "main_validation",
        "holdout_train",
        "holdout_validation",
        "reduced_main",
        "phase6_cells",
    )
    if any(not isinstance(loaded[key], list) for key in list_inputs):
        raise RuntimeError("an authorized Phase 7 input artifact is not a list")
    selection_contracts = freeze_view_selection_contracts(
        inputs["selection_payload"]
    )
    expected_holdout_train_families = sorted(
        str(value) for value in config["family_holdout"]["train_families"]
    )
    if sorted({str(row["family"]) for row in loaded["holdout_train"]}) != (
        expected_holdout_train_families
    ):
        raise RuntimeError("Phase 7 holdout training view is not exactly R01--R05")
    if sorted({str(row["family"]) for row in loaded["holdout_validation"]}) != [
        str(config["family_holdout"]["selection_family"])
    ]:
        raise RuntimeError("Phase 7 holdout selection view is not exactly R06")
    main_train_ids = {str(row["system_id"]) for row in loaded["main_train"]}
    main_validation_ids = {
        str(row["system_id"]) for row in loaded["main_validation"]
    }
    if {str(row["system_id"]) for row in loaded["holdout_train"]} != {
        str(row["system_id"])
        for row in loaded["main_train"]
        if str(row["family"]) in expected_holdout_train_families
    } or {str(row["system_id"]) for row in loaded["holdout_validation"]} != {
        str(row["system_id"])
        for row in loaded["main_validation"]
        if str(row["family"]) == str(config["family_holdout"]["selection_family"])
    }:
        raise RuntimeError("Phase 7 view subsets do not exactly match main artifacts")
    if len(main_train_ids) != len(loaded["main_train"]) or len(main_validation_ids) != len(
        loaded["main_validation"]
    ):
        raise RuntimeError("Phase 7 main train/validation contains duplicate system IDs")

    mode = "smoke" if args.smoke else "full"
    if str(inputs["manifests"][6].get("mode")) != mode:
        raise RuntimeError(
            f"Phase 7 {mode} cannot consume a Phase 6 "
            f"{inputs['manifests'][6].get('mode')} campaign"
        )
    n_bundles = int(chosen_budget["n_seeds"])
    bundle_indices = list(range(n_bundles))
    learning_rates = [
        float(value) for value in chosen_budget["hyperparameter_learning_rates"]
    ]
    steps = [int(value) for value in chosen_budget["hyperparameter_steps"]]
    grid = hyperparameter_grid(learning_rates, steps)
    if not args.smoke and len(grid) != 9:
        raise RuntimeError("authoritative Phase 7 requires the exact 3 x 3 grid")
    if not args.smoke and n_bundles != 3:
        raise RuntimeError("authoritative Phase 7 requires three paired bundles")
    max_steps = max(steps)

    main_validation_by_id = {
        str(row["system_id"]): row for row in loaded["main_validation"]
    }
    reduced_ids = [str(row["system_id"]) for row in loaded["reduced_main"]]
    if len(reduced_ids) != len(set(reduced_ids)) or not set(reduced_ids).issubset(
        main_validation_by_id
    ):
        raise RuntimeError("Phase 4 reduced panel is not a unique validation subset")
    main_panel = [main_validation_by_id[value] for value in sorted(reduced_ids)]
    holdout_panel = _panel_rows(
        loaded["holdout_validation"], len(loaded["holdout_validation"])
    )
    train_rows = {
        "main": loaded["main_train"],
        "family_holdout": loaded["holdout_train"],
    }
    panels = {"main": main_panel, "family_holdout": holdout_panel}
    if args.smoke:
        panels = {
            view: _variants_per_family(
                rows, int(chosen_budget["validation_variants_per_family"])
            )
            for view, rows in panels.items()
        }
        train_rows = {
            view: _variants_per_family(
                rows, int(chosen_budget["train_variants_per_family"])
            )
            for view, rows in train_rows.items()
        }
    elif len(main_panel) != 24 or len(holdout_panel) != 10:
        raise RuntimeError("authoritative Phase 7 panels must be main=24 and R06=10")

    panel_hashes = {
        view: fingerprint_json([str(row["system_id"]) for row in panels[view]])
        for view in VIEWS
    }
    selection_hashes = {
        view: fingerprint_json(selection_contracts[view]) for view in VIEWS
    }
    seed_maps = {
        view: {
            bundle: candidate_seed_map(
                panels[view], config=config, bundle_indices=[bundle]
            )
            for bundle in bundle_indices
        }
        for view in VIEWS
    }
    campaign_identity = {
        "schema_version": "gpu_run5_phase7_campaign_v1",
        "git_commit": git["commit"],
        "mode": mode,
        "config_fingerprint": fingerprint_json(config),
        "raw_checkpoint_sha256": raw_checkpoint_sha,
        "base_model_state_sha256": base_sha,
        "device": device,
        "environment_fingerprint": fingerprint_json(environment),
        "authorized_input_sha256": {
            **{key: sha256_file(path) for key, path in inputs["paths"].items()},
            "selection_contract": sha256_file(inputs["selection_path"]),
            "R06_prestage_manifest": sha256_file(
                inputs["prestage_manifest_path"]
            ),
            "R06_selection": sha256_file(inputs["prestage_selection_path"]),
            "phase6_manifest": sha256_file(root / "phase6" / "manifest.json"),
        },
        "views": {
            view: {
                "training_families": sorted(
                    {str(row["family"]) for row in train_rows[view]}
                ),
                "validation_families": sorted(
                    {str(row["family"]) for row in panels[view]}
                ),
                "validation_panel_sha256": panel_hashes[view],
                "candidate_selection": selection_contracts[view],
                "candidate_selection_sha256": selection_hashes[view],
            }
            for view in VIEWS
        },
        "learning_rates": learning_rates,
        "snapshot_steps": steps,
        "screening_bundle_indices": [0],
        "screening_beam_size": SCREENING_BEAM_SIZE,
        "confirmation_bundle_indices": bundle_indices,
        "confirmation_beam_size": (
            int(chosen_budget["beam_size"])
            if args.smoke
            else CONFIRMATION_BEAM_SIZE
        ),
        "rank_source": "screening_reduced_panel_bundle0_beam8",
        "confirmation_may_change_rank": False,
        "generalization_trajectory_accessed": False,
        "test_accessed": False,
    }
    campaign_sha = fingerprint_json(campaign_identity)
    write_json(out / "protocol_frozen.json", campaign_identity)
    write_json(out / "config_snapshot.json", config)
    write_json(out / "view_selection_contracts.json", selection_contracts)

    screening_paths: list[Path] = []
    screening_training_paths: list[Path] = []
    selections: dict[str, dict[str, Any]] = {view: {} for view in VIEWS}
    screening_deltas: dict[tuple[str, str], dict[str, Any]] = {}
    for view in VIEWS:
        rows = panels[view]
        corpus = train_rows[view]
        normalized = adapt_input_training_records(corpus)
        schedule = training_order(
            normalized,
            steps=max_steps,
            seed=int(config["seed_bundles"][0]["data_seed"]),
        )
        expected_cells = sorted(seed_maps[view][0])
        for layer in layers:
            trial_identity = phase7_trial_identity(
                view=view,
                layer=layer,
                bundle_indices=[0],
                base_model_state_sha256=base_sha,
                training_corpus_sha256=schedule["training_corpus_sha256"],
                training_order_sha256=schedule["order_sha256"],
                model_seed=int(config["seed_bundles"][0]["model_seed"]),
                validation_panel_sha256=panel_hashes[view],
                candidate_seed_map_sha256=candidate_seed_map_sha256(
                    seed_maps[view][0]
                ),
                selection_contract_sha256=selection_hashes[view],
            )
            candidates: list[dict[str, Any]] = []
            for lr in learning_rates:
                _restore_base(model, base_state)
                result = train_adam_with_snapshots(
                    model,
                    corpus,
                    trainable_layers={layer},
                    lr=lr,
                    max_steps=max_steps,
                    snapshot_steps=steps,
                    data_order_seed=int(config["seed_bundles"][0]["data_seed"]),
                    model_seed=int(config["seed_bundles"][0]["model_seed"]),
                )
                if (
                    result["training_corpus_sha256"]
                    != schedule["training_corpus_sha256"]
                    or result["order_sha256"] != schedule["order_sha256"]
                ):
                    raise RuntimeError("single-block training order is not paired")
                training_path = (
                    out
                    / "training"
                    / "screening"
                    / view
                    / layer
                    / f"lr{lr:g}.json"
                )
                training_record = {
                    "path": training_path.relative_to(out).as_posix(),
                    "view": view,
                    "layer": layer,
                    **{key: value for key, value in result.items() if key != "snapshots"},
                }
                write_json(training_path, training_record)
                screening_training_paths.append(training_path)
                for step in steps:
                    config_row = {"lr": float(lr), "steps": int(step)}
                    if step not in result["snapshots"]:
                        candidates.append(
                            {
                                "status": "failed",
                                "failure_reason": result["failure_reason"]
                                or "MissingExactSnapshot",
                                "config": config_row,
                                "trial_identity": trial_identity,
                                "validation_cell_ids": [],
                                "score_vector": [
                                    0.0,
                                    -1.0,
                                    0.0,
                                    -float("inf"),
                                ],
                                "training_record": training_record["path"],
                            }
                        )
                        continue
                    restore_parameter_state(
                        model,
                        result["snapshots"][step],
                        allowed_parameter_keys=result["trainable_parameter_keys"],
                    )
                    identity = phase7_delta_identity(
                        trial_identity,
                        stage="screening",
                        lr=lr,
                        steps=step,
                        raw_checkpoint_sha256=raw_checkpoint_sha,
                        config_fingerprint=fingerprint_json(config),
                    )
                    delta = _save_current_delta(
                        model,
                        out_path=out
                        / "checkpoints"
                        / "screening"
                        / view
                        / layer
                        / f"lr{lr:g}_s{step}.pt",
                        parameter_keys=result["trainable_parameter_keys"],
                        identity=identity,
                        layers={layer},
                        base_sha=base_sha,
                        persist=False,
                    )
                    stage = f"screening_lr{lr:g}_s{step}"
                    cells, paths = _decode_panel(
                        model=model,
                        rows=rows,
                        config=config,
                        selection_contract=selection_contracts[view],
                        out=out,
                        campaign_identity_sha256=campaign_sha,
                        stage=stage,
                        view=view,
                        layer=layer,
                        delta_sha256=str(delta["delta_sha256"]),
                        beam_size=SCREENING_BEAM_SIZE,
                        bundle_indices=[0],
                        seed_maps={0: seed_maps[view][0]},
                    )
                    screening_paths.extend(paths)
                    coverage = coverage_audit(
                        cells,
                        expected_cell_ids=expected_cells,
                        expected_beam_size=SCREENING_BEAM_SIZE,
                        expected_seed_map=seed_maps[view][0],
                    )
                    if not coverage["pass"]:
                        raise RuntimeError(
                            f"Phase 7 screening coverage failed: {view}/{layer}/{config_row}"
                        )
                    ce, ce_rows = _validation_cell_ce(
                        model, rows, config=config, bundle_indices=[0]
                    )
                    score = formula_score_vector(
                        _selected_rows(cells, ce_rows),
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
                            "coverage_audit": coverage,
                            "delta": delta,
                            "training_record": training_record["path"],
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
                quantization_digits=SCORE_QUANTIZATION_DIGITS,
                expected_validation_cell_ids=expected_cells,
            )
            selections[view][layer] = selected
            screening_deltas[(view, layer)] = dict(selected["selected"]["delta"])
            print(
                f"Phase7 screening {view}/{layer}: "
                f"lr={selected['selected']['config']['lr']:g} "
                f"steps={selected['selected']['config']['steps']}",
                flush=True,
            )

    write_json(out / "screening_selection.json", selections)
    hyperparameter_freeze = freeze_selected_hyperparameters(selections)
    write_json(out / "hyperparameter_freeze.json", hyperparameter_freeze)
    hyperparameter_freeze_sha = sha256_file(out / "hyperparameter_freeze.json")
    causal_rankings = {
        "main": list(loaded["causal_main"]["ranking"]),
        "family_holdout": list(loaded["causal_holdout"]["ranking"]),
    }
    layer_freeze = freeze_layer_sets(
        {
            view: {
                layer: selections[view][layer]["selected"]["score_vector"]
                for layer in layers
            }
            for view in VIEWS
        },
        causal_rankings=causal_rankings,
        random_seed=RANDOM_LAYER_SEED,
        random_set_count=5,
    )
    layer_freeze.pop("freeze_sha256", None)
    layer_freeze["hyperparameter_freeze_sha256"] = hyperparameter_freeze_sha
    layer_freeze["freeze_sha256"] = fingerprint_json(layer_freeze)
    write_json(out / "layer_freeze.json", layer_freeze)
    layer_freeze_sha = sha256_file(out / "layer_freeze.json")

    decoder_lens_rows = list(loaded["decoder_logit_lens"].get("formula_rows") or [])
    decoder_lens_scores: dict[str, list[float]] = {}
    for layer in (value for value in layers if value.startswith("decoder_")):
        rows = [row for row in decoder_lens_rows if str(row.get("layer")) == layer]
        if not rows:
            raise RuntimeError(f"Phase 4 decoder lens has no rows for {layer}")
        decoder_lens_scores[layer] = [
            float(np.mean([float(row.get("exponent_aware_skeleton_exact", 0.0)) for row in rows])),
            -float(np.mean([float(row.get("normalized_variable_aware_ted", 1.0)) for row in rows])),
            float(np.mean([float(bool(row.get("valid"))) for row in rows])),
        ]
    auxiliary_rankings = {
        "views": {
            view: {
                "teacher_forcing_ce": tie_aware_vector_ranking(
                    {
                        layer: [
                            -float(
                                selections[view][layer]["selected"][
                                    "validation_teacher_forcing_ce"
                                ]
                            )
                        ]
                        for layer in layers
                    },
                    quantization_digits=SCORE_QUANTIZATION_DIGITS,
                ),
                "encoder_only_iole_formula": tie_aware_vector_ranking(
                    {
                        layer: selections[view][layer]["selected"]["score_vector"]
                        for layer in layers
                        if layer.startswith("encoder_")
                    },
                    quantization_digits=SCORE_QUANTIZATION_DIGITS,
                ),
                "decoder_only_iole_formula": tie_aware_vector_ranking(
                    {
                        layer: selections[view][layer]["selected"]["score_vector"]
                        for layer in layers
                        if layer.startswith("decoder_")
                    },
                    quantization_digits=SCORE_QUANTIZATION_DIGITS,
                ),
                "causal_intervention": causal_rankings[view],
            }
            for view in VIEWS
        },
        "decoder_lens_control": tie_aware_vector_ranking(
            decoder_lens_scores,
            quantization_digits=SCORE_QUANTIZATION_DIGITS,
        ),
        "decoder_lens_source": {
            "path": "phase4/decoder_logit_lens.json",
            "sha256": sha256_file(inputs["paths"]["decoder_logit_lens"]),
            "corpus": "fixed_official_validation_panel",
            "role": "control_not_IOLE_selection",
        },
        "ambiguous_combined_rank_not_computed": True,
        "test_accessed": False,
    }
    write_json(out / "auxiliary_rankings.json", auxiliary_rankings)

    confirmation_beam = (
        int(chosen_budget["beam_size"])
        if args.smoke
        else CONFIRMATION_BEAM_SIZE
    )
    confirmation_paths: list[Path] = []
    confirmation_training_paths: list[Path] = []
    checkpoint_records: list[dict[str, Any]] = []
    confirmation_records: dict[str, Any] = {view: {} for view in VIEWS}
    score_by_view_seed: dict[str, dict[str, dict[str, list[float]]]] = {
        view: {str(bundle): {} for bundle in bundle_indices} for view in VIEWS
    }
    all_confirmation_coverages: list[dict[str, Any]] = []
    for view in VIEWS:
        rows = panels[view]
        corpus = train_rows[view]
        for layer in layers:
            selected = hyperparameter_freeze["views"][view][layer]
            lr = float(selected["config"]["lr"])
            selected_step = int(selected["config"]["steps"])
            layer_records: dict[str, Any] = {}
            for bundle_index in bundle_indices:
                _restore_base(model, base_state)
                bundle = config["seed_bundles"][bundle_index]
                result = train_adam_with_snapshots(
                    model,
                    corpus,
                    trainable_layers={layer},
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
                    / layer
                    / f"bundle{bundle_index}.json"
                )
                if (
                    result["status"] != "complete"
                    or selected_step not in result["snapshots"]
                ):
                    failure_record = {
                        "path": training_path.relative_to(out).as_posix(),
                        "view": view,
                        "layer": layer,
                        "bundle_index": bundle_index,
                        "selected_config": selected["config"],
                        **{
                            key: value
                            for key, value in result.items()
                            if key != "snapshots"
                        },
                    }
                    write_json(training_path, failure_record)
                    raise RuntimeError(
                        f"Phase 7 confirmation training failed: {view}/{layer}/"
                        f"bundle{bundle_index}:{result['failure_reason']}"
                    )
                trial_identity = phase7_trial_identity(
                    view=view,
                    layer=layer,
                    bundle_indices=[bundle_index],
                    base_model_state_sha256=base_sha,
                    training_corpus_sha256=result["training_corpus_sha256"],
                    training_order_sha256=result["order_sha256"],
                    model_seed=int(bundle["model_seed"]),
                    validation_panel_sha256=panel_hashes[view],
                    candidate_seed_map_sha256=candidate_seed_map_sha256(
                        seed_maps[view][bundle_index]
                    ),
                    selection_contract_sha256=selection_hashes[view],
                )
                identity = phase7_delta_identity(
                    trial_identity,
                    stage="confirmation",
                    lr=lr,
                    steps=selected_step,
                    raw_checkpoint_sha256=raw_checkpoint_sha,
                    config_fingerprint=fingerprint_json(config),
                )
                delta = _confirmation_delta(
                    model=model,
                    base_state=base_state,
                    base_sha=base_sha,
                    result=result,
                    selected_step=selected_step,
                    identity=identity,
                    layer=layer,
                    path=out
                    / "checkpoints"
                    / "confirmation"
                    / view
                    / layer
                    / f"bundle{bundle_index}.pt",
                )
                if bundle_index == 0:
                    delta["matches_selected_screening_delta"] = (
                        delta["delta_sha256"]
                        == screening_deltas[(view, layer)]["delta_sha256"]
                    )
                    if not delta["matches_selected_screening_delta"]:
                        raise RuntimeError(
                            f"Phase 7 confirmation did not reproduce screening: {view}/{layer}"
                        )
                checkpoint_records.append(
                    {
                        "view": view,
                        "layer": layer,
                        "bundle_index": bundle_index,
                        **delta,
                    }
                )
                training_record = {
                    "path": training_path.relative_to(out).as_posix(),
                    "view": view,
                    "layer": layer,
                    "bundle_index": bundle_index,
                    "selected_config": selected["config"],
                    "checkpoint_file_sha256": delta["file_sha256"],
                    "delta_sha256": delta["delta_sha256"],
                    **{
                        key: value
                        for key, value in result.items()
                        if key != "snapshots"
                    },
                }
                write_json(training_path, training_record)
                confirmation_training_paths.append(training_path)
                cells, paths = _decode_panel(
                    model=model,
                    rows=rows,
                    config=config,
                    selection_contract=selection_contracts[view],
                    out=out,
                    campaign_identity_sha256=campaign_sha,
                    stage="confirmation",
                    view=view,
                    layer=layer,
                    delta_sha256=str(delta["delta_sha256"]),
                    beam_size=confirmation_beam,
                    bundle_indices=[bundle_index],
                    seed_maps={bundle_index: seed_maps[view][bundle_index]},
                )
                confirmation_paths.extend(paths)
                expected = sorted(seed_maps[view][bundle_index])
                coverage = coverage_audit(
                    cells,
                    expected_cell_ids=expected,
                    expected_beam_size=confirmation_beam,
                    expected_seed_map=seed_maps[view][bundle_index],
                )
                if not coverage["pass"]:
                    raise RuntimeError(
                        f"Phase 7 confirmation coverage failed: {view}/{layer}/"
                        f"bundle{bundle_index}"
                    )
                all_confirmation_coverages.append(coverage)
                ce, ce_rows = _validation_cell_ce(
                    model, rows, config=config, bundle_indices=[bundle_index]
                )
                score = formula_score_vector(
                    _selected_rows(cells, ce_rows), expected_cell_ids=expected
                )
                score_by_view_seed[view][str(bundle_index)][layer] = list(score)
                layer_records[str(bundle_index)] = {
                    "score_vector": list(score),
                    "validation_teacher_forcing_ce": ce,
                    "coverage_audit": coverage,
                    "cells": len(cells),
                    "checkpoint_file_sha256": delta["file_sha256"],
                    "delta_sha256": delta["delta_sha256"],
                    "training_record": training_record["path"],
                }
                del result
                gc.collect()
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
            confirmation_records[view][layer] = layer_records

    write_json(out / "confirmation_summary.json", confirmation_records)
    write_json(out / "checkpoint_index.json", checkpoint_records)
    write_json(
        out / "screening_training_artifact_index.json",
        artifact_index(screening_training_paths, relative_to=out),
    )
    write_json(
        out / "confirmation_training_artifact_index.json",
        artifact_index(confirmation_training_paths, relative_to=out),
    )
    cell_paths = screening_paths + confirmation_paths
    cell_artifacts = artifact_index(cell_paths, relative_to=out)
    write_json(out / "cell_artifact_index.json", cell_artifacts)

    rank_stability = confirmation_rank_stability(score_by_view_seed)
    rank_stability["rank_frozen_before_confirmation"] = True
    rank_stability["layer_freeze_sha256"] = layer_freeze_sha
    write_json(out / "rank_stability.json", rank_stability)

    phase6_dir = root / "phase6"
    contribution: dict[str, Any] = {}
    phase6_reference_beam = (
        int(chosen_budget["beam_size"])
        if args.smoke
        else CONFIRMATION_BEAM_SIZE
    )
    for view in VIEWS:
        frozen_ted = _phase6_ted_by_seed(
            phase6_dir=phase6_dir,
            cell_index=loaded["phase6_cells"],
            view=view,
            condition="frozen",
            rows=panels[view],
            config=config,
            bundle_indices=bundle_indices,
            expected_beam_size=phase6_reference_beam,
        )
        full_ted = _phase6_ted_by_seed(
            phase6_dir=phase6_dir,
            cell_index=loaded["phase6_cells"],
            view=view,
            condition="grn_full",
            rows=panels[view],
            config=config,
            bundle_indices=bundle_indices,
            expected_beam_size=phase6_reference_beam,
        )
        layer_ted = {
            str(bundle): {
                layer: -float(score_by_view_seed[view][str(bundle)][layer][1])
                for layer in layers
            }
            for bundle in bundle_indices
        }
        contribution[view] = contribution_records(
            frozen_ted_by_seed=frozen_ted,
            full_ted_by_seed=full_ted,
            layer_ted_by_seed=layer_ted,
        )
    write_json(out / "iole_contribution.json", contribution)

    phase8_handoff = {
        "schema_version": "gpu_run5_phase7_to_phase8_handoff_v1",
        "layer_freeze": {
            "path": "layer_freeze.json",
            "sha256": layer_freeze_sha,
            "source": "reduced_panel_bundle0_beam8_formula_score",
            "confirmation_reselected_rank": False,
        },
        "hyperparameter_freeze": {
            "path": "hyperparameter_freeze.json",
            "sha256": hyperparameter_freeze_sha,
            "scope": "single_block_diagnostic_only_not_selective_ft",
        },
        "views": {
            view: {
                "candidate_selection_sha256": selection_hashes[view],
                "candidate_selection_source_artifact_sha256": selection_contracts[
                    view
                ]["source_artifact_sha256"],
                "layer_sets": {
                    key: layer_freeze["views"][view][key]
                    for key in (
                        "top1",
                        "top3",
                        "causal_top3",
                        "bottom3",
                        "random3",
                    )
                },
            }
            for view in VIEWS
        },
        "phase8_selective_hyperparameters": "must_run_equal_own_grid",
        "final_test_random_representative": "random3_0",
        "test_accessed": False,
    }
    write_json(out / "phase8_handoff.json", phase8_handoff)

    expected_counts = expected_phase7_counts(
        systems_by_view={view: len(panels[view]) for view in VIEWS},
        n_grid_candidates=len(grid),
        n_bundles=n_bundles,
        n_corruptions=len(corruption_grid(config)),
        n_layers=len(layers),
    )
    observed_grid = sum(
        selections[view][layer]["candidate_count"]
        for view in VIEWS
        for layer in layers
    )
    selected_trial_count = len(checkpoint_records)
    all_screen_coverages_pass = all(
        trial["coverage_audit"]["pass"]
        for view in VIEWS
        for layer in layers
        for trial in selections[view][layer]["trials"]
        if trial["status"] == "complete"
    )
    all_delta_verifications_pass = all(
        row["verification"]["fresh_base_matches_expected"]
        and row["verification"]["file_sha256_verified"]
        and row["verification"]["metadata_identity_verified"]
        and row["verification"]["parameter_allowlist_verified"]
        and row["verification"]["tensor_delta_sha256_verified"]
        and row["verification"]["adapted_state_matches"]
        and bool(row.get("matches_selected_screening_delta", True))
        for row in checkpoint_records
    )
    layer_freeze_unchanged = layer_freeze_sha == sha256_file(
        out / "layer_freeze.json"
    )
    go = {
        "phase2_through_phase6_complete_hashed_and_pretest": True,
        "test_and_generalization_trajectories_not_accessed": True,
        "view_specific_selection_contracts_and_r06_holdout_firewall": (
            selection_contracts["family_holdout"]["allowed_families"] == ["R06"]
            and selection_contracts["main"]["source_artifact_sha256"]
            != selection_contracts["family_holdout"]["source_artifact_sha256"]
        ),
        "phase6_view_campaign_identities_independently_verified": True,
        "all_16_layers_received_exact_equal_grid_in_both_views": observed_grid
        == expected_counts["screening_training_trials"],
        "screening_beam8_bundle0_reduced_panel_coverage_exact": (
            all_screen_coverages_pass
            and len(screening_paths) == expected_counts["screening_cells_total"]
        ),
        "formula_rank_and_layer_sets_frozen_before_confirmation": (
            layer_freeze_unchanged
            and layer_freeze["source"]
            == "reduced_panel_bundle0_beam8_formula_score"
        ),
        "five_distinct_random3_sets_seed5101_frozen_without_reroll": all(
            len(
                {
                    tuple(values)
                    for values in layer_freeze["views"][view]["random3"].values()
                }
            )
            == 5
            for view in VIEWS
        ),
        "beam50_three_bundle_confirmation_exact": (
            (args.smoke or confirmation_beam == CONFIRMATION_BEAM_SIZE)
            and selected_trial_count
            == expected_counts["selected_confirmation_training_trials"]
            and len(confirmation_paths)
            == expected_counts["confirmation_cells_total"]
            and all(item["pass"] for item in all_confirmation_coverages)
        ),
        "confirmation_did_not_reselect_rank_or_layer_sets": (
            rank_stability["rank_frozen_before_confirmation"]
            and rank_stability["layer_freeze_sha256"] == layer_freeze_sha
        ),
        "persisted_single_layer_deltas_verified_from_fresh_base": (
            len(checkpoint_records)
            == expected_counts["selected_confirmation_training_trials"]
            and all_delta_verifications_pass
        ),
        "c_l_only_computed_when_full_improves_frozen": all(
            all(
                row["full_improves_frozen"]
                or row["normalized_contribution"] is None
                for row in contribution[view]["rows"]
            )
            for view in VIEWS
        ),
        "all_formula_candidates_failures_training_and_hashes_saved": (
            len(cell_artifacts) == expected_counts["all_decode_cells_total"]
            and len(screening_training_paths)
            == len(VIEWS) * len(layers) * len(learning_rates)
            and len(confirmation_training_paths)
            == expected_counts["selected_confirmation_training_trials"]
        ),
        "git_commit_and_cleanliness_stable": git_info()["commit"] == git["commit"]
        and not git_info()["status_short"],
    }
    status = "complete" if all(go.values()) else "incomplete"
    summary = {
        "status": status,
        "mode": mode,
        "campaign_identity_sha256": campaign_sha,
        "hyperparameter_freeze_sha256": hyperparameter_freeze_sha,
        "layer_freeze_sha256": layer_freeze_sha,
        "expected_counts": expected_counts,
        "observed": {
            "grid_candidates": observed_grid,
            "screening_cells": len(screening_paths),
            "confirmation_cells": len(confirmation_paths),
            "selected_confirmation_training_trials": selected_trial_count,
            "checkpoint_count": len(checkpoint_records),
        },
        "frozen_layer_sets": {
            view: {
                key: layer_freeze["views"][view][key]
                for key in ("top1", "top3", "causal_top3", "bottom3", "random3")
            }
            for view in VIEWS
        },
        "rank_stability": {
            view: {
                "mean_spearman": rank_stability[view]["mean_spearman"],
                "mean_kendall_tau_b": rank_stability[view]["mean_kendall_tau_b"],
            }
            for view in VIEWS
        },
        "contribution_eligible_seeds": {
            view: contribution[view]["eligible_seeds"] for view in VIEWS
        },
        "go_conditions": go,
        "test_accessed": False,
    }
    write_json(out / "summary.json", summary)
    write_json(out / "go.json", go)
    artifact_names = [
        "protocol_frozen.json",
        "config_snapshot.json",
        "view_selection_contracts.json",
        "screening_selection.json",
        "hyperparameter_freeze.json",
        "layer_freeze.json",
        "auxiliary_rankings.json",
        "confirmation_summary.json",
        "checkpoint_index.json",
        "screening_training_artifact_index.json",
        "confirmation_training_artifact_index.json",
        "cell_artifact_index.json",
        "rank_stability.json",
        "iole_contribution.json",
        "phase8_handoff.json",
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
            "hyperparameter_freeze_sha256": hyperparameter_freeze_sha,
            "layer_freeze_sha256": layer_freeze_sha,
            "authorized_inputs": campaign_identity["authorized_input_sha256"],
            "phase_manifests": {
                str(phase): sha256_file(root / f"phase{phase}" / "manifest.json")
                for phase in (2, 3, 4, 5, 6)
            },
            "test_accessed": False,
            "generalization_trajectory_accessed": False,
            "artifact_sha256": {
                name: sha256_file(out / name) for name in artifact_names
            },
        }
    )
    write_manifest(out, 7, status, **manifest_payload)
    print(
        f"GPU_RUN5 Phase 7 {status}: grid={observed_grid} "
        f"screen={len(screening_paths)} confirm={len(confirmation_paths)}",
        flush=True,
    )
    return 0 if status == "complete" else 1


if __name__ == "__main__":
    raise SystemExit(main())
