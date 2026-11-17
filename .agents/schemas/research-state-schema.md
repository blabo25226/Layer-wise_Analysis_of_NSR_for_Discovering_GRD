# research_state.md required fields

Maintain a human-readable Markdown file with a machine-readable YAML block containing at least:

```yaml
campaign: GPU_RUNmultiAI
current_cycle: C0000
current_stage: STATE_RECONSTRUCTION
status: active
branch: null
observed_commit: null
base_commit: null
remote_branch: null
remote_commit: null
last_push_attempt_utc: null
last_push_error: null
binding_plan: null
hard_stop: false
hard_stop_reason: null
tracks:
  infrastructure:
    status: active
    current_cycle: C0000
    stage: null
  scientific:
    status: paused
    current_cycle: null
    stage: null
active_tasks: []
completed_tasks: []
open_findings: []
retries: {}
next_action: ""
last_checkpoint_utc: null
```

## Commit semantics

Do not use a single self-referential `commit` field.

- `observed_commit`: HEAD observed in the active checkout during reconstruction.
- `base_commit`: integration or task base commit the current work is measured against.
- `remote_branch`: upstream research branch name, when applicable.
- `remote_commit`: verified upstream SHA after a successful non-force push.

Record push failures in `last_push_attempt_utc` and `last_push_error`. Never report durability before `remote_commit`
matches the intended local integration SHA.

## Active task fields

Each active task should contain:
`task_id`, `role`, `worker`, `branch`, `worktree`, `write_scope`, `status`, `started_at`, `expected_outputs`,
`acceptance_test`, `retry_count`, and `fallback`.

During reconstruction, reclassify stale `running` tasks to `stale`, `failed`, or `completed` based on branch,
worktree, artifact, and test evidence. Do not leave interrupted tasks marked `running` without verification.

State must be updated before a parent session exits.
