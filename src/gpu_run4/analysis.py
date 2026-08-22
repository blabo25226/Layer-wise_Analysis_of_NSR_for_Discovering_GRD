"""Observational layer analysis: probes, gradient norms, CKA, rankings."""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Sequence

import numpy as np

from gpu_run4.architecture import unwrap_model
from gpu_run4.hooks import capture_layer_outputs
from gpu_run4.training import teacher_forcing_loss, _point_bag
from interpretability.cka import linear_cka
from interpretability.probes import fit_linear_classifier_probe, fit_linear_probe


def _pool(hidden: torch.Tensor) -> np.ndarray:
    array = hidden.detach().float().cpu().numpy()
    if array.ndim == 3:
        array = array.mean(axis=1)
    if array.ndim == 1:
        array = array.reshape(1, -1)
    return array.reshape(array.shape[0], -1)


def collect_encoder_features(model: Any, records: Sequence[dict[str, Any]], layers: Sequence[str]) -> dict[str, Any]:
    wrapped = unwrap_model(model)
    embedder = wrapped.embedder
    encoder = wrapped.encoder
    store = {name: [] for name in layers}
    labels = defaultdict(list)
    for row in records:
        bag = _point_bag(row["times"], row["trajectory"])
        x, x_len = embedder([bag])
        with capture_layer_outputs(wrapped, list(layers)) as captured:
            _ = encoder("fwd", x=x, lengths=x_len, causal=False)
            for name in layers:
                if name.startswith("encoder_") and name in captured:
                    store[name].append(_pool(captured[name])[0])
        labels["dimension"].append(int(row.get("dimension") or np.asarray(row["trajectory"]).shape[1]))
        labels["complexity"].append(float(row.get("complexity") or 0))
        infix = str(row.get("infix") or "")
        labels["has_sin"].append(1.0 if "sin" in infix else 0.0)
        labels["has_inv"].append(1.0 if ("inv" in infix or "/" in infix) else 0.0)
    features = {
        name: np.stack(rows) if rows else np.zeros((0, 1))
        for name, rows in store.items()
        if name.startswith("encoder_")
    }
    return {"features": features, "labels": {k: np.asarray(v) for k, v in labels.items()}}


def probe_layers(
    train: dict[str, Any],
    val: dict[str, Any],
    *,
    tasks: Sequence[str] = ("dimension", "complexity", "has_sin"),
) -> dict[str, Any]:
    results: dict[str, Any] = {}
    for layer, h_train in train["features"].items():
        h_val = val["features"].get(layer)
        if h_val is None or len(h_train) < 2 or len(h_val) < 2:
            continue
        layer_rows = {}
        for task in tasks:
            y_train = train["labels"][task]
            y_val = val["labels"][task]
            rng = np.random.default_rng(0)
            y_perm = rng.permutation(y_train)
            if task in {"dimension", "has_sin", "has_inv"}:
                fit = fit_linear_classifier_probe(h_train, y_train, eval_hidden=h_val, eval_labels=y_val)
                control = fit_linear_classifier_probe(h_train, y_perm, eval_hidden=h_val, eval_labels=y_val)
                score_key = "accuracy"
            else:
                fit = fit_linear_probe(h_train, y_train, eval_hidden=h_val, eval_targets=y_val)
                control = fit_linear_probe(h_train, y_perm, eval_hidden=h_val, eval_targets=y_val)
                score_key = "r2"
            layer_rows[task] = {"probe": fit, "control": control, "score_key": score_key}
        results[layer] = layer_rows
    return results


def cka_matrix(features: dict[str, np.ndarray], layer_names: Sequence[str]) -> list[list[float]]:
    matrix = []
    for left in layer_names:
        row = []
        for right in layer_names:
            a, b = features.get(left), features.get(right)
            if a is None or b is None or len(a) < 2:
                row.append(float("nan"))
            else:
                row.append(linear_cka(a, b))
        matrix.append(row)
    return matrix


def gradient_by_layer(model: Any, records: Sequence[dict[str, Any]], layers: Sequence[str]) -> dict[str, float]:
    wrapped = unwrap_model(model)
    wrapped.train()
    usable = [row for row in records if row.get("tree_encoded") is not None][:8]
    if not usable:
        wrapped.eval()
        return {name: float("nan") for name in layers}
    wrapped.zero_grad(set_to_none=True)
    loss = teacher_forcing_loss(wrapped, usable[0]["times"], usable[0]["trajectory"], usable[0]["tree_encoded"])
    loss.backward()
    from gpu_run4.architecture import ranking_block_modules

    scores = {}
    for name in layers:
        parts = ranking_block_modules(wrapped, name)
        total = 0.0
        n_params = 0
        for module in parts.values():
            if module is None:
                continue
            for parameter in module.parameters():
                n_params += parameter.numel()
                if parameter.grad is not None:
                    total += float(parameter.grad.detach().float().norm().cpu() ** 2)
        scores[name] = float(np.sqrt(total) / max(n_params, 1))
    wrapped.zero_grad(set_to_none=True)
    wrapped.eval()
    return scores


def probe_score_map(probe_results: dict[str, Any], task: str) -> dict[str, float]:
    out = {}
    for layer, tasks in probe_results.items():
        payload = tasks.get(task) or {}
        probe = payload.get("probe") or {}
        key = str(payload.get("score_key") or "r2")
        out[layer] = float(probe.get(key, probe.get("accuracy", probe.get("r2", float("nan")))))
    return out
