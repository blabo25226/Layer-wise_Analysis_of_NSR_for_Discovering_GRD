# C0001 preregistration v11 → v12 review response

- task: `C0001-T011`
- source review: `preregistration_v11_independent_review.md`
- v11 draft SHA256: `f8a31030a9032c204e0043a834f94cbe9e44fafac3ca11553ff38b126fe231d1`
- v12 draft path: `preregistration_draft_v12.md`
- audit_id: `c0001_metric_identifiability_audit_v12`
- status: **R11-1 through R11-9 closed in v12 draft**（v12 未凍結）

## Finding-by-finding closure map

| ID | Sev | v11 issue | v12 repair | v12 section |
|---|---|---|---|---|
| **R11-1** | P0 | Rational `(1/3)*x_0` cannot emit Float `0.3333` under Float-only Q4 rounder; conflicting `mul,p,q,pow,-1` ordering | Split **Q4-R4a** (Rational invariance: `x_0/3`, prefix `mul,1,pow,3,-1`, no Float `0.3333`) and **Q4-R4b** (decimal `mul,0.33333,x_0` → `0.3333`); freeze production-compatible Rational serialization `mul,p,pow,q,-1` | §3.4.5, §3.4.8, §6.1 `q4_fixture_06` |
| **R11-2** | P0 | REACH-SUP-1 single SFN row leaves 1,319 primary rows missing → undecidable | **REACH-SUP-1**: exactly **1,320** unique rows = **1** fully diagnostic SFN + **1,319** fully diagnostic `preserved`, all gates PASS; **REACH-UNS-1**: exactly **1,320** unique fully diagnostic `preserved`, all gates PASS | §3.8 |
| **R11-3** | P1 | v11 delegates binding rules to history/production | Inline operator arity (§3.4.1), `SYMPY_OPERATORS` (§3.4.5), n-ary `\|` serialization (§3.4.7), N1 (§4.3), B3 (§6.2), oracle finite grid (§3.5.2), sealed guard (§11), artifact schemas (§12), resume/env/provenance (§12–§13), F1–F8 (§16); **no normative historical cross-reference** | entire v12 |
| **R11-4** | P1 | B0 scope labels all rows primary; circular B1/G_b1 | Add `eligibility_layer` truth predicates (§2.5.1); derive `partition_scope` from condition × layer (§2.5.2); B0 scopes: primary 1,320 / secondary 240 / linear 480; `control_pass_row` computed from row flags (§2.5.3); **G_b1** = 510/510 `control_pass_row` (§10) | §2.5, §6, §10 G_b1 |
| **R11-5** | P1 | rescale early-return catch-all ambiguous | Freeze **exactly two** preconditions: `len(nodes)>len(scale)` and `x_k` with `k>=len(scale)`; optional return check `rescaled_tree is input_tree`; **delete catch-all third path**; forbid lexical/algebraic equality | §5.2 |
| **R11-6** | P1 | G1 mixes confirmatory and grand; resource measurement unspecified; REACH ledger unclear | **G1** confirmatory ≤ 27,636 only; **G_grand** ≤ 30,276; `time.monotonic()` elapsed ≤ 18,000 s; output-dir bytes ≤ 1,200,000,000 (decimal 1.2 GB) checked before/after each primitive and artifact write with abort manifest; REACH-* preflight **outside** counted ledger; **C_q4** P11 **counted** | §3.8, §8.1, §8.5, §10 |
| **R11-7** | P1 | 46/284 stratum not bound to pre-pair gate; exponent tokens alter pairs | **G_stratum** pre-pair gate: re-derived 330 strict-Hill, **46** active / **284** neutral, **zero** exponent tokens; mismatch or any exponent token → **abort** (not per-pair `construction_incomplete`) | §4.4, §4.5, §10 G_stratum |
| **R11-8** | P1 | G_impl ambiguous on F requirements | **G_impl** names exactly **F1, F2, F4, F5, F6, F7, F8**; F3 closed by protocol; all seven fully inlined in §16 | §10 G_impl, §15–§16 |
| **R11-9** | P2 | Self-referential `observed_commit` churn | Completion records content source commit and one remote verification; `observed_commit` is observation only, not amended to chase tip | completion doc; state update policy |

## Count / ceiling reconciliation

| Quantity | v12 value | Mechanism |
|---|---:|---|
| Primary denominator | 1,320 | §2.2（330×4） |
| B0 strict-Hill pairs | 1,320 | §2.5.2 `eligibility_layer=strict_hill_primary` |
| B0 non-strict pairs | 240 | §2.5.2 |
| B0 linear pairs | 480 | §2.5.2 |
| Confirmatory calls | 27,636 | §8.3 arithmetic |
| D2 descriptive | 2,640 | §8.4（330×8） |
| Grand maximum | 30,276 | §8.4 |
| Elapsed wall ceiling | 18,000 s | §8.5 `time.monotonic()` |
| Disk ceiling | 1,200,000,000 bytes | §8.5 decimal 1.2 GB |
| `quantization_active` components | 46 | §4.5 G_stratum |
| `quantization_neutral` components | 284 | §4.5 G_stratum |
| REACH-SUP-1 rows | 1,320 unique (1 SFN + 1,319 preserved) | §3.8 |
| REACH-UNS-1 rows | 1,320 unique preserved | §3.8 |
| C_q4 counted calls | 6 | §8.3 |

## Normative audit ID / ceiling check

- v12 normative fields use **`c0001_metric_identifiability_audit_v12`** only.
- No normative reference to prior `audit_id` values as binding identifiers.
- Ceilings **27,636** / **30,276** / **18,000** s / **1,200,000,000** bytes appear only as v12 §8 values.

## v9 / v10 / v11 immutability

| Document | SHA256 | Edited |
|---|---|---|
| `preregistration_draft_v9.md` | `60cfed79780c6b027192a3da14e69416d72090e0a89dddd22248b0f00f50cf00` | **no** |
| `preregistration_draft_v10.md` | `da00004793fc2715b8f54d8a8ba6a7bf24138452d30a5bee54c16f5d69f95f21` | **no** |
| `preregistration_draft_v11.md` | `f8a31030a9032c204e0043a834f94cbe9e44fafac3ca11553ff38b126fe231d1` | **no** |

## Residual open items (for targeted independent closure review)

1. **REACH-UNS-1 / REACH-SUP-1 constructive artifacts**: v12 specifies row counts and gate-pass obligations; implementation must emit `reachability_evidence.json` before G_impl PASS.
2. **F1–F8 implementation**: post-freeze code repairs remain blocked; G_impl requires acceptance tests PASS for all seven named requirements.
3. **Live G_stratum recount**: independent reviewer may re-derive 46/284 at implementation time; mismatch aborts per §4.5.
4. **v12 remains unfrozen** until targeted independent PASS + freeze record.
