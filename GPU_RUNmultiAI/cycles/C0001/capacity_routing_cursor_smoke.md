# C0001-INFRA-T002 Cursor smoke report

Task: `C0001-INFRA-T002` capacity-aware routing implementation smoke.
Worker: Cursor Agent (`repo-operator`).
Branch: `ai/C0001/repo-operator/capacity-routing`.
Date: 2026-09-12.

## Launch note

A direct `.ai/workers/cursor.sh --write` launch in the current pre-reload Codex session was **rejected by cached
policy**. The PI used a bash wrapper fallback to start this Cursor worktree session instead.

## Did the inventory prevent PI broad rescanning?

**Yes, materially.** The inventory at `GPU_RUNmultiAI/cycles/C0001/repo_evidence_inventory.md` documents current
routing, contradictions, adapter behavior, C0001 implications, and minimal canonical changes across 15 substantive
files with path-level provenance. A PI or downstream worker can proceed from the inventory and changed canonical
files without repeating a repository-wide routing scan.

## Files inspected (exact)

| # | Path | Purpose |
|---|---|---|
| 1 | `.agent/rules/08-routing-and-delegation.md` | canonical routing rules (edited) |
| 2 | `.agent/routing/MODEL_ROUTING.md` | role-to-model table (edited) |
| 3 | `.agent/routing/FALLBACKS.md` | fallback sequences (edited) |
| 4 | `.agent/agents/research-pi.md` | PI focus and delegation (edited) |
| 5 | `.agent/agents/repo-operator.md` | Cursor reconnaissance scope (edited) |
| 6 | `.agent/agents/research-scout.md` | Gemini scout role (edited) |
| 7 | `.agent/agents/bulk-worker.md` | Gemini bulk role (edited) |
| 8 | `.agent/agents/scientific-critic.md` | critic boundaries (edited) |
| 9 | `.agent/agents/report-writer.md` | report pipeline (edited) |
| 10 | `.agent/schemas/task-handoff-schema.md` | evidence provenance fields (edited) |
| 11 | `GPU_RUNmultiAI/RESEARCH_LOOP.md` | stage routing (edited) |
| 12 | `.agent/rules/09-subagent-policy.md` | Gemini E2E acceptance |
| 13 | `GPU_RUNmultiAI/research_state.md` | active task state (edited) |
| 14 | `.codex/README.md` | Codex PI adapter (edited) |
| 15 | `GEMINI.md` | Gemini bootstrap (edited) |
| 16 | `.cursor/rules/00-multiai-core.mdc` | Cursor adapter (edited) |
| 17 | `GPU_RUNmultiAI/cycles/C0001/capacity_routing_handoff.md` | task requirements |
| 18 | `.agent/skills/worker-handoff/SKILL.md` | handoff provenance (edited) |
| 19 | `.agent/skills/autonomous-research-cycle/SKILL.md` | cycle routing (edited) |
| 20 | `.agent/skills/implementation-handoff/SKILL.md` | Cursor-first implementation (edited) |

Scientific C0001 artifacts (`hypothesis_review.md`, `preregistration_draft.md`, `literature_evidence.md`, etc.)
were **not** opened or edited.

## Checks performed

| Check | Result |
|---|---|
| Inventory ≥10 substantive files with path provenance | PASS (15 files in inventory) |
| Thresholds, exceptions, prohibited misuse explicit | PASS (`.agent/rules/08-routing-and-delegation.md`, `MODEL_ROUTING.md`) |
| Stage routing non-contradictory | PASS (`RESEARCH_LOOP.md` aligned with routing rules) |
| Provider adapters thin (pointers, not wholesale copy) | PASS |
| Gemini filesystem limitation explicit | PASS (`FALLBACKS.md`, `GEMINI.md`, `09-subagent-policy.md`) |
| Preregistration/review/replication guards preserved | PASS (RESEARCH_LOOP Stages 3, 6, 9, 10 marked never demote) |
| Scientific C0001 artifacts untouched | PASS |
| `git diff --check` | PASS |
| `update_ai_manifest.sh` + `verify_ai_manifest.sh` | PASS (deterministic) |
| `python -m compileall -q src scripts tests` | PASS |

## Independent review response checks (H1–H7)

| Finding | Required fix | Result |
|---|---|---|
| H1 smoke artifacts uncommitted | Commit Gemini/Claude smoke artifacts with review fixes | PASS |
| H2 reconnaissance fallback contradiction | Align FALLBACKS/MODEL_ROUTING; PI exception before Codex/Claude broad recon | PASS |
| H3 `substantive file` undefined | Canonical definition in `.agent/rules/08-routing-and-delegation.md` | PASS |
| H4 reviewer independence unbound | `implementer_identity`, `independent_reviewer_identity`, `reviewer_diff_assertion` in handoff/state/loop | PASS |
| H5 Gemini limitation omitted from canonical threshold | Prompt-supplied evidence requirement beside ~10k threshold | PASS |
| H6 report numeric-fidelity gap | Stage 11 mechanical JSON/CSV comparison before polish/final claims | PASS |
| H7 evidence-packet chunking missing | Deterministic split by artifact/run/section; no universal token ceiling | PASS |
| Never-demote list consistency | Reviewer independence in all never-demote summaries | PASS |

## Downstream smoke status

| Worker | Task | Status |
|---|---|---|
| Gemini | Classify inventory; evidence/inference/speculation separation | **completed** (`capacity_routing_gemini_smoke.md`) |
| Claude Opus | Compressed-packet scientific-quality audit | **completed** (`capacity_routing_claude_review.md`; REVISE; fixes applied) |
| Codex PI | Integrate accepted routing policy to remote branch | **pending** |

## Deviations

None from handoff scope. All canonical minimum write-scope files updated; only necessary thin adapters touched.
Scientific C0001 artifacts remain untouched.
