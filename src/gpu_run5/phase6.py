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
