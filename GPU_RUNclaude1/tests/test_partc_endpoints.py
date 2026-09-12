"""Tests for gpu_runclaude1.partc_endpoints -- the Part C corpus-level
aggregation, the C2-S6/S7 descriptive rank/IQR panel, the corpus attribution
rule, and the Gate C->report null-credibility mechanics (v2 §8.3, §10.1).

All pure Python/numpy, no torch, no model, no GPU.
"""

from __future__ import annotations

import math

from gpu_runclaude1.partc_endpoints import (
    compute_c2s9,
    compute_cell_rank_panel,
    corpus_attribution_rule,
    corpus_proportion_endpoint,
    evaluate_null_credibility,
    reference_resolution_gate,
    rollup_system,
    two_stage_cluster_bootstrap_binary,
    two_stage_cluster_bootstrap_continuous,
)
from gpu_runclaude1.ladder import ClusterBootstrapResult


# --- rollup_system: the sb_rate >= 0.5 / == 0 boundary ---------------------


def test_rollup_system_sb_rate_exactly_half_is_e3():
    result = rollup_system("sys_a", "R01", sb_sel_values=[1, 0], sb_best_values=[0, 0])
    assert result.sb_rate_sel == 0.5
    assert result.e3_system is True  # >= 0.5
    assert result.e2_system is False


def test_rollup_system_sb_rate_just_under_half_is_not_e3():
    result = rollup_system("sys_a", "R01", sb_sel_values=[1, 0, 0], sb_best_values=[0, 0, 0])
    assert abs(result.sb_rate_sel - (1 / 3)) < 1e-9
    assert result.e3_system is False


def test_rollup_system_sb_rate_zero_is_e2():
    result = rollup_system("sys_a", "R01", sb_sel_values=[0, 0, 0], sb_best_values=[0, 0, 0])
    assert result.sb_rate_sel == 0.0
    assert result.e2_system is True
    assert result.e3_system is False  # 0 < 0.5, and E2/E3 are not both claimed


def test_rollup_system_zero_usable_cells_contributes_neither():
    result = rollup_system("sys_a", "R01", sb_sel_values=[], sb_best_values=[])
    assert result.n_usable_cells == 0
    assert result.sb_rate_sel is None
    assert result.e2_system is False
    assert result.e3_system is False


# --- corpus_proportion_endpoint: denominator is n_in_support, not len(indicators) --


def test_corpus_proportion_uses_n_in_support_as_denominator_even_with_missing_systems():
    # Only one system has usable evidence, but n_in_support is 4: the
    # missing three must not vanish from the denominator (v2 §8.3).
    indicators = {"sys_a": True}
    family_of_system = {"sys_a": "R01"}
    endpoint = corpus_proportion_endpoint(indicators, family_of_system, n_in_support=4)
    assert endpoint.k == 1
    assert endpoint.n == 4
    assert endpoint.rate == 0.25


def test_corpus_proportion_all_true():
    indicators = {f"sys_{i}": True for i in range(8)}
    family_of_system = {f"sys_{i}": f"fam_{i % 2}" for i in range(8)}
    endpoint = corpus_proportion_endpoint(indicators, family_of_system, n_in_support=8)
    assert endpoint.rate == 1.0
    assert endpoint.wilson_95[0] > 0.5  # a Wilson lower bound on 8/8 is well above 0.5


# --- reference_resolution_gate: the C2-S7 20%-of-cells boundary ------------


def _make_panel_with_gap(gap_in_iqr_units: float):
    """Construct a cell rank panel whose gt_gap_in_iqr_units is exactly the
    requested value, by choosing candidate values with a known (numpy
    linear-interpolation) IQR and solving for gt_logprob_sum.

    For ``candidates = [-9.0, -9.5, -10.5, -11.0]``:
    ``numpy.percentile([...], [25, 75])`` gives Q1=-10.625, Q3=-9.375, so
    IQR = 1.25 and median = -10.0.
    """
    candidates = [-9.0, -9.5, -10.5, -11.0]
    iqr = 1.25
    median = -10.0
    gt = median - gap_in_iqr_units * iqr
    return compute_cell_rank_panel(gt, 20, candidates, [20, 20, 20, 20])


def test_reference_resolution_gate_exactly_five_iqr_does_not_exceed():
    panel = _make_panel_with_gap(5.0)
    assert abs(panel.gt_gap_in_iqr_units - 5.0) < 1e-9
    gate = reference_resolution_gate([panel] * 10)
    assert gate.n_cells_exceeding == 0
    assert gate.gate_ok is True


def test_reference_resolution_gate_just_over_five_iqr_exceeds():
    panel = _make_panel_with_gap(5.0001)
    gate = reference_resolution_gate([panel])
    assert gate.n_cells_exceeding == 1


def test_reference_resolution_gate_20_percent_cell_fraction_boundary():
    exceeding = _make_panel_with_gap(6.0)
    ok = _make_panel_with_gap(0.0)
    # 2 of 10 == 20% == the frozen gate threshold: "more than 20%" must still pass.
    panels = [exceeding, exceeding] + [ok] * 8
    gate = reference_resolution_gate(panels)
    assert gate.fraction_exceeding == 0.2
    assert gate.gate_ok is True  # not "more than" 20%


def test_reference_resolution_gate_just_over_20_percent_fails():
    exceeding = _make_panel_with_gap(6.0)
    ok = _make_panel_with_gap(0.0)
    panels = [exceeding, exceeding, exceeding] + [ok] * 7
    gate = reference_resolution_gate(panels)
    assert gate.fraction_exceeding == 0.3
    assert gate.gate_ok is False


def test_reference_resolution_gate_zero_iqr_counts_as_exceeding():
    # All four candidates identical -> IQR collapses to 0: "no resolution".
    panel = compute_cell_rank_panel(-10.0, 20, [-9.0, -9.0, -9.0, -9.0], [20, 20, 20, 20])
    assert panel.gt_gap_in_iqr_units is None
    gate = reference_resolution_gate([panel])
    assert gate.n_cells_exceeding == 1


def test_compute_cell_rank_panel_below_all_indicator_and_rank_pct():
    # GT worse than every candidate.
    panel = compute_cell_rank_panel(-20.0, 20, [-9.0, -9.5, -10.5, -11.0], [20, 20, 20, 20])
    assert panel.below_all_indicator == 1
    assert panel.rank_pct_sum == 1.0


def test_compute_cell_rank_panel_beats_all_candidates():
    panel = compute_cell_rank_panel(-1.0, 20, [-9.0, -9.5, -10.5, -11.0], [20, 20, 20, 20])
    assert panel.below_all_indicator == 0
    assert panel.rank_pct_sum == 0.0


def test_compute_cell_rank_panel_length_match_unavailable():
    # GT length 100, all candidates length 20: none within +/-20%.
    panel = compute_cell_rank_panel(-10.0, 100, [-9.0, -9.5, -10.5, -11.0], [20, 20, 20, 20])
    assert panel.length_match_unavailable is True
    assert panel.rank_pct_length_matched is None


def test_compute_cell_rank_panel_no_usable_candidates():
    panel = compute_cell_rank_panel(-10.0, 20, [], [])
    assert panel.length_match_unavailable is True
    assert panel.candidate_logprob_iqr is None


# --- corpus_attribution_rule: the three named outcomes ---------------------


def _bootstrap(lo, hi):
    return ClusterBootstrapResult(point_estimate=(lo + hi) / 2, ci_low=lo, ci_high=hi, n_resamples=100, seed=1)


def test_attribution_e3_predominant_when_c2p_lower_bound_exceeds_half():
    outcome = corpus_attribution_rule(_bootstrap(0.6, 0.9), _bootstrap(0.0, 0.1))
    assert outcome == "E3_predominant"


def test_attribution_e2_predominant_when_c2p_upper_below_half_and_c2s1_lower_above_half():
    outcome = corpus_attribution_rule(_bootstrap(0.0, 0.2), _bootstrap(0.6, 0.9))
    assert outcome == "E2_predominant"


def test_attribution_neither_is_the_expected_dead_zone_outcome():
    outcome = corpus_attribution_rule(_bootstrap(0.2, 0.7), _bootstrap(0.1, 0.4))
    assert outcome == "neither_E2_nor_E3_predominant"


def test_attribution_neither_when_c2p_high_but_c2s1_not_confirmed():
    # C2-P upper bound is NOT below 0.5, so it cannot be E2, and its lower
    # bound is not above 0.5 either, so not E3: neither.
    outcome = corpus_attribution_rule(_bootstrap(0.3, 0.6), _bootstrap(0.6, 0.9))
    assert outcome == "neither_E2_nor_E3_predominant"


# --- Gate C -> report: NC1-NC3 gate reporting; NC4/NC5 are disclosed only --


def test_gate_c_to_report_passes_when_nc1_nc2_nc3_all_hold():
    nc = evaluate_null_credibility(
        regression_identity_ok=True,
        unreliable_reencoding_cell_fraction=0.05,
        n_cell_identity_mismatches=0,
        all_systems_distinct_payload_ok=True,
        n_in_support=60,
    )
    assert nc.gate_c_to_report_ok is True


def test_gate_c_to_report_fails_on_nc1():
    nc = evaluate_null_credibility(
        regression_identity_ok=False,
        unreliable_reencoding_cell_fraction=0.0,
        n_cell_identity_mismatches=0,
        all_systems_distinct_payload_ok=True,
        n_in_support=60,
    )
    assert nc.gate_c_to_report_ok is False


def test_gate_c_to_report_fails_on_nc2_over_ten_percent_unreliable():
    nc = evaluate_null_credibility(
        regression_identity_ok=True,
        unreliable_reencoding_cell_fraction=0.11,
        n_cell_identity_mismatches=0,
        all_systems_distinct_payload_ok=True,
        n_in_support=60,
    )
    assert nc.nc2_reencoding_audit_ok is False
    assert nc.gate_c_to_report_ok is False


def test_gate_c_to_report_exactly_ten_percent_unreliable_still_passes():
    nc = evaluate_null_credibility(
        regression_identity_ok=True,
        unreliable_reencoding_cell_fraction=0.10,
        n_cell_identity_mismatches=0,
        all_systems_distinct_payload_ok=True,
        n_in_support=60,
    )
    assert nc.nc2_reencoding_audit_ok is True


def test_gate_c_to_report_fails_on_nc3_identity_mismatch():
    nc = evaluate_null_credibility(
        regression_identity_ok=True,
        unreliable_reencoding_cell_fraction=0.0,
        n_cell_identity_mismatches=1,
        all_systems_distinct_payload_ok=True,
        n_in_support=60,
    )
    assert nc.nc3_identity_assertions_ok is False
    assert nc.gate_c_to_report_ok is False


def test_gate_c_to_report_unaffected_by_nc5_below_power_floor():
    """NC5 (n_in_support >= 30) is tracked and disclosed, but does not gate
    reporting per se -- Gate B->C already downgraded Part C to exploratory
    upstream of this gate; NC5 failing here must not also flip
    gate_c_to_report_ok.
    """
    nc = evaluate_null_credibility(
        regression_identity_ok=True,
        unreliable_reencoding_cell_fraction=0.0,
        n_cell_identity_mismatches=0,
        all_systems_distinct_payload_ok=True,
        n_in_support=5,
    )
    assert nc.nc5_n_in_support_ok is False
    assert nc.gate_c_to_report_ok is True


# --- two_stage_cluster_bootstrap_continuous / binary sanity ----------------


def test_two_stage_cluster_bootstrap_continuous_point_estimate_is_plain_mean():
    values = {"sys_a": 1.0, "sys_b": 3.0}
    family_of_system = {"sys_a": "fam_0", "sys_b": "fam_1"}
    result = two_stage_cluster_bootstrap_continuous(values, family_of_system, n_resamples=200, seed=1)
    assert abs(result.point_estimate - 2.0) < 1e-9
    assert result.ci_low <= result.point_estimate <= result.ci_high


def test_two_stage_cluster_bootstrap_binary_matches_ladder_module_scheme():
    indicators = {"sys_a": True, "sys_b": False, "sys_c": True}
    family_of_system = {"sys_a": "fam_0", "sys_b": "fam_0", "sys_c": "fam_1"}
    result = two_stage_cluster_bootstrap_binary(indicators, family_of_system, n_resamples=500, seed=7)
    assert abs(result.point_estimate - (2 / 3)) < 1e-9


# --- compute_c2s9: exploratory correlation, no decision content -----------


def test_compute_c2s9_degenerate_variance_returns_none():
    result = compute_c2s9([20, 20, 20], [-10.0, -9.0, -11.0], [0, 1, 0])
    assert result.r_length_vs_lp_gt is None  # zero variance in length


def test_compute_c2s9_perfect_positive_correlation():
    result = compute_c2s9([10, 20, 30], [-30.0, -20.0, -10.0], [0, 0, 1])
    assert result.r_length_vs_lp_gt is not None
    assert abs(result.r_length_vs_lp_gt - 1.0) < 1e-9
