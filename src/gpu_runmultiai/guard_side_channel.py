"""Durable child-process sealed-path guard attempt side channel."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from experiment_runtime import REPO_ROOT

SIDE_CHANNEL_NAME = "guard_attempts_side_channel.jsonl"


def side_channel_path(output_dir: Path) -> Path:
    return output_dir / SIDE_CHANNEL_NAME


def append_guard_attempts(path: Path, attempts: list[dict[str, str]]) -> None:
    if not attempts:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        for row in attempts:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def load_guard_attempts(path: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    if not path.is_file():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        payload = json.loads(line)
        rows.append(
            {
                "attempted_operation": str(payload["attempted_operation"]),
                "attempted_path_norm": str(payload["attempted_path_norm"]),
                "attempted_path_real": str(payload["attempted_path_real"]),
            }
        )
    return rows


def child_side_channel_path() -> Path:
    return REPO_ROOT / "GPU_RUNmultiAI" / ".runtime" / SIDE_CHANNEL_NAME
