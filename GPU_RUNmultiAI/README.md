# GPU_RUNmultiAI

Multi-AI autonomous research campaign workspace.

This directory plays the same broad campaign role that earlier `GPU_RUN*` directories played:
plans, run records, reports and provenance are explicit and reviewable.
Unlike a one-shot GPU run, this directory also carries persistent multi-cycle autonomous state.

## Tracks

- **Infrastructure track**: research OS bootstrap, routing, manifest, push durability, PR remediation. Not a scientific
  result.
- **Scientific track**: hypotheses, preregistration, experiments, analysis, independent review. Keep separate from
  infrastructure conclusions.

`research_state.md` records both tracks under `tracks.infrastructure` and `tracks.scientific`.

## Durable top-level files

- `RESEARCH_LOOP.md`: stage contract
- `research_state.md`: machine-resumable current state
- `hypothesis_tree.md`: competing scientific hypotheses
- `human_review_queue.md`: asynchronous items for the human
- `task_board.md`: current delegated task overview

## Directories

- `cycles/Cxxxx/`: cycle-local hypothesis, plan, analysis, report and handoffs
- `plans/`: frozen plans that need stable cross-cycle references
- `literature/`: evidence notes
- `reviews/`: cross-cycle or final reviews
- `reports/`: promoted human-facing reports/summaries
- `manifests/`: provenance and checksums
- `runs/`: run metadata/log references; large raw artifacts may live elsewhere and be referenced
- `syntheses/`: multi-cycle syntheses

Reusable code does not belong here by default. Put reusable software in `src/`, `scripts/`, `configs/`, `tests/`.

## Integrity manifest and checkpoints

Root [`MANIFEST.sha256`](../MANIFEST.sha256) checksums canonical bootstrap, control, and tooling files across
`.agent/`, provider adapters, and the durable `GPU_RUNmultiAI/` control files listed by
`scripts/ops/update_ai_manifest.sh`. The manifest excludes itself to avoid self-reference.

```bash
bash scripts/ops/update_ai_manifest.sh
bash scripts/ops/verify_ai_manifest.sh
```

Use this manifest after infrastructure edits and before reporting that the research OS checkpoint is durable.
Cycle archives and promoted reports may additionally store manifests under `GPU_RUNmultiAI/manifests/` or
`GPU_RUNmultiAI/runs/`; those are campaign artifacts, not substitutes for the root tooling manifest.
