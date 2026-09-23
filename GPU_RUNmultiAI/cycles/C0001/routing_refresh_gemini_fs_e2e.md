# C0001-INFRA-T003 Gemini direct filesystem E2E

```yaml
task_id: C0001-INFRA-T003-FS-E2E
direct_filesystem_verdict: FAIL
direct_filesystem_steps_passed: 0
broker_mode_verdict: PASS
status: direct_FS_FAIL_broker_PASS
verdict: broker_mode_remains_standard
agy_version: 1.2.9
model_flag: gemini-3.8-flash-high
tested_at_utc: 2026-09-23T06:55:19Z
disposable_worktree: /tmp/gemini-fs-e2e-1l1HQ6
first_failure_step: 1 (list)
steps_attempted: list, read, create, reread, delete (bounded; halted at step 1)
```

## Procedure (five-step bounded attempt)

1. **list** — `agy` in `accept-edits` + `--sandbox` asks to list files and emit `FS_E2E_LIST_OK`.
2. **read** — read `README.md` (not reached).
3. **create** — create `agy_fs_probe.txt` with `FS_E2E_OK` (not reached).
4. **reread** — read created file (not reached).
5. **delete** — delete probe file (not reached).

Disposable repo: `git init`, commit `README.md` with `FS_E2E_PROBE_BASE`.

Step log: `routing_refresh_gemini_fs_e2e_steps.log`.

## Result

**FAIL at step 1 (list)** — CLI exit code 0 but no usable output:

```text
jetski: no output produced — a tool required the "command" permission that headless mode cannot prompt for, so it was auto-denied.
```

Steps 2–5 were not executed.

## Implication

Direct Antigravity filesystem/command tools remain unreliable in headless sandbox without explicit permission allow-rules or `--dangerously-skip-permissions` (not enabled in `.ai/workers/gemini.sh`).

**Broker mode PASS** — see `routing_refresh_gemini_broker_smoke.md`, `routing_refresh_review_compressed.md`, and provenance JSON sidecars.

## CLI model availability

`agy models` lists `gemini-3.8-flash-high`; wrapper default `AI_WORKERS_GEMINI_MODEL=gemini-3.8-flash-high`.
