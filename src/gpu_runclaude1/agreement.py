"""Gate 0 item 11 (v2.1 §7.4 V2-MAJ-2): the M3-implementation agreement test.

Two guarantees, both required before ``skeleton_equivalence_with_reason``
(the implementation ``gpu_runclaude1.matcher.score_pair`` actually calls) may
stand in for ``symbolic_recovery(...)["skeleton"]`` (the pinned definition of
record):

(a) :func:`run_agreement_test` -- a synthetic agreement test over a fixed,
    seeded pair corpus drawn from the control battery's own constructions
    (:func:`collect_agreement_pairs`), with a frozen maximum disagreement
    rate of 0% and a hard-abort recommendation above it.
(b) :func:`census_indices` / :func:`run_in_pass_census` -- an in-pass 1-in-100
    double-computation census over the real endpoint pass.

**Scope note, disclosed (not silent).** v2.1 names a corpus of exactly 910
pairs (PC0 170 + PC2a 170 + PC2b's eligible instances + PC2c 170 + PC2d 170 +
PC3a 48 + PC3b 60 + PC4 170 + PC4b's eligible instances). This module
collects pairs from the same nine construction rules used by the real
control battery, deduplicated, and reports the **realized** n rather than
assuming 910 -- the realized size depends on how many rewrites fire and are
eligible on whatever corpus is passed in (the full 80-system/170-component
validation corpus is expected to realize close to 910; a smaller frame
realizes correspondingly fewer, and this is reported explicitly, never
silently presented as the frozen size).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence

from evaluation.equation_metrics import skeleton_equivalence_with_reason, symbolic_recovery
from gpu_runclaude1 import tree_rewrite
from gpu_runclaude1.partb import rewrite_b_r1_affine_infix


def collect_agreement_pairs(validation_rows: Sequence[dict[str, Any]]) -> list[tuple[str, str, str]]:
    """Collect (true_infix, candidate_infix, source_control) triples from the
    same nine construction rules the real control battery uses, deduplicated
    by the (true, candidate) pair. Contains **no candidate data** (only
    truth-side rewrites/alterations), so it can be run before the strata are
    frozen without violating v2.1 §7.2.
    """
    import sympy as sp

    from gpu_run4.formulas import _prepare_infix, _sympy_local_dict, parse_infix_component

    local = _sympy_local_dict()
    seen: set[tuple[str, str]] = set()
    pairs: list[tuple[str, str, str]] = []

    def _add(true_text: str, cand_text: str, source: str) -> None:
        if source != "PC0" and true_text == cand_text:
            return  # a no-op rewrite is not an instance of a sensitivity/specificity control
        key = (true_text, cand_text)
        if key in seen:
            return
        seen.add(key)
        pairs.append((true_text, cand_text, source))

    for row in validation_rows:
        components = row["teacher_components_infix"]
        for c in components:
            # PC0: identity.
            _add(c, c, "PC0")
            # PC2a: neg-asymmetry rewrite.
            rewritten, count = tree_rewrite.rewrite_neg_one_decay(c)
            if count > 0:
                _add(c, rewritten, "PC2a")
            # PC2b: affine decomposition (eligible = fired and verified, per the F1 fix).
            affine, fired = rewrite_b_r1_affine_infix(c)
            if fired and tree_rewrite.verify_function_preserving(c, affine)["verified"]:
                _add(c, affine, "PC2b")
            # PC2c / PC2d: tree-level commutation.
            add_commuted = tree_rewrite.commute_infix(c, swap_add=True, swap_mul=False)
            if add_commuted != c and tree_rewrite.verify_function_preserving(c, add_commuted)["verified"]:
                _add(c, add_commuted, "PC2c")
            mul_commuted = tree_rewrite.commute_infix(c, swap_add=False, swap_mul=True)
            if mul_commuted != c and tree_rewrite.verify_function_preserving(c, mul_commuted)["verified"]:
                _add(c, mul_commuted, "PC2d")
            # PC3a: wrong exponent (negative control).
            altered = tree_rewrite.alter_one_hill_exponent_infix(c)
            if altered is not None:
                _add(c, altered, "PC3a")
            # PC4: sympy.together.
            expr = sp.sympify(_prepare_infix(c), locals=local)
            together = str(sp.together(expr))
            if together != c:
                _add(c, together, "PC4")
            # PC4b: second gain class.
            pc4b, applied = tree_rewrite.rewrite_pc4b_infix(c)
            if applied:
                _add(c, pc4b, "PC4b")
        # PC3b: variable swap (negative control), dimension >= 2 only.
        if int(row.get("dimension", 1)) >= 2:
            import re

            variables = sorted({token for c in components for token in re.findall(r"x_\d+", c)})
            if len(variables) >= 2:
                var_a, var_b = variables[0], variables[1]
                for c in components:
                    if var_a not in c:
                        continue
                    swapped = tree_rewrite.swap_variables_infix(c, var_a, var_b)
                    if swapped != c:
                        _add(c, swapped, "PC3b")

    return pairs


@dataclass(frozen=True)
class AgreementTestResult:
    n_pairs: int
    n_disagreements: int
    disagreement_rate: float
    disagreements: tuple
    by_source: dict
    ok: bool


def run_agreement_test(pairs: Sequence[tuple[str, str, str]], *, max_disagreement_rate: float = 0.0) -> AgreementTestResult:
    """Compare ``symbolic_recovery(...)["skeleton"]`` (the pinned definition
    of record) against ``skeleton_equivalence_with_reason(...)[0]`` (the
    implementation) over every pair. Frozen requirement: 100% agreement (a
    disagreement rate of 0%); this is a hard-abort Gate 0 condition, not a
    descriptive rate.
    """
    n_disagreements = 0
    disagreements = []
    by_source_total: dict[str, int] = {}
    by_source_disagree: dict[str, int] = {}
    for true_text, cand_text, source in pairs:
        by_source_total[source] = by_source_total.get(source, 0) + 1
        reference = symbolic_recovery(true_text, cand_text)["skeleton"]
        under_test, _reason = skeleton_equivalence_with_reason(true_text, cand_text)
        if reference != under_test:
            n_disagreements += 1
            by_source_disagree[source] = by_source_disagree.get(source, 0) + 1
            disagreements.append({"true": true_text, "candidate": cand_text, "source": source, "reference": reference, "under_test": under_test})
    n_pairs = len(pairs)
    rate = (n_disagreements / n_pairs) if n_pairs else 0.0
    return AgreementTestResult(
        n_pairs=n_pairs,
        n_disagreements=n_disagreements,
        disagreement_rate=rate,
        disagreements=tuple(disagreements),
        by_source={"total": by_source_total, "disagreements": by_source_disagree},
        ok=(rate <= max_disagreement_rate),
    )


# ---------------------------------------------------------------------------
# In-pass 1-in-100 double-computation census (v2.1 §7.4 item b, A2-S6c).
# ---------------------------------------------------------------------------
def census_should_check(global_triple_index: int, *, every: int = 100) -> bool:
    """Every ``every``-th (cell, candidate, component) triple, in the frozen
    deterministic enumeration order the caller assigns, is double-checked.
    """
    return global_triple_index % every == 0


def run_in_pass_census(triples: Sequence[tuple[int, str, str]], *, every: int = 100) -> dict:
    """``triples`` is ``(global_triple_index, true_infix, candidate_infix)``
    in the frozen deterministic order the endpoint pass actually visits them.
    Only the selected 1-in-``every`` triples are double-computed; this is
    "in-pass" in the sense that it consumes the exact same triples, in the
    exact same order, that the endpoint pass itself produced, immediately
    following their computation in the same phase invocation -- not a
    separately re-run offline analysis over stored output.
    """
    checked = 0
    disagreements = []
    for global_index, true_text, cand_text in triples:
        if not census_should_check(global_index, every=every):
            continue
        checked += 1
        reference = symbolic_recovery(true_text, cand_text)["skeleton"]
        under_test, _reason = skeleton_equivalence_with_reason(true_text, cand_text)
        if reference != under_test:
            disagreements.append({"global_triple_index": global_index, "true": true_text, "candidate": cand_text})
    agreement_rate = 1.0 - (len(disagreements) / checked if checked else 0.0)
    return {
        "n_checked": checked,
        "n_disagreements": len(disagreements),
        "m3_implementation_agreement": agreement_rate,
        "disagreements": disagreements,
        "ok": agreement_rate == 1.0,
    }
