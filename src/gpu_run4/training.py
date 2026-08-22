"""Teacher-forcing CE and single-layer / selective fine-tuning for ODEFormer."""

from __future__ import annotations

import copy
import time
from typing import Any, Sequence

import numpy as np
import torch

from gpu_run4.architecture import set_trainable_layers, unwrap_model
from gpu_run4_runtime import install_odeformer_path


def _point_bag(times: np.ndarray, trajectory: np.ndarray) -> list:
    bag = []
    for t, y in zip(np.asarray(times), np.asarray(trajectory)):
        bag.append([float(t), np.asarray(y, dtype=float)])
    return bag


def teacher_forcing_loss(model: Any, times: np.ndarray, trajectory: np.ndarray, tree_encoded: Sequence[str]) -> torch.Tensor:
    install_odeformer_path()
    wrapped = unwrap_model(model)
    env = wrapped.env
    embedder = wrapped.embedder
    encoder = wrapped.encoder
    decoder = wrapped.decoder
    x1, len1 = embedder([_point_bag(times, trajectory)])
    x2, len2 = env.batch_equations(env.word_to_idx([list(tree_encoded)], float_input=False))
    device = next(wrapped.parameters()).device
    x2 = x2.to(device)
    len2 = len2.to(device)
    alen = torch.arange(int(len2.max()), dtype=torch.long, device=device)
    pred_mask = alen[:, None] < len2[None] - 1
    y = x2[1:].masked_select(pred_mask[:-1])
    encoded = encoder("fwd", x=x1, lengths=len1, causal=False)
    decoded = decoder(
        "fwd",
        x=x2,
        lengths=len2,
        causal=True,
        src_enc=encoded.transpose(0, 1),
        src_len=len1,
    )
    _scores, loss = decoder("predict", tensor=decoded, pred_mask=pred_mask, y=y, get_scores=False)
    return loss


def clone_model(model: Any) -> Any:
    clone = copy.deepcopy(model)
    device = next(unwrap_model(model).parameters()).device
    clone.to(device)
    return clone


def train_iole(
    model: Any,
    records: Sequence[dict[str, Any]],
    *,
    trainable_layers: set[str] | None,
    steps: int,
    lr: float,
) -> dict[str, Any]:
    wrapped = unwrap_model(model)
    counts = set_trainable_layers(wrapped, trainable_layers)
    usable = [row for row in records if row.get("tree_encoded") and row.get("times") is not None]
    if not usable:
        return {"steps": 0, "losses": [], "failure_reason": "InvalidPrefix", "trainable": counts}
    params = [p for p in wrapped.parameters() if p.requires_grad]
    optimizer = torch.optim.Adam(params, lr=float(lr)) if params else None
    losses: list[float] = []
    started = time.time()
    wrapped.train()
    for step in range(int(steps)):
        row = usable[step % len(usable)]
        if optimizer is None:
            break
        optimizer.zero_grad(set_to_none=True)
        loss = teacher_forcing_loss(wrapped, row["times"], row["trajectory"], row["tree_encoded"])
        loss.backward()
        optimizer.step()
        losses.append(float(loss.detach().cpu()))
    wrapped.eval()
    return {
        "steps": len(losses),
        "losses": losses,
        "final_loss": losses[-1] if losses else float("nan"),
        "wall_time": time.time() - started,
        "trainable": counts,
        "trainable_parameters": int(sum(p.numel() for p in params)),
    }
