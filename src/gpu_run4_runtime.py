"""Shared paths, config, ODEFormer import, and provenance helpers for GPU_RUN4."""

from __future__ import annotations

import os
import platform
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator, Mapping

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
from gpu_run3_runtime import seed_everything, software_versions

GPU_RUN4_CONFIG_DIR = REPO_ROOT / "configs" / "gpu_run4"
ODEFORER_PACKAGE_ROOT = REPO_ROOT / "third_party" / "odeformer"
ODEFORER_CHECKPOINT = REPO_ROOT / "assets" / "odeformer" / "weights" / "odeformer.pt"
FORBIDDEN_IMPORT_ROOT = REPO_ROOT / "GitHubSourceCode"

# Official README demo: https://github.com/sdascoli/odeformer
OFFICIAL_DEMO_TRAJECTORY = {
    "t_max": 10.0,
    "n_points": 50,
    "x_scale": 2.3,
    "x_phase": 0.5,
    "y_scale": 1.2,
    "y_phase": 0.1,
}


def load_gpu_run4_configs(*, config_dir: Path | None = None) -> dict[str, Any]:
    root = config_dir or GPU_RUN4_CONFIG_DIR
    return load_yaml_mapping(root / "base.yaml")


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
    cfg = dict(config or load_gpu_run4_configs())
    root = REPO_ROOT / str(cfg.get("output_root", "results/runs"))
    name = run_id or os.environ.get("LANSR_RUN_ID") or str(cfg.get("run_name", "gpu_run4_local"))
    path = (root / name).resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path


def graphs_dir(run_id: str, *, config: Mapping[str, Any] | None = None) -> tuple[Path, Path]:
    cfg = dict(config or load_gpu_run4_configs())
    base = REPO_ROOT / str(cfg.get("graphs_root", "graphs")) / run_id
    figures = base / "figures"
    tables = base / "tables"
    figures.mkdir(parents=True, exist_ok=True)
    tables.mkdir(parents=True, exist_ok=True)
    return figures, tables


def odeformer_paths(config: Mapping[str, Any] | None = None) -> dict[str, Path]:
    cfg = dict(config or load_gpu_run4_configs())
    package = Path(cfg.get("odeformer_package_root") or ODEFORER_PACKAGE_ROOT)
    checkpoint = Path(
        os.environ.get("LANSR_ODEFORER_WEIGHTS") or cfg.get("odeformer_checkpoint") or ODEFORER_CHECKPOINT
    )
    if not package.is_absolute():
        package = REPO_ROOT / package
    if not checkpoint.is_absolute():
        checkpoint = REPO_ROOT / checkpoint
    return {
        "package": package,
        "checkpoint": checkpoint,
        "odebench_equations": package / "odeformer" / "odebench" / "strogatz_equations.py",
        "odebench_extended": package / "odeformer" / "odebench" / "strogatz_extended.json",
        "parsers": package / "parsers.py",
        "license": package / "LICENSE.txt",
    }


def install_odeformer_path(package_root: Path | None = None) -> Path:
    """Put the vendored ODEFormer package on sys.path. Never use GitHubSourceCode/."""
    root = Path(package_root or ODEFORER_PACKAGE_ROOT).resolve()
    if not (root / "odeformer").is_dir():
        raise FileNotFoundError(f"vendored ODEFormer package missing: {root / 'odeformer'}")
    forbidden = FORBIDDEN_IMPORT_ROOT.resolve().as_posix()
    sys.path[:] = [p for p in sys.path if Path(p).resolve().as_posix() != forbidden]
    inserted = str(root)
    if inserted in sys.path:
        sys.path.remove(inserted)
    sys.path.insert(0, inserted)
    return root


def assert_odeformer_not_from_github_source() -> None:
    module = sys.modules.get("odeformer")
    if module is None:
        return
    origin = Path(getattr(module, "__file__", "") or "").resolve()
    if not origin.as_posix():
        return
    if "GitHubSourceCode" in origin.as_posix():
        raise RuntimeError(f"odeformer was imported from the survey tree: {origin}")
    expected = (ODEFORER_PACKAGE_ROOT / "odeformer").resolve()
    if expected.as_posix() not in origin.as_posix():
        raise RuntimeError(f"odeformer import origin {origin} is not {expected}")


def require_python_310() -> None:
    if sys.version_info[:2] != (3, 10) and os.environ.get("LANSR_ALLOW_NON_310") != "1":
        raise RuntimeError(
            f"GPU_RUN4 requires Python 3.10 (found {platform.python_version()}). "
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


def hardware_identity() -> dict[str, Any]:
    info = dict(cpu_identity())
    try:
        meminfo = Path("/proc/meminfo").read_text(encoding="utf-8", errors="replace")
        for line in meminfo.splitlines():
            if line.startswith("MemTotal:"):
                kb = int(line.split()[1])
                info["ram_gb"] = round(kb / (1024 ** 2), 2)
                break
    except OSError:
        pass
    info["os"] = platform.platform()
    return info


def download_checkpoint(dest: Path, *, file_id: str, url: str | None = None) -> Path:
    """Download the official ODEFormer pickle from Google Drive into assets/."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.is_file() and dest.stat().st_size > 0:
        return dest
    try:
        import gdown
    except ImportError as exc:
        raise RuntimeError(
            "CheckpointDownloadError: gdown is required to fetch the official ODEFormer weights. "
            "Install it in lansr310 with `pip install gdown`."
        ) from exc
    drive_url = url or f"https://drive.google.com/uc?id={file_id}"
    tmp = dest.with_suffix(dest.suffix + ".partial")
    try:
        try:
            gdown.download(id=file_id, output=str(tmp), quiet=False)
        except TypeError:
            gdown.download(drive_url, str(tmp), quiet=False)
    except Exception as exc:
        if tmp.is_file():
            tmp.unlink()
        raise RuntimeError(f"CheckpointDownloadError: {exc}") from exc
    if not tmp.is_file() or tmp.stat().st_size == 0:
        raise RuntimeError("CheckpointDownloadError: download produced an empty file")
    tmp.replace(dest)
    return dest


def load_odeformer_model(checkpoint: Path, *, device: str) -> Any:
    """Load the official pickled ModelWrapper. Fail fast on architecture / pickle errors."""
    import torch

    install_odeformer_path()
    if not checkpoint.is_file():
        raise FileNotFoundError(f"ODEFormer checkpoint missing: {checkpoint}")
    try:
        blob = torch.load(checkpoint, map_location=device, weights_only=False)
    except Exception as exc:
        raise RuntimeError(f"CheckpointLoadError: {exc}") from exc
    model = blob
    if isinstance(blob, dict):
        for key in ("model", "regressor", "state"):
            if key in blob and hasattr(blob[key], "encoder"):
                model = blob[key]
                break
        else:
            raise RuntimeError(
                "ArchitectureMismatch: checkpoint is a dict without a ModelWrapper-like object"
            )
    if not hasattr(model, "encoder") or not hasattr(model, "decoder"):
        raise RuntimeError(f"ArchitectureMismatch: loaded type {type(model)!r} has no encoder/decoder")
    # Backward-compatible default for checkpoints pickled before GPU_RUN5 added
    # an explicit sampling seed to the vendored ModelWrapper.
    if not hasattr(model, "generation_seed"):
        model.generation_seed = 0
    model.to(device)
    model.eval()
    model.device = torch.device(device)
    assert_odeformer_not_from_github_source()
    return model


def paper_model_args(protocol: Mapping[str, Any]) -> dict[str, Any]:
    """Paper inference knobs. Parser / ModelWrapper defaults are not used."""
    return {
        "beam_size": int(protocol.get("beam_size", 50)),
        "beam_temperature": float(protocol.get("beam_temperature", 0.1)),
        "beam_type": str(protocol.get("beam_type", "sampling")),
    }


def make_symbolic_regressor(
    model: Any,
    *,
    rescale: bool,
    beam_size: int,
    beam_temperature: float,
    beam_type: str = "sampling",
    generation_seed: int = 0,
) -> Any:
    """Wrap a loaded ModelWrapper with the official sklearn API and paper beam settings."""
    install_odeformer_path()
    from odeformer.model import SymbolicTransformerRegressor

    regressor = SymbolicTransformerRegressor(model=model, from_pretrained=False, rescale=rescale)
    regressor.set_model_args(
        {
            "beam_size": int(beam_size),
            "beam_temperature": float(beam_temperature),
            "beam_type": str(beam_type),
            "generation_seed": int(generation_seed),
        }
    )
    return regressor


def official_demo_arrays(*, n_points: int = 50):
    import numpy as np

    spec = dict(OFFICIAL_DEMO_TRAJECTORY)
    times = np.linspace(0, spec["t_max"], int(n_points))
    x = spec["x_scale"] * np.cos(times + spec["x_phase"])
    y = spec["y_scale"] * np.sin(times + spec["y_phase"])
    trajectory = np.stack([x, y], axis=1)
    return times, trajectory, spec


@contextmanager
def capture_numpy_permutation(seed: int) -> Iterator[list[Any]]:
    """Seed NumPy and record permutation outputs used by the official fit() shuffle."""
    import numpy as np

    recorded: list[Any] = []
    original = np.random.permutation

    def wrapped(x):
        result = original(x)
        recorded.append(np.asarray(result).tolist())
        return result

    rng_state = np.random.get_state()
    np.random.seed(int(seed))
    np.random.permutation = wrapped  # type: ignore[method-assign]
    try:
        yield recorded
    finally:
        np.random.permutation = original  # type: ignore[method-assign]
        np.random.set_state(rng_state)


def candidate_infix(tree: Any) -> str | None:
    if tree is None:
        return None
    if hasattr(tree, "infix"):
        try:
            return str(tree.infix())
        except Exception:
            return str(tree)
    return str(tree)


def load_odebench_equations(package_root: Path | None = None) -> list[dict[str, Any]]:
    install_odeformer_path(package_root)
    from odeformer.odebench.strogatz_equations import equations

    return list(equations)


def odebench_summary(equations: list[dict[str, Any]]) -> dict[str, Any]:
    counts: dict[int, int] = {}
    for item in equations:
        dim = int(item["dim"])
        counts[dim] = counts.get(dim, 0) + 1
    return {
        "n_systems": len(equations),
        "by_dimension": {str(k): counts[k] for k in sorted(counts)},
        "ids": [int(item["id"]) for item in equations],
    }


def fit_source_uses_permutation(sklearn_wrapper_path: Path) -> bool:
    text = sklearn_wrapper_path.read_text(encoding="utf-8")
    return "np.random.permutation" in text and "scaled_times[i] = scaled_time[permutation]" in text


def directory_fingerprint(path: Path) -> str:
    """SHA256 over relative paths and file hashes, skipping bytecode caches."""
    import hashlib

    digest = hashlib.sha256()
    if not path.is_dir():
        raise FileNotFoundError(path)
    files = [
        file_path
        for file_path in sorted(path.rglob("*"))
        if file_path.is_file()
        and "__pycache__" not in file_path.parts
        and file_path.suffix not in {".pyc", ".pyo"}
    ]
    for file_path in files:
        rel = file_path.relative_to(path).as_posix().encode("utf-8")
        digest.update(rel)
        digest.update(b"\0")
        digest.update(sha256_file(file_path).encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def classify_demo_exception(exc: BaseException) -> str:
    message = str(exc).lower()
    name = type(exc).__name__
    oom = "out of memory" in message or ("cuda" in message and "memory" in message)
    if name in {"OutOfMemoryError", "RuntimeError"} and oom:
        return "OOM"
    if name in {"TimeoutError", "MyTimeoutError"} or "timed out" in message:
        return "BeamDecodeTimeout"
    return name
