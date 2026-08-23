"""Frozen failure-aware formula model-selection key for GPU_RUN5."""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Iterable

import numpy as np


def formula_selection_key(records: Iterable[dict[str, Any]], validation_ce: float) -> tuple[float, float, float, float]:
    """Return a lexicographic minimization key, macro-averaged by system then seed.

    Invalid components receive exponent-exact=0 and normalized TED=1.  The
    first key is negated because exact recovery is maximized.
    """
    grouped: dict[tuple[str, int], list[dict[str, Any]]] = defaultdict(list)
    for row in records:
        grouped[(str(row["system_id"]), int(row["seed"]))].append(row)
    if not grouped:
        return (0.0, 1.0, 0.0, float(validation_ce))
    system_exact = []
    system_ted = []
    system_valid = []
    for rows in grouped.values():
        exact_values = [float(row.get("exponent_aware_skeleton_exact") or 0.0) if row.get("valid") else 0.0 for row in rows]
        ted_values = [
            min(max(float(row.get("normalized_variable_aware_ted", 1.0)), 0.0), 1.0)
            if row.get("valid") and row.get("normalized_variable_aware_ted") is not None else 1.0
            for row in rows
        ]
        valid_values = [float(bool(row.get("valid"))) for row in rows]
        system_exact.append(float(np.mean(exact_values)))
        system_ted.append(float(np.mean(ted_values)))
        system_valid.append(float(np.mean(valid_values)))
    return (-float(np.mean(system_exact)), float(np.mean(system_ted)), -float(np.mean(system_valid)), float(validation_ce))
