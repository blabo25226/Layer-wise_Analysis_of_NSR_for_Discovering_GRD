---
name: run-and-monitor-experiment
description: Safely executes a preregistered LANSR smoke or full experiment while checking GPU, storage, manifests, logging, failures, resume behavior, and test isolation. Use whenever running GPU_RUNclaude1 experiments.
---

# Run and Monitor Experiment

Before:
- verify branch
- inspect `git status --short`
- inspect GPU and temperature
- inspect disk space
- confirm environment
- confirm checkpoint/config hashes
- confirm output directory is unique
- run smoke test

During:
- follow preregistered config exactly
- log stdout/stderr
- preserve partial progress
- record failures
- record timeouts
- record OOM
- save per-problem equations
- do not tune on test

After:
- verify expected artifact counts
- check manifest completeness
- compare hashes
- record actual wall time and resource use

If scientific configuration must change, end the run and record a deviation rather than silently mutating it.
