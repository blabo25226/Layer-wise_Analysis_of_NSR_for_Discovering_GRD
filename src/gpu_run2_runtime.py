"""Shared paths, config loading, and manifest helpers for GPU_RUN2."""

from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

from experiment_runtime import (
    REPO_ROOT,
    default_nesymres_config,
    default_nesymres_eq_setting,
    default_nesymres_weights,
)

GPU_RUN2_CONFIG_DIR = REPO_ROOT / "configs" / "gpu_run2"
DEFAULT_DECODE_TIMEOUT_SEC = 30.0
GNW_SOURCE_COMMIT = "5016f55ab04c111f29d7d0b3a4881d4725d49467"


def load_yaml_mapping(path: Path) -> dict[str, Any]:
    """Load a YAML file as a plain dict. Fail fast if the file is missing."""
    if not path.is_file():
        raise FileNotFoundError(f"GPU_RUN2 config not found: {path}")
    try:
        from omegaconf import OmegaConf
    except ImportError as exc:  # pragma: no cover - omegaconf is a project dep
        raise RuntimeError("omegaconf is required to load GPU_RUN2 configs") from exc
    loaded = OmegaConf.load(path)
    data = OmegaConf.to_container(loaded, resolve=True)
    if not isinstance(data, dict):
        raise ValueError(f"expected a mapping in {path}, got {type(data).__name__}")
    return data


def load_gpu_run2_configs(
    *,
    config_dir: Path | None = None,
) -> dict[str, Any]:
    """Load base / operators / splits YAML and merge into one mapping."""
    root = config_dir or GPU_RUN2_CONFIG_DIR
    base = load_yaml_mapping(root / "base.yaml")
    operators = load_yaml_mapping(root / "operators.yaml")
    splits = load_yaml_mapping(root / "splits.yaml")
    merged = dict(base)
    merged["operators"] = operators
    merged["splits"] = splits
    return merged


def seed_bundles(config: Mapping[str, Any] | None = None) -> list[dict[str, int]]:
    """Return the three paired (data_seed, model_seed) bundles."""
    cfg = dict(config or load_gpu_run2_configs())
    bundles = cfg.get("seed_bundles")
    if not bundles:
        raise ValueError("GPU_RUN2 config is missing seed_bundles")
    out = []
    for item in bundles:
        out.append(
            {
                "data_seed": int(item["data_seed"]),
                "model_seed": int(item["model_seed"]),
            }
        )
    return out


def decode_timeout_sec(config: Mapping[str, Any] | None = None) -> float:
    cfg = dict(config or load_gpu_run2_configs())
    env = os.environ.get("LANSR_DECODE_TIMEOUT_SEC")
    if env:
        return float(env)
    return float(cfg.get("decode_timeout_sec", DEFAULT_DECODE_TIMEOUT_SEC))


def resolve_run_dir(
    run_id: str | None = None,
    *,
    config: Mapping[str, Any] | None = None,
) -> Path:
    """Return the local canonical run directory (never a Drive sync folder)."""
    env = os.environ.get("LANSR_RUN_DIR")
    if env:
        path = Path(env).expanduser().resolve()
        path.mkdir(parents=True, exist_ok=True)
        return path
    cfg = dict(config or load_gpu_run2_configs())
    root = REPO_ROOT / str(cfg.get("output_root", "results/runs"))
    name = run_id or os.environ.get("LANSR_RUN_ID") or str(cfg.get("run_name", "gpu_run2_local"))
    path = (root / name).resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path


def graphs_dir(run_id: str, *, config: Mapping[str, Any] | None = None) -> tuple[Path, Path]:
    cfg = dict(config or load_gpu_run2_configs())
    base = REPO_ROOT / str(cfg.get("graphs_root", "graphs")) / run_id
    figures = base / "figures"
    tables = base / "tables"
    figures.mkdir(parents=True, exist_ok=True)
    tables.mkdir(parents=True, exist_ok=True)
    return figures, tables


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def fingerprint_json(obj: Any) -> str:
    blob = json.dumps(obj, sort_keys=True, ensure_ascii=False, default=_json_default)
    return sha256_bytes(blob.encode("utf-8"))


def _json_default(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if hasattr(value, "tolist"):
        return value.tolist()
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def write_json(path: Path, payload: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, indent=2, ensure_ascii=False, default=_json_default)
    tmp = path.with_name(path.name + ".partial")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)
    return path


def git_info() -> dict[str, str | None]:
    def _run(*args: str) -> str | None:
        try:
            return subprocess.check_output(
                ["git", *args],
                cwd=REPO_ROOT,
                text=True,
                stderr=subprocess.DEVNULL,
            ).strip()
        except (OSError, subprocess.CalledProcessError):
            return None

    return {
        "branch": _run("branch", "--show-current"),
        "commit": _run("rev-parse", "HEAD"),
        "status_short": _run("status", "--short"),
    }


def cpu_identity() -> dict[str, Any]:
    info: dict[str, Any] = {
        "platform": platform.platform(),
        "processor": platform.processor(),
        "machine": platform.machine(),
        "python": platform.python_version(),
    }
    if os.name == "nt":
        brand = subprocess_output(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                "(Get-CimInstance Win32_Processor | Select-Object -First 1 -ExpandProperty Name)",
            ]
        )
        if brand:
            info["cpu_brand"] = brand.strip()
    else:
        try:
            cpuinfo = Path("/proc/cpuinfo").read_text(encoding="utf-8", errors="replace")
            for line in cpuinfo.splitlines():
                if line.lower().startswith("model name"):
                    info["cpu_brand"] = line.split(":", 1)[1].strip()
                    break
        except OSError:
            pass
    return info


def subprocess_output(command: Sequence[str]) -> str | None:
    try:
        return subprocess.check_output(command, text=True, stderr=subprocess.DEVNULL).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def nesymres_paths(config: Mapping[str, Any] | None = None) -> dict[str, Path]:
    cfg = dict(config or {})
    weights = Path(cfg["nesymres_weights"]) if cfg.get("nesymres_weights") else default_nesymres_weights()
    model_cfg = Path(cfg["nesymres_config"]) if cfg.get("nesymres_config") else default_nesymres_config()
    eq_setting = (
        Path(cfg["nesymres_eq_setting"])
        if cfg.get("nesymres_eq_setting")
        else default_nesymres_eq_setting()
    )
    if not weights.is_absolute():
        weights = REPO_ROOT / weights
    if not model_cfg.is_absolute():
        model_cfg = REPO_ROOT / model_cfg
    if not eq_setting.is_absolute():
        eq_setting = REPO_ROOT / eq_setting
    return {"weights": weights, "config": model_cfg, "eq_setting": eq_setting}


def require_python_310() -> None:
    import sys

    if sys.version_info[:2] != (3, 10) and os.environ.get("LANSR_ALLOW_NON_310") != "1":
        raise RuntimeError(
            f"GPU_RUN2 requires Python 3.10 (found {platform.python_version()}). "
            "Set LANSR_ALLOW_NON_310=1 only for local non-experiment checks."
        )
