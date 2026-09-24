# C0001-T025 implementation handoff — child guard durability (r6)

```yaml
task_id: C0001-T025
cycle: C0001
branch: ai/C0001/repo-operator/child-guard-durability
base_commit: c2067c252168d19e7d8946a6ae4e8e2a40915e3c
scope: r6 independent review REVISE_BEFORE_ACCEPTANCE (Python 3.10 Path stat fail-closed)
frozen_unchanged:
  - GPU_RUNmultiAI/cycles/C0001/preregistration_draft_v16.md
  - historical acceptance runs / r2 artifacts
  - GPU_RUNmultiAI/.runtime/ (not committed)
```

## Summary

r6 repair: auxiliary residual and orphan reconcile helpers no longer call `Path.is_file()` before guarded `stat()`. On Python 3.10 (`lansr310`), `is_file()` can re-raise non-ignorable `OSError` and bypass `GateAbortError` conversion (live probe `error_isolated=true` risk). Each helper now uses a single `stat()`; only `FileNotFoundError` means absent; any other `OSError` → `GateAbortError`. `_load_child_side_channel_attempts` in `odeformer_runtime.py` follows the same rule.

## Files changed

| Path | Change |
|------|--------|
| `src/gpu_runmultiai/audit.py` | `_assert_no_residual_auxiliary_denied_attempts`: stat-only presence check |
| `src/gpu_runmultiai/reachability.py` | `_reconcile_orphan_child_process_guard_side_channel`: stat-only presence check |
| `src/gpu_runmultiai/odeformer_runtime.py` | `_load_child_side_channel_attempts`: stat-only; `GateAbortError` on stat `OSError` |
| `tests/test_gpu_runmultiai_c0001_metric_audit.py` | Orphan stat_oserror test cleanup without patched `is_file()` |
| `GPU_RUNmultiAI/cycles/C0001/implementation_review_v16_child_guard_durability_r6.md` | PI transcription (review artifact) |

## Tests run (conda `lansr310`, not system Python)

```bash
python -m compileall -q src scripts tests
PYTHONPATH=src:. python -m pytest -q tests/test_gpu_runmultiai_c0001_metric_audit.py -k \
  "child_guard or child_side_channel or simplifier_subprocess or auxiliary or orphan or residual or uncertain or match_path_simplifier or exception_after_child or preexisting_side_channel or without_receipt or guard_attempts_list or stat_oserror or run_b0_pair_simplifier"
```

**Result:** `19 passed, 133 deselected in 133.73s` on committed source SHA recorded below after push.

**Not run this session:** full `test_gpu_runmultiai_c0001_metric_audit.py` module (~40 min). PI interrupted prior c2067c2 run at `23 passed in 301.63s`; that run is **not PASS** for acceptance.

## Finding disposition (r6)

| ID | Status |
|----|--------|
| MAJOR Python 3.10 `is_file` before `stat` | **Fixed** — one guarded `stat()` in residual/orphan helpers and child side-channel loader |
| r5 closures (timeout/receipt, run_b0_pair uncertainty, pre-unlink merge) | **Unchanged** — still closed in c2067c2 lineage |

## Closure-only residuals (documented, not expanded in r6)

- Other `OSError` during counted side-channel read/unlink may still surface as ordinary execution failure; incomplete guard accounting fail-closed before closure remains a separate hardening item.
- Preexisting child rows merged into later calls can mask later uncertainty; any denied row still prevents G4 PASS.
- Content-key dedupe undercounts repeated identical denials.
- Resume can lose child-denial evidence; no resume-based acceptance/full audit until fixed or explicitly gated.
- `simplify_tree_subprocess` still uses `side_channel.is_file()` before `unlink()` (not on the r6 blocking path; same class of risk if extended).
- Test gaps: direct first-call fixture, real-worker kill path.

## Next action

Parent: independent re-review on final committed SHA; PI-authorized full focused pytest on same SHA; then optional fresh acceptance (no acceptance/full audit in this task).
