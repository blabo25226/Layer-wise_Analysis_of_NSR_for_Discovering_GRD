# C0001-T019 — v16 implementation repair after round-3 BLOCK

## Binding inputs

- frozen plan SHA256: `67017f5c8bac861664fc867b70cf229d43be3d052d266ffd0d575e20e6c12078`
- review: `implementation_review_v16_round3.md`
- runtime under review: `1bd083def321f99b6e99c4fc558beb197f6626ec`
- reviewed tip: `ebafe5cb7adb8780f303950a2a081b36169edc6c`
- protected untracked path: `GPU_RUNmultiAI/cycles/C0001/runs/c0001_metric_identifiability_audit_v9_smoke/`
- round-2/round-3 validation directories: retained negative implementation evidence; do not edit or reuse
- full audit and closure record: prohibited until independent PASS

## Required repairs

1. Normalize both sides of the production identity-fallback comparison to the
   same frozen comma-separated component-prefix dialect.  Add a live
   multi-component fixture that makes the real simplifier return/represent its
   input and proves the detector fires; do not hand-set equal strings.
2. Make F1/F4 evidence execute and persist all four primary scales.  Replace
   source-text grep with executed assertions.  Make F6 evidence satisfy its
   510/510 criterion or represent a distinct pre-full executable acceptance
   population that faithfully proves that criterion; a two-row smoke must not
   produce a false `G_impl=true`.
3. Refuse non-smoke and all resume execution unless a valid accepted
   `implementation_closure_record.json` pins the current commit and complete
   source hash set.  Pre-closure bounded validation remains allowed.
4. Centralize artifact writes so every JSON, CSV, binary, JSONL append,
   deviation write, guard side-channel write, and manifest replacement is
   checked immediately before and after.  Put primitive post-checks in a
   `finally` path.  Ensure final recorded directory bytes include final
   artifacts without making completion self-inconsistent.
5. Route every global execution failure after output selection through
   `initializing`/`running` → `aborted`, including base invariant errors,
   runtime absence, resume/cache/JSONL failures, ceiling failures, and
   unexpected exceptions.  Preserve non-zero exit and do not swallow bugs.
6. Create the guard side-channel artifact unconditionally, including the
   zero-attempt case, with frozen durability and resource checks.  Add an
   executable parent/child import-order check before declaring the guard row
   PASS.
7. Persist completed D2 pair rows to durable pair cache and prove resume does
   not re-execute them.  Specify/test how derived B2 recovery works while its
   immutable B0 `pair_id` and duplicate-key invariant remain intact.
8. Replace tautological F7 evidence with an independent expected-outcome
   computation or fixture oracle.  Run identity-fallback reachability through
   the production E1/E2 comparison.  Either make UNS/SUP satisfy every frozen
   gate or record and resolve the protocol deviation; do not silently exclude
   gates while claiming §3.8 PASS.
9. Require a clean tracked worktree for validation/full execution and record
   the clean-state provenance.  Ignore but never stage or delete the protected
   historical v9 smoke.
10. Validate actual produced artifact schemas/presence, not only temporary
    sample rows.  Include tests that fail on a missing empty JSONL artifact,
    missing resource boundary, incomplete abort family, absent closure on a
    full/resume attempt, missing scale, and multi-component prefix mismatch.

## Mandatory execution order

1. Implement and pass Python 3.10 compileall, focused contract tests, plan
   hash, and `git diff --check`.
2. Commit and push runtime/tests first; verify local/tracking/remote equality.
3. From that clean runtime commit, generate a **new round-4** bounded
   validation.  It must exercise B0/B1/B2/C_q4/N1/B3/B4/D2 and at least one
   live multi-component dimension-three system.
4. Verify manifest commit/source hashes against Git blobs, executable F
   evidence, zero-attempt guard artifact, D2 resume cache, abort/resource
   traces, terminal vocabularies, and non-circular reachability.
5. Generate the round-4 completion report only from artifact values, then
   commit/push artifacts/report and verify remote parity.

Do not edit the frozen preregistration or historical validation directories,
touch the protected v9 smoke, create a closure record, or run the full audit.
