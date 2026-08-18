"""Compare ND2 formula recovery at two MCTS budgets, paired by system and seed.

The extended run repeats the same systems, seeds and simulation conditions as the
original; only the search budget differs. This writes the paired table that
answers whether the unrecovered systems were search-limited.

Usage:
  python scripts/reports/gpu_run3_budget_comparison.py --base <run-id> --extended <run-id>
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from gpu_run3_runtime import load_gpu_run3_configs, resolve_run_dir, write_json  # noqa: E402


def parse_args():
    parser = argparse.ArgumentParser(description="GPU_RUN3 budget comparison")
    parser.add_argument("--base", required=True)
    parser.add_argument("--extended", required=True)
    parser.add_argument("--out", default=str(ROOT / "GPU_RUN3" / "GPU_RUN3_budget_comparison.md"))
    return parser.parse_args()


def _recomputed(run_dir: Path) -> dict[tuple, dict]:
    path = run_dir / "structural_metrics_recomputed.json"
    if not path.is_file():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    out = {}
    for row in payload.get("records") or []:
        if row.get("status") != "recomputed" or row.get("condition") != "ndformer_mcts":
            continue
        if not row.get("system_id"):
            continue
        out[(row["system_id"], row.get("seed"))] = row
    return out


def _raw(run_dir: Path) -> dict[tuple, dict]:
    path = run_dir / "phase3" / "records.jsonl"
    if not path.is_file():
        return {}
    out = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("condition") != "ndformer_mcts":
            continue
        out[(row.get("system_id"), row.get("seed"))] = row
    return out


def _fmt(value, digits=4):
    if value is None:
        return "-"
    if isinstance(value, float):
        if math.isnan(value):
            return "NaN"
        return f"{value:.{digits}g}"
    return str(value)


def main() -> int:
    args = parse_args()
    config = load_gpu_run3_configs()
    base_dir = resolve_run_dir(args.base, config=config)
    ext_dir = resolve_run_dir(args.extended, config=config)
    base_struct, ext_struct = _recomputed(base_dir), _recomputed(ext_dir)
    base_raw, ext_raw = _raw(base_dir), _raw(ext_dir)
    if not ext_raw:
        print(f"no extended records yet in {ext_dir}", file=sys.stderr)

    keys = sorted(ext_raw, key=lambda k: (str(k[0]), str(k[1])))
    lines = [
        "# GPU_RUN3 — search budget comparison",
        "",
        f"Base run: `{args.base}`  ",
        f"Extended run: `{args.extended}`",
        "",
        "Paired by system and seed: identical systems, seeds and simulation conditions;",
        "only the MCTS budget differs. The extended run also disables the ACC4 early stop,",
        "so the larger budget is actually spent.",
        "",
        "| system | seed | budget s (base -> ext) | RMSE base | RMSE ext | R2 base | R2 ext "
        "| TED base | TED ext | exact base | exact ext |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    improved_fit = improved_ted = newly_exact = 0
    for key in keys:
        system, seed = key
        b, e = base_raw.get(key), ext_raw.get(key)
        bs, es = base_struct.get(key, {}), ext_struct.get(key, {})
        if b is None:
            continue
        b_r2 = (b.get("official_metrics") or {}).get("R2")
        e_r2 = (e.get("official_metrics") or {}).get("R2")
        b_ted, e_ted = bs.get("ted_raw", b.get("ted_raw")), es.get("ted_raw", e.get("ted_raw"))
        b_ex, e_ex = bs.get("exact", b.get("exact")), es.get("exact", e.get("exact"))
        if e.get("fit_error") is not None and b.get("fit_error") is not None and e["fit_error"] < b["fit_error"]:
            improved_fit += 1
        if isinstance(b_ted, (int, float)) and isinstance(e_ted, (int, float)) and e_ted < b_ted:
            improved_ted += 1
        if b_ex != 1.0 and e_ex == 1.0:
            newly_exact += 1
        lines.append(
            f"| {system} | {seed} | {_fmt(b.get('time_limit_sec'))} -> {_fmt(e.get('time_limit_sec'))} "
            f"| {_fmt(b.get('fit_error'))} | {_fmt(e.get('fit_error'))} "
            f"| {_fmt(b_r2)} | {_fmt(e_r2)} | {_fmt(b_ted)} | {_fmt(e_ted)} "
            f"| {_fmt(b_ex)} | {_fmt(e_ex)} |"
        )
    lines += [
        "",
        "## Summary",
        "",
        f"- paired runs compared: {len(keys)}",
        f"- fit error improved: {improved_fit}",
        f"- TED improved: {improved_ted}",
        f"- newly exact at the larger budget: {newly_exact}",
        "",
        "A system whose fit error was already near zero at the small budget cannot be "
        "search-limited: the reward was already maximised, so the failure to recover the "
        "true formula is one of identifiability, not compute. Only systems whose fit error "
        "was large at the small budget can be tested for search limitation here.",
        "",
    ]
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    write_json(
        ext_dir / "budget_comparison.json",
        {
            "base_run": args.base,
            "extended_run": args.extended,
            "n_pairs": len(keys),
            "improved_fit": improved_fit,
            "improved_ted": improved_ted,
            "newly_exact": newly_exact,
        },
    )
    print(f"wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
