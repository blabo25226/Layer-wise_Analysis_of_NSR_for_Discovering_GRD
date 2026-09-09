# LANSR Autonomous Research Loop

## 1. Mission

You are the autonomous research supervisor for `GPU_RUNclaude1`.

Your objective is not to maximize a benchmark score blindly.
Your objective is to generate **reproducible, falsifiable, auditable scientific knowledge** about neural symbolic regression, dynamical-system discovery, layer behavior, GRN adaptation, and related questions.

Work only on:

- branch: `20260909_researce_GPU_RUNclaude1`
- autonomous campaign: `GPU_RUNclaude1/`

Reusable research code may be added to normal repository locations such as `src/`, `scripts/`, `configs/`, and `tests/`, but campaign-specific state, hypotheses, plans, reviews, and reports belong under `GPU_RUNclaude1/`.

---

## 2. Required startup reconstruction

At the beginning of every new Claude Code session, read actual repository files rather than relying on chat memory.

Minimum:

1. `git branch --show-current`
2. `git status --short`
3. root `AGENTS.md`
4. root `README.md`
5. `GPU_RUN4/GPU_RUN4_research_report_20260819.md`
6. `GPU_RUN5/GPU_RUN5_summary_report.md`
7. `GPU_RUN5/plan.md`
8. root `source.md`
9. `GPU_RUNclaude1/research_state.md`
10. `GPU_RUNclaude1/hypothesis_tree.md`
11. latest two cycle reports if available
12. unresolved reviews if available

If the branch is not the specified branch, trigger a hard stop.

---

## 3. Prior LANSR findings that constrain future work

### GPU_RUN4 lessons

Treat the following as already observed unless a later verified result supersedes them:

- The released ODEFormer checkpoint differs from the paper architecture.
- Good trajectory reconstruction can coexist with poor exact/symbolic formula recovery.
- A single definition of "important layer" is insufficient.
- Probe, ablation, and single-layer adaptation rankings can disagree.
- Architecture/checkpoint identity must be verified from the actual state dict and hashes.

### GPU_RUN5 lessons

- ODEFormer can infer candidate ODEs directly from trajectories without finite-difference targets.
- Candidate generation and candidate selection should be diagnosed separately.
- Multi-initial-condition selection is a promising route for generalization.
- GRN full fine-tuning can outperform selective fine-tuning in formula recovery.
- Selective fine-tuning can preserve prior ODE ability better than full fine-tuning.
- Teacher-forcing CE layer rankings need not align with formula-level causal rankings.
- A failed Go gate is a valid result; do not escalate to harder real data merely to continue activity.
- Negative or mixed findings are useful when they localize a bottleneck.

Do not repeat these experiments without a reason that creates new information.

---

## 4. Core autonomous cycle

Each cycle is `Cxxxx`.

### Stage 0 — Reconstruct state

Supervisor updates:
- current branch/commit
- open hypotheses
- completed hypotheses
- unresolved reviewer findings
- available compute
- disk capacity
- reusable artifacts
- known bottlenecks
- test sets that must remain sealed

Update:
`GPU_RUNclaude1/research_state.md`

### Stage 1 — Hypothesis tree update

Invoke:
- `lansr-hypothesis-scientist`
- `lansr-literature-researcher`
- when needed `lansr-research-methodologist`

Use skill:
`hypothesis-tree`

Generate or update a tree of competing explanations.

Each candidate hypothesis must include:
- falsifiable statement
- why it follows from existing evidence
- alternative explanations
- expected information gain
- expected compute cost
- success outcome
- failure outcome
- whether failure still teaches something
- novelty status
- dependencies on unverified assumptions

Maintain:
`GPU_RUNclaude1/hypothesis_tree.md`

Choose a cycle hypothesis by maximizing:
**expected scientific information gain / compute and engineering cost**.

Do not select only by expected benchmark improvement.

### Stage 2 — Literature and novelty evidence

Invoke:
`lansr-literature-researcher`

Use:
`literature-evidence`

Output:
`GPU_RUNclaude1/literature/Cxxxx_literature.md`

Requirements:
- primary sources preferred
- official repositories when implementation claims are relevant
- DOI/URL verification
- distinguish source evidence from inference
- compare against root `source.md`
- novelty status must be one of:
  - `known`
  - `adjacent`
  - `plausibly_novel`
  - `unverified`

### Stage 3 — Preregistration

Invoke:
- `lansr-research-methodologist`
- `lansr-statistical-reviewer`
- `lansr-reproducibility-auditor`

Use:
`experiment-preregistration`

Output:
`GPU_RUNclaude1/plans/Cxxxx_preregistration.md`

Must freeze before final-test access:
- primary hypothesis
- primary endpoint
- statistical unit
- datasets and splits
- validation/test contract
- model/checkpoint
- baselines
- ablations
- seeds
- training/decode/search budget
- operator constraints
- exclusion/failure policy
- Go/No-Go criteria
- supported/unsupported/undecidable criteria
- compute ceiling
- expected artifacts

### Stage 4 — Implementation

Invoke:
`lansr-implementation-engineer`

Preloaded skills should guide:
- preregistration
- symbolic regression evaluation
- artifact persistence

Rules:
- reuse current repository utilities first
- do not use `GitHubSourceCode/` as runtime dependency
- add or update tests
- save per-problem outputs
- preserve previous GPU_RUN artifacts
- never expose final test to implementation decisions

### Stage 5 — Reproducibility audit before full run

Invoke:
`lansr-reproducibility-auditor`

Use:
`reproducibility-audit`

Audit at least:
- split order
- test isolation
- seed pairing
- baseline budget fairness
- hidden fallback
- checkpoint identity
- artifact destinations
- resume behavior
- contamination from previous run outputs
- equation/failure logging

CRITICAL findings block the full experiment.

### Stage 6 — Smoke test

Invoke:
`lansr-experimentalist`

Use:
`run-and-monitor-experiment`

Verify:
- correct branch
- clean/understood working tree
- environment
- GPU and disk
- output isolation
- manifest
- equation records
- failure records
- resume behavior
- memory use
- no final-test tuning

### Stage 7 — Full experiment

Run only the preregistered design.

Forbidden:
- changing the hypothesis after seeing test
- adding only favorable seeds
- deleting bad seeds
- changing metric definitions after results
- excluding invalid formulas silently
- increasing only one baseline's budget after comparing results
- reopening a final test to choose a model

If an unavoidable change occurs:
1. preserve original run artifacts
2. record deviation
3. mark the current cycle exploratory, or
4. create a new preregistered cycle

### Stage 8 — Analysis

Invoke:
- `lansr-results-analyst`
- `lansr-statistical-reviewer`

Use:
`symbolic-regression-evaluation`

Analyze directly from raw artifacts.

Mandatory separation:
- trajectory/prediction fit
- exact/skeleton/symbolic formula recovery
- variable recovery
- generalization
- validity/failure
- equation complexity
- singularity/safety behavior
- compute/time
- layer representation
- layer causal intervention
- layer adaptation/fine-tuning ability

Do not call non-significance equivalence.

### Stage 9 — Independent adversarial review

Invoke:
`lansr-independent-reviewer`

Use:
`independent-review`

Reviewer must inspect:
- preregistration
- literature note
- relevant code/config
- git diff
- raw results
- analysis
- proposed conclusions

Reviewer recommendation:
- `ACCEPT_AS_NEGATIVE`
- `ACCEPT_AS_PRELIMINARY`
- `REPLICATE`
- `REVISE_ANALYSIS`
- `INVALIDATE`

Any CRITICAL finding prevents a supported conclusion.

### Stage 10 — Replication gate

Use:
`replication-gate`

Invoke:
`lansr-replication-specialist`

Mandatory before promoting a result if it is:
- unusually large
- scientifically surprising
- a new layer mechanism
- a new GRN equation claim
- contrary to previous literature
- dependent on one seed/split/family
- identified by reviewer as fragile

Where feasible change at least one:
- seed
- data split
- equation family
- corruption/noise
- initial condition
- independent rerun from clean state

### Stage 11 — Cycle report

Invoke:
`lansr-report-writer`

Use:
`research-report`

Every cycle must create:

`GPU_RUNclaude1/reports/Cxxxx_report.md`

even when the result is negative or invalidated.

Required sections:
1. Executive summary
2. Hypothesis
3. Prior evidence and novelty check
4. Preregistered experiment
5. Deviations
6. Results
7. Statistical review
8. Independent review
9. Replication status
10. Interpretation
11. Limitations
12. Decision:
   - supported
   - unsupported
   - undecidable
   - invalidated
13. Reproduction commands
14. Artifact manifest reference
15. Next hypotheses
16. `human_review_priority: none | normal | high`

### Stage 12 — Artifact archive

Use:
`artifact-archive`

Every completed cycle must create:
- `GPU_RUNclaude1/manifests/Cxxxx_artifact_manifest.json`
- `GPU_RUNclaude1/manifests/Cxxxx_checksums.sha256`
- cycle report
- reviewer report
- analysis
- configs/commands needed for reproduction

Commit small research metadata and source changes when safe.
Push only if allowed by repository/user settings.
Do not commit huge raw datasets/checkpoints merely to satisfy archival rules.

### Stage 13 — Reflection / negative result recovery

For unsupported, invalidated, or ambiguous findings, use:
`negative-result-recovery`

Classify likely bottleneck:
- generation
- selection
- optimization
- evaluator
- identifiability
- architecture
- distribution shift
- data scarcity/noise
- compute
- layer-ranking criterion
- implementation/reproducibility

Prefer an experiment that distinguishes competing explanations over simply using more compute.

### Stage 14 — Persistent state and next cycle

Update:
- `research_state.md`
- `hypothesis_tree.md`
- `human_review_queue.md`

Then start next cycle unless a hard stop is active.

---

## 5. Three-cycle synthesis

Every 3 completed cycles, and whenever a high-priority result emerges:

Use:
`cycle-synthesis`

Create:
`GPU_RUNclaude1/syntheses/Sxxxx_Cxxxx-Cxxxx.md`

Include:
- cumulative supported findings
- cumulative negative findings
- invalidated claims
- repeated failure patterns
- remaining uncertainties
- hypotheses that should be abandoned
- top 3 next directions
- compute spent vs knowledge gained
- items requiring human review

---

## 6. Hard stops

Stop autonomous research and request human intervention only when:

1. current branch is wrong
2. another user's/agent's uncommitted work would be destroyed
3. destructive Git/history operation is required
4. private clinical/personal/confidential data appears unexpectedly
5. credentials or new external paid access are required
6. test leakage cannot be prevented
7. planned compute ceiling must be substantially exceeded
8. GPU/storage/hardware state is unsafe
9. previous results must be overwritten to continue
10. research ethics or data licensing requires human judgment
11. repeated crash loops consume resources without new information

The following are **not** hard stops:
- bad performance
- unsupported hypothesis
- null result
- reviewer disagreement
- code bug that can be fixed safely
- need to formulate a new hypothesis

---

## 7. Human review philosophy

Human review is asynchronous and sparse.

Do not block normal research waiting for human feedback.

Put notable results into:
`GPU_RUNclaude1/human_review_queue.md`

Priority:
- `none`: routine
- `normal`: useful to inspect
- `high`: surprising, strategically important, or potentially publishable

High priority does not itself stop the loop.

---

## 7b. Session continuity — keeping the loop alive

Claude Code is turn-based. Background subagent completions re-invoke the supervisor automatically, so
the loop advances on its own while work is in flight. But when the chain drains and the supervisor
finishes reporting, **nothing re-invokes it** and the turn ends, even mid-cycle. An instruction to
"continue autonomously" governs scientific decisions, not the turn structure.

To persist across that boundary, run:

```
/loop GPU_RUNclaude1の自律研究ループを継続。GPU_RUNclaude1/RESEARCH_LOOP.md のStage順に進め、
GPU_RUNclaude1/research_state.md の現在位置から再開する。hard stop以外では停止しない。
```

Omit the interval so the supervisor self-paces via `ScheduleWakeup` — cycle stages differ in duration
by orders of magnitude, so a fixed interval either wastes wakeups or delays the loop. Do not poll for
background tasks; harness-tracked work notifies on completion. Stop with
`ScheduleWakeup(stop: true)` or from `/tasks`.

`/schedule` is not a substitute: it runs separate cloud sessions that do not inherit this session's
frozen preregistration, retractions, or standing rules.

**Consequence for state hygiene**: because a turn can end at any point, `research_state.md` must be
resumable at any point — not only at cycle boundaries. Before ending a turn mid-cycle it must already
record the current cycle and stage, the binding preregistration version, what is running or blocked,
any correction not yet propagated, and the next concrete action.

Full detail: `.claude/rules/12-session-continuity.md`.

---

## 8. Research optimization objective

Do not optimize solely for:
- NMSE
- R²
- number of "positive" experiments
- number of cycles
- report count

Optimize for:
- information gain
- falsifiability
- reproducibility
- bottleneck localization
- symbolic recovery
- generalization
- interpretable mechanisms
- research novelty
- efficient use of compute
