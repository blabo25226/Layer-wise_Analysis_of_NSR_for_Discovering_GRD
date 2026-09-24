# C0001-T025 implementation handoff — child guard durability (r5)

```yaml
task_id: C0001-T025
cycle: C0001
branch: ai/C0001/repo-operator/child-guard-durability
base_commit: 0016644a4f2903f00abc1616912ff2b518e20155
scope: r5 independent review REVISE_BEFORE_ACCEPTANCE (PI repair)
frozen_unchanged:
  - GPU_RUNmultiAI/cycles/C0001/preregistration_draft_v16.md
  - historical acceptance runs / r2 artifacts
```

## Summary

PI repair after Opus r5 review: no-receipt timeout/crash and JSON without a `guard_attempts` list now set `child_guard_accounting_uncertain=True`; durable side-channel rows still prove attempts. `run_b0_pair` simplifier path raises `GateAbortError` on uncertainty (counted and auxiliary), not `execution_failure`. Pre-unlink orphan rows merge into subprocess accounting; auxiliary/residual side-channel `stat` `OSError` fails closed.

## Files changed

| Path | Change |
|------|--------|
| `src/gpu_runmultiai/odeformer_runtime.py` | Uncertain accounting rules; pre-unlink orphan merge; success-path uncertainty; receipt helper |
| `src/gpu_runmultiai/pipeline.py` | Fail-closed `GateAbortError` on uncertain simplifier child guard |
| `src/gpu_runmultiai/reachability.py` | `OSError` on child side-channel `stat` → `GateAbortError` |
| `src/gpu_runmultiai/audit.py` | `OSError` on auxiliary residual channel `stat` → `GateAbortError` |
| `tests/test_gpu_runmultiai_c0001_metric_audit.py` | r5 regressions (timeout/crash/receipt, run_b0_pair, orphans, stat fail-closed, cleanup) |
| `GPU_RUNmultiAI/cycles/C0001/implementation_review_v16_child_guard_durability_r5.md` | PI transcription (review artifact) |

## Tests run

```bash
python -m compileall -q src scripts tests
PYTHONPATH=src:. python -m pytest -q tests/test_gpu_runmultiai_c0001_metric_audit.py -k \
  "child_guard or child_side_channel or simplifier_subprocess or auxiliary or orphan or residual or uncertain or match_path_simplifier or exception_after_child or preexisting_side_channel or without_receipt or guard_attempts_list or stat_oserror or run_b0_pair_simplifier"
```

## Finding disposition (r5)

| ID | Status |
|----|--------|
| MAJOR-1 | **Fixed** — empty timeout/crash without receipt uncertain; JSON lacking `guard_attempts` list uncertain |
| MAJOR-2 | **Fixed** — `run_b0_pair` simplifier raises `GateAbortError` on uncertainty (live probe + counted) |
| MINOR content dedupe | **Documented residual** — `_merge_guard_attempts` may collapse identical tuples |
| MINOR OSError stat | **Fixed** — fail closed on auxiliary/residual and orphan reconcile `stat` |
| MINOR orphan unlink | **Fixed** — load preexisting rows before child side-channel replacement |
| MINOR test cleanup | **Fixed** — `try/finally` around real `.runtime` child channel paths |

## Unresolved risks

- Content-key dedupe can still undercount repeated identical-path denials (any single denial still aborts).
- SIGKILL mid-append without a complete JSONL line still relies on fail-closed load; concurrent `.runtime` writers remain a process hazard.
- Full `test_gpu_runmultiai_c0001_metric_audit.py` module not run in this session (PI runs on final SHA).

## Next action

Parent: independent re-review on committed SHA; PI-authorized full focused pytest; then optional fresh acceptance.
