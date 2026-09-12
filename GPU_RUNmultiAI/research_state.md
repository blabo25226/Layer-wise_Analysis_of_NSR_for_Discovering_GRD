# GPU_RUNmultiAI Research State

This file is the durable authority for autonomous campaign position.
Update it before a parent session ends.

```yaml
campaign: GPU_RUNmultiAI
status: active
current_cycle: C0001
current_stage: PREREGISTRATION_DRAFT
branch: 20260912_multiAI_research
commit: 85e38a3b2909fb730124d8603319c636c723145c
binding_plan: null

hard_stop: false
hard_stop_reason: null

active_tasks:
  - task_id: C0001-T004
    role: research-engineer
    worker: Claude Code
    branch: ai/C0001/research-engineer/preregister-metric-audit
    worktree: /tmp/lansr-multiai-C0001-preregister
    write_scope: [GPU_RUNmultiAI/cycles/C0001/scientific_state.md, GPU_RUNmultiAI/cycles/C0001/hypothesis_review.md, GPU_RUNmultiAI/cycles/C0001/literature_evidence.md, GPU_RUNmultiAI/cycles/C0001/preregistration_draft.md]
    status: planned
    started_at: null
    expected_outputs: [four scoped Markdown artifacts]
    acceptance_test: Draft covers the frozen-contract fields and preserves competing evidence.
    retry_count: 0
    fallback: Codex PI synthesis
completed_tasks:
  - task_id: C0000-T001
    worker: Claude Code
    status: integrated
    source_commit: a5f1c998cb54bdfe4a3fe0c267bc981dcffcdf49
    integration_commit: 942a5bc
    result: PASS
  - task_id: C0000-T002
    worker: Cursor Agent
    status: integrated
    source_commit: 5ab8beaa8760d879ae8c48b7506538b569dfaab2
    integration_commit: 6726cea
    result: PASS
  - task_id: C0000-T003
    worker: Gemini via Antigravity with Codex subagent fallback
    status: integrated_with_limitation
    source_commit: ee12453fbd396a9e21498280e0e10d36ce78d061
    integration_commit: 93b66db
    result: Gemini callable PASS; Gemini filesystem write FAIL; fallback persistence PASS
  - task_id: C0000-T004
    worker: Codex subagent
    status: completed
    result: PASS
  - task_id: C0001-T001
    worker: Codex subagent
    status: completed
    result: authorized scientific state reconstructed
  - task_id: C0001-T002
    worker: Codex subagent
    status: completed
    result: seven competing hypotheses ranked
  - task_id: C0001-T003
    worker: Codex subagent then Claude Opus fallback
    status: completed_with_fallback
    result: quota error after useful partial handoff; independent Claude review completed
open_findings:
  - Eight pre-existing GPU_RUN5 worktree records are prunable; they are unrelated to C0000 and were left untouched.
  - Gemini headless filesystem access soft-denies read_file/ListDir and can exit 0 without producing an artifact.
  - Claude critic raised a possible rescaling/exact-skeleton non-invariance; an exploratory algebraically equivalent formula check reproduced a false negative, but the actual pipeline round-trip remains untested.

retries:
  C0000-T003: 1
  C0001-T003: 1

next_action: >
  Run C0001-T004 in its isolated worktree, review and freeze the metric-identifiability preregistration, then hand
  the frozen contract to Cursor for implementation/tests. Do not inspect GPU_RUN5 sealed-test raw artifacts.

last_checkpoint_utc: 2026-09-12T11:05:00Z
```

## Notes

- `C0000` is infrastructure/bootstrap only, not a scientific result cycle.
- Replace branch/commit with actual values during first reconstruction.
- Active task entries follow `.agent/schemas/task-handoff-schema.md`.
