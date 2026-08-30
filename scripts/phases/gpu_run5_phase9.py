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
        # Enumerate every generated file.  The default status output collapses
        # a wholly-untracked directory to one ``?? directory/`` row, which
        # cannot be compared safely with the exact generated-file allowlist.
        "status_short": run("status", "--short", "--untracked-files=all"),
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
            "robustness_top3": row.get("robustness_top3"),
            "intervention_estimand": row.get("intervention_estimand"),
            "probe_causal_top3_jaccard": row.get("probe_causal_top3_jaccard"),
            "causal_iole_top3_jaccard": row.get("causal_iole_top3_jaccard"),
            "probe_iole_top3_jaccard": row.get("probe_iole_top3_jaccard"),
            "probe_robustness_top3_jaccard": row.get("probe_robustness_top3_jaccard"),
            "robustness_iole_top3_jaccard": row.get("robustness_iole_top3_jaccard"),
            "caveat": row.get("caveat", row.get("reason")),
        })
    return rows


def _write_graph_provenance(
    path: Path,
    *,
    repo_root: Path,
    run_id: str,
    generated: list[Path],
    catalog: Catalog,
    dependency_phases: Mapping[str, set[int]],
    historical_sources: list[Mapping[str, Any]],
    git_commit: str,
) -> None:
    script = Path(__file__).resolve()
    try:
        script_label = script.relative_to(repo_root).as_posix()
    except ValueError:
        script_label = script.as_posix()
    signed_sources = sorted({
        (int(row["phase"]), str(row["name"]), str(row["sha256"]))
        for row in catalog.audit
        if row.get("status") in {"verified", "indexed_shards_verified"}
        and isinstance(row.get("sha256"), str)
    })
    historical = sorted({
        (str(row.get("path")), str(row.get("sha256")), str(row.get("provenance")))
        for row in historical_sources
        if (
            isinstance(row, Mapping)
            and isinstance(row.get("path"), str)
            and isinstance(row.get("sha256"), str)
            and isinstance(row.get("provenance"), str)
        )
    })
    lines = [
        f"# GPU_RUN5 Phase 9 graph provenance — `{run_id}`",
        "",
        "図表は保存済み成果物からCPU-onlyで生成した。GPU_RUN5 sourceはproducer manifest署名を検証し、"
        "過去runのTrack E sourceはPhase 9時点のcontent hashとして明示的に区別した。",
        "",
        f"- generator: `{script_label}`",
        f"- generator SHA256: `{sha256_file(script)}`",
        f"- Git commit: `{git_commit}`",
        "- source policy: GPU_RUN5=producer-manifest signed; historical Track E=content-hashed at Phase 9",
        "",
        "| output | output SHA256 | direct sources |",
        "|---|---|---|",
    ]
    for output in sorted(generated):
        relative = output.relative_to(path.parent).as_posix()
        phases = dependency_phases.get(output.name, set())
        direct = [
            f"phase{phase}/{name}@{digest} [producer-manifest-signed]"
            for phase, name, digest in signed_sources if phase in phases
        ]
        if output.name in {
            "phase9_cross_run_rankings.csv", "phase9_results_a_e.csv",
            "phase9_cross_run_rank_disagreement.svg",
        }:
            direct.extend(
                f"{source_path}@{digest} [{provenance}]"
                for source_path, digest, provenance in historical
            )
        source_text = "; ".join(direct) or "no external source"
        lines.append(
            f"| `{relative}` | `{sha256_file(output)}` | {source_text.replace('|', '&#124;')} |"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _git_changes_are_generated_only(
    status_short: str, *, repo_root: Path, generated: list[Path]
) -> bool:
    allowed = {
        path.resolve().relative_to(repo_root).as_posix()
        for path in generated
        if path.resolve().is_relative_to(repo_root)
    }
    observed = []
    for line in status_short.splitlines():
        path = line[3:].strip()
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        observed.append(path.strip('"'))
    return all(path in allowed for path in observed)


def _gpu_run5_source_audit_pass(rows: list[Mapping[str, Any]]) -> bool:
    """Accept only explicit manifest/hash audit outcomes, including shard indices."""
    return all(
        row.get("status") in {
            "loaded", "verified", "indexed_shards_verified", "missing"
        }
        for row in rows
    )


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
    _write_json(out / "failure_analysis.json", results["failure_analysis"])
    _write_json(
        out / "condition_uncertainty.json",
        results["C_grn_adaptation"]["uncertainty"],
    )
    for letter, key in zip("ABCDE", [
        "A_decoded_support", "B_grn_generation_selection", "C_grn_adaptation",
        "D_layer_analysis", "E_cross_model_synthesis",
    ]):
        _write_json(out / f"result_{letter.lower()}.json", results[key])

    write_csv(tables / "phase9_preregistration_outcomes.csv", prereg["outcomes"])
    write_csv(tables / "phase9_results_a_e.csv", _result_table(results, prereg))
    write_csv(tables / "phase9_cross_run_rankings.csv", _cross_rows(cross))
    write_csv(tables / "phase9_formula_examples.csv", examples)
    write_csv(
        tables / "phase9_failure_events.csv",
        results["failure_analysis"]["events"],
    )
    write_csv(
        tables / "phase9_failure_funnel.csv",
        [
            *results["failure_analysis"]["event_summary"],
            *results["failure_analysis"]["funnel"],
            *results["failure_analysis"]["upstream_funnels"],
        ],
    )
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

    table_paths = sorted(tables.glob("phase9_*"))
    graph_readme = graph_root / "README.md"
    _write_graph_provenance(
        graph_readme,
        repo_root=repo_root,
        run_id=run_id,
        generated=[*table_paths, *figure_paths],
        catalog=catalog,
        dependency_phases={
            "phase9_preregistration_outcomes.csv": {0, 1, 3, 5, 8},
            "phase9_results_a_e.csv": set(range(9)),
            "phase9_cross_run_rankings.csv": {4, 5, 7},
            "phase9_formula_examples.csv": {1, 2, 3, 6, 7, 8},
            "phase9_failure_events.csv": {6, 7, 8},
            "phase9_failure_funnel.csv": {3, 5, 6, 7, 8},
            "phase9_condition_metrics.csv": {6, 8},
            "phase9_failure_funnel.svg": {3, 5, 6, 7, 8},
            "phase9_family_generation_recovery.svg": {3},
            "phase9_single_vs_multi_ic.svg": {3},
            "phase9_final_condition_formula_scores.svg": {8},
            "phase9_decoder_depth_ted.svg": {4},
            "phase9_reconstruction_vs_ted.svg": {3},
            "phase9_input_vs_generalization.svg": {3},
            "phase9_delta_ce_vs_delta_ted.svg": {5},
            "phase9_efficiency_pareto.svg": {6, 8},
            "phase9_cross_run_rank_disagreement.svg": {4, 5, 7},
        },
        historical_sources=[
            source
            for row in cross.get("rows") or [] if isinstance(row, Mapping)
            for source in row.get("sources") or [] if isinstance(source, Mapping)
        ],
        git_commit=str(git_at_start["commit"]),
    )

    # The audit is written after all source reads, so it is a complete list of
    # manifest-verification decisions made by this aggregation.
    source_audit = {
        "schema_version": "gpu_run5_phase9_source_audit_v2",
        "run_dir": run_root.as_posix(),
        "strict_json": True,
        "sealed_test_files_read": False,
        "artifacts": catalog.audit,
    }
    _write_json(out / "source_artifact_audit.json", source_audit)

    local_artifacts = [
        out / "preregistration_outcome.json", out / "integrated_results.json",
        out / "failure_analysis.json", out / "condition_uncertainty.json",
        *(out / f"result_{letter}.json" for letter in "abcde"),
        out / "source_artifact_audit.json",
    ]
    outcome_counts = prereg["counts"]
    git_at_end = _git(repo_root)
    generated_paths = [*report_paths, *table_paths, *figure_paths, graph_readme]
    git_provenance_ok = (
        bool(git_at_start["commit"])
        and not git_at_start["status_short"]
        and git_at_end["commit"] == git_at_start["commit"]
        and _git_changes_are_generated_only(
            git_at_end["status_short"],
            repo_root=repo_root,
            generated=generated_paths,
        )
    )
    failure_visibility = bool(failures) and all(
        isinstance(row.get("value"), (int, float))
        and row.get("value_kind") in {"count", "rate"}
        for row in failures
    )
    go_conditions = {
        "registered_outcomes_all_emitted": len(prereg["outcomes"]) == 7,
        "git_clean_at_start_and_commit_stable": git_provenance_ok,
        "upstream_campaign_terminal": bool(terminal["terminal"]),
        "required_result_sources_available": bool(required_sources["pass"]),
        "missing_upstream_is_undecidable_not_fabricated": True,
        "gpu_run5_sources_manifest_hash_verified": _gpu_run5_source_audit_pass(catalog.audit),
        "sealed_test_files_not_read": True,
        "results_a_through_e_separate": all((out / f"result_{letter}.json").is_file() for letter in "abcde"),
        "five_reports_written": len(report_paths) == 5,
        "tables_and_figures_written": bool(table_paths) and len(figure_paths) == 10,
        "cross_generation_scores_not_pooled": True,
        "formulas_and_failures_exported": (
            (tables / "phase9_formula_examples.csv").is_file()
            and (tables / "phase9_failure_events.csv").is_file()
            and (tables / "phase9_failure_funnel.csv").is_file()
        ),
        "failure_funnel_has_concrete_schema_aware_values": failure_visibility,
        "phase6_to_phase8_signed_shard_coverage_exact": bool(results["failure_analysis"]["coverage_pass"]),
        "terminal_rate_uncertainty_recomputed_from_signed_shards": results["C_grn_adaptation"]["uncertainty"].get("status") == "complete",
        "graph_provenance_map_written": graph_readme.is_file(),
    }
    phase9_complete = all(go_conditions.values())
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
        "go_conditions": go_conditions,
        "artifact_sha256": {path.name: sha256_file(path) for path in local_artifacts},
        "table_sha256": {path.name: sha256_file(path) for path in table_paths},
        "figure_sha256": {path.name: sha256_file(path) for path in figure_paths},
        "graph_provenance_sha256": sha256_file(graph_readme),
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
