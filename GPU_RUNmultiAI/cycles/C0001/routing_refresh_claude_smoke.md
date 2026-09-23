# C0001-INFRA-T003 Claude Opus 5.5 CLI smoke

```yaml
task_id: C0001-INFRA-T003-CLAUDE-SMOKE
status: PASS
model_observed: Claude Opus 5.5
mode: read-only (plan, Read/Glob/Grep only)
verified_at_utc: 2026-09-23T06:46:00Z
```

## Command

```bash
claude -p --no-session-persistence --permission-mode plan --tools Read,Glob,Grep --output-format text -- \
  "Read-only smoke: reply with exactly ROUTING_REFRESH_CLAUDE_OK and the first line of .agent/agents/scientific-critic.md frontmatter preferred_model field only."
```

## Observed stdout (excerpt)

```text
ROUTING_REFRESH_CLAUDE_OK
Claude Opus 5.5
```

Exit code: 0.
