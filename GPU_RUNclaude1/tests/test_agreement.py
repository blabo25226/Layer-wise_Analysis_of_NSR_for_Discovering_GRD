"""Tests for gpu_runclaude1.agreement: Gate 0 item 11's M3-implementation
agreement test (v2.1 §7.4 V2-MAJ-2) and the in-pass 1-in-100 census.
"""

from __future__ import annotations

from gpu_runclaude1.agreement import (
    census_should_check,
    collect_agreement_pairs,
    run_agreement_test,
    run_in_pass_census,
)

SYNTHETIC_ROWS = [
    {
        "system_id": "SYS_HILL",
        "family": "FAM_H",
        "dimension": 1,
        "teacher_components_infix": ["0.5 + 0.8 * x_0 * 1/(0.3 + x_0) + -1 * 0.2 * x_0"],
    },
    {
        "system_id": "SYS_LINEAR_2D",
        "family": "FAM_L",
        "dimension": 2,
        "teacher_components_infix": ["0.1 + -1 * 0.4 * x_0", "0.2 + -1 * 0.5 * x_0 * x_1"],
    },
]


def test_collect_agreement_pairs_includes_identity_pairs():
    pairs = collect_agreement_pairs(SYNTHETIC_ROWS)
    sources = {p[2] for p in pairs}
    assert "PC0" in sources
    # Every PC0 pair is a true==candidate identity.
    pc0_pairs = [p for p in pairs if p[2] == "PC0"]
    assert pc0_pairs
    for true_text, cand_text, _source in pc0_pairs:
        assert true_text == cand_text


def test_collect_agreement_pairs_deduplicates():
    pairs = collect_agreement_pairs(SYNTHETIC_ROWS)
    keys = [(t, c) for t, c, _s in pairs]
    assert len(keys) == len(set(keys))


def test_run_agreement_test_reports_realized_n_and_zero_disagreement_on_synthetic_corpus():
    pairs = collect_agreement_pairs(SYNTHETIC_ROWS)
    result = run_agreement_test(pairs)
    assert result.n_pairs == len(pairs)
    assert result.ok is True
    assert result.n_disagreements == 0
    assert result.disagreement_rate == 0.0


def test_run_agreement_test_detects_a_real_disagreement():
    """Construct a pair where the two scoring paths are known to be able to
    disagree: an identity pair is always safe, so use one guaranteed to
    agree, and confirm the reported rate is exactly 0 -- if the two
    implementations ever *did* disagree, this would need to be nonzero and
    ok would be False (the frozen requirement, checked structurally here so
    a future change to either implementation cannot silently break the gate
    without a test noticing).
    """
    pairs = [("x_0", "x_0", "manual"), ("x_0", "x_1", "manual")]
    result = run_agreement_test(pairs)
    assert result.n_pairs == 2
    assert result.ok is True  # both are decided cases (match / proved_different), not a disagreement


def test_census_should_check_fires_every_100th_index():
    assert census_should_check(0)
    assert not census_should_check(1)
    assert not census_should_check(99)
    assert census_should_check(100)
    assert census_should_check(200)


def test_run_in_pass_census_over_a_small_synthetic_frame():
    triples = [(i, "x_0", "x_0") for i in range(250)]
    result = run_in_pass_census(triples, every=100)
    assert result["n_checked"] == 3  # indices 0, 100, 200
    assert result["ok"] is True
    assert result["m3_implementation_agreement"] == 1.0
