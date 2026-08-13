"""DecoderLens for NeSymReS (Langedijk et al., arXiv:2310.03686).

Each encoder ISAB output is passed through the final PMA pooling (the encoder's
terminal normalization / pooling) and used as cross-attention memory for the
**original decoder**. No extra training is performed. Decoder-side logit lens
is intentionally not implemented here.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Mapping, Sequence

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


def prepare_encoder_input(model: nn.Module, X: np.ndarray, y: np.ndarray) -> torch.Tensor:
    """Build the NeSymReS encoder tensor ``[x_1, x_2, x_3, y]`` used by ``fitfunc``."""
    from models.nesymres_adapter import pad_features_to_three

    device = getattr(model, "device", next(model.parameters()).device)
    xp = pad_features_to_three(np.asarray(X))
    yv = np.asarray(y, dtype=np.float32).ravel()[:, None]
    x_t = torch.tensor(xp, device=device).unsqueeze(0)
    dim_input = int(getattr(model.cfg, "dim_input"))
    if x_t.shape[2] < dim_input - 1:
        pad = torch.zeros(1, x_t.shape[1], dim_input - x_t.shape[2] - 1, device=device)
        x_t = torch.cat((x_t, pad), dim=2)
    y_t = torch.tensor(yv, device=device).unsqueeze(0)
    return torch.cat((x_t, y_t), dim=2)


def prefix_tokens_to_equation(
    prefix_tokens: Sequence[str],
    *,
    variables: Sequence[str] | None = None,
    coefficients: Sequence[str] | None = None,
) -> tuple[str, bool]:
    """Parse DecoderLens prefix tokens into an infix string when possible."""
    tokens = [str(tok) for tok in prefix_tokens if str(tok) not in {"", "S", "F", "P"}]
    if not tokens:
        return "", False
    try:
        from nesymres.dataset.generator import Generator

        infix = Generator.prefix_to_infix(
            tokens,
            coefficients=list(coefficients or ["c", "c0", "c1", "c2"]),
            variables=list(variables or ["x_1", "x_2", "x_3"]),
        )
        return str(infix), True
    except Exception:
        return " ".join(tokens), False


def run_decoder_lens(
    model: nn.Module,
    X: np.ndarray,
    y: np.ndarray,
    *,
    encoder_layer: int,
    id2word: dict[int, str],
    word2id: dict[str, int],
    max_len: int | None = None,
    topk: int = 5,
    gt_token_ids: Sequence[int] | None = None,
    variables: Sequence[str] | None = None,
) -> list[DecoderLensStep]:
    """Greedy decode with intermediate-encoder PMA memory and the original decoder."""
    model.eval()
    device = getattr(model, "device", next(model.parameters()).device)
    encoder_input = prepare_encoder_input(model, X, y)
    memory = encoder_memory_at_layer(model.enc, encoder_input, int(encoder_layer))
    length_eq = int(max_len or getattr(model.cfg, "length_eq"))
    generated = torch.zeros((1, length_eq), dtype=torch.long, device=device)
    generated[0, 0] = int(word2id.get("S", 1))
    finish_id = int(word2id.get("F", -1))
    steps: list[DecoderLensStep] = []
    with torch.no_grad():
        for cur_len in range(1, length_eq):
            generated_mask1, generated_mask2 = model.make_trg_mask(generated[:, :cur_len])
            positions = (
                torch.arange(0, cur_len, device=device)
                .unsqueeze(0)
                .repeat(generated.shape[0], 1)
                .type_as(generated)
            )
            trg = model.dropout(model.tok_embedding(generated[:, :cur_len]) + model.pos_embedding(positions))
            output = model.decoder_transfomer(
                trg.permute(1, 0, 2),
                memory.permute(1, 0, 2),
                generated_mask2.float(),
                tgt_key_padding_mask=generated_mask1.bool(),
            )
            logits = model.fc_out(output).permute(1, 0, 2).contiguous()[:, -1, :]
            gt_id = None
            if gt_token_ids is not None and cur_len < len(gt_token_ids):
                gt_id = int(gt_token_ids[cur_len])
            tokens, probs, rank = topk_from_logits(
                logits[0], id2word, k=int(topk), ground_truth_id=gt_id
            )
            next_id = int(torch.argmax(logits[0]).item())
            generated[0, cur_len] = next_id
            partial_ids = [int(t) for t in generated[0, 1 : cur_len + 1].tolist() if int(t) != finish_id]
            partial_names = [id2word.get(tid, str(tid)) for tid in partial_ids]
            raw, parseable = prefix_tokens_to_equation(partial_names, variables=variables)
            simplified = ""
            if parseable and raw:
                try:
                    import sympy as sp

                    simplified = str(sp.simplify(sp.sympify(str(raw).replace("^", "**"))))
                except Exception:
                    simplified = raw
            steps.append(
                DecoderLensStep(
                    encoder_layer=int(encoder_layer),
                    decode_step=int(cur_len - 1),
                    topk_tokens=tokens,
                    topk_probs=probs,
                    gt_token_rank=rank,
                    partial_tokens=partial_names,
                    parseable=bool(parseable),
                    raw_equation=raw,
                    simplified_equation=simplified,
                    oracle_inputs=list(variables or []),
                )
            )
            if next_id == finish_id:
                break
    return steps


def write_decoder_lens_rank_heatmap(
    steps: Sequence[DecoderLensStep | Mapping[str, Any]],
    path: Path,
) -> Path | None:
    """Save mean GT-token rank by encoder layer × decode step. No-op without matplotlib."""
    from collections import defaultdict

    ranks: dict[tuple[int, int], list[float]] = defaultdict(list)
    for step in steps:
        payload = step.to_dict() if isinstance(step, DecoderLensStep) else dict(step)
        rank = payload.get("gt_token_rank")
        if rank is None:
            continue
        ranks[(int(payload["encoder_layer"]), int(payload["decode_step"]))].append(float(rank))
    if not ranks:
        return None
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return None
    layers = sorted({layer for layer, _ in ranks})
    decode_steps = sorted({step for _, step in ranks})
    matrix = np.full((len(layers), len(decode_steps)), np.nan)
    for i, layer in enumerate(layers):
        for j, decode_step in enumerate(decode_steps):
            values = ranks.get((layer, decode_step))
            if values:
                matrix[i, j] = float(np.mean(values))
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(max(4.0, 0.35 * len(decode_steps)), max(3.0, 0.4 * len(layers))))
    image = ax.imshow(matrix, aspect="auto", origin="lower", cmap="viridis_r")
    ax.set_xticks(range(len(decode_steps)), decode_steps)
    ax.set_yticks(range(len(layers)), [f"encoder_{i}" for i in layers])
    ax.set_xlabel("decode step")
    ax.set_ylabel("encoder layer")
    ax.set_title("DecoderLens mean GT token rank (lower is better)")
    fig.colorbar(image, ax=ax, label="rank")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
    return path
