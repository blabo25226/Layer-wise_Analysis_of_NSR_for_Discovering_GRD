#!/usr/bin/env bash
# Sequential GPU_RUN4 runner.
# Usage:
#   bash scripts/ops/run_gpu_run4.sh --run-id gpu_run4_phase0_01
#   bash scripts/ops/run_gpu_run4.sh --smoke --run-id gpu_run4_smoke_01 --allow-cpu
set -eo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT"

RUN_ID="${LANSR_RUN_ID:-gpu_run4_local}"
FROM_PHASE=0
TO_PHASE=1
SMOKE=0
DRY_RUN=0
ALLOW_CPU=0
SKIP_DOWNLOAD=0
SKIP_DEMO=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --run-id) RUN_ID="$2"; shift 2 ;;
    --from-phase) FROM_PHASE="$2"; shift 2 ;;
    --to-phase) TO_PHASE="$2"; shift 2 ;;
    --smoke) SMOKE=1; shift ;;
    --dry-run) DRY_RUN=1; shift ;;
    --allow-cpu) ALLOW_CPU=1; shift ;;
    --skip-download) SKIP_DOWNLOAD=1; shift ;;
    --skip-demo) SKIP_DEMO=1; shift ;;
    *) echo "Unknown arg: $1" >&2; exit 2 ;;
  esac
done

export LANSR_RUN_ID="$RUN_ID"
export LANSR_ODEFORER_WEIGHTS="${LANSR_ODEFORER_WEIGHTS:-$REPO_ROOT/assets/odeformer/weights/odeformer.pt}"
export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}"
export PYTHONDONTWRITEBYTECODE=1

RUN_DIR="$REPO_ROOT/results/runs/$RUN_ID"
export LANSR_RUN_DIR="$RUN_DIR"
mkdir -p "$RUN_DIR"

run_phase() {
  local phase="$1"
  local label="$2"
  shift 2
  if [[ "$phase" -lt "$FROM_PHASE" || "$phase" -gt "$TO_PHASE" ]]; then
    echo "Skipping Phase $phase (FROM_PHASE=$FROM_PHASE TO_PHASE=$TO_PHASE)"
    return 0
  fi
  echo "=== GPU_RUN4 Phase $phase ($label) ==="
  local started ended elapsed rc
  started="$(date +%s)"
  set +e
  python "$@"
  rc=$?
  set -e
  ended="$(date +%s)"
  elapsed=$((ended - started))
  echo "Phase $phase ($label) finished in ${elapsed}s (exit $rc)"
  echo "$elapsed" > "$RUN_DIR/phase${phase}_${label}_wall_seconds.txt"
  if [[ "$rc" -ne 0 ]]; then
    # Phase 0 may be incomplete because the public checkpoint is not the paper table.
    # Phase 1 still freezes evaluation on that run if preflight.json exists.
    if [[ "$phase" -eq 0 && "$TO_PHASE" -ge 1 && -f "$RUN_DIR/phase0/preflight.json" ]]; then
      echo "Phase 0 incomplete (exit $rc); continuing because Phase 1 only needs preflight.json."
      return 0
    fi
    return "$rc"
  fi
}

PHASE0=(scripts/phases/gpu_run4_phase0_preflight.py --run-id "$RUN_ID")
if [[ "$ALLOW_CPU" -eq 1 ]]; then PHASE0+=(--allow-cpu); fi
if [[ "$DRY_RUN" -eq 1 ]]; then PHASE0+=(--dry-run); fi
if [[ "$SMOKE" -eq 1 ]]; then PHASE0+=(--smoke); fi
if [[ "$SKIP_DOWNLOAD" -eq 1 ]]; then PHASE0+=(--skip-download); fi
if [[ "$SKIP_DEMO" -eq 1 ]]; then PHASE0+=(--skip-demo); fi
run_phase 0 preflight "${PHASE0[@]}"

PHASE1=(scripts/phases/gpu_run4_phase1_eval.py --run-id "$RUN_ID")
if [[ "$ALLOW_CPU" -eq 1 ]]; then PHASE1+=(--allow-cpu); fi
if [[ "$DRY_RUN" -eq 1 ]]; then PHASE1+=(--dry-run); fi
if [[ "$SMOKE" -eq 1 ]]; then PHASE1+=(--smoke); fi
run_phase 1 eval "${PHASE1[@]}"

echo "GPU_RUN4 finished run-id=$RUN_ID (implemented through Phase 1)"
