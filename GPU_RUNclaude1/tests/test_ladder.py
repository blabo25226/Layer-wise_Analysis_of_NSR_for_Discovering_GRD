"""Tests for gpu_runclaude1.ladder against the frozen v2 §9.3 Wilson table
and the §7.1/§9.1 ladder cutpoint / cluster bootstrap.
"""

from __future__ import annotations

from gpu_runclaude1.ladder import (
    ladder_cutpoint,
    ladder_verdict,
    power_at_least_one_gain,
    two_stage_cluster_bootstrap,
    wilson_interval,
)

# v2 §9.3 "Corrected Wilson values at n = 80" table.
FROZEN_WILSON_AT_N80 = {
    0: (0.0000, 0.0458),
    1: (0.0022, 0.0675),
    2: (0.0069, 0.0866),
    3: (0.0128, 0.1045),
    4: (0.0196, 0.1216),
    8: (0.0515, 0.1851),
}


def test_wilson_interval_matches_frozen_table_at_n_80():
    for k, (expected_lo, expected_hi) in FROZEN_WILSON_AT_N80.items():
        lo, hi = wilson_interval(k, 80)
        assert abs(lo - expected_lo) < 5e-4, (k, lo, expected_lo)
        assert abs(hi - expected_hi) < 5e-4, (k, hi, expected_hi)


def test_ladder_cutpoint_matches_worked_examples():
    assert ladder_cutpoint(140) == 3
    assert ladder_cutpoint(130) == 3  # the confirmed realized |H| for C0001's validation corpus
    assert ladder_cutpoint(100) == 2


def test_ladder_verdict_three_rungs():
    n_h = 130
    c = ladder_cutpoint(n_h)
    assert ladder_verdict(0, n_h) == "no_gain_observed_bound_only"
    assert ladder_verdict(1, n_h) == "weak_gain"
    assert ladder_verdict(c, n_h) == "weak_gain"
    assert ladder_verdict(c + 1, n_h) == "matcher_attributable_gain_confirmed"


def test_power_at_least_one_gain_matches_frozen_worked_values():
    # v2 §7.3: at p = 0.0525 (the effect size E0 requires), |H|=100 -> 0.9955, |H|=140 -> 0.9995.
    assert abs(power_at_least_one_gain(0.0525, 100) - 0.9955) < 1e-3
    assert abs(power_at_least_one_gain(0.0525, 140) - 0.9995) < 1e-3


def test_two_stage_cluster_bootstrap_all_zero_gives_a_degenerate_zero_interval():
    indicators = {f"sys_{i}": [0, 0] for i in range(10)}
    families = {f"sys_{i}": f"fam_{i % 2}" for i in range(10)}
    result = two_stage_cluster_bootstrap(indicators, families, n_resamples=200, seed=20260909)
    assert result.point_estimate == 0.0
    assert result.ci_low == 0.0
    assert result.ci_high == 0.0


def test_two_stage_cluster_bootstrap_is_deterministic_given_seed():
    indicators = {f"sys_{i}": [1 if i == 0 else 0, 0] for i in range(10)}
    families = {f"sys_{i}": f"fam_{i % 3}" for i in range(10)}
    a = two_stage_cluster_bootstrap(indicators, families, n_resamples=500, seed=20260909)
    b = two_stage_cluster_bootstrap(indicators, families, n_resamples=500, seed=20260909)
    assert a.ci_low == b.ci_low
    assert a.ci_high == b.ci_high
