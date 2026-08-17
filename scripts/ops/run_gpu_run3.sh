#!/usr/bin/env bash
# Sequential GPU_RUN3 runner.
# Usage:
#   bash scripts/ops/run_gpu_run3.sh --smoke --run-id gpu_run3_smoke_01
#   bash scripts/ops/run_gpu_run3.sh --from-phase 1 --run-id <id>
set -eo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT"

RUN_ID="${LANSR_RUN_ID:-gpu_run3_local}"
FROM_PHASE=0
TO_PHASE=9
SMOKE=0
DRY_RUN=0
ALLOW_CPU=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --run-id) RUN_ID="$2"; shift 2 ;;
    --from-phase) FROM_PHASE="$2"; shift 2 ;;
    --to-phase) TO_PHASE="$2"; shift 2 ;;
    --smoke) SMOKE=1; shift ;;
    --dry-run) DRY_RUN=1; shift ;;
    --allow-cpu) ALLOW_CPU=1; shift ;;
    *) echo "Unknown arg: $1" >&2; exit 2 ;;
  esac
done

export LANSR_RUN_ID="$RUN_ID"
export LANSR_ND2_WEIGHTS="${LANSR_ND2_WEIGHTS:-$REPO_ROOT/assets/nd2/weights/checkpoint.pth}"
export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}"

RUN_DIR="$REPO_ROOT/results/runs/$RUN_ID"
export LANSR_RUN_DIR="$RUN_DIR"
mkdir -p "$RUN_DIR"

COMMON=(--run-id "$RUN_ID")
if [[ "$SMOKE" -eq 1 ]]; then COMMON+=(--smoke); fi
if [[ "$DRY_RUN" -eq 1 ]]; then COMMON+=(--dry-run); fi
if [[ "$ALLOW_CPU" -eq 1 ]]; then COMMON+=(--allow-cpu); fi

run_phase() {
  local phase="$1"
  local label="$2"
  shift 2
  if [[ "$phase" -lt "$FROM_PHASE" || "$phase" -gt "$TO_PHASE" ]]; then
    echo "Skipping Phase $phase (FROM_PHASE=$FROM_PHASE TO_PHASE=$TO_PHASE)"
    return 0
  fi
  echo "=== GPU_RUN3 Phase $phase ($label) ==="
  local started ended elapsed
  started="$(date +%s)"
  python "$@"
  ended="$(date +%s)"
  elapsed=$((ended - started))
  echo "Phase $phase ($label) finished in ${elapsed}s"
  echo "$elapsed" > "$RUN_DIR/phase${phase}_${label}_wall_seconds.txt"
}

PHASE0=(scripts/phases/gpu_run3_phase0_preflight.py --run-id "$RUN_ID")
if [[ "$ALLOW_CPU" -eq 1 ]]; then PHASE0+=(--allow-cpu); fi
run_phase 0 preflight "${PHASE0[@]}"
run_phase 1 policy scripts/phases/gpu_run3_phase1_policy.py "${COMMON[@]}"
run_phase 2 pipeline scripts/phases/gpu_run3_phase2_pipeline.py "${COMMON[@]}"
run_phase 3 benchmark scripts/phases/gpu_run3_phase3_benchmark.py "${COMMON[@]}"
run_phase 4 probes scripts/phases/gpu_run3_phase4_probes.py "${COMMON[@]}"
run_phase 5 decoderlens scripts/phases/gpu_run3_phase5_decoderlens.py "${COMMON[@]}"
run_phase 6 causal scripts/phases/gpu_run3_phase6_causal.py "${COMMON[@]}"
run_phase 7 selective_ft scripts/phases/gpu_run3_phase7_selective_ft.py "${COMMON[@]}"
run_phase 8 test scripts/phases/gpu_run3_phase8_test.py "${COMMON[@]}"
run_phase 9 pretrain_dist scripts/phases/gpu_run3_phase9_pretrain_dist.py "${COMMON[@]}"

echo "GPU_RUN3 finished run-id=$RUN_ID"
