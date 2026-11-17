# Artifact provenance and reproducibility

Every substantive experiment must preserve enough information to reproduce and audit it.

Record when applicable:
- Git branch and commit
- task/cycle ID
- exact command
- config and arguments
- environment/package versions
- model/checkpoint identity and hash
- seeds
- dataset/split identity
- input artifact hashes
- per-problem outputs
- failures and exclusions
- timing/resource information
- output manifest and checksums

Prefer generated artifacts over manual transcription. Never overwrite an old run to make the current run look clean.
