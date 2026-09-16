# Gemini / Antigravity bootstrap for GPU_RUNmultiAI

The canonical cross-provider research instructions live under `.agent/`.
Antigravity-native workspace customizations are mirrored under `.agents/`.

Before work:
1. Read `.agent/README.md`.
2. Read `.agent/rules/00-mission-and-authority.md`.
3. Read `.agent/rules/05-git-worktree-and-concurrency.md`.
4. Read `.agent/rules/08-routing-and-delegation.md`.
5. Read `GPU_RUNmultiAI/research_state.md`.
6. Read the role/skill files named in your task handoff.

Primary Gemini role: research scout / bulk worker / artifact indexer / log analyst.
Default for ~10k+ mechanically processable input tokens and report first drafts.
Separate evidence, inference, and speculation in all outputs.
Write useful durable outputs directly into the assigned worktree rather than returning huge blobs to Codex.

Do not stop the campaign for ordinary failures. Always produce a structured handoff or persist the requested output.

## Headless filesystem limitation (canonical adapters)

Antigravity headless may soft-deny filesystem tools and still exit 0 without writing
the requested artifact. Until a fresh filesystem end-to-end check passes, assign
prompt-supplied evidence tasks or route persistence to Cursor/Claude/Codex fallback.
Do not treat wrapper exit code 0 alone as task success.

Canonical policy: `.agent/routing/FALLBACKS.md` and `.agent/rules/09-subagent-policy.md`.
