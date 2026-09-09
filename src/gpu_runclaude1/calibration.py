"""Part A cost calibration (Gate 0 item 8, v2 §11.1).

Frozen sampling frame: 400 candidates, 50 per family,
``numpy.random.default_rng(20260909)``, **timing only**. The integrity
constraint is frozen: no match indicator produced during timing calibration
may be stored, printed, logged, aggregated or read by any agent. A
calibration that reports a match rate has leaked the endpoint and makes Part
A ``undecidable``. :func:`run_calibration` enforces this by discarding the
``score_pair`` return value immediately at the call site -- it is never
placed in a variable that outlives the loop iteration, never returned, and
the function's return type carries no field capable of holding one.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence

import numpy as np

from gpu_runclaude1.matcher import score_pair


def sample_candidates(
    all_candidates: Sequence[dict[str, Any]],
    *,
    n_total: int,
    per_family: int,
    seed: int,
) -> list[dict[str, Any]]:
    """The frozen sampling frame: ``n_total`` candidates, ``per_family`` per
    family, drawn with ``numpy.random.default_rng(seed)`` (v2 §11.1).
    """
    rng = np.random.default_rng(seed)
    by_family: dict[str, list[int]] = {}
    for index, row in enumerate(all_candidates):
        by_family.setdefault(str(row["family"]), []).append(index)
    sampled_indices: list[int] = []
    for family in sorted(by_family):
        indices = by_family[family]
        k = min(per_family, len(indices))
        chosen = rng.choice(np.asarray(indices), size=k, replace=False)
        sampled_indices.extend(int(i) for i in chosen)
    sampled_indices = sampled_indices[:n_total]
    return [all_candidates[i] for i in sampled_indices]


@dataclass(frozen=True)
class CalibrationResult:
    n_candidates: int
    mean_sec: float
    median_sec: float
    p95_sec: float
    per_family_mean_sec: dict
    projected_core_hours: float


def run_calibration(sampled: Sequence[dict[str, Any]], *, n_stored_candidates: int) -> CalibrationResult:
    """Timing-only pass over ``sampled``. Each candidate is scored through the
    exact v2 Part A pipeline (:func:`gpu_runclaude1.matcher.score_pair`) so
    the timing reflects real cost, but the match result is discarded at the
    call site -- see the module docstring's integrity constraint.
    """
    import time

    per_family_times: dict[str, list[float]] = {}
    all_times: list[float] = []
    for row in sampled:
        true_infix = str(row.get("true_formula_infix") or row.get("true_formula") or "")
        candidate_infix = str(row.get("candidate_formula_raw") or "")
        family = str(row.get("family", "unknown"))
        started = time.perf_counter()
        score_pair(true_infix, candidate_infix)  # match result intentionally not bound to a name
        elapsed = time.perf_counter() - started
        all_times.append(elapsed)
        per_family_times.setdefault(family, []).append(elapsed)
    times = np.asarray(all_times, dtype=float)
    mean_sec = float(np.mean(times)) if times.size else float("nan")
    return CalibrationResult(
        n_candidates=len(sampled),
        mean_sec=mean_sec,
        median_sec=float(np.median(times)) if times.size else float("nan"),
        p95_sec=float(np.percentile(times, 95)) if times.size else float("nan"),
        per_family_mean_sec={family: float(np.mean(vals)) for family, vals in per_family_times.items()},
        projected_core_hours=(mean_sec * n_stored_candidates / 3600.0) if times.size else float("nan"),
    )
