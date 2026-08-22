"""Append a budget-sensitivity section to the GPU_RUN3 reproduction report.

Compares a baseline benchmark run against an extended-budget rerun of the systems
that were not recovered, so "unrecovered" can be split into search-limited and
structurally-limited rather than reported as one bucket.

The section is delimited by markers and rewritten in place, so re-running this is
idempotent and does not fight the main report builder.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from gpu_run3_runtime import load_gpu_run3_configs, resolve_run_dir  # noqa: E402

BEGIN = "<!-- BEGIN budget-sensitivity -->"
END = "<!-- END budget-sensitivity -->"
NETWORK_OPS = ("aggr", "rgga", "sour", "targ")


def parse_args():
    parser = argparse.ArgumentParser(description="GPU_RUN3 budget sensitivity section")
    parser.add_argument("--run-id", required=True, help="baseline benchmark run")
    parser.add_argument("--extended-run-id", required=True, help="extended-budget rerun")
    parser.add_argument("--report", default=str(ROOT / "GPU_RUN3" / "GPU_RUN3_nd2_reproduction_report.md"))
    return parser.parse_args()


def _records(run_dir: Path) -> list[dict]:
    path = run_dir / "phase3" / "records.jsonl"
    if not path.is_file():
        return []
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    return [r for r in rows if r.get("condition") == "ndformer_mcts"]


def _mean(values) -> float:
    finite = [float(v) for v in values if v is not None and math.isfinite(float(v))]
    return float(sum(finite) / len(finite)) if finite else float("nan")


def _fmt(value, digits=4) -> str:
    if value is None:
        return "-"
    if isinstance(value, float):
        if math.isnan(value):
            return "NaN"
        return f"{value:.{digits}g}"
    return str(value)


def _has_network_op(formula: str | None) -> bool:
    return bool(formula) and any(op in formula for op in NETWORK_OPS)


def main() -> int:
    args = parse_args()
    config = load_gpu_run3_configs()
    base = _records(resolve_run_dir(args.run_id, config=config))
    ext_dir = resolve_run_dir(args.extended_run_id, config=config)
    ext = _records(ext_dir)
    if not ext:
        raise SystemExit(f"no extended records in {ext_dir}")

    base_by: dict[str, list[dict]] = defaultdict(list)
    for row in base:
        base_by[str(row.get("system_id"))].append(row)
    ext_by: dict[str, list[dict]] = defaultdict(list)
    for row in ext:
        ext_by[str(row.get("system_id"))].append(row)

    base_limit = _mean([r.get("time_limit_sec") for r in base]) or 0
    ext_limit = _mean([r.get("time_limit_sec") for r in ext]) or 0

    lines = [
        BEGIN,
        "",
        "## 7. Budget sensitivity: search-limited vs structurally-limited",
        "",
        f"The systems not recovered in the main benchmark were rerun at "
        f"{_fmt(ext_limit, 4)}s per problem instead of {_fmt(base_limit, 4)}s, with the ACC4 "
        "early-stop predicate disabled. Without disabling it the search halts as soon "
        "as the fit saturates, so the larger budget would never be spent and every "
        "system would look equally stuck.",
        "",
        f"Extended run: `{args.extended_run_id}`",
        "",
        "| system | seeds | RMSE @base | RMSE @extended | best RMSE @extended | TED @base | TED @extended | mean nodes | solved |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    verdicts = {}
    for system in sorted(ext_by):
        b = base_by.get(system, [])
        e = ext_by[system]
        best = min((r.get("fit_error") for r in e if r.get("fit_error") is not None), default=float("nan"))
        solved = sum(1 for r in e if (r.get("fit_error") or 1.0) < 1e-4)
        lines.append(
            "| "
            + " | ".join(
                [
                    system,
                    str(len(e)),
                    _fmt(_mean([r.get("fit_error") for r in b])),
                    _fmt(_mean([r.get("fit_error") for r in e])),
                    _fmt(best),
                    _fmt(_mean([r.get("ted_raw") for r in b])),
                    _fmt(_mean([r.get("ted_raw") for r in e])),
                    _fmt(_mean([r.get("search_nodes") for r in e]), 5),
                    f"{solved}/{len(e)}",
                ]
            )
            + " |"
        )
        verdicts[system] = solved

    lines += [
        "",
        "### Whether the network-coupling term was found",
        "",
        "The ND2 operators (`aggr` / `sour` / `targ` / `rgga`) are what make a formula a",
        "*network* dynamics law rather than a node-local one. Counting how often they",
        "appear at all separates a search that misses a detail from one that never",
        "reaches the coupling term.",
        "",
        "| system | true formula has network op | predictions containing one (extended) |",
        "|---|---|---|",
    ]
    for system in sorted(ext_by):
        e = ext_by[system]
        truth = next((r.get("true_formula_raw") for r in e if r.get("true_formula_raw")), "")
        found = sum(1 for r in e if _has_network_op(r.get("pred_formula_raw")))
        lines.append(f"| {system} | {'yes' if _has_network_op(truth) else 'no'} | {found}/{len(e)} |")

    lines += [
        "",
        "### Per-seed predictions at the extended budget",
        "",
    ]
    for system in sorted(ext_by):
        e = sorted(ext_by[system], key=lambda r: r.get("seed") or 0)
        truth = next((r.get("true_formula_raw") for r in e if r.get("true_formula_raw")), "")
        lines.append(f"**{system}** — true: `{truth}`")
        lines.append("")
        for row in e:
            lines.append(
                f"- seed {row.get('seed')}: `{row.get('pred_formula_raw')}` "
                f"(RMSE {_fmt(row.get('fit_error'))}, TED {_fmt(row.get('ted_raw'))})"
            )
        lines.append("")

    lines += [
        "### Reading",
        "",
        "A system whose RMSE is flat under a six-fold budget increase is not waiting for",
        "more search. Where the predictions also omit the network operators entirely, the",
        "search is settling on the node-local part of the dynamics, which already explains",
        "most of the variance, and never pays the cost of reaching the coupling term.",
        "That is a different failure from one where the structure is reachable but found",
        "only in some seeds.",
        "",
        "These runs use the same checkpoint, corpus and configs as the main benchmark;",
        "only the MCTS time limit and the early-stop predicate differ.",
        "",
        END,
        "",
    ]
    section = "\n".join(lines)

    report = Path(args.report)
    text = report.read_text(encoding="utf-8") if report.is_file() else ""
    if BEGIN in text and END in text:
        head, rest = text.split(BEGIN, 1)
        _old, tail = rest.split(END, 1)
        text = head + section + tail
    else:
        text = text.rstrip("\n") + "\n\n" + section
    report.write_text(text, encoding="utf-8")
    print(f"wrote budget-sensitivity section into {report}")
    for system, solved in verdicts.items():
        print(f"  {system}: solved {solved}/{len(ext_by[system])} at the extended budget")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
