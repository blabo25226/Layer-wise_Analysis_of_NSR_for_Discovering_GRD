# C0002 preregistration v1 — statistical review (pre-freeze)

| field | value |
|---|---|
| reviewer role | `lansr-statistical-reviewer` |
| target | `GPU_RUNclaude1/plans/C0002_preregistration_v1.md` (1,199 lines) + `...v1.json`, status `DRAFT_PENDING_REVIEW` |
| date | 2026-09-11 |
| branch | `20260909_researce_GPU_RUNclaude1` |
| independence | independent of the drafting methodologist and of the concurrent `lansr-reproducibility-auditor` pass. No C0001 artifact, no run artifact and no draft file was edited. |
| sealed test | not touched; no `load_sealed_test` call was made |
| **verdict** | **MUST NOT BE FROZEN AS WRITTEN.** 7 CRITICAL, 13 MAJOR. |
| **supported-E2 defensibility** | **Not defensible as drafted** — see §A. |

Everything numeric below was recomputed from artifacts or simulated; the commands are in §F.
Anything I could not verify is labelled `unverified`.

---

## A. Headline verdict on the three E2-biasing mechanisms

The draft asks (§8.5) whether its bias-audit battery measures the three mechanisms or merely
discloses them. The answer, mechanism by mechanism:

| mechanism | direction | audit | can it block a supported E2? |
|---|---|---|---|
| T = 0.1 upper-tail sampling makes `B` near-greedy | → E2 | BA1 | **No** — appends a label (`E2_conditional_on_near_greedy_reference`) |
| summed-log-prob length bias (D19-1331 §4) | → E2 | BA2 | **No** — `length_control_not_measurable` is reported, and §13 lists only "BA2 fails its disagreement bar" as a confounding trigger |
| single-encoding `lp_gt` is a lower bound | → E2 | BA3 | **No** — its consequence ("only the logsumexp read is reportable") is a no-op, because the primary already *is* the logsumexp |
| F-g conditioning mismatch | unknown | BA4 | **Yes** — `conditioning_sensitive`, nothing attributed |

**All three audits that would police the campaign's preferred answer have label-only or no-op
consequences. The single audit with a real blocking consequence is the one whose direction is
unknown.** That asymmetry is not stated in the draft and is the central reason a supported E2
would not be defensible. It is compounded by CRITICAL-2 (the E2 rule reads a one-sided bound in the
direction where it carries no information) and CRITICAL-6 (BA2's availability measures ≈ 0.53
against its own 0.50 bar).

A supported E2 becomes defensible only if the E2 branch rests **solely** on the P2 positive
certificate, and BA1/BA2/BA3 are given blocking rather than cosmetic consequences.

---

## B. What verified clean

Stated first so the CRITICAL list is not read as a rejection of the whole design.

1. **Realized denominators (§4) verify exactly** against the durable artifacts. Recounted over
   `results/runs/gpu_run5_20260823_ddd267b0/phase3/cells/*.json` ∩
   `results/runs/gpu_runclaude1_c0001_b731cdd/phase2/partB_in_support_systems.json`:
   960 cell files; 71 in-support systems; **852** in-support cells; **42,593** candidates;
   **42,593 / 42,593 `valid: true`**; candidates per cell `{50: 846, 49: 5, 48: 1}`; per-family
   in-support counts `R01 10, R02 10, R03 10, R04 10, R05 10, R06 10, R07 4, R08 7`; every one of
   the 71 systems has exactly 12 cells; 47,987 candidates over all 960 cells. **Every figure in
   §4 and §0.1 that I could check is correct.** This is a real improvement over C0001.
2. **`H0010` attaches no sampling inference to a census.** §12.1 gives it "no interval" and
   `interval_interpretation: "deterministic_census_no_sampling_variability"`. Item 8's first half is
   satisfied.
3. **No `student_t_ci` anywhere in the draft**, and no endpoint applies it to a proportion. Item 9
   is clean on that count (the only repository occurrences are in `GPU_RUN4/tests/` and in prior
   review text forbidding it).
4. **§12.3 (non-significance ≠ equivalence) is correctly drafted**, as are §8.7's permitted and
   forbidden reporting sentences, including the 53.62% Beam-100 undercounting statement (verified
   against `literature/C0002_literature.md:96-97, :169-170`) and the refusal to set an equivalence
   margin on a log-probability difference.
5. **The degenerate-bootstrap substitute can bear a decision**, unlike C0001's. Verified:
   Wilson(0/8) = [0, **0.3244**] and Wilson(8/8) = [**0.6756**, 1]. Under a fully degenerate
   all-E2 corpus the E2 rule's arithmetic fires (P1 UB 0.3244 < 0.5, P2 LB 0.6756 > 0.5); under a
   fully degenerate all-E3 corpus the E3 rule fires. C0001's near-uninformative substitute is not
   repeated. (But see MAJOR-11 for the discontinuity it creates.)
6. **§10's controls do have measured, achievable expected values** — PC-GREEDY 2/10 with margins to
   +32.29 nats, PC/NC-H0010 12/12, the regression identity 7.3e-08…8.1e-07, the round trip 300/300.
   The MAJOR-R6 lesson is honoured **for §10**. It is not honoured for §8.5 (MAJOR-7).
7. **Arm B's exclusion is statistically sound**: its realized denominator is unknown by
   construction, which is exactly the OC hazard the cycle was selected to avoid.

---

## C. CRITICAL findings

### CRITICAL-1 — `lp_gt` as a logsumexp destroys the `G > B` certificate that P1 is built on
**Anchor:** §7.2 (`lp_gt(c) = logsumexp over the verified members of E(s)`), §8.1
(`sb_best(c) = 1[lp_gt(c) > lp_best(c)]` — "certified search error"), §1.1 ("this is the whole
reason the endpoint is usable").

Stahlberg & Byrne's bound is `γ ≤ log P(ŷ|x)` where `γ` is the log-probability of **one complete
sequence**. `L* ≥ G > B ⇒ search error` requires `G` to be a single-sequence score.

§7.2 defines `G = log Σ_{e ∈ E(s)} P(e)`, the truth's aggregated mass over up to 10 distinct token
sequences (`e1`, `e2`, and up to 8 orbit members). A set probability exceeding a point probability
implies nothing about any single member: `K` sequences each at `log P(b) − 1` sum to
`log P(b) − 1 + log K`, which exceeds `log P(b)` for `K ≥ 3`, while **no** member outscores `b`.
There is then no sequence certified to beat `lp_best`, and no search error is certified.

Direction of the damage: the `G < B` branch is **unharmed and in fact strengthened**
(`max_e log P(e) ≤ log Σ_e P(e) < log P(b) ≤ L*` ⇒ every spelling of the truth is below `b`).
So **P2 survives; P1 does not.** The draft has spent §7.2 fixing BA3's lower-bound bias by a
construction that invalidates the only endpoint it calls PRIMARY.

**Required change.** Wire the already-recorded quantities to the right endpoints:
`sb_best(c) = 1[lp_gt_max(c) > lp_best(c)]` using `lp_gt_max = max_e lp_gt(e)` (a single-sequence
score, so the certificate holds), and keep the logsumexp for `me_best` / P2 (where it strengthens
the certificate). Both quantities are already in §7.2 as "descriptive companions"; no new compute
and no threshold change is involved. `log K ≤ 2.30` nats for `K ≤ 10`, so this is numerically small
— but the *logic* of the primary endpoint is what is at stake, and boundary cells are exactly where
it bites. Record both variants of `sb_best` and preregister which bears the decision.

### CRITICAL-2 — the E2 rule reads P1's bound in the direction where it carries no information
**Anchor:** §13 ("**E2 predominant** iff the family-clustered 95% **upper** bound of **P1** < 0.5
and …"), against §8.7 ("an approximation built on a returned set systematically **undercounts**
search errors").

`sb_best = 1` certifies a search error. `sb_best = 0` certifies **nothing**: `lp_gt ≤ lp_best` is
fully compatible with some unreturned sequence outscoring `lp_best`. P1 is therefore a **certified
lower bound** on the true search-error system rate — the draft says so itself in §6, §8.7 and in the
JSON (`"status_of_indicator": "a CERTIFIED LOWER BOUND … not an estimate"`).

An upper confidence limit on a lower bound bounds nothing above. "P1 UB < 0.5" says only "the
certificate fired on fewer than half the systems". The true rate may be anything. Using it as one
of the two conditions for concluding E2 is **precisely rule 01 item 8** — non-detection read as
absence — in bound form, and it directly contradicts §8.7's own frozen sentence three sections
earlier.

**Required change.** Delete "the 95% upper bound of P1 < 0.5" from the E2-predominant rule. The E2
branch must rest **only** on P2, which is a positive certificate. State explicitly that C0002 cannot
bound the search-error rate from above, and that no configuration of P1 supports an
"and not search" claim.

### CRITICAL-3 — E2 and E3 are not mutually exclusive, so a single "corpus attribution" is invalid
**Anchor:** §1.1 ("Equivalently the failure is prior mass (**E2**), not search (**E3**)"), §13's
mutually-exclusive branch structure.

- E2 = "the truth is not the model's argmax" — certified by `me_best = 1`.
- E3 = "the decode failed to return the model's argmax" — certified by `sb_best = 1`.

Both can be true simultaneously. Indeed `sb_best = 1` gives `L* ≥ lp_gt > lp_best`, which leaves
`L* > lp_gt` entirely open — i.e. a certified search error is compatible with the truth **also** not
being the argmax. The per-cell indicators are mutually exclusive only because they compare the same
two numbers; the underlying propositions are not. `sb_best = 1` does not refute E2, and
`me_best = 1` does not refute E3.

§1.1's "equivalently" is therefore false, and §13's framing — one attribution, E2 *or* E3 *or*
neither — mis-states what the instrument can deliver. This is an estimand error that no interval
method can repair.

**Required change.** Reframe as two independent lower bounds reported side by side: P1 lower-bounds
the rate of systems with certified search error; P2 lower-bounds the rate of systems on which the
truth is certifiably not the argmax on every usable cell. Both may be high. Retire the words
"predominant" and "attribution", or define them explicitly as statements about *certificates*, never
about which failure mode obtains. `H0001-R`'s falsifiable statement in §1.1 must be rewritten to
drop "not search".

### CRITICAL-4 — the interval of record resamples 8 **fixed** families, contradicting §2.2, and undercovers
**Anchor:** §2.2 (superpopulation = "Hill-type GRN dynamical systems emitted by the R01–R08
generator"; the finite-population reading is explicitly rejected), §12.1 (interval of record =
"family-clustered … bootstrap over the 8 families").

R01–R08 are the generator's eight defined topologies, all eight present in the corpus. Under §2.2
the **systems** are the random draws and the families are **fixed strata**. Resampling families
with replacement targets a superpopulation of *families*, which §2.2 does not posit. **This is the
same random-family / fixed-family contradiction that helped render C0001 undecidable, repeated with
a different estimator.**

It is not a formality; measured consequences (simulation, §F):

*Coverage of the true superpopulation system rate (systems iid Bernoulli(p) within the 8 fixed
families, 500 reps, B = 600):*

| true p | draft's cluster bootstrap (8) | stratified-within-family bootstrap | Wilson(71) |
|---|---|---|---|
| 0.20 | **0.884** | 0.932 | 0.948 |
| 0.35 | **0.876** | 0.936 | 0.960 |
| 0.50 | **0.904** | 0.936 | 0.952 |
| 0.65 | **0.886** | 0.936 | 0.962 |
| 0.80 | **0.892** | 0.930 | 0.964 |

Nominal is 0.95; the draft's interval of record delivers **0.876–0.904**, i.e. roughly double the
declared error rate.

*Widths on fixed corpora (10,000 resamples, seed 20260911):*

| corpus | P | draft: cluster boot (8) | stratified boot | Wilson(71) |
|---|---|---|---|---|
| ~30% of systems | 0.296 | [0.288, 0.300] **w = 0.012** | [0.197, 0.408] w = 0.211 | [0.202, 0.410] w = 0.208 |
| ~50% | 0.507 | [**0.500**, 0.523] w = 0.023 | [0.394, 0.620] w = 0.225 | [0.393, 0.620] w = 0.227 |
| ~60% | 0.592 | [**0.576**, 0.600] w = 0.024 | [0.479, 0.704] w = 0.225 | [0.475, 0.698] w = 0.223 |
| ~70% | 0.704 | [0.700, 0.712] **w = 0.012** | [0.592, 0.803] w = 0.211 | [0.590, 0.798] w = 0.208 |

**A "clustered" interval narrower than the unclustered Wilson by up to 17× is diagnostic of the
wrong resampling unit.** Because all systems appear in every family and the families are
homogeneous under the null, resampling families removes almost all variability; the procedure treats
the 71 systems as a census and contradicts §2.2's rejection of the finite-population reading.

Decision-flipping consequence, explicitly: at P2 = 0.592 (42 of 71 systems) the draft's rule
declares **E2 predominant** (clustered LB 0.576 > 0.5); an interval consistent with §2.2's estimand
does not (LB 0.479). At P1 = 0.507 the clustered LB is **0.500** — the E3 branch sits on the
threshold at a coin-flip point estimate. The effective evidentiary bar for either branch drops from
`p̂ ≈ 0.62` to `p̂ ≈ 0.51` purely as an artefact of the interval method.

**Required change.** State which estimand is binding and use the matching resampling unit. If §2.2
stands (systems random, families fixed) the interval of record must be a **stratified bootstrap
resampling systems within each fixed family**, with the family kept as a fixed effect. If instead
the families are to be treated as random, §2.2 must say so and the draft must then disclose that
G = 8 clusters cannot support a 0.5-threshold decision at all. I take no position on which is more
likely to pass; the two must not be mixed as they are now.

### CRITICAL-5 — §12.4's disclosed operating characteristic is not what the draft's procedure produces
**Anchor:** §12.4 ("A family-clustered 95% interval on a mid-range proportion will be roughly
**0.3–0.5 wide**. `neither_E2_nor_E3_predominant` is therefore a plausible corpus-level outcome by
construction").

Simulated realized widths of the draft's own estimator on mid-range proportions are **0.012–0.080**
(table above). The disclosure is wrong by more than an order of magnitude, and wrong in the
dangerous direction: it warns the reader to expect an uninformatively wide interval when the actual
hazard is a spuriously narrow one that crosses the 0.5 cutpoint on a near-coin-flip estimate. Width
approaches 0.3–0.5 only under extreme between-family heterogeneity (e.g. four families entirely E3
and four entirely E2 gives w = 0.721), which is not the "mid-range proportion" case the sentence
describes.

This matters beyond arithmetic: §12.4 is the draft's pre-run inoculation against a later reading of
a wide interval as experimental failure. As written it would inoculate against the wrong failure and
leave the real one — a narrow, undercovering interval manufacturing a supported branch — undisclosed.

**Required change.** Recompute §12.4 from the estimator actually preregistered (after CRITICAL-4 is
resolved), report simulated coverage and width at several true rates, and state the minimum point
estimate at which each branch can fire.

### CRITICAL-6 — BA2 is not verified achievable, degenerates where it runs, and cannot block E2
**Anchor:** §8.5 BA2, §13, against §10's own opening principle ("a design whose observable ceiling …
so that no control could produce a non-zero value of the primary indicator" was C0001's near-fatal
defect) and the task-level constraint that a control which cannot produce a non-zero value of the
indicator it gates is not a control.

BA2 is the only audit of D19-1331's **own central finding** (§4, Tab. 1, Figs. 1/3), and it is the
one mechanism the literature record names as decisive (`literature/C0002_literature.md` §Q2.7:
"the percentile rank … and a length-controlled companion comparison must be co-reported, or the E2
conclusion is not defensible"). Unlike every control in §10 it carries **no measured expected
value** — the "verified achievable" discipline is simply absent for the whole §8.5 battery.

I measured a proxy, and it lands on the bar. Over 132 randomly sampled in-support cells (seed 1),
using an infix-token count for both the truth and each valid candidate and the draft's own
`±round(0.20·len_gt)` window:

- fraction of cells with **≥ 1** length-matched partner: **0.530** — against BA2's own
  `length_matched_partner_available_rate < 0.5` cutoff;
- mean per-cell fraction of candidates inside the window: **0.175**;
- **median per-cell count inside the window: 1**.

(`unverified` as an exact prediction — the real quantity uses model tokens via
`env.equation_encoder`, not infix tokens. Independent corroboration from the durable artifacts:
over 105 sampled in-support cells the GT prefix-token count has median **28** while candidate
`complexity` has a median-of-cell-**maxima** of **22**, i.e. in a typical cell the largest candidate
is smaller than the truth. The three dominant candidate classes are 2-term linear forms accounting
for 42,860 of 47,987 candidates.)

Two failures follow:

1. **The control may simply not run.** At an availability near 0.5 it is a coin flip whether the
   only length audit is `length_control_not_measurable`. And §13 triggers
   `E2_direction_observed_but_confounded` only when "BA2 **fails its disagreement bar**" — an
   unmeasurable control is neither a pass nor a fail, so **a supported E2 proceeds with the length
   confound entirely unaudited.** That is the C0001 defect in a new place.
2. **Where it does run it is degenerate.** With a median of one in-window candidate, `sb_best_len`
   reduces to comparing `lp_gt` against a single arbitrary candidate — which §5.1 itself identifies
   as the construction that would "fabricate" a direction. The >20% disagreement bar would then be
   tripped by window sparsity rather than by length bias, so neither firing nor not firing is
   informative.

**Required change.** (i) Measure `length_matched_partner_available_rate` and the in-window partner
count distribution **before freeze**, with the real tokenizer — this is leak-free, because it uses
only `candidate_token_length` and `gt_token_length` and touches no log-probability, and
`gt_token_length` is already on record for all 960 cells. (ii) Preregister a **minimum in-window
partner count** below which a cell contributes nothing, with its expected value stated. (iii) Make
`length_control_not_measurable` **block** a supported E2 (it should yield
`E2_direction_observed_but_length_unaudited`), not merely be reported. (iv) If the availability is
genuinely too low, adopt D19-1331's own Tab.-3 device instead (score against the best candidate at
the reference length; report sums and per-token means side by side as a declared side analysis,
never replacing the raw certificate). I am **not** proposing that the 0.5 bar be moved — the honest
consequence of a low availability is that the length confound is unauditable in this corpus and a
supported E2 is unavailable, and that must be said before compute is spent.

### CRITICAL-7 — the battery's blocking power is systematically anti-correlated with bias direction
**Anchor:** §8.5, §13.

Summarised in §A. Restating the required change as a single edit to §13: the E2-predominant branch
must require, conjunctively, that **BA1 did not fire**, that **BA2 both ran and passed**, and that
**BA4 did not show disagreement**. As drafted only the last of these is a condition. Without that
change the draft's own sentence "an E2 attribution that does not clear §8.5 is reported as
`E2_direction_observed_but_confounded`" is not implemented by §13.

---

## D. MAJOR findings

**MAJOR-1 — the bootstrap statistic's denominator is unspecified, and one reading is arithmetically
invalid.** §8.4 defines `P1 = Σ_s E3_system(s) / 71`; §12.1 says families are resampled. Whether the
resampled statistic is the ratio `Σ E3 / Σ n_f` or the fixed `Σ E3 / 71` is never stated. Simulated,
the fixed-denominator reading returns intervals **exceeding 1.0** (all-E3 corpus: [0.831, **1.127**];
90%: [0.746, **1.014**]) because resampled families have unequal sizes (10,10,10,10,10,10,4,7).
*Change:* name the statistic explicitly.

**MAJOR-2 — Holm is named but never operationalised, and is the wrong instrument.** §12.2 declares
"{P1, P2} … Holm-corrected at family-wise α = 0.05". The draft defines **no null hypothesis, no test
statistic and no p-value** for either endpoint (verified: the strings `p-value`/`p_value`/`alpha`
appear nowhere in the draft outside that one sentence), and §13's decision rules use **uncorrected**
95% one-sided interval conditions. The declared FWER of 0.05 is therefore not delivered by anything
in the document. Separately, the E2 rule is a conjunction of two one-sided conditions — an
intersection–union test, which attains level α with each component at level α and needs **no**
multiplicity correction; and the E3 and E2 branches are logically mutually exclusive
(`P1 LB > 0.5` and `P1 UB < 0.5` cannot both hold), so the multiplicity exposure is nearly nil.
*Change:* either define the two p-values and state how Holm modifies the intervals of record, or
delete Holm and replace §12.2 with the correct IUT argument plus a statement of the one-sided error
rate each branch carries. Do not leave a named correction that nothing implements.

**MAJOR-3 — "usable cells" is undefined, no per-system floor exists, and the /71 denominator is
hard-coded.** §8.1 defines "usable" for **candidates** only. §8.3 and §1.1 then aggregate "over the
system's usable cells" — a term with no definition. Cells can leave via `unreliable_reencoding`
(§8.2), `CellIdentityMismatch` (Gate 1) and, implicitly, `tie(c)`. Nothing states a minimum usable
cell count per system, and `P1 = Σ_s E3_system(s) / 71` hard-codes the nominal denominator, so a
system reduced to one usable cell still contributes a full system indicator, and a system with zero
usable cells silently contributes 0. **Direction matters:** `E2_system(s) = 1[sb_rate(s) = 0]`
becomes *easier* to satisfy as cells are lost, so cell attrition biases **P2 upward, toward E2**.
Expected attrition is ≈ 0 (§15), but this is exactly C0001's pattern — a nominal denominator of 130
whose realized value was at most 88. *Change:* define usable cell; preregister a per-system minimum
with its consequence (`system_not_evaluable`); report the realized per-system usable-cell
distribution; and make the P1/P2 denominator the **realized** evaluable-system count, reported
alongside the nominal 71, never a literal 71.

**MAJOR-4 — the 80 → 71 in-support filter is inherited from a criterion irrelevant to this
endpoint.** `partB_endpoints.json` states verbatim: "out of support is scoped to the preregistered
rewrite set B-R1..B-R4 (v2 §8.1); never claimed as out of support absolutely", and C0001 report §7.3
records `uses_only_in_support_operators` **True for all 9** excluded components; the design brief
§73 records GRN truths as "100% in-support" in the operator sense (F2, 560/560 round-trip).
C0001 itself computed `gt_logprob_sum` for all **960** cells. So nothing about the
log-probability endpoint requires this exclusion. It costs 9 systems and 108 cells (11%), and —
because the losses are concentrated in R07 (6) and R08 (3) — it is what drives the family sizes to
**4** and **7** and unbalances the very clusters CRITICAL-4 is about. It also silently narrows the
target population: §2.2 names "systems emitted by the R01–R08 generator", not "in-support systems",
and the filtering is not proportional across families, so the unweighted mean over 71 does not
estimate the population §2.2 names. *Change:* either restore the full 80 systems / 960 cells for
P1/P2 with in-support as a preregistered subgroup, or keep 71 and rewrite §2.2 to name the
in-support population as the estimand, stating that generalization beyond it is not licensed. State
which, before freeze, with the reason.

**MAJOR-5 — `H0010` reintroduces an unknown denominator through the CAS admission bound.** §9.1
applies `CAS_NODE_BUDGET = 400`; rows exceeding it are `budget_exceeded_by_input_size`, "counted and
reported". But such a class cannot be evaluated for `P_den`/`P_pow4`/`P_joint`, so it is excluded
from `n_class_joint` — and §15 lists its expected count as **"unknown"**. The exclusion deflates
`n_class_joint`, i.e. it pushes toward the prediction `≤ 5`. This is the one place in the draft
where an endpoint's denominator is not known by construction, which is the exact hazard §4 claims to
have eliminated. *Change:* `count_ops` over
`phase3/all_candidates.json` is CPU-cheap, leak-free (it reveals nothing about the three predicates)
and computable **before freeze** — measure the expected count now. Then preregister a bound-shaped
rule: if `n_class_joint ≤ 5` but `n_class_joint + n_budget_exceeded ≥ 6`, the verdict is
`H0010_undecidable_budget_limited`, not supported.

**MAJOR-6 — `H0010`'s thresholds are not derived, and two of the three are already satisfied.**
- `n_class_pow4 ≥ 10` is justified in §9.3 by C0001's published **11**. `P_pow4` (integer `|n| ≥ 4`
  over any variable-containing base) is a **superset** of C0001's nested-`pow2` Hill-4 classes, so
  11 is a lower bound and the bar of 10 is guaranteed to pass. H2 is a verification condition, not
  a prediction, and should be labelled so.
- `n_class_den > 0` likewise passes by construction from S1 `phi_denom`'s 5,824 / 77,983.
- `n_class_joint ≤ 5` vs `≥ 6` carries the entire scientific content and has **no stated
  derivation**. §9.3's defence — "this is the prediction, not a gate, so it needs no achievability
  proof" — is a non-sequitur: in a **census** there is no sampling variability to absorb the choice,
  so the cutpoint deterministically fixes the verdict. 5/846 = 0.59% and 6/846 = 0.71% are not
  distinguishable by any principle the draft offers.
*Change:* derive the cutpoint from a stated principle before freeze — a relative criterion matching
the hypothesis's own wording ("the joint is absent **while its marginals are realized**"), e.g. a
declared ratio to `min(n_class_den, n_class_pow4)` — or preregister a **graded** reading that states
in advance what conclusion follows in each band. I take no position on whether the principled value
lands above or below 5. Additionally, H4 (multiplicity-weighted over the 89,349 strings) is
`descriptive` with no rule, yet 5 rare classes and 5 classes covering a third of the corpus are
opposite findings: preregister that a class-level "supported" contradicted by the string-weighted
count is reported as a conflict, not as supported. (RD3 drops H4 entirely, removing the only
quantity that could contradict the class-level verdict — reconsider.)

**MAJOR-7 — the §8.5 gating quantities are cell-level, violating the draft's own frozen aggregation
order, and carry no interval method.** §2.1 freezes "within-system mean over usable cells → system
indicator → corpus rate" and states "a cell-level rate is **not** comparable to a system-level rate
and the two are never mixed". BA1 gates on the **median over cells** of `argmax_agreement_best`;
BA2 on disagreement over "> 20% of **those cells**"; BA3 on `encoding_flip_rate` = "fraction of
**cells**". All three gate the wording of a **system-level** conclusion. Cells are 12 corruption
variants of one truth, so a cell-level fraction has effective n far below 852 and is dominated by
systems retaining more cells. None of the three has a named interval method or a Monte-Carlo error
statement, yet each is compared to a hard threshold (0.95, 0.20, 0.05) with no rule for boundary
cases. *Change:* aggregate each audit to the system level before thresholding, and name an interval
(or state explicitly that the threshold is applied to a point estimate and what that costs).

**MAJOR-8 — BA3's consequence is a no-op, and the logsumexp is itself an unbounded lower bound.**
BA3's frozen consequence is "if `encoding_flip_rate > 0.05`, the single-encoding read is declared
invalid and **only** the logsumexp read is reportable" — but §7.2 already makes the logsumexp the
primary, so the consequence changes nothing that bears a decision. Meanwhile the mechanism BA3 names
is **not** removed by the logsumexp: `E(s)` is capped at 8 commutation-orbit members over `add`/`mul`
swaps plus `e1`/`e2`, while the set of semantically equivalent spellings (associativity,
distributivity, constant re-encodings, algebraically equivalent Hill forms) is far larger. `Δ_enc`
measures movement *within the enumerated set* and bounds nothing about the residual. §7.2's claim
that `Δ_enc` "is the measurement of this bias" overclaims. *Change:* give BA3 a consequence that
bites (e.g. a high `encoding_flip_rate` blocks a supported E2, since it demonstrates the endpoint is
sensitive to a nuisance whose full extent is unmeasured), and carry
`lp_gt_is_lower_bound_over_capped_enumeration: true` unconditionally on every artifact — not only
when the fallback to `e1` occurs.

**MAJOR-9 — BA1 firing should suspend the "not search" claim, not add a label.** If the median
`argmax_agreement_best ≥ 0.95` then `lp_best ≈ L*` and `sb_best = 1` was nearly unable to fire.
`P1 ≈ 0` then carries no information about search error — the E3 certificate had no opportunity.
The draft's consequence is the label `E2_conditional_on_near_greedy_reference`, which leaves the
conclusion "the failure is prior mass, **not search**" standing on an absence produced by the
instrument. *Change:* when BA1 fires, P1 is reported as `certificate_opportunity_insufficient`, the
"not search" half of `H0001-R` is declared unevaluable, and the reportable conclusion reduces to the
P2 certificate alone.

**MAJOR-10 — the §0.3 containment argument is broader than what it demonstrates, and §7.1
contradicts it.** §0.3 item 1 asserts "**No threshold in this document was chosen after, or in light
of, these values**". The supporting evidence covers only the rules inherited verbatim from v2.1
§8.3 (the 0.5 cutpoint, `E3_system`/`E2_system`, the clustered attribution rule) — a genuine and
well-documented defence for those. But the following thresholds are **new** to this draft and have
no stated derivation: BA1's 0.95, BA2's 0.20 window and >20% bar, BA3's 0.05, PC-GREEDY's ≥ 2/40,
`H0010`'s ≤ 5, `CAS_NODE_BUDGET` 400, the 20% `EncodingVerificationFailure` cap, and the ≥ 64/71
Gate-3b bar. **These are exactly the thresholds the observed direction could have influenced**,
because they are the ones that determine whether the preferred answer is policed.
Further, §7.1 states outright that the choice of `C_gen` as primary was made partly *because* the
exposure was under `C_raw` — and "the scoring contexts … and which is primary" is on §2.5's frozen
list. So a frozen design element **was** chosen in light of the observation, contradicting §0.3
item 1. (The choice is independently defensible on the F-g argument; the blanket claim is not.)
Finally, the containment argument is internally unstable: it says the `C_raw` exposure does not
contaminate the primary because the contexts differ, while BA4 exists precisely because the two
contexts might *agree or disagree* on the same attribution — with `lp_gt − lp_best` gaps of
100–500 nats on the 8 exposed cells, `sb_best` is very likely to agree across contexts, so the
primary indicator was, for practical purposes, observed on those 8 cells. *Change:* replace the
blanket claim with a per-threshold derivation table; state plainly that the primary-context choice
is post-observation and disclosed; and drop the "the primary quantity has never been observed"
framing in favour of "the primary quantity was not directly computed; the `C_raw` proxy was, on 8 of
852 cells, in the E2 direction".

**MAJOR-11 — the degenerate-bootstrap rule makes the interval of record discontinuous.** §12.1
substitutes Wilson-on-8-clusters only when all 8 clusters are *exactly identical*. Measured: at
exact degeneracy the interval of record is [0, 0.324] (width 0.324); one system away from
degeneracy the clustered bootstrap returns widths of 0.012–0.08. The width of the interval of record
therefore jumps by a factor of ~30 on an exact-equality test, and the **substitute is wider than the
procedure it substitutes for** — so the rule is not a conservative fallback but a discontinuity.
Resolving CRITICAL-4 largely dissolves this; if the clustered form is retained, the substitution
rule must be continuous (e.g. always report the more conservative of the two).

**MAJOR-12 — the literature's stated precondition for a defensible E2 is reported but forbidden from
bearing on it.** `literature/C0002_literature.md` §Q2.7: "The percentile rank of `lp_gt` within the
50 and a length-controlled companion comparison **must be co-reported, or the E2 conclusion is not
defensible**"; §Q2.4 item 2 calls the rank "the right mitigation … bias-free in a way the binary
indicator is not" and asks for it to be promoted to co-primary. The draft computes it (S8
`rank_pct_sum`) and then attaches the inherited v2.1 note "**no E2/E3 attribution may cite these**".
The v2.1 caution is itself sound (the 50 are an extreme upper-tail draw, so a low rank is not
evidence of model error). But the two requirements are in direct conflict and the draft resolves it
silently, in the direction that removes a check on the preferred answer. *Change:* the supervisor
must adjudicate before freeze and record the adjudication. As drafted, the gating input's own
condition for a defensible E2 is not met.

**MAJOR-13 — PC-GREEDY is a hard abort on the primary but its achievability evidence is from the
non-primary context and its evaluation context is unspecified.** §10.2's 2/10 probe was run under
`C_raw` ("on a disjoint 10-cell probe (`random.seed(4242)`, **`C_raw`**)"). Neither §10.2 nor Gate 4
says in which context the 40-cell gate is evaluated, and under `C_gen` the greedy decode must itself
run on the scaled/permuted conditioning for the comparison to be coherent ("from the cell's cached
encoder state" — which state is context-dependent). Operating characteristic at the frozen bar: with
a true rate of 0.20, `P(X ≥ 2 | n = 40)` ≈ 1.000; at 0.05 it is **0.601**, so a 40% abort
probability on the primary is live if the `C_gen` rate is materially lower than the `C_raw` probe.
*Change:* specify the gate's context (it should be the primary one), and either measure the probe
under `C_gen` before freeze or state the abort risk explicitly. Do not move the bar.

---

## E. MINOR findings

- **m-1** §12.1's "all 8 family clusters give the identical value" does not say whether "value" is
  the family count or the family rate. For the rate it is benign: with sizes {10, 4, 7} a common
  rate `v` requires `10v, 4v, 7v ∈ ℤ`, hence `v ∈ {0, 1}`, so the substitute Wilson has
  `x ∈ {0, 8}` and is well defined. That holds only by arithmetic accident of these family sizes and
  **would not survive RD2** (24-system panel). State the intended reading.
- **m-2** S2 and S3 are labelled "clustered" with no named method; S2 mixes a **cell-level** rate
  into a section whose other members are system-level. Name the estimator or drop the interval.
- **m-3** P2's name `certified_non_argmax_system_rate` is defined through `sb_rate(s) = 0`, i.e.
  through `sb_best`, not through `me_best`. It equals the non-argmax certificate only if tie cells
  are removed from the `sb_rate` denominator, which §8.1 implies ("excluded from both") but §8.3
  does not state. Ties are expected ≈ 0 (exact float equality requires the truth's encoding to equal
  a candidate's token sequence, and truth-in-beam is 0/960), so this is a wording fix, but the
  endpoint name currently promises a certificate the formula does not compute.
- **m-4** §14's `H0010` census is the only unmeasured compute component and is bounded only by the
  Gate-5 projection. Given MAJOR-5 requires a pre-freeze `count_ops` pass anyway, take the timing
  from it.
- **m-5** §19's replication gate fires on "an E2 or E3 corpus attribution". After CRITICAL-3 the
  word "attribution" should be replaced throughout, including here.

---

## F. Reproduction

Environment: `source /home/blabo/miniconda3/etc/profile.d/conda.sh && conda activate lansr310`.
All reads were read-only; no draft, C0001 artifact or run artifact was modified; no sealed path was
opened.

| finding | computation |
|---|---|
| §B.1 denominators | count over `results/runs/gpu_run5_20260823_ddd267b0/phase3/cells/*.json` intersected with `results/runs/gpu_runclaude1_c0001_b731cdd/phase2/partB_in_support_systems.json` |
| §B.5, CRITICAL-4/5 Wilson | closed-form Wilson, z = 1.959963985 |
| CRITICAL-4 coverage | 500 reps × B = 600, systems iid Bernoulli(p) within the 8 fixed families of sizes (10,10,10,10,10,10,4,7), numpy default_rng(11) |
| CRITICAL-4/5 widths, MAJOR-1 | 10,000 resamples, default_rng(20260911), ratio and fixed-denominator variants |
| CRITICAL-6 availability | 132 in-support cells sampled with `random.seed(1)`; infix-token regex `[A-Za-z_]\w*|\d+\.?\d*|[-+*/()|,^]` applied to `true_formula` and to each `valid` candidate's `candidate_formula_raw`; window `±round(0.20·len)` |
| CRITICAL-6 corroboration | 105 in-support cells, `random.seed(1)`: GT prefix-token count vs candidate `complexity` |
| MAJOR-4 | `results/runs/gpu_runclaude1_c0001_b731cdd/phase2/partB_endpoints.json` note field; `GPU_RUNclaude1/reports/C0001_report.md` §7.3 |
| §B.4 53.62% / 51.8% | `GPU_RUNclaude1/literature/C0002_literature.md:96-97, :169-170, :204` |
| §B.3 no `student_t_ci` | repository-wide grep excluding `results/` |

---

## G. Verdict

**The draft may not be frozen as written.** The realized-denominator discipline that C0001 lacked is
genuinely present and verifies exactly, and §10's control battery honours the MAJOR-R6 lesson. But
the primary endpoint's certificate is broken by its own encoding fix (CRITICAL-1), the E2 decision
rule reads a one-sided bound backwards in a way that contradicts the draft's own §8.7
(CRITICAL-2), the E2/E3 framing is not logically exclusive (CRITICAL-3), the interval of record
contradicts the declared estimand and undercovers at 0.876–0.904 while running up to 17× narrower
than the unclustered interval (CRITICAL-4/5), and the bias-audit battery's blocking power is
inversely arranged with respect to the direction of the known biases (CRITICAL-6/7).

**A supported-E2 conclusion would not be defensible under this contract.** It could become
defensible if: the E2 branch rests solely on P2; BA1, BA2 and BA3 acquire blocking consequences;
BA2's availability is measured before freeze and a minimum in-window partner count is preregistered;
the interval of record matches §2.2's estimand; and the conclusion is stated as two independent
certified lower bounds rather than as one attribution. None of those changes requires moving a
threshold to make a result more likely, and none requires additional compute beyond a leak-free
pre-freeze tokenizer pass and a `count_ops` pass.

The `H0010` companion is closer to sound — it correctly refuses sampling inference on a census — but
needs a derived cutpoint (MAJOR-6) and a bound-shaped rule for budget-excluded classes (MAJOR-5)
before it can bear a verdict.
