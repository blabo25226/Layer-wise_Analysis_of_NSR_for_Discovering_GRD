# Cycle Artifact Contract

Every completed cycle `Cxxxx` must preserve enough information to independently reconstruct what happened.

## Required research metadata
- hypothesis file
- literature note
- preregistration
- implementation commit/diff reference
- exact commands
- configs
- environment summary
- checkpoint hash
- raw run path
- per-problem result path
- analysis
- statistical review
- independent review
- replication record if applicable
- cycle report
- manifest
- checksums
- research_state update
- hypothesis_tree update

## Required per-equation information for SR experiments
When applicable:
- equation/problem ID
- ground-truth equation
- raw predicted equation
- simplified predicted equation
- variable mapping
- candidate rank
- candidate-set membership of truth/skeleton if measurable
- NMSE
- R²
- exact recovery
- skeleton recovery
- symbolic equivalence
- TED or other structural distance
- variable precision/recall/F1
- complexity
- valid flag
- failure reason
- integration/singularity diagnostics
- compute time

## Manifest path
`GPU_RUNclaude1/manifests/Cxxxx_artifact_manifest.json`

## Checksum path
`GPU_RUNclaude1/manifests/Cxxxx_checksums.sha256`

## Report path
`GPU_RUNclaude1/reports/Cxxxx_report.md`

## Large artifacts

Do not force large datasets/checkpoints into Git.

Instead record:
- absolute/relative storage path
- size
- hash when practical
- producer command
- source URL or derivation
- Git commit that generated them
