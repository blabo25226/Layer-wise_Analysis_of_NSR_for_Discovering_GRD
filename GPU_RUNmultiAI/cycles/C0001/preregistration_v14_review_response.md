# C0001 preregistration v14 → v15 review response

- task: `C0001-T014`
- source review: `preregistration_v14_independent_review.md`
- v14 draft SHA256: `0650d7a5e2af666c2036ee96a8b5137e9d325aac3ac70d076244ac2f1f74968c`
- v15 draft path: `preregistration_draft_v15.md`
- audit_id: `c0001_metric_identifiability_audit_v15`
- status: **R14-1 through R14-5 closed in v15 draft**（v15 未凍結）

## Finding-by-finding closure map

| ID | Sev | v14 issue | v15 repair | v15 section |
|---|---|---|---|---|
| **R14-1** | P0 | §3.4.6/§3.4.9 normative n-ary outputs used left-nested `add,add,...` / `mul,mul,...` | All normative expected emit outputs use right-nested `add,x_0,add,x_1,x_2` and `mul,2,mul,x_0,x_1`; left-nested strings remain **inputs only** in §6.1; explicit prohibition on stale left-nested **outputs** | §3.4.6, §3.4.9, §6.1, §10 G_q4ref |
| **R14-2** | P0 | leaf vs unknown-token rules contradicted valid `x_k` leaves | Operator iff `t in all_operators`; otherwise numeric or nonnumeric leaf; unknown emitted operator detected by mandatory empty remainder; optional emitted-leaf allowlist for Q4 reparse | §3.4.2 |
| **R14-3** | P0 | guard install called without construct path; package import before install | Freeze dependency-free `scripts/phases/guard_bootstrap.py` (stdlib-only, repo root from entry `__file__`, literal `repo_root/results/runs`); `install_guard_from_entry`; parent/child sequence; G_contract import-order test; inventory inclusion (82 paths) | §11, §10.1, §13.2 |
| **R14-4** | P1 | incomplete artifact schemas | `terminal_outcome` on C_q4 rows; B0+B1+D2 E1/E2 oracle rows with `condition`/`stage`/`reference`; exact `deviation_log.md` entry + final status line | §12.8 |
| **R14-5** | P1 | stale refs, 1-based component wording, production shortcuts | `component_idx=2` wording; §3.4.10 oracle ref; §3.4.9 Rational fixtures; inline `audit_rescale_function` + `audit_word_to_infix` in §3.4.8 | §2.2, §3.4.8, §3.7, §5.2, §14 |

## Required same-pass cleanup

| Item | v15 action |
|---|---|
| Right-nested n-ary emit | All normative outputs; §6.1 inputs unchanged |
| Parser leaf semantics | Executable operator/leaf split without rejecting `x_k` |
| Guard bootstrap | `guard_bootstrap.py` required future file in frozen inventory |
| Artifact schemas | C_q4 `terminal_outcome`; oracle B0/B1/D2 E1/E2; deviation entry schema |
| Stale section refs | §3.4.10 oracle; §3.4.9 Q4-R4a/R4b in checklist |
| Rescale/serialization | §3.4.8 full inline algorithm; path pins without pre-implementation content hashes |

## Count / ceiling reconciliation

| Quantity | v15 value | Mechanism |
|---|---:|---|
| C_q4 counted fixtures | 7 | §6.1 `q4_fixture_01`…`q4_fixture_07` |
| Confirmatory calls | 27,637 | §8.3 arithmetic |
| D2 descriptive | 2,640 | §8.4（330×8） |
| Grand maximum | 30,277 | §8.4 |
| Primary denominator | 1,320 | §2.2（330×4） |
| G_impl requirement IDs | 7 | F1, F2, F4, F5, F6, F7, F8 only |
| Source inventory paths | 82 | §13.2（+`guard_bootstrap.py`） |

## Normative audit ID / ceiling check

- v15 normative fields use **`c0001_metric_identifiability_audit_v15`** only.
- Ceilings **27,637** / **30,277** appear in §8, §10, §12.2, §12.6, and §14.
- No normative “same as production” shortcut without inlined algorithm in rescale/serialization paths.

## v9 / v10 / v11 / v12 / v13 / v14 immutability

| Document | SHA256 | Edited |
|---|---|---|
| `preregistration_draft_v9.md` | `60cfed79780c6b027192a3da14e69416d72090e0a89dddd22248b0f00f50cf00` | **no** |
| `preregistration_draft_v10.md` | `da00004793fc2715b8f54d8a8ba6a7bf24138452d30a5bee54c16f5d69f95f21` | **no** |
| `preregistration_draft_v11.md` | `f8a31030a9032c204e0043a834f94cbe9e44fafac3ca11553ff38b126fe231d1` | **no** |
| `preregistration_draft_v12.md` | `fc90aef070977e8b889fc9f0f89ae8bbcb92afb011133ab1cbb4e1f3fa78cee0` | **no** |
| `preregistration_draft_v13.md` | `c70502e194cac0420a5724b8ca7608ab92006aaad9f8c19faccf0d412447a962` | **no** |
| `preregistration_draft_v14.md` | `0650d7a5e2af666c2036ee96a8b5137e9d325aac3ac70d076244ac2f1f74968c` | **no** |

## Residual open items (for targeted independent closure review)

1. **`guard_bootstrap.py` implementation**: post-freeze, G_contract-gated; file listed in inventory but not required to exist pre-freeze.
2. **F1–F8 implementation**: post-freeze code repairs still required; G_impl requires acceptance tests PASS.
3. **G_contract acceptance tests**: must PASS before full audit; not executed in T014.
4. **v15 remains unfrozen** until targeted independent PASS on R14-1…R14-5 + freeze record.
