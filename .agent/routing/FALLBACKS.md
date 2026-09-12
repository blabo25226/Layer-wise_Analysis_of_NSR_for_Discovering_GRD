# Worker fallback routing

Suggested fallback sequence:

- Repo implementation: Cursor Composer -> Claude Sonnet -> Luna (only if small) -> PI diagnosis.
- Scientific engineering: Claude Sonnet -> Cursor Composer -> PI.
- Deep critique/statistics: Claude Opus -> PI -> independent second pass.
- Bulk scan/log/index: Gemini Flash -> Luna -> Cursor Explore/Bash subagent.
- Gemini filesystem write: **limited** until headless E2E passes. Until then use prompt-supplied evidence tasks or route
  persistence to Cursor/Claude/Codex fallback. Never treat Gemini wrapper exit code 0 alone as task success.
- Small mechanical task: Luna -> Gemini Flash -> local direct PI only if delegation overhead exceeds work.
- Report drafting: Claude Sonnet -> Luna -> PI final edit.
- Worker infrastructure failure: retry once -> alternate worker -> record infrastructure issue -> continue.

Do not silently replace an "independent reviewer" with the same worker that implemented the result.
