from __future__ import annotations

import json
from pathlib import Path

import pytest

from gpu_run5.phase6 import (
    TRAINABLE_CONDITIONS,
    VIEWS,
    audit_data_views,
    build_trial_identity,
    candidate_seed_map,
    candidate_seed_map_sha256,
    cell_cache_identity,
    coverage_audit,
    expected_phase6_counts,
    hyperparameter_grid,
    load_cached_cell,
    validation_cell_id,
    write_cached_cell,
)


def _row(system_id: str, family: str, checksum: str | None = None) -> dict:
    return {
        "system_id": system_id,
        "family": family,
        "trajectories": [
            {
                "role": "input",
                "role_index": 0,
                "times": [0.0, 1.0],
                "trajectory": [[0.0], [1.0]],
                "checksum": checksum or system_id,
            }
        ],
    }


def _config() -> dict:
    return {
        "selection": {"candidate_seed_namespace": "paired_phase6"},
        "seed_bundles": [
            {"candidate_seed": 3101},
            {"candidate_seed": 3202},
            {"candidate_seed": 3303},
        ],
        "corruptions": {
            "noise_sigmas": [0.0, 0.05],
            "subsample_rhos": [0.0, 0.5],
        },
    }


def test_data_views_are_exact_subsets_and_holdout_selection_is_r06_only() -> None:
    main_train = [_row("R01_train_0", "R01"), _row("R02_train_0", "R02")]
    main_validation = [_row("R06_validation_0", "R06"), _row("R01_validation_0", "R01")]
    audit = audit_data_views(
        main_train=main_train,
        main_validation=main_validation,
        holdout_train=main_train,
        holdout_validation=[main_validation[0]],
        holdout_train_families=["R01", "R02"],
        holdout_selection_family="R06",
    )
    assert audit["pass"]
    assert audit["families"]["holdout_validation"] == ["R06"]
    assert all(len(value) == 64 for value in audit["record_set_sha256"].values())

    leaked = audit_data_views(
        main_train=main_train,
        main_validation=main_validation,
        holdout_train=main_train,
        holdout_validation=main_validation,
        holdout_train_families=["R01", "R02"],
        holdout_selection_family="R06",
    )
    assert not leaked["pass"]
    assert not leaked["pass_flags"]["holdout_selection_family_exact"]
    assert not leaked["pass_flags"]["holdout_selection_is_exact_subset_of_main_validation"]


def test_exact_grid_and_phase_counts_match_preregistered_contract() -> None:
    grid = hyperparameter_grid([1e-6, 1e-5, 1e-4], [50, 200, 1000])
    assert len(grid) == 9
    assert {(row["lr"], row["steps"]) for row in grid} == {
        (lr, step)
        for lr in (1e-6, 1e-5, 1e-4)
        for step in (50, 200, 1000)
    }
    with pytest.raises(ValueError, match="duplicates"):
        hyperparameter_grid([1e-5, 1e-5], [50])

    counts = expected_phase6_counts(
        screen_systems={"main": 24, "family_holdout": 10},
        confirmation_systems={"main": 80, "family_holdout": 10},
        n_grid_candidates=9,
        n_bundles=3,
        n_corruptions=4,
    )
    assert counts == {
        "trainable_grid_trials": 54,
        "selected_training_trials": 18,
        "screening_cells": {"main": 2592, "family_holdout": 1080},
        "confirmation_cells": {"main": 3840, "family_holdout": 480},
        "screening_cells_total": 3672,
        "confirmation_cells_total": 4320,
        "all_decode_cells_total": 7992,
    }


def test_candidate_seeds_are_condition_neutral_and_cells_resume_by_exact_identity(
    tmp_path: Path,
) -> None:
    config = _config()
    rows = [_row("R01_validation_0", "R01"), _row("R06_validation_0", "R06")]
    seed_map = candidate_seed_map(rows, config=config, bundle_indices=[0])
    assert len(seed_map) == 8
    assert len(candidate_seed_map_sha256(seed_map)) == 64
    cell = validation_cell_id(
        system="R01_validation_0", bundle_index=0, noise_sigma=0.05, subsample_rho=0.5
    )
    identity = cell_cache_identity(
        campaign_identity_sha256="a" * 64,
        stage="screening_lr1e-05_s200",
        view="main",
        condition="grn_full",
        delta_sha256="b" * 64,
        beam_size=8,
        cell_id=cell,
        candidate_seed=seed_map[cell],
        input_trajectory_checksum="trajectory-sha",
    )
    path = tmp_path / "cell.json"
    payload = {
        "status": "complete",
        "cache_identity": identity,
        "cell_id": cell,
        "beam_size": 8,
        "candidate_seed": seed_map[cell],
    }
    write_cached_cell(path, payload)
    assert load_cached_cell(path, identity) == payload
    changed = {**identity, "beam_size": 50}
    assert load_cached_cell(path, changed) is None
    assert not path.with_name(path.name + ".partial").exists()


def test_coverage_rejects_seed_or_beam_drift() -> None:
    config = _config()
    rows = [_row("R01_validation_0", "R01")]
    seed_map = candidate_seed_map(rows, config=config, bundle_indices=[0])
    cells = []
    for cell_id, seed in seed_map.items():
        identity = cell_cache_identity(
            campaign_identity_sha256="c",
            stage="screening",
            view="main",
            condition="grn_full",
            delta_sha256="d",
            beam_size=8,
            cell_id=cell_id,
            candidate_seed=seed,
            input_trajectory_checksum="x",
        )
        cells.append(
            {
                "status": "complete",
                "cache_identity": identity,
                "cell_id": cell_id,
                "beam_size": 8,
                "candidate_seed": seed,
            }
        )
    audit = coverage_audit(
        cells,
        expected_cell_ids=sorted(seed_map),
        expected_beam_size=8,
        expected_seed_map=seed_map,
    )
    assert audit["pass"]
    cells[0]["candidate_seed"] += 1
    assert not coverage_audit(
        cells,
        expected_cell_ids=sorted(seed_map),
        expected_beam_size=8,
        expected_seed_map=seed_map,
    )["pass"]


def test_trial_identity_and_launcher_keep_the_firewall_explicit() -> None:
    identity = build_trial_identity(
        condition=TRAINABLE_CONDITIONS[0],
        view=VIEWS[0],
        bundle_indices=[0],
        base_model_state_sha256="base",
        training_corpus_sha256="corpus",
        training_order_sha256="order",
        model_seed=0,
        validation_panel_sha256="panel",
        candidate_seed_map_sha256_value="seeds",
    )
    assert identity["condition"] == "official_continued_full"
    assert identity["view"] == "main"
    with pytest.raises(ValueError, match="unknown Phase 6"):
        build_trial_identity(
            condition=TRAINABLE_CONDITIONS[0],
            view="test",
            bundle_indices=[0],
            base_model_state_sha256="base",
            training_corpus_sha256="corpus",
            training_order_sha256="order",
            model_seed=0,
            validation_panel_sha256="panel",
            candidate_seed_map_sha256_value="seeds",
        )

    launcher = Path("scripts/phases/gpu_run5_phase6.py").read_text(encoding="utf-8")
    assert "glob(" not in launcher
    assert "rglob(" not in launcher
    assert "load_sealed_test" not in launcher
    assert "sealed_test.json" not in launcher
    assert "sealed_family_holdout_test.json" not in launcher
    assert launcher.index('write_json(out / "hyperparameter_freeze.json"') < launcher.index(
        "_odebench_path_check(config)"
    )


def test_cached_cell_rejects_noncomplete_payload(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="only complete"):
        write_cached_cell(
            tmp_path / "bad.json",
            {"status": "running", "cache_identity": {"cell_id": "x"}},
        )
    malformed = tmp_path / "malformed.json"
    malformed.write_text(json.dumps({"status": "complete"}), encoding="utf-8")
    assert load_cached_cell(malformed, {"cell_id": "x"}) is None
