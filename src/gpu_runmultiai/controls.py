"""Validity gates and control summaries."""

from __future__ import annotations

from typing import Any

from gpu_runmultiai.outcomes import partition_counts

GATE_ORDER: tuple[str, ...] = (
    "G_corpus",
    "G_eligibility",
    "G_stratum",
    "G0",
    "G4",
    "G1",
    "G_grand",
    "G_contract",
    "G_impl",
    "G_q4ref",
    "G_n1",
    "G_b1",
    "G_b4",
    "G_ctrl_cov",
    "G_ctrl_fp",
    "G_ctrl_lin",
    "G_term",
    "G_inc",
)

ABORT_GATES: frozenset[str] = frozenset(
    {"G_corpus", "G_eligibility", "G_stratum", "G0", "G1", "G_grand"}
)


def gate_g0(scaler_asserts: dict[str, Any]) -> bool:
    expected = {
        "time_scale": 9,
        "time_shift": 1,
        "a_t": 0.9,
        "b_t": 1.0,
        "rescale_features": True,
    }
    return all(scaler_asserts.get(key) == value for key, value in expected.items())


def gate_g4(access_attempts: int) -> bool:
    return access_attempts == 0


def gate_g1(total_calls: int, ceiling: int) -> bool:
    return total_calls <= ceiling


def gate_g_grand(grand_calls: int, ceiling: int) -> bool:
    return grand_calls <= ceiling


def gate_g_eligibility(eligibility_counts: dict[str, int] | None) -> bool:
    if not eligibility_counts:
        return False
    return (
        eligibility_counts.get("strict_hill") == 330
        and eligibility_counts.get("non_strict_hill") == 60
        and eligibility_counts.get("linear") == 120
        and eligibility_counts.get("other", 0) == 0
    )


def gate_g_stratum(quantization_rows: list[dict[str, Any]] | None) -> bool:
    if not quantization_rows:
        return False
    strict_rows = [
        row
        for row in quantization_rows
        if row.get("eligibility_layer") in (None, "strict_hill_primary")
    ]
    active = sum(1 for row in strict_rows if row.get("quantization_stratum") == "quantization_active")
    neutral = sum(1 for row in strict_rows if row.get("quantization_stratum") == "quantization_neutral")
    return active == 46 and neutral == 284 and len(strict_rows) == 330


def gate_g_contract(state: dict[str, Any]) -> bool:
    evidence = state.get("g_contract_evidence", {})
    required = (
        "q4_fixtures",
        "guard_bootstrap",
        "source_inventory",
        "artifact_schemas",
        "jsonl_recovery",
        "resume_mismatch",
        "abort_deviation_lifecycle",
    )
    return all(evidence.get(key) for key in required)


def gate_g_impl(state: dict[str, Any]) -> bool:
    reachability = state.get("reachability_evidence", [])
    if not reachability or len(reachability) != 10:
        return False
    if not all(row.get("passed") for row in reachability):
        return False
    acceptance = state.get("f_acceptance", {})
    for key in ("F1", "F2", "F4", "F5", "F6", "F7", "F8"):
        if not acceptance.get(key):
            return False
    return True


def gate_n1(rows: list[dict[str, Any]]) -> bool:
    return len(rows) == 100 and all(
        row.get("oracle_completed") and not row.get("oracle_equivalent") for row in rows
    )


def gate_b4(rows: list[dict[str, Any]]) -> bool:
    return len(rows) == 510 and all(row.get("valid") and row.get("canonical_exact") == 1 for row in rows)


def gate_ctrl_cov(rows: list[dict[str, Any]]) -> bool:
    return len(rows) == 480 and all(row.get("classifier_parse_valid") and row.get("formula_metrics_valid") for row in rows)


def gate_ctrl_fp(rows: list[dict[str, Any]]) -> bool:
    return len(rows) == 480 and all(not row.get("hill_form") for row in rows)


def gate_ctrl_lin(rows: list[dict[str, Any]]) -> bool:
    return len(rows) == 480 and all(row.get("canonical_exact") == 1 for row in rows)


def gate_term(strict_rows: list[dict[str, Any]]) -> bool:
    pair_ids = [row["pair_id"] for row in strict_rows]
    return len(pair_ids) == 1320 and len(set(pair_ids)) == 1320 and all(
        row.get("outcome_category") != "unknown" for row in strict_rows
    )


def gate_inc(strict_rows: list[dict[str, Any]], max_rate: float = 0.05) -> bool:
    incomplete = sum(1 for row in strict_rows if row.get("outcome_category") == "construction_incomplete")
    return incomplete / 1320 <= max_rate


def gate_b1(rows: list[dict[str, Any]]) -> bool:
    return (
        len(rows) == 510
        and all(row.get("control_pass_row") for row in rows)
        and all(row.get("outcome_category") in {"control_pass", "control_failure"} for row in rows)
        and not any(row.get("outcome_category") == "unknown" for row in rows)
    )


def gate_q4ref(rows: list[dict[str, Any]]) -> bool:
    return len(rows) == 7 and all(row.get("fixture_pass") for row in rows)


def evaluate_validity_gates(state: dict[str, Any]) -> dict[str, bool]:
    gates = {
        "G_corpus": bool(state.get("g_corpus_pass")),
        "G_eligibility": gate_g_eligibility(state.get("eligibility_counts")),
        "G_stratum": gate_g_stratum(state.get("quantization_rows")),
        "G0": gate_g0(state.get("scaler_asserts", {})),
        "G4": gate_g4(int(state.get("access_attempts", 0))),
        "G1": gate_g1(int(state.get("total_calls", 0)), int(state.get("call_ceiling", 0))),
        "G_grand": gate_g_grand(int(state.get("grand_calls", 0)), int(state.get("grand_call_ceiling", 0))),
        "G_contract": gate_g_contract(state),
        "G_impl": gate_g_impl(state),
        "G_q4ref": gate_q4ref(state.get("c_q4_rows", [])),
        "G_n1": gate_n1(state.get("negative_controls", [])),
        "G_b1": gate_b1(state.get("b1_rows", [])),
        "G_b4": gate_b4(state.get("b4_rows", [])),
        "G_ctrl_cov": gate_ctrl_cov(state.get("linear_rows", [])),
        "G_ctrl_fp": gate_ctrl_fp(state.get("linear_rows", [])),
        "G_ctrl_lin": gate_ctrl_lin(state.get("linear_rows", [])),
        "G_term": gate_term(state.get("strict_rows", [])),
        "G_inc": gate_inc(state.get("strict_rows", [])),
    }
    return {name: gates[name] for name in GATE_ORDER}


def any_gate_failed(gates: dict[str, bool]) -> bool:
    return not all(gates.values())


def first_abort_gate(gates: dict[str, bool]) -> str | None:
    for name in GATE_ORDER:
        if name in ABORT_GATES and not gates.get(name):
            return name
    return None


def condition_summary(strict_rows: list[dict[str, Any]], *, gates: dict[str, bool] | None = None) -> dict[str, Any]:
    payload = {
        "denominator": 1320,
        "partition_rates": partition_counts(strict_rows, 1320),
        "diagnostic_coverage_rate": sum(1 for row in strict_rows if row.get("is_fully_diagnostic")) / 1320,
        "terminal_coverage_rate": sum(
            1 for row in strict_rows if row.get("outcome_category") != "unknown"
        ) / 1320,
    }
    if gates is not None:
        payload["validity_gates"] = gates
    return payload
