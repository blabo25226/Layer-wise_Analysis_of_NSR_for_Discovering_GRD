# Claude write isolation

Write tasks must respect `.agent/rules/05-git-worktree-and-concurrency.md`.
Commit task-local changes before handoff.
Do not modify another worker's active worktree or unintegrated branch.
