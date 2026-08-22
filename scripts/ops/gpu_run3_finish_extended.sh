#!/usr/bin/env bash
# Unattended completion for the extended-budget benchmark.
#
# Waits for the extended run to exit, then builds its reports and the paired
# budget comparison against the original run. Detach with setsid so it survives
# an SSH disconnect:
#   setsid nohup bash scripts/ops/gpu_run3_finish_extended.sh <ext-run-id> <base-run-id> <pid> &
set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT"

EXT_RUN="${1:?ext run-id}"
BASE_RUN="${2:?base run-id}"
WAIT_PID="${3:-}"
PY=/home/blabo/miniconda3/envs/lansr310/bin/python

if [[ -n "$WAIT_PID" ]]; then
  echo "[finish] waiting for pid $WAIT_PID"
  while kill -0 "$WAIT_PID" 2>/dev/null; do sleep 60; done
  echo "[finish] extended run exited"
fi

echo "[finish] === recompute (idempotent; the extended script also runs it) ==="
$PY scripts/reports/gpu_run3_recompute_structural.py --run-id "$EXT_RUN" || echo "[finish] recompute FAILED"

echo "[finish] === reports for the extended run ==="
$PY scripts/reports/gpu_run3_report.py --run-id "$EXT_RUN" \
  --out-dir "$REPO_ROOT/GPU_RUN3/extended" || echo "[finish] report FAILED"

echo "[finish] === paired budget comparison ==="
$PY scripts/reports/gpu_run3_budget_comparison.py --base "$BASE_RUN" --extended "$EXT_RUN" \
  || echo "[finish] comparison FAILED"

echo "[finish] done"
