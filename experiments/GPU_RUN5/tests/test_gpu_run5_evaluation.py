from __future__ import annotations

import numpy as np

from gpu_run5.evaluation import formula_metrics, formula_selection_key, select_candidate, trajectory_nrmse


def test_trajectory_nrmse_penalizes_invalid_prediction() -> None:
    truth = np.asarray([[0.0], [1.0], [2.0]])
    assert trajectory_nrmse(truth, None, penalty=10.0) == 10.0
    assert trajectory_nrmse(truth, np.asarray([[0.0], [1.0], [2.0]]), penalty=10.0) == 0.0
    finite_but_bad = trajectory_nrmse(truth, np.asarray([[1e9], [1e9], [1e9]]), penalty=10.0)
    assert finite_but_bad < 10.0


def test_formula_metrics_preserve_component_exponent() -> None:
    same = formula_metrics("2*x_0**2 | 3*x_1", "4*x_0**2 | 5*x_1")
    wrong = formula_metrics("2*x_0**2 | 3*x_1", "4*x_0**4 | 5*x_1")
    assert same["component_exponent_aware_skeleton_exact"] == [1.0, 1.0]
    assert wrong["component_exponent_aware_skeleton_exact"] == [0.0, 1.0]


def test_selection_rules_share_candidates_but_use_allowed_trajectories() -> None:
    candidates = [
        {"candidate_index": 0, "normalized_ted": 0.0, "complexity": 20,
         "trajectory_metrics": {"input_nrmse": [0.1], "selection_nrmse": [3.0]}},
        {"candidate_index": 1, "normalized_ted": 0.5, "complexity": 2,
         "trajectory_metrics": {"input_nrmse": [0.2], "selection_nrmse": [0.2]}},
    ]
    assert select_candidate(candidates, "official_reconstruction", penalty=10.0) == 0
    assert select_candidate(candidates, "input_robust", penalty=10.0) == 0
    assert select_candidate(candidates, "selection_ic", penalty=10.0) == 1
    assert select_candidate(candidates, "multi_ic", penalty=10.0) == 1
    assert select_candidate(candidates, "structural_oracle", penalty=10.0) == 0


def test_integration_failure_is_worse_than_large_finite_error() -> None:
    candidates = [
        {"candidate_index": 0, "normalized_ted": 0.0, "complexity": 1,
         "trajectory_metrics": {"input_nrmse": [10.0], "selection_nrmse": [10.0],
                                "input_failures": ["CandidateIntegrationFailure"],
                                "selection_failures": ["CandidateIntegrationFailure"]}},
        {"candidate_index": 1, "normalized_ted": 0.5, "complexity": 2,
         "trajectory_metrics": {"input_nrmse": [12.0], "selection_nrmse": [12.0],
                                "input_failures": [None], "selection_failures": [None]}},
    ]
    assert select_candidate(candidates, "input_robust", penalty=10.0) == 1
    assert select_candidate(candidates, "multi_ic", penalty=10.0) == 1


def test_formula_selection_key_macro_averages_system_bundle() -> None:
    common = {"component_normalized_variable_aware_ted": [0.2], "component_valid": [True]}
    rows = [
        {**common, "system_id": "one", "bundle_index": 0,
         "component_exponent_aware_skeleton_exact": [1.0]},
        {**common, "system_id": "three", "bundle_index": 0,
         "component_exponent_aware_skeleton_exact": [0.0, 0.0, 0.0]},
    ]
    exact, negative_ted, valid = formula_selection_key(rows)
    assert exact == 0.5
    assert negative_ted == -0.2
    assert valid == 1.0
