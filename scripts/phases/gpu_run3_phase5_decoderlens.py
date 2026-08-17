"""GPU_RUN3 Phase 5: encoder intermediate decode and decoder logit-lens.

Runs over a fixed validation panel (ID-ordered, chosen before results are seen)
rather than a single problem, and aggregates the layer-wise trajectory of true
symbol rank / probability and provisional-formula TED.
"""

from __future__ import annotations

import math
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from gpu_run3.architecture import inventory_ndformer  # noqa: E402
from gpu_run3.cli import (  # noqa: E402
    common_parser,
    dummy_phase_output,
    phase_budget,
    require_previous,
    seed_bundles,
    write_phase_manifest,
)
from gpu_run3.corpus import build_analysis_corpus, corpus_kwargs_from_budget, select_fixed_panel  # noqa: E402
from gpu_run3.decoderlens import decoder_logit_lens, encoder_intermediate_decode, encoder_ted_trajectory  # noqa: E402
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


def parse_args():
    return common_parser("GPU_RUN3 Phase 5 DecoderLens / intermediate decoding").parse_args()


def _mean(values) -> float:
    finite = [float(v) for v in values if v is not None and math.isfinite(float(v))]
    return float(sum(finite) / len(finite)) if finite else float("nan")


def _aggregate(outputs: list[dict], side: str) -> dict[str, dict[str, float]]:
    by_layer: dict[str, list[dict]] = defaultdict(list)
    for problem in outputs:
        for layer_row in problem.get(side) or []:
            if not layer_row.get("valid"):
                continue
            by_layer[layer_row["module_name"]].extend(layer_row.get("rows") or [])
    return {
        name: {
            "n": len(rows),
            "mean_true_symbol_rank": _mean([r.get("true_symbol_rank") for r in rows]),
            "mean_true_symbol_probability": _mean([r.get("true_symbol_probability") for r in rows]),
            "mean_entropy": _mean([r.get("entropy") for r in rows]),
            "top1_accuracy": _mean([1.0 if r.get("true_symbol_rank") == 1 else 0.0 for r in rows]),
            "mean_ted_raw": _mean([r.get("ted_raw") for r in rows]),
        }
        for name, rows in by_layer.items()
    }


def main() -> int:
    args = parse_args()
    require_python_310()
    config = load_gpu_run3_configs()
    run_dir = resolve_run_dir(args.run_id, config=config)
    out_dir = run_dir / "phase5"
    out_dir.mkdir(parents=True, exist_ok=True)
    if args.dry_run:
        dummy_phase_output(out_dir, 5, extra={"analysis": "encoder_intermediate_decode"})
        print(f"Phase 5 dry-run: {out_dir}")
        return 0
    require_previous(run_dir, "phase0/preflight.json")
    budget = phase_budget(config, smoke=args.smoke)
    paths = nd2_paths(config)
    device = select_device(allow_cpu=args.allow_cpu)
    model = load_ndformer(paths["checkpoint"], device=device)
    inventory = inventory_ndformer(model)
    corpus_kwargs = corpus_kwargs_from_budget(budget)
    n_problems = int(budget.get("decoderlens_problems", 1))
    n_examples = int(budget.get("decoderlens_examples", 4))

    outputs = []
    failures = []
    for seed in seed_bundles(config, budget, base_seed=args.seed):
        seed_everything(seed)
        corpus = build_analysis_corpus(seed=seed, **corpus_kwargs)
        panel = select_fixed_panel(corpus["records"], split="analysis_validation", n=n_problems)
        for row in panel:
            examples = [ex for ex in row["teacher_forcing"] if ex.get("target")][:n_examples]
            if not examples:
                failures.append({"problem_id": row["problem_id"], "failure_reason": "InvalidPrefix"})
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
            prefixes = [ex["prefix"] for ex in examples]
            targets = [ex["target"] for ex in examples]
            try:
                encoder_rows = encoder_intermediate_decode(
                    model, inventory["encoder_blocks"], prefixes, true_targets=targets
                )
                encoder_rows = encoder_ted_trajectory(encoder_rows, true_prefix=row["prefix"])
                decoder_rows = decoder_logit_lens(
                    model, inventory["decoder_blocks"], prefixes, true_targets=targets
                )
            except Exception as exc:
                failures.append(
                    {
                        "seed": seed,
                        "problem_id": row["problem_id"],
                        "failure_reason": f"ActivationHookError:{type(exc).__name__}:{exc}",
                    }
                )
                continue
            outputs.append(
                {
                    "seed": seed,
                    "problem_id": row["problem_id"],
                    "formula_id": row["formula_id"],
                    "true_formula": row["raw_expr"],
                    "n_examples": len(examples),
                    "encoder": encoder_rows,
                    "decoder": decoder_rows,
                }
            )

    encoder_summary = _aggregate(outputs, "encoder")
    decoder_summary = _aggregate(outputs, "decoder")
    summary = {
        "phase": 5,
        "status": "complete",
        "provenance": "layer_analysis",
        "seeds": sorted({item["seed"] for item in outputs}),
        "n_problems": len(outputs),
        "n_failures": len(failures),
        "failures": failures,
        "encoder_blocks": inventory["encoder_blocks"],
        "decoder_blocks": inventory["decoder_blocks"],
        "encoder_layer_summary": encoder_summary,
        "decoder_layer_summary": decoder_summary,
        "decoderlens_rank": rank_from_scores(
            {name: stats["mean_true_symbol_probability"] for name, stats in {**encoder_summary, **decoder_summary}.items()},
            higher_is_better=True,
        ),
        "note": (
            "encoder_intermediate_decode feeds each encoder block's memory to the "
            "trained decoder; it follows DecoderLens in spirit but is not the "
            "identical method, since NDformer has no per-layer decoder alignment."
        ),
    }
    write_json(out_dir / "trajectories.json", outputs)
    write_json(out_dir / "summary.json", summary)
    write_phase_manifest(out_dir, {k: v for k, v in summary.items() if k != "failures"})
    print(f"Phase 5 complete: {out_dir / 'summary.json'} (n_problems={len(outputs)}, failures={len(failures)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
