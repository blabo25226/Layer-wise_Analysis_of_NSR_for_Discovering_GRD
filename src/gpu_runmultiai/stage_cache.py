"""Resume caches keyed by counted-call identity."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from gpu_runmultiai.jsonl_durable import append_jsonl_line, load_jsonl, truncate_partial_suffix


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
    rows = load_jsonl(path, key_fn=lambda row: (row.get("cache_key"),))
    for row in rows:
        key = row.get("cache_key")
        if key:
            cache[key] = row.get("payload")
    return cache


def append_stage_cache(path: Path, *, cache_key_value: str, payload: Any) -> None:
    try:
        encoded_payload = payload
        json.dumps({"cache_key": cache_key_value, "payload": encoded_payload}, sort_keys=True)
    except (TypeError, ValueError) as exc:
        from gpu_runmultiai.invariants import StageCacheSerializationError

        raise StageCacheSerializationError(
            f"stage cache payload is not JSON-serializable for {cache_key_value}: {exc}"
        ) from exc
    append_jsonl_line(path, {"cache_key": cache_key_value, "payload": payload})
