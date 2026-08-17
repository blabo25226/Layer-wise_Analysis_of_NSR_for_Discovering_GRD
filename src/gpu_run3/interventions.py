"""Causal layer interventions for NDformer: zero / mean / matched replacement / patching.

Encoder blocks fire during ``model.encode``; decoder blocks fire only during the
decoder forward pass driven by ``get_policy``. Every helper here dispatches on
which side a layer belongs to, so a decoder-block name never silently produces an
empty capture.
"""

from __future__ import annotations

from typing import Any, Sequence

import torch

from gpu_run3.hooks import (
    capture_layer_outputs,
    identity_layer_output,
    mean_layer_output,
    replace_layer_output,
    zero_layer_output,
)
from gpu_run3.policy import teacher_forcing_metrics

ABLATION_MODES = ("skip", "zero", "mean", "replace")


def is_decoder_layer(layer_name: str) -> bool:
    return layer_name.startswith("decoder.")


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


def _drive_forward(model: Any, layer_name: str, examples: Sequence[dict[str, Any]]) -> None:
    """Run whichever forward pass makes ``layer_name`` fire."""
    if is_decoder_layer(layer_name):
        prefixes = [list(ex["prefix"]) for ex in examples if ex.get("target")]
        if not prefixes:
            raise RuntimeError("ActivationHookError: no usable prefix to drive the decoder")
        model.data_emb = model.encode(model.root_type, model.var_dict)
        _ = model.get_policy(prefixes)
    else:
        model.data_emb = model.encode(model.root_type, model.var_dict)


def baseline_policy_metrics(model: Any, examples: Sequence[dict[str, Any]], data: dict[str, Any]) -> dict[str, Any]:
    _prepare(model, data)
    return teacher_forcing_metrics(model, examples)


def ablate_layer(
    model: Any,
    layer_name: str,
    examples: Sequence[dict[str, Any]],
    data: dict[str, Any],
    *,
    mode: str = "skip",
    replacement: torch.Tensor | None = None,
) -> dict[str, Any]:
    """Evaluate teacher-forcing policy with one Transformer block intervened on.

    ``skip`` replaces the block with the identity (residual-preserving bypass) and
    is the primary ablation; ``zero`` deletes the representation entirely.
    """
    _prepare(model, data)
    try:
        if mode == "skip":
            context = identity_layer_output(model, layer_name)
        elif mode == "zero":
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
            # Force encoder recompute so encoder-side hooks fire; decoder-side hooks
            # fire inside teacher_forcing_metrics' get_policy call, also under the hook.
            model.data_emb = model.encode(model.root_type, model.var_dict)
            metrics = teacher_forcing_metrics(model, examples)
        metrics["failure_reason"] = None
        metrics["valid"] = True
    except Exception as exc:
        metrics = {
            "cross_entropy": float("nan"),
            "top1_accuracy": float("nan"),
            "topk_accuracy": float("nan"),
            "mean_true_symbol_rank": float("nan"),
            "mean_true_symbol_probability": float("nan"),
            "mean_policy_entropy": float("nan"),
            "valid_rate": 0.0,
            "failure_reason": f"{type(exc).__name__}:{exc}",
            "valid": False,
            "rows": [],
        }
    return {
        "module_name": layer_name,
        "mode": mode,
        **{k: v for k, v in metrics.items() if k != "rows"},
        "n_rows": len(metrics.get("rows") or []),
    }


def capture_mean_activation(
    model: Any,
    layer_name: str,
    data: dict[str, Any],
    examples: Sequence[dict[str, Any]] | None = None,
) -> torch.Tensor:
    """Mean activation of ``layer_name`` over the batch dimension.

    Raises ``ActivationHookError`` rather than KeyError when the layer never fires.
    """
    _prepare(model, data)
    with capture_layer_outputs(model, [layer_name]) as captured:
        _drive_forward(model, layer_name, examples or [])
    hidden = captured.get(layer_name)
    if hidden is None:
        raise RuntimeError(f"ActivationHookError: {layer_name} did not fire during the forward pass")
    return hidden.mean(dim=0, keepdim=True).detach()


def patch_activation(
    model: Any,
    layer_name: str,
    *,
    source_data: dict[str, Any],
    target_data: dict[str, Any],
    examples: Sequence[dict[str, Any]],
    source_examples: Sequence[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Activation patching: run ``source_data`` through the model, then splice its
    ``layer_name`` output into a ``target_data`` forward pass."""
    try:
        source_hidden = capture_mean_activation(
            model,
            layer_name,
            source_data,
            examples=list(source_examples or examples),
        )
    except Exception as exc:
        return {
            "module_name": layer_name,
            "mode": "patch",
            "valid": False,
            "failure_reason": f"ActivationPatchError:{type(exc).__name__}:{exc}",
            "cross_entropy": float("nan"),
            "top1_accuracy": float("nan"),
            "n_rows": 0,
        }
    result = ablate_layer(model, layer_name, examples, target_data, mode="replace", replacement=source_hidden)
    result["mode"] = "patch"
    return result
