---
name: negative-result-recovery
description: Turn unsupported, invalidated, or ambiguous findings into discriminating next hypotheses rather than blind compute escalation.
---
# Negative Result Recovery

Classify likely bottleneck:
generation, selection, optimization, evaluator, identifiability, architecture, distribution shift, data/noise,
compute, layer-ranking criterion, implementation/reproducibility, or unknown.

Prefer the cheapest experiment that separates two plausible explanations.
Do not respond to every negative result by increasing compute.
