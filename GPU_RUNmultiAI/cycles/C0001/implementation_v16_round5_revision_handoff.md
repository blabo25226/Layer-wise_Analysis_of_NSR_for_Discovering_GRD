# C0001-T021 worker handoff — v16 round-6 fresh acceptance

```yaml
task_id: C0001-T021
cycle: C0001
parent_task_id: C0001-T020-REVIEW
role: research-engineer / repo-operator
preferred_worker: Cursor Agent
objective: >
  Repair all round-5 provenance, reachability, cache/resume, F7, timing,
  closure-validation, schema/resource, and guard blockers; commit and push one
  immutable candidate source; then produce a fresh round-6 pre-closure
  acceptance artifact and report. Do not create closure or run the full audit.
authoritative_inputs:
  - AGENTS.md
  - .agent/README.md
  - .agent/rules/
  - GPU_RUNmultiAI/RESEARCH_LOOP.md
  - GPU_RUNmultiAI/research_state.md
  - GPU_RUNmultiAI/cycles/C0001/preregistration_draft_v16.md
  - GPU_RUNmultiAI/cycles/C0001/implementation_review_v16_round5.md
  - GPU_RUNmultiAI/cycles/C0001/implementation_completion_v16_round5.md
frozen_constraints:
  - preregistration SHA256 67017f5c8bac861664fc867b70cf229d43be3d052d266ffd0d575e20e6c12078
  - 510 B1 rows and exactly 4,080 dedicated named calls
  - acceptance artifacts are non-scientific and never reused by full audit
  - all JSONL duplicate-key rules remain strict; no cache validation bypass
  - frozen 27,637 confirmatory, 2,640 descriptive, 30,277 grand call budgets
  - frozen 18,000 second and 1,200,000,000 byte ceilings
write_scope:
  - src/gpu_runmultiai/
  - scripts/phases/gpu_runmultiai_c0001_metric_audit.py
  - scripts/phases/guard_bootstrap.py
  - tests/test_gpu_runmultiai_c0001_metric_audit.py
  - GPU_RUNmultiAI/cycles/C0001/implementation_completion_v16_round6.md
  - GPU_RUNmultiAI/cycles/C0001/runs/c0001_metric_identifiability_audit_v16_round6_acceptance/
read_scope:
  - repository except frozen sealed GPU_RUN5 paths
branch: ai/C0001/research-engineer/implement-metric-audit
worktree: /tmp/lansr-multiai-C0001-implement-audit
expected_outputs:
  - single immutable candidate runtime/tests commit and remote parity
  - fresh round-6 510-row/4,080-call acceptance tree bound to that commit
  - 10/10 reachability PASS and independent F7 mutation evidence
  - valid explicit-resume/cache evidence
  - multiplicity-weighted full-grand timing feasibility artifact
  - artifact-derived round-6 report and pushed artifact commit
acceptance_tests:
  - plan hash unchanged
  - compileall and focused pytest pass
  - source inventory equals bound commit Git blobs with zero mismatch
  - manifest/reachability/G_impl recomputation agrees
  - all cache keys unique and production loaders accept every JSONL file
  - completed lifecycle has no abort residue
  - F7 production mutation is caught by independent reference
  - timing sums exact frozen per-primitive multiplicities plus D2/overhead/margin
  - conservative projected grand runtime is at most 18000 seconds
  - local HEAD equals tracking and ls-remote after source and artifact commits
forbidden_changes:
  - frozen v16 and historical v9-v15 preregistrations
  - round-2 through round-5 artifacts
  - protected v9 smoke
  - implementation_closure_record.json
  - full 27,637-call audit
compute_budget: >
  focused tests plus one fresh pre-closure 510-B1/4,080-call acceptance run;
  frozen wall/disk ceilings; no full audit
status: ready
retry_count: 0
fallback: Claude Sonnet research-engineer, then Codex PI conflict resolution
implementer_identity: Cursor Agent
independent_reviewer_identity: Claude Code plus Codex executable-audit subagent
reviewer_diff_assertion: true
reviewer_independence_exception: null
evidence_packet: GPU_RUNmultiAI/cycles/C0001/implementation_review_v16_round5.md
```

## Required repair design

### Immutable provenance

Create a new output directory only after the final runtime/tests candidate is
committed, pushed, and local/tracking/remote equality is verified. Record that
exact commit in the manifest and recompute every inventory hash from its Git
blob. No source edit is permitted during the acceptance run. If a runtime fix
is needed, abandon the partial output as negative evidence, make a new commit,
and use a new fresh output directory.

### Reachability and F7

Find or construct a deterministic d>=2 multi-component input that actually
passes through the production simplifier and yields `E2 raw == E1 raw` while
E1 is not Q4-equivalent. Persist raw inputs/outputs and require all ten fixtures
to pass before G_impl can pass.

Restore the production B2 classification path to the real production
`classify_formula(E1)` result. Put the independent frozen reference in a
separate module or test implementation that imports no production classifier or
outcome helper. Add a mutation that changes production behavior and prove the
reference gate fails.

### Strict resume/cache lifecycle

Only explicit `--resume` may resume. Before reuse, load and validate the prior
manifest, source/commit identity, CLI/environment/fingerprint, and every JSONL
file. Duplicate complete keys abort. Never replace a bad cache with `{}`.
Fresh success must have a completed deviation terminator and no abort manifest.

### Timing

Use the frozen primitive table as the multiplicity authority. Measure
representative P1–P12 costs where applicable, including nontrivial B0
simplifier/oracle paths, real CAS comparisons, D2, append+fsync, resource scans,
startup and finalization. Sum `count_i * conservative_cost_i`, add fixed
overhead and a declared positive margin, and persist every input to the
calculation. Do not multiply all calls by the slowest primitive.

### Closure/schema/resource/guard

Canonical repository closure only. Verify accepted commit existence and Git
blob hashes plus plan/audit identity, artifact digests, G/F verdicts,
independent reviewer identity/verdict, and review digest. Validate every row and
lifecycle cross-condition of the acceptance-specific required artifacts. Route
all log/cache/artifact writes through enforceable resource boundaries. Use
fresh subprocess falsifiers for parent and child import ordering.

## Git and execution sequence

1. Preserve protected untracked trees and record pre-run recursive hashes.
2. Implement and run focused tests.
3. Commit runtime/tests once; push; verify three-way SHA equality.
4. Run one fresh round-6 acceptance from that immutable commit.
5. If it fails because source must change, keep the failed tree, create a new
   source commit, and use a distinct output directory; never finalize by reuse.
6. Mechanically verify all acceptance conditions.
7. Commit report/artifacts separately; push; verify equality.
8. Return the completion schema. Full audit and closure remain prohibited.
