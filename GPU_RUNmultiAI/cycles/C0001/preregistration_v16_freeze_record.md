# C0001 preregistration v16 freeze record

- binding plan: `GPU_RUNmultiAI/cycles/C0001/preregistration_draft_v16.md`
- version: `v16`
- audit_id: `c0001_metric_identifiability_audit_v16`
- SHA256: `67017f5c8bac861664fc867b70cf229d43be3d052d266ffd0d575e20e6c12078`
- content commit: `682fbed997388edf5be42e6dcfe9ea01a3056f2a`
- reviewed tip: `249c82ee0ae93d39a23f90c17d8eeec46468ad58`
- closure review: `GPU_RUNmultiAI/cycles/C0001/preregistration_v16_independent_review.md`
- closure verdict: **PASS**
- frozen_at_utc: `2026-09-16T01:06:24Z`
- freeze record commit: the Git commit containing this file; resolve with
  `git log -1 --format=%H -- GPU_RUNmultiAI/cycles/C0001/preregistration_v16_freeze_record.md`

## Frozen quantities

- C_q4: 7
- confirmatory calls: 27,637
- D2 calls: 2,640
- grand maximum: 30,277
- elapsed ceiling: 18,000 monotonic seconds
- disk ceiling: 1,200,000,000 decimal bytes
- GPU/decode calls: zero

## Mutation rule

These plan bytes are immutable. Any protocol change requires a new version,
deviation record, independent review, and a new freeze decision. Post-freeze
implementation may change runtime code only to satisfy the frozen F and
G_contract requirements; accepted source hashes are bound at implementation
closure, before smoke/full audit.

## Run gate

Full audit is prohibited until all of the following are persisted and reviewed:

1. F1, F2, F4, F5, F6, F7, F8 acceptance evidence;
2. G_contract acceptance evidence, including the bootstrap guard;
3. `reachability_evidence.json`;
4. accepted implementation commit and 82-path per-file hashes;
5. bounded smoke and independent reproducibility review.
