"""Focused tests for C0001 metric-identifiability audit v9."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from gpu_runmultiai.calls import CallLogger, expected_confirmatory_calls
from gpu_runmultiai.constants import (
    AUDIT_ID,
    CONFIRMATORY_CALL_CEILING,
    FULL_RUN_CALL_CEILING,
    PLAN_SHA256,
    SIMPLIFIER_SUBPROCESS_TIMEOUT_SEC,
)
from gpu_runmultiai.controls import evaluate_validity_gates, gate_b4, gate_n1
from gpu_runmultiai.corpus import load_frozen_corpus, tier_index
from gpu_runmultiai.ids import (
    COMPONENT_FIXTURE,
    NEGATIVE_FIXTURE,
    PAIR_FIXTURE,
    REWRITE_FIXTURE,
    component_id_for,
    component_key,
    negative_canonical_key,
    negative_id_for,
    pair_id_for,
    pair_key,
    rewrite_canonical_key,
    rewrite_id_for,
    sha256_hex,
)
from gpu_runmultiai.manifest import build_resume_identity, normalize_cli_args, verify_plan_hash
from gpu_runmultiai.odeformer_runtime import (
    ODEFormerUnavailable,
    build_production_scaler,
    decode_system_tree,
    forward_scale_system,
    get_env,
    rescale_system,
    simplify_tree_subprocess,
    tree_to_prefix_list,
    tree_to_system_infix,
)
from gpu_runmultiai.oracle import audit_rational_parse, oracle_equivalence, oracle_single_component
from gpu_runmultiai.outcomes import PAIR_RESULT_COLUMNS, build_outcome_row, classify_outcome, evaluate_primary_decision
from gpu_runmultiai.pipeline import run_b0_pair
from gpu_runmultiai.rewrites import rewrite_registration, truth_component_infix
from gpu_runmultiai.sealed_guard import SealedPathGuard
from gpu_runmultiai.strata import component_stratum


def test_binding_plan_sha_matches_fixture():
    assert verify_plan_hash() == PLAN_SHA256


@pytest.mark.parametrize(
    "fixture_name,fixture",
    [
        ("rewrite", REWRITE_FIXTURE),
        ("negative", NEGATIVE_FIXTURE),
        ("component", COMPONENT_FIXTURE),
        ("pair", PAIR_FIXTURE),
    ],
)
def test_frozen_sha_fixtures(fixture_name, fixture):
    if fixture_name == "rewrite":
        key = rewrite_canonical_key("R01_train_d61001_000", 0)
        rewrite_id, selected_r, _ = rewrite_id_for("R01_train_d61001_000", 0)
        assert key == fixture["canonical_key_string"]
        assert fixture["pipe_count"] == key.count("|")
        assert fixture["backslash_count"] == 0
        assert sha256_hex(key) == fixture["sha256"]
        assert selected_r == fixture["selected_r"]
        assert rewrite_id == fixture["rewrite_id"]
    elif fixture_name == "negative":
        key = negative_canonical_key("R01_train_d61001_000", 0)
        negative_id, selected_c, _ = negative_id_for("R01_train_d61001_000", 0)
        assert key == fixture["canonical_key_string"]
        assert sha256_hex(key) == fixture["sha256"]
        assert selected_c == fixture["selected_c"]
        assert negative_id == fixture["negative_id"]
    elif fixture_name == "component":
        key = component_key(fixture["corpus_hash"], fixture["system_id"], fixture["component_idx"])
        component_id, _ = component_id_for(fixture["corpus_hash"], fixture["system_id"], fixture["component_idx"])
        assert key == fixture["component_key"]
        assert component_id == fixture["component_id"]
    else:
        key = pair_key(
            fixture["corpus_hash"],
            fixture["system_id"],
            fixture["component_idx"],
            fixture["scale"],
            fixture["rewrite_id"],
        )
        pair_id, _ = pair_id_for(
            fixture["corpus_hash"],
            fixture["system_id"],
            fixture["component_idx"],
            fixture["scale"],
            fixture["rewrite_id"],
        )
        assert key == fixture["pair_key"]
        assert pair_id == fixture["pair_id"]


def test_corpus_source_index_contract():
    corpus = load_frozen_corpus()
    assert corpus["system_count"] == 240
    assert corpus["component_count"] == 510
    assert corpus["corpus_hash"] == corpus["fingerprint_payload_bytes_hash"]
    first = next(row for row in corpus["train_records"] if row["system_id"] == "R01_train_d61001_000")
    assert tier_index(first) == 0
    assert first["variant_index"] == 0


def test_outcome_precedence_exhaustive():
    cases = [
        ({"construction_incomplete": True}, "construction_incomplete"),
        ({"execution_failure": True}, "execution_failure"),
        ({"semantic_drift": True}, "semantic_drift"),
        (
            {
                "e1_oracle_equivalent": True,
                "e2_oracle_equivalent": True,
                "hill_form": False,
            },
            "structural_false_negative",
        ),
        (
            {
                "e1_oracle_equivalent": True,
                "e2_oracle_equivalent": True,
                "hill_form": True,
            },
            "preserved",
        ),
    ]
    for flags, expected in cases:
        assert classify_outcome(flags) == expected


def test_classifier_parse_failure_is_execution_failure():
    row = build_outcome_row(
        e1_oracle_equivalent=True,
        e2_oracle_equivalent=True,
        hill_form=False,
        classifier_parse_valid=False,
        classifier_parse_failure_reason="ParseError",
    )
    assert row["outcome_category"] == "execution_failure"


def test_primary_decision_order():
    supported = [
        {
            "condition": "B0",
            "stratum": "strict_hill",
            "pair_id": f"pair_sha256:{index:064x}",
            "outcome_category": "structural_false_negative" if index == 0 else "preserved",
            "is_fully_diagnostic": True,
        }
        for index in range(1320)
    ]
    assert evaluate_primary_decision(supported, validity_gate_failed=False) == "H0001 supported"
    unsupported = [
        {
            "condition": "B0",
            "stratum": "strict_hill",
            "pair_id": f"pair_sha256:{index:064x}",
            "outcome_category": "preserved",
            "is_fully_diagnostic": True,
        }
        for index in range(1320)
    ]
    assert evaluate_primary_decision(unsupported, validity_gate_failed=False) == "H0001 unsupported"
    assert evaluate_primary_decision(unsupported[:1319], validity_gate_failed=False) == "H0001 undecidable"


def test_counted_call_totals_and_resume_identity(tmp_path):
    assert expected_confirmatory_calls() == CONFIRMATORY_CALL_CEILING
    log_path = tmp_path / "call_log.jsonl"
    logger = CallLogger(log_path)
    logger.record(
        primitive="truth_register_classify",
        condition="registration",
        stage="truth",
        unit_type="component",
        unit_id="component_sha256:abc",
        status="completed",
    )
    logger.record(
        primitive="rewrite_oracle_precheck",
        condition="registration",
        stage="rewrite",
        unit_type="component",
        unit_id="component_sha256:abc",
        status="completed",
        rewrite_id="rewrite_sha256:def",
    )
    reloaded = CallLogger.load(log_path)
    assert reloaded.total() == 2
    with pytest.raises(RuntimeError, match="duplicate counted call"):
        reloaded.record(
            primitive="rewrite_oracle_precheck",
            condition="registration",
            stage="rewrite",
            unit_type="component",
            unit_id="component_sha256:abc",
            status="completed",
            rewrite_id="rewrite_sha256:def",
        )
    normalized = normalize_cli_args({"resume": True, "fail_if_exists": True, "allow_cpu": True, "primary_scales": ("0.1", "0.5")})
    assert "resume" not in normalized
    assert "fail_if_exists" not in normalized
    assert normalized["allow_cpu"] is True
    assert normalized["primary_scales"] == ["0.1", "0.5"]


def test_call_logger_assert_ceiling(monkeypatch):
    monkeypatch.setattr("gpu_runmultiai.calls.CONFIRMATORY_CALL_CEILING", 2)
    logger = CallLogger()
    logger.record(
        primitive="truth_register_classify",
        condition="registration",
        stage="truth",
        unit_type="component",
        unit_id="component_sha256:1",
        status="completed",
    )
    logger.record(
        primitive="truth_register_classify",
        condition="registration",
        stage="truth",
        unit_type="component",
        unit_id="component_sha256:2",
        status="completed",
    )
    logger.assert_ceiling()
    logger.record(
        primitive="truth_register_classify",
        condition="registration",
        stage="truth",
        unit_type="component",
        unit_id="component_sha256:3",
        status="completed",
    )
    with pytest.raises(RuntimeError, match="G1 FAIL"):
        logger.assert_ceiling()


def test_resume_identity_includes_fingerprint_paths(tmp_path):
    identity = build_resume_identity(
        commit="abc123",
        audit_script_path=Path("scripts/phases/gpu_runmultiai_c0001_metric_audit.py"),
        corpus_hash="0" * 64,
        cli_args={"smoke": True},
        output_dir=tmp_path,
    )
    assert identity["fingerprint_payload_path"].endswith("fingerprint_payload.json")
    assert identity["fingerprint_bytes_path"].endswith("fingerprint_bytes.bin")
    assert identity["fingerprint_payload_bytes_hash"] == "0" * 64


def test_sealed_guard_blocks_deep_paths_without_real_artifact(tmp_path):
    output_root = tmp_path / "results" / "runs"
    denied = output_root / "gpu_run5_example" / "phase8" / "nested" / "predictions" / "rows.json"
    denied.parent.mkdir(parents=True)
    denied.write_text("[]", encoding="utf-8")
    guard = SealedPathGuard(output_root_abs=output_root.resolve())
    guard.install()
    try:
        assert guard.is_denied(denied, denied)
        with pytest.raises(PermissionError):
            open(denied, encoding="utf-8")
        assert guard.attempt_count() == 1
    finally:
        guard.restore()
    # pytest tmp cleanup must succeed after restore
    open(tmp_path / "cleanup.txt", "w", encoding="utf-8").write("ok")


def test_n1_and_b4_gate_shapes():
    n1_rows = [{"oracle": {"completed": True, "equivalent": False}} for _ in range(100)]
    assert gate_n1(n1_rows)
    b4_rows = [{"valid": True, "canonical_exact": 1} for _ in range(510)]
    assert gate_b4(b4_rows)


def test_fail_if_exists_and_resume_mismatch(tmp_path):
    from gpu_runmultiai.audit import run_audit

    output_dir = tmp_path / "audit"
    output_dir.mkdir()
    (output_dir / "marker.txt").write_text("x", encoding="utf-8")
    options = {
        "output_dir": str(output_dir),
        "oracle_timeout_sec": 30.0,
        "fail_if_exists": True,
        "resume": False,
        "smoke": True,
        "primary_scales": ("0.1",),
    }
    with pytest.raises(RuntimeError, match="output directory already exists"):
        run_audit(options)


def test_smoke_audit_bounded(tmp_path):
    from gpu_runmultiai.audit import run_audit

    output_dir = tmp_path / "smoke"
    result = run_audit(
        {
            "output_dir": str(output_dir),
            "oracle_timeout_sec": 30.0,
            "simplifier_subprocess_timeout_sec": SIMPLIFIER_SUBPROCESS_TIMEOUT_SEC,
            "fail_if_exists": False,
            "resume": False,
            "smoke": True,
            "primary_scales": ("0.1",),
        }
    )
    assert (output_dir / "audit_manifest.json").is_file()
    assert (output_dir / "equivalence_oracle.json").is_file()
    assert (output_dir / "deviation_log.md").is_file()
    assert (output_dir / "pair_results.csv").is_file()
    header = (output_dir / "pair_results.csv").read_text(encoding="utf-8").splitlines()[0]
    assert header.split(",") == PAIR_RESULT_COLUMNS
    assert result["call_total"] < CONFIRMATORY_CALL_CEILING
    assert result["call_total"] < FULL_RUN_CALL_CEILING


def test_strata_counts():
    corpus = load_frozen_corpus()
    counts = {"strict_hill": 0, "non_strict_hill": 0, "linear": 0, "other": 0}
    for item in corpus["component_index"]:
        counts[component_stratum(item["family"], item["component_idx"])] += 1
    assert counts["strict_hill"] == 330
    assert counts["non_strict_hill"] == 60
    assert counts["linear"] == 120


def test_audit_rational_parse_preserves_exact_tokens():
    import sympy as sp

    value = audit_rational_parse("0.1")
    assert value == sp.Rational(1, 10)


def test_oracle_self_equivalence_single_component():
    corpus = load_frozen_corpus()
    record = next(row for row in corpus["train_records"] if row["system_id"] == "R01_train_d61001_000")
    _, truth_infix = truth_component_infix(record, 0)
    result = oracle_equivalence(truth_infix, truth_infix, component_idx=0, timeout_sec=30.0)
    assert result.completed
    assert result.equivalent
    assert result.analytic_equivalent
    assert result.numeric_equivalent
    assert result.parsed_rationals


def test_oracle_negative_control_rejects_addition():
    corpus = load_frozen_corpus()
    record = next(row for row in corpus["train_records"] if row["system_id"] == "R01_train_d61001_000")
    truth_prefix, truth_infix = truth_component_infix(record, 0)
    rewrite = rewrite_registration("R01_train_d61001_000", 0, truth_prefix, truth_infix, oracle_timeout_sec=30.0)
    negative_infix = f"(({truth_infix})+(1))"
    result = oracle_equivalence(truth_infix, negative_infix, component_idx=0, timeout_sec=30.0)
    assert result.completed
    assert not result.equivalent


def test_oracle_numeric_mismatch_retains_analytic():
    truth = "(x_0)"
    candidate = "(x_0 + 1)"
    result = oracle_equivalence(truth, candidate, component_idx=0, timeout_sec=30.0)
    assert result.completed
    assert result.analytic_equivalent is False
    assert result.numeric_equivalent is False
    assert not result.equivalent


@pytest.mark.skipif(os.environ.get("LANSR_SKIP_ODEFORMER_CHAIN") == "1", reason="ODEFormer runtime unavailable")
def test_e1_truth_equivalence_and_e2_from_e1_provenance():
    from gpu_runmultiai.odeformer_runtime import ODEFormerUnavailable, require_odeformer

    try:
        require_odeformer()
    except ODEFormerUnavailable:
        pytest.skip("ODEFormer runtime unavailable")
    corpus = load_frozen_corpus()
    record = next(row for row in corpus["train_records"] if row["system_id"] == "R01_train_d61001_000")
    truth_prefix, truth_infix = truth_component_infix(record, 0)
    rewrite = rewrite_registration("R01_train_d61001_000", 0, truth_prefix, truth_infix, oracle_timeout_sec=30.0)
    logger = CallLogger()
    guard = SealedPathGuard(output_root_abs=Path("/nonexistent/results/runs"))
    row = run_b0_pair(
        corpus_hash=corpus["corpus_hash"],
        record=record,
        component_idx=0,
        scale="0.1",
        rewrite_row=rewrite,
        oracle_timeout_sec=30.0,
        simplifier_timeout_sec=SIMPLIFIER_SUBPROCESS_TIMEOUT_SEC,
        call_logger=logger,
        runtime_available=True,
        guard=guard,
    )
    assert row.get("e1_prefix_raw")
    assert row.get("e2_prefix_raw")
    assert row["e1_prefix_raw"] != row["e0_prefix_raw"]
    e1_oracle = oracle_single_component(
        truth_infix,
        row["e1_infix"],
        candidate_component_idx=0,
        timeout_sec=30.0,
    )
    assert e1_oracle.completed
    assert e1_oracle.equivalent
    e1_prefixes = row["e1_prefix_raw"].split("|")
    simplified = simplify_tree_subprocess(e1_prefixes, timeout_sec=SIMPLIFIER_SUBPROCESS_TIMEOUT_SEC)
    assert simplified.get("ok")
    assert simplified.get("infix")


def test_resume_appends_call_log(tmp_path):
    from gpu_runmultiai.audit import run_audit

    output_dir = tmp_path / "resume"
    base_options = {
        "output_dir": str(output_dir),
        "oracle_timeout_sec": 30.0,
        "simplifier_subprocess_timeout_sec": SIMPLIFIER_SUBPROCESS_TIMEOUT_SEC,
        "fail_if_exists": False,
        "resume": False,
        "smoke": True,
        "primary_scales": ("0.1",),
    }
    first = run_audit(base_options)
    first_total = first["call_total"]
    second = run_audit({**base_options, "resume": True})
    assert second["call_total"] == first_total
    reloaded = CallLogger.load(output_dir / "call_log.jsonl")
    assert reloaded.total() == second["call_total"]
