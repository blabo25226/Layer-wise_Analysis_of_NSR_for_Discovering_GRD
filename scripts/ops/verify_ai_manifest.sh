#!/usr/bin/env bash
# Verify MANIFEST.sha256 matches the canonical bootstrap/control/tooling files.
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

MANIFEST="MANIFEST.sha256"
if [[ ! -f "$MANIFEST" ]]; then
  echo "verify_ai_manifest: missing $MANIFEST" >&2
  exit 1
fi

bash scripts/ops/update_ai_manifest.sh
first_hash="$(sha256sum "$MANIFEST" | awk '{print $1}')"
bash scripts/ops/update_ai_manifest.sh
second_hash="$(sha256sum "$MANIFEST" | awk '{print $1}')"

if [[ "$first_hash" != "$second_hash" ]]; then
  echo "verify_ai_manifest: update is not deterministic" >&2
  exit 1
fi

sha256sum -c "$MANIFEST"
echo "verify_ai_manifest: OK"
