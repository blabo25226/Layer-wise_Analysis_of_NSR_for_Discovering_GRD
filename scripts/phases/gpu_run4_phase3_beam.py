"""GPU_RUN4 Phase 3: beam-level symbolic recovery diagnosis."""

from __future__ import annotations

import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from gpu_run4.cli import common_parser, dummy_phase_output, require_previous, write_phase_manifest  # noqa: E402
from gpu_run4_runtime import load_gpu_run4_configs, resolve_run_dir, write_json  # noqa: E402


def parse_args():
    return common_parser("GPU_RUN4 Phase 3 beam diagnosis").parse_args()


def _group_key(row: dict) -> tuple:
    return (
        row.get("problem_id"),
        row.get("seed"),
        row.get("noise_sigma"),
        row.get("subsample_rho"),
        row.get("condition"),
    )


def diagnose(rows: list[dict]) -> list[dict]:
    grouped: dict[tuple, list[dict]] = defaultdict(list)
    for row in rows:
        grouped[_group_key(row)].append(row)
    reports = []
    for key, items in grouped.items():
        if key[4] not in {None, "odeformer"}:
            continue
        items = sorted(items, key=lambda r: int(r.get("candidate_index") or 0))
        selected = next((r for r in items if r.get("selected")), items[0] if items else None)
        skeletons = [r.get("candidate_formula_skeleton") for r in items if r.get("valid")]
        unique = len(set(skeletons))
        true_skel = selected.get("true_formula_skeleton") if selected else None
        in_beam = any(r.get("skeleton_exact") == 1.0 for r in items)
        oracle = min(items, key=lambda r: float(r.get("ted_raw") if r.get("ted_raw") == r.get("ted_raw") else 1e9))
        reports.append(
            {
                "problem_id": key[0],
                "seed": key[1],
                "noise_sigma": key[2],
                "subsample_rho": key[3],
                "n_candidates": len(items),
                "n_valid": sum(1 for r in items if r.get("valid")),
                "unique_skeletons": unique,
                "true_skeleton_in_beam": bool(in_beam),
                "selected_ted": selected.get("ted_raw") if selected else None,
                "oracle_ted": oracle.get("ted_raw") if oracle else None,
                "oracle_index": oracle.get("candidate_index") if oracle else None,
                "selected_reconstruction_r2": selected.get("reconstruction_r2") if selected else None,
                "selection_gap_ted": (
                    float(selected["ted_raw"]) - float(oracle["ted_raw"])
                    if selected and oracle and selected.get("ted_raw") == selected.get("ted_raw") and oracle.get("ted_raw") == oracle.get("ted_raw")
                    else None
                ),
                "true_skeleton": true_skel,
            }
        )
    return reports


def main() -> int:
    args = parse_args()
    config = load_gpu_run4_configs()
    run_dir = resolve_run_dir(args.run_id, config=config)
    out_dir = run_dir / "phase3"
    out_dir.mkdir(parents=True, exist_ok=True)
    if args.dry_run:
        dummy_phase_output(out_dir, 3)
        return 0
    require_previous(run_dir, "phase2/all_candidates.json")
    rows = __import__("json").loads((run_dir / "phase2" / "all_candidates.json").read_text())
    reports = diagnose(rows)
    n = len(reports) or 1
    rate = sum(1 for r in reports if r["true_skeleton_in_beam"]) / n
    payload = {
        "phase": 3,
        "status": "complete",
        "n_groups": len(reports),
        "true_skeleton_in_beam_rate": rate,
        "mean_unique_skeletons": sum(r["unique_skeletons"] for r in reports) / n,
        "mean_selection_gap_ted": sum((r["selection_gap_ted"] or 0) for r in reports) / n,
        "go_conditions": {"beam_diagnosis_saved": bool(reports)},
    }
    write_json(out_dir / "beam_groups.json", reports)
    write_json(out_dir / "eval.json", payload)
    write_phase_manifest(out_dir, payload)
    print(f"Phase 3 complete: skeleton-in-beam rate={rate:.3f} groups={len(reports)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
