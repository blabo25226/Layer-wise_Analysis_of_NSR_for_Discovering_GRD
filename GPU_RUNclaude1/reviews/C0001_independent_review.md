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

