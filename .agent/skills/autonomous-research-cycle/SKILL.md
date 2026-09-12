---
name: autonomous-research-cycle
description: Run or resume one complete GPU_RUNmultiAI scientific cycle and continue to the next cycle unless a hard stop is active.
---
# Autonomous Research Cycle

1. Read `GPU_RUNmultiAI/RESEARCH_LOOP.md` and `research_state.md`.
2. Reconstruct repository/campaign state (Cursor reconnaissance when 5+ substantive files).
3. Update competing hypotheses.
4. Select one falsifiable, high-information question.
5. Gather literature/repository evidence (Gemini breadth; Cursor reconnaissance for repo structure).
6. Freeze a preregistered plan before final-test access.
7. Delegate implementation into isolated worktrees (Cursor-first for multi-file).
8. Run reproducibility/pre-run audit and smoke tests.
9. Execute the frozen experiment.
10. Analyze raw artifacts (Gemini bulk extraction support).
11. Obtain independent adversarial review (Claude Opus; never skipped for capacity).
12. Replicate when required.
13. Write report (Gemini first draft → Claude polish → PI final claims), manifest and checksums.
14. Update persistent state/hypothesis tree/review queue.
15. If `hard_stop == false`, begin the next cycle.

Never skip the report because the result is negative.
Never let the implementer be the only reviewer; record `implementer_identity`, `independent_reviewer_identity`, and
`reviewer_diff_assertion` in handoffs and state.
Never demote preregistration and metric freeze, final scientific review and reviewer independence, leakage protection,
primary-artifact verification, or replication gates for capacity.
