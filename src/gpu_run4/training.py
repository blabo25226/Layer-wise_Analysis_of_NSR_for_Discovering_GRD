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


def teacher_forced_summed_logprob(
    model: Any, times: np.ndarray, trajectory: np.ndarray, tree_encoded: Sequence[str]
) -> tuple[float, int, list[float]]:
    """Teacher-forced **summed** log-probability of ``tree_encoded`` under the
    model, given the same conditioning trajectory as :func:`teacher_forcing_loss`.

    Added for GPU_RUNclaude1 C0001 (v2 §8.2 step 3): the paired
    Stahlberg-Byrne discriminator needs a probability-comparable quantity
    (``sum log P``), not the length-normalized mean cross-entropy
    :func:`teacher_forcing_loss` returns. This function is purely additive --
    :func:`teacher_forcing_loss` is not modified, since other phases depend on
    its exact return value -- and runs through the identical
    embed/encode/decode call sequence so the two are computed from the same
    forward pass in every respect but the final reduction.

    Returns ``(sum_logprob, n_scored_tokens, per_token_logprobs)``. The
    regression identity ``sum_logprob / n_scored_tokens == -teacher_forcing_loss(...)``
    must hold to 1e-5 (v2 §8.2 step 3), because ``teacher_forcing_loss``'s
    ``loss`` is exactly the mean cross-entropy over the same ``pred_mask``
    positions, i.e. ``-mean(log P(y))``.
    """
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
    scores, _loss = decoder("predict", tensor=decoded, pred_mask=pred_mask, y=y, get_scores=True)
    log_probs = torch.log_softmax(scores.float(), dim=-1)
    token_logprobs = log_probs.gather(1, y.view(-1, 1)).view(-1)
    sum_logprob = float(token_logprobs.sum().item())
    n_scored_tokens = int(y.numel())
    per_token_logprobs = [float(v) for v in token_logprobs.detach().cpu().tolist()]
    return sum_logprob, n_scored_tokens, per_token_logprobs


def teacher_forced_summed_logprob_batch(
    model: Any,
    times: np.ndarray,
    trajectory: np.ndarray,
    tree_encoded_list: Sequence[Sequence[str]],
    *,
    compute_ranks: bool = False,
) -> list[tuple[float, int, list[float], list[int] | None, list[int]]]:
    """Score multiple sequences against **one** cached encoder pass (v2 §8.2
    step 2: "run embedder + encoder ... once, cache src_enc for every
    sequence in the cell" -- both the compute-saving and the fairness
    construction of §5 item 5).

    Purely additive beside :func:`teacher_forced_summed_logprob` (never
    modifies it, and never modifies :func:`teacher_forcing_loss`): the
    embed/encode call sequence is identical, only run once and reused across
    every sequence in ``tree_encoded_list`` instead of once per sequence.
    Every individual entry must reproduce
    :func:`teacher_forced_summed_logprob`'s result to floating-point
    tolerance for the same conditioning trajectory and sequence -- this is
    asserted by a regression test, not merely implied by shared code.

    Returns a list, same order as ``tree_encoded_list``, of
    ``(sum_logprob, n_scored_tokens, per_token_logprobs, token_ranks, token_ids)``.
    ``token_ranks[i]`` is the 0-indexed rank of the true token at scored
    position ``i`` within the full vocabulary at that position (0 = the
    model's argmax), computed only when ``compute_ranks`` is True (v2 §8.3
    C2-S5); otherwise ``token_ranks`` is ``None`` for every entry, since no
    endpoint needs it for a candidate, only for GT-mult. ``token_ids`` is
    always returned (negligible extra cost): the vocabulary id truly scored
    at each position, same order as ``per_token_logprobs``, so a caller can
    map back to the token string via ``env.equation_id2word`` for C2-S5's
    per-token-class breakdown without a second forward pass.
    """
    install_odeformer_path()
    wrapped = unwrap_model(model)
    env = wrapped.env
    embedder = wrapped.embedder
    encoder = wrapped.encoder
    decoder = wrapped.decoder
    device = next(wrapped.parameters()).device
    x1, len1 = embedder([_point_bag(times, trajectory)])
    encoded = encoder("fwd", x=x1, lengths=len1, causal=False)
    src_enc = encoded.transpose(0, 1)

    results: list[tuple[float, int, list[float], list[int] | None, list[int]]] = []
    for tree_encoded in tree_encoded_list:
        x2, len2 = env.batch_equations(env.word_to_idx([list(tree_encoded)], float_input=False))
        x2 = x2.to(device)
        len2 = len2.to(device)
        alen = torch.arange(int(len2.max()), dtype=torch.long, device=device)
        pred_mask = alen[:, None] < len2[None] - 1
        y = x2[1:].masked_select(pred_mask[:-1])
        decoded = decoder(
            "fwd",
            x=x2,
            lengths=len2,
            causal=True,
            src_enc=src_enc,
            src_len=len1,
        )
        scores, _loss = decoder("predict", tensor=decoded, pred_mask=pred_mask, y=y, get_scores=True)
        log_probs = torch.log_softmax(scores.float(), dim=-1)
        token_logprobs = log_probs.gather(1, y.view(-1, 1)).view(-1)
        sum_logprob = float(token_logprobs.sum().item())
        n_scored_tokens = int(y.numel())
        per_token_logprobs = [float(v) for v in token_logprobs.detach().cpu().tolist()]
        token_ranks: list[int] | None = None
        if compute_ranks:
            true_scores = scores.gather(1, y.view(-1, 1))
            # Number of vocabulary entries with a strictly greater score than
            # the true token at that position; 0 == the model's own argmax.
            token_ranks = (scores > true_scores).sum(dim=-1).detach().cpu().tolist()
            token_ranks = [int(v) for v in token_ranks]
        token_ids = [int(v) for v in y.detach().cpu().tolist()]
        results.append((sum_logprob, n_scored_tokens, per_token_logprobs, token_ranks, token_ids))
    return results


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
