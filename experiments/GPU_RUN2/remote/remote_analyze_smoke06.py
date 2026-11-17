#!/usr/bin/env python
from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path

run = Path.home() / "Layer-wise_Analysis_of_NSR_for_Discovering_GRD/results/runs/gpu_run2_smoke_06"
log = (run / "smoke_nohup.log").read_text(encoding="utf-8", errors="replace")
walls = re.findall(r"Phase (\d+) finished in (\d+)s", log)
print("wall_events", walls)
acc: dict[int, int] = defaultdict(int)
for phase, seconds in walls:
    acc[int(phase)] += int(seconds)
print("phase_sum", dict(sorted(acc.items())), "total", sum(acc.values()))

secs: list[float] = []
for path in run.rglob("*.json"):
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        continue
    rows = data if isinstance(data, list) else data.get("records") or data.get("rows") or []
    if isinstance(data, dict) and not rows:
        rows = [data]
    if not isinstance(rows, list):
        continue
    for row in rows:
        if isinstance(row, dict) and "process_seconds" in row:
            secs.append(float(row["process_seconds"]))

nonzero = sorted(s for s in secs if s > 0)


def pct(vals: list[float], q: float) -> float | None:
    if not vals:
        return None
    k = (len(vals) - 1) * q
    f = int(k)
    c = min(f + 1, len(vals) - 1)
    return vals[f] if f == c else vals[f] + (vals[c] - vals[f]) * (k - f)


print(
    "process_seconds",
    {
        "n": len(secs),
        "zeros": sum(1 for s in secs if s == 0),
        "mean_all": (sum(secs) / len(secs)) if secs else None,
        "nonzero_mean": (sum(nonzero) / len(nonzero)) if nonzero else None,
        "p50": pct(nonzero, 0.5),
        "p90": pct(nonzero, 0.9),
        "p95": pct(nonzero, 0.95),
        "max": max(nonzero) if nonzero else None,
    },
)

ft = []
for path in (run / "phase5").rglob("*_records.json"):
    for row in json.loads(path.read_text(encoding="utf-8")):
        if row.get("ft_metrics"):
            ft.append((path.name, row.get("condition"), row.get("ft_metrics"), row.get("split_view")))
print("ft_metrics_n", len(ft))
print("ft_samples", ft[:10])
print("candidates", json.loads((run / "phase3/candidate_layers.json").read_text())["candidates"])
print("timing_file", json.loads((run / "smoke_timing_summary.json").read_text()))
