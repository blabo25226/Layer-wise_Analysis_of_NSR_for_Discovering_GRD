#!/usr/bin/env bash
set -eo pipefail
cd ~/Layer-wise_Analysis_of_NSR_for_Discovering_GRD
python3 - <<'PY'
import json
from pathlib import Path
d = json.loads(Path("results/runs/gpu_run2_smoke_06/smoke_timing_summary.json").read_text())
keys = [
    "decode_count", "decode_p50", "decode_p90", "decode_p95", "timeout_count", "timeout_rate",
    "full_ft_count", "full_ft_mean", "single_layer_ft_count", "single_layer_ft_mean",
    "pysr_search_mean", "pysr_search_p95", "note",
    "phase0_seconds", "phase1_seconds", "phase2_seconds", "phase3_seconds",
    "phase4_seconds", "phase5_seconds", "total_seconds",
    "estimated_full_runtime_hours_p90",
]
for k in keys:
    print(f"{k}: {d.get(k)}")

p5 = Path("results/runs/gpu_run2_smoke_06/phase5")
skips = []
n = 0
for f in p5.rglob("*.json"):
    try:
        obj = json.loads(f.read_text())
    except Exception:
        continue
    rows = obj if isinstance(obj, list) else obj.get("records") or obj.get("results") or [obj]
    if not isinstance(rows, list):
        rows = [rows]
    for r in rows:
        if not isinstance(r, dict):
            continue
        n += 1
        if r.get("ft_skipped"):
            skips.append((f.name, r.get("ft_skipped"), r.get("eq_id") or r.get("condition")))
print("phase5_records", n, "ft_skipped", len(skips))
for s in skips[:8]:
    print(" skip", s)

log = Path("results/runs/gpu_run2_smoke_06/smoke_nohup.log").read_text(errors="ignore")
hits = []
for line in log.splitlines():
    low = line.lower()
    if any(x in low for x in ("ft_skipped", "length_eq", "empty", "teacher_token", "oom", "error")):
        if "warning" in low or "pkg_resources" in low:
            continue
        hits.append(line.strip()[:220])
print("log_hits", len(hits))
for h in hits[:15]:
    print(" LOG", h)
PY
