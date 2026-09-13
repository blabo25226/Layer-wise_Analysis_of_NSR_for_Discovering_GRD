"""Config path helpers without hard dependency on omegaconf."""

from __future__ import annotations

from pathlib import Path

from experiment_runtime import REPO_ROOT

from gpu_runmultiai.constants import CONFIG_PATH


def output_root_abs() -> Path:
    from gpu_run5.config import load_config

    config = load_config()
    return (REPO_ROOT / str(config["output_root"])).resolve()
