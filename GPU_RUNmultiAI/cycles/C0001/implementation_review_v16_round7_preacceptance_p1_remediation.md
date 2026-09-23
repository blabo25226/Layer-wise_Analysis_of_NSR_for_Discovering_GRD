# C0001-T023 round-7 pre-acceptance P1 remediation

Implementer: Cursor Agent. Review basis: `implementation_review_v16_round7_preacceptance.md` (BLOCK @ `92fe0c7`).

## P1-1 (REACH-IDENT-FALLBACK-1 synthetic oracle honesty)

- `_reach_ident_fallback_1_synthetic` now computes `e1_oracle` / `e2_oracle` via production-independent `oracle_equivalence_prefix` and `oracle_single_component` (Q4 component prefix vs E2 component prefix).
- Asserts `e2_oracle_equivalent=False` for the five-decimal E1 leaf vs Q4 four-decimal emission, and a counterfactual row with `e2_identity_fallback_candidate=False` classifies as `semantic_drift` (fallback precedence over drift).
- Production `detect_e2_identity_fallback_candidate` and `build_outcome_row` precedence unchanged; E2 remains explicit synthetic injection.

## P1-2 (live observation isolation)

- `build_reachability_evidence(..., include_live_ident_fallback_observation=False)` by default; full confirmatory audit path unchanged (synthetic-only REACH-IDENT-FALLBACK-1).
- Implementation acceptance enables live observation via `include_live_ident_fallback_observation=True`.
- Live `run_b0_pair` uses a dedicated `CallLogger()` without `ResourceMonitor`; failures are isolated and cannot flip synthetic `passed`.

## P2 (feasible review tests / labels)

- Mutation tests: E2 raw inequality, E1≡Q4 disables fallback, no-fallback → `semantic_drift`.
- Ledger isolation test; default build excludes live probe; live detail labels `bounded_no_match_within_first_8_trials`, `simplifier_subprocess_rerun_not_production_e2`, production vs recomputed fallback flags.

**Not run:** 4080-call implementation acceptance (awaiting independent Claude Opus 5.5 re-review).
