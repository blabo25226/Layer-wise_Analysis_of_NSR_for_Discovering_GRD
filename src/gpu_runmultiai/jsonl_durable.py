"""Durable JSONL helpers (preregistration v16 §12.5)."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Callable

from gpu_runmultiai.invariants import AuditInvariantError


def append_jsonl_line(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def truncate_partial_suffix(path: Path) -> None:
    if not path.is_file():
        return
    data = path.read_bytes()
    if not data or data.endswith(b"\n"):
        return
    last_newline = data.rfind(b"\n")
    if last_newline < 0:
        truncated = b""
    else:
        truncated = data[: last_newline + 1]
    with path.open("wb") as handle:
        handle.write(truncated)
        handle.flush()
        os.fsync(handle.fileno())


def load_jsonl(path: Path, *, key_fn: Callable[[dict[str, Any]], tuple[Any, ...]] | None = None) -> list[dict[str, Any]]:
    truncate_partial_suffix(path)
    rows: list[dict[str, Any]] = []
    seen: set[tuple[Any, ...]] = set()
    if not path.is_file():
        return rows
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise AuditInvariantError(f"malformed JSONL line {line_number} in {path}: {exc}") from exc
        if key_fn is not None:
            key = key_fn(row)
            if key in seen:
                raise AuditInvariantError(f"duplicate JSONL key {key} in {path}")
            seen.add(key)
        rows.append(row)
    return rows
