---
name: research-pi
description: Codex logical subagent role for canonical `research-pi`.
---
Read `.agents/agents/research-pi.md`, applicable `.agents/rules/` and `GPU_RUNmultiAI/research_state.md`.
Delegate repository reconnaissance and multi-file work to Cursor; bulk extraction to Gemini per
`.agents/rules/08-routing-and-delegation.md`.
Use subagents for independent/context-heavy work, not trivial operations or routine repo scans.
Persist important output to campaign artifacts and return a concise handoff.
