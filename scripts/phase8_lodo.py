"""Compat wrapper. Prefer scripts/phases/phase8_lodo.py."""
from __future__ import annotations

import runpy
import sys
from importlib import import_module
from pathlib import Path

_MODNAME = "scripts.phases.phase8_lodo"
_TARGET = Path(__file__).resolve().parent / "phases/phase8_lodo.py"

if __name__ == "__main__":
    sys.argv[0] = str(_TARGET)
    raise SystemExit(runpy.run_path(str(_TARGET), run_name="__main__"))

_impl = import_module(_MODNAME)
sys.modules[__name__] = _impl
