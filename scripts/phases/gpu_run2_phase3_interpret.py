"""GPU_RUN2 Phase 3: validation probing, CKA, and DecoderLens."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "third_party" / "nesymres"))

from evaluation.layer_contribution import freeze_candidate_layers, rank_agreement_table  # noqa: E402
from evaluation.reproduction_bias import corpus_fingerprint  # noqa: E402
from data.gnw_synthetic import load_problem_npz  # noqa: E402
from gpu_run2_experiment import (  # noqa: E402
    build_finetune_loader,
    collect_layer_representations,
    filter_index_rows,
    finetune_hparams,
    gt_token_ids_for_row,
    iter_seed_noise,
    layer_gradient_norms_from_loader,
    load_nesymres_gpu_run2,
    load_phase1_index,
    require_nesymres_checkpoint,
    selectable_layer_names,
)
from gpu_run2_runtime import (  # noqa: E402
    graphs_dir,
    load_gpu_run2_configs,
    resolve_run_dir,
    utc_now,
    write_json,
)
from interpretability.cka import linear_cka  # noqa: E402
from interpretability.decoder_lens import (  # noqa: E402
    run_decoder_lens,
    write_decoder_lens_rank_heatmap,
)
from interpretability.probes import (  # noqa: E402
    expression_structure_attributes,
    fit_linear_classifier_probe,
    fit_linear_probe,
    gradient_norms,
    mean_rank_layer_scores,
    ranking_from_mean_rank,
)

CANDIDATE_SELECTION_METRICS = {
    "template_accuracy": True,
    "next_token_accuracy": True,
    "n_operators_r2": True,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="GPU_RUN2 Phase 3 interpretability")
    parser.add_argument("--run-id", default=os.environ.get("LANSR_RUN_ID"))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--candidate-k", type=int, default=5)
    return parser.parse_args()


def _placeholder_layers(n_encoder: int = 5, n_decoder: int = 5) -> list[str]:
    return [f"encoder_{i}" for i in range(n_encoder)] + [f"decoder_{i}" for i in range(n_decoder)]


def _dummy_structure_probes(layers: list[str]) -> dict[str, dict[str, float]]:
    rng = np.random.default_rng(0)
    dummy_hidden = rng.normal(size=(32, 16))
    dummy_base = rng.normal(size=(32, 16))
    template_labels = np.array(["T01_basal", "T02_single_regulator", "T04_two_independent_activators", "T07_two_module_mixture"] * 8)
    next_tokens = rng.integers(2, 12, size=32)
    n_ops = rng.integers(1, 6, size=32).astype(np.float64)
    template_acc = {}
    next_token_acc = {}
    n_ops_r2 = {}
    cka_scores = {}
    for name in layers:
        hidden = dummy_hidden + 0.05 * rng.normal(size=dummy_hidden.shape)
        template_acc[name] = fit_linear_classifier_probe(hidden, template_labels)["accuracy"]
        next_token_acc[name] = fit_linear_classifier_probe(hidden, next_tokens)["accuracy"]
        n_ops_r2[name] = fit_linear_probe(hidden, n_ops)["r2"]
        cka_scores[name] = linear_cka(dummy_base, hidden)
    grads = gradient_norms({name: rng.normal(size=8) for name in layers})
    return {
        "template_accuracy": template_acc,
        "next_token_accuracy": next_token_acc,
        "n_operators_r2": n_ops_r2,
        "cka": cka_scores,
        "gradient_norms": grads,
    }


def _labels_for_eq_ids(eq_ids: list[str], catalogue_by_id: dict[str, dict]) -> tuple[list[str], np.ndarray, np.ndarray]:
    template_ids = []
    n_operators = []
    n_variables = []
    for eq_id in eq_ids:
        row = catalogue_by_id.get(eq_id, {})
        template_id = row.get("template_id")
        family_id = row.get("family_id")
        if not template_id:
            raise KeyError(f"catalogue row {eq_id!r} missing template_id")
        if str(template_id) == str(family_id):
            raise ValueError(
                f"template_id must be an algebraic template, not family_id, for {eq_id}: {template_id}"
            )
        template_ids.append(str(template_id))
        attrs = expression_structure_attributes(
            str(row.get("canonical_expr") or ""),
            variable_names=list(row.get("oracle_inputs") or []),
        )
        n_operators.append(attrs["n_operators"])
        n_variables.append(attrs["n_variables"])
    return template_ids, np.asarray(n_operators, dtype=np.float64), np.asarray(n_variables, dtype=np.float64)


def main() -> int:
    args = parse_args()
    config = load_gpu_run2_configs()
    run_dir = resolve_run_dir(args.run_id, config=config)
    phase1 = run_dir / "phase1"
    out_dir = run_dir / "phase3"
    out_dir.mkdir(parents=True, exist_ok=True)
    splits = json.loads((phase1 / "splits.json").read_text(encoding="utf-8"))
    catalogue = json.loads((phase1 / "catalogue.json").read_text(encoding="utf-8"))
    index = load_phase1_index(phase1)
    val_ids = list(splits["main"]["validation"])
    if args.smoke:
        val_ids = val_ids[:4]
    val_specs = [row for row in catalogue if row["eq_id"] in set(val_ids)]
    catalogue_by_id = {row["eq_id"]: row for row in catalogue}
    train_templates = [row["canonical_expr"] for row in catalogue if row["main_split"] == "train"]
    corpus = corpus_fingerprint(train_templates)
    write_json(out_dir / "finetune_corpus_fingerprint.json", corpus)

    if args.dry_run:
        layers = _placeholder_layers(int(config.get("encoder_layers", 5)))
        dummy = _dummy_structure_probes(layers)
        template_acc = dummy["template_accuracy"]
        next_token_acc = dummy["next_token_accuracy"]
        n_ops_r2 = dummy["n_operators_r2"]
        cka_scores = dummy["cka"]
        grads = dummy["gradient_norms"]
        decoder_lens_rows = []
        for spec in val_specs:
            for layer in range(int(config.get("encoder_layers", 5))):
                decoder_lens_rows.append(
                    {
                        "eq_id": spec["eq_id"],
                        "encoder_layer": layer,
                        "decode_step": 0,
                        "topk_tokens": ["add", "x_1", "mul"],
                        "topk_probs": [0.4, 0.2, 0.1],
                        "gt_token_rank": None,
                        "partial_tokens": [],
                        "parseable": False,
                        "raw_equation": "",
                        "simplified_equation": "",
                        "oracle_inputs": spec["oracle_inputs"],
                        "placeholder": True,
                    }
                )
        decoder_lens_ranking = [f"encoder_{i}" for i in range(int(config.get("encoder_layers", 5)))]
        live = False
    else:
        require_nesymres_checkpoint(config)
        model, params_fit = load_nesymres_gpu_run2(config)
        layers = selectable_layer_names(model, include_head=False)
        hp = finetune_hparams(config)
        template_accum: dict[str, list[float]] = {name: [] for name in layers}
        next_token_accum: dict[str, list[float]] = {name: [] for name in layers}
        n_ops_accum: dict[str, list[float]] = {name: [] for name in layers}
        cka_accum: dict[str, list[float]] = {name: [] for name in layers}
        grad_accum: dict[str, list[float]] = {name: [] for name in layers}
        decoder_lens_rows = []
        n_encoder = sum(1 for name in layers if name.startswith("encoder_") and name[-1].isdigit())
        for data_seed, model_seed, noise in iter_seed_noise(config, smoke=args.smoke):
            val_rows = filter_index_rows(
                index,
                split="validation",
                split_view="main",
                data_seed=data_seed,
                noise=noise,
                eq_ids=val_ids,
            )
            if not val_rows:
                continue
            loader = build_finetune_loader(
                phase1,
                val_rows,
                params_fit.word2id,
                max_points=hp["max_points"],
                batch_size=hp["batch_size"],
                seed=model_seed,
                shuffle=False,
            )
            collected = collect_layer_representations(
                model,
                loader,
                max_batches=2 if args.smoke else 8,
                layer_names=layers,
            )
            hidden = collected["hidden"]
            template_ids, n_operators, _n_variables = _labels_for_eq_ids(
                list(collected["eq_ids"]), catalogue_by_id
            )
            next_tokens = collected["next_token_ids"]
            encoder_hidden = {
                name: hidden[name]
                for name in layers
                if name.startswith("encoder_") and name in hidden
            }
            encoder_names = [name for name in layers if name in encoder_hidden]
            hidden_ns = [arr.shape[0] for arr in hidden.values()] or [len(template_ids)]
            n_examples = min(len(template_ids), len(next_tokens), *hidden_ns)
            template_ids = template_ids[:n_examples]
            n_operators = n_operators[:n_examples]
            next_tokens = next_tokens[:n_examples]
            for name, array in hidden.items():
                array = array[:n_examples]
                template_accum[name].append(fit_linear_classifier_probe(array, template_ids)["accuracy"])
                next_token_accum[name].append(fit_linear_classifier_probe(array, next_tokens)["accuracy"])
                n_ops_accum[name].append(fit_linear_probe(array, n_operators)["r2"])
            for idx, name in enumerate(encoder_names):
                if idx == 0:
                    cka_accum[name].append(1.0)
                else:
                    prev = encoder_names[idx - 1]
                    cka_accum[name].append(linear_cka(encoder_hidden[prev], encoder_hidden[name]))
            for name, value in layer_gradient_norms_from_loader(model, loader).items():
                grad_accum.setdefault(name, []).append(float(value))
            lens_rows = val_rows[:1] if args.smoke else val_rows
            for row in lens_rows:
                payload = load_problem_npz(phase1 / "data" / row["file"])
                gt_ids = gt_token_ids_for_row(row, params_fit.word2id)
                for layer_idx in range(n_encoder):
                    steps = run_decoder_lens(
                        model,
                        payload["X_train"],
                        payload["y_train"],
                        encoder_layer=layer_idx,
                        id2word=params_fit.id2word,
                        word2id=params_fit.word2id,
                        topk=int(config.get("decoder_lens_topk", 5)),
                        gt_token_ids=gt_ids,
                        variables=list(row["oracle_inputs"]),
                    )
                    for step in steps:
                        payload_step = step.to_dict()
                        payload_step.update(
                            {
                                "eq_id": row["eq_id"],
                                "noise": float(row["noise"]),
                                "data_seed": int(row["data_seed"]),
                                "seed": int(model_seed),
                                "oracle_inputs": list(row["oracle_inputs"]),
                            }
                        )
                        decoder_lens_rows.append(payload_step)
        template_acc = {name: float(np.mean(vals)) for name, vals in template_accum.items() if vals}
        next_token_acc = {name: float(np.mean(vals)) for name, vals in next_token_accum.items() if vals}
        n_ops_r2 = {name: float(np.mean(vals)) for name, vals in n_ops_accum.items() if vals}
        cka_scores = {name: float(np.mean(vals)) for name, vals in cka_accum.items() if vals}
        grads = {name: float(np.mean(vals)) for name, vals in grad_accum.items() if vals}
        decoder_rank_scores: dict[str, list[float]] = {}
        for row in decoder_lens_rows:
            if row.get("gt_token_rank") is None:
                continue
            name = f"encoder_{int(row['encoder_layer'])}"
            decoder_rank_scores.setdefault(name, []).append(float(row["gt_token_rank"]))
        decoder_lens_ranking = sorted(
            decoder_rank_scores,
            key=lambda name: float(np.mean(decoder_rank_scores[name])),
        ) or [name for name in layers if name.startswith("encoder_")]
        live = True
        figures, _tables = graphs_dir(args.run_id or str(config.get("run_name", run_dir.name)), config=config)
        write_decoder_lens_rank_heatmap(
            decoder_lens_rows,
            figures / "phase3_decoder_lens_gt_rank.png",
        )

    mean_ranks = mean_rank_layer_scores(
        {
            "template_accuracy": template_acc,
            "next_token_accuracy": next_token_acc,
            "n_operators_r2": n_ops_r2,
        },
        higher_is_better=CANDIDATE_SELECTION_METRICS,
    )
    probe_ranking = ranking_from_mean_rank(mean_ranks)
    cka_ranking = sorted(cka_scores, key=lambda key: -cka_scores[key])
    candidates = freeze_candidate_layers(probe_ranking, k=args.candidate_k)
    if any(name == "output_head" or str(name).endswith("_head") for name in candidates):
        raise RuntimeError(f"selective-FT candidates must not include heads: {candidates}")
    write_json(
        out_dir / "probe_scores.json",
        {
            "template_accuracy": template_acc,
            "next_token_accuracy": next_token_acc,
            "n_operators_r2": n_ops_r2,
            "cka": cka_scores,
            "gradient_norms": grads,
            "mean_rank": mean_ranks,
            "probe_ranking": probe_ranking,
            "cka_ranking": cka_ranking,
            "decoder_lens_ranking": decoder_lens_ranking,
            "selection_metrics": {
                name: {"higher_is_better": hib} for name, hib in CANDIDATE_SELECTION_METRICS.items()
            },
            "placeholder": not live,
            "note": (
                "Candidate freeze uses mean rank of template / next-token / n_operators "
                "probes. Point-mean regression of encoder inputs is not used. "
                "output_head is excluded. Phase 4 IOLE/ablation/intervention remain "
                "the causal layer rankings."
            ),
        },
    )
    write_json(out_dir / "decoder_lens.json", decoder_lens_rows)
    write_json(
        out_dir / "decoder_lens_summary.json",
        {
            "n_steps": len(decoder_lens_rows),
            "n_parseable": sum(1 for row in decoder_lens_rows if row.get("parseable")),
            "parseable_rate": (
                sum(1 for row in decoder_lens_rows if row.get("parseable")) / len(decoder_lens_rows)
                if decoder_lens_rows
                else 0.0
            ),
            "encoder_layers": sorted(
                {int(row["encoder_layer"]) for row in decoder_lens_rows if "encoder_layer" in row}
            ),
        },
    )
    write_json(
        out_dir / "candidate_layers.json",
        {
            "candidates": candidates,
            "k": args.candidate_k,
            "source": "mean_rank_template_next_token_n_operators",
            "include_output_head": False,
            "frozen_before_test": True,
            "rank_agreement": rank_agreement_table(
                {
                    "probe": probe_ranking,
                    "cka": cka_ranking,
                    "decoder_lens": decoder_lens_ranking,
                }
            ),
        },
    )
    write_json(
        out_dir / "manifest.json",
        {
            "phase": 3,
            "status": "complete",
            "at_utc": utc_now(),
            "n_validation_problems": len(val_specs),
            "used_test_problems": False,
            "dry_run": bool(args.dry_run),
            "smoke": bool(args.smoke),
            "live_model": live,
            "candidate_source": "mean_rank_template_next_token_n_operators",
            "corpus_fingerprint": corpus["fingerprint"],
        },
    )
    print(f"Phase 3 complete: candidates={candidates}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
