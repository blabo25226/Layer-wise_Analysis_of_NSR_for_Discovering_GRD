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
from gpu_run4.formulas import split_components, tree_to_infix
from gpu_run4_runtime import install_odeformer_path

from gpu_runmultiai.constants import SIMPLIFIER_SUBPROCESS_TIMEOUT_SEC


class ODEFormerUnavailable(RuntimeError):
    pass


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
    install_odeformer_path()
    from odeformer.envs.environment import FunctionEnvironment

    class Params:
        float_precision = 3
        max_size = 20
        use_two_hot = False
        use_sympy = False
        max_int = 10
        max_unary_depth = 6
        prob_prefactor = 0.0

    return FunctionEnvironment(Params())


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


def rescale_system(env: Any, scaler: Any, tree: Any) -> tuple[Any, bool]:
    a_t, b_t, scale = scaler.get_params()
    nodes = tree.prefix().split("|") if hasattr(tree, "prefix") else []
    if len(nodes) > len(scale):
        return tree, True
    rescaled = scaler.rescale_function(env, tree, a_t, b_t, scale)
    return rescaled, False


def simplify_tree_subprocess(prefixes: list[str], timeout_sec: float = SIMPLIFIER_SUBPROCESS_TIMEOUT_SEC) -> dict[str, Any]:
    worker = REPO_ROOT / "src/gpu_runmultiai/simplifier_worker.py"
    payload = json.dumps({"prefixes": prefixes, "timeout_sec": timeout_sec})
    proc = subprocess.run(
        [sys.executable, str(worker)],
        input=payload,
        text=True,
        capture_output=True,
        timeout=timeout_sec + 2.0,
        cwd=str(REPO_ROOT),
    )
    if proc.returncode != 0:
        return {"ok": False, "failure_reason": proc.stderr.strip() or "subprocess_failure"}
    return json.loads(proc.stdout)


def replace_component_prefixes(record: dict[str, Any], component_idx: int, new_prefix: str) -> list[str]:
    prefixes = split_components(record["teacher_prefix"])
    prefixes[component_idx] = new_prefix
    return prefixes
