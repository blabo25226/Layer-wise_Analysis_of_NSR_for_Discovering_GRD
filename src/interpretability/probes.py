"""Lightweight validation probes used before expensive GPU_RUN2 fine-tuning."""

from __future__ import annotations

from typing import Any, Iterable, Mapping, Sequence

import numpy as np


def fit_linear_probe(
    hidden: np.ndarray,
    targets: np.ndarray,
    *,
    ridge: float = 1e-4,
) -> dict[str, float]:
    """Ridge linear probe of scalar targets from flattened hidden states."""
    h = np.asarray(hidden, dtype=np.float64)
    y = np.asarray(targets, dtype=np.float64).ravel()
    if h.ndim == 3:
        h = h.reshape(h.shape[0], -1)
    if h.ndim != 2:
        raise ValueError(f"hidden must be 2D or 3D, got {h.shape}")
    if len(h) != len(y):
        raise ValueError("hidden and targets must have the same number of examples")
    n_features = h.shape[1]
    xtx = h.T @ h + ridge * np.eye(n_features)
    xty = h.T @ y
    try:
        weights = np.linalg.solve(xtx, xty)
    except np.linalg.LinAlgError:
        weights = np.linalg.pinv(xtx) @ xty
    pred = h @ weights
    residual = y - pred
    mse = float(np.mean(residual**2))
    denom = float(np.mean((y - np.mean(y)) ** 2)) + 1e-12
    return {
        "mse": mse,
        "nmse_var": float(np.sum(residual**2) / denom),
        "r2": 1.0 - float(np.sum(residual**2) / denom),
        "n_examples": float(len(y)),
        "n_features": float(n_features),
    }


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
