# C0001-T006-R5 implementation revision handoff

```yaml
task_id: C0001-T006-R5
cycle: C0001
track: scientific
role: research-engineer / repo-operator
preferred_worker: Cursor Agent
branch: ai/C0001/research-engineer/implement-metric-audit
worktree: /tmp/lansr-multiai-C0001-implement-audit
binding_plan: GPU_RUNmultiAI/cycles/C0001/preregistration_draft_v9.md
binding_plan_sha256: 60cfed79780c6b027192a3da14e69416d72090e0a89dddd22248b0f00f50cf00
review: GPU_RUNmultiAI/cycles/C0001/implementation_review_round4.md
implementer_identity: Cursor Agent
independent_reviewer_identity: Claude reproducibility auditor and Codex audit subagents
reviewer_diff_assertion: true
full_confirmatory_audit_authorized: false
```

## Objective

Repair every R4-1 through R4-8 finding at the fixed reviewed SHA.  Preserve the
frozen preregistration and all invalid historical smoke artifacts.  Implement,
test, run one bounded R5 smoke from a clean committed checkout, commit the
evidence and handoff, non-force push, and verify the remote branch SHA.

## Required completion record

Record exact commits, changed files, test commands and exit codes, clean-commit
smoke provenance, deviations, unresolved risks, local and remote SHA, and the
next independent-review action.  Do not merge and do not run the full audit.
