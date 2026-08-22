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


def train_policy_multi_problem(
    model: Any,
    records: Sequence[dict[str, Any]],
    *,
    steps: int,
    lr: float = 1e-4,
    batch_size: int = 4,
    max_examples_per_problem: int = 32,
    seed: int = 0,
) -> dict[str, Any]:
    """Fine-tune the policy across several problems.

    Each step re-runs ``set_data`` for one problem, so the encoder memory matches
    the batch; training on a single formula (the previous behaviour) makes every
    layer comparison an n=1 result.
    """
    import numpy as np

    started = time.time()
    usable = []
    for row in records:
        examples = [ex for ex in row["teacher_forcing"] if ex.get("target")][:max_examples_per_problem]
        if examples:
            usable.append((row, examples))
    if not usable:
        return {"steps": 0, "losses": [], "wall_time": 0.0, "failure_reason": "InvalidPrefix", "n_problems": 0}
    trainable = [p for p in model.parameters() if p.requires_grad]
    if not trainable:
        return {
            "steps": 0,
            "losses": [],
            "wall_time": time.time() - started,
            "trainable_parameters": 0,
            "n_problems": len(usable),
        }
    optimizer = torch.optim.Adam(trainable, lr=lr)
    rng = np.random.default_rng(int(seed))
    losses: list[float] = []
    failures: list[str] = []
    model.train()
    for step in range(int(steps)):
        row, examples = usable[step % len(usable)]
        model.set_data(
            Xv=row["Xv"],
            Xe=row.get("Xe") or {},
            A=row["A"],
            G=row["G"],
            Y=row["Y"],
            root_type=row.get("root_type", "node"),
            cache_data_emb=False,
        )
        pick = rng.choice(len(examples), size=min(int(batch_size), len(examples)), replace=False)
        batch = [examples[int(i)] for i in pick]
        optimizer.zero_grad(set_to_none=True)
        try:
            loss = policy_cross_entropy_loss(
                model,
                [list(item["prefix"]) for item in batch],
                [str(item["target"]) for item in batch],
            )
            loss.backward()
            optimizer.step()
            losses.append(float(loss.detach().cpu()))
        except Exception as exc:  # keep training, but never hide the failure
            failures.append(f"{type(exc).__name__}:{exc}")
    model.eval()
    return {
        "steps": int(len(losses)),
        "requested_steps": int(steps),
        "losses": losses,
        "first_loss": losses[0] if losses else None,
        "last_loss": losses[-1] if losses else None,
        "wall_time": time.time() - started,
        "trainable_parameters": int(sum(p.numel() for p in trainable)),
        "n_problems": len(usable),
        "batch_size": int(batch_size),
        "lr": float(lr),
        "failures": failures,
    }


def evaluate_records(
    model: Any,
    records: Sequence[dict[str, Any]],
    *,
    max_examples_per_problem: int = 32,
) -> dict[str, Any]:
    """Teacher-forcing metrics pooled over several problems."""
    import numpy as np

    model.eval()
    per_problem = []
    all_rows = []
    for row in records:
        examples = [ex for ex in row["teacher_forcing"] if ex.get("target")][:max_examples_per_problem]
        if not examples:
            continue
        model.set_data(
            Xv=row["Xv"],
            Xe=row.get("Xe") or {},
            A=row["A"],
            G=row["G"],
            Y=row["Y"],
            root_type=row.get("root_type", "node"),
            cache_data_emb=True,
        )
        metrics = teacher_forcing_metrics(model, examples)
        per_problem.append({"problem_id": row["problem_id"], **{k: v for k, v in metrics.items() if k != "rows"}})
        for item in metrics["rows"]:
            all_rows.append({**item, "problem_id": row["problem_id"]})

    def _mean(key):
        values = [r[key] for r in all_rows if r.get("valid") and r.get(key) is not None]
        return float(np.mean(values)) if values else float("nan")

    valid_rows = [r for r in all_rows if r.get("valid")]
    return {
        "n_problems": len(per_problem),
        "n_examples": len(all_rows),
        "n_valid": len(valid_rows),
        "valid_rate": float(len(valid_rows) / len(all_rows)) if all_rows else 0.0,
        "cross_entropy": _mean("ce"),
        "top1_accuracy": float(np.mean([float(r["top1"]) for r in valid_rows])) if valid_rows else float("nan"),
        "topk_accuracy": float(np.mean([float(r["topk"]) for r in valid_rows])) if valid_rows else float("nan"),
        "mean_true_symbol_rank": _mean("rank"),
        "mean_true_symbol_probability": _mean("true_probability"),
        "mean_policy_entropy": _mean("entropy"),
        "per_problem": per_problem,
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
    train_records: Sequence[dict[str, Any]],
    eval_records: Sequence[dict[str, Any]],
    steps: int,
    seed: int = 0,
    batch_size: int = 4,
    max_examples_per_problem: int = 32,
    include_frozen: bool = True,
    include_full: bool = True,
) -> dict[str, Any]:
    """Train exactly one Transformer block at a time (IOLE), plus frozen / full controls.

    All conditions share the same initial checkpoint, data order, seed and step
    budget, so differences are attributable to the trainable layer.
    """
    import gc

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
            train_info = train_policy_multi_problem(
                candidate,
                train_records,
                steps=steps,
                seed=seed,
                batch_size=batch_size,
                max_examples_per_problem=max_examples_per_problem,
            )
        metrics = evaluate_records(candidate, eval_records, max_examples_per_problem=max_examples_per_problem)
        results.append(
            {
                "condition": condition,
                "layers": layers,
                **param_info,
                **{k: v for k, v in metrics.items() if k != "per_problem"},
                "peak_memory_bytes": _peak_memory(candidate),
                "train": train_info,
            }
        )
        del candidate
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    del baseline
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    return {"results": results}


def _peak_memory(model: Any) -> int | None:
    if not torch.cuda.is_available() or str(getattr(model, "device", "cpu")) == "cpu":
        return None
    return int(torch.cuda.max_memory_allocated())
