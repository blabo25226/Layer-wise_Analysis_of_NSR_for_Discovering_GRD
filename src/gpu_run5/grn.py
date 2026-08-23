"""Closed Hill-type GRN systems and trajectory generation for GPU_RUN5.

Splits are made at the parameterized-system level.  Five trajectories belonging
to one system are never split across train/validation/test.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Callable

import numpy as np
from scipy.integrate import solve_ivp
from scipy.stats import qmc


@dataclass(frozen=True)
class FamilySpec:
    family: str
    dimension: int
    description: str


FAMILIES = {
    "R01": FamilySpec("R01", 1, "self activation"),
    "R02": FamilySpec("R02", 1, "self repression"),
    "R03": FamilySpec("R03", 2, "toggle switch"),
    "R04": FamilySpec("R04", 2, "activation cascade"),
    "R05": FamilySpec("R05", 2, "mutual activation"),
    "R06": FamilySpec("R06", 3, "repressilator"),
    "R07": FamilySpec("R07", 3, "coherent feed-forward loop"),
    "R08": FamilySpec("R08", 3, "compound activation"),
}


def _add(a: str, b: str) -> str:
    return f"add,{a},{b}"


def _mul(a: str, b: str) -> str:
    return f"mul,{a},{b}"


def _neg(a: str) -> str:
    return _mul("-1", a)


def _power(a: str, n: int) -> str:
    if n == 1:
        return a
    if n == 2:
        return f"pow2,{a}"
    if n == 4:
        return f"pow2,pow2,{a}"
    raise ValueError(f"unsupported Hill exponent: {n}")


def _act(x: str, alpha: float, k: float, n: int) -> str:
    xn = _power(x, n)
    return _mul(_mul(f"{alpha:.4g}", xn), f"inv,{_add(f'{k**n:.4g}', xn)}")


def _rep(x: str, alpha: float, k: float, n: int) -> str:
    xn = _power(x, n)
    return _mul(f"{alpha * k**n:.4g}", f"inv,{_add(f'{k**n:.4g}', xn)}")


def _decay(x: str, beta: float) -> str:
    return _neg(_mul(f"{beta:.4g}", x))


def _evaluate_prefix(prefix: str, state: np.ndarray) -> float:
    tokens = prefix.split(",")

    def consume(index: int) -> tuple[float, int]:
        token = tokens[index]
        if token in {"add", "mul"}:
            left, next_index = consume(index + 1)
            right, next_index = consume(next_index)
            return (left + right if token == "add" else left * right), next_index
        if token in {"inv", "pow2", "pow3"}:
            value, next_index = consume(index + 1)
            if token == "inv":
                return 1.0 / value, next_index
            return value ** int(token[-1]), next_index
        if token.startswith("x_"):
            return float(state[int(token[2:])]), index + 1
        return float(token), index + 1

    value, consumed = consume(0)
    if consumed != len(tokens):
        raise ValueError(f"unconsumed prefix tokens: {tokens[consumed:]}")
    return value


def _hill_act(x: float, alpha: float, k: float, n: int) -> float:
    xn = max(float(x), 0.0) ** n
    return alpha * xn / (k**n + xn)


def _hill_rep(x: float, alpha: float, k: float, n: int) -> float:
    xn = max(float(x), 0.0) ** n
    return alpha * k**n / (k**n + xn)


def _parameters(unit: np.ndarray, exponent: int) -> dict[str, float | int]:
    values = np.asarray(unit, dtype=float)
    return {
        "a1": float(0.8 + 1.7 * values[0]),
        "a2": float(0.8 + 1.7 * values[1]),
        "a3": float(0.8 + 1.7 * values[2]),
        "k1": float(0.4 + 1.2 * values[3]),
        "k2": float(0.4 + 1.2 * values[4]),
        "k3": float(0.4 + 1.2 * values[5]),
        "b1": float(0.25 + 0.65 * values[6]),
        "b2": float(0.25 + 0.65 * values[7]),
        "b3": float(0.25 + 0.65 * values[8]),
        "basal": float(0.03 + 0.17 * values[9]),
        "n": int(exponent),
    }


def system_definition(family: str, params: dict[str, Any]) -> tuple[Callable[[float, np.ndarray], np.ndarray], list[str]]:
    p = params
    n = int(p["n"])
    d = FAMILIES[family].dimension

    def rhs(_t: float, x: np.ndarray) -> np.ndarray:
        if family == "R01":
            return np.array([p["basal"] + _hill_act(x[0], p["a1"], p["k1"], n) - p["b1"] * x[0]])
        if family == "R02":
            return np.array([_hill_rep(x[0], p["a1"], p["k1"], n) - p["b1"] * x[0]])
        if family == "R03":
            return np.array([
                _hill_rep(x[1], p["a1"], p["k1"], n) - p["b1"] * x[0],
                _hill_rep(x[0], p["a2"], p["k2"], n) - p["b2"] * x[1],
            ])
        if family == "R04":
            return np.array([
                p["a1"] - p["b1"] * x[0],
                _hill_act(x[0], p["a2"], p["k2"], n) - p["b2"] * x[1],
            ])
        if family == "R05":
            return np.array([
                p["basal"] + _hill_act(x[1], p["a1"], p["k1"], n) - p["b1"] * x[0],
                p["basal"] + _hill_act(x[0], p["a2"], p["k2"], n) - p["b2"] * x[1],
            ])
        if family == "R06":
            return np.array([
                _hill_rep(x[2], p["a1"], p["k1"], n) - p["b1"] * x[0],
                _hill_rep(x[0], p["a2"], p["k2"], n) - p["b2"] * x[1],
                _hill_rep(x[1], p["a3"], p["k3"], n) - p["b3"] * x[2],
            ])
        if family == "R07":
            return np.array([
                p["a1"] - p["b1"] * x[0],
                _hill_act(x[0], p["a2"], p["k2"], n) - p["b2"] * x[1],
                _hill_act(x[0], p["a3"], p["k3"], n) * _hill_act(x[1], 1.0, p["k2"], n) - p["b3"] * x[2],
            ])
        product = max(float(x[0] * x[1]), 0.0)
        return np.array([
            p["a1"] - p["b1"] * x[0],
            p["a2"] - p["b2"] * x[1],
            _hill_act(product, p["a3"], p["k3"], n) - p["b3"] * x[2],
        ])

    if family == "R01":
        exprs = [_add(f"{p['basal']:.4g}", _add(_act("x_0", p["a1"], p["k1"], n), _decay("x_0", p["b1"])))]
    elif family == "R02":
        exprs = [_add(_rep("x_0", p["a1"], p["k1"], n), _decay("x_0", p["b1"]))]
    elif family == "R03":
        exprs = [
            _add(_rep("x_1", p["a1"], p["k1"], n), _decay("x_0", p["b1"])),
            _add(_rep("x_0", p["a2"], p["k2"], n), _decay("x_1", p["b2"])),
        ]
    elif family == "R04":
        exprs = [_add(f"{p['a1']:.4g}", _decay("x_0", p["b1"])), _add(_act("x_0", p["a2"], p["k2"], n), _decay("x_1", p["b2"]))]
    elif family == "R05":
        exprs = [
            _add(f"{p['basal']:.4g}", _add(_act("x_1", p["a1"], p["k1"], n), _decay("x_0", p["b1"]))),
            _add(f"{p['basal']:.4g}", _add(_act("x_0", p["a2"], p["k2"], n), _decay("x_1", p["b2"]))),
        ]
    elif family == "R06":
        exprs = [
            _add(_rep("x_2", p["a1"], p["k1"], n), _decay("x_0", p["b1"])),
            _add(_rep("x_0", p["a2"], p["k2"], n), _decay("x_1", p["b2"])),
            _add(_rep("x_1", p["a3"], p["k3"], n), _decay("x_2", p["b3"])),
        ]
    elif family == "R07":
        combined = _mul(_act("x_0", p["a3"], p["k3"], n), _act("x_1", 1.0, p["k2"], n))
        exprs = [
            _add(f"{p['a1']:.4g}", _decay("x_0", p["b1"])),
            _add(_act("x_0", p["a2"], p["k2"], n), _decay("x_1", p["b2"])),
            _add(combined, _decay("x_2", p["b3"])),
        ]
    else:
        product = _mul("x_0", "x_1")
        exprs = [
            _add(f"{p['a1']:.4g}", _decay("x_0", p["b1"])),
            _add(f"{p['a2']:.4g}", _decay("x_1", p["b2"])),
            _add(_act(product, p["a3"], p["k3"], n), _decay("x_2", p["b3"])),
        ]
    assert len(exprs) == d

    # The quantized teacher expression is the numerical source of truth.  This
    # prevents a hidden mismatch between full-precision Python parameters and
    # the finite-precision token sequence used for fine-tuning.
    def teacher_rhs(_t: float, state: np.ndarray) -> np.ndarray:
        return np.asarray([_evaluate_prefix(expr, state) for expr in exprs], dtype=float)

    return teacher_rhs, exprs


def trajectory_checksum(times: np.ndarray, trajectory: np.ndarray) -> str:
    digest = hashlib.sha256()
    digest.update(np.asarray(times, dtype="<f8").tobytes())
    digest.update(np.asarray(trajectory, dtype="<f8").tobytes())
    return digest.hexdigest()


def generate_corpus(
    *,
    variants: dict[str, int],
    n_points: int,
    t_span: tuple[float, float],
    seed: int,
    trajectory_seed: int | None = None,
    rtol: float,
    atol: float,
    minimum_variance: float,
    maximum_abs_state: float,
) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    rejections: list[dict[str, Any]] = []
    ic_seed = int(seed if trajectory_seed is None else trajectory_seed)
    split_offsets = {"train": 0, "validation": 100_000, "test": 200_000}
    for split, count in variants.items():
        for family_index, family in enumerate(FAMILIES):
            sampler = qmc.LatinHypercube(d=10, seed=seed + split_offsets[split] + family_index)
            units = sampler.random(max(int(count) * 10, int(count)))
            accepted = 0
            for attempt_index, unit in enumerate(units):
                if accepted >= int(count):
                    break
                variant_index = accepted
                exponent = (1, 2, 4)[variant_index % 3]
                params = _parameters(unit, exponent)
                rhs, components = system_definition(family, params)
                system_id = f"{family}_{split}_d{seed}_{variant_index:03d}"
                attempt_id = f"{family}_{split}_d{seed}_attempt{attempt_index:03d}"
                rng = np.random.default_rng(ic_seed + split_offsets[split] + family_index * 10_000 + attempt_index)
                trajectories = []
                for role, role_index in [("input", 0), ("selection", 0), ("selection", 1), ("generalization", 0), ("generalization", 1)]:
                    y0 = rng.uniform(0.05, 2.5, size=FAMILIES[family].dimension)
                    times = np.linspace(float(t_span[0]), float(t_span[1]), int(n_points))
                    sol = solve_ivp(rhs, t_span, y0, t_eval=times, method="RK45", rtol=rtol, atol=atol)
                    failure = None
                    if not sol.success or sol.y.shape != (FAMILIES[family].dimension, len(times)):
                        failure = "integration_failure"
                    elif not np.isfinite(sol.y).all():
                        failure = "non_finite"
                    elif np.max(np.abs(sol.y)) > maximum_abs_state:
                        failure = "divergent"
                    elif np.min(sol.y) < -1e-7:
                        failure = "negative_state"
                    elif float(np.min(np.var(sol.y, axis=1))) < minimum_variance:
                        failure = "insufficient_variance"
                    if failure:
                        rejections.append({"attempt_id": attempt_id, "role": role, "role_index": role_index, "reason": failure})
                        trajectories = []
                        break
                    trajectory = sol.y.T
                    trajectories.append({
                        "role": role,
                        "role_index": role_index,
                        "initial_condition": y0.tolist(),
                        "times": times.tolist(),
                        "trajectory": trajectory.tolist(),
                        "checksum": trajectory_checksum(times, trajectory),
                    })
                if trajectories:
                    records.append({
                        "system_id": system_id,
                        "family": family,
                        "description": FAMILIES[family].description,
                        "dimension": FAMILIES[family].dimension,
                        "split": split,
                        "variant_index": variant_index,
                        "parameters": params,
                        "teacher_prefix": "|".join(components),
                        "trajectories": trajectories,
                    })
                    accepted += 1
            if accepted < int(count):
                raise RuntimeError(f"could not generate {count} accepted systems for {family}/{split}; got {accepted}")
    rejected_attempts = len({row["attempt_id"] for row in rejections})
    attempted = len(records) + rejected_attempts
    rejection_rate = rejected_attempts / max(attempted, 1)
    fingerprint_payload = {
        "data_seed": seed,
        "trajectory_seed": ic_seed,
        "n_points": n_points,
        "t_span": t_span,
        "rtol": rtol,
        "atol": atol,
        "minimum_variance": minimum_variance,
        "maximum_abs_state": maximum_abs_state,
        "systems": [
            {"system_id": row["system_id"], "teacher_prefix": row["teacher_prefix"],
             "trajectory_checksums": [item["checksum"] for item in row["trajectories"]]}
            for row in records
        ],
    }
    fingerprint = hashlib.sha256(json.dumps(fingerprint_payload, sort_keys=True).encode()).hexdigest()
    return {
        "records": records, "rejections": rejections, "rejection_rate": rejection_rate,
        "fingerprint": fingerprint, "fingerprint_payload": fingerprint_payload,
    }
