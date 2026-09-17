# C0001-T019 independent implementation review — v16 round 4

## Verdict

**BLOCK.** Do not create `implementation_closure_record.json` and do not start the
27,637-call confirmatory audit.

The reviewed branch was `ai/C0001/research-engineer/implement-metric-audit` at
`13a582d10a6783befe1ea23ac45d63d764194b21`. Local, tracking, and remote refs were
equal. The frozen preregistration SHA256 remained
`67017f5c8bac861664fc867b70cf229d43be3d052d266ffd0d575e20e6c12078`.

Implementer and reviewers were independent:

- implementer: Cursor Agent
- independent reviewers: Claude Code, Codex executable-audit subagent, Codex
  protocol-resolution subagent
- PI: Codex
- `reviewer_diff_assertion: true`

Round 4 is preserved as negative implementation evidence. Its honest
`F6=false` / `G_impl=false` result is correct for the two-row smoke population.

## Blocking findings

### R4-1 — no executable pre-closure population for F6

The frozen plan requires G_impl before the full audit and F6 requires 510/510
B1 rows. Smoke creates two B1 rows, while non-smoke and resume require a closure
record. Therefore the current implementation cannot reach F6 PASS before the
closure it is meant to authorize.

The faithful bridge is a distinct pre-closure implementation-acceptance
invocation over all 510 real B1 components. Its eight named primitives per row
are **counted** and must be durably recorded in a dedicated 4,080-call ledger.
Only the later conjunct evaluation of the existing rows adds zero calls. These
acceptance rows are non-scientific implementation evidence and must never be
reused by the fresh full audit.

### R4-2 — closure binding is self-referential

`require_accepted_closure_for_execution()` requires the closure payload commit
to equal current HEAD. Committing the tracked closure record changes HEAD, so a
canonical committed record cannot satisfy that equality. The record must bind
`accepted_source_commit` and its complete source inventory. A later
metadata-only closure commit may contain the record; full execution must verify
the accepted source hashes and evidence/review digests without requiring the
metadata commit to equal the accepted source commit.

### R4-3 — production resume rejects its own output tree

`verify_clean_worktree()` runs before resume and treats the incomplete untracked
output directory as a dirty-tree violation. Resume must ignore exactly the
selected output directory while keeping every other tracked and untracked path
strict, apart from the two already documented exceptions.

### R4-4 — pair-cache key violates the frozen duplicate rule

Round 4 stores the same immutable `pair_id` for B0 and B2 and relaxes the loader
key to `(condition, pair_id)`. Frozen section 12.5 requires duplicate `pair_id`
to abort. B2 must be recoverable without adding a second pair-cache row with the
same `pair_id`; the implementation must retain the frozen key contract and
prove zero primitive re-execution on resume.

### R4-5 — identity-fallback reachability remains synthetic

`REACH-IDENT-FALLBACK-1` hands the same string to E1 and E2 at dimension one.
It does not drive a real simplifier fixed point on a live multi-component
`,|,` prefix. The positive production branch must be executed and persisted for
dimension at least two, with E1 unequal to Q4(E1).

### R4-6 — resource boundaries and abort durability are incomplete

Initial/running manifests, deviation initialization, stage-cache appends,
guard-side-channel creation, and abort artifacts do not all pass through the
central resource boundary. Abort artifacts need a non-raising measurement path
so evidence can still be written after a ceiling breach. The final manifest
recorded `dir_bytes=677664`, while the completed directory measured 699236
bytes, because size was sampled before the final manifest write.

### R4-7 — acceptance evidence is not sufficiently durable or independent

- F1/F4 execute four scales but persist only scale names, not per-scale analytic
  and numeric outcomes.
- F7 reuses the same production classifier/outcome helper, so the purported
  independent oracle is tautological. It needs a separately implemented frozen
  decision table plus a mutation falsifier.
- guard import ordering is checked by source-line scanning, not an executable
  parent/child subprocess probe, and does not fully cover `experiment_runtime`.
- artifact schema validation checks only the first row of JSON artifacts and
  does not fully validate CSV/JSONL/cache rows.

### R4-8 — timing feasibility must be established before full authorization

The smoke manifest reports about 81.42 seconds for 65 logged calls. Naive linear
projection exceeds the frozen 18,000-second ceiling. This is not yet a reliable
full-runtime estimate because call types differ, but full execution is not
authorized until a representative calibration (including subprocess/oracle/CAS
costs) projects completion with margin under the frozen ceiling. Do not amend
the ceiling without a separately reviewed protocol decision.

### R4-9 — report/state provenance is stale

The completion report still says push was blocked/local-only, but PI later
pushed and verified local/tracking/remote equality at `13a582d...`. Persistent
state also still described round 3. Both must be corrected without rewriting
the historical runtime artifact.

## Verified PASS items

- local/tracking/remote branch parity at `13a582d...`
- plan hash and 89 source hashes match the validation runtime commit
  `acc1982b4212bbeb7e55ace0ded0a879bb06d0f1`
- symmetric `,|,` multi-component serialization is present on live d=3 rows
- F1/F4 execute all four primary scales in-process
- F6 does not false-pass the two-row smoke
- non-smoke and resume require a closure record
- primitive resource post-check runs in `finally`
- production B1 identity scaler evidence and D2 terminal vocabulary are present
- zero-byte guard side-channel exists
- terminal `unknown` count is zero
- targeted independent tests: 8 passed
- compileall and `git diff --check`: PASS
- no closure record and no full audit were created
- protected v9 smoke remained untouched

## Round-5 acceptance conditions

1. A dedicated pre-closure mode executes 510 real B1 rows, records exactly the
   expected 4,080 named primitive calls in its own durable ledger, and persists
   source inventory, complete F evidence, G_contract/G_impl, reachability,
   resource, deviation, and abort evidence.
2. F6 fails at 509 rows, any duplicate/missing row, `unknown`, or illegal
   terminal; it passes only for 510 legal B1 rows.
3. Closure verification uses an accepted source commit plus exact hashes and
   independently reviewed evidence digests, without HEAD self-reference.
4. Resume ignores only its selected output directory and demonstrably restores
   B0/B1/B2/D2 state with zero primitive re-execution.
5. Pair-cache duplicate `pair_id` remains an abort condition.
6. Live multi-component simplifier identity fallback reaches the production
   execution-failure path.
7. Every normal artifact write is bracketed; abort writes preserve evidence
   after a ceiling breach and record pre/post measurements.
8. F7 is independent and mutation-tested; every artifact row is schema checked.
9. Executable parent/child guard import-order falsifiers cover both
   `gpu_runmultiai` and `experiment_runtime`.
10. Bounded validation covers `component_idx>0`, a secondary Hill component,
    and a linear control. F1/F4 evidence persists per-scale results.
11. A representative timing calibration supports the frozen wall ceiling.
12. Runtime/tests are committed and pushed before validation; final artifact and
    report commits are pushed; local/tracking/remote equality is recorded.
