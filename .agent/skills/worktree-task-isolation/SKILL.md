---
name: worktree-task-isolation
description: Create and manage isolated write-capable worker tasks using Git branches/worktrees and explicit write scopes.
---
# Worktree Task Isolation

1. Choose task ID, role and write scope.
2. Create a task branch from the intended integration commit.
3. Create an isolated worktree/project copy.
4. Record branch/worktree/task in `research_state.md`.
5. Give the worker a self-contained handoff.
6. Worker edits/tests/commits inside that worktree.
7. Parent reviews diff and tests.
8. Integrate by merge/cherry-pick.
9. Mark task integrated before deleting the worktree.
10. Never remove another active task's worktree.
