"""Stable, problem-scoped seed derivation for paired GPU_RUN5 decoding."""

from __future__ import annotations

import hashlib
import json
from typing import Any


def stable_problem_seed(
    base_seed: int,
    *,
    system_id: str,
    condition: str,
    noise_sigma: float,
    subsample_rho: float,
    sampling_replicate: int = 0,
) -> int:
    """Derive a deterministic PyTorch seed without Python's randomized hash()."""
    identity: dict[str, Any] = {
        "system_id": str(system_id),
        "condition": str(condition),
        "noise_sigma": float(noise_sigma),
        "subsample_rho": float(subsample_rho),
        "sampling_replicate": int(sampling_replicate),
    }
    digest = hashlib.sha256(json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()).digest()
    offset = int.from_bytes(digest[:8], byteorder="big", signed=False)
    return int((int(base_seed) + offset) % (2**31 - 1))
