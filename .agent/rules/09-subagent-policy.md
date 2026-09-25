# Subagent policy

Use subagents when:
- independent work can run in parallel
- context isolation is valuable
- an adversarial second opinion is useful
- a long exploration would bloat the parent context

Do not spawn a subagent for a trivial one-shot action.

## Codex subagents (exceptional resource)

Codex subagents are **not** default workers. The Research PI and repo-operator should prefer:

```text
repository work       → Cursor
bulk / scout          → Gemini (broker mode when filesystem E2E unverified)
scientific critique   → Claude Opus 5.5
statistics review     → Claude Opus 5.5
reproducibility audit → Claude Opus 5.5
small bounded work    → GPT-6 Luna
final synthesis       → GPT-6 Sol PI
```

Before starting a Codex subagent, document why Claude Opus 5.5, Cursor, Gemini, or Luna cannot reliably perform the
task. Under Codex 5h capacity pressure, new Codex subagents are disallowed except when scientifically mandatory and
non-substitutable.

Avoid PI trees where multiple Codex subagents replace Cursor/Gemini/Claude roles in the same cycle stage.

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

For Gemini/Antigravity headless work:
- **Broker mode:** require non-empty stdout, acceptance validation, and a persisted artifact + provenance from
  `.ai/workers/gemini.sh --broker`.
- **Direct filesystem:** treat exit code 0 without the requested filesystem artifact as **FAIL** until a fresh
  filesystem end-to-end check passes. Until then, assign prompt-supplied evidence tasks rather than repo-file write tasks.
