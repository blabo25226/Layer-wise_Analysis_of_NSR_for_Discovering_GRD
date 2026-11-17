#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
REPO_ROOT=$(cd "$SCRIPT_DIR/../.." && pwd)
FS_E2E_PASS_MARKER="${AI_WORKERS_GEMINI_FS_E2E_PASS_FILE:-$REPO_ROOT/GPU_RUNmultiAI/.runtime/gemini_direct_fs_e2e.pass}"

usage() {
    cat >&2 <<'EOF'
Usage:
  gemini.sh [--write] [--json] "PROMPT"
  printf "PROMPT" | gemini.sh [--write] [--json]
  gemini.sh --broker --prompt-file PACKET --output-file ARTIFACT \
    [--provenance-file PATH] [--acceptance MODE]

Broker mode runs Antigravity print mode, captures stdout, validates acceptance,
and persists the artifact locally (Gemini does not need repository filesystem access).
Broker mode is read-only: --write is not allowed with --broker.

Direct --write requires a recorded five-step filesystem E2E PASS marker file
(GPU_RUNmultiAI/.runtime/gemini_direct_fs_e2e.pass).

Acceptance modes (broker):
  non-empty   output must be non-whitespace and must not match headless deny markers
  headings    output must contain ## Evidence, ## Inference, ## Speculation
  json        output must be valid JSON object or array

Evidence-style prompt/output paths (evidence, packet, compressed) require headings acceptance.
EOF
}

gemini_broker_reject_deny_markers() {
    local capture_path="$1"
    if grep -qiE 'auto-denied|no output produced|jetski:' "$capture_path"; then
        printf 'gemini worker: broker rejected headless deny-marker output despite exit 0\n' >&2
        return 1
    fi
    return 0
}

gemini_broker_requires_structured_acceptance() {
    local prompt_path="$1"
    local artifact_path="$2"
    local prompt_base artifact_base
    prompt_base=$(basename "$prompt_path")
    artifact_base=$(basename "$artifact_path")
    [[ "$prompt_base" == *evidence* || "$prompt_base" == *packet* \
        || "$artifact_base" == *evidence* || "$artifact_base" == *compressed* ]]
}

gemini_broker_validate_acceptance_mode() {
    case "$1" in
        non-empty|headings|json)
            return 0
            ;;
        *)
            printf 'gemini worker: unknown acceptance mode %s\n' "$1" >&2
            return 1
            ;;
    esac
}

mode="read"
output_format="text"
broker_mode=0
prompt_file=""
output_file=""
provenance_file=""
acceptance="non-empty"

antigravity_bin="${AI_WORKERS_ANTIGRAVITY_BIN:-/home/blabo/.local/bin/agy}"
gemini_model="${AI_WORKERS_GEMINI_MODEL:-gemini-3.8-flash-high}"

while (( $# > 0 )); do
    case "$1" in
        --broker)
            broker_mode=1
            shift
            ;;
        --prompt-file)
            prompt_file="${2:-}"
            shift 2
            ;;
        --output-file)
            output_file="${2:-}"
            shift 2
            ;;
        --provenance-file)
            provenance_file="${2:-}"
            shift 2
            ;;
        --acceptance)
            acceptance="${2:-}"
            shift 2
            ;;
        --write)
            mode="write"
            shift
            ;;
        --json)
            output_format="json"
            shift
            ;;
        --)
            shift
            break
            ;;
        -*)
            printf 'gemini worker: unknown option %s\n' "$1" >&2
            usage
            exit 64
            ;;
        *)
            break
            ;;
    esac
done

if (( broker_mode == 1 )) && [[ "$mode" == "write" ]]; then
    printf 'gemini worker: --broker is read-only; omit --write (local shell persists artifacts)\n' >&2
    exit 64
fi

if [[ "$mode" == "write" ]] && [[ ! -f "$FS_E2E_PASS_MARKER" ]]; then
    printf 'gemini worker: direct --write blocked until five-step filesystem E2E PASS (%s)\n' \
        "$FS_E2E_PASS_MARKER" >&2
    printf 'Use --broker for packet stdout persistence or route edits to Cursor.\n' >&2
    exit 78
fi

if (( broker_mode == 1 )); then
    if [[ -z "$prompt_file" || -z "$output_file" ]]; then
        printf 'gemini worker: broker mode requires --prompt-file and --output-file\n' >&2
        usage
        exit 64
    fi
    if [[ ! -f "$prompt_file" ]]; then
        printf 'gemini worker: prompt file not found: %s\n' "$prompt_file" >&2
        exit 66
    fi
    if gemini_broker_requires_structured_acceptance "$prompt_file" "$output_file" \
        && [[ "$acceptance" == "non-empty" ]]; then
        printf 'gemini worker: evidence/packet tasks require --acceptance headings (or json)\n' >&2
        exit 74
    fi
    if ! gemini_broker_validate_acceptance_mode "$acceptance"; then
        exit 64
    fi
    if [[ -z "$provenance_file" ]]; then
        provenance_file="${output_file}.provenance.json"
    fi
    prompt=$(<"$prompt_file")
else
    if (( $# == 1 )); then
        prompt=$1
    elif (( $# == 0 )) && [[ ! -t 0 ]]; then
        prompt=$(</dev/stdin)
    else
        usage
        exit 64
    fi
fi

if [[ -z "$prompt" ]]; then
    printf 'gemini worker: prompt must not be empty\n' >&2
    exit 64
fi

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
    --model "$gemini_model"
    --sandbox
    --output-format "$output_format"
    --print-timeout "${AI_WORKERS_PRINT_TIMEOUT:-5m}"
)

printf 'worker=gemini mode=%s output_format=%s broker=%s model=%s\n' \
    "$mode" "$output_format" "$broker_mode" "$gemini_model" >&2

if (( broker_mode == 1 )); then
    stdout_capture=$(mktemp)
    trap 'rm -f "$stdout_capture"' EXIT
    "${command_args[@]}" >"$stdout_capture"
    worker_status=$?
    printf 'worker=gemini exit_code=%d\n' "$worker_status" >&2
    if (( worker_status != 0 )); then
        exit "$worker_status"
    fi
    if [[ ! -s "$stdout_capture" ]] || [[ -z "$(tr -d '[:space:]' <"$stdout_capture")" ]]; then
        printf 'gemini worker: broker rejected empty stdout despite exit 0\n' >&2
        exit 70
    fi
    if ! gemini_broker_reject_deny_markers "$stdout_capture"; then
        exit 73
    fi
    case "$acceptance" in
        non-empty)
            ;;
        headings)
            if ! grep -qE '^##[[:space:]]+Evidence' "$stdout_capture" \
                || ! grep -qE '^##[[:space:]]+Inference' "$stdout_capture" \
                || ! grep -qE '^##[[:space:]]+Speculation' "$stdout_capture"; then
                printf 'gemini worker: broker acceptance headings failed\n' >&2
                exit 71
            fi
            ;;
        json)
            if ! python3 -c '
import json, sys
path = sys.argv[1]
with open(path, encoding="utf-8") as handle:
    data = json.load(handle)
if not isinstance(data, (dict, list)):
    raise SystemExit(1)
' "$stdout_capture" 2>/dev/null; then
                printf 'gemini worker: broker acceptance json failed (need object or array)\n' >&2
                exit 72
            fi
            ;;
    esac
    output_dir=$(dirname "$output_file")
    if [[ -n "$output_dir" && "$output_dir" != . ]]; then
        if ! mkdir -p "$output_dir"; then
            printf 'gemini worker: broker failed to create output directory %s\n' "$output_dir" >&2
            exit 75
        fi
    fi
    staging_artifact=$(mktemp)
    staging_provenance=$(mktemp)
    trap 'rm -f "$stdout_capture" "$staging_artifact" "$staging_provenance"' EXIT
    if ! cp "$stdout_capture" "$staging_artifact"; then
        printf 'gemini worker: broker failed to stage artifact copy\n' >&2
        exit 76
    fi
    agy_version=$("$antigravity_bin" --version 2>/dev/null || printf 'unknown')
    prompt_sha=$(sha256sum "$prompt_file" | awk '{print $1}')
    output_sha=$(sha256sum "$staging_artifact" | awk '{print $1}')
    utc_now=$(date -u +%Y-%m-%dT%H:%M:%SZ)
    if ! GEMINI_PROVENANCE_PATH="$staging_provenance" \
        GEMINI_PROVENANCE_UTC="$utc_now" \
        GEMINI_PROVENANCE_AGY_VERSION="$agy_version" \
        GEMINI_PROVENANCE_MODEL="$gemini_model" \
        GEMINI_PROVENANCE_EXIT_CODE="$worker_status" \
        GEMINI_PROVENANCE_PROMPT_FILE="$prompt_file" \
        GEMINI_PROVENANCE_PROMPT_SHA="$prompt_sha" \
        GEMINI_PROVENANCE_OUTPUT_FILE="$output_file" \
        GEMINI_PROVENANCE_OUTPUT_SHA="$output_sha" \
        GEMINI_PROVENANCE_ACCEPTANCE="$acceptance" \
        python3 <<'PY'
import json
import os
import sys

record = {
    "worker": "gemini",
    "mode": "broker",
    "captured_at_utc": os.environ["GEMINI_PROVENANCE_UTC"],
    "agy_version": os.environ["GEMINI_PROVENANCE_AGY_VERSION"],
    "model": os.environ["GEMINI_PROVENANCE_MODEL"],
    "exit_code": int(os.environ["GEMINI_PROVENANCE_EXIT_CODE"]),
    "prompt_file": os.environ["GEMINI_PROVENANCE_PROMPT_FILE"],
    "prompt_sha256": os.environ["GEMINI_PROVENANCE_PROMPT_SHA"],
    "output_file": os.environ["GEMINI_PROVENANCE_OUTPUT_FILE"],
    "output_sha256": os.environ["GEMINI_PROVENANCE_OUTPUT_SHA"],
    "acceptance": os.environ["GEMINI_PROVENANCE_ACCEPTANCE"],
}
path = os.environ["GEMINI_PROVENANCE_PATH"]
with open(path, "w", encoding="utf-8") as handle:
    json.dump(record, handle, indent=2)
    handle.write("\n")
PY
    then
        printf 'gemini worker: broker failed to write provenance record\n' >&2
        exit 77
    fi
    if ! cp "$staging_provenance" "$provenance_file"; then
        printf 'gemini worker: broker failed to persist provenance at %s\n' "$provenance_file" >&2
        exit 77
    fi
    if ! cp "$staging_artifact" "$output_file"; then
        printf 'gemini worker: broker failed to persist artifact at %s\n' "$output_file" >&2
        exit 76
    fi
    printf 'worker=gemini broker_output=%s provenance=%s\n' "$output_file" "$provenance_file" >&2
    cat "$stdout_capture"
    exit 0
fi

"${command_args[@]}"
worker_status=$?
printf 'worker=gemini exit_code=%d\n' "$worker_status" >&2
exit "$worker_status"
