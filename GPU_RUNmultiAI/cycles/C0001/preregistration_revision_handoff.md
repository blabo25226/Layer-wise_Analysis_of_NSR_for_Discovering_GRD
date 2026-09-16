# C0001 preregistration revision handoff

```yaml
task_id: C0001-T005
track: scientific
role: repo-operator
preferred_worker: Cursor Agent
objective: Revise the C0001 metric-invariance preregistration so it closes every independent review finding without changing the scientific question after results.
authoritative_inputs:
  - GPU_RUNmultiAI/cycles/C0001/preregistration_draft.md
  - GPU_RUNmultiAI/cycles/C0001/preregistration_independent_review.md
  - GPU_RUNmultiAI/cycles/C0001/scientific_state.md
  - GPU_RUNmultiAI/cycles/C0001/hypothesis_review.md
frozen_constraints:
  - no PR #4 or GPU_RUNclaude1 scientific evidence
  - no GPU_RUN5 sealed raw test access
  - deterministic fresh audit corpus only
  - no implementation or experiment execution in this task
write_scope:
  - GPU_RUNmultiAI/cycles/C0001/preregistration_draft_v2.md
  - GPU_RUNmultiAI/cycles/C0001/preregistration_review_response.md
  - GPU_RUNmultiAI/research_state.md
  - GPU_RUNmultiAI/task_board.md
  - MANIFEST.sha256
branch: ai/C0001/repo-operator/revise-preregistration
worktree: /tmp/lansr-multiai-C0001-revise-prereg
expected_outputs:
  - complete v2 preregistration closing C1-C3 and M1-M7
  - finding-by-finding response with exact v2 section references
acceptance_tests:
  - one primary endpoint and unambiguous decision rule
  - analytically correct full-system E0 to E1 to E2 chain
  - exact corpus and call counts with failure-aware denominators
  - explicit Scaler assertions, equivalence oracle, sealed-path access guard, commands, outputs, resume rules, and compute ceiling
  - git diff --check
forbidden_changes:
  - C0001 implementation or experiment code
  - original preregistration_draft.md
  - prior scientific artifacts
compute_budget: CPU-only document task
status: planned
retry_count: 0
fallback: Claude Sonnet specialized scientific writing; Codex PI only for conflict resolution
implementer_identity: Cursor Agent
independent_reviewer_identity: Claude scientific-critic
reviewer_diff_assertion: true
evidence_packet: GPU_RUNmultiAI/cycles/C0001/preregistration_independent_review.md
```
