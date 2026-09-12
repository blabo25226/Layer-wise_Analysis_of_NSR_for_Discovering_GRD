# AI worker CLI wrappers

This directory contains thin wrappers that let Codex call the three installed
coding-agent CLIs without mixing orchestration code into the LANSR research
runtime.

## Usage

Run these commands from the repository root:

```bash
.ai/workers/claude.sh "Review the design without changing files."
.ai/workers/cursor.sh "Check this implementation without changing files."
.ai/workers/gemini.sh "Summarize this log without changing files."
```

Each wrapper accepts exactly one quoted prompt. A multiline prompt can instead
be supplied on standard input:

```bash
printf '%s\n' "First line" "Second line" | .ai/workers/claude.sh
```

The default mode is read-only:

- Claude Code receives only its `Read`, `Glob`, and `Grep` tools in plan mode.
- Cursor Agent runs in ask mode.
- Gemini runs through Antigravity CLI in `plan` mode and its terminal sandbox.

Use `--write` only when file edits are explicitly intended. The wrappers still
do not enable Claude's permission bypass, Cursor's `--force`/`--yolo`, or
Antigravity's `--dangerously-skip-permissions` mode.

```bash
.ai/workers/cursor.sh --write "Implement the requested change and run focused tests."
```

Use `--json` after the optional `--write` flag for the CLI's native structured
output:

```bash
.ai/workers/gemini.sh --json "Return a short status summary."
```

The model response is written to stdout. Worker identity, mode, and the final
process exit code are written to stderr. The wrapper itself exits with the same
code as the worker process.

## Installed commands and authentication

Verified on 2026-09-12:

| Worker | Command | Version | Authentication |
|---|---|---|---|
| Claude Code | `claude` | `2.1.226` | CLI-managed Claude account login |
| Cursor Agent | `agent` / `cursor-agent` | `2026.09.10-fd3934a` | CLI-managed Cursor browser login |
| Gemini via Antigravity CLI | `agy` | `1.2.2` | CLI-managed Google AI Pro login |

The standalone Gemini CLI `0.59.0` and Node.js 22 are also installed in the
`ai-workers-node` Conda environment. Google no longer supports Google AI
Pro/Ultra consumer-account login in that CLI, so the repository wrapper uses
the official Antigravity successor instead. A user-local `gemini` launcher is
retained for diagnostics, but it is not used by `.ai/workers/gemini.sh`.
Override the Antigravity executable with `AI_WORKERS_ANTIGRAVITY_BIN` if it is
moved. Override its five-minute non-interactive wait with
`AI_WORKERS_PRINT_TIMEOUT` when a longer task is intentional.

No wrapper reads or stores passwords, OAuth tokens, session cookies, or API
keys. Authentication remains owned by each official CLI.

The installations followed the official setup paths:

```bash
curl https://cursor.com/install -fsS | bash
conda create -n ai-workers-node -c conda-forge nodejs=22
conda run -n ai-workers-node npm install -g @google/gemini-cli
curl -fsSL https://antigravity.google/cli/install.sh | bash
```

Official references:

- [Claude Code CLI reference](https://docs.anthropic.com/en/docs/claude-code/cli-usage)
- [Cursor CLI overview](https://docs.cursor.com/en/cli/overview)
- [Gemini Code Assist for individuals deprecation](https://developers.google.com/gemini-code-assist/docs/deprecations/code-assist-individuals)
- [Antigravity CLI installation](https://antigravity.google/docs/cli/install/)
- [Antigravity CLI headless mode](https://antigravity.google/docs/cli/headless/)
- [Codex command rules](https://learn.chatgpt.com/docs/agent-configuration/rules)

## Codex command rules

Project-local rules in `.codex/rules/ai-workers.rules` use a single `allow`
policy for all authorized wrapper prefixes, including `--write` invocations.
There is no separate `ai-workers-full-access.rules` file. The project must be
trusted and Codex must be restarted after the rules are first added or changed.

## Delegated write tasks

Use `--write` only for isolated tasks with an explicit worktree/branch and a
declared write scope. Do not run parallel write tasks in the same checkout.

A delegated task succeeds only when the expected artifact(s), acceptance
test(s), and any required commit are present. Process exit code alone is
insufficient, especially for Gemini/Antigravity headless work. Canonical policy:
`.agent/rules/09-subagent-policy.md` and `.agent/schemas/task-handoff-schema.md`.
