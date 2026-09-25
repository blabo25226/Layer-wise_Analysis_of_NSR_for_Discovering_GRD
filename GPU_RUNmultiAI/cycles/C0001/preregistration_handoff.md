# C0001-T004 preregistration drafting handoff

```yaml
task_id: C0001-T004
cycle: C0001
parent_task_id: null
role: research-engineer
preferred_worker: Claude Sonnet-compatible
objective: Persist the authorized scientific reconstruction, competing-hypothesis review, literature evidence, and a preregistration draft for the rescaling/structural-metric identifiability audit.
authoritative_inputs: [.agent/README.md, .agent/rules/01-research-integrity.md, .agent/rules/04-preregistration-and-metric-freeze.md, .agent/skills/hypothesis-tree/SKILL.md, .agent/skills/experiment-preregistration/SKILL.md, GPU_RUNmultiAI/research_state.md, GPU_RUN5/README.md, GPU_RUN5/GPU_RUN5_summary_report.md, configs/gpu_run5/base.yaml, third_party/odeformer/odeformer/model/utils_wrapper.py, third_party/odeformer/odeformer/envs/simplifiers.py, src/gpu_run5/evaluation.py, src/evaluation/gpu_run5_structure.py, src/gpu_run4/ted.py]
frozen_constraints: [No PR #4 or GPU_RUNclaude1 scientific content, no GPU_RUN5 sealed-test raw access, draft only, no experiment, keep exploratory check separate.]
write_scope: [GPU_RUNmultiAI/cycles/C0001/scientific_state.md, GPU_RUNmultiAI/cycles/C0001/hypothesis_review.md, GPU_RUNmultiAI/cycles/C0001/literature_evidence.md, GPU_RUNmultiAI/cycles/C0001/preregistration_draft.md]
branch: ai/C0001/research-engineer/preregister-metric-audit
worktree: /tmp/lansr-multiai-C0001-preregister
expected_outputs: [four scoped Markdown artifacts]
acceptance_tests: [Preserve at least five competing hypotheses, justify H0001 by information gain/cost, draft all metric-freeze fields, use only verified primary literature or label unverified, git diff --check, commit scoped files only.]
forbidden_changes: [No reusable code/tests/config edits, no final-test access, no claim promotion.]
compute_budget: writing only
status: planned
retry_count: 0
fallback: Codex PI synthesis
```
