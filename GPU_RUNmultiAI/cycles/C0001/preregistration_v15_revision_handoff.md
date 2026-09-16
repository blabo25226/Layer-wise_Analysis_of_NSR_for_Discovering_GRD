# C0001-T014 v15 narrow revision handoff

## Objective and scope

Create `preregistration_draft_v15.md`, `preregistration_v14_review_response.md`,
`preregistration_v15_drafting_completion.md`, and update state. Preserve v9-v14
bytes. Edit no code/tests/results and do not touch the untracked v9 smoke.

## Exact required changes

1. Replace every normative n-ary expected output with
   `add,x_0,add,x_1,x_2` and `mul,2,mul,x_0,x_1`. Search the entire v15 for and
   prohibit stale `add,add,x_0,x_1,x_2` and `mul,mul,2,x_0,x_1` as outputs.
   They remain valid **inputs** only in §6.1.
2. Define parser semantics without contradiction: `t in all_operators` means
   operator; otherwise numeric and nonnumeric tokens are leaves. For audit Q4
   emitted output, optionally validate nonnumeric leaves against
   `{x_0..x_9,n,e,pi,euler_gamma}` after parsing. Empty remainder is mandatory.
3. Specify a new dependency-free `guard_bootstrap.py` post-freeze requirement:
   stdlib-only; derive repo root from entrypoint; literal output root
   `repo_root/results/runs`; construct/install guard before importing
   `gpu_runmultiai` package, reading config/plan/corpus/output, or loading
   ODEFormer. Apply to parent and child. Add source-inventory inclusion and a
   G_contract import-order acceptance test.
4. Add `terminal_outcome` to C_q4 schema; include B0, B1, and D2 E1/E2 rows in
   oracle schema with condition/stage/reference; define deviation entry exactly
   as `- {utc} | {deviation_id} | {description} | {scientific_impact} |
   {resolution} | {approval_reference_or_none}` plus final status line.
5. Repair all stale section references and zero-based component wording.
6. Inline remaining rescale/serialization algorithms instead of normative
   “same as production” wording. Pin their inventory paths but do not bind
   pre-implementation content hashes.
7. Keep audit ID `c0001_metric_identifiability_audit_v15`, C_q4=7, counts
   27,637/2,640/30,277, G_impl exact seven IDs, and all v14 contracts otherwise.

## Git protocol

At most two commits after the current tip: content commit, then optional
completion-only commit. Push each used commit once. Do not chase the final tip
inside state/completion. Report local and remote tips separately.

## Acceptance

- v9-v14 hashes unchanged;
- exact consistency searches PASS;
- `git diff --check` PASS;
- local/tracking/remote parity after push;
- v15 remains unfrozen for targeted review.
