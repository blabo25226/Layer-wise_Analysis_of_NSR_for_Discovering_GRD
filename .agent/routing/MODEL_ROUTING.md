# Logical role -> preferred model

| Logical role | Preferred worker/model | Primary purpose | Fallback |
|---|---|---|---|
| research-pi | GPT-6 Sol (Medium in UI) | direction, decomposition, integration, final decision | Claude Opus 5.5 |
| scientific-critic | Claude Opus 5.5 | adversarial scientific review | GPT-6 Sol |
| final-auditor | Claude Opus 5.5 | cycle promotion audit | GPT-6 Sol |
| research-engineer | Claude Sonnet 5 | scientific implementation/design concretization | Cursor Composer 2.5 |
| repo-operator | Cursor Composer 2.5 | repository reconnaissance, multi-file editing, refactor, tests, Git | Claude Sonnet 5 (implementation-only; not routine broad reconnaissance) |
| fast-worker | GPT-6 Luna | small code/edit/search/test work | Gemini 3.8 Flash |
| research-scout | Gemini 3.8 Flash (`gemini-3.8-flash-high`) | broad search, corpus/log scan, evidence packets, compression | Cursor Composer 2.5 → Luna |
| bulk-worker | Gemini 3.8 Flash | repetitive extraction/transformation/indexing, report first drafts | Cursor Composer 2.5 → Luna |
| results-analyst | Claude Sonnet 5 + Luna/Gemini support | interpretation after mechanical extraction | GPT-6 Sol |
| statistical-reviewer | Claude Opus 5.5 | design/inference audit | GPT-6 Sol |
| report-writer | Gemini 3.8 Flash (draft) → Claude Sonnet 5 / Opus 5.5 (polish) | human-facing report pipeline | GPT-6 Luna |
| reproducibility-auditor | Claude Opus 5.5 | leakage/provenance/reproducibility | GPT-6 Sol |

GPT-6 Astra: exceptional verification only (not routine routing).

Routing is a default, not a scientific fact. The Research PI may reroute based on availability, context length, failure,
or task characteristics, and must record material rerouting when it affects independence.

## Capacity-aware default thresholds

| Trigger | Default worker | Notes |
|---|---|---|
| 5+ substantive repository files (reconnaissance) | Cursor `repo-operator` | see substantive-file definition in `.agent/rules/08-routing-and-delegation.md` |
| Gemini-first (see rule in 08-routing) | Gemini `research-scout` / `bulk-worker` | ~5k+ tokens, 5+ artifacts, 10+ records, compressible packets, first drafts |
| Multi-file implementation | Cursor `repo-operator` | refactors, tests, Git task branches |
| Report first draft | Gemini `bulk-worker` | numeric-fidelity check → Claude polish; PI owns final claims |

Codex/Claude broad reconnaissance and Codex subagents are not routine fallbacks. Record a PI exception and reason before
delegating.

## Capacity pressure

Routine work may reroute per the thresholds. Preregistration and metric freeze, final scientific review and reviewer
independence, primary-artifact verification, leakage protection, and replication gates are **never** demoted for
capacity reasons.

## Gemini broker and filesystem

Use `.ai/workers/gemini.sh --broker` for prompt packet → stdout → local artifact persistence when direct filesystem
access is unverified. Antigravity model flag: `--model gemini-3.8-flash-high` (override with `AI_WORKERS_GEMINI_MODEL`).

Until direct filesystem E2E passes, use broker mode or prompt-supplied evidence; see `.agent/routing/FALLBACKS.md`.

## Evidence-packet chunking

When a prompt-supplied packet is too large for one worker context or approaches the configured/request limit, split
deterministically by artifact/run/logical section; preserve chunk IDs and provenance; deduplicate only after chunk
summaries; retain links to primary artifacts. Do not invent a universal token ceiling.
