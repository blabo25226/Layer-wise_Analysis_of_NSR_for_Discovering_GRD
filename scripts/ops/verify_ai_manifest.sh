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

TMPDIR="$(mktemp -d)"
cleanup() {
  rm -rf "$TMPDIR"
}
trap cleanup EXIT

EXPECTED_FIRST="$TMPDIR/expected-first.sha256"
EXPECTED_SECOND="$TMPDIR/expected-second.sha256"

bash scripts/ops/update_ai_manifest.sh -o "$EXPECTED_FIRST"
bash scripts/ops/update_ai_manifest.sh -o "$EXPECTED_SECOND"

first_hash="$(sha256sum "$EXPECTED_FIRST" | awk '{print $1}')"
second_hash="$(sha256sum "$EXPECTED_SECOND" | awk '{print $1}')"

if [[ "$first_hash" != "$second_hash" ]]; then
  echo "verify_ai_manifest: update is not deterministic" >&2
  exit 1
fi

if ! cmp -s "$MANIFEST" "$EXPECTED_FIRST"; then
  echo "verify_ai_manifest: tracked $MANIFEST differs from expected content; run update_ai_manifest.sh" >&2
  exit 1
fi

sha256sum -c "$MANIFEST"
echo "verify_ai_manifest: OK"
