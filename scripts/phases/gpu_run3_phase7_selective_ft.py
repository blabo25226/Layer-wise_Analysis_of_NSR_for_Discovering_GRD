"""GPU_RUN3 Phase 7: validation layer ranking and selective fine-tuning.

The consensus ranking is frozen here from validation-only evidence (Phase 4
probes, Phase 5 DecoderLens, Phase 6 IOLE / ablation / intervention). Missing
upstream rankings are recorded as degraded rather than silently replaced by
declaration order.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from gpu_run3.architecture import inventory_ndformer, set_trainable_layers  # noqa: E402
from gpu_run3.cli import (  # noqa: E402
    common_parser,
    dummy_phase_output,
    phase_budget,
    require_previous,
    write_phase_manifest,
)
from gpu_run3.corpus import build_analysis_corpus, corpus_kwargs_from_budget, select_fixed_panel  # noqa: E402
from gpu_run3.ranking import compare_rankings  # noqa: E402
from gpu_run3.search import run_mcts  # noqa: E402
from gpu_run3.training import clone_model, evaluate_records, train_policy_multi_problem  # noqa: E402
from gpu_run3_runtime import (  # noqa: E402
    configure_nd2_logging,
    load_gpu_run3_configs,
    load_ndformer,
    nd2_paths,
    require_python_310,
    resolve_run_dir,
    seed_everything,
    select_device,
    write_json,
)
from training.selective_layers import sample_random_layers_gpu_run2  # noqa: E402


def parse_args():
    parser = common_parser("GPU_RUN3 Phase 7 ranking / selective FT")
    parser.add_argument("--skip-mcts", action="store_true")
    return parser.parse_args()


def _load_rank(path: Path, key: str) -> tuple[list[str], str]:
    if not path.is_file():
        return [], f"missing:{path.name}"
    payload = json.loads(path.read_text(encoding="utf-8"))
    value = payload.get(key) or payload.get("summary", {}).get(key)
    if not value:
        return [], f"missing_key:{key}"
    return list(value), "ok"


def _mean(values) -> float:
    finite = [float(v) for v in values if v is not None and math.isfinite(float(v))]
    return float(sum(finite) / len(finite)) if finite else float("nan")


def main() -> int:
    args = parse_args()
    require_python_310()
    config = load_gpu_run3_configs()
    run_dir = resolve_run_dir(args.run_id, config=config)
    out_dir = run_dir / "phase7"
    out_dir.mkdir(parents=True, exist_ok=True)
    if args.dry_run:
        dummy_phase_output(out_dir, 7, extra={"conditions": ["frozen", "full", "top_1", "top_3", "random_3"]})
        print(f"Phase 7 dry-run: {out_dir}")
        return 0
    require_previous(run_dir, "phase0/preflight.json")
    configure_nd2_logging(out_dir / "nd2.log")
    budget = phase_budget(config, smoke=args.smoke)
    paths = nd2_paths(config)
    device = select_device(allow_cpu=args.allow_cpu)
    model = load_ndformer(paths["checkpoint"], device=device)
    inventory = inventory_ndformer(model)
    layers = inventory["ranking_layers"]
    seed = int(args.seed) or int((config.get("seed_bundles") or [{"data_seed": 101}])[0]["data_seed"])
    seed_everything(seed)

    sources = {
        "probe": (run_dir / "phase4" / "summary.json", "probe_rank_next_symbol"),
        "gradient": (run_dir / "phase4" / "summary.json", "gradient_rank"),
        "decoderlens": (run_dir / "phase5" / "summary.json", "decoderlens_rank"),
        "iole": (run_dir / "phase6" / "summary.json", "iole_rank"),
        "ablation": (run_dir / "phase6" / "summary.json", "ablation_rank"),
        "intervention": (run_dir / "phase6" / "summary.json", "intervention_rank"),
        "update_sensitivity": (run_dir / "phase6" / "summary.json", "update_sensitivity_rank"),
    }
    rankings: dict[str, list[str]] = {}
    rank_status: dict[str, str] = {}
    for label, (path, key) in sources.items():
        names, status = _load_rank(path, key)
        cleaned = [name.replace("iole::", "") for name in names]
        cleaned = [name for name in cleaned if name in layers]
        rank_status[label] = status if not cleaned else "ok"
        if cleaned:
            rankings[label] = cleaned
    degraded = [label for label, status in rank_status.items() if status != "ok"]
    if not rankings:
        raise RuntimeError(f"no upstream layer ranking available: {rank_status}")

    agreement = compare_rankings(rankings, k=3)
    # Consensus = mean rank position across available validation-only methods.
    scores = {name: 0.0 for name in layers}
    counts = {name: 0 for name in layers}
    for names in rankings.values():
        for position, name in enumerate(names):
            if name in scores:
                scores[name] += float(position)
                counts[name] += 1
    consensus = sorted(layers, key=lambda name: (scores[name] / max(counts[name], 1), name))
    random_3 = sample_random_layers_gpu_run2(layers, k=min(3, len(layers)), seed=seed)
    conditions = {
        "frozen": [],
        "full": None,
        "top_1": consensus[:1],
        "top_3": consensus[: min(3, len(consensus))],
        "random_3": list(random_3),
    }
    write_json(
        out_dir / "conditions.json",
        {
            "consensus": consensus,
            "conditions": conditions,
            "agreement": agreement,
            "rank_sources": rank_status,
            "degraded_rank_sources": degraded,
            "frozen_on_split": "analysis_validation",
            "seed": seed,
        },
    )

    corpus = build_analysis_corpus(seed=seed, **corpus_kwargs_from_budget(budget))
    train_records = [r for r in corpus["records"] if r["split"] == "analysis_train"]
    panel = select_fixed_panel(corpus["records"], split="analysis_validation", n=int(budget.get("panel_problems", 2)))
    if not train_records or not panel:
        raise RuntimeError(f"empty split: train={len(train_records)} panel={len(panel)}")
    max_examples = int(budget.get("probe_examples", 16))
    ft_steps = int(budget.get("ft_steps", 2))
    mcts_panel = panel[: int(budget.get("mcts_panel_problems", min(2, len(panel))))]

    ft_results = []
    for name, selected in conditions.items():
        candidate = clone_model(model)
        if name == "full":
            param_info = set_trainable_layers(candidate, None, train_all=True)
        elif name == "frozen":
            param_info = set_trainable_layers(candidate, [], train_all=False)
        else:
            param_info = set_trainable_layers(candidate, list(selected or []), train_all=False)
        train_info = (
            {"steps": 0, "losses": [], "wall_time": 0.0, "trainable_parameters": 0}
            if name == "frozen"
            else train_policy_multi_problem(
                candidate, train_records, steps=ft_steps, seed=seed, max_examples_per_problem=max_examples
            )
        )
        metrics = evaluate_records(candidate, panel, max_examples_per_problem=max_examples)
        result = {
            "condition": name,
            "layers": selected,
            **param_info,
            **{k: v for k, v in metrics.items() if k != "per_problem"},
            "per_problem": metrics.get("per_problem"),
            "train": train_info,
        }
        if not args.skip_mcts:
            mcts_records = []
            for row in mcts_panel:
                mcts_records.append(
                    run_mcts(
                        model=candidate,
                        Xv=row["Xv"],
                        Xe=row["Xe"],
                        A=row["A"],
                        G=row["G"],
                        Y=row["Y"],
                        vars_node=row["vars_node"],
                        vars_edge=row["vars_edge"],
                        true_prefix=row["prefix"],
                        episode_limit=int(budget.get("mcts_episode_limit", 3)),
                        time_limit_sec=float(budget.get("mcts_time_limit_sec_ft", 30)),
                        mcts_config=config["mcts"],
                        random_state=seed,
                        problem_id=f"phase7_{name}_{row['problem_id']}",
                        system_name=row["system_id"],
                        split="analysis_validation",
                        condition=name,
                    )
                )
            result["mcts"] = mcts_records
            result["mcts_summary"] = {
                "n": len(mcts_records),
                "n_valid": sum(1 for r in mcts_records if r.get("valid")),
                "n_exact": sum(1 for r in mcts_records if r.get("exact") == 1.0),
                "mean_ted_raw": _mean([r.get("ted_raw") for r in mcts_records]),
                "mean_fit_error": _mean([r.get("fit_error") for r in mcts_records]),
                "mean_wall_time": _mean([r.get("wall_time") for r in mcts_records]),
            }
        ft_results.append(result)
        del candidate
        import gc

        import torch

        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        print(
            f"  {name}: CE={result.get('cross_entropy')} top1={result.get('top1_accuracy')} "
            f"trainable={result.get('trainable_ratio')}"
        )

    summary = {
        "phase": 7,
        "status": "complete",
        "provenance": "layer_analysis",
        "seed": seed,
        "consensus": consensus,
        "conditions": conditions,
        "rank_sources": rank_status,
        "degraded_rank_sources": degraded,
        "rank_agreement": agreement,
        "n_train_problems": len(train_records),
        "n_panel_problems": len(panel),
        "results": [{k: v for k, v in row.items() if k not in {"mcts", "per_problem"}} for row in ft_results],
    }
    write_json(out_dir / "selective_ft.json", ft_results)
    write_json(out_dir / "summary.json", summary)
    write_phase_manifest(out_dir, {k: v for k, v in summary.items() if k != "rank_agreement"})
    print(f"Phase 7 complete: {out_dir / 'summary.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
