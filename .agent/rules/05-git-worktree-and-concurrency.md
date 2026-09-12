# Git worktree and concurrency

All workers may write, but concurrent writing must be isolated.

## Default

Each write-capable delegated task gets:
- its own branch
- its own Git worktree (or an equivalent isolated project copy)
- an explicit `write_scope`
- an explicit acceptance test
- a task ID recorded in `GPU_RUNmultiAI/research_state.md`

Recommended naming:
- branch: `ai/<cycle>/<role>/<task-slug>`
- worktree: `.worktrees/<cycle>-<role>-<task-slug>`

Do not attach one branch to two worktrees.

## Integration

Workers commit their deliverable before handoff unless explicitly told otherwise.
The parent/PI inspects diff/tests and integrates by merge or cherry-pick.
Do not edit the integration worktree merely to avoid making a proper handoff.

## Forbidden destructive shared-state operations

Without explicit human authorization:
- no force push
- no shared-history rewrite
- no deleting another worker's branch/worktree
- no `git reset --hard` against another worker's unintegrated work
- no broad clean operation that can remove unrelated artifacts
- no overwriting prior run directories

If branches conflict, resolve deliberately and record what was chosen.
