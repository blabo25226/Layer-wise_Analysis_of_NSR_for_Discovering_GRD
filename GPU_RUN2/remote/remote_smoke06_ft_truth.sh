#!/usr/bin/env bash
set -eo pipefail
cd ~/Layer-wise_Analysis_of_NSR_for_Discovering_GRD
python3 - <<'PY'
import json
from pathlib import Path
base = Path("results/runs/gpu_run2_smoke_06/phase5")
for name in [
    "checkpoint_main_validation_full_seed101_noise0.json",
    "checkpoint_structure_holdout_validation_full_seed101_noise0.json",
    "reproduction_main_validation.json",
    "hp_selected_main.json",
]:
    obj = json.loads((base/name).read_text())
    print("====", name)
    if isinstance(obj, dict):
        print("top", list(obj.keys())[:20])
        for k in ("identity", "metrics", "train_metrics", "ft_metrics", "completed_eq_ids", "n_completed"):
            if k in obj:
                print(k, obj[k])
        # nested
        for k,v in obj.items():
            if isinstance(v, dict) and any(x in k.lower() for x in ("metric", "train", "ft", "skip")):
                print("dict", k, v)
        if "records" in obj and obj["records"]:
            r0 = obj["records"][0]
            print("record0_keys", list(r0.keys())[:30])
            print("record0_snip", {k:r0.get(k) for k in ["eq_id","condition","failure_reason","decoder"]})
    print()

# phase1 of smoke06 teacher lengths?
p1 = Path("results/runs/gpu_run2_smoke_06/phase1")
if (p1/"catalogue.json").is_file():
    cat = json.loads((p1/"catalogue.json").read_text())
    print("smoke06 catalogue n", len(cat), "has_teacher", "teacher_expr" in cat[0])
    if "teacher_expr" in cat[0]:
        print("sample teacher", cat[0]["teacher_expr"][:80])
    else:
        print("sample keys", list(cat[0].keys()))
if (p1/"teacher_token_audit.json").is_file():
    print("audit", json.loads((p1/"teacher_token_audit.json").read_text()))
else:
    print("no teacher_token_audit in smoke06")
PY
