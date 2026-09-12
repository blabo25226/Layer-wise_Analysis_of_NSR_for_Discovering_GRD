# C0001 — Stage 9 Independent Adversarial Review

- Reviewer: `lansr-independent-reviewer` (this document). Distinct from implementation
  (`lansr-implementation-engineer`), primary analysis (`lansr-results-analyst`), statistical review
  (`lansr-statistical-reviewer`) and the supervisor, per `.claude/rules/07-independent-review.md`.
- Binding contract: `GPU_RUNclaude1/plans/C0001_preregistration_v2.1.md` / `.json` only.
  v1 and v2 are superseded and not cited.
- Run of record: `results/runs/gpu_runclaude1_c0001_b731cdd`
  (phase0 manifest commit `b731cddd168390c973dbb0974349e4a2c55b9113`,
  phase1/2/3 manifest commit `8ff622defc227b4598e0094fc000b8227c4ffdad`).
- Branch `20260909_researce_GPU_RUNclaude1`. Review begun at HEAD
  `34da7fc107f280ac3f867dde0daf199e161c1a0a`; finalized at HEAD `029fe12` after the supervisor
  landed `c4bbf16 "Retract the CPU-contention mechanism for the timeout count"`, which falsified
  the mechanism my own §1.5 first draft asserted. §1.5 is corrected accordingly.
- **Load disclosure.** The supervisor was running its own timeout measurement concurrently with
  mine on the same 12-core host (1-minute load average 7.8–13.3 during my §1.4 arm, recorded per
  repetition). My repetitions are therefore *not* an idle-host measurement, which matters for the
  mechanism question and not for the reproducibility question (§1.5).
- **Nothing frozen was modified.** No threshold, cap, cutpoint, seed or timeout was changed.
  `SYMPY_OP_TIMEOUT_SEC` remained `10.0` in every measurement below.
- **No sealed artifact was read.** Every path I opened is under
  `results/runs/gpu_runclaude1_c0001_b731cdd/phase{0,1,2,3}/` or
  `results/runs/gpu_run5_20260823_ddd267b0/phase3/cells/*_validation_*.json`; none begins with
  `sealed` (`src/gpu_runclaude1/io_allowlist.py:81 is_sealed_path`). `load_sealed_test` was never
  called. Measurement scripts live in the session scratchpad, never in the repository.
- Everything below was recomputed from raw artifacts. Where I reproduce a number that an existing
  analysis also reports, I say so; I did not take any number from a summary.

---

## 0. Bottom line

| Claim under attack | Verdict |
|---|---|
| 1. Part A's verdict of record is `undecidable` | **SURVIVES** — but for a different and narrower reason than the cycle documents give, and only *for the run of record*. See §1. |
| 2. M0 ≡ M3 pointwise on 101,963 triples, symmetric difference 0 | **SURVIVES as arithmetic, FAILS as evidence.** In stratum H only **187 of 77,983** triples (**9 of 130** components) were even comparable, and M3 matched **none** of them, so the identity there is 77,983 forced double-zeros. See §2. |
| 3. E1' explains at most 9/170 components | **SURVIVES**, with the scope tightened to 9/130 H components and to one operationalization. Hill-4 spelling verified correct. See §3. |
| 4. The Gate B→C violation caused no scientific damage | **SURVIVES on damage, FAILS on residue.** See §4. |
| 5. Supervisor reliability discount | **Not uniform.** The two load-bearing conclusions are unaffected; the retraction discipline is sound and I **withdrew** both residue findings I drafted. See §5. |

**Recommendation: `REPLICATE` (blocking), then `ACCEPT_AS_PRELIMINARY` for the instrument facts
only.** C0001 may write its mandatory cycle report — the report is mandatory even for an
undecidable cycle (`.claude/rules/08-cycle-persistence.md`) — but it **may not** close as a cycle
whose primary endpoint carries a verdict. Two independent reasons, either sufficient:
`undecidable` held in only 6 of my 8 contract-compliant repetitions of the frozen instrument
(**CRITICAL-R1**), and the primary endpoint had no realized trial on **121 of its 130** analysis
units (**CRITICAL-R2**).

New CRITICALs raised here: **CRITICAL-R1** (the endpoint is a function of wall-clock time under an
unpinned execution), **CRITICAL-R2** (no realized opportunity — the quantity the statistical
review's CRITICAL-2 says was never measured; I measured it), **CRITICAL-R3** (`lp_sel` at
`candidate_index == 0` cannot measure search error, because the beam was **sampled**, not searched —
this binds C0002's decision endpoint). Six new MAJORs, two MINORs, five NOTEs. One finding of my own
withdrawn mid-review (§1.5) and two drafted findings withdrawn (§5.3).

---

## 1. PRIORITY — is the timeout count reproducible?

### 1.1 What the run recorded (independently recomputed, not read from a summary)

I re-derived the entire endpoint chain from the 960 files in
`results/runs/gpu_runclaude1_c0001_b731cdd/phase1/cell_cache/` plus
`phase1/component_strata.json`, with no reference to `partA_endpoints.json`:

| quantity | my recomputation | stored |
|---|---|---|
| scored (cell, candidate, component) triples | 101,963 | 101,963 (`constants.py:70`) |
| `match_outcome_m3` census | `proved_different` 99,719 / `could_not_evaluate` 9 / `matched` 2,235 | — |
| `failure_reason` census | `SymbolicEquivalenceTimeout` × 9, **nothing else** | — |
| `\|H\|` / `\|L\|` | 130 / 40 | 130 / 40 |
| `K` | **0** | 0 |
| `K_adversarial` | **6** | (implied by `sensitivity_agrees: false`) |
| `could_not_evaluate_rate` | 9/77,983 = **0.00011540976879576318** | 0.00011540976879576318 |
| `m3_level_h` / `m3_level_l` / `m3_level_overall` | 0.0 / 0.325 / 0.07647058823529412 | identical |
| A2-S6b (`m0_any=1 ∧ m3_any=0`) | **0** | not stored |

The 9 could-not-evaluate triples are exactly the 9 named in the task. Their 6 affected H components
are `R03_validation_d101_005/0`, `R05_validation_d101_000/1`, `R07_validation_d101_000/1`,
`R07_validation_d101_002/2`, `R07_validation_d101_003/1` (×2 triples),
`R07_validation_d101_009/2` (×3 triples); all six have `m0_any = 0`, `m1_any = 0`, `m3_any = 0`.
So the stored artifact is internally consistent and the arithmetic of the pivot is correct.

### 1.2 First correction: the pivot is not "9 vs ≤3". It is "≥1 vs 0"

The task briefing (and, in a weaker form, the statistical review's MAJOR-3) states that a re-run
yielding **≤ 3** affected components would give `sensitivity_agrees = true` and the verdict
`no_gain_observed_bound_only`. **That is wrong**, and it matters.

`src/gpu_runclaude1/ladder.py:44 ladder_verdict` has **three** rungs, not two:

```
if k == 0:      return "no_gain_observed_bound_only"
if k <= c:      return "weak_gain"
                return "matcher_attributable_gain_confirmed"
```

The non-match direction is `K = 0` ⇒ `no_gain_observed_bound_only`. Any `K_adversarial ∈ {1,2,3}`
is `weak_gain` — **a different rung**. §7.5 item 3 ("if the two land on different ladder rungs, the
verdict is `undecidable`") therefore fires on **one** could-not-evaluate triple anywhere in the
77,983 H triples, not on four. The design is a hair trigger, not a near-miss.

Consequences:

- The statistical review's **MAJOR-3 is understated**: its sentence "Disagreement requires only 4
  touched components" (`C0001_partA_statistical_review.md:437`) is false. Its conclusion — that
  §7.5 item 2's middle branch is practically unreachable — is nevertheless **right, and stronger
  than it argues**: the middle branch is unreachable *deterministically*, not merely in
  expectation, whenever `K = 0`. Recorded as **MAJOR-R3** below.
- The whole cutpoint arithmetic (`C = ceil(0.02·130) = 3`) is irrelevant to this cycle's verdict.
  Every cycle-document sentence of the form "6 > C = 3, so the rung moves" is a true statement
  about an inessential fact.

### 1.3 My measurement — serial, one fresh process per triple, frozen 10.0 s guard

I re-ran the 9 stored triples through the exact frozen path
(`evaluation.equation_metrics.skeleton_equivalence_with_reason` on
`gpu_run4.formulas.parse_system(..., as_prefix=False)["components_raw"][i]`, both sides infix per
rule R1), each in its own forked process so the SIGALRM guard is genuinely live, 3 repetitions,
one at a time. Raw inputs from `results/runs/gpu_run5_20260823_ddd267b0/phase3/cells/`.

| triple (cell / cand / comp) | rep0 | rep1 | rep2 |
|---|---|---|---|
| `R03_validation_d101_005_b2_n0p05_r0` / 14 / 0 | 2.61 s, decided | 2.55 s, decided | 2.61 s, decided |
| `R05_validation_d101_000_b2_n0p05_r0p5` / 9 / 1 | 2.40 s, decided | 2.38 s, decided | 2.39 s, decided |
| `R07_validation_d101_000_b1_n0_r0` / 47 / 1 | 2.40 s, decided | 2.38 s, decided | 2.41 s, decided |
| `R07_validation_d101_002_b2_n0_r0p5` / 16 / 2 | 3.45 s, decided | 3.47 s, decided | 3.47 s, decided |
| `R07_validation_d101_003_b0_n0_r0p5` / 35 / 1 | 2.45 s, decided | 2.47 s, decided | 2.43 s, decided |
| `R07_validation_d101_003_b2_n0_r0p5` / 19 / 1 | 2.51 s, decided | 2.55 s, decided | 2.69 s, decided |
| `R07_validation_d101_009_b0_n0_r0` / 6 / 2 | 11.70 s, **decided** | 14.68 s, **TIMEOUT** | 14.80 s, **TIMEOUT** |
| `R07_validation_d101_009_b1_n0_r0` / 12 / 2 | 4.68 s, decided | 3.45 s, decided | 4.75 s, decided |
| `R07_validation_d101_009_b1_n0p05_r0` / 29 / 2 | 6.28 s, decided | 4.13 s, decided | 4.11 s, decided |

"decided" = `failure_reason is None`. **In every one of the 27 completed comparisons the decided
value was `skeleton = 0.0`, i.e. `proved_different`.** Eight of the nine triples never timed out;
one timed out in 2 of 3 repetitions.

Two facts follow that no cycle document establishes:

1. **8 of the 9 could-not-evaluate outcomes are recoverable *inside* the frozen instrument.** The
   Stage 8 analysis lists as `unverified` ("§7 item 1") whether these 9 would become
   `proved_different` if the comparison completed, because it (correctly) refused to raise the
   timeout. It does not need to be raised: under this execution the frozen 10.0 s guard is simply
   not reached, and the comparison returns a **decided non-match**. So for at least 8 of the 9
   triples there **exists** a contract-compliant execution in which the adversarial arm's premise —
   count these as matches — is directly contradicted by the same instrument on the same inputs.
   This does not establish that all 9 are decided non-matches under every execution (they are not:
   `R07_009/6/2` timed out in 2 of 3 repetitions here), only that the adversarial recount is
   presuming a match for comparisons the instrument itself can and does decide the other way.
2. Note the 11.70 s "decided" cell. Total elapsed can exceed 10.0 s without a timeout because
   `skeleton_equivalence_with_reason` has **four** independent 10 s budgets per call
   (`_to_skeleton_with_reason` ×2 sides, `_timed_simplify(sk_true − sk_pred)`, `_timed_equals`).
   Elapsed wall time is therefore not a proxy for margin-to-timeout.

### 1.4 My measurement — the run's own 6-worker configuration

The run used `score_cells_parallel(..., n_workers=6)`. I re-scored the **9 cells** that carried the
9 stored timeouts (1,250 component comparisons per repetition) through `multiprocessing.Pool(6)`,
frozen timeout unchanged.

| rep | n_timeout | wall | p99 per-triple | timed-out triples |
|---|---|---|---|---|
| 0 | **6** | 150.8 s | 4.18 s | `R05_000_b2_n0p05_r0p5`/9/1, `R07_000_b1_n0_r0`/47/1, `R07_003_b0_n0_r0p5`/35/1, `R07_003_b2_n0_r0p5`/19/1, **`R07_009_b0_n0_r0`/42/2**, **`R07_009_b1_n0p05_r0`/44/2** |
| 1 | **4** | 86.9 s | 2.63 s | `R07_002_b2_n0_r0p5`/16/2, `R07_003_b2_n0_r0p5`/19/1, `R07_009_b0_n0_r0`/6/2, **`R07_009_b1_n0_r0`/13/2** |

Bolded triples are **not** among the run's 9: they are candidates 42 and 44 of
`R07_validation_d101_009_b0/b1`, and candidate **13** (not 12) of `R07_009_b1_n0_r0`. Meanwhile
stored timeouts `R03_005/14/0`, `R07_002/16/2`, `R07_009/6/2`, `R07_009/12/2` did **not** time out
in rep0, and `R03_005/14/0`, `R05_000/9/1`, `R07_000/47/1`, `R07_003/35/1`, `R07_009/29/2` did not
in rep1.

**The set of could-not-evaluate triples is not reproducible at all.** Only its order of magnitude
is. Reducing to affected H components: rep0 touches 4 components (`R05_000/1`, `R07_000/1`,
`R07_003/1`, `R07_009/2`) ⇒ `K_adversarial = 4 > 3` ⇒ upper rung; rep1 touches 3
(`R07_002/2`, `R07_003/1`, `R07_009/2`) ⇒ `K_adversarial = 3` ⇒ **middle** rung `weak_gain`.
Both differ from `K = 0`'s lower rung, so both give `undecidable` — but by way of *two different
adversarial rungs*, and this is only 9 of the 960 cells.

### 1.5 The decisive finding: the verdict is a function of execution details the contract does not pin

**Corrected 2026-09-11, before this review was final.** My first draft of this section asserted that
the driver is the **worker count**, since v2.1 §3 (`:666`) freezes Part A parallelism as
"process-based, **≤ 6** worker processes" — an upper bound, not a value — and my serial arm (§1.3)
and 6-worker arm (§1.4) differ. **I withdraw the mechanism, and keep the finding.**

Why I withdraw it. My two arms are **confounded**: the serial arm forked a fresh process **per
triple** (maximally cold SymPy cache), while the 6-worker arm reused each worker process across a
whole 50-candidate cell (a progressively warming cache). Parallelism and cache warmth moved
together, so my data cannot separate them. Independently, the supervisor ran the controlled version
of exactly this question — the same 9 triples scored under 0 vs 6 *competing* processes, 6
repetitions each — and reports a mean flipped-component count moving only 1.5 → 1.67, i.e. **CPU
contention is rejected**, with SymPy cache state supported instead
(`GPU_RUNclaude1/analyses/C0001_endpoint_irreproducibility.md`, whose own first edition asserted the
contention mechanism and retracts it). I have not re-derived their numbers and do not adopt them; I
cite the control because it falsifies **my** mechanism, which is the correct use of another agent's
result in an adversarial review.

What survives, from my measurements alone:

- **The verdict is not stable across contract-compliant executions.** Lower rung
  (`no_gain_observed_bound_only`, i.e. zero could-not-evaluate triples in H) occurred in **1 of 3**
  serial repetitions and **1 of 5** six-worker repetitions — `undecidable` in **6 of my 8**
  repetitions overall. "Roughly one execution in five returns a different verdict" is the honest
  statement; my earlier draft's "coin flip" overstated it and is withdrawn.
- **The mechanism is `unverified`.** Candidates: SymPy cache occupancy at the moment a comparison
  runs, process granularity, memory pressure after 47,987 candidates' worth of cache fill, host
  load. Contention alone is rejected. What is *certain* is the shape of the dependence: a
  `signal.setitimer(ITIMER_REAL, 10.0)` wall-clock alarm (`equation_metrics.py:21,36-53`) makes the
  endpoint a function of elapsed time, and elapsed time is not a property of the data.
- **The one arm that faithfully reproduces the run's own execution is mine.** The run scored 960
  cells with `Pool(6)`, each worker taking whole cells; §1.4 does the same on the 9 affected cells.
  It reproduces the run's magnitude (0–6 triples, 0–4 flipped components against the run's 9 and 6)
  where a 9-isolated-pair design does not. Scoring 9 pairs in isolation is not the instrument that
  produced the artifact, and any mechanism study should be run at cell granularity.
- **The contract still fails to pin the execution.** Whatever the mechanism, `≤ 6 workers` plus a
  wall-clock guard plus "any non-zero `cne_rate` triggers the sensitivity analysis" plus a
  three-rung ladder means the *contract does not determine its own verdict*. That is the finding,
  and it does not depend on which of the candidate mechanisms is responsible.

### 1.6 What survives the PRIORITY finding

- The verdict of record **for the run of record** is `undecidable`. §7.5 item 3 is mechanical, the
  run recorded 9 could-not-evaluate triples in H, and one is enough (§1.2). Claim 1 survives.
- It survives as a statement about *this execution*, not about *this experiment*. The mandatory
  cycle report must state that a compliant re-execution can return a different rung, and must not
  present `undecidable` as a property of the data.
- **`K = 0` is unaffected.** All 9 triples have `m0_any = 0` and, when decided, `m3 = 0`; none can
  become a gain. Every quantity that does not pass through the CAS is deterministic: M0's exact
  reproduction, the M0/M3 set identity, Part B's 9/170, PC4's 100/170.

### 1.7 Full measurement table (5 repetitions, 6 workers, 9 of 960 cells)

| rep | n_timeout | affected H components | `K_adversarial` | adversarial rung | verdict this execution would carry |
|---|---|---|---|---|---|
| 0 | 6 | 4 (`R05_000/1`, `R07_000/1`, `R07_003/1`, `R07_009/2`) | 4 | `matcher_attributable_gain_confirmed` | `undecidable` |
| 1 | 4 | 3 (`R07_002/2`, `R07_003/1`, `R07_009/2`) | 3 | `weak_gain` | `undecidable` |
| 2 | **0** | **0** | 0 | `no_gain_observed_bound_only` | **`no_gain_observed_bound_only`** |
| 3 | 3 | 3 (`R07_002/2`, `R07_003/1`, `R07_009/2`) | 3 | `weak_gain` | `undecidable` |
| 4 | 5 | 3 (`R05_000/1`, `R07_002/2`, `R07_009/2`) | 3 | `weak_gain` | `undecidable` |

Per-repetition wall clock 86.9–150.8 s; host `nproc` 12; 1-minute load average 7.8–13.3 during the
measurement (other campaign work was concurrent, which is itself the point — the run of record was
produced on the same shared host).

Note the second-order instability: the *adversarial rung* itself moves between `weak_gain` and
`matcher_attributable_gain_confirmed` across compliant executions, so the run of record's
"lower rung vs **upper** rung" framing is one realization of at least three.

**PRIORITY answer.** The stored count of 9 is **not** reproducible, and neither is the stored
*set*. Over 5 compliant 6-worker repetitions on the 9 affected cells I measured **6, 4, 0, 3, 5**
timeouts, with a different set every time, including five triples (`R07_009_b0/42/2`,
`R07_009_b1_n0p05/44/2`, `R07_009_b1_n0p05/45/2`, `R07_009_b1_n0/13/2`, `R07_002_b2/35/2`) that are
not among the run's 9 at all. Serially, with a fresh process per triple, 8 of the 9 never timed out
and all 27 completed comparisons returned `proved_different`.

Three things follow, and the third is the one the briefing got wrong:

1. The count is a random variable in [0, ~6] on these cells; the run's 9 across 960 cells sits at
   the high end of that but is not an outlier.
2. Because **one** could-not-evaluate triple in H suffices (§1.2), `undecidable` is far more robust
   than a "9 vs ≤3" framing implies: it held in **6 of my 8** repetitions. The verdict of record is
   the modal outcome, not a fluke.
3. It is nonetheless **not the deterministic outcome**: 2 of my 8 repetitions reached zero, which
   yields `sensitivity_agrees = true` and `no_gain_observed_bound_only`. So C0001's verdict of
   record is a property of an execution, not of the experiment — while being the *likely* property
   of a re-execution. Both halves must be reported.

---

## 2. Claim 2 — M0 ≡ M3 pointwise, symmetric difference 0

### 2.1 The arithmetic reproduces exactly

Recomputed over all 101,963 triples from `phase1/cell_cache/`, the joint `(m0, m1, m3)` distribution
has exactly two occupied cells:

| `(m0, m1, m3)` | count |
|---|---|
| (0.0, 0.0, 0.0) | 99,728 |
| (1.0, **0.0**, 1.0) | 2,235 |

`|M0 \ M3| = |M3 \ M0| = 0` at triple, cell×component (107 = 107), ANY-reduced component (13 = 13)
and system (0 = 0) resolution. `|M0 \ M1| = 2,235`; `|M1| = 0` at every resolution.
All 47,987 candidates have `valid: true` and `component_count_match: true`, so no candidate was
excluded. **The claim is arithmetically correct.** So is the statistical review's CRITICAL-2 census.

### 2.2 But how many opportunities did M3 actually have? — the measurement CRITICAL-2 says was never made

The statistical review's CRITICAL-2 states: "the number of rewrite-class opportunities actually
present in the beam — the real `n_eff` for E0 — was never measured." I measured it, two ways.

**(a) Rigorous necessary condition for an M3 match.** M3 returns 1.0 only if the two *skeletons*
are equal **as expressions** in (x, c) (`equation_metrics.py:216-222`: `simplify(sk_true − sk_pred)
== 0` or `sk_true.equals(sk_pred)`). A truth skeleton with a variable in a denominator cannot equal
a candidate skeleton with no variable in any denominator, for any constant assignment. This
condition is invariant under algebraic rewriting — `sympy.together`, affine decomposition and
operand commutation all preserve it — so it is a genuine necessary condition, not a heuristic. I
screened every triple for a variable-bearing denominator (`inv`, `div` right child, `pow` with
negative exponent) on both sides:

| stratum | M3 structurally **blocked** | M3 **possible** | total |
|---|---|---|---|
| **H** | **72,132 (92.50%)** | **5,851 (7.50%)** | 77,983 |
| L | 0 | 23,980 | 23,980 |

Component-level, over the primary's own denominator: **88 of the 130 H components have ≥ 1
M3-possible triple; 42 of 130 have none at all** — no candidate in any of the 12 cells' 50-candidate
beams carries a variable-bearing denominator, so `m3_any = 0` was structurally forced for those 42,
not measured.

**(b) Necessary condition for M0/M1, and the empirical support of every realized match.** M0's
`exponent_aware_skeleton` and M1's `canonical_exact` only collapse numeric literals; neither adds
or removes an operator node. Screening on equality of the component's operator multiset:

| | operator multiset **equal** (comparable) | **unequal** | of which matched |
|---|---|---|---|
| all triples | **2,466 (2.42%)** | 99,497 (97.58%) | 2,235, **all** inside the comparable set |
| stratum **H** | **187 (0.24%)** | 77,796 | **0** |
| stratum L | 2,279 | 21,701 | 2,235 |

Component-level: **9 of the 130 H components have ≥ 1 comparable triple; 121 of 130 have none.**
The screen has **zero observed false negatives**: every one of the 2,235 realized M3 matches lies
inside the comparable set. It is nevertheless not logically necessary for M3 — PC4 demonstrates M3
matching across `sympy.together` rewrites, which do change the operator multiset — so I report
(a) and (b) as a **bracket**, not a point.

### 2.3 What that does to the claim, and to the intervals built on 130

The primary's realized effective denominator is bracketed at **[9, 88] of 130 components**, not 130.

| assumed `n_eff` | Wilson(0, n) | power at E0's own `p = 0.0525` | power at `p = 0.02` |
|---|---|---|---|
| 130 (as reported in `partA_endpoints.json:wilson_95`) | [0, **0.028702**] | **0.99910** | 0.92766 |
| 88 (M3-possible components) | [0, **0.041827**] | 0.99131 | 0.83100 |
| 9 (comparable components) | [0, **0.299145**] | **0.38452** | 0.16625 |

At the tight end of the bracket the design was **not powered against the magnitude E0 itself
specifies**, independently of the ICC argument that produces the statistical review's CRITICAL-3
bracket [0.3504, 0.9991]. The two mechanisms are different (clustering vs. structural
non-comparability) and they degrade the same number, so they do not compose to something better.

**Verdict on Claim 2: SURVIVES as arithmetic, FAILS as evidence.** In the stratum the primary
endpoint is defined on, `M0 ≡ M3` is a statement about **77,983 double zeros**, of which 72,132 are
provably forced and at least 77,796 are unreachable by either matcher's normalization. There is
**no** H triple on which M3 matched, so there is no H triple on which the identity distinguishes
M3 from any other matcher that also returns 0 there — including a matcher that always returns 0.
The informative part of the identity is entirely in stratum L (2,235 concordant positives), and
stratum L **cannot contribute to `K` at all** (all 13 L components with `m3_any = 1` have
`m0_any = 1`, so `gain ≡ 0` there by definition).

This is **CRITICAL-R2**. It does not overturn the statistical review's CRITICAL-2 — it supplies the
missing number and shows CRITICAL-2 was, if anything, **understated**: it argued that `K = 0` was
not a Bernoulli draw; the measurement shows the trial was not run on 121 of 130 components.

### 2.4 Was the M3 pinning what actually ran? Yes, by code identity — stronger than the test says

`matcher.py:139` calls `skeleton_equivalence_with_reason(true_raw[index], cand_raw[index])`, not
`symbolic_recovery(...)["skeleton"]`. Reading `equation_metrics.py:241`, `symbolic_recovery`'s own
`"skeleton"` value is *literally the first element of that same call's return tuple* on
whitespace-stripped inputs, and `skeleton_equivalence_with_reason` strips its own arguments. The two
are therefore identical **by construction**, not merely by the 1,178-pair agreement test
(`phase0/m3_agreement_test.json`: `n_disagreements: 0`) or the 480-pair in-pass census
(`phase1/m3_implementation_agreement_census.json`: `n_disagreements: 0`). No other key of
`symbolic_recovery` reaches any endpoint. **Pinning verified.**

Two side facts confirming v2.1's own §7.5 accounting: `symbolic_recovery` builds its return dict
eagerly, so the `equiv` block at `:245-253` does run and does burn wall clock — but it cannot alter
`["skeleton"]`, and its `except Exception: equiv = skeleton` swallows `_SymTimeout` without touching
M3. Correct as v2.1 §7.5 item 1 describes.

### 2.5 Can an exception path return 0 and be counted as a *decided* non-match? Yes — one hole

`matcher.py`'s module docstring asserts "there is no code path in this module that returns a bare,
unlabelled non-match", and v2.1 §7.5 item 1 freezes a taxonomy on that basis. **There is one.**

```
if _timed_equals(sk_true, sk_pred): return 1.0, None
return 0.0, None                    # reason None -> matcher.py PROVED_DIFFERENT
```

`_timed_equals` is `bool(a.equals(b))` (`equation_metrics.py:62-65`). `sympy.Expr.equals` returns
`True`, `False`, **or `None`** when it cannot decide. `bool(None)` is `False`, so an *undecided*
comparison is recorded as a **decided non-match** with `failure_reason: None`, is classified
`proved_different` by `_outcome_for_skeleton`, and is **excluded from the
`could_not_evaluate_rate` numerator**. Direction of the error: it inflates `proved_different`,
deflates `could_not_evaluate` — **anti-conservative for a null-shaped endpoint**, the same failure
mode `research_state.md` §8 item 8 already records for the `formulas.py` CAS path.

I measured the realized rate. Mirroring the frozen logic in a local copy (frozen modules untouched,
timeout untouched) and recording the **raw** `.equals` return on a seeded random sample of 60 cells
× 12 candidates = **1,476 triples**: `diff_zero` 11, `equals_False` 1,465, **`equals_None` 0**.

So the hole did not fire in this sample. Wilson 95% on 0/1,476 is **[0, 0.0025959]**, which over
101,963 triples admits up to **≈ 265** silently-undecided triples. Given §1.2 (one
could-not-evaluate triple in H flips the verdict), an unmeasured surface of that size is material.
Recorded as **MAJOR-R1**; the measured point estimate is zero and I do not claim it fired.

---

## 3. Claim 3 — "E1' explains at most 9/170 components"

### 3.1 The Hill-exponent spelling did **not** cause a false absence — verified three ways

This was the specific worry, and it is discharged.

1. `partB_component_records.jsonl`, `realized_hill_exponents` over the 170 validation components:
   `(2,)` × 18, `(2,2)` × 18, `(2,2,2,2)` × 3, `(4,)` × 18, `(4,4)` × 18, `(4,4,4,4)` × 3,
   `()` × 92. **Exponent 4 is detected in 39 of 170 components** — exactly the 39/170 the
   retraction record (`C0001_RETRACTION_neg_finding.md`) says survives.
2. `src/gpu_runclaude1/partb.py:143 realized_hill_exponents` walks the **parsed tree** and derives
   the exponent from nested `pow2`/`pow3` chain depth. No surface-token search exists in the module;
   its docstring names the retracted mistake and forbids it. `pow4` appears nowhere.
3. The SymPy-side counterpart is handled too:
   `count_non_identity_unary_generator_equivalent` (`:88-115`) charges a folded `pow(base, n)`
   node the `_implied_pow2_applications(n)` cost (4 → 2), so `U_affine` cannot silently undercount
   relative to `U_mult`. Both spellings of Hill-4 — prefix `pow2,pow2,x_i` and the SymPy-evaluated
   `pow(x_i, 4)` — are priced identically.

**No false absence.** The retracted-mistake class is closed here.

### 3.2 Is `in_support` a fair operationalization? I attacked it and it held

`in_support = (U_min ≤ 3)` (`partb.py:390`) matches the frozen §8.1 definition (`v2.1:1279`)
verbatim. My attack: `MAX_BINARY_OPS_PER_DIM = 5` and `MAX_UNARY_DEPTH = 7` are imported by
`partb.py` but never enter the decision, and the measured `binary_ops_per_dim` distribution over the
170 validation components is `{3: 40, 5: 60, 6: 20, 7: 30, 8: 10, 10: 10}` — **70 of 170 components
carry more binary operators than the generator's own `max_binary_ops_per_dim = 5`, yet are labeled
`in_support`.** That looks like an over-generous support test.

It is not. Reading the official generator
(`GitHubSourceCode/ODEFormer/odeformer/envs/generators.py:594-612`): `nb_binary_ops` bounds the
**skeleton before decoration**; `add_prefactors` / `add_linear_transformations` then add further
`add`/`mul` nodes, and the function *re-counts* `nb_binary_ops_to_use` from the decorated prefix
afterwards. So a final tree with 7 or 10 binary nodes is reachable and the binary budget is
correctly **not** a support constraint. By contrast `add_unaries` (`:627-639`) *trims* unaries down
to `nb_unaries ≤ max_unary_ops_per_dim` and nothing adds unaries later, so the unary cap **is** a
hard cap on the finished tree. `U_min ≤ 3` is the right binding constraint. `uses_only_in_support_operators`
is `True` for all 170 (non-binding) and `unary_depth ≤ 3 < 7` (non-binding). **Claim survives this attack.**

One residual asymmetry, recorded as **MINOR-R1**: `add_unaries` trims on `x in self.unaries`, and
`self.unaries` includes `id` (`operators_to_use = "…id:3…"`, `generators.py:389`), so the
generator's real cap is on unaries *including* `id`. `U_mult` counts only non-identity unaries
(`_NON_IDENTITY_UNARY = UNARY_OPS - {"id"}`), a **weaker** necessary condition. v2.1 `:1297`
declares Part B's one-sidedness to be "over-report out-of-support, never under-report" (§14 item 3);
this particular asymmetry runs the **other** way. Net direction is `unverified` — B-R3's omission
pushes the declared way, the `id` accounting pushes against it — so the claimed one-sidedness is
not established, only asserted.

### 3.3 Where the claim needs tightening

- The measured values are `B2-S1` 9/80 systems (`rate 0.1125`, Wilson [0.06033, 0.20018]) and
  `B2-S2` 9/170 components (`rate 0.052941`, Wilson [0.02810, 0.09754]). I reproduced both.
- **All 9 out-of-support components are in stratum H** (cross-tabbing
  `partB_component_records.jsonl` against `phase1/component_strata.json`): `R07_*/2` × 6
  (`_001, _002, _004, _005, _007, _008`) and `R08_*/2` × 3 (`_002, _005, _008`). L is 40/40
  in support. So the number that matters for the primary is **9 of 130 H components (6.9%)**,
  not 9 of 170. B2-S7 (the H/L cross-tabulation §7.8 requires) is **absent from every artifact**;
  I had to compute it. Recorded as **MINOR-R2**.
- The claim must not be read as "E1' explains at most 9". It is: *under the frozen B-R1..B-R4
  rewrite set and the unary-budget criterion*, at most 9 H components are excluded by the
  generator's **operator budget**. Being inside the operator budget is a necessary, not sufficient,
  condition for the truth to be reachable: it says nothing about the checkpoint's probability mass
  (E2) or the beam's reach (E3). `partB_endpoints.json`'s own note says exactly this ("never
  claimed as out of support absolutely"), and the Stage 8 analysis §3.6 item 5 keeps the E1'/E2/E3
  attribution `unverified`. **Claim 3 SURVIVES as written and scoped**, provided the report carries
  the 9/130 framing and the necessary-not-sufficient caveat.
- Interaction with §2.2 worth stating plainly: of the 121 H components with **zero** comparable
  candidate anywhere in the beam, only 9 are out of the generator's operator support. So **112 H
  components are inside the generator's declared support and still had no structurally comparable
  candidate in a 50-wide beam across 12 conditioning cells.** That is the cycle's most informative
  measured fact, it is consistent with E2/E3 rather than E1', and it is not stated in any artifact.

---

## 4. Claim 4 — "the Gate B→C violation caused no scientific damage"

### 4.1 What I verified about the damage envelope

| question | finding |
|---|---|
| Did Part C touch a sealed artifact? | **No.** `phase0/firewall_test.json`: `sealed_paths_read: []`, `sealed_paths_read_count: 0`, `allowlist_has_no_sealed_path: true`, `known_sealed_files_count: 7`. `phase3/partC_cell_records.jsonl` covers exactly the 960 **validation** cells. |
| Was `C2-P` computed? | **No.** `partC_cell_records.jsonl` carries only `cell_id`, `excluded`, `cell_input_payload_sha256`, `gt_logprob_sum`, `gt_token_length`. No `lp_sel`, no `lp_best`, no `sb_sel`, no `sb_best`, no `search_error_system_rate`. `stahlberg_byrne_indicator` was never invoked. The DEVIATION record's claim is correct. |
| Compute consumed | ≈ 1 min GPU, peak 0.454 GiB VRAM against a 5.5 GiB ceiling (`phase3/manifest.json`, `gpu_telemetry.jsonl`). |
| Does any artifact or document cite a Part C number? | **No.** `grep -rn "gt_logprob"` over `GPU_RUNclaude1/**.md` returns only the DEVIATION record's statement that the field exists and the three preregistrations' field lists. No analysis, review or state file quotes a value. |
| Is the gate now mechanically closed? | **Yes, and correctly.** `scripts/phases/gpu_runclaude1_c0001_phase3_partc.py:41 _verdict_of_record` derives the verdict from `sensitivity_agrees is False` rather than trusting the stored `verdict` field, so it refuses even on the un-corrected artifact; `:109` refuses on any `undecidable*` prefix; `:80-85` refuses when `phase1/partA_component_summary.json` is absent (it is), i.e. a missing artifact is a refusal, not an assumed pass. Correct direction on all three. |
| Is "not a §6 hard stop" defensible? | **Yes.** `.claude/rules/09-human-intervention-policy.md` lists wrong branch, destructive change, private data, credential change, **unavoidable test leakage**, major ceiling increase, unsafe hardware, ethics/licensing. A preregistered-gate violation is none of them, the branch was correct, nothing was destroyed, and the firewall shows no leakage. The judgement holds. |

So on **damage**, Claim 4 survives.

### 4.2 Where it fails: the retention is right, the labelling of the retained artifact is not

Retention is correct — `.claude/rules/01-research-integrity.md` items 4 and 5 require preserving
null, negative and invalid output, and deleting `phase3/` would destroy the only primary evidence
that the violation occurred. But the retained artifact is **not** machine-legibly inadmissible:

- `phase3/gate_b_to_c.json` still records `"ok": true, "reasons": [], "part_a_verdict":
  "no_gain_observed_bound_only"`. Two of those three fields are wrong under the contract.
- `phase3/manifest.json` still records `"status": "complete"` with `go_conditions` all true and **no
  inadmissibility field**.
- The only inadmissibility marker is `phase3/INADMISSIBLE.md`, a prose file that no manifest,
  checksum list or `go_conditions` block points at.

A consumer reading manifests — the normal machine path, and the one an artifact-curation or
synthesis agent will take — sees a complete, gate-passed phase 3. This is the **same** failure the
cycle already identified as CRITICAL-1 for `partA_endpoints.json` ("labels travel downstream and
caveats do not", v2.1 §9.3), reproduced one directory over and not yet fixed. **MAJOR-R2.**

### 4.3 Where it fails second: the forward-leakage exposure is real, just small

`gt_logprob_sum` now exists for all 960 validation cells, and its distribution has been observed by
the campaign. Under `.claude/rules/02-test-and-data-leakage.md` this is **not** test leakage —
validation is the legitimate selection surface and the sealed set was untouched. But it is a
**hidden-tuning surface for the next preregistration**: any future absolute threshold on `lp_gt` (a
per-token CE cutoff, a "non-negligible probability" bar for E2) would be chosen with the answer
already visible.

Mitigating: v2.1's own E2/E3 endpoints are **paired comparisons** (`sb_sel = 1[lp_gt > lp_sel]`,
`sb_best = 1[lp_gt > lp_best]`, and the paired `lp_gt − lp_sel` of C2-S3), and none of the
comparison partners was computed, so the discriminating quantity was not observed. The exposure is
to an *absolute* threshold only.

**Required disclosure for C0002's preregistration** (I am recording this as a MAJOR because it is
cheap now and unfixable later): C0002 must state that the `lp_gt` distribution over the 960
validation cells was observed before freezing, and must either keep every E2/E3 endpoint
paired/comparison-based or label any absolute threshold on `lp_gt` **exploratory**. **MAJOR-R3.**

### 4.4 The counterfactual that makes the mechanical fix non-optional

The violation was harmless *because* Part C happened to read only validation cells. The gate that
failed is the same class of gate that stands between a phase and a restricted artifact. A gate
implemented from a summary rather than the contract's own text (the DEVIATION record's own root
cause) that fails open is a hard-stop generator in a future cycle, not a bookkeeping error. The
mechanical fix plus `GPU_RUNclaude1/tests/test_gate_b_to_c.py` is therefore the right response and
must not be downgraded because this instance was benign.

**Verdict on Claim 4: SURVIVES on damage, FAILS on residue.** Nothing scientific is contaminated;
the machine-readable record still says the opposite of the truth.

---

## 5. Claim 5 — how much should the supervisor's three false negatives discount each conclusion?

### 5.1 The error pattern, and why it is not symmetric

Three retracted supervisor findings this cycle, all from **unvalidated comparison methods**:

| # | retracted claim | mechanism of the error | direction |
|---|---|---|---|
| 1 | Hill-4 absent | searched a **canonicalized string** for a surface token `pow4`; the real spelling is `pow2,pow2,x_i` / `pow,pow,x_i,2,2` | false **absence** |
| 2 | "107/2040 structural matches the frozen matcher scored as misses" | compared a **prefix**-derived truth skeleton against **infix**-derived candidate skeletons; re-derived a value `beam_groups.json` already published | false **absence** (baseline 0/2040 was the artifact) |
| 3 | "5 of 60 B-R1 rewrites are not identities" | naive `simplify(a − b) == 0` on `Float` coefficients; max residual 3.33e-16, one exactly 0 | false **non-identity** |

All three are **false negatives of a comparison** — the method said "different / absent" when the
truth was "same / present". The primary endpoint is `K = 0`, i.e. also "M3 found nothing". **The
supervisor's demonstrated error direction and the cycle's headline result point the same way.**
`research_state.md` already flags this as an R5 validity threat that the C0001 report must disclose;
I confirm the flag and sharpen it.

### 5.2 How much discount each conclusion actually earns

The discount is **not** uniform, because the conclusions do not all rest on a comparison method the
supervisor wrote.

| conclusion | rests on | discount |
|---|---|---|
| M0 exact reproduction (47,987 / 101,963 / 2,235 / 0-of-960 / 107-of-2040, 8 family values) | GPU_RUN5's **own stored fields**, matched field-by-field; deterministic | **none.** This is a positive control against published values, correctly labelled as such under rule R1. I reproduced the triple and match counts independently. |
| `K = 0` | the same code path PC4 fires 100/170 on; every affected triple has `m0_any = 0` | **none from this failure mode.** PC4 is the correct guard and it is non-vacuous. |
| M0 ≡ M3 identity | a comparison, but one whose *positive* side (2,235 concordant matches) is verified against GPU_RUN5's stored `component_exponent_aware_skeleton_exact` | **moderate** — and superseded by §2, which shows the identity is uninformative in H regardless of whether it is correct. |
| Part B's 9/170 | analytic tree census, no CAS, no string search, both Hill-4 spellings priced (§3.1) | **low.** This is the one place where the supervisor's own error class was specifically engineered against, and I verified the engineering works. |
| the 9 timeouts / the `undecidable` verdict | a wall-clock lottery, not a comparison method | **not applicable** — but see §1, which is a *worse* problem. |
| PC2c/PC2d 170/170 as evidence of M3 invariance sensitivity | short-circuited controls with empty non-short-circuited subsets | **total.** Already CRITICAL by both Stage 8 documents; I concur (§6, MAJOR-R4). |

**The honest summary is not "discount everything by a constant".** It is: every C0001 conclusion
that rests on a *supervisor-authored comparison* is discounted, and the cycle's two load-bearing
conclusions (M0 reproduction, `K = 0` conditional on PC4) do not. The genuinely load-bearing
weaknesses this cycle are the ones in §1 and §2, neither of which is a supervisor false negative.

### 5.3 Retraction completeness — I looked for residue and found none

I drafted two residue findings and **withdraw both after checking the primary files**. Recording the
withdrawal rather than deleting it, per `.claude/rules/15-document-language.md`'s retraction rule.

- **Withdrawn RESIDUE-1.** I expected the withdrawn documents to be unmarked at their heads. They
  are not. Both `GPU_RUNclaude1/analyses/C0001_exploratory_neg_canonicalization.md:3-12` and
  `GPU_RUNclaude1/analyses/C0001_stage1_preobservation.md:3-11` open with an identical blockquote
  banner ("**RETRACTED IN PART — see `C0001_RETRACTION_neg_finding.md`**") naming the false claim,
  the prefix-vs-infix mechanism, the already-published 107/2040 value and the consequence for E0,
  before any content. `human_review_queue.md` HRQ-0002 carries a dated **訂正** paragraph doing the
  same. No reader can reach the withdrawn claim without the retraction.
- **Withdrawn RESIDUE-2.** I expected `C0001_pc2b_discrepancy_resolution.md`'s summary table to show
  the retracted `55` unqualified. The table cell itself reads
  `**55** ← この値は撤回済み。正しくは **60**`, with the full account below. Correct pattern.

**One residue does exist and is harmless.** `GPU_RUNclaude1/plans/C0001_preregistration.md:269`
still records `C-M0c ... 0/2040` — but that is **v1**, superseded, and v2.1 replaces it with
`107/2040 = 0.0525` while explicitly annotating it "**This is the frozen matcher's own value.** Not
an artifact, not a discovery, not a floor at zero" (`v2.1:187`) and deleting the derived quantity
that rested on the retracted claim (`v2.1:698`). No live contract carries the retracted number.

**Assessment: the retraction discipline in this cycle is good.** All three retractions are dated,
name the mechanism, name the discoverer, state what survives, and are propagated to every document
the retraction record itself lists. This is the part of the supervisor's conduct that most
mitigates §5.1.

### 5.4 One derivation worth flagging, unrelated to the retractions

The frozen effect size `GAIN_RATE_EFFECT_SIZE = 0.0525` (`constants.py:61`) is M0's **own**
component hit rate (107/2040), used as the magnitude the primary's **gain** (M3 match ∧ M0 miss)
must reach. Those are different estimands, and v2.1 admits the ANY-reduced counterpart "is **not
identified**: admissible range [0.053, 0.629]" (`:681`, V2-MAJ-4). Combined with §2.2 this becomes
sharp: under the operator-multiset screen the **maximum attainable** `K` on this corpus is 9, so the
maximum attainable gain rate is 9/130 = **0.0692**, only 1.32× the target 0.0525. A design whose
observable ceiling is 1.3× its target effect size cannot cleanly distinguish "no effect" from "no
room for the effect". **MAJOR-R6.**

---

## 6. Are the Stage 8 CRITICALs right? Overstated? Understated?

| finding | my assessment |
|---|---|
| Stage 8 **CRIT-1** / statistical **CRITICAL-1** (stored `verdict` ≠ contract verdict) | **Correct and correctly rated CRITICAL.** Verified: `partA_endpoints.json:primary.verdict = "no_gain_observed_bound_only"` with `sensitivity_agrees: false`; v2.1 `:1809` lists sensitivity disagreement as an `undecidable` trigger. `src/gpu_runclaude1/endpoints.py` was corrected in commit `34da7fc` **after** the run (artifact mtime 18:33, commit 19:17), and **the artifact was not regenerated**, so the defect is still live on disk. Also: `sensitivity_verdict_non_match_direction` / `_match_direction` exist on `PrimaryEndpointResult` but are still not persisted by `scripts/.../phase1_parta.py`, so the two rungs remain unrecoverable from artifacts alone. **Not overstated.** |
| Stage 8 **CRIT-2** / statistical **MAJOR-7** (null-branch gate void under §7.7.1) | **Correct.** The two documents rate the *same* finding CRITICAL and MAJOR respectively. I side with **MAJOR**: PC4 is the §7.7.3 hard-abort control, it is non-vacuous (gain 100/170, `gain_h` 100, 6 families, `gates_ok: true`), and PC0 is 170/170. The null branch is not uncontrolled; its *invariance-sensitivity* coverage is vacuous. Recorded as **MAJOR-R4** to settle the split. |
| Stage 8 **CRIT-3** (Part C ran under a gate violation) | **Correct.** See §4. |
| Statistical **CRITICAL-2** (no realized discriminating power) | **Correct and UNDERSTATED.** It says the opportunity count "was never measured"; §2.2 measures it at **[9, 88] of 130 components** and 187 / 5,851 of 77,983 H triples. |
| Statistical **CRITICAL-3** (circular power fallback, family-clustered power uncomputed) | **Correct.** I verified no family-clustered power figure exists in any phase-1 artifact and that the ICC = 1 bracket endpoint is 0.3504 at p = 0.0525. §2.3 adds a *second, independent* route to the same degradation (0.38452 at `n_eff = 9`). |
| Statistical **MAJOR-3** (§7.5 item 3 scale-mismatched against `C = 3`) | **Conclusion right, mechanism WRONG and understated.** Its "Disagreement requires only 4 touched components" (`:437`) is false: `ladder_verdict(1..3) = "weak_gain" ≠ "no_gain_observed_bound_only"`, so **one** touched component suffices whenever `K = 0`. The middle branch of §7.5 item 2 is unreachable *deterministically*, not in expectation. Recorded as **MAJOR-R3-correction**. |
| Statistical **MAJOR-4** (verdict non-deterministic) | **Correct and UNDERSTATED.** It says a faster host "could" give an empty set. §1 measures it: the set is different on *every* repetition, and a 6-worker repetition produced **zero** timeouts. It also stops short of the decisive point — that `≤ 6 workers` is unpinned, so the verdict is a function of a free contract parameter (**CRITICAL-R1**). |
| Stage 8 **MAJ-3** / statistical **MAJOR-2** (`could_not_evaluate_rate` denominator) | **Correct.** Reproduced: implementation gives 9/77,983 = 0.00011540976879576318 (H only); §7.5 item 2's denominator is all scored triples, 9/101,963 = 0.0000882673126526289. Gate outcome unchanged; the reported number is not the frozen quantity. |
| Stage 8 **MAJ-6** (adversarial recount can flip `m0_any = 1` components) | **Correct, latent.** `endpoints.py:117-127` flips on `n_could_not_evaluate > 0 ∧ gain == 0` without re-checking `m0_any == 0`. Did not fire: L has zero could-not-evaluate triples and all 13 `m0_any = 1` components are in L. |
| Stage 8 **MAJ-7** (monotonicity audit never checks M0→M3) | **Correct.** `audit_monotonicity` checks only M0→M1 and M1→M3; `|M1| = 0` identically, so the M1→M3 leg is vacuous. `A2-S6b = 0` and `|M0 \ M3| = 0` appear in no artifact; I recomputed both. |
| Statistical **MAJOR-9** / Stage 8 **MIN-1** (`monotonicity_severity: "CRITICAL"` inside `go_conditions`) | **Correct.** Verified the string is present in `phase1/manifest.json:go_conditions` and that no code gates on it. |
| Statistical **MINOR-1** (severity string not internally well-defined) | **Correct.** `n_checked` counts units, violations count checks; the same data reads CRITICAL / MAJOR / CRITICAL under the three defensible denominators (2,235/149,950 = 0.014905, 2,235/299,900 = 0.0074525, 2,235/101,963 = 0.021920). |

Nothing in either Stage 8 document is **overstated**. Two things are understated (statistical
CRITICAL-2 and MAJOR-4), and one mechanism is wrong (statistical MAJOR-3's "4").

---

## 7. `lp_sel`, `select_candidate`, and the §8.3 citation defect

The task's reading — that v2.1 §8.3 (`:645`, `:1202`) cites `gpu_run5_selection.py:11
formula_selection_key`, which is a cross-run model-selection scorer grouped by `(system_id, seed)`
and not a per-cell candidate selector, while the actual per-cell selector
`src/gpu_run5/evaluation.py:107 select_candidate` returns `0` unconditionally under
`"official_reconstruction"` — is **correct**. I confirm both readings from the source.

**But adopting index 0 is not thereby justified, and I found a stronger reason to distrust it.**

1. `results/runs/gpu_run5_20260823_ddd267b0/phase3/config_snapshot.json`:
   `paper_protocol.beam_type = "sampling"`, `beam_temperature = 0.1`, `beam_size = 50`
   (mirrored in `src/gpu_runclaude1/constants.py:41-43`).
2. In the official implementation, **only** the `beam_type == "search"` branch sorts hypotheses by
   score: `GitHubSourceCode/ODEFormer/odeformer/model/model_wrapper.py:107-113`
   (`sorted(..., key=lambda s: s[0], reverse=True)`). The `"sampling"` branch (`:135-175`) returns
   the samples in **sampling order**, unsorted.
3. No per-candidate score or log-probability is stored anywhere in
   `phase3/cells/*.json` (candidate keys are structural/TED/trajectory fields only).

Therefore **`candidate_index == 0` is the first sampled hypothesis, not the model's argmax and not
"the search's own output".** Consequences:

- **Material to `lp_sel` and hence to C2-P, decisively.** `sb_sel(c) = 1[lp_gt(c) > lp_sel(c)]`
  (v2.1 `:1414`) is a Stahlberg–Byrne search-error indicator, which is only meaningful when
  `lp_sel` is the log-probability of *what search returned*. With `lp_sel` = log-prob of an
  arbitrary temperature-0.1 sample, `sb_sel` measures "is the truth more likely than a random
  sample", which for a peaked decoder is nearly always true — **it would inflate
  `search_error_system_rate` toward 1 and manufacture E3**. C2-P would not be a search-error rate.
- The right `lp_sel` is `lp_best` — the max over usable candidates — or a re-decode under
  `beam_type = "search"`. v2.1 already defines `lp_best` (`:1413`) and reports `sb_best` alongside;
  under sampling, `sb_best` is the defensible indicator and `sb_sel` is not.
- **Nothing in C0001 is contaminated**, because `lp_sel` was never computed (§4.1). This is
  entirely a C0002 preregistration item.
- It also mislabels a Stage 8 number: `C0001_partA_stage8_analysis.md` §3.2 reports "selected
  (`candidate_index == 0`) 58/2040" against "oracle 107/2040" and reads the gap as **"45.8%
  (49/107) of in-beam structural matches do not reach top-1 — a selection loss"**. Under sampling
  order there is no top-1, so that sentence asserts a selection failure where the measurement
  supports only "the first sample is not the best sample" — exactly the generation/selection
  confusion rule 03 and the `symbolic-regression-evaluation` skill forbid. The *number* 58/2040
  is fine as "first-sampled candidate"; the *interpretation* is not. **MAJOR-R5.**

Recorded as **CRITICAL-R3** for the forward path (it defines the next cycle's decision endpoint)
and **MAJOR-R5** for the current mislabel.

---

## 8. Rule 01 crossings checked

| rule 01 item | check | result |
|---|---|---|
| 1/2 — validation selects, no tuning after final-test access | No sealed artifact read (`phase0/firewall_test.json`); no threshold, cap, cutpoint, seed or timeout changed after results. `endpoints.py` was changed post-run (commit `34da7fc`) but **toward** the frozen §7.5 item 3 rule, not away from it, and it moves the verdict from a favourable rung to `undecidable`. | **clean** |
| 3 — no hypothesis/metric/seed/exclusion change to rescue | No exclusions: 47,987/47,987 candidates `valid: true`, 0 `ComponentCountMismatch`, 0 cell failures (`partA_cell_failures.json` = `[]`). No metric changed. The timeout was explicitly **not** raised. | **clean** |
| 4/5 — preserve null, negative, invalid | 9 timeouts enumerated with expressions; `phase3/` retained under `INADMISSIBLE.md` rather than deleted; three retractions preserved in place. | **clean** (see MAJOR-R2 on machine-legibility) |
| 6 — numerical fit is not symbolic recovery | Stage 8 §3.2 keeps them apart quantitatively: top-of-list `input_r2` median 0.954, `generalization_r2 > 0.9` in 306/960 cells, against system-level symbolic recovery 0/960 and H-component recovery 0/1,560. Good practice, and the strongest passage in the analysis. | **clean** |
| 7 — symbolic recovery is not biological causality | No GRN/biological claim anywhere; corpus is the synthetic R01–R08 Hill generator. `.claude/rules/04` layer questions: none measured, and Stage 8 §3.1 says so explicitly. | **clean** |
| 8 — non-significance is not equivalence | Stage 8 §9 and the statistical review both state that M0 ≡ M3 on real data is **not** an equivalence claim, citing PC4's 100/170. §2 of this review adds the reason it also is not *evidence*. The `cluster_bootstrap.ci_high: 0.0` in `partA_endpoints.json` is the live hazard — the bound of record was correctly switched to family Wilson [0, 0.3244], but the `[0,0]` bootstrap still sits in the artifact unlabelled (statistical MAJOR-1, confirmed). | **clean in the analyses, hazardous in the artifact** |
| 9 — exploratory labelled | Stage 8 labels its numeric skeleton-difference probe, its power correction and its clustered-power bracket exploratory. The `neg` canonicalization document is titled `EXPLORATORY`. This review's own §1.3/§1.4 re-scoring is **exploratory** and outside the frozen instrument: it does not replace any endpoint. | **clean** |
| 10 — novelty needs literature verification | No novelty claim is made in any C0001 artifact I read. | **clean** |
| rule 03 — generation / oracle / selected kept distinct | Kept distinct in form, but the "selected" leg is mislabelled — see §7 / MAJOR-R5. | **defect** |
| rule 04 — layer-importance questions not averaged | No layer quantity measured at all; nothing to average. | **clean** |

Test suite at review-time HEAD: **467 passed, 1 skipped** (the skip is the optional DREAM4 archive).

---

## 9. Findings

### CRITICAL

**CRITICAL-R1 — the frozen contract does not determine its own verdict: the primary endpoint is a
function of elapsed wall-clock time.** `evaluation/equation_metrics.py:21,36-53` guards every SymPy
call with `signal.setitimer(ITIMER_REAL, 10.0)`, so `could_not_evaluate_rate` depends on how long a
comparison happens to take, which is not a property of the data. v2.1 §3 (`:666`) then leaves the
execution unpinned ("process-based, **≤ 6** worker processes" — a bound, not a value), and §7.5
item 3 triggers on **any** non-zero rate while `ladder_verdict(1..3) = "weak_gain" ≠
ladder_verdict(0)` (§1.2), so a **single** such triple in H changes the verdict. Measured (§1.3,
§1.4, §1.7; frozen timeout untouched): counts **6, 4, 0, 3, 5** over 5 six-worker repetitions and
**0, 1, 1** over 3 serial repetitions, with a **different set every time** and five timed-out
triples that are not among the run's 9. `undecidable` held in **6 of my 8** repetitions and the
lower rung in **2 of 8**. **The mechanism is `unverified`** — I withdraw my own CPU-contention
attribution (§1.5); a controlled 0-vs-6 competing-process experiment rejects contention and
supports SymPy cache state, and my two arms confound parallelism with cache warmth.
**Blocks a supported conclusion**, because the verdict may not be reported as a property of the
experiment. Remedy: a new preregistration that (a) pins the execution configuration and (b)
redefines `could_not_evaluate` on a **deterministic** budget — node count or operation count —
instead of wall clock. **Not** a raised timeout.

**CRITICAL-R2 — the primary endpoint had no realized trial on 121 of its 130 analysis units, so
`M0 ≡ M3` is uninformative in the stratum the primary is defined on.** Measured over all 101,963
triples (§2.2). Rigorous necessary condition for an M3 match (variable-bearing denominator on both
sides, invariant under `together`/affine/commutation rewriting): **72,132 of 77,983 H triples
(92.50%) are structurally blocked**; only **88 of 130** H components have even one M3-possible
triple. Necessary condition for M0/M1 (operator-multiset equality, satisfied by **all** 2,235
realized matches, zero observed false negatives): only **187 of 77,983 H triples (0.24%)** are
comparable, and only **9 of 130** H components have one. The reported `wilson_95: [0.0, 0.028702]`
and the §7.3 power 0.99910 at `p = 0.0525` assume `n = 130`; at the bracket's tight end
(`n_eff = 9`) they are **[0, 0.299145]** and **0.38452**. **Blocks any supported conclusion.** The
reportable content is the opportunity census itself plus PC4's demonstration that M3 *can* gain —
an instrument characterization, not evidence about E0.

**CRITICAL-R3 — `lp_sel` as implemented cannot measure search error, and C2-P is the next cycle's
decision endpoint.** v2.1 §8.3 cites `gpu_run5_selection.py:11 formula_selection_key` as "the frozen
selection rule"; that function is a cross-run model-selection scorer grouped by
`(system_id, seed)`, not a per-cell selector (contract defect, correctly identified). The adopted
substitute — `src/gpu_run5/evaluation.py:107 select_candidate(..., "official_reconstruction")`
returning index 0 — is **not** the search's own output: the stored candidates were decoded with
`beam_type = "sampling"`, `beam_temperature = 0.1`
(`phase3/config_snapshot.json`, `constants.py:41-43`), and only the `"search"` branch of
`GitHubSourceCode/ODEFormer/odeformer/model/model_wrapper.py:107-113` sorts by score; the
`"sampling"` branch (`:135-175`) returns samples unsorted, and **no per-candidate score or log-prob
is stored anywhere in `phase3/cells/*.json`**. `sb_sel = 1[lp_gt > lp_sel]` with `lp_sel` = log-prob
of an arbitrary temperature-0.1 sample would inflate `search_error_system_rate` toward 1 and
manufacture E3. **Nothing in C0001 is contaminated** (`lp_sel` was never computed), but C0002 must
not freeze this. Defensible options: use `lp_best` / `sb_best`, or re-decode under
`beam_type = "search"`. `unverified`: whether any GPU_RUN5 artifact anywhere records a per-candidate
model score that would make index 0 recoverable as the argmax.

I concur with the two Stage 8 CRITICALs that stand: **CRIT-1** (stored `verdict` ≠ contract verdict;
still live on disk — `endpoints.py` was fixed in `34da7fc` at 19:17 but `partA_endpoints.json` has
mtime 18:33 and was never regenerated) and **CRIT-3** (Part C ran under a gate violation). I
downgrade Stage 8 **CRIT-2** to MAJOR-R4 (below), agreeing with the statistical review's rating.

### MAJOR

**MAJOR-R1 — the failure taxonomy has one unlabelled non-match surface, and it is anti-conservative
for a null.** `equation_metrics.py:216-222` ends `if _timed_equals(...): return 1.0, None` /
`return 0.0, None`, and `_timed_equals` is `bool(a.equals(b))` (`:62-65`). `sympy.Expr.equals`
returns `True`/`False`/**`None`**; `bool(None)` is `False`, so an **undecided** comparison is
recorded as `proved_different` with `failure_reason: None` and is excluded from the
`could_not_evaluate_rate` numerator — contradicting `matcher.py`'s docstring ("there is no code path
in this module that returns a bare, unlabelled non-match") and v2.1 §7.5 item 1's completeness
claim. Measured rate on a seeded sample of **1,476** triples (60 cells × 12 candidates), raw
`.equals` return recorded, frozen modules untouched: `diff_zero` 11, `equals_False` 1,465,
**`equals_None` 0**. Wilson 95% on 0/1,476 = **[0, 0.0025959]**, i.e. up to ≈ **265** silently
undecided triples over 101,963. Given that one such triple in H flips the verdict (§1.2), the
surface must be labelled, not assumed empty. Point estimate is zero; I do not claim it fired.

**MAJOR-R2 — the inadmissible phase-3 artifact is not machine-legibly inadmissible.**
`phase3/gate_b_to_c.json` still records `"ok": true, "reasons": [], "part_a_verdict":
"no_gain_observed_bound_only"`; `phase3/manifest.json` still records `"status": "complete"` with all
`go_conditions` true and no inadmissibility field. The only marker is the prose
`phase3/INADMISSIBLE.md`, which no manifest, `go_conditions` block or checksum list references. This
is v2.1 §9.3's own hazard ("labels travel downstream and caveats do not") reproduced one directory
over. Remedy: add an explicit inadmissibility field to `phase3/manifest.json` and reference
`INADMISSIBLE.md` from it; retain all data.

**MAJOR-R3 — C0002 must disclose that the `lp_gt` distribution was observed before freezing.**
`phase3/partC_cell_records.jsonl` now carries `gt_logprob_sum` and `gt_token_length` for all 960
validation cells, produced under a gate violation. This is not test leakage (validation, and
`sealed_paths_read: []`), and no artifact quotes a value, but it is a hidden-tuning surface for any
**absolute** threshold on `lp_gt` in a future preregistration. v2.1's own E2/E3 endpoints are paired
(`sb_sel`, `sb_best`, `lp_gt − lp_sel`) and their comparison partners were never computed, so the
exposure is confined to absolute thresholds. C0002 must state the observation and keep E2/E3
endpoints paired, or label any absolute `lp_gt` threshold **exploratory**.

**MAJOR-R3-correction — the statistical review's MAJOR-3 mechanism is wrong.**
`C0001_partA_statistical_review.md:437` states "Disagreement requires only 4 touched components".
`ladder.py:44-52` has three rungs; `K_adversarial ∈ {1,2,3}` is `weak_gain`, already a different
rung from `K = 0`'s `no_gain_observed_bound_only`. **One** touched component suffices. The finding's
conclusion (§7.5 item 2's middle branch is unreachable) is therefore right and *stronger* than
argued — deterministic rather than in expectation — but the stated number must be corrected before
it is quoted in the cycle report or the PR body.

**MAJOR-R4 — the null branch has no valid invariance-sensitivity gate (settling a CRITICAL/MAJOR
split).** v2.1 §7.7.1 forbids gating on a control whose non-short-circuited subset is empty; §7.7.3
places the null-branch gate on exactly PC2c/PC2d, which `partA_controls.json` records as
`170/170 short_circuited by canonical_exact` with empty non-short-circuited subsets. Stage 8 rates
this CRITICAL; the statistical review rates it MAJOR. I rate it **MAJOR**, because PC4 — the
§7.7.3 hard-abort control — is non-vacuous (`gain_total 100`, `gain_h 100`, 6 of 8 families,
`gates_ok: true`) and PC0 is 170/170. PC2c/PC2d's 100% **may not** be cited as evidence that M3 is
sensitive to invariance rewrites, and no artifact says so.

**MAJOR-R5 — "selection loss" is asserted where the measurement cannot support it.**
`C0001_partA_stage8_analysis.md` §3.2 reads oracle 107/2040 vs "selected (`candidate_index == 0`)"
58/2040 as "45.8% (49/107) of in-beam structural matches do not reach top-1 — a selection loss".
Under `beam_type = "sampling"` there is no top-1 (CRITICAL-R3), so the measurement supports only
"the first sampled candidate is not the best sampled candidate". This is the
generation-vs-selection confusion that rule 03 and the `symbolic-regression-evaluation` skill
forbid. The number 58/2040 is fine relabelled as *first-sampled*; the interpretation is not.

**MAJOR-R6 — the corpus's attainable ceiling is only 1.32× the target effect size.**
`GAIN_RATE_EFFECT_SIZE = 0.0525` (`constants.py:61`) is M0's own component hit rate (107/2040), used
as the magnitude the *gain* must reach; v2.1 `:681` concedes the ANY-reduced counterpart "is **not
identified**: admissible range [0.053, 0.629]". Under §2.2's operator-multiset screen the maximum
attainable `K` is **9**, so the maximum attainable gain rate is **9/130 = 0.0692**. A design whose
observable ceiling is 1.32× its target cannot separate "no effect" from "no room for the effect".

I additionally **confirm** these already-recorded MAJORs from my own recomputation: `could_not_evaluate_rate`
denominator 9/77,983 vs the contracted 9/101,963 = 0.0000882673126526289 (Stage 8 MAJ-3 /
statistical MAJOR-2); the absent §9.5 items 0/1/6 and §9.3 verbatim sentences (MAJOR-1); the absent
family-clustered power (CRITICAL-3); the latent `m0_any = 1` flip in `endpoints.py:117-127`
(MAJ-6); the vacuous `M1 → M3` monotonicity leg with `|M1| = 0` (MAJ-7); the missing §12.1
artifacts including `partA_component_summary.json`; `monotonicity_severity: "CRITICAL"` inside
`go_conditions` (MAJOR-9); and the 480-pair in-pass census of which 360 are vacuous
`SkeletonParseFailure` pairs (MAJOR-4 / MAJ-4).

### MINOR / NOTE

- **MINOR-R1** — Part B's declared one-sidedness is not established. v2.1 `:1297` / §14 item 3 say
  Part B must over-report out-of-support. `add_unaries`
  (`GitHubSourceCode/ODEFormer/odeformer/envs/generators.py:627-639`) trims on `x in self.unaries`,
  and `self.unaries` includes `id` (`operators_to_use = "…id:3…"`, `:389`), so the generator's real
  cap is on unaries **including** `id`, while `U_mult` counts only non-identity unaries
  (`partb.py:36`). That asymmetry runs *against* the declared direction; B-R3's omission runs *with*
  it. Net direction `unverified`.
- **MINOR-R2** — B2-S7 (the `in_support` × H/L cross-tabulation §7.8 requires) is in no artifact.
  I computed it: **all 9** out-of-support components are in stratum H (`R07_*/2` × 6,
  `R08_*/2` × 3); L is 40/40 in support. The number that bears on the primary is 9/130 = 6.9%,
  not 9/170.
- **NOTE-R1** — the binary-op budget is correctly **not** an `in_support` constraint, contrary to my
  initial suspicion. 70 of 170 validation components exceed `max_binary_ops_per_dim = 5`
  (`binary_ops_per_dim` distribution `{3:40, 5:60, 6:20, 7:30, 8:10, 10:10}`) yet are `in_support`,
  and that is right: `generators.py:594-612` spends `nb_binary_ops` on the **undecorated** skeleton,
  then `add_prefactors` / `add_linear_transformations` add more `add`/`mul` nodes and the count is
  **re-derived** afterwards. Only the unary cap survives decoration. `U_min ≤ 3` is the correct
  binding constraint. Recorded so a future reviewer does not re-raise it.
- **NOTE-R2** — the M3 pinning is exact by **code identity**, not merely by the 1,178-pair and
  480-pair agreement tests: `symbolic_recovery`'s `"skeleton"` (`equation_metrics.py:241`) *is* the
  first element of `skeleton_equivalence_with_reason`'s return on stripped inputs, which is what
  `matcher.py:139` calls. Stronger than the artifacts claim.
- **NOTE-R3** — the eager-dict reasoning in v2.1 §7.5 item 1 is correct: `symbolic_recovery`'s
  `equiv` block (`:245-253`) does execute and does burn wall clock on every M3 call, and its
  `except Exception: equiv = skeleton` swallows `_SymTimeout` without touching `["skeleton"]`.
- **NOTE-R4** — three independently-derived `undecidable` verdicts are **not** three independent
  derivations of the same strength. They share one input (`sensitivity_agrees: false`) and one
  contract clause (§7.5 item 3), and the derivation is a two-line mechanical lookup. What is
  genuinely independent is the *recomputation of `K` and `K_adversarial` from `cell_cache/`*, which
  the Stage 8 analyst, the statistical reviewer and I each did separately and which agrees exactly.
  So the agreement is real but narrow; it certifies the arithmetic, not the verdict's meaning, and
  §1.5 shows the arithmetic is execution-dependent. The cycle report should not present "three
  independent derivations agree" as corroboration of the verdict.
- **NOTE-R5** — `phase0` manifest commit `b731cdd` ≠ `phase1/2/3` manifest commit `8ff622d`; the
  diff does not touch the Part A matcher path. No reproducibility impact (agrees with Stage 8 MIN-4).

---

## 10. Alternative explanations for the null that C0001 cannot exclude

The primary is "M3 adds no match M0 missed, in stratum H". Four explanations remain live; the cycle
must not collapse them.

1. **E0 is false** (canonicalization adds nothing) — the intended reading. Not supported: §2.2 shows
   the trial was not run on 121 of 130 components.
2. **No opportunity existed in the beam** (the measured fact): 112 of the 130 H components are
   inside the generator's operator support (§3.3) yet have **no structurally comparable candidate**
   anywhere in a 50-wide sampling beam across 12 conditioning cells. This is consistent with E2
   (probability mass) or E3 (search reach), and Part A cannot separate them.
3. **M3 is itself insensitive on the relevant shapes.** PC4's own breakdown (Stage 8 §5.1, which I
   confirm from `partA_controls.json`) shows M3 failing on **30 of 130** H components under
   `sympy.together` — all of R01 (10/10) and all of R05 (20/20) — because collapsing three or more
   distinct constants to a single `c` breaks the identity. So the demonstrated-sensitive H subset is
   100, not 130, and `K = 0` is effectively a statement about 100 components at most, intersected
   with the ≤ 88 that had any opportunity.
4. **The instrument silently mis-scored some comparisons.** Bounded, not excluded: ≤ 265 possible
   `equals`-undecided triples (MAJOR-R1) and 9–0 load-dependent timeouts (CRITICAL-R1).

The one explanation the cycle **does** exclude is "the gain indicator cannot fire": PC4 fires
100/170 through the same `gain_indicator` function object (`controls.py:507`), the same
`formula_metrics` / `symbolic_recovery` path, the same infix derivation and the same 10.0 s guard.
That is a genuine and reusable instrument fact.

---

## 11. Replication gate

`.claude/skills/replication-gate` mandates replication when a result is based on one seed/split or
is **marked fragile by a reviewer**. Both apply, and CRITICAL-R1 makes it unavoidable: the verdict
of record is not the same across contract-compliant executions.

Minimum design for the confirmation run — to be **preregistered as C0002, not patched into C0001**:

- **Independent factor changed:** the execution configuration, which is the factor CRITICAL-R1
  identifies. Pin `n_workers` explicitly (both `1` and `6` as two declared arms) and pin the
  host-load condition. Do **not** change `SYMPY_OP_TIMEOUT_SEC`, the cutpoint, the cap or any seed.
- **Recorded per triple:** wall clock per guarded call, which of the four 10 s budgets fired, and
  the raw `.equals` return (`True`/`False`/`None`) so MAJOR-R1 becomes a measured endpoint rather
  than an assumption.
- **Primary replication endpoint:** the *distribution* of `could_not_evaluate_rate` and of the
  resulting ladder rung over ≥ 10 executions per arm — not a single verdict.
- **Reported separately** from C0001's run of record, per the skill.
- **Expected outcomes:** `replicated` only if every execution in both arms lands on the same rung;
  otherwise `failed replication` on the verdict, with `K = 0` and the M0/M3 identity
  `directionally replicated` since they are deterministic.
- The right resolution of the 9 timeouts is v2.1 named contingency 1's own channel: a **new
  preregistered cycle** that raises the cap deliberately, with the 9 triples as its declared unit.
  That is the campaign's stated plan and it is correct. It is **not** a rescue of C0001.

---

## 12. Recommendation

### `REPLICATE`

Reasons, in order of force:

1. **CRITICAL-R1.** The verdict of record is a function of elapsed wall-clock time under an
   execution the contract does not pin. Measured on identical inputs with the frozen timeout
   untouched: `undecidable` in 4 of 5 six-worker repetitions and 2 of 3 serial repetitions,
   `no_gain_observed_bound_only` in the remaining 2 of 8. `undecidable` is the modal outcome but
   not the determined one, and the mechanism is `unverified`.
2. **CRITICAL-R2.** The primary's realized denominator is 9–88 of its nominal 130, so no interval or
   power figure in `partA_endpoints.json` or `partA_ladder_realized.json` describes the inference
   performed.
3. **CRITICAL-R3** binds the *next* cycle's decision endpoint and must be resolved before C0002
   freezes.
4. Two CRITICALs already on the record (Stage 8 CRIT-1, CRIT-3) remain unremediated **in the
   artifacts**, even though the code is fixed.

Under `.claude/rules/07-independent-review.md`, CRITICAL findings block a supported conclusion.

### May C0001 proceed to a cycle report, or must it be held?

**It may — and must — proceed to a cycle report, but not to a cycle *conclusion*.**
`.claude/rules/08-cycle-persistence.md` makes the report mandatory for negative, null, failed,
invalidated and inconclusive outcomes alike; holding it would violate that rule and lose the
instrument facts. Conditions the report must satisfy:

1. State the verdict of record as **`undecidable`** *for the run of record*, and immediately
   disclose that a contract-compliant re-execution reaches `no_gain_observed_bound_only` — with the
   measured counts (§1.3, §1.4, §1.7), not as a hypothetical.
2. Report the opportunity census (§2.2) as a **primary result**, not a caveat: 121 of 130 H
   components had no comparable candidate; 112 of those are inside the generator's operator
   support. This is the cycle's most informative measured fact and it currently appears in no
   artifact.
3. Never state or imply that C0001 found no matcher-attributable gain, that M0 and M3 are
   equivalent, or that E0 is bounded or refuted. `K = 0` may be reported only as a raw observation
   carrying the `undecidable` label, per rule 01 item 8.
4. Quote the bound of record as the **family-level** Wilson [0, 0.3244075683414076] with its method
   name, never the independence-assuming [0, 0.028701561634224194], and never the degenerate
   bootstrap [0, 0].
5. Not issue the §9.5 item 1 `K = 0` sentence: it is the reporting form of the `supported` verdict,
   and its mandated family-clustered-power `[value]` is uncomputed.
6. Carry the R5 validity-threat disclosure (§5.1) and the MAJOR-R3-correction (§1.2) so the wrong
   "4 touched components" number is not propagated.
7. Not present "three independent derivations agree" as corroboration of the verdict (NOTE-R4).

**What may be reported as established, at `ACCEPT_AS_PRELIMINARY` strength** — all deterministic,
all independent of the CAS lottery, all reproduced by me:

- M0's exact reproduction of GPU_RUN5's stored fields: 47,987 candidates, 101,963 component
  comparisons, 2,235 component hits, 0 mismatches, ANY-reduced 0/960 system and 107/2040 component,
  and all eight family counts. Labelled a **positive control** against published values, per rule R1.
- The set relations at every resolution: `|M0| = |M3| = 2,235`, `|M1| = 0`,
  `|M0 \ M3| = |M3 \ M0| = 0`, `|M0 \ M1| = 2,235`, A2-S6b `= 0` — with §2's reading of what they
  do and do not evidence.
- The opportunity census: 2,466/101,963 comparable triples; H 187/77,983 and 5,851/77,983 under the
  two screens; 9 and 88 of 130 H components respectively.
- PC4 as an instrument characterization: gain 100/170, all 100 in H, 6 of 8 families — **and** its
  limitation, M3 failing on 30/130 H components (R01 10/10, R05 20/20) under `sympy.together`.
- Part B: 9/170 components (9/130 H, 0/40 L) outside the generator's unary budget under B-R1..B-R4,
  with Hill-4 verified detected in 39/170 components in both spellings.
- The instrument defect list: the wall-clock verdict dependence, the `.equals`-`None` surface, the
  vacuous PC2c/PC2d gate, the vacuous `M1 → M3` monotonicity leg, and the sampling-order candidate
  ordering that voids `lp_sel`.

Nothing here warrants `INVALIDATE`: no leakage, no exclusion bias, no post-hoc threshold change, and
the deterministic half of the cycle reproduces exactly. Nothing warrants `ACCEPT_AS_NEGATIVE`
either: there is no negative result, because on 121 of 130 analysis units the measurement did not
take place.

---

## 13. What I could not verify (`unverified`)

- Whether a **full 960-cell** re-execution reaches zero could-not-evaluate triples. I measured 9 of
  960 cells; the other 951 contain unsampled near-boundary triples, so the full-run count could be
  higher than my per-arm figures. My repetitions bound the *set*'s instability, not the full-run
  count's floor.
- **The mechanism of the timeout non-determinism.** I withdrew CPU contention (§1.5); my serial and
  6-worker arms confound parallelism with SymPy cache warmth because they differ in process
  granularity, and I did not run the de-confounded design. Memory pressure after 47,987 candidates'
  worth of cache fill is unmeasured by me.
- The realized `equals`-`None` rate below 0.26% (MAJOR-R1's Wilson upper on 1,476 triples).
- Whether any GPU_RUN5 artifact records a per-candidate model score or log-probability that would
  let `candidate_index == 0` be recovered as the model's argmax (CRITICAL-R3).
- The net direction of Part B's one-sidedness (MINOR-R1): the `id`-inclusive unary cap and B-R3's
  omission push opposite ways and I did not quantify either.
- The family-clustered power at `|H| = 130`. The contract specifies no ICC model, so the quantity is
  not computable as written; the ICC = 0 / ICC = 1 endpoints are 0.9991 and 0.3504 at `p = 0.0525`.
- Attribution of the 121 zero-opportunity H components among E1' / E2 / E3 beyond the 9 that E1'
  covers. Part A does not measure it and Part C's decision endpoint was never computed.

---

## 14. Reproduction of this review's measurements

Frozen code and artifacts were read only. The four measurement scripts were written to the session
scratchpad, not the repository, and each is described in full in the section that uses it:

| section | what it recomputes | inputs |
|---|---|---|
| §1.1, §2.1 | the whole endpoint chain, the `(m0, m1, m3)` contingency, A2-S6b | `phase1/cell_cache/*.json` (960), `phase1/component_strata.json` |
| §1.3 | the 9 stored triples, serial, one forked process each, 3 reps | `gpu_run5_.../phase3/cells/*.json` |
| §1.4, §1.7 | the 9 affected cells (1,250 comparisons), `Pool(6)`, 5 reps | same |
| §2.2 | the two opportunity screens over all 101,963 triples | same + strata + `cell_cache` |
| §2.5 | raw `.equals` return over 1,476 seeded-sample triples | same |
| §3 | Part B cross-tabulation and the generator-source checks | `phase2/partB_component_records.jsonl`, `GitHubSourceCode/ODEFormer/odeformer/envs/generators.py` |

`SYMPY_OP_TIMEOUT_SEC` was `10.0` throughout. No file under `results/runs/` was written or modified.
