---
name: literature-evidence
description: Gather and verify literature or official implementation evidence relevant to a cycle hypothesis.
---
# Literature Evidence

- Prefer primary papers and official repositories/docs.
- Verify identifiers/URLs when possible.
- Distinguish source evidence from inference and speculation.
- Record search date.
- Label novelty as `known`, `adjacent`, `plausibly_novel`, or `unverified`.
- Use Gemini/bulk workers for breadth (~10k+ token corpora) and an independent critic for high-stakes novelty judgments.
- Use Cursor `repo-operator` for repository structure reconnaissance when 5+ substantive files are involved.
- Store durable notes in `GPU_RUNmultiAI/literature/` or the cycle directory.
