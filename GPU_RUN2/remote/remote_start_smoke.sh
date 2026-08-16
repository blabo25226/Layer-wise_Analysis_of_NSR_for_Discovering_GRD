#!/usr/bin/env bash
set -eo pipefail
REPO=~/Layer-wise_Analysis_of_NSR_for_Discovering_GRD
cd "$REPO"
mkdir -p results/runs/gpu_run2_smoke_06
nohup bash GPU_RUN2/remote_run_smoke.sh > results/runs/gpu_run2_smoke_06/smoke_nohup.log 2>&1 &
echo "STARTED_PID=$!"
sleep 3
head -n 20 results/runs/gpu_run2_smoke_06/smoke_nohup.log || true
