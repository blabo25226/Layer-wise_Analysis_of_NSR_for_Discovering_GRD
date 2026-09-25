# C0001-T006 implementation handoff

```yaml
task_id: C0001-T006
cycle: C0001
parent_task_id: C0001-T005
role: research-engineer / repo-operator
preferred_worker: Cursor Agent
objective: Implement the frozen C0001 metric-identifiability audit and its bounded smoke/tests without changing the scientific contract.
authoritative_inputs:
  - GPU_RUNmultiAI/cycles/C0001/preregistration_draft_v9.md
  - GPU_RUNmultiAI/cycles/C0001/preregistration_v9_freeze_record.md
  - GPU_RUNmultiAI/cycles/C0001/preregistration_v9_closure_review.md
  - src/gpu_run5/grn.py
  - src/gpu_run5/evaluation.py
  - src/evaluation/gpu_run5_structure.py
  - src/gpu_run4/formulas.py
  - src/gpu_run4/ted.py
  - third_party/odeformer/odeformer/model/utils_wrapper.py
  - third_party/odeformer/odeformer/model/sklearn_wrapper.py
  - third_party/odeformer/odeformer/envs/simplifiers.py
  - configs/gpu_run5/base.yaml
frozen_constraints:
  - binding plan SHA256 is 60cfed79780c6b027192a3da14e69416d72090e0a89dddd22248b0f00f50cf00
  - audit_id is c0001_metric_identifiability_audit_v9
  - no historical GPU_RUN5 sealed artifact access
  - no scientific endpoint, denominator, seed, gate, timeout, ID, budget, or decision-rule changes
  - confirmatory ceiling 23550; full-run ceiling 25860; GPU/decode calls zero
  - implementation deviations return to PI before execution
write_scope:
  - src/gpu_runmultiai/**
  - scripts/phases/gpu_runmultiai_c0001_metric_audit.py
  - tests/test_gpu_runmultiai_c0001_metric_audit.py
  - GPU_RUNmultiAI/cycles/C0001/implementation_completion.md
  - GPU_RUNmultiAI/research_state.md
  - GPU_RUNmultiAI/task_board.md
  - MANIFEST.sha256
read_scope:
  - authoritative_inputs above
  - existing tests and shared runtime utilities required for reuse
branch: ai/C0001/research-engineer/implement-metric-audit
worktree: /tmp/lansr-multiai-C0001-implement-audit
expected_outputs:
  - reusable audit implementation
  - frozen CLI entry point
  - focused unit/integration tests
  - bounded smoke output under GPU_RUNmultiAI/cycles/C0001/runs/ only if small and Git-safe
  - implementation completion record
acceptance_tests:
  - binding plan SHA verified before work and at runtime
  - four frozen SHA fixtures pass
  - corpus/source index contract passes
  - exhaustive outcome/decision tests pass
  - counted-call totals and typed resume identity tests pass
  - deep sealed guard tests pass without touching a real sealed artifact
  - N1/B4/linear control gates are tested
  - fail-if-exists and resume mismatch tests pass
  - python -m compileall -q src scripts tests
  - focused pytest for the new test module
  - git diff --check
forbidden_changes:
  - frozen preregistration v9 and its review/freeze records
  - existing scientific results or GPU_RUN5 sealed/test artifacts
  - hidden fallback, endpoint relaxation, denominator reduction, or budget increase
compute_budget: CPU only; no full confirmatory run; <=60 minutes implementation tests and bounded smoke
status: planned
retry_count: 0
fallback: Claude Sonnet research-engineer for implementation; Codex PI for conflict resolution only
implementer_identity: Cursor Agent
independent_reviewer_identity: Claude reproducibility-auditor or methodological subagent fallback
reviewer_diff_assertion: true
reviewer_independence_exception: null
evidence_packet: GPU_RUNmultiAI/cycles/C0001/preregistration_v9_freeze_record.md
```

Completion record must include commit SHA, changed files, exact tests/results, smoke artifacts, deviations, unresolved risks, files inspected, and next action. Process exit code alone is not acceptance evidence.
