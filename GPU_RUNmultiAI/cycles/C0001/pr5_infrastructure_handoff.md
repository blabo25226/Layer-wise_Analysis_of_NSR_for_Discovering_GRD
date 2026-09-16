# C0001 infrastructure task handoff: PR #5 review

## Identity

- task_id: `C0001-INFRA-T001`
- role: `repo-operator`
- worker: Cursor Agent
- base commit: `47d745911825a4b2af27eeb65916b678365fbbcd`
- branch: `ai/C0001/repo-operator/pr5-infra`
- worktree: `/tmp/lansr-multiai-C0001-pr5-infra`

## Objective

Address the six owner-review findings on PR #5 without mixing infrastructure conclusions into the C0001 scientific
result. Make the autonomous research OS resumable, acceptance-tested, and durably pushed.

## Required changes

1. Consolidate `.codex/rules/ai-workers*.rules` so write-mode wrapper calls have one unambiguous `allow` policy.
2. Add a root `AGENTS.md` bootstrap to `.agent/README.md`, the PI role, loop, state, and hypothesis tree.
3. Encode the current Gemini limitation: use prompt-supplied evidence tasks until a fresh filesystem E2E passes; never
   treat process exit code alone as task success.
4. Replace the self-referential state `commit` field with semantically explicit observed/base/remote fields, and
   require reconstruction to reclassify stale `running` tasks.
5. Add deterministic update/verify commands for `MANIFEST.sha256` and document checkpoint/archive use.
6. Separate infrastructure and scientific tracks in the research loop and current state.
7. Add the user-required Git policy: after each accepted integration or stable checkpoint on an active remote research
   branch, non-force push it and verify the remote SHA. Record and retry push failures; never report durability before
   verification.
8. Persist a concise PR #5 response artifact under `GPU_RUNmultiAI/reviews/`.

## Write scope

- `AGENTS.md`
- `.codex/rules/ai-workers.rules`
- `.codex/rules/ai-workers-full-access.rules` (delete if consolidated)
- applicable `.agent/rules/`, `.agent/routing/`, and `.agent/schemas/` files
- `GPU_RUNmultiAI/README.md`
- `GPU_RUNmultiAI/RESEARCH_LOOP.md`
- `GPU_RUNmultiAI/research_state.md`
- `GPU_RUNmultiAI/task_board.md`
- `GPU_RUNmultiAI/reviews/PR5_20260912_infrastructure_response.md`
- `scripts/ops/update_ai_manifest.sh`
- `scripts/ops/verify_ai_manifest.sh`
- `MANIFEST.sha256`

Do not edit C0001 scientific evidence or preregistration files.

## Acceptance

- no conflicting `prompt` rule remains for any wrapper `--write` prefix
- shell scripts pass `bash -n`
- manifest update is deterministic and verification passes
- `git diff --check` passes
- focused text checks cover bootstrap, Gemini fallback, task acceptance, state semantics, track separation, and push
- commit exactly the scoped infrastructure changes with a clear English message

