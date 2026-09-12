"""Tests for gpu_runclaude1.endpoints: the primary gain-rate aggregation,
the two-sided sensitivity analysis, and the K=0 bound-of-record correction
(v2.1 V2-MAJ-3).
"""

from __future__ import annotations

from gpu_runclaude1.endpoints import ComponentCellResult, compute_primary_endpoint
from gpu_runclaude1.strata import STRATUM_H, STRATUM_L


def _component(system_id, family, index, stratum, m0_any, m3_any, n_cne=0, n_scored=12):
    return ComponentCellResult(
        system_id=system_id,
        family=family,
        component_index=index,
        stratum=stratum,
        m0_any=m0_any,
        m3_any=m3_any,
        n_could_not_evaluate=n_cne,
        n_scored=n_scored,
    )


def test_primary_endpoint_k_zero_uses_family_wilson_as_bound_of_record():
    """v2.1 V2-MAJ-3: at K=0 the two-stage bootstrap percentile is exactly
    [0, 0] -- reporting it as the upper bound would violate rule 01 item 8.
    The bound of record must be the 8-cluster family-level Wilson instead.
    """
    components = [
        _component(f"sys_{i}", f"fam_{i % 4}", 0, STRATUM_H, m0_any=0, m3_any=0)
        for i in range(20)
    ]
    result = compute_primary_endpoint(components, bootstrap_resamples=500, bootstrap_seed=20260909)
    assert result.k_gains == 0
    assert result.cluster_bootstrap.ci_low == 0.0
    assert result.cluster_bootstrap.ci_high == 0.0
    assert result.bound_of_record_method == "family_level_wilson_8_cluster"
    assert result.bound_of_record == (result.family_wilson[0], result.family_wilson[1])
    assert result.bound_of_record[1] > 0.0  # not the degenerate [0, 0]


def test_primary_endpoint_k_positive_uses_cluster_bootstrap_as_bound_of_record():
    components = [
        _component(f"sys_{i}", f"fam_{i % 4}", 0, STRATUM_H, m0_any=0, m3_any=(1 if i == 0 else 0))
        for i in range(20)
    ]
    result = compute_primary_endpoint(components, bootstrap_resamples=500, bootstrap_seed=20260909)
    assert result.k_gains == 1
    assert result.bound_of_record_method == "two_stage_cluster_bootstrap_percentile_95"
    assert result.bound_of_record == (result.cluster_bootstrap.ci_low, result.cluster_bootstrap.ci_high)


def test_primary_endpoint_ignores_l_stratum_components():
    components = [
        _component("sys_h", "fam_0", 0, STRATUM_H, m0_any=0, m3_any=1),
        _component("sys_l", "fam_0", 1, STRATUM_L, m0_any=0, m3_any=1),  # would be a gain, but not in H
    ]
    result = compute_primary_endpoint(components, bootstrap_resamples=100, bootstrap_seed=1)
    assert result.n_h == 1
    assert result.k_gains == 1


def test_two_sided_sensitivity_flags_undecidable_when_directions_disagree():
    """v2 §7.5 item 3: if the non-match and match directions land on
    different ladder rungs, sensitivity_agrees must be False.
    """
    # |H| small enough that flipping one could-not-evaluate component from
    # non-match to match crosses the ladder cutpoint.
    components = [_component(f"sys_{i}", f"fam_{i % 2}", 0, STRATUM_H, m0_any=0, m3_any=0) for i in range(40)]
    # Mark one component as could-not-evaluate so the adversarial recount flips it to a gain.
    components[0] = _component("sys_flipped", "fam_0", 0, STRATUM_H, m0_any=0, m3_any=0, n_cne=1)
    result = compute_primary_endpoint(components, bootstrap_resamples=100, bootstrap_seed=1)
    assert result.could_not_evaluate_rate > 0.0
    # ladder_cutpoint(40) == 1, so K=0 -> "no_gain_observed_bound_only" while
    # the adversarial K=1 -> "weak_gain": the two rungs differ.
    assert result.sensitivity_verdict_non_match_direction != result.sensitivity_verdict_match_direction
    assert result.sensitivity_agrees is False
