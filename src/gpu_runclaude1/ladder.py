"""Wilson intervals, the two-stage cluster bootstrap, and the outcome ladder (v2 §7.1, §7.3, §9.1-9.3).

Nothing here uses ``src/gpu_run4/aggregation.py:22 student_t_ci``: v2 forbids
it for any proportion in C0001 (STAT-M3 -- its simulated coverage at a 0.05
rate is 0.909-0.913 with a negative lower limit 5-17% of the time). Every
proportion in this module is a Wilson score interval or the two-stage cluster
bootstrap, both frozen by v2 §9.1.

The realized-``|H|`` ladder table and its operating characteristics must be
computed from the frozen formulas here and written to
``R/phase1/partA_ladder_realized.json`` **before** any match indicator is
computed (v2 §7.2 step 2); see :mod:`gpu_runclaude1.strata` for the mechanical
ordering enforcement that depends on this artifact's hash.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Mapping, Sequence

import numpy as np

Z_975 = 1.959964  # Phi^{-1}(0.975), frozen (v2 §9.1)


def wilson_interval(k: int, n: int, *, z: float = Z_975) -> tuple[float, float]:
    """Plain Wilson score interval, no continuity correction (v2 §9.1)."""
    if n <= 0:
        return (float("nan"), float("nan"))
    p_hat = k / n
    denom = 1.0 + z * z / n
    center = (p_hat + z * z / (2 * n)) / denom
    half = (z / denom) * math.sqrt(p_hat * (1 - p_hat) / n + z * z / (4 * n * n))
    lo = max(0.0, center - half)
    hi = min(1.0, center + half)
    return (lo, hi)


def ladder_cutpoint(n_h: int) -> int:
    """C = ceil(0.02 * |H|) (v2 §7.1, §9.3)."""
    return math.ceil(0.02 * n_h)


def ladder_verdict(k: int, n_h: int) -> str:
    """The primary ladder label from the observed Hill-stratum gain count K (v2 §9.3)."""
    c = ladder_cutpoint(n_h)
    if k == 0:
        return "no_gain_observed_bound_only"
    if k <= c:
        return "weak_gain"
    return "matcher_attributable_gain_confirmed"


def power_at_least_one_gain(true_rate: float, n_h: int) -> float:
    """P(K >= 1) under independence across components: 1 - (1-p)^|H| (v2 §7.3)."""
    return 1.0 - (1.0 - true_rate) ** n_h


def operating_characteristics(n_h: int, true_rates: Sequence[float]) -> list[dict[str, float]]:
    """P(K falls on each ladder rung) at |H| = n_h under a homogeneous binomial (v2 §9.3)."""
    from scipy.stats import binom

    c = ladder_cutpoint(n_h)
    rows = []
    for p in true_rates:
        dist = binom(n_h, p)
        p0 = float(dist.pmf(0))
        p_mid = float(dist.cdf(c) - dist.pmf(0))
        p_upper = float(1.0 - dist.cdf(c))
        rows.append({"true_rate": float(p), "p_lower_rung": p0, "p_middle_rung": p_mid, "p_upper_rung": p_upper})
    return rows


def realized_power_table(n_h: int, true_rates: Sequence[float] = (0.0525, 0.02, 0.01)) -> list[dict[str, float]]:
    return [{"true_rate": float(p), "power_at_least_one_gain": power_at_least_one_gain(p, n_h)} for p in true_rates]


@dataclass(frozen=True)
class ClusterBootstrapResult:
    point_estimate: float
    ci_low: float
    ci_high: float
    n_resamples: int
    seed: int
    method: str = "two_stage_cluster_bootstrap_percentile_95"


def two_stage_cluster_bootstrap(
    indicators_by_system: Mapping[str, Sequence[int]],
    family_of_system: Mapping[str, str],
    *,
    n_resamples: int,
    seed: int,
) -> ClusterBootstrapResult:
    """Families resampled with replacement, then systems within family with
    replacement, 10,000 resamples, seed 20260909 (v2 §7.1, §9.1) -- the
    **interval of record** for the primary endpoint.

    ``indicators_by_system`` maps system_id -> the 0/1 gain indicators of
    that system's components (already reduced ANY-over-12-cells); components
    within a system are never independently resampled, only carried together
    with their system.
    """
    families: dict[str, list[str]] = {}
    for system_id, family in family_of_system.items():
        families.setdefault(family, []).append(system_id)
    family_names = sorted(families)
    if not family_names:
        return ClusterBootstrapResult(float("nan"), float("nan"), float("nan"), n_resamples, seed)

    all_indicators = [v for values in indicators_by_system.values() for v in values]
    point = float(np.mean(all_indicators)) if all_indicators else float("nan")

    rng = np.random.default_rng(seed)
    rates = np.empty(n_resamples, dtype=float)
    for resample_index in range(n_resamples):
        resampled_families = rng.choice(family_names, size=len(family_names), replace=True)
        pooled: list[int] = []
        for family in resampled_families:
            systems = families[family]
            resampled_systems = rng.choice(systems, size=len(systems), replace=True)
            for system_id in resampled_systems:
                pooled.extend(indicators_by_system.get(system_id, ()))
        rates[resample_index] = float(np.mean(pooled)) if pooled else float("nan")
    finite = rates[np.isfinite(rates)]
    if finite.size == 0:
        return ClusterBootstrapResult(point, float("nan"), float("nan"), n_resamples, seed)
    lo, hi = np.percentile(finite, [2.5, 97.5])
    return ClusterBootstrapResult(point, float(lo), float(hi), n_resamples, seed)


def family_level_wilson(indicators_by_system: Mapping[str, Sequence[int]], family_of_system: Mapping[str, str]) -> tuple[float, float, int, int]:
    """8-cluster Wilson interval on the family-level indicator (v2 §7.1(c)):
    a family counts as a "hit" iff at least one of its components gained.
    Returns (lo, hi, hits, n_families).
    """
    families: dict[str, bool] = {}
    for system_id, indicators in indicators_by_system.items():
        family = family_of_system[system_id]
        hit = any(int(v) == 1 for v in indicators)
        families[family] = families.get(family, False) or hit
    n_families = len(families)
    hits = sum(1 for v in families.values() if v)
    lo, hi = wilson_interval(hits, n_families)
    return (lo, hi, hits, n_families)


def build_ladder_realized_artifact(n_h: int, strata_sha256: str) -> dict:
    """v2 §7.2 step 2's payload: the Wilson table, ladder cutpoint, and the
    OC/power tables, all computed from |H| alone -- before any matching.
    """
    reference_rates = (0.0525, 0.03, 0.02, 0.0125, 0.01, 0.005, 0.0)
    return {
        "n_h": n_h,
        "ladder_cutpoint": ladder_cutpoint(n_h),
        "wilson_table": [
            {"k": k, "wilson_95": list(wilson_interval(k, n_h))}
            for k in range(0, min(n_h, 9))
        ],
        "operating_characteristics": operating_characteristics(n_h, reference_rates),
        "power_table": realized_power_table(n_h, reference_rates),
        "sha256_of_component_strata_input": strata_sha256,
    }
