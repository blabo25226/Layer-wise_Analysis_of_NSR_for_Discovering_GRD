# C0001-T024 independent source review r3 (Claude Opus 5.5)

Date: 2026-09-24. Scope: uncommitted safety revision against task-branch HEAD `456d8be`; frozen v16 preregistration and prior r2 review. This is a read-only source review, not a test-result or experiment review. No scientific result is asserted.

## Verdict

`PASS_TO_ONE_FRESH_ACCEPTANCE_ONLY`, conditional. No critical or major source finding for the three r2 issues, but minor evidence-integrity issues below must be fixed or explicitly waived before closure. PI has **not** accepted this as final closure or authorized a full audit. The independent reviewer did not run shell checks or tests. A separate PI focused suite subsequently showed at least one failing test; its final outcome is pending.

## Primary observations

- Match-path extra simplifier child attempts are merged in `reachability.py` and flushed to the auxiliary sink on normal return. Exception-after-child uses a `finally` flush; missing sink raises `GateAbortError` through fixture wrappers.
- `audit.py` writes auxiliary rows in `finally`, then aborts before any counted call on a denied row. This is stricter than a late G4 failure; the §11/G4 interpretation needs explicit independent approval in the deviation record before closure.
- `abort_manifest.json` is archived before subsequent writes. Invalid/no-ledger resume cannot silently start fresh. The old abort is archived only after identity/closure/fingerprint validation in normal resume flow, though an invalid attempt's new abort necessarily archives it too.

## Minor findings and conditions

1. A simplifier subprocess can raise after child work but before its `guard_attempts` reach the probe guard (e.g. malformed `.runtime/guard_attempts_side_channel.jsonl`); `except Exception` then emits `error_isolated=true`. A timeout can also lose worker rows written only on exit. Treat any `error_isolated=true` as non-certifying; investigate/fix before closure.
2. A match-path test patches `gpu_runmultiai.pipeline.detect_e2_identity_fallback_candidate`, but `reachability.py` imported the function directly; the patch is ineffective and the branch is reached incidentally. Make the test deterministic.
3. The P3 ordering test cannot distinguish archiving before versus after identity validation, because abort writing also archives. Add a direct ordering assertion and acceptance-resume mismatch coverage.
4. Invalid resume still rewrites `audit_manifest.json`, appends deviation terminators and may truncate ledger during `CallLogger.load` before identity is checked. Existing-directory non-resume without `--fail-if-exists` may wipe ledgers. These pre-existing behaviors warrant separate durability remediation.
5. One auxiliary side-channel append bypasses the artifact resource ceiling wrapper.

For one fresh acceptance: commit source/tests/review, use a new empty suffixed directory with `--fail-if-exists` and no `--resume`, avoid concurrent audit/pytest in this worktree, require empty auxiliary side channel, 10/10 fixtures, and no `error_isolated=true`. Before closure, independently approve and document abort-instead-of-merge semantics and resolve or waive findings 1–3. Preserve r2 and all prior outputs.

Reviewer identity: Claude Opus 5.5, independent of Cursor/Sonnet implementers. Review output delivered to PI in read-only session `80838`; this file is a PI transcription, not a verbatim log.
