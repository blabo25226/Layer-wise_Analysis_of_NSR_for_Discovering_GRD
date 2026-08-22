"""GPU_RUN3 Phase 2: NDformer-guided MCTS pipeline reproduction.

Validates the whole ND2 discovery pipeline (network dynamical operators ->
NDformer policy -> MCTS -> reward / constant optimization -> final formula) on a
single official system before Phase 3 runs the full benchmark.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from gpu_run3.cli import (  # noqa: E402
    common_parser,
    dummy_phase_output,
    opt_int,
    phase_budget,
    require_previous,
    write_phase_manifest,
)
from gpu_run3.search import run_mcts  # noqa: E402
from gpu_run3.synthetic import load_official_systems, problem_from_simulation, simulate_system  # noqa: E402
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


def parse_args():
    parser = common_parser("GPU_RUN3 Phase 2 ND2 full-pipeline reproduction")
    parser.add_argument("--unguided", action="store_true", help="optional uniform MCTS comparison")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    require_python_310()
    config = load_gpu_run3_configs()
    run_dir = resolve_run_dir(args.run_id, config=config)
    out_dir = run_dir / "phase2"
    out_dir.mkdir(parents=True, exist_ok=True)
    if args.dry_run:
        dummy_phase_output(out_dir, 2)
        print(f"Phase 2 dry-run: {out_dir}")
        return 0
    require_previous(run_dir, "phase0/preflight.json")
    seed_everything(args.seed)
    configure_nd2_logging(out_dir / "nd2.log")
    budget = phase_budget(config, smoke=args.smoke)
    paths = nd2_paths(config)
    device = select_device(allow_cpu=args.allow_cpu)
    model = load_ndformer(paths["checkpoint"], device=device)
    official = load_official_systems(paths["synthetic_config"])
    simulated = simulate_system(
        "KUR",
        official["KUR"],
        seed=args.seed,
        n_steps=opt_int(budget, "simulate_steps"),
        n_nodes=opt_int(budget, "n_nodes"),
        n_edges=opt_int(budget, "n_edges"),
        fallback_nodes=int(config.get("kur_fallback_nodes", 50)),
        fallback_edges=int(config.get("kur_fallback_edges", 200)),
    )
    problem = problem_from_simulation(simulated, target_var="omega", input_vars=["x", "omega0"])
    mcts_kwargs = dict(
        Xv=problem["Xv"],
        A=problem["A"],
        G=problem["G"],
        Y=problem["Y"],
        vars_node=problem["vars_node"],
        true_prefix=problem["true_prefix"],
        episode_limit=int(budget.get("mcts_episode_limit", 3)),
        time_limit_sec=float(budget.get("mcts_time_limit_sec", 30)),
        mcts_config=config["mcts"],
        random_state=args.seed,
        system_name="KUR",
    )
    guided = run_mcts(model=model, problem_id="phase2_kur", condition="ndformer_mcts", **mcts_kwargs)
    write_json(out_dir / "guided_mcts.json", guided)
    comparison = {"guided": guided}
    unguided = None
    if args.unguided or config["mcts"].get("unguided_comparison"):
        unguided = run_mcts(model=None, problem_id="phase2_kur_unguided", condition="unguided_mcts", **mcts_kwargs)
        write_json(out_dir / "unguided_mcts.json", unguided)
        comparison["unguided"] = unguided
    summary = {
        "phase": 2,
        "status": "complete",
        "provenance": "upstream_reproduction",
        "system": "KUR",
        "network": simulated["network"],
        "n_time_steps": int(problem["Y"].shape[0]),
        "guided_valid": guided.get("valid"),
        "guided_pred": guided.get("pred_formula_raw"),
        "guided_exact": guided.get("exact"),
        "guided_ted_raw": guided.get("ted_raw"),
        "guided_ted_skeleton": guided.get("ted_skeleton"),
        "guided_fit_error": guided.get("fit_error"),
        "guided_official_metrics": guided.get("official_metrics"),
        "search_nodes": guided.get("search_nodes"),
        "candidate_count": guided.get("candidate_count"),
        "wall_time": guided.get("wall_time"),
        "failure_reason": guided.get("failure_reason"),
        "true_formula": guided.get("true_formula_raw"),
    }
    if unguided is not None:
        summary["unguided"] = {
            "pred": unguided.get("pred_formula_raw"),
            "exact": unguided.get("exact"),
            "ted_raw": unguided.get("ted_raw"),
            "fit_error": unguided.get("fit_error"),
            "search_nodes": unguided.get("search_nodes"),
            "candidate_count": unguided.get("candidate_count"),
            "wall_time": unguided.get("wall_time"),
        }
    write_json(out_dir / "summary.json", summary)
    write_phase_manifest(out_dir, {**summary, "comparison_keys": list(comparison)})
    print(f"Phase 2 complete: {out_dir / 'summary.json'} (pred={summary['guided_pred']!r})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
