"""Outcome partition and primary decision rule (v16)."""

from __future__ import annotations

from typing import Any

FIVE_OUTCOME_CATEGORIES = (
    "construction_incomplete",
    "execution_failure",
    "semantic_drift",
    "structural_false_negative",
    "preserved",
)

OUTCOME_CATEGORIES = FIVE_OUTCOME_CATEGORIES + (
    "control_pass",
    "control_failure",
)

# §2.5.4 D2 descriptive terminal mapping: the five-outcome result is recorded as a
# descriptive terminal, never as `preserved`.
DESCRIPTIVE_RECORDED_SOURCE_OUTCOMES = frozenset(
    {"preserved", "structural_false_negative", "semantic_drift", "execution_failure"}
)

# §2.5.2 allowed terminal vocabulary per partition_scope; `unknown` is prohibited everywhere.
TERMINAL_VOCABULARY: dict[str, frozenset[str]] = {
    "primary": frozenset(FIVE_OUTCOME_CATEGORIES),
    "secondary": frozenset(FIVE_OUTCOME_CATEGORIES),
    "control_linear": frozenset(FIVE_OUTCOME_CATEGORIES),
    "control": frozenset({"control_pass", "control_failure"}),
    "diagnostic": frozenset({"diagnostic_complete", "diagnostic_failed"}),
    "metric_sanity": frozenset({"sanity_pass", "sanity_failure"}),
    "negative_control": frozenset({"negative_reject", "negative_failed"}),
    "q4_fixture": frozenset({"fixture_pass", "fixture_failure"}),
    "descriptive": frozenset({"descriptive_recorded", "descriptive_failed"}),
}

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


ELIGIBILITY_LAYER_BY_STRATUM = {
    "strict_hill": "strict_hill_primary",
    "non_strict_hill": "non_strict_hill_secondary",
    "linear": "linear_control",
}


def eligibility_layer_for_stratum(stratum: str | None) -> str:
    """Map a truth-side stratum to its frozen eligibility layer; abort when unmapped."""
    layer = ELIGIBILITY_LAYER_BY_STRATUM.get(str(stratum))
    if layer is None:
        from gpu_runmultiai.invariants import StratumGateError

        raise StratumGateError(
            f"G_stratum FAIL: component stratum {stratum!r} has no frozen eligibility layer"
        )
    return layer


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


def _execution_failure_predicate(row: dict[str, Any]) -> bool:
    """§2.2 precedence-2 predicate, read only from durable row flags."""
    return bool(
        row.get("execution_failure")
        or row.get("q4_construction_completed") is False
        or row.get("e2_identity_fallback_candidate")
        or row.get("classifier_parse_valid") is False
        or row.get("rescale_incomplete")
        or row.get("e1_oracle_completed") is False
        or row.get("e2_oracle_completed") is False
    )


def _semantic_drift_predicate(row: dict[str, Any], *, stage_keys: tuple[str, ...]) -> bool:
    for stage in stage_keys:
        if row.get(f"{stage}_oracle_completed") and not row.get(f"{stage}_oracle_equivalent"):
            return True
    return bool(row.get("semantic_drift"))


def _classify_five_whole_chain(row: dict[str, Any]) -> str:
    if row.get("construction_incomplete"):
        return "construction_incomplete"
    if _execution_failure_predicate(row):
        return "execution_failure"
    if _semantic_drift_predicate(row, stage_keys=("e1", "e2")):
        return "semantic_drift"
    e1_eq = bool(row.get("e1_oracle_equivalent"))
    e2_eq = bool(row.get("e2_oracle_equivalent"))
    if e1_eq and e2_eq:
        return "preserved" if row.get("hill_form") else "structural_false_negative"
    return "unknown"


def _classify_five_e1_only(row: dict[str, Any]) -> str:
    """B2 partition (§2.5.2, F7): decided from E1-stage fields only, never from B0 E2 flags."""
    if row.get("construction_incomplete"):
        return "construction_incomplete"
    if (
        row.get("execution_failure")
        or row.get("q4_construction_completed") is False
        or row.get("rescale_incomplete")
        or row.get("classifier_parse_valid") is False
        or row.get("e1_oracle_completed") is False
    ):
        return "execution_failure"
    if not row.get("e1_oracle_equivalent"):
        return "semantic_drift"
    return "preserved" if row.get("hill_form") else "structural_false_negative"


def classify_five_outcome(row: dict[str, Any]) -> str:
    if str(row.get("condition")) == "B2":
        return _classify_five_e1_only(row)
    return _classify_five_whole_chain(row)


def descriptive_terminal(five_outcome: str) -> str:
    if five_outcome in DESCRIPTIVE_RECORDED_SOURCE_OUTCOMES:
        return "descriptive_recorded"
    return "descriptive_failed"


def classify_outcome(row: dict[str, Any]) -> str:
    condition = str(row.get("condition")) if row.get("condition") is not None else None
    if condition == "B1":
        return "control_pass" if row.get("control_pass_row") else "control_failure"
    five = classify_five_outcome(row)
    if condition == "D2":
        return descriptive_terminal(five)
    return five


def is_fully_diagnostic(outcome_category: str) -> bool:
    return outcome_category in {"preserved", "structural_false_negative"}


def assert_terminal_vocabulary(
    rows: list[dict[str, Any]],
    *,
    partition_scope: str | None = None,
    terminal_key: str = "outcome_category",
    context: str = "pair_results",
) -> None:
    """Whole-artifact invariant: every terminal is legal for its scope and never `unknown`."""
    from gpu_runmultiai.invariants import TerminalVocabularyError

    for index, row in enumerate(rows):
        scope = partition_scope or row.get("partition_scope")
        allowed = TERMINAL_VOCABULARY.get(str(scope))
        if allowed is None:
            raise TerminalVocabularyError(
                f"{context}[{index}]: unknown partition_scope {scope!r}"
            )
        terminal = row.get(terminal_key)
        if terminal not in allowed:
            raise TerminalVocabularyError(
                f"{context}[{index}] scope={scope}: illegal terminal {terminal!r}; "
                f"allowed {sorted(allowed)}"
            )


def build_outcome_row(**flags: Any) -> dict[str, Any]:
    row = dict(flags)
    stratum = row.pop("stratum", None)
    if "eligibility_layer" not in row and stratum is not None:
        row["eligibility_layer"] = eligibility_layer_for_stratum(stratum)
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
    five = classify_five_outcome(row)
    category = classify_outcome(row)
    if row.get("condition") == "D2":
        row["descriptive_source_outcome"] = five
    row["outcome_category"] = category
    row["is_fully_diagnostic"] = is_fully_diagnostic(five)
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


def partition_absolute_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts = {name: 0 for name in FIVE_OUTCOME_CATEGORIES}
    counts["unknown"] = 0
    for row in rows:
        category = str(row.get("outcome_category", "unknown"))
        if category in counts:
            counts[category] += 1
        else:
            counts["unknown"] += 1
    return counts


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
