"""Pure execution and firewall contracts for GPU_RUN5 Phase 8.

The module deliberately has no knowledge of phase directories.  The launcher
must first finish validation, freeze the exact five-condition protocol, and
only then claim the single test-open event before it receives sealed records.
"""

from __future__ import annotations

import fcntl
import json
import math
import os
from copy import deepcopy
from pathlib import Path
from typing import Any, Mapping, Sequence
from uuid import uuid4

from gpu_run2_runtime import fingerprint_json, utc_now
from gpu_run5.training import OFFICIAL_LAYER_REGISTRY


PHASE8_SCHEMA_VERSION = "gpu_run5_phase8_v1"
VIEWS = ("main", "family_holdout")
REUSED_VALIDATION_CONDITIONS = (
    "frozen",
    "official_continued_full",
    "grn_full",
    "grn_decoder_all",
)
SELECTIVE_BASE_CONDITIONS = ("grn_top1", "grn_top3", "grn_causal_top3", "grn_bottom3")
FINAL_CONDITIONS = (
    "frozen",
    "official_continued_full",
    "grn_full",
    "grn_top3",
    "grn_random3_0",
)
SCORE_QUANTIZATION_DIGITS = 12


def selective_conditions(random_set_count: int = 5) -> tuple[str, ...]:
    count = int(random_set_count)
    if count <= 0:
        raise ValueError("random_set_count must be positive")
    return SELECTIVE_BASE_CONDITIONS + tuple(
        f"grn_random3_{index}" for index in range(count)
    )


def expected_layer_sets(layer_freeze: Mapping[str, Any], *, random_set_count: int = 5) -> dict[str, dict[str, list[str]]]:
    """Validate and adapt the Phase 7 layer freeze for Phase 8 conditions."""
    if layer_freeze.get("test_accessed") is not False:
        raise ValueError("Phase 7 layer freeze does not prove test_accessed=false")
    views = layer_freeze.get("views")
    if not isinstance(views, Mapping) or set(views) != set(VIEWS):
        raise ValueError("Phase 7 layer freeze must contain exactly both views")
    registry = set(OFFICIAL_LAYER_REGISTRY)
    output: dict[str, dict[str, list[str]]] = {}
    for view in VIEWS:
        row = views[view]
        if not isinstance(row, Mapping):
            raise ValueError(f"invalid layer freeze view: {view}")
        random3 = row.get("random3")
        expected_random = {f"random3_{index}" for index in range(int(random_set_count))}
        if not isinstance(random3, Mapping) or set(random3) != expected_random:
            raise ValueError(f"random layer-set registry mismatch for {view}")
        mappings = {
            "grn_top1": row.get("top1"),
            "grn_top3": row.get("top3"),
            "grn_causal_top3": row.get("causal_top3"),
            "grn_bottom3": row.get("bottom3"),
            **{f"grn_{key}": value for key, value in random3.items()},
        }
        expected_sizes = {"grn_top1": 1, **{name: 3 for name in mappings if name != "grn_top1"}}
        normalized: dict[str, list[str]] = {}
        for condition, values in mappings.items():
            layers = [str(value) for value in (values or [])]
            if len(layers) != expected_sizes[condition] or len(layers) != len(set(layers)):
                raise ValueError(f"invalid layer count for {view}/{condition}")
            if not set(layers).issubset(registry):
                raise ValueError(f"unknown layer in {view}/{condition}")
            normalized[condition] = layers
        output[view] = normalized
    return output


def validate_selection_contracts(payload: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    """Require distinct validation-only candidate-selection artifacts per view."""
    source = payload.get("candidate_selection", payload)
    if not isinstance(source, Mapping) or set(source) != set(VIEWS):
        raise ValueError("candidate selection must contain exactly both views")
    expected_families = {
        "main": [f"R{index:02d}" for index in range(1, 9)],
        "family_holdout": ["R06"],
    }
    output: dict[str, dict[str, Any]] = {}
    for view in VIEWS:
        row = source[view]
        if not isinstance(row, Mapping):
            raise ValueError(f"missing candidate-selection contract for {view}")
        rule = str(row.get("selection_rule", row.get("rule", "")))
        if rule != "multi_ic_complexity":
            raise ValueError(f"unexpected candidate-selection rule for {view}")
        value = float(row.get("complexity_lambda", float("nan")))
        if not math.isfinite(value) or value < 0:
            raise ValueError(f"invalid complexity lambda for {view}")
        families = sorted(str(value) for value in row.get("allowed_families", []))
        if families != expected_families[view]:
            raise ValueError(f"candidate-selection family scope mismatch for {view}")
        artifact_sha = str(row.get("source_artifact_sha256", ""))
        if len(artifact_sha) != 64:
            raise ValueError(f"candidate-selection artifact hash missing for {view}")
        expected_split = "validation" if view == "main" else "family_holdout_validation_R06_only"
        if row.get("source_split") != expected_split:
            raise ValueError(f"candidate selection is not validation-only for {view}")
        signature = row.get("selection_artifact_signature_sha256")
        if view == "family_holdout" and (not isinstance(signature, str) or len(signature) != 64):
            raise ValueError("family-holdout R06-only selection signature is missing")
        if view == "main" and signature is not None:
            raise ValueError("main selection unexpectedly carries a holdout signature")
        output[view] = {
            "selection_rule": rule,
            "complexity_lambda": value,
            "source_split": expected_split,
            "allowed_families": families,
            "source_artifact_sha256": artifact_sha,
            "selection_artifact_signature_sha256": signature,
        }
    if output["main"]["source_artifact_sha256"] == output["family_holdout"]["source_artifact_sha256"]:
        raise ValueError("main and family-holdout candidate selection must use distinct artifacts")
    return output


def phase8_trial_identity(
    *,
    view: str,
    condition: str,
    layers: Sequence[str],
    bundle_indices: Sequence[int],
    base_model_state_sha256: str,
    training_corpus_sha256: str,
    training_order_sha256: str,
    model_seed: int,
    validation_panel_sha256: str,
    candidate_seed_map_sha256: str,
    layer_freeze_sha256: str,
    selection_contract_sha256: str,
) -> dict[str, Any]:
    if view not in VIEWS or condition not in selective_conditions(5):
        raise ValueError("unknown Phase 8 view or selective condition")
    names = [str(value) for value in layers]
    if not names or len(names) != len(set(names)) or not set(names).issubset(OFFICIAL_LAYER_REGISTRY):
        raise ValueError("invalid Phase 8 trainable layer set")
    bundles = sorted(int(value) for value in bundle_indices)
    if not bundles or len(bundles) != len(set(bundles)):
        raise ValueError("bundle_indices must be non-empty and unique")
    return {
        "schema_version": PHASE8_SCHEMA_VERSION,
        "condition": condition,
        "view": view,
        "trainable_layers": names,
        "bundle_indices": bundles,
        "base_model_state_sha256": str(base_model_state_sha256),
        "training_corpus_sha256": str(training_corpus_sha256),
        "training_order_sha256": str(training_order_sha256),
        "model_seed": int(model_seed),
        "validation_panel_sha256": str(validation_panel_sha256),
        "candidate_seed_map_sha256": str(candidate_seed_map_sha256),
        "layer_freeze_sha256": str(layer_freeze_sha256),
        "selection_contract_sha256": str(selection_contract_sha256),
    }


def phase8_cell_identity(
    *,
    campaign_identity_sha256: str,
    stage: str,
    view: str,
    condition: str,
    checkpoint_sha256: str,
    beam_size: int,
    cell_id: str,
    candidate_seed: int,
    input_trajectory_checksum: str,
    selection_contract_sha256: str,
    final_freeze_sha256: str | None = None,
    test_open_event_id: str | None = None,
) -> dict[str, Any]:
    allowed_stages = {"validation_screening", "validation_confirmation", "final_test"}
    if stage not in allowed_stages or view not in VIEWS:
        raise ValueError("invalid Phase 8 cell stage or view")
    if stage == "final_test":
        if condition not in FINAL_CONDITIONS or not final_freeze_sha256 or not test_open_event_id:
            raise ValueError("final-test cell lacks frozen protocol or test-open identity")
    elif final_freeze_sha256 is not None or test_open_event_id is not None:
        raise ValueError("validation cell may not carry final-test access metadata")
    return {
        "schema_version": PHASE8_SCHEMA_VERSION,
        "campaign_identity_sha256": str(campaign_identity_sha256),
        "stage": stage,
        "view": view,
        "condition": str(condition),
        "checkpoint_sha256": str(checkpoint_sha256),
        "beam_size": int(beam_size),
        "cell_id": str(cell_id),
        "candidate_seed": int(candidate_seed),
        "input_trajectory_checksum": str(input_trajectory_checksum),
        "selection_contract_sha256": str(selection_contract_sha256),
        "final_freeze_sha256": final_freeze_sha256,
        "test_open_event_id": test_open_event_id,
    }


def expected_phase8_validation_counts(
    *,
    screen_systems: Mapping[str, int],
    confirmation_systems: Mapping[str, int],
    n_grid_candidates: int,
    n_bundles: int,
    n_corruptions: int,
    random_set_count: int = 5,
) -> dict[str, Any]:
    if set(screen_systems) != set(VIEWS) or set(confirmation_systems) != set(VIEWS):
        raise ValueError("system counts must contain exactly both Phase 8 views")
    n_conditions = len(selective_conditions(random_set_count))
    screen = {
        view: int(screen_systems[view]) * int(n_corruptions) * n_conditions * int(n_grid_candidates)
        for view in VIEWS
    }
    confirmation = {
        view: int(confirmation_systems[view]) * int(n_corruptions) * n_conditions * int(n_bundles)
        for view in VIEWS
    }
    return {
        "selective_conditions": n_conditions,
        "grid_trials": len(VIEWS) * n_conditions * int(n_grid_candidates),
        "selected_training_trials": len(VIEWS) * n_conditions * int(n_bundles),
        "screening_cells": screen,
        "confirmation_cells": confirmation,
        "screening_cells_total": sum(screen.values()),
        "confirmation_cells_total": sum(confirmation.values()),
        "all_decode_cells_total": sum(screen.values()) + sum(confirmation.values()),
    }


def expected_phase8_final_counts(*, main_systems: int, holdout_systems: int, n_bundles: int, n_corruptions: int) -> dict[str, Any]:
    per_view = {
        "main": int(main_systems) * len(FINAL_CONDITIONS) * int(n_bundles) * int(n_corruptions),
        "family_holdout": int(holdout_systems) * len(FINAL_CONDITIONS) * int(n_bundles) * int(n_corruptions),
    }
    return {"conditions": len(FINAL_CONDITIONS), "cells": per_view, "cells_total": sum(per_view.values())}


def _quantized_score(value: Sequence[float], digits: int = SCORE_QUANTIZATION_DIGITS) -> tuple[float, float, float, float]:
    vector = tuple(float(item) for item in value)
    if len(vector) != 4 or any(math.isnan(item) for item in vector):
        raise ValueError(f"invalid formula score vector: {vector}")
    return tuple(round(item, int(digits)) if math.isfinite(item) else item for item in vector)  # type: ignore[return-value]


def evaluate_go6(main_validation_scores: Mapping[str, Sequence[float]], *, random_sets_to_beat: int = 3) -> dict[str, Any]:
    """Apply the preregistered main-validation-only Go 6 rule."""
    required = {"frozen", "grn_top3", *(f"grn_random3_{index}" for index in range(5))}
    if not required.issubset(main_validation_scores):
        raise ValueError(f"Go 6 score registry missing: {sorted(required - set(main_validation_scores))}")
    top = _quantized_score(main_validation_scores["grn_top3"])
    frozen = _quantized_score(main_validation_scores["frozen"])
    random = {name: _quantized_score(main_validation_scores[name]) for name in sorted(required) if name.startswith("grn_random3_")}
    beaten = [name for name, score in random.items() if top > score]
    threshold = int(random_sets_to_beat)
    if threshold != 3:
        raise ValueError("GPU_RUN5 preregisters exactly three of five random sets")
    return {
        "rule": "grn_top3_strictly_beats_frozen_and_at_least_3_of_5_random3_on_main_validation_formula_score",
        "quantization_digits": SCORE_QUANTIZATION_DIGITS,
        "grn_top3_score": list(top),
        "frozen_score": list(frozen),
        "random_scores": {key: list(value) for key, value in random.items()},
        "beats_frozen": top > frozen,
        "random_sets_beaten": beaten,
        "n_random_sets_beaten": len(beaten),
        "required_random_sets_beaten": threshold,
        "pass": bool(top > frozen and len(beaten) >= threshold),
        "test_accessed": False,
    }


def build_final_freeze(
    *,
    checkpoint_registry: Mapping[str, Mapping[str, Mapping[str, Any]]],
    layer_sets: Mapping[str, Mapping[str, Sequence[str]]],
    candidate_selection: Mapping[str, Mapping[str, Any]],
    upstream_manifest_sha256: Mapping[str, str],
    config_fingerprint: str,
    layer_freeze_sha256: str,
    validation_freeze_sha256: str,
    expected_bundles: int = 3,
    beam_size: int = 50,
    corruptions: Sequence[Sequence[float]] = ((0.0, 0.0), (0.0, 0.5), (0.05, 0.0), (0.05, 0.5)),
) -> dict[str, Any]:
    """Create the sole immutable protocol allowed to open either test view."""
    if set(checkpoint_registry) != set(VIEWS) or set(layer_sets) != set(VIEWS):
        raise ValueError("final freeze requires separate checkpoint and layer registries for both views")
    frozen_registry: dict[str, Any] = {}
    for view in VIEWS:
        conditions = checkpoint_registry[view]
        if tuple(conditions) != FINAL_CONDITIONS and set(conditions) != set(FINAL_CONDITIONS):
            raise ValueError(f"final condition registry mismatch for {view}")
        frozen_registry[view] = {}
        for condition in FINAL_CONDITIONS:
            bundles = conditions[condition]
            expected_keys = {str(index) for index in range(int(expected_bundles))}
            normalized = {str(key): deepcopy(dict(value)) for key, value in bundles.items()}
            if set(normalized) != expected_keys:
                raise ValueError(f"checkpoint bundle registry mismatch for {view}/{condition}")
            identities = []
            for bundle, record in sorted(normalized.items()):
                file_sha = str(record.get("file_sha256", ""))
                state_sha = str(record.get("checkpoint_sha256", record.get("delta_sha256", "")))
                if len(file_sha) != 64 or len(state_sha) != 64:
                    raise ValueError(f"checkpoint hash missing for {view}/{condition}/bundle{bundle}")
                if str(record.get("view")) != view or str(record.get("condition")) != condition:
                    raise ValueError(f"checkpoint provenance mismatch for {view}/{condition}/bundle{bundle}")
                identities.append(record)
            frozen_registry[view][condition] = identities
    payload = {
        "schema_version": "gpu_run5_phase8_final_freeze_v1",
        "conditions": list(FINAL_CONDITIONS),
        "condition_selection": "preregistered_not_validation_selected",
        "test_random_representative": "grn_random3_0",
        "views": frozen_registry,
        "layer_sets": deepcopy({view: dict(layer_sets[view]) for view in VIEWS}),
        "candidate_selection": deepcopy({view: dict(candidate_selection[view]) for view in VIEWS}),
        "candidate_budget": {"beam_size": int(beam_size), "corruptions": [list(value) for value in corruptions], "bundles": int(expected_bundles)},
        "upstream_manifest_sha256": dict(upstream_manifest_sha256),
        "config_fingerprint": str(config_fingerprint),
        "layer_freeze_sha256": str(layer_freeze_sha256),
        "validation_freeze_sha256": str(validation_freeze_sha256),
        "generalization_used_for_candidate_selection": False,
        "test_accessed": False,
    }
    payload["freeze_sha256"] = fingerprint_json(payload)
    return payload


def audit_go7(
    freeze: Mapping[str, Any],
    *,
    go6: Mapping[str, Any],
    upstream_test_accessed: Mapping[str, bool],
    observed_freeze_sha256: str,
) -> dict[str, Any]:
    expected_upstream = {f"phase{phase}" for phase in range(2, 8)}
    checks = {
        "go6_passed": go6.get("pass") is True and go6.get("test_accessed") is False,
        "exact_preregistered_final_conditions": list(freeze.get("conditions") or []) == list(FINAL_CONDITIONS),
        "both_views_frozen_separately": set((freeze.get("views") or {})) == set(VIEWS),
        "candidate_budget_beam50": int((freeze.get("candidate_budget") or {}).get("beam_size", -1)) == 50,
        "three_bundles_frozen": int((freeze.get("candidate_budget") or {}).get("bundles", -1)) == 3,
        "generalization_not_used_for_selection": freeze.get("generalization_used_for_candidate_selection") is False,
        "freeze_hash_matches_disk": str(freeze.get("freeze_sha256"))
        == str(observed_freeze_sha256)
        == fingerprint_json({key: value for key, value in freeze.items() if key != "freeze_sha256"}),
        "all_upstream_phases_prove_test_unopened": set(upstream_test_accessed)
        == expected_upstream
        and all(value is False for value in upstream_test_accessed.values()),
        "freeze_itself_proves_test_unopened": freeze.get("test_accessed") is False,
    }
    return {"checks": checks, "pass": all(checks.values()), "test_accessed": False}


def evaluate_preregistered_test_outcomes(
    *,
    main_summaries: Mapping[str, Mapping[str, Any]],
    odebench_forgetting: Mapping[str, Mapping[str, Any]],
    test_open_event_id: str,
) -> dict[str, Any]:
    """Mechanically evaluate the three preregistered Phase 8 predictions."""
    required_grn = {"frozen", "grn_top3", "grn_full"}
    if not required_grn.issubset(main_summaries):
        raise ValueError(
            f"preregistered GRN summaries missing: {sorted(required_grn - set(main_summaries))}"
        )
    if not required_grn.issubset(odebench_forgetting):
        raise ValueError(
            "preregistered ODEBench summaries missing: "
            f"{sorted(required_grn - set(odebench_forgetting))}"
        )

    def formula_vector(condition: str) -> tuple[float, float, float]:
        raw = tuple(
            float(value)
            for value in main_summaries[condition].get(
                "formula_score_vector_without_ce", ()
            )
        )
        if len(raw) != 3 or any(not math.isfinite(value) for value in raw):
            raise ValueError(f"invalid final GRN formula score for {condition}: {raw}")
        return tuple(round(value, SCORE_QUANTIZATION_DIGITS) for value in raw)  # type: ignore[return-value]

    def ode_exact(condition: str) -> float:
        value = float(
            odebench_forgetting[condition].get(
                "exponent_aware_skeleton_exact_system_then_seed_macro",
                float("nan"),
            )
        )
        if not math.isfinite(value) or not 0.0 <= value <= 1.0:
            raise ValueError(f"invalid ODEBench exponent-aware exact rate for {condition}")
        return value

    def ode_drop(condition: str) -> float:
        value = float(
            odebench_forgetting[condition].get(
                "paired_exponent_aware_skeleton_drop_from_frozen_system_then_seed_macro",
                float("nan"),
            )
        )
        if not math.isfinite(value):
            raise ValueError(f"invalid paired ODEBench forgetting drop for {condition}")
        return value

    frozen_score = formula_vector("frozen")
    top_score = formula_vector("grn_top3")
    full_score = formula_vector("grn_full")
    p3_rate = frozen_score[0]
    p3_supported = p3_rate < 0.05
    reconstruction = float(main_summaries["frozen"].get("reconstruction_r2_median"))
    if not math.isfinite(reconstruction):
        raise ValueError("invalid frozen reconstruction R2 median")
    p4_supported = reconstruction >= 0.85 and p3_supported
    frozen_exact, top_exact, full_exact = (
        ode_exact(condition) for condition in ("frozen", "grn_top3", "grn_full")
    )
    top_drop = ode_drop("grn_top3")
    full_drop = ode_drop("grn_full")
    if not math.isclose(top_drop, frozen_exact - top_exact, abs_tol=1e-12) or not math.isclose(
        full_drop, frozen_exact - full_exact, abs_tol=1e-12
    ):
        raise ValueError("paired ODEBench forgetting drop disagrees with frozen-rate difference")
    top_better = top_score > full_score
    p7_supported = top_better and top_drop < full_drop
    return {
        "schema_version": "gpu_run5_phase8_preregistered_test_outcomes_v1",
        "P3": {
            "metric": "main_frozen_component_exponent_aware_exact_system_then_seed_macro",
            "value": p3_rate,
            "operator": "<",
            "threshold": 0.05,
            "supported": p3_supported,
            "outcome": "hit" if p3_supported else "miss",
        },
        "P4": {
            "metric": "main_frozen_reconstruction_r2_median_and_P3",
            "reconstruction_r2_median": reconstruction,
            "reconstruction_operator": ">=",
            "reconstruction_threshold": 0.85,
            "P3_required_and_supported": p3_supported,
            "supported": p4_supported,
            "outcome": "hit" if p4_supported else "miss",
        },
        "P7": {
            "metric": "main_test_formula_lexicographic_and_odebench_exponent_exact_forgetting",
            "score_quantization_digits": SCORE_QUANTIZATION_DIGITS,
            "grn_top3_formula_score": list(top_score),
            "grn_full_formula_score": list(full_score),
            "grn_top3_strictly_better": top_better,
            "odebench_frozen_exponent_exact": frozen_exact,
            "odebench_grn_top3_exponent_exact": top_exact,
            "odebench_grn_full_exponent_exact": full_exact,
            "odebench_grn_top3_drop_from_frozen": top_drop,
            "odebench_grn_full_drop_from_frozen": full_drop,
            "top3_drop_strictly_smaller": top_drop < full_drop,
            "supported": p7_supported,
            "outcome": "hit" if p7_supported else "miss",
        },
        "test_open_event_id": str(test_open_event_id),
        "test_accessed": True,
    }


def _fsync_parent(path: Path) -> None:
    descriptor = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _replace_json_durably(path: Path, payload: Mapping[str, Any]) -> None:
    temporary = path.with_name(f"{path.name}.{os.getpid()}.partial")
    encoded = (json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        _fsync_parent(path)
    except BaseException:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass
        raise


def claim_test_open(ledger_path: Path, *, freeze_sha256: str, sealed_paths: Mapping[str, str]) -> dict[str, Any]:
    """Atomically claim the campaign's sole test-open event before reading tests.

    An interrupted run may resume with the same event/freeze/path registry.  A
    completed ledger or any identity drift is rejected.
    """
    path = Path(ledger_path)
    normalized_paths = {str(key): str(value) for key, value in sorted(sealed_paths.items())}
    if path.exists():
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("freeze_sha256") != str(freeze_sha256) or payload.get("sealed_paths") != normalized_paths:
            raise RuntimeError("test-open ledger identity drift")
        if payload.get("open_count") != 1:
            raise RuntimeError("invalid test-open count")
        if payload.get("status") == "complete":
            raise RuntimeError("final test was already completed and cannot be reopened")
        if payload.get("status") not in {"claimed", "running"}:
            raise RuntimeError("invalid resumable test-open ledger status")
        payload["status"] = "running"
        payload["resume_count"] = int(payload.get("resume_count", 0)) + 1
        payload["resumed_at_utc"] = utc_now()
    else:
        payload = {
            "schema_version": "gpu_run5_phase8_test_open_ledger_v1",
            "event_id": uuid4().hex,
            "freeze_sha256": str(freeze_sha256),
            "sealed_paths": normalized_paths,
            "sealed_artifact_sha256": None,
            "status": "claimed",
            "open_count": 1,
            "resume_count": 0,
            "claimed_at_utc": utc_now(),
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        encoded = (json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
        try:
            descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError:
            # Another process won the atomic claim.  The caller holds the
            # campaign lock, so this indicates external protocol drift.
            raise RuntimeError("test-open ledger was claimed concurrently")
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        _fsync_parent(path)
        return payload
    _replace_json_durably(path, payload)
    return payload


def acquire_test_open_lock(lock_path: Path) -> Any:
    """Hold an exclusive process lock for the complete final-test invocation."""
    path = Path(lock_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = path.open("a+", encoding="utf-8")
    try:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        handle.close()
        raise RuntimeError("another Phase 8 final-test process holds the test-open lock")
    return handle


def bind_test_artifact_hashes(ledger_path: Path, hashes: Mapping[str, str]) -> dict[str, Any]:
    path = Path(ledger_path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    normalized = {str(key): str(value) for key, value in sorted(hashes.items())}
    if any(len(value) != 64 for value in normalized.values()):
        raise ValueError("sealed test artifact hash missing")
    prior = payload.get("sealed_artifact_sha256")
    if prior is not None and prior != normalized:
        raise RuntimeError("sealed test artifact changed after the test-open event")
    payload["sealed_artifact_sha256"] = normalized
    payload["status"] = "running"
    _replace_json_durably(path, payload)
    return payload


def complete_test_open(ledger_path: Path, *, final_artifact_sha256: Mapping[str, str]) -> dict[str, Any]:
    path = Path(ledger_path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("status") not in {"claimed", "running"} or payload.get("open_count") != 1:
        raise RuntimeError("test-open ledger cannot be completed")
    if not payload.get("sealed_artifact_sha256"):
        raise RuntimeError("sealed test hashes were never bound to the ledger")
    normalized = {str(key): str(value) for key, value in sorted(final_artifact_sha256.items())}
    if any(len(value) != 64 for value in normalized.values()):
        raise ValueError("final artifact hash missing")
    payload["final_artifact_sha256"] = normalized
    payload["status"] = "complete"
    payload["completed_at_utc"] = utc_now()
    _replace_json_durably(path, payload)
    return payload
