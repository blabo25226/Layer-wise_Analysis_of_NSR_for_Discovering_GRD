"""Focused tests for C0001 metric-identifiability audit v16."""

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
    Q4_TIMEOUT_SEC,
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
from gpu_runmultiai.oracle import (
    audit_parse_prefix_component,
    audit_rational_parse,
    oracle_equivalence,
    oracle_equivalence_prefix,
    oracle_single_component,
    prefix_to_infix_component,
)
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
            "eligibility_layer": "strict_hill_primary",
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
            "eligibility_layer": "strict_hill_primary",
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


def test_oracle_numeric_close_but_analytically_distinct():
    truth = "(x_0)"
    candidate = "(x_0 + 1e-12)"
    result = oracle_equivalence(truth, candidate, component_idx=0, timeout_sec=30.0)
    assert result.completed
    assert result.analytic_equivalent is False
    assert result.numeric_equivalent is True
    assert result.equivalent is False
    assert result.equivalent == (result.analytic_equivalent and result.numeric_equivalent)


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
        q4_timeout_sec=Q4_TIMEOUT_SEC,
        simplifier_timeout_sec=SIMPLIFIER_SUBPROCESS_TIMEOUT_SEC,
        call_logger=logger,
        runtime_available=True,
        guard=guard,
    )
    assert row.get("e1_prefix_raw")
    assert row.get("e2_prefix_raw")
    assert row["e1_prefix_raw"] != row["e0_prefix_raw"]
    e1_component_prefix = row["e1_prefix_raw"].split("|")[0]
    e1_oracle = oracle_single_component(
        truth_infix,
        row["e1_infix"],
        candidate_component_idx=0,
        timeout_sec=30.0,
        truth_component_prefix=truth_prefix,
        candidate_component_prefix=e1_component_prefix,
    )
    assert e1_oracle.completed
    assert e1_oracle.equivalent == (
        e1_oracle.analytic_equivalent and e1_oracle.numeric_equivalent
    )
    assert row["e1_oracle_equivalent"] == e1_oracle.equivalent
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


def test_confirmatory_and_descriptive_counters_are_separate():
    logger = CallLogger()
    logger.record(
        primitive="e0_analytic_construct",
        condition="B0",
        stage="E0",
        unit_type="pair",
        unit_id="pair_sha256:1",
        status="completed",
    )
    logger.record(
        primitive="e0_analytic_construct",
        condition="D2",
        stage="E0",
        unit_type="pair",
        unit_id="pair_sha256:2",
        status="completed",
    )
    assert logger.confirmatory_total() == 1
    assert logger.descriptive_total() == 1
    logger.assert_ceiling(run_d2=True)


def test_oracle_pow_tiers_and_long_decimal_tokens():
    import sympy as sp

    for op in ("pow2", "pow3", "pow4"):
        prefix = f"{op},x_0"
        tree = audit_parse_prefix_component(prefix)
        assert tree is not None
        result = oracle_equivalence_prefix(prefix, prefix, timeout_sec=5.0)
        assert result.completed
        assert result.equivalent
        assert result.parsed_rationals
    long_token = "0.1234567890123"
    parsed = audit_rational_parse(long_token)
    assert parsed == sp.Rational(long_token)


def test_sealed_guard_os_open_rdonly_is_intercepted(tmp_path):
    output_root = tmp_path / "results" / "runs"
    denied = output_root / "gpu_run5_example" / "test" / "rows.json"
    denied.parent.mkdir(parents=True)
    denied.write_text("[]", encoding="utf-8")
    guard = SealedPathGuard(output_root_abs=output_root.resolve())
    guard.install()
    try:
        with pytest.raises(PermissionError):
            os.open(denied, os.O_RDONLY)
        assert guard.attempt_count() == 1
    finally:
        guard.restore()


@pytest.mark.skipif(os.environ.get("LANSR_SKIP_ODEFORMER_CHAIN") == "1", reason="ODEFormer runtime unavailable")
@pytest.mark.parametrize("scale", ("0.1", "0.5", "1.0", "2.0"))
def test_e0_e1_round_trip_primary_scales(scale):
    from gpu_runmultiai.odeformer_runtime import ODEFormerUnavailable, require_odeformer

    try:
        require_odeformer()
    except ODEFormerUnavailable:
        pytest.skip("ODEFormer runtime unavailable")
    corpus = load_frozen_corpus()
    record = next(row for row in corpus["train_records"] if row["system_id"] == "R01_train_d61001_000")
    truth_prefix, truth_infix = truth_component_infix(record, 0)
    rewrite = rewrite_registration("R01_train_d61001_000", 0, truth_prefix, truth_infix, oracle_timeout_sec=30.0)
    row = run_b0_pair(
        corpus_hash=corpus["corpus_hash"],
        record=record,
        component_idx=0,
        scale=scale,
        rewrite_row=rewrite,
        oracle_timeout_sec=30.0,
        q4_timeout_sec=Q4_TIMEOUT_SEC,
        simplifier_timeout_sec=SIMPLIFIER_SUBPROCESS_TIMEOUT_SEC,
        call_logger=CallLogger(),
        runtime_available=True,
        guard=SealedPathGuard(output_root_abs=Path("/nonexistent/results/runs")),
    )
    assert row.get("e1_oracle_completed")
    assert row.get("outcome_category") in {"preserved", "semantic_drift", "execution_failure", "construction_incomplete"}
    if row.get("e1_oracle_completed") and row.get("e1_oracle_equivalent"):
        assert row.get("e1_analytic_equivalent") is True
        assert row.get("e1_numeric_equivalent") is True
    assert row.get("e1_oracle_equivalent") == (
        bool(row.get("e1_analytic_equivalent")) and bool(row.get("e1_numeric_equivalent"))
    )
    e1_prefix = row["e1_prefix_raw"].split("|")[0]
    oracle = oracle_equivalence_prefix(rewrite["rewrite_prefix"], e1_prefix, timeout_sec=30.0)
    assert oracle.completed
    assert oracle.equivalent == (oracle.analytic_equivalent and oracle.numeric_equivalent)


def test_resume_skips_reexecution_with_spy(tmp_path):
    from gpu_runmultiai.audit import run_audit

    output_dir = tmp_path / "resume_spy"
    options = {
        "output_dir": str(output_dir),
        "oracle_timeout_sec": 30.0,
        "simplifier_subprocess_timeout_sec": SIMPLIFIER_SUBPROCESS_TIMEOUT_SEC,
        "fail_if_exists": False,
        "resume": False,
        "smoke": True,
        "primary_scales": ("0.1",),
    }
    first = run_audit(options)
    calls_before = CallLogger.load(output_dir / "call_log.jsonl").total()
    second = run_audit({**options, "resume": True})
    calls_after = CallLogger.load(output_dir / "call_log.jsonl").total()
    assert calls_after == calls_before
    assert second["call_total"] == first["call_total"]


@pytest.mark.skipif(os.environ.get("LANSR_SKIP_ODEFORMER_CHAIN") == "1", reason="ODEFormer runtime unavailable")
def test_live_d2_pair_counts_descriptive_only():
    from gpu_runmultiai.odeformer_runtime import ODEFormerUnavailable, require_odeformer
    from gpu_runmultiai.pipeline import run_d2_pair

    try:
        require_odeformer()
    except ODEFormerUnavailable:
        pytest.skip("ODEFormer runtime unavailable")
    corpus = load_frozen_corpus()
    record = next(
        row
        for row in corpus["train_records"]
        if row["system_id"] == "R01_train_d61001_000"
    )
    truth_prefix, truth_infix = truth_component_infix(record, 0)
    rewrite = rewrite_registration(
        "R01_train_d61001_000", 0, truth_prefix, truth_infix, oracle_timeout_sec=30.0
    )
    logger = CallLogger()
    before_confirmatory = logger.confirmatory_total()
    before_descriptive = logger.descriptive_total()
    run_d2_pair(
        corpus_hash=corpus["corpus_hash"],
        record=record,
        component_idx=0,
        rewrite_row=rewrite,
        oracle_timeout_sec=30.0,
        q4_timeout_sec=Q4_TIMEOUT_SEC,
        simplifier_timeout_sec=SIMPLIFIER_SUBPROCESS_TIMEOUT_SEC,
        call_logger=logger,
        runtime_available=True,
        guard=SealedPathGuard(output_root_abs=Path("/nonexistent/results/runs")),
    )
    assert logger.confirmatory_total() == before_confirmatory
    assert logger.descriptive_total() == before_descriptive + 7
    d2_calls = [row for row in logger.rows if row["condition"] == "D2"]
    assert len(d2_calls) == 7
    assert {row["primitive"] for row in d2_calls} == {
        "e0_analytic_construct",
        "scaler_rescale_function",
        "simplifier_subprocess",
        "oracle_equivalence",
        "classify_component_flags",
        "formula_metrics_pair",
    }
    assert sum(1 for row in d2_calls if row["primitive"] == "oracle_equivalence") == 2


def test_simplifier_subprocess_timeout_is_exact():
    import subprocess
    from unittest.mock import patch

    from gpu_runmultiai.odeformer_runtime import simplify_tree_subprocess

    with patch("gpu_runmultiai.odeformer_runtime.subprocess.run") as mocked_run:
        mocked_run.side_effect = subprocess.TimeoutExpired(cmd="worker", timeout=5.0)
        result = simplify_tree_subprocess(["add,x_0,1"], timeout_sec=SIMPLIFIER_SUBPROCESS_TIMEOUT_SEC)
        assert mocked_run.call_args.kwargs["timeout"] == SIMPLIFIER_SUBPROCESS_TIMEOUT_SEC
        assert result["failure_reason"] == "SubprocessTimeout"


def test_sealed_guard_symlink_lexical_and_real_checks(tmp_path):
    output_root = tmp_path / "results" / "runs"
    denied_real = output_root / "gpu_run5_example" / "phase8" / "test" / "rows.json"
    denied_real.parent.mkdir(parents=True)
    denied_real.write_text("[]", encoding="utf-8")
    link_parent = output_root / "gpu_run5_linkdir"
    link_parent.mkdir(parents=True)
    symlink_path = link_parent / "alias.json"
    symlink_path.symlink_to(denied_real)
    guard = SealedPathGuard(output_root_abs=output_root.resolve())
    assert guard.is_denied(symlink_path, symlink_path)
    lexical_only = output_root / "gpu_run5_lexical" / "test" / "rows.json"
    lexical_only.parent.mkdir(parents=True)
    lexical_only.write_text("[]", encoding="utf-8")
    assert guard.is_denied(lexical_only, lexical_only)


def test_simplifier_preserves_child_guard_attempts_on_failure(tmp_path, monkeypatch):
    import gpu_runmultiai.odeformer_runtime as runtime

    attempts = [
        {
            "attempted_operation": "open",
            "attempted_path_norm": "/tmp/norm",
            "attempted_path_real": "/tmp/real",
        }
    ]
    payload = json.dumps({"ok": False, "failure_reason": "PermissionError", "guard_attempts": attempts})

    class _Proc:
        returncode = 1
        stdout = payload
        stderr = ""

    monkeypatch.setattr(runtime.subprocess, "run", lambda *args, **kwargs: _Proc())
    result = runtime.simplify_tree_subprocess(["add,x_0,1"], timeout_sec=5.0)
    assert result["guard_attempts"] == attempts


def test_component_level_linear_control_metrics():
    from gpu_runmultiai.odeformer_runtime import full_system_infix_from_record
    from gpu_runmultiai.pipeline import _component_metrics

    corpus = load_frozen_corpus()
    record = next(row for row in corpus["train_records"] if row["system_id"] == "R01_train_d61001_000")
    truth_full = full_system_infix_from_record(record)
    metrics = _component_metrics(record, truth_full, 0)
    assert metrics["canonical_exact"] == 1.0
    assert metrics["exponent_aware_skeleton_exact"] == 1.0


def test_terminal_row_on_invalid_rewrite():
    corpus = load_frozen_corpus()
    record = next(row for row in corpus["train_records"] if row["system_id"] == "R01_train_d61001_000")
    invalid_rewrite = {"rewrite_id": "rewrite_sha256:bad", "valid": False}
    row = run_b0_pair(
        corpus_hash=corpus["corpus_hash"],
        record=record,
        component_idx=0,
        scale="0.1",
        rewrite_row=invalid_rewrite,
        oracle_timeout_sec=30.0,
        q4_timeout_sec=Q4_TIMEOUT_SEC,
        simplifier_timeout_sec=SIMPLIFIER_SUBPROCESS_TIMEOUT_SEC,
        call_logger=CallLogger(),
        runtime_available=True,
        guard=SealedPathGuard(output_root_abs=Path("/nonexistent/results/runs")),
    )
    assert row["outcome_category"] == "construction_incomplete"
    assert row["pair_id"]


def test_oracle_token_preserving_rational_analytic_independent():
    result = oracle_equivalence("(0.1*x_0)", "((1/10)*x_0)", component_idx=0, timeout_sec=5.0)
    assert result.completed
    assert result.analytic_equivalent is True
    assert result.numeric_equivalent is True
    assert result.equivalent is True
    assert result.parsed_rationals.get("1/10") == "1/10"


def test_registration_all_components_accept_pow_dialect():
    corpus = load_frozen_corpus()
    logger = CallLogger()
    from gpu_runmultiai.audit import _attach_records
    from gpu_runmultiai.pipeline import registration_rows
    from gpu_runmultiai.stage_cache import load_stage_cache

    cache_path = Path("/tmp/lansr_registration_pow_test.jsonl")
    if cache_path.exists():
        cache_path.unlink()
    component_index = _attach_records(corpus["component_index"], corpus["train_records"])
    truth_rows, rewrite_rows = registration_rows(
        corpus["corpus_hash"],
        component_index,
        oracle_timeout_sec=30.0,
        call_logger=logger,
        stage_cache={},
        cache_path=cache_path,
    )
    assert len(truth_rows) == 510
    assert len(rewrite_rows) == 510
    assert all(row["valid"] for row in rewrite_rows)
    assert logger.total() == 1020
    assert len(load_stage_cache(cache_path)) == 1020


def test_n1_all_controls_reject_with_prefix_oracle():
    corpus = load_frozen_corpus()
    logger = CallLogger()
    from gpu_runmultiai.audit import _attach_records
    from gpu_runmultiai.pipeline import run_negative_controls

    component_index = _attach_records(corpus["component_index"], corpus["train_records"])
    rows = run_negative_controls(
        component_index,
        oracle_timeout_sec=30.0,
        call_logger=logger,
        stage_cache={},
        cache_path=None,
        limit=100,
    )
    assert len(rows) == 100
    assert all(row["oracle"]["completed"] for row in rows)
    assert all(not row["oracle"]["equivalent"] for row in rows)
    assert logger.total() == 100


def test_stage_cache_rejects_non_serializable_payload(tmp_path):
    from gpu_runmultiai.invariants import StageCacheSerializationError
    from gpu_runmultiai.stage_cache import append_stage_cache

    class _Bad:
        pass

    with pytest.raises(StageCacheSerializationError):
        append_stage_cache(tmp_path / "stage_cache.jsonl", cache_key_value="k", payload=_Bad())


def test_execute_or_record_records_failed_call_on_exception(tmp_path):
    logger = CallLogger(tmp_path / "call_log.jsonl")

    def _boom():
        raise ValueError("boom")

    with pytest.raises(ValueError):
        logger.execute_or_record(
            primitive="truth_register_classify",
            condition="registration",
            stage="truth",
            unit_type="component",
            unit_id="component_sha256:fail",
            executor=_boom,
        )
    reloaded = CallLogger.load(tmp_path / "call_log.jsonl")
    assert reloaded.total() == 1
    assert reloaded.rows[0]["status"] == "failed"
    assert reloaded.rows[0]["duration_sec"] is not None


def test_b2_ordinary_exception_terminalizes_without_abort():
    from gpu_runmultiai.pipeline import run_b2_pair

    b0_row = {
        "pair_id": "pair_sha256:deadbeef",
        "component_idx": 0,
        "e1_infix": None,
        "e0_status": "completed",
        "condition": "B0",
        "system_id": "R01_train_d61001_000",
        "component_id": "component_sha256:abc",
        "scale": "0.1",
        "rewrite_id": "rewrite_sha256:def",
        "stratum": "strict_hill",
    }
    corpus = load_frozen_corpus()
    record = next(row for row in corpus["train_records"] if row["system_id"] == "R01_train_d61001_000")
    logger = CallLogger()
    row = run_b2_pair(
        pair_id="pair_sha256:deadbeef",
        component_id="component_sha256:abc",
        system_id="R01_train_d61001_000",
        component_idx=0,
        scale="0.1",
        rewrite_id="rewrite_sha256:def",
        stratum="strict_hill",
        e1_infix=None,
        record=record,
        call_logger=logger,
    )
    assert row["condition"] == "B2"
    assert row.get("execution_failure") is True
    assert logger.total() == 2


def test_b3_failure_still_counts_call():
    from gpu_runmultiai.pipeline import run_b3_pairs

    selected = [
        {
            "pair_id": "pair_sha256:abc",
            "component_idx": 0,
            "truth_infix": "(x_0)",
            "e2_infix_pre_classifier": None,
            "condition": "B0",
            "stratum": "strict_hill",
        }
    ]
    logger = CallLogger()
    rows = run_b3_pairs(selected, call_logger=logger)
    assert len(rows) == 1
    assert rows[0].get("execution_failure") or rows[0].get("valid") is False
    assert logger.total() == 1


def test_invariant_exception_does_not_record_failed_call(tmp_path):
    from gpu_runmultiai.invariants import AuditInvariantError

    logger = CallLogger(tmp_path / "call_log.jsonl")

    def _boom():
        raise AuditInvariantError("ceiling")

    with pytest.raises(AuditInvariantError):
        logger.execute_or_record(
            primitive="truth_register_classify",
            condition="registration",
            stage="truth",
            unit_type="component",
            unit_id="component_sha256:invariant",
            executor=_boom,
        )
    assert CallLogger.load(tmp_path / "call_log.jsonl").total() == 0


def test_sealed_guard_repo_relative_path_denied_after_chdir(tmp_path, monkeypatch):
    import experiment_runtime
    import gpu_runmultiai.sealed_guard as sealed_guard_module

    monkeypatch.setattr(experiment_runtime, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(sealed_guard_module, "REPO_ROOT", tmp_path)
    output_root = tmp_path / "results" / "runs"
    denied = output_root / "gpu_run5_example" / "test" / "rows.json"
    denied.parent.mkdir(parents=True)
    denied.write_text("[]", encoding="utf-8")
    guard = SealedPathGuard(output_root_abs=output_root.resolve())
    guard.install()
    try:
        repo_relative = "results/runs/gpu_run5_example/test/rows.json"
        monkeypatch.chdir("/tmp")
        with pytest.raises(PermissionError):
            open(repo_relative, encoding="utf-8")
        assert guard.attempt_count() == 1
    finally:
        guard.restore()


def test_resume_replays_guard_side_channel(tmp_path):
    from gpu_runmultiai.audit import run_audit
    from gpu_runmultiai.guard_side_channel import append_guard_attempts, load_guard_attempts, side_channel_path

    output_dir = tmp_path / "resume_guard"
    options = {
        "output_dir": str(output_dir),
        "oracle_timeout_sec": 30.0,
        "simplifier_subprocess_timeout_sec": SIMPLIFIER_SUBPROCESS_TIMEOUT_SEC,
        "fail_if_exists": False,
        "resume": False,
        "smoke": True,
        "primary_scales": ("0.1",),
    }
    run_audit(options)
    append_guard_attempts(
        side_channel_path(output_dir),
        [
            {
                "attempted_operation": "open",
                "attempted_path_norm": "/tmp/norm",
                "attempted_path_real": "/tmp/real",
            }
        ],
    )
    resumed = run_audit({**options, "resume": True})
    manifest = json.loads((output_dir / "audit_manifest.json").read_text(encoding="utf-8"))
    assert manifest["status"] == "completed"
    assert any(
        item["attempted_path_norm"] == "/tmp/norm"
        for item in manifest["access_guard_attempts"]
    )
    assert resumed["manifest"]["status"] == "completed"


def test_manifest_completed_last_and_schema_columns(tmp_path):
    from gpu_runmultiai.audit import run_audit

    output_dir = tmp_path / "schema_smoke"
    run_audit(
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
    manifest = json.loads((output_dir / "audit_manifest.json").read_text(encoding="utf-8"))
    assert manifest["status"] == "completed"
    call_rows = [
        json.loads(line)
        for line in (output_dir / "call_log.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert all(row.get("duration_sec") is not None for row in call_rows)
    header = (output_dir / "pair_results.csv").read_text(encoding="utf-8").splitlines()[0]
    assert "failure_reason" in header
    assert "rescale_incomplete" in header
    assert "formula_metrics_valid" in header
    oracle_payload = json.loads((output_dir / "equivalence_oracle.json").read_text(encoding="utf-8"))
    assert oracle_payload
    assert "failure_reason" in oracle_payload[0]["E1"]
    assert "rational_tokens" in oracle_payload[0]["E1"]


def test_frozen_environment_mismatch_fails_fast(monkeypatch):
    from gpu_runmultiai.invariants import FrozenEnvironmentError
    from scripts.phases.gpu_runmultiai_c0001_metric_audit import _validate_frozen_environment

    monkeypatch.setenv("LANSR_TED_TIMEOUT_SEC", "999")
    with pytest.raises(FrozenEnvironmentError):
        _validate_frozen_environment()


def test_b1_uses_production_scaler_identity_rescale():
    from gpu_runmultiai.odeformer_runtime import ODEFormerUnavailable, build_production_scaler, require_odeformer

    try:
        require_odeformer()
    except ODEFormerUnavailable:
        pytest.skip("ODEFormer runtime unavailable")
    scaler, asserts = build_production_scaler(1.0, 3)
    assert asserts["rescale_features"] is True
    assert scaler.get_params()[2].tolist() == [1.0, 1.0, 1.0]


def test_f2_compound_pow_preserves_subtree_arity():
    prefix = "pow2,div,mul,10.0,x_0,10.0"
    tree = audit_parse_prefix_component(prefix)
    assert tree is not None
    assert tree[0] == "pow"
    assert tree[1][0][0] == "div"


def test_c_q4_all_fixtures_pass():
    from gpu_runmultiai.pipeline import run_c_q4_fixtures

    rows = run_c_q4_fixtures(call_logger=CallLogger(), q4_timeout_sec=Q4_TIMEOUT_SEC)
    assert len(rows) == 7
    assert all(row["fixture_pass"] for row in rows)


def test_q4_contract_error_global_abort():
    from gpu_runmultiai.q4_reference import Q4ContractError, verify_q4_emitted_prefix

    with pytest.raises(Q4ContractError):
        verify_q4_emitted_prefix("foobar,x_0")


def test_guard_bootstrap_singleton_and_deny(tmp_path):
    from experiment_runtime import REPO_ROOT
    from scripts.phases import guard_bootstrap as gb

    gb._INSTALLED_GUARD = None
    denied = REPO_ROOT / "results" / "runs" / "gpu_run5_example" / "test" / "rows.json"
    denied.parent.mkdir(parents=True, exist_ok=True)
    if not denied.is_file():
        denied.write_text("[]", encoding="utf-8")
    handle = gb.install_guard_from_entry(str(REPO_ROOT / "scripts/phases/gpu_runmultiai_c0001_metric_audit.py"))
    assert gb.get_installed_guard() is handle
    with pytest.raises(PermissionError):
        open(denied, encoding="utf-8")
    handle.restore()
    gb._INSTALLED_GUARD = None


def test_jsonl_partial_suffix_truncate(tmp_path):
    from gpu_runmultiai.invariants import AuditInvariantError
    from gpu_runmultiai.jsonl_durable import load_jsonl, truncate_partial_suffix

    path = tmp_path / "call_log.jsonl"
    path.write_bytes(b'{"a":1}\n{"b":2,')
    truncate_partial_suffix(path)
    rows = load_jsonl(path)
    assert rows == [{"a": 1}]


def test_jsonl_malformed_line_aborts(tmp_path):
    from gpu_runmultiai.invariants import AuditInvariantError
    from gpu_runmultiai.jsonl_durable import load_jsonl

    path = tmp_path / "bad.jsonl"
    path.write_text('{"a":1}\n{bad}\n', encoding="utf-8")
    with pytest.raises(AuditInvariantError):
        load_jsonl(path)


def test_source_inventory_has_guard_bootstrap():
    from gpu_runmultiai.source_inventory import enumerate_source_inventory_paths

    paths = enumerate_source_inventory_paths()
    assert "scripts/phases/guard_bootstrap.py" in paths
    assert len(paths) >= 82


def test_reachability_evidence_supported_and_unsupported():
    from gpu_runmultiai.reachability import build_reachability_evidence

    rows = build_reachability_evidence()
    by_id = {row["fixture_id"]: row for row in rows}
    assert by_id["REACH-UNS-1"]["passed"] is True
    assert by_id["REACH-SUP-1"]["passed"] is True
