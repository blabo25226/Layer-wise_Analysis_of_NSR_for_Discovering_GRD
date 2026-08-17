"""Recompute structural formula metrics for a GPU_RUN3 run under one canonicalization.

Records written by different phases can predate a canonicalization change (for
example the numeric-identity folding that makes `0 + x` match `x`). Rather than
editing stored records in place, this pass re-derives exact / skeleton /
symbolic-equivalence / TED from the stored `prefix` and `true` formula of every
record and writes them alongside, so the whole campaign can be reported under a
single, stated definition.

The original recorded values are preserved and carried through as
`*_as_recorded`, so the effect of the change is auditable.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from gpu_run3.formulas import compare_formulas, parse_to_prefix  # noqa: E402
from gpu_run3.ted import IDENTITY_ATOL, NUMERIC_SIGNIFICANT_DIGITS  # noqa: E402
from gpu_run3_runtime import load_gpu_run3_configs, resolve_run_dir, write_json  # noqa: E402


def parse_args():
    parser = argparse.ArgumentParser(description="GPU_RUN3 structural metric recompute")
    parser.add_argument("--run-id", required=True)
    return parser.parse_args()


def _read_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _true_prefix(record: dict) -> list[str] | None:
    """Recover the ground-truth prefix from whichever field the record stored."""
    canonical = record.get("true_formula_canonical")
    if canonical:
        tokens = [t for t in str(canonical).split(",") if t]
        if tokens:
            return tokens
    raw = record.get("true_formula_raw")
    if raw:
        try:
            return parse_to_prefix(str(raw))
        except Exception:
            return None
    return None


def recompute(record: dict) -> dict | None:
    pred_prefix = [str(t) for t in (record.get("prefix") or [])]
    true_prefix = _true_prefix(record)
    if not pred_prefix or not true_prefix:
        return {
            "problem_id": record.get("problem_id"),
            "system_id": record.get("system_id"),
            "seed": record.get("seed"),
            "condition": record.get("condition"),
            "status": "skipped",
            "reason": "missing prefix" if not pred_prefix else "missing true formula",
            "exact_as_recorded": record.get("exact"),
        }
    comparison = compare_formulas(true_prefix, pred_prefix)
    return {
        "problem_id": record.get("problem_id"),
        "system_id": record.get("system_id"),
        "system_name": record.get("system_name"),
        "seed": record.get("seed"),
        "condition": record.get("condition"),
        "status": "recomputed",
        "true_formula_raw": record.get("true_formula_raw"),
        "pred_formula_raw": record.get("pred_formula_raw"),
        "true_canonical_expr": comparison.get("true_canonical_expr"),
        "pred_canonical_expr": comparison.get("pred_canonical_expr"),
        "exact": comparison.get("exact"),
        "skeleton": comparison.get("skeleton"),
        "symbolic_equivalent": comparison.get("symbolic_equivalent"),
        "ted_raw": comparison.get("ted_raw"),
        "ted_skeleton": comparison.get("ted_skeleton"),
        "ted_variable_aware": comparison.get("ted_variable_aware"),
        "failure_reason": comparison.get("failure_reason"),
        "exact_as_recorded": record.get("exact"),
        "skeleton_as_recorded": record.get("skeleton"),
        "ted_raw_as_recorded": record.get("ted_raw"),
        "fit_error": record.get("fit_error"),
        "valid": record.get("valid"),
    }


def main() -> int:
    args = parse_args()
    config = load_gpu_run3_configs()
    run_dir = resolve_run_dir(args.run_id, config=config)
    sources: list[tuple[str, list[dict]]] = []
    guided = run_dir / "phase2" / "guided_mcts.json"
    unguided = run_dir / "phase2" / "unguided_mcts.json"
    for path in (guided, unguided):
        if path.is_file():
            sources.append((f"phase2/{path.stem}", [json.loads(path.read_text(encoding="utf-8"))]))
    phase3 = _read_jsonl(run_dir / "phase3" / "records.jsonl")
    if phase3:
        sources.append(("phase3/records.jsonl", phase3))
    # Phase 7 / 8 store their post-fine-tuning MCTS results nested per condition.
    for relative in ("phase7/selective_ft.json", "phase8/test_conditions.json"):
        path = run_dir / relative
        if not path.is_file():
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        nested = [record for entry in payload for record in (entry.get("mcts") or [])]
        if nested:
            sources.append((relative, nested))

    rows = []
    for origin, records in sources:
        for record in records:
            result = recompute(record)
            if result is not None:
                rows.append({"origin": origin, **result})

    recomputed = [r for r in rows if r["status"] == "recomputed"]
    changed = [
        r
        for r in recomputed
        if r.get("exact") != r.get("exact_as_recorded") or r.get("ted_raw") != r.get("ted_raw_as_recorded")
    ]
    payload = {
        "run_id": args.run_id,
        "canonicalization": {
            "numeric_significant_digits": NUMERIC_SIGNIFICANT_DIGITS,
            "identity_atol": IDENTITY_ATOL,
            "folds": ["0+x -> x", "x-0 -> x", "1*x -> x", "0*x -> 0", "x/1 -> x", "x**1 -> x"],
            "sign_normalization": ["a-b -> a+neg(b)", "-1*b -> neg(b)", "neg(neg(x)) -> x"],
            "commutative_sorted": ["add", "mul"],
            "note": "Applied uniformly to every record below, regardless of the phase that wrote it.",
        },
        "n_records": len(rows),
        "n_recomputed": len(recomputed),
        "n_changed": len(changed),
        "n_exact": sum(1 for r in recomputed if r.get("exact") == 1.0),
        "n_exact_as_recorded": sum(1 for r in recomputed if r.get("exact_as_recorded") == 1.0),
        "n_skeleton": sum(1 for r in recomputed if r.get("skeleton") == 1.0),
        "records": rows,
    }
    out_path = run_dir / "structural_metrics_recomputed.json"
    write_json(out_path, payload)
    print(
        f"wrote {out_path}: {payload['n_recomputed']} recomputed, {payload['n_changed']} changed, "
        f"exact {payload['n_exact_as_recorded']} -> {payload['n_exact']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
