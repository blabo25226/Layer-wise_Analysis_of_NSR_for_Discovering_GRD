# Subagent policy

Use subagents when:
- independent work can run in parallel
- context isolation is valuable
- an adversarial second opinion is useful
- a long exploration would bloat the parent context

Do not spawn a subagent for a trivial one-shot action.

For write-capable parallel subagents, use isolated worktrees/project copies or non-overlapping write scopes.
Read-only reviewers may share a checkout only when no files are modified.

A subagent starts with incomplete context. Its task must state:
- objective
- cycle/task ID
- authoritative files
- frozen constraints
- expected output
- acceptance test
- prohibited changes

Prefer 2-4 focused subagents to a large vague swarm. Persist important outputs to files instead of sending huge results
back through the parent context.

## Task acceptance

A delegated task is not accepted on process exit code alone.

Require the expected artifact(s), recorded commands/tests, and the stated acceptance test to pass.
For Gemini/Antigravity headless work, treat exit code 0 without the requested filesystem artifact as **FAIL** until a
fresh filesystem end-to-end check passes. Until then, assign prompt-supplied evidence tasks rather than repo-file
write tasks.
