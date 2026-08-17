"""GPU_RUN3 Phase 3: official synthetic systems formula recovery."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from gpu_run3.cli import common_parser, dummy_phase_output, phase_budget, require_previous, write_phase_manifest  # noqa: E402
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
    return common_parser("GPU_RUN3 Phase 3 synthetic benchmark").parse_args()


def main() -> int:
    args = parse_args()
    require_python_310()
    config = load_gpu_run3_configs()
    run_dir = resolve_run_dir(args.run_id, config=config)
    out_dir = run_dir / "phase3"
    out_dir.mkdir(parents=True, exist_ok=True)
    if args.dry_run:
        dummy_phase_output(out_dir, 3)
        print(f"Phase 3 dry-run: {out_dir}")
        return 0
    require_previous(run_dir, "phase0/preflight.json")
    seed_everything(args.seed)
    configure_nd2_logging(out_dir / "nd2.log")
    budget = phase_budget(config, smoke=args.smoke)
    paths = nd2_paths(config)
    device = select_device(allow_cpu=args.allow_cpu)
    model = load_ndformer(paths["checkpoint"], device=device)
    official = load_official_systems(paths["synthetic_config"])
    systems = list(config["systems"])
    if args.smoke:
        systems = systems[: int(budget.get("n_systems", 1))]
    records = []
    for spec in systems:
        system_id = spec["system_id"]
        cfg = official[system_id]
        simulated = simulate_system(
            system_id,
            cfg,
            seed=args.seed,
            n_steps=int(budget.get("simulate_steps", 24)),
            n_nodes=int(budget.get("n_nodes", 6)),
            n_edges=int(budget.get("n_edges", 10)),
        )
        target = spec["target_var"]
        if target not in simulated["dependent"]:
            records.append({"system_id": system_id, "failure_reason": "InvalidPrefix", "valid": False})
            continue
        available = [name for name in spec["vars"] if name in simulated["independent"]]
        problem = problem_from_simulation(simulated, target_var=target, input_vars=available)
        record = run_mcts(
            model=model,
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
            problem_id=f"phase3_{system_id}",
            system_name=spec["paper_name"],
            condition="ndformer_mcts",
        )
        records.append(record)
        write_json(out_dir / f"{system_id}.json", record)
    summary = {
        "phase": 3,
        "status": "complete",
        "provenance": "upstream_reproduction",
        "n_systems": len(records),
        "n_valid": sum(1 for r in records if r.get("valid")),
        "n_exact": sum(1 for r in records if r.get("exact") == 1.0),
        "records": records,
    }
    write_json(out_dir / "summary.json", summary)
    write_phase_manifest(out_dir, {k: v for k, v in summary.items() if k != "records"})
    print(f"Phase 3 complete: {out_dir / 'summary.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
