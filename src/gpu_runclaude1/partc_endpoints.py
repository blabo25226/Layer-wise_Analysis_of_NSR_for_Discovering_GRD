"""Part C corpus-level endpoints, the reference-resolution gate, and the
null-credibility / Gate C->report mechanics (v2 §8.3, §10.1, §10.3).

Pure Python/numpy, no torch, no model object -- everything here consumes
already-scored per-cell quantities (:mod:`gpu_runclaude1.partc` produces the
per-cell Stahlberg-Byrne indicator and the re-encoding audit; the phase
script produces the raw log-probs). This module is the aggregation layer:
per-system roll-up, the corpus-level Wilson + family-clustered bootstrap
(reusing :mod:`gpu_runclaude1.ladder`'s frozen resampling scheme rather than
re-deriving it), the C2-S6/S7 descriptive rank/IQR panel, and the frozen
attribution rule with its named dead zone.

Two frozen numbers this module does **not** invent: ``N_IN_SUPPORT_MINIMUM``
and the 10% re-encoding tolerances live in :mod:`gpu_runclaude1.constants`
and are imported, never re-typed.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Mapping, Optional, Sequence

import numpy as np

from gpu_runclaude1.constants import (
    CELL_REENCODING_MISMATCH_CELL_MAX_FRACTION,
    CLUSTER_BOOTSTRAP_RESAMPLES,
    CLUSTER_BOOTSTRAP_SEED,
    N_IN_SUPPORT_MINIMUM,
    UNRELIABLE_REENCODING_CELL_MAX_FRACTION,
)
from gpu_runclaude1.ladder import ClusterBootstrapResult, wilson_interval
from gpu_runclaude1.partc import system_attribution

# v2 §8.3: length-matching window for the C2-S6 descriptive panel only
# (never decision-bearing). Frozen in prose ("±20% length-matching"); no
# named constant exists in gpu_runclaude1.constants for it, so it is defined
# here, next to the one endpoint that uses it, rather than invented at the
# call site.
LENGTH_MATCH_TOLERANCE_FRACTION = 0.20

# v2 §8.3 C2-S7's frozen gate: "if the GT gap exceeds 5 x IQR in more than
# 20% of cells, the reference distribution has no resolution".
C2_S7_IQR_MULTIPLE = 5.0
C2_S7_CELL_FRACTION_GATE = 0.20

# v2 §8.3 C2-S4: dropped if > 20% of in-support systems lack an affine encoding.
C2_S4_MISSING_SYSTEM_FRACTION_GATE = 0.20


# ---------------------------------------------------------------------------
# Per-system roll-up
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SystemRollup:
    system_id: str
    family: str
    n_usable_cells: int
    sb_rate_sel: Optional[float]
    sb_rate_best: Optional[float]
    e2_system: bool
    e3_system: bool
    e2_system_best: bool
    e3_system_best: bool


def rollup_system(system_id: str, family: str, sb_sel_values: Sequence[int], sb_best_values: Sequence[int]) -> SystemRollup:
    """v2 §8.3: ``sb_rate(s)`` = mean of ``sb_sel`` over the system's usable
    cells; ``E3_system`` / ``E2_system`` from :func:`gpu_runclaude1.partc.system_attribution`.

    A system with zero usable cells contributes neither E2 nor E3 (there is
    no usable evidence either way) but is **not** dropped from the caller's
    denominator -- the frozen corpus rate divides by ``n_in_support``, not
    by the count of systems with usable evidence, so a zero-usable-cell
    system must be visible in the artifact, never silently absorbed.
    """
    n = len(sb_sel_values)
    if n == 0:
        return SystemRollup(system_id, family, 0, None, None, False, False, False, False)
    sb_rate_sel = float(np.mean(sb_sel_values))
    sb_rate_best = float(np.mean(sb_best_values)) if sb_best_values else None
    attribution_sel = system_attribution(sb_rate_sel)
    attribution_best = system_attribution(sb_rate_best) if sb_rate_best is not None else {"E2_system": False, "E3_system": False}
    return SystemRollup(
        system_id=system_id,
        family=family,
        n_usable_cells=n,
        sb_rate_sel=sb_rate_sel,
        sb_rate_best=sb_rate_best,
        e2_system=attribution_sel["E2_system"],
        e3_system=attribution_sel["E3_system"],
        e2_system_best=attribution_best["E2_system"],
        e3_system_best=attribution_best["E3_system"],
    )


# ---------------------------------------------------------------------------
# Corpus-level proportion endpoints (C2-P, C2-S1, and the sb_best variants)
# ---------------------------------------------------------------------------


def two_stage_cluster_bootstrap_binary(
    indicators_by_system: Mapping[str, bool],
    family_of_system: Mapping[str, str],
    *,
    n_resamples: int = CLUSTER_BOOTSTRAP_RESAMPLES,
    seed: int = CLUSTER_BOOTSTRAP_SEED,
) -> ClusterBootstrapResult:
    """The frozen family-clustered bootstrap (v2 §9.1), applied to a
    system-level 0/1 indicator (one value per system) instead of Part A's
    per-component indicator lists. Delegates the actual two-stage
    (family-then-system) resampling to :func:`gpu_runclaude1.ladder.two_stage_cluster_bootstrap`
    by wrapping each system's single indicator in a length-1 list, so the
    resampling scheme, seed and resample count are exactly Part A's, never
    re-derived.
    """
    from gpu_runclaude1.ladder import two_stage_cluster_bootstrap

    wrapped = {system_id: [int(bool(value))] for system_id, value in indicators_by_system.items()}
    return two_stage_cluster_bootstrap(wrapped, family_of_system, n_resamples=n_resamples, seed=seed)


@dataclass(frozen=True)
class ProportionEndpoint:
    k: int
    n: int
    rate: float
    wilson_95: tuple
    cluster_bootstrap: ClusterBootstrapResult


def corpus_proportion_endpoint(
    indicators_by_system: Mapping[str, bool],
    family_of_system: Mapping[str, str],
    n_in_support: int,
) -> ProportionEndpoint:
    """A corpus-level rate over ``n_in_support`` systems (the frozen
    denominator, v2 §8.3), with the family-clustered bootstrap as the
    interval of record and the plain Wilson reported alongside.
    """
    k = sum(1 for value in indicators_by_system.values() if value)
    rate = (k / n_in_support) if n_in_support else float("nan")
    wilson = wilson_interval(k, n_in_support) if n_in_support else (float("nan"), float("nan"))
    bootstrap = two_stage_cluster_bootstrap_binary(indicators_by_system, family_of_system)
    return ProportionEndpoint(k=k, n=n_in_support, rate=rate, wilson_95=wilson, cluster_bootstrap=bootstrap)


# ---------------------------------------------------------------------------
# C2-S3 / C2-S4: paired continuous differences, cluster-bootstrapped
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ContinuousClusterBootstrapResult:
    point_estimate: float
    ci_low: float
    ci_high: float
    n_resamples: int
    seed: int


def two_stage_cluster_bootstrap_continuous(
    values_by_system: Mapping[str, float],
    family_of_system: Mapping[str, str],
    *,
    n_resamples: int = CLUSTER_BOOTSTRAP_RESAMPLES,
    seed: int = CLUSTER_BOOTSTRAP_SEED,
) -> ContinuousClusterBootstrapResult:
    """The same family-then-system two-stage resampling scheme as
    :func:`gpu_runclaude1.ladder.two_stage_cluster_bootstrap`, applied to a
    continuous per-system mean (v2 §8.3 C2-S3/C2-S4 call for a
    cluster-bootstrapped paired difference, not a proportion). Not a
    modification of the frozen Part A module -- Part A's bootstrap is
    binary-indicator-only by construction (it averages 0/1 values); this is
    new code for a different endpoint class, using the identical resampling
    topology and the identical frozen seed/resample count.
    """
    families: dict[str, list[str]] = {}
    for system_id, family in family_of_system.items():
        families.setdefault(family, []).append(system_id)
    family_names = sorted(families)
    if not family_names or not values_by_system:
        return ContinuousClusterBootstrapResult(float("nan"), float("nan"), float("nan"), n_resamples, seed)

    all_values = list(values_by_system.values())
    point = float(np.mean(all_values))

    rng = np.random.default_rng(seed)
    means = np.empty(n_resamples, dtype=float)
    for resample_index in range(n_resamples):
        resampled_families = rng.choice(family_names, size=len(family_names), replace=True)
        pooled: list[float] = []
        for fam in resampled_families:
            systems = families[fam]
            resampled_systems = rng.choice(systems, size=len(systems), replace=True)
            for system_id in resampled_systems:
                if system_id in values_by_system:
                    pooled.append(values_by_system[system_id])
        means[resample_index] = float(np.mean(pooled)) if pooled else float("nan")
    finite = means[np.isfinite(means)]
    if finite.size == 0:
        return ContinuousClusterBootstrapResult(point, float("nan"), float("nan"), n_resamples, seed)
    lo, hi = np.percentile(finite, [2.5, 97.5])
    return ContinuousClusterBootstrapResult(point, float(lo), float(hi), n_resamples, seed)


# ---------------------------------------------------------------------------
# C2-S6 / C2-S7: the descriptive rank panel and its gate
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CellRankPanel:
    candidate_logprob_iqr: Optional[float]
    gt_gap_in_iqr_units: Optional[float]
    rank_pct_sum: Optional[float]
    rank_pct_per_token: Optional[float]
    rank_pct_length_matched: Optional[float]
    below_all_indicator: Optional[int]
    length_match_unavailable: bool


def compute_cell_rank_panel(
    gt_logprob_sum: float,
    gt_token_length: int,
    usable_candidate_logprob_sums: Sequence[float],
    usable_candidate_token_lengths: Sequence[int],
) -> CellRankPanel:
    """v2 §8.3 C2-S6/C2-S7, computed from the summed log-probs of the
    ``lp_best``-eligible ("usable") candidates in one cell -- no per-token
    vocabulary softmax needed (that is C2-S5's separate, per-position
    computation), only the same summed-log-prob values already produced for
    the Stahlberg-Byrne discriminator.

    ``rank_pct_sum`` = fraction of usable candidates whose summed log-prob
    **exceeds** the GT's (0.0 = GT beats every candidate; 1.0 = GT is beaten
    by every candidate; ties do not count as "exceeds"). This direction and
    tie convention are an explicit choice, made once here, because v2 §8.3
    names the quantity without giving its exact formula; a statistical
    reviewer should confirm this convention before C2-S6 is cited.
    ``rank_pct_per_token`` is the same computation on per-token mean
    log-prob. ``rank_pct_length_matched`` restricts the candidate set to
    those within ±20% of ``gt_token_length`` (the frozen, descriptive-only
    length-matching window named in the §8.3 preamble); if no candidate
    qualifies, ``LengthMatchUnavailable`` and the field is excluded from this
    cell's contribution to the panel (rule 03 exclusion (d)).
    """
    n = len(usable_candidate_logprob_sums)
    if n == 0:
        return CellRankPanel(None, None, None, None, None, None, True)

    values = np.asarray(usable_candidate_logprob_sums, dtype=float)
    lengths = np.asarray(usable_candidate_token_lengths, dtype=float)

    q1, q3 = np.percentile(values, [25, 75])
    iqr = float(q3 - q1)
    median = float(np.median(values))
    if iqr > 0:
        gap_in_iqr_units = (median - gt_logprob_sum) / iqr
    else:
        gap_in_iqr_units = None

    rank_pct_sum = float(np.mean(values > gt_logprob_sum))
    below_all_indicator = int(bool(np.all(values > gt_logprob_sum)))

    per_token_values = values / np.where(lengths > 0, lengths, np.nan)
    gt_per_token = gt_logprob_sum / gt_token_length if gt_token_length else float("nan")
    finite_per_token = per_token_values[np.isfinite(per_token_values)]
    rank_pct_per_token = float(np.mean(finite_per_token > gt_per_token)) if finite_per_token.size else None

    tolerance = LENGTH_MATCH_TOLERANCE_FRACTION * gt_token_length
    length_mask = np.abs(lengths - gt_token_length) <= tolerance
    length_matched_values = values[length_mask]
    if length_matched_values.size:
        rank_pct_length_matched = float(np.mean(length_matched_values > gt_logprob_sum))
        length_match_unavailable = False
    else:
        rank_pct_length_matched = None
        length_match_unavailable = True

    return CellRankPanel(
        candidate_logprob_iqr=iqr,
        gt_gap_in_iqr_units=gap_in_iqr_units,
        rank_pct_sum=rank_pct_sum,
        rank_pct_per_token=rank_pct_per_token,
        rank_pct_length_matched=rank_pct_length_matched,
        below_all_indicator=below_all_indicator,
        length_match_unavailable=length_match_unavailable,
    )


@dataclass(frozen=True)
class ReferenceResolutionGate:
    n_cells_considered: int
    n_cells_exceeding: int
    fraction_exceeding: float
    gate_ok: bool  # True == C2-S6 MAY be interpreted; False == it may NOT


def reference_resolution_gate(panels: Sequence[CellRankPanel]) -> ReferenceResolutionGate:
    """v2 §8.3 C2-S7's frozen gate on C2-S6: "if the GT gap exceeds 5 x IQR
    in more than 20% of cells, the reference distribution has no resolution
    and no rank-based statistic in C2-S6 may be interpreted at all". A cell
    whose IQR collapsed to zero (:attr:`CellRankPanel.gt_gap_in_iqr_units` is
    None) cannot be resolved either and counts as exceeding, since a
    zero-spread reference distribution has no resolution by construction.
    """
    considered = [p for p in panels if p.candidate_logprob_iqr is not None]
    n = len(considered)
    if n == 0:
        return ReferenceResolutionGate(0, 0, 0.0, False)
    exceeding = 0
    for panel in considered:
        if panel.gt_gap_in_iqr_units is None:
            exceeding += 1
        elif abs(panel.gt_gap_in_iqr_units) > C2_S7_IQR_MULTIPLE:
            exceeding += 1
    fraction = exceeding / n
    return ReferenceResolutionGate(n, exceeding, fraction, fraction <= C2_S7_CELL_FRACTION_GATE)


# ---------------------------------------------------------------------------
# Corpus-level attribution rule (frozen, with its dead zone named)
# ---------------------------------------------------------------------------


def corpus_attribution_rule(c2p_bootstrap: ClusterBootstrapResult, c2s1_bootstrap: ClusterBootstrapResult) -> str:
    """v2 §8.3: E3 predominant iff the clustered *lower* bound of C2-P > 0.5;
    E2 predominant iff the clustered *upper* bound of C2-P < 0.5 AND the
    clustered *lower* bound of C2-S1 > 0.5; otherwise
    ``neither_E2_nor_E3_predominant`` -- a real, reportable result, distinct
    from ``undecidable`` (which is reserved for instrument failure, i.e. a
    failed Gate C->report, and is never returned by this function).
    """
    if c2p_bootstrap.ci_low > 0.5:
        return "E3_predominant"
    if c2p_bootstrap.ci_high < 0.5 and c2s1_bootstrap.ci_low > 0.5:
        return "E2_predominant"
    return "neither_E2_nor_E3_predominant"


# ---------------------------------------------------------------------------
# Null-credibility conditions and Gate C -> report
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class NullCredibilityConditions:
    nc1_regression_identity_ok: bool
    nc2_reencoding_audit_ok: bool
    nc3_identity_assertions_ok: bool
    nc4_s7_reported: bool
    nc5_n_in_support_ok: bool

    @property
    def gate_c_to_report_ok(self) -> bool:
        """v2 §10.1: "Part C endpoints are reported only if NC1-NC3 pass."
        NC4/NC5 are tracked and disclosed but do not gate reporting: NC4's
        failure gates only C2-S6 (v2 §8.3), and NC5 already gated Part C down
        to ``exploratory`` at Gate B->C, upstream of this gate.
        """
        return self.nc1_regression_identity_ok and self.nc2_reencoding_audit_ok and self.nc3_identity_assertions_ok


def evaluate_null_credibility(
    *,
    regression_identity_ok: bool,
    unreliable_reencoding_cell_fraction: float,
    n_cell_identity_mismatches: int,
    all_systems_distinct_payload_ok: bool,
    n_in_support: int,
) -> NullCredibilityConditions:
    nc2 = unreliable_reencoding_cell_fraction <= UNRELIABLE_REENCODING_CELL_MAX_FRACTION
    nc3 = (n_cell_identity_mismatches == 0) and all_systems_distinct_payload_ok
    nc5 = n_in_support >= N_IN_SUPPORT_MINIMUM
    return NullCredibilityConditions(
        nc1_regression_identity_ok=regression_identity_ok,
        nc2_reencoding_audit_ok=nc2,
        nc3_identity_assertions_ok=nc3,
        nc4_s7_reported=True,  # always True: this module always computes and reports it when called
        nc5_n_in_support_ok=nc5,
    )


# ---------------------------------------------------------------------------
# C2-S9 (exploratory): simple pooled correlations, no decision content
# ---------------------------------------------------------------------------


def _pearson_r(x: Sequence[float], y: Sequence[float]) -> Optional[float]:
    x_arr = np.asarray(x, dtype=float)
    y_arr = np.asarray(y, dtype=float)
    if x_arr.size < 2 or np.std(x_arr) == 0 or np.std(y_arr) == 0:
        return None
    return float(np.corrcoef(x_arr, y_arr)[0, 1])


@dataclass(frozen=True)
class ExploratoryLengthCorrelations:
    n: int
    r_length_vs_lp_gt: Optional[float]
    r_length_vs_sb_sel: Optional[float]


def compute_c2s9(gt_token_lengths: Sequence[int], gt_logprob_sums: Sequence[float], sb_sel_values: Sequence[int]) -> ExploratoryLengthCorrelations:
    """v2 §8.3 C2-S9, exploratory only: GT token length vs ``lp_gt`` and vs
    ``sb_sel``, pooled Pearson correlation over all usable cells (no
    per-system clustering -- an exploratory endpoint carries no confirmatory
    interval by construction, rule 09).
    """
    return ExploratoryLengthCorrelations(
        n=len(gt_token_lengths),
        r_length_vs_lp_gt=_pearson_r(gt_token_lengths, gt_logprob_sums),
        r_length_vs_sb_sel=_pearson_r(gt_token_lengths, sb_sel_values),
    )
