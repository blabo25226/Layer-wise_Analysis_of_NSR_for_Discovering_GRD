"""Counted-call logging and primitive table."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from gpu_runmultiai.constants import CONFIRMATORY_CALL_CEILING, FULL_RUN_CALL_CEILING

PRIMITIVE_TABLE: list[dict[str, Any]] = [
    {"id": "P1", "primitive": "truth_register_classify", "condition": "registration", "units": 510},
    {"id": "P2", "primitive": "rewrite_oracle_precheck", "condition": "registration", "units": 510},
    {"id": "P3", "primitive": "e0_analytic_construct", "condition": "B0", "units": 2040},
    {"id": "P5", "primitive": "scaler_rescale_function", "condition": "B0", "units": 2040},
    {"id": "P6", "primitive": "simplifier_subprocess", "condition": "B0", "units": 2040},
    {"id": "P7", "primitive": "oracle_equivalence", "condition": "B0_E2", "units": 2040},
    {"id": "P7", "primitive": "oracle_equivalence", "condition": "B0_E1", "units": 2040},
    {"id": "P8", "primitive": "classify_component_flags", "condition": "B0", "units": 2040},
    {"id": "P9", "primitive": "formula_metrics_pair", "condition": "B0", "units": 2040},
    {"id": "P4", "primitive": "e0_identity_construct", "condition": "B1", "units": 510},
    {"id": "P5", "primitive": "scaler_rescale_function", "condition": "B1", "units": 510},
    {"id": "P6", "primitive": "simplifier_subprocess", "condition": "B1", "units": 510},
    {"id": "P8", "primitive": "classify_component_flags", "condition": "B1", "units": 510},
    {"id": "P9", "primitive": "formula_metrics_pair", "condition": "B1", "units": 510},
    {"id": "P8", "primitive": "classify_component_flags", "condition": "B2", "units": 2040},
    {"id": "P9", "primitive": "formula_metrics_pair", "condition": "B2", "units": 2040},
    {"id": "P8", "primitive": "classify_component_flags", "condition": "B4", "units": 510},
    {"id": "P9", "primitive": "formula_metrics_pair", "condition": "B4", "units": 510},
    {"id": "P10", "primitive": "compare_formulas_cas", "condition": "B3", "units": 500},
    {"id": "P7", "primitive": "oracle_equivalence", "condition": "N1", "units": 100},
]


def expected_confirmatory_calls() -> int:
    return sum(int(row["units"]) for row in PRIMITIVE_TABLE)


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

    @classmethod
    def load(cls, path: Path) -> "CallLogger":
        logger = cls(path)
        if not path.is_file():
            return logger
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            key = CallKey(
                row["primitive"],
                row["condition"],
                row["stage"],
                row["unit_type"],
                row["unit_id"],
            ).as_tuple()
            if key in logger._keys:
                raise RuntimeError(f"duplicate counted call in call_log: {key}")
            logger._keys.add(key)
            logger.rows.append(row)
        return logger

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
            raise RuntimeError(f"duplicate counted call: {key}")
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
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(row, sort_keys=True) + "\n")

    def total(self) -> int:
        return len(self.rows)

    def assert_ceiling(self, *, descriptive: bool = False) -> None:
        ceiling = FULL_RUN_CALL_CEILING if descriptive else CONFIRMATORY_CALL_CEILING
        total = self.total()
        if total > ceiling:
            raise RuntimeError(f"G1 FAIL: counted calls {total} exceed ceiling {ceiling}")
