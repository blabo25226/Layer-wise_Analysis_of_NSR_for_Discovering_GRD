"""GPU_RUN3 Phase 4: hidden states, linear probes, gradient norms, CKA.

Probes are fitted on ``analysis_train`` formulas and scored on the disjoint
``analysis_validation`` formulas, with a shuffled-label control fitted the same
way, so a high score cannot come from in-sample memorisation.
"""

from __future__ import annotations

import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from gpu_run3.architecture import inventory_ndformer, resolve_layer_module  # noqa: E402
from gpu_run3.cli import (  # noqa: E402
    common_parser,
    dummy_phase_output,
    phase_budget,
    require_previous,
    seed_bundles,
    write_phase_manifest,
)
from gpu_run3.corpus import build_analysis_corpus, corpus_kwargs_from_budget, select_fixed_panel  # noqa: E402
from gpu_run3.hooks import capture_layer_outputs  # noqa: E402
from gpu_run3.ranking import rank_from_scores  # noqa: E402
from gpu_run3_runtime import (  # noqa: E402
    load_gpu_run3_configs,
    load_ndformer,
    nd2_paths,
    require_python_310,
    resolve_run_dir,
    seed_everything,
    select_device,
    write_json,
)
from interpretability.cka import linear_cka  # noqa: E402
from interpretability.probes import fit_linear_classifier_probe, fit_linear_probe, gradient_norms  # noqa: E402

CLASSIFICATION_TASKS = {"next_symbol", "formula_root_operator"}


def parse_args():
    return common_parser("GPU_RUN3 Phase 4 probes / gradient / CKA").parse_args()


def _tree_depth(tree) -> int:
    if not tree:
        return 0
    _label, children = tree
    return 1 + max((_tree_depth(child) for child in children), default=0)


def _per_example(hidden, n_examples: int) -> np.ndarray:
    """Pool a captured activation to one row per teacher-forcing example.

    Encoder activations depend only on the problem's data, so they are pooled and
    broadcast; the resulting within-problem constancy is reported separately.
    """
    array = hidden.detach().float().cpu().numpy()
    if array.ndim == 3:
        array = array.mean(axis=1)
    if array.ndim == 1:
        array = array.reshape(1, -1)
    if array.shape[0] != n_examples:
        pooled = array.mean(axis=0, keepdims=True)
        array = np.repeat(pooled, n_examples, axis=0)
    return array.reshape(n_examples, -1)


def _collect(model, layers, records, max_examples: int):
    """Return per-layer feature matrices plus aligned label vectors."""
    store = {name: [] for name in layers}
    labels = defaultdict(list)
    problem_ids: list[str] = []
    for row in records:
        examples = [ex for ex in row["teacher_forcing"] if ex.get("target")][:max_examples]
        if not examples:
            continue
        model.set_data(
            Xv=row["Xv"],
            Xe=row["Xe"],
            A=row["A"],
            G=row["G"],
            Y=row["Y"],
            root_type=row["root_type"],
            cache_data_emb=False,
        )
        prefixes = [ex["prefix"] for ex in examples]
        with capture_layer_outputs(model, layers) as captured:
            _ = model.get_policy(prefixes)
        missing = [name for name in layers if name not in captured]
        if missing:
            raise RuntimeError(f"ActivationHookError: layers did not fire: {missing}")
        for name in layers:
            store[name].append(_per_example(captured[name], len(examples)))
        depth = _tree_depth(row.get("expression_tree"))
        n_net_ops = float(sum(tok in {"aggr", "rgga", "sour", "targ"} for tok in row["prefix"]))
        for ex in examples:
            labels["next_symbol"].append(str(ex["target"]))
            labels["formula_root_operator"].append(str((row["prefix"] or ["empty"])[0]))
            labels["partial_prefix_length"].append(float(len(ex["prefix"])))
            labels["tree_depth"].append(float(depth))
            labels["tree_size"].append(float(len(row["prefix"])))
            labels["network_op_count"].append(n_net_ops)
            problem_ids.append(row["problem_id"])
    features = {
        name: (np.concatenate(chunks, axis=0) if chunks else np.zeros((0, 1)))
        for name, chunks in store.items()
    }
    return features, {k: np.array(v) for k, v in labels.items()}, problem_ids


def _pool_by_problem(features: np.ndarray, problem_ids: list[str]) -> np.ndarray:
    """One row per problem, so encoder layers (constant within a problem) get real variance."""
    if features.size == 0 or not problem_ids:
        return np.zeros((0, 1))
    groups: dict[str, list[int]] = defaultdict(list)
    for index, pid in enumerate(problem_ids):
        groups[pid].append(index)
    return np.stack([features[idx].mean(axis=0) for _pid, idx in sorted(groups.items())], axis=0)


def _within_problem_variation(features: np.ndarray, problem_ids: list[str]) -> float:
    """Mean within-problem feature std divided by overall std (0 => constant per problem)."""
    if features.size == 0 or not problem_ids:
        return float("nan")
    overall = float(np.std(features))
    if overall <= 0:
        return 0.0
    groups = defaultdict(list)
    for index, pid in enumerate(problem_ids):
        groups[pid].append(index)
    stds = [float(np.std(features[idx], axis=0).mean()) for idx in groups.values() if len(idx) > 1]
    return float(np.mean(stds) / overall) if stds else float("nan")


PROBE_RIDGE_GRID = (1.0, 10.0, 100.0, 1000.0, 10000.0)


def _standardize(train_h: np.ndarray, eval_h: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Zero-mean / unit-variance using train statistics only.

    Raw NDformer activations differ by orders of magnitude across layers; without
    this the ridge solve is effectively unregularised and held-out R2 blows up to
    -1e13 instead of reporting a usable score.
    """
    mean = train_h.mean(axis=0, keepdims=True)
    std = train_h.std(axis=0, keepdims=True)
    std = np.where(std < 1e-8, 1.0, std)
    return (train_h - mean) / std, (eval_h - mean) / std


def _fit_and_score(task: str, train_h, train_y, eval_h, eval_y, ridge: float) -> float:
    if task in CLASSIFICATION_TASKS:
        return float(
            fit_linear_classifier_probe(train_h, train_y, ridge=ridge, eval_hidden=eval_h, eval_labels=eval_y)[
                "accuracy"
            ]
        )
    return float(fit_linear_probe(train_h, train_y, ridge=ridge, eval_hidden=eval_h, eval_targets=eval_y)["r2"])


def _select_ridge(task: str, train_z, train_y, train_groups: list[str]) -> float:
    """Choose the ridge on an inner split of analysis_train, never on the eval split.

    With 512-dimensional activations and a few hundred examples the solve is
    near-singular, so a fixed small ridge yields held-out R2 of order -1e13
    instead of a usable score.
    """
    unique = sorted(set(train_groups))
    if len(unique) < 4 or len(train_y) < 8:
        return PROBE_RIDGE_GRID[len(PROBE_RIDGE_GRID) // 2]
    holdout = set(unique[:: max(len(unique) // 3, 1)][:2] or unique[:1])
    inner_mask = np.array([g not in holdout for g in train_groups])
    if inner_mask.all() or not inner_mask.any():
        return PROBE_RIDGE_GRID[len(PROBE_RIDGE_GRID) // 2]
    inner_y = np.asarray(train_y)[inner_mask]
    outer_y = np.asarray(train_y)[~inner_mask]
    if task in CLASSIFICATION_TASKS:
        if len(set(inner_y.tolist())) < 2:
            return PROBE_RIDGE_GRID[len(PROBE_RIDGE_GRID) // 2]
    elif float(np.var(np.asarray(outer_y, dtype=np.float64))) < 1e-12:
        return PROBE_RIDGE_GRID[len(PROBE_RIDGE_GRID) // 2]
    best_ridge = PROBE_RIDGE_GRID[0]
    best_score = -np.inf
    for ridge in PROBE_RIDGE_GRID:
        try:
            score = _fit_and_score(task, train_z[inner_mask], inner_y, train_z[~inner_mask], outer_y, ridge)
        except Exception:
            continue
        if np.isfinite(score) and score > best_score:
            best_score = score
            best_ridge = ridge
    return best_ridge


def _score(task: str, train_h, train_y, eval_h, eval_y, train_groups: list[str] | None = None) -> tuple[float, float]:
    if train_h.size == 0 or eval_h.size == 0 or len(train_y) == 0 or len(eval_y) == 0:
        return float("nan"), float("nan")
    train_z, eval_z = _standardize(np.asarray(train_h, dtype=np.float64), np.asarray(eval_h, dtype=np.float64))
    if task not in CLASSIFICATION_TASKS and float(np.var(np.asarray(eval_y, dtype=np.float64))) < 1e-12:
        return float("nan"), float("nan")  # constant held-out target: R2 is undefined
    ridge = _select_ridge(task, train_z, train_y, list(train_groups or []))
    try:
        return _fit_and_score(task, train_z, train_y, eval_z, eval_y, ridge), ridge
    except Exception:
        return float("nan"), ridge


def main() -> int:
    args = parse_args()
    require_python_310()
    config = load_gpu_run3_configs()
    run_dir = resolve_run_dir(args.run_id, config=config)
    out_dir = run_dir / "phase4"
    out_dir.mkdir(parents=True, exist_ok=True)
    if args.dry_run:
        dummy_phase_output(out_dir, 4, extra={"probe_tasks": ["next_symbol", "formula_root_operator"]})
        print(f"Phase 4 dry-run: {out_dir}")
        return 0
    require_previous(run_dir, "phase0/preflight.json")
    budget = phase_budget(config, smoke=args.smoke)
    paths = nd2_paths(config)
    device = select_device(allow_cpu=args.allow_cpu)
    model = load_ndformer(paths["checkpoint"], device=device)
    inventory = inventory_ndformer(model)
    layers = inventory["ranking_layers"]
    corpus_kwargs = corpus_kwargs_from_budget(budget)
    max_examples = int(budget.get("probe_examples", 16))
    panel_n = int(budget.get("panel_problems", 2))

    per_seed = []
    probe_scores_seeds = defaultdict(lambda: defaultdict(list))
    control_scores_seeds = defaultdict(lambda: defaultdict(list))
    ridge_seeds = defaultdict(lambda: defaultdict(list))
    grad_seeds = defaultdict(list)
    cka_seeds = defaultdict(list)
    cka_problem_seeds = defaultdict(list)
    variation_seeds = defaultdict(list)

    for seed in seed_bundles(config, budget, base_seed=args.seed):
        seed_everything(seed)
        corpus = build_analysis_corpus(seed=seed, **corpus_kwargs)
        train_records = [r for r in corpus["records"] if r["split"] == "analysis_train"]
        val_records = [r for r in corpus["records"] if r["split"] == "analysis_validation"]
        if not train_records or not val_records:
            per_seed.append({"seed": seed, "status": "skipped", "failure_reason": "empty split"})
            continue
        train_features, train_labels, train_problem_ids = _collect(model, layers, train_records, max_examples)
        val_features, val_labels, val_problem_ids = _collect(model, layers, val_records, max_examples)

        rng = np.random.default_rng(seed)
        for task, y_train in train_labels.items():
            y_val = val_labels[task]
            for name in layers:
                score, ridge = _score(
                    task, train_features[name], y_train, val_features[name], y_val, train_problem_ids
                )
                shuffled = y_train.copy()
                rng.shuffle(shuffled)
                control, _ = _score(
                    task, train_features[name], shuffled, val_features[name], y_val, train_problem_ids
                )
                probe_scores_seeds[task][name].append(score)
                control_scores_seeds[task][name].append(control)
                ridge_seeds[task][name].append(ridge)
        for name in layers:
            variation_seeds[name].append(_within_problem_variation(val_features[name], val_problem_ids))
        pooled = {name: _pool_by_problem(val_features[name], val_problem_ids) for name in layers}
        for i, left in enumerate(layers):
            for right in layers[i:]:
                key = f"{left}||{right}"
                n = min(val_features[left].shape[0], val_features[right].shape[0])
                cka_seeds[key].append(
                    float(linear_cka(val_features[left][:n], val_features[right][:n])) if n else float("nan")
                )
                m = min(pooled[left].shape[0], pooled[right].shape[0])
                cka_problem_seeds[key].append(
                    float(linear_cka(pooled[left][:m], pooled[right][:m])) if m > 1 else float("nan")
                )

        # Gradient norms over a fixed validation panel, accumulated then averaged.
        from gpu_run3.policy import policy_cross_entropy_loss

        panel = select_fixed_panel(corpus["records"], split="analysis_validation", n=panel_n)
        model.train()
        model.zero_grad(set_to_none=True)
        n_batches = 0
        for row in panel:
            examples = [ex for ex in row["teacher_forcing"] if ex.get("target")][:max_examples]
            if not examples:
                continue
            model.set_data(
                Xv=row["Xv"],
                Xe=row["Xe"],
                A=row["A"],
                G=row["G"],
                Y=row["Y"],
                root_type=row["root_type"],
                cache_data_emb=True,
            )
            loss = policy_cross_entropy_loss(
                model,
                [list(ex["prefix"]) for ex in examples],
                [str(ex["target"]) for ex in examples],
            )
            loss.backward()
            n_batches += 1
        layer_grads = {}
        for name in layers:
            module = resolve_layer_module(model, name)
            grads = [p.grad.detach().float().cpu().numpy().ravel() for p in module.parameters() if p.grad is not None]
            layer_grads[name] = np.concatenate(grads) / max(n_batches, 1) if grads else np.zeros(1)
        for name, value in gradient_norms(layer_grads).items():
            grad_seeds[name].append(value)
        model.zero_grad(set_to_none=True)
        model.eval()
        per_seed.append(
            {
                "seed": seed,
                "status": "complete",
                "n_train_problems": len(train_records),
                "n_val_problems": len(val_records),
                "n_train_examples": int(len(train_labels["next_symbol"])),
                "n_val_examples": int(len(val_labels["next_symbol"])),
                "n_gradient_batches": n_batches,
            }
        )

    def _avg(values):
        finite = [float(v) for v in values if v is not None and np.isfinite(v)]
        return float(np.mean(finite)) if finite else float("nan")

    probe_scores = {task: {name: _avg(v) for name, v in per_layer.items()} for task, per_layer in probe_scores_seeds.items()}
    control_scores = {task: {name: _avg(v) for name, v in per_layer.items()} for task, per_layer in control_scores_seeds.items()}
    probe_minus_control = {
        task: {name: probe_scores[task][name] - control_scores[task][name] for name in probe_scores[task]}
        for task in probe_scores
    }
    grad_table = {name: _avg(values) for name, values in grad_seeds.items()}
    param_counts = {name: int(sum(p.numel() for p in resolve_layer_module(model, name).parameters())) for name in layers}
    normalized = {name: float(grad_table.get(name, float("nan")) / max(param_counts[name], 1)) for name in layers}

    summary = {
        "phase": 4,
        "status": "complete",
        "provenance": "layer_analysis",
        "seeds": [item["seed"] for item in per_seed],
        "per_seed": per_seed,
        "ranking_layers": layers,
        "probe_fit_split": "analysis_train",
        "probe_eval_split": "analysis_validation",
        "probe_scores": probe_scores,
        "probe_control_scores": control_scores,
        "probe_ridge_selected": {
            task: {name: _avg(v) for name, v in per_layer.items()} for task, per_layer in ridge_seeds.items()
        },
        "probe_ridge_grid": list(PROBE_RIDGE_GRID),
        "probe_ridge_selection": "inner split of analysis_train, by problem",
        "probe_minus_control": probe_minus_control,
        "probe_rank_next_symbol": rank_from_scores(probe_minus_control.get("next_symbol", {}), higher_is_better=True),
        "within_problem_feature_variation": {name: _avg(v) for name, v in variation_seeds.items()},
        "cka": {key: _avg(v) for key, v in cka_seeds.items()},
        "cka_problem_level": {key: _avg(v) for key, v in cka_problem_seeds.items()},
        "gradient_norm": grad_table,
        "gradient_norm_normalized": normalized,
        "parameter_counts": param_counts,
        "gradient_rank": rank_from_scores(grad_table, higher_is_better=True),
        "note": (
            "Encoder activations do not depend on the decoded prefix, so their "
            "within_problem_feature_variation is ~0 and example-level tasks such as "
            "next_symbol are only informative for decoder blocks."
        ),
    }
    write_json(out_dir / "summary.json", summary)
    write_phase_manifest(out_dir, {k: v for k, v in summary.items() if k != "cka"})
    print(f"Phase 4 complete: {out_dir / 'summary.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
