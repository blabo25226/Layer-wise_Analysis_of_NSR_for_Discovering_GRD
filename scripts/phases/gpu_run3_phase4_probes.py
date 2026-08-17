"""GPU_RUN3 Phase 4: hidden states, linear probes, gradient norms, CKA."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from gpu_run3.architecture import inventory_ndformer, resolve_layer_module  # noqa: E402
from gpu_run3.cli import common_parser, dummy_phase_output, phase_budget, require_previous, write_phase_manifest  # noqa: E402
from gpu_run3.corpus import build_analysis_corpus  # noqa: E402
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


def parse_args():
    return common_parser("GPU_RUN3 Phase 4 probes / gradient / CKA").parse_args()


def _per_example(hidden, n_examples: int) -> np.ndarray:
    array = hidden.detach().float().cpu().numpy()
    if array.ndim == 3:
        array = array.mean(axis=1)
    if array.ndim == 1:
        array = array.reshape(1, -1)
    if array.shape[0] != n_examples:
        pooled = array.mean(axis=0, keepdims=True)
        array = np.repeat(pooled, n_examples, axis=0)
    return array.reshape(n_examples, -1)


def main() -> int:
    args = parse_args()
    require_python_310()
    config = load_gpu_run3_configs()
    run_dir = resolve_run_dir(args.run_id, config=config)
    out_dir = run_dir / "phase4"
    out_dir.mkdir(parents=True, exist_ok=True)
    if args.dry_run:
        dummy_phase_output(out_dir, 4, extra={"probe_tasks": ["next_symbol", "root_operator"]})
        print(f"Phase 4 dry-run: {out_dir}")
        return 0
    require_previous(run_dir, "phase0/preflight.json")
    seed_everything(args.seed)
    budget = phase_budget(config, smoke=args.smoke)
    paths = nd2_paths(config)
    device = select_device(allow_cpu=args.allow_cpu)
    model = load_ndformer(paths["checkpoint"], device=device)
    inventory = inventory_ndformer(model)
    layers = inventory["ranking_layers"]
    corpus = build_analysis_corpus(seed=args.seed, n_nodes=int(budget.get("n_nodes", 6)), n_edges=int(budget.get("n_edges", 10)))
    records = [row for row in corpus["records"] if row["split"] == "analysis_validation"]
    if args.smoke:
        records = records[:2]
    hidden_store = {name: [] for name in layers}
    next_symbols = []
    root_ops = []
    depths = []
    sizes = []
    network_op_counts = []
    for row in records:
        examples = [ex for ex in row["teacher_forcing"] if ex.get("target")]
        if not examples:
            continue
        model.set_data(Xv=row["Xv"], Xe=row["Xe"], A=row["A"], G=row["G"], Y=row["Y"], root_type=row["root_type"], cache_data_emb=False)
        prefixes = [ex["prefix"] for ex in examples]
        with capture_layer_outputs(model, layers) as captured:
            _ = model.get_policy(prefixes)
        for name in layers:
            hidden_store[name].append(_per_example(captured[name], len(examples)))
        for ex in examples:
            next_symbols.append(str(ex["target"]))
            root_ops.append(str((ex["prefix"] or ["empty"])[0]))
            depths.append(float(len(ex["prefix"])))
            sizes.append(float(len(row["prefix"])))
            network_op_counts.append(float(sum(tok in {"aggr", "sour", "targ"} for tok in row["prefix"])))
    hidden = {name: np.concatenate(chunks, axis=0) if chunks else np.zeros((0, 1)) for name, chunks in hidden_store.items()}
    min_n = min((arr.shape[0] for arr in hidden.values()), default=0)
    labels = {
        "next_symbol": np.array(next_symbols[:min_n]),
        "root_operator": np.array(root_ops[:min_n]),
        "tree_depth": np.array(depths[:min_n]),
        "tree_size": np.array(sizes[:min_n]),
        "network_op_count": np.array(network_op_counts[:min_n]),
    }
    probe_scores = {}
    for task, y in labels.items():
        probe_scores[task] = {}
        for name, h in hidden.items():
            h = h[: min_n]
            if h.size == 0 or len(y) == 0:
                probe_scores[task][name] = float("nan")
                continue
            if y.dtype.kind in {"U", "S", "O"}:
                probe_scores[task][name] = float(fit_linear_classifier_probe(h, y)["accuracy"])
            else:
                probe_scores[task][name] = float(fit_linear_probe(h, y)["r2"])
    cka = {}
    names = list(layers)
    for i, left in enumerate(names):
        for right in names[i:]:
            if hidden[left].size == 0:
                cka[f"{left}||{right}"] = float("nan")
                continue
            n = min(hidden[left].shape[0], hidden[right].shape[0])
            cka[f"{left}||{right}"] = float(linear_cka(hidden[left][:n], hidden[right][:n]))
    # Gradient norms on one validation batch.
    model.train()
    layer_grads = {}
    row = records[0]
    model.set_data(Xv=row["Xv"], Xe=row["Xe"], A=row["A"], G=row["G"], Y=row["Y"], root_type=row["root_type"], cache_data_emb=True)
    from gpu_run3.policy import policy_cross_entropy_loss

    example = next(ex for ex in row["teacher_forcing"] if ex.get("target"))
    loss = policy_cross_entropy_loss(model, [example["prefix"]], [example["target"]])
    loss.backward()
    for name in layers:
        module = resolve_layer_module(model, name)
        grads = [p.grad.detach().float().cpu().numpy().ravel() for p in module.parameters() if p.grad is not None]
        layer_grads[name] = np.concatenate(grads) if grads else np.zeros(1)
    grad_table = gradient_norms(layer_grads)
    param_counts = {name: int(sum(p.numel() for p in resolve_layer_module(model, name).parameters())) for name in layers}

    normalized = {name: float(grad_table[name] / max(param_counts[name], 1)) for name in layers}
    summary = {
        "phase": 4,
        "status": "complete",
        "provenance": "layer_analysis",
        "ranking_layers": layers,
        "probe_scores": probe_scores,
        "probe_rank_next_symbol": rank_from_scores(probe_scores.get("next_symbol", {}), higher_is_better=True),
        "cka": cka,
        "gradient_norm": grad_table,
        "gradient_norm_normalized": normalized,
        "gradient_rank": rank_from_scores(grad_table, higher_is_better=True),
        "n_examples": min_n,
    }
    write_json(out_dir / "summary.json", summary)
    write_phase_manifest(out_dir, summary)
    print(f"Phase 4 complete: {out_dir / 'summary.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
