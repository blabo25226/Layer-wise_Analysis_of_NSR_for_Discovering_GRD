#!/usr/bin/env python3
"""Frozen CLI entry point for C0001 metric-identifiability audit v9."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from gpu_runmultiai.audit import run_audit
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
    PRIMARY_SCALES,
    SIMPLIFIER_SUBPROCESS_TIMEOUT_SEC,
)
from gpu_runmultiai.manifest import verify_plan_hash


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="C0001 metric-identifiability audit v9")
    parser.add_argument("--audit-id", default=AUDIT_ID)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--audit-data-seed", type=int, default=AUDIT_DATA_SEED)
    parser.add_argument("--audit-trajectory-seed", type=int, default=AUDIT_TRAJECTORY_SEED)
    parser.add_argument("--audit-rewrite-seed", type=int, default=AUDIT_REWRITE_SEED)
    parser.add_argument("--audit-negative-seed", type=int, default=AUDIT_NEGATIVE_SEED)
    parser.add_argument("--audit-cas-subset-seed", type=int, default=AUDIT_CAS_SUBSET_SEED)
    parser.add_argument("--allow-cpu", action="store_true")
    parser.add_argument("--oracle-timeout-sec", type=float, default=ORACLE_TIMEOUT_SEC)
    parser.add_argument("--simplifier-subprocess-timeout-sec", type=float, default=SIMPLIFIER_SUBPROCESS_TIMEOUT_SEC)
    parser.add_argument("--cas-timeout-sec", type=float, default=CAS_TIMEOUT_SEC)
    parser.add_argument("--fail-if-exists", action="store_true")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--smoke", action="store_true", help="Bounded developer smoke; not part of confirmatory CLI identity")
    return parser.parse_args()


def _validate_frozen_seeds(args: argparse.Namespace) -> None:
    if args.audit_id != AUDIT_ID:
        raise SystemExit(f"audit-id must be {AUDIT_ID}")
    if args.audit_data_seed != AUDIT_DATA_SEED:
        raise SystemExit(f"audit-data-seed must be {AUDIT_DATA_SEED}")
    if args.audit_trajectory_seed != AUDIT_TRAJECTORY_SEED:
        raise SystemExit(f"audit-trajectory-seed must be {AUDIT_TRAJECTORY_SEED}")
    if args.audit_rewrite_seed != AUDIT_REWRITE_SEED:
        raise SystemExit(f"audit-rewrite-seed must be {AUDIT_REWRITE_SEED}")
    if args.audit_negative_seed != AUDIT_NEGATIVE_SEED:
        raise SystemExit(f"audit-negative-seed must be {AUDIT_NEGATIVE_SEED}")
    if args.audit_cas_subset_seed != AUDIT_CAS_SUBSET_SEED:
        raise SystemExit(f"audit-cas-subset-seed must be {AUDIT_CAS_SUBSET_SEED}")


def main() -> int:
    for key, value in FROZEN_ENV_VARS.items():
        os.environ.setdefault(key, value)
    verify_plan_hash()
    args = parse_args()
    _validate_frozen_seeds(args)
    options = {
        "audit_id": args.audit_id,
        "output_dir": args.output_dir,
        "audit_data_seed": args.audit_data_seed,
        "audit_trajectory_seed": args.audit_trajectory_seed,
        "audit_rewrite_seed": args.audit_rewrite_seed,
        "audit_negative_seed": args.audit_negative_seed,
        "audit_cas_subset_seed": args.audit_cas_subset_seed,
        "allow_cpu": args.allow_cpu,
        "oracle_timeout_sec": args.oracle_timeout_sec,
        "simplifier_subprocess_timeout_sec": args.simplifier_subprocess_timeout_sec,
        "cas_timeout_sec": args.cas_timeout_sec,
        "fail_if_exists": args.fail_if_exists,
        "resume": args.resume,
        "smoke": args.smoke,
        "primary_scales": PRIMARY_SCALES,
    }
    run_audit(options)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
