#!/usr/bin/env bash
set -eo pipefail
cd ~/Layer-wise_Analysis_of_NSR_for_Discovering_GRD
python3 - <<'PY'
import json
from pathlib import Path
p = Path("results/runs/gpu_run2_ft_microbench_02/phase1")
m = json.loads((p / "manifest.json").read_text())
a = json.loads((p / "teacher_token_audit.json").read_text())
print("manifest_keys", {k: m[k] for k in ["n_problems", "n_variants_per_family", "n_train_points", "data_seeds", "noises", "smoke", "teacher_token_audit"]})
print("audit", {k: a[k] for k in ["n_problems", "n_ok", "max_observed", "max_token_len", "n_overflow"]})
# spot-check one saved row has teacher_expr
idx = json.loads((p / "index.json").read_text())
row = idx[0]
print("sample_eq", row.get("eq_id"), "teacher_len_chars", len(row.get("teacher_expr") or ""), "canonical_len_chars", len(row.get("canonical_expr") or ""))
print("teachers_differ", row.get("teacher_expr") != row.get("canonical_expr"))
PY
