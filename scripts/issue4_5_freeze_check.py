"""Compat wrapper. Prefer scripts/legacy/issue4_5_freeze_check.py."""
from __future__ import annotations

import runpy
import sys
from importlib import import_module
from pathlib import Path

_MODNAME = "scripts.legacy.issue4_5_freeze_check"
_TARGET = Path(__file__).resolve().parent / "legacy/issue4_5_freeze_check.py"

if __name__ == "__main__":
    sys.argv[0] = str(_TARGET)
    raise SystemExit(runpy.run_path(str(_TARGET), run_name="__main__"))

_impl = import_module(_MODNAME)
sys.modules[__name__] = _impl
