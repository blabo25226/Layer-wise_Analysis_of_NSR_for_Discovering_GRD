from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

EXPECTED_LAYERS = [
    *(f"encoder_{index}" for index in range(4)),
    *(f"decoder_{index}" for index in range(12)),
]

from gpu_run5.phase9 import (  # noqa: E402
    ArtifactError,
    Catalog,
    aggregate_results,
    campaign_terminal_state,
    condition_uncertainty,
    cross_run_synthesis,
    evaluate_preregistration,
    failure_rows,
    failure_analysis,
    formula_examples,
    render_reports,
    sha256_file,
    strict_json,
    write_figures,
    _svg,
)
from scripts.phases.gpu_run5_phase9 import (  # noqa: E402
    _git,
    _git_changes_are_generated_only,
    _gpu_run5_source_audit_pass,
    _write_graph_provenance,
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


def _indexed_cells(
    run: Path,
    phase: int,
    index_name: str,
    cells: list[dict],
    artifacts: dict[str, object],
    **manifest_fields,
) -> None:
    directory = run / f"phase{phase}"
    index = []
    for position, cell in enumerate(cells):
        relative = f"cells/cell_{position}.json"
        path = directory / relative
        _write(path, cell)
        index.append({
            "path": relative,
            "sha256": sha256_file(path),
            "bytes": path.stat().st_size,
        })
    _phase(run, phase, {**artifacts, index_name: index}, **manifest_fields)


def _cell(
    bundle: int,
    *,
    condition: str = "grn_top3",
    failure: bool = False,
    stage: str = "final_test",
) -> dict:
    selected = {
        "candidate_index": 0,
        "candidate_formula_raw": "x_0",
        "candidate_formula_canonical": "x_0",
        "component_exponent_aware_skeleton_exact": [0.0 if failure else 1.0],
        "component_normalized_variable_aware_ted": [1.0 if failure else 0.0],
        "component_valid": [not failure],
        "component_failure_reason": ["ParseError" if failure else None],
        "formula_metrics_evaluated": not failure,
        "failure_reason": "ParseError" if failure else None,
        "generation_failure": "CellEvaluationTimeout" if failure else None,
        "structure": {"failure_reason": "TEDParseError" if failure else None},
        "trajectory_metrics": {
            "input_failures": ["TrajectoryIntegrationTimeout"] if failure else [None],
        },
    }
    return {
        "cell_id": f"{condition}|b{bundle}",
        "stage": stage,
        "view": "main",
        "condition": condition,
        "system_id": f"s{bundle}",
        "family": "R01",
        "dimension": 1,
        "bundle_index": bundle,
        "beam_size": 2,
        "n_candidates": 1,
        "cell_evaluation_timeout_triggered": failure,
        "true_formula": "x_0",
        "variable_to_gene": {"x_0": "g0"},
        "selected": selected,
        "selected_clean_trajectory_metrics": {
            "roles": {
                "generalization": [
                    {"nrmse": 1.0 if failure else 0.1, "failure": "IntegrationTimeout" if failure else None},
                    {"nrmse": 1.0 if failure else 0.1, "failure": "IntegrationTimeout" if failure else None},
                ]
            }
        } if stage == "final_test" else None,
        "candidates": [selected],
    }


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
    paired = [
        {"system_id": f"s{index % 80:02d}", "paired_index": index}
        for index in range(960)
    ]
    _phase(
        run,
        1,
        {
            "decoded_support.json": {
                "candidate_count": 100,
                "selected_count": 20,
                "candidate_variable_denominator_rate": 0.12,
                "all_group_true_exponent_skeleton_in_beam_rate": 0.1,
                "variable_denominator_selected_exponent_exact_count": 0,
                "variable_denominator_cell_count": 56,
                "variable_denominator_group_true_exponent_skeleton_in_beam_count": 1,
                "variable_denominator_group_count": 56,
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
                "n_cells": 960,
                "n_system_clusters": 80,
                "prediction_P6": "supported",
                "paired_cell_differences": paired,
            },
            "summary.json": {"status": "complete", "n_cells": 960},
            "failure_funnel.json": {"generation_failure": 2},
        },
    )
    _phase(
        run,
        5,
        {
            "p5.json": {
                "rho": 0.2, "p_value_two_sided": 0.4, "n_layers": 16,
                "expected_layer_count": 16, "layers": EXPECTED_LAYERS,
                "determinate": True, "supported": True,
            },
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
        phase8_artifacts = {
                "final_result.json": {
                    "status": "complete", "test_accessed": True,
                    "test_open_event_id": "event-1", "test_open_count": 1,
                    "summaries": summaries,
                },
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
        }
        for name, value in phase8_artifacts.items():
            _write(run / "phase8" / name, value)
        final_hashes = {
            name: sha256_file(run / "phase8" / name)
            for name in phase8_artifacts
        }
        sealed_hashes = {"main": "a" * 64, "family_holdout": "b" * 64}
        phase8_artifacts["test_open_ledger.json"] = {
            "schema_version": "gpu_run5_phase8_test_open_ledger_v1",
            "event_id": "event-1", "status": "complete", "open_count": 1,
            "sealed_paths": {"main": "/sealed/main", "family_holdout": "/sealed/holdout"},
            "sealed_artifact_sha256": sealed_hashes,
            "final_artifact_sha256": final_hashes,
        }
        _phase(
            run,
            8,
            phase8_artifacts,
            substage="final-test",
            test_open_count=1,
            test_open_event_id="event-1",
            sealed_artifact_sha256=sealed_hashes,
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


def test_catalog_rejects_manifest_advertised_artifact_deletion(tmp_path: Path) -> None:
    run = _base_run(tmp_path, final=False)
    (run / "phase1" / "decoded_support.json").unlink()
    with pytest.raises(ArtifactError, match="signed by the manifest but missing"):
        Catalog(run).artifact(1, "decoded_support.json")


def test_catalog_rejects_existing_unsigned_artifact(tmp_path: Path) -> None:
    run = _base_run(tmp_path, final=False)
    _write(run / "phase1" / "unexpected.json", {"value": 1})
    with pytest.raises(ArtifactError, match="without a signed manifest hash"):
        Catalog(run).artifact(1, "unexpected.json")


def test_catalog_rejects_orphan_artifact_without_producer_manifest(tmp_path: Path) -> None:
    run = _base_run(tmp_path, final=False)
    _write(run / "phase2" / "orphan.json", {"value": 1})
    with pytest.raises(ArtifactError, match="without a producer manifest"):
        Catalog(run).artifact(2, "orphan.json")


def test_all_registered_outcomes_are_machine_evaluated(tmp_path: Path) -> None:
    run = _base_run(tmp_path, final=True)
    payload = evaluate_preregistration(Catalog(run))
    assert [row["id"] for row in payload["outcomes"]] == ["P3", "P4", "P5", "P6", "P7", "R4", "R5"]
    assert payload["counts"] == {"hit": 7, "miss": 0, "undecidable": 0}
    assert payload["test_firewall"]["sealed_test_files_read_by_phase9"] is False
    assert payload["test_firewall"]["phase8_test_open_ledger"]["pass"] is True
    p7 = next(row for row in payload["outcomes"] if row["id"] == "P7")
    assert p7["observed"]["grn_top3_formula_better_than_grn_full"] is True
    assert p7["observed"]["grn_top3_forgetting_less_than_grn_full"] is True


def test_invalid_signed_phase8_ledger_keeps_final_outcomes_undecidable(tmp_path: Path) -> None:
    run = _base_run(tmp_path, final=True)
    phase8 = run / "phase8"
    ledger = strict_json(phase8 / "test_open_ledger.json")
    ledger["event_id"] = "different-event"
    artifacts = {
        path.name: strict_json(path)
        for path in phase8.glob("*.json")
        if path.name != "manifest.json"
    }
    artifacts["test_open_ledger.json"] = ledger
    _phase(
        run, 8, artifacts,
        substage="final-test", test_open_count=1, test_open_event_id="event-1",
        sealed_artifact_sha256=ledger["sealed_artifact_sha256"],
    )
    payload = evaluate_preregistration(Catalog(run))
    outcomes = {row["id"]: row["outcome"] for row in payload["outcomes"]}
    assert all(outcomes[key] == "undecidable" for key in ("P3", "P4", "P7"))
    assert payload["test_firewall"]["phase8_final_test_available"] is False
    assert payload["test_firewall"]["phase8_test_open_ledger"]["pass"] is False


def test_unopened_test_remains_undecidable(tmp_path: Path) -> None:
    run = _base_run(tmp_path, final=False)
    payload = evaluate_preregistration(Catalog(run))
    outcomes = {row["id"]: row["outcome"] for row in payload["outcomes"]}
    assert outcomes == {
        "P3": "undecidable", "P4": "undecidable", "P5": "hit", "P6": "hit",
        "P7": "undecidable", "R4": "hit", "R5": "hit",
    }


def test_p6_truncated_signed_artifact_is_undecidable(tmp_path: Path) -> None:
    run = _base_run(tmp_path, final=False)
    p3 = run / "phase3"
    p6 = strict_json(p3 / "p6_validation.json")
    p6["n_cells"] = 959
    p6["paired_cell_differences"] = p6["paired_cell_differences"][:959]
    _phase(
        run,
        3,
        {
            "p6_validation.json": p6,
            "summary.json": strict_json(p3 / "summary.json"),
            "failure_funnel.json": strict_json(p3 / "failure_funnel.json"),
        },
    )
    outcome = {
        row["id"]: row for row in evaluate_preregistration(Catalog(run))["outcomes"]
    }["P6"]
    assert outcome["outcome"] == "undecidable"
    assert "960 paired cells" in outcome["reason"]


def test_p5_requires_fixed_unique_layer_inventory(tmp_path: Path) -> None:
    run = _base_run(tmp_path, final=False)
    p5 = strict_json(run / "phase5" / "p5.json")
    p5["layers"] = ["encoder_0"] * 16
    _phase(
        run, 5,
        {
            "p5.json": p5,
            "summary.json": strict_json(run / "phase5" / "summary.json"),
            "failure_funnel.json": strict_json(run / "phase5" / "failure_funnel.json"),
        },
    )
    outcome = {
        row["id"]: row for row in evaluate_preregistration(Catalog(run))["outcomes"]
    }["P5"]
    assert outcome["outcome"] == "undecidable"
    assert "exact unique" in outcome["reason"]


def test_p6_saved_outcome_must_match_recomputation(tmp_path: Path) -> None:
    run = _base_run(tmp_path, final=False)
    phase3 = run / "phase3"
    p6 = strict_json(phase3 / "p6_validation.json")
    p6["prediction_P6"] = "not_supported"
    _phase(
        run, 3,
        {
            "p6_validation.json": p6,
            "summary.json": strict_json(phase3 / "summary.json"),
            "failure_funnel.json": strict_json(phase3 / "failure_funnel.json"),
        },
    )
    with pytest.raises(ArtifactError, match="saved P6 outcome disagrees"):
        evaluate_preregistration(Catalog(run))


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


def test_formula_examples_include_a_signed_final_test_representative(tmp_path: Path) -> None:
    run = _base_run(tmp_path, final=False)
    _phase(
        run, 2,
        {"validation.json": [{
            "system_id": "s1", "teacher_infix": "x_0",
            "variable_to_gene": {"x_0": "g0"},
        }]},
    )
    phase3 = run / "phase3"
    phase3_artifacts = {
        name: strict_json(path)
        for name in ("p6_validation.json", "summary.json", "failure_funnel.json")
        if (path := phase3 / name).is_file()
    }
    phase3_artifacts["selected.json"] = [{
        "cell_id": "validation", "system_id": "s1", "family": "R01",
        "selection_rule": "multi_ic_complexity", "candidate_formula_raw": "x_0",
        "candidate_formula_canonical": "x_0", "valid": True,
        "exponent_aware_skeleton_exact": 1.0, "trajectory_metrics": {},
    }]
    _phase(run, 3, phase3_artifacts)
    _indexed_cells(
        run, 8, "final_cell_artifact_index.json", [_cell(0)],
        {"final_result.json": {"expected_counts": {"cells_total": 1}}},
        substage="final-test",
    )
    rows = formula_examples(Catalog(run))
    final = [row for row in rows if row["source_phase"] == 8]
    assert len(final) == 1
    assert final[0]["category"] == "final_test_success"
    assert final[0]["true_formula"] == "x_0"


def test_cross_run_missing_sources_are_explicit(tmp_path: Path) -> None:
    run = _base_run(tmp_path, final=False)
    payload = cross_run_synthesis(tmp_path, Catalog(run))
    assert len(payload["rows"]) == 4
    assert all(row["status"] == "unavailable" for row in payload["rows"])
    assert "never compared" in payload["comparison_policy"]


def test_gpu_run2_robustness_order_is_not_relabelled_as_causal(tmp_path: Path) -> None:
    run = _base_run(tmp_path, final=False)
    _write(
        tmp_path / "results" / "runs" / "gpu_run2_20260815_1d91927" / "phase4" / "rankings.json",
        {
            "probe": ["decoder_1", "decoder_2", "decoder_3"],
            "intervention": ["decoder_4", "decoder_5", "decoder_6"],
            "iole": ["decoder_7", "decoder_8", "decoder_9"],
        },
    )
    row = cross_run_synthesis(tmp_path, Catalog(run))["rows"][0]
    assert row["run"] == "GPU_RUN2"
    assert row["causal_top3"] == []
    assert row["robustness_top3"] == ["decoder_4", "decoder_5", "decoder_6"]
    assert row["intervention_estimand"] == "robustness_least_damage"
    assert row["probe_causal_top3_jaccard"] is None
    assert row["probe_robustness_top3_jaccard"] == 0.0
    assert row["robustness_iole_top3_jaccard"] == 0.0


def test_incomplete_producer_is_excluded(tmp_path: Path) -> None:
    run = _base_run(tmp_path, final=False)
    _phase(run, 6, {"summary.json": {"status": "smoke-value"}})
    manifest = strict_json(run / "phase6" / "manifest.json")
    manifest["status"] = "incomplete"
    _write(run / "phase6" / "manifest.json", manifest)
    catalog = Catalog(run)
    assert catalog.artifact(6, "summary.json") is None
    assert any(row["status"] == "producer_incomplete" for row in catalog.audit)


def test_incomplete_producer_still_rejects_advertised_deletion(tmp_path: Path) -> None:
    run = _base_run(tmp_path, final=False)
    _phase(run, 6, {"summary.json": {"status": "smoke-value"}})
    manifest = strict_json(run / "phase6" / "manifest.json")
    manifest["status"] = "incomplete"
    _write(run / "phase6" / "manifest.json", manifest)
    (run / "phase6" / "summary.json").unlink()
    with pytest.raises(ArtifactError, match="signed by the manifest but missing"):
        Catalog(run).artifact(6, "summary.json")


def test_full_validation_nogo_is_terminal_but_missing_phase_is_not(tmp_path: Path) -> None:
    run = _base_run(tmp_path, final=False)
    assert campaign_terminal_state(Catalog(run), phase8_final_test_available=False)["terminal"] is False
    for phase in (2, 4, 6, 7):
        _phase(run, phase, {})
    _phase(
        run,
        8,
        {
            "validation_summary.json": {
                "status": "complete", "mode": "full", "validation_complete": True,
                "test_accessed": False, "final_test_authorized": False,
                "go6": {"pass": False, "test_accessed": False},
                "go7": {"pass": False, "test_accessed": False},
            },
            "go6.json": {"pass": False, "test_accessed": False},
            "go7.json": {"pass": False, "test_accessed": False},
        },
        substage="validation", mode="full", test_accessed=False,
        final_test_authorized=False,
    )
    state = campaign_terminal_state(Catalog(run), phase8_final_test_available=False)
    assert state["terminal"] is True
    assert state["state"] == "reported_terminal_validation_no_go"


def test_failure_funnel_nested_schema_is_flattened_without_none(tmp_path: Path) -> None:
    run = _base_run(tmp_path, final=False)
    _phase(
        run,
        5,
        {
            "failure_funnel.json": {
                "main": {
                    "n_cells": 1224, "empty_beam": 0, "beam_shortfall": 478,
                    "selected_valid": 955, "selected_valid_rate": 0.78,
                    "selected_failure_reasons": {"none": 955, "TEDParseError": 110, "ParseError": 159},
                },
                "zero_robustness": {
                    "n_cells": 216, "selected_failure_reasons": {"NonFiniteConstant": 72}
                },
            },
            "p5.json": {"rho": 0.2, "n_layers": 16, "determinate": True},
            "summary.json": {"status": "complete"},
        },
    )
    rows = failure_rows(Catalog(run))
    assert {row["subgroup"] for row in rows if row["phase"] == 5} >= {
        "main", "main/selected_failure_reasons", "zero_robustness/selected_failure_reasons"
    }
    assert all(row["value"] is not None for row in rows)
    parse = next(row for row in rows if row["subgroup"] == "main/selected_failure_reasons" and row["metric"] == "ParseError")
    assert parse["value"] == 159


def test_result_d_summarizes_signed_observational_and_intervention_outputs(tmp_path: Path) -> None:
    run = _base_run(tmp_path, final=False)
    _phase(
        run, 4,
        {
            "summary.json": {"status": "complete"},
            "probes.json": {
                "decoder_token": {
                    "decoder_0": {
                        "next_token": {
                            "probe": {"accuracy": 0.8},
                            "label_shuffle_control": {"accuracy": 0.2},
                        }
                    }
                }
            },
            "decoder_logit_lens.json": {
                "formula_rows": [
                    {"layer": "decoder_0", "normalized_variable_aware_ted": 0.25}
                ],
                "token_rows": [{"layer": "decoder_0"}], "failures": [],
            },
            "gradient_norms.json": {
                "layers": {"decoder_0": {"per_sqrt_parameter": 0.3}}
            },
            "cka.json": {
                "encoder": [[1.0, 0.5], [0.5, 1.0]],
                "decoder": [[1.0, 0.4], [0.4, 1.0]],
            },
        },
    )
    phase5 = run / "phase5"
    _phase(
        run, 5,
        {
            "summary.json": strict_json(phase5 / "summary.json"),
            "p5.json": strict_json(phase5 / "p5.json"),
            "failure_funnel.json": strict_json(phase5 / "failure_funnel.json"),
            "layer_effects.json": {
                "decoder_0": {
                    "damage_ce": 0.2, "failure_aware_ted_increase": 0.3,
                    "component_exact_loss": 0.1, "component_valid_loss": 0.0,
                    "generalization_r2_loss": 1.25,
                    "n_formula_pairs": 72, "n_ce_pairs": 24,
                }
            },
            "causal_ranking.json": {"ranking": ["decoder_0"]},
        },
    )
    _phase(
        run, 7,
        {
            "summary.json": {"status": "complete", "contribution_eligible_seeds": {"main": ["0"]}},
            "layer_freeze.json": {"views": {"main": {"iole_formula_ranking": ["decoder_0"]}}},
            "rank_stability.json": {"main": {"mean_spearman": 0.75}},
            "iole_contribution.json": {
                "main": {
                    "eligible_seeds": ["0"], "normalized_contribution_reportable": True,
                    "rows": [{
                        "seed": "0", "layer": "decoder_0",
                        "frozen_failure_aware_ted": 0.5,
                        "full_failure_aware_ted": 0.4,
                        "layer_failure_aware_ted": 0.42,
                        "normalized_contribution": 0.8,
                    }],
                }
            },
        },
    )
    result = aggregate_results(Catalog(run), {"outcomes": []}, {"rows": []})[
        "D_layer_analysis"
    ]
    assert result["observational"]["decoder_next_token_probe_top3"] == [
        {"layer": "decoder_0", "accuracy_minus_shuffle": pytest.approx(0.6)}
    ]
    assert result["observational"]["within_module_cka"]["encoder"]["mean_off_diagonal"] == 0.5
    assert result["intervention"]["causal_top3"] == ["decoder_0"]
    assert result["intervention"]["causal_top3_layer_effects"]["decoder_0"] == {
        "damage_ce": 0.2,
        "failure_aware_ted_increase": 0.3,
        "component_exact_loss": 0.1,
        "component_valid_loss": 0.0,
        "generalization_r2_loss": 1.25,
        "n_formula_pairs": 72.0,
        "n_ce_pairs": 24.0,
    }
    assert result["formula_iole"]["rank_stability"]["main"]["mean_spearman"] == 0.75
    assert result["formula_iole"]["raw_and_normalized_c_l"]["main"]["rows"][0]["normalized_contribution"] == 0.8
    assert {row["artifact"] for row in result["signed_sources"]} == {
        "probes.json", "decoder_logit_lens.json", "gradient_norms.json",
        "cka.json", "layer_effects.json", "causal_ranking.json", "summary.json",
        "layer_freeze.json", "rank_stability.json", "iole_contribution.json",
    }


def test_family_figure_marks_missing_selected_recovery_undecidable(tmp_path: Path) -> None:
    run = _base_run(tmp_path, final=False)
    p3 = run / "phase3"
    existing = {
        name: strict_json(p3 / name)
        for name in ("p6_validation.json", "summary.json", "failure_funnel.json")
    }
    existing["beam_groups.json"] = [
        {"family": "R01", "true_exponent_aware_skeleton_in_beam": False}
    ]
    _phase(run, 3, existing)
    out = tmp_path / "figures"
    write_figures(Catalog(run), out, {"rows": []})
    text = (out / "phase9_family_generation_recovery.svg").read_text(encoding="utf-8")
    assert "selected-exact=undecidable" in text
    assert "selected-exact=0.0000" not in text


def test_scatter_figure_has_axes_ticks_reference_and_legend(tmp_path: Path) -> None:
    run = _base_run(tmp_path, final=False)
    phase3 = run / "phase3"
    p6 = strict_json(phase3 / "p6_validation.json")
    p6["paired_cell_differences"][0].update({
        "official_reconstruction_nrmse": 0.2,
        "multi_ic_nrmse": 0.1,
    })
    _phase(
        run, 3,
        {
            "p6_validation.json": p6,
            "summary.json": strict_json(phase3 / "summary.json"),
            "failure_funnel.json": strict_json(phase3 / "failure_funnel.json"),
        },
    )
    output = tmp_path / "figures"
    write_figures(Catalog(run), output, {"rows": []})
    svg = (output / "phase9_single_vs_multi_ic.svg").read_text(encoding="utf-8")
    assert "single-trajectory NRMSE" in svg
    assert "multi-IC NRMSE" in svg
    assert "reference: y=x" in svg
    assert "stroke-dasharray" in svg
    assert svg.count("<circle") == 1


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
    assert proc.returncode == 1, proc.stderr
    manifest = strict_json(run / "phase9" / "manifest.json")
    assert manifest["status"] == "incomplete"
    assert manifest["campaign_terminal_state"] == "deferred_upstream_incomplete"
    assert manifest["go_conditions"]["upstream_campaign_terminal"] is False
    assert (graphs / "README.md").is_file()
    provenance = (graphs / "README.md").read_text(encoding="utf-8")
    assert "generator SHA256" in provenance
    assert "Git commit" in provenance
    assert "phase9_failure_funnel.svg" in provenance
    scatter = (graphs / "figures" / "phase9_single_vs_multi_ic.svg").read_text(encoding="utf-8")
    # Empty fixtures have no points, so exercise axes in a direct figure test below.
    assert "Single-trajectory vs multi-IC" in scatter
    assert len(list(reports.glob("GPU_RUN5_*report.md"))) == 4
    assert (reports / "GPU_RUN5_cross_model_synthesis.md").is_file()
    assert len(list((graphs / "figures").glob("*.svg"))) == 10
    assert len(list((graphs / "tables").glob("*.csv"))) == 7
    assert all(
        b"\r\n" not in path.read_bytes()
        for path in (graphs / "tables").glob("*.csv")
    )


@pytest.mark.parametrize("mutation", ["duplicate", "traversal", "size", "sha"])
def test_signed_index_reader_rejects_unsafe_or_drifting_shards(
    tmp_path: Path, mutation: str
) -> None:
    run = tmp_path / "run"
    cells = [_cell(0), _cell(1)]
    _indexed_cells(
        run, 6, "cell_artifact_index.json", cells,
        {"summary.json": {"expected_counts": {"all_decode_cells_total": 2}}},
    )
    phase = run / "phase6"
    index = strict_json(phase / "cell_artifact_index.json")
    if mutation == "duplicate":
        index[1]["path"] = index[0]["path"]
    elif mutation == "traversal":
        index[0]["path"] = "../outside.json"
    elif mutation == "size":
        index[0]["bytes"] += 1
    else:
        index[0]["sha256"] = "0" * 64
    _phase(
        run, 6,
        {
            "summary.json": {"expected_counts": {"all_decode_cells_total": 2}},
            "cell_artifact_index.json": index,
        },
    )
    with pytest.raises(ArtifactError):
        list(Catalog(run).indexed_json(6, "cell_artifact_index.json", required=True))


def test_failure_analysis_has_nonduplicated_event_and_funnel_layers(tmp_path: Path) -> None:
    run = tmp_path / "run"
    failed_cell = _cell(0, failure=True)
    # Keep a real trajectory failure distinct from the cell-level timeout;
    # synthetic timeout-filled role entries are intentionally not double-counted.
    failed_cell["selected"]["generation_failure"] = "ParseError"
    _indexed_cells(
        run, 6, "cell_artifact_index.json", [failed_cell],
        {"summary.json": {"expected_counts": {"all_decode_cells_total": 1}}},
    )
    catalog = Catalog(run)
    analysis = failure_analysis(catalog)
    assert analysis["coverage_pass"] is True
    assert analysis["event_identity_unique"] is True
    assert analysis["selected_is_attribute_not_event"] is True
    event_types = {row["failure_class"] for row in analysis["events"]}
    assert {"timeout", "beam_shortfall", "parse", "ted", "trajectory"} <= event_types
    assert all(row["layer"] == "failure_event" for row in analysis["events"])
    assert all(row["layer"] == "derived_funnel" for row in analysis["funnel"])
    assert any(row["selected"] is True for row in analysis["events"])


def test_full_mode_coverage_uses_registered_counts_not_self_report_only(tmp_path: Path) -> None:
    run = tmp_path / "run"
    _indexed_cells(
        run, 6, "cell_artifact_index.json", [_cell(0)],
        {"summary.json": {
            "mode": "full", "expected_counts": {"all_decode_cells_total": 1}
        }},
    )
    analysis = failure_analysis(Catalog(run))
    row = analysis["index_coverage"][0]
    assert row["expected_shards"] == 7992
    assert row["pass"] is False
    assert analysis["coverage_pass"] is False


def test_full_mode_phase8_validation_uses_correct_registered_count(tmp_path: Path) -> None:
    run = tmp_path / "run"
    _indexed_cells(
        run, 8, "validation_cell_artifact_index.json", [_cell(0)],
        {"validation_summary.json": {
            "mode": "full", "expected_counts": {"all_decode_cells_total": 1}
        }},
        substage="validation",
    )
    analysis = failure_analysis(Catalog(run))
    row = analysis["index_coverage"][0]
    assert row["expected_shards"] == 20736
    assert row["pass"] is False


def test_full_mode_odebench_forgetting_is_stream_verified(tmp_path: Path) -> None:
    run = tmp_path / "run"
    _indexed_cells(
        run, 8, "odebench_forgetting_index.json", [_cell(0)],
        {
            "validation_summary.json": {
                "mode": "full", "expected_counts": {"all_decode_cells_total": 20736}
            },
            "odebench_forgetting_audit.json": {
                "expected_cells_total": 1, "observed_cells_total": 1, "pass": True
            },
        },
        substage="final-test",
    )
    catalog = Catalog(run)
    analysis = failure_analysis(catalog)
    row = analysis["index_coverage"][0]
    assert row["index"] == "odebench_forgetting_index.json"
    assert row["verified_shards"] == 1
    assert row["expected_shards"] == 3780
    assert row["pass"] is False
    audit_row = next(
        item for item in catalog.audit
        if item.get("name") == "odebench_forgetting_index.json"
        and item.get("status") == "indexed_shards_verified"
    )
    assert audit_row["verified_shard_count"] == 1


def test_terminal_uncertainty_uses_signed_three_seed_component_shards(tmp_path: Path) -> None:
    run = tmp_path / "run"
    cells = [_cell(0), _cell(1), _cell(2, failure=True)]
    _indexed_cells(
        run, 8, "final_cell_artifact_index.json", cells,
        {
            "final_result.json": {
                "expected_counts": {"cells_total": 3},
                "summaries": {"main": {"grn_top3": {}}},
            }
        },
        substage="final-test",
    )
    result = condition_uncertainty(Catalog(run))
    row = result["rows"][0]
    assert result["stage"] == "final_test"
    assert row["exact_successes"] == 2
    assert row["components"] == 3
    assert row["exact_rate"] == pytest.approx(2 / 3)
    assert len(row["exact_rate_wilson_95_ci"]) == 2
    assert len(row["exact_seed_macro_student_t_95_ci"]) == 2
    assert "n=3" in row["uncertainty_caveat"]


def test_result_c_keeps_validation_evidence_in_both_terminal_paths(tmp_path: Path) -> None:
    no_go = tmp_path / "no_go"
    _indexed_cells(
        no_go, 6, "cell_artifact_index.json",
        [
            _cell(bundle, condition="frozen", stage="confirmation")
            for bundle in (0, 1, 2)
        ],
        {"summary.json": {"expected_counts": {"all_decode_cells_total": 3}}},
    )
    validation_cells = [
        _cell(bundle, stage="validation_confirmation")
        for bundle in (0, 1, 2)
    ]
    _indexed_cells(
        no_go, 8, "validation_cell_artifact_index.json", validation_cells,
        {
            "validation_summary.json": {
                "status": "complete", "mode": "full", "validation_complete": True,
                "test_accessed": False, "final_test_authorized": False,
                "expected_counts": {"all_decode_cells_total": 3},
                "condition_scores": {"main": {"grn_top3": [1.0, -0.25, 1.0, -2.0]}},
                "go6": {"pass": False, "reason": "top3 did not beat frozen"},
                "go7": {"pass": False, "reason": "blocked by Go6"},
            },
            "go6.json": {"pass": False, "reason": "top3 did not beat frozen"},
            "go7.json": {"pass": False, "reason": "blocked by Go6"},
        },
        substage="validation", mode="full", test_accessed=False,
    )
    no_go_result = aggregate_results(Catalog(no_go), {}, {"rows": []})["C_grn_adaptation"]
    assert no_go_result["phase8_validation"]["condition_scores"]
    assert no_go_result["go6"]["reason"] == "top3 did not beat frozen"
    assert no_go_result["go7"]["reason"] == "blocked by Go6"
    assert no_go_result["sealed_test_remained_unopened"] is True
    top3 = next(
        row for row in no_go_result["condition_metrics"]
        if row["condition"] == "grn_top3"
    )
    assert top3["failure_aware_component_ted_mean"] == 0.25
    assert top3["validation_teacher_forcing_ce"] == 2.0

    final = tmp_path / "final"
    directory = final / "phase8"
    indexes = {}
    for label in ("validation", "final"):
        rows = []
        source_cells = (
            validation_cells
            if label == "validation"
            else [_cell(bundle, stage="final_test") for bundle in (0, 1, 2)]
        )
        for position, cell in enumerate(source_cells):
            relative = f"{label}_cells/cell_{position}.json"
            path = directory / relative
            _write(path, cell)
            rows.append({"path": relative, "sha256": sha256_file(path), "bytes": path.stat().st_size})
        indexes[f"{label}_cell_artifact_index.json"] = rows
    _phase(
        final, 8,
        {
            **indexes,
            "validation_summary.json": {
                "status": "complete", "expected_counts": {"all_decode_cells_total": 3},
                "condition_scores": {"main": {"grn_top3": {}}},
            },
            "go6.json": {"pass": True}, "go7.json": {"pass": True},
            "final_result.json": {
                "status": "complete", "expected_counts": {"cells_total": 3},
                "summaries": {"main": {"grn_top3": {}}},
            },
        },
        substage="final-test",
    )
    final_result = aggregate_results(Catalog(final), {}, {"rows": []})["C_grn_adaptation"]
    assert final_result["phase8_validation"]["condition_scores"]
    assert final_result["phase8_final"]["summaries"]
    assert final_result["sealed_test_remained_unopened"] is False


def test_report_escapes_formula_pipes_and_labels_gpu2_robustness(tmp_path: Path) -> None:
    prereg = {
        "outcomes": [
            {"id": key, "outcome": "undecidable", "observed": None}
            for key in ("P3", "P4", "P5", "P6", "P7", "R4", "R5")
        ]
    }
    results = {
        "A_decoded_support": {}, "B_grn_generation_selection": {},
        "C_grn_adaptation": {
            "condition_metrics": [],
            "go8": {"pass": False},
        },
        "D_layer_analysis": {},
        "E_cross_model_synthesis": {"rows": [{
            "run": "GPU_RUN2", "model": "NeSymReS", "generation": "old|generation",
            "probe_top3": [], "causal_top3": [], "robustness_top3": ["decoder_4"],
            "iole_top3": [], "intervention_estimand": "robustness_least_damage",
            "status": "available",
        }]},
    }
    reports = render_reports(
        tmp_path, run_id="unit", results=results, prereg=prereg,
        examples=[{
            "category": "success", "cell_id": "a|b", "true_formula": "x_0 | x_1",
            "predicted_formula_raw": "x_0 | x_1", "failure_reason": None,
        }],
    )
    benchmark = reports["GPU_RUN5_grn_benchmark_report.md"]
    assert "a\\|b" in benchmark
    assert "x_0 \\| x_1" in benchmark
    cross = reports["GPU_RUN5_cross_model_synthesis.md"]
    assert "old\\|generation" in cross
    assert "robustness_least_damage" in cross
    for report in reports.values():
        assert "Go 8 は NO-GO" in report
        assert "DREAM4・実データへの追加実験は実施しなかった" in report


def test_signed_index_rejects_symlink_shard(tmp_path: Path) -> None:
    run = tmp_path / "run"
    _indexed_cells(
        run, 6, "cell_artifact_index.json", [_cell(0)],
        {"summary.json": {"expected_counts": {"all_decode_cells_total": 1}}},
    )
    shard = run / "phase6" / "cells" / "cell_0.json"
    target = shard.with_name("real.json")
    shard.rename(target)
    os.symlink(target.name, shard)
    with pytest.raises(ArtifactError, match="symlink"):
        list(Catalog(run).indexed_json(6, "cell_artifact_index.json", required=True))


def test_failure_events_have_stable_physical_identity_and_shortfall_magnitude(
    tmp_path: Path,
) -> None:
    run = tmp_path / "run"
    timed = _cell(0, failure=True)
    _indexed_cells(
        run, 6, "cell_artifact_index.json", [timed],
        {"summary.json": {"expected_counts": {"all_decode_cells_total": 1}}},
    )
    analysis = failure_analysis(Catalog(run))
    events = analysis["events"]
    assert len({row["event_id"] for row in events}) == len(events)
    shortfall = [row for row in events if row["failure_class"] == "beam_shortfall"]
    assert len(shortfall) == 1
    assert shortfall[0]["missing_candidate_slots"] == 1
    # Candidate timeout penalties fill every trajectory slot with the same
    # reason; they are not independent trajectory-integration failures.
    assert not [row for row in events if row["failure_class"] == "trajectory"]
    timeouts = [row for row in events if row["failure_class"] == "timeout"]
    assert len(timeouts) == 1
    assert timeouts[0]["unit"] == "candidate"
    assert not [row for row in events if row["failure_class"] == "component"]
    assert all(row["source_sha256"] and row["source_path"] for row in events)


@pytest.mark.parametrize("cell_reason", [None, "RuntimeError:DecodeError"])
def test_empty_beam_placeholder_is_the_only_generation_failure_event(
    tmp_path: Path, cell_reason: str | None,
) -> None:
    run = tmp_path / "run"
    cell = _cell(0)
    cell["candidates"] = []
    cell["n_candidates"] = 0
    cell["generation_failure"] = cell_reason
    cell["selected"] = {
        "candidate_index": None,
        "candidate_formula_raw": "",
        "component_exponent_aware_skeleton_exact": [0.0],
        "component_normalized_variable_aware_ted": [1.0],
        "component_valid": [False],
        "generation_failure": "EmptyCandidateSet",
    }
    _indexed_cells(
        run, 6, "cell_artifact_index.json", [cell],
        {"summary.json": {"expected_counts": {"all_decode_cells_total": 1}}},
    )
    events = failure_analysis(Catalog(run))["events"]
    generation = [row for row in events if row["failure_class"] == "generation"]
    assert len(generation) == 1
    assert generation[0]["selected"] is True
    assert generation[0]["unit"] == "candidate"


def test_validation_uncertainty_excludes_grid_and_joins_phase6_confirmation(
    tmp_path: Path,
) -> None:
    run = tmp_path / "run"
    phase6_cells = [
        *[_cell(bundle, condition="frozen", stage="confirmation") for bundle in (0, 1, 2)],
        *[_cell(bundle, condition="frozen", failure=True, stage="screening_lr1e-4_s50") for bundle in (0, 1, 2)],
    ]
    _indexed_cells(
        run, 6, "cell_artifact_index.json", phase6_cells,
        {"summary.json": {"expected_counts": {"all_decode_cells_total": 6}}},
    )
    phase8_cells = [
        *[_cell(bundle, stage="validation_confirmation") for bundle in (0, 1, 2)],
        *[_cell(bundle, failure=True, stage="validation_screening") for bundle in (0, 1, 2)],
    ]
    _indexed_cells(
        run, 8, "validation_cell_artifact_index.json", phase8_cells,
        {"validation_summary.json": {
            "mode": "smoke", "expected_counts": {"all_decode_cells_total": 6}
        }},
        substage="validation",
    )
    result = condition_uncertainty(Catalog(run))
    assert result["retained_cells"] == 6
    assert result["skipped_nonterminal_screening_cells"] == 6
    rows = {row["condition"]: row for row in result["rows"]}
    assert set(rows) == {"frozen", "grn_top3"}
    assert rows["frozen"]["exact_rate"] == 1.0
    assert rows["grn_top3"]["exact_rate"] == 1.0
    assert len(rows["grn_top3"]["failure_aware_ted_seed_macro_student_t_95_ci"]) == 2
    assert rows["grn_top3"]["failure_aware_generalization_nrmse_seed_macro_student_t_95_ci"] is None


def test_nogo_terminal_rejects_contradictory_signed_go_artifacts(tmp_path: Path) -> None:
    run = _base_run(tmp_path, final=False)
    for phase in (2, 4, 6, 7):
        _phase(run, phase, {})
    embedded_go6 = {"pass": False, "test_accessed": False}
    _phase(
        run, 8,
        {
            "validation_summary.json": {
                "status": "complete", "mode": "full", "validation_complete": True,
                "test_accessed": False, "final_test_authorized": False,
                "go6": embedded_go6,
                "go7": {"pass": False, "test_accessed": False},
            },
            "go6.json": {"pass": True, "test_accessed": False},
            "go7.json": {"pass": False, "test_accessed": False},
        },
        substage="validation", mode="full", test_accessed=False,
        final_test_authorized=False,
    )
    state = campaign_terminal_state(Catalog(run), phase8_final_test_available=False)
    assert state["terminal"] is False


def test_git_generated_allowlist_sees_individual_untracked_files(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
    tracked = repo / "tracked.txt"
    tracked.write_text("base\n", encoding="utf-8")
    subprocess.run(["git", "add", "tracked.txt"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-qm", "base"], cwd=repo, check=True)
    generated = repo / "graphs" / "unit" / "figures" / "a.svg"
    generated.parent.mkdir(parents=True)
    generated.write_text("<svg/>\n", encoding="utf-8")
    status = _git(repo)["status_short"]
    assert "graphs/unit/figures/a.svg" in status
    assert _git_changes_are_generated_only(status, repo_root=repo, generated=[generated])
    unrelated = repo / "unrelated.txt"
    unrelated.write_text("no\n", encoding="utf-8")
    assert not _git_changes_are_generated_only(
        _git(repo)["status_short"], repo_root=repo, generated=[generated]
    )


def test_source_audit_accepts_verified_indices_but_rejects_unknown_status() -> None:
    assert _gpu_run5_source_audit_pass([
        {"status": "verified"}, {"status": "indexed_shards_verified"},
        {"status": "loaded"}, {"status": "missing"},
    ])
    assert not _gpu_run5_source_audit_pass([{"status": "producer_incomplete"}])


def test_graph_provenance_maps_direct_and_historical_sources_per_output(
    tmp_path: Path,
) -> None:
    root = tmp_path / "repo"
    generated = [
        root / "graphs" / "unit" / "tables" / "phase9_failure_funnel.csv",
        root / "graphs" / "unit" / "tables" / "phase9_cross_run_rankings.csv",
        root / "graphs" / "unit" / "tables" / "phase9_condition_metrics.csv",
        root / "graphs" / "unit" / "tables" / "phase9_preregistration_outcomes.csv",
    ]
    for path in generated:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("x\n", encoding="utf-8")
    catalog = Catalog(root / "run")
    catalog.audit.extend([
        {"phase": 0, "name": "preregistration.json", "sha256": "0" * 64, "status": "verified"},
        {"phase": 1, "name": "decoded_support.json", "sha256": "1" * 64, "status": "verified"},
        {"phase": 6, "name": "cell_artifact_index.json", "sha256": "a" * 64, "status": "indexed_shards_verified"},
        {"phase": 7, "name": "layer_freeze.json", "sha256": "b" * 64, "status": "verified"},
        {"phase": 8, "name": "validation_cell_artifact_index.json", "sha256": "8" * 64, "status": "indexed_shards_verified"},
    ])
    readme = root / "graphs" / "unit" / "README.md"
    _write_graph_provenance(
        readme, repo_root=root, run_id="unit", generated=generated,
        catalog=catalog,
        dependency_phases={
            "phase9_failure_funnel.csv": {6},
            "phase9_cross_run_rankings.csv": {7},
            "phase9_condition_metrics.csv": {6, 8},
            "phase9_preregistration_outcomes.csv": {0, 1},
        },
        historical_sources=[{
            "path": "results/GPU_RUN2/ranks.json", "sha256": "c" * 64,
            "provenance": "content_hashed_at_phase9_not_manifest_signed",
        }],
        git_commit="d" * 40,
    )
    lines = readme.read_text(encoding="utf-8").splitlines()
    failure_line = next(line for line in lines if "phase9_failure_funnel.csv" in line)
    cross_line = next(line for line in lines if "phase9_cross_run_rankings.csv" in line)
    condition_line = next(line for line in lines if "phase9_condition_metrics.csv" in line)
    prereg_line = next(line for line in lines if "phase9_preregistration_outcomes.csv" in line)
    assert "phase6/cell_artifact_index.json" in failure_line
    assert "GPU_RUN2" not in failure_line
    assert "phase7/layer_freeze.json" in cross_line
    assert "GPU_RUN2/ranks.json" in cross_line
    assert "content_hashed_at_phase9_not_manifest_signed" in cross_line
    assert "phase6/cell_artifact_index.json" in condition_line
    assert "phase8/validation_cell_artifact_index.json" in condition_line
    assert "phase0/preregistration.json" in prereg_line
    assert "phase1/decoded_support.json" in prereg_line


def test_svg_reference_geometry_uses_shared_scale_and_includes_zero(tmp_path: Path) -> None:
    diagonal = tmp_path / "diagonal.svg"
    _svg(
        diagonal, "asymmetric", [], points=[(0.0, 10.0, "a"), (1.0, 20.0, "b")],
        x_label="x", y_label="y", reference="diagonal",
    )
    text = diagonal.read_text(encoding="utf-8")
    # A common 0..20 scale is printed on both axes; under independent scales
    # the x axis would end at 1 and the corner line would not represent y=x.
    assert text.count(">0</text>") >= 2
    assert text.count(">20</text>") >= 2
    zero = tmp_path / "zero.svg"
    _svg(
        zero, "positive", [], points=[(1.0, 2.0, "a"), (2.0, 3.0, "b")],
        reference="zero_y",
    )
    assert "reference: y=0" in zero.read_text(encoding="utf-8")
