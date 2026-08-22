"""GPU_RUN4 Phase 7: IOLE / single-layer fine-tuning on analysis-train."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

import numpy as np  # noqa: E402

from gpu_run4.cli import common_parser, dummy_phase_output, require_previous, write_phase_manifest  # noqa: E402
from gpu_run4.ranking_utils import rank_from_scores  # noqa: E402
from gpu_run4.session import jsonable, open_session  # noqa: E402
from gpu_run4.training import teacher_forcing_loss, train_iole  # noqa: E402
from gpu_run4_runtime import load_odeformer_model, write_json  # noqa: E402


def parse_args():
    return common_parser("GPU_RUN4 Phase 7 IOLE").parse_args()


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

        dummy_phase_output(resolve_run_dir(args.run_id) / "phase7", 7)
        return 0
    session = open_session(args)
    run_dir = session["run_dir"]
    require_previous(run_dir, "phase4/corpus.json")
    out_dir = run_dir / "phase7"
    out_dir.mkdir(parents=True, exist_ok=True)
    budget = session["budget"]
    steps = int(budget.get("ft_steps", 2))
    lr = float(budget.get("ft_lr", 1e-4))
    train = _split(run_dir / "phase4" / "corpus.json", "analysis_train")
    val = _split(run_dir / "phase4" / "corpus.json", "analysis_validation")
    layers = session["ranking_layers"]
    base_ce = _mean_ce(session["model"], val)
    rows = []
    rows.append({"condition": "frozen", "val_ce": base_ce, "delta_ce": 0.0, "iole_score": 0.0, "steps": 0})
    for name in layers:
        model = load_odeformer_model(session["paths"]["checkpoint"], device=session["device"])
        fit = train_iole(model, train, trainable_layers={name}, steps=steps, lr=lr)
        val_ce = _mean_ce(model, val)
        rows.append({"condition": name, "val_ce": val_ce, "delta_ce": val_ce - base_ce, "iole_score": base_ce - val_ce, **fit})
        del model
    full = load_odeformer_model(session["paths"]["checkpoint"], device=session["device"])
    fit_full = train_iole(full, train, trainable_layers=None, steps=steps, lr=lr)
    full_ce = _mean_ce(full, val)
    rows.append({"condition": "full", "val_ce": full_ce, "delta_ce": full_ce - base_ce, "iole_score": base_ce - full_ce, **fit_full})
    iole_scores = {row["condition"]: float(row.get("iole_score") or 0) for row in rows if row["condition"] not in {"frozen", "full"}}
    ranking = rank_from_scores(iole_scores, higher_is_better=True)
    go = {"iole_ran": len(rows) >= len(layers), "full_ft_ran": any(r["condition"] == "full" and r.get("steps", 0) > 0 for r in rows)}
    payload = {
        "phase": 7,
        "status": "complete" if all(go.values()) else "incomplete",
        "base_ce": base_ce,
        "steps": steps,
        "lr": lr,
        "rows": jsonable(rows),
        "iole_ranking": ranking,
        "go_conditions": go,
    }
    write_json(out_dir / "eval.json", jsonable(payload))
    write_json(out_dir / "iole_ranking.json", ranking)
    write_phase_manifest(out_dir, jsonable(payload))
    print(f"Phase 7 {payload['status']}: top IOLE={ranking[:3]}")
    return 0 if payload["status"] == "complete" else 1


if __name__ == "__main__":
    raise SystemExit(main())
