# C0000-T003 Gemini handoff

```yaml
task_id: C0000-T003
cycle: C0000
parent_task_id: null
role: research-scout
preferred_worker: Gemini via Antigravity
objective: Verify Gemini write-mode operation, canonical-rule discovery, isolated editing, validation, and commit.
authoritative_inputs: [.agent/README.md, .agent/rules/05-git-worktree-and-concurrency.md, GPU_RUNmultiAI/research_state.md]
frozen_constraints: [Infrastructure smoke only; no scientific claim or experiment.]
write_scope: [GPU_RUNmultiAI/cycles/C0000/gemini_smoke.md]
branch: ai/C0000/research-scout/gemini-smoke
worktree: /tmp/lansr-multiai-C0000-gemini-smoke
expected_outputs: [GPU_RUNmultiAI/cycles/C0000/gemini_smoke.md]
acceptance_tests: [Artifact names task/role/branch, git diff --check passes, worker commits the artifact.]
forbidden_changes: [No other files, no PR #4 scientific content, no experiment.]
compute_budget: minimal
status: planned
retry_count: 0
fallback: GPT-5.6 Luna subagent
```
