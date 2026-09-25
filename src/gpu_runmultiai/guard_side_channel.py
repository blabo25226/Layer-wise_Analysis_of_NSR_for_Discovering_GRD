"""Durable child-process sealed-path guard attempt side channel."""

from __future__ import annotations

import os
import stat as stat_module
from pathlib import Path

from experiment_runtime import REPO_ROOT
from gpu_runmultiai.invariants import AuditInvariantError, GateAbortError
from gpu_runmultiai.jsonl_durable import append_jsonl_line, load_jsonl

SIDE_CHANNEL_NAME = "guard_attempts_side_channel.jsonl"
REACHABILITY_AUXILIARY_SIDE_CHANNEL_NAME = "reachability_auxiliary_guard_side_channel.jsonl"
GUARD_ATTEMPT_FIELDS = ("attempted_operation", "attempted_path_norm", "attempted_path_real")


def side_channel_path(output_dir: Path) -> Path:
    return output_dir / SIDE_CHANNEL_NAME


def reachability_auxiliary_side_channel_path(output_dir: Path) -> Path:
    """Durable sealed-path attempts from §3.8 live ident-fallback probe (excluded from G4 ledger)."""
    return output_dir / REACHABILITY_AUXILIARY_SIDE_CHANNEL_NAME


def ensure_guard_side_channel(path: Path) -> None:
    """Create an empty durable side channel when zero attempts occur (§11, §12.1)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_file():
        return
    with path.open("wb") as handle:
        handle.flush()
        os.fsync(handle.fileno())


def append_guard_attempts(path: Path, attempts: list[dict[str, str]]) -> None:
    """Append §11 attempt rows; each line is flushed and fsynced unconditionally (§12.5)."""
    ensure_guard_side_channel(path)
    for row in attempts:
        append_jsonl_line(path, {field: str(row[field]) for field in GUARD_ATTEMPT_FIELDS})


def load_guard_attempts(path: Path) -> list[dict[str, str]]:
    """Load the durable side channel; malformed complete lines abort (§12.5)."""
    rows: list[dict[str, str]] = []
    for index, payload in enumerate(load_jsonl(path)):
        if not isinstance(payload, dict):
            raise AuditInvariantError(
                f"malformed guard side-channel line {index + 1} in {path}: expected object, got {type(payload).__name__}"
            )
        missing = [field for field in GUARD_ATTEMPT_FIELDS if field not in payload]
        if missing:
            raise AuditInvariantError(
                f"malformed guard side-channel line {index + 1} in {path}: missing {missing}"
            )
        rows.append({field: str(payload[field]) for field in GUARD_ATTEMPT_FIELDS})
    return rows


def child_side_channel_path() -> Path:
    return REPO_ROOT / "GPU_RUNmultiAI" / ".runtime" / SIDE_CHANNEL_NAME


def _side_channel_stat(path: Path):
    try:
        return path.stat()
    except FileNotFoundError:
        return None
    except OSError as exc:
        raise GateAbortError(
            f"child guard side channel stat failed at {path}: {exc}"
        ) from exc


def _require_regular_side_channel_file(path: Path, st: os.stat_result) -> None:
    if not stat_module.S_ISREG(st.st_mode):
        raise GateAbortError(
            f"child guard side channel path is not a regular file at {path}"
        )


def remove_side_channel_file(path: Path) -> None:
    """Remove a durable side-channel file using stat-only guards (Python 3.10 safe)."""
    st = _side_channel_stat(path)
    if st is None:
        return
    _require_regular_side_channel_file(path, st)
    try:
        path.unlink()
    except OSError as exc:
        raise GateAbortError(
            f"child guard side channel unlink failed at {path}: {exc}"
        ) from exc


def load_durable_side_channel_attempts(path: Path) -> list[dict[str, str]]:
    """Load attempt rows; absent path returns []. Stat/read/malformed paths fail closed."""
    st = _side_channel_stat(path)
    if st is None:
        return []
    _require_regular_side_channel_file(path, st)
    try:
        return load_guard_attempts(path)
    except AuditInvariantError as exc:
        raise GateAbortError(
            f"malformed child guard side channel at {path}"
        ) from exc
    except OSError as exc:
        raise GateAbortError(
            f"child guard side channel read failed at {path}: {exc}"
        ) from exc
