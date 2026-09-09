"""GPU_RUNclaude1 C0001 Phase 1: Part A (v2 §7).

Frozen ordering, mechanically enforced (v2 §7.2 step 3, §14 item 8): the
component strata and the realized-|H| ladder are written and hashed to disk
*before* :func:`gpu_runclaude1.partA_driver.score_cell` is ever called, and
that function refuses to run without the resulting
:class:`~gpu_runclaude1.strata.StrataFrozenToken`.

``--dry-run`` writes a dummy manifest only. ``--smoke`` computes the real
strata/ladder/control-battery over the full 80-system corpus (cheap, CPU-only,
no candidates), then runs the real matching cascade -- gated by the frozen
token -- over a small subset of cells (default 3) rather than all 960, and
verifies M0 reproduction only on that subset. It does not run the full
47,987-candidate pass; that is Stage 6/7's job.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from gpu_runclaude1 import config as c0001_config  # noqa: E402
from gpu_runclaude1.controls import run_all_controls  # noqa: E402
from gpu_runclaude1.endpoints import ComponentCellResult, compute_primary_endpoint, compute_secondaries  # noqa: E402
from gpu_runclaude1.io_allowlist import (  # noqa: E402
    install_sealed_audit_hook,
    GPU_RUN5_ALLOWLIST_RELATIVE,
    InstrumentedOpener,
    enumerate_validation_cells,
    sealed_open_guard,
)
from gpu_runclaude1.agreement import run_in_pass_census  # noqa: E402
from gpu_runclaude1.ladder import build_ladder_realized_artifact
from gpu_runclaude1.matcher import COULD_NOT_EVALUATE, ComponentMatch, MatchResult, audit_monotonicity
from gpu_runclaude1.partA_driver import score_cells_parallel_resumable
from gpu_runclaude1.strata import assign_strata, require_strata_frozen, write_component_strata

GPU_RUN5_SOURCE_RUN = ROOT / "results" / "runs" / "gpu_run5_20260823_ddd267b0"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="GPU_RUNclaude1 C0001 Phase 1 (Part A)")
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--smoke-cells", type=int, default=3)
    parser.add_argument("--n-workers", type=int, default=6, help="process-based parallelism for the matching pass (v2 §3)")
    parser.add_argument("--census-every", type=int, default=100, help="in-pass double-computation census interval (v2.1 §7.4 item b)")
    return parser.parse_args()


def _control_summary(results: dict) -> dict:
    return {
        name: {"n_eligible": r.n_eligible, "n_pass": r.n_pass, "rate": r.rate, "note": r.note, "extra": r.extra}
        for name, r in results.items()
    }


def _match_result_from_dict(d: dict) -> MatchResult:
    """Reconstruct a MatchResult (the reverse of dataclasses.asdict) from the
    JSON-round-tripped dict form the resumable parallel driver returns, so
    downstream analysis (audit_monotonicity) can reuse the exact same
    library function unchanged rather than a duplicated dict-shaped copy.
    """
    components = tuple(ComponentMatch(**c) for c in d["components"])
    return MatchResult(
        component_count_match=d["component_count_match"],
        m0_system=d["m0_system"],
        m1_system=d["m1_system"],
        m3_system=d["m3_system"],
        m0_any_components=d["m0_any_components"],
        components=components,
        valid=d["valid"],
        failure_reason=d["failure_reason"],
    )


def _verify_m0_reproduction_dict(cell: dict, results: list[dict]) -> dict:
    """Same check as gpu_runclaude1.partA_driver.verify_m0_reproduction (v2
    §7.6), adapted for the JSON-round-tripped dict form
    score_cells_parallel_resumable returns (attribute access -> key access).
    """
    candidates = cell.get("candidates", [])
    mismatches = []
    for index, (candidate, result) in enumerate(zip(candidates, results)):
        stored_system = candidate.get("exponent_aware_skeleton_exact")
        if stored_system is not None and float(stored_system) != result["m0_system"]:
            mismatches.append({"candidate_index": index, "level": "system", "stored": stored_system, "recomputed": result["m0_system"]})
        stored_components = candidate.get("component_exponent_aware_skeleton_exact") or []
        for component_index, stored_value in enumerate(stored_components):
            if component_index >= len(result["components"]):
                continue
            recomputed = result["components"][component_index]["m0"]
            if float(stored_value) != recomputed:
                mismatches.append(
                    {"candidate_index": index, "level": "component", "component_index": component_index, "stored": stored_value, "recomputed": recomputed}
                )
    return {"cell_id": cell.get("cell_id"), "n_candidates": len(candidates), "n_mismatches": len(mismatches), "mismatches": mismatches, "ok": not mismatches}


def main() -> int:
    args = parse_args()
    run_root = c0001_config.resolve_run_dir_for_phase(args.run_id, is_first_phase=False)
    out_dir = c0001_config.phase_dir(run_root, 1)

    if args.dry_run:
        c0001_config.write_manifest(out_dir, 1, "dry_run", note="dry-run: no data touched")
        print(f"Phase 1 dry-run: {out_dir}")
        return 0

    install_sealed_audit_hook()  # v2.1 §2.4 item 7a: process-wide, before any file access
    allowlist = [GPU_RUN5_SOURCE_RUN / rel for rel in GPU_RUN5_ALLOWLIST_RELATIVE]
    opener = InstrumentedOpener(allowlist)
    cell_paths = enumerate_validation_cells(GPU_RUN5_SOURCE_RUN / "phase3")
    opener.extend_allowlist(cell_paths)

    with sealed_open_guard():
        validation_rows = opener.read_json(GPU_RUN5_SOURCE_RUN / "phase2" / "validation.json")

        # --- Step 1 (v2 §7.2 step 1): strata, written and hashed first. ---
        records = assign_strata(validation_rows)
        strata_path = out_dir / "component_strata.json"
        strata_payload = write_component_strata(strata_path, records)

        # --- Step 2 (v2 §7.2 step 2): the realized-|H| ladder, from |H| alone. ---
        ladder_path = out_dir / "partA_ladder_realized.json"
        ladder_payload = build_ladder_realized_artifact(strata_payload["n_h"], strata_payload["sha256_of_component_assignment"])
        ladder_path.write_text(json.dumps(ladder_payload, indent=2), encoding="utf-8")

        # --- Step 3: only now may a match indicator be computed. ---
        strata_token = require_strata_frozen(strata_path, ladder_path)

        if args.smoke:
            # Keep the smoke path fast (one system per family, 8 of 80): the
            # control battery's SymPy cost is per-system, not per-cell, so
            # the full 80-system battery is real Stage 6/7 work, not a smoke
            # demonstration. This still exercises every control's code path.
            seen_families: set[str] = set()
            control_rows = []
            for row in validation_rows:
                if row["family"] not in seen_families:
                    seen_families.add(row["family"])
                    control_rows.append(row)
        else:
            control_rows = validation_rows
        print(f"Running control battery over {len(control_rows)} systems...", flush=True)
        controls = run_all_controls(control_rows, stratum_lookup=strata_token.component_lookup)
        print("Control battery complete.", flush=True)

        # v2.1 §7.10 item 4 / §7.7.3: gate the HARD ABORT controls (PC0,
        # PC4, PC2a harness-identity) *before* spending the endpoint-pass
        # budget. On the real corpus (control_rows == all 80 systems, i.e.
        # a non-smoke run) this stops here for ~0.5 core-h rather than
        # burning the full ~8.7 core-h pass only to report undecidable.
        # Under --smoke, control_rows is an 8-system subset for speed, so
        # PC4's absolute-count thresholds (frozen against the full 170-
        # component corpus) cannot be expected to pass here; the gate is
        # still evaluated and reported, but only enforced (aborts the run)
        # on a full, non-smoke invocation.
        hard_abort_reasons = []
        if controls["PC0"].n_pass != controls["PC0"].n_eligible:
            hard_abort_reasons.append("PC0 failed: matcher broken")
        if controls["PC2a"].n_pass != controls["PC2a"].n_eligible:
            hard_abort_reasons.append("PC2a failed: harness differs from the audited one")
        if not controls["PC4"].extra.get("gates_ok"):
            hard_abort_reasons.append("PC4 failed: gain indicator not demonstrated")
        if hard_abort_reasons and not args.smoke:
            c0001_config.write_manifest(
                out_dir,
                1,
                "undecidable",
                go_conditions={"hard_abort": True, "reasons": hard_abort_reasons},
                n_h=strata_payload["n_h"],
                n_l=strata_payload["n_l"],
            )
            (out_dir / "partA_controls.json").write_text(json.dumps(_control_summary(controls), indent=2), encoding="utf-8")
            print(f"Phase 1 undecidable (hard abort before endpoint pass): {hard_abort_reasons}")
            return 1

        cells_for_matching_paths = cell_paths[: args.smoke_cells] if args.smoke else cell_paths
        # Read every cell once, through the guarded opener, in the main
        # process (v2.1 §2.4: workers never touch the filesystem).
        cells_for_matching = [opener.read_json(p) for p in cells_for_matching_paths]

        # --- Matching pass: process-based parallelism, resumable, with
        # per-cell failure isolation (v2 §3; F4). Cache dir is inside this
        # run's own phase1 output, so a killed-and-restarted invocation of
        # this same run does not recompute already-scored cells. ---
        n_workers = 1 if args.smoke else args.n_workers
        cache_dir = out_dir / "cell_cache"
        outcomes = score_cells_parallel_resumable(
            cells_for_matching, strata_token, cache_dir=cache_dir, n_workers=n_workers
        )

        reproduction_reports = []
        component_cell_results: dict[tuple, ComponentCellResult] = {}
        monotonicity_inputs = []
        cell_failures = []
        # Frozen deterministic enumeration order for the in-pass census
        # (v2.1 §7.4 item b): cells in cell_paths order, candidates in
        # stored order, components in index order.
        census_triples = []
        global_triple_index = 0
        for cell, outcome in zip(cells_for_matching, outcomes):
            if not outcome["ok"]:
                cell_failures.append({"cell_id": outcome["cell_id"], "error_type": outcome["error_type"], "error_message": outcome["error_message"]})
                continue
            results = outcome["results"]  # list[dict], JSON-round-tripped MatchResult
            reproduction_reports.append(_verify_m0_reproduction_dict(cell, results))
            system_id = cell["system_id"]
            family = cell["family"]
            for candidate, result in zip(cell.get("candidates", []), results):
                monotonicity_inputs.append((f"{cell['cell_id']}", _match_result_from_dict(result)))
                true_infix = str(cell["true_formula"])
                candidate_infix = str(candidate.get("candidate_formula_raw") or "")
                census_triples.append((global_triple_index, true_infix, candidate_infix))
                global_triple_index += 1
                for component in result["components"]:
                    key = (system_id, component["component_index"])
                    stratum = strata_token.component_lookup.get(key, "L")
                    existing = component_cell_results.get(key)
                    m0_any = int(component["m0"] == 1.0) or (existing.m0_any if existing else 0)
                    m3_any = int(component["m3"] == 1.0) or (existing.m3_any if existing else 0)
                    n_cne = int(component["match_outcome_m3"] == COULD_NOT_EVALUATE) + (existing.n_could_not_evaluate if existing else 0)
                    n_scored = 1 + (existing.n_scored if existing else 0)
                    component_cell_results[key] = ComponentCellResult(
                        system_id=system_id,
                        family=family,
                        component_index=component["component_index"],
                        stratum=stratum,
                        m0_any=m0_any,
                        m3_any=m3_any,
                        n_could_not_evaluate=n_cne,
                        n_scored=n_scored,
                    )

        # In-pass 1-in-100 double-computation census (v2.1 §7.4 item b,
        # A2-S6c), run immediately after the pass that produced these
        # exact triples, in this same phase invocation.
        census = run_in_pass_census(census_triples, every=args.census_every)

    monotonicity = audit_monotonicity(monotonicity_inputs, minor_max_rate=0.001, major_max_rate=0.01)
    components = list(component_cell_results.values())
    primary = compute_primary_endpoint(components, bootstrap_resamples=2000 if args.smoke else 10000, bootstrap_seed=20260909)
    secondaries = compute_secondaries(components)

    n_reproduction_mismatches = sum(r["n_mismatches"] for r in reproduction_reports)
    go = {
        "strata_written_before_matching": True,  # mechanically true: score_cell raised TypeError otherwise
        "m0_reproduction_ok_on_scored_subset": n_reproduction_mismatches == 0,
        "pc0_ok": controls["PC0"].n_pass == controls["PC0"].n_eligible,
        # v2.1 §7.10 item 4 / §7.7.3: PC0, PC4 and PC2a are HARD ABORT gates,
        # evaluated and enforced *before* this point in the script (the
        # matching pass never starts unless these already passed, so a hard
        # abort on the real 80-system corpus costs only the ~0.5 core-h
        # control battery, not the ~8.7 core-h endpoint pass).
        "pc4_gates_ok": controls["PC4"].extra.get("gates_ok"),
        "pc2a_harness_identity_ok": controls["PC2a"].n_pass == controls["PC2a"].n_eligible,
        "monotonicity_severity": monotonicity.severity,
        "m3_implementation_agreement_ok": census["ok"],
        "n_cell_failures": len(cell_failures),
        "reduced_scope_smoke": args.smoke,
    }
    status = "complete" if (go["m0_reproduction_ok_on_scored_subset"] and go["pc0_ok"] and not cell_failures) else "incomplete"

    (out_dir / "partA_controls.json").write_text(json.dumps(_control_summary(controls), indent=2), encoding="utf-8")
    (out_dir / "partA_cell_failures.json").write_text(json.dumps(cell_failures, indent=2), encoding="utf-8")
    (out_dir / "m3_implementation_agreement_census.json").write_text(
        json.dumps({k: v for k, v in census.items() if k != "disagreements"} | {"disagreements_sample": census["disagreements"][:20]}, indent=2),
        encoding="utf-8",
    )
    (out_dir / "m0_reproduction.json").write_text(
        json.dumps({"n_cells_checked": len(reproduction_reports), "n_mismatches": n_reproduction_mismatches, "reports": reproduction_reports}, indent=2),
        encoding="utf-8",
    )
    (out_dir / "matcher_monotonicity.json").write_text(
        json.dumps(
            {
                "n_checked": monotonicity.n_checked,
                "n_violations": monotonicity.n_violations,
                "violation_rate": monotonicity.violation_rate,
                "severity": monotonicity.severity,
                "violations_sample": monotonicity.violations[:50],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (out_dir / "partA_endpoints.json").write_text(
        json.dumps(
            {
                "prior_information_disclosed": "GPU_RUNclaude1/plans/C0001_preregistration_v2.md §0",
                "primary": {
                    "n_h": primary.n_h,
                    "k_gains": primary.k_gains,
                    "ladder_cutpoint": primary.ladder_cutpoint,
                    "verdict": primary.verdict,
                    "wilson_95": list(primary.wilson_95),
                    "cluster_bootstrap": {
                        "point_estimate": primary.cluster_bootstrap.point_estimate,
                        "ci_low": primary.cluster_bootstrap.ci_low,
                        "ci_high": primary.cluster_bootstrap.ci_high,
                        "n_resamples": primary.cluster_bootstrap.n_resamples,
                        "seed": primary.cluster_bootstrap.seed,
                    },
                    "family_wilson": list(primary.family_wilson),
                    "bound_of_record": list(primary.bound_of_record),
                    "bound_of_record_method": primary.bound_of_record_method,
                    "could_not_evaluate_rate": primary.could_not_evaluate_rate,
                    "sensitivity_agrees": primary.sensitivity_agrees,
                    "verdict_scope_sentence": (
                        "conditional on the single initial condition per system stored in GPU_RUN5 "
                        "phase 3, and on the 10 distinct conditioning payloads its 12 cells realize; "
                        "scope reduced under --smoke to the first N cells only, not the full 960."
                        if args.smoke
                        else "conditional on the single initial condition per system stored in GPU_RUN5 "
                        "phase 3, and on the 10 distinct conditioning payloads its 12 cells realize."
                    ),
                },
                "secondaries": {
                    "l_stratum_gain_rate": secondaries.l_stratum_gain_rate,
                    "l_stratum_n": secondaries.l_stratum_n,
                    "h_minus_l_difference": secondaries.h_minus_l_difference,
                    "m3_level_overall": secondaries.m3_level_overall,
                    "m3_level_h": secondaries.m3_level_h,
                    "m3_level_l": secondaries.m3_level_l,
                },
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    c0001_config.write_manifest(
        out_dir, 1, status, go_conditions=go, n_h=strata_payload["n_h"], n_l=strata_payload["n_l"], n_cells_scored=len(cells_for_matching)
    )
    print(f"Phase 1 {status}: {out_dir}")
    if status != "complete":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
