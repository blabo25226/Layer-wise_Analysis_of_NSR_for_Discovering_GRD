# C0001-T011 v12 targeted revision handoff

## Objective

Create self-contained `preregistration_draft_v12.md` and close R11-1 through
R11-9 from `preregistration_v11_independent_review.md` without editing code or
historical plans.

## Isolation and scope

- worker: Cursor repo-operator / scientific document implementer
- worktree: `/tmp/lansr-multiai-C0001-implement-audit`
- branch: `ai/C0001/research-engineer/implement-metric-audit`
- write: v12 plan, v11 review response, v12 completion, durable state
- prohibited: v9/v10/v11 edits, code/tests, smoke/full experiment, freeze claim,
  GPU_RUN5 results

## Required changes

1. Split exact Rational invariance and decimal Float rounding fixtures.
2. Reachability decision fixtures use exactly 1,320 unique rows and all-gate-PASS
   inputs: supported = 1 SFN + 1,319 preserved; unsupported = 1,320 preserved.
3. Inline every binding rule omitted from v11, including complete operator maps,
   N1/B3/IDs/oracle/guard/schema/resume/environment/provenance contracts and the
   seven F requirements. No normative historical cross-reference.
4. Add `eligibility_layer` and non-circular row predicates for every condition;
   derive scope for strict/non-strict/linear B0 rows.
5. Freeze the two rescale early-return preconditions and optional object-identity
   return check; no equality or catch-all condition.
6. Split confirmatory call gate and grand-total gate. Freeze `time.monotonic()`
   elapsed wall seconds, output-directory byte checks before/after each primitive
   and artifact write, and abort manifest behavior.
7. State REACH preflight calls are outside an audit invocation's counted ledger;
   C_q4 calls remain confirmatory and counted.
8. Add pre-pair corpus/stratum gate requiring 46 active, 284 neutral strict-Hill
   components and zero exponent tokens; mismatch aborts without pair outcomes.
9. G_impl names exactly `F1,F2,F4,F5,F6,F7,F8` and all are fully inlined.
10. Do not chase self-referential commit fields. Record content source and remote
    verification in completion text without follow-up churn.

## Stable quantities

- denominator: 1,320
- confirmatory calls: 27,636
- D2: 2,640
- grand maximum: 30,276
- elapsed wall ceiling: 18,000 seconds
- disk ceiling: 1,288,490,188 bytes (decimal 1.2 GB) — state the byte convention
  explicitly and use it consistently
- GPU/decode: zero

If the existing implementation uses binary GiB, the plan must choose and name a
single convention; do not silently equate 1.2 GB with 1.2 GiB.

## Acceptance

- v9/v10/v11 hashes unchanged.
- exact plan audit ID `c0001_metric_identifiability_audit_v12`.
- internal table/schema/count checks and `git diff --check` PASS.
- commit once for content/state, push, and verify local/remote SHA. A second
  metadata-only commit is allowed only if it does not try to equal its own SHA.
- v12 remains unfrozen pending targeted independent review.
