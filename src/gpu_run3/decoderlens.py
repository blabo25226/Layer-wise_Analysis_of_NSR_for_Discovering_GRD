"""DecoderLens-style encoder readout and decoder logit-lens for NDformer."""

from __future__ import annotations

from typing import Any, Sequence

import numpy as np
import torch
import torch.nn.functional as F

from gpu_run3.architecture import resolve_layer_module
from gpu_run3.formulas import compare_formulas
from gpu_run3.hooks import capture_layer_outputs
from gpu_run3_runtime import install_nd2_path


def _decode_policy(model: Any, data_emb: torch.Tensor, prefixes: list[list[str]]) -> np.ndarray:
    install_nd2_path()
    from ND2.GDExpr import GDExpr

    mapped = [[model.var_map.get(token, token) for token in prefix] for prefix in prefixes]
    expr_ids = [torch.from_numpy(GDExpr.vectorize(["sos", model.root_type, *prefix, "eos"])) for prefix in mapped]
    expr_ids = torch.nn.utils.rnn.pad_sequence(expr_ids, batch_first=True, padding_value=GDExpr.pad_id).to(model.device)
    parents = [torch.LongTensor([0, 0, *GDExpr.analysis_parent(prefix, 0, 1), 0]) for prefix in mapped]
    parents = torch.nn.utils.rnn.pad_sequence(parents, batch_first=True, padding_value=GDExpr.pad_id).to(model.device)
    types = [
        torch.from_numpy(GDExpr.vectorize(["sos", model.root_type, *GDExpr.analysis_type(prefix, model.root_type), "eos"]))
        for prefix in mapped
    ]
    types = torch.nn.utils.rnn.pad_sequence(types, batch_first=True, padding_value=GDExpr.pad_id).to(model.device)
    _, policy_logits, _ = model.decoder(data_emb.to(model.device), expr_ids, parents, types)
    return torch.softmax(policy_logits, dim=-1).detach().cpu().numpy()


def encoder_intermediate_decode(
    model: Any,
    encoder_layers: Sequence[str],
    prefixes: list[list[str]],
    *,
    true_targets: list[str] | None = None,
    collect_memories: dict[str, torch.Tensor] | None = None,
) -> list[dict[str, Any]]:
    """Pass each encoder block output as decoder memory. Not claimed to be identical to DecoderLens."""
    install_nd2_path()
    from ND2.GDExpr import GDExpr

    if model.data_emb is None:
        raise RuntimeError("set_data() must be called first")
    # Re-run encoder to capture intermediates. Use a dummy decode prefix to trigger encoder via encode().
    captured: dict[str, torch.Tensor] = {}
    with capture_layer_outputs(model, list(encoder_layers)) as captured:
        _ = model.encode(model.root_type, model.var_dict)
    if collect_memories is not None:
        collect_memories.update({name: tensor for name, tensor in captured.items()})
    rows = []
    for layer_name in encoder_layers:
        hidden = captured.get(layer_name)
        if hidden is None:
            rows.append({"module_name": layer_name, "failure_reason": "ActivationHookError", "valid": False})
            continue
        policy = _decode_policy(model, hidden, prefixes)
        layer_rows = []
        for i, prefix in enumerate(prefixes):
            probs = policy[i]
            order = np.argsort(-probs)
            target = None if true_targets is None else true_targets[i]
            rank = None
            true_prob = None
            if target is not None and target in GDExpr.word2id:
                target_id = int(GDExpr.word2id[model.var_map.get(target, target)])
                rank = int(np.where(order == target_id)[0][0]) + 1
                true_prob = float(probs[target_id])
            layer_rows.append(
                {
                    "prefix": prefix,
                    "target": target,
                    "topk_symbols": [GDExpr.id2word.get(int(j), str(j)) for j in order[:5]],
                    "topk_probs": [float(probs[int(j)]) for j in order[:5]],
                    "true_symbol_rank": rank,
                    "true_symbol_probability": true_prob,
                    "entropy": float(-(probs * np.log(np.clip(probs, 1e-12, 1))).sum()),
                }
            )
        rows.append(
            {
                "module_name": layer_name,
                "analysis_type": "encoder_intermediate_decode",
                "rows": layer_rows,
                "valid": True,
                "failure_reason": None,
            }
        )
    return rows


def decoder_logit_lens(
    model: Any,
    decoder_layers: Sequence[str],
    prefixes: list[list[str]],
    *,
    true_targets: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Apply the final policy readout to intermediate decoder hidden states."""
    install_nd2_path()
    from ND2.GDExpr import GDExpr

    mapped = [[model.var_map.get(token, token) for token in prefix] for prefix in prefixes]
    expr_ids = [torch.from_numpy(GDExpr.vectorize(["sos", model.root_type, *prefix, "eos"])) for prefix in mapped]
    expr_ids = torch.nn.utils.rnn.pad_sequence(expr_ids, batch_first=True, padding_value=GDExpr.pad_id).to(model.device)
    parents = [torch.LongTensor([0, 0, *GDExpr.analysis_parent(prefix, 0, 1), 0]) for prefix in mapped]
    parents = torch.nn.utils.rnn.pad_sequence(parents, batch_first=True, padding_value=GDExpr.pad_id).to(model.device)
    types = [
        torch.from_numpy(GDExpr.vectorize(["sos", model.root_type, *GDExpr.analysis_type(prefix, model.root_type), "eos"]))
        for prefix in mapped
    ]
    types = torch.nn.utils.rnn.pad_sequence(types, batch_first=True, padding_value=GDExpr.pad_id).to(model.device)
    data_emb = model.data_emb.to(model.device)
    with capture_layer_outputs(model, list(decoder_layers)) as captured:
        _ = model.decoder(data_emb, expr_ids, parents, types)
    rows = []
    weight = model.decoder.token_embedding.weight
    for layer_name in decoder_layers:
        hidden = captured.get(layer_name)
        if hidden is None or hidden.ndim != 3 or hidden.shape[1] < 2:
            rows.append({"module_name": layer_name, "failure_reason": "ActivationHookError", "valid": False})
            continue
        logits = F.linear(hidden[:, 1, :], weight)
        policy = torch.softmax(logits, dim=-1).detach().cpu().numpy()
        layer_rows = []
        for i, prefix in enumerate(prefixes):
            probs = policy[i]
            order = np.argsort(-probs)
            target = None if true_targets is None else true_targets[i]
            rank = None
            true_prob = None
            if target is not None and target in GDExpr.word2id:
                target_id = int(GDExpr.word2id[model.var_map.get(target, target)])
                rank = int(np.where(order == target_id)[0][0]) + 1
                true_prob = float(probs[target_id])
            layer_rows.append(
                {
                    "prefix": prefix,
                    "target": target,
                    "topk_symbols": [GDExpr.id2word.get(int(j), str(j)) for j in order[:5]],
                    "topk_probs": [float(probs[int(j)]) for j in order[:5]],
                    "true_symbol_rank": rank,
                    "true_symbol_probability": true_prob,
                    "entropy": float(-(probs * np.log(np.clip(probs, 1e-12, 1))).sum()),
                }
            )
        rows.append(
            {
                "module_name": layer_name,
                "analysis_type": "decoder_logit_lens",
                "rows": layer_rows,
                "valid": True,
                "failure_reason": None,
            }
        )
    return rows


def _action_mask(prefix: Sequence[str], *, vars_node: Sequence[str], vars_edge: Sequence[str], max_tokens: int, max_coeff: int):
    """Legal next symbols for the first placeholder, mirroring ND2's MCTS.get_mask."""
    install_nd2_path()
    from ND2.GDExpr import GDExpr

    tokens = list(prefix)
    placeholder_index = next((i for i, t in enumerate(tokens) if t in ("node", "edge")), None)
    if placeholder_index is None:
        return None, None
    placeholder = tokens[placeholder_index]
    allowed: set[str] = set()
    remaining = max_tokens - len(tokens)
    if remaining >= 2:
        allowed |= set(GDExpr.operator.binary)
    if remaining >= 1:
        allowed |= set(GDExpr.operator.unary)
    if placeholder == "edge":
        allowed -= {"aggr", "rgga"}
    else:
        allowed -= {"sour", "targ"}
    if remaining >= 0:
        allowed |= set(vars_node) if placeholder == "node" else set(vars_edge)
        constant_ok = False
        count, pos = 1, placeholder_index - 1
        known_vars = ["node", "edge", *vars_node, *vars_edge]
        while count > 0 and pos >= 0 and not constant_ok:
            token = tokens[pos]
            if token in GDExpr.operator.binary:
                count -= 2
            elif token in GDExpr.operator.unary:
                count -= 1
            elif token in known_vars:
                count += 1
                constant_ok = True
            else:
                count += 1
            pos -= 1
        if constant_ok or count == -1:
            allowed |= set(GDExpr.constant)
            if tokens.count(GDExpr.coeff_token) < max_coeff:
                allowed.add(GDExpr.coeff_token)
    return allowed, placeholder


def _apply_action(prefix: Sequence[str], action: str, placeholder: str) -> list[str]:
    """Replace the first placeholder, mirroring ND2's MCTS.act."""
    install_nd2_path()
    from ND2.GDExpr import GDExpr

    tokens = list(prefix)
    index = next(i for i, t in enumerate(tokens) if t in ("node", "edge"))
    if action in ("aggr", "rgga"):
        return [*tokens[:index], action, "edge", *tokens[index + 1 :]]
    if action in ("sour", "targ"):
        return [*tokens[:index], action, "node", *tokens[index + 1 :]]
    if action in GDExpr.operator.binary:
        return [*tokens[:index], action, placeholder, placeholder, *tokens[index + 1 :]]
    if action in GDExpr.operator.unary:
        return [*tokens[:index], action, placeholder, *tokens[index + 1 :]]
    return [*tokens[:index], action, *tokens[index + 1 :]]


def greedy_rollout(
    model: Any,
    memory: torch.Tensor,
    *,
    root_type: str = "node",
    vars_node: Sequence[str] = (),
    vars_edge: Sequence[str] = (),
    max_tokens: int = 30,
    max_coeff: int = 5,
) -> dict[str, Any]:
    """Greedily complete a formula from one encoder memory, under ND2's grammar.

    Used so each encoder block yields a *complete* formula that can be compared to
    the ground truth. Appending only the top-1 next symbol leaves placeholders in
    the prefix, which never parses and makes every TED a NaN.
    """
    install_nd2_path()
    from ND2.GDExpr import GDExpr

    prefix = [root_type]
    steps = 0
    while steps < max_tokens * 2:
        allowed, placeholder = _action_mask(
            prefix, vars_node=vars_node, vars_edge=vars_edge, max_tokens=max_tokens, max_coeff=max_coeff
        )
        if allowed is None:
            return {"prefix": prefix, "complete": True, "failure_reason": None, "steps": steps}
        if not allowed:
            return {"prefix": prefix, "complete": False, "failure_reason": "InvalidPrefix", "steps": steps}
        probs = _decode_policy(model, memory, [prefix])[0]
        best = max(allowed, key=lambda token: probs[int(GDExpr.word2id[model.var_map.get(token, token)])])
        prefix = _apply_action(prefix, best, placeholder)
        steps += 1
    return {"prefix": prefix, "complete": False, "failure_reason": "MCTSTimeout", "steps": steps}


def encoder_ted_trajectory(
    layer_rows: list[dict[str, Any]],
    *,
    true_prefix: Sequence[str],
    model: Any | None = None,
    memories: dict[str, torch.Tensor] | None = None,
    root_type: str = "node",
    vars_node: Sequence[str] = (),
    vars_edge: Sequence[str] = (),
    max_tokens: int = 30,
) -> list[dict[str, Any]]:
    """Attach a greedy-rollout formula and its TED to each encoder layer's readout."""
    out = []
    for row in layer_rows:
        if not row.get("valid"):
            out.append(row)
            continue
        rollout = None
        if model is not None and memories is not None and row["module_name"] in memories:
            rollout = greedy_rollout(
                model,
                memories[row["module_name"]],
                root_type=root_type,
                vars_node=vars_node,
                vars_edge=vars_edge,
                max_tokens=max_tokens,
            )
        if rollout is None:
            out.append({**row, "rollout": None, "failure_reason": "ActivationHookError"})
            continue
        comparison = compare_formulas(list(true_prefix), rollout["prefix"]) if rollout["complete"] else {}
        out.append(
            {
                **row,
                "rollout_prefix": rollout["prefix"],
                "rollout_complete": rollout["complete"],
                "rollout_steps": rollout["steps"],
                "rollout_failure_reason": rollout["failure_reason"],
                "rollout_formula": comparison.get("pred_raw_expr"),
                "ted_raw": comparison.get("ted_raw"),
                "ted_skeleton": comparison.get("ted_skeleton"),
                "exact": comparison.get("exact"),
                "skeleton": comparison.get("skeleton"),
            }
        )
    return out
