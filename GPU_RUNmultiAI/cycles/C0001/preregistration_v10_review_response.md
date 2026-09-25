# C0001 preregistration v10 → v11 review response

- task: `C0001-T010`
- source review: `preregistration_v10_independent_review.md`
- v10 draft SHA256: `da00004793fc2715b8f54d8a8ba6a7bf24138452d30a5bee54c16f5d69f95f21`
- v11 draft path: `preregistration_draft_v11.md`
- audit_id: `c0001_metric_identifiability_audit_v11`
- status: **B1–B9 closed in v11 draft**（v11 未凍結）

## Finding-by-finding closure map

| ID | Sev | v10 issue | v11 repair | v11 section |
|---|---|---|---|---|
| **B1** | P0 | Silent simplifier identity fallback makes negative conclusion unreachable when Q4(E1)≠E1 | Define `e2_identity_fallback_candidate` (E2 raw==E1 raw AND E1≢Q4 via SymPy oracle); classify as `execution_failure` before `semantic_drift`; persist field; no timeout claim; no global zero-rate gate | §0, §2.2, §9, §3.8 REACH-IDENT-FALLBACK-1 |
| **B2** | P0 | Q4 Float serialization unfrozen; wrong stage (`word_to_infix` only) | Freeze production `sympy_to_prefix` Float (`str(sp.Float)`) and Rational (`mul,p,pow,q,-1`) rules in §3.4.4–3.4.5; SymPy-expression canonical oracle §3.4.7; Q4-R4 `1/3→0.3333`; production simplifier forbidden as Q4 input | §3.4.4–3.4.7, §6.1 `q4_fixture_06` |
| **B3** | P0 | Supported/unsupported reachability asserted not proven | Pin REACH-SFN-1 (`2*x_0**2/(1+x_0**2)` vs `4*x_0**2/(2+2*x_0**2)`, `hill_form=false` rechecked); REACH-PRESERVED-1 (`x_0**2/(1+x_0**2)`, `hill_form=true`); REACH-UNS-1 (1,320 synthetic diagnostic rows); REACH-SUP-1 (one SFN); **G_impl** pre-full gate | §3.8, §10 G_impl |
| **B4** | P1 | Missing classifier parse and full rescale early-return coverage | `classifier_parse_valid=false` → `execution_failure` precedence 2; §5.2 lists all production `rescale_function` early returns (`len(nodes)>len(scale)`, `dim>=len(scale)`); REACH-PARSE-1, REACH-RESCALE-1; all mixed AND/OR parenthesized in §2.2 precedence | §2.2, §5.2, §9, §3.8 |
| **B5** | P1 | Non-primary outcome vocabulary deferred | Freeze `partition_scope` per condition; B1 `control_pass`/`control_failure` only; analogous vocab for B2–B4, N1, C_q4, D2; **`unknown` prohibited** on all non-primary rows | §2.5 |
| **B6** | P1 | B1 oracle validity gate missing; invalid C_q4 unit type | **G_b1**: 510/510 B1 rows require Q4 complete, both oracles equivalent, valid classifier parse, valid metrics; no added calls; **`unit_type=fixture`** for C_q4 | §6.1, §7.1, §10 G_b1 |
| **B7** | P2 | Bounded non-independence and timeout asymmetry unstated | §0 documents shared-defect risk (audit mirrors production parse/round/serialize) and Q4 external vs production internal timeout asymmetry; explicit non-claim on internal timeout | §0, §3.6 |
| **B8** | P1 | v10 not self-contained (“same as v9”) | v11 inlines corpus, scale, N1, guard, provenance, resume, serialization, gates, and algorithms; normative text contains no “same as v9/v10” | entire v11（§18 は歴史参照のみ） |
| **B9** | P1 | Ambiguous quantization token algorithm | Frozen raw-token grammar: reject exponent notation; strip sign; split on `.`; strip trailing fractional zeros; count remainder; integer→0; 46/284 expected counts retained from v10 verified arithmetic | §4.4 |

## Count / ceiling reconciliation

| Quantity | v11 value | Mechanism |
|---|---:|---|
| Primary denominator | 1,320 | §2.2（330×4） |
| Confirmatory calls | 27,636 | §8.3 arithmetic |
| D2 descriptive | 2,640 | §8.4（330×8） |
| Grand maximum | 30,276 | §8.4 |
| CPU wall | 5 h | §8.5 |
| Disk | 1.2 GB | §8.5 |
| `quantization_active` components | 46 | §4.4（v10 drafting PASS） |
| `quantization_neutral` components | 284 | §4.4 |

## Normative audit ID / ceiling check

- v11 normative fields use **`c0001_metric_identifiability_audit_v11`** only.
- No normative reference to `c0001_metric_identifiability_audit_v9` or `c0001_metric_identifiability_audit_v10` as binding audit IDs.
- Ceilings **27,636** / **30,276** appear only as v11 §8 values.

## v9 / v10 immutability

| Document | SHA256 | Edited |
|---|---|---|
| `preregistration_draft_v9.md` | `60cfed79780c6b027192a3da14e69416d72090e0a89dddd22248b0f00f50cf00` | **no** |
| `preregistration_draft_v10.md` | `da00004793fc2715b8f54d8a8ba6a7bf24138452d30a5bee54c16f5d69f95f21` | **no** |

## Residual open items (for independent closure review)

1. **REACH-UNS-1 constructive proof artifact**: v11 specifies the 1,320-row synthetic grid requirement; implementation must emit `reachability_evidence.json` before G_impl PASS.
2. **F1–F8 implementation**: post-freeze repairs remain blocked on code; G_impl requires their acceptance tests PASS.
3. **46/284 live corpus recount**: v11 retains v10-verified static inventory; independent reviewer may request regeneration check at implementation time.
4. **v11 remains unfrozen** until independent PASS + freeze record.
