# Worker fallback routing

Suggested fallback sequence:

- **Repository reconnaissance (5+ files):** Cursor Composer → Luna explore → PI diagnosis.
- **Repo implementation (multi-file):** Cursor Composer → Claude Sonnet → Luna (only if small) → PI diagnosis.
- **Scientific engineering:** Claude Sonnet → Cursor Composer → PI.
- **Deep critique/statistics:** Claude Opus → PI → independent second pass.
- **Bulk scan/log/index (~10k+ tokens):** Gemini Flash → Luna → Cursor Explore/Bash subagent.
- **Gemini filesystem write:** **limited** until headless E2E passes. Until then use prompt-supplied evidence tasks or route
  persistence to Cursor/Claude/Codex fallback. Never treat Gemini wrapper exit code 0 alone as task success.
- **Small mechanical task:** Luna → Gemini Flash → local direct PI only if delegation overhead exceeds work.
- **Report drafting:** Gemini Flash (first draft) → Claude Sonnet (review/polish) → Luna → PI final claims.
- **Worker infrastructure failure:** retry once → alternate worker → record infrastructure issue → continue.

## Capacity pressure

Under capacity pressure, apply the fallback sequences above for routine work only.
Do not demote preregistration, final scientific review, primary-artifact verification, leakage protection, or
replication gates.

## Prohibited fallback patterns

- silently replacing an independent reviewer with the implementing worker
- routing final scientific decisions to Gemini
- accepting Cursor implementation summaries as unsupported scientific conclusions
- duplicating reconnaissance across Codex, Claude, and Cursor without recorded reason

Do not silently replace an "independent reviewer" with the same worker that implemented the result.
