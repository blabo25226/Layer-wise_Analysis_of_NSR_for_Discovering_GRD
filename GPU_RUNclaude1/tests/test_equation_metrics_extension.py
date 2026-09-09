"""Verifies the additive equation_metrics.py refactor is behavior-preserving.

`skeleton_equivalence_with_reason` / `to_skeleton` were refactored (not
reimplemented) so the exact failure surfaces v2 §7.5 requires labeled
(SkeletonParseFailure, SymbolicEquivalenceTimeout, SkeletonEvaluationFailure)
carry an explicit reason. `symbolic_recovery`'s own "skeleton" value, and
`to_skeleton`'s return value for any input, must be byte-identical to before
the refactor. These tests assert that equivalence directly (never
reimplemented independently) over the real GRN corpus plus edge cases, per
the coordinator's explicit review request.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from evaluation.equation_metrics import skeleton_equivalence_with_reason, symbolic_recovery, to_skeleton

REPO_ROOT = Path(__file__).resolve().parents[2]
GPU_RUN5_SOURCE_RUN = REPO_ROOT / "results" / "runs" / "gpu_run5_20260823_ddd267b0"


@pytest.mark.parametrize(
    "true_expr,pred_expr",
    [
        ("x_0", "x_0"),
        ("x_0", "x_1"),
        ("2 * x_0", "3 * x_0"),
        ("", "x_0"),
        ("x_0", ""),
        ("x_0", "not an equation )))"),
        ("1/(1/(1/(1/(1/(x_0)))))", "x_0"),
    ],
)
def test_skeleton_equivalence_with_reason_matches_symbolic_recovery(true_expr, pred_expr):
    reference = symbolic_recovery(true_expr, pred_expr)["skeleton"]
    under_test, _reason = skeleton_equivalence_with_reason(true_expr, pred_expr)
    assert under_test == reference


@pytest.mark.skipif(not GPU_RUN5_SOURCE_RUN.is_dir(), reason="GPU_RUN5 source run not present in this environment")
def test_skeleton_equivalence_with_reason_matches_symbolic_recovery_over_real_corpus():
    """Deviation disclosure: gpu_runclaude1.matcher calls
    skeleton_equivalence_with_reason rather than symbolic_recovery(...)
    ["skeleton"] directly, so it can attach a failure reason. This proves
    they never disagree over all 170 real GRN validation components
    compared against themselves (the identity case) -- if they ever
    diverge, the v2-pinned symbolic_recovery(...)["skeleton"] is the
    function of record and gpu_runclaude1's variant is the defect.
    """
    rows = json.loads((GPU_RUN5_SOURCE_RUN / "phase2" / "validation.json").read_text(encoding="utf-8"))
    checked = 0
    for row in rows:
        for component in row["teacher_components_infix"]:
            reference = symbolic_recovery(component, component)["skeleton"]
            under_test, _reason = skeleton_equivalence_with_reason(component, component)
            assert under_test == reference
            checked += 1
    assert checked == 170


def test_to_skeleton_return_value_unchanged_for_parseable_and_unparseable_input():
    assert to_skeleton("x_0") is not None
    assert to_skeleton("this is not an equation )))") is None
    assert to_skeleton("") is None


def test_symbolic_recovery_eager_equiv_cost_is_disclosed_not_paid_by_the_primary_matcher():
    """Cost-model note (coordinator review): symbolic_recovery's returned
    dict eagerly computes the "equiv" field (and, when skeleton matches,
    _approximately_equivalent) for every call -- this is a real SymPy cost
    PC0 pays (v2 §7.7 pins PC0 to call symbolic_recovery(...) directly), but
    gpu_runclaude1.matcher's primary scoring path uses
    skeleton_equivalence_with_reason, which computes only the skeleton
    branch and never reaches the equiv computation. This test pins that
    architectural fact so a future edit cannot silently make the primary
    path pay PC0's extra cost.
    """
    import ast
    import inspect

    from gpu_runclaude1 import matcher as matcher_module

    source = inspect.getsource(matcher_module)
    tree = ast.parse(source)
    imported_names = {
        alias.asname or alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        for alias in node.names
    }
    assert "symbolic_recovery" not in imported_names
    assert "skeleton_equivalence_with_reason" in imported_names
