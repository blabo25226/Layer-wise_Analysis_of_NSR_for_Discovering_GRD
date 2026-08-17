"""GPU_RUN3 Phase 7: validation layer ranking and selective fine-tuning."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from gpu_run3.architecture import inventory_ndformer, set_trainable_layers  # noqa: E402
from gpu_run3.cli import common_parser, dummy_phase_output, phase_budget, require_previous, write_phase_manifest  # noqa: E402
from gpu_run3.corpus import build_analysis_corpus  # noqa: E402
from gpu_run3.ranking import compare_rankings  # noqa: E402
from gpu_run3.search import run_mcts  # noqa: E402
from gpu_run3.training import clone_model, evaluate_examples, train_policy_steps  # noqa: E402
from gpu_run3_runtime import (  # noqa: E402
    load_gpu_run3_configs,
    load_json,
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


def _load_rank(path: Path, key: str) -> list[str]:
    if not path.is_file():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    value = payload.get(key) or payload.get("summary", {}).get(key)
    return list(value or [])


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
    seed_everything(args.seed)
    budget = phase_budget(config, smoke=args.smoke)
    paths = nd2_paths(config)
    device = select_device(allow_cpu=args.allow_cpu)
    model = load_ndformer(paths["checkpoint"], device=device)
    inventory = inventory_ndformer(model)
    layers = inventory["ranking_layers"]
    probe_rank = _load_rank(run_dir / "phase4" / "summary.json", "probe_rank_next_symbol") or list(layers)
    iole_rank = _load_rank(run_dir / "phase6" / "summary.json", "iole_rank") or list(layers)
    ablation_rank = _load_rank(run_dir / "phase6" / "summary.json", "ablation_rank") or list(layers)
    rankings = {
        "probe": [name for name in probe_rank if name in layers],
        "iole": [name.replace("iole::", "") for name in iole_rank if name.replace("iole::", "") in layers],
        "ablation": [name for name in ablation_rank if name in layers],
    }
    agreement = compare_rankings({k: v for k, v in rankings.items() if v}, k=3)
    # Validation-only ranking freeze: consensus = mean rank of available methods.
    scores = {name: 0.0 for name in layers}
    counts = {name: 0 for name in layers}
    for names in rankings.values():
        for rank, name in enumerate(names):
            if name in scores:
                scores[name] += float(rank)
                counts[name] += 1
    consensus = sorted(layers, key=lambda name: (scores[name] / max(counts[name], 1), name))
    random_3 = sample_random_layers_gpu_run2(layers, k=min(3, len(layers)), seed=args.seed)
    conditions = {
        "frozen": [],
        "full": None,
        "top_1": consensus[:1],
        "top_3": consensus[: min(3, len(consensus))],
        "random_3": list(random_3),
    }
    write_json(out_dir / "conditions.json", {"consensus": consensus, "conditions": {k: v for k, v in conditions.items()}, "agreement": agreement, "frozen_on_split": "analysis_validation"})
    corpus = build_analysis_corpus(seed=args.seed)
    train_row = next(row for row in corpus["records"] if row["split"] == "analysis_train")
    val_row = next(row for row in corpus["records"] if row["split"] == "analysis_validation")
    examples = [ex for ex in train_row["teacher_forcing"] if ex.get("target")]
    val_examples = [ex for ex in val_row["teacher_forcing"] if ex.get("target")]
    ft_results = []
    for name, selected in conditions.items():
        candidate = clone_model(model)
        if name == "full":
            param_info = set_trainable_layers(candidate, None, train_all=True)
            train_info = train_policy_steps(candidate, examples, steps=int(budget.get("iole_steps", 2)), data=train_row)
        elif name == "frozen":
            param_info = set_trainable_layers(candidate, [], train_all=False)
            train_info = {"steps": 0, "losses": [], "wall_time": 0.0}
        else:
            param_info = set_trainable_layers(candidate, list(selected or []), train_all=False)
            train_info = train_policy_steps(candidate, examples, steps=int(budget.get("iole_steps", 2)), data=train_row)
        metrics = evaluate_examples(candidate, val_examples, val_row)
        result = {"condition": name, "layers": selected, **param_info, **{k: v for k, v in metrics.items() if k != "rows"}, "train": train_info}
        if not args.skip_mcts:
            result["mcts"] = run_mcts(
                model=candidate,
                Xv=val_row["Xv"],
                A=val_row["A"],
                G=val_row["G"],
                Y=val_row["Y"],
                vars_node=val_row["vars_node"],
                true_prefix=val_row["prefix"],
                episode_limit=int(budget.get("mcts_episode_limit", 3)),
                time_limit_sec=float(budget.get("mcts_time_limit_sec", 30)),
                mcts_config=config["mcts"],
                random_state=args.seed,
                problem_id=f"phase7_{name}",
                system_name=val_row["system_id"],
                condition=name,
            )
        ft_results.append(result)
    summary = {"phase": 7, "status": "complete", "provenance": "layer_analysis", "consensus": consensus, "conditions": {k: v for k, v in conditions.items()}}
    write_json(out_dir / "selective_ft.json", ft_results)
    write_json(out_dir / "summary.json", summary)
    write_phase_manifest(out_dir, summary)
    print(f"Phase 7 complete: {out_dir / 'summary.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
