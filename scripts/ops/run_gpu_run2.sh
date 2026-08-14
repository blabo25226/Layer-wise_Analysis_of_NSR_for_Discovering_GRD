#!/usr/bin/env bash
# Sequential GPU_RUN2 runner for Linux (RTX 2070).
# Usage:
#   bash scripts/ops/run_gpu_run2.sh
#   bash scripts/ops/run_gpu_run2.sh --smoke
#   bash scripts/ops/run_gpu_run2.sh --smoke --run-id gpu_run2_smoke_01
#   bash scripts/ops/run_gpu_run2.sh --from-phase 3
set -eo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT"

RUN_ID="${LANSR_RUN_ID:-gpu_run2_local}"
FROM_PHASE=0
SMOKE=0
DRY_RUN=0
ALLOW_CPU=0
SKIP_ARCHIVE=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --run-id) RUN_ID="$2"; shift 2 ;;
    --from-phase) FROM_PHASE="$2"; shift 2 ;;
    --smoke) SMOKE=1; shift ;;
    --dry-run) DRY_RUN=1; shift ;;
    --allow-cpu) ALLOW_CPU=1; shift ;;
    --skip-archive) SKIP_ARCHIVE=1; shift ;;
    *) echo "Unknown arg: $1" >&2; exit 2 ;;
  esac
done

export LANSR_RUN_ID="$RUN_ID"
export LANSR_DECODE_TIMEOUT_SEC="${LANSR_DECODE_TIMEOUT_SEC:-30}"
export LANSR_WEIGHTS="${LANSR_WEIGHTS:-$REPO_ROOT/assets/nesymres/weights/100M.ckpt}"
export LANSR_CONFIG="${LANSR_CONFIG:-$REPO_ROOT/assets/nesymres/jupyter/100M/config.yaml}"
export LANSR_EQ_SETTING="${LANSR_EQ_SETTING:-$REPO_ROOT/assets/nesymres/jupyter/100M/eq_setting.json}"
export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}"

RUN_DIR="$REPO_ROOT/results/runs/$RUN_ID"
export LANSR_RUN_DIR="$RUN_DIR"
mkdir -p "$RUN_DIR"

COMMON=(--run-id "$RUN_ID")
if [[ "$SMOKE" -eq 1 ]]; then COMMON+=(--smoke); fi
if [[ "$DRY_RUN" -eq 1 ]]; then COMMON+=(--dry-run); fi

run_phase() {
  local phase="$1"
  shift
  if [[ "$phase" -lt "$FROM_PHASE" ]]; then
    echo "Skipping Phase $phase (FROM_PHASE=$FROM_PHASE)"
    return 0
  fi
  echo "=== GPU_RUN2 Phase $phase ==="
  local started
  started="$(date +%s)"
  python "$@"
  local ended elapsed
  ended="$(date +%s)"
  elapsed=$((ended - started))
  echo "Phase $phase finished in ${elapsed}s"
  echo "$elapsed" > "$RUN_DIR/phase${phase}_wall_seconds.txt"
}

PHASE0=(scripts/phases/gpu_run2_phase0_preflight.py --run-id "$RUN_ID")
if [[ "$ALLOW_CPU" -eq 1 ]]; then PHASE0+=(--allow-cpu); fi
run_phase 0 "${PHASE0[@]}"

run_phase 1 scripts/phases/gpu_run2_phase1_data.py "${COMMON[@]}"
run_phase 2 scripts/phases/gpu_run2_phase2_baseline.py "${COMMON[@]}" --split validation
run_phase 2 scripts/phases/gpu_run2_phase2_baseline.py "${COMMON[@]}" --split test
# Overwrite phase2 wall with combined note: keep last; also accumulate below via python summary later
run_phase 3 scripts/phases/gpu_run2_phase3_interpret.py "${COMMON[@]}"
run_phase 4 scripts/phases/gpu_run2_phase4_contribution.py "${COMMON[@]}"
run_phase 5 scripts/phases/gpu_run2_phase5_selective_ft.py "${COMMON[@]}" --view main --split validation
run_phase 5 scripts/phases/gpu_run2_phase5_selective_ft.py "${COMMON[@]}" --view structure_holdout --split validation
run_phase 5 scripts/phases/gpu_run2_phase5_selective_ft.py "${COMMON[@]}" --view main --split test
run_phase 5 scripts/phases/gpu_run2_phase5_selective_ft.py "${COMMON[@]}" --view structure_holdout --split test

echo "=== GPU_RUN2 finalize ==="
FINALIZE=(scripts/ops/finalize_gpu_run2.py --run-id "$RUN_ID")
if [[ "$SKIP_ARCHIVE" -eq 1 ]]; then FINALIZE+=(--skip-archive); fi
python "${FINALIZE[@]}"

# Lightweight timing rollup for smoke / runtime estimation
python - <<PY
import json, statistics, time
from pathlib import Path
run_dir = Path(r"""$RUN_DIR""")
phase_secs = {}
for p in range(0, 6):
    f = run_dir / f"phase{p}_wall_seconds.txt"
    if f.is_file():
        phase_secs[f"phase{p}_seconds"] = float(f.read_text().strip())

decode_secs = []
timeouts = 0
pysr_secs = []
ft_full = []
ft_single = []
for path in run_dir.rglob("*.json"):
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        continue
    rows = data if isinstance(data, list) else data.get("rows") or data.get("records") or []
    if isinstance(data, dict) and not rows:
        # single record-like dict
        candidates = [data]
    else:
        candidates = rows if isinstance(rows, list) else []
    for row in candidates:
        if not isinstance(row, dict):
            continue
        if "process_seconds" in row:
            try:
                decode_secs.append(float(row["process_seconds"]))
            except Exception:
                pass
        if "search_seconds" in row:
            try:
                pysr_secs.append(float(row["search_seconds"]))
            except Exception:
                pass
        fr = str(row.get("failure_reason") or "")
        if "timeout" in fr.lower() or "DecodeTimeout" in fr:
            timeouts += 1
        cond = str(row.get("condition") or row.get("trainable") or "")
        if "full_ft_seconds" in row:
            ft_full.append(float(row["full_ft_seconds"]))
        if "single_layer_ft_seconds" in row:
            ft_single.append(float(row["single_layer_ft_seconds"]))

def pct(vals, q):
    if not vals:
        return None
    s = sorted(vals)
    if len(s) == 1:
        return s[0]
    k = (len(s) - 1) * q
    f = int(k)
    c = min(f + 1, len(s) - 1)
    if f == c:
        return s[f]
    return s[f] + (s[c] - s[f]) * (k - f)

total = sum(phase_secs.values())
summary = {
    **phase_secs,
    "total_seconds": total,
    "decode_count": len(decode_secs),
    "decode_mean": (sum(decode_secs) / len(decode_secs)) if decode_secs else None,
    "decode_p50": pct(decode_secs, 0.50),
    "decode_p90": pct(decode_secs, 0.90),
    "decode_p95": pct(decode_secs, 0.95),
    "decode_max": max(decode_secs) if decode_secs else None,
    "timeout_count": timeouts,
    "timeout_rate": (timeouts / len(decode_secs)) if decode_secs else None,
    "pysr_search_mean": (sum(pysr_secs) / len(pysr_secs)) if pysr_secs else None,
    "pysr_search_p95": pct(pysr_secs, 0.95),
    "full_ft_count": len(ft_full),
    "full_ft_mean": (sum(ft_full) / len(ft_full)) if ft_full else None,
    "single_layer_ft_count": len(ft_single),
    "single_layer_ft_mean": (sum(ft_single) / len(ft_single)) if ft_single else None,
    "note": "Wall phase seconds from runner; decode/search/FT mined from JSON if present.",
    "smoke": bool($SMOKE),
}
# Rough full-run estimate using plan.md counts (conservative placeholders).
# GPU_RUN2 plan: 3 seed bundles x 2 noise; Phase2 validation+test; etc.
# Prefer measured decode/FT means when available.
dec_p50 = summary["decode_p50"] or 0.0
dec_p90 = summary["decode_p90"] or 0.0
# Production counts from GPU_RUN2/plan.md Phase decode table (serial upper-bound units).
# Phase2 NeSymReS half of 1152 method-runs ≈ 576; Phase3/4/5 add more GPU decode-like work.
# For estimate we split method searches and FT runs explicitly.
N_NESYMRES_DECODE = 576 + 1440 + 1440 + 4680  # plan Phase2(NSR)+3+4+5
N_PYSR = 576  # Phase2 PySR half of 1152
N_FULL_FT = 48  # Phase5 selective FT upper learning runs (plan max 48)
N_SINGLE_FT = 30  # Phase4 contribution learning runs (plan max 30)
ft_full_m = summary["full_ft_mean"] or 0.0
ft_single_m = summary["single_layer_ft_mean"] or 0.0
pysr_m = summary["pysr_search_mean"] or 0.0
est_p50 = N_NESYMRES_DECODE * dec_p50 + N_FULL_FT * ft_full_m + N_SINGLE_FT * ft_single_m + N_PYSR * pysr_m
est_p90 = N_NESYMRES_DECODE * dec_p90 + N_FULL_FT * ft_full_m + N_SINGLE_FT * ft_single_m + N_PYSR * (summary["pysr_search_p95"] or pysr_m)
# Also scale observed smoke wall by problem/seed expansion if smoke.
if summary.get("smoke") and total > 0:
    # smoke: 1 seed x 1 noise; full: 3 seeds x 2 noise => x6, plus more problems (~5-10x depending on phase)
    # Use a blended multiplier: seed/noise x6 and problem expansion ~8 => ~48 as rough upper; use 20 as mid.
    summary["estimated_full_runtime_hours_from_smoke_wall_x20"] = (total * 20) / 3600.0
    summary["estimated_full_runtime_hours_from_smoke_wall_x48"] = (total * 48) / 3600.0
summary["estimated_full_runtime_hours_p50"] = est_p50 / 3600.0
summary["estimated_full_runtime_hours_p90"] = est_p90 / 3600.0
summary["estimate_assumptions"] = {
    "N_NESYMRES_DECODE": N_NESYMRES_DECODE,
    "N_FULL_FT": N_FULL_FT,
    "N_SINGLE_FT": N_SINGLE_FT,
    "N_PYSR": N_PYSR,
    "source": "GPU_RUN2/plan.md Phase decode table",
}
out = run_dir / "smoke_timing_summary.json"
out.write_text(json.dumps(summary, indent=2), encoding="utf-8")
print(json.dumps(summary, indent=2))
print(f"Wrote {out}")
PY

echo "GPU_RUN2 finished. Run dir: $RUN_DIR"
