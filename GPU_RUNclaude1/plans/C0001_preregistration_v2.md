# C0001 — Preregistration **v2** (re-freeze)

**Title**: Does canonicalization recover Hill-component matches the frozen string matcher missed?
A component-type-stratified test of E0, with E1' (generator support) and E2/E3 (model vs search
error) as bounded secondary parts.

| field | value |
|---|---|
| cycle | `C0001` |
| preregistration version | **v2** — supersedes `C0001_preregistration.md` (v1) |
| stage | 3 (re-preregistration after two blocking Stage-3 reviews and one retraction) |
| branch | `20260909_researce_GPU_RUNclaude1` |
| commit at freeze | `de894b4` (`Retract the C0001 neg-canonicalization finding as an analysis artifact`) |
| v1 commit provenance, corrected | v1 recorded `commit_at_freeze = 94a571b`; the preregistration files were actually introduced by **`7cfc0ff`** (AUDIT-MIN-1). `94a571b` is "prepare for claude". |
| source-run commit pinned | GPU_RUN5 inputs produced at `ddd267b07a0646140c948c1f4a92ee83e320c772`, branch `main` (`phase3/manifest.json`) — AUDIT-MIN-7 |
| date frozen | 2026-09-09 |
| status | **FROZEN** on write of this file |
| campaign | `GPU_RUNclaude1` |
| new run ID | `gpu_runclaude1_c0001_<short7>`, `<short7>` re-derived from the commit at run start; at freeze **`gpu_runclaude1_c0001_de894b4`** |
| sealed test consumed | **NONE** |
| layer estimands measured | **NONE** (§16, rule 04) |
| training performed | **NONE** |
| adaptation performed | **NONE** |

Amendments after Stage 4 begins are permitted only through the deviation policy (§14) and must be
appended as dated `DEVIATION-nn` blocks, never by editing frozen text. v1 is **not edited**; it
remains the historical record of what was frozen and why it failed review.

---

## Supersession

**This document supersedes `GPU_RUNclaude1/plans/C0001_preregistration.md` (v1) in its entirety.**
v1 must not be used to plan, implement, execute, or interpret any part of C0001. It is retained
unmodified as the historical record.

### Why v2 exists

1. **A motivating finding was retracted.** `GPU_RUNclaude1/analyses/C0001_RETRACTION_neg_finding.md`
   establishes that v1's P6 ("`neg`-normalization raises the component-level truth-in-beam rate from
   0/2040 to 107/2040") was an artifact of comparing a **prefix**-derived truth skeleton against
   **infix**-derived candidate skeletons. The "raw 0/2040" baseline never existed. The 107/2040
   figure is GPU_RUN5's **already-published** value, stored in
   `results/runs/gpu_run5_20260823_ddd267b0/phase3/beam_groups.json:component_true_exponent_aware_skeleton_in_beam`.
   **E0 loses its component-level empirical support.** E0 remains live — no one has run a
   canonicalizing CAS matcher — but it must now be tested from scratch against the *correct*
   published baselines (system 0/960, component 107/2040), never against zero.
2. **Two independent Stage-3 reviews returned blocking verdicts**, 8 CRITICAL findings between them:
   `reviews/C0001_statistical_review.md` (4 CRITICAL, 13 MAJOR, `AMEND_BEFORE_FREEZE`) and
   `reviews/C0001_reproducibility_audit.md` (4 CRITICAL, 9 MAJOR, `AMEND_BEFORE_IMPLEMENTATION`).
3. **The measured compute cost of the corrected v1 design breaches the cycle ceiling.** Fixing
   AUDIT-CRIT-3 as v1 specified projects Part A at ≈66 CPU-core-hours against a 24 core-hour
   ceiling — a rule-06 hard stop. v2 re-scopes rather than requests an increase.

Finding-ID convention used throughout: `STAT-Cn`/`STAT-Mn`/`STAT-mn` =
`reviews/C0001_statistical_review.md`; `AUDIT-CRITn`/`AUDIT-MAJn`/`AUDIT-MINn` =
`reviews/C0001_reproducibility_audit.md`; `RETRACT` =
`analyses/C0001_RETRACTION_neg_finding.md`; `R1` = `research_state.md` §8b standing rule.

### Every v1 endpoint, gate, control and rule that changed

| v1 element | v2 disposition | forced by |
|---|---|---|
| **PRIMARY** `system_semantic_equivalence_in_beam_rate_M3_ANY` (80 systems, Wilson upper < 0.05) | **DEMOTED to descriptive secondary** and renamed `system_skeleton_equivalence_in_beam_rate_M3_ANY` (A2-S3). Carries no confirmatory claim and may not invalidate a GPU_RUN5 result. | STAT-C1 (conjunction orthogonal to E0's per-component mechanism; 0.286 bits), STAT-C2 (bound invalid unless family ICC ≤ 0.011), STAT-M12, RETRACT, AUDIT-MIN-10 (naming) |
| **NEW PRIMARY** — none in v1 | `hill_component_matcher_attributable_gain_rate` (§7.1) | STAT-C1 required a confirmatory endpoint at component resolution, stratified by component type |
| `A-S1` system-level M2 rate (CAS with constants) | **CUT.** No M2 arm exists in v2. | AUDIT-CRIT-3 (node cap silently zeroes M2 for 55.1% of pairs; 52/80 truths fail equality with *themselves*), AUDIT-MAJ-4 (fix projects ≈66 core-h vs 24 ceiling, rule 06) |
| `A-S2` per-system MEAN hit fraction, M3 | Retained, **relabelled `descriptive`** (was a Holm secondary). | STAT-M4 |
| `A-S3` component-level rate "estimation only, P6 disclosed = 0.0525" | **REPLACED.** The disclosure that motivated the demotion was a misattribution: 0.0525 is M0's own published value, not a seen M3 value. v2's component-level M3 *level* is secondary A2-S1; the *gain over M0* is the primary. The unweighted per-system-mean estimator is dropped entirely. | RETRACT, STAT-C1, STAT-M1 (estimand mismatch, admissible range [0.052, 0.629]), STAT-M2 (3.78× over-weighting of 1-D families), STAT-M3 (`student_t_ci` coverage 0.909, negative lower limits) |
| `A-S4` per-family rates | Retained descriptive; explicit note that 0/10 → [0, 0.278] cannot establish family homogeneity. | STAT-m7 |
| `A-S5` cascade increment table | Retained descriptive, **restricted to M0/M1/M3** (M2 column removed). | AUDIT-CRIT-3 |
| `A-S6` oracle vs selected candidate | Retained descriptive, unchanged. | — (endorsed) |
| `A-S7` matcher failure accounting | **PROMOTED** to a reported endpoint with a pre-specified maximum above which the primary is `undecidable`, and extended to cover `could_not_evaluate` outcomes that v1 could not see. | AUDIT-CRIT-3, AUDIT-MAJ-6 |
| `A-S8` layer-consequence statement | Retained as a statement only, **re-grounded**: in-beam component coverage (107/2040, published) and `component_exact_loss` under causal intervention are **different estimands**; v1's inference moved between them illegitimately. | RETRACT, rule 04 |
| `N6` null-credibility condition (`A-S3 > 0`) | **DROPPED.** | RETRACT, STAT-M1 (vacuous by construction; two contradictory thresholds) |
| §7.6 matcher-defect trigger `A-S3 ≥ 0.0525` | **DROPPED**, replaced by exact reproduction of GPU_RUN5's stored per-candidate fields for all 47,987 candidates (§7.6). | RETRACT, AUDIT-CRIT-1, STAT-M1, R1 |
| Comparator `C-M0c = 0/2040` | **CORRECTED to `107/2040 = 0.0525`.** | AUDIT-CRIT-1 (a correct M0 implementation would have tripped v1's own Gate A→B and voided the cycle) |
| Comparator `C-NEG` (crude `neg` folder, "lower bound on what a canonicalizer should find") | **DROPPED.** It was a re-derivation of GPU_RUN5's published value. | RETRACT, AUDIT-CRIT-2, R1 |
| `PC1` identity control (inject the truth as its own candidate) | **REPLACED by `PC0`**, which calls the M3 implementation directly and bypasses `compare_formulas`. v1's PC1 passed 80/80 only because `formulas.py:493` short-circuits `symbolic = 1.0` when `canonical_exact == 1.0`; the CAS path alone gives 28/80. | AUDIT-CRIT-4 |
| `N1` (PC1 = 80/80 for M1, M2, M3) | Redefined on PC0 and on M3's own code path; the M2 clause is removed with M2. | AUDIT-CRIT-4, AUDIT-CRIT-3 |
| Part C step 1 fairness verification via `input_trajectory_checksum` | **REPLACED** by `cell_input_payload_sha256` (a digest of the actual conditioning payload) plus explicit cell-identity assertions. `input_trajectory_checksum` is relabelled a **system-identity** check: measured 80 distinct values over 80 systems, constant across all 12 cells of every system, while the 12 cells carry 10 distinct payloads. | STAT-C3 |
| §5 item 3 ("There is no 'GT gets a special path' asymmetry") | **AMENDED.** True at the code level, false at the estimand level: the GT is scored as one of ~26–664 equivalent encodings. Preregistered as a directional bias toward E2, with magnitude. | STAT-C3, STAT-M9 |
| `C-S1`/`C-S2`/`C-S3` (`rank_pct_sum`, `rank_pct_per_token`, `rank_pct_length_matched`) and the conjunctive E2/E3 rule | **DEMOTED to descriptive**; the conjunctive rule is **DROPPED**. | STAT-C4 (T = 0.1 gives an extreme upper-tail sample; a GT above 99% of the model's mass still falls below all 50 draws), STAT-M10 (undecidable by construction, undefined "direction", unreachable E2 at sd ≥ 0.134), STAT-M11 |
| `C-S4` `below_all_indicator` system rate (E2 threshold ≥ 0.80, Wilson lower > 0.70) | **DEMOTED to descriptive.** As written it passed by construction, giving the E2 verdict a false-positive rate near 1. | STAT-C4 |
| `C-S6` (per-token GT minus selected candidate) | **PROMOTED and redefined** as the paired Stahlberg–Byrne indicator on **summed** log-probability; this is now the sole E2/E3 discriminator. | STAT-C4, STAT-M11 |
| Length-normalization policy (triple report, conjunctive veto) | **REPLACED.** Summed log-prob is the only variant that is a probability comparison and the only one that may bear a decision. Per-token mean is not the probability of anything; ±20% length matching selects on a structure-correlated variable with an outcome-dependent analyzed set. Both retained as descriptive only. | STAT-M11 |
| Holm–Bonferroni families S1/S2/S3 | **DROPPED entirely.** No nulls or p-values were ever defined; S2 corrected a deterministic census; S1's members are deterministic re-reductions of the primary; S1's *m* was ambiguous; S3 was doubly specified. Secondaries are explicitly `descriptive`. | STAT-M4 |
| §9.4 item 4 ("no equivalence claim may be made in C0001 at all") | **REWRITTEN** — it contradicted the primary and instructed Stage 9 to strike it. | STAT-M6 |
| Verdict label `null_credible` | **RENAMED** `no_gain_observed_bound_only`, and every artifact carrying it must carry the **v2 §9.5 item 1** sentence verbatim in a machine-readable field. | STAT-M7 |
| Outcome-ladder CI values (`0.0462`, `0.0026`, `0.1055`, "lower bound > 0.013") | **CORRECTED** to the true Wilson values at n = 80; v1's were computed at n = 79 and `0.013` matched no method. Operating-characteristic tables and false-positive rates appended. | STAT-m1, STAT-M8 |
| §2.1 cell-grid description ("4 corruptions × 3 bundles") | **CORRECTED**: one initial condition and one source trajectory per system; 12 cells → 10 distinct input payloads; the three clean cells are byte-identical across bundles in 80/80 systems and differ only in decode seed. Scope sentence added to every rate. | STAT-M12 |
| §14 deviations 4 and 5, reduced design (`bundle_index == 0`, all 4 corruptions) | **CHANGED** to span all three bundles: 6 cells = {b0, b1, b2} × {(0,0), (0.05, 0.5)}. v1's subsample kept the four *most* mutually dependent cells and discarded the dimension GPU_RUN5 measured least stable (bundle, Spearman 0.480). | STAT-M13 |
| M3 specification (`symbolic_recovery(...)["skeleton"]`, "plus `_approximately_equivalent`, plus `to_skeleton`") | **PINNED to exactly `["skeleton"]`.** The "plus" clause was not a composition rule and admitted three readings with different rates; `["equiv"]` additionally carries a hidden `equiv = skeleton` fallback at `equation_metrics.py:205`. | AUDIT-MAJ-1 |
| Primary endpoint name containing "semantic equivalence" | **RENAMED** to "skeleton equivalence" everywhere. M3 collapses every numeric constant to `c` (`equation_metrics.py:162-163`); calling that semantic equivalence invites the conflation rule 03 forbids. | AUDIT-MIN-10 |
| Gate 0 item 2 (`pytest GPU_RUN5/tests/test_gpu_run5_firewall.py`) | **CHANGED.** That file is 17 lines, two tests, one of them a firewall test over a `tmp_path` file, validating an accessor **C0001 never calls**. The substantive firewall-ordering assertions are in `test_gpu_run5_phase8.py:541-544` and are currently un-collectable: 6 files raise `ModuleNotFoundError: No module named 'scripts'` without `PYTHONPATH=.`. | AUDIT-MAJ-9, `research_state.md` §8 defect 6 |
| `run_manifest.py --data-path` (unspecified in v1) | **Explicit file-level allowlist preregistered.** `tree_sha256` at `scripts/ops/run_manifest.py:28` does `rglob("*")` and byte-reads every file; pointed at a GPU_RUN5 run root it would open all three seals including the campaign's only **unspent** one. GPU_RUN5's own phase 8 treats hashing sealed bytes as *the test-open event*. | AUDIT-MAJ-2, AUDIT-MAJ-3, `research_state.md` §8 defect 7, rule 02 |
| Part A parallelization model (unstated in v1) | **Process-based parallelism preregistered**, with a smoke assertion that the timeout guard fires inside a worker. `_time_limit` silently no-ops off the main thread (`equation_metrics.py:38-45`), so thread parallelism removes every SymPy wall-clock guard v1 relied on. | AUDIT-MAJ-5 |
| Part C re-encoding audit (compare to `candidate_formula_canonical`; >10% aborts Part C) | **Separator normalization specified**: `\|` ↔ `,\|,` before comparison. Unnormalized, raw prefix round-trip equality is 20/80 (the 1-D systems only) and 80/80 after GPU_RUN5's own normalization (`gpu_run5_phase2.py:189`) — v1 would have self-aborted at ≈100% mismatch for a cosmetic reason. | AUDIT-MAJ-7 |
| Replication "changed factor" = `numeric_equivalent(seed 0 → 1)` | **CORRECTED.** That function is unreachable from the primary matcher; M3's numeric grid is hard-coded and non-random (`equation_metrics.py:72-73`). With M3 pinned to `["skeleton"]` it is not called at all. The replication varies **corpus + process + agent**; the primary matcher is deterministic. | AUDIT-MAJ-8 |
| Silent non-match paths (`formulas.py:451`, `equation_metrics.py:193`, `to_skeleton` → `None`) | **`proved_different` and `could_not_evaluate` separated at every cascade level**, each non-match carries an explicit `failure_reason`, and the could-not-evaluate rate is a reported endpoint with a frozen maximum. | AUDIT-CRIT-3, AUDIT-MAJ-6 |
| **Part D** (ODEBench denominator-arity classification, exploratory) | **CUT.** It bears on no C0001 endpoint and dilutes a cycle that must answer one question cleanly. Routed to `hypothesis_tree.md` as a C0002 candidate. | §18 (scope discipline) |
| Compute basis (P11: 129 ms/candidate on ODEBench → 1.72 core-h, "4.7× margin") | **REPLACED by a measured basis** on the endpoint corpus: 795 ms/candidate mean, 604 ms median, over 150 real GRN candidates → **10.60 core-h** for all 47,987, 6.2× v1's calibration and above v1's own 8 core-h allocation. | AUDIT-MAJ-4 |
| PC3a threshold "≥ 78/80 NON-match" | **Eligible set defined**: not all 80 systems have an alterable realized Hill exponent (24/80 carry nested `pow`; the auditor's crude rewrite reached 48/80). Threshold stated against the eligible set. | AUDIT-MIN-9 |
| `.../phase1/matcher_regression_cases.json` write path | **`R/phase1/...`** explicitly, everywhere. `...` abbreviated the *GPU_RUN5* run directory elsewhere in v1 — a rule-05 hazard. | AUDIT-MIN-3 |
| Citations `evaluation.py:40`, `records.py:47`, run-dir count 28, VRAM 7,782 MiB | **CORRECTED** to `evaluation.py:41`, `records.py:50`, 27 directories + 1 stray log file, and 8,192 MiB total / 7,154 MiB free / 49 °C measured. | AUDIT-MIN-8, AUDIT-MIN-2, AUDIT-MIN-6 |

### What v2 deliberately keeps unchanged

The reviewers recorded 33 verified-positive items. v2 changes none of them. Explicitly retained
because both reviewers endorsed them by name: the **system as the statistical unit** and the stated
reason for it; the **`ANY`-over-cells reduction** as the generation-coverage estimand and as the
anti-conservative direction for a null-shaped claim; the **degenerate-paired-test warning** (M0 ≡ 0
at system level makes the M3 − M0 difference Bernoulli, not t, so no t-test is run on it);
**PC3a/PC3b** as specificity controls; **M3 as the most permissive level**, whose four-matcher
multiplicity is genuinely absorbed under monotonicity because M3 dominates the cascade; the
**prior-information ledger** and its mandatory machine-readable disclosure field; **v1 §9.4 items 1–3** (retained as v2 §9.5 items 1–3)
verbatim; Part B's `interval_interpretation: "generator_sampling_not_measurement_error"`;
**retention of invalid and failed candidates** in every denominator; usable-candidate denominators
rather than a hardcoded 50; the additive Part C instrument with its `sum/n == −mean_CE` regression
test; the crash-loop rule; and the rule-03 30-field record schema with the
generation-coverage / oracle-candidate / selected-candidate distinction intact.

---

## 0. Prior information disclosed before freeze (rule 01 item 9)

This cycle is **not blind**, and it is now *less* blind than v1 was: two Stage-3 reviews measured
quantities on the endpoint corpus. Everything observed before this freeze is declared here so that
no downstream artifact can present it as a C0001 discovery.

### 0.1 Published GPU_RUN5 values that are comparators, not findings (R1)

| # | quantity | value | source | role in v2 |
|---|---|---|---|---|
| **P0a** | `true_exponent_aware_skeleton_in_beam` (system level) | **0/960 cells = 0.0000**, and 0/120 in every family | `phase3/beam_groups.json` | comparator `C-M0`; the published claim whose interpretation is under test |
| **P0b** | `component_true_exponent_aware_skeleton_in_beam` | **107/2040 = 0.0525**; by family R01 0/120, R02 0/120, R03 0/240, **R04 56/240**, R05 0/240, R06 0/360, **R07 17/360**, **R08 34/360** | `phase3/beam_groups.json` | comparator `C-M0c`. **This is the frozen string matcher's own value.** It is not an artifact, not a discovery, and not a floor at zero. |
| **P0c** | stored per-candidate fields | `exponent_aware_skeleton_exact` = 0.0 for all 47,987; `canonical_exact` = 0.0 for all 47,987; `skeleton_exact` = 0.0 for all 47,987; `component_exponent_aware_skeleton_exact` = 1.0 for **2,235 of 101,963** component comparisons | audit §4 | the only non-degenerate signal in the stored data; Gate A→B requires its exact reproduction |
| **P0d** | deduction from P0a + P0b | R01 and R02 are **1-dimensional**, so a component match *is* a system match there; 0/120 at system level therefore forces **0 of the 107 component matches in any dim-1 system**. All 107 lie in the 1,800 dim ≥ 2 component-cells (rate 0.0594 there, 0.0000 in dim-1). | STAT-C1, verified from `phase2/validation.json` | a published-data deduction, not a C0001 result |

**Retracted and unavailable as evidence** (`RETRACT`): the claim that the frozen matcher scored 107
real component matches as misses; the claim that GPU_RUN5's component-level measurement was biased
to zero by the matcher; the claim that the `component_exact_loss = 0.0` floor was matcher-induced.
v1's P5 and P6 are withdrawn as *findings*. No v2 element may depend on a 0/2040 baseline.

### 0.2 Truth-side facts (no outcome content)

| # | quantity | value | source | consequence |
|---|---|---|---|---|
| P1 | GRN truths `teacher_valid` | 240/240 train, 80/80 validation; prefix round-trip exact 80/80 and 240/240 under GPU_RUN5's `\|` ↔ `,\|,` normalization | Stage 1; AUDIT-OK-7 | **E1 (raw expressibility) REFUTED. Not re-tested. Cited only.** |
| P2 | zero-probability operators under the checkpoint's persisted generator | `abs, sqrt, log, exp, arcsin, cos, arccos, tan, arctan, pow3, sub, div` all exactly 0.0 | Stage 1 addendum | fixed constraint, not an endpoint |
| P3 | GT teacher token length, validation | min 19, median 47, mean 45.7, max 80 | Stage 1 | Part C length policy (§8.3) |
| P4 | `neg` node in truth exponent-aware skeletons vs candidates | truths **prefix-derived** 960/960; candidates **infix-derived** 1,541/47,987 = 3.2% | `C0001_exploratory_neg_canonicalization.md`, corrected by `RETRACT` | **These two counts come from different derivation paths and must never be differenced.** What survives is the *encoding* fact: the GRN generator writes decay as `-1 * k * x` while ODEFormer must use a signed constant, because `sub` and `div` both have exactly zero generation probability. This is the asymmetry PC2a tests. It is **not** a defect in GPU_RUN5's measurement. |
| P5 | nested `pow2,pow2` (realized Hill exponent 4) | 39/170 validation components, 24/80 systems; 130/510 train components | v1 §0.2, AUDIT-OK-14 | E1' is LIVE; defines PC3a's eligible set |
| P6 | train-split non-identity unary count per truth component | 80/510 components (15.69%) and 60/240 systems (25.0%) exceed `max_unary_ops_per_dim = 3` | v1 §0.1 | Part B has a non-degenerate effect |
| P7 | truth token census (per 960 validation cells) | `CONST` 6120, `mul` 4920, `add` 4080, `x_0` 2760, `pow` 2376, `2` 2376, **`neg` 2040**, **`inv` 1680**, `x_1` 1680, `x_2` 480 | exploratory note | basis for the §7.2 predicted stratum sizes; `neg` 2040/960 = 2.125 per system = exactly one per component (170/80 = 2.125), `inv` 1680/960 = 1.75 per system |
| P8 | corpus shape | R01 R02 dim 1, R03 R04 R05 dim 2, R06 R07 R08 dim 3; 10 systems each; 20/30/30 systems, 170 components | `phase2/validation.json` | **dimension is perfectly confounded with family** (STAT-C2) |
| P9 | stored candidate fields | no `symbolic_equivalent` field; no log-probability/score field of any kind | v1 §0.1, AUDIT-OK-6 | Part A must recompute equivalence; Part C must re-encode and re-score |
| P10 | candidate-set completeness | 951 cells with 50, 6 with 49, 2 with 48, 1 with 47 → 47,987; shortfall 13 | v1 §0.1 | denominators are *usable candidates*, never a hardcoded 50 |
| P11 | cell-grid structure (**corrects v1 §2.1**) | one initial condition and one source trajectory per system; 12 cells → **10** distinct `observations["input"]` payloads; the three clean `(σ=0, ρ=0)` cells are **byte-identical across bundles in 80/80 systems**, differing only in decode seed; `input_trajectory_checksum` takes 80 distinct values over 80 systems and is **constant across each system's 12 cells** | STAT-C3, STAT-M12 | every rate is conditional on one IC per system; the v1 fairness check was vacuous |

### 0.3 Quantities measured on the endpoint corpus by the Stage-3 reviewers

These were measured **before** this freeze and are therefore disclosed prior information. Two of
them are control-battery outcomes, which means those controls are now *verifications of a known
value* rather than blind checks, and must be reported as such.

| # | quantity | value | source | consequence |
|---|---|---|---|---|
| Q1 | **PC2a sensitivity of M3** — rewrite every `-1 * k * x_i` to `(-k) * x_i` in all 80 truths | **M3 = 80/80** | AUDIT-OK-8 | M3 *can* detect the exact asymmetry E0 alleges. N2 is now a **verification**, not a discovery. If the C0001 run does not reproduce 80/80, the harness differs from the auditor's and Part A is `undecidable`. |
| Q2 | **PC3a specificity of M3** — alter one realized Hill exponent | **48/48 correctly scored NON-match** (48 = the auditor's alterable set) | AUDIT-OK-8 | M3 is not over-permissive on exponent structure. N4 is likewise a verification. |
| Q3 | **M0 exact reproducibility** via `formula_metrics(teacher_infix, candidate_formula_raw)` | **600/600** system-level and component-level vectors reproduce the stored fields; 32 stored component hits in the sample, 32 recomputed | AUDIT §4 | Gate A→B is achievable *and* non-trivial. This is the R1-mandated positive control. |
| Q4 | **CAS self-equality**, `_sympy_components_equal(truth, truth)` with the M1 short-circuit removed | **28/80**; 52/80 exceed `SYMPY_MAX_NODES = 40` (R01 10/10, R02 10/10, R03 4/10, R04 4/10, R05–R08 0/10) | AUDIT-CRIT-3 | the CAS path answers "does a GRN truth equal itself?" with *no* for 52/80 systems. Reported as an instrument fact (§7.4 PC0-CAS). |
| Q5 | node-cap exceedance on real pairs | **1,652/3,000 = 55.1%** silently return `0.0, None`; by family R01 0.0%, R02 0.0%, R03 33.0%, R04 14.5%, R05 92.9%, R06 100.0%, R07 100.0%, R08 100.0% | AUDIT-CRIT-3 | M2 is structurally incapable of matching R05–R08. This is why M2 is cut. |
| Q6 | **Part A matcher throughput** on 150 real GRN candidates, full M1+M2+M3 cascade | mean **795 ms/candidate**, median 604 ms; by family R01 953, R02 390, R03 1269, R04 399, R05 658, R06 1077, R07 871, R08 604 ms → **10.60 single-core-hours** for 47,987 | AUDIT-MAJ-4 | the measured compute basis (§11). Replaces v1's P11 ODEBench estimate. |
| Q7 | truth-side CAS node totals | min 10, median 25, mean 26.2, max 48 (R07 median 48) | AUDIT-CRIT-3 | a combined cap ≥ 200 would be needed to cover the observed range |
| Q8 | prefix round-trip separator convention | raw equality 20/80 (1-D only); **80/80** under `\|` → `,\|,` | AUDIT-MAJ-7 | Part C's audit must normalize or it self-aborts |
| Q9 | hardware, measured | GPU 0: 8,192 MiB total, 629 MiB used, 7,154 MiB free, 49 °C; disk 117 G free; RAM 60 G total / 52 G available | AUDIT-MIN-6 | Gate 0 item 6 is satisfiable |
| Q10 | `phase3/cells/` contents | exactly **960** files, all `*_validation_*`, zero containing `test`; `all_candidates.json` split values `{validation: 47987}` | AUDIT-OK-3 | the Part A glob cannot reach a seal |
| Q11 | statistical constants | Wilson at n = 80: k=0 [0, 0.0458], k=1 [0.0022, 0.0675], k=2 [0.0069, 0.0866], k=3 [0.0128, 0.1045], k=4 [0.0196, 0.1216], k=8 [0.0515, 0.1851]; one-sided 95% at 0/80 = 0.0327; rule of three 0.0375; smallest n tolerating 1 hit under a 0.05 bound = 110, 2 hits = 142; family-clustered 0/8 = [0, 0.3244]; critical ICC = **0.011** | STAT §1.1, §1.2, §3 | the corrected ladder (§9.3) |

### 0.4 The one quantity deliberately **not** looked at before this freeze

> **The component-type stratification of GPU_RUN5's 107 published M0 component matches has NOT been
> computed, inspected, or estimated by anyone at the time of this freeze.**

STAT-C1 identifies it as the single remaining unobserved quantity in Part A and the decisive one.
This document therefore freezes the stratum definitions (§7.2), the primary endpoint built on them
(§7.1), and the **predicted values** (§7.3) *first*. Only after this file is committed may the
stratification census be computed. Looking first would convert the last unseen quantity in Part A
into disclosed prior information and force a second demotion.

Every artifact carrying a Part A endpoint must carry the field
`prior_information_disclosed` naming §0.1–§0.3 of this file, and the Stage-11 report must
reproduce §0 verbatim in its "Prior evidence" section.

---

## 1. Frozen primary hypothesis

**H-C0001-P (primary, confirmatory).**

> **E0 does not explain the Hill-component generation failure.** Among the
> **Hill / variable-denominator** truth components of the 80 GRN validation systems, a
> canonicalizing constant-collapsing matcher (**M3**) recovers **no in-beam structural matches that
> GPU_RUN5's frozen string matcher (M0) scored as misses**, at the magnitude E0 requires. The
> preregistered effect size E0 requires is **0.0525** — the component-level in-beam rate the frozen
> matcher already achieves corpus-wide (P0b). Predicted value of the primary endpoint: **0**.

This is a **null-shaped primary**, so §9 specifies a mandatory control battery and a
null-credibility ladder without which the null is uninterpretable. Its inferential content is
**powered falsification of a stated effect size**, not an equivalence claim: at the realized
stratum size the design is powered to see the effect E0 predicts (§7.3), and the reported result
of a zero observation is a bound plus that power statement — never "the rate is zero" (§9.5).

**Falsifier.** More than `ceil(0.02 · H)` Hill components showing a matcher-attributable gain
(where `H` = the frozen Hill-stratum size, §7.2) refutes H-C0001-P, means E0 operates at the
component resolution that matters, requires revision of GPU_RUN5's component-level interpretation,
and routes through the replication gate (§15). **Unsupported ≠ refuted**: 1 to `ceil(0.02 · H)`
gains leaves H-C0001-P `unsupported` without refuting it (§9.3).

### 1.1 The four competing explanations, with corrected status

| id | explanation | status entering v2 | decided by |
|---|---|---|---|
| **E0** | measurement/evaluator artifact — the beam contains algebraically equivalent structure that the exponent-aware **string** matcher scores as a miss | **LIVE, with no component-level empirical support.** v1 recorded "partially confirmed at component level (P6)"; that support is **retracted** (`RETRACT`). What is known is that M0 itself already finds 107/2040 component matches and 0/960 system matches. Nobody has run a canonicalizing matcher on this corpus. | **Part A** |
| **E1** | raw expressibility | **REFUTED** (P1). Not re-tested. | cited only |
| **E1'** | generator-support exclusion — the truth's minimal form exceeds `max_unary_ops_per_dim = 3` | **LIVE** (P5, P6) | **Part B** |
| **E2** | prior mass / model error — the truth is in support but near-zero probability under the decoder given the trajectory | LIVE | **Part C** |
| **E3** | search error — the truth has non-negligible probability but beam-50 sampling at T = 0.1 never reaches it | LIVE | **Part C** |

E0, E1', E2 and E3 are **not mutually exclusive** and may hold on different subsets. The design
reports a **partition of the systems**, never a single winner (§10.3). No single-number "the cause
is X" claim is permitted.

### 1.2 Explicitly out of scope

- No beam-size or temperature sweep (the literature answers it; restating it is a known-answer
  experiment).
- No novelty claim for teacher-forced GT scoring: precedented by Stahlberg & Byrne, EMNLP-IJCNLP
  2019, pp. 3356–3362, **DOI 10.18653/v1/D19-1331** (https://aclanthology.org/D19-1331/). The cycle
  report must cite it and must not claim the instrument as novel.
- No biological-causality language. Targets are synthetic Hill-type systems (rule 01 item 7).
- No equation-discovery claim from R²/NMSE (rule 03). Trajectory fit is a covariate only.
- No layer-importance claim (rule 04, §16). No representation-geometry, gradient, ablation,
  IOLE or selective-fine-tuning estimand is measured.
- No M2 / CAS-with-constants endpoint (§18).
- No ODEBench denominator-arity classification (v1 Part D, cut).

---

## 2. Statistical unit, splits, firewall

### 2.1 Units and the analysis hierarchy

Three nested levels, kept distinct throughout:

| level | n | role |
|---|---|---|
| **truth component** | **170** (20 dim-1 × 1 + 30 dim-2 × 2 + 30 dim-3 × 3) | the **analysis element of the primary endpoint** |
| **parameterized system** | **80** (10 per family) | the **resampling cluster**, and the unit of the demoted system-level secondary |
| **family** | **8** (R01–R08) | the **second-level resampling cluster**; perfectly confounded with dimension (P8) |

**Cells are never a unit.** Each system has 12 cells = `noise_sigma ∈ {0.0, 0.05}` ×
`subsample_rho ∈ {0.0, 0.5}` × `bundle_index ∈ {0,1,2}`, but the true structure is (P11): **one**
initial condition and **one** source trajectory per system, **10** distinct conditioning payloads
across the 12 cells, and 12 distinct decode seeds, with the three clean cells byte-identical across
bundles in 80/80 systems. Cells within a system share a ground truth *and* largely share their
conditioning; treating them as independent would inflate n by up to 12×.

**Aggregation order (frozen, non-negotiable): within-component over cells first, then across
components, with clustering by system and family.**

- Component-level binary endpoints: per (cell, candidate, component) indicator → `ANY` over the
  candidates in a cell → `ANY` over the component's 12 cells → the component-level indicator →
  aggregate across components with system- and family-clustered intervals.
- The `ANY` reduction is the **generation-coverage** estimand (rule 03) and is deliberately
  **anti-conservative for a null-shaped claim** (up to 12× inflation of the hit probability under
  independence), which is the adversarially correct direction. Two consequences are frozen:
  (i) an `ANY`-over-12 rate is **not comparable** to GPU_RUN5's per-cell rate except at exactly
  zero, and no artifact may present them as the same quantity improved; (ii) if any `ANY` rate is
  non-zero, the union-of-12 structure must be reported beside it.
- Continuous endpoints: per-cell value → per-system mean over usable cells → across-system interval.

**Frozen scope sentence, required on every rate in every artifact:** *"conditional on the single
initial condition per system stored in GPU_RUN5 phase 3, and on the 10 distinct conditioning
payloads its 12 cells realize."* GPU_RUN5's own P6 result (multi-IC selection, mean clustered
ΔNRMSE −0.20278, paired CI [−0.32323, −0.08233]) establishes that IC materially affects outcomes on
this corpus, so the restriction is not innocuous.

### 2.2 Target population (STAT-C2)

Frozen, stated explicitly because v1 never did:

> The estimand's population is **Hill-type GRN truth components emitted by the R01–R08 generator
> under the frozen `configs/gpu_run5/base.yaml` settings**, of which the 170 validation components
> in 80 systems in 8 families are a realized sample. This is the **superpopulation** reading.

Because family is perfectly confounded with dimension and structure is a family-template property,
the intra-cluster correlation cannot be assumed zero. §9.2 therefore freezes a two-interval
reporting rule and the ICC conditional. Under the alternative **finite-population** reading ("these
170 components"), an observed 0 is exactly 0, no interval is licensed, and no bound on any wider
rate may be claimed; that reading is recorded here and rejected as the estimand, not left implicit.

### 2.3 Splits

| role | artifact | n | use |
|---|---|---|---|
| **train / calibration** | `phase2/train.json` | 240 systems | Part B calibration, rewrite-set development, threshold sanity. **Never contributes to any endpoint.** |
| **validation / measurement** | `phase2/validation.json` (SHA256 `f4644d1d4c30f8a3d6f0cafc8f321fb2c07e72979d8e4c42d28862376abb8f64`) | 80 systems, 170 components | all C0001 endpoints |
| **validation / measurement** | `phase3/all_candidates.json` (47,987) + `phase3/cells/*_validation_*.json` (960, verified count) | 960 cells | Part A re-scoring; Part C candidate distribution and per-cell input payload |
| **replication corpus** | `results/runs/gpu_run4_phase0_01/phase2/all_candidates.json` | 12,632 candidates, 63 ODEBench systems | §15 replication only |
| **model** | `assets/odeformer/weights/odeformer.pt`, SHA256 `56754040be5aa92ed4767fc43ee2008faa293f87c12b643e66c7df3e1623a5e8`, 464,822,385 B (verified) | 1 checkpoint | Part C forward passes only |
| **final test** | all three `sealed_*` artifacts | — | **NOT ACCESSED** (§2.4) |

All 47,987 stored candidates are `split == "validation"` (P9), so there is **no train candidate
set**: Part A's matcher cannot be timing-calibrated or threshold-tuned on train candidates. v1
calibrated on ODEBench and was 6.2× wrong (Q6). v2 therefore calibrates on a **preregistered random
sample of validation candidates, timing only** (§11.1), with the frozen constraint that no match
indicator produced during timing calibration may be aggregated, stored, or read.

### 2.4 Test firewall

| artifact | status | C0001 access |
|---|---|---|
| `phase2/sealed_test.json` (SHA256 `881f784b…64ce0`) | **SPENT** (opened 2026-09-01, `open_count: 1`) | **MUST NOT be read at all.** |
| `phase2/sealed_family_holdout_test.json` (SHA256 `fa8fe375…baf91`) | **SPENT** | **MUST NOT be read at all.** |
| `phase4/sealed_official_test.json` (SHA256 `2860d829…f28e070`) | **UNSPENT — the campaign's only clean seal** | **MUST NOT be touched.** |
| ODEBench 63 systems | not sealed; forbidden as adaptation / selection / hyperparameter data | read-only, replication only |

**Enforcement, strengthened (AUDIT-MAJ-2, AUDIT-MAJ-3, rule 02):**

1. **Every input path is an explicit file-level allowlist entry**, frozen here:
   `phase2/train.json`, `phase2/validation.json`, `phase3/all_candidates.json`,
   `phase3/beam_groups.json`, the enumerated 960 `phase3/cells/*_validation_*.json`,
   `phase4/fixed_grn_validation_panel.json`, and (replication only)
   `results/runs/gpu_run4_phase0_01/phase2/all_candidates.json`. No directory path is ever passed
   to any reader or fingerprinter.
2. **`scripts/ops/run_manifest.py --data-path` receives only individual files from that allowlist.
   Passing any GPU_RUN5 or GPU_RUN4 run directory — or any directory containing a `sealed*` file —
   is forbidden.** `tree_sha256` (`run_manifest.py:28`) does `rglob("*")` and byte-reads every file
   it finds; GPU_RUN5's own phase 8 (`scripts/phases/gpu_run5_phase8.py:1171-1176`) treats hashing
   sealed bytes as **the test-open event**. A manifest call on a run root would open the only
   unspent seal and make `sealed_paths_read: []` a false record.
3. **An instrumented opener records every path C0001 opens**, and `sealed_paths_read` is a
   **computed** field, never a hardcoded `[]`. An assertion raises if any resolved path matches
   `sealed*`.
4. `assert len(glob("phase3/cells/*_validation_*.json")) == 960` and
   `assert all("test" not in name)`, so the guarantee is content-checked rather than path-shaped.
5. A **new C0001-specific firewall test** asserts (a) the allowlist contains no `sealed*` path,
   (b) the instrumented opener recorded zero sealed reads, and (c) no manifest call received a
   directory argument. v1's chosen test validated `load_sealed_test`, a 5-line accessor **C0001
   never calls**.
6. Safe repo-level fix, applied before Gate 0: add `pythonpath = .` **and** `GPU_RUN5/tests` to
   `pytest.ini` (`research_state.md` §8 defects 1 and 6). Without `PYTHONPATH=.` six files raise
   `ModuleNotFoundError: No module named 'scripts'`, including `test_gpu_run5_phase8.py`, which
   holds the real firewall-ordering assertions (`:541-544`: `claim_test_open(` must precede
   `load_sealed_test(`).
7. Cheap hardening, applied before Gate 0: add a `sealed*` guard to
   `src/gpu_run5/config.py:56 require_artifact`, the documented bypass of the firewall accessor
   (AUDIT-MIN-5).

**C0001 consumes no seal. There is no final-test access in this cycle.**

### 2.5 What cannot change after final-test access?

C0001 accesses no final test. The analogous irreversible commitment is **the first computation of
any Part A match indicator on the 170 validation components**. Immediately before that moment the
component-strata assignment (§7.2) must already be written and hashed. After that moment the
following are immutable for this cycle, and any change forces a **new cycle ID**, not an amendment:

the primary hypothesis · the primary endpoint, its stratum definitions and its matcher level (M3,
pinned to `symbolic_recovery(...)["skeleton"]`) · the M0 / M1 / M3 cascade definitions, their
representations (infix on both sides) and their timeouts · the three-level unit hierarchy and the
aggregation order · the `ANY` reduction · the clustered-interval estimator, its resample count and
its seed · the outcome ladder and its cutpoints · the null-credibility conditions · the control
battery and its pass thresholds · the `could_not_evaluate` maximum · the Go/No-Go gates · the
supported / unsupported / undecidable criteria · the exclusion and failure policy · the E2/E3
discriminator and its thresholds · seeds · the checkpoint SHA256 · the compute ceiling · the run ID.

### 2.6 The ten separations kept explicit (role contract, rules 03 and 04)

| aspect | C0001 v2 |
|---|---|
| **training** | **NONE.** Zero parameters updated, no optimizer constructed, zero training budget. |
| **validation** | The 80-system / 170-component GPU_RUN5 validation split is the *only* measurement set. Every threshold in this file is fixed before Stage 4; nothing is selected on validation *outcomes*. |
| **final test** | **NOT ACCESSED.** Two seals SPENT, one UNSPENT and untouched (§2.4). |
| **generation** | Measured as **coverage**: `ANY` over the candidates the model actually emitted (rule 03 generation coverage). Candidate generation itself is not re-run; the decode budget is zero. |
| **selection** | Measured **separately** from generation: A2-S5 reports the **oracle** candidate per cell per level against the **selected** candidate under the frozen selection rule (`src/evaluation/gpu_run5_selection.py:11`). Generation failure and selection failure are never merged. |
| **numerical fit** | `reconstruction_r2`, `generalization_r2`, NRMSE and the trajectory metrics are carried as **covariates only** and may be cross-tabulated against match status. **No match, recovery or discovery claim may be made from any of them** (rule 01 item 6, rule 03). |
| **formula recovery** | Reported at four distinct resolutions, never collapsed: exact string (`exact`), canonical prefix exact (M1), constant-collapsed skeleton equivalence (M3), and structural distance (stored `ted_raw`, `ted_skeleton`, `normalized_ted`, `component_normalized_variable_aware_ted`). Variable recovery (precision / recall / F1 / `unnecessary_variables`) is reported separately again. **M3 is a skeleton criterion at collapsed constants and is named as such** (AUDIT-MIN-10). |
| **representation** | **NOT MEASURED.** No CKA, no similarity geometry, no probe. |
| **causal contribution** | **NOT MEASURED.** No ablation, no intervention. A2-S7 states a *consequence* for a future cycle and explicitly notes that in-beam component coverage and `component_exact_loss` under intervention are **different estimands** — the conflation the retraction identified. |
| **adaptation** | **NOT MEASURED.** No IOLE, no single-layer fine-tuning, no selective fine-tuning, no fine-tuning of any kind. |

---

## 3. Model, checkpoint, seeds, budgets

| item | frozen value |
|---|---|
| checkpoint | `assets/odeformer/weights/odeformer.pt`, SHA256 `56754040be5aa92ed4767fc43ee2008faa293f87c12b643e66c7df3e1623a5e8` (verified at audit) |
| architecture of record | released `4 encoder (dim 256) + 12 decoder (dim 512)`, 16 heads, 60,646,773 params — **not** the paper's 4+16 / dim 512 / ~86M |
| **training budget** | **ZERO** |
| **hyperparameter search space** | **EMPTY**. Every threshold in this file is fixed before Stage 4. |
| **new decoding / candidate budget** | **ZERO**. No new beam search, no new sampling. Part A re-scores stored artifacts; Part C is forward-only teacher-forced scoring. |
| decode config of the stored candidates (fixed context, never swept) | `beam_size = 50`, `beam_type = sampling`, `beam_temperature = 0.1`, `max_generated_output_len = 200`, `rescale = True`, `failure_penalty = 10.0` |
| operator constraints of record | `operators_to_use = "sin:1,inv:1,pow2:1,id:3,add:3,mul:1"`; `min/max_unary_ops_per_dim = 0/3`; `min/max_binary_ops_per_dim = 1/5`; `max_unary_depth = 7`; `max_int = 10`; `float_precision = 3`; `max_dimension = 6`. Zero-probability operators per P2. |
| seeds | Part A is **deterministic**: M0/M1/M3 involve no RNG, and with M3 pinned to `["skeleton"]` the non-random hard-coded grid in `_approximately_equivalent` (`equation_metrics.py:72-73`) is not called at all. Part B is deterministic except rewrite verification, `numeric_equivalent(seed = 0)`, frozen at **0**. Part C is deterministic (`model.eval()`, `torch.no_grad()`, `torch.use_deterministic_algorithms(True)` where supported). Cluster bootstrap seed **20260909**, 10,000 resamples. Global seed **20260909**. |
| Part A parallelism | **process-based, ≤ 6 worker processes** (AUDIT-MAJ-5). Thread parallelism is **forbidden**: `_time_limit` (`equation_metrics.py:38-45`) silently yields unguarded off the main thread, removing every SymPy wall-clock guard. A Stage-6 smoke assertion must demonstrate `_time_limit` firing **inside a worker**. |
| SymPy guards | `SYMPY_OP_TIMEOUT_SEC = 10.0` (`equation_metrics.py:56 _timed_simplify`, `:62 _timed_equals`). Unchanged by C0001. `LANSR_SYMPY_MAX_NODES` and `SYMPY_EQUIV_TIMEOUT_SEC` (`ted.py:14-15`) apply only to `_sympy_components_equal`, which no v2 **endpoint** calls (§18); the §7.4 PC0-CAS diagnostic runs it with the cap raised to **200** and that raise is recorded as an instrument-diagnostic parameter, not an endpoint parameter. |
| dtype / device | fp32 throughout; Part C on `cuda:0`; Parts A and B CPU-only |
| environment | PyTorch 2.5.1+cu124, sympy 1.13.1, numpy 2.2.6, zss 1.2.0, Python 3.10.20, env `lansr310` — identical to the versions recorded in the source run's `phase3/manifest.json`, which is why re-scoring is reproducible |

---

## 4. Comparators and baseline conditions

Nothing is trained, so there is no trained baseline. The comparators are **frozen published
measurements**, corrected:

| comparator | value of record | role |
|---|---|---|
| **C-M0** frozen string matcher, system level | `true_exponent_aware_skeleton_in_beam` = **0/960 cells**, 0/120 per family (P0a) | the published claim whose interpretation is under test. Note the stored value is a **mean over 960 cells** (`gpu_run5_phase3.py:442`), not over 80 systems; the reductions coincide only because the value is exactly 0 (AUDIT-MIN-11). |
| **C-M0c** frozen string matcher, component level | **107/2040 = 0.0525** (P0b), by family R01 0, R02 0, R03 0, R04 56, R05 0, R06 0, R07 17, R08 34 | **CORRECTED from v1's `0/2040`** (AUDIT-CRIT-1). The reference level the primary's *gain* is measured against, and the effect size E0 must beat. |
| **C-M0f** stored per-candidate fields | `exponent_aware_skeleton_exact` and `component_exponent_aware_skeleton_exact` for all **47,987** candidates / **101,963** component comparisons, including all **2,235** component-level ones (P0c) | the R1-mandated positive control. Gate A→B requires exact reproduction (§10.1). |
| **C-ODEB** ODEBench string matcher | 4/252 = 1.59% [0.0062, 0.0401] | non-zero corpus-level positive control for the §15 replication |
| **C-BUDGET** the generator's own unary budget | `max_unary_ops_per_dim = 3` | Part B reference |
| **C-SAMPLED** the model's own 50 sampled candidates per cell | measured in Part C | Part C reference — the model is compared against **itself**, which is the budget-matched comparison, with the T = 0.1 upper-tail caveat frozen in §8.3 |
| **C-SELECTED** the candidate the frozen selection rule actually returned per cell | measured in Part C | the second element of the paired Stahlberg–Byrne discriminator (§8.3) |

**Dropped comparator.** v1's `C-NEG` (crude `neg`-folded matcher, "0/960 system, 107/2040
component, a lower bound on what a proper canonicalizer should find") is **deleted**. Its
component value *was* C-M0c, re-derived; per R1 that is a positive control, not a comparator, and
presenting it as an independent lower bound double-counted one measurement.

---

## 5. Fair comparison budget

Every comparison is budget-matched **by construction**, and the two places where matching holds at
the code level but not at the estimand level are declared rather than asserted away.

1. **Part A** applies M0, M1 and M3 to the **identical** 47,987 stored candidates, the identical
   170 truths, the identical 960 cells, in the **same pass, in one process, from the same parsed
   inputs**. No arm sees different data, more candidates, more cells or more compute. The only
   thing that varies is the equivalence criterion, so any difference is attributable to the
   instrument alone. **Both sides of every comparison are fed the infix representation** (R1,
   AUDIT-CRIT-2): `formula_metrics(teacher_infix, candidate_formula_raw)` for M0 and the same infix
   pair for M1/M3. `phase3/cells/*.json:true_structure` is **prefix-derived** and must never be
   compared against an infix-derived skeleton — that mixing produced the retracted finding.
2. **Timeout and failure budgets are identical** across arms, truths, candidates and controls. No
   arm receives a longer wall clock, a larger node budget, or a retry the others do not get.
3. **Part B** compares two encodings (multiplicative vs affine-decomposed) of the **same** truth
   against the **same** fixed budget of 3, with an identical 200-rewrite enumeration cap on both.
4. **Part C** scores the ground truth and all candidates for a cell through the **identical**
   forward path: one `embedder` + `encoder("fwd", causal=False)` pass whose `src_enc` is cached and
   reused, then the same `decoder("fwd") → decoder("predict", get_scores=True)` call, in the same
   process, in fp32, on the same device. Both GT encodings and all candidates go through the same
   new scoring function. §8.2 preregisters the audit that proves it.
5. **Declared asymmetry 1 — conditioning identity (STAT-C3).** v1 rested the Part C fairness
   guarantee on `input_trajectory_checksum`. That field is the **pre-corruption source** checksum:
   80 distinct values over 80 systems, constant across all 12 cells of every system, while the 12
   cells carry 10 distinct payloads (P11). It cannot detect a cell-level mixup — scoring every cell
   against the wrong corruption, the wrong bundle or the wrong noise level would pass it silently.
   v2 replaces it (§8.2 step 1) and relabels it a **system-identity** check.
6. **Declared asymmetry 2 — encoding orbit (STAT-M9).** Each candidate is scored as the **one**
   token sequence the model actually emitted, for which the single-sequence log-prob is exactly the
   right quantity. The GT is scored as **one of many equivalent encodings**, so `logP(one encoding)`
   is a **lower bound** on the probability the model assigns to the truth as a function. Magnitude,
   from the truth token census (P7): 4920/960 = 5.125 `mul` + 4080/960 = 4.250 `add` = **9.375
   commutable binary nodes per system truth** → ~26 equivalent orderings at 50% swappability
   (**3.25 nats** understated), ~131 at 75% (**4.87 nats**), ~664 at 100% (**6.50 nats**). This is a
   **preregistered directional bias toward E2 (model error)**, of magnitude 14–28% of a 0.5
   nats/token decision scale at Lg = 47. It is disclosed, bounded, and partially mitigated by the
   §8.3 commutation-orbit report; it is **not** claimed to be absent. v1's §5 item 3 sentence
   ("There is no 'GT gets a special path' asymmetry") is **withdrawn**: it is true of the forward
   pass and false of the estimand.

---

## 6. Experiment structure and ordering

**Three parts** (v1's Part D is cut), ordered so the cheapest claim-invalidating check runs first.

| part | question | instrument | compute | gate |
|---|---|---|---|---|
| **Part A** | **E0** — does canonicalization recover Hill-component matches M0 missed? | M0 / M1 / M3 cascade over the stored candidates, component-type-stratified | **CPU only** | Gate 0 → A |
| **Part B** | **E1'** — is the truth outside the generator's sampling support? | analytic unary-budget census over stored truths | **CPU only** | Gate A → B |
| **Part C** | **E2 vs E3** — model error or search error? | teacher-forced summed log-probability, paired against the candidate search actually returned | **GPU, forward passes only** | Gate B → C |

Parts A and B touch no GPU. Part C is the only GPU work in the cycle.

---

## 7. Part A — evaluator adequacy at component resolution (CPU only)

### 7.1 PRIMARY ENDPOINT (the one and only)

> **`hill_component_matcher_attributable_gain_rate`**
>
> Let `H` be the frozen set of **Hill / variable-denominator** truth components (§7.2). For a truth
> component `(s, i)` define, over the **usable** candidates of the **12 cells** of system `s`:
>
> - `m0_any(s, i) = 1` iff at least one candidate in at least one cell is an **M0** component match
>   at index `i`;
> - `m3_any(s, i) = 1` iff at least one candidate in at least one cell is an **M3** component match
>   at index `i`;
> - **`gain(s, i) = 1[ m3_any(s, i) = 1 AND m0_any(s, i) = 0 ]`.**
>
> **Primary = ( Σ_{(s,i) ∈ H} gain(s, i) ) / |H|.**
>
> Reported with **three** intervals, all frozen: (a) plain **Wilson score** 95% over `|H|`
> components, labeled `assumes_component_independence: true`; (b) a **two-stage cluster bootstrap**
> 95% percentile interval (families resampled with replacement, then systems within family with
> replacement, 10,000 resamples, seed 20260909) — **this is the interval of record**; (c) the
> **8-cluster Wilson** interval on the family-level indicator as an explicit bounding case.

**Why this endpoint and not v1's.** E0 asserts that the frozen string matcher *misses structurally
correct candidates*. The disclosed mechanism is a **per-component** encoding asymmetry (P4). v1's
primary reduced by **conjunction over all components of a system**, i.e. it estimated the *d-th
power* of the phenomenon E0 describes, in a corpus where dimension is perfectly confounded with
family and where the only stratum in which the conjunction can realistically fire (dim-1, R01/R02)
is known to be empty at component level (P0d). Its outcome carried **0.286 bits** (STAT-C1). This
endpoint is at the resolution E0 operates at, restricted to the components whose failure is the
scientific question, and it is a **difference against a verified non-zero reference** (C-M0c =
107/2040) rather than a comparison against zero.

**Why the *gain* and not the level.** The component-level M3 *level* is bounded below by M0's
published 107/2040 under monotonicity, so a positive level is guaranteed and uninformative. The
**gain** is exactly the retracted claim, now tested properly: *are there components whose structure
is in the beam and which the frozen matcher scored as a miss?* Nobody has measured it.

**Naming.** M3 collapses every numeric constant to `c` (`equation_metrics.py:158-164`), so an M3
match is **skeleton equivalence at collapsed constants**, not semantic equivalence. The endpoint
name says `skeleton`-level things and no artifact may call it semantic equivalence (AUDIT-MIN-10,
rule 03).

### 7.2 Component-type strata (frozen definition; assignment computed before any matching)

Assignment is a **truth-side** property and carries no outcome information. It is computed from
`phase2/validation.json:teacher_components_infix` through
`src/gpu_run4/formulas.py formula_views(..., as_prefix=False)["components"]` — the **infix** path,
so that stratum assignment and matcher input come from the same derivation path (R1).

| stratum | definition (decidable on the parsed tree) |
|---|---|
| **H — Hill / variable-denominator** | the component's parsed tree contains **at least one `inv` node whose argument subtree contains at least one variable leaf `x_j`** |
| **L — no variable denominator** | every other component: linear-decay-only, constant-affine, and any component whose only `inv` arguments are constant subtrees |

Frozen procedural requirements, in this order:

1. The strata assignment for all 170 components is written to `R/phase1/component_strata.json`,
   with `|H|`, `|L|`, the per-family and per-dimension breakdown, and the SHA256 of the file.
2. The realized-`H` **Wilson table, ladder cutpoint and operating-characteristic table** are
   computed from the frozen formulas in §9.3 and written to `R/phase1/partA_ladder_realized.json`.
   Both depend on `|H|` alone.
3. **Only then** may any match indicator be computed.

Any implementation that computes a match indicator before steps 1 and 2 have been written and
hashed has violated the preregistration, and Part A is `undecidable`.

**Frozen fallbacks, so no post-hoc choice exists.** If `|H| < 40` **or** `|L| < 15`, the stratified
primary is `not_measurable` and the primary falls back — automatically, with no discretion — to the
**unstratified** component-level gain rate over all 170 components, with the stratified values
reported descriptively. If `40 ≤ |H| < 100`, the primary stands but its null-direction verdict is
labeled `underpowered_bound_only` whenever the realized power to detect a 0.0525 gain rate falls
below 0.90, and in that state it **may not be cited as refuting E0**.

### 7.3 Frozen predictions (recorded before the stratification of the 107 was looked at)

Required by the STAT-C1 integrity constraint. These are predictions, not results.

| quantity | frozen prediction | basis |
|---|---|---|
| `|H|` | **130–145** of 170 | P7: `inv` 1680/960 = 1.75 nodes per system against 170/80 = 2.125 components per system, i.e. ≈ 0.82 `inv`-bearing components per component. **An inference from disclosed aggregate token counts, not a measurement.** |
| `|L|` | **25–40** of 170 | same |
| **PRIMARY — Hill-stratum gain rate** | **0 / `|H|`** | E0 has no component-level empirical support after `RETRACT`; M0 already finds the 107 |
| L-stratum gain rate | **> 0** | real candidates spell decay as a signed constant (P4), which M0 cannot match and M3 can (Q1: PC2a = 80/80). Linear-decay components are where that rewrite is the whole component. |
| type stratification of GPU_RUN5's 107 M0 matches | **majority in stratum L** — at least 54 of 107 | if the 107 were mostly Hill components, GPU_RUN5's own published data would already show Hill structure reaching the beam, contradicting `research_state.md` §2's record of zero exact Hill/variable-denominator components in every GPU_RUN5 final condition |
| dimension distribution of the 107 | **0 in dim-1** | not a prediction: deduced from published values (P0d) |
| monotonicity violations (`m0_any = 1, m3_any = 0`) | **≤ 0.1%** of scored triples | M3 is strictly more permissive in intent; `to_skeleton` constant-collapsing can legitimately break inclusion in rare cases |

**Powered-falsification statement (this is the primary's inferential content, not an equivalence
claim).** Under independence across components, the probability of observing **≥ 1** gain is
`1 − (1 − p)^{|H|}`:

| true per-component gain rate `p` | `|H|` = 100 | `|H|` = 140 |
|---|---|---|
| **0.0525** (the effect size E0 requires, = C-M0c) | **0.9955** | **0.9995** |
| 0.02 | 0.867 | 0.941 |
| 0.01 | 0.634 | 0.755 |

So a zero observation is informative **against E0 at its own stated magnitude** and progressively
uninformative below ≈ 0.01. The exact value at the realized `|H|` must be computed from this frozen
formula and written to `partA_ladder_realized.json` before counting (§7.2 step 2). Clustering
reduces effective power below these independence figures; the cluster bootstrap must report the
family-clustered power at the realized `|H|` alongside them, and the *smaller* of the two is the
number the report quotes.

### 7.4 The matcher cascade (frozen definitions; M2 removed)

Applied per (cell, candidate, component), index-aligned by variable: truth component *i* is
compared **only** to candidate component *i*; a component-count mismatch is an automatic non-match
with `failure_reason = "ComponentCountMismatch"`.

| level | definition | implementation of record |
|---|---|---|
| **M0** | frozen exponent-aware **string** skeleton equality | `src/gpu_run5/evaluation.py:39 formula_metrics(teacher_infix, candidate_formula_raw)`, fields `exponent_aware_skeleton_exact` (system, `:84-87`, which requires `component_count_match` **and** whole-string equality) and `component_exponent_aware_skeleton_exact` (component, `:47-53`, index-aligned split on `" \| "`). **Infix on both sides.** |
| **M1** | canonical prefix exact | `src/gpu_run4/formulas.py:479 compare_formulas(..., skip_cas=True)["canonical_exact"]` |
| **M3** | **constant-collapsed skeleton equivalence — the primary level** | **exactly** `src/evaluation/equation_metrics.py:169 symbolic_recovery(T_i_infix, C_i_infix)["skeleton"]`, and **no other key**. Internally: `to_skeleton` (`:153`) maps constants to `c` and returns `_timed_simplify(sympify(...))`, then `:189 _timed_simplify(sk_true − sk_pred) == 0` or `:190 _timed_equals(sk_true, sk_pred)`. |

**M3 pinning (AUDIT-MAJ-1).** v1 wrote "`symbolic_recovery(...)["skeleton"]`, plus
`_approximately_equivalent(rtol=1e-6)`, plus `to_skeleton`", which is not a composition rule and
admitted three readings with different rates — leaving the cycle's primary endpoint undetermined.
v2 pins M3 to the single key `["skeleton"]`. Consequences, recorded: `_approximately_equivalent` is
**not called** (it is reachable only through `["equiv"]` at `:203`); the hidden fallback
`except Exception: equiv = skeleton` at `:205` is **not reachable**; `recovery = max(exact,
skeleton, equiv)` is **not used**.

**M2 is removed from the design.** See §18 for the reasoning, the declined amendment and its
consequences. `_sympy_components_equal` is called nowhere in Part A's endpoint path.

**Roll-up (frozen).**
`component_match(i, level)` → `cell_component_hit(i, level) = OR over usable candidates` →
`component_any(i, level) = OR over the 12 cells` → primary as §7.1; and, for the demoted
system-level secondary, `system_match(candidate, level) = component_count_match AND all_i
component_match(i, level)` → `cell_hit = OR over candidates` → `system_hit_ANY = OR over 12 cells`.

### 7.5 Failure taxonomy, monotonicity, and the reported failure endpoint (AUDIT-CRIT-3, AUDIT-MAJ-6)

v1 inherited guards whose design intent is the opposite of what a null-shaped claim needs. The code
comment at `equation_metrics.py:18-20` says a timeout is treated as "could not prove equivalence
(the conservative outcome that never inflates a recovery score)". That is conservative for a
*recovery* claim and **anti-conservative for C0001's null**, where an unprovable comparison counted
as a miss pushes the primary toward `supported`. Frozen requirements:

1. **Every non-match carries an explicit `failure_reason`, and `proved_different` is separated from
   `could_not_evaluate` at every level.** No path may return an unlabelled non-match. The specific
   surfaces that must be labeled, each verified present in the code:
   - `to_skeleton` returning `None` (`equation_metrics.py:166`) → `SkeletonParseFailure`;
   - `except Exception: skeleton = 0.0` (`:192-193`) → `SkeletonEvaluationFailure`;
   - a `_timed_simplify` / `_timed_equals` wall-clock trip → `SymbolicEquivalenceTimeout`;
   - component-count mismatch → `ComponentCountMismatch`;
   - a parse failure on either side → `ParseError`;
   - and, for the §7.4 PC0-CAS diagnostic only, `nodes > SYMPY_MAX_NODES`
     (`src/gpu_run4/formulas.py:434`, which today returns `0.0, None` with **no** reason) →
     `SymbolicNodeCapExceeded`.
2. **`could_not_evaluate_rate` is a reported endpoint** (A2-S6), not a diagnostic footnote:
   `(SkeletonParseFailure + SkeletonEvaluationFailure + SymbolicEquivalenceTimeout + ParseError) /`
   all scored (cell, candidate, component) triples.
   **Frozen maximum: 2.0%.** Above 2.0%, the Part A primary is **`undecidable` (instrument
   failure)** and no null may be reported. Between 0% and 2.0% the primary is reported **together
   with** the two-sided sensitivity analysis of item 3.
3. **Two-sided sensitivity analysis, mandatory whenever `could_not_evaluate_rate > 0`**: recompute
   the primary counting every could-not-evaluate triple as a **non-match** (the primary of record,
   the direction that does not inflate the gain) **and** as a **match** (the adversarial direction).
   If the two land on different ladder rungs, the verdict is **`undecidable`**.
4. **Monotonicity audit.** Expected `M0 ⊆ M1 ⊆ M3` as sets of matching triples. Every violation is
   logged with both expressions and both derivation paths. Frozen policy: ≤ 0.1% → recorded as a
   known constant-collapsing edge case, reported, non-blocking; (0.1%, 1%] → **MAJOR**, must be
   diagnosed before the primary is reported; > 1% → **CRITICAL**, cascade defective, Part A
   `undecidable`. The monotonicity check is **the precondition for the primary's multiplicity
   argument** (§9.4), not merely an internal audit — v1 did not say so (STAT-M5).
   Additionally, the component-level count of `m0_any = 1, m3_any = 0` is reported explicitly: it
   is the direct sibling of the primary and the exact check that would have caught the retracted
   representation bug.

### 7.6 The reproduction gate that replaces v1's defect trigger

v1's instrument safeguard was `A-S3 ≥ 0.0525`, an `ANY`-over-12-cells rate compared against a
cell-level rate whose admissible range for the same 107 matches is **[0.052, 0.629]** (STAT-M1) —
a trigger that could not fire even if the cascade were twelve times worse per cell. It also rested
on a retracted reading. It is **deleted** and replaced by an exact-reproduction requirement (R1,
AUDIT-CRIT-1, AUDIT §4):

> **The M0 arm, computed as `formula_metrics(teacher_infix, candidate_formula_raw)`, must reproduce
> the stored `exponent_aware_skeleton_exact` and `component_exponent_aware_skeleton_exact` fields
> for **all 47,987 candidates** and **all 101,963 component comparisons** exactly — including all
> **2,235** stored component-level ones — and must reproduce the reduced values
> **0/960 system-level** and **107/2040 component-level**.**

This is non-vacuous in a way the aggregate check was not: every stored `exponent_aware_skeleton_exact`,
`canonical_exact` and `skeleton_exact` value is 0.0 (P0c), so "reproduces 0.0" is satisfied by any
implementation that never returns a match, including a completely broken one. The 2,235 stored
component ones are the only non-degenerate signal in the stored data, and the auditor demonstrated
600/600 reproduction on a random sample (Q3), so the requirement is achievable and diagnostic.

**Failure protocol.** Any mismatch is a **harness defect, not a finding**: halt, store the
disagreeing records at `R/phase1/m0_reproduction_failures.jsonl` (explicit `R/` prefix, AUDIT-MIN-3),
diagnose, fix only the defect, re-run Part A **whole**, record a `DEVIATION-nn`. If it cannot be
isolated within the ceiling, the **entire cycle is `undecidable`** — the comparator of record could
not be reproduced. The first hypothesis to check on failure is a representation mismatch between
prefix- and infix-derived strings (R1).

### 7.7 Mandatory control battery

Synthetic candidates are injected per system, tagged `positive_control_tag`, stored in a separate
artifact, and **never** enter any endpoint.

| control | construction | measures | pass threshold |
|---|---|---|---|
| **PC0** identity through M3's own path | call `symbolic_recovery(T_i, T_i)["skeleton"]` **directly**, bypassing `compare_formulas` entirely | sensitivity of the exact code path the primary uses | **170/170 components and 80/80 systems.** Any failure ⇒ matcher broken ⇒ **abort Part A** |
| **PC0-CAS** CAS self-equality (instrument diagnostic, **not** an endpoint) | `_sympy_components_equal(truth, truth)` directly, M1 short-circuit bypassed, `LANSR_SYMPY_MAX_NODES` raised to **200** | whether the CAS path can answer "does a GRN truth equal itself?" | **reported, not gating.** Known value at cap 40: **28/80** with 52/80 cap-exceeded (Q4). Expected at cap 200: 80/80. Reported as a `descriptive` instrument fact; **may not invalidate any GPU_RUN5 result**; cost bounded at 80 calls × 10 s = 0.22 core-h |
| **PC1** identity through `compare_formulas` | inject the truth as its own candidate | reproduces v1's PC1 **as a demonstration that it is vacuous** | reported alongside PC0. `formulas.py:493` short-circuits `symbolic = 1.0` when `canonical_exact == 1.0`, which is why v1's PC1 gave M2 80/80 while the CAS path alone gives 28/80 (AUDIT-CRIT-4). PC1 is retained only to document the artifact; **it gates nothing.** |
| **PC2a** `neg` asymmetry | rewrite every `-1 * k * x_i` to `(-k) * x_i` — the exact artifact P4 identifies, in the model's own spelling | sensitivity of M3 | **80/80** for M3. **This value is already known (Q1)**, so this is a *verification*: any result other than 80/80 means the C0001 harness differs from the audited one ⇒ Part A `undecidable`. |
| **PC2b** affine decomposition | `a * A^n * inv(K + A^n)` → `a − a*K*inv(K + A^n)`, SymPy-verified | sensitivity of M3 | ≥ 76/80 |
| **PC2c** `add` commutation | permute every `add` operand pair | sensitivity of M1, M3 | ≥ 76/80 |
| **PC2d** `mul` commutation | permute every `mul` operand pair | sensitivity of M1, M3 | ≥ 76/80 |
| **PC3a** wrong exponent (**negative** control) | truth with one realized Hill exponent altered (4→2 or 2→1) | **specificity** of M3 | **≥ 95% of the eligible set scored NON-match.** Eligible set = systems with an alterable realized exponent, enumerated and reported; **48** under the auditor's rewrite, of 24/80 carrying nested `pow` (P5, AUDIT-MIN-9). Known value: **48/48** (Q2) ⇒ verification. |
| **PC3b** permuted variable (**negative** control) | truth with two variable indices swapped in one component (`dimension ≥ 2` only, n = 60) | specificity of M3 | ≥ 58/60 NON-match |

**Frozen check on the controls themselves (AUDIT-CRIT-4).** For each of PC2a–PC2d it must be
verified and reported whether the rewrite canonicalizes back to a form that M1 already matches. A
control whose rewrite is absorbed by `canonical_exact` tests nothing about M3's own path; any such
control is reported as `short_circuited` and its threshold is evaluated on the non-short-circuited
subset, with the subset size stated.

PC3a/PC3b were not in the original brief; both reviewers endorsed them. A null-shaped primary is
destroyed by an over-permissive matcher exactly as easily as by an under-permissive one, and only a
specificity control detects that.

### 7.8 Secondary endpoints (Part A) — all `descriptive`, none confirmatory

No Part A secondary may carry a confirmatory claim, receive a hypothesis test, or invalidate a
GPU_RUN5 result (§9.4).

| id | endpoint | inference | note |
|---|---|---|---|
| A2-S1 | **L-stratum** matcher-attributable gain rate, and the **H − L difference** | descriptive; cluster bootstrap interval | the internal contrast: where the gain lives, if anywhere. Predicted `L > 0` (§7.3). |
| A2-S2 | component-level **M3 level** (not gain), overall and by stratum | descriptive; cluster bootstrap | bounded below by C-M0c under monotonicity, hence uninformative alone; reported so the gain has a denominator context |
| A2-S3 | `system_skeleton_equivalence_in_beam_rate_M3_ANY` over 80 systems — **v1's demoted primary** | descriptive; Wilson (`assumes_family_icc_zero: true`) **and** family-clustered | **carries no confirmatory claim.** Reported with STAT-C1's power analysis and the §9.2 clustering caveat. Not comparable to GPU_RUN5's per-cell 0/960 except at exactly zero. |
| A2-S4 | per-system **MEAN** hit fraction over the 12 cells, M3, and per-dimension and per-family stratifications (20/30/30 and 8 × 10) | descriptive | at 0/10 a family Wilson interval is [0, 0.278]; **it cannot establish family homogeneity** (STAT-m7) and must not be read that way |
| A2-S5 | cascade increment table: |M0|, |M1|, |M3| at candidate, component and system level; **oracle** candidate per cell per level vs **selected** candidate under the frozen selection rule (`gpu_run5_selection.py:11`) | descriptive | rule 03: generation coverage vs oracle vs selected, kept distinct |
| A2-S6 | **`could_not_evaluate_rate`** and the full failure taxonomy of §7.5, plus monotonicity-violation rates and the `m0_any=1, m3_any=0` count | **reported endpoint with a frozen maximum of 2.0%** | above 2.0% ⇒ primary `undecidable` |
| A2-S7 | **statement only, not measured**: *if* a Hill-stratum gain exists, *then* a future cycle should re-examine whether GPU_RUN5's causal-intervention analysis discarded usable signal. | none | **Re-grounded (RETRACT).** In-beam component coverage (107/2040, published) and `component_exact_loss` under causal intervention are **different estimands**; v1's A-S8 moved between them illegitimately. C0001 measures neither the intervention nor any layer estimand (rule 04, §16). Routed to `hypothesis_tree.md` as a C0002 candidate. |
| A2-S8 | rule-03 completeness panel: parse validity, NaN/Inf, denominator margin, `near_singularity`, `extrapolation_valid`, `extrapolation_extreme`, `has_division`, `has_tan`, complexity (node/operator counts, length), variable precision/recall/F1, `unnecessary_variables`, stored TED fields, variable mapping | descriptive | preserved per rule 03; TED is **carried, not recomputed** |

### 7.9 Data handling and exclusions

- **Invalid and failed candidates are retained** (rule 01 item 5). A candidate with `valid == false`
  is scored as a non-match with its `failure_reason` preserved and is **never dropped from any
  denominator**. Denominators are *usable candidates present in the cell* — 47/48/49/50 (P10) —
  never a hardcoded 50. The 13 missing candidates are carried as `candidate_return_shortfall`.
- **No exclusion of any kind is permitted from the Part A primary endpoint.**
- **Numerical fit is not recovery** (rule 01 item 6, §2.6).
- Variable mapping preserved from `phase2/validation.json:variable_to_gene`.
- Structural distance carried from the stored `ted_raw`, `ted_skeleton`, `normalized_ted`,
  `component_normalized_variable_aware_ted`.

---

## 8. Part B and Part C

### 8.1 Part B — generator-support accounting (CPU only, deterministic census)

Unchanged from v1 in substance; both reviewers endorsed its construction and its one-sidedness.
Changes: it is removed from every multiplicity family and every endpoint is labeled `descriptive`.

For each of the 320 train + validation truths, per component, from the stored
`teacher_components_prefix`:

- `realized_hill_exponents` — detected as the **nesting depth of `pow2` over a variable-containing
  subtree** (depth 1 → exponent 2, depth 2 → exponent 4). A literal `pow,4` token is **not** how
  exponent 4 is spelled in this corpus (P5); an implementation searching for it is wrong by
  construction, and searching a canonicalized string for a surface token is the exact error R1
  forbids.
- `U_mult` — non-identity unary nodes (`inv, pow2, sin, abs, sqrt, log, exp, pow3`) in the stored
  canonical multiplicative form. Deterministic.
- `U_affine` — minimum non-identity unary count over the frozen rewrite set below.
- `U_min = min(U_mult, U_affine)`; `in_support = (U_min <= 3)`.
- `uses_only_in_support_operators`; `binary_ops_per_dim` vs `max_binary_ops_per_dim = 5`;
  `unary_depth` vs `max_unary_depth = 7` — all three generator constraints checked, not only the
  unary count.

**Frozen rewrite set for `U_affine`** (bottom-up, cap **200** accepted rewrites per component,
deterministic traversal, each rewrite verified by `numeric_equivalent(n_points=32, seed=0)` and
**discarded and logged** as `RewriteVerificationFailure` on failure):
**B-R1** `A^n * inv(K + A^n) → 1 − K * inv(K + A^n)`; **B-R2** fold pure-constant subtrees to a
constant leaf; **B-R3** distribute `mul` over `add` **only when it strictly lowers** the
non-identity unary count; **B-R4** `neg(X) ↔ mul(-1, X)`.

**Preregistered one-sidedness.** `U_affine` is a minimum over a *bounded* rewrite set, hence an
**upper bound** on the true minimal unary count. A component reported `out_of_support` may be in
support under a rewrite outside the set. Part B's claim is therefore explicitly *"out of support
under the preregistered rewrite set"*, never *"out of support"*. **B-R1 does not rescue multi-term
components**: the affine expansion of a product of two Hill terms yields four terms with ≥ 6
unaries, so `U_min` for such components stays > 3. **Manual hand-construction of affine encodings
is forbidden** — it would make the rewrite set investigator-dependent and unreproducible.

| id | endpoint | inference |
|---|---|---|
| B2-S1 | validation **system-level** `out_of_support_rate` (of 80) | descriptive; Wilson with `interval_interpretation` |
| B2-S2 | validation **component-level** `out_of_support_rate` (of 170) | descriptive; Wilson + cluster bootstrap |
| B2-S3 | realized-exponent histogram, train and validation, reconciled against `configs/gpu_run5/base.yaml:28 hill_exponents: [1, 2, 4]` | descriptive |
| B2-S4 | mechanism decomposition: (i) multiplicative Hill-4 single-term (`U_mult = 5`, rescued by B-R1 to 3) vs (ii) **multi-term** components (`U_mult ≥ 6`, **not** rescued) | descriptive |
| B2-S5 | per-family out-of-support rate | descriptive, underpowered |
| B2-S6 | zero-probability-operator usage by truths (expected 0/320) | descriptive; falsifies P2's scope if non-zero |
| B2-S7 | **`in_support` cross-tabulated against Part A's component strata H/L** | descriptive | 

**Frozen wording (endorsed by both reviewers, retained verbatim in intent).** Part B's values are
**deterministic functions of a fixed corpus** — there is no measurement noise. A Wilson interval
here describes sampling variability of the **R01–R08 generator** ("at what rate does this generator
emit out-of-support truths"), not estimation uncertainty. Every artifact reporting B2-S1/B2-S2
carries `interval_interpretation: "generator_sampling_not_measurement_error"`.

**Preregistered possibility that E1' is inapplicable.** If B2-S1 = 0, E1' is refuted for this corpus
and that is itself a reportable result. Calibration (P6: 25.0% of train systems exceed budget) makes
an observed 0 unlikely, so it additionally triggers a train/validation consistency check as a
possible implementation defect.

### 8.2 Part C — model error vs search error (GPU, forward passes only)

Run **only on the in-support subset** from Part B (systems all of whose components have
`U_min ≤ 3`), because running it on out-of-support systems conflates E1' with E2. Expected
`n_in_support ≈ 60` of 80. **If `n_in_support < 30`, Part C is downgraded to `exploratory` for
insufficient power**, reported as such, and cannot support an E2 or E3 attribution.

Per cell, frozen procedure:

1. **Conditioning-identity verification (replaces v1 step 1; STAT-C3).** Load the cell's **input**
   trajectory from `phase3/cells/<cell_id>.json:observations["input"]` and:
   a. compute **`cell_input_payload_sha256`** — SHA256 over the float64 little-endian bytes of the
      exact arrays passed to `_point_bag`, concatenated in the frozen order
      `times ‖ observed_trajectory ‖ initial_condition`, each preceded by its shape as
      little-endian `int64`. This is a digest of **the object actually used**;
   b. assert that `system_id`, `bundle_index`, `noise_sigma` and `subsample_rho` parsed from the
      record **equal** the values encoded in `cell_id`, and that `candidate_set_hash` and
      `cache_identity` match the stored values;
   c. assert that the number of distinct `cell_input_payload_sha256` values within a system is
      **10** (P11) — a system showing 12 or 1 indicates a cell mixup or a stale cache;
   d. retain the `input_trajectory_checksum` comparison but record it as
      `system_identity_checksum_ok`, **explicitly a system-identity check, not a conditioning
      check** (80 distinct values over 80 systems, constant across a system's 12 cells).
   Any failure marks the cell `CellIdentityMismatch` and **excludes it, counted and reported**.
   `EncoderCacheMiss` as v1 defined it is deleted: it could never fire for the stated reason.
2. Build the embedder point bag exactly as `src/gpu_run4/training.py:16 _point_bag`, run
   `embedder` + `encoder("fwd", causal=False)` **once**, cache `src_enc` for every sequence in the
   cell. This is both the compute saving and the fairness construction (§5 item 4).
3. Score with `decoder("fwd", causal=True, src_enc=..., src_len=...)` then
   `decoder("predict", tensor=..., pred_mask=..., y=..., get_scores=True)`, gathering log-softmax at
   the `pred_mask` positions, for: **GT-mult** (the stored `tree_encoded`, the corpus multiplicative
   encoding); **GT-affine** (the Part B affine rewrite re-encoded via
   `env.equation_encoder.encode`; on failure → `AffineEncodingUnavailable`, logged, cell contributes
   GT-mult only); **each usable candidate** re-encoded from `candidate_formula_raw`; and **the
   selected candidate** under the frozen selection rule, identified explicitly.
   **Instrument change, declared not discovered.** `src/gpu_run4/training.py:23
   teacher_forcing_loss` returns the **mean** CE via `get_scores=False`. C0001 **adds** a new
   function (it does **not** modify the existing one, which other phases depend on) returning
   `(sum_logprob, n_scored_tokens, per_token_logprobs)`. A regression test must assert
   `sum_logprob / n_scored_tokens == -teacher_forcing_loss(...)` to within 1e-5 on ≥ 5 fixed
   examples.
4. **Re-encoding round-trip audit** (the single largest threat to Part C, since no log-prob was ever
   stored — P9). For every candidate: `encode(parse(raw))` → `decode` → canonicalize, compared to
   the stored `candidate_formula_canonical` **after the frozen separator normalization
   `\|` → `,\|,`** (AUDIT-MAJ-7; raw equality is 20/80 and normalized equality 80/80, Q8, so an
   unnormalized comparison self-aborts Part C for a cosmetic reason).
   - exact → `candidate_reencoding_roundtrip_exact = True`, usable;
   - mismatch → `CandidateReencodingMismatch`; **excluded from the comparison distribution but
     counted and reported**;
   - > 10% of a cell's candidates mismatch → cell `unreliable_reencoding`, excluded from the Part C
     decision endpoint, reported separately;
   - > 10% of cells `unreliable_reencoding` → **Part C `undecidable`**.
   The Stage-6 smoke must demonstrate ≥ 90% exact round-trip on a known-good cell **before** Part C
   runs.
5. **Commutation-orbit report (optional mitigation of §5 item 6, gated on measured cost).**
   Enumerate the GT encoding's commutation orbit under `add`/`mul` operand swaps to a frozen cap of
   **8** orderings, deterministic traversal, and report `logsumexp` over the orbit beside the
   single-encoding value. This converts a lower bound into a tighter lower bound at the cost of 8
   extra decoder passes per cell against 50 candidate passes. **Frozen gate**: enabled only if the
   Stage-6 smoke measures the total Part C projection at ≤ 2.0 GPU-hours with it enabled; otherwise
   it is dropped and the §5 item 6 bias remains disclosed-only. No orbit value may be used in any
   decision rule; it is `descriptive`.

### 8.3 Part C endpoints, the E2/E3 discriminator, and the length policy

**Length policy, frozen (STAT-M11).** An autoregressive decoder defines a normalized distribution
over variable-length token sequences, so `logP(A)` and `logP(B)` are probabilities of two events in
one sample space and comparing them is valid regardless of length. **Summed log-probability is the
only variant that is a probability comparison and the only variant that may bear a decision.**
Per-token mean log-prob is **not** the log-probability of anything — it is a length-normalized
decoding heuristic — and ±20% length-matching selects on a variable strongly correlated with
structural complexity while making the analyzed set outcome-dependent. Both are retained as
`descriptive` and may not support an E2 or E3 attribution. v1's conjunctive triple-report gave two
statistics that cannot bear the interpretation **veto power over the one that can**; it is dropped.

**THE E2/E3 DISCRIMINATOR (frozen; the promoted C-S6).** Precedented by Stahlberg & Byrne
(DOI 10.18653/v1/D19-1331), which compares the model score of the reference against the model score
of **the sequence search actually returned** — no reference distribution, no temperature distortion,
no normalization choice. Per usable cell `c` of an in-support system `s`:

- `lp_gt(c)` = summed log-prob of GT-mult; `lp_sel(c)` = summed log-prob of the **selected**
  candidate; `lp_best(c)` = max over usable candidates.
- **`sb_sel(c) = 1[ lp_gt(c) > lp_sel(c) ]`** — the model preferred the truth over what search
  returned ⇒ **search error (E3)** for that cell.
- `sb_best(c) = 1[ lp_gt(c) > lp_best(c) ]` — reported alongside.
- `sb_rate(s)` = mean of `sb_sel(c)` over the system's usable cells.
- `E3_system(s) = 1[ sb_rate(s) ≥ 0.5 ]`; `E2_system(s) = 1[ sb_rate(s) = 0 ]`.

| id | endpoint | inference |
|---|---|---|
| **C2-P** | **`search_error_system_rate`** = `Σ_s E3_system(s) / n_in_support` | **the Part C decision endpoint**; Wilson 95% **and** family-clustered bootstrap (interval of record) |
| C2-S1 | `model_error_system_rate` = `Σ_s E2_system(s) / n_in_support` | descriptive; same two intervals |
| C2-S2 | mean `sb_rate` across systems, and `sb_best` versions of C2-P and C2-S1 | descriptive |
| C2-S3 | paired `lp_gt − lp_sel` per system (nats, **summed**), and the per-token version | descriptive; cluster bootstrap. The per-token version may not bear a decision. |
| C2-S4 | `lp_gt(GT-affine) − lp_gt(GT-mult)` per system, **summed** | descriptive; cluster bootstrap. Dropped if > 20% of in-support systems lack an affine encoding. |
| C2-S5 | **per-position GT-token-rank profile** — for each GT position, the rank of the GT token in the model's predicted distribution, aggregated over cells and systems, broken out by token class (operator, mantissa, exponent, the `\|` component separator) | descriptive | **strictly stronger than any rank-in-50 statistic and immune to the length confound; costs nothing extra** since `per_token_logprobs` is already stored (STAT-M11) |
| C2-S6 | **descriptive rank panel**: `rank_pct_sum`, `rank_pct_per_token`, `rank_pct_length_matched`, `below_all_indicator` | **descriptive only** | frozen note: *the 50 candidates were drawn at T = 0.1, i.e. from p^10 renormalized, and are an extreme upper-tail sample of the model's distribution. A sequence the model ranks above 99% of everything it could emit still falls below every one of 50 such draws (STAT-C4). A low rank does not establish model error and no E2/E3 attribution may cite these.* |
| C2-S7 | **reference-resolution diagnostic**: per cell, the interquartile range of the 50 candidate summed log-probs, and the GT gap in IQR units | descriptive; gates C2-S6 | frozen: *if the GT gap exceeds 5 × IQR in more than 20% of cells, the reference distribution has no resolution and no rank-based statistic in C2-S6 may be interpreted at all* |
| C2-S8 | instrument audit: re-encoding mismatch rate, `unreliable_reencoding` cell rate, `AffineEncodingUnavailable` rate, `CellIdentityMismatch` rate, payload-digest distinct-count check, `sum/n == −mean_CE` regression result | descriptive; gates §10.1 | |
| C2-S9 | GT token length vs `lp_gt` and vs `sb_sel` | **exploratory** | |

**Corpus-level attribution rule (frozen, with its dead zone named).**

- **E3 (search error) predominant** iff the family-clustered 95% **lower** bound of C2-P > 0.5.
- **E2 (model error) predominant** iff the family-clustered 95% **upper** bound of C2-P < 0.5
  **and** the clustered lower bound of C2-S1 > 0.5.
- **Otherwise `neither_E2_nor_E3_predominant`** — a real, reportable result, explicitly **distinct
  from `undecidable`**, which is reserved for instrument failure (§10.3).
- **Disclosed operating characteristic**: at `n_in_support ≈ 30–60` a proportion's 95% interval is
  0.2–0.3 wide in the middle of the range, so `neither_E2_nor_E3_predominant` is the **expected**
  corpus-level outcome. Part C's deliverable is therefore primarily the **per-system partition**
  (§10.3), which is well-defined regardless, not the corpus-level label.
- **No corpus-level attribution may invalidate a GPU_RUN5 result on its own.** An E2 or E3
  attribution triggers the replication gate (§15).

**Part C null-credibility conditions (v1 had none; STAT-C4).** All must hold or Part C is
`undecidable`: **NC1** the `sum/n == −mean_CE` regression test passes to 1e-5 on ≥ 5 fixed examples;
**NC2** the normalized re-encoding audit is within the §8.2 step 4 tolerances; **NC3** every scored
cell passes the §8.2 step 1 identity assertions, including the 10-distinct-payload check; **NC4** the
C2-S7 resolution diagnostic is reported (its failure gates only C2-S6, since no decision depends on
a rank statistic); **NC5** `n_in_support ≥ 30`, else Part C is `exploratory` and attributes nothing.

---

## 9. Statistical plan

### 9.1 Estimators and intervals

| endpoint class | estimator | interval | note |
|---|---|---|---|
| **primary** (component-level gain rate over `\|H\|`) | proportion over the component-level `gain` indicators | (a) plain **Wilson score**, z = Φ⁻¹(0.975) = **1.959964**, no continuity correction, labeled `assumes_component_independence: true`; (b) **two-stage cluster bootstrap** percentile 95% (families with replacement, then systems within family with replacement, **10,000** resamples, **seed 20260909**) — **interval of record**; (c) 8-cluster Wilson on the family indicator as a bounding case | v1 promised "a clustered interval" and specified `src/gpu_run4/aggregation.py:22 student_t_ci`, which is a plain symmetric unclustered Student-t with `ddof=1`, unbounded, whose simulated coverage at a 0.05 rate is **0.909–0.913** with a **negative** lower limit 5–17% of the time (STAT-M3). **`student_t_ci` may not be used for any proportion in C0001.** The clustered estimator must be added to the Part A implementation ticket by name so it is not silently substituted. |
| component- and system-level proportions (A2-S1…A2-S4, B2-S1, B2-S2, C2-P, C2-S1) | proportion over the relevant indicators | Wilson + cluster bootstrap, both reported; raw limits reported, **never silently clipped** to [0, 1] | STAT-m8 |
| per-system continuous means (A2-S4 MEAN, C2-S2, C2-S3, C2-S4) | mean of per-system means | cluster bootstrap over systems and families; `student_t_ci` may be reported **beside** it, labeled unclustered | the two-stage estimator is valid regardless of within-system dependence, which is absorbed into between-system variance (STAT-OK-3) |
| control sensitivity / specificity | proportion over 80 systems, 170 components, or the stated eligible set | exact counts against exact thresholds; **no interval carries a decision** | |

**Explicit invalid-test warning, retained verbatim in intent (endorsed).** The natural "M3 rate
minus M0 rate" comparison at **system** level is **degenerate**: M0 is 0 for all 80 systems at
system level (P0a), so the per-system paired difference equals the M3 indicator exactly and its
sampling distribution is Bernoulli, not t. **No paired t-test is run on it**; it is reported as the
Wilson interval on the M3 indicator with the note that system-level M0 ≡ 0. This does **not** apply
at component level, where M0 is 107/2040 and the paired difference is genuinely informative — which
is why the primary lives there.

**One-sidedness labeling (STAT-m3).** Every "upper bound" in this document is the upper limit of a
**two-sided 95%** interval, i.e. a **97.5% one-sided** bound — conservative, and labeled as such.
For reference, the one-sided 95% Wilson upper at 0/80 is **0.0327** and the rule-of-three
approximation is **0.0375**. A reader comparing against a one-sided 95% bound elsewhere in the
campaign is not comparing like with like unless the label is carried.

### 9.2 Clustering, the ICC conditional, and the target population

Family is perfectly confounded with dimension (P8), and whether a candidate structurally matches a
truth is overwhelmingly a property of the truth's *structure*, i.e. of the family template. The
design effect is `deff = 1 + (m − 1)·ICC` with m = 10 systems per family:

| ICC | deff | n_eff (from 80) | Wilson upper @ 0 hits | < 0.05? |
|---|---|---|---|---|
| 0.00 | 1.00 | 80.0 | **0.0458** | yes |
| **0.011** | 1.10 | 72.8 | **0.0500** | **boundary** |
| 0.10 | 1.90 | 42.1 | 0.0836 | no |
| 0.20 | 2.80 | 28.6 | 0.1185 | no |
| 0.30 | 3.70 | 21.6 | 0.1509 | no |
| 0.50 | 5.50 | 14.5 | 0.2089 | no |
| 1.00 | 10.00 | 8.0 | 0.3244 | no |

**A naive Wilson bound below 0.05 survives only for ICC ≤ 0.011.** At the family level, 0/8 gives
[0, 0.3244]. Supporting evidence that the ICC is not negligible: GPU_RUN5's bundle rank stability is
Spearman 0.480 / Kendall 0.389, and GPU_RUN4's dimension gradient (1-D 17/92, 2-D 2/112, 3-D 0/40)
is a between-family effect of enormous size, since dimension **is** family here.

**Frozen conditional (pre-committed, not a post-hoc rescue).** The empirical ICC of the primary's
component-level indicator is a **reported quantity**. If **ICC ≥ 0.011**, any naive-Wilson bound is
**withdrawn** and the family-clustered bound is the reported result. **If the observed count is
zero the ICC is not estimable** — every indicator is identical — and in that state the
family-clustered bound is **automatically** the bound of record, with the naive Wilson reported
beside it under `assumes_component_independence: true`. This is why the primary's inferential
content is the §7.3 **powered-falsification statement** and not a small-margin bound: at this
corpus size an honest clustered bound is of order 0.1–0.32 and would license almost nothing.

**Target population**: as §2.2. The finite-population reading is recorded and rejected as the
estimand.

### 9.3 The outcome ladder, corrected, with its operating characteristics disclosed

**Primary ladder** (`K` = observed Hill-stratum gains, `C = ceil(0.02 · |H|)`; at `|H| = 140`,
`C = 3`):

| observed `K` | verdict label | consequence |
|---|---|---|
| **0** | **`no_gain_observed_bound_only`** | H-C0001-P **supported**. Licenses **only** the §9.5 item 1 sentence plus the §7.3 power statement. |
| **1 … C** | `weak_gain` | H-C0001-P **unsupported** (not refuted). E0 operates at component resolution at a magnitude below what it needs; GPU_RUN5's component-level interpretation requires **partial revision**. Replication gate triggered. |
| **> C** | `matcher_attributable_gain_confirmed` | H-C0001-P **refuted**. E0 confirmed at the resolution that matters; GPU_RUN5's component-level interpretation **requires revision**. Replication gate **mandatory** (§15). |

The verdict label was renamed from v1's `null_credible` because **labels travel downstream and
caveats do not** (STAT-M7). Every artifact carrying the verdict must also carry the §9.5 item 1
sentence **verbatim in a machine-readable field**, the same mechanism §0.4 already requires for
`prior_information_disclosed`.

**Corrected Wilson values at n = 80** (v1's ladder values were computed at n = 79, and its
"lower bound > 0.013" is reproducible by no method — not plain Wilson, continuity-corrected Wilson,
Jeffreys, Agresti–Coull or Clopper–Pearson):

| k / 80 | Wilson 95% | Clopper–Pearson 95% | v1 stated | upper < 0.05? |
|---|---|---|---|---|
| 0 | **[0.0000, 0.0458]** | [0.0000, 0.0451] | upper `0.0462` (n = 79) | yes |
| 1 | **[0.0022, 0.0675]** | [0.0003, 0.0677] | lower `0.0026` (n ≈ 70) | no |
| 2 | **[0.0069, 0.0866]** | [0.0030, 0.0874] | — | no |
| 3 | **[0.0128, 0.1045]** | [0.0078, 0.1057] | upper `0.1055` (n = 79) | no |
| 4 | **[0.0196, 0.1216]** | [0.0138, 0.1231] | "lower > `0.013`" — no method reproduces this | no |
| 8 | **[0.0515, 0.1851]** | [0.0442, 0.1876] | — | no |

At n = 80 an upper bound below 0.05 is attainable **only** at exactly zero hits; the smallest n at
which one hit still permits it is **110**, and two hits **142**. These values govern the demoted
system-level secondary A2-S3. The primary's ladder is at `n = |H|` and its table must be computed
from the frozen formula and written before counting (§7.2 step 2).

**Operating characteristics of the 0 / 1–3 / ≥ 4 cutpoints at n = 80, under a homogeneous binomial
(which the clustering analysis above already shows is optimistic) — disclosed, not implied:**

| true rate p | P(K = 0) → lower rung | P(1 ≤ K ≤ 3) → middle | P(K ≥ 4) → upper rung |
|---|---|---|---|
| 0.000 | 1.0000 | 0.0000 | 0.0000 |
| 0.005 | 0.6696 | 0.3297 | **0.0007** |
| 0.010 | 0.4475 | 0.5438 | **0.0087** |
| 0.0125 | 0.3656 | 0.6162 | **0.0182** |
| 0.020 | **0.1986** | 0.7245 | **0.0769** |
| 0.030 | **0.0874** | 0.6933 | **0.2193** |
| 0.050 | 0.0165 | 0.4119 | 0.5716 |

**Frozen disclosure sentence, required in every artifact reporting a ladder verdict:** *"The upper
rung fires with probability 0.077 / 0.219 when the true rate is 0.02 / 0.03; the lower rung fires
with probability 0.199 / 0.087 at those same rates. Neither rung is calibrated. This is why the
replication gate is mandatory for the upper rung and why the bound — not the point estimate — is the
reported result for the lower rung."* No cutpoint moves: 0, 1 and `C` are as defensible as any other
choice at this n. What was missing in v1 was the disclosure, not a different threshold.

### 9.4 Multiplicity

**Exactly one primary endpoint** (§7.1), at α = 0.05, **unadjusted**.

**The Holm plan is dropped in full** (STAT-M4). It was not executable: no null hypothesis or test
statistic was ever defined for any secondary, so there were no p-values to order; family S2 would
have corrected a **deterministic census** the plan itself correctly described as noiseless; family
S1's members are deterministic re-reductions of the same M3 indicator set as the primary (an M2 hit
implied an M3 hit under the frozen monotonicity, and A-S2/A-S4 are re-reductions), so the correction
controlled nothing; S1's *m* was ambiguous between 3 and 10; and S3's members carried their own
uncorrected decision thresholds, leaving the governing alpha undefined. A decorative correction is
worse than none, because it creates a false impression of error control.

**In its place, frozen:**

1. **Every non-primary endpoint is `descriptive` or `exploratory`.** None receives a hypothesis
   test. None may support a confirmatory claim, a `supported` verdict, or the invalidation of a
   GPU_RUN5 result.
2. **Simultaneous coverage is stated explicitly, with `m` as a number.** Reported intervals are
   nominal 95%, and each descriptive group additionally reports **Bonferroni-widened** intervals at
   α/m: Part A `m = 7` (A2-S1, A2-S2, A2-S3, A2-S4, A2-S5, A2-S6, A2-S8; A2-S7 is a statement and
   is not an endpoint), Part B `m = 7` (B2-S1…B2-S7), Part C `m = 8` (C2-S1…C2-S8). Every such
   artifact carries the frozen sentence *"these intervals are not multiplicity-controlled and no
   secondary supports a confirmatory claim."*
3. **Decision rules and estimation intervals are different objects**, and each decision rule states
   its own bound: the **primary ladder** decides on counts (0 / 1…C / > C) and reports a two-sided
   95% (= one-sided 97.5%) clustered bound; **Part C's attribution rule** decides on the family-
   clustered 95% bound of C2-P against 0.5; the **control battery** and the **gates** decide on
   exact counts and rates with no alpha at all.
4. **The M0 / M1 / M3 multiplicity is absorbed, not corrected** (STAT-M5, endorsed). M3 is the
   **most permissive** level, so under the frozen monotonicity `M0 ⊆ M1 ⊆ M3` the M3 indicator
   dominates: if M3 returns 0, every level returns 0. The primary is a **maximum** over the cascade,
   which is the adversarially correct choice for a null-shaped hypothesis, and no type-I inflation
   arises in the null direction. **This argument is conditional on the monotonicity check of §7.5
   actually passing**; that check is therefore the *precondition* for the primary's multiplicity
   argument, not merely an internal audit.

### 9.5 Non-significance is not equivalence (rule 01 item 8)

Frozen wording constraints for every C0001 artifact, report and abstract:

1. **A primary observation of 0 gains licenses exactly this and nothing more:** *"No Hill /
   variable-denominator truth component gained an in-beam structural match under M3 that the frozen
   M0 matcher scored as a miss. The family-clustered 95% upper bound on the per-component gain rate
   is [value]; the naive Wilson bound, which assumes zero intra-family correlation, is [value]. The
   design had [power] probability of observing at least one gain had the gain rate been 0.0525, the
   component-level in-beam rate the frozen matcher already achieves."*
   It does **not** license: "the gain rate is zero"; "the matcher makes no difference"; "M0 and M3
   are equivalent"; "canonicalization is unnecessary"; "the two matchers agree"; or any statement
   about components outside stratum H.
2. **Any Part C interval containing 0 licenses only:** *"this design did not detect a difference of
   the preregistered size."* It does **not** license "GT-affine and GT-mult are equally probable"
   (C2-S4) or "the GT is as likely as the sampled candidates".
3. **A Part B rate of 0 licenses only:** *"no validation system was out of support under the
   preregistered rewrite set."* It does **not** license "the truth is in the generator's support".
4. **On equivalence claims (rewritten; v1's blanket prohibition contradicted its own primary and
   instructed Stage 9 to strike it — STAT-M6).** The primary is a **preregistered one-sided
   bound with margin 0.05 on the Hill-stratum gain rate, evaluated as a confidence-bound inclusion
   test**, which is the standard one-sided analogue of TOST for a bounded rate, plus the power
   statement of item 1. That is legitimate and is specifically **not** the rule-01-item-8 error,
   because it asserts a bound rather than inferring sameness from non-significance. **No *other*
   equivalence claim may be made in C0001** — in particular no claim of equivalence between matcher
   levels, between the two GT encodings, between the GT and the sampled candidates, between strata,
   or between families, for none of which is a margin preregistered. Stage 9 enforces **this**
   sentence, not v1's.
5. **"Not significant" is never reported as evidence of equivalence anywhere in this cycle.** Where
   an interval is wide, the width is reported as the finding.

---

## 10. Go/No-Go gates, aborts, verdicts

### 10.1 Gates

**Gate 0 — pre-run; all must pass before any endpoint is computed.**

1. `git branch --show-current` == `20260909_researce_GPU_RUNclaude1`; `git status --short` clean or
   fully explained in the manifest.
2. **`PYTHONPATH=. pytest GPU_RUN5/tests/test_gpu_run5_firewall.py GPU_RUN5/tests/test_gpu_run5_phase8.py -k "firewall or sealed or test_open"` green** (4 tests), **plus** the new
   C0001-specific firewall test of §2.4 item 5 green, **plus** `PYTHONPATH=. pytest GPU_RUN5/tests
   --collect-only` collecting 124 tests with **zero** collection errors. v1's chosen invocation
   covered an accessor C0001 never calls while the real firewall-ordering assertions were
   un-collectable (AUDIT-MAJ-9).
3. A fresh Stage-5 reproducibility audit of the **v2** design reports **zero CRITICAL** findings;
   `grep -rn sealed` over the C0001 diff shows no direct sealed read.
4. Checkpoint SHA256 == `56754040be…a5e8`.
5. Input SHA256 recorded for every file on the §2.4 allowlist, from the instrumented opener; no
   directory argument was passed to `run_manifest.py`; `sealed_paths_read` computed and empty.
6. GPU 0 idle temperature < 70 °C; free VRAM ≥ 6.0 GiB (measured 7,154 MiB free at 49 °C, Q9);
   disk free ≥ 40 GiB (measured 117 G).
7. Stage-6 smoke on `phase4/fixed_grn_validation_panel.json` (24 systems) completes, writes a
   manifest, equation records and failure records, demonstrates resume, **demonstrates
   `_time_limit` firing inside a worker process**, and demonstrates ≥ 90% normalized re-encoding
   round-trip on a known-good cell.
8. **Measured Part A cost calibration (§11.1) completed and within budget**, with the frozen
   constraint that no match indicator produced during timing calibration was aggregated or stored.
9. `R/phase1/component_strata.json` and `R/phase1/partA_ladder_realized.json` written and hashed
   (§7.2 steps 1–2) **before** any match indicator is computed.
10. New run directory does not already exist (verified at freeze: no `results/runs/gpu_runclaude1*`;
    27 existing run directories plus one stray log file).

**Gate A → B.** Proceed to Part B only if **all**:
(i) the M0 arm reproduces **all 47,987 stored per-candidate fields and all 101,963 component
comparisons exactly**, including the 2,235 component ones, and the reduced values 0/960 (system,
mean over cells) and 107/2040 (component) — §7.6;
(ii) **PC0 = 170/170 components and 80/80 systems**;
(iii) **PC2a = 80/80** (verification of Q1) and **PC3a = 48/48 of its eligible set** (verification
of Q2); PC2b/PC2c/PC2d ≥ 76/80; PC3b ≥ 58/60;
(iv) `could_not_evaluate_rate` ≤ **2.0%** and monotonicity violations ≤ **1%**;
(v) the §7.6 reproduction protocol was not triggered, or was triggered and resolved.
*If the control battery fails, Part B may still proceed* (independent instrument, no shared
matcher), but Part A is reported `undecidable` and Part C is **not** run.

**Gate B → C.** Proceed to Part C only if **both**:
(i) Part A is **not** `undecidable`. If Part A lands on `matcher_attributable_gain_confirmed`,
**Part C is not run in C0001**: the premise has changed and the correct next move is replication of
Part A (§15), not a diagnosis of a failure whose extent has just moved.
(ii) `n_in_support ≥ 30` validation systems are fully in support **and** have Part A component
gains = 0 — i.e. in-support truths that were still never generated. If `n_in_support < 30`, Part C
runs but is reported **exploratory** and attributes nothing.

**Gate C → report.** Part C endpoints are reported only if NC1–NC3 pass (§8.3). Otherwise Part C is
`undecidable`.

### 10.2 Abort and crash-loop conditions

- Cumulative GPU 0 time > **4.0 h**, or CPU > **24 core-hours**, or new disk > **15 GiB** ⇒ abort
  the running part, preserve partial artifacts, report what completed.
- Peak VRAM on GPU 0 > **5.5 GiB** at any sample ⇒ abort immediately (GPU 0 is shared with the
  user's live desktop; ~629 MiB is already held). Preregistered fallback chain, in order: Part C
  batch size to 1 → the §14 reduced cell design → GPU 1 (GTX 1060 3 GB, forward-only, batch 1). The
  chain changes **which cells** are scored, never the numerics: fp32 throughout, never fp16, never
  CPU, so log-probability comparability is preserved.
- GPU 0 temperature > 85 °C sustained 60 s ⇒ pause, cool, resume once.
- **Crash-loop rule (rule 06)**: **3 consecutive identical fatal failures with no new diagnostic
  information ⇒ stop and reassess.** Record the three tracebacks and their identical signature in
  the cycle report, classify the bottleneck via `negative-result-recovery`, and end the cycle. A
  failed hypothesis does not justify more compute.
- **Projected-throughput abort**: if the §11.1 measured calibration projects Part A > **12
  core-hours** or the Stage-6 smoke projects Part C > **2.0 GPU-hours**, invoke the §14 reduced
  designs **before** starting, not midway.

### 10.3 Supported / unsupported / undecidable

**For the primary hypothesis H-C0001-P:**

| verdict | criterion |
|---|---|
| **supported** | Gate A → B passed in full; primary `K = 0`; reported as the §9.5 item 1 sentence plus the §7.3 power statement, with the family-clustered bound of record |
| **unsupported** | Gate A → B passed in full; `1 ≤ K ≤ C` (`weak_gain`) |
| **refuted** | Gate A → B passed in full; `K > C` (`matcher_attributable_gain_confirmed`); replication gate mandatory |
| **undecidable** | M0 fails exact reproduction; **or** PC0 ≠ 170/170; **or** PC2a ≠ 80/80 or PC3a ≠ its known value; **or** `could_not_evaluate_rate` > 2.0%; **or** monotonicity violations > 1%; **or** the two-sided sensitivity analysis of §7.5 item 3 disagrees on the rung; **or** the strata/ladder artifacts were not written before matching; **or** `\|H\|` < 40 and the fallback primary is also unmeasurable; **or** the run aborted before the primary was computed |
| **underpowered_bound_only** | `40 ≤ \|H\| < 100` and realized power to detect 0.0525 < 0.90, with `K = 0`. Reportable; **may not be cited as refuting E0.** |

**For the four-way mechanism attribution** (secondary; reported as a **partition**, never a single
winner):

| mechanism | attributed to a component or system when |
|---|---|
| **E0** | that **component** has an M3 in-beam match that M0 scored as a miss (`gain = 1`), reported separately for stratum H and stratum L |
| **E1'** | Part A gain = 0 for the system **and** ≥ 1 of its components has `U_min > 3` (out of support **under the preregistered rewrite set**) |
| **E2** | Part A gain = 0, system fully in support, and `E2_system(s) = 1` (§8.3) |
| **E3** | Part A gain = 0, system fully in support, and `E3_system(s) = 1` |
| **unattributed** | none of the above, or Part C `undecidable`/`exploratory` for it |

The report must state counts in all five buckets at both component and system resolution. Overlaps
are possible and must be **shown, not resolved by fiat**. **No single-number "the cause is X" claim
is permitted.**

### 10.4 Every part remains informative on failure

Frozen, because a cycle whose parts can only succeed is not an experiment:

| part | if its own hypothesis fails or its instrument breaks, what is still learned |
|---|---|
| **Part A** | `K = 0` bounds E0 at the resolution that matters and quantifies the power of that bound. `K > 0` locates E0 by stratum and by family. **Either way** the cycle delivers: the first exact reproduction of GPU_RUN5's 47,987 stored matcher fields (C-M0f); the first component-type stratification of its 107 published component matches; the M0/M1/M3 increment table; a measured `could_not_evaluate` rate for the CAS-free skeleton path; and PC0-CAS's measured verdict on whether the repository's CAS path can recognize a GRN truth as itself. If the instrument fails, the failure is itself the reportable result — v1 would have shipped a green null with 55.1% of its M2 comparisons never performed. |
| **Part B** | `out_of_support_rate = 0` refutes E1' for this corpus and is reportable. Non-zero quantifies it and decomposes it into multiplicative-Hill-4 vs multi-term mechanisms, of which the second is a mechanism the original brief did not name. The H/L cross-tabulation (B2-S7) is informative either way. |
| **Part C** | The expected corpus-level outcome is `neither_E2_nor_E3_predominant`, and that is **reported as a result**, not as a failure. The per-system partition, the per-position GT-token-rank profile (C2-S5) and the reference-resolution diagnostic (C2-S7) are all delivered regardless of which label the corpus-level rule returns. If the re-encoding audit fails, the finding is that GPU_RUN5's stored candidate strings do not round-trip through the model's own tokenizer — a first-order reproducibility fact about the artifact store. |

---

## 11. Compute ceiling and the measured cost basis

**No ceiling increase is requested.** v1's corrected design did require one — fixing AUDIT-CRIT-3
as v1 specified projects Part A at ≈**66 CPU-core-hours** against a 24 core-hour ceiling, a rule-06
hard stop. v2 avoids that by **removing M2 from the design** (§18), not by raising the ceiling.

| resource | ceiling (rule 06 / `research_state.md` §5) | v2 allocation | basis |
|---|---|---|---|
| GPU 0 (RTX 2070, 8,192 MiB total / 7,154 MiB free measured, **shared with the user's live desktop**) | **≤ 4.0 GPU-hours** | Part C ≤ 2.0 h; Stage-6 smoke ≤ 0.3 h; reserve 1.7 h | v1 allocation retained; Part C's work is unchanged in kind |
| peak VRAM on GPU 0 | **≤ 5.5 GiB** | Part C target ≤ 3.0 GiB | 60.6M params fp32 ≈ 242 MB weights, cached `src_enc` per cell, batch ≤ 8, seq ≤ 200 — assessed feasible at audit (AUDIT-OK-12) |
| CPU | **≤ 24 core-hours** | **Part A ≤ 12** · Part B ≤ 2 · Part C host-side ≤ 2 · **total ≤ 16, slack 8** | **measured**, see below |
| new disk | **≤ 15 GiB** | ≈ 3–6 GiB under `R/` | v1 estimate, assessed sound at audit (AUDIT-OK-13) |
| RAM | 60 GiB total / 52 GiB available (measured) | ≤ 6 worker processes, one comparison resident each; `all_candidates.json` is 174 MB on disk | AUDIT-OK-13 |
| GPU 1 (GTX 1060 3 GB) | forward-only fallback | only under the §10.2 chain | AUDIT-OK-12 |

### 11.1 The measured basis for Part A, and what is still unmeasured

**Measured (Q6, `lansr310`, 150 randomly sampled real GRN candidates, full M1+M2+M3 cascade):**
mean **795 ms/candidate**, median 604 ms; per family R01 953, R02 390, R03 1269, R04 399, R05 658,
R06 1077, R07 871, R08 604 ms. Projection for all 47,987 candidates: **10.60 single-core-hours.**

This is v1's P11 replaced: P11 estimated 129 ms/candidate on the **ODEBench** corpus and projected
1.72 core-h, which was **6.2× wrong** and already above v1's own 8 core-h allocation.

**How the measured number bounds v2.** v2's endpoint pass runs **M0 + M1 + M3** and never calls
`_sympy_components_equal`. Removing M2 strictly removes work from the measured cascade, so
**10.60 core-h is a measured upper bound on v2's Part A endpoint pass.** Bounded additions:
PC0-CAS at 80 calls × `SYMPY_EQUIV_TIMEOUT_SEC = 10 s` ≤ **0.22 core-h** worst case; the control
battery at ≈ 640 synthetic system comparisons × 0.795 s ≈ **0.14 core-h**; the M0 exact-reproduction
pass is a subset of the same pass. Allocation **12 core-h** therefore carries measured headroom
above a measured upper bound, inside a 24 core-h ceiling.

**What is honestly not measured**, and is therefore gated rather than assumed:
(a) the M0+M1+M3-only per-candidate cost — known only to be **≤ 795 ms**;
(b) the overhead of the §7.5 failure-reason instrumentation;
(c) wall-clock under 6-process parallelism.
**Frozen requirement (Gate 0 item 8): a measured calibration before the full run.** Sampling frame
frozen now: **400 candidates, 50 per family**, drawn from `phase3/all_candidates.json` with
`numpy.random.default_rng(20260909)`, scored through the exact v2 Part A pipeline, **timing only**.
Report mean, median and p95 per family; project `mean × 47,987`. If the projection exceeds **12
core-h**, the §14 reduced design applies **before** starting.
**Integrity constraint on the calibration, frozen:** the calibration harness must **discard the
match boolean at the call site**, before any aggregation. No match indicator produced during timing
calibration may be stored, printed, logged, aggregated or read by any agent, and the calibration
artifact `R/phase0/partA_cost_calibration.json` contains **timings and failure labels only**. A
calibration that reports a match rate has leaked the endpoint and Part A becomes `undecidable`.

---

## 12. Run ID and artifact contract

**Run ID.** `gpu_runclaude1_c0001_<short7>`, `<short7>` = the first 7 characters of the git commit
**at run start**. At freeze that is **`gpu_runclaude1_c0001_de894b4`**. v1 recorded
`gpu_runclaude1_c0001_94a571b` derived from the wrong commit (AUDIT-MIN-1: the preregistration was
introduced by `7cfc0ff`, not `94a571b`). If the directory exists, append `_v2`, `_v3`, …; **never
overwrite** any of the 27 existing `results/runs/*` directories (rule 05). Verified: no directory
begins with `gpu_runclaude1`. `git reset --hard` and force-push are forbidden. Branch and commit are
recorded in every manifest via `scripts/ops/run_manifest.py`, **with the §2.4 file-level allowlist
only**. `campaign` must be passed through to `write_manifest`, which hardcodes
`{"campaign": "GPU_RUN5", ...}` at `src/gpu_run5/config.py:45` (AUDIT-MIN-4), so C0001 phase
manifests are not mislabelled.

### 12.1 Expected artifacts

Run root **`R = results/runs/gpu_runclaude1_c0001_<short7>/`**. Every `R/` below is literal; v1's
`.../` abbreviation was ambiguous with the GPU_RUN5 run directory and was a rule-05 hazard
(AUDIT-MIN-3).

| path | content |
|---|---|
| `R/manifest.json` | branch, commit, `pip freeze`, GPU + driver, checkpoint SHA256, **per-file** input fingerprints, per-phase status, `campaign: GPU_RUNclaude1_C0001` |
| `R/phase0/environment_audit.json` | env, GPU/temp/VRAM, disk, library versions |
| `R/phase0/checkpoint_audit.json` | checkpoint SHA256 + size + persisted generator config |
| `R/phase0/firewall_test.json` | the §10.1 item 2 test results; **computed** `sealed_paths_read` |
| `R/phase0/input_fingerprints.json` | SHA256 of every path the instrumented opener actually opened |
| `R/phase0/partA_cost_calibration.json` | §11.1 measured calibration — **timings and failure labels only** |
| `R/phase1/component_strata.json` | the §7.2 H/L assignment for all 170 components, `\|H\|`, `\|L\|`, per-family and per-dimension breakdown, file SHA256. **Written before any matching.** |
| `R/phase1/partA_ladder_realized.json` | the realized-`\|H\|` Wilson table, ladder cutpoint `C`, OC table and power table from the §9.3 / §7.3 frozen formulas. **Written before any matching.** |
| `R/phase1/partA_records.jsonl` | one record per (cell, candidate, component); extended schema (§13) |
| `R/phase1/m0_reproduction.json` | the §7.6 exact-reproduction result over 47,987 candidates / 101,963 component comparisons / 2,235 stored component hits |
| `R/phase1/m0_reproduction_failures.jsonl` | written **only** on a reproduction mismatch |
| `R/phase1/partA_component_summary.json` | per component: `m0_any`, `m3_any`, `gain`, stratum, family, dimension |
| `R/phase1/partA_system_summary.json` | per-system `ANY` and `MEAN` indicators at each level |
| `R/phase1/partA_endpoints.json` | primary + A2-S1…A2-S6, A2-S8, with Wilson, cluster-bootstrap and Bonferroni-widened intervals, the reported ICC, and the verdict with the §9.5 item 1 sentence in a machine-readable field |
| `R/phase1/partA_controls.json` | PC0, PC0-CAS, PC1, PC2a–d, PC3a–b, their eligible sets, `short_circuited` flags, and Gate A→B pass/fail |
| `R/phase1/partA_failures.jsonl` | every could-not-evaluate, timeout, parse error, non-finite and monotonicity violation, with both expressions **and both derivation paths** |
| `R/phase1/matcher_monotonicity.json` | the `M0 ⊆ M1 ⊆ M3` audit and the `m0_any=1, m3_any=0` census |
| `R/phase2/partB_component_records.jsonl` | per component: realized exponents, `U_mult`, `U_affine`, `U_min`, `in_support`, all three budget checks |
| `R/phase2/partB_rewrites.jsonl` | every attempted rewrite with its numeric-verification outcome |
| `R/phase2/partB_endpoints.json` | B2-S1…B2-S7 with `interval_interpretation` |
| `R/phase2/partB_in_support_systems.json` | the Part C eligibility list and `n_in_support` |
| `R/phase3/partC_cell_records.jsonl` | per (cell, sequence): token length, summed log-prob, per-token log-probs, encoding tag, `cell_input_payload_sha256`, round-trip result |
| `R/phase3/partC_identity_audit.json` | §8.2 step 1 assertions, including the 10-distinct-payload check per system |
| `R/phase3/partC_reencoding_audit.json` | normalized mismatch rates, `unreliable_reencoding` cells, `AffineEncodingUnavailable` |
| `R/phase3/partC_endpoints.json` | C2-P, C2-S1…C2-S9, the attribution-rule outcome, and the disclosed dead-zone statement |
| `R/phase3/partC_instrument_test.json` | the `sum/n == −mean_CE` regression test |
| `R/phase3/gpu_telemetry.jsonl` | VRAM/temperature samples at ≤ 10 s interval |
| `R/phase4/mechanism_partition.json` | the five-bucket partition at component and system resolution |
| `R/phase4/compute_accounting.json` | GPU-hours, CPU-core-hours, disk, against the ceiling |
| `GPU_RUNclaude1/analyses/C0001_analysis.md` | Stage 8 analysis |
| `GPU_RUNclaude1/reviews/C0001_statistical_review_stage8.md` | Stage 8 statistical review — a **separate file**, so it does not overwrite the Stage-3 review (STAT-m9) |
| `GPU_RUNclaude1/reviews/C0001_reproducibility_audit_v2.md` | the fresh Stage-5 audit of **this** design |
| `GPU_RUNclaude1/reviews/C0001_independent_review.md` | Stage 9 adversarial review |
| `GPU_RUNclaude1/reports/C0001_report.md` | Stage 11 cycle report (**mandatory even if null / undecidable / aborted**) |
| `GPU_RUNclaude1/reports/C0001_replication.md` | §15, recorded separately, never merged into the primary result |
| `GPU_RUNclaude1/manifests/C0001_artifact_manifest.json` + `C0001_checksums.sha256` | Stage 12 |
| `GPU_RUNclaude1/plans/C0001_preregistration_v2.md` / `.json` | this file and its machine twin |
| `GPU_RUNclaude1/plans/C0001_preregistration.md` / `.json` | **v1, superseded, retained unmodified** |

Large artifacts (`partA_records.jsonl` expected ~0.5–2 GiB) are **not committed**; paths and SHA256s
are preserved in the manifest (rule 05).

---

## 13. Record schema (rule 03)

**Base**: the 30-field `src/gpu_run4/records.py:7 GPU_RUN4_REQUIRED_FIELDS`, **extended, never
replaced**, via `:76 make_formula_record(**extra)`. `campaign = "GPU_RUNclaude1_C0001"`.

**Added fields.**

*Part A matcher* — `matcher_level`, `m0_string_exponent_aware_skeleton_exact`,
`m0_component_exponent_aware_skeleton_exact`, `m1_canonical_exact`, `m3_skeleton_equivalent`,
`component_m3_skeleton_equivalent`, `component_index`, `component_stratum` (`H` | `L`),
`m0_any`, `m3_any`, **`gain`**, `derivation_path` (`infix` for both sides, always),
`match_outcome` (`matched` | `proved_different` | `could_not_evaluate`), `matcher_failure_reason`,
`cas_wall_time_sec`, `monotonicity_violation`, `m0_reproduces_stored_field`.

*Rule-03 completeness* — `true_components_infix`, `candidate_components_infix`, `variable_to_gene`,
`variable_precision`, `variable_recall`, `variable_f1`, `unnecessary_variables`, `near_singularity`,
`extrapolation_valid`, `extrapolation_extreme`, `has_division`, `has_tan`, `complexity`,
`ted_raw`, `ted_skeleton`, `normalized_ted`, `component_normalized_variable_aware_ted`.

*Generation vs selection* — `generation_coverage_scope` (`cell` | `component` | `system`),
`oracle_candidate_index_by_level`, `selected_candidate_index_by_rule`,
`candidate_return_shortfall`, `n_usable_candidates`.

*Controls* — `positive_control_tag` (`none` | `PC0` | `PC0_CAS` | `PC1` | `PC2a` | `PC2b` | `PC2c` |
`PC2d` | `PC3a` | `PC3b`), `control_expected_outcome`, `control_eligible`, `control_short_circuited`.

*Part B* — `u_mult`, `u_affine`, `u_min`, `in_support`, `realized_hill_exponents`, `unary_depth`,
`binary_ops_per_dim`, `uses_only_in_support_operators`, `rewrite_verification_outcome`,
`out_of_support_mechanism` (`multiplicative_hill4` | `multi_term_component` | `other` | `none`).

*Part C* — `gt_encoding` (`mult` | `affine` | `orbit`), `gt_logprob_sum`, `gt_token_length`,
`candidate_logprob_sum`, `candidate_token_length`, `is_selected_candidate`, **`sb_sel`**,
`sb_best`, `sb_rate`, `gt_logprob_per_token`, `candidate_logprob_per_token`, `per_token_logprobs`,
`gt_token_rank_profile`, `candidate_logprob_iqr`, `gt_gap_in_iqr_units`, `rank_pct_sum`,
`rank_pct_per_token`, `rank_pct_length_matched`, `below_all_indicator`,
`cell_input_payload_sha256`, `system_identity_checksum_ok`,
`candidate_reencoding_roundtrip_exact`, `candidate_reencoding_mismatch`, `cell_reliability_flag`.

*Integrity* — `prior_information_disclosed` (mandatory, non-empty, on every artifact carrying a
Part A endpoint), `inference` (`primary` | `descriptive` | `exploratory` | `statement_only`),
`interval_interpretation`, `verdict_scope_sentence` (the §9.5 item 1 sentence, verbatim, on every
artifact carrying a ladder verdict), `assumes_component_independence`, `assumes_family_icc_zero`.

**`FAILURE_REASONS` extension** — the existing enum at `src/gpu_run4/records.py:50` is **kept
intact** (the citation corrects v1's `:47`, AUDIT-MIN-8); C0001 appends exactly:
`CanonicalizationError`, `RewriteVerificationFailure`, `AffineEncodingUnavailable`,
`CandidateReencodingMismatch`, `NumericEquivalenceNonFinite`, `PositiveControlFailure`,
`MatcherMonotonicityViolation`, `LengthMatchUnavailable`, **`SkeletonParseFailure`**,
**`SkeletonEvaluationFailure`**, **`SymbolicNodeCapExceeded`**, **`ComponentCountMismatch`**,
**`CellIdentityMismatch`**. `EncoderCacheMiss` from v1 is **removed** — it could never fire for the
reason v1 gave.

**Failure / exclusion policy (frozen).** Nothing is silently dropped. Every invalid, failed,
timed-out or unparseable equation is written with its `failure_reason` and counted in the
denominator of its own diagnostic rate (rule 01 items 4 and 5). Preserved invalid equations include
the retained non-matching controls. The **only** permitted exclusions, each counted and reported:
(a) candidates failing the Part C re-encoding round trip, from the Part C comparison distribution
only; (b) cells flagged `unreliable_reencoding`, from the Part C decision endpoint only;
(c) cells flagged `CellIdentityMismatch`, from Part C only; (d) cells flagged
`LengthMatchUnavailable`, from the C2-S6 descriptive panel only.
**No exclusion of any kind is permitted from the Part A primary endpoint.**

---

## 14. Deviation policy

General rule: preserve original artifacts, append a dated `DEVIATION-nn` block to **this** file, and
either mark the affected endpoint **exploratory** or open a new preregistered cycle. Never edit
frozen text; never change a threshold to rescue a result (rule 01 item 3).

Named contingencies, decided **now**:

1. **`could_not_evaluate_rate` non-zero.** ≤ 2.0% → proceed, report it as A2-S6, **and** run the
   two-sided sensitivity analysis of §7.5 item 3; if the two directions land on different rungs, the
   verdict is `undecidable`. > 2.0% → `undecidable`. **No timeout value is raised mid-cycle** —
   that would change the frozen instrument.
2. **A needed stored field is absent.** Verified present at freeze: `candidate_formula_raw`,
   `candidate_formula_canonical`, `candidate_exponent_aware_skeleton`, `true_formula`,
   `true_prefix`, `teacher_components_infix`, `teacher_components_prefix`, `tree_encoded`,
   `teacher_token_length`, `valid`, `failure_reason`, `complexity`, the TED fields,
   `trajectory_metrics`, `observations{input, selection, generalization}`. Verified **absent**:
   `symbolic_equivalent`, any log-prob or score field. On absence, recover from
   `phase3/cells/<cell_id>.json`; if still absent the dependent endpoint is dropped, marked
   `not_measurable_from_stored_artifacts`, and reported. **The primary depends only on
   `candidate_formula_raw` and `teacher_components_infix`, both verified present**, so no field
   absence can void it.
3. **An affine encoding cannot be constructed.** Log `AffineEncodingUnavailable`; `U_affine` falls
   back to `U_mult`, making `U_min = U_mult` — the **conservative** direction, which over-reports
   out-of-support, and the report must say so. C2-S4 is dropped if > 20% of in-support systems lack
   one. **Hand-construction is forbidden.**
4. **Part A projected > 12 core-hours** by the §11.1 measured calibration. Reduced design, chosen
   **now**: **6 cells per system** = `{bundle_index 0, 1, 2} × {(σ=0, ρ=0), (σ=0.05, ρ=0.5)}` → 480
   cells, ≈ 24,000 candidates, ≈ 5.3 core-h at the measured upper-bound rate. The endpoint
   definitions are unchanged; only the number of cells entering the `ANY` union shrinks, which
   **weakens** the primary (fewer chances to observe a gain), so a zero under the reduced design
   must be reported with the reduced coverage and the recomputed power stated explicitly.
   **This deliberately differs from v1's reduced design** (`bundle_index == 0`, all 4 corruptions),
   which kept the four *most mutually dependent* cells — four corruptions of one trajectory
   realization in one bundle — and discarded all between-bundle variation, the dimension GPU_RUN5
   measured **least** stable (Spearman 0.480 / Kendall 0.389). v2's subsample spans all three
   bundles at the same compute (STAT-M13).
5. **Part C projected > 2.0 GPU-hours.** The same 6-cell design, then batch 1, then GPU 1
   (§10.2 chain). The commutation-orbit report (§8.2 step 5) is dropped first, before any cell is
   dropped.
6. **M0 fails exact reproduction of the stored fields.** Harness defect, not a finding: §7.6
   protocol; if unresolved, the **entire cycle is `undecidable`**.
7. **`\|H\|` falls outside the §7.3 predicted 130–145 range.** Record a `DEVIATION` noting the
   prediction miss — the prediction is part of the scientific record and a miss is reportable — and
   change **nothing**: the §7.2 frozen fallbacks already cover every case, so no discretion exists.
8. **The strata or ladder artifacts were not written and hashed before matching.** Part A is
   `undecidable`. There is no remedy short of a new cycle ID, because the integrity ordering that
   makes the primary unobserved cannot be reconstructed after the fact.

---

## 15. Replication gate (rule 07, `replication-gate`)

**Trigger, preregistered.** The gate fires if **any** of: (i) the primary lands on `weak_gain` or
`matcher_attributable_gain_confirmed` — a revision or invalidation of a prior published campaign
interpretation, exactly the high-impact case rule 07 reserves the gate for; (ii) the independent
reviewer marks any Part A result fragile; (iii) Part C returns an E2 or E3 corpus-level attribution;
(iv) the component-type stratification of the 107 contradicts the §7.3 frozen prediction in a way
that changes a stated conclusion.

**Minimum replication design, frozen, with at least one independent factor changed:**

| factor | C0001 | replication |
|---|---|---|
| **corpus** | GPU_RUN5 GRN validation, 80 systems / 170 components, Hill-type | **GPU_RUN4 ODEBench**, `results/runs/gpu_run4_phase0_01/phase2/all_candidates.json`, 12,632 candidates, 63 physics/biology systems — different corpus, different generation run, different dimensionality mix |
| **process / path** | this run | fresh process, clean checkout at a recorded commit, independent run ID `results/runs/gpu_runclaude1_c0001r_<short7>/` |
| **agent** | implementation + primary analysis | executed by `lansr-replication-specialist`, distinct from implementer and primary analyst |
| **matcher seed** | **not available, and v1's claim that it was is corrected** | With M3 pinned to `["skeleton"]`, the primary matcher contains **no RNG at all**: `numeric_equivalent(seed=...)` is reachable only from M2's fallback (`formulas.py:498`), which v2 does not run, and M3's numeric grid is hard-coded and non-random (`equation_metrics.py:72-73`, `base = [0.2, 0.7, 1.3, 1.9]`, `+ 0.11 * index`) with no `points` or `seed` parameter. **The primary instrument is deterministic; no seed change can perturb it** (AUDIT-MAJ-8). The replication varies corpus, process and agent only, and this is stated plainly rather than dressed up as a seed perturbation. |

The ODEBench arm carries a **built-in corpus-level positive control**: the frozen string matcher
reports 4/252 = 1.59% [0.0062, 0.0401] truth-in-beam there (C-ODEB), so the cascade must reproduce a
non-zero baseline and must return M3 ≥ M0 on that corpus. **A cascade that returns 0 on ODEBench is
broken**, independently of anything it says about GRN.

**Recorded outcome classes**: `replicated` · `directionally_replicated` · `failed_replication` ·
`inconclusive`. Recorded **separately** at `GPU_RUNclaude1/reports/C0001_replication.md`, never
merged into the C0001 primary result. Per rule 07, a CRITICAL reviewer finding blocks a supported
conclusion regardless of the replication outcome.

---

## 16. Rule 04 — layer analysis contract

**C0001 measures none of the six layer estimands.** No probe/readout (information availability), no
CKA/similarity (representation geometry), no gradient (optimization signal), no
ablation/intervention (causal necessity), no IOLE/single-layer fine-tuning (adaptation capacity), no
selective fine-tuning (multi-layer adaptation). Nothing is averaged into a layer ranking. **No
layer-importance claim may appear in any C0001 artifact.**

The one layer-adjacent item is **A2-S7**, a *statement of a testable consequence for a later cycle*,
not a measurement — and it is re-grounded relative to v1's A-S8. v1 wrote: *"if A-S3 > 0, then
GPU_RUN5's `component_exact_loss = 0.0` at all 16 layers was not at the floor."* The retraction
establishes that this conflated two distinct estimands — **in-beam component coverage** (already
107/2040, published) and **exact recovery of the selected candidate under causal intervention**
(`component_exact_loss`) — and that moving between them is illegitimate. v2's A2-S7 therefore states
only that the *question* of whether the intervention floor is genuine remains **open and untested**,
and routes it to `hypothesis_tree.md` as a C0002 candidate. C0001 tests neither and must not imply
that it has.

---

## 17. Required reviews before the full experiment

Per the `experiment-preregistration` skill, all three reviews must be **re-run against v2** before
Stage 7, each by an agent distinct from the implementer. **The Stage-3 reviews of v1 do not carry
over**: v2 changed the primary endpoint, the cascade, the compute basis and Part C's discriminator.

| review | agent | must confirm, specifically for v2 |
|---|---|---|
| **methodology** | `lansr-research-methodologist` | that E0/E1'/E2/E3 remain mutually discriminating as re-operationalized; that the H/L stratum definitions are decidable and non-degenerate; that the gain endpoint is the right operationalization of E0; that Part C's restriction to the in-support subset is correct; that cutting M2 and Part D does not remove a needed discrimination |
| **statistical** | `lansr-statistical-reviewer` | the three-level unit hierarchy and the aggregation order; the cluster-bootstrap specification and its seed; the ICC conditional and its zero-count degeneracy; the realized-`\|H\|` ladder and its OC/power tables; the §9.4 replacement for Holm; the §9.5 equivalence wording; the Part C discriminator's thresholds and disclosed dead zone; that no endpoint uses `student_t_ci` for a proportion |
| **reproducibility** | `lansr-reproducibility-auditor` | the §2.4 allowlist, instrumented opener and computed `sealed_paths_read`; that no `run_manifest.py` call receives a directory; the pinned M3 key; process-based parallelism and the worker-timeout assertion; the §7.5 failure taxonomy covering **every** silent non-match surface; the §7.2 write-before-match ordering; the §11.1 calibration's outcome-suppression constraint; the corrected commit and run ID; that `teacher_forcing_loss` is **extended, not modified** |

**Stage 9 independent review is additionally instructed** to check that: no artifact presents the
component-type stratification of the 107 as anything other than a **new reduction of GPU_RUN5's own
published field** (R1); no artifact presents 107/2040 as a C0001 discovery or as a matcher defect;
no artifact reads a zero primary as an equivalence claim; and no artifact cites a Part A or Part C
secondary as confirmatory. Any such framing is a **MAJOR** finding.

---

## 18. What was cut, and the one reviewer amendment declined

### 18.1 Cut: the M2 arm and A-S1 (declined amendment)

**Declined**: the reviewers' amendment to fix `SYMPY_MAX_NODES` by raising it to ≥ 200 and retaining
M2/A-S1 as an endpoint.

**Reason (rule 06).** `SYMPY_MAX_NODES = 40` is a **combined** truth+candidate budget, and
`src/gpu_run4/formulas.py:434` returns `0.0, None` above it with **no** failure reason. Measured:
the CAS path answers "does this GRN truth equal **itself**?" with *no* for **52/80** systems, and
**55.1%** of 3,000 real pairs exceed the cap, with R06/R07/R08 at **100%** (Q4, Q5). This is
conservative for a recovery score and **anti-conservative for a null-shaped claim**, and it is
invisible to v1's N5 failure budget and to its monotonicity check, because a spuriously empty M2 is
monotonicity-*consistent*. So M2 as v1 froze it is unusable. Fixing it, however, pushes R05–R08 into
full `simplify()` on 40–90-node trees at up to 10 s each: the auditor's projection is ≈**66
core-hours** against a **24 core-hour** ceiling — a rule-06 hard stop requiring human approval,
which this cycle will not request for a **secondary** endpoint.

**Consequence, stated as the rules require.** M2 and A-S1 are **cut, not downgraded**: no M2
endpoint exists in v2, so no M2 result — confirmatory, descriptive or exploratory — can be reported,
and none can invalidate a GPU_RUN5 result. This is strictly stronger than the "label it
`exploratory`" remedy a decline would otherwise require. Two substitutes preserve what M2 was for:
(a) the primary already uses **M3**, the most permissive level, which has **no node cap** and was
independently verified sensitive (PC2a 80/80) and specific (PC3a 48/48) on this corpus — so the
adversarially correct level is retained; (b) **PC0-CAS** runs `_sympy_components_equal(truth, truth)`
on all 80 systems with the cap raised to 200, at a bounded 0.22 core-h, and **reports** whether the
repository's CAS path can recognize a GRN truth as itself. That measured instrument fact is a
deliverable of this cycle and belongs in `research_state.md` §8 defect 8 regardless of what Part A
concludes.

The substance of AUDIT-CRIT-3's requirement is met in full for every path v2 actually runs: explicit
`failure_reason` on every non-match, `proved_different` separated from `could_not_evaluate`, and the
failure rate as a **reported endpoint with a pre-specified 2.0% maximum** above which the result is
`undecidable` (§7.5).

### 18.2 Cut: Part D

v1's Part D (denominator-arity classification of the 1,860 ODEBench variable-denominator candidates)
is **cut**. It bears on no C0001 endpoint, sharpens a C0002 question rather than this cycle's, and a
cycle that answers one question cleanly beats parts that each answer nothing. Routed to
`hypothesis_tree.md` as a C0002 candidate. No compute is reallocated to it.

### 18.3 Not cut, but demoted to `descriptive`

v1's primary (the system-level M3 `ANY` rate) is retained as **A2-S3** because it is a free
deterministic roll-up of indicators the primary already computes. It carries **no** confirmatory
claim, cannot invalidate a GPU_RUN5 result, and must be reported with the STAT-C1 power analysis,
the §9.2 clustering caveat and the frozen non-comparability sentence of §2.1.

### 18.4 Amendments accepted in full

Every other required amendment from both reviews is accepted: STAT-C1 (new component-stratified
confirmatory endpoint, §7.1–7.3), STAT-C2 (population, two intervals, ICC conditional, §2.2/§9.2),
STAT-C3 (payload digest, §8.2 step 1), STAT-C4 (paired discriminator, §8.3), STAT-M1…M13,
STAT-m1…m9, AUDIT-CRIT-1 (§7.6), AUDIT-CRIT-2 (§0.1, §5 item 1, R1), AUDIT-CRIT-3 (§7.5 + §18.1),
AUDIT-CRIT-4 (PC0, §7.7), AUDIT-MAJ-1…MAJ-9 and AUDIT-MIN-1…MIN-11. The commutation-orbit
mitigation (STAT-M9) is accepted **conditionally**, gated on the Stage-6 measured cost (§8.2 step 5);
if the gate fails, the bias remains disclosed with its magnitude and no decision depends on it.

---

## 19. Compact statement of what is frozen

primary hypothesis **H-C0001-P** · the single primary endpoint
**`hill_component_matcher_attributable_gain_rate`** over the frozen Hill stratum, with the
family-clustered bootstrap interval as the interval of record · the **H/L stratum definitions** and
the requirement that the strata and the realized-`|H|` ladder be **written and hashed before any
match indicator is computed** · the **§7.3 frozen predictions**, recorded before the stratification
of the 107 was looked at · the **M0 / M1 / M3** cascade, with M3 pinned to
`symbolic_recovery(...)["skeleton"]` and both sides fed the **infix** · the exclusion of M2 · the
three-level unit hierarchy and the within-component-then-across-components aggregation order · the
`ANY` reduction and its non-comparability sentence · the target population and the ICC conditional ·
the cluster bootstrap (10,000 resamples, seed 20260909) · the outcome ladder `0 / 1…ceil(0.02·|H|) /
>ceil(0.02·|H|)` with its OC and power tables · the control battery **PC0, PC0-CAS, PC1, PC2a–d,
PC3a–b** and its thresholds and eligible sets · the failure taxonomy and the **2.0%
`could_not_evaluate` maximum** · the §7.6 exact-reproduction gate over all 47,987 candidates ·
Part B's rewrite set B-R1…B-R4, its 200-rewrite cap and the `U_min ≤ 3` criterion · Part C's
restriction to the in-support subset, the **summed-log-prob-only** policy, the **paired
Stahlberg–Byrne discriminator** and its 0.5 thresholds, the `cell_input_payload_sha256` identity
protocol, the `|` ↔ `,|,` normalization and the 10%/10% re-encoding tolerances · the Part C
null-credibility conditions NC1–NC5 · the §9.5 equivalence wording · the Go/No-Go gates · the
supported / unsupported / refuted / undecidable / underpowered criteria · the exclusion and failure
policy · seeds (global 20260909; `numeric_equivalent(seed=0)` in Part B only; the primary matcher is
deterministic) · zero training, zero tuning, zero adaptation, zero new decoding · the compute
ceiling (4 GPU-h, 5.5 GiB VRAM, 24 CPU-core-h, 15 GiB disk) and the **measured** 12 core-h Part A
allocation · the §11.1 calibration and its outcome-suppression constraint · the crash-loop rule ·
the run ID rule · the artifact list · the replication design · the sealed-test firewall and its
file-level allowlist.

**Signed off (Stage 3, re-freeze)**: cycle `C0001`, preregistration **v2**, branch
`20260909_researce_GPU_RUNclaude1`, commit `de894b4`, 2026-09-09.
**v1 (`C0001_preregistration.md`) was not modified by this re-freeze.**
