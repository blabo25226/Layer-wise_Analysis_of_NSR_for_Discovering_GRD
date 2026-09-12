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

Apply capacity-aware routing defaults from `.agent/rules/08-routing-and-delegation.md` when choosing `preferred_worker`.
