# C0001-INFRA-T003 Claude Opus 5.5 CLI smoke

```yaml
task_id: C0001-INFRA-T003-CLAUDE-SMOKE
status: PASS
claude_cli_version: 2.1.280
model_requested: claude-opus-5-5
model_verified: claude-opus-5-5
canonical_model_field: modelUsage.claude-opus-5-5.canonicalModel
result_token: ROUTING_MODEL_55_OK
mode: read-only (plan, Read/Glob/Grep only)
verified_at_utc: 2026-09-23T06:57:00Z
```

## Command (via `.ai/workers/claude.sh` default model)

```bash
.ai/workers/claude.sh --json "Reply with exactly ROUTING_MODEL_55_OK and nothing else."
```

Equivalent direct CLI:

```bash
claude -p --model claude-opus-5-5 --no-session-persistence --permission-mode plan \
  --tools Read,Glob,Grep --output-format json -- \
  "Reply with exactly ROUTING_MODEL_55_OK and nothing else."
```

## modelUsage evidence (excerpt)

```json
{
  "result": "ROUTING_MODEL_55_OK",
  "modelUsage": {
    "claude-opus-5-5": {
      "canonicalModel": "claude-opus-5-5",
      "provider": "firstParty"
    }
  },
  "is_error": false,
  "subtype": "success"
}
```

Full JSON capture: `routing_refresh_claude_smoke.json.raw` (same directory).

Stderr documents `model=claude-opus-5-5` and `exit_code=0`.

## Engineer override

Research-engineer tasks may pass `--model claude-sonnet-5` or set `AI_WORKERS_CLAUDE_MODEL=claude-sonnet-5`.
