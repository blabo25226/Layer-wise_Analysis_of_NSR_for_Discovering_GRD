"""Representative timing calibration for frozen wall-ceiling feasibility (§8)."""

from __future__ import annotations

import time
from typing import Any

from gpu_runmultiai.calls import expected_confirmatory_calls
from gpu_runmultiai.constants import (
    ELAPSED_WALL_CEILING_SEC,
    IDENTITY_REWRITE_ID,
    IDENTITY_SCALE,
    ORACLE_TIMEOUT_SEC,
    Q4_TIMEOUT_SEC,
    SIMPLIFIER_SUBPROCESS_TIMEOUT_SEC,
)
from gpu_runmultiai.corpus import load_frozen_corpus
from gpu_runmultiai.ids import component_id_for, pair_id_for
from gpu_runmultiai.pipeline import run_b1_pair, run_b3_pairs, run_c_q4_fixtures
from gpu_runmultiai.rewrites import truth_component_infix
from gpu_runmultiai.sealed_guard import SealedPathGuard
from gpu_runmultiai.strata import component_stratum, is_linear_component, is_strict_hill_component

B1_PRIMITIVES_PER_COMPONENT = 8
MIN_CALIBRATION_COMPONENTS = 20


def _select_calibration_components(component_index: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Pick >=20 representative components covering strata and dimensions."""
    selected: list[dict[str, Any]] = []
    seen_keys: set[tuple[str, int]] = set()

    def _add(item: dict[str, Any]) -> None:
        key = (item["system_id"], int(item["component_idx"]))
        if key in seen_keys:
            return
        seen_keys.add(key)
        selected.append(item)

    d3_secondary = [
        item
        for item in component_index
        if int(item["record"]["dimension"]) == 3 and int(item["component_idx"]) > 0
    ]
    if d3_secondary:
        _add(d3_secondary[0])

    linear = [
        item
        for item in component_index
        if is_linear_component(item["record"]["family"], item["component_idx"])
    ]
    if linear:
        _add(linear[0])

    secondary_hill = [
        item
        for item in component_index
        if component_stratum(item["record"]["family"], item["component_idx"]) == "non_strict_hill"
    ]
    if secondary_hill:
        _add(secondary_hill[0])

    for dimension in (1, 2, 3):
        for item in component_index:
            if int(item["record"]["dimension"]) == dimension:
                _add(item)
                break

    stride = max(1, len(component_index) // max(MIN_CALIBRATION_COMPONENTS, 1))
    for index in range(0, len(component_index), stride):
        _add(component_index[index])
        if len(selected) >= MIN_CALIBRATION_COMPONENTS:
            break

    if len(selected) < MIN_CALIBRATION_COMPONENTS:
        for item in component_index:
            _add(item)
            if len(selected) >= MIN_CALIBRATION_COMPONENTS:
                break
    return selected[: max(MIN_CALIBRATION_COMPONENTS, len(selected))]


def _aggregate_call_type_means(rows: list[dict[str, Any]]) -> dict[str, float]:
    buckets: dict[str, list[float]] = {}
    for row in rows:
        duration = row.get("duration_sec")
        if duration is None:
            continue
        buckets.setdefault(str(row["primitive"]), []).append(float(duration))
    return {
        primitive: sum(values) / len(values)
        for primitive, values in buckets.items()
        if values
    }


def run_timing_calibration(
    *,
    call_logger: Any,
    runtime_available: bool,
    guard: Any,
) -> dict[str, Any]:
    """Sample representative B1/C_q4/B3 costs and project a conservative full-run wall time."""
    from gpu_runmultiai.calls import CallLogger
    from gpu_runmultiai.odeformer_runtime import ODEFormerUnavailable, require_odeformer

    if not runtime_available:
        return {
            "status": "BLOCK",
            "reason": "odeformer_unavailable",
            "sampled_components": 0,
            "projected_full_run_sec": None,
            "elapsed_wall_ceiling_sec": ELAPSED_WALL_CEILING_SEC,
        }

    try:
        require_odeformer()
    except ODEFormerUnavailable as exc:
        return {
            "status": "BLOCK",
            "reason": f"odeformer_unavailable:{exc}",
            "sampled_components": 0,
            "projected_full_run_sec": None,
            "elapsed_wall_ceiling_sec": ELAPSED_WALL_CEILING_SEC,
        }

    corpus = load_frozen_corpus()
    component_index = [
        {**item, "record": next(r for r in corpus["train_records"] if r["system_id"] == item["system_id"])}
        for item in corpus["component_index"]
    ]
    selected = _select_calibration_components(component_index)
    calibration_logger = CallLogger()
    started = time.monotonic()

    for item in selected:
        record = item["record"]
        component_idx = int(item["component_idx"])
        run_b1_pair(
            corpus_hash=corpus["corpus_hash"],
            record=record,
            component_idx=component_idx,
            oracle_timeout_sec=ORACLE_TIMEOUT_SEC,
            q4_timeout_sec=Q4_TIMEOUT_SEC,
            simplifier_timeout_sec=SIMPLIFIER_SUBPROCESS_TIMEOUT_SEC,
            call_logger=calibration_logger,
            runtime_available=True,
            guard=guard,
        )

    run_c_q4_fixtures(
        call_logger=calibration_logger,
        q4_timeout_sec=Q4_TIMEOUT_SEC,
    )
    sample_b0 = {
        "pair_id": "pair_sha256:" + "c" * 64,
        "component_id": "component_sha256:" + "d" * 64,
        "component_idx": 0,
        "classifier_parse_valid": True,
        "formula_metrics_valid": True,
        "exponent_aware_skeleton_exact": 1.0,
        "truth_infix": "(x_0)",
        "e2_infix_pre_classifier": "(x_0)",
    }
    run_b3_pairs([sample_b0], call_logger=calibration_logger)

    observed_sec = time.monotonic() - started
    per_type = _aggregate_call_type_means(calibration_logger.rows)
    b1_calls = len(selected) * B1_PRIMITIVES_PER_COMPONENT
    mean_b1_call = (
        sum(per_type.get(name, 0.0) for name in (
            "e0_identity_construct",
            "scaler_rescale_function",
            "q4_decimal_round_reference",
            "simplifier_subprocess",
            "oracle_equivalence",
            "classify_component_flags",
            "formula_metrics_pair",
        ))
        / 7.0
        if per_type
        else observed_sec / max(b1_calls, 1)
    )
    oracle_mean = per_type.get("oracle_equivalence", mean_b1_call)
    simplifier_mean = per_type.get("simplifier_subprocess", mean_b1_call)
    cas_mean = per_type.get("compare_formulas_cas", mean_b1_call)
    q4_mean = per_type.get("q4_decimal_round_reference", mean_b1_call)

    projected = (
        expected_confirmatory_calls() * max(mean_b1_call, oracle_mean, simplifier_mean, q4_mean) * 1.15
        + 500 * cas_mean * 1.10
    )
    status = "PASS" if projected <= ELAPSED_WALL_CEILING_SEC else "BLOCK"
    component_ids = []
    for item in selected:
        component_id, _ = component_id_for(corpus["corpus_hash"], item["system_id"], item["component_idx"])
        pair_id, _ = pair_id_for(
            corpus["corpus_hash"],
            item["system_id"],
            item["component_idx"],
            IDENTITY_SCALE,
            IDENTITY_REWRITE_ID,
        )
        component_ids.append(
            {
                "component_id": component_id,
                "pair_id": pair_id,
                "system_id": item["system_id"],
                "component_idx": item["component_idx"],
                "dimension": int(item["record"]["dimension"]),
                "stratum": component_stratum(item["record"]["family"], item["component_idx"]),
            }
        )
    return {
        "status": status,
        "sampled_components": len(selected),
        "sampled_component_ids": component_ids,
        "observed_calibration_sec": observed_sec,
        "call_type_mean_sec": per_type,
        "conservative_multiplier": 1.15,
        "projected_full_run_sec": projected,
        "elapsed_wall_ceiling_sec": ELAPSED_WALL_CEILING_SEC,
        "confirmatory_call_ceiling": expected_confirmatory_calls(),
    }
