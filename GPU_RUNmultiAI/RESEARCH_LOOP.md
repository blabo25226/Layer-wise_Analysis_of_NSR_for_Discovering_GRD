# GPU_RUNmultiAI Autonomous Research Loop

## Mission

Run a continuous, falsifiable, reproducible multi-AI research program.
The default is to continue into the next cycle unless a hard stop is active.

## Tracks

Keep infrastructure and scientific work separate in state, reviews, and integration.

| Track | Examples | Durability authority |
|---|---|---|
| Infrastructure | C0000 bootstrap, PR #5 remediation, routing, manifest, push policy | `research_state.md` `tracks.infrastructure` |
| Scientific | hypothesis tree, preregistration, experiments, analysis | `research_state.md` `tracks.scientific` plus cycle artifacts under `cycles/Cxxxx/` |

Infrastructure PASS/FAIL does not support or falsify a scientific hypothesis.
Do not mix infrastructure conclusions into scientific reports or preregistrations.

## Capacity-aware routing (C0001 onward)

Apply `.agent/rules/08-routing-and-delegation.md` at every stage. Summary:

| Trigger | Default worker |
|---|---|
| 5+ substantive repository files | Cursor `repo-operator` |
| ~10k+ mechanically processable tokens | Gemini scout/bulk-worker |
| Multi-file implementation | Cursor `repo-operator` |
| Report first draft | Gemini → Claude polish → PI final claims |

Capacity pressure may reroute routine work but **never** removes preregistration and metric freeze, final scientific
review and reviewer independence, primary-artifact verification, leakage protection, or replication gates.

Routine broad reconnaissance must not fall back to Codex or Claude without a recorded PI exception and reason.

## Stage 0 — Reconstruct state

Research PI:
- read repository state and `research_state.md`
- delegate repository reconnaissance (5+ files) to Cursor `repo-operator`
- inspect active branches/worktrees/tasks
- repair stale bookkeeping and reclassify stale `running` tasks
- record `observed_commit`, `base_commit`, and verified `remote_commit`
- identify exact next action for each track

## Stage 1 — Competing hypotheses

Cursor `repo-operator` performs repository reconnaissance when needed.
PI subagents synthesize; Gemini provides breadth when useful; Claude Opus critiques.
Update `hypothesis_tree.md`.
Select one cycle hypothesis by information gain / cost.

## Stage 2 — Literature / repository evidence

Gemini Scout performs broad evidence collection (~10k+ token corpora).
Cursor reconnaissance for repository structure when 5+ substantive files are involved.
A higher-reliability critic checks high-impact literature/novelty claims.
Persist evidence with provenance; separate evidence/inference/speculation.

## Stage 3 — Preregistration

Claude Sonnet or Research Engineer may draft.
Claude Opus / statistical reviewer attacks the design.
Research PI freezes the binding version before final-test access.
**Never demote for capacity.**

## Stage 4 — Work decomposition and isolation

Create bounded task handoffs with evidence-packet provenance fields when useful.
Write-capable concurrent tasks use independent branches/worktrees.
Record write scopes and active tasks in state.

## Stage 5 — Implementation

Default:
- Cursor Composer: repository reconnaissance and heavy multi-file implementation
- Claude Sonnet: scientific engineering / secondary implementation
- Luna: small fixes/tests
- Gemini: bulk generated indexes/derived mechanical artifacts

Run tests and commit task branches.

## Stage 6 — Pre-run audit and smoke

Independent reproducibility review.
Verify leakage protection, checkpoint identity, outputs, resume behavior, GPU/storage, manifest and compute ceiling.
Run a smoke experiment.
**Never demote for capacity.**

## Stage 7 — Full frozen experiment

Execute only the frozen design.
Preserve failures and deviations.
Do not tune on final-test observations.

## Stage 8 — Analysis

Use bulk workers for extraction and aggregation support (~10k+ token artifacts).
Primary analyst interprets raw artifacts using the frozen endpoint.
Separate numerical, symbolic, validity, generalization, compute and layer evidence.

## Stage 9 — Independent adversarial review

Claude Opus is preferred.
Reviewer attempts to falsify the conclusion from primary artifacts.
**Never demote for capacity.**

## Stage 10 — Replication gate

Replicate fragile/surprising/high-impact claims when required.
**Never demote for capacity.**

## Stage 11 — Report and archive

Gemini produces report first draft.

Before Claude Sonnet review/polish or PI final claims, **mechanically verify numeric fidelity**: compare every reported
numeric value, table cell, and aggregate cited in the draft against the primary JSON/CSV artifacts that produced them.
Record discrepancies and resolve or flag them before scientific polish or final claim approval.

Claude Sonnet reviews/polishes; PI owns final claims.
Record `implementer_identity` and `independent_reviewer_identity` in the handoff/state contract; assert the final
independent reviewer differs from the implementation author unless a documented hard-stop exception is approved.

Create cycle report, manifest/checksums, review record and reproduction commands.
Negative/invalidated cycles still get a report.

## Stage 12 — Persist and continue

Update:
- `research_state.md`
- `hypothesis_tree.md`
- `human_review_queue.md`
- task board

After accepted integration or a stable checkpoint on an active remote research branch, non-force push and verify
`remote_commit` before reporting durability.

Refresh `MANIFEST.sha256` when bootstrap/control/tooling files change:

```bash
bash scripts/ops/update_ai_manifest.sh
bash scripts/ops/verify_ai_manifest.sh
```

If `hard_stop: false`, create/select the next cycle and continue.

## Continuity rule

A provider session may naturally end. That event is not a research stop.
Before the parent session ends, state must identify the exact next action.
An external watchdog may relaunch Codex/PI and instruct it to run state reconstruction then continue.

## Hard-stop rule

Use `.agent/rules/13-retry-fallback-and-hard-stops.md`.
