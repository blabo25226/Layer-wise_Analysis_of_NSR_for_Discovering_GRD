#!/usr/bin/env bash
# Continue setup: checkpoint + preflight (+ optional PySR note)
set -eo pipefail
source ~/miniconda3/etc/profile.d/conda.sh
conda activate lansr310
set -u
cd ~/Layer-wise_Analysis_of_NSR_for_Discovering_GRD

mkdir -p assets/nesymres/weights
CKPT="assets/nesymres/weights/100M.ckpt"
if [[ ! -f "$CKPT" ]]; then
  echo "Downloading 100M.ckpt ..."
  wget -O "$CKPT" \
    "https://huggingface.co/TommasoBendinelli/NeuralSymbolicRegressionThatScales/resolve/main/100M.ckpt"
fi
sha256sum "$CKPT"
ls -lh "$CKPT"

python scripts/ops/preflight_gpu.py \
  --weights "$PWD/$CKPT" \
  --config "$PWD/assets/nesymres/jupyter/100M/config.yaml" \
  --eq-setting "$PWD/assets/nesymres/jupyter/100M/eq_setting.json"

echo "=== pysr import check ==="
python - <<'PY'
try:
    import pysr
    print("pysr OK", getattr(pysr, "__version__", "?"))
except Exception as e:
    print("pysr MISSING:", type(e).__name__, e)
PY

echo "=== CONTINUE OK ==="
