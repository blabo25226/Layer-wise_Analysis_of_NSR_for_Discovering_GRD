# Logical role -> preferred model

| Logical role | Preferred worker/model | Primary purpose | Fallback |
|---|---|---|---|
| research-pi | GPT-5.6 Sol | direction, decomposition, integration, final decision | Claude Opus 5 |
| scientific-critic | Claude Opus 5 | adversarial scientific review | GPT-5.6 Sol |
| final-auditor | Claude Opus 5 | cycle promotion audit | GPT-5.6 Sol |
| research-engineer | Claude Sonnet 5 | scientific implementation/design concretization | Cursor Composer 2.5 |
| repo-operator | Cursor Composer 2.5 | repository reconnaissance, multi-file editing, refactor, tests, Git | Claude Sonnet 5 (implementation-only; not routine broad reconnaissance) |
| fast-worker | GPT-5.6 Luna | small code/edit/search/test work | Gemini 3.8 Flash |
| research-scout | Gemini 3.8 Flash | broad search, corpus/log scan, evidence packets | Cursor Composer 2.5 → Luna |
| bulk-worker | Gemini 3.8 Flash | repetitive extraction/transformation/indexing, report first drafts | Cursor Composer 2.5 → Luna |
| results-analyst | Claude Sonnet 5 + Luna/Gemini support | interpretation after mechanical extraction | GPT-5.6 Sol |
| statistical-reviewer | Claude Opus 5 | design/inference audit | GPT-5.6 Sol |
| report-writer | Gemini 3.8 Flash (draft) → Claude Sonnet 5 (polish) | human-facing report pipeline | GPT-5.6 Luna |
| reproducibility-auditor | Claude Opus 5 | leakage/provenance/reproducibility | GPT-5.6 Sol |

Routing is a default, not a scientific fact. The Research PI may reroute based on availability, context length, failure,
or task characteristics, and must record material rerouting when it affects independence.

## Capacity-aware default thresholds

| Trigger | Default worker | Notes |
|---|---|---|
| 5+ substantive repository files (reconnaissance) | Cursor `repo-operator` | see substantive-file definition in `.agent/rules/08-routing-and-delegation.md` |
| ~10k+ mechanically processable input tokens | Gemini `research-scout` / `bulk-worker` | prompt-supplied evidence when filesystem E2E unverified; see limitation below |
| Multi-file implementation | Cursor `repo-operator` | refactors, tests, Git task branches |
| Report first draft | Gemini `bulk-worker` | numeric-fidelity check → Claude Sonnet polish; PI owns final claims |

Codex/Claude broad reconnaissance is not a routine fallback. Record a PI exception and reason before delegating.

## Capacity pressure

Routine work may reroute per the thresholds. Preregistration and metric freeze, final scientific review and reviewer
independence, primary-artifact verification, leakage protection, and replication gates are **never** demoted for
capacity reasons.

## Gemini filesystem limitation

Antigravity headless may soft-deny filesystem tools and exit 0 without writing artifacts. Until filesystem E2E passes,
use prompt-supplied evidence tasks or route persistence to Cursor/Claude/Codex fallback. See `.agent/routing/FALLBACKS.md`.

## Evidence-packet chunking

When a prompt-supplied packet is too large for one worker context or approaches the configured/request limit, split
deterministically by artifact/run/logical section; preserve chunk IDs and provenance; deduplicate only after chunk
summaries; retain links to primary artifacts. Do not invent a universal token ceiling.
