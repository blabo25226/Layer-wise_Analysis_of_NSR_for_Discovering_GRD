"""Fit ODEFormer, score candidates, and optionally BFGS-optimize constants."""

from __future__ import annotations

import math
import regex
import time
from typing import Any, Sequence

import numpy as np

from gpu_run4.formulas import compare_formulas, instantiate_odebench_item
from gpu_run4.records import make_formula_record
from gpu_run4.ted import time_limit, TedTimeout
from gpu_run4.trajectories import r2_score
from gpu_run4_runtime import candidate_infix, capture_numpy_permutation


_CONST_RE = regex.compile(
    r"(?:(?<!_\d*))(?:(?<!\*\*))(?:[-+]?)?(?:(?<=\()[-+]?)?(?:(?<=^)[-+]?)?(?:(?:\d*\.\d+)|(?:\d+\.?))(?:[Ee][+-]?\d+)?"
)


def _safe_r2(true: np.ndarray, pred: np.ndarray | None) -> float:
    return r2_score(true, pred)


def integrate_candidate(regressor: Any, times: np.ndarray, y0: Sequence[float], tree: Any, *, timeout_sec: float) -> tuple[np.ndarray | None, str | None]:
    try:
        with time_limit(timeout_sec):
            pred = regressor.integrate_prediction(times, y0, prediction=tree)
    except TedTimeout:
        return None, "CandidateIntegrationFailure"
    except Exception as exc:
        return None, f"CandidateIntegrationFailure:{type(exc).__name__}"
    if pred is None:
        return None, "CandidateIntegrationFailure"
    arr = np.asarray(pred, dtype=float)
    if not np.isfinite(arr).all():
        return None, "Inf" if np.isinf(arr).any() else "NaN"
    return arr, None


def optimize_constants(
    eq: str,
    times: np.ndarray,
    y0: Sequence[float],
    observed: np.ndarray,
    *,
    timeout_sec: float,
    regressor: Any,
) -> tuple[str, str | None]:
    """BFGS on numeric literals. Failures are recorded, not coerced to success."""
    from scipy.optimize import minimize

    constants = [float(match.group(0)) for match in _CONST_RE.finditer(eq)]
    if not constants:
        return eq, None

    def insert(values: Sequence[float]) -> str:
        leftover = list(values)
        return _CONST_RE.sub(lambda _: f"{leftover.pop(0):.6g}", eq)

    def objective(values: np.ndarray) -> float:
        try:
            pred = regressor.integrate_prediction(times, y0, prediction=insert(values))
        except Exception:
            return 1e6
        if pred is None or not np.isfinite(np.asarray(pred)).all():
            return 1e6
        return float(np.mean((np.asarray(pred) - observed) ** 2))

    try:
        with time_limit(timeout_sec):
            result = minimize(objective, np.asarray(constants, dtype=float), method="BFGS", options={"maxiter": 40})
        if not result.success:
            return eq, "ConstantOptimizationFailure"
        return insert(result.x), None
    except TedTimeout:
        return eq, "ConstantOptimizationFailure"
    except Exception:
        return eq, "ConstantOptimizationFailure"


def _variable_f1(true_text: str, pred_text: str) -> dict[str, float]:
    true_vars = set(regex.findall(r"x_\d+", true_text))
    pred_vars = set(regex.findall(r"x_\d+", pred_text or ""))
    if not true_vars and not pred_vars:
        return {"variable_precision": 1.0, "variable_recall": 1.0, "variable_f1": 1.0}
    if not pred_vars:
        return {"variable_precision": 0.0, "variable_recall": 0.0, "variable_f1": 0.0}
    precision = len(true_vars & pred_vars) / len(pred_vars)
    recall = len(true_vars & pred_vars) / len(true_vars) if true_vars else 0.0
    f1 = 0.0 if precision + recall == 0 else 2 * precision * recall / (precision + recall)
    return {"variable_precision": precision, "variable_recall": recall, "variable_f1": f1}


def score_candidate(
    *,
    item: dict[str, Any],
    true_views: dict[str, Any],
    tree: Any,
    formula_raw: str | None,
    times_obs: np.ndarray,
    traj_obs: np.ndarray,
    times_recon: np.ndarray,
    traj_recon: np.ndarray,
    y0_recon: Sequence[float],
    times_gen: np.ndarray,
    traj_gen: np.ndarray,
    y0_gen: Sequence[float],
    regressor: Any,
    integration_timeout: float,
    gen_timeout: float,
    candidate_index: int,
    selected: bool,
    condition: str,
    split: str,
    beam_size: int,
    beam_temperature: float,
    wall_time: float,
    extra: dict[str, Any] | None = None,
    skip_cas: bool = False,
    integrate: bool = True,
) -> dict[str, Any]:
    parsed = formula_raw or ""
    comparison = compare_formulas(true_views["true_formula_instantiated"], parsed, skip_cas=skip_cas) if parsed else {
        "canonical_exact": 0.0,
        "skeleton_exact": 0.0,
        "symbolic_equivalent": 0.0,
        "ted_raw": float("nan"),
        "ted_skeleton": float("nan"),
        "normalized_ted": float("nan"),
        "complexity": 0,
        "valid": False,
        "failure_reason": "ParseError",
        "pred_formula_canonical": "",
        "pred_formula_skeleton": "",
        "pred_formula_prefix": "",
    }
    recon_pred, recon_fail = (None, None)
    gen_pred, gen_fail = (None, None)
    recon_r2 = float("nan")
    gen_r2 = float("nan")
    obs_r2 = float("nan")
    if integrate:
        recon_pred, recon_fail = integrate_candidate(regressor, times_recon, y0_recon, tree, timeout_sec=integration_timeout)
        gen_pred, gen_fail = integrate_candidate(regressor, times_gen, y0_gen, tree, timeout_sec=gen_timeout)
        recon_r2 = _safe_r2(traj_recon, recon_pred)
        gen_r2 = _safe_r2(traj_gen, gen_pred)
        try:
            obs_pred, _ = integrate_candidate(regressor, times_obs, traj_obs[int(np.argmin(times_obs))], tree, timeout_sec=integration_timeout)
            obs_r2 = _safe_r2(traj_obs, obs_pred)
        except Exception:
            pass
    failure = comparison.get("failure_reason") or recon_fail or gen_fail
    valid = bool(comparison.get("valid")) and recon_fail is None
    var = _variable_f1(true_views["true_formula_instantiated"], parsed)
    record = make_formula_record(
        problem_id=f"odebench_{item['id']}",
        benchmark="odebench",
        system_name=str(item.get("eq_description") or item["id"]),
        dimension=int(item["dim"]),
        split=split,
        condition=condition,
        true_formula_raw=true_views["true_formula_raw"],
        true_formula_prefix=true_views["true_formula_prefix"],
        true_formula_canonical=true_views["true_formula_canonical"],
        true_formula_skeleton=true_views["true_formula_skeleton"],
        candidate_index=candidate_index,
        candidate_formula_raw=parsed,
        candidate_formula_canonical=str(comparison.get("pred_formula_canonical") or ""),
        candidate_formula_skeleton=str(comparison.get("pred_formula_skeleton") or ""),
        selected=selected,
        reconstruction_r2=recon_r2,
        generalization_r2=gen_r2,
        canonical_exact=comparison.get("canonical_exact"),
        skeleton_exact=comparison.get("skeleton_exact"),
        symbolic_equivalent=comparison.get("symbolic_equivalent"),
        ted_raw=comparison.get("ted_raw"),
        ted_skeleton=comparison.get("ted_skeleton"),
        complexity=comparison.get("complexity"),
        valid=valid,
        failure_reason=failure,
        wall_time=wall_time,
        beam_size=beam_size,
        beam_temperature=beam_temperature,
        observed_r2=obs_r2,
        normalized_ted=comparison.get("normalized_ted"),
        **var,
        **(extra or {}),
    )
    return record


def fit_and_collect(
    regressor: Any,
    times: np.ndarray,
    trajectory: np.ndarray,
    *,
    permutation_seed: int,
    sort_metric: str = "r2",
) -> dict[str, Any]:
    started = time.perf_counter()
    with capture_numpy_permutation(permutation_seed) as permutations:
        candidates = regressor.fit(times, trajectory, sort_candidates=True, sort_metric=sort_metric)
    wall = time.perf_counter() - started
    trees = list((candidates or {}).get(0) or [])
    infixes = [candidate_infix(tree) for tree in trees]
    return {
        "trees": trees,
        "infixes": infixes,
        "wall_time": wall,
        "n_candidates": len(trees),
        "permutations": permutations,
    }


def evaluate_system(
    item: dict[str, Any],
    *,
    regressor: Any,
    recon: dict[str, Any],
    gen: dict[str, Any],
    times_obs: np.ndarray,
    traj_obs: np.ndarray,
    sigma: float,
    rho: float,
    seed: int,
    permutation_seed: int,
    condition: str,
    split: str,
    beam_size: int,
    beam_temperature: float,
    integration_timeout: float,
    gen_timeout: float,
    bfgs_timeout: float,
    save_all_candidates: bool,
    run_opt: bool,
) -> dict[str, Any]:
    true_views = instantiate_odebench_item(item)
    fit = fit_and_collect(regressor, times_obs, traj_obs, permutation_seed=permutation_seed, sort_metric="r2")
    trees = fit["trees"]
    selected_tree = trees[0] if trees else None
    records = []
    to_score = list(enumerate(trees)) if save_all_candidates else ([(0, selected_tree)] if selected_tree is not None else [])
    for index, tree in to_score:
        if tree is None:
            continue
        raw = candidate_infix(tree)
        records.append(
            score_candidate(
                item=item,
                true_views=true_views,
                tree=tree,
                formula_raw=raw,
                times_obs=times_obs,
                traj_obs=traj_obs,
                times_recon=recon["times"],
                traj_recon=recon["trajectory"],
                y0_recon=recon["y0"] if "y0" in recon else traj_obs[0],
                times_gen=gen["times"],
                traj_gen=gen["trajectory"],
                y0_gen=gen["y0"],
                regressor=regressor,
                integration_timeout=integration_timeout,
                gen_timeout=gen_timeout,
                candidate_index=index,
                selected=index == 0,
                condition=condition,
                split=split,
                beam_size=beam_size,
                beam_temperature=beam_temperature,
                wall_time=fit["wall_time"],
                extra={"noise_sigma": sigma, "subsample_rho": rho, "seed": seed},
                skip_cas=index != 0,
                integrate=index == 0,
            )
        )
    opt_record = None
    if run_opt and selected_tree is not None:
        raw = candidate_infix(selected_tree) or ""
        opt_eq, opt_fail = optimize_constants(
            raw,
            times_obs,
            traj_obs[int(np.argmin(times_obs))],
            traj_obs,
            timeout_sec=bfgs_timeout,
            regressor=regressor,
        )
        opt_record = score_candidate(
            item=item,
            true_views=true_views,
            tree=opt_eq,
            formula_raw=opt_eq,
            times_obs=times_obs,
            traj_obs=traj_obs,
            times_recon=recon["times"],
            traj_recon=recon["trajectory"],
            y0_recon=recon.get("y0", traj_obs[0]),
            times_gen=gen["times"],
            traj_gen=gen["trajectory"],
            y0_gen=gen["y0"],
            regressor=regressor,
            integration_timeout=integration_timeout,
            gen_timeout=gen_timeout,
            candidate_index=0,
            selected=True,
            condition="odeformer_opt",
            split=split,
            beam_size=beam_size,
            beam_temperature=beam_temperature,
            wall_time=fit["wall_time"],
            extra={
                "noise_sigma": sigma,
                "subsample_rho": rho,
                "seed": seed,
                "opt_failure_reason": opt_fail,
                "pre_opt_formula": raw,
            },
        )
        if opt_fail:
            opt_record["failure_reason"] = opt_record.get("failure_reason") or opt_fail
            opt_record["valid"] = False
    return {
        "id": int(item["id"]),
        "n_candidates": fit["n_candidates"],
        "wall_time": fit["wall_time"],
        "records": records,
        "opt_record": opt_record,
        "selected_formula": candidate_infix(selected_tree) if selected_tree is not None else None,
        "true_formula": true_views["true_formula_instantiated"],
    }
