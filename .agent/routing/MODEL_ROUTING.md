# Logical role -> preferred model

| Logical role | Preferred worker/model | Primary purpose | Fallback |
|---|---|---|---|
| research-pi | GPT-5.6 Sol | direction, decomposition, integration, final decision | Claude Opus 5 |
| scientific-critic | Claude Opus 5 | adversarial scientific review | GPT-5.6 Sol |
| final-auditor | Claude Opus 5 | cycle promotion audit | GPT-5.6 Sol |
| research-engineer | Claude Sonnet 5 | scientific implementation/design concretization | Cursor Composer 2.5 |
| repo-operator | Cursor Composer 2.5 | multi-file editing, refactor, tests, Git | Claude Sonnet 5 |
| fast-worker | GPT-5.6 Luna | small code/edit/search/test work | Gemini 3.8 Flash |
| research-scout | Gemini 3.8 Flash | broad search, corpus/log scan | GPT-5.6 Luna |
| bulk-worker | Gemini 3.8 Flash | repetitive extraction/transformation/indexing | GPT-5.6 Luna |
| results-analyst | Claude Sonnet 5 + Luna/Gemini support | interpretation after mechanical extraction | GPT-5.6 Sol |
| statistical-reviewer | Claude Opus 5 | design/inference audit | GPT-5.6 Sol |
| report-writer | Claude Sonnet 5 | human-facing report | GPT-5.6 Luna |
| reproducibility-auditor | Claude Opus 5 | leakage/provenance/reproducibility | GPT-5.6 Sol |

Routing is a default, not a scientific fact. The Research PI may reroute based on availability, context length, failure,
or task characteristics, and must record material rerouting when it affects independence.
