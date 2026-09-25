---
name: independent-review
description: Adversarially review a completed analysis using primary artifacts and try to falsify its conclusions.
---
# Independent Review

Do not merely rewrite the analyst summary.
Inspect plan, diff/config, raw results, analysis, exclusions, statistics and claim text.

Focus on:
- leakage
- hidden tuning
- metric drift
- unfair baseline
- missing failures
- fragile effects
- overclaim
- alternative explanations
- novelty mistakes

Use `.agent/schemas/review-schema.md`.
