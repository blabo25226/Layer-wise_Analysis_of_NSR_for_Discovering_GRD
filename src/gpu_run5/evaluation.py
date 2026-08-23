"""Failure-aware trajectory and formula helpers for GPU_RUN5."""

from __future__ import annotations

import math
from typing import Any, Iterable

import numpy as np

from evaluation.gpu_run5_structure import classify_formula
from gpu_run4.formulas import compare_formulas, parse_system
from gpu_run4.ted import system_ted, tree_size


def trajectory_nrmse(true: np.ndarray, predicted: np.ndarray | None, *, penalty: float) -> float:
    """Return scale-normalized RMSE, assigning ``penalty`` to every failure."""
    truth = np.asarray(true, dtype=float)
    if predicted is None:
        return float(penalty)
    pred = np.asarray(predicted, dtype=float)
    if pred.shape != truth.shape or not np.isfinite(pred).all():
        return float(penalty)
    scale = float(np.sqrt(np.mean((truth - np.mean(truth, axis=0, keepdims=True)) ** 2)))
    if not math.isfinite(scale) or scale < 1e-8:
        scale = max(float(np.sqrt(np.mean(truth**2))), 1e-8)
    value = float(np.sqrt(np.mean((pred - truth) ** 2)) / scale)
    if not math.isfinite(value):
        return float(penalty)
    # A successful but very poor integration must remain distinguishable from
    # an outright failure, whose preregistered score is exactly ``penalty``.
    return min(value, float(penalty) - max(abs(float(penalty)) * 1e-9, 1e-12))


def robust_median(values: Iterable[float], *, penalty: float) -> float:
    finite = [float(value) if math.isfinite(float(value)) else float(penalty) for value in values]
    return float(np.median(finite)) if finite else float(penalty)


def formula_metrics(true_infix: str, predicted_infix: str) -> dict[str, Any]:
    """Compute system and component metrics without expensive CAS equivalence."""
    comparison = compare_formulas(true_infix, predicted_infix, skip_cas=True)
    true_parsed = parse_system(true_infix)
    pred_parsed = parse_system(predicted_infix)
    component = system_ted(true_parsed["components"], pred_parsed["components"])
    true_structure = classify_formula(true_infix)
    pred_structure = classify_formula(predicted_infix)
    true_exp = true_structure["exponent_aware_skeleton"].split(" | ")
    pred_exp = pred_structure["exponent_aware_skeleton"].split(" | ")
    n_components = max(len(true_exp), len(pred_exp), 1)
    component_exp = [
        float(index < len(true_exp) and index < len(pred_exp) and true_exp[index] == pred_exp[index])
        for index in range(n_components)
    ]
    true_components = list(true_parsed["components"])
    pred_components = list(pred_parsed["components"])
    n_tree_components = max(len(true_components), len(pred_components), 1)
    true_components += [None] * (n_tree_components - len(true_components))
    pred_components += [None] * (n_tree_components - len(pred_components))
    component_normalized = []
    component_valid = []
    component_failures = []
    for index, (true_tree, pred_tree) in enumerate(zip(true_components, pred_components)):
        denom = tree_size(true_tree) + tree_size(pred_tree)
        raw = float(component["component_ted_raw"][index])
        component_normalized.append(min(max(raw / max(denom, 1), 0.0), 1.0))
        valid = true_tree is not None and pred_tree is not None
        component_valid.append(bool(valid))
        component_failures.append(None if valid else "TEDParseError")
    return {
        "valid": bool(comparison["valid"] and comparison["component_count_match"]),
        "failure_reason": comparison["failure_reason"],
        "canonical_exact": comparison["canonical_exact"],
        "skeleton_exact": comparison["skeleton_exact"],
        "exponent_aware_skeleton_exact": float(
            comparison["component_count_match"]
            and true_structure["exponent_aware_skeleton"] == pred_structure["exponent_aware_skeleton"]
        ),
        "component_exponent_aware_skeleton_exact": component_exp,
        "ted_raw": comparison["ted_raw"],
        "ted_skeleton": comparison["ted_skeleton"],
        "normalized_ted": comparison["normalized_ted"],
        "component_ted_raw": component["component_ted_raw"],
        "component_ted_skeleton": component["component_ted_skeleton"],
        "component_normalized_variable_aware_ted": component_normalized,
        "component_valid": component_valid,
        "component_failure_reason": component_failures,
        "normalized_variable_aware_ted": float(np.mean(component_normalized)),
        "variable_aware_ted_definition": "index-aligned component TED preserving x_i identity / (true_size + predicted_size)",
        "complexity": comparison["complexity"],
        "candidate_formula_canonical": comparison["pred_formula_canonical"],
        "candidate_formula_skeleton": comparison["pred_formula_skeleton"],
        "candidate_exponent_aware_skeleton": pred_structure["exponent_aware_skeleton"],
        "structure": pred_structure,
    }


def select_candidate(candidates: list[dict[str, Any]], rule: str, *, penalty: float, complexity_lambda: float = 0.0) -> int | None:
    """Select one candidate using only the trajectories permitted by ``rule``."""
    if not candidates:
        return None
    if rule == "official_reconstruction":
        return 0

    def score(row: dict[str, Any]) -> tuple[float, float, int]:
        metrics = row["trajectory_metrics"]
        if rule == "input_robust":
            value = robust_median(metrics["input_nrmse"], penalty=penalty)
            failures = sum(item is not None for item in metrics.get("input_failures", [None] * len(metrics["input_nrmse"])))
        elif rule == "selection_ic":
            value = robust_median(metrics["selection_nrmse"], penalty=penalty)
            failures = sum(item is not None for item in metrics.get("selection_failures", [None] * len(metrics["selection_nrmse"])))
        elif rule in {"multi_ic", "multi_ic_complexity"}:
            value = robust_median(metrics["input_nrmse"] + metrics["selection_nrmse"], penalty=penalty)
            failures = sum(
                item is not None
                for item in metrics.get("input_failures", [None] * len(metrics["input_nrmse"]))
                + metrics.get("selection_failures", [None] * len(metrics["selection_nrmse"]))
            )
            if rule == "multi_ic_complexity":
                value += float(complexity_lambda) * float(row.get("complexity") or 0)
        elif rule == "structural_oracle":
            value = float(row.get("normalized_ted")) if row.get("normalized_ted") is not None else float(penalty)
            failures = 0 if row.get("valid") else 1
        else:
            raise ValueError(f"unknown selection rule: {rule}")
        if not math.isfinite(value):
            value = float(penalty)
        return float(failures), value, int(row["candidate_index"])

    return min(candidates, key=score)["candidate_index"]


def formula_selection_key(rows: list[dict[str, Any]]) -> tuple[float, float, float]:
    """System×bundle macro key: component exact ↑, failure-aware TED ↓, valid ↑."""
    if not rows:
        return (0.0, -1.0, 0.0)
    grouped: dict[tuple[str, int], list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault((str(row.get("system_id", "")), int(row.get("bundle_index", 0))), []).append(row)
    exact_groups, ted_groups, valid_groups = [], [], []
    for group in grouped.values():
        cell_exact, cell_ted, cell_valid = [], [], []
        for row in group:
            exact_values = row.get("component_exponent_aware_skeleton_exact", []) or [0.0]
            ted_values = row.get("component_normalized_variable_aware_ted", []) or [1.0]
            valid_values = row.get("component_valid", []) or [False]
            cell_exact.append(float(np.mean(exact_values)))
            cell_ted.append(float(np.mean([value if math.isfinite(float(value)) else 1.0 for value in ted_values])))
            cell_valid.append(float(np.mean(valid_values)))
        exact_groups.append(float(np.mean(cell_exact)))
        ted_groups.append(float(np.mean(cell_ted)))
        valid_groups.append(float(np.mean(cell_valid)))
    return float(np.mean(exact_groups)), -float(np.mean(ted_groups)), float(np.mean(valid_groups))
