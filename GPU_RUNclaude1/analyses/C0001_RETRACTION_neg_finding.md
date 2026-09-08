# RETRACTION — the C0001 `neg`-canonicalization "finding" was an artifact of my own analysis

**Issued**: 2026-09-09, by the supervisor, during C0001 Stage 3 review.
**Severity**: material. The retracted claim appeared in a commit message (`bfbf727`), in
`human_review_queue.md` (HRQ-0002), in `C0001_stage1_preobservation.md`, and in
`C0001_exploratory_neg_canonicalization.md`, and it was used to reframe C0001 around explanation E0.
**Found by**: `lansr-reproducibility-auditor` (CRIT-1, CRIT-2), independently verified by the supervisor.

---

## What I claimed

> "All 960 truth skeletons contain a `neg` node versus 3.2% of candidates. Folding that asymmetry
> leaves the system-level truth-in-beam rate at 0/960 but raises the component-level rate from
> **0/2040 to 107/2040**, so GPU_RUN5's component floor effect was matcher-induced."

and, more specifically:

> "107 of 2040 components (5.25%) are structural matches that the frozen string matcher scored as
> complete misses."

## Why it is wrong

**1. The 0/2040 baseline was an artifact of mixing two representations.**

`phase3/cells/*.json -> true_structure.exponent_aware_skeleton` is derived from **`true_prefix`**.
The candidate skeletons are derived from **infix** formula strings. Verified over all 960 validation cells:

| stored truth skeleton reproduced from | match |
|---|---|
| `true_prefix` | **960 / 960** |
| `true_formula` (infix) | **0 / 960** |

Example (R01), same system, two representations:

```
from true_prefix : add,add,CONST,mul,mul,CONST,inv,add,CONST,x_0,x_0,neg,mul,CONST,x_0
from true_formula: add,add,CONST,mul,CONST,x_0,mul,mul,CONST,inv,add,CONST,x_0,x_0
```

The prefix-derived form contains `neg`; the infix-derived form does not. I compared the
**prefix-derived truth** against **infix-derived candidates**. That comparison cannot match, for
reasons that have nothing to do with the model or the matcher. My "raw 0/2040" measured my own
representation mismatch.

**2. The 107/2040 figure is not new — it is GPU_RUN5's already-published value.**

`results/runs/gpu_run5_20260823_ddd267b0/phase3/beam_groups.json` field
`component_true_exponent_aware_skeleton_in_beam` contains, over all 960 groups:

```
component_true_exponent_aware_skeleton_in_beam : 107/2040 = 0.0525
true_exponent_aware_skeleton_in_beam           :   0/960  = 0.0000
by family: R01 0/120, R02 0/120, R03 0/240, R04 56/240, R05 0/240,
           R06 0/360, R07 17/360, R08 34/360
```

GPU_RUN5 already measured and stored both numbers. My `neg`-folding coincidentally transformed the
prefix form toward the infix form and thereby **re-derived the published value**. I mistook a
re-derivation for a discovery.

## What is retracted

- **RETRACTED**: that the frozen matcher scored 107 real component matches as misses.
  GPU_RUN5's matcher compared infix to infix correctly and recorded all 107.
- **RETRACTED**: that GPU_RUN5's component-level measurement was "biased to exactly zero by the
  matcher". It was never zero. The zero was mine.
- **RETRACTED**: that "GPU_RUN5's `component_exact_loss = 0.0` floor effect was matcher-induced."
  This additionally conflated two distinct quantities — *in-beam component coverage* (107/2040) and
  *exact recovery of the selected candidate* under causal intervention (`component_exact_loss`).
  They are different estimands and my inference moved between them illegitimately. Whether that
  causal-intervention floor is genuine remains **open and untested**.
- **CONSEQUENCE**: explanation **E0 (evaluator/measurement artifact) loses its component-level
  empirical support.** It is not refuted — no one has yet run a canonicalizing CAS matcher — but the
  evidence I offered for it does not exist.

## What survives, and is unaffected

- **The `neg` representational asymmetry itself is real** as a fact about the two encodings:
  the GRN generator writes decay as an explicit `-1 * k * x` while ODEFormer must use signed
  constants, because `sub` and `div` both have exactly zero generation probability in this
  checkpoint. This remains a correct and relevant observation about the model's expressive route.
  It is simply **not** a defect in GPU_RUN5's measurement.
- **The zero-probability operator finding stands** (HRQ-0001): 12 of 18 operators at exactly 0.0
  sampling probability under the checkpoint's own persisted generator. Verified directly from
  `env.generator`, independent of any skeleton comparison.
- **The encodability finding stands** (HRQ-0002 first half): 320/320 (Stage 1: 560/560) GRN truths
  round-trip through the tokenizer. Verified from the stored `teacher_valid` field.
- **The Hill-4 correction stands**: nested `pow,pow,x_i,2,2` in 39/170 components, 24/80 systems,
  so E1' (generator-support exclusion) is live. Verified on parsed structure.
- **The system-level claim stands**: truth-in-beam is 0/960, as GPU_RUN5 published.

## Root cause, and the standing rule it produces

Two errors compounded, both mine:

1. I compared derived string representations without first verifying they were produced by the same
   derivation path. The earlier Hill-4 error had exactly the same shape — searching a canonicalized
   string for a surface token.
2. I did not check whether the quantity I was "discovering" was already stored in the source run's
   own artifacts. `beam_groups.json` had the answer the whole time, one field away from the file I
   was reading.

**Standing rule for this campaign, effective now:**

> Before reporting any re-measurement of a prior run as new, (a) verify that both sides of any
> comparison come from the same derivation path, and (b) grep the source run's stored artifacts for
> the quantity itself. Re-deriving a published number is a *positive control*, not a finding — and it
> should be run and labeled as such.

This rule is added to `research_state.md` §8 and should be applied by the implementation and analysis
stages of every subsequent cycle.
