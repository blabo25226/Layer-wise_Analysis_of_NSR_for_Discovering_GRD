# C0001 — Statistical Review (Stage 3, pre-freeze)

| field | value |
|---|---|
| cycle | `C0001` |
| stage | 3 — statistical review required by `C0001_preregistration.md` §17 before Stage 7 |
| reviewer role | `lansr-statistical-reviewer` (distinct from methodologist, implementer, analyst) |
| object of review | `GPU_RUNclaude1/plans/C0001_preregistration.md` + `.json`, commit `94a571b` |
| branch | `20260909_researce_GPU_RUNclaude1` |
| date | 2026-09-09 |
| preregistration modified by this review | **NO** (read-only, per instruction) |
| verdict | **AMEND_BEFORE_FREEZE** |

All intervals, error rates and simulations below were computed by this reviewer in
`lansr310`, not quoted from the plan. Reproduction commands are in §12.

---

## 0. Summary of position

The preregistration is unusually careful about *disclosure* and *bookkeeping* and unusually
careless about *estimands*. Its statistical unit, its aggregation order, its control battery, its
degenerate-paired-test warning and its prior-information ledger are better than most published
work. But four things are wrong at the level of what is being estimated, and two of them mean
the cycle as written cannot answer the question it poses:

1. The primary endpoint's reduction — a conjunction over *all* components of a system — is
   orthogonal to the mechanism E0 is alleged to operate through, which is a *per-component*
   encoding asymmetry. The primary is therefore not a near-tautology by accident; it is a
   near-tautology by construction, and its power against the scientifically live alternative is
   approximately zero.
2. The Wilson interval on 80 systems is valid only if the intra-family correlation is below
   **0.011**. Family is perfectly confounded with dimension in this corpus, and the campaign's
   own prior evidence says dimension is the dominant predictor. Under the natural reading of the
   estimand, the effective sample size is 8–15, and the bound at 0 hits is 0.08–0.32, not 0.046.
3. Part C's fairness verification (`input_trajectory_checksum`) is empirically vacuous — the
   field is constant across all 12 cells of a system.
4. Part C's E2/E3 discriminator (rank of the GT log-prob within 50 temperature-0.1 samples)
   does not identify model error, and its E2 branch will pass by construction.

None of these requires discarding the four-part structure, the data, or the compute plan. All
six required amendments in §11 are surgical. But two of them replace the inferential core of a
part rather than adjust it, and the plan must not be frozen with them outstanding.

I found no evidence of result-rescuing, hypothesis-shifting, or undisclosed prior information.
The integrity discipline is real. The problem is measurement theory, not honesty.

---

## 1. Verification of the arithmetic the plan asserts

### 1.1 The methodologist's power claim is CORRECT

`OK` — §9.2 ("Power limitation, stated plainly"), §7.1.

The claim that at n = 80 a Wilson 95% upper bound < 0.05 is attainable **only at exactly zero
hits** is verified. Plain Wilson score, α = 0.05, z = 1.959964:

| k / 80 | p̂ | Wilson 95% CI | Clopper–Pearson 95% CI | upper < 0.05? |
|---|---|---|---|---|
| **0** | 0.0000 | **[0.0000, 0.0458]** | [0.0000, 0.0451] | **yes** |
| **1** | 0.0125 | **[0.0022, 0.0675]** | [0.0003, 0.0677] | no |
| **2** | 0.0250 | **[0.0069, 0.0866]** | [0.0030, 0.0874] | no |
| **3** | 0.0375 | **[0.0128, 0.1045]** | [0.0078, 0.1057] | no |
| **4** | 0.0500 | **[0.0196, 0.1216]** | [0.0138, 0.1231] | no |
| **8** | 0.1000 | **[0.0515, 0.1851]** | [0.0442, 0.1876] | no |

The plan's "1/80 already gives a Wilson upper bound of ≈ 0.0675" is exactly right.

Smallest n at which one hit still permits the bound: **n = 110** (upper 0.0497). Two hits:
**n = 142**. The 80-system validation set is roughly 30 systems short of tolerating a single hit.

### 1.2 The frozen ladder's CI values are wrong

`MINOR` — §9.2 outcome-ladder table; `.json` `statistical_plan.outcome_ladder`.

| plan value | correct value at n = 80 | plan value matches |
|---|---|---|
| k = 0 → upper `0.0462` | **0.0458** | n = 79 (0.0464) |
| k = 1 → lower `0.0026` | **0.0022** | n ≈ 70 (0.0025) |
| k = 3 → upper `0.1055` | **0.1045** | n = 79 (0.1058) |
| k ≥ 4 → "lower bound > `0.013`" | **0.0196** at k = 4 | no method reproduces 0.013 |
| §9.4 item 1 → "bounded above by `0.046`" | 0.0458 → 0.046 | correct |

Every ladder value is systematically slightly too large, consistent with n = 79. The
`0.013` figure for the ≥ 4 rung is not reproducible by plain Wilson, continuity-corrected
Wilson, Jeffreys, Agresti–Coull, or Clopper–Pearson (all computed; see §12).

**Consequence**: the verdict is unaffected (0.0458 < 0.05, so `null_credible` still triggers at
0/80), but the frozen table will disagree with the number the code emits, which is exactly the
situation that later gets resolved by "adjusting" one of them.

**Required fix**: replace the three ladder values with 0.0458 / 0.0022 / 0.1045, replace
"lower bound > 0.013" with "lower bound 0.0196 at k = 4", and record the interval function
(`plain Wilson score, z = Φ⁻¹(0.975) = 1.959964, no continuity correction`) so the artifact and
the table are computed by the same definition.

### 1.3 One-sided vs two-sided is unlabeled

`MINOR` — §7.1.

H-C0001-P is a one-sided claim ("upper bound < 0.05") tested with a two-sided 95% interval.
That is a 97.5% one-sided bound — conservative, and therefore acceptable, but it should be
labeled, because the corresponding one-sided 95% Wilson upper at 0/80 is **0.0327** and the
rule-of-three approximation is **0.0375**. A reader comparing 0.046 to a one-sided 95% bound
elsewhere in the campaign will not be comparing like with like.

---

## 2. CRITICAL-1 — The primary endpoint's reduction is orthogonal to the mechanism under test

`CRITICAL` — §7.1 (primary endpoint definition), §7.2 roll-up
(`system_match = component_count_match AND all_i component_match(i)`), §1 (H-C0001-P).

### The defect

E0 is the hypothesis that the string matcher *misses structurally correct candidates*. The
disclosed mechanism (P4) is a **per-component** encoding asymmetry: every GRN family writes its
decay term as `-1 * k * x` (a `neg` node) and the model emits `-k * x` (a signed constant). This
asymmetry applies independently to each component of each candidate.

The primary endpoint reduces by **conjunction over all components of a system**. A dim-3 system
scores a hit only if a single candidate simultaneously matches all three components. The
estimand is therefore the *d-th power* of the phenomenon E0 describes, and the design has no
endpoint at the power of 1 that carries a confirmatory claim (A-S3 is estimation-only by §0.3).

### Quantification

From the disclosed P6 (107/2040 cell-level component matches), the implied per
(cell, candidate, component) rate is q = 1 − (1 − 0.0525)^(1/50) = **0.001077**. Under
within-candidate independence of component matches:

| dim | # systems | P(one candidate matches all d) | P(cell hit) | P(ANY over 12 cells) | E[hits] |
|---|---|---|---|---|---|
| 1 | 20 | 1.077e-03 | 5.245e-02 | 4.761e-01 | **9.52** |
| 2 | 30 | 1.160e-06 | 5.799e-05 | 6.957e-04 | 0.021 |
| 3 | 30 | 1.249e-09 | 6.245e-08 | 7.494e-07 | 0.000 |

Independence predicts ≈ 9.5 hits, i.e. `evaluator_artifact_confirmed`. But P5 observed **0/960**
full-system hits under the same `neg` normalization, **including 0/120 in R01 and 0/120 in R02**.
I verified from `phase2/validation.json` that the corpus is:

| family | R01 | R02 | R03 | R04 | R05 | R06 | R07 | R08 |
|---|---|---|---|---|---|---|---|---|
| dimension | **1** | **1** | 2 | 2 | 2 | 3 | 3 | 3 |
| systems | 10 | 10 | 10 | 10 | 10 | 10 | 10 | 10 |

(20 dim-1, 30 dim-2, 30 dim-3; 170 components total.)

**R01 and R02 are one-dimensional.** For a 1-D system a component match *is* a full-system match
(ODEFormer returns a system of the input trajectory's dimension, so component-count mismatch is
not an available escape). P5's 0/120 in R01 and 0/120 in R02 therefore forces the deduction:

> **None of the 107 component matches lies in a dim-1 system.** They come from the 1,800
> dim ≥ 2 component-cells, at a rate of 107/1800 = **0.0594** there and **0.0000** in dim-1.

Two things follow, and both are fatal to the primary as an instrument for E0:

1. Component matches do not occur at all in the simplest systems — the only stratum where the
   full-system conjunction has any realistic chance of firing.
2. Component matches are so far from independent within a candidate that the conjunction is
   empirically zero. The plan's primary measures the conjunction.

Information content: at a prior P(0 hits) of 0.95 the primary outcome carries **0.286 bits**.

### Consequence for the scientific conclusion

A `null_credible` verdict on this primary will license the sentence "the system-level
semantic-equivalence-in-beam rate is bounded above by 0.046". That sentence will be true and
will say nothing about E0, because the design has no confirmatory endpoint at the resolution at
which E0 operates. The cycle will have spent its inferential apparatus on the one outcome that
was already known (GPU_RUN5's published 0.0, re-confirmed by P5 under a *cruder* matcher) and
will have relegated its only informative Part A measurement to estimation-only status.

The plan is honest that A-S3 must be demoted — that is correct under rule 01 item 9 and must not
be reversed. The fix is not to un-demote A-S3. The fix is to preregister a **new, unseen,
confirmatory endpoint at component resolution**, stratified along the axis that has never been
observed.

### Required fix (CRITICAL, must precede freeze)

Add a co-primary or elevated-secondary confirmatory endpoint whose value has **not** been
observed in any form:

> **A-P2 `component_type_stratified_M3_match_rate`** — the M3 component-level match rate
> stratified by component type: (i) **nontrivial Hill / variable-denominator** components
> (those containing `inv` applied to a variable-containing subtree) versus (ii) **linear-decay**
> components (`neg mul CONST x_i` and constant-affine terms). Reported separately, each with a
> **system-clustered** interval, and with the two strata's difference.

Justification for confirmatory status: neither the plan, the exploratory note, nor GPU_RUN5
reports any component-type breakdown of the 107, so this quantity is genuinely unobserved. It is
also the *decisive* quantity: `research_state.md` §2 records that the exact component count for
nontrivial Hill / variable-denominator components of R03–R08 was **0 in every GPU_RUN5 final
condition**, and if all 107 matches turn out to be linear-decay terms then E0 explains nothing
that matters and the four-way decomposition changes shape. If some are Hill components, E0 is
confirmed at the level that matters and GPU_RUN5's floor claim is invalidated.

**Do not compute the stratification of the 107 from the crude-folder data before freezing this
endpoint.** Preregister first, then measure with the CAS cascade only. Looking first converts the
one remaining unseen quantity in Part A into disclosed prior information and forces a second
demotion.

Secondary fix: also stratify the primary by dimension (20/30/30), reported descriptively. The
pooled 80-system proportion assumes a homogeneous Bernoulli p across a population the campaign's
own data says is strongly heterogeneous (GPU_RUN4: 1-D skeleton-exact 17/92, 2-D 2/112, 3-D 0/40).

### Note: the campaign's own rule H-G3 is not honored

`MINOR` — `hypotheses/C0001_candidates.md` makes a component-stratified secondary
**mandatory** ("rule H-G3") for aggregate/component decoupling. C0001 has no component-type
stratification anywhere. Amendment A-P2 discharges this.

---

## 3. CRITICAL-2 — Family/dimension clustering is not modeled; the target population is unstated

`CRITICAL` — §2.1 ("Family is **not** the inference unit"), §9.1 (system-level proportions row),
§7.1 (Wilson 95%).

### The defect

The plan correctly identifies that cells are not the unit and correctly collapses within-system
dependence via the `ANY` reduction. It then treats the resulting 80 system-level indicators as
80 independent Bernoulli draws. They are not: the 80 systems are **8 families × 10 parameter
variants**, and family is **perfectly confounded with dimension** (verified above). Within a
family, all 10 variants share the same topology, the same operator structure and the same
component count; they differ only in parameter values and in whether a Hill exponent is 2 or 4.

Whether a candidate structurally matches a truth is overwhelmingly a property of the truth's
*structure*, i.e. of the family template. The intra-family correlation of the hit indicator is
therefore plausibly large.

### Quantification

Design effect deff = 1 + (m − 1)·ICC with m = 10; n_eff = 80/deff. Wilson upper bound at 0 hits:

| ICC | deff | n_eff | Wilson upper @ 0 hits | < 0.05? |
|---|---|---|---|---|
| 0.00 | 1.00 | 80.0 | **0.0458** | yes |
| **0.011** | 1.10 | 72.8 | **0.0500** | **boundary** |
| 0.10 | 1.90 | 42.1 | 0.0836 | no |
| 0.20 | 2.80 | 28.6 | 0.1185 | no |
| 0.30 | 3.70 | 21.6 | 0.1509 | no |
| 0.50 | 5.50 | 14.5 | 0.2089 | no |
| 1.00 | 10.00 | 8.0 | 0.3244 | no |

**The preregistered bound survives only for ICC ≤ 0.011.** If the inference unit is the family,
0/8 gives Wilson 95% = **[0, 0.3244]**.

The plan's dismissal — "with 10 systems per family no family-level rate is adequately powered
and none may carry a confirmatory claim" — is true and beside the point. Under-powering the
*stratum-specific* estimates is not a reason to assume ICC = 0 in the *pooled* interval.

Supporting evidence that ICC is not negligible: GPU_RUN5's own rank stability across bundles is
Spearman 0.480 / Kendall 0.389 (`research_state.md` §2), i.e. substantial structure-linked
variability; GPU_RUN4's dimension gradient (1-D 17/92, 2-D 2/112, 3-D 0/40) is a between-family
effect of enormous size, since dimension *is* family here.

### The deeper problem: the estimand's population is never stated

§7.1 gives a proportion and an interval but never says what the interval is an interval *about*.
Two readings, with different answers:

- **Finite-population / conditional reading** — "these 80 systems". Then 0/80 is exactly 0, the
  Wilson interval is meaningless surplus, and no bound on any wider rate is licensed. Under this
  reading the primary's "< 0.05" claim in §1 is not a claim the design can make at all.
- **Superpopulation reading** — "Hill-type GRN systems emitted by the R01–R08 generator". Then
  the interval is the right object but must be family-clustered, and 0/80 gives an upper bound
  between 0.08 and 0.32, not 0.046.

Either way the headline "Wilson 95% upper bound < 0.05" as written is unsupported. This is not a
soft point about conservatism: it is the difference between "at most 5 in 100 systems" and "at
most 1 in 3 family templates".

### Required fix (CRITICAL, must precede freeze)

1. State the target population explicitly in §7.1 and in `primary_endpoint` in the `.json`.
2. If the superpopulation reading is intended, report **two** intervals for the primary:
   (a) the naive Wilson interval over 80 systems, labeled `assumes_family_icc_zero: true`, and
   (b) a **family-clustered** interval over the 8 clusters — cluster bootstrap over families, or
   the 8-cluster Wilson interval as a bounding case, whichever the supervisor prefers, frozen now.
3. Preregister the empirical ICC as a reported quantity (it is estimable from the 80 indicators
   once observed) with the frozen statement: *if ICĈ > 0.011, the "< 0.05" bound is withdrawn and
   the clustered bound is the reported result.* This is a pre-committed conditional, not a
   post-hoc rescue.
4. Amend §1's H-C0001-P statement so that the bound it asserts is the one the design can deliver.

---

## 4. CRITICAL-3 — Part C's fairness verification is empirically vacuous

`CRITICAL` — §8.2 step 1, §5 item 3, `FAILURE_REASONS` addition `EncoderCacheMiss`.

### The defect

§8.2 step 1: *"verify `input_trajectory_checksum` — this is the exact conditioning the model saw.
A checksum mismatch marks the cell `EncoderCacheMiss` and excludes it."* §5 item 3 rests the
whole Part C fairness guarantee on this field.

The field does not mean what the plan says. I read all 960 validation cells:

- **80 distinct `input_trajectory_checksum` values across 80 systems.**
- **0 of 80 systems have more than one distinct value among their 12 cells.**
- Source: `src/gpu_run5/phase8_runtime.py:555` sets it from `input_observation["source_checksum"]`
  — the *pre-corruption source* trajectory, one per system.

Meanwhile the actual conditioning payloads *do* differ: the 12 cells of a system carry **10
distinct** `observations["input"]` payloads.

**Consequence**: the check cannot detect any cell-level mixup — a Part C run that scored every
cell against the wrong corruption, the wrong bundle, or the wrong noise level would pass it
silently. It detects only cross-system mixups. The `EncoderCacheMiss` exclusion rule will never
fire for the reason stated, so §13's "counted and reported" exclusion accounting is also void
for that category.

### Required fix (CRITICAL)

Replace §8.2 step 1's verification with a check on the object actually used:

1. Compute a digest of the exact array passed to `_point_bag` (times + observed_trajectory +
   initial_condition) and record it as a new field `cell_input_payload_sha256`.
2. Additionally assert `noise_sigma`, `subsample_rho`, `bundle_index` and `system_id` parsed from
   the record equal those encoded in `cell_id`, and that `candidate_set_hash` /
   `cache_identity` match the stored values.
3. Retain the `input_trajectory_checksum` comparison but relabel it what it is — a
   **system-identity** check, not a conditioning check — so no downstream reader mistakes it for
   the fairness guarantee.
4. Amend §5 item 3, which currently asserts a guarantee the machinery does not provide.

---

## 5. CRITICAL-4 — The Part C E2/E3 discriminator does not identify model error

`CRITICAL` — §8.3 (`rank_pct_sum`, `below_all_indicator`), §8.3 conjunctive E2/E3 rule, C-S4.

### The defect

The stored candidates were produced with `beam_type = sampling`, `beam_temperature = 0.1`
(§3, decode config of record). Temperature-0.1 sampling draws from p^(1/T) = p^10 renormalized —
a massively sharpened, near-greedy distribution. The 50 candidates are therefore an extreme
**upper-tail, size-biased** sample of the model's sequence distribution, not a characterization
of it.

"Percentile/rank of the GT log-prob within the sampled distribution" is a well-defined
descriptive statistic — the plan is right that it compares the model against itself (C-SAMPLED),
and right that this is budget-matched. What does **not** follow is the interpretation:
*GT below all 50 samples ⇒ model error (E2)*.

### Quantification

Token-level simulation (L = 47 positions matching P3's median GT length, V = 40, fixed
per-position logits, 50 sequences drawn at T = 0.1, model distribution characterized by 200,000
draws at T = 1.0):

| quantity | value |
|---|---|
| model log-prob distribution | mean −110.8, sd 9.0, 5th pct −126.1, 95th pct −96.5 |
| 50 T = 0.1 samples | min −58.5, median −57.8, max −57.2 |
| fraction of the model's own mass below the **worst** of the 50 samples | **1.0000** |
| GT at the model's 50th percentile — below all 50 samples? | yes |
| GT at the model's 90th percentile — below all 50 samples? | yes |
| GT at the model's **99th** percentile — below all 50 samples? | **yes** |

A sequence that the model ranks above 99% of everything it could emit still falls below every
one of 50 T = 0.1 samples. The exact magnitude is model-dependent (this toy assumes positional
independence; a real conditioned autoregressive decoder is *more* peaked, not less), but the
direction is structural and unavoidable at T = 0.1.

**Consequence**: `below_all_indicator` is near-degenerate at 1. The frozen E2 criterion —
`C-S4 ≥ 0.80` with Wilson lower bound > 0.70 — will therefore pass **by construction**,
regardless of whether the GT actually has low probability. Part C, the cycle's only GPU work,
will "support E2" whatever the truth is. That is a false-positive rate near 1 for the E2 verdict.

### The valid instrument is already in the plan, demoted

`MAJOR` — C-S6 versus C-S1/C-S2/C-S3.

The precedented decomposition the plan itself cites — Stahlberg & Byrne, DOI
10.18653/v1/D19-1331 — does **not** rank the reference within a sample. It compares the model
score of the reference against the model score of **the sequence search actually returned**:

- logP(GT) > logP(found output) ⇒ the model preferred the GT and search failed to find it ⇒
  **search error (E3)**.
- logP(GT) < logP(found output) ⇒ the model genuinely prefers the wrong answer ⇒
  **model error (E2)**.

That comparison is well-defined, involves no reference distribution, no temperature distortion,
and no length normalization choice. It is in the plan as **C-S6** — buried as a per-token Holm
secondary, while the invalid rank-in-50 statistic carries the decision.

### Required fix (CRITICAL)

1. Make the E2/E3 discriminator the per-system paired indicator
   **`1[logP_sum(GT) > logP_sum(selected candidate)]`** (and, reported alongside,
   `1[logP_sum(GT) > max_k logP_sum(candidate_k)]`), aggregated over in-support systems with a
   Wilson interval. Freeze the E2/E3 thresholds on *this* statistic.
2. Demote `rank_pct_sum`, `rank_pct_per_token`, `rank_pct_length_matched` and
   `below_all_indicator` to **descriptive**, with the frozen note that a T = 0.1 sample is an
   upper-tail sample and a low rank does not establish model error.
3. Add a preregistered **reference-distribution resolution diagnostic**, analogous to N1–N6:
   report the interquartile range of the 50 candidate log-probs per cell and the GT gap expressed
   in IQR units. Freeze the condition: *if the candidate log-prob IQR is small relative to the
   GT gap (say gap > 5 × IQR) in more than 20% of cells, the reference distribution has no
   resolution and no rank-based statistic may be interpreted.* This is the Part C equivalent of
   the Part A control battery, which Part C currently lacks entirely.

---

## 6. MAJOR findings

### MAJOR-1 — The matcher-defect trigger and N6 compare incommensurable estimands

`MAJOR` — §0.3 item 4, §7.6, §9.2 N6, A-S3 definition in §7.5.

P6 is a **cell-level** component rate: 107/2040, where 2040 = 170 components × 12 cells.
A-S3 is defined as *"per-system fraction of its components **ever** matched, then across 80
systems"* — an **`ANY`-over-12-cells** reduction. These are different quantities, and the
frozen floor `A-S3 ≥ 0.0525` compares one to the other.

Bounds on A-S3 consistent with the same 107 cell-level hits:

| concentration of the 107 hits | distinct hit components | implied per-system component fraction |
|---|---|---|
| each hit component hits in all 12 cells | 107/12 = 8.9 | **0.0525** |
| each hit is a distinct component in one cell | 107 | **0.6294** |

A-S3 can legitimately lie anywhere in **[0.052, 0.629]** while the cell-level rate is exactly
0.0525. The `< 0.0475` trigger therefore cannot fire even if the CAS cascade is up to twelve
times *worse* per cell than the crude token folder. The plan's single quantitative instrument
safeguard is vacuous, and N6 (`A-S3 > 0`) is weaker still.

Compounding: §0.3 item 4 and §7.6 say the floor is **≥ 0.0525**; §9.2 N6 says the condition is
**> 0**. Two different thresholds for the same check in the same document.

**Required fix**: (a) recompute the crude `neg`-folder's value under the *exact same* reduction
as A-S3 and freeze that as the floor — this is a re-reduction of already-disclosed exploratory
data and adds no new unblinding; **or** (b) redefine A-S3 as the cell-level component rate
(directly comparable to 107/2040) with a system-clustered interval. Either way the floor and the
endpoint must be the same estimand. Reconcile N6's `> 0` with §7.6's `≥ 0.0525` to one number.

### MAJOR-2 — A-S3's estimator over-weights the easiest stratum by 3.78×

`MAJOR` — §7.5 A-S3, §9.1 per-system-means row.

A-S3 is an unweighted mean over 80 systems of "fraction of that system's components matched".
Component counts per system are 1 (dim-1), 2 (dim-2), 3 (dim-3), and dimension is perfectly
confounded with family. So each component receives weight 1/d:

| family | dim | # comps | % of all comps | A-S3 weight | % of A-S3 weight | distortion |
|---|---|---|---|---|---|---|
| R01 | 1 | 10 | 5.9% | 10.000 | 22.2% | **3.78×** |
| R02 | 1 | 10 | 5.9% | 10.000 | 22.2% | **3.78×** |
| R03–R05 | 2 | 20 ea | 11.8% ea | 5.000 ea | 11.1% ea | 0.94× |
| R06–R08 | 3 | 30 ea | 17.6% ea | 3.333 ea | 7.4% ea | **0.42×** |

The 1-D families (R01/R02 — the shortest truths, median 27 and 20 tokens) hold 11.8% of the
components but **44.4%** of A-S3's weight. The 3-D families (R06–R08 — median 62/74/53 tokens)
hold 52.9% of the components but **22.2%** of the weight.

Given GPU_RUN4's dimension gradient, A-S3 is an **upward-biased** estimate of the
component-level rate. That bias runs in the same direction as MAJOR-1's estimand mismatch, so the
two errors compound: the matcher-defect trigger becomes even less likely to fire.

Note the interaction with §2's deduction: the 1-D families contributed **zero** of the 107, so
44.4% of A-S3's weight sits on systems where the phenomenon is known to be absent.

**Required fix**: report A-S3 in two forms — (a) component-weighted (the direct analogue of
107/2040) and (b) dimension-stratified. State which is the floor comparator. Do not report the
unweighted per-system mean as "the component-level rate".

### MAJOR-3 — A-S3's interval method is wrong, and the promised estimator does not exist

`MAJOR` — §0.3 item 2 ("a clustered interval"), §7.5 A-S3 (`student_t_ci, dof 79`),
§9.1 per-system-means row.

§0.3 item 2 promises a *clustered* interval. §7.5 and §9.1 both specify
`src/gpu_run4/aggregation.py:22 student_t_ci`. I read that function: it is a plain symmetric
Student-t interval on per-observation values with `ddof=1`, no clustering, no bounding to [0, 1].
**The repository has no clustered-interval utility**, so the implementer will silently satisfy
the letter of §9.1 and violate §0.3.

Coverage of `student_t_ci` for A-S3, simulated 20,000× on the true corpus shape
(20 systems × 1 comp, 30 × 2, 30 × 3):

| true per-component rate | system ICC | t-CI coverage | P(lower limit < 0) | mean width |
|---|---|---|---|---|
| 0.05 | 0.0 | **0.913** | **0.054** | 0.070 |
| 0.05 | 0.3 | **0.909** | **0.167** | 0.078 |
| 0.10 | 0.0 | 0.934 | 0.000 | 0.099 |
| 0.10 | 0.3 | 0.930 | 0.001 | 0.110 |
| 0.20 | 0.0 | 0.943 | 0.000 | 0.133 |
| 0.40 | 0.0 | 0.949 | 0.000 | 0.163 |

At the rate that actually matters (≈ 0.05) coverage is 0.909–0.913, not 0.95, and the interval's
lower limit is **negative** 5–17% of the time — inadmissible for a proportion, and exactly the
kind of artifact that gets quietly clipped to zero at reporting time.

**Required fix**: specify the estimator by name. Either a cluster bootstrap over systems
(and, per CRITICAL-2, over families) or a logit-scale interval with a system-clustered sandwich
variance. Freeze the number of bootstrap resamples and the RNG seed. Add the utility to the
Part A implementation ticket so it is not silently replaced by `student_t_ci`.

### MAJOR-4 — The Holm multiplicity plan is not executable as written

`MAJOR` — §9.3, `.json` `statistical_plan.multiplicity`.

Verified problems, in order of severity:

1. **No p-values exist.** Holm–Bonferroni is a procedure over p-values from hypothesis tests.
   §9.3 declares "Holm–Bonferroni within family at α = 0.05" for S1/S2/S3, but the plan never
   states a null hypothesis or a test statistic for **any** secondary endpoint. There is nothing
   to Holm-order. The instruction is not implementable.
2. **S2 corrects a deterministic census.** The plan itself says (§8.1, "Statistical honesty")
   that Part B's values are *"deterministic functions of a fixed corpus — there is no measurement
   noise"*. Holm-correcting B-S1 and B-S2 is incoherent with the plan's own correct
   characterization of them.
3. **S1 corrects no real multiplicity.** By the frozen monotonicity M0 ⊆ M1 ⊆ M2 ⊆ M3, A-S1
   (the M2 rate) is *nested inside* the primary: an M2 hit implies an M3 hit. A-S2 (M3 MEAN) and
   A-S4 (M3 per-family) are deterministic re-reductions of the *same* M3 indicator set as the
   primary. The three S1 members and the primary are functions of one underlying observation;
   the correction is cargo-cult rather than harmful, but it creates a false impression of error
   control.
4. **S1's family size is ambiguous.** The table reads "A-S1, A-S2, A-S4 (8 family rates)". Is
   m = 3 or m = 10? Holm's outcome depends on m. Undetermined.
5. **S3 is doubly specified and self-contradictory.** C-S1/C-S2/C-S3 carry decision thresholds
   (upper bound < 0.05; lower bound ≥ 0.25) and C-S4 carries another (≥ 0.80, Wilson lower
   > 0.70), all at *nominal* 95%. The conjunctive E2/E3 rule in §8.3 uses those uncorrected
   bounds. Yet §9.3 places all six in a Holm family. Which alpha governs the E2/E3 verdict is
   undefined.

**Families are non-overlapping as sets of ids** — that part is correct — and no endpoint appears
in two families. The primary is genuinely singular and unadjusted, which is right.

**Required fix**: drop Holm. Declare every secondary **estimation-only** and report simultaneous
coverage explicitly: Bonferroni-widened intervals at α/m within each family (m stated as a
number), or plainly labeled nominal 95% intervals with the frozen sentence "these are not
multiplicity-controlled and no secondary supports a confirmatory claim". Then state, separately
and unambiguously, the alpha and the exact interval bound that governs each *decision* rule
(the E2/E3 conjunction, the Gate thresholds, the control-battery pass marks). Decision rules and
estimation intervals must not be the same objects.

### MAJOR-5 — Hidden multiplicity of M0–M3: the plan gets this right

`OK`, recorded here because the review brief asks.

Four matchers are run on the same data and M3 is preregistered as primary. This is **not**
selection of the most favorable analysis, for a reason the plan states correctly and I verify:
M3 is the *most permissive* level, so under the frozen monotonicity M0 ⊆ M1 ⊆ M2 ⊆ M3 the M3
indicator dominates all others. If M3 returns 0, every level returns 0. The primary is therefore
a **maximum** over the cascade, and the multiplicity of four levels is fully absorbed with no
inflation of the type-I error for the null direction. Choosing the level that makes the null
maximally falsifiable is the adversarially correct choice for a null-shaped hypothesis, and
choosing a stricter level would have been the illegitimate move.

One caveat worth freezing: this argument depends on the monotonicity actually holding. §7.3's
monotonicity self-check is what licenses it, and the plan should say so explicitly — the check
is not merely an internal consistency audit, it is the precondition for the primary's
multiplicity argument.

### MAJOR-6 — §9.4 item 4 contradicts the primary hypothesis

`MAJOR` — §9.4 item 4 versus §1 and §7.1; §17 (Stage 9 instructed to enforce item 4).

§9.4 item 4: *"Any equivalence claim requires a preregistered equivalence margin and a
two-one-sided-test procedure. **None is preregistered in C0001. Therefore no equivalence claim
may be made in C0001 at all.** This sentence is the operative constraint; Stage 9 must enforce
it."*

But H-C0001-P **is** a one-sided equivalence-shaped claim, and it **does** have a preregistered
margin. §1: *"the per-system semantic-equivalence-in-beam rate ... remains at or near zero:
Wilson 95% upper bound < 0.05."* The margin is 0.05; the procedure is a confidence-bound
inclusion test, which is the standard one-sided equivalent of TOST for a bounded-rate claim.
This is legitimate — it is precisely *not* the rule-01-item-8 error, because it asserts a bound
rather than inferring sameness from non-significance.

The contradiction is operative, not cosmetic: §17 instructs Stage 9 to enforce item 4, which
would oblige the independent reviewer to strike the primary conclusion as a forbidden
equivalence claim.

**Required fix**: rewrite item 4 as: *"The primary is a preregistered one-sided bound with
margin 0.05 on the system-level rate; a `null_credible` verdict licenses exactly the bounded-rate
sentence in item 1 and nothing beyond it. No **other** equivalence claim may be made — in
particular no claim of equivalence between matcher levels, between GT encodings, or between the
GT and the sampled candidates, for which no margin is preregistered."*

### MAJOR-7 — Does `null_credible` smuggle in an equivalence claim? Mostly no

`OK` with one `MINOR` caveat — §9.2 ladder, §9.4 items 1–3, §10.3.

I tried to break this and could not. The frozen wording in §9.4 items 1–3 is correct and
unusually explicit: a 0/80 observation licenses only the bounded-rate sentence and specifically
does **not** license "the rate is zero", "the matcher makes no difference", "M0 and M3 are
equivalent", or "the two matchers agree". Item 2 correctly refuses "GT-affine and GT-mult are
equally probable" from a C-S5 interval containing 0. Item 3 correctly refuses "the truth is in
the generator's support" from a Part B rate of 0. These are the four sentences a lazy report
would actually write, and the plan pre-emptively forbids all four. That is genuine rule-01-item-8
compliance, not a fig leaf.

The `MINOR` caveat is the **verdict label itself**. "`null_credible`" and "H-C0001-P
**supported**" will be quoted downstream in `hypothesis_tree.md`, cycle reports and syntheses
stripped of §9.4's constraints. Labels travel; caveats do not.

**Required fix (MINOR)**: rename the rung to something self-limiting — `rate_bounded_below_0.05`
or `no_system_level_hits_bound_0.046` — so the label carries its own scope. And require that
every artifact carrying the verdict also carries the §9.4 item 1 sentence verbatim in a
machine-readable field, in the same way §0.3 item 3 already requires
`prior_information_disclosed` alongside A-S3. The mechanism is already in the plan; apply it here
too.

### MAJOR-8 — The outcome ladder has no error control

`MAJOR` — §9.2 outcome ladder, §1 falsifier.

The three rungs (0 → `null_credible`; 1–3 → `weak_positive`; ≥ 4 →
`evaluator_artifact_confirmed`) have no pre-specified type-I or type-II budget. Computed
operating characteristics under a homogeneous binomial (which CRITICAL-2 shows is already
optimistic):

| true rate p | P(K = 0) → `null_credible` | P(1 ≤ K ≤ 3) → `weak_positive` | P(K ≥ 4) → `artifact_confirmed` |
|---|---|---|---|
| 0.000 | 1.0000 | 0.0000 | 0.0000 |
| 0.005 | 0.6696 | 0.3297 | **0.0007** |
| 0.010 | 0.4475 | 0.5438 | **0.0087** |
| 0.0125 | 0.3656 | 0.6162 | **0.0182** |
| 0.020 | **0.1986** | 0.7245 | **0.0769** |
| 0.030 | **0.0874** | 0.6933 | **0.2193** |
| 0.050 | 0.0165 | 0.4119 | 0.5716 |

Two facts the plan does not state:

- **False-positive rate of the `≥ 4` rung.** It is 7.7% at a true rate of 0.02 and 21.9% at 0.03
  — both well inside the range the plan's own H-C0001-P treats as "essentially zero". So the
  `evaluator_artifact_confirmed` rung, which per §10.3 **INVALIDATES a published campaign
  headline claim**, fires roughly one time in five when the true rate is 3%. The replication gate
  (§15) is the mitigation and it is mandatory for that rung, which is the right call — but the
  ladder should state the rate rather than leave the reader to assume the rung is conservative.
- **The `null_credible` rung is not conservative either.** It fires with probability 0.199 when
  the true rate is 0.02 and 0.087 when it is 0.03. A `null_credible` verdict is compatible with a
  true rate above the plan's own margin roughly 9–20% of the time. This is the honest content of
  §9.2's "power limitation" paragraph, which correctly says the design "cannot certify ≤ 5% in
  the presence of even one hit" but does not give the complementary error rate.

**Is a three-rung ladder a defensible substitute for a hypothesis test?** Yes, as a *reporting*
device — it is better than a bare p-value here, because it makes the three qualitatively
different consequences (survive / revise / invalidate) explicit in advance. No, as an *inferential*
device, because without stated error rates the rungs read as if they were calibrated and they are
not.

**Minimal fix**: append the two operating-characteristic tables above to §9.2 verbatim, and add
the frozen sentence: *"the `≥ 4` rung has a 7.7% / 21.9% probability of firing when the true rate
is 0.02 / 0.03; the `null_credible` rung has a 19.9% / 8.7% probability of firing at those same
rates; both are reasons the replication gate is mandatory for the upper rung and the bound
(not the point estimate) is the reported result for the lower."* No cutpoint needs to move — 0, 1
and 4 are as defensible as any other choice at this n. What is missing is the disclosure, not a
different threshold.

Also `MINOR`: §1's falsifier (≥ 4) and §10.3's "unsupported" criterion (≥ 1) use different
thresholds. That is coherent (unsupported ≠ refuted) but nowhere stated; add one sentence.

### MAJOR-9 — Part C's asymmetric estimand biases every statistic toward E2

`MAJOR` — §8.2 step 3, §5 item 3; the Stage-1 caveat that flagged this and was not carried into
the design.

Each candidate is scored as the **one** token sequence the model actually emitted — for it, the
single-sequence log-prob is the correct quantity. The GT is scored as **one** of many equivalent
encodings (§8.2 scores GT-mult and, when constructible, GT-affine — two of them). But
logP(one encoding) is a **lower bound** on the probability the model assigns to the truth *as a
function*, and the plan's own PC2c/PC2d controls exist precisely because `add` and `mul` operand
order is a free choice.

Magnitude, from the truth token census in the exploratory note (per validation cell):
mul 4920/960 = 5.125 nodes, add 4080/960 = 4.250 nodes → **9.375 commutable binary nodes per
system truth**.

| fraction of binary nodes order-swappable | equivalent encodings | understated log-prob | at Lg = 47 |
|---|---|---|---|
| 50% | ~26 | 3.25 nats | 0.069 nats/token |
| 75% | ~131 | 4.87 nats | 0.104 nats/token |
| 100% | ~664 | 6.50 nats | 0.138 nats/token |

Against C-S6's threshold of 0.5 nats/token, the bias is 14–28% of the decision threshold.
Not fatal alone; material when combined with CRITICAL-4.

§5 item 3's claim — *"There is no 'GT gets a special path' asymmetry"* — is **true at the code
level and false at the estimand level**. The plan's §5 audit proves the forward pass is shared;
it does not and cannot address the fact that the two sides are estimating different things.

**Required fix**: state the asymmetry in §5 and §8.3 as a preregistered directional bias toward
E2, with the magnitude above. Cheap partial mitigation, already available: enumerate the
commutation orbit of the GT encoding under `add`/`mul` operand swaps up to a frozen cap (say 32
orderings, deterministic traversal, reusing the PC2c/PC2d machinery), score all of them, and
report `logsumexp` over the orbit alongside the single-encoding value. That converts a lower
bound into a tighter lower bound at negligible GPU cost, since the encoder output is already
cached per cell.

### MAJOR-10 — The conjunctive triple-report is under-powered and under-defined

`MAJOR` — §8.3 conjunctive E2/E3 rule, C-S1/C-S2/C-S3.

Three separate defects.

**(a) It will return `undecidable` by construction.** P3: GT median 47 tokens, max 80.
ODEFormer candidates are compact (GPU_RUN4 complexity median 17). Whenever the GT is
substantially longer, the *summed* statistic ranks it last while the *per-token* statistic can
rank it anywhere:

| candidate length | GT/cand mean per-token logprob | GT lower by sum? | GT lower per-token? |
|---|---|---|---|
| 15 | −0.30 / −0.30 | **yes** | no |
| 25 | −0.30 / −0.30 | **yes** | no |
| 40 | −0.30 / −0.30 | **yes** | no |
| 40 | −0.25 / −0.30 | no | no |
| 47 | −0.30 / −0.30 | no | no |

C-S1 ≈ 0 with C-S2 ≫ 0 is the *expected* regime, and it triggers the "any disagreement in
direction ⇒ `undecidable`" clause. The clause is a good instinct — it does prevent choosing the
tidier normalization — but as written it converts the expected outcome into a non-result, and
Part C is the cycle's only GPU spend.

**(b) "Disagreement in direction" is undefined.** Direction relative to what? No reference value
is given. Three means in [0, 1] have no intrinsic direction. As written the clause is not
adjudicable.

**(c) The rule has an unhandled dead zone.** E2 needs all three upper bounds < 0.05; E3 needs all
three lower bounds ≥ 0.25. If all three agree and land in between, neither branch fires and the
rule specifies nothing (`undecidable` is reserved for disagreement). Minimum detectable effects
at n = 30, dof 29, t = 2.0452:

| sd | se | E2 needs mean < | E3 needs mean > | dead zone width |
|---|---|---|---|---|
| 0.05 | 0.0091 | 0.0313 | 0.2687 | 0.237 |
| 0.10 | 0.0183 | 0.0127 | 0.2873 | 0.275 |
| 0.15 | 0.0274 | **−0.0060** | 0.3060 | 0.312 |
| 0.25 | 0.0456 | **−0.0434** | 0.3434 | 0.387 |

**At sd ≥ 0.134 the E2 condition is unreachable at any non-negative mean.** With 30 systems the
design cannot satisfy its own E2 criterion unless the per-system rank statistic is almost
noiseless. Combined with (a), Part C's most likely outcomes are `undecidable` or a
by-construction E2 (via C-S4, CRITICAL-4).

**Is n ≥ 30 adequate?** For establishing "essentially zero" (E2's upper bound at low variance),
yes. For E3, no: E3 requires a mean rank above 0.29–0.34, a large effect. For the paired
Stahlberg–Byrne indicator recommended in §5 above, n = 30 gives a Wilson interval of width
≈ 0.2–0.3 in the middle of the range — adequate for a coarse partition, not for a rate estimate.
The plan's own downgrade-to-exploratory rule at n < 30 is the right shape; the threshold should
be justified against the statistic that actually carries the verdict, which is currently the
wrong one.

**Required fix**: with the CRITICAL-4 fix in place (paired indicator as discriminator), demote
the triple report to a descriptive robustness display, define "disagreement" as a stated sign
test on a stated reference value, and pre-specify the dead-zone outcome explicitly as
`neither_E2_nor_E3_supported` — a real, reportable result, distinct from `undecidable`
(instrument failure).

### MAJOR-11 — Length normalization: only one of the three variants is a probability comparison, and it is not the one the brief suspects

`MAJOR` — §8.3 length-normalization policy.

The review brief asks whether summing log-probs over different lengths "compares
different-dimensional objects". It does not, and I will not endorse that framing. An
autoregressive decoder defines a normalized distribution over the space of *variable-length*
token sequences (terminated by EOS). P(seq A) and P(seq B) are probabilities of two events in one
sample space, and comparing them is entirely valid regardless of length. **`rank_pct_sum` is the
only one of the three variants that is a valid probability comparison.**

The two "robustness" variants are the invalid ones:

- **`rank_pct_per_token`** — mean per-token log-prob is not the log-probability of anything. It is
  a length-normalized *score* (standard in MT decoding, where it is a heuristic, not an
  estimator). It cannot support any claim about which sequence the model assigns more
  probability, and therefore cannot support an E2 or E3 verdict.
- **`rank_pct_length_matched`** — summed log-prob restricted to candidates within ±20% of the GT
  length is a valid probability comparison on a **selected sub-population**. Length is strongly
  correlated with structural complexity, so the candidates surviving a ±20% filter around a
  47-token GT are the structurally most elaborate ones — plausibly the most Hill-like, i.e. the
  ones whose match status is most informative. The filter induces selection on a variable
  correlated with the outcome. The `< 5 candidates ⇒ LengthMatchUnavailable` rule also makes the
  analyzed set outcome-dependent.

So the conjunctive rule gives two statistics that cannot bear the interpretation **veto power
over the one that can**. That is the reverse of what a robustness requirement should do.

The genuine problem with `rank_pct_sum` is not validity but **confounding**: it cannot separate
"the GT is improbable because it is 47 tokens long" from "the GT is improbable because the model
dislikes its structure". Per-token normalization is the wrong handle for that, because it
discards the probability interpretation to fix a confound. The right handles are:

1. The **paired Stahlberg–Byrne comparison** (CRITICAL-4 fix), which is length-agnostic because
   it compares two specific sequences under one model, and where the length difference is part of
   what is being asked about, not a nuisance.
2. The **per-position** view. §8.2's new scoring function already returns `per_token_logprobs`.
   Report the distribution of the GT's per-position log-prob and, better, the GT token's **rank**
   in the model's predicted distribution at each position. That localizes where the probability
   is lost — a specific operator, a mantissa token, the `|` component separator — and is immune to
   the length confound entirely. This is a strictly stronger diagnostic than any of the three
   preregistered variants and costs nothing extra: the forward pass is already being run and the
   per-token log-probs are already being stored.

**Required fix**: designate `rank_pct_sum` the only rank statistic with an interpretation;
relabel `rank_pct_per_token` and `rank_pct_length_matched` `descriptive` with the frozen note
that neither is a probability comparison; add the per-position GT-token-rank profile as a
preregistered descriptive endpoint (it needs no new compute).

### MAJOR-12 — The within-system dependence structure is misdescribed

`MAJOR` — §2.1 (12 cells = 4 corruptions × 3 bundles; "3 bundles" as seed replicates),
§14 deviation 4.

I read all 960 validation cells to check the nesting the review brief asks about. Findings:

1. **One initial condition and one source trajectory per system.** `input_trajectory_checksum`
   (= `source_checksum`) takes exactly **80 distinct values over 80 systems**, constant across
   each system's 12 cells. All 12 cells are corruptions of a single solved ODE from a single IC.
2. **The three clean cells are byte-identical across bundles.** For all **80/80** systems, the
   `(noise_sigma = 0, subsample_rho = 0)` cells at `bundle_index` 0, 1, 2 have identical
   `times`, `observed_trajectory` and `initial_condition`. They differ **only** in the decode
   seed (e.g. R01 `d101_000`: 873793043 vs 1303197227).
3. **12 cells → 10 distinct input payloads**, for every one of the 80 systems.

So the structure is not "4 corruptions × 3 independent bundles". It is: one trajectory per
system; 10 distinct conditionings derived from it; 12 distinct decode seeds. Consequences:

- The `ANY`-over-12 reduction has fewer genuinely distinct chances than 12, and for the clean
  condition the three "bundles" are pure decode-RNG replicates.
- **The primary's estimand is conditional on a single initial condition per system.** The plan
  never says this. GPU_RUN5's own P6 result (multi-IC selection, mean clustered ΔNRMSE −0.20278,
  paired CI [−0.32323, −0.08233]) establishes that IC materially affects outcomes on this very
  corpus, so the restriction is not innocuous. A 0/80 result bounds the rate for these systems
  *at these ICs*, not for these systems.

The `ANY` reduction is nonetheless the **right** choice, and the plan's reasoning is correct:
`ANY` is the generation-coverage estimand (rule 03), and relative to a single cell it inflates
the hit probability — up to 12× under independence, which is the **anti-conservative direction
for the null** and therefore the adversarially correct choice for a null-shaped primary:

| per-cell q | ANY over 12 (indep) | ANY over 3 (indep) | ANY (perfect corr) |
|---|---|---|---|
| 0.002 | 0.0237 | 0.0060 | 0.0020 |
| 0.005 | 0.0584 | 0.0149 | 0.0050 |
| 0.010 | 0.1136 | 0.0297 | 0.0100 |
| 0.020 | 0.2153 | 0.0588 | 0.0200 |

The multiplicity of the 12-cell union is thus **not** an uncontrolled type-I inflation for the
null claim; it is deliberate and correctly directed. But two things must be said that the plan
does not say: (i) the resulting rate is **not comparable** to GPU_RUN5's per-cell 0/960 except at
exactly zero, so no report may present them as the same quantity improved; (ii) if the primary
ever returns a non-zero value, the union-of-12 structure must be reported alongside it, because
1/80 systems is 1/960 cells and the two framings differ by an order of magnitude in apparent size.

**Required fix**: correct §2.1's description of the cell grid to match the artifacts (single IC
and source trajectory per system; 10 distinct payloads; clean cells identical across bundles).
Add to §7.1 the scope sentence: *"conditional on the one initial condition per system stored in
GPU_RUN5 phase 3."* Add to §9.4 the constraint that the system-level `ANY` rate may not be
compared to GPU_RUN5's per-cell rate except at zero.

### MAJOR-13 — The reduced design discards the wrong dimension

`MAJOR` — §14 deviation 4 and 5 ("stratified subsample of 4 of the 12 cells per system,
`bundle_index == 0`, all 4 corruptions").

Given MAJOR-12's structure, `bundle_index == 0` with all 4 corruptions selects the **4 most
mutually dependent** cells — four corruptions of one trajectory realization within one bundle —
and discards all between-bundle variation. GPU_RUN5 measured between-bundle rank stability at
Spearman 0.480 / Kendall 0.389, i.e. bundle is the dimension with the *most* measured
variability. The label "stratified" is a misnomer: the subsample is not stratified, it is a
single level of one factor.

**Required fix**: make the reduced design span all three bundles — e.g. 6 cells as
{b0, b1, b2} × {(0,0), (0.05, 0.5)}, or a 4-cell balanced assignment covering all 3 bundles and
all 4 corruptions. This preserves the between-bundle variance at the same compute, and it keeps
the `ANY` union across genuinely distinct conditionings rather than across four corruptions of
one draw. Apply the same change to deviation 5 (Part C).

---

## 7. MINOR findings

| id | location | finding |
|---|---|---|
| m1 | §9.2 ladder | CI values wrong (see §1.2). Fix to 0.0458 / 0.0022 / 0.1045 / 0.0196 and record the interval function. |
| m2 | §9.4 item 1 vs §9.2 | "0.046" vs "0.0462" for the same bound. Pick one (0.046 is the correct rounding of 0.0458). |
| m3 | §7.1 | Two-sided 95% interval used for a one-sided claim; label it as the 97.5% one-sided bound it is (one-sided 95% = 0.0327). |
| m4 | §1 vs §10.3 | Falsifier is ≥ 4; "unsupported" is ≥ 1. Coherent but unstated; add one sentence distinguishing unsupported from refuted. |
| m5 | `C0001_candidates.md` vs §2.1 | The hypothesis definition specifies "clustered by family R01–R08 for inference (8 clusters); families are the replicate unit for any cross-family claim". §2.1 reverses this to "family is **not** the inference unit" without addressing the change. Given CRITICAL-2, the candidates file was right. Justify the reversal in writing or adopt the original. |
| m6 | §9.3 / §8.1 | Wilson intervals on a deterministic census (B-S1/B-S2) are correctly explained by the `interval_interpretation` field but incorrectly placed in a Holm family (subsumed by MAJOR-4). |
| m7 | §7.5 A-S4 | 8 per-family rates at n = 10 each: Wilson width at 0/10 is [0, 0.278]. Correctly labeled underpowered and non-confirmatory. No fix needed — recorded so the descriptive table is not later read as evidence of family homogeneity, which it cannot establish. |
| m8 | §9.1 | `student_t_ci` produces symmetric unbounded intervals; A-S2, A-S3 and C-S1..C-S3 are all bounded in [0, 1] and will be near a boundary. Require reporting of the raw limits (not silently clipped) plus a bounded alternative. |
| m9 | §12.1 | The statistical review is listed as a Stage 8 artifact; §17 requires it at Stage 3, before the full experiment. This file is the Stage 3 review. Add a second row so the Stage 8 post-analysis review does not overwrite it. |

---

## 8. What the plan gets right

Stated explicitly so the supervisor can separate the above from generic critique. These are not
courtesies; each is a place where the plan avoids an error I specifically looked for.

1. **The statistical unit is correct, and the reason given is correct.** §2.1: cells are not the
   unit because they share a ground truth; treating them as independent would inflate n by 12×.
   The frozen within-system-then-across-systems aggregation order is the right two-stage cluster
   estimator.
2. **The `ANY` reduction correctly collapses within-system dependence.** For the primary, this
   makes within-system correlation irrelevant by construction — a genuinely clean solution to the
   nesting problem, and it is the anti-conservative direction for a null-shaped claim (§6,
   MAJOR-12 table). Many designs get this exactly backwards.
3. **A-S2's two-stage estimator is valid.** A Student-t interval across 80 per-system means is
   correct regardless of the within-system dependence structure, which is absorbed into the
   between-system variance. I checked for the common error of pooling 960 cells; the plan does not
   make it.
4. **§9.1's degenerate-paired-test warning is sharp and correct.** Recognizing in advance that
   the M3 − M0 paired difference is Bernoulli rather than t because M0 ≡ 0, and refusing to run
   the t-test on it, is a specific error caught before it happened. I verified the reasoning holds.
5. **PC3a/PC3b — the specificity controls — are the single best addition to the design.** A
   null-shaped primary is destroyed by an over-permissive matcher exactly as easily as by an
   under-permissive one, and the plan is right that only a negative control detects that. Adding
   them was not in the brief.
6. **The M3-as-primary argument is legitimate, not analysis shopping** (MAJOR-5). Choosing the
   most permissive matcher maximizes the null's falsifiability and, under monotonicity, absorbs
   the four-level multiplicity entirely.
7. **The prior-information ledger (§0) is exemplary.** Eleven disclosed quantities with sources
   and consequences, the machine-readable `prior_information_disclosed` field required on every
   artifact carrying A-S3, and the requirement that §0 be reproduced verbatim in the Stage-11
   report. This is materially better than the field norm.
8. **§0.2's correction of record is right and load-bearing.** The `pow2` → `pow(X,2)`
   canonicalization detection artifact is real, the counts are stated, and the methodological
   lesson ("never test for an operator by searching for its surface token in a canonicalized
   string") is correct and generalizes.
9. **The demotion of A-S3 to estimation-only is the correct response to having seen it.** Do not
   reverse this under any of my findings above; CRITICAL-1's fix adds an unseen endpoint rather
   than reinstating a seen one.
10. **§9.4 items 1–3 are correct rule-01-item-8 compliance** (MAJOR-7). The four sentences a
    lazy report would write are each pre-emptively forbidden by name.
11. **Rule 03's generation / oracle / selected distinction is respected**, not collapsed: `ANY` is
    labeled as the coverage estimand, A-S6 reports oracle versus selected candidate per level
    under the frozen selection rule, and A-S5 gives the cascade increment table. §7.7 correctly
    forbids any match claim from `reconstruction_r2` / `generalization_r2` / NRMSE and carries
    them as covariates only. Complexity, validity, failure reason, variable mapping, variable
    recovery, structural distance and singularity diagnostics are all preserved per the contract.
12. **Part B's `interval_interpretation: "generator_sampling_not_measurement_error"` field** is an
    unusually careful distinction — the plan correctly identifies that a Wilson interval on a
    deterministic census describes the *generator's* sampling variability, not estimation
    uncertainty. Most analyses would report the interval without noticing.
13. **Part B's one-sidedness is correctly preregistered.** `U_affine` is a minimum over a bounded
    rewrite set, hence an upper bound on the true minimal unary count, so `out_of_support` is
    explicitly "out of support under the preregistered rewrite set". The refusal to hand-construct
    affine encodings (§14 item 3) protects reproducibility at the cost of a conservative bias, and
    the plan states which direction the bias runs.
14. **Denominators are usable candidates, never a hardcoded 50** (P10, §7.7), and invalid/failed
    candidates are retained rather than dropped (rule 01 item 5). The 13-candidate shortfall is
    carried forward explicitly.
15. **§14 item 1's timeout policy pre-commits to the conservative direction** (timed-out triples
    counted as non-matches, with a labeled sensitivity analysis the other way, and `undecidable`
    if the two disagree on the rung). Refusing to raise `SYMPY_OP_TIMEOUT_SEC` mid-cycle is
    correct.
16. **The re-encoding round-trip audit and the `sum/n == −mean_CE` regression test** are the right
    instrument checks for Part C's one genuinely new code path, with pre-stated tolerances and a
    pre-stated `undecidable` consequence.
17. **The null-credibility ladder N1–N5 is the right idea**, and the principle that a null is
    inadmissible without a passing control battery is correct. My objection is confined to N6
    (MAJOR-1) and to the absence of any equivalent battery for Part C (CRITICAL-4).
18. **§16's rule-04 compliance is clean.** No layer estimand is measured, nothing is averaged into
    a ranking, and A-S8 is explicitly a statement of a testable consequence rather than a
    measurement.

---

## 9. Answer to the specific question about N6

`MAJOR` — resolved in MAJOR-1 above; stated separately because the brief asks whether N6
smuggles the seen figure back into an inferential role.

**Verdict: N6 is legitimate in kind but vacuous in practice, and its quantitative sibling in
§7.6 is mis-specified.**

- **Legitimate in kind.** Requiring an assay to return a signal on the actual specimen is a
  standard positive control, and it is not the same thing as testing a hypothesis about that
  signal. N6 gates *admissibility of the instrument*, not the primary's value, and the primary
  remains system-level and unobserved. The plan's handling — system-level primary, A-S3 demoted
  to estimation, mandatory disclosure field, Stage-9 instruction to flag discovery-framing — is a
  sound response to the disclosure problem.
- **Vacuous in practice.** A CAS cascade strictly more permissive than a hand-written token
  folder must find at least the 107 cell-level matches the folder found. So `A-S3 > 0` will pass
  by construction and provides essentially zero instrument assurance beyond what PC2a–d already
  provide with *synthetic* controls that do not touch the endpoint data.
- **Mis-specified where it has teeth.** The quantitative version (§0.3 item 4, §7.6:
  `A-S3 ≥ 0.0525`) compares an `ANY`-over-12-cells reduction against a cell-level rate — a
  quantity whose admissible range is [0.052, 0.629] for the very same 107 matches (MAJOR-1) — and
  is further biased upward by A-S3's 3.78× over-weighting of the 1-D families (MAJOR-2). The
  matcher-defect protocol therefore cannot fire even for a badly broken cascade.
- **One asymmetry worth pre-stating.** N6 makes the primary's `null_credible` verdict
  *conditional* on a positive finding in a correlated secondary measured on the same data. If the
  cascade finds nothing at all — the strongest possible null — N6 fails and the verdict is
  `undecidable` rather than `null_credible`. That is defensible given P6, but it is a structural
  asymmetry in the ladder's error rates and it should be stated rather than left implicit.

**Required fix**: keep N6 as a declared *instrument sanity floor* with the frozen note that it is
expected to pass by construction and therefore carries little assurance; put the real assurance
on PC2a–d, which are synthetic and independent of the endpoint data; and repair the estimand
mismatch per MAJOR-1 so the quantitative floor is comparable to what it is compared against.

---

## 10. Findings by severity

| id | severity | location | one-line defect |
|---|---|---|---|
| C1 | **CRITICAL** | §7.1, §7.2 roll-up, §1 | Primary's full-system conjunction is orthogonal to E0's per-component mechanism; power ≈ 0 against the live alternative |
| C2 | **CRITICAL** | §2.1, §9.1, §7.1 | Family/dimension clustering unmodeled; Wilson bound valid only at ICC ≤ 0.011; target population unstated |
| C3 | **CRITICAL** | §8.2 step 1, §5 item 3 | `input_trajectory_checksum` is constant across a system's 12 cells; the Part C fairness check is vacuous |
| C4 | **CRITICAL** | §8.3, C-S4 | Rank within 50 T=0.1 samples does not identify model error; the E2 branch passes by construction |
| M1 | MAJOR | §0.3 item 4, §7.6, §9.2 N6 | Defect trigger compares an `ANY`-reduced rate to a cell-level rate; cannot fire; two different thresholds stated |
| M2 | MAJOR | §7.5 A-S3 | Unweighted per-system fractions over-weight 1-D families 3.78×, under-weight 3-D 0.42× |
| M3 | MAJOR | §0.3 item 2, §7.5, §9.1 | Promised "clustered interval" specified as `student_t_ci`; coverage 0.909–0.913, lower limit negative 5–17% of the time; no clustered utility exists in the repo |
| M4 | MAJOR | §9.3 | Holm plan not executable: no p-values or nulls defined; S2 corrects a deterministic census; S1 members are functions of the primary; S1's m ambiguous; S3 doubly specified |
| M5 | MAJOR (OK finding) | §7.1, §7.3 | M0–M3 multiplicity is correctly absorbed by taking the maximum level — but this depends on the monotonicity check, which must be named as the precondition |
| M6 | MAJOR | §9.4 item 4 vs §1/§7.1, §17 | "No equivalence claim at all" contradicts the primary, which *is* a preregistered one-sided bound with margin 0.05 |
| M7 | MAJOR (mostly OK) | §9.2 label, §9.4 | `null_credible` wording is compliant; the *label* travels without its caveats |
| M8 | MAJOR | §9.2 ladder | No error control stated: `≥4` rung fires at 7.7% / 21.9% when p = 0.02 / 0.03; `null_credible` fires at 19.9% / 8.7% at those rates |
| M9 | MAJOR | §8.2 step 3, §5 item 3 | GT scored as one of ~26–664 equivalent encodings vs candidates' exact sequences; up to 6.5 nats (28% of C-S6's threshold) biasing toward E2 |
| M10 | MAJOR | §8.3 conjunctive rule | `undecidable` by construction; "direction" undefined; unhandled dead zone; E2 unreachable at sd ≥ 0.134 with n = 30 |
| M11 | MAJOR | §8.3 | Only `rank_pct_sum` is a valid probability comparison; the two "robustness" variants are not and hold veto power over the one that is |
| M12 | MAJOR | §2.1, §14 dev 4 | Cell grid misdescribed: one IC and one source trajectory per system; 12 cells → 10 distinct payloads; clean cells byte-identical across bundles (80/80) |
| M13 | MAJOR | §14 dev 4, dev 5 | Reduced design keeps the 4 most dependent cells and drops all between-bundle variation (the dimension GPU_RUN5 measured least stable) |
| m1–m9 | MINOR | see §7 | Ladder CI arithmetic, one-sided labeling, falsifier/unsupported mismatch, candidates-file divergence, unbounded intervals, artifact-row duplication |

Counts: **4 CRITICAL**, **13 MAJOR** (of which M5 and M7 are substantially favourable),
**9 MINOR**, **18 explicit OK findings** (§8).

---

## 11. Verdict

### `AMEND_BEFORE_FREEZE`

Not `STATISTICALLY_SOUND_AS_WRITTEN`: the primary endpoint cannot detect the mechanism it is
aimed at, its interval is not valid for any stated population, and Part C's decision instrument
does not measure what the decision rule claims.

Not `REDESIGN_REQUIRED`: the four-part structure, the statistical unit, the aggregation order,
the control battery, the disclosure discipline, the artifact contract, the firewall and the
compute plan are all sound and should be kept unchanged. Every defect has a surgical fix that
touches endpoint definitions and decision rules only — no change to the data, the parts, the
matchers, or the compute ceiling. Amendments 1 and 5 do replace the inferential core of Part A's
claim set and Part C's discriminator respectively, and must not be deferred to a deviation block
after Stage 4 begins.

### Minimum amendments, in priority order

1. **Add confirmatory endpoint A-P2, component-type-stratified M3 match rate** (Hill /
   variable-denominator components versus linear-decay components), each with a system-clustered
   interval, plus the two strata's difference; and stratify the primary by dimension
   descriptively. Do **not** compute the crude-folder stratification of the 107 before freezing
   this. *(fixes C1; discharges the campaign's H-G3 rule)*
2. **State the primary's target population, and report a family-clustered interval alongside the
   naive one.** Preregister the empirical ICC as a reported quantity with the frozen conditional:
   if ICĈ > 0.011 the "< 0.05" bound is withdrawn and the clustered bound is the reported result.
   Amend §1's H-C0001-P to assert only the bound the design can deliver. *(fixes C2)*
3. **Replace Part C step 1's verification** with a digest of the actual conditioning payload
   (`cell_input_payload_sha256`) plus cell-identity assertions on `noise_sigma`,
   `subsample_rho`, `bundle_index`, `system_id` and `candidate_set_hash`; relabel
   `input_trajectory_checksum` as a system-identity check; amend §5 item 3. *(fixes C3)*
4. **Repair the matcher-defect protocol's estimand.** Either recompute the crude folder's value
   under A-S3's exact `ANY` reduction and freeze that as the floor, or redefine A-S3 as the
   cell-level component rate. Report A-S3 component-weighted and dimension-stratified. Name the
   clustered interval estimator (cluster bootstrap over systems and families, resamples and seed
   frozen) and add it to the implementation ticket so `student_t_ci` is not silently substituted.
   Reconcile N6's `> 0` with §7.6's `≥ 0.0525`. *(fixes M1, M2, M3)*
5. **Make the E2/E3 discriminator the paired Stahlberg–Byrne indicator**
   `1[logP_sum(GT) > logP_sum(selected candidate)]`, with thresholds frozen on that statistic;
   demote all four rank statistics to descriptive; add the Part C reference-distribution
   resolution diagnostic as a Part C null-credibility condition; add the per-position GT-token
   rank profile (no new compute); define "disagreement" precisely and name the dead-zone outcome
   `neither_E2_nor_E3_supported`. *(fixes C4, M10, M11)*
6. **Fix the multiplicity, equivalence and disclosure text.** Drop Holm; declare secondaries
   estimation-only with stated simultaneous coverage and a stated m; separate decision rules from
   estimation intervals and give each decision rule its own alpha and bound. Rewrite §9.4 item 4
   so it does not contradict the primary. Append the §6/MAJOR-8 operating-characteristic tables
   to §9.2. Rename the `null_credible` rung to a self-limiting label and require the §9.4 item 1
   sentence in a machine-readable field on every artifact carrying the verdict. Correct §2.1's
   cell-grid description and add the single-IC scope sentence to §7.1. Correct the ladder CI
   values and record the interval function. Span all three bundles in the reduced designs
   (§14 dev 4 and 5). *(fixes M4, M6, M7, M8, M12, M13, m1–m9)*

Amendment 5 also requires stating M9's encoding asymmetry as a preregistered directional bias
toward E2, with the orbit-`logsumexp` mitigation if the supervisor accepts it.

**If any of amendments 1, 2 or 5 is declined**, the affected part must be labeled `exploratory`
in the preregistration **before** Stage 4 begins, and may not carry a confirmatory claim, a
`supported` verdict, or an invalidation of a GPU_RUN5 result.

---

## 12. Reproduction

Environment: `source /home/blabo/miniconda3/etc/profile.d/conda.sh && conda activate lansr310`
(Python 3.10.20, numpy 2.2.6, scipy). All computations read-only. **No `sealed_*` path was
opened.** Files read: `plans/C0001_preregistration.md`, `plans/C0001_preregistration.json`,
`analyses/C0001_stage1_preobservation.md`,
`analyses/C0001_exploratory_neg_canonicalization.md`, `research_state.md`,
`hypotheses/C0001_candidates.md`, `.claude/rules/01,02,03`,
`src/gpu_run4/aggregation.py`, `src/gpu_run5/phase6.py`, `src/gpu_run5/seeding.py`,
`results/runs/gpu_run5_20260823_ddd267b0/phase2/validation.json`,
`results/runs/gpu_run5_20260823_ddd267b0/phase3/cells/*_validation_*.json` (960 files, read-only).

Quantities computed by this review, in order of appearance:

| § | quantity | method |
|---|---|---|
| 1.1 | Wilson / Clopper–Pearson at k = 0,1,2,3,4,8 of 80 | closed form, z = Φ⁻¹(0.975) |
| 1.1 | minimum n tolerating 1 and 2 hits (110, 142) | search over n |
| 1.2 | comparison against Wilson-cc, Jeffreys, Agresti–Coull | closed form |
| 1.3 | one-sided 95% Wilson (0.0327), rule of three (0.0375) | closed form |
| 2 | implied q = 0.001077; E[hits] under independence = 9.54 | binomial algebra |
| 2 | corpus dimension/family cross-tabulation | `phase2/validation.json`, 80 rows |
| 2, L | outcome entropy at priors 0.80–0.98 | Shannon |
| 3 | design effect table, ICC_crit = 0.011 | deff = 1 + 9·ICC, Wilson at n_eff |
| 4 | 80 distinct checksums / 0 of 80 systems with >1 value / 10 distinct payloads | full scan of 960 cells |
| 5 | token-level T = 0.1 sampling simulation (L = 47, V = 40, 200k reference draws) | numpy, seed 3 |
| 6/M1 | A-S3 admissible range [0.0525, 0.6294] | concentration bounds on 107 hits |
| 6/M2 | A-S3 weight distortion 3.78× / 0.94× / 0.42× | 1/d weighting algebra |
| 6/M3 | `student_t_ci` coverage simulation, 20,000 reps | numpy, seed 7 |
| 6/M8 | ladder operating characteristics | `scipy.stats.binom` |
| 6/M9 | 9.375 commutable binary nodes; 3.25–6.50 nats | token census / 960 |
| 6/M10 | minimum detectable effects at n = 30; sd_crit = 0.134 | t(29, 0.975) = 2.0452 |
| 6/M12 | ANY-inflation table; 80/80 identical clean inputs | binomial; full scan of 960 cells |

---

**Reviewed by**: `lansr-statistical-reviewer`, cycle C0001, Stage 3, branch
`20260909_researce_GPU_RUNclaude1`, commit `94a571b`, 2026-09-09.
**Preregistration was not modified by this review.**
