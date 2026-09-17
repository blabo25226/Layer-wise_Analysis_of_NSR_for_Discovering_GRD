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

from gpu_runmultiai.constants import MAX_SYSTEM_DIMENSION, SIMPLIFIER_SUBPROCESS_TIMEOUT_SEC
from gpu_runmultiai.guard_side_channel import child_side_channel_path, load_guard_attempts
from gpu_runmultiai.invariants import ScalerGateError

PRODUCTION_SCALER_MODULE = "odeformer.model.utils_wrapper"
PRODUCTION_RESCALE_QUALNAME = "Scaler.rescale_function"

PRODUCTION_TIME_RANGE = [1, 10]
PRODUCTION_TIME_GRID = (0.0, 10.0, 150)

# B1 identity parameters (a_t=1, b_t=0, scale=1) expressed purely through the
# production Scaler configuration: time_range=[0, 1] over t in [0, 1] gives
# a_t = 1/(1-0) = 1 and b_t = 0, and a constant unit trajectory gives scale = 1.
IDENTITY_TIME_RANGE = [0, 1]
IDENTITY_TIME_GRID = (0.0, 1.0, 150)
IDENTITY_TRAJECTORY_VALUE = 1.0

_LAST_RESCALE_CALL_PROOF: dict[str, Any] = {}


class ODEFormerUnavailable(RuntimeError):
    pass


def last_rescale_call_proof() -> dict[str, Any]:
    """Proof hook: parameters and callable identity of the most recent rescale call."""
    return dict(_LAST_RESCALE_CALL_PROOF)


def production_rescale_callable_identity(scaler: Any) -> tuple[str | None, str | None]:
    unbound = type(scaler).rescale_function
    return getattr(unbound, "__module__", None), getattr(unbound, "__qualname__", None)


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
    # The frozen corpus contains 3-dimensional systems; the ODEFormer default
    # (max_dimension=2) makes `x_2` undecodable, so §3.4.8 audit_word_to_infix
    # would return None for every d=3 system. Decoded output for d<=2 systems is
    # unchanged by this setting.
    params.max_dimension = MAX_SYSTEM_DIMENSION
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


MULTI_COMPONENT_SEPARATOR = ",|,"


def component_prefix_list_from_raw(raw: str) -> list[str]:
    """Split a system prefix into per-component comma-separated prefix strings (§3.4.8)."""
    text = str(raw or "")
    if MULTI_COMPONENT_SEPARATOR in text:
        return [part for part in text.split(MULTI_COMPONENT_SEPARATOR) if part]
    if "|" in text:
        return [part.strip().strip(",") for part in text.split("|") if part.strip().strip(",")]
    return [text] if text else []


def canonical_system_prefix_raw(tree_or_raw: Any) -> str:
    """Frozen comma-separated multi-component dialect for byte-identical E1/E2 comparison (§2.2)."""
    if hasattr(tree_or_raw, "prefix"):
        raw = str(tree_or_raw.prefix())
    else:
        raw = str(tree_or_raw or "")
    return MULTI_COMPONENT_SEPARATOR.join(component_prefix_list_from_raw(raw))


def tree_to_prefix_list(tree: Any) -> list[str]:
    raw = tree.prefix() if hasattr(tree, "prefix") else str(tree)
    return component_prefix_list_from_raw(str(raw))


def _fit_production_scaler(
    *,
    time_range: list[int],
    time_grid: tuple[float, float, int],
    feature_value: float,
    dimension: int,
) -> tuple[Any, dict[str, Any]]:
    require_odeformer()
    from gpu_run4_runtime import install_odeformer_path

    install_odeformer_path()
    from odeformer.model.utils_wrapper import Scaler

    start, stop, points = time_grid
    time = np.linspace(start, stop, points)
    trajectory = np.full((points, dimension), feature_value, dtype=float)
    scaler = Scaler(time_range=list(time_range), feature_scale=1, rescale_features=True)
    scaler.fit(time, trajectory)
    a_t, b_t, scale = scaler.get_params()
    asserts = {
        "time_scale": scaler.time_scale,
        "time_shift": scaler.time_shift,
        # +0.0 normalises the signed zero SymPy/NumPy may produce for b_t.
        "a_t": float(a_t) + 0.0,
        "b_t": float(b_t) + 0.0,
        "rescale_features": bool(scaler.rescale_features),
        "scale": [float(value) for value in np.asarray(scale, dtype=float).tolist()],
    }
    return scaler, asserts


def build_production_scaler(s: float, dimension: int) -> tuple[Any, dict[str, Any]]:
    return _fit_production_scaler(
        time_range=PRODUCTION_TIME_RANGE,
        time_grid=PRODUCTION_TIME_GRID,
        feature_value=float(s),
        dimension=dimension,
    )


def build_identity_scaler(dimension: int) -> tuple[Any, dict[str, Any]]:
    """B1 identity scaler: the production Scaler configured for a_t=1, b_t=0, scale=1."""
    scaler, asserts = _fit_production_scaler(
        time_range=IDENTITY_TIME_RANGE,
        time_grid=IDENTITY_TIME_GRID,
        feature_value=IDENTITY_TRAJECTORY_VALUE,
        dimension=dimension,
    )
    if asserts["a_t"] != 1.0 or asserts["b_t"] != 0.0 or any(
        value != 1.0 for value in asserts["scale"]
    ):
        raise ScalerGateError(
            "F5 FAIL: identity scaler must yield a_t=1.0, b_t=0.0, scale=1.0; got "
            f"a_t={asserts['a_t']}, b_t={asserts['b_t']}, scale={asserts['scale']}"
        )
    return scaler, asserts


def measure_g0_scaler_asserts(dimension: int, *, scale: float = 0.1) -> dict[str, Any]:
    _, asserts = build_production_scaler(scale, dimension)
    return asserts


def _production_decimal_token(value: float) -> str:
    return str(float(value))


def _rational_reciprocal_factor_prefix(numerator_token: str, denominator_token: str) -> list[str]:
    """Emit mul,numer,pow,denom,-1 instead of a rounded decimal quotient."""
    return ["mul", numerator_token, "pow", denominator_token, "-1"]


def _substitute_variables_forward(prefix: list[str], scale: np.ndarray) -> list[str]:
    idx = 0
    while idx < len(prefix):
        token = prefix[idx]
        if token.startswith("x_"):
            dim = int(token.split("_")[1])
            scale_token = _production_decimal_token(float(scale[dim]))
            prefix = prefix[:idx] + ["div", token, scale_token] + prefix[idx + 1 :]
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
    a_t_token = _production_decimal_token(float(a_t))
    rebuilt: list[str] = []
    for index, node_str in enumerate(nodes):
        prefix = [token for token in node_str.split(",") if token]
        prefix = _substitute_variables_forward(prefix, scale_arr)
        scale_token = _production_decimal_token(float(scale_arr[index]))
        factor_prefix = _rational_reciprocal_factor_prefix(scale_token, a_t_token)
        scaled_prefix = ["mul"] + factor_prefix + prefix
        rebuilt.append(",".join(scaled_prefix))
    full_prefix: list[str] = []
    for index, part in enumerate(rebuilt):
        if index:
            full_prefix.append("|")
        full_prefix.extend(part.split(","))
    return env.word_to_infix(full_prefix, is_float=False, str_array=False)


def rescale_system(env: Any, scaler: Any, tree: Any) -> tuple[Any, bool, dict[str, Any]]:
    """Execute the frozen production rescale (§3.4.8) and detect both early returns (§5.2)."""
    module, qualname = production_rescale_callable_identity(scaler)
    if module != PRODUCTION_SCALER_MODULE or qualname != PRODUCTION_RESCALE_QUALNAME:
        raise ScalerGateError(
            "F5 FAIL: rescale must execute the production "
            f"{PRODUCTION_SCALER_MODULE}.{PRODUCTION_RESCALE_QUALNAME}; got {module}.{qualname}"
        )
    a_t, b_t, scale = scaler.get_params()
    input_nodes = len(tree.prefix().split("|")) if hasattr(tree, "prefix") else None
    rescaled = scaler.rescale_function(env, tree, a_t, b_t, scale)
    # §5.2: the only two untransformed return paths are detected by object identity.
    rescale_incomplete = rescaled is tree
    proof = {
        "rescale_callable_module": module,
        "rescale_callable_qualname": qualname,
        "a_t": float(a_t) + 0.0,
        "b_t": float(b_t) + 0.0,
        "scale": [float(value) for value in np.asarray(scale, dtype=float).tolist()],
        "input_node_count": input_nodes,
        "rescale_incomplete": rescale_incomplete,
        "returned_input_tree": rescale_incomplete,
    }
    _LAST_RESCALE_CALL_PROOF.clear()
    _LAST_RESCALE_CALL_PROOF.update(proof)
    return rescaled, rescale_incomplete, proof


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
