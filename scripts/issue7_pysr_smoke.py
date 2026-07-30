"""Compat wrapper. Prefer scripts/legacy/issue7_pysr_smoke.py."""
from __future__ import annotations

import runpy
import sys
from importlib import import_module
from pathlib import Path

_MODNAME = "scripts.legacy.issue7_pysr_smoke"
_TARGET = Path(__file__).resolve().parent / "legacy/issue7_pysr_smoke.py"

if __name__ == "__main__":
    sys.argv[0] = str(_TARGET)
    raise SystemExit(runpy.run_path(str(_TARGET), run_name="__main__"))

_impl = import_module(_MODNAME)
sys.modules[__name__] = _impl
