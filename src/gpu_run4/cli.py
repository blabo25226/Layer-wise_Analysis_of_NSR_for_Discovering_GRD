"""Common CLI flags for GPU_RUN4 phase scripts."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Any

from gpu_run4.records import dummy_formula_record
from gpu_run4_runtime import load_gpu_run4_configs, resolve_run_dir, utc_now, write_json


def common_parser(description: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--run-id", default=os.environ.get("LANSR_RUN_ID"))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--allow-cpu", action="store_true")
    parser.add_argument("--seed", type=int, default=0)
    return parser


def phase_budget(config: dict[str, Any], *, smoke: bool) -> dict[str, Any]:
    key = "smoke" if smoke else "full"
    return dict(config.get(key) or {})


def write_phase_manifest(out_dir: Path, payload: dict[str, Any]) -> Path:
    payload.setdefault("campaign", "GPU_RUN4")
    payload.setdefault("at_utc", utc_now())
    return write_json(out_dir / "manifest.json", payload)


def require_previous(run_dir: Path, relative: str) -> Path:
    path = run_dir / relative
    if not path.is_file():
        raise FileNotFoundError(f"required previous-phase artifact missing: {path}")
    return path


def seed_bundles(config: dict[str, Any], budget: dict[str, Any], *, base_seed: int) -> list[dict[str, int]]:
    bundles = list(config.get("seed_bundles") or [])
    n = int(budget.get("n_seeds", 1) or 1)
    if not bundles:
        return [{"data_seed": int(base_seed), "model_seed": 0, "permutation_seed": 1001, "corruption_seed": 1101}]
    return [dict(item) for item in bundles[: max(1, n)]]


def dummy_phase_output(out_dir: Path, phase: int, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = {
        "phase": phase,
        "status": "dry_run",
        "records": [dummy_formula_record(f"dry_run_phase{phase}")],
        **(extra or {}),
    }
    write_json(out_dir / "dummy_records.json", payload["records"])
    write_phase_manifest(out_dir, payload)
    return payload
