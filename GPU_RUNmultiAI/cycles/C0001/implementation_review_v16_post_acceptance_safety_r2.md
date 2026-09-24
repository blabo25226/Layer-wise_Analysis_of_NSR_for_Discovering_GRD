# Independent review of C0001-T024 second safety revision

Reviewer: Claude Opus 5.5 (read-only), independent of Cursor Agent implementer. Reviewed source `456d8becaa274a89ef3c770cd2aac9f4693fe38c`. Verdict: **PASS with conditions for one fresh 4,080-call acceptance only; no implementation closure or full-audit authorization**. The reviewer read final source, tests, frozen v16 §§3.8/10–12, and r2 evidence. Shell, git diff, SHA recomputation, and test execution were unavailable to the reviewer. PI verified frozen plan SHA, four-to-seven-file source change scope, branch and remote SHA; Cursor's committed-tree conda focused suite reported **124 passed**.

## Closed by this revision

- Entrypoint injected REACH-SFN-1 failure test asserts zero counted calls, no registration, and an abort manifest.
- Acceptance/full preflight occurs before counted primitives; exact ten fixture IDs remain enforced.
- Real live-probe-body tests use a fake `run_b0_pair` and check the auxiliary logger has no durable path while counted `call_log` and `stage_cache` bytes remain unchanged.
- Child attempts on ordinary probe returns are written to an auxiliary side-channel; deviation text now describes additional uncounted work and the frozen §3.8-before-§10 ordering.

## Open evidence-integrity findings

1. **P2 auxiliary attempts can still be lost.** The match-path extra `simplify_tree_subprocess` discards its `guard_attempts`. If the probe raises after collecting child attempts, only normal return paths flush the guard into the auxiliary sink. `GateAbortError` for a missing sink is caught by the outer `except Exception`, so the fixture can still PASS on its synthetic part. The acceptance entrypoint must not silently certify a probe with unrecorded attempts.
2. **P2 auxiliary channel is not gated.** Child rows are excluded from G4 and are not checked elsewhere; frozen §11 says child attempts merge into the parent bootstrap handle. Either fail closed on any auxiliary denied row or explicitly document and independently approve a non-equivalent interpretation before closure. Add entrypoint tests for match/exception and side-channel content.
3. **P3 destructive resume provenance.** `clear_stale_abort_manifest()` runs before resume identity/closure verification. An invalid resume can delete an earlier abort record and replace it. Preserve prior abort evidence, validate identity first, and avoid overwriting or deleting abort files without a recoverable record. A full `--resume` without `call_log.jsonl` also silently takes a fresh path (pre-existing issue).

Before final-source acceptance, PI requires a bounded remediation of findings 1–3, followed by focused tests, independent re-review, and one acceptance run in a new empty directory. Prior r2 output is immutable and bound to source `6e20b25`. No scientific decision follows from this review.
