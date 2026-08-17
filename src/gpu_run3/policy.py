"""Teacher-forcing policy evaluation for NDformer."""

from __future__ import annotations

from typing import Any, Sequence

import numpy as np
import torch
import torch.nn.functional as F

from gpu_run3_runtime import install_nd2_path


def policy_from_prefixes(model: Any, prefixes: list[list[str]], *, actions: list[str] | None = None) -> np.ndarray:
    return np.asarray(model.get_policy(prefixes, actions=actions), dtype=np.float64)


def teacher_forcing_metrics(
    model: Any,
    examples: Sequence[dict[str, Any]],
    *,
    top_k: int = 5,
) -> dict[str, Any]:
    """Evaluate next-symbol policy against ground-truth tokens.

    Invalid examples are kept and counted as failures rather than dropped.
    """
    install_nd2_path()
    from ND2.GDExpr import GDExpr

    rows: list[dict[str, Any]] = []
    valid_prefixes = []
    valid_targets = []
    valid_indices = []
    for idx, example in enumerate(examples):
        target = example.get("target")
        prefix = list(example.get("prefix") or [])
        if not target or target not in GDExpr.word2id:
            rows.append(
                {
                    "example_index": idx,
                    "prefix": prefix,
                    "target": target,
                    "failure_reason": example.get("failure_reason") or "InvalidSymbol",
                    "valid": False,
                }
            )
            continue
        valid_prefixes.append(prefix)
        valid_targets.append(target)
        valid_indices.append(idx)

    policies = None
    if valid_prefixes:
        policies = policy_from_prefixes(model, valid_prefixes)

    ce_values: list[float] = []
    top1 = []
    topk = []
    ranks = []
    true_probs = []
    entropies = []
    policy_iter = iter(policies if policies is not None else [])
    valid_lookup = {orig: i for i, orig in enumerate(valid_indices)}
    for idx, example in enumerate(examples):
        if idx not in valid_lookup:
            continue
        policy = next(policy_iter)
        target = valid_targets[valid_lookup[idx]]
        target_id = int(GDExpr.word2id[target])
        if target_id >= len(policy):
            rows.append(
                {
                    "example_index": idx,
                    "prefix": example.get("prefix"),
                    "target": target,
                    "failure_reason": "InvalidSymbol",
                    "valid": False,
                }
            )
            continue
        log_policy = np.log(np.clip(policy, 1e-12, 1.0))
        ce = float(-log_policy[target_id])
        order = np.argsort(-policy)
        rank = int(np.where(order == target_id)[0][0]) + 1
        entropy = float(-(policy * log_policy).sum())
        ce_values.append(ce)
        top1.append(float(rank == 1))
        topk.append(float(rank <= top_k))
        ranks.append(rank)
        true_probs.append(float(policy[target_id]))
        entropies.append(entropy)
        rows.append(
            {
                "example_index": idx,
                "prefix": example.get("prefix"),
                "target": target,
                "target_id": target_id,
                "ce": ce,
                "rank": rank,
                "true_probability": float(policy[target_id]),
                "true_logit": float(log_policy[target_id]),
                "top1": rank == 1,
                "topk": rank <= top_k,
                "entropy": entropy,
                "topk_symbols": [GDExpr.id2word.get(int(i), str(i)) for i in order[:top_k]],
                "topk_probs": [float(policy[int(i)]) for i in order[:top_k]],
                "valid": True,
                "failure_reason": None,
            }
        )

    n = len(examples)
    n_valid = sum(1 for row in rows if row.get("valid"))
    return {
        "n_examples": n,
        "n_valid": n_valid,
        "valid_rate": float(n_valid / n) if n else 0.0,
        "cross_entropy": float(np.mean(ce_values)) if ce_values else float("nan"),
        "top1_accuracy": float(np.mean(top1)) if top1 else float("nan"),
        "topk_accuracy": float(np.mean(topk)) if topk else float("nan"),
        "mean_true_symbol_rank": float(np.mean(ranks)) if ranks else float("nan"),
        "mean_true_symbol_probability": float(np.mean(true_probs)) if true_probs else float("nan"),
        "mean_policy_entropy": float(np.mean(entropies)) if entropies else float("nan"),
        "rows": rows,
    }


def policy_cross_entropy_loss(model: Any, prefixes: list[list[str]], targets: list[str]) -> torch.Tensor:
    """Differentiable policy CE for fine-tuning. Uses decoder logits, not softmaxed get_policy."""
    install_nd2_path()
    from ND2.GDExpr import GDExpr

    if not hasattr(model, "data_emb") or model.data_emb is None:
        raise RuntimeError("NDformer.set_data() must be called before policy_cross_entropy_loss")
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
    _, policy_logits, _ = model.decoder(data_emb, expr_ids, parents, types)
    target_ids = torch.tensor(
        [int(GDExpr.word2id[model.var_map.get(target, target)]) for target in targets],
        device=model.device,
        dtype=torch.long,
    )
    return F.cross_entropy(policy_logits, target_ids)
