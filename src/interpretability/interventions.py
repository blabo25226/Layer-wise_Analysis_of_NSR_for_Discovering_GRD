"""Fixed ablation and activation-intervention protocols for GPU_RUN2 Phase 4."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterator

import numpy as np
import torch
from torch import nn


def ablation_zero_output(activation: np.ndarray) -> np.ndarray:
    """Replace a layer activation with zeros (hard ablation)."""
    return np.zeros_like(np.asarray(activation))


def interpolate_activations(
    source: np.ndarray,
    destination: np.ndarray,
    *,
    alpha: float,
) -> np.ndarray:
    """Linear activation intervention: ``(1-alpha)*source + alpha*destination``."""
    if not 0.0 <= float(alpha) <= 1.0:
        raise ValueError(f"alpha must be in [0, 1], got {alpha}")
    src = np.asarray(source, dtype=np.float64)
    dst = np.asarray(destination, dtype=np.float64)
    if src.shape != dst.shape:
        raise ValueError(f"activation shapes differ: {src.shape} vs {dst.shape}")
    return ((1.0 - alpha) * src + alpha * dst).astype(src.dtype, copy=False)


def mean_activation_baseline(activation: np.ndarray, *, axis: int = 0) -> np.ndarray:
    """Broadcast the mean activation as a non-informative replacement."""
    array = np.asarray(activation, dtype=np.float64)
    mean = array.mean(axis=axis, keepdims=True)
    return np.broadcast_to(mean, array.shape).copy()


def intervention_delta(
    baseline_score: float,
    intervened_score: float,
    *,
    higher_is_better: bool,
) -> float:
    """Signed effect of an intervention relative to the unintervened score."""
    if higher_is_better:
        return float(intervened_score - baseline_score)
    return float(baseline_score - intervened_score)


def _as_tensor_output(output: Any) -> torch.Tensor:
    if isinstance(output, tuple):
        return output[0]
    if not isinstance(output, torch.Tensor):
        raise TypeError(f"expected tensor output, got {type(output)!r}")
    return output


def register_zero_output_hook(module: nn.Module) -> Any:
    """Hard ablation: replace the module output with zeros."""

    def hook(_mod: nn.Module, _inputs: Any, output: Any) -> Any:
        tensor = _as_tensor_output(output)
        zeros = torch.zeros_like(tensor)
        if isinstance(output, tuple):
            return (zeros, *output[1:])
        return zeros

    return module.register_forward_hook(hook)


def _broadcast_replacement(replacement: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
    """Broadcast ``replacement`` onto ``target``, collapsing mismatched sequence dims.

    Decode uses a different number of points / tokens than the capture batch, so a
    mean activation of shape ``(1, S_ref, H)`` must still apply to ``(1, S_decode, H)``.
    Any non-feature axis that cannot expand is reduced by mean to size 1, then expanded.
    """
    ref = replacement.to(device=target.device, dtype=target.dtype)
    while ref.ndim < target.ndim:
        ref = ref.unsqueeze(0)
    while ref.ndim > target.ndim:
        ref = ref.mean(dim=0)
    for dim in range(ref.ndim):
        if ref.shape[dim] == target.shape[dim] or ref.shape[dim] == 1:
            continue
        if dim == ref.ndim - 1:
            raise RuntimeError(
                f"intervention replacement feature dim {ref.shape[dim]} "
                f"cannot match target {target.shape[dim]}"
            )
        ref = ref.mean(dim=dim, keepdim=True)
    try:
        return ref.expand(target.shape)
    except RuntimeError as exc:
        raise RuntimeError(
            f"intervention replacement shape {tuple(replacement.shape)} "
            f"cannot broadcast to {tuple(target.shape)}"
        ) from exc


def register_replace_output_hook(module: nn.Module, replacement: torch.Tensor) -> Any:
    """Replace the module output with a broadcast copy of ``replacement``."""

    def hook(_mod: nn.Module, _inputs: Any, output: Any) -> Any:
        tensor = _as_tensor_output(output)
        ref = _broadcast_replacement(replacement, tensor)
        if isinstance(output, tuple):
            return (ref, *output[1:])
        return ref

    return module.register_forward_hook(hook)


def capture_module_activation(
    model: nn.Module,
    module: nn.Module,
    batch: tuple[torch.Tensor, torch.Tensor],
    *,
    device: torch.device | None = None,
) -> torch.Tensor:
    """Run one teacher-forcing forward and return the named module's output."""
    device = device or getattr(model, "device", batch[0].device)
    captured: dict[str, torch.Tensor] = {}

    def hook(_mod: nn.Module, _inputs: Any, output: Any) -> None:
        captured["act"] = _as_tensor_output(output).detach()

    handle = module.register_forward_hook(hook)
    model.eval()
    try:
        with torch.no_grad():
            model.forward([batch[0].to(device), batch[1].to(device)])
    finally:
        handle.remove()
    if "act" not in captured:
        raise RuntimeError("module produced no activation during capture")
    return captured["act"]


@contextmanager
def zero_output_context(module: nn.Module) -> Iterator[None]:
    handle = register_zero_output_hook(module)
    try:
        yield
    finally:
        handle.remove()


@contextmanager
def replace_output_context(module: nn.Module, replacement: torch.Tensor) -> Iterator[None]:
    handle = register_replace_output_hook(module, replacement)
    try:
        yield
    finally:
        handle.remove()
