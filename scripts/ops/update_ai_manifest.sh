#!/usr/bin/env bash
# Regenerate MANIFEST.sha256 for Multi-AI bootstrap/control/tooling files.
# The manifest never includes itself to avoid self-reference.
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

MANIFEST="MANIFEST.sha256"
TMP="$(mktemp)"

collect_manifest_paths() {
  local paths=()

  while IFS= read -r path; do
    paths+=("$path")
  done < <(
    {
      find .agent .agents .claude .codex .cursor .gemini \
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

while IFS= read -r rel; do
  sha256sum "$rel"
done < <(collect_manifest_paths | LC_ALL=C sort) > "$TMP"

mv "$TMP" "$MANIFEST"
