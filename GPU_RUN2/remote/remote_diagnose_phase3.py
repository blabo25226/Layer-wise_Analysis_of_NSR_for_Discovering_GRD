#!/usr/bin/env python
"""Diagnose Phase3 CUDA index assert on GPU_RUN2 smoke data."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "third_party" / "nesymres"))

from gpu_run2_experiment import (  # noqa: E402
    build_finetune_loader,
    filter_index_rows,
    load_nesymres_gpu_run2,
    load_phase1_index,
)
from gpu_run2_runtime import load_gpu_run2_configs  # noqa: E402


def main() -> int:
    cfg = load_gpu_run2_configs()
    run = ROOT / "results/runs/gpu_run2_smoke_02/phase1"
    index = load_phase1_index(run)
    splits = json.loads((run / "splits.json").read_text(encoding="utf-8"))
    val_ids = splits["main"]["validation"][:4]
    print("val_ids", val_ids)
    model, params = load_nesymres_gpu_run2(cfg)
    print(
        "vocab",
        len(params.word2id),
        "output_dim",
        model.cfg.output_dim,
        "length_eq",
        model.cfg.length_eq,
        "max_word_id",
        max(params.word2id.values()),
    )
    rows = filter_index_rows(
        index,
        split="validation",
        split_view="main",
        data_seed=101,
        noise=0.0,
        eq_ids=val_ids,
    )
    print("rows", len(rows), [r["eq_id"] for r in rows])
    loader = build_finetune_loader(
        run,
        rows,
        params.word2id,
        max_points=80,
        batch_size=4,
        seed=0,
        shuffle=False,
    )
    print("dataset", len(loader.dataset))
    batch = next(iter(loader))
    nums, tokens = batch[0], batch[1]
    print(
        "nums",
        tuple(nums.shape),
        "tokens",
        tuple(tokens.shape),
        "token_min_max",
        int(tokens.min()),
        int(tokens.max()),
    )
    print("any_token_ge_output_dim", bool((tokens >= model.cfg.output_dim).any().item()))
    print("seq_len_vs_length_eq", int(tokens.shape[1]), int(model.cfg.length_eq))
    model_cpu = model.cpu()
    try:
        out = model_cpu.forward([nums, tokens])
        print("CPU_forward_OK", type(out), [type(x) for x in out] if isinstance(out, tuple) else None)
    except Exception as exc:  # noqa: BLE001
        print("CPU_forward_FAIL", type(exc).__name__, exc)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
