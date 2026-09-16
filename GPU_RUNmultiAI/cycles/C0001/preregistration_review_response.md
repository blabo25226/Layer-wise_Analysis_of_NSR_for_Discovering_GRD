# C0001 preregistration review response

- task: C0001-T005
- implementer: Cursor Agent
- reviewer packet: `preregistration_independent_review.md`
- revised artifact: `preregistration_draft_v2.md`
- date: 2026-09-13
- verdict requested: independent re-review (`ready_for_independent_review`)

## Summary

v2 closes all ten findings (C1–C3, M1–M7) named in the independent review.
The scientific question is unchanged: does the production-like rescaling → simplification →
`formula_metrics(skip_cas=True)` chain systematically reject oracle-equivalent Hill representations?
Claims are narrowed to **non-invariance and undercounting**; prior syntactic exact results are not wholesale invalidated.
One primary endpoint (`hill_false_negative_rate` with an existence decision rule), one confirmatory compute tier (8,260 calls),
CPU-only execution, and no decode are frozen.

---

## Finding closure map

| ID | Review finding (abbrev.) | v2 closure | Status |
|---|---|---|---|
| **C1** | E0 forward construction undefined; need E0→E1→E2 chain and independent oracle | §3 defines E0 analytic full-system forward scaling $g_i(z)=\frac{s_i}{a_t}f_i(z/s)$; E1=`rescale_function`; E2=`simplify_tree`; primary FNR only on oracle-confirmed E2; E1-equiv/E2-nonequiv → `simplifier_semantic_drift_rate` (§2.3); independent analytic + numeric oracle (§3.5) | **CLOSED** |
| **C2** | Component-only scaling conflicts with NodeList semantics | §2.2 primary unit = 240 parameterized systems; 510 within-system components; forward/reverse on **full ordered system** then score fixed component IDs; frozen counts 240 / 510 / 390 Hill / 120 linear (§4.1) | **CLOSED** |
| **C3** | Parse/runtime failures excluded from primary rate | §2.1 denominator = all registered oracle-eligible Hill pairs; failures count as FNR (§9); `*_valid_pairs_only` secondary with explicit naming (§2.3); truth/oracle construction failure → incomplete, not FNR (§3.6, §9) | **CLOSED** |
| **M1** | Claim too broad | §0 limits claim to non-invariance/undercounting; separates syntactic exact/skeleton from algebraic equivalence; does not invalidate historical syntactic exact results; Hill classification reported separately (§2.3–§2.4) | **CLOSED** |
| **M2** | Conflicting endpoints and CI on existence proof | §2.1 single primary endpoint `hill_false_negative_rate`; decision = ≥1 E2-oracle-equivalent Hill false negative; **no CI on primary gate**; family/scale prevalence descriptive only (§2.4, §10) | **CLOSED** |
| **M3** | Invalid ablation counterfactuals | Removed `rescale=false`; B1 = identity scaler (§6); B2 scores **E1** without simplifier; B3 CAS diagnostic only; removed redundant identity baseline (old B5); §6 forbidden list | **CLOSED** |
| **M4** | Linear controls in Hill FNR denominator | Hill FNR denominator restricted to 390 Hill oracle-eligible pairs; linear 120 used for `linear_canonical_invariance_rate` and `hill_false_positive_rate` (§2.3, §6) | **CLOSED** |
| **M5** | Scale design / compute inconsistency | Primary scales `{0.1,0.5,1.0,2.0}` inside IC range; `5.0` stress labeled descriptive only (§4.2); explicit call-count table (§8.1); confirmatory hard ceiling 8,260 | **CLOSED** |
| **M6** | Silent wrong Scaler time range | Explicit `Scaler(time_range=[1,10], feature_scale=1)` (§5); runtime asserts `time_scale=9`, `time_shift=1`, `a_t=0.9`, `b_t=1.0`; abort on mismatch; forbids default `[1,5]` path | **CLOSED** |
| **M7** | Incomplete reproducibility / leakage contract | §7 seeds, ordering, quantization, CAS subset by hash; §12 fail-if-exists/resume; §13 commands, env, source hashes; §4.5 sealed-path guard; S5/smoke excluded from primary corpus (§4.4, §11 G5) | **CLOSED** |

---

## Section reference index (reviewer quick lookup)

| Topic | v2 sections |
|---|---|
| Calibrated claims | §0, §10 |
| Primary endpoint & units | §2 |
| E0/E1/E2 & oracle | §3 |
| Corpus & scales | §4 |
| Scaler asserts | §5 |
| Ablations | §6 |
| Seeds & determinism | §7 |
| Compute / call counts | §8 |
| Failure policy | §9 |
| Decision rules | §10 |
| Gates | §11 |
| Artifacts & resume | §12 |
| Commands & hashes | §13 |

---

## Deviations from v1 (`preregistration_draft.md`)

| v1 element | v2 disposition | Rationale |
|---|---|---|
| Three co-primary rates (Hill, skeleton, canonical) | Single primary: `hill_false_negative_rate`; others secondary | M2 |
| S1/S2 = 240 pairs each | C = 510 components, 390 Hill oracle-eligible × 4 scales = 1,560 primary pairs | C2, M4, M5 |
| `traj_scale` including 5.0 in primary sweep | Primary grid omits 5.0; stress tier descriptive | M5 |
| B1 `rescale=false` | Removed; B1 = identity scaler | M3 |
| B5 redundant identity | Removed | M3 |
| G3 CI lower bound > 0 | Replaced by existence rule (≥1 FNR) | M2 |
| Optional GPU decode (≤10 trajectories) | **Forbidden** (0 decode) | Task handoff CPU-only |
| Total calls ≤10,000 undifferentiated | Confirmatory tier 8,260 hard ceiling; descriptive tier optional | M5, §8.1 |
| Component-level rescaling implied | Full-system E0→E1→E2 | C1, C2 |
| No E-stage definitions | Explicit E0/E1/E2 + independent oracle | C1 |
| Parse failures excluded from Hill FNR numerator logic | Failure-aware denominator | C3 |

v1 remains untouched as historical draft.

---

## Acceptance test self-check

| Test | Evidence |
|---|---|
| One primary endpoint + unambiguous decision rule | §2.1, §10 |
| Correct full-system E0→E1→E2 chain | §3.2–§3.4 |
| Exact corpus/call counts + failure-aware denominators | §4.1, §8.1, §9 |
| Scaler asserts | §5 |
| Independent equivalence oracle | §3.5 |
| Sealed-path guard | §4.5 |
| Commands, env, source hashes, fail-if-exists/resume | §12–§13 |
| CPU-only, no decode | §8 |
| C1–C3, M1–M7 closed | Table above |

---

## Items for independent re-review

1. Confirm E0 formula matches `rescale_function` semantics for all 8 families at nontrivial scales.
2. Confirm 8,260 confirmatory call budget is sufficient for declared ablations without implicit factorial expansion.
3. Confirm existence-based primary gate is acceptable for PI freeze given deterministic generator.
4. Verify sealed-path glob list covers all GPU_RUN5 holdout locations in this repository layout.

---

## Implementer attestation

- Original `preregistration_draft.md` was not edited.
- No implementation or experiment code was changed in this task.
- Review response section references were verified against `preregistration_draft_v2.md` before commit.
