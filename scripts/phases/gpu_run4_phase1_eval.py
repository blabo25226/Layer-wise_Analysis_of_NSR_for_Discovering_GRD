"""GPU_RUN4 Phase 1: freeze symbolic evaluation before the main experiment."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from gpu_run4.cli import (  # noqa: E402
    common_parser,
    dummy_phase_output,
    require_previous,
    write_phase_manifest,
)
from gpu_run4.formulas import (  # noqa: E402
    compare_formulas,
    evaluate_gold_cases,
    instantiate_odebench_item,
    singularity_probe,
    timeout_probe,
)
from gpu_run4.records import make_formula_record  # noqa: E402
from gpu_run4_runtime import (  # noqa: E402
    load_gpu_run4_configs,
    load_odebench_equations,
    odebench_summary,
    require_python_310,
    resolve_run_dir,
    utc_now,
    write_json,
)


NORMALIZED_TED_DEFINITION = "ted_raw / (size_true + size_pred)"


def parse_args():
    return common_parser("GPU_RUN4 Phase 1 evaluation / canonicalization validation").parse_args()


def _jsonable_gold(row: dict) -> dict:
    skip = {"components"}
    return {key: value for key, value in row.items() if key not in skip}


def main() -> int:
    args = parse_args()
    require_python_310()
    config = load_gpu_run4_configs()
    run_dir = resolve_run_dir(args.run_id, config=config)
    out_dir = run_dir / "phase1"
    out_dir.mkdir(parents=True, exist_ok=True)
    if args.dry_run:
        dummy_phase_output(out_dir, 1, extra={"note": "dry-run evaluation freeze only"})
        print(f"Phase 1 dry-run: {out_dir}")
        return 0

    require_previous(run_dir, "phase0/preflight.json")
    equations = load_odebench_equations()
    summary = odebench_summary(equations)
    parsed_rows = []
    identity_records = []
    n_valid = 0
    n_identity_exact = 0
    n_prefix_roundtrip = 0
    for item in equations:
        parsed = instantiate_odebench_item(item)
        identity = compare_formulas(parsed["true_formula_instantiated"], parsed["true_formula_instantiated"])
        roundtrip = compare_formulas(
            parsed["true_formula_instantiated"],
            parsed["true_formula_prefix"],
            pred_as_prefix=True,
        )
        parsed["identity_canonical_exact"] = identity["canonical_exact"]
        parsed["identity_symbolic_equivalent"] = identity["symbolic_equivalent"]
        parsed["identity_ted_raw"] = identity["ted_raw"]
        parsed["identity_normalized_ted"] = identity["normalized_ted"]
        parsed["prefix_roundtrip_canonical_exact"] = roundtrip["canonical_exact"]
        parsed["prefix_roundtrip_failure"] = roundtrip["failure_reason"]
        parsed_rows.append(parsed)
        if parsed["valid"]:
            n_valid += 1
        if identity["canonical_exact"] == 1.0:
            n_identity_exact += 1
        if roundtrip["canonical_exact"] == 1.0:
            n_prefix_roundtrip += 1
        identity_records.append(
            make_formula_record(
                problem_id=f"odebench_{parsed['id']}",
                benchmark="odebench",
                system_name=parsed["system_name"],
                dimension=parsed["dimension"],
                split="validation",
                condition="phase1_identity",
                true_formula_raw=parsed["true_formula_raw"],
                true_formula_prefix=parsed["true_formula_prefix"],
                true_formula_canonical=parsed["true_formula_canonical"],
                true_formula_skeleton=parsed["true_formula_skeleton"],
                candidate_index=0,
                candidate_formula_raw=parsed["true_formula_instantiated"],
                candidate_formula_canonical=parsed["true_formula_canonical"],
                candidate_formula_skeleton=parsed["true_formula_skeleton"],
                selected=True,
                reconstruction_r2=None,
                generalization_r2=None,
                canonical_exact=identity["canonical_exact"],
                skeleton_exact=identity["skeleton_exact"],
                symbolic_equivalent=identity["symbolic_equivalent"],
                ted_raw=identity["ted_raw"],
                ted_skeleton=identity["ted_skeleton"],
                complexity=parsed["complexity"],
                valid=parsed["valid"],
                failure_reason=parsed["failure_reason"],
                wall_time=None,
                beam_size=None,
                beam_temperature=None,
                normalized_ted=identity["normalized_ted"],
                true_formula_infix=parsed.get("true_formula_infix"),
                prefix_roundtrip_canonical_exact=roundtrip["canonical_exact"],
            )
        )

    gold_rows = evaluate_gold_cases()
    timeout = timeout_probe()
    singularity = singularity_probe()
    gold_ok = all(row["ok"] for row in gold_rows)
    equivalent_names = {
        "commutative_add",
        "commutative_mul",
        "associative_add",
        "reciprocal_as_inv",
        "negative_constant",
        "sub_as_add_neg",
    }
    different_names = {
        "component_order_preserved",
        "intentionally_different_sign",
        "intentionally_different_variable",
        "skeleton_ignores_constant",
        "parse_failure_recorded",
    }
    gold_equivalents_match = all(row["ok"] for row in gold_rows if row["name"] in equivalent_names)
    intentionally_different_do_not_match = all(row["ok"] for row in gold_rows if row["name"] in different_names)
    component_order = next(row for row in gold_rows if row["name"] == "component_order_preserved")
    parse_failure = next(row for row in gold_rows if row["name"] == "parse_failure_recorded")
    invalid_without_reason = [
        row["id"] for row in parsed_rows if not row["valid"] and not row.get("failure_reason")
    ]

    go = {
        "gold_equivalents_match": gold_equivalents_match,
        "intentionally_different_do_not_match": intentionally_different_do_not_match,
        "component_order_preserved": bool(component_order["ok"])
        and component_order["symbolic_equivalent"] == 0.0
        and component_order["component_count_match"] is True,
        "failures_saved_with_reason": bool(parse_failure["ok"])
        and parse_failure["failure_reason"] == "ParseError"
        and not invalid_without_reason,
        "odebench_all_parsed": n_valid == summary["n_systems"] == 63,
        "odebench_identity_ted_zero": n_identity_exact == n_valid,
        "prefix_roundtrip_ok": n_prefix_roundtrip == n_valid,
        "timeout_recorded": bool(timeout["ok"]),
        "singularity_recorded": bool(singularity["ok"]),
        "gold_suite_ok": gold_ok,
    }
    status = "complete" if all(go.values()) else "incomplete"
    payload = {
        "phase": 1,
        "status": status,
        "campaign": "GPU_RUN4",
        "at_utc": utc_now(),
        "normalized_ted_definition": NORMALIZED_TED_DEFINITION,
        "odebench": summary,
        "n_parsed": len(parsed_rows),
        "n_valid": n_valid,
        "n_identity_exact": n_identity_exact,
        "n_prefix_roundtrip": n_prefix_roundtrip,
        "invalid_without_reason": invalid_without_reason,
        "go_conditions": go,
        "gold_failed": [row["name"] for row in gold_rows if not row["ok"]],
        "parse_failures": [
            {"id": row["id"], "system_name": row["system_name"], "failure_reason": row["failure_reason"]}
            for row in parsed_rows
            if not row["valid"]
        ],
        "timeout": timeout,
        "singularity": singularity,
    }
    write_json(out_dir / "odebench_parsed.json", parsed_rows)
    write_json(out_dir / "gold_cases.json", [_jsonable_gold(row) for row in gold_rows])
    write_json(out_dir / "timeout.json", timeout)
    write_json(out_dir / "singularity.json", singularity)
    write_json(out_dir / "identity_records.json", identity_records)
    write_json(out_dir / "go.json", go)
    write_json(out_dir / "eval.json", payload)
    write_phase_manifest(out_dir, payload)
    print(f"Phase 1 {status}: {out_dir / 'eval.json'}")
    if not all(go.values()):
        failed = [name for name, ok in go.items() if not ok]
        print(f"Go conditions failed: {failed}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
