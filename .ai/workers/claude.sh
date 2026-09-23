#!/usr/bin/env bash

set -uo pipefail

usage() {
    cat >&2 <<'EOF'
Usage:
  claude.sh [--write] [--json] [--model MODEL] "PROMPT"
  printf "PROMPT" | claude.sh [--write] [--json] [--model MODEL]

Default model: claude-opus-5-5 (critique, review, audit roles).
Override with --model or AI_WORKERS_CLAUDE_MODEL (e.g. claude-sonnet-5 for research-engineer).
EOF
}

mode="read"
output_format="text"
claude_model="${AI_WORKERS_CLAUDE_MODEL:-claude-opus-5-5}"

while (( $# > 0 )); do
    case "$1" in
        --write)
            mode="write"
            shift
            ;;
        --json)
            output_format="json"
            shift
            ;;
        --model)
            claude_model="${2:-}"
            shift 2
            ;;
        --)
            shift
            break
            ;;
        -*)
            printf 'claude worker: unknown option %s\n' "$1" >&2
            usage
            exit 64
            ;;
        *)
            break
            ;;
    esac
done

if (( $# == 1 )); then
    prompt=$1
elif (( $# == 0 )) && [[ ! -t 0 ]]; then
    prompt=$(</dev/stdin)
else
    usage
    exit 64
fi

if [[ -z "$prompt" ]]; then
    printf 'claude worker: prompt must not be empty\n' >&2
    exit 64
fi
if ! command -v claude >/dev/null 2>&1; then
    printf 'claude worker: claude executable not found in PATH\n' >&2
    exit 127
fi

command_args=(
    claude
    -p
    --no-session-persistence
    --model "$claude_model"
    --output-format "$output_format"
)
if [[ "$mode" == "read" ]]; then
    command_args+=(--permission-mode plan --tools Read,Glob,Grep)
else
    command_args+=(--permission-mode acceptEdits)
fi
command_args+=(-- "$prompt")

printf 'worker=claude mode=%s output_format=%s model=%s\n' \
    "$mode" "$output_format" "$claude_model" >&2
"${command_args[@]}"
worker_status=$?
printf 'worker=claude exit_code=%d\n' "$worker_status" >&2
exit "$worker_status"
