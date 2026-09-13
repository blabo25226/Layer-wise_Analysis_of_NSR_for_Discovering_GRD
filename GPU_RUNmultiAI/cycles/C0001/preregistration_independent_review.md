# C0001 preregistration independent adversarial review

Reviewer: Codex independent subagent (`statistical-reviewer` / methodological critic)
Review mode: read-only
Verdict: `REVISE_ANALYSIS`
Date: 2026-09-12

## Scope and firewall

Reviewed the canonical preregistration, leakage, reproducibility, and independent-review contracts; the four C0001
scientific/preregistration drafts; and only the necessary Scaler, formula-evaluation, GRN-generation, and GPU_RUN5
configuration source files.

The reviewer did not inspect PR #4, `GPU_RUNclaude1` scientific content, or GPU_RUN5 sealed raw test artifacts.

## Reproduced implementation facts

- `SymbolicTransformerRegressor(params=None)` constructs `Scaler(time_range=[1,10])`; direct `Scaler()` defaults to
  `[1,5]`.
- Mapping `[0,10]` to `[1,10]` gives `a_t=0.9`, `b_t=1.0`.
- The frozen family design yields 510 component instances across 240 parameterized systems: 390 Hill-containing and
  120 pure-linear components.
- `rescale_function` indexes output scale by NodeList component position. A later component passed alone may therefore
  be rescaled with `scale[0]`; the audit must transform full systems before scoring fixed component IDs.

## Critical findings

### C1 — scaled-space forward construction was undefined

With `z_j=s_j x_j` and `tau=a_t t+b_t`, a valid scaled-space candidate is

```math
g_i(z)=\frac{s_i}{a_t} f_i(z/s).
```

Applying `rescale_function` directly to the unscaled truth or to an arbitrary common-factor rewrite does not test a
valid round trip. The frozen audit must record:

- `E0`: analytically forward-scaled full-system candidate
- `E1`: result immediately after the actual rescaling operation
- `E2`: result after the actual simplifier

Only E2 candidates independently confirmed equivalent to the target are eligible for a structural-metric false
negative. E1-equivalent/E2-nonequivalent cases are a separate `simplifier_semantic_drift` endpoint.

Equivalence must use exact-rational analytic construction plus deterministic high-precision fixed-point numerical
checks; it must not depend only on the same CAS path being audited.

### C2 — component design conflicted with full-system Scaler semantics

Run forward scaling and reverse scaling on the full ordered system, then score pre-indexed components. Use the
parameterized system as the primary sampling unit and treat components as within-system repeated observations. Freeze
system, component, Hill-eligible, and linear-control counts separately.

### C3 — parse/runtime failures were excluded from the primary rate

The primary failure-aware rate must use every registered oracle-eligible pair as the denominator. Predicted parse
failure, timeout, NaN/Inf, or silent skip counts as failure. A valid-pair-only rate may be secondary and must be named
conditionally. Truth or oracle-construction failure makes the run incomplete rather than a model/metric false
negative.

## Major findings

### M1 — claim and estimand were too broad

Syntactic exact-tree and skeleton metrics intentionally test representation, not general algebraic equivalence. Limit
the claim to non-invariance and undercounting of algebraically equivalent Hill representations. Do not invalidate the
historical syntactic exact result wholesale. Evaluate Hill-family classification separately from exact-tree recovery.

### M2 — primary endpoint and decision gates conflicted

Use one primary endpoint. For deterministic instrument non-invariance, the clean existence criterion is at least one
registered non-identity E2-equivalent Hill pair whose primary structural metric rejects it. Do not attach a confidence
interval to this existence proof. Treat family/scale prevalence as descriptive unless a minimum rate and breadth are
frozen in advance.

### M3 — ablation conditions were not valid counterfactuals

Do not evaluate a scaled candidate against unscaled truth with `rescale=false`. Use an identity scaler or an
analytically direct-unscaled equivalent candidate. Score E1 for the no-simplifier condition. Treat CAS equivalence as a
diagnostic, not as a rescue of Hill/skeleton endpoints. Remove redundant identity baselines.

### M4 — linear controls cannot enter a Hill false-negative denominator

Use pure-linear components as canonical/skeleton invariance controls. If needed, define a Hill false-positive rate for
non-Hill truth. Keep Hill false-negative calculations restricted to independently eligible Hill expressions.

### M5 — scale design and compute ceiling were inconsistent

Primary scales must stay inside the stated generated range. Keep `5.0` only as a labeled stress condition. Freeze a
finite isotropic grid or an explicit seeded vector list rather than leaving an exponential factorial implicit. Provide
an exact call-count table within the compute ceiling.

### M6 — Scaler construction could silently use the wrong time range

Instantiate `Scaler(time_range=[1,10], feature_scale=1)` explicitly, or freeze the exact wrapper construction. Assert and
save `time_scale=9`, `time_shift=1`, `a_t=0.9`, and `b_t=1.0` at runtime.

### M7 — reproducibility and no-leakage contract was incomplete

Freeze parameter distributions, system ordering, float quantization, scale-vector generation, CAS subset selection,
smoke IDs, exact commands, output overwrite/resume behavior, environment versions, and source hashes. Select any
bounded diagnostic subset by result-independent hash order. A sealed-path guard must be recorded. Smoke observations
must not change the primary corpus or decision gate.

## Required closure

Before PI freeze, a revised draft must close C1-C3 and M1-M7, receive an independent review by a worker different from
the revision implementer, pass the canonical preregistration contract, and remain independent of sealed final-test
artifacts.
