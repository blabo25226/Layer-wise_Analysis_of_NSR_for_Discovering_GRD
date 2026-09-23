# Minimal broker packet (post-remediation)

Summarize only the facts below. Use headings ## Evidence, ## Inference, ## Speculation.

Facts:
- Integration base df39f61; routing-refresh branch; Claude Opus 5.5 independent review verdict BLOCK remediated.
- gemini.sh: fail-closed broker persistence; deny-marker rejection; evidence paths require headings acceptance; direct --write blocked without FS E2E pass file; broker rejects --write.
- Codex ai-workers.rules: gemini --write deny; broker allow example uses headings (evidence/packet paths enforced in gemini.sh).
- MODEL_ROUTING: PI fallback is GPT-6 Astra or human decision, not Claude.
- Direct Gemini FS E2E: FAIL 0/5 at list step; pre-remediation broker smoke PASS 06:47 UTC; post-remediation live broker FAIL exit 70; agy 1.2.9; model gemini-3.8-flash-high.
- tests/test_ai_workers_gemini_broker.py: 15 passed (focused broker tests).
- Do not invent SHAs or test counts.
