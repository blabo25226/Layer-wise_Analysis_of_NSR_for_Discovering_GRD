# C0001-T023 worker handoff — v16 round-7 implementation repair

```yaml
task_id: C0001-T023
cycle: C0001
parent_task_id: C0001-T022-REVIEW
role: research-engineer / repo-operator
preferred_worker: Cursor Agent
objective: >
  Repair the five round-6 closure blockers, commit and push one immutable source
  candidate, then generate one fresh pre-closure 510-B1/4,080-call acceptance
  packet. Do not create closure and do not run the full audit.
authoritative_inputs:
  - AGENTS.md
  - .agent/README.md
  - .agent/rules/
  - GPU_RUNmultiAI/RESEARCH_LOOP.md
  - GPU_RUNmultiAI/research_state.md
  - GPU_RUNmultiAI/cycles/C0001/preregistration_draft_v16.md
  - GPU_RUNmultiAI/cycles/C0001/implementation_review_v16_round6.md
frozen_constraints:
  - preregistration SHA256 67017f5c8bac861664fc867b70cf229d43be3d052d266ffd0d575e20e6c12078
  - 510 B1 rows and exactly 4,080 dedicated counted calls
  - acceptance evidence is non-scientific and is never reused
  - 27,637 confirmatory, 2,640 D2, 30,277 grand calls
  - 18,000 monotonic seconds and 1,200,000,000 output bytes
  - canonical repository closure only; fail closed before counted calls
branch: ai/C0001/research-engineer/implement-metric-audit
worktree: /tmp/lansr-multiai-C0001-implement-audit
write_scope:
  - src/gpu_runmultiai/
  - scripts/phases/gpu_runmultiai_c0001_metric_audit.py
  - scripts/phases/guard_bootstrap.py
  - tests/test_gpu_runmultiai_c0001_metric_audit.py
  - GPU_RUNmultiAI/cycles/C0001/implementation_completion_v16_round7.md
  - GPU_RUNmultiAI/cycles/C0001/runs/c0001_metric_identifiability_audit_v16_round7_acceptance/
acceptance_tests:
  - frozen plan hash unchanged
  - full focused test module passes on Python 3.10; no cherry-picked four-test subset
  - genuine production identity-fallback reachability with unmodified E2
  - independent production/reference F7 mutation falsifiers pass
  - canonical closure negative fixtures fail closed before counted calls
  - exact per-primitive confirmatory and D2 timing multiplicities plus measured overhead
  - final artifact tree schema/lifecycle/resource validation passes
  - source inventory equals immutable candidate Git blobs
  - fresh 510 B1 rows and 4,080 unique calls
  - commit, push, and local/tracking/remote equality recorded
forbidden_changes:
  - frozen v16 and historical v9-v15 preregistrations
  - round-2 through round-6 artifacts
  - protected v9 smoke
  - implementation_closure_record.json
  - full 27,637-call audit
status: ready
retry_count: 0
fallback: Claude Sonnet research-engineer, then Codex PI conflict resolution
implementer_identity: Cursor Agent
independent_reviewer_identity: Claude Code plus Codex executable-audit subagent
reviewer_diff_assertion: true
evidence_packet: GPU_RUNmultiAI/cycles/C0001/implementation_review_v16_round6.md
```

## Required repair design

### 1. Genuine identity-fallback fixture

Delete all replacement of production E2 with E1. Construct or discover a
deterministic d>=2 multi-component E1 that is a real production simplifier
fixed point and is not Q4-equivalent. A permitted construction is to pass a
deterministic multi-component decimal expression through the production
simplifier once to obtain E1, pass that E1 through the same production path a
second time to obtain E2, and require byte-identical canonical raw prefixes.
Persist input, first output, second output, Q4 result, and oracle result. Any
production E2 != E1 makes this fixture FAIL.

### 2. Non-circular F7

Keep production B2 classification and production outcome precedence wholly in
production modules. Keep the frozen independent reference in its own module
with no imports from the production classifier, outcome, or pipeline. Add two
falsifiers: mutate production classifier output and mutate production outcome
precedence. Each mutation must disagree with the unchanged independent
reference. Static no-import tests alone are insufficient.

### 3. One canonical closure validator

Replace the weak full-run authorization call with the canonical validator.
Require exact audit ID and plan hash, an existing accepted source commit,
source hashes recomputed from its Git blobs, exact `PASS` for G_contract,
G_impl, and independent review, non-empty reviewer identity, and recomputed
acceptance/review artifact digests. Test missing, malformed, non-PASS, wrong
digest, nonexistent commit, wrong plan/audit, and source mismatch cases. All
must abort before any counted call. Remove or update the stale
output-directory closure test.

### 4. Exact timing model

Persist a table with one row per frozen primitive/condition multiplicity,
observed sample count, conservative unit cost, and weighted cost. Measure
P1/P2/P12 instead of assigning a blanket fallback. Calculate D2 as the exact
330-pair eight-call multiset, including two P7 calls. Measure append+fsync,
resource scans, startup, and finalization; derive rather than assert fixed
overhead. Add a positive declared margin only after the exact subtotal.

### 5. Final-state resource/schema validation

Use the shared resource monitor for registration, reachability, F acceptance,
timing, caches, and all artifact writes. Finalize deviation and lifecycle state,
write the provisional completed manifest, validate every required row/cache and
cross-file invariant on that final tree, then persist a clearly defined final
byte measurement without invalidating the validation contract.

## Execution sequence

1. Preserve every historical and failed output tree; never resume round 6.
2. Implement repairs and run the complete focused test module under `lansr310`.
3. Commit source/tests, push, and verify local/tracking/remote equality.
4. Hold source immutable and run one fresh round-7 acceptance directory.
5. If source changes are needed, preserve the failed directory and restart in a
   new suffixed directory from a newly committed and pushed source candidate.
6. Mechanically recompute every acceptance condition from persisted artifacts.
7. Commit and push artifact/report separately; verify remote equality.
8. Return the standard handoff schema. Independent PASS remains required before
   closure or full audit.
