"""Fine-tuning conditions, layer transplant (swap), and weight-change measurement."""

from __future__ import annotations

import copy
import time
from typing import Any, Sequence

import numpy as np
import torch

from gpu_run4.architecture import ranking_block_modules, set_trainable_layers, unwrap_model
from gpu_run4.training import teacher_forcing_loss


def finetune(wrapped: Any, records: Sequence[dict[str, Any]], *, trainable: set[str] | None, steps: int,
             lr: float, batch: int, seed: int) -> dict[str, Any]:
    """Adam on teacher-forcing CE. ``trainable=None`` is full fine-tuning. Order is seeded."""
    torch.manual_seed(seed)
    counts = set_trainable_layers(wrapped, trainable)
    params = [p for p in wrapped.parameters() if p.requires_grad]
    opt = torch.optim.Adam(params, lr=lr)
    rng = np.random.default_rng(seed)
    losses = []
    started = time.time()
    wrapped.train()
    for _ in range(steps):
        opt.zero_grad(set_to_none=True)
        total = 0.0
        for idx in rng.integers(0, len(records), size=batch):
            row = records[int(idx)]
            loss = teacher_forcing_loss(wrapped, row["times_np"], row["trajectory_np"], row["tokens"]) / batch
            loss.backward()
            total += float(loss.detach())
        opt.step()
        losses.append(total)
    wrapped.eval()
    for p in wrapped.parameters():
        p.requires_grad = False
    return {"trainable": counts, "trainable_parameters": int(sum(p.numel() for p in params)),
            "losses": losses, "wall_time": time.time() - started}


def block_state(wrapped: Any, layer: str) -> dict[str, torch.Tensor]:
    out = {}
    for key, module in ranking_block_modules(wrapped, layer).items():
        if module is None:
            continue
        for name, tensor in module.state_dict().items():
            out[f"{key}.{name}"] = tensor.detach().clone()
    return out


def load_block_state(wrapped: Any, layer: str, state: dict[str, torch.Tensor]) -> None:
    modules = ranking_block_modules(wrapped, layer)
    grouped: dict[str, dict[str, torch.Tensor]] = {}
    for full, tensor in state.items():
        key, name = full.split(".", 1)
        grouped.setdefault(key, {})[name] = tensor
    for key, sub in grouped.items():
        modules[key].load_state_dict(sub)


def relative_weight_change(base: Any, tuned: Any, layer: str) -> float:
    a, b = block_state(base, layer), block_state(tuned, layer)
    num = sum(float((b[k].float() - a[k].float()).norm() ** 2) for k in a)
    den = sum(float(a[k].float().norm() ** 2) for k in a)
    return float(np.sqrt(num / max(den, 1e-12)))


def clone(wrapped: Any) -> Any:
    return copy.deepcopy(wrapped)
