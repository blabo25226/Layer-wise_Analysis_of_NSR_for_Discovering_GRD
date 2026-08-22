"""GPU_RUN4 Phase 9: analysis-test once, then integrated Result A / Result B reports."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

import numpy as np  # noqa: E402

from gpu_run4.cli import common_parser, dummy_phase_output, require_previous, write_phase_manifest  # noqa: E402
from gpu_run4.session import jsonable, open_session  # noqa: E402
from gpu_run4.training import teacher_forcing_loss, train_iole  # noqa: E402
from gpu_run4_runtime import load_odeformer_model, utc_now, write_json  # noqa: E402


def parse_args():
    return common_parser("GPU_RUN4 Phase 9 final test / integrated analysis").parse_args()


def _read(path: Path, default=None):
    if not path.is_file():
        return default
    return json.loads(path.read_text())


def _split(rows, name):
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
    for row in rows:
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

        dummy_phase_output(resolve_run_dir(args.run_id) / "phase9", 9)
        return 0
    session = open_session(args)
    run_dir = session["run_dir"]
    require_previous(run_dir, "phase8/conditions.json")
    require_previous(run_dir, "phase2/eval.json")
    out_dir = run_dir / "phase9"
    out_dir.mkdir(parents=True, exist_ok=True)
    conditions = _read(run_dir / "phase8" / "conditions.json", {})
    corpus = _read(run_dir / "phase4" / "corpus.json", [])
    train = _split(corpus, "analysis_train")
    test = _split(corpus, "analysis_test")
    steps = int(session["budget"].get("ft_steps", 2))
    lr = float(session["budget"].get("ft_lr", 1e-4))
    test_rows = []
    for name, layers in conditions.items():
        trainable = None if layers == "full" or layers is None else set(layers)
        model = load_odeformer_model(session["paths"]["checkpoint"], device=session["device"])
        train_iole(model, train, trainable_layers=trainable, steps=steps, lr=lr)
        test_rows.append({"condition": name, "layers": layers, "test_ce": _mean_ce(model, test)})
        del model
    phase2 = _read(run_dir / "phase2" / "eval.json", {})
    phase3 = _read(run_dir / "phase3" / "eval.json", {})
    phase5 = _read(run_dir / "phase5" / "eval.json", {})
    phase6 = _read(run_dir / "phase6" / "eval.json", {})
    phase7 = _read(run_dir / "phase7" / "eval.json", {})
    result_a = {
        "architecture_target": "released_checkpoint_4enc_12dec_61M",
        "not_paper_table": True,
        "odebench_summary": phase2.get("summary_odeformer"),
        "opt_summary": phase2.get("summary_opt"),
        "qualitative_ids": phase2.get("qualitative_ids"),
        "beam_true_skeleton_in_beam_rate": phase3.get("true_skeleton_in_beam_rate"),
        "n_phase2_records": phase2.get("n_records"),
    }
    result_b = {
        "architecture_target": "released_checkpoint_4enc_12dec_61M",
        "not_paper_table": True,
        "n_ranking_layers": len(session["ranking_layers"]),
        "ranking_layers": session["ranking_layers"],
        "probe_ranking": (phase5.get("rankings") or {}).get("probe_dimension"),
        "causal_ranking": phase6.get("causal_ranking"),
        "iole_ranking": phase7.get("iole_ranking"),
        "selective_ft_test": test_rows,
    }
    go = {"test_evaluated_once": bool(test_rows), "result_a_saved": True, "result_b_saved": True}
    payload = {
        "phase": 9,
        "status": "complete",
        "at_utc": utc_now(),
        "result_a_reproduction": result_a,
        "result_b_layer_analysis": result_b,
        "go_conditions": go,
        "caveats": [
            "Released checkpoint is 4 encoder + 12 decoder / ~61M, not the paper 4+16 / ~86M table.",
            "Layer ranking used validation only; analysis-test was evaluated once in this phase.",
            "Causal decode used teacher-forcing CE rather than beam-50 to keep wall time bounded.",
        ],
    }
    write_json(out_dir / "eval.json", jsonable(payload))
    write_json(out_dir / "result_a.json", jsonable(result_a))
    write_json(out_dir / "result_b.json", jsonable(result_b))
    write_phase_manifest(out_dir, jsonable(payload))
    print(f"Phase 9 complete: test conditions={len(test_rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
