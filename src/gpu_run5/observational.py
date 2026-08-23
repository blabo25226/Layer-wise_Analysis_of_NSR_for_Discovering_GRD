"""Observational encoder/decoder analyses for the released ODEFormer."""

from __future__ import annotations

from collections import Counter
from typing import Any, Sequence

import numpy as np
import torch

from evaluation.gpu_run5_structure import classify_formula
from gpu_run4.architecture import ranking_block_modules, unwrap_model
from gpu_run4.formulas import parse_system
from gpu_run4.hooks import capture_layer_outputs
from gpu_run4.training import _point_bag, teacher_forcing_loss
from gpu_run4_runtime import candidate_infix
from gpu_run5.evaluation import formula_metrics
from interpretability.cka import linear_cka
from interpretability.probes import fit_linear_classifier_probe, fit_linear_probe


STRUCTURE_TASKS = (
    "variable_denominator_form", "algebraically_rational", "hill_form",
    "modulated_hill_form", "sigmoid_saturating_form",
)


def token_category(token: str) -> str:
    value = str(token)
    if value.startswith("x_"):
        return "variable"
    if value == "inv":
        return "inv"
    if value in {"pow", "pow2", "pow3"}:
        return "integer_power"
    if value == "mul":
        return "multiplication"
    if value in {"add", "sub"}:
        return "addition"
    if value == "<EOS>":
        return "eos"
    if value == "<PAD>":
        return "padding"
    if value == "|":
        return "separator"
    try:
        float(value)
        return "constant"
    except ValueError:
        pass
    if value.startswith(("N", "E", "INT", "+", "-")) or value.isdigit():
        return "constant"
    return "other_operator"


def _tree_depth(tree: Any) -> int:
    if tree is None:
        return 0
    return 1 + max((_tree_depth(child) for child in tree[1]), default=0)


def formula_depth(infix: str) -> float:
    parsed = parse_system(infix)
    return float(max((_tree_depth(tree) for tree in parsed["components"]), default=0))


def _pool_sequence(hidden: torch.Tensor) -> np.ndarray:
    value = hidden.detach().float()
    if value.ndim == 3:
        value = value[0, :, :].mean(dim=0)
    elif value.ndim == 2:
        value = value.mean(dim=0)
    return value.cpu().numpy().reshape(-1)


@torch.no_grad()
def collect_layer_features(
    model: Any,
    records: Sequence[dict[str, Any]],
    layers: Sequence[str],
    *,
    max_tokens_per_formula: int = 4,
) -> dict[str, Any]:
    """Collect expression pools and formula-split token samples from every block."""
    wrapped = unwrap_model(model)
    expression = {layer: [] for layer in layers}
    token_features = {layer: [] for layer in layers if layer.startswith("decoder_")}
    expression_labels: dict[str, list[Any]] = {
        "dimension": [], "complexity": [], "tree_depth": [], **{task: [] for task in STRUCTURE_TASKS}
    }
    token_labels: dict[str, list[Any]] = {
        "next_token": [], "token_category": [], "tree_depth": [], "formula_id": [],
        **{task: [] for task in STRUCTURE_TASKS},
    }
    failures = []
    for row in records:
        try:
            times = np.asarray(row["times"], dtype=float)
            trajectory = np.asarray(row["trajectory"], dtype=float)
            x1, len1 = wrapped.embedder([_point_bag(times, trajectory)])
            x2, len2 = wrapped.env.batch_equations(
                wrapped.env.word_to_idx([list(row["tree_encoded"])], float_input=False)
            )
            device = next(wrapped.parameters()).device
            x2, len2 = x2.to(device), len2.to(device)
            with capture_layer_outputs(wrapped, list(layers)) as captured:
                encoded = wrapped.encoder("fwd", x=x1, lengths=len1, causal=False)
                _ = wrapped.decoder(
                    "fwd", x=x2, lengths=len2, causal=True,
                    src_enc=encoded.transpose(0, 1), src_len=len1,
                )
            structure = classify_formula(row["infix"])
            labels = {
                "dimension": int(row["dimension"]), "complexity": float(row.get("complexity") or 0),
                "tree_depth": formula_depth(row["infix"]),
                **{task: int(bool(structure.get(task))) for task in STRUCTURE_TASKS},
            }
            for key, value in labels.items():
                expression_labels[key].append(value)
            n_targets = max(int(len2[0].item()) - 1, 0)
            positions = (
                np.unique(np.linspace(0, n_targets - 1, min(max_tokens_per_formula, n_targets), dtype=int))
                if n_targets else np.asarray([], dtype=int)
            )
            target_ids = x2[1 : n_targets + 1, 0].detach().cpu().tolist()
            target_tokens = [wrapped.env.equation_id2word.get(int(value), str(int(value))) for value in target_ids]
            for layer in layers:
                hidden = captured.get(layer)
                if hidden is None:
                    raise RuntimeError(f"missing captured layer {layer}")
                expression[layer].append(_pool_sequence(hidden))
                if layer.startswith("decoder_"):
                    token_features[layer].extend(
                        hidden[0, int(position)].detach().float().cpu().numpy() for position in positions
                    )
            for position in positions:
                token = target_tokens[int(position)]
                token_labels["next_token"].append(token)
                token_labels["token_category"].append(token_category(token))
                token_labels["tree_depth"].append(labels["tree_depth"])
                token_labels["formula_id"].append(str(row["problem_id"]))
                for task in STRUCTURE_TASKS:
                    token_labels[task].append(labels[task])
        except Exception as exc:
            failures.append({"problem_id": row.get("problem_id"), "reason": f"{type(exc).__name__}:{exc}"})
    return {
        "expression_features": {key: np.asarray(value, dtype=np.float32) for key, value in expression.items()},
        "token_features": {key: np.asarray(value, dtype=np.float32) for key, value in token_features.items()},
        "expression_labels": {key: np.asarray(value) for key, value in expression_labels.items()},
        "token_labels": {key: np.asarray(value) for key, value in token_labels.items()},
        "failures": failures,
    }


def _top_token_mapping(labels: np.ndarray, n: int = 20) -> dict[str, str]:
    keep = {value for value, _ in Counter(str(item) for item in labels).most_common(n)}
    return {str(value): str(value) if str(value) in keep else "<OTHER_TOKEN>" for value in labels}


def _ridge_factor(hidden: np.ndarray, ridge: float = 1e-4):
    from scipy.linalg import cho_factor

    matrix = np.asarray(hidden, dtype=np.float64)
    gram = matrix.T @ matrix + float(ridge) * np.eye(matrix.shape[1])
    return matrix, cho_factor(gram, check_finite=False)


def _factored_classifier(
    train_hidden: np.ndarray,
    factor: Any,
    train_labels: np.ndarray,
    validation_hidden: np.ndarray,
    validation_labels: np.ndarray,
) -> dict[str, float]:
    from scipy.linalg import cho_solve

    encoded = np.asarray([str(value) for value in train_labels])
    classes, inverse = np.unique(encoded, return_inverse=True)
    if len(classes) < 2:
        return {"accuracy": None, "majority_baseline": 1.0, "n_classes": float(len(classes))}
    target = np.full((len(encoded), len(classes)), -1.0, dtype=np.float64)
    target[np.arange(len(encoded)), inverse] = 1.0
    weights = cho_solve(factor, train_hidden.T @ target, check_finite=False)
    scores = np.asarray(validation_hidden, dtype=np.float64) @ weights
    mapping = {value: index for index, value in enumerate(classes)}
    expected = np.asarray([mapping.get(str(value), -1) for value in validation_labels])
    counts = np.bincount(inverse, minlength=len(classes))
    return {
        "accuracy": float(np.mean(scores.argmax(axis=1) == expected)),
        "majority_baseline": float(np.max(counts) / len(encoded)),
        "n_classes": float(len(classes)), "n_examples": float(len(validation_labels)),
        "n_train_examples": float(len(encoded)), "n_features": float(train_hidden.shape[1]),
    }


def _factored_regression(
    train_hidden: np.ndarray,
    factor: Any,
    train_targets: np.ndarray,
    validation_hidden: np.ndarray,
    validation_targets: np.ndarray,
) -> dict[str, float]:
    from scipy.linalg import cho_solve

    target = np.asarray(train_targets, dtype=np.float64)
    weights = cho_solve(factor, train_hidden.T @ target, check_finite=False)
    predicted = np.asarray(validation_hidden, dtype=np.float64) @ weights
    truth = np.asarray(validation_targets, dtype=np.float64)
    residual = truth - predicted
    denom = float(np.sum((truth - np.mean(truth)) ** 2)) + 1e-12
    return {
        "mse": float(np.mean(residual**2)), "nmse_var": float(np.sum(residual**2) / denom),
        "r2": 1.0 - float(np.sum(residual**2) / denom),
        "n_examples": float(len(truth)), "n_train_examples": float(len(target)),
        "n_features": float(train_hidden.shape[1]),
    }


def fit_layer_probes(train: dict[str, Any], validation: dict[str, Any]) -> dict[str, Any]:
    """Fit real and label-shuffle controls using disjoint formula splits."""
    results: dict[str, Any] = {"encoder_expression": {}, "decoder_expression": {}, "decoder_token": {}}
    rng = np.random.default_rng(1701)
    expression_tasks = ("dimension", "complexity", "tree_depth", *STRUCTURE_TASKS)
    for layer, train_hidden in train["expression_features"].items():
        val_hidden = validation["expression_features"][layer]
        destination = results["encoder_expression" if layer.startswith("encoder_") else "decoder_expression"]
        destination[layer] = {}
        for task in expression_tasks:
            y_train, y_val = train["expression_labels"][task], validation["expression_labels"][task]
            shuffled = rng.permutation(y_train)
            if task in {"complexity", "tree_depth"}:
                probe = fit_linear_probe(train_hidden, y_train, eval_hidden=val_hidden, eval_targets=y_val)
                control = fit_linear_probe(train_hidden, shuffled, eval_hidden=val_hidden, eval_targets=y_val)
                score = "r2"
            else:
                probe = fit_linear_classifier_probe(train_hidden, y_train, eval_hidden=val_hidden, eval_labels=y_val)
                control = fit_linear_classifier_probe(train_hidden, shuffled, eval_hidden=val_hidden, eval_labels=y_val)
                score = "accuracy"
            destination[layer][task] = {"probe": probe, "label_shuffle_control": control, "score": score}
    mapping = _top_token_mapping(train["token_labels"]["next_token"])
    token_tasks = ("next_token", "token_category", "tree_depth", *STRUCTURE_TASKS)
    for layer, train_hidden in train["token_features"].items():
        val_hidden = validation["token_features"][layer]
        train_matrix, factor = _ridge_factor(train_hidden)
        results["decoder_token"][layer] = {}
        for task in token_tasks:
            y_train = train["token_labels"][task]
            y_val = validation["token_labels"][task]
            if task == "next_token":
                y_train = np.asarray([mapping.get(str(value), "<OTHER_TOKEN>") for value in y_train])
                y_val = np.asarray([mapping.get(str(value), "<OTHER_TOKEN>") for value in y_val])
            shuffled = rng.permutation(y_train)
            if task == "tree_depth":
                probe = _factored_regression(train_matrix, factor, y_train, val_hidden, y_val)
                control = _factored_regression(train_matrix, factor, shuffled, val_hidden, y_val)
                score = "r2"
            else:
                probe = _factored_classifier(train_matrix, factor, y_train, val_hidden, y_val)
                control = _factored_classifier(train_matrix, factor, shuffled, val_hidden, y_val)
                score = "accuracy"
            results["decoder_token"][layer][task] = {"probe": probe, "label_shuffle_control": control, "score": score}
    results["next_token_label_policy"] = "20 most frequent train tokens plus <OTHER_TOKEN>"
    results["formula_split_enforced"] = True
    return results


def within_module_cka(features: dict[str, np.ndarray], layers: Sequence[str]) -> list[list[float | None]]:
    matrix = []
    for left in layers:
        row = []
        for right in layers:
            try:
                value = float(linear_cka(features[left], features[right]))
                row.append(value if np.isfinite(value) else None)
            except Exception:
                row.append(None)
        matrix.append(row)
    return matrix


def gradient_norms_by_layer(model: Any, records: Sequence[dict[str, Any]], layers: Sequence[str]) -> dict[str, Any]:
    wrapped = unwrap_model(model)
    wrapped.train()
    wrapped.zero_grad(set_to_none=True)
    usable = [row for row in records if row.get("tree_encoded")][:8]
    losses = []
    for row in usable:
        loss = teacher_forcing_loss(
            wrapped, np.asarray(row["times"]), np.asarray(row["trajectory"]), row["tree_encoded"]
        ) / max(len(usable), 1)
        loss.backward()
        losses.append(float(loss.detach().cpu()) * max(len(usable), 1))
    output = {}
    for layer in layers:
        squared, n_params = 0.0, 0
        seen = set()
        for module in ranking_block_modules(wrapped, layer).values():
            if module is None:
                continue
            for parameter in module.parameters():
                if id(parameter) in seen:
                    continue
                seen.add(id(parameter))
                n_params += parameter.numel()
                if parameter.grad is not None:
                    squared += float(parameter.grad.detach().float().pow(2).sum().cpu())
        raw = float(np.sqrt(squared))
        output[layer] = {
            "raw_l2": raw, "per_sqrt_parameter": raw / np.sqrt(max(n_params, 1)),
            "n_parameters": n_params,
        }
    wrapped.zero_grad(set_to_none=True)
    wrapped.eval()
    return {"layers": output, "losses": losses, "n_records": len(usable)}


@torch.no_grad()
def decoder_logit_lens(
    model: Any, records: Sequence[dict[str, Any]], decoder_layers: Sequence[str]
) -> dict[str, Any]:
    wrapped = unwrap_model(model)
    token_rows, formula_rows, failures = [], [], []
    for row in records:
        try:
            x1, len1 = wrapped.embedder([
                _point_bag(np.asarray(row["times"]), np.asarray(row["trajectory"]))
            ])
            x2, len2 = wrapped.env.batch_equations(
                wrapped.env.word_to_idx([list(row["tree_encoded"])], float_input=False)
            )
            device = next(wrapped.parameters()).device
            x2, len2 = x2.to(device), len2.to(device)
            with capture_layer_outputs(wrapped, list(decoder_layers)) as captured:
                encoded = wrapped.encoder("fwd", x=x1, lengths=len1, causal=False)
                _ = wrapped.decoder(
                    "fwd", x=x2, lengths=len2, causal=True,
                    src_enc=encoded.transpose(0, 1), src_len=len1,
                )
            n_targets = int(len2[0].item()) - 1
            targets = x2[1 : n_targets + 1, 0].long()
            for layer in decoder_layers:
                hidden = captured[layer][0, :n_targets]
                logits = wrapped.decoder.proj(hidden)
                ranks = 1 + (logits > logits.gather(1, targets[:, None])).sum(dim=1)
                predicted = logits.argmax(dim=1).detach().cpu().tolist()
                target_ids = targets.detach().cpu().tolist()
                for position, (target, prediction, rank) in enumerate(
                    zip(target_ids, predicted, ranks.detach().cpu().tolist())
                ):
                    target_token = wrapped.env.equation_id2word.get(int(target), str(target))
                    token_rows.append({
                        "problem_id": row["problem_id"], "layer": layer, "position": position,
                        "target_token": target_token, "target_category": token_category(target_token),
                        "predicted_token": wrapped.env.equation_id2word.get(int(prediction), str(prediction)),
                        "target_rank": int(rank),
                    })
                try:
                    predicted_tokens = [
                        wrapped.env.equation_id2word.get(int(value), str(value))
                        for value in predicted
                        if wrapped.env.equation_id2word.get(int(value), str(value)) not in {"<EOS>", "<PAD>"}
                    ]
                    prediction_tree = wrapped.env.equation_encoder.decode(predicted_tokens)
                    prediction = candidate_infix(prediction_tree) or ""
                    metrics = formula_metrics(row["infix"], prediction)
                except Exception as exc:
                    prediction = ""
                    metrics = {"valid": False, "failure_reason": f"{type(exc).__name__}:{exc}"}
                formula_rows.append({
                    "problem_id": row["problem_id"], "layer": layer,
                    "readout": "teacher_forced_intermediate_hidden_to_final_projection",
                    "prediction": prediction, **metrics,
                })
        except Exception as exc:
            failures.append({"problem_id": row.get("problem_id"), "reason": f"{type(exc).__name__}:{exc}"})
    return {"token_rows": token_rows, "formula_rows": formula_rows, "failures": failures}


@torch.no_grad()
def encoder_intermediate_greedy(
    model: Any, records: Sequence[dict[str, Any]], encoder_layers: Sequence[str]
) -> dict[str, Any]:
    """Decode post-block memories directly; ODEFormer has no PMA/outatt."""
    wrapped = unwrap_model(model)
    output, failures = [], []
    for row in records:
        try:
            x1, len1 = wrapped.embedder([
                _point_bag(np.asarray(row["times"]), np.asarray(row["trajectory"]))
            ])
            with capture_layer_outputs(wrapped, list(encoder_layers)) as captured:
                _ = wrapped.encoder("fwd", x=x1, lengths=len1, causal=False)
            for layer in encoder_layers:
                memory = captured[layer]
                generated, _, masks = wrapped.decoder.generate(
                    memory, len1, sample_temperature=None,
                    max_len=wrapped.max_generated_output_len, env=wrapped.env,
                    seed=int(getattr(wrapped, "generation_seed", 0)),
                )
                ids = generated[:, 0].detach().cpu().tolist()[1:-1]
                mask = masks[:, 0].detach().cpu().tolist()[1:-1]
                tree = wrapped.env.idx_to_infix(
                    ids, is_float=False, str_array=False, is_two_hot=mask
                )
                prediction = candidate_infix(tree) or ""
                output.append({
                    "problem_id": row["problem_id"], "layer": layer,
                    "prediction": prediction,
                    "distribution_shift": "intermediate encoder state supplied directly to decoder trained on final state",
                    **formula_metrics(row["infix"], prediction),
                })
        except Exception as exc:
            failures.append({"problem_id": row.get("problem_id"), "reason": f"{type(exc).__name__}:{exc}"})
    return {
        "rows": output, "failures": failures, "pma_used": False,
        "reason": "ODEFormer encoder is a sequence Transformer and exposes no PMA/outatt",
    }
