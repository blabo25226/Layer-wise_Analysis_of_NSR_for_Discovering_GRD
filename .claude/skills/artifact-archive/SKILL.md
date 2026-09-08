---
name: artifact-archive
description: Finalizes and preserves a GPU_RUNclaude1 cycle with an artifact manifest, SHA256 checksums, reproduction commands, Git references, and safe handling of large outputs. Use at the end of every completed cycle.
---

# Artifact Archive

Create:
- `GPU_RUNclaude1/manifests/Cxxxx_artifact_manifest.json`
- `GPU_RUNclaude1/manifests/Cxxxx_checksums.sha256`

Manifest fields should include:
- cycle
- hypothesis
- branch
- commits
- environment
- checkpoint hashes
- config paths
- exact commands
- raw result paths
- analysis path
- review path
- report path
- replication path
- artifact sizes
- status
- deviations

Checksum small/medium persistent artifacts and key result files.

For very large artifacts:
- record path
- size
- producer
- hash when feasible
- do not force them into Git

Commit metadata/source changes if safe.
Never delete older cycle artifacts to make the current cycle look clean.
