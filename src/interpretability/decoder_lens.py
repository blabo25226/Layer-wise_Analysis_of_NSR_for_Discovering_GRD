"""DecoderLens for NeSymReS (Langedijk et al., arXiv:2310.03686).

Each encoder ISAB output is passed through the final PMA pooling (the encoder's
terminal normalization / pooling) and used as cross-attention memory for the
**original decoder**. No extra training is performed. Decoder-side logit lens
is intentionally not implemented here.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Sequence

import numpy as np
import torch
from torch import nn


@dataclass
class DecoderLensStep:
    encoder_layer: int
    decode_step: int
    topk_tokens: list[str]
    topk_probs: list[float]
    gt_token_rank: int | None
    partial_tokens: list[str]
    parseable: bool
    raw_equation: str
    simplified_equation: str
    noise: float | None = None
    seed: int | None = None
    checkpoint: str | None = None
    oracle_inputs: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def apply_final_encoder_pool(encoder: nn.Module, hidden: torch.Tensor) -> torch.Tensor:
    """Apply the SetEncoder PMA (``outatt``) to an intermediate ISAB state."""
    if not hasattr(encoder, "outatt"):
        raise AttributeError("SetEncoder-like module must expose outatt (PMA)")
    return encoder.outatt(hidden)


def encoder_hidden_states(encoder: nn.Module, x: torch.Tensor) -> list[torch.Tensor]:
    """Return post-ISAB hidden states, one per encoder layer (before PMA)."""
    hidden = x
    if getattr(encoder, "bit16", False):
        hidden = encoder.float2bit(hidden)
        hidden = hidden.view(hidden.shape[0], hidden.shape[1], -1)
        if getattr(encoder, "norm", False):
            hidden = (hidden - 0.5) * 2
    if getattr(encoder, "input_normalization", False):
        means = hidden[:, :, -1].mean(axis=1).reshape(-1, 1)
        std = hidden[:, :, -1].std(axis=1).reshape(-1, 1)
        std[std == 0] = 1
        hidden = hidden.clone()
        hidden[:, :, -1] = (hidden[:, :, -1] - means) / std
    if getattr(encoder, "linear", False):
        if encoder.activation == "relu":
            hidden = torch.relu(encoder.linearl(hidden))
        elif encoder.activation == "sine":
            hidden = torch.sin(encoder.linearl(hidden))
        else:
            hidden = encoder.linearl(hidden)
    states = []
    hidden = encoder.selfatt1(hidden)
    states.append(hidden)
    for layer in encoder.selfatt:
        hidden = layer(hidden)
        states.append(hidden)
    return states


def encoder_memory_at_layer(encoder: nn.Module, x: torch.Tensor, layer_index: int) -> torch.Tensor:
    """Intermediate ISAB state + final PMA, for DecoderLens memory."""
    states = encoder_hidden_states(encoder, x)
    if layer_index < 0 or layer_index >= len(states):
        raise IndexError(f"encoder layer_index {layer_index} out of range 0..{len(states) - 1}")
    return apply_final_encoder_pool(encoder, states[layer_index])


def summarize_decoder_lens_steps(
    steps: Sequence[DecoderLensStep],
) -> dict[str, Any]:
    parseable = [step for step in steps if step.parseable]
    return {
        "n_steps": len(steps),
        "n_parseable": len(parseable),
        "parseable_rate": len(parseable) / len(steps) if steps else 0.0,
        "encoder_layers": sorted({step.encoder_layer for step in steps}),
        "steps": [step.to_dict() for step in steps],
    }


def topk_from_logits(
    logits: torch.Tensor,
    id2word: dict[int, str],
    *,
    k: int = 5,
    ground_truth_id: int | None = None,
) -> tuple[list[str], list[float], int | None]:
    """Return top-k tokens/probs and the rank of the ground-truth token."""
    probs = torch.softmax(logits.float(), dim=-1)
    values, indices = torch.topk(probs, k=min(k, probs.numel()))
    tokens = [id2word.get(int(i), str(int(i))) for i in indices.tolist()]
    rank = None
    if ground_truth_id is not None:
        order = torch.argsort(probs, descending=True)
        matches = (order == int(ground_truth_id)).nonzero(as_tuple=False)
        if len(matches):
            rank = int(matches[0].item()) + 1
    return tokens, [float(v) for v in values.tolist()], rank
