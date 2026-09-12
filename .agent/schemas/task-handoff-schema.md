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
# Evidence-packet provenance (reconnaissance and bulk tasks)
evidence_packet: null          # path to structured packet when produced
files_inspected: []            # repository paths read for claims
evidence_provenance:           # optional separation for scout/bulk handoffs
  evidence: []
  inference: []
  speculation: []
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
- `files_inspected` and evidence/inference/speculation separation (for reconnaissance or bulk tasks)

## Acceptance

`status: completed` requires the expected artifact(s) and acceptance test(s) to pass.
Process exit code alone is insufficient, especially for Gemini/Antigravity headless filesystem work.
