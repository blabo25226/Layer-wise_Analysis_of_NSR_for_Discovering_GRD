"""Fixed ablation and activation-intervention protocols for GPU_RUN2 Phase 4."""

from __future__ import annotations

from typing import Any

import numpy as np


def ablation_zero_output(activation: np.ndarray) -> np.ndarray:
    """Replace a layer activation with zeros (hard ablation)."""
    return np.zeros_like(np.asarray(activation))


def interpolate_activations(
    source: np.ndarray,
    destination: np.ndarray,
    *,
    alpha: float,
) -> np.ndarray:
    """Linear activation intervention: ``(1-alpha)*source + alpha*destination``."""
    if not 0.0 <= float(alpha) <= 1.0:
        raise ValueError(f"alpha must be in [0, 1], got {alpha}")
    src = np.asarray(source, dtype=np.float64)
    dst = np.asarray(destination, dtype=np.float64)
    if src.shape != dst.shape:
        raise ValueError(f"activation shapes differ: {src.shape} vs {dst.shape}")
    return ((1.0 - alpha) * src + alpha * dst).astype(src.dtype, copy=False)


def mean_activation_baseline(activation: np.ndarray, *, axis: int = 0) -> np.ndarray:
    """Broadcast the mean activation as a non-informative replacement."""
    array = np.asarray(activation, dtype=np.float64)
    mean = array.mean(axis=axis, keepdims=True)
    return np.broadcast_to(mean, array.shape).copy()


def intervention_delta(
    baseline_score: float,
    intervened_score: float,
    *,
    higher_is_better: bool,
) -> float:
    """Signed effect of an intervention relative to the unintervened score."""
    if higher_is_better:
        return float(intervened_score - baseline_score)
    return float(baseline_score - intervened_score)
