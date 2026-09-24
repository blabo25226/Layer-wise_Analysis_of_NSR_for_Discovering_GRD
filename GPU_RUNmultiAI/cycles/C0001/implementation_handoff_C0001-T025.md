# C0001-T025 implementation handoff — child guard durability (r4)

```yaml
task_id: C0001-T025
cycle: C0001
branch: ai/C0001/repo-operator/child-guard-durability
base_commit: 86d089123226dfef434d8e0921f5f37d3afa81fc
scope: r4 review MAJOR-1 / MINOR-1,3,4,5 (+ document MINOR-2)
frozen_unchanged:
  - GPU_RUNmultiAI/cycles/C0001/preregistration_draft_v16.md
  - historical acceptance runs / r2 artifacts
```

## Summary

Closed the r4 evidence hole where simplifier child timeout/early crash could lose sealed-path denied attempts while the live auxiliary probe reported zero child attempts. Child worker now durably appends deny rows before exit; parent subprocess wrapper merges timeout side-channel rows and flags uncertain accounting; auxiliary live probe fails closed on uncertainty or malformed durable rows. Idempotent child-attempt merge and always-on orphan reconcile prevent duplicate auxiliary counts. Acceptance re-checks residual denied rows on the auxiliary JSONL before reachability.

## Files changed

| Path | Change |
|------|--------|
| `src/gpu_runmultiai/simplifier_worker.py` | Durable per-deny flush, atexit/finally, lazy ODEFormer import inside `main` |
| `src/gpu_runmultiai/odeformer_runtime.py` | Side-channel merge on timeout; `child_guard_accounting_uncertain` |
| `src/gpu_runmultiai/reachability.py` | Fail-closed on uncertain accounting; always reconcile orphans in `finally`; sink dedupe |
| `src/gpu_runmultiai/sealed_guard.py` | Idempotent `extend_child_attempts` |
| `src/gpu_runmultiai/guard_side_channel.py` | Non-dict row fail-closed |
| `src/gpu_runmultiai/jsonl_durable.py` | Invalid UTF-8 fail-closed |
| `src/gpu_runmultiai/audit.py` | `_assert_no_residual_auxiliary_denied_attempts` before acceptance reachability |
| `tests/test_gpu_runmultiai_c0001_metric_audit.py` | r4 regressions (timeout merge, malformed channel, ordering, orphans, residual aux) |

## Tests run

```bash
python -m compileall -q src scripts tests
PYTHONPATH=src:. python -m pytest -q tests/test_gpu_runmultiai_c0001_metric_audit.py -k \
  "child_guard or child_side_channel or simplifier_subprocess or auxiliary or orphan or residual or acceptance_resume_invalid or malformed_child or uncertain_child or match_path_simplifier or exception_after_child"
```

Result: **14 passed** (focused subset; full module not run in this worktree to avoid collision with parallel C0001-T024 full pytest).

## Finding disposition

| ID | Status |
|----|--------|
| MAJOR-1 | **Fixed** — durable child deny logging + parent timeout side-channel merge + auxiliary fail-closed on `child_guard_accounting_uncertain` |
| MINOR-1 | **Fixed** — idempotent `extend_child_attempts`, sink dedupe, always reconcile in probe `finally` |
| MINOR-2 | **Documented residual** — child side channel remains `GPU_RUNmultiAI/.runtime/guard_attempts_side_channel.jsonl` per worktree; do not run concurrent audit/pytest writers in one worktree |
| MINOR-3 | **Fixed** — `test_acceptance_resume_invalid_identity_verifies_before_clear_stale` |
| MINOR-4 | **Fixed** — non-dict / invalid UTF-8 JSONL → `AuditInvariantError` → `GateAbortError` on auxiliary path |
| MINOR-5 | **Fixed** — `_assert_no_residual_auxiliary_denied_attempts` before acceptance reachability |

## Unresolved risks

- SIGKILL mid-append without a complete JSONL line still relies on `truncate_partial_suffix` + fail-closed load; extremely concurrent `.runtime` writers remain a process hazard (MINOR-2).
- Fresh implementation acceptance still requires PI-authorized empty output dir and no concurrent jobs in this worktree.

## Next action

Parent: await C0001-T024 full focused pytest on the same commit; then PI may authorize one fresh `--fail-if-exists` acceptance only after r4 closure review.
