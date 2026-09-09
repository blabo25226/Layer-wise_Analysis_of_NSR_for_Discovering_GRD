"""Frozen numeric constants for GPU_RUNclaude1 cycle C0001.

Every value below is copied verbatim from
``GPU_RUNclaude1/plans/C0001_preregistration_v2.md`` (the frozen contract).
Per v2 §2.5, none of these may change after the first Part A match indicator
is computed except through the §14 deviation policy (a dated ``DEVIATION-nn``
block in that file), which also forbids raising a threshold to rescue a
result (rule 01 item 3). Centralizing them here means every module cites the
same frozen value instead of re-typing a magic number.
"""

from __future__ import annotations

CAMPAIGN = "GPU_RUNclaude1_C0001"
CYCLE_ID = "C0001"
BRANCH = "20260909_researce_GPU_RUNclaude1"

# v2 §3 / Gate 0 item 4
CHECKPOINT_SHA256 = "56754040be5aa92ed4767fc43ee2008faa293f87c12b643e66c7df3e1623a5e8"
CHECKPOINT_SIZE_BYTES = 464_822_385

# v2 §3 operator-constraint values "of record". These are frozen because they
# were verified at the reproducibility audit against the checkpoint's own
# persisted generator config (`env.generator` / `params`); phase0 preflight
# re-verifies the live checkpoint still agrees rather than assuming it.
OPERATORS_TO_USE = "sin:1,inv:1,pow2:1,id:3,add:3,mul:1"
MIN_UNARY_OPS_PER_DIM = 0
MAX_UNARY_OPS_PER_DIM = 3  # C-BUDGET, the generator's own unary budget
MIN_BINARY_OPS_PER_DIM = 1
MAX_BINARY_OPS_PER_DIM = 5
MAX_UNARY_DEPTH = 7
MAX_INT = 10
FLOAT_PRECISION = 3
MAX_DIMENSION = 6
ZERO_PROBABILITY_OPERATORS = (
    "abs", "sqrt", "log", "exp", "arcsin", "cos", "arccos", "tan", "arctan",
    "pow3", "sub", "div",
)

# decode config of the stored candidates (fixed context, never swept)
BEAM_SIZE = 50
BEAM_TEMPERATURE = 0.1
BEAM_TYPE = "sampling"
MAX_GENERATED_OUTPUT_LEN = 200
RESCALE = True
FAILURE_PENALTY = 10.0

# v2 §3 seeds
GLOBAL_SEED = 20260909
CLUSTER_BOOTSTRAP_SEED = 20260909
CLUSTER_BOOTSTRAP_RESAMPLES = 10_000
NUMERIC_EQUIVALENT_SEED = 0  # Part B rewrite verification only (numeric_equivalent)

# v2 §7.2 frozen fallback thresholds (component strata)
MIN_H_FOR_STRATIFIED_PRIMARY = 40
MIN_L_FOR_STRATIFIED_PRIMARY = 15
UNDERPOWERED_H_CEILING = 100
UNDERPOWERED_POWER_FLOOR = 0.90

# v2 §7.1 / §7.3 -- the effect size E0 requires, = C-M0c
GAIN_RATE_EFFECT_SIZE = 0.0525

# v2 §7.5 / A2-S6 failure and monotonicity budgets
COULD_NOT_EVALUATE_MAX_RATE = 0.02
MONOTONICITY_MINOR_MAX_RATE = 0.001
MONOTONICITY_MAJOR_MAX_RATE = 0.01

# v2 §7.6 -- Gate A->B exact-reproduction targets (R1, AUDIT-CRIT-1)
N_STORED_CANDIDATES = 47_987
N_STORED_COMPONENT_COMPARISONS = 101_963
N_STORED_COMPONENT_HITS = 2_235
STORED_SYSTEM_LEVEL_HITS = 0
STORED_SYSTEM_LEVEL_N = 960          # mean over 960 cells (AUDIT-MIN-11)
STORED_COMPONENT_LEVEL_HITS = 107
STORED_COMPONENT_LEVEL_N = 2_040

# v2 §7.7 control battery pass thresholds and known verification values
PC0_N_COMPONENTS = 170
PC0_N_SYSTEMS = 80
PC0_CAS_KNOWN_HITS_AT_CAP_40 = 28   # of 80, Q4
PC0_CAS_KNOWN_CAP_EXCEEDED_AT_CAP_40 = 52
PC0_CAS_RAISED_CAP = 200
PC2A_KNOWN_HITS = 80                # of 80, Q1
PC2B_MIN_HITS = 76                  # of 80
PC2C_MIN_HITS = 76                  # of 80
PC2D_MIN_HITS = 76                  # of 80
PC3A_KNOWN_ELIGIBLE_N = 48          # of 48, Q2
PC3B_MIN_HITS = 58                  # of 60

# v2 §11.1 measured cost calibration (Gate 0 item 8)
CALIBRATION_N_CANDIDATES = 400
CALIBRATION_PER_FAMILY = 50
CALIBRATION_SEED = 20260909
PART_A_PROJECTED_CEILING_CORE_HOURS = 12.0

# v2 §11 / §10.2 compute ceiling (rule 06)
GPU_HOURS_CEILING = 4.0
PEAK_VRAM_GIB_CEILING = 5.5
CPU_CORE_HOURS_CEILING = 24.0
NEW_DISK_GIB_CEILING = 15.0
GPU_ABORT_TEMP_C = 85.0

# corpus shape (v2 P8)
FAMILIES = ("R01", "R02", "R03", "R04", "R05", "R06", "R07", "R08")
N_VALIDATION_SYSTEMS = 80
N_VALIDATION_COMPONENTS = 170
N_VALIDATION_CELLS = 960

# v2 §8.1 Part B
REWRITE_CAP_PER_COMPONENT = 200

# v2 §8.2 / §8.3 Part C
CELL_REENCODING_MISMATCH_CELL_MAX_FRACTION = 0.10
UNRELIABLE_REENCODING_CELL_MAX_FRACTION = 0.10
COMMUTATION_ORBIT_CAP = 8
N_IN_SUPPORT_MINIMUM = 30
N_DISTINCT_PAYLOADS_PER_SYSTEM = 10  # P11
N_CELLS_PER_SYSTEM = 12
SUM_LOGPROB_REGRESSION_TOLERANCE = 1e-5

# v2 §14 item 4 -- reduced cell design if Part A projects > 12 core-h
REDUCED_BUNDLES = (0, 1, 2)
REDUCED_NOISE_SUBSAMPLE = ((0.0, 0.0), (0.05, 0.5))
