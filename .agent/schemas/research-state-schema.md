# research_state.md required fields

Maintain a human-readable Markdown file with a machine-readable YAML block containing at least:

```yaml
campaign: GPU_RUNmultiAI
current_cycle: C0000
current_stage: STATE_RECONSTRUCTION
status: active
branch: null
commit: null
binding_plan: null
hard_stop: false
hard_stop_reason: null
active_tasks: []
completed_tasks: []
open_findings: []
retries: {}
next_action: ""
last_checkpoint_utc: null
```

Each active task should contain:
`task_id`, `role`, `worker`, `branch`, `worktree`, `write_scope`, `status`, `started_at`, `expected_outputs`,
`acceptance_test`, `retry_count`, and `fallback`.

State must be updated before a parent session exits.
