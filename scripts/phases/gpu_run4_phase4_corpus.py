"""GPU_RUN4 Phase 4: independent synthetic corpus and teacher-forcing baseline."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from gpu_run4.cli import common_parser, dummy_phase_output, require_previous, seed_bundles, write_phase_manifest  # noqa: E402
from gpu_run4.corpus import build_analysis_corpus, select_fixed_panel  # noqa: E402
from gpu_run4.session import jsonable, open_session  # noqa: E402
from gpu_run4.training import teacher_forcing_loss  # noqa: E402
from gpu_run4_runtime import seed_everything, write_json  # noqa: E402


def parse_args():
    return common_parser("GPU_RUN4 Phase 4 analysis corpus").parse_args()


def main() -> int:
    args = parse_args()
    if args.dry_run:
        from gpu_run4_runtime import resolve_run_dir

        dummy_phase_output(resolve_run_dir(args.run_id) / "phase4", 4)
        return 0
    session = open_session(args)
    run_dir = session["run_dir"]
    require_previous(run_dir, "phase2/eval.json")
    out_dir = run_dir / "phase4"
    out_dir.mkdir(parents=True, exist_ok=True)
    budget = session["budget"]
    bundle = seed_bundles(session["config"], budget, base_seed=args.seed)[0]
    seed_everything(int(bundle["data_seed"]))
    corpus = build_analysis_corpus(
        session["model"],
        n_train=int(budget.get("n_corpus_train", 24)),
        n_validation=int(budget.get("n_corpus_val", 8)),
        n_test=int(budget.get("n_corpus_test", 8)),
        seed=int(bundle["data_seed"]),
    )
    val = [row for row in corpus["records"] if row["split"] == "analysis_validation"]
    panel = select_fixed_panel(val, int(budget.get("n_panel", 4)), seed=int(bundle["data_seed"]))
    ce_losses = []
    for row in val[: min(4, len(val))]:
        try:
            loss = teacher_forcing_loss(session["model"], row["times"], row["trajectory"], row["tree_encoded"])
            ce_losses.append(float(loss.detach().cpu()))
        except Exception as exc:
            ce_losses.append(None)
            row["tf_error"] = f"{type(exc).__name__}:{exc}"
    serializable = []
    for row in corpus["records"]:
        serializable.append(
            {
                **{k: v for k, v in row.items() if k not in {"times", "trajectory"}},
                "times": row["times"].tolist(),
                "trajectory": row["trajectory"].tolist(),
                "tree_encoded": list(row["tree_encoded"]) if row.get("tree_encoded") is not None else None,
            }
        )
    go = {
        "corpus_built": corpus["n_train"] > 0,
        "no_skeleton_leakage": all(v == 0 for v in corpus["skeleton_leakage"].values()),
        "panel_built": len(panel) > 0,
        "teacher_forcing_ok": any(v is not None for v in ce_losses),
    }
    payload = {
        "phase": 4,
        "status": "complete" if all(go.values()) else "incomplete",
        "fingerprint": corpus["fingerprint"],
        "n_train": corpus["n_train"],
        "n_validation": corpus["n_validation"],
        "n_test": corpus["n_test"],
        "n_failures": corpus["n_failures"],
        "skeleton_leakage": corpus["skeleton_leakage"],
        "panel_ids": [row["problem_id"] for row in panel],
        "teacher_forcing_ce": ce_losses,
        "go_conditions": go,
    }
    write_json(out_dir / "corpus.json", jsonable(serializable))
    write_json(out_dir / "panel.json", jsonable([{k: v for k, v in row.items() if k not in {"times", "trajectory"}} | {"times": row["times"].tolist(), "trajectory": row["trajectory"].tolist()} for row in panel]))
    write_json(out_dir / "eval.json", jsonable(payload))
    write_phase_manifest(out_dir, jsonable(payload))
    print(f"Phase 4 {payload['status']}: train={corpus['n_train']} leak={corpus['skeleton_leakage']}")
    return 0 if payload["status"] == "complete" else 1


if __name__ == "__main__":
    raise SystemExit(main())
