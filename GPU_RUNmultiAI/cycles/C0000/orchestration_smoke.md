# C0000 Multi-AI orchestration smoke report

## Status

**PASS_WITH_LIMITATIONS**. C0000 is infrastructure/bootstrap only and contains no scientific result.

## Acceptance matrix

| Requirement | Result | Evidence |
|---|---|---|
| Claude callable | PASS | `claude_smoke.md`; wrapper exit 0 |
| Cursor callable | PASS | `cursor_smoke.md`; wrapper exit 0 |
| Gemini callable | PASS | authenticated Antigravity model ran twice and returned structured denial metadata |
| Write-mode task works | PASS | Claude and Cursor each created and committed their scoped artifact |
| Isolated Git worktree creation | PASS | three distinct branches/worktrees from `4a97d31` |
| Worker edit/test/commit | PASS | Claude `a5f1c99`; Cursor `5ab8bea` |
| PI commit inspection/integration | PASS | cherry-picked as `942a5bc`, `6726cea`, `93b66db` |
| Codex subagent delegation | PASS | `subagent_smoke.md`; fallback commit source `ee12453` |
| Resumable state persistence | PASS | `research_state.md` advances to C0001 with exact next action |

## Limitation and recovery

Gemini/Antigravity was callable, but its headless write-mode run soft-denied `ListDir` / `read_file` and exited 0
without producing an artifact. One scoped permission configuration retry produced the same outcome. The temporary
user-level permission additions were removed after diagnosis. C0000 therefore does not claim that Gemini's current
headless filesystem write path works. C0001 should route Gemini tasks that require repository files through a
prompt-supplied evidence packet or use the declared Luna/subagent fallback until the launcher is repaired.

This is recoverable infrastructure degradation, not a hard stop. No dangerous global permission bypass was used.

## Scientific boundary

No hypothesis, measurement, result, analysis, or cycle decision from PR #4 / `GPU_RUNclaude1` was imported.
