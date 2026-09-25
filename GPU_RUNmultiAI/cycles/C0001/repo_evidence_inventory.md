# C0001-INFRA-T002 repository evidence inventory

Task: capacity-aware routing reconnaissance for `C0001-INFRA-T002`.
Base commit: `0e168edb297400ec5569c44c2898e4bd473a423a`.
Inventory author: Cursor Agent (`repo-operator`).
Date: 2026-09-12.

This inventory covers current routing, contradictions, adapter behavior, active C0001 implications, and the minimal
canonical changes required. Each claim cites a repository path.

## 1. `.agent/rules/08-routing-and-delegation.md`

**Current state (pre-change):** Lists default model routing by logical role. `repo-operator` maps to Cursor Composer 2.5;
`research-scout` and `bulk-worker` map to Gemini 3.8 Flash. Instructs Sol to avoid bulk editing but does not encode
capacity thresholds, prohibited misuse, or stage-specific routing.

**Contradiction:** Sol is told to avoid bulk editing, but there is no positive rule routing repository reconnaissance
(5+ files) to Cursor or ~10k-token mechanical work to Gemini. Stage defaults in `RESEARCH_LOOP.md` partially overlap
but are not unified here.

**Proposed change:** Add capacity-aware routing principle, default thresholds, capacity-pressure exceptions, and
prohibited misuse. Keep vendor names only in the routing table reference.

## 2. `.agent/routing/MODEL_ROUTING.md`

**Current state:** Role-to-model table with fallbacks. `repo-operator` -> Cursor; `research-scout`/`bulk-worker` ->
Gemini; `report-writer` -> Claude Sonnet 5. Notes that routing is a default, not a scientific fact.

**Contradiction:** `report-writer` is Claude-first, but the handoff requires Gemini first draft with Claude
review/polish. `research-engineer` lists Cursor as fallback, which is correct for scientific engineering but
conflicts with making Cursor the default reconnaissance worker from Stage 1.

**Proposed change:** Add capacity thresholds section; split report drafting into Gemini draft + Claude polish;
clarify `repo-operator` as Repository Intelligence + Implementation from Stage 1 onward.

## 3. `.agent/routing/FALLBACKS.md`

**Current state:** Fallback sequences per task type. Gemini filesystem write limitation is explicit (lines 9–10).
Report drafting: Claude Sonnet -> Luna -> PI. Bulk scan: Gemini -> Luna -> Cursor Explore.

**Gap:** No explicit fallback for repository reconnaissance at 5+ files (should be Cursor first). Report drafting
order contradicts the new Gemini-first draft policy.

**Proposed change:** Add reconnaissance fallback (Cursor -> Luna explore -> PI). Reorder report drafting to
Gemini -> Claude Sonnet -> Luna -> PI final claims. Preserve Gemini filesystem E2E limitation text.

## 4. `.agent/agents/research-pi.md`

**Current state:** PI owns direction, decomposition, routing, integration, freeze, verdict, continuity. Delegates
bulk editing and routine operations; uses expensive context for synthesis.

**Gap:** Does not enumerate the PI focus areas from the handoff (hypothesis integration, experiment choice, conflict
resolution, design freeze, critical verification, interpretation, next-cycle decision). Does not prohibit PI from
doing broad repo scans when Cursor is available.

**Proposed change:** Enumerate PI focus; explicitly delegate repository reconnaissance and multi-file implementation
to Cursor from Stage 1 onward.

## 5. `.agent/agents/repo-operator.md`

**Current state:** "Default heavy-write worker" for multi-file edits, refactors, tests, Git. No reconnaissance scope.

**Gap:** Handoff requires Cursor as "Repository Intelligence + Implementation" from Stage 1 — including call/dependency/
history/test discovery and implementation summaries.

**Proposed change:** Expand role to repository-wide reconnaissance, discovery, multi-file implementation, and
implementation summaries. Remain explicit that scientific endpoints must not be altered for test passage.

## 6. `.agent/agents/research-scout.md`

**Current state:** Broad literature, repository, artifact, and log exploration; evidence inventories. Gemini preferred.

**Gap:** Does not state prompt-supplied evidence mode while Gemini filesystem E2E is unavailable. Does not reference
the ~10k-token threshold.

**Proposed change:** Clarify Gemini as bulk information processor/scout; separate evidence/inference/speculation;
note prompt-supplied evidence tasks when filesystem tools are soft-denied.

## 7. `.agent/agents/bulk-worker.md`

**Current state:** Repetitive extraction, indexing, conversion, summarization. Records failure counts.

**Gap:** Does not list long-log classification, deduplication, tables/indexes, evidence packets, failure taxonomy,
or report first drafts as in-scope.

**Proposed change:** Enumerate bulk processing categories from handoff; escalate scientific interpretation.

## 8. `.agent/agents/scientific-critic.md`

**Current state:** Adversarial review from primary artifacts; inspect rather than trust summaries.

**Alignment:** Already correct — critic inspects primary artifacts. No broad repo scan default needed.

**Proposed change:** Add explicit note that broad repository reconnaissance and routine first drafts should not
default to Claude Opus; critic receives compressed evidence packets and checks only necessary primary files.

## 9. `.agent/agents/report-writer.md`

**Current state:** Claude Sonnet 5 preferred; Japanese human-facing reports from verified artifacts.

**Contradiction:** Handoff routes report first draft to Gemini; Claude does review/polish; Codex PI owns final claims.

**Proposed change:** Reposition as review/polish stage after Gemini first draft; preserve exact numbers and no
claim strengthening.

## 10. `.agent/schemas/task-handoff-schema.md`

**Current state:** YAML schema with task_id, role, write_scope, acceptance_tests, etc. Completion record lists
commit, tests, deviations.

**Gap:** No fields for evidence-packet provenance (source files inspected, evidence vs inference separation).

**Proposed change:** Add optional `evidence_packet`, `files_inspected`, `evidence_provenance` fields and require
evidence/inference/speculation separation in completion records for reconnaissance tasks.

## 11. `GPU_RUNmultiAI/RESEARCH_LOOP.md`

**Current state:** Stage 0 PI reconstructs state. Stage 1 uses PI subagents + Gemini breadth + Claude critique.
Stage 2: Gemini Scout broad evidence. Stage 5: Cursor heavy implementation. No Cursor reconnaissance at Stage 1.

**Contradiction:** Stage 1–2 do not route 5+ file repository reconnaissance to Cursor. Stage 11 report does not
mention Gemini first draft.

**Proposed change:** Stage 0–1: Cursor reconnaissance when 5+ substantive files. Stage 2: Gemini breadth with
prompt-supplied evidence fallback. Stage 5: Cursor-first multi-file. Stage 11: Gemini draft -> Claude polish ->
PI final claims. Preserve preregistration, leakage, replication, and independent review guards.

## 12. `.agent/rules/09-subagent-policy.md`

**Current state:** Gemini exit 0 without artifact = FAIL. Prompt-supplied evidence tasks when filesystem E2E fails.

**Alignment:** Matches handoff requirement. No change to core policy; reference from routing rules.

## 13. `.agent/skills/worker-handoff/SKILL.md` and `.agent/skills/implementation-handoff/SKILL.md`

**Current state:** Point to task-handoff schema; implementation handoff defines frozen constraints and acceptance.

**Gap:** No mention of evidence-packet provenance or Cursor-first reconnaissance threshold.

**Proposed change:** Add provenance requirements and routing threshold references.

## 14. `GPU_RUNmultiAI/research_state.md`

**Current state:** `C0001-INFRA-T002` status `planned`; infrastructure track stage `CAPACITY_AWARE_ROUTING`;
scientific track at `PREREGISTRATION_REVIEW`. Open finding: Gemini headless filesystem soft-deny.

**C0001 implication:** Infrastructure routing change must not touch scientific artifacts under `cycles/C0001/`
(hypothesis, preregistration, evidence). State update records Cursor completion; Gemini/Claude smoke remains pending.

## 15. Provider adapters (`.codex/README.md`, `.cursor/rules/00-multiai-core.mdc`, `GEMINI.md`, `.agents/rules/01-gemini-scout.md`, `CLAUDE.md`)

**Current state:** Thin adapters pointing to canonical files. Cursor: "primary repo operator for heavy multi-file
editing." Codex: "default Research PI, not default bulk editor." Gemini: headless filesystem limitation explicit.

**Gap:** Cursor adapter does not mention reconnaissance. Codex adapter does not mention capacity thresholds.
Gemini adapter does not mention ~10k-token bulk threshold or report first-draft role.

**Proposed change:** Thin pointer updates only — no wholesale canonical copy.

## Contradictions summary

| Area | Conflict | Resolution |
|---|---|---|
| Report drafting | MODEL_ROUTING + FALLBACKS Claude-first vs handoff Gemini-first | Gemini draft, Claude polish, PI claims |
| Stage 1 reconnaissance | RESEARCH_LOOP PI/subagent vs handoff Cursor-first at 5+ files | Cursor repo-operator from Stage 1 |
| Scout role | research-scout Gemini without filesystem caveat | Prompt-supplied evidence + bulk threshold |
| PI scope | Implicit delegation vs no threshold encoding | Explicit thresholds in 08-routing |

## Prohibited guards (must remain unchanged)

From `.agent/rules/04-preregistration-and-metric-freeze.md`, `.agent/rules/10-independent-review-and-replication.md`,
and `RESEARCH_LOOP.md` Stages 3, 6, 9, 10:

- preregistration freeze before final-test access
- leakage protection and primary-artifact verification
- independent adversarial review (implementer ≠ sole reviewer)
- replication gate for fragile/high-impact claims
- failure-aware aggregation

Capacity routing must not weaken these.

## Minimal write scope (confirmed)

Canonical: files listed in `capacity_routing_handoff.md` § Canonical minimum write scope.
Campaign: inventory, smoke, state, task board, MANIFEST.
Excluded: C0001 scientific evidence, hypothesis, preregistration, review, implementation, result artifacts.
