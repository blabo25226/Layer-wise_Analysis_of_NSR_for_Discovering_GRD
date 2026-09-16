# C0001-T009 v10 preregistration drafting handoff

## Objective

Draft a complete, self-contained v10 preregistration that supersedes frozen v9
without altering v9. Close the protocol defect and all consequences enumerated
in `preregistration_v10_amendment_decision.md`.

## Worker role and isolation

- preferred worker: Claude research engineer / scientific writer
- branch: `ai/C0001/research-engineer/implement-metric-audit`
- worktree: `/tmp/lansr-multiai-C0001-implement-audit`
- write scope: C0001 v10 preregistration draft, change table, drafting completion
- prohibited: implementation edits, full experiment, freeze declaration,
  scientific result claims, GPU_RUN5 sealed/result access

## Required inputs

- `preregistration_draft_v9.md`
- `preregistration_v9_freeze_record.md`
- `implementation_review_round5.md`
- `preregistration_v10_amendment_decision.md`
- `.agent/rules/04-preregistration-and-metric-freeze.md`
- `.agent/skills/experiment-preregistration/SKILL.md`

## Required outputs

1. `preregistration_draft_v10.md`: full contract, not a patch note.
2. `preregistration_v9_to_v10_change_table.md`: every changed endpoint, gate,
   field, primitive, count, budget, ID, failure rule, and claim boundary.
3. `preregistration_v10_drafting_completion.md`: exact validation performed,
   unresolved review questions, and statement that v10 is not frozen.

## Acceptance before independent review

- v9 bytes and SHA256 unchanged.
- New audit ID is `c0001_metric_identifiability_audit_v10`.
- Q4 algorithm, rounding semantics, serialization, independent implementation,
  oracle references, and evidence fields are executable rather than prose-only.
- Primary denominator remains 1,320 with no post-E2 exclusions.
- E1-original and E2-Q4 oracle meanings are unambiguous in every table.
- Positive, negative, drift, timeout, Q4-failure, and compound-power fixtures are
  specified.
- Supported and unsupported decisions are constructively reachable.
- Confirmatory and grand call counts are re-derived from primitive tables.
- Compute and disk ceilings are reconsidered rather than copied blindly.
- `git diff --check` passes; artifacts are committed, pushed, and remote SHA is
  verified.
