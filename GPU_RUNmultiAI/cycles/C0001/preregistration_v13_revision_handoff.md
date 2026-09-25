# C0001-T012 v13 revision handoff

## Objective

Create a self-contained `preregistration_draft_v13.md` and close R12-1 through
R12-5 from `preregistration_v12_independent_review.md`. Preserve v9-v12 bytes.

## Isolation and scope

- worker: Cursor repo-operator / scientific document implementer
- worktree: `/tmp/lansr-multiai-C0001-implement-audit`
- branch: `ai/C0001/research-engineer/implement-metric-audit`
- write: v13 plan, v12 review response, v13 completion, durable state
- prohibited: v9-v12 edits, scientific code/tests, smoke/full experiment,
  freeze claim, GPU_RUN5 results, untracked v9 smoke directory

## Required changes

1. Add exact Rational Q4-R4a as counted `q4_fixture_07`; require all 7 in
   G_q4ref and the Q4 artifact. Recalculate every table and gate to confirmatory
   **27,637**, D2 **2,640**, grand **30,277**.
2. Inline the exact production n-ary SymPy fold and child order. Add a 3-child
   Add/Mul parity fixture. Keep production Q4 arity faithful to `generators.py`.
3. Define a separate audit-oracle extended arity table with unary `pow4` for F2.
   Do not claim `pow4` is a production Q4 operator. Abort on unreparseable Q4
   emitted operators.
4. Inline exact truth-side zero-based component index sets for strict,
   non-strict, and linear eligibility, plus exclusive/exhaustive abort checks.
5. Restore the full pointwise oracle finite/tolerance contract.
6. Restore the full sealed matcher and require guard installation before task
   code in parent and all children. Name the side-channel artifact and merge it
   before G4; deny attempts must block and log.
7. Enumerate complete artifact schemas, including raw/emitted E0/E1/E2 fields,
   analytic/numeric oracle fields, failure reasons, secondary metrics, exact
   fingerprint payload/bytes, durable caches, call log, guard side channel,
   abort manifest, and deviation log.
8. Freeze append+flush/fsync boundary and trailing-partial-line recovery for
   resumable JSONL. Name `stage_cache.jsonl` and `pair_cache.jsonl` if the runtime
   uses both; otherwise explicitly forbid the unused cache.
9. Restore full resume identity: commit, all hashes, corpus/fingerprint bytes,
   seeds, ordered primitives, timeouts, semantic CLI, dependencies, OS/CPU, and
   environment. Any mismatch aborts before reuse.
10. Source-hash every imported runtime file, including all
    `src/gpu_runmultiai/*.py`, `src/gpu_run4/ted.py`, ODEFormer
    `sklearn_wrapper.py`, `environment.py`, and `generators.py`. An explicit
    sorted recursive file inventory with per-file SHA256 is acceptable and is
    preferred over an incomplete hand-maintained list.
11. Define direct row predicates for B3, B4, N1, C_q4, and D2. Define exact
    canonical scale tokens and confirmatory-only G1 filtering.
12. Copy all other complete binding contracts from v12/v9 into v13; no
    normative cross-reference to historical drafts or production prose such as
    “same as production” without the algorithm and pinned source hash.

## Acceptance

- audit ID exactly `c0001_metric_identifiability_audit_v13`;
- v9/v10/v11/v12 hashes unchanged;
- all R12 findings mapped to exact v13 sections in a response table;
- 7 Q4 fixtures and 27,637/2,640/30,277 arithmetic reconcile everywhere;
- exact operator tables and n-ary fixtures are internally consistent;
- `git diff --check` and document consistency searches PASS;
- one content commit, push, and exact local/remote verification; at most one
  non-self-referential completion commit.

v13 remains unfrozen pending independent review.
