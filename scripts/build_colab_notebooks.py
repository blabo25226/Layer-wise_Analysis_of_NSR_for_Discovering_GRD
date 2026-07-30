"""Compat wrapper. Prefer GPU_RUN1/scripts/build_colab_notebooks.py."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_TARGET = Path(__file__).resolve().parents[1] / "GPU_RUN1" / "scripts" / "build_colab_notebooks.py"
_SPEC = importlib.util.spec_from_file_location("gpu_run1_build_colab_notebooks", _TARGET)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(f"Cannot load {_TARGET}")
_MOD = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MOD)

validate_notebook = _MOD.validate_notebook
main = _MOD.main
OUT = _MOD.OUT
ROOT = _MOD.ROOT

if __name__ == "__main__":
    raise SystemExit(main())
