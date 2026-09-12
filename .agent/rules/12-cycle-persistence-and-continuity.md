# Cycle persistence and session continuity

The research campaign must remain resumable at every stage, not only at cycle boundaries.

Before any main-agent session ends, ensure `GPU_RUNmultiAI/research_state.md` contains:
- current cycle and stage
- current branch plus `observed_commit`, `base_commit`, and verified `remote_commit` when applicable
- separate infrastructure and scientific track status under `tracks`
- binding preregistration/version if any
- active worker tasks and branches/worktrees
- completed work
- unresolved findings
- deviations/retractions not yet propagated
- exact `next_action`
- retry counters/fallback state
- `hard_stop: true|false` and reason

A CLI session ending is not a hard stop.
If no hard stop exists, the state must describe how a watchdog or next session can continue without asking the human.

Long-running workers should write progress artifacts or commit checkpoints when practical.

During state reconstruction, inspect each `active_task` with `status: running` and reclassify stale entries using
branch, worktree, artifact, and acceptance-test evidence. A provider session ending does not keep a task `running`.
