"""Outcome partition and primary decision rule (v16)."""

from __future__ import annotations

from typing import Any

OUTCOME_CATEGORIES = (
    "construction_incomplete",
    "execution_failure",
    "semantic_drift",
    "structural_false_negative",
    "preserved",
    "control_pass",
    "control_failure",
)

PAIR_RESULT_COLUMNS = [
    "condition",
    "pair_id",
    "component_id",
    "system_id",
    "component_idx",
    "scale",
    "rewrite_id",
    "eligibility_layer",
    "partition_scope",
    "outcome_category",
    "construction_incomplete",
    "is_fully_diagnostic",
    "failure_reason",
    "rescale_incomplete",
    "formula_metrics_valid",
    "q4_construction_completed",
    "q4_emitted_infix",
    "q4_sympy_expr_canonical",
    "q4_construction_failure_reason",
    "e2_identity_fallback_candidate",
    "e1_oracle_completed",
    "e1_oracle_equivalent",
    "e1_analytic_equivalent",
    "e1_numeric_equivalent",
    "e1_oracle_failure_reason",
    "e2_oracle_completed",
    "e2_oracle_equivalent",
    "e2_analytic_equivalent",
    "e2_numeric_equivalent",
    "e2_oracle_failure_reason",
    "e0_status",
    "e1_status",
    "e2_status",
    "e0_prefix_raw",
    "e1_prefix_raw",
    "e2_prefix_raw",
    "e0_infix",
    "e1_infix",
    "e2_infix",
    "e2_infix_pre_classifier",
    "classifier_parse_valid",
    "classifier_parse_failure_reason",
    "hill_form",
    "canonical_exact",
    "exponent_aware_skeleton_exact",
    "original_vs_q4_numeric_max_abs_error",
    "quantization_stratum",
    "control_pass_row",
]


def _eligibility_layer(stratum: str | None) -> str:
    mapping = {
        "strict_hill": "strict_hill_primary",
        "non_strict_hill": "non_strict_hill_secondary",
        "linear": "linear_control",
    }
    return mapping.get(str(stratum), "linear_control")


def _partition_scope(condition: str, eligibility_layer: str) -> str:
    if condition == "B1":
        return "control"
    if condition == "B2":
        if eligibility_layer == "strict_hill_primary":
            return "primary"
        if eligibility_layer == "non_strict_hill_secondary":
            return "secondary"
        return "control_linear"
    if condition == "D2":
        return "descriptive"
    if eligibility_layer == "strict_hill_primary":
        return "primary"
    if eligibility_layer == "non_strict_hill_secondary":
        return "secondary"
    return "control_linear"


def classify_outcome(row: dict[str, Any]) -> str:
    if row.get("condition") == "B1":
        return "control_pass" if row.get("control_pass_row") else "control_failure"
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
    stratum = row.pop("stratum", None)
    if "eligibility_layer" not in row and stratum is not None:
        row["eligibility_layer"] = _eligibility_layer(stratum)
    if "partition_scope" not in row:
        row["partition_scope"] = _partition_scope(str(row.get("condition", "B0")), row.get("eligibility_layer", ""))
    if row.get("classifier_parse_valid") is False and not row.get("construction_incomplete"):
        row["execution_failure"] = True
        if not row.get("classifier_parse_failure_reason"):
            row["classifier_parse_failure_reason"] = "ClassifierParseError"
    if row.get("condition") == "B1":
        row["control_pass_row"] = bool(
            row.get("q4_construction_completed")
            and row.get("e1_oracle_completed")
            and row.get("e1_oracle_equivalent")
            and row.get("e2_oracle_completed")
            and row.get("e2_oracle_equivalent")
            and row.get("classifier_parse_valid")
            and row.get("formula_metrics_valid")
        )
    category = classify_outcome(row)
    row["outcome_category"] = category
    row["is_fully_diagnostic"] = is_fully_diagnostic(category)
    return row


def evaluate_primary_decision(
    pair_rows: list[dict[str, Any]],
    *,
    validity_gate_failed: bool,
) -> str:
    strict_rows = [
        row
        for row in pair_rows
        if row.get("eligibility_layer") == "strict_hill_primary" and row.get("condition") == "B0"
    ]
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
