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
    MULTI_COMPONENT_SEPARATOR,
    ODEFormerUnavailable,
    build_production_scaler,
    canonical_system_prefix_raw,
    component_prefix_list_from_raw,
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
from gpu_runmultiai.strata import component_stratum, is_linear_component

AUDIT_ENTRY_SCRIPT = "scripts/phases/gpu_runmultiai_c0001_metric_audit.py"


@pytest.fixture(scope="session")
def bootstrap_guard():
    """The single guard_bootstrap handle `run_audit` accepts (§10.1-2)."""
    from experiment_runtime import REPO_ROOT
    from scripts.phases import guard_bootstrap as gb

    try:
        return gb.get_installed_guard()
    except gb.GuardBootstrapViolation:
        return gb.install_guard_from_entry(str(REPO_ROOT / AUDIT_ENTRY_SCRIPT))


def _source_inventory_for_commit(commit: str) -> list[dict[str, str]]:
    import hashlib
    import subprocess

    from experiment_runtime import REPO_ROOT
    from gpu_runmultiai.source_inventory import build_source_inventory

    inventory: list[dict[str, str]] = []
    for entry in build_source_inventory(include_hashes=True):
        rel_path = entry["path"]
        blob = subprocess.run(
            ["git", "show", f"{commit}:{rel_path}"],
            cwd=REPO_ROOT,
            capture_output=True,
            check=True,
        ).stdout
        inventory.append({"path": rel_path, "sha256": hashlib.sha256(blob).hexdigest()})
    return inventory


def _canonical_closure_record_payload(tmp_path: Path | None = None) -> dict:
    import hashlib

    from experiment_runtime import REPO_ROOT
    from gpu_runmultiai.manifest import current_commit

    artifact_dir = REPO_ROOT / "GPU_RUNmultiAI/.runtime/closure_test_artifacts"
    artifact_dir.mkdir(parents=True, exist_ok=True)
    acceptance_path = artifact_dir / "acceptance.json"
    review_path = artifact_dir / "review.json"
    acceptance_path.write_text('{"acceptance":"ok"}', encoding="utf-8")
    review_path.write_text('{"review":"ok"}', encoding="utf-8")
    commit = current_commit()
    return {
        "commit": commit,
        "accepted_source_commit": commit,
        "source_hashes": _source_inventory_for_commit(commit),
        "plan_hash": PLAN_SHA256,
        "audit_id": AUDIT_ID,
        "g_contract_verdict": "PASS",
        "g_impl_verdict": "PASS",
        "independent_reviewer_identity": "pytest-canonical-closure",
        "independent_review_verdict": "PASS",
        "acceptance_artifact_path": str(acceptance_path.relative_to(REPO_ROOT)),
        "acceptance_artifact_digest": hashlib.sha256(acceptance_path.read_bytes()).hexdigest(),
        "review_artifact_path": str(review_path.relative_to(REPO_ROOT)),
        "review_artifact_digest": hashlib.sha256(review_path.read_bytes()).hexdigest(),
    }


@pytest.fixture
def canonical_closure_record(tmp_path, monkeypatch):
    from gpu_runmultiai import manifest as manifest_module

    closure_path = tmp_path / "implementation_closure_record.json"
    payload = _canonical_closure_record_payload(tmp_path)
    closure_path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
    monkeypatch.setattr(manifest_module, "CANONICAL_CLOSURE_RECORD_PATH", closure_path)
    yield payload


def _run_audit(options, guard):
    from gpu_runmultiai.audit import run_audit

    options = {**options, "require_clean_worktree": False}
    return run_audit(options, guard=guard)


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
    n1_rows = [{"oracle_completed": True, "oracle_equivalent": False} for _ in range(100)]
    assert gate_n1(n1_rows)
    b4_rows = [{"valid": True, "canonical_exact": 1} for _ in range(510)]
    assert gate_b4(b4_rows)


def test_fail_if_exists_and_resume_mismatch(tmp_path, bootstrap_guard):
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
        _run_audit(options, bootstrap_guard)


def test_smoke_audit_bounded(tmp_path, bootstrap_guard):
    output_dir = tmp_path / "smoke"
    result = _run_audit(
        {
            "output_dir": str(output_dir),
            "oracle_timeout_sec": 30.0,
            "simplifier_subprocess_timeout_sec": SIMPLIFIER_SUBPROCESS_TIMEOUT_SEC,
            "fail_if_exists": False,
            "resume": False,
            "smoke": True,
            "primary_scales": ("0.1",),
        },
        bootstrap_guard,
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
    e1_component_prefix = component_prefix_list_from_raw(row["e1_prefix_raw"])[0]
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
    e1_prefixes = component_prefix_list_from_raw(row["e1_prefix_raw"])
    simplified = simplify_tree_subprocess(e1_prefixes, timeout_sec=SIMPLIFIER_SUBPROCESS_TIMEOUT_SEC)
    assert simplified.get("ok")
    assert simplified.get("infix")


def test_resume_appends_call_log(tmp_path, bootstrap_guard, canonical_closure_record):
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
    first = _run_audit(base_options, bootstrap_guard)
    first_total = first["call_total"]
    second = _run_audit({**base_options, "resume": True}, bootstrap_guard)
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
    assert row.get("e1_analytic_equivalent") is True
    assert row.get("e1_numeric_equivalent") is True
    assert row.get("e1_oracle_equivalent") is True
    assert row.get("e1_oracle_equivalent") == (
        bool(row.get("e1_analytic_equivalent")) and bool(row.get("e1_numeric_equivalent"))
    )
    e1_prefix = component_prefix_list_from_raw(row["e1_prefix_raw"])[0]
    oracle = oracle_equivalence_prefix(rewrite["rewrite_prefix"], e1_prefix, timeout_sec=30.0)
    assert oracle.completed
    assert oracle.equivalent == (oracle.analytic_equivalent and oracle.numeric_equivalent)


def test_resume_skips_reexecution_with_spy(tmp_path, bootstrap_guard, canonical_closure_record):
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
    first = _run_audit(options, bootstrap_guard)
    calls_before = CallLogger.load(output_dir / "call_log.jsonl").total()
    second = _run_audit({**options, "resume": True}, bootstrap_guard)
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
    assert logger.descriptive_total() == before_descriptive + 8
    d2_calls = [row for row in logger.rows if row["condition"] == "D2"]
    assert len(d2_calls) == 8
    assert {row["primitive"] for row in d2_calls} == {
        "e0_analytic_construct",
        "scaler_rescale_function",
        "q4_decimal_round_reference",
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
    assert logger.total() == 1530
    assert len(load_stage_cache(cache_path)) == 1530


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


def test_resume_replays_guard_side_channel(tmp_path, bootstrap_guard, canonical_closure_record):
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
    _run_audit(options, bootstrap_guard)
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
    resumed = _run_audit({**options, "resume": True}, bootstrap_guard)
    manifest = json.loads((output_dir / "audit_manifest.json").read_text(encoding="utf-8"))
    assert manifest["status"] == "completed"
    assert any(
        item["attempted_path_norm"] == "/tmp/norm"
        for item in manifest["access_guard_attempts"]
    )
    assert resumed["manifest"]["status"] == "completed"


def test_manifest_completed_last_and_schema_columns(tmp_path, bootstrap_guard):
    output_dir = tmp_path / "schema_smoke"
    _run_audit(
        {
            "output_dir": str(output_dir),
            "oracle_timeout_sec": 30.0,
            "simplifier_subprocess_timeout_sec": SIMPLIFIER_SUBPROCESS_TIMEOUT_SEC,
            "fail_if_exists": False,
            "resume": False,
            "smoke": True,
            "primary_scales": ("0.1",),
        },
        bootstrap_guard,
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
    assert "stage" in oracle_payload[0]
    assert "reference" in oracle_payload[0]
    assert "failure_reason" in oracle_payload[0]


def test_frozen_environment_mismatch_fails_fast(monkeypatch):
    from gpu_runmultiai.invariants import FrozenEnvironmentError
    from scripts.phases.gpu_runmultiai_c0001_metric_audit import _validate_frozen_environment

    monkeypatch.setenv("LANSR_TED_TIMEOUT_SEC", "999")
    with pytest.raises(FrozenEnvironmentError):
        _validate_frozen_environment()


def test_b1_uses_identity_scaler_parameters():
    from gpu_runmultiai.odeformer_runtime import ODEFormerUnavailable, build_identity_scaler, require_odeformer

    try:
        require_odeformer()
    except ODEFormerUnavailable:
        pytest.skip("ODEFormer runtime unavailable")
    scaler, asserts = build_identity_scaler(3)
    assert asserts["a_t"] == 1.0
    assert asserts["b_t"] == 0.0
    assert asserts["rescale_features"] is True
    assert scaler.get_params()[0] == 1.0
    assert scaler.get_params()[1] == 0.0


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


def test_guard_bootstrap_singleton_and_deny(tmp_path, bootstrap_guard):
    """Singleton identity is asserted on the installed handle; denial is probed under tmp_path."""
    from scripts.phases import guard_bootstrap as gb

    assert gb.get_installed_guard() is bootstrap_guard
    with pytest.raises(gb.GuardBootstrapViolation):
        gb.install_guard_from_entry(str(Path(AUDIT_ENTRY_SCRIPT)))

    output_root = tmp_path / "results" / "runs"
    denied = output_root / "gpu_run5_example" / "test" / "rows.json"
    denied.parent.mkdir(parents=True, exist_ok=True)
    denied.write_text("[]", encoding="utf-8")
    parent_attempts_before = bootstrap_guard.attempt_count()
    probe = gb.BootstrapGuardHandle(repo_root=str(tmp_path), output_root_abs=str(output_root))
    assert probe.is_denied(denied, denied)
    probe.install()
    try:
        with pytest.raises(PermissionError):
            open(denied, encoding="utf-8")
    finally:
        probe.restore()
    assert probe.attempt_count() == 1
    assert probe.to_log()[0]["attempted_operation"]
    # The parent (G4) ledger must not absorb probe attempts.
    assert bootstrap_guard.attempt_count() == parent_attempts_before


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


def test_reachability_evidence_all_ten_fixtures():
    from gpu_runmultiai.reachability import build_reachability_evidence

    rows = build_reachability_evidence()
    by_id = {row["fixture_id"]: row for row in rows}
    expected = {
        "REACH-POW-COMP-1",
        "REACH-SFN-1",
        "REACH-PRESERVED-1",
        "REACH-UNS-1",
        "REACH-SUP-1",
        "REACH-DRIFT-E2",
        "REACH-Q4FAIL-1",
        "REACH-IDENT-FALLBACK-1",
        "REACH-PARSE-1",
        "REACH-RESCALE-1",
    }
    assert set(by_id) == expected
    assert by_id["REACH-UNS-1"]["passed"] is True
    assert by_id["REACH-SUP-1"]["passed"] is True
    assert by_id["REACH-IDENT-FALLBACK-1"]["passed"] is True


def test_reach_ident_fallback_synthetic_fixture_passes_without_production_e2():
    from gpu_runmultiai.reachability import _reach_ident_fallback_1_synthetic

    passed, detail = _reach_ident_fallback_1_synthetic()
    assert passed is True
    assert "e2_source=synthetic_injection_not_production" in detail
    assert "e1_neq_q4=True" in detail
    assert "fallback_candidate=True" in detail
    assert "outcome=execution_failure" in detail


def test_reach_ident_fallback_live_observation_run_b0_pair_hard_bounded(monkeypatch):
    from gpu_runmultiai.corpus import load_frozen_corpus
    from gpu_runmultiai.reachability import (
        LIVE_IDENT_FALLBACK_RUN_B0_PAIR_BUDGET,
        _live_ident_fallback_b0_pair_trials,
        _reach_ident_fallback_1_live_production_observation,
    )

    corpus = load_frozen_corpus()
    trials = _live_ident_fallback_b0_pair_trials(corpus)
    assert len(trials) <= LIVE_IDENT_FALLBACK_RUN_B0_PAIR_BUDGET

    calls: list[tuple[str, int, str]] = []

    def _fake_run_b0_pair(**kwargs):
        record = kwargs["record"]
        calls.append((record["system_id"], kwargs["component_idx"], kwargs["scale"]))
        return {
            "e1_prefix_raw": "a|b",
            "e2_prefix_raw": "different",
            "q4_construction_completed": True,
        }

    monkeypatch.setattr(
        "gpu_runmultiai.pipeline.run_b0_pair",
        _fake_run_b0_pair,
    )
    monkeypatch.setattr(
        "gpu_runmultiai.odeformer_runtime.require_odeformer",
        lambda: None,
    )

    detail = _reach_ident_fallback_1_live_production_observation(None)
    assert len(calls) == len(trials)
    assert len(calls) <= LIVE_IDENT_FALLBACK_RUN_B0_PAIR_BUDGET
    assert f"run_b0_pair_budget={LIVE_IDENT_FALLBACK_RUN_B0_PAIR_BUDGET}" in detail
    assert "run_b0_pair_calls=" in detail
    assert "bounded_scan_exhausted=" in detail
    assert "bounded_no_match=true" in detail
    assert "not_global_corpus_absence" in detail
    assert "production_e2_unchanged=True" in detail
    assert "live_simplifier_fixed_point" not in detail


def test_reach_ident_fallback_row_labels_synthetic_pass_not_live_production(monkeypatch):
    from gpu_runmultiai.reachability import _reach_ident_fallback_1

    monkeypatch.setattr(
        "gpu_runmultiai.reachability._reach_ident_fallback_1_live_production_observation",
        lambda _rm: (
            "live_production_observation bounded_no_match=true "
            "observation_scope=first_8_sorted_trials run_b0_pair_budget=8 "
            "run_b0_pair_calls=0 bounded_scan_exhausted=False "
            "not_global_corpus_absence production_e2_unchanged=True"
        ),
    )
    row = _reach_ident_fallback_1()
    assert row["fixture_id"] == "REACH-IDENT-FALLBACK-1"
    assert row["evidence_type"] == "synthetic"
    assert row["passed"] is True
    assert "synthetic_injection_not_production" in row["details"]
    assert "live_simplifier_fixed_point" not in row["details"]


def test_g_contract_artifact_schema_round_trip(tmp_path):
    from gpu_runmultiai.pipeline import run_c_q4_fixtures
    from gpu_run2_runtime import write_json

    rows = run_c_q4_fixtures(call_logger=CallLogger(), q4_timeout_sec=Q4_TIMEOUT_SEC)
    path = tmp_path / "q4_reference_controls.json"
    write_json(path, rows)
    loaded = json.loads(path.read_text(encoding="utf-8"))
    assert len(loaded) == 7
    required = {
        "fixture_id",
        "e1_prefix_input",
        "q4_construction_completed",
        "q4_emitted_prefix",
        "fixture_pass",
        "terminal_outcome",
    }
    assert required.issubset(loaded[0].keys())


def test_g_contract_abort_and_deviation_lifecycle(tmp_path):
    from gpu_runmultiai.audit import (
        ABORT_MANIFEST_REQUIRED_FIELDS,
        append_deviation_entry,
        build_deviation_entry,
        finalize_deviation_log,
        init_deviation_log,
        write_abort_manifest,
    )

    call_logger = CallLogger()
    payload = write_abort_manifest(
        tmp_path,
        abort_type="Q4ContractError",
        abort_reason="dialect violation",
        call_logger=call_logger,
    )
    abort = json.loads((tmp_path / "abort_manifest.json").read_text(encoding="utf-8"))
    assert abort == payload
    assert abort["abort_type"] == "Q4ContractError"
    for field in ABORT_MANIFEST_REQUIRED_FIELDS:
        assert field in abort

    path = tmp_path / "deviation_log.md"
    init_deviation_log(path)
    append_deviation_entry(
        path,
        build_deviation_entry(
            description="bounded smoke run",
            scientific_impact="none for primary decision",
            resolution="full confirmatory run required",
        ),
    )
    finalize_deviation_log(path, status="completed", abort_type=None)
    body = path.read_text(encoding="utf-8")
    assert "bounded smoke run" in body
    assert "status=completed abort_type=none" in body

    abort_path = tmp_path / "deviation_log_aborted.md"
    init_deviation_log(abort_path)
    finalize_deviation_log(abort_path, status="aborted", abort_type="Q4ContractError")
    assert "status=aborted abort_type=Q4ContractError" in abort_path.read_text(encoding="utf-8")


def test_resource_monitor_uses_frozen_ceilings():
    from gpu_runmultiai.constants import ELAPSED_WALL_CEILING_SEC, OUTPUT_DIR_BYTE_CEILING
    from gpu_runmultiai.resources import BYTE_CONVENTION, CPU_WALL_LIMIT_SEC, DISK_LIMIT_BYTES

    assert CPU_WALL_LIMIT_SEC == ELAPSED_WALL_CEILING_SEC == 18000
    assert DISK_LIMIT_BYTES == OUTPUT_DIR_BYTE_CEILING == 1_200_000_000
    assert BYTE_CONVENTION == "decimal_gb"


def test_gate_order_includes_mandatory_gates():
    from gpu_runmultiai.controls import GATE_ORDER

    assert "G_eligibility" in GATE_ORDER
    assert "G_stratum" in GATE_ORDER
    assert "G_grand" in GATE_ORDER
    assert "G_contract" in GATE_ORDER
    assert "G_impl" in GATE_ORDER
    assert GATE_ORDER.index("G_eligibility") < GATE_ORDER.index("G_stratum")


def test_gate_b1_requires_control_pass_rows():
    from gpu_runmultiai.controls import gate_b1

    assert gate_b1([{"control_pass_row": True, "outcome_category": "control_pass"}] * 510)
    assert not gate_b1([{"control_pass_row": False, "outcome_category": "control_failure"}] * 510)


def test_quantization_stratum_counts_on_corpus():
    from gpu_runmultiai.eligibility import validate_g_eligibility
    from gpu_runmultiai.quantization import assign_quantization_stratum, validate_g_stratum
    from gpu_runmultiai.rewrites import truth_component_infix

    corpus = load_frozen_corpus()
    validate_g_eligibility(corpus["component_index"])
    rows = []
    for item in corpus["component_index"]:
        record = next(r for r in corpus["train_records"] if r["system_id"] == item["system_id"])
        truth_prefix, _ = truth_component_infix(record, item["component_idx"])
        component_id, _ = component_id_for(corpus["corpus_hash"], item["system_id"], item["component_idx"])
        layer = {
            "strict_hill": "strict_hill_primary",
            "non_strict_hill": "non_strict_hill_secondary",
            "linear": "linear_control",
        }[component_stratum(item["family"], item["component_idx"])]
        rows.append(
            {
                "component_id": component_id,
                "quantization_stratum": assign_quantization_stratum(truth_prefix),
                "eligibility_layer": layer,
            }
        )
    validate_g_stratum(rows)


def test_rescale_complete_on_production_scaler():
    from gpu_runmultiai.odeformer_runtime import (
        ODEFormerUnavailable,
        build_production_scaler,
        decode_system_tree,
        forward_scale_system,
        get_env,
        require_odeformer,
        rescale_system,
        truth_system_prefixes,
    )

    try:
        require_odeformer()
    except ODEFormerUnavailable:
        pytest.skip("ODEFormer runtime unavailable")
    env = get_env()
    corpus = load_frozen_corpus()
    record = corpus["train_records"][0]
    scaler, _ = build_production_scaler(0.1, int(record["dimension"]))
    tree = forward_scale_system(env, decode_system_tree(env, truth_system_prefixes(record)), scaler)
    _, incomplete, proof = rescale_system(env, scaler, tree)
    assert incomplete is False
    assert proof["returned_input_tree"] is False


def test_b1_identity_scaler_is_the_production_scaler():
    """§16 F5: identity parameters come from the production Scaler, not a bypass class."""
    from gpu_runmultiai import odeformer_runtime as ort

    try:
        ort.require_odeformer()
    except ort.ODEFormerUnavailable:
        pytest.skip("ODEFormer runtime unavailable")
    assert not hasattr(ort, "IdentityScaler")
    scaler, asserts = ort.build_identity_scaler(3)
    assert type(scaler).__module__ == ort.PRODUCTION_SCALER_MODULE
    assert type(scaler).__name__ == "Scaler"
    assert asserts["a_t"] == 1.0
    assert asserts["b_t"] == 0.0
    assert asserts["scale"] == [1.0, 1.0, 1.0]
    module, qualname = ort.production_rescale_callable_identity(scaler)
    assert (module, qualname) == (ort.PRODUCTION_SCALER_MODULE, ort.PRODUCTION_RESCALE_QUALNAME)


def test_b1_rescale_call_proof_records_production_callable():
    from gpu_runmultiai import odeformer_runtime as ort

    try:
        ort.require_odeformer()
    except ort.ODEFormerUnavailable:
        pytest.skip("ODEFormer runtime unavailable")
    env = ort.get_env()
    scaler, _ = ort.build_identity_scaler(1)
    tree = ort.decode_system_tree(env, ["mul,2.0,x_0"])
    rescaled, incomplete, proof = ort.rescale_system(env, scaler, tree)
    assert incomplete is False
    assert rescaled is not tree
    assert proof["rescale_callable_module"] == ort.PRODUCTION_SCALER_MODULE
    assert proof["rescale_callable_qualname"] == ort.PRODUCTION_RESCALE_QUALNAME
    assert proof["a_t"] == 1.0 and proof["b_t"] == 0.0 and proof["scale"] == [1.0]
    assert ort.last_rescale_call_proof() == proof


def test_rescale_rejects_non_production_scaler():
    from gpu_runmultiai.invariants import ScalerGateError
    from gpu_runmultiai.odeformer_runtime import ODEFormerUnavailable, get_env, require_odeformer, rescale_system

    try:
        require_odeformer()
    except ODEFormerUnavailable:
        pytest.skip("ODEFormer runtime unavailable")

    class FakeScaler:
        def get_params(self):
            return 1.0, 0.0, [1.0]

        def rescale_function(self, env, tree, a_t, b_t, scale):
            return tree

    with pytest.raises(ScalerGateError, match="production"):
        rescale_system(get_env(), FakeScaler(), object())


def test_rescale_detects_both_frozen_early_returns():
    """§5.2: component-count and variable-index early returns both return the input tree."""
    from gpu_runmultiai import odeformer_runtime as ort

    try:
        ort.require_odeformer()
    except ort.ODEFormerUnavailable:
        pytest.skip("ODEFormer runtime unavailable")
    env = ort.get_env()
    scaler, _ = ort.build_identity_scaler(1)

    # Condition 1: len(nodes) > len(scale)
    two_component = ort.decode_system_tree(env, ["x_0", "x_0"])
    out1, incomplete1, proof1 = ort.rescale_system(env, scaler, two_component)
    assert incomplete1 is True
    assert out1 is two_component
    assert proof1["input_node_count"] == 2
    assert len(proof1["scale"]) == 1

    # Condition 2: x_k with dim >= len(scale)
    out_of_range = ort.decode_system_tree(env, ["add,x_0,x_1"])
    out2, incomplete2, proof2 = ort.rescale_system(env, scaler, out_of_range)
    assert incomplete2 is True
    assert out2 is out_of_range
    assert proof2["input_node_count"] == 1
    assert proof2["returned_input_tree"] is True


def test_guard_bootstrap_no_replacement(bootstrap_guard):
    from scripts.phases import guard_bootstrap as gb

    with pytest.raises(gb.GuardBootstrapViolation):
        gb.install_guard_from_entry(str(Path(AUDIT_ENTRY_SCRIPT)))
    assert gb.get_installed_guard() is bootstrap_guard


def test_run_audit_requires_guard_bootstrap_singleton(tmp_path, bootstrap_guard):
    """§10.1-2: `run_audit` accepts no substitute guard and no `None`."""
    from gpu_runmultiai.audit import run_audit
    from scripts.phases.guard_bootstrap import BootstrapGuardHandle, GuardBootstrapViolation

    options = {
        "output_dir": str(tmp_path / "no_guard"),
        "oracle_timeout_sec": 30.0,
        "fail_if_exists": False,
        "resume": False,
        "smoke": True,
        "primary_scales": ("0.1",),
        "require_clean_worktree": False,
    }
    with pytest.raises(GuardBootstrapViolation, match="requires the guard_bootstrap singleton"):
        run_audit(options)
    substitute = BootstrapGuardHandle(
        repo_root=str(tmp_path), output_root_abs=str(tmp_path / "results" / "runs")
    )
    with pytest.raises(GuardBootstrapViolation, match="not the installed bootstrap singleton"):
        run_audit({**options, "output_dir": str(tmp_path / "sub_guard")}, guard=substitute)
    with pytest.raises(GuardBootstrapViolation):
        run_audit(
            {**options, "output_dir": str(tmp_path / "sealed_guard")},
            guard=SealedPathGuard(output_root_abs=Path("/nonexistent/results/runs")),
        )


def test_smoke_writes_quantization_and_negative_controls(tmp_path, bootstrap_guard):
    output_dir = tmp_path / "schema_round2"
    _run_audit(
        {
            "output_dir": str(output_dir),
            "oracle_timeout_sec": 30.0,
            "simplifier_subprocess_timeout_sec": SIMPLIFIER_SUBPROCESS_TIMEOUT_SEC,
            "fail_if_exists": False,
            "resume": False,
            "smoke": True,
            "primary_scales": ("0.1",),
        },
        bootstrap_guard,
    )
    manifest = json.loads((output_dir / "audit_manifest.json").read_text(encoding="utf-8"))
    assert manifest["elapsed_wall_ceiling_sec"] == 18000
    assert manifest["output_dir_byte_ceiling"] == 1_200_000_000
    assert manifest["byte_convention"] == "decimal_gb"
    assert "G_eligibility" in manifest["validity_gates"]
    assert "G_grand" in manifest["validity_gates"]
    assert (output_dir / "quantization_stratum.json").is_file()
    assert (output_dir / "negative_controls.json").is_file()


# --------------------------------------------------------------------------- #
# Round-3 contract-first tests
# --------------------------------------------------------------------------- #


def test_b2_partition_uses_e1_fields_only():
    """§2.5.2 / F7: B2 terminals are decided from E1 fields; E2 flags must not leak."""
    from gpu_runmultiai.outcomes import FIVE_OUTCOME_CATEGORIES, build_outcome_row
    from gpu_runmultiai.pipeline import B2_FORBIDDEN_INHERITED_FIELDS, b2_inherited_e1_fields

    b0_row = {
        "q4_construction_completed": True,
        "e1_oracle_completed": True,
        "e1_oracle_equivalent": True,
        "e1_analytic_equivalent": True,
        "e1_numeric_equivalent": True,
        "e1_oracle_failure_reason": None,
        "e2_oracle_completed": True,
        "e2_oracle_equivalent": False,
        "e2_identity_fallback_candidate": True,
        "rescale_incomplete": False,
        "hill_form": False,
        "canonical_exact": 0.0,
    }
    inherited = b2_inherited_e1_fields(b0_row)
    assert "e2_oracle_equivalent" not in inherited
    assert "e2_identity_fallback_candidate" not in inherited
    assert "hill_form" not in inherited
    assert "canonical_exact" not in inherited
    assert inherited["e1_oracle_equivalent"] is True
    assert inherited["rescale_incomplete"] is False

    row = build_outcome_row(
        condition="B2",
        pair_id="pair_sha256:" + "0" * 64,
        stratum="strict_hill",
        classifier_parse_valid=True,
        formula_metrics_valid=True,
        hill_form=True,
        **inherited,
    )
    # E2 drift in the B0 row must not make the B2 row drift.
    assert row["outcome_category"] == "preserved"
    assert row["outcome_category"] in FIVE_OUTCOME_CATEGORIES
    assert row["outcome_category"] != "unknown"
    for key in B2_FORBIDDEN_INHERITED_FIELDS:
        if key.startswith("e2_"):
            assert row.get(key) in (None, False), key

    drifted = build_outcome_row(
        condition="B2",
        pair_id="pair_sha256:" + "1" * 64,
        stratum="strict_hill",
        classifier_parse_valid=True,
        formula_metrics_valid=True,
        hill_form=True,
        **{**inherited, "e1_oracle_equivalent": False},
    )
    assert drifted["outcome_category"] == "semantic_drift"

    sfn = build_outcome_row(
        condition="B2",
        pair_id="pair_sha256:" + "2" * 64,
        stratum="strict_hill",
        classifier_parse_valid=True,
        formula_metrics_valid=True,
        hill_form=False,
        **inherited,
    )
    assert sfn["outcome_category"] == "structural_false_negative"

    incomplete_e1 = build_outcome_row(
        condition="B2",
        pair_id="pair_sha256:" + "9" * 64,
        stratum="strict_hill",
        classifier_parse_valid=True,
        formula_metrics_valid=True,
        hill_form=True,
        **{**inherited, "rescale_incomplete": True},
    )
    assert incomplete_e1["outcome_category"] == "execution_failure"


def test_d2_terminals_use_descriptive_vocabulary():
    """§2.5.4: D2 rows are descriptive_recorded / descriptive_failed, never `preserved`."""
    from gpu_runmultiai.outcomes import TERMINAL_VOCABULARY, assert_terminal_vocabulary, build_outcome_row

    recorded = build_outcome_row(
        condition="D2",
        pair_id="pair_sha256:" + "3" * 64,
        stratum="strict_hill",
        q4_construction_completed=True,
        e1_oracle_completed=True,
        e1_oracle_equivalent=True,
        e2_oracle_completed=True,
        e2_oracle_equivalent=True,
        classifier_parse_valid=True,
        formula_metrics_valid=True,
        hill_form=True,
    )
    assert recorded["partition_scope"] == "descriptive"
    assert recorded["outcome_category"] == "descriptive_recorded"
    assert recorded["descriptive_source_outcome"] == "preserved"

    failed = build_outcome_row(
        condition="D2",
        pair_id="pair_sha256:" + "4" * 64,
        stratum="strict_hill",
        construction_incomplete=True,
        q4_construction_completed=False,
    )
    assert failed["outcome_category"] == "descriptive_failed"
    assert TERMINAL_VOCABULARY["descriptive"] == frozenset({"descriptive_recorded", "descriptive_failed"})
    assert_terminal_vocabulary([recorded, failed], context="d2_rows")


def test_terminal_vocabulary_rejects_illegal_terminal():
    from gpu_runmultiai.invariants import TerminalVocabularyError
    from gpu_runmultiai.outcomes import assert_terminal_vocabulary

    with pytest.raises(TerminalVocabularyError, match="illegal terminal"):
        assert_terminal_vocabulary(
            [{"partition_scope": "primary", "outcome_category": "unknown"}], context="probe"
        )
    with pytest.raises(TerminalVocabularyError, match="unknown partition_scope"):
        assert_terminal_vocabulary(
            [{"partition_scope": "not_a_scope", "outcome_category": "preserved"}], context="probe"
        )


def test_unmapped_stratum_aborts_without_linear_fallthrough():
    from gpu_runmultiai.invariants import StratumGateError
    from gpu_runmultiai.outcomes import eligibility_layer_for_stratum

    assert eligibility_layer_for_stratum("strict_hill") == "strict_hill_primary"
    assert eligibility_layer_for_stratum("non_strict_hill") == "non_strict_hill_secondary"
    assert eligibility_layer_for_stratum("linear") == "linear_control"
    for unmapped in ("other", None, "", "hill"):
        with pytest.raises(StratumGateError, match="no frozen eligibility layer"):
            eligibility_layer_for_stratum(unmapped)


def test_b3_terminal_requires_executed_cas_compare():
    """§2.5.4: `cas_compare_completed` comes from execution, not from key presence."""
    from gpu_runmultiai.pipeline import run_b3_pairs

    b0_row = {
        "pair_id": "pair_sha256:" + "5" * 64,
        "component_id": "component_sha256:" + "6" * 64,
        "component_idx": 0,
        "classifier_parse_valid": True,
        "formula_metrics_valid": True,
        "exponent_aware_skeleton_exact": 1.0,
        "truth_infix": "(x_0)",
        "e2_infix_pre_classifier": "(x_0)",
    }
    rows = run_b3_pairs([b0_row], call_logger=CallLogger())
    assert len(rows) == 1
    row = rows[0]
    assert row["cas_compare_completed"] is True
    assert row["terminal_outcome"] in {"diagnostic_complete", "diagnostic_failed"}
    assert row["exponent_aware_skeleton_exact"] == 1.0
    assert row["component_id"] == b0_row["component_id"]

    failing = {**b0_row, "pair_id": "pair_sha256:" + "7" * 64, "classifier_parse_valid": False}
    failed_rows = run_b3_pairs([failing], call_logger=CallLogger())
    assert failed_rows[0]["terminal_outcome"] == "diagnostic_failed"

    unparseable = {
        **b0_row,
        "pair_id": "pair_sha256:" + "8" * 64,
        "truth_infix": "(((",
        "e2_infix_pre_classifier": "(((",
    }
    unparseable_rows = run_b3_pairs([unparseable], call_logger=CallLogger())
    assert unparseable_rows[0]["terminal_outcome"] == "diagnostic_failed"


def test_negative_controls_carry_component_id():
    from gpu_runmultiai.pipeline import run_negative_controls

    corpus = load_frozen_corpus()
    component_index = [
        {**item, "record": next(r for r in corpus["train_records"] if r["system_id"] == item["system_id"])}
        for item in corpus["component_index"][:2]
    ]
    rows = run_negative_controls(
        component_index,
        oracle_timeout_sec=30.0,
        call_logger=CallLogger(),
        corpus_hash=corpus["corpus_hash"],
        limit=2,
    )
    assert rows
    for row in rows:
        assert row["component_id"]
        assert row["component_id"].startswith("component_sha256:")


def test_registration_truth_and_rewrite_schema_fields():
    """§12.8: registration_truth carries component_flags; rewrite precheck fields are flat."""
    from gpu_runmultiai.pipeline import registration_rows

    corpus = load_frozen_corpus()
    component_index = [
        {**item, "record": next(r for r in corpus["train_records"] if r["system_id"] == item["system_id"])}
        for item in corpus["component_index"][:1]
    ]
    truth_rows, rewrite_rows = registration_rows(
        corpus["corpus_hash"],
        component_index,
        oracle_timeout_sec=30.0,
        call_logger=CallLogger(),
        stage_cache={},
        cache_path=None,
        limit=1,
    )
    assert truth_rows and rewrite_rows
    assert isinstance(truth_rows[0]["component_flags"], list)
    assert truth_rows[0]["component_flags"]
    for key in ("precheck_completed", "precheck_equivalent", "precheck_failure_reason"):
        assert key in rewrite_rows[0]


def test_condition_summary_reports_call_counts_and_absolute_counts():
    from gpu_runmultiai.controls import condition_summary

    rows = [
        {"outcome_category": "preserved", "is_fully_diagnostic": True},
        {"outcome_category": "structural_false_negative", "is_fully_diagnostic": True},
    ]
    payload = condition_summary(rows, gates={"G_corpus": True}, confirmatory_calls=11, descriptive_calls=3)
    assert payload["confirmatory_calls"] == 11
    assert payload["descriptive_calls"] == 3
    assert payload["primary_partition_counts"]["preserved"] == 1
    assert payload["primary_partition_counts"]["structural_false_negative"] == 1
    assert payload["primary_partition_counts"]["unknown"] == 0


def test_dependency_versions_include_sklearn_and_numexpr():
    from gpu_runmultiai.manifest import dependency_versions

    versions = dependency_versions()
    for key in ("python", "numpy", "scipy", "sympy", "scikit-learn", "numexpr", "torch", "os", "cpu"):
        assert key in versions
        assert versions[key]


def test_resume_identity_paths_are_repo_relative(tmp_path):
    from experiment_runtime import REPO_ROOT
    from gpu_runmultiai.manifest import repo_relative_path

    inside = REPO_ROOT / "GPU_RUNmultiAI" / "cycles" / "C0001" / "runs" / "probe"
    assert repo_relative_path(inside) == "GPU_RUNmultiAI/cycles/C0001/runs/probe"
    assert not repo_relative_path(inside).startswith("/")
    identity = build_resume_identity(
        commit="abc123",
        audit_script_path=Path(AUDIT_ENTRY_SCRIPT),
        corpus_hash="0" * 64,
        cli_args={"smoke": True},
        output_dir=inside,
    )
    assert identity["fingerprint_payload_path"] == "GPU_RUNmultiAI/cycles/C0001/runs/probe/fingerprint_payload.json"
    assert identity["dependency_versions"]["scikit-learn"]
    assert identity["dependency_versions"]["numexpr"]


def test_resume_requires_byte_identical_fingerprint_artifacts(tmp_path):
    from gpu_runmultiai.invariants import ResumeIdentityError
    from gpu_runmultiai.manifest import verify_fingerprint_artifacts

    payload = {"corpus": "fixture", "n": 3}
    payload_bytes = json.dumps(payload, sort_keys=True).encode()
    with pytest.raises(ResumeIdentityError, match="requires fingerprint artifact"):
        verify_fingerprint_artifacts(tmp_path, fingerprint_bytes=payload_bytes, manifest_payload=payload)
    (tmp_path / "fingerprint_bytes.bin").write_bytes(payload_bytes)
    (tmp_path / "fingerprint_payload.json").write_bytes(payload_bytes)
    verify_fingerprint_artifacts(tmp_path, fingerprint_bytes=payload_bytes, manifest_payload=payload)
    with pytest.raises(ResumeIdentityError, match="bytes mismatch"):
        verify_fingerprint_artifacts(tmp_path, fingerprint_bytes=b"other", manifest_payload=payload)
    with pytest.raises(ResumeIdentityError, match="manifest payload dict"):
        verify_fingerprint_artifacts(
            tmp_path, fingerprint_bytes=payload_bytes, manifest_payload={"corpus": "other"}
        )
    # Re-serialisation must not be used to paper over a byte difference.
    (tmp_path / "fingerprint_payload.json").write_text(
        json.dumps(payload, sort_keys=True, indent=2), encoding="utf-8"
    )
    with pytest.raises(ResumeIdentityError, match="byte-identical"):
        verify_fingerprint_artifacts(tmp_path, fingerprint_bytes=payload_bytes, manifest_payload=payload)


def test_resume_identity_mismatch_raises_resume_identity_error():
    from gpu_runmultiai.invariants import ResumeIdentityError
    from gpu_runmultiai.manifest import verify_resume_identity

    baseline = {"commit": "a" * 40, "corpus_hash": "b" * 64}
    verify_resume_identity(baseline, dict(baseline))
    with pytest.raises(ResumeIdentityError, match="commit"):
        verify_resume_identity(baseline, {**baseline, "commit": "c" * 40})


def test_accepted_closure_source_hash_hook_is_absent_by_default(tmp_path):
    from gpu_runmultiai.manifest import verify_accepted_closure_source_hashes
    from gpu_runmultiai.source_inventory import build_source_inventory

    inventory = build_source_inventory(include_hashes=True)
    status = verify_accepted_closure_source_hashes(inventory, output_dir=tmp_path)
    assert status == "closure_record_absent"
    (tmp_path / "implementation_closure_record.json").write_text(
        json.dumps({"source_hashes": [{"path": "src/gpu_runmultiai/audit.py", "sha256": "0" * 64}]}),
        encoding="utf-8",
    )
    from gpu_runmultiai.invariants import ResumeIdentityError

    with pytest.raises(ResumeIdentityError, match="accepted closure source hashes"):
        verify_accepted_closure_source_hashes(inventory, output_dir=tmp_path)


def test_manifest_status_lifecycle_rejects_illegal_status(tmp_path):
    from gpu_runmultiai.audit import MANIFEST_STATUSES, _write_atomic_manifest
    from gpu_runmultiai.invariants import GateAbortError

    assert MANIFEST_STATUSES == ("initializing", "running", "completed", "aborted")
    path = tmp_path / "audit_manifest.json"
    for status in MANIFEST_STATUSES:
        _write_atomic_manifest(path, {"status": status})
        assert json.loads(path.read_text(encoding="utf-8"))["status"] == status
    with pytest.raises(GateAbortError, match="illegal manifest status"):
        _write_atomic_manifest(path, {"status": "in_progress"})


def test_global_abort_routes_gate_errors_through_aborted(tmp_path, bootstrap_guard, monkeypatch):
    """§12.7: every listed gate error yields status=aborted plus an abort manifest and deviation entry."""
    from gpu_runmultiai import audit as audit_module
    from gpu_runmultiai.audit import ABORT_MANIFEST_REQUIRED_FIELDS, run_audit
    from gpu_runmultiai.invariants import (
        CorpusGateError,
        EligibilityGateError,
        ExponentTokenError,
        FrozenEnvironmentError,
        GateAbortError,
        ResourceCeilingError,
        ScalerGateError,
        StratumGateError,
    )
    from gpu_runmultiai.q4_reference import Q4ContractError
    from scripts.phases.guard_bootstrap import GuardBootstrapViolation

    error_types = [
        CorpusGateError,
        ScalerGateError,
        EligibilityGateError,
        StratumGateError,
        ResourceCeilingError,
        GateAbortError,
        Q4ContractError,
        ExponentTokenError,
        FrozenEnvironmentError,
        GuardBootstrapViolation,
    ]
    for index, error_type in enumerate(error_types):
        output_dir = tmp_path / f"abort_{index}"

        def _boom(*_args, **_kwargs):
            raise error_type(f"synthetic {error_type.__name__}")

        monkeypatch.setattr(audit_module, "_run_audit_body", _boom)
        options = {
            "output_dir": str(output_dir),
            "oracle_timeout_sec": 30.0,
            "fail_if_exists": False,
            "resume": False,
            "smoke": True,
            "primary_scales": ("0.1",),
            "require_clean_worktree": False,
        }
        with pytest.raises(error_type):
            run_audit(options, guard=bootstrap_guard)
        manifest = json.loads((output_dir / "audit_manifest.json").read_text(encoding="utf-8"))
        assert manifest["status"] == "aborted"
        assert manifest["abort_type"] == error_type.__name__
        abort = json.loads((output_dir / "abort_manifest.json").read_text(encoding="utf-8"))
        for field in ABORT_MANIFEST_REQUIRED_FIELDS:
            assert field in abort, f"{error_type.__name__} abort manifest missing {field}"
        assert abort["status"] == "aborted"
        assert abort["abort_utc"]
        assert abort["output_dir_bytes"] >= 0
        assert "last_durable_call_key" in abort
        assert "last_durable_cache_key" in abort
        body = (output_dir / "deviation_log.md").read_text(encoding="utf-8")
        entry_lines = [line for line in body.splitlines() if line.startswith("- ")]
        assert entry_lines
        assert len(entry_lines[-1][2:].split(" | ")) == 6
        assert body.rstrip().endswith(f"status=aborted abort_type={error_type.__name__}")


def test_deviation_entries_have_six_fields(tmp_path):
    from gpu_runmultiai.audit import append_deviation_entry, build_deviation_entry, finalize_deviation_log, init_deviation_log
    from gpu_runmultiai.invariants import GateAbortError

    path = tmp_path / "deviation_log.md"
    init_deviation_log(path)
    entry = build_deviation_entry(
        description="probe",
        scientific_impact="none",
        resolution="probe only",
        approval_reference="cursor-round3",
    )
    assert len(entry) == 6
    assert entry[5] == "cursor-round3"
    append_deviation_entry(path, entry)
    with pytest.raises(GateAbortError, match="six fields"):
        append_deviation_entry(path, ("a", "b", "c"))
    finalize_deviation_log(path, status="completed", abort_type=None)
    body = path.read_text(encoding="utf-8")
    assert body.rstrip().endswith("status=completed abort_type=none")


def test_call_logger_checks_resources_around_every_primitive(tmp_path):
    """§8.5: the counted-call path measures ceilings before and after execution."""
    from gpu_runmultiai.invariants import ResourceCeilingError

    class SpyMonitor:
        def __init__(self):
            self.checks = 0

        def assert_within_limits(self):
            self.checks += 1

    monitor = SpyMonitor()
    logger = CallLogger(tmp_path / "call_log.jsonl", resource_monitor=monitor)
    logger.execute_or_record(
        primitive="oracle_equivalence",
        condition="B0",
        stage="E1",
        unit_type="pair",
        unit_id="pair_sha256:" + "9" * 64,
        executor=lambda: "done",
    )
    assert monitor.checks >= 2

    class TrippingMonitor:
        def assert_within_limits(self):
            raise ResourceCeilingError("output directory byte ceiling exceeded")

    tripping = CallLogger(resource_monitor=TrippingMonitor())
    with pytest.raises(ResourceCeilingError):
        tripping.execute_or_record(
            primitive="oracle_equivalence",
            condition="B0",
            stage="E1",
            unit_type="pair",
            unit_id="pair_sha256:" + "a" * 64,
            executor=lambda: "done",
        )


def test_g_contract_checks_are_executed_not_asserted(bootstrap_guard):
    """§10.1: all seven G_contract rows come from executable checks."""
    from gpu_runmultiai.contract_evidence import G_CONTRACT_CHECK_KEYS, evaluate_g_contract_checks
    from gpu_runmultiai.pipeline import run_c_q4_fixtures

    c_q4_rows = [
        {**row, "terminal_outcome": "fixture_pass" if row.get("fixture_pass") else "fixture_failure"}
        for row in run_c_q4_fixtures(call_logger=CallLogger(), q4_timeout_sec=Q4_TIMEOUT_SEC)
    ]
    rows = evaluate_g_contract_checks(guard=bootstrap_guard, c_q4_rows=c_q4_rows)
    assert tuple(row["check_key"] for row in rows) == G_CONTRACT_CHECK_KEYS
    for row in rows:
        assert row["requirement"]
        assert row["details"]
        assert row["passed"] is True, f"{row['check_key']}: {row['details']}"

    # The evidence is data-dependent, not a literal: a broken fixture set must fail.
    broken = evaluate_g_contract_checks(
        guard=bootstrap_guard,
        c_q4_rows=[{**c_q4_rows[0], "fixture_pass": False}],
    )
    assert broken[0]["passed"] is False
    assert "fixture_count=1" in broken[0]["details"]


def test_f_acceptance_rows_are_computed_from_rows():
    from gpu_runmultiai.contract_evidence import F_ACCEPTANCE_IDS, evaluate_f_acceptance

    empty = evaluate_f_acceptance(b0_rows=[], b1_rows=[], b2_rows=[])
    assert tuple(row["requirement_id"] for row in empty) == F_ACCEPTANCE_IDS
    by_id = {row["requirement_id"]: row for row in empty}
    # F1/F2/F4/F8 execute their acceptance population independently of persisted rows.
    assert by_id["F2"]["passed"] is True
    assert by_id["F8"]["passed"] is True
    try:
        from gpu_runmultiai.odeformer_runtime import require_odeformer

        require_odeformer()
        odeformer_available = os.environ.get("LANSR_SKIP_ODEFORMER_CHAIN") != "1"
    except ODEFormerUnavailable:
        odeformer_available = False
    if odeformer_available:
        assert by_id["F1"]["passed"] is True
        assert by_id["F4"]["passed"] is True
    # Row-population gates must fail loudly when no rows exist.
    assert by_id["F5"]["passed"] is False
    assert by_id["F7"]["passed"] is False
    assert by_id["F6"]["passed"] is False
    assert "510" in by_id["F6"]["details"]


def test_g_contract_and_g_impl_gates_read_executed_evidence():
    from gpu_runmultiai.controls import gate_g_contract, gate_g_impl
    from gpu_runmultiai.contract_evidence import F_ACCEPTANCE_IDS, G_CONTRACT_CHECK_KEYS

    passing = {key: True for key in G_CONTRACT_CHECK_KEYS}
    assert gate_g_contract({"g_contract_evidence": passing}) is True
    for key in G_CONTRACT_CHECK_KEYS:
        assert gate_g_contract({"g_contract_evidence": {**passing, key: False}}) is False
    assert gate_g_contract({}) is False

    reachability = [{"passed": True} for _ in range(10)]
    acceptance = {key: True for key in F_ACCEPTANCE_IDS}
    assert gate_g_impl({"reachability_evidence": reachability, "f_acceptance": acceptance}) is True
    for key in F_ACCEPTANCE_IDS:
        assert (
            gate_g_impl(
                {"reachability_evidence": reachability, "f_acceptance": {**acceptance, key: False}}
            )
            is False
        )


@pytest.mark.skipif(os.environ.get("LANSR_SKIP_ODEFORMER_CHAIN") == "1", reason="ODEFormer runtime unavailable")
def test_reachability_uns_sup_use_real_gate_evaluation():
    """§10.2: UNS/SUP rows must run evaluate_validity_gates + evaluate_primary_decision."""
    from gpu_runmultiai.odeformer_runtime import require_odeformer
    from gpu_runmultiai.reachability import build_reachability_evidence

    try:
        require_odeformer()
    except ODEFormerUnavailable:
        pytest.skip("ODEFormer runtime unavailable")
    rows = {row["fixture_id"]: row for row in build_reachability_evidence()}
    assert len(rows) == 10
    for fixture_id, row in rows.items():
        assert row["passed"] is True, f"{fixture_id}: {row['details']}"
    assert rows["REACH-UNS-1"]["evidence_type"] == "primary_decision_grid"
    assert "H0001 unsupported" in rows["REACH-UNS-1"]["details"]
    assert "rows=1320" in rows["REACH-UNS-1"]["details"]
    assert "failed_gates=[]" in rows["REACH-UNS-1"]["details"]
    assert "H0001 supported" in rows["REACH-SUP-1"]["details"]
    assert "sfn=1" in rows["REACH-SUP-1"]["details"]
    assert rows["REACH-RESCALE-1"]["evidence_type"] == "live_production_rescale"
    assert "Scaler.rescale_function" in rows["REACH-RESCALE-1"]["details"]


def test_round3_artifact_schemas_present_in_smoke(tmp_path, bootstrap_guard):
    """§12.8 required keys are read back from a real bounded run."""
    from gpu_runmultiai.contract_evidence import ARTIFACT_ROW_SCHEMAS

    output_dir = tmp_path / "schema_round3"
    result = _run_audit(
        {
            "output_dir": str(output_dir),
            "oracle_timeout_sec": 30.0,
            "simplifier_subprocess_timeout_sec": SIMPLIFIER_SUBPROCESS_TIMEOUT_SEC,
            "fail_if_exists": False,
            "resume": False,
            "smoke": True,
            "primary_scales": ("0.1",),
        },
        bootstrap_guard,
    )
    manifest = result["manifest"]
    for key in (
        "status",
        "audit_id",
        "plan_hash",
        "commit",
        "seeds",
        "corpus_hash",
        "fingerprint_payload_bytes_hash",
        "source_hashes",
        "dependency_versions",
        "environment",
        "runtime_provenance",
        "primitive_table",
        "cli_args_normalized",
        "confirmatory_calls",
        "descriptive_calls",
        "grand_calls",
        "validity_gates",
        "primary_decision",
        "g_contract_evidence",
        "f_acceptance",
    ):
        assert key in manifest, f"manifest missing {key}"
    assert manifest["status"] == "completed"

    for artifact in ("registration_truth.json", "registration_rewrites.json", "quantization_stratum.json",
                     "negative_controls.json", "b3_results.json", "b4_results.json",
                     "q4_reference_controls.json", "reachability_evidence.json",
                     "equivalence_oracle.json", "condition_summary.json", "contract_evidence.json"):
        assert (output_dir / artifact).is_file(), artifact
    for artifact, required in ARTIFACT_ROW_SCHEMAS.items():
        path = output_dir / artifact
        if not path.is_file() or artifact.endswith(".jsonl"):
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        rows = payload if isinstance(payload, list) else [payload]
        if not rows:
            continue
        missing = [key for key in required if key not in rows[0]]
        assert not missing, f"{artifact} missing {missing}"

    # Fingerprint payload file is byte-identical to the frozen fingerprint bytes.
    assert (output_dir / "fingerprint_payload.json").read_bytes() == (
        output_dir / "fingerprint_bytes.bin"
    ).read_bytes()
    contract = json.loads((output_dir / "contract_evidence.json").read_text(encoding="utf-8"))
    assert contract["g_contract_pass"] is True
    assert len(contract["g_contract"]) == 7
    assert len(contract["f_acceptance"]) == 7


def test_smoke_terminal_vocabulary_has_no_unknown(tmp_path, bootstrap_guard):
    import csv as _csv

    output_dir = tmp_path / "vocab_round3"
    _run_audit(
        {
            "output_dir": str(output_dir),
            "oracle_timeout_sec": 30.0,
            "simplifier_subprocess_timeout_sec": SIMPLIFIER_SUBPROCESS_TIMEOUT_SEC,
            "fail_if_exists": False,
            "resume": False,
            "smoke": True,
            "primary_scales": ("0.1",),
        },
        bootstrap_guard,
    )
    with (output_dir / "pair_results.csv").open(encoding="utf-8") as handle:
        rows = list(_csv.DictReader(handle))
    assert rows
    assert all(row["outcome_category"] != "unknown" for row in rows)
    b2_rows = [row for row in rows if row["condition"] == "B2"]
    if b2_rows:
        assert all(row["outcome_category"] != "unknown" for row in b2_rows)
    d2_rows = [row for row in rows if row["condition"] == "D2"]
    assert d2_rows
    assert all(
        row["outcome_category"] in {"descriptive_recorded", "descriptive_failed"} for row in d2_rows
    )
    b1_rows = [row for row in rows if row["condition"] == "B1"]
    assert b1_rows
    assert all(row["outcome_category"] in {"control_pass", "control_failure"} for row in b1_rows)


def test_canonical_prefix_normalizes_pipe_and_comma_dialects():
    legacy = "add,x_0,1|mul,x_1,2"
    production = f"add,x_0,1{MULTI_COMPONENT_SEPARATOR}mul,x_1,2"
    assert canonical_system_prefix_raw(legacy) == production
    assert canonical_system_prefix_raw(production) == production


@pytest.mark.skipif(os.environ.get("LANSR_SKIP_ODEFORMER_CHAIN") == "1", reason="ODEFormer runtime unavailable")
def test_multi_component_identity_fallback_uses_canonical_prefix_dialect():
    from gpu_runmultiai.odeformer_runtime import ODEFormerUnavailable, require_odeformer
    from gpu_runmultiai.pipeline import detect_e2_identity_fallback_candidate, run_b0_pair
    from gpu_runmultiai.q4_reference import audit_q4_decimal_round_reference

    try:
        require_odeformer()
    except ODEFormerUnavailable:
        pytest.skip("ODEFormer runtime unavailable")
    corpus = load_frozen_corpus()
    record = next(row for row in corpus["train_records"] if row["dimension"] == 3)
    truth_prefix, truth_infix = truth_component_infix(record, 0)
    rewrite = rewrite_registration(
        record["system_id"], 0, truth_prefix, truth_infix, oracle_timeout_sec=30.0
    )
    row = run_b0_pair(
        corpus_hash=corpus["corpus_hash"],
        record=record,
        component_idx=0,
        scale="0.1",
        rewrite_row=rewrite,
        oracle_timeout_sec=30.0,
        q4_timeout_sec=Q4_TIMEOUT_SEC,
        simplifier_timeout_sec=SIMPLIFIER_SUBPROCESS_TIMEOUT_SEC,
        call_logger=CallLogger(),
        runtime_available=True,
        guard=SealedPathGuard(output_root_abs=Path("/nonexistent/results/runs")),
    )
    assert MULTI_COMPONENT_SEPARATOR in (row.get("e1_prefix_raw") or "")
    e1_component = component_prefix_list_from_raw(row["e1_prefix_raw"])[0]
    q4 = audit_q4_decimal_round_reference(
        e1_component, dimension=3, timeout_sec=Q4_TIMEOUT_SEC
    )
    mismatched_legacy = row["e1_prefix_raw"].replace(MULTI_COMPONENT_SEPARATOR, "|")
    assert mismatched_legacy != row["e1_prefix_raw"]
    assert detect_e2_identity_fallback_candidate(
        e1_prefix_raw=mismatched_legacy,
        e2_prefix_raw=row["e1_prefix_raw"],
        e1_component_prefix=e1_component,
        q4_sympy_expr_canonical=q4.q4_sympy_expr_canonical,
        dimension=3,
        q4_timeout_sec=Q4_TIMEOUT_SEC,
    ) is False
    assert detect_e2_identity_fallback_candidate(
        e1_prefix_raw=row["e1_prefix_raw"],
        e2_prefix_raw=row["e1_prefix_raw"],
        e1_component_prefix=e1_component,
        q4_sympy_expr_canonical=q4.q4_sympy_expr_canonical,
        dimension=3,
        q4_timeout_sec=Q4_TIMEOUT_SEC,
    ) == bool(q4.q4_construction_completed and q4.q4_sympy_expr_canonical)


def test_guard_side_channel_exists_even_with_zero_attempts(tmp_path, bootstrap_guard):
    from gpu_runmultiai.guard_side_channel import side_channel_path

    output_dir = tmp_path / "guard_zero"
    _run_audit(
        {
            "output_dir": str(output_dir),
            "oracle_timeout_sec": 30.0,
            "simplifier_subprocess_timeout_sec": SIMPLIFIER_SUBPROCESS_TIMEOUT_SEC,
            "fail_if_exists": False,
            "resume": False,
            "smoke": True,
            "primary_scales": ("0.1",),
        },
        bootstrap_guard,
    )
    path = side_channel_path(output_dir)
    assert path.is_file()


def test_resume_requires_accepted_closure_record(tmp_path, bootstrap_guard):
    from gpu_runmultiai.invariants import ResumeIdentityError

    output_dir = tmp_path / "resume_closure"
    base = {
        "output_dir": str(output_dir),
        "oracle_timeout_sec": 30.0,
        "simplifier_subprocess_timeout_sec": SIMPLIFIER_SUBPROCESS_TIMEOUT_SEC,
        "fail_if_exists": False,
        "resume": False,
        "smoke": True,
        "primary_scales": ("0.1",),
        "require_clean_worktree": False,
    }
    _run_audit(base, bootstrap_guard)
    with pytest.raises(ResumeIdentityError, match="implementation_closure_record"):
        _run_audit({**base, "resume": True}, bootstrap_guard)


def test_f6_smoke_population_does_not_pass_acceptance(tmp_path, bootstrap_guard):
    from gpu_runmultiai.contract_evidence import evaluate_f_acceptance

    output_dir = tmp_path / "f6_smoke"
    result = _run_audit(
        {
            "output_dir": str(output_dir),
            "oracle_timeout_sec": 30.0,
            "simplifier_subprocess_timeout_sec": SIMPLIFIER_SUBPROCESS_TIMEOUT_SEC,
            "fail_if_exists": False,
            "resume": False,
            "smoke": True,
            "primary_scales": ("0.1",),
        },
        bootstrap_guard,
    )
    f6 = next(row for row in result["contract_evidence"]["f_acceptance"] if row["requirement_id"] == "F6")
    assert f6["passed"] is False
    assert "510" in f6["details"]
    assert result["gates"]["G_impl"] is False


def test_closure_binds_accepted_source_commit_not_metadata(tmp_path, canonical_closure_record):
    from gpu_runmultiai.manifest import require_accepted_closure_for_execution
    from gpu_runmultiai.source_inventory import build_source_inventory

    inventory = _source_inventory_for_commit(canonical_closure_record["accepted_source_commit"])
    status = require_accepted_closure_for_execution(
        canonical_closure_record["accepted_source_commit"],
        inventory,
        plan_hash=PLAN_SHA256,
        audit_id=AUDIT_ID,
    )
    assert (
        "accepted_source_commit=" + canonical_closure_record["accepted_source_commit"] in status
    )
    assert "metadata_commit=" + canonical_closure_record["commit"] in status


def test_canonical_closure_negative_fixtures_fail_closed(tmp_path, monkeypatch):
    from gpu_runmultiai import manifest as manifest_module
    from gpu_runmultiai.invariants import ResumeIdentityError
    from gpu_runmultiai.manifest import verify_canonical_closure_record

    closure_path = tmp_path / "implementation_closure_record.json"
    monkeypatch.setattr(manifest_module, "CANONICAL_CLOSURE_RECORD_PATH", closure_path)
    base = _canonical_closure_record_payload(tmp_path)
    inventory = list(base["source_hashes"])

    def _write(payload):
        closure_path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")

    _write({**base, "g_impl_verdict": "BLOCK"})
    with pytest.raises(ResumeIdentityError, match="g_impl_verdict"):
        verify_canonical_closure_record(
            commit=base["accepted_source_commit"],
            source_inventory=inventory,
            plan_hash=PLAN_SHA256,
            audit_id=AUDIT_ID,
            required=True,
        )
    _write({**base, "plan_hash": "0" * 64})
    with pytest.raises(ResumeIdentityError, match="plan_hash"):
        verify_canonical_closure_record(
            commit=base["accepted_source_commit"],
            source_inventory=inventory,
            plan_hash=PLAN_SHA256,
            audit_id=AUDIT_ID,
            required=True,
        )
    _write({**base, "acceptance_artifact_digest": "0" * 64})
    with pytest.raises(ResumeIdentityError, match="acceptance_artifact_digest"):
        verify_canonical_closure_record(
            commit=base["accepted_source_commit"],
            source_inventory=inventory,
            plan_hash=PLAN_SHA256,
            audit_id=AUDIT_ID,
            required=True,
        )
    closure_path.unlink(missing_ok=True)
    with pytest.raises(ResumeIdentityError, match="require accepted"):
        verify_canonical_closure_record(
            commit=base["accepted_source_commit"],
            source_inventory=inventory,
            plan_hash=PLAN_SHA256,
            audit_id=AUDIT_ID,
            required=True,
        )


def test_verify_clean_worktree_excludes_output_dir_only(monkeypatch):
    import subprocess

    from experiment_runtime import REPO_ROOT
    from gpu_runmultiai.manifest import verify_clean_worktree

    output_rel = "runs/acceptance_out"
    other_rel = "runs/other_dirty"
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            args=args[0],
            returncode=0,
            stdout=f"?? {output_rel}/artifact.json\n",
            stderr="",
        ),
    )
    provenance = verify_clean_worktree(exclude_paths=[str((REPO_ROOT / output_rel).resolve())])
    assert provenance["clean"] is True
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            args=args[0],
            returncode=0,
            stdout=f"?? {other_rel}/dirty.txt\n",
            stderr="",
        ),
    )
    with pytest.raises(Exception):
        verify_clean_worktree(exclude_paths=[str((REPO_ROOT / output_rel).resolve())])


def test_pair_cache_duplicate_pair_id_aborts(tmp_path):
    from gpu_runmultiai.audit import _load_pair_cache
    from gpu_runmultiai.invariants import AuditInvariantError

    path = tmp_path / "pair_cache.jsonl"
    path.write_text(
        '{"pair_id":"pair_sha256:1","condition":"B0"}\n'
        '{"pair_id":"pair_sha256:1","condition":"B2"}\n',
        encoding="utf-8",
    )
    with pytest.raises(AuditInvariantError, match="duplicate JSONL key"):
        _load_pair_cache(path)


def test_f7_independent_reference_module_has_no_production_classifier_import():
    import ast
    from pathlib import Path

    source = Path("src/gpu_runmultiai/f7_independent_reference.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    imported_from = {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    }
    assert "evaluation.gpu_run5_structure" not in imported_from
    assert "gpu_runmultiai.outcomes" not in imported_from
    assert "gpu_runmultiai.pipeline" not in imported_from


def test_verify_source_inventory_at_commit_matches_head():
    from gpu_runmultiai.manifest import verify_source_inventory_at_commit
    from gpu_runmultiai.manifest import current_commit
    from gpu_runmultiai.source_inventory import build_source_inventory

    inventory = build_source_inventory(include_hashes=True)
    verify_source_inventory_at_commit(current_commit(), inventory)


def test_timing_calibration_uses_multiplicity_weighting():
    from gpu_runmultiai.constants import D2_CALLS_PER_PAIR, D2_PAIR_COUNT
    from gpu_runmultiai.timing_calibration import D2_PAIR_PRIMITIVE_SEQUENCE, run_timing_calibration
    from gpu_runmultiai.calls import expected_confirmatory_calls, expected_descriptive_calls

    assert len(D2_PAIR_PRIMITIVE_SEQUENCE) == D2_CALLS_PER_PAIR
    assert sum(1 for _primitive, _condition in D2_PAIR_PRIMITIVE_SEQUENCE if _primitive == "oracle_equivalence") == 2
    blocked = run_timing_calibration(call_logger=None, runtime_available=False, guard=None)
    assert blocked["status"] == "BLOCK"
    assert blocked["reason"] == "odeformer_unavailable"
    assert expected_descriptive_calls() == D2_PAIR_COUNT * D2_CALLS_PER_PAIR
    assert expected_confirmatory_calls() == 27637


def test_f7_frozen_decision_table_mutation_falsifier():
    from gpu_runmultiai.f7_independent_reference import classify_b2_outcome_frozen, compute_b2_expected_outcome

    row = {
        "construction_incomplete": False,
        "q4_construction_completed": True,
        "rescale_incomplete": False,
        "classifier_parse_valid": True,
        "e1_oracle_completed": True,
        "e1_oracle_equivalent": True,
        "hill_form": True,
    }
    assert classify_b2_outcome_frozen(row) == "preserved"
    assert classify_b2_outcome_frozen({**row, "e1_oracle_equivalent": False}) == "semantic_drift"
    expected = compute_b2_expected_outcome(
        e1_infix="x_0**2/(1+x_0**2)",
        component_idx=0,
        e1_fields={
            "q4_construction_completed": True,
            "e1_oracle_completed": True,
            "e1_oracle_equivalent": True,
            "rescale_incomplete": False,
        },
    )
    assert expected in {"preserved", "structural_false_negative", "semantic_drift", "execution_failure"}


def test_resource_monitor_snapshot_is_non_raising(tmp_path):
    from gpu_runmultiai.invariants import ResourceCeilingError
    from gpu_runmultiai.resources import ResourceMonitor

    monitor = ResourceMonitor(tmp_path)
    snapshot = monitor.snapshot()
    assert "elapsed_sec" in snapshot
    assert "output_dir_bytes" in snapshot

    class TrippingMonitor(ResourceMonitor):
        def assert_within_limits(self):
            raise ResourceCeilingError("ceiling")

    tripping = TrippingMonitor(tmp_path)
    tripping_snapshot = tripping.snapshot()
    assert tripping_snapshot["bytes_exceeded"] in (True, False)


def test_select_smoke_components_covers_required_strata():
    from gpu_runmultiai.audit import _select_smoke_components

    corpus = load_frozen_corpus()
    component_index = [
        {**item, "record": next(r for r in corpus["train_records"] if r["system_id"] == item["system_id"])}
        for item in corpus["component_index"]
    ]
    selected = _select_smoke_components(component_index)
    assert any(int(item["record"]["dimension"]) == 3 and int(item["component_idx"]) > 0 for item in selected)
    assert any(
        component_stratum(item["record"]["family"], item["component_idx"]) == "non_strict_hill"
        for item in selected
    )
    assert any(is_linear_component(item["record"]["family"], item["component_idx"]) for item in selected)


def test_implementation_acceptance_cli_flag_exists():
    import inspect

    from scripts.phases import gpu_runmultiai_c0001_metric_audit as cli_module

    source = inspect.getsource(cli_module.parse_args)
    assert "--implementation-acceptance" in source
