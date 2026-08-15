"""Thin adapter around pretrained NeSymReS inference."""

from __future__ import annotations

import contextlib
import io
import json
from functools import partial
from pathlib import Path
from typing import Any, Dict, Optional, Sequence, Tuple

import numpy as np
import omegaconf
import torch

from nesymres.architectures.model import Model
from nesymres.dclasses import BFGSParams, FitParams


def load_nesymres(
    weights: Path,
    config_yaml: Path,
    eq_setting_json: Path,
    beam_size: int = 2,
) -> Tuple[Model, FitParams]:
    with eq_setting_json.open(encoding="utf-8") as f:
        eq_setting = json.load(f)
    cfg = omegaconf.OmegaConf.load(config_yaml)

    bfgs = BFGSParams(
        activated=cfg.inference.bfgs.activated,
        n_restarts=cfg.inference.bfgs.n_restarts,
        add_coefficients_if_not_existing=cfg.inference.bfgs.add_coefficients_if_not_existing,
        normalization_o=cfg.inference.bfgs.normalization_o,
        idx_remove=cfg.inference.bfgs.idx_remove,
        normalization_type=cfg.inference.bfgs.normalization_type,
        stop_time=cfg.inference.bfgs.stop_time,
    )
    params_fit = FitParams(
        word2id=eq_setting["word2id"],
        id2word={int(k): v for k, v in eq_setting["id2word"].items()},
        una_ops=eq_setting["una_ops"],
        bin_ops=eq_setting["bin_ops"],
        total_variables=list(eq_setting["total_variables"]),
        total_coefficients=list(eq_setting["total_coefficients"]),
        rewrite_functions=list(eq_setting["rewrite_functions"]),
        bfgs=bfgs,
        beam_size=beam_size,
    )
    model = Model.load_from_checkpoint(str(weights), cfg=cfg.architecture)
    model.eval()
    if torch.cuda.is_available():
        model.cuda()
    return model, params_fit


def pad_features_to_three(X: np.ndarray) -> np.ndarray:
    """NeSymReS expects up to 3 variables (x_1..x_3)."""
    X = np.asarray(X, dtype=np.float32)
    if X.ndim != 2:
        raise ValueError(f"X must be 2D, got {X.shape}")
    if X.shape[1] >= 3:
        return X[:, :3]
    pad = np.zeros((X.shape[0], 3 - X.shape[1]), dtype=np.float32)
    return np.concatenate([X, pad], axis=1)


def predict_equation(
    model: Model,
    params_fit: FitParams,
    X: np.ndarray,
    y: np.ndarray,
    *,
    quiet: bool = True,
) -> Dict[str, Any]:
    """Run NeSymReS fitfunc; return best expression and raw output."""
    Xp = pad_features_to_three(X)
    y = np.asarray(y, dtype=np.float32).ravel()
    fitfunc = partial(model.fitfunc, cfg_params=params_fit)

    ctx = contextlib.redirect_stdout(io.StringIO()) if quiet else contextlib.nullcontext()
    with ctx:
        with torch.no_grad():
            output = fitfunc(Xp, y)

    preds = output.get("best_bfgs_preds") or output.get("all_bfgs_preds") or []
    losses = output.get("best_bfgs_loss") or output.get("all_bfgs_loss") or []
    if isinstance(preds, str):
        preds = [preds]
    elif not isinstance(preds, (list, tuple)):
        preds = [preds]
    if np.isscalar(losses):
        losses = [losses]
    elif not isinstance(losses, (list, tuple)):
        losses = list(losses)
    best_expr = preds[0] if preds else ""
    best_loss = float(losses[0]) if losses else float("inf")
    return {
        "equation": str(best_expr),
        "bfgs_loss": best_loss,
        "all_preds": [str(p) for p in preds],
        "raw": {k: v for k, v in output.items() if k != "raw"},
    }


def predict_equation_gpu_run2(
    model: Model,
    params_fit: FitParams,
    X: np.ndarray,
    y: np.ndarray,
    *,
    timeout_sec: float = 30.0,
    operator_config: dict | None = None,
    quiet: bool = True,
) -> Dict[str, Any]:
    """Decode with the GPU_RUN2 operator filter and timeout bookkeeping."""
    import time

    from evaluation.decode_timeout import DecodeTimeout, run_with_timeout
    from evaluation.operator_policy import (
        allowed_pow_exponents,
        nesymres_allowed_token_ids,
        validate_candidate_expression,
    )

    operator_cfg = dict(operator_config or {})
    n_variables = int(np.asarray(X).shape[1])
    params_fit.allowed_token_ids = sorted(
        nesymres_allowed_token_ids(params_fit.word2id, config=operator_cfg)
    )
    params_fit.allowed_pow_exponent_ids = sorted(
        int(params_fit.word2id[str(value)])
        for value in allowed_pow_exponents(operator_cfg)
        if str(value) in params_fit.word2id
    )
    params_fit.allowed_variable_ids = sorted(
        int(params_fit.word2id[f"x_{index}"])
        for index in range(1, n_variables + 1)
        if f"x_{index}" in params_fit.word2id
    )

    started = time.perf_counter()
    timeout = False
    failure_reason = None
    try:
        result = run_with_timeout(
            predict_equation,
            model,
            params_fit,
            X,
            y,
            timeout_sec=timeout_sec,
            quiet=quiet,
        )
    except DecodeTimeout:
        timeout = True
        failure_reason = "DecodeTimeout"
        result = {
            "equation": "",
            "bfgs_loss": float("inf"),
            "all_preds": [],
            "raw": {},
        }
    elapsed = time.perf_counter() - started
    equation = str(result.get("equation") or "")
    candidates = [str(p) for p in result.get("all_preds") or []]
    if equation and not failure_reason:
        ok, reason = validate_candidate_expression(
            equation,
            point_sets={"train": (np.asarray(X), [f"x_{i+1}" for i in range(np.asarray(X).shape[1])])},
        )
        if not ok:
            failure_reason = reason
            equation = ""
    return {
        **result,
        "equation": equation,
        "all_preds": candidates,
        "timeout": timeout,
        "timeout_budget_sec": float(timeout_sec),
        "search_seconds": float(elapsed),
        "n_candidate_evals": len(candidates),
        "failure_reason": failure_reason,
        "operator_config_fingerprint": None if operator_config is None else str(sorted(operator_config)),
        "decode_mask_active": True,
    }
