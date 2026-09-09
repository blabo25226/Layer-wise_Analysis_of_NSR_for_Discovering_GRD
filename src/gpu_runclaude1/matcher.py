"""The M0/M1/M3 matcher cascade, failure taxonomy, and monotonicity audit (v2 §7.4, §7.5).

M2 is **cut** (v2 §18.1) and is never called from this module.

Every comparison feeds **infix** to both sides (rule R1, AUDIT-CRIT-2):
``phase3/cells/*.json:true_structure`` is prefix-derived and must never reach
this module. Callers must pass ``true_infix`` (the cell's ``true_formula``
field, or ``phase2/validation.json:teacher_infix`` /
``teacher_components_infix``) and ``candidate_formula_raw`` -- both already
infix strings emitted by ODEFormer / GPU_RUN5.

Frozen definitions of record:

* **M0** -- ``src/gpu_run5/evaluation.py:41 formula_metrics(teacher_infix,
  candidate_formula_raw)``, fields ``exponent_aware_skeleton_exact`` (system)
  and ``component_exponent_aware_skeleton_exact`` (component).
* **M1** -- ``src/gpu_run4/formulas.py:479 compare_formulas(..., skip_cas=True)
  ["canonical_exact"]`` (system level; component level is this module's own
  index-aligned canonicalized-tree equality, needed for the cascade
  increment table and the monotonicity audit -- not itself a v2 endpoint).
* **M3** -- exactly ``src/evaluation/equation_metrics.py:169
  symbolic_recovery(...)["skeleton"]``, via the reason-carrying
  ``skeleton_equivalence_with_reason`` added beside it, and **no other key**
  (M3 pinning, AUDIT-MAJ-1).

Every non-match carries an explicit ``failure_reason`` (v2 §7.5 item 1):
``proved_different`` (a decided non-match) is always distinguished from
``could_not_evaluate`` (an unprovable comparison) -- there is no code path in
this module that returns a bare, unlabelled non-match.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional, Sequence

from evaluation.equation_metrics import skeleton_equivalence_with_reason
from gpu_run4.formulas import compare_formulas, parse_infix_component, parse_system
from gpu_run5.evaluation import formula_metrics

MATCHED = "matched"
PROVED_DIFFERENT = "proved_different"
COULD_NOT_EVALUATE = "could_not_evaluate"

_COULD_NOT_EVALUATE_REASONS = frozenset(
    {"SkeletonParseFailure", "SkeletonEvaluationFailure", "SymbolicEquivalenceTimeout", "ParseError"}
)


@dataclass(frozen=True)
class ComponentMatch:
    component_index: int
    m0: float
    m1: float
    m3: float
    match_outcome_m3: str  # MATCHED | PROVED_DIFFERENT | COULD_NOT_EVALUATE
    failure_reason: Optional[str]


@dataclass(frozen=True)
class MatchResult:
    """One (truth, candidate) system-level comparison, all three levels, at
    both system and component resolution, computed in a single pass from the
    same parsed infix inputs (v2 §5 item 1 fair-comparison budget).
    """

    component_count_match: bool
    m0_system: float
    m1_system: float
    m3_system: float
    m0_any_components: list  # 1.0/0.0 per component index (M0 component hit)
    components: tuple  # tuple[ComponentMatch, ...]
    valid: bool
    failure_reason: Optional[str]


def _outcome_for_skeleton(skeleton: float, reason: Optional[str]) -> str:
    if skeleton == 1.0:
        return MATCHED
    if reason in _COULD_NOT_EVALUATE_REASONS:
        return COULD_NOT_EVALUATE
    return PROVED_DIFFERENT


def score_pair(true_infix: str, candidate_infix: str) -> MatchResult:
    """Score one (truth, candidate) system pair under M0, M1 and M3 (v2 §7.4).

    Both inputs are parsed as infix, always (``as_prefix=False``), never
    auto-detected, so the derivation path can never silently drift (rule R1).
    """
    true_parsed = parse_system(true_infix, as_prefix=False)
    cand_parsed = parse_system(candidate_infix, as_prefix=False)
    component_count_match = len(true_parsed["components"]) == len(cand_parsed["components"])

    m0 = formula_metrics(true_infix, candidate_infix)
    m0_system = float(m0["exponent_aware_skeleton_exact"])
    m0_components = [float(v) for v in m0["component_exponent_aware_skeleton_exact"]]

    m1_compare = compare_formulas(true_infix, candidate_infix, as_prefix=False, skip_cas=True)
    m1_system = float(m1_compare["canonical_exact"])

    n_components = max(len(true_parsed["components"]), len(cand_parsed["components"]), 1)
    true_components = list(true_parsed["components"]) + [None] * (n_components - len(true_parsed["components"]))
    cand_components = list(cand_parsed["components"]) + [None] * (n_components - len(cand_parsed["components"]))
    true_raw = list(true_parsed["components_raw"]) + [""] * (n_components - len(true_parsed["components_raw"]))
    cand_raw = list(cand_parsed["components_raw"]) + [""] * (n_components - len(cand_parsed["components_raw"]))

    component_results: list[ComponentMatch] = []
    all_m3_match = component_count_match and n_components > 0
    for index in range(n_components):
        if not component_count_match:
            # v2.1 V2-MIN-9: a component-count mismatch is a decided
            # non-match (an observed fact, not a failed evaluation), never
            # could_not_evaluate, and is excluded from the
            # could_not_evaluate_rate numerator.
            component_results.append(
                ComponentMatch(index, 0.0, 0.0, 0.0, PROVED_DIFFERENT, "ComponentCountMismatch")
            )
            all_m3_match = False
            continue
        true_tree = true_components[index]
        cand_tree = cand_components[index]
        if true_tree is None or cand_tree is None:
            component_results.append(
                ComponentMatch(index, 0.0, 0.0, 0.0, COULD_NOT_EVALUATE, "ParseError")
            )
            all_m3_match = False
            continue
        m1_component = 1.0 if true_tree == cand_tree else 0.0
        skeleton, reason = skeleton_equivalence_with_reason(true_raw[index], cand_raw[index])
        outcome = _outcome_for_skeleton(skeleton, reason)
        m0_component = m0_components[index] if index < len(m0_components) else 0.0
        component_results.append(
            ComponentMatch(index, m0_component, m1_component, float(skeleton), outcome, reason)
        )
        if skeleton != 1.0:
            all_m3_match = False

    m3_system = 1.0 if all_m3_match else 0.0
    valid = bool(m0["valid"]) and component_count_match
    failure_reason = None if component_count_match else "ComponentCountMismatch"
    if not valid and failure_reason is None:
        failure_reason = m0.get("failure_reason")

    return MatchResult(
        component_count_match=component_count_match,
        m0_system=m0_system,
        m1_system=m1_system,
        m3_system=m3_system,
        m0_any_components=m0_components,
        components=tuple(component_results),
        valid=valid,
        failure_reason=failure_reason,
    )


@dataclass(frozen=True)
class MonotonicityAudit:
    n_checked: int
    n_violations: int
    violation_rate: float
    violations: tuple
    severity: str  # "ok" | "minor" | "MAJOR" | "CRITICAL"


def audit_monotonicity(
    results: Sequence[tuple[str, MatchResult]],
    *,
    minor_max_rate: float,
    major_max_rate: float,
) -> MonotonicityAudit:
    """M0 subset-of M1 subset-of M3, checked at both system and component
    resolution (v2 §7.5 item 4). A violation is any triple where a *more
    restrictive* level matched but a *more permissive* level (M1 over M0, M3
    over M1) did not.
    """
    violations: list[dict[str, Any]] = []
    n_checked = 0
    for label, result in results:
        n_checked += 1
        if result.m0_system == 1.0 and result.m1_system != 1.0:
            violations.append({"scope": "system", "label": label, "level_pair": "M0->M1"})
        if result.m1_system == 1.0 and result.m3_system != 1.0:
            violations.append({"scope": "system", "label": label, "level_pair": "M1->M3"})
        for component in result.components:
            n_checked += 1
            if component.m0 == 1.0 and component.m1 != 1.0:
                violations.append(
                    {"scope": "component", "label": label, "component_index": component.component_index, "level_pair": "M0->M1"}
                )
            if component.m1 == 1.0 and component.m3 != 1.0:
                violations.append(
                    {"scope": "component", "label": label, "component_index": component.component_index, "level_pair": "M1->M3"}
                )
    rate = (len(violations) / n_checked) if n_checked else 0.0
    if rate > major_max_rate:
        severity = "CRITICAL"
    elif rate > minor_max_rate:
        severity = "MAJOR"
    elif violations:
        severity = "minor"
    else:
        severity = "ok"
    return MonotonicityAudit(
        n_checked=n_checked,
        n_violations=len(violations),
        violation_rate=rate,
        violations=tuple(violations),
        severity=severity,
    )


def could_not_evaluate_rate(component_matches: Sequence[ComponentMatch]) -> float:
    """A2-S6: the reported failure endpoint with a frozen 2.0% maximum (v2 §7.5 item 2)."""
    if not component_matches:
        return 0.0
    n_could_not_evaluate = sum(1 for c in component_matches if c.match_outcome_m3 == COULD_NOT_EVALUATE)
    return n_could_not_evaluate / len(component_matches)
