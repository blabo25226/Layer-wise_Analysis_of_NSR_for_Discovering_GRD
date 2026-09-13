## Multi-AI autonomous research track: GPU_RUNmultiAI

For autonomous multi-AI research, the canonical operating system is under `.agent/`.

Before starting or resuming this track, read:

1. `.agent/README.md`
2. `.agent/rules/00-mission-and-authority.md`
3. `.agent/rules/05-git-worktree-and-concurrency.md`
4. `.agent/rules/08-routing-and-delegation.md`
5. `.agent/rules/12-cycle-persistence-and-continuity.md`
6. `GPU_RUNmultiAI/RESEARCH_LOOP.md`
7. `GPU_RUNmultiAI/research_state.md`
8. `GPU_RUNmultiAI/hypothesis_tree.md`

`GPU_RUNmultiAI/` is the persistent campaign area. Reusable source code belongs in the normal repository locations
(`src/`, `scripts/`, `configs/`, `tests/`) while campaign-specific plans, reviews, state, reports, manifests and
cycle artifacts belong under `GPU_RUNmultiAI/`.

Do not import scientific conclusions, cycle results, or experimental artifacts from the retired PR #4
`GPU_RUNclaude1` autonomous track unless the human explicitly authorizes that source. Process patterns may be reused.

The default is to continue autonomously. Negative results, bugs, reviewer disagreement, or a worker failure are not
hard stops. Before any agent session ends, persist the current stage, active work, unresolved issues, and exact
`next_action` to `GPU_RUNmultiAI/research_state.md`.
