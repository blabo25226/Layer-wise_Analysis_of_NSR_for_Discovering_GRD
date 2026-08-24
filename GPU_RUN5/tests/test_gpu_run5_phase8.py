from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

import gpu_run5.phase8_runtime as phase8_runtime
from gpu_run5.phase8 import (
    FINAL_CONDITIONS,
    VIEWS,
    acquire_test_open_lock,
    audit_go7,
    bind_test_artifact_hashes,
    build_final_freeze,
    claim_test_open,
    complete_test_open,
    evaluate_go6,
    evaluate_preregistered_test_outcomes,
    expected_layer_sets,
    expected_phase8_final_counts,
    expected_phase8_validation_counts,
    phase8_cell_identity,
    selective_conditions,
    validate_selection_contracts,
)
from gpu_run5.phase8_runtime import (
    audit_decode_cell,
    candidate_set_sha256,
    odebench_instantiated_exponent_aware_exact,
)
from gpu_run5.training import OFFICIAL_LAYER_REGISTRY
from scripts.phases.gpu_run5_phase8 import _complete_manifest


def _layer_freeze() -> dict:
    random3 = {
        f"random3_{index}": list(OFFICIAL_LAYER_REGISTRY[index : index + 3])
        for index in range(5)
    }
    return {
        "test_accessed": False,
        "views": {
            view: {
                "top1": ["decoder_0"],
                "top3": ["decoder_0", "decoder_1", "decoder_2"],
                "causal_top3": ["decoder_3", "decoder_4", "decoder_5"],
                "bottom3": ["encoder_0", "encoder_1", "encoder_2"],
                "random3": random3,
            }
            for view in VIEWS
        },
    }


def _selections() -> dict:
    return {
        "main": {
            "selection_rule": "multi_ic_complexity",
            "complexity_lambda": 0.01,
            "source_split": "validation",
            "allowed_families": [f"R{index:02d}" for index in range(1, 9)],
            "source_artifact_sha256": "a" * 64,
        },
        "family_holdout": {
            "selection_rule": "multi_ic_complexity",
            "complexity_lambda": 0.001,
            "source_split": "family_holdout_validation_R06_only",
            "allowed_families": ["R06"],
            "source_artifact_sha256": "b" * 64,
            "selection_artifact_signature_sha256": "c" * 64,
        },
    }


def _checkpoint_registry() -> dict:
    return {
        view: {
            condition: {
                str(bundle): {
                    "view": view,
                    "condition": condition,
                    "bundle_index": bundle,
                    "path": f"{view}/{condition}/{bundle}.pt",
                    "file_sha256": f"{1 + bundle:064x}",
                    "checkpoint_sha256": f"{11 + bundle:064x}",
                }
                for bundle in range(3)
            }
            for condition in FINAL_CONDITIONS
        }
        for view in VIEWS
    }


def test_exact_layer_and_selection_adapters_keep_views_separate() -> None:
    layers = expected_layer_sets(_layer_freeze())
    assert set(layers) == set(VIEWS)
    assert tuple(layers["main"]) == selective_conditions(5)
    selections = validate_selection_contracts(_selections())
    assert selections["family_holdout"]["allowed_families"] == ["R06"]

    leaked = _selections()
    leaked["family_holdout"] = dict(leaked["family_holdout"])
    leaked["family_holdout"]["allowed_families"] = ["R06", "R07"]
    with pytest.raises(ValueError, match="family scope"):
        validate_selection_contracts(leaked)
    shared = _selections()
    shared["family_holdout"] = dict(shared["family_holdout"])
    shared["family_holdout"]["source_artifact_sha256"] = "a" * 64
    with pytest.raises(ValueError, match="distinct"):
        validate_selection_contracts(shared)


def test_exact_full_phase8_budgets() -> None:
    validation = expected_phase8_validation_counts(
        screen_systems={"main": 24, "family_holdout": 10},
        confirmation_systems={"main": 80, "family_holdout": 10},
        n_grid_candidates=9,
        n_bundles=3,
        n_corruptions=4,
    )
    assert validation == {
        "selective_conditions": 9,
        "grid_trials": 162,
        "selected_training_trials": 54,
        "screening_cells": {"main": 7776, "family_holdout": 3240},
        "confirmation_cells": {"main": 8640, "family_holdout": 1080},
        "screening_cells_total": 11016,
        "confirmation_cells_total": 9720,
        "all_decode_cells_total": 20736,
    }
    assert expected_phase8_final_counts(
        main_systems=80, holdout_systems=20, n_bundles=3, n_corruptions=4
    ) == {
        "conditions": 5,
        "cells": {"main": 4800, "family_holdout": 1200},
        "cells_total": 6000,
    }


def test_go6_uses_strict_lexicographic_formula_score() -> None:
    scores = {
        "frozen": [0.10, -0.50, 0.80, -1.0],
        "grn_top3": [0.20, -0.90, 0.10, -9.0],
        "grn_random3_0": [0.19, -0.10, 1.00, -0.1],
        "grn_random3_1": [0.18, -0.10, 1.00, -0.1],
        "grn_random3_2": [0.17, -0.10, 1.00, -0.1],
        "grn_random3_3": [0.21, -0.10, 1.00, -0.1],
        "grn_random3_4": [0.22, -0.10, 1.00, -0.1],
    }
    result = evaluate_go6(scores)
    assert result["pass"]
    assert result["n_random_sets_beaten"] == 3
    scores["grn_top3"] = list(scores["frozen"])
    assert not evaluate_go6(scores)["pass"]


def test_final_freeze_and_go7_require_exact_five_conditions() -> None:
    layer_sets = expected_layer_sets(_layer_freeze())
    freeze = build_final_freeze(
        checkpoint_registry=_checkpoint_registry(),
        layer_sets=layer_sets,
        candidate_selection=validate_selection_contracts(_selections()),
        upstream_manifest_sha256={"phase6": "6" * 64, "phase7": "7" * 64},
        config_fingerprint="c" * 64,
        layer_freeze_sha256="d" * 64,
        validation_freeze_sha256="e" * 64,
    )
    assert freeze["conditions"] == list(FINAL_CONDITIONS)
    assert freeze["views"]["main"] is not freeze["views"]["family_holdout"]
    go6 = {"pass": True, "test_accessed": False}
    go7 = audit_go7(
        freeze,
        go6=go6,
        upstream_test_accessed={"phase2": False, "phase3": False, "phase4": False, "phase5": False, "phase6": False, "phase7": False},
        observed_freeze_sha256=freeze["freeze_sha256"],
    )
    assert go7["pass"]
    for invalid in (
        {"phase2": False},
        {
            "phase2": False,
            "phase3": False,
            "phase4": False,
            "phase5": None,
            "phase6": False,
            "phase7": False,
        },
        {
            "phase2": False,
            "phase3": False,
            "phase4": False,
            "phase5": 0,
            "phase6": False,
            "phase7": False,
        },
    ):
        assert not audit_go7(
            freeze,
            go6=go6,
            upstream_test_accessed=invalid,
            observed_freeze_sha256=freeze["freeze_sha256"],
        )["pass"]

    missing = _checkpoint_registry()
    missing["main"] = dict(missing["main"])
    missing["main"].pop("grn_random3_0")
    with pytest.raises(ValueError, match="condition registry"):
        build_final_freeze(
            checkpoint_registry=missing,
            layer_sets=layer_sets,
            candidate_selection=validate_selection_contracts(_selections()),
            upstream_manifest_sha256={},
            config_fingerprint="c",
            layer_freeze_sha256="d",
            validation_freeze_sha256="e",
        )


def test_complete_upstream_manifest_requires_nonempty_exact_true_go_conditions(
    tmp_path: Path,
) -> None:
    phase = tmp_path / "phase5"
    phase.mkdir()
    manifest = phase / "manifest.json"
    for go_conditions in ({}, {"complete": 1}, {"complete": True, "other": False}):
        manifest.write_text(
            json.dumps({"status": "complete", "go_conditions": go_conditions}),
            encoding="utf-8",
        )
        with pytest.raises(RuntimeError, match="not complete"):
            _complete_manifest(tmp_path, 5)
    manifest.write_text(
        json.dumps({"status": "complete", "go_conditions": {"complete": True}}),
        encoding="utf-8",
    )
    assert _complete_manifest(tmp_path, 5)["status"] == "complete"


def test_final_cell_requires_freeze_and_test_open_event() -> None:
    with pytest.raises(ValueError, match="lacks frozen"):
        phase8_cell_identity(
            campaign_identity_sha256="campaign",
            stage="final_test",
            view="main",
            condition="grn_top3",
            checkpoint_sha256="checkpoint",
            beam_size=50,
            cell_id="cell",
            candidate_seed=1,
            input_trajectory_checksum="input",
            selection_contract_sha256="selection",
        )
    cell = phase8_cell_identity(
        campaign_identity_sha256="campaign",
        stage="final_test",
        view="family_holdout",
        condition="grn_top3",
        checkpoint_sha256="checkpoint",
        beam_size=50,
        cell_id="cell",
        candidate_seed=1,
        input_trajectory_checksum="input",
        selection_contract_sha256="selection",
        final_freeze_sha256="freeze",
        test_open_event_id="event",
    )
    assert cell["view"] == "family_holdout"


def test_test_open_ledger_allows_only_same_identity_resume_then_closes(tmp_path: Path) -> None:
    ledger = tmp_path / "test_open_ledger.json"
    first = claim_test_open(
        ledger,
        freeze_sha256="f" * 64,
        sealed_paths={"main": "phase2/sealed_test.json", "family_holdout": "phase2/sealed_family_holdout_test.json"},
    )
    assert first["open_count"] == 1
    resumed = claim_test_open(
        ledger,
        freeze_sha256="f" * 64,
        sealed_paths={"main": "phase2/sealed_test.json", "family_holdout": "phase2/sealed_family_holdout_test.json"},
    )
    assert resumed["event_id"] == first["event_id"]
    assert resumed["resume_count"] == 1
    with pytest.raises(RuntimeError, match="identity drift"):
        claim_test_open(ledger, freeze_sha256="0" * 64, sealed_paths={"main": "x"})
    bind_test_artifact_hashes(ledger, {"main": "a" * 64, "family_holdout": "b" * 64})
    complete_test_open(ledger, final_artifact_sha256={"final_summary.json": "c" * 64})
    assert json.loads(ledger.read_text())["status"] == "complete"
    with pytest.raises(RuntimeError, match="already completed"):
        claim_test_open(
            ledger,
            freeze_sha256="f" * 64,
            sealed_paths={"main": "phase2/sealed_test.json", "family_holdout": "phase2/sealed_family_holdout_test.json"},
        )


def test_test_open_lock_rejects_a_concurrent_worker(tmp_path: Path) -> None:
    lock = tmp_path / "test_open.lock"
    first = acquire_test_open_lock(lock)
    try:
        with pytest.raises(RuntimeError, match="another Phase 8 final-test"):
            acquire_test_open_lock(lock)
    finally:
        first.close()
    reopened = acquire_test_open_lock(lock)
    reopened.close()


def test_test_open_atomic_create_rejects_a_lost_race(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ledger = tmp_path / "ledger.json"
    ledger.write_text("already won", encoding="utf-8")
    original_exists = Path.exists
    monkeypatch.setattr(
        Path,
        "exists",
        lambda self: False if self == ledger else original_exists(self),
    )
    with pytest.raises(RuntimeError, match="claimed concurrently"):
        claim_test_open(
            ledger,
            freeze_sha256="f" * 64,
            sealed_paths={"main": "sealed"},
        )


def _complete_decode_cell() -> dict:
    identity = {
        "cell_id": "system|b0|n0|r0",
        "stage": "final_test",
        "view": "main",
        "condition": "grn_top3",
        "beam_size": 2,
        "candidate_seed": 17,
        "input_trajectory_checksum": "input-sha",
        "selection_contract_sha256": "selection-sha",
    }
    candidate = {
        "candidate_index": 0,
        "candidate_formula_raw": "x_0",
        "candidate_formula_canonical": "x_0",
        "candidate_formula_skeleton": "x_0",
        "candidate_exponent_aware_skeleton": "x_0",
        "valid": True,
        "failure_reason": None,
        "trajectory_metrics": {
            "input_nrmse": [0.1],
            "selection_nrmse": [0.1, 0.2],
            "input_failures": [None],
            "selection_failures": [None, None],
        },
    }
    return {
        "status": "complete",
        "cache_identity": identity,
        **identity,
        "true_formula": "x_0",
        "true_prefix": "x_0",
        "variable_to_gene": {"x_0": "G0"},
        "candidates": [candidate],
        "selected": candidate,
        "n_candidates": 1,
        "beam_size": 2,
        "candidate_shortfall": 1,
        "candidate_set_hash": candidate_set_sha256(["x_0"]),
        "generation_failure": None,
        "generalization_trajectory_accessed": True,
        "selected_clean_trajectory_metrics": {
            "candidate_selection_finished_before_generalization_access": True,
            "roles": {
                role: [
                    {
                        "role_index": index,
                        "source_checksum": f"{role}-{index}",
                        "nrmse": 0.1,
                        "r2": 0.9,
                        "failure": None,
                    }
                    for index in range(count)
                ]
                for role, count in {"input": 1, "selection": 2, "generalization": 2}.items()
            },
        },
    }


def test_resume_shard_audit_rejects_candidate_and_generalization_drift() -> None:
    valid = _complete_decode_cell()
    assert audit_decode_cell(valid, require_clean_generalization=True)["pass"]
    for mutate in (
        lambda row: row.update(candidate_set_hash="0" * 64),
        lambda row: row["candidates"][0].update(candidate_index=1),
        lambda row: row["selected_clean_trajectory_metrics"]["roles"].pop("generalization"),
        lambda row: row["cache_identity"].update(candidate_seed=18),
        lambda row: row["selected_clean_trajectory_metrics"]["roles"]["input"][0].update(nrmse=None),
    ):
        malformed = deepcopy(valid)
        mutate(malformed)
        assert not audit_decode_cell(
            malformed, require_clean_generalization=True
        )["pass"]


def test_empty_beam_is_a_complete_failure_aware_shard(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        phase8_runtime,
        "observed_selection_trajectories",
        lambda *args, **kwargs: {
            "input": [
                {
                    "times": [0.0, 1.0],
                    "trajectory": [[1.0], [1.0]],
                    "initial_condition": [1.0],
                    "source_checksum": "input-sha",
                }
            ],
            "selection": [],
        },
    )
    monkeypatch.setattr(phase8_runtime, "make_regressor", lambda *args, **kwargs: object())
    monkeypatch.setattr(
        phase8_runtime,
        "fit_and_collect",
        lambda *args, **kwargs: {
            "infixes": [],
            "trees": [],
            "wall_time": 0.01,
        },
    )
    identity = {
        "cell_id": "cell",
        "stage": "validation_confirmation",
        "view": "main",
        "condition": "grn_top3",
        "beam_size": 8,
        "candidate_seed": 1,
        "input_trajectory_checksum": "input-sha",
        "selection_contract_sha256": "selection-sha",
    }
    cell = phase8_runtime.decode_cell(
        {
            "system_id": "system",
            "family": "R01",
            "dimension": 1,
            "teacher_infix": "x_0",
            "teacher_prefix": "x_0",
            "variable_to_gene": {"x_0": "G0"},
        },
        model=object(),
        config={
            "seed_bundles": [{"candidate_seed": 1}],
            "selection": {"trajectory_nrmse_failure_penalty": 10.0},
        },
        selection_contract={
            "selection_rule": "multi_ic_complexity",
            "complexity_lambda": 0.01,
        },
        bundle_index=0,
        sigma=0.0,
        rho=0.0,
        beam_size=8,
        candidate_seed=1,
        cache_identity=identity,
        include_clean_generalization=False,
    )
    assert cell["generation_failure"] == "EmptyCandidateSet"
    assert cell["selected"]["failure_reason"] == "EmptyCandidateSet"
    assert audit_decode_cell(cell, require_clean_generalization=False)["pass"]


def test_preregistered_phase8_outcomes_follow_exact_p3_p4_p7_contract() -> None:
    summaries = {
        "frozen": {
            "formula_score_vector_without_ce": [0.04, -0.8, 0.9],
            "reconstruction_r2_median": 0.86,
        },
        "grn_top3": {"formula_score_vector_without_ce": [0.20, -0.3, 0.9]},
        "grn_full": {"formula_score_vector_without_ce": [0.19, -0.2, 0.95]},
    }
    odebench = {
        "frozen": {
            "exponent_aware_skeleton_exact_system_then_seed_macro": 0.8,
            "paired_exponent_aware_skeleton_drop_from_frozen_system_then_seed_macro": 0.0,
        },
        "grn_top3": {
            "exponent_aware_skeleton_exact_system_then_seed_macro": 0.7,
            "paired_exponent_aware_skeleton_drop_from_frozen_system_then_seed_macro": 0.1,
        },
        "grn_full": {
            "exponent_aware_skeleton_exact_system_then_seed_macro": 0.6,
            "paired_exponent_aware_skeleton_drop_from_frozen_system_then_seed_macro": 0.2,
        },
    }
    result = evaluate_preregistered_test_outcomes(
        main_summaries=summaries,
        odebench_forgetting=odebench,
        test_open_event_id="event",
    )
    assert result["P3"]["supported"]
    assert result["P4"]["supported"]
    assert result["P7"]["supported"]
    assert result["P7"]["odebench_grn_top3_drop_from_frozen"] < result["P7"]["odebench_grn_full_drop_from_frozen"]

    summaries["grn_top3"]["formula_score_vector_without_ce"] = [0.18, -0.3, 0.9]
    assert not evaluate_preregistered_test_outcomes(
        main_summaries=summaries,
        odebench_forgetting=odebench,
        test_open_event_id="event",
    )["P7"]["supported"]


def test_odebench_forgetting_uses_instantiated_truth_not_symbolic_coefficients() -> None:
    instantiated = "(1.0-x_0/2.0)/3.0"
    record = {
        "true_formula_raw": "(c_0-x_0/c_1)/c_2",
        "true_formula_canonical": instantiated,
        "candidate_formula_raw": instantiated,
    }
    assert odebench_instantiated_exponent_aware_exact(record) == 1.0
    missing = dict(record)
    missing["true_formula_canonical"] = ""
    with pytest.raises(ValueError, match="instantiated"):
        odebench_instantiated_exponent_aware_exact(missing)


def test_launcher_has_explicit_validation_and_final_test_stages() -> None:
    source = Path("scripts/phases/gpu_run5_phase8.py").read_text(encoding="utf-8")
    assert 'choices=("validation", "final-test")' in source
    assert "claim_test_open(" in source
    assert "load_sealed_test(" in source
    assert source.index("claim_test_open(") < source.index("load_sealed_test(")
    final_stage = source[source.index("def _final_test_stage") :]
    assert final_stage.index("_preopen_revalidate(") < final_stage.index("sealed_paths =")
    assert final_stage.index("claim_test_open(") < final_stage.index("sha256_file(Path(path))")
    assert "glob(" not in source
    assert "rglob(" not in source
