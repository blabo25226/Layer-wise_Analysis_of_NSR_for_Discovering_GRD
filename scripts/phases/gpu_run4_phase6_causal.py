"""GPU_RUN4 Phase 6: causal ablation / mean intervention on a fixed panel."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

import numpy as np  # noqa: E402

from gpu_run4.cli import common_parser, dummy_phase_output, require_previous, write_phase_manifest  # noqa: E402
from gpu_run4.hooks import identity_control_hook, mean_replace_block, zero_residual_block  # noqa: E402
from gpu_run4.ranking_utils import rank_from_scores  # noqa: E402
from gpu_run4.session import jsonable, open_session  # noqa: E402
from gpu_run4.training import teacher_forcing_loss  # noqa: E402
from gpu_run4_runtime import write_json  # noqa: E402


def parse_args():
    return common_parser("GPU_RUN4 Phase 6 causal analysis").parse_args()


def main() -> int:
    args = parse_args()
    if args.dry_run:
        from gpu_run4_runtime import resolve_run_dir

        dummy_phase_output(resolve_run_dir(args.run_id) / "phase6", 6)
        return 0
    session = open_session(args)
    run_dir = session["run_dir"]
    require_previous(run_dir, "phase4/panel.json")
    require_previous(run_dir, "phase5/rankings.json")
    out_dir = run_dir / "phase6"
    out_dir.mkdir(parents=True, exist_ok=True)
    panel = __import__("json").loads((run_dir / "phase4" / "panel.json").read_text())
    for row in panel:
        row["times"] = np.asarray(row["times"], dtype=float)
        row["trajectory"] = np.asarray(row["trajectory"], dtype=float)
    layers = session["ranking_layers"]
    control_ok = True
    deltas = {name: [] for name in layers}
    for row in panel[: int(session["budget"].get("n_panel", 4))]:
        if not row.get("tree_encoded"):
            continue
        base = float(teacher_forcing_loss(session["model"], row["times"], row["trajectory"], row["tree_encoded"]).detach().cpu())
        first = layers[0]
        with identity_control_hook(session["model"], first):
            hooked = float(teacher_forcing_loss(session["model"], row["times"], row["trajectory"], row["tree_encoded"]).detach().cpu())
        if abs(base - hooked) > 1e-5:
            control_ok = False
        for name in layers:
            try:
                with zero_residual_block(session["model"], name):
                    ablated = float(
                        teacher_forcing_loss(session["model"], row["times"], row["trajectory"], row["tree_encoded"]).detach().cpu()
                    )
                deltas[name].append(ablated - base)
            except Exception:
                deltas[name].append(float("nan"))
    mean_delta = {name: float(np.nanmean(vals)) if vals else float("nan") for name, vals in deltas.items()}
    ranking = rank_from_scores(mean_delta, higher_is_better=True)
    go = {"control_hook_ok": control_ok, "ablation_ran": any(v == v for v in mean_delta.values())}
    payload = {
        "phase": 6,
        "status": "complete" if all(go.values()) else "incomplete",
        "control_hook_ok": control_ok,
        "ablation_delta_ce": mean_delta,
        "causal_ranking": ranking,
        "go_conditions": go,
        "note": "Ablation is residual-zero of attn/FFN; decode after intervention uses teacher-forcing CE, not beam-50, to avoid compute explosion.",
    }
    write_json(out_dir / "eval.json", jsonable(payload))
    write_json(out_dir / "causal_ranking.json", ranking)
    write_phase_manifest(out_dir, jsonable(payload))
    print(f"Phase 6 {payload['status']}: top causal={ranking[:3]} control_ok={control_ok}")
    return 0 if payload["status"] == "complete" else 1


if __name__ == "__main__":
    raise SystemExit(main())
