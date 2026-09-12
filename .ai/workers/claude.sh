#!/usr/bin/env bash

set -uo pipefail

usage() {
    printf 'Usage: %s [--write] [--json] "PROMPT"\n' "$0" >&2
    printf '       printf "PROMPT" | %s [--write] [--json]\n' "$0" >&2
}

mode="read"
output_format="text"

if [[ "${1:-}" == "--write" ]]; then
    mode="write"
    shift
fi
if [[ "${1:-}" == "--json" ]]; then
    output_format="json"
    shift
fi
if [[ "${1:-}" == "--" ]]; then
    shift
fi

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
    --output-format "$output_format"
)
if [[ "$mode" == "read" ]]; then
    command_args+=(--permission-mode plan --tools Read,Glob,Grep)
else
    command_args+=(--permission-mode acceptEdits)
fi
command_args+=(-- "$prompt")

printf 'worker=claude mode=%s output_format=%s\n' "$mode" "$output_format" >&2
"${command_args[@]}"
worker_status=$?
printf 'worker=claude exit_code=%d\n' "$worker_status" >&2
exit "$worker_status"
