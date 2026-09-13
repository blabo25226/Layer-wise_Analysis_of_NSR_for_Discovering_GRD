# C0001 implementation review — round 2

Date: 2026-09-13
Primary reviewed commit: `1de692a05f697212127639d20d62d3c0f19dcb88`
Follow-up guard commit: `7791530857861bcb283f8e37d6235bc8da2a6611`
Frozen preregistration SHA256: `60cfed79780c6b027192a3da14e69416d72090e0a89dddd22248b0f00f50cf00`

## PI decision

`BLOCK_CURRENT_IMPLEMENTATION_AND_REVISE`

Round 1 connected more of the audit topology, but independent contract and
reproducibility reviews found remaining P0/P1 violations.  Commit `7791530`
fixes the Python 3.10 guard recursion, but the real E0/E1 chain test still fails.
No confirmatory audit may start from either commit.

## Independent execution evidence

Frozen-compatible local runtime:
`/home/blabo/miniconda3/envs/lansr310/bin/python` (Python 3.10.20).

- At `1de692a`: focused pytest exited 1 with `4 failed, 19 passed`.
- At `7791530`: compileall and `git diff --check` passed; focused pytest exited
  1 with `1 failed, 22 passed` in 129.18 seconds.
- Remaining failing test:
  `test_e1_truth_equivalence_and_e2_from_e1_provenance`.
- Observed failure: the independent oracle completed but
  `e1_oracle.equivalent` was false.

## Blocking findings

### R2-1. Analytic E0 forward scaling uses the wrong scale

Production `Scaler.get_params()` returns `scale = 1 / traj_scale`.  The
implementation builds E0 with `traj_scale` where frozen v9 requires `scale`:

`g_i(z) = (scale_i / a_t) f_i(z / scale)`.

This is now confirmed by the real Python 3.10 E1 round-trip test.  Use the
production `scale` values exactly and test all four primary scales on nonlinear,
multidimensional systems and nonzero component indices.  The frozen production
construction path must also be respected.

### R2-2. The oracle is still not an exact raw-token rational oracle

The oracle still enters through the shared parser that converts numeric leaves
to float and formats them to four significant digits before rationalization.
The power normalization also fails for `pow2`/`pow3`/`pow4`.  Replace this with
a dedicated parser whose numeric leaves go directly from the original token
string to `sympy.Rational`.  Persist raw-token/parsed-rational evidence and
failure reasons.  Cover R01–R08, exponent tiers, long decimal tokens and nonzero
components with self, positive and negative tests.

### R2-3. Confirmatory and optional D2 counters are mixed

The live full path executes 23,550 confirmatory calls plus 2,310 D2 calls, then
passes the combined 25,860 total to G1's confirmatory ceiling of 23,550.  A
successful run would therefore fail G1 and report a completion rate over one.
Separate confirmatory and descriptive counters; make D2 explicitly optional;
check 23,550 and 25,860 against their respective ceilings.

### R2-4. Terminal outcomes are not guaranteed for stage failures

The chain catches too few exception types.  Decode, construction, inverse
rescaling, subprocess timeout, JSON, classifier and metrics failures can abort
the audit rather than yielding exactly one terminal row per attempted primary
pair.  Use the frozen external simplifier timeout of exactly 5.0 seconds.  Wire
B3 to its frozen 60-second CAS timeout.  Convert stage-aware failures according
to the frozen precedence and retain evidence.

### R2-5. Sealed guard coverage remains incomplete

Commit `7791530` removes the recursion seen on Python 3.10, but round-2 review
also found ordinary `os.open(..., os.O_RDONLY)` can bypass a bit-test because
`os.O_RDONLY == 0`.  Use `flags & os.O_ACCMODE`.  Install child protection before
task imports and preserve child access-attempt JSON on success, nonzero exit and
timeout.  Test O_RDONLY, write modes, symlink directions and exceptional exits.

### R2-6. Resume is log suppression after recomputation, not computation resume

Existing keys are checked only when a new call is recorded, after the primitive
has already executed.  Interrupted runs may lack a manifest because it is
written only at the end.  Implement pre-execution 5-tuple lookup with persisted
results, atomic initial manifest/progress checkpoints, true skip/cache restore,
and pre-call ceiling checks.  Prove with a spy/counter that resume does not
re-execute completed primitives.

### R2-7. Typed IDs and reconstructible artifacts remain incomplete

B4 must use frozen `unit_type=pair` and `pair_id`.  Persist complete B3/B4 rows,
registration/precheck evidence, oracle failures and rational parsing evidence,
secondary/TED validity fields, measured Scaler assertions, timeouts, OS/CPU and
all required fixed CSV fields.  Do not use `extrasaction=ignore` to silently
discard evidence.  Configuration load failure must fail fast rather than switch
to an unregistered parser.

## Confirmed improvements

- Live B0/B1/B2/B3/B4/N1/D2 routes now exist.
- Static call arithmetic remains 23,550 confirmatory and 25,860 with D2.
- B0 strata and primary strict-Hill denominator are connected.
- E2 input now comes from E1.
- Classifier parse failure and ordinary five-way outcome precedence improved.
- Commit `7791530` fixed the observed guard re-entrancy and pytest teardown
  failure on Python 3.10.

## Round-3 acceptance requirement

All items R2-1 through R2-7 must be implemented and directly tested.  The
focused suite must exit zero under `lansr310`; static constants alone do not
count as topology/count evidence.  A bounded smoke must run from a clean commit
and record that exact commit.  The full confirmatory audit remains prohibited
until another independent review passes.

The reviews did not use PR #4, `GPU_RUNclaude1` science, or historical sealed
GPU_RUN5 result artifacts.
