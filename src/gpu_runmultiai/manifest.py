"""Audit manifest and resume identity."""

from __future__ import annotations

import hashlib
import json
import os
import platform
import sys
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
    FROZEN_ENV_VARS,
    ORACLE_TIMEOUT_SEC,
    PLAN_PATH,
    PLAN_SHA256,
    SIMPLIFIER_SUBPROCESS_TIMEOUT_SEC,
    SOURCE_HASH_PATHS,
)


def verify_plan_hash() -> str:
    digest = hashlib.sha256(PLAN_PATH.read_bytes()).hexdigest()
    if digest != PLAN_SHA256:
        raise RuntimeError(
            f"binding plan SHA mismatch: expected {PLAN_SHA256}, got {digest}"
        )
    return digest


def source_hashes() -> dict[str, str]:
    return {str(path.relative_to(REPO_ROOT)): sha256_file(path) for path in SOURCE_HASH_PATHS}


def audit_script_hash(script_path: Path) -> str:
    return sha256_file(script_path)


def dependency_versions() -> dict[str, str]:
    versions = {
        "python": platform.python_version(),
        "numpy": np.__version__,
        "scipy": scipy.__version__,
    }
    try:
        import sympy

        versions["sympy"] = sympy.__version__
    except ImportError:
        versions["sympy"] = "missing"
    try:
        import torch

        versions["torch"] = torch.__version__
    except ImportError:
        versions["torch"] = "missing"
    return versions


def frozen_environment() -> dict[str, str]:
    return {key: os.environ.get(key, "") for key in FROZEN_ENV_VARS}


def normalize_cli_args(args: dict[str, Any]) -> dict[str, Any]:
    excluded = {"resume", "fail_if_exists"}
    return {key: value for key, value in sorted(args.items()) if key not in excluded}


def build_resume_identity(
    *,
    commit: str,
    audit_script_path: Path,
    corpus_hash: str,
    cli_args: dict[str, Any],
) -> dict[str, Any]:
    return {
        "audit_id": AUDIT_ID,
        "commit": commit,
        "plan_hash": verify_plan_hash(),
        "audit_script_hash": audit_script_hash(audit_script_path),
        "config_hash": sha256_file(SOURCE_HASH_PATHS[-1]),
        "source_hashes": source_hashes(),
        "corpus_hash": corpus_hash,
        "seeds": {
            "audit_data_seed": AUDIT_DATA_SEED,
            "audit_trajectory_seed": AUDIT_TRAJECTORY_SEED,
            "audit_rewrite_seed": AUDIT_REWRITE_SEED,
            "audit_negative_seed": AUDIT_NEGATIVE_SEED,
            "audit_cas_subset_seed": AUDIT_CAS_SUBSET_SEED,
        },
        "primitive_table": PRIMITIVE_TABLE,
        "cli_args_normalized": normalize_cli_args(cli_args),
        "oracle_timeout_sec": ORACLE_TIMEOUT_SEC,
        "simplifier_subprocess_timeout_sec": SIMPLIFIER_SUBPROCESS_TIMEOUT_SEC,
        "cas_timeout_sec": CAS_TIMEOUT_SEC,
        "dependency_versions": dependency_versions(),
        "environment": frozen_environment(),
        "confirmatory_call_ceiling": expected_confirmatory_calls(),
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
        "seeds",
        "primitive_table",
        "cli_args_normalized",
        "oracle_timeout_sec",
        "simplifier_subprocess_timeout_sec",
        "cas_timeout_sec",
        "dependency_versions",
        "environment",
    ]
    for key in keys:
        if existing.get(key) != current.get(key):
            raise RuntimeError(f"resume identity mismatch for {key}")


def write_manifest(path: Path, payload: dict[str, Any]) -> None:
    write_json(path, {"at_utc": utc_now(), **payload})


def current_commit() -> str:
    return git_info()["commit"]
