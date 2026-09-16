"""Frozen C0001 audit constants (preregistration v16)."""

from __future__ import annotations

from pathlib import Path

from experiment_runtime import REPO_ROOT

AUDIT_ID = "c0001_metric_identifiability_audit_v16"
PLAN_PATH = REPO_ROOT / "GPU_RUNmultiAI/cycles/C0001/preregistration_draft_v16.md"
PLAN_SHA256 = "67017f5c8bac861664fc867b70cf229d43be3d052d266ffd0d575e20e6c12078"

CONFIRMATORY_CALL_CEILING = 27637
FULL_RUN_CALL_CEILING = 30277
D2_PAIR_COUNT = 330
D2_CALLS_PER_PAIR = 8

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
C_Q4_FIXTURE_COUNT = 7

ORACLE_TIMEOUT_SEC = 30.0
Q4_TIMEOUT_SEC = 10.0
SIMPLIFIER_SUBPROCESS_TIMEOUT_SEC = 5.0
CAS_TIMEOUT_SEC = 60.0
ELAPSED_WALL_CEILING_SEC = 18000
OUTPUT_DIR_BYTE_CEILING = 1_200_000_000

ORACLE_ATOL = 1e-8
ORACLE_RTOL = 1e-8
ORACLE_X_GRID = (0.01, 0.1, 0.5, 1.0, 2.0)
ORACLE_T_GRID = (0.0, 5.0, 10.0)

MAX_REJECTION_RATE = 0.30
EXPECTED_TRAIN_SYSTEMS = 240
EXPECTED_COMPONENTS = 510
EXPECTED_STRICT_HILL_COMPONENTS = 330
EXPECTED_NON_STRICT_HILL_COMPONENTS = 60
EXPECTED_LINEAR_COMPONENTS = 120
EXPECTED_QUANTIZATION_ACTIVE_COMPONENTS = 46
EXPECTED_QUANTIZATION_NEUTRAL_COMPONENTS = 284

FROZEN_ENV_VARS = {
    "LANSR_TED_TIMEOUT_SEC": "10",
    "LANSR_SYMPY_TIMEOUT_SEC": "10",
    "LANSR_SYMPY_MAX_NODES": "40",
}

CONFIG_PATH = REPO_ROOT / "configs/gpu_run5/base.yaml"

SOURCE_INVENTORY_EXTRA_PATHS = (
    REPO_ROOT / "src/experiment_runtime.py",
    REPO_ROOT / "src/gpu_run2_runtime.py",
    REPO_ROOT / "src/gpu_run3_runtime.py",
    REPO_ROOT / "src/gpu_run4_runtime.py",
    REPO_ROOT / "configs/gpu_run5/base.yaml",
    REPO_ROOT / "scripts/phases/gpu_runmultiai_c0001_metric_audit.py",
    REPO_ROOT / "scripts/phases/guard_bootstrap.py",
    REPO_ROOT / "src/evaluation/gpu_run5_structure.py",
    REPO_ROOT / "src/gpu_run4/formulas.py",
    REPO_ROOT / "src/gpu_run4/ted.py",
    REPO_ROOT / "src/gpu_run5/config.py",
    REPO_ROOT / "src/gpu_run5/evaluation.py",
    REPO_ROOT / "src/gpu_run5/grn.py",
)
