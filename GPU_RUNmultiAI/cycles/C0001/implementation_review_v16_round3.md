# C0001 v16 implementation independent review — round 3

- reviewed tip: `ebafe5cb7adb8780f303950a2a081b36169edc6c`
- runtime commit recorded by validation: `1bd083def321f99b6e99c4fc558beb197f6626ec`
- frozen plan SHA256: `67017f5c8bac861664fc867b70cf229d43be3d052d266ffd0d575e20e6c12078`
- reviewers: Claude hostile implementation review, Codex independent executable subagent, Research PI
- PI commands: plan hash PASS; Python 3.10 compileall PASS; `git diff --check` PASS; 89 manifest/inventory hashes equal the runtime commit Git blobs; local/tracking/remote equal `ebafe5c`
- worker test report: focused pytest **96 passed in 542.11 s**
- decision: **BLOCK**
- closure/full audit: **DENIED**

Round 3 genuinely repairs the production B1 path, B2 and D2 vocabularies,
B3 linkage, most resume/provenance fields, and the stale validation provenance.
Those partial passes remain useful implementation evidence, but the following
load-bearing defects prohibit implementation closure.

## P0 blockers

1. **Multi-component identity-fallback detection is unreachable.**
   Parent E1 is serialized by `"|".join(tree_to_prefix_list(...))`, producing
   `a,b|c,d`.  The simplifier child returns raw ODEFormer `NodeList.prefix()`,
   whose separator is `,|,`, producing `a,b,|,c,d`.  The byte comparison can
   therefore never detect an unchanged result for systems with two or more
   components.  The round-3 smoke used only two one-dimensional components,
   and `REACH-IDENT-FALLBACK-1` manually supplies equal strings rather than
   exercising the production comparison.  This can incorrectly turn a silent
   simplifier fallback into a fully diagnostic row and bias the asymmetric
   primary decision toward `H0001 unsupported`.

2. **`G_impl=true` is not supported by the frozen F acceptance population.**
   F1 and F4 require all primary scales, but persisted evidence contains only
   two rows at scale `0.1`.  F4 verifies source-code strings naming a test and
   assertions instead of executing the acceptance.  F6 requires 510/510 B1
   rows but passes with two smoke rows.  `gate_g_impl` trusts caller-provided
   booleans after only cardinality/check-key checks.  A reduced smoke may not
   claim full F1/F4/F6 acceptance without separate executable, persisted
   evidence covering the frozen criterion.

3. **A full audit is not gated on an accepted closure record.**
   `verify_accepted_closure_source_hashes()` returns
   `closure_record_absent`; non-smoke execution continues.  Frozen §13.2
   requires full audit and resume to match the accepted commit/hash set.

4. **Resource checks still do not bracket every frozen boundary.**
   The two fingerprint files share one before/after group.  Pair CSV,
   equivalence oracle, guard side channel, deviation finalization, and the
   final manifest are not each checked immediately before and after their
   write.  The manifest records directory bytes before writing itself.  A
   primitive exception also skips the post-execution check rather than using a
   `finally` boundary.

5. **The global-abort lifecycle is incomplete.**
   Only a fixed exception tuple reaches `_handle_global_abort`.
   `AuditInvariantError` from call ceilings/JSONL/cache invariants,
   plan/corpus runtime errors, `ODEFormerUnavailable`, and unexpected global
   exceptions can escape with no abort manifest or finalized deviation log.
   Tests route only a subset of the listed families through `run_audit`.

## P1 blockers

6. **The required zero-attempt guard side-channel artifact is absent.**
   `append_guard_attempts()` creates a file only when a row exists, so the
   round-3 directory has no `guard_attempts_side_channel.jsonl`.  Zero attempts
   cannot be distinguished from a writer that never ran.  The schema probe
   writes sample rows in a temporary directory and skips a missing JSONL in
   the real smoke.

7. **Durable pair cache is incomplete.**
   The artifact has only the two B0 and two B1 rows.  The executed D2 row is
   placed in the in-memory cache but never appended to `pair_cache.jsonl`, so
   resume cannot recover that completed pair.  B2 derivation/recovery must
   also be made explicit without violating its immutable B0 `pair_id` and the
   duplicate-key rule.

8. **`G_contract` guard evidence omits import ordering.**
   The runtime entry order appears correct, but the executable guard check
   does not prove that parent and child install the stdlib-only guard before
   importing package/runtime modules, despite §10.1/§11 requiring it.

9. **Reachability and acceptance evidence retain circular shortcuts.**
   UNS/SUP exclude `G_contract` and `G_impl` although §3.8 says all gates pass;
   the exclusion is not a deviation.  F7 recomputes the outcome with the same
   private classifier that produced it.  The production E1/E2 comparison is
   not used by the identity-fallback fixture.

## Additional hardening required before PASS

- Require and record a clean worktree before validation/full execution.
- Include at least one live multi-component, preferably dimension-three,
  end-to-end row in the next bounded validation.
- Validate actual produced artifact payloads, including JSONL presence, not
  only schema sample rows.
- Keep round-2 and round-3 directories quarantined as negative implementation
  evidence; neither is scientific evidence.

## Verified round-3 partial passes

- Frozen plan hash is unchanged.
- Runtime commit precedes the artifact commit; the round-3 artifact is absent
  from the runtime commit.
- Manifest commit equals `1bd083d`; all 89 source hashes reproduce from that
  commit; local/tracking/remote equal `ebafe5c`.
- B1 uses production `Scaler.rescale_function` with identity parameters and
  both live early-return unit fixtures pass.
- B2 has no E2 leakage or `unknown`; D2 uses descriptive vocabulary.
- B3 executes CAS and yields 2/2 `diagnostic_complete` linked to B0 fields.
- N1 component IDs, exact call totals, timeouts, decimal byte ceiling, and the
  core JSONL durability helpers are present.
- No closure record or full audit was created.  The protected untracked v9
  smoke remains untouched.

## Acceptance rule

Repair every blocker above, add falsifying tests, commit and push runtime/tests
before validation, and generate a new bounded validation from that clean
runtime commit.  The new completion report must be artifact-derived.  A fresh
Claude and executable independent review must PASS before the PI may create a
closure record or authorize the 27,637-call full audit.
