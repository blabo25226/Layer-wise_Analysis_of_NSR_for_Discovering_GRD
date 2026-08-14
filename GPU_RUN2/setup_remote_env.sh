#!/usr/bin/env bash
# LANSR GPU PC remaining env setup (gpu_pc.md §15–19).
# Run inside: conda activate lansr310 && cd ~/Layer-wise_Analysis_of_NSR_for_Discovering_GRD
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

echo "=== 0. Repo / env sanity ==="
git status --short
git branch --show-current
git log -1 --oneline
python --version
python -c "import torch; print(torch.__version__, torch.version.cuda, torch.cuda.is_available(), torch.cuda.device_count())"
nvidia-smi -L

# Confirm torch will not be overwritten by requirements (gpu.txt only includes base.txt; no torch pin).
echo "=== 1. Inspect requirements (torch must stay pip cu124) ==="
grep -nE 'torch|pytorch' requirements/base.txt requirements/gpu.txt requirements/cpu.txt requirements/dev.txt || true

echo "=== 2. Install LANSR deps without touching torch ==="
# gpu.txt == base.txt only; install base explicitly so we never pull cpu.txt's torch==2.5.1 CPU wheel.
pip install -r requirements/base.txt
pip install -e third_party/nesymres
# dev.txt pulls cpu.txt which pins torch==2.5.1 (CPU index). Install pytest only.
pip install 'pytest>=7.4,<9'

echo "=== 3. Re-verify torch CUDA ==="
python -c "import torch; print(torch.__version__, torch.version.cuda, torch.cuda.is_available(), torch.cuda.device_count())"
pip check || true

echo "=== 4. Dual-GPU matmul smoke ==="
python - <<'PY'
import torch
assert torch.cuda.is_available(), "CUDA not available"
for i in range(torch.cuda.device_count()):
    device = f"cuda:{i}"
    x = torch.randn(1000, 1000, device=device)
    y = x @ x
    print(i, torch.cuda.get_device_name(i), y.device, float(y.mean()))
PY

echo "=== 5. Compileall + pytest ==="
python -m compileall -q src scripts tests
python -m pytest -q

echo "=== 6. Checkpoint ==="
mkdir -p assets/nesymres/weights
CKPT="assets/nesymres/weights/100M.ckpt"
if [[ ! -f "$CKPT" ]]; then
  echo "Downloading NeSymReS 100M.ckpt ..."
  wget -O "$CKPT" \
    "https://huggingface.co/TommasoBendinelli/NeuralSymbolicRegressionThatScales/resolve/main/100M.ckpt"
fi
sha256sum "$CKPT"
ls -lh "$CKPT"

export LANSR_WEIGHTS="$PWD/$CKPT"
export LANSR_CONFIG="$PWD/assets/nesymres/jupyter/100M/config.yaml"
export LANSR_EQ_SETTING="$PWD/assets/nesymres/jupyter/100M/eq_setting.json"

echo "=== 7. GPU preflight ==="
python scripts/ops/preflight_gpu.py \
  --weights "$LANSR_WEIGHTS" \
  --config "$LANSR_CONFIG" \
  --eq-setting "$LANSR_EQ_SETTING"

echo "=== Setup complete. Ready for GPU_RUN2 smoke. ==="
