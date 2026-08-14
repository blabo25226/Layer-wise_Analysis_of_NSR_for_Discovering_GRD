#!/usr/bin/env python
"""Microbenchmark GPU_RUN2 fine-tuning conditions for runtime estimation."""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "third_party" / "nesymres"))

from gpu_run2_experiment import (  # noqa: E402
    build_finetune_loader,
    filter_index_rows,
    finetune_hparams,
    load_nesymres_gpu_run2,
    load_phase1_index,
    selectable_layer_names,
    train_layers,
)
from gpu_run2_runtime import load_gpu_run2_configs, resolve_run_dir, write_json  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", required=True, help="existing Phase-1 run id")
    parser.add_argument("--repeats", type=int, default=2)
    parser.add_argument("--out", type=Path, default=None)
    return parser.parse_args()


def _mean(xs: list[float]) -> float | None:
    return float(statistics.mean(xs)) if xs else None


def main() -> int:
    args = parse_args()
    config = load_gpu_run2_configs()
    run_dir = resolve_run_dir(args.run_id, config=config)
    phase1 = run_dir / "phase1"
    if not (phase1 / "index.json").is_file():
        raise FileNotFoundError(f"Phase 1 index missing under {phase1}")
    index = load_phase1_index(phase1)
    splits = json.loads((phase1 / "splits.json").read_text(encoding="utf-8"))
    # Use the full main split (not smoke's 8/4 cap) so wall-time matches Phase 5 FT.
    train_ids = list(splits["main"]["train"])
    val_ids = list(splits["main"]["validation"])
    train_rows = filter_index_rows(
        index, split="train", split_view="main", data_seed=101, noise=0.0, eq_ids=train_ids
    )
    val_rows = filter_index_rows(
        index, split="validation", split_view="main", data_seed=101, noise=0.0, eq_ids=val_ids
    )
    if not train_rows or not val_rows:
        raise RuntimeError("need non-empty main train/validation rows for microbench")

    pretrained, params = load_nesymres_gpu_run2(config)
    layers = selectable_layer_names(pretrained, include_head=False)
    decoder_layers = [name for name in layers if name.startswith("decoder_")]
    hp = finetune_hparams(config)
    max_len = int(pretrained.cfg.length_eq)
    train_loader = build_finetune_loader(
        phase1,
        train_rows,
        params.word2id,
        max_points=hp["max_points"],
        batch_size=hp["batch_size"],
        seed=0,
        shuffle=True,
        max_token_len=max_len,
    )
    val_loader = build_finetune_loader(
        phase1,
        val_rows,
        params.word2id,
        max_points=hp["max_points"],
        batch_size=hp["batch_size"],
        seed=0,
        shuffle=False,
        max_token_len=max_len,
    )
    if len(train_loader.dataset) == 0 or len(val_loader.dataset) == 0:
        raise RuntimeError(
            "empty FT loaders after token-length filter; re-run Phase 1 with compact teacher_expr"
        )
    del pretrained

    conditions = {
        "full": None,
        "single_layer": decoder_layers[-1:] if decoder_layers else layers[:1],
        "top3": (decoder_layers[-3:] if len(decoder_layers) >= 3 else layers[:3]),
    }
    results: dict[str, Any] = {
        "run_id": args.run_id,
        "repeats": int(args.repeats),
        "n_train_rows": len(train_rows),
        "n_val_rows": len(val_rows),
        "n_train_loader": len(train_loader.dataset),
        "n_val_loader": len(val_loader.dataset),
        "conditions": {},
    }
    for name, layer_names in conditions.items():

        times: list[float] = []
        for rep in range(int(args.repeats)):
            started = time.perf_counter()
            _model, _params, metrics = train_layers(
                config,
                layer_names=layer_names,
                train_loader=train_loader,
                val_loader=val_loader,
                seed=rep,
            )
            elapsed = time.perf_counter() - started
            del _model
            times.append(float(elapsed))
            print(f"{name} rep={rep} seconds={elapsed:.2f} metrics={metrics}")
        results["conditions"][name] = {
            "layer_names": None if layer_names is None else list(layer_names),
            "seconds": times,
            "mean_seconds": _mean(times),
            "max_seconds": max(times) if times else None,
        }

    # Rough full-run add-on using plan.md learning-run upper bounds.
    full_m = results["conditions"]["full"]["mean_seconds"] or 0.0
    single_m = results["conditions"]["single_layer"]["mean_seconds"] or 0.0
    top3_m = results["conditions"]["top3"]["mean_seconds"] or 0.0
    # Phase4 max ~30 single-ish runs; Phase5 max ~48 selective runs (mix of full/top/random).
    # Attribute Phase5 as: 1/5 full + 1/5 top1(~single) + 1/5 top3 + 1/5 random3(~top3) + 1/5 frozen(0).
    n_phase4 = 30
    n_phase5 = 48
    ft_hours = (
        n_phase4 * single_m
        + n_phase5 * (0.2 * full_m + 0.2 * single_m + 0.4 * top3_m)
    ) / 3600.0
    decode_p90_hours = 11.05  # from smoke_06 decode-centric estimate
    results["estimate"] = {
        "decode_p90_hours_from_smoke06": decode_p90_hours,
        "ft_hours_from_microbench": ft_hours,
        "combined_hours_p90_plus_ft": decode_p90_hours + ft_hours,
        "assumptions": {
            "N_PHASE4_LEARNING_RUNS": n_phase4,
            "N_PHASE5_LEARNING_RUNS": n_phase5,
            "phase5_mix": "0.2 full + 0.2 single + 0.4 top3/random3 + 0.2 frozen",
        },
    }
    print(json.dumps(results["estimate"], indent=2))
    out = args.out or (run_dir / "ft_microbench.json")
    write_json(out, results)
    print(f"Wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
