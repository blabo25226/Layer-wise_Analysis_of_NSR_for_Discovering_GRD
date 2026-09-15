# Human Review Queue

Human review is asynchronous. Items here do not stop the loop unless `research_state.md` also sets `hard_stop: true`.

| Priority | Cycle | Item | Why it matters | Blocking? | Status |
|---|---|---|---|---|---|
| none | C0000 | Multi-AI research OS bootstrap | Confirm after installation if desired | no | open |
| normal | C0001 | v10 Q4 amendment raises CPU ceiling from 4 h to 5 h and disk ceiling from 1 GB to 1.2 GB | Independent Claude review found the absolute CPU-only increase non-substantial; useful to inspect asynchronously | no | open |
