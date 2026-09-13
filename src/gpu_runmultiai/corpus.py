"""Frozen corpus generation and source-index contract."""

from __future__ import annotations

import json
from typing import Any

from gpu_run5.grn import FAMILIES, generate_corpus

from gpu_runmultiai.constants import (
    AUDIT_DATA_SEED,
    AUDIT_TRAJECTORY_SEED,
    EXPECTED_COMPONENTS,
    EXPECTED_TRAIN_SYSTEMS,
    MAX_REJECTION_RATE,
)
def frozen_generate_corpus() -> dict[str, Any]:
    return generate_corpus(
        variants={"train": 30},
        n_points=150,
        t_span=(0.0, 10.0),
        seed=AUDIT_DATA_SEED,
        trajectory_seed=AUDIT_TRAJECTORY_SEED,
        rtol=1e-8,
        atol=1e-10,
        minimum_variance=1e-5,
        maximum_abs_state=100.0,
    )


def fingerprint_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True).encode()


def validate_corpus(corpus: dict[str, Any]) -> dict[str, Any]:
    train_records = [row for row in corpus["records"] if row["split"] == "train"]
    if len(train_records) != EXPECTED_TRAIN_SYSTEMS:
        raise RuntimeError(
            f"G_corpus FAIL: expected {EXPECTED_TRAIN_SYSTEMS} train systems, got {len(train_records)}"
        )
    component_count = sum(len(row["teacher_prefix"].split("|")) for row in train_records)
    if component_count != EXPECTED_COMPONENTS:
        raise RuntimeError(
            f"G_corpus FAIL: expected {EXPECTED_COMPONENTS} components, got {component_count}"
        )
    if float(corpus["rejection_rate"]) > MAX_REJECTION_RATE:
        raise RuntimeError(
            f"G_corpus FAIL: rejection_rate {corpus['rejection_rate']} exceeds {MAX_REJECTION_RATE}"
        )
    payload = corpus["fingerprint_payload"]
    payload_bytes = fingerprint_bytes(payload)
    payload_hash = sha256_hex_from_bytes(payload_bytes)
    corpus_hash = str(corpus["fingerprint"])
    if payload_hash != corpus_hash:
        raise RuntimeError(
            f"G_corpus FAIL: fingerprint_payload_bytes_hash {payload_hash} != corpus fingerprint {corpus_hash}"
        )
    return {
        "corpus_hash": corpus_hash,
        "fingerprint_payload": payload,
        "fingerprint_bytes": payload_bytes,
        "fingerprint_payload_bytes_hash": payload_hash,
        "train_records": train_records,
        "rejection_rate": float(corpus["rejection_rate"]),
        "component_count": component_count,
        "system_count": len(train_records),
    }


def sha256_hex_from_bytes(data: bytes) -> str:
    import hashlib

    return hashlib.sha256(data).hexdigest()


def source_variant_index(record: dict[str, Any]) -> int:
    return int(record["variant_index"])


def tier_index(record: dict[str, Any]) -> int:
    return source_variant_index(record) % 3


def draw_index(record: dict[str, Any]) -> int:
    return source_variant_index(record) // 3


def hill_exponent(record: dict[str, Any]) -> int:
    return (1, 2, 4)[tier_index(record)]


def iter_components(record: dict[str, Any]) -> list[dict[str, Any]]:
    family = str(record["family"])
    prefixes = str(record["teacher_prefix"]).split("|")
    rows = []
    for component_idx, prefix in enumerate(prefixes):
        rows.append(
            {
                "system_id": record["system_id"],
                "family": family,
                "dimension": int(record["dimension"]),
                "component_idx": component_idx,
                "truth_prefix": prefix,
                "source_variant_index": source_variant_index(record),
                "tier_index": tier_index(record),
                "draw_index": draw_index(record),
                "hill_exponent": hill_exponent(record),
            }
        )
    return rows


def build_component_index(train_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    components: list[dict[str, Any]] = []
    for record in sorted(train_records, key=lambda row: (row["family"], row["system_id"])):
        components.extend(iter_components(record))
    return components


def load_frozen_corpus() -> dict[str, Any]:
    corpus = frozen_generate_corpus()
    validated = validate_corpus(corpus)
    validated["component_index"] = build_component_index(validated["train_records"])
    return validated
