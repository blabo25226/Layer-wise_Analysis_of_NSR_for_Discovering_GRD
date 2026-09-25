# Independent Claude Opus 5.5 review — C0001-T026 r2

- Source: `78cafb00250471513eefcb42aa9ba702c960e536` (Cursor Agent implementation).
- Reviewer: Claude Opus 5.5, read-only; different from implementer, `reviewer_diff_assertion=true`.
- Reviewer method: direct source/test reading; no shell, Git diff, SHA, or test execution. The PI separately ran the complete focused conda suite on this exact commit: **163 passed in 2167.37s**.
- Verdict: **PASS_TO_PI_GATE with conditions**, not implementation closure, fresh-acceptance authorization, full-audit authorization, or a scientific result.

The r1 MAJOR orphan-reconcile post-stat read failure is closed: `reachability.py` now uses `load_durable_side_channel_attempts`, which raises `GateAbortError` for stat/read/non-regular/malformed cases. The audit residual check uses the same loader; acceptance requires `--fail-if-exists`; absent fingerprint artifacts now have null paths/hash. Frozen scientific endpoints did not change.

## Remaining review findings

1. **M1 — late freshness guard:** `audit.py` writes an initializing manifest and truncates the deviation log before `_run_implementation_acceptance` checks `fail_if_exists`. An invocation missing the flag into an existing directory can destroy prior evidence before aborting. Move the check before any output writes; test that pre-existing files remain byte-identical.
2. **M2 — shared runtime tests:** several older tests still touch the real `.runtime` child channel; new isolated tests alone do not cover the suite. Keep tests away from an active acceptance checkout and ideally isolate the whole suite.
3. **M3 — coverage:** no completed acceptance-manifest assertion for the new freshness/G4 fields and no new first-call/worker-termination fixture; direct read-error test does not traverse the whole live-observation wrapper.
4. **M4 — stale rows:** the reachability live path removes a pre-existing shared side-channel file without first recording/aborting on its rows. Preserve or fail closed on prior crashed-child evidence.
5. Pre-existing durable JSONL reader can truncate a torn last row; old loader remains on non-acceptance paths. Handoff file still describes r1 only.

PI interpretation: M1 and M4 are evidence-preservation issues and remain closure-blocking despite the review's conditional PASS. No fresh acceptance is launched while GitHub credentials are invalid. After authentication recovery, request a narrow Cursor revision for M1/M4 and pragmatic shared-channel test isolation, then rerun affected tests and independent diff review. Preserve r6 and all historical run directories.
