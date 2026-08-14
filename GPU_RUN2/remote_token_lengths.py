#!/usr/bin/env python
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "third_party" / "nesymres"))

from data.finetune_dataset import expression_to_tokens, instantiate_expr  # noqa: E402
from data.gnw_synthetic import load_problem_npz  # noqa: E402
from gpu_run2_experiment import (  # noqa: E402
    load_nesymres_gpu_run2,
    load_phase1_index,
    row_to_sampled,
)
from gpu_run2_runtime import load_gpu_run2_configs  # noqa: E402


def main() -> None:
    cfg = load_gpu_run2_configs()
    _, params = load_nesymres_gpu_run2(cfg)
    run = ROOT / "results/runs/gpu_run2_smoke_02/phase1"
    index = load_phase1_index(run)
    for row in index:
        if row["noise"] != 0.0:
            continue
        ds = row_to_sampled(run, row, xy="train")
        expr = instantiate_expr(ds)
        toks = expression_to_tokens(expr, dict(params.word2id))
        n = None if toks is None else len(toks)
        print(f"{row['eq_id']:20s} split={row['main_split']:10s} toklen={n} expr={expr[:80]}")


if __name__ == "__main__":
    main()
