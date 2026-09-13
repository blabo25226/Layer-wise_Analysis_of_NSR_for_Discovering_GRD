# C0001 implementation revision handoff

Task ID: `C0001-T006-R1`
Role: Repo Operator / Research Engineer
Preferred worker: Cursor
Branch: `ai/C0001/research-engineer/implement-metric-audit`
Worktree: `/tmp/lansr-multiai-C0001-implement-audit`
Input review: `implementation_review_round1.md`

## Objective

Revise commit `88720c1` so the implementation executes the complete frozen v9
audit contract.  The current implementation is blocked from integration; this
task repairs it without changing the frozen preregistration.

## Constraints

- Do not edit the frozen v9 preregistration or its freeze record.
- Do not read or import scientific results from PR #4, `GPU_RUNclaude1`, or
  historical sealed GPU_RUN5 result artifacts.
- Do not run the full confirmatory audit.
- Work only in this isolated worktree.
- Preserve the invalid untracked smoke run as failure evidence; do not present it
  as acceptance evidence and do not silently delete it.
- Use Python 3.10 for acceptance if an existing authorized environment is
  available.  If not, report the environment gap accurately and do not claim it
  was tested.
- Do not replace a frozen condition with a cheaper approximation.  If an exact
  implementation is impossible, record a deviation and stop that substep for PI
  decision.

## Required work

Implement every acceptance item in `implementation_review_round1.md`, including:

- exact E0 forward scaling, production E1 inverse scaling, and E2 from E1;
- consistent full-system/component indexing;
- exact-rational independent oracle with raw-token evidence;
- live B0/B1/B2/B3/B4/N1 paths and D2 support exactly as frozen;
- observed gates, terminal classification and complete artifacts;
- true resume/dedup/ceiling enforcement;
- robust parent/child sealed-access guard with `finally` restoration;
- fail-fast frozen CLI/environment checks;
- tests that exercise the real chain and observed operation counts.

## Verification and completion

1. Run `git diff --check`.
2. Run compile checks and the focused test suite; preserve the final process exit
   code, not only the number of completed test bodies.
3. Run the narrowest useful bounded smoke from a clean committed state only when
   its required runtime dependencies are present.
4. Update `implementation_completion.md`, `task_board.md` and
   `research_state.md` truthfully.  Mark this round ready for review, not accepted.
5. Commit the repair in meaningful commits, push the task branch, and report the
   local and remote SHA plus exact test results.

The PI will independently review the resulting diff and evidence before any
cherry-pick or confirmatory execution.
