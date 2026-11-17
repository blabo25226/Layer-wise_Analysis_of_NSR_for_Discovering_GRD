#!/usr/bin/env bash
set -eo pipefail
cd ~/Layer-wise_Analysis_of_NSR_for_Discovering_GRD
source ~/miniconda3/etc/profile.d/conda.sh
conda activate lansr310
git fetch origin
# Discard agent SCP debris; keep results/assets
git reset --hard origin/main
git clean -fd -e results -e assets -e data -e GitHubSourceCode -e third_party
echo "=== HEAD ==="
git log -1 --oneline
git rev-parse HEAD
grep -n '^run_name:' configs/gpu_run2/base.yaml
test -f scripts/ops/run_gpu_run2.sh
test -f src/data/nesymres_tokenize.py
test -f assets/nesymres/weights/100M.ckpt
grep -n candidate_layers_structure_holdout scripts/phases/gpu_run2_phase3_interpret.py | head
grep -n 'save_phase5_finetuned_checkpoint\|hp_selected_' scripts/phases/gpu_run2_phase5_selective_ft.py | head
export LANSR_RUN_ID=gpu_run2_20260815
export CUDA_VISIBLE_DEVICES=0
mkdir -p "results/runs/${LANSR_RUN_ID}"
chmod +x scripts/ops/run_gpu_run2.sh
nohup bash scripts/ops/run_gpu_run2.sh --run-id "${LANSR_RUN_ID}" \
  > "results/runs/${LANSR_RUN_ID}/nohup_full.log" 2>&1 &
echo "STARTED_PID=$!"
sleep 5
pgrep -af 'run_gpu_run2|gpu_run2_phase' || true
tail -n 50 "results/runs/${LANSR_RUN_ID}/nohup_full.log" || true
