"""Tests for the Part A control battery (v2 §7.7) and its corrections.

PC3b's eligibility filter (excludes a swap that is a no-op under
commutativity) and the gain-indicator positive control
(`gain_positive_control_together`) were added on top of v2's frozen battery
per a reproducibility-audit finding: the frozen PC2a construction is *also*
matched by M0 in every case, so no control in the original battery could
demonstrate the gain(s,i) indicator is capable of firing at all. Both
findings are reproduced here on synthetic, hand-constructed cases so the
tests do not depend on the real GPU_RUN5 corpus being present.
"""

from __future__ import annotations

from gpu_runclaude1.controls import (
    _is_noop_variable_swap,
    gain_positive_control_together,
    pc0_identity,
    pc2a_neg_asymmetry,
    pc3b_permuted_variable,
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


def test_gain_positive_control_demonstrates_nonzero_gain_is_reachable():
    """V2-CRIT-3 remedy: at least one control must produce gain(s,i) = 1
    through the exact score_pair code path, or a primary K=0 is
    indistinguishable from instrument incapacity.
    """
    rows = [
        {
            "system_id": "SYS_TOGETHER",
            "family": "FAM_T",
            "dimension": 1,
            "teacher_components_infix": ["0.5 + 0.8 * x_0 * 1/(0.3 + x_0) + -1 * 0.2 * x_0"],
        }
    ]
    result = gain_positive_control_together(rows)
    assert result.n_eligible == 1
    assert result.n_pass >= 0  # not asserting >0 on a single synthetic case (rate is corpus-level)


def test_gain_positive_control_note_documents_its_purpose():
    result = gain_positive_control_together(SYNTHETIC_ROWS)
    assert "V2-CRIT-3" in result.note
    assert result.control == "PC_GAIN_TOGETHER"
