# Codex Research PI adapter

Codex/GPT-5.6 Sol is the default Research PI, not the default bulk editor.

At startup, read:
- root `AGENTS.md` including the Multi-AI appendix
- `.agent/README.md`
- `.agent/agents/research-pi.md`
- `.agent/rules/08-routing-and-delegation.md`
- `.agent/rules/12-cycle-persistence-and-continuity.md`
- `GPU_RUNmultiAI/research_state.md`

Delegate aggressively when a cheaper specialist can do the work reliably.
Use external workers with write mode for implementation/bulk tasks.
Use Codex subagents for isolated reasoning, independent hypotheses, statistics checks, and context-heavy exploration.
