# C0001 infrastructure task handoff: capacity-aware routing

## Identity

- task_id: `C0001-INFRA-T002`
- track: `infrastructure`
- role: `repo-operator`
- preferred_worker: `Cursor Agent`
- branch: `ai/C0001/repo-operator/capacity-routing`
- worktree: `/tmp/lansr-multiai-C0001-capacity-routing`
- base commit: `0e168edb297400ec5569c44c2898e4bd473a423a`

## Objective

Make capacity-aware routing a durable part of the canonical Multi-AI Research OS. Preserve research quality while
moving repository reconnaissance, routine multi-file implementation, bulk extraction, first-draft writing, and
mechanical organization away from Codex/Claude and toward Cursor/Gemini.

This is resource routing, not quota equalization. Final scientific judgment remains with the PI and independent
scientific critics.

## Required repository reconnaissance

Before editing, inspect at least ten substantive canonical/provider/campaign files and create
`GPU_RUNmultiAI/cycles/C0001/repo_evidence_inventory.md`. Each claim must cite a repository path and, when relevant,
a section, function, config key, test, or artifact. Cover current routing, contradictions, adapter behavior, active
C0001 implications, and proposed minimal changes. The PI should not need to repeat the broad scan.

## Required policy changes

1. Codex PI focuses on direction, hypothesis integration, experiment choice, delegation, conflict resolution, design
   freeze, critical verification, interpretation, verdict, next-cycle decision, and continuity.
2. Cursor becomes `Repository Intelligence + Implementation` from Stage 1 onward. Repository-wide reconnaissance,
   call/dependency/history/test discovery, multi-file implementation, refactor, debug, tests, and implementation
   summaries route Cursor-first.
3. Gemini becomes the prompt-supplied bulk information processor/scout while filesystem E2E is unavailable: long-log
   classification, JSON/CSV/result organization, literature breadth, deduplication, tables/indexes, evidence packets,
   failure taxonomy, and report first drafts. It separates evidence/inference/speculation.
4. Claude Opus focuses on scientific/statistical/methodological/adversarial/reproducibility/final audit; Claude Sonnet
   on specialized scientific engineering and scientific polish. Broad repo scan and routine first drafts should not
   default to Claude.
5. Encode default thresholds with explicit exceptions:
   - five or more substantive repository files -> Cursor reconnaissance first
   - roughly 10k or more mechanically processable input tokens -> Gemini first
   - multi-file implementation -> Cursor first
   - report first draft -> Gemini first; Claude review/polish; Codex final claims
6. Capacity pressure may reroute routine work, but must never remove preregistration, final scientific review,
   primary-artifact verification, leakage protection, or replication gates.
7. Prohibit artificial quota burning, unnecessary duplicated work, Gemini final scientific decisions, Cursor
   unsupported scientific conclusions, and quality loss for usage balancing.
8. Update the stage-by-stage cycle routing and active-task defaults for C0001 onward.
9. Keep `.agent/` canonical. Provider files stay thin adapters pointing to canonical policy.
10. Add task-handoff fields that make evidence-packet provenance and acceptance explicit where useful.

## Canonical minimum write scope

- `.agent/rules/08-routing-and-delegation.md`
- `.agent/routing/MODEL_ROUTING.md`
- `.agent/routing/FALLBACKS.md`
- `.agent/agents/research-pi.md`
- `.agent/agents/repo-operator.md`
- `.agent/agents/research-scout.md`
- `.agent/agents/bulk-worker.md`
- `.agent/agents/scientific-critic.md`
- `.agent/agents/report-writer.md`
- `.agent/skills/worker-handoff/SKILL.md`
- `.agent/skills/state-reconstruction/SKILL.md`
- `.agent/skills/autonomous-research-cycle/SKILL.md`
- `.agent/skills/literature-evidence/SKILL.md`
- `.agent/skills/implementation-handoff/SKILL.md`
- `.agent/schemas/task-handoff-schema.md`
- `GPU_RUNmultiAI/RESEARCH_LOOP.md`

## Thin adapter / campaign write scope

- only necessary `.codex/`, `.cursor/`, `.claude/`, `.gemini/`, `.agents/`, `GEMINI.md`, and `CLAUDE.md` adapter files
- `GPU_RUNmultiAI/cycles/C0001/repo_evidence_inventory.md`
- `GPU_RUNmultiAI/cycles/C0001/capacity_routing_cursor_smoke.md`
- `GPU_RUNmultiAI/task_board.md`
- `GPU_RUNmultiAI/research_state.md`
- `MANIFEST.sha256`

Do not edit C0001 scientific evidence, hypothesis, preregistration, review, implementation, or result artifacts.

## Acceptance tests

- inventory covers at least ten substantive files and every material claim has path-level provenance
- thresholds, exceptions, prohibited misuse, capacity pressure, and stage routing are explicit and non-contradictory
- provider adapters remain thin; canonical text is not copied wholesale
- current Gemini filesystem limitation remains explicit
- final-test, preregistration, failure-aware, primary-artifact, reviewer-independence, and replication guards remain
- manifest update/verify passes and is deterministic
- `git diff --check` passes
- only scoped files are changed
- commit with message `Rebalance Multi-AI research routing`

## Downstream smoke packet

The PI will pass the Cursor inventory to Gemini without requiring filesystem access. Gemini must return categories,
deduplicated findings, unresolved questions, candidate routing risks, and evidence/inference/speculation separation.
Claude then receives the compressed packet and checks only necessary primary files before a scientific-quality audit.
