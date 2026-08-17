"""Causal layer interventions for NDformer: zero / mean / matched replacement / patching."""

from __future__ import annotations

from typing import Any, Sequence

import torch

from gpu_run3.hooks import capture_layer_outputs, mean_layer_output, replace_layer_output, zero_layer_output
from gpu_run3.policy import teacher_forcing_metrics


def _prepare(model: Any, data: dict[str, Any]) -> None:
    model.eval()
    model.set_data(
        Xv=data["Xv"],
        Xe=data.get("Xe") or {},
        A=data["A"],
        G=data["G"],
        Y=data["Y"],
        root_type=data.get("root_type", "node"),
        cache_data_emb=False,
    )


def baseline_policy_metrics(model: Any, examples: Sequence[dict[str, Any]], data: dict[str, Any]) -> dict[str, Any]:
    _prepare(model, data)
    return teacher_forcing_metrics(model, examples)


def ablate_layer(
    model: Any,
    layer_name: str,
    examples: Sequence[dict[str, Any]],
    data: dict[str, Any],
    *,
    mode: str = "zero",
    replacement: torch.Tensor | None = None,
) -> dict[str, Any]:
    _prepare(model, data)
    try:
        if mode == "zero":
            context = zero_layer_output(model, layer_name)
        elif mode == "mean":
            if replacement is None:
                raise RuntimeError("ActivationHookError: mean ablation requires a replacement tensor")
            context = mean_layer_output(model, layer_name, replacement)
        elif mode == "replace":
            if replacement is None:
                raise RuntimeError("ActivationPatchError: replacement tensor missing")
            context = replace_layer_output(model, layer_name, replacement)
        else:
            raise ValueError(f"unknown ablation mode {mode}")
        with context:
            # Force encoder recompute so hooks fire.
            model.data_emb = model.encode(model.root_type, model.var_dict)
            metrics = teacher_forcing_metrics(model, examples)
        metrics["failure_reason"] = None
        metrics["valid"] = True
    except Exception as exc:
        metrics = {
            "cross_entropy": float("nan"),
            "top1_accuracy": float("nan"),
            "valid_rate": 0.0,
            "failure_reason": f"{type(exc).__name__}:{exc}",
            "valid": False,
            "rows": [],
        }
    return {"module_name": layer_name, "mode": mode, **{k: v for k, v in metrics.items() if k != "rows"}, "n_rows": len(metrics.get("rows") or [])}


def capture_mean_activation(model: Any, layer_name: str, data: dict[str, Any]) -> torch.Tensor:
    _prepare(model, data)
    with capture_layer_outputs(model, [layer_name]) as captured:
        _ = model.encode(model.root_type, model.var_dict)
    hidden = captured[layer_name]
    return hidden.mean(dim=0, keepdim=True).detach()


def patch_activation(
    model: Any,
    layer_name: str,
    *,
    source_data: dict[str, Any],
    target_data: dict[str, Any],
    examples: Sequence[dict[str, Any]],
) -> dict[str, Any]:
    _prepare(model, source_data)
    with capture_layer_outputs(model, [layer_name]) as captured:
        _ = model.encode(model.root_type, model.var_dict)
    source_hidden = captured[layer_name].detach()
    return ablate_layer(model, layer_name, examples, target_data, mode="replace", replacement=source_hidden)
