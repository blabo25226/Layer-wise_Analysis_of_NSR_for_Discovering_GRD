---
name: evidence-compression
description: Gemini-first mechanical compression, classification, and deduplication of logs, artifacts, and worker outputs before PI or Claude review.
---
# Evidence Compression

Use when Gemini-first triggers in `.agent/rules/08-routing-and-delegation.md` apply.

## Workflow

1. Cursor or the PI assembles a **deterministic evidence packet** (paths, hashes, excerpts — no credentials).
2. Run Gemini via **broker mode** when repository filesystem access is unverified:

```bash
.ai/workers/gemini.sh --broker \
  --prompt-file path/to/packet.md \
  --output-file path/to/compressed.md \
  --acceptance headings
```

3. Verify: non-empty artifact, provenance sidecar, required structure (evidence / inference / speculation separated).
4. Route the compressed artifact to Claude Opus 5.5 for critique or to GPT-6 Sol PI for synthesis — not raw bulk input.

## Output requirements

- Preserve numerical values and identifiers when present in the packet.
- Do not make final scientific decisions or cycle verdicts.
- Record failure counts and malformed inputs instead of silent drops.

## Related skills

- `literature-evidence` for breadth and candidate classification
- `worker-handoff` for task schema and provenance fields
