"""Hidden-state hooks for NDformer Transformer encoder / decoder blocks."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterator

import torch
from torch import nn

from gpu_run3.architecture import resolve_layer_module


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
def replace_layer_output(model: Any, layer_name: str, replacement: torch.Tensor) -> Iterator[None]:
    module = resolve_layer_module(model, layer_name)

    def hook(_module: nn.Module, _inputs: Any, output: Any) -> Any:
        tensor = _as_tensor(output)
        value = replacement
        if value.shape != tensor.shape:
            if value.ndim == tensor.ndim and value.shape[-1] == tensor.shape[-1]:
                value = value.mean(dim=1, keepdim=True).expand_as(tensor)
            else:
                raise RuntimeError(
                    f"ActivationPatchError: shape {tuple(value.shape)} vs {tuple(tensor.shape)} for {layer_name}"
                )
        value = value.to(device=tensor.device, dtype=tensor.dtype)
        if isinstance(output, tuple):
            return (value, *output[1:])
        return value

    handle = module.register_forward_hook(hook)
    try:
        yield
    finally:
        handle.remove()


@contextmanager
def zero_layer_output(model: Any, layer_name: str) -> Iterator[None]:
    module = resolve_layer_module(model, layer_name)

    def hook(_module: nn.Module, _inputs: Any, output: Any) -> Any:
        tensor = _as_tensor(output)
        zeros = torch.zeros_like(tensor)
        if isinstance(output, tuple):
            return (zeros, *output[1:])
        return zeros

    handle = module.register_forward_hook(hook)
    try:
        yield
    finally:
        handle.remove()


@contextmanager
def mean_layer_output(model: Any, layer_name: str, mean: torch.Tensor) -> Iterator[None]:
    with replace_layer_output(model, layer_name, mean):
        yield
