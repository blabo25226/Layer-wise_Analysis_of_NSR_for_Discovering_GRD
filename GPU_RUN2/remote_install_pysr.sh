#!/usr/bin/env bash
set -eo pipefail
source ~/miniconda3/etc/profile.d/conda.sh
conda activate lansr310
pip install 'setuptools<81' pysr
python - <<'PY'
import pysr
print("pysr", getattr(pysr, "__version__", "?"))
# Trigger Julia backend install if needed
from pysr import install
try:
    install()
    print("pysr julia backend install OK")
except Exception as e:
    print("pysr install() note:", type(e).__name__, e)
PY
