#!/usr/bin/env bash
set -eo pipefail
cd ~/Layer-wise_Analysis_of_NSR_for_Discovering_GRD
echo "=== git ==="
git status --short | head -50 || true
git log -1 --oneline || true
echo "=== ckpt ==="
ls -lh assets/nesymres/weights/100M.ckpt
echo "=== gpu ==="
nvidia-smi --query-gpu=index,name,memory.used,memory.total --format=csv
echo "=== runs ==="
ls results/runs
echo "=== smoke06 ==="
if [[ -f results/runs/gpu_run2_smoke_06/smoke_timing_summary.json ]]; then
  python3 - <<'PY'
import json
from pathlib import Path
p=Path("results/runs/gpu_run2_smoke_06/smoke_timing_summary.json")
d=json.loads(p.read_text())
print("timing_keys", sorted(d.keys())[:40])
for k in sorted(d):
    if "estimat" in k.lower() or k in ("total_seconds","status","decode"):
        print(k, d[k] if not isinstance(d[k], dict) else {kk:d[k].get(kk) for kk in list(d[k])[:12]})
PY
else
  echo "no smoke_timing_summary.json"
  ls results/runs/gpu_run2_smoke_06 2>/dev/null | head || echo "no smoke06 dir"
fi
echo "=== smoke06 phases ==="
ls results/runs/gpu_run2_smoke_06 2>/dev/null
echo "=== microbench02 ==="
python3 - <<'PY'
import json
from pathlib import Path
base=Path("results/runs/gpu_run2_ft_microbench_02/phase1")
m=json.loads((base/"manifest.json").read_text())
a=json.loads((base/"teacher_token_audit.json").read_text())
print("phase1", {k:m.get(k) for k in ["n_problems","n_train_points","n_eval_points","data_seeds","noises","smoke","status"]})
print("audit", {k:a.get(k) for k in ["n_ok","max_observed","n_overflow","n_tokenize_fail"]})
PY
# compare key source files vs expected teacher helpers
python3 - <<'PY'
from pathlib import Path
p=Path("src/data/gnw_synthetic.py").read_text()
print("has_compact_teacher", "_compact_teacher_expression" in p)
print("has_teacher_field", "teacher_expr: str" in p)
print("has_nesymres_tokenize", Path("src/data/nesymres_tokenize.py").is_file())
print("phase1_audit_call", "assert_all_teachers_within_length_eq" in Path("scripts/phases/gpu_run2_phase1_data.py").read_text())
PY
