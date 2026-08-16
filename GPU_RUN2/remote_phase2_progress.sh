#!/usr/bin/env bash
set -eo pipefail
RUN=~/Layer-wise_Analysis_of_NSR_for_Discovering_GRD/results/runs/gpu_run2_20260815
python3 - <<PY
import json, time
from pathlib import Path
p = Path("$RUN") / "phase2"
now = time.time()
if not p.is_dir():
    print("no phase2")
else:
    for f in sorted(p.glob("*.json")):
        d = json.loads(f.read_text())
        age = now - f.stat().st_mtime
        if isinstance(d, dict) and "completed_eq_ids" in d:
            print(f"{f.name}: completed={len(d['completed_eq_ids'])} age_s={age:.0f}")
        elif isinstance(d, dict):
            print(f"{f.name}: dict keys={list(d)[:8]}")
        else:
            print(f"{f.name}: {type(d).__name__}")
PY
bash ~/remote_full_status.sh | head -n 25
