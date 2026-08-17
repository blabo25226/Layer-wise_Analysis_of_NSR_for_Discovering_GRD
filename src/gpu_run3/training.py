"""IOLE / selective fine-tuning of NDformer Transformer blocks."""

from __future__ import annotations

import copy
import time
from typing import Any, Sequence

import torch

from gpu_run3.architecture import set_trainable_layers
from gpu_run3.policy import policy_cross_entropy_loss, teacher_forcing_metrics


def clone_model(model: Any) -> Any:
    clone = copy.deepcopy(model)
    clone.to(model.device)
    return clone


def train_policy_steps(
    model: Any,
    examples: Sequence[dict[str, Any]],
    *,
    steps: int,
    lr: float = 1e-4,
    data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    started = time.time()
    if data is not None:
        model.set_data(
            Xv=data["Xv"],
            Xe=data.get("Xe") or {},
            A=data["A"],
            G=data["G"],
            Y=data["Y"],
            root_type=data.get("root_type", "node"),
            cache_data_emb=True,
        )
    trainable = [p for p in model.parameters() if p.requires_grad]
    optimizer = torch.optim.Adam(trainable, lr=lr) if trainable else None
    losses: list[float] = []
    model.train()
    usable = [ex for ex in examples if ex.get("target") and ex.get("prefix") is not None]
    if not usable:
        return {"steps": 0, "losses": [], "wall_time": 0.0, "failure_reason": "InvalidPrefix"}
    for step in range(int(steps)):
        batch = usable[step % len(usable) : step % len(usable) + 1]
        prefixes = [list(item["prefix"]) for item in batch]
        targets = [str(item["target"]) for item in batch]
        if optimizer is None:
            break
        optimizer.zero_grad(set_to_none=True)
        loss = policy_cross_entropy_loss(model, prefixes, targets)
        loss.backward()
        optimizer.step()
        losses.append(float(loss.detach().cpu()))
    model.eval()
    return {
        "steps": int(len(losses)),
        "losses": losses,
        "wall_time": time.time() - started,
        "trainable_parameters": int(sum(p.numel() for p in trainable)),
    }


def evaluate_examples(model: Any, examples: Sequence[dict[str, Any]], data: dict[str, Any]) -> dict[str, Any]:
    model.eval()
    model.set_data(
        Xv=data["Xv"],
        Xe=data.get("Xe") or {},
        A=data["A"],
        G=data["G"],
        Y=data["Y"],
        root_type=data.get("root_type", "node"),
        cache_data_emb=True,
    )
    return teacher_forcing_metrics(model, examples)


def parameter_update_norms(before: Any, after: Any, layer_names: Sequence[str]) -> dict[str, dict[str, float]]:
    from gpu_run3.architecture import resolve_layer_module

    out: dict[str, dict[str, float]] = {}
    for name in layer_names:
        left = resolve_layer_module(before, name)
        right = resolve_layer_module(after, name)
        delta_sq = 0.0
        base_sq = 0.0
        for p_before, p_after in zip(left.parameters(), right.parameters()):
            diff = (p_after.detach() - p_before.detach()).float()
            delta_sq += float(torch.sum(diff * diff))
            base_sq += float(torch.sum(p_before.detach().float() * p_before.detach().float()))
        delta = delta_sq ** 0.5
        base = base_sq ** 0.5
        out[name] = {
            "delta_l2": delta,
            "theta_l2": base,
            "relative_l2": float(delta / base) if base > 0 else float("nan"),
        }
    return out


def iole_condition_name(layer_name: str | None, *, full: bool = False, frozen: bool = False) -> str:
    if frozen:
        return "frozen"
    if full:
        return "full"
    if layer_name is None:
        return "unknown"
    return f"iole::{layer_name}"


def run_iole_sweep(
    model: Any,
    *,
    layer_names: Sequence[str],
    examples: Sequence[dict[str, Any]],
    data: dict[str, Any],
    steps: int,
    include_frozen: bool = True,
    include_full: bool = True,
) -> dict[str, Any]:
    results = []
    baseline = clone_model(model)
    conditions: list[tuple[str, list[str] | None, bool]] = []
    if include_frozen:
        conditions.append(("frozen", [], False))
    for name in layer_names:
        conditions.append((iole_condition_name(name), [name], False))
    if include_full:
        conditions.append(("full", None, True))
    for condition, layers, train_all in conditions:
        candidate = clone_model(baseline)
        param_info = set_trainable_layers(candidate, layers, train_all=train_all)
        train_info = {"steps": 0, "losses": [], "wall_time": 0.0, "trainable_parameters": 0}
        if condition != "frozen":
            train_info = train_policy_steps(candidate, examples, steps=steps, data=data)
        metrics = evaluate_examples(candidate, examples, data)
        results.append(
            {
                "condition": condition,
                "layers": layers,
                **param_info,
                **{k: v for k, v in metrics.items() if k != "rows"},
                "train": train_info,
            }
        )
    return {"results": results}
