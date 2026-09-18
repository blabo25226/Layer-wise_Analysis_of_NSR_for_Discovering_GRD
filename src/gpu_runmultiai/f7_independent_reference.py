"""F7 independent frozen B2 oracle (preregistration v16 §16).

This module must not import production ``classify_formula`` or production outcome
helpers.  It provides the adversarial reference used to validate that production
B2 terminals are decided from B0 E1-only fields.
"""

from __future__ import annotations

from typing import Any


def frozen_hill_form_literal(e1_infix: str, component_idx: int) -> bool:
    """Literal Hill detector independent of production ``classify_formula``."""
    component = _extract_component_infix_literal(e1_infix, component_idx)
    normalized = component.replace(" ", "")
    if "**2/(1+" in normalized and "x_" in normalized:
        return True
    if normalized in {"(x_0)", "x_0"}:
        return False
    if "/(1+" in normalized and "**2" in normalized:
        return True
    return False


def _extract_component_infix_literal(infix: str, component_idx: int) -> str:
    """Minimal ``|`` split without importing production oracle helpers."""
    parts = [part.strip() for part in infix.split("|")]
    if component_idx < len(parts):
        return parts[component_idx]
    return infix


def classify_b2_outcome_frozen(row: dict[str, Any]) -> str:
    """Literal frozen B2 five-outcome decision table."""
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


def compute_b2_expected_outcome(
    *,
    e1_infix: str,
    component_idx: int,
    e1_fields: dict[str, Any],
    classifier_parse_valid: bool | None = None,
) -> str:
    """Derive the B2 terminal from B0 E1 inputs using the independent literal oracle."""
    synthetic = dict(e1_fields)
    synthetic.update(
        condition="B2",
        classifier_parse_valid=(
            classifier_parse_valid
            if classifier_parse_valid is not None
            else synthetic.get("classifier_parse_valid", True)
        ),
        hill_form=frozen_hill_form_literal(e1_infix, component_idx),
    )
    return classify_b2_outcome_frozen(synthetic)
