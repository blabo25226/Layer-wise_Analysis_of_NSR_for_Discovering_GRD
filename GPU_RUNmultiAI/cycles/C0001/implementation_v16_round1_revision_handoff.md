# C0001-T017 — v16 implementation repair after round-1 BLOCK

## Binding inputs

- plan SHA256: `67017f5c8bac861664fc867b70cf229d43be3d052d266ffd0d575e20e6c12078`
- review: `implementation_review_v16_round1.md`
- implementation base: the current branch tip containing the review/handoff
- protected path: untracked
  `GPU_RUNmultiAI/cycles/C0001/runs/c0001_metric_identifiability_audit_v9_smoke/`

## Task

Repair every P0 and required contract item in the round-1 review.  Treat the
frozen v16 preregistration as normative and the review as a defect list, not
as permission to weaken a gate, fixture, schema, count, or abort condition.

Required outcomes:

1. Real B1 identity E0/E1 chain and 510/510 `control_pass_row` gate logic.
2. Runtime and manifest enforcement for `G_eligibility`, `G_stratum`,
   `G_grand`, `G_contract`, and `G_impl` with the frozen disposition/order.
3. P12 quantization assignment, exponent-token global abort, populated row
   fields, and `quantization_stratum.json`.
4. Both production rescale early-return conditions detected and durable.
5. Parent guard installed before every package import/read; no replacement
   guard; durable parent+child ledger; import-order/no-replacement/merge/G4
   acceptance tests.
6. All ten frozen reachability fixtures, including `REACH-SFN-1`, through the
   real classification/gate/decision paths.
7. 18,000 monotonic seconds and 1,200,000,000 decimal bytes, checked at the
   frozen boundaries and represented in the manifest.
8. Complete abort/deviation/manifest/artifact/resume schemas and durability
   semantics listed in the review and frozen plan.
9. Exact frozen dialect/oracle/fallback/cache semantics.
10. Fresh bounded artifacts that exercise B0, B1, B2, C_q4, N1, B3, B4, and
    D2 without running the full audit.

## Verification and Git

- Use Python 3.10.
- Run compileall, focused tests, exact plan-hash check, source-inventory
  reconciliation, and `git diff --check`.
- Record initial failures and final results in
  `implementation_completion_v16_round2.md`.
- Do not create `implementation_closure_record.json`.
- Do not run the full audit.
- Commit in meaningful units, push the task branch, and verify
  local/tracking/remote SHA equality.
