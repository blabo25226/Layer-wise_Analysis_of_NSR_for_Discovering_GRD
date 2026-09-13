# Example task handoff

```yaml
task_id: C0000-T001
cycle: C0000
parent_task_id: null
role: repo-operator
preferred_worker: Cursor Composer 2.5
objective: Verify that the multi-AI configuration is discoverable and that a disposable worktree task can edit/test/commit.
authoritative_inputs:
  - .agent/README.md
  - GPU_RUNmultiAI/research_state.md
frozen_constraints:
  - Do not start a scientific experiment.
write_scope:
  - GPU_RUNmultiAI/cycles/C0000/
branch: ai/C0000/repo-operator/smoke
worktree: .worktrees/C0000-repo-operator-smoke
expected_outputs:
  - GPU_RUNmultiAI/cycles/C0000/orchestration_smoke.md
acceptance_tests:
  - Worker can read canonical rules.
  - Worker can create/edit/commit in isolated worktree.
forbidden_changes:
  - No scientific result import from retired PR #4.
compute_budget: minimal
status: planned
retry_count: 0
fallback: Claude Sonnet 5
```
