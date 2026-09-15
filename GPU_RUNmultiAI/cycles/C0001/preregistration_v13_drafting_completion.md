# C0001-T012 v13 preregistration drafting completion

- task: C0001-T012
- worker: Cursor Agent
- branch: `ai/C0001/research-engineer/implement-metric-audit`
- worktree: `/tmp/lansr-multiai-C0001-implement-audit`
- starting_tip: `7ed72c5a0d10d68a3bb48edb936e7b84a6a98678`
- completed_at_utc: 2026-09-15T15:30:00Z
- content_source_commit: `7ed72c5a0d10d68a3bb48edb936e7b84a6a98678`
- v13 SHA256: `c70502e194cac0420a5724b8ca7608ab92006aaad9f8c19faccf0d412447a962`
- deliverable_commit: see post-push metadata commit
- remote_verified: see post-push metadata commit
- status: **ready_for_targeted_review**
- frozen: **NO**

## Deliverables

| Output | Path | Status |
|---|---|---|
| v13 preregistration draft | `GPU_RUNmultiAI/cycles/C0001/preregistration_draft_v13.md` | written |
| v12 review response | `GPU_RUNmultiAI/cycles/C0001/preregistration_v12_review_response.md` | written |
| drafting completion | `GPU_RUNmultiAI/cycles/C0001/preregistration_v13_drafting_completion.md` | written |
| research state | `GPU_RUNmultiAI/research_state.md` | updated |

## Prohibited actions (confirmed not performed)

- v9 / v10 / v11 / v12 preregistration edits: **none**
- v13 freeze declaration: **none**
- code / test edits: **none**
- smoke / full confirmatory audit execution: **none**
- GPU_RUN5 sealed / result artifact access: **none**
- untracked v9 smoke directory touch: **none**

## v9 / v10 / v11 / v12 integrity verification

```text
preregistration_draft_v9.md   60cfed79780c6b027192a3da14e69416d72090e0a89dddd22248b0f00f50cf00
preregistration_draft_v10.md  da00004793fc2715b8f54d8a8ba6a7bf24138452d30a5bee54c16f5d69f95f21
preregistration_draft_v11.md  f8a31030a9032c204e0043a834f94cbe9e44fafac3ca11553ff38b126fe231d1
preregistration_draft_v12.md  fc90aef070977e8b889fc9f0f89ae8bbcb92afb011133ab1cbb4e1f3fa78cee0
```

All four match historical introduction records.

## Internal validation performed

### R12-1 through R12-5 closure

| Finding | Status |
|---|---|
| R12-1 Rational q4_fixture_07 + ceilings | PASS — 7 fixtures; 27637/30277; G_q4ref 7/7 |
| R12-2 n-ary fold + audit-oracle pow4 | PASS — §3.4.6 fold; §3.4.7 separate table; unparseable abort |
| R12-3 oracle/guard/artifacts/resume/provenance | PASS — §3.5.2 finite grid; §11 side channel; §12 schemas/JSONL; §13.2 hashes |
| R12-4 truth-side index sets | PASS — §2.5.1 G_eligibility |
| R12-5 row predicates + scale tokens + G1 filter | PASS — §2.5.3–2.5.4; confirmatory-only G1 |

### Call-count arithmetic

| Bucket | Expected | Verified |
|---|---:|---|
| Registration (510×3) | 1,530 | PASS |
| B0 (2040×8) | 16,320 | PASS |
| B1 (510×8) | 4,080 | PASS |
| B2 (2040×2) | 4,080 | PASS |
| B4 (510×2) | 1,020 | PASS |
| C_q4 | 7 | PASS |
| B3+N1 | 600 | PASS |
| **Confirmatory** | **27,637** | PASS |
| D2 (330×8) | 2,640 | PASS |
| **Grand max** | **30,277** | PASS |

### Consistency searches

- `rg '27636|30276|27,636|30,276' preregistration_draft_v13.md` → **0 matches**
- `q4_fixture_07` present in §6.1 and G_q4ref
- `audit_id` v13 only in normative CLI / resume / manifest fields
- `git diff --check` → **PASS**

## Next steps (out of T012 scope)

1. Targeted independent closure review on v13 R12-1…R12-5.
2. Freeze v13 at exact path + SHA256 + source commit if PASS.
3. Implement F1,F2,F4,F5,F6,F7,F8 + reachability evidence; bounded smoke.
4. Full 27,637-call audit only after v13 freeze + G_impl PASS.

## Acceptance statement

- v13 draft is **self-contained** and addresses R12-1 through R12-5.
- v9–v12 bytes remain immutable.
- v13 is **not frozen** and must not be used as `binding_plan` until freeze record exists.
