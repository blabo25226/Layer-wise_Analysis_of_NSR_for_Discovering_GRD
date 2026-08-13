"""Linear CKA (Kornblith et al., ICML 2019) for layer representation similarity."""

from __future__ import annotations

import numpy as np


def _center_columns(x: np.ndarray) -> np.ndarray:
    x = np.asarray(x, dtype=np.float64)
    if x.ndim != 2:
        raise ValueError(f"CKA input must be 2D (n_examples, n_features), got {x.shape}")
    return x - x.mean(axis=0, keepdims=True)


def linear_cka(x: np.ndarray, y: np.ndarray) -> float:
    """Unbiased-looking linear CKA between two representation matrices.

    ``x`` and ``y`` must share the example axis. Features may differ. Returns
    a value in ``[0, 1]`` when both matrices have variance; otherwise ``nan``.
    """
    xc = _center_columns(x)
    yc = _center_columns(y)
    if xc.shape[0] != yc.shape[0]:
        raise ValueError("CKA requires the same number of examples in x and y")
    if xc.shape[0] < 2:
        return float("nan")
    xtx = xc.T @ xc
    yty = yc.T @ yc
    xty = xc.T @ yc
    hsic_xy = float(np.sum(xty * xty))
    hsic_xx = float(np.sum(xtx * xtx))
    hsic_yy = float(np.sum(yty * yty))
    denom = np.sqrt(hsic_xx * hsic_yy)
    if denom <= 0.0 or not np.isfinite(denom):
        return float("nan")
    return float(hsic_xy / denom)
