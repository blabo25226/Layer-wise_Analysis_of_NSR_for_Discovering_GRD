#!/usr/bin/env bash
set -eo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT"

RUN_ID="${LANSR_RUN_ID:-gpu_run5_local}"
FROM_PHASE=0
TO_PHASE=9
SMOKE=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --run-id) RUN_ID="$2"; shift 2 ;;
    --from-phase) FROM_PHASE="$2"; shift 2 ;;
    --to-phase) TO_PHASE="$2"; shift 2 ;;
    --smoke) SMOKE=1; shift ;;
    *) echo "Unknown argument: $1" >&2; exit 2 ;;
  esac
done

export LANSR_RUN_ID="$RUN_ID"
export LANSR_RUN_DIR="$REPO_ROOT/results/runs/$RUN_ID"
export LANSR_ODEFORER_WEIGHTS="${LANSR_ODEFORER_WEIGHTS:-$REPO_ROOT/assets/odeformer/weights/odeformer.pt}"
export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}"
export PYTHONDONTWRITEBYTECODE=1
mkdir -p "$LANSR_RUN_DIR"

run_phase() {
  local phase="$1"
  local script="$2"
  if [[ "$phase" -lt "$FROM_PHASE" || "$phase" -gt "$TO_PHASE" ]]; then
    return 0
  fi
  if [[ ! -f "$script" ]]; then
    echo "Phase $phase entrypoint is not implemented: $script" >&2
    return 2
  fi
  local args=("$script" --run-id "$RUN_ID")
  if [[ "$SMOKE" -eq 1 ]]; then args+=(--smoke); fi
  local started ended rc
  started="$(date +%s)"
  set +e
  python "${args[@]}"
  rc=$?
  set -e
  ended="$(date +%s)"
  echo "$((ended - started))" > "$LANSR_RUN_DIR/phase${phase}_wall_seconds.txt"
  return "$rc"
}

run_phase 0 scripts/phases/gpu_run5_phase0_preflight.py
run_phase 1 scripts/phases/gpu_run5_phase1_decoded_support.py
for phase in 2 3 4 5 6 7 8 9; do
  run_phase "$phase" "scripts/phases/gpu_run5_phase${phase}.py"
done
