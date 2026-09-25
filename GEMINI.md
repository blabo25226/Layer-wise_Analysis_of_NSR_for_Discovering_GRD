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

Primary Gemini role: research scout / bulk worker / evidence compression / artifact indexer / log analyst.
Target model: **Gemini 3.8 Flash** via Antigravity (`gemini-3.8-flash-high`, override with `AI_WORKERS_GEMINI_MODEL`).
Apply Gemini-first thresholds in `.agent/rules/08-routing-and-delegation.md` (not optional when triggers match).

Separate evidence, inference, and speculation in all outputs.

## Broker mode (standard when filesystem E2E unverified)

```bash
.ai/workers/gemini.sh --broker \
  --prompt-file path/to/packet.md \
  --output-file path/to/artifact.md \
  --acceptance headings
```

The local wrapper persists stdout and provenance; Gemini does not need repository write access.

## Direct filesystem

Until headless filesystem E2E passes in a disposable worktree, do not rely on Antigravity writing repository files.
For repo changes, emit structured edit proposals / diffs / plans for Cursor to apply.

Canonical policy: `.agent/routing/FALLBACKS.md`, `.agent/skills/evidence-compression/SKILL.md`, and
`.agent/rules/09-subagent-policy.md`.

Do not stop the campaign for ordinary failures. Always produce a structured handoff or broker-persisted artifact.
