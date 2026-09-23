# C0001-INFRA-T003 — AI routing refresh and Gemini broker

```yaml
task_id: C0001-INFRA-T003
cycle: C0001
track: infrastructure
role: repo-operator / implementation
preferred_worker: Cursor Agent
objective: >
  Implement the human attachment's permanent multi-AI routing update, a usable
  Gemini broker, and honest provider smokes while preserving the scientific
  C0001 worktree and all frozen research guardrails.
authoritative_inputs:
  - /home/blabo/.codex/attachments/299e711c-8381-4eb6-bf80-4ba955cd02b5/貼り付けたテキスト.txt
  - AGENTS.md
  - .agent/README.md
  - .agent/rules/
  - .agent/routing/
  - GPU_RUNmultiAI/RESEARCH_LOOP.md
  - GPU_RUNmultiAI/research_state.md
  - GPU_RUNmultiAI/task_board.md
  - .ai/workers/
branch: ai/C0001/repo-operator/routing-refresh
worktree: /tmp/lansr-multiai-C0001-routing-refresh
write_scope:
  - .agent/
  - .codex/
  - .claude/
  - .cursor/
  - .gemini/
  - .agents/
  - CLAUDE.md
  - GEMINI.md
  - .ai/workers/
  - GPU_RUNmultiAI/RESEARCH_LOOP.md
  - GPU_RUNmultiAI/research_state.md
  - GPU_RUNmultiAI/task_board.md
  - GPU_RUNmultiAI/cycles/C0001/routing_refresh_*.md
  - tests/ for focused worker-wrapper tests
  - MANIFEST.sha256
frozen_constraints:
  - keep C0001 v16 preregistration SHA256 67017f5c8bac861664fc867b70cf229d43be3d052d266ffd0d575e20e6c12078
  - preserve scientific guardrails and independent review
  - root PR #5 branch is long-running; merge readiness is not the objective
  - do not edit the scientific implementation worktree or its dirty files
expected_outputs:
  - canonical GPT-6 Sol Medium PI, GPT-6 Luna small work, Claude Opus 5.5 critics, Cursor repo work, Gemini 3.8 Flash broker-first routing
  - Codex subagent exceptional-only rule and Gemini-first thresholds/exceptions
  - broker-capable gemini.sh with deterministic packet, stdout acceptance, local persistence, and provenance
  - Antigravity version/help/model availability/direct filesystem E2E evidence
  - Cursor and Claude small smokes, Gemini broker smoke, wrapper tests
  - state/task-board pause of C0001 scientific T023 and exact resumption route
  - refreshed MANIFEST.sha256 and verified push
acceptance_tests:
  - CLI options and model selection verified from installed help; no guessed Gemini model setting
  - broker packet to Gemini to structured stdout to persisted artifact PASS
  - direct filesystem E2E verdict FAIL until five-step PASS; broker mode verdict PASS separately
  - Claude Opus 5.5 actual read-only CLI smoke
  - Cursor reconnaissance plus implementation smoke
  - no old preferred model names in active configuration (historical artifacts excluded)
  - `bash scripts/ops/verify_ai_manifest.sh` PASS
  - focused tests, bash syntax checks, git diff --check PASS
  - non-force push and local/tracking/remote SHA equality
forbidden_changes:
  - GPU_RUNmultiAI/cycles/C0001/preregistration_draft_v16.md
  - scientific runtime, results, experiments, and historical artifacts
  - /tmp/lansr-multiai-C0001-implement-audit contents
  - PR #4 scientific results
compute_budget: small infrastructure smokes only
status: pending_independent_review_and_integration
retry_count: 0
fallback: Claude Sonnet 5 implementation, then PI scoped resolution
implementer_identity: Cursor Agent
independent_reviewer_identity: Claude Opus 5.5 or closest available Claude model
reviewer_diff_assertion: true
```

## Specific implementation guidance

Read the entire attachment. Update each active canonical role/routing/skill and
thin adapter named there. Do not rewrite old model names in historical records.
Keep Research PI decisions with GPT-6 Sol Medium; humans control the UI model
setting. The 5,000-token / five-artifact / ten-record / draft-first Gemini
triggers are operational defaults, with a recorded exception when bypassed.
Codex subagents require a documented non-substitutability reason.

For Gemini, inspect the installed `agy` version/help/configuration before
changing the model. A direct filesystem test belongs in a disposable isolated
worktree and must be judged by files actually written/read. If direct access
fails, retain broker mode as the standard path. The broker must accept an input
packet, capture real stdout, reject empty/invalid output despite exit 0, and
write output plus provenance using local shell code. Never include credentials
in logs. Structured edit proposals go to Cursor for application and tests.

The scientific worktree `/tmp/lansr-multiai-C0001-implement-audit` is at
`9e422dcbb856e9c69342d4ff274654ccafab28ac` with uncommitted edits in
`manifest.py`, `reachability.py`, and the focused test file, plus untracked
attempt artifacts. No research worker process was running at handoff. Record
scientific task T023 as paused by the human routing override, with the exact
dirty paths and a resume action after infrastructure integration. This pause
is not a scientific hard stop.

Commit cohesive pieces, push this task branch, and return changed files,
test/smoke results, CLI model availability, direct-filesystem outcome,
unresolved limitations, and remote SHA. Do not integrate into PR #5 yourself.
