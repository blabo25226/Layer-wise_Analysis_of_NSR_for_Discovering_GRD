# C0002 — Preregistration **v1** (DRAFT — NOT FROZEN)

| field | value |
|---|---|
| cycle | `C0002` |
| stage | 3 (design) |
| status | **`DRAFT_PENDING_REVIEW`** — this document freezes nothing. It becomes binding only after `lansr-statistical-reviewer` and `lansr-reproducibility-auditor` have reviewed it independently and the supervisor marks a successor version `FROZEN`. |
| author role | `lansr-research-methodologist` (drafting only). **No review has been performed on this document.** |
| branch | `20260909_researce_GPU_RUNclaude1` |
| HEAD at authoring | `6d3f373ac01bf322cd26fde6534119b02a747564` |
| source run pinned | `results/runs/gpu_run5_20260823_ddd267b0` (read-only) |
| prior cycle artifacts | `results/runs/gpu_runclaude1_c0001_b731cdd` (read-only; `phase3/` is `INADMISSIBLE`) |
| language | English, per `.claude/rules/15-document-language.md` (frozen contracts stay English; subagents reference field and endpoint names) |
| sealed test consumed | **NONE** |
| training performed | **NONE** |
| adaptation performed | **NONE** |
| layer estimands measured | **NONE** (rule 04, §17) |

> **This document does not edit, amend or supersede any C0001 artifact.** `plans/C0001_preregistration_v2.1.md`
> remains the frozen contract of record for C0001, and C0001's verdict of record remains
> **`undecidable`**. Nothing here changes it. Where this document inherits a definition from v2.1 it
> says so and cites the line; inheritance is used deliberately, because a threshold frozen on
> 2026-09-09 cannot have been chosen in response to anything observed on 2026-09-11 (§0.3).

---

## 0. Prior information disclosed before freeze (rule 01 item 9)

Everything in this section was known, or was made known, **before** this document fixed any
threshold. It is disclosed so that a reviewer can judge which thresholds could have been
contaminated by prior observation, and so that the two mandated reviews can attack that judgement.

### 0.1 Published GPU_RUN5 / C0001 values that are comparators, not findings (rule R1)

| quantity | value | source |
|---|---|---|
| stored GRN candidates | **47,987**, `valid: true` on **47,987 / 47,987**, 0 cell failures | `results/runs/gpu_run5_20260823_ddd267b0/phase3/summary.json:"n_candidates"`; re-verified here by direct count over `phase3/cells/*.json` |
| cells | **960** = 80 systems × 12 conditions (3 bundles × 2 `noise_sigma` × 2 `subsample_rho`) | `phase3/cells/` (960 files) |
| truth-in-beam | **0 / 960** | C0001 report §1 |
| unique skeletons per beam | 9.28 mean at `beam_size = 50`, `beam_temperature = 0.1` | C0001 report |
| Part B in-support systems | **`n_in_support = 71`** of 80; 9 / 170 components out of support, all H, all `component_index = 2`, families R07 (6) and R08 (3) | `results/runs/gpu_runclaude1_c0001_b731cdd/phase2/partB_in_support_systems.json`; C0001 report §7.3 |
| Part A gains | `k_gains = 0` on all 130 H and all 40 L components | `GPU_RUNclaude1/derived/C0001/partA_component_summary.derived.json` |
| realized candidate skeleton classes | **846**; component strings **89,349**; constant-folded classes **879** → **877** under frozen M3; class pairs **2,191**; component comparisons **101,963** | `GPU_RUNclaude1/replications/C0001_opportunity_census_replication.md:121-123, :141-144, :182-183, :449` — **prose only**, see §0.5 |
| Hill-4 candidate skeleton classes found on the infix path | **11 classes / 308 comparisons, none of which has a denominator** | C0001 report / design brief §4.1 |
| S1 `phi_denom` (variable in the cancelled denominator, equality-invariant screen) | passes **5,824 / 77,983** H triples, **88 / 130** H components | `replications/C0001_opportunity_census_replication.md:167` |
| `equals_NONE` over the realized 2,191 class pairs | **exactly 0** | ibid. `:362` |
| `could_not_evaluate` label instability | **14 / 101,963** labels flip in both directions on identical inputs; recorded run 9 vs replication 7, 1 in common; **the M3 value itself agreed on all 101,963 comparisons** | ibid. §6.2 |

### 0.2 MAJOR-R3 — `lp_gt` was already computed and observed for all 960 cells

`reviews/C0001_independent_review.md` §4.3 records this and requires C0002 to disclose it.
Verified here directly: `results/runs/gpu_runclaude1_c0001_b731cdd/phase3/partC_cell_records.jsonl`
holds **960** rows with exactly the keys
`cell_id, excluded, cell_input_payload_sha256, gt_logprob_sum, gt_token_length`. Observed marginals:
`min = -846.0560302734375`, `max = -115.8770751953125`, `median = -297.5801086425781`.

**No comparison partner was computed in C0001.** `partC_endpoints.json`, `partC_reencoding_audit.json`
and `partC_identity_audit.json` do not exist in that directory, and no row carries `lp_sel`, `lp_best`,
`sb_sel` or `sb_best`. The discriminating quantity was therefore **not** observed in C0001.

Binding consequence, inherited from MAJOR-R3: **every E2/E3 endpoint in this contract is paired or
comparison-based. No absolute threshold on `lp_gt` bears any decision anywhere in this document.**

### 0.3 SELF-REPORTED DISCLOSURE — the drafting agent observed the primary indicator on 8 cells

**This is a deviation from the discipline v2.1 §11.1 imposed on itself** ("no match indicator
produced during timing calibration was aggregated, stored, printed, logged or read"). It is reported
here in full rather than concealed, and it is flagged to both reviewers as a self-declared MAJOR.

On 2026-09-11, while measuring GPU throughput to replace the design brief's unmeasured
0.3–1.0 GPU-h estimate, the drafting agent ran `teacher_forced_summed_logprob_batch` on **8 cells**
drawn with `random.seed(999)` from the 960 stored cells, under the **`C_raw`** scoring context
(§7.1), and **printed `lp_gt`, `lp_best` and `sb_best`**. The values observed:

| cell_id | n scored seq | `lp_gt` | `lp_best` | `sb_best` | GT token length |
|---|---|---|---|---|---|
| `R07_validation_d101_006_b2_n0_r0` | 51 | −423.94 | −62.14 | 0 | 69 |
| `R06_validation_d101_007_b2_n0p05_r0p5` | 51 | −435.31 | −85.64 | 0 | 63 |
| `R01_validation_d101_006_b2_n0_r0p5` | 51 | −164.92 | −23.96 | 0 | 26 |
| `R08_validation_d101_006_b1_n0_r0p5` | 51 | −257.78 | −50.94 | 0 | 52 |
| `R08_validation_d101_004_b1_n0_r0p5` | 51 | −308.66 | −62.35 | 0 | 54 |
| `R05_validation_d101_008_b1_n0_r0p5` | 51 | −550.89 | −40.44 | 0 | 60 |
| `R05_validation_d101_008_b2_n0p05_r0p5` | 51 | −548.05 | −44.66 | 0 | 60 |
| `R05_validation_d101_005_b1_n0p05_r0` | 51 | −516.80 | −48.11 | 0 | 60 |

Additionally, in verifying the greedy positive control (§10, PC-GREEDY) on a **disjoint** sample of
10 cells drawn with `random.seed(4242)`, `lp_best` was observed on those 10 cells and
`lp_greedy − lp_best` was printed. **`lp_gt` was not computed on those 10 cells**, so the
discriminating quantity was not observed there.

**Containment measures, all of which a reviewer should check rather than accept:**

1. **No threshold in this document was chosen after, or in light of, these values.** The primary
   decision rule (§8.4), the system-level cutpoint `0.5`, the aggregation
   `E3_system(s) = 1[sb_rate(s) ≥ 0.5]` and `E2_system(s) = 1[sb_rate(s) = 0]`, and the
   clustered-interval attribution rule are **inherited verbatim from
   `plans/C0001_preregistration_v2.1.md` §8.3, frozen 2026-09-09**, two days before the observation.
   That is the specific defence: they could not have been reverse-engineered from what was seen.
2. **The primary scoring context is `C_gen` (§7.1), not `C_raw`.** Both the C0001 `lp_gt` exposure
   (§0.2) and the 8-cell exposure above are under `C_raw`, which this contract demotes to a
   preregistered robustness arm. The primary quantity has never been observed.
3. **The 8 cells are not excluded.** Excluding them would be a post-hoc, outcome-dependent exclusion
   (rule 01 item 3). They stay in the 852-cell corpus and are listed above so that any influence is
   auditable. Six of the eight belong to in-support systems; two (`R07_validation_d101_006`,
   `R08_validation_d101_006`) must be checked against `partB_in_support_systems.json` at run time
   and reported either way.
4. **The direction observed (`sb_best = 0`, i.e. E2) is the campaign's preferred answer.** This makes
   the bias-audit battery of §8.5 not a courtesy but the scientific content of the cycle: an E2
   attribution that does not clear §8.5 is reported as `E2_direction_observed_but_confounded`, which
   is **not** a supported E2.

### 0.4 Deliberately not looked at before freeze

- Any value of `lp_best`, `sb_best`, `me_best` or `lp_gt` under the **`C_gen`** context.
- The realized class-level counts of the three `H0010` predicates `P_den`, `P_pow4`, `P_joint` on the
  846 realized candidate classes. The `H0010` predictions in §9.3 are written **before** that
  measurement, and the predicate function was validated only on the 12 hand-written synthetic cases
  listed verbatim in §10.4.
- The length-matched companion indicator of §8.5 BA2 on any cell.
- Any sealed artifact (§2.4).

### 0.5 The C0001 skeleton-class numbers are prose, not an archived artifact

**Established while drafting, and it changes the `H0010` design.** The numbers 846 / 89,349 / 879 /
877 / 2,191 exist only as prose in `replications/C0001_opportunity_census_replication.md` and as
pickles in a session-scoped scratchpad declared uncommitted at that file's `:692-695`.
`manifests/C0001_manifest.json` does not checksum them. They therefore enter this contract as
**unreproduced prior**, not as established denominators, and §9.2 makes their end-to-end regeneration
from the durable artifact `phase3/all_candidates.json` a **gating precondition computed before the
`H0010` endpoint**, never after it.

### 0.6 Instrument facts established while drafting this document

Each was verified directly, and each is reported because it constrains the design. None of them
alters any C0001 conclusion.

| # | fact | evidence |
|---|---|---|
| F-a | `sympy 1.13.1` (the pinned version) has `sympy/core/random.py:28-29` `import random as _random` / `rng = _random.Random()` — a module-level generator seeded from OS entropy at import. `sympy.core.random.seed(a, version=2)` exists at `:44` and reseeds **both** `rng` and `_assumptions_rng`. `Expr.equals` is at `sympy/core/expr.py:699` and reaches `_random` at `:760`; `is_constant` (`:527`) reaches it at `:654, :663, :669, :673`. | read from the installed package in `lansr310` |
| F-b | `Expr.equals` is documented three-valued (`True` / `False` / `None`). `src/evaluation/equation_metrics.py:65` is `return bool(a.equals(b))` inside `_timed_equals`, collapsing `None` to `False`. **Correction to the design brief:** the defect is at `:65`, not `:216-222`; `:215-222` is the call site inside `skeleton_equivalence_with_reason` (`:197`). `symbolic_recovery` is at **`:226`**, not `:169`. | direct read |
| F-c | `_time_limit` (`equation_metrics.py:28-53`) silently runs **unguarded** when `seconds <= 0`, when `SIGALRM` is unavailable, or when called off the main thread (`:35-41`). Every C0001 worker was a process, so the guard was active; a `ThreadPool` would have dropped it silently. | direct read |
| F-d | `use_two_hot = False` in the released checkpoint, so constants are ordinary vocabulary tokens (sign, `N<4-digit mantissa>`, `E<exponent>`; `envs/encoders.py:104-138`). `lp_gt` and `lp_best` are therefore commensurable sums of categorical log-probabilities. | `literature/C0002_literature.md` §Q2.6, confirmed against `envs/environment.py:79-83` |
| F-e | **No per-candidate model score exists anywhere in `phase3/`.** The 24-key candidate schema has no score, log-probability, NLL or rank field. | `literature/C0002_literature.md` §Q2.5 |
| F-f | **`candidate_index == 0` is NOT sample order.** `ModelWrapper` does not sort the sampling branch (`model_wrapper.py:140-186`), but one level up `SymbolicTransformerRegressor.fit` calls `sort_candidates(..., metric="r2")` (`sklearn_wrapper.py:172`, implementation `:205-228`, `descending = True` for `"r2"`), on the **input window** in original units. Verified empirically: over 40 randomly sampled cells, `trajectory_metrics.input_r2` is non-increasing in `candidate_index` in 35/40 under a mean scalarization; the 5 exceptions are all multi-dimensional systems where ODEFormer's own `compute_metrics` aggregation differs from that scalarization. **So `candidate_index == 0` is the highest-input-R² candidate, which is a trajectory-fit selection, not a decoder argmax and not a sample index.** | direct read + count |
| F-g | **The generation conditioning is not the scoring conditioning.** GPU_RUN5 generated with `rescale: true`: `Scaler(time_range=[1,10], feature_scale=1)` (`sklearn_wrapper.py:118-127`, `utils_wrapper.py:17-52`), then a point permutation from `np.random.seed(candidate_seed)` (`sklearn_wrapper.py:133-136`, captured by `gpu_run4_runtime.py:267 capture_numpy_permutation`), then bagging at `max_input_points = 10000` — **one bag**, since every cell has ≤ 150 points. The model emitted trees in **scaled** units; `Scaler.rescale_function` (`utils_wrapper.py:54-80`) wrapped them back to original units and `simplify_tree` folded the wrapping. `teacher_forcing_loss` / `teacher_forced_summed_logprob` (`src/gpu_run4/training.py:23, :51, :104`) instead condition on **raw, unrescaled, unpermuted, single-bag** points. | direct read |
| F-h | **Consequence of F-g: the model's emitted token sequence is not recoverable from the stored artifacts.** `candidate_formula_raw` is the `simplify_tree`d image of the emitted tree under `rescale_function`; the inverse of `simplify_tree` does not exist. Any `lp_best` computed in this cycle is therefore the score of a **re-spelling** of what the decoder emitted, never of the emitted token stream itself. | inference from F-g, stated as a limitation in §8.6 |

**F-f materially affects the stated basis of the retracted MAJOR-R5 reading** (which rested on
"under sampling order there is no top-1"). **This contract does not reinstate that reading and
forbids any C0002 artifact from doing so** (§1.4 item 5). The disposition of MAJOR-R5 in the light of
F-f belongs to the supervisor and to `human_review_queue.md`, not to this preregistration.

---

## 1. Frozen primary hypothesis, companion, and what may not be claimed

### 1.1 Primary — `H0001-R`

- **id**: `H0001-R` (the re-instrumentation of `H0001`. `H0001` itself was **never measured**: C0001
  Part C ran under a Gate B→C violation and the decision endpoint C2-P was never computed; that
  `phase3/` is marked `INADMISSIBLE`. This is a first measurement, not a rerun.)
- **type**: `directional_confirmatory_with_two_sided_certificates`
- **falsifiable statement**: for a GRN cell, the teacher-forced summed log-probability of the ground
  truth is **below** the maximum such score over the model's own realized candidate set. Equivalently
  the failure is prior mass (**E2**), not search (**E3**).
- **falsifier**: `lp_gt(c) > lp_best(c)` on at least half the usable cells of at least half the
  in-support systems, with the family-clustered 95% lower bound of the primary endpoint above 0.5
  (§8.4). That outcome promotes **E3** and fires `H0003` (temperature / beam sweep) **on evidence**.
- **why both directions are certificates**, and this is the whole reason the endpoint is usable:
  let `L*` be the model's unknown global-best score for the cell, `B = lp_best`, `G = lp_gt`.
  `B ≤ L*` holds for the maximum over **any** finite set of complete sequences, so
  - `G > B ⇒ L* ≥ G > B`: the returned set does not contain the global best — a search error is
    **certified** for that cell (Stahlberg & Byrne footnote 5, p. 3358, applied to the returned set);
  - `G < B ⇒ L* ≥ B > G`: the truth is **not** the model's argmax — no improvement to search under
    this model and this conditioning can make it so. Certified.
  (`SOURCE` for `γ ≤ log P(ŷ|x)`: Stahlberg & Byrne §2, p. 3357, DOI **10.18653/v1/D19-1331**,
  https://aclanthology.org/D19-1331/ . The second branch is the contrapositive of that bound and is
  `INFERENCE`; `literature/C0002_literature.md` §Q2.3.)

### 1.2 Companion — `H0010`

- **falsifiable statement**: among the realized candidate skeleton classes, the **joint** predicate
  (a cancelled denominator containing a variable **and** a numerator containing a variable that the
  denominator does not) is absent or near-absent, while its marginal constituents are realized.
- **falsifier**: `n_class_joint ≥ 6` (§9.3). Then the joint structure *is* generated and the coverage
  hole lies elsewhere — a result that closes the "structured-decoding" branch and sends C0003 to the
  support / vocabulary side, which is the cheaper repair.
- CPU only. Exhaustive classification, not a sample.

### 1.3 Novelty labels — frozen, and none may be upgraded

| item | label | binding basis |
|---|---|---|
| teacher-forced scoring as a search-error indicator | **`known`** | Stahlberg & Byrne 2019, DOI 10.18653/v1/D19-1331, verified in full (`literature/C0002_literature.md` §Q1.1) |
| `H0001-R` as an application | **`adjacent`** | ND2 SI §3.2 / Supp. Fig. 6d and `ND2/model/trainer.py:202` already compute a teacher-forced ground-truth probability under a pretrained SR model (token level). DOI 10.1038/s43588-025-00893-8 |
| `H0010` | **`adjacent`** | Sato & Sato Def. 5.1 (arXiv 2505.22081); NeSymReS §4.4 — structural-class coverage is established, always generated-vs-training |
| `H0006` (encoding audit) | **`known`** problem / **`adjacent`** audit | Sato & Sato Remark 5.2; TSRM Fig. 7 (31.8% / 39.2% round-trip failure) |
| deterministic budget for the equivalence instrument | **`adjacent`** mechanism, methodological only | egg, POPL 2021, DOI 10.1145/3434304 §5.1/§5.3 |

**No C0002 candidate may be described as novel, in any artifact, at any stage.** Any claim of the
form "first to measure the model's own probability mass on the ground truth in symbolic regression"
is **false** and must not appear. `H0001-R`'s framing must credit ND2; `H0010`'s must credit
Sato & Sato and NeSymReS.

### 1.4 Explicitly out of scope, and forbidden

1. **Arm B** (`beam_type = "search"` re-decode). Out of scope for C0002 — see §6 for the decision and
   its justification.
2. **Any selection endpoint on GRN.** The oracle is 0 on the H stratum and the per-cell selector is
   not a decoder argmax (F-f). Rule 03's three-way distinction is carried at the endpoint-name level
   (§16.2): **"selected" is not measurable on GRN this cycle** and no endpoint name claims it.
3. **Any sealed artifact.** §2.4.
4. **Any training or adaptation.** No gradient step is taken anywhere in this cycle.
5. **Reinstating the retracted MAJOR-R5 reading** ("oracle 107 vs selected 58 ⇒ selection loss 49").
   It stays retracted. F-f changes its stated basis but not its disposition, which is the
   supervisor's to make.
6. **Citing `k_gains = 0` for or against E0.** Inherited from v2.1 §9.5 item 0.
7. **Citing D19-1331 for a reference-based search-error rate.** The paper defines search errors
   against the exact global argmax from DFS (footnote 5, p. 3358) and never performs a
   reference-vs-returned comparison under any decoding procedure. §8.7 fixes the permitted wording.

---

## 2. Statistical unit, splits, firewall

### 2.1 Units and the analysis hierarchy

| level | object | role |
|---|---|---|
| candidate | one of the 42,593 in-support stored candidates | scored; **never** an analysis unit |
| cell | one of 852 in-support (system × bundle × `noise_sigma` × `subsample_rho`) | the indicator `sb_best(c)` / `me_best(c)` is defined here; **not** a resampling unit |
| **system** | one of **71** in-support GRN systems | **the analysis element of the primary endpoint** |
| family | one of 8 (R01–R08) | **the resampling cluster** |

Aggregation order is frozen: within-system mean over usable cells → system indicator → corpus rate.
A cell-level rate is **not** comparable to a system-level rate and the two are never mixed.

Dimension and family are **completely confounded** in this corpus (v2.1 §2.1); no dimension effect
may be claimed.

### 2.2 Target population

Superpopulation reading: Hill-type GRN dynamical systems emitted by the R01–R08 generator under the
frozen corruption grid, scored under the frozen ODEFormer checkpoint. A finite-population reading of
the 71 systems is recorded and rejected as the estimand; under it every interval collapses and no
generalization is licensed.

### 2.3 Splits

- **Measurement set**: GPU_RUN5 `phase2/validation.json`, 80 systems, of which 71 are in support.
- **Calibration set**: GPU_RUN5 `phase2/train.json` (240 systems) may be used only for cost
  calibration and for control construction, never for an endpoint.
- **No final test is opened in this cycle.** There is no model selection, no hyperparameter search
  and no early stopping, so there is nothing for a test set to adjudicate.
- Trajectory-level leakage is not a hazard here: no derivative-derived rows are constructed and no
  model is fitted. Splits are inherited from GPU_RUN5's `audit.json` (zero system / parameter-variant
  / trajectory duplication, fingerprint `e5edac34...ba8af`).

### 2.4 Test firewall

- `src/gpu_run5/config.py load_sealed_test` raises `PermissionError` for `phase < 8`. Every C0002
  phase is `< 8`.
- The **7** sealed files are enumerated **from the filesystem**, never from a hard-coded three-path
  list (`research_state.md` §4). `src/gpu_runclaude1/io_allowlist.py`'s
  `install_sealed_audit_hook()` / `sealed_open_guard()` are installed in every C0002 entry point, as
  at `scripts/phases/gpu_runclaude1_c0001_phase3_partc.py:249, :254`.
- Gate 0 writes `phase0/sealed_inventory.json` with ≥ 7 entries and asserts an **empty intersection**
  against the read allowlist, and asserts `sealed_paths_read == []` at every phase boundary.
- Two GRN seals are **SPENT**; `phase4/sealed_official_test.json` has had its bytes read by its own
  generating phase (R3). **No C0002 endpoint requires any of them.**

### 2.5 What cannot change after final-test access?

No final test is accessed in this cycle, so the question is answered in its stronger form: **what
cannot change after the first primary indicator of the frozen run is computed.**

Frozen at that instant and changeable only through the §18 deviation policy: the primary hypothesis
and its falsifier; the primary endpoint and its decision rule; the `0.5` system cutpoint; the
scoring contexts `C_gen` / `C_raw` and which is primary; the admissible-encoding enumeration and its
cap; the control battery and every control threshold; the exclusion rules; all seeds; the cluster
definition; the multiplicity plan; the `H0010` predicates and the `n_class_joint ≥ 6` falsifier; and
the compute ceiling. **Raising a threshold to rescue a result is forbidden without exception**
(rule 01 item 3).

---

## 3. Model, checkpoint, seeds, budgets

| item | frozen value |
|---|---|
| checkpoint | `assets/odeformer/weights/odeformer.pt`, SHA256 `56754040be5aa92ed4767fc43ee2008faa293f87c12b643e66c7df3e1623a5e8`, 464,822,385 bytes |
| package | `third_party/odeformer` via `gpu_run4_runtime.install_odeformer_path`, guarded by `assert_odeformer_not_from_github_source()`. `GitHubSourceCode/` is reference-only and must not be a runtime dependency |
| precision | **fp32 throughout**. Never fp16, never bf16, never CPU for a scored sequence — log-probability comparability across cells depends on one numeric path |
| device | GPU 0 (RTX 2070). `torch.cuda.set_per_process_memory_fraction(5.5 / 8.0, device=0)` before the first allocation |
| decode config of the stored candidates (context, never swept) | `beam_type = "sampling"`, `beam_temperature = 0.1`, `beam_size = 50`, `rescale = true`, `max_generated_output_len = 200` |
| `GLOBAL_SEED` | `20260911` |
| `SYMPY_RNG_SEED` | `20260911` — passed to `sympy.core.random.seed(...)` **in every worker process, at worker start**, before any SymPy call (§5.2) |
| `CLUSTER_BOOTSTRAP_SEED` / resamples | `20260911` / `10000` |
| `ENCODING_VERIFICATION_SEED` | `20260911`, 8 evaluation points per component, `rtol = 1e-3` (§7.2) |
| `CONTROL_CELL_SEED` | `20260911` |
| fingerprint parameters (inherited from C0001, unchanged) | stdlib `random.seed(77771)`, `mpmath.mp.dps = 40`, 10 points |
| `N_WORKERS` | **6**, declared as a **value**, not a cap (§5.2) |
| training budget | **zero**. No optimizer is constructed |
| decode budget | **zero new decoding**, except the greedy control PC-GREEDY (§10.2), capped at 40 cells |

---

## 4. Realized denominators

The two hypotheses were selected because their denominators are known by construction. Verified here
against the durable artifacts, not assumed:

| endpoint | realized denominator | how known | census required? |
|---|---|---|---|
| `H0001-R` primary | **71** in-support systems / **852** cells / **42,593** candidates, **42,593 / 42,593 `valid: true`** | counted directly over `phase3/cells/*.json` ∩ `partB_in_support_systems.json` | **no** |
| — candidates per cell | 50 on 846 cells, 49 on 5, 48 on 1 | same count | no |
| — in-support systems per family | R01 10, R02 10, R03 10, R04 10, R05 10, R06 10, R07 4, R08 7 | same count | no |
| `H0006` gate | **71** systems, each with an enumerated encoding set | enumeration is itself the census | no |
| `H0010` | exhaustive over realized candidate component strings and their classes | **derived from `phase3/all_candidates.json`, which is durable — but the C0001 counts 89,349 / 879 / 846 are prose (§0.5)** | **YES — §9.2 is a gating census, computed before the endpoint** |

**Standing requirement OC (design brief §6) is satisfied**: the only endpoint whose realized
denominator is not already established from a checksummed artifact is `H0010`'s, and for it an
opportunity census is preregistered as a gating precondition (§9.2, Gate 2), computed **before** the
endpoint and never after.

---

## 5. Instrument changes

**Every change below makes the instrument *measurable* or *reproducible*. None of them alters any
C0001 conclusion.** In particular **`k_gains = 0` is not at stake**: the Stage-10 replication
established that the M3 *value* agreed on **all 101,963** comparisons, so no redefinition of the
failure label can move it. What moves is the reproducibility of the *failure classification*, which
was never part of `k_gains`.

### 5.1 Change 1 — the reference set for the Stahlberg–Byrne indicator

**What was broken.** v2.1 §8.3 defined the decision endpoint on `lp_sel`, the log-probability of "the
selected candidate", citing `gpu_run5_selection.py:11` as "the frozen selection rule". That citation
is wrong twice over, and the implementation substitute was wrong a third way.

**The citation, corrected.** `src/evaluation/gpu_run5_selection.py:11 formula_selection_key(records,
validation_ce)` groups by `(system_id, seed)` and returns a 4-tuple lexicographic **cross-run
model-selection** key. It never indexes a candidate. A **different** function of the same name, with
a different arity, also exists at `src/gpu_run5/evaluation.py`; **cite the module path, never the
bare name**. The function that actually selects one candidate per cell is
**`src/gpu_run5/evaluation.py:107 select_candidate(candidates, rule, *, penalty, complexity_lambda)`**,
whose `"official_reconstruction"` branch returns `0` unconditionally at `:111-112`. That is the real
object; this contract cites it and does not use it for any endpoint.

**What this contract uses instead.** `lp_best`, the **maximum** over usable candidates —
Stahlberg & Byrne's γ verbatim (Alg. 1 line 12 is an `arg max` over the returned set; the set's
provenance is not part of the definition). **Sampling is admissible.** An arbitrary member of the
returned set is **not** γ and is never used. `lp_sel` does not appear as an endpoint anywhere in this
contract.

**What this makes measurable**: without it, `sb_sel` would measure "is the truth more probable than
an arbitrary T = 0.1 draw", which for a peaked decoder is nearly always true and would **fabricate
E3**. **C0001 is uncontaminated** — `lp_sel` was never computed there.

**What it does not change**: nothing in C0001. `lp_sel` has no value on record.

### 5.2 Change 2 — a deterministic budget for CAS work, and a seeded SymPy RNG

**Where it binds in C0002.** Honest scoping first: **no C0002 endpoint depends on a CAS equivalence
decision.** `H0001-R` uses log-probabilities; `H0010`'s predicates use `sympy.cancel(sympy.together(·))`
and `sympy.fraction`, with no `simplify`, no `equals`, and no equivalence test. The change is
therefore carried as a repository-level instrument repair with its own verification, **not** as a gate
on a C0002 endpoint. It is still preregistered here because the C0002 code path calls SymPy and must
not inherit the defect.

Frozen:

1. **Deterministic admission precondition replaces the wall clock as the thing that determines the
   label.** Before any SymPy call on the decision path, compute `sympy.count_ops(expr)` on the input.
   If it exceeds the frozen bound `CAS_NODE_BUDGET = 400`, the call is **not attempted** and the
   outcome is `budget_exceeded_by_input_size` — a function of the input alone, reproducible by
   construction. The 10.0 s `SIGALRM` guard is **retained as a crash-safety net only**, and its firing
   is recorded under the **separate** label `wall_clock_guard_fired`, which is counted and **must be
   0** for the run to be admissible. If it is non-zero, the affected rows are reported and the
   affected endpoint is `undecidable`, never silently rated.
2. **`sympy.core.random.seed(SYMPY_RNG_SEED)` is called in every worker process at worker start**,
   before any SymPy call. Verified in the pinned 1.13.1 (F-a): the generator is module-level and
   unseeded, `seed(...)` exists and reseeds both `rng` and `_assumptions_rng`, and `Expr.equals`
   reaches it. This closes a **third** nondeterminism mechanism, independent of the wall clock and of
   cache state. **It is a hypothesis, not a finding, that this mechanism caused any of the 14
   C0001 flips**; C0002 does not test that claim.
3. **`Expr.equals`'s raw three-valued return is recorded** wherever it is called, as
   `equals_raw ∈ {True, False, None}`. `bool(...)` is never applied to it. Realized `equals_NONE` on
   the C0001 corpus was **exactly 0**, so this changes no C0001 number; it labels a hole for future
   input distributions.
4. **`N_WORKERS = 6` is a declared value**, and every worker is a **process**, never a thread —
   `_time_limit` silently degrades off the main thread (F-c).
5. **Never call `.equals` outside the guard.** The raw return is taken by one call inside
   `_time_limit(...)` (the `step17_equals.py` shape). An unguarded probe over 2,191 pairs did not
   finish in ~25 minutes at 6-way parallelism in C0001.

**What this makes reproducible**: the failure classification becomes a function of the inputs and of
declared values, not of machine load, SymPy cache state, or OS entropy.

**What it does not change**: C0001's `k_gains = 0`, its `undecidable` verdict of record, or any
number in `C0001_report.md`.

**Declared shortfall — see §21 item 1.** A true operation-count or iteration budget *inside* a SymPy
call is not implementable without patching SymPy. egg's e-graph size / iteration limits
(DOI 10.1145/3434304 §5.1) are cited as the **precedent for the property** — an outcome that is a
function of the input terms and the rewrite set only — **not** as an available mechanism. The
`count_ops` admission bound achieves that property for admission but not for termination.

### 5.3 Change 3 — the conditioning under which sequences are scored

**What was broken.** F-g: candidates were generated under a rescaled, permuted conditioning and
returned as original-unit expressions, while the teacher-forcing helpers condition on raw,
unpermuted points. Scoring re-encoded original-unit candidates against a raw-conditioned encoder is
internally consistent but is **not** the conditioning under which the search ran, so the E3 branch
could not honestly be called a search error.

**What this contract does.** Two declared scoring contexts, both fully specified, with the matched
one primary (§7.1). **The direction of this bias was unknown**, which is worse than a known
direction; it is now measured rather than disclosed.

**What it does not change**: nothing in C0001, whose only scored quantity was `lp_gt` under `C_raw`,
which survives as this contract's robustness arm.

---

## 6. Arm A / Arm B — scope decision

**Decision: Arm A is in scope. Arm B is OUT of scope for C0002.** They are separate experiments on
different candidate sets, not alternatives; Arm B is deferred to C0003 conditional on this cycle's
outcome, and is **not** a substitute for Arm A in either direction.

| | Arm A (in scope) | Arm B (deferred) |
|---|---|---|
| candidate set | the **stored** T = 0.1 sampled set (42,593 in-support candidates) | a **new** set from `beam_type = "search"` |
| indicator | `sb_best = 1[lp_gt > lp_best]` | `sb_sel` against search's own top-1 |
| status of the indicator | a **certified lower bound** on the search-error rate | an estimate against a different returned set |

**Justification, item by item.**

1. **The literature gate makes Arm A defensible on its own.** `lp_best` over the stored sampled set
   *is* γ; Alg. 1 line 12's `arg max` says nothing about how the set was filled
   (`literature/C0002_literature.md` §Q1.3, §Q2.3). Arm B is not needed to validate Arm A.
2. **Arm B's realized denominator is unknown by construction.** How many search hypotheses return,
   how many parse, how many are `valid` — none of it is known before the compute is spent. Under the
   standing requirement OC (§4) Arm B would need its own opportunity census funded ahead of its own
   endpoint. That is precisely the failure mode C0002 was selected to avoid.
3. **Arm B's compute is unmeasured.** Arm A's is now measured at **0.233 GPU-h** for a full
   960-cell scoring pass (§14). A beam-50 *generation* pass over 852 cells has no measured basis on
   this hardware and could consume the whole 4.0 GPU-h ceiling on an unbudgeted instrument.
4. **The specific question Arm B would answer is answered in scope at near-zero cost.** "How loose is
   `lp_best` as a bound on `L*`?" is measured by **BA1** (the argmax-agreement fraction of the best
   candidate, free — the ranks are already computed) and by **PC-GREEDY** (§10.2, 40 cells,
   ≈ 80 s GPU), whose feasibility is verified: greedy beat `lp_best` on **2 of 10** probe cells with
   margins in [−45.21, +32.29] nats.
5. **Mixing them would conflate instruments.** Every C0001 and GPU_RUN5 fact is conditioned on the
   `sampling`, T = 0.1, beam-50 decode. A second decode configuration inside the same cycle would
   make a disagreement uninterpretable.

**What is thereby given up, stated plainly**: C0002 cannot report a search-error rate against what a
*search* procedure returns, and cannot bound how much of `sb_best = 0` is attributable to the
sampling temperature as opposed to the model's prior. Those remain open and are the content of Arm B.

---

## 7. Scoring contexts and the `H0006` encoding gate

### 7.1 The two frozen scoring contexts

A **scoring context** fixes (i) the encoder input and (ii) the unit system in which every scored
sequence is expressed. Within a context, the ground truth and every candidate are scored by one
function, under one conditioning, in one unit system. Contexts are never mixed inside an indicator.

**`C_gen` — matched conditioning. PRIMARY.**
1. `scaler = odeformer.model.utils_wrapper.Scaler(time_range=[1, 10], feature_scale=1)`;
   `scaled_times, scaled_traj = scaler.fit_transform(times, observed_trajectory)` on the cell's
   stored `observations["input"][0]`. (`time_range` and `feature_scale` follow from
   `SymbolicTransformerRegressor.__init__` with `params=None`, as
   `gpu_run4_runtime.make_symbolic_regressor` constructs it.)
2. `np.random.seed(int(cell["candidate_seed"]))`; `perm = np.random.permutation(len(scaled_times))`;
   apply `perm` to both arrays. This reproduces `sklearn_wrapper.py:133-136` exactly.
3. One bag (every cell has ≤ 150 points, `max_input_points = 10000`).
4. Every scored sequence is expressed in **scaled** units by the closed-form forward map, the exact
   inverse of `Scaler.rescale_function`:
   `f_s,d(x_s) = (scale[d] / a_t) · f_o,d(x_j → x_{s,j} / scale[j])`, with `(a_t, b_t, scale) =
   scaler.get_params()`; if a sequence contains `t`, additionally `t → (t − b_t) / a_t`.

   **Verified**: the map applied and its inverse recovered the original expression to
   `1e-8` relative on **300 / 300** candidates across 6 randomly chosen cells (seed 12345) spanning
   dimensions 1, 2 and 3 and both corruption settings. Scaled-unit expressions were tokenizable
   through `env.equation_encoder` on **300 / 300**.

**`C_raw` — raw conditioning. ROBUSTNESS ARM.**
Raw `times` / `observed_trajectory`, unscaled, unpermuted, single bag, every sequence in original
units — i.e. exactly what `src/gpu_run4/training.py:51 teacher_forced_summed_logprob` already does
and what C0001 used for `lp_gt`.

**Why `C_gen` is primary**: only under `C_gen` is the candidate set the set the decoder produced
*under that conditioning*, so only there does `sb_best = 1` read as a search error of the decode that
actually happened. Under `C_raw` the `G < B` certificate still holds (the truth is not the argmax
under `C_raw`), but `G > B` certifies only that the truth outscores 50 arbitrary expressions under a
conditioning the search never saw.

**Secondary but real reason, disclosed**: the leakage of §0.2 and §0.3 is entirely under `C_raw`.
Making `C_gen` primary means the primary quantity has never been observed.

### 7.2 `H0006` — the admissible-encoding enumeration, as a **hard gate**

`lp_gt` for a single spelling of the truth is a **lower bound** on the truth's probability under the
model, which biases the read toward E2 for a third time (`literature/C0002_literature.md` §Q2.4
item 4). `H0006` is therefore a precondition, not a companion.

**Frozen enumeration `E(s)` per in-support system `s`, per context:**
- `e1` = the stored `tree_encoded` from `phase2/validation.json` (prefix-derived).
- `e2` = `infix_to_model_tokens(env, teacher_infix)` (infix-derived, via
  `sympy → env.simplifier.sympy_expr_to_tree → env.equation_encoder.encode`;
  `src/gpu_runclaude1/partc_reencoding.py:85`).
- `e3 … eK` = the commutation orbit of `e2`'s tree under `add` / `mul` operand swaps, **cap 8**, in
  the enumeration order **frozen by v2.1 §8.2 step 5** (commutable binary nodes indexed in pre-order,
  root first, left to right; orbit member `t` swaps node `k` iff bit `k` of `t` is set; `t = 0` is
  the unswapped encoding). Inherited verbatim so that the order was fixed on 2026-09-09.

**Verification of each member**: decode the token list with `env.equation_encoder.decode`, then check
numeric equality against `teacher_infix` at `ENCODING_VERIFICATION_SEED = 20260911`, **8** points per
component drawn uniformly from `[0.2, 2.5]`, `rtol = 1e-3`. Members that fail are **dropped and
logged** as `EncodingVerificationFailure`, never silently.

**`lp_gt(c) = logsumexp over the verified members of E(s)`**, evaluated in the cell's context.
`lp_gt_single` (= `e1` only) and `lp_gt_max` are recorded as descriptive companions.
`Δ_enc(c) = lp_gt − lp_gt_single ≥ 0` by construction, and is the measurement of this bias.

**Gate 3 thresholds, with the evidence that each is achievable — measured, not assumed:**

| # | condition | threshold | verified achievable |
|---|---|---|---|
| 3a | every in-support system has **≥ 1 verified** encoding | **71 / 71** | **71 / 71** measured at `rtol = 1e-3` (and `e1` was scored for all 960 cells in C0001 with no failure) |
| 3b | systems with **≥ 2 verified and distinct** encodings | **≥ 64 of 71 (90%)** | **71 / 71** measured. Token lengths differ (e.g. 25 vs 24, 27 vs 30, 29 vs 30), so the two are genuinely distinct sequences, not the same list |
| 3c | `EncodingVerificationFailure` rate over enumerated members | **≤ 20%** | `e1` and `e2` both verified at 100%; only the orbit members are untested, and a failing orbit member is dropped without affecting 3a or 3b |

**If 3b fails**, the logsumexp arm is `not_measurable`, `lp_gt` falls back to `e1` alone, and **every
E2 statement in the cycle report is qualified `single_encoding_lower_bound`** — a downgrade, not an
abort.

**`H0006`'s own negative branch is informative**: if the enumeration is exhausted and `lp_gt` barely
moves (`Δ_enc` small on most cells) while truth-in-beam stays 0, then `0/960` hardens as a property
of the model rather than of the spelling, and the `H0001-R` reading is strengthened.

---

## 8. `H0001-R` — endpoints, decision rule, and the bias-audit battery

### 8.1 Per-cell quantities (both contexts)

For each of the 852 in-support cells `c`:

- `lp_gt(c)` — §7.2.
- for each stored candidate: `candidate_reencoding_roundtrip_exact`, and if usable,
  `candidate_logprob_sum`, `candidate_token_length`. **Usable** = `valid: true` **and** the
  re-encoding round trip is exact **and** the token conversion succeeds. Every non-usable candidate
  is retained with its `failure_reason` (rule 03); none is silently dropped.
- `lp_best(c)` = max over usable candidates. **This is an ORACLE quantity** (rule 03) and is never
  presented as achieved selection performance.
- `sb_best(c) = 1[lp_gt(c) > lp_best(c)]` — certified search error for `c`.
- `me_best(c) = 1[lp_gt(c) < lp_best(c)]` — certified "truth is not the argmax" for `c`.
- `tie(c) = 1[lp_gt(c) == lp_best(c)]` — counted, reported, excluded from both.
- `gt_token_rank_profile(c)` — per-position rank of the GT token in the model's distribution
  (0 = argmax), from `teacher_forced_summed_logprob_batch(..., compute_ranks=True)`.
- `argmax_agreement_best(c)` — the fraction of the best candidate's scored positions at rank 0.

### 8.2 Re-encoding audit (inherited from v2.1 §8.2 step 4, thresholds re-verified)

`encode(parse(raw)) → decode → canonicalize`, compared to the stored `candidate_formula_canonical`
after the frozen separator normalization `\|` → `,\|,` (`src/gpu_runclaude1/partc.py:96, :112`).

- mismatch → `CandidateReencodingMismatch`: excluded from the comparison distribution, **counted and
  reported**;
- > 10% of a cell's candidates mismatch → cell `unreliable_reencoding`, excluded from the decision
  endpoint, reported separately;
- > 10% of cells `unreliable_reencoding` → `H0001-R` is **`undecidable`**.

**Verified achievable**: exact round trip on **300 / 300** candidates over 6 cells (seed 12345),
i.e. a measured per-cell rate of 1.000 against a 0.90 bar.

### 8.3 System aggregation (inherited verbatim from v2.1 §8.3, frozen 2026-09-09)

`sb_rate(s)` = mean of `sb_best(c)` over the system's usable cells;
`E3_system(s) = 1[sb_rate(s) ≥ 0.5]`; `E2_system(s) = 1[sb_rate(s) = 0]`.

### 8.4 Endpoints

| id | endpoint | type | inference |
|---|---|---|---|
| **P1** | **`certified_search_error_system_rate` = Σ_s E3_system(s) / 71**, in `C_gen` | **PRIMARY** | family-clustered 95% bootstrap interval (**interval of record**) and Wilson |
| **P2** | `certified_non_argmax_system_rate` = Σ_s E2_system(s) / 71, in `C_gen` | **CO-PRIMARY** | same two intervals |
| S1 | P1 and P2 recomputed in `C_raw` | robustness (BA4) | same |
| S2 | mean `sb_rate` across systems; the cell-level `sb_best` and `me_best` rates with their denominators | descriptive | clustered |
| S3 | paired `lp_gt − lp_best` per system in nats, **summed**; and the per-token version | descriptive | clustered. **The per-token version may not bear a decision** |
| S4 | `Δ_enc` distribution, and `encoding_flip_rate` = fraction of cells where logsumexp vs single flips `sb_best` | **BA3**, gating wording | descriptive |
| S5 | per-position GT-token-rank profile, broken out by token class (operator, mantissa, exponent, `\|` separator) | descriptive | free; `classify_token_class` at `src/gpu_runclaude1/partc.py:162` |
| S6 | `argmax_agreement_best` distribution | **BA1**, gating wording | descriptive |
| S7 | `sb_best_len` — the length-controlled companion (§8.5 BA2) — plus `length_matched_partner_available_rate` | **BA2**, gating wording | descriptive |
| S8 | `rank_pct_sum(c)` = fraction of usable candidates scoring above `lp_gt`; `below_all_indicator`; the IQR of the 50 candidate scores and the GT gap in IQR units | descriptive | **carries the frozen note of v2.1 §8.3 C2-S6 verbatim: the 50 were drawn at T = 0.1 and are an extreme upper-tail sample. A low rank does not establish model error and no E2/E3 attribution may cite these** |
| S9 | instrument audit panel: re-encoding mismatch rate, `unreliable_reencoding` cell rate, `EncodingVerificationFailure` rate, `CellIdentityMismatch` rate, the 10-distinct-payload check, the `sum/n == −mean_CE` regression result, `wall_clock_guard_fired` count | descriptive | gates §11 |
| S10 | GT token length vs `lp_gt` and vs `sb_best` | **exploratory** (rule 01 item 9) | — |

**Rule 03 endpoint-name contract**: `lp_best` and every endpoint built on it are **oracle** quantities
over the generated set. `P1` and `P2` are statements about **generation and the decoder's own
preference**, never about selection. **No selected-candidate endpoint exists in this contract**, and
`generation_coverage_scope: "cell"` is carried on every record.

### 8.5 The bias-audit battery — the cycle's scientific content

Three mechanisms bias the read toward E2, which is the campaign's preferred answer
(`literature/C0002_literature.md` §Q2.7); F-g adds a fourth of unknown direction. **An E2 attribution
that does not clear this battery is reported as `E2_direction_observed_but_confounded`, which is not
a supported E2 and may not be cited as one.**

| id | mechanism | measurement | frozen consequence |
|---|---|---|---|
| **BA1** | T = 0.1 upper-tail sampling makes `B` a tight bound on `L*`, so `G > B` is hard to trip. `beam_type = "sampling"` and `beam_temperature = 0.1` are the **checkpoint's own stored defaults**, not a campaign choice | S6 `argmax_agreement_best` | if the **median** over cells ≥ **0.95**, `lp_best` is effectively the greedy score and the E3 branch was nearly unable to fire: the attribution is reported as `E2_conditional_on_near_greedy_reference` in every artifact |
| **BA2** | summed log-probability is length-confounded — D19-1331's own central finding (§4, Tab. 1, Figs. 1/3) — and Hill truths are token-longer than the polynomial candidates that dominate the realized vocabulary | S7 `sb_best_len(c) = 1[lp_gt(c) > max over usable candidates with \|len − len_gt\| ≤ round(0.20 · len_gt)]` | if `length_matched_partner_available_rate < 0.5`, the control is `length_control_not_measurable` and that is reported. Where partners exist, if `sb_best_len` and `sb_best` disagree in direction on **> 20%** of those cells, the verdict is `E2_direction_observed_but_confounded`. **Length normalization itself breaks the monotonicity that makes γ admissible** (D19-1331 §2), so no normalized variant may replace the raw certificate |
| **BA3** | a single-encoding `lp_gt` is a lower bound on the truth's probability | S4 `Δ_enc`, `encoding_flip_rate` | if `encoding_flip_rate > 0.05`, the single-encoding read is declared invalid and **only** the logsumexp read is reportable |
| **BA4** | the generation conditioning is not the scoring conditioning (F-g), direction unknown | S1 — P1 and P2 recomputed in `C_raw` | if the two contexts disagree on the corpus attribution, the verdict is **`conditioning_sensitive`** and **nothing is attributed** |

### 8.6 Declared limitation that no design can remove

By F-h the decoder's emitted token sequence is unrecoverable from the stored artifacts. `lp_best` in
either context is the score of a **re-spelling** of what the decoder emitted. The inequality
`lp_best ≤ L*` is unaffected — it holds for the maximum over any set of complete sequences — so both
certificates survive. What does not survive is any claim that `lp_best` equals the model score the
decoder assigned to its own output. Every artifact reporting `lp_best` carries
`lp_best_is_respelling: true`.

### 8.7 Frozen reporting sentences

These exact framings are binding on the cycle report, the analysis and any synthesis:

- **Permitted**: "`sb_best` is a **certified lower bound** on the search-error rate under the
  preregistered scoring context. It is not an estimate of it. D19-1331's own Beam-100 configuration
  still shows **53.62%** search errors against the exact global argmax, so an approximation built on
  a returned set systematically **undercounts** search errors."
- **Forbidden**: any sentence of the form "the search-error rate is X" citing D19-1331, or any
  sentence presenting `sb_best` as an estimate of that rate. D19-1331 defines search errors against
  the exact global argmax from DFS (footnote 5, p. 3358) and never performs a reference-versus-returned
  comparison under any decoding procedure.
- **Permitted**: "`me_best = 1` certifies that the truth is **not the model's argmax** under this
  conditioning."
- **Forbidden**: "the truth has negligible probability mass under the model." The `G < B` branch
  bounds **nothing** about how much mass the truth has. Rule 01 item 8 applies verbatim: a
  non-significant or zero indicator is **not** equivalence.
- **Forbidden**: any claim that more search **would** find the truth on the strength of `G > B`.
  D19-1331's central result is that the exact global best can be degenerate (51.8% empty
  translations, BLEU 2.1); the SR analogue — a degenerately short expression — is not ruled out here.

---

## 9. `H0010` — joint versus marginal absence (CPU only)

### 9.1 Predicates, frozen

Computed on each realized candidate **component** expression, derived **from the infix path on both
sides** (rule R1), never by searching a normalized string for a surface token (rule R1 forbids it
explicitly, and that exact error occurred twice in C0001).

Let `X = {x_0 … x_5}`, `num, den = sympy.fraction(sympy.cancel(sympy.together(e)))`:

- **`P_den`** = `den.free_symbols ∩ X ≠ ∅`
- **`P_pow4`** = there exists a subexpression `Pow(b, n)` of `e` with `b.free_symbols ∩ X ≠ ∅` and `n`
  an `Integer` with `|n| ≥ 4`. (Derivation-path invariant: SymPy normalizes `(x**2)**2 → x**4`, so
  the `pow2∘pow2` and `pow(·,4)` spellings both match. This is the structural replacement for the
  forbidden token search.)
- **`P_joint`** = `P_den ∧ ((num.free_symbols ∩ X) \ (den.free_symbols ∩ X) ≠ ∅)`

Class key: `str(constants_to_placeholder(_normalize_expr_str(expr)))`, the C0001 replication's own key
(`rep/step3_keys.py`), reimplemented in repository code.

`sympy.count_ops` admission bound `CAS_NODE_BUDGET = 400` applies (§5.2); rows that exceed it are
labelled `budget_exceeded_by_input_size`, counted, and reported — never silently dropped.

### 9.2 Gate 2 — the class census, computed **before** the endpoint

End-to-end from the durable artifact `results/runs/gpu_run5_20260823_ddd267b0/phase3/all_candidates.json`
(181,594,403 bytes), reimplemented in repository code (the C0001 pipeline lives only in a
session-scoped scratchpad, §0.5). Report:

| quantity | C0001 prose value | status |
|---|---|---|
| distinct candidate component strings + truth strings | 89,349 | **expected**, not assumed |
| constant-folded skeleton classes | 879 | expected |
| realized candidate skeleton classes | 846 | expected |
| stored candidates | 47,987 | verified here by direct count |

**Gate 2 passes if the census completes and writes `phase1/h0010_class_census.json` with its counts
and a SHA256.** Reproducing the prose values is **not** a pass condition: if they do not reproduce,
the discrepancy is reported, the C0001 prose numbers are marked **unreproduced**, and the endpoint
proceeds on the **realized** counts — which are exhaustive either way, so the denominator remains
known by construction. This is deliberate: a gate that could fail for a reason unrelated to C0002's
question must not be able to abort C0002.

### 9.3 Endpoints and the frozen prediction

Written **before** any of these quantities was measured (§0.4).

| id | endpoint | prediction |
|---|---|---|
| **H1** | `n_class_den` — classes with `P_den` | **> 0** (precondition) |
| **H2** | `n_class_pow4` — classes with `P_pow4` | **≥ 10** |
| **H3** | **`n_class_joint`** — classes with `P_joint` | **≤ 5** |
| H4 | the same three counts weighted by realized multiplicity over the 89,349 component strings | descriptive |
| H5 | the 2 × 2 table of `P_den` × `P_pow4` at class level | descriptive |

**Decision rule, frozen:**
- **`H0010` supported** iff `n_class_den > 0` **and** `n_class_pow4 ≥ 10` **and** `n_class_joint ≤ 5`.
  Reading: the marginals are generated, the joint is not; the repair is structured decoding.
- **`H0010` refuted in the joint direction** iff `n_class_joint ≥ 6`. Reading: the joint **is**
  generated; the coverage hole is elsewhere and C0003 goes to the cheaper support / vocabulary side.
- **`H0010` refuted in the marginal direction** iff `n_class_den = 0` **or** `n_class_pow4 < 10`.
  Reading: the absence is already at the marginal level — also the cheap branch. This is the
  informative negative the design brief names.

**Threshold achievability, stated rather than assumed:**
- `n_class_pow4 ≥ 10`: **verified achievable** — C0001 published **11** candidate skeleton classes
  containing nested `pow2` on the infix path (308 comparisons).
- `n_class_den > 0`: **verified achievable** — S1 `phi_denom` is an equality-invariant screen
  requiring a variable in the cancelled denominator on **both** sides of a comparison, and it passes
  **5,824 / 77,983** H triples, so at least one candidate class has one.
- `n_class_joint ≤ 5`: this is the **prediction**, not a gate, so it needs no achievability proof.
  What does need proof is that the instrument **can** return `P_joint = True`; §10.4 proves it on 4
  of 12 frozen synthetic cases.

### 9.4 Exploratory companion `H0011`

The covariate structure of the 42 no-opportunity H components (dimension, `noise_sigma`,
`subsample_rho`, family, with system clustering) is **exploratory** and must be labelled so in every
artifact (rule 01 item 9). It bears no decision. Dimension and family are fully confounded (§2.1).

---

## 10. Controls — every one with a stated, achievable expected value, verified before freeze

C0001's near-fatal defect (MAJOR-R6) was a design whose observable ceiling was 1.3× its target effect
size, so that no control could produce a non-zero value of the primary indicator and a zero result
was indistinguishable from a broken instrument. Rule R2 requires the population a control runs on to
be **verified** to have the property the control assumes; its corollary requires controls to run
**before** the expensive endpoint. Both are honoured below.

**Control cell set**: 40 cells drawn from the 852 in-support cells with `CONTROL_CELL_SEED = 20260911`,
stratified to include ≥ 3 cells from each of the 8 families. Frozen and written to
`phase0/control_cells.json` before any endpoint is computed.

### 10.1 PC-HOLDOUT — the indicator plumbing produces 1

Treat the **highest**-scoring usable candidate of a control cell as a pseudo-truth and compute
`sb_best` against the remaining usable candidates. **Expected value 1.000** on every cell whose
maximum is unique. Same indicator code path, same scorer.

**Threshold: ≥ 0.95 of control cells return 1.** Achievable by construction (arithmetic on a strict
maximum); cells with a tied maximum are counted and excluded from the denominator.

### 10.2 PC-GREEDY — the **scorer** produces 1 on a sequence the model itself prefers

This is the control C0001 did not have. From the cell's cached encoder state run
`decoder.generate(..., sample_temperature=None, max_len=200, seed=0)` — the greedy pass
`ModelWrapper` itself always runs (`model_wrapper.py:74-80`) — convert the ids to tokens via
`env.equation_id2word`, score the result with the same `teacher_forced_summed_logprob_batch`, and
compute `1[lp_greedy > lp_best]`.

**Threshold: ≥ 2 of the 40 control cells return 1.**

**Verified achievable, measured**: on a disjoint 10-cell probe (`random.seed(4242)`, `C_raw`), greedy
beat `lp_best` on **2 / 10** cells, margins `lp_greedy − lp_best ∈ [−45.21, +32.29]` nats:

| cell_id | greedy token length | `lp_greedy − lp_best` | beats |
|---|---|---|---|
| `R08_validation_d101_003_b1_n0p05_r0p5` | 51 | −14.89 | 0 |
| `R04_validation_d101_005_b1_n0_r0p5` | 44 | −6.25 | 0 |
| `R02_validation_d101_001_b0_n0p05_r0` | 22 | −9.56 | 0 |
| `R01_validation_d101_002_b1_n0_r0p5` | 31 | −28.06 | 0 |
| `R06_validation_d101_002_b1_n0p05_r0p5` | 53 | **+32.29** | **1** |
| `R04_validation_d101_003_b0_n0p05_r0p5` | 38 | **+8.35** | **1** |
| `R04_validation_d101_002_b1_n0_r0` | 47 | −18.22 | 0 |
| `R03_validation_d101_007_b1_n0_r0` | 40 | −45.21 | 0 |
| `R03_validation_d101_003_b1_n0_r0p5` | 60 | −21.43 | 0 |
| `R02_validation_d101_005_b2_n0_r0p5` | 30 | −3.65 | 0 |

At an observed rate of 0.20 the expected count on 40 cells is 8, against a bar of 2.

**If PC-GREEDY fails, the primary is `undecidable (indicator not demonstrated)`** — a zero `P1` is
then indistinguishable from a scorer that cannot produce a 1, and no E2 attribution may be made.
**This is a hard abort on the primary, evaluated in Gate 4, before the expensive pass.**

### 10.3 Negative controls

| id | construction | expected | threshold |
|---|---|---|---|
| **NC-HOLDOUT** | **lowest**-scoring usable candidate as pseudo-truth vs the rest | `sb_best = 0` on every cell | ≤ 0.05 of control cells return 1. Achievable by construction |
| **NC-CONDITION** | score the truth against an encoder pass built from a **different** cell's trajectory | `lp_gt` must move | ≥ 0.95 of control cells show \|Δ\| > 1 nat. **Verified achievable**: C0001's own stored 960 `gt_logprob_sum` values differ between bundles of the same system (e.g. −159.50254821777344 / −160.61439514160156 / −158.15951538085938 on `R01_validation_d101_000`), so a conditioning change moves the score by more than 1 nat |
| **NC-SHUFFLE-TOKENS** | score a random permutation of the GT token list | must score **below** the GT encoding | ≥ 0.95 of control cells. Not separately verified; failure downgrades S5 only and gates nothing |

### 10.4 PC/NC-H0010 — the predicate battery, 12 frozen synthetic cases

Listed verbatim so the reviewer can recompute them. Expected `(P_den, P_pow4, P_joint)`:

| expression | expected | role |
|---|---|---|
| `x_0/(1.0+x_0)` | `(T, F, F)` | Hill-1 self-regulation |
| `x_1/(1.0+x_0**2)` | `(T, F, T)` | **joint positive** |
| `x_0**4/(1.0+x_0**4)` | `(T, T, F)` | Hill-4 self |
| `x_1*x_0**4/(1.0+x_0**4)` | `(T, T, T)` | all three |
| `(x_0**2)**2/(1.0+(x_0**2)**2)` | `(T, T, F)` | **Hill-4 spelled as nested `pow2` — the R1 trap** |
| `x_0**4 + x_1` | `(F, T, F)` | `pow4` marginal, no denominator |
| `1.0*x_0 + 2.0*x_1` | `(F, F, F)` | polynomial |
| `1.0/(2.0+3.0)` | `(F, F, F)` | constant denominator, near-miss |
| `x_0*x_1/(1.0+x_2**2)` | `(T, F, T)` | joint via two other variables |
| `x_0/(x_0)` | `(F, F, F)` | cancels to 1 |
| `(x_0+x_1)/(x_0+x_1)` | `(F, F, F)` | cancels to 1, near-miss |
| `x_0**3/(1.0+x_0**3)` | `(T, F, F)` | Hill-3, `pow4` near-miss |

**Threshold: 12 / 12. Verified achievable: 12 / 12 measured** with the frozen predicate definitions
of §9.1 under `sympy 1.13.1`. Four of the twelve produce `P_joint = True`, which is the
demonstration that the instrument can return the effect `H0010` claims is absent.

### 10.5 The regression identity (NC1, inherited)

`sum_logprob / n_scored_tokens == −teacher_forcing_loss(...)` to **1e-5** on ≥ 5 fixed examples
(`src/gpu_run4/training.py:66-70`). **Verified achievable**: C0001's
`phase3/partC_instrument_test.json` records `identity_error` in the range `7.3e-08 … 8.1e-07` on
960 cells, all below `1e-5`.

---

## 11. Go / No-Go gates

Every condition below is **machine-checkable and must be implemented as a machine check**. R7 is
binding: each gate is implemented by **quoting the contract text verbatim in a comment** beside the
check, clause by clause, not from a summary. C0001 shipped a gate whose text had two clauses and
whose code had one, and Part C ran when it should not have. A gate that reads a derived field must
also assert that the code producing that field matches this contract.

**Gate 0 — preflight, before any endpoint.**
1. `git branch --show-current == 20260909_researce_GPU_RUNclaude1`; `git status --short` clean, or
   every entry enumerated and explained in the run manifest.
2. `python -m pytest -q` green, including the new C0002 tests; `GPU_RUN5/tests --collect-only` with
   zero collection errors.
3. Checkpoint SHA256 `56754040be5aa92ed4767fc43ee2008faa293f87c12b643e66c7df3e1623a5e8`.
4. `phase0/sealed_inventory.json` written with ≥ 7 entries, enumerated from the filesystem, empty
   intersection with the read allowlist; `sealed_paths_read == []`.
5. GPU 0 idle temperature < 70 °C; free VRAM ≥ 4.0 GiB; disk free ≥ 40 GiB.
6. `results/runs/gpu_runclaude1_c0002_<short7>/` does not already exist.
7. `sympy.__version__ == "1.13.1"`; `sympy.core.random.seed` is callable; a worker-start assertion
   proves `SYMPY_RNG_SEED` was applied in each of the 6 workers.
8. `phase0/control_cells.json` written (40 cells, ≥ 3 per family) **before** any scoring.

**Gate 1 — cell identity** (inherited from v2.1 §8.2 step 1, whose satisfiability was verified there
over all 960 cells): `cell_input_payload_sha256` computed; `system_id`, `bundle_index`,
`noise_sigma`, `subsample_rho` parsed from the record equal those encoded in `cell_id`;
`candidate_set_hash` and `cache_identity` match; **10 distinct payloads per system** (verified 80/80
in C0001, 0 violations). Failure ⇒ `CellIdentityMismatch`, cell excluded, counted, reported.

**Gate 2 — `H0010` class census** (§9.2). Passes on completion; the C0001 prose values are
**expected**, not required.

**Gate 3 — `H0006` encoding enumeration** (§7.2): 3a **71/71** (verified 71/71), 3b **≥ 64/71**
(verified 71/71), 3c ≤ 20%.

**Gate 4 — controls, evaluated on 40 cells BEFORE the 852-cell pass.** A failure here costs minutes,
not hours (rule R2 corollary).

| condition | threshold | evidence it is achievable |
|---|---|---|
| **PC-GREEDY** | ≥ 2 of 40 return 1 | 2/10 measured, margins up to +32.29 nats (§10.2) |
| PC-HOLDOUT | ≥ 0.95 return 1 | arithmetic on a strict maximum |
| NC-HOLDOUT | ≤ 0.05 return 1 | arithmetic |
| NC-CONDITION | ≥ 0.95 show \|Δ\| > 1 nat | C0001's stored 960 `gt_logprob_sum` differ across bundles of one system by > 1 nat |
| PC/NC-H0010 | 12/12 | 12/12 measured (§10.4) |
| regression identity | < 1e-5 on ≥ 5 examples | 7.3e-08 … 8.1e-07 measured on 960 cells |
| `C_gen` reconstruction | forward map + inverse recovers the original to 1e-8 relative on ≥ 0.98 of control-cell candidates | 300/300 measured (§7.1) |
| re-encoding round trip | ≥ 0.90 per control cell | 300/300 measured (§8.2) |

**PC-GREEDY failure ⇒ `H0001-R` is `undecidable (indicator not demonstrated)` and the 852-cell pass
does not run.** Every other Gate-4 failure is reported and downgrades the affected endpoint per its
own rule; none of them silently proceeds.

**Gate 5 — smoke.** A reduced run on 24 cells completes end to end, writes a manifest, equation
records and failure records, demonstrates resume, and projects the full pass at ≤ **2.0 GPU-hours**
and ≤ **12 CPU core-hours**. A projection above either bound invokes §18's reduced design **before**
starting, not midway.

**Gate 6 — report.** `H0001-R` endpoints are reported only if: the regression identity passes; the
re-encoding audit is within §8.2 tolerances; every scored cell passed Gate 1; Gate 3 passed;
`wall_clock_guard_fired == 0`; and BA4 (`C_gen` vs `C_raw`) has been computed. Otherwise `H0001-R`
is `undecidable`.

**Abort conditions.** Cumulative GPU > **4.0 h**, CPU > **24 core-h**, new disk > **15 GiB**, or peak
VRAM > **5.5 GiB** ⇒ abort, preserve partial artifacts, report what completed. VRAM is additionally
enforced as an allocator cap. GPU 0 > 85 °C sustained 60 s ⇒ pause, cool, resume once. **Crash-loop
rule: 3 consecutive identical fatal failures with no new diagnostic information ⇒ stop and reassess**
(rule 06). Preregistered VRAM fallback chain, in order: batch size 1 → the reduced 24-cell design →
GPU 1 (GTX 1060 3 GB, forward-only, batch 1). The chain changes **which cells** are scored, never the
numerics.

---

## 12. Statistical plan

### 12.1 Estimators and intervals

| endpoint class | estimator | interval of record |
|---|---|---|
| P1, P2 (system proportions) | plain proportion over 71 | **family-clustered bootstrap over the 8 families, `CLUSTER_BOOTSTRAP_SEED = 20260911`, 10,000 resamples**, percentile method; Wilson reported beside it and explicitly labelled as ignoring clustering |
| paired nat differences (S3) | mean of system means | family-clustered bootstrap |
| `H0010` counts | exhaustive counts over a fixed corpus | **no interval**. Every artifact carries `interval_interpretation: "deterministic_census_no_sampling_variability"` |
| control rates | proportion over 40 | Wilson, descriptive |

**Degenerate-bootstrap rule, frozen**: if all 8 family clusters give the identical value, the
percentile bootstrap returns a zero-width interval. That interval is **not** reported as evidence of
precision. In that case the interval of record becomes the **Wilson interval computed on the 8
clusters** (`n = 8`), and the artifact carries `bootstrap_degenerate: true`. With only 8 clusters the
clustered interval is wide; that is a disclosed operating characteristic, not a defect.

### 12.2 Multiplicity

- **Confirmatory family = {P1, P2} only.** Two endpoints, Holm-corrected at family-wise α = 0.05.
- `H0010`'s three counts are a **separate, deterministic** family with no sampling variability and no
  correction.
- Everything else in §8.4 is `descriptive` or `exploratory` and bears no decision. Descriptive
  endpoints are never promoted to confirmatory after the fact.

### 12.3 Non-significance is not equivalence (rule 01 item 8)

Binding sentences:

- A `P1` whose interval includes 0 does **not** establish that search errors are absent. It
  establishes that, under this conditioning and this candidate set, the certificate did not fire.
- A `P2` near 1 does **not** establish that the truth has negligible probability mass. It establishes
  that the truth is not the argmax. The `G < B` branch bounds nothing about mass.
- **No equivalence test is preregistered and none may be run post hoc.** If an equivalence claim is
  wanted, it requires its own preregistered equivalence margin, which this contract does not set
  because no defensible margin on a log-probability difference is available.
- Any zero or near-zero count is reported with its denominator and its Wilson bound, never as "no
  effect".

### 12.4 Power and operating characteristics, disclosed before the run

With 71 systems clustered into 8 families, the effective information for a proportion is closer to 8
than to 71. A family-clustered 95% interval on a mid-range proportion will be roughly 0.3–0.5 wide.
**`neither_E2_nor_E3_predominant` is therefore a plausible corpus-level outcome by construction**, and
the deliverable is primarily the **per-system partition**, which is well defined regardless of
interval width. This is disclosed now so that a wide interval cannot later be read as a failure of
the experiment.

---

## 13. Supported / unsupported / undecidable

**`H0001-R` — corpus attribution (inherited from v2.1 §8.3, then gated by §8.5):**

- **E3 predominant** iff the family-clustered 95% **lower** bound of **P1** > 0.5.
- **E2 predominant** iff the family-clustered 95% **upper** bound of **P1** < 0.5 **and** the
  clustered **lower** bound of **P2** > 0.5 **and** the §8.5 battery is clear.
- **`E2_direction_observed_but_confounded`** iff the E2 arithmetic holds but BA2 fails its
  disagreement bar or BA4 shows context disagreement. **This is not a supported E2.**
- **`conditioning_sensitive`** iff `C_gen` and `C_raw` disagree on the attribution. Nothing is
  attributed.
- **`neither_E2_nor_E3_predominant`** otherwise — a real, reportable result, explicitly distinct from
  `undecidable`.
- **`undecidable`** is reserved for **instrument failure**: PC-GREEDY fails; or Gate 6 fails; or
  `wall_clock_guard_fired > 0`; or > 10% of cells are `unreliable_reencoding`.

**`H0010`**: supported / refuted-in-the-joint-direction / refuted-in-the-marginal-direction per
§9.3. `undecidable` if Gate 2 does not complete or if the predicate battery fails 12/12.

**Every branch is informative.** If E2 is supported, no realistic budget increase surfaces the truth
and `H0003` (temperature / beam sweep) closes permanently. If E2 is rejected, `H0003` fires **on
evidence** for the first time. If `H0010` is refuted in either direction, C0003's repair is located
on the cheaper side. A null or confounded outcome is reported as such and a cycle report is written
regardless (`.claude/rules/08-cycle-persistence.md`).

---

## 14. Compute ceiling and the **measured** cost basis

Ceilings (`research_state.md` §5): ≤ **4.0 GPU-h**, ≤ **24 CPU core-h**, ≤ **5.5 GiB** peak VRAM,
≤ **15 GiB** new disk.

**Measured on this hardware while drafting** (RTX 2070, fp32, batch of 51 sequences against one
cached encoder pass, `compute_ranks=True`):

| measurement | value |
|---|---|
| 8 cells, 408 sequences | **7.0 s GPU**, 2.1 s CPU preparation |
| peak VRAM | **0.458 GiB** |
| projection to 960 cells, one context | **0.233 GPU-h**, 0.07 CPU core-h |
| tokenization + re-encoding + audit + scaling map | **≈ 0.07 s per candidate** (20.9 s / 300) |

**Projection for the full C0002 design:**

| component | GPU-h | CPU core-h | disk |
|---|---|---|---|
| primary pass, 852 cells × 2 contexts | 0.42 | — | — |
| `H0006` orbit members (cap 8) × 2 contexts | 0.07 | — | — |
| PC-GREEDY, 40 cells | 0.03 | — | — |
| smoke, 24 cells × 2 contexts | 0.02 | — | — |
| re-encoding / tokenization, 42,593 × 2 | — | 1.7 | — |
| `H0010` census over 89,349 strings | — | ≤ 8 | — |
| controls, audits, records | 0.01 | ≤ 2 | — |
| **total** | **≈ 0.55** | **≈ 12** | **< 1 GiB** |
| **ceiling** | **4.0** | **24** | **15 GiB** |
| **margin** | **≈ 7×** | **≈ 2×** | **≈ 15×** |

Peak VRAM projects to **< 1.0 GiB** against a 5.5 GiB ceiling; the design brief's < 2.5 GiB estimate
is conservative. GPU 0 is shared with the user's live desktop (≈ 559 MiB held at measurement,
41 °C), which the allocator cap accounts for.

**The `H0010` census is the only unmeasured component.** Its budget is bounded by the `count_ops`
admission rule and by the ≤ 12 CPU core-h Gate-5 projection bar; exceeding it invokes the reduced
design, not more compute.

---

## 15. Failure policy, exclusions, and their expected counts

All frozen. Every excluded row is retained with its reason (rule 03 / rule 01 items 4–5); nothing is
deleted.

| rule | expected count | disposition |
|---|---|---|
| candidate `valid: false` | **0** (42,593 / 42,593 valid, verified) | excluded from `lp_best`, retained with `failure_reason` |
| `CandidateReencodingMismatch` | **≈ 0** (300/300 exact in the probe) | excluded from the comparison distribution, counted |
| cell `unreliable_reencoding` (> 10% mismatch) | **≈ 0** | excluded from P1/P2, reported separately. > 10% of cells ⇒ `undecidable` |
| `CellIdentityMismatch` | **0** (10-distinct-payload check verified 80/80 in C0001) | cell excluded, counted |
| `EncodingVerificationFailure` | orbit members only; `e1`/`e2` verified 71/71 | member dropped, counted; ≤ 20% or Gate 3c fails |
| `tie(c)` | unknown, expected ≈ 0 | counted, excluded from both `sb_best` and `me_best`, reported |
| `budget_exceeded_by_input_size` | unknown | counted, reported, never silently rated |
| `wall_clock_guard_fired` | **must be 0** | non-zero ⇒ affected endpoint `undecidable` |
| `equals_NONE` | **0** (realized 2,191 pairs) | recorded as `equals_raw: null`, never coerced |

**No outcome-dependent exclusion is permitted.** In particular the 8 cells of §0.3 are **not**
excluded, and no cell may be excluded after its indicator is known.

---

## 16. Artifact contract and record schema

### 16.1 Run and artifacts

Run id `gpu_runclaude1_c0002_<short7>` derived from the freezing commit; if the directory exists,
append `_v2`, never overwrite (rule 05). Expected artifacts:

```
results/runs/gpu_runclaude1_c0002_<short7>/
  phase0/{manifest,sealed_inventory,control_cells,preflight}.json
  phase1/{h0010_class_census,h0010_endpoints,h0010_control_battery}.json
  phase2/{h0006_encoding_sets,h0006_gate}.json
  phase3/{controls_gate4,smoke_projection}.json
  phase4/{partI_cell_records.jsonl,partI_candidate_records.jsonl,
          partI_endpoints,partI_bias_audit,partI_instrument_audit}.json
  manifest.json, gpu_telemetry.jsonl
```

`scripts/ops/run_manifest.py` records git commit and branch, `pip freeze`, GPU and driver, checkpoint
SHA256, and a recursive data-tree fingerprint. Large artifacts need not be committed; hashes and
paths are preserved (rule 05).

### 16.2 Record schema (rule 03)

Every equation-bearing record carries, at minimum: `candidate_formula_raw`, `candidate_formula_canonical`,
`candidate_formula_skeleton`, `candidate_exponent_aware_skeleton`, the ground truth
(`true_formula`, `true_prefix`, `tree_encoded`), the variable mapping (`variable_to_gene`), numerical
fit (`trajectory_metrics`: `input_nrmse`, `selection_nrmse`, `generalization_nrmse` and their R²),
recovery (`canonical_exact`, `skeleton_exact`, `exponent_aware_skeleton_exact`,
`component_exponent_aware_skeleton_exact`), structural distance (`ted_raw`, `ted_skeleton`,
`normalized_ted`, `normalized_variable_aware_ted`, `variable_aware_ted_definition`), `complexity`,
`valid`, `failure_reason`, and the singularity / integration diagnostics already produced by
`expression_safety`.

**Rule 03's three-way distinction is carried at the endpoint-name level**, as the literature record
requires (ND2 and TPSR both collapse it; this campaign deliberately does not):

- `generation_coverage_scope: "cell"` — what the beam contained.
- `lp_best`, `oracle_*` — **oracle over the generated set**.
- **selected**: **not measurable on GRN this cycle.** Every record carries
  `selected_candidate_measurable: false` with
  `reason: "no per-candidate decoder score is stored (F-e); candidate_index==0 is the highest-input-R2 candidate (F-f), not a decoder argmax"`.
  No endpoint name contains `selected`.

Additional C0002 fields: `scoring_context ∈ {"C_gen","C_raw"}`, `lp_best_is_respelling: true`,
`encoding_set_size`, `encoding_verification_failures`, `equals_raw`, `cas_outcome`,
`prior_information_disclosed: "C0002_preregistration_v1.md §0"`.

---

## 17. Rule 04 — layer analysis contract

**No layer-wise estimand is measured in this cycle.** No probe, no CKA, no gradient norm, no
ablation, no IOLE, no selective fine-tuning. Nothing in this contract produces a layer ranking, and
nothing may be averaged into one. `H0007` (the layer-side question) is untouched and may not be
ranked against the generation-side endpoints here.

---

## 18. Deviation policy and reduced designs

- Any departure from this contract is recorded as a dated `DEVIATION-nn` block appended to a
  successor version of this file, naming what changed, why, who decided, and what it invalidates.
- **A threshold may never be raised to rescue a result** (rule 01 item 3). A timeout increase, a cap
  increase, or a seed change for that purpose is forbidden without exception.
- **Preregistered reduced designs** (invoked at Gate 5 *before* starting, never midway):
  **RD1** single context (`C_gen` only), with BA4 reported `not_measurable` and the E2 wording
  correspondingly qualified; **RD2** the 24-system fixed GRN validation panel instead of 71 systems,
  with P1/P2 reported `exploratory` and attributing nothing; **RD3** `H0010` census restricted to the
  846 realized classes without the multiplicity weighting (H4 dropped).
- Named contingency: if the `C_gen` reconstruction fails Gate 4, `C_raw` becomes primary, **and every
  E3 statement in the cycle is downgraded** to "the truth outscores all 50 candidates under a
  conditioning the search did not see", which is not a search-error claim.

---

## 19. Replication gate (rule 07)

The replication gate **fires** on any of: an E2 or E3 corpus attribution; `H0010` supported; any
result an independent reviewer marks fragile; or any result resting on a single seed or a single
context. The minimum replication changes **at least one independent factor**: a fresh process and
artifact path, a different `CONTROL_CELL_SEED`, the other scoring context, or an independent
re-derivation of `lp_best` from a separately written scorer. The confirmation is recorded separately
under `GPU_RUNclaude1/replications/` with one of `replicated` / `directionally replicated` /
`failed replication` / `inconclusive`.

An E2 or E3 attribution **may not invalidate a GPU_RUN5 result on its own**.

---

## 20. Required reviews before the full experiment

1. **`lansr-statistical-reviewer`** — units, the paired structure, the 8-cluster bootstrap and its
   degenerate case, the Holm family of two, the §12.3 equivalence prohibition, the §12.4 operating
   characteristics, and **the §0.3 self-reported leakage and whether the inherited-threshold defence
   is adequate**.
2. **`lansr-reproducibility-auditor`** — the sealed-path firewall and the 7-file enumeration, seed
   plumbing (especially `sympy.core.random.seed` in every worker), checkpoint identity, hidden
   fallbacks, the `C_gen` reconstruction, the gate implementations against R7, and artifact
   provenance.

**Neither review has been performed. This document must not be described as reviewed.**
`lansr-independent-reviewer` reviews the completed cycle separately (rule 07) and must be distinct
from implementation and primary analysis.

---

## 21. Found unimplementable, or implementable only in a weaker form, as stated in the gating inputs

Reported rather than quietly dropped.

1. **"`could_not_evaluate` on a deterministic node/operation budget."** A genuine operation-count or
   iteration budget *inside* a SymPy call does not exist and cannot be added without patching SymPy.
   egg's runners have it; SymPy has no analogue. §5.2 implements the *property* the requirement is
   after — an outcome that is a function of the inputs alone — via a `count_ops` **admission** bound
   plus a seeded RNG plus three-valued recording, and demotes the wall clock to a crash-safety net
   whose firing is a separate, counted label that must be 0. **This is weaker than the requirement as
   written**: it makes admission deterministic, not termination.
2. **"The Schwartz–Zippel numerical certificate as a declared arbitration procedure."** Not adopted
   as an arbiter. The bound is stated for polynomials over a field; the GRN skeletons are rational
   functions with variable denominators, and the clearing-of-denominators and pole-avoidance argument
   is not established in any primary source (`literature/C0002_literature.md` §Q7 item 6). The C0001
   fingerprint is used only where C0001 used it, and no new soundness claim is made for it.
3. **"Realized denominators known by construction for both hypotheses."** True for `H0001-R`
   (verified: 71 / 852 / 42,593). **Not** true as stated for `H0010`: the 846 / 89,349 / 879 counts
   are prose plus a session-scoped scratchpad, not an archived artifact (§0.5). §9.2 converts this
   into a gating census computed before the endpoint.
4. **"`candidate_index == 0` is sample order."** False (F-f). It is the highest-input-R² candidate.
   The conclusion that it cannot serve as `lp_sel` is unchanged and strengthened — a trajectory-fit
   selection is even further from a decoder argmax than a sample index would be — but the stated
   reason in the design brief and the independent review is wrong, and the disposition of MAJOR-R5 in
   the light of it belongs to the supervisor.
5. **"Score the candidates the model produced."** Impossible from the stored artifacts (F-g, F-h).
   The emitted token sequence is unrecoverable; every `lp_best` here is the score of a re-spelling.
   The certificate survives; the identification with the decoder's own score does not. This was not
   identified in any gating input and is the largest single validity limitation of the cycle.
6. **"Three mechanisms bias the read toward E2."** There are **four**: the conditioning mismatch
   (F-g) is a fourth, and unlike the other three its direction is unknown. BA4 measures it.

---

## 22. Compact statement of what is frozen

Primary `H0001-R`; falsifier; **P1** `certified_search_error_system_rate` over **71** in-support
systems in context **`C_gen`**, with **P2** co-primary; the `0.5` system cutpoint and the
`E3_system` / `E2_system` definitions, **inherited verbatim from v2.1 §8.3 (2026-09-09)**;
`lp_gt` = logsumexp over the verified admissible encoding set; `lp_best` = max over usable
candidates; the two scoring contexts and which is primary; the `H0006` gate at 71/71 and ≥ 64/71;
the control battery **PC-GREEDY ≥ 2/40, PC-HOLDOUT ≥ 0.95, NC-HOLDOUT ≤ 0.05, NC-CONDITION ≥ 0.95,
PC/NC-H0010 12/12**, all evaluated before the expensive pass; the four bias audits and their
consequences; `H0010`'s three predicates and the `n_class_joint ≥ 6` falsifier with the
`n_class_pow4 ≥ 10` and `n_class_den > 0` preconditions; seeds `20260911` and `77771`;
`N_WORKERS = 6`; `CAS_NODE_BUDGET = 400`; the exclusion rules and their expected counts; the
confirmatory family `{P1, P2}` under Holm at 0.05; the clustered bootstrap and its degenerate-case
rule; the compute ceilings; the artifact contract; and the reporting sentences of §8.7.

**Not frozen, because it is a draft**: everything above is subject to the two mandated reviews.
