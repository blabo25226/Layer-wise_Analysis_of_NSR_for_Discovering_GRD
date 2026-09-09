"""Tests for gpu_runclaude1.partb: U_mult/U_affine/U_min and the B-R1..B-R4
rewrite set (v2 §8.1), against the frozen worked example and synthetic cases.
"""

from __future__ import annotations

from gpu_run4.formulas import numeric_equivalent, parse_infix_component
from gpu_runclaude1.partb import (
    affine_rewrite_component,
    analyze_component,
    count_non_identity_unary,
    realized_hill_exponents,
    uses_only_in_support_operators,
)
from gpu_runclaude1.tree_rewrite import raw_prefix_tree


def test_realized_hill_exponents_reports_each_chain_once():
    # Hill-4, single occurrence: nested pow2,pow2 over a variable.
    tree = raw_prefix_tree("pow2,pow2,x_0")
    assert realized_hill_exponents(tree) == [4]

    # Hill-2, single pow2 over a variable.
    tree2 = raw_prefix_tree("pow2,x_0")
    assert realized_hill_exponents(tree2) == [2]

    # No wrapping at all: nothing realized.
    tree3 = raw_prefix_tree("x_0")
    assert realized_hill_exponents(tree3) == []


def test_u_mult_counts_raw_generator_tokens_not_canonicalized_pow():
    # "add,mul,mul,CONST,pow2,pow2,x_0,inv,add,CONST,pow2,pow2,x_0" style
    # component: two pow2,pow2 occurrences (numerator + denominator) + one inv
    # = 5 non-identity unary nodes, matching v2's own worked example (§8.1).
    prefix = "add,mul,mul,0.8,pow2,pow2,x_0,inv,add,0.5,pow2,pow2,x_0,mul,-1,mul,0.2,x_0"
    tree = raw_prefix_tree(prefix)
    assert count_non_identity_unary(tree) == 5


def test_worked_example_hill4_single_term_rescued_by_b_r1_to_three():
    """v2 §8.1's own worked example: 'multiplicative Hill-4 single-term
    (U_mult = 5, rescued by B-R1 to 3)'.
    """
    row = {
        "system_id": "WORKED_EXAMPLE",
        "teacher_components_prefix": ["add,mul,mul,0.8,pow2,pow2,x_0,inv,add,0.5,pow2,pow2,x_0,mul,-1,mul,0.2,x_0"],
        "teacher_components_infix": ["0.1 + 0.8 * ((x_0)**2)**2 * 1/(0.5 + ((x_0)**2)**2) + -1 * 0.2 * x_0"],
    }
    record = analyze_component(row["system_id"], 0, row["teacher_components_prefix"][0], row["teacher_components_infix"][0])
    assert record.u_mult == 5
    assert record.affine_available
    assert record.u_affine == 3
    assert record.u_min == 3
    assert record.in_support is True  # 3 <= max_unary_ops_per_dim


def test_b_r1_rewrite_is_numerically_equivalent_to_the_original():
    component = "0.1954 + 0.8878 * x_0 * 1/(0.8392 + x_0) + -1 * 0.3968 * x_0"
    original_tree = parse_infix_component(component)
    rewritten_tree, attempts = affine_rewrite_component(component)
    assert attempts, "expected at least one accepted B-R1/B-R4 rewrite"
    assert all(a.accepted for a in attempts)
    check = numeric_equivalent([original_tree], [rewritten_tree])
    assert check["equivalent"] is True


def test_multi_term_component_is_not_rescued_below_budget():
    """v2 §8.1: 'B-R1 does not rescue multi-term components': a product of
    two independent Hill terms needs >= 6 unary applications even after the
    rewrite (constructed here from two independent Hill-4 terms).
    """
    prefix = (
        "add,"
        "mul,mul,0.5,pow2,pow2,x_0,inv,add,0.3,pow2,pow2,x_0,"
        "mul,mul,0.5,pow2,pow2,x_1,inv,add,0.3,pow2,pow2,x_1"
    )
    infix = "0.5 * ((x_0)**2)**2 * 1/(0.3 + ((x_0)**2)**2) + 0.5 * ((x_1)**2)**2 * 1/(0.3 + ((x_1)**2)**2)"
    record = analyze_component("MULTI_TERM", 0, prefix, infix)
    assert record.u_mult >= 10  # two independent Hill-4 terms
    assert record.u_min > 3
    assert record.in_support is False


def test_uses_only_in_support_operators_flags_a_forbidden_operator():
    in_support_tree = raw_prefix_tree("add,x_0,inv,x_0")
    assert uses_only_in_support_operators(in_support_tree) is True
    out_of_vocab_tree = raw_prefix_tree("tan,x_0")  # not in operators_to_use
    assert uses_only_in_support_operators(out_of_vocab_tree) is False
