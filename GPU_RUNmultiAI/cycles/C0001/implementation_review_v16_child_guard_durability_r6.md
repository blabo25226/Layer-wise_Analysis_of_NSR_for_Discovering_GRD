# C0001-T025 independent source review r6

Reviewer: Claude Opus 5.5, read-only session `52328`, independent of Cursor implementer. Source: committed `c2067c252168d19e7d8946a6ae4e8e2a40915e3c`. Frozen v16 §11/§12 and prior r5 review inspected. Reviewer did not run shell/tests or compute hashes. No scientific-result claim.

## Verdict

`REVISE_BEFORE_ACCEPTANCE`. The prior r5 MAJOR timeout/no-receipt and first/live/counted simplifier propagation findings are closed in source. One new MAJOR finding remains on Python 3.10.

## Blocking finding

`audit.py` and `reachability.py` call `Path.is_file()` **outside** their guarded `stat()` try/except. In the `lansr310` Python 3.10 `pathlib.Path.is_file()` re-raises non-ignorable `OSError` (including a mocked `OSError` without errno). Thus the intended `GateAbortError` conversion is bypassed; in live-probe wrappers a raw `OSError` can become `error_isolated=true` and the auxiliary sink may never see collected attempts. PI independently inspected the conda Python 3.10 `Path.is_file()` source and confirmed this control flow. Fix with one guarded `stat()` operation; treat only `FileNotFoundError` as absent and every other `OSError` as `GateAbortError`. Apply in both helpers and consider the child side-channel loader.

The PI stopped the c2067c2 conda full focused suite after `23 passed in 301.63s` because this source will be revised; that run is **not PASS**.

## Closure-only residuals

- Other `OSError` during counted side-channel read/unlink can become an ordinary execution failure. Handle incomplete guard accounting fail-closed before closure.
- Preexisting child rows merged into later calls can mask later uncertainty and misattribute rows; any denied row still prevents G4 PASS.
- Content-key dedupe undercounts repeated identical denials.
- Resume can lose child-denial evidence; no resume-based acceptance/full audit until fixed or explicitly gated.
- Test gaps include a direct first-call fixture and real-worker kill path; handoff should state observed test results.

## PI gate

No fresh acceptance until the blocking Python 3.10 path is repaired, targeted tests and full focused suite PASS on one committed source, and an independent follow-up review passes. Preserve frozen plan and historical runs.

This is a PI transcription of the reviewer message, not a verbatim log.
