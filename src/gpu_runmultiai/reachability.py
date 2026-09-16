"""Reachability evidence builders for G_impl (preregistration v16 §3.8)."""

from __future__ import annotations

from typing import Any

from gpu_runmultiai.outcomes import evaluate_primary_decision
from gpu_runmultiai.q4_reference import C_Q4_FIXTURES, audit_q4_decimal_round_reference, evaluate_c_q4_fixture


def _reachability_row(fixture_id: str, evidence_type: str, passed: bool, details: str) -> dict[str, Any]:
    return {
        "fixture_id": fixture_id,
        "evidence_type": evidence_type,
        "passed": passed,
        "details": details,
    }


def build_reachability_evidence() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    pow_comp = audit_q4_decimal_round_reference("pow2,div,mul,10.0,x_0,10.0")
    rows.append(
        _reachability_row(
            "REACH-POW-COMP-1",
            "prefix_q4_construction",
            pow_comp.q4_construction_completed,
            pow_comp.q4_emitted_prefix or pow_comp.q4_construction_failure_reason or "",
        )
    )

    c_q4_rows = [evaluate_c_q4_fixture(fixture) for fixture in C_Q4_FIXTURES]
    rows.append(
        _reachability_row(
            "REACH-Q4-REF",
            "c_q4_fixtures",
            all(row["fixture_pass"] for row in c_q4_rows),
            f"{sum(1 for row in c_q4_rows if row['fixture_pass'])}/{len(c_q4_rows)} fixture_pass",
        )
    )

    unsupported_rows = [
        {
            "condition": "B0",
            "eligibility_layer": "strict_hill_primary",
            "pair_id": f"pair_sha256:{index:064x}",
            "outcome_category": "preserved",
            "is_fully_diagnostic": True,
        }
        for index in range(1320)
    ]
    unsupported_decision = evaluate_primary_decision(unsupported_rows, validity_gate_failed=False)
    rows.append(
        _reachability_row(
            "REACH-UNS-1",
            "primary_decision_grid",
            unsupported_decision == "H0001 unsupported",
            unsupported_decision,
        )
    )

    supported_rows = list(unsupported_rows)
    supported_rows[0] = {
        **supported_rows[0],
        "outcome_category": "structural_false_negative",
    }
    supported_decision = evaluate_primary_decision(supported_rows, validity_gate_failed=False)
    rows.append(
        _reachability_row(
            "REACH-SUP-1",
            "primary_decision_grid",
            supported_decision == "H0001 supported",
            supported_decision,
        )
    )

    return rows
