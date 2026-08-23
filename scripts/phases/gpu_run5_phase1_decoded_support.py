"""GPU_RUN5 Phase 1: reanalyse saved GPU_RUN4 ODEBench candidates."""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from evaluation.gpu_run5_structure import classify_formula  # noqa: E402
from gpu_run2_runtime import sha256_file, write_json  # noqa: E402
from gpu_run5.config import load_config, phase_dir, read_json, run_dir, write_manifest  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="GPU_RUN5 Phase 1 decoded support")
    parser.add_argument("--run-id", default=os.environ.get("LANSR_RUN_ID"))
    parser.add_argument("--smoke", action="store_true")
    return parser.parse_args()


def _system_id(row: dict) -> int:
    return int(str(row["problem_id"]).rsplit("_", 1)[-1])


def _annotate(row: dict) -> dict:
    truth = classify_formula(row.get("true_formula_raw") or "")
    candidate = classify_formula(row.get("candidate_formula_raw") or "")
    return {
        **row,
        "ode_id": _system_id(row),
        "true_structure": truth,
        "candidate_structure": candidate,
        "exponent_aware_skeleton_exact": bool(
            truth["valid"] and candidate["valid"] and
            truth["exponent_aware_skeleton"] == candidate["exponent_aware_skeleton"]
        ),
    }


def _mean(rows: list[dict], key: str) -> float | None:
    values = [float(row[key]) for row in rows if row.get(key) is not None]
    return sum(values) / len(values) if values else None


def _selected_summary(rows: list[dict]) -> dict:
    return {
        "n": len(rows),
        "valid_rate": sum(bool(row.get("valid")) for row in rows) / max(len(rows), 1),
        "skeleton_exact_rate": _mean(rows, "skeleton_exact"),
        "exponent_aware_skeleton_exact_rate": sum(row["exponent_aware_skeleton_exact"] for row in rows) / max(len(rows), 1),
        "normalized_ted_mean": _mean(rows, "normalized_ted"),
        "reconstruction_r2_mean": _mean(rows, "reconstruction_r2"),
        "generalization_r2_mean": _mean(rows, "generalization_r2"),
        "failure_counts": dict(Counter(str(row.get("failure_reason") or "none") for row in rows)),
    }


def main() -> int:
    args = parse_args()
    config = load_config()
    root = run_dir(args.run_id)
    phase0 = read_json(root / "phase0" / "manifest.json", {})
    if phase0.get("status") != "complete":
        raise RuntimeError("Phase 0 is not complete")
    out = phase_dir(args.run_id, 1)
    source = ROOT / str(config["gpu_run4_source_run"]) / "phase2"
    selected_source = json.loads((source / "selected.json").read_text())
    candidate_source = json.loads((source / "all_candidates.json").read_text())
    selected = [_annotate(row) for row in selected_source if row.get("condition") == "odeformer"]
    candidates = [_annotate(row) for row in candidate_source if row.get("condition") == "odeformer"]
    if len(selected) != 252 or len(candidates) != 12600:
        raise RuntimeError(f"unexpected GPU_RUN4 record counts: selected={len(selected)} candidates={len(candidates)}")

    variable_denominator_ids = sorted({row["ode_id"] for row in selected if row["true_structure"]["variable_denominator_form"]})
    rational_variable_ids = sorted({row["ode_id"] for row in selected if row["true_structure"]["rational_with_variable_denominator"]})
    candidate_denominator_rate = sum(row["candidate_structure"]["variable_denominator_form"] for row in candidates) / len(candidates)
    variable_selected = [row for row in selected if row["ode_id"] in variable_denominator_ids]
    selected_exact_count = sum(row["exponent_aware_skeleton_exact"] for row in variable_selected)
    grouped: dict[tuple, list[dict]] = defaultdict(list)
    for row in candidates:
        key = (row["problem_id"], row["noise_sigma"], row["subsample_rho"], row["seed"])
        grouped[key].append(row)
    truth_in_beam = []
    for rows in grouped.values():
        truth = rows[0]["true_structure"]["exponent_aware_skeleton"]
        truth_in_beam.append(any(row["candidate_structure"]["exponent_aware_skeleton"] == truth for row in rows))
    variable_group_support = [
        any(row["exponent_aware_skeleton_exact"] for row in rows)
        for rows in grouped.values() if rows[0]["ode_id"] in variable_denominator_ids
    ]
    candidate_support_rows = []
    support_groups: dict[tuple, list[dict]] = defaultdict(list)
    for row in candidates:
        true_form = "variable_denominator" if row["true_structure"]["variable_denominator_form"] else "other"
        support_groups[(true_form, row["dimension"], row["noise_sigma"], row["subsample_rho"])].append(row)
    for key, rows in sorted(support_groups.items(), key=lambda item: str(item[0])):
        candidate_support_rows.append({
            "true_form": key[0], "dimension": key[1], "noise_sigma": key[2], "subsample_rho": key[3],
            "n_candidates": len(rows),
            "variable_denominator_candidate_rate": sum(r["candidate_structure"]["variable_denominator_form"] for r in rows) / len(rows),
            "rational_with_variable_denominator_candidate_rate": sum(r["candidate_structure"]["rational_with_variable_denominator"] for r in rows) / len(rows),
            "hill_candidate_rate": sum(r["candidate_structure"]["hill_form"] for r in rows) / len(rows),
            "sigmoid_candidate_rate": sum(r["candidate_structure"]["sigmoid_saturating_form"] for r in rows) / len(rows),
        })
    selected_form_comparison = {
        "rational_with_variable_denominator": _selected_summary([r for r in selected if r["true_structure"]["rational_with_variable_denominator"]]),
        "other": _selected_summary([r for r in selected if not r["true_structure"]["rational_with_variable_denominator"]]),
    }
    summary = {
        "selected_count": len(selected),
        "candidate_count": len(candidates),
        "variable_denominator_system_ids": variable_denominator_ids,
        "variable_denominator_system_count": len(variable_denominator_ids),
        "variable_denominator_cell_count": len(variable_selected),
        "rational_with_variable_denominator_system_ids": rational_variable_ids,
        "rational_with_variable_denominator_system_count": len(rational_variable_ids),
        "candidate_variable_denominator_rate": candidate_denominator_rate,
        "variable_denominator_selected_exponent_exact_count": int(selected_exact_count),
        "all_group_true_exponent_skeleton_in_beam_rate": sum(truth_in_beam) / len(truth_in_beam),
        "variable_denominator_group_true_exponent_skeleton_in_beam_count": int(sum(variable_group_support)),
        "variable_denominator_group_count": len(variable_group_support),
        "candidate_support_by_form_dimension_corruption": candidate_support_rows,
        "selected_rational_vs_other": selected_form_comparison,
        "source_artifacts": {
            "selected_sha256": sha256_file(source / "selected.json"),
            "all_candidates_sha256": sha256_file(source / "all_candidates.json"),
        },
        "retrospective_outcomes": {
            "R4": {"observed": candidate_denominator_rate, "threshold": 0.05, "passed": candidate_denominator_rate >= 0.05},
            "R5": {"observed": int(selected_exact_count), "threshold": 0, "passed": selected_exact_count == 0},
        },
    }
    go = {
        "record_counts_ok": len(selected) == 252 and len(candidates) == 12600,
        "variable_denominator_count_ok": len(variable_denominator_ids) == 14,
        "all_records_classified": all(row["true_structure"]["valid"] and row["candidate_structure"]["valid"] for row in candidates),
        "r1_r3_aggregates_saved": bool(candidate_support_rows and selected_form_comparison),
        "retrospective_outcomes_saved": True,
        "truth_specific_beam_support_saved": len(variable_group_support) == 56,
    }
    write_json(out / "selected_annotated.json", selected)
    write_json(out / "candidates_annotated.json", candidates)
    write_json(out / "decoded_support.json", summary)
    write_json(out / "go.json", go)
    status = "complete" if all(go.values()) else "incomplete"
    write_manifest(out, 1, status, go_conditions=go, summary=summary)
    print(f"GPU_RUN5 Phase 1 {status}: {summary}")
    return 0 if status == "complete" else 1


if __name__ == "__main__":
    raise SystemExit(main())
