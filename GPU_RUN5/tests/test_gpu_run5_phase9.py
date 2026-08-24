from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from gpu_run5.phase9 import (  # noqa: E402
    ArtifactError,
    Catalog,
    cross_run_synthesis,
    evaluate_preregistration,
    formula_examples,
    sha256_file,
    strict_json,
)


def _write(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, allow_nan=False) + "\n", encoding="utf-8")


def _phase(run: Path, phase: int, artifacts: dict[str, object], **manifest_fields) -> None:
    directory = run / f"phase{phase}"
    hashes = {}
    for name, value in artifacts.items():
        _write(directory / name, value)
        hashes[name] = sha256_file(directory / name)
    _write(
        directory / "manifest.json",
        {
            "campaign": "GPU_RUN5",
            "phase": phase,
            "status": "complete",
            "artifact_sha256": hashes,
            **manifest_fields,
        },
    )


def _preregistration() -> dict:
    return {
        "predictions": {
            "P3": {"metric": "exact", "operator": "<", "threshold": 0.05},
            "P4": {
                "metric": "recon_and_P3",
                "operator": "and",
                "clauses": [
                    {"metric": "recon", "operator": ">=", "threshold": 0.85},
                    {"prediction": "P3", "operator": "is", "threshold": True},
                ],
            },
            "P5": {"metric": "rho", "operator": "<=", "threshold": 0.5},
            "P6": {"metric": "ci_upper", "operator": "<", "threshold": 0.0},
            "P7": {"metric": "formula_and_forgetting", "operator": "and", "clauses": []},
        },
        "retrospective_hypotheses": {
            "R4": {"metric": "denominator_rate", "operator": ">=", "threshold": 0.05},
            "R5": {"metric": "exact_count", "operator": "==", "threshold": 0, "n_cells": 56},
        },
    }


def _base_run(tmp_path: Path, *, final: bool) -> Path:
    run = tmp_path / "run"
    _phase(run, 0, {"preregistration.json": _preregistration()})
    _phase(
        run,
        1,
        {
            "decoded_support.json": {
                "candidate_variable_denominator_rate": 0.12,
                "variable_denominator_selected_exponent_exact_count": 0,
                "variable_denominator_cell_count": 56,
                "variable_denominator_group_true_exponent_skeleton_in_beam_count": 1,
            }
        },
    )
    _phase(
        run,
        3,
        {
            "p6_validation.json": {
                "mean_clustered_difference": -0.2,
                "student_t_95_ci": [-0.3, -0.1],
                "ci95_upper": -0.1,
                "n_system_clusters": 80,
                "paired_cell_differences": [],
            },
            "summary.json": {"status": "complete", "n_cells": 960},
            "failure_funnel.json": {"generation_failure": 2},
        },
    )
    _phase(
        run,
        5,
        {
            "p5.json": {"rho": 0.2, "p_value_two_sided": 0.4, "n_layers": 16, "determinate": True},
            "summary.json": {"status": "complete", "main_causal_top3": ["decoder_1"]},
            "failure_funnel.json": {"decode_failure": 3},
        },
    )
    if final:
        summaries = {
            "main": {
                "frozen": {
                    "component_exponent_aware_skeleton_exact_rate": 0.01,
                    "reconstruction_r2_median": 0.9,
                    "formula_score_vector_without_ce": [0.01, -0.5, 0.8],
                },
                "grn_top3": {"formula_score_vector_without_ce": [0.2, -0.3, 0.9]},
                "grn_full": {"formula_score_vector_without_ce": [0.1, -0.2, 0.95]},
            }
        }
        _phase(
            run,
            8,
            {
                "final_result.json": {"status": "complete", "test_accessed": True, "test_open_event_id": "event-1", "summaries": summaries},
                "preregistered_test_outcomes.json": {
                    "schema_version": "gpu_run5_phase8_preregistered_test_outcomes_v1",
                    "test_accessed": True,
                    "test_open_event_id": "event-1",
                    "P3": {"value": 0.01, "supported": True, "outcome": "hit"},
                    "P4": {"reconstruction_r2_median": 0.9, "supported": True, "outcome": "hit"},
                    "P7": {
                        "grn_top3_formula_score": [0.2, -0.3, 0.9],
                        "grn_full_formula_score": [0.1, -0.2, 0.95],
                        "odebench_grn_top3_drop_from_frozen": 0.02,
                        "odebench_grn_full_drop_from_frozen": 0.1,
                        "supported": True, "outcome": "hit",
                    },
                },
                "odebench_forgetting_summary.json": {
                    "frozen": {
                        "exponent_aware_skeleton_exact_system_then_seed_macro": 0.2,
                        "paired_exponent_aware_skeleton_drop_from_frozen_system_then_seed_macro": 0.0,
                        "paired_cell_identity_matches_frozen": True,
                    },
                    "grn_top3": {
                        "exponent_aware_skeleton_exact_system_then_seed_macro": 0.18,
                        "paired_exponent_aware_skeleton_drop_from_frozen_system_then_seed_macro": 0.02,
                        "paired_cell_identity_matches_frozen": True,
                    },
                    "grn_full": {
                        "exponent_aware_skeleton_exact_system_then_seed_macro": 0.1,
                        "paired_exponent_aware_skeleton_drop_from_frozen_system_then_seed_macro": 0.1,
                        "paired_cell_identity_matches_frozen": True,
                    },
                },
                "odebench_forgetting_audit.json": {"pass": True},
            },
            substage="final-test",
            test_open_count=1,
            test_open_event_id="event-1",
        )
    return run


def test_strict_json_rejects_nonfinite(tmp_path: Path) -> None:
    path = tmp_path / "bad.json"
    path.write_text('{"value": NaN}', encoding="utf-8")
    with pytest.raises(ValueError, match="non-finite"):
        strict_json(path)


def test_catalog_rejects_hash_drift(tmp_path: Path) -> None:
    run = _base_run(tmp_path, final=False)
    path = run / "phase1" / "decoded_support.json"
    path.write_text("{}\n", encoding="utf-8")
    with pytest.raises(ArtifactError, match="hash mismatch"):
        Catalog(run).artifact(1, "decoded_support.json", required=True)


def test_all_registered_outcomes_are_machine_evaluated(tmp_path: Path) -> None:
    run = _base_run(tmp_path, final=True)
    payload = evaluate_preregistration(Catalog(run))
    assert [row["id"] for row in payload["outcomes"]] == ["P3", "P4", "P5", "P6", "P7", "R4", "R5"]
    assert payload["counts"] == {"hit": 7, "miss": 0, "undecidable": 0}
    assert payload["test_firewall"]["sealed_test_files_read_by_phase9"] is False
    p7 = next(row for row in payload["outcomes"] if row["id"] == "P7")
    assert p7["observed"]["grn_top3_formula_better_than_grn_full"] is True
    assert p7["observed"]["grn_top3_forgetting_less_than_grn_full"] is True


def test_unopened_test_remains_undecidable(tmp_path: Path) -> None:
    run = _base_run(tmp_path, final=False)
    payload = evaluate_preregistration(Catalog(run))
    outcomes = {row["id"]: row["outcome"] for row in payload["outcomes"]}
    assert outcomes == {
        "P3": "undecidable", "P4": "undecidable", "P5": "hit", "P6": "hit",
        "P7": "undecidable", "R4": "hit", "R5": "hit",
    }


def test_formula_examples_keep_truth_predictions_mapping_and_failures(tmp_path: Path) -> None:
    run = _base_run(tmp_path, final=False)
    _phase(
        run,
        2,
        {"validation.json": [{"system_id": "s1", "teacher_infix": "x_0", "variable_to_gene": {"x_0": "g0"}}]},
    )
    records = [
        {
            "cell_id": "a", "system_id": "s1", "family": "R01", "selection_rule": "multi_ic_complexity",
            "candidate_formula_raw": "x_0", "candidate_formula_canonical": "x_0", "valid": True,
            "failure_reason": None, "exponent_aware_skeleton_exact": 1.0,
            "normalized_variable_aware_ted": 0.0, "trajectory_metrics": {"input_r2": [1.0], "generalization_r2": [1.0]},
        },
        {
            "cell_id": "b", "system_id": "s1", "family": "R01", "selection_rule": "multi_ic_complexity",
            "candidate_formula_raw": None, "candidate_formula_canonical": None, "valid": False,
            "failure_reason": "parse_error", "exponent_aware_skeleton_exact": 0.0,
            "normalized_variable_aware_ted": 1.0, "trajectory_metrics": {},
        },
    ]
    # Replace Phase 3 with a manifest that signs both the prior summary inputs and selected records.
    p3 = run / "phase3"
    existing = {name: strict_json(path) for name in ("p6_validation.json", "summary.json", "failure_funnel.json") if (path := p3 / name).is_file()}
    existing["selected.json"] = records
    _phase(run, 3, existing)
    rows = formula_examples(Catalog(run))
    assert {row["category"] for row in rows} == {"success", "generation_or_evaluation_failure"}
    assert rows[0]["true_formula"] == "x_0"
    assert rows[0]["variable_to_gene"] == {"x_0": "g0"}
    assert rows[1]["failure_reason"] == "parse_error"


def test_cross_run_missing_sources_are_explicit(tmp_path: Path) -> None:
    run = _base_run(tmp_path, final=False)
    payload = cross_run_synthesis(tmp_path, Catalog(run))
    assert len(payload["rows"]) == 4
    assert all(row["status"] == "unavailable" for row in payload["rows"])
    assert "never compared" in payload["comparison_policy"]


def test_phase9_entrypoint_writes_reports_tables_figures_and_manifest(tmp_path: Path) -> None:
    run = _base_run(tmp_path, final=False)
    reports = tmp_path / "reports"
    graphs = tmp_path / "graphs"
    proc = subprocess.run(
        [
            sys.executable, str(ROOT / "scripts" / "phases" / "gpu_run5_phase9.py"),
            "--run-id", "unit", "--run-dir", str(run), "--repo-root", str(tmp_path),
            "--reports-dir", str(reports), "--graphs-dir", str(graphs),
        ],
        cwd=ROOT, text=True, capture_output=True,
    )
    assert proc.returncode == 0, proc.stderr
    manifest = strict_json(run / "phase9" / "manifest.json")
    assert manifest["status"] == "complete"
    assert manifest["campaign_terminal_state"] == "reported_with_sealed_or_missing_final_test"
    assert all(manifest["go_conditions"].values())
    assert len(list(reports.glob("GPU_RUN5_*report.md"))) == 4
    assert (reports / "GPU_RUN5_cross_model_synthesis.md").is_file()
    assert len(list((graphs / "figures").glob("*.svg"))) == 10
    assert len(list((graphs / "tables").glob("*.csv"))) == 6
