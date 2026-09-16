---
name: state-reconstruction
description: Reconstruct the exact current multi-AI campaign state at session start or after interruption.
---
# State Reconstruction

Read actual files; do not rely on chat memory.

When 5+ substantive repository files are needed for reconstruction, delegate repository reconnaissance to Cursor
`repo-operator` first per `.agent/rules/08-routing-and-delegation.md`.

Minimum:
- `git branch --show-current`
- `git status --short`
- root `AGENTS.md`
- root `README.md`
- `GPU_RUNmultiAI/RESEARCH_LOOP.md`
- `GPU_RUNmultiAI/research_state.md`
- `GPU_RUNmultiAI/hypothesis_tree.md`
- latest cycle report/review/manifests
- active task branches/worktrees listed in state

Verify that each `active_task` still exists and classify it as running, completed, failed, stale, or unknown.
Update state before proceeding.
