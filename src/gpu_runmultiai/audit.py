"""C0001 metric-identifiability audit orchestrator."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from experiment_runtime import REPO_ROOT
from gpu_run2_runtime import write_json
from gpu_runmultiai.calls import CallLogger, expected_confirmatory_calls
from gpu_runmultiai.config_paths import output_root_abs
from gpu_runmultiai.controls import any_gate_failed, condition_summary, evaluate_validity_gates
from gpu_runmultiai.corpus import load_frozen_corpus
from gpu_runmultiai.ids import component_id_for
from gpu_runmultiai.manifest import build_resume_identity, current_commit, verify_plan_hash, verify_resume_identity, write_manifest
from gpu_runmultiai.odeformer_runtime import ODEFormerUnavailable, get_env, measure_g0_scaler_asserts, require_odeformer
from gpu_runmultiai.outcomes import PAIR_RESULT_COLUMNS, evaluate_primary_decision
from gpu_runmultiai.pipeline import (
    registration_rows,
    run_b0_pair,
    run_b1_pair,
    run_b2_pair,
    run_b3_pairs,
    run_b4_row,
    run_d2_pair,
    run_negative_controls,
    select_b3_pairs,
)
from gpu_runmultiai.sealed_guard import SealedPathGuard
from gpu_runmultiai.strata import is_linear_component, is_strict_hill_component


def _attach_records(component_index: list[dict[str, Any]], train_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_id = {row["system_id"]: row for row in train_records}
    enriched = []
    for item in component_index:
        enriched.append({**item, "record": by_id[item["system_id"]]})
    return enriched


def _write_pair_results(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=PAIR_RESULT_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column) for column in PAIR_RESULT_COLUMNS})


def _write_equivalence_oracle(path: Path, rows: list[dict[str, Any]]) -> None:
    payload = []
    for row in rows:
        if row.get("condition") not in {"B0", "D2"}:
            continue
        payload.append(
            {
                "pair_id": row["pair_id"],
                "component_idx": row["component_idx"],
                "scale": row["scale"],
                "E1": {
                    "completed": row.get("e1_oracle_completed"),
                    "analytic_equivalent": row.get("e1_analytic_equivalent"),
                    "numeric_equivalent": row.get("e1_numeric_equivalent"),
                    "equivalent": row.get("e1_oracle_equivalent"),
                },
                "E2": {
                    "completed": row.get("e2_oracle_completed"),
                    "analytic_equivalent": row.get("e2_analytic_equivalent"),
                    "numeric_equivalent": row.get("e2_numeric_equivalent"),
                    "equivalent": row.get("e2_oracle_equivalent"),
                },
            }
        )
    write_json(path, payload)


def _write_deviation_log(path: Path) -> None:
    path.write_text(
        "# C0001 deviation log\n\nNo frozen-protocol deviations recorded in implementation revision R1.\n",
        encoding="utf-8",
    )


def run_audit(options: dict[str, Any]) -> dict[str, Any]:
    verify_plan_hash()
    output_dir = Path(options["output_dir"]).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    if options.get("fail_if_exists") and any(output_dir.iterdir()) and not options.get("resume"):
        raise RuntimeError(f"output directory already exists: {output_dir}")

    runtime_available = True
    try:
        require_odeformer()
        get_env()
    except ODEFormerUnavailable:
        runtime_available = False
        if not options.get("smoke"):
            raise

    guard = SealedPathGuard(output_root_abs=output_root_abs())
    guard.install()
    try:
        return _run_audit_body(options, output_dir, guard, runtime_available=runtime_available)
    finally:
        guard.restore()


def _run_audit_body(
    options: dict[str, Any],
    output_dir: Path,
    guard: SealedPathGuard,
    *,
    runtime_available: bool,
) -> dict[str, Any]:
    corpus = load_frozen_corpus()
    component_index = _attach_records(corpus["component_index"], corpus["train_records"])
    smoke_limit = 2 if options.get("smoke") else None

    call_log_path = output_dir / "call_log.jsonl"
    if options.get("resume") and call_log_path.is_file():
        call_logger = CallLogger.load(call_log_path)
        call_logger.skip_duplicates = True
    else:
        if call_log_path.exists():
            call_log_path.unlink()
        call_logger = CallLogger(call_log_path)

    commit = current_commit()
    script_path = REPO_ROOT / "scripts/phases/gpu_runmultiai_c0001_metric_audit.py"
    resume_identity = build_resume_identity(
        commit=commit,
        audit_script_path=script_path,
        corpus_hash=corpus["corpus_hash"],
        cli_args=options,
        output_dir=output_dir,
    )
    manifest_path = output_dir / "audit_manifest.json"
    if options.get("resume"):
        existing = json.loads(manifest_path.read_text(encoding="utf-8"))
        verify_resume_identity(existing.get("resume_identity", {}), resume_identity)

    oracle_timeout_sec = float(options["oracle_timeout_sec"])
    simplifier_timeout_sec = float(options.get("simplifier_subprocess_timeout_sec", 5.0))

    truth_rows, rewrite_rows = registration_rows(
        corpus["corpus_hash"],
        component_index,
        oracle_timeout_sec=oracle_timeout_sec,
        call_logger=call_logger,
        limit=smoke_limit,
    )
    rewrite_by_component = {row["component_id"]: row for row in rewrite_rows}

    pair_rows: list[dict[str, Any]] = []
    b0_rows: list[dict[str, Any]] = []
    b1_rows: list[dict[str, Any]] = []
    b2_rows: list[dict[str, Any]] = []
    d2_rows: list[dict[str, Any]] = []
    scales = ["0.1"] if options.get("smoke") else list(options.get("primary_scales", ("0.1", "0.5", "1.0", "2.0")))
    selected_components = component_index[: smoke_limit or len(component_index)]

    for item in selected_components:
        record = item["record"]
        component_idx = item["component_idx"]
        component_id, _ = component_id_for(corpus["corpus_hash"], item["system_id"], component_idx)
        rewrite_row = rewrite_by_component[component_id]
        for scale in scales:
            row = run_b0_pair(
                corpus_hash=corpus["corpus_hash"],
                record=record,
                component_idx=component_idx,
                scale=scale,
                rewrite_row=rewrite_row,
                oracle_timeout_sec=oracle_timeout_sec,
                simplifier_timeout_sec=simplifier_timeout_sec,
                call_logger=call_logger,
                runtime_available=runtime_available,
                guard=guard,
            )
            b0_rows.append(row)
            pair_rows.append(row)
            if runtime_available and not options.get("smoke"):
                b2_rows.append(run_b2_pair(b0_row=row, record=record, call_logger=call_logger))
        if is_strict_hill_component(record["family"], component_idx) and not options.get("smoke"):
            d2_rows.append(
                run_d2_pair(
                    corpus_hash=corpus["corpus_hash"],
                    record=record,
                    component_idx=component_idx,
                    rewrite_row=rewrite_row,
                    oracle_timeout_sec=oracle_timeout_sec,
                    simplifier_timeout_sec=simplifier_timeout_sec,
                    call_logger=call_logger,
                    runtime_available=runtime_available,
                    guard=guard,
                )
            )
        b1_rows.append(
            run_b1_pair(
                corpus_hash=corpus["corpus_hash"],
                record=record,
                component_idx=component_idx,
                oracle_timeout_sec=oracle_timeout_sec,
                simplifier_timeout_sec=simplifier_timeout_sec,
                call_logger=call_logger,
                runtime_available=runtime_available,
                guard=guard,
            )
        )

    pair_rows.extend(b1_rows)
    pair_rows.extend(b2_rows)
    pair_rows.extend(d2_rows)

    b4_rows = [
        run_b4_row(
            corpus_hash=corpus["corpus_hash"],
            record=item["record"],
            component_idx=item["component_idx"],
            call_logger=call_logger,
        )
        for item in selected_components
    ]
    negative_controls = run_negative_controls(
        component_index,
        oracle_timeout_sec=oracle_timeout_sec,
        call_logger=call_logger,
        limit=2 if options.get("smoke") else 100,
    )
    b3_rows = run_b3_pairs(select_b3_pairs(b0_rows), call_logger=call_logger) if b0_rows else []

    linear_rows = []
    non_strict_rows = []
    for row in b0_rows:
        control_row = {
            "pair_id": row["pair_id"],
            "classifier_parse_valid": row.get("classifier_parse_valid"),
            "formula_metrics_valid": row.get("formula_metrics_valid"),
            "hill_form": row.get("hill_form"),
            "canonical_exact": row.get("canonical_exact"),
        }
        if row.get("stratum") == "linear":
            linear_rows.append(control_row)
        if row.get("stratum") == "non_strict_hill":
            non_strict_rows.append(control_row)

    sample_dimension = int(selected_components[0]["record"]["dimension"]) if selected_components else 3
    try:
        scaler_asserts = measure_g0_scaler_asserts(sample_dimension, scale=float(scales[0]))
    except ODEFormerUnavailable:
        scaler_asserts = {}

    strict_rows = [row for row in b0_rows if row.get("stratum") == "strict_hill"]
    descriptive = bool(d2_rows)
    call_logger.assert_ceiling(descriptive=descriptive)

    gate_state = {
        "g_corpus_pass": True,
        "scaler_asserts": scaler_asserts,
        "access_attempts": guard.attempt_count(),
        "total_calls": call_logger.total(),
        "call_ceiling": expected_confirmatory_calls(),
        "negative_controls": negative_controls,
        "b4_rows": b4_rows,
        "linear_rows": linear_rows,
        "strict_rows": strict_rows,
    }
    gates = evaluate_validity_gates(gate_state)
    decision = evaluate_primary_decision(strict_rows, validity_gate_failed=any_gate_failed(gates))
    manifest = {
        "audit_id": resume_identity["audit_id"],
        "commit": commit,
        "resume_identity": resume_identity,
        "corpus_hash": corpus["corpus_hash"],
        "fingerprint_payload": corpus["fingerprint_payload"],
        "fingerprint_bytes_path": str(output_dir / "fingerprint_bytes.bin"),
        "fingerprint_payload_path": str(output_dir / "fingerprint_payload.json"),
        "fingerprint_payload_bytes_hash": corpus["corpus_hash"],
        "access_guard_attempts": guard.to_log(),
        "validity_gates": gates,
        "primary_decision": decision,
        "primitive_completion_rate": call_logger.total() / expected_confirmatory_calls(),
        "b3_rows": len(b3_rows),
        "non_strict_rows": len(non_strict_rows),
    }
    (output_dir / "fingerprint_bytes.bin").write_bytes(corpus["fingerprint_bytes"])
    write_json(output_dir / "fingerprint_payload.json", corpus["fingerprint_payload"])
    write_manifest(manifest_path, manifest)
    write_json(output_dir / "condition_summary.json", condition_summary(strict_rows))
    write_json(output_dir / "negative_controls.json", negative_controls)
    _write_pair_results(output_dir / "pair_results.csv", pair_rows)
    _write_equivalence_oracle(output_dir / "equivalence_oracle.json", b0_rows + d2_rows)
    _write_deviation_log(output_dir / "deviation_log.md")
    return {
        "manifest": manifest,
        "pair_rows": pair_rows,
        "call_total": call_logger.total(),
        "gates": gates,
        "decision": decision,
    }
