# C0001 v16 implementation independent review — round 2

- reviewed tip: `74a19c2a9562d1f68c6cfbf4acff6304ba72a9c1`
- frozen plan SHA256: `67017f5c8bac861664fc867b70cf229d43be3d052d266ffd0d575e20e6c12078`
- reviewers: Claude hostile implementation review, Luna independent executable audit, Research PI
- independent commands: Python 3.10 compileall PASS; focused pytest **68 passed in 485.94 s**; `git diff --check` PASS
- Git: local, tracking, and remote matched `74a19c2`
- decision: **BLOCK**
- closure/full audit: **DENIED**

Round 2 closes several round-1 defects: P12 and the 46/284 stratum gate,
eligibility counts, frozen resource values, parent entry bootstrap ordering,
the 10 reachability identifiers, B1 gate cardinality, durable core JSONL,
Q4 fixtures/dialect, and the second rescale early-return detector.  These
partial passes do not authorize the full audit because the following
load-bearing contracts remain open.

## P0 blockers

1. **The validation manifest cannot reproduce its declared execution.**
   `audit_manifest.json` records commit `917402c`, but runtime changes are in
   `fa955a2` and `45eef68`; its 88 source hashes match the latter working
   content, not `917402c`.  The runtime must be committed first and the fresh
   validation must then record that clean commit.  The completion report also
   says 45 calls and 82 paths, while the artifact records 57 confirmatory
   calls, 8 descriptive calls, and 88 paths.

2. **`G_contract` and `G_impl` are asserted, not demonstrated.**
   Four contract rows and all F1/F2/F4–F8 acceptance values are literal
   `True` in `audit.py`.  The guard row is only `hasattr(guard, "to_log")`.
   Several reachability rows set their desired failure flag directly, and
   UNS/SUP bypass real gate evaluation.  Such circular evidence cannot gate
   a confirmatory run.

3. **F5 is still violated.**
   Round 2 replaces the wrong production scaler with a custom
   `IdentityScaler.rescale_function` that rebuilds/returns the input instead
   of executing the frozen production rescale algorithm with
   `a_t=1`, `b_t=0`, `scale=1`.  The test checks parameters, not the production
   path.  Identity bypass is explicitly forbidden.

4. **B2 and D2 terminal vocabularies are wrong.**
   Both B2 validation rows are primary-scope `unknown`, which v16 prohibits;
   a full run would silently produce 1,320 such rows without a gate seeing
   them.  D2 is emitted as `preserved` rather than
   `descriptive_recorded`/`descriptive_failed`.

5. **B3 is structurally unable to complete.**
   Both B3 rows are `diagnostic_failed` although CAS completed and was valid,
   because the payload never receives classifier/metrics fields from the
   originating B0 row.  `cas_compare_completed` is inferred from key
   presence rather than the executed CAS result.

6. **Global abort and lifecycle contracts remain incomplete.**
   Only `Q4ContractError` writes abort evidence.  Other corpus, eligibility,
   stratum, resource, resume, JSONL, and ceiling failures escape.  The first
   manifest status remains forbidden `in_progress`; abort fields omit
   `abort_utc`, `output_dir_bytes`, and durable last keys; the deviation entry
   schema is not the frozen six-field format and is not initialized at run
   start.

7. **Resume remains checkout-dependent and insufficiently bound.**
   Absolute fingerprint paths are part of semantic identity.  Required
   files may be absent without abort, and the payload is reparsed and
   reserialized instead of enforcing the frozen byte/dict comparisons and
   accepted closure source hashes.

8. **Artifact schemas and durability remain incomplete.**
   Examples: registration truth lacks `component_flags`; rewrites keep
   precheck fields nested; condition summary lacks confirmatory/descriptive
   calls and primary counts; required provenance fields are only nested or
   missing at manifest top level; the guard side channel lacks unconditional
   flush/fsync and durable malformed/duplicate handling; N1 component IDs are
   null.

9. **Resource checks occur at the wrong boundaries.**
   The correct 18,000 s and 1,200,000,000-byte values are present, but checks
   do not wrap every primitive and every artifact write as frozen in §8.5.

10. **Exact fallback/dialect invariants remain open.**
    Oracle parsing still accepts non-frozen `neg`; the identity-fallback
    comparison uses an incomplete local dictionary/unfrozen timeout; an
    unmapped stratum can still fall through to `linear_control`.

11. **Tests are weaker than the contract at the open boundaries.**
    They do not trigger either real early-return case, do not prove production
    B1 rescale, cover only a small subset of artifact schemas/abort fields,
    and write a guard fixture under the real `results/runs` tree.

## Round-2 artifact disposition

The round-2 directory is retained as negative implementation evidence.  It
does exercise B0, B1, B2, C_q4, N1, B3, B4, and D2, but its stale commit,
invalid B2/D2 terminals, dead B3 rows, and circular gates make it inadmissible
for closure.

The 82-path list in the plan is an observed pre-implementation snapshot;
the frozen recursive inventory algorithm is normative.  The six added Python
modules make 88 paths legitimate, but the 82→88 reconciliation must be
recorded and the accepted 88 hashes pinned only after a PASS review.

## Acceptance rule

Repair all items above, add contract-first tests, commit runtime before
executing validation, regenerate artifacts from a clean committed tip, report
only values read from those artifacts, pass independent review, push every
stable commit, and verify remote parity.  Only then may the PI create the
closure record or authorize the full audit.
