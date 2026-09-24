# C0001 v16 round7 r2 pre-closure acceptance verification

Scope: implementation acceptance only. This is not a scientific result, implementation closure, or full-audit authorization. The frozen plan is `preregistration_draft_v16.md`, SHA256 `67017f5c8bac861664fc867b70cf229d43be3d052d266ffd0d575e20e6c12078`.

Run output: `runs/c0001_metric_identifiability_audit_v16_round7_acceptance_r2/`, created at source commit `6e20b25dc633dbc698fe79d63cfee7b87a255ea8`. Earlier round6/round7 outputs were preserved. `audit_manifest.json` reports `completed` at 2026-09-24 06:00:35 UTC, mode `implementation_acceptance`, 510 B1 rows, 4,080 confirmatory and grand calls, 2,145.36 elapsed seconds, and 8,713,621 bytes. The frozen limits are 18,000 seconds and 1,200,000,000 bytes. No `abort_manifest.json` exists; the only deviation declares the non-scientific acceptance mode.

## Independent mechanical checks

- PI shell `sha256sum preregistration_draft_v16.md` matched the frozen SHA; `git rev-parse HEAD` and remote branch SHA both matched `6e20b25` before the evidence-only documentation commit.
- PI `jq -s` over `call_log.jsonl`: 4,080 rows, all B1 and all completed; 4,080 unique `(primitive, condition, stage, unit_type, unit_id)` keys; 510 unique units. Primitive counts: six single-call primitives ×510 and `oracle_equivalence` ×1,020.
- PI `jq` over `b1_evidence.json`: 510 rows, 510 unique pairs/components, all `control_pass_row=true`, and 510 `control_pass` outcomes.
- PI `jq` over `q4_reference_controls.json`: 7/7 `fixture_pass=true`; over `reachability_evidence.json`: 10/10 `passed=true`. Four reachability fixtures are explicitly synthetic; the auxiliary production rescale fixture is labelled live.
- `contract_evidence.json` reports all seven G_contract checks and all seven named F1/F2/F4–F8 checks PASS. F3 is resolved in frozen v16 protocol and is intentionally not in G_impl. `timing_calibration.json` reports PASS with projected full-run 15,036.79 seconds; the projection is not a guarantee.
- Cursor read-only mechanical verifier independently inspected the frozen plan, source, and output packet. It found the artifacts internally consistent but could not run shell in Ask mode, so PI directly recomputed hashes and unique-key counts. Gemini broker successfully compressed a prompt-supplied packet; its output is an index, not primary evidence. Its F3 speculation was rejected against v16 §15–16.

## Independent Claude Opus 5.5 review

Reviewer identity: Claude Opus 5.5 reproducibility auditor. Implementer identity: Cursor Agent. `reviewer_diff_assertion=true`. Read-only verdict: **PASS for this pre-closure acceptance packet only**; no P0/P1 blocker in that scope. Claude read primary output, frozen plan, source modules and tests. Claude could not run a shell; PI recomputations above cover that limitation.

Claude retained a **P2 full-audit blocker**: `build_reachability_evidence()` is called after counted work in the full path and uncontained synthetic-fixture exceptions could abort after roughly 27k calls. Before any full run, move the reachability checks before counted primitives or contain fixture errors, then test/review. Additional P2: auxiliary live-probe child guard attempts are discarded, and the ledger-isolation unit test is tautological; improve audit honesty and regression protection. P3: G_impl checks pass count but not exact fixture-ID set; acceptance deviation under-describes uncounted auxiliary work; timing calibration has thin headroom; the plan body still says “unfrozen” despite the external immutable freeze record.

**PI gate:** accept r2 as an implementation-acceptance evidence packet. The 82-vs-91 source-inventory governance issue is reconciled below and must be explicitly accepted at closure. Do not create an implementation-closure record or launch the 27,637-call full audit until the P2 full-audit blocker, source-hash binding, and independent post-fix review are resolved. No scientific hypothesis is supported or rejected by this packet.

## Source-inventory and freeze reconciliation (Claude Opus 5.5 follow-up)

Independent Claude review interpreted v16 §13.2's deterministic recursive inventory algorithm as normative; its “82 paths” list is explicitly an observed pre-implementation snapshot. The freeze record's “82-path per-file hashes” shorthand does not override that algorithm. The completed r2 inventory contains all 82 snapshot paths, with unchanged 13 shared runtime/evaluation and 47 `third_party/odeformer` paths; `src/gpu_runmultiai/*.py` grew from 22 to 31. The nine additions are `contract_evidence.py`, `eligibility.py`, `f7_independent_reference.py`, `jsonl_durable.py`, `q4_reference.py`, `quantization.py`, `reachability.py`, `source_inventory.py`, and `timing_calibration.py`. The first seven were already reconciled in `implementation_completion_v16_round3.md`; the last two are post-freeze F7 independent-reference and timing-ceiling evidence helpers. This **82→91 reconciliation** must be included in the closure review and accepted source-hash record; it is not an amendment to the frozen plan.

The plan body still calls itself “unfrozen” because those immutable bytes were drafted before the separate `preregistration_v16_freeze_record.md` and independent PASS closure. The external freeze record and SHA are the authority. Do not edit the frozen plan to change the label. Claude did not independently recompute 91 blob hashes; the post-fix closure reviewer must verify the final accepted commit against every algorithmically enumerated path.
