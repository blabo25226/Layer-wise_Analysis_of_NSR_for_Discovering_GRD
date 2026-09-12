# GPU_RUNmultiAI

Multi-AI autonomous research campaign workspace.

This directory plays the same broad campaign role that earlier `GPU_RUN*` directories played:
plans, run records, reports and provenance are explicit and reviewable.
Unlike a one-shot GPU run, this directory also carries persistent multi-cycle autonomous state.

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
