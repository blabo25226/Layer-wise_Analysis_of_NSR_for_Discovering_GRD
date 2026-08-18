"""ODEBench trajectory integration, multiplicative noise, and subsampling."""

from __future__ import annotations

from typing import Any, Sequence

import numpy as np

ODEBENCH_INTEGRATION = {
    "t_span": (0.0, 10.0),
    "n_points": 150,
    "method": "LSODA",
    "rtol": 1e-5,
    "atol": 1e-7,
    "first_step": 1e-6,
}

QUALITATIVE_PANEL_IDS = (9, 16, 27, 40, 52, 54, 62, 63)
STROGATZ_2D_IDS = (24, 25, 26, 27, 28, 29, 30)


def _prepare_eq(eq: str) -> str:
    return str(eq).replace("^", "**")


def callable_system(item: dict[str, Any], *, const_index: int = 0):
    import sympy as sp

    dim = int(item["dim"])
    parts = [_prepare_eq(part.strip()) for part in str(item["eq"]).split("|")]
    consts = list((item.get("consts") or [[]])[const_index])
    local = {f"x_{i}": sp.symbols(f"x_{i}") for i in range(dim)}
    local.update({f"c_{i}": float(value) for i, value in enumerate(consts)})
    local.update({"exp": sp.exp, "log": sp.log, "sin": sp.sin, "cos": sp.cos, "tan": sp.tan, "cot": sp.cot, "abs": sp.Abs})
    exprs = [sp.sympify(part, locals=local) for part in parts]
    symbols = [local[f"x_{i}"] for i in range(dim)]
    fns = [sp.lambdify(symbols, expr, "numpy") for expr in exprs]

    def rhs(_t, state):
        values = [float(v) for v in np.atleast_1d(state)]
        out = []
        for fn in fns:
            value = fn(*values)
            out.append(float(np.asarray(value).reshape(-1)[0]))
        return np.asarray(out, dtype=float)

    return rhs


def integrate_item(
    item: dict[str, Any],
    y0: Sequence[float],
    *,
    n_points: int | None = None,
) -> dict[str, Any]:
    from scipy.integrate import solve_ivp

    n_points = int(n_points or ODEBENCH_INTEGRATION["n_points"])
    t_eval = np.linspace(ODEBENCH_INTEGRATION["t_span"][0], ODEBENCH_INTEGRATION["t_span"][1], n_points)
    rhs = callable_system(item)
    try:
        sol = solve_ivp(
            rhs,
            ODEBENCH_INTEGRATION["t_span"],
            np.asarray(y0, dtype=float),
            t_eval=t_eval,
            method=ODEBENCH_INTEGRATION["method"],
            rtol=ODEBENCH_INTEGRATION["rtol"],
            atol=ODEBENCH_INTEGRATION["atol"],
            first_step=ODEBENCH_INTEGRATION["first_step"],
        )
    except Exception as exc:
        return {
            "success": False,
            "message": str(exc),
            "times": t_eval,
            "trajectory": None,
            "failure_reason": "CandidateIntegrationFailure",
        }
    traj = sol.y.T if sol.y.ndim == 2 else sol.y
    ok = bool(sol.success) and np.isfinite(traj).all()
    return {
        "success": ok,
        "message": sol.message,
        "times": np.asarray(sol.t if ok else t_eval, dtype=float),
        "trajectory": np.asarray(traj, dtype=float) if ok else None,
        "failure_reason": None if ok else "CandidateIntegrationFailure",
    }


def reconstruct_and_generalize(item: dict[str, Any], *, n_points: int | None = None) -> dict[str, Any]:
    inits = list(item.get("init") or [])
    if len(inits) < 2:
        raise ValueError(f"ODEBench id={item.get('id')} needs two initial conditions")
    recon = integrate_item(item, inits[0], n_points=n_points)
    gen = integrate_item(item, inits[1], n_points=n_points)
    return {
        "id": int(item["id"]),
        "dimension": int(item["dim"]),
        "y0_recon": list(inits[0]),
        "y0_gen": list(inits[1]),
        "recon": recon,
        "gen": gen,
    }


def corrupt_trajectory(
    times: np.ndarray,
    trajectory: np.ndarray,
    *,
    sigma: float,
    rho: float,
    seed: int,
) -> tuple[np.ndarray, np.ndarray]:
    """Official multiplicative Gaussian noise plus uniform random subsampling."""
    rng = np.random.RandomState(int(seed))
    noisy = np.asarray(trajectory, dtype=float).copy()
    if float(sigma) > 0:
        noisy = noisy + float(sigma) * noisy * rng.randn(*noisy.shape)
    t_out = np.asarray(times, dtype=float).copy()
    if float(rho) > 0:
        n_remove = int(round(len(t_out) * float(rho)))
        n_remove = min(max(n_remove, 0), max(len(t_out) - 8, 0))
        if n_remove:
            drop = rng.choice(len(t_out), n_remove, replace=False)
            keep = np.sort(np.setdiff1d(np.arange(len(t_out)), drop))
            t_out = t_out[keep]
            noisy = noisy[keep]
    return t_out, noisy


def r2_score(true: np.ndarray, pred: np.ndarray | None) -> float:
    from sklearn.metrics import r2_score as _r2

    if pred is None or true is None:
        return float("nan")
    true_arr = np.asarray(true, dtype=float)
    pred_arr = np.asarray(pred, dtype=float)
    if true_arr.shape != pred_arr.shape or not np.isfinite(pred_arr).all():
        return float("nan")
    try:
        return float(_r2(true_arr, pred_arr, multioutput="variance_weighted"))
    except Exception:
        return float("nan")
