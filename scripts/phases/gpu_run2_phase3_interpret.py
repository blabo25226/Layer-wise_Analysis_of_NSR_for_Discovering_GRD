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
from interpretability.probes import fit_linear_probe, gradient_norms  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="GPU_RUN2 Phase 3 interpretability")
    parser.add_argument("--run-id", default=os.environ.get("LANSR_RUN_ID"))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--candidate-k", type=int, default=5)
    return parser.parse_args()


def _placeholder_layers(n_encoder: int = 5, n_decoder: int = 5) -> list[str]:
    return [f"encoder_{i}" for i in range(n_encoder)] + [f"decoder_{i}" for i in range(n_decoder)]


def _dummy_probe(layers: list[str]) -> tuple[dict[str, float], dict[str, float], dict[str, float]]:
    rng = np.random.default_rng(0)
    dummy_target = rng.normal(size=32)
    dummy_base = rng.normal(size=(32, 16))
    probe_scores = {}
    cka_scores = {}
    for name in layers:
        hidden = dummy_base + 0.05 * rng.normal(size=dummy_base.shape)
        probe_scores[name] = fit_linear_probe(hidden, dummy_target)["nmse_var"]
        cka_scores[name] = linear_cka(dummy_base, hidden)
    grads = gradient_norms({name: rng.normal(size=8) for name in layers})
    return probe_scores, cka_scores, grads


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
    train_templates = [row["canonical_expr"] for row in catalogue if row["main_split"] == "train"]
    corpus = corpus_fingerprint(train_templates)
    write_json(out_dir / "finetune_corpus_fingerprint.json", corpus)

    if args.dry_run:
        layers = _placeholder_layers(int(config.get("encoder_layers", 5)))
        probe_scores, cka_scores, grads = _dummy_probe(layers)
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
        layers = selectable_layer_names(model)
        hp = finetune_hparams(config)
        probe_accum: dict[str, list[float]] = {name: [] for name in layers}
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
            hidden, targets = collect_layer_representations(
                model,
                loader,
                max_batches=2 if args.smoke else 8,
                layer_names=layers,
            )
            encoder_hidden = {
                name: hidden[name]
                for name in layers
                if name.startswith("encoder_") and name in hidden
            }
            encoder_names = [name for name in layers if name in encoder_hidden]
            for name, array in hidden.items():
                probe_accum[name].append(fit_linear_probe(array, targets)["nmse_var"])
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
        probe_scores = {name: float(np.mean(vals)) for name, vals in probe_accum.items() if vals}
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

    probe_ranking = sorted(probe_scores, key=lambda key: probe_scores[key])
    cka_ranking = sorted(cka_scores, key=lambda key: -cka_scores[key])
    candidates = freeze_candidate_layers(probe_ranking, k=args.candidate_k)
    write_json(
        out_dir / "probe_scores.json",
        {
            "probe_nmse_var": probe_scores,
            "cka": cka_scores,
            "gradient_norms": grads,
            "probe_ranking": probe_ranking,
            "cka_ranking": cka_ranking,
            "decoder_lens_ranking": decoder_lens_ranking,
            "placeholder": not live,
            "note": (
                "dry-run uses synthetic hidden states. A live RTX 2070 run "
                "overwrites this file with encoder/decoder activations from "
                "validation problems only."
            )
            if args.dry_run
            else "live probe scores from validation teacher-forcing activations",
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
            "source": "probe_nmse_var",
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
            "corpus_fingerprint": corpus["fingerprint"],
        },
    )
    print(f"Phase 3 complete: candidates={candidates}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
