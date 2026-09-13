# C0001 implementation review — round 3

Date: 2026-09-14
Reviewed commit: `bd2a471e673aa631917205128ee81d2f5a906d67`
Frozen preregistration SHA256: `60cfed79780c6b027192a3da14e69416d72090e0a89dddd22248b0f00f50cf00`

## PI decision

`BLOCK_CURRENT_IMPLEMENTATION_AND_REVISE`

The PI independently reproduced `32 passed` under Python 3.10.20, but the
Claude critic found two endpoint-invalidating P0 bugs and several auditability
gaps by reading the immutable target commit.  Passing tests are therefore
insufficient for integration.  This remains a recoverable implementation
failure, not a scientific result or hard stop.

Both round-3 Codex review subagents exhausted their service usage before
returning evidence.  This availability failure is recorded and does not alter
the Claude/PI verdict.

## Independent execution evidence

Command:

```text
PYTHONPATH=src /home/blabo/miniconda3/envs/lansr310/bin/python \
  -m pytest -q tests/test_gpu_runmultiai_c0001_metric_audit.py
```

Result: `32 passed in 250.68s`, exit 0.

`git diff --check` and compileall also exited 0.  No full audit was run.

## P0 findings

### R3-1. Oracle fabricates analytic equivalence

`src/gpu_runmultiai/oracle.py` changes `analytic_equivalent` to true whenever
the numeric grid passes, so the final conjunction reduces to numeric evidence.
Frozen v9 requires independent exact-rational analytic and numeric results, and
`equivalent = analytic AND numeric` without mutation.

This can manufacture a `structural_false_negative`, which is sufficient to
support the existence hypothesis.  Remove the mutation and preserve the real
analytic result.  Add a numerically close but analytically distinct regression
case.  If production tokens make the frozen analytic endpoint impossible, log
an endpoint-affecting deviation and return to preregistration rather than
silently weakening the oracle.

### R3-2. D2 oracle calls are mislabeled as confirmatory B0 calls

The D2 chain labels its E1/E2 oracle calls as `B0_E1` and `B0_E2`.  The live
totals become:

- confirmatory: `23,550 + 660 = 24,210`;
- descriptive: `2,310 - 660 = 1,650`.

The pre-gate ceiling then aborts a completed full run because 24,210 exceeds
23,550.  Label all seven D2 primitives descriptively and test one live D2 pair
as confirmatory 0 / descriptive 7.

## P1 findings

1. External simplifier timeout remains 5.5 seconds (`timeout + 0.5`) rather
   than the frozen 5.0 seconds.
2. Child guard attempts are discarded on timeout, nonzero exit and JSON decode
   failure; G4 can therefore miss prohibited access.
3. The normalized path is realpathed again inside matching, collapsing the
   required independent lexical and real-path checks.  Both symlink directions
   need tests.
4. True resume pre-skip/cache exists only for B0.  Registration, B1, B2, B3,
   B4 and N1 are re-executed and merely suppressed in the log.  The available
   `execute_or_record` helper has no live callers.
5. Secondary canonical/skeleton metrics used by the linear control are
   system-level.  Frozen units are components; sibling Hill changes can
   incorrectly fail a linear component.
6. Required evidence is still discarded: general failure reasons,
   `rescale_incomplete`, formula-metric validity, truth expression, full B3/B4
   rows, registration/precheck evidence, measured Scaler assertions, corpus
   counts/rejection rate and OS/CPU provenance.
7. B2/B3/B4 timeouts and exceptions can still abort the whole audit.  A broad
   exception handler can also convert ceiling/duplicate invariant violations to
   ordinary pair failures instead of re-raising them.
8. Effective timeout and environment values are not fully validated by the CLI
   and resume identity may record constants rather than actual options.

## P2 and disclosure gaps

- `g_corpus_pass` and the no-deviation text are hardcoded rather than derived.
- Raw-token evidence is collected after rationalization, so it is not the
  original input token.
- B1 uses an identity stub rather than the production Scaler with identity
  parameters.
- The only preserved smoke is the explicitly invalid pre-R3 run: wrong commit,
  Python 3.14 and missing torch.  It is not acceptance evidence.
- The test weakens scale 2.0 to chain completion without E1 equivalence.  That
  is not justified by frozen v9 and needs a scientific diagnosis, not an
  assertion relaxation.

## Confirmed improvements

- Correct production scale is now used in the E0 forward transformation.
- E2 is constructed from E1.
- Live B0–B4, N1 and D2 routes exist.
- O_RDONLY matching and early child guard installation were improved.
- Atomic in-progress manifest, typed B4 pair IDs and B0 resume cache exist.
- The focused Python 3.10 test process now exits zero.

## Round-4 acceptance

Fix R3-1/R3-2 and all P1/P2 gaps above.  Add direct tests for analytic/numeric
independence, live D2 attribution, every-condition zero-reexecution resume,
symlink directions, child attempts on all exit modes, component-level controls,
artifact schemas and exception terminalization.  Run a bounded smoke only from
a clean committed checkout under Python 3.10 with torch present, and require its
manifest to record that exact commit and D2 confirmatory contribution zero.

Full confirmatory execution remains prohibited until independent review passes.
No forbidden prior scientific result or historical sealed result was used.
