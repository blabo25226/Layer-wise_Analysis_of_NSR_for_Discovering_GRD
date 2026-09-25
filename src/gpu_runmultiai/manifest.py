"""Audit manifest and resume identity."""

from __future__ import annotations

import hashlib
import importlib
import json
import os
import platform
from pathlib import Path
from typing import Any

import numpy as np
import scipy

from experiment_runtime import REPO_ROOT
from gpu_run2_runtime import git_info, sha256_file, utc_now, write_json

from gpu_runmultiai.calls import PRIMITIVE_TABLE, expected_confirmatory_calls
from gpu_runmultiai.constants import (
    AUDIT_CAS_SUBSET_SEED,
    AUDIT_DATA_SEED,
    AUDIT_ID,
    AUDIT_NEGATIVE_SEED,
    AUDIT_REWRITE_SEED,
    AUDIT_TRAJECTORY_SEED,
    CAS_TIMEOUT_SEC,
    CONFIRMATORY_CALL_CEILING,
    FROZEN_ENV_VARS,
    FULL_RUN_CALL_CEILING,
    ORACLE_TIMEOUT_SEC,
    PLAN_PATH,
    PLAN_SHA256,
    Q4_TIMEOUT_SEC,
    SIMPLIFIER_SUBPROCESS_TIMEOUT_SEC,
)
from gpu_runmultiai.invariants import ResumeIdentityError
from gpu_runmultiai.source_inventory import build_source_inventory


def verify_plan_hash() -> str:
    digest = hashlib.sha256(PLAN_PATH.read_bytes()).hexdigest()
    if digest != PLAN_SHA256:
        raise RuntimeError(
            f"binding plan SHA mismatch: expected {PLAN_SHA256}, got {digest}"
        )
    return digest


def source_hashes() -> list[dict[str, str]]:
    return build_source_inventory(include_hashes=True)


def audit_script_hash(script_path: Path) -> str:
    return sha256_file(script_path)


def runtime_provenance() -> dict[str, str]:
    return {
        "os": platform.platform(),
        "cpu": platform.processor() or platform.machine(),
    }


def dependency_versions() -> dict[str, str]:
    """§12.6 dependency identity: python, numpy, scipy, sympy, scikit-learn, numexpr, torch, os, cpu."""
    versions = {
        "python": platform.python_version(),
        "numpy": np.__version__,
        "scipy": scipy.__version__,
        **runtime_provenance(),
    }
    for key, module_name in (
        ("sympy", "sympy"),
        ("scikit-learn", "sklearn"),
        ("numexpr", "numexpr"),
        ("torch", "torch"),
    ):
        try:
            module = importlib.import_module(module_name)
        except ImportError:
            versions[key] = "missing"
        else:
            versions[key] = str(getattr(module, "__version__", "unknown"))
    return versions


def frozen_environment() -> dict[str, str]:
    return {key: os.environ.get(key, "") for key in FROZEN_ENV_VARS}


def _normalize_value(value: Any) -> Any:
    if isinstance(value, tuple):
        return [_normalize_value(item) for item in value]
    if isinstance(value, list):
        return [_normalize_value(item) for item in value]
    if isinstance(value, dict):
        return {key: _normalize_value(item) for key, item in sorted(value.items())}
    return value


def normalize_cli_args(args: dict[str, Any]) -> dict[str, Any]:
    excluded = {"resume", "fail_if_exists"}
    normalized = {
        key: _normalize_value(value)
        for key, value in sorted(args.items())
        if key not in excluded
    }
    return normalized


def repo_relative_path(path: Path) -> str:
    """Checkout-independent path token: repo-relative POSIX when possible (§12.6)."""
    resolved = Path(path).resolve()
    try:
        return resolved.relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        # Paths outside the checkout (developer smoke directories) stay absolute.
        return resolved.as_posix()


def build_resume_identity(
    *,
    commit: str,
    audit_script_path: Path,
    corpus_hash: str,
    cli_args: dict[str, Any],
    output_dir: Path | None = None,
    fingerprint_artifacts_expected: bool = True,
) -> dict[str, Any]:
    fingerprint_payload_path = None
    fingerprint_bytes_path = None
    if output_dir is not None and fingerprint_artifacts_expected:
        fingerprint_payload_path = repo_relative_path(Path(output_dir) / "fingerprint_payload.json")
        fingerprint_bytes_path = repo_relative_path(Path(output_dir) / "fingerprint_bytes.bin")
    return {
        "audit_id": AUDIT_ID,
        "commit": commit,
        "plan_hash": verify_plan_hash(),
        "audit_script_hash": audit_script_hash(audit_script_path),
        "config_hash": sha256_file(REPO_ROOT / "configs/gpu_run5/base.yaml"),
        "source_hashes": source_hashes(),
        "corpus_hash": corpus_hash,
        "fingerprint_payload_path": fingerprint_payload_path,
        "fingerprint_bytes_path": fingerprint_bytes_path,
        "fingerprint_payload_bytes_hash": corpus_hash,
        "seeds": {
            "audit_data_seed": AUDIT_DATA_SEED,
            "audit_trajectory_seed": AUDIT_TRAJECTORY_SEED,
            "audit_rewrite_seed": AUDIT_REWRITE_SEED,
            "audit_negative_seed": AUDIT_NEGATIVE_SEED,
            "audit_cas_subset_seed": AUDIT_CAS_SUBSET_SEED,
        },
        "primitive_table": PRIMITIVE_TABLE,
        "cli_args_normalized": normalize_cli_args(cli_args),
        "oracle_timeout_sec": float(cli_args.get("oracle_timeout_sec", ORACLE_TIMEOUT_SEC)),
        "q4_timeout_sec": float(cli_args.get("q4_timeout_sec", Q4_TIMEOUT_SEC)),
        "simplifier_subprocess_timeout_sec": float(
            cli_args.get("simplifier_subprocess_timeout_sec", SIMPLIFIER_SUBPROCESS_TIMEOUT_SEC)
        ),
        "cas_timeout_sec": float(cli_args.get("cas_timeout_sec", CAS_TIMEOUT_SEC)),
        "dependency_versions": dependency_versions(),
        "environment": frozen_environment(),
        "runtime_provenance": runtime_provenance(),
        "confirmatory_call_ceiling": CONFIRMATORY_CALL_CEILING,
        "grand_call_ceiling": FULL_RUN_CALL_CEILING,
    }


def verify_resume_identity(existing: dict[str, Any], current: dict[str, Any]) -> None:
    keys = [
        "audit_id",
        "commit",
        "plan_hash",
        "audit_script_hash",
        "config_hash",
        "source_hashes",
        "corpus_hash",
        "fingerprint_payload_path",
        "fingerprint_bytes_path",
        "fingerprint_payload_bytes_hash",
        "seeds",
        "primitive_table",
        "cli_args_normalized",
        "oracle_timeout_sec",
        "q4_timeout_sec",
        "simplifier_subprocess_timeout_sec",
        "cas_timeout_sec",
        "confirmatory_call_ceiling",
        "grand_call_ceiling",
        "dependency_versions",
        "environment",
        "runtime_provenance",
    ]
    for key in keys:
        if existing.get(key) != current.get(key):
            raise ResumeIdentityError(f"resume identity mismatch for {key}")


FINGERPRINT_BYTES_NAME = "fingerprint_bytes.bin"
FINGERPRINT_PAYLOAD_NAME = "fingerprint_payload.json"
CLOSURE_RECORD_NAME = "implementation_closure_record.json"
PROTECTED_UNTRACKED_SMOKE = (
    "GPU_RUNmultiAI/cycles/C0001/runs/c0001_metric_identifiability_audit_v9_smoke"
)
PRESERVED_NEGATIVE_ACCEPTANCE_RUNS = (
    "GPU_RUNmultiAI/cycles/C0001/runs/c0001_metric_identifiability_audit_v16_round6_acceptance",
    "GPU_RUNmultiAI/cycles/C0001/runs/c0001_metric_identifiability_audit_v16_round6_acceptance_r2",
    "GPU_RUNmultiAI/cycles/C0001/runs/c0001_metric_identifiability_audit_v16_round6_acceptance_r3",
    "GPU_RUNmultiAI/cycles/C0001/runs/c0001_metric_identifiability_audit_v16_round7_acceptance",
)
RUNTIME_SCRATCH_DIR = "GPU_RUNmultiAI/.runtime"


def verify_clean_worktree(exclude_paths: list[str] | None = None) -> dict[str, Any]:
    """Require a clean tracked worktree; ignore protected v9 smoke, runtime scratch, and explicit excludes."""
    import subprocess

    excluded_abs: set[str] = set()
    for raw in exclude_paths or []:
        resolved = str(Path(raw).resolve())
        excluded_abs.add(resolved)
        try:
            excluded_abs.add(repo_relative_path(Path(raw)))
        except Exception:
            pass

    def _path_is_excluded(path: str) -> bool:
        resolved = str((REPO_ROOT / path).resolve())
        if path in excluded_abs or resolved in excluded_abs:
            return True
        for excluded in excluded_abs:
            if resolved == excluded or resolved.startswith(excluded.rstrip("/") + "/"):
                return True
            if path == excluded or path.startswith(excluded.rstrip("/") + "/"):
                return True
        return False

    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    ignored: list[str] = []
    violations: list[str] = []
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        path = line[3:].strip()
        if path == PROTECTED_UNTRACKED_SMOKE or path.startswith(PROTECTED_UNTRACKED_SMOKE + "/"):
            ignored.append(path)
            continue
        if path == RUNTIME_SCRATCH_DIR or path.startswith(RUNTIME_SCRATCH_DIR + "/"):
            ignored.append(path)
            continue
        resolved = str((REPO_ROOT / path).resolve())
        if _path_is_excluded(path):
            ignored.append(path)
            continue
        violations.append(line)
    if violations:
        raise ResumeIdentityError(
            "validation/full execution requires a clean tracked worktree; "
            f"dirty entries: {violations}"
        )
    return {"clean": True, "ignored_untracked": ignored, "excluded_paths": sorted(excluded_abs)}


def _artifact_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _verify_closure_artifact_digest(payload: dict[str, Any], digest_field: str, path_field: str) -> None:
    expected = payload.get(digest_field)
    rel_path = payload.get(path_field)
    if not expected or not rel_path:
        raise ResumeIdentityError(f"closure record missing {digest_field} or {path_field}")
    artifact_path = REPO_ROOT / rel_path
    if not artifact_path.is_file():
        raise ResumeIdentityError(f"closure artifact missing: {rel_path}")
    actual = _artifact_digest(artifact_path)
    if actual != expected:
        raise ResumeIdentityError(
            f"closure record {digest_field} mismatch for {rel_path}: "
            f"record={expected} recomputed={actual}"
        )


def require_accepted_closure_for_execution(
    commit: str,
    source_inventory: list[dict[str, str]],
    *,
    plan_hash: str,
    audit_id: str,
    output_dir: Path | None = None,
) -> str:
    """§13.2: non-smoke and resume runs require fail-closed canonical closure validation."""
    return verify_canonical_closure_record(
        commit=commit,
        source_inventory=source_inventory,
        plan_hash=plan_hash,
        audit_id=audit_id,
        required=True,
    )


def verify_fingerprint_artifacts(
    output_dir: Path,
    *,
    fingerprint_bytes: bytes,
    manifest_payload: dict[str, Any] | None,
) -> None:
    """§12.6 resume checks: both fingerprint files must exist and match byte-for-byte."""
    bytes_path = Path(output_dir) / FINGERPRINT_BYTES_NAME
    payload_path = Path(output_dir) / FINGERPRINT_PAYLOAD_NAME
    for path in (bytes_path, payload_path):
        if not path.is_file():
            raise ResumeIdentityError(f"resume requires fingerprint artifact {path}")
    stored_bytes = bytes_path.read_bytes()
    if stored_bytes != fingerprint_bytes:
        raise ResumeIdentityError(
            "resume fingerprint bytes mismatch: "
            f"{len(stored_bytes)} stored bytes != {len(fingerprint_bytes)} regenerated bytes"
        )
    stored_payload_bytes = payload_path.read_bytes()
    if stored_payload_bytes != fingerprint_bytes:
        raise ResumeIdentityError(
            "resume fingerprint payload file is not byte-identical to the frozen fingerprint bytes"
        )
    if manifest_payload is not None:
        # Verbatim dict comparison against the first-run manifest payload; the stored
        # payload is never re-serialised for this check.
        stored_payload = json.loads(stored_payload_bytes.decode("utf-8"))
        if stored_payload != manifest_payload:
            raise ResumeIdentityError(
                "resume fingerprint payload does not match the first-run manifest payload dict"
            )


CANONICAL_CLOSURE_RECORD_PATH = REPO_ROOT / "GPU_RUNmultiAI/cycles/C0001" / CLOSURE_RECORD_NAME


def accepted_closure_source_hashes(output_dir: Path | None = None) -> tuple[list[dict[str, str]] | None, str]:
    """Optional hook: accepted per-file hashes become normative only after closure PASS (§13.2)."""
    path = CANONICAL_CLOSURE_RECORD_PATH
    if path.is_file():
        payload = json.loads(path.read_text(encoding="utf-8"))
        return payload.get("source_hashes"), str(path)
    return None, "absent"


def verify_source_inventory_at_commit(
    commit: str,
    inventory: list[dict[str, str]],
) -> None:
    """Prove manifest source inventory matches Git blobs at the bound commit (R5-1)."""
    import subprocess

    for entry in inventory:
        rel_path = entry["path"]
        expected = entry.get("sha256")
        if not expected:
            raise ResumeIdentityError(f"source inventory missing sha256 for {rel_path}")
        try:
            blob = subprocess.run(
                ["git", "show", f"{commit}:{rel_path}"],
                cwd=REPO_ROOT,
                capture_output=True,
                check=True,
            ).stdout
        except subprocess.CalledProcessError as exc:
            raise ResumeIdentityError(
                f"bound commit {commit} does not contain inventory path {rel_path}: {exc.stderr.decode()}"
            ) from exc
        digest = hashlib.sha256(blob).hexdigest()
        if digest != expected:
            raise ResumeIdentityError(
                f"source inventory sha256 mismatch for {rel_path} at {commit}: "
                f"inventory={expected} git_blob={digest}"
            )


def verify_canonical_closure_record(
    *,
    commit: str,
    source_inventory: list[dict[str, str]],
    plan_hash: str,
    audit_id: str,
    required: bool = False,
) -> str:
    """Canonical repository closure validation (R5-7 / round-7 fail-closed gate)."""
    import subprocess

    path = CANONICAL_CLOSURE_RECORD_PATH
    if not path.is_file():
        if required:
            raise ResumeIdentityError(
                "non-smoke and resume execution require accepted "
                "implementation_closure_record.json at the canonical repository path"
            )
        return "closure_record_absent"
    payload = json.loads(path.read_text(encoding="utf-8"))
    accepted_source_commit = payload.get("accepted_source_commit") or payload.get("commit")
    if not accepted_source_commit:
        raise ResumeIdentityError("closure record missing accepted_source_commit")
    try:
        subprocess.run(
            ["git", "cat-file", "-e", accepted_source_commit],
            cwd=REPO_ROOT,
            capture_output=True,
            check=True,
        )
    except subprocess.CalledProcessError as exc:
        raise ResumeIdentityError(
            f"accepted_source_commit {accepted_source_commit} does not exist in git: {exc.stderr.decode()}"
        ) from exc
    accepted_hashes = payload.get("source_hashes")
    if accepted_hashes != source_inventory:
        raise ResumeIdentityError("closure record source_hashes do not match recomputed inventory")
    verify_source_inventory_at_commit(accepted_source_commit, source_inventory)
    if payload.get("plan_hash") != plan_hash:
        raise ResumeIdentityError("closure record plan_hash mismatch")
    if payload.get("audit_id") != audit_id:
        raise ResumeIdentityError("closure record audit_id mismatch")
    for field in (
        "g_contract_verdict",
        "g_impl_verdict",
        "independent_reviewer_identity",
        "independent_review_verdict",
        "review_artifact_digest",
        "acceptance_artifact_digest",
        "acceptance_artifact_path",
        "review_artifact_path",
    ):
        if not payload.get(field):
            raise ResumeIdentityError(f"closure record missing required field {field}")
    for verdict_field in ("g_contract_verdict", "g_impl_verdict", "independent_review_verdict"):
        if payload.get(verdict_field) != "PASS":
            raise ResumeIdentityError(f"closure record {verdict_field} is not PASS")
    _verify_closure_artifact_digest(payload, "acceptance_artifact_digest", "acceptance_artifact_path")
    _verify_closure_artifact_digest(payload, "review_artifact_digest", "review_artifact_path")
    return (
        f"canonical_closure_verified:{path}:accepted_source_commit={accepted_source_commit}:"
        f"metadata_commit={payload.get('commit') or 'unknown'}"
    )


def verify_accepted_closure_source_hashes(
    current: list[dict[str, str]],
    *,
    output_dir: Path | None = None,
) -> str:
    accepted, source = accepted_closure_source_hashes(output_dir)
    if accepted is None:
        return "closure_record_absent"
    if accepted != current:
        raise ResumeIdentityError(
            f"accepted closure source hashes in {source} do not match the recomputed inventory"
        )
    return f"closure_record_verified:{source}"


def write_manifest(path: Path, payload: dict[str, Any]) -> None:
    write_json(path, {"at_utc": utc_now(), **payload})


def current_commit() -> str:
    return git_info()["commit"]
