# C0001-T022 independent implementation review — v16 round 6

## Verdict

**BLOCK.** Do not create `implementation_closure_record.json` and do not start
the full 27,637-call confirmatory audit.

The authoritative acceptance packet is
`runs/c0001_metric_identifiability_audit_v16_round6_acceptance_r4/`, bound to
source commit `9aa9ad76d277c485bedd1cc8f60c655e6c0ed97f`. The reviewed branch tip is
`cbdd909cc714b023925a7eff37f4276954aeef3b`; local, tracking, and remote refs
were equal at review time. Frozen v16 remains unchanged at SHA256
`67017f5c8bac861664fc867b70cf229d43be3d052d266ffd0d575e20e6c12078`.

Review independence:

- implementer: Cursor Agent
- independent executable reviewer: Codex subagent
- methodological reviewer: Claude Code invocation (separate read-only worker)
- PI and conflict resolution: Codex
- `reviewer_diff_assertion: true`

Round 6 is retained as negative implementation evidence and must not be reused
by round 7 or by the scientific audit.

## Mechanically supported progress

- B1 evidence has exactly 510 rows, 510 unique pairs, and 510 unique components.
- Eligibility counts are 330 strict Hill, 60 non-strict Hill, and 120 linear.
- All 510 B1 terminals are `control_pass`; `unknown=0`.
- The dedicated ledger contains exactly 4,080 unique completed B1 calls with
  the frozen primitive multiset: P4/P5/P11/P6/P8/P9 each 510 and P7 1,020.
- `stage_cache.jsonl` has 5,617 unique keys, no duplicates, and loads through
  the production loader.
- The 91-entry manifest and artifact source inventories agree with the Git
  blobs at `9aa9ad7` with zero hash mismatch.
- The r4 tree has no abort manifest; its deviation log terminates as completed.
- No closure record or full audit was created.

These are real improvements over round 5, but they do not establish G_impl or
implementation closure.

## Blocking findings

### R6-1 — REACH-IDENT-FALLBACK-1 is fabricated

`src/gpu_runmultiai/reachability.py:398-404` defines
`production_simplifier_ran` as production E2 being *different* from E1, then
replaces the stored E2 with E1 precisely in that case. The synthetic stored
pair is passed to the detector at lines 405-420, and lines 429-433 count the
combination of a changed production E2 and the fabricated stored equality as a
PASS.

The artifact exposes the contradiction verbatim:

```text
production_e1_raw==e2_raw=False
stored_e1_raw==e2_raw=True
simplifier_subprocess_identity=False
```

This is not a live production simplifier fixed point. Therefore persisted
10/10 reachability and `G_impl=true` are false. A valid fixture must feed an
actual d>=2 multi-component E1 through the production simplifier and preserve
its real E2 unmodified, with E2 raw byte-identical to E1 raw and E1 not
Q4-equivalent.

### R6-2 — full-run closure authorization bypasses the canonical verifier

The full path calls `require_accepted_closure_for_execution()` at
`src/gpu_runmultiai/audit.py:1132-1136`. That function does not use its `commit`
argument and verifies neither commit existence nor Git blobs, plan/audit
identity, PASS verdict values, acceptance/review digests, or reviewer identity.
The stronger `verify_canonical_closure_record()` is called only by the
pre-closure acceptance path.

Even the stronger verifier makes `plan_hash` and `audit_id` optional, treats
arbitrary non-empty verdict strings as accepted, and does not recompute the
review digest. Full and resume execution must call one fail-closed canonical
validator and verify exact expected values and file digests before any counted
primitive.

The focused test
`test_closure_binds_accepted_source_commit_not_metadata` also fails on the
reviewed source because its old output-directory closure assumption no longer
matches the canonical-only implementation. The test and contract must be
reconciled rather than omitted from the acceptance test selection.

### R6-3 — F7 production/reference logic is circular

`src/gpu_runmultiai/outcomes.py:162-178` implements the production B2 outcome by
importing and calling
`f7_independent_reference.classify_b2_outcome_frozen`. Production and reference
therefore share the same decision table. Mutating that table changes both sides
and cannot be caught by the claimed independent oracle.

Production B2 may use the production `classify_formula(E1)` result, but its
five-outcome decision must live in production code. The independent reference
must duplicate the frozen specification without importing production
classifier, production outcome, or production pipeline helpers. Mutation tests
must independently mutate both production classifier output and production
decision precedence and show that the reference rejects each mutation.

### R6-4 — timing projection is not the frozen exact multiplicity calculation

The confirmatory projection uses the frozen aggregate primitive table, but
P1/P2/P12 are not directly measured and receive a blanket whole-calibration
fallback. D2 is calculated as `2640 * mean(7 primitive types)` even though the
frozen path is `330 * 8 calls` and includes two oracle calls per pair. The
review recomputation from the stored means gives 1,193.79 s for exact D2
multiplicities, versus the persisted 1,350.31 s; the persisted formula is not
the registered calculation even though it happens to be conservative here.

Append+fsync, resource scans, startup, and finalization are not measured, while
45 seconds is asserted as fixed overhead without evidence. The reported
12,949-second PASS is therefore not a reproducible feasibility gate.

### R6-5 — final lifecycle/resource state is not fully validated

Several reachability, F-acceptance smoke, and timing `CallLogger()` instances do
not carry the shared resource monitor. Acceptance schema validation occurs
before deviation finalization and before the completed manifest is written, so
the final cross-artifact lifecycle cannot be the state that was validated.

The next acceptance must route all primitive and artifact writes through the
resource boundary, finalize lifecycle artifacts first, then validate the final
tree and write a manifest whose post-finalization byte measurement is defined
and checked.

## PI decision

Round 6 closes provenance, B1 population, duplicate-cache, and abort-residue
failures from round 5. It does not close reachability, F7 independence, closure
authorization, timing, or final lifecycle/resource enforcement. These are
implementation defects, not a hard stop. Proceed to a fresh round-7 repair and
acceptance attempt under the unchanged v16 preregistration.
