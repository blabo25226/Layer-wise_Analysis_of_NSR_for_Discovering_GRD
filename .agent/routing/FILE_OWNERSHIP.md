# Default file ownership

Ownership is a routing preference, not exclusive permission.

- Research PI: `GPU_RUNmultiAI/research_state.md`, hypothesis tree integration, cycle decision records.
- Claude Opus: reviews, audits, methodology/statistics critiques.
- Claude Sonnet: preregistration drafts, implementation notes, reports, research code when appropriate.
- Cursor Composer: `src/`, `scripts/`, `configs/`, `tests/`, refactors, implementation commits.
- Gemini Flash: literature candidate files, indexes, log summaries, artifact inventories, mechanical derived files.
- Luna: focused fixes, small tests, lightweight analyses and transformations.

A task handoff's explicit `write_scope` overrides this default.
Concurrent tasks must not have overlapping write scopes unless they are isolated in separate worktrees and later
integrated deliberately.
