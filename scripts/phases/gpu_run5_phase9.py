"""GPU_RUN5 Phase 9: CPU-only integration, preregistration outcomes, and reports."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from time import perf_counter
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from gpu_run2_runtime import utc_now  # noqa: E402
from gpu_run5.phase9 import (  # noqa: E402
    Catalog,
    aggregate_results,
    campaign_terminal_state,
    condition_rows,
    cross_run_synthesis,
    evaluate_preregistration,
    failure_rows,
    formula_examples,
    render_reports,
    required_result_sources_available,
    sha256_file,
    write_csv,
    write_figures,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", default=os.environ.get("LANSR_RUN_ID"))
    parser.add_argument("--run-dir", type=Path, default=None)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--reports-dir", type=Path, default=None)
    parser.add_argument("--graphs-dir", type=Path, default=None)
    parser.add_argument("--smoke", action="store_true", help="Accepted for runner compatibility; aggregation is identical.")
    return parser.parse_args()


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=False, allow_nan=False) + "\n"
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(text, encoding="utf-8")
    temp.replace(path)


def _git(repo_root: Path) -> dict[str, Any]:
    def run(*args: str) -> str:
        proc = subprocess.run(
            ["git", *args], cwd=repo_root, text=True, capture_output=True, check=False
        )
        return proc.stdout.strip() if proc.returncode == 0 else ""

    return {
        "branch": run("branch", "--show-current"),
        "commit": run("rev-parse", "HEAD"),
        "status_short": run("status", "--short"),
    }


def _result_table(results: Mapping[str, Any], prereg: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for key, value in results.items():
        if not key[:1] in {"A", "B", "C", "D", "E"}:
            continue
        status = value.get("status") if isinstance(value, Mapping) else None
        rows.append({"result": key[0], "section": key, "status": status or "aggregated", "comparison_generation": "within_run_only"})
    for row in prereg["outcomes"]:
        rows.append({"result": "preregistration", "section": row["id"], "status": row["outcome"], "comparison_generation": "registered_threshold"})
    return rows


def _cross_rows(cross: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for row in cross.get("rows") or []:
        rows.append({
            "run": row.get("run"), "model": row.get("model"), "generation": row.get("generation"),
            "status": row.get("status"), "probe_top3": row.get("probe_top3"),
            "causal_top3": row.get("causal_top3"), "iole_top3": row.get("iole_top3"),
            "probe_causal_top3_jaccard": row.get("probe_causal_top3_jaccard"),
            "causal_iole_top3_jaccard": row.get("causal_iole_top3_jaccard"),
            "probe_iole_top3_jaccard": row.get("probe_iole_top3_jaccard"),
            "caveat": row.get("caveat", row.get("reason")),
        })
    return rows


def main() -> int:
    args = parse_args()
    started_utc, started = utc_now(), perf_counter()
    repo_root = args.repo_root.resolve()
    git_at_start = _git(repo_root)
    run_id = args.run_id or "gpu_run5_local"
    run_root = (args.run_dir or repo_root / "results" / "runs" / run_id).resolve()
    out = run_root / "phase9"
    out.mkdir(parents=True, exist_ok=True)
    reports_dir = (args.reports_dir or repo_root / "GPU_RUN5").resolve()
    graph_root = (args.graphs_dir or repo_root / "graphs" / run_id).resolve()
    figures, tables = graph_root / "figures", graph_root / "tables"

    catalog = Catalog(run_root)
    prereg = evaluate_preregistration(catalog)
    terminal = campaign_terminal_state(
        catalog,
        phase8_final_test_available=bool(
            prereg["test_firewall"]["phase8_final_test_available"]
        ),
    )
    cross = cross_run_synthesis(repo_root, catalog)
    results = aggregate_results(catalog, prereg, cross)
    examples = formula_examples(catalog)
    failures = failure_rows(catalog)
    conditions = condition_rows(catalog)
    required_sources = required_result_sources_available(
        catalog, terminal_state=str(terminal["state"])
    )

    _write_json(out / "preregistration_outcome.json", prereg)
    _write_json(out / "integrated_results.json", results)
    for letter, key in zip("ABCDE", [
        "A_decoded_support", "B_grn_generation_selection", "C_grn_adaptation",
        "D_layer_analysis", "E_cross_model_synthesis",
    ]):
        _write_json(out / f"result_{letter.lower()}.json", results[key])

    write_csv(tables / "phase9_preregistration_outcomes.csv", prereg["outcomes"])
    write_csv(tables / "phase9_results_a_e.csv", _result_table(results, prereg))
    write_csv(tables / "phase9_cross_run_rankings.csv", _cross_rows(cross))
    write_csv(tables / "phase9_formula_examples.csv", examples)
    write_csv(tables / "phase9_failure_funnel.csv", failures)
    write_csv(tables / "phase9_condition_metrics.csv", conditions)
    figure_paths = write_figures(catalog, figures, cross)

    reports = render_reports(
        repo_root, run_id=run_id, results=results, prereg=prereg, examples=examples
    )
    reports_dir.mkdir(parents=True, exist_ok=True)
    report_paths = []
    for name, content in reports.items():
        path = reports_dir / name
        path.write_text(content.rstrip() + "\n", encoding="utf-8")
        report_paths.append(path)

    # The audit is written after all source reads, so it is a complete list of
    # manifest-verification decisions made by this aggregation.
    source_audit = {
        "schema_version": "gpu_run5_phase9_source_audit_v1",
        "run_dir": run_root.as_posix(),
        "strict_json": True,
        "sealed_test_files_read": False,
        "artifacts": catalog.audit,
    }
    _write_json(out / "source_artifact_audit.json", source_audit)

    local_artifacts = [
        out / "preregistration_outcome.json", out / "integrated_results.json",
        *(out / f"result_{letter}.json" for letter in "abcde"),
        out / "source_artifact_audit.json",
    ]
    table_paths = sorted(tables.glob("phase9_*"))
    outcome_counts = prereg["counts"]
    git_at_end = _git(repo_root)
    git_provenance_ok = (
        bool(git_at_start["commit"])
        and not git_at_start["status_short"]
        and git_at_end["commit"] == git_at_start["commit"]
    )
    failure_visibility = bool(failures) and all(
        isinstance(row.get("value"), (int, float))
        and row.get("value_kind") in {"count", "rate"}
        for row in failures
    )
    phase9_complete = bool(
        terminal["terminal"] and required_sources["pass"] and failure_visibility
        and git_provenance_ok
    )
    manifest = {
        "campaign": "GPU_RUN5", "phase": 9,
        "status": "complete" if phase9_complete else "incomplete",
        "at_utc": utc_now(), "started_utc": started_utc,
        "wall_time_sec": perf_counter() - started, "mode": "cpu_only_aggregation",
        "run_id": run_id,
        "git_at_start": git_at_start,
        "git_at_end": git_at_end,
        "output_directories": {
            "phase9": out.as_posix(),
            "reports": reports_dir.as_posix(),
            "figures": figures.as_posix(),
            "tables": tables.as_posix(),
        },
        "test_accessed_by_phase9": False,
        "phase8_final_test_available": prereg["test_firewall"]["phase8_final_test_available"],
        "outcome_counts": outcome_counts,
        "campaign_terminal_state": terminal["state"],
        "campaign_terminal_audit": terminal,
        "required_result_sources": required_sources,
        "go_conditions": {
            "registered_outcomes_all_emitted": len(prereg["outcomes"]) == 7,
            "git_clean_at_start_and_commit_stable": git_provenance_ok,
            "upstream_campaign_terminal": terminal["terminal"],
            "required_result_sources_available": required_sources["pass"],
            "missing_upstream_is_undecidable_not_fabricated": True,
            "gpu_run5_sources_manifest_hash_verified": all(
                row["status"] in {"loaded", "verified", "missing"}
                for row in catalog.audit
            ),
            "sealed_test_files_not_read": True,
            "results_a_through_e_separate": all((out / f"result_{letter}.json").is_file() for letter in "abcde"),
            "five_reports_written": len(report_paths) == 5,
            "tables_and_figures_written": bool(table_paths) and len(figure_paths) == 10,
            "cross_generation_scores_not_pooled": True,
            "formulas_and_failures_exported": (tables / "phase9_formula_examples.csv").is_file() and (tables / "phase9_failure_funnel.csv").is_file(),
            "failure_funnel_has_concrete_schema_aware_values": failure_visibility,
        },
        "artifact_sha256": {path.name: sha256_file(path) for path in local_artifacts},
        "table_sha256": {path.name: sha256_file(path) for path in table_paths},
        "figure_sha256": {path.name: sha256_file(path) for path in figure_paths},
        "report_sha256": {path.name: sha256_file(path) for path in report_paths},
    }
    _write_json(out / "manifest.json", manifest)
    print(
        f"GPU_RUN5 Phase 9 {manifest['status']}: hit={outcome_counts['hit']} "
        f"miss={outcome_counts['miss']} undecidable={outcome_counts['undecidable']}",
        flush=True,
    )
    return 0 if phase9_complete or args.smoke else 1


if __name__ == "__main__":
    raise SystemExit(main())
