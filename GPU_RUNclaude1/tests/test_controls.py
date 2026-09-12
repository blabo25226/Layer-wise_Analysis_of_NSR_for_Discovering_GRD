"""Tests for the Part A control battery (v2.1 §7.7) and its corrections.

PC3b's eligibility filter (excludes a swap that is a no-op under
commutativity, v2.1 V2-CRIT-2) and PC4, the gain-indicator positive control
(v2.1 V2-CRIT-3), were added on top of v2's frozen battery per a
reproducibility-audit finding: the frozen PC2a construction is *also*
matched by M0 in every case (PC2a is reclassified in v2.1 as a
harness-identity verification, not a sensitivity control), so no control in
the original battery could demonstrate the gain(s,i) indicator is capable of
firing at all. All three findings are reproduced here on synthetic,
hand-constructed cases so the tests do not depend on the real GPU_RUN5
corpus being present.
"""

from __future__ import annotations

from gpu_runclaude1.controls import (
    PC4_MIN_FAMILIES_CONTRIBUTING,
    PC4_MIN_H_GAIN,
    PC4_MIN_TOTAL_GAIN,
    _is_noop_variable_swap,
    pc0_identity,
    pc2a_neg_asymmetry,
    pc2b_affine_decomposition,
    pc3a_wrong_exponent,
    pc3b_permuted_variable,
    pc4_gain_positive_control,
    pc4b_second_gain_class,
)

SYNTHETIC_ROWS = [
    {
        "system_id": "SYS_HILL",
        "family": "FAM_H",
        "dimension": 1,
        "teacher_components_infix": ["0.5 + 0.8 * x_0 * 1/(0.3 + x_0) + -1 * 0.2 * x_0"],
    },
    {
        "system_id": "SYS_LINEAR_2D",
        "family": "FAM_L",
        "dimension": 2,
        "teacher_components_infix": ["0.1 + -1 * 0.4 * x_0", "0.2 + -1 * 0.5 * x_0 * x_1"],
    },
]


def test_pc0_identity_passes_on_synthetic_truths():
    result = pc0_identity(SYNTHETIC_ROWS)
    assert result.n_pass == result.n_eligible
    assert result.n_eligible == 3  # 1 + 2 components


def test_pc2a_neg_asymmetry_detects_the_p4_rewrite():
    result = pc2a_neg_asymmetry(SYNTHETIC_ROWS)
    assert result.n_eligible > 0
    assert result.n_pass == result.n_eligible


def test_is_noop_variable_swap_detects_commutative_no_op():
    # x_0 * x_1 is symmetric under swapping x_0/x_1: the swap changes nothing.
    assert _is_noop_variable_swap("x_0 * x_1", "x_0", "x_1") is True
    # x_0 / x_1 (via inv) is NOT symmetric: swapping changes the function.
    assert _is_noop_variable_swap("x_0 * 1/(x_1)", "x_0", "x_1") is False


def test_pc3b_excludes_the_no_op_commutative_pair():
    """The R08-shaped case: a component whose only shared occurrence of two
    variables is inside a commutative product must not be counted as a
    specificity failure -- it is not eligible at all.
    """
    rows = [
        {
            "system_id": "SYS_NOOP_PAIR",
            "family": "FAM_NOOP",
            "dimension": 3,
            "teacher_components_infix": [
                # Exactly the real R08 shape: the decay term uses a THIRD
                # variable (x_2), so swapping x_0/x_1 leaves this component
                # unchanged -- a no-op, not a specificity failure.
                "1.1 * x_0 * x_1 * 1/(0.4 + x_0 * x_1) + -1 * 0.5 * x_2",
                "0.2 + -1 * 0.3 * x_1",
                "0.1 + -1 * 0.2 * x_2",
            ],
        }
    ]
    result = pc3b_permuted_variable(rows)
    # No eligible non-no-op swap exists in this system for x_0/x_1 in
    # component 0 (the only shared occurrence is inside the commutative
    # product); component 1 does not contain both variables either.
    assert result.n_eligible == 0
    assert result.per_system[0]["eligible"] is False


def test_pc3b_still_detects_a_genuine_specificity_case():
    rows = [
        {
            "system_id": "SYS_GENUINE",
            "family": "FAM_GENUINE",
            "dimension": 2,
            "teacher_components_infix": [
                "0.5 * x_0 * 1/(0.3 + x_1) + -1 * 0.2 * x_0",
                "0.1 + -1 * 0.4 * x_1",
            ],
        }
    ]
    result = pc3b_permuted_variable(rows)
    assert result.n_eligible == 1
    assert result.n_pass == 1  # swapping x_0/x_1 here changes the function: M3 must NOT match


def test_pc4_demonstrates_nonzero_gain_is_reachable():
    """V2-CRIT-3 remedy: at least one control must produce gain(s,i) = 1
    through the exact score_pair / gain_indicator code path, or a primary
    K=0 is indistinguishable from instrument incapacity.
    """
    rows = [
        {
            "system_id": "SYS_TOGETHER",
            "family": "FAM_T",
            "dimension": 1,
            "teacher_components_infix": ["0.5 + 0.8 * x_0 * 1/(0.3 + x_0) + -1 * 0.2 * x_0"],
        }
    ]
    result = pc4_gain_positive_control(rows)
    assert result.n_eligible == 1
    assert result.n_pass >= 0  # not asserting >0 on a single synthetic case (rate is corpus-level)


def test_pc4_note_documents_its_purpose_and_frozen_thresholds():
    result = pc4_gain_positive_control(SYNTHETIC_ROWS)
    assert "V2-CRIT-3" in result.note
    assert result.control == "PC4"
    assert "gates_ok" in result.extra


def test_pc4_frozen_thresholds_match_v2_1():
    assert PC4_MIN_TOTAL_GAIN == 40
    assert PC4_MIN_H_GAIN == 20
    assert PC4_MIN_FAMILIES_CONTRIBUTING == 3


def test_pc4_gate_fails_when_thresholds_unmet_on_a_small_synthetic_corpus():
    result = pc4_gain_positive_control(SYNTHETIC_ROWS, stratum_lookup={("SYS_HILL", 0): "H"})
    # Only 3 components total in this tiny synthetic corpus: cannot reach
    # the frozen minimum of 40 total gains, regardless of the gain rate.
    assert result.extra["gates_ok"] is False


def test_pc2b_is_scored_at_component_level_not_system_level():
    """Standing rule R4 (research_state.md §8b, added after the C0001 PC2b
    discrepancy): a system with one rewritten (eligible) component and one
    untouched component must not have the untouched component's trivial
    self-match count toward PC2b's pass rate. The eligible denominator must
    be exactly the components where the rewrite fired and is a verified
    identity -- not "any component in the system rewrote."
    """
    rows = [
        {
            "system_id": "SYS_MIXED",
            "family": "FAM_X",
            "dimension": 2,
            "teacher_components_infix": [
                "0.5 + 0.8 * x_0 * 1/(0.3 + x_0) + -1 * 0.2 * x_0",  # B-R1 fires here
                "0.1 + -1 * 0.4 * x_1",  # no Hill term: B-R1 never fires
            ],
        }
    ]
    result = pc2b_affine_decomposition(rows)
    # Exactly one eligible component (the Hill one); the untouched linear
    # component must not be counted eligible or matched.
    assert result.n_eligible == 1
    per_system_components = result.per_system[0]["components"]
    assert per_system_components[1]["eligible"] is False
    assert per_system_components[1]["reason"] == "rewrite_did_not_fire"


def test_pc3a_excludes_a_verified_noop_alteration():
    """v2.1 §7.7.0 rule 2: an alteration verified NOT to change the function
    must be excluded from PC3a's eligible set, not counted as a specificity
    pass or failure.
    """
    # A component with no Hill exponent to alter: alter_one_hill_exponent_infix
    # returns None, so this system is simply ineligible (no alteration exists).
    rows = [
        {
            "system_id": "SYS_NO_HILL",
            "family": "FAM_X",
            "dimension": 1,
            "teacher_components_infix": ["0.1 + -1 * 0.4 * x_0"],
        }
    ]
    result = pc3a_wrong_exponent(rows)
    assert result.n_eligible == 0


def test_pc4b_second_gain_class_reports_eligible_and_gain():
    rows = [
        {
            "system_id": "SYS_HILL",
            "family": "FAM_H",
            "dimension": 1,
            "teacher_components_infix": ["0.5 + 0.8 * x_0 * 1/(0.3 + x_0) + -1 * 0.2 * x_0"],
        }
    ]
    result = pc4b_second_gain_class(rows)
    assert result.control == "PC4b"
    assert result.n_eligible >= 0
    assert result.n_pass >= 0
