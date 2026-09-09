"""Part A mandatory control battery: PC0, PC0-CAS, PC1, PC2a-d, PC3a, PC3b (v2 §7.7).

Every control is constructed from ``phase2/validation.json``'s
``teacher_components_infix`` (never the stored, prefix-derived
``true_structure``), tagged ``positive_control_tag``, and never enters any
Part A endpoint (v2 §7.7 preamble). PC0 and PC1 gate Part A itself (an
abort); PC2a/PC3a are frozen verifications of already-known values (Q1, Q2);
PC0-CAS/PC2b/PC2c/PC2d/PC3b are reported, not gating (except through the
Gate A->B thresholds where v2 says so).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Sequence

from evaluation.equation_metrics import symbolic_recovery
from gpu_run4 import formulas as gpu_run4_formulas
from gpu_run4.formulas import compare_formulas, parse_infix_component

from gpu_runclaude1 import tree_rewrite
from gpu_runclaude1.constants import PC0_CAS_RAISED_CAP
from gpu_runclaude1.matcher import score_pair
from gpu_runclaude1.partb import rewrite_b_r1_affine_infix


def _join(components: Sequence[str]) -> str:
    return " | ".join(components)


@dataclass(frozen=True)
class ControlBatteryResult:
    control: str
    n_eligible: int
    n_pass: int
    per_system: tuple = field(repr=False)
    note: str = ""
    extra: dict = field(default_factory=dict)

    @property
    def rate(self) -> float:
        return (self.n_pass / self.n_eligible) if self.n_eligible else float("nan")


def pc0_identity(validation_rows: Sequence[dict[str, Any]]) -> ControlBatteryResult:
    """PC0: ``symbolic_recovery(T_i, T_i)["skeleton"]`` called **directly**,
    bypassing ``compare_formulas`` entirely (v2 §7.7, AUDIT-CRIT-4). Any
    failure means the matcher is broken and Part A must abort.
    """
    per_system = []
    n_components = 0
    n_component_pass = 0
    n_system_pass = 0
    for row in validation_rows:
        components = row["teacher_components_infix"]
        component_results = [symbolic_recovery(c, c)["skeleton"] for c in components]
        n_components += len(component_results)
        n_component_pass += sum(1 for v in component_results if v == 1.0)
        system_pass = all(v == 1.0 for v in component_results) and bool(component_results)
        n_system_pass += int(system_pass)
        per_system.append(
            {"system_id": row["system_id"], "component_results": component_results, "system_pass": system_pass}
        )
    return ControlBatteryResult(
        control="PC0",
        n_eligible=n_components,
        n_pass=n_component_pass,
        per_system=tuple(per_system),
        note=f"systems: {n_system_pass}/{len(validation_rows)}",
    )


def pc0_cas_self_equality(validation_rows: Sequence[dict[str, Any]]) -> ControlBatteryResult:
    """PC0-CAS: ``_sympy_components_equal(truth, truth)`` with the M1
    short-circuit bypassed and ``LANSR_SYMPY_MAX_NODES`` raised to 200 for
    this diagnostic call only (v2 §7.7). Reported, not gating; may not
    invalidate any GPU_RUN5 result.
    """
    original_cap = gpu_run4_formulas.SYMPY_MAX_NODES
    per_system = []
    n_pass = 0
    try:
        gpu_run4_formulas.SYMPY_MAX_NODES = PC0_CAS_RAISED_CAP
        for row in validation_rows:
            trees = [parse_infix_component(c) for c in row["teacher_components_infix"]]
            value, reason = gpu_run4_formulas._sympy_components_equal(trees, trees)
            passed = value == 1.0
            n_pass += int(passed)
            per_system.append({"system_id": row["system_id"], "value": value, "reason": reason, "pass": passed})
    finally:
        gpu_run4_formulas.SYMPY_MAX_NODES = original_cap
    return ControlBatteryResult(
        control="PC0_CAS",
        n_eligible=len(validation_rows),
        n_pass=n_pass,
        per_system=tuple(per_system),
        note=f"cap raised to {PC0_CAS_RAISED_CAP} for this diagnostic call only",
    )


def pc1_identity_through_compare_formulas(validation_rows: Sequence[dict[str, Any]]) -> ControlBatteryResult:
    """PC1: inject the truth as its own candidate through ``compare_formulas``
    (default ``skip_cas=False``), reproducing v1's vacuous PC1 as a
    documented artifact of the ``canonical_exact == 1.0`` short-circuit at
    ``formulas.py:493`` (AUDIT-CRIT-4). Gates nothing.
    """
    per_system = []
    n_pass = 0
    for row in validation_rows:
        text = _join(row["teacher_components_infix"])
        result = compare_formulas(text, text, as_prefix=False)
        passed = result["symbolic_equivalent"] == 1.0
        n_pass += int(passed)
        per_system.append(
            {
                "system_id": row["system_id"],
                "canonical_exact": result["canonical_exact"],
                "symbolic_equivalent": result["symbolic_equivalent"],
                "short_circuited_by_canonical_exact": result["canonical_exact"] == 1.0,
                "pass": passed,
            }
        )
    return ControlBatteryResult(
        control="PC1",
        n_eligible=len(validation_rows),
        n_pass=n_pass,
        per_system=tuple(per_system),
        note="documents the v1 artifact; carries no gate",
    )


def pc2a_neg_asymmetry(validation_rows: Sequence[dict[str, Any]]) -> ControlBatteryResult:
    """PC2a: rewrite every ``-1 * k * x_i`` to ``(-k) * x_i``.

    **Reclassified (v2.1 V2-CRIT-3): a harness-identity verification, not a
    sensitivity control.** Measured M0 = 170/170 on this exact rewrite (Q12b)
    -- the CRIT-2 fix made M0 itself a canonicalizing, constant-collapsing
    tree matcher, so it already absorbs the P4 asymmetry E0 discloses. PC2a
    therefore cannot demonstrate anything M3-specific: its non-short-
    circuited subset is empty (`short_circuited: true` for every instance),
    and it gates only on reproducing the two disclosed values, M3 170/170
    (Q1) *and* M0 170/170 (Q12b). Any other value means the harness differs
    from the audited one, not that M3 lacks sensitivity, and Part A is
    `undecidable`. It may not be cited as evidence that M3 adds anything
    beyond M0 here (v2.1 §1.3 M-i).
    """
    per_system = []
    n_pass_m3 = 0
    n_pass_m0 = 0
    n_eligible = 0
    for row in validation_rows:
        components = row["teacher_components_infix"]
        rewritten = []
        n_rewrites = 0
        for c in components:
            new_c, count = tree_rewrite.rewrite_neg_one_decay(c)
            rewritten.append(new_c)
            n_rewrites += count
        eligible = n_rewrites > 0
        n_eligible += int(eligible)
        result = score_pair(_join(components), _join(rewritten))
        m3_passed = result.m3_system == 1.0
        m0_passed = result.m0_system == 1.0
        n_pass_m3 += int(m3_passed and eligible)
        n_pass_m0 += int(m0_passed and eligible)
        per_system.append(
            {
                "system_id": row["system_id"],
                "n_rewrites": n_rewrites,
                "eligible": eligible,
                "m3_system": result.m3_system,
                "m0_system": result.m0_system,
                "short_circuited_by_m0": m0_passed,
                "pass": m3_passed and m0_passed,
            }
        )
    return ControlBatteryResult(
        control="PC2a",
        n_eligible=n_eligible,
        n_pass=min(n_pass_m3, n_pass_m0),
        per_system=tuple(per_system),
        note=(
            f"harness-identity verification, not a sensitivity control (v2.1 V2-CRIT-3): "
            f"M3 pass {n_pass_m3}/{n_eligible}, M0 pass {n_pass_m0}/{n_eligible} (M0 also matches "
            f"this rewrite, so the non-short-circuited subset is empty); gates on both reproducing "
            f"170/170, not on M3 sensitivity"
        ),
    )


def pc2b_affine_decomposition(validation_rows: Sequence[dict[str, Any]]) -> ControlBatteryResult:
    """PC2b: ``a * A^n * inv(K + A^n) -> a - a*K*inv(K + A^n)`` (v2.1 §7.7,
    reclassified ``m3_affine_decomposition_limitation``, non-gating).

    **Standing rule R4** (``research_state.md`` §8b, added after the C0001
    PC2b discrepancy): a control's reduction level must match its endpoint's
    reduction level, and any rewrite shared by a control and a reported
    endpoint must be identity-verified per instance. This function was
    previously scored at **system** level via ``result.m3_system`` while its
    denominator (``any_rewrite``) was assembled from per-**component**
    firing decisions -- components where the rewrite was a no-op were
    appended unchanged and matched themselves trivially, inflating the
    apparent pass rate to 110/170 against a component-level question that
    was never actually asked. Fixed here: scored **per component**, over
    only the components where the rewrite fired **and** is verified a true
    algebraic identity (:func:`gpu_runclaude1.tree_rewrite.verify_function_preserving`,
    which uses an exact-rational ``nsimplify`` fallback so quantization noise
    from the 4-significant-digit round-trip cannot manufacture a false
    verification either way). Frozen expected value: 0 matches on every
    eligible instance (v2.1); measured on the real corpus: eligible 60,
    matched 0 (`GPU_RUNclaude1/analyses/C0001_pc2b_discrepancy_resolution.md`).
    """
    per_system = []
    n_pass = 0
    n_eligible = 0
    n_ineligible_unverified = 0
    for row in validation_rows:
        components = row["teacher_components_infix"]
        component_reports = []
        for c in components:
            new_c, fired = rewrite_b_r1_affine_infix(c)
            if not fired:
                component_reports.append({"eligible": False, "reason": "rewrite_did_not_fire"})
                continue
            verification = tree_rewrite.verify_function_preserving(c, new_c)
            if not verification["verified"]:
                n_ineligible_unverified += 1
                component_reports.append(
                    {"eligible": False, "reason": "ineligible_rewrite_unverified", "verification_method": verification["method"]}
                )
                continue
            n_eligible += 1
            result = score_pair(c, new_c)
            passed = result.m3_system == 1.0
            n_pass += int(passed)
            component_reports.append({"eligible": True, "verification_method": verification["method"], "m3": result.m3_system, "pass": passed})
        per_system.append({"system_id": row["system_id"], "components": component_reports})
    return ControlBatteryResult(
        control="PC2b",
        n_eligible=n_eligible,
        n_pass=n_pass,
        per_system=tuple(per_system),
        note=(
            f"m3_affine_decomposition_limitation, non-gating, descriptive (v2.1 reclassification). "
            f"Component-level (standing rule R4): {n_eligible} eligible (rewrite fired and verified "
            f"identity-preserving; {n_ineligible_unverified} fired-but-unverified excluded), {n_pass} matched. "
            f"Frozen expected value: 0 matches on every eligible instance. A non-zero value is a "
            f"harness-difference DEVIATION, not a finding about E0."
        ),
    )


def _pc2_commutation(validation_rows: Sequence[dict[str, Any]], *, swap_add: bool, swap_mul: bool, label: str) -> ControlBatteryResult:
    """Tree-level commutation control, reported at **component** resolution
    (v2.1's frozen convention: eligible 170/170, M3 170/170 on the real
    corpus, using the tree-level permutation below -- never a string proxy,
    which the coordinator's review found scores a spurious 40/170).
    """
    from gpu_runclaude1.tree_rewrite import verify_function_preserving

    per_system = []
    n_eligible = 0
    n_pass = 0
    n_short_circuited = 0
    for row in validation_rows:
        components = row["teacher_components_infix"]
        swapped_components = [
            tree_rewrite.commute_infix(c, swap_add=swap_add, swap_mul=swap_mul) for c in components
        ]
        result = score_pair(_join(components), _join(swapped_components))
        component_reports = []
        for original, swapped, cm in zip(components, swapped_components, result.components):
            if original == swapped:
                component_reports.append({"eligible": False, "reason": "textually_unchanged"})
                continue
            verification = verify_function_preserving(original, swapped)
            if not verification["verified"]:
                component_reports.append(
                    {"eligible": False, "reason": "ineligible_rewrite_unverified", "verification_method": verification["method"]}
                )
                continue
            n_eligible += 1
            passed = cm.m3 == 1.0
            n_pass += int(passed)
            short_circuited = cm.m1 == 1.0
            n_short_circuited += int(short_circuited)
            component_reports.append(
                {
                    "eligible": True,
                    "m1": cm.m1,
                    "m3": cm.m3,
                    "short_circuited_by_canonical_exact": short_circuited,
                    "pass": passed,
                }
            )
        per_system.append({"system_id": row["system_id"], "components": component_reports})
    return ControlBatteryResult(
        control=label,
        n_eligible=n_eligible,
        n_pass=n_pass,
        per_system=tuple(per_system),
        note=(
            f"{n_short_circuited}/{n_eligible} short_circuited by canonical_exact "
            "(canonicalize_tree already sorts commutative operands, so M1 alone recovers "
            "equivalence; the non-short-circuited subset size is the honest denominator "
            "for what this control tests about M3 specifically, per the AUDIT-CRIT-4 check). "
            "Reported at component resolution, tree-level verified permutation."
        ),
    )


def pc2c_add_commutation(validation_rows: Sequence[dict[str, Any]]) -> ControlBatteryResult:
    return _pc2_commutation(validation_rows, swap_add=True, swap_mul=False, label="PC2c")


def pc2d_mul_commutation(validation_rows: Sequence[dict[str, Any]]) -> ControlBatteryResult:
    return _pc2_commutation(validation_rows, swap_add=False, swap_mul=True, label="PC2d")


def pc3a_wrong_exponent(validation_rows: Sequence[dict[str, Any]]) -> ControlBatteryResult:
    """PC3a (negative control): alter one realized Hill exponent. Verification
    of Q2 (already known: 48/48 of the eligible set). The eligible set is
    enumerated, not assumed 80, and every alteration is verified
    function-changing (v2.1 §7.7.0 rule 2 / standing rule R4) via
    :func:`gpu_runclaude1.tree_rewrite.verify_function_changing` before being
    counted eligible -- an alteration numerically indistinguishable from the
    original (a no-op) would otherwise inflate the specificity denominator
    with an instance that tests nothing.
    """
    per_system = []
    n_eligible = 0
    n_ineligible_noop = 0
    n_pass = 0
    for row in validation_rows:
        components = row["teacher_components_infix"]
        altered = list(components)
        changed_index = None
        for index, c in enumerate(components):
            new_c = tree_rewrite.alter_one_hill_exponent_infix(c)
            if new_c is None:
                continue
            changing = tree_rewrite.verify_function_changing(c, new_c)
            if not changing["changed"]:
                n_ineligible_noop += 1
                continue
            altered[index] = new_c
            changed_index = index
            break
        eligible = changed_index is not None
        n_eligible += int(eligible)
        if not eligible:
            per_system.append({"system_id": row["system_id"], "eligible": False})
            continue
        result = score_pair(_join(components), _join(altered))
        passed = result.m3_system == 0.0  # specificity: expect NON-match
        n_pass += int(passed)
        per_system.append(
            {"system_id": row["system_id"], "eligible": True, "changed_component": changed_index, "m3_system": result.m3_system, "pass": passed}
        )
    return ControlBatteryResult(
        control="PC3a",
        n_eligible=n_eligible,
        n_pass=n_pass,
        per_system=tuple(per_system),
        note=f"{n_ineligible_noop} ineligible_alteration_is_noop excluded (v2.1 §7.7.0 rule 2)",
    )


def _is_noop_variable_swap(component_infix: str, var_a: str, var_b: str) -> bool:
    """True iff swapping ``var_a``/``var_b`` in this component leaves the
    parsed, canonicalized tree unchanged -- e.g. the pair occurs only inside
    a commutative product like ``x_0 * x_1``, where the swap changes no
    function at all. v2's PC3a already carries an eligibility filter for
    exactly this shape of problem (its "eligible set", AUDIT-MIN-9); PC3b did
    not, and measured 50/60 with all 10 misses in family R08 at component
    index 2, whose text is ``... * x_0 * x_1 * 1/(... + x_0 * x_1) ...`` --
    every failure is this no-op case, confirmed by direct inspection, not a
    genuine specificity gap in M3. This filter is the corresponding
    amendment for PC3b (reported to the supervisor for the v2.1 amendment).
    """
    original_tree = parse_infix_component(component_infix)
    swapped_tree = parse_infix_component(tree_rewrite.swap_variables_infix(component_infix, var_a, var_b))
    return original_tree is not None and original_tree == swapped_tree


def pc3b_permuted_variable(validation_rows: Sequence[dict[str, Any]]) -> ControlBatteryResult:
    """PC3b (negative control): two variable indices swapped in one
    component, dimension >= 2 only (v2 §7.7), with the eligibility filter
    excluding a swap that is a no-op under commutativity (see
    :func:`_is_noop_variable_swap`; the corresponding amendment already
    exists for PC3a, v2 AUDIT-MIN-9).
    """
    per_system = []
    n_eligible = 0
    n_pass = 0
    for row in validation_rows:
        if int(row["dimension"]) < 2:
            continue
        components = row["teacher_components_infix"]
        variables = sorted({token for c in components for token in __import__("re").findall(r"x_\d+", c)})
        if len(variables) < 2:
            per_system.append({"system_id": row["system_id"], "eligible": False})
            continue
        var_a, var_b = variables[0], variables[1]
        candidate_indices = [i for i, c in enumerate(components) if var_a in c and var_b in c]
        candidate_indices += [i for i, c in enumerate(components) if var_a in c and i not in candidate_indices]
        changed_index = None
        swapped = list(components)
        for index in candidate_indices:
            if _is_noop_variable_swap(components[index], var_a, var_b):
                continue
            swapped[index] = tree_rewrite.swap_variables_infix(components[index], var_a, var_b)
            changed_index = index
            break
        eligible = changed_index is not None
        n_eligible += int(eligible)
        if not eligible:
            per_system.append({"system_id": row["system_id"], "eligible": False, "reason": "no_non_noop_swap_available"})
            continue
        result = score_pair(_join(components), _join(swapped))
        passed = result.m3_system == 0.0  # specificity: expect NON-match
        n_pass += int(passed)
        per_system.append(
            {"system_id": row["system_id"], "eligible": True, "changed_component": changed_index, "m3_system": result.m3_system, "pass": passed}
        )
    return ControlBatteryResult(control="PC3b", n_eligible=n_eligible, n_pass=n_pass, per_system=tuple(per_system))


PC4_MIN_TOTAL_GAIN = 40
PC4_MIN_H_GAIN = 20
PC4_MIN_FAMILIES_CONTRIBUTING = 3


def pc4_gain_positive_control(
    validation_rows: Sequence[dict[str, Any]],
    *,
    stratum_lookup: dict[tuple, str] | None = None,
) -> ControlBatteryResult:
    """PC4: the gain-indicator positive control (v2.1 §7.7, V2-CRIT-3).

    v2's own control battery cannot demonstrate that ``gain(s,i) = 1[m3=1
    AND m0=0]`` is capable of firing at all through the real code path: PC2a
    (the only sensitivity control that touches M3's distinctive
    constant-collapsing behavior) is *also* matched by M0 in every case
    (measured 170/170), because the CRIT-2 remedy made M0 itself a
    canonicalizing tree matcher, not a literal string matcher. Without a
    control that can produce a nonzero gain, an observed primary of K = 0 is
    indistinguishable from an instrument that cannot produce a gain under
    any circumstance -- the exact failure v2.1 §7.7.0 says the battery
    exists to exclude.

    Construction: rewrite each truth component with ``sympy.together()``
    (recombine a sum of terms over one common denominator) and score the
    *rewritten* form as a synthetic candidate against the *original* truth,
    through the same ``score_pair`` / ``gain_indicator`` code path the
    primary endpoint uses (v2.1 §7.10 item 3). Measured on the real GRN
    validation corpus: 100/170 components show ``m3 == 1 and m0 == 0``, all
    100 in stratum H, contributed by 6 of 8 families -- gain is
    demonstrably reachable through the exact scoring path Part A uses.

    Frozen gate (v2.1 §7.7.1): ``gain_pc4_total >= 40`` **and**
    ``gain_pc4_H >= 20`` **and** at least 3 distinct families each
    contributing >= 1 gain. Failure is a **HARD ABORT**: Part A is
    `undecidable (gain indicator not demonstrated)`, K may not be reported
    for or against E0, and Part C is not run (§7.7.3).
    """
    import sympy as sp

    from gpu_run4.formulas import _prepare_infix, _sympy_local_dict
    from gpu_runclaude1.endpoints import gain_indicator
    from gpu_runclaude1.strata import STRATUM_H
    from gpu_runclaude1.tree_rewrite import verify_function_preserving

    local = _sympy_local_dict()
    per_system = []
    n_components = 0
    n_eligible = 0
    n_ineligible_unverified = 0
    n_gain_total = 0
    n_gain_h = 0
    families_with_gain: set[str] = set()
    for row in validation_rows:
        components = row["teacher_components_infix"]
        system_id = row["system_id"]
        family = row.get("family", "")
        rewritten = []
        for c in components:
            expr = sp.sympify(_prepare_infix(c), locals=local)
            rewritten.append(str(sp.together(expr)))
        result = score_pair(_join(components), _join(rewritten))
        system_gains = []
        for index, (original, candidate, cm) in enumerate(zip(components, rewritten, result.components)):
            n_components += 1
            if original == candidate:
                # v2.1 §7.7.0 rule 1: a rewrite that is textually a no-op is
                # not an instance of this control at all.
                system_gains.append({"eligible": False, "reason": "textually_unchanged", "gain": False})
                continue
            verification = verify_function_preserving(original, candidate)
            if not verification["verified"]:
                n_ineligible_unverified += 1
                system_gains.append(
                    {"eligible": False, "reason": "ineligible_rewrite_unverified", "verification_method": verification["method"], "gain": False}
                )
                continue
            n_eligible += 1
            gain = bool(gain_indicator(int(cm.m0 == 1.0), int(cm.m3 == 1.0)))
            n_gain_total += int(gain)
            if gain:
                families_with_gain.add(family)
                if stratum_lookup is not None and stratum_lookup.get((system_id, cm.component_index)) == STRATUM_H:
                    n_gain_h += 1
            system_gains.append({"eligible": True, "verification_method": verification["method"], "gain": gain})
        per_system.append({"system_id": system_id, "family": family, "components": system_gains})
    gates_ok = (
        n_gain_total >= PC4_MIN_TOTAL_GAIN
        and (stratum_lookup is None or n_gain_h >= PC4_MIN_H_GAIN)
        and len(families_with_gain) >= PC4_MIN_FAMILIES_CONTRIBUTING
    )
    return ControlBatteryResult(
        control="PC4",
        n_eligible=n_eligible,
        n_pass=n_gain_total,
        per_system=tuple(per_system),
        note=(
            f"gain-indicator positive control (v2.1 V2-CRIT-3, HARD ABORT gate): "
            f"eligible {n_eligible}/{n_components} ({n_ineligible_unverified} ineligible_rewrite_unverified), "
            f"total gain {n_gain_total} (need >= {PC4_MIN_TOTAL_GAIN}), "
            f"H {n_gain_h if stratum_lookup is not None else 'n/a (no stratum_lookup supplied)'} "
            f"(need >= {PC4_MIN_H_GAIN}), {len(families_with_gain)} families contributing "
            f"(need >= {PC4_MIN_FAMILIES_CONTRIBUTING}); gates_ok={gates_ok}"
        ),
        extra={
            "n_components_total": n_components,
            "n_ineligible_unverified": n_ineligible_unverified,
            "gain_total": n_gain_total,
            "gain_h": n_gain_h if stratum_lookup is not None else None,
            "n_families_contributing": len(families_with_gain),
            "families_contributing": sorted(families_with_gain),
            "gates_ok": gates_ok,
        },
    )


def pc4b_second_gain_class(validation_rows: Sequence[dict[str, Any]]) -> ControlBatteryResult:
    """PC4b: a second, non-gating gain-diversification control (v2.1 §7.7).

    Rewrite ``a * X * inv(K + X)`` as ``a * inv(K * inv(X) + 1)`` (divide
    numerator and denominator by ``X``), bottom-up, one rewrite per
    component, each verified function-preserving before being counted
    eligible. Reported, not gated: a frozen, unverified *prediction* of
    gain > 0, diversifying PC4's single rewrite class rather than
    replacing it.
    """
    per_system = []
    n_components = 0
    n_eligible = 0
    n_ineligible_unverified = 0
    n_gain = 0
    for row in validation_rows:
        components = row["teacher_components_infix"]
        system_id = row["system_id"]
        rewritten = []
        fired = []
        for c in components:
            new_c, applied = tree_rewrite.rewrite_pc4b_infix(c)
            rewritten.append(new_c)
            fired.append(applied)
        result = score_pair(_join(components), _join(rewritten))
        component_reports = []
        for original, candidate, did_fire, cm in zip(components, rewritten, fired, result.components):
            n_components += 1
            if not did_fire:
                component_reports.append({"eligible": False, "reason": "pattern_did_not_match"})
                continue
            verification = tree_rewrite.verify_function_preserving(original, candidate)
            if not verification["verified"]:
                n_ineligible_unverified += 1
                component_reports.append({"eligible": False, "reason": "ineligible_rewrite_unverified"})
                continue
            n_eligible += 1
            gain = cm.m3 == 1.0 and cm.m0 == 0.0
            n_gain += int(gain)
            component_reports.append({"eligible": True, "gain": gain})
        per_system.append({"system_id": system_id, "components": component_reports})
    return ControlBatteryResult(
        control="PC4b",
        n_eligible=n_eligible,
        n_pass=n_gain,
        per_system=tuple(per_system),
        note=(
            f"second gain class, non-gating (v2.1 §7.7): eligible {n_eligible}/{n_components} "
            f"({n_ineligible_unverified} ineligible_rewrite_unverified), gain {n_gain}. "
            f"Reported as an unverified prediction of gain > 0, not gated."
        ),
    )


def run_all_controls(
    validation_rows: Sequence[dict[str, Any]],
    *,
    stratum_lookup: dict[tuple, str] | None = None,
) -> dict[str, ControlBatteryResult]:
    """Run the full battery. ``stratum_lookup`` (system_id, component_index)
    -> "H"|"L", from a :class:`gpu_runclaude1.strata.StrataFrozenToken`, is
    required for PC4's H-stratum gate component; without it PC4 still runs
    and reports its total gain, but cannot evaluate the H-specific gate.
    """
    return {
        "PC0": pc0_identity(validation_rows),
        "PC0_CAS": pc0_cas_self_equality(validation_rows),
        "PC1": pc1_identity_through_compare_formulas(validation_rows),
        "PC2a": pc2a_neg_asymmetry(validation_rows),
        "PC2b": pc2b_affine_decomposition(validation_rows),
        "PC2c": pc2c_add_commutation(validation_rows),
        "PC2d": pc2d_mul_commutation(validation_rows),
        "PC3a": pc3a_wrong_exponent(validation_rows),
        "PC3b": pc3b_permuted_variable(validation_rows),
        "PC4": pc4_gain_positive_control(validation_rows, stratum_lookup=stratum_lookup),
        "PC4b": pc4b_second_gain_class(validation_rows),
    }
