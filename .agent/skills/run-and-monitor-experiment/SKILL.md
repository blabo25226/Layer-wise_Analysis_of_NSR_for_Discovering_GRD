---
name: run-and-monitor-experiment
description: Execute smoke and full experiments under the frozen plan while monitoring resources and preserving artifacts.
---
# Run and Monitor Experiment

Preflight:
- correct branch/commit
- environment/checkpoint identity
- output isolation
- disk/GPU health
- manifest path
- test leakage protections

Then:
1. focused tests
2. smoke run
3. verify outputs/resume behavior
4. full frozen run
5. persist command/log/manifest
6. record failures rather than hiding them

A recoverable crash routes to retry/fallback policy; it does not end the campaign.
