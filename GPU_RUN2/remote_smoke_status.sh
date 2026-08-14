#!/usr/bin/env bash
set -eo pipefail
RUN=${1:-gpu_run2_smoke_02}
ROOT=~/Layer-wise_Analysis_of_NSR_for_Discovering_GRD/results/runs/$RUN
echo "=== processes ==="
ps -ef | grep -E 'run_gpu_run2|gpu_run2_phase|remote_run_smoke' | grep -v grep || true
echo "=== log tail ($RUN) ==="
tail -n 100 "$ROOT/smoke_nohup.log" || true
echo "=== run dir ==="
ls -la "$ROOT" || true
if [[ -f "$ROOT/phase1/manifest.json" ]]; then
  echo "=== phase1 manifest ==="
  cat "$ROOT/phase1/manifest.json"
fi
if [[ -f "$ROOT/phase2/manifest.json" ]]; then
  echo "=== phase2 manifest ==="
  cat "$ROOT/phase2/manifest.json"
fi
if [[ -f "$ROOT/phase3/manifest.json" ]]; then
  echo "=== phase3 manifest ==="
  cat "$ROOT/phase3/manifest.json"
fi
if [[ -f "$ROOT/phase3/candidate_layers.json" ]]; then
  echo "=== candidates ==="
  cat "$ROOT/phase3/candidate_layers.json"
fi
if [[ -f "$ROOT/smoke_timing_summary.json" ]]; then
  echo "=== timing ==="
  cat "$ROOT/smoke_timing_summary.json"
fi
