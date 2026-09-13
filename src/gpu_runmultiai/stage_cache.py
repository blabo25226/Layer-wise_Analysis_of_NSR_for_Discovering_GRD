"""Resume caches keyed by counted-call identity."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def cache_key(
    *,
    primitive: str,
    condition: str,
    stage: str,
    unit_type: str,
    unit_id: str,
) -> str:
    return "|".join((primitive, condition, stage, unit_type, unit_id))


def load_stage_cache(path: Path) -> dict[str, Any]:
    cache: dict[str, Any] = {}
    if not path.is_file():
        return cache
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        key = row.get("cache_key")
        if key:
            cache[key] = row.get("payload")
    return cache


def append_stage_cache(path: Path, *, cache_key_value: str, payload: Any) -> None:
    try:
        encoded = json.dumps({"cache_key": cache_key_value, "payload": payload}, sort_keys=True)
    except (TypeError, ValueError):
        return
    with path.open("a", encoding="utf-8") as handle:
        handle.write(encoded + "\n")
