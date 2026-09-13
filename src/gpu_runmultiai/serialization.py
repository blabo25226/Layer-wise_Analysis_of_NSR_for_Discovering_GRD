"""JSON-safe serialization helpers for stage-cache payloads."""

from __future__ import annotations

from typing import Any

from gpu_runmultiai.odeformer_runtime import tree_to_prefix_list, tree_to_system_infix


def json_safe_stage_payload(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, dict):
        return {str(key): json_safe_stage_payload(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe_stage_payload(item) for item in value]
    if hasattr(value, "prefix"):
        prefixes = tree_to_prefix_list(value)
        return {
            "kind": "odeformer_tree",
            "prefixes": prefixes,
            "prefix_raw": "|".join(prefixes),
            "infix": tree_to_system_infix(value),
        }
    raise TypeError(f"unsupported stage-cache payload type: {type(value)!r}")
