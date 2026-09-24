# C0001-T025 independent child-guard review r5

Reviewer: Claude Opus 5.5, read-only session `58328`, independent of Cursor implementer. Source: committed `0016644a4f2903f00abc1616912ff2b518e20155`. Scope: frozen v16 §11/§12, T025 handoff, source/tests. Reviewer did not run tests or SHA checks. No scientific-result claim.

## Verdict

`REVISE_BEFORE_ACCEPTANCE`. No CRITICAL findings. Two MAJOR findings leave the r4 child-guard evidence gap open.

## MAJOR findings

1. `odeformer_runtime.py` returns `child_guard_accounting_uncertain=False` for a timeout/nonzero crash with empty stdout and no durable rows. A killed child cannot run `atexit`/`finally` and may die between appending an attempt in memory and fsync. A JSON object without a `guard_attempts` list is also treated as certainty. The existing timeout test checks only `failure_reason`.
2. The first simplifier call inside live auxiliary `run_b0_pair` ignores `child_guard_accounting_uncertain`; only the later match-path rerun checks it. The live probe can record a synthetic PASS with no guard uncertainty marker.

## MINOR findings

- Content-key dedupe undercounts repeated genuine denials of the same path; any denial still aborts, but count evidence can be wrong.
- `OSError` on auxiliary/residual side-channel `stat` is treated as okay instead of fail-closed.
- Unlinking the child side channel before every call can erase orphan rows; inspect/merge or fail closed before replacement.
- Some tests write the real per-worktree `.runtime` path without `try/finally` cleanup and do not test the real child worker's pre-kill durability.

## PI resolution and required repair

PI rejects `0016644` for a new acceptance. Make no-receipt timeout/crash uncertain; require a structured worker receipt with a `guard_attempts` list to prove zero rows. Propagate uncertainty from **both** the first live-probe simplifier and the later rerun, and fail closed before counted work. PI also resolves the counted-path protocol conservatively: a child crash/timeout without complete guard accounting must not certify G4 zero attempts; record a deviation and fail closed globally instead of silently classifying it as an ordinary execution failure. Add focused timeout/crash/first-call tests, fail closed on side-channel `OSError`, and preserve the frozen plan and prior artifacts. Re-run full focused suite on the final committed source and seek independent review before a fresh acceptance.

This file is a PI transcription of the independent reviewer message, not a verbatim log.
