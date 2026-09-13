"""Validity gates and control summaries."""

from __future__ import annotations

from typing import Any

from gpu_runmultiai.outcomes import partition_counts


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


def gate_n1(rows: list[dict[str, Any]]) -> bool:
    return len(rows) == 100 and all(
        row["oracle"]["completed"] and not row["oracle"]["equivalent"] for row in rows
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


def evaluate_validity_gates(state: dict[str, Any]) -> dict[str, bool]:
    return {
        "G_corpus": bool(state.get("g_corpus_pass")),
        "G0": gate_g0(state.get("scaler_asserts", {})),
        "G4": gate_g4(int(state.get("access_attempts", 0))),
        "G1": gate_g1(int(state.get("total_calls", 0)), int(state.get("call_ceiling", 0))),
        "G_n1": gate_n1(state.get("negative_controls", [])),
        "G_b4": gate_b4(state.get("b4_rows", [])),
        "G_ctrl_cov": gate_ctrl_cov(state.get("linear_rows", [])),
        "G_ctrl_fp": gate_ctrl_fp(state.get("linear_rows", [])),
        "G_ctrl_lin": gate_ctrl_lin(state.get("linear_rows", [])),
        "G_term": gate_term(state.get("strict_rows", [])),
        "G_inc": gate_inc(state.get("strict_rows", [])),
    }


def any_gate_failed(gates: dict[str, bool]) -> bool:
    return not all(gates.values())


def condition_summary(strict_rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "denominator": 1320,
        "partition_rates": partition_counts(strict_rows, 1320),
        "diagnostic_coverage_rate": sum(1 for row in strict_rows if row.get("is_fully_diagnostic")) / 1320,
        "terminal_coverage_rate": sum(
            1 for row in strict_rows if row.get("outcome_category") != "unknown"
        ) / 1320,
    }
