"""Failure-aware trajectory and formula helpers for GPU_RUN5."""

from __future__ import annotations

import math
from typing import Any, Iterable

import numpy as np

from evaluation.gpu_run5_structure import classify_formula
from gpu_run4.formulas import compare_formulas, parse_system
from gpu_run4.ted import system_ted


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
    return value if math.isfinite(value) else float(penalty)


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

    def score(row: dict[str, Any]) -> tuple[float, int]:
        metrics = row["trajectory_metrics"]
        if rule == "input_robust":
            value = robust_median(metrics["input_nrmse"], penalty=penalty)
        elif rule == "selection_ic":
            value = robust_median(metrics["selection_nrmse"], penalty=penalty)
        elif rule in {"multi_ic", "multi_ic_complexity"}:
            value = robust_median(metrics["input_nrmse"] + metrics["selection_nrmse"], penalty=penalty)
            if rule == "multi_ic_complexity":
                value += float(complexity_lambda) * float(row.get("complexity") or 0)
        elif rule == "structural_oracle":
            value = float(row.get("normalized_ted")) if row.get("normalized_ted") is not None else float(penalty)
        else:
            raise ValueError(f"unknown selection rule: {rule}")
        if not math.isfinite(value):
            value = float(penalty)
        return value, int(row["candidate_index"])

    return min(candidates, key=score)["candidate_index"]


def formula_selection_key(rows: list[dict[str, Any]]) -> tuple[float, float, float]:
    """Lexicographic validation key: exact ↑, failure-aware TED ↓, valid ↑."""
    if not rows:
        return (0.0, -1.0, 0.0)
    component_exact = [
        value
        for row in rows
        for value in row.get("component_exponent_aware_skeleton_exact", [])
    ]
    exact = float(np.mean(component_exact)) if component_exact else 0.0
    ted = [
        float(row["normalized_ted"])
        if row.get("valid") and row.get("normalized_ted") is not None and math.isfinite(float(row["normalized_ted"]))
        else 1.0
        for row in rows
    ]
    valid = float(np.mean([bool(row.get("valid")) for row in rows]))
    return exact, -float(np.mean(ted)), valid
