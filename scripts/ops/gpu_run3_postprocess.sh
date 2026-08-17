#!/usr/bin/env bash
# Post-processing for a finished GPU_RUN3 run.
#
# Waits for the sequential runner to exit, then:
#   1. re-runs Phase 5 so the DecoderLens trajectory uses the greedy rollout
#      (the in-run Phase 5 predates that fix and wrote NaN TEDs)
#   2. re-scores every stored formula under one canonicalization
#   3. writes a provenance note recording that analysis code changed mid-campaign
#   4. builds the plan section 18 reports and tables
#
# Usage: bash scripts/ops/gpu_run3_postprocess.sh <run-id> [runner-pid]
set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT"

RUN_ID="${1:?usage: gpu_run3_postprocess.sh <run-id> [runner-pid]}"
RUNNER_PID="${2:-}"
PY=/home/blabo/miniconda3/envs/lansr310/bin/python
RUN_DIR="$REPO_ROOT/results/runs/$RUN_ID"

if [[ -n "$RUNNER_PID" ]]; then
  echo "[postprocess] waiting for runner pid $RUNNER_PID to exit"
  while kill -0 "$RUNNER_PID" 2>/dev/null; do sleep 30; done
  echo "[postprocess] runner exited"
fi

step() { echo "[postprocess] === $* ==="; }

step "Phase 5 re-run (greedy rollout)"
if [[ -d "$RUN_DIR/phase5" ]]; then
  mv "$RUN_DIR/phase5" "$RUN_DIR/phase5_before_rollout_fix" 2>/dev/null || true
fi
$PY scripts/phases/gpu_run3_phase5_decoderlens.py --run-id "$RUN_ID" || echo "[postprocess] phase5 re-run FAILED"

step "structural metric recompute"
$PY scripts/reports/gpu_run3_recompute_structural.py --run-id "$RUN_ID" || echo "[postprocess] recompute FAILED"

step "provenance note"
$PY - "$RUN_ID" <<'PYEOF' || echo "[postprocess] provenance note FAILED"
import json, subprocess, sys
from pathlib import Path

run_id = sys.argv[1]
run_dir = Path("results/runs") / run_id
head = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
preflight = json.loads((run_dir / "phase0" / "preflight.json").read_text())
note = {
    "run_id": run_id,
    "commit_at_preflight": (preflight.get("git") or {}).get("commit"),
    "commit_at_postprocess": head,
    "single_frozen_commit": False,
    "explanation": (
        "Analysis code was corrected during the campaign, so phases did not all run at "
        "one commit. Phases 0-3 ran before the canonicalization fixes; phases 4-9 ran "
        "after the probe-ridge fix. Structural metrics for every stored formula are "
        "therefore re-derived once, after the run, by "
        "scripts/reports/gpu_run3_recompute_structural.py, and the original values are "
        "retained as *_as_recorded so the effect of each change stays auditable."
    ),
    "changes_during_run": [
        {
            "change": "probe ridge selected on an inner analysis_train split",
            "reason": "fixed penalty gave held-out R2 of order -1e13 at 512 features",
            "phases_affected": "4 onward (ran after the change)",
        },
        {
            "change": "fold arithmetic identities (0+x, 1*x, x-0, 0*x, x/1, x**1)",
            "reason": "BFGS-fitted constants made correct recoveries score exact=0",
            "phases_affected": "written after phases 2-3; applied to all via recompute",
        },
        {
            "change": "normalize signs (a-b -> a+neg(b), -1*b -> neg(b))",
            "reason": "plan section 11 requires sign handling to be fixed; it was absent",
            "phases_affected": "written after phases 2-3; applied to all via recompute",
        },
        {
            "change": "greedy rollout in the encoder DecoderLens trajectory",
            "reason": "appending one symbol left placeholders, so every TED was NaN",
            "phases_affected": "phase 5 re-run after the pipeline finished",
        },
    ],
    "test_split_evaluations": 1,
    "test_split_note": (
        "analysis_test was evaluated once, by phase 8, under the conditions frozen in "
        "phase 7. The phase 5 re-run and the recompute pass touch validation-side and "
        "stored-formula artefacts only; neither re-evaluates the test split."
    ),
}
path = run_dir / "provenance_note.json"
path.write_text(json.dumps(note, indent=2) + "\n", encoding="utf-8")
print(f"wrote {path}")
PYEOF

step "reports and tables"
$PY scripts/reports/gpu_run3_report.py --run-id "$RUN_ID" || echo "[postprocess] report FAILED"

step "done"
ls -la "$RUN_DIR"
