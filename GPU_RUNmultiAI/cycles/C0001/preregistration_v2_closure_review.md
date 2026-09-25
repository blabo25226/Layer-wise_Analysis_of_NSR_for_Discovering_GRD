# C0001 preregistration v2 independent closure review

Reviewer: Claude (`scientific-critic` / methodological reviewer)
Implementer: Cursor Agent
Reviewed commit: `bb201c158bddd827ed08ab656b946d00d61a8444`
Mode: read-only
Verdict: `REVISE`
Date: 2026-09-13

## Scope and firewall

The reviewer read the v1 review packet, v2 draft, response map, and only the necessary Scaler, simplifier,
formula-evaluation, structure-classification, GRN-generation, and GPU_RUN5 configuration source files. PR #4,
`GPU_RUNclaude1` scientific content, and GPU_RUN5 sealed raw test artifacts were not inspected.

## Independently verified as correct

- The analytic E0 inversion is family-independent:
  `g_i(z)=(s_i/a_t) f_i(z/s)` exactly inverts `rescale_function` before serialization/simplification.
- `time_scale=9`, `time_shift=1`, `a_t=0.9`, and `b_t=1.0` are correct for `[0,10] -> [1,10]`.
- 240 systems, 510 components, and 120 pure-linear components are correct.
- `{0.1,0.5,1.0,2.0}` is within the IC scale range and `5.0` is a stress value.
- Full ordered-system transformation avoids the NodeList component-index mismatch.
- The v2 grand total 11,190 is arithmetically correct, although its confirmatory subtotal and included operations are
  not correct.

## Blockers

### C-A — primary readout does not come from `formula_metrics`

`formula_metrics(skip_cas=True)` does not return `hill_form`. `classify_formula` produces both a system-level
`hill_form=any(component)` and component-level flags. The system-level OR can hide the component false negative.

Required fix: use
`classify_formula(E2_infix)["component_flags"][component_idx]["hill_form"]` as the primary readout. Use
`formula_metrics` only for secondary canonical/skeleton/TED measures.

### C-B — strict-Hill denominator is 330 components, not 390

Truth-side strict classification gives 11 strict-Hill components per family/exponent/draw tuple:

- R01: 1
- R02: 1
- R03: 2
- R04: 1
- R05: 2
- R06: 3
- R07: 1; R07 component 3 is modulated, not strict
- R08: 0; R08 component 3 has a product base rejected by the strict denominator checker

Thus the result-independent primary denominator is `11 * 3 * 10 = 330` components and `330 * 4 = 1,320` scale
pairs. The remaining partition is 60 non-strict Hill-bearing components and 120 linear components. Including the 60
would make the existence gate spuriously support the hypothesis because their truth itself is not strict-Hill.

Required fix: freeze eligibility from the truth-side component flag before running E0/E1/E2; report the 60-component
stratum separately.

### C-C — call ceiling is wrong and omits required work

`2,040 * 4 + 500 + 100` is 8,760, not 8,260. The table also omitted rewrite equivalence prechecks, N1 oracle checks,
and E1 equivalence decisions needed for semantic-drift classification. A literal 8,260 abort would stop below the
registered work and force an undecidable result.

Required fix: rederive all operation counts from the corrected 330/1,320 corpus. Define exactly what one counted call
means. Include every truth/rewrite precheck, E1/E2 oracle check, classifier/metric call, baseline, negative control, and
diagnostic. Raise or reduce the budget explicitly; do not patch one subtotal in isolation.

### C-D — B1 is the forbidden scaled-vs-unscaled comparison

Passing primary-grid E0 through an identity scaler leaves E0 scaled while the reference truth is unscaled. Even at
`traj_scale=1`, `a_t=0.9`, so E0 is not the truth. It provides no valid counterfactual.

Required fix: construct B1 E0 at identity parameters (`s=1`, `a_t=1`, `b_t=0`), then run the identity rescale and
simplifier. This is one scale-independent condition, not four.

### C-E — actual simplifier semantics were not modeled

The production default is `expand=False, resimplify=False`; it parses with SymPy and rounds every Float to four decimal
places. GRN constants are currently formatted to four significant digits, so small constants may drift at E2. The
internal one-second timeout is swallowed and returns the original tree, so an ordinary try/except cannot observe it.

Required fix: make every generated audit constant exactly representable at four decimal places, record the production
defaults, run simplification in a single-threaded instrumented subprocess with an external frozen timeout, and keep
semantic drift/execution status separate from structural false negatives. Do not infer timeout solely from E2==E1.

### C-F — denominator was still conditioned on E2 outcome

`oracle-eligible` was defined by E2 equivalence, so non-equivalent E2 and failures were removed after observing the
outcome. Parse failures cannot simultaneously satisfy the numerator requirement of E2 equivalence.

Required fix: freeze the denominator as all registered truth-side strict-Hill pairs. Assign every pair to exactly one
of `{structural_false_negative, oracle_equivalent_and_flagged, simplifier_drift, execution_failure,
construction_incomplete}`. Report every category over the same fixed denominator so the proportions sum to one.

## Major findings

### M-a — primary rule gained secondary conjuncts

The existence rule was later combined with linear false-positive, linear non-invariance, and incomplete thresholds,
leaving some outcomes undefined. Controls should be validity gates evaluated before the sole hypothesis decision. A
failed control makes the result undecidable, not unsupported.

### M-b — Scaler production path description was inaccurate

`SymbolicTransformerRegressor(params=None)` is the correct `[1,10]` path; only bare `Scaler()` defaults to `[1,5]`.
Also freeze/assert `rescale_features=true` and define the synthetic trajectory supplied to `Scaler.fit`, because it
sets `traj_scale` from the earliest time point.

### M-c — timeout values were not frozen

Freeze external oracle and CAS timeout seconds. Treat timeouts as their own fixed-denominator outcome category, not as
a structural false negative. State the production simplifier's source-fixed internal one-second behavior.

### M-d — equivalent rewrites had no operational role or seed

State whether primary E0 is built from the equivalent rewrite or truth. If the hypothesis concerns representation
non-invariance, use the non-identity rewrite, preverify it, and add `audit_rewrite_seed=61003`.

### M-e — serialization and prefix dialect were unspecified

Freeze tree-to-infix conversion. Handle `neg` explicitly and document power normalization: the truth may encode
fourth power as nested `pow2` while SymPy emits `x**4`, which can mechanically change skeleton strings. Preserve both
raw prefix and emitted infix at E0/E1/E2.

### M-f — sealed-path guard was vacuous in the isolated worktree

Derive prohibited paths from configured GPU_RUN5 output roots, enumerate explicit glob patterns including per-problem
prediction files, record match counts including zero, and fail on any attempted read. State that freshly regenerating
R07/R08 from source with a new seed is allowed and does not access the historical sealed holdout.

### M-g — `rescale_incomplete` is construction failure

It must be an assert/incomplete outcome, never a structural false negative. It should be unreachable for a correct full
system.

### M-h — resume and commands were incomplete

Resume key must be `(condition, pair_id)`, not `pair_id`. Frozen commands must include every seed, and resume must verify
audit ID, commit, config/source hashes, corpus hash, and seeds before skipping completed rows.

## Moderate findings

- Rename `linear_canonical_invariance_rate` to `linear_canonical_noninvariance_rate` because it counts exact failures.
- Remove inert `audit_scale_seed` for a full deterministic cross.
- Use one completion threshold consistently.
- B4 truth-copy is scale-independent and should run once per component if retained.
- State explicitly that component flags, not system-level OR, are read.
- Forbid thread-parallel simplification because the timeout implementation uses process signals.
- State the autonomous-system precondition for omitting `tau` from `g_i`.
- Explain the explicit CPU override without mutating `base.yaml`'s `allow_cpu: false`.
- Acknowledge that an existence gate is thin confirmatory evidence; any prevalence threshold must be frozen separately
  and not substituted after results.

## Required closure

Do not freeze v2. Produce a v3 that resolves C-A through C-F, re-derives the corpus and complete call table, closes
M-a through M-h and the moderate items, then submit it to an independent reviewer distinct from Cursor.
