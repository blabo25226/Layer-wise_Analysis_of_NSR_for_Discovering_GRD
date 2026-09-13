"""Config path helpers without hard dependency on omegaconf."""

from __future__ import annotations

from pathlib import Path

from experiment_runtime import REPO_ROOT

from gpu_runmultiai.constants import CONFIG_PATH


def output_root_abs() -> Path:
    try:
        from gpu_run5.config import load_config

        config = load_config()
        return (REPO_ROOT / str(config["output_root"])).resolve()
    except RuntimeError:
        for line in CONFIG_PATH.read_text(encoding="utf-8").splitlines():
            if line.startswith("output_root:"):
                return (REPO_ROOT / line.split(":", 1)[1].strip()).resolve()
        raise RuntimeError(f"output_root not found in {CONFIG_PATH}")
