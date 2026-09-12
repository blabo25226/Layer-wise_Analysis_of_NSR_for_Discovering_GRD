# Multi-AI Task Board

This is a human-readable mirror of active delegated tasks.
`research_state.md` remains the machine-resumable authority.

| Task ID | Cycle | Role | Worker | Branch/worktree | Write scope | Status | Next |
|---|---|---|---|---|---|---|---|
| C0000-T001 | C0000 | scientific-critic | Claude Code | `ai/C0000/scientific-critic/claude-smoke` / `/tmp/lansr-multiai-C0000-claude-smoke` | `claude_smoke.md` | integrated | PASS |
| C0000-T002 | C0000 | repo-operator | Cursor Agent | `ai/C0000/repo-operator/cursor-smoke` / `/tmp/lansr-multiai-C0000-cursor-smoke` | `cursor_smoke.md` | integrated | PASS |
| C0000-T003 | C0000 | research-scout | Gemini / Antigravity + subagent fallback | `ai/C0000/research-scout/gemini-smoke` / `/tmp/lansr-multiai-C0000-gemini-smoke` | `gemini_smoke.md` | integrated with limitation | repair headless permissions before repo-file tasks |
| C0000-T004 | C0000 | fast-worker | Codex subagent | read-only then T003 fallback worktree | `subagent_smoke.md`, fallback record | completed | PASS |
| C0001-T001 | C0001 | research-scout | Codex subagent | shared read-only checkout | none | completed | state reconstructed |
| C0001-T002 | C0001 | hypothesis-scientist | Codex subagent | shared read-only checkout | none | completed | seven candidates returned |
| C0001-T003 | C0001 | statistical-reviewer / critic | Codex subagent + Claude Opus fallback | shared read-only checkout | none | completed with fallback | metric validity issue promoted for verification |
| C0001-T004 | C0001 | research-engineer | Claude Code | `ai/C0001/research-engineer/preregister-metric-audit` / `/tmp/lansr-multiai-C0001-preregister` | four C0001 planning artifacts | planned | draft and commit preregistration package |
