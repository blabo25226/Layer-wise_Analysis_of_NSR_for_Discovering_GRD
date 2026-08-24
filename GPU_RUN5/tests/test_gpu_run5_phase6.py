from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from gpu_run2_runtime import fingerprint_json
from gpu_run5.phase6 import (
    TRAINABLE_CONDITIONS,
    VIEWS,
    audit_data_views,
    build_holdout_selection_artifact,
    build_trial_identity,
    candidate_seed_map,
    candidate_seed_map_sha256,
    cell_cache_identity,
    coverage_audit,
    expected_phase6_counts,
    freeze_phase3_selection,
    hyperparameter_grid,
    load_cached_cell,
    phase3_cell_filename,
    validation_cell_id,
    verify_holdout_selection_artifact,
    write_cached_cell,
)
from scripts.phases.gpu_run5_phase6 import write_json as phase6_write_json


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


def _phase3_cell(cell_id: str, *, family: str = "R06") -> dict:
    candidates = [
        {
            "candidate_index": 0,
            "candidate_formula_raw": "x_0",
            "complexity": 100,
            "trajectory_metrics": {
                "input_nrmse": [0.0],
                "selection_nrmse": [0.0],
                "input_failures": [None],
                "selection_failures": [None],
            },
            "component_exponent_aware_skeleton_exact": [0.0],
            "component_normalized_variable_aware_ted": [1.0],
            "component_valid": [True],
        },
        {
            "candidate_index": 1,
            "candidate_formula_raw": "x_0 + 1",
            "complexity": 1,
            "trajectory_metrics": {
                "input_nrmse": [0.5],
                "selection_nrmse": [0.5],
                "input_failures": [None],
                "selection_failures": [None],
            },
            "component_exponent_aware_skeleton_exact": [1.0],
            "component_normalized_variable_aware_ted": [0.0],
            "component_valid": [True],
        },
    ]
    raw = [row["candidate_formula_raw"] for row in candidates]
    return {
        "status": "complete",
        "cell_id": cell_id,
        "system_id": "R06_validation_0" if family == "R06" else "R07_validation_0",
        "family": family,
        "dimension": 1,
        "bundle_index": 0,
        "candidate_set_hash": hashlib.sha256(
            json.dumps(raw, ensure_ascii=True, separators=(",", ":")).encode()
        ).hexdigest(),
        "n_candidates": len(candidates),
        "cache_identity": {
            "schema_version": "phase3",
            "git_commit": "old",
            "git_status_short": "",
            "config_fingerprint": "config",
            "checkpoint_sha256": "checkpoint",
            "beam_size": 50,
            "beam_temperature": 0.1,
            "beam_type": "sampling",
            "rescale": True,
            "failure_penalty": 10.0,
            "candidate_seed_namespace": "paired",
            "device": "cuda",
            "environment_fingerprint": "environment",
        },
        "candidates": candidates,
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


def test_phase3_multi_ic_complexity_freeze_rejects_drift() -> None:
    payload = {
        "chosen_lambda": 0.01,
        "split": "validation",
        "audit": [
            {"lambda": 0.0},
            {"lambda": 0.0001},
            {"lambda": 0.001},
            {"lambda": 0.01},
        ],
    }
    assert freeze_phase3_selection(payload) == {
        "selection_rule": "multi_ic_complexity",
        "complexity_lambda": 0.01,
        "source_split": "validation",
        "candidate_lambdas": [0.0, 0.0001, 0.001, 0.01],
    }
    with pytest.raises(ValueError, match="chosen lambda changed"):
        freeze_phase3_selection({**payload, "chosen_lambda": 0.001})
    with pytest.raises(ValueError, match="not selected on validation"):
        freeze_phase3_selection({**payload, "split": "test"})
    with pytest.raises(ValueError, match="duplicates"):
        freeze_phase3_selection(
            {**payload, "audit": [{"lambda": 0.01}, {"lambda": 0.01}]}
        )
    with pytest.raises(ValueError, match="non-finite"):
        freeze_phase3_selection(
            {**payload, "audit": [{"lambda": 0.01}, {"lambda": float("nan")}]}
        )


def test_R06_selection_uses_explicit_shards_and_rejects_other_families(
    tmp_path: Path,
) -> None:
    cell_id = "R06_validation_0_b0_n0_r0"
    cells_dir = tmp_path / "phase3" / "cells"
    cells_dir.mkdir(parents=True)
    r06_path = cells_dir / f"{cell_id}.json"
    r06_path.write_text(json.dumps(_phase3_cell(cell_id)), encoding="utf-8")
    r07_path = cells_dir / "R07_validation_0_b0_n0_r0.json"
    r07_path.write_text(
        json.dumps(_phase3_cell("R07_validation_0_b0_n0_r0", family="R07")),
        encoding="utf-8",
    )
    r08_path = cells_dir / "R08_validation_0_b0_n0_r0.json"
    r08_path.write_text(
        json.dumps(_phase3_cell("R08_validation_0_b0_n0_r0", family="R08")),
        encoding="utf-8",
    )
    kwargs = {
        "cell_sources": [(f"phase3/cells/{r06_path.name}", r06_path)],
        "expected_cell_ids": [cell_id],
        "expected_system_ids": ["R06_validation_0"],
        "candidate_lambdas": [0.0, 0.01],
        "failure_penalty": 10.0,
        "source_phase2_manifest_sha256": "phase2",
        "source_phase3_config_snapshot_sha256": "phase3-config",
        "source_holdout_validation_sha256": "validation",
        "config_fingerprint": "config",
        "git_provenance": {"commit": "abc", "status_short": ""},
        "expected_beam_size": 50,
        "expected_checkpoint_sha256": "checkpoint",
    }
    artifact = build_holdout_selection_artifact(**kwargs)
    assert artifact["chosen_lambda"] == 0.01
    assert artifact["source_family"] == "R06"
    assert artifact["source_cell_count"] == 1
    assert artifact["source_artifacts"][0]["path"] == f"phase3/cells/{r06_path.name}"
    protocol = verify_holdout_selection_artifact(
        artifact,
        expected_cell_ids=[cell_id],
        expected_system_ids=["R06_validation_0"],
        expected_phase2_manifest_sha256="phase2",
        expected_phase3_config_snapshot_sha256="phase3-config",
        expected_holdout_validation_sha256="validation",
        source_root=tmp_path,
    )
    assert protocol["complexity_lambda"] == 0.01

    bad_candidate_hash = _phase3_cell(cell_id)
    bad_candidate_hash["candidate_set_hash"] = "0" * 64
    r06_path.write_text(json.dumps(bad_candidate_hash), encoding="utf-8")
    with pytest.raises(ValueError, match="candidate-set hash mismatch"):
        build_holdout_selection_artifact(**kwargs)
    r06_path.write_text(json.dumps(_phase3_cell(cell_id)), encoding="utf-8")

    # Unlisted R07/R08 shards in the same directory cannot influence the signed result.
    assert build_holdout_selection_artifact(**kwargs)["signature_sha256"] == artifact[
        "signature_sha256"
    ]
    with pytest.raises(ValueError, match="non-R06"):
        build_holdout_selection_artifact(
            **{
                **kwargs,
                "cell_sources": [
                    *kwargs["cell_sources"],
                    (f"phase3/cells/{r07_path.name}", r07_path),
                ],
            }
        )
    with pytest.raises(ValueError, match="non-R06"):
        build_holdout_selection_artifact(
            **{
                **kwargs,
                "cell_sources": [
                    *kwargs["cell_sources"],
                    (f"phase3/cells/{r08_path.name}", r08_path),
                ],
            }
        )
    tampered = {**artifact, "chosen_lambda": 0.0}
    with pytest.raises(ValueError, match="signature mismatch"):
        verify_holdout_selection_artifact(
            tampered,
            expected_cell_ids=[cell_id],
            expected_system_ids=["R06_validation_0"],
            expected_phase2_manifest_sha256="phase2",
            expected_phase3_config_snapshot_sha256="phase3-config",
            expected_holdout_validation_sha256="validation",
            source_root=tmp_path,
        )
    forged_path = json.loads(json.dumps(artifact))
    forged_path["source_artifacts"][0]["path"] = (
        "phase3/cells/R06_validation_0_b0_n0_r0_extra.json"
    )
    forged_path["source_artifact_index_sha256"] = fingerprint_json(
        forged_path["source_artifacts"]
    )
    forged_path["source_path_sha256_index_sha256"] = fingerprint_json(
        [
            {"path": row["path"], "sha256": row["sha256"]}
            for row in forged_path["source_artifacts"]
        ]
    )
    forged_path["source_filename_sha256_index_sha256"] = fingerprint_json(
        [
            {"path": Path(row["path"]).name, "sha256": row["sha256"]}
            for row in forged_path["source_artifacts"]
        ]
    )
    unsigned = {key: value for key, value in forged_path.items() if key != "signature_sha256"}
    forged_path["signature_sha256"] = fingerprint_json(unsigned)
    with pytest.raises(ValueError, match="paths are not the exact allowlist"):
        verify_holdout_selection_artifact(
            forged_path,
            expected_cell_ids=[cell_id],
            expected_system_ids=["R06_validation_0"],
            expected_phase2_manifest_sha256="phase2",
            expected_phase3_config_snapshot_sha256="phase3-config",
            expected_holdout_validation_sha256="validation",
            source_root=tmp_path,
        )
    r06_path.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="source hash mismatch"):
        verify_holdout_selection_artifact(
            artifact,
            expected_cell_ids=[cell_id],
            expected_system_ids=["R06_validation_0"],
            expected_phase2_manifest_sha256="phase2",
            expected_phase3_config_snapshot_sha256="phase3-config",
            expected_holdout_validation_sha256="validation",
            source_root=tmp_path,
        )


def test_phase3_cell_filename_is_exact_and_has_no_family_discovery() -> None:
    assert phase3_cell_filename(
        system="R06_validation_0",
        bundle_index=2,
        noise_sigma=0.05,
        subsample_rho=0.5,
    ) == "R06_validation_0_b2_n0p05_r0p5.json"


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
        candidate_selection_sha256="selection-main",
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
            candidate_selection_sha256="selection-main",
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
    assert '"phase3_lambda_selection": root / "phase3" / "lambda_selection.json"' in launcher
    assert '"candidate_selection_by_view": selection_protocols' in launcher
    assert '"trajectory_selection_roles": ["input", "selection"]' in launcher
    assert '"generalization_used_for_selection": False' in launcher
    assert '"variable_to_gene": dict(row.get("variable_to_gene") or {})' in launcher
    assert "manifest_payload = sanitize_nonfinite(" in launcher
    assert "load_delta_checkpoint(" in launcher
    assert "apply_delta_checkpoint(" in launcher
    assert "view_campaign_sha256[view]" in launcher
    assert launcher.index('write_json(out / "hyperparameter_freeze.json"') < launcher.index(
        "_odebench_path_check(config)"
    )

    prestage = Path(
        "scripts/phases/gpu_run5_phase6_holdout_prestage.py"
    ).read_text(encoding="utf-8")
    assert "glob(" not in prestage
    assert "rglob(" not in prestage
    assert '"phase3" / "manifest.json"' not in prestage
    assert "all_candidates.json" not in prestage
    assert "selected.json" not in prestage
    assert "lambda_selection.json" not in prestage
    assert "load_config" not in prestage
    assert "run_dir(" not in prestage
    assert 'expected_family = "R06"' in prestage


def test_cached_cell_rejects_noncomplete_payload(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="only complete"):
        write_cached_cell(
            tmp_path / "bad.json",
            {"status": "running", "cache_identity": {"cell_id": "x"}},
        )
    malformed = tmp_path / "malformed.json"
    malformed.write_text(json.dumps({"status": "complete"}), encoding="utf-8")
    assert load_cached_cell(malformed, {"cell_id": "x"}) is None


def test_phase6_json_writer_never_persists_nonfinite_constants(tmp_path: Path) -> None:
    path = tmp_path / "strict.json"
    phase6_write_json(
        path,
        {"failed_score": -float("inf"), "nan": float("nan"), "status": "failed"},
    )
    raw = path.read_text(encoding="utf-8")
    assert "Infinity" not in raw
    assert "NaN" not in raw
    assert json.loads(raw) == {"failed_score": None, "nan": None, "status": "failed"}
