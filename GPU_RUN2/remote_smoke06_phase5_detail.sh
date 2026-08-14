#!/usr/bin/env bash
set -eo pipefail
cd ~/Layer-wise_Analysis_of_NSR_for_Discovering_GRD
python3 - <<'PY'
import json
from pathlib import Path
from collections import Counter
p5 = Path("results/runs/gpu_run2_smoke_06/phase5")
cond = Counter()
trainable = Counter()
keys_sample = Counter()
for f in sorted(p5.rglob("*.json")):
    try:
        obj = json.loads(f.read_text())
    except Exception as e:
        print("bad", f, e)
        continue
    if f.name.startswith("hp_") or "aggregate" in f.name or "manifest" in f.name:
        print("meta", f.relative_to(p5), type(obj).__name__, list(obj)[:8] if isinstance(obj, dict) else "")
        continue
    rows = obj if isinstance(obj, list) else obj.get("records") or []
    if isinstance(obj, dict) and not rows:
        # checkpoint style
        rows = obj.get("records") or []
        if "condition" in obj:
            cond[obj.get("condition")] += 1
    for r in rows:
        if not isinstance(r, dict):
            continue
        for k in r:
            keys_sample[k] += 1
        c = r.get("condition") or r.get("method") or "?"
        cond[c] += 1
        m = r.get("metrics") or r.get("train_metrics") or {}
        if isinstance(m, dict) and "trainable" in m:
            trainable[int(float(m["trainable"]) > 0)] += 1
        if r.get("ft_skipped"):
            trainable["skipped"] += 1
print("conditions", cond.most_common(20))
print("trainable_pos", trainable)
print("top_keys", keys_sample.most_common(25))
# list phase5 files
for f in sorted(p5.rglob("*")):
    if f.is_file():
        print("file", f.relative_to(p5), f.stat().st_size)
PY
