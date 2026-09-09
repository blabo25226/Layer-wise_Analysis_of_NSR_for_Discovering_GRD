# C0001 — Preregistration **v2.1** (amendment to v2)

**Title**: Does a constant-collapsing canonicalizing matcher recover Hill-component matches that
GPU_RUN5's frozen exponent-aware **canonical-tree** matcher scored as misses?
A component-type-stratified test of E0, with E1' (generator support) and E2/E3 (model vs search
error) as bounded secondary parts.

| field | value |
|---|---|
| cycle | `C0001` |
| preregistration version | **v2.1** — amends and supersedes `C0001_preregistration_v2.md` (v2), which superseded `C0001_preregistration.md` (v1) |
| stage | 3 (amendment after a fresh Stage-5 audit of v2 returned 3 CRITICAL / 7 MAJOR / 10 MINOR, verdict `AMEND_BEFORE_RUN`, Gate 0 item 3 **NOT SATISFIED**) |
| legality of this amendment | v2 §28-equivalent clause (`v2:28`): amendment without a new cycle ID is permitted until Stage 4 begins. **Stage 4 has not begun** — `ls -d results/runs/gpu_runclaude1*` returns nothing, no endpoint has been computed, and no seal has been read. The primary endpoint, its stratum definitions, the aggregation order and the ladder are **unchanged**; only the control battery, two statistical sentences, the M0 characterization and the disclosure record change. |
| branch | `20260909_researce_GPU_RUNclaude1` |
| HEAD at write time | authoring began at `7f507cc` (`Re-freeze C0001 as preregistration v2 after two blocking reviews`); during authoring a concurrent commit landed the audit, so HEAD at write completion is **`7c7d96a`** (`Record the fresh v2 reproducibility audit: 3 CRITICAL, Gate 0 item 3 unmet`). Both are recorded because the v2 audit was performed at `7f507cc`. |
| commit at freeze | **the commit that introduces this file**, to be recorded in `R/manifest.json` at run start by `git log --oneline --diff-filter=A -- GPU_RUNclaude1/plans/C0001_preregistration_v2.1.md`. v2 recorded `de894b4` but was introduced by `7f507cc`; v1 recorded `94a571b` but was introduced by `7cfc0ff`. **This error class is closed by rule, not by a value** (V2-MIN-1, AUDIT-MIN-1). |
| source-run commit pinned | GPU_RUN5 inputs produced at `ddd267b07a0646140c948c1f4a92ee83e320c772`, branch `main` (`phase3/manifest.json`) |
| date frozen | 2026-09-09 |
| status | **FROZEN** on write of this file |
| campaign | `GPU_RUNclaude1` |
| new run ID | `gpu_runclaude1_c0001_<short7>`, `<short7>` re-derived from the commit at run start |
| sealed test consumed | **NONE** |
| layer estimands measured | **NONE** (§16, rule 04) |
| training performed | **NONE** |
| adaptation performed | **NONE** |

This document is a **complete standalone contract**. An implementer needs this file and nothing
else; no diff against v1 or v2 is required to execute C0001. v1 and v2 are **not edited** and remain
the historical record of what was frozen, why it failed review, and what was corrected.

Amendments after Stage 4 begins are permitted only through the deviation policy (§14) and must be
appended as dated `DEVIATION-nn` blocks, never by editing frozen text.

---

## Amendment record (v2 → v2.1)

Object of response: `GPU_RUNclaude1/reviews/C0001_v2_reproducibility_audit.md` (841 lines, fresh
Stage-5 audit of the v2 design; 3 CRITICAL, 7 MAJOR, 10 MINOR, 16 verified positives; verdict
`AMEND_BEFORE_RUN`).

**What the audit confirmed and this amendment does not touch.** All 8 prior CRITICALs
(AUDIT-CRIT-1…4, STAT-C1…C4) were re-verified as **fixed by design, none by wording**. The primary
endpoint was judged sound and an improvement on v1's. Accordingly v2.1 does **not** redesign the
primary: the endpoint definition, the H/L stratum definitions, the three-level unit hierarchy, the
aggregation order, the `ANY` reduction, the ladder cutpoints, the §7.6 reproduction gate, Part B,
Part C's discriminator and the compute ceiling are carried over unchanged. All three new CRITICALs
were confined to the **control battery** and are fixed there.

### The single root cause, stated once and applied everywhere

`src/evaluation/equation_metrics.py to_skeleton` (`:153-166`, and its refactored twin
`_to_skeleton_with_reason`) maps **every** distinct numeric constant to the **same** symbol `c`
(`:162-163`). Combined with the AUDIT-CRIT-2 fix — which requires the **infix** representation on
**both** sides of every comparison — this has three consequences v2 never stated:

1. **M0 is not a string matcher.** With infix on both sides, `parse_system` folds `-1 * 0.3968 * x_0`
   into `-0.3968 * x_0` *before* M0's exponent-aware skeleton is formed. M0 is a
   **canonical-prefix, constant-collapsed, exponent-aware tree matcher**. v2 called it "the frozen
   **string** matcher" throughout; every such phrase is corrected in v2.1, and every claim that
   depended on M0 being string-based has been re-derived (see the row for V2-CRIT-3 below).
2. **M3 cannot prove affine decomposition.** `a·A/(K+A) = a − a·K/(K+A)` is not an identity once
   `a`, `K` and `a·K` are all the single symbol `c`. Leaving `a*K` unfolded gives a byte-identical
   skeleton.
3. **M3 is not a superset of M0.** Under `sympy.apart` the audit measured M0 3/20 vs M3 0/20. Set
   inclusion `M0 ⊆ M1 ⊆ M3` is **false as a mathematical statement** and is removed from every
   argument in v2.1.

### CRITICAL resolutions

| finding | v2 text superseded | v2.1 resolution |
|---|---|---|
| **V2-CRIT-1** — PC2b's gate `M3 ≥ 76/80` is unachievable by construction (measured 0/28 components, 0/80 systems; independently reproduced here as 0 matches on every numerically-verified eligible instance). Gate A→B (iii) would fail **deterministically**, burning the full CPU budget to report `undecidable`. | `v2:709` PC2b threshold `≥ 76/80`; `v2:1152` Gate A→B (iii) inclusion of PC2b; JSON `PC2b.gating: true` | PC2b is **retained, `gating: false`, reclassified** from "sensitivity of M3" to **`m3_affine_decomposition_limitation`**, a `descriptive` instrument-limitation measurement with a **frozen expected value of 0 matches on every eligible instance** (§7.7). It is **removed from Gate A→B**. Its former diagnostic role — demonstrating M3 sensitivity to an E0-disclosed mechanism — is **replaced by PC4** for instrument capability, and is declared **unfillable** for the affine mechanism itself: see the scope restriction in §1.3. A non-zero PC2b value is a harness-difference `DEVIATION`, not a finding about E0. |
| **V2-CRIT-2** — PC3b's gate `≥ 58/60 NON-match` is failed by a faithful implementation (measured 50/60; all 10 failures R08, where the swapped pair occurs only inside the commutative product `x_0 * x_1`, so the swap is a **no-op** and M3 is *correct* to match). No eligibility requirement; v2 had applied exactly this amendment to PC3a (MIN-9) and omitted it for PC3b. Satisfaction also depended on an **unspecified implementation choice**. | `v2:712` PC3b threshold `≥ 58/60`; `v2:1153`; the unspecified swap rule | The swap rule is **frozen deterministically** (first eligible `(component index, variable pair)` in lexicographic order, §7.7) and an **eligibility filter** is added: a swap is eligible only if verified to **change the function**. Threshold is restated as **≥ 95% of the realized eligible set** — the same form PC3a already used. Reproduced here under the frozen rule: **eligible 60/60, NON-match 60/60**; under the audit's fixed-choice rule: eligible 50, NON-match 50/50, 10 ineligible no-ops, all R08. The frozen rule dominates: it covers all 60 dim ≥ 2 systems instead of 50. |
| **V2-CRIT-3** — **no positive control exists for the gain indicator.** `M0 scores 170/170 on PC2a`, so v2's claim that PC2a exercises structure "which M0 cannot match" (`v2:575`) is **false**, and E0's flagship disclosed mechanism (P4) is already absorbed by M0. **Every** control in v2 yields `gain = 0`. A primary of `K = 0` would be indistinguishable from an instrument that cannot produce a gain at all — the exact failure `v2:210-212` says the battery exists to exclude. The primary endpoint was therefore **uninterpretable at its predicted value**. | `v2:575`; `v2:694-720` (the whole battery); `v2:210-212`; `v2:1152` PC2a hard threshold; §7.3's L-stratum prediction and its stated basis | Four changes. **(a) PC4 added** — a preregistered **gain-indicator positive control**: each truth component rewritten by `sympy.together`, injected as a synthetic candidate and scored through the **same** `formula_metrics` / `symbolic_recovery` / `gain` code path as the real measurement (§7.7, §7.10). Independently reproduced here: eligible 170/170, **M0 40/170, M3 140/170, gain 100/170, of which 100 in stratum H and 0 in stratum L**, contributed by 6 of 8 families. **Hard-abort gate** with thresholds and consequences in §7.7 / §10.1. **(b) PC2a is reclassified** from a sensitivity control to a **harness-identity verification**, recorded `short_circuited: true` with an empty non-short-circuited subset, gating only on the reproduction of both known values (M0 170/170 **and** M3 170/170). **(c) `v2:575` is withdrawn**: M0 *does* match the P4 rewrite, 170/170. **(d) the L-stratum gain prediction is re-derived** from **`> 0`** to **`0`**, because its only stated basis was the now-false claim that M0 cannot match the P4 rewrite; the re-derivation is recorded, not silently dropped. |

### MAJOR resolutions

| finding | v2.1 resolution |
|---|---|
| **V2-MAJ-1** — v2 asserts three times (`v2:409`, `v2:620-623`, `v2:1478`) that `_approximately_equivalent` and the `:205` fallback do not run. **They always do**: the return dict at `equation_metrics.py:207-212` is eager, so reading `["skeleton"]` still executes the whole equiv block, including a 10 s `_timed_simplify` at `:200` on the un-skeletonized expressions. | All three sentences **corrected** (§3, §7.4, §15). The `:200 _timed_simplify` timeout is **added to the §7.5 failure-surface list**. Citations corrected: `:72-73` → `:84-85` (`_approximately_equivalent`'s grid), `:38-45` → `:36-42` (`_time_limit`'s off-main-thread no-op). The cost model is corrected in §11.1: the eager block **is inside** the measured 655 ms/candidate, so the compute basis is unaffected and remains an upper bound. What survives unchanged: `["skeleton"]` is finalized at `:187-193` strictly before the equiv block, data flow is one-directional, and the grid is non-random — so the M3 pinning and the determinism conclusion stand. |
| **V2-MAJ-2 / V2-MAJ-7** — the working tree calls `skeleton_equivalence_with_reason`, not the pinned `symbolic_recovery(...)["skeleton"]`, with no equivalence test; `to_skeleton` and `symbolic_recovery` were **refactored**, not merely extended; and this happened before Gate 0 item 3 returned. | §7.4 keeps `symbolic_recovery(...)["skeleton"]` as the **definition of record** and permits `skeleton_equivalence_with_reason` as the **implementation** only under a preregistered two-part agreement test (§7.4, Gate 0 item 11): (a) 100% bit-identical agreement over the **910 synthetic control pairs** (which span matches, proved non-matches and every labeled failure surface, and contain **no candidate data**), and (b) an in-pass **1-in-100 deterministic double-computation census** over the real endpoint pass, reported as `m3_implementation_agreement` with a frozen requirement of 100%. §17's "extended, not modified" discipline is **extended to `src/evaluation/equation_metrics.py`**. Gate 0 item 1 requires the tree committed or fully explained in the manifest. |
| **V2-MAJ-3** — the designated interval of record (two-stage bootstrap percentile) is exactly **[0, 0]** at the predicted `K = 0`, so §9.5 item 1's mandated sentence would report an evidential upper bound of 0.0000 — licensing what rule 01 item 8 forbids. | §7.1 and §9.2 **freeze** that at `K = 0` the bound of record is interval **(c)**, the 8-cluster family-level Wilson, `0/8 → [0, 0.3244]`. §9.5 item 1 now has **two verbatim variants**, one for `K = 0` and one for `K ≥ 1`, and the `K = 0` variant **states that no percentile interval is reportable and that the power statement is the substantive content**. A frozen prohibition is added: **no bootstrap percentile upper bound of 0 may be reported as an upper bound anywhere in this cycle.** |
| **V2-MAJ-4** — the effect size of record (0.0525, a per-`(component, cell)` rate over `2040 = 170 × 12`) is used against an `ANY`-over-12 endpoint, the cross-reduction comparison `v2:281-284` explicitly forbids. | §1 and §7.3 **restate** it: the quantity of record is **M0's `ANY`-over-12 reduced component rate, whose admissible range for the same 107 matches is [0.053, 0.629]** (STAT-M1); **0.0525 is used explicitly and only as the arithmetic lower bound of that range**, the 12-cell coincidence is named, and the power table is computed at that lower bound because a larger true `p` yields more power — the conservative direction for a power statement. |
| **V2-MAJ-5** — the firewall rationale invokes GPU_RUN5's "hashing = the test-open event" doctrine, but `gpu_run5_phase4.py:118-119,151-152` already hashed `sealed_official_test.json` **pre-ledger**, and its digest `2860d829…` is the very hash v2 §2.4 records for the "unspent clean seal". Also **7** sealed files exist, not 3. | §2.4 is rewritten: the sealed inventory is **enumerated at run time from the ledger plus a name-only filesystem census**, never hardcoded (7 files found, 2 with ledger entries, 5 without); v2.1 **adopts the strong doctrine for C0001's own conduct** and records that the campaign's history contains a weak-doctrine event C0001 did not cause; and the phase-4 seal's status is **restated precisely** — see §2.4a. The phrase "UNSPENT — the campaign's only clean seal … MUST NOT be touched / never touched" is **withdrawn as imprecise**. |
| **V2-MAJ-6** — `sealed_paths_read` is not a computed guarantee: the instrumented opener is a **sanctioned wrapper**, not an interception, so any direct `open`/`json.load(open(...))`/`np.load`/`pandas.read_*` is invisible to it. | §2.4 items 3–5 **preregister the interception**: a `sys.addaudithook` installed for the entire duration of Parts A/B/C that **raises** on any `open` whose resolved path matches `sealed*` or lies under a GPU_RUN5/GPU_RUN4 run root without being on the allowlist; a requirement that the guarded opener be the **sole** path by which candidate or truth files are opened in C0001 modules; a **test that a direct `open()` on a sealed path from inside `src/gpu_runclaude1/` raises**; and an **AST test** over every C0001 module forbidding un-guarded file-read call sites. `sealed_paths_read` is downgraded in wording from "records every path C0001 opens" to exactly what the hook guarantees. |
| **Monotonicity is not guaranteed** (M0 3/20 vs M3 0/20 under `apart`). | Every text assuming `M3 ⊇ M0` is removed (§7.5, §9.4 item 4, §7.8 A2-S2, §18.1). §9.4's multiplicity argument is **re-derived without inclusion**: the primary is a **single conjunction indicator**, so exactly one test is performed and no cascade multiplicity arises. The monotonicity audit is **demoted to a reported, non-gating diagnostic** with a proof that violations cannot affect the primary (the primary requires `m0_any = 0`, so any component with `m0_any = 1` contributes 0 to the numerator by definition and M3's behavior there is irrelevant). The v2 `> 1% ⇒ CRITICAL ⇒ undecidable` tripwire is **removed** as a second deterministic-burn hazard, and the `≤ 0.1%` prediction is **withdrawn** as unfounded. **Code is forbidden from assuming inclusion** (§7.4). |
| **Stale `ModuleNotFoundError` claim** (V2-MIN-2) | Dropped. `pytest.ini` already carries `pythonpath = .` and `GPU_RUN5/tests`; 124 tests collect clean with zero errors; the default suite is **301 passed / 1 skipped**. `research_state.md` §8 defect 1 already records that the claim did not reproduce. v2 §2.4 item 6 presented an already-applied fix as pending; §2.4 item 7 of v2.1 records it as **done**. |

### MINOR resolutions (all folded into this pass)

| finding | v2.1 resolution |
|---|---|
| V2-MIN-1 | `commit_at_freeze` closed by rule (header row), not by a value. |
| V2-MIN-3 | Gate 0 item 2's "(4 tests)" corrected to **6** (both tests in `test_gpu_run5_firewall.py` match on the filename, including `test_nonfinite_values_are_sanitized_for_strict_json`), and the gate is restated as "all selected tests green" rather than an exact count. |
| V2-MIN-4 | §2.4 records that `test_gpu_run5_phase8.py:542`'s ordering assertion is a **lexical** first-occurrence check on source text, not a runtime ordering check; the C0001-specific firewall test of §2.4 item 5 is the real protection. |
| V2-MIN-5 | `LANSR_SYMPY_MAX_NODES=200` for PC0-CAS must be set **in the environment before interpreter start**, in a dedicated subprocess: `ted.py:15` reads it at import and binds it by value into `formulas.py:13`, so in-process monkeypatching leaves `formulas.py:434` at 40 and PC0-CAS would silently re-measure 28/80. Frozen as a subprocess invocation with an asserted `SYMPY_MAX_NODES == 200` echo. |
| V2-MIN-6 | Bootstrap generator named: `numpy.random.default_rng(20260909)`, **one** generator stream, draw order **families first, then systems within each drawn family**, 10,000 resamples, percentile method. |
| V2-MIN-7 | Commutation-orbit enumeration order defined (§8.2 step 5). |
| V2-MIN-8 | `R/phase0/partA_cost_calibration.json` restricted to **per-family aggregates** (mean/median/p95) and failure-label counts; **per-candidate timings are forbidden** (wall time is a side channel on the match indicator: a proved match exits at `equation_metrics.py:189`, a non-match additionally runs `_timed_equals` at `:190`). |
| V2-MIN-9 | `ComponentCountMismatch` classified **once**: it is a **decided non-match (`proved_different`)**, never `could_not_evaluate`, because component counts are observed facts and not failed evaluations. It is therefore **excluded** from the `could_not_evaluate_rate` numerator. Empirically inert on this corpus (diagonal for all 47,987; 0 of the 2,235 stored component hits under a count mismatch). |
| V2-MIN-10 | Hard VRAM cap added: `torch.cuda.set_per_process_memory_fraction` sized to 5.5 GiB of the 8,192 MiB device, so the ceiling is an allocator cap and not only a ≤ 10 s tripwire. |
| audit §5.4 | The `StrataFrozenToken` write-before-match capability gate is **frozen in this document** (§7.2 step 4), not left incidental to one implementation. |
| audit §2.2 | A2-S1's predicted L-stratum contrast is structurally suppressed if the 107 sit in L; recorded in §7.8 alongside the re-derived prediction of 0. |
| audit §5.3 | §18.1 records that cutting M2 leaves E0's affine-decomposition mechanism with **no** instrument. |
| audit §12.1 filename | §12.1 now names the audit file by its actual path, `GPU_RUNclaude1/reviews/C0001_v2_reproducibility_audit.md`, plus `C0001_v2.1_reproducibility_audit.md` for the narrow re-audit. |
| audit item 12 / §0.4 | `|H| = 130`, `|L| = 40` and the full family/dimension breakdown are recorded in §0.3 as auditor-disclosed prior information, and §7.3's stratification prediction is **downgraded from blind to partly derivable** — see §0.4. |

### What v2.1 declines, with reasons

| declined | reason |
|---|---|
| Re-deriving PC2b's threshold from a train-split measurement (the audit's option (b) for V2-CRIT-1) | The obstruction is **algebraic, not sample-dependent**: constant collapsing destroys the affine identity for every instance in every split. A train-split measurement would return 0 there too and would spend compute to re-derive a structural fact. Option (a) — non-gating documented limitation plus an explicit scope restriction — is preferred, cheaper, and more honest. |
| Cutting PC2b entirely | It costs ~28 comparisons (≈ 20 s) and it is **informative on failure**: a non-zero value proves the harness differs from two independent measurements of the same construction. Kept, non-gating. |
| Reinstating M2 (CAS with constants) to give the affine mechanism an instrument | Rule 06. Fixing `SYMPY_MAX_NODES` projects ≈ 66 CPU-core-hours against a 24 core-hour ceiling, for a **secondary**. The consequence — E0's affine mechanism has no instrument in this cycle — is stated as a scope restriction (§1.3) rather than bought with a ceiling breach. Routed to `hypothesis_tree.md`. |
| Making PC4 the primary endpoint's mechanism | PC4 is an **instrument-capability** control on synthetic candidates. It is not evidence that any real beam candidate carries a common-denominator rewrite. Conflating the two would be exactly the rule-03 error the campaign is guarding against. |
| Editing `research_state.md` §8 to add the phase-4 pre-ledger-hashing defect (audit's amendment item 9) | Out of scope for this task, which permits writing `C0001_preregistration_v2.1.md`/`.json` only. The finding is recorded in §2.4a of this document and listed in §20 as a required follow-up so it is not lost. |
| Any change to the primary endpoint, strata, aggregation order, ladder cutpoints, seeds, ceiling, or Part B/Part C design | The audit judged them sound. Rule 01 item 3. |

---

## Supersession

**This document supersedes `C0001_preregistration_v2.md` (v2) and `C0001_preregistration.md` (v1) in
their entirety.** Neither may be used to plan, implement, execute or interpret any part of C0001.
Both are retained unmodified as the historical record.

### Why v2 existed (carried forward, unchanged)

1. **A motivating finding was retracted.** `GPU_RUNclaude1/analyses/C0001_RETRACTION_neg_finding.md`
   establishes that v1's P6 ("`neg`-normalization raises the component-level truth-in-beam rate from
   0/2040 to 107/2040") was an artifact of comparing a **prefix**-derived truth skeleton against
   **infix**-derived candidate skeletons. The "raw 0/2040" baseline never existed. 107/2040 is
   GPU_RUN5's **already-published** value, stored at
   `results/runs/gpu_run5_20260823_ddd267b0/phase3/beam_groups.json:component_true_exponent_aware_skeleton_in_beam`.
   **E0 lost its component-level empirical support.** E0 remains live — no one has run a
   canonicalizing constant-collapsing matcher on this corpus — but it must be tested against the
   *correct* published baselines (system 0/960, component 107/2040), never against zero.
2. **Two independent Stage-3 reviews returned blocking verdicts**, 8 CRITICAL between them:
   `reviews/C0001_statistical_review.md` (4 CRITICAL, 13 MAJOR, `AMEND_BEFORE_FREEZE`) and
   `reviews/C0001_reproducibility_audit.md` (4 CRITICAL, 9 MAJOR, `AMEND_BEFORE_IMPLEMENTATION`).
3. **The corrected v1 design breached the compute ceiling** (≈ 66 vs 24 CPU-core-hours). v2
   re-scoped rather than requesting an increase.

### Why v2.1 exists

A fresh Stage-5 audit of v2 (`reviews/C0001_v2_reproducibility_audit.md`) found the v2 **control
battery** structurally unable to validate the endpoint it exists to validate: two of its thresholds
were unachievable by construction, and **none** of its controls could produce a non-zero value of
the primary's own indicator. Gate A→B would have failed deterministically and the cycle would have
spent its full CPU budget to report `undecidable`. Gate 0 item 3 of v2 was therefore **NOT
SATISFIED**, which blocks the run under v2's own gate and under rule 07.

Finding-ID convention: `STAT-Cn`/`STAT-Mn`/`STAT-mn` = `reviews/C0001_statistical_review.md`;
`AUDIT-CRITn`/`AUDIT-MAJn`/`AUDIT-MINn` = `reviews/C0001_reproducibility_audit.md`;
`V2-CRITn`/`V2-MAJn`/`V2-MINn`/`V2-OKn` = `reviews/C0001_v2_reproducibility_audit.md`;
`RETRACT` = `analyses/C0001_RETRACTION_neg_finding.md`; `R1` = `research_state.md` §8b standing rule.

### What v2.1 keeps unchanged from v2

The 16 v2-verified positives and the 33 v1-verified positives are all retained. Explicitly retained
because reviewers endorsed them by name: the **system as the resampling cluster** and the stated
reason; the **`ANY`-over-cells reduction** as the generation-coverage estimand and as the
anti-conservative direction for a null-shaped claim; the **degenerate-paired-test warning**; the
**prior-information ledger** and its mandatory machine-readable disclosure field; §9.5's wording
constraints; Part B's `interval_interpretation`; **retention of invalid and failed candidates** in
every denominator; usable-candidate denominators rather than a hardcoded 50; the additive Part C
instrument with its `sum/n == −mean_CE` regression test; the `cell_input_payload_sha256` identity
protocol (the best-verified machinery in the cycle: 10 distinct payloads per system in 80/80); the
crash-loop rule; the §7.6 exact-reproduction gate; and the rule-03 30-field record schema with the
generation-coverage / oracle-candidate / selected-candidate distinction intact.

---

## 0. Prior information disclosed before freeze (rule 01 item 9)

This cycle is **not blind**, and v2.1 is **less blind than v2**: the Stage-5 audit of v2 and this
amendment measured further quantities on the endpoint corpus, all of them **truth-side or
synthetic** (truth vs rewritten truth). Everything observed before this freeze is declared here so
that no downstream artifact can present it as a C0001 discovery.

### 0.1 Published GPU_RUN5 values that are comparators, not findings (R1)

| # | quantity | value | source | role |
|---|---|---|---|---|
| **P0a** | `true_exponent_aware_skeleton_in_beam` (system level) | **0/960 cells = 0.0000**, and 0/120 in every family | `phase3/beam_groups.json` | comparator `C-M0`; the published claim whose interpretation is under test |
| **P0b** | `component_true_exponent_aware_skeleton_in_beam` | **107/2040 = 0.0525**; by family R01 0/120, R02 0/120, R03 0/240, **R04 56/240**, R05 0/240, R06 0/360, **R07 17/360**, **R08 34/360** | `phase3/beam_groups.json`; all eight counts re-verified exactly by the v2 audit | comparator `C-M0c`. **This is the frozen matcher's own value.** Not an artifact, not a discovery, not a floor at zero. |
| **P0c** | stored per-candidate fields | `exponent_aware_skeleton_exact` = 0.0 for all **47,987**; `canonical_exact` = 0.0 for all 47,987; `skeleton_exact` = 0.0 for all 47,987; `component_exponent_aware_skeleton_exact` = 1.0 for **2,235 of 101,963** component comparisons | v1 audit §4; every figure re-verified by the v2 audit | the only non-degenerate signal in the stored data; Gate A→B requires its exact reproduction |
| **P0d** | deduction from P0a + P0b | R01 and R02 are 1-dimensional, so a component match *is* a system match there; 0/120 at system level therefore forces **0 of the 107 component matches in any dim-1 system**. All 107 lie in the 1,800 dim ≥ 2 component-cells (rate 0.0594 there, 0.0000 in dim-1). | STAT-C1, verified from `phase2/validation.json` | a published-data deduction, not a C0001 result |

**Retracted and unavailable as evidence** (`RETRACT`): that the frozen matcher scored 107 real
component matches as misses; that GPU_RUN5's component-level measurement was biased to zero by the
matcher; that the `component_exact_loss = 0.0` floor was matcher-induced. v1's P5 and P6 are
withdrawn as *findings*. **No v2.1 element depends on a 0/2040 baseline** (verified by `grep`).

### 0.2 Truth-side facts (no outcome content)

| # | quantity | value | source | consequence |
|---|---|---|---|---|
| P1 | GRN truths `teacher_valid` | 240/240 train, 80/80 validation; prefix round-trip exact 80/80 and 240/240 under GPU_RUN5's `\|` ↔ `,\|,` normalization | Stage 1; AUDIT-OK-7 | **E1 (raw expressibility) REFUTED. Not re-tested. Cited only.** |
| P2 | zero-probability operators under the checkpoint's persisted generator | `abs, sqrt, log, exp, arcsin, cos, arccos, tan, arctan, pow3, sub, div` all exactly 0.0 | Stage 1 addendum | fixed constraint, not an endpoint. **`inv`, `mul`, `add` all have non-zero generation probability** — the basis for PC4's within-support justification (§7.7). |
| P3 | GT teacher token length, validation | min 19, median 47, mean 45.7, max 80 | Stage 1 | Part C length policy (§8.3) |
| P4 | `neg` node in truth exponent-aware skeletons vs candidates | truths **prefix-derived** 960/960; candidates **infix-derived** 1,541/47,987 = 3.2% | `C0001_exploratory_neg_canonicalization.md`, corrected by `RETRACT` | **These two counts come from different derivation paths and must never be differenced.** What survives is the *encoding* fact: the GRN generator writes decay as `-1 * k * x` while ODEFormer must use a signed constant, because `sub` and `div` have exactly zero generation probability. **v2.1 correction (V2-CRIT-3): this asymmetry is fully absorbed by M0 in the mandated infix configuration (Q12b: M0 = 170/170 on the PC2a rewrite). It is not a matcher defect and cannot produce a gain.** |
| P5 | nested `pow2,pow2` (realized Hill exponent 4) | 39/170 validation components, 24/80 systems; 130/510 train components | v1 §0.2, AUDIT-OK-14 | E1' is LIVE; defines PC3a's eligible set |
| P6 | train-split non-identity unary count per truth component | 80/510 components (15.69%) and 60/240 systems (25.0%) exceed `max_unary_ops_per_dim = 3` | v1 §0.1 | Part B has a non-degenerate effect |
| P7 | truth token census (per 960 validation cells) | `CONST` 6120, `mul` 4920, `add` 4080, `x_0` 2760, `pow` 2376, `2` 2376, **`neg` 2040**, **`inv` 1680**, `x_1` 1680, `x_2` 480 | exploratory note | basis for v2's §7.3 predicted stratum sizes (now superseded by the measured Q16) |
| P8 | corpus shape | R01 R02 dim 1, R03 R04 R05 dim 2, R06 R07 R08 dim 3; 10 systems each; 20/30/30 systems, 170 components | `phase2/validation.json` | **dimension is perfectly confounded with family** (STAT-C2) |
| P9 | stored candidate fields | no `symbolic_equivalent` field; no log-probability or score field of any kind | v1 §0.1, AUDIT-OK-6 | Part A must recompute equivalence; Part C must re-encode and re-score |
| P10 | candidate-set completeness | 951 cells with 50, 6 with 49, 2 with 48, 1 with 47 → 47,987; shortfall 13 | v1 §0.1 | denominators are *usable candidates*, never a hardcoded 50 |
| P11 | cell-grid structure | one initial condition and one source trajectory per system; 12 cells → **10** distinct `observations["input"]` payloads; the three clean `(σ=0, ρ=0)` cells are **byte-identical across bundles in 80/80** systems, differing only in decode seed; `input_trajectory_checksum` takes 80 distinct values over 80 systems and is **constant across each system's 12 cells** | STAT-C3, STAT-M12; **re-verified exactly by the v2 audit over all 960 cell files** | every rate is conditional on one IC per system; the v1 fairness check was vacuous |

### 0.3 Quantities measured on the endpoint corpus before this freeze

These were measured **before** this freeze and are disclosed prior information. Several are
control-battery outcomes, which makes those controls **verifications of a known value** rather than
blind checks; each is labeled as such and each remains informative, because a divergence proves the
C0001 harness differs from the measuring harness.

| # | quantity | value | source | consequence |
|---|---|---|---|---|
| Q1 | **PC2a rewrite, M3 side** — rewrite every `-1 * k * x_i` to `(-k) * x_i` in all 80 truths | **M3 = 80/80 systems, 170/170 components** | v1 audit AUDIT-OK-8; v2 audit | M3 detects the P4 asymmetry. **Verification, not discovery.** |
| Q2 | **PC3a specificity of M3** — alter one realized Hill exponent | **48/48 of the eligible set correctly scored NON-match** | AUDIT-OK-8 | M3 is not over-permissive on exponent structure. Verification. |
| Q3 | **M0 exact reproducibility** via `formula_metrics(teacher_infix, candidate_formula_raw)` | **600/600** system- and component-level vectors reproduce the stored fields; 32 stored component hits in the sample, 32 recomputed | v1 audit §4 | Gate A→B is achievable *and* non-trivial. The R1-mandated positive control. |
| Q4 | **CAS self-equality**, `_sympy_components_equal(truth, truth)` with the M1 short-circuit removed | **28/80**; 52/80 exceed `SYMPY_MAX_NODES = 40` (R01 10/10, R02 10/10, R03 4/10, R04 4/10, R05–R08 0/10) | AUDIT-CRIT-3 | the CAS path answers "does a GRN truth equal itself?" with *no* for 52/80. Reported as an instrument fact (PC0-CAS). |
| Q5 | node-cap exceedance on real pairs | **1,652/3,000 = 55.1%** silently return `0.0, None`; R01 0.0%, R02 0.0%, R03 33.0%, R04 14.5%, R05 92.9%, R06 100.0%, R07 100.0%, R08 100.0% | AUDIT-CRIT-3 | M2 is structurally incapable of matching R05–R08. Why M2 is cut. |
| Q6 | Part A throughput, **v1's M1+M2+M3 cascade**, 150 real candidates | mean 795 ms/candidate, median 604 ms | AUDIT-MAJ-4 | **superseded as the compute basis by Q17.** |
| Q7 | truth-side CAS node totals | min 10, median 25, mean 26.2, max 48 (R07 median 48) | AUDIT-CRIT-3 | a combined cap ≥ 200 covers the observed range |
| Q8 | prefix round-trip separator convention | raw equality 20/80 (1-D only); **80/80** under `\|` → `,\|,` | AUDIT-MAJ-7 | Part C's audit must normalize or it self-aborts |
| Q9 | hardware, measured | GPU 0: 8,192 MiB total, 629 MiB used, 7,154 MiB free, 49 °C; disk 117 G free; RAM 60 G total / 52 G available | AUDIT-MIN-6 | Gate 0 item 6 is satisfiable |
| Q10 | `phase3/cells/` contents | exactly **960** files, all `*_validation_*`, **0** containing `test`, 960 containing `validation`; `all_candidates.json` split values `{validation: 47987}` | AUDIT-OK-3; re-verified V2-OK-12 | the Part A glob cannot reach a seal |
| Q11 | statistical constants at n = 80 | Wilson k=0 [0, 0.0458], k=1 [0.0022, 0.0675], k=2 [0.0069, 0.0866], k=3 [0.0128, 0.1045], k=4 [0.0196, 0.1216], k=8 [0.0515, 0.1851]; one-sided 95% at 0/80 = 0.0327; rule of three 0.0375; smallest n tolerating 1 hit under a 0.05 bound = 110, 2 hits = 142; family-clustered 0/8 = **[0, 0.3244]**; critical ICC = **0.011** | STAT §1.1–§3 | governs the demoted system-level secondary A2-S3 |
| **Q12** | **PC4 gain-indicator positive control** — every truth component rewritten by `sympy.together(sympify(component))`, injected as a synthetic candidate, scored through the endpoint's own `formula_metrics` / `symbolic_recovery` / `gain` path | **eligible 170/170** (every rewrite is textually non-trivial); **M0 = 40/170**, **M3 = 140/170**, **gain = 100/170**; **gain in stratum H = 100, gain in stratum L = 0**; per-family gain R01 0, R02 10, R03 20, R04 10, R05 0, R06 30, R07 20, R08 10 (**6 of 8 families contribute**) | v2 audit V2-OK-4 (total 100/170); **independently reproduced by this amendment**, which additionally measured the H/L and per-family split | **The gain indicator can fire, and it fires exactly where the primary measures (stratum H).** PC4 is therefore a **verification** of a known value and a **hard-abort gate** (§7.7, §10.1). |
| **Q12b** | **PC2a, M0 side** — the same P4 rewrite, scored by M0 | **M0 = 170/170 components, 80/80 systems**, hence **gain = 0/170 by construction** | v2 audit V2-CRIT-3 | E0's flagship disclosed mechanism is **already absorbed by M0**. `v2:575`'s "which M0 cannot match" is **withdrawn**. PC2a is reclassified as a harness-identity verification with `short_circuited: true` and an empty non-short-circuited subset. |
| **Q13** | **PC2c / PC2d under a frozen tree-level commutative permutation** (reverse the argument order of every n-ary `add`, resp. `mul`, node bottom-up, re-serialize to infix, each rewrite verified equivalent by `numeric_equivalent(n_points=32, seed=0)`) | `add`: **eligible 170/170, M3 = 170/170, 0 unverified rewrites**. `mul`: **eligible 170/170, M3 = 170/170, 0 unverified rewrites** | measured by this amendment | The audit's crude "PC2c-like / PC2d-like" proxies (M0 = M3 = 40/170) were **implementation artifacts of an unverified rewrite**, not matcher failures. A precisely specified, equivalence-verified permutation is fully achievable, so PC2c/PC2d can gate safely at the component level. |
| **Q14** | **PC2b affine decomposition** | **M3 = 0 matches on every eligible instance.** Audit's construction: 0/28 components, 0/80 systems, under an *unverified* rewrite. This amendment's construction, restricted to instances verified equivalent by `numeric_equivalent`: **0/1**. Both agree at zero. | v2 audit V2-CRIT-1; reproduced here | **M3 cannot prove affine decomposition under constant collapsing.** PC2b becomes a non-gating documented limitation and the basis of the §1.3 scope restriction. |
| **Q15** | **PC3b permuted-variable specificity** | Under the **v2.1 frozen rule** (first eligible `(i, x_j, x_k)` in lexicographic order): **eligible 60/60 systems, NON-match 60/60, 0 ineligible**. Under the audit's fixed-choice rule (two lowest indices in the first multi-variable component): **eligible 50, NON-match 50/50, ineligible no-ops 10 — all R08**, where the swapped pair occurs only inside the commutative product `x_0 * x_1`. | v2 audit V2-CRIT-2 (50/60); reproduced here, and the frozen rule measured here | The frozen rule dominates: full coverage of all 60 dim ≥ 2 systems and 100% correct specificity. **Verification.** The general hazard the audit demonstrated (`symbolic_recovery("1.0*x_0 + 2.0*x_1", "1.0*x_1 + 2.0*x_0")["skeleton"] == 1.0`, an eligible swap M3 wrongly matches because constants collapse) **does not materialize on this corpus** but is real; the eligibility census will detect it if a reimplementation differs. |
| **Q16** | **the H/L stratum census** — computed by exactly the path §7.2 prescribes | **`\|H\| = 130`, `\|L\| = 40`** of 170. H by family: R01 10, R02 10, R03 20, R04 10, R05 20, R06 30, R07 20, R08 10. **L by family: R04 10, R07 10, R08 20** (R01, R02, R03, R05, R06 have **zero** L components). H by dimension: 1→20, 2→50, 3→60. L by dimension: 2→10, 3→30. Agreement with the independently-derived stored `structure.component_flags[i].variable_denominator_form`: **170/170**. | v2 audit V2-OK-1; reproduced 170/170 by this amendment | `\|H\| = 130` is inside v2's predicted 130–145 (at the lower boundary); `\|L\| = 40` is inside 25–40 (at the upper boundary). No §7.2 fallback fires; `\|H\| ≥ 100` so `underpowered_bound_only` does not fire. **`C = ceil(0.02 × 130) = 3`.** Realized ladder, power and OC tables are frozen in §7.3/§9.3 rather than left to be computed. **See §0.4 for the blinding consequence.** |
| **Q17** | **Part A throughput in the v2.1 configuration** — M0 + M1 + M3, 120 real candidates, 15 per family, `random.seed(20260909)`, `formula_metrics` + `compare_formulas(skip_cas=True)` + per-component `symbolic_recovery` | M0 mean 45 ms, M1 mean 16 ms, M3 mean 594 ms; **M0+M1+M3 mean 655 ms, median 608, p95 1480, max 1992**; per family R01 770, R02 226, R03 794, R04 338, R05 631, R06 906, R07 927, R08 647 ms; **projection 8.73 single-core-hours for 47,987** | v2 audit V2-OK-8 | **the measured compute basis of record** (§11), replacing Q6's 10.60 core-h upper bound. The eager `equation_metrics.py:195-212` equiv block **is inside** this measurement (V2-MAJ-1), so the figure needs no upward correction. |
| **Q18** | RAM | `phase3/all_candidates.json` (174 MB on disk) loads to **0.53 GiB** peak process RSS; 6 workers ≈ 3.2 GiB against 52 GiB available | v2 audit V2-OK-9 | the 6-process plan is safe |
| **Q19** | sealed-artifact inventory | **7** files named `sealed*` under `results/runs`, in **3** run directories; **2** covered by a test-open ledger (`phase8/test_open_ledger.json`, `open_count: 1`, `status: complete`), **5** with no ledger entry | v2 audit V2-MAJ-5; re-verified by name-only census here | v2 §2.4 listed 3. §2.4 of v2.1 enumerates at run time instead of hardcoding. |
| **Q20** | test suite | `pytest GPU_RUN5/tests --collect-only -q` → **124 collected, 0 errors, bare**; the Gate 0 item 2 selector collects **6** tests, not 4; default suite **301 passed / 1 skipped** | v2 audit V2-MIN-2/MIN-3; `research_state.md` §8 defect 1 | the `ModuleNotFoundError` claim is **withdrawn as stale** |

### 0.4 What is *no longer* unobserved, stated honestly

v2 §0.4 declared one quantity deliberately unobserved:

> *"The component-type stratification of GPU_RUN5's 107 published M0 component matches has NOT been
> computed, inspected, or estimated by anyone at the time of this freeze."*

**That statement is still literally true at this freeze, and it is preserved as a binding
constraint** (§7.2 step 3): the H/L split of the 107 has **not** been computed, and it must not be
computed until `R/phase1/component_strata.json` and `R/phase1/partA_ladder_realized.json` are
written and hashed. The Stage-5 auditor respected this ordering and explicitly declined to compute
it; so did this amendment.

**But the blinding claim attached to it in v2 §7.3 no longer holds, and v2.1 does not assert it.**
Computing `|H|` — which v2 §7.2 step 1 requires anyway, and which the audit performed — reveals
that **stratum L is non-empty in exactly and only R04, R07 and R08**, which are **exactly and only
the three families carrying all 107 published M0 component hits** (P0b). The correlation between
L-membership and M0 success is therefore **perfect at family resolution**, derivable from a
truth-side census plus already-published data. Two further facts sharpen it:

- v2's §7.3 prediction "at least 54 of 107 of the M0 hits lie in stratum L" is consequently **not a
  blind prediction**; it is **partly derivable**. §7.3 relabels it accordingly.
- Q12 adds that on those same three families — and only those — M0's canonical tree **absorbs** a
  common-denominator rewrite of the truth (M0 = 40/170 under PC4, distributed R04 10, R07 10, R08 20,
  which coincides with L's family distribution exactly). This is a synthetic truth-vs-truth fact
  with no candidate-outcome content, but it further narrows what an unbiased predictor could not
  have guessed.

**Frozen consequence.** The §7.3 stratification prediction is **demoted from `frozen_blind_prediction`
to `partly_derivable_prediction`** and may not be cited as evidence of foresight. It is still
recorded, because a *miss* against a partly-derivable prediction is informative about the
derivation. The **primary endpoint itself remains genuinely unobserved**: no candidate-side match
indicator has been computed by anyone, and every quantity in §0.3 is either published, truth-side,
or synthetic (truth vs rewritten truth). That is the distinction that keeps the primary
confirmatory, and it is the distinction §7.2's write-before-match ordering exists to protect.

### 0.5 Mandatory disclosure field

Every artifact carrying a Part A endpoint must carry the field `prior_information_disclosed` naming
**§0.1–§0.4 of this file** (v2.1, not v2), and the Stage-11 report must reproduce §0 verbatim in its
"Prior evidence" section. Every artifact carrying a control result must additionally carry
`control_is_verification_of_disclosed_value: true` for PC2a, PC2c, PC2d, PC3a, PC3b and PC4.

---

## 1. Frozen primary hypothesis

**H-C0001-P (primary, confirmatory).**

> **E0 does not explain the Hill-component generation failure.** Among the
> **Hill / variable-denominator** truth components of the 80 GRN validation systems, a
> canonicalizing constant-collapsing matcher (**M3**) recovers **no in-beam structural matches that
> GPU_RUN5's frozen exponent-aware canonical-tree matcher (M0) scored as misses**, at the magnitude
> E0 requires. Predicted value of the primary endpoint: **0**.

**Effect size of record (restated, V2-MAJ-4).** The quantity E0 must beat is **M0's own
`ANY`-over-12-cells reduced component rate**, which is the reduction the primary uses. For the same
107 published component matches that rate is **not identified** by the published data: its
admissible range is **[9/170, 107/170] = [0.053, 0.629]** (STAT-M1), because the 107 could be
concentrated in as few as 9 components (12 cells each) or spread over as many as 107. **v2.1 uses
0.0525 explicitly and only as the arithmetic lower bound of that range**, and states why: the
numerical coincidence `107/2040 ≈ 9/170 ≈ 0.053` arises because there are exactly 12 cells per
system and `2040 = 170 × 12`. Using the lower bound is the **conservative choice for a power
statement** — a larger true `p` gives more power, not less. **No artifact may present 0.0525 as "the
rate M0 achieves under the primary's reduction"**; §2.1 forbids that cross-reduction comparison and
this restatement is what makes the power table admissible.

This is a **null-shaped primary**, so §7.7 specifies a mandatory control battery and §9.3 a
null-credibility ladder **without which the null is uninterpretable**. Its inferential content is
**powered falsification of a stated effect size**, not an equivalence claim: at the realized stratum
size `|H| = 130` the design has **0.9991** probability of observing at least one gain if the
per-component gain rate were 0.0525 (§7.3), and the reported result of a zero observation is a bound
plus that power statement — never "the rate is zero" (§9.5).

**Falsifier.** More than `C = ceil(0.02 · |H|) = 3` Hill components showing a matcher-attributable
gain refutes H-C0001-P, means E0 operates at the component resolution that matters, requires
revision of GPU_RUN5's component-level interpretation, and routes through the replication gate
(§15). **Unsupported ≠ refuted**: 1 to 3 gains leaves H-C0001-P `unsupported` without refuting it
(§9.3).

**The one condition without which no verdict may be reported (V2-CRIT-3).** A result of `K = 0` may
be reported as **evidence against E0** if and only if the **PC4 gain-indicator positive control
passed** (§7.7, Gate A→B item (iii)). If PC4 fails, Part A is `undecidable (gain indicator not
demonstrated)` and `K` — whatever its value — may not be cited for or against E0. This is stated
again in §9.5 item 0 and in §10.3, and it must appear verbatim in the machine-readable
`verdict_scope_sentence` of every artifact carrying a ladder verdict.

### 1.1 The four competing explanations, with corrected status

| id | explanation | status entering v2.1 | decided by |
|---|---|---|---|
| **E0** | measurement/evaluator artifact — the beam contains algebraically equivalent structure that the frozen matcher scores as a miss | **LIVE, with no component-level empirical support.** v1 recorded "partially confirmed at component level (P6)"; that support is **retracted**. What is known: M0 itself already finds 107/2040 component matches and 0/960 system matches, and M0 is a canonicalizing tree matcher, not a string matcher. Nobody has run a constant-collapsing matcher on this corpus. **Now qualified by the scope restriction of §1.3.** | **Part A** |
| **E1** | raw expressibility | **REFUTED** (P1). Not re-tested. | cited only |
| **E1'** | generator-support exclusion — the truth's minimal form exceeds `max_unary_ops_per_dim = 3` | **LIVE** (P5, P6) | **Part B** |
| **E2** | prior mass / model error — the truth is in support but near-zero probability under the decoder given the trajectory | LIVE | **Part C** |
| **E3** | search error — the truth has non-negligible probability but beam-50 sampling at T = 0.1 never reaches it | LIVE | **Part C** |

E0, E1', E2 and E3 are **not mutually exclusive** and may hold on different subsets. The design
reports a **partition of the systems**, never a single winner (§10.3). No single-number "the cause is
X" claim is permitted.

### 1.2 Explicitly out of scope

- No beam-size or temperature sweep (the literature answers it).
- No novelty claim for teacher-forced GT scoring: precedented by Stahlberg & Byrne, EMNLP-IJCNLP
  2019, pp. 3356–3362, **DOI 10.18653/v1/D19-1331** (https://aclanthology.org/D19-1331/). The cycle
  report must cite it and must not claim the instrument as novel.
- No biological-causality language. Targets are synthetic Hill-type systems (rule 01 item 7).
- No equation-discovery claim from R²/NMSE (rule 03). Trajectory fit is a covariate only.
- No layer-importance claim (rule 04, §16). No representation-geometry, gradient, ablation, IOLE or
  selective-fine-tuning estimand is measured.
- No M2 / CAS-with-constants endpoint (§18.1).
- No ODEBench denominator-arity classification (v1 Part D, cut).
- **New in v2.1**: no claim about E0 acting through **affine decomposition** — see §1.3.

### 1.3 Frozen scope restriction: which E0 mechanisms C0001 can and cannot reach (V2-CRIT-1, V2-CRIT-3)

E0 names two disclosed mechanisms. Neither is testable as a *gain* by this cycle's instrument, and
v2.1 states that plainly rather than leaving it implicit.

**(M-i) The P4 encoding asymmetry — absorbed by M0, so no gain is possible.** The GRN generator
writes decay as `-1 * k * x`; ODEFormer must use a signed constant. In the mandated configuration
(infix on **both** sides, AUDIT-CRIT-2), `parse_system` folds `-1 * 0.3968 * x_0` into
`-0.3968 * x_0` **before** M0's exponent-aware skeleton is formed, so **M0 matches the rewrite
170/170 components and 80/80 systems** (Q12b). Since `gain` requires `m0_any = 0`, the gain
indicator is **identically 0 on this mechanism by construction, for every candidate, at every
cascade level**. Consequently:
- A `K = 0` primary carries **no information** about M-i. It cannot.
- What *can* be said about M-i is different and stronger: **M-i is not a matcher defect at all**,
  because the frozen matcher already handles it. v2's contrary claim (`v2:575`, "which M0 cannot
  match") is **withdrawn**. This is a reportable v2.1 finding about the instrument, sourced to Q12b,
  and it must be reported as a *disclosed prior measurement*, not a C0001 discovery.

**(M-ii) Affine decomposition of a Hill term — undetectable by any matcher in v2.1.**
`a·A/(K+A) = a − a·K/(K+A)` ceases to be an identity when `a`, `K` and `a·K` all collapse to the
single symbol `c`, so:
- **M3 cannot prove it** (Q14: 0 matches on every eligible instance, under two independent
  constructions).
- **M1 cannot prove it**: M1 is canonical-prefix *exact*, strictly stricter than M3 on this class.
- **M0 cannot prove it**: M0 canonicalizes but performs no algebraic rearrangement of this kind.
- **M2 could in principle prove it** — it is the only CAS-with-constants level, and it does not
  collapse constants — **but M2 is cut** on rule-06 compute grounds (§18.1: ≈ 66 core-hours against
  a 24 core-hour ceiling, for a secondary).

> **Frozen restriction.** *The affine-decomposition mechanism of E0 is not detectable by any matcher
> in C0001 v2.1 under constant-collapsing skeletons. C0001 can neither confirm nor falsify E0 acting
> through affine decomposition.* Any artifact reporting the primary must carry this sentence
> verbatim in `verdict_scope_sentence` alongside the §9.5 sentence, and the Stage-11 report must
> state it in its limitations section. A future cycle wanting this mechanism needs a
> **constant-preserving** CAS level with a node budget ≥ 200 and a compute ceiling that admits it;
> that is routed to `hypothesis_tree.md` as a C0002 candidate.

**(M-iii) What the primary actually tests: algebraic re-association / common-denominator rewriting.**
This is the rewrite class the instrument demonstrably *can* prove and on which the gain indicator
demonstrably *does* fire: **PC4 gives gain 100/170, all 100 in stratum H** (Q12). It is **not** one
of E0's disclosed mechanisms, and v2.1 does not pretend otherwise. Two things make it the right
class to carry the primary anyway:
1. It is **within the model's own generation support**: `inv`, `mul` and `add` all have non-zero
   generation probability under the checkpoint's persisted generator (P2), so a real beam candidate
   *can* spell a Hill component as a single common-denominator ratio, or as a re-associated sum of
   products over one denominator, where the truth spells it multiplicatively.
2. It is exactly the class where a **constant-collapsing** matcher differs from a
   **constant-collapsing canonical-tree** matcher, which is the M3-vs-M0 contrast the primary is
   built on.

> **Frozen interpretation rule.** The primary's verdict is a statement about *"the rewrite classes
> M3 can prove"*, of which PC4's class is the demonstrated member, M-i is excluded by construction,
> and M-ii is out of reach. No artifact may generalize the verdict to "E0 is false", to "the
> canonicalization makes no difference", or to any rewrite class not exercised by a passing control.

---

## 2. Statistical unit, splits, firewall

### 2.1 Units and the analysis hierarchy

| level | n | role |
|---|---|---|
| **truth component** | **170** (20 dim-1 × 1 + 30 dim-2 × 2 + 30 dim-3 × 3) | the **analysis element of the primary endpoint** |
| **parameterized system** | **80** (10 per family) | the **resampling cluster**, and the unit of the demoted system-level secondary |
| **family** | **8** (R01–R08) | the **second-level resampling cluster**; perfectly confounded with dimension (P8) |

**Cells are never a unit.** Each system has 12 cells = `noise_sigma ∈ {0.0, 0.05}` ×
`subsample_rho ∈ {0.0, 0.5}` × `bundle_index ∈ {0,1,2}`, but the true structure is (P11): **one**
initial condition and **one** source trajectory per system, **10** distinct conditioning payloads
across the 12 cells, and 12 distinct decode seeds, with the three clean cells byte-identical across
bundles in 80/80 systems. Treating cells as independent would inflate n by up to 12×.

**Aggregation order (frozen, non-negotiable): within-component over cells first, then across
components, with clustering by system and family.**

- Component-level binary endpoints: per (cell, candidate, component) indicator → `ANY` over the
  usable candidates in a cell → `ANY` over the component's 12 cells → the component-level indicator
  → aggregate across components with system- and family-clustered intervals.
- The `ANY` reduction is the **generation-coverage** estimand (rule 03) and is deliberately
  **anti-conservative for a null-shaped claim** (up to 12× inflation of the hit probability under
  independence), the adversarially correct direction. Two consequences are frozen:
  **(i) an `ANY`-over-12 rate is not comparable to GPU_RUN5's per-cell rate except at exactly zero,
  and no artifact may present them as the same quantity improved**; (ii) if any `ANY` rate is
  non-zero, the union-of-12 structure must be reported beside it.
- Continuous endpoints: per-cell value → per-system mean over usable cells → across-system interval.

**Frozen scope sentence, required on every rate in every artifact:** *"conditional on the single
initial condition per system stored in GPU_RUN5 phase 3, and on the 10 distinct conditioning
payloads its 12 cells realize."* GPU_RUN5's own P6 result (multi-IC selection, mean clustered
ΔNRMSE −0.20278, paired CI [−0.32323, −0.08233]) establishes that IC materially affects outcomes on
this corpus, so the restriction is not innocuous.

### 2.2 Target population (STAT-C2)

> The estimand's population is **Hill-type GRN truth components emitted by the R01–R08 generator
> under the frozen `configs/gpu_run5/base.yaml` settings**, of which the 170 validation components
> in 80 systems in 8 families are a realized sample. This is the **superpopulation** reading.

Because family is perfectly confounded with dimension and structure is a family-template property,
the intra-cluster correlation cannot be assumed zero. §9.2 freezes a two-interval reporting rule and
the ICC conditional. Under the alternative **finite-population** reading ("these 170 components"),
an observed 0 is exactly 0, no interval is licensed, and no bound on any wider rate may be claimed;
that reading is recorded here and **rejected as the estimand**, not left implicit.

### 2.3 Splits

| role | artifact | n | use |
|---|---|---|---|
| **train / calibration** | `phase2/train.json` | 240 systems | Part B calibration, rewrite-set development, threshold sanity. **Never contributes to any endpoint.** |
| **validation / measurement** | `phase2/validation.json` (SHA256 `f4644d1d4c30f8a3d6f0cafc8f321fb2c07e72979d8e4c42d28862376abb8f64`) | 80 systems, 170 components | all C0001 endpoints |
| **validation / measurement** | `phase3/all_candidates.json` (47,987) + `phase3/cells/*_validation_*.json` (960, verified count) | 960 cells | Part A re-scoring; Part C candidate distribution and per-cell input payload |
| **replication corpus** | `results/runs/gpu_run4_phase0_01/phase2/all_candidates.json` | 12,632 candidates, 63 ODEBench systems | §15 replication only |
| **model** | `assets/odeformer/weights/odeformer.pt`, SHA256 `56754040be5aa92ed4767fc43ee2008faa293f87c12b643e66c7df3e1623a5e8`, 464,822,385 B (verified) | 1 checkpoint | Part C forward passes only |
| **final test** | every `sealed*` artifact (§2.4, enumerated at run time) | — | **NOT ACCESSED** |

All 47,987 stored candidates are `split == "validation"` (P9), so there is **no train candidate
set**: Part A's matcher cannot be timing-calibrated or threshold-tuned on train candidates. v1
calibrated on ODEBench and was 6.2× wrong. v2.1 calibrates on a **preregistered random sample of
validation candidates, timing only** (§11.1), under the frozen constraint that no match indicator
produced during timing calibration may be aggregated, stored, printed, logged or read.

### 2.4 Test firewall (rewritten: V2-MAJ-5, V2-MAJ-6)

**Inventory is enumerated at run time, never hardcoded.** v2 §2.4 listed **3** sealed artifacts;
**7** exist (Q19). Frozen procedure, executed in Gate 0 and written to
`R/phase0/sealed_inventory.json`:

1. Read `results/runs/gpu_run5_20260823_ddd267b0/phase8/test_open_ledger.json` — a **ledger of
   digests and paths, containing no test payload** — and take its `sealed_paths` and
   `sealed_artifact_sha256` maps as the authority on **open status**.
2. Take a **name-only filesystem census** (`find results/runs -name 'sealed*'`; `stat` only, no
   read, no hash) as the authority on **existence**.
3. Every sealed artifact found by (2) and **absent** from (1) is recorded with
   `ledger_status: "no_ledger_entry"` and treated as **forbidden**, exactly as a spent seal is.
   Status unknown is not status clean.
4. Assert the census count is ≥ 7 and that the C0001 allowlist (item 6 below) intersects it in the
   empty set. A census returning fewer than 7 means a run directory moved and the assertion fails
   loudly rather than silently narrowing the guard.

At write time the census returns 7 files in 3 run directories, of which the ledger covers 2:

| artifact | ledger status | C0001 access |
|---|---|---|
| `gpu_run5_20260823_ddd267b0/phase2/sealed_test.json` (SHA256 `881f784b…64ce0`) | **SPENT**, `open_count: 1`, `status: complete`, claimed 2026-08-31, completed 2026-09-01 | **MUST NOT be read.** |
| `gpu_run5_20260823_ddd267b0/phase2/sealed_family_holdout_test.json` (SHA256 `fa8fe375…baf91`) | **SPENT** (same ledger event); a *subset* of the 80 — never independent evidence | **MUST NOT be read.** |
| `gpu_run5_20260823_ddd267b0/phase4/sealed_official_test.json` (SHA256 `2860d829…f28e070`) | **no ledger entry** — see §2.4a | **MUST NOT be touched.** |
| `gpu_run5_20260823_8cd0b6fa/phase2/sealed_test.json` | no ledger entry (abandoned run directory) | **MUST NOT be read.** |
| `gpu_run5_20260823_8cd0b6fa/phase2/sealed_family_holdout_test.json` | no ledger entry | **MUST NOT be read.** |
| `gpu_run5_20260823_fec3a894/phase2/sealed_test.json` | no ledger entry (abandoned run directory) | **MUST NOT be read.** |
| `gpu_run5_20260823_fec3a894/phase2/sealed_family_holdout_test.json` | no ledger entry | **MUST NOT be read.** |
| ODEBench 63 systems (`third_party/odeformer/odeformer/odebench/`) | not sealed | read-only, replication only; **forbidden** as adaptation / selection / hyperparameter data |

**Enforcement, frozen:**

5. **Explicit file-level allowlist**, frozen here, no directory ever passed to any reader or
   fingerprinter: `phase2/train.json`, `phase2/validation.json`, `phase3/all_candidates.json`,
   `phase3/beam_groups.json`, the enumerated 960 `phase3/cells/*_validation_*.json`,
   `phase4/fixed_grn_validation_panel.json`, `phase8/test_open_ledger.json` (status only, item 1),
   and (replication only) `results/runs/gpu_run4_phase0_01/phase2/all_candidates.json`.
   **Structural hazard named** (AUDIT-MAJ-3): `phase4/fixed_grn_validation_panel.json` is a
   directory **sibling** of `phase4/sealed_official_test.json`. The file-level grain is the whole
   protection; **any relaxation to a directory grain re-opens the hole immediately** and is
   forbidden for the life of this cycle.
6. **`scripts/ops/run_manifest.py --data-path` receives only individual files from that allowlist.
   Passing any GPU_RUN5 or GPU_RUN4 run directory — or any directory containing a `sealed*` file —
   is forbidden.** `tree_sha256` (`run_manifest.py:28`) does `rglob("*")` and byte-reads every file
   it finds; a manifest call on a run root would hash every seal.
7. **Interception, not convention (V2-MAJ-6).** v2 claimed "an instrumented opener records every
   path C0001 opens"; as designed and as built (`src/gpu_runclaude1/io_allowlist.py
   InstrumentedOpener`) that is a **sanctioned wrapper class**, so any direct `open(...)`,
   `json.load(open(...))`, `np.load` or `pandas.read_*` is invisible to it and
   `sealed_paths_read: []` would again be a **discipline claim, not a guarantee**. Frozen
   replacement, all four parts required:
   a. **A `sys.addaudithook` is installed for the entire duration of Parts A, B and C** (and for the
      replication run), before any C0001 module is imported. It inspects the `open` and
      `os.open` audit events and **raises `SealedPathAccessError`** when the resolved path's
      basename matches `sealed*`, **or** when the resolved path lies under any
      `results/runs/gpu_run5_*` or `results/runs/gpu_run4_*` directory and is not on the item-5
      allowlist. Writes under `R/` and reads of repository code, configs and the checkpoint are
      unaffected.
   b. **The guarded opener is the sole path by which candidate or truth files are opened in C0001
      modules.** No module under `src/gpu_runclaude1/` (nor any C0001 entry script) may contain a
      file-read call site whose path does not come from the allowlist API.
   c. **Test (must be green at Gate 0):** a direct `open(<a sealed path>)` executed **from inside
      the `src/gpu_runclaude1` package** raises `SealedPathAccessError`. The test constructs the
      path by name from the census and never reads it.
   d. **AST test (must be green at Gate 0):** a static check over every module in
      `src/gpu_runclaude1/` and every C0001 entry script asserts there is **no** call to `open`,
      `io.open`, `json.load`+`open`, `numpy.load`, `numpy.loadtxt`, `pandas.read_*`, `Path.read_text`,
      `Path.read_bytes` or `Path.open` whose path argument is not obtained from the allowlist API.
      Violations are listed by file and line.
   **Wording downgrade, frozen:** `sealed_paths_read` is *"the set of `sealed*`-matching paths the
   audit hook observed, which is empty iff no such path was opened by any code running under the
   hook"*. It is **computed**, never a hardcoded `[]`. It is **not** a claim that every path C0001
   opened is enumerated — only reads reaching the CPython audit hook are, which is every
   filesystem open performed by Python-level code in-process.
8. `assert len(glob("phase3/cells/*_validation_*.json")) == 960` and
   `assert all("test" not in name)` — content-checked, not path-shaped (Q10).
9. **A C0001-specific firewall test** asserts (a) the allowlist contains no `sealed*` path and no
   directory, (b) the audit hook is installed and `sealed_paths_read` is empty, (c) no manifest call
   received a directory argument, (d) items 7c and 7d pass. **Note on the existing test relied on by
   v2** (V2-MIN-4): `GPU_RUN5/tests/test_gpu_run5_phase8.py:542` asserts
   `source.index("claim_test_open(") < source.index("load_sealed_test(")` — a **lexical
   first-occurrence check on source text**, not a runtime ordering check; it would pass even if a
   later call site violated the order. This C0001 test is the real protection.
10. **`load_sealed_test` and `require_artifact`.** `src/gpu_run5/config.py:63-67 load_sealed_test`
    raises `PermissionError` for `int(phase) < 8`, and C0001's declared phases are `R/phase0`–
    `R/phase4`, all below 8 — but **the real protection is that v2.1 never calls it**, not the phase
    gate. `require_artifact` (`config.py:56-72`) now carries a `sealed*` guard; it had **zero
    callers repo-wide** before, so AUDIT-MIN-5 overstated it as a live bypass. Both facts are
    recorded so neither is mistaken for the primary safeguard.
11. **Repo-level fixes: status.** `pytest.ini` **already** carries `pythonpath = .` and lists
    `GPU_RUN5/tests` (added in `39ab0fd`). v2's §2.4 item 6 presented this as pending and asserted
    that six files raise `ModuleNotFoundError: No module named 'scripts'` without `PYTHONPATH=.`;
    **that claim is withdrawn as stale** — 124 tests collect bare with zero errors and the default
    suite is 301 passed / 1 skipped (Q20, `research_state.md` §8 defect 1). Nothing further is
    required here.

**C0001 consumes no seal. There is no final-test access in this cycle. No sealed file is read,
hashed, `stat`-ed for content, or deserialized; only its name appears, from the census.**

### 2.4a The phase-4 seal: precise restatement (V2-MAJ-5)

v2 §2.4 recorded `phase4/sealed_official_test.json` as **"UNSPENT — the campaign's only clean seal …
MUST NOT be touched"**, and cited GPU_RUN5's own doctrine — `scripts/phases/gpu_run5_phase8.py:1170-1176`,
which opens `claim_test_open(` and then states *"The sole open event is durably recorded above. Only
now may sealed bytes be hashed or deserialized"* — as the reason a manifest call over a run root
would constitute a test-open event. Both halves of that record need correcting.

**The fact.** `scripts/phases/gpu_run5_phase4.py:151-152` computes
`sha256_file` over `sealed_official_test.json` **at write time**, inside phase 4, with **no**
`claim_test_open` and **no** ledger, and persists the digest to
`phase4/official_corpus_meta.json:artifact_sha256["sealed_official_test.json"]` as
`2860d829d9077d01258489fb68ed8dcd8a333d6a0e150b8e36b301f28bb1e070`. The same file re-hashes it on
every cache-validity check at `:118-119`. **That digest is byte-identical to the hash v2 §2.4
records for the seal**, so v2's provenance value came from the pre-ledger event. The same meta file
records `test_generated_not_evaluated: true`.

**Two doctrines are live in the repository**, and v2 invoked one while its own provenance value came
from conduct consistent only with the other:
- **strong doctrine** (phase 8's comment): hashing sealed bytes *is* the test-open event. Under it,
  this seal was opened before C0001 existed, by its own producing phase, outside any ledger.
- **weak doctrine** (phase 4's own behavior plus `test_generated_not_evaluated: true`): hashing is a
  provenance operation, and phase 8's hash-binding step is ceremonial.

**Frozen resolution.**
1. **v2.1 adopts the strong doctrine for C0001's own conduct.** C0001 will not read, hash, or
   deserialize any sealed file, and the §2.4 prohibition is prudent under either doctrine.
2. **v2.1 does not adjudicate the campaign's history**, which it did not cause and cannot undo.
3. **The phrase "UNSPENT — never touched" is withdrawn.** The seal's precise status of record is:
   > *`phase4/sealed_official_test.json` was **generated and never evaluated**
   > (`test_generated_not_evaluated: true`); it is **not covered by any test-open ledger**; and its
   > SHA256 was **computed by its own producing phase (GPU_RUN5 phase 4) outside any ledger**, and is
   > recomputed on every phase-4 cache-validity check. Under the strong doctrine GPU_RUN5 phase 8
   > itself asserts, that hashing already constituted a test-open event. Whether this seal is usable
   > as a clean confirmation set is therefore **an open campaign-level question, not a settled
   > fact.* C0001 does not touch it and does not rely on its cleanliness.*
4. **Required follow-up outside this document** (§20): record this as a `research_state.md` §8
   defect and correct §4's "UNSPENT — the only clean seal available" row. It is a campaign-level
   fact bearing on a future cycle's confirmation set, not a C0001 finding.

### 2.5 What cannot change after the irreversible commitment?

C0001 accesses no final test. The analogous irreversible commitment is **the first computation of
any Part A match indicator on a real stored candidate**. Immediately before that moment the
component-strata assignment and the realized ladder (§7.2) must already be written and hashed, and
the control battery (§7.7) must already have been run and gated (§7.10). After that moment the
following are immutable for this cycle, and any change forces a **new cycle ID**, not an amendment:

the primary hypothesis · the primary endpoint, its stratum definitions and its matcher level (M3) ·
the M0 / M1 / M3 cascade definitions, their representations (infix on both sides) and their
timeouts · the three-level unit hierarchy and the aggregation order · the `ANY` reduction · the
clustered-interval estimators, their resample count, generator and seed · the outcome ladder and its
cutpoints · the control battery, its eligibility rules, its thresholds and its **gating map (§7.7)**
· the `could_not_evaluate` maximum · the Go/No-Go gates · the supported / unsupported / refuted /
undecidable criteria · the exclusion and failure policy · the E2/E3 discriminator and its thresholds
· seeds · the checkpoint SHA256 · the compute ceiling · the run ID · the §1.3 scope restriction.

### 2.6 The ten separations kept explicit (role contract, rules 03 and 04)

| aspect | C0001 v2.1 |
|---|---|
| **training** | **NONE.** Zero parameters updated, no optimizer constructed, zero training budget. |
| **validation** | The 80-system / 170-component GPU_RUN5 validation split is the *only* measurement set. Every threshold in this file is fixed before Stage 4; nothing is selected on validation *outcomes*. |
| **final test** | **NOT ACCESSED.** 7 sealed artifacts enumerated, 2 ledger-spent, 5 with no ledger entry, all forbidden (§2.4). |
| **generation** | Measured as **coverage**: `ANY` over the candidates the model actually emitted (rule 03). Candidate generation is not re-run; the decode budget is zero. |
| **selection** | Measured **separately** from generation: A2-S5 reports the **oracle** candidate per cell per level against the **selected** candidate under the frozen selection rule (`src/evaluation/gpu_run5_selection.py:11`). Generation failure and selection failure are never merged. |
| **numerical fit** | `reconstruction_r2`, `generalization_r2`, NRMSE and the trajectory metrics are carried as **covariates only** and may be cross-tabulated against match status. **No match, recovery or discovery claim may be made from any of them** (rule 01 item 6, rule 03). |
| **formula recovery** | Reported at four distinct resolutions, never collapsed: exact string (`exact`), canonical prefix exact (M1), constant-collapsed skeleton equivalence (M3), and structural distance (stored `ted_raw`, `ted_skeleton`, `normalized_ted`, `component_normalized_variable_aware_ted`). Variable recovery (precision / recall / F1 / `unnecessary_variables`) is reported separately again. **M3 is a skeleton criterion at collapsed constants and is named as such.** |
| **representation** | **NOT MEASURED.** No CKA, no similarity geometry, no probe. |
| **causal contribution** | **NOT MEASURED.** No ablation, no intervention. A2-S7 states a *consequence* for a future cycle and notes that in-beam component coverage and `component_exact_loss` under intervention are **different estimands**. |
| **adaptation** | **NOT MEASURED.** No IOLE, no single-layer fine-tuning, no selective fine-tuning, no fine-tuning of any kind. |

---

## 3. Model, checkpoint, seeds, budgets

| item | frozen value |
|---|---|
| checkpoint | `assets/odeformer/weights/odeformer.pt`, SHA256 `56754040be5aa92ed4767fc43ee2008faa293f87c12b643e66c7df3e1623a5e8` (verified at both audits) |
| architecture of record | released `4 encoder (dim 256) + 12 decoder (dim 512)`, 16 heads, 60,646,773 params — **not** the paper's 4+16 / dim 512 / ~86M |
| **training budget** | **ZERO** |
| **hyperparameter search space** | **EMPTY**. Every threshold in this file is fixed before Stage 4. |
| **new decoding / candidate budget** | **ZERO**. No new beam search, no new sampling. Part A re-scores stored artifacts; Part C is forward-only teacher-forced scoring. |
| decode config of the stored candidates (fixed context, never swept) | `beam_size = 50`, `beam_type = sampling`, `beam_temperature = 0.1`, `max_generated_output_len = 200`, `rescale = True`, `failure_penalty = 10.0` |
| operator constraints of record | `operators_to_use = "sin:1,inv:1,pow2:1,id:3,add:3,mul:1"`; `min/max_unary_ops_per_dim = 0/3`; `min/max_binary_ops_per_dim = 1/5`; `max_unary_depth = 7`; `max_int = 10`; `float_precision = 3`; `max_dimension = 6`. Zero-probability operators per P2. |
| **seeds** | **Part A's matcher is deterministic**: M0, M1 and M3 involve no RNG. **Correction (V2-MAJ-1):** v2 stated that with M3 pinned to `["skeleton"]` the grid in `_approximately_equivalent` "is not called at all". That is **false** — the return dict at `equation_metrics.py:207-212` is built **eagerly**, so the whole equiv block at `:195-205` executes on every M3 call, including `_approximately_equivalent` at `:203` whenever `diff != 0 and skeleton == 1.0`. It remains **non-random**: `:84-85` fixes `base = [0.2, 0.7, 1.3, 1.9]` and `args = [base + 0.11*index …]`, with no `points` or `seed` parameter. (v2's citation `:72-73` is corrected to `:84-85`.) Determinism therefore holds for the reason stated, not for the reason v2 gave. Part B is deterministic except rewrite verification, `numeric_equivalent(seed = 0)`, frozen at **0**. Part C is deterministic (`model.eval()`, `torch.no_grad()`, `torch.use_deterministic_algorithms(True)` where supported). **Cluster bootstrap: `numpy.random.default_rng(20260909)`, one generator stream, 10,000 resamples, draw order families then systems within family** (V2-MIN-6). Global seed **20260909**. Control-battery eligibility verification: `numeric_equivalent(n_points=32, seed=0)`. Cost calibration sampling: `numpy.random.default_rng(20260909)`. |
| Part A parallelism | **process-based, ≤ 6 worker processes** (AUDIT-MAJ-5). Thread parallelism is **forbidden**: `_time_limit` (`equation_metrics.py:36-42`, and its docstring at `:32-34` says so outright) silently yields unguarded off the main thread, removing every SymPy wall-clock guard. A Stage-6 smoke assertion must demonstrate `_time_limit` firing **inside a worker**. (v2's citation `:38-45` is corrected to `:36-42`.) RAM basis: 0.53 GiB/process, 6 workers ≈ 3.2 GiB of 52 GiB available (Q18). |
| SymPy guards | `SYMPY_OP_TIMEOUT_SEC = 10.0` (`equation_metrics.py:21`; used by `_timed_simplify` and `_timed_equals`). Unchanged by C0001. **Three live 10-second surfaces per M3 call, all inside the measured cost basis:** `to_skeleton`'s `_timed_simplify` (twice, once per side), `:189`'s `_timed_simplify(sk_true − sk_pred)`, `:190`'s `_timed_equals`, **and `:200`'s `_timed_simplify(true_parsed − pred_parsed)` on the un-skeletonized expressions**, which v2 believed unreachable (V2-MAJ-1). `LANSR_SYMPY_MAX_NODES` and `SYMPY_EQUIV_TIMEOUT_SEC` (`ted.py:14-15`) apply only to `_sympy_components_equal`, which **no v2.1 endpoint calls**; the PC0-CAS diagnostic runs it with the cap raised to **200**, in a **dedicated subprocess with the environment variable set before interpreter start** (V2-MIN-5: `ted.py:15` reads it at import and `formulas.py:13` binds it by value, so in-process monkeypatching leaves `formulas.py:434` at 40 and PC0-CAS would silently re-measure 28/80). |
| dtype / device | fp32 throughout; Part C on `cuda:0`; Parts A and B CPU-only |
| environment | PyTorch 2.5.1+cu124, sympy 1.13.1, numpy 2.2.6, zss 1.2.0, Python 3.10.20, env `lansr310` — identical to the versions in the source run's `phase3/manifest.json`, which is why re-scoring is reproducible |

---

## 4. Comparators and baseline conditions

Nothing is trained, so there is no trained baseline. The comparators are **frozen published
measurements**:

| comparator | value of record | role |
|---|---|---|
| **C-M0** frozen matcher, system level | `true_exponent_aware_skeleton_in_beam` = **0/960 cells**, 0/120 per family (P0a) | the published claim whose interpretation is under test. The stored value is a **mean over 960 cells** (`gpu_run5_phase3.py:442`), not over 80 systems; the reductions coincide only because the value is exactly 0 (AUDIT-MIN-11). |
| **C-M0c** frozen matcher, component level | **107/2040 = 0.0525** (P0b), by family R01 0, R02 0, R03 0, R04 56, R05 0, R06 0, R07 17, R08 34 | the reference level the primary's *gain* is measured against. Its `ANY`-reduced counterpart, which is what the primary actually compares against, is **not identified**: admissible range [0.053, 0.629] (§1, V2-MAJ-4). |
| **C-M0f** stored per-candidate fields | `exponent_aware_skeleton_exact` and `component_exponent_aware_skeleton_exact` for all **47,987** candidates / **101,963** component comparisons, including all **2,235** component-level ones (P0c) | the R1-mandated positive control. Gate A→B requires exact reproduction (§7.6). |
| **C-ODEB** ODEBench frozen matcher | 4/252 = 1.59% [0.0062, 0.0401] | non-zero corpus-level positive control for the §15 replication |
| **C-BUDGET** the generator's own unary budget | `max_unary_ops_per_dim = 3` | Part B reference |
| **C-SAMPLED** the model's own 50 sampled candidates per cell | measured in Part C | Part C reference — the model is compared against **itself**, the budget-matched comparison, with the T = 0.1 upper-tail caveat frozen in §8.3 |
| **C-SELECTED** the candidate the frozen selection rule returned per cell | measured in Part C | the second element of the paired Stahlberg–Byrne discriminator (§8.3) |

**Naming correction, applied throughout v2.1 (V2-CRIT-3 root cause).** M0 is **not** "the frozen
string matcher". It is the **frozen exponent-aware canonical-tree matcher with collapsed constants**:
in the mandated infix-on-both-sides configuration, `formula_views(..., as_prefix=False)` parses and
canonicalizes before the skeleton is formed, so e.g. `-1 * 0.3968 * x_0` becomes `-0.3968 * x_0` and
the emitted canonical prefix is
`add,add,0.1954,mul,-0.3968,x_0,mul,mul,0.8878,inv,add,0.8392,x_0,x_0`. Every "string matcher" phrase
in v1 and v2 is superseded. The consequence for the M0-vs-M3 contrast is spelled out in §1.3 and
§7.4.

**Dropped comparator.** v1's `C-NEG` (crude `neg`-folded matcher, "a lower bound on what a proper
canonicalizer should find") is **deleted**. Its component value *was* C-M0c, re-derived; per R1 that
is a positive control, not a comparator, and presenting it as an independent lower bound
double-counted one measurement.

---

## 5. Fair comparison budget

Every comparison is budget-matched **by construction**, and the places where matching holds at the
code level but not at the estimand level are declared rather than asserted away.

1. **Part A** applies M0, M1 and M3 to the **identical** 47,987 stored candidates, the identical 170
   truths, the identical 960 cells, in the **same pass, from the same parsed inputs**. No arm sees
   different data, more candidates, more cells or more compute. The only thing that varies is the
   equivalence criterion, so any difference is attributable to the instrument alone. **Both sides of
   every comparison are fed the infix representation** (R1, AUDIT-CRIT-2):
   `formula_metrics(teacher_infix, candidate_formula_raw)` for M0 and the same infix pair for
   M1/M3. `phase3/cells/*.json:true_structure` is **prefix-derived** and must never be compared
   against an infix-derived skeleton — that mixing produced the retracted finding.
2. **Timeout and failure budgets are identical** across arms, truths, candidates and controls. No
   arm receives a longer wall clock, a larger node budget, or a retry the others do not get. In
   particular, all three matcher arms are subject to the same `SYMPY_OP_TIMEOUT_SEC = 10.0`, and no
   arm runs under a raised `LANSR_SYMPY_MAX_NODES` (the PC0-CAS subprocess is a **diagnostic, not an
   arm**, and produces no endpoint).
3. **Control-battery budget parity (new in v2.1).** Every control is scored through the **same**
   functions, the same representation, the same timeouts and the same `gain` code as the endpoint
   pass (§7.10). No control receives a bespoke matcher, a relaxed tolerance, or a second attempt.
   PC4 in particular is **not** a bypass: it calls `formula_metrics` and `symbolic_recovery` exactly
   as the endpoint pass does, differing only in that its candidate is synthetic and tagged.
4. **Part B** compares two encodings (multiplicative vs affine-decomposed) of the **same** truth
   against the **same** fixed budget of 3, with an identical 200-rewrite enumeration cap on both.
5. **Part C** scores the ground truth and all candidates for a cell through the **identical**
   forward path: one `embedder` + `encoder("fwd", causal=False)` pass whose `src_enc` is cached and
   reused, then the same `decoder("fwd") → decoder("predict", get_scores=True)` call, in the same
   process, in fp32, on the same device. Both GT encodings and all candidates go through the same
   new scoring function. §8.2 preregisters the audit that proves it.
6. **Declared asymmetry 1 — conditioning identity (STAT-C3).** `input_trajectory_checksum` is the
   **pre-corruption source** checksum: 80 distinct values over 80 systems, constant across all 12
   cells of every system, while the 12 cells carry 10 distinct payloads (P11, re-verified in 80/80).
   It cannot detect a cell-level mixup. v2.1 replaces it (§8.2 step 1) and relabels it a
   **system-identity** check.
7. **Declared asymmetry 2 — encoding orbit (STAT-M9).** Each candidate is scored as the **one** token
   sequence the model actually emitted, for which the single-sequence log-prob is exactly the right
   quantity. The GT is scored as **one of many equivalent encodings**, so `logP(one encoding)` is a
   **lower bound** on the probability the model assigns to the truth as a function. Magnitude, from
   P7: 4920/960 = 5.125 `mul` + 4080/960 = 4.250 `add` = **9.375 commutable binary nodes per system
   truth** → ~26 equivalent orderings at 50% swappability (**3.25 nats** understated), ~131 at 75%
   (**4.87 nats**), ~664 at 100% (**6.50 nats**). This is a **preregistered directional bias toward
   E2 (model error)**, of magnitude 14–28% of a 0.5 nats/token decision scale at Lg = 47. It is
   disclosed, bounded, and partially mitigated by the §8.2 step 5 orbit report; it is **not** claimed
   to be absent. v1's "there is no 'GT gets a special path' asymmetry" is **withdrawn**: true of the
   forward pass, false of the estimand.

---

## 6. Experiment structure and ordering

**Three parts**, ordered so the cheapest claim-invalidating check runs first.

| part | question | instrument | compute | gate |
|---|---|---|---|---|
| **Part A** | **E0** — does canonicalization recover Hill-component matches M0 missed? | M0 / M1 / M3 cascade over the stored candidates, component-type-stratified | **CPU only** | Gate 0 → A |
| **Part B** | **E1'** — is the truth outside the generator's sampling support? | analytic unary-budget census over stored truths | **CPU only** | Gate A → B |
| **Part C** | **E2 vs E3** — model error or search error? | teacher-forced summed log-probability, paired against the candidate search actually returned | **GPU, forward passes only** | Gate B → C |

Parts A and B touch no GPU. Part C is the only GPU work in the cycle. **Within Part A the execution
order is itself frozen** (§7.10), so that the instrument is proved capable **before** the endpoint
pass spends 8.73 core-hours.

---

## 7. Part A — evaluator adequacy at component resolution (CPU only)

### 7.1 PRIMARY ENDPOINT (the one and only) — unchanged from v2

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
> **Primary = ( Σ_{(s,i) ∈ H} gain(s, i) ) / |H| = K / 130.**

**Intervals, frozen, with the degenerate case resolved (V2-MAJ-3).** Three are computed and
reported always:

| id | interval | label |
|---|---|---|
| (a) | plain **Wilson score** 95% over `\|H\| = 130` components, z = Φ⁻¹(0.975) = 1.959964, no continuity correction | `assumes_component_independence: true` |
| (b) | **two-stage cluster bootstrap** 95% **percentile** interval: families resampled with replacement, then systems within each drawn family with replacement, **10,000** resamples, `numpy.random.default_rng(20260909)`, one generator stream, draw order families-then-systems | `interval_target: component_gain_rate` |
| (c) | **8-cluster Wilson** interval on the family-level indicator (a family contributes 1 iff ≥ 1 of its H components shows a gain) | `interval_target: family_level_indicator_rate` |

> **Frozen bound-of-record rule.** For `K ≥ 1` the **interval of record is (b)**. For **`K = 0`** the
> interval of record is **(c)**, whose value is fixed and known: `0/8 → [0, 0.3244]`. **Reason**: at
> `K = 0` all 130 component indicators are 0, so **every** bootstrap resample yields 0 and (b) is
> exactly the degenerate `[0, 0]`. **It is forbidden, anywhere in this cycle, to report a bootstrap
> percentile upper bound of 0 as an upper bound**, and forbidden to fill §9.5 item 1's `[value]`
> slot with `0.0000`. (b) is still computed and reported at `K = 0`, but under the label
> `degenerate_all_resamples_zero: true` and explicitly **not as an evidential bound**. §9.5 item 1
> has a separate verbatim variant for `K = 0` in which the **power statement**, not an interval, is
> the substantive content.

**Why this endpoint and not v1's.** E0 asserts that the frozen matcher misses structurally correct
candidates. The disclosed mechanism is **per-component**. v1's primary reduced by conjunction over
all components of a system, i.e. it estimated the *d-th power* of the phenomenon, in a corpus where
dimension is perfectly confounded with family and where the only stratum in which the conjunction
can realistically fire (dim-1, R01/R02) is known to be empty at component level (P0d). Its outcome
carried **0.286 bits** (STAT-C1). This endpoint is at the resolution E0 operates at, restricted to
the components whose failure is the scientific question.

**Why the *gain* and not the level.** The component-level M3 *level* is not informative on its own:
it is a mixture of what M0 already finds and what M3 adds. **v2's justification for this — that the
level is "bounded below by 107/2040 under monotonicity" — is withdrawn**, because monotonicity is
false (V2-MAJ, §7.5). The correct justification does not need it: the **gain** is exactly the
retracted claim, tested properly — *are there components whose structure is in the beam and which the
frozen matcher scored as a miss?* — and it is measured **only on M0's misses** by construction.

**The endpoint is measured where M0 failed, not where it succeeded** (V2-OK-2). `gain` requires
`m0_any = 0`. Quantitatively: **90 of the 130 H components** lie in R01/R02/R03/R05/R06, families
with **0** published M0 component hits (0/120, 0/120, 0/240, 0/240, 0/360), so `m0_any = 0` there by
published data and `gain = m3_any` outright. At most **40** H components (in R04/R07/R08) can carry
`m0_any = 1` and be structurally barred from contributing. The denominator is therefore at worst 31%
inflated by components that cannot contribute, which **deflates the rate — the conservative
direction for a null-shaped claim** — and the ladder decides on the **count `K`** against `C = 3`,
which the denominator does not touch.

**Naming.** M3 collapses every numeric constant to `c` (`equation_metrics.py:162-163`), so an M3
match is **skeleton equivalence at collapsed constants**, not semantic equivalence. No artifact may
call it semantic equivalence (AUDIT-MIN-10, rule 03).

### 7.2 Component-type strata (frozen definition; assignment computed before any matching)

Assignment is a **truth-side** property and carries no candidate-outcome information. It is computed
from `phase2/validation.json:teacher_components_infix` through
`src/gpu_run4/formulas.py formula_views(..., as_prefix=False)["components"]` — the **infix** path, so
that stratum assignment and matcher input come from the same derivation path (R1).

| stratum | definition (decidable on the parsed tree) |
|---|---|
| **H — Hill / variable-denominator** | the component's parsed tree contains **at least one `inv` node whose argument subtree contains at least one variable leaf `x_j`** |
| **L — no variable denominator** | every other component: linear-decay-only, constant-affine, and any component whose only `inv` arguments are constant subtrees |

**Realized values, now known and frozen here (Q16).** `|H| = 130`, `|L| = 40`, agreement with the
independently-derived stored `structure.component_flags[i].variable_denominator_form` **170/170**.
H by family: R01 10, R02 10, R03 20, R04 10, R05 20, R06 30, R07 20, R08 10. L by family: R04 10,
R07 10, R08 20; **R01, R02, R03, R05, R06 have zero L components**. H by dimension 1→20, 2→50,
3→60; L by dimension 2→10, 3→30. **`C = ceil(0.02 × 130) = 3`.** The implementation must
**recompute** these and **assert equality** with the values frozen here; a mismatch is a harness
defect, halts Part A, and is handled under §7.6's failure protocol.

Frozen procedural requirements, in this order:

1. The strata assignment for all 170 components is written to `R/phase1/component_strata.json`,
   with `|H|`, `|L|`, the per-family and per-dimension breakdown, the assertion result against the
   frozen Q16 values, and the SHA256 of the file.
2. The realized-`|H|` **Wilson table, ladder cutpoint `C`, operating-characteristic table and power
   table** are written to `R/phase1/partA_ladder_realized.json`, recomputed from the frozen formulas
   of §9.3 and §7.3 and **asserted equal** to the values frozen in those sections. Both depend on
   `|H|` alone.
3. **The H/L stratification of GPU_RUN5's 107 published M0 component hits may be computed only after
   steps 1 and 2 are written and hashed** (§0.4).
4. **Mechanical enforcement, frozen in this document (audit §5.4).** The write-before-match ordering
   is enforced by a **capability token**, not by a comment or by call ordering:
   `src/gpu_runclaude1/strata.py require_strata_frozen(...)` returns a `StrataFrozenToken` whose
   **only** constructor is that function, and it refuses to return unless (i) both artifacts exist
   on disk, (ii) the strata file's recorded `sha256_of_component_assignment` re-verifies against its
   own content, and (iii) the ladder file records that same hash as
   `sha256_of_component_strata_input`. **Every function that can compute a match indicator on a real
   stored candidate must require that token as a parameter.** A reimplementation that satisfies the
   ordering by call sequence alone does **not** satisfy this preregistration.
5. **Only then** may any match indicator be computed on a real stored candidate. (Control-battery
   indicators on **synthetic** truth-vs-rewritten-truth pairs are exempt and are run in step
   §7.10-3, before the endpoint pass, because they contain no candidate-outcome information.)

Any implementation that computes a match indicator on a real stored candidate before steps 1, 2 and
4 are satisfied has violated the preregistration, and Part A is **`undecidable`** with no remedy
short of a new cycle ID (§14 item 8).

**Frozen fallbacks, so no post-hoc choice exists.** If `|H| < 40` **or** `|L| < 15`, the stratified
primary is `not_measurable` and the primary falls back — automatically, with no discretion — to the
**unstratified** component-level gain rate over all 170 components, with the stratified values
reported descriptively. If `40 ≤ |H| < 100`, the primary stands but its null-direction verdict is
labeled `underpowered_bound_only` whenever the realized power to detect a 0.0525 gain rate falls
below 0.90, and in that state it **may not be cited as refuting E0**. **Neither fallback fires at
the realized `|H| = 130`, `|L| = 40`**; they are retained so that a harness returning different
values has a defined, non-discretionary path.

### 7.3 Frozen predictions

| quantity | prediction | status | basis |
|---|---|---|---|
| `\|H\|` | **130** | **measured (Q16)**, inside v2's blind prediction of 130–145, at the lower boundary | v2 predicted from P7's aggregate token counts; the realized value is now disclosed |
| `\|L\|` | **40** | **measured (Q16)**, inside v2's blind prediction of 25–40, at the upper boundary | same |
| **PRIMARY — Hill-stratum gain count `K`** | **0** of 130 | **frozen blind prediction; genuinely unobserved** | E0 has no component-level empirical support after `RETRACT`; M0 already finds the 107; and by §1.3 the only E0 mechanism the instrument can see is M-iii, for which no candidate-side evidence exists |
| **L-stratum gain count** | **0** of 40 — **re-derived in v2.1** | frozen blind prediction | **v2 predicted `> 0`** on the basis that "real candidates spell decay as a signed constant (P4), **which M0 cannot match** and M3 can". **That basis is false** (Q12b: M0 = 170/170 on the P4 rewrite), so the prediction is re-derived rather than retained. With M-i absorbed by M0, **no known mechanism produces a gain in stratum L**, and Q12 shows the one rewrite class that does produce gains (common-denominator) yields **0 gains in L** on synthetic candidates, because `together` is absorbed by M0 on exactly the L components. The honest prediction is therefore 0. Recording the change, its cause and the withdrawn basis is required by rule 01 item 3 — this is a **correction of a refuted premise before observation**, not a threshold moved to rescue a result. |
| H − L gain difference (A2-S1) | **0** | descriptive | follows from the two rows above |
| type stratification of GPU_RUN5's 107 M0 hits | **majority in stratum L — at least 54 of 107** | **`partly_derivable_prediction`, no longer blind (§0.4)** | L is non-empty in **exactly and only** R04/R07/R08, the three families carrying **all** 107 hits (Q16 + P0b). May **not** be cited as evidence of foresight. A miss is still informative about the derivation. |
| dimension distribution of the 107 | **0 in dim-1** | **not a prediction: deduced** from published values (P0d) | — |
| monotonicity violations (`m0_any = 1, m3_any = 0`) | **no prediction** — v2's "≤ 0.1%" is **withdrawn** | reported, non-gating (§7.5) | M3 is **not** a superset of M0: under `sympy.apart` the audit measured M0 3/20 vs M3 0/20, because constant collapsing breaks identities M0's canonical tree still matches. A non-trivial violation rate is expected, is explained, and **provably cannot affect the primary** (§7.5 item 4). |
| PC4 gain (positive control) | **≥ 40 total and ≥ 20 in stratum H** | **verification of Q12** (measured 100 total, 100 in H) | §7.7 |

**Powered-falsification statement (the primary's inferential content, not an equivalence claim).**
Under independence across components, the probability of observing **≥ 1** gain is
`1 − (1 − p)^{130}`. Frozen at the realized `|H| = 130`:

| true per-component gain rate `p` | power to observe ≥ 1 gain |
|---|---|
| **0.0525** — the arithmetic lower bound of M0's `ANY`-reduced component rate (§1, V2-MAJ-4) | **0.9991** |
| 0.03 | 0.9809 |
| 0.02 | 0.9277 |
| 0.01 | 0.7292 |
| 0.005 | 0.4788 |

So a zero observation is informative **against E0 at its own stated magnitude** and progressively
uninformative below ≈ 0.01. **Clustering reduces effective power below these independence figures**;
the cluster bootstrap must report the family-clustered power at `|H| = 130` alongside them, and the
**smaller** of the two is the number the report quotes. These values must be recomputed into
`partA_ladder_realized.json` and asserted equal to the table above (§7.2 step 2).

### 7.4 The matcher cascade (frozen definitions; M2 removed)

Applied per (cell, candidate, component), index-aligned by variable: truth component *i* is compared
**only** to candidate component *i*.

| level | definition | implementation of record |
|---|---|---|
| **M0** | frozen exponent-aware **canonical-tree** skeleton equality with collapsed constants — **not** a string matcher (§4) | `src/gpu_run5/evaluation.py:39 formula_metrics(teacher_infix, candidate_formula_raw)`, fields `exponent_aware_skeleton_exact` (system, `:84-87`, requiring `component_count_match` **and** whole-string equality of the canonical skeleton) and `component_exponent_aware_skeleton_exact` (component, `:47-53`, index-aligned split on `" \| "`). **Infix on both sides**; `formula_metrics` calls `compare_formulas(true_infix, predicted_infix, skip_cas=True)` at `:41`. |
| **M1** | canonical prefix exact | `src/gpu_run4/formulas.py:479 compare_formulas(..., skip_cas=True)["canonical_exact"]` |
| **M3** | **constant-collapsed skeleton equivalence — the primary level** | **definition of record: exactly** `src/evaluation/equation_metrics.py:169 symbolic_recovery(T_i_infix, C_i_infix)["skeleton"]`, and **no other key**. Internally: `to_skeleton` (`:153`, via `_to_skeleton_with_reason`) maps constants to `c` and returns `_timed_simplify(sympify(...))`, then `:189 _timed_simplify(sk_true − sk_pred) == 0` **or** `:190 _timed_equals(sk_true, sk_pred)`. |

**M3 pinning.** v1 wrote "`symbolic_recovery(...)["skeleton"]`, plus `_approximately_equivalent(rtol=1e-6)`,
plus `to_skeleton`", which is not a composition rule and admitted three readings with different
rates. v2 and v2.1 pin M3 to the single key `["skeleton"]`.

**Corrected consequences of pinning (V2-MAJ-1).** v2 asserted three times (`v2:409`, `v2:620-623`,
`v2:1478`) that `_approximately_equivalent` is "not called" and that the `:205`
`except Exception: equiv = skeleton` fallback is "not reachable". **Both assertions are false.** The
return dict at `equation_metrics.py:207-212` is built **eagerly** — Python has no lazy dict values —
so a caller reading only `["skeleton"]` still executes the entire equiv block at `:195-205`: two
`sympify` calls, `_timed_simplify(true_parsed − pred_parsed)` at `:200` on the **un-skeletonized**
expressions (bounded by `SYMPY_OP_TIMEOUT_SEC = 10.0`), `_approximately_equivalent` at `:203`
whenever `diff != 0 and skeleton == 1.0`, and the `:204-205` handler. **What survives unchanged, and
why the pinning is still correct:** `skeleton` is finalized at `:187-193` **strictly before** the
equiv block; `:205` writes only to the local `equiv`; the data flow is one-directional
(`skeleton → equiv`, never back); and `_approximately_equivalent`'s grid is non-random (`:84-85`).
So `["skeleton"]` **cannot** be contaminated and the M3 value is deterministic. **What changes:** the
`:200` timeout joins the §7.5 failure-surface list, and the compute model in §11.1 records that this
block is inside the measured 655 ms/candidate.

**Implementation divergence, resolved (V2-MAJ-2).** The in-flight implementation calls
`skeleton_equivalence_with_reason` (added to `equation_metrics.py`) rather than
`symbolic_recovery(...)["skeleton"]`; that function skips the equiv block and is therefore faster,
and `to_skeleton`/`symbolic_recovery` were **refactored**, not merely extended. Frozen resolution —
`skeleton_equivalence_with_reason` may be the **implementation** if and only if both hold:

- **(a) Synthetic agreement test, Gate 0 item 11.** Over the **910 synthetic control pairs** of
  §7.7 — PC0 (170), PC2a (170), PC2b (its eligible instances), PC2c (170), PC2d (170), PC3a (48),
  PC3b (60), PC4 (170), PC4b (170) — the two implementations must return **bit-identical**
  `["skeleton"]` values, **100% agreement, no exceptions**. This corpus spans proved matches, proved
  non-matches and every labeled failure surface, and contains **no candidate data**, so it can be run
  before the strata are frozen without violating §7.2.
- **(b) In-pass agreement census.** During the endpoint pass, every 100th (cell, candidate,
  component) triple in the frozen deterministic enumeration order is scored by **both**
  implementations and the agreement recorded. `m3_implementation_agreement` is a reported endpoint
  (A2-S6c) with a **frozen requirement of 100%**; any disagreement halts Part A as a harness defect
  under §7.6's protocol. Cost: ≈ 480 extra M3 calls ≈ 0.08 core-h.

If either fails, the implementation must call `symbolic_recovery(...)["skeleton"]` directly and the
pass is re-run whole. **§17's "extended, not modified" discipline is extended to
`src/evaluation/equation_metrics.py`.**

**Monotonicity must not be assumed by code (V2-MAJ).** `M0 ⊆ M1 ⊆ M3` is **false**. No
implementation may short-circuit M1 or M3 on the basis of an M0 result, skip a level because a lower
level matched, or derive one level's indicator from another's. All three levels are computed
independently for every triple. **`ComponentCountMismatch` is a decided non-match**
(`match_outcome = "proved_different"`, `failure_reason = "ComponentCountMismatch"`) at **every**
level — this is its single classification, resolving V2-MIN-9's three-way ambiguity — and it is
**excluded** from the `could_not_evaluate_rate` numerator, because a component count is an observed
fact and not a failed evaluation. Empirically inert on this corpus: `(true_dim, n_pred_components)`
is diagonal for all 47,987 candidates (12,000 / 17,998 / 17,989) and **0** of the 2,235 stored
component hits occurs under a count mismatch.

**M2 is removed from the design** (§18.1). `_sympy_components_equal` is called nowhere in Part A's
endpoint path, and its unreachability is structural: one definition (`formulas.py:427`), one call
site (`:496`) behind `elif not skip_cas:` (`:495`), `formula_metrics` passes `skip_cas=True`, and
`equation_metrics.py` never imports `gpu_run4`. Its node cap (`SYMPY_MAX_NODES = 40`,
`formulas.py:434`, returning `0.0, None` with **no** failure reason) is therefore **unreachable from
every v2.1 endpoint path**.

**Roll-up (frozen).**
`component_match(i, level)` → `cell_component_hit(i, level) = OR over usable candidates` →
`component_any(i, level) = OR over the 12 cells` → primary as §7.1; and, for the demoted
system-level secondary, `system_match(candidate, level) = component_count_match AND all_i
component_match(i, level)` → `cell_hit = OR over candidates` → `system_hit_ANY = OR over 12 cells`.

### 7.5 Failure taxonomy, monotonicity, and the reported failure endpoint

The code comment at `equation_metrics.py:18-20` says a timeout is treated as "could not prove
equivalence (the conservative outcome that never inflates a recovery score)". That is conservative
for a *recovery* claim and **anti-conservative for C0001's null**, where an unprovable comparison
counted as a miss pushes the primary toward `supported`. Frozen requirements:

1. **Every non-match carries an explicit `failure_reason`, and `proved_different` is separated from
   `could_not_evaluate` at every level.** No path may return an unlabelled non-match. The specific
   surfaces, each verified present in the code:
   - `to_skeleton` returning `None` (`equation_metrics.py:166`, i.e. `_to_skeleton_with_reason`'s
     terminal return) → `SkeletonParseFailure`;
   - the same terminal return when the failing attempt raised `_SymTimeout` →
     `SymbolicEquivalenceTimeout`;
   - `except Exception: skeleton = 0.0` (`:192-193`) → `SkeletonEvaluationFailure`;
   - a `_timed_simplify` / `_timed_equals` wall-clock trip at `:189` or `:190` →
     `SymbolicEquivalenceTimeout`;
   - **`_timed_simplify(true_parsed − pred_parsed)` at `:200`** — the surface v2 omitted because it
     wrongly believed the block dead (V2-MAJ-1). It cannot change `["skeleton"]`, but it **can**
     trip the 10 s guard and it **does** consume wall clock on every call, so it is labeled
     `EquivBlockTimeout_NonEndpoint` and **counted separately**, outside the
     `could_not_evaluate_rate` numerator (it cannot affect the endpoint value);
   - component-count mismatch → `ComponentCountMismatch`, classified as **`proved_different`**
     (§7.4), **excluded** from the `could_not_evaluate` numerator;
   - a parse failure on either side → `ParseError`;
   - and, for the PC0-CAS diagnostic only, `nodes > SYMPY_MAX_NODES` (`formulas.py:434`) →
     `SymbolicNodeCapExceeded`.
2. **`could_not_evaluate_rate` is a reported endpoint** (A2-S6):
   `(SkeletonParseFailure + SkeletonEvaluationFailure + SymbolicEquivalenceTimeout + ParseError) /`
   all scored (cell, candidate, component) triples. **Frozen maximum: 2.0%.** Above 2.0% the Part A
   primary is **`undecidable` (instrument failure)** and no null may be reported. Between 0% and
   2.0% the primary is reported **together with** the two-sided sensitivity analysis of item 3.
3. **Two-sided sensitivity analysis, mandatory whenever `could_not_evaluate_rate > 0`**: recompute
   the primary counting every could-not-evaluate triple as a **non-match** (the primary of record,
   the direction that does not inflate the gain) **and** as a **match** (the adversarial direction).
   If the two land on different ladder rungs, the verdict is **`undecidable`**.
4. **Monotonicity: reported, non-gating, and provably irrelevant to the primary (V2-MAJ).**
   v2 expected `M0 ⊆ M1 ⊆ M3` and made a `> 1%` violation rate a CRITICAL that renders Part A
   `undecidable`. **That expectation is false and the tripwire is removed**, for two reasons:
   - **The expectation is false.** Under `sympy.apart` the audit measured M0 3/20 vs M3 0/20. M3 can
     be **strictly less permissive** than M0 because `to_skeleton` maps every distinct constant to
     the same symbol `c`, under which some algebraic identities cease to hold while M0's
     exponent-aware canonical tree still matches. Retaining a CRITICAL tripwire on an expectation
     known to be false is a second deterministic-burn hazard of exactly the kind V2-CRIT-1 and
     V2-CRIT-2 identified.
   - **Violations cannot affect the primary.** `gain(s,i)` requires `m0_any(s,i) = 0`. Every
     violation is a component with `m0_any = 1`, which therefore contributes **0** to the numerator
     **by definition**, whatever M3 does there. Monotonicity failures can neither inflate nor deflate
     `K`. The primary is an **indicator conjunction, not a difference**, so it lies in {0,1} and can
     never be negative.
   Frozen policy: the full `M0 ⊆ M1 ⊆ M3` audit is **computed and reported** at triple resolution,
   every violation logged with both expressions and both derivation paths; the component-level count
   of **`m0_any = 1, m3_any = 0`** is reported explicitly as **A2-S6b** — it is the direct sibling of
   the primary and the exact check that would have caught the retracted representation bug. **No
   threshold on it gates anything.** The report must state the measured rate and the reason it does
   not bear on `K`.
5. **The multiplicity argument does not rest on monotonicity** (§9.4 item 4, re-derived).

### 7.6 The reproduction gate that replaces v1's defect trigger

v1's instrument safeguard was `A-S3 ≥ 0.0525`, an `ANY`-over-12-cells rate compared against a
cell-level rate whose admissible range for the same 107 matches is [0.052, 0.629] — a trigger that
could not fire even if the cascade were twelve times worse per cell. It is **deleted** and replaced:

> **The M0 arm, computed as `formula_metrics(teacher_infix, candidate_formula_raw)`, must reproduce
> the stored `exponent_aware_skeleton_exact` and `component_exponent_aware_skeleton_exact` fields
> for all 47,987 candidates and all 101,963 component comparisons exactly — including all 2,235
> stored component-level ones — and must reproduce the reduced values 0/960 system-level and
> 107/2040 component-level, and all eight per-family counts (R01 0/120, R02 0/120, R03 0/240,
> R04 56/240, R05 0/240, R06 0/360, R07 17/360, R08 34/360).**

Every one of those figures was re-verified exactly by the Stage-5 audit of v2 (V2-OK-5). The gate is
non-vacuous in a way the aggregate check was not: every stored `exponent_aware_skeleton_exact`,
`canonical_exact` and `skeleton_exact` value is 0.0 (P0c), so "reproduces 0.0" is satisfied by any
implementation that never returns a match, including a completely broken one. The **2,235** stored
component hits are the only non-degenerate signal, and 600/600 reproduction was demonstrated on a
random sample (Q3).

**Failure protocol.** Any mismatch — including a mismatch of the frozen `|H|`/`|L|` values (§7.2) or
of `m3_implementation_agreement` (§7.4) — is a **harness defect, not a finding**: halt, store the
disagreeing records at `R/phase1/m0_reproduction_failures.jsonl`, diagnose, fix only the defect,
re-run Part A **whole**, record a `DEVIATION-nn`. If it cannot be isolated within the ceiling, the
**entire cycle is `undecidable`** — the comparator of record could not be reproduced. The first
hypothesis to check on failure is a representation mismatch between prefix- and infix-derived
strings (R1).

### 7.7 Mandatory control battery (rebuilt: V2-CRIT-1, V2-CRIT-2, V2-CRIT-3)

Synthetic candidates are injected per system, tagged `positive_control_tag`, stored in a separate
artifact, and **never** enter any endpoint.

#### 7.7.0 Control well-posedness contract (new in v2.1 — the general fix for the CRITICAL root cause)

Both V2-CRIT-1 and V2-CRIT-2 have the same shape: **a control whose frozen threshold was stated as
an absolute count against a population that was never verified to have the property the control
assumes.** Four rules are frozen so that shape cannot recur.

1. **Every positive control's rewrite must be verified function-preserving.** Verification is
   `numeric_equivalent(n_points=32, seed=0)` on the parsed trees, and, where it returns within the
   guard, `_timed_simplify(orig − rewritten) == 0`. An instance failing verification is
   **`ineligible_rewrite_unverified`**, is enumerated with its expressions, and is **excluded from
   the denominator**. A control tests the matcher only on instances where the rewrite provably
   preserves the function; otherwise it tests the rewriter.
2. **Every negative control's alteration must be verified function-changing.** Same machinery,
   opposite verdict: an alteration that `numeric_equivalent` finds equivalent is a **no-op**, is
   recorded **`ineligible_alteration_is_noop`**, is enumerated, and is **excluded from the
   denominator**. This is precisely the filter v2 applied to PC3a and omitted for PC3b.
3. **Every threshold is a fraction of the realized eligible set**, never an absolute count against an
   assumed population, and every control reports `n_eligible`, `n_ineligible` and the ineligibility
   reason distribution. Each control additionally carries a **frozen minimum eligible-set size**
   below which it is reported `not_measurable` and **does not gate** — so a control can fail to be
   measurable without destroying the cycle.
4. **Gating is mapped to verdict branch by the direction of the bias the control detects, frozen
   before any `K` is observed** (§7.7.3). This is not outcome-dependent analysis: both branches are
   specified here, in advance, and no threshold changes in either.

#### 7.7.1 The battery

| control | class | construction (frozen) | eligible set | threshold | gating |
|---|---|---|---|---|---|
| **PC0** identity through M3's own path | sensitivity | call `symbolic_recovery(T_i, T_i)["skeleton"]` **directly**, bypassing `compare_formulas` entirely | all 170 components / 80 systems | **170/170 components and 80/80 systems** (measured: 170/170) | **HARD ABORT** on any failure ⇒ matcher broken ⇒ Part A `undecidable`, no verdict |
| **PC4** **gain-indicator positive control** *(new, V2-CRIT-3)* | **capability of the endpoint's own indicator** | for each truth component `T_i`, build `R_i = str(sympy.together(sympify(T_i)))`; assemble the system candidate `" \| ".join(R_i)`; inject it as a **synthetic candidate** and score it **through the same code path as the real measurement**: M0 = `formula_metrics(teacher_infix, synthetic_system)["component_exponent_aware_skeleton_exact"][i]`, M3 = `symbolic_recovery(T_i, R_i)["skeleton"]`, and `gain_pc4(i)` computed by **the identical `gain` function the primary calls** (§7.10 item 3 requires the same call site). No bypass, no bespoke matcher, no relaxed tolerance. | instances where `R_i` differs textually from `T_i` **and** the rewrite verifies function-preserving (measured: **170/170**) | **`gain_pc4_total ≥ 40`** of the eligible set **AND `gain_pc4_H ≥ 20`** (gains in stratum H) **AND ≥ 3 distinct families contribute ≥ 1 gain**. Measured (Q12): **total 100, H 100, L 0, 6 of 8 families** — margins of 2.5×, 5× and 2×. | **HARD ABORT.** Failure ⇒ Part A `undecidable (gain indicator not demonstrated)`, **`K` may not be reported for or against E0**, Part B may still run, **Part C is not run** |
| **PC4b** second gain class *(new, non-gating)* | capability, diversification | rewrite `a * X * inv(K + X)` as `a * inv(K * inv(X) + 1)` (divide numerator and denominator by `X`), bottom-up, cap 1 rewrite per component, each verified function-preserving | instances where the pattern applies and verification passes | **no threshold** — reported. Frozen as an **unverified prediction** of gain > 0 | **non-gating** |
| **PC0-CAS** CAS self-equality | instrument diagnostic, **not** an endpoint | `_sympy_components_equal(truth, truth)` directly, M1 short-circuit bypassed, **in a dedicated subprocess with `LANSR_SYMPY_MAX_NODES=200` set before interpreter start** (V2-MIN-5), asserting `formulas.SYMPY_MAX_NODES == 200` on entry | 80 systems | **reported, not gating.** Known at cap 40: **28/80** with 52/80 cap-exceeded (Q4). Expected at cap 200: 80/80. Cost bounded at 80 calls × `SYMPY_EQUIV_TIMEOUT_SEC = 10 s` = **0.22 core-h** (the per-component loop runs inside a **single** `time_limit` at `formulas.py:437`) | **non-gating**; may not invalidate any GPU_RUN5 result |
| **PC1** identity through `compare_formulas` | documentation of a known artifact | inject the truth as its own candidate | 80 systems | reported alongside PC0. `formulas.py:493-494` short-circuits `symbolic = 1.0` when `canonical_exact == 1.0`, which is why v1's PC1 gave M2 80/80 while the CAS path alone gives 28/80 | **non-gating** |
| **PC2a** P4 `neg` asymmetry | **harness-identity verification** *(reclassified, V2-CRIT-3)* | rewrite every `-1 * k * x_i` to `(-k) * x_i` — the artifact P4 identifies, in the model's own spelling | 170 components / 80 systems | **M3 = 170/170 components and 80/80 systems (Q1) AND M0 = 170/170 components and 80/80 systems (Q12b)** | **gating on harness identity only.** Any other value ⇒ the C0001 harness differs from the audited one ⇒ Part A `undecidable`. **`short_circuited: true`, non-short-circuited subset = ∅, `gain_pc2a = 0/170` by construction.** It is **not** a sensitivity control and **may not** be cited as evidence that M3 adds anything (§1.3 M-i) |
| **PC2b** affine decomposition | **`m3_affine_decomposition_limitation`** *(reclassified, V2-CRIT-1)* | `a * A^n * inv(K + A^n) → a − a*K*inv(K + A^n)`, both the folded (`a*K` as one literal) and unfolded forms, each verified function-preserving | instances matching the pattern and verifying equivalent (audit: 28 under an unverified construction; this amendment: 1 under a verified one) | **frozen expected value: 0 matches on every eligible instance** (Q14, two independent constructions agree at zero). No pass threshold; a **non-zero** value is a harness-difference `DEVIATION` and must be investigated, not reported as a finding about E0 | **non-gating, `descriptive`.** Its former role — demonstrating M3 sensitivity to an E0 mechanism — is **declared unfillable** for this mechanism (§1.3 M-ii) and its instrument-capability role is taken by PC4 |
| **PC2c** `add` commutation | sensitivity | **tree-level**: parse to `formula_views(..., as_prefix=False)["components"]`, reverse the argument order of **every n-ary `add` node bottom-up**, re-serialize with `tree_to_infix` | instances whose rewrite is textually non-trivial and verifies function-preserving (measured: **170/170**, zero unverified) | **≥ 95% of the eligible set matched by M3** (measured: 170/170 = 100%) | gating, **null branch** (§7.7.3) |
| **PC2d** `mul` commutation | sensitivity | identical, on every n-ary `mul` node | measured: **170/170**, zero unverified | **≥ 95% of the eligible set matched by M3** (measured: 170/170 = 100%) | gating, **null branch** |
| **PC3a** wrong exponent | **specificity** (negative) | truth with one realized Hill exponent altered (4→2 or 2→1) | systems with an alterable realized exponent, enumerated and reported; **48** under the auditor's rewrite, of the 24/80 carrying nested `pow` (P5). Alterations verified **function-changing** per §7.7.0 rule 2 | **≥ 95% of the eligible set scored NON-match** (measured: 48/48 = 100%, Q2) | gating, **gain branch** (§7.7.3) |
| **PC3b** permuted variable | **specificity** (negative) *(rebuilt, V2-CRIT-2)* | **frozen swap rule**: for each system of dimension ≥ 2, enumerate `(i, x_j, x_k)` with `i` the component index in ascending order and `(x_j, x_k)` the distinct variable leaves *present in component i*, `j < k`, in lexicographic order of `(i, j, k)`; the system's PC3b instance is the **first** triple whose swap verifies **function-changing**. Swap is applied on the parsed tree and re-serialized. | systems for which such a triple exists. Swaps that are **no-ops under commutativity** (e.g. R08's `x_0 * x_1`) are `ineligible_alteration_is_noop`, enumerated, excluded. Measured under the frozen rule: **eligible 60/60, 0 ineligible**; under the audit's fixed-choice rule: eligible 50, **10 ineligible, all R08** | **≥ 95% of the eligible set scored NON-match** (measured under the frozen rule: **60/60 = 100%**) | gating, **gain branch** |

**Minimum eligible-set sizes, frozen** (§7.7.0 rule 3): PC2c, PC2d, PC4 ≥ 40 components; PC3a ≥ 20
instances; PC3b ≥ 20 systems; PC2b ≥ 1 instance (else reported `not_measurable`, which is itself the
finding that the corpus carries no affine-decomposable component). Below its minimum a control is
`not_measurable` and **does not gate**; the report must say which control was not measurable and why.

**Short-circuit check, retained and now enforced** (AUDIT-CRIT-4, §7.7 of v2). For each of PC2a–PC2d
and PC4 it must be verified and reported whether the rewrite canonicalizes back to a form M0 or M1
already matches. A control whose rewrite is absorbed by `canonical_exact` tests nothing about M3's
own path; such a control is reported `short_circuited: true` with its non-short-circuited subset size
stated, **and no gate may be placed on a control whose non-short-circuited subset is empty**. This
rule is what reclassifies PC2a: M0 matches its rewrite 170/170, so its non-short-circuited subset is
∅ and v2's Gate A→B hard threshold on it as a *sensitivity* control is **removed**; what remains is
the harness-identity check, which is a claim about **reproducing two disclosed values** and is
therefore legitimate on an empty non-short-circuited subset.

#### 7.7.2 Why PC4's rewrite class is the right one, and what it does not show

**Why it is admissible.** (i) It runs through the **same code path** as the real measurement — the
same `formula_metrics`, the same `symbolic_recovery`, the same `gain` function, the same infix
representation, the same timeouts (§5 item 3). (ii) It **demonstrably produces a non-zero gain**:
100/170, all 100 in stratum H, contributed by 6 of 8 families (Q12). (iii) Its rewrite class is
**within the model's own generation support** — `inv`, `mul` and `add` all have non-zero generation
probability (P2) — so a real beam candidate *can* spell a Hill component as a common-denominator
ratio where the truth spells it multiplicatively. (iv) It exercises exactly the M3-vs-M0 difference
the primary is built on: an algebraic re-association that a constant-collapsing CAS can prove and a
canonical-tree matcher cannot.

**What it does not show, stated plainly.** PC4 is **instrument validation, not mechanism validation.**
It does not show that any real beam candidate carries such a rewrite; that is what the primary
measures. It does not restore E0's two disclosed mechanisms, one of which is absorbed by M0 and the
other out of reach (§1.3). And it is a **verification of a disclosed value** (Q12), so a non-failure
is not a discovery.

#### 7.7.3 Gating map: which control licenses which verdict (frozen before any `K` is observed)

| control class | direction of the bias it detects | effect on the primary | gates |
|---|---|---|---|
| **PC0** (identity sensitivity), **PC4** (gain capability) | an instrument that cannot produce a match, or cannot produce a *gain*, manufactures `K = 0` | fatal to **any** verdict — a null and a refutation are both uninterpretable | **both branches. HARD ABORT.** |
| **PC2a** (harness identity) | a harness differing from the one that produced Q1/Q12b invalidates every disclosed comparison | fatal to comparability | **both branches** |
| **PC2c, PC2d** (invariance sensitivity) | an M3 that fails on commutation is **under**-permissive ⇒ deflates `m3_any` ⇒ **manufactures `K = 0`** | can only push toward the null | **null branch**: if either is < 95% of its eligible set and `K = 0`, the null is **`undecidable (matcher sensitivity insufficient)`**. If `K ≥ 1`, they are reported as measured instrument facts and do not gate, because an under-permissive matcher cannot manufacture a gain |
| **PC3a, PC3b** (specificity) | an M3 that matches an altered truth is **over**-permissive ⇒ inflates `m3_any` ⇒ **manufactures `K ≥ 1`** | can only push away from the null | **gain branch**: if either is < 95% of its eligible set and `K ≥ 1`, that verdict (`weak_gain` or `matcher_attributable_gain_confirmed`) is **`undecidable (matcher specificity insufficient)`**. If `K = 0`, they are reported as measured instrument facts and do not gate, and the report must state the direction argument explicitly |
| **PC2b, PC0-CAS, PC1, PC4b** | documented limitations and instrument facts | none | **non-gating** |

**Frozen note on the legitimacy of branch-conditional gating.** Both branches are specified here,
before any `K` exists, and no threshold differs between them. What differs is only **which
verdict a given instrument failure is allowed to license** — which is a statement about the
direction of a bias, derived above and not from data. Rule 01 item 3 is not engaged: nothing is
changed to rescue a result, and the *stricter* condition applies to whichever verdict the bias could
have manufactured. The gating map is listed in §2.5 among the items whose change forces a new cycle
ID.

**Why specificity controls exist at all.** A null-shaped primary is destroyed by an over-permissive
matcher exactly as easily as by an under-permissive one, and only a specificity control detects
that. Both reviewers endorsed PC3a/PC3b for this reason. The **known general hazard**, recorded:
under constant collapsing, M3 is invariant to a variable permutation whenever the two variables
occupy structurally identical positions differing only in constants — the audit demonstrated
`symbolic_recovery("1.0*x_0 + 2.0*x_1", "1.0*x_1 + 2.0*x_0")["skeleton"] == 1.0` on an **eligible**
(function-changing) swap. This hazard **does not materialize on this corpus** (Q15: 60/60 correct),
but it is real, it is why PC3b's threshold is 95% rather than 100%, and if a reimplementation's
eligible set differs the census will expose it.

### 7.8 Secondary endpoints (Part A) — all `descriptive`, none confirmatory

No Part A secondary may carry a confirmatory claim, receive a hypothesis test, or invalidate a
GPU_RUN5 result (§9.4).

| id | endpoint | inference | note |
|---|---|---|---|
| A2-S1 | **L-stratum** gain rate, and the **H − L difference** | descriptive; cluster bootstrap | **Predicted 0 (re-derived, §7.3).** Recorded structural weakness (audit §2.2): L exists **only** in R04/R07/R08, the three families where M0 already succeeds, so if the 107 sit in L then `m0_any = 1` for many L components and any L-gain contrast is **structurally suppressed**. This endpoint is therefore weak by construction and may not be read as evidence that the gain "lives in H". |
| A2-S2 | component-level **M3 level** (not gain), overall and by stratum | descriptive; cluster bootstrap | reported so the gain has denominator context. **v2's justification ("bounded below by C-M0c under monotonicity") is withdrawn** — monotonicity is false (§7.5 item 4), so no such lower bound holds. The level is reported as a mixture with no inequality claim attached. |
| A2-S3 | `system_skeleton_equivalence_in_beam_rate_M3_ANY` over 80 systems — **v1's demoted primary** | descriptive; Wilson (`assumes_family_icc_zero: true`) **and** family-clustered | **carries no confirmatory claim.** Reported with STAT-C1's power analysis and the §9.2 clustering caveat. Not comparable to GPU_RUN5's per-cell 0/960 except at exactly zero. |
| A2-S4 | per-system **MEAN** hit fraction over the 12 cells, M3, plus per-dimension (20/30/30) and per-family (8 × 10) stratifications | descriptive | at 0/10 a family Wilson interval is [0, 0.278]; **it cannot establish family homogeneity** (STAT-m7) and must not be read that way |
| A2-S5 | cascade increment table: \|M0\|, \|M1\|, \|M3\| at candidate, component and system level; **oracle** candidate per cell per level vs **selected** candidate under the frozen selection rule (`gpu_run5_selection.py:11`) | descriptive | rule 03: generation coverage vs oracle vs selected, kept distinct. **The table may not be presented as a nested cascade**: monotonicity is false, so the three levels are reported as three sets with their pairwise intersections and differences. |
| A2-S6 | **`could_not_evaluate_rate`** and the full §7.5 failure taxonomy | **reported endpoint, frozen maximum 2.0%** | above 2.0% ⇒ primary `undecidable` |
| A2-S6b | **`m0_any = 1, m3_any = 0` component census** and the full triple-level monotonicity audit | **reported endpoint, no threshold** | the direct sibling of the primary; the check that would have caught the retracted bug. §7.5 item 4 proves it cannot affect `K`. |
| A2-S6c | **`m3_implementation_agreement`** — the §7.4 in-pass 1-in-100 double-computation census | **reported endpoint, frozen requirement 100%** | any disagreement halts Part A as a harness defect |
| A2-S7 | **statement only, not measured**: *if* a Hill-stratum gain exists, *then* a future cycle should re-examine whether GPU_RUN5's causal-intervention analysis discarded usable signal | none | In-beam component coverage (107/2040, published) and `component_exact_loss` under causal intervention are **different estimands**; v1's A-S8 moved between them illegitimately. C0001 measures neither the intervention nor any layer estimand (rule 04, §16). Routed to `hypothesis_tree.md` as a C0002 candidate. |
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
- **Control ineligibility is never an exclusion from an endpoint** — controls contribute to no
  endpoint. Ineligible control instances are enumerated with their expressions and their
  ineligibility reason and are preserved in `R/phase1/partA_controls.json` (rule 01 item 5:
  invalid and failed generated equations are preserved).

### 7.10 Frozen execution order within Part A (new in v2.1)

The order matters for two independent reasons — the integrity ordering of §7.2 and the
compute-protection purpose of the battery — so it is frozen rather than left to the implementer.

1. **Strata census.** Compute H/L, assert against the frozen Q16 values, write and hash
   `R/phase1/component_strata.json`.
2. **Realized ladder.** Compute the Wilson/OC/power tables at `|H| = 130`, assert against §7.3 and
   §9.3, write and hash `R/phase1/partA_ladder_realized.json`. Obtain the `StrataFrozenToken`
   (§7.2 step 4).
3. **Control battery, in full, on synthetic pairs only.** PC0, PC0-CAS (subprocess), PC1, PC2a,
   PC2b, PC2c, PC2d, PC3a, PC3b, PC4, PC4b, including every eligibility verification. **PC4's `gain`
   must be computed by the same function object the endpoint pass will call** — the implementation
   must expose one `gain(m0_any, m3_any)` and one per-triple scoring function and use them in both
   places; a duplicated implementation for the control is a preregistration violation. Write
   `R/phase1/partA_controls.json`. Cost ≤ 0.5 core-h (§11).
4. **Gate the hard-abort controls before spending the endpoint budget.** If **PC0** or **PC4** or
   **PC2a** fails, **stop here**: Part A is `undecidable` with the corresponding reason, no endpoint
   pass is run, ≈ 8.7 core-hours are not spent, and the cycle reports the instrument failure as its
   Part A result (§10.4). This ordering is the practical answer to V2-CRIT-1/2's "burn the full CPU
   budget to report `undecidable`".
5. **Endpoint pass** over all 47,987 candidates / 101,963 component comparisons: M0, M1 and M3
   computed independently per triple, the §7.6 reproduction check accumulated in the same pass, the
   §7.4(b) 1-in-100 implementation-agreement census accumulated in the same pass, all failure labels
   recorded. Write `R/phase1/partA_records.jsonl`, `m0_reproduction.json`,
   `partA_component_summary.json`, `partA_system_summary.json`, `partA_failures.jsonl`,
   `matcher_monotonicity.json`.
6. **Reduce and gate.** Compute the primary and all secondaries, evaluate §7.5's rates, evaluate the
   §7.7.3 gating map against the realized `K`, write `R/phase1/partA_endpoints.json` with the
   verdict, both mandated sentences and every integrity field.
7. **Only now** compute the H/L stratification of the 107 published M0 hits (§0.4, §7.2 step 3) and
   report it as **a new reduction of GPU_RUN5's own published field**, never as a C0001 discovery.

---

## 8. Part B and Part C

### 8.1 Part B — generator-support accounting (CPU only, deterministic census)

Unchanged in substance from v2; both Stage-3 reviewers endorsed its construction and its
one-sidedness, and the Stage-5 audit of v2 raised nothing against it. Every endpoint is
`descriptive` and it is in no multiplicity family.

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
deterministic traversal in the enumeration order of §8.2 step 5, each rewrite verified by
`numeric_equivalent(n_points=32, seed=0)` and **discarded and logged** as
`RewriteVerificationFailure` on failure): **B-R1** `A^n * inv(K + A^n) → 1 − K * inv(K + A^n)`;
**B-R2** fold pure-constant subtrees to a constant leaf; **B-R3** distribute `mul` over `add` **only
when it strictly lowers** the non-identity unary count; **B-R4** `neg(X) ↔ mul(-1, X)`.

**Note on B-R1 and §1.3.** B-R1 is the same algebraic move as PC2b's affine decomposition. Part B
uses it as a **unary-count reduction on the truth side only**, which is a syntactic count and needs
no matcher, so **Part B is unaffected by M3's inability to prove the identity** (Q14). The two uses
must not be confused: Part B asks *"can the generator express this at all"*; PC2b asked *"can M3
prove these two forms equal"*, and the answer is no.

**Preregistered one-sidedness.** `U_affine` is a minimum over a *bounded* rewrite set, hence an
**upper bound** on the true minimal unary count. A component reported `out_of_support` may be in
support under a rewrite outside the set. Part B's claim is therefore explicitly *"out of support
under the preregistered rewrite set"*, never *"out of support"*. **B-R1 does not rescue multi-term
components**: the affine expansion of a product of two Hill terms yields four terms with ≥ 6 unaries,
so `U_min` for such components stays > 3. **Manual hand-construction of affine encodings is
forbidden** — it would make the rewrite set investigator-dependent and unreproducible.

| id | endpoint | inference |
|---|---|---|
| B2-S1 | validation **system-level** `out_of_support_rate` (of 80) | descriptive; Wilson with `interval_interpretation` |
| B2-S2 | validation **component-level** `out_of_support_rate` (of 170) | descriptive; Wilson + cluster bootstrap |
| B2-S3 | realized-exponent histogram, train and validation, reconciled against `configs/gpu_run5/base.yaml:28 hill_exponents: [1, 2, 4]` | descriptive |
| B2-S4 | mechanism decomposition: (i) multiplicative Hill-4 single-term (`U_mult = 5`, rescued by B-R1 to 3) vs (ii) **multi-term** components (`U_mult ≥ 6`, **not** rescued) | descriptive |
| B2-S5 | per-family out-of-support rate | descriptive, underpowered |
| B2-S6 | zero-probability-operator usage by truths (expected 0/320) | descriptive; falsifies P2's scope if non-zero |
| B2-S7 | **`in_support` cross-tabulated against Part A's component strata H/L** | descriptive |

**Frozen wording.** Part B's values are **deterministic functions of a fixed corpus** — there is no
measurement noise. A Wilson interval here describes sampling variability of the **R01–R08 generator**
("at what rate does this generator emit out-of-support truths"), not estimation uncertainty. Every
artifact reporting B2-S1/B2-S2 carries
`interval_interpretation: "generator_sampling_not_measurement_error"`.

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

1. **Conditioning-identity verification (STAT-C3).** Load the cell's **input** trajectory from
   `phase3/cells/<cell_id>.json:observations["input"]` and:
   a. compute **`cell_input_payload_sha256`** — SHA256 over the float64 little-endian bytes of the
      exact arrays passed to `_point_bag`, concatenated in the frozen order
      `times ‖ observed_trajectory ‖ initial_condition`, each preceded by its shape as
      little-endian `int64`. This is a digest of **the object actually used**;
   b. assert that `system_id`, `bundle_index`, `noise_sigma` and `subsample_rho` parsed from the
      record **equal** the values encoded in `cell_id`, and that `candidate_set_hash` and
      `cache_identity` match the stored values;
   c. assert that the number of distinct `cell_input_payload_sha256` values within a system is
      **10** (P11) — a system showing 12 or 1 indicates a cell mixup or a stale cache. **This
      assertion was verified satisfiable over all 960 cell files: 10 distinct payloads in 80/80
      systems, 0 violations; the 3 clean cells 1 distinct payload in 80/80** (V2-OK-10);
   d. retain the `input_trajectory_checksum` comparison but record it as
      `system_identity_checksum_ok`, **explicitly a system-identity check, not a conditioning
      check** (80 distinct values over 80 systems, constant across a system's 12 cells, verified in
      80/80).
   Any failure marks the cell `CellIdentityMismatch` and **excludes it, counted and reported**.
   `EncoderCacheMiss` as v1 defined it is deleted: it could never fire for the stated reason.
2. Build the embedder point bag exactly as `src/gpu_run4/training.py:16 _point_bag`, run `embedder`
   + `encoder("fwd", causal=False)` **once**, cache `src_enc` for every sequence in the cell. This is
   both the compute saving and the fairness construction (§5 item 5).
3. Score with `decoder("fwd", causal=True, src_enc=..., src_len=...)` then
   `decoder("predict", tensor=..., pred_mask=..., y=..., get_scores=True)`, gathering log-softmax at
   the `pred_mask` positions, for: **GT-mult** (the stored `tree_encoded`); **GT-affine** (the Part B
   affine rewrite re-encoded via `env.equation_encoder.encode`; on failure →
   `AffineEncodingUnavailable`, logged, cell contributes GT-mult only); **each usable candidate**
   re-encoded from `candidate_formula_raw`; and **the selected candidate** under the frozen selection
   rule, identified explicitly.
   **Instrument change, declared not discovered.** `src/gpu_run4/training.py:23 teacher_forcing_loss`
   returns the **mean** CE via `get_scores=False`. C0001 **adds** a new function (it does **not**
   modify the existing one, which other phases depend on) returning
   `(sum_logprob, n_scored_tokens, per_token_logprobs)`. A regression test must assert
   `sum_logprob / n_scored_tokens == -teacher_forcing_loss(...)` to within 1e-5 on ≥ 5 fixed
   examples.
4. **Re-encoding round-trip audit** (the single largest threat to Part C, since no log-prob was ever
   stored — P9). For every candidate: `encode(parse(raw))` → `decode` → canonicalize, compared to the
   stored `candidate_formula_canonical` **after the frozen separator normalization `\|` → `,\|,`**
   (AUDIT-MAJ-7; raw equality is 20/80 and normalized equality 80/80, Q8, so an unnormalized
   comparison self-aborts Part C for a cosmetic reason).
   - exact → `candidate_reencoding_roundtrip_exact = True`, usable;
   - mismatch → `CandidateReencodingMismatch`; **excluded from the comparison distribution but
     counted and reported**;
   - > 10% of a cell's candidates mismatch → cell `unreliable_reencoding`, excluded from the Part C
     decision endpoint, reported separately;
   - > 10% of cells `unreliable_reencoding` → **Part C `undecidable`**.
   The Stage-6 smoke must demonstrate ≥ 90% exact round-trip on a known-good cell **before** Part C
   runs.
5. **Commutation-orbit report (optional mitigation of §5 item 7, gated on measured cost).**
   Enumerate the GT encoding's commutation orbit under `add`/`mul` operand swaps to a frozen cap of
   **8** orderings and report `logsumexp` over the orbit beside the single-encoding value.
   **Enumeration order, frozen (V2-MIN-7)**: index the commutable binary nodes of the GT tree in
   **pre-order (root first, left-to-right)**; the orbit is enumerated in **binary-counter order over
   that index** — orbit member `t` swaps the operands of node `k` iff bit `k` of `t` is set, for
   `t = 0, 1, 2, …, 7`; `t = 0` is the stored encoding. If the tree has fewer than 3 commutable
   nodes the orbit is the full `2^n` set and the cap does not bind. **Frozen gate**: enabled only if
   the Stage-6 smoke measures the total Part C projection at ≤ 2.0 GPU-hours with it enabled;
   otherwise dropped and the §5 item 7 bias remains disclosed-only. No orbit value may be used in
   any decision rule; it is `descriptive`.

### 8.3 Part C endpoints, the E2/E3 discriminator, and the length policy

**Length policy, frozen (STAT-M11).** An autoregressive decoder defines a normalized distribution
over variable-length token sequences, so `logP(A)` and `logP(B)` are probabilities of two events in
one sample space and comparing them is valid regardless of length. **Summed log-probability is the
only variant that is a probability comparison and the only variant that may bear a decision.**
Per-token mean log-prob is **not** the log-probability of anything, and ±20% length-matching selects
on a variable strongly correlated with structural complexity while making the analyzed set
outcome-dependent. Both are retained as `descriptive` and may not support an E2 or E3 attribution.
v1's conjunctive triple-report gave two statistics that cannot bear the interpretation **veto power
over the one that can**; it is dropped.

**THE E2/E3 DISCRIMINATOR (frozen).** Precedented by Stahlberg & Byrne
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
| C2-S5 | **per-position GT-token-rank profile** — for each GT position, the rank of the GT token in the model's predicted distribution, aggregated over cells and systems, broken out by token class (operator, mantissa, exponent, the `\|` separator) | descriptive; **strictly stronger than any rank-in-50 statistic, immune to the length confound, and costs nothing extra** since `per_token_logprobs` is already stored (STAT-M11) |
| C2-S6 | **descriptive rank panel**: `rank_pct_sum`, `rank_pct_per_token`, `rank_pct_length_matched`, `below_all_indicator` | **descriptive only**; frozen note: *the 50 candidates were drawn at T = 0.1, i.e. from p^10 renormalized, and are an extreme upper-tail sample of the model's distribution. A sequence the model ranks above 99% of everything it could emit still falls below every one of 50 such draws (STAT-C4). A low rank does not establish model error and no E2/E3 attribution may cite these.* |
| C2-S7 | **reference-resolution diagnostic**: per cell, the interquartile range of the 50 candidate summed log-probs, and the GT gap in IQR units | descriptive; gates C2-S6. Frozen: *if the GT gap exceeds 5 × IQR in more than 20% of cells, the reference distribution has no resolution and no rank-based statistic in C2-S6 may be interpreted at all* |
| C2-S8 | instrument audit: re-encoding mismatch rate, `unreliable_reencoding` cell rate, `AffineEncodingUnavailable` rate, `CellIdentityMismatch` rate, payload-digest distinct-count check, `sum/n == −mean_CE` regression result | descriptive; gates §10.1 |
| C2-S9 | GT token length vs `lp_gt` and vs `sb_sel` | **exploratory** |

**Corpus-level attribution rule (frozen, with its dead zone named).**

- **E3 (search error) predominant** iff the family-clustered 95% **lower** bound of C2-P > 0.5.
- **E2 (model error) predominant** iff the family-clustered 95% **upper** bound of C2-P < 0.5 **and**
  the clustered lower bound of C2-S1 > 0.5.
- **Otherwise `neither_E2_nor_E3_predominant`** — a real, reportable result, explicitly **distinct
  from `undecidable`**, which is reserved for instrument failure (§10.3).
- **Disclosed operating characteristic**: at `n_in_support ≈ 30–60` a proportion's 95% interval is
  0.2–0.3 wide in the middle of the range, so `neither_E2_nor_E3_predominant` is the **expected**
  corpus-level outcome. Part C's deliverable is therefore primarily the **per-system partition**
  (§10.3), which is well-defined regardless.
- **No corpus-level attribution may invalidate a GPU_RUN5 result on its own.** An E2 or E3
  attribution triggers the replication gate (§15).

**Part C null-credibility conditions.** All must hold or Part C is `undecidable`: **NC1** the
`sum/n == −mean_CE` regression test passes to 1e-5 on ≥ 5 fixed examples; **NC2** the normalized
re-encoding audit is within the §8.2 step 4 tolerances; **NC3** every scored cell passes the §8.2
step 1 identity assertions, including the 10-distinct-payload check; **NC4** the C2-S7 resolution
diagnostic is reported (its failure gates only C2-S6, since no decision depends on a rank statistic);
**NC5** `n_in_support ≥ 30`, else Part C is `exploratory` and attributes nothing.

---

## 9. Statistical plan

### 9.1 Estimators and intervals

| endpoint class | estimator | interval | note |
|---|---|---|---|
| **primary** (component-level gain rate over `\|H\| = 130`) | proportion over the component-level `gain` indicators | (a) plain **Wilson score**, z = 1.959964, no continuity correction, labeled `assumes_component_independence: true`; (b) **two-stage cluster bootstrap** percentile 95%, `numpy.random.default_rng(20260909)`, one stream, families with replacement then systems within family with replacement, **10,000** resamples; (c) **8-cluster Wilson** on the family indicator. **Interval of record: (b) if `K ≥ 1`, (c) if `K = 0`** (§7.1, V2-MAJ-3) | v1 promised "a clustered interval" and specified `src/gpu_run4/aggregation.py:22 student_t_ci`, a plain symmetric unclustered Student-t with `ddof=1`, unbounded, whose simulated coverage at a 0.05 rate is **0.909–0.913** with a **negative** lower limit 5–17% of the time (STAT-M3). **`student_t_ci` may not be used for any proportion in C0001.** The clustered estimator must be named in the Part A implementation ticket so it is not silently substituted. |
| component- and system-level proportions (A2-S1…A2-S4, B2-S1, B2-S2, C2-P, C2-S1) | proportion over the relevant indicators | Wilson + cluster bootstrap, both reported; raw limits reported, **never silently clipped** to [0, 1] | STAT-m8 |
| per-system continuous means (A2-S4 MEAN, C2-S2, C2-S3, C2-S4) | mean of per-system means | cluster bootstrap over systems and families; `student_t_ci` may be reported **beside** it, labeled unclustered | the two-stage estimator is valid regardless of within-system dependence, which is absorbed into between-system variance (STAT-OK-3) |
| control sensitivity / specificity | proportion over the **realized eligible set** (§7.7.0 rule 3) | exact counts against exact fractional thresholds; **no interval carries a decision** | every control reports `n_eligible`, `n_ineligible` and the ineligibility-reason distribution |

**Explicit invalid-test warning (endorsed by both reviewers, retained).** The natural "M3 rate minus
M0 rate" comparison at **system** level is **degenerate**: M0 is 0 for all 80 systems at system level
(P0a), so the per-system paired difference equals the M3 indicator exactly and its sampling
distribution is Bernoulli, not t. **No paired t-test is run on it**; it is reported as the Wilson
interval on the M3 indicator with the note that system-level M0 ≡ 0. This does **not** apply at
component level, where M0 is 107/2040 and the paired difference is genuinely informative — which is
why the primary lives there.

**One-sidedness labeling (STAT-m3).** Every "upper bound" in this document is the upper limit of a
**two-sided 95%** interval, i.e. a **97.5% one-sided** bound — conservative, and labeled as such. For
reference at the realized `|H| = 130`: the **one-sided 95%** Wilson upper at 0/130 is **0.0204** and
the rule-of-three approximation is **0.0231**; the **two-sided 95%** Wilson upper is **0.0287** and
Clopper–Pearson is **0.0280**. A reader comparing against a one-sided 95% bound elsewhere in the
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
**withdrawn** and the family-clustered bound is the reported result.

**Zero-count degeneracy, resolved (V2-MAJ-3).** v2 wrote: *"if the observed count is zero the ICC is
not estimable … and in that state the family-clustered bound is **automatically** the bound of
record"* — which is ambiguous between interval (b) and interval (c), and resolves the wrong way,
because §7.1 had already named (b) the interval of record and (b) is exactly `[0, 0]` when every
indicator is 0. **Frozen replacement:**
- At `K = 0` the ICC is **not estimable** (every indicator is identical) and this is reported as
  `icc_not_estimable_zero_count: true`.
- At `K = 0` the **bound of record is interval (c)**, the 8-cluster family-level Wilson,
  `0/8 → [0, 0.3244]`, carrying `interval_target: family_level_indicator_rate` so no reader mistakes
  it for a bound on the per-component rate.
- Interval (b) is still computed and reported at `K = 0`, labeled
  `degenerate_all_resamples_zero: true`, and **may not be quoted as an evidential upper bound**.
- Interval (a) is reported beside them under `assumes_component_independence: true` (value at 0/130:
  `[0.0000, 0.0287]`).
- **A bootstrap percentile upper bound of 0 may not be reported as an upper bound anywhere in this
  cycle.**

**Consequence, stated plainly.** At this corpus size an honest clustered bound is of order 0.03–0.32
and would license almost nothing on its own. **That is why the primary's inferential content is the
§7.3 powered-falsification statement and not a small-margin bound** — and why §9.5 item 1's `K = 0`
variant puts the power statement, not an interval, in the substantive position.

**Target population**: as §2.2. The finite-population reading is recorded and rejected as the
estimand.

### 9.3 The outcome ladder, realized at `|H| = 130`, with its operating characteristics disclosed

**Primary ladder** (`K` = observed Hill-stratum gains, `C = ceil(0.02 · 130) = 3`):

| observed `K` | verdict label | consequence |
|---|---|---|
| **0** | **`no_gain_observed_bound_only`** | H-C0001-P **supported**, *provided PC4 passed* (§7.7.3). Licenses **only** the §9.5 item 1 `K = 0` sentence plus the §7.3 power statement plus the §1.3 scope restriction. |
| **1 … 3** | `weak_gain` | H-C0001-P **unsupported** (not refuted). E0 operates at component resolution at a magnitude below what it needs; GPU_RUN5's component-level interpretation requires **partial revision**. Replication gate triggered. **Requires the specificity controls to have passed** (§7.7.3). |
| **> 3** | `matcher_attributable_gain_confirmed` | H-C0001-P **refuted**. E0 confirmed at the resolution that matters, **within the rewrite classes M3 can prove** (§1.3); GPU_RUN5's component-level interpretation **requires revision**. Replication gate **mandatory** (§15). **Requires the specificity controls to have passed.** |

The label was renamed from v1's `null_credible` because **labels travel downstream and caveats do
not** (STAT-M7). Every artifact carrying the verdict must also carry the §9.5 item 1 sentence and the
§1.3 scope-restriction sentence **verbatim in machine-readable fields**, the same mechanism §0.5
requires for `prior_information_disclosed`.

**Wilson and Clopper–Pearson at the realized `n = |H| = 130`** (frozen; recomputed into
`partA_ladder_realized.json` and asserted equal):

| k / 130 | Wilson 95% | Clopper–Pearson 95% upper | upper < 0.05? |
|---|---|---|---|
| 0 | **[0.0000, 0.0287]** | 0.0280 | yes |
| 1 | **[0.0014, 0.0423]** | — | yes |
| 2 | **[0.0042, 0.0544]** | — | no |
| 3 | **[0.0079, 0.0657]** | — | no |
| 4 | **[0.0120, 0.0764]** | — | no |

For the **demoted system-level secondary A2-S3** at n = 80 the corrected values of Q11 apply
(0 → [0.0000, 0.0458], 1 → [0.0022, 0.0675], 2 → [0.0069, 0.0866], 3 → [0.0128, 0.1045],
4 → [0.0196, 0.1216], 8 → [0.0515, 0.1851]); v1's ladder values were computed at n = 79 and its
"lower bound > 0.013" is reproducible by no method. At n = 80 an upper bound below 0.05 is attainable
**only** at exactly zero hits; the smallest n at which one hit still permits it is **110**, and two
hits **142**.

**Operating characteristics of the 0 / 1–3 / ≥ 4 cutpoints at `|H| = 130`, under a homogeneous
binomial (which the clustering analysis above already shows is optimistic) — disclosed, not
implied:**

| true rate p | P(K = 0) → lower rung | P(1 ≤ K ≤ 3) → middle | P(K ≥ 4) → upper rung |
|---|---|---|---|
| 0.000 | 1.0000 | 0.0000 | 0.0000 |
| 0.005 | 0.5212 | 0.4745 | **0.0043** |
| 0.010 | 0.2708 | 0.6870 | **0.0422** |
| 0.0125 | 0.1949 | 0.7240 | **0.0811** |
| 0.020 | **0.0723** | 0.6646 | **0.2631** |
| 0.030 | **0.0191** | 0.4314 | **0.5495** |
| 0.050 | 0.0013 | 0.1045 | 0.8942 |
| 0.0525 | 0.0009 | 0.0846 | 0.9145 |

**Frozen disclosure sentence, required in every artifact reporting a ladder verdict:** *"At the
realized Hill stratum size 130, the upper rung fires with probability 0.263 / 0.550 when the true
per-component gain rate is 0.02 / 0.03; the lower rung fires with probability 0.072 / 0.019 at those
same rates. Neither rung is calibrated. This is why the replication gate is mandatory for the upper
rung and why the bound — not the point estimate — is the reported result for the lower rung."*
No cutpoint moves: 0, 1 and `C = 3` are as defensible as any other choice at this n. What was
missing in v1 was the disclosure, not a different threshold.

### 9.4 Multiplicity

**Exactly one primary endpoint** (§7.1), at α = 0.05, **unadjusted**.

**The Holm plan is dropped in full** (STAT-M4). It was not executable: no null hypothesis or test
statistic was ever defined for any secondary, so there were no p-values to order; family S2 would
have corrected a **deterministic census** the plan itself correctly described as noiseless; family S1's
members are deterministic re-reductions of the same indicator set as the primary; S1's *m* was
ambiguous between 3 and 10; and S3's members carried their own uncorrected decision thresholds,
leaving the governing alpha undefined. A decorative correction is worse than none, because it
creates a false impression of error control.

**In its place, frozen:**

1. **Every non-primary endpoint is `descriptive` or `exploratory`.** None receives a hypothesis test.
   None may support a confirmatory claim, a `supported` verdict, or the invalidation of a GPU_RUN5
   result.
2. **Simultaneous coverage is stated explicitly, with `m` as a number.** Reported intervals are
   nominal 95%, and each descriptive group additionally reports **Bonferroni-widened** intervals at
   α/m: Part A **`m = 9`** (A2-S1, A2-S2, A2-S3, A2-S4, A2-S5, A2-S6, A2-S6b, A2-S6c, A2-S8; A2-S7 is
   a statement and is not an endpoint — **`m` rises from v2's 7 because A2-S6b and A2-S6c are new
   reported endpoints**), Part B `m = 7` (B2-S1…B2-S7), Part C `m = 8` (C2-S1…C2-S8). Every such
   artifact carries the frozen sentence *"these intervals are not multiplicity-controlled and no
   secondary supports a confirmatory claim."*
3. **Decision rules and estimation intervals are different objects**, and each decision rule states
   its own bound: the **primary ladder** decides on counts (0 / 1…3 / > 3) and reports a two-sided
   95% (= one-sided 97.5%) clustered bound; **Part C's attribution rule** decides on the
   family-clustered 95% bound of C2-P against 0.5; the **control battery** and the **gates** decide
   on exact counts and fractions of realized eligible sets, with no alpha at all.
4. **Cascade multiplicity is absorbed by the endpoint's construction, not by monotonicity
   (re-derived, V2-MAJ).** v2 argued that M3 dominates the cascade under `M0 ⊆ M1 ⊆ M3` so "if M3
   returns 0, every level returns 0". **That inclusion is false** (§7.5 item 4) and the argument is
   withdrawn. The correct argument needs no inclusion: the primary is **one indicator**,
   `gain = 1[m3_any ∧ ¬m0_any]`, so **exactly one test is performed on exactly one endpoint**, and no
   family of cascade-level tests exists to correct. M0's and M1's own levels appear only in the
   `descriptive` A2-S2 and A2-S5. The choice of M3 as the primary's positive level remains the
   adversarially correct one for a null-shaped hypothesis — it is the **most permissive** level *in
   intent*, and where it is not (the monotonicity violations of A2-S6b) the affected components are
   precisely those with `m0_any = 1`, which contribute 0 to `K` by definition.

### 9.5 Non-significance is not equivalence (rule 01 item 8)

Frozen wording constraints for every C0001 artifact, report and abstract.

0. **The precondition, stated first because everything below depends on it (V2-CRIT-3).** *"A primary
   observation of `K = 0` may be reported as evidence against E0 **if and only if the PC4
   gain-indicator positive control passed** (§7.7). If PC4 failed, Part A is `undecidable (gain
   indicator not demonstrated)` and no value of `K` may be cited for or against E0, because a `K = 0`
   would then be indistinguishable from an instrument incapable of producing a gain."* This sentence
   is mandatory, verbatim, in the machine-readable `verdict_scope_sentence` of every artifact
   carrying a Part A verdict.

1. **A primary observation of `K = 0` licenses exactly this and nothing more** (frozen verbatim,
   `K = 0` variant — note that **no percentile interval appears in it**, per V2-MAJ-3):
   > *"No Hill / variable-denominator truth component gained an in-beam structural match under M3
   > that the frozen M0 matcher scored as a miss (K = 0 of 130). At K = 0 the two-stage cluster
   > bootstrap percentile interval is degenerate — every resample is identically zero — and is
   > therefore **not** reported as an evidential bound. The bound of record is the family-clustered
   > 8-cluster interval on the family-level indicator, [0, 0.3244]; the naive Wilson interval on the
   > per-component rate, which assumes zero intra-family correlation, is [0.0000, 0.0287]. The
   > substantive content of this result is the design's power: it had **0.9991** probability of
   > observing at least one gain had the per-component gain rate been 0.0525 — the arithmetic lower
   > bound of the frozen matcher's own `ANY`-reduced component rate — and 0.9277 at a rate of 0.02,
   > falling to 0.7292 at 0.01. The family-clustered power at the realized stratum size is [value]
   > and is the figure quoted, being the smaller of the two."*
   For `K ≥ 1`, the same sentence is used with the count, the interval **(b)** as the interval of
   record, and the ladder rung named.
   It does **not** license: "the gain rate is zero"; "the matcher makes no difference"; "M0 and M3
   are equivalent"; "canonicalization is unnecessary"; "the two matchers agree"; any statement about
   components outside stratum H; or any statement about the E0 mechanisms excluded by §1.3.
2. **Any Part C interval containing 0 licenses only:** *"this design did not detect a difference of
   the preregistered size."* It does **not** license "GT-affine and GT-mult are equally probable"
   (C2-S4) or "the GT is as likely as the sampled candidates".
3. **A Part B rate of 0 licenses only:** *"no validation system was out of support under the
   preregistered rewrite set."* It does **not** license "the truth is in the generator's support".
4. **On equivalence claims.** The primary is a **preregistered one-sided bound with margin 0.05 on
   the Hill-stratum gain rate, evaluated as a confidence-bound inclusion test**, the standard
   one-sided analogue of TOST for a bounded rate, plus the power statement of item 1. That is
   legitimate and is specifically **not** the rule-01-item-8 error, because it asserts a bound rather
   than inferring sameness from non-significance. **No *other* equivalence claim may be made in
   C0001** — in particular no claim of equivalence between matcher levels, between the two GT
   encodings, between the GT and the sampled candidates, between strata, or between families, for
   none of which is a margin preregistered. Stage 9 enforces **this** sentence.
5. **"Not significant" is never reported as evidence of equivalence anywhere in this cycle.** Where
   an interval is wide, **the width is reported as the finding**. In particular the `K = 0` bound of
   record, [0, 0.3244], is wide, and the report must say so rather than quoting the narrower
   independence-assuming interval as if it were the result.
6. **New in v2.1 — the scope sentence.** Every artifact carrying a Part A verdict must also carry,
   verbatim: *"The affine-decomposition mechanism of E0 is not detectable by any matcher in C0001
   v2.1 under constant-collapsing skeletons, and the P4 encoding asymmetry is fully absorbed by M0
   (M0 = 170/170 on that rewrite), so the gain indicator is identically zero on it by construction.
   This verdict concerns only the rewrite classes M3 can prove, of which the demonstrated member is
   algebraic re-association / common denominator (PC4)."*

---

## 10. Go/No-Go gates, aborts, verdicts

### 10.1 Gates

**Gate 0 — pre-run; all must pass before any endpoint is computed.**

1. `git branch --show-current` == `20260909_researce_GPU_RUNclaude1`; **`git status --short` clean,
   or every entry explained in `R/manifest.json`** (V2-MAJ-7: at the time of the v2 audit the tree
   carried `M src/evaluation/equation_metrics.py` (+86/−19, `to_skeleton` and `symbolic_recovery`
   refactored), `M src/gpu_run4/records.py` (+17, additive `FAILURE_REASONS`), `M src/gpu_run5/config.py`
   (+13, additive `sealed*` guard) and `?? src/gpu_runclaude1/` (6 modules, 929 lines). The audit read
   the full diff and judged the `equation_metrics.py` refactor **value-preserving for `["skeleton"]`
   on every input**, but the M3 implementation of record was edited before this gate returned, which
   is a process defect against rule 05. **Required**: commit with a manifest explanation, and pass
   Gate 0 item 11.) **The tree has since grown beyond that snapshot** — at the time of writing v2.1 it
   additionally carries `M pytest.ini` (adds `GPU_RUNclaude1/tests` to `testpaths`),
   `M src/gpu_run4/training.py` (**additive**: a new `teacher_forced_summed_logprob` returning
   `(sum_logprob, n_scored_tokens, per_token_logprobs)`, with `teacher_forcing_loss` itself untouched —
   exactly what §8.2 step 3 requires), `?? GPU_RUNclaude1/tests/` and
   `?? scripts/phases/gpu_runclaude1_c0001_phase{0,1,2,3,4}_*.py`. Gate 0 therefore **enumerates
   `git status --short` at run time** and explains every entry then; the snapshot above is recorded only
   because it is what the v2 audit judged. **Two entries carry a specific verification requirement**:
   `src/gpu_run4/training.py` must be shown to leave `teacher_forcing_loss` **byte-identical** (§8.2
   step 3, §17), and `src/evaluation/equation_metrics.py` must pass Gate 0 item 11 (§7.4, V2-MAJ-2).
2. **`pytest GPU_RUN5/tests/test_gpu_run5_firewall.py GPU_RUN5/tests/test_gpu_run5_phase8.py -k "firewall or sealed or test_open"` green — all selected tests, currently 6** (V2-MIN-3: v2 said "4 tests"; the selector matches on the **filename**, so both tests in `test_gpu_run5_firewall.py` are selected including `test_nonfinite_values_are_sanitized_for_strict_json`, which is not a firewall test. The gate is "all selected green", not an exact count) — **plus** the new C0001-specific firewall test of §2.4 item 9 green, **plus** `pytest GPU_RUN5/tests --collect-only` collecting **124** tests with **zero** collection errors. `PYTHONPATH=.` is **not** required: `pytest.ini` already carries `pythonpath = .` (V2-MIN-2).
3. **A fresh Stage-5 reproducibility audit of the *v2.1* design reports zero CRITICAL findings.** The
   audit of v2 stated the re-audit **can be narrow**: it needs to confirm only (i) the amended
   control battery — PC2b's declassification, PC3b's eligibility rule and threshold, and **PC4's
   construction, its same-code-path property and its thresholds**; (ii) the `K = 0` bound of record
   and the §9.5 sentence variants; (iii) the restated effect size; (iv) the §1.3 scope restriction;
   (v) the §2.4 interception mechanism and sealed inventory. Everything in the v2 audit's §8 (16
   verified positives) is already confirmed and need not be re-derived. Additionally
   `grep -rn sealed` over the C0001 diff shows no direct sealed read.
4. Checkpoint SHA256 == `56754040be5aa92ed4767fc43ee2008faa293f87c12b643e66c7df3e1623a5e8`.
5. Input SHA256 recorded for every file on the §2.4 item 5 allowlist; **no directory argument was
   passed to `run_manifest.py`**; the `sys.addaudithook` guard is installed and
   `sealed_paths_read` is **computed and empty**; `R/phase0/sealed_inventory.json` written with ≥ 7
   entries and an empty intersection against the allowlist.
6. GPU 0 idle temperature < 70 °C; free VRAM ≥ 6.0 GiB (measured 7,154 MiB free at 49 °C, Q9); disk
   free ≥ 40 GiB (measured 117 G).
7. Stage-6 smoke on `phase4/fixed_grn_validation_panel.json` (24 systems) completes, writes a
   manifest, equation records and failure records, demonstrates resume, **demonstrates `_time_limit`
   firing inside a worker process**, and demonstrates ≥ 90% normalized re-encoding round-trip on a
   known-good cell.
8. **Measured Part A cost calibration (§11.1) completed and within budget**, with the frozen
   constraint that no match indicator produced during timing calibration was aggregated, stored,
   printed, logged or read, and that the artifact contains **per-family aggregates only** (V2-MIN-8).
9. `R/phase1/component_strata.json` and `R/phase1/partA_ladder_realized.json` written and hashed,
   their values **asserted equal** to the frozen Q16 / §7.3 / §9.3 tables, and the
   `StrataFrozenToken` obtainable (§7.2 step 4) **before** any match indicator is computed on a real
   stored candidate.
10. New run directory does not already exist (verified: no `results/runs/gpu_runclaude1*`; 27
    existing run directories plus one stray log file = 28 entries).
11. **M3 implementation-agreement test green (§7.4, V2-MAJ-2)**: 100% bit-identical `["skeleton"]`
    agreement between `symbolic_recovery(...)["skeleton"]` and any substitute implementation over the
    910 synthetic control pairs.
12. **Interception tests green (§2.4 item 7c/7d, V2-MAJ-6)**: a direct `open()` on a sealed path from
    inside `src/gpu_runclaude1/` raises `SealedPathAccessError`, and the AST check reports zero
    unguarded file-read call sites in any C0001 module.

**Gate A → B.** Proceed to Part B only if **all** hold. Items marked **HARD** are evaluated in §7.10
step 4, **before** the endpoint pass:

| # | condition | branch |
|---|---|---|
| (i) | the M0 arm reproduces **all 47,987 stored per-candidate fields and all 101,963 component comparisons exactly**, including the 2,235 component ones, and the reduced values 0/960 (system, mean over cells), 107/2040 (component) and all eight per-family counts — §7.6 | both |
| (ii) | **HARD — PC0 = 170/170 components and 80/80 systems** | both |
| (iii) | **HARD — PC4 passes: `gain_pc4_total ≥ 40` of its eligible set AND `gain_pc4_H ≥ 20` AND ≥ 3 distinct families contribute a gain** | both. **Failure ⇒ Part A `undecidable (gain indicator not demonstrated)`, no `K` reported for or against E0, Part C not run** |
| (iv) | **HARD — PC2a harness identity: M3 = 170/170 components and 80/80 systems AND M0 = 170/170 components and 80/80 systems** | both |
| (v) | PC2c ≥ 95% and PC2d ≥ 95% of their realized eligible sets matched by M3 | **null branch only** (§7.7.3): binding when `K = 0` |
| (vi) | PC3a ≥ 95% and PC3b ≥ 95% of their realized eligible sets scored NON-match | **gain branch only**: binding when `K ≥ 1` |
| (vii) | `could_not_evaluate_rate` ≤ **2.0%** | both |
| (viii) | `m3_implementation_agreement` = 100% | both |
| (ix) | the §7.6 reproduction protocol was not triggered, or was triggered and resolved | both |

**Removed from Gate A→B relative to v2**: PC2b's `≥ 76/80` (V2-CRIT-1 — unachievable by
construction), PC3b's absolute `≥ 58/60` (V2-CRIT-2 — replaced by (vi)), PC2a's *sensitivity*
threshold (V2-CRIT-3 — replaced by (iv), a harness-identity check), and the **monotonicity ≤ 1%**
condition (V2-MAJ — the expectation it tested is false and violations provably cannot affect `K`).

*If a gating control fails, Part B may still proceed* (independent instrument, no shared matcher),
but Part A is reported with the corresponding `undecidable` reason and **Part C is not run**.

**Gate B → C.** Proceed to Part C only if **both**:
(i) Part A is **not** `undecidable`. If Part A lands on `matcher_attributable_gain_confirmed`,
**Part C is not run in C0001**: the premise has changed and the correct next move is replication of
Part A (§15), not a diagnosis of a failure whose extent has just moved.
(ii) `n_in_support ≥ 30` validation systems are fully in support **and** have Part A component gains
= 0 — i.e. in-support truths that were still never generated. If `n_in_support < 30`, Part C runs but
is reported **exploratory** and attributes nothing.

**Gate C → report.** Part C endpoints are reported only if NC1–NC3 pass (§8.3). Otherwise Part C is
`undecidable`.

### 10.2 Abort and crash-loop conditions

- Cumulative GPU 0 time > **4.0 h**, or CPU > **24 core-hours**, or new disk > **15 GiB** ⇒ abort the
  running part, preserve partial artifacts, report what completed.
- **Peak VRAM on GPU 0 > 5.5 GiB ⇒ abort immediately**, and — new in v2.1 (V2-MIN-10) — the ceiling
  is additionally enforced as an **allocator cap**: Part C calls
  `torch.cuda.set_per_process_memory_fraction(5.5 / 8.0, device=0)` before the first allocation, so
  an overrun raises rather than being detected up to 10 s later by the telemetry sampler. GPU 0 is
  shared with the user's live desktop (~629 MiB already held), and `nvidia-smi`-visible totals include
  that desktop allocation, which is why a sampled tripwire alone was insufficient. Preregistered
  fallback chain, in order: Part C batch size to 1 → the §14 reduced cell design → GPU 1 (GTX 1060
  3 GB, forward-only, batch 1). The chain changes **which cells** are scored, never the numerics:
  fp32 throughout, never fp16, never CPU, so log-probability comparability is preserved.
- GPU 0 temperature > 85 °C sustained 60 s ⇒ pause, cool, resume once.
- **Crash-loop rule (rule 06)**: **3 consecutive identical fatal failures with no new diagnostic
  information ⇒ stop and reassess.** Record the three tracebacks and their identical signature in the
  cycle report, classify the bottleneck via `negative-result-recovery`, and end the cycle. A failed
  hypothesis does not justify more compute.
- **Projected-throughput abort**: if the §11.1 measured calibration projects Part A > **12
  core-hours** or the Stage-6 smoke projects Part C > **2.0 GPU-hours**, invoke the §14 reduced
  designs **before** starting, not midway.

### 10.3 Supported / unsupported / undecidable

**For the primary hypothesis H-C0001-P:**

| verdict | criterion |
|---|---|
| **supported** | Gate A→B passed in full **including PC4** (§10.1 (iii)); primary `K = 0`; reported as the §9.5 item 1 `K = 0` sentence **plus** the §7.3 power statement **plus** the §9.5 item 6 scope sentence, with interval (c) as the bound of record |
| **unsupported** | Gate A→B passed in full, including the **gain-branch** specificity conditions (vi); `1 ≤ K ≤ 3` (`weak_gain`) |
| **refuted** | Gate A→B passed in full, including (vi); `K > 3` (`matcher_attributable_gain_confirmed`); replication gate mandatory; the claim is bounded by §1.3 to the rewrite classes M3 can prove |
| **undecidable** | **PC4 fails** ⇒ `undecidable (gain indicator not demonstrated)`; **or** PC0 ≠ 170/170; **or** PC2a ≠ its two known values (harness differs); **or** `K = 0` and PC2c or PC2d < 95% of its eligible set ⇒ `undecidable (matcher sensitivity insufficient)`; **or** `K ≥ 1` and PC3a or PC3b < 95% of its eligible set ⇒ `undecidable (matcher specificity insufficient)`; **or** M0 fails exact reproduction; **or** `\|H\|`/`\|L\|` differ from the frozen Q16 values; **or** `m3_implementation_agreement` < 100%; **or** `could_not_evaluate_rate` > 2.0%; **or** the §7.5 item 3 two-sided sensitivity analysis disagrees on the rung; **or** the strata/ladder artifacts were not written and the token not obtained before matching; **or** `\|H\| < 40` and the fallback primary is also unmeasurable; **or** the run aborted before the primary was computed |
| **underpowered_bound_only** | `40 ≤ \|H\| < 100` and realized power to detect 0.0525 < 0.90, with `K = 0`. Reportable; **may not be cited as refuting E0.** **Does not fire at `\|H\| = 130`** (power 0.9991). |

**For the four-way mechanism attribution** (secondary; reported as a **partition**, never a single
winner):

| mechanism | attributed to a component or system when |
|---|---|
| **E0** | that **component** has an M3 in-beam match that M0 scored as a miss (`gain = 1`), reported separately for stratum H and stratum L, **and always with the §1.3 restriction attached** |
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
| **Part A** | `K = 0` bounds E0 at the resolution that matters, over the rewrite classes M3 can prove, and quantifies the power of that bound. `K > 0` locates E0 by stratum and by family. **Either way** the cycle delivers: the first exact reproduction of GPU_RUN5's 47,987 stored matcher fields (C-M0f); the first component-type stratification of its 107 published component matches; the M0/M1/M3 three-set increment table with its measured **non-inclusion**; a measured `could_not_evaluate` rate for the CAS-free skeleton path; PC0-CAS's measured verdict on whether the repository's CAS path can recognize a GRN truth as itself; and — new in v2.1 — a measured, preregistered statement of **what the instrument can and cannot prove** (PC2b's zero, PC4's 100/170, PC2a's absorption by M0), which is a reusable instrument characterization for every later cycle. **If a hard-abort control fails at §7.10 step 4, that failure is the reportable Part A result and ≈ 8.7 core-hours are not spent** — v2 would have spent them to report the same `undecidable`. |
| **Part B** | `out_of_support_rate = 0` refutes E1' for this corpus and is reportable. Non-zero quantifies it and decomposes it into multiplicative-Hill-4 vs multi-term mechanisms, the second of which the original brief did not name. The H/L cross-tabulation (B2-S7) is informative either way. |
| **Part C** | The expected corpus-level outcome is `neither_E2_nor_E3_predominant`, and that is **reported as a result**, not a failure. The per-system partition, the per-position GT-token-rank profile (C2-S5) and the reference-resolution diagnostic (C2-S7) are delivered regardless of which label the corpus-level rule returns. If the re-encoding audit fails, the finding is that GPU_RUN5's stored candidate strings do not round-trip through the model's own tokenizer — a first-order reproducibility fact about the artifact store. |

---

## 11. Compute ceiling and the measured cost basis

**No ceiling increase is requested**, and the ceiling is unchanged from v2: **≤ 4.0 GPU-hours,
≤ 5.5 GiB VRAM, ≤ 24 CPU-core-hours, ≤ 15 GiB new disk.**

| resource | ceiling | v2.1 allocation | basis |
|---|---|---|---|
| GPU 0 (RTX 2070, 8,192 MiB total / 7,154 MiB free measured, **shared with the user's live desktop**) | **≤ 4.0 GPU-hours** | Part C ≤ 2.0 h; Stage-6 smoke ≤ 0.3 h; reserve 1.7 h | unchanged; Part C's work is unchanged in kind |
| peak VRAM on GPU 0 | **≤ 5.5 GiB**, now an **allocator cap** (§10.2) | Part C target ≤ 3.0 GiB | 60.6M params fp32 ≈ 242 MB weights, cached `src_enc` per cell, batch ≤ 8, seq ≤ 200 |
| CPU | **≤ 24 core-hours** | **Part A ≤ 12** · Part B ≤ 2 · Part C host-side ≤ 2 · **total ≤ 16, slack 8** | **measured**, see §11.1 |
| new disk | **≤ 15 GiB** | ≈ 3–6 GiB under `R/` | assessed sound at both audits |
| RAM | 60 GiB total / 52 GiB available (measured) | ≤ 6 worker processes at **0.53 GiB** each ≈ 3.2 GiB (Q18) | measured, V2-OK-9 |
| GPU 1 (GTX 1060 3 GB) | forward-only fallback | only under the §10.2 chain | — |

### 11.1 The revised measured basis for Part A

**Measured in the v2.1 configuration (Q17, `lansr310`, 120 real GRN candidates, 15 per family,
`random.seed(20260909)`, `formula_metrics` + `compare_formulas(skip_cas=True)` + per-component
`symbolic_recovery`):**

```
M0 mean  45 ms     M1 mean  16 ms     M3 mean 594 ms
M0+M1+M3 mean 655 ms    median 608    p95 1480    max 1992
projection for 47,987 candidates: 8.73 single-core-hours
by family (ms): R01 770  R02 226  R03 794  R04 338  R05 631  R06 906  R07 927  R08 647
```

**This replaces v2's basis.** v2 argued from Q6 (795 ms/candidate for the **M1+M2+M3** cascade →
10.60 core-h) that "removing M2 strictly removes work, so 10.60 core-h is a measured upper bound".
The gap in that argument was that **M0 was not in Q6's measurement**, so the removal was not
automatically net-negative. It is: M0 adds 45 ms and removing M2 saves more, and the direct
measurement of the actual v2.1 configuration gives **655 ms → 8.73 core-h**, comfortably below
v2's claimed bound.

**The `:195-205` equiv block is inside this figure (V2-MAJ-1).** v2 believed that block dead and
therefore did not budget for it. The 655 ms measurement calls `symbolic_recovery` — the eager path —
so the two `sympify` calls, the `:200 _timed_simplify` and `:203 _approximately_equivalent` are all
included. **No upward correction is needed, and any substitute implementation that skips the block
(§7.4) can only be faster.**

**Bounded additions to the 8.73 core-h endpoint pass:**

| item | cost | basis |
|---|---|---|
| control battery (≈ 1,316 synthetic comparisons: PC0 170, PC1 80, PC2a 170, PC2b ≤ 28, PC2c 170, PC2d 170, PC3a 48, PC3b 60 + eligibility search, PC4 170, PC4b 170) | ≈ **0.25 core-h** | at the measured 594 ms M3 mean, plus `numeric_equivalent(n_points=32)` eligibility checks at ≈ 1 ms each |
| PC0-CAS | ≤ **0.22 core-h** | 80 calls × `SYMPY_EQUIV_TIMEOUT_SEC = 10 s` worst case; the per-component loop runs inside a **single** `time_limit` (`formulas.py:437`), and Q7's truth node totals (max 48, doubled to ≤ 96 for truth-vs-truth) sit well inside a cap of 200 |
| §7.4(b) in-pass implementation-agreement census (1 in 100) | ≈ **0.08 core-h** | ≈ 480 extra M3 calls |
| §11.1 timing calibration (400 candidates) | ≈ **0.07 core-h** | 400 × 655 ms |
| §7.5 failure-reason instrumentation overhead | not separately measured; gated by the calibration | — |
| M0 exact-reproduction pass | **0** | it is a by-product of the same endpoint pass |
| **total** | **≈ 9.35 core-h against a 12 core-h allocation and a 24 core-h ceiling** | |

**What is honestly not measured**, and is therefore gated rather than assumed: (a) the overhead of
the §7.5 failure-reason instrumentation; (b) wall-clock under 6-process parallelism; (c) the
eligibility-search cost of PC3b's frozen rule on the worst-case system.

**Frozen requirement (Gate 0 item 8): a measured calibration before the full run.** Sampling frame
frozen: **400 candidates, 50 per family**, drawn from `phase3/all_candidates.json` with
`numpy.random.default_rng(20260909)`, scored through the exact v2.1 Part A pipeline, **timing only**.
Report **per-family** mean, median and p95; project `mean × 47,987`. If the projection exceeds **12
core-h**, the §14 item 4 reduced design applies **before** starting.

**Integrity constraint on the calibration, frozen and tightened (V2-MIN-8).** The calibration harness
must **discard the match boolean at the call site**, before any aggregation. No match indicator
produced during timing calibration may be stored, printed, logged, aggregated or read by any agent,
and `R/phase0/partA_cost_calibration.json` contains **per-family aggregates (mean, median, p95) and
failure-label counts only**. **Per-candidate timings are forbidden in that artifact**, because
per-candidate wall time is a **side channel on the match indicator** — a proved match exits at
`equation_metrics.py:189` while a non-match additionally runs `_timed_equals` at `:190` — and the
calibration sample is drawn from the **same** 47,987 candidates the primary scores. Per-family
aggregates leak negligibly; per-candidate timings would leak materially. A calibration artifact
containing per-candidate timings or any match rate has leaked the endpoint and Part A becomes
`undecidable`.

---

## 12. Run ID and artifact contract

**Run ID.** `gpu_runclaude1_c0001_<short7>`, `<short7>` = the first 7 characters of the git commit
**at run start**. If the directory exists, append `_v2`, `_v3`, …; **never overwrite** any of the 27
existing `results/runs/*` directories (rule 05). Verified: no directory begins with
`gpu_runclaude1`. `git reset --hard` and force-push are forbidden. Branch and commit are recorded in
every manifest via `scripts/ops/run_manifest.py`, **with the §2.4 item 5 file-level allowlist only**.
`campaign` must be passed through to `write_manifest`, which hardcodes
`{"campaign": "GPU_RUN5", ...}` at `src/gpu_run5/config.py:45` (AUDIT-MIN-4), so C0001 phase
manifests are not mislabelled.

### 12.1 Expected artifacts

Run root **`R = results/runs/gpu_runclaude1_c0001_<short7>/`**. Every `R/` below is literal.

| path | content |
|---|---|
| `R/manifest.json` | branch, commit, **the commit that introduced this preregistration**, `pip freeze`, GPU + driver, checkpoint SHA256, **per-file** input fingerprints, per-phase status, `campaign: GPU_RUNclaude1_C0001`, and the explanation of every `git status --short` entry |
| `R/phase0/environment_audit.json` | env, GPU/temp/VRAM, disk, library versions |
| `R/phase0/checkpoint_audit.json` | checkpoint SHA256 + size + persisted generator config |
| `R/phase0/firewall_test.json` | the §10.1 items 2, 5 and 12 results; **computed** `sealed_paths_read`; the audit-hook installation record; the AST-check report |
| `R/phase0/sealed_inventory.json` | the §2.4 run-time enumeration: ledger entries, name-only census, per-file `ledger_status`, and the empty intersection against the allowlist |
| `R/phase0/input_fingerprints.json` | SHA256 of every allowlisted path actually opened |
| `R/phase0/partA_cost_calibration.json` | §11.1 — **per-family aggregates and failure-label counts only** |
| `R/phase0/m3_implementation_agreement.json` | the §7.4(a) 910-pair synthetic agreement test |
| `R/phase1/component_strata.json` | the §7.2 H/L assignment for all 170 components, `\|H\|`, `\|L\|`, per-family and per-dimension breakdown, the assertion result against Q16, file SHA256. **Written before any matching.** |
| `R/phase1/partA_ladder_realized.json` | the realized-`\|H\|` Wilson table, ladder cutpoint `C`, OC table and power table, asserted equal to §7.3 / §9.3. **Written before any matching.** |
| `R/phase1/partA_controls.json` | PC0, PC0-CAS, PC1, PC2a, PC2b, PC2c, PC2d, PC3a, PC3b, **PC4, PC4b**; each with `n_eligible`, `n_ineligible`, the ineligibility-reason distribution, the enumerated ineligible instances **with their expressions**, `short_circuited`, the threshold, the pass/fail, the gating branch, and Gate A→B's per-item outcome |
| `R/phase1/partA_records.jsonl` | one record per (cell, candidate, component); extended schema (§13) |
| `R/phase1/m0_reproduction.json` | the §7.6 exact-reproduction result over 47,987 candidates / 101,963 component comparisons / 2,235 stored component hits / eight family counts |
| `R/phase1/m0_reproduction_failures.jsonl` | written **only** on a reproduction mismatch |
| `R/phase1/partA_component_summary.json` | per component: `m0_any`, `m1_any`, `m3_any`, `gain`, stratum, family, dimension |
| `R/phase1/partA_system_summary.json` | per-system `ANY` and `MEAN` indicators at each level |
| `R/phase1/partA_endpoints.json` | primary + A2-S1…A2-S6c, A2-S8, with intervals (a)/(b)/(c), the **bound of record** and its selection reason, Bonferroni-widened intervals at α/9, the reported ICC or `icc_not_estimable_zero_count`, and the verdict with **both** mandated sentences (§9.5 items 0/1 and 6) in machine-readable fields |
| `R/phase1/partA_failures.jsonl` | every could-not-evaluate, timeout, parse error, non-finite and monotonicity violation, with both expressions **and both derivation paths** |
| `R/phase1/matcher_monotonicity.json` | the three-set `M0 / M1 / M3` audit with pairwise intersections and differences, and the `m0_any=1, m3_any=0` census (A2-S6b) |
| `R/phase1/m0_hits_stratification.json` | the H/L stratification of the 107 published M0 component hits, computed **only** at §7.10 step 7, labeled **a new reduction of GPU_RUN5's own published field** |
| `R/phase2/partB_component_records.jsonl` | per component: realized exponents, `U_mult`, `U_affine`, `U_min`, `in_support`, all three budget checks |
| `R/phase2/partB_rewrites.jsonl` | every attempted rewrite with its numeric-verification outcome |
| `R/phase2/partB_endpoints.json` | B2-S1…B2-S7 with `interval_interpretation` |
| `R/phase2/partB_in_support_systems.json` | the Part C eligibility list and `n_in_support` |
| `R/phase3/partC_cell_records.jsonl` | per (cell, sequence): token length, summed log-prob, per-token log-probs, encoding tag, `cell_input_payload_sha256`, round-trip result |
| `R/phase3/partC_identity_audit.json` | §8.2 step 1 assertions, including the 10-distinct-payload check per system |
| `R/phase3/partC_reencoding_audit.json` | normalized mismatch rates, `unreliable_reencoding` cells, `AffineEncodingUnavailable` |
| `R/phase3/partC_endpoints.json` | C2-P, C2-S1…C2-S9, the attribution-rule outcome, the disclosed dead-zone statement |
| `R/phase3/partC_instrument_test.json` | the `sum/n == −mean_CE` regression test |
| `R/phase3/gpu_telemetry.jsonl` | VRAM/temperature samples at ≤ 10 s interval, plus the allocator-cap setting |
| `R/phase4/mechanism_partition.json` | the five-bucket partition at component and system resolution |
| `R/phase4/compute_accounting.json` | GPU-hours, CPU-core-hours, disk, against the ceiling |
| `GPU_RUNclaude1/analyses/C0001_analysis.md` | Stage 8 analysis |
| `GPU_RUNclaude1/reviews/C0001_statistical_review_stage8.md` | Stage 8 statistical review — a **separate file**, so it does not overwrite the Stage-3 review (STAT-m9) |
| `GPU_RUNclaude1/reviews/C0001_v2_reproducibility_audit.md` | the fresh Stage-5 audit of **v2** (exists; the object of this amendment). v2 §12.1 named it `C0001_reproducibility_audit_v2.md`, which does not exist; **this row is the corrected name** |
| `GPU_RUNclaude1/reviews/C0001_v2.1_reproducibility_audit.md` | the narrow Stage-5 re-audit of **v2.1** required by Gate 0 item 3 |
| `GPU_RUNclaude1/reviews/C0001_independent_review.md` | Stage 9 adversarial review |
| `GPU_RUNclaude1/reports/C0001_report.md` | Stage 11 cycle report (**mandatory even if null / undecidable / aborted**) |
| `GPU_RUNclaude1/reports/C0001_replication.md` | §15, recorded separately, never merged into the primary result |
| `GPU_RUNclaude1/manifests/C0001_artifact_manifest.json` + `C0001_checksums.sha256` | Stage 12 |
| `GPU_RUNclaude1/plans/C0001_preregistration_v2.1.md` / `.json` | this file and its machine twin |
| `GPU_RUNclaude1/plans/C0001_preregistration_v2.md` / `.json` | **v2, superseded, retained unmodified** |
| `GPU_RUNclaude1/plans/C0001_preregistration.md` / `.json` | **v1, superseded, retained unmodified** |

Large artifacts (`partA_records.jsonl` expected ~0.5–2 GiB) are **not committed**; paths and SHA256s
are preserved in the manifest (rule 05).

---

## 13. Record schema (rule 03)

**Base**: the 30-field `src/gpu_run4/records.py:7 GPU_RUN4_REQUIRED_FIELDS`, **extended, never
replaced**, via `:76 make_formula_record(**extra)`. `campaign = "GPU_RUNclaude1_C0001"`. The rule-03
distinction between **generation coverage**, **oracle candidate** and **selected candidate** is
preserved in the field set and in every reduction.

**Added fields.**

*Part A matcher* — `matcher_level`, `m0_string_exponent_aware_skeleton_exact` (name retained for
continuity with the stored GPU_RUN5 field; **it is a canonical-tree criterion, not a string one**,
§4), `m0_component_exponent_aware_skeleton_exact`, `m1_canonical_exact`, `m3_skeleton_equivalent`,
`component_m3_skeleton_equivalent`, `component_index`, `component_stratum` (`H` | `L`), `m0_any`,
`m1_any`, `m3_any`, **`gain`**, `derivation_path` (`infix` for both sides, always), `match_outcome`
(`matched` | `proved_different` | `could_not_evaluate`), `matcher_failure_reason`, `cas_wall_time_sec`,
`monotonicity_violation`, `m0_reproduces_stored_field`, **`m3_implementation_agreement_checked`**,
**`m3_implementation_agreement_ok`**.

*Rule-03 completeness* — `true_components_infix`, `candidate_components_infix`, `variable_to_gene`,
`variable_precision`, `variable_recall`, `variable_f1`, `unnecessary_variables`, `near_singularity`,
`extrapolation_valid`, `extrapolation_extreme`, `has_division`, `has_tan`, `complexity`, `ted_raw`,
`ted_skeleton`, `normalized_ted`, `component_normalized_variable_aware_ted`.

*Generation vs selection* — `generation_coverage_scope` (`cell` | `component` | `system`),
`oracle_candidate_index_by_level`, `selected_candidate_index_by_rule`, `candidate_return_shortfall`,
`n_usable_candidates`.

*Controls* — `positive_control_tag` (`none` | `PC0` | `PC0_CAS` | `PC1` | `PC2a` | `PC2b` | `PC2c` |
`PC2d` | `PC3a` | `PC3b` | **`PC4`** | **`PC4b`**), `control_class` (`sensitivity` |
`specificity` | `capability` | `harness_identity` | `limitation` | `diagnostic`),
`control_expected_outcome`, `control_eligible`, **`control_ineligibility_reason`**
(`none` | `ineligible_rewrite_unverified` | `ineligible_alteration_is_noop` |
`ineligible_pattern_absent`), `control_short_circuited`, **`control_gating_branch`**
(`both` | `null` | `gain` | `none`), **`control_rewrite_verification`** (the
`numeric_equivalent` result for the instance).

*Part B* — `u_mult`, `u_affine`, `u_min`, `in_support`, `realized_hill_exponents`, `unary_depth`,
`binary_ops_per_dim`, `uses_only_in_support_operators`, `rewrite_verification_outcome`,
`out_of_support_mechanism` (`multiplicative_hill4` | `multi_term_component` | `other` | `none`).

*Part C* — `gt_encoding` (`mult` | `affine` | `orbit`), `gt_logprob_sum`, `gt_token_length`,
`candidate_logprob_sum`, `candidate_token_length`, `is_selected_candidate`, **`sb_sel`**, `sb_best`,
`sb_rate`, `gt_logprob_per_token`, `candidate_logprob_per_token`, `per_token_logprobs`,
`gt_token_rank_profile`, `candidate_logprob_iqr`, `gt_gap_in_iqr_units`, `rank_pct_sum`,
`rank_pct_per_token`, `rank_pct_length_matched`, `below_all_indicator`, `cell_input_payload_sha256`,
`system_identity_checksum_ok`, `candidate_reencoding_roundtrip_exact`,
`candidate_reencoding_mismatch`, `cell_reliability_flag`, `orbit_member_index`.

*Integrity* — `prior_information_disclosed` (mandatory, non-empty, naming §0.1–§0.4 of **v2.1**, on
every artifact carrying a Part A endpoint), **`control_is_verification_of_disclosed_value`**,
`inference` (`primary` | `descriptive` | `exploratory` | `statement_only`), `interval_interpretation`,
**`interval_target`** (`component_gain_rate` | `family_level_indicator_rate`),
**`bound_of_record`**, **`degenerate_all_resamples_zero`**, **`icc_not_estimable_zero_count`**,
`verdict_scope_sentence` (the §9.5 item 1 sentence **and** the §9.5 items 0 and 6 sentences, verbatim,
on every artifact carrying a ladder verdict), `assumes_component_independence`,
`assumes_family_icc_zero`, **`e0_mechanism_scope`** (the §1.3 restriction, machine-readable:
`{"M-i": "absorbed_by_M0", "M-ii": "no_instrument", "M-iii": "tested"}`).

**`FAILURE_REASONS` extension** — the existing enum at `src/gpu_run4/records.py:50` is **kept intact**;
C0001 appends exactly: `CanonicalizationError`, `RewriteVerificationFailure`,
`AffineEncodingUnavailable`, `CandidateReencodingMismatch`, `NumericEquivalenceNonFinite`,
`PositiveControlFailure`, `MatcherMonotonicityViolation`, `LengthMatchUnavailable`,
`SkeletonParseFailure`, `SkeletonEvaluationFailure`, `SymbolicEquivalenceTimeout`,
`SymbolicNodeCapExceeded`, `ComponentCountMismatch`, `CellIdentityMismatch`, and — new in v2.1 —
**`EquivBlockTimeout_NonEndpoint`** (§7.5 item 1), **`SealedPathAccessError`** (§2.4 item 7),
**`ControlIneligible`**. `EncoderCacheMiss` from v1 is **removed** — it could never fire for the
reason v1 gave.

**Failure / exclusion policy (frozen).** Nothing is silently dropped. Every invalid, failed,
timed-out or unparseable equation is written with its `failure_reason` and counted in the denominator
of its own diagnostic rate (rule 01 items 4 and 5). **Preserved invalid equations include every
non-matching control instance and every ineligible control instance, with its expressions.** The
**only** permitted exclusions, each counted and reported: (a) candidates failing the Part C
re-encoding round trip, from the Part C comparison distribution only; (b) cells flagged
`unreliable_reencoding`, from the Part C decision endpoint only; (c) cells flagged
`CellIdentityMismatch`, from Part C only; (d) cells flagged `LengthMatchUnavailable`, from the C2-S6
descriptive panel only; (e) **ineligible control instances, from that control's denominator only** —
never from any endpoint, since controls contribute to none.
**No exclusion of any kind is permitted from the Part A primary endpoint.**

---

## 14. Deviation policy

General rule: preserve original artifacts, append a dated `DEVIATION-nn` block to **this** file, and
either mark the affected endpoint **exploratory** or open a new preregistered cycle. Never edit
frozen text; **never change a threshold to rescue a result** (rule 01 item 3).

Named contingencies, decided **now**:

1. **`could_not_evaluate_rate` non-zero.** ≤ 2.0% → proceed, report as A2-S6, **and** run the
   two-sided sensitivity analysis of §7.5 item 3; if the two directions land on different rungs, the
   verdict is `undecidable`. > 2.0% → `undecidable`. **No timeout value is raised mid-cycle** — that
   would change the frozen instrument.
2. **A needed stored field is absent.** Verified present at freeze: `candidate_formula_raw`,
   `candidate_formula_canonical`, `candidate_exponent_aware_skeleton`, `true_formula`, `true_prefix`,
   `teacher_components_infix`, `teacher_components_prefix`, `tree_encoded`, `teacher_token_length`,
   `valid`, `failure_reason`, `complexity`, the TED fields, `trajectory_metrics`,
   `observations{input, selection, generalization}`, `structure.component_flags[i].variable_denominator_form`.
   Verified **absent**: `symbolic_equivalent`, any log-prob or score field. On absence, recover from
   `phase3/cells/<cell_id>.json`; if still absent the dependent endpoint is dropped, marked
   `not_measurable_from_stored_artifacts`, and reported. **The primary depends only on
   `candidate_formula_raw` and `teacher_components_infix`, both verified present**, so no field
   absence can void it.
3. **An affine encoding cannot be constructed (Part C).** Log `AffineEncodingUnavailable`; `U_affine`
   falls back to `U_mult`, making `U_min = U_mult` — the **conservative** direction, which
   over-reports out-of-support, and the report must say so. C2-S4 is dropped if > 20% of in-support
   systems lack one. **Hand-construction is forbidden.**
4. **Part A projected > 12 core-hours** by the §11.1 measured calibration. Reduced design, chosen
   **now**: **6 cells per system** = `{bundle_index 0, 1, 2} × {(σ=0, ρ=0), (σ=0.05, ρ=0.5)}` → 480
   cells, ≈ 24,000 candidates, ≈ 4.4 core-h at the measured 655 ms rate. The endpoint definitions are
   unchanged; only the number of cells entering the `ANY` union shrinks, which **weakens** the primary
   (fewer chances to observe a gain), so a zero under the reduced design must be reported with the
   reduced coverage and the **recomputed power** stated explicitly. This deliberately differs from
   v1's reduced design (`bundle_index == 0`, all 4 corruptions), which kept the four *most mutually
   dependent* cells and discarded all between-bundle variation — the dimension GPU_RUN5 measured
   **least** stable (Spearman 0.480 / Kendall 0.389). v2.1's subsample spans all three bundles at the
   same compute (STAT-M13).
5. **Part C projected > 2.0 GPU-hours.** The same 6-cell design, then batch 1, then GPU 1 (§10.2
   chain). The commutation-orbit report (§8.2 step 5) is dropped **first**, before any cell is
   dropped.
6. **M0 fails exact reproduction of the stored fields**, or `|H|`/`|L|` differ from Q16, or
   `m3_implementation_agreement` < 100%. Harness defect, not a finding: §7.6 protocol; if unresolved,
   the **entire cycle is `undecidable`**.
7. **`|H|` falls outside 130** (the measured value). Record a `DEVIATION` noting the discrepancy
   against a **measured, disclosed** quantity — which is a harness defect, not a prediction miss —
   and apply item 6.
8. **The strata or ladder artifacts were not written and hashed, or the `StrataFrozenToken` was not
   obtained, before matching.** Part A is `undecidable`. There is no remedy short of a new cycle ID,
   because the integrity ordering that makes the primary unobserved cannot be reconstructed after the
   fact.
9. **A gating control fails.** Apply §7.7.3's map and §10.3's `undecidable` reasons. **No control
   threshold may be lowered, no control redefined, and no eligible set re-derived after the fact**
   (rule 01 item 3). If PC4 fails, the correct next move is a new cycle that finds a gain-capable
   rewrite class on the **train** split before freezing, not an amendment to this one.
10. **A control's realized eligible set falls below its §7.7.1 minimum.** The control is reported
    `not_measurable` and **does not gate** (§7.7.0 rule 3). The report must name it and say why. If
    **PC4** is `not_measurable`, that is equivalent to PC4 failing: Part A is `undecidable (gain
    indicator not demonstrated)`.
11. **PC2b returns a non-zero value.** Record a `DEVIATION`: two independent measurements found 0
    (Q14), so a non-zero value means the harness differs. Investigate as a harness difference; it is
    **not** reported as a finding about E0, and it does not change the §1.3 scope restriction unless
    the discrepancy is resolved in favor of the new harness, which would require a new cycle.

---

## 15. Replication gate (rule 07, `replication-gate`)

**Trigger, preregistered.** The gate fires if **any** of: (i) the primary lands on `weak_gain` or
`matcher_attributable_gain_confirmed` — a revision or invalidation of a prior published campaign
interpretation, exactly the high-impact case rule 07 reserves the gate for; (ii) the independent
reviewer marks any Part A result fragile; (iii) Part C returns an E2 or E3 corpus-level attribution;
(iv) the component-type stratification of the 107 contradicts the §7.3 `partly_derivable_prediction`
in a way that changes a stated conclusion.

**Minimum replication design, frozen, with at least one independent factor changed:**

| factor | C0001 | replication |
|---|---|---|
| **corpus** | GPU_RUN5 GRN validation, 80 systems / 170 components, Hill-type | **GPU_RUN4 ODEBench**, `results/runs/gpu_run4_phase0_01/phase2/all_candidates.json`, 12,632 candidates, 63 physics/biology systems — different corpus, different generation run, different dimensionality mix |
| **process / path** | this run | fresh process, clean checkout at a recorded commit, independent run ID `results/runs/gpu_runclaude1_c0001r_<short7>/` |
| **agent** | implementation + primary analysis | executed by `lansr-replication-specialist`, distinct from implementer and primary analyst |
| **matcher seed** | **not available, and v1's claim that it was is corrected** | With M3 pinned to `["skeleton"]`, the primary matcher contains **no RNG at all**: `numeric_equivalent(seed=...)` is reachable only from M2's fallback (`formulas.py:498`), which v2.1 does not run, and M3's numeric grid is hard-coded and non-random (`equation_metrics.py:84-85`, `base = [0.2, 0.7, 1.3, 1.9]`, `+ 0.11 * index`) with no `points` or `seed` parameter. **Note the v2.1 correction (V2-MAJ-1): that grid *is* executed on every M3 call, via the eager dict at `:207-212`; it simply cannot change `["skeleton"]` and is not random.** The primary instrument is deterministic; no seed change can perturb it (AUDIT-MAJ-8). The replication varies corpus, process and agent only, stated plainly rather than dressed up as a seed perturbation. |

The ODEBench arm carries a **built-in corpus-level positive control**: the frozen matcher reports
4/252 = 1.59% [0.0062, 0.0401] truth-in-beam there (C-ODEB), so the cascade must reproduce a non-zero
baseline. **v2.1 correction**: v2 also required "M3 ≥ M0 on that corpus". That requirement is
**withdrawn** — monotonicity is false (§7.5 item 4) and M3 can legitimately be less permissive than
M0 on individual pairs. The replication requirement is: **M0 reproduces 4/252, and the three-set
M0/M1/M3 table is reported with its intersections and differences.** A cascade that returns 0 for M0
on ODEBench is broken, independently of anything it says about GRN. **PC4 must also be run and pass
on the replication corpus**, since a gain indicator that cannot fire there would make the ODEBench
arm as uninterpretable as the GRN one.

**Recorded outcome classes**: `replicated` · `directionally_replicated` · `failed_replication` ·
`inconclusive`. Recorded **separately** at `GPU_RUNclaude1/reports/C0001_replication.md`, never
merged into the C0001 primary result. Per rule 07, a CRITICAL reviewer finding blocks a supported
conclusion regardless of the replication outcome.

---

## 16. Rule 04 — layer analysis contract

**C0001 measures none of the six layer estimands.** No probe/readout (information availability), no
CKA/similarity (representation geometry), no gradient (optimization signal), no ablation/intervention
(causal necessity), no IOLE/single-layer fine-tuning (adaptation capacity), no selective fine-tuning
(multi-layer adaptation). **Nothing is averaged into a layer ranking. No layer-importance claim may
appear in any C0001 artifact.** The v2 audit verified this by `grep` across the whole document
(V2-OK-15) and the same must hold for v2.1.

The one layer-adjacent item is **A2-S7**, a *statement of a testable consequence for a later cycle*,
not a measurement. v1 wrote: *"if A-S3 > 0, then GPU_RUN5's `component_exact_loss = 0.0` at all 16
layers was not at the floor."* The retraction establishes that this conflated two distinct estimands
— **in-beam component coverage** (already 107/2040, published) and **exact recovery of the selected
candidate under causal intervention** (`component_exact_loss`) — and that moving between them is
illegitimate. A2-S7 therefore states only that the *question* of whether the intervention floor is
genuine remains **open and untested**, and routes it to `hypothesis_tree.md` as a C0002 candidate.
C0001 tests neither and must not imply that it has.

---

## 17. Required reviews before the full experiment

Per the `experiment-preregistration` skill, all three reviews must be current **against v2.1** before
Stage 7, each by an agent distinct from the implementer. The v1 Stage-3 reviews do not carry over;
the **v2 Stage-5 reproducibility audit does carry over for its 16 verified positives**, and Gate 0
item 3 requires only the **narrow re-audit** enumerated there.

| review | agent | must confirm, specifically for v2.1 |
|---|---|---|
| **methodology** | `lansr-research-methodologist` | that E0/E1'/E2/E3 remain mutually discriminating under the §1.3 scope restriction; that the H/L stratum definitions are decidable and non-degenerate; that the gain endpoint is still the right operationalization of E0 **given that only M-iii is reachable**; that PC4's rewrite class is a defensible instrument control and is **not** being passed off as a mechanism; that Part C's restriction to the in-support subset is correct; that cutting M2 and Part D does not remove a needed discrimination **beyond what §1.3 already concedes** |
| **statistical** | `lansr-statistical-reviewer` | the three-level unit hierarchy and the aggregation order; the cluster-bootstrap specification, generator, draw order and seed; the **`K = 0` bound-of-record rule and the prohibition on a degenerate percentile bound**; the ICC conditional and its zero-count degeneracy; the realized-`\|H\| = 130` ladder, OC and power tables; the **restated effect size** and the `[0.053, 0.629]` admissible range; the §9.4 re-derived multiplicity argument **that no longer uses monotonicity**; the §9.5 sentence variants; the **branch-conditional gating map of §7.7.3** and whether it is legitimately outcome-independent; the Part C discriminator's thresholds and disclosed dead zone; that no endpoint uses `student_t_ci` for a proportion |
| **reproducibility** | `lansr-reproducibility-auditor` | the §2.4 run-time sealed inventory, the **`sys.addaudithook` interception**, the sole-path requirement and the two new tests; that no `run_manifest.py` call receives a directory; the pinned M3 key **and the implementation-agreement test**; process-based parallelism and the worker-timeout assertion; the §7.5 failure taxonomy covering **every** silent non-match surface **including `:200`**; the §7.2 write-before-match ordering **and the `StrataFrozenToken` gate**; the §11.1 calibration's outcome-suppression constraint **and the per-family-aggregates-only restriction**; the §7.10 execution order and the hard-abort-before-endpoint-pass property; that `teacher_forcing_loss` is **extended, not modified**, and that **`equation_metrics.py` is extended, not modified** |

**Stage 9 independent review is additionally instructed** to check that: no artifact presents the
component-type stratification of the 107 as anything other than a **new reduction of GPU_RUN5's own
published field** (R1); no artifact presents 107/2040 as a C0001 discovery or as a matcher defect; no
artifact reads a zero primary as an equivalence claim; no artifact cites a Part A or Part C secondary
as confirmatory; **no artifact calls M0 a "string matcher"**; **no artifact presents PC4's 100/170 as
evidence that real candidates carry that rewrite**; **no artifact reports a `K = 0` verdict without
the §9.5 items 0, 1 and 6 sentences**; and **no artifact generalizes the verdict past §1.3's scope
restriction**. Any such framing is a **MAJOR** finding.

---

## 18. What was cut, and the reviewer amendments declined

### 18.1 Cut: the M2 arm and A-S1 (declined amendment), and what that now costs

**Declined**: the v1 reviewers' amendment to fix `SYMPY_MAX_NODES` by raising it to ≥ 200 and
retaining M2/A-S1 as an endpoint.

**Reason (rule 06).** `SYMPY_MAX_NODES = 40` is a **combined** truth+candidate budget, and
`src/gpu_run4/formulas.py:434` returns `0.0, None` above it with **no** failure reason. Measured: the
CAS path answers "does this GRN truth equal **itself**?" with *no* for **52/80** systems, and
**55.1%** of 3,000 real pairs exceed the cap, with R06/R07/R08 at **100%** (Q4, Q5). This is
conservative for a recovery score and **anti-conservative for a null-shaped claim**, and it is
invisible to a failure budget and to a monotonicity check, because a spuriously empty M2 is
monotonicity-*consistent*. So M2 as v1 froze it is unusable. Fixing it pushes R05–R08 into full
`simplify()` on 40–90-node trees at up to 10 s each: ≈ **66 core-hours** against a **24 core-hour**
ceiling — a rule-06 hard stop requiring human approval, which this cycle will not request for a
**secondary** endpoint. The Stage-5 audit of v2 independently endorsed the cut (audit §5.3).

**Consequence, stated as the rules require.** M2 and A-S1 are **cut, not downgraded**: no M2 endpoint
exists, so no M2 result — confirmatory, descriptive or exploratory — can be reported, and none can
invalidate a GPU_RUN5 result. Two substitutes preserve part of what M2 was for: (a) the primary uses
**M3**, which has **no node cap**, is verified sensitive on identity (PC0 170/170) and on commutation
(PC2c/PC2d 170/170), verified specific on exponents (PC3a 48/48) and on variable permutation (PC3b
60/60), and verified **capable of producing a gain** (PC4 100/170); (b) **PC0-CAS** runs
`_sympy_components_equal(truth, truth)` on all 80 systems at cap 200, at a bounded 0.22 core-h, and
**reports** whether the repository's CAS path can recognize a GRN truth as itself. That measured
instrument fact is a deliverable of this cycle and belongs in `research_state.md` §8 defect 8
regardless of what Part A concludes.

**New in v2.1 — the cost of the cut, stated explicitly (audit §5.3, V2-CRIT-1).** With M2 gone, **M3
is the sole permissive level, and M3 collapses constants.** Therefore **E0's affine-decomposition
mechanism has no instrument in this cycle at all**: M0 and M1 are stricter, M3 provably cannot prove
the identity (Q14), and M2 — the only level that does not collapse constants and could in principle
prove it — is cut. v2 listed the two substitutes and omitted this consequence. It is now a **frozen
scope restriction on what C0001 can conclude about E0** (§1.3 M-ii), it appears in the mandatory
`verdict_scope_sentence`, and it is the primary motivation for the C0002 candidate "constant-preserving
CAS equivalence at a node budget that covers the GRN corpus, with a compute ceiling that admits it".

### 18.2 Cut: Part D

v1's Part D (denominator-arity classification of the 1,860 ODEBench variable-denominator candidates)
is **cut**. It bears on no C0001 endpoint, sharpens a C0002 question rather than this cycle's, and a
cycle that answers one question cleanly beats parts that each answer nothing. Routed to
`hypothesis_tree.md`. No compute is reallocated to it.

### 18.3 Not cut, but demoted to `descriptive`

v1's primary (the system-level M3 `ANY` rate) is retained as **A2-S3** because it is a free
deterministic roll-up of indicators the primary already computes. It carries **no** confirmatory
claim, cannot invalidate a GPU_RUN5 result, and must be reported with the STAT-C1 power analysis, the
§9.2 clustering caveat and the frozen non-comparability sentence of §2.1.

### 18.4 Reclassified rather than cut in v2.1

| element | v2 | v2.1 | why not cut |
|---|---|---|---|
| **PC2b** | gating sensitivity control, `≥ 76/80` | non-gating `m3_affine_decomposition_limitation`, expected 0 | ≈ 20 s of compute; a non-zero value proves a harness difference against two independent measurements; and it is the empirical basis of §1.3 M-ii, which is one of this cycle's real deliverables |
| **PC2a** | gating sensitivity control, `≥ 80/80` for M3 | gating **harness-identity** verification on **both** M0 and M3, `short_circuited: true` | it still detects a harness that differs from the one producing Q1/Q12b, which would invalidate every disclosed comparison. Only its *interpretation* as evidence of M3 sensitivity is removed |
| **monotonicity audit** | gating: `> 1%` ⇒ CRITICAL ⇒ `undecidable` | reported endpoint A2-S6b, no threshold | it is the exact check that would have caught the retracted representation bug; only the false expectation and the burn hazard are removed |
| **PC1** | non-gating documentation | unchanged | documents a real artifact (`formulas.py:493-494`) at negligible cost |

### 18.5 Amendments accepted in full

Every required amendment from all three reviews is accepted except those listed in the Amendment
record's "declined" table: STAT-C1…C4, STAT-M1…M13, STAT-m1…m9, AUDIT-CRIT-1…4, AUDIT-MAJ-1…9,
AUDIT-MIN-1…11, **V2-CRIT-1…3, V2-MAJ-1…7, V2-MIN-1…10**, plus the audit's §2.4, §5.3 and §5.4
recommendations. The commutation-orbit mitigation (STAT-M9) remains accepted **conditionally**, gated
on the Stage-6 measured cost (§8.2 step 5); if the gate fails, the bias remains disclosed with its
magnitude and no decision depends on it.

---

## 19. Compact statement of what is frozen

primary hypothesis **H-C0001-P** · the single primary endpoint
**`hill_component_matcher_attributable_gain_rate`** over the frozen Hill stratum, with **interval (b)
as the bound of record for `K ≥ 1` and interval (c) for `K = 0`**, and the prohibition on reporting a
degenerate percentile bound · the **§1.3 scope restriction** on which E0 mechanisms are reachable
(M-i absorbed by M0, M-ii without an instrument, M-iii the tested class) · the **H/L stratum
definitions**, the realized `|H| = 130` / `|L| = 40` / `C = 3`, and the requirement that the strata
and the realized ladder be **written, hashed and token-gated before any match indicator on a real
candidate** · the **§7.3 predictions**, with the L-stratum prediction **re-derived to 0** and the
stratification prediction relabelled `partly_derivable` · the **M0 / M1 / M3** cascade with M3 pinned
to `symbolic_recovery(...)["skeleton"]`, both sides fed **infix**, the three levels computed
independently, **no code assuming monotonicity**, and the implementation-agreement test · the
exclusion of M2 and the scope cost of that exclusion · the three-level unit hierarchy and the
within-component-then-across-components aggregation order · the `ANY` reduction and its
non-comparability sentence · the **effect size restated on the endpoint's own reduction**, with
0.0525 as the arithmetic lower bound of `[0.053, 0.629]` · the target population and the ICC
conditional · the cluster bootstrap (`numpy.random.default_rng(20260909)`, one stream, families then
systems, 10,000 resamples) · the outcome ladder `0 / 1…3 / >3` with its realized OC and power tables ·
the **control battery PC0, PC0-CAS, PC1, PC2a, PC2b, PC2c, PC2d, PC3a, PC3b, PC4, PC4b**, the
**well-posedness contract** (verified rewrites, verified alterations, thresholds as fractions of
realized eligible sets, minimum eligible-set sizes), and the **gating map** (§7.7.3) · **PC4 as a
hard-abort gate and the rule that `K = 0` is evidence against E0 only if PC4 passed** · the §7.10
execution order, which gates the hard-abort controls **before** the endpoint pass · the failure
taxonomy including the `:200` surface, and the **2.0% `could_not_evaluate` maximum** · the §7.6
exact-reproduction gate over all 47,987 candidates and eight family counts · Part B's rewrite set
B-R1…B-R4, its 200-rewrite cap and the `U_min ≤ 3` criterion · Part C's restriction to the in-support
subset, the **summed-log-prob-only** policy, the **paired Stahlberg–Byrne discriminator** and its 0.5
thresholds, the `cell_input_payload_sha256` identity protocol, the `|` ↔ `,|,` normalization, the
10%/10% re-encoding tolerances, the orbit enumeration order and NC1–NC5 · the §9.5 equivalence
wording and its three mandatory verbatim sentences · the Go/No-Go gates · the supported / unsupported
/ refuted / undecidable / underpowered criteria · the exclusion and failure policy · seeds (global
20260909; bootstrap `default_rng(20260909)`; `numeric_equivalent(seed=0)` for Part B and for control
eligibility; the primary matcher is deterministic) · zero training, zero tuning, zero adaptation,
zero new decoding · the compute ceiling (**4 GPU-h, 5.5 GiB VRAM enforced as an allocator cap, 24
CPU-core-h, 15 GiB disk**) and the **measured 8.73 core-h endpoint basis inside a 12 core-h
allocation** · the §11.1 calibration, its outcome-suppression constraint and its
per-family-aggregates-only restriction · the crash-loop rule · the run ID rule · the artifact list ·
the replication design · the sealed-test firewall, its run-time inventory, its file-level allowlist
and its audit-hook interception.

---

## 20. Required follow-ups outside this document

Recorded here so they are not lost, since this amendment is scoped to
`C0001_preregistration_v2.1.md` / `.json` only and modifies nothing else.

1. **`research_state.md` §8: add a defect** recording that `scripts/phases/gpu_run5_phase4.py:118-119`
   and `:151-152` hash `sealed_official_test.json` outside any test-open ledger, that the resulting
   digest `2860d829d9077d01258489fb68ed8dcd8a333d6a0e150b8e36b301f28bb1e070` is the value the campaign
   records for that seal, and that this bears on whether that seal is usable as a clean confirmation
   set for a future cycle (§2.4a). **Correct §4's row** from "UNSPENT — generated, never evaluated …
   The only clean seal available" to the precise status of §2.4a.
2. **`research_state.md` §4: correct the sealed inventory** from 3 artifacts to the 7 that exist
   (Q19), noting that 5 have no ledger entry.
3. **`research_state.md` §8 defect 6**: mark the `ModuleNotFoundError` claim **withdrawn as
   non-reproducing** (it is already noted as not reproducing under defect 1; defect 6 still states it
   as fact).
4. **`research_state.md` §8b**: consider adopting a standing rule **R2** from this amendment's root
   cause: *before freezing any control threshold, verify that the population the control assumes
   actually has the property the control tests — positive-control rewrites verified
   function-preserving, negative-control alterations verified function-changing — and state every
   threshold as a fraction of the realized eligible set.* Both v2 CRITICALs in the control battery
   were instances of violating this.
5. **`hypothesis_tree.md`**: add the C0002 candidate *"constant-preserving CAS equivalence at a node
   budget covering the GRN corpus"*, motivated by §1.3 M-ii and §18.1, alongside the existing Part D
   and A2-S7 routings.
6. **Gate 0 item 3**: commission the **narrow** Stage-5 re-audit of v2.1 (§10.1 item 3) by an agent
   distinct from this amendment's author.
7. **Gate 0 item 1**: commit the working tree (`src/evaluation/equation_metrics.py`,
   `src/gpu_run4/records.py`, `src/gpu_run5/config.py`, `src/gpu_runclaude1/`) with a manifest
   explanation, before any run.

---

**Signed off (Stage 3, amendment v2.1)**: cycle `C0001`, preregistration **v2.1**, branch
`20260909_researce_GPU_RUNclaude1`, authored at HEAD `7f507cc`, completed at HEAD `7c7d96a`, 2026-09-09.
**v1 (`C0001_preregistration.md`) and v2 (`C0001_preregistration_v2.md`) were not modified by this
amendment.**
