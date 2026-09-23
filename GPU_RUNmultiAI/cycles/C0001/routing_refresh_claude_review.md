# C0001-INFRA-T003 independent Claude Opus 5.5 review

Verdict: **BLOCK** pending remediation. Read-only review; Claude CLI `modelUsage` identified `claude-opus-5-5`. The reviewer could not run shell commands, so PI must independently verify diff, tests, manifest, and remote SHA.

## P1 findings

1. `.ai/workers/gemini.sh`: artifact/provenance persistence failures can still return success (`set -uo pipefail` and unchecked `mkdir`, `cp`, hash, Python writer). Add fail-closed behavior and tests.
2. `.ai/workers/gemini.sh`, `.codex/rules/ai-workers.rules`, `.agent/rules/08-routing-and-delegation.md`: Gemini direct `--write` / broker `--write` remain allowed despite unpassed filesystem E2E. Gate direct writes until a five-step PASS; broker must be read-only.
3. `.ai/workers/gemini.sh`: default `non-empty` acceptance might accept an exit-0 soft-deny diagnostic. Reject known deny markers and require structured acceptance for evidence tasks.
4. `.agent/routing/MODEL_ROUTING.md`: Research PI fallback to Claude Opus 5.5 conflicts with the user's requirement that Claude not become PI. Route fallback to GPT-6 Astra or explicit human decision.
5. `GPU_RUNmultiAI/cycles/C0001/routing_refresh_gemini_fs_e2e.md`, `GPU_RUNmultiAI/task_board.md`: `PASS_WITH_LIMITATIONS` is misleading when step 1 failed and zero of five steps passed. Direct FS verdict must be FAIL; broker PASS separately.

## P2 follow-ups

- Resolve conflicting scientific resume conditions and self-referential/stale commit fields in `research_state.md`.
- Reconcile agy version in broker packet, stale Cursor smoke test count, and README statements about wrapper exit codes.
- Rebuild Gemini review evidence from the final diff, not the earlier pre-remediation tree. Keep Gemini speculation separate from verified fact.
- Align remaining `~10k` threshold / legacy preferred-model wording where current; consider broker acceptance/provenance handoff fields.
- Ensure failed broker calls cannot silently reuse stale artifacts; document packet-size/chunking limit.

The reviewer did **not** require Gemini direct filesystem PASS; a verified broker fallback is acceptable. Review provenance: Claude CLI read-only invocation on routing-refresh worktree, 2026-09-23; `modelUsage.claude-opus-5-5.canonicalModel = claude-opus-5-5`, no subagents, no edits.
