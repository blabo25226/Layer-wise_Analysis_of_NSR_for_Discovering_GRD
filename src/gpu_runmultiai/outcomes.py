"""Outcome partition and primary decision rule (v9)."""

from __future__ import annotations

from typing import Any

OUTCOME_CATEGORIES = (
    "construction_incomplete",
    "execution_failure",
    "semantic_drift",
    "structural_false_negative",
    "preserved",
)


def classify_outcome(row: dict[str, Any]) -> str:
    if row.get("construction_incomplete"):
        return "construction_incomplete"
    if row.get("execution_failure"):
        return "execution_failure"
    if row.get("semantic_drift"):
        return "semantic_drift"
    e1_eq = bool(row.get("e1_oracle_equivalent"))
    e2_eq = bool(row.get("e2_oracle_equivalent"))
    hill_form = bool(row.get("hill_form"))
    if e1_eq and e2_eq and not hill_form:
        return "structural_false_negative"
    if e1_eq and e2_eq and hill_form:
        return "preserved"
    return "unknown"


def is_fully_diagnostic(outcome_category: str) -> bool:
    return outcome_category in {"preserved", "structural_false_negative"}


def build_outcome_row(**flags: Any) -> dict[str, Any]:
    row = dict(flags)
    category = classify_outcome(row)
    row["outcome_category"] = category
    row["is_fully_diagnostic"] = is_fully_diagnostic(category)
    return row


def evaluate_primary_decision(
    pair_rows: list[dict[str, Any]],
    *,
    validity_gate_failed: bool,
) -> str:
    strict_rows = [row for row in pair_rows if row.get("stratum") == "strict_hill" and row.get("condition") == "B0"]
    pair_ids = [row["pair_id"] for row in strict_rows]
    if validity_gate_failed:
        return "H0001 undecidable"
    if len(pair_ids) != 1320 or len(set(pair_ids)) != 1320:
        return "H0001 undecidable"
    if any(row.get("outcome_category") == "unknown" for row in strict_rows):
        return "H0001 undecidable"
    sfn = sum(1 for row in strict_rows if row.get("outcome_category") == "structural_false_negative")
    if sfn >= 1:
        return "H0001 supported"
    fully_diagnostic = all(row.get("is_fully_diagnostic") for row in strict_rows)
    if sfn == 0 and fully_diagnostic:
        return "H0001 unsupported"
    return "H0001 undecidable"


def partition_counts(rows: list[dict[str, Any]], denominator: int) -> dict[str, float]:
    counts = {name: 0 for name in OUTCOME_CATEGORIES}
    unknown = 0
    for row in rows:
        category = row.get("outcome_category", "unknown")
        if category in counts:
            counts[category] += 1
        else:
            unknown += 1
    rates = {name: counts[name] / denominator for name in OUTCOME_CATEGORIES}
    rates["unknown"] = unknown / denominator
    return rates
