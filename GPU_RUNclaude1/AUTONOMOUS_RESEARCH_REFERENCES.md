# Autonomous Research System Design Notes

## The AI Scientist — adopted ideas

Use:
- explicit idea/hypothesis stage
- automated experiment implementation and execution
- report generation
- post-hoc scientific review
- baseline comparison
- failure preservation

Do not copy blindly:
- automated reviewer scores are not ground truth
- code execution requires strong repository and artifact isolation
- benchmark optimization must not become a substitute for scientific discovery

## Agent Laboratory — adopted ideas

Use:
- specialist-agent decomposition
- literature → experimentation → report pipeline
- persistent notes/state
- resumability
- explicit compute resources
- low human involvement by default

## LANSR extensions

GPU_RUNclaude1 adds:
- preregistration before final-test access
- dedicated statistical reviewer
- dedicated reproducibility auditor
- adversarial independent reviewer
- replication gate
- persistent hypothesis tree
- negative-result recovery
- cycle manifest/checksums
- 3-cycle synthesis
- LANSR-specific symbolic recovery contract
