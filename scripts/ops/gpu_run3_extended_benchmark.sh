#!/usr/bin/env bash
# Re-run the ND2 synthetic benchmark with an extended MCTS budget, restricted to the
# systems whose ground-truth formula was NOT recovered at the original budget.
#
# Written to its own run-id so the original 300s results stay intact and the two
# budgets can be compared as a paired experiment (same seeds, same systems, same
# simulation conditions; only the search budget differs).
#
# Usage:
#   bash scripts/ops/gpu_run3_extended_benchmark.sh <run-id> <systems-csv> <seconds> [wait-pid]
set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT"

RUN_ID="${1:?usage: <run-id> <systems-csv> <seconds> [wait-pid]}"
SYSTEMS="${2:?systems csv required}"
SECONDS_BUDGET="${3:?budget seconds required}"
WAIT_PID="${4:-}"
PY=/home/blabo/miniconda3/envs/lansr310/bin/python

if [[ -n "$WAIT_PID" ]]; then
  echo "[extended] waiting for pid $WAIT_PID to exit"
  while kill -0 "$WAIT_PID" 2>/dev/null; do sleep 20; done
  echo "[extended] predecessor exited"
fi

echo "[extended] run-id=$RUN_ID systems=$SYSTEMS budget=${SECONDS_BUDGET}s"

# Phase 0 is required by phase 3 and records provenance for this run.
$PY scripts/phases/gpu_run3_phase0_preflight.py --run-id "$RUN_ID" || {
  echo "[extended] preflight FAILED"; exit 1;
}

# Guided only: the unguided control was already measured at the original budget,
# and the question here is recovery under more search, not guidance value.
$PY scripts/phases/gpu_run3_phase3_benchmark.py \
  --run-id "$RUN_ID" \
  --systems "$SYSTEMS" \
  --no-unguided \
  --mcts-time-limit "$SECONDS_BUDGET" \
  --no-early-stop \
  || echo "[extended] phase3 FAILED"

echo "[extended] === recompute structural metrics ==="
$PY scripts/reports/gpu_run3_recompute_structural.py --run-id "$RUN_ID" || echo "[extended] recompute FAILED"

echo "[extended] done"
