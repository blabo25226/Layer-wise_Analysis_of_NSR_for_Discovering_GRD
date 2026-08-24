from __future__ import annotations

from pathlib import Path

import pytest

from gpu_run5.phase7 import (
    CONFIRMATION_BEAM_SIZE,
    PHASE7_SCHEMA_VERSION,
    SCREENING_BEAM_SIZE,
    VIEWS,
    confirmation_rank_stability,
    contribution_records,
    expected_phase7_counts,
    freeze_layer_sets,
    freeze_selected_hyperparameters,
    freeze_view_selection_contracts,
    phase7_cell_identity,
    phase7_trial_identity,
)
from gpu_run5.training import OFFICIAL_LAYER_REGISTRY


def _selection_contracts() -> dict:
    return {
        "candidate_selection_by_view": {
            "main": {
                "selection_rule": "multi_ic_complexity",
                "complexity_lambda": 0.01,
                "source_split": "validation",
                "candidate_lambdas": [0.0, 0.0001, 0.001, 0.01],
            },
            "family_holdout": {
                "selection_rule": "multi_ic_complexity",
                "complexity_lambda": 0.001,
                "source_split": "family_holdout_validation_R06_only",
                "selection_artifact_signature_sha256": "c" * 64,
            },
        },
        "candidate_selection_artifact_sha256_by_view": {
            "main": "a" * 64,
            "family_holdout": "b" * 64,
        },
    }


def _scores(offset: float = 0.0) -> dict[str, list[float]]:
    return {
        layer: [
            0.5 + offset - index * 0.001,
            -0.2 - index * 0.001,
            0.9 - index * 0.001,
            -1.0 - index * 0.001,
        ]
        for index, layer in enumerate(OFFICIAL_LAYER_REGISTRY)
    }


def test_view_specific_selection_contract_rejects_shared_or_leaky_artifact() -> None:
    frozen = freeze_view_selection_contracts(_selection_contracts())
    assert set(frozen) == set(VIEWS)
    assert frozen["family_holdout"]["allowed_families"] == ["R06"]
    assert frozen["family_holdout"]["complexity_lambda"] == 0.001

    shared = _selection_contracts()
    shared["candidate_selection_artifact_sha256_by_view"]["family_holdout"] = (
        "a" * 64
    )
    with pytest.raises(ValueError, match="distinct artifacts"):
        freeze_view_selection_contracts(shared)

    leaked = _selection_contracts()
    leaked["candidate_selection_by_view"]["family_holdout"]["source_split"] = (
        "validation"
    )
    with pytest.raises(ValueError, match="source split mismatch"):
        freeze_view_selection_contracts(leaked)

    with pytest.raises(ValueError, match="exactly both"):
        freeze_view_selection_contracts(
            {
                "candidate_selection_by_view": {
                    "main": _selection_contracts()["candidate_selection_by_view"][
                        "main"
                    ]
                },
                "candidate_selection_artifact_sha256_by_view": {
                    "main": "a" * 64
                },
            }
        )


def test_phase7_exact_full_budget_is_26112_sharded_decode_cells() -> None:
    counts = expected_phase7_counts(
        systems_by_view={"main": 24, "family_holdout": 10},
        n_grid_candidates=9,
        n_bundles=3,
        n_corruptions=4,
    )
    assert counts == {
        "screening_training_trials": 288,
        "selected_confirmation_training_trials": 96,
        "screening_cells": {"main": 13824, "family_holdout": 5760},
        "confirmation_cells": {"main": 4608, "family_holdout": 1920},
        "screening_cells_total": 19584,
        "confirmation_cells_total": 6528,
        "all_decode_cells_total": 26112,
    }
    assert SCREENING_BEAM_SIZE == 8
    assert CONFIRMATION_BEAM_SIZE == 50


def test_layer_freeze_is_view_specific_tie_aware_and_random_sets_are_fixed() -> None:
    main = _scores()
    holdout = _scores()
    holdout["decoder_11"] = [0.99, -0.01, 0.99, -0.5]
    causal = {
        "main": list(reversed(OFFICIAL_LAYER_REGISTRY)),
        "family_holdout": list(OFFICIAL_LAYER_REGISTRY),
    }
    frozen = freeze_layer_sets(
        {"main": main, "family_holdout": holdout}, causal_rankings=causal
    )
    assert frozen["test_accessed"] is False
    assert frozen["views"]["main"]["top1"] != frozen["views"]["family_holdout"]["top1"]
    random_main = frozen["views"]["main"]["random3"]
    random_holdout = frozen["views"]["family_holdout"]["random3"]
    assert random_main == random_holdout
    assert len({tuple(value) for value in random_main.values()}) == 5
    assert all(len(value) == 3 for value in random_main.values())
    assert frozen["views"]["main"]["causal_top3"] == list(
        reversed(OFFICIAL_LAYER_REGISTRY)
    )[:3]
    assert len(frozen["freeze_sha256"]) == 64


def test_confirmation_stability_does_not_replace_frozen_ranking() -> None:
    payload = {
        view: {
            0: _scores(),
            1: _scores(0.01),
            2: _scores(0.02),
        }
        for view in VIEWS
    }
    stability = confirmation_rank_stability(payload)
    assert set(stability) == set(VIEWS)
    assert len(stability["main"]["pairs"]) == 3
    assert stability["main"]["mean_spearman"] == pytest.approx(1.0)


def test_contribution_only_exists_when_full_improves_frozen() -> None:
    layer_scores = {
        "0": {layer: 0.7 for layer in OFFICIAL_LAYER_REGISTRY},
        "1": {layer: 0.8 for layer in OFFICIAL_LAYER_REGISTRY},
        "2": {layer: 0.9 for layer in OFFICIAL_LAYER_REGISTRY},
    }
    result = contribution_records(
        frozen_ted_by_seed={"0": 0.8, "1": 0.8, "2": 0.8},
        full_ted_by_seed={"0": 0.6, "1": 0.8, "2": 0.9},
        layer_ted_by_seed=layer_scores,
    )
    assert result["eligible_seeds"] == ["0"]
    assert result["normalized_contribution_reportable"]
    seed0 = [row for row in result["rows"] if row["seed"] == "0"]
    seed1 = [row for row in result["rows"] if row["seed"] == "1"]
    assert all(row["normalized_contribution"] == pytest.approx(0.5) for row in seed0)
    assert all(row["normalized_contribution"] is None for row in seed1)


def test_trial_and_cell_identities_bind_view_layer_selection_and_seed() -> None:
    trial = phase7_trial_identity(
        view="family_holdout",
        layer="decoder_11",
        bundle_indices=[0],
        base_model_state_sha256="base",
        training_corpus_sha256="corpus",
        training_order_sha256="order",
        model_seed=0,
        validation_panel_sha256="panel",
        candidate_seed_map_sha256="seeds",
        selection_contract_sha256="selection",
    )
    assert trial["schema_version"] == PHASE7_SCHEMA_VERSION
    assert trial["trainable_layers"] == ["decoder_11"]
    cell = phase7_cell_identity(
        campaign_identity_sha256="campaign",
        stage="screening_lr1e-05_s200",
        view="family_holdout",
        layer="decoder_11",
        delta_sha256="delta",
        beam_size=8,
        cell_id="R06_validation_0|b0|n0|r0",
        candidate_seed=123,
        input_trajectory_checksum="trajectory",
        selection_contract_sha256="selection",
    )
    assert cell["view"] == "family_holdout"
    assert cell["candidate_seed"] == 123
    assert cell["selection_contract_sha256"] == "selection"


def test_hyperparameter_freeze_requires_all_16_layers_per_view() -> None:
    selected = {
        view: {
            layer: {
                "selected_index": 0,
                "selected": {
                    "config": {"lr": 1e-5, "steps": 200},
                    "score_vector": [0.1, -0.2, 0.9, -1.0],
                    "delta": {"delta_sha256": f"{index:064d}"},
                },
            }
            for index, layer in enumerate(OFFICIAL_LAYER_REGISTRY)
        }
        for view in VIEWS
    }
    frozen = freeze_selected_hyperparameters(selected)
    assert frozen["selection_source"] == "reduced_panel_bundle0_beam8"
    assert len(frozen["views"]["main"]) == 16
    missing = {view: dict(values) for view, values in selected.items()}
    missing["main"] = dict(missing["main"])
    missing["main"].pop("encoder_0")
    with pytest.raises(ValueError, match="registry mismatch"):
        freeze_selected_hyperparameters(missing)


def test_launcher_never_names_or_discovers_sealed_test_artifacts() -> None:
    launcher = Path("scripts/phases/gpu_run5_phase7.py")
    if not launcher.exists():
        pytest.skip("launcher is added after pure contract tests")
    source = launcher.read_text(encoding="utf-8")
    assert "glob(" not in source
    assert "rglob(" not in source
    assert "sealed_test.json" not in source
    assert "sealed_family_holdout_test.json" not in source
    assert '"test_accessed": False' in source
    assert "freeze_view_selection_contracts(" in source
    assert 'write_json(out / "layer_freeze.json"' in source
    assert 'write_json(out / "phase8_handoff.json"' in source
    assert '"phase8_selective_hyperparameters": "must_run_equal_own_grid"' in source
    assert 'payload.get("candidate_selection_by_view")' in source
    assert 'payload.get("candidate_selection_artifact_sha256_by_view")' in source
    assert 'root / "phase6_holdout_prestage" / "selection.json"' in source
    assert 'prestage_selection.get("source_family") != "R06"' in source
