"""Enzyme-kinetics effective laws and complexity-matched polynomial controls.

All systems are generated directly in ODEFormer's native input coordinates:
time in [1, 10] and every observed variable that starts away from zero starts at
1 (the official ``Scaler`` maps any input to exactly this frame). Because the
data already live in that frame, inference uses ``rescale=False`` and the true
law written below is exactly the teacher sequence the decoder should emit.

Families
--------
Rational (effective laws of enzyme mechanisms, variable denominator):
  MM_S    substrate view of Michaelis-Menten     dx/dt = -V x / (K + x)
  MM_P    product view (progress curve, p0 = 0)  dx/dt =  V (1 - x) / (K + 1 - x)
  SI      substrate inhibition                   dx/dt = -V x / (K + x + x^2 / Ki)
  HILL2   cooperative binding, n = 2             dx/dt = -V x^2 / (K + x^2)
Polynomial controls (same token budget, decaying, no denominator):
  LIN     first-order decay                      dx/dt = -a x
  QUAD    decay with quadratic correction        dx/dt = -a x + b x^2
  QUAD2   decay with quadratic loss              dx/dt = -a x - b x^2
Full mass-action mechanism E + S <-> C -> E + P observed as (s, c):
  MA_SC   ds/dt = -k1 e0 s + k1 s c + km1 c ;  dc/dt = k1 e0 s - k1 s c - (km1 + k2) c
  MA_S    the same simulation observed through s only (QSSA effective law = MM_S)
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from typing import Any, Callable

import numpy as np
import sympy as sp
from scipy.integrate import solve_ivp

T_SPAN = (1.0, 10.0)
N_POINTS = 100
RATIONAL_1D = ("MM_S", "MM_P", "SI", "HILL2")
POLY_1D = ("LIN", "QUAD", "QUAD2")
FAMILIES_1D = RATIONAL_1D + POLY_1D
ALL_FAMILIES = FAMILIES_1D + ("MA_SC", "MA_S")

# Expected structural class of the true law (see ``structural_class``).
TRUE_CLASS = {
    "MM_S": "R[1/1]",
    "MM_P": "R[1/1]",
    "SI": "R[1/2]",
    "HILL2": "R[2/2]",
    "LIN": "P[1]",
    "QUAD": "P[2]",
    "QUAD2": "P[2]",
    "MA_S": "R[1/1]",
}


def _c(value: float) -> str:
    return f"{value:.4g}"


@dataclass
class System:
    family: str
    params: dict[str, float]
    prefix: str  # ODEFormer prefix, components joined by ",|,"
    rhs: Callable[[float, np.ndarray], np.ndarray]
    dimension: int
    x0: np.ndarray
    observe: tuple[int, ...]  # observed state indices of the simulated state


def _depletion_rate(K: float, end: float) -> float:
    """V such that dx/dt = -Vx/(K+x) goes from 1 to ``end`` over the time span."""
    return (K * math.log(1.0 / end) + (1.0 - end)) / (T_SPAN[1] - T_SPAN[0])


def make_system(family: str, rng: np.random.Generator) -> System:
    """Sample one system. Parameters are drawn so that the observed curve spans its range."""
    end = float(rng.uniform(0.05, 0.4))  # remaining fraction at t = 10
    if family in ("MM_S", "MM_P", "SI", "HILL2", "MA_S", "MA_SC"):
        K = float(10 ** rng.uniform(math.log10(0.03), math.log10(30.0)))
    if family == "MM_S":
        V = _depletion_rate(K, end)
        prefix = f"mul,{_c(-V)},mul,x_0,inv,add,{_c(K)},x_0"
        rhs = lambda t, x: np.array([-V * x[0] / (K + x[0])])
        return System(family, {"V": V, "K": K, "end": end}, prefix, rhs, 1, np.array([1.0]), (0,))
    if family == "MM_P":
        V = _depletion_rate(K, end)
        prefix = f"mul,{_c(V)},mul,add,1,mul,-1,x_0,inv,add,{_c(K + 1.0)},mul,-1,x_0"
        rhs = lambda t, x: np.array([V * (1.0 - x[0]) / (K + 1.0 - x[0])])
        return System(family, {"V": V, "K": K, "end": end}, prefix, rhs, 1, np.array([0.0]), (0,))
    if family == "SI":
        Ki = float(10 ** rng.uniform(math.log10(0.1), math.log10(2.0)))
        # V chosen numerically below to hit the depletion target.
        def law(V: float) -> Callable:
            return lambda t, x: np.array([-V * x[0] / (K + x[0] + x[0] ** 2 / Ki)])
        V = _calibrate(law, end)
        prefix = f"mul,{_c(-V)},mul,x_0,inv,add,{_c(K)},add,x_0,mul,{_c(1.0 / Ki)},pow2,x_0"
        return System(family, {"V": V, "K": K, "Ki": Ki, "end": end}, prefix, law(V), 1, np.array([1.0]), (0,))
    if family == "HILL2":
        def law(V: float) -> Callable:
            return lambda t, x: np.array([-V * x[0] ** 2 / (K + x[0] ** 2)])
        V = _calibrate(law, end)
        prefix = f"mul,{_c(-V)},mul,pow2,x_0,inv,add,{_c(K)},pow2,x_0"
        return System(family, {"V": V, "K": K, "end": end}, prefix, law(V), 1, np.array([1.0]), (0,))
    if family == "LIN":
        a = math.log(1.0 / end) / (T_SPAN[1] - T_SPAN[0])
        prefix = f"mul,{_c(-a)},x_0"
        return System(family, {"a": a, "end": end}, prefix, lambda t, x: np.array([-a * x[0]]), 1, np.array([1.0]), (0,))
    if family in ("QUAD", "QUAD2"):
        ratio = float(rng.uniform(0.2, 0.8))  # |b| / a, keeps the law monotone decaying on [0, 1]
        sign = 1.0 if family == "QUAD" else -1.0

        def law(a: float) -> Callable:
            b = sign * ratio * a
            return lambda t, x: np.array([-a * x[0] + b * x[0] ** 2])
        a = _calibrate(law, end)
        b = sign * ratio * a
        prefix = f"add,mul,{_c(-a)},x_0,mul,{_c(b)},pow2,x_0"
        return System(family, {"a": a, "b": b, "end": end}, prefix, law(a), 1, np.array([1.0]), (0,))
    if family in ("MA_SC", "MA_S"):
        # Mechanism with e0 / (S0 + K) small, so the QSSA reduction is accurate on the substrate view.
        e0 = float(10 ** rng.uniform(-2.0, -1.0))
        Vmax = _depletion_rate(K, end)
        k2 = Vmax / e0
        k1 = float(10 ** rng.uniform(1.0, 2.0)) * k2  # fast binding
        km1 = max(K * k1 - k2, 0.0)
        K_eff = (km1 + k2) / k1

        # State (s, y) with y = c / e0 the bound-enzyme fraction (0 <= y <= 1).
        def rhs(t: float, state: np.ndarray) -> np.ndarray:
            s, y = state
            return np.array([-k1 * e0 * (1 - y) * s + km1 * e0 * y, k1 * (1 - y) * s - (km1 + k2) * y])

        params = {"e0": e0, "k1": k1, "km1": km1, "k2": k2, "K": K_eff, "Vmax": Vmax, "end": end}
        if family == "MA_SC":
            ds = f"add,mul,{_c(-k1 * e0)},x_0,add,mul,{_c(k1 * e0)},mul,x_0,x_1,mul,{_c(km1 * e0)},x_1"
            dc = f"add,mul,{_c(k1)},x_0,add,mul,{_c(-k1)},mul,x_0,x_1,mul,{_c(-(km1 + k2))},x_1"
            return System(family, params, f"{ds},|,{dc}", rhs, 2, np.array([1.0, 0.0]), (0, 1))
        prefix = f"mul,{_c(-Vmax)},mul,x_0,inv,add,{_c(K_eff)},x_0"
        return System(family, params, prefix, rhs, 2, np.array([1.0, 0.0]), (0,))
    raise KeyError(family)


def _calibrate(law_factory: Callable[[float], Callable], end: float) -> float:
    """Bisection on the rate so that the 1D decay ends at ``end`` (monotone in the rate)."""
    lo, hi = 1e-4, 50.0
    for _ in range(60):
        mid = math.sqrt(lo * hi)
        value = _simulate(law_factory(mid), np.array([1.0]), np.array([T_SPAN[1]]))[-1, 0]
        if value > end:
            lo = mid
        else:
            hi = mid
    return math.sqrt(lo * hi)


def _simulate(rhs: Callable, x0: np.ndarray, t_eval: np.ndarray) -> np.ndarray:
    sol = solve_ivp(rhs, T_SPAN, x0, t_eval=t_eval, method="LSODA", rtol=1e-10, atol=1e-12)
    if not sol.success:
        raise RuntimeError(sol.message)
    return sol.y.T


def times() -> np.ndarray:
    return np.linspace(T_SPAN[0], T_SPAN[1], N_POINTS)


def generalization_x0(system: System) -> list[np.ndarray]:
    """Held-out initial conditions in the same units (law unchanged)."""
    if system.family == "MM_P":
        return [np.array([0.3])]
    if system.dimension == 2:
        return [np.array([0.6, 0.0])]
    return [np.array([0.6]), np.array([1.2])]  # below QUAD's unstable fixed point 1/ratio >= 1.25


def make_problem(family: str, seed: int, index: int, noise_sigma: float = 0.0) -> dict[str, Any]:
    rng = np.random.default_rng([seed, index, ALL_FAMILIES.index(family)])
    system = make_system(family, rng)
    t = times()
    full = _simulate(system.rhs, system.x0, t)
    observed = full[:, list(system.observe)]
    if noise_sigma > 0:
        noise_rng = np.random.default_rng([seed, index, 7919])
        scale = np.maximum(np.abs(observed), 1e-3)
        observed = observed + noise_sigma * scale * noise_rng.standard_normal(observed.shape)
    gens = []
    for x0 in generalization_x0(system):
        x0_full = x0 if system.dimension == len(x0) else x0
        gens.append({"x0": x0_full.tolist(), "trajectory": _simulate(system.rhs, x0_full, t)[:, list(system.observe)].tolist()})
        if not np.isfinite(gens[-1]["trajectory"]).all():
            raise RuntimeError(f"non-finite generalization trajectory {family} {index}")
    row = {
        "problem_id": f"{family}_s{seed}_{index:04d}",
        "family": family,
        "seed": int(seed),
        "index": int(index),
        "noise_sigma": float(noise_sigma),
        "params": system.params,
        "true_prefix": system.prefix,
        "true_class": TRUE_CLASS.get(family, "MA"),
        "rational": family in RATIONAL_1D or family == "MA_S",
        "dimension_observed": len(system.observe),
        "times": t.tolist(),
        "trajectory": observed.tolist(),
        "generalization": gens,
    }
    row["checksum"] = hashlib.sha256(json.dumps([row["true_prefix"], row["trajectory"]]).encode()).hexdigest()[:16]
    return row


# ---------------------------------------------------------------------------
# Structural classes (parameterization-invariant)
# ---------------------------------------------------------------------------

_X = [sp.Symbol(f"x_{i}") for i in range(6)]


def _clean_poly(expr: sp.Expr, var: sp.Symbol, rel_tol: float = 1e-4) -> sp.Poly | None:
    try:
        poly = sp.Poly(sp.expand(expr), var)
    except sp.PolynomialError:
        return None
    coeffs = [float(abs(c)) for c in poly.coeffs() if c.is_number]
    if len(coeffs) != len(poly.coeffs()):
        return None
    scale = max(coeffs) if coeffs else 0.0
    terms = {m: c for m, c in poly.terms() if scale == 0 or abs(float(c)) > rel_tol * scale}
    if not terms:
        return sp.Poly(0, var)
    return sp.Poly.from_dict(dict(terms), var)


def structural_class(infix: str | None) -> str:
    """Class of a 1D law: P[d] polynomial of degree d; R[n/m] reduced rational with
    numerator degree n and denominator degree m >= 1; OTHER otherwise (sin, sqrt, ...)."""
    if not infix:
        return "INVALID"
    try:
        expr = sp.sympify(infix.replace("^", "**"), locals={f"x_{i}": _X[i] for i in range(6)})
    except Exception:
        return "INVALID"
    free = expr.free_symbols
    if len(free - {_X[0]}) > 0:
        return "OTHER"
    if expr.has(sp.sin, sp.cos, sp.exp, sp.log, sp.sqrt, sp.atan) or any(
        isinstance(p, sp.Pow) and not (p.exp.is_Integer) for p in expr.atoms(sp.Pow)
    ):
        return "OTHER"
    num, den = sp.fraction(sp.cancel(sp.together(expr)))
    pn = _clean_poly(num, _X[0])
    pd = _clean_poly(den, _X[0])
    if pn is None or pd is None:
        return "OTHER"
    if pd.degree() <= 0:
        return f"P[{max(pn.degree(), 0)}]"
    return f"R[{max(pn.degree(), 0)}/{pd.degree()}]"


def monomial_support(infix: str | None) -> frozenset | None:
    """Monomial support of a polynomial component in (x_0, x_1); None if not polynomial."""
    if not infix:
        return None
    try:
        expr = sp.expand(sp.sympify(infix.replace("^", "**"), locals={f"x_{i}": _X[i] for i in range(6)}))
        poly = sp.Poly(expr, _X[0], _X[1])
    except Exception:
        return None
    coeffs = [abs(float(c)) for c in poly.coeffs()]
    scale = max(coeffs) if coeffs else 0.0
    return frozenset(m for m, c in poly.terms() if abs(float(c)) > 1e-3 * scale)


MA_SUPPORT = frozenset({(1, 0), (1, 1), (0, 1)})


def class_match(family: str, infix: str | None) -> bool:
    if family == "MA_SC":
        if not infix or "|" not in infix:
            return False
        parts = [p.strip() for p in infix.split("|")]
        return len(parts) == 2 and all(monomial_support(p) == MA_SUPPORT for p in parts)
    return structural_class(infix) == TRUE_CLASS[family]
