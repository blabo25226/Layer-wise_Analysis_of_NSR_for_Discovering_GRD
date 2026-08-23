"""GPU_RUN5 Phase 1: reanalyse saved GPU_RUN4 ODEBench candidates."""

from __future__ import annotations

import argparse
import json
import math
import os
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from evaluation.gpu_run5_structure import classify_formula  # noqa: E402
from gpu_run2_runtime import git_info, sha256_file, write_json  # noqa: E402
from gpu_run5.config import load_config, phase_dir, read_json, run_dir, sanitize_nonfinite, write_manifest  # noqa: E402


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
    values = [float(row[key]) for row in rows if row.get(key) is not None and math.isfinite(float(row[key]))]
    return sum(values) / len(values) if values else None


def _selected_summary(rows: list[dict]) -> dict:
    finite_ted = [float(row["normalized_ted"]) for row in rows if row.get("normalized_ted") is not None and math.isfinite(float(row["normalized_ted"]))]
    finite_recon = [float(row["reconstruction_r2"]) for row in rows if row.get("reconstruction_r2") is not None and math.isfinite(float(row["reconstruction_r2"]))]
    finite_gen = [float(row["generalization_r2"]) for row in rows if row.get("generalization_r2") is not None and math.isfinite(float(row["generalization_r2"]))]
    return {
        "n": len(rows),
        "formula_parse_valid_rate": sum(bool(row["candidate_structure"]["valid"]) for row in rows) / max(len(rows), 1),
        "record_valid_rate": sum(bool(row.get("valid")) for row in rows) / max(len(rows), 1),
        "evaluation_success_rate": sum(not row.get("failure_reason") for row in rows) / max(len(rows), 1),
        "skeleton_exact_rate": _mean(rows, "skeleton_exact"),
        "exponent_aware_skeleton_exact_rate": sum(row["exponent_aware_skeleton_exact"] for row in rows) / max(len(rows), 1),
        "normalized_ted_mean": _mean(rows, "normalized_ted"),
        "normalized_ted_median": statistics.median(finite_ted) if finite_ted else None,
        "normalized_ted_finite_count": len(finite_ted),
        "failure_penalized_normalized_ted_mean": sum(
            float(row["normalized_ted"]) if row.get("normalized_ted") is not None and math.isfinite(float(row["normalized_ted"])) else 1.0
            for row in rows
        ) / max(len(rows), 1),
        "reconstruction_r2_mean": _mean(rows, "reconstruction_r2"),
        "reconstruction_r2_median": statistics.median(finite_recon) if finite_recon else None,
        "reconstruction_r2_finite_count": len(finite_recon),
        "generalization_r2_mean": _mean(rows, "generalization_r2"),
        "generalization_r2_median": statistics.median(finite_gen) if finite_gen else None,
        "generalization_r2_finite_count": len(finite_gen),
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
            "algebraically_rational_candidate_rate": sum(r["candidate_structure"]["algebraically_rational"] for r in rows) / len(rows),
            "hill_candidate_rate": sum(r["candidate_structure"]["hill_form"] for r in rows) / len(rows),
            "modulated_hill_candidate_rate": sum(r["candidate_structure"]["modulated_hill_form"] for r in rows) / len(rows),
            "sigmoid_candidate_rate": sum(r["candidate_structure"]["sigmoid_saturating_form"] for r in rows) / len(rows),
        })
    selected_form_comparison = {
        "rational_with_variable_denominator": _selected_summary([r for r in selected if r["true_structure"]["rational_with_variable_denominator"]]),
        "other": _selected_summary([r for r in selected if not r["true_structure"]["rational_with_variable_denominator"]]),
    }
    structure_flags = [
        "variable_denominator_form", "algebraically_rational", "rational_with_variable_denominator",
        "hill_form", "modulated_hill_form", "sigmoid_saturating_form",
    ]
    truth_form_system_ids = {
        flag: sorted({row["ode_id"] for row in selected if row["true_structure"][flag]})
        for flag in structure_flags
    }
    unique_truth_by_id = {row["ode_id"]: row for row in selected}
    truth_form_component_counts = {
        flag: sum(sum(bool(component[flag]) for component in row["true_structure"]["component_flags"]) for row in unique_truth_by_id.values())
        for flag in structure_flags
    }
    candidate_support_by_true_flag = []
    for flag in structure_flags:
        for flag_value in (False, True):
            rows = [row for row in candidates if bool(row["true_structure"][flag]) is flag_value]
            if not rows:
                continue
            candidate_support_by_true_flag.append({
                "truth_flag": flag,
                "truth_flag_value": flag_value,
                "n_candidates": len(rows),
                **{
                    f"candidate_{candidate_flag}_rate": sum(r["candidate_structure"][candidate_flag] for r in rows) / len(rows)
                    for candidate_flag in structure_flags
                },
            })
    selected_all_exact = sum(row["exponent_aware_skeleton_exact"] for row in selected)
    generation_selection = {
        "all_groups": len(grouped),
        "true_exponent_skeleton_in_beam_count": int(sum(truth_in_beam)),
        "selected_exponent_skeleton_exact_count": int(selected_all_exact),
        "selection_miss_count_when_exact_in_beam": int(sum(truth_in_beam) - selected_all_exact),
        "variable_denominator_groups": len(variable_group_support),
        "variable_denominator_true_exponent_skeleton_in_beam_count": int(sum(variable_group_support)),
        "interpretation": "truth-specific generation failure on variable-denominator systems" if not any(variable_group_support) else "selection is evaluable where truth support exists",
    }
    truth_support_details = []
    for key, rows in grouped.items():
        matches = [row for row in rows if row["exponent_aware_skeleton_exact"]]
        if matches:
            truth_support_details.append({
                "group": {"problem_id": key[0], "noise_sigma": key[1], "subsample_rho": key[2], "seed": key[3]},
                "selected_exact": any(row["selected"] and row["exponent_aware_skeleton_exact"] for row in rows),
                "matching_candidates": [
                    {"candidate_index": row["candidate_index"], "formula": row["candidate_formula_raw"]} for row in matches
                ],
            })
    beam_any_denominator = [any(row["candidate_structure"]["variable_denominator_form"] for row in rows) for rows in grouped.values()]
    variable_beam_any_denominator = [
        any(row["candidate_structure"]["variable_denominator_form"] for row in rows)
        for rows in grouped.values() if rows[0]["ode_id"] in variable_denominator_ids
    ]
    selected_variable_denominator = [row for row in variable_selected if row["candidate_structure"]["variable_denominator_form"]]
    unique_skeleton_counts = [len({row["candidate_structure"]["exponent_aware_skeleton"] for row in rows}) for rows in grouped.values()]
    qualitative = [
        {"ode_id": row["ode_id"], "true_formula": row["true_formula_raw"], "selected_formula": row["candidate_formula_raw"],
         "normalized_ted": row.get("normalized_ted"), "failure_reason": row.get("failure_reason")}
        for row in selected
        if row["ode_id"] in variable_denominator_ids and row["noise_sigma"] == 0.0 and row["subsample_rho"] == 0.0
    ]
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
        "truth_form_system_ids": truth_form_system_ids,
        "truth_form_component_counts": truth_form_component_counts,
        "candidate_support_by_true_flag": candidate_support_by_true_flag,
        "selected_rational_vs_other": selected_form_comparison,
        "truth_specific_generation_selection": generation_selection,
        "truth_support_details": truth_support_details,
        "support_denominators": {
            "candidate_occurrence": {"success": int(sum(row["candidate_structure"]["variable_denominator_form"] for row in candidates)), "total": len(candidates)},
            "beam_group_any": {"success": int(sum(beam_any_denominator)), "total": len(beam_any_denominator)},
            "variable_truth_beam_group_any": {"success": int(sum(variable_beam_any_denominator)), "total": len(variable_beam_any_denominator)},
            "variable_truth_selected": {"success": len(selected_variable_denominator), "total": len(variable_selected)},
            "unique_exponent_skeletons_per_beam_mean": sum(unique_skeleton_counts) / len(unique_skeleton_counts),
        },
        "qualitative_variable_denominator_panel": qualitative,
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
        "r1_truth_form_breakdown_saved": all(flag in truth_form_system_ids and flag in truth_form_component_counts for flag in structure_flags),
        "r2_candidate_support_saved": all(
            all(key in row for key in ["variable_denominator_candidate_rate", "algebraically_rational_candidate_rate", "hill_candidate_rate", "modulated_hill_candidate_rate", "sigmoid_candidate_rate"])
            for row in candidate_support_rows
        ),
        "r3_rational_comparison_saved": all(value["n"] > 0 for value in selected_form_comparison.values()),
        "retrospective_outcomes_saved": True,
        "truth_specific_beam_support_saved": len(variable_group_support) == 56,
    }
    selected = sanitize_nonfinite(selected)
    candidates = sanitize_nonfinite(candidates)
    summary = sanitize_nonfinite(summary)
    write_json(out / "selected_annotated.json", selected)
    write_json(out / "candidates_annotated.json", candidates)
    write_json(out / "decoded_support.json", summary)
    write_json(out / "go.json", go)
    status = "complete" if all(go.values()) else "incomplete"
    write_manifest(out, 1, status, go_conditions=go, summary=summary, git=git_info(), test_accessed=False)
    print(f"GPU_RUN5 Phase 1 {status}: {summary}")
    return 0 if status == "complete" else 1


if __name__ == "__main__":
    raise SystemExit(main())
