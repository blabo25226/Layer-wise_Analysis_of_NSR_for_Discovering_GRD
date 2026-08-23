from evaluation.gpu_run5_selection import formula_selection_key


def test_formula_selection_key_penalizes_failure_and_is_macro_by_system():
    good = [
        {"system_id": "a", "seed": 1, "valid": True, "exponent_aware_skeleton_exact": 1, "normalized_variable_aware_ted": 0},
        {"system_id": "b", "seed": 1, "valid": True, "exponent_aware_skeleton_exact": 0, "normalized_variable_aware_ted": 0.2},
    ]
    failed = [dict(good[0]), {"system_id": "b", "seed": 1, "valid": False}]
    assert formula_selection_key(good, 2.0) < formula_selection_key(failed, 1.0)


def test_ce_is_only_final_tie_breaker():
    rows = [{"system_id": "a", "seed": 1, "valid": True, "exponent_aware_skeleton_exact": 0, "normalized_variable_aware_ted": 0.5}]
    assert formula_selection_key(rows, 1.0) < formula_selection_key(rows, 2.0)
