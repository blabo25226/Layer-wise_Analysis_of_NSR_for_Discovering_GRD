# C0001 Stage 1 — pre-preregistration observation (expressibility check)

**Status**: exploratory, zero-compute, read-only re-analysis of an **already-stored field** in
GPU_RUN5's train/validation splits. No test data touched. Recorded before preregistration so that it
cannot be presented later as a confirmatory result.

**Date**: 2026-09-09. **Branch/commit**: `20260909_researce_GPU_RUNclaude1` @ `94a571b`.

## Question

The GRN generation failure (`true_exponent_aware_skeleton_in_beam_rate = 0.0` over 960 validation cells
and 47,987 candidates, GPU_RUN5 Phase 3) has at least three competing explanations:

- **E1 expressibility** — the Hill-type truth cannot be written at all in ODEFormer's token grammar
  (`operators_to_use: "sin:1,inv:1,pow2:1,id:3,add:3,mul:1"`, `max_int: 10`, no learnable-exponent `pow`).
- **E2 prior mass / model error** — the truth is expressible but has near-zero probability under the
  pretrained decoder conditioned on the trajectory.
- **E3 search error** — the truth has non-negligible probability but beam-50 *sampling* at
  `beam_temperature: 0.1` never reaches it.

E1 is decidable with no compute, because `scripts/phases/gpu_run5_phase2.py:30 _encode_teacher` already
round-tripped every ground truth through `model.env.equation_encoder.encode/decode` at corpus-build time
and stored the outcome.

## Method

Read `results/runs/gpu_run5_20260823_ddd267b0/phase2/train.json` (240 systems) and
`validation.json` (80 systems). Tabulated the stored fields `teacher_valid`, `teacher_token_length`,
`family`, `dimension`. `teacher_valid` is defined at `gpu_run5_phase2.py:57` as
`bool(decoded is not None and structure["valid"])`, i.e. the truth encoded to ODEFormer tokens **and**
decoded back to a valid tree.

## Result

| split | n | `teacher_valid: True` | `teacher_valid: False` |
|---|---|---|---|
| train | 240 | **240** | 0 |
| validation | 80 | **80** | 0 |

Ground-truth teacher token length (ODEFormer vocabulary):

| split | min | median | mean | max |
|---|---|---|---|---|
| train | 19 | 47.0 | 46.0 | 80 |
| validation | 19 | 47.0 | 45.7 | 80 |

Median token length by family (identical in both splits):

| R01 | R02 | R03 | R04 | R05 | R06 | R07 | R08 |
|---|---|---|---|---|---|---|---|
| 27 | 20 | 41 | 36 | 55 | **62** | **74** | 53 |

Family and dimension coverage is balanced (30 per family in train, 10 per family in validation;
dims 1/2/3 = 60/90/90 train, 20/30/30 validation).

## Interpretation

- **E1 (expressibility) is refuted for this corpus.** 320/320 Hill-type GRN ground truths, including
  every exponent-4 case that must be written `pow2(pow2(x))`, are representable in the checkpoint's
  token grammar and survive an encode/decode round trip. The truth is *inside* the grammar and was
  still never generated. This is a **SOURCE**-level fact from a stored corpus field, not an inference.
- Therefore the generation failure must be **E2 (prior mass) or E3 (search)**, and these two are the
  hypotheses C0001 should discriminate.
- Truth sequences are **long**: median 47 tokens, up to 80. `max_generated_output_len: 200` is not the
  binding limit, so length does not make the truth unreachable *in principle*. But length is the
  mechanism by which E2 and E3 both bite: an exact 47-to-80-token match must survive that many
  sequential decisions. R07 (median 74) and R06 (median 62) are the longest — and R07/R08 were exactly
  the family-holdout test families where selective FT did worst.
- The E2/E3 distinction is the classic **model-error vs search-error** decomposition. It is measurable
  with forward passes only, because `src/gpu_run4/training.py:23 teacher_forcing_loss` already computes
  the decoder CE of an arbitrary token sequence conditioned on a trajectory, and every ground-truth
  sequence is already stored as `tree_encoded`. Comparing the ground truth's per-sequence log-probability
  against the log-probabilities of the 47,987 candidates that *were* sampled decides E2 vs E3 directly:
  - truth log-prob **below** the sampled candidates' range => model error (E2)
  - truth log-prob **within or above** the sampled range yet never sampled => search error (E3)

## Caveats

- `teacher_valid` certifies encodability and tree validity, **not** that the stored `tree_encoded`
  is the *unique* or *shortest* encoding of the truth. Constant tokenization (`max_int: 10`, float
  encoding) may mean the truth's stored form is one of several encodings, which matters for any
  probability claim and must be handled in the preregistration.
- A naive string comparison of `teacher_roundtrip_prefix` against `teacher_prefix` matched only
  60/240 and 20/80. **This is an artifact of my own crude comparison** (component separator `|`
  handling), not evidence of round-trip failure; `teacher_valid` is the authoritative field. Do not
  cite the 60/240 figure as a result.
- This corpus is the GPU_RUN5 *synthetic closed* GRN corpus (R01-R08). The conclusion "the truth is
  expressible" does not automatically transfer to ODEBench truths or to real GRN data.
- Exploratory and hypothesis-generating. It constrains which hypothesis C0001 should test; it is not
  itself a C0001 result.

---

# Addendum — supervisor verification of the operator-support mechanism (F1)

Stage 1 reported that 12 operators carry exactly zero generation probability. I verified this
independently rather than accepting it, because it reshapes the hypothesis tree.

## Verified: the generator config is persisted inside the checkpoint itself

Loading `assets/odeformer/weights/odeformer.pt` yields an `odeformer.model.model_wrapper.ModelWrapper`
whose `.env.params` carries the generator configuration:

```
operators_to_use        = 'sin:1,inv:1,pow2:1,id:3,add:3,mul:1'
operators_to_not_use    = (absent)
required_operators      = ''
extra_unary_operators   = ''
extra_binary_operators  = ''
max_int                 = 10
min_dimension / max_dimension = 1 / 6
max_unary_depth         = 7
min/max_binary_ops_per_dim = 1 / 5
min/max_unary_ops_per_dim  = 0 / 3
float_precision         = 3
max_exponent            = 100
use_sympy               = True
reload_data             = '/data/rcp/odeformer/experiments/datagen_final/datagen_use_sympy_True'
n_enc_layers / n_dec_layers = 4 / 12
```

`reload_data` is a path on the **authors' own training infrastructure**
(`.../experiments/datagen_final/...`). Together with `use_sympy: True` matching that directory name,
this is strong evidence that the persisted `operators_to_use` is the **actual pretraining
data-generation configuration**, not a local parser default. `n_enc_layers`/`n_dec_layers` = 4/12 in the
same object independently corroborates the 4+12 architecture finding from GPU_RUN4.

## Verified: realized sampling probabilities

Read from the live `env.generator` object:

| unary | abs | inv | sqrt | log | exp | sin | arcsin | cos | arccos | tan | arctan | pow2 | pow3 | id |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| prob | **0** | 0.1667 | **0** | **0** | **0** | 0.1667 | **0** | **0** | **0** | **0** | **0** | 0.1667 | **0** | 0.5 |

| binary | add | sub | mul | div |
|---|---|---|---|---|
| prob | 0.75 | **0** | 0.25 | **0** |

**Exactly-zero-probability operators (12 of 18): `abs, sqrt, log, exp, arcsin, cos, arccos, tan,
arctan, pow3, sub, div`.**

Mechanism confirmed in source at `third_party/odeformer/odeformer/envs/generators.py:369-373`:
`self.operators_downsample_ratio = defaultdict(float)` is populated *only* from the
`operators_to_use` string; the probability loop then appends `0.0` for any operator not present.
So absence from that string is not a down-weighting — it is exact exclusion.

## Why this matters scientifically

- **Vocabulary membership is not prior mass.** The decoder vocabulary has 10,293 words and contains
  these operator tokens, but the training distribution assigned them zero mass. Any analysis that
  infers "the model can express X" from vocabulary alone is invalid for this checkpoint.
- **`div` and `sub` are both zero.** Division is reachable only as `mul(x, inv(y))`, and subtraction
  only as `add` with a negative constant. Every rational/Hill structure must be assembled from
  `{id, add, mul, inv, pow2, sin}` alone. `max_unary_depth = 7` does permit `pow2(pow2(x))`, so
  Hill exponent 4 is reachable in principle — consistent with the 560/560 encodability result above.
- **`exp` and `log` are zero** — both ubiquitous in biochemical and pharmacokinetic dynamics.
- This sharpens, rather than replaces, the model-error vs search-error question for GRN: the GRN
  truths use *only* in-support operators, so operator support cannot explain the 0/960 GRN failure.
  It is a genuine dissociation, and it is why C0001 must discriminate prior mass from search budget.

## Scope limit

This establishes zero probability **under the generator configuration persisted in the released
checkpoint**. It does not by itself prove the published training run used no other operator
distribution at any stage. Pending primary-source confirmation, the defensible claim is exactly:
*"zero probability under the checkpoint's own persisted generator configuration."*

---

# Correction — "encodable" is not "in the generator's support"

Stage 2 (literature) surfaced a distinction that **weakens the interpretation** I attached to the
560/560 `teacher_valid` result above. Recording the correction here rather than silently revising.

`env.params` also carries **`max_unary_ops_per_dim = 3`**, and the unary sampling distribution gives
`id` weight 0.5 (3 of 6), so `id` itself consumes unary budget — the expected non-identity unary count
per dimension is roughly 1.5.

Counting minimal non-identity unary operators for a Hill-4 term:

| form | unary ops needed | within `max_unary_ops_per_dim = 3`? |
|---|---|---|
| multiplicative `a * x^4 / (K^4 + x^4)` | **5** | **no** |
| affine-decomposed `a - a*K^4 * inv(K^4 + x^4)` (algebraically identical) | **3** | yes |

So:

- **What 560/560 `teacher_valid` does establish**: the truth is representable in the token vocabulary
  and survives `equation_encoder.encode/decode`. The tokenizer is not the barrier.
- **What it does NOT establish**: that the pretraining *generator* could ever have sampled that form.
  In its canonical multiplicative form, Hill-4 exceeds the generator's per-dimension unary budget and is
  therefore **outside the pretraining support**, even though it is perfectly encodable.
- The two forms above are algebraically equal but structurally different. Which one the corpus stored as
  the "truth skeleton", and which one the matcher required, therefore determines whether
  `true_exponent_aware_skeleton_in_beam_rate = 0.0` measures a **generation failure** or a
  **matcher/canonicalization failure**.

## Consequence for C0001 design

This creates a fourth competing explanation that must be tested *before* the model-error vs
search-error question, because it can invalidate the premise of that question:

- **E0 measurement/evaluator artifact** — the model does place algebraically-equivalent structure in the
  beam, but the exponent-aware *string* skeleton matcher scores it as a miss.
- E1 expressibility — refuted (560/560 encodable).
- **E1' generator-support exclusion** — the truth's canonical form exceeds
  `max_unary_ops_per_dim`, so it was never in the pretraining distribution. **New, and live.**
- E2 prior mass / model error.
- E3 search error.

E0 and E1' are both decidable with **zero GPU**: E0 by re-scoring the already-stored 47,987 GRN
candidates with a canonicalizing / CAS-equivalence matcher instead of a string matcher; E1' by
analytically counting minimal unary ops for each of the 320 train+validation truths in both forms.
E2 vs E3 then requires forward passes only, and must score the ground truth in **both** encodings.

C0001 is therefore reframed from a two-way (E2 vs E3) test into a preregistered **four-way
decomposition** (E0 / E1' / E2 / E3), ordered so that the cheapest claim-invalidating check runs first.
