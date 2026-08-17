"""Shared paths, config, ND2 import, and provenance helpers for GPU_RUN3."""

from __future__ import annotations

import os
import platform
import sys
from io import BytesIO
from pathlib import Path
from typing import Any, Mapping

from experiment_runtime import REPO_ROOT
from gpu_run2_runtime import (
    cpu_identity,
    fingerprint_json,
    git_info,
    load_yaml_mapping,
    sha256_file,
    utc_now,
    write_json,
)

GPU_RUN3_CONFIG_DIR = REPO_ROOT / "configs" / "gpu_run3"
ND2_PACKAGE_ROOT = REPO_ROOT / "third_party" / "nd2"
ND2_CHECKPOINT = REPO_ROOT / "assets" / "nd2" / "weights" / "checkpoint.pth"
FORBIDDEN_IMPORT_ROOT = REPO_ROOT / "GitHubSourceCode"

FAILURE_REASONS = (
    "CheckpointLoadError",
    "ArchitectureMismatch",
    "InvalidPrefix",
    "InvalidSymbol",
    "ParseError",
    "MCTSTimeout",
    "ConstantOptimizationFailure",
    "NaN",
    "Inf",
    "TEDParseError",
    "TEDTimeout",
    "ActivationHookError",
    "ActivationPatchError",
    "OOM",
    "MissingPhase0",
    "MissingCheckpoint",
    "CUDAUnavailable",
)


def load_gpu_run3_configs(*, config_dir: Path | None = None) -> dict[str, Any]:
    root = config_dir or GPU_RUN3_CONFIG_DIR
    base = load_yaml_mapping(root / "base.yaml")
    mcts = load_yaml_mapping(root / "mcts.yaml")
    systems = load_yaml_mapping(root / "systems.yaml")
    merged = dict(base)
    merged["mcts"] = mcts
    merged["systems"] = systems.get("systems", systems)
    return merged


def resolve_run_dir(
    run_id: str | None = None,
    *,
    config: Mapping[str, Any] | None = None,
) -> Path:
    env = os.environ.get("LANSR_RUN_DIR")
    if env:
        path = Path(env).expanduser().resolve()
        path.mkdir(parents=True, exist_ok=True)
        return path
    cfg = dict(config or load_gpu_run3_configs())
    root = REPO_ROOT / str(cfg.get("output_root", "results/runs"))
    name = run_id or os.environ.get("LANSR_RUN_ID") or str(cfg.get("run_name", "gpu_run3_local"))
    path = (root / name).resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path


def graphs_dir(run_id: str, *, config: Mapping[str, Any] | None = None) -> tuple[Path, Path]:
    cfg = dict(config or load_gpu_run3_configs())
    base = REPO_ROOT / str(cfg.get("graphs_root", "graphs")) / run_id
    figures = base / "figures"
    tables = base / "tables"
    figures.mkdir(parents=True, exist_ok=True)
    tables.mkdir(parents=True, exist_ok=True)
    return figures, tables


def nd2_paths(config: Mapping[str, Any] | None = None) -> dict[str, Path]:
    cfg = dict(config or load_gpu_run3_configs())
    package = Path(cfg.get("nd2_package_root") or ND2_PACKAGE_ROOT)
    checkpoint = Path(os.environ.get("LANSR_ND2_WEIGHTS") or cfg.get("nd2_checkpoint") or ND2_CHECKPOINT)
    synthetic = Path(cfg.get("nd2_synthetic_config") or (package / "config" / "synthetic.yaml"))
    if not package.is_absolute():
        package = REPO_ROOT / package
    if not checkpoint.is_absolute():
        checkpoint = REPO_ROOT / checkpoint
    if not synthetic.is_absolute():
        synthetic = REPO_ROOT / synthetic
    return {
        "package": package,
        "checkpoint": checkpoint,
        "synthetic_config": synthetic,
        "pretrain_csv_dir": REPO_ROOT / str(cfg.get("official_pretrain_csv_dir", "data/nd2/pretrain")),
        "synthetic_data_dir": REPO_ROOT / str(cfg.get("official_synthetic_data_dir", "data/nd2/synthetic")),
    }


def install_nd2_path(package_root: Path | None = None) -> Path:
    """Put the vendored ND2 package on sys.path. Never use GitHubSourceCode/."""
    root = Path(package_root or ND2_PACKAGE_ROOT).resolve()
    if not (root / "ND2").is_dir():
        raise FileNotFoundError(f"vendored ND2 package missing: {root / 'ND2'}")
    forbidden = str(FORBIDDEN_IMPORT_ROOT.resolve())
    sys.path[:] = [p for p in sys.path if Path(p).resolve().as_posix() != Path(forbidden).as_posix()]
    inserted = str(root)
    if inserted in sys.path:
        sys.path.remove(inserted)
    sys.path.insert(0, inserted)
    return root


def assert_nd2_not_from_github_source() -> None:
    nd2 = sys.modules.get("ND2")
    if nd2 is None:
        return
    origin = Path(getattr(nd2, "__file__", "") or "").resolve()
    if not origin.as_posix():
        return
    if "GitHubSourceCode" in origin.as_posix():
        raise RuntimeError(f"ND2 was imported from the survey tree: {origin}")
    expected = (ND2_PACKAGE_ROOT / "ND2").resolve()
    if expected.as_posix() not in origin.as_posix():
        raise RuntimeError(f"ND2 import origin {origin} is not {expected}")


def require_python_310() -> None:
    if sys.version_info[:2] != (3, 10) and os.environ.get("LANSR_ALLOW_NON_310") != "1":
        raise RuntimeError(
            f"GPU_RUN3 requires Python 3.10 (found {platform.python_version()}). "
            "Set LANSR_ALLOW_NON_310=1 only for local non-experiment checks."
        )


def select_device(*, allow_cpu: bool) -> str:
    try:
        import torch
    except Exception as exc:
        if allow_cpu:
            return "cpu"
        raise RuntimeError("PyTorch import failed") from exc
    if torch.cuda.is_available():
        return "cuda"
    if allow_cpu:
        return "cpu"
    raise RuntimeError("CUDA is not available. Pass --allow-cpu for CPU-only smoke.")


def load_checkpoint_blob(path: Path, map_location: str | None = None) -> dict[str, Any]:
    """Load the official NDformer checkpoint, including the upstream src->ND2 pickle patch."""
    import torch

    if not path.is_file():
        raise FileNotFoundError(f"ND2 checkpoint missing: {path}")
    try:
        blob = torch.load(path, map_location=map_location or "cpu", weights_only=False)
    except ModuleNotFoundError:
        payload = path.read_bytes().replace(b"src", b"ND2")
        blob = torch.load(BytesIO(payload), map_location=map_location or "cpu", weights_only=False)
    if not isinstance(blob, dict) or "encoder" not in blob or "decoder" not in blob:
        raise RuntimeError("ArchitectureMismatch: checkpoint is missing encoder/decoder state dicts")
    return blob


def load_ndformer(
    checkpoint: Path,
    *,
    device: str,
    weights_only: bool = False,
) -> Any:
    """Instantiate NDformer and load official weights with fail-fast mismatch checks."""
    install_nd2_path()
    from ND2.model import NDformer

    model = NDformer(device=device)
    blob = load_checkpoint_blob(checkpoint, map_location=device)
    try:
        model.encoder.load_state_dict(blob["encoder"], strict=True)
        model.decoder.load_state_dict(blob["decoder"], strict=True)
    except Exception as exc:
        raise RuntimeError(f"ArchitectureMismatch: {exc}") from exc
    model.to(device)
    model.eval()
    assert_nd2_not_from_github_source()
    return model


def download_checkpoint(url: str, dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.is_file() and dest.stat().st_size > 0:
        return dest
    import urllib.request

    tmp = dest.with_suffix(dest.suffix + ".partial")
    with urllib.request.urlopen(url, timeout=120) as response, tmp.open("wb") as handle:
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            handle.write(chunk)
    tmp.replace(dest)
    return dest


def directory_fingerprint(path: Path) -> str:
    """SHA256 over relative paths and file hashes, for vendored-tree provenance."""
    import hashlib

    digest = hashlib.sha256()
    if not path.is_dir():
        raise FileNotFoundError(path)
    for file_path in sorted(p for p in path.rglob("*") if p.is_file()):
        rel = file_path.relative_to(path).as_posix().encode("utf-8")
        digest.update(rel)
        digest.update(b"\0")
        digest.update(sha256_file(file_path).encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def software_versions() -> dict[str, Any]:
    versions: dict[str, Any] = {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "executable": sys.executable,
    }
    for name in ("torch", "numpy", "sympy", "scipy", "sklearn", "pandas", "networkx", "yaml", "zss"):
        try:
            module = __import__(name if name != "yaml" else "yaml")
            versions[name] = getattr(module, "__version__", "present")
        except Exception as exc:
            versions[name] = f"import_failed:{exc}"
    try:
        import torch

        versions["cuda_available"] = bool(torch.cuda.is_available())
        versions["cuda_version"] = getattr(torch.version, "cuda", None)
        if torch.cuda.is_available():
            versions["gpu_name"] = torch.cuda.get_device_name(0)
            versions["gpu_count"] = int(torch.cuda.device_count())
    except Exception as exc:
        versions["torch_runtime"] = f"unavailable:{exc}"
    return versions


def require_phase_artifact(run_dir: Path, relative: str) -> Path:
    path = run_dir / relative
    if not path.is_file():
        raise FileNotFoundError(f"MissingPhase0: required artifact not found: {path}")
    return path


def load_json(path: Path) -> Any:
    import json

    return json.loads(path.read_text(encoding="utf-8"))


def seed_everything(seed: int) -> None:
    import random

    import numpy as np

    random.seed(int(seed))
    np.random.seed(int(seed))
    try:
        import torch

        torch.manual_seed(int(seed))
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(int(seed))
    except Exception:
        pass


def configure_nd2_logging(log_path: Path) -> None:
    install_nd2_path()
    from ND2.utils import init_logger

    log_path.parent.mkdir(parents=True, exist_ok=True)
    init_logger("GPU_RUN3", str(log_path), root_name="ND2", info_level="warning")
