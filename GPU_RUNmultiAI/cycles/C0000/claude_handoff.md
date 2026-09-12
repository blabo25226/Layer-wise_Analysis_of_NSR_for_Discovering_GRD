# C0000-T001 Claude handoff

```yaml
task_id: C0000-T001
cycle: C0000
parent_task_id: null
role: scientific-critic
preferred_worker: Claude Code
objective: Verify Claude write-mode operation, canonical-rule discovery, isolated editing, validation, and commit.
authoritative_inputs: [.agent/README.md, .agent/rules/05-git-worktree-and-concurrency.md, GPU_RUNmultiAI/research_state.md]
frozen_constraints: [Infrastructure smoke only; no scientific claim or experiment.]
write_scope: [GPU_RUNmultiAI/cycles/C0000/claude_smoke.md]
branch: ai/C0000/scientific-critic/claude-smoke
worktree: /tmp/lansr-multiai-C0000-claude-smoke
expected_outputs: [GPU_RUNmultiAI/cycles/C0000/claude_smoke.md]
acceptance_tests: [Artifact names task/role/branch, git diff --check passes, worker commits the artifact.]
forbidden_changes: [No other files, no PR #4 scientific content, no experiment.]
compute_budget: minimal
status: planned
retry_count: 0
fallback: Claude default model then Codex subagent
```
