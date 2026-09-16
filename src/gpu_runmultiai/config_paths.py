"""Config path helpers without hard dependency on omegaconf."""

from __future__ import annotations

from pathlib import Path

from experiment_runtime import REPO_ROOT


def output_root_abs() -> Path:
    return (REPO_ROOT / "results" / "runs").resolve()
