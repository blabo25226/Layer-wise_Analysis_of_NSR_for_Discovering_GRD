"""Lazy ODEFormer runtime helpers for scaler and simplifier stages."""

from __future__ import annotations

import json
import subprocess
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any

import numpy as np

from experiment_runtime import REPO_ROOT
from gpu_run4.formulas import split_components

from gpu_runmultiai.constants import SIMPLIFIER_SUBPROCESS_TIMEOUT_SEC
from gpu_runmultiai.guard_side_channel import child_side_channel_path, load_guard_attempts


class ODEFormerUnavailable(RuntimeError):
    pass


class IdentityScaler:
    """Frozen B1 identity scaler parameters (s=1, a_t=1, b_t=0)."""

    def __init__(self, dimension: int) -> None:
        self.dimension = dimension
        self.time_scale = 1
        self.time_shift = 0
        self.rescale_features = True
        self.traj_scale = np.ones(dimension, dtype=float)
        self.feature_scale = 1

    def get_params(self):
        scale = self.feature_scale / self.traj_scale
        return (1.0, 0.0, scale)

    def rescale_function(self, env, tree, a_t, b_t, scale):
        return tree


def require_odeformer() -> None:
    try:
        import sklearn  # noqa: F401
        import torch  # noqa: F401
    except ImportError as exc:
        raise ODEFormerUnavailable(
            "ODEFormer runtime requires torch and scikit-learn for scaler/simplifier stages"
        ) from exc


@lru_cache(maxsize=1)
def get_env() -> Any:
    require_odeformer()
    from gpu_run4_runtime import install_odeformer_path

    install_odeformer_path()
    from odeformer.envs.environment import FunctionEnvironment
    from parsers import get_parser

    params = get_parser().parse_args([])
    params.float_precision = 3
    params.use_two_hot = False
    params.use_sympy = False
    params.max_int = 10
    params.max_unary_depth = 6
    params.prob_prefactor = 0.0
    return FunctionEnvironment(params)


def prefix_tokens_for_system(prefixes: list[str]) -> list[str]:
    tokens: list[str] = []
    for index, prefix in enumerate(prefixes):
        if index:
            tokens.append("|")
        tokens.extend(prefix.split(","))
    return tokens


def decode_system_tree(env: Any, prefixes: list[str]) -> Any:
    tokens = prefix_tokens_for_system(prefixes)
    tree = env.equation_encoder.decode(tokens)
    if tree is None:
        raise ValueError("failed to decode system prefix")
    return tree


def tree_to_system_infix(tree: Any) -> str:
    if hasattr(tree, "infix"):
        return str(tree.infix())
    return str(tree)


def tree_to_prefix_list(tree: Any) -> list[str]:
    raw = tree.prefix() if hasattr(tree, "prefix") else str(tree)
    return [part.strip().strip(",") for part in raw.split("|") if part.strip().strip(",")]


def build_production_scaler(s: float, dimension: int) -> tuple[Any, dict[str, Any]]:
    require_odeformer()
    from odeformer.model.utils_wrapper import Scaler

    time = np.linspace(0.0, 10.0, 150)
    trajectory = np.full((150, dimension), s, dtype=float)
    scaler = Scaler(time_range=[1, 10], feature_scale=1, rescale_features=True)
    scaler.fit(time, trajectory)
    a_t, b_t, scale = scaler.get_params()
    asserts = {
        "time_scale": scaler.time_scale,
        "time_shift": scaler.time_shift,
        "a_t": float(a_t),
        "b_t": float(b_t),
        "rescale_features": bool(scaler.rescale_features),
    }
    return scaler, asserts


def build_identity_scaler(dimension: int) -> tuple[IdentityScaler, dict[str, Any]]:
    scaler = IdentityScaler(dimension)
    asserts = {
        "time_scale": scaler.time_scale,
        "time_shift": scaler.time_shift,
        "a_t": 1.0,
        "b_t": 0.0,
        "rescale_features": bool(scaler.rescale_features),
    }
    return scaler, asserts


def measure_g0_scaler_asserts(dimension: int, *, scale: float = 0.1) -> dict[str, Any]:
    _, asserts = build_production_scaler(scale, dimension)
    return asserts


def _substitute_variables_forward(prefix: list[str], scale: np.ndarray) -> list[str]:
    idx = 0
    while idx < len(prefix):
        token = prefix[idx]
        if token.startswith("x_"):
            dim = int(token.split("_")[1])
            s_j = str(float(scale[dim]))
            prefix = prefix[:idx] + ["div", token, s_j] + prefix[idx + 1 :]
            idx += 3
        else:
            idx += 1
    return prefix


def forward_scale_system(env: Any, tree: Any, scaler: Any) -> Any:
    """Apply g_i(z) = (scale_i/a_t) f_i(z/scale) on the full ordered system."""
    a_t, _, scale = scaler.get_params()
    scale_arr = np.asarray(scale, dtype=float)
    nodes = tree.prefix().split("|") if hasattr(tree, "prefix") else []
    if len(nodes) > len(scale_arr):
        raise ValueError("forward scale dimension mismatch")
    rebuilt: list[str] = []
    for index, node_str in enumerate(nodes):
        prefix = [token for token in node_str.split(",") if token]
        prefix = _substitute_variables_forward(prefix, scale_arr)
        factor = str(float(scale_arr[index]) / float(a_t))
        scaled_prefix = ["mul", factor] + prefix
        rebuilt.append(",".join(scaled_prefix))
    full_prefix: list[str] = []
    for index, part in enumerate(rebuilt):
        if index:
            full_prefix.append("|")
        full_prefix.extend(part.split(","))
    return env.word_to_infix(full_prefix, is_float=False, str_array=False)


def rescale_system(env: Any, scaler: Any, tree: Any) -> tuple[Any, bool]:
    a_t, b_t, scale = scaler.get_params()
    nodes = tree.prefix().split("|") if hasattr(tree, "prefix") else []
    if len(nodes) > len(scale):
        return tree, True
    rescaled = scaler.rescale_function(env, tree, a_t, b_t, scale)
    return rescaled, False


def simplify_tree_subprocess(
    prefixes: list[str],
    *,
    timeout_sec: float = SIMPLIFIER_SUBPROCESS_TIMEOUT_SEC,
) -> dict[str, Any]:
    worker = REPO_ROOT / "src/gpu_runmultiai/simplifier_worker.py"
    payload = json.dumps({"prefixes": prefixes, "timeout_sec": timeout_sec})
    side_channel = child_side_channel_path()
    if side_channel.is_file():
        side_channel.unlink()
    try:
        proc = subprocess.run(
            [sys.executable, str(worker)],
            input=payload,
            text=True,
            capture_output=True,
            timeout=timeout_sec,
            cwd=str(REPO_ROOT),
        )
    except subprocess.TimeoutExpired as exc:
        guard_attempts = _merge_guard_attempts(
            _guard_attempts_from_timeout_output(exc),
            load_guard_attempts(side_channel),
        )
        return {
            "ok": False,
            "failure_reason": "SubprocessTimeout",
            "guard_attempts": guard_attempts,
        }

    guard_attempts = _merge_guard_attempts(
        _guard_attempts_from_process_output(proc.stdout, proc.stderr),
        load_guard_attempts(side_channel),
    )
    if proc.returncode != 0:
        return {
            "ok": False,
            "failure_reason": proc.stderr.strip() or "subprocess_failure",
            "guard_attempts": guard_attempts,
        }
    try:
        result_payload = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return {
            "ok": False,
            "failure_reason": "JSONDecodeError",
            "guard_attempts": guard_attempts,
        }
    if not result_payload.get("guard_attempts"):
        result_payload["guard_attempts"] = guard_attempts
    else:
        result_payload["guard_attempts"] = _merge_guard_attempts(
            result_payload.get("guard_attempts", []),
            guard_attempts,
        )
    return result_payload


def _merge_guard_attempts(*groups: list[dict[str, str]]) -> list[dict[str, str]]:
    merged: list[dict[str, str]] = []
    seen: set[tuple[str, str, str]] = set()
    for group in groups:
        for row in group:
            key = (
                row.get("attempted_operation", ""),
                row.get("attempted_path_norm", ""),
                row.get("attempted_path_real", ""),
            )
            if key in seen:
                continue
            seen.add(key)
            merged.append(row)
    return merged


def _guard_attempts_from_process_output(stdout: str, stderr: str) -> list[dict[str, str]]:
    for blob in (stdout, stderr):
        text = str(blob or "").strip()
        if not text:
            continue
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            continue
        attempts = payload.get("guard_attempts")
        if isinstance(attempts, list):
            return attempts
    return []


def _guard_attempts_from_timeout_output(exc: subprocess.TimeoutExpired) -> list[dict[str, str]]:
    stdout = exc.stdout
    stderr = exc.stderr
    if isinstance(stdout, bytes):
        stdout = stdout.decode("utf-8", errors="replace")
    if isinstance(stderr, bytes):
        stderr = stderr.decode("utf-8", errors="replace")
    return _guard_attempts_from_process_output(str(stdout or ""), str(stderr or ""))


def replace_component_prefixes(record: dict[str, Any], component_idx: int, new_prefix: str) -> list[str]:
    prefixes = split_components(record["teacher_prefix"])
    prefixes[component_idx] = new_prefix
    return prefixes


def truth_system_prefixes(record: dict[str, Any]) -> list[str]:
    return split_components(record["teacher_prefix"])


def full_system_infix_from_record(record: dict[str, Any]) -> str:
    from gpu_runmultiai.oracle import prefix_to_infix_component

    return " | ".join(prefix_to_infix_component(prefix) for prefix in truth_system_prefixes(record))
