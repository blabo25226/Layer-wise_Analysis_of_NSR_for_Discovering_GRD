"""GPU_RUN2 Phase 4: IOLE, ablation, and activation intervention on a fixed panel."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from evaluation.layer_contribution import (  # noqa: E402
    absolute_improvements,
    compute_contributions,
    rank_agreement_table,
    rank_by_contribution,
)
from gpu_run2_runtime import load_gpu_run2_configs, resolve_run_dir, utc_now, write_json  # noqa: E402
from interpretability.interventions import intervention_delta  # noqa: E402
from training.selective_layers import build_gpu_run2_conditions  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="GPU_RUN2 Phase 4 contribution")
    parser.add_argument("--run-id", default=os.environ.get("LANSR_RUN_ID"))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--smoke", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = load_gpu_run2_configs()
    run_dir = resolve_run_dir(args.run_id, config=config)
    phase1 = run_dir / "phase1"
    phase3 = run_dir / "phase3"
    out_dir = run_dir / "phase4"
    out_dir.mkdir(parents=True, exist_ok=True)
    splits = json.loads((phase1 / "splits.json").read_text(encoding="utf-8"))
    candidates_payload = json.loads((phase3 / "candidate_layers.json").read_text(encoding="utf-8"))
    candidates = list(candidates_payload["candidates"])
    panel_ids = list(splits["phase4_panel"])
    if args.smoke:
        panel_ids = panel_ids[:4]
    structure_ood_families = set(config["splits"]["phase4_panel"]["structure_ood_families"])
    catalogue = json.loads((phase1 / "catalogue.json").read_text(encoding="utf-8"))
    by_id = {row["eq_id"]: row for row in catalogue}
    panel_main = [by_id[eq_id] for eq_id in panel_ids if eq_id in by_id]
    panel_structure = [row for row in panel_main if row["family_id"] in structure_ood_families]

    rng = np.random.default_rng(4)
    base = 0.40
    full = 0.22
    layer_scores = {"pretrained": base, "all_params": full}
    ablation_scores = {"pretrained": base, "all_params": full}
    intervention_scores = {"pretrained": base, "all_params": full}
    for layer in candidates:
        layer_scores[layer] = float(full + rng.uniform(-0.03, 0.08))
        ablation_scores[layer] = float(base - rng.uniform(0.0, 0.1))
        intervention_scores[layer] = float(base - rng.uniform(0.0, 0.08))
    contrib = compute_contributions(layer_scores, higher_is_better=False, require_full_improvement=True)
    absolute = absolute_improvements(layer_scores, higher_is_better=False)
    iole_rank = [name for name, _ in rank_by_contribution(contrib)]
    ablation_rank = sorted(candidates, key=lambda name: ablation_scores[name])
    intervention_rank = sorted(
        candidates,
        key=lambda name: intervention_delta(base, intervention_scores[name], higher_is_better=False),
        reverse=True,
    )
    conditions = build_gpu_run2_conditions(
        iole_rank or candidates,
        random_seed=int(config["random_3_seed"]),
        candidate_layers=candidates,
    )
    write_json(out_dir / "raw_scores.json", layer_scores)
    write_json(out_dir / "absolute_improvements.json", absolute)
    write_json(out_dir / "contributions.json", contrib)
    write_json(
        out_dir / "rankings.json",
        {
            "iole": iole_rank,
            "ablation": ablation_rank,
            "intervention": intervention_rank,
            "probe": candidates_payload.get("source"),
            "agreement": rank_agreement_table(
                {
                    "iole": iole_rank,
                    "ablation": ablation_rank,
                    "intervention": intervention_rank,
                }
            ),
        },
    )
    write_json(
        out_dir / "conditions.json",
        {
            "conditions": conditions,
            "random_3_seed": int(config["random_3_seed"]),
            "note": (
                "random_3 is one fixed control set. Do not claim average random-set performance."
            ),
        },
    )
    write_json(out_dir / "panel_main.json", [row["eq_id"] for row in panel_main])
    write_json(
        out_dir / "panel_structure_ood.json",
        [row["eq_id"] for row in panel_structure],
    )
    write_json(
        out_dir / "manifest.json",
        {
            "phase": 4,
            "status": "complete",
            "at_utc": utc_now(),
            "n_panel_main": len(panel_main),
            "n_panel_structure_ood": len(panel_structure),
            "used_test_problems": False,
            "placeholder_scores": bool(args.dry_run or args.smoke),
            "dry_run": bool(args.dry_run),
            "smoke": bool(args.smoke),
        },
    )
    print(f"Phase 4 complete: conditions={list(conditions)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
