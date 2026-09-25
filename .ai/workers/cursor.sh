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
    printf 'cursor worker: prompt must not be empty\n' >&2
    exit 64
fi
if ! command -v agent >/dev/null 2>&1; then
    printf 'cursor worker: agent executable not found in PATH\n' >&2
    exit 127
fi

command_args=(
    agent
    -p
    --trust
    --output-format "$output_format"
)
if [[ "$mode" == "read" ]]; then
    command_args+=(--mode=ask)
else
    command_args+=(--auto-review)
fi
command_args+=("$prompt")

printf 'worker=cursor mode=%s output_format=%s\n' "$mode" "$output_format" >&2
"${command_args[@]}"
worker_status=$?
printf 'worker=cursor exit_code=%d\n' "$worker_status" >&2
exit "$worker_status"
