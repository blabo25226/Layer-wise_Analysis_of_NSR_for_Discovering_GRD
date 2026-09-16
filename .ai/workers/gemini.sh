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
    printf 'gemini worker: prompt must not be empty\n' >&2
    exit 64
fi

antigravity_bin="${AI_WORKERS_ANTIGRAVITY_BIN:-/home/blabo/.local/bin/agy}"
if [[ ! -x "$antigravity_bin" ]]; then
    printf 'gemini worker: Antigravity executable not found at %s\n' "$antigravity_bin" >&2
    printf 'Set AI_WORKERS_ANTIGRAVITY_BIN to the agy executable.\n' >&2
    exit 127
fi

agent_mode="plan"
if [[ "$mode" == "write" ]]; then
    agent_mode="accept-edits"
fi
command_args=(
    "$antigravity_bin"
    -p "$prompt"
    --mode "$agent_mode"
    --sandbox
    --output-format "$output_format"
    --print-timeout "${AI_WORKERS_PRINT_TIMEOUT:-5m}"
)

printf 'worker=gemini mode=%s output_format=%s\n' "$mode" "$output_format" >&2
"${command_args[@]}"
worker_status=$?
printf 'worker=gemini exit_code=%d\n' "$worker_status" >&2
exit "$worker_status"
