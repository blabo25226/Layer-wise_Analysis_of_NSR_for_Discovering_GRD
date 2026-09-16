"""G_eligibility checks (preregistration v16 §2.5.1)."""

from __future__ import annotations

from typing import Iterable

from gpu_runmultiai.constants import (
    EXPECTED_COMPONENTS,
    EXPECTED_LINEAR_COMPONENTS,
    EXPECTED_NON_STRICT_HILL_COMPONENTS,
    EXPECTED_STRICT_HILL_COMPONENTS,
)
from gpu_runmultiai.invariants import EligibilityGateError
from gpu_runmultiai.strata import component_stratum


def validate_g_eligibility(component_index: Iterable[dict]) -> dict[str, int]:
    counts = {"strict_hill": 0, "non_strict_hill": 0, "linear": 0, "other": 0}
    for item in component_index:
        stratum = component_stratum(item["family"], item["component_idx"])
        counts[stratum] += 1
    if sum(counts.values()) != EXPECTED_COMPONENTS:
        raise EligibilityGateError(f"G_eligibility FAIL: component count {sum(counts.values())} != {EXPECTED_COMPONENTS}")
    if counts["other"] > 0:
        raise EligibilityGateError("G_eligibility FAIL: component in zero or multiple layers")
    if counts["strict_hill"] != EXPECTED_STRICT_HILL_COMPONENTS:
        raise EligibilityGateError(
            f"G_eligibility FAIL: strict_hill={counts['strict_hill']} != {EXPECTED_STRICT_HILL_COMPONENTS}"
        )
    if counts["non_strict_hill"] != EXPECTED_NON_STRICT_HILL_COMPONENTS:
        raise EligibilityGateError(
            f"G_eligibility FAIL: non_strict_hill={counts['non_strict_hill']} != {EXPECTED_NON_STRICT_HILL_COMPONENTS}"
        )
    if counts["linear"] != EXPECTED_LINEAR_COMPONENTS:
        raise EligibilityGateError(
            f"G_eligibility FAIL: linear={counts['linear']} != {EXPECTED_LINEAR_COMPONENTS}"
        )
    return counts
