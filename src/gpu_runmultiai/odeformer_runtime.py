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


def _substitute_variables_forward(prefix: list[str], traj_scale: np.ndarray) -> list[str]:
    idx = 0
    while idx < len(prefix):
        token = prefix[idx]
        if token.startswith("x_"):
            dim = int(token.split("_")[1])
            s_j = str(float(traj_scale[dim]))
            prefix = prefix[:idx] + ["div", token, s_j] + prefix[idx + 1 :]
            idx += 3
        else:
            idx += 1
    return prefix


def forward_scale_system(env: Any, tree: Any, scaler: Any) -> Any:
    """Apply g_i(z) = (s_i/a_t) f_i(z/s) on the full ordered system."""
    a_t, _, _ = scaler.get_params()
    traj_scale = scaler.traj_scale
    nodes = tree.prefix().split("|") if hasattr(tree, "prefix") else []
    if len(nodes) > len(traj_scale):
        raise ValueError("forward scale dimension mismatch")
    rebuilt: list[str] = []
    for index, node_str in enumerate(nodes):
        prefix = [token for token in node_str.split(",") if token]
        prefix = _substitute_variables_forward(prefix, traj_scale)
        factor = str(float(traj_scale[index]) / float(a_t))
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
    proc = subprocess.run(
        [sys.executable, str(worker)],
        input=payload,
        text=True,
        capture_output=True,
        timeout=timeout_sec + 0.5,
        cwd=str(REPO_ROOT),
    )
    if proc.returncode != 0:
        return {
            "ok": False,
            "failure_reason": proc.stderr.strip() or "subprocess_failure",
            "guard_attempts": [],
        }
    return json.loads(proc.stdout)


def replace_component_prefixes(record: dict[str, Any], component_idx: int, new_prefix: str) -> list[str]:
    prefixes = split_components(record["teacher_prefix"])
    prefixes[component_idx] = new_prefix
    return prefixes


def truth_system_prefixes(record: dict[str, Any]) -> list[str]:
    return split_components(record["teacher_prefix"])


def full_system_infix_from_record(record: dict[str, Any]) -> str:
    from gpu_runmultiai.oracle import prefix_to_infix_component

    return " | ".join(prefix_to_infix_component(prefix) for prefix in truth_system_prefixes(record))
