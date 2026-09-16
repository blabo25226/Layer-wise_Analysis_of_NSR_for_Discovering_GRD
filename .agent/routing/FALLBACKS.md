# Worker fallback routing

Suggested fallback sequence (aligned with `.agent/routing/MODEL_ROUTING.md`):

- **Repository reconnaissance (5+ substantive files):** Cursor Composer → Luna explore → PI diagnosis.
  Codex/Claude broad reconnaissance is **not** a routine fallback; require a recorded PI exception and reason.
- **Repo implementation (multi-file):** Cursor Composer → Claude Sonnet → Luna (only if small) → PI diagnosis.
- **Scientific engineering:** Claude Sonnet → Cursor Composer → PI.
- **Deep critique/statistics:** Claude Opus → PI → independent second pass.
- **Research-scout / bulk scan/log/index (~10k+ tokens):** Gemini Flash → Cursor Composer → Luna.
  Codex/Claude bulk reconnaissance is **not** a routine fallback; require a recorded PI exception and reason.
- **Gemini filesystem write:** **limited** until headless E2E passes. Until then use prompt-supplied evidence tasks or route
  persistence to Cursor/Claude/Codex fallback. Never treat Gemini wrapper exit code 0 alone as task success.
- **Evidence-packet oversize:** when a prompt-supplied packet approaches the configured/request limit or exceeds one worker
  context, split deterministically by artifact/run/logical section; preserve chunk IDs and provenance; deduplicate only
  after chunk summaries; retain links to primary artifacts. Do not invent a universal token ceiling.
- **Small mechanical task:** Luna → Gemini Flash → local direct PI only if delegation overhead exceeds work.
- **Report drafting:** Gemini Flash (first draft) → numeric-fidelity check against primary JSON/CSV → Claude Sonnet
  (review/polish) → Luna → PI final claims.
- **Worker infrastructure failure:** retry once → alternate worker → record infrastructure issue → continue.

## Capacity pressure

Under capacity pressure, apply the fallback sequences above for routine work only.
Do not demote preregistration and metric freeze, final scientific review and reviewer independence,
primary-artifact verification, leakage protection, or replication gates.

## Prohibited fallback patterns

- silently replacing an independent reviewer with the implementing worker
- routing final scientific decisions to Gemini
- accepting Cursor implementation summaries as unsupported scientific conclusions
- duplicating reconnaissance across Codex, Claude, and Cursor without recorded reason
- routine broad reconnaissance to Codex or Claude without a recorded PI exception

Do not silently replace an "independent reviewer" with the same worker that implemented the result.
Record `implementer_identity` and `independent_reviewer_identity` in handoffs and state; assert they differ unless a
documented hard-stop exception is approved.
