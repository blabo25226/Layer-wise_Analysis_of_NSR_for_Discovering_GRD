# Independent C0001 post-acceptance source review

Reviewer: Claude Opus 5.5, read-only, independent of Cursor Agent implementer. Source: `f9933b223606deab88b7ec675b64eb349acb7815`; base: `ba8ccfc612c29077214d30a0e4a451bbfd3642ed`. Verdict: **PASS to a fresh 4,080-call implementation acceptance only**. This does not authorize implementation closure or the 27,637-call full audit.

The reviewer read final source, frozen v16 §§3.8/10, tests, and r2 evidence. No shell, tests, hash recomputation, or experiment execution were available to the reviewer. PI separately checked four-file diff, frozen plan SHA256, branch/remote SHA, and clean tracked source. Cursor reported 107 passed and 14 skipped under system Python; the conda full focused suite remains required before closure.

## Closed full-audit blocker

- `build_reachability_evidence()` is now called before counted primitives in acceptance and full paths (`audit.py` near the `running` manifest), and the same evidence feeds the later gate.
- Individual fixture exceptions become fail-closed rows rather than crashing after counted work. The preflight refuses non-smoke counted work when any of the exact ten §3.8 fixtures fails.
- The exact fixture-ID set is checked, not merely a count of ten; synthetic UNS/SUP gate states use labelled fixture rows, avoiding a circular gate.

## Remaining findings before final-source acceptance

- **P2-A, auxiliary guard transparency:** live-probe child attempts are only counted in a detail string and are not side-channel records or G4 attempts. The new `auxiliary_guard_direct_attempts` label overlaps child attempts because the guard's `attempts` list includes children. For the final run, either fail closed on any child attempt or persist those attempts to an auxiliary side channel; do not silently drop them.
- **P2-B, ledger-isolation tests:** current tests stub the live probe rather than running its body with a fake `run_b0_pair`; they do not prove the probe logger is separate from the counted logger.
- **P2-C, preflight placement test:** helper-only tests do not prove an injected fixture failure leaves `call_log.jsonl` empty and an abort manifest with zero counted calls at the public acceptance/full entry point.
- **P3:** Record that v16 §3.8 requires G_impl before full execution, so a preflight failure aborts before the count instead of producing an undecidable completed run under §10. Expand acceptance deviation wording to cover trial-internal rewrite/Q4/simplifier calls, G0, and G_contract probes. Preserve evidence-type accuracy for failed fixtures if straightforward. The full resume path's old `abort_manifest.json` handling deserves a separate check before full audit.

The reviewer recommends closing inexpensive P2-A/B/C findings before rerunning acceptance, because the final source hashes will change. Acceptance r2 is bound to source `6e20b25` and cannot close implementation at a later source. No scientific hypothesis decision follows from this review.
