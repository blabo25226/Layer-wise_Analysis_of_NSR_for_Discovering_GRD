"""Canonical ID serialization for C0001 audit (v9 pipe contract)."""

from __future__ import annotations

import hashlib
from typing import Iterable

from gpu_runmultiai.constants import (
    AUDIT_NEGATIVE_SEED,
    AUDIT_REWRITE_SEED,
    N1_COEFFS,
    PRIMES,
)

PIPE = "|"


def sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def pipe_count(text: str) -> int:
    return text.count(PIPE)


def backslash_count(text: str) -> int:
    return text.count("\\")


def rewrite_canonical_key(system_id: str, component_idx: int) -> str:
    return f"audit_rewrite_seed={AUDIT_REWRITE_SEED}{PIPE}system_id={system_id}{PIPE}component_idx={component_idx}"


def negative_canonical_key(system_id: str, component_idx: int) -> str:
    return f"audit_negative_seed={AUDIT_NEGATIVE_SEED}{PIPE}system_id={system_id}{PIPE}component_idx={component_idx}"


def component_key(corpus_hash: str, system_id: str, component_idx: int) -> str:
    return f"corpus_hash={corpus_hash}{PIPE}system_id={system_id}{PIPE}component_idx={component_idx}"


def pair_key(
    corpus_hash: str,
    system_id: str,
    component_idx: int,
    scale: str,
    rewrite_id: str,
) -> str:
    return (
        f"corpus_hash={corpus_hash}{PIPE}system_id={system_id}{PIPE}component_idx={component_idx}"
        f"{PIPE}scale={scale}{PIPE}rewrite_id={rewrite_id}"
    )


def digest_select(collection: Iterable[int], digest_hex: str) -> int:
    return collection[int.from_bytes(bytes.fromhex(digest_hex)[:8], "big") % len(collection)]


def rewrite_id_for(system_id: str, component_idx: int) -> tuple[str, int, str]:
    key = rewrite_canonical_key(system_id, component_idx)
    digest = sha256_hex(key)
    selected_r = digest_select(PRIMES, digest)
    return f"rewrite_sha256:{digest}", selected_r, key


def negative_id_for(system_id: str, component_idx: int) -> tuple[str, int, str]:
    key = negative_canonical_key(system_id, component_idx)
    digest = sha256_hex(key)
    selected_c = digest_select(N1_COEFFS, digest)
    return f"negative_sha256:{digest}", selected_c, key


def component_id_for(corpus_hash: str, system_id: str, component_idx: int) -> tuple[str, str]:
    key = component_key(corpus_hash, system_id, component_idx)
    return f"component_sha256:{sha256_hex(key)}", key


def pair_id_for(
    corpus_hash: str,
    system_id: str,
    component_idx: int,
    scale: str,
    rewrite_id: str,
) -> tuple[str, str]:
    key = pair_key(corpus_hash, system_id, component_idx, scale, rewrite_id)
    return f"pair_sha256:{sha256_hex(key)}", key


# Frozen representative fixtures (preregistration v9 §3.2, §4.3, §7).
FIXTURE_SYSTEM_ID = "R01_train_d61001_000"
FIXTURE_COMPONENT_IDX = 0
FIXTURE_ZERO_CORPUS = "0" * 64

REWRITE_FIXTURE = {
    "canonical_key_string": rewrite_canonical_key(FIXTURE_SYSTEM_ID, FIXTURE_COMPONENT_IDX),
    "pipe_count": 2,
    "backslash_count": 0,
    "sha256": "91a3f6eb6ae668bbefd4a9d9cfc0242032549f5e9346450e932c09129bdf4d90",
    "selected_r": 3,
    "rewrite_id": "rewrite_sha256:91a3f6eb6ae668bbefd4a9d9cfc0242032549f5e9346450e932c09129bdf4d90",
}

NEGATIVE_FIXTURE = {
    "canonical_key_string": negative_canonical_key(FIXTURE_SYSTEM_ID, FIXTURE_COMPONENT_IDX),
    "pipe_count": 2,
    "backslash_count": 0,
    "sha256": "ce6d15ac5f359552092e79614df18a4f743cead7cdf6454fefd79d3455888bc8",
    "selected_c": 3,
    "negative_id": "negative_sha256:ce6d15ac5f359552092e79614df18a4f743cead7cdf6454fefd79d3455888bc8",
}

COMPONENT_FIXTURE = {
    "corpus_hash": FIXTURE_ZERO_CORPUS,
    "system_id": FIXTURE_SYSTEM_ID,
    "component_idx": FIXTURE_COMPONENT_IDX,
    "component_key": component_key(FIXTURE_ZERO_CORPUS, FIXTURE_SYSTEM_ID, FIXTURE_COMPONENT_IDX),
    "pipe_count": 2,
    "backslash_count": 0,
    "component_id_digest": "2eadb0ad33ac644db3f2d1f43fe1b88883e26cd07430a5a2708cf8417e476231",
    "component_id": "component_sha256:2eadb0ad33ac644db3f2d1f43fe1b88883e26cd07430a5a2708cf8417e476231",
}

PAIR_FIXTURE = {
    "corpus_hash": FIXTURE_ZERO_CORPUS,
    "system_id": FIXTURE_SYSTEM_ID,
    "component_idx": FIXTURE_COMPONENT_IDX,
    "scale": "0.1",
    "rewrite_id": REWRITE_FIXTURE["rewrite_id"],
    "pair_key": pair_key(
        FIXTURE_ZERO_CORPUS,
        FIXTURE_SYSTEM_ID,
        FIXTURE_COMPONENT_IDX,
        "0.1",
        REWRITE_FIXTURE["rewrite_id"],
    ),
    "pipe_count": 4,
    "backslash_count": 0,
    "pair_id_digest": "2c5158b45bf63b67f87824ff7dceb338a5eff06f147d0406947da56932a5048c",
    "pair_id": "pair_sha256:2c5158b45bf63b67f87824ff7dceb338a5eff06f147d0406947da56932a5048c",
}
