#!/usr/bin/env bash
# Regenerate MANIFEST.sha256 for Multi-AI bootstrap/control/tooling files.
# The manifest never includes itself to avoid self-reference.
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

OUTPUT="MANIFEST.sha256"
while [[ $# -gt 0 ]]; do
  case "$1" in
    -o|--output)
      if [[ $# -lt 2 ]]; then
        echo "update_ai_manifest: missing argument for $1" >&2
        exit 2
      fi
      OUTPUT="$2"
      shift 2
      ;;
    -h|--help)
      echo "Usage: update_ai_manifest.sh [-o|--output PATH]" >&2
      exit 0
      ;;
    --)
      shift
      break
      ;;
    -*)
      echo "update_ai_manifest: unknown option: $1" >&2
      exit 2
      ;;
    *)
      OUTPUT="$1"
      shift
      ;;
  esac
done

collect_manifest_paths() {
  local paths=()

  while IFS= read -r path; do
    paths+=("$path")
  done < <(
    {
      find .agent .agents .ai .claude .codex .cursor .gemini \
        -type f ! -path '*/.*' 2>/dev/null || true
      printf '%s\n' \
        AGENTS.md \
        CLAUDE.md \
        COMPATIBILITY.md \
        FULL_ACCESS_SETUP.md \
        GEMINI.md \
        README_JA.md \
        ROOT_SNIPPETS/AGENTS_APPEND.md \
        PACKAGE.json \
        GPU_RUNmultiAI/README.md \
        GPU_RUNmultiAI/RESEARCH_LOOP.md \
        GPU_RUNmultiAI/research_state.md \
        GPU_RUNmultiAI/task_board.md \
        GPU_RUNmultiAI/hypothesis_tree.md \
        GPU_RUNmultiAI/human_review_queue.md \
        GPU_RUNmultiAI/cycles/.gitkeep \
        GPU_RUNmultiAI/cycles/C0000/task_handoff_example.md \
        GPU_RUNmultiAI/literature/.gitkeep \
        GPU_RUNmultiAI/manifests/.gitkeep \
        GPU_RUNmultiAI/plans/.gitkeep \
        GPU_RUNmultiAI/reports/.gitkeep \
        GPU_RUNmultiAI/reviews/.gitkeep \
        GPU_RUNmultiAI/runs/.gitkeep \
        GPU_RUNmultiAI/syntheses/.gitkeep \
        scripts/ops/update_ai_manifest.sh \
        scripts/ops/verify_ai_manifest.sh
    } | LC_ALL=C sort -u
  )

  local path
  for path in "${paths[@]}"; do
    if [[ -f "$path" ]]; then
      printf '%s\n' "$path"
    fi
  done
}

TMP="$(mktemp)"
while IFS= read -r rel; do
  sha256sum "$rel"
done < <(collect_manifest_paths | LC_ALL=C sort) > "$TMP"

mv "$TMP" "$OUTPUT"
