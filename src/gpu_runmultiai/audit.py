"""C0001 metric-identifiability audit orchestrator."""

from __future__ import annotations

import csv
import hashlib
import json
import os
from pathlib import Path
from typing import Any

from experiment_runtime import REPO_ROOT
from gpu_run2_runtime import utc_now, write_json
from gpu_runmultiai.constants import (
    CONFIRMATORY_CALL_CEILING,
    ELAPSED_WALL_CEILING_SEC,
    FULL_RUN_CALL_CEILING,
    OUTPUT_DIR_BYTE_CEILING,
    Q4_TIMEOUT_SEC,
)
from gpu_runmultiai.eligibility import validate_g_eligibility
from gpu_runmultiai.jsonl_durable import append_jsonl_line, load_jsonl
from gpu_runmultiai.calls import CallLogger, expected_confirmatory_calls, expected_descriptive_calls
from gpu_runmultiai.contract_evidence import (
    contract_evidence_payload,
    evaluate_f_acceptance,
    evaluate_g_contract_checks,
    validate_output_artifact_schemas,
)
from gpu_runmultiai.controls import (
    any_gate_failed,
    condition_summary,
    evaluate_validity_gates,
    first_abort_gate,
)
from gpu_runmultiai.corpus import load_frozen_corpus
from gpu_runmultiai.guard_side_channel import (
    append_guard_attempts,
    ensure_guard_side_channel,
    load_guard_attempts,
    side_channel_path,
)
from gpu_runmultiai.invariants import (
    AuditInvariantError,
    ContractEvidenceError,
    CorpusGateError,
    EligibilityGateError,
    ExponentTokenError,
    FrozenEnvironmentError,
    GateAbortError,
    ResourceCeilingError,
    ResumeCacheMissError,
    ResumeIdentityError,
    ScalerGateError,
    StratumGateError,
    TerminalVocabularyError,
)
from gpu_runmultiai.quantization import validate_g_stratum
from gpu_runmultiai.resources import BYTE_CONVENTION, ResourceMonitor, _directory_size_bytes
from gpu_runmultiai.ids import component_id_for
from gpu_runmultiai.manifest import (
    build_resume_identity,
    current_commit,
    dependency_versions,
    frozen_environment,
    normalize_cli_args,
    repo_relative_path,
    require_accepted_closure_for_execution,
    runtime_provenance,
    verify_accepted_closure_source_hashes,
    verify_clean_worktree,
    verify_fingerprint_artifacts,
    verify_plan_hash,
    verify_resume_identity,
)
from gpu_runmultiai.odeformer_runtime import ODEFormerUnavailable, get_env, measure_g0_scaler_asserts, require_odeformer
from gpu_runmultiai.outcomes import (
    PAIR_RESULT_COLUMNS,
    assert_terminal_vocabulary,
    eligibility_layer_for_stratum,
    evaluate_primary_decision,
)
from gpu_runmultiai.pipeline import (
    b2_inherited_e1_fields,
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

from gpu_runmultiai.calls import PRIMITIVE_TABLE
from gpu_runmultiai.constants import (
    AUDIT_CAS_SUBSET_SEED,
    AUDIT_DATA_SEED,
    AUDIT_NEGATIVE_SEED,
    AUDIT_REWRITE_SEED,
    AUDIT_TRAJECTORY_SEED,
)

MANIFEST_STATUSES = ("initializing", "running", "completed", "aborted")

ABORT_MANIFEST_REQUIRED_FIELDS = (
    "abort_reason",
    "abort_type",
    "abort_utc",
    "elapsed_sec",
    "output_dir_bytes",
    "confirmatory_calls",
    "grand_calls",
    "last_durable_call_key",
    "last_durable_cache_key",
)


def _global_abort_error_types() -> tuple[type[BaseException], ...]:
    from scripts.phases.guard_bootstrap import GuardBootstrapViolation

    return (
        AuditInvariantError,
        ResumeCacheMissError,
        CorpusGateError,
        ScalerGateError,
        EligibilityGateError,
        StratumGateError,
        ResourceCeilingError,
        GateAbortError,
        Q4ContractError,
        ExponentTokenError,
        FrozenEnvironmentError,
        GuardBootstrapViolation,
        ResumeIdentityError,
        TerminalVocabularyError,
        ContractEvidenceError,
        ODEFormerUnavailable,
    )


class ArtifactWriter:
    """Centralized artifact writes with immediate pre/post resource checks (§8.5)."""

    def __init__(self, resource_monitor: ResourceMonitor) -> None:
        self._resource_monitor = resource_monitor

    def write_json(self, path: Path, payload: Any) -> None:
        self._resource_monitor.assert_within_limits()
        write_json(path, payload)
        self._resource_monitor.assert_within_limits()

    def write_bytes(self, path: Path, payload: bytes) -> None:
        self._resource_monitor.assert_within_limits()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
        self._resource_monitor.assert_within_limits()

    def write_pair_results(self, path: Path, rows: list[dict[str, Any]]) -> None:
        self._resource_monitor.assert_within_limits()
        _write_pair_results(path, rows)
        self._resource_monitor.assert_within_limits()

    def append_pair_cache(self, path: Path, row: dict[str, Any]) -> None:
        self._resource_monitor.assert_within_limits()
        _append_pair_cache(path, row)
        self._resource_monitor.assert_within_limits()

    def append_guard_attempts(self, path: Path, attempts: list[dict[str, str]]) -> None:
        self._resource_monitor.assert_within_limits()
        append_guard_attempts(path, attempts)
        self._resource_monitor.assert_within_limits()

    def append_deviation_entry(self, path: Path, entry: tuple[str, str, str, str, str, str]) -> None:
        self._resource_monitor.assert_within_limits()
        append_deviation_entry(path, entry)
        self._resource_monitor.assert_within_limits()

    def finalize_deviation_log(self, path: Path, *, status: str, abort_type: str | None) -> None:
        self._resource_monitor.assert_within_limits()
        finalize_deviation_log(path, status=status, abort_type=abort_type)
        self._resource_monitor.assert_within_limits()

    def write_atomic_manifest(self, path: Path, payload: dict[str, Any]) -> None:
        self._resource_monitor.assert_within_limits()
        _write_atomic_manifest(path, payload)
        self._resource_monitor.assert_within_limits()


def _select_smoke_components(component_index: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Bounded validation: include one d=1 and one live d=3 multi-component system."""
    by_dimension: dict[int, list[dict[str, Any]]] = {}
    for item in component_index:
        by_dimension.setdefault(int(item["record"]["dimension"]), []).append(item)
    selected: list[dict[str, Any]] = []
    if 1 in by_dimension:
        selected.append(by_dimension[1][0])
    if 3 in by_dimension:
        selected.append(by_dimension[3][0])
    if len(selected) < 2:
        selected = component_index[:2]
    return selected


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


def _pair_cache_key(condition: str, pair_id: str) -> tuple[str, str]:
    return (condition, pair_id)


def _load_pair_cache(path: Path) -> dict[tuple[str, str], dict[str, Any]]:
    rows = load_jsonl(
        path,
        key_fn=lambda row: (row.get("condition"), row.get("pair_id")),
    )
    return {
        (str(row["condition"]), str(row["pair_id"])): row
        for row in rows
        if row.get("pair_id") and row.get("condition")
    }


def _append_pair_cache(path: Path, row: dict[str, Any]) -> None:
    append_jsonl_line(path, row)


def _write_atomic_manifest(path: Path, payload: dict[str, Any]) -> None:
    """§12.7 atomic replacement: write a temp file then os.replace."""
    if payload.get("status") not in MANIFEST_STATUSES:
        raise GateAbortError(f"illegal manifest status {payload.get('status')!r}")
    tmp = path.with_suffix(".json.tmp")
    write_json(tmp, payload)
    os.replace(tmp, path)


def _last_durable_jsonl_row(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    last: dict[str, Any] | None = None
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            last = json.loads(line)
        except json.JSONDecodeError:
            continue
    return last


def _last_durable_call_key(path: Path) -> list[str] | None:
    row = _last_durable_jsonl_row(path)
    if not row:
        return None
    try:
        return [
            str(row["primitive"]),
            str(row["condition"]),
            str(row["stage"]),
            str(row["unit_type"]),
            str(row["unit_id"]),
        ]
    except KeyError:
        return None


def _last_durable_cache_key(path: Path) -> str | None:
    row = _last_durable_jsonl_row(path)
    if not row:
        return None
    key = row.get("cache_key")
    return str(key) if key else None


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


# --------------------------------------------------------------------------- #
# §12.7 deviation log lifecycle
# --------------------------------------------------------------------------- #

DEVIATION_LOG_HEADER = "# C0001 deviation log\n\n"


def init_deviation_log(path: Path) -> None:
    """Create the deviation log at run start (status=initializing)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        handle.write(DEVIATION_LOG_HEADER)
        handle.flush()
        os.fsync(handle.fileno())


def build_deviation_entry(
    *,
    description: str,
    scientific_impact: str,
    resolution: str,
    approval_reference: str | None = None,
    utc: str | None = None,
) -> tuple[str, str, str, str, str, str]:
    """§12.7 six-field deviation entry."""
    timestamp = utc or utc_now()
    deviation_id = "deviation_sha256:" + hashlib.sha256(description.encode("utf-8")).hexdigest()
    return (
        timestamp,
        deviation_id,
        description,
        scientific_impact,
        resolution,
        approval_reference or "none",
    )


def append_deviation_entry(path: Path, entry: tuple[str, str, str, str, str, str]) -> None:
    if len(entry) != 6:
        raise GateAbortError(f"deviation entry must have six fields, got {len(entry)}")
    line = "- " + " | ".join(str(field) for field in entry) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(line)
        handle.flush()
        os.fsync(handle.fileno())


def finalize_deviation_log(path: Path, *, status: str, abort_type: str | None) -> None:
    if not path.is_file():
        init_deviation_log(path)
    body = path.read_text(encoding="utf-8")
    if "No frozen-protocol deviations recorded." not in body and not body.strip().endswith("---"):
        if not any(line.startswith("- ") for line in body.splitlines()):
            with path.open("a", encoding="utf-8") as handle:
                handle.write("No frozen-protocol deviations recorded.\n")
                handle.flush()
                os.fsync(handle.fileno())
    with path.open("a", encoding="utf-8") as handle:
        handle.write(f"\nstatus={status} abort_type={abort_type or 'none'}\n")
        handle.flush()
        os.fsync(handle.fileno())


def _derive_deviation_entries(options: dict[str, Any]) -> list[tuple[str, str, str, str, str, str]]:
    entries: list[tuple[str, str, str, str, str, str]] = []
    if float(options.get("oracle_timeout_sec", 30.0)) != 30.0:
        entries.append(
            build_deviation_entry(
                description=f"oracle_timeout_sec={options.get('oracle_timeout_sec')} differs from frozen 30.0",
                scientific_impact="undecidable",
                resolution="unresolved",
            )
        )
    if float(options.get("simplifier_subprocess_timeout_sec", 5.0)) != 5.0:
        entries.append(
            build_deviation_entry(
                description="simplifier_subprocess_timeout_sec differs from frozen 5.0",
                scientific_impact="undecidable",
                resolution="unresolved",
            )
        )
    if float(options.get("cas_timeout_sec", 60.0)) != 60.0:
        entries.append(
            build_deviation_entry(
                description=f"cas_timeout_sec={options.get('cas_timeout_sec')} differs from frozen 60.0",
                scientific_impact="undecidable",
                resolution="unresolved",
            )
        )
    if options.get("smoke"):
        entries.append(
            build_deviation_entry(
                description="bounded smoke run (--smoke): reduced component/scale grid",
                scientific_impact="none for primary decision; run is not confirmatory evidence",
                resolution="full confirmatory run required after independent review",
            )
        )
    return entries


def write_abort_manifest(
    output_dir: Path,
    *,
    abort_type: str,
    abort_reason: str,
    call_logger: CallLogger,
    resource_monitor: ResourceMonitor | None = None,
) -> dict[str, Any]:
    """§12.7 abort manifest with all frozen fields and durable last keys."""
    payload = {
        "status": "aborted",
        "abort_type": abort_type,
        "abort_reason": abort_reason,
        "abort_utc": utc_now(),
        "elapsed_sec": resource_monitor.elapsed_sec() if resource_monitor is not None else None,
        "output_dir_bytes": _directory_size_bytes(Path(output_dir)),
        "confirmatory_calls": call_logger.confirmatory_total(),
        "grand_calls": call_logger.total(),
        "last_durable_call_key": _last_durable_call_key(Path(output_dir) / "call_log.jsonl"),
        "last_durable_cache_key": _last_durable_cache_key(Path(output_dir) / "stage_cache.jsonl"),
        "elapsed_wall_ceiling_sec": ELAPSED_WALL_CEILING_SEC,
        "output_dir_byte_ceiling": OUTPUT_DIR_BYTE_CEILING,
        "byte_convention": BYTE_CONVENTION,
    }
    write_json(Path(output_dir) / "abort_manifest.json", payload)
    return payload


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


def _require_installed_guard(guard: Any) -> Any:
    from scripts.phases.guard_bootstrap import GuardBootstrapViolation, get_installed_guard

    if guard is None:
        raise GuardBootstrapViolation(
            "run_audit requires the guard_bootstrap singleton handle returned by "
            "install_guard_from_entry; no replacement guard is permitted"
        )
    installed = get_installed_guard()
    if installed is not guard:
        raise GuardBootstrapViolation(
            "guard handle passed to run_audit is not the installed bootstrap singleton"
        )
    return installed


def run_audit(options: dict[str, Any], *, guard=None) -> dict[str, Any]:
    verify_plan_hash()
    output_dir = Path(options["output_dir"]).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    if options.get("fail_if_exists") and any(output_dir.iterdir()) and not options.get("resume"):
        raise RuntimeError(f"output directory already exists: {output_dir}")

    resource_monitor = ResourceMonitor(output_dir)
    manifest_path = output_dir / "audit_manifest.json"
    deviation_path = output_dir / "deviation_log.md"
    context: dict[str, Any] = {"call_logger": None}

    if not options.get("resume"):
        _write_atomic_manifest(
            manifest_path,
            {
                "status": "initializing",
                "audit_id": options.get("audit_id"),
                "plan_hash": verify_plan_hash(),
                "started_utc": utc_now(),
            },
        )
        init_deviation_log(deviation_path)

    try:
        guard = _require_installed_guard(guard)
        runtime_available = True
        try:
            require_odeformer()
            get_env()
        except ODEFormerUnavailable:
            runtime_available = False
            if not options.get("smoke"):
                raise
        return _run_audit_body(
            options,
            output_dir,
            guard,
            runtime_available=runtime_available,
            resource_monitor=resource_monitor,
            context=context,
        )
    except (KeyboardInterrupt, SystemExit):
        raise
    except BaseException as exc:
        _handle_global_abort(
            output_dir,
            exc=exc,
            resource_monitor=resource_monitor,
            context=context,
            manifest_path=manifest_path,
            deviation_path=deviation_path,
        )
        raise


def _handle_global_abort(
    output_dir: Path,
    *,
    exc: BaseException,
    resource_monitor: ResourceMonitor,
    context: dict[str, Any],
    manifest_path: Path,
    deviation_path: Path,
) -> None:
    """Route every global abort through initializing → running → aborted (§12.7)."""
    call_logger = context.get("call_logger")
    if call_logger is None:
        call_log_path = output_dir / "call_log.jsonl"
        try:
            call_logger = CallLogger.load(call_log_path) if call_log_path.is_file() else CallLogger()
        except Exception:
            call_logger = CallLogger()
    abort_type = type(exc).__name__
    abort_payload = write_abort_manifest(
        output_dir,
        abort_type=abort_type,
        abort_reason=str(exc),
        call_logger=call_logger,
        resource_monitor=resource_monitor,
    )
    append_deviation_entry(
        deviation_path,
        build_deviation_entry(
            description=f"global abort {abort_type}: {exc}",
            scientific_impact="undecidable",
            resolution="unresolved",
        ),
    )
    finalize_deviation_log(deviation_path, status="aborted", abort_type=abort_type)
    existing: dict[str, Any] = {}
    if manifest_path.is_file():
        try:
            existing = json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            existing = {}
    existing.update(
        {
            "status": "aborted",
            "abort_type": abort_type,
            "abort_reason": str(exc),
            "abort_utc": abort_payload["abort_utc"],
            "abort_manifest_path": repo_relative_path(output_dir / "abort_manifest.json"),
        }
    )
    _write_atomic_manifest(manifest_path, existing)


def _run_audit_body(
    options: dict[str, Any],
    output_dir: Path,
    guard: Any,
    *,
    runtime_available: bool,
    resource_monitor: ResourceMonitor,
    context: dict[str, Any],
) -> dict[str, Any]:
    manifest_path = output_dir / "audit_manifest.json"
    deviation_path = output_dir / "deviation_log.md"
    artifacts = ArtifactWriter(resource_monitor)
    if options.get("require_clean_worktree", True):
        worktree_provenance = verify_clean_worktree()
    else:
        worktree_provenance = {"clean": "skipped_for_unit_test"}
    ensure_guard_side_channel(side_channel_path(output_dir))

    corpus = load_frozen_corpus()
    _assert_g_corpus(corpus)
    component_index = _attach_records(corpus["component_index"], corpus["train_records"])
    eligibility_counts = validate_g_eligibility(component_index)
    from gpu_runmultiai.quantization import assign_quantization_stratum
    from gpu_runmultiai.rewrites import truth_component_infix

    quantization_artifact_rows = []
    for item in component_index:
        record = item["record"]
        truth_prefix, _ = truth_component_infix(record, item["component_idx"])
        component_id, _ = component_id_for(corpus["corpus_hash"], item["system_id"], item["component_idx"])
        stratum = component_stratum(record["family"], item["component_idx"])
        quantization_artifact_rows.append(
            {
                "component_id": component_id,
                "quantization_stratum": assign_quantization_stratum(truth_prefix),
                "eligibility_layer": eligibility_layer_for_stratum(stratum),
            }
        )
    validate_g_stratum(quantization_artifact_rows)
    smoke_limit = 2 if options.get("smoke") else None
    scales = ["0.1"] if options.get("smoke") else list(options.get("primary_scales", ("0.1", "0.5", "1.0", "2.0")))
    selected_components = (
        _select_smoke_components(component_index)
        if options.get("smoke")
        else component_index[: smoke_limit or len(component_index)]
    )
    sample_dimension = int(selected_components[0]["record"]["dimension"]) if selected_components else 3
    scaler_asserts = _assert_g0(sample_dimension, scale=float(scales[0])) if runtime_available else {}

    call_log_path = output_dir / "call_log.jsonl"
    pair_cache_path = output_dir / "pair_cache.jsonl"
    stage_cache_path = output_dir / "stage_cache.jsonl"
    if options.get("resume") and call_log_path.is_file():
        call_logger = CallLogger.load(call_log_path, resource_monitor=resource_monitor)
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
        call_logger = CallLogger(call_log_path, resource_monitor=resource_monitor)
        pair_cache = {}
        stage_cache = {}
    context["call_logger"] = call_logger

    commit = current_commit()
    script_path = REPO_ROOT / "scripts/phases/gpu_runmultiai_c0001_metric_audit.py"
    resume_identity = build_resume_identity(
        commit=commit,
        audit_script_path=script_path,
        corpus_hash=corpus["corpus_hash"],
        cli_args=options,
        output_dir=output_dir,
    )
    source_inventory = build_source_inventory(include_hashes=True)
    if options.get("resume") or not options.get("smoke"):
        closure_hash_status = require_accepted_closure_for_execution(
            commit, source_inventory, output_dir=output_dir
        )
    else:
        closure_hash_status = verify_accepted_closure_source_hashes(
            source_inventory, output_dir=output_dir
        )
    if options.get("resume"):
        existing_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        verify_resume_identity(existing_manifest.get("resume_identity", {}), resume_identity)
        verify_fingerprint_artifacts(
            output_dir,
            fingerprint_bytes=corpus["fingerprint_bytes"],
            manifest_payload=existing_manifest.get("fingerprint_payload"),
        )

    # §12.7: counted primitives run under status=running.
    _write_atomic_manifest(
        manifest_path,
        {
            "status": "running",
            "audit_id": resume_identity["audit_id"],
            "plan_hash": resume_identity["plan_hash"],
            "commit": commit,
            "resume_identity": resume_identity,
            "fingerprint_payload": corpus["fingerprint_payload"],
            "accepted_closure_source_hash_status": closure_hash_status,
            "worktree_provenance": worktree_provenance,
            "started_utc": utc_now(),
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
        registration_index = (
            selected_components if options.get("smoke") else component_index[: smoke_limit or len(component_index)]
        )
        truth_rows, rewrite_rows = registration_rows(
            corpus["corpus_hash"],
            registration_index,
            oracle_timeout_sec=oracle_timeout_sec,
            call_logger=call_logger,
            stage_cache=stage_cache,
            cache_path=stage_cache_path,
            limit=None,
        )
        artifacts.write_json(registration_truth_path, truth_rows)
        artifacts.write_json(registration_rewrites_path, rewrite_rows)
    rewrite_by_component = {row["component_id"]: row for row in rewrite_rows}

    pair_rows: list[dict[str, Any]] = []
    b0_rows: list[dict[str, Any]] = []
    b1_rows: list[dict[str, Any]] = []
    b2_rows: list[dict[str, Any]] = []
    d2_rows: list[dict[str, Any]] = []
    cached_pair_keys = set(pair_cache.keys())
    b2_result_cache: dict[str, dict[str, Any]] = {
        pair_id: row for (condition, pair_id), row in pair_cache.items() if condition == "B2"
    }

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
            b0_key = _pair_cache_key("B0", row["pair_id"])
            if b0_key not in cached_pair_keys:
                artifacts.append_pair_cache(pair_cache_path, row)
                pair_cache[b0_key] = row
                cached_pair_keys.add(b0_key)
            b0_rows.append(row)
            pair_rows.append(row)
            if runtime_available:
                if row["pair_id"] in b2_result_cache:
                    b2_row = b2_result_cache[row["pair_id"]]
                else:
                    b2_row = run_b2_pair(
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
                        e1_fields=b2_inherited_e1_fields(row),
                        stage_cache=stage_cache,
                        cache_path=stage_cache_path,
                        result_cache=b2_result_cache,
                    )
                    b2_key = _pair_cache_key("B2", row["pair_id"])
                    if b2_key not in cached_pair_keys:
                        artifacts.append_pair_cache(pair_cache_path, b2_row)
                        pair_cache[b2_key] = b2_row
                        cached_pair_keys.add(b2_key)
                b2_rows.append(b2_row)
        if is_strict_hill_component(record["family"], component_idx) and (
            not options.get("smoke") or len(d2_rows) == 0
        ):
            d2_row = run_d2_pair(
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
            d2_rows.append(d2_row)
            d2_key = _pair_cache_key("D2", d2_row["pair_id"])
            if d2_key not in cached_pair_keys:
                artifacts.append_pair_cache(pair_cache_path, d2_row)
                pair_cache[d2_key] = d2_row
                cached_pair_keys.add(d2_key)
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
        b1_key = _pair_cache_key("B1", b1_row["pair_id"])
        if b1_key not in cached_pair_keys:
            artifacts.append_pair_cache(pair_cache_path, b1_row)
            pair_cache[b1_key] = b1_row
            cached_pair_keys.add(b1_key)
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
        selected_components if options.get("smoke") else component_index,
        oracle_timeout_sec=oracle_timeout_sec,
        call_logger=call_logger,
        corpus_hash=corpus["corpus_hash"],
        stage_cache=stage_cache,
        cache_path=stage_cache_path,
        limit=len(selected_components) if options.get("smoke") else 100,
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

    deviation_entries = _derive_deviation_entries(options)
    for entry in deviation_entries:
        artifacts.append_deviation_entry(deviation_path, entry)
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
            "partition_scope": "negative_control",
            "terminal_outcome": "negative_reject"
            if row["oracle"]["completed"] and not row["oracle"]["equivalent"]
            else "negative_failed",
        }
        for row in negative_controls
    ]
    b3_payload = [
        {
            "pair_id": row["pair_id"],
            "component_id": row.get("component_id"),
            "partition_scope": "diagnostic",
            "classifier_parse_valid": row.get("classifier_parse_valid"),
            "formula_metrics_valid": row.get("formula_metrics_valid"),
            "cas_compare_completed": row.get("cas_compare_completed"),
            "cas_compare_valid": row.get("cas_compare_valid"),
            "canonical_exact": row.get("canonical_exact"),
            "exponent_aware_skeleton_exact": row.get("exponent_aware_skeleton_exact"),
            "failure_reason": row.get("failure_reason"),
            "terminal_outcome": row.get("terminal_outcome"),
        }
        for row in b3_rows
    ]
    b4_payload = [
        {
            "component_id": row["component_id"],
            "partition_scope": "metric_sanity",
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
    c_q4_payload = [
        {
            **row,
            "partition_scope": "q4_fixture",
            "terminal_outcome": "fixture_pass" if row.get("fixture_pass") else "fixture_failure",
        }
        for row in c_q4_rows
    ]

    # Whole-artifact terminal vocabulary invariants (§2.5.2): no illegal or unknown terminals.
    assert_terminal_vocabulary(pair_rows, context="pair_results.csv")
    assert_terminal_vocabulary(b3_payload, terminal_key="terminal_outcome", context="b3_results.json")
    assert_terminal_vocabulary(b4_payload, terminal_key="terminal_outcome", context="b4_results.json")
    assert_terminal_vocabulary(
        negative_controls_payload, terminal_key="terminal_outcome", context="negative_controls.json"
    )
    assert_terminal_vocabulary(
        c_q4_payload, terminal_key="terminal_outcome", context="q4_reference_controls.json"
    )

    g_contract_rows = evaluate_g_contract_checks(guard=guard, c_q4_rows=c_q4_rows)
    f_acceptance_rows = evaluate_f_acceptance(b0_rows=b0_rows, b1_rows=b1_rows, b2_rows=b2_rows)
    gate_state = {
        "g_corpus_pass": _g_corpus_pass(corpus),
        "eligibility_counts": eligibility_counts,
        "quantization_rows": quantization_artifact_rows,
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
        "g_contract_evidence": {row["check_key"]: row["passed"] for row in g_contract_rows},
        "f_acceptance": {row["requirement_id"]: row["passed"] for row in f_acceptance_rows},
    }
    gates = evaluate_validity_gates(gate_state)
    if options.get("smoke") and not runtime_available:
        # Bounded smoke without ODEFormer cannot measure G0; do not abort on it.
        gates["G0"] = True
    decision = evaluate_primary_decision(strict_rows, validity_gate_failed=any_gate_failed(gates))
    abort_gate = first_abort_gate(gates)
    if abort_gate is not None:
        raise GateAbortError(f"{abort_gate} FAIL: abort-disposition validity gate failed")

    artifacts.write_bytes(output_dir / "fingerprint_bytes.bin", corpus["fingerprint_bytes"])
    artifacts.write_bytes(output_dir / "fingerprint_payload.json", corpus["fingerprint_bytes"])
    artifacts.write_json(output_dir / "quantization_stratum.json", quantization_artifact_rows)
    artifacts.write_json(output_dir / "negative_controls.json", negative_controls_payload)
    artifacts.write_json(output_dir / "b3_results.json", b3_payload)
    artifacts.write_json(output_dir / "b4_results.json", b4_payload)
    artifacts.write_json(
        output_dir / "condition_summary.json",
        condition_summary(
            strict_rows,
            gates=gates,
            confirmatory_calls=call_logger.confirmatory_total(),
            descriptive_calls=call_logger.descriptive_total(),
        ),
    )
    artifacts.write_json(output_dir / "q4_reference_controls.json", c_q4_payload)
    artifacts.write_json(output_dir / "reachability_evidence.json", reachability_evidence)
    artifacts.write_json(
        output_dir / "contract_evidence.json",
        contract_evidence_payload(
            g_contract_rows=g_contract_rows, f_acceptance_rows=f_acceptance_rows
        ),
    )
    artifacts.write_json(output_dir / "source_inventory.json", source_inventory)
    artifacts.write_pair_results(output_dir / "pair_results.csv", pair_rows)
    artifacts.write_json(
        output_dir / "equivalence_oracle.json",
        [
            _oracle_stage_payload(row, "E1", "original_truth")
            for row in b0_rows + b1_rows + d2_rows
        ]
        + [
            _oracle_stage_payload(row, "E2", "q4_e1")
            for row in b0_rows + b1_rows + d2_rows
        ],
    )
    artifacts.append_guard_attempts(side_channel_path(output_dir), guard.to_log())
    schema_ok, schema_detail = validate_output_artifact_schemas(output_dir)
    if not schema_ok:
        raise GateAbortError(f"produced artifact schema validation failed: {schema_detail}")
    artifacts.finalize_deviation_log(deviation_path, status="completed", abort_type=None)

    manifest = {
        "status": "completed",
        "audit_id": resume_identity["audit_id"],
        "plan_hash": verify_plan_hash(),
        "commit": commit,
        "resume_identity": resume_identity,
        "seeds": {
            "audit_data_seed": AUDIT_DATA_SEED,
            "audit_trajectory_seed": AUDIT_TRAJECTORY_SEED,
            "audit_rewrite_seed": AUDIT_REWRITE_SEED,
            "audit_negative_seed": AUDIT_NEGATIVE_SEED,
            "audit_cas_subset_seed": AUDIT_CAS_SUBSET_SEED,
        },
        "corpus_hash": corpus["corpus_hash"],
        "corpus_system_count": corpus["system_count"],
        "corpus_component_count": corpus["component_count"],
        "corpus_rejection_rate": corpus.get("rejection_rate"),
        "fingerprint_payload": corpus["fingerprint_payload"],
        "fingerprint_bytes_path": repo_relative_path(output_dir / "fingerprint_bytes.bin"),
        "fingerprint_payload_path": repo_relative_path(output_dir / "fingerprint_payload.json"),
        "fingerprint_payload_bytes_hash": corpus["corpus_hash"],
        "source_hashes": source_inventory,
        "accepted_closure_source_hash_status": closure_hash_status,
        "access_guard_attempts": guard.to_log(),
        "confirmatory_call_ceiling": CONFIRMATORY_CALL_CEILING,
        "grand_call_ceiling": FULL_RUN_CALL_CEILING,
        "elapsed_wall_ceiling_sec": ELAPSED_WALL_CEILING_SEC,
        "output_dir_byte_ceiling": OUTPUT_DIR_BYTE_CEILING,
        "byte_convention": BYTE_CONVENTION,
        "primitive_table": PRIMITIVE_TABLE,
        "cli_args_normalized": normalize_cli_args(options),
        "dependency_versions": dependency_versions(),
        "environment": frozen_environment(),
        "runtime_provenance": runtime_provenance(),
        "oracle_timeout_sec": oracle_timeout_sec,
        "q4_timeout_sec": q4_timeout_sec,
        "simplifier_subprocess_timeout_sec": simplifier_timeout_sec,
        "cas_timeout_sec": float(options.get("cas_timeout_sec", 60.0)),
        "validity_gates": gates,
        "primary_decision": decision,
        "confirmatory_calls": call_logger.confirmatory_total(),
        "descriptive_calls": call_logger.descriptive_total(),
        "grand_calls": call_logger.total(),
        "descriptive_call_ceiling": expected_descriptive_calls(),
        "primitive_completion_rate": call_logger.confirmatory_total() / expected_confirmatory_calls(),
        "g_contract_evidence": gate_state["g_contract_evidence"],
        "f_acceptance": gate_state["f_acceptance"],
        "contract_evidence_path": repo_relative_path(output_dir / "contract_evidence.json"),
        "b3_rows": len(b3_rows),
        "non_strict_rows": len(non_strict_rows),
        "scaler_asserts_measured": scaler_asserts,
        "registration_truth_path": repo_relative_path(registration_truth_path),
        "registration_rewrites_path": repo_relative_path(registration_rewrites_path),
        "b3_results_path": repo_relative_path(output_dir / "b3_results.json"),
        "b4_results_path": repo_relative_path(output_dir / "b4_results.json"),
        "deviations": ["- " + " | ".join(entry) for entry in deviation_entries],
        "elapsed_sec": resource_monitor.elapsed_sec(),
        "dir_bytes": resource_monitor.dir_bytes(),
        "completed_utc": utc_now(),
    }
    manifest["worktree_provenance"] = worktree_provenance
    artifacts.write_atomic_manifest(manifest_path, manifest)
    return {
        "manifest": manifest,
        "pair_rows": pair_rows,
        "call_total": call_logger.total(),
        "gates": gates,
        "decision": decision,
        "contract_evidence": {
            "g_contract": g_contract_rows,
            "f_acceptance": f_acceptance_rows,
        },
    }
