# C0002 — Preregistration **v2** (DRAFT — NOT FROZEN)

| field | value |
|---|---|
| cycle | `C0002` |
| stage | 3 (design, revision 2) |
| status | **`DRAFT_PENDING_SUPERVISOR_CHECK`** — this document freezes nothing. It becomes binding only when the supervisor has checked that the two independent reviews of v1 are discharged and marks it `FROZEN`. |
| supersedes | `plans/C0002_preregistration_v1.md` + `.json`, status `DRAFT_PENDING_REVIEW` |
| v1 disposition | **v1 is retained unedited as the historical record.** It is not amended, not annotated and not deleted. Every line of it stands as the document the two reviewers reviewed. |
| author role | `lansr-research-methodologist` (drafting only). The author of v1 is the author of v2; **the two reviewers were independent of the author and of each other.** |
| reviews addressed | `reviews/C0002_preregistration_statistical_review.md` (7 CRITICAL, 13 MAJOR, 5 MINOR) and `reviews/C0002_preregistration_reproducibility_audit.md` (3 CRITICAL, 14 MAJOR, 8 MINOR). Disposition of **every** CRITICAL and MAJOR is in **§23**. |
| branch | `20260909_researce_GPU_RUNclaude1` |
| language | English, per `.claude/rules/15-document-language.md` (frozen contracts stay English; subagents reference field and endpoint names) |
| sealed test consumed | **NONE** |
| training performed | **NONE** |
| adaptation performed | **NONE** |
| layer estimands measured | **NONE** (rule 04, §17) |

> **This document does not edit, amend or supersede any C0001 artifact.**
> `plans/C0001_preregistration_v2.1.md` remains the frozen contract of record for C0001, and C0001's
> verdict of record remains **`undecidable`**. Nothing here changes it.

---

## 0.0 What a supervisor must read before deciding whether to freeze this

Three consequences of the revision change what this cycle can conclude. They are stated here, before
anything else, because two of them **narrow the cycle's reach** and one of them was established by a
measurement taken for this revision.

1. **A supported E2 is not available in C0002, and this is now known before any compute is spent.**
   BA2 — the only audit of the length confound that is D19-1331's own central finding — requires
   length-matched comparison partners. Measured before freeze with the real model tokenizer over the
   full 960-cell corpus, all 47,987 candidates, **zero tokenizer failures** (**M1**, §0.7): at the
   frozen minimum of 3 in-window partners the availability is **0.4625**, against BA2's own `< 0.5`
   cutoff. **No admissible partner floor clears that cutoff** — `k = 2` gives **0.4990** and `k = 1`
   is forbidden by this contract's own §5.1 — so the conclusion does not depend on where the floor
   was put. BA2 therefore returns `length_control_not_measurable`, and in v2 that **blocks** a
   supported E2 instead of merely being reported (§8.5, §13).
   The underlying reason is structural, not a matter of estimator choice: on **0.6302** of cells the
   ground truth is token-longer than **every** candidate in its cell (median GT length **48** against
   a median per-cell maximum candidate length of **38.5**), so no in-corpus length control —
   window-matched, length-adjusted or otherwise — can cover this corpus. **No threshold was moved to
   reach this conclusion; it is the consequence of not moving one.**
2. **`H0001-R` reports two independent certified lower bounds, not one attribution.** E2 and E3 are
   not mutually exclusive propositions; the supervisor has already retracted the exclusivity premise
   in `hypotheses/C0002_selection.md`. v1's single-attribution framing was an estimand error, and
   v1 §13's "upper bound of P1 < 0.5" read a one-sided bound in the direction where it carries no
   information. Both are removed (§13).
3. **Gate 4's `C_gen` reconstruction condition is predicted to fail at its own frozen bar.** Re-expressed
   as the real tokenizer round trip that the audit requires, it measures **0.9683** in `C_gen`
   against `≥ 0.98` (**M5**, §0.7). The frozen consequence (§18's named contingency) is that `C_raw`
   becomes primary — which **collapses the §0.3 containment argument**, because `C_raw` is the context
   under which `lp_gt` was already observed on all 960 cells and under which the 8-cell `sb_best`
   exposure occurred. This is a decision for the supervisor, laid out in §7.3.

**Disposition counts (§23):** **10 CRITICAL — 10 FIXED.** **27 MAJOR — 25 FIXED, 2 FIXED IN PART with
an accepted limitation and its consequence stated.** **13 MINOR — 12 FIXED, 1 ACCEPTED.**
**Nothing is silently dropped, and no finding was resolved by moving a threshold.**

---

## 0. Prior information disclosed before freeze (rule 01 item 9)

### 0.1 Published GPU_RUN5 / C0001 values that are comparators, not findings (rule R1)

Unchanged from v1 §0.1 except where a measurement in §0.7 has since corrected or established a value.

| quantity | value | source |
|---|---|---|
| stored GRN candidates | **47,987**, `valid: true` on **47,987 / 47,987**, 0 cell failures | `results/runs/gpu_run5_20260823_ddd267b0/phase3/summary.json:"n_candidates"`; re-verified by direct count over `phase3/cells/*.json` |
| cells | **960** = 80 systems × 12 conditions (3 bundles × 2 `noise_sigma` × 2 `subsample_rho`) | `phase3/cells/` (960 files) |
| truth-in-beam | **0 / 960** | C0001 report §1 |
| unique skeletons per beam | 9.28 mean at `beam_size = 50`, `beam_temperature = 0.1` | C0001 report |
| Part B in-support systems | **`n_in_support = 71`** of 80; 9 / 170 components out of support, all H, all `component_index = 2`, families R07 (6) and R08 (3), **`uses_only_in_support_operators` True on all 9** | `results/runs/gpu_runclaude1_c0001_b731cdd/phase2/partB_in_support_systems.json`; C0001 report §7.3 |
| Part A gains | `k_gains = 0` on all 130 H and all 40 L components | `GPU_RUNclaude1/derived/C0001/partA_component_summary.derived.json` |
| realized candidate skeleton classes | **846**; component strings **89,349**; constant-folded classes **879** → **877** under frozen M3; class pairs **2,191**; component comparisons **101,963** | `replications/C0001_opportunity_census_replication.md:121-123, :141-144, :182-183, :449`. **The 89,349 figure is no longer prose-only — it is reproduced exactly by M2 (§0.5, §0.7).** |
| Hill-4 candidate skeleton classes on the infix path | **11 classes / 308 comparisons, none with a denominator** | C0001 report / design brief §4.1 |
| S1 `phi_denom` | passes **5,824 / 77,983** H triples, **88 / 130** H components | `replications/C0001_opportunity_census_replication.md:167` |
| `equals_NONE` over the realized 2,191 class pairs | **exactly 0** | ibid. `:362` |
| `could_not_evaluate` label instability | **14 / 101,963** labels flip in both directions on identical inputs; recorded run 9 vs replication 7, 1 in common; **the M3 value itself agreed on all 101,963 comparisons** | ibid. §6.2 |

### 0.2 MAJOR-R3 — `lp_gt` was already computed and observed for all 960 cells

Unchanged from v1 §0.2. `results/runs/gpu_runclaude1_c0001_b731cdd/phase3/partC_cell_records.jsonl`
holds **960** rows with exactly the keys
`cell_id, excluded, cell_input_payload_sha256, gt_logprob_sum, gt_token_length`;
`min = -846.0560302734375`, `max = -115.8770751953125`, `median = -297.5801086425781`.
No comparison partner was computed in C0001: `partC_endpoints.json`, `partC_reencoding_audit.json`
and `partC_identity_audit.json` do not exist there, and no row carries `lp_sel`, `lp_best`, `sb_sel`
or `sb_best`.

**Binding consequence, inherited from MAJOR-R3 and unchanged:** every E2/E3 endpoint in this contract
is paired or comparison-based. **No absolute threshold on `lp_gt` bears any decision anywhere in this
document.**

**New in v2 (M4, §0.7):** the pre-freeze NC-CONDITION probe recomputed `lp_gt` under `C_raw` with
matched conditioning on 200 cells and **reproduced the stored `gt_logprob_sum` exactly on 200 / 200**.
That is a positive control on the scorer and consumed no new information: those values were already
on record.

### 0.3 SELF-REPORTED DISCLOSURE — the drafting agent observed the primary indicator on 8 cells

**Retained verbatim from v1 §0.3**, including the table of 8 cells, because a disclosure may not be
softened in a revision. The containment claims, however, are corrected below — v1's claim 1 was
overbroad and the statistical review was right to say so (MAJOR-10 SR).

On 2026-09-11, while measuring GPU throughput, the drafting agent ran
`teacher_forced_summed_logprob_batch` on **8 cells** drawn with `random.seed(999)` from the 960 stored
cells, under the **`C_raw`** scoring context, and **printed `lp_gt`, `lp_best` and `sb_best`**:

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

Separately, on a **disjoint** 10-cell sample (`random.seed(4242)`), `lp_best` and
`lp_greedy − lp_best` were observed for PC-GREEDY; `lp_gt` was **not** computed there.

**Containment measures — v1's claim 1 is CORRECTED here, not repeated.**

1. **Per-threshold derivation, replacing v1's blanket claim.** v1 §0.3 item 1 asserted that *no*
   threshold in the document was chosen after or in light of these values. That claim was true only
   of the rules inherited verbatim from v2.1 §8.3. §0.9 below is the per-threshold table the
   statistical review required, distinguishing **inherited** (frozen 2026-09-09, two days before the
   observation), **derived** (from a stated principle, recorded here) and **new-without-derivation**
   (disclosed as such).
2. **The primary scoring context is `C_gen` (§7.1).** Both the C0001 exposure (§0.2) and the 8-cell
   exposure are under `C_raw`. **v1's framing "the primary quantity has never been observed" is
   withdrawn** and replaced with the accurate one: *the primary quantity was not directly computed;
   the `C_raw` proxy was, on 8 of 960 cells, in the E2 direction, with `lp_gt − lp_best` gaps of
   100–500 nats, so `sb_best` is very likely to agree across contexts on those 8 cells.*
   **§7.3 further records that if Gate 4's `C_gen` condition fails as M5 predicts, `C_raw` becomes
   primary and this containment is gone entirely.**
3. **The 8 cells are not excluded.** Excluding them would be a post-hoc, outcome-dependent exclusion
   (rule 01 item 3). They stay in the corpus and are listed above so that any influence is auditable.
   Under v2's §4 all 80 systems are in the corpus, so all 8 are in, and the v1 caveat about checking
   two of them against `partB_in_support_systems.json` no longer applies to the primary denominator.
4. **The direction observed (`sb_best = 0`, i.e. E2) is the campaign's preferred answer.** In v1 this
   made the §8.5 battery "the scientific content of the cycle"; the statistical review showed that
   the battery as drafted could not police that direction at all. **§8.5 in v2 gives BA1, BA2 and
   BA3 blocking consequences**, which is the change that makes the disclosure meaningful rather than
   decorative.
5. **§7.1's disclosure of a post-observation design choice.** v1 §7.1 stated that `C_gen` was made
   primary partly *because* the exposure was under `C_raw`, while "which context is primary" is on
   the §2.5 frozen list. That is a frozen design element chosen in light of an observation. It is
   **disclosed, not defended as containment**: the choice is independently justified by the F-g
   conditioning argument, and that argument alone is what v2 rests it on.

### 0.4 Deliberately not looked at before freeze — and what the v2 measurements did and did not touch

Still not looked at, as of this draft:

- Any value of `lp_best`, `sb_best`, `me_best`, `lp_gt_max` or `lp_gt_lse` under the **`C_gen`**
  context.
- The realized class-level counts of the three `H0010` predicates `P_den`, `P_pow4`, `P_joint` on the
  realized candidate classes. **M2 deliberately computed the parse and `sympy.count_ops` only, and
  called neither `together`, nor `cancel`, nor `fraction`** — the predicate values were not computed,
  not in memory and not on disk.
- The value of `sb_best_len` (BA2's indicator) on any cell. M1 measured **token lengths only**.
- Any sealed artifact (§2.4).

Newly looked at for v2, all disclosed in §0.7:

- Model-tokenizer **token lengths** of the ground truth and of all 47,987 candidates (M1). Leak-free:
  no log-probability is a function of a token length alone, and `gt_token_length` was already on
  record for all 960 cells (§0.2).
- `sympy.count_ops` of the 89,349 distinct component strings (M2).
- `lp_gt` under `C_raw` with **matched** conditioning (already on record, §0.2) and with a
  **mismatched** different-system conditioning, on 200 cells (M4). The mismatched score is not an
  endpoint of this contract in either context and no candidate was scored, so no `lp_best`, `sb_best`
  or `me_best` value was produced.
- Encoder token sequences and encode→decode→encode identity in both contexts (M5). No
  log-probability.

### 0.5 The C0001 skeleton-class numbers — the corpus size is now REPRODUCED, the class counts are not

v1 §0.5 recorded that 846 / 89,349 / 879 / 877 / 2,191 existed only as prose plus a session-scoped
scratchpad, and entered v1 as **unreproduced prior**.

**M2 (§0.7) reproduces one of them end to end from the durable artifact.** Over
`phase3/all_candidates.json` (SHA256 `451e66ec14238335f646c1237e7b32062c681b85b08b8ea8abc20a883488a07a`,
181,594,403 bytes), the union of distinct candidate component strings and distinct truth component
strings across all 80 systems is **89,349** — the prose value, exactly. Breakdown:
distinct candidate components **89,179**, distinct truth components **170**, union **89,349**.
Restricted to the 71 in-support systems the same quantities are **73,974 / 143 / 74,117**.

The **class** counts (846 realized, 879 / 877 constant-folded, 2,191 class pairs) are still
unreproduced: reproducing them requires the class key, which is part of `H0010`'s own pipeline.
They therefore remain **unreproduced prior**, and §9.2's gating census (Gate 2) still regenerates
them before the endpoint, exactly as v1 required.

### 0.6 Instrument facts

F-a … F-h are carried forward **unchanged** from v1 §0.6 and are not restated here; they are binding
by reference to `plans/C0002_preregistration_v1.md` §0.6, which is retained unedited. In summary:
F-a module-level unseeded `sympy.core.random.rng`; F-b `bool(a.equals(b))` at
`equation_metrics.py:65` collapsing the three-valued return; F-c `_time_limit` running unguarded when
`seconds <= 0`, without `SIGALRM`, or off the main thread; F-d `use_two_hot = False`, so constants are
ordinary vocabulary tokens; F-e no per-candidate model score anywhere in `phase3/` (24-key schema);
F-f `candidate_index == 0` is the highest-input-R² candidate, not a decoder argmax and not a sample
index; F-g the generation conditioning is not the scoring conditioning; F-h the decoder's emitted
token sequence is unrecoverable from the stored artifacts.

**New instrument facts established for v2.** Each constrains the design and each is a direct result
of a review finding.

| # | fact | evidence |
|---|---|---|
| **F-i** | **`lp_gt` as a logsumexp is not a single-sequence score, so it cannot carry the Stahlberg–Byrne certificate.** `L* ≥ log Σ_e P(e)` does **not** follow from `L* = max_y log P(y|x)`. `K` sequences each at `log P(b) − 1` sum to `log P(b) − 1 + log K > log P(b)` for `K ≥ 3` while no member beats `b`. The `G < B` direction is unharmed and in fact strengthened, since `logsumexp ≥ max`. | both reviews, independently; CRITICAL-1 SR and CRITICAL-1 RA |
| **F-j** | **In `C_gen`, `e1` and `e2` collapse onto the same token sequence.** The stored `tree_encoded` is in **original** units; scoring it in `C_gen` requires decode → forward map → re-encode, which is exactly `e2`'s path. Measured (M5): `e1` and `e2` are **identical on 120 / 120** cells in `C_gen`. In `C_raw`, where the stored token list can be scored as stored, they are **distinct on 80 / 80** systems (token lengths e.g. 25 vs 24, 27 vs 30, 29 vs 30, 19 vs 18, 39 vs 37, 34 vs 30, 51 vs 49, 59 vs 56, 68 vs 62, 51 vs 44). | M5, §0.7. Predicted by MAJOR-10 RA |
| **F-k** | **The encoder's 4-significant-digit constant quantization is lossless on original-unit GRN constants and lossy on scaled ones.** GRN truths carry 4-significant-digit decimal constants (`0.1954`, `0.8878`, `0.8392`, `0.3968`), which encode exactly; `C_gen` constants are arbitrary reals. Measured numeric round trip (M5): `C_raw` max relative error **0.0** on 120 / 120; `C_gen` accurate to `rtol = 1e-3` on **0.275** of cells, median relative error **2.03e-3**, p90 **1.30e-2**, max **1.05e-1**. | M5, §0.7. `env.params.float_precision = 3`, `float_descriptor_length = 3`; `odeformer/envs/encoders.py:124` |
| **F-l** | **`sympy.count_ops` never binds on this corpus.** Over all 89,349 distinct component strings the maximum `count_ops` is **14**, median **3**, p99 **9**; `CAS_NODE_BUDGET = 400` excludes **0** rows. The parse itself costs 0.001458 s per string, 130.27 s (0.0362 core-h) for the whole corpus. | M2, §0.7 |
| **F-m** | **The three bundles of a system at `noise_sigma = 0, subsample_rho = 0` share one conditioning payload, so `lp_gt` is byte-identical across them.** `cell_input_payload_sha256` takes exactly **10** distinct values per system on all **80** systems; 240 of the 960 across-bundle same-corruption pairs have `|Δ| = 0` **exactly**, and they are exactly the `n0_r0` ones. At the other three corruption settings the median `|Δ|` is 0.9730 / 4.0100 / 4.3333 nats and the fraction exceeding 1 nat is 0.4917 / 0.8292 / 0.8625. | direct recount of `partC_cell_records.jsonl`. Predicted by MAJOR-7 RA |

**F-m retracts v1 §10.3's stated achievability evidence for NC-CONDITION.** v1 cited
`-159.50254821777344 / -160.61439514160156 / -158.15951538085938` on `R01_validation_d101_000` as
differing "between bundles of the same system". They do not: all three are **bundle 0**, differing in
`noise_sigma` / `subsample_rho`. The genuine across-bundle triple at fixed corruption is
`R01_validation_d101_000_b{0,1,2}_n0_r0` = **`-159.50254821777344`** three times, byte-identical.
The v1 citation is withdrawn; §10.3 in v2 cites M4 instead.

### 0.7 Pre-freeze measurements taken for v2

Both reviews required that every gating control carry a measured, achievable expected value, and both
identified specific quantities as leak-free and measurable before freeze. These were measured.
**Every one of them is recorded here with its realized value, including the ones that fail their
own bar.** Scripts and raw outputs are in the session scratchpad and are reproduced by the commands
in §0.8.

Environment: `source /home/blabo/miniconda3/etc/profile.d/conda.sh && conda activate lansr310`,
`sympy 1.13.1`, checkpoint SHA256 `56754040be5aa92ed4767fc43ee2008faa293f87c12b643e66c7df3e1623a5e8`.
No sealed path was opened. No C0001 artifact and nothing under `results/runs/` was modified.

**M1 — BA2 length-matched-partner availability, real model tokenizer, full corpus.**
`infix_to_model_tokens(env, candidate_formula_raw)` on **all 47,987 candidates** of **all 960 cells**;
ground-truth lengths from `partC_cell_records.jsonl`'s `gt_token_length`; window `±round(0.20·len_gt)`.
**Zero tokenizer failures.** 212.5 s CPU.

| quantity | value |
|---|---|
| cells with ≥ 1 in-window partner | **0.5844** (561 / 960) |
| cells with ≥ 2 | **0.4990** (479 / 960) |
| cells with ≥ 3 — **the frozen floor** | **0.4625** (444 / 960) |
| cells with ≥ 5 | 0.4052 (389 / 960) |
| median in-window partner count | **1** |
| mean in-window partner count | 10.024 |
| mean per-cell fraction of candidates in window | 0.2006 |
| **cells where the GT is longer than every candidate** | **0.6302** |
| cells where the GT length lies inside `[min, max]` of candidate lengths | 0.3698 |
| cells with ≥ 3 distinct candidate token lengths | 0.7583 |
| median GT token length / median per-cell maximum candidate length | **48** / **38.5** |
| systems (of 80) with no cell reaching the floor of 3 | **20** |
| systems with ≥ 8 of their 12 cells reaching the floor of 3 | **33 / 80** |

**M2 — `H0010` corpus size and `count_ops` census.** Parse + `sympy.count_ops` over the distinct
component strings of `phase3/all_candidates.json`. **`together` / `cancel` / `fraction` were not
called and no predicate was evaluated** (§0.4).

| quantity | value |
|---|---|
| distinct candidate component strings, 80 systems / 71 in-support | **89,179** / 73,974 |
| distinct truth component strings, 80 / 71 | **170** / 143 |
| **union, 80 systems** | **89,349** — reproduces the C0001 prose value exactly |
| union, 71 in-support | 74,117 |
| parse failures | **0 / 89,349** |
| `count_ops` min / median / mean / p99 / **max** | 0 / 3 / 3.967 / 9 / **14** |
| rows exceeding `CAS_NODE_BUDGET = 400` | **0** |
| parse + `count_ops` wall time | **130.27 s** = 0.001458 s/string = **0.0362 CPU core-h** |

**M3 — operating characteristics of the candidate intervals of record.** Simulation, systems iid
Bernoulli(p) within the 8 fixed families; 500 replications, B = 600 for coverage; 10,000 resamples for
widths; `default_rng(20260912)` / `default_rng(20260911)`. Run at both corpus sizes.

Coverage against nominal 0.95, **80 systems in 8 fixed families of 10** (the v2 corpus):

| true p | v1's cluster bootstrap over 8 families | stratified within fixed families | Wilson(80) | **v2 rule (conservative of the two)** |
|---|---|---|---|---|
| 0.20 | 0.908 | 0.940 | 0.956 | **0.960** |
| 0.35 | 0.904 | 0.940 | 0.956 | **0.958** |
| 0.50 | 0.910 | 0.938 | 0.938 | **0.942** |
| 0.65 | 0.916 | 0.956 | 0.958 | **0.964** |
| 0.80 | 0.922 | 0.952 | 0.966 | **0.968** |

Coverage at **71 systems in families of (10,10,10,10,10,10,4,7)** — v1's unbalanced corpus, which v2
abandons (§4) — is worse for v1's estimator and independently reproduces the statistical review's
finding: **0.884 / 0.876-equivalent band 0.884–0.916** for the cluster bootstrap against
0.936–0.982 for the v2 rule.

The diagnostic the statistical review reported is reproduced directly. On a corpus where every family
has the same rate (the homogeneous case, 71 systems, `p̂ = 0.5070`), v1's cluster bootstrap returns
**[0.5000, 0.5231], width 0.0231**, against the stratified **[0.3944, 0.6197], width 0.2254** — an
interval **~10× narrower than the unclustered comparator, with its lower bound sitting exactly on the
0.5 cutpoint.** A "clustered" interval narrower than its unclustered counterpart is diagnostic of the
wrong resampling unit.

Minimum point estimate at which a one-sided 95% lower bound can exceed 0.5 under the **v2** interval:
**48 / 80 = 0.600** (Wilson component; the stratified component can require more).

**M4 — NC-CONDITION under a different-system partner.** 200 cells, `CONTROL_CELL_SEED = 20260911`,
`C_raw`, GPU 0, 10.9 s.

| quantity | value |
|---|---|
| stored `gt_logprob_sum` reproduced exactly (matched conditioning) | **200 / 200** |
| fraction with `\|Δ\| > 1` nat under a different-system partner | **0.95** |
| fraction with `\|Δ\| > 10` nat | 0.59 |
| min / median / max `\|Δ\|` | 0.009063720703125 / **13.080673217773438** / 123.88052368164062 |
| exactly-zero `\|Δ\|` | **0** |
| `P(≥ 38 of 40 \| p = 0.95)`, i.e. the Gate-4 pass probability | **0.6767** |

The same-system case is the one F-m rules out: 240 of the 960 across-bundle same-corruption pairs have
`|Δ| = 0` exactly.

**M5 — `C_gen` achievability for Gate 3b and Gate 4.** 120 cells, `seed = 20260911`, CPU. A first
attempt at this probe returned 0.0 on two rates; that was a **defect in the probe** (its `e1` path used
`parse_prefix_component`'s tuple tree as if it were sympifiable, and its numeric evaluator raised),
**not a finding**, and its zeros are not reported anywhere. The corrected probe carries its own
`C_raw` control, which is the check that the probe measures what it claims (rule R5).

| quantity | `C_gen` | `C_raw` control |
|---|---|---|
| `e1` encodable | 1.000 | 1.000 |
| `e2` encodable | 1.000 | 1.000 |
| **`e1` and `e2` distinct token sequences** | **0.000 (0 / 120)** | **1.000 (80 / 80 systems)** |
| encode → decode numeric agreement at `rtol = 1e-3` | **0.275** | **1.000** |
| numeric round-trip relative error, median / p90 / max | `0.002028412819124974` / `0.012986786773734979` / `0.10482806200821848` | **`0.0` / `0.0` / `0.0`** |
| encode → decode → encode **token identity**, ground truth | **1.000 (120 / 120)** | 1.000 (120 / 120) |
| encode → decode → encode **token identity**, candidates | **0.9683 (581 / 600)** | 0.9917 (595 / 600) |

The 5 / 600 candidate failures in the lossless `C_raw` control bound how much of the `C_gen` shortfall
is attributable to the probe rather than to quantization: the quantization-attributable excess is
≈ 14 / 600 = 2.3 pp. The absolute rates are labelled **probe-measured**; the **differential**
(−0.0234) is the robust part.

**M6 — the regression identity, recounted.** `phase3/partC_instrument_test.json`, 960
`regression_checks`, `tolerance: 1e-05`, top-level `ok: true`, **0 rows over tolerance**.
`identity_error` min **`0.0`** (17 entries exactly zero), smallest non-zero
**`1.2226593959496768e-08`**, max **`2.8991699210223487e-06`**. v1 §10.5's quoted range
`7.3e-08 … 8.1e-07` is **wrong at both ends** and is corrected here; the realized margin to the
`1e-5` bar is **3.45×**, not the ~12× v1 implied.

**M7 — input artifact digests**, recorded so that §3 pins inputs by hash and not by path.

| artifact | bytes | SHA256 |
|---|---|---|
| `assets/odeformer/weights/odeformer.pt` | 464,822,385 | `56754040be5aa92ed4767fc43ee2008faa293f87c12b643e66c7df3e1623a5e8` |
| `.../gpu_run5_20260823_ddd267b0/phase2/validation.json` | 7,679,547 | `f4644d1d4c30f8a3d6f0cafc8f321fb2c07e72979d8e4c42d28862376abb8f64` |
| `.../gpu_run5_20260823_ddd267b0/phase3/all_candidates.json` | 181,594,403 | `451e66ec14238335f646c1237e7b32062c681b85b08b8ea8abc20a883488a07a` |
| `.../gpu_runclaude1_c0001_b731cdd/phase2/partB_in_support_systems.json` | 2,247 | `a8a82d4b98e3974304092ecde7d0bb069a35bef5c75d2abe22b287c8242dfd33` |
| `.../gpu_runclaude1_c0001_b731cdd/phase3/partC_cell_records.jsonl` | 218,464 | `5368c790167bd78229269da73380eace66169dc64add22d27c08ddec7e5f7077` |
| `.../gpu_runclaude1_c0001_b731cdd/phase3/partC_instrument_test.json` | 205,107 | `5c53ab753b7307dacb6353aa75e3cecad75d3433b5050e7490ddf95f2ea51bbc` |
| the 960 `phase3/cells/*.json`, rolled up | — | `cf4922e13b4be9ff5c782ac6227cd320e186f2c114602bea05aee3d5669f31f7` (SHA256 of the sorted per-file digest listing) |

**Measured but NOT verifiable before freeze, and declared as such:**

- **PC-GREEDY's rate under `C_gen`.** Measuring it requires computing `lp_best` under `C_gen`, which
  §0.4 forbids. Its 2 / 10 probe stands as a **`C_raw`** figure and is labelled
  `unverified_for_C_gen` wherever it appears. The abort risk is disclosed instead (§10.2, §0.9).
- **Gate 3b's achievability under `C_gen` from orbit members alone.** F-j removes `e1`/`e2` as a
  source of distinct encodings in `C_gen`; whether the commutation orbit supplies ≥ 2 verified
  distinct members on ≥ 90% of systems in `C_gen` was not measured. 3b is therefore a **downgrade
  condition only** (§11) and no decision rests on it.

### 0.8 Reproduction of the v2 measurements

| measurement | how |
|---|---|
| M1 | tokenize every `valid` candidate of every `phase3/cells/*.json` with `gpu_runclaude1.partc_reencoding.infix_to_model_tokens` against a CPU-loaded checkpoint; compare `len(tokens)` to `gt_token_length` from `partC_cell_records.jsonl` under `±round(0.20·len_gt)` |
| M2 | `gpu_run4.formulas.parse_system` over every `candidate_formula_raw` and `true_formula` in `phase3/all_candidates.json`; `sympy.sympify` + `sympy.count_ops` on the distinct component strings |
| M3 | simulation as described above; statistic `Σ_s indicator / n_eval`; percentile intervals; Wilson with `z = 1.959963985` two-sided, `z = 1.6448536` one-sided |
| M4 | `gpu_run4.training.teacher_forced_summed_logprob` with the cell's own `observations["input"][0]` and with a different in-support system's, against `validation.json`'s `tree_encoded` |
| M5 | `odeformer.model.utils_wrapper.Scaler(time_range=[1,10], feature_scale=1).fit_transform`, the §7.1 forward map, `env.simplifier.sympy_expr_to_tree` → `env.equation_encoder.encode` / `.decode` |
| M6 | direct recount of `phase3/partC_instrument_test.json` |
| M7 | `sha256sum` |

### 0.9 Per-threshold derivation table — replacing v1 §0.3's blanket containment claim

The statistical review's MAJOR-10 required this. Every threshold that bears on a decision is
classified. **`inherited`** = frozen in `plans/C0001_preregistration_v2.1.md` on 2026-09-09, two days
before the 8-cell observation, and therefore not reverse-engineerable from it. **`derived`** = follows
from a stated principle recorded in this document. **`new_no_derivation`** = disclosed as chosen
without a derivation, with the consequence stated.

| threshold | value | class | basis |
|---|---|---|---|
| system cutpoint in `E3_system` | `sb_rate(s) ≥ 0.5` | **inherited** | v2.1 §8.3 |
| corpus cutpoint in the decision rule | `0.5` | **inherited** | v2.1 §8.3 |
| `E2_system` definition | `me_rate(s) = 1` | **derived** | §8.3: `me_best` is the certificate whose name P2 carries (m-3 SR); the all-cells form is v2.1 §8.3's `sb_rate(s) = 0` re-expressed on the quantity that certifies it, and is **strictly harder to satisfy** than v1's form (§8.3 proof) |
| interval of record | conservative of stratified bootstrap and Wilson | **derived** | §12.1: matches §2.2's estimand; coverage measured in M3 |
| re-encoding mismatch caps | 10% per cell, 10% of cells | **inherited** | v2.1 §8.2 step 4 |
| `EncodingVerificationFailure` cap | ≤ 20% | **new_no_derivation** | disclosed. Consequence: §11 Gate 3c is **report-only** in v2, so no decision rests on it |
| `H0006` Gate 3a | 80 / 80 systems with ≥ 1 verified encoding | **derived** | a system with no verified encoding has no `lp_gt` at all, so 100% is the only admissible bar. Measured 80 / 80 (M5) |
| `H0006` Gate 3b | ≥ 90% of systems with ≥ 2 verified distinct encodings | **new_no_derivation** | disclosed. Consequence: 3b is a **downgrade condition, never a pass condition** (§11), and M5 shows it cannot be met from `e1`/`e2` in `C_gen` at all (F-j) |
| BA1 near-greedy bar | median `argmax_agreement_best` ≥ 0.95 | **new_no_derivation** | disclosed. In v2 it **blocks**, so the direction of the disclosure is conservative: an undermotivated bar now costs the campaign's preferred answer, it does not buy it |
| BA2 window | `±round(0.20 · len_gt)` | **new_no_derivation** | disclosed |
| BA2 availability cutoff | `< 0.5` ⇒ not measurable | **new_no_derivation** in v1, **unchanged in v2** | **not moved.** Measured **0.4625** at the frozen partner floor of 3, and **0.4990** at the lowest admissible floor of 2 — the cycle fails its own bar at every admissible floor (§0.0 item 1) |
| BA2 minimum in-window partners | **3** | **derived** | §8.5: §5.1 of this contract already forbids "an arbitrary member of the returned set" as a comparison partner, which rules out `k = 1`; `k = 2` makes the maximum the larger of a pair. `k = 3` is the smallest count at which a **majority** of the comparison set lies below its own maximum. Chosen from §5.1, **before** the availability curve was consulted, and **not revised** after 0.4625 was measured. The choice is not load-bearing: `k = 2`, the only other admissible value, also fails the 0.5 cutoff (0.4990) |
| BA2 disagreement bar | > 20% of contributing cells | **new_no_derivation** | disclosed |
| BA3 flip bar | `encoding_flip_rate > 0.05` | **new_no_derivation** | disclosed. In v2 it **blocks** |
| PC-GREEDY | ≥ 2 of 40 | **new_no_derivation** | disclosed, with the operating characteristic now stated: `P(X ≥ 2 | n = 40)` = 0.9985 at a true rate of 0.20, **0.6009** at 0.05, 0.1905 at 0.02 |
| PC-HOLDOUT / NC-HOLDOUT | ≥ 0.95 / ≤ 0.05 | **derived** | arithmetic on a strict maximum / minimum |
| NC-CONDITION | ≥ 0.95 of control cells with `|Δ| > 1` nat | **new_no_derivation**, **not moved** | measured population rate **0.95** (M4), i.e. exactly at the bar; `P(pass | 40 cells, p = 0.95)` = **0.6767** |
| `C_gen` reconstruction | ≥ 0.98 | **new_no_derivation**, **not moved** | measured **0.9683** in `C_gen` — does not clear (§7.3) |
| regression identity | < 1e-5 | **inherited** | v2.1 §8.2 step 3; measured max 2.8991699210223487e-06 |
| `CAS_NODE_BUDGET` | 400 | **new_no_derivation** | disclosed. Measured inert: max `count_ops` on the corpus is 14 (F-l), so it excludes 0 rows |
| `H0010` `n_class_den > 0` | > 0 | **derived**, relabelled | a **precondition**, not a prediction (§9.3) |
| `H0010` `n_class_pow4 ≥ 10` | ≥ 10 | **derived**, **relabelled as a verification condition** | C0001 published **11**, and `P_pow4` is a **superset** of that screen, so 11 is a lower bound and the bar passes by construction. It is not a prediction and v2 does not report it as one (MAJOR-6 SR) |
| `H0010` `n_class_joint ≤ 5` | **replaced** | — | v1's cutpoint had no derivation and, in a census, deterministically fixes the verdict. v2 replaces it with a **relative, graded** rule (§9.3) |

---

## 1. Frozen primary hypothesis, companion, and what may not be claimed

### 1.1 Primary — `H0001-R` (REWRITTEN; v1 §1.1 is withdrawn)

- **id**: `H0001-R`. `H0001` itself was **never measured**: C0001 Part C ran under a Gate B→C
  violation, the decision endpoint C2-P was never computed, and that `phase3/` is `INADMISSIBLE`.
  This is a first measurement, not a rerun.
- **type**: `two_independent_certified_lower_bounds`. **Not** `directional_confirmatory` and **not**
  an attribution.

**Why the v1 framing is withdrawn.** v1 stated the hypothesis as "the truth is below the best
candidate; **equivalently** the failure is prior mass (E2), **not search** (E3)". The word
"equivalently" is false, and the supervisor has retracted the underlying exclusivity premise in
`hypotheses/C0002_selection.md` (retraction dated 2026-09-12):

> **E2 and E3 are not mutually exclusive.** `sb_best = 1` yields `L* ≥ lp_gt_max > lp_best`, which
> leaves `L* > lp_gt_max` **entirely open** — a certified search error is compatible with the truth
> **also** not being the model's argmax. The per-cell indicators are exclusive only because they
> compare the same two numbers; the **propositions** are not.

This is an estimand error. No choice of interval repairs it. v2 therefore reports **two independent
certified lower bounds side by side** and makes no attribution.

**The two certificates, and exactly what each licenses.**
Let `L*` be the model's unknown global-best score for the cell under the scoring context,
`B = lp_best`, and `G_max = lp_gt_max` = the maximum over the verified admissible encodings of the
truth — **a single-sequence score** (§7.2). `B ≤ L*` holds for the maximum over any finite set of
complete sequences.

- **Certificate S (search error).** `G_max > B ⇒ L* ≥ G_max > B`: the returned set does not contain
  the global best. A search error is **certified** for that cell.
  `SOURCE`: Stahlberg & Byrne §2 p. 3357 and footnote 5 p. 3358, DOI **10.18653/v1/D19-1331**,
  https://aclanthology.org/D19-1331/ , applied to the returned set.
- **Certificate N (non-argmax).** `G_lse < B ⇒ L* ≥ B > G_lse ≥ G_max`: **every** verified spelling of
  the truth is below `b`, so the truth is **not** the model's argmax under this conditioning.
  Certified. `INFERENCE` from the same bound; `literature/C0002_literature.md` §Q2.3.

**F-i is why the two certificates use different quantities.** A logsumexp is not the log-probability
of any sequence, so `L* ≥ log Σ_e P(e)` does not hold and Certificate S **fails** on it. It holds on
`G_max`. Conversely `logsumexp ≥ max`, so Certificate N is **strengthened** by the logsumexp.
v2 therefore wires each certificate to the quantity that carries it — `sb_best` on `lp_gt_max`,
`me_best` on `lp_gt_lse` — at **zero additional compute**, since §7.2 computes both.

**What each certificate does NOT license, binding:**

- `sb_best = 0` certifies **nothing**. `lp_gt_max ≤ lp_best` is fully compatible with some unreturned
  sequence outscoring `lp_best`. **P1 is a certified LOWER bound on the search-error rate and
  C0002 cannot bound that rate from above.** No configuration of P1 supports an "and not search"
  claim, and v1 §13's condition "the 95% **upper** bound of P1 < 0.5" is **deleted** (§13).
- `me_best = 1` certifies that the truth is not the argmax. It does **not** establish that the truth
  has negligible mass, and it does **not** refute a search error.

- **falsifiable statement (rewritten)**: on the majority of GRN systems, the teacher-forced summed
  log-probability of **every verified spelling** of the ground truth is below the maximum such score
  over the model's own realized candidate set.
- **falsifier (unchanged in arithmetic, restated without "not search")**: `sb_best = 1` on at least
  half the usable cells of at least half the systems, with the one-sided 95% lower bound of **P1**
  above 0.5 (§13). That outcome certifies search error on a majority of systems and fires `H0003`
  (temperature / beam sweep) **on evidence**.

### 1.2 Companion — `H0010`

- **falsifiable statement**: among the realized candidate skeleton classes, the **joint** predicate
  (a cancelled denominator containing a variable **and** a numerator containing a variable that the
  denominator does not) is absent or near-absent **relative to its own realized marginals**.
- **falsifier**: §9.3's graded rule fires in the joint-present band. v1's bare
  `n_class_joint ≥ 6` cutpoint is **withdrawn**: it had no derivation and, in a census with no
  sampling variability, it deterministically fixes the verdict (MAJOR-6 SR).
- CPU only. Exhaustive classification, not a sample.

### 1.3 Novelty labels — frozen, none may be upgraded

Carried forward unchanged from v1 §1.3. `known` for teacher-forced scoring as a search-error
indicator (D19-1331); `adjacent` for `H0001-R` as an application (ND2, DOI 10.1038/s43588-025-00893-8),
for `H0010` (Sato & Sato arXiv 2505.22081 Def. 5.1; NeSymReS §4.4), for the `H0006` encoding audit
(Sato & Sato Remark 5.2; TSRM Fig. 7), and for the deterministic equivalence budget (egg, POPL 2021,
DOI 10.1145/3434304 §5.1/§5.3).

**No C0002 candidate may be described as novel, in any artifact, at any stage.** `H0001-R`'s framing
must credit ND2; `H0010`'s must credit Sato & Sato and NeSymReS.

### 1.4 Explicitly out of scope, and forbidden

1. **Arm B** (`beam_type = "search"` re-decode). Out of scope — §6.
2. **Any selection endpoint on GRN.** Oracle is 0 on the H stratum and the per-cell selector is not a
   decoder argmax (F-f). Rule 03's three-way distinction is carried at the endpoint-name level
   (§16.2): **"selected" is not measurable on GRN this cycle** and no endpoint name claims it.
3. **Any sealed artifact** (§2.4).
4. **Any training or adaptation.** No gradient step anywhere in this cycle.
5. **Reinstating the retracted MAJOR-R5 reading** ("oracle 107 vs selected 58 ⇒ selection loss 49").
   It stays retracted.
6. **Citing `k_gains = 0` for or against E0.** Inherited from v2.1 §9.5 item 0.
7. **Citing D19-1331 for a reference-based search-error rate.** §8.7.
8. **NEW — any sentence attributing the corpus to E2 *or* E3, or using the words "predominant" or
   "attribution" for the pair.** §13 replaces them. Where "predominant" survives it names a
   **certificate rate**, never which failure mode obtains.

---

## 2. Statistical unit, splits, firewall

### 2.1 Units and the analysis hierarchy

| level | object | role |
|---|---|---|
| candidate | one of the 47,987 stored candidates | scored; **never** an analysis unit |
| cell | one of 960 (system × bundle × `noise_sigma` × `subsample_rho`) | `sb_best(c)` / `me_best(c)` defined here; **not** a resampling unit |
| **system** | one of **80** GRN systems | **the analysis element of the primary endpoints** |
| family | one of 8 (R01–R08) | **fixed stratum**, not a random draw (§2.2, §12.1) |

Aggregation order is frozen: within-system mean over usable cells → system indicator → corpus rate.
A cell-level rate is **not** comparable to a system-level rate and the two are never mixed.
**In v2 this binds on the bias-audit battery too** (MAJOR-7 SR): BA1, BA2 and BA3 are aggregated to
the system level before any threshold is applied (§8.5).

Dimension and family are **completely confounded** in this corpus (v2.1 §2.1); no dimension effect
may be claimed.

**Replicate structure, disclosed (MINOR-7 RA).** `cell_input_payload_sha256` takes exactly **10**
distinct values per system on all 80 systems: the three bundles at `noise_sigma = 0,
subsample_rho = 0` share one conditioning payload, so `lp_gt` is byte-identical on them (F-m).
**240 of the 960 cells are therefore 80 conditionings replicated 3×.** `sb_rate(s)` averages them as
if they were 12 independent cells; this is disclosed, not corrected, because correcting it would
change the inherited v2.1 §8.3 aggregation. It also explains Gate 1's "10 distinct payloads per
system" check.

### 2.1b Usable candidate, usable cell, evaluable system — all three defined (MAJOR-3 SR)

v1 defined "usable" for **candidates** only, then aggregated "over the system's usable cells", a term
with no definition, and hard-coded the denominator as a literal `71`. Both are fixed.

- **Usable candidate**: `valid: true` **and** the re-encoding round trip is exact **and** the token
  conversion succeeds **and** (NEW, MAJOR-11 RA) its free symbols lie within the system's dimension,
  so the `C_gen` forward map is not applied to a `rescale_function` early-return image. Every
  non-usable candidate is retained with its `failure_reason` (rule 03).
- **Usable cell**: a cell that passed Gate 1, is not `unreliable_reencoding` (§8.2), has
  `lp_gt_max` and `lp_gt_lse` defined (its system passed Gate 3a), and has **≥ 1 usable candidate**.
- **Evaluable system**: a system whose usable cells (i) number **≥ 8 of its 12** and (ii) **cover all
  four `(noise_sigma, subsample_rho)` settings**. A system failing either is
  `system_not_evaluable`, counted, reported, and **excluded from the numerator and the denominator**.

  *Derivation of the floor, recorded before it was checked.* `E2_system(s)` is an all-cells condition,
  so it becomes **easier** to satisfy as cells are lost: cell attrition biases **P2 upward, toward
  E2**, the campaign's preferred answer. The grid-coverage clause is the design-derived part — each
  system's 12 cells are 3 bundles × 4 corruption settings, and a system indicator driven by one
  corner of the grid is not a statement about the system. The `≥ 8 of 12` clause is the absolute
  floor and is stated as `new_no_derivation` in §0.9.
  *Verified achievable*: every one of the 80 systems currently has exactly 12 cells, 3 per corruption
  setting, and expected attrition is ≈ 0 (§15).

- **The denominator of P1 and P2 is `n_eval`, the realized evaluable-system count**, reported beside
  the nominal 80 in every artifact. **A literal `80` never appears in a denominator.**
- The realized per-system usable-cell distribution is reported.

### 2.2 Target population

Superpopulation reading: Hill-type GRN dynamical systems emitted by the R01–R08 generator under the
frozen corruption grid, scored under the frozen ODEFormer checkpoint. **Systems are the random draws;
the eight families are FIXED strata**, all eight present in the corpus with 10 systems each. A
finite-population reading of the 80 systems is recorded and rejected as the estimand.

**This sentence now binds the interval of record** (§12.1). v1 declared this estimand and then
resampled the 8 families, which targets a superpopulation of *families* that §2.2 does not posit —
the same random-family / fixed-family contradiction that helped render C0001 undecidable
(CRITICAL-4 SR). v2's interval resamples **systems within fixed families**.

### 2.3 Splits

- **Measurement set**: GPU_RUN5 `phase2/validation.json`, **80 systems, all of them** (§4).
- **Calibration set**: GPU_RUN5 `phase2/train.json` (240 systems) may be used only for cost
  calibration and control construction, never for an endpoint.
- **No final test is opened in this cycle.** There is no model selection, no hyperparameter search
  and no early stopping, so there is nothing for a test set to adjudicate.
- Trajectory-level leakage is not a hazard: no derivative-derived rows are constructed and no model is
  fitted. Splits are inherited from GPU_RUN5's `audit.json` (zero system / parameter-variant /
  trajectory duplication, fingerprint `e5edac34...ba8af`).
- `phase3/all_candidates.json` was checked and contains **only** `split == "validation"` rows (47,987),
  so the `H0010` census carries no test-split contamination.

### 2.4 Test firewall

- `src/gpu_run5/config.py load_sealed_test` raises `PermissionError` for `phase < 8`. Every C0002
  phase is `< 8`.
- The **7** sealed files are enumerated **from the filesystem**, never from a hard-coded list
  (`research_state.md` §4). `src/gpu_runclaude1/io_allowlist.py`'s `install_sealed_audit_hook()` /
  `sealed_open_guard()` are installed in every C0002 entry point, as at
  `scripts/phases/gpu_runclaude1_c0001_phase3_partc.py:249, :254`.
- Gate 0 writes `phase0/sealed_inventory.json` with ≥ 7 entries and asserts an **empty intersection**
  against the read allowlist, and asserts `sealed_paths_read == []` at every phase boundary.
- **Caveat carried, per MINOR-5 RA**: `sealed_paths_read == []` is a computed property of
  `InstrumentedOpener` over paths opened **through it**. The `sys.addaudithook` guard **raises**
  rather than accumulating, and reads not routed through the opener are invisible to it. The
  assertion is therefore necessary but not sufficient, and the two guards are the actual protection.

- **REINSTATED FROM C0001 v2.1 §2.4 item 6, VERBATIM (CRITICAL-3 RA).** v1 dropped this and thereby
  reinstated an unguarded sealed-byte read that Gate 0 would not have caught:

  > `scripts/ops/run_manifest.py --data-path` receives only individual files from that allowlist.
  > [Passing a directory] is forbidden.

  Enforcement in v2, all four parts required:
  1. **Every** `run_manifest.py` invocation routes its paths through
     `io_allowlist.safe_run_manifest_data_paths()`. A bare `--data-path` is a contract violation.
  2. `io_allowlist.assert_no_directory_argument()` is called on every path before invocation.
  3. **Gate 0 and every phase boundary assert** "no directory argument reached `run_manifest.py`",
     recorded as a machine check with its own artifact field.
  4. `run_manifest.py`'s own `main()` calls `install_sealed_audit_hook()`, so the guard is not
     conditional on the caller.

  **Why all four are needed.** `scripts/ops/run_manifest.py:28-42 tree_sha256` does
  `sorted(p for p in path.rglob("*") if p.is_file())` then `sha256()` on every one, and `:119` applies
  it to each `--data-path`. It imports no guard, and it runs as a **separate process**, so
  `install_sealed_audit_hook()` / `sealed_open_guard()` installed in the phase entry point do not
  protect it. A directory `--data-path` aimed at `results/runs/gpu_run5_20260823_ddd267b0` would
  byte-read `phase2/sealed_test.json`, `phase2/sealed_family_holdout_test.json` and
  `phase4/sealed_official_test.json` **while Gate 0's `sealed_paths_read == []` still passed**,
  because that value is computed over `InstrumentedOpener` in the *phase* process.
  This is the recurrence of `C0001_reproducibility_audit.md` MAJ-2.

- Two GRN seals are **SPENT**; `phase4/sealed_official_test.json` has had its bytes read by its own
  generating phase (R3). **No C0002 endpoint requires any of them.**

### 2.5 What cannot change after the first primary indicator is computed

No final test is accessed, so the question is answered in its stronger form. Frozen at that instant
and changeable only through §18: the primary hypothesis and its falsifier; **both** endpoints and
**both** decision rules; the `0.5` system cutpoint; the scoring contexts and which is primary; the
admissible-encoding enumeration, its cap and **which quantity carries which certificate**; the
control battery and every control threshold; the usable-candidate / usable-cell / evaluable-system
definitions and the per-system floor; all exclusion rules; all seeds; **the fixed-stratum cluster
definition and the interval of record**; the `H0010` predicates, **the frozen `H0010` corpus** and
the graded rule; and the compute ceiling.
**Raising a threshold to rescue a result is forbidden without exception** (rule 01 item 3).

---

## 3. Model, checkpoint, seeds, budgets

| item | frozen value |
|---|---|
| checkpoint | `assets/odeformer/weights/odeformer.pt`, SHA256 `56754040be5aa92ed4767fc43ee2008faa293f87c12b643e66c7df3e1623a5e8`, 464,822,385 bytes |
| **input artifacts, pinned by hash (NEW, MAJOR-5 RA)** | the six digests + the cells roll-up of **M7** (§0.7). Gate 0 recomputes each and asserts equality |
| **`phase0/input_fingerprints.json` (NEW)** | written from `io_allowlist.InstrumentedOpener.fingerprints()` (`io_allowlist.py:165-176`), listing every input path opened with its SHA256. **Gate 0 check.** v1 dropped this requirement, which C0001 v2 had mandated |
| package | `third_party/odeformer` via `gpu_run4_runtime.install_odeformer_path`, guarded by `assert_odeformer_not_from_github_source()`. `GitHubSourceCode/` is reference-only |
| precision | **fp32 throughout**. Never fp16, never bf16, never CPU for a scored sequence |
| device | GPU 0 (RTX 2070). `torch.cuda.set_per_process_memory_fraction(5.5 / 8.0, device=0)` before the first allocation |
| decode config of the stored candidates (context, never swept) | `beam_type = "sampling"`, `beam_temperature = 0.1`, `beam_size = 50`, `rescale = true`, `max_generated_output_len = 200` — the checkpoint's own stored defaults, verified by reading the checkpoint |
| `GLOBAL_SEED` | `20260911` |
| `SYMPY_RNG_SEED` | `20260911` |
| **`multiprocessing` start method (NEW, MAJOR-1 RA)** | **`fork`**, declared explicitly via `mp.get_context("fork")`. Both the seed contract and the §2.4 firewall guards' inheritance silently depend on this: `fork` inherits `builtins.open` patching and `sys.addaudithook`, `spawn` does not. If the platform forces `spawn`, the worker initializer **must** install `install_sealed_audit_hook()` and `sealed_open_guard()` as well as the seed, and that substitution is a §18 deviation |
| `CLUSTER_BOOTSTRAP_SEED` / resamples | `20260911` / `10000` |
| `ENCODING_VERIFICATION_SEED` | `20260911`, 8 evaluation points per component, `rtol = 1e-3` (§7.2) |
| `CONTROL_CELL_SEED` | `20260911` |
| fingerprint parameters (inherited from C0001, unchanged) | stdlib `random.seed(77771)`, `mpmath.mp.dps = 40`, 10 points |
| `N_WORKERS` | **6**, declared as a **value**, not a cap |
| training budget | **zero**. No optimizer is constructed |
| decode budget | **zero new decoding**, except PC-GREEDY (§10.2), capped at 40 cells |

---

## 4. Realized denominators — the 80 → 71 filter is DROPPED (MAJOR-4 SR)

**v1 restricted P1/P2 to the 71 in-support systems. v2 does not.** The filter is inherited from a
criterion that is irrelevant to a log-probability endpoint, and `partB_endpoints.json` says so
verbatim in its own `note` field:

> "out of support is scoped to the preregistered rewrite set B-R1..B-R4 (v2 §8.1); never claimed as
> out of support absolutely."

Further: C0001 report §7.3 records `uses_only_in_support_operators` **True for all 9** excluded
components; the design brief §73 records GRN truths as 100% in-support in the operator sense
(F2, 560/560 round trip); and C0001 itself computed `gt_logprob_sum` for **all 960** cells. Nothing
about a teacher-forced log-probability comparison requires the exclusion.

The exclusion also **cost the design**: it removed 9 systems and 108 cells (11%), concentrated in R07
(6) and R08 (3), which is what drove the family sizes to 4 and 7 and unbalanced the very clusters
CRITICAL-4 SR is about; and it silently narrowed §2.2's stated population, non-proportionally across
families, so the unweighted mean over 71 did not estimate the population §2.2 names.

**Frozen corpus for P1/P2**, recounted directly over `phase3/cells/*.json`:

| quantity | value |
|---|---|
| systems | **80**, every one `split == "validation"` |
| systems per family | **R01–R08 = 10 each** — eight equal fixed strata |
| cells | **960**, **120 per family**, exactly 12 per system |
| candidates | **47,987**; `valid: true` on **47,987 / 47,987**; 0 cell failures |
| candidates per cell | 50 on 951, 49 on 6, 48 on 2, 47 on 1 |

**The 71 in-support systems are retained as a preregistered sensitivity subgroup** (S11, §8.4), with
its own realized denominators (71 systems / 852 cells / 42,593 candidates / 42,593 valid; per-family
R01–R06 = 10, R07 = 4, R08 = 7), reported beside the primary. **The primary is the 80-system read**;
the subgroup may not be promoted to primary after the fact.

| endpoint | realized denominator | how known | census required? |
|---|---|---|---|
| `H0001-R` P1/P2 | **80** systems / **960** cells / **47,987** candidates → reported as `n_eval` evaluable systems (§2.1b) | counted directly | **no** |
| S11 in-support subgroup | 71 / 852 / 42,593 | counted directly | no |
| `H0006` gate | 80 systems, each with an enumerated encoding set | enumeration is the census | no |
| `H0010` | **89,349** distinct component strings over all 80 systems (§9.2) | **reproduced end to end by M2** from `all_candidates.json` | the class census still gates (§9.2) |

**Standing requirement OC (design brief §6) is satisfied**: the only endpoint whose realized
denominator was not already established from a checksummed artifact is `H0010`'s class count, and for
it a census is preregistered as a gating precondition (§9.2, Gate 2) computed **before** the endpoint.

---

## 5. Instrument changes

**Every change below makes the instrument *measurable* or *reproducible*. None alters any C0001
conclusion.** In particular **`k_gains = 0` is not at stake**: the Stage-10 replication established
that the M3 *value* agreed on all 101,963 comparisons.

### 5.1 Change 1 — the reference set for the Stahlberg–Byrne indicator

Unchanged from v1 §5.1, whose three citation corrections both reviewers verified in full.

`src/evaluation/gpu_run5_selection.py:11 formula_selection_key(records, validation_ce)` groups by
`(system_id, seed)` and returns a 4-tuple lexicographic **cross-run model-selection** key; it never
indexes a candidate. A **different** `formula_selection_key(rows)` of arity 1 exists at
`src/gpu_run5/evaluation.py:143`. The function that actually selects one candidate per cell is
**`src/gpu_run5/evaluation.py:107 select_candidate(...)`**, whose `"official_reconstruction"` branch
returns `0` unconditionally at `:111-112`. **Cite the module path, never the bare name.**

This contract uses **`lp_best`, the maximum over usable candidates** — Stahlberg & Byrne's γ verbatim
(Alg. 1 line 12 is an `arg max` over the returned set; the set's provenance is not part of the
definition). **Sampling is admissible. An arbitrary member of the returned set is NOT γ and is never
used anywhere in this contract** — a prohibition that §8.5 now invokes to derive BA2's minimum
partner count. `lp_sel` does not appear as an endpoint anywhere.

**What this makes measurable**: without it, `sb_sel` would measure "is the truth more probable than an
arbitrary T = 0.1 draw", which for a peaked decoder is nearly always true and would **fabricate E3**.
**C0001 is uncontaminated** — `lp_sel` was never computed there.

### 5.2 Change 2 — a deterministic budget for CAS work, and a **per-item** seeded SymPy RNG

**Where it binds.** No C0002 endpoint depends on a CAS equivalence decision. `H0001-R` uses
log-probabilities; `H0010`'s predicates use `sympy.cancel(sympy.together(·))` and `sympy.fraction`,
with no `simplify`, no `equals`, no equivalence test. The change is a repository-level instrument
repair with its own verification, **not** a gate on a C0002 endpoint. **v2 makes that scoping
binding on Gate 6** (MAJOR-3 RA); see §11.

Frozen:

1. **The `count_ops` admission bound applies to already-parsed `Expr` objects only.** v1 said "compute
   `sympy.count_ops(expr)` on the input", but the real call sites take **strings**
   (`src/gpu_runclaude1/partc_reencoding.py:103`, `src/evaluation/equation_metrics.py:174,183`), and
   `count_ops` on a string **sympifies internally**, so the parse is paid unconditionally before the
   budget can apply and is itself unbounded (MAJOR-2 RA). v2 therefore:
   - parses explicitly first, then applies `CAS_NODE_BUDGET = 400` to the `Expr`;
   - gives the unbounded parse its own explicit, counted label **`parse_not_admitted_unbounded`**,
     which is reported rather than hidden;
   - **requires the call sites to be fixed** so that `sympify(...)` is evaluated **inside** the
     `with _time_limit(...)` block. `equation_metrics.py:174` and `:183` currently pass
     `sympify(sk)` as an *argument* to `_timed_simplify`, so the parse is evaluated before the guard
     is entered and is protected by **neither** the budget nor the clock.
   - **Measured (F-l, M2)**: over all 89,349 distinct component strings the maximum `count_ops` is
     **14**, so the 400-node bound **excludes 0 rows** and is inert on this corpus; the parse costs
     0.001458 s/string. The bound is retained for the property it guarantees, not for a filtering
     effect it does not have.
   - **Declared, not fixed**: `count_ops` is not monotone with the runtime of `cancel` / `simplify` on
     rational functions, so a 400-node bound does not bound `cancel`. §21 item 1.
2. **A deterministic PER-ITEM SymPy reseed replaces v1's per-worker seed** (MAJOR-1 RA). v1 called
   `sympy.core.random.seed(SYMPY_RNG_SEED)` once at worker start. `sympy/core/random.py` holds one
   module-level `rng` per interpreter; seeding at worker start fixes its state at `t = 0`, while the
   state at any given comparison is advanced by every RNG-consuming call that worker happened to
   handle first — and that assignment is **load-dependent** under any availability-scheduled pool.
   The audit demonstrated this directly in the pinned 1.13.1. v2 freezes instead, immediately before
   each guarded call:

   ```
   sympy.core.random.seed(SYMPY_RNG_SEED ^ int(sha256(normalized_input_key).hexdigest()[:8], 16))
   ```

   so the outcome is a function of the input and `SYMPY_RNG_SEED` alone, regardless of worker
   assignment, chunk size and arrival order. `normalized_input_key` is the frozen class key of §9.1.
   **Required test**: two runs with different `chunksize` produce **byte-identical** label files.
   Gate 0's v1 item 7 (asserting `seed()` was called in each worker) proved only the part that was
   never in question and is replaced by this test.
3. **`Expr.equals`'s raw three-valued return is recorded** wherever it is called, as
   `equals_raw ∈ {True, False, None}`. `bool(...)` is never applied to it. Realized `equals_NONE` on
   the C0001 corpus was **exactly 0**, so this changes no C0001 number.
4. **`N_WORKERS = 6` is a declared value**, every worker is a **process**, never a thread (F-c), and
   the start method is **`fork`**, declared (§3).
5. **Never call `.equals` outside the guard.**

**What this makes reproducible**: the failure classification becomes a function of the inputs and of
declared values, not of machine load, worker assignment, SymPy cache state, or OS entropy.

**What it does not change**: C0001's `k_gains = 0`, its `undecidable` verdict of record, or any number
in `C0001_report.md`.

### 5.3 Change 3 — the conditioning under which sequences are scored

Unchanged from v1 §5.3. F-g: candidates were generated under a rescaled, permuted conditioning and
returned as original-unit expressions, while the teacher-forcing helpers condition on raw, unpermuted
points. Two declared scoring contexts, both fully specified, with the matched one primary (§7.1) —
**subject to §7.3**, which records that M5 predicts the matched context will fail its own Gate-4 bar.

---

## 6. Arm A / Arm B — scope decision

Unchanged from v1 §6. **Arm A is in scope. Arm B is OUT of scope for C0002.** They are separate
experiments on different candidate sets, not alternatives.

| | Arm A (in scope) | Arm B (deferred) |
|---|---|---|
| candidate set | the **stored** T = 0.1 sampled set (47,987 candidates) | a **new** set from `beam_type = "search"` |
| indicator | `sb_best = 1[lp_gt_max > lp_best]`, `me_best = 1[lp_gt_lse < lp_best]` | `sb_sel` against search's own top-1 |
| status of the indicator | a **certified lower bound**, not an estimate | an estimate against a different returned set |

Justification: (1) `lp_best` over the stored sampled set *is* γ, so Arm B is not needed to validate
Arm A; (2) **Arm B's realized denominator is unknown by construction** — precisely the failure mode
C0002 was selected to avoid; (3) Arm B's compute is unmeasured while Arm A's is measured at
0.233 GPU-h per 960-cell pass; (4) the specific question Arm B would answer ("how loose is `lp_best`
as a bound on `L*`?") is answered in scope by BA1 and PC-GREEDY; (5) mixing two decode configurations
inside one cycle would make a disagreement uninterpretable.

**What is thereby given up, stated plainly**: C0002 cannot report a search-error rate against what a
*search* procedure returns, and cannot bound how much of `me_best = 1` is attributable to the sampling
temperature as opposed to the model's prior. Those remain open and are the content of Arm B.

---

## 7. Scoring contexts and the `H0006` encoding gate

### 7.1 The two frozen scoring contexts

A **scoring context** fixes (i) the encoder input and (ii) the unit system in which every scored
sequence is expressed. Within a context, the ground truth and every candidate are scored by one
function, under one conditioning, in one unit system. Contexts are never mixed inside an indicator.

**`C_gen` — matched conditioning. PRIMARY, subject to §7.3.**
1. `scaler = odeformer.model.utils_wrapper.Scaler(time_range=[1, 10], feature_scale=1)`;
   `scaled_times, scaled_traj = scaler.fit_transform(times, observed_trajectory)` on the cell's stored
   `observations["input"][0]`.
2. `np.random.seed(int(cell["candidate_seed"]))`; `perm = np.random.permutation(len(scaled_times))`;
   apply `perm` to both arrays. Reproduces `sklearn_wrapper.py:133-136` exactly.
3. One bag (every cell has ≤ 150 points, `max_input_points = 10000`).
4. Every scored sequence is expressed in **scaled** units by the closed-form forward map, the exact
   inverse of `Scaler.rescale_function`:
   `f_s,d(x_s) = (scale[d] / a_t) · f_o,d(x_j → x_{s,j} / scale[j])`, with
   `(a_t, b_t, scale) = scaler.get_params()`; if a sequence contains `t`, additionally
   `t → (t − b_t) / a_t`.

**`C_raw` — raw conditioning. ROBUSTNESS ARM.** Raw `times` / `observed_trajectory`, unscaled,
unpermuted, single bag, every sequence in original units — exactly what
`src/gpu_run4/training.py:51 teacher_forced_summed_logprob` does and what C0001 used for `lp_gt`.

**Why `C_gen` is primary — the F-g argument alone.** Only under `C_gen` is the candidate set the set
the decoder produced *under that conditioning*, so only there does `sb_best = 1` read as a search
error of the decode that actually happened. Under `C_raw` Certificate N still holds, but Certificate S
certifies only that the truth outscores 50 arbitrary expressions under a conditioning the search never
saw. **v1's secondary reason — that the leakage of §0.2/§0.3 is entirely under `C_raw` — is withdrawn
as a justification** and retained only as a disclosure (§0.3 item 5), because "which context is
primary" is on the §2.5 frozen list and choosing it in light of an observation is a post-observation
design choice, not containment.

**The `rescale_function` early-return hazard, guarded (MAJOR-11 RA).**
`third_party/odeformer/odeformer/model/utils_wrapper.py:54-80 rescale_function` returns the tree
**unchanged** at `:56-57` (`if len(nodes)>len(scale)`) and at `:67-68` (`if dim>=len(scale)`); the
second fires whenever a candidate references a variable index `≥ dim`, which ODEFormer can emit
(`max_dimension = 6` against 1–3-dimensional GRN systems). And `sklearn_wrapper.py:166-167` is a bare
`except: pass` around `simplify_tree`, so a candidate whose simplification raised is stored
un-simplified. For such candidates the stored `candidate_formula_raw` is **not** the
`rescale_function`-then-`simplify_tree` image of a scaled-unit tree, and applying the forward map
would **doubly transform** them, producing a silently wrong `lp_best` contribution.
**Frozen guard**: a candidate is usable in `C_gen` only if its free symbols lie within the system's
dimension (§2.1b). Candidates failing it are excluded with `failure_reason:
"rescale_function_early_return_suspected"`, counted and reported (rule 03) — **never transformed**.
Whether any candidate actually hits those branches is `unverified`; the guard is preregistered so that
the answer is recorded either way.

### 7.2 `H0006` — the admissible-encoding enumeration

A single spelling of the truth gives a `lp_gt` that is a **lower bound** on the truth's probability
under the model, biasing the read toward E2 (`literature/C0002_literature.md` §Q2.4 item 4).

**Frozen enumeration `E(s)` per system `s`, per context:**
- `e1` = the stored `tree_encoded` from `phase2/validation.json` (prefix-derived).
- `e2` = `infix_to_model_tokens(env, teacher_infix)` (infix-derived, via
  `sympy → env.simplifier.sympy_expr_to_tree → env.equation_encoder.encode`;
  `src/gpu_runclaude1/partc_reencoding.py:85`).
- `e3 … eK` = the commutation orbit of `e2`'s tree under `add` / `mul` operand swaps, **cap 8**, in
  the enumeration order **frozen by v2.1 §8.2 step 5** (commutable binary nodes indexed in pre-order,
  root first, left to right; orbit member `t` swaps node `k` iff bit `k` of `t` is set; `t = 0` is the
  unswapped encoding). Inherited verbatim so the order was fixed on 2026-09-09.

**`e1` in `C_gen` is specified explicitly (MAJOR-10 RA).** The stored `tree_encoded` is in **original**
units. Scoring it in `C_gen` requires `env.equation_encoder.decode` → the §7.1 forward map →
`sympy_expr_to_tree` → `encode`. **That is exactly `e2`'s path, and F-j measures the consequence:
`e1` and `e2` are identical on 120 / 120 cells in `C_gen`.** In `C_raw`, where the stored list is
scored as stored, they are distinct on 80 / 80 systems.

**Verification of each member**: decode with `env.equation_encoder.decode`, then check numeric equality
against `teacher_infix` at `ENCODING_VERIFICATION_SEED = 20260911`, **8** points per component drawn
uniformly from `[0.2, 2.5]`, `rtol = 1e-3`. Failing members are **dropped and logged** as
`EncodingVerificationFailure`, never silently.

**The two quantities, and which certificate each carries (CRITICAL-1, both reviews):**

| quantity | definition | carries |
|---|---|---|
| **`lp_gt_max(c)`** | `max_e` over the verified members of `E(s)`, evaluated in the cell's context — **a single-sequence score** | **`sb_best` / Certificate S / P1** |
| **`lp_gt_lse(c)`** | `logsumexp_e` over the same members | **`me_best` / Certificate N / P2** |
| `lp_gt_single(c)` | `e1` alone | descriptive |
| `Δ_enc(c)` | `lp_gt_lse − lp_gt_single ≥ 0` | BA3 |
| `Δ_maxlse(c)` | `lp_gt_lse − lp_gt_max ∈ [0, log|E(s)|]` | descriptive; `≤ 2.303` nats at the cap of 10 |

v1 defined **both** indicators on the logsumexp. That destroys Certificate S (F-i) while leaving
Certificate N intact, and §8.7 made "certified lower bound" a **binding** permitted sentence, so v1
mandated a claim its own endpoint could not support. The fix costs **no new compute** — both
quantities were already computed in v1 §7.2 as "descriptive companions".

**Both variants of `sb_best` are recorded** (`sb_best_max` on `lp_gt_max`, `sb_best_lse` on
`lp_gt_lse`) so the difference is auditable, and **`sb_best_max` is preregistered as the one that
bears the decision.**

**`lp_gt_is_lower_bound_over_capped_enumeration: true` is carried UNCONDITIONALLY on every artifact**
(MAJOR-8 SR), not only when the fallback to `e1` occurs. `E(s)` is capped at 8 orbit members over
`add`/`mul` swaps plus `e1`/`e2`, while the set of semantically equivalent spellings (associativity,
distributivity, constant re-encodings, algebraically equivalent Hill forms) is far larger. **`Δ_enc`
measures movement within the enumerated set and bounds nothing about the residual.** v1 §7.2's claim
that `Δ_enc` "is the measurement of this bias" is withdrawn as an overclaim; it is a measurement of
*part* of it.

**`H0006`'s own negative branch is informative**: if the enumeration is exhausted and `Δ_enc` is small
on most cells while truth-in-beam stays 0, then `0/960` hardens as a property of the model rather than
of the spelling.

### 7.2b Gate 3 — split into PASS conditions and a DOWNGRADE condition (CRITICAL-2 RA)

v1 had **two contradictory dispositions for the identical condition**: §7.2 said a 3b failure is
"a downgrade, not an abort", while §11 Gate 3 listed 3b as a gate condition and Gate 6 reported the
primary only if Gate 3 passed. **This is the C0001 Gate B→C defect verbatim** — one contract, two
clauses — and it makes rule R7's "quote the contract text verbatim beside the check" unsatisfiable,
because there are two contract passages saying opposite things.

**Frozen split. There is exactly one disposition per condition, stated here and nowhere else.**

| # | condition | threshold | **class** | disposition on failure | achievability |
|---|---|---|---|---|---|
| **3a** | every system has ≥ 1 verified encoding | **80 / 80** | **PASS condition** (abort-class) | `H0001-R` is `undecidable (no admissible encoding)`. A system with no verified encoding has no `lp_gt` at all | **80 / 80 measured** (M5, `C_raw`); `e1` was scored for all 960 cells in C0001 with no failure |
| **3b** | systems with ≥ 2 verified **distinct** encodings | ≥ 90% | **DOWNGRADE condition** — **NOT** a pass condition, **NOT** consulted by Gate 6 | the logsumexp arm is `not_measurable`; `lp_gt_lse` falls back to `lp_gt_max`; **every E2-direction statement is qualified `single_encoding_lower_bound`**; BA3 is reported `not_measurable` and, per §8.5, that **blocks** a supported E2 | **cannot be met from `e1`/`e2` in `C_gen`** (F-j: 0 / 120 distinct). In `C_gen` it rests on orbit members alone and its achievability there is **`unverified`** (§0.7). In `C_raw` it is met 80 / 80 |
| **3c** | `EncodingVerificationFailure` rate over enumerated members | ≤ 20% | **REPORT-ONLY** | counted and reported; **no endpoint changes**. v1 gave 3c no disposition anywhere except transitively through Gate 6 (MAJOR-14 RA) | `e1` and `e2` verified 100%; only orbit members are untested, and a failing orbit member is dropped without affecting 3a or 3b |

**Gate 6 consults 3a only.** 3b and 3c are removed from every conjunction.

### 7.3 The `C_gen` / `C_raw` primacy decision the supervisor must make

This is not a defect to be repaired inside the contract; it is a fork, and it is stated so the
supervisor decides it before freeze rather than an implementer discovering it at Gate 4.

**The measured facts.** Gate 4's `C_gen` reconstruction condition, re-expressed as MAJOR-9 RA requires
— a real round trip through `env.equation_encoder`, not the vacuous "forward map + inverse to 1e-8"
that any invertible map passes and that never reaches the tokenizer — measures
**0.9683** in `C_gen` against its frozen `≥ 0.98` bar, and **0.9917** in `C_raw` (M5). The numeric
round trip in `C_gen` is accurate to `rtol = 1e-3` on only **0.275** of cells, median relative error
**2.03e-3**, max **1.05e-1**; in `C_raw` it is exact (F-k). The cause is the encoder's
4-significant-digit constant quantization (`float_precision = 3`, `float_descriptor_length = 3`,
`odeformer/envs/encoders.py:124`), which is lossless on original-unit GRN constants and lossy on the
arbitrary reals `C_gen` produces.

**The bar is NOT moved.** Setting the tolerance from the measured distribution would be exactly the
forbidden move. `≥ 0.98` stands.

**Consequences, both stated in advance:**

- **If `C_gen` fails Gate 4** — which M5 predicts — §18's named contingency fires: **`C_raw` becomes
  primary, and every Certificate-S statement in the cycle is downgraded** to "the truth outscores all
  50 candidates under a conditioning the search did not see", which is **not** a search-error claim.
  **And §0.3's containment collapses**: the primary context becomes the one under which `lp_gt` was
  already observed on all 960 cells (§0.2) and under which the 8-cell `sb_best` exposure occurred
  (§0.3). The cycle would then be reporting a primary endpoint in a context whose proxy was observed,
  in the preferred direction, before freeze. **That must be disclosed in the cycle report as a
  validity threat, not absorbed silently.**
- **If `C_gen` passes**, nothing changes and the design proceeds as written.

**A third option the supervisor may take, recorded so it is a preregistered choice and not a
post-hoc rescue**: declare **both contexts co-primary with no fallback**, report P1 and P2 in each,
and make disagreement between them the `conditioning_sensitive` verdict of §13 — which BA4 already
computes. This neither moves a threshold nor privileges the observed context, but it doubles the
number of reported intervals and weakens what a single agreeing result can claim. **The methodologist
takes no position; the choice is the supervisor's and must be recorded before Gate 4 runs.**

**Note on the quantization itself.** It is not an error in the endpoint: both `lp_gt` and `lp_best` are
scored on quantized sequences, so they remain commensurable, and F-d already establishes that constants
are ordinary vocabulary tokens. What the quantization does mean is that **the truth scored in `C_gen`
is a 4-significant-digit approximation of the truth**, and every `C_gen` artifact carries
`gt_is_quantized_in_context: true` so no reader mistakes it for the exact expression.

---

## 8. `H0001-R` — endpoints, decision rule, and the bias-audit battery

### 8.1 Per-cell quantities (both contexts)

For each of the 960 cells `c`:

- `lp_gt_max(c)`, `lp_gt_lse(c)`, `lp_gt_single(c)`, `Δ_enc(c)`, `Δ_maxlse(c)` — §7.2.
- for each stored candidate: `candidate_reencoding_roundtrip_exact`, and if **usable** (§2.1b),
  `candidate_logprob_sum`, `candidate_token_length`. Every non-usable candidate is retained with its
  `failure_reason` (rule 03); none is silently dropped.
- `lp_best(c)` = max over usable candidates. **This is an ORACLE quantity** (rule 03) and is never
  presented as achieved selection performance.
- **`sb_best(c) = 1[lp_gt_max(c) > lp_best(c)]`** — Certificate S for `c`. *(v1 used `lp_gt_lse`.)*
- **`me_best(c) = 1[lp_gt_lse(c) < lp_best(c)]`** — Certificate N for `c`.
- **`neither_cert(c) = 1[lp_gt_max(c) ≤ lp_best(c) ≤ lp_gt_lse(c)]`** — **NEW and required by the
  split.** Because the two certificates now read different quantities and `lp_gt_max ≤ lp_gt_lse`,
  a band exists in which **neither** certificate fires. Cells in it are **counted, reported, and
  excluded from both `sb_rate` and `me_rate` denominators.** Its width is `Δ_maxlse ≤ log|E(s)| ≤ 2.303`
  nats, so it is expected to be rare, but it is real and v1 had no name for it.
  `tie(c) = 1[lp_gt_max(c) == lp_best(c)]` is a boundary case of it, counted separately.
  **The realized `neither_cert` rate is reported with its denominator and may not be omitted.**
- `gt_token_rank_profile(c)` — per-position rank of the GT token (0 = argmax), from
  `teacher_forced_summed_logprob_batch(..., compute_ranks=True)`.
- `argmax_agreement_best(c)` — the fraction of the best candidate's scored positions at rank 0.
- `candidate_token_length` and `gt_token_length`, for BA2.

### 8.2 Re-encoding audit (inherited from v2.1 §8.2 step 4)

`encode(parse(raw)) → decode → canonicalize`, compared to the stored `candidate_formula_canonical`
after the frozen separator normalization `\|` → `,\|,` (`src/gpu_runclaude1/partc.py:96, :112`).

- mismatch → `CandidateReencodingMismatch`: excluded from the comparison distribution, **counted and
  reported**;
- > 10% of a cell's candidates mismatch → cell `unreliable_reencoding`, excluded from the decision
  endpoints, reported separately;
- > 10% of cells `unreliable_reencoding` → `H0001-R` is **`undecidable`**.

**Achievability, relabelled (MAJOR-9 RA).** v1's "exact round trip on 300 / 300 candidates over 6 cells
(seed 12345)" was measured on the **stored `candidate_formula_canonical`**, i.e. in original units, and
is **`unverified_for_C_gen`**. The `C_gen` figure is M5's **0.9683** candidate token-identity round
trip against `0.9917` in `C_raw` (§7.3). Every v1 achievability figure taken in `C_raw` or in original
units is labelled `unverified_for_C_gen` wherever it appears in v2.

### 8.3 System aggregation

`sb_rate(s)` = mean of `sb_best(c)` over the system's usable cells excluding `neither_cert` cells;
`me_rate(s)` = mean of `me_best(c)` over the same denominator.

- **`E3_system(s) = 1[sb_rate(s) ≥ 0.5]`** — inherited verbatim from v2.1 §8.3, frozen 2026-09-09.
- **`E2_system(s) = 1[me_rate(s) = 1]`** — **CHANGED from v1's `1[sb_rate(s) = 0]`** (m-3 SR).

**Why the change is admissible, and why it cannot make E2 easier.** v1's P2 was named
`certified_non_argmax_system_rate` but computed through `sb_best`, so it equalled the non-argmax
certificate only if tie cells were removed from the `sb_rate` denominator — which §8.1 implied and
§8.3 did not state. Once the certificates read different quantities (§7.2), `sb_rate(s) = 0` no longer
implies `me_best = 1` on every cell, because of the `neither_cert` band. So the v1 form would name a
certificate it does not compute.
**The new form is strictly stronger**: `me_rate(s) = 1 ⇒ sb_rate(s) = 0`, but not conversely
(a system all of whose cells sit in the `neither_cert` band has `sb_rate = 0` and `me_rate < 1`).
**The change therefore makes a supported E2 harder, never easier** — which is the direction in which a
definitional change to the campaign's preferred answer must go.

### 8.4 Endpoints

| id | endpoint | type | inference |
|---|---|---|---|
| **P1** | **`certified_search_error_system_rate` = Σ_s E3_system(s) / n_eval**, primary context | **PRIMARY** | §12.1's interval of record |
| **P2** | **`certified_non_argmax_system_rate` = Σ_s E2_system(s) / n_eval**, primary context | **CO-PRIMARY** | same |
| S1 | P1 and P2 recomputed in the non-primary context | robustness (**BA4**) | same |
| S2 | mean `sb_rate` and `me_rate` across systems; the **cell-level** `sb_best`, `me_best` and `neither_cert` rates **with their denominators** | descriptive | Wilson on the stated denominator, **labelled cell-level and never compared to a system-level rate** (m-2 SR) |
| S3 | paired `lp_gt_max − lp_best` and `lp_gt_lse − lp_best` per system in nats, **summed**; and the per-token version | descriptive | stratified bootstrap. **The per-token version may not bear a decision** |
| S4 | `Δ_enc`, `Δ_maxlse`, and `encoding_flip_rate` = fraction of **systems** on which logsumexp vs single flips `E2_system` | **BA3**, **blocking** | descriptive |
| S5 | per-position GT-token-rank profile by token class (operator, mantissa, exponent, `\|` separator) | descriptive | `classify_token_class` at `src/gpu_runclaude1/partc.py:162` |
| S6 | `argmax_agreement_best` distribution, aggregated **to the system level** | **BA1**, **blocking** | descriptive |
| S7 | `sb_best_len` and `me_best_len` — the length-controlled companions — plus `length_matched_partner_available_rate` and the in-window partner count distribution | **BA2**, **blocking** | descriptive |
| S8 | `rank_pct_sum(c)` = fraction of usable candidates scoring above `lp_gt_max`; `below_all_indicator`; the IQR of the candidate scores and the GT gap in IQR units | descriptive | **carries the frozen v2.1 §8.3 C2-S6 note verbatim**: the candidates were drawn at T = 0.1 and are an extreme upper-tail sample; a low rank does not establish model error and **no E2/E3 statement may cite these** — see §8.5b for the adjudication this required |
| S9 | instrument audit panel: re-encoding mismatch rate, `unreliable_reencoding` cell rate, `EncodingVerificationFailure` rate, `CellIdentityMismatch` rate, the 10-distinct-payload check, the `sum/n == −mean_CE` regression result, `wall_clock_guard_fired` count **broken out by endpoint**, `parse_not_admitted_unbounded` count, `rescale_function_early_return_suspected` count, `system_not_evaluable` count and the per-system usable-cell distribution | descriptive | gates §11 |
| S10 | GT token length vs `lp_gt_max` and vs `sb_best` | **exploratory** (rule 01 item 9) | — |
| **S11** | **P1 and P2 recomputed on the 71 in-support systems** | **preregistered sensitivity subgroup** (§4) | same. **May not be promoted to primary** |

**Rule 03 endpoint-name contract**: `lp_best` and every endpoint built on it are **oracle** quantities
over the generated set. P1 and P2 are statements about **generation and the decoder's own preference**,
never about selection. **No selected-candidate endpoint exists in this contract**, and
`generation_coverage_scope: "cell"` is carried on every record.

### 8.5 The bias-audit battery — now with blocking consequences (CRITICAL-6, CRITICAL-7 SR)

Three mechanisms bias the read toward E2, the campaign's preferred answer; F-g adds a fourth of
unknown direction.

**The defect v2 repairs.** In v1 the three audits of mechanisms pointing **toward** E2 had label-only
or no-op consequences, and the **only** audit with a real blocking consequence was BA4, whose direction
is unknown. The battery's blocking power was therefore systematically **anti-correlated with bias
direction**. v2 gives BA1, BA2 and BA3 blocking consequences, so the wording "an E2 statement that
does not clear §8.5 is not a supported E2" is actually implemented by §13.

**Aggregation, frozen (MAJOR-7 SR).** Each audit is reduced **to the system level before any threshold
is applied**, honouring §2.1's frozen order. Where a threshold is applied to a point estimate with no
interval, that is stated explicitly and the cost is named.

| id | mechanism | measurement (system-level) | **frozen consequence — all four now bite** |
|---|---|---|---|
| **BA1** | T = 0.1 upper-tail sampling makes `B` a tight bound on `L*`, so Certificate S is hard to trip. `beam_type = "sampling"` and `beam_temperature = 0.1` are the **checkpoint's own stored defaults**, not a campaign choice | per system, the median `argmax_agreement_best` over its usable cells; then the **median over systems** | if the median over systems ≥ **0.95**: `lp_best ≈ L*`, so Certificate S was nearly unable to fire and **`P1 ≈ 0` carries no information**. **P1 is reported `certificate_opportunity_insufficient`**, the falsifier is declared **unevaluable**, and — because a near-greedy reference is precisely what makes `me_best = 1` easy — **a supported E2 is BLOCKED**, not merely labelled `E2_conditional_on_near_greedy_reference` as in v1 |
| **BA2** | summed log-probability is length-confounded — D19-1331's own central finding (§4, Tab. 1, Figs. 1/3) — and Hill truths are token-longer than the polynomial candidates that dominate the realized vocabulary | a cell **contributes** iff it has **≥ 3** in-window partners (`\|len − len_gt\| ≤ round(0.20 · len_gt)`); `sb_best_len` / `me_best_len` computed on contributing cells; aggregated to systems; `length_matched_partner_available_rate` = fraction of usable cells contributing | if the availability `< 0.5`: **`length_control_not_measurable`**, and **that BLOCKS a supported E2**, yielding `E2_direction_observed_but_length_unaudited`. v1 merely reported it, and §13 triggered the confounded verdict only when BA2 "fails its disagreement bar" — so an **unmeasurable** control, being neither a pass nor a fail, let a supported E2 through with the length confound entirely unaudited. **Measured before freeze: 0.4625 at the frozen floor of 3, 0.4990 at the lowest admissible floor of 2 — so this branch is predicted to fire (§0.0 item 1).** Where it does run, if `sb_best_len`/`me_best_len` disagree in direction with `sb_best`/`me_best` on **> 20%** of contributing systems, the verdict is `E2_direction_observed_but_confounded`. **Length normalization itself breaks the monotonicity that makes γ admissible** (D19-1331 §2), so no normalized variant may replace the raw certificate |
| **BA3** | a single-encoding `lp_gt` is a lower bound on the truth's probability, and the enumeration `E(s)` is itself capped (§7.2) | `Δ_enc`, `Δ_maxlse`, and `encoding_flip_rate` = fraction of **systems** on which `E2_system` flips between the logsumexp and the single-encoding read | if `encoding_flip_rate > 0.05`, or if Gate 3b failed so that the logsumexp arm is `not_measurable`: **a supported E2 is BLOCKED**. v1's consequence ("only the logsumexp read is reportable") was a **no-op**, because the primary already *was* the logsumexp. The blocking form is the one that bites: a high flip rate demonstrates that the endpoint is sensitive to a nuisance **whose full extent is unmeasured**, since `Δ_enc` moves only within the enumerated set |
| **BA4** | the generation conditioning is not the scoring conditioning (F-g), **direction unknown** | S1 — P1 and P2 recomputed in the non-primary context | if the two contexts disagree on **either** certificate rate at the §13 decision level, the verdict is **`conditioning_sensitive`** and **nothing is concluded about either certificate** |

### 8.5b Adjudication of the S8 conflict (MAJOR-12 SR)

`literature/C0002_literature.md` §Q2.7 states that the percentile rank of `lp_gt` within the candidate
set "and a length-controlled companion comparison **must be co-reported, or the E2 conclusion is not
defensible**", and §Q2.4 item 2 asks for the rank to be promoted to co-primary. The inherited v2.1
§8.3 C2-S6 note forbids any E2/E3 statement from citing it. v1 carried both and resolved the conflict
**silently, in the direction that removed a check on the preferred answer**.

**Frozen adjudication.** Both instruments are right about different things and the conflict is
resolved by making the *reporting* obligation binding while the *inferential* prohibition stands:

1. **S8 is co-reported, mandatorily.** The rank and the length-controlled companion appear in the
   cycle report whenever a P2 result is reported. Omitting either is a contract violation.
2. **S8 bears no decision.** The v2.1 caution is sound on its own terms: the candidates are an extreme
   upper-tail T = 0.1 draw, so a low rank is not evidence of model error. No threshold is applied to
   S8 and no decision branch in §13 reads it.
3. **The literature's precondition is therefore met on the co-reporting limb and NOT met on the
   length-control limb**, because BA2 is predicted `length_control_not_measurable` (§0.0 item 1).
   **This is a further, independent reason why C0002 cannot deliver a supported E2**, and it is stated
   here rather than discovered at reporting time.

### 8.6 Declared limitation that no design can remove

By F-h the decoder's emitted token sequence is unrecoverable from the stored artifacts. `lp_best` in
either context is the score of a **re-spelling** of what the decoder emitted. The inequality
`lp_best ≤ L*` is unaffected — it holds for the maximum over any set of complete sequences — so both
certificates survive. What does not survive is any claim that `lp_best` equals the model score the
decoder assigned to its own output. Every artifact reporting `lp_best` carries
`lp_best_is_respelling: true`; PC-GREEDY's records additionally carry
`lp_greedy_is_respelling: false`, because the greedy pass scores the model's own emitted ids
(MINOR-2 RA).

### 8.7 Frozen reporting sentences (REWRITTEN for two bounds)

Binding on the cycle report, the analysis and any synthesis.

- **Permitted**: "`sb_best`, computed on `lp_gt_max`, is a **certified lower bound** on the
  search-error rate under the preregistered scoring context. It is not an estimate of it. D19-1331's
  own Beam-100 configuration still shows **53.62%** search errors against the exact global argmax, so
  an approximation built on a returned set systematically **undercounts** search errors."
- **Permitted**: "`me_best = 1` certifies that the truth is **not the model's argmax** under this
  conditioning."
- **Permitted, and REQUIRED wherever P1 and P2 are reported together**: "P1 and P2 are two
  **independent** certified lower bounds. Neither refutes the other's proposition: a certified search
  error is compatible with the truth also not being the argmax. C0002 reports no attribution."
- **Forbidden**: any sentence of the form "the search-error rate is X" citing D19-1331, or any
  sentence presenting `sb_best` as an estimate of that rate. D19-1331 defines search errors against
  the exact global argmax from DFS (footnote 5, p. 3358) and never performs a reference-versus-returned
  comparison under any decoding procedure.
- **Forbidden**: "the truth has negligible probability mass under the model." Certificate N bounds
  **nothing** about how much mass the truth has. Rule 01 item 8 applies verbatim.
- **Forbidden**: any claim that more search **would** find the truth on the strength of `sb_best = 1`.
  D19-1331's central result is that the exact global best can be degenerate (51.8% empty translations,
  BLEU 2.1); the SR analogue — a degenerately short expression — is not ruled out here.
- **NEW, forbidden**: **"the failure is prior mass, not search"**, and every variant of it. C0002
  cannot bound the search-error rate from above, so no configuration of P1 supports the "not search"
  half. This sentence appeared in v1 §1.1 and is withdrawn.
- **NEW, forbidden**: "E2 predominant", "E3 predominant" and "the corpus attribution", as statements
  about which failure mode obtains. Where "predominant" is used at all it names a **certificate rate**
  and must say so in the same sentence.
- **NEW, forbidden**: reporting a `C_gen` result without `gt_is_quantized_in_context: true` (§7.3), or
  a P2 result without S8's co-report (§8.5b).

---

## 9. `H0010` — joint versus marginal absence (CPU only)

### 9.1 Predicates, frozen

Computed on each realized candidate **component** expression, derived **from the infix path on both
sides** (rule R1), never by searching a normalized string for a surface token — rule R1 forbids that
explicitly and that exact error occurred twice in C0001.

Let `X = {x_0 … x_5}`, `num, den = sympy.fraction(sympy.cancel(sympy.together(e)))`:

- **`P_den`** = `den.free_symbols ∩ X ≠ ∅`
- **`P_pow4`** = there exists a subexpression `Pow(b, n)` of `e` with `b.free_symbols ∩ X ≠ ∅` and `n`
  an `Integer` with `|n| ≥ 4`. Derivation-path invariant: SymPy normalizes `(x**2)**2 → x**4`, so the
  `pow2∘pow2` and `pow(·,4)` spellings both match.
- **`P_joint`** = `P_den ∧ ((num.free_symbols ∩ X) \ (den.free_symbols ∩ X) ≠ ∅)`

Class key: `str(constants_to_placeholder(_normalize_expr_str(expr)))`, the C0001 replication's own key
(`rep/step3_keys.py`), reimplemented in repository code. **This key is also the
`normalized_input_key` of §5.2 item 2's per-item reseed.**

The `CAS_NODE_BUDGET = 400` admission bound applies to the **parsed `Expr`** (§5.2 item 1); rows
exceeding it are `budget_exceeded_by_input_size`, counted and reported, never silently dropped.
**Measured expected count: 0** (F-l — the maximum `count_ops` over all 89,349 strings is 14).

### 9.2 Gate 2 — the class census, computed **before** the endpoint

End-to-end from the durable artifact `.../phase3/all_candidates.json`
(SHA256 `451e66ec14238335f646c1237e7b32062c681b85b08b8ea8abc20a883488a07a`, 181,594,403 bytes),
reimplemented in repository code.

**The corpus is FROZEN (MAJOR-12 RA).** `H0010` runs on **all 80 systems / 47,987 candidates /
89,349 distinct component strings**, not on the 71 in-support subset. The reason is definitional:
`H0010` is about **generation coverage**, and support is a property of the **truth**, not of what the
decoder generated. v1 never stated which corpus it used, while its decision rule was an integer
comparison — so including or excluding the 5,394 candidates of the 9 excluded systems could flip the
verdict. That is an unfrozen researcher degree of freedom in a confirmatory count, which rule 01
item 3 exists to prevent. The **71-system restriction is reported as a preregistered sensitivity**
(distinct union 74,117), never as the primary.

| quantity | C0001 prose value | status in v2 |
|---|---|---|
| distinct candidate component strings + truth strings, 80 systems | 89,349 | **REPRODUCED EXACTLY by M2** (§0.5, §0.7): 89,179 candidate + 170 truth = 89,349 |
| constant-folded skeleton classes | 879 | **expected**, still unreproduced |
| realized candidate skeleton classes | 846 | **expected**, still unreproduced |
| stored candidates | 47,987 | verified by direct count |

**Gate 2 passes if the census completes and writes `phase1/h0010_class_census.json` with its counts
and a SHA256.** Reproducing the unreproduced prose values is **not** a pass condition: if they do not
reproduce, the discrepancy is reported, those values are marked **unreproduced**, and the endpoint
proceeds on the **realized** counts — exhaustive either way, so the denominator stays known by
construction. A gate that could fail for a reason unrelated to C0002's question must not abort C0002.

**Gate 2a — a timing gate BEFORE the census (MAJOR-13 RA).** v1 said the census budget was "bounded by
the `count_ops` admission rule and by the ≤ 12 CPU core-h Gate-5 projection bar". Neither is a
mechanism: Gate 5 is the *smoke* gate and concerns the GPU pass; v1 fixed no execution order between
them; and F-l shows `count_ops` excludes nothing. The only protection was the global 24 core-h abort,
i.e. the budget was protected by spending it. v2 freezes:

- run the predicate pipeline on a **preregistered random subsample of 5,000** of the 89,349 strings,
  drawn with `GLOBAL_SEED`, record wall time, and require the linear projection to the full corpus to
  be **≤ 8 CPU core-h** before the full census runs. Above it, **RD3** is invoked.
- **Measured lower bound on the cost**: the parse + `count_ops` stage alone is **130.27 s = 0.0362
  core-h** for the full corpus (M2), so the projection's dominant term is `together`/`cancel`/
  `fraction`, which Gate 2a is what measures. M2 did **not** run those (§0.4), so the census cost
  remains the cycle's one unmeasured component — but it is now gated before it is spent, which is what
  v1 lacked.

### 9.3 Endpoints and the frozen rule (REWRITTEN; v1's cutpoint is withdrawn)

Written **before** any of these quantities was measured (§0.4). **The predicate values were not
computed by M2.**

| id | endpoint | role |
|---|---|---|
| **H1** | `n_class_den` — classes with `P_den` | **precondition**, not a prediction |
| **H2** | `n_class_pow4` — classes with `P_pow4` | **verification condition**, not a prediction — see below |
| **H3** | **`n_class_joint`** and **`r_joint = n_class_joint / min(n_class_den, n_class_pow4)`** | **the scientific content** |
| **H4** | the same counts weighted by realized multiplicity over the 89,349 component strings | **conflict check** — **retained, and RD3 may no longer drop it** |
| H5 | the 2 × 2 table of `P_den` × `P_pow4` at class level | descriptive |
| H6 | `n_budget_exceeded_by_input_size` and `n_parse_not_admitted_unbounded` | denominator audit |

**H2 is relabelled (MAJOR-6 SR).** `n_class_pow4 ≥ 10` is justified by C0001's published **11**, and
`P_pow4` (integer `|n| ≥ 4` over any variable-containing base) is a **superset** of C0001's nested-`pow2`
Hill-4 screen. So 11 is a lower bound and the bar passes **by construction**. It is a verification that
the predicate is wired correctly, **not a prediction**, and v2 does not report it as one. The same
holds for H1, which passes by construction from S1 `phi_denom`'s 5,824 / 77,983.

**The frozen graded rule for H3.** v1's `n_class_joint ≤ 5` vs `≥ 6` carried the entire scientific
content with **no stated derivation**, and in a census there is no sampling variability to absorb the
choice, so the cutpoint deterministically fixes the verdict: 5/846 = 0.59% and 6/846 = 0.71% are not
distinguishable by any principle v1 offered. v2 replaces it with a **relative** rule, whose *form* is
derived from the hypothesis's own wording — "the joint is absent **while its marginals are realized**"
— and whose band edges are declared order-of-magnitude conventions, disclosed as such.

| band | reading | verdict |
|---|---|---|
| `n_class_joint = 0` | the joint structure is **never** generated while both marginals are | **`H0010` supported (joint absent)** |
| `0 < r_joint ≤ 0.10` | the joint is generated an **order of magnitude** more rarely than the rarer of its own marginals | **`H0010` supported (joint near-absent)**, reported with `r_joint` and both marginal counts |
| `0.10 < r_joint < 0.50` | intermediate | **`H0010` neither supported nor refuted** — a real, reportable result, distinct from `undecidable` |
| `r_joint ≥ 0.50` | the joint is generated at a rate **comparable to its own marginals** | **`H0010` refuted in the joint direction.** The coverage hole is elsewhere; C0003 goes to the cheaper support / vocabulary side |
| `n_class_den = 0` **or** `n_class_pow4 < 10` | the absence is already at the **marginal** level | **`H0010` refuted in the marginal direction** — the informative negative the design brief names |

**H4's conflict rule, frozen (MAJOR-6 SR).** Five rare classes and five classes covering a third of the
corpus are opposite findings. If the class-level verdict is `supported` but the multiplicity-weighted
count over the 89,349 component strings contradicts it — i.e. the joint-bearing classes account for a
**larger** share of realized strings than the rarer marginal's classes do — the result is reported as
**`H0010_class_vs_multiplicity_conflict`**, **not** as supported. **RD3 may no longer drop H4**, since
H4 is the only quantity that can contradict the class-level verdict.

**The budget rule, bound-shaped (MAJOR-5 SR).** A class that cannot be evaluated for the three
predicates is excluded from `n_class_joint`, which **deflates it, i.e. pushes toward the supported
reading**. Frozen: if the verdict would be `supported` but
`n_class_joint + n_budget_exceeded + n_parse_not_admitted_unbounded` would move it out of the supported
band, the verdict is **`H0010_undecidable_budget_limited`**, not supported.
**Measured expected count of both exclusion classes: 0** (F-l, and 0 / 89,349 parse failures in M2), so
this rule is expected to be vacuous — but it is preregistered because v1 listed the count as "unknown",
and an unknown denominator in the direction of the prediction is the exact failure that made C0001
undecidable.

### 9.4 Exploratory companion `H0011`

The covariate structure of the 42 no-opportunity H components (dimension, `noise_sigma`,
`subsample_rho`, family, with system clustering) is **exploratory** and must be labelled so in every
artifact (rule 01 item 9). It bears no decision. Dimension and family are fully confounded (§2.1).

---

## 10. Controls — every one with a stated expected value, and a stated disposition on failure

C0001's near-fatal defect (MAJOR-R6) was a design whose observable ceiling was 1.3× its target effect
size, so no control could produce a non-zero value of the primary indicator and a zero result was
indistinguishable from a broken instrument. Rule R2 requires the population a control runs on to be
**verified** to have the property the control assumes; its corollary requires controls to run **before**
the expensive endpoint.

**Control cell set**: 40 cells drawn from the 960 cells with `CONTROL_CELL_SEED = 20260911`, stratified
to include ≥ 3 cells from each of the 8 families. Frozen and written to `phase0/control_cells.json`
before any endpoint is computed.

**Every control below now carries an explicit, single-clause disposition** (MAJOR-14 RA). v1 gave
PC-HOLDOUT, NC-HOLDOUT, NC-CONDITION, PC/NC-H0010, the regression identity and the round trip
**thresholds but no consequence anywhere**, which makes R7's "quote the contract text verbatim beside
the check" unsatisfiable — there was no contract text to quote.

| id | construction | threshold | expected value, **measured** | **disposition on failure** |
|---|---|---|---|---|
| **PC-GREEDY** | greedy decode from the cell's cached encoder state (`decoder.generate(..., sample_temperature=None, max_len=200, seed=self.generation_seed)` — `model_wrapper.py:74-81` runs unconditionally, before the `beam_type` branch at `:101/:140`), ids → tokens via `env.equation_id2word`, scored with the same `teacher_forced_summed_logprob_batch`; `1[lp_greedy > lp_best]` | **≥ 2 of 40** | **2 / 10 on a disjoint probe**, margins `lp_greedy − lp_best ∈ [−45.21, +32.29]` nats — **`C_raw`, `unverified_for_C_gen`**. Operating characteristic: `P(X ≥ 2 \| n = 40)` = **0.9985** at a true rate of 0.20, **0.6009** at 0.05, **0.1905** at 0.02 | **ABORT-CLASS.** `H0001-R` is `undecidable (indicator not demonstrated)` and the full pass does not run. A zero P1 would otherwise be indistinguishable from a scorer that cannot produce a 1 |
| **PC-HOLDOUT** | the **highest**-scoring usable candidate of a control cell as pseudo-truth, `sb_best` against the rest | ≥ 0.95 return 1 | 1.000 by construction on any cell with a strict maximum; tied-maximum cells counted and excluded from the denominator | **ABORT-CLASS.** The indicator plumbing cannot produce a 1; `H0001-R` is `undecidable (indicator plumbing not demonstrated)` |
| **NC-HOLDOUT** | the **lowest**-scoring usable candidate as pseudo-truth vs the rest | ≤ 0.05 return 1 | 0.000 by construction | **ABORT-CLASS.** The indicator fires where it must not |
| **NC-CONDITION** | score the truth against an encoder pass built from a cell of a **DIFFERENT system**, drawn per cell with `CONTROL_CELL_SEED` | ≥ 0.95 of control cells show `\|Δ\| > 1` nat | **0.95 measured over 200 cells (M4)** — i.e. **exactly at the bar**, median `\|Δ\|` **13.08** nats, min 0.0091, max 123.88, **0 exact zeros**. `P(pass \| 40 cells, p = 0.95)` = **0.6767** | **DOWNGRADE-CLASS.** The scorer's conditioning-dependence is `not_demonstrated_at_cell_level`; **BA4's context comparison is reported `uninterpretable`**, which by §8.5 BA4 blocks any conclusion resting on context agreement. Not abort-class, because the measured median of 13.08 nats establishes that the instrument does respond — the per-cell binary is what is fragile |
| **NC-SHUFFLE-TOKENS** | score a random permutation of the GT token list | must score **below** the GT encoding, ≥ 0.95 | not separately verified | **REPORT-ONLY.** Downgrades S5 only; gates nothing |
| **PC/NC-H0010** | the 12 frozen synthetic cases of §10.4 | **12 / 12** | **12 / 12 measured** under `sympy 1.13.1`; 4 of the 12 produce `P_joint = True` | **ABORT-CLASS for `H0010` only.** `H0010` is `undecidable (predicate battery failed)`. `H0001-R` is unaffected |
| **regression identity** | `sum_logprob / n_scored_tokens == −teacher_forcing_loss(...)` (`src/gpu_run4/training.py:66-70`) | < 1e-5 on ≥ 5 fixed examples | **CORRECTED (MAJOR-8 RA):** `phase3/partC_instrument_test.json`, 960 checks, `tolerance: 1e-05`, **0 over tolerance**; `identity_error` min **`0.0`** (17 exactly zero), smallest non-zero **`1.2226593959496768e-08`**, max **`2.8991699210223487e-06`**. Realized margin **3.45×**. v1's quoted `7.3e-08 … 8.1e-07` was wrong at both ends | **ABORT-CLASS.** The scorer does not compute what it claims |
| **`C_gen` reconstruction** | **REDEFINED (MAJOR-9 RA):** `env.equation_encoder.encode` → `.decode` → `encode` **token-identity** round trip on control-cell candidates in the primary context. v1's "forward map + inverse recovers the original to 1e-8 relative" is **vacuous** — any invertible map passes it, and it never goes through the tokenizer, so it cannot see the 4-significant-digit constant quantization | ≥ 0.98 | **0.9683 in `C_gen`; 0.9917 in `C_raw`** (M5). **Does not clear in `C_gen`** | **NAMED-CONTINGENCY-CLASS**, §7.3 and §18. Not a silent downgrade: the supervisor's §7.3 decision governs |
| **re-encoding round trip** | §8.2 | ≥ 0.90 per control cell | 300/300 in original units, **`unverified_for_C_gen`**; M5's `C_gen` candidate figure is 0.9683 | **DOWNGRADE-CLASS.** Affected cells become `unreliable_reencoding` per §8.2's own cascade |

### 10.4 PC/NC-H0010 — the 12 frozen synthetic cases

Unchanged from v1 §10.4 and listed verbatim so a reviewer can recompute them. Expected
`(P_den, P_pow4, P_joint)`:

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

---

## 11. Go / No-Go gates

Every condition below is **machine-checkable and must be implemented as a machine check**. R7 is
binding: each gate is implemented by **quoting the contract text verbatim in a comment** beside the
check, clause by clause, not from a summary. C0001 shipped a gate whose text had two clauses and whose
code had one, and Part C ran when it should not have. A gate that reads a derived field must also
assert that the code producing that field matches this contract.

**Every condition in §11 carries exactly one class, and the class is stated in the same row.** There is
no condition anywhere in this document whose disposition must be inferred from a second passage.

- **ABORT** — the named endpoint is `undecidable` and the remaining work for it does not run.
- **DOWNGRADE** — the run proceeds; a named qualifier attaches to the named endpoint.
- **REPORT-ONLY** — counted and reported; no endpoint changes.

**Frozen execution order (MAJOR-13 RA; v1 fixed none):**
`0 → 1 → 2a → 2 → 3 → 4 → 5 → (960-cell pass) → 6`.

**Gate 0 — preflight, before any endpoint.** All ABORT.
1. `git branch --show-current == 20260909_researce_GPU_RUNclaude1`; `git status --short` clean, or
   every entry enumerated and explained in the run manifest.
2. `python -m pytest -q` green, including the new C0002 tests; `GPU_RUN5/tests --collect-only` with
   zero collection errors.
3. Checkpoint SHA256 `56754040be5aa92ed4767fc43ee2008faa293f87c12b643e66c7df3e1623a5e8`.
4. **Every M7 input digest recomputed and equal** (§3), and `phase0/input_fingerprints.json` written
   from `InstrumentedOpener.fingerprints()`. *(NEW — MAJOR-5 RA.)*
5. `phase0/sealed_inventory.json` written with ≥ 7 entries, enumerated from the filesystem, empty
   intersection with the read allowlist; `sealed_paths_read == []` — **with §2.4's caveat recorded
   beside it, since the assertion is necessary but not sufficient**.
6. **`no_directory_argument_reached_run_manifest == true`**, asserted from the routing through
   `safe_run_manifest_data_paths()`, and `run_manifest.py`'s own `main()` verified to call
   `install_sealed_audit_hook()`. *(NEW — CRITICAL-3 RA. This is the check whose absence in v1 would
   have let a subprocess byte-read three sealed files while item 5 still passed.)*
7. GPU 0 idle temperature < 70 °C; free VRAM ≥ 4.0 GiB; disk free ≥ 40 GiB.
8. `results/runs/gpu_runclaude1_c0002_<short7>/` does not already exist.
9. `sympy.__version__ == "1.13.1"`; `sympy.core.random.seed` is callable; **the `multiprocessing`
   start method equals the declared `fork`**; and **the chunk-size invariance test of §5.2 item 2
   passes** — two runs with different `chunksize` produce byte-identical label files. *(NEW — this
   replaces v1's worker-start seed assertion, which proved only the part that was never in question.)*
10. `phase0/control_cells.json` written (40 cells, ≥ 3 per family) **before** any scoring.

**Gate 1 — cell identity.** DOWNGRADE (per cell). Inherited from v2.1 §8.2 step 1, verified over all
960 cells there: `cell_input_payload_sha256` computed; `system_id`, `bundle_index`, `noise_sigma`,
`subsample_rho` parsed from the record equal those encoded in `cell_id`; `candidate_set_hash` and
`cache_identity` match; **10 distinct payloads per system** (verified 80/80 in C0001, 0 violations —
and explained by F-m). Failure ⇒ `CellIdentityMismatch`, cell excluded, counted, reported.

**Gate 2a — `H0010` census timing** (§9.2). ABORT-to-RD3: a projection above 8 CPU core-h invokes RD3;
it does not spend the budget.

**Gate 2 — `H0010` class census** (§9.2). ABORT for `H0010` only. Passes on completion; the
unreproduced C0001 prose values are **expected**, not required.

**Gate 3 — `H0006` encoding enumeration.** See §7.2b for the full table.
**3a: ABORT (80 / 80). 3b: DOWNGRADE (≥ 90%). 3c: REPORT-ONLY (≤ 20%).**
**Gate 6 consults 3a only.**

**Gate 4 — controls, evaluated on 40 cells BEFORE the 960-cell pass.** A failure here costs minutes,
not hours (rule R2 corollary). Classes and dispositions are in §10's table, one row each; they are not
restated here so that there is exactly one contract text per condition for R7 to quote.
PC-GREEDY, PC-HOLDOUT, NC-HOLDOUT, the regression identity and PC/NC-H0010 are **ABORT**;
NC-CONDITION and the re-encoding round trip are **DOWNGRADE**; NC-SHUFFLE-TOKENS is **REPORT-ONLY**;
the `C_gen` reconstruction is **NAMED-CONTINGENCY** per §7.3.
**PC-GREEDY's evaluation context is the PRIMARY context**, stated explicitly (MAJOR-13 SR; v1 never
said), with its achievability labelled `unverified_for_C_gen`.

**Gate 5 — smoke.** ABORT-to-RD. A reduced run on 24 cells completes end to end, writes a manifest,
equation records and failure records, **demonstrates resume per §11b**, and projects the full pass at
≤ **2.0 GPU-hours** and ≤ **12 CPU core-hours**. A projection above either bound invokes §18's reduced
design **before** starting, not midway.

**Gate 6 — report.** `H0001-R` endpoints are reported only if **every ABORT-class condition passed**:
the regression identity; the re-encoding audit within §8.2's tolerances; every scored cell passed
Gate 1; **Gate 3a** (not 3b, not 3c); PC-GREEDY, PC-HOLDOUT and NC-HOLDOUT; the §11b resume-ledger
identity; and BA4 computed. Otherwise `H0001-R` is `undecidable`.

**`wall_clock_guard_fired` is SCOPED, not global (MAJOR-3 RA).** v1 made a single CAS timeout anywhere
turn the **GPU log-probability** primary `undecidable`, while §5.2 itself says no C0002 endpoint depends
on a CAS equivalence decision — a gate that can kill the primary for a reason the contract says is
unrelated to it. And it carried **no achievability evidence**, while the only measurement on record
points the other way: C0001 recorded **9** firings in the run and **7** in the replication over 101,963
comparisons at the identical 10.0 s `SIGALRM` limit. v2 freezes:

- `wall_clock_guard_fired` is **counted and reported per endpoint** (S9).
- A non-zero count on the `H0010` path ⇒ **`H0010`** carries `wall_clock_affected_rows: n` and the
  affected classes are reported; if the affected classes could move the §9.3 band, the verdict is
  `H0010_undecidable_wall_clock_limited`.
- A non-zero count **does not affect `H0001-R`**, which consumes no CAS decision.
- **The 10.0 s limit is NOT raised.** That is forbidden and is not the fix.

**Abort conditions.** Cumulative GPU > **4.0 h**, CPU > **24 core-h**, new disk > **15 GiB**, or peak
VRAM > **5.5 GiB** ⇒ abort, preserve partial artifacts, report what completed. VRAM is additionally
enforced as an allocator cap. GPU 0 > 85 °C sustained 60 s ⇒ pause, cool, resume once.
**Crash-loop rule: 3 consecutive identical fatal failures with no new diagnostic information ⇒ stop and
reassess** (rule 06). Preregistered VRAM fallback chain, in order: batch size 1 → the reduced 24-cell
design → GPU 1 (GTX 1060 3 GB, forward-only, batch 1). The chain changes **which cells** are scored,
never the numerics.

### 11b Resume semantics — defined (MAJOR-6 RA)

v1 required Gate 5 to "demonstrate resume" and defined the word nowhere: no resume unit, no ordering
rule, no double-count protection, no ledger. v1's own abort conditions contemplate restarts, so a
restart is an expected path, not an exceptional one. C0001 v2.1 had an explicit write-before-match
ordering requirement (`v2.1.md:2193`); v1 dropped it. Frozen:

1. **Resume unit** = one `(cell_id, scoring_context)` pair.
2. **Ordering**: a unit's records are written **and `fsync`ed**, and only then is its id appended to
   `phase4/completed_units.jsonl`.
3. **On restart**: units present in the ledger are **skipped**; any `partI_*.jsonl` lines belonging to
   units **not** in the ledger are **truncated** before work resumes.
4. **Denominators are computed from the ledger**, never from line counts.
5. **Gate 6 check**: `len(ledger) == number of distinct units == number of record groups`.

---

## 12. Statistical plan

### 12.1 Estimators and the interval of record (REWRITTEN; CRITICAL-4, CRITICAL-5, MAJOR-1, MAJOR-11 SR)

**The estimand governs the resampling unit.** §2.2 makes **systems** the random draws and the **eight
families fixed strata**. v1 resampled the 8 families with replacement, which targets a superpopulation
of *families* that §2.2 does not posit — the same random-family / fixed-family contradiction that
helped render C0001 undecidable.

| endpoint class | estimator | **interval of record** |
|---|---|---|
| P1, P2, S11 (system proportions) | plain proportion **`Σ_s indicator / n_eval`**, `n_eval` the realized evaluable-system count (§2.1b) | **the bound-by-bound more conservative of (a) a stratified bootstrap resampling systems WITH replacement WITHIN each of the 8 fixed families, `CLUSTER_BOOTSTRAP_SEED = 20260911`, 10,000 resamples, percentile method, and (b) the Wilson interval on `n_eval`** — i.e. `min` of the two lower bounds and `max` of the two upper bounds |
| paired nat differences (S3) | mean of system means | the same stratified bootstrap |
| `H0010` counts | exhaustive counts over a **frozen** corpus (§9.2) | **no interval**. Every artifact carries `interval_interpretation: "deterministic_census_no_sampling_variability"` |
| control rates | proportion over 40 | Wilson, descriptive |
| cell-level rates (S2) | proportion over the stated cell denominator | Wilson, **labelled cell-level**, never compared to a system-level rate |

**The bootstrap statistic is named explicitly (MAJOR-1 SR).** It is `Σ_s indicator(s) / n_eval` with
`n_eval` **fixed at its realized value** across resamples. Under the *stratified* scheme each resample
draws exactly `n_f` systems from family `f`, so the denominator is `n_eval` by construction and the
pathology v1's scheme had — resampled families of unequal size producing intervals **exceeding 1.0**
(e.g. `[0.831, 1.127]`) — cannot arise.

**The degenerate-bootstrap special case is DELETED (MAJOR-11 SR).** v1 substituted Wilson-on-8-clusters
only at exact degeneracy, which made the width of the interval of record jump by ~30× on an
exact-equality test, with the substitute **wider than the procedure it substituted for** — a
discontinuity, not a conservative fallback. v2's "more conservative of the two, always" is continuous
by construction and handles degeneracy with no special case: at 0 / 80 it returns `[0, 0.0458]` and at
80 / 80 `[0.9542, 1]`, both from the Wilson limb.

**Measured operating characteristics (M3, §0.7)**, at 80 systems in 8 fixed families of 10:

| true p | v1's estimator | **v2's interval of record** |
|---|---|---|
| 0.20 | 0.908 | **0.960** |
| 0.35 | 0.904 | **0.958** |
| 0.50 | 0.910 | **0.942** |
| 0.65 | 0.916 | **0.964** |
| 0.80 | 0.922 | **0.968** |

### 12.2 Multiplicity — Holm is DELETED and replaced with the correct argument (MAJOR-2 SR)

v1 declared "{P1, P2} … Holm-corrected at family-wise α = 0.05" while defining **no null hypothesis, no
test statistic and no p-value** anywhere, and while §13's rules used **uncorrected** interval bounds.
The declared FWER was delivered by nothing in the document. Holm is also the wrong instrument here.

**Frozen:**

- **No p-value is defined and none is computed.** Every decision in §13 is a one-sided interval
  condition on P1 or on P2.
- **Each branch of §13 is an intersection–union test (IUT).** The `certified_non_argmax_prevalent`
  branch is a **conjunction** of one-sided conditions (P2's lower bound, plus the §8.5 battery), and an
  IUT attains level α with **each component at level α**. **No multiplicity correction is required and
  none is applied.**
- The **one-sided error rate carried by each branch is 0.05**, stated explicitly in the cycle report
  beside the branch that fired.
- The P1 branch and the P2 branch are **logically mutually exclusive as indicator statements**
  (`E3_system` and `E2_system` cannot both hold for a system, and both lower bounds cannot exceed 0.5),
  so the multiplicity exposure across branches is nil. **This is a fact about the indicators and must
  not be restated as a claim that the propositions E2 and E3 are exclusive** — §1.1 establishes they
  are not.

### 12.3 Non-significance is not equivalence (rule 01 item 8)

Binding sentences, carried forward and extended:

- A `P1` whose interval includes 0 does **not** establish that search errors are absent. It establishes
  that, under this conditioning and this candidate set, the certificate did not fire.
- A `P2` near 1 does **not** establish that the truth has negligible probability mass. It establishes
  that the truth is not the argmax.
- **NEW**: a low `P1` does **not** bound the search-error rate from above, so it is not evidence that
  the failure is "not search". §8.7 forbids that sentence outright.
- **No equivalence test is preregistered and none may be run post hoc.** An equivalence claim requires
  its own preregistered margin, which this contract does not set, because no defensible margin on a
  log-probability difference is available.
- Any zero or near-zero count is reported with its denominator and its Wilson bound, never as "no
  effect".

### 12.4 Power and operating characteristics (REWRITTEN; CRITICAL-5 SR)

**v1's disclosure is withdrawn.** v1 said "a family-clustered 95% interval on a mid-range proportion
will be roughly 0.3–0.5 wide" and that a wide interval was therefore the expected hazard. Simulated
realized widths of v1's own estimator on mid-range proportions are **0.10–0.24**, and on a
family-homogeneous corpus as little as **0.0231** — wrong by up to an order of magnitude, **and wrong
in the dangerous direction**: it inoculated the reader against an uninformatively wide interval when
the actual hazard was a spuriously **narrow, undercovering** one straddling the 0.5 cutpoint. At
`p̂ = 0.5070` v1's estimator returns a lower bound of exactly **0.5000**.

**v2's disclosure, computed from the estimator actually preregistered (M3):**

- Coverage is **0.942–0.968** against nominal 0.95 across true rates 0.20–0.80.
- Realized widths on mid-range proportions are ≈ **0.21** at `n_eval = 80`.
- **No branch of §13 can fire below `p̂ = 48 / 80 = 0.600`** (the Wilson limb requires k ≥ 48; the
  stratified limb can require more). This is the minimum point estimate at which a one-sided 95% lower
  bound exceeds 0.5, and it is stated in advance so that a `neither` outcome is not later read as a
  failure of the experiment.
- **`neither_certificate_prevalent` is a plausible corpus-level outcome by construction**, and the
  deliverable is then the **per-system partition**, which is well defined regardless of interval width.

---

## 13. Supported / unsupported / undecidable — THE PRIMARY DECISION RULE (REWRITTEN)

v1 §13 is withdrawn in full. It framed the cycle as **one attribution** over mutually exclusive
alternatives (CRITICAL-3 SR, retracted by the supervisor in `hypotheses/C0002_selection.md`), and it
made "the family-clustered 95% **upper** bound of **P1** < 0.5" one of the two conditions for
concluding E2 — reading a **certified lower bound** in the direction where it carries no information
(CRITICAL-2 SR), in direct contradiction of v1 §8.7 three sections earlier. **That condition is
deleted and does not appear anywhere in v2.**

### 13.1 What is reported, always

**Two independent certified lower bounds, side by side, with no attribution:**

> **P1** lower-bounds the rate of systems on which a **search error is certified** on at least half of
> the system's usable cells.
> **P2** lower-bounds the rate of systems on which the truth is **certifiably not the model's argmax**
> on **every** usable cell.
> **Both may be high. Neither refutes the other's proposition.** C0002 cannot bound the search-error
> rate from above and makes no claim of the form "the failure is X, not Y".

Reported beside them, always: `n_eval` and the nominal 80; the per-system usable-cell distribution;
the `neither_cert` rate with its denominator; the realized value of **every** §8.5 audit; S8's
co-report (§8.5b); and S11's in-support subgroup read.

### 13.2 The branches

Let `LB(·)` denote the one-sided 95% lower bound under §12.1's interval of record, in the primary
context.

| verdict | condition | what it licenses |
|---|---|---|
| **`H0001-R` refuted — certified search error prevalent** | `LB(P1) > 0.5` | a search error is certified on the majority of systems. **`H0003` (temperature / beam sweep) fires on evidence.** It does **not** license any statement about whether the truth is also non-argmax |
| **`certified_non_argmax_prevalent`** *(the supported-E2-direction branch)* | `LB(P2) > 0.5` **AND** BA1 did not fire **AND** BA2 both **ran and passed** **AND** BA3 did not fire **AND** BA4 showed no context disagreement **AND** NC-CONDITION passed | the truth is certifiably not the model's argmax on the majority of systems, with all four known biases audited. **This branch is NOT reachable in C0002** — BA2 is predicted `length_control_not_measurable` at 0.4625 (§0.0 item 1, §8.5). It is written out in full anyway, because a branch that is unreachable must be visible as such rather than absent |
| **`E2_direction_observed_but_length_unaudited`** | `LB(P2) > 0.5` **AND** BA2 is `length_control_not_measurable` | **the strongest E2-direction outcome available in C0002.** The certificate fired; the length confound that D19-1331 identifies as central could not be audited on this corpus. **This is NOT a supported E2 and may not be cited as one, in any artifact, at any stage** |
| **`E2_direction_observed_but_confounded`** | `LB(P2) > 0.5` **AND** BA2 ran and **failed** its disagreement bar, or BA1 fired, or BA3 fired | as above; **not a supported E2** |
| **`certificate_opportunity_insufficient`** | BA1 fired (median system-level `argmax_agreement_best` ≥ 0.95) | `lp_best ≈ L*`, so Certificate S was nearly unable to fire and **P1 carries no information**. The falsifier is **unevaluable**. Reported instead of P1 |
| **`conditioning_sensitive`** | BA4 shows the two contexts disagree at the decision level, **or** NC-CONDITION failed so BA4 is `uninterpretable` | **nothing is concluded about either certificate** |
| **`neither_certificate_prevalent`** | neither lower bound exceeds 0.5 and no instrument failure | a real, reportable result, explicitly distinct from `undecidable`. The deliverable is the per-system partition |
| **`undecidable`** | **instrument failure only**, enumerated exhaustively: any **ABORT-class** Gate-4 condition failed (PC-GREEDY, PC-HOLDOUT, NC-HOLDOUT, the regression identity); **Gate 3a** failed; Gate 6's conjunction failed; the §11b ledger identity failed; or > 10% of cells are `unreliable_reencoding` | — |

**`wall_clock_guard_fired > 0` is NOT in the `undecidable` list for `H0001-R`.** v1 put it there; §11
scopes it to `H0010`, which is the only endpoint that consumes a CAS decision.

**`H0010`**: supported (joint absent) / supported (joint near-absent) / neither / refuted-in-the-joint
-direction / refuted-in-the-marginal-direction, per §9.3's graded rule; plus
`H0010_class_vs_multiplicity_conflict`, `H0010_undecidable_budget_limited`,
`H0010_undecidable_wall_clock_limited`, and `undecidable` if Gate 2 does not complete or the predicate
battery fails 12/12.

### 13.3 Every branch is informative — restated honestly

- `LB(P1) > 0.5` fires `H0003` on evidence for the first time.
- `E2_direction_observed_but_length_unaudited` — the outcome §0.0 predicts — is **still informative**:
  it establishes the certificate rate, it establishes that the length confound is **structurally
  unauditable on this corpus** (0.6302 of cells have a truth longer than every candidate), and it makes
  the design of a corpus that *can* audit it the content of C0003. What it does **not** do is close
  `H0003`, and v1's claim that an E2 result would close `H0003` "permanently" is withdrawn.
- `neither_certificate_prevalent` is reported as such.
- A cycle report is written regardless (`.claude/rules/08-cycle-persistence.md`).

---

## 14. Compute ceiling and the measured cost basis

Ceilings (`research_state.md` §5): ≤ **4.0 GPU-h**, ≤ **24 CPU core-h**, ≤ **5.5 GiB** peak VRAM,
≤ **15 GiB** new disk.

**Measured on this hardware** (RTX 2070, fp32, batch of 51 sequences against one cached encoder pass,
`compute_ranks=True`): 8 cells / 408 sequences = **7.0 s GPU**, 2.1 s CPU preparation; peak VRAM
**0.458 GiB**; projection to 960 cells one context = **0.233 GPU-h**; tokenization + re-encoding +
audit + scaling map ≈ **0.07 s per candidate**.

| component | GPU-h | CPU core-h | disk |
|---|---|---|---|
| primary pass, **960** cells × 2 contexts | 0.47 | — | — |
| `H0006` orbit members (cap 8) × 2 contexts | 0.08 | — | — |
| PC-GREEDY, 40 cells | 0.03 | — | — |
| smoke, 24 cells × 2 contexts | 0.02 | — | — |
| re-encoding / tokenization, 47,987 × 2 | — | 1.9 | — |
| **`H0010` parse + `count_ops` (MEASURED, M2)** | — | **0.04** | — |
| `H0010` predicate census (`together`/`cancel`/`fraction`) | — | ≤ 8, **gated by Gate 2a** | — |
| controls, audits, records | 0.01 | ≤ 2 | — |
| **total** | **≈ 0.61** | **≈ 12** | **see below** |
| **ceiling** | **4.0** | **24** | **15 GiB** |
| **margin** | **≈ 6.6×** | **≈ 2×** | — |

Peak VRAM projects to **< 1.0 GiB** against a 5.5 GiB ceiling. GPU 0 is shared with the user's live
desktop (569 MiB held, 42 °C at the last check), which the allocator cap accounts for.

**Disk arithmetic, shown (MINOR-8 RA; v1 asserted "< 1 GiB" with no derivation).**
`partI_candidate_records.jsonl` carries 47,987 candidates × 2 contexts = 95,974 rows, each with the
§16.2 schema **plus** per-token log-probabilities and ranks. At a median GT/candidate length of ~30–50
tokens and ~16 bytes per float in JSON, the per-token arrays alone are ~1–2 KB per row, and the
copied rule-03 fields are ~1–2 KB more, giving **≈ 0.3–0.5 GiB** for that file. `partI_cell_records`
and the audit JSONs are small. **Projected new disk ≈ 1 GiB, bounded at 2 GiB**; if the realized size
exceeds 2 GiB the per-token arrays are written to a separate `.npz` sidecar rather than inline, which
is a format change, not a data loss. The 15 GiB ceiling has ~7× margin either way.

**The `H0010` predicate census is the only unmeasured component.** Unlike v1, it is now **gated before
it is spent** (Gate 2a), not merely "bounded by" a projection that ran after it.

---

## 15. Failure policy, exclusions, and their expected counts

All frozen. Every excluded row is retained with its reason (rule 03 / rule 01 items 4–5); nothing is
deleted. **Every expected count below is either measured or explicitly marked unknown.**

| rule | expected count | disposition |
|---|---|---|
| candidate `valid: false` | **0** (47,987 / 47,987 valid, counted) | excluded from `lp_best`, retained with `failure_reason` |
| `rescale_function_early_return_suspected` | **unknown** — `unverified` (§7.1, MAJOR-11 RA) | candidate excluded in `C_gen`, counted, reported; **never transformed** |
| `CandidateReencodingMismatch` | **≈ 0** in original units (300/300); **`unverified_for_C_gen`**, where M5 measures 0.9683 token identity | excluded from the comparison distribution, counted |
| cell `unreliable_reencoding` (> 10% mismatch) | **≈ 0** in original units; `unverified_for_C_gen` | excluded from P1/P2, reported separately. > 10% of cells ⇒ `undecidable` |
| `CellIdentityMismatch` | **0** (10-distinct-payload check verified 80/80 in C0001) | cell excluded, counted |
| `EncodingVerificationFailure` | orbit members only; `e1`/`e2` verified 80/80 | member dropped, counted; **Gate 3c is REPORT-ONLY** |
| `neither_cert(c)` | **unknown, expected small** — bounded by `Δ_maxlse ≤ log\|E(s)\| ≤ 2.303` nats | counted, **reported with its denominator**, excluded from both `sb_rate` and `me_rate` |
| `tie(c)` | unknown, expected ≈ 0 | counted, reported, a boundary case of `neither_cert` |
| `system_not_evaluable` (§2.1b) | **0** expected — all 80 systems currently have 12 cells, 3 per corruption setting | system excluded from **numerator and denominator**; `n_eval` reported |
| `budget_exceeded_by_input_size` | **0** — **MEASURED** (F-l: max `count_ops` = 14 over 89,349 strings) | counted, reported; §9.3's bound-shaped rule applies |
| `parse_not_admitted_unbounded` | **0** — **MEASURED** (0 / 89,349 parse failures, M2) | counted, reported |
| `wall_clock_guard_fired` | **non-zero is EXPECTED** — C0001 recorded 9 and its replication 7 over 101,963 comparisons at the same 10.0 s limit | counted **per endpoint**; affects `H0010` only (§11). **v1's "must be 0" is withdrawn as unevidenced and as coupling the GPU primary to an unrelated subsystem** |
| `equals_NONE` | **0** (realized 2,191 pairs) | recorded as `equals_raw: null`, never coerced |

**No outcome-dependent exclusion is permitted.** In particular the 8 cells of §0.3 are **not** excluded,
and no cell may be excluded after its indicator is known.

---

## 16. Artifact contract and record schema

### 16.1 Run and artifacts

Run id `gpu_runclaude1_c0002_<short7>` derived from the freezing commit; if the directory exists,
append `_v2`, never overwrite (rule 05).

```
results/runs/gpu_runclaude1_c0002_<short7>/
  phase0/{manifest,sealed_inventory,control_cells,preflight,input_fingerprints}.json
  phase1/{h0010_census_timing,h0010_class_census,h0010_endpoints,h0010_control_battery}.json
  phase2/{h0006_encoding_sets,h0006_gate}.json
  phase3/{controls_gate4,smoke_projection}.json
  phase4/{partI_cell_records.jsonl,partI_candidate_records.jsonl,completed_units.jsonl,
          partI_endpoints,partI_bias_audit,partI_instrument_audit}.json
  manifest.json, gpu_telemetry.jsonl
```

`scripts/ops/run_manifest.py` records git commit and branch, `pip freeze`, GPU and driver, and the
checkpoint SHA256.

> **BINDING, reinstated verbatim from C0001 v2.1 §2.4 item 6 (CRITICAL-3 RA):
> `scripts/ops/run_manifest.py --data-path` receives only individual files from that allowlist.
> [Passing a directory] is forbidden.**

Every invocation routes through `io_allowlist.safe_run_manifest_data_paths()`;
`assert_no_directory_argument()` is called on every path; `run_manifest.py`'s own `main()` installs
`install_sealed_audit_hook()`; and **Gate 0 item 6 and every phase boundary assert that no directory
argument reached it**. **v1 §16.1's "a recursive data-tree fingerprint" is struck** — that is exactly
`tree_sha256`'s `rglob("*")` + `sha256()` over every file, in a **separate process** the phase's guards
do not cover, and Gate 0's `sealed_paths_read == []` would still have passed. Large artifacts need not
be committed; hashes and paths are preserved (rule 05).

### 16.2 Record schema (rule 03)

**Every rule-03 field below is COPIED from the stored artifact with provenance, NOT recomputed**
(MINOR-1 RA). All of them are present in the stored 24-key candidate schema, and `true_formula` /
`true_prefix` / `tree_encoded` / `variable_to_gene` are present in the cell and `validation.json` rows.
Recomputing them would run `symbolic_recovery` 47,987 times, reintroducing the 10 s `SIGALRM` into the
run and putting §11's wall-clock scoping immediately in play. Each copied field carries
`source_artifact` and `source_run_sha256`.

Fields: `candidate_formula_raw`, `candidate_formula_canonical`, `candidate_formula_skeleton`,
`candidate_exponent_aware_skeleton`; the ground truth (`true_formula`, `true_prefix`, `tree_encoded`);
the variable mapping (`variable_to_gene`); numerical fit (`trajectory_metrics`: `input_nrmse`,
`selection_nrmse`, `generalization_nrmse` and their R²); recovery (`canonical_exact`, `skeleton_exact`,
`exponent_aware_skeleton_exact`, `component_exponent_aware_skeleton_exact`); structural distance
(`ted_raw`, `ted_skeleton`, `normalized_ted`, `normalized_variable_aware_ted`,
`variable_aware_ted_definition`); `complexity`; `valid`; `failure_reason`.

**The `expression_safety` clause is STRUCK (MAJOR-4 RA).** v1 mandated "the singularity / integration
diagnostics **already produced by** `expression_safety`". That is false four ways: none of
`has_tan` / `has_division` / `near_singularity` / `extrapolation_valid` / `extrapolation_extreme` is
among the stored 24 keys; `expression_safety` is reached only from
`equation_metrics.py:374,398 score_prediction`, which the GPU_RUN5 phase-3 pipeline never calls, so
satisfying the clause would mean running it on 47,987 candidates with **no budget line**;
`equation_metrics.py:329` is `lambdify(["x_1", "x_2", "x_3"], ...)` with `:330-331` padding to 3
columns, while GRN systems use `x_0 … x_5` at `max_dimension = 6`, so any expression containing `x_0`,
`x_4` or `x_5` **raises**; and `:338-339` is
`except Exception: base["near_singularity"] = 1.0 if base["has_division"] else 0.0`, a hidden fallback
that **records a failure as a result** by degenerating to a substring test on `"/"`, with no label.
That is the same class of defect as F-b, inside a routine v1 mandated.

**Rule 03's singularity / validity item is instead carried by fields that actually exist**: the stored
`structure` flags and `trajectory_metrics.*_failures`, cited by name and copied with provenance.
`equation_metrics.py:338-339` is recorded in `research_state.md` §8 as a repository-level known defect;
**C0002 does not call it and does not rely on it.**

**Rule 03's three-way distinction is carried at the endpoint-name level**, as the literature record
requires (ND2 and TPSR both collapse it; this campaign deliberately does not):

- `generation_coverage_scope: "cell"` — what the beam contained.
- `lp_best`, `oracle_*` — **oracle over the generated set**.
- **selected**: **not measurable on GRN this cycle.** Every record carries
  `selected_candidate_measurable: false` with
  `reason: "no per-candidate decoder score is stored (F-e); candidate_index==0 is the highest-input-R2 candidate (F-f), not a decoder argmax"`.
  **No endpoint name contains `selected`.**

Additional C0002 fields: `scoring_context ∈ {"C_gen","C_raw"}`, `lp_best_is_respelling: true`,
`lp_greedy_is_respelling: false` (PC-GREEDY records only), **`lp_gt_is_lower_bound_over_capped_enumeration: true` (unconditional)**,
**`gt_is_quantized_in_context`**, `encoding_set_size`, `encoding_verification_failures`,
`certificate_carrier: {"sb_best": "lp_gt_max", "me_best": "lp_gt_lse"}`, `neither_cert`, `equals_raw`,
`cas_outcome`, `n_eval`, `prior_information_disclosed: "C0002_preregistration_v2.md §0"`.

---

## 17. Rule 04 — layer analysis contract

**No layer-wise estimand is measured in this cycle.** No probe, no CKA, no gradient norm, no ablation,
no IOLE, no selective fine-tuning. Nothing in this contract produces a layer ranking and nothing may be
averaged into one. `H0007` (the layer-side question) is untouched and may not be ranked against the
generation-side endpoints here.

---

## 18. Deviation policy and reduced designs

- Any departure is recorded as a dated `DEVIATION-nn` block appended to a **successor** version of this
  file, naming what changed, why, who decided, and what it invalidates. **v1 and v2 are never edited.**
- **A threshold may never be raised to rescue a result** (rule 01 item 3). A timeout increase, a cap
  increase, a tolerance relaxation or a seed change for that purpose is forbidden without exception.
- **Preregistered reduced designs** (invoked at Gate 5 or Gate 2a *before* starting, never midway):
  - **RD1** single context (the primary only), with BA4 reported `not_measurable` — and, since BA4 then
    cannot clear, **a supported E2 is blocked** under RD1 as well.
  - **RD2** the 24-system fixed GRN validation panel instead of 80 systems, with P1/P2 reported
    `exploratory` and concluding nothing. **Note (m-1 SR)**: §12.1's interval has no degenerate special
    case, so it survives RD2's unequal strata without the arithmetic accident v1's substitute relied on.
  - **RD3** `H0010` census restricted to the realized classes without multiplicity weighting.
    **AMENDED: H4 may NOT be dropped** (MAJOR-6 SR) — it is the only quantity that can contradict the
    class-level verdict. RD3 instead restricts the multiplicity weighting to the realized classes.
- **Named contingency**: if the `C_gen` reconstruction fails Gate 4 — which M5 predicts (§7.3) — the
  supervisor's §7.3 decision governs. If it is the fallback, `C_raw` becomes primary, **every
  Certificate-S statement is downgraded** to "the truth outscores all 50 candidates under a conditioning
  the search did not see", which is not a search-error claim, **and the collapse of §0.3's containment
  is disclosed in the cycle report as a validity threat.**

---

## 19. Replication gate (rule 07)

Fires on any of: **either certified lower bound reported as prevalent**; `H0010` supported in either
band; any result an independent reviewer marks fragile; or any result resting on a single seed or a
single context. *(v1's trigger said "an E2 or E3 corpus attribution"; after §13 the word "attribution"
is gone and the trigger is restated on the certificate rates — m-5 SR.)*

The minimum replication changes **at least one independent factor**: a fresh process and artifact path;
a different `CONTROL_CELL_SEED`; the other scoring context; or an independent re-derivation of
`lp_best` from a separately written scorer. The confirmation is recorded separately under
`GPU_RUNclaude1/replications/` with one of `replicated` / `directionally replicated` /
`failed replication` / `inconclusive`.

**A C0002 certificate rate may not invalidate a GPU_RUN5 result on its own.**

---

## 20. Required reviews before the full experiment

v1 was reviewed by `lansr-statistical-reviewer` and `lansr-reproducibility-auditor`, independently of
the author and of each other. **This document is the response to those reviews and has not itself been
reviewed.** It must not be described as reviewed.

The supervisor's check before freezing should confirm, at minimum:

1. that §23's disposition is accurate — every CRITICAL and MAJOR fixed, downgraded with a stated
   reason, or accepted as a limitation with its consequence;
2. the **three decisions in §0.0** — that a supported E2 is unavailable, that the cycle reports two
   bounds rather than one attribution, and the §7.3 `C_gen` / `C_raw` fork;
3. that no threshold was moved to make a result likelier or a design passable (§0.9);
4. the adjudication of §8.5b, which v1 resolved silently.

`lansr-independent-reviewer` reviews the completed cycle separately (rule 07) and must be distinct from
implementation and primary analysis.

---

## 21. Found unimplementable, or implementable only in a weaker form

Reported rather than quietly dropped. v1's six items are carried forward and extended.

1. **"`could_not_evaluate` on a deterministic node/operation budget."** A genuine operation-count or
   iteration budget *inside* a SymPy call does not exist and cannot be added without patching SymPy.
   egg's runners have it; SymPy has no analogue. §5.2 implements the *property* — an outcome that is a
   function of the inputs alone — via an **admission** bound on the parsed `Expr`, a **per-item**
   deterministic reseed, and three-valued recording. **Weaker than the requirement as written:** it
   makes admission deterministic, not termination. **Three further shortfalls, conceded (MAJOR-2 RA):**
   the parse itself is unbounded and is labelled `parse_not_admitted_unbounded`; `_timed_simplify`'s
   call sites evaluate `sympify` **outside** the `_time_limit` guard and must be fixed; and `count_ops`
   is not monotone with `cancel`/`simplify` runtime on rational functions, so a 400-node bound does not
   bound `cancel`. F-l measures the bound to be **inert** on this corpus.
2. **"The Schwartz–Zippel numerical certificate as a declared arbitration procedure."** Not adopted.
   The bound is stated for polynomials over a field; GRN skeletons are rational functions with variable
   denominators, and the clearing-of-denominators and pole-avoidance argument is not established in any
   primary source (`literature/C0002_literature.md` §Q7 item 6).
3. **"Realized denominators known by construction for both hypotheses."** True for `H0001-R` (80 / 960 /
   47,987, counted). **Partly true for `H0010`**: M2 reproduces the **89,349** corpus size exactly from
   the durable artifact, but the **class** counts (846 / 879 / 877 / 2,191) remain unreproduced prose
   and §9.2's gating census still regenerates them before the endpoint.
4. **"`candidate_index == 0` is sample order."** False (F-f). It is the highest-input-R² candidate. The
   conclusion that it cannot serve as `lp_sel` is unchanged and strengthened.
5. **"Score the candidates the model produced."** Impossible from the stored artifacts (F-g, F-h). The
   emitted token sequence is unrecoverable; every `lp_best` here is the score of a re-spelling. The
   certificates survive; the identification with the decoder's own score does not. **The largest single
   validity limitation of the cycle.**
6. **"Three mechanisms bias the read toward E2."** There are **four**: the conditioning mismatch (F-g)
   is a fourth and its direction is unknown. BA4 measures it.
7. **NEW — "A length-controlled companion comparison, as the literature requires."** **Not achievable on
   this corpus at any admissible partner floor** (§0.0 item 1). On 0.6302 of cells the truth is
   token-longer than every candidate, so there is no in-corpus comparison that removes the confound —
   window-matched, length-adjusted or otherwise. The consequence is that a supported E2 is unavailable
   in C0002 and that designing a corpus that *can* audit the confound is C0003's content.
8. **NEW — "A distinct `e1`/`e2` pair in the primary context."** Not achievable in `C_gen` (F-j):
   scoring the stored `tree_encoded` there requires decode → scale → re-encode, which is `e2`'s own
   path, and the two coincide on 120 / 120 cells. Gate 3b in `C_gen` rests on orbit members alone and
   its achievability there is **`unverified`**; 3b is therefore a downgrade condition only (§7.2b).
9. **NEW — "PC-GREEDY's achievability in the primary context, before freeze."** Not measurable without
   violating §0.4, since it requires `lp_best` under `C_gen`. The 2 / 10 probe stands as a `C_raw`
   figure and the abort risk is disclosed instead: `P(X ≥ 2 | n = 40)` = 0.6009 at a true rate of 0.05
   (MAJOR-13 SR).
10. **NEW — "An interval of record that is both correct for the estimand and informative at this
    sample size."** §12.1's interval is correct for §2.2's estimand and covers at 0.942–0.968, but it
    cannot fire a branch below `p̂ = 0.600` (§12.4). That is a real loss of power relative to v1's
    estimator, and it is the price of correctness, **not** a defect to be optimized away.

---

## 22. Compact statement of what is frozen

Primary `H0001-R` as **two independent certified lower bounds**, not an attribution; the rewritten
falsifier; **P1** `certified_search_error_system_rate` and **P2** `certified_non_argmax_system_rate`
over **all 80** systems in the primary context, denominator `n_eval`; the `0.5` system cutpoint and
`E3_system(s) = 1[sb_rate(s) ≥ 0.5]` **inherited verbatim from v2.1 §8.3 (2026-09-09)**, with
`E2_system(s) = 1[me_rate(s) = 1]` re-expressed on the quantity that certifies it and **strictly harder
to satisfy** than v1's form; **`sb_best` on `lp_gt_max` and `me_best` on `lp_gt_lse`**, with
`neither_cert` counted and reported; `lp_best` = max over usable candidates; the usable-candidate /
usable-cell / evaluable-system definitions and the ≥ 8-of-12 + all-four-corruption-settings floor; the
two scoring contexts and the §7.3 primacy decision; **Gate 3 split into 3a ABORT / 3b DOWNGRADE /
3c REPORT-ONLY**, with Gate 6 consulting 3a only; the control battery **PC-GREEDY ≥ 2/40,
PC-HOLDOUT ≥ 0.95, NC-HOLDOUT ≤ 0.05, NC-CONDITION ≥ 0.95 with a different-system partner,
PC/NC-H0010 12/12, regression identity < 1e-5, `C_gen` reconstruction ≥ 0.98 as a tokenizer round
trip**, each with **exactly one** disposition, all evaluated before the expensive pass; the four bias
audits **with BA1, BA2 and BA3 blocking**; `H0010`'s three predicates, its **frozen 80-system /
89,349-string corpus**, the **graded relative rule** of §9.3, H4's conflict rule and the bound-shaped
budget rule; the interval of record as **the more conservative of a within-fixed-family stratified
bootstrap and Wilson on `n_eval`**, with **no** Holm and **no** degenerate special case; seeds
`20260911` and `77771`; the `fork` start method; the per-item SymPy reseed; `N_WORKERS = 6`;
`CAS_NODE_BUDGET = 400`; the `run_manifest.py` directory prohibition; the §11b resume ledger; the
exclusion rules and their measured expected counts; the compute ceilings; the artifact contract; and
the reporting sentences of §8.7.

**Not frozen, because it is a draft**: everything above awaits the supervisor's check (§20).

---

## 23. Disposition of every CRITICAL and MAJOR from both reviews

**Nothing is silently dropped.** Every finding is `FIXED`, `FIXED IN PART + ACCEPTED LIMITATION` with
its consequence stated, `DOWNGRADED` with a stated reason, or `ACCEPTED LIMITATION` with its
consequence stated. `SR` = `reviews/C0002_preregistration_statistical_review.md`;
`RA` = `reviews/C0002_preregistration_reproducibility_audit.md`.

**Counts.** CRITICAL 10 → **10 FIXED** (9 rows: SR-C1 and RA-C1 are the **same finding**, reached
independently on different grounds, and share one row). MAJOR 27 → **25 FIXED, 2 FIXED IN PART +
ACCEPTED LIMITATION**. MINOR 13 → **12 FIXED, 1 ACCEPTED**. **No finding was resolved by moving a threshold**, and both
reviewers independently noted that none of their required changes needed one.

### 23.1 CRITICAL

| # | finding | resolution | where |
|---|---|---|---|
| **SR-C1 / RA-C1** *(the convergent CRITICAL — found independently on different grounds)* | `lp_gt` is a logsumexp, so `sb_best` is not a certificate; `L* ≥ lp_gt` fails and P1's "certified lower bound" is a claim the endpoint cannot support, while §8.7 makes that sentence binding | **FIXED.** `sb_best` is defined on **`lp_gt_max`**, a single-sequence score §7.2 already computed; the logsumexp is kept for `me_best`, where it is conservative. Zero new compute, no threshold moved. F-i records the fact; §8.1 defines the new `neither_cert` band the split necessarily creates; both variants of `sb_best` are recorded and the decision-bearing one is preregistered | §1.1, §7.2, §8.1, F-i |
| **SR-C2** | the E2 rule reads P1's **upper** bound, i.e. a certified **lower** bound in the direction where it carries no information — rule 01 item 8 in bound form, contradicting §8.7 | **FIXED.** The condition "the 95% upper bound of P1 < 0.5" is **deleted and appears nowhere in v2**. The E2-direction branch rests **solely** on P2. §13.1 states in binding form that C0002 cannot bound the search-error rate from above, and §8.7 forbids "not search" outright | §13.2, §8.7, §12.3 |
| **SR-C3** | E2 and E3 are not mutually exclusive, so a single corpus attribution is an estimand error no interval repairs | **FIXED.** v2 reports **two independent certified lower bounds**, never one attribution. "Predominant" and "attribution" are retired as statements about failure modes (§1.4 item 8, §8.7). `H0001-R`'s falsifiable statement is rewritten to drop "not search". The supervisor's retraction in `hypotheses/C0002_selection.md` is cited | §1.1, §13, §8.7 |
| **SR-C4** | the interval of record resamples 8 **fixed** families, contradicting §2.2, and undercovers at 0.876–0.904 while running up to 17× narrower than the unclustered Wilson; decision-flipping | **FIXED.** §12.1's interval of record is the bound-by-bound more conservative of a **stratified bootstrap resampling systems within the 8 fixed families** and **Wilson on `n_eval`**. Independently re-simulated (M3): v1's estimator covers 0.904–0.922 at 80 systems (0.884–0.916 at 71), v2's covers **0.942–0.968**. The homogeneous-family diagnostic is reproduced: v1's estimator returns width **0.0231** with its lower bound exactly on 0.5 | §12.1, §2.2, M3 |
| **SR-C5** | §12.4's disclosed operating characteristic is wrong by an order of magnitude **and in the dangerous direction** | **FIXED.** §12.4 is rewritten from the estimator actually preregistered, with simulated coverage and widths at five true rates and the **minimum point estimate at which any branch can fire (`48 / 80 = 0.600`)** stated in advance | §12.4, M3 |
| **SR-C6** | BA2 is not verified achievable (≈ 0.530 against its own 0.50 bar, median 1 partner), degenerates where it runs, and cannot block E2 | **FIXED, and the honest consequence is stated rather than engineered away.** Availability was measured before freeze with the **real model tokenizer** over the **full 960-cell corpus**, all 47,987 candidates, zero tokenizer failures: **0.4625** at the frozen minimum of 3 partners, **0.4990** at the lowest admissible floor of 2. **No admissible floor clears the 0.5 cutoff, and the cutoff was not moved.** A minimum partner count is preregistered and derived from this contract's own §5.1. `length_control_not_measurable` now **BLOCKS** a supported E2. **Consequence, stated before compute: C0002 cannot produce a supported E2** | §0.0 item 1, §8.5 BA2, §13.2, §21 item 7, M1 |
| **SR-C7** | the battery's blocking power is systematically anti-correlated with bias direction — all three audits of mechanisms pointing toward the preferred answer are label-only or no-ops, and only BA4, of unknown direction, can block | **FIXED.** **BA1, BA2 and BA3 all block a supported E2.** §13.2's `certified_non_argmax_prevalent` branch is an explicit conjunction requiring BA1 not to fire, BA2 to **run and pass**, BA3 not to fire, BA4 to agree, and NC-CONDITION to pass. Each audit is also aggregated **to the system level** before thresholding (SR-M7) | §8.5, §13.2 |
| **RA-C2** | Gate 3b has two contradictory dispositions — §7.2 "a downgrade, not an abort" vs §11's gate conjunction — the C0001 Gate B→C defect verbatim, making R7 unsatisfiable | **FIXED.** Gate 3 is split into **3a PASS/ABORT, 3b DOWNGRADE, 3c REPORT-ONLY**, stated once in §7.2b and referenced (not restated) by §11, so there is **exactly one contract text per condition** for R7 to quote. **3b and 3c are removed from Gate 6's conjunction.** The same audit was then applied to every other gate and control: §10's table and §11's classes give each condition exactly one disposition (RA-M14) | §7.2b, §11, §10 |
| **RA-C3** | §16.1 reinstates the unguarded `run_manifest.py` directory fingerprint that C0001 v2.1 forbade; it runs in a **separate process** the phase guards do not cover, and Gate 0's `sealed_paths_read == []` would still pass | **FIXED.** v2.1's prohibition is **reinstated verbatim** in both §2.4 and §16.1; v1's "a recursive data-tree fingerprint" clause is struck; every invocation routes through `safe_run_manifest_data_paths()`; `assert_no_directory_argument()` is called on every path; `run_manifest.py`'s own `main()` installs `install_sealed_audit_hook()`; and **Gate 0 item 6 and every phase boundary assert that no directory argument reached it** | §2.4, §16.1, §11 Gate 0 |

### 23.2 MAJOR — statistical review

| # | finding | resolution | where |
|---|---|---|---|
| SR-M1 | the bootstrap statistic's denominator is unspecified; the fixed-denominator reading returns intervals **exceeding 1.0** | **FIXED.** The statistic is named explicitly as `Σ_s indicator(s) / n_eval` with `n_eval` fixed across resamples; under the stratified scheme each resample draws exactly `n_f` from family `f`, so the >1.0 pathology cannot arise | §12.1 |
| SR-M2 | Holm is named but no null, statistic or p-value is defined, §13 uses uncorrected intervals, and it is the wrong instrument anyway | **FIXED.** Holm is **deleted**. §12.2 states the correct **intersection–union** argument, records that **no p-value is defined or computed**, states the one-sided error rate each branch carries, and notes the indicator-level exclusivity **without** restating it as propositional exclusivity | §12.2 |
| SR-M3 | "usable cells" undefined; no per-system floor; `/71` hard-coded; attrition biases P2 **upward toward E2** | **FIXED.** §2.1b defines usable candidate, usable cell and **evaluable system**, with a floor (≥ 8 of 12 **and** all four corruption settings covered) whose direction-of-bias derivation is recorded and whose achievability is verified (all 80 systems have 12 cells, 3 per setting). The denominator is the **realized `n_eval`**, reported beside the nominal 80; **a literal denominator never appears**. The realized per-system usable-cell distribution is reported | §2.1b, §8.4 S9, §15 |
| SR-M4 | the 80 → 71 filter is inherited from a rewrite-set criterion irrelevant to a log-probability endpoint, costs 11% of systems, drives R07 to 4 and R08 to 7, and narrows §2.2's population non-proportionally | **FIXED by dropping the filter.** P1/P2 run on **all 80 systems / 960 cells / 47,987 candidates**, giving **eight equal fixed strata of 10**. The 71-system read is retained as preregistered sensitivity **S11** and may not be promoted. `partB_endpoints.json`'s own `note` and the `uses_only_in_support_operators: True` finding are quoted as the basis | §4, §8.4 S11, §2.2 |
| SR-M5 | `H0010`'s `budget_exceeded_by_input_size` reintroduces an unknown denominator **in the direction of the prediction** — the exact failure that made C0001 undecidable | **FIXED, and the count is now MEASURED at 0.** M2's leak-free `count_ops` pass over all 89,349 distinct component strings finds a **maximum `count_ops` of 14**, so `CAS_NODE_BUDGET = 400` excludes **0 rows** (F-l). A **bound-shaped rule** is preregistered anyway: if the verdict would be supported but adding the excluded classes would move it out of the band, the verdict is `H0010_undecidable_budget_limited` | §9.1, §9.3, F-l, M2 |
| SR-M6 | `H0010`'s thresholds are not derived; `n_class_pow4 ≥ 10` and `n_class_den > 0` pass **by construction**; the `≤ 5` cutpoint carries all the content with no derivation and deterministically fixes a census verdict; H4 is dropped by RD3 | **FIXED.** H1 and **H2 are relabelled** as precondition and **verification condition**, not predictions, with the superset argument stated. The bare cutpoint is **withdrawn** and replaced by a **graded relative rule** on `r_joint = n_class_joint / min(n_class_den, n_class_pow4)`, whose *form* is derived from the hypothesis's own wording and whose band edges are disclosed as order-of-magnitude conventions, with a stated conclusion for **every** band. **H4 acquires a conflict rule and RD3 may no longer drop it** | §9.3, §1.2, §18 RD3 |
| SR-M7 | the §8.5 gating quantities are **cell-level**, violating §2.1's own frozen aggregation order, and carry no interval method | **FIXED.** BA1, BA2 and BA3 are aggregated **to the system level before any threshold is applied**, per §2.1. Where a threshold is applied to a point estimate with no interval, §8.5 states that explicitly and names the cost — the reviewer's own second option | §8.5, §2.1 |
| SR-M8 | BA3's consequence is a no-op (the primary already **is** the logsumexp), and the logsumexp is itself an unbounded lower bound over a capped enumeration | **FIXED.** BA3 **blocks** a supported E2 on a high flip rate or on a 3b downgrade. `lp_gt_is_lower_bound_over_capped_enumeration: true` is carried **unconditionally** on every artifact. v1's claim that `Δ_enc` "is the measurement of this bias" is **withdrawn as an overclaim** — it measures movement within the enumerated set and bounds nothing about the residual | §8.5 BA3, §7.2 |
| SR-M9 | BA1 firing should suspend the "not search" claim, not add a label | **FIXED.** When BA1 fires, **P1 is reported `certificate_opportunity_insufficient`**, the falsifier is declared **unevaluable**, and a supported E2 is **blocked**. (The "not search" claim itself is separately forbidden outright by §8.7, per SR-C2/C3) | §8.5 BA1, §13.2, §8.7 |
| SR-M10 | §0.3's containment claim is broader than what it demonstrates; §7.1 contradicts it by stating the primary context was chosen in light of the observation; "the primary quantity has never been observed" overstates | **FIXED.** v1's blanket claim is **replaced by §0.9's per-threshold derivation table** (inherited / derived / new-without-derivation). §0.3 item 2's framing is **withdrawn** and replaced by the accurate statement. §0.3 item 5 **discloses** the post-observation primacy choice rather than defending it, and §7.1 rests the choice on the F-g argument alone | §0.9, §0.3, §7.1 |
| SR-M11 | the degenerate-bootstrap rule makes the interval of record discontinuous, with the substitute **wider** than what it substitutes for | **FIXED.** The special case is **deleted**. §12.1's "more conservative of the two, always" is continuous by construction and handles both degenerate corners with no special case | §12.1 |
| SR-M12 | the literature's stated precondition for a defensible E2 is reported but forbidden from bearing on it, and v1 resolved the conflict **silently**, in the direction that removed a check | **FIXED by explicit adjudication.** §8.5b makes S8's **co-reporting mandatory** while keeping the v2.1 inferential prohibition, and records that the precondition is met on the co-reporting limb and **not** met on the length-control limb — an independent second reason a supported E2 is unavailable | §8.5b |
| SR-M13 | PC-GREEDY is a hard abort on the primary but its achievability evidence is from the **non-primary** context and its evaluation context is unspecified; abort risk 40% at a true rate of 0.05 | **FIXED IN PART + ACCEPTED LIMITATION.** *Fixed*: the gate's context is now stated explicitly as **the primary context**, and the operating characteristic is disclosed (`P(X ≥ 2 \| n = 40)` = 0.9985 / **0.6009** / 0.1905 at true rates 0.20 / 0.05 / 0.02). *Accepted*: the probe **cannot** be re-measured in `C_gen` before freeze, because doing so requires `lp_best` under `C_gen`, which §0.4 forbids. **Consequence**: the 2 / 10 figure is labelled `unverified_for_C_gen` everywhere, and a live ~40% abort risk on the primary is carried into Gate 4 with the supervisor informed. **The bar was not moved** | §10 PC-GREEDY, §11 Gate 4, §21 item 9 |

### 23.3 MAJOR — reproducibility audit

| # | finding | resolution | where |
|---|---|---|---|
| RA-M1 | per-worker SymPy seeding does not close the RNG mechanism (state at a comparison is load-dependent); the `multiprocessing` start method is unpinned, and both the seed and the firewall guards' inheritance depend on it | **FIXED.** A **deterministic per-item reseed** keyed on `sha256(normalized_input_key)` replaces the per-worker seed, so the outcome is a function of the input and `SYMPY_RNG_SEED` alone regardless of worker assignment, chunk size and order. The start method is **declared `fork`**, with an explicit `spawn` fallback that must also install the guards. v1's worker-start assertion — which proved only the part never in question — is **replaced by a chunk-size invariance test** at Gate 0 | §5.2 item 2, §3, §11 Gate 0 item 9 |
| RA-M2 | `CAS_NODE_BUDGET` is not load-independent on the real paths: the call sites take **strings** so the parse precedes the budget and is unbounded; `_timed_simplify(sympify(...))` evaluates the parse **outside** the guard; `count_ops` is not monotone with `cancel`/`simplify` runtime | **FIXED IN PART + ACCEPTED LIMITATION.** *Fixed*: the bound is scoped to already-parsed `Expr` objects; the unbounded parse gets its own counted label `parse_not_admitted_unbounded`; and the call sites **must be fixed** so `sympify` is evaluated inside `with _time_limit(...)`. *Accepted*: `count_ops`'s non-monotonicity with `cancel` runtime on rational functions cannot be repaired without patching SymPy. **Consequence**: a 400-node bound does not bound `cancel`, and the wall clock still decides in the tail — which is exactly why RA-M3's scoping matters. Measured mitigation: F-l shows the budget is **inert** here (max `count_ops` = 14) | §5.2 item 1, §21 item 1, F-l |
| RA-M3 | Gate 6's `wall_clock_guard_fired == 0` has no achievability evidence (C0001 recorded 9 and 7 firings) and couples the **GPU log-probability primary** to a subsystem §5.2 says it does not depend on | **FIXED by scoping.** `wall_clock_guard_fired` is counted and reported **per endpoint**; a non-zero count affects **`H0010` only** and **does not affect `H0001-R`**. v1's "must be 0" is **withdrawn as unevidenced**, and §15 now records that a non-zero count is **expected**. **The 10.0 s limit is not raised** | §11, §15, §13.2 |
| RA-M4 | §16.2's `expression_safety` diagnostics are not in the stored schema, are unbudgeted, hardcode `x_1,x_2,x_3` against GRN's `x_0..x_5`, and hide a bare `except` that records a failure as a result | **FIXED by striking the clause.** Rule 03's singularity / validity item is instead carried by fields that **do** exist — the stored `structure` flags and `trajectory_metrics.*_failures` — cited by name and copied with provenance. `equation_metrics.py:338-339` is recorded as a repository-level known defect that **C0002 does not call** | §16.2 |
| RA-M5 | no input artifact is pinned by hash; `phase0/input_fingerprints.json` was dropped | **FIXED.** **M7** records SHA256 and byte size for the checkpoint, `validation.json`, `all_candidates.json`, `partB_in_support_systems.json`, `partC_cell_records.jsonl`, `partC_instrument_test.json` and a roll-up over the 960 cell files. `phase0/input_fingerprints.json` is **mandated** from `InstrumentedOpener.fingerprints()`, and **Gate 0 item 4** asserts every digest matches | §3, §0.7 M7, §11 Gate 0 |
| RA-M6 | resume is required by Gate 5 but defined nowhere — no unit, no ordering, no double-count protection, no ledger | **FIXED.** §11b freezes the resume unit as `(cell_id, scoring_context)`, the write-then-`fsync`-then-append ordering, ledger-based skip and truncation on restart, denominators computed **from the ledger**, and a Gate-6 ledger-identity check | §11b, §11 Gate 5, Gate 6 |
| RA-M7 | NC-CONDITION's evidence is misattributed (the cited triple is bundle 0 corruption variants; the real across-bundle triple is byte-identical `-159.50254821777344`), and provably-zero-Δ partners exist | **FIXED.** **F-m** records the byte-identity and the systemic 10-distinct-payloads-per-system fact; v1's citation is **explicitly withdrawn**. The partner rule is frozen as **a cell of a DIFFERENT system**, drawn per cell with `CONTROL_CELL_SEED`, and the achievability is re-measured (**M4**, 200 cells): `frac \|Δ\| > 1` nat = **0.95**, median **13.08** nats, **0 exact zeros**. The bar is **not lowered**; instead the razor-thin margin is disclosed (`P(pass \| 40, p = 0.95)` = **0.6767**) and the control is given a **DOWNGRADE** disposition with a named consequence | F-m, §10 NC-CONDITION, M4 |
| RA-M8 | §10.5's `identity_error` range is wrong at both ends | **FIXED.** Corrected from the artifact (**M6**): min **`0.0`** (17 exactly zero), smallest non-zero **`1.2226593959496768e-08`**, max **`2.8991699210223487e-06`**, tolerance `1e-05`, 0 rows over tolerance. The realized margin is stated honestly as **3.45×**, not the ~12× v1 implied | §10, M6 |
| RA-M9 | every gate threshold binding in `C_gen` was measured in `C_raw`; PC-GREEDY's context is never stated; Gate 4's reconstruction check is **vacuous** (never goes through the tokenizer, so it cannot see the 4-significant-digit quantization) | **FIXED.** Gate 4's condition is **redefined** as an `encode → decode → encode` **token-identity round trip through `env.equation_encoder`** in the primary context, and **measured** (M5): **0.9683** in `C_gen` vs **0.9917** in `C_raw`, with the numeric round trip 0.275 vs 1.000 and F-k recording the quantization as the cause. PC-GREEDY's context is stated. Every `C_raw`-derived achievability figure is labelled **`unverified_for_C_gen`**. **The ≥ 0.98 bar is not moved**; §7.3 states the predicted failure, its frozen consequence, and the supervisor's fork | §7.3, §10, §8.2, F-k, M5 |
| RA-M10 | under `C_gen`, `e1` cannot be the stored `tree_encoded`, which undermines Gate 3b | **FIXED and quantified.** §7.2 specifies `e1`'s `C_gen` procedure explicitly, and **F-j measures the consequence: `e1` and `e2` are identical on 120 / 120 cells in `C_gen`** (distinct on 80 / 80 systems in `C_raw`). Gate 3b in `C_gen` therefore rests on orbit members alone, its achievability there is declared **`unverified`**, and 3b is a **DOWNGRADE condition only** so no decision rests on it | F-j, §7.2, §7.2b, §21 item 8 |
| RA-M11 | the `C_gen` forward map assumes `rescale_function` was always applied; `rescale_function:56-57,67-68` returns unrescaled trees and `sklearn_wrapper.py:166-167` is `except: pass` | **FIXED.** A per-candidate guard is preregistered: a candidate is usable in `C_gen` only if its free symbols lie within the system's dimension. Failures are excluded with `failure_reason: "rescale_function_early_return_suspected"`, counted and reported per rule 03, **never transformed**. Whether any candidate hits the branches is declared `unverified`, so the answer is recorded either way | §7.1, §2.1b, §15 |
| RA-M12 | `H0010`'s corpus is unfrozen (80 vs 71) while its falsifier is an integer count | **FIXED.** The corpus is **frozen at all 80 systems / 47,987 candidates / 89,349 distinct component strings**, with the definitional reason stated (`H0010` is about generation coverage; support is a property of the truth). The 71-system restriction is a preregistered sensitivity (74,117 strings). The integer falsifier is separately replaced by a graded rule (SR-M6) | §9.2, §4 |
| RA-M13 | no gate stops the census — the one unmeasured cost — before it is spent; the claimed bounds are not mechanisms | **FIXED.** **Gate 2a** runs the predicate pipeline on a preregistered 5,000-string subsample with `GLOBAL_SEED`, records wall time, and requires the linear projection to be ≤ 8 CPU core-h before the full census runs; above it, RD3. The **execution order `0 → 1 → 2a → 2 → 3 → 4 → 5 → pass → 6` is frozen**, as C0001 v2.1 §7.10 did. M2 additionally measures the parse stage at 0.0362 core-h | §9.2, §11, §14 |
| RA-M14 | several Gate-4 and Gate-3 failure dispositions **do not exist**, so the gates are not machine-checkable and R7 has no text to quote | **FIXED.** §10's control table gives **every** control an explicit single-clause disposition (ABORT / DOWNGRADE / REPORT-ONLY / NAMED-CONTINGENCY) in its own row, §7.2b does the same for 3a/3b/3c, and §11 states the classes without restating the conditions — so there is **exactly one contract text per condition**. **Gate 6 consults only ABORT-class conditions** | §10, §7.2b, §11 |

### 23.4 MINOR

| # | finding | resolution |
|---|---|---|
| SR m-1 | "all 8 clusters give the identical value" — is "value" the count or the rate? holds only by arithmetic accident and would not survive RD2 | **FIXED.** The degenerate special case is deleted entirely (§12.1), so the ambiguity has nothing to attach to; §18 records that RD2's unequal strata are therefore safe |
| SR m-2 | S2 and S3 labelled "clustered" with no named method; S2 mixes a cell-level rate into a system-level section | **FIXED.** §8.4 names the estimator for each, and S2's cell-level rates are labelled cell-level with their denominators and **may never be compared to a system-level rate** (§2.1) |
| SR m-3 | P2's name promises a certificate its formula does not compute | **FIXED.** `E2_system(s) = 1[me_rate(s) = 1]`, defined through `me_best`. §8.3 proves the new form is **strictly harder to satisfy** than v1's |
| SR m-4 | the `H0010` census is the only unmeasured compute component; take the timing from the `count_ops` pass | **FIXED.** M2 records 130.27 s / 0.0362 core-h for the parse stage, and Gate 2a measures the predicate stage before spending it |
| SR m-5 | "attribution" in §19's replication trigger | **FIXED.** §19 is restated on the certificate rates; the word is retired throughout (§1.4 item 8) |
| RA 1 | §16.2 does not say the rule-03 fields are **copied** rather than recomputed | **FIXED.** §16.2 states they are copied with provenance (`source_artifact`, `source_run_sha256`), and names the hazard of recomputing: 47,987 `symbolic_recovery` calls would reintroduce the 10 s `SIGALRM` |
| RA 2 | PC-GREEDY compares unequal spellings | **FIXED.** §8.6 states it, and PC-GREEDY records carry `lp_greedy_is_respelling: false` beside `lp_best_is_respelling: true` |
| RA 3 | §10.2 cites `seed=0`; the code uses `seed=self.generation_seed` | **FIXED.** §10's PC-GREEDY row cites `seed=self.generation_seed` and `model_wrapper.py:74-81` |
| RA 4 | F-f cites `sklearn_wrapper.py:172`; the call is at `:173` | **ACCEPTED.** F-a … F-h are carried **by reference** to v1 §0.6, which is retained **unedited** as the historical record; correcting a line number inside it would edit v1. The correction is recorded here — the call is at `:173`, `:171` is `if sort_candidates:` — and the substance (`sort_metric="r2"` passed explicitly at `src/gpu_run4/inference.py:202,242`, ranking on original units) is unaffected |
| RA 5 | `sealed_paths_read == []` is weaker than it reads | **FIXED.** §2.4 carries the caveat: it is a computed property over paths opened through `InstrumentedOpener`; the audit hook **raises** rather than accumulating; the assertion is necessary but not sufficient |
| RA 6 | Holm declared but no decision uses a p-value | **FIXED** — same resolution as SR-M2 |
| RA 7 | disclose the replicate structure of the cells | **FIXED.** §2.1 records that 240 of the 960 cells are 80 conditionings replicated 3×, that `sb_rate(s)` averages them as if independent, and that this explains Gate 1's 10-distinct-payload check |
| RA 8 | §14's `< 1 GiB` new-disk projection is not derived | **FIXED.** §14 shows the arithmetic, projects ≈ 1 GiB bounded at 2 GiB, and names the `.npz` sidecar fallback |

### 23.5 Findings raised by the v2 measurements themselves

Recorded here because they were not in either review and a reader must not mistake them for reviewer
findings.

| # | finding | disposition |
|---|---|---|
| V2-1 | **The length confound is structurally unauditable on this corpus.** On **0.6302** of cells the truth is token-longer than **every** candidate, so no in-corpus length control can cover the corpus, and the availability shortfall is not an artefact of the window or the floor | **ACCEPTED LIMITATION with its consequence stated: a supported E2 is unavailable in C0002** (§0.0, §13.2, §21 item 7). Designing a corpus that can audit it is C0003's content |
| V2-2 | **Gate 4's `C_gen` condition is predicted to fail**, and the frozen fallback would make the observed context primary, collapsing §0.3's containment | **ESCALATED to the supervisor as a preregistered fork** (§7.3), with three options and no threshold moved |
| V2-3 | The certificate split creates a band (`lp_gt_max ≤ lp_best ≤ lp_gt_lse`) in which **neither** certificate fires, which v1 had no name for | **FIXED by definition**: `neither_cert(c)`, counted, reported with its denominator, excluded from both rates (§8.1, §15) |
| V2-4 | The first `C_gen` probe returned 0.0 on two rates because of **a defect in the probe**, not a finding | **DISCARDED, and disclosed.** The corrected probe carries its own `C_raw` control (rule R5). The zeros are reported nowhere as a result (§0.7 M5) |

---

## 24. What cannot change after the first primary indicator of the frozen run is computed

Restated as the skill requires, in one place. **Everything in §22**, plus:
which quantity carries which certificate; the `neither_cert` definition; `n_eval`'s construction;
the §7.3 context decision once the supervisor has recorded it; the §8.5b adjudication; the §9.3 bands;
and the §13.2 branch table.

**Nothing on that list may be changed to rescue a result.** A threshold may never be raised, a
tolerance relaxed, a cap increased or a seed changed for that purpose (rule 01 item 3).

**And specifically**: if the run returns `E2_direction_observed_but_length_unaudited` — the outcome
§0.0 predicts — **that is the result.** It may not be reported as a supported E2, BA2's cutoff may not
be lowered to 0.46, the minimum partner count may not be lowered to 1 or 2, and no length control may
be substituted after the fact.
