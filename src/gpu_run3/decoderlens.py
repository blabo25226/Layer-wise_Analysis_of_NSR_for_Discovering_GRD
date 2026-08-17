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


def encoder_ted_trajectory(
    layer_rows: list[dict[str, Any]],
    *,
    true_prefix: Sequence[str],
) -> list[dict[str, Any]]:
    """Attach TED between a provisional top-1 continuation and the true formula when parseable."""
    out = []
    for row in layer_rows:
        if not row.get("valid"):
            out.append(row)
            continue
        attached = []
        for item in row.get("rows") or []:
            top = (item.get("topk_symbols") or [None])[0]
            provisional = list(item.get("prefix") or [])
            if top:
                provisional = [*provisional, str(top)]
            comparison = compare_formulas(list(true_prefix), provisional)
            attached.append({**item, "provisional_prefix": provisional, "ted_raw": comparison["ted_raw"], "exact": comparison["exact"]})
        out.append({**row, "rows": attached})
    return out
