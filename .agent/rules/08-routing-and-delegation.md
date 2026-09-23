# Routing and delegation

Use logical roles, not vendor names, as the stable interface.

## Capacity-aware routing principle

This is **resource routing**, not quota equalization. Preserve research quality while moving repository
reconnaissance, routine multi-file implementation, bulk extraction, first-draft writing, and mechanical
organization away from Codex/Claude toward Cursor/Gemini when reliable.

Final scientific judgment remains with the Research PI (GPT-6 Sol, reasoning level Medium — configured by humans in the UI)
and independent scientific critics (Claude Opus 5.5).

Expensive-model token use should maximize research value: Sol for synthesis and decisions, not routine mechanical work.

## Standard pipeline (C0001 onward)

When multiple workers apply, prefer:

```text
Cursor        → repository evidence collection / implementation
Gemini        → compression, classification, deduplication, first drafts
Claude Opus 5.5 → scientific / statistical / methodological criticism
GPT-6 Sol PI  → final synthesis / decision
```

Before Codex or Claude directly processes large mechanical evidence, route through Gemini unless a documented exception
applies (see **Gemini-first rule** below).

## Default role routing

| Logical role | Preferred worker/model | Primary responsibility |
|---|---|---|
| research-pi | GPT-6 Sol (Medium in UI) | direction, hypothesis integration, experiment choice, delegation, conflict resolution, design freeze, critical verification, interpretation, verdict, next-cycle decision, continuity |
| repo-operator | Cursor Composer 2.5 | Repository Intelligence + Implementation from Stage 1 onward |
| research-scout, bulk-worker, artifact-curator | Gemini 3.8 Flash (`gemini-3.8-flash-high` via Antigravity) | bulk information processing, scout, indexing, long-log work, evidence compression |
| scientific-critic, final-auditor, statistical-reviewer, reproducibility-auditor | Claude Opus 5.5 | scientific, statistical, methodological, adversarial, reproducibility, final audit |
| research-engineer | Claude Sonnet 5 | specialized scientific engineering and scientific polish |
| report-writer | Gemini 3.8 Flash (first draft) → Claude Sonnet 5 or Opus 5.5 (polish) | report drafting pipeline; GPT-6 Sol PI owns final claims |
| fast-worker | GPT-6 Luna | small bounded edits, search, manifest/check, and tests |
| results-analyst | Claude Sonnet 5 + Luna/Gemini support | interpretation after mechanical extraction |

GPT-6 Astra is **not** a routine worker. Use only for exceptional hard contradictions, very difficult math, unresolved
strong reviewer conflict, or exceptionally important final verification.

See `.agent/routing/MODEL_ROUTING.md` for the full table and `.agent/routing/FALLBACKS.md` for fallback sequences.

## Codex subagent policy (exceptional only)

Codex subagents are **not** default workers. Before launching a Codex subagent, answer:

```text
Why can Claude Opus 5.5 / Cursor / Gemini / GPT-6 Luna not reliably perform this task?
```

If another worker can substitute, do not use a Codex subagent. Under Codex 5h capacity pressure, new Codex subagents are
disallowed except when scientifically mandatory and non-substitutable. Record the reason when used.

Routine work must not flow back to GPT-6 Sol PI: broad reconnaissance, implementation, repetitive testing, log/JSON
processing, report first drafts, and mechanical evidence organization belong to Cursor, Gemini, or Luna per thresholds.

## Substantive file (canonical definition)

A repository file counts toward the **5+ substantive file** reconnaissance threshold when understanding its
task-relevant logic, configuration, result, or contract requires **material reading** rather than a path or
existence check.

Exclude generated, vendor, and boilerplate files unless they contain task-relevant primary evidence.

## Default thresholds (with explicit exceptions)

Apply unless the Research PI records a material exception (availability, failure, independence requirement):

- **5+ substantive repository files** for discovery or reconnaissance → Cursor (`repo-operator`) first
- **Gemini-first** when **any** of:
  - mechanically processable input ≥ ~5k tokens
  - 5+ artifacts/reports/logs need comparison
  - 10+ runs/records need classification
  - an evidence packet can be mechanically compressed
  - a report/table/index first draft is needed
- **Multi-file implementation** → Cursor (`repo-operator`) first
- **Report first draft** → Gemini first; Claude review/polish; GPT-6 Sol PI final claims

Do not use ~10k tokens as the only Gemini trigger.

### Gemini-first rule (PI must not bypass)

The PI **must not** directly consume a large mechanical evidence set when it can first be reliably compressed by Gemini.

Before Codex or Claude directly processes 5+ result artifacts, 5+ reports/logs, 10+ runs/records, broad literature
candidate sets, or large mechanically processable text, route through Gemini unless:

1. Gemini is unavailable,
2. scientific interpretation cannot reasonably be separated from extraction,
3. the evidence is too sensitive to compression for the decision, or
4. the PI records an explicit exception in `research_state.md`.

Broad repository scan and routine first drafts should not default to Claude or Codex. When routine broad
reconnaissance must fall back to Codex or Claude, the Research PI must record an **exception and reason** in
`research_state.md` before delegation.

## Gemini broker vs direct filesystem

**Broker mode** (`.ai/workers/gemini.sh --broker`) is the standard path when Antigravity cannot write repository files:
prompt-supplied evidence packet → Gemini print stdout → local wrapper persists artifact + provenance. Exit code 0 alone
is never sufficient.

**Direct filesystem** work remains optional until headless E2E passes in a disposable worktree. When direct write is
unavailable, Gemini returns structured edit proposals / diffs / plans; **Cursor** applies, tests, and commits.

## Evidence-packet chunking

When a prompt-supplied evidence packet is too large for one worker context or approaches the configured/request
limit, do **not** guess a universal provider token ceiling. Instead:

- split deterministically by artifact, run, or logical section
- preserve chunk IDs and provenance
- deduplicate only after chunk summaries
- retain links to primary artifacts

See `.agent/routing/FALLBACKS.md` for worker-specific fallback sequences.

## Capacity pressure and routing diagnostics

Under capacity pressure, reroute **routine** work per the thresholds above.

If Cursor or Gemini usage stays &lt; 5% **and** Codex repeatedly hits the 5h limit, treat routing as misconfigured.

**Never** reroute, skip, or weaken:

- preregistration and metric freeze
- final scientific review and reviewer independence
- primary-artifact verification
- leakage protection
- replication gates

## Prohibited misuse

- artificial quota burning
- unnecessary duplicated work across workers
- Gemini final scientific decisions
- Cursor unsupported scientific conclusions
- quality loss for usage balancing
- Codex PI reading bulk mechanical evidence that Gemini could compress first

## Delegation rules

Workers may delegate to subagents when useful, but the parent worker remains responsible for the result.
Prefer Cursor, Gemini, Claude, or Luna over Codex subagents (see **Codex subagent policy**).

Use the cheapest/fastest role that can reliably complete the task.
Sol should spend expensive context on decomposition, synthesis, conflict resolution, and research decisions — not bulk
editing, broad repository scans, or routine multi-file implementation.

The Research PI may reroute based on availability, context length, failure, or task characteristics, and must record
material rerouting when it affects independence.
