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
from gpu_runmultiai.manifest import build_resume_identity, current_commit, verify_plan_hash, verify_resume_identity, write_manifest
from gpu_runmultiai.odeformer_runtime import ODEFormerUnavailable, require_odeformer
from gpu_runmultiai.outcomes import evaluate_primary_decision
from gpu_runmultiai.ids import component_id_for
from gpu_runmultiai.pipeline import (
    registration_rows,
    run_b0_pair,
    run_b4_row,
    run_negative_controls,
)
from gpu_runmultiai.sealed_guard import SealedPathGuard
from gpu_runmultiai.strata import is_strict_hill_component


def _attach_records(component_index: list[dict[str, Any]], train_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_id = {row["system_id"]: row for row in train_records}
    enriched = []
    for item in component_index:
        enriched.append({**item, "record": by_id[item["system_id"]]})
    return enriched


def run_audit(options: dict[str, Any]) -> dict[str, Any]:
    verify_plan_hash()
    output_dir = Path(options["output_dir"]).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    if options.get("fail_if_exists") and any(output_dir.iterdir()) and not options.get("resume"):
        raise RuntimeError(f"output directory already exists: {output_dir}")
    guard = SealedPathGuard(output_root_abs=output_root_abs())
    guard.install()
    corpus = load_frozen_corpus()
    component_index = _attach_records(corpus["component_index"], corpus["train_records"])
    smoke_limit = 2 if options.get("smoke") else None
    runtime_available = True
    try:
        require_odeformer()
    except ODEFormerUnavailable:
        runtime_available = False
        if not options.get("smoke"):
            raise
    call_log_path = output_dir / "call_log.jsonl"
    if options.get("resume") and call_log_path.is_file():
        call_logger = CallLogger()
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
    )
    manifest_path = output_dir / "audit_manifest.json"
    if options.get("resume"):
        existing = json.loads(manifest_path.read_text(encoding="utf-8"))
        verify_resume_identity(existing.get("resume_identity", {}), resume_identity)
    truth_rows, rewrite_rows = registration_rows(
        corpus["corpus_hash"],
        component_index,
        oracle_timeout_sec=float(options["oracle_timeout_sec"]),
        call_logger=call_logger,
        limit=smoke_limit,
    )
    rewrite_by_component = {row["component_id"]: row for row in rewrite_rows}
    pair_rows: list[dict[str, Any]] = []
    scales = ["0.1"] if options.get("smoke") else list(options.get("primary_scales", ("0.1", "0.5", "1.0", "2.0")))
    for item in component_index[: smoke_limit or len(component_index)]:
        record = item["record"]
        component_idx = item["component_idx"]
        component_id, _ = component_id_for(corpus["corpus_hash"], item["system_id"], component_idx)
        rewrite_row = rewrite_by_component[component_id]
        if is_strict_hill_component(record["family"], component_idx):
            for scale in scales:
                pair_rows.append(
                    run_b0_pair(
                        corpus_hash=corpus["corpus_hash"],
                        record=record,
                        component_idx=component_idx,
                        scale=scale,
                        rewrite_row=rewrite_row,
                        oracle_timeout_sec=float(options["oracle_timeout_sec"]),
                        call_logger=call_logger,
                        runtime_available=runtime_available,
                    )
                )
    b4_rows = [
        run_b4_row(
            corpus_hash=corpus["corpus_hash"],
            record=item["record"],
            component_idx=item["component_idx"],
            call_logger=call_logger,
        )
        for item in component_index[: smoke_limit or len(component_index)]
    ]
    negative_controls = run_negative_controls(
        component_index,
        oracle_timeout_sec=float(options["oracle_timeout_sec"]),
        call_logger=call_logger,
        limit=2 if options.get("smoke") else 100,
    )
    linear_rows = []
    for row in pair_rows:
        if row.get("stratum") == "linear":
            linear_rows.append(
                {
                    "pair_id": row["pair_id"],
                    "classifier_parse_valid": row.get("classifier_parse_valid"),
                    "formula_metrics_valid": row.get("canonical_exact") is not None,
                    "hill_form": row.get("hill_form"),
                    "canonical_exact": row.get("canonical_exact"),
                }
            )
    strict_rows = [row for row in pair_rows if row.get("stratum") == "strict_hill"]
    gate_state = {
        "g_corpus_pass": True,
        "scaler_asserts": {"time_scale": 9, "time_shift": 1, "a_t": 0.9, "b_t": 1.0, "rescale_features": True},
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
        "access_guard_attempts": guard.to_log(),
        "validity_gates": gates,
        "primary_decision": decision,
        "primitive_completion_rate": call_logger.total() / expected_confirmatory_calls(),
    }
    (output_dir / "fingerprint_bytes.bin").write_bytes(corpus["fingerprint_bytes"])
    write_json(output_dir / "fingerprint_payload.json", corpus["fingerprint_payload"])
    write_manifest(manifest_path, manifest)
    write_json(output_dir / "condition_summary.json", condition_summary(strict_rows))
    write_json(output_dir / "negative_controls.json", negative_controls)
    _write_pair_results(output_dir / "pair_results.csv", pair_rows)
    return {
        "manifest": manifest,
        "pair_rows": pair_rows,
        "call_total": call_logger.total(),
        "gates": gates,
        "decision": decision,
    }


def _write_pair_results(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = sorted({key for row in rows for key in row.keys()})
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
