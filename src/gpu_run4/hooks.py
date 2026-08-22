"""Hidden-state capture and residual-preserving interventions for ODEFormer blocks."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterator

import torch
from torch import nn

from gpu_run4.architecture import ranking_block_modules, resolve_layer_module, unwrap_model


def _as_tensor(output: Any) -> torch.Tensor:
    if isinstance(output, tuple):
        return output[0]
    if not isinstance(output, torch.Tensor):
        raise TypeError(f"ActivationHookError: expected tensor, got {type(output)!r}")
    return output


@contextmanager
def capture_layer_outputs(model: Any, layer_names: list[str]) -> Iterator[dict[str, torch.Tensor]]:
    captured: dict[str, torch.Tensor] = {}
    handles = []

    def _make_hook(name: str):
        def hook(_module: nn.Module, _inputs: Any, output: Any) -> Any:
            captured[name] = _as_tensor(output).detach()
            return output

        return hook

    try:
        for name in layer_names:
            module = resolve_layer_module(model, name)
            handles.append(module.register_forward_hook(_make_hook(name)))
        yield captured
    except Exception as exc:
        raise RuntimeError(f"ActivationHookError: {exc}") from exc
    finally:
        for handle in handles:
            handle.remove()


@contextmanager
def identity_control_hook(model: Any, layer_name: str) -> Iterator[None]:
    """Hook that returns the original output. Baseline must match an unhooked forward."""
    module = resolve_layer_module(model, layer_name)

    def hook(_module: nn.Module, _inputs: Any, output: Any) -> Any:
        return output

    handle = module.register_forward_hook(hook)
    try:
        yield
    finally:
        handle.remove()


@contextmanager
def zero_residual_block(model: Any, layer_name: str) -> Iterator[None]:
    """Zero attention and FFN (and decoder cross-attn) so the block adds no residual."""
    parts = ranking_block_modules(model, layer_name)
    handles = []

    def _zero(_module: nn.Module, _inputs: Any, output: Any) -> Any:
        tensor = _as_tensor(output)
        zeros = torch.zeros_like(tensor)
        if isinstance(output, tuple):
            return (zeros, *output[1:])
        return zeros

    try:
        for key in ("attn", "ffn", "cross"):
            module = parts.get(key)
            if module is None:
                continue
            handles.append(module.register_forward_hook(_zero))
        yield
    finally:
        for handle in handles:
            handle.remove()


@contextmanager
def mean_replace_block(model: Any, layer_name: str, replacement: torch.Tensor | None = None) -> Iterator[None]:
    module = resolve_layer_module(model, layer_name)

    def hook(_module: nn.Module, _inputs: Any, output: Any) -> Any:
        tensor = _as_tensor(output)
        if replacement is None:
            value = tensor.mean(dim=1, keepdim=True).expand_as(tensor)
        else:
            value = replacement.to(device=tensor.device, dtype=tensor.dtype)
            if value.shape != tensor.shape:
                value = value.mean(dim=1, keepdim=True).expand_as(tensor)
        if isinstance(output, tuple):
            return (value, *output[1:])
        return value

    handle = module.register_forward_hook(hook)
    try:
        yield
    finally:
        handle.remove()


def enable_store_outputs(model: Any, enabled: bool = True) -> None:
    from odeformer.model.transformer import TransformerModel

    TransformerModel.STORE_OUTPUTS = bool(enabled)
    wrapped = unwrap_model(model)
    wrapped.encoder.outputs = []
    wrapped.decoder.outputs = []
