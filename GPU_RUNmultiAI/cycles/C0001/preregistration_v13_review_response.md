# C0001 preregistration v13 → v14 review response

- task: `C0001-T013`
- source review: `preregistration_v13_independent_review.md`
- v13 draft SHA256: `c70502e194cac0420a5724b8ca7608ab92006aaad9f8c19faccf0d412447a962`
- v14 draft path: `preregistration_draft_v14.md`
- audit_id: `c0001_metric_identifiability_audit_v14`
- status: **R13-1 through R13-6 closed in v14 draft**（v14 未凍結）

## Finding-by-finding closure map

| ID | Sev | v13 issue | v14 repair | v14 section |
|---|---|---|---|---|
| **R13-1** | P0 | Q4 fixtures contradict prefix API and n-ary fold; fixture 07 used infix not E1 prefix | Replace fixtures 03/04 with 3-arg Add/Mul prefix inputs and complete emit outputs; fixture 07 input `mul,div,1,3,x_0` → emit `mul,mul,1,pow,3,-1,x_0`; gate all seven at **G_q4ref** | §3.4.6, §3.4.9, §6.1, §10 G_q4ref |
| **R13-2** | P0 | prefix-to-infix not self-contained; unparseable Q4 continued per-row | Inline full `write_infix` mapping, remainder check, leaf/unknown behavior; **`Q4ContractError` global abort** before pair outcome reuse | §3.4.2, §3.4.7 |
| **R13-3** | P0 | guard installed after task init | Freeze minimal bootstrap; parent/child install guard before audit/runtime, corpus, config, output, ODEFormer, task code | §11 |
| **R13-4** | P1 | incomplete source-hash contract blocks F repairs | Freeze sorted path-inventory algorithm (81 paths incl. shared runtimes, `gpu_run5/config.py`, recursive `third_party/odeformer/**/*.py`); bind per-file hashes only after implementation closure PASS | §13.2, §12.1 `implementation_closure_record.json` |
| **R13-5** | P1 | artifact/durability/resume incomplete | Full row schemas §12.8; `construction_incomplete` in `pair_results.csv`; remove duplicate `stratum` column; JSONL truncate+fsync; universal `abort_manifest.json`; `deviation_log.md` lifecycle; resume fingerprint/corpus/deps | §12.3, §12.5–12.7, §12.6 |
| **R13-6** | P1 | G_impl alone cannot enforce new protocol contracts | Add separate pre-full-audit **`G_contract`**; keep **`G_impl` exactly F1,F2,F4,F5,F6,F7,F8** | §10, §10.1 |

## Required same-pass cleanup

| Item | v14 action |
|---|---|
| Orphaned scale-predicate rows | §2.5.1 scale predicate table with header |
| Zero-based component wording | §2.5.1 explicit zero-based `component_idx` sets retained |
| Stale section references | §14 checklist updated for v14 gates/artifacts |
| Object identity | §5.2 `rescaled_tree is input_tree` **mandatory** |
| `neg` consistency | §3.4.2 / §3.7: `neg` not in frozen Q4 dialect |
| `formula_metrics_valid` in G_b4 | §10 G_b4 uses `formula_metrics_valid=true` |
| Completion-only metadata churn | Two-commit protocol only; no state tip chase on completion commit |

## Count / ceiling reconciliation

| Quantity | v14 value | Mechanism |
|---|---:|---|
| C_q4 counted fixtures | 7 | §6.1 `q4_fixture_01`…`q4_fixture_07` |
| Confirmatory calls | 27,637 | §8.3 arithmetic |
| D2 descriptive | 2,640 | §8.4（330×8） |
| Grand maximum | 30,277 | §8.4 |
| Primary denominator | 1,320 | §2.2（330×4） |
| Elapsed wall ceiling | 18,000 s | §8.5 |
| Disk ceiling | 1,200,000,000 bytes | §8.5 decimal 1.2 GB |

## Normative audit ID / ceiling check

- v14 normative fields use **`c0001_metric_identifiability_audit_v14`** only.
- Ceilings **27,637** / **30,277** appear in §8, §10, §12.2, §12.6, and §14.
- No normative “same as production” shortcut without inlined algorithm.

## v9 / v10 / v11 / v12 / v13 immutability

| Document | SHA256 | Edited |
|---|---|---|
| `preregistration_draft_v9.md` | `60cfed79780c6b027192a3da14e69416d72090e0a89dddd22248b0f00f50cf00` | **no** |
| `preregistration_draft_v10.md` | `da00004793fc2715b8f54d8a8ba6a7bf24138452d30a5bee54c16f5d69f95f21` | **no** |
| `preregistration_draft_v11.md` | `f8a31030a9032c204e0043a834f94cbe9e44fafac3ca11553ff38b126fe231d1` | **no** |
| `preregistration_draft_v12.md` | `fc90aef070977e8b889fc9f0f89ae8bbcb92afb011133ab1cbb4e1f3fa78cee0` | **no** |
| `preregistration_draft_v13.md` | `c70502e194cac0420a5724b8ca7608ab92006aaad9f8c19faccf0d412447a962` | **no** |

## Residual open items (for targeted independent closure review)

1. **REACH-UNS-1 / REACH-SUP-1 constructive artifacts**: unchanged; `reachability_evidence.json` remains post-freeze G_impl evidence.
2. **F1–F8 implementation**: post-freeze code repairs still required; G_impl requires acceptance tests PASS.
3. **G_contract acceptance tests**: must PASS before full audit; not executed in T013.
4. **v14 remains unfrozen** until targeted independent PASS on R13-1…R13-6 + freeze record.
