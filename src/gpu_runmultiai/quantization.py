"""Truth-side quantization stratum (preregistration v16 §4.4–§4.5)."""

from __future__ import annotations

from typing import Iterable

from gpu_runmultiai.invariants import ExponentTokenError
from gpu_runmultiai.q4_reference import ALL_OPERATORS


def fractional_digit_count(token: str) -> int:
    """Count fractional digits in a numeric leaf raw token string."""
    if "e" in token or "E" in token:
        raise ExponentTokenError(f"exponent token in numeric leaf: {token}")
    stripped = token.lstrip("+").lstrip("-")
    if "." not in stripped:
        return 0
    fractional = stripped.split(".", 1)[1]
    return len(fractional.rstrip("0"))


def _prefix_leaves(prefix: str) -> list[str]:
    tokens = [token for token in prefix.split(",") if token]
    leaves: list[str] = []
    index = 0

    def consume() -> None:
        nonlocal index
        token = tokens[index]
        index += 1
        if token in ALL_OPERATORS:
            for _ in range(ALL_OPERATORS[token]):
                consume()
        else:
            leaves.append(token)

    while index < len(tokens):
        consume()
    return leaves


def assign_quantization_stratum(truth_prefix: str) -> str:
    """Assign quantization_neutral or quantization_active for one component."""
    for leaf in _prefix_leaves(truth_prefix):
        try:
            float(leaf)
        except ValueError:
            continue
        if fractional_digit_count(leaf) > 4:
            return "quantization_active"
    return "quantization_neutral"


def validate_g_stratum(rows: Iterable[dict[str, str]]) -> None:
    """Abort if strict-Hill quantization stratum counts or exponent tokens fail."""
    active = 0
    neutral = 0
    for row in rows:
        if row.get("eligibility_layer") not in (None, "strict_hill_primary"):
            continue
        stratum = row.get("quantization_stratum")
        if stratum == "quantization_active":
            active += 1
        elif stratum == "quantization_neutral":
            neutral += 1
        else:
            raise ExponentTokenError(f"unclassified quantization stratum: {stratum!r}")
    from gpu_runmultiai.constants import (
        EXPECTED_QUANTIZATION_ACTIVE_COMPONENTS,
        EXPECTED_QUANTIZATION_NEUTRAL_COMPONENTS,
    )
    from gpu_runmultiai.invariants import StratumGateError

    if active != EXPECTED_QUANTIZATION_ACTIVE_COMPONENTS:
        raise StratumGateError(
            f"G_stratum FAIL: quantization_active={active} != {EXPECTED_QUANTIZATION_ACTIVE_COMPONENTS}"
        )
    if neutral != EXPECTED_QUANTIZATION_NEUTRAL_COMPONENTS:
        raise StratumGateError(
            f"G_stratum FAIL: quantization_neutral={neutral} != {EXPECTED_QUANTIZATION_NEUTRAL_COMPONENTS}"
        )
