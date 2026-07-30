#!/usr/bin/env python
"""Compat wrapper. Prefer GPU_RUN1/scripts/reanalysis_figures.py."""

from __future__ import annotations

import runpy
import sys
from pathlib import Path

_TARGET = Path(__file__).resolve().parents[1] / "GPU_RUN1" / "scripts" / "reanalysis_figures.py"

if __name__ == "__main__":
    sys.argv[0] = str(_TARGET)
    raise SystemExit(runpy.run_path(str(_TARGET), run_name="__main__"))
