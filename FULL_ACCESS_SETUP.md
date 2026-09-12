# Full-access operational setup

## Goal

All AI workers should be able to read, write, run shell commands, run tests/experiments, and perform ordinary Git
operations without waiting for a human during routine research.

The safety boundary is **worktree/branch isolation plus destructive-operation rules**, not read-only mode.

## Codex -> external worker wrappers

The current `.ai/workers/{claude,cursor,gemini}.sh` wrappers are assumed to exist.

Codex should use `--write` for delegated tasks that can modify files:

```bash
.ai/workers/claude.sh --write "<task>"
.ai/workers/cursor.sh --write "<task>"
.ai/workers/gemini.sh --write "<task>"
```

`.codex/rules/ai-workers.rules` uses one `allow` policy for read-only and `--write`
wrapper prefixes. There is no separate full-access rules file.

If a wrapper itself still launches its provider in a plan/read-only mode, update that wrapper locally so `--write`
selects the provider's normal autonomous write/execute mode. Keep authentication owned by the official CLI.

## Isolated write tasks and acceptance

Delegated write tasks require an isolated worktree/branch and a declared write scope.
Do not treat worker exit code 0 as task success. Require the expected artifact(s),
acceptance test(s), and any required commit. Canonical policy:
`.agent/rules/09-subagent-policy.md` and `.agent/schemas/task-handoff-schema.md`.

## Provider setting principle

Configure each provider so that routine repo-local operations do not require interactive approval:

- file read/write/create/delete within the designated worktree
- shell commands required by the repository
- test/lint/build
- normal Git add/commit/branch/merge/cherry-pick
- experiment execution
- normal research web/network access where available

Do **not** convert "full access" into permission to destroy shared state. The common rules still prohibit force-push,
history rewriting, deleting another worker's worktree/branch, reading secrets unnecessarily, and silently overwriting
prior experiment artifacts.
