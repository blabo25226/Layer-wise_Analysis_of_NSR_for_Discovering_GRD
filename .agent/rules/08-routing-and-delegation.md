# Routing and delegation

Use logical roles, not vendor names, as the stable interface.

Default model routing:
- `research-pi` -> GPT-5.6 Sol
- `scientific-critic`, `final-auditor`, deep statistical/method review -> Claude Opus 5
- `research-engineer`, `report-writer` -> Claude Sonnet 5
- `repo-operator` -> Cursor Composer 2.5
- `fast-worker` -> GPT-5.6 Luna
- `research-scout`, `bulk-worker`, `artifact-curator`, large-log work -> Gemini 3.8 Flash

Use the cheapest/fastest role that can reliably complete the task.
Sol should spend its expensive context on decomposition, synthesis, conflict resolution, and research decisions rather
than bulk editing.

Workers may delegate to their own subagents when useful, but the parent worker remains responsible for the result.
