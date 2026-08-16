#!/usr/bin/env bash
# Quick status for gpu_run2_20260815 full run
set -eo pipefail
RUN=~/Layer-wise_Analysis_of_NSR_for_Discovering_GRD/results/runs/gpu_run2_20260815
cd ~/Layer-wise_Analysis_of_NSR_for_Discovering_GRD
echo "=== processes ==="
pgrep -af 'run_gpu_run2|gpu_run2_phase' || echo NONE
echo "=== gpu ==="
nvidia-smi --query-gpu=index,name,utilization.gpu,memory.used,memory.total --format=csv
echo "=== run dir ==="
ls -la "$RUN" 2>/dev/null || echo missing
echo "=== phase walls ==="
for p in 0 1 2 3 4 5; do
  f="$RUN/phase${p}_wall_seconds.txt"
  if [[ -f "$f" ]]; then echo "phase$p $(cat "$f")s"; fi
done
echo "=== teacher audit ==="
if [[ -f "$RUN/phase1/teacher_token_audit.json" ]]; then
  python3 -c "import json;from pathlib import Path;a=json.loads(Path('$RUN/phase1/teacher_token_audit.json').read_text());print({k:a.get(k) for k in ['n_ok','max_observed','n_overflow','n_problems']})"
fi
echo "=== log tail ==="
tail -n 25 "$RUN/nohup_full.log" 2>/dev/null || true
echo "=== errors in log ==="
grep -E 'Error|Traceback|RuntimeError|OOM|FAIL|FileNotFoundError' "$RUN/nohup_full.log" 2>/dev/null | tail -n 20 || true
