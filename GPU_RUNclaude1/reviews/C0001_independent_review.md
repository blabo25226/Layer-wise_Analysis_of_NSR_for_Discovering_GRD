# C0001 — Stage 9 Independent Adversarial Review

- Reviewer: `lansr-independent-reviewer` (this document). Distinct from implementation
  (`lansr-implementation-engineer`), primary analysis (`lansr-results-analyst`), statistical review
  (`lansr-statistical-reviewer`) and the supervisor, per `.claude/rules/07-independent-review.md`.
- Binding contract: `GPU_RUNclaude1/plans/C0001_preregistration_v2.1.md` / `.json` only.
  v1 and v2 are superseded and not cited.
- Run of record: `results/runs/gpu_runclaude1_c0001_b731cdd`
  (phase0 manifest commit `b731cddd168390c973dbb0974349e4a2c55b9113`,
  phase1/2/3 manifest commit `8ff622defc227b4598e0094fc000b8227c4ffdad`).
- Branch `20260909_researce_GPU_RUNclaude1`. Review-time HEAD `34da7fc107f280ac3f867dde0daf199e161c1a0a`.
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
| 2. M0 ≡ M3 pointwise on 101,963 triples, symmetric difference 0 | **SURVIVES as arithmetic, FAILS as evidence.** M3 had **zero** opportunities to differ anywhere in stratum H. See §2. |
| 3. E1' explains at most 9/170 components | **SURVIVES**, with the scope tightened to 9/130 H components and to one operationalization. Hill-4 spelling verified correct. See §3. |
| 4. The Gate B→C violation caused no scientific damage | **SURVIVES on damage, FAILS on residue.** See §4. |
| 5. Supervisor reliability discount | See §5. Two live residues found. |

**Recommendation: `REPLICATE` (blocking), then `ACCEPT_AS_PRELIMINARY` for the instrument facts
only.** C0001 may write its mandatory cycle report — the report is mandatory even for an
undecidable cycle (`.claude/rules/08-cycle-persistence.md`) — but it **may not** close as a cycle
whose primary endpoint carries a verdict, because I establish below that the verdict of record is
determined by an execution parameter the frozen contract left free.

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

### 1.3 My measurement — serial, idle host, frozen 10.0 s guard

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
   timeout. It does not need to be raised: on an unloaded host the frozen 10.0 s guard is not
   reached at all. The adversarial arm's premise — count these as matches — is contradicted by the
   same instrument on the same inputs.
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

### 1.5 The decisive finding: the verdict is a function of an unpinned execution parameter

v2.1 §3 (`:666`) freezes Part A parallelism as "**process-based, ≤ 6 worker processes**". It fixes
an upper bound, not a value. Combining §1.3 and §1.4:

- executed with 1 worker on an idle host, the frozen instrument decides 8 of the 9 pathological
  comparisons as `proved_different`, and reaches `could_not_evaluate_rate = 0` in a substantial
  fraction of attempts ⇒ `sensitivity_agrees = true` ⇒ verdict **`no_gain_observed_bound_only`**;
- executed with 6 workers, it reaches ≥ 3 affected components in the 9 cells I re-scored alone
  ⇒ verdict **`undecidable`**.

Both executions comply with the frozen contract. **Two contract-compliant executions of C0001 land
on two different verdicts of record.** This is not "the verdict depends on machine load" (a
property of the host); it is "the verdict depends on a knob the preregistration deliberately left
open" (a property of the contract). Recorded as **CRITICAL-R1**.

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

**PRIORITY answer.** The stored count of 9 is **not** reproducible. Over 5 compliant 6-worker
repetitions on 9 of the 960 cells I measured 6, 4, 0, 3, 5 timeouts, with a **different set every
time**, including three triples (`R07_009_b0/42/2`, `R07_009_b1_n0p05/44/2`, `R07_009_b1_n0/13/2`,
`R07_002_b2/35/2`, `R07_009_b1_n0p05/45/2`) that are not among the run's 9 at all. Serially on an
idle host, 8 of the 9 never time out and all 27 completed comparisons return
`proved_different`. The verdict of record is therefore **not a property of the experiment**; it is
a property of an execution, and `≤ 6 workers` (v2.1 §3, `:666`) does not pin that execution.

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

