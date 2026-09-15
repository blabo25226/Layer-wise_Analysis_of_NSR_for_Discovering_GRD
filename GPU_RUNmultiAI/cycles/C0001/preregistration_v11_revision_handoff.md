# C0001-T010 v11 preregistration revision handoff

## Objective

Create a complete, self-contained v11 preregistration that supersedes the
unfrozen v10 draft and closes B1–B9 in
`preregistration_v10_independent_review.md`.

## Worker and scope

- preferred worker: Cursor repo-operator / scientific document implementer
- worktree: `/tmp/lansr-multiai-C0001-implement-audit`
- branch: `ai/C0001/research-engineer/implement-metric-audit`
- write scope: v11 preregistration, v10 review response, drafting completion,
  durable state, human review queue
- prohibited: code/tests, v9/v10 edits, freeze declaration, full experiment,
  sealed or historical GPU_RUN5 result access

## Required outputs

1. `preregistration_draft_v11.md`, audit ID
   `c0001_metric_identifiability_audit_v11`, with all binding rules inlined.
2. `preregistration_v10_review_response.md`, mapping B1–B9 to exact v11 sections.
3. `preregistration_v11_drafting_completion.md`, checks and open questions.
4. `research_state.md` updated to v11 ready for independent closure review.

## Binding resolutions

- Keep denominator 1,320, calls 27,636, D2 2,640, grand maximum 30,276 unless
  the revised primitive table proves a different count.
- Keep 5 CPU-hours, 1.2 GB, GPU/decode zero; record normal human-review item,
  non-blocking.
- Add `e2_identity_fallback_candidate` and precedence before semantic drift.
- Freeze Q4 SymPy Float/Rational serialization and parity fixtures.
- Pin and recheck real supported/preserved fixtures; add pure decision fixtures.
- Add `G_impl` and `G_b1` without duplicating counted calls.
- Freeze non-primary `partition_scope` and control outcomes; prohibit `unknown`.
- Add allowed `unit_type=fixture` for C_q4.
- Inline all v9/v10 binding content. Do not use “same as v9” as a normative rule.
- Freeze raw decimal token grammar/counting for quantization strata.

## Validation

- v9 and v10 hashes unchanged.
- no old audit IDs or ceilings in normative v11 fields.
- all mixed AND/OR expressions parenthesized.
- supported/unsupported, drift, Q4 failure, classifier parse failure, fallback,
  and compound-power fixtures are constructively reachable.
- arithmetic and schema tables reconcile mechanically.
- `git diff --check` passes.
- commit, push, and verify local/remote SHA.
