# C0001-T018 — v16 implementation repair after round-2 BLOCK

## Binding inputs

- frozen plan SHA256: `67017f5c8bac861664fc867b70cf229d43be3d052d266ffd0d575e20e6c12078`
- review: `implementation_review_v16_round2.md`
- protected untracked path: `GPU_RUNmultiAI/cycles/C0001/runs/c0001_metric_identifiability_audit_v9_smoke/`
- full audit: prohibited
- closure record: prohibited until independent PASS

## Required repairs

1. Execute B1 through the frozen production rescale algorithm with identity
   parameters.  Remove the identity bypass and prove the actual production
   function was called while E1 remains oracle-equivalent to truth.
2. Replace every literal contract/F-acceptance `True` with executable,
   persisted evidence.  Make all ten reachability fixtures causal; run
   UNS/SUP through real gate evaluation.
3. Implement legal B2 five-outcome classification from E1-only fields and
   the frozen D2 descriptive terminal mapping.  Add whole-artifact invariants
   forbidding illegal/unknown terminals.
4. Populate B3 from the selected B0 row and actual CAS result so successful
   diagnostics can terminate `diagnostic_complete`.
5. Remove the replacement guard fallback.  `run_audit` must require the
   installed singleton handle; tests must use an isolated temporary root and
   verify parent/child durable ledger ownership.
6. Route every global abort through legal `initializing` → `running` →
   `aborted` lifecycle, complete frozen abort fields/last durable keys, and
   non-erasing six-field deviation entries.  Use `completed` only after all
   gates/artifacts finish.
7. Make resume identity checkout-independent and require byte-identical
   fingerprint files, verbatim payload dict, dependency versions including
   scikit-learn/numexpr, and accepted closure source hashes for full/resume.
8. Implement every §12.8 artifact schema and durable guard side channel;
   condition summary and manifest must expose all required top-level fields.
9. Check resource ceilings before/after every counted primitive and every
   artifact write; route violations through the global-abort lifecycle.
10. Restore the exact frozen oracle/fallback dictionary, timeout, and
    operator set; abort on unmapped strata.
11. Replace weak tests with contract-first negative and positive tests,
    including both actual rescale early returns, production B1 call proof,
    all schemas, every abort family, cross-worktree resume identity, and
    guard tests outside `results/runs`.

## Mandatory execution order

1. Implement and pass Python 3.10 compileall/focused tests.
2. Commit and push the runtime/test repair; verify local/tracking/remote.
3. From that clean committed tip, create a **new** bounded round-3 validation
   directory exercising B0/B1/B2/C_q4/N1/B3/B4/D2.
4. Verify its manifest `commit` equals the runtime commit and all source
   hashes recompute exactly; verify B1 passes, B2 has no unknown, D2 uses the
   descriptive vocabulary, B3 can complete, and all evidence is non-circular.
5. Generate the completion report from artifact values (no hand-copied call
   or inventory counts), commit/push artifacts/report, and verify parity.

Do not edit historical preregistration files, touch the protected v9 smoke,
create `implementation_closure_record.json`, or run the full audit.
