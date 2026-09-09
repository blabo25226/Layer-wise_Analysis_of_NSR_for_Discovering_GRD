"""Every non-match must carry an explicit failure_reason (v2 §7.5 item 1).

`proved_different` (a decided non-match) must always be distinguished from
`could_not_evaluate` (an unprovable comparison); no path in
gpu_runclaude1.matcher may return an unlabelled non-match.
"""

from __future__ import annotations

from gpu_runclaude1.matcher import (
    COULD_NOT_EVALUATE,
    MATCHED,
    PROVED_DIFFERENT,
    could_not_evaluate_rate,
    score_pair,
)


def test_matched_case_has_no_failure_reason():
    result = score_pair("x_0", "x_0")
    component = result.components[0]
    assert component.match_outcome_m3 == MATCHED
    assert component.m3 == 1.0
    assert component.failure_reason is None


def test_proved_different_is_labeled_and_distinct_from_could_not_evaluate():
    result = score_pair("x_0", "x_1")  # different variable: a genuine, decidable non-match
    component = result.components[0]
    assert component.match_outcome_m3 == PROVED_DIFFERENT
    assert component.m3 == 0.0
    # proved_different carries no failure_reason -- it is a decided outcome, not a failure.
    assert component.failure_reason is None


def test_unparseable_candidate_is_could_not_evaluate_with_a_reason():
    result = score_pair("x_0", "this is not an equation )))")
    component = result.components[0]
    assert component.match_outcome_m3 == COULD_NOT_EVALUATE
    assert component.failure_reason is not None
    assert component.failure_reason in {"SkeletonParseFailure", "ParseError", "SkeletonEvaluationFailure", "SymbolicEquivalenceTimeout"}


def test_component_count_mismatch_is_labeled():
    """v2.1 V2-MIN-9: a component-count mismatch is a *decided* non-match
    (an observed fact, not a failed evaluation) -- classified
    proved_different, not could_not_evaluate, and therefore excluded from
    the could_not_evaluate_rate numerator, while still carrying an explicit
    failure_reason so it is never confused with an ordinary decided
    difference.
    """
    result = score_pair("x_0 | x_1", "x_0")  # 2 truth components, 1 candidate component
    assert result.component_count_match is False
    for component in result.components:
        assert component.match_outcome_m3 == PROVED_DIFFERENT
        assert component.failure_reason == "ComponentCountMismatch"
    assert could_not_evaluate_rate(result.components) == 0.0


def test_no_bare_except_surfaces_an_unlabelled_non_match_over_a_battery_of_inputs():
    """A representative battery of pathological inputs: every one must
    resolve to MATCHED, PROVED_DIFFERENT (with no reason), or
    COULD_NOT_EVALUATE (always with a reason) -- there is no fourth,
    unlabelled outcome representable by ComponentMatch.
    """
    pairs = [
        ("x_0", "x_0"),
        ("x_0", "x_1"),
        ("", "x_0"),
        ("x_0", ""),
        ("x_0 / 0", "x_0"),
        ("((((", "x_0"),
        ("x_0 ** x_1 ** x_0", "x_0"),
        ("1/(1/(1/(1/(1/(x_0)))))", "x_0"),
    ]
    for true_text, candidate_text in pairs:
        result = score_pair(true_text, candidate_text)
        for component in result.components:
            assert component.match_outcome_m3 in {MATCHED, PROVED_DIFFERENT, COULD_NOT_EVALUATE}
            if component.match_outcome_m3 == COULD_NOT_EVALUATE:
                assert component.failure_reason, f"could_not_evaluate with no reason for pair {true_text!r} vs {candidate_text!r}"
            if component.match_outcome_m3 == PROVED_DIFFERENT:
                # A decided non-match carries no failure_reason, UNLESS it is
                # specifically a component-count mismatch (v2.1 V2-MIN-9),
                # which is a decided non-match that still records why.
                assert component.failure_reason in (None, "ComponentCountMismatch")


def test_could_not_evaluate_rate_over_a_mixed_battery():
    pairs = [("x_0", "x_0"), ("x_0", "x_1"), ("x_0", "not an equation )))")]
    results = [score_pair(t, c) for t, c in pairs]
    components = [c for r in results for c in r.components]
    rate = could_not_evaluate_rate(components)
    assert 0.0 < rate < 1.0  # exactly one of three triples is could_not_evaluate
