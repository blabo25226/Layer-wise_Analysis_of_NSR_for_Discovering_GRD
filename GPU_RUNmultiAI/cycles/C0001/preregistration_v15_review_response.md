# C0001 preregistration v15 → v16 review response

- task: `C0001-T015`
- source review: `preregistration_v15_independent_review.md`
- v15 draft SHA256: `dd986ab519eb3097b0978368482b02fc9e94f5514f89c2ad35e56d6870d8ecf2`
- v16 draft path: `preregistration_draft_v16.md`
- audit_id: `c0001_metric_identifiability_audit_v16`
- status: **R15-1 and R15-2 closed in v16 draft**（v16 未凍結）

## Finding-by-finding closure map

| ID | Sev | v15 issue | v16 repair | v16 section |
|---|---|---|---|---|
| **R15-1** | P0 | Bootstrap implemented after G_contract PASS but G_contract requires bootstrap; stdlib module imported `SealedPathGuard`; `install_guard_from_entry` returned `None` with no handle for child merge / G4 | Implementation required **post-freeze, before G_contract evaluation**; `guard_bootstrap.py` is self-contained stdlib-only (matcher, interceptors, attempt ledger, restore/merge); `install_guard_from_entry -> BootstrapGuardHandle` + `get_installed_guard()` singleton; parent retains handle for merge and G4 ledger | §10.1 row 2, §11, §12.1 |
| **R15-2** | P1 | Title prose called v15 a v14 draft; oracle grid referenced §13.1 instead of §3.5.2 | Title identifies v15 revision closing R15-1/R15-2; numeric grid reference fixed to §3.5.2 | header, §3.5.2 step 2 |

## Required same-pass cleanup

| Item | v16 action |
|---|---|
| Bootstrap ordering | post-freeze, before G_contract evaluation (not after G_contract PASS) |
| Self-contained guard | stdlib-only matcher/interceptors/ledger in `guard_bootstrap.py`; no package guard import |
| Handle ownership | `BootstrapGuardHandle` returned + singleton; parent merge + G4 from retained handle |
| G_contract acceptance | import-order, singleton identity, no replacement, propagation, deny/block, G4 ledger source |
| Stale refs | v15 identity in title; §3.5.2 oracle grid reference |

## Count / ceiling reconciliation

| Quantity | v16 value | Mechanism |
|---|---:|---|
| C_q4 counted fixtures | 7 | §6.1 `q4_fixture_01`…`q4_fixture_07` |
| Confirmatory calls | 27,637 | §8.3 arithmetic |
| D2 descriptive | 2,640 | §8.4（330×8） |
| Grand maximum | 30,277 | §8.4 |
| Primary denominator | 1,320 | §2.2（330×4） |
| G_impl requirement IDs | 7 | F1, F2, F4, F5, F6, F7, F8 only |
| Source inventory paths | 82 | §13.2（+`guard_bootstrap.py`） |

## Normative audit ID / ceiling check

- v16 normative fields use **`c0001_metric_identifiability_audit_v16`** only.
- Ceilings **27,637** / **30,277** appear in §8, §10, §12.2, §12.6, and §14.
- G_impl list remains **F1, F2, F4, F5, F6, F7, F8** only.

## v9 / v10 / v11 / v12 / v13 / v14 / v15 immutability

| Document | SHA256 | Edited |
|---|---|---|
| `preregistration_draft_v9.md` | `60cfed79780c6b027192a3da14e69416d72090e0a89dddd22248b0f00f50cf00` | **no** |
| `preregistration_draft_v10.md` | `da00004793fc2715b8f54d8a8ba6a7bf24138452d30a5bee54c16f5d69f95f21` | **no** |
| `preregistration_draft_v11.md` | `f8a31030a9032c204e0043a834f94cbe9e44fafac3ca11553ff38b126fe231d1` | **no** |
| `preregistration_draft_v12.md` | `fc90aef070977e8b889fc9f0f89ae8bbcb92afb011133ab1cbb4e1f3fa78cee0` | **no** |
| `preregistration_draft_v13.md` | `c70502e194cac0420a5724b8ca7608ab92006aaad9f8c19faccf0d412447a962` | **no** |
| `preregistration_draft_v14.md` | `0650d7a5e2af666c2036ee96a8b5137e9d325aac3ac70d076244ac2f1f74968c` | **no** |
| `preregistration_draft_v15.md` | `dd986ab519eb3097b0978368482b02fc9e94f5514f89c2ad35e56d6870d8ecf2` | **no** |

## Residual open items (for targeted independent closure review)

1. **`guard_bootstrap.py` implementation**: post-freeze, before G_contract evaluation; file listed in inventory but not required to exist pre-freeze.
2. **F1–F8 implementation**: post-freeze code repairs still required; G_impl requires acceptance tests PASS.
3. **G_contract acceptance tests**: must PASS before full audit; not executed in T015.
4. **v16 remains unfrozen** until targeted independent PASS on R15-1…R15-2 + freeze record.
