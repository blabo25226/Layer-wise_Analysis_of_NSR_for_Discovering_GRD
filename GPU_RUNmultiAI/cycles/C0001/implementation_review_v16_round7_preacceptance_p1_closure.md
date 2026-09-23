# C0001-T023 independent pre-acceptance P1 closure

Reviewer: Claude Opus 5.5, read-only, independent of Cursor implementer. Source reviewed: `663a56d467636761a2030aa381a12fb2af4313c2`. Verdict: **PASS to run one fresh pre-closure 510 B1 / 4,080-call acceptance packet, conditional on a full focused-suite PASS at this source.** This does **not** authorize the 27,637-call full audit.

## Closed P1 findings

1. `src/gpu_runmultiai/reachability.py` now computes real E1 and E2 oracle outcomes. The synthetic E2 remains explicitly labelled synthetic. PASS requires E1≢Q4(E1), E2 oracle completed and non-equivalent, production fallback detection, `execution_failure` with fallback, and `semantic_drift` for the same row with only the fallback flag cleared. This tests the frozen precedence rather than asserting the desired result.
2. The capped live-production observation is enabled only in the pre-closure acceptance path. The full counted audit uses the default that excludes it. Its logger has no counted ledger path, errors are contained without changing the synthetic fixture's `passed` value, and the acceptance timing monitor sees elapsed time. The full-run projected cost therefore does not include an unrequested live probe.

## Unresolved P2 before full-audit authorization

- The live probe does not currently forward child sealed-path guard attempts into the audit access-attempt count.
- The ledger-isolation test does not pass the audit logger into the probe; add an acceptance-level before/after check for call and cache files.
- Full audit still runs synthetic reachability checks after counted work; exceptions there should not be able to abort a completed run. Resolve before full audit, even though it does not block pre-closure acceptance.
- Improve second-simplifier-rerun and bounded-eight labels.

Review was based on primary source and frozen v16; no tests or audit were run by the reviewer. PI independently ran the targeted reachability subset: 7 passed, 111 deselected in 30.62 s. A prior full focused run was intentionally interrupted at 23 passed after Claude identified the P1 source blockers; it is **not** a full-suite PASS.
