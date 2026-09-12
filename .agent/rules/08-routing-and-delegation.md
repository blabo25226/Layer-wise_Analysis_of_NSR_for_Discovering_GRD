# Routing and delegation

Use logical roles, not vendor names, as the stable interface.

## Capacity-aware routing principle

This is **resource routing**, not quota equalization. Preserve research quality while moving repository
reconnaissance, routine multi-file implementation, bulk extraction, first-draft writing, and mechanical
organization away from Codex/Claude toward Cursor/Gemini when reliable.

Final scientific judgment remains with the Research PI and independent scientific critics.

## Default role routing

| Logical role | Preferred worker/model | Primary responsibility |
|---|---|---|
| research-pi | GPT-5.6 Sol | direction, hypothesis integration, experiment choice, delegation, conflict resolution, design freeze, critical verification, interpretation, verdict, next-cycle decision, continuity |
| repo-operator | Cursor Composer 2.5 | Repository Intelligence + Implementation from Stage 1 onward |
| research-scout, bulk-worker, artifact-curator | Gemini 3.8 Flash | bulk information processing, scout, indexing, long-log work |
| scientific-critic, final-auditor, statistical-reviewer | Claude Opus 5 | scientific, statistical, methodological, adversarial, reproducibility, final audit |
| research-engineer | Claude Sonnet 5 | specialized scientific engineering and scientific polish |
| report-writer | Gemini 3.8 Flash (first draft) → Claude Sonnet 5 (review/polish) | report drafting pipeline; Codex PI owns final claims |
| fast-worker | GPT-5.6 Luna | small bounded edits, search, and tests |
| results-analyst | Claude Sonnet 5 + Luna/Gemini support | interpretation after mechanical extraction |

See `.agent/routing/MODEL_ROUTING.md` for the full table and `.agent/routing/FALLBACKS.md` for fallback sequences.

## Default thresholds (with explicit exceptions)

Apply unless the Research PI records a material exception (availability, failure, independence requirement):

- **5+ substantive repository files** for discovery or reconnaissance → Cursor (`repo-operator`) first
- **~10k+ mechanically processable input tokens** → Gemini (`research-scout` / `bulk-worker`) first
- **Multi-file implementation** → Cursor (`repo-operator`) first
- **Report first draft** → Gemini first; Claude Sonnet review/polish; Codex PI final claims

Broad repository scan and routine first drafts should not default to Claude or Codex.

## Capacity pressure

Under capacity pressure, reroute **routine** work per the thresholds above.

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

## Delegation rules

Workers may delegate to their own subagents when useful, but the parent worker remains responsible for the result.

Use the cheapest/fastest role that can reliably complete the task.
Sol should spend expensive context on decomposition, synthesis, conflict resolution, and research decisions — not bulk
editing, broad repository scans, or routine multi-file implementation.

The Research PI may reroute based on availability, context length, failure, or task characteristics, and must record
material rerouting when it affects independence.
