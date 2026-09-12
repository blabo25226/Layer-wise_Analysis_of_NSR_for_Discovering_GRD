# C0001-INFRA-T002 independent routing review

Reviewer: Claude (`scientific-critic` / methodological critic)
Reviewed commit: `ceb92cb6f51411d8d3d8f225a49007c0616fe44e`
Date: 2026-09-12
Mode: read-only

## Scope

The reviewer started from:

- `GPU_RUNmultiAI/cycles/C0001/capacity_routing_gemini_smoke.md`
- `GPU_RUNmultiAI/cycles/C0001/repo_evidence_inventory.md`

It then inspected only these four primary policy files:

- `.agent/rules/08-routing-and-delegation.md`
- `.agent/routing/MODEL_ROUTING.md`
- `.agent/routing/FALLBACKS.md`
- `GPU_RUNmultiAI/RESEARCH_LOOP.md`

PR #4, `GPU_RUNclaude1` scientific content, and sealed GPU_RUN5 raw test artifacts were not inspected.

An initial read-only attempt ended without returning the review body. The retry returned this complete review. The first
process exit code was therefore not treated as task success.

## Findings

### H1 — MAJOR: smoke artifacts were not committed

The Gemini and Claude smoke artifacts were added after `ceb92cb`. They must be committed before handoff so the audit is
recoverable.

Required fix: commit both smoke artifacts and the fixes below on the task branch.

### H2 — MAJOR: reconnaissance fallback contradiction

`.agent/routing/FALLBACKS.md` routed repository reconnaissance Cursor -> Luna -> PI, while the capacity principle says
broad scans should not default back to Codex. `MODEL_ROUTING.md` also used a different research-scout fallback order.

Required fix: make the chains agree. When routine broad reconnaissance falls back to Codex or Claude, require a
recorded PI exception and reason.

### H3 — MAJOR: `substantive file` was undefined

The five-file threshold was not auditable because the term was undefined.

Required fix: define it once in `.agent/rules/08-routing-and-delegation.md`. Exclude generated/vendor/boilerplate files
unless they contain task-relevant primary evidence, and count a file when understanding its task-relevant logic,
configuration, result, or contract requires material reading rather than a path/existence check.

### H4 — MAJOR: reviewer independence was not mechanically bound

Fallback routing could let one worker implement, analyze, and polish its own output. Soft wording alone did not bind
reviewer identity.

Required fix: add implementer and independent-reviewer identity fields to the handoff/state contract and assert that
the final independent reviewer differs from the implementation author unless a documented hard-stop exception is
approved.

### H5 — MODERATE: canonical routing rule omitted Gemini filesystem limitation

The limitation existed in routing support files but not beside the canonical Gemini threshold.

Required fix: add an explicit pointer and prompt-supplied evidence requirement in
`.agent/rules/08-routing-and-delegation.md`.

### H6 — MODERATE: report pipeline lacked numeric-fidelity verification

Gemini draft -> Claude polish -> PI final claims did not require checking numbers against primary artifacts.

Required fix: Stage 11 must mechanically compare reported numeric values/tables with primary JSON/CSV artifacts and
record discrepancies before scientific polish or final claim approval.

### H7 — MODERATE: no evidence-packet chunking rule

Prompt-supplied mode did not define a practical oversize-packet behavior.

Required fix: do not guess a provider token ceiling. If an evidence packet is too large for one worker context or
approaches the configured/request limit, split it deterministically by artifact/run/logical section; preserve chunk
IDs and provenance; deduplicate only after chunk summaries; and retain links to primary artifacts.

## Guardrail verdict

`PASS`

Preregistration/metric freeze, final scientific review, primary-artifact verification, leakage protection, and
replication gates were all retained. The reviewer requested consistent explicit mention of reviewer independence in
every summary of the never-demote set.

## Context-reduction verdict

`SUPPORTED_DIRECTIONALLY_MAGNITUDE_UNSUBSTANTIATED`

The compressed packet reduced the audit to the four policy files above and retained the material routing conflicts and
guards. No quantitative efficiency gain is established because no baseline context/token measurement was frozen.

## Final verdict

`REVISE`

H1 and H2 block acceptance. H3 and H4 must also close before the routing gate is operational/auditable. H5-H7 are
required consistency and scientific-integrity fixes. The scientific C0001 track does not need rollback.
