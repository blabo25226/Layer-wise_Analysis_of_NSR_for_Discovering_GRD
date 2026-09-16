"""Counted-call logging and primitive table."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from gpu_runmultiai.constants import CONFIRMATORY_CALL_CEILING, FULL_RUN_CALL_CEILING
from gpu_runmultiai.invariants import AuditInvariantError
from gpu_runmultiai.jsonl_durable import append_jsonl_line, load_jsonl, truncate_partial_suffix

DESCRIPTIVE_CONDITIONS = frozenset({"D2"})

PRIMITIVE_TABLE: list[dict[str, Any]] = [
    {"id": "P1", "primitive": "truth_register_classify", "condition": "registration", "units": 510},
    {"id": "P2", "primitive": "rewrite_oracle_precheck", "condition": "registration", "units": 510},
    {"id": "P12", "primitive": "quantization_stratum_assign", "condition": "registration", "units": 510},
    {"id": "P3", "primitive": "e0_analytic_construct", "condition": "B0", "units": 2040},
    {"id": "P5", "primitive": "scaler_rescale_function", "condition": "B0", "units": 2040},
    {"id": "P11", "primitive": "q4_decimal_round_reference", "condition": "B0", "units": 2040},
    {"id": "P6", "primitive": "simplifier_subprocess", "condition": "B0", "units": 2040},
    {"id": "P7", "primitive": "oracle_equivalence", "condition": "B0_E2", "units": 2040},
    {"id": "P7", "primitive": "oracle_equivalence", "condition": "B0_E1", "units": 2040},
    {"id": "P8", "primitive": "classify_component_flags", "condition": "B0", "units": 2040},
    {"id": "P9", "primitive": "formula_metrics_pair", "condition": "B0", "units": 2040},
    {"id": "P4", "primitive": "e0_identity_construct", "condition": "B1", "units": 510},
    {"id": "P5", "primitive": "scaler_rescale_function", "condition": "B1", "units": 510},
    {"id": "P11", "primitive": "q4_decimal_round_reference", "condition": "B1", "units": 510},
    {"id": "P6", "primitive": "simplifier_subprocess", "condition": "B1", "units": 510},
    {"id": "P7", "primitive": "oracle_equivalence", "condition": "B1_E2", "units": 510},
    {"id": "P7", "primitive": "oracle_equivalence", "condition": "B1_E1", "units": 510},
    {"id": "P8", "primitive": "classify_component_flags", "condition": "B1", "units": 510},
    {"id": "P9", "primitive": "formula_metrics_pair", "condition": "B1", "units": 510},
    {"id": "P8", "primitive": "classify_component_flags", "condition": "B2", "units": 2040},
    {"id": "P9", "primitive": "formula_metrics_pair", "condition": "B2", "units": 2040},
    {"id": "P8", "primitive": "classify_component_flags", "condition": "B4", "units": 510},
    {"id": "P9", "primitive": "formula_metrics_pair", "condition": "B4", "units": 510},
    {"id": "P11", "primitive": "q4_decimal_round_reference", "condition": "C_q4", "units": 7},
    {"id": "P10", "primitive": "compare_formulas_cas", "condition": "B3", "units": 500},
    {"id": "P7", "primitive": "oracle_equivalence", "condition": "N1", "units": 100},
]


def expected_confirmatory_calls() -> int:
    return sum(int(row["units"]) for row in PRIMITIVE_TABLE)


def expected_descriptive_calls() -> int:
    return FULL_RUN_CALL_CEILING - CONFIRMATORY_CALL_CEILING


@dataclass(frozen=True)
class CallKey:
    primitive: str
    condition: str
    stage: str
    unit_type: str
    unit_id: str

    def as_tuple(self) -> tuple[str, str, str, str, str]:
        return (self.primitive, self.condition, self.stage, self.unit_type, self.unit_id)


class CallLogger:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path
        self.rows: list[dict[str, Any]] = []
        self._keys: set[tuple[str, str, str, str, str]] = set()
        self.skip_duplicates: bool = False
        if path is not None and path.is_file():
            truncate_partial_suffix(path)

    @classmethod
    def load(cls, path: Path) -> "CallLogger":
        logger = cls(path)
        loaded = load_jsonl(
            path,
            key_fn=lambda row: (
                row["primitive"],
                row["condition"],
                row["stage"],
                row["unit_type"],
                row["unit_id"],
            ),
        )
        for row in loaded:
            key = CallKey(
                row["primitive"],
                row["condition"],
                row["stage"],
                row["unit_type"],
                row["unit_id"],
            ).as_tuple()
            logger._keys.add(key)
            logger.rows.append(row)
        return logger

    def is_recorded(
        self,
        *,
        primitive: str,
        condition: str,
        stage: str,
        unit_type: str,
        unit_id: str,
    ) -> bool:
        key = CallKey(primitive, condition, stage, unit_type, unit_id).as_tuple()
        return key in self._keys

    def assert_pre_call_ceiling(self, condition: str) -> None:
        if condition in DESCRIPTIVE_CONDITIONS:
            if self.descriptive_total() >= expected_descriptive_calls():
                raise AuditInvariantError("G1 FAIL: descriptive call ceiling reached before execution")
            if self.total() >= FULL_RUN_CALL_CEILING:
                raise AuditInvariantError("G1 FAIL: full-run call ceiling reached before execution")
        else:
            if self.confirmatory_total() >= CONFIRMATORY_CALL_CEILING:
                raise AuditInvariantError("G1 FAIL: confirmatory call ceiling reached before execution")

    def execute_or_record(
        self,
        *,
        primitive: str,
        condition: str,
        stage: str,
        unit_type: str,
        unit_id: str,
        status: str = "completed",
        duration_sec: float | None = None,
        rewrite_id: str | None = None,
        executor: Callable[[], Any] | None = None,
        status_for_result: Callable[[Any], str] | None = None,
        rewrite_id_for_result: Callable[[Any], str | None] | None = None,
    ) -> tuple[bool, Any]:
        if self.is_recorded(
            primitive=primitive,
            condition=condition,
            stage=stage,
            unit_type=unit_type,
            unit_id=unit_id,
        ):
            return False, None
        self.assert_pre_call_ceiling(condition)
        started = time.perf_counter()
        result = None
        resolved_status = status
        resolved_rewrite_id = rewrite_id
        should_record = True
        try:
            if executor is not None:
                result = executor()
            resolved_status = status_for_result(result) if status_for_result is not None else status
            resolved_rewrite_id = (
                rewrite_id_for_result(result) if rewrite_id_for_result is not None else rewrite_id
            )
        except AuditInvariantError:
            should_record = False
            raise
        except Exception:
            resolved_status = "failed"
            raise
        finally:
            if should_record:
                measured = duration_sec
                if measured is None:
                    measured = time.perf_counter() - started
                self.record(
                    primitive=primitive,
                    condition=condition,
                    stage=stage,
                    unit_type=unit_type,
                    unit_id=unit_id,
                    status=resolved_status,
                    duration_sec=measured,
                    rewrite_id=resolved_rewrite_id,
                )
        return True, result

    def record(
        self,
        *,
        primitive: str,
        condition: str,
        stage: str,
        unit_type: str,
        unit_id: str,
        status: str,
        duration_sec: float | None = None,
        rewrite_id: str | None = None,
    ) -> None:
        key = CallKey(primitive, condition, stage, unit_type, unit_id).as_tuple()
        if key in self._keys:
            if self.skip_duplicates:
                return
            raise AuditInvariantError(f"duplicate counted call: {key}")
        self._keys.add(key)
        row = {
            "primitive": primitive,
            "condition": condition,
            "stage": stage,
            "unit_type": unit_type,
            "unit_id": unit_id,
            "status": status,
            "duration_sec": duration_sec,
        }
        if rewrite_id is not None:
            row["rewrite_id"] = rewrite_id
        self.rows.append(row)
        if self.path is not None:
            append_jsonl_line(self.path, row)

    def confirmatory_total(self) -> int:
        return sum(1 for row in self.rows if row["condition"] not in DESCRIPTIVE_CONDITIONS)

    def descriptive_total(self) -> int:
        return sum(1 for row in self.rows if row["condition"] in DESCRIPTIVE_CONDITIONS)

    def total(self) -> int:
        return len(self.rows)

    def assert_ceiling(self, *, run_d2: bool = False) -> None:
        confirmatory = self.confirmatory_total()
        if confirmatory > CONFIRMATORY_CALL_CEILING:
            raise AuditInvariantError(
                f"G1 FAIL: confirmatory calls {confirmatory} exceed ceiling {CONFIRMATORY_CALL_CEILING}"
            )
        if run_d2:
            full_total = self.total()
            if full_total > FULL_RUN_CALL_CEILING:
                raise AuditInvariantError(
                    f"G1 FAIL: full-run calls {full_total} exceed ceiling {FULL_RUN_CALL_CEILING}"
                )
