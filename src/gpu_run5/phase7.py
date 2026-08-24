"""Pure, testable execution contracts for GPU_RUN5 Phase 7.

Phase 7 ranks the released ODEFormer's four encoder and twelve decoder
Transformer blocks by single-block fine-tuning.  This module is deliberately
file-agnostic: the launcher supplies already-authorized validation artifacts,
and these helpers enforce the two-view firewall and the preregistered freeze.
"""

from __future__ import annotations

import math
from copy import deepcopy
from typing import Any, Mapping, Sequence

from gpu_run2_runtime import fingerprint_json
from gpu_run5.training import (
    OFFICIAL_LAYER_REGISTRY,
    deterministic_random_layer_sets,
    pairwise_rank_stability,
    tie_aware_vector_ranking,
)


PHASE7_SCHEMA_VERSION = "gpu_run5_phase7_v1"
VIEWS = ("main", "family_holdout")
SCREENING_BEAM_SIZE = 8
CONFIRMATION_BEAM_SIZE = 50
RANDOM_LAYER_SEED = 5101
RANDOM_SET_COUNT = 5
RANDOM_SET_SIZE = 3
SCORE_QUANTIZATION_DIGITS = 12


def freeze_view_selection_contracts(
    payload: Mapping[str, Any],
    *,
    expected_artifact_sha256: Mapping[str, str] | None = None,
) -> dict[str, dict[str, Any]]:
    """Validate independent Phase 3 selection contracts for both views.

    A single shared source artifact is intentionally rejected even if its
    numeric lambda happens to equal both view-specific choices.  The family
    holdout contract must carry the signed R06-only pre-stage identity; it may
    never be derived from the main R01--R08 validation artifact.
    """
    source = payload.get("candidate_selection_by_view")
    artifact_hashes = payload.get("candidate_selection_artifact_sha256_by_view")
    if not isinstance(source, Mapping) or set(source) != set(VIEWS):
        raise ValueError(
            "candidate_selection_by_view must contain exactly both Phase 7 views"
        )
    if not isinstance(artifact_hashes, Mapping) or set(artifact_hashes) != set(VIEWS):
        raise ValueError(
            "candidate_selection_artifact_sha256_by_view must contain exactly both views"
        )
    expected_families = {
        "main": [f"R{index:02d}" for index in range(1, 9)],
        "family_holdout": ["R06"],
    }
    frozen: dict[str, dict[str, Any]] = {}
    for view in VIEWS:
        row = source.get(view)
        if not isinstance(row, Mapping):
            raise ValueError(f"missing view-scoped candidate selection: {view}")
        rule = str(row.get("selection_rule", row.get("rule", "")))
        if rule != "multi_ic_complexity":
            raise ValueError(f"unexpected candidate selection rule for {view}: {rule}")
        try:
            complexity_lambda = float(row["complexity_lambda"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"missing numeric complexity lambda for {view}") from exc
        if not math.isfinite(complexity_lambda) or complexity_lambda < 0:
            raise ValueError(f"invalid complexity lambda for {view}")
        split = str(row.get("source_split", ""))
        expected_split = (
            "validation" if view == "main" else "family_holdout_validation_R06_only"
        )
        if split != expected_split:
            raise ValueError(f"candidate selection source split mismatch for {view}")
        artifact_sha = str(artifact_hashes[view])
        if len(artifact_sha) != 64:
            raise ValueError(f"candidate selection source hash missing for {view}")
        if expected_artifact_sha256 is not None and artifact_sha != str(
            expected_artifact_sha256[view]
        ):
            raise ValueError(f"candidate selection source hash mismatch for {view}")
        signature = row.get("selection_artifact_signature_sha256")
        if view == "family_holdout" and (
            not isinstance(signature, str) or len(signature) != 64
        ):
            raise ValueError("family-holdout R06-only selection signature is missing")
        if view == "main" and signature is not None:
            raise ValueError("main selection unexpectedly carries a holdout signature")
        frozen[view] = {
            "selection_rule": rule,
            "complexity_lambda": complexity_lambda,
            "source_split": split,
            "allowed_families": expected_families[view],
            "source_artifact_sha256": artifact_sha,
            "selection_artifact_signature_sha256": signature,
        }
    if (
        frozen["main"]["source_artifact_sha256"]
        == frozen["family_holdout"]["source_artifact_sha256"]
    ):
        raise ValueError("main and family-holdout selections must use distinct artifacts")
    return frozen


def phase7_trial_identity(
    *,
    view: str,
    layer: str,
    bundle_indices: Sequence[int],
    base_model_state_sha256: str,
    training_corpus_sha256: str,
    training_order_sha256: str,
    model_seed: int,
    validation_panel_sha256: str,
    candidate_seed_map_sha256: str,
    selection_contract_sha256: str,
) -> dict[str, Any]:
    """Build the exact paired identity shared by one layer's LR grid."""
    if view not in VIEWS:
        raise ValueError(f"unknown Phase 7 view: {view}")
    if layer not in OFFICIAL_LAYER_REGISTRY:
        raise ValueError(f"unknown ODEFormer block: {layer}")
    bundles = sorted(int(value) for value in bundle_indices)
    if not bundles or len(bundles) != len(set(bundles)):
        raise ValueError("bundle_indices must be non-empty and unique")
    fields = {
        "schema_version": PHASE7_SCHEMA_VERSION,
        "condition": "grn_single_block",
        "view": view,
        "layer": layer,
        "trainable_layers": [layer],
        "bundle_indices": bundles,
        "base_model_state_sha256": str(base_model_state_sha256),
        "training_corpus_sha256": str(training_corpus_sha256),
        "training_order_sha256": str(training_order_sha256),
        "model_seed": int(model_seed),
        "validation_panel_sha256": str(validation_panel_sha256),
        "candidate_seed_map_sha256": str(candidate_seed_map_sha256),
        "selection_contract_sha256": str(selection_contract_sha256),
    }
    if any(value == "" for value in fields.values()):
        raise ValueError("Phase 7 trial identity contains an empty provenance field")
    return fields


def phase7_delta_identity(
    trial_identity: Mapping[str, Any],
    *,
    stage: str,
    lr: float,
    steps: int,
    raw_checkpoint_sha256: str,
    config_fingerprint: str,
) -> dict[str, Any]:
    if stage not in {"screening", "confirmation"}:
        raise ValueError(f"unknown Phase 7 stage: {stage}")
    return {
        **dict(trial_identity),
        "stage": stage,
        "lr": float(lr),
        "steps": int(steps),
        "raw_checkpoint_sha256": str(raw_checkpoint_sha256),
        "config_fingerprint": str(config_fingerprint),
        "training_source": f"{trial_identity['view']}_grn_train",
    }


def phase7_cell_identity(
    *,
    campaign_identity_sha256: str,
    stage: str,
    view: str,
    layer: str,
    delta_sha256: str,
    beam_size: int,
    cell_id: str,
    candidate_seed: int,
    input_trajectory_checksum: str,
    selection_contract_sha256: str,
) -> dict[str, Any]:
    """Return an exact identity for an atomic decode shard."""
    if view not in VIEWS or layer not in OFFICIAL_LAYER_REGISTRY:
        raise ValueError("invalid Phase 7 cell view or layer")
    return {
        "schema_version": PHASE7_SCHEMA_VERSION,
        "campaign_identity_sha256": str(campaign_identity_sha256),
        "stage": str(stage),
        "view": view,
        "condition": "grn_single_block",
        "layer": layer,
        "delta_sha256": str(delta_sha256),
        "beam_size": int(beam_size),
        "cell_id": str(cell_id),
        "candidate_seed": int(candidate_seed),
        "input_trajectory_checksum": str(input_trajectory_checksum),
        "selection_contract_sha256": str(selection_contract_sha256),
    }


def expected_phase7_counts(
    *,
    systems_by_view: Mapping[str, int],
    n_grid_candidates: int,
    n_bundles: int,
    n_corruptions: int,
    n_layers: int = 16,
) -> dict[str, Any]:
    """Return the exact sharded training/decode budget for auditing."""
    if set(systems_by_view) != set(VIEWS):
        raise ValueError("systems_by_view must contain exactly both views")
    screening = {
        view: int(systems_by_view[view])
        * int(n_corruptions)
        * int(n_layers)
        * int(n_grid_candidates)
        for view in VIEWS
    }
    confirmation = {
        view: int(systems_by_view[view])
        * int(n_corruptions)
        * int(n_layers)
        * int(n_bundles)
        for view in VIEWS
    }
    return {
        "screening_training_trials": len(VIEWS) * int(n_layers) * int(n_grid_candidates),
        "selected_confirmation_training_trials": len(VIEWS)
        * int(n_layers)
        * int(n_bundles),
        "screening_cells": screening,
        "confirmation_cells": confirmation,
        "screening_cells_total": sum(screening.values()),
        "confirmation_cells_total": sum(confirmation.values()),
        "all_decode_cells_total": sum(screening.values()) + sum(confirmation.values()),
    }


def freeze_layer_sets(
    scores_by_view: Mapping[str, Mapping[str, Sequence[float]]],
    *,
    causal_rankings: Mapping[str, Sequence[str]],
    random_seed: int = RANDOM_LAYER_SEED,
    random_set_count: int = RANDOM_SET_COUNT,
    quantization_digits: int = SCORE_QUANTIZATION_DIGITS,
) -> dict[str, Any]:
    """Freeze IOLE, causal, bottom, and random controls before confirmation."""
    if set(scores_by_view) != set(VIEWS) or set(causal_rankings) != set(VIEWS):
        raise ValueError("layer freeze requires independent records for both views")
    random_sets = deterministic_random_layer_sets(
        OFFICIAL_LAYER_REGISTRY,
        seed=int(random_seed),
        n_sets=int(random_set_count),
        k=RANDOM_SET_SIZE,
    )
    views: dict[str, Any] = {}
    for view in VIEWS:
        scores = scores_by_view[view]
        if set(scores) != set(OFFICIAL_LAYER_REGISTRY):
            raise ValueError(f"IOLE score registry mismatch for {view}")
        ranking = tie_aware_vector_ranking(
            scores, quantization_digits=int(quantization_digits)
        )
        ordered = list(ranking["ranking"])
        causal = [str(value) for value in causal_rankings[view]]
        if len(causal) != len(OFFICIAL_LAYER_REGISTRY) or set(causal) != set(
            OFFICIAL_LAYER_REGISTRY
        ):
            raise ValueError(f"causal ranking registry mismatch for {view}")
        top3 = ordered[:3]
        views[view] = {
            "iole_formula_ranking": ranking,
            "top1": ordered[:1],
            "top3": top3,
            "bottom3": ordered[-3:],
            "causal_top3": causal[:3],
            "random3": {
                f"random3_{index}": values
                for index, values in enumerate(random_sets)
            },
            "random3_overlap_with_top3": {
                f"random3_{index}": len(set(values) & set(top3))
                for index, values in enumerate(random_sets)
            },
            "top_k_boundary_tie_broken_by_fixed_layer_name": bool(
                ranking["rows"][2]["tie_group"]
                == ranking["rows"][3]["tie_group"]
            ),
        }
    payload = {
        "schema_version": "gpu_run5_phase7_layer_freeze_v1",
        "source": "reduced_panel_bundle0_beam8_formula_score",
        "quantization_digits": int(quantization_digits),
        "random_layer_seed": int(random_seed),
        "random_sets_shared_across_views": True,
        "views": views,
        "test_accessed": False,
    }
    payload["freeze_sha256"] = fingerprint_json(payload)
    return payload


def confirmation_rank_stability(
    score_vectors: Mapping[str, Mapping[int | str, Mapping[str, Sequence[float]]]],
    *,
    quantization_digits: int = SCORE_QUANTIZATION_DIGITS,
) -> dict[str, Any]:
    """Compute per-view 3-bundle Spearman/Kendall stability without reranking."""
    if set(score_vectors) != set(VIEWS):
        raise ValueError("rank stability requires both data views")
    return {
        view: pairwise_rank_stability(
            score_vectors[view], quantization_digits=int(quantization_digits)
        )
        for view in VIEWS
    }


def contribution_records(
    *,
    frozen_ted_by_seed: Mapping[int | str, float],
    full_ted_by_seed: Mapping[int | str, float],
    layer_ted_by_seed: Mapping[int | str, Mapping[str, float]],
) -> dict[str, Any]:
    """Compute C_l only on seeds where full strictly improves frozen TED."""
    seeds = sorted(
        set(str(value) for value in frozen_ted_by_seed)
        & set(str(value) for value in full_ted_by_seed)
        & set(str(value) for value in layer_ted_by_seed)
    )
    frozen = {str(key): float(value) for key, value in frozen_ted_by_seed.items()}
    full = {str(key): float(value) for key, value in full_ted_by_seed.items()}
    layers = {
        str(seed): {str(layer): float(value) for layer, value in values.items()}
        for seed, values in layer_ted_by_seed.items()
    }
    rows = []
    for seed in seeds:
        base_value, full_value = frozen[seed], full[seed]
        denominator = base_value - full_value
        valid_denominator = (
            math.isfinite(base_value)
            and math.isfinite(full_value)
            and denominator > 0.0
        )
        for layer in OFFICIAL_LAYER_REGISTRY:
            value = layers[seed].get(layer)
            contribution = None
            if valid_denominator and value is not None and math.isfinite(value):
                contribution = (base_value - value) / denominator
            rows.append(
                {
                    "seed": seed,
                    "layer": layer,
                    "frozen_failure_aware_ted": base_value,
                    "full_failure_aware_ted": full_value,
                    "layer_failure_aware_ted": value,
                    "denominator": denominator if math.isfinite(denominator) else None,
                    "full_improves_frozen": valid_denominator,
                    "normalized_contribution": contribution,
                }
            )
    eligible = [
        seed
        for seed in seeds
        if math.isfinite(frozen[seed])
        and math.isfinite(full[seed])
        and frozen[seed] - full[seed] > 0.0
    ]
    return {
        "definition": "(L_frozen-L_layer)/(L_frozen-L_full)",
        "loss": "failure_aware_component_normalized_variable_aware_ted",
        "eligible_seeds": eligible,
        "ineligible_seeds": [seed for seed in seeds if seed not in eligible],
        "normalized_contribution_reportable": bool(eligible),
        "rows": rows,
    }


def freeze_selected_hyperparameters(
    selections: Mapping[str, Mapping[str, Mapping[str, Any]]]
) -> dict[str, Any]:
    """Strip a complete per-layer grid selection to its irreversible choices."""
    if set(selections) != set(VIEWS):
        raise ValueError("hyperparameter freeze requires both views")
    output: dict[str, Any] = {"views": {}, "test_accessed": False}
    for view in VIEWS:
        if set(selections[view]) != set(OFFICIAL_LAYER_REGISTRY):
            raise ValueError(f"hyperparameter selection registry mismatch for {view}")
        output["views"][view] = {}
        for layer in OFFICIAL_LAYER_REGISTRY:
            source = selections[view][layer]
            selected = source.get("selected")
            if not isinstance(selected, Mapping):
                raise ValueError(f"missing selected grid candidate: {view}/{layer}")
            output["views"][view][layer] = {
                "config": deepcopy(dict(selected.get("config") or {})),
                "score_vector": deepcopy(list(selected.get("score_vector") or [])),
                "delta_sha256": str((selected.get("delta") or {}).get("delta_sha256", "")),
                "candidate_index": int(source.get("selected_index", -1)),
            }
    output["schema_version"] = "gpu_run5_phase7_hyperparameter_freeze_v1"
    output["selection_source"] = "reduced_panel_bundle0_beam8"
    output["freeze_sha256"] = fingerprint_json(output)
    return output
