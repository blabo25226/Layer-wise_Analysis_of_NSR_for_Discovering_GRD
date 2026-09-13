"""Frozen C0001 audit constants (preregistration v9)."""

from __future__ import annotations

from pathlib import Path

from experiment_runtime import REPO_ROOT

AUDIT_ID = "c0001_metric_identifiability_audit_v9"
PLAN_PATH = REPO_ROOT / "GPU_RUNmultiAI/cycles/C0001/preregistration_draft_v9.md"
PLAN_SHA256 = "60cfed79780c6b027192a3da14e69416d72090e0a89dddd22248b0f00f50cf00"

CONFIRMATORY_CALL_CEILING = 23550
FULL_RUN_CALL_CEILING = 25860

PRIMARY_STRICT_HILL_PAIRS = 1320
PRIMARY_SCALES = ("0.1", "0.5", "1.0", "2.0")
STRESS_SCALE = "5.0"
IDENTITY_SCALE = "identity"
TRUTH_COPY_REWRITE_ID = "truth_copy"
IDENTITY_REWRITE_ID = "identity"

AUDIT_DATA_SEED = 61001
AUDIT_TRAJECTORY_SEED = 61002
AUDIT_REWRITE_SEED = 61003
AUDIT_NEGATIVE_SEED = 61004
AUDIT_CAS_SUBSET_SEED = 61005

PRIMES = [2, 3, 5, 7, 11]
N1_COEFFS = [1, 2, 3, 5, 7]
N1_COUNT = 100
B3_PAIR_COUNT = 500

ORACLE_TIMEOUT_SEC = 30.0
SIMPLIFIER_SUBPROCESS_TIMEOUT_SEC = 5.0
CAS_TIMEOUT_SEC = 60.0

ORACLE_ATOL = 1e-8
ORACLE_RTOL = 1e-8
ORACLE_X_GRID = (0.01, 0.1, 0.5, 1.0, 2.0)
ORACLE_T_GRID = (0.0, 5.0, 10.0)

MAX_REJECTION_RATE = 0.30
EXPECTED_TRAIN_SYSTEMS = 240
EXPECTED_COMPONENTS = 510

FROZEN_ENV_VARS = {
    "LANSR_TED_TIMEOUT_SEC": "10",
    "LANSR_SYMPY_TIMEOUT_SEC": "10",
    "LANSR_SYMPY_MAX_NODES": "40",
}

SOURCE_HASH_PATHS = (
    REPO_ROOT / "src/gpu_run5/grn.py",
    REPO_ROOT / "src/evaluation/gpu_run5_structure.py",
    REPO_ROOT / "third_party/odeformer/odeformer/model/utils_wrapper.py",
    REPO_ROOT / "third_party/odeformer/odeformer/model/sklearn_wrapper.py",
    REPO_ROOT / "third_party/odeformer/odeformer/envs/simplifiers.py",
    REPO_ROOT / "src/gpu_run5/evaluation.py",
    REPO_ROOT / "src/gpu_run4/formulas.py",
    REPO_ROOT / "src/gpu_run4/ted.py",
    REPO_ROOT / "configs/gpu_run5/base.yaml",
)

CONFIG_PATH = REPO_ROOT / "configs/gpu_run5/base.yaml"
