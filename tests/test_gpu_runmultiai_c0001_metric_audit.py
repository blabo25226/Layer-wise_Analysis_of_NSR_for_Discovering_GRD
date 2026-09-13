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
from gpu_runmultiai.manifest import normalize_cli_args, verify_plan_hash
from gpu_runmultiai.outcomes import classify_outcome, evaluate_primary_decision
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


def test_counted_call_totals_and_resume_identity():
    assert expected_confirmatory_calls() == CONFIRMATORY_CALL_CEILING
    logger = CallLogger()
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
    with pytest.raises(RuntimeError, match="duplicate counted call"):
        logger.record(
            primitive="rewrite_oracle_precheck",
            condition="registration",
            stage="rewrite",
            unit_type="component",
            unit_id="component_sha256:abc",
            status="completed",
            rewrite_id="rewrite_sha256:def",
        )
    normalized = normalize_cli_args({"resume": True, "fail_if_exists": True, "allow_cpu": True})
    assert "resume" not in normalized
    assert "fail_if_exists" not in normalized
    assert normalized["allow_cpu"] is True


def test_sealed_guard_blocks_deep_paths_without_real_artifact(tmp_path):
    output_root = tmp_path / "results" / "runs"
    denied = output_root / "gpu_run5_example" / "phase8" / "nested" / "predictions" / "rows.json"
    denied.parent.mkdir(parents=True)
    denied.write_text("[]", encoding="utf-8")
    guard = SealedPathGuard(output_root_abs=output_root.resolve())
    assert guard.is_denied(denied, denied)
    guard.install()
    with pytest.raises(PermissionError):
        open(denied, encoding="utf-8")
    assert guard.attempt_count() == 1


def test_n1_and_b4_gate_shapes():
    n1_rows = [
        {"oracle": {"completed": True, "equivalent": False}} for _ in range(100)
    ]
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
            "fail_if_exists": False,
            "resume": False,
            "smoke": True,
            "primary_scales": ("0.1",),
        }
    )
    assert (output_dir / "audit_manifest.json").is_file()
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
