# C0001 implementation review — round 4

Date: 2026-09-14
Reviewed commit: `c4a4c6d3534425ae4216c753ea4602bc4fa5e0ec`
Frozen preregistration SHA256: `60cfed79780c6b027192a3da14e69416d72090e0a89dddd22248b0f00f50cf00`
Remote task-branch SHA: `c4a4c6d3534425ae4216c753ea4602bc4fa5e0ec`

## PI decision

`BLOCK_CURRENT_IMPLEMENTATION_AND_REVISE`

Two independent Codex reviewers and the PI found endpoint-invalidating defects
at the immutable R4 commit.  The focused Python 3.10 test suite passes, but the
implementation cannot yet execute the frozen confirmatory endpoint faithfully.
This is a recoverable implementation failure, not a scientific result and not
a hard stop.  No full audit was run.

Implementer: Cursor Agent.  Independent reviewers: Codex contract-audit
subagent and Codex reproducibility-audit subagent.  The reviewers differ from
the implementer (`reviewer_diff_assertion: true`).

## Independent execution evidence

```text
PYTHONPATH=src /home/blabo/miniconda3/envs/lansr310/bin/python \
  -m pytest -q tests/test_gpu_runmultiai_c0001_metric_audit.py
```

PI result: `38 passed in 265.34s`, exit 0.  Reproducibility-reviewer result:
`38 passed in 277.72s`, exit 0.

The preregistration hash and local/remote task-branch SHA match.  The complete
range check
`git diff --check 8a82516218d5d6ab6baf949f3c9ff25250990fcb..c4a4c6d3534425ae4216c753ea4602bc4fa5e0ec`
fails on trailing whitespace in the committed R4 smoke CSV.  The completion
record's diff-check claim therefore does not reproduce for the delivered range.

## Blocking findings

### R4-1 — exact-rational oracle violates the frozen parser and analytic method (P0)

`src/gpu_runmultiai/oracle.py:120-125,173-184` converts a parsed SymPy Float
with `Rational(expr)`, not each original decimal token with
`Rational(token_string)`.  `oracle.py:363-403` also retains non-frozen
`equals` and tolerance-based `nsimplify`.  The prefix route converts back to
infix and loses original raw-token provenance (`oracle.py:419-438`).

The reviewer reproduced `(0.1*x_0)` versus `((1/10)*x_0)` as
`numeric_equivalent=true` but `analytic_equivalent=false`.  Frozen v9 requires
exact-token rationalization, exact `simplify(expand=True)`, and independently
computed analytic and numeric results.  Implement one token-preserving parse
path shared by truth/E0/E1/E2 and remove all non-frozen fallback semantics.

### R4-2 — registration and N1 fail on the production power dialect (P0)

`pow2`/`pow4` expressions are sent through an incompatible infix route
(`src/gpu_runmultiai/rewrites.py:39,69`; `oracle.py:467-471`).  An independent
full registration-only diagnostic produced 250 valid and 260 invalid rewrites;
all 260 invalid rows were `ParseError`.  N1 produced only 46 completed rejects
and 54 `ParseError` rows.  Thus G_inc and G_n1 fail because of the audit
implementation rather than the frozen scientific condition.

Use the token-preserving prefix dialect for registration/N1 and normalize all
frozen power operators.  Add complete 510-registration and 100-N1 acceptance
tests or a deterministic bounded equivalent that asserts all relevant dialects.

### R4-3 — counted-call persistence is neither terminal nor crash durable (P0)

`CallLogger.execute_or_record` records only after the executor returns
(`src/gpu_runmultiai/calls.py:124-149`).  A timeout or exception is therefore
not counted.  Tree payloads are not JSON serializable and
`stage_cache.append_stage_cache` silently drops them
(`src/gpu_runmultiai/stage_cache.py:35-40`).  The committed smoke has 29 call
records but only 23 stage-cache records; all six E0/scaler calls needed for
resume are missing.

Persist a JSON-safe, sufficient stage result for every counted primitive and
make progress crash-consistent.  A completed or terminal failed call must have
one durable key and sufficient result data before later stages proceed.  Do not
silently discard serialization failures.  Add kill-point tests around executor,
call-log and cache persistence, then prove zero re-execution after resume.

### R4-4 — B2/B3/B4 failure terminalization is broken (P0)

All `RuntimeError` instances are re-raised at
`src/gpu_runmultiai/pipeline.py:683,765,877`, so ordinary production failures
abort the audit instead of producing terminal rows.  Only explicit ceiling,
duplicate-key and resume-identity/cache invariants may abort.  Additionally the
B2 handler expands `**b0_row` and repeats `condition`/status keywords
(`pipeline.py:686-693`), causing a second exception during recovery.  B3 can
return a failure payload while logging zero counted calls.

Introduce explicit invariant exception types; terminalize ordinary exceptions
and timeouts with one failed counted call and a complete row.  Directly test
ordinary `RuntimeError`, timeout and invariant injection for B2, B3 and B4.

### R4-5 — B1 is not the frozen identity baseline (P1)

The B1 path calls `build_production_scaler(1.0)` and forward scaling
(`src/gpu_runmultiai/pipeline.py:284-306`), yielding `a_t=0.9`, `b_t=1.0` and
`time_scale=9`.  Frozen B1 requires identity E0 followed by identity rescale,
once per component, with `s=1`, `a_t=1`, `b_t=0`.  The existing
`build_identity_scaler` is unused.  Route B1 through that identity scaler and
assert the actual parameters and component count.

### R4-6 — G4 can false-pass, especially after resume or timeout (P1)

The simplifier child prints guard attempts only after the simplifier returns
(`src/gpu_runmultiai/simplifier_worker.py:28-50`); a killed child cannot expose
an attempt that occurred before timeout.  Cached simplifier/pair results do not
merge prior child attempts into the current guard.  Relative paths are resolved
against current working directory rather than repository root
(`src/gpu_runmultiai/sealed_guard.py:26-32`); the reviewer reproduced a denied
relative path becoming allowed after `chdir('/tmp')`.

Use durable child-attempt side-channel storage or an equivalent mechanism that
survives nonzero, invalid JSON and timeout, replay attempts during resume, and
resolve all relative paths against the repository root.  Test both symlink
directions, a changed working directory, every child exit mode, and resumed
G4 aggregation.

### R4-7 — required artifacts and terminal ordering remain incomplete (P1)

`pair_results.csv` omits general `failure_reason`, `rescale_incomplete` and
`formula_metrics_valid`; `equivalence_oracle.json` drops oracle failure reasons
and raw-token/parsed-rational evidence.  Every smoke `duration_sec` is null.
The manifest is marked `completed` before the final artifacts are written
(`src/gpu_runmultiai/audit.py:395-433`).

Emit the complete frozen schema, measure real durations, write all primary
artifacts atomically, and set `status=completed` last.  Add exact schema and
finalization-order tests.  Remove the committed CSV whitespace defect at its
generator, then regenerate smoke evidence from the repaired clean commit.

### R4-8 — frozen resource/environment gates do not fail fast (P1)

The 4 CPU-hour and 1 GB ceilings are not enforced.  The CLI uses `setdefault`,
so an incorrect pre-existing frozen environment value is accepted.  G0 is
evaluated only after all work and becomes an undecidable result instead of
aborting before the primary audit.

Validate frozen environment values byte-for-byte, enforce resource ceilings,
and run G_corpus/G0/G4 preconditions at their frozen positions.  Add negative
tests for each fail-fast condition.

## Confirmed R4 improvements

- all seven D2 primitives are descriptive condition `D2`, contributing zero
  confirmatory calls per live pair;
- the external simplifier timeout is exactly 5.0 seconds;
- the preregistration file was unchanged;
- the task branch was pushed and its remote SHA verified;
- focused tests pass under the intended Python 3.10 environment.

## Round-5 acceptance

Fix R4-1 through R4-8 without changing the frozen plan, weakening assertions or
using forbidden prior science.  Tests must reproduce the full dialect, failure,
crash/resume, guard and schema contracts rather than only happy paths.  Run the
bounded smoke from a clean exact commit under `lansr310`, regenerate only the
R5 smoke path, run the complete range `git diff --check`, commit, non-force push
the task branch and verify the remote SHA.  The pre-R4 untracked smoke remains
invalid and must not be staged or used as acceptance evidence.

Full confirmatory execution remains prohibited until a different worker's
independent reproducibility review passes.
