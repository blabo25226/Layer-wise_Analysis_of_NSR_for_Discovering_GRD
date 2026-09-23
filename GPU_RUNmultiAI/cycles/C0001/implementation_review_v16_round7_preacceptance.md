# C0001-T023 pre-acceptance independent review

Reviewer: Claude Opus 5.5, read-only; implementer: Cursor Agent; reviewer differs from implementer. Reviewed source `92fe0c7973ba23a8e71ad245005708d7b41eaac3` against frozen v16 and the round-7 PI resolution. Verdict: **BLOCK** before any new 510-B1/4,080-call acceptance packet. No full audit was run.

## P1 blockers

1. `src/gpu_runmultiai/reachability.py` synthetic identity fixture sets E2 equal to E1 but hard-codes `e2_oracle_equivalent=True`. Its E1 `0.04598*x_0` differs from Q4 `0.0460*x_0`, so a real E2-vs-Q4 oracle must not report equivalence. This currently tests fallback versus `preserved`, not the frozen precedence over `semantic_drift`. Compute oracle results using production-independent oracle functions; assert that clearing only the fallback flag would classify the same row as `semantic_drift`.
2. The auxiliary capped live observation runs inside `build_reachability_evidence` on the full counted audit path after counted work, with the audit resource monitor. An exception can abort a completed run, and its cost is absent from the timing projection. Restrict the live observation to the pre-closure acceptance/preflight path, or otherwise isolate it from full-run resources and record any failure without changing G_impl. Keep synthetic fixture as the frozen PASS criterion.

## Additional checks requested

- Mutation/negative tests for E2 raw inequality, E1 equivalent to Q4, and fallback precedence over drift.
- Test that live match/error cannot alter the synthetic fixture's `passed` value or append to counted call/stage-cache ledgers.
- Cross-check the live production row's own fallback flag against independently recomputed classification; label a second simplifier invocation as a re-run, not production E2 identity.
- Correct comments that call non-ledger probes “counted”; label eight-pair no-match as bounded only.

Positive observations: R6-1 fabricated production E2 is removed; frozen §3.8 synthetic predicates are represented honestly; capped live observation does not itself enter `G_impl` or the counted ledger. The reviewer did not run tests. The PI interrupted a separate full focused suite at 23 PASS after 441.61 s because this source requires P1 edits; that interrupted suite is **not** a PASS.
