# C0001 Part A — Stage 8 Statistical Review

- **Reviewer role**: `lansr-statistical-reviewer` (statistical design and inference only; substantive
  interpretation is a separate analyst's task and was not supplied to this reviewer)
- **Binding contract**: `GPU_RUNclaude1/plans/C0001_preregistration_v2.1.md` (v1, v2 superseded)
- **Review scope**: the `lansr-statistical-reviewer` row of v2.1 §17, plus the eight items assigned
  at Stage 8. Part C items in that row (`C2-P` discriminator thresholds, disclosed dead zone) are
  **deferred**: Part C has not run and no Part C artifact exists under
  `results/runs/gpu_runclaude1_c0001_b731cdd/`.
- **Run under review**: `gpu_runclaude1_c0001_b731cdd`, phase 1, manifest commit
  `8ff622defc227b4598e0094fc000b8227c4ffdad`, branch `20260909_researce_GPU_RUNclaude1`
- **Frozen code reviewed**: `src/gpu_runclaude1/endpoints.py`, `src/gpu_runclaude1/ladder.py`,
  `src/gpu_runclaude1/matcher.py` (`audit_monotonicity`, `_outcome_for_skeleton`),
  `scripts/phases/gpu_runclaude1_c0001_phase1_parta.py`, `src/evaluation/equation_metrics.py`
  (timeout machinery)
- **Everything below was recomputed from the 960 raw cell caches**, not taken from the endpoint
  artifact. Method: independent re-aggregation of all 101,963 stored
  `(cell, candidate, component)` records into `(system_id, component_index)` keys, `ANY` over the
  12 cells, `gain = 1[m3_any ∧ ¬m0_any]`, and independent re-implementation of Wilson,
  Clopper–Pearson, the binomial operating characteristics and the power table.

---

## 0. Standing hard constraint applied throughout

`K = 0` with an upper bound is **a bound, not a demonstration of absence**. Non-significance is not
equivalence (rule 01 item 8, v2.1 §9.5). Every sentence in this review that touches the primary is
written to that constraint, and §4 below quantifies exactly which effect sizes the design did and
did not exclude. **This review nowhere proposes raising a threshold, cap, seed or timeout.** Where
the frozen design is underpowered or fragile, that is recorded as a finding and routed to a
preregistered next cycle (§11).

---

## 1. Independent verification of the realized primary

Every realized primary value supplied for verification reproduces **exactly** from the raw cell
caches. Nothing was taken on trust.

| quantity | supplied | recomputed independently | status |
|---|---|---|---|
| `n_h` | 130 | **130** | exact |
| `n_l` | 40 | **40** | exact |
| `k_gains` | 0 | **0** | exact |
| `ladder_cutpoint` | 3 | `ceil(0.02 × 130) =` **3** | exact |
| `could_not_evaluate_rate` | 0.00011540976879576318 | **9 / 77983 = 0.00011540976879576318** | exact value, **deviant denominator** (MAJOR-2) |
| `wilson_95` | [0.0, 0.028701561634224194] | **[0.0, 0.028701561634224194]** | exact |
| `cluster_bootstrap` | 0.0, [0.0, 0.0], 10000, seed 20260909 | **[0, 0] by construction** (all 130 indicators are 0 ⇒ every resample is 0) | exact, degenerate |
| `family_wilson` | [0.0, 0.3244075683414076, 0, 8] | **Wilson(0, 8) = [0.0, 0.3244075683414076]**, 0 family hits of 8 | exact |
| `bound_of_record` | [0.0, 0.3244075683414076] | matches `family_level_wilson(...)` output | exact |
| `bound_of_record_method` | `family_level_wilson_8_cluster` | `endpoints.py:103-105` | is the v2.1 rule |
| `sensitivity_agrees` | false | **false**; `K_adversarial = 6` | exact |
| A2-S6b (`m0_any=1, m3_any=0`) | — | **0 components** | exact |
| secondaries `l_stratum_gain_rate` / `m3_level_overall` / `m3_level_h` / `m3_level_l` | 0.0 / 0.07647058823529412 / 0.0 / 0.325 | **0.0 / 13/170 = 0.07647058823529412 / 0.0 / 13/40 = 0.325** | exact |

Corpus census, recomputed: **960 / 960 cells `ok`**, 0 cell failures, **101,963** scored
`(cell, candidate, component)` triples, **80 systems × exactly 12 cells each**, **170** component
keys, **130 H / 40 L** matching `component_strata.json` and the frozen Q16 values.

`partA_ladder_realized.json` was recomputed in full from `|H| = 130` alone: the 9-row Wilson table,
the 7-row operating-characteristic table (binomial pmf/cdf at `C = 3`) and the 7-row power table all
agree to **< 1e-12**. The reference figures quoted in v2.1 §9.1 also reproduce: one-sided 95% Wilson
upper at 0/130 = **0.0204**, rule of three 3/130 = **0.0231**, two-sided Clopper–Pearson upper =
**0.0280**, two-sided Wilson upper = **0.0287**. The hash chain holds:
`component_strata.json:sha256_of_component_assignment` =
`partA_ladder_realized.json:sha256_of_component_strata_input` =
`29a9b0f14069f59909261c7a79dcd49116a069b6a11d209ab9eb31a9a13bd546`.

### 1.1 The finding that reframes every interval below

Recomputing the **joint** distribution of `(m0, m1, m3)` over all 101,963 triples gives exactly two
cells:

| `(m0, m1, m3)` | count |
|---|---|
| (0.0, 0.0, 0.0) | **99,728** |
| (1.0, 0.0, 1.0) | **2,235** |

**M0 and M3 are pointwise identical on every one of the 101,963 real component triples** — 2,235
concordant matches, 99,728 concordant non-matches, **zero discordant triples in either direction**.
`gain(s,i) = 1[m3_any ∧ ¬m0_any]` is therefore **identically zero as a set identity on this corpus**,
not as the realization of a Bernoulli process. This is recorded as CRITICAL-2 and it governs the
interpretation of §2, §3 and §4.

Two subsidiary instrument facts fall out. First, **M1 returns 0 on all 101,963 triples**, including
the 2,235 that both M0 and M3 match; all 2,235 monotonicity violations in
`matcher_monotonicity.json` are `M0->M1` (see MINOR-5). Second, M3's only demonstrated capability on
the *real* measurement path is the one PC4 exercises synthetically; the real beam contained no
instance of it.

---

## 2. Item 1 — the three-level unit hierarchy and the aggregation order

### 2.1 Is `ANY`-over-cells before the component count the right unit?

**Yes, and it is the adversarially correct choice.** v2.1 §2.1 fixes the truth component as the
analysis element (170; 130 in H), the parameterized system as the resampling cluster (80), and the
family as the second-level cluster (8), and freezes *within-component over cells first, then across
components*. The implementation matches: `scripts/.../phase1_parta.py:224-238` accumulates
`m0_any = int(m0==1.0) or existing.m0_any` and likewise for `m3_any`, keyed on
`(system_id, component_index)`, so the OR runs over candidates within a cell and then over the 12
cells before any counting. `endpoints.py:79-83` filters to H and sums. Verified reproduction: 80
systems × 12 cells, none double-counted, none missing.

The `ANY` reduction is anti-conservative for a null-shaped claim — up to 12× inflation of the hit
probability under independence, as §2.1 states — which is the correct direction: it gives E0 the
most favourable reduction and still returned 0. Cells are correctly never a unit; §2.1's P11 facts
(one initial condition and one source trajectory per system, 10 distinct conditioning payloads
across 12 cells, three clean cells byte-identical across bundles in 80/80 systems) make cell-level
independence indefensible, and treating cells as units would have inflated n by up to 12×.

### 2.2 Is the effective sample size honestly stated? Partly — and this is where independence bites

The design states three candidate sample sizes (130 components, 80 systems, 8 families) and a
design-effect table (§9.2). Where independence bites, level by level:

1. **Within component, across the 12 cells (up to ~600 triples per component).** Essentially no
   independence: one IC, one trajectory, 10 distinct payloads, 3 byte-identical clean cells.
   **Correctly handled** by collapsing to one indicator. Not a live problem for the primary — but it
   is the lever arm that breaks the sensitivity analysis (§6).
2. **Within system, across components.** A d-dimensional system's components share the same truth
   system, the same beam and the same candidate strings. Strongly dependent. **Correctly handled**:
   `ladder.py:124` extends the *whole* system's indicator list when a system is drawn, so components
   are never resampled apart from their system.
3. **Within family, across systems.** This is where independence bites hardest. Structure is a
   family-template property, family is perfectly confounded with dimension (P8), and structural
   matching is overwhelmingly a property of structure. The ICC cannot be assumed zero, and §9.2's
   own supporting evidence (GPU_RUN4's dimension gradient 17/92, 2/112, 0/40 — a between-family
   effect of enormous size) says it is large. §9.2 concedes the naive Wilson survives only for
   ICC ≤ 0.011.
4. **Across families.** **R01–R08 is the generator's complete template set, not a sample from a
   superpopulation of templates.** §2.2 defines the estimand as "components emitted by the R01–R08
   generator under the frozen `configs/gpu_run5/base.yaml`" — families are **fixed** in the estimand.
   See MAJOR-6: both interval (c) and the family-resampling stage of interval (b) treat those 8
   fixed templates as 8 random draws, which contradicts the estimand v2.1 itself adopts.

**Where the honest statement falls short.** §9.2's design-effect table computes
`deff = 1 + (m − 1)·ICC` with `m = 10` systems per family and reports `n_eff (from 80)` — i.e. it is
anchored to the **80 systems**. But the primary's analysis element is the **130 components**, and its
interval (a) is a Wilson at `n = 130`. The two are not interconvertible: 130 H components sit in 80
systems (1.625 per system on average) inside 8 families, so an honest `deff` for the primary needs
two nested factors, not one. Worse, the H components per family are **10, 10, 20, 10, 20, 30, 20, 10**
— a 3× spread — so the equal-cluster-size formula with `m = 10` does not describe the primary's
clustering at any ICC. Only the endpoints of the table are defensible: ICC = 0 corresponds to (a)'s
`n = 130` reading and ICC = 1 corresponds to `n_eff = 8`. The middle rows (ICC 0.10 → `n_eff` 42.1 →
"Wilson upper 0.0836", etc.) describe neither the component rate at n = 130 nor the system rate.
Recorded as MAJOR-5.

**Additionally, and decisively (CRITICAL-2).** Given §1.1's pointwise identity `m3 ≡ m0` on all
101,963 triples, the realized effective sample size for the *estimand the primary claims to measure*
is not 130, not 80 and not 8. The realized data contain **zero** discordant triples, so the design
observed zero opportunities for `gain` to be non-zero, and the number of *rewrite-class
opportunities* actually present in the stored beam — the quantity that determines how many
independent chances E0 had to show itself — **was never measured by Part A**. `n_eff` for the
substantive question is therefore unknown and is not bounded below by anything the design reports.

---

## 3. Item 2 — the `K = 0` bound-of-record rule and the honesty of [0, 0.3244]

### 3.1 Is the substitution the one v2.1 specifies? Yes, exactly

v2.1 specifies it in two places, identically. §7.1's frozen bound-of-record rule: "For `K ≥ 1` the
interval of record is (b). For `K = 0` the interval of record is (c), whose value is fixed and known:
`0/8 → [0, 0.3244]`." §9.2's zero-count resolution repeats it and adds that a bootstrap percentile
upper bound of 0 "may not be quoted as an evidential upper bound" and may not fill §9.5 item 1's
`[value]` slot.

`endpoints.py:103-108` implements precisely this branch — `if k == 0` → `family_wilson[0:2]` with
`bound_of_record_method = "family_level_wilson_8_cluster"`, `else` → the bootstrap. No other branch
exists. The prohibited object is correctly kept out of `bound_of_record`. **The substitution is the
specified one.**

### 3.2 Is it correctly computed? Yes

`family_level_wilson` (`ladder.py:133-146`) marks a family a hit iff at least one of its H components
gained, then applies the same Wilson function. Recomputed independently: family hits
`{R01: 0, R02: 0, R03: 0, R04: 0, R05: 0, R06: 0, R07: 0, R08: 0}` → 0/8 → `Wilson(0, 8) =`
**[0.0, 0.3244075683414076]**, agreeing with the artifact to all 16 digits and with §9.2's ICC = 1
row (`n_eff` 8.0 → 0.3244). Interval (b) is correctly `[0, 0]`: with all 130 indicators zero, every
one of the 10,000 resamples pools an all-zero vector, so the percentile interval is degenerate by
construction, exactly as v2.1 predicted.

Cluster-bootstrap specification compliance, checked line by line against §7.1(b) and §9.1:
families resampled with replacement (`ladder.py:118`) **then** systems within each drawn family with
replacement (`:122`) — draw order families-then-systems ✔; one generator stream,
`np.random.default_rng(20260909)` created once at `:115` ✔; 10,000 resamples ✔; percentile
`[2.5, 97.5]` at `:129` ✔; deterministic family order via `sorted(families)` at `:108` ✔. The
pooled-mean estimator at `:125` is a **ratio** estimator (total gains / total resampled H
components), which matches the primary's own definition `K / |H|` rather than an average of
per-system rates — the right choice, and it correctly lets the denominator vary across resamples.

### 3.3 Is [0, 0.3244] the honest bound given only 8 clusters?

**It is the honest *conservative endpoint*, and it should be reported as one endpoint of a bracket
rather than as "the" bound.** Three things are true simultaneously:

- It is the **worst-case-honest** figure. It coincides exactly with §9.2's ICC = 1 row, i.e. the
  limit in which within-family correlation is total and each family contributes one independent
  observation. Pre-committing to that endpoint when the ICC conditional cannot be discharged (§4.1)
  is *good* integrity practice, and v2.1 deserves credit for freezing it before `K` existed rather
  than choosing after.
- Its **target is the wrong parameter for the scientific claim**. It is an interval on the
  **family-level indicator rate** — the probability that a family shows ≥ 1 gain somewhere among its
  10–30 H components — not on the per-component gain rate. Only under ICC = 1 do those two
  parameters coincide. `partA_endpoints.json` records `bound_of_record_method` but **omits the
  `interval_target: family_level_indicator_rate` label that §7.1(c) and §9.2 freeze precisely so
  that "no reader mistakes it for a bound on the per-component rate"** (MAJOR-1).
- Its **model contradicts the estimand** (MAJOR-6). An 8-cluster Wilson on families presupposes that
  R01–R08 are 8 exchangeable draws from a superpopulation of families. Under §2.2's actual estimand
  the families are **fixed** and only systems and components are random within them, for which the
  correct clustered interval is a *stratified* system-level bootstrap over 8 fixed strata — an
  analysis whose `n_eff` lies between 8 and 80, not at 8. So [0, 0.3244] is, relative to the frozen
  estimand, **over**-conservative, while (a)'s [0, 0.0287] is **anti**-conservative; the defensible
  bound lies between them and was never computed.

**Can an 8-cluster bound support any claim at all?** Essentially no substantive one. Concretely, at
0/8 the interval is [0, 0.3244] whatever the data beyond "no family showed a gain"; it is a function
of the cluster count alone. It supports exactly two statements: (i) the descriptive fact that **none
of the eight families showed a single Hill-stratum gain**, and (ii) the inferential statement that
**the family-level gain-incidence rate is bounded above by 0.3244 under a random-families model**. It
supports **no** exclusion of any per-component gain rate at or below 0.3244 — which, as §4 shows,
means it excludes nothing E0 needs. v2.1 says this itself at §9.2: "an honest clustered bound is of
order 0.03–0.32 and would license almost nothing on its own." That admission is correct, and the
report must carry it, per §9.5 item 5, as *the width being the finding*.

**Judgement.** The substitution is correct, correctly computed, and the right conservative choice
under the frozen contract. But [0, 0.3244] is **not a demonstration that the gain rate is zero, is
small, or is negligible**; it is a bound on a coarser parameter than the one E0 concerns, computed
under a families-random model the estimand does not adopt, from a cluster count too small to exclude
any interesting effect. It cannot carry a `supported` conclusion on its own, and v2.1's own fallback
to the power statement (which it says is the primary's real inferential content) is circular —
CRITICAL-3.

---

## 4. Item 3 — the ICC conditional and its zero-count degeneracy

### 4.1 The conditional is well-designed; it simply cannot be discharged here

§9.2's frozen conditional — "the empirical ICC of the primary's component-level indicator is a
reported quantity. If ICC ≥ 0.011, any naive-Wilson bound is withdrawn and the family-clustered
bound is the reported result" — is a legitimate pre-commitment: it is stated before observation, it
names a numeric boundary, and its direction is fixed in advance.

At `K = 0` the ICC is **not estimable**: all 130 indicators are identical, so both the between- and
within-family variance components are exactly 0 and the ratio is 0/0. Verified from the raw data.
v2.1 anticipated this (V2-MAJ-3) and resolved it in the conservative direction — the family-clustered
bound is automatically the bound of record. **That is the correct structural resolution**: when the
conditional is undecidable, the design pre-committed to the branch that assumes the worse case rather
than leaving a post-hoc choice. Credit where due.

### 4.2 What the degeneracy actually costs, and what was not recorded

The cost is not cosmetic. Because the ICC is not estimable, **nothing in the realized data
discriminates between the ICC = 0 world (in which [0, 0.0287] would be right) and the ICC = 1 world
(in which [0, 0.3244] is right)**. The two differ by a factor of 11.3 in the upper limit, and by the
factor that decides §4/§5 below. A `K = 0` dataset is structurally incapable of estimating the
correlation parameter that determines how much a `K = 0` dataset is worth. That is a real design
limitation, it is not repairable by any analysis of these data, and it must be stated as a finding.

Three v2.1-mandated machine-readable records of this state are **absent from every artifact** —
verified by grep over `partA_endpoints.json`, `partA_ladder_realized.json`, `manifest.json`,
`partA_controls.json`:

- `icc_not_estimable_zero_count: true` (§9.2, mandatory at `K = 0`) — **absent**
- `degenerate_all_resamples_zero: true` on interval (b) (§7.1, §9.2) — **absent**, while
  `cluster_bootstrap.ci_high: 0.0` sits unlabeled in the artifact
- `assumes_component_independence: true` on interval (a) (§7.1, §9.1) — **absent**, while
  `wilson_95: [0.0, 0.0287]` is printed in the `primary` block **above** `bound_of_record`

Recorded as MAJOR-1. The third is the most consequential: §9.5 item 5 specifically forbids "quoting
the narrower independence-assuming interval as if it were the result", and the artifact's field
order plus the missing label make exactly that misquotation the path of least resistance for a
downstream reader.

---

## 5. Item 4 — the realized ladder, cutpoint 3, OC and power tables; what was actually excludable

### 5.1 The tables are arithmetically correct

Recomputed from `|H| = 130` alone, all to < 1e-12: `C = ceil(0.02 × 130) = 3`; the 9-row Wilson
table; the operating characteristics (`P(K=0) = pmf(0)`, `P(1 ≤ K ≤ 3) = cdf(3) − pmf(0)`,
`P(K ≥ 4) = 1 − cdf(3)`); the power table `1 − (1 − p)^130`. The frozen disclosure sentence's figures
check out: the upper rung fires with probability **0.2631 / 0.5495** at true rates 0.02 / 0.03, and
the lower rung with **0.0723 / 0.0191** at those same rates. Neither rung is calibrated, exactly as
§9.3 discloses. **No cutpoint is questioned here and none should move**; §9.3 is right that what was
missing in v1 was the disclosure, not a different threshold.

### 5.2 What effect sizes were actually excludable — checked against [0.053, 0.629]

The frozen admissible range for the quantity of record — M0's `ANY`-over-12 reduced component rate
for the same 107 matches — is **[9/170, 107/170] = [0.053, 0.629]** (§1 V2-MAJ-4, §7.3, §17), with
**0.0525 used explicitly and only as its arithmetic lower bound**.

| bound | value | excludes of [0.053, 0.629] | admissible under v2.1? |
|---|---|---|---|
| (a) naive Wilson, 0/130 | [0, **0.0287**] | the **whole** range | **No.** Requires ICC ≤ 0.011 (§9.2); at `K = 0` the ICC is not estimable, so the conditional cannot be discharged and (a) is not the bound of record |
| (c) **bound of record**, 0/8 families | [0, **0.3244**] | only **(0.3244, 0.629]** = width 0.3046 = **52.9%** of the range | Yes — this is the bound of record |
| (b) cluster bootstrap | [0, 0] | — | **Forbidden** as an evidential bound (§7.1, §9.2) |

**So the honest answer to "what did K = 0 of 130 exclude?" is: per-component Hill-stratum gain rates
above 0.3244, and nothing below it.** Rates of 0.053, 0.10, 0.20 and 0.30 all lie **inside** the
bound of record and are **not excluded**. In particular the design **did not exclude E0 at 0.0525**,
the very magnitude §7.3 frames the primary against. It excluded roughly the upper half (52.9% by
width) of the admissible range and left the lower 47.1% — including every value E0 plausibly needs —
untouched. The bound is a bound; it is not absence.

### 5.3 The power claim, and why it cannot be quoted as written (CRITICAL-3)

§9.2 concedes the bound licenses almost nothing and says: "**That is why the primary's inferential
content is the §7.3 powered-falsification statement and not a small-margin bound.**" §9.5 item 1's
`K = 0` variant accordingly puts the power figure, not an interval, in the substantive position:
0.9991 at p = 0.0525, 0.9277 at 0.02, 0.7292 at 0.01.

**Those figures are computed under independence across all 130 components** — i.e. under exactly the
ICC = 0 assumption whose failure forced the retreat from interval (a) to interval (c). The design
adopts the ICC = 1 worst case to choose its bound and the ICC = 0 best case to state its power. The
two cannot both be the reported basis. **This is a circularity, and it is fatal to a `supported`
reading.**

v2.1 saw this and legislated against it: §7.3 requires that "the cluster bootstrap must report the
family-clustered power at `|H| = 130` alongside them, and the **smaller** of the two is the number
the report quotes", and §9.5 item 1's verbatim sentence contains the slot "the family-clustered power
at the realized stratum size is **[value]** and is the figure quoted, being the smaller of the two."

**That quantity was never computed.** Grep confirms no artifact contains a family-clustered power
figure. Consequently **the §9.5 item 1 sentence cannot currently be issued at all** — its mandated
slot cannot be filled — and any artifact quoting 0.9991 as the design's power violates §7.3's
smaller-of-the-two rule.

For the reviewer's record, the ICC = 1 bracket (`n_eff = 8` independent family-level opportunities),
computed here, is:

| true per-component rate p | power under independence, n = 130 | power at `n_eff` = 80 | power at `n_eff` = **8** (ICC = 1) |
|---|---|---|---|
| **0.0525** | 0.9991 | 0.9866 | **0.3504** |
| 0.03 | 0.9809 | 0.9126 | **0.2163** |
| 0.02 | 0.9277 | 0.8014 | **0.1492** |
| 0.0125 | 0.8051 | 0.6344 | **0.0957** |
| 0.01 | 0.7292 | 0.5525 | **0.0773** |
| 0.005 | 0.4788 | 0.3304 | **0.0393** |

Under the *same* worst-case clustering assumption that v2.1 uses to select its bound of record, the
design's power against E0's own stated magnitude is **≈ 0.35, not 0.9991**. Because the ICC is not
estimable at `K = 0` (§4), the true family-clustered power is likewise **not estimable from these
data**; it is only bracketed, by [0.3504, 0.9991] at p = 0.0525. The honest report is that bracket,
labeled as a bracket. It is emphatically **not** "the design had 0.9991 power and saw nothing".

Note also that §10.3's `underpowered_bound_only` row is written to fire only when
`40 ≤ |H| < 100` — so at `|H| = 130` it cannot fire even though the ICC = 1 power (0.3504) is far
below the 0.90 threshold that row names. The label's *guard* is a stratum-size condition while its
*content* is a power condition; at `|H| = 130` those come apart. Not a rule to change now; recorded
for the next cycle (§11).

### 5.4 And the deeper problem (CRITICAL-2)

Every figure in §5.1–§5.3 models `K` as `Binomial(130, p)`. Given §1.1 — `m3 ≡ m0` pointwise on all
101,963 triples, zero discordance either way — the realized mechanism is a **deterministic set
identity**, not a low-rate Bernoulli process. Under a set identity the sampling distribution of `K`
is a point mass at 0 for reasons that have nothing to do with `p`, and a power calculation over `p`
does not describe the inference that was actually performed. The scientifically informative statement
available from these data is the identity itself — *"on GPU_RUN5's stored beam the constant-collapsed
skeleton matcher M3 accepts exactly the same 2,235 triples as the frozen M0 matcher, with zero
discordant triples"* — together with PC4's demonstration (100/170 gains on synthetic `together`
rewrites) that M3 *can* produce gains when the rewrite class is present. That pairing says the real
beam contained no instance of M3's one demonstrated gain class. It does **not** say E0 is false, and
it is not an equivalence claim about M0 and M3 over any wider population.

---

## 6. Item 6 — the two-sided sensitivity analysis (§7.5 item 3)

### 6.1 What the recount actually does, and whether it is the specified one

§7.5 item 3 specifies: recompute the primary "counting every could-not-evaluate **triple** as a
non-match … **and** as a match".

`endpoints.py:114-127` does **not** operate on triples. It operates on already-`ANY`-reduced
components:

```python
adversarial_gains = [
    1 if (gain == 0 and component.n_could_not_evaluate > 0) else gain
    for component, gain in zip(h_components, gains)
]
```

i.e. any H component carrying ≥ 1 could-not-evaluate triple and gain 0 is flipped to gain 1. In
general this is **more adversarial than specified**: the triple-level recount sets `m3 = 1` on the
unprovable triples, giving `m3_any = 1`, and then `gain = 1[m3_any ∧ ¬m0_any]` still returns **0**
whenever `m0_any = 1`; the component-level shortcut returns 1 regardless of `m0_any`.

**On this data the two are numerically identical, and I verified it.** All 6 affected H components
have `m0_any = 0`:

| system | component | stratum | `m0_any` | `m3_any` | could-not-evaluate triples | scored triples |
|---|---|---|---|---|---|---|
| `R03_validation_d101_005` | 0 | H | 0 | 0 | 1 | 600 |
| `R05_validation_d101_000` | 1 | H | 0 | 0 | 1 | 600 |
| `R07_validation_d101_000` | 1 | H | 0 | 0 | 1 | 600 |
| `R07_validation_d101_002` | 2 | H | 0 | 0 | 1 | 600 |
| `R07_validation_d101_003` | 1 | H | 0 | 0 | 2 | 600 |
| `R07_validation_d101_009` | 2 | H | 0 | 0 | 3 | 600 |

So `K_adversarial = 6` under either formulation. The implementation deviates from the frozen wording
in **form** but not in **realized value**, and the deviation **cannot** explain
`sensitivity_agrees = false`. Recorded as MINOR-3 with a verified null effect.

### 6.2 Is the recount appropriately calibrated against a cutpoint of 3? No — MAJOR-3

The two arms of §7.5 are calibrated on **incompatible scales**.

- Item 2's cap is a **per-triple** rate with a frozen maximum of 2.0%. The realized rate is
  9/101,963 = **0.0088%** over all triples (9/77,983 = 0.0115% as the artifact computes it) — three
  orders of magnitude inside the cap, an essentially immaculate instrument.
- Item 3's disagreement test is evaluated **after** the `ANY` reduction, against a **count** cutpoint
  `C = 3` out of 130.

The `ANY` reduction has a lever arm of up to **600 triples per component**. A single unprovable
triple among 600 flips an entire component. So 9 timeouts (0.0088% of triples) become 6 flipped
components (4.6% of H), which exceeds `C = 3` and lands the adversarial arm on the **upper** rung
while the arm of record sits on the **lower** rung. Disagreement is then automatic.

Quantifying how automatic, at 600 triples per component and 130 components:

| per-triple could-not-evaluate rate | P(a component is touched) | E[touched of 130] |
|---|---|---|
| 8.8e-05 (**realized**) | 0.0514 | **6.69** |
| 1e-04 | 0.0582 | 7.57 |
| 1e-03 | 0.4514 | 58.68 |
| 5e-03 | 0.9506 | 123.58 |
| **2.0e-02 (the frozen cap)** | 1.0000 | **130.00** |

Disagreement requires only 4 touched components. **At any per-triple rate at or above roughly 5e-05
the expected number of touched components already exceeds 3**, and at the frozen 2.0% cap every one
of the 130 components is touched, making `K_adversarial = 130` and disagreement certain. Therefore
§7.5 item 2's middle branch — "Between 0% and 2.0% the primary is reported **together with** the
two-sided sensitivity analysis of item 3" — describes a state that is, in practice, **unreachable**:
any non-zero timeout rate on a 600-triple `ANY` reduction forces `undecidable`. The only reportable
states the design admits are exactly-zero could-not-evaluate, or `undecidable`.

This is a **design fragility, not an implementation defect**, and it is a finding, not a licence to
change anything. The cap must not be raised; the cutpoint must not be moved; the timeout must not be
lengthened. §11 routes the fix to a preregistered next cycle.

### 6.3 A second problem: the trigger is non-deterministic — MAJOR-4

All 9 could-not-evaluate triples carry `failure_reason: "SymbolicEquivalenceTimeout"`.
`src/evaluation/equation_metrics.py` implements the guard with `signal.setitimer(signal.ITIMER_REAL, …)`
against `SYMPY_OP_TIMEOUT_SEC = 10.0` — a **wall-clock** SIGALRM. Which triples time out is therefore
a function of machine speed, load and process scheduling, not of the data. On a faster or less loaded
host the set could be empty (⇒ `sensitivity_agrees = true`, verdict on the lower rung) or larger
(⇒ same `undecidable`). The mandated verdict is thus a function of a non-deterministic quantity, and
the run is not bit-reproducible in its verdict. Note also that the 9 timeouts are clustered: 6 of 9
triples and 4 of 6 affected components are **R07**, so the adversarial arm's family-level indicator
would be 3/8 (R03, R05, R07), Wilson [0.1368, 0.6943] — itself a reminder that the timeout surface is
not exchangeable across families.

For completeness, had `K_adversarial = 6` been the count of record, the intervals would have been:
Wilson(6, 130) = [0.0213, 0.0970]; family Wilson(3, 8) = [0.1368, 0.6943]; and interval (b) would
have become the bound of record (non-degenerate). These are recorded only to show the magnitude of
what the 9 unprovable comparisons put at stake, not as an alternative result.

### 6.4 The verdict consequence v2.1 mandates

Realized: `verdict_non_match_direction = "no_gain_observed_bound_only"` (`K = 0`, lower rung);
`verdict_match_direction = "matcher_attributable_gain_confirmed"` (`K_adversarial = 6 > C = 3`, upper
rung). **They land on different ladder rungs.** Both recomputed independently and confirmed.

- §7.5 item 3, verbatim: "**If the two land on different ladder rungs, the verdict is
  `undecidable`.**"
- §10.3, `undecidable` row, verbatim: "**or** the §7.5 item 3 two-sided sensitivity analysis
  disagrees on the rung".

**Mandated verdict: Part A's primary endpoint is `undecidable`.** H-C0001-P is therefore **neither
`supported` nor `unsupported` nor `refuted`** — the `supported` row of §10.3 requires
`K = 0` *and* the rest of the row, and the sensitivity clause of the `undecidable` row fires
unconditionally. Consequences that follow directly:

1. `K = 0` may be reported as a **raw observation** with the `undecidable` label attached, but it
   **may not be cited as evidence for or against E0** in any confirmatory sense.
2. The **§9.5 item 1 `K = 0` verbatim sentence may not be issued as a result sentence** — it is the
   reporting form of the `supported` verdict (§10.3 row 1), and independently its mandated
   `[value]` slot (family-clustered power) is uncomputed (§5.3).
3. No downstream artifact, report, PR body or synthesis may state or imply that C0001 Part A found
   no matcher-attributable gain, that M0 and M3 are equivalent, or that E0 is bounded — pending a
   clean rerun in which the sensitivity arms agree.
4. The replication gate is engaged on the fragility ground of `.claude/skills/replication-gate`
   ("marked fragile by reviewer"): the verdict turns on 9 wall-clock-dependent triples.

**Critically, the mandated verdict appears nowhere in the artifacts.** `partA_endpoints.json` stores
`"verdict": "no_gain_observed_bound_only"` — the non-match-direction rung label — with
`sensitivity_agrees: false` recorded separately several fields away, and `manifest.json` records
`"status": "complete"`. Any consumer reading `primary.verdict` obtains the wrong verdict. This is
CRITICAL-1, and it is precisely the hazard v2.1 §9.3 names in its own rationale for renaming v1's
label: "**labels travel downstream and caveats do not**".

---

## 7. Item 5 — the §9.4 re-derived multiplicity argument

**Verified: it holds, and it does not use monotonicity.**

§9.4's structure: exactly one primary endpoint at α = 0.05, unadjusted; the Holm plan dropped in full
with five stated reasons (no null hypothesis or test statistic for any secondary, hence no p-values
to order; a deterministic census cannot be corrected; S1's members are deterministic re-reductions of
the primary's own indicator set; S1's `m` was ambiguous; S3 carried its own uncorrected thresholds).
"A decorative correction is worse than none" is right.

Item 4's replacement argument: the primary is **one indicator**, `gain = 1[m3_any ∧ ¬m0_any]`, so
exactly one test is performed on exactly one endpoint and no family of cascade-level tests exists to
correct. Verified against the code: `endpoints.py:82-83` forms one `gains` vector and one `k`;
`ladder.py:45-52` returns one label from that one count; **no per-level test statistic, p-value or
decision is computed for M0, M1 or M3 anywhere in the endpoint path.** M0's and M1's levels appear
only in the `descriptive` A2-S2 and A2-S5. The argument invokes `M0 ⊆ M1 ⊆ M3` **nowhere**. ✔

The one place item 4 could be suspected of smuggling monotonicity back in is its closing clause:
"where it is not [the most permissive level] (the monotonicity violations of A2-S6b) the affected
components are precisely those with `m0_any = 1`, which contribute 0 to `K` by definition." That is a
**tautology from the definition of `gain`** (`m0_any = 1 ⇒ gain = 0`), not an inclusion claim, so it
is legitimate. ✔ It is also empty on this run: I recompute **A2-S6b = 0** components with
`m0_any = 1, m3_any = 0`, since M0 and M3 are pointwise identical (§1.1).

Item 2's simultaneous-coverage requirement (`m = 9` for Part A, Bonferroni-widened intervals at α/m,
plus the frozen sentence "these intervals are not multiplicity-controlled and no secondary supports
a confirmatory claim") is **not satisfied by the artifacts** — MAJOR-8. `partA_endpoints.json`
carries the six secondary values as bare point estimates with **no** intervals of any kind, whereas
§9.1 requires "Wilson + cluster bootstrap, both reported" for the component- and system-level
proportions A2-S1…A2-S4, with "raw limits reported, never silently clipped". The frozen sentence
appears in no artifact.

Item 3's separation of decision rules from estimation intervals is respected in the code: the ladder
decides on counts (`ladder.py:45-52`), the controls decide on exact counts and fractions of realized
eligible sets with no α (`partA_controls.json` reports `n_eligible` / `n_pass` throughout), and no
interval carries a control decision. ✔

---

## 8. Item 7 — does any endpoint use `student_t_ci` for a proportion?

**No. Verified clean.** Grep over `src/gpu_runclaude1/`, `scripts/phases/gpu_runclaude1_c0001_phase1_parta.py`
and `GPU_RUNclaude1/tests/` returns exactly **one** occurrence of the string `student_t_ci`, at
`src/gpu_runclaude1/ladder.py:3`, inside the module docstring that **forbids** it and records why
(STAT-M3: simulated coverage 0.909–0.913 at a 0.05 rate, negative lower limit 5–17% of the time).
There is no import of `gpu_run4.aggregation` anywhere in the Part A path. Every proportion in the
realized endpoint is a Wilson score interval or the two-stage cluster bootstrap, as §9.1 freezes. ✔

§9.1's requirement that the clustered estimator be **named in the implementation ticket so it is not
silently substituted** is met in substance: `ladder.py:89` `two_stage_cluster_bootstrap` is the named
function and `endpoints.py:92` is its sole call site.

---

## 9. Item 8 — does the monotonicity audit's stored `severity` carry decision weight?

**Under v2.1: no, it carries none — and it must not be allowed to acquire any.**

v2.1 is unambiguous. §7.5 item 4: the `M0 ⊆ M1 ⊆ M3` expectation "is false and the tripwire is
**removed**"; the audit is "computed and reported" with "**No threshold on it gates anything**".
§7.3: v2's "≤ 0.1%" prediction is "**withdrawn**". §9.4 item 4 withdraws the monotonicity-based
multiplicity argument. §10.3's `undecidable` row does **not** list monotonicity among its triggers.
Verified in code: `scripts/.../phase1_parta.py:252-265` writes `monotonicity_severity` into the
`go` dict but the `status` line immediately below computes
`status = "complete" if (m0_reproduction_ok and pc0_ok and not cell_failures)` — **`monotonicity_severity`
is not read by any gate.** ✔ Correct behaviour.

But the artifact is a live misreading hazard — MAJOR-9. `manifest.json` records
`"go_conditions": {… "monotonicity_severity": "CRITICAL" …}`. A string reading `CRITICAL` inside a
field named `go_conditions`, sitting beside eight genuine boolean gates, invites a downstream
consumer — human or a later automated gate — to read it as a failed Go condition. Under
`.claude/rules/07-independent-review.md` a CRITICAL finding blocks a supported conclusion; a
decorative `"CRITICAL"` in a `go_conditions` block is therefore actively dangerous. It should be
moved out of `go_conditions` into a reported (non-gating) block, and it should be relabeled, because:

**The severity string is not even internally well-defined** — MINOR-1. `matcher.py:174-218` increments
`n_checked` **once per unit** (once per `MatchResult`, once per component) while performing **two**
checks on each (`M0->M1` and `M1->M3`). Verified: `n_checked = 149,950 = 47,987` system-scope units
`+ 101,963` component-scope units — a denominator that also **mixes two different scopes**. The
numerator, 2,235, is all component-scope `M0->M1`. Rates:

| denominator | rate | severity under the coded thresholds |
|---|---|---|
| per **unit**, 2235 / 149,950 | 0.014904968322774258 | **CRITICAL** (> `major_max_rate` 0.01) |
| per **check**, 2235 / 299,900 | 0.007452484161387129 | **MAJOR** (> 0.001, < 0.01) |
| per component **triple**, 2235 / 101,963 | 0.021920 | CRITICAL |

The label flips on an arbitrary bookkeeping choice. And its thresholds — `minor_max_rate=0.001`,
`major_max_rate=0.01`, passed at `scripts/.../phase1_parta.py:246` — are **exactly v2's withdrawn
"≤ 0.1%" prediction and withdrawn "> 1% ⇒ CRITICAL" tripwire**. The code still carries the
superseded v2 calibration and emits a v2-shaped verdict string that v2.1 explicitly de-gated.

Substantively the "CRITICAL" is the withdrawn expectation being confirmed false, exactly as v2.1
predicted: **all 2,235 violations are `M0->M1`**, driven by M1 returning 0 on all 101,963 triples
(MINOR-5), and there are **zero** `M1->M3` violations and **zero** `m0_any=1, m3_any=0` components.
So the audit's finding is "M1 is inert at component resolution", which is an instrument fact bearing
on the descriptive A2-S5 cascade table, and — per §7.5 item 4's proof, which I verified holds — it
**cannot** inflate or deflate `K`, because every violation would have to sit on a component with
`m0_any = 1`, which contributes 0 to `K` by definition.

---

## 10. Findings

Ordered by severity. Each names the artifact or file and line it rests on. Anything not verifiable
from an artifact is labeled `unverified`.

### CRITICAL

**CRITICAL-1 — the machine-readable verdict contradicts the verdict v2.1 mandates.**
`results/runs/gpu_runclaude1_c0001_b731cdd/phase1/partA_endpoints.json`, `primary.verdict` =
`"no_gain_observed_bound_only"`, produced by `src/gpu_runclaude1/endpoints.py:135`
(`verdict=verdict_non_match_direction`). The sensitivity arms disagree on the rung
(`sensitivity_agrees: false`, verified: lower rung vs upper rung), so v2.1 §7.5 item 3 and §10.3
mandate `undecidable`. That verdict appears in **no** artifact; `manifest.json` records
`"status": "complete"`. A consumer reading `primary.verdict` gets the wrong answer. This is the exact
hazard §9.3 names ("labels travel downstream and caveats do not"). **Blocks any supported
conclusion.** Remedy: `endpoints.py` must derive the final verdict from the sensitivity outcome and
the artifact must carry `undecidable` in the field a consumer reads; no threshold changes.

**CRITICAL-2 — the primary had no realized discriminating power on this corpus, so no Bernoulli-model
interval or power figure describes the inference performed.** Recomputed from all 960 cell caches
(`.../phase1/cell_cache/*.json`): the joint `(m0, m1, m3)` distribution over 101,963 triples has
exactly two cells, (0,0,0)×99,728 and (1,0,1)×2,235. **M0 and M3 are pointwise identical, zero
discordant triples in either direction**, so `gain ≡ 0` as a set identity. `K = 0` was not a draw
from `Binomial(130, p)`. Every interval and power figure in `partA_endpoints.json` and
`partA_ladder_realized.json` is computed under a model the realized data contradict, and the number
of rewrite-class opportunities actually present in the beam — the real `n_eff` for E0 — was never
measured. **Blocks any supported conclusion.** The reportable content is the identity itself plus
PC4's 100/170 demonstration that M3 *can* gain when the rewrite class is present; that is an
instrument characterization, **not** an equivalence claim about M0 and M3 and **not** evidence that
E0 is false.

**CRITICAL-3 — the fallback from a weak bound to a power statement is circular, and the mandated
power figure was never computed.** v2.1 §9.2 retreats from interval (a) to interval (c) because the
ICC cannot be assumed zero, then declares (§9.2, §9.5 item 1) that the primary's inferential content
is the §7.3 power statement — which is computed **under independence across all 130 components**,
i.e. the ICC = 0 assumption just abandoned. §7.3 and §9.5 item 1 require the **family-clustered**
power and mandate quoting the **smaller** of the two; grep over all four phase-1 artifacts finds
**no** family-clustered power figure, so §9.5 item 1's `[value]` slot cannot be filled and the
sentence cannot be issued. Recomputed ICC = 1 bracket: power **0.3504** (not 0.9991) at p = 0.0525,
**0.1492** at 0.02, **0.0773** at 0.01. Under the same worst case that selects the bound of record,
the design was **not** powered against E0's own stated magnitude. **Blocks any supported
conclusion.** Because the ICC is not estimable at `K = 0`, the correct report is the bracket
[0.3504, 0.9991] at p = 0.0525, labeled as a bracket — never 0.9991 alone.

### MAJOR

**MAJOR-1 — every v2.1-mandated machine-readable label and sentence on the `K = 0` state is absent.**
Verified by grep over `partA_endpoints.json`, `partA_ladder_realized.json`, `manifest.json`,
`partA_controls.json`: `interval_target: family_level_indicator_rate` (§7.1(c), §9.2) — absent;
`degenerate_all_resamples_zero: true` (§7.1, §9.2) — absent, while `cluster_bootstrap.ci_high: 0.0`
sits unlabeled; `icc_not_estimable_zero_count: true` (§9.2) — absent;
`assumes_component_independence: true` (§7.1(a), §9.1) — absent, while `wilson_95: [0.0, 0.0287]`
is printed **above** `bound_of_record`; the §9.3 frozen disclosure sentence ("At the realized Hill
stratum size 130, the upper rung fires with probability 0.263 / 0.550 …") — absent; the §9.5 item 0
PC4-precondition sentence and the §9.5 item 6 scope sentence, both required **verbatim in
machine-readable fields** — absent (`verdict_scope_sentence` carries only the §2.1 initial-condition
sentence). The combination of the missing independence label, the field ordering, and the missing
disclosure sentence makes the §9.5 item 5 violation — quoting the narrow independence-assuming
[0, 0.0287] as if it were the result — the path of least resistance.

**MAJOR-2 — `could_not_evaluate_rate` uses a denominator the contract does not specify.**
`src/gpu_runclaude1/endpoints.py:110-112` sums `n_could_not_evaluate` and `n_scored` over
`h_components` only, giving 9 / 77,983 = 0.00011540976879576318. §7.5 item 2 defines the denominator
as "**all** scored (cell, candidate, component) triples", which is 9 / 101,963 =
**0.0000882673126526289**. Both are three orders of magnitude below the 2.0% cap, so the gate outcome
is unchanged, and the H-only denominator is the **larger**, i.e. conservative. Recorded because the
reported number is not the frozen quantity and the report must not present it as such.
Note that `matcher.py:221-226 could_not_evaluate_rate` — an unused second implementation — divides by
component-match count, a third denominator; it is called from no endpoint path (`unverified` whether
it is called elsewhere in the campaign).

**MAJOR-3 — §7.5 item 3's disagreement criterion is scale-mismatched against `C = 3`, making the
"report with sensitivity" branch effectively unreachable.** Item 2's cap is a **per-triple** rate
(max 2.0%); item 3's test is evaluated **after** an `ANY` reduction with a lever arm of up to 600
triples per component, against a **count** cutpoint of 3 out of 130. Computed here: at the realized
per-triple rate 8.8e-05 the expected number of touched components is **6.69**; disagreement needs
only 4; at the frozen 2.0% cap **all 130** components are touched and `K_adversarial = 130`. So any
non-zero could-not-evaluate rate forces `undecidable`, and §7.5 item 2's stated middle branch
("Between 0% and 2.0% the primary is reported together with the two-sided sensitivity analysis")
describes a practically unreachable state. This is a frozen-design fragility. **No threshold, cap,
cutpoint or timeout may be changed to alter this run's result**; routed to §11.

**MAJOR-4 — the mandated verdict is a function of a non-deterministic quantity.** All 9
could-not-evaluate triples are `SymbolicEquivalenceTimeout`, produced by
`src/evaluation/equation_metrics.py`'s `signal.setitimer(signal.ITIMER_REAL, …)` wall-clock guard at
`SYMPY_OP_TIMEOUT_SEC = 10.0`. Which triples trip depends on host speed and load, so
`sensitivity_agrees` — and hence the §10.3 verdict — is not bit-reproducible. The timeouts are also
family-clustered (6 of 9 triples and 4 of 6 affected components are R07), so the failure surface is
not exchangeable. A clean rerun from a fresh process on identical inputs is required to establish
whether the disagreement is stable; that rerun is the natural replication-gate design (§11).

**MAJOR-5 — the §9.2 design-effect table is anchored to the wrong `n` for the primary, and its
cluster-size assumption is violated.** §9.2 computes `deff = 1 + (m − 1)·ICC` with `m = 10` systems
per family and tabulates "`n_eff` (from **80**)" plus "Wilson upper @ 0 hits" for those `n_eff` — but
the primary's analysis element is the **130 components** and interval (a) is a Wilson at `n = 130`.
The two are not interconvertible: an honest `deff` for the primary needs nested
components-in-systems-in-families factors. Verified from `component_strata.json:by_family`, the H
components per family are **10, 10, 20, 10, 20, 30, 20, 10** — a 3× spread — so the equal-cluster
formula does not describe the primary's clustering at any ICC. Only the ICC = 0 and ICC = 1 endpoints
of the table are defensible; the middle rows (e.g. ICC 0.10 → `n_eff` 42.1 → 0.0836) bound neither
the component rate at 130 nor the system rate at 80 and must not be quoted as bounds on the primary.

**MAJOR-6 — interval (c)'s random-families model contradicts §2.2's fixed-families estimand.** §2.2
defines the estimand's population as "Hill-type GRN truth components emitted by the **R01–R08**
generator under the frozen `configs/gpu_run5/base.yaml` settings" — the eight templates are **fixed
and exhaustively sampled**, not 8 draws from a superpopulation of families. Yet interval (c)
(`ladder.py:133-146`) is an 8-cluster Wilson **on the family indicator**, and interval (b)
(`ladder.py:118`) resamples **families with replacement**. Both presuppose exchangeable random
families. Under §2.2's own estimand the correct clustered interval is a **stratified** system-level
bootstrap over 8 **fixed** strata, whose `n_eff` lies between 8 and 80 — and it was not computed.
Consequence for reporting: [0, 0.3244] is over-conservative relative to the frozen estimand while
[0, 0.0287] is anti-conservative; the defensible bound is bracketed by them, and the bound of record
must be reported as **the conservative endpoint of a bracket on a family-level rate**, never as "the
95% bound on the per-component gain rate".

**MAJOR-7 — the null-branch gate is placed on controls that v2.1 §7.7.1 forbids gating on.**
§7.7.1's short-circuit rule reads, verbatim: "**no gate may be placed on a control whose
non-short-circuited subset is empty**." `partA_controls.json` records PC2c and PC2d as
`170/170 short_circuited by canonical_exact (canonicalize_tree already sorts commutative operands, so
M1 alone recovers equivalence…)` — i.e. their non-short-circuited subsets are **empty**. Yet §7.7.3
places the **null-branch** gate on exactly PC2c/PC2d, and §10.3's `undecidable` row triggers on
"`K = 0` and PC2c or PC2d < 95% of its eligible set". Under §7.7.1 that gate is **void as written**,
and PC2c/PC2d's 100% pass **may not be cited as evidence that M3 is sensitive to invariance
rewrites**. What remains genuinely non-vacuous is PC4 (gain 100, `gain_h` 100, 6 of 8 families,
`gates_ok: true`) — which does demonstrate the gain indicator can fire and does satisfy the §9.5
item 0 precondition — and PC0 (170/170). PC2a is already correctly reclassified by v2.1 as
harness-identity only. So the null branch is not uncontrolled, but its **invariance-sensitivity**
coverage is vacuous, and no artifact may claim otherwise. (Rated MAJOR rather than CRITICAL precisely
because PC4, the §7.7.3 hard-abort control, is non-vacuous.)

**MAJOR-8 — the secondaries carry no intervals and no multiplicity disclosure.**
`partA_endpoints.json:secondaries` reports six bare point values
(`l_stratum_gain_rate: 0.0`, `l_stratum_n: 40`, `h_minus_l_difference: 0.0`,
`m3_level_overall: 0.07647058823529412`, `m3_level_h: 0.0`, `m3_level_l: 0.325`), all recomputed and
correct. But §9.1 requires "Wilson + cluster bootstrap, **both reported**" for the component- and
system-level proportions A2-S1…A2-S4, with raw limits "**never silently clipped**"; §9.4 item 2
requires **Bonferroni-widened intervals at α/m with `m = 9`** for Part A plus the frozen sentence
"these intervals are not multiplicity-controlled and no secondary supports a confirmatory claim";
and §7.8 requires A2-S3 to carry both `assumes_family_icc_zero: true` Wilson and family-clustered
forms. None of this is present in any artifact. `compute_secondaries` (`endpoints.py:158-182`)
computes no interval of any kind. Note also §7.8's own warning that A2-S1 is structurally suppressed
(L exists only in R04/R07/R08, where M0 already succeeds) — verified from
`component_strata.json:by_family` — so the `h_minus_l_difference: 0.0` must not be read as evidence
that any gain "lives in H".

**MAJOR-9 — a non-gating, withdrawn-threshold severity string is stored inside `go_conditions`.**
`manifest.json:go_conditions.monotonicity_severity` = `"CRITICAL"`, beside eight genuine boolean
gates. Under v2.1 §7.5 item 4 this quantity gates **nothing** ("No threshold on it gates anything"),
and I verified the code does not gate on it (`scripts/.../phase1_parta.py:252-265`: `status` reads
only `m0_reproduction_ok_on_scored_subset`, `pc0_ok` and `n_cell_failures`). But its placement and
its value make misreading by a downstream consumer — or capture by a future automated gate — likely,
and under `.claude/rules/07-independent-review.md` a CRITICAL blocks a supported conclusion. It must
be moved out of `go_conditions` into a reported non-gating block, and its `minor_max_rate=0.001` /
`major_max_rate=0.01` thresholds (`phase1_parta.py:246`) are v2's **withdrawn** tripwires still live
in code.

### MINOR

**MINOR-1 — the monotonicity `severity` label is not internally well-defined.**
`matcher.py:186-203` increments `n_checked` once per **unit** while performing **two** checks per
unit, and mixes scopes: `n_checked = 149,950 = 47,987` system-scope `+ 101,963` component-scope
(verified). Per-unit rate 2235/149,950 = 0.014905 → `CRITICAL`; per-check rate 2235/299,900 =
0.007452 → `MAJOR`; per component triple 2235/101,963 = 0.021920 → `CRITICAL`. The label flips on a
bookkeeping choice. Harmless under v2.1 only because the label gates nothing (see MAJOR-9).

**MINOR-2 — the admissible range is printed inconsistently in the contract.** §1 (line 84), §1
(line 301), §4 (line 681), §17 (line 2192) and §19 (line 2294) all give
**[9/170, 107/170] = [0.053, 0.629]**; §7.6 (line 1059) gives **[0.052, 0.629]**. The correct value
is 9/170 = 0.052941…, so both roundings are defensible, but the report must use one — and §17
assigns this reviewer **[0.053, 0.629]**, which §5.2 above uses.

**MINOR-3 — the adversarial recount is implemented on `ANY`-reduced components, not on triples;
verified numerically identical here.** `endpoints.py:122-125` flips any H component with
`n_could_not_evaluate > 0` and `gain == 0` to gain 1, whereas §7.5 item 3 specifies counting each
could-not-evaluate **triple** as a match and re-running the reduction. The shortcut is
**more** adversarial in general (it flips components with `m0_any = 1`, which the triple-level
recount would leave at 0). Verified: all 6 affected H components have `m0_any = 0`, so
`K_adversarial = 6` under either formulation and the deviation **cannot** explain
`sensitivity_agrees = false`. Should be corrected in form for future cycles.

**MINOR-4 — 10,000 bootstrap resamples of an identically-zero vector.** With all 130 indicators 0
every resample is 0 by construction, so interval (b) carries zero information. Correctly excluded
from `bound_of_record` (`endpoints.py:103-105`) and correctly still reported per §7.1 — but it must
carry the `degenerate_all_resamples_zero: true` label it currently lacks (MAJOR-1), and its
`ci_high: 0.0` must never be quoted as an upper bound (§7.1's absolute prohibition).

**MINOR-5 — M1 is inert at component resolution.** Recomputed: `m1 = 0` on **all 101,963** triples,
including all 2,235 that both M0 and M3 match. This drives 100% of the monotonicity "violations". M1
is not in the primary's definition, so this does not touch `K`, but it materially affects the
descriptive A2-S5 cascade increment table, which under §7.8 "may not be presented as a nested
cascade" — here the three sets are `M0 = M3 = ` 2,235 triples and `M1 = ∅`. Whether M1's inertness is
a defect or the correct behaviour of `canonical_exact` on component-split infix is `unverified` from
these artifacts.

### Verified correct (credit where due)

- `n_h` 130, `n_l` 40, `K` 0, cutpoint 3, and all six secondary point values reproduce **exactly**
  from the 960 raw cell caches.
- `partA_ladder_realized.json` reproduces in full from `|H| = 130` alone (Wilson table, OC table,
  power table) to **< 1e-12**, and §9.1's reference figures (one-sided Wilson 0.0204, rule of three
  0.0231, Clopper–Pearson 0.0280, two-sided Wilson 0.0287) all check out.
- The §7.2 write-before-match hash chain holds:
  `component_strata.json:sha256_of_component_assignment` =
  `partA_ladder_realized.json:sha256_of_component_strata_input` = `29a9b0f1…13bd546`.
- The bound-of-record substitution at `K = 0` is **exactly** the rule v2.1 §7.1 and §9.2 specify, and
  is correctly computed.
- Cluster-bootstrap specification compliance is complete: one `default_rng(20260909)` stream,
  families-then-systems draw order, families then systems both with replacement, 10,000 resamples,
  percentile [2.5, 97.5], deterministic `sorted()` family order, components never resampled apart
  from their system, ratio estimator matching `K/|H|`.
- **No `student_t_ci` anywhere in the Part A path**; its only occurrence is the docstring forbidding
  it.
- §9.4's multiplicity argument is verified to hold **without** any use of `M0 ⊆ M1 ⊆ M3`.
- A2-S6b = **0** verified; §7.5 item 4's proof that monotonicity violations cannot affect `K` is
  verified sound (it is a tautology from `gain`'s definition).
- The §7.7.3 gating map **is** legitimately outcome-independent: both branches are written before any
  `K` exists, no threshold differs between them, and what differs is only which verdict a given
  instrument bias may license — a direction-of-bias argument, not a data-dependent one. Rule 01
  item 3 is not engaged. (Its PC2c/PC2d row is separately void for the vacuity reason of MAJOR-7.)
- PC4, the §7.7.3 hard-abort control, is **non-vacuous** (gain 100 ≥ 40, `gain_h` 100 ≥ 20, 6 of 8
  families ≥ 3, `gates_ok: true`), so the §9.5 item 0 precondition is satisfied and `K` is not being
  read off an instrument incapable of producing a gain.
- 960/960 cells `ok`, 0 cell failures, `m3_implementation_agreement` 480/480 = 1.0.

---

## 11. Recommendation for a preregistered next cycle

Stated as design recommendations only. **Nothing here is a proposal to change a threshold, cap, seed
or timeout in order to change C0001's result**, and C0001 Part A's mandated `undecidable` stands
regardless of whether any of this is adopted.

1. **Preregister the sensitivity criterion on a matched scale (fixes MAJOR-3).** The disagreement
   test must be defined on the same reduction as the quantity it perturbs. Options to freeze *before*
   observation: state the adversarial recount at triple level (as §7.5 item 3's words already say)
   **and** declare in advance a maximum number of `ANY`-reduced components the unprovable triples may
   touch, derived from the frozen per-triple cap and the 600-triple lever arm rather than chosen after
   seeing the count; or make the primary's decision rule operate on a quantity the `ANY` reduction
   does not amplify.
2. **Resolve the unprovable comparisons by a preregistered decision procedure, not by a longer
   clock (fixes MAJOR-4).** A wall-clock SIGALRM makes the verdict host-dependent. The fix is a
   *deterministic* adjudication of the specific unprovable triples — declared in advance, applied
   identically to every triple, and reported with its own outcome column — not a larger
   `SYMPY_OP_TIMEOUT_SEC`.
3. **Compute the family-clustered power, and quote a bracket (fixes CRITICAL-3).** Preregister that
   the reported power is a bracket whose endpoints are the independence figure and the ICC = 1 figure
   at the realized stratum size, since a `K = 0` dataset cannot estimate the ICC. Also decouple
   §10.3's `underpowered_bound_only` guard from `|H|` and attach it to the realized (bracketed) power,
   so the label can fire at `|H| = 130` when the clustered power is 0.35.
4. **Align the clustered interval with §2.2's fixed-families estimand (fixes MAJOR-6, MAJOR-5).**
   Preregister a stratified system-level bootstrap over 8 **fixed** family strata as the interval of
   record, with the 8-cluster family Wilson retained as the explicitly-labeled conservative endpoint
   of a reported bracket, and build the design-effect table on the primary's own element count (130
   components in 80 systems in 8 families with unequal H-per-family) rather than on 80 systems with
   `m = 10`.
5. **Measure the estimand the identity of §1.1 actually poses (fixes CRITICAL-2).** The question
   Part A could not answer is *how many instances of M3's demonstrated gain classes were present in
   the stored beam at all*. Preregister that census — a candidate-side count of rewrite-class
   opportunities — as a primary, so a zero gain count can be distinguished from a zero opportunity
   count. Without it, `K = 0` is uninformative about E0 in a way no interval width can convey.
6. **Replace the vacuous invariance-sensitivity controls (fixes MAJOR-7).** PC2c/PC2d must be
   redesigned so their non-short-circuited subsets are non-empty, or the null-branch row of §7.7.3
   must be rewritten to rest only on controls that are non-vacuous. §7.7.1's own rule already
   forbids the current arrangement.
7. **Emit the mandated labels and sentences mechanically (fixes CRITICAL-1, MAJOR-1, MAJOR-8).** The
   verbatim §9.3 and §9.5 sentences, the interval labels, the ICC degeneracy flag and the final
   §10.3-derived verdict should be written by the endpoint code and asserted present by a test, not
   left to the report writer. A required-fields test over `partA_endpoints.json` would have caught
   all of MAJOR-1 and CRITICAL-1 before Stage 8.

---

## 12. Statement required by the hard constraint

`K = 0` of 130, with a bound of record of [0, 0.3244] on the **family-level** indicator rate, is **a
bound, not a demonstration of absence**. It does not license "the gain rate is zero", "the matcher
makes no difference", "M0 and M3 are equivalent", "canonicalization is unnecessary", or "the two
matchers agree" — and the pointwise identity of §1.1 is an *observed property of GPU_RUN5's stored
beam*, not an equivalence result about the two matchers over any wider population. The bound
excludes only per-component gain rates above 0.3244, i.e. **52.9% of the frozen admissible range
[0.053, 0.629] by width**, leaving every value at or below 0.3244 — including E0's own stated
magnitude of 0.0525 — **unexcluded**. Under the worst-case clustering that v2.1 itself adopts to
select that bound, the design's power against 0.0525 is **0.3504**, not 0.9991. And the verdict
v2.1's own frozen rules mandate for this run is **`undecidable`**, not a null.

---

## 13. Addendum — concurrent code change observed during this review

While this review was being written, `src/gpu_runclaude1/endpoints.py` was modified on disk by
another agent (uncommitted; `git diff --stat` shows 13 insertions, 1 deletion). The change addresses
**CRITICAL-1** directly: `endpoints.py:143-147` now folds the sensitivity disagreement into the
returned verdict —

```python
verdict=(
    verdict_non_match_direction
    if verdict_non_match_direction == verdict_match_direction
    else "undecidable (two-sided sensitivity disagreement)"
),
```

This reviewer's assessment of the change: **it is the right fix and it is in the right place.** It
derives the verdict of record from the §7.5 item 3 outcome rather than leaving `sensitivity_agrees`
to be noticed by a caller, and it introduces no threshold, cap, seed or timeout change.

**CRITICAL-1 is nevertheless not yet discharged**, for two reasons:

1. **The artifact still carries the wrong verdict.** Re-read after the code change,
   `results/runs/gpu_runclaude1_c0001_b731cdd/phase1/partA_endpoints.json` still records
   `primary.verdict = "no_gain_observed_bound_only"` with `sensitivity_agrees: false`. The stored
   run predates the fix. Under `.claude/rules/05-git-and-artifact-safety.md` this run's artifacts
   must not be overwritten; the corrected verdict must be published either as a new run ID or as an
   explicit, dated correction record that states the superseded value. Until one of those exists, any
   consumer reading the stored artifact still gets `no_gain_observed_bound_only`.
2. **The string is not one of §10.3's verdict labels.** `"undecidable (two-sided sensitivity
   disagreement)"` is a new label; §10.3's row lists the triggers under the single verdict
   `undecidable`, and its sibling parenthetical forms are the frozen
   `undecidable (gain indicator not demonstrated)` and
   `undecidable (matcher sensitivity insufficient)` / `(matcher specificity insufficient)`. The new
   string is in the same style and is unambiguous, so this is a **MINOR** naming point, not a defect
   — but it should be added to the enumerated label set so downstream consumers can match on it, and
   a test should assert that the emitted verdict is a member of that set.

Neither point changes the verdict consequence: **Part A's primary is `undecidable`.** The remaining
CRITICAL-2 and CRITICAL-3 findings are untouched by this change — they concern the pointwise
`m3 ≡ m0` identity and the uncomputed family-clustered power, neither of which is an
`endpoints.py` verdict-labeling matter.
