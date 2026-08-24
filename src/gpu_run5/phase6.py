"""Pure execution-contract helpers for GPU_RUN5 Phase 6.

The functions in this module deliberately receive already-authorized records.
They never discover files or inspect a test split.  The Phase 6 launcher is
responsible for passing only train and validation artifacts.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any, Mapping, Sequence

from gpu_run2_runtime import fingerprint_json, sha256_file, write_json
from gpu_run5.evaluation import formula_selection_key, select_candidate
from gpu_run5.seeding import stable_problem_seed


PHASE6_SCHEMA_VERSION = "gpu_run5_phase6_v1"
TRAINABLE_CONDITIONS = (
    "official_continued_full",
    "grn_full",
    "grn_decoder_all",
)
VIEWS = ("main", "family_holdout")
PHASE3_SELECTION_RULE = "multi_ic_complexity"
PHASE3_COMPLEXITY_LAMBDA = 0.01
HOLDOUT_SELECTION_SCHEMA_VERSION = "gpu_run5_R06_only_selection_v1"


def system_id(row: Mapping[str, Any]) -> str:
    """Return the stable system identifier required by a GRN record."""
    value = row.get("system_id")
    if value is None or not str(value):
        raise ValueError("GRN record has no system_id")
    return str(value)


def audit_data_views(
    *,
    main_train: Sequence[Mapping[str, Any]],
    main_validation: Sequence[Mapping[str, Any]],
    holdout_train: Sequence[Mapping[str, Any]],
    holdout_validation: Sequence[Mapping[str, Any]],
    holdout_train_families: Sequence[str],
    holdout_selection_family: str,
) -> dict[str, Any]:
    """Validate the two pre-test data views without knowing test family names."""
    collections = {
        "main_train": list(main_train),
        "main_validation": list(main_validation),
        "holdout_train": list(holdout_train),
        "holdout_validation": list(holdout_validation),
    }
    ids: dict[str, list[str]] = {}
    duplicate_ids: dict[str, list[str]] = {}
    for name, rows in collections.items():
        values = [system_id(row) for row in rows]
        ids[name] = values
        duplicate_ids[name] = sorted(
            value for value in set(values) if values.count(value) > 1
        )
    expected_train = sorted(str(value) for value in holdout_train_families)
    observed_train = sorted({str(row.get("family")) for row in holdout_train})
    observed_validation = sorted({str(row.get("family")) for row in holdout_validation})
    overlaps = {
        "main_train_validation": sorted(set(ids["main_train"]) & set(ids["main_validation"])),
        "holdout_train_validation": sorted(
            set(ids["holdout_train"]) & set(ids["holdout_validation"])
        ),
    }
    pass_flags = {
        "all_views_nonempty": all(collections.values()),
        "ids_unique_within_view": not any(duplicate_ids.values()),
        "main_train_validation_disjoint": not overlaps["main_train_validation"],
        "holdout_train_validation_disjoint": not overlaps["holdout_train_validation"],
        "holdout_train_families_exact": observed_train == expected_train,
        "holdout_selection_family_exact": observed_validation
        == [str(holdout_selection_family)],
        "holdout_is_exact_subset_of_main_train": set(ids["holdout_train"])
        == {
            system_id(row)
            for row in main_train
            if str(row.get("family")) in set(expected_train)
        },
        "holdout_selection_is_exact_subset_of_main_validation": set(
            ids["holdout_validation"]
        )
        == {
            system_id(row)
            for row in main_validation
            if str(row.get("family")) == str(holdout_selection_family)
        },
    }
    return {
        "pass": all(pass_flags.values()),
        "pass_flags": pass_flags,
        "counts": {name: len(rows) for name, rows in collections.items()},
        "families": {
            name: sorted({str(row.get("family")) for row in rows})
            for name, rows in collections.items()
        },
        "duplicate_ids": duplicate_ids,
        "overlaps": overlaps,
        "record_set_sha256": {
            name: fingerprint_json(sorted(values)) for name, values in ids.items()
        },
    }


def hyperparameter_grid(
    learning_rates: Sequence[float], steps: Sequence[int]
) -> list[dict[str, Any]]:
    """Return a deterministic, duplicate-free LR by snapshot-step grid."""
    rates = [float(value) for value in learning_rates]
    checkpoints = [int(value) for value in steps]
    if not rates or not checkpoints or any(value <= 0 for value in rates + checkpoints):
        raise ValueError("learning rates and steps must be positive and non-empty")
    if len(rates) != len(set(rates)) or len(checkpoints) != len(set(checkpoints)):
        raise ValueError("hyperparameter grid axes must not contain duplicates")
    return [
        {"lr": rate, "steps": step}
        for rate in sorted(rates)
        for step in sorted(checkpoints)
    ]


def corruption_grid(config: Mapping[str, Any]) -> list[tuple[float, float]]:
    corruptions = config["corruptions"]
    return [
        (float(sigma), float(rho))
        for sigma in corruptions["noise_sigmas"]
        for rho in corruptions["subsample_rhos"]
    ]


def freeze_phase3_selection(
    payload: Mapping[str, Any],
    *,
    expected_lambda: float = PHASE3_COMPLEXITY_LAMBDA,
) -> dict[str, Any]:
    """Validate the Phase 3 validation-only multi-IC selection freeze."""
    try:
        chosen = float(payload["chosen_lambda"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("Phase 3 lambda selection has no numeric chosen_lambda") from exc
    if not math.isfinite(chosen) or chosen != float(expected_lambda):
        raise ValueError(
            f"Phase 3 chosen lambda changed: observed={chosen}, expected={expected_lambda}"
        )
    if payload.get("split") != "validation":
        raise ValueError("Phase 3 complexity lambda was not selected on validation")
    audit = payload.get("audit")
    if not isinstance(audit, list) or not audit:
        raise ValueError("Phase 3 lambda selection audit is missing")
    candidates = []
    for row in audit:
        if not isinstance(row, Mapping) or "lambda" not in row:
            raise ValueError("Phase 3 lambda audit contains an invalid row")
        candidates.append(float(row["lambda"]))
    if not all(map(math.isfinite, candidates)):
        raise ValueError("Phase 3 lambda audit contains a non-finite candidate")
    if chosen not in candidates or len(candidates) != len(set(candidates)):
        raise ValueError("Phase 3 chosen lambda is absent or the audit grid has duplicates")
    return {
        "selection_rule": PHASE3_SELECTION_RULE,
        "complexity_lambda": chosen,
        "source_split": "validation",
        "candidate_lambdas": candidates,
    }


def phase3_cell_filename(
    *, system: str, bundle_index: int, noise_sigma: float, subsample_rho: float
) -> str:
    """Return the exact Phase 3 shard filename without directory discovery."""
    value = (
        f"{system}_b{int(bundle_index)}_n{float(noise_sigma):g}"
        f"_r{float(subsample_rho):g}"
    )
    return value.replace(".", "p") + ".json"


def _empty_formula_placeholder(cell: Mapping[str, Any]) -> dict[str, Any]:
    dimension = max(int(cell.get("dimension") or 0), 1)
    return {
        "cell_id": str(cell["cell_id"]),
        "system_id": str(cell["system_id"]),
        "bundle_index": int(cell["bundle_index"]),
        "component_exponent_aware_skeleton_exact": [0.0] * dimension,
        "component_normalized_variable_aware_ted": [1.0] * dimension,
        "component_valid": [False] * dimension,
        "empty_candidate_placeholder": True,
    }


def build_holdout_selection_artifact(
    *,
    cell_sources: Sequence[tuple[str, Path]],
    expected_cell_ids: Sequence[str],
    expected_system_ids: Sequence[str],
    candidate_lambdas: Sequence[float],
    failure_penalty: float,
    source_phase2_manifest_sha256: str,
    source_phase3_config_snapshot_sha256: str,
    source_holdout_validation_sha256: str,
    config_fingerprint: str,
    git_provenance: Mapping[str, Any],
    expected_beam_size: int,
    expected_checkpoint_sha256: str,
) -> dict[str, Any]:
    """Select the complexity lambda from explicitly allowlisted R06 shards only."""
    expected_cells = sorted(str(value) for value in expected_cell_ids)
    expected_systems = sorted(str(value) for value in expected_system_ids)
    if not expected_cells or len(expected_cells) != len(set(expected_cells)):
        raise ValueError("R06 expected cell IDs must be non-empty and unique")
    if not expected_systems or len(expected_systems) != len(set(expected_systems)):
        raise ValueError("R06 expected system IDs must be non-empty and unique")
    if not str(git_provenance.get("commit") or ""):
        raise ValueError("R06 selection signing requires a Git commit")
    if git_provenance.get("status_short"):
        raise ValueError("R06 selection signing requires a clean worktree")
    lambdas = [float(value) for value in candidate_lambdas]
    if (
        not lambdas
        or len(lambdas) != len(set(lambdas))
        or any(not math.isfinite(value) or value < 0 for value in lambdas)
    ):
        raise ValueError("R06 candidate lambdas must be finite, non-negative, and unique")
    penalty = float(failure_penalty)
    if not math.isfinite(penalty) or penalty <= 0:
        raise ValueError("R06 failure penalty must be finite and positive")

    observed: list[dict[str, Any]] = []
    source_artifacts: list[dict[str, Any]] = []
    cache_projections: list[dict[str, Any]] = []
    for label, path in sorted(cell_sources, key=lambda item: item[0]):
        source = Path(path)
        try:
            cell = json.loads(source.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(f"cannot read authorized R06 shard: {label}") from exc
        if not isinstance(cell, dict) or cell.get("status") != "complete":
            raise ValueError(f"R06 shard is not complete: {label}")
        if str(cell.get("family")) != "R06":
            raise ValueError(f"non-R06 shard rejected: {label}")
        if str(cell.get("system_id")) not in expected_systems:
            raise ValueError(f"unexpected R06 system rejected: {label}")
        if str(cell.get("cell_id")) not in expected_cells:
            raise ValueError(f"unexpected R06 cell rejected: {label}")
        if not isinstance(cell.get("candidates"), list):
            raise ValueError(f"R06 shard has no candidate list: {label}")
        candidates = list(cell["candidates"])
        raw_formulas = [str(row.get("candidate_formula_raw") or "") for row in candidates]
        recomputed_candidate_hash = hashlib.sha256(
            json.dumps(raw_formulas, ensure_ascii=True, separators=(",", ":")).encode(
                "utf-8"
            )
        ).hexdigest()
        if cell.get("candidate_set_hash") != recomputed_candidate_hash:
            raise ValueError(f"R06 shard candidate-set hash mismatch: {label}")
        if int(cell.get("n_candidates", -1)) != len(candidates):
            raise ValueError(f"R06 shard candidate count mismatch: {label}")
        candidate_indices = [int(row.get("candidate_index", -1)) for row in candidates]
        if candidate_indices != list(range(len(candidates))):
            raise ValueError(f"R06 shard candidate indices are not contiguous: {label}")
        cache = cell.get("cache_identity")
        if not isinstance(cache, Mapping):
            raise ValueError(f"R06 shard cache identity is missing: {label}")
        projection = {
            key: cache.get(key)
            for key in (
                "schema_version",
                "git_commit",
                "git_status_short",
                "config_fingerprint",
                "checkpoint_sha256",
                "beam_size",
                "beam_temperature",
                "beam_type",
                "rescale",
                "failure_penalty",
                "candidate_seed_namespace",
                "device",
                "environment_fingerprint",
            )
        }
        if projection["config_fingerprint"] != str(config_fingerprint):
            raise ValueError(f"R06 shard config fingerprint mismatch: {label}")
        if projection["checkpoint_sha256"] != str(expected_checkpoint_sha256):
            raise ValueError(f"R06 shard checkpoint mismatch: {label}")
        if int(projection["beam_size"] or -1) != int(expected_beam_size):
            raise ValueError(f"R06 shard beam mismatch: {label}")
        if projection["git_status_short"]:
            raise ValueError(f"R06 shard was generated from a dirty worktree: {label}")
        cache_projections.append(projection)
        observed.append(cell)
        source_artifacts.append(
            {
                "path": str(label),
                "sha256": sha256_file(source),
                "bytes": source.stat().st_size,
                "cell_id": str(cell["cell_id"]),
                "system_id": str(cell["system_id"]),
                "family": "R06",
                "candidate_set_sha256": recomputed_candidate_hash,
            }
        )
    observed_ids = sorted(str(cell["cell_id"]) for cell in observed)
    if observed_ids != expected_cells or len(observed_ids) != len(set(observed_ids)):
        raise ValueError("R06 source shard coverage is not exact")
    if sorted({str(cell["system_id"]) for cell in observed}) != expected_systems:
        raise ValueError("R06 source system coverage is not exact")
    if not cache_projections or any(
        projection != cache_projections[0] for projection in cache_projections[1:]
    ):
        raise ValueError("R06 source shard cache identities are not paired")

    audit = []
    for complexity_lambda in lambdas:
        selected_rows: list[dict[str, Any]] = []
        empty_count = 0
        for cell in observed:
            candidate_index = select_candidate(
                list(cell["candidates"]),
                PHASE3_SELECTION_RULE,
                penalty=penalty,
                complexity_lambda=complexity_lambda,
            )
            if candidate_index is None:
                selected_rows.append(_empty_formula_placeholder(cell))
                empty_count += 1
                continue
            by_index = {
                int(candidate["candidate_index"]): candidate
                for candidate in cell["candidates"]
            }
            if int(candidate_index) not in by_index:
                raise ValueError("R06 selected candidate index is absent from its shard")
            selected_rows.append(
                {
                    "cell_id": str(cell["cell_id"]),
                    "system_id": str(cell["system_id"]),
                    "bundle_index": int(cell["bundle_index"]),
                    **dict(by_index[int(candidate_index)]),
                }
            )
        score = formula_selection_key(selected_rows)
        audit.append(
            {
                "lambda": complexity_lambda,
                "selection_key": list(score),
                "n_cells": len(selected_rows),
                "n_empty_candidate_placeholders": empty_count,
            }
        )
    chosen = max(
        audit,
        key=lambda row: (*[float(value) for value in row["selection_key"]], -float(row["lambda"])),
    )
    body = {
        "schema_version": HOLDOUT_SELECTION_SCHEMA_VERSION,
        "selection_rule": PHASE3_SELECTION_RULE,
        "source_split": "family_holdout_validation_R06_only",
        "source_family": "R06",
        "source_system_ids": expected_systems,
        "source_cell_ids": expected_cells,
        "source_cell_count": len(expected_cells),
        "source_artifacts": source_artifacts,
        "candidate_lambdas": lambdas,
        "audit": audit,
        "chosen_lambda": float(chosen["lambda"]),
        "failure_penalty": penalty,
        "source_phase2_manifest_sha256": str(source_phase2_manifest_sha256),
        "source_phase3_config_snapshot_sha256": str(
            source_phase3_config_snapshot_sha256
        ),
        "source_holdout_validation_sha256": str(source_holdout_validation_sha256),
        "source_system_ids_sha256": fingerprint_json(expected_systems),
        "source_cell_ids_sha256": fingerprint_json(expected_cells),
        "source_artifact_index_sha256": fingerprint_json(source_artifacts),
        "source_path_sha256_index_sha256": fingerprint_json(
            [
                {"path": row["path"], "sha256": row["sha256"]}
                for row in source_artifacts
            ]
        ),
        "source_filename_sha256_index_sha256": fingerprint_json(
            [
                {
                    "path": Path(str(row["path"])).name,
                    "sha256": row["sha256"],
                }
                for row in source_artifacts
            ]
        ),
        "source_phase3_cache_identity_projection": cache_projections[0],
        "config_fingerprint": str(config_fingerprint),
        "git": dict(git_provenance),
        "forbidden_family_outcomes_accessed": False,
        "directory_discovery_used": False,
        "retrospective_signing_limitation": (
            "legacy Phase3 shards were not individually pinned by a safe pre-outcome "
            "manifest; this artifact revalidates internal candidate hashes and signs "
            "their current exact file hashes retrospectively"
        ),
    }
    return {**body, "signature_sha256": fingerprint_json(body)}


def verify_holdout_selection_artifact(
    artifact: Mapping[str, Any],
    *,
    expected_cell_ids: Sequence[str],
    expected_system_ids: Sequence[str],
    expected_phase2_manifest_sha256: str,
    expected_phase3_config_snapshot_sha256: str,
    expected_holdout_validation_sha256: str,
    source_root: Path,
) -> dict[str, Any]:
    """Verify signature, exact R06 provenance, and return its decode protocol."""
    payload = dict(artifact)
    signature = payload.pop("signature_sha256", None)
    if payload.get("schema_version") != HOLDOUT_SELECTION_SCHEMA_VERSION:
        raise ValueError("unsupported R06 selection artifact schema")
    if signature != fingerprint_json(payload):
        raise ValueError("R06 selection artifact signature mismatch")
    expected_cells = sorted(str(value) for value in expected_cell_ids)
    expected_systems = sorted(str(value) for value in expected_system_ids)
    if payload.get("source_family") != "R06":
        raise ValueError("R06 selection artifact has a forbidden family")
    if payload.get("selection_rule") != PHASE3_SELECTION_RULE:
        raise ValueError("R06 selection artifact rule mismatch")
    if payload.get("source_split") != "family_holdout_validation_R06_only":
        raise ValueError("R06 selection artifact split mismatch")
    if payload.get("source_cell_ids") != expected_cells:
        raise ValueError("R06 selection artifact cell coverage mismatch")
    if payload.get("source_system_ids") != expected_systems:
        raise ValueError("R06 selection artifact system coverage mismatch")
    if payload.get("source_cell_count") != len(expected_cells):
        raise ValueError("R06 selection artifact cell count mismatch")
    if payload.get("source_system_ids_sha256") != fingerprint_json(expected_systems):
        raise ValueError("R06 selection artifact system ID-set hash mismatch")
    if payload.get("source_cell_ids_sha256") != fingerprint_json(expected_cells):
        raise ValueError("R06 selection artifact cell ID-set hash mismatch")
    if payload.get("source_phase2_manifest_sha256") != str(expected_phase2_manifest_sha256):
        raise ValueError("R06 selection artifact Phase 2 manifest mismatch")
    if payload.get("source_phase3_config_snapshot_sha256") != str(
        expected_phase3_config_snapshot_sha256
    ):
        raise ValueError("R06 selection artifact Phase 3 config snapshot mismatch")
    if payload.get("source_holdout_validation_sha256") != str(expected_holdout_validation_sha256):
        raise ValueError("R06 selection artifact validation source mismatch")
    if payload.get("forbidden_family_outcomes_accessed") is not False:
        raise ValueError("R06 selection artifact reports forbidden-family access")
    if payload.get("directory_discovery_used") is not False:
        raise ValueError("R06 selection artifact reports directory discovery")
    provenance = payload.get("git")
    if (
        not isinstance(provenance, Mapping)
        or not str(provenance.get("commit") or "")
        or provenance.get("status_short")
    ):
        raise ValueError("R06 selection artifact Git provenance is invalid")
    if not str(payload.get("retrospective_signing_limitation") or ""):
        raise ValueError("R06 selection artifact omits its retrospective limitation")
    artifacts = payload.get("source_artifacts")
    if not isinstance(artifacts, list) or len(artifacts) != len(expected_cells):
        raise ValueError("R06 selection artifact source index mismatch")
    if any(row.get("family") != "R06" for row in artifacts):
        raise ValueError("R06 selection artifact source index contains another family")
    if sorted(str(row.get("cell_id")) for row in artifacts) != expected_cells:
        raise ValueError("R06 selection artifact source cell index mismatch")
    if sorted({str(row.get("system_id")) for row in artifacts}) != expected_systems:
        raise ValueError("R06 selection artifact source system index mismatch")
    if any(len(str(row.get("candidate_set_sha256") or "")) != 64 for row in artifacts):
        raise ValueError("R06 selection artifact candidate-set audit is missing")
    if payload.get("source_artifact_index_sha256") != fingerprint_json(artifacts):
        raise ValueError("R06 selection artifact source-index hash mismatch")
    path_sha_index = [
        {"path": row.get("path"), "sha256": row.get("sha256")}
        for row in artifacts
    ]
    if payload.get("source_path_sha256_index_sha256") != fingerprint_json(
        path_sha_index
    ):
        raise ValueError("R06 selection artifact path/hash index mismatch")
    filename_sha_index = [
        {
            "path": Path(str(row.get("path"))).name,
            "sha256": row.get("sha256"),
        }
        for row in artifacts
    ]
    if payload.get("source_filename_sha256_index_sha256") != fingerprint_json(
        filename_sha_index
    ):
        raise ValueError("R06 selection artifact filename/hash index mismatch")
    expected_paths = sorted(
        (Path("phase3") / "cells" / f"{cell_id}.json").as_posix()
        for cell_id in expected_cells
    )
    if sorted(str(row.get("path")) for row in artifacts) != expected_paths:
        raise ValueError("R06 selection artifact source paths are not the exact allowlist")
    if any(
        str(row.get("path"))
        != (Path("phase3") / "cells" / f"{row.get('cell_id')}.json").as_posix()
        for row in artifacts
    ):
        raise ValueError("R06 selection artifact path/cell binding mismatch")
    allowed_root = (Path(source_root) / "phase3" / "cells").resolve()
    for row in artifacts:
        source = (Path(source_root) / str(row.get("path"))).resolve()
        if source.parent != allowed_root:
            raise ValueError("R06 selection artifact source path escaped the shard allowlist")
        if (
            not source.is_file()
            or source.stat().st_size != int(row.get("bytes", -1))
            or sha256_file(source) != str(row.get("sha256"))
        ):
            raise ValueError("R06 selection artifact source hash mismatch")
    chosen = float(payload.get("chosen_lambda"))
    candidates = [float(value) for value in payload.get("candidate_lambdas") or []]
    if not math.isfinite(chosen) or chosen not in candidates:
        raise ValueError("R06 selection artifact chosen lambda is invalid")
    return {
        "selection_rule": PHASE3_SELECTION_RULE,
        "complexity_lambda": chosen,
        "source_split": "family_holdout_validation_R06_only",
        "selection_artifact_signature_sha256": str(signature),
    }


def validation_cell_id(
    *, system: str, bundle_index: int, noise_sigma: float, subsample_rho: float
) -> str:
    """Return a condition-independent cell identity for paired coverage."""
    raw = (
        f"{system}|b{int(bundle_index)}|n{float(noise_sigma):.17g}"
        f"|r{float(subsample_rho):.17g}"
    )
    return raw.replace(".", "p")


def candidate_seed_map(
    rows: Sequence[Mapping[str, Any]],
    *,
    config: Mapping[str, Any],
    bundle_indices: Sequence[int],
) -> dict[str, int]:
    """Create the method-independent decode seed map frozen by the plan."""
    namespace = str(config["selection"]["candidate_seed_namespace"])
    output: dict[str, int] = {}
    for bundle_index in sorted(int(value) for value in bundle_indices):
        bundle = config["seed_bundles"][bundle_index]
        for row in sorted(rows, key=system_id):
            name = system_id(row)
            for sigma, rho in corruption_grid(config):
                cell = validation_cell_id(
                    system=name,
                    bundle_index=bundle_index,
                    noise_sigma=sigma,
                    subsample_rho=rho,
                )
                output[cell] = stable_problem_seed(
                    int(bundle["candidate_seed"]),
                    system_id=name,
                    condition=namespace,
                    noise_sigma=sigma,
                    subsample_rho=rho,
                    sampling_replicate=bundle_index,
                )
    expected = len(rows) * len(bundle_indices) * len(corruption_grid(config))
    if len(output) != expected:
        raise ValueError("candidate seed map has duplicate validation cell identities")
    return dict(sorted(output.items()))


def candidate_seed_map_sha256(seed_map: Mapping[str, int]) -> str:
    return fingerprint_json({str(key): int(value) for key, value in seed_map.items()})


def build_trial_identity(
    *,
    condition: str,
    view: str,
    bundle_indices: Sequence[int],
    base_model_state_sha256: str,
    training_corpus_sha256: str,
    training_order_sha256: str,
    model_seed: int,
    validation_panel_sha256: str,
    candidate_seed_map_sha256_value: str,
) -> dict[str, Any]:
    """Build the condition-level identity shared by every grid candidate."""
    if condition not in TRAINABLE_CONDITIONS or view not in VIEWS:
        raise ValueError("unknown Phase 6 condition or data view")
    indices = sorted(int(value) for value in bundle_indices)
    if not indices or len(indices) != len(set(indices)):
        raise ValueError("bundle_indices must be non-empty and unique")
    return {
        "condition": condition,
        "view": view,
        "bundle_indices": indices,
        "base_model_state_sha256": str(base_model_state_sha256),
        "training_corpus_sha256": str(training_corpus_sha256),
        "training_order_sha256": str(training_order_sha256),
        "model_seed": int(model_seed),
        "validation_panel_sha256": str(validation_panel_sha256),
        "candidate_seed_map_sha256": str(candidate_seed_map_sha256_value),
    }


def delta_identity(
    trial_identity: Mapping[str, Any],
    *,
    stage: str,
    lr: float,
    steps: int,
    raw_checkpoint_sha256: str,
    config_fingerprint: str,
    training_source: str,
) -> dict[str, Any]:
    """Extend a paired trial identity with the exact delta provenance."""
    if stage not in {"screening", "confirmation"}:
        raise ValueError("unknown Phase 6 checkpoint stage")
    return {
        "schema_version": PHASE6_SCHEMA_VERSION,
        "stage": stage,
        **dict(trial_identity),
        "lr": float(lr),
        "steps": int(steps),
        "raw_checkpoint_sha256": str(raw_checkpoint_sha256),
        "config_fingerprint": str(config_fingerprint),
        "training_source": str(training_source),
    }


def cell_cache_identity(
    *,
    campaign_identity_sha256: str,
    stage: str,
    view: str,
    condition: str,
    delta_sha256: str | None,
    beam_size: int,
    cell_id: str,
    candidate_seed: int,
    input_trajectory_checksum: str,
    candidate_selection_sha256: str,
) -> dict[str, Any]:
    """Build the exact resume identity for one decode shard."""
    return {
        "schema_version": PHASE6_SCHEMA_VERSION,
        "campaign_identity_sha256": str(campaign_identity_sha256),
        "stage": str(stage),
        "view": str(view),
        "condition": str(condition),
        "delta_sha256": None if delta_sha256 is None else str(delta_sha256),
        "beam_size": int(beam_size),
        "cell_id": str(cell_id),
        "candidate_seed": int(candidate_seed),
        "input_trajectory_checksum": str(input_trajectory_checksum),
        "candidate_selection_sha256": str(candidate_selection_sha256),
    }


def load_cached_cell(path: Path, expected_identity: Mapping[str, Any]) -> dict[str, Any] | None:
    """Return a complete exact-identity shard, otherwise force recomputation."""
    source = Path(path)
    if not source.is_file():
        return None
    try:
        payload = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict) or payload.get("status") != "complete":
        return None
    if payload.get("cache_identity") != dict(expected_identity):
        return None
    return payload


def write_cached_cell(path: Path, payload: Mapping[str, Any]) -> Path:
    """Atomically persist a complete decode shard."""
    if payload.get("status") != "complete" or not isinstance(
        payload.get("cache_identity"), Mapping
    ):
        raise ValueError("only complete identity-bearing cells may enter the cache")
    return write_json(Path(path), dict(payload))


def coverage_audit(
    rows: Sequence[Mapping[str, Any]],
    *,
    expected_cell_ids: Sequence[str],
    expected_beam_size: int,
    expected_seed_map: Mapping[str, int],
) -> dict[str, Any]:
    """Audit exact cell coverage and paired candidate seeds for one trial."""
    observed_ids = [str(row.get("cell_id")) for row in rows]
    expected = sorted(str(value) for value in expected_cell_ids)
    observed = sorted(observed_ids)
    duplicates = sorted(value for value in set(observed_ids) if observed_ids.count(value) > 1)
    beam_exact = all(int(row.get("beam_size", -1)) == int(expected_beam_size) for row in rows)
    seed_exact = all(
        str(row.get("cell_id")) in expected_seed_map
        and int(row.get("candidate_seed", -1))
        == int(expected_seed_map[str(row.get("cell_id"))])
        for row in rows
    )
    identities_exact = all(
        isinstance(row.get("cache_identity"), Mapping)
        and row["cache_identity"].get("cell_id") == row.get("cell_id")
        and int(row["cache_identity"].get("candidate_seed", -1))
        == int(row.get("candidate_seed", -1))
        for row in rows
    )
    flags = {
        "coverage_exact": observed == expected and not duplicates,
        "beam_exact": beam_exact,
        "candidate_seeds_exact": seed_exact,
        "cache_identities_exact": identities_exact,
        "all_cells_complete": all(row.get("status") == "complete" for row in rows),
    }
    return {
        "pass": all(flags.values()),
        "pass_flags": flags,
        "expected_count": len(expected),
        "observed_count": len(rows),
        "duplicate_cell_ids": duplicates,
        "missing_cell_ids": sorted(set(expected) - set(observed)),
        "extra_cell_ids": sorted(set(observed) - set(expected)),
    }


def artifact_index(paths: Sequence[Path], *, relative_to: Path) -> list[dict[str, Any]]:
    """Hash an ordered set of existing sharded artifacts."""
    base = Path(relative_to)
    rows = []
    for path in sorted(Path(value) for value in paths):
        if not path.is_file():
            raise FileNotFoundError(path)
        rows.append(
            {
                "path": path.relative_to(base).as_posix(),
                "sha256": sha256_file(path),
                "bytes": path.stat().st_size,
            }
        )
    return rows


def expected_phase6_counts(
    *,
    screen_systems: Mapping[str, int],
    confirmation_systems: Mapping[str, int],
    n_grid_candidates: int,
    n_bundles: int,
    n_corruptions: int,
) -> dict[str, Any]:
    """Return explicit Phase 6 trial/cell counts for manifest auditing."""
    screen = {
        view: int(count) * int(n_corruptions) * len(TRAINABLE_CONDITIONS) * int(n_grid_candidates)
        for view, count in screen_systems.items()
    }
    confirmation = {
        view: int(count) * int(n_corruptions) * int(n_bundles)
        * (len(TRAINABLE_CONDITIONS) + 1)
        for view, count in confirmation_systems.items()
    }
    return {
        "trainable_grid_trials": len(VIEWS) * len(TRAINABLE_CONDITIONS) * int(n_grid_candidates),
        "selected_training_trials": len(VIEWS) * len(TRAINABLE_CONDITIONS) * int(n_bundles),
        "screening_cells": screen,
        "confirmation_cells": confirmation,
        "screening_cells_total": sum(screen.values()),
        "confirmation_cells_total": sum(confirmation.values()),
        "all_decode_cells_total": sum(screen.values()) + sum(confirmation.values()),
    }
