from __future__ import annotations

import json
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
    cross_run_synthesis,
    evaluate_preregistration,
    failure_rows,
    formula_examples,
    sha256_file,
    strict_json,
    write_figures,
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
    paired = [
        {"system_id": f"s{index % 80:02d}", "paired_index": index}
        for index in range(960)
    ]
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


def test_cross_run_missing_sources_are_explicit(tmp_path: Path) -> None:
    run = _base_run(tmp_path, final=False)
    payload = cross_run_synthesis(tmp_path, Catalog(run))
    assert len(payload["rows"]) == 4
    assert all(row["status"] == "unavailable" for row in payload["rows"])
    assert "never compared" in payload["comparison_policy"]


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
                "go6": {"pass": False}, "go7": {"pass": False},
            }
        },
        substage="validation", mode="full", test_accessed=False,
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
    assert {row["artifact"] for row in result["signed_sources"]} == {
        "probes.json", "decoder_logit_lens.json", "gradient_norms.json",
        "cka.json", "layer_effects.json", "causal_ranking.json",
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
    assert len(list(reports.glob("GPU_RUN5_*report.md"))) == 4
    assert (reports / "GPU_RUN5_cross_model_synthesis.md").is_file()
    assert len(list((graphs / "figures").glob("*.svg"))) == 10
    assert len(list((graphs / "tables").glob("*.csv"))) == 6
