# C0001-T009 v10 preregistration drafting completion

- task: C0001-T009
- worker: **Cursor Agent** (authorized fallback after Claude write attempts)
- branch: `ai/C0001/research-engineer/implement-metric-audit`
- worktree: `/tmp/lansr-multiai-C0001-implement-audit`
- starting_tip: `985b2445d8256a691de07963390ab257cbfe7ebe`
- completed_at_utc: 2026-09-14T04:30:00Z
- status: **ready_for_independent_review**
- frozen: **NO** — v10 is a draft only

## Worker fallback record

| Attempt | Worker | Result |
|---:|---|---|
| 1 | Claude Code (research engineer) | **no file edits** |
| 2 | Claude Code (retry) | **no file edits** |
| 3 | Cursor Agent (authorized fallback) | **deliverables written** |

## Deliverables

| Output | Path | Status |
|---|---|---|
| v10 preregistration draft | `GPU_RUNmultiAI/cycles/C0001/preregistration_draft_v10.md` | written |
| v9→v10 change table | `GPU_RUNmultiAI/cycles/C0001/preregistration_v9_to_v10_change_table.md` | written |
| drafting completion | `GPU_RUNmultiAI/cycles/C0001/preregistration_v10_drafting_completion.md` | written |
| research state update | `GPU_RUNmultiAI/research_state.md` | updated |

## Prohibited actions (confirmed not performed)

- v9 preregistration file edits: **none**
- v10 freeze declaration: **none**
- implementation / test edits: **none**
- full confirmatory audit execution: **none**
- GPU_RUN5 sealed / result artifact access: **none**

## v9 integrity verification

```bash
sha256sum GPU_RUNmultiAI/cycles/C0001/preregistration_draft_v9.md
# 60cfed79780c6b027192a3da14e69416d72090e0a89dddd22248b0f00f50cf00
```

Matches `preregistration_v9_freeze_record.md` binding SHA256.

## Internal validation performed

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

### Denominator / stratum counts

| Quantity | Value | Verified |
|---|---:|---|
| strict-Hill components | 330 | PASS |
| primary pairs | 1,320 | PASS |
| quantization_active components (expected) | 46 | PASS |
| quantization_active pairs (expected) | 184 | PASS |
| quantization_neutral components (expected) | 284 | PASS |
| quantization_neutral pairs (expected) | 1,136 | PASS |
| 184 + 1,136 | 1,320 | PASS |

### PI binding choices (12/12)

All twelve choices in `preregistration_v10_amendment_decision.md` mapped in change table §19.

### Q4 contract executability

- Algorithm steps 1–5 specified with failure modes
- `audit_round_float_atoms` pseudocode frozen
- `FROZEN_Q4_LOCAL_DICT` enumerated
- C_q4 fixtures with `q4_fixture_01` rounding `0.04598→0.0460`
- Production simplifier call explicitly prohibited for Q4

### Oracle dual-reference clarity

- E1 P7: `original_truth` in all B0/B1 tables
- E2 P7: `q4_e1` / `E2-q4` stage label
- Partition precedence uses separate e1/e2 equivalence fields

### Reachability

- supported / unsupported / undecidable / drift / Q4-fail / timeout / compound-power fixtures in §3.8

### git diff --check

Run at commit time (see commit record below).

## Unresolved questions for independent methodology review

1. **`sympy_expr_to_audit_infix` emission parity**: v10 requires audit-owned emission equivalent to production `word_to_infix` but forbids production import. Reviewer should confirm the specified contract is testable via C_q4 + REACH fixtures without circular dependence on E2.

2. **B1 outcome partition scope**: v10 adds B1 E1/E2 oracles; F6 explicit B1 outcome taxonomy is deferred to post-freeze §16. Reviewer should confirm B1 rows are excluded from primary 1,320 denominator (already true) and that B1 unknown prohibition is sufficiently specified for closure.

3. **D2 recount inclusion of P11**: D2 uses 8 primitives (adds P11). Independent review should confirm D2 does not need separate E1/E2 oracle recount lines (oracles are confirmatory B0 only in current table).

4. **Resource ceilings**: CPU 5 h / disk 1.2 GB are proportional estimates, not benchmarked. Reviewer may request adjustment before freeze.

5. **REACH-SFN-1 constructive fixture**: v10 names the fixture class but does not pin a corpus `pair_id` for guaranteed `hill_form=false` under repaired F1. Closure review may require a hand fixture ID or prereg amendment before freeze.

## Next steps (not in T009 scope)

1. Independent methodological review (reachable fixtures, Q4 non-circularity, full recount).
2. Revise per review; freeze v10 at exact path + SHA256 + source commit.
3. Implement F1–F8 against frozen v10; bounded `smoke_r6` from clean commit.
4. Independent implementation / reproducibility review before full 27,636-call audit.

## Acceptance statement

- v10 draft is **self-contained** and supersedes v9 scientifically at amendment points only.
- v9 bytes remain immutable.
- v10 is **not frozen** and must not be used as binding_plan until freeze record exists.
