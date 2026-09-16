# C0001 preregistration v12 → v13 review response

- task: `C0001-T012`
- source review: `preregistration_v12_independent_review.md`
- v12 draft SHA256: `fc90aef070977e8b889fc9f0f89ae8bbcb92afb011133ab1cbb4e1f3fa78cee0`
- v13 draft path: `preregistration_draft_v13.md`
- audit_id: `c0001_metric_identifiability_audit_v13`
- status: **R12-1 through R12-5 closed in v13 draft**（v13 未凍結）

## Finding-by-finding closure map

| ID | Sev | v12 issue | v13 repair | v13 section |
|---|---|---|---|---|
| **R12-1** | P0 | Rational Q4-R4a not connected to counted gate; C_q4/G_q4ref only six fixtures | Add counted **`q4_fixture_07`** (Q4-R4a Rational invariance); **G_q4ref** requires **7/7**; confirmatory/grand ceilings **27,637** / **30,277** everywhere | §6.1, §8.3–§8.4, §10 G_q4ref, §12.2 |
| **R12-2** | P0 | n-ary Add/Mul fold undefined; `pow4` conflated with production Q4 table | Inline production `_sympy_to_prefix` fold (§3.4.6); **Q4-NARY-3** 3-child parity fixture; separate **audit-oracle** table with unary `pow4` (§3.4.7); abort on unparseable Q4 emitted operators | §3.4.6–3.4.7, §3.4.9, §16 F2 |
| **R12-3** | P1 | Self-containment regressed for oracle, guard, artifacts, resume, provenance | Restore pointwise oracle finite/tolerance table (§3.5.2); mandatory parent+child guard install and `guard_attempts_side_channel.jsonl` merge before G4 (§11); full artifact schemas + JSONL durability (§12.1–12.5); complete resume identity (§12.6); sorted recursive `source_hashes` inventory (§13.2) | §3.5.2, §11, §12, §13.2 |
| **R12-4** | P1 | Truth-side eligibility lacks zero-based component index binding | Inline exact per-family index sets matching `src/gpu_runmultiai/strata.py`; **G_eligibility** abort if zero/multiple membership (§2.5.1) | §2.5.1, §10 G_eligibility |
| **R12-5** | P1 | B3/B4/N1/C_q4/D2 row predicates and scale tokens underspecified | Direct row predicates (§2.5.4); canonical scale tokens `0.1`/`0.5`/`1.0`/`2.0`/`5.0` + identity cases (§2.5.3); **G1** confirmatory-only filter explicit in §3.5.2 | §2.5.3–2.5.4, §3.5.2, §10 G1 |

## Count / ceiling reconciliation

| Quantity | v13 value | Mechanism |
|---|---:|---|
| C_q4 counted fixtures | 7 | §6.1 `q4_fixture_01`…`q4_fixture_07` |
| Confirmatory calls | 27,637 | §8.3 arithmetic (`+7` C_q4) |
| D2 descriptive | 2,640 | §8.4（330×8） |
| Grand maximum | 30,277 | §8.4 |
| Primary denominator | 1,320 | §2.2（330×4） |
| Elapsed wall ceiling | 18,000 s | §8.5 |
| Disk ceiling | 1,200,000,000 bytes | §8.5 decimal 1.2 GB |

## Normative audit ID / ceiling check

- v13 normative fields use **`c0001_metric_identifiability_audit_v13`** only.
- Ceilings **27,637** / **30,277** appear in §8, §10, §12.2, §12.6, and §14.
- No normative “same as production” shorthand without inlined algorithm + §13.2 source hash.

## v9 / v10 / v11 / v12 immutability

| Document | SHA256 | Edited |
|---|---|---|
| `preregistration_draft_v9.md` | `60cfed79780c6b027192a3da14e69416d72090e0a89dddd22248b0f00f50cf00` | **no** |
| `preregistration_draft_v10.md` | `da00004793fc2715b8f54d8a8ba6a7bf24138452d30a5bee54c16f5d69f95f21` | **no** |
| `preregistration_draft_v11.md` | `f8a31030a9032c204e0043a834f94cbe9e44fafac3ca11553ff38b126fe231d1` | **no** |
| `preregistration_draft_v12.md` | `fc90aef070977e8b889fc9f0f89ae8bbcb92afb011133ab1cbb4e1f3fa78cee0` | **no** |

## Residual open items (for targeted independent closure review)

1. **REACH-UNS-1 / REACH-SUP-1 constructive artifacts**: unchanged from v12; `reachability_evidence.json` remains post-freeze G_impl evidence.
2. **F1–F8 implementation**: post-freeze code repairs still blocked; G_impl requires acceptance tests PASS.
3. **v13 remains unfrozen** until targeted independent PASS on R12-1…R12-5 + freeze record.
