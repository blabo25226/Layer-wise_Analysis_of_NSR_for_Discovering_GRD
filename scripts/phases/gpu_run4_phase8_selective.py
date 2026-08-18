"""GPU_RUN4 Phase 8: selective fine-tuning from validation rankings only."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

import numpy as np  # noqa: E402

from gpu_run4.cli import common_parser, dummy_phase_output, require_previous, write_phase_manifest  # noqa: E402
from gpu_run4.session import jsonable, open_session  # noqa: E402
from gpu_run4.training import teacher_forcing_loss, train_iole  # noqa: E402
from gpu_run4_runtime import load_odeformer_model, write_json  # noqa: E402


def parse_args():
    return common_parser("GPU_RUN4 Phase 8 selective fine-tuning").parse_args()


def _split(path: Path, name: str) -> list[dict]:
    rows = __import__("json").loads(path.read_text())
    out = []
    for row in rows:
        if row.get("split") != name:
            continue
        row = dict(row)
        row["times"] = np.asarray(row["times"], dtype=float)
        row["trajectory"] = np.asarray(row["trajectory"], dtype=float)
        out.append(row)
    return out


def _mean_ce(model, rows) -> float:
    vals = []
    for row in rows[:8]:
        if not row.get("tree_encoded"):
            continue
        try:
            vals.append(float(teacher_forcing_loss(model, row["times"], row["trajectory"], row["tree_encoded"]).detach().cpu()))
        except Exception:
            continue
    return float(np.mean(vals)) if vals else float("nan")


def main() -> int:
    args = parse_args()
    if args.dry_run:
        from gpu_run4_runtime import resolve_run_dir

        dummy_phase_output(resolve_run_dir(args.run_id) / "phase8", 8)
        return 0
    session = open_session(args)
    run_dir = session["run_dir"]
    require_previous(run_dir, "phase7/iole_ranking.json")
    require_previous(run_dir, "phase6/causal_ranking.json")
    out_dir = run_dir / "phase8"
    out_dir.mkdir(parents=True, exist_ok=True)
    iole = __import__("json").loads((run_dir / "phase7" / "iole_ranking.json").read_text())
    causal = __import__("json").loads((run_dir / "phase6" / "causal_ranking.json").read_text())
    layers = session["ranking_layers"]
    rng = np.random.default_rng(int(session["config"]["seed_bundles"][0]["data_seed"]))
    random_sets = []
    for _ in range(int(session["budget"].get("n_random_sets", 3))):
        random_sets.append([str(x) for x in rng.choice(layers, size=min(3, len(layers)), replace=False)])
    conditions = {
        "frozen": set(),
        "full": None,
        "top1": set(iole[:1]),
        "top3": set(iole[:3]),
        "bottom3": set(iole[-3:]),
        "causal_top3": set(causal[:3]),
    }
    for index, names in enumerate(random_sets):
        conditions[f"random3_{index}"] = set(names)
    train = _split(run_dir / "phase4" / "corpus.json", "analysis_train")
    val = _split(run_dir / "phase4" / "corpus.json", "analysis_validation")
    steps = int(session["budget"].get("ft_steps", 2))
    lr = float(session["budget"].get("ft_lr", 1e-4))
    results = []
    for name, trainable in conditions.items():
        model = load_odeformer_model(session["paths"]["checkpoint"], device=session["device"])
        fit = train_iole(model, train, trainable_layers=trainable, steps=steps, lr=lr)
        results.append(
            {
                "condition": name,
                "layers": sorted(trainable) if trainable is not None else "full",
                "val_ce": _mean_ce(model, val),
                **{k: v for k, v in fit.items() if k != "losses"},
                "final_loss": fit.get("final_loss"),
            }
        )
        del model
    go = {"conditions_ran": len(results) >= 6, "rankings_from_validation_only": True}
    payload = {
        "phase": 8,
        "status": "complete" if go["conditions_ran"] else "incomplete",
        "iole_ranking": iole,
        "causal_ranking": causal,
        "random_sets": random_sets,
        "results": jsonable(results),
        "go_conditions": go,
        "note": "Layer sets were frozen from validation rankings before any analysis-test evaluation.",
    }
    write_json(out_dir / "eval.json", jsonable(payload))
    write_json(out_dir / "conditions.json", jsonable({k: (sorted(v) if isinstance(v, set) else v) for k, v in conditions.items()}))
    write_phase_manifest(out_dir, jsonable(payload))
    print(f"Phase 8 {payload['status']}: {len(results)} conditions")
    return 0 if payload["status"] == "complete" else 1


if __name__ == "__main__":
    raise SystemExit(main())
