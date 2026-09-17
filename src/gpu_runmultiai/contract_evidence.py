"""Executable G_contract and F-acceptance evidence (preregistration v16 §10.1, §16).

Every row in this module is produced by running the checked behaviour in-process.
No acceptance value may be a literal; a check that cannot be executed is reported as
``passed=False`` with the failure recorded in ``details``.

None of these checks appends a counted call to the ledger (§10 note, §8.1).
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any, Callable

from experiment_runtime import REPO_ROOT

from gpu_runmultiai.constants import PRIMARY_SCALES, Q4_TIMEOUT_SEC, SIMPLIFIER_SUBPROCESS_TIMEOUT_SEC
from gpu_runmultiai.invariants import AuditInvariantError, ResumeIdentityError
from gpu_runmultiai.outcomes import FIVE_OUTCOME_CATEGORIES, compute_b2_expected_outcome
from gpu_runmultiai.pipeline import b2_inherited_e1_fields
from gpu_runmultiai.q4_reference import (
    Q4ContractError,
    audit_q4_decimal_round_reference,
    verify_q4_emitted_prefix,
)
from gpu_runmultiai.source_inventory import build_source_inventory, enumerate_source_inventory_paths

G_CONTRACT_CHECK_KEYS = (
    "q4_fixtures",
    "guard_bootstrap",
    "source_inventory",
    "artifact_schemas",
    "jsonl_recovery",
    "resume_mismatch",
    "abort_deviation_lifecycle",
)

F_ACCEPTANCE_IDS = ("F1", "F2", "F4", "F5", "F6", "F7", "F8")

# §12.8 required row keys per artifact.
ARTIFACT_ROW_SCHEMAS: dict[str, tuple[str, ...]] = {
    "registration_truth.json": (
        "component_id",
        "system_id",
        "component_idx",
        "truth_infix",
        "truth_prefix",
        "eligibility_layer",
        "classifier_parse_valid",
        "hill_form",
        "component_flags",
    ),
    "registration_rewrites.json": (
        "component_id",
        "rewrite_id",
        "rewrite_prefix",
        "rewrite_infix",
        "precheck_completed",
        "precheck_equivalent",
        "precheck_failure_reason",
    ),
    "quantization_stratum.json": ("component_id", "quantization_stratum"),
    "q4_reference_controls.json": (
        "fixture_id",
        "e1_prefix_input",
        "q4_construction_completed",
        "q4_emitted_prefix",
        "q4_emitted_infix",
        "q4_sympy_expr_canonical",
        "fixture_pass",
        "fixture_specific_assertions_pass",
        "q4_construction_failure_reason",
        "terminal_outcome",
    ),
    "negative_controls.json": (
        "negative_id",
        "component_id",
        "oracle_completed",
        "oracle_equivalent",
        "oracle_analytic_equivalent",
        "oracle_numeric_equivalent",
        "oracle_failure_reason",
        "terminal_outcome",
    ),
    "b3_results.json": (
        "pair_id",
        "classifier_parse_valid",
        "formula_metrics_valid",
        "cas_compare_completed",
        "cas_compare_valid",
        "canonical_exact",
        "exponent_aware_skeleton_exact",
        "terminal_outcome",
    ),
    "b4_results.json": (
        "component_id",
        "classifier_parse_valid",
        "formula_metrics_valid",
        "canonical_exact",
        "exponent_aware_skeleton_exact",
        "terminal_outcome",
    ),
    "reachability_evidence.json": ("fixture_id", "evidence_type", "passed", "details"),
    "equivalence_oracle.json": (
        "pair_id",
        "component_id",
        "condition",
        "stage",
        "reference",
        "completed",
        "analytic_equivalent",
        "numeric_equivalent",
        "equivalent",
        "failure_reason",
    ),
    "guard_attempts_side_channel.jsonl": (
        "attempted_operation",
        "attempted_path_norm",
        "attempted_path_real",
    ),
    "condition_summary.json": (
        "confirmatory_calls",
        "descriptive_calls",
        "primary_partition_counts",
        "diagnostic_coverage_rate",
        "validity_gates",
    ),
}

_SCHEMA_SAMPLE_ROWS: dict[str, Any] = {
    "registration_truth.json": {
        "component_id": "component_sha256:" + "0" * 64,
        "system_id": "R01_train_d61001_000",
        "component_idx": 0,
        "truth_infix": "(x_0)",
        "truth_prefix": "x_0",
        "eligibility_layer": "strict_hill_primary",
        "classifier_parse_valid": True,
        "hill_form": True,
        "component_flags": [{"hill_form": True}],
    },
    "registration_rewrites.json": {
        "component_id": "component_sha256:" + "0" * 64,
        "rewrite_id": "rewrite_sha256:" + "1" * 64,
        "rewrite_prefix": "div,mul,2,x_0,2",
        "rewrite_infix": "((2*(x_0))/2)",
        "precheck_completed": True,
        "precheck_equivalent": True,
        "precheck_failure_reason": None,
    },
    "quantization_stratum.json": {
        "component_id": "component_sha256:" + "0" * 64,
        "quantization_stratum": "quantization_neutral",
    },
    "q4_reference_controls.json": {
        "fixture_id": "q4_fixture_01",
        "e1_prefix_input": "mul,0.04598,x_0",
        "q4_construction_completed": True,
        "q4_emitted_prefix": "mul,0.0460,x_0",
        "q4_emitted_infix": "((0.0460)*(x_0))",
        "q4_sympy_expr_canonical": "0.046*x_0",
        "fixture_pass": True,
        "fixture_specific_assertions_pass": True,
        "q4_construction_failure_reason": None,
        "terminal_outcome": "fixture_pass",
    },
    "negative_controls.json": {
        "negative_id": "negative_sha256:" + "2" * 64,
        "component_id": "component_sha256:" + "0" * 64,
        "oracle_completed": True,
        "oracle_equivalent": False,
        "oracle_analytic_equivalent": False,
        "oracle_numeric_equivalent": False,
        "oracle_failure_reason": None,
        "terminal_outcome": "negative_reject",
    },
    "b3_results.json": {
        "pair_id": "pair_sha256:" + "3" * 64,
        "classifier_parse_valid": True,
        "formula_metrics_valid": True,
        "cas_compare_completed": True,
        "cas_compare_valid": True,
        "canonical_exact": 1.0,
        "exponent_aware_skeleton_exact": 1.0,
        "terminal_outcome": "diagnostic_complete",
    },
    "b4_results.json": {
        "component_id": "component_sha256:" + "0" * 64,
        "classifier_parse_valid": True,
        "formula_metrics_valid": True,
        "canonical_exact": 1.0,
        "exponent_aware_skeleton_exact": 1.0,
        "terminal_outcome": "sanity_pass",
    },
    "reachability_evidence.json": {
        "fixture_id": "REACH-PRESERVED-1",
        "evidence_type": "hand_algebraic",
        "passed": True,
        "details": "e1=True q4=True e2=True hill=True",
    },
    "equivalence_oracle.json": {
        "pair_id": "pair_sha256:" + "3" * 64,
        "component_id": "component_sha256:" + "0" * 64,
        "condition": "B0",
        "stage": "E1",
        "reference": "original_truth",
        "completed": True,
        "analytic_equivalent": True,
        "numeric_equivalent": True,
        "equivalent": True,
        "failure_reason": None,
    },
    "guard_attempts_side_channel.jsonl": {
        "attempted_operation": "open",
        "attempted_path_norm": "/tmp/norm",
        "attempted_path_real": "/tmp/real",
    },
    "condition_summary.json": {
        "confirmatory_calls": 0,
        "descriptive_calls": 0,
        "primary_partition_counts": {name: 0 for name in FIVE_OUTCOME_CATEGORIES},
        "diagnostic_coverage_rate": 0.0,
        "validity_gates": {"G_corpus": True},
    },
}


def _row(check_key: str, requirement: str, passed: bool, details: str) -> dict[str, Any]:
    return {
        "check_key": check_key,
        "requirement": requirement,
        "passed": bool(passed),
        "details": details,
    }


def _guarded(check_key: str, requirement: str, fn: Callable[[], tuple[bool, str]]) -> dict[str, Any]:
    try:
        passed, details = fn()
    except Exception as exc:  # evidence must record, never mask, its own failure
        return _row(check_key, requirement, False, f"{type(exc).__name__}: {exc}")
    return _row(check_key, requirement, passed, details)


def _expect_raises(exc_type: type[BaseException], fn: Callable[[], Any]) -> bool:
    try:
        fn()
    except exc_type:
        return True
    except Exception:
        return False
    return False


# --------------------------------------------------------------------------- #
# G_contract §10.1
# --------------------------------------------------------------------------- #


def _check_q4_fixtures(c_q4_rows: list[dict[str, Any]]) -> tuple[bool, str]:
    expected_prefix = {
        "q4_fixture_03": "add,x_0,add,x_1,x_2",
        "q4_fixture_04": "mul,2,mul,x_0,x_1",
        "q4_fixture_07": "mul,mul,1,pow,3,-1,x_0",
    }
    expected_token = {"q4_fixture_01": "0.0460", "q4_fixture_06": "0.3333"}
    by_id = {row.get("fixture_id"): row for row in c_q4_rows}
    problems: list[str] = []
    if len(c_q4_rows) != 7:
        problems.append(f"fixture_count={len(c_q4_rows)}")
    for row in c_q4_rows:
        if not row.get("fixture_pass"):
            problems.append(f"{row.get('fixture_id')}:not_pass")
        if row.get("terminal_outcome") not in {"fixture_pass", "fixture_failure"}:
            problems.append(f"{row.get('fixture_id')}:terminal={row.get('terminal_outcome')}")
    for fixture_id, prefix in expected_prefix.items():
        emitted = (by_id.get(fixture_id) or {}).get("q4_emitted_prefix")
        if emitted != prefix:
            problems.append(f"{fixture_id}:emit={emitted!r}!={prefix!r}")
    for fixture_id, token in expected_token.items():
        emitted = (by_id.get(fixture_id) or {}).get("q4_emitted_prefix") or ""
        if token not in emitted:
            problems.append(f"{fixture_id}:token{token}_absent")
    rational_canonical = (by_id.get("q4_fixture_07") or {}).get("q4_sympy_expr_canonical") or ""
    if "0.3333" in rational_canonical:
        problems.append("q4_fixture_07:float_leaked")
    if not _expect_raises(Q4ContractError, lambda: verify_q4_emitted_prefix("foobar,x_0")):
        problems.append("Q4ContractError_path_not_raised")
    if not _expect_raises(Q4ContractError, lambda: verify_q4_emitted_prefix("add,x_0")):
        problems.append("Q4ContractError_arity_path_not_raised")
    return not problems, "ok" if not problems else "; ".join(problems)


def _guard_install_before_package_imports(source: str, *, entry_main_only: bool = False) -> bool:
    block = source
    if entry_main_only:
        marker = "def main("
        start = source.find(marker)
        if start < 0:
            return False
        block = source[start:]
    install_line = -1
    first_package_import = -1
    for index, line in enumerate(block.splitlines()):
        stripped = line.strip()
        if "install_guard_from_entry" in stripped and install_line < 0:
            install_line = index
        if stripped.startswith(("from gpu_runmultiai", "import gpu_runmultiai")):
            if first_package_import < 0:
                first_package_import = index
    if install_line < 0:
        return False
    if first_package_import < 0:
        return True
    return install_line < first_package_import


def _check_guard_import_order() -> tuple[bool, str]:
    problems: list[str] = []
    entry = REPO_ROOT / "scripts/phases/gpu_runmultiai_c0001_metric_audit.py"
    worker = REPO_ROOT / "src/gpu_runmultiai/simplifier_worker.py"
    if not _guard_install_before_package_imports(entry.read_text(encoding="utf-8"), entry_main_only=True):
        problems.append(f"{entry}:guard_must_install_before_package_imports")
    if not _guard_install_before_package_imports(worker.read_text(encoding="utf-8")):
        problems.append(f"{worker}:guard_must_install_before_package_imports")
    return not problems, "ok" if not problems else "; ".join(problems)


def _check_guard_bootstrap(guard: Any) -> tuple[bool, str]:
    from scripts.phases import guard_bootstrap as gb

    problems: list[str] = []
    import_ok, import_detail = _check_guard_import_order()
    if not import_ok:
        problems.append(import_detail)
    installed = gb.get_installed_guard()
    if installed is not guard:
        problems.append("singleton_identity_mismatch")
    if not _expect_raises(
        gb.GuardBootstrapViolation,
        lambda: gb.install_guard_from_entry(
            str(REPO_ROOT / "scripts/phases/gpu_runmultiai_c0001_metric_audit.py")
        ),
    ):
        problems.append("replacement_install_not_rejected")
    if len(guard.to_log()) != len(guard.attempts):
        problems.append("g4_ledger_not_from_parent_handle")

    # Deny matcher, attempt ledger, and child merge are exercised on an isolated
    # temporary root so the parent (G4) ledger is never polluted.
    with tempfile.TemporaryDirectory(prefix="c0001_guard_") as tmp:
        tmp_root = Path(tmp)
        output_root = tmp_root / "results" / "runs"
        denied = output_root / "gpu_run5_probe" / "test" / "rows.json"
        denied.parent.mkdir(parents=True, exist_ok=True)
        denied.write_text("[]", encoding="utf-8")
        allowed = output_root / "gpu_run5_probe" / "phase7" / "rows.json"
        allowed.parent.mkdir(parents=True, exist_ok=True)
        allowed.write_text("[]", encoding="utf-8")
        probe = gb.BootstrapGuardHandle(
            repo_root=str(tmp_root), output_root_abs=str(output_root)
        )
        if not probe.is_denied(denied, denied):
            problems.append("deny_matcher_missed_sealed_dir")
        if probe.is_denied(allowed, allowed):
            problems.append("deny_matcher_false_positive")
        probe.install()
        try:
            if not _expect_raises(PermissionError, lambda: open(denied, encoding="utf-8")):
                problems.append("deny_did_not_block")
        finally:
            probe.restore()
        if probe.attempt_count() != 1:
            problems.append(f"attempt_ledger={probe.attempt_count()}")
        probe.extend_child_attempts(
            [
                {
                    "attempted_operation": "open",
                    "attempted_path_norm": str(denied),
                    "attempted_path_real": str(denied),
                }
            ]
        )
        if probe.attempt_count() != 2:
            problems.append("child_side_channel_merge_failed")
    return not problems, "ok" if not problems else "; ".join(problems)


def _check_source_inventory() -> tuple[bool, str]:
    from gpu_run2_runtime import sha256_file

    paths = enumerate_source_inventory_paths()
    problems: list[str] = []
    if paths != sorted(paths):
        problems.append("inventory_not_sorted")
    if len(paths) != len(set(paths)):
        problems.append("inventory_has_duplicates")
    if "scripts/phases/guard_bootstrap.py" not in paths:
        problems.append("guard_bootstrap_absent")
    if "third_party/odeformer/parsers.py" not in paths:
        problems.append("odeformer_parsers_absent")
    for module in sorted((REPO_ROOT / "src/gpu_runmultiai").glob("*.py")):
        rel = str(module.relative_to(REPO_ROOT))
        if rel not in paths:
            problems.append(f"missing:{rel}")
    inventory = build_source_inventory(include_hashes=True)
    if [entry["path"] for entry in inventory] != paths:
        problems.append("inventory_path_order_mismatch")
    mismatched = [
        entry["path"]
        for entry in inventory
        if entry.get("sha256") != sha256_file(REPO_ROOT / entry["path"])
    ]
    if mismatched:
        problems.append(f"hash_mismatch:{mismatched[:3]}")
    detail = f"paths={len(paths)} hashes={len(inventory)}"
    return not problems, detail if not problems else f"{detail}; " + "; ".join(problems)


def validate_output_artifact_schemas(output_dir: Path) -> tuple[bool, str]:
    from gpu_runmultiai.guard_side_channel import load_guard_attempts

    problems: list[str] = []
    root = Path(output_dir)

    def _validate_loaded(artifact: str, required: tuple[str, ...], loaded: dict[str, Any]) -> None:
        missing = [key for key in required if key not in loaded]
        if missing:
            problems.append(f"{artifact}:missing={missing}")

    for artifact, required in ARTIFACT_ROW_SCHEMAS.items():
        path = root / artifact
        if artifact == "guard_attempts_side_channel.jsonl":
            if not path.is_file():
                problems.append(f"{artifact}:absent")
                continue
            rows = load_guard_attempts(path)
            if rows:
                _validate_loaded(artifact, required, rows[0])
            continue
        if not path.is_file():
            problems.append(f"{artifact}:absent")
            continue
        if artifact == "condition_summary.json":
            loaded = json.loads(path.read_text(encoding="utf-8"))
            _validate_loaded(artifact, required, loaded)
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        rows = payload if isinstance(payload, list) else [payload]
        if not rows:
            problems.append(f"{artifact}:empty")
            continue
        _validate_loaded(artifact, required, rows[0])
    detail = f"output_artifacts={len(ARTIFACT_ROW_SCHEMAS)}"
    return not problems, detail if not problems else f"{detail}; " + "; ".join(problems)


def _check_artifact_schemas() -> tuple[bool, str]:
    from gpu_run2_runtime import write_json
    from gpu_runmultiai.guard_side_channel import (
        append_guard_attempts,
        ensure_guard_side_channel,
        load_guard_attempts,
    )

    problems: list[str] = []

    with tempfile.TemporaryDirectory(prefix="c0001_schema_") as tmp:
        tmp_dir = Path(tmp)
        for artifact, required in ARTIFACT_ROW_SCHEMAS.items():
            sample = _SCHEMA_SAMPLE_ROWS[artifact]
            path = tmp_dir / artifact
            if artifact.endswith(".jsonl"):
                ensure_guard_side_channel(path)
                append_guard_attempts(path, [sample])
                loaded_rows = load_guard_attempts(path)
                loaded = loaded_rows[0] if loaded_rows else {}
            elif artifact == "condition_summary.json":
                write_json(path, sample)
                loaded = json.loads(path.read_text(encoding="utf-8"))
            else:
                write_json(path, [sample])
                payload = json.loads(path.read_text(encoding="utf-8"))
                loaded = payload[0] if payload else {}
            missing = [key for key in required if key not in loaded]
            if missing:
                problems.append(f"{artifact}:round_trip_missing={missing}")
            elif any(loaded[key] != sample[key] for key in required):
                problems.append(f"{artifact}:round_trip_value_drift")
    detail = f"schemas={len(ARTIFACT_ROW_SCHEMAS)}"
    return not problems, detail if not problems else f"{detail}; " + "; ".join(problems)


def _check_jsonl_recovery() -> tuple[bool, str]:
    from gpu_runmultiai.jsonl_durable import load_jsonl, truncate_partial_suffix

    problems: list[str] = []
    with tempfile.TemporaryDirectory(prefix="c0001_jsonl_") as tmp:
        tmp_dir = Path(tmp)
        partial = tmp_dir / "call_log.jsonl"
        partial.write_bytes(b'{"a": 1}\n{"b": 2,')
        truncate_partial_suffix(partial)
        if partial.read_bytes() != b'{"a": 1}\n':
            problems.append("partial_suffix_not_truncated")
        if load_jsonl(partial) != [{"a": 1}]:
            problems.append("recovered_rows_mismatch")

        malformed = tmp_dir / "malformed.jsonl"
        malformed.write_text('{"a": 1}\n{bad}\n', encoding="utf-8")
        if not _expect_raises(AuditInvariantError, lambda: load_jsonl(malformed)):
            problems.append("malformed_line_not_aborted")

        duplicate = tmp_dir / "duplicate.jsonl"
        duplicate.write_text('{"k": 1}\n{"k": 1}\n', encoding="utf-8")
        if not _expect_raises(
            AuditInvariantError,
            lambda: load_jsonl(duplicate, key_fn=lambda row: (row.get("k"),)),
        ):
            problems.append("duplicate_key_not_aborted")
    return not problems, "ok" if not problems else "; ".join(problems)


def _check_resume_mismatch() -> tuple[bool, str]:
    from gpu_runmultiai.manifest import verify_fingerprint_artifacts, verify_resume_identity

    baseline = {
        "audit_id": "c0001_metric_identifiability_audit_v16",
        "commit": "a" * 40,
        "plan_hash": "b" * 64,
        "audit_script_hash": "c" * 64,
        "config_hash": "d" * 64,
        "source_hashes": [{"path": "src/gpu_runmultiai/audit.py", "sha256": "e" * 64}],
        "corpus_hash": "f" * 64,
        "fingerprint_payload_path": "out/fingerprint_payload.json",
        "fingerprint_bytes_path": "out/fingerprint_bytes.bin",
        "fingerprint_payload_bytes_hash": "f" * 64,
        "seeds": {"audit_data_seed": 61001},
        "primitive_table": [{"id": "P1"}],
        "cli_args_normalized": {"allow_cpu": True},
        "oracle_timeout_sec": 30.0,
        "q4_timeout_sec": 10.0,
        "simplifier_subprocess_timeout_sec": 5.0,
        "cas_timeout_sec": 60.0,
        "confirmatory_call_ceiling": 27637,
        "grand_call_ceiling": 30277,
        "dependency_versions": {"python": "3.10.20", "scikit-learn": "1.7.2", "numexpr": "2.14.1"},
        "environment": {"LANSR_TED_TIMEOUT_SEC": "10"},
        "runtime_provenance": {"os": "linux", "cpu": "x86_64"},
    }
    problems: list[str] = []
    verify_resume_identity(baseline, dict(baseline))
    for key, mutated in (
        ("fingerprint_payload_bytes_hash", "0" * 64),
        ("corpus_hash", "1" * 64),
        ("dependency_versions", {"python": "3.11.0"}),
        ("source_hashes", [{"path": "src/gpu_runmultiai/audit.py", "sha256": "9" * 64}]),
        ("commit", "9" * 40),
    ):
        current = {**baseline, key: mutated}
        if not _expect_raises(
            ResumeIdentityError, lambda: verify_resume_identity(baseline, current)
        ):
            problems.append(f"mismatch_not_aborted:{key}")

    payload = {"corpus": "fixture"}
    payload_bytes = json.dumps(payload, sort_keys=True).encode()
    with tempfile.TemporaryDirectory(prefix="c0001_resume_") as tmp:
        tmp_dir = Path(tmp)
        if not _expect_raises(
            ResumeIdentityError,
            lambda: verify_fingerprint_artifacts(
                tmp_dir, fingerprint_bytes=payload_bytes, manifest_payload=payload
            ),
        ):
            problems.append("missing_fingerprint_files_not_aborted")
        (tmp_dir / "fingerprint_bytes.bin").write_bytes(payload_bytes)
        (tmp_dir / "fingerprint_payload.json").write_text(
            json.dumps(payload, sort_keys=True), encoding="utf-8"
        )
        verify_fingerprint_artifacts(
            tmp_dir, fingerprint_bytes=payload_bytes, manifest_payload=payload
        )
        if not _expect_raises(
            ResumeIdentityError,
            lambda: verify_fingerprint_artifacts(
                tmp_dir, fingerprint_bytes=b"different", manifest_payload=payload
            ),
        ):
            problems.append("fingerprint_bytes_mismatch_not_aborted")
        if not _expect_raises(
            ResumeIdentityError,
            lambda: verify_fingerprint_artifacts(
                tmp_dir, fingerprint_bytes=payload_bytes, manifest_payload={"corpus": "other"}
            ),
        ):
            problems.append("fingerprint_payload_dict_mismatch_not_aborted")
    return not problems, "ok" if not problems else "; ".join(problems)


def _check_abort_deviation_lifecycle() -> tuple[bool, str]:
    from gpu_runmultiai.audit import (
        ABORT_MANIFEST_REQUIRED_FIELDS,
        append_deviation_entry,
        build_deviation_entry,
        finalize_deviation_log,
        init_deviation_log,
        write_abort_manifest,
    )
    from gpu_runmultiai.calls import CallLogger

    problems: list[str] = []
    with tempfile.TemporaryDirectory(prefix="c0001_abort_") as tmp:
        tmp_dir = Path(tmp)
        deviation_path = tmp_dir / "deviation_log.md"
        init_deviation_log(deviation_path)
        if not deviation_path.is_file():
            problems.append("deviation_log_not_created")
        entry = build_deviation_entry(
            description="contract lifecycle probe",
            scientific_impact="none",
            resolution="probe only",
        )
        if len(entry) != 6:
            problems.append(f"deviation_entry_fields={len(entry)}")
        append_deviation_entry(deviation_path, entry)
        write_abort_manifest(
            tmp_dir,
            abort_type="Q4ContractError",
            abort_reason="contract lifecycle probe",
            call_logger=CallLogger(),
        )
        finalize_deviation_log(deviation_path, status="aborted", abort_type="Q4ContractError")
        abort = json.loads((tmp_dir / "abort_manifest.json").read_text(encoding="utf-8"))
        missing = [field for field in ABORT_MANIFEST_REQUIRED_FIELDS if field not in abort]
        if missing:
            problems.append(f"abort_manifest_missing={missing}")
        body = deviation_path.read_text(encoding="utf-8")
        if body.count("|") < 5:
            problems.append("deviation_entry_not_six_field")
        if not body.rstrip().endswith("status=aborted abort_type=Q4ContractError"):
            problems.append("deviation_log_not_finalized")

        completed_path = tmp_dir / "deviation_log_completed.md"
        init_deviation_log(completed_path)
        finalize_deviation_log(completed_path, status="completed", abort_type=None)
        if not completed_path.read_text(encoding="utf-8").rstrip().endswith(
            "status=completed abort_type=none"
        ):
            problems.append("completed_finalize_line_wrong")
    return not problems, "ok" if not problems else "; ".join(problems)


def evaluate_g_contract_checks(
    *,
    guard: Any,
    c_q4_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Run all seven §10.1 G_contract checks and return persisted evidence rows."""
    return [
        _guarded("q4_fixtures", "§10.1-1 C_q4 7/7 and Q4ContractError path", lambda: _check_q4_fixtures(c_q4_rows)),
        _guarded("guard_bootstrap", "§10.1-2 guard bootstrap ordering/singleton/ledger", lambda: _check_guard_bootstrap(guard)),
        _guarded("source_inventory", "§10.1-3 §13.2 sorted inventory recomputes", _check_source_inventory),
        _guarded(
            "artifact_schemas",
            "§10.1-4 §12.8 schema round-trips",
            _check_artifact_schemas,
        ),
        _guarded("jsonl_recovery", "§10.1-5 JSONL truncate/malformed/duplicate", _check_jsonl_recovery),
        _guarded("resume_mismatch", "§10.1-6 resume identity and fingerprint mismatch abort", _check_resume_mismatch),
        _guarded("abort_deviation_lifecycle", "§10.1-7 abort manifest and deviation lifecycle", _check_abort_deviation_lifecycle),
    ]


# --------------------------------------------------------------------------- #
# G_impl F-acceptance §16
# --------------------------------------------------------------------------- #


def _execute_primary_scale_b0_rows() -> tuple[dict[str, dict[str, Any]], list[str]]:
    from pathlib import Path

    from gpu_runmultiai.calls import CallLogger
    from gpu_runmultiai.corpus import load_frozen_corpus
    from gpu_runmultiai.odeformer_runtime import ODEFormerUnavailable, require_odeformer
    from gpu_runmultiai.pipeline import run_b0_pair
    from gpu_runmultiai.rewrites import rewrite_registration, truth_component_infix
    from gpu_runmultiai.sealed_guard import SealedPathGuard

    problems: list[str] = []
    rows_by_scale: dict[str, dict[str, Any]] = {}
    try:
        require_odeformer()
    except ODEFormerUnavailable as exc:
        return {}, [f"odeformer_unavailable:{exc}"]
    corpus = load_frozen_corpus()
    record = next(row for row in corpus["train_records"] if row["system_id"] == "R01_train_d61001_000")
    truth_prefix, truth_infix = truth_component_infix(record, 0)
    rewrite = rewrite_registration(
        "R01_train_d61001_000", 0, truth_prefix, truth_infix, oracle_timeout_sec=30.0
    )
    guard = SealedPathGuard(output_root_abs=Path("/nonexistent/results/runs"))
    for scale in PRIMARY_SCALES:
        row = run_b0_pair(
            corpus_hash=corpus["corpus_hash"],
            record=record,
            component_idx=0,
            scale=scale,
            rewrite_row=rewrite,
            oracle_timeout_sec=30.0,
            q4_timeout_sec=Q4_TIMEOUT_SEC,
            simplifier_timeout_sec=SIMPLIFIER_SUBPROCESS_TIMEOUT_SEC,
            call_logger=CallLogger(),
            runtime_available=True,
            guard=guard,
        )
        rows_by_scale[scale] = row
        if not row.get("e1_analytic_equivalent") or not row.get("e1_numeric_equivalent"):
            problems.append(f"scale={scale}:e1_not_equivalent")
        prefix = row.get("e0_prefix_raw") or ""
        if "pow" not in prefix:
            problems.append(f"scale={scale}:e0_missing_rational_reciprocal")
    return rows_by_scale, problems


def _f1_e0_rational_forward(b0_rows: list[dict[str, Any]]) -> tuple[bool, str]:
    from gpu_runmultiai.odeformer_runtime import _rational_reciprocal_factor_prefix

    problems: list[str] = []
    factor = _rational_reciprocal_factor_prefix("0.1", "0.9")
    if factor != ["mul", "0.1", "pow", "0.9", "-1"]:
        problems.append(f"reciprocal_not_rational:{factor}")
    executed, exec_problems = _execute_primary_scale_b0_rows()
    problems.extend(exec_problems)
    missing_scales = [scale for scale in PRIMARY_SCALES if scale not in executed]
    if missing_scales:
        problems.append(f"missing_primary_scales={missing_scales}")
    detail = f"executed_scales={sorted(executed)} persisted_scales={sorted({str(row.get('scale')) for row in b0_rows})}"
    return not problems, detail if not problems else f"{detail}; " + "; ".join(problems[:8])


def _f2_compound_pow_arity() -> tuple[bool, str]:
    from gpu_runmultiai.oracle import audit_parse_prefix_component

    problems: list[str] = []
    prefix = "pow2,div,mul,10.0,x_0,10.0"
    tree = audit_parse_prefix_component(prefix)
    if tree is None:
        problems.append("parse_failed")
    else:
        if tree[0] != "pow" or len(tree[1]) != 2:
            problems.append(f"root={tree[0]}/{len(tree[1])}")
        elif tree[1][0][0] != "div" or len(tree[1][0][1]) != 2:
            problems.append("div_subtree_arity_lost")
        elif tree[1][0][1][0][0] != "mul" or len(tree[1][0][1][0][1]) != 2:
            problems.append("mul_subtree_arity_lost")
    q4 = audit_q4_decimal_round_reference(prefix, timeout_sec=Q4_TIMEOUT_SEC)
    if not q4.q4_construction_completed:
        problems.append(f"q4_failed:{q4.q4_construction_failure_reason}")
    elif audit_parse_prefix_component(q4.q4_emitted_prefix or "") is None:
        problems.append("q4_emit_not_reparseable")
    return not problems, "ok" if not problems else "; ".join(problems)


def _f4_round_trip_acceptance(b0_rows: list[dict[str, Any]]) -> tuple[bool, str]:
    problems: list[str] = []
    executed, exec_problems = _execute_primary_scale_b0_rows()
    problems.extend(exec_problems)
    for scale in PRIMARY_SCALES:
        row = executed.get(scale)
        if row is None:
            problems.append(f"scale={scale}:not_executed")
            continue
        if not (
            row.get("e1_oracle_completed")
            and row.get("e1_oracle_equivalent")
            and row.get("e1_analytic_equivalent") is True
            and row.get("e1_numeric_equivalent") is True
        ):
            problems.append(f"scale={scale}:e1_round_trip_failed")
    detail = f"executed_scales={sorted(executed)} persisted_scales={sorted({str(row.get('scale')) for row in b0_rows})}"
    return not problems, detail if not problems else f"{detail}; " + "; ".join(problems[:8])


def _f5_b1_production_rescale(b1_rows: list[dict[str, Any]]) -> tuple[bool, str]:
    from gpu_runmultiai.odeformer_runtime import (
        PRODUCTION_RESCALE_QUALNAME,
        PRODUCTION_SCALER_MODULE,
    )

    problems: list[str] = []
    if not b1_rows:
        problems.append("no_b1_rows")
    for row in b1_rows:
        proof = row.get("rescale_call_proof") or {}
        if proof.get("rescale_callable_module") != PRODUCTION_SCALER_MODULE:
            problems.append(f"{row.get('pair_id')}:module={proof.get('rescale_callable_module')}")
            continue
        if proof.get("rescale_callable_qualname") != PRODUCTION_RESCALE_QUALNAME:
            problems.append(f"{row.get('pair_id')}:qualname={proof.get('rescale_callable_qualname')}")
            continue
        if proof.get("a_t") != 1.0 or proof.get("b_t") != 0.0:
            problems.append(f"{row.get('pair_id')}:a_t={proof.get('a_t')},b_t={proof.get('b_t')}")
        if any(value != 1.0 for value in proof.get("scale", [])):
            problems.append(f"{row.get('pair_id')}:scale={proof.get('scale')}")
        if proof.get("rescale_incomplete"):
            problems.append(f"{row.get('pair_id')}:identity_return")
        if not row.get("e1_oracle_equivalent"):
            problems.append(f"{row.get('pair_id')}:e1_not_oracle_equivalent")
    detail = f"b1_rows={len(b1_rows)}"
    return not problems, detail if not problems else f"{detail}; " + "; ".join(problems[:5])


def _f6_b1_explicit_partition(b1_rows: list[dict[str, Any]]) -> tuple[bool, str]:
    allowed = {"control_pass", "control_failure"}
    problems: list[str] = []
    if len(b1_rows) != 510:
        problems.append(f"b1_population={len(b1_rows)} requires 510/510 for F6 acceptance")
    illegal = [
        f"{row.get('pair_id')}:{row.get('outcome_category')}"
        for row in b1_rows
        if row.get("outcome_category") not in allowed
    ]
    if illegal:
        problems.append(f"illegal_terminals={illegal[:5]}")
    unknown = [row.get("pair_id") for row in b1_rows if row.get("outcome_category") == "unknown"]
    if unknown:
        problems.append(f"unknown_terminals={unknown[:5]}")
    passes = sum(1 for row in b1_rows if row.get("outcome_category") == "control_pass")
    detail = f"b1_rows={len(b1_rows)} control_pass={passes}"
    return not problems, detail if not problems else f"{detail}; " + "; ".join(problems)


def _f7_b2_e1_only(
    b2_rows: list[dict[str, Any]],
    *,
    b0_rows: list[dict[str, Any]] | None = None,
) -> tuple[bool, str]:
    from gpu_runmultiai.pipeline import B2_FORBIDDEN_INHERITED_FIELDS

    forbidden_e2 = tuple(
        key for key in B2_FORBIDDEN_INHERITED_FIELDS if key.startswith("e2_")
    )
    problems: list[str] = []
    if not b2_rows:
        problems.append("no_b2_rows")
    b0_by_pair = {row["pair_id"]: row for row in (b0_rows or []) if row.get("pair_id")}
    for row in b2_rows:
        leaked = [key for key in forbidden_e2 if row.get(key) not in (None, False)]
        if leaked:
            problems.append(f"{row.get('pair_id')}:e2_leak={leaked}")
        b0_row = b0_by_pair.get(row.get("pair_id"))
        if b0_row is None:
            problems.append(f"{row.get('pair_id')}:missing_b0_source")
            continue
        expected = compute_b2_expected_outcome(
            e1_infix=b0_row.get("e1_infix") or "",
            component_idx=int(row.get("component_idx", 0)),
            e1_fields=b2_inherited_e1_fields(b0_row),
        )
        if expected != row.get("outcome_category"):
            problems.append(
                f"{row.get('pair_id')}:{row.get('outcome_category')}!=expected_from_b0_e1({expected})"
            )
        if row.get("outcome_category") not in FIVE_OUTCOME_CATEGORIES:
            problems.append(f"{row.get('pair_id')}:illegal={row.get('outcome_category')}")
    detail = f"b2_rows={len(b2_rows)} b0_sources={len(b0_by_pair)}"
    return not problems, detail if not problems else f"{detail}; " + "; ".join(problems[:5])


def _f8_shared_component_split() -> tuple[bool, str]:
    from gpu_run4.formulas import split_components as canonical_split
    from gpu_runmultiai import pipeline
    from gpu_runmultiai.oracle import extract_component_infix

    problems: list[str] = []
    if pipeline.split_components is not canonical_split:
        problems.append("pipeline_uses_local_split")
    prefix_system = "x_0|add,x_1,1|mul,2,x_2"
    parts = canonical_split(prefix_system)
    if parts != ["x_0", "add,x_1,1", "mul,2,x_2"]:
        problems.append(f"prefix_split={parts}")
    infix_system = "(x_0) | ((x_1)+(1)) | ((2)*(x_2))"
    for index, expected_symbol in enumerate(("x_0", "x_1", "x_2")):
        component = extract_component_infix(infix_system, index)
        if expected_symbol not in component:
            problems.append(f"component_{index}={component!r}")
    return not problems, "ok" if not problems else "; ".join(problems)


def evaluate_f_acceptance(
    *,
    b0_rows: list[dict[str, Any]],
    b1_rows: list[dict[str, Any]],
    b2_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Run the seven §16 F-acceptance requirements named by G_impl."""
    rows = [
        _guarded("F1", "§16 F1 exact-rational E0 forward and E1≡truth", lambda: _f1_e0_rational_forward(b0_rows)),
        _guarded("F2", "§16 F2 compound pow arity preservation", _f2_compound_pow_arity),
        _guarded("F4", "§16 F4 round-trip acceptance expects E1≡truth", lambda: _f4_round_trip_acceptance(b0_rows)),
        _guarded("F5", "§16 F5 B1 executes production rescale with identity params", lambda: _f5_b1_production_rescale(b1_rows)),
        _guarded("F6", "§16 F6 B1 explicit partition without unknown", lambda: _f6_b1_explicit_partition(b1_rows)),
        _guarded(
            "F7",
            "§16 F7 B2 decided from B0 E1-only fields",
            lambda: _f7_b2_e1_only(b2_rows, b0_rows=b0_rows),
        ),
        _guarded("F8", "§16 F8 shared `|` component split", _f8_shared_component_split),
    ]
    for row in rows:
        row["requirement_id"] = row["check_key"]
    return rows


def contract_evidence_payload(
    *,
    g_contract_rows: list[dict[str, Any]],
    f_acceptance_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "g_contract": g_contract_rows,
        "f_acceptance": f_acceptance_rows,
        "g_contract_pass": all(row["passed"] for row in g_contract_rows),
        "f_acceptance_pass": all(row["passed"] for row in f_acceptance_rows),
    }
