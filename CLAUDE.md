# Claude bootstrap for GPU_RUNmultiAI

Read `.agent/README.md` and the relevant canonical files under `.agent/rules/`, `.agent/agents/`, and `.agent/skills/`.

For autonomous research state, read `GPU_RUNmultiAI/research_state.md` and `GPU_RUNmultiAI/RESEARCH_LOOP.md`.

Claude roles:
- Opus-class: scientific critic, methodology/statistics reviewer, independent reviewer, final auditor.
- Sonnet-class: research engineer, scientific polish, report review after Gemini first draft.

Broad repository scan and routine first drafts should not default to Claude. See
`.agent/rules/08-routing-and-delegation.md` for capacity-aware routing.

You have normal write/shell/Git access in your assigned worktree. Commit your deliverable to your task branch before
handoff unless the parent explicitly requests an uncommitted review.

Do not stop the campaign for ordinary failures. If this session is ending, checkpoint state or return an explicit,
machine-actionable handoff to the parent.
