"""Lightweight validation probes used before expensive GPU_RUN2 fine-tuning."""

from __future__ import annotations

import sys
from typing import Any, Iterable, Mapping, Sequence

import numpy as np
import sympy as sp

from evaluation.equation_metrics import extract_variables


def _dense_matmul(left: np.ndarray, right: np.ndarray) -> np.ndarray:
    torch_mod = sys.modules.get("torch")
    if torch_mod is not None:
        return (
            torch_mod.as_tensor(left, dtype=torch_mod.float64)
            @ torch_mod.as_tensor(right, dtype=torch_mod.float64)
        ).detach().cpu().numpy()
    return np.asarray(left) @ np.asarray(right)


def _ridge_weights(h: np.ndarray, y: np.ndarray, ridge: float) -> np.ndarray:
    """Solve ridge regression in the cheaper primal/dual form.

    Uses the dual ``(HHᵀ + λI)α = y``, ``w = Hᵀα`` when ``n_features > n_examples``,
    otherwise the primal ``(HᵀH + λI)w = Hᵀy``. The primal alone is catastrophic for
    NeSymReS activations flattened to tens of thousands of features with few rows.
    """
    h = np.asarray(h, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64).ravel()
    n_examples, n_features = h.shape
    torch_mod = sys.modules.get("torch")
    if torch_mod is not None:
        H = torch_mod.as_tensor(h, dtype=torch_mod.float64)
        target = torch_mod.as_tensor(y, dtype=torch_mod.float64)
        if n_features > n_examples:
            hht = H @ H.T + float(ridge) * torch_mod.eye(n_examples, dtype=H.dtype)
            try:
                alpha = torch_mod.linalg.solve(hht, target)
            except Exception:
                alpha = torch_mod.linalg.lstsq(hht, target, rcond=None).solution
            return (H.T @ alpha).detach().cpu().numpy()
        xtx = H.T @ H + float(ridge) * torch_mod.eye(n_features, dtype=H.dtype)
        try:
            return torch_mod.linalg.solve(xtx, H.T @ target).detach().cpu().numpy()
        except Exception:
            return torch_mod.linalg.lstsq(xtx, H.T @ target, rcond=None).solution.detach().cpu().numpy()
    if n_features > n_examples:
        hht = h @ h.T + float(ridge) * np.eye(n_examples)
        try:
            alpha = np.linalg.solve(hht, y)
        except np.linalg.LinAlgError:
            alpha = np.linalg.pinv(hht) @ y
        return h.T @ alpha
    xtx = h.T @ h + float(ridge) * np.eye(n_features)
    xty = h.T @ y
    try:
        return np.linalg.solve(xtx, xty)
    except np.linalg.LinAlgError:
        return np.linalg.pinv(xtx) @ xty


def fit_linear_probe(
    hidden: np.ndarray,
    targets: np.ndarray,
    *,
    ridge: float = 1e-4,
    eval_hidden: np.ndarray | None = None,
    eval_targets: np.ndarray | None = None,
) -> dict[str, float]:
    """Ridge probe, optionally scored on a disjoint held-out set."""
    h = np.asarray(hidden, dtype=np.float64)
    y = np.asarray(targets, dtype=np.float64).ravel()
    if h.ndim == 3:
        h = h.reshape(h.shape[0], -1)
    if h.ndim != 2:
        raise ValueError(f"hidden must be 2D or 3D, got {h.shape}")
    if len(h) != len(y):
        raise ValueError("hidden and targets must have the same number of examples")
    weights = _ridge_weights(h, y, ridge)
    h_eval = h if eval_hidden is None else np.asarray(eval_hidden, dtype=np.float64)
    y_eval = y if eval_targets is None else np.asarray(eval_targets, dtype=np.float64).ravel()
    if h_eval.ndim == 3:
        h_eval = h_eval.reshape(h_eval.shape[0], -1)
    if h_eval.ndim != 2 or len(h_eval) != len(y_eval):
        raise ValueError("eval_hidden and eval_targets must be aligned 2D data")
    pred = _dense_matmul(h_eval, weights)
    residual = y_eval - pred
    mse = float(np.mean(residual**2))
    denom = float(np.sum((y_eval - np.mean(y_eval)) ** 2)) + 1e-12
    return {
        "mse": mse,
        "nmse_var": float(np.sum(residual**2) / denom),
        "r2": 1.0 - float(np.sum(residual**2) / denom),
        "n_examples": float(len(y_eval)),
        "n_train_examples": float(len(y)),
        "n_features": float(h.shape[1]),
    }


def fit_linear_classifier_probe(
    hidden: np.ndarray,
    labels: Sequence[Any],
    *,
    ridge: float = 1e-4,
    eval_hidden: np.ndarray | None = None,
    eval_labels: Sequence[Any] | None = None,
) -> dict[str, float]:
    """One-vs-rest ridge classifier, optionally scored on held-out examples."""
    h = np.asarray(hidden, dtype=np.float64)
    if h.ndim == 3:
        h = h.reshape(h.shape[0], -1)
    if h.ndim != 2:
        raise ValueError(f"hidden must be 2D or 3D, got {h.shape}")
    encoded = np.asarray([str(label) for label in labels], dtype=object)
    if len(h) != len(encoded):
        raise ValueError("hidden and labels must have the same number of examples")
    classes, inv = np.unique(encoded, return_inverse=True)
    n_examples, n_features = h.shape
    if len(classes) < 2:
        return {
            "accuracy": float("nan"),
            "majority_baseline": 1.0 if n_examples else float("nan"),
            "n_classes": float(len(classes)),
            "n_examples": float(n_examples),
            "n_features": float(n_features),
        }
    h_eval = h if eval_hidden is None else np.asarray(eval_hidden, dtype=np.float64)
    labels_eval = encoded if eval_labels is None else np.asarray(
        [str(label) for label in eval_labels], dtype=object
    )
    if h_eval.ndim == 3:
        h_eval = h_eval.reshape(h_eval.shape[0], -1)
    if h_eval.ndim != 2 or len(h_eval) != len(labels_eval):
        raise ValueError("eval_hidden and eval_labels must be aligned 2D data")
    class_to_index = {label: index for index, label in enumerate(classes)}
    scores = np.zeros((len(h_eval), len(classes)), dtype=np.float64)
    for index in range(len(classes)):
        y = np.where(inv == index, 1.0, -1.0)
        weights = _ridge_weights(h, y, ridge)
        scores[:, index] = _dense_matmul(h_eval, weights)
    predicted = scores.argmax(axis=1)
    expected = np.asarray([class_to_index.get(label, -1) for label in labels_eval])
    counts = np.bincount(inv, minlength=len(classes))
    return {
        "accuracy": float(np.mean(predicted == expected)),
        "majority_baseline": float(np.max(counts) / max(n_examples, 1)),
        "n_classes": float(len(classes)),
        "n_examples": float(len(labels_eval)),
        "n_train_examples": float(n_examples),
        "n_features": float(n_features),
    }


def expression_structure_attributes(expr: str, *, variable_names: Sequence[str] | None = None) -> dict[str, float]:
    """Scalar symbolic-structure targets for regression probes."""
    text = str(expr or "").strip()
    n_variables = float(len(extract_variables(text))) if text else 0.0
    if n_variables == 0.0 and variable_names:
        n_variables = float(len(variable_names))
    n_operators = 0.0
    if text:
        try:
            tree = sp.sympify(text.replace("^", "**"))
            n_operators = float(
                sum(1 for node in sp.preorder_traversal(tree) if node.is_Add or node.is_Mul or node.is_Pow)
            )
        except Exception:
            n_operators = float("nan")
    return {"n_variables": n_variables, "n_operators": n_operators}


def mean_rank_layer_scores(
    tables: Mapping[str, Mapping[str, float]],
    *,
    higher_is_better: Mapping[str, bool],
) -> dict[str, float]:
    """Average per-metric ranks. Rank 1 is best. Missing metrics are skipped."""
    layers = sorted({name for table in tables.values() for name in table})
    ranks: dict[str, list[float]] = {name: [] for name in layers}
    for metric, table in tables.items():
        usable = {
            name: float(value)
            for name, value in table.items()
            if value is not None and np.isfinite(float(value))
        }
        if len(usable) < 2:
            continue
        hib = bool(higher_is_better.get(metric, True))
        ordered = sorted(usable, key=lambda name: usable[name], reverse=hib)
        rank_map = {name: float(index + 1) for index, name in enumerate(ordered)}
        for name in layers:
            if name in rank_map:
                ranks[name].append(rank_map[name])
    return {name: float(np.mean(values)) for name, values in ranks.items() if values}


def ranking_from_mean_rank(mean_ranks: Mapping[str, float]) -> list[str]:
    """Best → worst by mean rank (ties broken by layer name)."""
    return sorted(mean_ranks, key=lambda name: (float(mean_ranks[name]), str(name)))


def gradient_norms(
    named_grads: Mapping[str, np.ndarray] | Iterable[tuple[str, Any]],
) -> dict[str, float]:
    """L2 gradient norms per named layer or parameter group."""
    if isinstance(named_grads, Mapping):
        items = named_grads.items()
    else:
        items = named_grads
    out: dict[str, float] = {}
    for name, value in items:
        array = np.asarray(value, dtype=np.float64)
        out[str(name)] = float(np.linalg.norm(array))
    return out


def parameter_update_sensitivity(
    before: Mapping[str, np.ndarray],
    after: Mapping[str, np.ndarray],
) -> dict[str, float]:
    """Relative parameter change ``||Δθ|| / (||θ|| + eps)`` per layer."""
    out: dict[str, float] = {}
    for name, base in before.items():
        if name not in after:
            continue
        b = np.asarray(base, dtype=np.float64)
        a = np.asarray(after[name], dtype=np.float64)
        delta = a - b
        out[str(name)] = float(np.linalg.norm(delta) / (np.linalg.norm(b) + 1e-12))
    return out
