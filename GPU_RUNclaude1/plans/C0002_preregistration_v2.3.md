# C0002 — Preregistration **v2.3** (DRAFT — NOT FROZEN)

| field | value |
|---|---|
| cycle | `C0002` |
| stage | 3 (design, revision 2.3) |
| status | **`FROZEN`** — 2026-09-12, by the supervisor, at commit `78c487ce349fa2e91c0d4ce149a256518ff958c7`. BINDING. The delta review's seven findings are discharged; no threshold was moved in any revision; v1, v2, v2.1 and v2.2 are retained unedited as historical record. See `plans/C0002_freeze_decision.md` for what was checked and the one condition attached. |
| supersedes | `plans/C0002_preregistration_v2.2.md` + `.json`, status `DRAFT_PENDING_SUPERVISOR_CHECK`, which superseded v2.1, v2 and v1 |
| v1 / v2 / v2.1 / v2.2 disposition | **v1, v2, v2.1 and v2.2 are retained unedited as the historical record.** None is amended, annotated or deleted. v1 is the document the two reviewers reviewed; v2 is the document on which the supervisor's three decisions were taken; v2.1 is the document the supervisor verified and partially sent back; **v2.2 is the document the delta review reviewed.** |
| author role | `lansr-research-methodologist` (drafting only). The author of v1, v2, v2.1 and v2.2 is the author of v2.3; **every reviewer was independent of the author and of each other.** |
| reviews addressed | `reviews/C0002_preregistration_statistical_review.md` (7 CRITICAL, 13 MAJOR, 5 MINOR) and `reviews/C0002_preregistration_reproducibility_audit.md` (3 CRITICAL, 14 MAJOR, 8 MINOR). Disposition of **every** CRITICAL and MAJOR is in **§23**, carried forward from v2 unchanged except where a supervisor decision supersedes it. |
| supervisor decisions implemented | **`plans/C0002_supervisor_decisions.md`, dated 2026-09-12**: three decisions (§25) **plus the 追補 send-back of the same date** (§26). All taken **before** Gate 4 runs and before any endpoint is computed; none is a post-hoc rescue. |
| reviews addressed in v2.3 | **`reviews/C0002_v2.2_delta_review.md`** (`lansr-statistical-reviewer`, 2026-09-12): **1 CRITICAL, 4 MAJOR, 2 MINOR**, all textual, **none requiring a threshold to move or anything to be recomputed**. The review **verifies the v2.2 decision as correct** and verifies independently that no threshold moved. Disposition of every finding is in **§27**. |
| **what v2.3 changes** | **the delta review's seven findings, and nothing else.** The largest two: **§19 is rewritten** — it was declared P1's only cross-check while two of its three remaining factors could not perturb P1 and **no outcome of it had any consequence**; and **§13.4 rule 0 is re-grounded** on decode-indexing rather than the false and symmetric "commensurability" premise v2.2 froze. **§13.6 is new**: the preregistered consequence of each replication outcome for a fired P1. **The v2.2 decision itself — rule 2 scoped to P2 — is unchanged and is verified correct.** |
| thresholds moved in v2.1, v2.2 and v2.3 | **NONE.** Not one bar, cap, tolerance, cutoff, window, floor, partner count, seed or ceiling differs from v2. §25.4 is the clause-by-clause table, **independently verified by the supervisor: 31 rows, zero rows whose v2 value differs.** v2.2 moves none of them either — it corrects **which quantities are commensurable**, nothing else. |
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

Four facts change what this cycle can conclude. Three were established in v2 and are unchanged; the
fourth is the supervisor's resolution of the fork v2 escalated. Two of the four **narrow the cycle's
reach**, and they are stated here, before anything else, so that the narrowing is part of the frozen
contract and not a limitation discovered at reporting time.

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

   **This is binding, not a limitation note.** The strongest E2-direction outcome reachable in this
   cycle is **`E2_direction_observed_but_length_unaudited`** (§13.2). `certified_non_argmax_prevalent`
   is written out in full and is **unreachable**. Any artifact, analysis, report or synthesis that
   describes a C0002 outcome as a supported E2 is a contract violation, at any stage.
   **The cycle nevertheless runs**, because `LB(P1) > 0.5` is reachable and decisive: it would refute
   the E2-direction reading and demonstrate certified search error on a majority of systems, with an
   interval. See §13.3.

   **New in v2.1 — the length fact is promoted to a registered descriptive endpoint (`S12`, §8.5c).**
   "On **0.6302** of cells the ground truth is token-longer than every candidate" is not merely the
   reason BA2 cannot run. It is structural evidence about the **generator**, which is what this cycle
   asks about; it depends on **no** log-probability, on **none** of the contested certificate
   machinery, and on **neither** scoring context; and it is already measured at zero additional cost.
   It is registered with per-system, per-family and per-stratum reporting and a realized denominator —
   and with an explicit prohibition: **it may not be used for attribution and may not be offered on
   its own as evidence for E2.** It is a fact about a length distribution, not a mechanism.
2. **`H0001-R` reports two independent certified lower bounds, not one attribution.** E2 and E3 are
   not mutually exclusive propositions; the supervisor has already retracted the exclusivity premise
   in `hypotheses/C0002_selection.md`. v1's single-attribution framing was an estimand error, and
   v1 §13's "upper bound of P1 < 0.5" read a one-sided bound in the direction where it carries no
   information. Both are removed (§13).
3. **Gate 4's `C_gen` reconstruction condition is predicted to fail at its own frozen bar.** Re-expressed
   as the real tokenizer round trip that the audit requires, it measures **0.9683** in `C_gen`
   against `≥ 0.98` (**M5**, §0.7). **The bar is not moved and never was.**
4. **RESOLVED IN v2.1 — the `C_gen` / `C_raw` fork. Both contexts are CO-PRIMARY. There is no
   fallback.** v2 §7.3 escalated three options; the supervisor took the third on 2026-09-12
   (`plans/C0002_supervisor_decisions.md` 決定 1). **v2's frozen fallback — "if `C_gen` fails Gate 4,
   `C_raw` becomes primary" — is REMOVED from this contract.** P1 and P2 are reported in **each**
   context; disagreement between them is the `conditioning_sensitive` verdict that BA4 already
   computes. The reason the fallback was rejected is research integrity, not convenience: `C_raw` is
   the context in which `lp_gt` was already observed on all 960 cells (§0.2) and in which the 8-cell
   `sb_best` exposure occurred (§0.3), so a fallback would have promoted an **already-observed**
   context to primary, in the direction the campaign prefers, and would have **silently changed what
   the cycle measures**. Four conditions ride with the decision and are binding:

   1. **`C_raw` results carry the downgraded sentence** — "the truth outscores all 50 candidates under
      a conditioning the search did not see" — which is **not** a search-error claim.
      **Certificate-S language is restricted to `C_gen`** (§7.1, §8.7).
   2. **The 8-cell `sb_best` exposure is disclosed as prior information** (§0.3, §0.3a) and those
      8 cells carry **`pre_freeze_exposed: true` in every `C_raw` artifact**, so that no analyst can
      aggregate them unknowingly.
   3. **`gt_is_quantized_in_context: true` stays on every `C_gen` artifact**, and the contract states
      plainly that **the truth scored in `C_gen` is a 4-significant-digit approximation of the truth**
      (§7.3).
   4. **Agreement between the two contexts may NOT be presented as double confirmation** (§8.7,
      §13.4). They share the model, the truths and the candidate set; they are **not** independent.
      Reading agreement as corroboration is the same error as C0001's "three independent derivations
      agree" (`reviews/C0001_independent_review.md` NOTE-R4; carried in `research_state.md` as a
      standing correction, cited by the decision record as 訂正 2).

   **What Gate 4's `≥ 0.98` now governs.** It stays exactly where it is and it still bites — but it
   now governs **which context carries which sentence**, not **which context is primary**. §10 and
   §11 state the one disposition it carries.
5. **ALSO RESOLVED IN v2.1 — PC-GREEDY no longer gates anything.** Its achievability under `C_gen` is
   `unverified` and cannot be verified before freeze without violating §0.4. A control whose expected
   value has not been verified achievable **must not sit on a gate**: that is C0001's near-fatal
   defect (MAJOR-R6), where no control could produce a non-zero value of the primary indicator and a
   zero result was therefore indistinguishable from a broken instrument. PC-GREEDY is moved from
   **ABORT** to **REPORT-ONLY** (§10, §11 Gate 4). What that costs, and what still covers the gap, is
   stated in §10.2b rather than left implicit.

6. **NEW IN v2.2, RE-GROUNDED IN v2.3 — the two certificates are indexed to different things, and
   the cycle-level rule no longer requires agreement of the one for which agreement is meaningless.**
   v2.1's §13.4 rule 2 made a cross-context disagreement collapse to `conditioning_sensitive` for
   **both** certificates. The supervisor sent that back on 2026-09-12
   (`plans/C0002_supervisor_decisions.md`, 追補), on grounds internal to this contract:

   > **§13.2 branch 1 already says `C_raw`'s P1 is not a search-error claim.** Requiring P1 to agree
   > across contexts therefore requires it to agree with **a quantity that measures something else**.
   > A certified search error in `C_gen` — the context the search actually ran in — would vanish
   > merely because it differed from a number that was never a search-error claim.

   **Frozen consequence (§13.4):** rule 2 applies to **P2**. **For P1 the `C_gen` result stands on
   its own**, with the `C_raw` downgraded value and the difference between them **reported alongside,
   mandatorily**. Rule 3 — one context `undecidable` — **stays as written for P1 too**, because that
   is an instrument-failure question and has nothing to do with what a certificate is indexed to.

   **The premise was corrected in v2.3 (§13.4 rule 0).** v2.2 grounded the split on
   "commensurability" and asserted that P2's two readings are "the same proposition". The delta review
   showed that claim is **false and symmetric** — it applies verbatim to P1 — so it could not support
   the asymmetry, and run consistently it would have licensed dropping rule 2 **for P2**, the
   campaign's preferred direction. **The correct ground, which reaches the same conclusion, is what
   each certificate is indexed to**: Certificate S is indexed to **a historical decode event** and
   there was exactly **one** decode; Certificate N is a **property of the model**, for which neither
   conditioning is privileged, so requiring both is a real robustness demand.

7. **NEW IN v2.3 — the replication gate is P1's only cross-check, and until v2.3 it could not carry
   that.** v2.2 declared §19 load-bearing for P1 and left it unable to bear the load: its factor menu
   contained an option §19 itself declares invalid, **two of its remaining three factors cannot
   perturb P1's value at all** (`CONTROL_CELL_SEED` draws only the 40-cell control set, and a fresh
   process path reproduces a teacher-forced fp32 number), and **no outcome of the gate had any stated
   consequence** for the verdict it exists to police. §19 is rewritten, **§13.6 preregisters the
   disposition of every replication outcome**, and a fired P1 is **provisional** until the
   confirmation returns. **§12.2 step 4's admission that P1 carries a single-context read is NOT
   softened** — the delta review was explicit that its loudness is right and its **enforceability**
   was what was missing.

   **This is not a loosening in the campaign's favour, and the direction matters.** P1 is the branch
   that **refutes** the E2-direction reading and fires `H0003`. **P2 — the campaign's preferred
   direction — keeps the full cross-context conjunction, unchanged.** The requirement was relaxed
   only on the refuting branch. **No threshold moved** (§26.4).

**Disposition counts (§23):** **10 CRITICAL — 10 FIXED.** **27 MAJOR — 25 FIXED, 2 FIXED IN PART with
an accepted limitation and its consequence stated.** **13 MINOR — 12 FIXED, 1 ACCEPTED.**
**Nothing is silently dropped, and no finding was resolved by moving a threshold.**
**v2.1's own disposition — every change relative to v2, with its reason — is in §25.
v2.2's disposition — the single change relative to v2.1 and every place it rippled — is in §26.**

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
2. **CORRECTED AGAIN IN v2.1 — there is no containment left, and none is claimed.** v1 claimed the
   primary quantity had never been observed; v2 withdrew that and replaced it with "the primary
   quantity was not directly computed; the `C_raw` proxy was, on 8 of 960 cells, in the E2 direction,
   with `lp_gt − lp_best` gaps of 100–500 nats, so `sb_best` is very likely to agree across contexts
   on those 8 cells" — while noting that a fallback to `C_raw` would end the containment entirely.
   **Under the supervisor's 決定 1 there is no fallback because `C_raw` is CO-PRIMARY outright**
   (§7.3). So the accurate statement, which this contract adopts and which may not be softened, is:

   > **A co-primary endpoint's own proxy was observed, before freeze, on 8 of 960 cells, in the
   > direction the campaign prefers.** This is prior information about a co-primary context. It is
   > **not** contained, **not** mitigated by the other context, and **not** cancelled by the fact that
   > `C_gen` was unobserved.

   The mitigation is disclosure and marking, not containment: §0.3a.
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

### 0.3a The `pre_freeze_exposed` marking rule (NEW in v2.1, from 決定 1 condition 2)

**Binding.** The **8** cell ids listed in §0.3 — and only those 8 — carry **`pre_freeze_exposed: true`**
on **every** `C_raw` record, cell record, endpoint record and audit record this cycle writes. Every
other cell carries `pre_freeze_exposed: false`. The field is written unconditionally, so its absence
is itself a contract violation a machine check can catch.

| requirement | frozen |
|---|---|
| which cells | exactly the 8 of §0.3, listed by `cell_id`, written to `phase0/pre_freeze_exposed_cells.json` at Gate 0 **before** any scoring |
| which artifacts | every `C_raw` artifact. `C_gen` artifacts carry the same field with the value `false`, because the `C_gen` quantity was not observed — the field is never simply omitted |
| what it does **not** do | **it does not exclude them.** Excluding them would be a post-hoc, outcome-dependent exclusion (rule 01 item 3). They stay in the numerator and the denominator |
| what it **does** do | every `C_raw` endpoint is additionally reported **with** and **without** those 8 cells, as a **descriptive** sensitivity, so a reader can see their influence. Neither read may be selected after the fact: **the with-them read is the endpoint**, and the without-them read is reported beside it and labelled descriptive |
| prohibition | **no analyst may aggregate a `C_raw` quantity over cells without carrying this flag through.** An aggregate that drops it is not reportable |

The 8 cells are 8 / 960 = **0.0083** of the corpus and at most 8 / 12 of one system's cells are
involved; the realized per-system exposure is reported. This does not make the exposure harmless — it
bounds it, which is a different statement.

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

**NEW in v2.1 — M1's length row is promoted to a registered descriptive endpoint.** The row
**"cells where the GT is longer than every candidate = 0.6302"** is registered as **`S12`** (§8.5c),
with per-system, per-family and per-stratum reporting on the realized usable denominator.
**Disclosed as prior information, since registering an already-measured quantity requires it**: the
pre-freeze value over all 960 cells is **0.6302**, and the run recomputes it over the realized
**usable**-cell denominator, which is a different and generally smaller denominator (§2.1b). Because
`S12` is **descriptive, bears no decision, has no threshold and may not be used for attribution**
(§8.5c), registering a known value creates no researcher degree of freedom that rule 01 item 3 is
concerned with — but it is labelled `pre_measured_before_freeze: true` in every artifact so that no
reader mistakes it for a quantity this cycle first discovered.

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
| PC-GREEDY | ≥ 2 of 40 | **new_no_derivation**, **not moved** | disclosed, with the operating characteristic stated: `P(X ≥ 2 | n = 40)` = 0.9985 at a true rate of 0.20, **0.6009** at 0.05, 0.1905 at 0.02. **v2.1: the bar is unchanged and the control is now REPORT-ONLY (§10, 決定 3)** — its achievability in `C_gen` is `unverified` and an unverified control may not sit on a gate. The bar is retained so the reported figure has a stated reference point, not because anything depends on clearing it |
| PC-HOLDOUT / NC-HOLDOUT | ≥ 0.95 / ≤ 0.05 | **derived** | arithmetic on a strict maximum / minimum |
| NC-CONDITION | ≥ 0.95 of control cells with `|Δ| > 1` nat | **new_no_derivation**, **not moved** | measured population rate **0.95** (M4), i.e. exactly at the bar; `P(pass | 40 cells, p = 0.95)` = **0.6767** |
| `C_gen` reconstruction | ≥ 0.98 | **new_no_derivation**, **not moved** | measured **0.9683** in `C_gen` — does not clear (§7.3). **v2.1: the bar is in exactly the same place; what changed is what failing it does.** It no longer selects a primary context (there is no fallback); it attaches a named qualifier to the `C_gen` read and routes the affected candidates through §2.1b's usable-candidate filter and §8.2's existing cascade (§10, §11) |
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
8. **NEW in v2 — any sentence attributing the corpus to E2 *or* E3, or using the words "predominant"
   or "attribution" for the pair.** §13 replaces them. Where "predominant" survives it names a
   **certificate rate**, never which failure mode obtains.
9. **NEW in v2.1 — presenting agreement between `C_gen` and `C_raw` as confirmation, corroboration,
   replication, robustness evidence or a "double" anything.** The two contexts share the model, the
   truths and the candidate set. They are **not** independent, they are not two experiments, and the
   second is not a replication of the first (§19 says what a replication would have to change).
   §8.7 freezes the sentence that must be used instead.
10. **NEW in v2.1 — Certificate-S language applied to a `C_raw` result**, and **any use of `S12`
    (the length census) as evidence for E2, for E3, or for any attribution.** §8.7 and §8.5c.
11. **NEW in v2.1 — citing PC-GREEDY as a gate, or as licensing or blocking any conclusion.** It is
    REPORT-ONLY (§10.2b). Its value is reported; nothing depends on it.

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
**both** decision rules; the `0.5` system cutpoint; **the two CO-PRIMARY scoring contexts, the
absence of any fallback between them, and which certificate language each carries**; the
admissible-encoding enumeration, its cap and **which quantity carries which certificate**; the
control battery, every control threshold **and every control's class**, PC-GREEDY's REPORT-ONLY class
included; the usable-candidate / usable-cell / evaluable-system definitions and the per-system floor;
**the `pre_freeze_exposed` marking rule of §0.3a**; **`S12` and its prohibition on attribution**; all
exclusion rules; all seeds; **the fixed-stratum cluster definition and the interval of record**; the
`H0010` predicates, **the frozen `H0010` corpus** and the graded rule; and the compute ceiling.
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
| `H0001-R` P1/P2, **each of the two co-primary contexts** | **80** systems / **960** cells / **47,987** candidates → reported as `n_eval` evaluable systems (§2.1b), **separately per context**, since usability is context-dependent (§2.1b's `C_gen` free-symbol clause) | counted directly | **no** |
| S11 in-support subgroup | 71 / 852 / 42,593 | counted directly | no |
| **S12 length census (§8.5c)** | the realized **usable**-cell count, reported per context, per system, per family and per `(noise_sigma, subsample_rho)` stratum. Pre-freeze value over all 960 cells is **0.6302** (M1) | counted directly by M1 over the full corpus; recomputed on the realized denominator | no |
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
points. Two declared scoring contexts, both fully specified, **both CO-PRIMARY** by the supervisor's
決定 1 (§7.3). Neither falls back to the other. They differ in **what each may be said to certify**,
not in rank.

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

**`C_gen` — matched conditioning. CO-PRIMARY. The only context that may carry Certificate-S language.**
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

**`C_raw` — raw conditioning. CO-PRIMARY. Certificate-S language is forbidden here.** Raw `times` /
`observed_trajectory`, unscaled, unpermuted, single bag, every sequence in original units — exactly
what `src/gpu_run4/training.py:51 teacher_forced_summed_logprob` does and what C0001 used for `lp_gt`.
**This is the context in which `lp_gt` was already observed on all 960 cells (§0.2) and in which the
8-cell `sb_best` exposure occurred (§0.3);** §0.3a's marking rule applies to every `C_raw` artifact.

**What the F-g argument establishes, and what it does NOT — REWRITTEN in v2.1.**

*It establishes which context may carry which sentence.* Only under `C_gen` is the candidate set the
set the decoder produced *under that conditioning*, so only there does `sb_best = 1` read as a search
error of the decode that actually happened. Under `C_raw`, **Certificate N still holds** — the truth
is certifiably not the argmax under that conditioning — but **Certificate S certifies only that the
truth outscores 50 arbitrary expressions under a conditioning the search never saw**, which is not a
statement about search. That asymmetry is real and it is frozen in §8.7's sentences.

*It does NOT establish that `C_gen` is primary and `C_raw` secondary.* v1 and v2 drew that further
conclusion; v2.1 does not. Certificate N is carried by **both** contexts, P2 is defined on Certificate
N, and `C_raw` is where the truth is scored **exactly**, without the 4-significant-digit approximation
`C_gen` imposes (F-k, §7.3). A context that scores the truth exactly and certifies non-argmax is not
a "robustness arm". **Both are co-primary; each is reported with the language it can carry.**

**v1's secondary reason — that the leakage of §0.2/§0.3 is entirely under `C_raw` — was withdrawn as
a justification in v2** and retained only as a disclosure (§0.3 item 5). **v2.1 goes further**: since
`C_raw` is now co-primary, the observation is prior information bearing directly on a reported
endpoint (§0.3 item 2, §0.3a), and it is disclosed as such rather than reasoned away.

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

**Gate 3 is evaluated PER CONTEXT (NEW in v2.1).** With two co-primary contexts there is no single
"primary" in which to run it, and the realized values differ between them by construction (F-j). The
frozen rule, which introduces no new threshold:

- **3a** must hold in a context for that context's `H0001-R` read to exist. If it fails in one
  context only, **that context's** read is `undecidable (no admissible encoding)` and the other
  context's read stands, reported alone, with §13.4's disagreement rule applying.
- **3b**'s downgrade attaches to **the context in which it failed**. Measured: it is met **80 / 80**
  in `C_raw`, and in `C_gen` it rests on orbit members alone with achievability `unverified` (F-j).
  So `BA3 not_measurable` — and the supported-E2 block it carries (§8.5) — is expected to bind in
  `C_gen` and not in `C_raw`. **This changes nothing about reachability**, because BA2 already blocks
  a supported E2 in both contexts (§0.0 item 1); it is recorded so that the per-context qualifiers
  are not discovered at reporting time.
- **3c** is REPORT-ONLY per context.

### 7.3 The `C_gen` / `C_raw` decision — TAKEN, and what it binds

v2 escalated this as a fork. **The supervisor decided it on 2026-09-12, before Gate 4 runs**
(`plans/C0002_supervisor_decisions.md` 決定 1). This section records the decision, the options
rejected, and the conditions that ride with it. It is no longer a fork and no longer a
"named contingency".

**The measured facts, unchanged from v2.** Gate 4's `C_gen` reconstruction condition, re-expressed as
MAJOR-9 RA requires — a real round trip through `env.equation_encoder`, not the vacuous "forward map +
inverse to 1e-8" that any invertible map passes and that never reaches the tokenizer — measures
**0.9683** in `C_gen` against its frozen `≥ 0.98` bar, and **0.9917** in `C_raw` (M5). The numeric
round trip in `C_gen` is accurate to `rtol = 1e-3` on only **0.275** of cells, median relative error
**2.03e-3**, max **1.05e-1**; in `C_raw` it is exact (F-k). The cause is the encoder's
4-significant-digit constant quantization (`float_precision = 3`, `float_descriptor_length = 3`,
`odeformer/envs/encoders.py:124`), which is lossless on original-unit GRN constants and lossy on the
arbitrary reals `C_gen` produces.

**The bar is NOT moved.** Setting the tolerance from the measured distribution would be exactly the
forbidden move. **`≥ 0.98` stands, byte for byte as v2 froze it.**

#### 7.3.1 The decision: both contexts CO-PRIMARY, no fallback

**FROZEN.** `C_gen` and `C_raw` are **co-primary**. P1 and P2 are computed and reported in **each**.
**There is no fallback from either to the other, in either direction, under any gate outcome.**

**Options rejected, with reasons, recorded so the choice is auditable:**

| option | disposition | reason |
|---|---|---|
| v2's frozen fallback — `C_gen` fails Gate 4 ⇒ `C_raw` becomes primary | **REJECTED. Removed from this contract.** | It is the worst of the three on research-integrity grounds. It would promote to primary the context in which **`lp_gt` was already observed on all 960 cells** (§0.2) and in which the **8-cell `sb_best` exposure** occurred (§0.3) — i.e. it would report the primary endpoint in a context already seen, in the direction the campaign prefers. It would also **silently change what the cycle measures**: Certificate-S was tied to `C_gen` precisely because that is where the search ran |
| move Gate 4's `≥ 0.98` | **REJECTED, out of the question** | rule 01 item 3. The methodologist was right not to move it, and v2.1 does not |
| **both co-primary, no fallback** | **ADOPTED** | (1) it privileges no already-observed context; (2) it keeps Certificate-S tied to the context the search actually ran in; (3) **disagreement between the contexts is itself a finding** — if the E2 / E3 reading depends on the conditioning context, that is a reportable fact bearing directly on the question this cycle asks about the generator, and BA4 already computes it; (4) the cost — doubled reporting intervals, and a weaker claim from a single agreeing result — is acceptable, and is marginal given that BA2 has already made a supported E2 unreachable |

**Compute cost of the decision: effectively zero.** §14 already budgeted the 960-cell pass across
**both** contexts (0.47 GPU-h of a 4.0 GPU-h ceiling), because v2 computed the non-primary context for
BA4 anyway. Co-primacy renames what was already being computed; it does not buy new compute.

#### 7.3.2 The four conditions that ride with the decision — all binding

**Condition 1 — `C_raw` carries the downgraded sentence, and only it.**
A `C_raw` result licenses exactly this, verbatim (§8.7):

> the truth outscores all 50 candidates under a conditioning the search did not see.

**That is not a search-error claim.** Certificate-S language — "a search error is certified", "the
returned set does not contain the global best", and every paraphrase — is **restricted to `C_gen`**.
`LB(P1 | C_raw) > 0.5` does **not** fire `H0003` and does **not** refute `H0001-R` in the
search-error sense. Certificate N is unaffected: it holds in both contexts, so P2 carries its full
meaning in each.

**Condition 2 — the 8-cell exposure is prior information, disclosed and marked.** §0.3 (disclosure,
with the cells listed) and §0.3a (the `pre_freeze_exposed: true` marking rule and the with/without
descriptive sensitivity).

**Condition 3 — `C_gen` scores an approximation of the truth, and says so.**
`gt_is_quantized_in_context: true` is carried on **every** `C_gen` artifact. Stated plainly, as the
decision requires and as no reader may be left to infer:

> **The truth scored in `C_gen` is a 4-significant-digit approximation of the truth, not the truth.**

This is not an error in the endpoint — both `lp_gt` and `lp_best` are scored on quantized sequences,
so they remain commensurable, and F-d already establishes that constants are ordinary vocabulary
tokens. It is a statement about what the `C_gen` number is a number about. §8.7 makes reporting a
`C_gen` result without the flag a contract violation.

**Condition 4 — agreement is NOT double confirmation.**

> **FROZEN SENTENCE, binding on the cycle report, the analysis and any synthesis.**
> The two scoring contexts **share the model, share the ground truths and share the candidate set**.
> They are two conditionings of one instrument, not two experiments. **Agreement between them is
> therefore not confirmation, not corroboration, not replication and not independent support**; it
> means the certificate rate is insensitive to the conditioning within this one instrument, and
> nothing more. Disagreement is informative (§13.4); agreement is not.

This is the same error as C0001's "three independent derivations agree", found by the independent
reviewer as NOTE-R4 (`reviews/C0001_independent_review.md`) and carried in `research_state.md` as a
standing correction, which the supervisor's decision record cites as 訂正 2. It is frozen here so it
cannot recur by omission.

**NEW in v2.2, RE-GROUNDED in v2.3 — for P1 there is a SECOND and INDEPENDENT reason, and it is the
stronger one.** The non-independence above is about *shared inputs*. For P1 the objection is prior to
that: **the `C_raw` value is not a claim about the decode that produced the candidate set.**
Certificate S is indexed to a historical decode event and **there was exactly one decode**, under
generation conditioning (rule 0). `C_gen`'s P1 is a certified search-error rate for the search that
actually ran; `C_raw`'s P1 describes a search that never happened, which §13.2 branch 1 and §8.7 both
state is **not** a search-error claim. So for P1 the `C_raw` value:

- **may not be read as confirmation** when it agrees (non-independence, **and** it is not about the
  decode that ran);
- **may not be read as disconfirmation, a failed check, a robustness failure or a reason to doubt**
  when it disagrees (same reason). §8.7 forbids both readings by name.

*(v2.2 grounded this on the two values being "not the same quantity" / "non-commensurable". That
ground was withdrawn in v2.3 as false and symmetric — see rule 0. **The prohibition itself is
unchanged and now rests on a premise that survives scrutiny.**)*

**It is nevertheless reported, mandatorily, with the difference** (§13.4 rule 1b). Withholding it
would be worse: a reader must be able to see how far the two conditionings move the number, even
though that movement adjudicates nothing.

#### 7.3.3 What Gate 4's `≥ 0.98` governs now — one disposition, stated once

**The bar is in the same place. What changed is what failing it does**, because there is no longer a
primary for `C_raw` to become.

| Gate 4 `C_gen` reconstruction | frozen disposition |
|---|---|
| **≥ 0.98** | `C_gen` results carry Certificate-S language without a reconstruction qualifier |
| **< 0.98** (predicted: 0.9683) | **DOWNGRADE, scoped to `C_gen`.** `cgen_reconstruction_below_bar: true` is carried on every `C_gen` artifact and **every** `C_gen` Certificate-S sentence must be reported with it. **No context becomes primary and none is dropped.** The affected candidates are not silently kept: a candidate whose re-encoding round trip is not exact is **already not a usable candidate** under §2.1b, so they flow through §8.2's existing cascade — counted as `CandidateReencodingMismatch`; > 10% of a cell's candidates ⇒ that cell is `unreliable_reencoding` **in `C_gen`**; > 10% of `C_gen` cells ⇒ `H0001-R` **in `C_gen`** is `undecidable`, with the `C_raw` read still reported and §13.4 applying. **No new threshold is introduced by this row** — every number in it is inherited from §2.1b and §8.2 |

**Why a downgrade and not an abort.** The bar measures whether the encoder round trip reproduces its
own token sequence on control-cell candidates. A shortfall of ≈ 3.2 pp means a small minority of
candidates cannot be scored reliably in `C_gen`; the contract already has a filter that removes
exactly those candidates and a cascade that escalates to `undecidable` if the minority is not small.
Making Gate 4 abort-class on top of that cascade would be a second, redundant disposition for one
condition — the C0001 Gate B→C defect that §7.2b exists to prevent.

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
| **P1** | **`certified_search_error_system_rate` = Σ_s E3_system(s) / n_eval**, computed **in each of the two co-primary contexts**, reported as `P1(C_gen)` and `P1(C_raw)` | **PRIMARY, in both contexts** | §12.1's interval of record, one per context |
| **P2** | **`certified_non_argmax_system_rate` = Σ_s E2_system(s) / n_eval**, computed **in each of the two co-primary contexts**, reported as `P2(C_gen)` and `P2(C_raw)` | **CO-PRIMARY, in both contexts** | same |
| S1 | **REDEFINED in v2.1**: the **cross-context comparison** of the four co-primary reads — `P1(C_gen)` vs `P1(C_raw)` and `P2(C_gen)` vs `P2(C_raw)`, at the §13 decision level and as paired per-system indicator agreement. *(In v2 S1 was "P1 and P2 recomputed in the non-primary context"; with no non-primary context, the recomputation is now the endpoint itself and S1 is the comparison.)* | **BA4** | §13.4. **Agreement may not be reported as confirmation (§7.3.2 condition 4)** |
| S2 | mean `sb_rate` and `me_rate` across systems; the **cell-level** `sb_best`, `me_best` and `neither_cert` rates **with their denominators** | descriptive | Wilson on the stated denominator, **labelled cell-level and never compared to a system-level rate** (m-2 SR) |
| S3 | paired `lp_gt_max − lp_best` and `lp_gt_lse − lp_best` per system in nats, **summed**; and the per-token version | descriptive | stratified bootstrap. **The per-token version may not bear a decision** |
| S4 | `Δ_enc`, `Δ_maxlse`, and `encoding_flip_rate` = fraction of **systems** on which logsumexp vs single flips `E2_system` | **BA3**, **blocking** | descriptive |
| S5 | per-position GT-token-rank profile by token class (operator, mantissa, exponent, `\|` separator) | descriptive | `classify_token_class` at `src/gpu_runclaude1/partc.py:162` |
| S6 | `argmax_agreement_best` distribution, aggregated **to the system level** | **BA1**, **blocking** | descriptive |
| S7 | `sb_best_len` and `me_best_len` — the length-controlled companions — plus `length_matched_partner_available_rate` and the in-window partner count distribution | **BA2**, **blocking** | descriptive |
| S8 | `rank_pct_sum(c)` = fraction of usable candidates scoring above `lp_gt_max`; `below_all_indicator`; the IQR of the candidate scores and the GT gap in IQR units | descriptive | **carries the frozen v2.1 §8.3 C2-S6 note verbatim**: the candidates were drawn at T = 0.1 and are an extreme upper-tail sample; a low rank does not establish model error and **no E2/E3 statement may cite these** — see §8.5b for the adjudication this required |
| S9 | instrument audit panel: re-encoding mismatch rate, `unreliable_reencoding` cell rate, `EncodingVerificationFailure` rate, `CellIdentityMismatch` rate, the 10-distinct-payload check, the `sum/n == −mean_CE` regression result, `wall_clock_guard_fired` count **broken out by endpoint**, `parse_not_admitted_unbounded` count, `rescale_function_early_return_suspected` count, `system_not_evaluable` count and the per-system usable-cell distribution | descriptive | gates §11 |
| S10 | GT token length vs `lp_gt_max` and vs `sb_best` | **exploratory** (rule 01 item 9) | — |
| **S11** | **P1 and P2 recomputed on the 71 in-support systems**, in both co-primary contexts | **preregistered sensitivity subgroup** (§4) | same. **May not be promoted to primary** |
| **S12** | **`gt_longer_than_every_candidate_rate`** — the registered length census of §8.5c, reported per system, per family and per `(noise_sigma, subsample_rho)` stratum, with the realized denominator | **registered DESCRIPTIVE endpoint** (決定 2) | **none. No interval bears a decision, no threshold is applied, and it may not be used for attribution** (§8.5c) |

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
| **BA2** | summed log-probability is length-confounded — D19-1331's own central finding (§4, Tab. 1, Figs. 1/3) — and Hill truths are token-longer than the polynomial candidates that dominate the realized vocabulary | a cell **contributes** iff it has **≥ 3** in-window partners (`\|len − len_gt\| ≤ round(0.20 · len_gt)`); `sb_best_len` / `me_best_len` computed on contributing cells; aggregated to systems; `length_matched_partner_available_rate` = fraction of usable cells contributing | if the availability `< 0.5`: **`length_control_not_measurable`**, and **that BLOCKS a supported E2**, yielding `E2_direction_observed_but_length_unaudited`. v1 merely reported it, and §13 triggered the confounded verdict only when BA2 "fails its disagreement bar" — so an **unmeasurable** control, being neither a pass nor a fail, let a supported E2 through with the length confound entirely unaudited. **Measured before freeze: 0.4625 at the frozen floor of 3, 0.4990 at the lowest admissible floor of 2 — so this branch is predicted to fire (§0.0 item 1).** Where it does run, if `sb_best_len`/`me_best_len` disagree in direction with `sb_best`/`me_best` on **> 20%** of contributing systems, the verdict is `E2_direction_observed_but_confounded`. **Length normalization itself breaks the monotonicity that makes γ admissible** (D19-1331 §2), so no normalized variant may replace the raw certificate. **v2.1: the structural fact that makes BA2 unrunnable is separately registered as the descriptive endpoint `S12` (§8.5c). `S12` does not rescue BA2, does not substitute for a length control, and may not be offered as evidence for E2 — a distribution fact is not a mechanism. BA2's 0.50 cutoff, its `±round(0.20 · len_gt)` window, its floor of 3 and its > 20% disagreement bar are all unchanged** |
| **BA3** | a single-encoding `lp_gt` is a lower bound on the truth's probability, and the enumeration `E(s)` is itself capped (§7.2) | `Δ_enc`, `Δ_maxlse`, and `encoding_flip_rate` = fraction of **systems** on which `E2_system` flips between the logsumexp and the single-encoding read | if `encoding_flip_rate > 0.05`, or if Gate 3b failed so that the logsumexp arm is `not_measurable`: **a supported E2 is BLOCKED**. v1's consequence ("only the logsumexp read is reportable") was a **no-op**, because the primary already *was* the logsumexp. The blocking form is the one that bites: a high flip rate demonstrates that the endpoint is sensitive to a nuisance **whose full extent is unmeasured**, since `Δ_enc` moves only within the enumerated set |
| **BA4** | the generation conditioning is not the scoring conditioning (F-g), **direction unknown** | S1 — **the cross-context comparison of the two co-primary reads** (§8.4). Reported at two resolutions: (i) whether the two contexts fire the **same §13.2 branch**, and (ii) the paired per-system agreement rate of `E3_system` and of `E2_system` across contexts, with its denominator | **SCOPED in v2.2, per certificate.** **For P2**: if the two contexts disagree at the §13 decision level, the cycle-level P2 verdict is **`conditioning_sensitive`** and **nothing is concluded about the non-argmax certificate** (§13.4 rule 2b) — unchanged from v2 in threshold and in consequence. **For P1**: the comparison is **DESCRIPTIVE AND MANDATORY TO REPORT, and it does not gate** (§13.4 rule 1b). `C_raw`'s P1 is not a search-error claim by this contract's own §13.2 branch 1, so a disagreement with it can neither withdraw nor qualify `C_gen`'s certificate — the quantities differ. **If the contexts agree, BA4 licenses NOTHING additional** for either certificate: they are not independent (§7.3.2 condition 4), and for P1 they are additionally not the same quantity. **BA4's threshold is not moved; BA4 is not weakened as a bias audit, because its direction was always "unknown" and it never protected against the preferred answer — the audits that do (BA1, BA2, BA3) are untouched, and BA4 still blocks the preferred P2 branch in full** |

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

### 8.5c `S12` — the registered length census (NEW in v2.1, 決定 2)

**Why this is an endpoint and not a footnote.** M1 measured, with the real model tokenizer, over the
full 960-cell corpus and all 47,987 candidates with **zero tokenizer failures**, that on **0.6302** of
cells the ground truth is token-longer than **every** candidate in its cell (median GT length **48**
against a median per-cell maximum candidate length of **38.5**). In v2 that fact appeared only as the
structural explanation for BA2's unavailability. The supervisor promoted it because it is
**structural evidence about the generator**, which is what this cycle asks about, and because it has
three properties nothing else in this contract has at once:

1. it depends on **no log-probability**;
2. it depends on **none** of the contested certificate machinery — not `sb_best`, not `me_best`, not
   `lp_gt_max`, not `lp_gt_lse`, not F-i's split;
3. it depends on **neither scoring context** — token length is a property of the encoding, and the
   `C_gen` / `C_raw` choice does not enter it.

It is already measured, at **zero additional compute**.

**Frozen definition.** For a usable cell `c`, `gt_longer_than_every_candidate(c) = 1[len_gt(c) >
max_over_usable_candidates len_cand(c)]`, with `len` the **model tokenizer** length via
`gpu_runclaude1.partc_reencoding.infix_to_model_tokens`, `len_gt` from
`partC_cell_records.jsonl`'s `gt_token_length`. `S12 = Σ_c gt_longer_than_every_candidate(c) / n_usable_cells`.

**Frozen reporting obligations — all four required, omission is a contract violation:**

| level | what is reported |
|---|---|
| corpus | `S12` **with its realized denominator stated** (`n_usable_cells`, not the nominal 960), beside the pre-freeze full-corpus value **0.6302** on 960 cells |
| per system | the per-system rate over that system's usable cells, and the distribution across the 80 systems |
| per family | the rate within each of the eight fixed strata R01–R08, with each family's denominator |
| per stratum | the rate within each of the four `(noise_sigma, subsample_rho)` settings, with each denominator |

Also reported: the median GT token length and the median per-cell maximum candidate token length, at
each level; and the companion `gt_inside_candidate_length_hull` rate. Every `S12` artifact carries
`pre_measured_before_freeze: true` (§0.7) and `endpoint_type: "descriptive"`.

**Frozen prohibition — this is the load-bearing half of the registration.**

> **`S12` may NOT be used for attribution.** It is a fact about a **length distribution**, not a
> mechanism. It may **not** be offered, on its own or as the leading evidence, as support for E2, for
> E3, or for any statement about which failure mode obtains. It may **not** be used to explain,
> excuse or substitute for BA2's `length_control_not_measurable`. **No threshold is applied to it, no
> interval on it bears a decision, and no branch of §13 reads it.**

This is the same discipline rule 01 item 6 applies to numerical fit: a distribution fact is not a
mechanism, exactly as a fit is not a recovery. What `S12` legitimately supports is the **design of
C0003**: it quantifies, per family and per corruption setting, where a length-auditable corpus would
have to differ from this one.

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
- **NEW in v2, forbidden**: reporting a `C_gen` result without `gt_is_quantized_in_context: true`
  (§7.3), or a P2 result without S8's co-report (§8.5b).

**NEW in v2.1 — the co-primacy sentences (§7.3.2).**

- **Permitted, and REQUIRED as the ONLY licensed reading of a `C_raw` Certificate-S-shaped result**,
  verbatim: "**the truth outscores all 50 candidates under a conditioning the search did not see.**"
  It must be accompanied by: "This is **not** a search-error claim."
- **Forbidden**: any Certificate-S language applied to a `C_raw` result — "a search error is
  certified", "the returned set does not contain the global best", "the search failed", and every
  paraphrase. Certificate-S language is **restricted to `C_gen`**.
- **Permitted** in `C_raw`, unchanged: Certificate N's sentence. `me_best = 1` certifies non-argmax in
  **either** context.
- **Permitted, and REQUIRED wherever a `C_gen` result appears**, verbatim: "**The truth scored in
  `C_gen` is a 4-significant-digit approximation of the truth, not the truth.**"
- **REQUIRED wherever a `C_gen` Certificate-S result appears while Gate 4's reconstruction condition
  measured below `≥ 0.98`**: the qualifier `cgen_reconstruction_below_bar`, with its realized value.
- **Forbidden**: presenting agreement between `C_gen` and `C_raw` as confirmation, corroboration,
  replication, robustness evidence, "both contexts agree, therefore", "double", or any construction
  that treats the second context as independent support.
  **REQUIRED instead, verbatim, wherever the two contexts agree**: "**The two contexts share the
  model, the ground truths and the candidate set. Their agreement means the certificate rate is
  insensitive to the conditioning within this one instrument; it is not independent confirmation.**"
- **Forbidden**: any sentence offering `S12` — "on 0.6302 of cells the truth is longer than every
  candidate" and its variants — as evidence for E2, for E3, or for any attribution, or as a substitute
  for the length control BA2 could not run. Where `S12` is reported it must be accompanied by:
  "**This is a fact about the length distribution, not a mechanism.**"
- **Forbidden**: describing PC-GREEDY as a gate, or citing it as licensing, blocking, supporting or
  refuting anything. It is REPORT-ONLY (§10.2b); its realized value is reported and nothing depends
  on it.

**NEW in v2.2 — the P1 co-report sentences (§13.4 rule 1).**

- **REQUIRED wherever a cycle-level P1 result is reported**: `LB(P1 | C_raw)` with its own `n_eval`
  and interval, its downgraded sentence verbatim, the point difference `P1(C_gen) − P1(C_raw)`, and
  the paired per-system `E3_system` agreement rate with its denominator. **Omitting any of the four is
  a contract violation.**
- **Forbidden**: presenting `LB(P1 | C_raw)` as confirming, corroborating, validating or "checking"
  the `C_gen` P1 — and, equally, **as disconfirming, undermining, failing to replicate or casting
  doubt on it.** Two independent reasons: the contexts are not independent, **and** — re-grounded in
  v2.3 — **the `C_raw` value is not a claim about the decode that produced the candidate set**
  (§13.4 rule 0, §7.3.2 condition 4). There was exactly one decode; a Certificate-S-shaped number
  computed under a conditioning no decode used describes a search that never happened, and such a
  number neither confirms nor disconfirms a statement about the search that did.
- **Forbidden**: any sentence in which a cross-context P1 difference is offered as evidence that the
  **search-error rate** depends on the conditioning. The difference is between a search-error
  certificate and a quantity that is not one. Where part of it is traceable to a known instrument
  asymmetry, §13.4 rule 5 **requires** that to be stated.
- **Forbidden**: reporting a cycle-level P1 verdict as `conditioning_sensitive` on the strength of a
  cross-context P1 disagreement. That branch is P2's (§13.4 rule 2b); for P1 only rule 3's
  `(one context undecidable)` form can arise.

**NEW in v2.2 — the `L*` limitation must reach the reader, not sit in a control's rationale.**

- **REQUIRED in the LIMITATIONS SECTION of the cycle report, not only in §10.2b**: "**No control in
  C0002 demonstrates that a sequence outside the stored candidate set can outscore `lp_best`.**
  PC-GREEDY, the only control that could have, is REPORT-ONLY because its expected value is
  unverified in `C_gen` (§10.2b). This follows from `L*` being unknowable from the stored artifacts —
  which is precisely why `sb_best` is a **certified lower bound** and not an estimate (§1.1, §8.6)."
  Placing it only in a control's rationale would leave a reader to find a structural limitation by
  reading a gate table.

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
| **PC-GREEDY** | greedy decode from the cell's cached encoder state (`decoder.generate(..., sample_temperature=None, max_len=200, seed=self.generation_seed)` — `model_wrapper.py:74-81` runs unconditionally, before the `beam_type` branch at `:101/:140`), ids → tokens via `env.equation_id2word`, scored with the same `teacher_forced_summed_logprob_batch`; `1[lp_greedy > lp_best]`. **Run and reported in BOTH co-primary contexts** | **≥ 2 of 40**, **unchanged** | **2 / 10 on a disjoint probe**, margins `lp_greedy − lp_best ∈ [−45.21, +32.29]` nats — **`C_raw`, `unverified_for_C_gen`**. Operating characteristic: `P(X ≥ 2 \| n = 40)` = **0.9985** at a true rate of 0.20, **0.6009** at 0.05, **0.1905** at 0.02 | **REPORT-ONLY (CHANGED in v2.1, 決定 3).** Counted and reported per context; **no endpoint changes and nothing aborts, downgrades or is blocked on it, in either direction.** See §10.2b for why the demotion was required and what still covers the gap it leaves |
| **PC-HOLDOUT** | the **highest**-scoring usable candidate of a control cell as pseudo-truth, `sb_best` against the rest | ≥ 0.95 return 1 | 1.000 by construction on any cell with a strict maximum; tied-maximum cells counted and excluded from the denominator | **ABORT-CLASS.** The indicator plumbing cannot produce a 1; `H0001-R` is `undecidable (indicator plumbing not demonstrated)` |
| **NC-HOLDOUT** | the **lowest**-scoring usable candidate as pseudo-truth vs the rest | ≤ 0.05 return 1 | 0.000 by construction | **ABORT-CLASS.** The indicator fires where it must not |
| **NC-CONDITION** | score the truth against an encoder pass built from a cell of a **DIFFERENT system**, drawn per cell with `CONTROL_CELL_SEED` | ≥ 0.95 of control cells show `\|Δ\| > 1` nat | **0.95 measured over 200 cells (M4)** — i.e. **exactly at the bar**, median `\|Δ\|` **13.08** nats, min 0.0091, max 123.88, **0 exact zeros**. `P(pass \| 40 cells, p = 0.95)` = **0.6767** | **DOWNGRADE-CLASS.** The scorer's conditioning-dependence is `not_demonstrated_at_cell_level`; **BA4's context comparison is reported `uninterpretable`**, which by §8.5 BA4 blocks any conclusion resting on context agreement. Not abort-class, because the measured median of 13.08 nats establishes that the instrument does respond — the per-cell binary is what is fragile |
| **NC-SHUFFLE-TOKENS** | score a random permutation of the GT token list | must score **below** the GT encoding, ≥ 0.95 | not separately verified | **REPORT-ONLY.** Downgrades S5 only; gates nothing |
| **PC/NC-H0010** | the 12 frozen synthetic cases of §10.4 | **12 / 12** | **12 / 12 measured** under `sympy 1.13.1`; 4 of the 12 produce `P_joint = True` | **ABORT-CLASS for `H0010` only.** `H0010` is `undecidable (predicate battery failed)`. `H0001-R` is unaffected |
| **regression identity** | `sum_logprob / n_scored_tokens == −teacher_forcing_loss(...)` (`src/gpu_run4/training.py:66-70`) | < 1e-5 on ≥ 5 fixed examples | **CORRECTED (MAJOR-8 RA):** `phase3/partC_instrument_test.json`, 960 checks, `tolerance: 1e-05`, **0 over tolerance**; `identity_error` min **`0.0`** (17 exactly zero), smallest non-zero **`1.2226593959496768e-08`**, max **`2.8991699210223487e-06`**. Realized margin **3.45×**. v1's quoted `7.3e-08 … 8.1e-07` was wrong at both ends | **ABORT-CLASS.** The scorer does not compute what it claims |
| **`C_gen` reconstruction** | **REDEFINED (MAJOR-9 RA):** `env.equation_encoder.encode` → `.decode` → `encode` **token-identity** round trip on control-cell candidates, **in `C_gen`**. v1's "forward map + inverse recovers the original to 1e-8 relative" is **vacuous** — any invertible map passes it, and it never goes through the tokenizer, so it cannot see the 4-significant-digit constant quantization | ≥ 0.98, **unchanged, not moved** | **0.9683 in `C_gen`; 0.9917 in `C_raw`** (M5). **Does not clear in `C_gen`** | **DOWNGRADE-CLASS, scoped to `C_gen` (CHANGED in v2.1).** v2 called this NAMED-CONTINGENCY because the contingency was "`C_raw` becomes primary"; **that fallback is removed** (§7.3.1), so the class is now the ordinary downgrade §7.3.3 states in one row: `cgen_reconstruction_below_bar: true` on every `C_gen` artifact, every `C_gen` Certificate-S sentence reported with it, and the affected candidates routed through §2.1b and §8.2's **existing** cascade. **No new threshold** |
| **re-encoding round trip** | §8.2 | ≥ 0.90 per control cell | 300/300 in original units, **`unverified_for_C_gen`**; M5's `C_gen` candidate figure is 0.9683 | **DOWNGRADE-CLASS.** Affected cells become `unreliable_reencoding` per §8.2's own cascade |

### 10.2b Why PC-GREEDY was demoted, and what covers the gap (NEW in v2.1, 決定 3)

**The rule being applied.** A control whose expected value has **not** been verified achievable must
not sit on a gate. C0001's near-fatal defect (MAJOR-R6) was exactly this shape: a design in which no
control could produce a non-zero value of the primary indicator, so a zero result was
**indistinguishable from a broken instrument**. Rule R2 (`research_state.md` §8b) states it as a
standing campaign rule: *a control is not well defined until the population it runs on is verified to
have the property the control assumes.*

**Why PC-GREEDY fails that rule here.** Its only achievability evidence is **2 / 10 under `C_raw`**,
and it **cannot** be re-measured in `C_gen` before freeze, because that requires `lp_best` under
`C_gen`, which §0.4 forbids (§21 item 9). With `C_gen` co-primary, an ABORT-class PC-GREEDY would
have been a hard abort on a co-primary endpoint resting on an expected value never verified in that
context — the C0001 defect reproduced.

**Considered and rejected: gate it in `C_raw` only.** Its `C_raw` achievability *is* verified
(2 / 10). But an abort in one co-primary context that kills or does not kill the other is a second
disposition for one condition, which §7.2b exists to prevent; and it would let a control verified in
the **already-observed** context gate the cycle. Rejected.

**Adopted: REPORT-ONLY in both contexts.** The `≥ 2 of 40` bar is retained unchanged as the stated
reference point for the reported figure — **it was not moved, and it now gates nothing.**

**What is lost, stated plainly rather than left implicit.** PC-GREEDY was the only control that could
demonstrate that a sequence **outside the stored candidate set** can outscore `lp_best` — i.e. that
Certificate S has live opportunity against a real competitor the decoder itself produced. That
demonstration is now **reported, not required.**

**What still covers the gap, and what does not:**

| protection | still in force? | detail |
|---|---|---|
| "a zero P1 is not distinguishable from a scorer that cannot produce a 1" | **YES — PC-HOLDOUT** | PC-HOLDOUT remains **ABORT-CLASS** and its expected value is **verified achievable by construction**: on any control cell with a strict maximum, using the highest-scoring usable candidate as pseudo-truth returns `sb_best = 1`. It demonstrates the indicator **plumbing** can produce a 1 in the context it runs in, which is precisely the C0001 defect's antidote |
| "the indicator fires where it must not" | **YES — NC-HOLDOUT** | ABORT-CLASS, expected 0.000 **by construction** on the lowest-scoring usable candidate as pseudo-truth |
| "`lp_best ≈ L*`, so Certificate S was nearly unable to fire" | **YES — BA1** | BA1 **blocks** a supported E2 and declares the falsifier unevaluable via `certificate_opportunity_insufficient` (§8.5, §13.2). It needs no separate achievability verification: `argmax_agreement_best` is a fraction computed from the 960-cell pass itself and is always defined |
| "a real out-of-set competitor **outside the stored candidate set** can beat `lp_best`" | **NO — this is the gap** | It is now a **reported quantity only**, in both contexts. No control demonstrates it and none can before freeze (§0.4). §21 item 9 records it as an accepted limitation rather than absorbing it. **NEW in v2.2, on the supervisor's instruction: this gap MUST ALSO APPEAR IN THE CYCLE REPORT'S LIMITATIONS SECTION**, in the frozen wording of §8.7 — it is structural, it follows from `L*` being unknowable (which is exactly why `sb_best` is a bound and not an estimate), and **a reader must not have to find it in a control's rationale** |

**Explicitly forbidden, so the demotion is not quietly undone.** A PC-GREEDY result of `0 / 40` is
suggestive of `lp_best ≈ L*` and therefore points in BA1's direction. **It may not be wired to BA1,
to any gate, or to any verdict branch** — not even to *block* the campaign's preferred answer. Using
an unverified control to block is still using an unverified control to gate, and the asymmetry is
deliberate: an unverified instrument may not decide anything, in either direction.

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

**There are exactly three classes in v2.1.** v2 used a fourth, `NAMED-CONTINGENCY`, on one row of §10
while listing only three here — a small inconsistency that the removal of the fallback resolves: the
`C_gen` reconstruction is now **DOWNGRADE** (§7.3.3) and no condition anywhere carries a fourth class.
**Where an endpoint exists per context, a class applies to the context in which the condition was
evaluated**, and §13.4 governs what that means for the cycle verdict.

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
11. **NEW (v2.1, §0.3a)** — `phase0/pre_freeze_exposed_cells.json` written with **exactly the 8
    `cell_id`s of §0.3**, **before** any scoring, and asserted to have length 8 and to be a subset of
    the 960. The run asserts that every `C_raw` record carries a `pre_freeze_exposed` boolean, so an
    omitted flag is a machine-detectable contract violation.

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
**Gate 6 consults 3a only.** **Evaluated per context** (§7.2b); a failure's disposition attaches to
the context in which it failed, and the other context's read stands with §13.4 applying.

**Gate 4 — controls, evaluated on 40 cells BEFORE the 960-cell pass.** A failure here costs minutes,
not hours (rule R2 corollary). Classes and dispositions are in §10's table, one row each; they are not
restated here so that there is exactly one contract text per condition for R7 to quote.
**PC-HOLDOUT, NC-HOLDOUT, the regression identity and PC/NC-H0010 are ABORT**; NC-CONDITION, the
re-encoding round trip and the **`C_gen` reconstruction** are **DOWNGRADE**; **NC-SHUFFLE-TOKENS and
PC-GREEDY are REPORT-ONLY**.

**Two changes in v2.1, both stated here and derived in §10:**

- **PC-GREEDY is removed from the ABORT list** (決定 3, §10.2b). Its bar is unchanged and it gates
  nothing. It is **run and reported in both co-primary contexts**, which also yields the `C_gen`
  figure that could not be measured before freeze.
- **The `C_gen` reconstruction is no longer NAMED-CONTINGENCY**, because the contingency it named —
  "`C_raw` becomes primary" — is removed (§7.3.1). It is a **DOWNGRADE scoped to `C_gen`**, with the
  single disposition in §7.3.3's table.

**Every control is evaluated in the context or contexts its row names**, and a control's disposition
attaches only to the context in which it was evaluated. `unverified_for_C_gen` labelling is carried
wherever a figure originates in `C_raw` or in original units (§8.2, §10).

**Gate 5 — smoke.** ABORT-to-RD. A reduced run on 24 cells completes end to end, writes a manifest,
equation records and failure records, **demonstrates resume per §11b**, and projects the full pass at
≤ **2.0 GPU-hours** and ≤ **12 CPU core-hours**. A projection above either bound invokes §18's reduced
design **before** starting, not midway.

**Gate 6 — report.** `H0001-R` endpoints are reported **for a given co-primary context** only if
**every ABORT-class condition passed for that context**: the regression identity; the re-encoding
audit within §8.2's tolerances; every scored cell passed Gate 1; **Gate 3a** (not 3b, not 3c);
**PC-HOLDOUT and NC-HOLDOUT**; the §11b resume-ledger identity; and BA4 computed. Otherwise
`H0001-R` **in that context** is `undecidable`, and the other context's read is reported alone with
§13.4 applying.

**`PC-GREEDY` is struck from this conjunction** (決定 3, §10.2b). **Nothing else is added or removed
from it**; in particular no threshold in it changes, and 3b / 3c remain outside it exactly as v2
froze them.

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

**Four intervals, not two (NEW in v2.1).** With both contexts co-primary, the interval of record is
computed **separately** for `P1(C_gen)`, `P1(C_raw)`, `P2(C_gen)` and `P2(C_raw)`, each on **that
context's** realized `n_eval`. **The estimator, the seed, the resample count, the stratification and
the "more conservative of the two" rule are all unchanged**; only the number of times the unchanged
procedure is run has changed. `n_eval` may differ between contexts, because usability is
context-dependent (§2.1b's `C_gen` free-symbol clause), and **each interval reports its own
denominator**. **The four intervals are never pooled, averaged or combined into one**, and **no
cross-context difference interval is preregistered for either certificate** — no interval is placed on
`P1(C_gen) − P1(C_raw)` or on the P2 analogue, and neither difference is an estimated contrast.

**Scoped in v2.3** *(this sentence was a third orphan of the rule-2 change; §26.3 wrongly certified
§12.1 as needing no edit, and §27.4 records the correction).* v2.2 said the cross-context comparison
"is a branch-level agreement check". **That is true of P2 only.** For **P1** the comparison is a
**mandatory reported point difference plus the paired per-system `E3_system` agreement rate**
(§13.4 rule 1b) which **bears no decision at all** — it is neither a branch-level check nor a contrast,
because by rule 0 there is nothing for it to check. For **P2** it remains the branch-level agreement
check that rule 2 evaluates.

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

**The multiplicity exposure created by two co-primary contexts — RE-DERIVED IN v2.2, separately for
each certificate.** v2.1 answered this with a single intersection–union test across contexts, applied
to both certificates. §13.4 rule 0 removes that answer for P1, so the argument is redone here rather
than patched. **No threshold is moved anywhere in it.**

**Step 1 — how many of the four reported bounds can fire a cycle-level conclusion?**

| bound | can it fire a cycle-level conclusion? | by what |
|---|---|---|
| `LB(P1 \| C_gen)` | **yes** | §13.4 rule 1a, **on its own** |
| `LB(P1 \| C_raw)` | **no** | §13.2 branch 1 and §8.7 restrict it to a sentence that is **not a search-error claim**; §13.4 rule 1d says it fires nothing. It is **descriptive by contract** for the P1 proposition |
| `LB(P2 \| C_gen)` | only **conjoined** | §13.4 rule 2a |
| `LB(P2 \| C_raw)` | only **conjoined** | §13.4 rule 2a |

So the cycle's **decision-bearing** conditions number **three**, not four, and they compose into
**two** possible cycle-level conclusions: one P1 event and one P2 event.

**Step 2 — P2: the intersection–union argument is retained unchanged.** The P2 event requires
`LB(P2 | C_gen) > 0.5` **and** `LB(P2 | C_raw) > 0.5` **and** the §8.5 battery. A conjunction of
one-sided conditions each at level 0.05 is an **IUT** and attains level **0.05 with no correction**,
while being **strictly harder** to fire than either context alone. Unchanged from v2.1.

**Step 3 — P1: there is no multiplicity to correct, because there was never a second test of the
proposition.** The exposure v2.1's conjunction controlled for P1 was an artefact of treating **a
statement about the one decode that ran** and **a statement about a search that never happened** as
two shots at one proposition (rule 0). Once `C_raw`'s P1 is not a claim about search error, there is
**one** test of "a search error is certified on the majority of systems", evaluated **once**, in
**one** context, at a one-sided error rate of **0.05**. Removing the conjunction does not uncontrol an
exposure; it removes a control on a non-exposure. *(v2.2 said "non-commensurable quantities"; that
premise was withdrawn in v2.3, the step's conclusion is unchanged.)*

**Step 4 — the honest statement, which the supervisor asked for in those words: P1 carries a
single-context read.**

- Its error rate is 0.05, from one test, and **it has no internal cross-check.**
- v2.1's conjunction, although mis-derived, **did incidentally give P1 a second hurdle**. v2.2 removes
  it. **That incidental conservatism is gone, and this contract says so rather than implying the
  protection survives in another form.**
- **No threshold was moved to compensate**, and none may be (rule 01 item 3). Raising
  `LB(P1) > 0.5` to buy back the lost hurdle would be the forbidden move in its most tempting shape.
- **What replaces it is external, not internal**: §19's replication gate, which fires **mandatorily**
  on a certified lower bound reported as prevalent. **§19 is P1's only cross-check and may not be
  waived.**
- **NEW in v2.3 — that sentence was a promise v2.2 could not keep, and the promise is now enforceable.**
  The delta review found that v2.2's §19 could be discharged by a factor that leaves P1
  **bit-identical** (`CONTROL_CELL_SEED` draws only the 40-cell control set) or that merely reproduces
  a teacher-forced fp32 number (a fresh process path), and that **no outcome of the gate had any
  consequence** for the P1 verdict. **§19.3 now names the admissible factor for a fired P1** — an
  independently written scorer, or an independently written `C_gen` forward-map reconstruction — and
  **names the insufficient ones with the reason**; **§13.6 preregisters what each outcome does to the
  verdict**, including `failed replication`, which **withdraws** it. **Nothing in this step is
  softened by that repair**: P1 still carries a single-context read, still has no internal
  cross-check, and the incidental conservatism is still gone. What changed is that the replacement is
  now a mechanism rather than a label.

**Step 5 — residual exposures, named rather than assumed away.**

1. **The "report whichever fired" temptation is real and is controlled by a language restriction, not
   by a correction.** `LB(P1 | C_raw) > 0.5` cannot fire the branch, cannot fire `H0003`, and cannot
   carry Certificate-S language (§8.7). This is **machine-checkable** through the
   `certificate_language_permitted` field (§16.2), which is `"certificate_N_only"` on every `C_raw`
   record.
2. **Across-endpoint exposure (P1 versus P2) is still nil, and the v2 argument still carries.**
   `E3_system` and `E2_system` are mutually exclusive per system, so their rates sum to at most 1 and
   both one-sided lower bounds cannot exceed 0.5 **within a context**; P2's conjunction includes
   `C_gen`; therefore the P1 event and the P2 event remain **mutually exclusive**, and the family-wise
   error rate across the cycle's two possible conclusions is **≤ 0.05 with no correction** — by
   **exclusivity**, not by conjunction. **This is a fact about the indicators and must not be
   restated as a claim that the propositions E2 and E3 are exclusive** (§1.1 establishes they are
   not).
3. **Reporting is not testing.** Four bounds are still reported and each carries its own one-sided
   0.05. Two of the four are decision-bearing only in conjunction and one is descriptive by contract.
   No reported bound may be promoted to a cycle-level conclusion outside §13.4.

**Step 6 — the direction of the relaxation, checked explicitly.** Scoping rule 2 to P2 **relaxes a
requirement only on P1**, which is the branch that **refutes** the E2-direction reading and fires
`H0003`. **P2 — the campaign's preferred direction — keeps the full cross-context conjunction, and
every one of BA1, BA2, BA3, BA4 and NC-CONDITION remains a conjunct of it.** The change therefore
makes the campaign's preferred answer **no easier**, and makes the answer against it **not harder than
its own frozen bar already makes it**. A relaxation that ran the other way would require far more than
an internal-consistency argument to justify.

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
- **SCOPED in v2.2** — requiring a branch to fire in **both** co-primary contexts makes a cycle-level
  conclusion **strictly harder** to reach than v2's single-primary rule. **That now applies to P2
  only** (§13.4 rule 2). The `p̂ ≥ 48 / 80 = 0.600` floor is a **necessary** condition in each context
  and not a sufficient one for the P2 cycle verdict. **This is a loss of power taken deliberately and
  disclosed in advance**, so that a `conditioning_sensitive` outcome on P2 is not later read as a
  failure of the experiment. It is the price of not privileging an already-observed context, and **no
  threshold was lowered anywhere to offset it**.
- **NEW in v2.2 — P1's power is not reduced by a cross-context conjunction, and this is a correction,
  not a concession.** The P1 cycle verdict fires on `LB(P1 | C_gen) > 0.5` alone, so the `p̂ ≥ 0.600`
  floor is necessary **and sufficient** for it, in `C_gen`, given branch 1's other conditions. v2.1
  had made P1 strictly harder by conjoining it with a quantity that is **not a search-error claim**
  (§13.4 rule 0); removing that is not a power optimisation but the removal of a category error.
  **`LB(P1) > 0.5` itself is not moved.** The cost is stated in §12.2 step 4: **P1 carries a
  single-context read with no internal cross-check**, and §19's replication gate is its only external
  one.

---

## 13. Supported / unsupported / undecidable — THE PRIMARY DECISION RULE

v1 §13 was withdrawn in full by v2. It framed the cycle as **one attribution** over mutually exclusive
alternatives (CRITICAL-3 SR, retracted by the supervisor in `hypotheses/C0002_selection.md`), and it
made "the family-clustered 95% **upper** bound of **P1** < 0.5" one of the two conditions for
concluding E2 — reading a **certified lower bound** in the direction where it carries no information
(CRITICAL-2 SR), in direct contradiction of v1 §8.7 three sections earlier. **That condition is
deleted and appears nowhere in v2 or v2.1.**

**v2.1 restructures §13 into three layers**, because 決定 1 makes both contexts co-primary:
**§13.2 evaluates the branches within each context**; **§13.3 states what is reachable**;
**§13.4 is the cycle-level rule across the two contexts**. **No branch condition, cutpoint or bar
changed. The branch table below is v2's, with a context column added and the `undecidable`
enumeration corrected for PC-GREEDY's demotion.**

### 13.1 What is reported, always

**Two independent certified lower bounds, side by side, in each of two co-primary contexts, with no
attribution:**

> **P1** lower-bounds the rate of systems on which a **search error is certified** on at least half of
> the system's usable cells.
> **P2** lower-bounds the rate of systems on which the truth is **certifiably not the model's argmax**
> on **every** usable cell.
> **Both may be high. Neither refutes the other's proposition.** C0002 cannot bound the search-error
> rate from above and makes no claim of the form "the failure is X, not Y".

**Four numbers with four intervals**: `P1(C_gen)`, `P1(C_raw)`, `P2(C_gen)`, `P2(C_raw)`, each with
its own `n_eval` and its own §12.1 interval. Each is reported with the language its context may carry
(§8.7): **Certificate-S language is permitted only on `C_gen`**; a `C_raw` P1 result licenses only
"the truth outscores all 50 candidates under a conditioning the search did not see", which is **not**
a search-error claim. Certificate N, and therefore P2's meaning, is identical in both.

Reported beside them, always: `n_eval` per context and the nominal 80; the per-system usable-cell
distribution per context; the `neither_cert` rate with its denominator per context; the realized value
of **every** §8.5 audit; S8's co-report (§8.5b); **S12's four-level length census with its realized
denominator and its prohibition restated (§8.5c)**; S11's in-support subgroup read; **PC-GREEDY's
realized rate in both contexts, labelled REPORT-ONLY (§10.2b)**; **`gt_is_quantized_in_context: true`
and, if Gate 4's reconstruction measured below `≥ 0.98`, `cgen_reconstruction_below_bar` with its
value, on every `C_gen` result**; and **the `pre_freeze_exposed` with/without descriptive sensitivity
on every `C_raw` endpoint (§0.3a)**.

**NEW in v2.2, required wherever a cycle-level P1 result is reported** (§13.4 rule 1b, §8.7): the
`C_raw` P1 value with its own `n_eval` and interval and its downgraded sentence; the point difference
`P1(C_gen) − P1(C_raw)`; the paired per-system `E3_system` cross-context agreement rate with its
denominator; and rule 5's reading of that difference. **Also required, in the cycle report's
limitations section**: the `L*` / out-of-set-competitor limitation in §8.7's frozen wording.

### 13.2 The branches — evaluated INDEPENDENTLY WITHIN EACH CO-PRIMARY CONTEXT

Let `LB_X(·)` denote the one-sided 95% lower bound under §12.1's interval of record, computed in
context `X ∈ {C_gen, C_raw}` on that context's `n_eval`. Every audit referenced below is the value
realized **in that same context**. The table is applied twice, once per context, yielding a
**per-context verdict**; §13.4 then produces the cycle verdict.

**How the two certificates reach the cycle level differs, and §13.4 rule 0 is why.** The **P1** cycle
verdict is the **`C_gen`** per-context verdict, with the `C_raw` value and the difference co-reported
(rule 1). The **P2** cycle verdict requires **both** contexts to fire the same branch (rule 2).
Rules 3–6 apply to both.

| per-context verdict | condition, evaluated in context `X` | what it licenses **in `C_gen`** | what it licenses **in `C_raw`** |
|---|---|---|---|
| **`H0001-R` refuted — certified search error prevalent** | `LB_X(P1) > 0.5` | **the cycle-level P1 verdict (§13.4 rule 1a).** A search error is **certified** on the majority of systems. **`H0003` (temperature / beam sweep) fires on evidence.** It does **not** license any statement about whether the truth is also non-argmax. If Gate 4's reconstruction measured below `≥ 0.98`, every sentence carries `cgen_reconstruction_below_bar` (§7.3.3) | **NOT a search-error claim, and `H0003` does NOT fire on it.** Licenses only, verbatim: "the truth outscores all 50 candidates under a conditioning the search did not see." The name of the branch is retained for one-to-one comparability across contexts; **the licensed sentence is the downgraded one** (§8.7). **NEW in v2.2: this limb NEVER produces a cycle-level P1 verdict.** It is reported, it licenses only the downgraded sentence, and by §13.4 rule 1d it does not fire `H0003` and does not make the cycle `conditioning_sensitive` by disagreeing with the `C_gen` limb |
| **`certified_non_argmax_prevalent`** *(the supported-E2-direction branch)* | `LB_X(P2) > 0.5` **AND** BA1 did not fire **AND** BA2 both **ran and passed** **AND** BA3 did not fire **AND** BA4 showed no context disagreement **AND** NC-CONDITION passed | the truth is certifiably not the model's argmax on the majority of systems, with all four known biases audited. **This branch is NOT reachable in C0002, in either context** — BA2 is predicted `length_control_not_measurable` at 0.4625 (§0.0 item 1, §8.5), and BA2 is corpus-level, so it blocks in both. It is written out in full anyway, because a branch that is unreachable must be visible as such rather than absent | as `C_gen`. **Unreachable** |
| **`E2_direction_observed_but_length_unaudited`** | `LB_X(P2) > 0.5` **AND** BA2 is `length_control_not_measurable` | **the strongest E2-direction outcome available in C0002.** The certificate fired; the length confound that D19-1331 identifies as central could not be audited on this corpus. **This is NOT a supported E2 and may not be cited as one, in any artifact, at any stage.** `S12` may **not** be offered to fill the gap (§8.5c) | identical. Certificate N holds in `C_raw` exactly as in `C_gen`, so this branch's meaning does **not** downgrade across contexts — **only the P1 / Certificate-S branch does** |
| **`E2_direction_observed_but_confounded`** | `LB_X(P2) > 0.5` **AND** BA2 ran and **failed** its disagreement bar, **or** BA1 fired in `X`, **or** BA3 fired in `X` | as above; **not a supported E2**. **Note (v2.1):** BA3 is expected to fire in `C_gen` and not in `C_raw`, because Gate 3b is met 80 / 80 in `C_raw` and rests on orbit members alone in `C_gen` (F-j, §7.2b). A BA3-driven difference between the contexts is therefore **anticipated and is an instrument fact, not a conditioning finding** — §13.4 requires it to be reported as such | identical |
| **`certificate_opportunity_insufficient`** | BA1 fired in `X` (median system-level `argmax_agreement_best` ≥ 0.95) | `lp_best ≈ L*`, so Certificate S was nearly unable to fire and **P1 carries no information**. The falsifier is **unevaluable**. Reported instead of P1 | identical |
| **`neither_certificate_prevalent`** | neither `LB_X(P1)` nor `LB_X(P2)` exceeds 0.5, and no instrument failure in `X` | a real, reportable result, explicitly distinct from `undecidable`. The deliverable is the per-system partition | identical |
| **`undecidable` in `X`** | **instrument failure in `X` only**, enumerated exhaustively: any **ABORT-class** Gate-4 condition failed (**PC-HOLDOUT, NC-HOLDOUT, the regression identity, PC/NC-H0010 for `H0010`**); **Gate 3a** failed in `X`; Gate 6's conjunction failed for `X`; the §11b ledger identity failed; or **> 10% of `X`'s cells are `unreliable_reencoding`** | — | — |

**`PC-GREEDY` is REMOVED from the `undecidable` enumeration** (決定 3, §10.2b). v2 listed it there as
an ABORT-class Gate-4 condition; it is now REPORT-ONLY and **no value of it makes anything
`undecidable`**. **Nothing else was added to or removed from that enumeration.**

**`wall_clock_guard_fired > 0` is NOT in the `undecidable` list for `H0001-R`.** v1 put it there; §11
scopes it to `H0010`, which is the only endpoint that consumes a CAS decision.

**`H0010`**: supported (joint absent) / supported (joint near-absent) / neither / refuted-in-the-joint
-direction / refuted-in-the-marginal-direction, per §9.3's graded rule; plus
`H0010_class_vs_multiplicity_conflict`, `H0010_undecidable_budget_limited`,
`H0010_undecidable_wall_clock_limited`, and `undecidable` if Gate 2 does not complete or the predicate
battery fails 12/12. **`H0010` is context-free** — it consumes no log-probability — so §13.4 does not
apply to it and it has exactly one verdict.

### 13.3 What is reachable, stated before compute

| outcome | reachable in C0002? | why |
|---|---|---|
| **`LB(P1 \| C_gen) > 0.5`** — the cycle-level P1 verdict | **YES, and decisive** | it refutes the E2-direction reading of the corpus with an interval and fires `H0003` on evidence for the first time. **This is the reason the cycle runs despite the E2 asymmetry.** **CORRECTED in v2.2**: v2.1 required this in *both* contexts, which required agreement with a quantity that is not a search-error claim (§13.4 rule 0). It now rests on `C_gen` alone, with the `C_raw` value and the difference co-reported |
| `LB(P1 \| C_raw) > 0.5` **on its own** | reachable as a **number**, but it **fires nothing** | it licenses only "the truth outscores all 50 candidates under a conditioning the search did not see", does not fire `H0003`, and does not produce a cycle-level verdict (§13.4 rule 1d). It is reported because withholding it would hide how far the conditioning moves the number, not because it adjudicates anything |
| `certified_non_argmax_prevalent` (**supported E2**) | **NO — unreachable, in either context** | BA2 is `length_control_not_measurable` at every admissible partner floor (0.4625 at 3, 0.4990 at 2; `k = 1` forbidden by §5.1), and BA2 blocks. §0.0 item 1, §8.5b item 3 |
| `E2_direction_observed_but_length_unaudited` | **YES — the strongest E2-direction outcome available** | and it is **not** a supported E2 |
| `neither_certificate_prevalent` | **YES** | plausible by construction (§12.4); the deliverable is then the per-system partition |
| `conditioning_sensitive` **on P2** | **YES** | and it is a finding, not a failure (§13.4 rule 2b). **In v2.2 this verdict no longer arises from a P1 cross-context difference** — for P1 a difference is reported and read under rule 5, not converted into a verdict |
| `conditioning_sensitive (one context undecidable)` | **YES**, for **both** certificates | rule 3, unchanged: an instrument failure in either context, on an instrument the two contexts share |

**The asymmetry is disclosed in advance and is the point of a preregistration.** C0002 can **refute**
the E2-direction reading decisively and can **support** it only in a qualified, explicitly-not-supported
form. This is a different situation from C0001's, where the realized denominator was unknown before
the run: here **what is reachable was known before freeze, and the cycle is run knowing it.**

### 13.4 The cycle-level rule across the two co-primary contexts

**Frozen. This is the only place a cycle-level verdict is formed.**
**REWRITTEN in v2.2** — v2.1's rule 2 required cross-context agreement of **both** certificates; the
supervisor sent that back for P1 on 2026-09-12. Rules 3, 4 and 5 are carried forward with their scope
made explicit. **No threshold changed.**

#### Rule 0 — what each certificate is indexed to (RE-GROUNDED in v2.3)

**v2.2's rule 0 is WITHDRAWN. It was grounded on "commensurability", and that ground was false and
symmetric.** The delta review established this and it is accepted in full
(`reviews/C0002_v2.2_delta_review.md` §2, MAJOR-1). The **conclusion** — rule 2 for P2, not for P1 —
is unchanged and correct; only its premise is replaced.

**What v2.2 said, and why it was wrong.** v2.2's P2 row read: `me_best` "certifies that the truth is
not the model's argmax **under the conditioning it was scored in**. That proposition is the same
proposition in both contexts; only the conditioning differs." **That is self-contradicting.** `C_gen`
and `C_raw` induce **different conditional distributions** over token sequences, and
"the truth is not the argmax of `P(· | x_scaled,permuted)`" and
"the truth is not the argmax of `P(· | x_raw)`" are **logically independent**: a model can rank the
truth first under one conditioning and not the other. **They are no more "the same proposition" than
the two P1 readings are**, so v2.2's P1 row ground — "two different quantities" — applied verbatim to
its own P2 row. Rule 0 as frozen in v2.2 therefore proved the same thing about both rows and **could
not support the asymmetry it asserted.**

**Why that mattered, and why it is a correction rather than a tidy-up.** Run consistently, v2.2's
rule 0 licensed either keeping rule 2 for P1 (so v2.2 removed a real control) **or dropping it for
P2**. The second is the live hazard: a later cycle could have argued **from this contract's own frozen
text** that P2's contexts are equally non-commensurable and dropped the cross-context requirement —
removing the last full conjunction protecting **the campaign's preferred direction**, which is exactly
the failure §12.2 step 6's direction check exists to prevent, re-entering through the premise instead
of through the rule. v2.2's language had already propagated to six places; all are corrected below and
listed in §27.2.

**The correct ground is the supervisor's own, from the 2026-09-12 追補
(`me_best` は探索の意味論を帯びておらず — Certificate N carries no search semantics), and it is not
about commensurability at all. It is about what each certificate is INDEXED TO.**

| certificate | what it is indexed to | may cross-context agreement be required of it? |
|---|---|---|
| **P1 — Certificate S** | **a historical decode event.** It asserts that **the decode that ran** failed to return the model's best sequence. **There was exactly one decode**, and it ran under the generation conditioning (F-g). | **NO.** A Certificate-S-shaped number computed under a conditioning **no decode ever used** is a statement about **a search that never happened**. It is not a second measurement of the same search; there is no second search. This is precisely what §13.2 branch 1 and §8.7 already encode, and requiring agreement with it would require the one real search-error certificate to agree with a statement about a counterfactual one |
| **P2 — Certificate N** | **a property of the model** — that the model does not rank the truth first. It is not indexed to any decode; **no decode need have happened at all** for it to be meaningful. | **YES.** Both conditionings are legitimate probes of the model's preference ordering and **neither is privileged**. A Certificate-N conclusion that holds under only one conditioning is therefore **conditioning-dependent**, and reporting it as a corpus-level finding would hide that. Requiring both is a **real robustness demand**, not a category error |

**What this ground does NOT assert.** It does **not** claim the two P2 readings are the same
proposition — they are not, and v2.3 says so above. It claims something weaker and true: that for a
claim about the model's preference ordering **neither conditioning has a prior claim to be the right
one**, so a conclusion surviving only one of them is conditioning-dependent. **Rule 2 survives on that
weaker and correct premise**, and the prohibition on reading `C_raw`'s P1 as confirming **or**
disconfirming `C_gen`'s survives too — more cleanly, because it no longer rests on a false claim about
propositional identity.

**The consequence the supervisor drew, and this contract adopts:** under v2.1's rule 2, a certified
search error in `C_gen` — the context the search actually ran in — would have vanished **merely
because it differed from a number that describes a search that never happened.**

#### Rule 1 — P1: the `C_gen` read stands on its own, with a mandatory co-report

**1a. The cycle-level P1 verdict is the `C_gen` verdict.** If `LB(P1 | C_gen) > 0.5` and §13.2's
branch-1 conditions hold in `C_gen`, the cycle verdict is **`H0001-R` refuted — certified search error
prevalent**, and **`H0003` fires on evidence**. It does **not** require, and may **not** be made
conditional on, any value of `LB(P1 | C_raw)`.

**NEW in v2.3 — that verdict is PROVISIONAL until §19 returns.** It fires the replication gate by
construction (§19.1), it carries `p1_replication_status` on every artifact, and **§13.6 states what
each replication outcome does to it** — including `failed replication`, which **withdraws** it. Until
the status leaves `pending`, no artifact, analysis, report or synthesis may present it as settled.

**1b. Three things must be reported beside it, and omitting any of them is a contract violation:**

1. **`LB(P1 | C_raw)`** with its own `n_eval` and interval, carrying its downgraded sentence verbatim
   and the statement that it is **not** a search-error claim (§8.7);
2. **the difference** `P1(C_gen) − P1(C_raw)`, as a point difference of the two system rates, **and**
   the paired per-system agreement rate of `E3_system` across contexts with its denominator (BA4, S1);
3. **the reading of that difference**, per rule 5 — whether any part of it is traceable to a known
   instrument asymmetry rather than to the conditioning.

**NEW in v2.3 (delta review MINOR-2) — the co-report under a failed NC-CONDITION.** Item 3 requires a
**reading** of the cross-context comparison, and if NC-CONDITION failed, §10 has already declared that
comparison **`uninterpretable`**. The co-report may not then silently supply a reading of something
the contract says cannot be read. **Frozen: when NC-CONDITION has failed, the P1 co-report carries
`ba4_uninterpretable: true`, item 3 is satisfied by recording that fact and nothing else, and no
interpretation of the difference may be offered.** Items 1 and 2 — the value and the difference — are
still reported; only their *reading* is suspended. This changes nothing about the cycle-level P1
verdict, which by rule 4 does not rest on the comparison.

**1c. What the co-reported value may NOT do.** It may not confirm, corroborate, validate, check,
disconfirm, undermine, or cast doubt on the `C_gen` P1. Two independent reasons, both binding
(§7.3.2 condition 4): the contexts are **not independent** (shared model, truths and candidate set),
**and** — the stronger reason for P1 — **the `C_raw` value is not a claim about the decode that
produced the candidate set** (rule 0). There was one decode; a number describing a search that never
happened neither confirms nor disconfirms a statement about the search that did. §8.7 forbids both
readings by name.

**1d. `LB(P1 | C_raw) > 0.5` on its own fires nothing.** It is reported, it licenses only the
downgraded sentence, and it does **not** fire `H0003`, does **not** produce a cycle-level verdict, and
does **not** make the cycle `conditioning_sensitive` by disagreeing.

**1e. BA1's scope under rule 1.** BA1 firing **in `C_gen`** makes the cycle-level P1 read
`certificate_opportunity_insufficient` and the falsifier **unevaluable** — unchanged, and it still
bites, because P1's cycle read lives in `C_gen`. BA1 firing **in `C_raw` only** does not touch the
cycle-level P1; it is reported and attaches to the co-reported `C_raw` value.

#### Rule 2 — P2: the cross-context conjunction, RETAINED IN FULL

**2a.** If **both** contexts fire the same §13.2 P2-branch, that branch is the cycle-level P2 verdict,
**with each context's own licensed language attached**. **Agreement licenses nothing beyond the
per-context verdicts themselves** (§7.3.2 condition 4, rule 6 below).

**2b.** If the two contexts fire **different** P2-branches at the decision level, the cycle-level P2
verdict is **`conditioning_sensitive`** and **nothing is concluded about the non-argmax certificate**.
Both per-context reads are still reported in full, with their intervals and their audits — **the
disagreement is the finding**, and it bears directly on the question this cycle asks about the
generator: whether the non-argmax reading depends on the conditioning the model is given.

**2c. Unchanged from v2.1 in every particular.** `LB(P2 | ·) > 0.5` is not moved; BA1, BA2, BA3, BA4
and NC-CONDITION remain conjuncts of `certified_non_argmax_prevalent`; and that branch remains
**unreachable** in C0002 because BA2 is `length_control_not_measurable` in both contexts.
**P2 is the campaign's preferred direction, and it keeps the full conjunction.**

#### Rule 3 — one context `undecidable`: UNCHANGED, and it applies to P1 as well as P2

**If either context is `undecidable`** (§13.2's instrument-failure enumeration), the cycle verdict is
**`conditioning_sensitive (one context undecidable)`** for **both** certificates, and the surviving
read **may not** be promoted to a cycle-level conclusion on its own.

**Why this is NOT relaxed for P1, when rule 2 was.** The two rules rest on different grounds, and only
rule 2's ground was defective. Rule 2 asked whether **cross-context agreement is a meaningful demand**
for a given certificate — a question about **what that certificate is indexed to** (rule 0), and for
Certificate S it is not, because there was one decode. **Rule 3 is an instrument-failure question, and
what a certificate is indexed to has nothing to do with it.** An `undecidable` in either context means a control,
a gate or the ledger failed on an instrument the two contexts **share** — one model, one scorer, one
candidate set, one resume ledger. And rule 1b's mandatory co-report **cannot be produced** if the
`C_raw` read does not exist. So `C_gen`'s P1 does not stand alone here, and the qualifier
`(one context undecidable)` — not the word `conditioning` — is the operative half of the verdict name.
**The name is carried over from v2.1 unchanged rather than renamed, to avoid churn in a frozen verdict
label.**

#### Rule 4 — NC-CONDITION failed: scoped, and deliberately NOT extended to P1

**If NC-CONDITION failed**, BA4 is `uninterpretable` and the **P2** cycle-level verdict is
**`conditioning_sensitive`** regardless of whether the P2 branches agree. Unchanged from v2.1 and from
v2's BA4 consequence.

**It does not touch the cycle-level P1 read**, and §10's own frozen text already scopes it that way:
NC-CONDITION's DOWNGRADE consequence is that BA4 **"blocks any conclusion resting on context
agreement."** Under rule 1, P1's cycle read **does not rest on context agreement**, so there is
nothing for the block to attach to.

**Why extending it to P1 anyway would be an error, not extra caution.** NC-CONDITION is a per-cell
binary over 40 cells at a bar of `≥ 0.95`, whose population rate measures **exactly** 0.95 (M4), with
`P(pass | 40, p = 0.95) = 0.6767`. A failure is therefore **substantially likely even when the scorer
is behaving exactly as measured** — the median `|Δ|` is **13.08** nats with **0** exact zeros, which
establishes that the instrument *does* respond to conditioning. Reading a failed per-cell binary as
evidence that `C_gen`'s conditioning is inert, and using that to withdraw a within-context arithmetic
certificate, would be treating a non-significant control as evidence of equivalence — **rule 01
item 8**, in the one place this contract would be most tempted to commit it. The failure **is**
reported, and it attaches to every cross-context statement.

#### Rule 5 — anticipated-difference disclosure: REQUIRED, and now it applies to rule 1b too

Where a cross-context difference is traceable to a **known instrument asymmetry** rather than to the
conditioning, the report **must** say so explicitly and **must not** present the difference as
evidence that the certificate rate depends on the conditioning. The two known asymmetries:

- **BA3 / Gate 3b** — met **80 / 80** in `C_raw`, resting on unverified orbit members in `C_gen`
  (F-j, §7.2b);
- **the Gate-4 reconstruction shortfall** — a `C_gen`-only quantization effect (F-k, §7.3.3).

**This applies in two places now.** (i) To rule 2b, where a P2 disagreement produces
`conditioning_sensitive` and the reader must know whether the source is an artefact. (ii) **NEW in
v2.2** — to rule 1b's mandatory P1 difference report, where the disclosure prevents a reader inferring
conditioning-dependence from an instrument artefact **in a difference that adjudicates nothing in the
first place**. Disagreement is informative only where its source is not already known to be an
instrument artefact.

#### Rule 6 — agreement is never confirmation, for either certificate

The frozen sentence of §7.3.2 condition 4 is **required** wherever the two contexts agree, on either
certificate. §1.4 item 9 forbids reading agreement as confirmation, corroboration, replication or
robustness evidence. **For P1, §7.3.2's second reason additionally applies**: the `C_raw` value is not a claim about the
decode that produced the candidate set (rule 0), so neither agreement nor disagreement between them
adjudicates anything.

#### Summary table — which rule governs which certificate

| situation | P1 (Certificate S) | P2 (Certificate N) |
|---|---|---|
| both contexts fire the same branch | `C_gen` verdict stands; `C_raw` value + difference co-reported; **agreement is not confirmation** | that branch is the cycle verdict; **agreement is not confirmation** |
| contexts fire different branches | **`C_gen` verdict stands** (rule 1a); the difference is reported and read under rule 5; **NOT `conditioning_sensitive`** | **`conditioning_sensitive`**; nothing concluded (rule 2b) |
| one context `undecidable` | **`conditioning_sensitive (one context undecidable)`** (rule 3) | **`conditioning_sensitive (one context undecidable)`** (rule 3) |
| NC-CONDITION failed | cycle-level P1 **unaffected**; the failure is reported and attaches to every cross-context statement (rule 4) | **`conditioning_sensitive`** (rule 4) |
| BA1 fired in `C_gen` | `certificate_opportunity_insufficient`; falsifier unevaluable (rule 1e) | contributes to blocking a supported E2 (§8.5) |

### 13.5 Every branch is informative — restated honestly

- **`LB(P1 | C_gen) > 0.5` fires `H0003` on evidence for the first time.** The `C_raw` read
  contributes the downgraded sentence and the co-reported difference only, and adjudicates nothing
  (§13.4 rule 1). *(v2.1 said "in both contexts"; corrected in v2.2 — see §26.)*
- `E2_direction_observed_but_length_unaudited` — the outcome §0.0 predicts — is **still informative**:
  it establishes the certificate rate, it establishes that the length confound is **structurally
  unauditable on this corpus** (`S12`: 0.6302 of cells have a truth longer than every candidate), and
  it makes the design of a corpus that *can* audit it the content of C0003. What it does **not** do is
  close `H0003`, and v1's claim that an E2 result would close `H0003` "permanently" is withdrawn.
- `conditioning_sensitive` is a **result**, not a failure: it says the certificate rate is not stable
  across the two conditionings of one instrument, which constrains every downstream reading of
  teacher-forced scores on this checkpoint.
- `neither_certificate_prevalent` is reported as such.
- **`S12` is reported in every case**, at all four levels, with its prohibition restated (§8.5c).
- A cycle report is written regardless (`.claude/rules/08-cycle-persistence.md`).

---

### 13.6 Post-replication disposition of a fired P1 (NEW in v2.3)

**Frozen. This is the only place the consequence of a §19 outcome on the P1 verdict is stated.**
v2.2 declared §19 to be P1's only cross-check and then gave **no outcome of it any effect** on the
verdict it exists to police (delta review CRITICAL, third limb). A rule-2 conjunction would have
**prevented** a verdict from forming; §19 only asks that a formed verdict be revisited — so §19 is
worth nothing unless the revisiting has a stated consequence. It does now.

**The cycle-level P1 verdict is PROVISIONAL until the §19 confirmation returns.** `p1_replication_status`
is mandatory on every artifact carrying it (§16.2, §19.4).

| §19 outcome | criterion | **frozen disposition of the fired P1 cycle verdict** |
|---|---|---|
| **`replicated`** | the independently derived quantity also gives **`LB(P1) > 0.5`** under §12.1's unchanged interval of record | the verdict **STANDS**, reported with its replication reference. `H0003` fires **on evidence** |
| **`directionally replicated`** | the point rate is in the same direction but its own **`LB(P1)` does not exceed 0.5** | the verdict is **DOWNGRADED to `certified_search_error_prevalent_unreplicated`**. It remains reportable as a certificate rate with **both** intervals shown, but **`H0003` fires as `exploratory`, not on evidence**, and the result **may not be cited as a refutation of the E2-direction reading** |
| **`failed replication`** | the independently derived quantity **contradicts** the original — the certificate does not fire on a majority of systems, or the two derivations disagree on `1[lp_gt_max > lp_best]` for a material number of systems | the verdict is **WITHDRAWN** and the cycle's P1 read becomes **`undecidable (independent derivation disagrees)`**. **`H0003` does not fire.** The disagreement is an **instrument** finding and is reported as one: two implementations of the same frozen contract do not agree about the primary quantity, which is a stronger and more useful result than either number. The original value is **retained, not deleted** (rule 01 items 4–5) |
| **`inconclusive`** | the confirmation could not be completed, or its own instrument failed its checks | the verdict stays **PROVISIONAL** and is reported as **`certified_search_error_prevalent_replication_inconclusive`**. `H0003` fires as `exploratory` only, and **the cycle report must state that the check this contract declared load-bearing did not return** |
| **not run** | — | **contract violation** (§19, §24). The verdict may not be reported as settled, and `p1_replication_status` stays `pending` |

**Why `failed replication` withdraws rather than downgrades.** P1 is a **certified** lower bound, and
a certificate is an arithmetic claim about two numbers. If an independent derivation of those numbers
does not reproduce the inequality, what is in doubt is not the *strength* of the evidence but
**whether the inequality holds at all**. Downgrading would report a certificate whose arithmetic is
contested as though it were merely weaker. `undecidable` is the honest label, and C0001's verdict of
record is the precedent for using it.

**No threshold is introduced by this table.** `LB(P1) > 0.5` is §13.2's frozen cutpoint, applied
unchanged to the confirmation. "A material number of systems" in the `failed replication` row is
**deliberately not given a numeric bar**, because setting one before the two derivations exist would
be inventing a threshold; instead the row is reached whenever the confirmation's own
`LB(P1) > 0.5` fails **and** the per-system disagreement set is non-empty, both of which are
determined by quantities already frozen. **The replication specialist may not set a new bar either.**

**This table applies to P1 only.** A fired P2 is unreachable in C0002 (§13.3), and `H0010`'s
replication disposition is unchanged.

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
| PC-GREEDY, 40 cells × **2 contexts** (REPORT-ONLY, §10.2b) | **0.06** | — | — |
| smoke, 24 cells × 2 contexts | 0.02 | — | — |
| re-encoding / tokenization, 47,987 × 2 | — | 1.9 | — |
| **`H0010` parse + `count_ops` (MEASURED, M2)** | — | **0.04** | — |
| `H0010` predicate census (`together`/`cancel`/`fraction`) | — | ≤ 8, **gated by Gate 2a** | — |
| controls, audits, records | 0.01 | ≤ 2 | — |
| **total** | **≈ 0.64** | **≈ 12** | **see below** |
| **ceiling** | **4.0** | **24** | **15 GiB** |
| **margin** | **≈ 6.3×** | **≈ 2×** | — |

**Co-primacy costs no new compute (v2.1).** v2 already budgeted the 960-cell pass over **both**
contexts (0.47 GPU-h), because BA4 required the non-primary context to be computed anyway. 決定 1
renames what was already being computed; the only increment in v2.1 is **+0.03 GPU-h** for running
PC-GREEDY in the second context as a REPORT-ONLY quantity, which also supplies the `C_gen` figure that
§0.4 forbade measuring before freeze. **No ceiling is raised** (rule 06).

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
| **`pre_freeze_exposed` cells (§0.3a)** | **exactly 8 of 960**, known and listed | **NOT an exclusion.** Retained in numerator and denominator; flagged on every `C_raw` artifact; the with/without read is reported as a **descriptive** sensitivity and neither read may be selected after the fact |
| **PC-GREEDY realized rate** | **unknown in `C_gen`** (`unverified_for_C_gen`); **2 / 10 probe in `C_raw`** | **REPORT-ONLY.** Counted and reported per context; **no value of it excludes, aborts, downgrades or blocks anything** (§10.2b) |
| **`cgen_reconstruction_below_bar`** | **expected TRUE** — measured 0.9683 against `≥ 0.98` (M5) | flag carried on every `C_gen` artifact; affected candidates already excluded by §2.1b's usable-candidate definition and counted as `CandidateReencodingMismatch` under §8.2's existing cascade |

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
`cas_outcome`, `n_eval`, `prior_information_disclosed: "C0002_preregistration_v2.1.md §0"`.

**Added in v2.1, all written unconditionally so an omission is machine-detectable:**

| field | on which records | value |
|---|---|---|
| **`pre_freeze_exposed`** | **every** record, `C_gen` and `C_raw` | `true` on exactly the 8 `cell_id`s of §0.3 in `C_raw`; `false` elsewhere. Never omitted (§0.3a) |
| **`context_role`** | every record | `"co_primary"` for both contexts. **There is no `"primary"` or `"secondary"` value in this contract** |
| **`certificate_language_permitted`** | every record | `"certificate_S_and_N"` in `C_gen`; **`"certificate_N_only"` in `C_raw`** (§7.3.2 condition 1, §8.7) |
| **`cgen_reconstruction_below_bar`** | every `C_gen` record | boolean, with the realized rate in `cgen_reconstruction_rate` (§7.3.3) |
| **`gt_longer_than_every_candidate`** | every cell record | the per-cell `S12` indicator (§8.5c), with `pre_measured_before_freeze: true` on the `S12` summary |
| **`pc_greedy_is_gating: false`** | PC-GREEDY records | frozen constant, so the demotion is visible in the artifact and not only in this document (§10.2b) |
| **`contexts_are_not_independent: true`** | every endpoint and audit record | frozen constant, carrying the §7.3.2 condition 4 reading into the artifacts (§1.4 item 9) |

**Added in v2.2**, so §13.4's split is machine-checkable and not only prose:

| field | on which records | value |
|---|---|---|
| **`p1_cycle_read_is_single_context: true`** | every P1 endpoint record | frozen constant. The cycle-level P1 verdict is the `C_gen` verdict (§13.4 rule 1a) |
| **`p1_cross_context_comparison_is_descriptive: true`** | every BA4 / S1 record touching P1 | frozen constant. The P1 cross-context difference is **reported and does not gate**; the P2 comparison **does** gate and carries `p2_cross_context_comparison_is_gating: true` |
| **`p1_cycle_context`** | every P1 endpoint record | `"C_gen"`, frozen. Never `"C_raw"`, under any gate outcome |
| **`p1_co_report_present`** | every cycle-level P1 endpoint record | boolean, asserted **true** at Gate 6: the four items of §13.4 rule 1b are present. A false value is a contract violation, not a missing-data condition |

**Added in v2.3**, so §19's repair and §13.6's dispositions are machine-checkable rather than prose:

| field | on which records | value |
|---|---|---|
| **`p1_replication_status`** | every artifact carrying a fired cycle-level P1 verdict | `pending` / `replicated` / `directionally_replicated` / `failed` / `inconclusive` (§13.6). **Written from the moment the verdict is formed**; while it is `pending` the verdict may not be presented as settled |
| **`p1_verdict_is_provisional`** | same | boolean, `true` iff `p1_replication_status == "pending"` (§13.4 rule 1a) |
| **`p1_replication_factor`** | every §19 confirmation record for a fired P1 | one of `independent_scorer` / `independent_cgen_forward_map`. **The values `control_cell_seed`, `fresh_process_path` and `other_scoring_context` are NOT admissible here** and a confirmation recording one of them does not discharge the gate (§19.3) |
| **`ba4_uninterpretable`** | the P1 co-report, when NC-CONDITION has failed | `true`. Rule 1b item 3 is then satisfied by recording this and nothing else; **no interpretation of the cross-context difference may be offered** (§13.4 rule 1b) |

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
  - **RD1** single context, **AMENDED in v2.1**: with both contexts co-primary there is no "primary
    only" to fall back to, so RD1 must **name the retained context in advance**. **Frozen: RD1 retains
    `C_gen`** — the context in which the search actually ran and the only one that may carry
    Certificate-S language (§7.3.2 condition 1) — and reports `C_raw` as `not_measurable`.
    **RE-GROUNDED in v2.3 (delta review MAJOR-4)**: v2.2 said "§13.4's cross-context conjunction
    cannot be evaluated", **but after v2.2 there is no cross-context conjunction for P1**, so that
    citation was to a rule that no longer exists and rule 1a would otherwise form a P1 verdict from
    `C_gen` alone. **The outcome v2.2 stated is nevertheless correct, on rule 3's ground.** RD1 is not
    rule 3's *instrument-failure* trigger — dropping a context under RD1 is a planned reduction, not a
    failure — but it produces rule 3's **operative condition**: no `C_raw` read exists, so
    **rule 1b's mandatory co-report cannot be produced**, and rule 3 forbids a surviving read from
    being promoted to a cycle-level conclusion alone. **Stated explicitly, as the review required:
    under RD1 NO cycle-level verdict forms, for EITHER certificate.** The `C_gen` read is reported as
    a **per-context** result only; BA4 is `not_measurable`; P2's rule-2 conjunction cannot be
    evaluated; and **a supported E2 is blocked** under RD1 as it is everywhere else. **RD1 is not expected to be invoked**: §14
    projects 0.64 GPU-h against a 4.0 GPU-h ceiling, so cost is not a reason to drop a context.
  - **RD2** the 24-system fixed GRN validation panel instead of 80 systems, with P1/P2 reported
    `exploratory` and concluding nothing. **Note (m-1 SR)**: §12.1's interval has no degenerate special
    case, so it survives RD2's unequal strata without the arithmetic accident v1's substitute relied on.
  - **RD3** `H0010` census restricted to the realized classes without multiplicity weighting.
    **AMENDED: H4 may NOT be dropped** (MAJOR-6 SR) — it is the only quantity that can contradict the
    class-level verdict. RD3 instead restricts the multiplicity weighting to the realized classes.
- **The "named contingency" of v2 is REMOVED (v2.1, 決定 1).** v2's contingency was "if the `C_gen`
  reconstruction fails Gate 4, `C_raw` becomes primary". **There is no fallback between the contexts,
  in either direction, under any gate outcome** (§7.3.1). Gate 4's `≥ 0.98` stands unmoved and now
  carries the single DOWNGRADE disposition of §7.3.3, scoped to `C_gen`.
  **The downgraded sentence survives the removal of the fallback and is now permanent rather than
  contingent**: `C_raw` results carry "the truth outscores all 50 candidates under a conditioning the
  search did not see" **always**, not only when a fallback fires (§8.7).
  **And §0.3's containment is not "collapsed by a contingency" — it is withdrawn outright** (§0.3
  item 2), because a co-primary endpoint's proxy was observed before freeze. That is disclosed as
  prior information in §0 and marked per cell by §0.3a, and the cycle report must carry it as a
  validity threat, not absorb it silently.

---

## 19. Replication gate (rule 07) — REWRITTEN in v2.3

**Why this section was rewritten.** v2.2 made §19 **P1's only cross-check** and then left it unable to
carry that load. The delta review found three defects, all accepted
(`reviews/C0002_v2.2_delta_review.md` §1, CRITICAL): its factor menu contained an option §19 itself
declares invalid; two of the remaining three **cannot perturb P1's value at all**; and **no outcome of
the gate had any stated consequence** for the verdict it exists to police. **A gate with no stated
consequence is not a gate**, and a declared protection that is not delivered is worse than declaring
none. All three are repaired here. **No threshold is moved, and nothing is recomputed.**

### 19.1 When the gate fires

Fires on any of: **either certified lower bound reported as prevalent**; `H0010` supported in either
band; any result an independent reviewer marks fragile; or any result resting on a single seed or a
single context. **`conditioning_sensitive` additionally fires it**, and so does a cycle verdict that
rests on agreement between the two contexts, precisely because that agreement is not independent
support (§7.3.2 condition 4).
*(v1's trigger said "an E2 or E3 corpus attribution"; after §13 the word "attribution" is gone and the
trigger is restated on the certificate rates — m-5 SR.)*

**A fired cycle-level P1 is inside the trigger by construction, not by interpretation**: §13.2's
branch name is "`H0001-R` refuted — **certified search error prevalent**". It is reinforced in §12.2
step 4, §24 and §19.4 below.

### 19.2 The general menu of admissible independent factors

The minimum replication changes **at least one independent factor**: a fresh process and artifact
path; a different `CONTROL_CELL_SEED`; or an independent re-derivation of `lp_best` from a separately
written scorer.

**"The other scoring context" is DELETED from this menu (v2.3).** It was an orphan carried from v1 /
v2.1: §19.5 below — and §12.2 step 4 and §21 item 11, which already omitted it — declare it satisfies
**none** of the factors. A menu containing an option the same section declares invalid is a defect,
not a choice.

### 19.3 For a FIRED P1 the general menu does NOT apply — the factor is named

**Frozen. The "at least one of" rule is suspended for a fired cycle-level P1.** The replication
**must** change a factor that can actually perturb P1's value, and exactly two qualify:

| admissible factor for a fired P1 | why it qualifies |
|---|---|
| **an independently written scorer** — an independent re-derivation of `lp_best` **and** `lp_gt_max` under `C_gen`, written against the contract rather than against the C0002 implementation, by an agent that did not write the C0002 scorer | it recomputes **both sides of the certificate** `1[lp_gt_max > lp_best]` from the model, so a disagreement is a real disagreement about the quantity |
| **an independently written `C_gen` forward-map reconstruction** — an independent implementation of §7.1's scaler, permutation and closed-form forward map, feeding the existing scorer | `C_gen`'s conditioning is where F-g, F-j and F-k all bite, and it is the step whose correctness the whole Certificate-S reading depends on |

**Named as INSUFFICIENT for a fired P1, with the reason** — so that a replication cannot formally
discharge the gate while checking nothing:

| factor | why it is insufficient **for P1** |
|---|---|
| **a different `CONTROL_CELL_SEED`** | §10's control-cell set is **40 cells** drawn with that seed, and NC-CONDITION's per-cell partner. **P1 is computed over all 80 systems / 960 cells** (§22). Changing this seed re-runs the **controls** and leaves **P1 bit-identical.** It is a valid factor for a control-battery replication and for `H0010`; it is inert against P1 |
| **a fresh process and artifact path** | the scoring pass is **teacher-forced, fp32, over stored candidates, with no sampling**. A fresh process reproduces the number up to GPU-kernel float nondeterminism. That is a **reproducibility** check, not a check of the quantity's **validity** — and §12.2 step 4's claim is about validity |
| **the other scoring context** | deleted from the menu (§19.2), and for P1 barred twice over: it shares the model, the truths and the candidate set, **and** by rule 0 it is not indexed to the decode that ran |

**A replication of a fired P1 that changes only an insufficient factor does not discharge this gate**,
and reporting it as having done so is a contract violation. Both admissible factors may be run; at
least one must be.

### 19.4 Preregistered consequence of each outcome — the P1 cycle verdict is PROVISIONAL until §19 returns

**Frozen, and this is the half v2.2 was missing entirely.** A fired cycle-level P1 verdict is
**provisional** from the moment it is formed until the §19 confirmation returns. Every artifact
carrying it also carries **`p1_replication_status ∈ {pending, replicated, directionally_replicated,
failed, inconclusive}`**, and **no artifact, analysis, report or synthesis may present a fired P1 as a
settled result while the status is `pending`.** The dispositions are §13.6's table, and they are
stated there so there is exactly one contract text per outcome for R7 to quote.

**The confirmation's own criterion reuses the frozen cutpoint and introduces no new one**: the
confirmation is evaluated by applying **`LB(P1) > 0.5` under §12.1's interval of record**, unchanged,
to the independently derived quantity. **No threshold is moved to define replication success.**

The confirmation is recorded separately under `GPU_RUNclaude1/replications/` with one of
`replicated` / `directionally replicated` / `failed replication` / `inconclusive`.

### 19.5 The second context is NOT a replication

`C_gen` and `C_raw` share the model, the ground truths and the candidate set, so computing both
satisfies **none** of §19.2's factors. **For P1 there is a second and independent reason**: by rule 0
the `C_raw` value is **not a claim about the decode that produced the candidate set**, so it could not
be a replication of a search-error certificate even if the inputs were independent.
**C0002 contains no internal replication of its primary endpoint** (§21 item 11).

**A C0002 certificate rate may not invalidate a GPU_RUN5 result on its own.**

---

## 20. Required reviews before the full experiment

v1 was reviewed by `lansr-statistical-reviewer` and `lansr-reproducibility-auditor`, independently of
the author and of each other. **This document is the response to those reviews and has not itself been
reviewed.** It must not be described as reviewed.

**v2.1 has likewise not been reviewed.** It is the implementation of the supervisor's three decisions
in the contract text, and it must not be described as reviewed.

The supervisor's check before freezing **v2.1** should confirm, at minimum:

1. that the **three decisions** of `plans/C0002_supervisor_decisions.md` are faithfully reflected —
   決定 1 in §0.0 item 4, §0.3, §0.3a, §7.1, §7.3, §8.4, §8.5 BA4, §8.7, §12.1, §12.2, §13;
   決定 2 in §0.0 item 1, §8.5 BA2, §8.5c, §13.2, §13.3; 決定 3 in §0.0 item 5, §10, §10.2b,
   §11 Gate 4, §11 Gate 6, §13.2;
2. that **no threshold was moved** — §0.9's table, and §25's clause-by-clause record;
3. that removing the fallback **orphaned nothing** — §25.2 enumerates every place v2 referred to it
   and how each was resolved;
4. that §23's v2 disposition is carried forward accurately and that §25 records every deviation from
   it;
5. the items v2's check already required and that v2.1 does not disturb: that a supported E2 is
   unavailable, that the cycle reports two bounds rather than one attribution, and the §8.5b
   adjudication.

**Added for v2.2**, since the supervisor has already discharged items 1–4 for v2.1:

6. that **§13.4 rule 2 is now scoped to P2** and that P1's cycle read is the `C_gen` read with a
   **mandatory** co-report — §13.4 rules 0, 1 and the summary table;
7. that **rule 3 still applies to P1**, and that rule 4 is scoped to P2 **with the stated reason**
   (§13.4 rule 4) rather than by omission;
8. that the **§12.2 re-derivation** is honest about P1 carrying a **single-context read with no
   internal cross-check**, and that §19 is named as its only external one;
9. that the relaxation runs **only on the refuting branch** — §12.2 step 6 — and that P2 keeps the
   full conjunction;
10. that **no threshold moved in v2.2** — §26.4.

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
8. **NEW in v2 — "A distinct `e1`/`e2` pair in `C_gen`."** *(v2 said "in the primary context"; with
   both contexts co-primary the item names the context directly.)* Not achievable in `C_gen` (F-j):
   scoring the stored `tree_encoded` there requires decode → scale → re-encode, which is `e2`'s own
   path, and the two coincide on 120 / 120 cells. Gate 3b in `C_gen` rests on orbit members alone and
   its achievability there is **`unverified`**; 3b is therefore a downgrade condition only (§7.2b).
9. **NEW in v2 — "PC-GREEDY's achievability in `C_gen`, before freeze." AMENDED in v2.1.** Still not
   measurable without violating §0.4, since it requires `lp_best` under `C_gen`. v2 disclosed a live
   abort risk instead (`P(X ≥ 2 | n = 40)` = 0.6009 at a true rate of 0.05, MAJOR-13 SR). **v2.1 does
   not carry that risk: the control is demoted to REPORT-ONLY** (決定 3, §10.2b), so the unverified
   expected value no longer sits on a gate. **What remains unimplementable is the demonstration
   itself** — C0002 cannot establish before or during the run that a sequence **outside** the stored
   candidate set can outscore `lp_best` in `C_gen`. That demonstration is now a **reported quantity**,
   and the gap it leaves is named in §10.2b rather than papered over.
10. **NEW in v2 — "An interval of record that is both correct for the estimand and informative at this
    sample size."** §12.1's interval is correct for §2.2's estimand and covers at 0.942–0.968, but it
    cannot fire a branch below `p̂ = 0.600` (§12.4). That is a real loss of power relative to v1's
    estimator, and it is the price of correctness, **not** a defect to be optimized away.
11. **NEW in v2.1 — "An independent second read of the primary endpoint, inside this cycle."** Not
    achievable. The two co-primary contexts share the model, the ground truths and the candidate set;
    they are two conditionings of one instrument. **Their agreement is therefore not confirmation**
    (§7.3.2 condition 4), and C0002 contains **no internal replication** of P1 or P2. §19's gate is
    the mechanism that supplies one, and it requires a genuinely independent factor — a fresh process
    and artifact path, a different `CONTROL_CELL_SEED`, or an independently written scorer.
    **Recording this is the whole point of 決定 1's condition 4**: the cheapest way to overstate this
    cycle would be to count the second context as a second experiment.
12. **NEW in v2.1 — "A cycle-level verdict from a single context." REWRITTEN in v2.3; the v2.1 form
    is WITHDRAWN as false.** v2.1 and v2.2 both carried: *"Not available by construction. §13.4
    requires the two contexts to agree before any cycle-level branch fires."* **Under §13.4 rule 1a
    the cycle-level P1 verdict IS a verdict from a single context**, so that sentence stated the
    superseded rule as frozen fact (delta review MAJOR-3). It is withdrawn, not edited away — and
    §26.3's certification that §21 needed no edit was **wrong**, which §27.4 records.

    **What is actually unimplementable, restated:** a cycle-level **P2** verdict from a single
    context is not available by construction (rule 2), and a cycle-level verdict of **either** kind is
    not available when one context is `undecidable` or not computed (rule 3, §18 RD1). That remains a
    deliberate loss of power (§12.4).

    **What survives of the original clause, and it survives on the facts:** an **already-observed**
    context can never carry a conclusion alone. The single context P1's verdict lives in is
    **`C_gen`** — the context that was **not** observed before freeze — while `C_raw`, the context in
    which the 8-cell `sb_best` exposure occurred (§0.3), **cannot carry a P1 cycle verdict at all**
    (rule 1d). The protection is real; v2.1's stated reason for it was not.

---

## 22. Compact statement of what is frozen

Primary `H0001-R` as **two independent certified lower bounds**, not an attribution; the rewritten
falsifier; **P1** `certified_search_error_system_rate` and **P2** `certified_non_argmax_system_rate`
over **all 80** systems, denominator `n_eval`, **computed and reported in EACH of two CO-PRIMARY
scoring contexts `C_gen` and `C_raw`, with NO fallback between them in either direction under any gate
outcome**; **Certificate-S language restricted to `C_gen`**, with `C_raw` carrying the frozen
downgraded sentence "the truth outscores all 50 candidates under a conditioning the search did not
see", which is not a search-error claim; **the frozen prohibition on reading agreement between the
contexts as confirmation, corroboration, replication or robustness evidence**, they being two
conditionings of one instrument; **`gt_is_quantized_in_context: true` on every `C_gen` artifact and
the statement that the truth scored in `C_gen` is a 4-significant-digit approximation of the truth**;
**the §0.3a `pre_freeze_exposed: true` marking rule over exactly the 8 disclosed cells, which are
flagged and retained, never excluded**; the `0.5` system cutpoint and
`E3_system(s) = 1[sb_rate(s) ≥ 0.5]` **inherited verbatim from v2.1 §8.3 (2026-09-09)**, with
`E2_system(s) = 1[me_rate(s) = 1]` re-expressed on the quantity that certifies it and **strictly harder
to satisfy** than v1's form; **`sb_best` on `lp_gt_max` and `me_best` on `lp_gt_lse`**, with
`neither_cert` counted and reported; `lp_best` = max over usable candidates; the usable-candidate /
usable-cell / evaluable-system definitions and the ≥ 8-of-12 + all-four-corruption-settings floor;
**Gate 3 split into 3a ABORT / 3b DOWNGRADE / 3c REPORT-ONLY, evaluated per context**, with Gate 6
consulting 3a only; the control battery **PC-HOLDOUT ≥ 0.95, NC-HOLDOUT ≤ 0.05, NC-CONDITION ≥ 0.95
with a different-system partner, PC/NC-H0010 12/12, regression identity < 1e-5, `C_gen` reconstruction
≥ 0.98 as a tokenizer round trip, PC-GREEDY ≥ 2/40**, each with **exactly one** disposition, all
evaluated before the expensive pass — **with PC-GREEDY REPORT-ONLY and gating nothing**, and the
**`C_gen` reconstruction DOWNGRADE-class scoped to `C_gen`**; the four bias audits **with BA1, BA2 and
BA3 blocking** and **BA4 redefined as the cross-context comparison**; **`S12`, the registered
descriptive length census, with per-system / per-family / per-stratum reporting, a stated realized
denominator, and the binding prohibition that it may not be used for attribution nor offered on its
own as evidence for E2**; **§13.4's cycle-level rule, in its v2.2 form: for
**P2** a branch fires only if **both** contexts fire it, disagreement being `conditioning_sensitive`;
for **P1** the `C_gen` read stands on its own with the `C_raw` value and the difference **co-reported
mandatorily**, because `C_raw`'s P1 is not a search-error claim and **Certificate S is indexed to the
one decode that ran** (§13.4 rule 0, re-grounded in v2.3);
rule 3 (`one context undecidable`) applying to **both**; rule 4 (NC-CONDITION) scoped to **P2**;
rules 5 and 6 applying to both**; `H0010`'s three predicates, its **frozen 80-system /
89,349-string corpus**, the **graded relative rule** of §9.3, H4's conflict rule and the bound-shaped
budget rule; the interval of record as **the more conservative of a within-fixed-family stratified
bootstrap and Wilson on `n_eval`**, computed **four times, once per endpoint per context, never
pooled**, with **no** Holm and **no** degenerate special case; seeds `20260911` and `77771`; the
`fork` start method; the per-item SymPy reseed; `N_WORKERS = 6`; `CAS_NODE_BUDGET = 400`; the
`run_manifest.py` directory prohibition; the §11b resume ledger; the exclusion rules and their
measured expected counts; the compute ceilings; the artifact contract **including the v2.1 fields
`pre_freeze_exposed`, `context_role`, `certificate_language_permitted`,
`cgen_reconstruction_below_bar`, `gt_longer_than_every_candidate`, `pc_greedy_is_gating: false` and
`contexts_are_not_independent: true`**, **plus v2.2's `p1_cycle_read_is_single_context: true` and
`p1_cross_context_comparison_is_descriptive: true`**; and the reporting sentences of §8.7,
**including v2.2's mandatory P1 co-report and the `L*` limitation required in the cycle report's
limitations section**; **and, added in v2.3: §19's rewritten replication gate — the deleted
"other scoring context" factor, the named admissible factor for a fired P1 (an independently written
scorer, or an independently written `C_gen` forward-map reconstruction) with `CONTROL_CELL_SEED` and
the fresh process path declared insufficient for P1, and §13.6's preregistered disposition of every
replication outcome, under which a fired P1 is PROVISIONAL until the confirmation returns and a
`failed replication` WITHDRAWS it**.

**NO THRESHOLD IN THIS LIST DIFFERS FROM v2.** Every bar, cap, tolerance, cutoff, window, floor and
seed is byte-identical to `plans/C0002_preregistration_v2.md`. What v2.1 changed is **which
disposition a threshold carries** and **which context may say what** — never a number. §25.4 records
this clause by clause, and the supervisor verified it independently: **31 rows, zero rows whose v2
value differs.**
**v2.2 moves none of them either**, and **v2.3 moves none.** v2.2 changed which certificates may be
required to agree; **v2.3 replaces the reason for that and makes §19 enforceable**, neither of which
touches a number. `LB(P1) > 0.5`, `LB(P2) > 0.5` and every control bar stand exactly as frozen —
including in **§13.6**, where replication success is defined by applying the **unchanged**
`LB(P1) > 0.5` to the confirmation rather than by any new bar. §26 and §27 record this.

**Not frozen, because it is a draft**: everything above awaits the supervisor's check (§20).

---

## 23. Disposition of every CRITICAL and MAJOR from both reviews

**Nothing is silently dropped.** Every finding is `FIXED`, `FIXED IN PART + ACCEPTED LIMITATION` with
its consequence stated, `DOWNGRADED` with a stated reason, or `ACCEPTED LIMITATION` with its
consequence stated. `SR` = `reviews/C0002_preregistration_statistical_review.md`;
`RA` = `reviews/C0002_preregistration_reproducibility_audit.md`.

> **§23 is CARRIED FORWARD FROM v2 UNCHANGED.** Every disposition below stands as v2 recorded it. Two
> of them are **superseded in part** by a supervisor decision — **SR-M13** (PC-GREEDY's abort risk,
> superseded by 決定 3) and **RA-M9 / V2-2** (the Gate-4 fork, superseded by 決定 1) — and in both
> cases the v2 text is left intact here, with the supersession recorded in **§25.3**, so a reviewer can
> diff the reasoning and not only the text. **No disposition is weakened, and none is removed.**

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
which quantity carries which certificate; the `neither_cert` definition; `n_eval`'s construction
**per context**; **the co-primacy of the two contexts and the absence of any fallback**; **which
context may carry Certificate-S language**; **§0.3a's `pre_freeze_exposed` marking rule and the
identity of the 8 cells**; **`S12`'s definition, its four reporting levels and its prohibition**;
**PC-GREEDY's REPORT-ONLY class**; **Gate 4's `≥ 0.98` and the single disposition of §7.3.3**; the
§8.5b adjudication; the §9.3 bands; **the §13.2 branch table and §13.4's cross-context rule**.

**Nothing on that list may be changed to rescue a result.** A threshold may never be raised, a
tolerance relaxed, a cap increased or a seed changed for that purpose (rule 01 item 3).

**And specifically**: if the run returns `E2_direction_observed_but_length_unaudited` — the outcome
§0.0 predicts — **that is the result.** It may not be reported as a supported E2, BA2's cutoff may not
be lowered to 0.46, the minimum partner count may not be lowered to 1 or 2, and no length control may
be substituted after the fact. **`S12` may not be offered in place of the control that could not run.**

**And specifically, added in v2.1 and SCOPED in v2.2**: if the two contexts disagree **on P2**,
**`conditioning_sensitive` is the result**, and the context that happened to fire the preferred branch
may not be promoted to primary, reported alone, or described as the "matched" or "correct" one.

**And specifically, added in v2.2 — the one thing a reader could mistake for a post-hoc promotion.**
That P1's cycle read lives in `C_gen` is **not** a promotion of `C_gen` and may never be described as
one. `C_gen` was the **only** context that could carry a search-error claim from the moment §13.2
branch 1 was written, which was **v2.1, before any endpoint was computed**, on an argument (F-g) that
dates to v1. v2.2 does not move P1 into `C_gen`; it **stops requiring P1 to agree with a context that
was already barred from making the claim.** Accordingly:
- `C_raw`'s P1 may not be promoted to the cycle read if `C_gen`'s P1 fails to fire;
- a cross-context P1 difference may not be converted into `conditioning_sensitive` after the fact;
- rule 1b's co-report may not be dropped because the difference is large, or because it is small;
- and **§19's replication gate may not be waived on a fired P1** — it is that read's only cross-check
  (§12.2 step 4).

**And specifically, added in v2.3 — the replication gate and its consequences.** A fired P1 is
**provisional** until §19 returns (§13.4 rule 1a, §13.6). Accordingly:
- the gate **may not be discharged by a factor §19.3 names as insufficient for P1** — not by a
  different `CONTROL_CELL_SEED`, which leaves P1 bit-identical, and not by a fresh process path, which
  reproduces a teacher-forced fp32 number;
- **§13.6's dispositions may not be renegotiated after the confirmation returns.** In particular a
  `failed replication` **withdraws** the verdict to `undecidable (independent derivation disagrees)`
  and may not be re-labelled `directionally replicated`, `inconclusive`, or a difference of
  implementation detail;
- **no numeric bar may be invented for "a material number of systems"** in §13.6's `failed
  replication` row, by the replication specialist or anyone else. The row is reached by quantities
  already frozen;
- **`LB(P1) > 0.5` may not be raised** to compensate for the hurdle rule 2 incidentally gave P1 — the
  delta review confirmed v2.2 did not take that move, and v2.3 does not either;
- and **the original P1 value is retained, never deleted**, whatever the outcome (rule 01 items 4–5). **If they agree, that agreement may
not be reported as confirmation.** If Gate 4's `C_gen` reconstruction measures below `≥ 0.98`, the bar
may not be lowered to 0.9683 or to anything else, and `C_raw` may not be promoted to primary — the
fallback that would have done so was removed before the run, deliberately, and may not be reinstated
afterwards. **If PC-GREEDY returns 0 / 40, that may not be wired to BA1 or to any gate** (§10.2b).

---

## 25. v2.1 disposition — what changed relative to v2, and why

This section exists so a reviewer can **diff the reasoning, not only the text**. v2 is retained
unedited; this is the record of what v2.1 does differently and on whose authority.

**Authority.** `plans/C0002_supervisor_decisions.md`, dated 2026-09-12, three decisions taken
**before Gate 4 runs**. The methodologist took no position on the §7.3 fork in v2 and referred it to
the supervisor; the supervisor's note records that explicitly.

**The single most important fact about this revision: NO THRESHOLD MOVED.** Not one bar, cap,
tolerance, cutoff, window, floor, partner count, seed or ceiling differs from v2. Every one of the
three decisions was taken without moving one, which is what made them takeable at all. §25.4 is the
clause-by-clause check.

### 25.1 Change log, section by section

| § | change | which decision | why |
|---|---|---|---|
| header | version, supersession, "thresholds moved: NONE" row, pointer to the decision record and to §25 | all three | provenance |
| §0.0 | "three consequences" → **four facts**; item 1 gains the binding unreachability statement and the `S12` promotion; item 3 keeps the measured 0.9683 but loses the fallback consequence; **item 4 records the co-primacy decision with its four conditions**; **item 5 records PC-GREEDY's demotion** | 1, 2, 3 | the narrowing must be in the contract, not in a limitations note |
| §0.3 item 2 | v2's "containment survives unless the fallback fires" → **containment withdrawn outright**; the accurate statement is quoted in a block so it cannot be softened | 1 | with `C_raw` co-primary, a co-primary endpoint's proxy was observed pre-freeze; that is prior information, not a contained leak |
| **§0.3a (new)** | the `pre_freeze_exposed: true` marking rule, the Gate-0 artifact, the with/without descriptive sensitivity, the prohibition on aggregating without the flag | 1, condition 2 | "so no analyst can aggregate them unknowingly" |
| §0.7 M1 | promotion note; `pre_measured_before_freeze: true` disclosure | 2 | registering an already-measured quantity requires disclosing that it is already measured |
| §0.9 | PC-GREEDY row and `C_gen` reconstruction row annotated **"not moved"**, with the changed *role* stated | 1, 3 | the table is the audit trail for thresholds; a changed disposition must be visible there |
| §1.4 | forbidden items **9, 10, 11** added: double-confirmation reading; Certificate-S in `C_raw`; `S12` as attribution; PC-GREEDY as a gate | 1, 2, 3 | each decision carries a prohibition; prohibitions live in §1.4 and §8.7 |
| §2.5 | frozen list updated for co-primacy, `pre_freeze_exposed`, `S12`, control classes | all three | §2.5 is the "cannot change" list |
| §4 | denominator table: P1/P2 **per context**; **`S12` row added** | 1, 2 | `n_eval` can differ between contexts (§2.1b's `C_gen` free-symbol clause) |
| §5.3 | "matched one primary, subject to §7.3" → **both co-primary** | 1 | |
| §7.1 | `C_gen` and `C_raw` both **CO-PRIMARY**; "Why `C_gen` is primary" → **"what the F-g argument establishes and what it does not"** | 1 | F-g licenses a *language* asymmetry, not a *rank* asymmetry — and `C_raw` scores the truth exactly, which `C_gen` does not (F-k) |
| §7.2b | Gate 3 **evaluated per context**, with 3b's expected `C_gen`-only failure recorded | 1 | removing the single primary orphaned "in which context is 3b evaluated" |
| **§7.3** | rewritten from **a fork for the supervisor** into **the recorded decision**: options rejected with reasons, the four binding conditions, and §7.3.3's single Gate-4 disposition | 1 | |
| §8.4 | P1/P2 per context; **S1 redefined** as the cross-context comparison; **S12 added** | 1, 2 | S1's v2 definition ("the non-primary context") became meaningless |
| §8.5 | BA2 gains the `S12` pointer **and the statement that `S12` does not rescue it**; **BA4 redefined** as the cross-context comparison, with "agreement licenses nothing" | 1, 2 | |
| **§8.5c (new)** | `S12` registered: definition, four reporting levels, realized denominator, and the binding prohibition on attribution | 2 | |
| §8.7 | the co-primacy sentence block: the required `C_raw` downgraded sentence, the `C_gen` quantization sentence, the required anti-double-confirmation sentence, the `S12` prohibition, the PC-GREEDY prohibition | 1, 2, 3 | |
| §10 | **PC-GREEDY → REPORT-ONLY**; **`C_gen` reconstruction → DOWNGRADE scoped to `C_gen`** (was NAMED-CONTINGENCY) | 3, 1 | |
| **§10.2b (new)** | why PC-GREEDY was demoted, the rejected "gate it in `C_raw` only" option, **what is lost**, what still covers the gap, and the prohibition on wiring `0 / 40` to BA1 | 3 | "what is lost" must be stated, not implied |
| §11 | Gate 0 item 11 (the `pre_freeze_exposed` artifact); Gate 3 per context; **Gate 4 list corrected**; **Gate 6 conjunction loses PC-GREEDY**; **the class list is now exactly three** — v2's fourth class `NAMED-CONTINGENCY` existed on one §10 row but was never listed in §11, and removing the fallback removes the class | 1, 3 | a class used but not defined is the R7 "no contract text to quote" defect in miniature |
| §12.1 | **four intervals**, never pooled; same estimator, seed, resamples and rule | 1 | |
| §12.2 | the cross-context multiplicity exposure, and the **IUT-across-contexts** argument that controls it **without a correction and without moving a threshold** | 1 | four bounds instead of two is a real exposure and must be answered |
| §12.4 | the power cost of the cross-context conjunction, disclosed in advance | 1 | |
| **§13** | restructured into §13.1 reporting / §13.2 **per-context** branches / §13.3 reachability / §13.4 **cycle-level cross-context rule** / §13.5 informativeness. **No condition, cutpoint or bar changed**; a context column was added, the `undecidable` enumeration lost PC-GREEDY, and §13.3 was promoted from a remark to a table | 1, 2, 3 | |
| §14 | PC-GREEDY 0.03 → **0.06 GPU-h** (both contexts); total 0.61 → **0.64**; margin 6.6× → **6.3×**; note that co-primacy costs nothing | 1, 3 | |
| §15 | rows for `pre_freeze_exposed`, PC-GREEDY, `cgen_reconstruction_below_bar` | 1, 3 | |
| §16.2 | seven new unconditional artifact fields | 1, 2, 3 | a decision that lives only in prose is not machine-checkable |
| §18 | **named contingency removed**; **RD1 amended** to name `C_gen` as the retained context | 1 | |
| §19 | the second context is **not** a replication; `conditioning_sensitive` fires the gate | 1 | |
| §20 | supervisor check rewritten for v2.1 | all three | |
| §21 | item 9 amended; **items 11 and 12 added** | 1, 3 | |
| §22 | recompacted, with the "no threshold differs from v2" assertion | all three | |
| §23 | carried forward **unchanged**, with a header note naming the two partially superseded rows | — | v2's reasoning is the historical record |
| §24 | extended with the v2.1-specific "may not" list | all three | |

### 25.2 Every place v2 referred to the removed fallback, and how it was resolved

The fallback was load-bearing. Every reference was located by searching v2's `.md` and `.json` for
`fallback`, `contingenc`, `becomes primary`, `primacy`, `non-primary`, `primary context` and `§7.3`.
**All of them are resolved below; none was left dangling, and none was resolved by weakening a bar.**

| v2 location | what it said | resolution in v2.1 |
|---|---|---|
| §0.0 item 3 | "the frozen consequence (§18's named contingency) is that `C_raw` becomes primary — which collapses the §0.3 containment argument … a decision for the supervisor" | rewritten: the measurement stands, the fallback clause is deleted, and **item 4** records the decision |
| §0.3 item 2, last sentence | "§7.3 further records that if Gate 4's `C_gen` condition fails as M5 predicts, `C_raw` becomes primary and this containment is gone entirely" | deleted; **containment withdrawn outright** and replaced by the §0.3 block quote + §0.3a marking |
| §0.9, `C_gen` reconstruction row | "does not clear (§7.3)" | retained, plus the **changed role**: governs sentence, not primacy |
| §5.3 | "with the matched one primary (§7.1) — **subject to §7.3**" | "**both CO-PRIMARY**. Neither falls back to the other" |
| §7.1 `C_gen` heading | "**PRIMARY, subject to §7.3**" | "**CO-PRIMARY.** The only context that may carry Certificate-S language" |
| §7.1 `C_raw` heading | "**ROBUSTNESS ARM**" | "**CO-PRIMARY.** Certificate-S language is forbidden here" + the exposure pointer |
| §7.1 "Why `C_gen` is primary" | the F-g argument used to establish rank | rewritten as what F-g **does** (language) and **does not** (rank) establish |
| §7.2b, 3b row and Gate-3 scope | evaluated in "the primary" | **evaluated per context**, with the disposition attaching to the failing context |
| **§7.3 in full** | the fork, its three options, "the methodologist takes no position" | replaced by the recorded decision, the rejected options with reasons, the four conditions, and §7.3.3's single Gate-4 disposition |
| §8.2 achievability note | `C_gen` figure "0.9683 … (§7.3)" | pointer retained; §7.3 now says what failing it does |
| §8.4 P1/P2 rows | "primary context" | "**in each of the two co-primary contexts**" |
| §8.4 **S1** | "P1 and P2 recomputed in the **non-primary** context" | **orphaned by the decision.** Redefined as the cross-context comparison of the four co-primary reads |
| §8.5 **BA4** | "S1 — P1 and P2 recomputed in the non-primary context" | same redefinition, plus "**agreement licenses nothing additional**" |
| §8.7 | "reporting a `C_gen` result without `gt_is_quantized_in_context`" | retained; the required `C_raw` downgraded sentence and the anti-double-confirmation sentence added |
| §10, `C_gen` reconstruction row | "**NAMED-CONTINGENCY-CLASS**, §7.3 and §18 … the supervisor's §7.3 decision governs" | **DOWNGRADE-CLASS scoped to `C_gen`**, §7.3.3, one row, no new threshold |
| §10, PC-GREEDY row | "evaluation context is the PRIMARY context" | **run in both contexts, REPORT-ONLY** |
| §11 Gate 4 | "the `C_gen` reconstruction is **NAMED-CONTINGENCY** per §7.3"; "PC-GREEDY's evaluation context is the PRIMARY context" | both corrected; the ABORT / DOWNGRADE / REPORT-ONLY lists rewritten |
| §11 Gate 6 | conjunction included PC-GREEDY; reported "the primary" | **per context**, PC-GREEDY struck |
| §12.1 | one interval of record, in "the primary context" | **four intervals**, one per endpoint per context, never pooled |
| §13.2 | branches evaluated "in the primary context"; `undecidable` enumeration listed PC-GREEDY | **per-context branch table** + **§13.4 cycle-level rule**; PC-GREEDY removed from the enumeration |
| §13.2 BA4 row / `conditioning_sensitive` | verdict existed but had no cycle-level rule attached | promoted into **§13.4**, which is now the only place a cycle verdict is formed |
| §18 named contingency | "if it is the fallback, `C_raw` becomes primary …" | **removed**; replaced by the permanence of the downgraded sentence and the outright withdrawal of containment |
| §18 **RD1** | "single context (**the primary only**)" | **orphaned by the decision.** Amended to name **`C_gen`** as the retained context in advance |
| §20 item 2 | "the §7.3 `C_gen` / `C_raw` **fork**" | rewritten as the check that the decision is faithfully reflected |
| §21 items 8, 9 | "in the primary context" | reworded to `C_gen`; item 9 amended for the demotion |
| §22 | "the two scoring contexts and the §7.3 primacy decision" | "two **co-primary** contexts … **no fallback**" |
| §23 **V2-2** | "**ESCALATED** to the supervisor as a preregistered fork" | left **unedited** as the historical record; **§25.3** records that it is now discharged |
| §24 | "the §7.3 context decision **once the supervisor has recorded it**" | the decision is recorded; §24 now freezes it and adds the v2.1 "may not" list |
| `.json` `the_c_gen_c_raw_fork_for_the_supervisor`, `if_C_gen_fails`, `third_option_recorded_so_it_is_preregistered`, `methodologist_position`, `named_contingency`, `gates.gate_4_controls.named_contingency`, `secondary.S1`, `BA4.measurement`, `C_gen_reconstruction.class` | the fork and the fallback in machine-readable form | all rewritten in `C0002_preregistration_v2.1.json`; the fork keys are replaced by `the_c_gen_c_raw_decision_TAKEN` and the `named_contingency` key by `named_contingency_REMOVED` **stating that it was removed and why**, so the removal is itself machine-readable rather than an absence |

**Two orphans found and named, since a silent orphan is the real risk of removing a load-bearing
clause:** **S1 / BA4's "non-primary context"** and **RD1's "the primary only"**. Both were phrases
whose referent ceased to exist; both are redefined above rather than deleted.

### 25.3 v2 §23 rows that a supervisor decision supersedes in part

**Neither is weakened; both v2 texts stand unedited in §23.**

| v2 §23 row | v2's disposition | superseded how |
|---|---|---|
| **SR-M13** (PC-GREEDY: hard abort on the primary, achievability from the non-primary context, ~40% abort risk disclosed) | FIXED IN PART + ACCEPTED LIMITATION: context stated, operating characteristic disclosed, **live abort risk carried into Gate 4** | **決定 3.** The accepted limitation is **removed rather than carried**: the control is REPORT-ONLY, so the unverified expected value no longer sits on a gate and there is no abort risk to carry. The **bar was not moved**. What replaces the limitation is §10.2b's explicit statement of the demonstration C0002 therefore cannot make, and §21 item 9 |
| **RA-M9 / V2-2** (Gate 4's `C_gen` condition redefined and measured at 0.9683; the fork escalated) | FIXED for the redefinition; the fork **ESCALATED** to the supervisor | **決定 1.** The escalation is **discharged**: both contexts co-primary, no fallback, and Gate 4's unmoved `≥ 0.98` carries the single DOWNGRADE disposition of §7.3.3 |

### 25.4 Threshold-integrity check, clause by clause

Every numeric bar that v2 froze, confirmed unchanged in v2.1:

| threshold | v2 | v2.1 | note |
|---|---|---|---|
| system cutpoint `sb_rate(s) ≥ 0.5` | 0.5 | **0.5** | inherited from C0001 v2.1 §8.3 |
| corpus cutpoint in the decision rule | 0.5 | **0.5** | |
| `E2_system` `me_rate(s) = 1` | 1 | **1** | |
| BA1 bar | median ≥ 0.95 | **≥ 0.95** | |
| BA2 availability cutoff | < 0.5 | **< 0.5** | measured 0.4625 / 0.4990; **not moved, which is the whole finding** |
| BA2 minimum in-window partners | 3 | **3** | |
| BA2 window | ±round(0.20·len_gt) | **±round(0.20·len_gt)** | |
| BA2 disagreement bar | > 20% | **> 20%** | |
| BA3 flip bar | > 0.05 | **> 0.05** | |
| Gate 3a | 80 / 80 | **80 / 80** | now per context |
| Gate 3b | ≥ 90% | **≥ 90%** | now per context, downgrade-only as in v2 |
| Gate 3c | ≤ 20% | **≤ 20%** | |
| PC-GREEDY | ≥ 2 of 40 | **≥ 2 of 40** | **class changed ABORT → REPORT-ONLY; the bar did not** |
| PC-HOLDOUT / NC-HOLDOUT | ≥ 0.95 / ≤ 0.05 | **unchanged** | both still ABORT |
| NC-CONDITION | ≥ 0.95, \|Δ\| > 1 nat | **unchanged** | still DOWNGRADE |
| `C_gen` reconstruction | ≥ 0.98 | **≥ 0.98** | **class changed NAMED-CONTINGENCY → DOWNGRADE; the bar did not** |
| re-encoding round trip | ≥ 0.90 per control cell | **unchanged** | |
| re-encoding mismatch caps | 10% / 10% | **10% / 10%** | now per context |
| `EncodingVerificationFailure` cap | ≤ 20% | **≤ 20%** | |
| regression identity | < 1e-5 | **< 1e-5** | |
| `CAS_NODE_BUDGET` | 400 | **400** | |
| `H0010` bands (0, 0.10, 0.50) | — | **unchanged** | |
| `H0010` `n_class_pow4` | ≥ 10 | **≥ 10** | |
| evaluable-system floor | ≥ 8 of 12 + all four settings | **unchanged** | |
| interval of record | conservative of stratified bootstrap and Wilson, 10,000 resamples | **unchanged**, run four times | |
| one-sided error rate per branch | 0.05 | **0.05** | conjunction across contexts, **no correction applied and none needed** |
| Gate 2a projection bar | ≤ 8 CPU core-h | **≤ 8 CPU core-h** | |
| Gate 5 projection bars | ≤ 2.0 GPU-h, ≤ 12 CPU core-h | **unchanged** | |
| compute ceilings | 4.0 GPU-h / 24 core-h / 5.5 GiB / 15 GiB | **unchanged** | §14 total rose 0.61 → 0.64 GPU-h, **well inside** |
| wall-clock guard | 10.0 s | **10.0 s, not raised** | |
| all seeds | 20260911 / 20260912 / 77771 | **unchanged** | |

**Additions that are not thresholds**: `S12` has **no** threshold (§8.5c forbids one); §0.3a's marking
rule has none; §13.4's cross-context rule is a **conjunction of existing** conditions and introduces
no number.

### 25.5 Found unimplementable as stated in the three decisions

Reported rather than quietly absorbed, per §21's discipline.

1. **決定 3 offered two options — "move PC-GREEDY to reported-non-gating, **or** give it a verified
   achievable expected value."** The second is **not available before freeze**: verifying it in
   `C_gen` requires `lp_best` under `C_gen`, which §0.4 forbids, and verifying it in `C_raw` only
   (where 2 / 10 *is* measured) would let a control verified in the **already-observed** context gate a
   co-primary cycle, and would give one condition two dispositions across contexts — the defect §7.2b
   exists to prevent. **The first option is taken**, and the rejected alternative is recorded in
   §10.2b so the choice is auditable rather than assumed.
2. **決定 1's condition 2 says "mark those 8 cells `pre_freeze_exposed: true` in every `C_raw`
   artifact".** Implemented as stated, **and extended**: `C_gen` artifacts carry the same field with
   value `false` rather than omitting it, because an omitted field is indistinguishable from a
   forgotten one and cannot be machine-checked. This is stricter than the decision, not weaker.
3. **決定 2 asks for `S12` "per-system, per-family and per-stratum" reporting.** "Stratum" is not a
   term v2 defines. It is implemented as the four `(noise_sigma, subsample_rho)` corruption settings —
   the only cell-level stratification in the design that is not already the family — and **not** as
   the eight families, which are covered by the per-family limb. If the supervisor meant something
   else by "stratum", this is the one place v2.1 chose an interpretation; it is flagged here rather
   than buried. **Note also that dimension and family are completely confounded** (§2.1), so a
   per-dimension breakdown is not available and is not offered.
4. **Nothing in the three decisions was found unimplementable in substance.** The 決定 1 fallback
   removal, the 決定 2 promotion and prohibition, and the 決定 3 demotion are all implemented as
   written, without moving a threshold.

### 25.6 What a reviewer should attack first

Stated so the adversarial reviewer does not have to find it:

1. **§13.4's cross-context conjunction is a design choice, not a derivation.** It controls the
   four-bound multiplicity exposure and prevents an already-observed context from carrying a
   conclusion alone — but it also means a genuine, real effect visible in one context and absent in
   the other yields `conditioning_sensitive` and no conclusion. That is a deliberate loss of power
   (§12.4), and a reviewer may reasonably argue it is the wrong trade.
   > **SUSTAINED, and acted on. 2026-09-12.** The supervisor agreed and **sent rule 2 back for P1**,
   > on a stronger ground than the one given here: not that the trade is bad, but that **the contract's
   > own §13.2 branch 1 already says `C_raw`'s P1 is not a search-error claim**, so requiring
   > agreement required agreement with a different quantity. **v2.2 §13.4 rule 0** implements it.
   > This paragraph is left as written, because it is v2.1's record and v2.1's record is not edited.
2. **§7.3.3's choice of DOWNGRADE over ABORT for the `C_gen` reconstruction.** The argument is that
   §2.1b and §8.2 already remove and escalate on exactly the affected candidates, so an abort would
   be a second disposition for one condition. A reviewer should check that claim directly against
   §2.1b's usable-candidate definition.
3. **PC-GREEDY's demotion leaves no control that demonstrates a live out-of-set competitor.** §10.2b
   argues PC-HOLDOUT covers the C0001 defect and BA1 covers the opportunity question. A reviewer
   should test whether PC-HOLDOUT's "by construction" achievability really is context-independent.
4. **`S12` is a registered endpoint whose value was measured before freeze.** §0.7 and §8.5c argue
   this is admissible because it is descriptive, unthresholded and barred from attribution. A reviewer
   should check that no §13 branch, no gate and no audit reads it.
5. **`C_raw` is co-primary and its proxy was observed on 8 cells, pre-freeze, in the preferred
   direction.** §0.3a bounds and marks the exposure; it does not eliminate it. This remains the
   cycle's sharpest validity threat and the cycle report must say so.

---

## 26. v2.2 disposition — the single change from v2.1, and every place it rippled

v2.1 is retained unedited. This section records what v2.2 does differently and on whose authority, so
a reviewer can diff the reasoning and not only the text.

### 26.1 Authority and scope

**Authority.** `plans/C0002_supervisor_decisions.md`, **追補 dated 2026-09-12** (commit `15e308a`):
the supervisor verified v2.1, **sustained three of its four flagged items as written**, and **sent one
back**.

| item | supervisor's disposition |
|---|---|
| §25.6 item 2 — DOWNGRADE not ABORT for the Gate-4 shortfall | **UPHELD.** The supervisor read §2.1b directly and confirmed that "usable candidate" already requires the re-encoding round trip to be **exact**, so the premise holds. Carried into v2.2 unchanged |
| §25.6 item 3 — PC-HOLDOUT covers the C0001 defect | **UPHELD**, and strengthened: PC-HOLDOUT's achievability is **arithmetic, not an assumption** — a strict maximum used as pseudo-truth returns `sb_best = 1` by construction, a property of the comparison and therefore context-independent. **One addition implemented**: the out-of-set-competitor gap must appear in the **cycle report's limitations section** as well as §10.2b (§8.7, §10.2b, §13.1) |
| §25.5 item 3 — "per-stratum" read as the four `(noise_sigma, subsample_rho)` settings | **CONFIRMED.** Dimension and family are fully confounded per §2.1, so no other cell-level stratification exists. Flagging rather than burying it was the right call. Unchanged |
| **§25.6 item 1 — the cross-context conjunction** | **SUSTAINED AND SENT BACK.** This is the whole of v2.2 |
| threshold-integrity table | **independently verified**: 31 rows, **zero rows whose v2 value differs from v2.1**; the four textual diffs all say "unchanged". v1 and v2 unmodified |

**Scope.** v2.2 changes **§13.4 rule 2** and the things that depended on it. It changes **nothing
else**: not a hypothesis, not an endpoint definition, not a cutpoint, not a control, not a gate, not a
seed, not a budget, not the `H0010` design, not the artifact contract except for four new
machine-checkable flags.

### 26.2 The send-back, and why the supervisor's reason is stronger than the methodologist's

**v2.1 §13.4 rule 2** made a cross-context disagreement collapse to `conditioning_sensitive`, with
nothing concluded **about either certificate**. §25.6 item 1 flagged this as a possibly-bad trade:
a real effect in one context and not the other yields no conclusion.

**The supervisor's ground is different and stronger, and it is internal to this contract:**

> **§13.2 branch 1 already says `C_raw`'s P1 is not a search-error claim** — it licenses only "the
> truth outscores all 50 candidates under a conditioning the search did not see". So requiring
> cross-context agreement on P1 **requires agreement with a quantity that measures something else.** A
> certified search error in `C_gen` — the context the search actually ran in — would then vanish
> because it differed from a number that was never a search-error claim.

**That is a category error, not a conservative trade**, and it is visible without any data. The
methodologist's version of the objection ("a deliberate loss of power, possibly the wrong trade")
would have been arguable either way; the supervisor's is not.

**P2 is unaffected** because `me_best` carries no search semantics.

> ~~"the truth is not the model's argmax under the conditioning it was scored in" is the **same
> proposition** in both contexts, so the two measurements **are** commensurable and may be required to
> agree.~~
>
> **WITHDRAWN in v2.3 (delta review MAJOR-1). The struck clause is FALSE** — `C_gen` and `C_raw`
> induce different conditional distributions and the two argmax statements are **logically
> independent** — **and it is symmetric**, so it applied verbatim to the P1 row and could not support
> the asymmetry it was written to support. **The correct reason P2 is unaffected**: Certificate N is a
> **property of the model**, not a claim about any decode, and **neither conditioning is privileged**
> as a probe of the model's preference ordering — so a Certificate-N conclusion holding under only one
> of them is **conditioning-dependent**, and requiring both is a real robustness demand. See §13.4
> rule 0. **The conclusion — rule 2 retained for P2 — is unchanged.**

### 26.3 Every place the change rippled

| § | what changed | why it had to change |
|---|---|---|
| header | version, supersession, "what v2.2 changes" row | provenance |
| §0.0 | **new item 6** recording the send-back, the P1/P2 commensurability split, and that the relaxation runs only on the **refuting** branch | the narrowing and the loosening both belong in the contract's opening, not in a late section |
| §7.3.2 condition 4 | **a second, independent reason added for P1**: the two values are not the same quantity, so the `C_raw` P1 can neither confirm **nor disconfirm** | v2.1's only reason was non-independence (shared inputs). For P1 the prior objection is non-commensurability, and it forbids the *disconfirming* reading too — which v2.1 did not address |
| §8.5 **BA4** | consequence **scoped per certificate**: gating for P2, **descriptive and mandatory-to-report** for P1 | BA4 was the mechanism rule 2 ran through |
| §8.7 | **four new forbidden** readings of the `C_raw` P1 (confirm / disconfirm / conditioning-dependence / `conditioning_sensitive`), **one new required** four-part co-report, and **the `L*` limitation required in the cycle report's limitations section** | a prohibition that exists only in §13.4 is not enforceable at reporting time |
| §10.2b | the out-of-set-competitor gap must also reach the cycle report's limitations section | the supervisor's addition to the upheld push-back |
| §12.2 | **re-derived from scratch, per certificate** (§26.5 summarises; the derivation itself is in §12.2 steps 1–6) | the IUT-across-contexts argument was v2.1's answer to the four-bound exposure and it no longer covers P1 |
| §12.4 | the cross-context power cost **scoped to P2**; P1's restored power stated as a **correction, not a concession**, with its cost named | v2.1's disclosure would otherwise misdescribe P1 |
| §13.1 | the four-part P1 co-report and the `L*` limitation added to "always reported" | rule 1b is only real if it is in the reporting list |
| §13.2 | preamble states how each certificate reaches the cycle level; branch 1's `C_gen` limb marked as the cycle-level P1 verdict; branch 1's `C_raw` limb marked as **never** producing one | the branch table is applied per context and had to say what each limb becomes |
| §13.3 | reachability row 1 corrected from "in **both** contexts" to `C_gen`; **a new row** for `LB(P1 \| C_raw) > 0.5` alone; `conditioning_sensitive` split into the P2 form and rule 3's form | v2.1's row 1 stated the superseded requirement — this was the clearest orphan |
| **§13.4** | **rewritten**: rule 0 (commensurability premise), rule 1 (P1, five parts), rule 2 (P2, retained in full), rule 3 (unchanged, **applies to P1 too**, with the reason it is not relaxed), rule 4 (scoped to P2, **with the reason extending it would be a rule 01 item 8 error**), rule 5 (now applies to rule 1b as well), rule 6, and a summary table | the send-back itself |
| §13.5 | first bullet corrected from "in both contexts" to `C_gen` | orphan |
| §16.2 | **four new frozen flags** so the split is machine-checkable | a decision that lives only in prose is not machine-checkable — the same standard v2.1 applied to 決定 1 |
| §19 | §19 named as **P1's only cross-check**, mandatory and non-waivable; a **second reason** the second context is not a replication | this is what replaced the incidental conservatism rule 2 had given P1 |
| §20 | supervisor check items **6–10** for v2.2 | items 1–4 are discharged for v2.1 |
| §22 | the cycle-level rule restated in its split form; the new flags; the "v2.2 moves no threshold either" assertion | §22 is the compact frozen statement |
| §24 | the P2-scoped disagreement sentence; **a new block on the one thing a reader could mistake for a post-hoc promotion of `C_gen`** | see §26.6 |
| §25 | §25.6 item 1 annotated **SUSTAINED, and acted on**, with the stronger ground recorded; the paragraph left as written | v2.1's record is not edited, but a reader must not find a live concern that has since been discharged |

> **CORRECTED in v2.3 (delta review MAJOR-3, MINOR-1, and one finding of the author's own re-read).
> The "checked and found NOT to need changing" list below is WRONG in three places, and is left
> standing with its errors marked rather than quietly repaired.** §27.4 is the full re-read.
> **§21 did need an edit** (its item 12 stated the superseded rule as frozen fact — the review's
> MAJOR-3); **§18 did need an edit** (RD1 cited the deleted conjunction — MAJOR-4, and §26.3 had
> listed §18 among the unchanged); and **§12.1 did need an edit** (its "branch-level agreement check"
> characterisation is true of P2 only — found by the author on re-read, missed by both the author and
> the review). **A certification of "no change needed" produced from recollection rather than from
> reading is worth nothing, and this is the demonstration.**
>
> **Also missing from the ripple table, per MINOR-1:** **§25.4's threshold-integrity row for the
> one-sided error rate** still justifies 0.05 by "**conjunction across contexts**, no correction
> applied and none needed". For **P1** that justification is superseded — §26.4 and §12.2 step 5
> re-derive 0.05 by **exclusivity plus a single test**. §25 is retained unedited by design, which is
> the right convention; but the supersession belongs in this table and was not recorded. It is
> recorded here and in §27.5.

**Checked and found NOT to need changing** — recorded so the check is auditable
**(this list is wrong in three places; see the correction immediately above)**:

- **§13.4 rule 3** — carried over verbatim and **extended in scope explicitly to P1**, per instruction.
  Its ground is instrument failure on a **shared** instrument, which commensurability does not touch;
  and rule 1b's co-report **cannot be produced** if one context's read does not exist.
- **§10's NC-CONDITION row** — already scoped correctly: its DOWNGRADE consequence is that BA4
  "blocks any conclusion resting on **context agreement**". P1's cycle read no longer rests on context
  agreement, so **no edit was needed and none was made**. §13.4 rule 4 states the scope rather than
  changing the control.
- **BA1, BA2, BA3** — untouched. All three still **block a supported E2**; none was scoped, weakened
  or rerouted. BA1 additionally still kills the P1 cycle read when it fires **in `C_gen`** (rule 1e).
- **§13.2 branches 2–7**, §8.5b, §8.5c, §9, §10 (except the 10.2b note), §11, §14, §15, §17, §18, §21,
  §23 — no reference to rule 2 and no edit.
- **§12.1** — four intervals, never pooled: unchanged. The number of intervals did not change; only
  which of them can fire a conclusion.

### 26.4 Threshold integrity for v2.2

**No threshold moved.** §25.4's 31-row table stands unaltered and every row's value is still the v2
value. In particular:

| threshold | status in v2.2 |
|---|---|
| `LB(P1) > 0.5` | **not moved.** The condition is identical; only the set of contexts required to satisfy it changed, from "both" to "`C_gen`" |
| `LB(P2) > 0.5` | **not moved**, and still required in **both** contexts |
| every control bar (PC-HOLDOUT, NC-HOLDOUT, NC-CONDITION, PC-GREEDY, regression identity, `C_gen` reconstruction, round trip, PC/NC-H0010) | **not moved**, and no control's class changed in v2.2 |
| BA1 0.95, BA2 0.50 / window / floor 3 / 20%, BA3 0.05 | **not moved** |
| one-sided error rate per branch | **0.05**, unchanged; §12.2 re-derives that it is still attained, by exclusivity for the cycle's two possible conclusions and by an IUT within P2 |
| `p̂ ≥ 48 / 80 = 0.600` | **not moved.** Still necessary in each context; now necessary **and sufficient** for the P1 cycle read given branch 1's other conditions, which is a consequence of the rule change, not a change to the number |
| ceilings, seeds, caps, tolerances | **not moved** |

**And the compensation that was NOT taken**: raising `LB(P1) > 0.5` to buy back the hurdle rule 2 had
incidentally given P1 would have been the forbidden move in its most tempting shape (rule 01 item 3).
It was not taken. The replacement is **external** — §19 — and is named as such.

### 26.5 The multiplicity re-derivation, in one paragraph

Of the four reported one-sided bounds, **three are decision-bearing**: `LB(P1 | C_gen)` fires the P1
conclusion alone, and `LB(P2 | C_gen)` with `LB(P2 | C_raw)` fire the P2 conclusion only conjoined.
`LB(P1 | C_raw)` is **descriptive by contract**. **P2 keeps its intersection–union argument unchanged**
— a conjunction of level-0.05 one-sided conditions attains 0.05 with no correction. **P1 has no
multiplicity to correct**, because there was never a second test of the search-error proposition: the
exposure v2.1's conjunction controlled was an artefact of treating two non-commensurable quantities as
two shots at one proposition. The **honest statement is that P1 carries a single-context read** with
no internal cross-check, at a one-sided error rate of 0.05. Across the cycle's **two** possible
conclusions the family-wise rate remains **≤ 0.05 with no correction**, by the **exclusivity** of
`E3_system` and `E2_system` within a context — a fact about the indicators, **not** a claim that the
propositions E2 and E3 are exclusive (§1.1 establishes they are not). Full derivation, including the
two residual exposures and the direction check, is §12.2 steps 1–6.

### 26.6 The objection a reviewer should raise first about v2.2

**"Scoping rule 2 to P2 promotes `C_gen` for P1, and it happens to help the branch the campaign would
find newsworthy."** Both halves deserve an answer.

1. **It is not a promotion.** `C_gen` has been the **only** context that could carry a search-error
   claim since §13.2 branch 1 was written — in **v2.1**, before any endpoint was computed, on the F-g
   argument that dates to **v1**. v2.2 does not move P1 into `C_gen`; it stops requiring P1 to agree
   with a context this contract had **already barred** from making the claim. §24 freezes the
   prohibition on describing it as a promotion.
2. ~~**No realized value is known.** §0.4 still forbids `lp_best` under `C_gen`, so no P1 value in
   either context has been computed or seen by anyone. The change cannot have been fitted to an
   outcome because there is no outcome.~~

   > **WITHDRAWN in v2.3 (delta review MAJOR-2). The struck text above is FALSE, and it is left
   > visible rather than deleted.**
   >
   > **Why it is false — the contract contradicts it twice, in its own text.** §0.3 discloses that
   > `lp_gt`, `lp_best` and **`sb_best`** were computed and printed on **8 of 960 cells under
   > `C_raw`**, with **`sb_best = 0` on all eight**. §0.3 item 2 states, as this contract's own adopted
   > and unsoftenable position: *"A co-primary endpoint's own proxy was observed, before freeze, on 8
   > of 960 cells, in the direction the campaign prefers. This is prior information about a co-primary
   > context. It is **not** contained."* Answer 2 therefore **denied, in §26, prior information that
   > §0.3 discloses and refuses to call contained** — and it did so in the one place where the
   > objection being answered is about outcome-fitting.
   >
   > **And the direction is the adverse one.** Eight observed cells all at `sb_best = 0` is `C_raw`'s
   > P1 running **low** — which is **exactly the configuration in which the removed cross-context
   > conjunction would have bound against a fired `C_gen` P1**. That is the worst direction for this
   > particular denial to have been wrong in.
   >
   > **What replaces it.** No **aggregate** P1 value in either context has been computed: §0.4 still
   > forbids `lp_best` under `C_gen`, and no corpus-level rate exists in either context. But **partial,
   > directional outcome information about `C_raw`'s P1 does exist** — 8 of 960 cells, all
   > `sb_best = 0` — and by §0.3 item 2's own reasoning (gaps of 100–500 nats) it is informative about
   > `C_gen`'s. **The change is defended by answer 1's dating, not by an absence of outcome
   > information.**
   >
   > **This is not evidence the change was outcome-fitted.** Answer 1 is a genuine, dated defence and
   > the delta review verified it independently; 8 of 960 cells is thin. But **the correct form of this
   > answer is disclosure, not denial**, and §0.3 already shows this contract knows how to write one.
3. **The direction is against the campaign's preference, not with it.** P1 **refutes** the
   E2-direction reading; P2 is the preferred direction and **keeps the full conjunction and all five
   conjuncts**. §12.2 step 6 states this check explicitly, and the delta review **verified it true**
   change by change.

   > **Narrowed in v2.3 (delta review §3, §4).** This answers the **E2-preference** half of the
   > objection and **not the newsworthiness half**, and the two come apart here. §13.3 records that
   > `certified_non_argmax_prevalent` is **unreachable in either context**, so the campaign's preferred
   > *answer* is off the table before the run; **the only branch v2.2 could affect is P1**, which fires
   > `H0003` and is the one a reader would find publishable. So the direction check is real but
   > **narrower than the objection §26.6 raises against itself**, and **answer 1's dating must carry
   > the newsworthiness half alone.** It can: §13.2 branch 1 was written in v2.1, before any endpoint
   > was computed, on an argument dating to v1.
4. **What a reviewer should still attack**: that P1 now has **no internal cross-check**, which §12.2
   step 4 concedes in those words. If §19's replication gate is not actually executed on a fired P1,
   the read stands on one context, one seed and one process — and the contract would then have traded
   a mis-derived protection for a promised one that was never delivered. **Verifying that §19 fires is
   the single highest-value check an independent reviewer can make on this cycle's P1 result.**

---

## 27. v2.3 disposition — the delta review's seven findings, and the re-read it forced

v2.2 is retained unedited. This section records what v2.3 does differently and why.

### 27.1 The review, and what it settled

**`reviews/C0002_v2.2_delta_review.md`**, `lansr-statistical-reviewer`, 2026-09-12, commit `4e65606`.
Scope: the v2.2 delta only (§13.4, §12.2, §19, §26 and an orphan sweep). **It made no edit to any
contract.**

**What it settled in v2.3's favour, and which therefore does not change:**

- **The v2.2 decision is correct and stands.** Requiring P1 to agree with a reading the contract had
  already barred from making the claim was incoherent.
- **The direction check of §12.2 step 6 VERIFIES TRUE**, change by change: every relaxation lands on
  P1, none on P2, and §13.2 branch 2 still carries all five audit conjuncts.
- **No threshold moved anywhere in the delta.** The reviewer specifically checked the tempting move —
  raising `LB(P1) > 0.5` to buy back the hurdle — and confirms it was not taken. `P(pass | 40,
  p = 0.95) = 0.6767` was recomputed and confirmed.
- **§12.2 step 4 "is exemplary and should not be softened."** It is not softened in v2.3; §27.3
  explains why the §19 repair does not soften it.
- **§19's firing is airtight** and the second context is correctly ruled out as a replication factor.

**Verdict: 1 CRITICAL, 4 MAJOR, 2 MINOR — all textual, none requiring a threshold to move or anything
to be recomputed. All seven are accepted in full. None is contested, downgraded or deferred.**

### 27.2 Disposition of every finding

| # | severity | finding | disposition | where |
|---|---|---|---|---|
| 1 | **CRITICAL** | §19 is declared P1's only cross-check but cannot carry it: its menu contains "the other scoring context", which §19 itself declares invalid; `CONTROL_CELL_SEED` leaves P1 **bit-identical**; a fresh process path is a reproducibility check, not a validity check; and **no outcome of the gate has any stated consequence** | **FIXED, all three limbs.** §19 rewritten into §19.1–19.5: the orphan factor **deleted**; **§19.3 suspends the "at least one of" rule for a fired P1** and names the two admissible factors, with `CONTROL_CELL_SEED` and the fresh process path **declared insufficient with the reason**; and **§13.6 is new**, preregistering the disposition of every outcome, under which a fired P1 is **provisional** and a `failed replication` **withdraws** it | §19, §13.6, §13.4 rule 1a, §16.2, §24 |
| 2 | MAJOR | rule 0's "commensurability" ground is **false and symmetric**: the P2 row's "same proposition" claim is self-contradicting, and the P1 row's ground applies verbatim to it, so rule 0 cannot support its own asymmetry — and run consistently it licenses dropping rule 2 **for P2** | **FIXED by replacing the premise, not the conclusion.** Rule 0 re-grounded on **what each certificate is indexed to**: Certificate S to **a historical decode event**, of which there was **exactly one**; Certificate N to **a property of the model**, for which **neither conditioning is privileged**. The "same proposition" claim is **withdrawn as false**, with the hazard stated. Echoes corrected in all six places | §13.4 rule 0, §7.3.2 cond 4, §8.7, §12.2 step 3, §13.4 rules 1c/3/6, §22, §0.0 item 6 |
| 3 | MAJOR | §26.6 answer 2 — "no P1 value in either context has been computed or seen" — is **false**; §0.3 discloses 8 of 960 cells under `C_raw`, all `sb_best = 0`, in the direction the removed conjunction would have bound | **FIXED by withdrawal, struck text left visible.** Replaced with the §0.3-consistent statement: no **aggregate** value exists, but partial directional information does, its direction is the adverse one, and **the change is defended by answer 1's dating, not by an absence of outcome information**. Answer 3 narrowed to concede it covers the E2-preference half and **not** the newsworthiness half | §26.6 |
| 4 | MAJOR | §21 item 12 states the superseded rule as frozen fact — and §26.3 **certified §21 as needing no edit** | **FIXED.** Item 12's v2.1 form **withdrawn as false**; rewritten to what is actually unimplementable (a single-context **P2** verdict; either kind under rule 3 / RD1); the surviving protection restated **on the facts** — P1's single context is `C_gen`, the **unobserved** one, and `C_raw` cannot carry a P1 verdict at all. §26.3's certification corrected in place | §21 item 12, §26.3, §27.4 |
| 5 | MAJOR | §18 RD1 is grounded on the deleted conjunction and does not say whether a P1 verdict forms | **FIXED, outcome unchanged, ground replaced.** RD1 re-grounded on **rule 3** — not its instrument-failure trigger, but its **operative condition**, since rule 1b's mandatory co-report cannot be produced when no `C_raw` read exists. **Stated explicitly: under RD1 no cycle-level verdict forms, for either certificate** | §18 RD1 |
| 6 | MINOR | §25.4's "one-sided error rate" row still justifies 0.05 by "conjunction across contexts"; §26.3's ripple table does not record it as superseded | **FIXED.** Recorded in §26.3's correction block and in §27.5. §25 itself stays **unedited by design** | §26.3, §27.5 |
| 7 | MINOR | rule 1b requires a **reading** of a comparison that §10 declares `uninterpretable` when NC-CONDITION fails | **FIXED.** When NC-CONDITION has failed the co-report carries **`ba4_uninterpretable: true`**, item 3 is satisfied by recording that and nothing else, and **no interpretation may be offered**. Items 1 and 2 are still reported | §13.4 rule 1b, §16.2 |

### 27.3 Why the §19 repair does not soften §12.2 step 4

The review was explicit that step 4's loudness is right and its **enforceability** was what was
missing, and that softening it would be the wrong repair. **Nothing in step 4 is withdrawn or
qualified.** P1 still carries a single-context read; it still has **no internal cross-check**; the
incidental conservatism v2.1's conjunction gave it is still **gone**; and `LB(P1) > 0.5` is still not
raised to compensate. What v2.3 adds is a **new bullet** recording that v2.2's replacement was a
promise it could not keep, and that the replacement is now a mechanism: a named factor that can
actually perturb P1, and a preregistered consequence for every outcome including failure.

**The standard being applied is the review's own**: *a declared protection that is not delivered is
worse than declaring none.* v2.2 declared one. v2.3 delivers it or, where it cannot, says so.

### 27.4 Re-read of every §26.3 "no change needed" entry — by reading, not by recollection

The review's MAJOR-3 noted the aggravating fact that §26.3's own audit row certified §21 as needing no
edit. **The whole list was therefore re-read against the v2.2 text, not recalled.** Method: locate
every occurrence of rule-2-dependent language — `cross-context conjunction`, `conjunction across`,
`both contexts to agree`, `requires the two contexts`, `agree before any`, `conditioning_sensitive`,
`§13.4`, `rule 2`, `cross-context` — and attribute each hit to its enclosing section.

| entry certified "no change" in §26.3 | re-read result |
|---|---|
| **§21** | **WRONG — needed an edit.** Item 12, line 2697 of v2.2: "§13.4 requires the two contexts to agree before any cycle-level branch fires." The review's MAJOR-3. Fixed |
| **§18** | **WRONG — needed an edit.** RD1, line 2538 of v2.2: "§13.4's cross-context conjunction cannot be evaluated." The review's MAJOR-4. Fixed |
| **§12.1** | **WRONG — needed an edit, and this one both the author and the review missed.** Line 1918 of v2.2: "the cross-context comparison is a **branch-level agreement check** (§13.4)". True of **P2 only**; for P1 the comparison is a mandatory reported difference bearing **no decision**. Found on this re-read and fixed (§12.1) |
| §11 | **correct — no edit needed.** Three hits (lines 1756, 1803, 1835 of v2.2) are **pointers** to §13.4, not restatements of rule 2: "§13.4 governs what that means for the cycle verdict" and "the other context's read stands with §13.4 applying". Both remain true under v2.3, where rule 3 is exactly what §13.4 supplies in that situation |
| §13.2 branches 2–7 | **correct.** Branches 2–7 are per-context conditions; only branch 1 needed the cycle-level annotation, and it received it in v2.2 |
| §8.5b | **correct.** Zero hits. The S8 adjudication is about co-reporting and inference, not about contexts |
| §8.5c | **correct.** Zero hits. `S12` is context-free by construction — token length does not depend on the conditioning |
| §9 | **correct.** Zero hits. `H0010` consumes no log-probability and is context-free; §13.2 already states the cross-context rule does not apply to it |
| §10 | **correct.** Zero hits beyond the §10.2b note already made. **The NC-CONDITION row in particular was already correctly scoped** — its consequence is that BA4 "blocks any conclusion resting on **context agreement**", and P1's cycle read does not rest on context agreement. §13.4 rule 4 states the scope rather than changing the control |
| §14, §15, §17, §23 | **correct.** Zero hits |
| **§13.4 rule 3** | **correct as an outcome, but its stated ground was superseded twice.** v2.1's ground ("the §12.2 conjunction that keeps the error rate at 0.05 requires both") was replaced in v2.2; v2.2's replacement invoked commensurability and is replaced again in v2.3. **The rule and its disposition are unchanged throughout** |
| **BA1, BA2, BA3** | **correct.** All three still **block a supported E2**; none was scoped, weakened or rerouted. BA1 additionally still kills the P1 cycle read when it fires **in `C_gen`** |

**Three of twelve entries were wrong, and two of the three were certified from recollection.** The
lesson is recorded rather than absorbed: **an audit row asserting that a section needed no change is
itself a claim requiring evidence**, and in v2.3 every entry above was produced by locating the text.

### 27.5 Threshold integrity for v2.3

**No threshold moved.** Every bar, cap, tolerance, cutoff, window, floor, partner count, seed and
ceiling stands at its v2 value, and §25.4's 31-row table is unaltered.

| item | status |
|---|---|
| `LB(P1) > 0.5` | **not moved** — and §13.6 defines replication success by applying **this same unchanged condition** to the confirmation, rather than by any new bar |
| `LB(P2) > 0.5` | **not moved**, still required in both contexts |
| every control bar, BA1/BA2/BA3, `p̂ ≥ 48 / 80 = 0.600`, ceilings, seeds | **not moved** |
| "a material number of systems" (§13.6 `failed replication`) | **deliberately NOT given a numeric bar.** Setting one before the two derivations exist would be inventing a threshold. The row is reached when the confirmation's own `LB(P1) > 0.5` fails **and** the per-system disagreement set is non-empty — both determined by quantities already frozen. §24 forbids the replication specialist from inventing one either |

**Recorded per MINOR-1**: §25.4's "one-sided error rate per branch" row justifies 0.05 by
"**conjunction across contexts**". For **P1** that justification was superseded in v2.2 — §12.2 step 5
and §26.4 re-derive 0.05 by **exclusivity plus a single test** — and the row is **stale as a
justification while remaining correct as a value**. §25 is retained unedited by design; the
supersession is recorded here and in §26.3.

### 27.6 What is left for a reviewer to attack in v2.3

1. **§13.6's `failed replication` row withdraws the verdict to `undecidable`.** That is the strongest
   available disposition and it is deliberate — a contested certificate is contested arithmetic, not
   weaker evidence. A reviewer may argue that two implementations disagreeing is itself a *finding*
   that deserves a verdict of its own rather than `undecidable`. §13.6 states the reasoning; the
   counter-argument is live.
2. **The absence of a numeric bar in that row** is a deliberate refusal to invent a threshold, but it
   leaves a judgement call at the moment it is exercised. §24 constrains it; it does not eliminate it.
3. **§19.3 rests on the claim that an independently written scorer is achievable within this
   campaign's resources.** It is unmeasured. If it turns out not to be, the honest consequence is that
   **P1 has no cross-check at all** and §12.2 step 4's admission becomes the whole of the story — which
   the contract must then say, rather than falling back on an insufficient factor.
4. **Rule 0's new ground is a claim about what a certificate is *about***, not a statistical claim. It
   is the right kind of ground for this asymmetry and the review endorses it, but it is philosophical
   rather than derivable, and a reviewer is entitled to test whether "there was exactly one decode"
   carries the weight placed on it. F-g, F-h and §8.6 are where that claim's evidence lives.
