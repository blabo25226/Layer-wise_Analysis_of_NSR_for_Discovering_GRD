# GPU_RUNclaude1 Persistent Research State

## Campaign
- branch: `20260909_researce_GPU_RUNclaude1`
- status: initialized
- current_cycle: `C0001`
- last_completed_cycle: none
- last_synthesis: none

## Human intent

Run an AI-led research line independently of the human-led LANSR line.

Claude should autonomously repeat:

hypothesis
→ literature
→ preregistration
→ implementation
→ experiment
→ analysis
→ independent review
→ replication when needed
→ cycle report
→ reflection
→ next hypothesis

Humans mainly inspect reports periodically.

## Prior constraints

### GPU_RUN4
- ODEFormer released checkpoint architecture differs from paper description.
- Strong reconstruction does not prove symbolic recovery.
- Probe/ablation/IOLE rankings need not agree.

### GPU_RUN5
- Direct trajectory-to-ODE inference avoids finite-difference target estimation.
- Generation and selection failure should be separated.
- Multi-initial-condition candidate selection is promising.
- Full GRN FT and selective FT exhibit a recovery/forgetting tradeoff.
- CE-based layer ranking and formula-level causal ranking may differ substantially.
- Negative Go/No-Go outcomes must be respected.

## Open high-level research problems
1. Formula recovery bottleneck localization.
2. Hill / variable-denominator candidate coverage.
3. Candidate selection identifiability.
4. Structural OOD generalization.
5. Layer-importance criterion disagreement.
6. Adaptation–forgetting tradeoff.
7. Fair baseline evaluation.
8. Real-data readiness gates.
9. Connection to derivative-free biological dynamics methods.

## Current sealed resources

Fill during C0001 startup:
- final test sets:
- held-out equation families:
- ODEBench subsets:
- other sealed artifacts:

## Compute state

Fill at session startup:
- GPU:
- VRAM:
- free disk:
- current temperature:
- current jobs:

## Human review queue
See `human_review_queue.md`.

## Next action
Run Stage 0–3 of C0001.
