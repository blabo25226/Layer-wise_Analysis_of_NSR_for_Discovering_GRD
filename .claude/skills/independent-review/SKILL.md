---
name: independent-review
description: Performs adversarial scientific review of a completed GPU_RUNclaude1 experiment by directly inspecting preregistration, code/config, raw results, analysis, and claims. Use after analysis and before accepting any cycle conclusion.
---

# Independent Review

Try to falsify the proposed conclusion.

Inspect primary artifacts, not only summaries.

Check for:
- leakage
- hidden tuning
- post-hoc metric changes
- selective seed reporting
- biased failure exclusions
- unfair baselines
- wrong statistical unit
- incorrect equivalence claims
- reconstruction/formula-recovery confusion
- generation/selection confusion
- representation/causality confusion
- novelty overclaim
- biological/causal overclaim
- low-n fragility
- alternate explanations

Severity:
- CRITICAL
- MAJOR
- MINOR
- NOTE

Recommendation:
- ACCEPT_AS_NEGATIVE
- ACCEPT_AS_PRELIMINARY
- REPLICATE
- REVISE_ANALYSIS
- INVALIDATE
