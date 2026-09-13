# C0001 preregistration v6 closure review response

- task: C0001-T005
- implementer: Cursor Agent (repo-operator)
- reviewer packet: `preregistration_v6_closure_review.md`
- revised artifact: `preregistration_draft_v7.md`
- date: 2026-09-13
- verdict requested: sixth independent closure review (`ready_for_independent_closure_review`)

## Summary

v7 closes all five required revisions from the v6 independent closure review.
The scientific question is unchanged. v7 deepens the **phase8→predictions deny rule** to any
earlier `phase8` in the campaign-relative component sequence (evaluated separately on `norm_abs`
and `real_abs`), freezes **canonical pair_key / pair_id serialization** with a representative
fixture and B3/resume/duplicate identity, repairs the **resume identity Markdown table** and
freezes **`LANSR_TED_TIMEOUT_SEC`**, **`LANSR_SYMPY_TIMEOUT_SEC`**, **`LANSR_SYMPY_MAX_NODES`**
for manifest/resume comparison on both initial and resume commands, specifies **atol/rtol numeric
oracle tolerance** with finite-point requirements, and removes **variable-denominator null wording**
in favor of fixed 1,320-pair absence logic. Confirmatory budget arithmetic is unchanged
(**23,550**; grand max **25,860**).

## Finding closure map

| ID | Review finding (abbrev.) | v7 closure | Status |
|---|---|---|---|
| **V6-1** | `phase8`/`predictions` deny depth | §11: under `gpu_run5_*`, deny `test`/`sealed`/`final_test` directory + descendants at any depth; deny `predictions` directory + descendants whenever `phase8` occurs anywhere earlier in the campaign-relative component sequence (not only immediate predecessor); apply matcher separately to `norm_abs` and `real_abs`; all child processes inherit/install guard before task code | **CLOSED** |
| **V6-2** | Pair ID canonical serialization | §7: `system_id={family}:variant_index={i}:draw_index={j}`; `pair_key` field order `corpus_hash|system_id|component_idx|scale|rewrite_id` (literal ASCII pipe, UTF-8, no escaping); scale tokens exactly `0.1`, `0.5`, `1.0`, `2.0`, `identity`; `pair_id=pair_sha256:{digest}`; frozen fixture → expected digest `0ec45c4f3ee51650104b49b968198bc51795e323a77aef921e162c9c397a2bb6`; B3 sort, duplicate detection, resume use canonical `pair_id` only | **CLOSED** |
| **V6-3** | Resume identity table and environment | §12: repaired Markdown table; manifest/resume compare `LANSR_TED_TIMEOUT_SEC=10`, `LANSR_SYMPY_TIMEOUT_SEC=10`, `LANSR_SYMPY_MAX_NODES=40`; §13.3 shows exports on initial and resume commands | **CLOSED** |
| **V6-4** | Numeric oracle tolerance | §3.5: `atol=1e-8`, `rtol=1e-8`; per-point pass iff finite and `abs(pred-truth) <= atol + rtol*abs(truth)`; `numeric_equivalent` only if all grid points finite and pass; any nonfinite → `completed=false` | **CLOSED** |
| **V6-5** | Null denominator wording | §1: fixed 1,320 pairs; absence conclusion only when all 1,320 fully diagnostic and SFN=0; removed “fully diagnostic only as denominator” phrasing | **CLOSED** |

---

## v6 → v7 disposition (selected)

| v6 element | v7 disposition | Rationale |
|---|---|---|
| `predictions` deny only when immediately after `phase8` | Any earlier `phase8` in component sequence | V6-1 |
| Informal `pair_id` field list | Frozen `pair_key` serialization + fixture | V6-2 |
| Broken resume table rows after `cli_args_normalized` | Single contiguous table + env vars | V6-3 |
| Numeric tol `10^{-8}` only | Explicit atol/rtol combined inequality + finite rules | V6-4 |
| Null hypothesis uses diagnostic-only denominator | Fixed 1,320 denominator; absence needs full diagnostic coverage | V6-5 |
| `c0001_metric_identifiability_audit_v6` | `c0001_metric_identifiability_audit_v7` | audit_id bump |

v1–v6 drafts and `preregistration_v6_closure_review.md` remain untouched.

---

## Acceptance self-check

| Test | Evidence |
|---|---|
| phase8 anywhere-before-predictions deny + dual norm/real matcher | §11 |
| Canonical pair_key / pair_id + fixture | §7 |
| Resume table + frozen LANSR env vars on both commands | §12, §13.1, §13.3 |
| atol/rtol numeric oracle | §3.5 |
| Fixed 1,320 null wording | §1 |
| Confirmatory 23,550; grand max 25,860 | §8.3–§8.5 |
| V6-1–V6-5 closed | table above |

---

## Implementer attestation

- `preregistration_draft_v6.md` and `preregistration_v6_closure_review.md` were not edited.
- No implementation, experiment execution, sealed artifact access, push, or freeze was performed.
- Prior drafts v1–v5 and all prior review packets remain preserved.
