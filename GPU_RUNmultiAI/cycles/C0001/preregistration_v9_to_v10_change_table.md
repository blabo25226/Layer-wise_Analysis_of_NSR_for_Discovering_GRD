# C0001 preregistration v9 → v10 exhaustive change table

- source: `preregistration_draft_v9.md` (frozen SHA256 `60cfed79780c6b027192a3da14e69416d72090e0a89dddd22248b0f00f50cf00`)
- target: `preregistration_draft_v10.md` (draft; not frozen)
- amendment authority: `preregistration_v10_amendment_decision.md`
- task: C0001-T009
- date: 2026-09-14

Legend: **CHANGED** = substantive amendment; **UNCHANGED** = verbatim carry-forward; **NEW** = v10-only.

---

## 1. Document metadata

| Field | v9 | v10 | Status |
|---|---|---|---|
| `audit_id` | `c0001_metric_identifiability_audit_v9` | `c0001_metric_identifiability_audit_v10` | **CHANGED** |
| task | C0001-T005 | C0001-T009 | **CHANGED** |
| supersedes | v8 draft | v9 frozen + amendment decision | **CHANGED** |
| state | frozen (via separate record) | draft (not frozen) | **CHANGED** |
| amendment_authority | n/a | `preregistration_v10_amendment_decision.md` | **NEW** |
| v9 file bytes | immutable | not edited | **UNCHANGED** |

---

## 2. Claim boundary (§0)

| Topic | v9 | v10 | Status |
|---|---|---|---|
| Primary causal claim | whole-chain `hill_form` false negative | same | **UNCHANGED** |
| E1 equivalence target | original truth | original truth | **UNCHANGED** |
| E2 equivalence target | original truth | **`Q4(E1)` audit reference** | **CHANGED** |
| Quantization vs SFN | implicit conflation risk | explicit separation; `original_vs_q4_*` descriptive only | **CHANGED** |
| Quantization stratum | absent | `quantization_neutral` / `quantization_active` reporting only | **NEW** |
| Stage attribution | not claimed | not claimed | **UNCHANGED** |
| GPU_RUN5 access | prohibited | prohibited | **UNCHANGED** |
| unsupported reachability | reachable in principle | **constructively reachable** after E2–Q4 oracle | **CHANGED** |

---

## 3. Primary hypothesis (§1)

| Element | v9 | v10 | Status |
|---|---|---|---|
| Hypothesis ID | H0001-METRIC (v9) | H0001-METRIC (v10) | **CHANGED** (oracle wording) |
| H statement oracle conjunct | E1 equiv **and** E2 equiv (both vs truth) | E1 vs **original truth** **and** E2 vs **`Q4(E1)`** | **CHANGED** |
| Null hypothesis denominator | 1,320 | 1,320 | **UNCHANGED** |
| Decision order ranks 1–4 | exclusive 4-rank | same structure | **UNCHANGED** |
| supported logic | ≥1 diagnostic SFN | same | **UNCHANGED** |
| unsupported logic | SFN=0 and all 1,320 diagnostic | same | **UNCHANGED** |
| Q4 failure denominator | n/a | non-diagnostic; **denominator fixed** | **NEW** |
| Reachability fixtures | not specified | §3.8 table (6 classes) | **NEW** |

---

## 4. Primary endpoint (§2.1)

| Field | v9 | v10 | Status |
|---|---|---|---|
| Primary readout | component `hill_form` | same | **UNCHANGED** |
| Pipeline stages | E0→E1→simplifier→classify | E0→E1→**Q4**→simplifier→classify | **CHANGED** |
| Stage A-pre fields | absent | `q4_construction_completed`, `q4_emitted_infix`, `q4_construction_failure_reason` | **NEW** |
| Descriptive field | absent | `original_vs_q4_numeric_max_abs_error` | **NEW** |

---

## 5. Denominator and partition (§2.2)

| Element | v9 | v10 | Status |
|---|---|---|---|
| strict-Hill components | 330 | 330 | **UNCHANGED** |
| primary pairs | 1,320 | 1,320 | **UNCHANGED** |
| post-E2 exclusions | none | none | **UNCHANGED** |
| Outcome categories (5) | same names | same names | **UNCHANGED** |
| `construction_incomplete` | simplifier前 E1 不能 | same | **UNCHANGED** |
| `execution_failure` | oracle/simplifier failures | **adds `q4_construction_completed=false`** | **CHANGED** |
| `semantic_drift` | E1 or E2 vs truth nonequiv | E1 vs **truth** OR E2 vs **`Q4(E1)`** nonequiv | **CHANGED** |
| `structural_false_negative` | E1∧E2 equiv truth, hill=false | E1∧E2 equiv **(truth, Q4)** respectively | **CHANGED** |
| `preserved` | E1∧E2 equiv truth, hill=true | E1∧E2 equiv **(truth, Q4)** respectively | **CHANGED** |
| Precedence ranks 1–5 | 5-rank table | 5-rank table (rank 2 expanded) | **CHANGED** |
| `e1_oracle_reference` | implicit truth | frozen `original_truth` | **NEW** |
| `e2_oracle_reference` | implicit truth | frozen `q4_e1` | **NEW** |
| `quantization_stratum` | absent | per-component stratum on pair rows | **NEW** |
| Prohibition | n/a | E2≠truth alone cannot imply SFN | **NEW** |

---

## 6. Quantization stratum (§4.4)

| Element | v9 | v10 | Status |
|---|---|---|---|
| Stratum labels | n/a | `quantization_neutral`, `quantization_active` | **NEW** |
| Rule | n/a | `fractional_digit_count(token) > 4` on any leaf | **NEW** |
| Expected strict-Hill active components | n/a | 46 (184 pairs) | **NEW** |
| Expected strict-Hill neutral components | n/a | 284 (1,136 pairs) | **NEW** |
| Exclusion from denominator | n/a | **prohibited** | **NEW** |
| Assignment primitive | n/a | P12 at registration (510) | **NEW** |
| Artifact | n/a | `quantization_stratum.json` | **NEW** |

---

## 7. Q4 reference algorithm (§3.4)

| Element | v9 | v10 | Status |
|---|---|---|---|
| Q4 primitive | absent | P11 `q4_decimal_round_reference` | **NEW** |
| Production simplifier call | E2 only | E2 only; Q4 **must not** call simplifier | **NEW** |
| Transform | n/a | `parse_expr(evaluate=True)` → `Float.round(4)` | **NEW** |
| `prefix_to_sympy_infix` | n/a | audit-owned reimplementation | **NEW** |
| `audit_round_float_atoms` | n/a | `xreplace` on `sp.Float` only, decimals=4 | **NEW** |
| `FROZEN_Q4_LOCAL_DICT` | n/a | frozen symbol table | **NEW** |
| Q4 timeout | n/a | 10.0 s external | **NEW** |
| Representative fixtures | n/a | Q4-R1..R3 + C_q4 01..06 | **NEW** |
| Internal 1s timeout | documented for simplifier | **not used** in Q4 | **NEW** |

---

## 8. Oracle semantics (§3.5)

| Call | v9 reference | v10 reference | Status |
|---|---|---|---|
| E1 P7 | truth | **original truth** (explicit) | **UNCHANGED** (clarified) |
| E2 P7 | truth | **`q4_emitted_infix` from P11** | **CHANGED** |
| P7 count per B0 pair | 2 | 2 (references differ) | **UNCHANGED** count |
| `original_vs_q4_numeric_max_abs_error` | n/a | descriptive numeric grid max error | **NEW** |
| Analytic/numeric grid/atol/rtol | frozen | frozen | **UNCHANGED** |
| Oracle timeout | 30.0 s | 30.0 s | **UNCHANGED** |

---

## 9. Baselines and controls (§6)

| Condition | v9 | v10 | Status |
|---|---|---|---|
| B0 pipeline | E0→E1→simplify | E0→E1→**Q4**→simplify | **CHANGED** |
| B0 P7 stages | E1, E2 vs truth | E1-original, E2–Q4 | **CHANGED** |
| B1 pipeline | identity E0→simplify | identity E0→rescale→**Q4**→simplify | **CHANGED** |
| B1 P7 | **absent** | E1-original + E2–Q4 (510 each) | **CHANGED** |
| B1 P11 | absent | 510 | **NEW** |
| B2 | E1 classify+metrics | same scope | **UNCHANGED** (F7 post-freeze) |
| B3 | 500 CAS pairs | 500 | **UNCHANGED** |
| B4 | 510 truth-copy | 510 | **UNCHANGED** |
| C_q4 | absent | 6 Q4 fixtures (P11 only) | **NEW** |

---

## 10. Primitives (§8.2)

| ID | v9 | v10 | Status |
|---|---|---|---|
| P1–P10 | defined | same definitions | **UNCHANGED** |
| P11 | n/a | `q4_decimal_round_reference` | **NEW** |
| P12 | n/a | `quantization_stratum_assign` | **NEW** |

---

## 11. Counted-call budget (§8.3–§8.5)

| Bucket | v9 | v10 | Δ |
|---|---|---:|---:|
| Registration | 1,020 | 1,530 | +510 (P12) |
| B0 per-pair primitives | 7 | 8 | +1 (P11) |
| B0 subtotal | 14,280 | 16,320 | +2,040 |
| B1 subtotal | 2,550 | 4,080 | +1,530 |
| B2 subtotal | 4,080 | 4,080 | 0 |
| B4 subtotal | 1,020 | 1,020 | 0 |
| C_q4 | 0 | 6 | +6 |
| B3 + N1 | 600 | 600 | 0 |
| **Confirmatory total** | **23,550** | **27,636** | **+4,086** |
| D2 (330 × primitives) | 2,310 (×7) | 2,640 (×8) | +330 |
| **Grand maximum** | **25,860** | **30,276** | **+4,416** |
| CPU ceiling | 4 h | 5 h | +1 h |
| Disk ceiling | 1 GB | 1.2 GB | +0.2 GB |
| GPU | 0 | 0 | 0 |

**Arithmetic verification (v10)**:

```text
1530 + 16320 + 4080 + 4080 + 1020 + 6 + 600 = 27636
27636 + 2640 = 30276
```

---

## 12. Failure policy (§9)

| Event | v9 outcome | v10 outcome | Status |
|---|---|---|---|
| Q4 construction fail | n/a | `execution_failure` | **NEW** |
| Q4 timeout/nonfinite | n/a | `execution_failure` | **NEW** |
| E2≠truth, E2≡Q4 | `semantic_drift` (v9) | **not drift**; SFN/preserved candidate | **CHANGED** |
| E1≢truth | `semantic_drift` | `semantic_drift` | **UNCHANGED** |
| E2≢Q4 | n/a (was vs truth) | `semantic_drift` | **CHANGED** |
| Denominator reduction on Q4 fail | n/a | **prohibited** | **NEW** |
| `original_vs_q4` error alone | n/a | no outcome change | **NEW** |

---

## 13. Validity gates (§10)

| Gate | v9 | v10 | Status |
|---|---|---|---|
| G_corpus | defined | same | **UNCHANGED** |
| G0 | defined | same | **UNCHANGED** |
| G4 | defined | same | **UNCHANGED** |
| G1 ceiling | 23,550 | **27,636** | **CHANGED** |
| G_q4ref | absent | C_q4 6/6 + fixture 01 rounding | **NEW** |
| G_n1 | 100/100 reject | same | **UNCHANGED** |
| G_b4 | 510/510 self-match | same | **UNCHANGED** |
| G_ctrl_* | defined | same | **UNCHANGED** |
| G_term | 1,320/1,320 | same | **UNCHANGED** |
| G_inc | ≤5% construction_incomplete | same | **UNCHANGED** |
| Evaluation order | G_corpus→…→G_term | inserts **G_q4ref** after G1 | **CHANGED** |

---

## 14. Artifacts and schema (§12)

| Artifact / field | v9 | v10 | Status |
|---|---|---|---|
| `audit_id` in manifest | v9 | v10 | **CHANGED** |
| `pair_results.csv` q4 columns | absent | `q4_*` block | **NEW** |
| `e1_oracle_reference` | absent | `original_truth` | **NEW** |
| `e2_oracle_reference` | absent | `q4_e1` | **NEW** |
| `quantization_stratum` | absent | on pair rows | **NEW** |
| `original_vs_q4_numeric_max_abs_error` | absent | descriptive column | **NEW** |
| `quantization_stratum.json` | absent | required | **NEW** |
| `q4_reference_controls.json` | absent | required | **NEW** |
| `call_log.jsonl` P11/P12 | absent | required | **NEW** |
| P7 stage labels | E1/E2 | `E1-original` / `E2-q4` | **CHANGED** |
| `q4_timeout_sec` | absent | 10.0 | **NEW** |
| `confirmatory_call_ceiling` | 23550 | 27636 | **CHANGED** |
| `grand_call_ceiling` | 25860 | 30276 | **CHANGED** |
| Resume tuple key | 5-tuple | same | **UNCHANGED** |

---

## 15. CLI and provenance (§13)

| Item | v9 | v10 | Status |
|---|---|---|---|
| `--audit-id` | `..._v9` | `..._v10` | **CHANGED** |
| `--output-dir` | `..._audit_v9` | `..._audit_v10` | **CHANGED** |
| `--q4-timeout-sec` | absent | 10.0 | **NEW** |
| Seeds 61001–61005 | frozen | frozen | **UNCHANGED** |
| Source hash table | §13.2 | same files | **UNCHANGED** |
| Env vars LANSR_* | frozen | frozen | **UNCHANGED** |

---

## 16. Reachability fixtures (§3.8)

| Fixture ID | v9 | v10 | Status |
|---|---|---|---|
| REACH-SFN-1 | not specified | E1≡truth, E2≡Q4, hill=false | **NEW** |
| REACH-UNS-1 | unreachable under v9 | all diagnostic SFN=0 | **NEW** |
| REACH-DRIFT-E2 | implicit | E2≢Q4 completed nonequiv | **NEW** |
| REACH-Q4FAIL-1 | n/a | Q4 fail → execution_failure | **NEW** |
| REACH-TIMEOUT-1 | implied | simplifier timeout | **UNCHANGED** |
| REACH-POW-COMP-1 | n/a | compound power (F2) | **NEW** |

---

## 17. Post-freeze implementation (§16)

| ID | v9 prereg | v10 prereg | Status |
|---|---|---|---|
| F1 E0 rational construction | not in prereg | **§16 required** | **NEW** |
| F2 compound power parse | not in prereg | **§16 required** | **NEW** |
| F3 E2–Q4 oracle | broken (E2 vs truth) | **protocol fix in v10** | **CHANGED** |
| F4 inverted acceptance test | not in prereg | **§16 required** | **NEW** |
| F5 B1 production scaler | not in prereg | **§16 required** | **NEW** |
| F6 B1 unknown outcome | not in prereg | **§16 required** | **NEW** |
| F7 B2 E2 contamination | not in prereg | **§16 required** | **NEW** |
| F8 B3 separator | not in prereg | **§16 required** | **NEW** |

---

## 18. Items explicitly unchanged from v9

- Corpus generator call and `corpus_hash` rules (§4.1)
- Rewrite generation (`audit_rewrite_seed=61003`) and N1 selection (§3.2, §4.3)
- Canonical serialization (pipe `0x7c`, field labels, representative fixtures)
- Scaler construction asserts (§5)
- Sealed-path access guard matcher (§11)
- Typed unit IDs: `component`, `pair`, `negative` (§7.1)
- Secondary metrics naming (`valid_nmse` pattern via conditional metrics §2.4)
- Existence/absence asymmetric decision logic structure (§1)
- Linear control 480 pairs and FP/canonical gates
- D1 zero-call descriptive aggregation
- Internal simplifier 1s timeout observability limit

---

## 19. PI binding choices traceability

| PI choice # | v10 section | Closed in change table rows |
|---:|---|---|
| 1 | §2.2 denominator 1,320 | §5 |
| 2 | §3.5.2 E1-original oracle | §8 |
| 3 | §3.4 Q4 audit-owned | §7 |
| 4 | §3.5.2 E2–Q4 oracle | §8 |
| 5 | §3.5.3 descriptive error | §4, §8 |
| 6 | §4.4 stratum | §6 |
| 7 | §9 Q4 fail denominator | §5, §12 |
| 8 | §2.2 partition | §5 |
| 9 | §3.8 reachability | §16 |
| 10 | §8.3 recount | §11 |
| 11 | §6.1 C_q4 + G_q4ref | §9, §13 |
| 12 | §16 F1–F8 post-freeze | §17 |

---

## 20. Internal consistency checks performed

| Check | Result |
|---|---|
| Confirmatory sum §8.3 | 27,636 PASS |
| Grand sum §8.4 | 30,276 PASS |
| B0 row count 8×2040 | 16,320 PASS |
| B1 row count 8×510 | 4,080 PASS |
| D2 row count 8×330 | 2,640 PASS |
| strict-Hill pairs 330×4 | 1,320 PASS |
| Stratum expected pairs 184+1136 | 1,320 PASS |
| v9 SHA256 unchanged | `60cfed79780c6b027192a3da14e69416d72090e0a89dddd22248b0f00f50cf00` PASS |
