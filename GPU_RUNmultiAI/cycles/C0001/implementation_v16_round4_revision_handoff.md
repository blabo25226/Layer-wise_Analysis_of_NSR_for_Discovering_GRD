# C0001-T020 worker handoff — v16 round-5 implementation acceptance

```yaml
task_id: C0001-T020
cycle: C0001
parent_task_id: C0001-T019-REVIEW
role: research-engineer / repo-operator
preferred_worker: Cursor Agent
objective: >
  Repair every round-4 blocker, add a non-circular pre-closure 510-row B1
  implementation-acceptance path, and produce a fresh round-5 evidence packet
  eligible for independent review. Do not create closure or run the full audit.
authoritative_inputs:
  - AGENTS.md
  - .agent/README.md
  - .agent/rules/
  - GPU_RUNmultiAI/RESEARCH_LOOP.md
  - GPU_RUNmultiAI/research_state.md
  - GPU_RUNmultiAI/cycles/C0001/preregistration_draft_v16.md
  - GPU_RUNmultiAI/cycles/C0001/implementation_review_v16_round4.md
  - GPU_RUNmultiAI/cycles/C0001/implementation_completion_v16_round4.md
frozen_constraints:
  - preregistration SHA256 67017f5c8bac861664fc867b70cf229d43be3d052d266ffd0d575e20e6c12078
  - acceptance B1 generation records 8 x 510 = 4,080 named primitive calls in a dedicated ledger
  - G_impl/F6 conjunct evaluation adds zero calls after the 510 rows exist
  - acceptance rows are non-scientific and may not be reused by the full audit
  - full audit remains 27,637 confirmatory plus 2,640 descriptive calls
  - frozen 18,000 second and 1,200,000,000 byte ceilings remain unchanged
  - no final-test data access and no GPU_RUN5 sealed-path access
write_scope:
  - src/gpu_runmultiai/
  - scripts/phases/gpu_runmultiai_c0001_metric_audit.py
  - scripts/phases/guard_bootstrap.py
  - tests/test_gpu_runmultiai_c0001_metric_audit.py
  - GPU_RUNmultiAI/cycles/C0001/implementation_completion_v16_round5.md
  - GPU_RUNmultiAI/cycles/C0001/runs/c0001_metric_identifiability_audit_v16_round5_acceptance/
read_scope:
  - repository except sealed GPU_RUN5 paths defined by v16
branch: ai/C0001/research-engineer/implement-metric-audit
worktree: /tmp/lansr-multiai-C0001-implement-audit
expected_outputs:
  - committed and pushed runtime/tests candidate source commit
  - fresh 510-row B1 pre-closure acceptance artifact with 4,080-call ledger
  - complete F1/F2/F4/F5/F6/F7/F8 and G_contract/G_impl evidence
  - representative timing calibration and projection under frozen ceiling
  - artifact-derived round-5 completion report
acceptance_tests:
  - frozen plan hash unchanged
  - compileall and focused pytest pass
  - F6 510 legal rows pass; 509/duplicate/unknown/illegal terminal fail
  - acceptance ledger contains exactly 4,080 unique B1 primitive calls
  - closure metadata commit can differ from accepted_source_commit without weakening source hash binding
  - real resume clean-tree gate permits exactly its output directory and rejects other dirt
  - resume spy proves zero B0/B1/B2/D2 primitive re-execution
  - duplicate pair_id in pair_cache aborts
  - real multi-component simplifier fixed point reaches identity fallback
  - abort artifacts survive a pre-existing resource ceiling breach
  - F7 mutation falsifier fails the gate
  - every row of JSON/CSV/JSONL/cache artifacts is schema validated
  - executable parent and child guard import-order falsifiers pass
  - d3 component_idx greater than zero, secondary Hill, and linear control are covered
  - local HEAD equals tracking and ls-remote after each stable commit set
forbidden_changes:
  - GPU_RUNmultiAI/cycles/C0001/preregistration_draft_v16.md
  - historical v9-v15 preregistrations
  - round-2, round-3, and round-4 artifacts
  - GPU_RUNmultiAI/cycles/C0001/runs/c0001_metric_identifiability_audit_v9_smoke/
  - implementation_closure_record.json
  - full 27,637-call audit
compute_budget: >
  Pre-closure B1 acceptance only: 4,080 named primitive calls, frozen resource
  ceilings, followed by focused tests and timing calibration. Stop before full.
status: ready
retry_count: 0
fallback: Claude Sonnet research-engineer, then Codex PI conflict resolution
implementer_identity: Cursor Agent
independent_reviewer_identity: Claude Code plus Codex executable-audit subagent
reviewer_diff_assertion: true
reviewer_independence_exception: null
evidence_packet: GPU_RUNmultiAI/cycles/C0001/implementation_review_v16_round4.md
```

## Required implementation decisions

### 1. Add a distinct implementation-acceptance execution mode

Do not overload `--smoke` or bypass the closure gate for ordinary non-smoke
execution. Add an explicit pre-closure acceptance mode that executes all 510
real B1 components through the production pipeline. It owns a separate output
tree and call ledger. Persist the 510 rows and reconstruct all seven F checks
from durable evidence.

The generation calls are counted in this acceptance ledger. The plan's
“G_impl adds zero calls” language applies to evaluating existing rows, not to
creating them.

### 2. Remove closure self-reference without weakening binding

Define and validate a closure schema containing at least:

- plan hash and audit id
- `accepted_source_commit`
- exact sorted source inventory and hashes
- acceptance artifact paths and SHA256 digests
- G_contract/G_impl/F verdicts
- independent reviewer identity, verdict, and review artifact digest
- closure metadata commit or creation provenance

Full/resume may run from a later metadata-only commit only when current source
inventory exactly equals the accepted inventory. Do not accept an output-dir
closure record over a canonical repository record.

### 3. Repair resume and pair-cache semantics

On resume, exclude exactly the selected output directory from clean-tree
violations; do not broaden ignores. Preserve the frozen duplicate-`pair_id`
abort rule. Make B2 durable/reconstructable without writing a second pair-cache
row under the same immutable pair id. Use spies and crash-point tests.

### 4. Make acceptance evidence genuinely executable

- drive identity fallback through a real simplifier fixed point on a d>=2
  multi-component prefix and persist the live inputs/outputs
- implement F7's expected result from an independent literal frozen decision
  table, not production classifier helpers; add mutation testing
- execute parent/child guard import-order probes in fresh subprocesses and fail
  if either `gpu_runmultiai` or `experiment_runtime` was imported first
- persist per-scale F1/F4 analytic and numeric outcomes, including d3 and
  component index greater than zero
- cover secondary-Hill and linear-control rows

### 5. Complete resource and schema enforcement

Route initial/running/final manifests, deviation lifecycle, stage/pair/call
caches, guard side-channel, and normal artifacts through one pre/post boundary.
Use a non-raising resource snapshot for abort evidence, including when already
over ceiling. Write the final manifest so its recorded size accounts for its own
durable form, or record an explicitly defined post-finalization measurement.
Validate every row and exact terminal vocabulary for all frozen artifacts.

### 6. Calibrate before asking for full authorization

Use at least 20 representative components and include simplifier, oracle, and
CAS costs. Record observed call-type timing and a conservative full-run
projection. If the frozen 18,000-second ceiling cannot be met, report BLOCK;
do not silently change timeouts, parallelism semantics, or the ceiling.

## Required Git sequence

1. Preserve both untracked protected paths exactly as found.
2. Implement and test.
3. Commit runtime/tests as a candidate source commit.
4. Push it and record local/tracking/remote equality.
5. Run the fresh acceptance output from that clean source commit.
6. Commit the acceptance artifacts and completion report separately.
7. Push again and record equality.
8. Return the completion record required by `.agent/schemas/task-handoff-schema.md`.

If the worker cannot push because of its execution policy, return the exact
error and stable commits; the PI will push immediately. A failed push is not a
reason to omit commit or provenance fields.
