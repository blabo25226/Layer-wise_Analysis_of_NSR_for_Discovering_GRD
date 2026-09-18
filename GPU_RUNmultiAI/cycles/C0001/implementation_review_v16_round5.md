# C0001-T020 independent implementation review — v16 round 5

## Verdict

**BLOCK.** Do not create `implementation_closure_record.json` and do not start
the full 27,637-call confirmatory audit.

The reviewed remote tip was
`947d539818eadfcaa43ab664fbc141fd93728afa`. The frozen v16 SHA256 remained
`67017f5c8bac861664fc867b70cf229d43be3d052d266ffd0d575e20e6c12078`.

Review independence:

- implementer: Cursor Agent
- independent reviewers: Claude Code and Codex executable-audit subagent
- PI: Codex
- `reviewer_diff_assertion: true`

Round 5 is retained as negative implementation evidence. Its 510-row execution
must not be reused by a later acceptance or scientific audit.

## Mechanically supported progress

- `pair_results.csv`: 510 rows, 510 unique `pair_id`, 510 unique components
- strata: 330 strict Hill, 60 non-strict Hill, 120 linear
- all 510 rows: `control_pass`; `unknown=0`
- `call_log.jsonl`: exactly 4,080 unique five-tuples, all `condition=B1`
- primitive multiset: P4/P5/P11/P6/P8/P9 each 510 and P7 1,020
- frozen plan unchanged; no closure record; no full audit
- protected tracked paths unchanged
- local/tracking/remote equality at the reviewed tip

These facts establish that the dedicated B1 population is executable. They do
not establish closure because the evidence packet is internally inconsistent.

## Blocking findings

### R5-1 — mixed source provenance

The acceptance began before the final runtime fixes and was finalized after
additional runtime commits. `source_inventory.json` matches `9b4b02e`, but
`audit.py` and `contract_evidence.py` differ from claimed final runtime
`24f1e04`. The committed manifest does not contain a trustworthy `commit`,
`resume_identity`, `source_hashes`, or clean-worktree provenance. A runtime
commit was created inside the manifest time window.

Acceptance must be generated from one already pushed candidate source commit in
a fresh output directory. No runtime source may change until that run is
complete and independently reviewed.

### R5-2 — persisted G_impl evidence is FAIL

`reachability_evidence.json` records
`REACH-IDENT-FALLBACK-1 passed=false`, `fallback_candidate=false`,
`e1_raw==e2_raw=false`, and outcome `preserved`. The manifest nevertheless
claims `G_impl=true`. Recomputing the gate from persisted evidence returns
false. The live d>=2 simplifier fixed-point path remains unreached.

### R5-3 — completed and aborted lifecycle states are mixed

The output contains `abort_manifest.json`; `deviation_log.md` ends with
`status=aborted`; the final manifest says completed while retaining abort fields.
The abort was caused by duplicate C_q4 stage-cache keys. A completed acceptance
tree may not retain unresolved aborted lifecycle state.

### R5-4 — resume/cache contract is bypassed

`stage_cache.jsonl` contains 5,624 rows but only 5,617 unique keys: all seven
C_q4 keys occur twice. Production loading correctly raises
`AuditInvariantError`, but implementation-acceptance resume sets
`stage_cache={}` and skips validation. Resume is inferred from file existence
instead of explicit `--resume` and does not verify the previous identity before
reuse. This violates frozen section 12.5.

### R5-5 — F7 is still circular and changes production semantics

The production B2 path computes the real classifier result and then replaces it
with `frozen_hill_form_literal()`. The purported independent expectation uses
the same literal helper/decision table. This is not independent, and the
literal detector disagrees with production classification on 330/510 persisted
expressions. The test mutates an input to the shared table rather than mutating
production against an independent reference.

### R5-6 — timing verdict uses an invalid projection

The implementation multiplies every one of the 27,637 calls by the slowest
sampled primitive mean. It therefore reports about 101,614 seconds. Applying
the same observed means to the frozen confirmatory primitive multiplicities and
a 15% margin gives about 9,622 seconds before D2/fixed overhead. A separate
reviewer estimate including D2 is about 10,887 seconds.

The reported timing BLOCK is mathematically invalid, but timing PASS is also not
yet established because registration/P2, representative B0, real CAS,
descriptive D2, fsync/resource scans, and fixed overhead were not all sampled.

### R5-7 — closure verification is incomplete

Closure verification checks only that an accepted-commit string exists and that
the current inventory equals the supplied list. It does not prove that the
commit exists, recompute its Git blobs, or verify plan/audit identity, artifact
digests, G/F verdicts, reviewer identity/verdict, or review digest. It also
prefers an output-directory closure record over the canonical repository record.

### R5-8 — schema/resource/guard claims remain incomplete

- acceptance schema validation uses `present_only=True` and does not validate
  manifest/lifecycle/cache consistency
- G_contract schema evidence still checks temporary samples rather than all
  produced rows
- acceptance registration/evidence loggers do not all carry the resource monitor
- child guard ordering still relies partly on source-string ordering
- clean-tree logic adds a completion-report exception beyond the authorized
  output directory and two protected paths

## PI timing decision

The frozen ceiling is unchanged. Round 6 must project time by summing each
frozen primitive multiplicity times a representative per-primitive estimate,
then adding all 2,640 D2 calls, setup/finalization/fsync/resource overhead, and a
positive declared margin. Slowest-call multiplication over all calls is
forbidden. Full authorization remains blocked until this calculation is
reproducible and at most 18,000 seconds.

## Round-6 acceptance conditions

1. One candidate source commit is committed, pushed, and held immutable for the
   entire fresh acceptance run.
2. Fresh output only; no reuse of round-5 rows, logs, or caches.
3. Exact 510 B1 rows and 4,080 unique calls are reproduced.
4. Manifest source inventory has zero mismatches against Git blobs of its bound
   commit and contains the required provenance/environment/resource fields.
5. Every JSONL cache loads with unique keys; explicit resume validates complete
   identity before reuse and never skips duplicate detection.
6. Completed output has no abort artifact or aborted deviation terminator.
7. All ten persisted reachability fixtures pass, including a real production
   d>=2 multi-component simplifier fixed point.
8. Production B2 uses the production classifier. An independent reference that
   shares no production classification helper detects a production mutation.
9. Every produced artifact row and lifecycle cross-condition is validated.
10. Closure validation uses only the canonical repository record and verifies
    commit existence, Git blobs, plan/audit identity, evidence/review digests,
    verdicts, and reviewer identity.
11. Multiplicity-weighted grand-call timing plus overhead and margin is at most
    18,000 seconds.
12. Tests, artifact report, commits, pushes, and local/tracking/remote equality
    are recorded; another independent review PASS is required.
