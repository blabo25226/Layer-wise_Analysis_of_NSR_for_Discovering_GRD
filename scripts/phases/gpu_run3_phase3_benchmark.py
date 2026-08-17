"""GPU_RUN3 Phase 3: official synthetic systems formula recovery.

Runs NDformer-guided MCTS on the 10 synthetic systems of the ND2 paper, under the
official per-system N / V / E unless the budget overrides them, and repeats over
the configured seeds. Every problem is written out with its failure reason,
whether or not the search succeeded.
"""

from __future__ import annotations

import json
import math
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from gpu_run3.cli import (  # noqa: E402
    common_parser,
    dummy_phase_output,
    opt_int,
    phase_budget,
    require_previous,
    seed_bundles,
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
    parser = common_parser("GPU_RUN3 Phase 3 synthetic benchmark")
    parser.add_argument("--unguided", action="store_true", help="also run uniform (unguided) MCTS per system")
    return parser.parse_args()


def _mean(values) -> float:
    finite = [float(v) for v in values if v is not None and math.isfinite(float(v))]
    return float(sum(finite) / len(finite)) if finite else float("nan")


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
    configure_nd2_logging(out_dir / "nd2.log")
    budget = phase_budget(config, smoke=args.smoke)
    paths = nd2_paths(config)
    device = select_device(allow_cpu=args.allow_cpu)
    model = load_ndformer(paths["checkpoint"], device=device)
    official = load_official_systems(paths["synthetic_config"])
    systems = list(config["systems"])[: int(budget.get("n_systems", 10))]
    unguided_enabled = bool(args.unguided or config["mcts"].get("unguided_comparison"))

    # Resume support: seed x system is the resume unit (plan 16.3).
    records_path = out_dir / "records.jsonl"
    done: set[tuple[int, str, str]] = set()
    if records_path.is_file():
        for line in records_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            done.add((int(row.get("seed", -1)), str(row.get("system_id")), str(row.get("condition"))))
    records = []
    if records_path.is_file():
        records = [json.loads(line) for line in records_path.read_text(encoding="utf-8").splitlines() if line.strip()]

    handle = records_path.open("a", encoding="utf-8")
    try:
        for seed in seed_bundles(config, budget, base_seed=args.seed):
            for spec in systems:
                system_id = spec["system_id"]
                cfg = official[system_id]
                conditions = ["ndformer_mcts"] + (["unguided_mcts"] if unguided_enabled else [])
                if all((seed, system_id, cond) in done for cond in conditions):
                    print(f"  resume: skipping seed={seed} system={system_id}")
                    continue
                seed_everything(seed)
                started = time.time()
                try:
                    simulated = simulate_system(
                        system_id,
                        cfg,
                        seed=seed,
                        n_steps=opt_int(budget, "simulate_steps"),
                        n_nodes=opt_int(budget, "n_nodes"),
                        n_edges=opt_int(budget, "n_edges"),
                        fallback_nodes=int(config.get("kur_fallback_nodes", 50)),
                        fallback_edges=int(config.get("kur_fallback_edges", 200)),
                    )
                except Exception as exc:
                    row = {
                        "seed": seed,
                        "system_id": system_id,
                        "condition": "ndformer_mcts",
                        "valid": False,
                        "failure_reason": f"SimulationError:{type(exc).__name__}:{exc}",
                        "wall_time": time.time() - started,
                    }
                    handle.write(json.dumps(row) + "\n")
                    handle.flush()
                    records.append(row)
                    continue
                target = spec["target_var"]
                if target not in simulated["dependent"]:
                    row = {
                        "seed": seed,
                        "system_id": system_id,
                        "condition": "ndformer_mcts",
                        "valid": False,
                        "failure_reason": "InvalidPrefix",
                    }
                    handle.write(json.dumps(row) + "\n")
                    handle.flush()
                    records.append(row)
                    continue
                available = [name for name in spec["vars"] if name in simulated["independent"]]
                problem = problem_from_simulation(simulated, target_var=target, input_vars=available)
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
                    random_state=seed,
                    system_name=spec["paper_name"],
                )
                for condition in conditions:
                    if (seed, system_id, condition) in done:
                        continue
                    record = run_mcts(
                        model=None if condition == "unguided_mcts" else model,
                        problem_id=f"phase3_{system_id}_s{seed}_{condition}",
                        condition=condition,
                        **mcts_kwargs,
                    )
                    record["seed"] = seed
                    record["system_id"] = system_id
                    record["network"] = simulated["network"]
                    record["n_time_steps"] = int(problem["Y"].shape[0])
                    handle.write(json.dumps(record) + "\n")
                    handle.flush()
                    records.append(record)
                    print(
                        f"  seed={seed} {system_id} [{condition}] valid={record.get('valid')} "
                        f"exact={record.get('exact')} ted={record.get('ted_raw')} "
                        f"rmse={record.get('fit_error')} t={record.get('wall_time', 0):.0f}s"
                    )
    finally:
        handle.close()

    guided = [r for r in records if r.get("condition") == "ndformer_mcts"]
    per_system = {}
    for spec in systems:
        rows = [r for r in guided if r.get("system_id") == spec["system_id"]]
        if not rows:
            continue
        per_system[spec["system_id"]] = {
            "paper_name": spec["paper_name"],
            "n": len(rows),
            "n_valid": sum(1 for r in rows if r.get("valid")),
            "n_exact": sum(1 for r in rows if r.get("exact") == 1.0),
            "n_skeleton": sum(1 for r in rows if r.get("skeleton") == 1.0),
            "mean_ted_raw": _mean([r.get("ted_raw") for r in rows]),
            "mean_ted_skeleton": _mean([r.get("ted_skeleton") for r in rows]),
            "mean_fit_error": _mean([r.get("fit_error") for r in rows]),
            "mean_r2": _mean([(r.get("official_metrics") or {}).get("R2") for r in rows]),
            "mean_wall_time": _mean([r.get("wall_time") for r in rows]),
            "mean_search_nodes": _mean([r.get("search_nodes") for r in rows]),
            "failure_reasons": sorted({str(r.get("failure_reason")) for r in rows if r.get("failure_reason")}),
            "true_formula": next((r.get("true_formula_raw") for r in rows if r.get("true_formula_raw")), None),
            "pred_formulas": [r.get("pred_formula_raw") for r in rows],
        }
    summary = {
        "phase": 3,
        "status": "complete",
        "provenance": "upstream_reproduction",
        "seeds": sorted({int(r["seed"]) for r in records if "seed" in r}),
        "n_runs": len(guided),
        "n_systems": len(per_system),
        "n_valid": sum(1 for r in guided if r.get("valid")),
        "n_exact": sum(1 for r in guided if r.get("exact") == 1.0),
        "n_skeleton": sum(1 for r in guided if r.get("skeleton") == 1.0),
        "mean_ted_raw": _mean([r.get("ted_raw") for r in guided]),
        "mean_r2": _mean([(r.get("official_metrics") or {}).get("R2") for r in guided]),
        "unguided_enabled": unguided_enabled,
        "per_system": per_system,
    }
    if unguided_enabled:
        rows = [r for r in records if r.get("condition") == "unguided_mcts"]
        summary["unguided"] = {
            "n": len(rows),
            "n_exact": sum(1 for r in rows if r.get("exact") == 1.0),
            "mean_ted_raw": _mean([r.get("ted_raw") for r in rows]),
            "mean_r2": _mean([(r.get("official_metrics") or {}).get("R2") for r in rows]),
            "mean_search_nodes": _mean([r.get("search_nodes") for r in rows]),
        }
    write_json(out_dir / "summary.json", summary)
    write_phase_manifest(out_dir, {k: v for k, v in summary.items() if k != "per_system"})
    print(f"Phase 3 complete: {out_dir / 'summary.json'} (exact {summary['n_exact']}/{summary['n_runs']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
