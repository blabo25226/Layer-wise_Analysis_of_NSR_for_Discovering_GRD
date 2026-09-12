---
name: gemini-scout
description: Prefer Gemini/Antigravity for broad scans, logs, indexes, literature candidate collection, and bulk work.
---
For scientific conclusions or high-impact novelty claims, flag results for independent critic/PI review.
Keep evidence and inference separate.

Headless Antigravity may soft-deny filesystem writes and still exit 0. Until filesystem E2E passes,
use prompt-supplied evidence tasks or route persistence to Cursor/Claude/Codex fallback; never treat exit 0 alone
as task success. Canonical policy: `.agent/routing/FALLBACKS.md` and `.agent/rules/09-subagent-policy.md`.
