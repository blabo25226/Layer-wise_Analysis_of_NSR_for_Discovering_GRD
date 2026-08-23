"""Configuration, paths, provenance, and phase manifest helpers for GPU_RUN5."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from experiment_runtime import REPO_ROOT
from gpu_run2_runtime import load_yaml_mapping, utc_now, write_json

CONFIG_PATH = REPO_ROOT / "configs" / "gpu_run5" / "base.yaml"


def load_config() -> dict[str, Any]:
    return load_yaml_mapping(CONFIG_PATH)


def run_dir(run_id: str | None = None) -> Path:
    configured = load_config()
    explicit = os.environ.get("LANSR_RUN_DIR")
    if explicit:
        path = Path(explicit).expanduser().resolve()
    else:
        name = run_id or os.environ.get("LANSR_RUN_ID") or str(configured["run_name"])
        path = (REPO_ROOT / str(configured["output_root"]) / name).resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path


def phase_dir(run_id: str | None, phase: int) -> Path:
    path = run_dir(run_id) / f"phase{phase}"
    path.mkdir(parents=True, exist_ok=True)
    return path


def read_json(path: Path, default: Any = None) -> Any:
    if not path.is_file():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_manifest(out_dir: Path, phase: int, status: str, **payload: Any) -> Path:
    return write_json(
        out_dir / "manifest.json",
        {"campaign": "GPU_RUN5", "phase": int(phase), "status": status, "at_utc": utc_now(), **payload},
    )


def budget(config: dict[str, Any], smoke: bool) -> dict[str, Any]:
    return dict(config["smoke" if smoke else "full"])


def require_artifact(root: Path, relative: str) -> Path:
    path = root / relative
    if not path.is_file():
        raise FileNotFoundError(f"required previous-phase artifact missing: {path}")
    return path


def load_sealed_test(path: Path, *, phase: int) -> Any:
    """Read a GRN test artifact only from the final-test phase or later."""
    if int(phase) < 8:
        raise PermissionError(f"test firewall: phase {phase} cannot read {path}")
    return read_json(path)
