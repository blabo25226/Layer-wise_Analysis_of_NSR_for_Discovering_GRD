"""Tests for gpu_runclaude1.partc's pure (torch-free) identity and
discriminator functions (v2 §8.2, §8.3).
"""

from __future__ import annotations

from gpu_runclaude1.partc import (
    audit_reencoding_roundtrip,
    cell_input_payload_sha256,
    check_distinct_payload_count,
    normalize_prefix_separator,
    stahlberg_byrne_indicator,
    system_attribution,
    verify_cell_identity,
)


def test_cell_input_payload_sha256_is_deterministic_and_shape_sensitive():
    times = [0.0, 1.0, 2.0]
    trajectory = [[1.0], [2.0], [3.0]]
    initial_condition = [1.0]
    a = cell_input_payload_sha256(times, trajectory, initial_condition)
    b = cell_input_payload_sha256(times, trajectory, initial_condition)
    assert a == b
    # Changing any single value changes the digest.
    c = cell_input_payload_sha256(times, [[1.0], [2.0], [3.5]], initial_condition)
    assert c != a


def test_verify_cell_identity_ok_case():
    cell = {
        "cell_id": "R01_validation_d101_000_b1_n0p05_r0p5",
        "bundle_index": 1,
        "candidate_set_hash": "abc123",
        "cache_identity": {"schema_version": "v1"},
        "observations": {
            "input": [
                {
                    "times": [0.0, 1.0],
                    "observed_trajectory": [[1.0], [2.0]],
                    "initial_condition": [1.0],
                }
            ]
        },
    }
    check = verify_cell_identity(cell)
    assert check.ok is True
    assert check.failure_reason is None
    assert check.payload_sha256 is not None


def test_verify_cell_identity_detects_bundle_mismatch():
    cell = {
        "cell_id": "R01_validation_d101_000_b1_n0_r0",
        "bundle_index": 2,  # mismatched against "_b1_" in cell_id
        "candidate_set_hash": "abc123",
        "cache_identity": {"schema_version": "v1"},
        "observations": {"input": [{"times": [0.0], "observed_trajectory": [[1.0]], "initial_condition": [1.0]}]},
    }
    check = verify_cell_identity(cell)
    assert check.ok is False
    assert check.failure_reason == "CellIdentityMismatch"


def test_verify_cell_identity_detects_missing_candidate_set_hash():
    cell = {
        "cell_id": "R01_validation_d101_000_b0_n0_r0",
        "bundle_index": 0,
        "cache_identity": {"schema_version": "v1"},
        "observations": {"input": [{"times": [0.0], "observed_trajectory": [[1.0]], "initial_condition": [1.0]}]},
    }
    check = verify_cell_identity(cell)
    assert check.ok is False
    assert check.failure_reason == "CellIdentityMismatch"


def test_check_distinct_payload_count_flags_a_stale_cache():
    ok_system = {"sys_a": {f"hash_{i}" for i in range(10)}}
    stale_system = {"sys_b": {"same_hash"} }  # 1 distinct instead of 10: a stale cache
    report = check_distinct_payload_count({**ok_system, **stale_system})
    assert report["sys_a"]["ok"] is True
    assert report["sys_b"]["ok"] is False
    assert report["sys_b"]["n_distinct_payloads"] == 1


def test_normalize_prefix_separator_frozen_normalization():
    assert normalize_prefix_separator("add,x_0|x_1") == "add,x_0,|,x_1"
    already_normalized = "add,x_0,|,x_1"
    assert normalize_prefix_separator(already_normalized) == already_normalized


def test_audit_reencoding_roundtrip_exact_and_mismatch():
    ok = audit_reencoding_roundtrip("add,x_0|x_1", "add,x_0,|,x_1")
    assert ok.exact is True
    assert ok.failure_reason is None
    bad = audit_reencoding_roundtrip("add,x_0|x_1", "add,x_0,|,x_2")
    assert bad.exact is False
    assert bad.failure_reason == "CandidateReencodingMismatch"


def test_stahlberg_byrne_indicator_directions():
    preferred_truth = stahlberg_byrne_indicator(lp_gt=-10.0, lp_sel=-15.0, lp_best=-9.0)
    assert preferred_truth.sb_sel == 1  # model preferred truth over what search returned: search error
    assert preferred_truth.sb_best == 0  # but not over the single best candidate

    preferred_selected = stahlberg_byrne_indicator(lp_gt=-20.0, lp_sel=-15.0, lp_best=-9.0)
    assert preferred_selected.sb_sel == 0


def test_system_attribution_thresholds():
    assert system_attribution(0.6)["E3_system"] is True
    assert system_attribution(0.5)["E3_system"] is True  # >= 0.5
    assert system_attribution(0.0)["E2_system"] is True
    assert system_attribution(0.3)["E2_system"] is False
    assert system_attribution(0.3)["E3_system"] is False
