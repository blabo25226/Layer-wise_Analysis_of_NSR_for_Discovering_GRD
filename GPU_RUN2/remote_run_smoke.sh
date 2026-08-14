#!/usr/bin/env bash
set -eo pipefail
source ~/miniconda3/etc/profile.d/conda.sh
conda activate lansr310
cd ~/Layer-wise_Analysis_of_NSR_for_Discovering_GRD
export CUDA_VISIBLE_DEVICES=0
export LANSR_WEIGHTS="$PWD/assets/nesymres/weights/100M.ckpt"
export LANSR_CONFIG="$PWD/assets/nesymres/jupyter/100M/config.yaml"
export LANSR_EQ_SETTING="$PWD/assets/nesymres/jupyter/100M/eq_setting.json"
chmod +x scripts/ops/run_gpu_run2.sh
exec bash scripts/ops/run_gpu_run2.sh --smoke --run-id gpu_run2_smoke_06 --skip-archive
