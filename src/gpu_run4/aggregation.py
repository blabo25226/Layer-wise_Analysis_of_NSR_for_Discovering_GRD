"""Failure-aware aggregation with Student-t intervals for GPU_RUN4."""

from __future__ import annotations

import math
from typing import Any, Sequence

import numpy as np


def finite(values: Sequence[Any]) -> list[float]:
    out = []
    for value in values:
        if value is None:
            continue
        number = float(value)
        if math.isfinite(number):
            out.append(number)
    return out


def student_t_ci(values: Sequence[float], *, alpha: float = 0.05) -> dict[str, float]:
    sample = finite(values)
    n = len(sample)
    if n == 0:
        return {"n": 0, "mean": float("nan"), "std": float("nan"), "ci_low": float("nan"), "ci_high": float("nan")}
    mean = float(np.mean(sample))
    if n == 1:
        return {"n": 1, "mean": mean, "std": float("nan"), "ci_low": mean, "ci_high": mean, "ci_method": "student_t"}
    std = float(np.std(sample, ddof=1))
    from scipy.stats import t

    half = float(t.ppf(1 - alpha / 2, df=n - 1) * std / math.sqrt(n))
    return {
        "n": n,
        "mean": mean,
        "median": float(np.median(sample)),
        "std": std,
        "ci_low": mean - half,
        "ci_high": mean + half,
        "ci_method": "student_t",
    }


def summarize_records(rows: Sequence[dict[str, Any]], *, keys: Sequence[str]) -> dict[str, Any]:
    n = len(rows)
    n_valid = sum(1 for row in rows if row.get("valid"))
    out: dict[str, Any] = {
        "n": n,
        "n_valid": n_valid,
        "valid_rate": float(n_valid / n) if n else float("nan"),
        "accuracy_r2_gt_0.9": float(
            sum(1 for row in rows if (row.get("reconstruction_r2") or float("nan")) > 0.9) / n
        )
        if n
        else float("nan"),
    }
    for key in keys:
        stats = student_t_ci([row.get(key) for row in rows])
        out[key] = stats
        penalized = []
        for row in rows:
            value = row.get(key)
            if row.get("valid") and value is not None and math.isfinite(float(value)):
                penalized.append(float(value))
            elif key.endswith("_r2"):
                penalized.append(-1.0)
            else:
                penalized.append(float("nan"))
        out[f"penalized_{key}"] = student_t_ci(penalized)
    failures: dict[str, int] = {}
    for row in rows:
        reason = row.get("failure_reason")
        if reason:
            failures[str(reason)] = failures.get(str(reason), 0) + 1
    out["failures"] = failures
    return out
