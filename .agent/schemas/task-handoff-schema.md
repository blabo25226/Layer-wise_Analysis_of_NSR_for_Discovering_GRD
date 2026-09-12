# Task handoff schema

Each delegated task should communicate:

```yaml
task_id:
cycle:
parent_task_id:
role:
preferred_worker:
objective:
authoritative_inputs: []
frozen_constraints: []
write_scope: []
read_scope: []
branch:
worktree:
expected_outputs: []
acceptance_tests: []
forbidden_changes: []
compute_budget:
status:
retry_count: 0
fallback:
```

The task prompt must be self-contained enough for a fresh-context subagent/worker.

At completion, return:
- status
- commit SHA (for write tasks)
- files changed
- tests/commands run and results
- material findings
- deviations
- unresolved risks
- recommended next action

## Acceptance

`status: completed` requires the expected artifact(s) and acceptance test(s) to pass.
Process exit code alone is insufficient, especially for Gemini/Antigravity headless filesystem work.
