# Multi-AI Task Board

This is a human-readable mirror of active delegated tasks.
`research_state.md` remains the machine-resumable authority.

| Task ID | Cycle | Track | Role | Worker | Branch/worktree | Write scope | Status | Next |
|---|---|---|---|---|---|---|---|---|
| C0000-T001 | C0000 | infrastructure | scientific-critic | Claude Code | `ai/C0000/scientific-critic/claude-smoke` / `/tmp/lansr-multiai-C0000-claude-smoke` | `claude_smoke.md` | integrated | PASS |
| C0000-T002 | C0000 | infrastructure | repo-operator | Cursor Agent | `ai/C0000/repo-operator/cursor-smoke` / `/tmp/lansr-multiai-C0000-cursor-smoke` | `cursor_smoke.md` | integrated | PASS |
| C0000-T003 | C0000 | infrastructure | research-scout | Gemini / Antigravity + subagent fallback | `ai/C0000/research-scout/gemini-smoke` / `/tmp/lansr-multiai-C0000-gemini-smoke` | `gemini_smoke.md` | integrated with limitation | prompt-supplied evidence until Gemini filesystem E2E passes |
| C0000-T004 | C0000 | infrastructure | fast-worker | Codex subagent | read-only then T003 fallback worktree | `subagent_smoke.md`, fallback record | completed | PASS |
| C0001-T001 | C0001 | scientific | research-scout | Codex subagent | shared read-only checkout | none | completed | state reconstructed |
| C0001-T002 | C0001 | scientific | hypothesis-scientist | Codex subagent | shared read-only checkout | none | completed | seven candidates returned |
| C0001-T003 | C0001 | scientific | statistical-reviewer / critic | Codex subagent + Claude Opus fallback | shared read-only checkout | none | completed with fallback | metric validity issue promoted for verification |
| C0001-T004 | C0001 | scientific | research-engineer | Claude Code | `ai/C0001/research-engineer/preregister-metric-audit` / `/tmp/lansr-multiai-C0001-preregister` | four C0001 planning artifacts | integrated | preregistration draft committed |
| C0001-INFRA-T001 | C0001 | infrastructure | repo-operator | Cursor Agent | `ai/C0001/repo-operator/pr5-infra` / `/tmp/lansr-multiai-C0001-pr5-infra` | PR #5 scoped infrastructure files | integrated and pushed | PASS; remote SHA verified |
| C0001-INFRA-T002 | C0001 | infrastructure | repo-operator | Cursor Agent | `ai/C0001/repo-operator/capacity-routing` / `/tmp/lansr-multiai-C0001-capacity-routing` | routing rules, roles, adapters, evidence inventory, smoke | completed | canonical routing updated; review fixes applied |
| C0001-INFRA-T002-GEMINI-SMOKE | C0001 | infrastructure | research-scout | Gemini / Antigravity | shared capacity-routing worktree | prompt-supplied evidence packet | completed | PASS_WITH_LIMITATIONS; see gemini_smoke.md |
| C0001-INFRA-T002-CLAUDE-SMOKE | C0001 | infrastructure | scientific-critic | Claude Opus | shared capacity-routing worktree | compressed-packet audit | completed | REVISE; see claude_review.md; H1-H7 fixes applied |
| C0001-INFRA-T002-PI-INTEGRATION | C0001 | infrastructure | research-pi | Codex PI | shared capacity-routing worktree | integrate to remote research branch | pending | integrate review fixes, push, verify remote SHA |
