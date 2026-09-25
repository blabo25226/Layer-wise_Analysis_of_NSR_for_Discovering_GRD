# C0001 preregistration v2 closure review response

- task: C0001-T005
- implementer: Cursor Agent
- reviewer packet: `preregistration_v2_closure_review.md`
- revised artifact: `preregistration_draft_v3.md`
- date: 2026-09-13
- verdict requested: second independent review (`ready_for_second_independent_review`)

## Summary

v3 closes all closure blockers (C-A–C-F), major findings (M-a–M-h), and moderate items from the v2
independent closure review. The scientific question is unchanged in spirit: does the production-like
rescaling → simplification → classification chain systematically reject oracle-equivalent strict-Hill
representations at the component level? v3 re-derives the truth-side denominator (330 components,
1,320 primary scale pairs), freezes a fixed-denominator mutually exclusive outcome partition, corrects
the B1 counterfactual, models simplifier semantics with external timeouts, and supplies a complete
confirmatory counted-call table totaling **23,370** logical invocations.

---

## Blocker closure map

| ID | Review finding (abbrev.) | v3 closure | Status |
|---|---|---|---|
| **C-A** | Primary readout must be `component_flags[idx].hill_form`, not `formula_metrics` | §2.1 freezes `classify_formula(E2_infix)["component_flags"][component_idx]["hill_form"]`; forbids system-level OR; `formula_metrics` secondary only | **CLOSED** |
| **C-B** | Strict-Hill denominator is 330 components / 1,320 pairs, not 390 / 1,560 | §2.2 re-derives 11 strict-Hill per family slice × 30 = 330; 330 × 4 = 1,320; modulated 60 reported separately; linear 120 excluded from primary denominator | **CLOSED** |
| **C-C** | Call ceiling wrong; omitted prechecks and E1 oracle work | §8.1–§8.3 define counted-call primitive; §8.3 operations table lists registration prechecks, B0 E1/E2 oracles, B1–B4, B3, N1; confirmatory total **23,370** (not patched subtotal) | **CLOSED** |
| **C-D** | B1 was scaled-vs-unscaled forbidden comparison | §3.2 B1 builds identity E0 at `s=1, a_t=1, b_t=0` once per component (510 units, not ×4 scales); §6 table | **CLOSED** |
| **C-E** | Simplifier semantics not modeled | §3.4 records `expand=False, resimplify=False`, 4-decimal rounding, swallowed internal 1s timeout; audit uses 4-decimal constants, single-thread subprocess, external 5s timeout; drift vs structural FN separated | **CLOSED** |
| **C-F** | Denominator conditioned on E2 outcome | §2.2 freezes truth-side 1,320 pairs; §2.2 five-way mutually exclusive partition over same denominator; proportions sum to 1 | **CLOSED** |

---

## Major finding closure map

| ID | Review finding (abbrev.) | v3 closure | Status |
|---|---|---|---|
| **M-a** | Primary rule gained secondary conjuncts | §1 single existence rule; §10 controls as validity gates evaluated before hypothesis; control FAIL → undecidable | **CLOSED** |
| **M-b** | Scaler path / `rescale_features` / fit trajectory | §5 `SymbolicTransformerRegressor(params=None)` path; asserts `rescale_features=true`; synthetic trajectory `np.full(..., s)` at earliest time | **CLOSED** |
| **M-c** | Timeout values not frozen | §3.4 external simplifier 5.0s; §3.5 oracle 30.0s; §13.1 CAS 60.0s; internal 1s documented as non-observable | **CLOSED** |
| **M-d** | Equivalent rewrite role / seed | §3.2 primary E0 from preverified non-identity rewrite; `audit_rewrite_seed=61003`; registration P2 precheck | **CLOSED** |
| **M-e** | Serialization / prefix dialect unspecified | §3.6 raw prefix + emitted infix at E0/E1/E2; `neg` handling; `pow2` vs `x**4` skeleton note | **CLOSED** |
| **M-f** | Sealed-path guard vacuous | §11 globs derived from `configs/gpu_run5/base.yaml`; match counts including zero; fresh R07/R08 generation allowed | **CLOSED** |
| **M-g** | `rescale_incomplete` is construction failure | §2.2, §9: `execution_failure`, never structural FN | **CLOSED** |
| **M-h** | Resume key and commands incomplete | §12 resume key `(condition, pair_id)`; §13 all seeds, timeouts, hashes; resume verifies audit_id, commit, hashes, seeds | **CLOSED** |

---

## Moderate finding closure map

| Item | v3 closure | Status |
|---|---|---|
| Rename invariance rate | §2.4 `linear_canonical_noninvariance_rate` | **CLOSED** |
| Remove inert `audit_scale_seed` | §4.2 full deterministic cross product; §7 seed table omits scale seed | **CLOSED** |
| One completion threshold | §10 G1: 95% of 23,370 confirmatory calls (≥ 22,202) | **CLOSED** |
| B4 scale-independent | §6 B4: 510 components once | **CLOSED** |
| Component flags not system OR | §2.1 explicit forbid system-level OR | **CLOSED** |
| Forbid thread-parallel simplification | §3.4 single-thread subprocess only | **CLOSED** |
| Autonomous-system precondition for omitting τ | §3.1 | **CLOSED** |
| CPU override without mutating base.yaml | §13.1 `--allow-cpu` CLI only | **CLOSED** |
| Existence gate thin; no post-hoc prevalence | §0, §1 | **CLOSED** |

---

## v2 → v3 disposition (selected)

| v2 element | v3 disposition | Rationale |
|---|---|---|
| 390 Hill / 1,560 primary pairs | 330 strict-Hill / 1,320 pairs | C-B |
| `formula_metrics` as primary readout | `component_flags[idx].hill_form` | C-A |
| Oracle-eligible denominator post-E2 | Truth-side frozen 1,320 + 5-way partition | C-F |
| B1 identity scaler on scaled E0 | Identity-built E0 once per component | C-D |
| Confirmatory ceiling 8,260 | Confirmatory ceiling 23,370 | C-C |
| Primary rule + control conjuncts | Single rule + validity gates | M-a |
| `linear_canonical_invariance_rate` | `linear_canonical_noninvariance_rate` | moderate |
| `audit_scale_seed` | removed | moderate |

v1 and v2 drafts remain untouched.

---

## Acceptance self-check

| Test | Evidence |
|---|---|
| Component-level primary readout | §2.1 |
| 330 / 1,320 denominator re-derived | §2.2, §4.1 |
| Fixed mutually exclusive partition | §2.2 |
| Complete operations table | §8.3 |
| B1 identity E0 | §3.2, §6 |
| Simplifier + external timeout contract | §3.4 |
| Controls as gates, one hypothesis rule | §1, §10 |
| Sealed-path guard from config | §11 |
| Resume `(condition, pair_id)` + full commands | §12–§13 |
| C-A–C-F, M-a–M-h, moderate closed | tables above |

---

## Items for second independent review

1. Confirm 330 strict-Hill component derivation matches `classify_formula` on generated corpus at `audit_data_seed=61001`.
2. Confirm 23,370 confirmatory call arithmetic and B2 sharing convention (E0/E1 in B0 rows; B2 adds E1-stage metrics only).
3. Confirm five-way outcome partition is mutually exclusive and complete for all execution paths.
4. Confirm sealed-path globs cover GPU_RUN5 holdout layout without blocking permitted fresh generation.

---

## Implementer attestation

- `preregistration_draft.md` and `preregistration_draft_v2.md` were not edited.
- No implementation, experiment execution, sealed artifact access, or push was performed.
- Section references verified against `preregistration_draft_v3.md` before commit.
