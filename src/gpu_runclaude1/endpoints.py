"""Part A primary-endpoint aggregation: gain(s,i), the ANY-over-cells roll-up,
the two-sided sensitivity analysis, and the descriptive secondaries (v2 §7.1,
§7.5 item 3, §7.8).

Matching itself (:mod:`gpu_runclaude1.matcher`) never runs without a
:class:`gpu_runclaude1.strata.StrataFrozenToken` in the driving phase script;
this module consumes already-scored per-(cell, candidate, component) results
and is agnostic to how they were produced, so it can be unit-tested on
synthetic data without recomputing the frozen ordering guarantee itself.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Sequence

from gpu_runclaude1.ladder import (
    ClusterBootstrapResult,
    family_level_wilson,
    ladder_cutpoint,
    ladder_verdict,
    two_stage_cluster_bootstrap,
    wilson_interval,
)
from gpu_runclaude1.matcher import COULD_NOT_EVALUATE
from gpu_runclaude1.strata import STRATUM_H


@dataclass(frozen=True)
class ComponentCellResult:
    """One (system, component_index) triple's reduction over its 12 cells,
    already ANY-reduced over the usable candidates within each cell.
    """

    system_id: str
    family: str
    component_index: int
    stratum: str
    m0_any: int  # OR over 12 cells of (OR over candidates of m0 component match)
    m3_any: int
    n_could_not_evaluate: int
    n_scored: int


def gain_indicator(m0_any: int, m3_any: int) -> int:
    """gain(s,i) = 1[m3_any = 1 AND m0_any = 0] (v2 §7.1)."""
    return int(m3_any == 1 and m0_any == 0)


@dataclass(frozen=True)
class PrimaryEndpointResult:
    n_h: int
    k_gains: int
    ladder_cutpoint: int
    verdict: str
    wilson_95: tuple
    cluster_bootstrap: ClusterBootstrapResult
    family_wilson: tuple
    bound_of_record: tuple
    bound_of_record_method: str
    could_not_evaluate_rate: float
    sensitivity_agrees: bool
    sensitivity_verdict_non_match_direction: str
    sensitivity_verdict_match_direction: str


def compute_primary_endpoint(
    components: Sequence[ComponentCellResult],
    *,
    bootstrap_resamples: int,
    bootstrap_seed: int,
) -> PrimaryEndpointResult:
    """The primary endpoint over the frozen Hill stratum H (v2 §7.1, §7.5 item 3).

    Every ``ComponentCellResult`` must already carry ``stratum`` from a
    :class:`gpu_runclaude1.strata.StrataFrozenToken` (the caller enforces
    that; this function only filters on the label).
    """
    h_components = [c for c in components if c.stratum == STRATUM_H]
    n_h = len(h_components)

    gains = [gain_indicator(c.m0_any, c.m3_any) for c in h_components]
    k = sum(gains)

    indicators_by_system: dict[str, list[int]] = {}
    family_of_system: dict[str, str] = {}
    for component, gain in zip(h_components, gains):
        indicators_by_system.setdefault(component.system_id, []).append(gain)
        family_of_system[component.system_id] = component.family

    wilson = wilson_interval(k, n_h) if n_h else (float("nan"), float("nan"))
    bootstrap = two_stage_cluster_bootstrap(
        indicators_by_system, family_of_system, n_resamples=bootstrap_resamples, seed=bootstrap_seed
    )
    family_wilson = family_level_wilson(indicators_by_system, family_of_system) if indicators_by_system else (float("nan"), float("nan"), 0, 0)

    # v2.1 V2-MAJ-3: at K = 0 the two-stage bootstrap percentile is exactly
    # [0, 0] (every resample is all-zero), which would license "the upper
    # bound is 0.0000" -- exactly what rule 01 item 8 forbids. The bound of
    # record at K = 0 is therefore the 8-cluster family-level Wilson
    # interval instead; at K >= 1 the bootstrap remains the interval of
    # record (v2 §7.1).
    if k == 0:
        bound_of_record = (family_wilson[0], family_wilson[1])
        bound_of_record_method = "family_level_wilson_8_cluster"
    else:
        bound_of_record = (bootstrap.ci_low, bootstrap.ci_high)
        bound_of_record_method = "two_stage_cluster_bootstrap_percentile_95"

    n_could_not_evaluate = sum(c.n_could_not_evaluate for c in h_components)
    n_scored = sum(c.n_scored for c in h_components)
    cne_rate = (n_could_not_evaluate / n_scored) if n_scored else 0.0

    # v2 §7.5 item 3: two-sided sensitivity, only meaningful if any could-not-evaluate exists.
    verdict_non_match_direction = ladder_verdict(k, n_h) if n_h else "not_measurable"
    if n_could_not_evaluate > 0:
        # Adversarial direction: every could-not-evaluate triple counted as a match.
        # A component already gaining stays a gain; a component with zero could-not-evaluate
        # contributions is unaffected. This module receives already-ANY-reduced per-component
        # results, so the adversarial recount is: any component with n_could_not_evaluate > 0
        # AND gain == 0 is flipped to gain = 1 (the could-not-evaluate triple is presumed a match).
        adversarial_gains = [
            1 if (gain == 0 and component.n_could_not_evaluate > 0) else gain
            for component, gain in zip(h_components, gains)
        ]
        k_adversarial = sum(adversarial_gains)
        verdict_match_direction = ladder_verdict(k_adversarial, n_h) if n_h else "not_measurable"
    else:
        verdict_match_direction = verdict_non_match_direction

    return PrimaryEndpointResult(
        n_h=n_h,
        k_gains=k,
        ladder_cutpoint=ladder_cutpoint(n_h) if n_h else 0,
        # v2.1 §10.3 / §7.5 item 3: "the two-sided sensitivity analysis
        # disagrees on the rung" is itself one of the ``undecidable``
        # criteria. Reporting `verdict_non_match_direction` unconditionally
        # here (as this function did until this fix) let a disagreement
        # silently present as an ordinary ladder rung (e.g.
        # `no_gain_observed_bound_only`) with `sensitivity_agrees: false`
        # sitting unread beside it -- the verdict of record must fold that
        # disagreement in, not leave it to the caller to notice.
        verdict=(
            verdict_non_match_direction
            if verdict_non_match_direction == verdict_match_direction
            else "undecidable (two-sided sensitivity disagreement)"
        ),
        wilson_95=wilson,
        cluster_bootstrap=bootstrap,
        family_wilson=family_wilson,
        bound_of_record=bound_of_record,
        bound_of_record_method=bound_of_record_method,
        could_not_evaluate_rate=cne_rate,
        sensitivity_agrees=(verdict_non_match_direction == verdict_match_direction),
        sensitivity_verdict_non_match_direction=verdict_non_match_direction,
        sensitivity_verdict_match_direction=verdict_match_direction,
    )


@dataclass(frozen=True)
class SecondaryEndpoints:
    l_stratum_gain_rate: float
    l_stratum_n: int
    h_minus_l_difference: float
    m3_level_overall: float
    m3_level_h: float
    m3_level_l: float


def compute_secondaries(components: Sequence[ComponentCellResult]) -> SecondaryEndpoints:
    """A2-S1 (L-stratum gain and H-L difference) and A2-S2 (M3 level), v2 §7.8."""
    h_components = [c for c in components if c.stratum == STRATUM_H]
    l_components = [c for c in components if c.stratum != STRATUM_H]

    def gain_rate(rows: Sequence[ComponentCellResult]) -> float:
        if not rows:
            return float("nan")
        return sum(gain_indicator(c.m0_any, c.m3_any) for c in rows) / len(rows)

    def m3_level(rows: Sequence[ComponentCellResult]) -> float:
        if not rows:
            return float("nan")
        return sum(c.m3_any for c in rows) / len(rows)

    h_rate = gain_rate(h_components)
    l_rate = gain_rate(l_components)
    return SecondaryEndpoints(
        l_stratum_gain_rate=l_rate,
        l_stratum_n=len(l_components),
        h_minus_l_difference=(h_rate - l_rate) if (h_components and l_components) else float("nan"),
        m3_level_overall=m3_level(components),
        m3_level_h=m3_level(h_components),
        m3_level_l=m3_level(l_components),
    )
