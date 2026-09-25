"""Representative timing calibration for frozen wall-ceiling feasibility (§8)."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

from gpu_runmultiai.calls import PRIMITIVE_TABLE, expected_confirmatory_calls, expected_descriptive_calls
from gpu_runmultiai.constants import (
    D2_CALLS_PER_PAIR,
    D2_PAIR_COUNT,
    ELAPSED_WALL_CEILING_SEC,
    FULL_RUN_CALL_CEILING,
    IDENTITY_REWRITE_ID,
    IDENTITY_SCALE,
    ORACLE_TIMEOUT_SEC,
    PRIMARY_SCALES,
    Q4_TIMEOUT_SEC,
    SIMPLIFIER_SUBPROCESS_TIMEOUT_SEC,
)
from gpu_runmultiai.corpus import load_frozen_corpus
from gpu_runmultiai.ids import component_id_for, pair_id_for
from gpu_runmultiai.pipeline import (
    registration_rows,
    run_b0_pair,
    run_b1_pair,
    run_b3_pairs,
    run_c_q4_fixtures,
    run_d2_pair,
)
from gpu_runmultiai.rewrites import rewrite_registration, truth_component_infix
from gpu_runmultiai.sealed_guard import SealedPathGuard
from gpu_runmultiai.strata import component_stratum, is_linear_component

MIN_CALIBRATION_COMPONENTS = 20
POSITIVE_MARGIN_FRACTION = 0.15

D2_PAIR_PRIMITIVE_SEQUENCE: tuple[tuple[str, str], ...] = (
    ("e0_analytic_construct", "D2"),
    ("scaler_rescale_function", "D2"),
    ("q4_decimal_round_reference", "D2"),
    ("simplifier_subprocess", "D2"),
    ("oracle_equivalence", "D2_E1"),
    ("oracle_equivalence", "D2_E2"),
    ("classify_component_flags", "D2"),
    ("formula_metrics_pair", "D2"),
)


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


def _aggregate_call_type_means(rows: list[dict[str, Any]]) -> dict[tuple[str, str], float]:
    buckets: dict[tuple[str, str], list[float]] = {}
    for row in rows:
        duration = row.get("duration_sec")
        if duration is None:
            continue
        key = (str(row["primitive"]), str(row["condition"]))
        buckets.setdefault(key, []).append(float(duration))
    return {
        key: sum(values) / len(values)
        for key, values in buckets.items()
        if values
    }


def _frozen_primitive_rows() -> list[dict[str, Any]]:
    return [dict(row) for row in PRIMITIVE_TABLE]


def _conservative_cost(
    primitive: str,
    condition: str,
    per_type: dict[tuple[str, str], float],
    *,
    fallback: float,
) -> float:
    observed = per_type.get((primitive, condition))
    if observed is None:
        observed = per_type.get((primitive, condition.split("_")[0]))
    if observed is None:
        return fallback
    return observed * 1.10


def _measure_append_fsync_overhead(tmp_path: Path) -> float:
    target = tmp_path / "timing_append_probe.jsonl"
    started = time.monotonic()
    for index in range(20):
        with target.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps({"index": index}, sort_keys=True) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
    return (time.monotonic() - started) / 20.0


def run_timing_calibration(
    *,
    call_logger: Any,
    runtime_available: bool,
    guard: Any,
    resource_monitor: Any | None = None,
) -> dict[str, Any]:
    """Sample representative costs and project exact multiplicity-weighted grand runtime."""
    from gpu_runmultiai.calls import CallLogger
    from gpu_runmultiai.odeformer_runtime import ODEFormerUnavailable, require_odeformer

    if not runtime_available:
        return {
            "status": "BLOCK",
            "reason": "odeformer_unavailable",
            "sampled_components": 0,
            "projected_grand_run_sec": None,
            "elapsed_wall_ceiling_sec": ELAPSED_WALL_CEILING_SEC,
            "b0_calibration_scales_observed": [],
            "b0_primary_scales_frozen": list(PRIMARY_SCALES),
            "b0_scales_extrapolated_not_observed": list(PRIMARY_SCALES),
        }

    try:
        require_odeformer()
    except ODEFormerUnavailable as exc:
        return {
            "status": "BLOCK",
            "reason": f"odeformer_unavailable:{exc}",
            "sampled_components": 0,
            "projected_grand_run_sec": None,
            "elapsed_wall_ceiling_sec": ELAPSED_WALL_CEILING_SEC,
            "b0_calibration_scales_observed": [],
            "b0_primary_scales_frozen": list(PRIMARY_SCALES),
            "b0_scales_extrapolated_not_observed": list(PRIMARY_SCALES),
        }

    corpus = load_frozen_corpus()
    component_index = [
        {**item, "record": next(r for r in corpus["train_records"] if r["system_id"] == item["system_id"])}
        for item in corpus["component_index"]
    ]
    selected = _select_calibration_components(component_index)
    startup_started = time.monotonic()
    calibration_logger = CallLogger(resource_monitor=resource_monitor)
    startup_overhead_sec = time.monotonic() - startup_started
    calibration_started = time.monotonic()
    overhead_probe_dir = (
        resource_monitor._output_dir / ".timing_overhead_probe"
        if resource_monitor is not None
        else Path("/tmp/c0001_timing_overhead_probe")
    )
    overhead_probe_dir.mkdir(parents=True, exist_ok=True)

    registration_logger = CallLogger(resource_monitor=resource_monitor)
    registration_sample = selected[: max(5, min(len(selected), MIN_CALIBRATION_COMPONENTS // 4))]
    registration_rows(
        corpus["corpus_hash"],
        registration_sample,
        oracle_timeout_sec=ORACLE_TIMEOUT_SEC,
        call_logger=registration_logger,
        stage_cache={},
        cache_path=None,
        limit=len(registration_sample),
    )

    rewrite_by_component: dict[str, dict[str, Any]] = {}
    for item in selected:
        record = item["record"]
        component_idx = int(item["component_idx"])
        truth_prefix, truth_infix = truth_component_infix(record, component_idx)
        component_id, _ = component_id_for(corpus["corpus_hash"], item["system_id"], component_idx)
        rewrite_by_component[component_id] = rewrite_registration(
            record["system_id"],
            component_idx,
            truth_prefix,
            truth_infix,
            oracle_timeout_sec=ORACLE_TIMEOUT_SEC,
        )

    for item in selected:
        record = item["record"]
        component_idx = int(item["component_idx"])
        component_id, _ = component_id_for(corpus["corpus_hash"], item["system_id"], component_idx)
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
        run_b0_pair(
            corpus_hash=corpus["corpus_hash"],
            record=record,
            component_idx=component_idx,
            scale="0.1",
            rewrite_row=rewrite_by_component[component_id],
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

    d2_sample = next(
        item
        for item in component_index
        if component_stratum(item["record"]["family"], item["component_idx"]) == "strict_hill"
    )
    d2_record = d2_sample["record"]
    d2_component_idx = int(d2_sample["component_idx"])
    d2_component_id, _ = component_id_for(
        corpus["corpus_hash"], d2_sample["system_id"], d2_component_idx
    )
    if d2_component_id not in rewrite_by_component:
        truth_prefix, truth_infix = truth_component_infix(d2_record, d2_component_idx)
        rewrite_by_component[d2_component_id] = rewrite_registration(
            d2_record["system_id"],
            d2_component_idx,
            truth_prefix,
            truth_infix,
            oracle_timeout_sec=ORACLE_TIMEOUT_SEC,
        )
    run_d2_pair(
        corpus_hash=corpus["corpus_hash"],
        record=d2_record,
        component_idx=d2_component_idx,
        rewrite_row=rewrite_by_component[d2_component_id],
        oracle_timeout_sec=ORACLE_TIMEOUT_SEC,
        q4_timeout_sec=Q4_TIMEOUT_SEC,
        simplifier_timeout_sec=SIMPLIFIER_SUBPROCESS_TIMEOUT_SEC,
        call_logger=calibration_logger,
        runtime_available=True,
        guard=guard,
    )

    observed_sec = time.monotonic() - calibration_started
    combined_rows = registration_logger.rows + calibration_logger.rows
    per_type = _aggregate_call_type_means(combined_rows)
    fallback = observed_sec / max(len(combined_rows), 1)

    multiplicity_rows: list[dict[str, Any]] = []
    weighted_confirmatory = 0.0
    for row in _frozen_primitive_rows():
        primitive = str(row["primitive"])
        condition = str(row["condition"])
        units = int(row["units"])
        unit_cost = _conservative_cost(primitive, condition, per_type, fallback=fallback)
        weighted = units * unit_cost
        weighted_confirmatory += weighted
        multiplicity_rows.append(
            {
                "primitive_id": row["id"],
                "primitive": primitive,
                "condition": condition,
                "multiplicity": units,
                "sample_count": len(
                    [
                        sample
                        for sample in combined_rows
                        if sample.get("primitive") == primitive and sample.get("condition") == condition
                    ]
                ),
                "conservative_unit_cost_sec": unit_cost,
                "weighted_cost_sec": weighted,
            }
        )

    d2_pair_costs: list[dict[str, Any]] = []
    d2_pair_weighted = 0.0
    for primitive, condition in D2_PAIR_PRIMITIVE_SEQUENCE:
        unit_cost = _conservative_cost(primitive, condition, per_type, fallback=fallback)
        weighted = unit_cost
        d2_pair_weighted += weighted
        d2_pair_costs.append(
            {
                "primitive": primitive,
                "condition": condition,
                "conservative_unit_cost_sec": unit_cost,
            }
        )
    descriptive_weighted = D2_PAIR_COUNT * d2_pair_weighted

    append_fsync_sec = _measure_append_fsync_overhead(overhead_probe_dir)
    resource_scan_sec = 0.0
    if resource_monitor is not None:
        scan_started = time.monotonic()
        resource_monitor.snapshot()
        resource_monitor.dir_bytes()
        resource_scan_sec = time.monotonic() - scan_started
    finalization_probe_started = time.monotonic()
    probe_manifest = overhead_probe_dir / "finalization_probe.json"
    probe_manifest.write_text(json.dumps({"status": "completed"}, sort_keys=True), encoding="utf-8")
    finalization_sec = time.monotonic() - finalization_probe_started
    measured_overhead_sec = (
        startup_overhead_sec
        + append_fsync_sec * 200.0
        + resource_scan_sec * 50.0
        + finalization_sec * 10.0
    )

    subtotal = weighted_confirmatory + descriptive_weighted + measured_overhead_sec
    projected = subtotal * (1.0 + POSITIVE_MARGIN_FRACTION)
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
        "call_type_mean_sec": {f"{primitive}:{condition}": value for (primitive, condition), value in per_type.items()},
        "primitive_multiplicity_table": multiplicity_rows,
        "weighted_confirmatory_sec": weighted_confirmatory,
        "d2_pair_primitive_sequence": [
            {"primitive": primitive, "condition": condition}
            for primitive, condition in D2_PAIR_PRIMITIVE_SEQUENCE
        ],
        "d2_pair_weighted_sec": d2_pair_weighted,
        "d2_pair_count": D2_PAIR_COUNT,
        "d2_calls_per_pair": D2_CALLS_PER_PAIR,
        "descriptive_calls": expected_descriptive_calls(),
        "descriptive_weighted_sec": descriptive_weighted,
        "measured_overhead_sec": measured_overhead_sec,
        "overhead_components_sec": {
            "startup": startup_overhead_sec,
            "append_fsync_per_write": append_fsync_sec,
            "resource_scan": resource_scan_sec,
            "finalization": finalization_sec,
        },
        "positive_margin_fraction": POSITIVE_MARGIN_FRACTION,
        "projected_grand_run_sec": projected,
        "projected_full_run_sec": projected,
        "elapsed_wall_ceiling_sec": ELAPSED_WALL_CEILING_SEC,
        "confirmatory_call_ceiling": expected_confirmatory_calls(),
        "grand_call_ceiling": FULL_RUN_CALL_CEILING,
        "b0_calibration_scales_observed": ["0.1"],
        "b0_primary_scales_frozen": list(PRIMARY_SCALES),
        "b0_scales_extrapolated_not_observed": [
            scale for scale in PRIMARY_SCALES if scale != "0.1"
        ],
    }
