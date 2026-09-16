# C0001-T010 v11 preregistration drafting completion

- task: C0001-T010
- worker: Cursor Agent
- branch: `ai/C0001/research-engineer/implement-metric-audit`
- worktree: `/tmp/lansr-multiai-C0001-implement-audit`
- starting_tip: `402cac89511364b597dfde71e160685ca87ecf73`
- completed_at_utc: 2026-09-15T14:45:00Z
- commit: `5fdb2af29682625552efdfea11a0e4c0734a36de` (v11 deliverable content in `377f215`)
- v11 SHA256: `f8a31030a9032c204e0043a834f94cbe9e44fafac3ca11553ff38b126fe231d1`
- remote_verified: `5fdb2af29682625552efdfea11a0e4c0734a36de` (LOCAL==REMOTE PASS)
- status: **ready_for_independent_closure_review**
- frozen: **NO**

## Deliverables

| Output | Path | Status |
|---|---|---|
| v11 preregistration draft | `GPU_RUNmultiAI/cycles/C0001/preregistration_draft_v11.md` | written |
| v10 review response | `GPU_RUNmultiAI/cycles/C0001/preregistration_v10_review_response.md` | written |
| drafting completion | `GPU_RUNmultiAI/cycles/C0001/preregistration_v11_drafting_completion.md` | written |
| research state | `GPU_RUNmultiAI/research_state.md` | updated |
| human review queue | `GPU_RUNmultiAI/human_review_queue.md` | updated |

## Prohibited actions (confirmed not performed)

- v9 / v10 preregistration edits: **none**
- v11 freeze declaration: **none**
- code / test edits: **none**
- full confirmatory audit execution: **none**
- GPU_RUN5 sealed / result artifact access: **none**
- smoke run artifacts: **not modified**

## v9 / v10 integrity verification

```text
preregistration_draft_v9.md  60cfed79780c6b027192a3da14e69416d72090e0a89dddd22248b0f00f50cf00
preregistration_draft_v10.md da00004793fc2715b8f54d8a8ba6a7bf24138452d30a5bee54c16f5d69f95f21
```

Both match historical freeze / v10 drafting records.

## Internal validation performed

### B1–B9 closure

| Finding | Status |
|---|---|
| B1 identity fallback | PASS — §2.2, §9, REACH-IDENT-FALLBACK-1 |
| B2 Q4 sympy_to_prefix | PASS — §3.4.4–3.4.7, Q4-R4, fixture_06 |
| B3 reachability + G_impl | PASS — §3.8, §10 G_impl |
| B4 classifier + rescale | PASS — §2.2, §5.2, §9 |
| B5 partition_scope | PASS — §2.5 |
| B6 G_b1 + fixture unit | PASS — §7.1, §10 G_b1 |
| B7 claim limits | PASS — §0 |
| B8 self-contained | PASS — no normative v9/v10 deferrals |
| B9 token grammar | PASS — §4.4 |

### Call-count arithmetic

| Bucket | Expected | Verified |
|---|---:|---|
| Registration (510×3) | 1,530 | PASS |
| B0 (2040×8) | 16,320 | PASS |
| B1 (510×8) | 4,080 | PASS |
| B2 (2040×2) | 4,080 | PASS |
| B4 (510×2) | 1,020 | PASS |
| C_q4 | 6 | PASS |
| B3+N1 | 600 | PASS |
| **Confirmatory** | **27,636** | PASS |
| D2 (330×8) | 2,640 | PASS |
| **Grand max** | **30,276** | PASS |

### Stratum counts (static inventory per v10 drafting)

| Quantity | Value | Verified |
|---|---:|---|
| quantization_active components | 46 | PASS (carried forward) |
| quantization_neutral components | 284 | PASS |
| strict-Hill pairs | 1,320 | PASS |

### Reachability rechecks (classifier only; no audit run)

| Fixture | Expected `hill_form` | Recheck |
|---|---|---|
| `2*x_0**2/(1+x_0**2)` (truth) | true | PASS |
| `4*x_0**2/(2+2*x_0**2)` (SFN candidate) | false | PASS |
| `x_0**2/(1+x_0**2)` (preserved) | true | PASS |

### Schema / cross-reference

- `audit_id` v11 only in normative CLI / resume / manifest fields
- Mixed AND/OR rules parenthesized in §1 and §2.2
- `unit_type` includes `fixture` (4 tokens total)
- G_impl and G_b1 add **zero** counted calls

## git diff --check

Run at commit time (see commit record).

## Open questions for independent closure review

1. **REACH-UNS-1**: v11 defines the 1,320-row synthetic proof obligation; reviewer should confirm the specification is sufficient without naming implementation module paths.
2. **SymPy oracle vs token oracle**: v11 prefers SymPy-expression comparison for Q4 parity; reviewer should confirm non-circularity with production `simplify_tree`.
3. **Live 46/284 recount**: deferred to implementation G_impl evidence; static v10 inventory retained.
4. **Resource ceilings**: 5 h CPU / 1.2 GB disk remain estimates (human queue, non-blocking).

## Next steps (out of T010 scope)

1. Independent closure review on v11 draft bytes.
2. Freeze v11 at exact path + SHA256 + source commit if PASS.
3. Implement F1–F8 + reachability evidence; bounded smoke from clean commit.
4. Full 27,636-call audit only after v11 freeze + G_impl PASS.

## Acceptance statement

- v11 draft is **self-contained** and addresses B1–B9.
- v9 and v10 bytes remain immutable.
- v11 is **not frozen** and must not be used as `binding_plan` until freeze record exists.
