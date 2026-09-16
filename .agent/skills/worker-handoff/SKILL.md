---
name: worker-handoff
description: Create concise, self-contained tasks and completion handoffs between Codex, Claude, Cursor, Gemini, Luna, and subagents.
---
# Worker Handoff

Use `.agent/schemas/task-handoff-schema.md`.

Avoid forwarding entire conversations.
Reference authoritative files and persist large outputs to the repository.
Require a completion record with commit, tests, findings, deviations, unresolved risks, and next action.

For reconnaissance and bulk tasks, include:
- `files_inspected` with path-level provenance
- `evidence_provenance` separating evidence, inference, and speculation
- `evidence_packet` path when a structured packet is produced

For implementation and review tasks, include:
- `implementer_identity` (worker/model that produced the artifact)
- `independent_reviewer_identity` (worker/model assigned adversarial/final review)
- `reviewer_diff_assertion: true` when reviewer differs from implementer
- `reviewer_independence_exception` only when a documented hard-stop exception is approved

**Enforceable assertion:** do not mark a task complete when the independent reviewer is the same worker as the
implementer unless `reviewer_independence_exception` is recorded.

Apply capacity-aware routing defaults from `.agent/rules/08-routing-and-delegation.md` when choosing `preferred_worker`.
Oversize prompt-supplied evidence packets: split deterministically per `.agent/rules/08-routing-and-delegation.md`.
