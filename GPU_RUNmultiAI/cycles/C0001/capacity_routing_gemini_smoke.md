# C0001-INFRA-T002 Gemini evidence-compression smoke

Worker: Gemini via Antigravity (`research-scout` / `bulk-worker`)
Mode: read-only, prompt-supplied evidence packet; no repository filesystem access requested
Upstream packet: `GPU_RUNmultiAI/cycles/C0001/repo_evidence_inventory.md`
Date: 2026-09-12
Process result: exit code 0 with required structured output present

## Required categories returned

- core routing and threshold policies
- agent role definitions
- workflow and lifecycle coordination
- handoff schemas and skills
- provider adapters
- immutable scientific guards and excluded scientific artifacts

## Deduplicated findings

1. Assign repository reconnaissance involving five or more substantive files to Cursor and make the repo-operator role
   `Repository Intelligence + Implementation`.
2. Use Gemini for report first drafts, Claude Sonnet for scientific review/polish, and the PI for final claims.
3. Use Gemini as a prompt-supplied bulk processor for roughly 10k or more mechanically processable tokens while
   Antigravity filesystem access is unavailable.
4. Add evidence-packet provenance fields to handoffs and require evidence/inference/speculation separation.
5. Keep provider adapters thin and synchronized to canonical `.agent/` rules.

The returned path provenance pointed to the Cursor inventory and the primary canonical files rather than inventing
new repository evidence.

## Unresolved questions identified

- define what counts as a substantive file for the five-file threshold
- confirm the reconnaissance fallback when Cursor is unavailable or context-limited
- mechanically verify that Gemini first drafts do not alter numeric artifact values
- choose a chunking rule for prompt-supplied packets that exceed a practical Gemini context size

## Candidate routing risks identified

- accidental weakening of preregistration, leakage, independent-review, or replication guards
- upstream evidence omission causing prompt-only Gemini hallucination
- claim inflation during Claude polish
- Cursor reconnaissance expanding into premature edits or test manipulation
- provider adapter drift

## Evidence / inference / speculation separation

Gemini explicitly separated repository-grounded evidence from routing inferences and speculation. One speculative claim
estimated a 30–50% efficiency gain without evidence. The PI rejects that number; no quantitative efficiency benefit is
claimed by this smoke.

## Acceptance verdict

`PASS_WITH_LIMITATIONS`

- PASS: all requested sections were returned; findings were deduplicated; unresolved risks were surfaced; path
  provenance was retained; no final scientific decision was attempted.
- PASS: the packet reduced Claude's proposed primary-file audit to four files:
  `.agent/rules/08-routing-and-delegation.md`, `.agent/routing/MODEL_ROUTING.md`,
  `.agent/routing/FALLBACKS.md`, and `GPU_RUNmultiAI/RESEARCH_LOOP.md`.
- LIMITATION: Gemini emitted malformed `file://` Markdown links; this artifact preserves paths as plain repository
  paths instead.
- LIMITATION: filesystem E2E remains unverified, so prompt-supplied mode stays mandatory for Gemini repository work.
- LIMITATION: exit code 0 was not used alone; acceptance also required structured content and path provenance.

