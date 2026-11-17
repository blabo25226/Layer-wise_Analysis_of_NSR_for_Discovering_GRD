"""Layer-wise readouts for ODEFormer under teacher forcing.

Every block output analysed here is the output of ``layer_norm2[i]`` (post-LN
residual stream), the same tensor that the next block reads. Decoder hidden
states have shape (batch, position, dim); position p predicts target token p.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterator, Sequence

import numpy as np
import torch
from torch import nn

from gpu_run4.architecture import resolve_layer_module, unwrap_model

N_ENC, N_DEC = 4, 12
ENC_LAYERS = [f"encoder_{i}" for i in range(N_ENC)]
DEC_LAYERS = [f"decoder_{i}" for i in range(N_DEC)]
ALL_LAYERS = ENC_LAYERS + DEC_LAYERS

STRUCT_TOKENS = {"add", "mul", "inv", "pow2", "sin", "id", "|", "x_0", "x_1", "x_2", "x_3", "x_4", "x_5"}


def token_category(token: str) -> str:
    if token in {"inv"}:
        return "inv"
    if token in {"add", "mul", "pow2", "sin", "id", "|"}:
        return "operator"
    if token.startswith("x_"):
        return "variable"
    if token in {"+", "-"} or token.startswith("N") or token.startswith("E"):
        return "constant"
    if token in {"<EOS>", "</s>"}:
        return "eos"
    return "other"


def _point_bag(times: np.ndarray, trajectory: np.ndarray) -> list:
    return [[float(t), np.asarray(y, dtype=float)] for t, y in zip(np.asarray(times), np.asarray(trajectory))]


def encode_tokens(wrapped: Any, prefix: str) -> list[str]:
    env = wrapped.env
    tree = env.equation_encoder.decode(prefix.split(","))
    if tree is None:
        raise ValueError(f"cannot decode prefix {prefix}")
    return list(env.equation_encoder.encode(tree))


@contextmanager
def _hooks(wrapped: Any, capture: Sequence[str] = (), replace: dict[str, torch.Tensor] | None = None) -> Iterator[dict]:
    captured: dict[str, torch.Tensor] = {}
    handles = []

    def make(name: str):
        def hook(_m: nn.Module, _i: Any, output: Any) -> Any:
            tensor = output[0] if isinstance(output, tuple) else output
            if replace and name in replace:
                new = replace[name].to(device=tensor.device, dtype=tensor.dtype)
                if new.shape != tensor.shape:  # never silently broadcast
                    raise RuntimeError(f"PatchShapeMismatch {name}: {tuple(new.shape)} vs {tuple(tensor.shape)}")
                tensor = new
            if name in capture:
                captured[name] = tensor.detach()
            return (tensor, *output[1:]) if isinstance(output, tuple) else tensor
        return hook

    names = set(capture) | set((replace or {}).keys())
    try:
        for name in names:
            handles.append(resolve_layer_module(wrapped, name).register_forward_hook(make(name)))
        yield captured
    finally:
        for h in handles:
            h.remove()


@torch.no_grad()
def forward_teacher(wrapped: Any, times: np.ndarray, trajectory: np.ndarray, tokens: Sequence[str], *,
                    capture: Sequence[str] = (), replace: dict[str, torch.Tensor] | None = None) -> dict[str, Any]:
    """One teacher-forced pass. Returns final log-probs of the targets and captured states."""
    env = wrapped.env
    device = next(wrapped.parameters()).device
    x1, len1 = wrapped.embedder([_point_bag(times, trajectory)])
    x2, len2 = env.batch_equations(env.word_to_idx([list(tokens)], float_input=False))
    x2, len2 = x2.to(device), len2.to(device)
    with _hooks(wrapped, capture, replace) as captured:
        encoded = wrapped.encoder("fwd", x=x1, lengths=len1, causal=False)
        decoded = wrapped.decoder("fwd", x=x2, lengths=len2, causal=True, src_enc=encoded.transpose(0, 1), src_len=len1)
    n_targets = int(len2[0].item()) - 1
    targets = x2[1:n_targets + 1, 0].long()
    final_hidden = decoded.transpose(0, 1)[0, :n_targets]  # decoder fwd returns (slen, bs, dim)
    logp = torch.log_softmax(wrapped.decoder.proj(final_hidden).float(), dim=-1)
    target_logp = logp.gather(1, targets[:, None])[:, 0]
    words = [env.equation_id2word.get(int(t), str(int(t))) for t in targets.tolist()]
    return {"target_logp": target_logp.cpu().numpy(), "targets": targets, "target_words": words,
            "n_targets": n_targets, "captured": captured}


class TunedLens(nn.Module):
    """Affine translator per decoder layer, initialized to identity (Belrose et al. 2023)."""

    def __init__(self, dim: int, n_layers: int):
        super().__init__()
        self.translators = nn.ModuleList([nn.Linear(dim, dim) for _ in range(n_layers)])
        for lin in self.translators:
            nn.init.eye_(lin.weight)
            nn.init.zeros_(lin.bias)

    def forward(self, layer: int, hidden: torch.Tensor) -> torch.Tensor:
        return self.translators[layer](hidden)


@torch.no_grad()
def lens_logprobs(wrapped: Any, times: np.ndarray, trajectory: np.ndarray, tokens: Sequence[str],
                  tuned: TunedLens | None = None) -> dict[str, Any]:
    """Per decoder layer log p(target) under the logit lens and (optionally) the tuned lens."""
    out = forward_teacher(wrapped, times, trajectory, tokens, capture=DEC_LAYERS)
    n = out["n_targets"]
    targets = out["targets"]
    logit = np.zeros((N_DEC, n))
    tuned_lp = np.zeros((N_DEC, n)) if tuned is not None else None
    rank = np.zeros((N_DEC, n), dtype=int)
    for li, name in enumerate(DEC_LAYERS):
        hidden = out["captured"][name][0, :n].float()
        lp = torch.log_softmax(wrapped.decoder.proj(hidden).float(), dim=-1)
        tgt = lp.gather(1, targets[:, None])[:, 0]
        logit[li] = tgt.cpu().numpy()
        rank[li] = (1 + (lp > tgt[:, None]).sum(dim=1)).cpu().numpy()
        if tuned is not None:
            tl = torch.log_softmax(wrapped.decoder.proj(tuned(li, hidden)).float(), dim=-1)
            tuned_lp[li] = tl.gather(1, targets[:, None])[:, 0].cpu().numpy()
    return {"words": out["target_words"], "final": out["target_logp"], "logit_lens": logit,
            "tuned_lens": tuned_lp, "logit_rank": rank}


def train_tuned_lens(wrapped: Any, samples: Sequence[dict[str, Any]], *, epochs: int, lr: float, seed: int,
                     log: Any = None) -> tuple[TunedLens, list[float]]:
    """Distil each layer's translated logits towards the final-layer distribution (KL)."""
    torch.manual_seed(seed)
    device = next(wrapped.parameters()).device
    dim = wrapped.decoder.proj.in_features
    lens = TunedLens(dim, N_DEC).to(device)
    opt = torch.optim.Adam(lens.parameters(), lr=lr)
    history = []
    rng = np.random.default_rng(seed)
    for epoch in range(epochs):
        order = rng.permutation(len(samples))
        total, count = 0.0, 0
        for idx in order:
            row = samples[int(idx)]
            out = forward_teacher(wrapped, row["times"], row["trajectory"], row["tree_encoded"], capture=DEC_LAYERS)
            n = out["n_targets"]
            final = torch.log_softmax(wrapped.decoder.proj(out["captured"][DEC_LAYERS[-1]][0, :n].float()), dim=-1)
            loss = 0.0
            for li in range(N_DEC - 1):
                hidden = out["captured"][DEC_LAYERS[li]][0, :n].float()
                pred = torch.log_softmax(wrapped.decoder.proj(lens(li, hidden)), dim=-1)
                loss = loss + torch.nn.functional.kl_div(pred, final, log_target=True, reduction="batchmean")
            opt.zero_grad()
            loss.backward()
            opt.step()
            total += float(loss.detach())
            count += 1
        history.append(total / max(count, 1))
        if log:
            log(f"tuned lens epoch {epoch}: mean summed KL {history[-1]:.4f}")
    return lens, history


@torch.no_grad()
def probe_features(wrapped: Any, times: np.ndarray, trajectory: np.ndarray, tokens: Sequence[str]) -> dict[str, np.ndarray]:
    """Encoder layers: mean over input points. Decoder layers: state at position 0 (before any
    target token is visible, so no label leakage through teacher forcing)."""
    out = forward_teacher(wrapped, times, trajectory, tokens, capture=ALL_LAYERS)
    feats = {}
    for name in ENC_LAYERS:
        feats[name] = out["captured"][name][0].float().mean(dim=0).cpu().numpy()
    for name in DEC_LAYERS:
        feats[name] = out["captured"][name][0, 0].float().cpu().numpy()
    return feats


def input_baseline_features(times: np.ndarray, trajectory: np.ndarray) -> np.ndarray:
    """Hand-crafted trajectory statistics: the information a probe gets 'for free' from the input."""
    x = np.asarray(trajectory, dtype=float)[:, 0]
    t = np.asarray(times, dtype=float)
    dx = np.gradient(x, t)
    ddx = np.gradient(dx, t)
    q = np.linspace(0.05, 0.95, 10)
    rate = dx / np.where(np.abs(x) > 1e-6, x, 1e-6)
    return np.concatenate([np.quantile(x, q), np.quantile(dx, q), np.quantile(ddx, q), np.quantile(rate, q),
                           [x[0], x[-1], dx[0], dx[-1]]])


@torch.no_grad()
def block_skip_logprobs(wrapped: Any, times: np.ndarray, trajectory: np.ndarray, tokens: Sequence[str],
                        layers: Sequence[str] = DEC_LAYERS[1:]) -> dict[str, np.ndarray]:
    """Skip decoder block l (l >= 1): its output is replaced by its input, i.e. the output of block l-1
    computed in the same intervened pass. Implemented by chaining one hook that copies the previous
    block's output. Returns final target log-probs per skipped block."""
    out: dict[str, np.ndarray] = {}
    for name in layers:
        index = int(name.split("_")[1])
        prev_module = resolve_layer_module(wrapped, f"decoder_{index - 1}")
        this_module = resolve_layer_module(wrapped, name)
        store: dict[str, torch.Tensor] = {}
        h1 = prev_module.register_forward_hook(lambda _m, _i, o: store.__setitem__("prev", o.detach()) or o)
        h2 = this_module.register_forward_hook(lambda _m, _i, o: store["prev"])
        try:
            res = forward_teacher(wrapped, times, trajectory, tokens)
        finally:
            h1.remove()
            h2.remove()
        out[name] = res["target_logp"]
    return out


@torch.no_grad()
def patching_curve(wrapped: Any, clean: dict[str, Any], corrupt: dict[str, Any], tokens: Sequence[str],
                   layers: Sequence[str] = ALL_LAYERS) -> dict[str, Any]:
    """Denoising patching: run on the corrupt input, overwrite one block output with the clean run's
    output, and score the clean target tokens. Returns per-layer target log-probs."""
    t_c, y_c = np.asarray(clean["times"]), np.asarray(clean["trajectory"])
    t_k, y_k = np.asarray(corrupt["times"]), np.asarray(corrupt["trajectory"])
    clean_out = forward_teacher(wrapped, t_c, y_c, tokens, capture=list(layers))
    corrupt_out = forward_teacher(wrapped, t_k, y_k, tokens)
    patched = {}
    for name in layers:
        res = forward_teacher(wrapped, t_k, y_k, tokens, replace={name: clean_out["captured"][name]})
        patched[name] = res["target_logp"]
    # sanity: patching the corrupt run with its own activations must reproduce it exactly
    self_name = layers[len(layers) // 2]
    own = forward_teacher(wrapped, t_k, y_k, tokens, capture=[self_name])
    self_patch = forward_teacher(wrapped, t_k, y_k, tokens, replace={self_name: own["captured"][self_name]})
    return {"words": clean_out["target_words"], "clean": clean_out["target_logp"], "corrupt": corrupt_out["target_logp"],
            "patched": patched,
            "self_patch_max_abs_diff": float(np.max(np.abs(self_patch["target_logp"] - corrupt_out["target_logp"])))}
