# C0001 — Preregistration

**Title**: Four-way decomposition of the ODEFormer Hill-type GRN generation failure
(E0 evaluator artifact / E1' generator-support exclusion / E2 model error / E3 search error).

| field | value |
|---|---|
| cycle | `C0001` |
| stage | 3 (preregistration) |
| branch | `20260909_researce_GPU_RUNclaude1` |
| commit at freeze | `94a571b6944e4ebb383ea112a2c9032e3dd6b68e` |
| date frozen | 2026-09-09 |
| status | **FROZEN** on write of this file |
| campaign | `GPU_RUNclaude1` |
| upstream artifacts | `results/runs/gpu_run5_20260823_ddd267b0/` (read-only), `results/runs/gpu_run4_phase0_01/` (read-only, calibration + replication only) |
| new run ID | `gpu_runclaude1_c0001_<short7>` — see §12 |
| sealed test consumed | **NONE** |
| layer estimands measured | **NONE** (see §16, rule 04) |

Amendments to this file after Stage 4 begins are permitted only through the deviation
policy (§14) and must be appended as dated `DEVIATION-nn` blocks, never by editing frozen text.

---

## 0. Prior information disclosed before freeze (rule 01 item 9)

This cycle is **not blind**. The following quantities were observed before freeze and are
declared here so that no downstream report can present them as C0001 discoveries.

| # | observed quantity | value | source | consequence for this design |
|---|---|---|---|---|
| P1 | GRN truths `teacher_valid` (encodability) | 240/240 train, 80/80 validation | `C0001_stage1_preobservation.md` | **E1 (raw expressibility) is REFUTED. Not re-tested. Cited only.** |
| P2 | Zero-probability operator set under the checkpoint's persisted generator config | `abs, sqrt, log, exp, arcsin, cos, arccos, tan, arctan, pow3, sub, div` all exactly 0.0 | Stage 1 addendum, verified against `third_party/odeformer/odeformer/envs/generators.py:369-373` | Recorded as a fixed constraint, not an endpoint. |
| P3 | GT teacher token length, validation | min 19, median 47, mean 45.7, max 80 | Stage 1 | Drives the Part C length-normalization policy (§8.3). |
| P4 | `neg` node present in truth exponent-aware skeletons | 960/960 cells (100%) vs 1,541/47,987 candidates (3.2%) | `C0001_exploratory_neg_canonicalization.md` (EXPLORATORY) | Identifies the specific encoding asymmetry Part A must be *sensitive to*; becomes positive control PC2a. |
| P5 | **`neg`-normalized full-system truth-in-beam** | **0/960 = 0.0000**, and 0/120 in every family R01–R08 | same (EXPLORATORY) | System-level rate under a *crude* normalization is already known to be 0. The Part A primary uses a **different, strictly more permissive** instrument (CAS cascade, §7.2) whose system-level value is **unobserved**. |
| P6 | **`neg`-normalized per-component truth-in-beam** | **107/2040 = 0.0525** | same (EXPLORATORY) | **The component-level rate has been seen.** It is therefore preregistered as **estimation with a clustered interval, not as a discovery test** (§7.5). |
| P7 | Train-split non-identity unary count per truth component | histogram {0:120, 1:120, 2:70, 3:120, 5:60, 6:10, 10:10}; **80/510 components (15.69%) and 60/240 systems (25.0%) exceed `max_unary_ops_per_dim = 3`** | this file, §0.1 | Establishes Part B has a non-degenerate effect and calibrates its expected size. |
| P8 | Nested `pow2,pow2` (realized Hill exponent 4) | 130/510 train components; **39/170 validation components** | this file, §0.1 | **Corrects coordinator Finding 2** (see §0.2). |
| P9 | Stored candidate fields | `all_candidates.json` stores `candidate_formula_raw`, `canonical_exact`, `skeleton_exact`, `exponent_aware_skeleton_exact`; it stores **no `symbolic_equivalent` field and no log-probability/score field** | this file, §0.1 | Part A must recompute CAS equivalence (which GPU_RUN5 never computed: `src/gpu_run5/evaluation.py:40` calls `compare_formulas(..., skip_cas=True)`). Part C must **re-encode and re-score** all candidates, which introduces the re-encoding risk handled in §8.2. |
| P10 | Candidate-set completeness | 951 cells with 50, 6 with 49, 2 with 48, 1 with 47 → 47,987 total, shortfall 13 | this file, §0.1 | All rates use *usable* candidates as denominator, never a hardcoded 50. |
| P11 | CAS matcher throughput | 129 ms/candidate mean over a 60-candidate random sample of `results/runs/gpu_run4_phase0_01/phase2/all_candidates.json`, 0/60 exceeding 1 s → ≈1.72 single-core-hours projected for 47,987 | this file, §0.1 | Makes the Part A CPU ceiling (§11) credible; calibration used a **different corpus** (ODEBench), not the endpoint data. |

### 0.1 Provenance of the checks run during Stage 3

All Stage-3 verification was read-only against `phase2/train.json`, `phase2/validation.json`,
`phase3/all_candidates.json`, `phase3/cells/`, `src/`, `configs/`, and
`results/runs/gpu_run4_phase0_01/phase2/all_candidates.json`. **No file under any `sealed_*`
path was opened.** No file was written outside `GPU_RUNclaude1/plans/`.

P7/P8 were computed on the **train** split so that design decisions are made on the
calibration split (rule 02). The single validation-side quantity computed at Stage 3 is the
P8 nested-`pow2` component count (39/170), which was a *design-feasibility yes/no* question:
had exponent 4 been absent from validation, Part B's rewrite set would have had to change.
It is disclosed above and Part B's validation endpoints are consequently specified as
**estimation**, not discovery.

### 0.2 Correction of record: coordinator Finding 2 is refuted

The coordinator's Stage-3 message states that the validation truths "realize Hill exponents
**1 and 2 only**, not 4", inferred from `0/960 truth skeletons contain pow2` and
`never pow,4`.

**This inference is incorrect, and the correction is load-bearing for Part B.**

- The corpus prefix uses the token `pow2`; the *canonicalizer* rewrites `pow2(X)` to
  `pow(X, 2)`. Hence the canonical exponent-aware skeleton legitimately contains zero `pow2`
  tokens even when every component is a square.
- Exponent 4 is spelled **`pow2(pow2(x))`**, canonicalizing to `pow(pow(x,2),2)` — tokens
  `pow, pow, x_i, 2, 2`. It never produces a literal `4`. A search for `pow2` or `pow,4`
  therefore cannot detect it.
- Verified counts: nested `pow2,pow2` appears in **39 of 170 validation truth components**
  and **130 of 510 train truth components**. Worked train examples:
  - R01 `0.1621 + 2.1 * ((x_0)**2)**2 * 1/(1.731 + ((x_0)**2)**2) + -1 * 0.4956 * x_0`
    → `U_mult = 5` (multiplicative Hill-4, the exact form the Stage-1 addendum predicted).
  - R07 `1.786 * (x_0)**2 * 1/(2.028 + (x_0)**2) * 1 * (x_1)**2 * 1/(0.2277 + (x_1)**2) + -1 * 0.2693 * x_2`
    → `U_mult = 6` (product of two Hill-2 terms).
  - R08 `1.077 * ((x_0 * x_1)**2)**2 * 1/(1.743 + ((x_0*x_1)**2)**2) + -1 * 0.264 * x_2`
    → `U_mult = 5`.
- **E1' is therefore LIVE, not inapplicable.** It bites through *two* mechanisms, only one of
  which the original brief named: (i) multiplicative Hill-4 (`U_mult = 5`), and (ii)
  **multi-term components** — a single component containing two Hill terms exceeds a
  per-dimension budget of 3 even at exponent 2 (`U_mult = 6`). Mechanism (ii) is a new
  observation and is preregistered as a Part B endpoint.
- Consequence for the rescue argument: affine decomposition rescues (i) to `U_affine = 3`
  but **does not rescue (ii)** — the affine expansion of a *product* of two Hill terms yields
  four terms whose unary count is ≥ 6. Part B must therefore report `U_min = min(U_mult,
  U_affine)` per component and must not assume affine decomposition restores support.

### 0.3 Handling of coordinator constraint (b) — the research-integrity-sensitive item

Because the 5.25% component-level figure (P6) has been seen, the following is frozen:

1. The **primary endpoint is system-level, not component-level** (§7.1). The system-level
   value under the Part A instrument is unobserved.
2. The component-level rate is a **secondary endpoint specified as estimation**: report the
   point estimate and a clustered interval. **No hypothesis test of "rate > 0" may be
   reported for it**, and no artifact, table, figure, abstract, or report sentence may
   describe it as a discovery, a new finding, or a surprise.
3. Every artifact carrying the component-level rate must carry the machine-readable field
   `prior_information_disclosed: "C0001_exploratory_neg_canonicalization.md:107/2040=0.0525"`
   alongside it. The Stage-11 report must reproduce §0 verbatim in its
   "Prior evidence" section.
4. Expected direction is preregistered (§7.6): the CAS cascade must return a component-level
   rate **≥ 0.0525**. A materially *lower* value is a **matcher defect**, not a result, and
   triggers the §7.6 defect protocol rather than a scientific claim.
5. The independent reviewer (Stage 9) is instructed in §17 to check specifically for
   discovery-framing of the component-level rate and to raise it as MAJOR if found.

---

## 1. Frozen primary hypothesis

**H-C0001-P (primary, confirmatory).**

> GPU_RUN5's headline claim — `true_exponent_aware_skeleton_in_beam_rate = 0.0` for Hill-type
> GRN systems — is **not** an evaluator artifact at the level of the whole ODE system.
> Under a canonicalizing, CAS-equivalence matcher applied to the already-stored 47,987 GRN
> validation candidates, the **per-system semantic-equivalence-in-beam rate** over the 80 GRN
> validation systems remains at or near zero: Wilson 95% upper bound < 0.05.

This is a **null-shaped primary hypothesis**. §9 therefore specifies a full null-credibility
policy and a mandatory positive-control battery, without which the null is uninterpretable.

**Falsifier.** ≥ 4 of the 80 systems having a semantically equivalent full-system candidate in
beam falsifies H-C0001-P, invalidates GPU_RUN5's headline interpretation, and routes through
the replication gate (§15).

### 1.1 The four competing explanations

| id | explanation | status entering C0001 | decided by |
|---|---|---|---|
| **E0** | measurement/evaluator artifact — beam contains algebraically equivalent structure that the exponent-aware **string** matcher scores as a miss | **LIVE**; partially confirmed at component level (P6), refuted at system level under crude normalization (P5) | **Part A** |
| **E1** | raw expressibility — the truth cannot be written in the token grammar | **REFUTED** (P1: 320/320 encode and round-trip). **Not re-tested.** | cited, not measured |
| **E1'** | generator-support exclusion — the truth's minimal form exceeds `max_unary_ops_per_dim = 3`, so it was never in the pretraining sampling support even though encodable | **LIVE** (P7/P8, §0.2) | **Part B** |
| **E2** | prior mass / model error — the truth is in support but has near-zero probability under the pretrained decoder given the trajectory | LIVE | **Part C** |
| **E3** | search error — the truth has non-negligible probability but beam-50 sampling at T = 0.1 never reaches it | LIVE | **Part C** |

E0, E1', E2 and E3 are **not mutually exclusive**; they can hold on different subsets of
systems. The design therefore reports a **partition of the 80 systems**, not a single winner
(§10.3).

### 1.2 Explicitly out of scope

- No beam-size or temperature sweep is preregistered as any endpoint. The literature already
  answers it (ODEFormer ICLR 2024 Appendix G: "Increasing the beam size improves
  reconstruction, but not generalization"; CTC_NSR: beam 150 "provided no additional
  information"). Restating it would be a known-answer experiment.
- No claim of novelty for teacher-forced GT scoring. It is `adjacent`, precedented by
  Stahlberg & Byrne, EMNLP-IJCNLP 2019, pp. 3356–3362, **DOI 10.18653/v1/D19-1331**
  (https://aclanthology.org/D19-1331/), which separates search errors from model errors in
  NMT. The cycle report must cite it and must not claim the instrument as novel.
- No biological-causality language anywhere. Targets are synthetic Hill-type systems
  (rule 01 item 7).
- No equation-discovery claim from R²/NMSE (rule 03). Part A/B/C endpoints are structural
  match rates, unary-budget counts and log-probabilities. Trajectory fit is recorded as a
  covariate only.
- No layer-importance claim (rule 04; §16).

---

## 2. Statistical unit, splits, and the test firewall

### 2.1 Statistical unit

**The parameterized GRN system.** n = 80 (validation), 10 per family R01–R08.

Cells are **not** the unit. Each system has exactly **12 cells** = 4 corruption settings
(`noise_sigma ∈ {0.0, 0.05}` × `subsample_rho ∈ {0.0, 0.5}`) × 3 bundles
(`bundle_index ∈ {0,1,2}`). Cells within a system share the same ground truth, so treating
them as independent would inflate n by 12× and understate every interval.

**Aggregation order (frozen, non-negotiable): within-system first, then across systems.**

- Binary endpoints: compute the per-cell indicator, then the per-system indicator, then
  aggregate across the 80 systems. Two per-system reductions are preregistered and both are
  reported:
  - `ANY` (generation coverage, **primary**): system indicator = 1 if **any** of its 12 cells
    has a hit. This is the coverage question — "did the model ever place the structure in a
    beam for this system?"
  - `MEAN` (per-system hit fraction, secondary): mean of the 12 cell indicators, aggregated
    with `student_t_ci`. This is the robustness question.
- Continuous endpoints: per-cell value → per-system mean over its usable cells → across-system
  `student_t_ci`.
- Family is **not** the inference unit. Per-family rates (n = 10 systems each) are reported
  descriptively with Wilson intervals and are secondary; with 10 systems per family no
  family-level rate is adequately powered and none may carry a confirmatory claim.

### 2.2 Datasets

| role | artifact | n | use |
|---|---|---|---|
| **calibration / design** | `results/runs/gpu_run5_20260823_ddd267b0/phase2/train.json` | 240 systems | Part B calibration, rewrite-set development, threshold sanity, power checks. **Never contributes to a primary or secondary endpoint.** |
| **measurement** | `results/runs/gpu_run5_20260823_ddd267b0/phase2/validation.json` (SHA256 recorded in cells as `phase2_validation_sha256 = f4644d1d4c30f8a3d6f0cafc8f321fb2c07e72979d8e4c42d28862376abb8f64`) | 80 systems | ground truths for all endpoints |
| **measurement** | `.../phase3/all_candidates.json` (47,987 candidates) + `.../phase3/cells/*.json` (960) | 960 cells | Part A re-scoring; Part C candidate distribution and per-cell input trajectory |
| **matcher timing calibration + replication corpus** | `results/runs/gpu_run4_phase0_01/phase2/all_candidates.json` | 12,632 candidates, 63 ODEBench systems | P11 timing; §15 replication; Part D exploratory |
| **model** | `assets/odeformer/weights/odeformer.pt`, SHA256 `56754040be5aa92ed4767fc43ee2008faa293f87c12b643e66c7df3e1623a5e8`, 464,822,385 B | 1 checkpoint | Part C forward passes only |

Because all 47,987 stored candidates carry `split == "validation"` (P9), there is **no train
candidate set**. Part A's matcher can therefore not be timing-calibrated or threshold-tuned on
train candidates; calibration uses the ODEBench corpus instead (P11). This limitation is
recorded here rather than discovered later.

### 2.3 Test firewall (explicit)

| artifact | status | C0001 access |
|---|---|---|
| `.../phase2/sealed_test.json` (80 systems, SHA256 `881f784b…64ce0`) | **SPENT** — opened once 2026-09-01, `open_count: 1` | **MUST NOT be read at all.** |
| `.../phase2/sealed_family_holdout_test.json` (20 systems, subset of the 80, SHA256 `fa8fe375…baf91`) | **SPENT**; never independent evidence | **MUST NOT be read at all.** |
| `.../phase4/sealed_official_test.json` (500 official formulas, SHA256 `2860d829…f28e070`) | **UNSPENT — the campaign's only clean seal** | **MUST NOT be touched.** Preserved for a future cycle. |
| ODEBench 63 systems (`third_party/odeformer/odeformer/odebench/`) | not sealed, but forbidden as adaptation / layer-selection / hyperparameter data | read-only, calibration and replication only; no adaptation, no selection |

**Enforcement mechanism.** `src/gpu_run5/config.py:63 load_sealed_test` raises
`PermissionError(f"test firewall: phase {phase} cannot read {path}")` whenever `phase < 8`.
Every C0001 phase runs with `phase ∈ {0,1,2,3,4}`, so any sealed read raises. In addition:

1. C0001 code MUST route every read of a path matching `sealed*` through `load_sealed_test`;
   direct `open()`/`read_json()` on such a path is a CRITICAL audit finding.
2. Stage 5 (reproducibility audit) MUST grep the C0001 diff for `sealed` and confirm zero
   direct reads.
3. Stage 6 MUST run `pytest GPU_RUN5/tests/test_gpu_run5_firewall.py` green **before** any
   endpoint computation. `pytest.ini` currently omits `GPU_RUN5/tests` (known defect 1 in
   `research_state.md`); C0001 therefore invokes that path explicitly rather than relying on
   a bare `pytest`.
4. Every phase manifest records `sealed_paths_read: []` and the SHA256 of each input actually
   opened.

**C0001 consumes no seal.** There is no final-test access in this cycle.

### 2.4 What cannot change after final-test access?

C0001 accesses no final test. The analogous irreversible commitment is **the first computation
of the Part A primary endpoint on the 80 validation systems**. After that moment the following
are immutable for this cycle, and any change forces a new cycle ID rather than an amendment:

primary hypothesis · primary endpoint and its matcher level (M3) · the M0–M3 cascade
definitions and their tolerances · statistical unit and aggregation order · the `ANY` primary
reduction · the null-credibility ladder (§9.2) · the positive/negative control battery and its
pass thresholds · the Go/No-Go gates · the supported/unsupported/undecidable criteria · the
exclusion and failure policy · seeds · the checkpoint SHA256 · the compute ceiling · the run ID.

---

## 3. Model, checkpoint, seeds, and budgets

| item | frozen value |
|---|---|
| checkpoint | `assets/odeformer/weights/odeformer.pt`, SHA256 `56754040be5aa92ed4767fc43ee2008faa293f87c12b643e66c7df3e1623a5e8` |
| architecture of record | released `4 encoder (dim 256) + 12 decoder (dim 512)`, 16 heads, 60,646,773 params — **not** the paper's 4+16/dim 512/~86M |
| **training budget** | **ZERO.** No parameter is updated in C0001. No optimizer is constructed. |
| **hyperparameter search space** | **EMPTY.** No hyperparameter is tuned. Every threshold in this file is fixed before Stage 4. |
| **new decoding budget** | **ZERO.** No new beam search, no new sampling. Part A and B re-score stored artifacts; Part C is forward-only teacher-forced scoring. |
| decode config of the stored candidates (fixed context, not swept) | `beam_size = 50`, `beam_type = sampling`, `beam_temperature = 0.1`, `max_generated_output_len = 200`, `rescale = True`, `failure_penalty = 10.0` |
| operator constraints of record | `operators_to_use = "sin:1,inv:1,pow2:1,id:3,add:3,mul:1"`; `min/max_unary_ops_per_dim = 0/3`; `min/max_binary_ops_per_dim = 1/5`; `max_unary_depth = 7`; `max_int = 10`; `float_precision = 3`; `max_dimension = 6`; `operators_to_not_repeat = ""`. Zero-probability operators: `abs, sqrt, log, exp, arcsin, cos, arccos, tan, arctan, pow3, sub, div` |
| seeds | Part A/B are deterministic (no RNG) except `numeric_equivalent(seed=0)`, frozen at **0**. Part C is deterministic (forward passes, `torch.use_deterministic_algorithms(True)` where supported, `model.eval()`, `torch.no_grad()`). Global seed **20260909** set for numpy/torch/python for reproducibility of any incidental ordering. The replication run (§15) uses `numeric_equivalent(seed=1)` and an independent safe-domain point set — the deliberately changed factor. |
| dtype/device | fp32; Part C on `cuda:0`; Parts A, B, D CPU-only |
| PyTorch | 2.5.1+cu124; sympy 1.13.1; numpy 2.2.6; zss 1.2.0; env `lansr310` (Python 3.10.20) |

---

## 4. Baseline conditions and comparators

There is no trained baseline, because nothing is trained. The comparators are **frozen
measurements of record**:

| comparator | value of record | role |
|---|---|---|
| **C-M0** frozen string matcher, system level | `true_exponent_aware_skeleton_in_beam_rate = 0.0` over 960 cells (`scripts/phases/gpu_run5_phase3.py:442`) | the claim under test; must be **reproduced exactly** by C0001's M0 arm before any other number is believed |
| **C-M0c** frozen string matcher, component level | 0/2040 | comparator for the component-level secondary |
| **C-NEG** crude `neg`-folded matcher (EXPLORATORY, P5/P6) | 0/960 system, 107/2040 component | a *lower bound* on what a proper canonicalizer should find; the CAS cascade must not fall below it (§7.6) |
| **C-ODEB** ODEBench string matcher | 4/252 = 1.59% [0.0062, 0.0401] | non-zero corpus-level positive control for the cascade in the §15 replication |
| **C-BUDGET** the generator's own unary budget | `max_unary_ops_per_dim = 3` | Part B reference |
| **C-SAMPLED** the empirical log-prob distribution of the 50 candidates the model actually sampled in each cell | to be measured in Part C | Part C reference distribution — the model is compared against **itself**, which is the fair-budget comparison (§5) |

### 5. Fair comparison budget

Every comparison in C0001 is made at a **matched budget by construction**, and this is
recorded so that no arm can be accused of an advantage:

1. **Part A** compares four matchers (M0/M1/M2/M3) on the **identical** 47,987 stored
   candidates and the identical 80 truths. No arm sees different data, more candidates, or a
   different number of cells. The only thing that varies is the equivalence criterion. Any
   difference is attributable to the instrument alone.
2. **Part B** compares two encodings (multiplicative vs affine-decomposed) of the **same**
   truth against the **same** fixed budget of 3. The rewrite enumeration is capped identically
   (200 verified rewrites per component) for both.
3. **Part C** compares the ground truth against the model's **own** 50 samples, conditioned on
   the **identical** input trajectory (verified by `input_trajectory_checksum`), through the
   **identical** forward path (same embedder point-bag construction, same cached encoder
   output, same `decoder("predict", get_scores=True)` call). Both GT encodings and all
   candidates are scored with the same code path in the same process. There is no
   "GT gets a special path" asymmetry — and §8.2 preregisters the audit that proves it.
4. No arm receives extra compute. The CAS timeout (10 s) and node cap
   (`SYMPY_MAX_NODES`) apply identically to M2 and M3, to truths and candidates, and to
   controls and real data.
5. Part C candidate log-probs are computed, never inherited from a differently normalized
   stored score — no stored score exists (P9), which removes that class of unfairness but
   creates the re-encoding risk handled in §8.2.

---

## 6. Experiment structure and ordering

Four parts, ordered so the cheapest **claim-invalidating** check runs first.

| part | question | instrument | compute | gate |
|---|---|---|---|---|
| **Part A** | E0 — is the 0.0 a string-matcher artifact? | canonicalizing + CAS-equivalence cascade over stored candidates | **CPU only** | Gate 0 → A |
| **Part B** | E1' — is the truth outside the generator's sampling support? | analytic unary-budget census over stored truths | **CPU only** | Gate A → B |
| **Part C** | E2 vs E3 — model error or search error? | teacher-forced GT log-probability vs the model's own sampled distribution | **GPU, forward passes only** | Gate B → C |
| **Part D** | exploratory: what *are* the ODEBench variable-denominator candidates? | denominator-arity classification | **CPU only** | none; exploratory |

Parts A, B and D touch no GPU. Part C is the only GPU work in the cycle.

---

## 7. Part A — evaluator adequacy (CPU only)

### 7.1 PRIMARY ENDPOINT (the one and only)

> **`system_semantic_equivalence_in_beam_rate_M3_ANY`**
> = (number of the 80 GRN validation systems for which **at least one** of the ≤ 50 candidates
> in **at least one** of the system's 12 cells is a full-system semantic match to that
> system's ground truth under matcher level **M3**) / 80.
>
> Reported with a **Wilson score 95% interval** (continuity-corrected form not used; plain
> Wilson, `alpha = 0.05`).

Rationale for M3 as the primary level: E0 alleges the string matcher *misses* structurally
correct candidates. The adversarially correct choice is the **most permissive** structural
criterion available, because it makes the null maximally easy to falsify. Using a stricter
criterion would make a null trivially easy to obtain and scientifically worthless.

Rationale for `ANY`: rule 03 requires **generation coverage** to be distinguished from
selection. `ANY` is the coverage estimand: did the generator ever produce the structure for
this system, under any corruption, in any bundle?

### 7.2 The matcher cascade (frozen definitions)

Applied per (cell, candidate, component). Index-aligned by variable: component *i* of the
truth is compared **only** to component *i* of the candidate; a dimension mismatch is an
automatic non-match with `failure_reason = "ParseError"`. Reused code, no reimplementation:

| level | definition | implementation of record |
|---|---|---|
| **M0** | frozen exponent-aware **string** skeleton equality | `src/evaluation/gpu_run5_structure.py:206 classify_formula` → `exponent_aware_skeleton` string equality, exactly as `src/gpu_run5/evaluation.py:84` |
| **M1** | canonical prefix exact | `src/gpu_run4/formulas.py:479 compare_formulas(...)["canonical_exact"]` |
| **M2** | CAS symbolic equivalence, **constants included** | `compare_formulas(..., skip_cas=False)["symbolic_equivalent"]` — internally timeout-guarded `simplify(T_i − C_i)`, then `T_i.equals(C_i)`, then `src/gpu_run4/formulas.py:361 numeric_equivalent(n_points=32, seed=0, rtol=1e-5, atol=1e-6)` on the safe domain |
| **M3** | CAS equivalence at **matched constants** (structural) | `src/evaluation/equation_metrics.py:169 symbolic_recovery(T_i_infix, C_i_infix)["skeleton"]`, plus `:68 _approximately_equivalent(rtol=1e-6)` at the fitted constants, plus `:153 to_skeleton` |

All SymPy paths are already wall-clock guarded: `equation_metrics.py:56 _timed_simplify` and
`:62 _timed_equals` at `SYMPY_OP_TIMEOUT_SEC = 10.0`; `formulas.py:437` guards
`_sympy_components_equal` at `SYMPY_EQUIV_TIMEOUT_SEC` with a `SYMPY_MAX_NODES` cap. **No
timeout value is changed by C0001.**

Roll-up (frozen):
`component_match(i, level)` → `system_match(candidate, level) = component_count_match AND all_i component_match(i, level)`
→ `cell_hit(level) = OR over usable candidates` → `system_hit_ANY(level) = OR over the 12 cells`.

### 7.3 Monotonicity self-check (internal consistency, mandatory)

Expected: **M0 ≤ M1 ≤ M2 ≤ M3** as sets of matching (cell, candidate, component) triples.
Every violation is logged with both expressions, and:

- violation fraction ≤ 0.1% of scored triples → recorded as a known CAS edge case
  (`to_skeleton` collapsing distinct constants to one symbol `c` can legitimately break
  M2 ⊆ M3); reported, not blocking;
- violation fraction in (0.1%, 1%] → **MAJOR** finding; must be diagnosed before the primary
  is reported;
- violation fraction > 1% → **CRITICAL**; the cascade is defective, Part A verdict is
  `undecidable` (instrument failure), and no null may be claimed.

### 7.4 Mandatory control battery (this is what makes a null admissible)

Synthetic candidates are injected per system. They **do not** enter the endpoint; they are
tagged `positive_control_tag` and stored in a separate artifact.

| control | construction | measured | pass threshold |
|---|---|---|---|
| **PC1** identity | inject the truth itself (its own `teacher_components_infix`) as a candidate | sensitivity of M1, M2, M3 | **80/80 for all of M1, M2, M3.** Any failure ⇒ matcher broken ⇒ **abort Part A** |
| **PC2a** `neg` asymmetry | rewrite every `-1 * k * x_i` to `(-k) * x_i` — **the exact artifact P4 identified, in the model's own spelling** | sensitivity of M2, M3 | **≥ 76/80 (95%)** for M3. If M3 < 95% here, the matcher **cannot detect the artifact E0 alleges** ⇒ Part A verdict is `undecidable`, **not** `null` |
| **PC2b** affine decomposition | rewrite `a * A^n * inv(K + A^n)` → `a − a*K*inv(K + A^n)`; SymPy-verified | sensitivity of M2, M3 | ≥ 76/80 for M3 |
| **PC2c** `add` commutation | permute every `add` operand pair | sensitivity of M1, M2, M3 | ≥ 76/80 for M3 |
| **PC2d** `mul` commutation | permute every `mul` operand pair | sensitivity of M1, M2, M3 | ≥ 76/80 for M3 |
| **PC3a** wrong exponent (**negative** control) | truth with one realized Hill exponent altered (4→2, or 2→1) | **specificity** of M2, M3 | **≥ 78/80 must be scored NON-match.** Protects against a matcher so permissive it manufactures a false positive |
| **PC3b** permuted variable (**negative** control) | truth with two variable indices swapped in one component (systems with `dimension ≥ 2` only, n = 60) | specificity of M2, M3 | ≥ 58/60 NON-match |

PC3a/PC3b were **not** in the original brief and are added here: a null-shaped primary can be
destroyed by an over-permissive matcher just as easily as by an under-permissive one, and only
a specificity control detects that.

### 7.5 Secondary endpoints (Part A)

| id | endpoint | inference | note |
|---|---|---|---|
| A-S1 | `system_semantic_equivalence_in_beam_rate_M2_ANY` (constants included) | Wilson 95% | stricter criterion |
| A-S2 | per-system **MEAN** hit fraction over the 12 cells, M3 | `student_t_ci`, dof 79 | robustness reduction |
| A-S3 | **component-level** semantic-equivalence-in-beam rate, M3: per-system fraction of its components ever matched, then across 80 systems | `student_t_ci`, dof 79 (**estimation only**) | **P6 disclosed = 0.0525. NO hypothesis test. NO discovery framing.** (§0.3) |
| A-S4 | per-family system-level M3 rate (8 × n = 10) | Wilson 95%, descriptive | underpowered by construction; no confirmatory claim |
| A-S5 | cascade increment table: |M0|, |M1|, |M2|, |M3| as candidate-level and system-level counts | descriptive | quantifies how much of the "generation failure" is instrument |
| A-S6 | **oracle candidate** per cell per level (the candidate with the best match, ties broken by lowest `candidate_index`) vs the **selected candidate** under each frozen selection rule (`src/evaluation/gpu_run5_selection.py:11`) | descriptive | rule 03: generation coverage vs oracle vs selected |
| A-S7 | matcher failure accounting: `cas_timeout` rate, `ParseError` rate, `SymbolicEquivalenceTimeout` rate, `numeric_equivalence_finite_points` distribution | descriptive | feeds the §9.2 null-credibility condition |
| A-S8 | **preregistered consequence for a later cycle** (coordinator finding (d)): if A-S3 > 0, then GPU_RUN5's `component_exact_loss = 0.0` at all 16 layers was **not** at the floor, and its causal-intervention analysis may have discarded usable signal. **Stated as a testable consequence; NOT tested in C0001** (rule 04 — no layer estimand is measured here). Routed to `hypothesis_tree.md` as a C0002+ candidate. | none | statement only |

### 7.6 Preregistered expected direction, and the matcher-defect protocol

Frozen expectation, from P5/P6 and from the fact that a CAS cascade is strictly more permissive
than a hand-written token folder:

- **component level**: `A-S3 ≥ 0.0525`. Expected somewhat higher.
- **system level**: `primary ≥ 0` and, given P5, most likely **0**.

If `A-S3 < 0.0525 − 0.005` (i.e. the CAS cascade finds *fewer* component matches than the crude
`neg` folder), this is a **matcher defect, not a result**. Defect protocol, frozen:

1. Halt reporting of Part A endpoints.
2. Recover, from the raw records, the specific triples the crude folder matched and the cascade
   did not; store them at `.../phase1/matcher_regression_cases.json`.
3. Diagnose; the most likely cause is `to_skeleton` constant collapsing or a `numeric_equivalent`
   safe-domain rejection.
4. Fix only the defect; re-run Part A **whole**; record a `DEVIATION-nn` block.
5. If the defect cannot be isolated within the compute ceiling, Part A verdict is
   `undecidable`, and **no null may be claimed**.

### 7.7 Data handling, exclusions, and rule-01/03 compliance

- **Invalid and failed candidates are retained** (rule 01 item 5). A candidate with
  `valid == false` is scored as a non-match with its `failure_reason` preserved; it is **never
  dropped from any denominator**. Denominators are *usable candidates present in the cell*,
  which is 47/48/49/50 depending on cell (P10) — never a hardcoded 50. The 13 missing
  candidates are recorded as `candidate_return_shortfall`, carried forward from GPU_RUN5.
- **Numerical fit is not recovery** (rule 01 item 6): `reconstruction_r2`, `generalization_r2`
  and the NRMSE fields are carried into every record as covariates and may be cross-tabulated
  against match status, but no match claim may be made from them.
- Per-candidate **singularity/safety diagnostics** are recomputed with
  `src/evaluation/equation_metrics.py:250 expression_safety` on the cell's input trajectory
  support, giving `near_singularity`, `extrapolation_valid`, `extrapolation_extreme`,
  `has_division`, `has_tan` (rule 03).
- **Variable mapping** is preserved from `phase2/validation.json:variable_to_gene`.
- **Structural distance** is carried from the stored `ted_raw`, `ted_skeleton`,
  `normalized_ted`, `component_normalized_variable_aware_ted` (`src/gpu_run4/ted.py:313
  system_ted`); C0001 does not recompute TED.
- **Complexity** carried from the stored `complexity`.
- **Variable recovery** (precision/recall/F1) computed with
  `src/evaluation/equation_metrics.py:125 variable_recovery`, plus `unnecessary_variables`.

---

## 8. Part B and Part C

### 8.1 Part B — generator-support accounting (CPU only, analytic, deterministic)

For each of the **320** train + validation truths, per component, from the stored
`teacher_components_prefix`:

- `realized_hill_exponents`: multiset of realized exponents, detected as the **nesting depth of
  `pow2` over a variable-containing subtree** (depth 1 → exponent 2; depth 2 → exponent 4). A
  literal `pow,4` token is **not** how exponent 4 is spelled in this corpus (§0.2); an
  implementation that searches for it is wrong by construction.
- `U_mult` = number of **non-identity** unary nodes (`inv, pow2, sin, abs, sqrt, log, exp,
  pow3`) in the stored canonical multiplicative form. Deterministic, exact.
- `U_affine` = minimum non-identity unary count over the **preregistered, finite,
  numerically verified** rewrite set below.
- `U_min = min(U_mult, U_affine)`; `in_support = (U_min <= 3)`.
- `uses_only_in_support_operators` = every operator in the component has non-zero sampling
  probability under the checkpoint's generator config (expected `True` for all; P2).
- `binary_ops_per_dim` vs `max_binary_ops_per_dim = 5`, and `unary_depth` vs
  `max_unary_depth = 7`, so that all three generator constraints are checked, not only the
  unary count.

**Frozen rewrite set for `U_affine`** (applied bottom-up, cap **200** accepted rewrites per
component, deterministic traversal order, each rewrite verified equivalent by
`numeric_equivalent(n_points=32, seed=0)` and **discarded and logged** as
`RewriteVerificationFailure` if it fails):

- **B-R1** `A^n * inv(K + A^n) → 1 − K * inv(K + A^n)` for any subtree `A`, integer `n ≥ 1`
  (the activation → affine-decomposed-repression rewrite).
- **B-R2** fold any pure-constant subtree to a single constant leaf (removes unaries applied
  only to constants).
- **B-R3** distribute `mul` over `add` **only when it strictly lowers** the non-identity unary
  count.
- **B-R4** `neg(X) ↔ mul(-1, X)`.

**Preregistered limitation, stated in advance**: `U_affine` is a minimum over a *bounded*
rewrite set, hence an **upper bound** on the true minimal unary count. A component reported
`out_of_support` may be in support under a rewrite outside this set. Part B's out-of-support
claim is therefore explicitly one-sided: "out of support under the preregistered rewrite set",
never "out of support". **B-R1 does not rescue multi-term components**: the affine expansion of
a product of two Hill terms yields four terms with ≥ 6 unaries (§0.2), so `U_min` for such
components stays > 3.

**Part B endpoints (all SECONDARY; Part B is a deterministic census).**

| id | endpoint | inference |
|---|---|---|
| B-S1 | validation system-level `out_of_support_rate` = fraction of the 80 systems with ≥ 1 component having `U_min > 3` | Wilson 95% |
| B-S2 | validation component-level `out_of_support_rate` (of 170 components) | Wilson 95%, clustered note |
| B-S3 | realized-exponent histogram, train and validation, and reconciliation against `configs/gpu_run5/base.yaml:28 hill_exponents: [1, 2, 4]` | descriptive |
| B-S4 | mechanism decomposition of out-of-support components: (i) multiplicative Hill-4 single-term (`U_mult = 5`, rescued by B-R1 to 3) vs (ii) **multi-term** components (`U_mult ≥ 6`, **not** rescued) | descriptive; **new mechanism (§0.2)** |
| B-S5 | per-family out-of-support rate | descriptive, underpowered |
| B-S6 | zero-probability-operator usage by truths | expected 0/320; falsification of P2's scope if not |

**Statistical honesty (frozen wording).** Part B's per-system values are **deterministic
functions of a fixed corpus** — there is no measurement noise. The Wilson interval describes
sampling variability of the **R01–R08 generator**, i.e. it answers "at what rate does this
generator emit out-of-support truths", not "how uncertain is our count". Every artifact
reporting B-S1/B-S2 carries the field `interval_interpretation: "generator_sampling_not_measurement_error"`.

**Preregistered possibility that E1' is inapplicable.** If B-S1 = 0 (no validation system has
any out-of-support component), then E1' is refuted for this corpus and that is itself a
reportable result: it would mean the multiplicative-Hill unary-budget argument, though correct
in general, does not explain the 0/960. Calibration (P7) makes this **unlikely** (25.0% of
train systems exceed budget), so an observed 0 would additionally trigger a train/validation
consistency check as a possible implementation defect.

### 8.2 Part C — model error vs search error (GPU, FORWARD PASSES ONLY)

Run **only on the in-support subset** defined by Part B: systems all of whose components have
`U_min ≤ 3`. Running Part C on out-of-support systems would conflate E1' with E2, and the
original proposal did not restrict it. Expected n from calibration: ≈ 60 of 80. **If
`n_in_support < 30`, Part C is downgraded to `exploratory` for insufficient power**, reported
as such, and cannot support an E2 or E3 verdict.

Per cell (frozen procedure):

1. Load the cell's **input** trajectory from `phase3/cells/<cell_id>.json:observations["input"]`
   and verify `input_trajectory_checksum` — this is the exact conditioning the model saw. A
   checksum mismatch marks the cell `EncoderCacheMiss` and excludes it (reported).
2. Build the embedder point bag exactly as `src/gpu_run4/training.py:16 _point_bag`, run
   `embedder` + `encoder("fwd", causal=False)` **once**, and cache `src_enc` for reuse across
   all sequences in the cell. This is both the compute saving and the fairness guarantee (§5.3).
3. Score, with `decoder("fwd", causal=True, src_enc=..., src_len=...)` then
   `decoder("predict", tensor=..., pred_mask=..., y=..., get_scores=True)`, gathering
   log-softmax at the `pred_mask` positions:
   - **GT-mult**: the stored `tree_encoded` sequence (the corpus multiplicative encoding).
   - **GT-affine**: the affine-decomposed rewrite from Part B, re-encoded via
     `env.equation_encoder.encode`. If construction or encoding fails → `AffineEncodingUnavailable`,
     logged; the cell contributes GT-mult only.
   - **each of the ≤ 50 stored candidates**, re-encoded from `candidate_formula_raw`.

   **Instrument change required (declared now, not discovered later):**
   `src/gpu_run4/training.py:23 teacher_forcing_loss` returns the **mean** CE via
   `get_scores=False`. C0001 adds a *new* function (it does **not** modify the existing one,
   which other phases depend on) returning `(sum_logprob, n_scored_tokens, per_token_logprobs)`
   from `get_scores=True`. A regression test must assert
   `sum_logprob / n_scored_tokens == -teacher_forcing_loss(...)` to within 1e-5 on ≥ 5 fixed
   examples, proving the new path agrees with the audited one.

4. **Mandatory re-encoding round-trip audit** (this is the single largest threat to Part C,
   because no log-prob was ever stored — P9). For every candidate: `encode(parse(raw))` →
   `decode` → canonicalize, and compare to the stored `candidate_formula_canonical`.
   - exact match → `candidate_reencoding_roundtrip_exact = True`, candidate is usable;
   - mismatch → `candidate_reencoding_mismatch = True`, `failure_reason =
     "CandidateReencodingMismatch"`; the candidate is **excluded from the comparison
     distribution but counted and reported**;
   - if > 10% of a cell's candidates mismatch → cell flagged `unreliable_reencoding`, excluded
     from the Part C primary and reported separately;
   - if > 10% of cells are `unreliable_reencoding` → **Part C verdict is `undecidable`**. A
     re-scored distribution that does not reproduce the model's own emitted token sequences
     cannot answer the reachability question.

### 8.3 Part C endpoints and the length-normalization policy (frozen)

GT sequences are long (P3: median 47, max 80 tokens) and candidate sequences differ in length.
Unnormalized summed log-probability is monotonically penalized by length, which **biases the
diagnosis toward E2 (model error)**. This is not a nuisance to be normalized away silently; it
is preregistered as a triple-reported quantity with a conjunctive decision rule.

Per cell, over the usable candidates:

- `rank_pct_sum` = (# usable candidates with **lower** summed log-prob than GT-mult) /
  (# usable candidates). `0` = GT worse than every candidate the model sampled.
- `rank_pct_per_token` = same, on length-normalized (per-token mean) log-prob.
- `rank_pct_length_matched` = same, on summed log-prob but restricted to candidates whose token
  length is within **±20%** of the GT token length; if fewer than **5** such candidates exist,
  the cell is marked `LengthMatchUnavailable` and excluded from **this secondary only** (never
  from the primary).
- `below_all_indicator` = `1[rank_pct_sum == 0]`.

Per-system reduction: mean over the system's usable cells. Across systems: `student_t_ci`
(`src/gpu_run4/aggregation.py:22`), dof = `n_in_support − 1`.

| id | endpoint | inference |
|---|---|---|
| C-S1 | per-system mean `rank_pct_sum` (GT-mult) | `student_t_ci`, dof `n−1` |
| C-S2 | per-system mean `rank_pct_per_token` | `student_t_ci` |
| C-S3 | per-system mean `rank_pct_length_matched` | `student_t_ci` |
| C-S4 | `below_all_indicator` system-level rate (system = 1 if ALL its cells have `below_all = 1`) | Wilson 95% |
| C-S5 | paired difference `logP(GT-affine) − logP(GT-mult)` per system, summed and per-token | paired `student_t_ci`, dof `n−1` |
| C-S6 | GT per-token log-prob minus selected-candidate per-token log-prob (nats/token) | paired `student_t_ci` |
| C-S7 | re-encoding audit: mismatch rate, `unreliable_reencoding` cell rate, `AffineEncodingUnavailable` rate, `LengthMatchUnavailable` rate | descriptive; gates §10.2 |
| C-S8 | GT token length vs `rank_pct_sum` regression | **EXPLORATORY** |

**Conjunctive E2/E3 decision rule (frozen).**

- **E2 (model error) supported** iff, on the in-support subset: `C-S1`, `C-S2` and `C-S3` upper
  95% bounds are all < 0.05, **and** `C-S4 ≥ 0.80` with Wilson lower bound > 0.70.
- **E3 (search error) supported** iff `C-S1`, `C-S2` and `C-S3` lower 95% bounds are all
  ≥ 0.25, **while** the Part A primary is ≈ 0 (structure never in beam).
- **Any disagreement among C-S1/C-S2/C-S3 in direction ⇒ Part C verdict `undecidable`**, with
  the disagreement reported. This prevents choosing whichever normalization gives the tidier
  story.

### 8.4 Part D — exploratory secondary (CPU only, cheap)

Classify the **1,860 / 12,600 = 14.76%** ODEBench variable-denominator candidates
(`results/runs/gpu_run5_20260823_ddd267b0/phase1/candidates_annotated.json`) by **denominator
arity and structure**: `inv(affine_in_one_variable)` (i.e. `inv(a*x + b)`, saturating but
non-Hill) vs `inv(polynomial_degree ≥ 2)` vs `inv(multivariate)` vs other. Endpoint: the
fraction of the 14.76% that are `inv(affine)`.

**Labeled EXPLORATORY.** No confidence interval carries inferential weight; no hypothesis is
tested; it may not be cited as a C0001 finding. It exists to sharpen the C0002 question of
whether "denominators are reachable in form" is even the right description.

---

## 9. Statistical plan

### 9.1 Estimators, intervals, dof

| endpoint class | estimator | interval | dof |
|---|---|---|---|
| system-level proportions (primary, A-S1, A-S4, B-S1, B-S2, C-S4) | Bernoulli proportion over the 80 (or `n_in_support`) system-level indicators | **Wilson score, α = 0.05** | — |
| per-system means (A-S2, A-S3, C-S1..C-S3) | mean of per-system means | `src/gpu_run4/aggregation.py:22 student_t_ci`, α = 0.05 | `n − 1` (= **79** for n = 80) |
| paired differences (C-S5, C-S6) | mean of per-system paired differences | paired Student-t via `student_t_ci` on the differences | `n − 1` |
| control sensitivity/specificity | proportion over 80 (or 60 for PC3b) | Wilson score | — |

**Explicit invalid-test warning, frozen.** The natural "M3 rate minus M0 rate" comparison is
**degenerate**: M0 is 0 for all 80 systems by C-M0, so the per-system paired difference equals
the M3 indicator exactly and its sampling distribution is Bernoulli, not t. A paired Student-t
on that difference would be invalid. **The M3-vs-M0 comparison is therefore reported as the
Wilson interval on the M3 indicator, with the note that M0 ≡ 0**, and no t-test is run on it.
(A t-test *is* valid for A-S2 and the Part C paired differences, which are genuinely
continuous.)

### 9.2 Null-credibility ladder (mandatory; §requirement 6)

Because the primary hypothesis is null-shaped, a "no hits" observation is admissible **only**
if all six conditions hold:

- **N1** PC1 sensitivity = 80/80 for M1, M2 and M3.
- **N2** PC2a sensitivity ≥ 76/80 for M3 (the matcher can detect the `neg` artifact E0 alleges).
- **N3** PC2b, PC2c, PC2d each ≥ 76/80 for M3.
- **N4** PC3a specificity ≥ 78/80 and PC3b ≥ 58/60 for M2 and M3 (the matcher is not
  over-permissive).
- **N5** matcher failure fraction (`cas_timeout` + `ParseError` + `SymbolicEquivalenceTimeout`)
  **< 2%** of all scored (cell, candidate, component) triples, and cascade monotonicity
  violations ≤ 0.1%.
- **N6** the component-level rate A-S3 is **> 0**, demonstrating that the cascade *can* find
  partial matches on this very data. (This uses the disclosed 5.25% as a **sanity floor**, not
  as a discovery — §0.3.)

If any of N1–N6 fails, the Part A verdict is **`undecidable` (instrument failure)** and **no
null may be reported**.

Graded outcome ladder, frozen before any hit is counted (Wilson 95% upper bounds at n = 80):

| observed hits / 80 | Wilson 95% CI | verdict |
|---|---|---|
| **0** | [0.0000, 0.0462] | `null_credible` — H-C0001-P **supported**; GPU_RUN5's system-level claim survives |
| **1–3** | up to [0.0026, 0.1055] | `weak_positive` — H-C0001-P **unsupported**; prior claim requires **partial revision**; replication gate triggered |
| **≥ 4** | lower bound > 0.013 | `evaluator_artifact_confirmed` — H-C0001-P **refuted**; GPU_RUN5's headline interpretation **INVALIDATED**; replication gate mandatory (§15) |

**Power limitation, stated plainly.** At n = 80 the 0.05 threshold in H-C0001-P is attainable
**only** by observing exactly zero hits: 1/80 already gives a Wilson upper bound of ≈ 0.0675.
The design therefore cannot certify "≤ 5%" in the presence of even one hit. That is a genuine
limitation of the 80-system validation set and it is why the ladder above is graded rather than
binary. It also means the primary is **not** a well-powered test of small positive rates; it is
a test of *whether the rate is essentially zero*.

### 9.3 Multiplicity

**Exactly one primary endpoint** (§7.1), tested at α = 0.05, **unadjusted**.

Everything else is secondary or exploratory. Three pre-declared secondary families, each
controlled by **Holm–Bonferroni within family** at α = 0.05; both adjusted and unadjusted
intervals are reported:

| family | members |
|---|---|
| **S1** (Part A) | A-S1, A-S2, A-S4 (8 family rates) |
| **S2** (Part B) | B-S1, B-S2 |
| **S3** (Part C) | C-S1, C-S2, C-S3, C-S4, C-S5, C-S6 |

**Not in any multiplicity family** (no inference is drawn from them, by construction):
A-S3 (estimation only, §0.3), A-S5, A-S6, A-S7, A-S8, B-S3–B-S6, C-S7, C-S8, Part D, and all
control-battery rates. Every such artifact carries `inference: "descriptive"` or
`inference: "exploratory"`.

### 9.4 Non-significance is not equivalence (rule 01 item 8)

Frozen wording constraints for every C0001 artifact, report, and abstract:

1. A Part A observation of 0/80 licenses only: *"the system-level semantic-equivalence-in-beam
   rate is bounded above by 0.046 with 95% confidence."* It does **not** license "the rate is
   zero", "the matcher makes no difference", "M0 and M3 are equivalent", or "the two matchers
   agree".
2. Any Part C interval containing 0 licenses only: *"this design did not detect a difference of
   the preregistered size."* It does **not** license "GT-affine and GT-mult are equally
   probable" (C-S5) or "the GT is as likely as the sampled candidates".
3. A Part B rate of 0 licenses only: *"no validation system was out of support under the
   preregistered rewrite set."* It does **not** license "the truth is in the generator's
   support".
4. Any equivalence claim requires a **preregistered equivalence margin and a two-one-sided-test
   procedure**. None is preregistered in C0001. **Therefore no equivalence claim may be made in
   C0001 at all.** This sentence is the operative constraint; Stage 9 must enforce it.

---

## 10. Go/No-Go gates and verdict criteria

### 10.1 Gates

**Gate 0 — pre-run (all must pass before any endpoint is computed).**
1. `git branch --show-current` == `20260909_researce_GPU_RUNclaude1`; `git status --short`
   clean or fully explained in the manifest.
2. `pytest GPU_RUN5/tests/test_gpu_run5_firewall.py` green (invoked explicitly; `pytest.ini`
   omits that path).
3. Stage 5 reproducibility audit reports **zero CRITICAL** findings; `grep -rn sealed` over the
   C0001 diff shows no direct sealed read.
4. Checkpoint SHA256 == `56754040be…a5e8`.
5. Input SHA256s recorded for `phase2/train.json`, `phase2/validation.json`,
   `phase3/all_candidates.json`, and each `phase3/cells/*.json` read.
6. GPU 0 idle temperature < 70 °C; free VRAM ≥ 6.0 GiB; disk free ≥ 40 GiB.
7. Stage 6 smoke on the 24-system panel `phase4/fixed_grn_validation_panel.json` completes,
   writes a manifest, writes equation records, writes failure records, and demonstrates resume.
8. New run directory does not already exist.

**Gate A → B.** Proceed to Part B only if:
(i) the M0 arm **reproduces C-M0 exactly** (system-level 0.0 over 960 cells and 0/2040
component level) — a non-reproduction means the harness is wrong and everything downstream is
void; (ii) N1–N5 of §9.2 pass; (iii) the §7.6 defect protocol was not triggered, or was
triggered and resolved.
*If the control battery fails, Part B may still proceed* (independent instrument, no shared
matcher), but Part A is reported `undecidable` and Part C is **not** run.

**Gate B → C.** Proceed to Part C only if **both**:
(i) the Part A primary is on the `null_credible` or `weak_positive` rung — i.e. the generation
failure is real enough that "model error vs search error" is a well-posed question. If Part A
lands on `evaluator_artifact_confirmed`, **Part C is NOT run in C0001**: the premise has
changed, and the correct next move is the replication of Part A (§15), not a diagnosis of a
failure that may not exist.
(ii) Part B identifies `n_in_support ≥ 30` validation systems that are fully in support *and*
have Part A hit = 0 — i.e. there exist in-support truths that were still never generated. If
`n_in_support < 30`, Part C runs but is reported **exploratory** (underpowered), and cannot
support an E2 or E3 verdict.

**Gate C → report.** Part C endpoints are reported only if C-S7 shows the re-encoding audit
within tolerance (§8.2 step 4). Otherwise Part C is `undecidable`.

### 10.2 Abort and crash-loop conditions

- Cumulative GPU 0 time > **4.0 h**, or CPU > **24 core-hours**, or new disk > **15 GiB**
  ⇒ abort the running part, preserve partial artifacts, report what completed.
- Peak VRAM on GPU 0 > **5.5 GiB** at any sample ⇒ abort immediately (the GPU is shared with
  the user's live desktop; ~888 MiB is already held by gnome-shell/Xwayland). Fallback, already
  preregistered: reduce the Part C batch size to 1, then move Part C to the reduced design
  (`bundle_index == 0` only, 4 cells/system instead of 12); if still over, move Part C to
  GPU 1 (GTX 1060 3 GB, forward-only) with batch 1.
- GPU 0 temperature > 85 °C sustained 60 s ⇒ pause, cool, resume once.
- **Crash-loop rule (rule 06)**: **3 consecutive identical fatal failures with no new
  diagnostic information ⇒ stop and reassess.** Do not re-run. Record the three tracebacks and
  their identical signature in the cycle report, classify the bottleneck via
  `negative-result-recovery`, and end the cycle. A failed hypothesis does not justify more
  compute.
- Projected-throughput abort: if the Stage-6 smoke projects Part A > 8 core-hours or Part C
  > 2.0 GPU-hours, invoke the preregistered reduced designs (§14) **before** starting, not
  midway.

### 10.3 Supported / unsupported / undecidable

**For the primary hypothesis H-C0001-P:**

| verdict | criterion |
|---|---|
| **supported** | N1–N6 all pass; M0 reproduces C-M0; Part A primary = 0/80 (Wilson upper 0.0462 < 0.05) |
| **unsupported** | N1–N6 all pass; M0 reproduces C-M0; Part A primary ≥ 1/80 (i.e. the `weak_positive` or `evaluator_artifact_confirmed` rung) |
| **undecidable** | any of N1–N6 fails; **or** M0 fails to reproduce C-M0; **or** cascade monotonicity violation > 1%; **or** matcher failure fraction ≥ 2%; **or** the §7.6 defect protocol could not be resolved within the ceiling; **or** the run aborted before the primary was computed |

**For the four-way mechanism attribution** (secondary, reported as a **partition of the 80
systems**, never as a single winner):

| mechanism | attributed to a system when |
|---|---|
| **E0** | that system has a Part A M3 hit that M0 scored as a miss |
| **E1'** | Part A hit = 0 **and** ≥ 1 component has `U_min > 3` (out of support under the preregistered rewrite set) |
| **E2** | Part A hit = 0, fully in support, and Part C's conjunctive E2 rule holds for it (all three normalizations agree, `below_all = 1` in every cell) |
| **E3** | Part A hit = 0, fully in support, and Part C's conjunctive E3 rule holds for it |
| **unattributed** | none of the above, or Part C `undecidable` for it |

The report must state the counts in all five buckets. Overlaps are possible and must be shown,
not resolved by fiat. **No single-number "the cause is X" claim is permitted.**

---

## 11. Compute ceiling

| resource | ceiling (per rule 06 / `research_state.md` §5) | C0001 allocation |
|---|---|---|
| GPU 0 (RTX 2070, ~6.5 GiB usable, **shared with the user's live desktop**) | **≤ 4.0 GPU-hours** | Part C ≤ 2.0 h; Stage-6 smoke ≤ 0.3 h; reserve 1.7 h |
| peak VRAM on GPU 0 | **≤ 5.5 GiB** | Part C target ≤ 3.0 GiB (fp32, 60.6M params ≈ 250 MB weights, cached `src_enc` per cell, batch ≤ 8, seq ≤ 200) |
| CPU | **≤ 24 core-hours** | Part A ≤ 8 (P11 projects ≈ 1.7 single-core; 4.7× margin for GRN's larger 3-component trees and the control battery); Part B ≤ 2; Part C host-side ≤ 2; Part D ≤ 0.5; slack 11.5 |
| new disk | **≤ 15 GiB** | expected ≈ 3–6 GiB under `results/runs/gpu_runclaude1_c0001_<short7>/` |
| GPU 1 (GTX 1060 3 GB) | forward-only fallback | used only under the §10.2 VRAM fallback |

No ceiling increase is requested. A ceiling increase would be a **hard stop** requiring human
approval (rule 06); this design is sized to avoid one.

---

## 12. Run ID and artifact contract

**Run ID (frozen rule).** `gpu_runclaude1_c0001_<short7>` where `<short7>` is the first 7
characters of the git commit at run start. At freeze that is **`gpu_runclaude1_c0001_94a571b`**.
If the directory already exists, append `_v2`, `_v3`, … **Never overwrite** any of the 28
existing `results/runs/*` directories (rule 05). Verified at freeze: no existing directory
begins with `gpu_runclaude1`.

`git reset --hard` and force-push are forbidden (rule 05). Branch and commit are recorded in
every manifest via `scripts/ops/run_manifest.py`.

### 12.1 Expected artifacts (destination paths)

Run root `R = results/runs/gpu_runclaude1_c0001_<short7>/`.

| path | content |
|---|---|
| `R/manifest.json` | run manifest: branch, commit, `pip freeze`, GPU + driver, checkpoint SHA256, input data-tree fingerprints, per-phase status |
| `R/phase0/environment_audit.json` | env, GPU/temp/VRAM, disk, library versions |
| `R/phase0/checkpoint_audit.json` | checkpoint SHA256 + size + persisted generator config |
| `R/phase0/firewall_test.json` | `test_gpu_run5_firewall.py` result; `sealed_paths_read: []` |
| `R/phase0/input_fingerprints.json` | SHA256 of every input file opened |
| `R/phase1/partA_records.jsonl` | one record per (cell, candidate, component); extended 30+ field schema (§13) |
| `R/phase1/partA_cell_summary.json` | per-cell hits at M0/M1/M2/M3, oracle and selected candidate indices per level |
| `R/phase1/partA_system_summary.json` | per-system `ANY` and `MEAN` indicators at each level |
| `R/phase1/partA_endpoints.json` | primary + A-S1…A-S7 with Wilson / Student-t intervals, Holm-adjusted where applicable |
| `R/phase1/partA_controls.json` | PC1, PC2a–d, PC3a–b sensitivity/specificity vs the §7.4 thresholds; N1–N6 pass/fail |
| `R/phase1/partA_failures.jsonl` | every timeout, parse error, non-finite, monotonicity violation, with both expressions |
| `R/phase1/matcher_monotonicity.json` | cascade set-inclusion audit |
| `R/phase1/matcher_regression_cases.json` | written **only** if the §7.6 defect protocol fires |
| `R/phase2/partB_component_records.jsonl` | per truth component: realized exponents, `U_mult`, `U_affine`, `U_min`, `in_support`, budget checks |
| `R/phase2/partB_rewrites.jsonl` | every attempted rewrite with its numeric-verification outcome |
| `R/phase2/partB_endpoints.json` | B-S1…B-S6, with `interval_interpretation` field |
| `R/phase2/partB_in_support_systems.json` | the Part C eligibility list and `n_in_support` |
| `R/phase3/partC_cell_records.jsonl` | per (cell, sequence): token length, summed and per-token log-prob, encoding tag, round-trip audit result |
| `R/phase3/partC_reencoding_audit.json` | mismatch rates, `unreliable_reencoding` cells, `AffineEncodingUnavailable` cells |
| `R/phase3/partC_endpoints.json` | C-S1…C-S8 with intervals; conjunctive E2/E3 rule outcome |
| `R/phase3/partC_instrument_test.json` | the `sum/n == -mean_CE` regression test vs `teacher_forcing_loss` |
| `R/phase3/gpu_telemetry.jsonl` | VRAM/temperature samples (≤ 10 s interval) |
| `R/phase4/partD_denominator_arity.json` | Part D, tagged `exploratory` |
| `R/phase4/mechanism_partition.json` | the five-bucket E0/E1'/E2/E3/unattributed partition |
| `R/phase4/compute_accounting.json` | GPU-hours, CPU-core-hours, disk, vs ceiling |
| `GPU_RUNclaude1/analyses/C0001_analysis.md` | Stage 8 analysis |
| `GPU_RUNclaude1/reviews/C0001_statistical_review.md` | Stage 8 statistical review |
| `GPU_RUNclaude1/reviews/C0001_independent_review.md` | Stage 9 adversarial review |
| `GPU_RUNclaude1/reviews/C0001_reproducibility_audit.md` | Stage 5 audit |
| `GPU_RUNclaude1/reports/C0001_report.md` | Stage 11 cycle report (**mandatory even if null / undecidable / aborted**) |
| `GPU_RUNclaude1/manifests/C0001_artifact_manifest.json` | Stage 12 manifest |
| `GPU_RUNclaude1/manifests/C0001_checksums.sha256` | Stage 12 checksums |
| `GPU_RUNclaude1/plans/C0001_preregistration.md` / `.json` | this file and its machine twin |

Large artifacts (`partA_records.jsonl` expected ~0.5–2 GiB) are **not committed**; their paths
and SHA256s are preserved in the manifest (rule 05).

---

## 13. Record schema (rule 03 compliance)

**Base**: the 30-field `src/gpu_run4/records.py:7 GPU_RUN4_REQUIRED_FIELDS`, **extended, never
replaced**, constructed via `:76 make_formula_record(**extra)`. `campaign` is set to
`"GPU_RUNclaude1_C0001"`.

**Added fields (exhaustive list).**

*Part A matcher* — `matcher_level`, `m0_string_exponent_aware_skeleton_exact`,
`m1_canonical_exact`, `m2_cas_symbolic_equivalent`, `m3_skeleton_cas_equivalent`,
`m3_numeric_equivalent_at_matched_constants`, `component_m3_skeleton_cas_equivalent`,
`cas_timeout`, `cas_wall_time_sec`, `numeric_equivalence_finite_points`,
`matcher_failure_reason`, `monotonicity_violation`.

*Rule-03 completeness* — `true_components_infix`, `candidate_components_infix`,
`variable_to_gene`, `variable_precision`, `variable_recall`, `variable_f1`,
`unnecessary_variables`, `near_singularity`, `extrapolation_valid`, `extrapolation_extreme`,
`has_division`, `has_tan`.

*Generation vs selection* — `generation_coverage_scope` (`cell` | `system`),
`oracle_candidate_index_by_level`, `selected_candidate_index_by_rule`,
`candidate_return_shortfall`.

*Controls* — `positive_control_tag` (`none` | `PC1` | `PC2a` | `PC2b` | `PC2c` | `PC2d` |
`PC3a` | `PC3b`), `control_expected_outcome`.

*Part B* — `u_mult`, `u_affine`, `u_min`, `in_support`, `realized_hill_exponents`,
`unary_depth`, `binary_ops_per_dim`, `uses_only_in_support_operators`,
`rewrite_verification_outcome`, `out_of_support_mechanism` (`multiplicative_hill4` |
`multi_term_component` | `other` | `none`).

*Part C* — `gt_encoding` (`mult` | `affine`), `gt_logprob_sum`, `gt_logprob_per_token`,
`gt_token_length`, `candidate_logprob_sum`, `candidate_logprob_per_token`,
`candidate_token_length`, `rank_pct_sum`, `rank_pct_per_token`, `rank_pct_length_matched`,
`below_all_indicator`, `candidate_reencoding_roundtrip_exact`,
`candidate_reencoding_mismatch`, `cell_reliability_flag`, `n_usable_candidates`.

*Integrity* — `prior_information_disclosed` (mandatory and non-empty on every artifact carrying
A-S3), `inference` (`primary` | `secondary_holm` | `descriptive` | `exploratory`),
`interval_interpretation`.

**`FAILURE_REASONS` extension** — the existing 22-entry enum in
`src/gpu_run4/records.py:47` is **kept intact**; C0001 appends exactly these nine:
`CanonicalizationError`, `RewriteVerificationFailure`, `AffineEncodingUnavailable`,
`CandidateReencodingMismatch`, `NumericEquivalenceNonFinite`, `PositiveControlFailure`,
`MatcherMonotonicityViolation`, `LengthMatchUnavailable`, `EncoderCacheMiss`.

**Failure / exclusion policy (frozen).** Nothing is silently dropped. Every invalid, failed,
timed-out, or unparseable equation is written to the records with its `failure_reason` and
counted in the denominator of its own diagnostic rate (rule 01 items 4 and 5). The only
exclusions permitted are the three explicitly preregistered ones, each of which is *counted and
reported*: (a) candidates failing the Part C re-encoding round trip, excluded from the Part C
comparison distribution only; (b) cells with `LengthMatchUnavailable`, excluded from C-S3 only;
(c) cells flagged `unreliable_reencoding`, excluded from the Part C primary only. **No
exclusion of any kind is permitted from the Part A primary endpoint.**

---

## 14. Deviation policy

General rule: preserve original artifacts, append a dated `DEVIATION-nn` block to this file,
and either mark the affected endpoint **exploratory** or open a new preregistered cycle. Never
edit frozen text; never change a threshold to rescue a result (rule 01 item 3).

Named contingencies, decided **now**:

1. **Matcher times out on some fraction.** < 2% of triples → proceed, report the rate as A-S7
   (this is inside the N5 budget). 2–10% → Part A primary is reported with the timed-out
   triples counted as **non-matches** (the conservative direction against the null being
   spuriously large) **and** a second, clearly labeled sensitivity analysis counting them as
   matches; if the two disagree on the ladder rung, the verdict is `undecidable`. > 10% →
   `undecidable`; do not raise `SYMPY_OP_TIMEOUT_SEC` (that would change the frozen instrument
   mid-cycle).
2. **`all_candidates.json` lacks a needed field.** Verified present at freeze:
   `candidate_formula_raw`, `candidate_formula_canonical`, `candidate_exponent_aware_skeleton`,
   `true_formula`, `true_prefix`, `valid`, `failure_reason`, `complexity`, TED fields,
   `trajectory_metrics`. Verified **absent**: `symbolic_equivalent`, any log-prob/score. If a
   field turns out to be needed and absent, recover it from `phase3/cells/<cell_id>.json`
   (which stores the full per-cell record including `observations`); if still absent, the
   dependent endpoint is dropped, marked `not_measurable_from_stored_artifacts`, and reported
   as such. **The primary endpoint depends only on `candidate_formula_raw` and
   `teacher_components_infix`, both verified present**, so no field absence can void the
   primary.
3. **The affine-decomposed encoding cannot be constructed automatically.** Per component:
   log `AffineEncodingUnavailable` and fall back to GT-mult only. Consequences: C-S5 is dropped
   if > 20% of in-support systems lack an affine encoding; Part B's `U_affine` falls back to
   `U_mult` for those components (making `U_min = U_mult`, the **conservative** direction —
   it over-reports out-of-support, and the report must say so). **Manual hand-construction of
   affine encodings is forbidden**: it would make the rewrite set unreproducible and
   investigator-dependent.
4. **Part A projected over 8 core-hours.** Preregistered reduced design, chosen before running:
   stratified subsample of **4 of the 12 cells per system** (`bundle_index == 0`, all 4
   corruptions), giving 320 cells / ≈ 16,000 candidates. The primary endpoint definition is
   unchanged; only the number of cells contributing to the `ANY` reduction shrinks. This
   **weakens** the primary (fewer chances to find a hit), so a null under the reduced design
   must be reported with the reduced coverage stated explicitly.
5. **Part C projected over 2.0 GPU-hours.** Same reduced cell design (`bundle_index == 0`),
   then batch 1, then GPU 1.
6. **M0 fails to reproduce C-M0 = 0.0.** This is a harness defect, not a finding. Halt, diagnose,
   and if unresolved, the entire cycle is `undecidable` — no C0001 endpoint may be reported,
   because the comparator of record could not be reproduced.

---

## 15. Replication gate (rule 07 / `replication-gate`)

**Trigger, preregistered.** The replication gate fires if **any** of:
(i) the Part A primary lands on the `weak_positive` or `evaluator_artifact_confirmed` rung —
this would be a **revision or invalidation of a prior published campaign claim**, which is
exactly the high-impact case rule 07 reserves the gate for;
(ii) the independent reviewer marks any Part A result fragile;
(iii) Part C returns an E2 or E3 verdict (a new mechanism claim on a single split and a single
checkpoint).

**Minimum replication design, frozen in advance** (at least one independent factor changed):

| factor | C0001 | replication |
|---|---|---|
| **corpus** | GPU_RUN5 GRN validation, 80 systems, Hill-type | **GPU_RUN4 ODEBench**, `results/runs/gpu_run4_phase0_01/phase2/all_candidates.json`, 12,632 candidates, 63 physics/biology systems — a different corpus, different generation run, different dimensionality mix |
| **numeric-equivalence seed / points** | `seed = 0`, 32 uniform points on [0.2, 1.8] | **`seed = 1`** and an independent safe-domain point set |
| **process / path** | this run | fresh process, clean checkout at a recorded commit, **independent run ID** `results/runs/gpu_runclaude1_c0001r_<short7>/` |
| **agent** | implementation + primary analysis | executed by `lansr-replication-specialist`, distinct from implementer and primary analyst |

The ODEBench arm carries a **built-in corpus-level positive control**: the frozen string matcher
already reports 4/252 = 1.59% [0.0062, 0.0401] truth-in-beam there (C-ODEB), so the cascade must
reproduce a non-zero baseline and must return M3 ≥ M0 on that corpus. A cascade that returns
0 on ODEBench is broken, independently of anything it says about GRN.

**Recorded outcome classes**: `replicated` · `directionally_replicated` · `failed_replication` ·
`inconclusive`. Recorded **separately** at
`GPU_RUNclaude1/reports/C0001_replication.md`, never merged into the C0001 primary result. Per
rule 07, a CRITICAL reviewer finding blocks a supported conclusion regardless of the replication
outcome.

---

## 16. Rule 04 — layer analysis contract

**C0001 measures none of the six layer estimands.** No probe/readout, no CKA/similarity, no
gradient, no ablation/intervention, no IOLE/single-layer fine-tuning, no selective fine-tuning.
Nothing is averaged into a layer ranking. No layer-importance claim may appear in any C0001
artifact.

The one layer-adjacent item is A-S8, which is a **statement of a testable consequence for a
later cycle**, not a measurement: *if* the component-level match baseline is ≈ 5% rather than 0,
*then* GPU_RUN5's `component_exact_loss = 0.0` across all 16 layers was not a floor effect and
its causal-intervention analysis may have discarded usable signal. C0001 does not test this and
must not imply that it has.

---

## 17. Required reviews before the full experiment

Per the `experiment-preregistration` skill, three reviews are required **before** Stage 7, each
by an agent distinct from the implementer:

| review | agent | must confirm |
|---|---|---|
| **methodology** | `lansr-research-methodologist` | the four explanations are mutually discriminating as operationalized; Part C's restriction to the in-support subset is correct; the `ANY` vs `MEAN` reductions answer the stated questions; §0.2's correction is sound |
| **statistical** | `lansr-statistical-reviewer` | statistical unit and aggregation order; Wilson vs Student-t choices and dof; the §9.1 degenerate-paired-test warning; Holm families; the §9.2 power limitation at n = 80; the §9.4 non-equivalence constraints; that A-S3 carries no test |
| **reproducibility** | `lansr-reproducibility-auditor` | test isolation and the §2.3 firewall (grep for `sealed`); split order; no hidden fallback; checkpoint identity; artifact destinations and non-overwrite; resume behavior; failure/equation logging completeness; that `teacher_forcing_loss` is **extended, not modified** |

**Stage 9 independent review is additionally instructed** (§0.3 item 5) to check specifically
that no artifact, table, figure, or sentence presents the component-level rate (A-S3) as a
discovery, and to raise any such framing as **MAJOR**.

---

## 18. Compact statement of what is frozen

primary hypothesis H-C0001-P · the single primary endpoint
`system_semantic_equivalence_in_beam_rate_M3_ANY` over 80 validation systems with a Wilson 95%
interval · the M0/M1/M2/M3 cascade definitions, their code paths and their timeouts · the
statistical unit (system) and the within-system-then-across-system aggregation order · the
`ANY` primary reduction · the graded outcome ladder (0 / 1–3 / ≥ 4 of 80) · the N1–N6
null-credibility conditions · the PC1/PC2a–d/PC3a–b control battery and its pass thresholds ·
the §7.6 matcher-defect protocol and the preregistered expected direction (A-S3 ≥ 0.0525) ·
Part B's rewrite set B-R1…B-R4 and its 200-rewrite cap · the `U_min ≤ 3` support criterion ·
Part C's restriction to the in-support subset, the triple length-normalization reporting and the
conjunctive E2/E3 decision rule · the re-encoding audit tolerances (10% / 10%) · the three
Holm secondary families · seeds (`numeric_equivalent(seed=0)`, global 20260909) · the checkpoint
SHA256 · zero training, zero tuning, zero new decoding · the compute ceiling (4 GPU-h, 5.5 GiB
VRAM, 24 CPU-core-h, 15 GiB disk) · the crash-loop rule · the run ID rule · the artifact list ·
the replication design · the sealed-test firewall.

**Signed off (Stage 3)**: `lansr-research-methodologist` role, cycle C0001, branch
`20260909_researce_GPU_RUNclaude1`, commit `94a571b`, 2026-09-09.
