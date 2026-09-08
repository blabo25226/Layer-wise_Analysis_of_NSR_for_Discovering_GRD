# C0001 — EXPLORATORY diagnostic: `neg` canonicalization asymmetry in the truth-in-beam matcher

**LABEL: EXPLORATORY.** Run by the supervisor on 2026-09-09 *before* the C0001 preregistration was
frozen, as a feasibility probe on whether the planned Part A measurement is well-posed. It is **not**
a confirmatory C0001 result and must be disclosed as prior information in
`GPU_RUNclaude1/plans/C0001_preregistration.md` (rule 01 item 9).

Data: GPU_RUN5 **validation** cells only (`results/runs/gpu_run5_20260823_ddd267b0/phase3/cells/*_validation_*.json`,
960 files, 47,987 candidates). **No sealed test data was read.** Branch `20260909_researce_GPU_RUNclaude1` @ `94a571b`.

## Observation that prompted this

Token-vocabulary comparison of the stored exponent-aware skeletons:

| | truth skeletons (n=960) | candidate skeletons (n=47,987) |
|---|---|---|
| contain `neg` | **960 (100.0%)** | **1,541 (3.2%)** |
| contain `pow2` | 0 | 0 |

Truth skeleton token vocabulary: `CONST` 6120, `mul` 4920, `add` 4080, `x_0` 2760, `pow` 2376,
`2` 2376, `neg` 2040, `inv` 1680, `x_1` 1680, `x_2` 480.
Candidate vocabulary (top): `CONST` 241094, `mul` 222331, `add` 117050, `x_0` 94060, `x_1` 72404,
`x_2` 33786, `pow` 26880, `2` 25159, `inv` 9000, `sin` 6613, `neg` 1555, `3` 1336, `4` 308, `5` 77.

**Mechanism.** Every GRN family writes its decay term as an explicit `-1 *` product, e.g. R01's truth
`0.1954 + 0.8878 * x_0 * 1/(0.8392 + x_0) + -1 * 0.3968 * x_0`, which canonicalizes to a skeleton
containing `neg,mul,CONST,x_0`. ODEFormer instead emits a *signed constant*
(`-0.0191 * (12.77 + 2.664*x_0)**-1`), which canonicalizes to `mul,CONST,...` with **no `neg` node**.
Under `CONST` masking the constant's *value* is erased but the `neg` node is *structural*. So
`-1 * k * x` and `-k * x` are the same function yet produce different skeletons.

Because `sub` and `div` both have **exactly zero** generation probability in this checkpoint
(see `C0001_stage1_preobservation.md` addendum), the model has no way to produce a `neg`-shaped
subtraction; it must use signed constants. The truth-side encoding and the model-side encoding are
therefore systematically mismatched for a term present in **every** GRN system.

## Exploratory re-measurement

I folded `neg,mul,CONST -> mul,CONST` and `neg,CONST -> CONST` on both sides (a crude hand-written
token folder, *not* the repository canonicalizer) and recomputed index-aligned matches.

| endpoint | raw exponent-aware skeleton | `neg`-normalized |
|---|---|---|
| full-system truth-in-beam | **0 / 960 = 0.0000** | **0 / 960 = 0.0000** |
| per-component truth-in-beam | **0 / 2040 = 0.0000** | **107 / 2040 = 0.0525** |

Per family (n=120 cells each), full-system hits were 0 both raw and normalized for all of
R01-R08 — no family recovers a whole-system match.

## Interpretation (bounded)

1. **GPU_RUN5's headline system-level claim survives.** Truth-in-beam remains exactly 0/960 after
   normalization. The conclusion "the true GRN system skeleton is never generated" is **not** a
   canonicalization artifact. E0 does not overturn it.
2. **But the component-level measurement was biased to exactly zero by the matcher.** 107 of 2040
   components (5.25%) are structural matches that the frozen string matcher scored as complete misses.
   The model does place correct component structure in the beam far more often than 0% of the time.
3. **This has a concrete downstream consequence.** GPU_RUN5 reported
   `component_exact_loss = 0.0` for all 16 layers in the causal-intervention analysis and called it a
   floor effect. If the true component-match baseline is ~5% rather than 0%, that endpoint is **not**
   at the floor, and the causal-intervention analysis may have discarded usable signal. This is a
   testable, specific consequence for a later cycle.
4. Scope: this is one crude normalization of one encoding asymmetry. A proper Part A must use
   `src/gpu_run4/formulas.py` canonicalization plus timeout-guarded CAS equivalence
   (`src/evaluation/equation_metrics.py:169 symbolic_recovery`, `:68 _approximately_equivalent`),
   which will likely find *more* matches than my token folder, and must include a mandatory positive
   control so that a null cannot be produced by a broken matcher.

## Effect on the preregistration

Because I have now seen the 5.25% figure, the confirmatory Part A **cannot** be framed as a blind
discovery test of "is the component rate > 0". It must instead be preregistered as an **estimation**
with a clustered confidence interval, with this exploratory value disclosed as prior information, and
with the *system-level* rate as the primary endpoint (which I have seen only as 0/960, consistent with
the already-published GPU_RUN5 value, so no new information was gained there).

Also note for Part B: **0/960 truth skeletons contain `pow2`**, and the truth vocabulary contains only
`pow,2` (2376 occurrences), never `pow,4`. The validation truths in this corpus realize Hill exponents
1 and 2, not 4. The multiplicative-Hill-4 unary-budget argument (5 non-identity unaries vs
`max_unary_ops_per_dim = 3`) therefore applies to **fewer systems than assumed**, and Part B must count
the actual realized exponents rather than the configured `hill_exponents: [1, 2, 4]`.
