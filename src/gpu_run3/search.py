"""NDformer-guided MCTS wrapper with timeouts, formula saving, and failure reasons."""

from __future__ import annotations

import time
from typing import Any, Sequence

from gpu_run3.formulas import compare_formulas, formula_views, prefix_to_string
from gpu_run3.records import make_formula_record
from gpu_run3_runtime import install_nd2_path


def run_mcts(
    *,
    model: Any | None,
    Xv: dict,
    Xe: dict | None = None,
    A,
    G,
    Y,
    vars_node: Sequence[str],
    vars_edge: Sequence[str] | None = None,
    true_prefix: Sequence[str] | None = None,
    episode_limit: int = 3,
    time_limit_sec: float | None = 30.0,
    mcts_config: dict[str, Any] | None = None,
    random_state: int = 0,
    problem_id: str = "mcts",
    system_name: str = "",
    split: str = "validation",
    condition: str = "ndformer_mcts",
) -> dict[str, Any]:
    install_nd2_path()
    from ND2.GDExpr import GDExpr
    from ND2.search import MCTS
    from ND2.search.reward_solver import RewardSolver

    cfg = dict(mcts_config or {})
    started = time.time()
    failure = None
    try:
        rewarder = RewardSolver(Xv=Xv, Xe=Xe or {}, A=A, G=G, Y=Y)
        if model is not None:
            model.eval()
            model.set_data(Xv=Xv, Xe=Xe or {}, A=A, G=G, Y=Y, root_type=cfg.get("root_type", "node"), cache_data_emb=True)
        est = MCTS(
            rewarder=rewarder,
            ndformer=model,
            vars_node=list(vars_node),
            vars_edge=list(vars_edge or []),
            log_per_episode=int(cfg.get("log_per_episode", 10)),
            beam_size=int(cfg.get("beam_size", 10)),
            use_random_simulate=bool(cfg.get("use_random_simulate", False)),
            max_coeff_num=int(cfg.get("max_coeff_num", 5)),
            max_token_num=int(cfg.get("max_token_num", 30)),
            c_puct=float(cfg.get("c_puct", 5.0)),
            tempreture=float(cfg.get("tempreture", 0.0)),
            lambda_rollout=float(cfg.get("lambda_rollout", 0.5)),
            random_state=int(random_state),
        )
        acc4 = float(cfg.get("early_stop_acc4", 0.99))
        est.fit(
            [cfg.get("root_type", "node")],
            episode_limit=int(episode_limit),
            time_limit=None if time_limit_sec is None else float(time_limit_sec),
            early_stop=(lambda metric: float(metric.get("ACC4", 0.0)) > acc4),
        )
        pred_prefix = list(est.best_model or [])
        metrics = dict(est.best_metric)
        if time_limit_sec is not None and (time.time() - started) >= float(time_limit_sec) and not pred_prefix:
            failure = "MCTSTimeout"
        if pred_prefix:
            try:
                _ = GDExpr.prefix2str(pred_prefix)
            except Exception:
                failure = failure or "ParseError"
        else:
            failure = failure or "MCTSTimeout"
        search_nodes = len(est.MC_Tree)
        candidate_count = len(est.rewards)
    except TimeoutError:
        pred_prefix = []
        metrics = {}
        failure = "MCTSTimeout"
        search_nodes = 0
        candidate_count = 0
        est = None
    except Exception as exc:
        pred_prefix = []
        metrics = {}
        failure = f"{type(exc).__name__}:{exc}"
        search_nodes = 0
        candidate_count = 0
        est = None

    wall = time.time() - started
    true_prefix = list(true_prefix or [])
    pred_views = formula_views(pred_prefix) if pred_prefix else {
        "raw_expr": "",
        "canonical_expr": "",
        "skeleton_expr": "",
        "canonical_prefix": [],
        "valid": False,
        "complexity": 0,
        "failure_reason": failure or "ParseError",
    }
    comparison = compare_formulas(true_prefix, pred_prefix) if true_prefix and pred_prefix else {
        "exact": 0.0,
        "skeleton": 0.0,
        "symbolic_equivalent": 0.0,
        "ted_raw": None,
        "ted_skeleton": None,
        "ted_variable_aware": None,
        "true_raw_expr": prefix_to_string(true_prefix) if true_prefix else "",
        "true_canonical_expr": ",".join(true_prefix),
        "true_skeleton_expr": ",".join(true_prefix),
        "pred_raw_expr": pred_views.get("raw_expr", ""),
        "pred_canonical_expr": pred_views.get("canonical_expr", ""),
        "pred_skeleton_expr": pred_views.get("skeleton_expr", ""),
        "valid": bool(pred_views.get("valid")),
        "failure_reason": pred_views.get("failure_reason") or failure,
        "complexity": pred_views.get("complexity", 0),
    }
    fit_error = metrics.get("RMSE")
    if fit_error is not None:
        try:
            fit_error = float(fit_error)
            if not np_isfinite(fit_error):
                failure = "NaN" if str(fit_error) == "nan" else "Inf"
        except (TypeError, ValueError):
            failure = failure or "ConstantOptimizationFailure"

    record = make_formula_record(
        problem_id=problem_id,
        system_name=system_name,
        formula_id=system_name or problem_id,
        split=split,
        condition=condition,
        true_formula_raw=comparison.get("true_raw_expr", ""),
        true_formula_canonical=comparison.get("true_canonical_expr", ""),
        true_formula_skeleton=comparison.get("true_skeleton_expr", ""),
        pred_formula_raw=comparison.get("pred_raw_expr", ""),
        pred_formula_canonical=comparison.get("pred_canonical_expr", ""),
        pred_formula_skeleton=comparison.get("pred_skeleton_expr", ""),
        fit_error=None if fit_error is None else float(fit_error),
        exact=comparison.get("exact"),
        skeleton=comparison.get("skeleton"),
        symbolic_equivalent=comparison.get("symbolic_equivalent"),
        ted_raw=comparison.get("ted_raw"),
        ted_skeleton=comparison.get("ted_skeleton"),
        ted_variable_aware=comparison.get("ted_variable_aware"),
        complexity=comparison.get("complexity"),
        valid=bool(pred_prefix) and bool(comparison.get("valid", False)) and failure is None,
        failure_reason=failure or comparison.get("failure_reason"),
        search_nodes=int(search_nodes),
        candidate_count=int(candidate_count),
        wall_time=float(wall),
        prefix=pred_prefix,
        official_metrics={k: _json_number(v) for k, v in metrics.items()},
        used_ndformer=model is not None,
        n_rewards=int(candidate_count),
    )
    return record


def np_isfinite(value: float) -> bool:
    import math

    return math.isfinite(float(value))


def _json_number(value: Any) -> Any:
    try:
        import numpy as np

        if isinstance(value, (np.floating, np.integer)):
            return value.item()
    except Exception:
        pass
    if isinstance(value, (float, int, str, bool)) or value is None:
        return value
    return str(value)
