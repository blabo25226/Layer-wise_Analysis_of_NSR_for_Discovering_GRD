#!/usr/bin/env bash
# Paste into the open GPU PC SSH session (lansr310 already active).
# Or: bash GPU_RUN2/remote_setup_commands.sh  after scp/sync.
set -euo pipefail
cd ~/Layer-wise_Analysis_of_NSR_for_Discovering_GRD

echo "=== status ==="
git status --short
git branch --show-current
git log -1 --oneline
python --version
python -c "import torch; print(torch.__version__, torch.version.cuda, torch.cuda.is_available(), torch.cuda.device_count())"
nvidia-smi -L

echo "=== install deps (keep torch cu124) ==="
# Do NOT use requirements/gpu.txt via a path that pulls cpu.txt's torch pin.
# gpu.txt only includes base.txt, but install base explicitly.
pip install -r requirements/base.txt
pip install -e third_party/nesymres
# Avoid requirements/dev.txt (pulls cpu.txt -> torch CPU). pytest only.
pip install 'pytest>=7.4,<9'

echo "=== verify torch still CUDA ==="
python -c "import torch; print(torch.__version__, torch.version.cuda, torch.cuda.is_available(), torch.cuda.device_count())"
pip check || true

echo "=== dual GPU matmul ==="
python - <<'PY'
import torch
for i in range(torch.cuda.device_count()):
    device = f"cuda:{i}"
    x = torch.randn(1000, 1000, device=device)
    y = x @ x
    print(i, torch.cuda.get_device_name(i), y.device, float(y.mean()))
PY

echo "=== compile + pytest ==="
python -m compileall -q src scripts tests
python -m pytest -q

echo "=== checkpoint ==="
mkdir -p assets/nesymres/weights
CKPT=assets/nesymres/weights/100M.ckpt
if [[ ! -f "$CKPT" ]]; then
  wget -O "$CKPT" \
    https://huggingface.co/TommasoBendinelli/NeuralSymbolicRegressionThatScales/resolve/main/100M.ckpt
fi
sha256sum "$CKPT"
ls -lh "$CKPT"

export LANSR_WEIGHTS="$PWD/$CKPT"
export LANSR_CONFIG="$PWD/assets/nesymres/jupyter/100M/config.yaml"
export LANSR_EQ_SETTING="$PWD/assets/nesymres/jupyter/100M/eq_setting.json"

echo "=== preflight ==="
python scripts/ops/preflight_gpu.py \
  --weights "$LANSR_WEIGHTS" \
  --config "$LANSR_CONFIG" \
  --eq-setting "$LANSR_EQ_SETTING"

echo "=== SETUP OK ==="
