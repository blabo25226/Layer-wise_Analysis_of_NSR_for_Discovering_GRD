#!/usr/bin/env bash
# Full-catalogue Phase-1 (one seed, noise 0) then FT microbenchmark on the GPU PC.
set -eo pipefail
source ~/miniconda3/etc/profile.d/conda.sh
conda activate lansr310
set -u
cd ~/Layer-wise_Analysis_of_NSR_for_Discovering_GRD
export PYTHONPATH="$PWD/src:$PWD/third_party/nesymres${PYTHONPATH:+:$PYTHONPATH}"
export LANSR_RUN_ID="${LANSR_RUN_ID:-gpu_run2_ft_microbench_02}"
mkdir -p "results/runs/${LANSR_RUN_ID}"
LOG="results/runs/${LANSR_RUN_ID}/microbench_run.log"
exec > >(tee -a "$LOG") 2>&1
echo "=== Phase 1 full catalogue (${LANSR_RUN_ID}) ==="
# Production problem count; points capped by finetune.max_points=80 later.
python scripts/phases/gpu_run2_phase1_data.py \
  --run-id "${LANSR_RUN_ID}" \
  --n-variants 30 \
  --n-train 128 \
  --n-eval 32 \
  --data-seeds 101
echo "=== FT microbench (full main train/val) ==="
python scripts/ops/gpu_run2_ft_microbench.py \
  --run-id "${LANSR_RUN_ID}" \
  --repeats 2
echo "=== done ==="
python - <<PY
import json
from pathlib import Path
import os
p = Path("results/runs") / os.environ["LANSR_RUN_ID"] / "ft_microbench.json"
d = json.loads(p.read_text())
print("n_train_rows", d.get("n_train_rows"), "n_train_loader", d.get("n_train_loader"))
print(json.dumps(d.get("estimate", d), indent=2))
for name, block in d.get("conditions", {}).items():
    print(name, "mean_s", block.get("mean_seconds"))
PY
