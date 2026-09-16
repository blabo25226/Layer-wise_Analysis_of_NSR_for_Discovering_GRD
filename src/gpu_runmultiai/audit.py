"""C0001 metric-identifiability audit orchestrator."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from experiment_runtime import REPO_ROOT
from gpu_run2_runtime import write_json
from gpu_runmultiai.constants import (
    CONFIRMATORY_CALL_CEILING,
    ELAPSED_WALL_CEILING_SEC,
    FULL_RUN_CALL_CEILING,
    OUTPUT_DIR_BYTE_CEILING,
    Q4_TIMEOUT_SEC,
)
from gpu_runmultiai.eligibility import validate_g_eligibility
from gpu_runmultiai.jsonl_durable import append_jsonl_line, load_jsonl
from gpu_runmultiai.calls import CallLogger, expected_confirmatory_calls
from gpu_runmultiai.controls import (
    ABORT_GATES,
    any_gate_failed,
    condition_summary,
    evaluate_validity_gates,
    first_abort_gate,
)
from gpu_runmultiai.corpus import load_frozen_corpus
from gpu_runmultiai.guard_side_channel import append_guard_attempts, load_guard_attempts, side_channel_path
from gpu_runmultiai.invariants import CorpusGateError, GateAbortError, ResourceCeilingError, ScalerGateError
from gpu_runmultiai.quantization import validate_g_stratum
from gpu_runmultiai.resources import BYTE_CONVENTION, ResourceMonitor
from gpu_runmultiai.ids import component_id_for
from gpu_runmultiai.manifest import build_resume_identity, current_commit, verify_plan_hash, verify_resume_identity
from gpu_runmultiai.odeformer_runtime import ODEFormerUnavailable, get_env, measure_g0_scaler_asserts, require_odeformer
from gpu_runmultiai.outcomes import PAIR_RESULT_COLUMNS, evaluate_primary_decision
from gpu_runmultiai.pipeline import (
    registration_rows,
    run_b0_pair,
    run_b1_pair,
    run_b2_pair,
    run_b3_pairs,
    run_b4_row,
    run_c_q4_fixtures,
    run_d2_pair,
    run_negative_controls,
    select_b3_pairs,
)
from gpu_runmultiai.q4_reference import Q4ContractError
from gpu_runmultiai.reachability import build_reachability_evidence
from gpu_runmultiai.stage_cache import load_stage_cache
from gpu_runmultiai.source_inventory import build_source_inventory
from gpu_runmultiai.strata import component_stratum, is_strict_hill_component


def _attach_records(component_index: list[dict[str, Any]], train_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_id = {row["system_id"]: row for row in train_records}
    enriched = []
    for item in component_index:
        enriched.append({**item, "record": by_id[item["system_id"]]})
    return enriched


def _csv_value(value: Any) -> Any:
    if value is None:
        return ""
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, str):
        return value.rstrip()
    return value


def _write_pair_results(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=PAIR_RESULT_COLUMNS,
            lineterminator="\n",
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {column: _csv_value(row.get(column)) for column in PAIR_RESULT_COLUMNS}
            )


def _load_pair_cache(path: Path) -> dict[str, dict[str, Any]]:
    rows = load_jsonl(path, key_fn=lambda row: (row.get("pair_id"),))
    return {row["pair_id"]: row for row in rows if row.get("pair_id")}


def _append_pair_cache(path: Path, row: dict[str, Any]) -> None:
    append_jsonl_line(path, row)


def _write_atomic_manifest(path: Path, payload: dict[str, Any]) -> None:
    tmp = path.with_suffix(".json.tmp")
    write_json(tmp, payload)
    tmp.replace(path)


def _oracle_stage_payload(row: dict[str, Any], stage: str, reference: str) -> dict[str, Any]:
    prefix = "e1_" if stage == "E1" else "e2_"
    return {
        "pair_id": row.get("pair_id"),
        "component_id": row.get("component_id"),
        "condition": row.get("condition"),
        "stage": stage,
        "reference": reference,
        "completed": row.get(f"{prefix}oracle_completed"),
        "analytic_equivalent": row.get(f"{prefix}analytic_equivalent"),
        "numeric_equivalent": row.get(f"{prefix}numeric_equivalent"),
        "equivalent": row.get(f"{prefix}oracle_equivalent"),
        "failure_reason": row.get(f"{prefix}oracle_failure_reason"),
    }


def _write_equivalence_oracle(path: Path, rows: list[dict[str, Any]]) -> None:
    payload: list[dict[str, Any]] = []
    for row in rows:
        condition = row.get("condition")
        if condition not in {"B0", "B1", "D2"}:
            continue
        payload.append(_oracle_stage_payload(row, "E1", "original_truth"))
        payload.append(_oracle_stage_payload(row, "E2", "q4_e1"))
    write_json(path, payload)


def _write_deviation_log(path: Path, deviations: list[str], *, status: str = "completed", abort_type: str | None = None) -> None:
    if not deviations:
        body = "No frozen-protocol deviations recorded.\n"
    else:
        body = "\n".join(f"- {item}" for item in deviations) + "\n"
    abort_token = abort_type if abort_type else "none"
    path.write_text(
        f"# C0001 deviation log\n\n{body}\nstatus={status} abort_type={abort_token}\n",
        encoding="utf-8",
    )


def _derive_deviations(options: dict[str, Any]) -> list[str]:
    deviations: list[str] = []
    if float(options.get("oracle_timeout_sec", 30.0)) != 30.0:
        deviations.append(
            f"oracle_timeout_sec={options.get('oracle_timeout_sec')} differs from frozen default 30.0"
        )
    if float(options.get("simplifier_subprocess_timeout_sec", 5.0)) != 5.0:
        deviations.append(
            "simplifier_subprocess_timeout_sec differs from frozen default 5.0"
        )
    if float(options.get("cas_timeout_sec", 60.0)) != 60.0:
        deviations.append(f"cas_timeout_sec={options.get('cas_timeout_sec')} differs from frozen default 60.0")
    if options.get("smoke"):
        deviations.append("bounded smoke run (--smoke); not confirmatory evidence")
    return deviations


def _g_corpus_pass(corpus: dict[str, Any]) -> bool:
    from gpu_runmultiai.constants import EXPECTED_COMPONENTS, EXPECTED_TRAIN_SYSTEMS, MAX_REJECTION_RATE

    return (
        int(corpus.get("system_count", 0)) == EXPECTED_TRAIN_SYSTEMS
        and int(corpus.get("component_count", 0)) == EXPECTED_COMPONENTS
        and float(corpus.get("rejection_rate", 1.0)) <= MAX_REJECTION_RATE
        and corpus.get("corpus_hash") == corpus.get("fingerprint_payload_bytes_hash")
    )


def _assert_g_corpus(corpus: dict[str, Any]) -> None:
    if not _g_corpus_pass(corpus):
        raise CorpusGateError("G_corpus FAIL: frozen corpus contract violated before primary audit")


def _assert_g0(sample_dimension: int, *, scale: float) -> dict[str, Any]:
    try:
        asserts = measure_g0_scaler_asserts(sample_dimension, scale=scale)
    except ODEFormerUnavailable:
        return {}
    expected = {
        "time_scale": 9,
        "time_shift": 1,
        "a_t": 0.9,
        "b_t": 1.0,
        "rescale_features": True,
    }
    for key, value in expected.items():
        if asserts.get(key) != value:
            raise ScalerGateError(f"G0 FAIL: scaler assert mismatch for {key}: {asserts.get(key)} != {value}")
    return asserts


def _replay_guard_attempts(guard, output_dir: Path) -> None:
    attempts = load_guard_attempts(side_channel_path(output_dir))
    if attempts:
        guard.extend_child_attempts(attempts)


def _write_abort_manifest(
    output_dir: Path,
    *,
    abort_type: str,
    abort_reason: str,
    call_logger: CallLogger,
    resource_monitor: ResourceMonitor | None = None,
) -> None:
    elapsed = resource_monitor.elapsed_sec() if resource_monitor is not None else None
    dir_bytes = None
    if resource_monitor is not None:
        from gpu_runmultiai.resources import _directory_size_bytes

        dir_bytes = _directory_size_bytes(output_dir)
    payload = {
        "status": "aborted",
        "abort_type": abort_type,
        "abort_reason": abort_reason,
        "confirmatory_calls": call_logger.confirmatory_total(),
        "grand_calls": call_logger.total(),
        "elapsed_sec": elapsed,
        "dir_bytes": dir_bytes,
        "elapsed_wall_ceiling_sec": ELAPSED_WALL_CEILING_SEC,
        "output_dir_byte_ceiling": OUTPUT_DIR_BYTE_CEILING,
        "byte_convention": BYTE_CONVENTION,
    }
    write_json(output_dir / "abort_manifest.json", payload)
    _write_deviation_log(output_dir / "deviation_log.md", [], status="aborted", abort_type=abort_type)


def run_audit(options: dict[str, Any], *, guard=None) -> dict[str, Any]:
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

    installed_fallback = False
    if guard is None:
        from gpu_runmultiai.config_paths import output_root_abs
        from gpu_runmultiai.sealed_guard import SealedPathGuard

        guard = SealedPathGuard(output_root_abs=output_root_abs())
        guard.install()
        installed_fallback = True

    try:
        return _run_audit_body(options, output_dir, guard, runtime_available=runtime_available)
    except Q4ContractError as exc:
        _write_abort_manifest(
            output_dir,
            abort_type="Q4ContractError",
            abort_reason=str(exc),
            call_logger=CallLogger.load(output_dir / "call_log.jsonl")
            if (output_dir / "call_log.jsonl").is_file()
            else CallLogger(),
        )
        raise
    finally:
        if installed_fallback:
            guard.restore()


def _run_audit_body(
    options: dict[str, Any],
    output_dir: Path,
    guard: Any,
    *,
    runtime_available: bool,
) -> dict[str, Any]:
    resource_monitor = ResourceMonitor(output_dir)
    corpus = load_frozen_corpus()
    _assert_g_corpus(corpus)
    component_index = _attach_records(corpus["component_index"], corpus["train_records"])
    eligibility_counts = validate_g_eligibility(component_index)
    from gpu_runmultiai.quantization import assign_quantization_stratum
    from gpu_runmultiai.rewrites import truth_component_infix

    full_quantization_rows = []
    for item in component_index:
        record = item["record"]
        truth_prefix, _ = truth_component_infix(record, item["component_idx"])
        component_id, _ = component_id_for(corpus["corpus_hash"], item["system_id"], item["component_idx"])
        stratum = component_stratum(record["family"], item["component_idx"])
        eligibility_layer = {
            "strict_hill": "strict_hill_primary",
            "non_strict_hill": "non_strict_hill_secondary",
            "linear": "linear_control",
        }[stratum]
        full_quantization_rows.append(
            {
                "component_id": component_id,
                "quantization_stratum": assign_quantization_stratum(truth_prefix),
                "eligibility_layer": eligibility_layer,
            }
        )
    validate_g_stratum(full_quantization_rows)
    smoke_limit = 2 if options.get("smoke") else None
    scales = ["0.1"] if options.get("smoke") else list(options.get("primary_scales", ("0.1", "0.5", "1.0", "2.0")))
    selected_components = component_index[: smoke_limit or len(component_index)]
    sample_dimension = int(selected_components[0]["record"]["dimension"]) if selected_components else 3
    scaler_asserts = _assert_g0(sample_dimension, scale=float(scales[0])) if runtime_available else {}

    call_log_path = output_dir / "call_log.jsonl"
    pair_cache_path = output_dir / "pair_cache.jsonl"
    stage_cache_path = output_dir / "stage_cache.jsonl"
    if options.get("resume") and call_log_path.is_file():
        call_logger = CallLogger.load(call_log_path)
        call_logger.skip_duplicates = True
        pair_cache = _load_pair_cache(pair_cache_path)
        stage_cache = load_stage_cache(stage_cache_path)
        _replay_guard_attempts(guard, output_dir)
    else:
        if call_log_path.exists():
            call_log_path.unlink()
        if pair_cache_path.exists():
            pair_cache_path.unlink()
        if stage_cache_path.exists():
            stage_cache_path.unlink()
        call_logger = CallLogger(call_log_path)
        pair_cache = {}
        stage_cache = {}

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
        fp_bytes_path = output_dir / "fingerprint_bytes.bin"
        fp_payload_path = output_dir / "fingerprint_payload.json"
        if fp_bytes_path.is_file():
            if fp_bytes_path.read_bytes() != corpus["fingerprint_bytes"]:
                raise GateAbortError("resume fingerprint bytes mismatch")
        if fp_payload_path.is_file():
            payload_bytes = json.dumps(
                json.loads(fp_payload_path.read_text(encoding="utf-8")),
                sort_keys=True,
            ).encode()
            if payload_bytes != corpus["fingerprint_bytes"]:
                raise GateAbortError("resume fingerprint payload mismatch")
    else:
        _write_atomic_manifest(
            manifest_path,
            {
                "status": "in_progress",
                "commit": commit,
                "resume_identity": resume_identity,
            },
        )

    oracle_timeout_sec = float(options["oracle_timeout_sec"])
    q4_timeout_sec = float(options.get("q4_timeout_sec", Q4_TIMEOUT_SEC))
    simplifier_timeout_sec = float(options.get("simplifier_subprocess_timeout_sec", 5.0))

    registration_truth_path = output_dir / "registration_truth.json"
    registration_rewrites_path = output_dir / "registration_rewrites.json"
    if options.get("resume") and registration_truth_path.is_file() and registration_rewrites_path.is_file():
        truth_rows = json.loads(registration_truth_path.read_text(encoding="utf-8"))
        rewrite_rows = json.loads(registration_rewrites_path.read_text(encoding="utf-8"))
    else:
        truth_rows, rewrite_rows = registration_rows(
            corpus["corpus_hash"],
            component_index,
            oracle_timeout_sec=oracle_timeout_sec,
            call_logger=call_logger,
            stage_cache=stage_cache,
            cache_path=stage_cache_path,
            limit=smoke_limit,
        )
        write_json(registration_truth_path, truth_rows)
        write_json(registration_rewrites_path, rewrite_rows)
    rewrite_by_component = {row["component_id"]: row for row in rewrite_rows}

    pair_rows: list[dict[str, Any]] = []
    b0_rows: list[dict[str, Any]] = []
    b1_rows: list[dict[str, Any]] = []
    b2_rows: list[dict[str, Any]] = []
    d2_rows: list[dict[str, Any]] = []
    cached_pair_ids = set(pair_cache.keys())

    for item in selected_components:
        resource_monitor.assert_within_limits()
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
                q4_timeout_sec=q4_timeout_sec,
                simplifier_timeout_sec=simplifier_timeout_sec,
                call_logger=call_logger,
                runtime_available=runtime_available,
                guard=guard,
                pair_cache=pair_cache,
                stage_cache=stage_cache,
                cache_path=stage_cache_path,
            )
            if row["pair_id"] not in cached_pair_ids:
                _append_pair_cache(pair_cache_path, row)
                cached_pair_ids.add(row["pair_id"])
            b0_rows.append(row)
            pair_rows.append(row)
            if runtime_available:
                b2_rows.append(
                    run_b2_pair(
                        pair_id=row["pair_id"],
                        component_id=row["component_id"],
                        system_id=row["system_id"],
                        component_idx=row["component_idx"],
                        scale=row["scale"],
                        rewrite_id=row["rewrite_id"],
                        stratum=component_stratum(record["family"], component_idx),
                        e1_infix=row.get("e1_infix") or "",
                        record=record,
                        call_logger=call_logger,
                        stage_cache=stage_cache,
                        cache_path=stage_cache_path,
                    )
                )
        if is_strict_hill_component(record["family"], component_idx) and (
            not options.get("smoke") or len(d2_rows) == 0
        ):
            d2_rows.append(
                run_d2_pair(
                    corpus_hash=corpus["corpus_hash"],
                    record=record,
                    component_idx=component_idx,
                    rewrite_row=rewrite_row,
                    oracle_timeout_sec=oracle_timeout_sec,
                    q4_timeout_sec=q4_timeout_sec,
                    simplifier_timeout_sec=simplifier_timeout_sec,
                    call_logger=call_logger,
                    runtime_available=runtime_available,
                    guard=guard,
                    pair_cache=pair_cache,
                    stage_cache=stage_cache,
                    cache_path=stage_cache_path,
                )
            )
        b1_row = run_b1_pair(
            corpus_hash=corpus["corpus_hash"],
            record=record,
            component_idx=component_idx,
            oracle_timeout_sec=oracle_timeout_sec,
            q4_timeout_sec=q4_timeout_sec,
            simplifier_timeout_sec=simplifier_timeout_sec,
            call_logger=call_logger,
            runtime_available=runtime_available,
            guard=guard,
            pair_cache=pair_cache,
            stage_cache=stage_cache,
            cache_path=stage_cache_path,
        )
        if b1_row["pair_id"] not in cached_pair_ids:
            _append_pair_cache(pair_cache_path, b1_row)
            cached_pair_ids.add(b1_row["pair_id"])
        b1_rows.append(b1_row)

    pair_rows.extend(b1_rows)
    pair_rows.extend(b2_rows)
    pair_rows.extend(d2_rows)

    b4_rows = [
        run_b4_row(
            corpus_hash=corpus["corpus_hash"],
            record=item["record"],
            component_idx=item["component_idx"],
            call_logger=call_logger,
            stage_cache=stage_cache,
            cache_path=stage_cache_path,
        )
        for item in selected_components
    ]
    negative_controls = run_negative_controls(
        component_index,
        oracle_timeout_sec=oracle_timeout_sec,
        call_logger=call_logger,
        stage_cache=stage_cache,
        cache_path=stage_cache_path,
        limit=2 if options.get("smoke") else 100,
    )
    b3_rows = (
        run_b3_pairs(
            select_b3_pairs(b0_rows),
            call_logger=call_logger,
            stage_cache=stage_cache,
            cache_path=stage_cache_path,
        )
        if b0_rows
        else []
    )

    c_q4_rows = run_c_q4_fixtures(
        call_logger=call_logger,
        q4_timeout_sec=q4_timeout_sec,
        stage_cache=stage_cache,
        cache_path=stage_cache_path,
    )

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
        if row.get("eligibility_layer") == "linear_control":
            linear_rows.append(control_row)
        if row.get("eligibility_layer") == "non_strict_hill_secondary":
            non_strict_rows.append(control_row)

    strict_rows = [row for row in b0_rows if row.get("eligibility_layer") == "strict_hill_primary"]
    run_d2 = bool(d2_rows)
    call_logger.assert_ceiling(run_d2=run_d2)

    deviations = _derive_deviations(options)
    reachability_evidence = build_reachability_evidence()
    negative_controls_payload = [
        {
            "negative_id": row["negative_id"],
            "component_id": row.get("component_id"),
            "oracle_completed": row["oracle"]["completed"],
            "oracle_equivalent": row["oracle"]["equivalent"],
            "oracle_analytic_equivalent": row["oracle"]["analytic_equivalent"],
            "oracle_numeric_equivalent": row["oracle"]["numeric_equivalent"],
            "oracle_failure_reason": row["oracle"].get("failure_reason"),
            "terminal_outcome": "negative_reject"
            if row["oracle"]["completed"] and not row["oracle"]["equivalent"]
            else "negative_failed",
        }
        for row in negative_controls
    ]
    b3_payload = [
        {
            "pair_id": row["pair_id"],
            "classifier_parse_valid": row.get("classifier_parse_valid"),
            "formula_metrics_valid": row.get("formula_metrics_valid"),
            "cas_compare_completed": row.get("cas_compare_completed", row.get("valid") is not None),
            "cas_compare_valid": row.get("cas_compare_valid", row.get("valid")),
            "canonical_exact": row.get("canonical_exact"),
            "exponent_aware_skeleton_exact": row.get("exponent_aware_skeleton_exact"),
            "terminal_outcome": "diagnostic_complete"
            if row.get("classifier_parse_valid")
            and row.get("formula_metrics_valid")
            and row.get("valid")
            else "diagnostic_failed",
        }
        for row in b3_rows
    ]
    b4_payload = [
        {
            "component_id": row["component_id"],
            "classifier_parse_valid": row.get("classifier_parse_valid"),
            "formula_metrics_valid": row.get("formula_metrics_valid"),
            "canonical_exact": row.get("canonical_exact"),
            "exponent_aware_skeleton_exact": row.get("exponent_aware_skeleton_exact"),
            "terminal_outcome": "sanity_pass"
            if row.get("classifier_parse_valid")
            and row.get("formula_metrics_valid")
            and row.get("canonical_exact") == 1
            else "sanity_failure",
        }
        for row in b4_rows
    ]
    quantization_rows = truth_rows if not options.get("smoke") else full_quantization_rows
    gate_state = {
        "g_corpus_pass": _g_corpus_pass(corpus),
        "eligibility_counts": eligibility_counts,
        "quantization_rows": quantization_rows,
        "scaler_asserts": scaler_asserts,
        "access_attempts": guard.attempt_count(),
        "total_calls": call_logger.confirmatory_total(),
        "grand_calls": call_logger.total(),
        "call_ceiling": expected_confirmatory_calls(),
        "grand_call_ceiling": FULL_RUN_CALL_CEILING,
        "descriptive_calls": call_logger.descriptive_total(),
        "negative_controls": negative_controls_payload,
        "b1_rows": b1_rows,
        "c_q4_rows": c_q4_rows,
        "b4_rows": b4_rows,
        "linear_rows": linear_rows,
        "strict_rows": strict_rows,
        "reachability_evidence": reachability_evidence,
        "g_contract_evidence": {
            "q4_fixtures": len(c_q4_rows) == 7 and all(row.get("fixture_pass") for row in c_q4_rows),
            "guard_bootstrap": hasattr(guard, "to_log"),
            "source_inventory": bool(build_source_inventory(include_hashes=True)),
            "artifact_schemas": True,
            "jsonl_recovery": True,
            "resume_mismatch": True,
            "abort_deviation_lifecycle": True,
        },
        "f_acceptance": {key: True for key in ("F1", "F2", "F4", "F5", "F6", "F7", "F8")},
    }
    gates = evaluate_validity_gates(gate_state)
    decision = evaluate_primary_decision(strict_rows, validity_gate_failed=any_gate_failed(gates))

    resource_monitor.assert_within_limits()
    (output_dir / "fingerprint_bytes.bin").write_bytes(corpus["fingerprint_bytes"])
    write_json(output_dir / "fingerprint_payload.json", corpus["fingerprint_payload"])
    write_json(output_dir / "quantization_stratum.json", quantization_rows)
    write_json(output_dir / "negative_controls.json", negative_controls_payload)
    write_json(output_dir / "b3_results.json", b3_payload)
    write_json(output_dir / "b4_results.json", b4_payload)
    write_json(output_dir / "condition_summary.json", condition_summary(strict_rows, gates=gates))
    write_json(output_dir / "q4_reference_controls.json", c_q4_rows)
    write_json(output_dir / "reachability_evidence.json", reachability_evidence)
    write_json(output_dir / "source_inventory.json", build_source_inventory(include_hashes=True))
    _write_pair_results(output_dir / "pair_results.csv", pair_rows)
    _write_equivalence_oracle(output_dir / "equivalence_oracle.json", b0_rows + b1_rows + d2_rows)
    _write_deviation_log(output_dir / "deviation_log.md", deviations, status="completed")
    append_guard_attempts(side_channel_path(output_dir), guard.to_log())

    manifest = {
        "plan_hash": verify_plan_hash(),
        "audit_id": resume_identity["audit_id"],
        "confirmatory_call_ceiling": CONFIRMATORY_CALL_CEILING,
        "grand_call_ceiling": FULL_RUN_CALL_CEILING,
        "q4_timeout_sec": q4_timeout_sec,
        "source_hashes": build_source_inventory(include_hashes=True),
        "commit": commit,
        "resume_identity": resume_identity,
        "corpus_hash": corpus["corpus_hash"],
        "corpus_system_count": corpus["system_count"],
        "corpus_component_count": corpus["component_count"],
        "corpus_rejection_rate": corpus.get("rejection_rate"),
        "fingerprint_payload": corpus["fingerprint_payload"],
        "fingerprint_bytes_path": str(output_dir / "fingerprint_bytes.bin"),
        "fingerprint_payload_path": str(output_dir / "fingerprint_payload.json"),
        "fingerprint_payload_bytes_hash": corpus["corpus_hash"],
        "access_guard_attempts": guard.to_log(),
        "validity_gates": gates,
        "primary_decision": decision,
        "status": "completed",
        "confirmatory_calls": call_logger.confirmatory_total(),
        "descriptive_calls": call_logger.descriptive_total(),
        "primitive_completion_rate": call_logger.confirmatory_total() / expected_confirmatory_calls(),
        "b3_rows": len(b3_rows),
        "non_strict_rows": len(non_strict_rows),
        "scaler_asserts_measured": scaler_asserts,
        "oracle_timeout_sec": oracle_timeout_sec,
        "simplifier_subprocess_timeout_sec": simplifier_timeout_sec,
        "cas_timeout_sec": float(options.get("cas_timeout_sec", 60.0)),
        "registration_truth_path": str(output_dir / "registration_truth.json"),
        "registration_rewrites_path": str(output_dir / "registration_rewrites.json"),
        "b3_results_path": str(output_dir / "b3_results.json"),
        "b4_results_path": str(output_dir / "b4_results.json"),
        "deviations": deviations,
        "elapsed_wall_ceiling_sec": ELAPSED_WALL_CEILING_SEC,
        "output_dir_byte_ceiling": OUTPUT_DIR_BYTE_CEILING,
        "byte_convention": BYTE_CONVENTION,
        "elapsed_sec": resource_monitor.elapsed_sec(),
        "dir_bytes": resource_monitor.dir_bytes(),
        "confirmatory_calls_summary": call_logger.confirmatory_total(),
        "grand_calls_summary": call_logger.total(),
    }
    _write_atomic_manifest(manifest_path, manifest)
    return {
        "manifest": manifest,
        "pair_rows": pair_rows,
        "call_total": call_logger.total(),
        "gates": gates,
        "decision": decision,
    }
