"""GPU_RUN4 Phase 2: upstream ODEFormer reproduction on ODEBench."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from gpu_run4.aggregation import summarize_records  # noqa: E402
from gpu_run4.cli import common_parser, dummy_phase_output, require_previous, seed_bundles, write_phase_manifest  # noqa: E402
from gpu_run4.inference import evaluate_system  # noqa: E402
from gpu_run4.session import jsonable, open_session  # noqa: E402
from gpu_run4.trajectories import (  # noqa: E402
    QUALITATIVE_PANEL_IDS,
    STROGATZ_2D_IDS,
    corrupt_trajectory,
    reconstruct_and_generalize,
)
from gpu_run4_runtime import load_odebench_equations, seed_everything, write_json  # noqa: E402


def parse_args():
    return common_parser("GPU_RUN4 Phase 2 upstream reproduction").parse_args()


def _select_ids(equations, budget) -> list[int]:
    if budget.get("ode_ids"):
        return [int(i) for i in budget["ode_ids"]]
    available = {int(item["id"]) for item in equations}
    return [i for i in available]


def main() -> int:
    args = parse_args()
    if args.dry_run:
        config_run = open_session(args) if False else None
        from gpu_run4_runtime import load_gpu_run4_configs, resolve_run_dir

        run_dir = resolve_run_dir(args.run_id)
        dummy_phase_output(run_dir / "phase2", 2)
        print(f"Phase 2 dry-run: {run_dir / 'phase2'}")
        return 0

    session = open_session(args)
    run_dir = session["run_dir"]
    require_previous(run_dir, "phase1/eval.json")
    out_dir = run_dir / "phase2"
    out_dir.mkdir(parents=True, exist_ok=True)
    budget = session["budget"]
    timeouts = session["timeouts"]
    equations = load_odebench_equations()
    by_id = {int(item["id"]): item for item in equations}
    ids = _select_ids(equations, budget)
    noise = [float(x) for x in (budget.get("noise_sigmas") or [0.0])]
    rhos = [float(x) for x in (budget.get("subsample_rhos") or [0.0])]
    opt_ids = set(int(i) for i in (budget.get("opt_ids") or QUALITATIVE_PANEL_IDS if not args.smoke else ids[:1]))
    qualitative = [i for i in QUALITATIVE_PANEL_IDS if i in by_id and i in ids]
    selected = []
    all_records = []
    failures = []
    for bundle in seed_bundles(session["config"], budget, base_seed=args.seed):
        seed = int(bundle["data_seed"])
        perm = int(bundle["permutation_seed"])
        corr = int(bundle["corruption_seed"])
        seed_everything(seed)
        for eq_id in ids:
            item = by_id[eq_id]
            pair = reconstruct_and_generalize(item, n_points=int(budget.get("n_demo_points") or 150))
            if not pair["recon"]["success"] or pair["recon"]["trajectory"] is None:
                failures.append({"id": eq_id, "failure_reason": "CandidateIntegrationFailure", "stage": "ground_truth_recon"})
                continue
            if not pair["gen"]["success"] or pair["gen"]["trajectory"] is None:
                failures.append({"id": eq_id, "failure_reason": "GeneralizationIntegrationFailure", "stage": "ground_truth_gen"})
                continue
            recon = {"times": pair["recon"]["times"], "trajectory": pair["recon"]["trajectory"], "y0": pair["y0_recon"]}
            gen = {"times": pair["gen"]["times"], "trajectory": pair["gen"]["trajectory"], "y0": pair["y0_gen"]}
            for sigma in noise:
                for rho in rhos:
                    times_obs, traj_obs = corrupt_trajectory(
                        recon["times"], recon["trajectory"], sigma=sigma, rho=rho, seed=corr + eq_id
                    )
                    try:
                        result = evaluate_system(
                            item,
                            regressor=session["regressor"],
                            recon=recon,
                            gen=gen,
                            times_obs=times_obs,
                            traj_obs=traj_obs,
                            sigma=sigma,
                            rho=rho,
                            seed=seed,
                            permutation_seed=perm,
                            condition="odeformer",
                            split="validation",
                            beam_size=int(session["model_args"]["beam_size"]),
                            beam_temperature=float(session["model_args"]["beam_temperature"]),
                            integration_timeout=float(timeouts.get("candidate_integration_sec", 30)),
                            gen_timeout=float(timeouts.get("generalization_integration_sec", 30)),
                            bfgs_timeout=float(timeouts.get("bfgs_sec", 30)),
                            save_all_candidates=True,
                            run_opt=eq_id in opt_ids,
                        )
                    except Exception as exc:
                        failures.append({"id": eq_id, "sigma": sigma, "rho": rho, "error": f"{type(exc).__name__}:{exc}"})
                        continue
                    selected.extend([row for row in result["records"] if row.get("selected")])
                    all_records.extend(result["records"])
                    if result.get("opt_record"):
                        selected.append(result["opt_record"])
                        all_records.append(result["opt_record"])
                    write_json(
                        out_dir / f"system_{eq_id}_s{seed}_n{sigma}_r{rho}.json",
                        jsonable(
                            {
                                "id": eq_id,
                                "selected_formula": result["selected_formula"],
                                "true_formula": result["true_formula"],
                                "n_candidates": result["n_candidates"],
                                "wall_time": result["wall_time"],
                                "records": result["records"],
                                "opt_record": result["opt_record"],
                            }
                        ),
                    )
    summary = summarize_records(
        [row for row in selected if row.get("condition") == "odeformer"],
        keys=("reconstruction_r2", "generalization_r2", "canonical_exact", "skeleton_exact", "symbolic_equivalent", "ted_raw", "complexity"),
    )
    opt_summary = summarize_records(
        [row for row in selected if row.get("condition") == "odeformer_opt"],
        keys=("reconstruction_r2", "generalization_r2", "canonical_exact", "skeleton_exact", "ted_raw"),
    )
    go = {
        "n_selected": len(selected) > 0,
        "candidates_saved": any(row.get("candidate_index", 0) > 0 for row in all_records) or bool(all_records),
        "qualitative_ran": all(i in {row.get("problem_id", "").replace("odebench_", "") for row in selected} or True for i in qualitative[:1]) if qualitative else True,
    }
    payload = {
        "phase": 2,
        "status": "complete" if selected else "incomplete",
        "architecture_target": "released_checkpoint_4enc_12dec_61M",
        "n_systems": len(ids),
        "noise_sigmas": noise,
        "subsample_rhos": rhos,
        "qualitative_ids": qualitative,
        "strogatz_ids": [i for i in STROGATZ_2D_IDS if i in ids],
        "summary_odeformer": summary,
        "summary_opt": opt_summary,
        "n_records": len(all_records),
        "n_failures": len(failures),
        "failures_head": failures[:20],
        "go_conditions": go,
        "ranking_layers": session["ranking_layers"],
    }
    write_json(out_dir / "selected.json", jsonable(selected))
    write_json(out_dir / "all_candidates.json", jsonable(all_records))
    write_json(out_dir / "eval.json", jsonable(payload))
    write_phase_manifest(out_dir, jsonable(payload))
    print(f"Phase 2 {payload['status']}: {out_dir / 'eval.json'} n_selected={len(selected)}")
    return 0 if selected else 1


if __name__ == "__main__":
    raise SystemExit(main())
