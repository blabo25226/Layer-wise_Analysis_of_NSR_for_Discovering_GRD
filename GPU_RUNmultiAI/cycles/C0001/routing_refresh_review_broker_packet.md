# Broker packet — routing refresh review compression

Compress the evidence below. Do not invent numbers or SHAs.

## Required response format

Respond with exactly: ## Evidence, ## Inference, ## Speculation (markdown headings).

---

# C0001-INFRA-T003 routing diff review evidence (deterministic)

```yaml
generated_at_utc: 2026-09-23T06:56:12Z
integration_base: df39f61f862da3329f29257b573659a19477601c
branch_head_before_commit: d668e2eb9d99c535b2e0344ad62a88573f531955
diff_range: df39f61...HEAD
```

## Changed paths and blob SHA256 (pre-commit tree)
99c80ce43bad30828bd5b34426cd391922eebe86ce25e182388e88c56559c0ef .agent/agents/bulk-worker.md
ddd71a5d98952860865ef434705791bb9402fc3d7ae4eb3b317a3ed64ca9fa5b .agent/agents/continuity-controller.md
da076faca1b4303dce42329068856d75dfdd26a46bb61917045f0271b8c04403 .agent/agents/fast-worker.md
f44770e1342acf4427375e95419383b5efbc262a84626f0bd49a007410f4f73c .agent/agents/final-auditor.md
08c9b3580046c8e1611913487cba47af4798de25a1b3a4ac7178c6ffe98dcf38 .agent/agents/hypothesis-scientist.md
f9198d87f17728b6fb2334d1646127d145654562610e35083a19ba978c0cb381 .agent/agents/reproducibility-auditor.md
ebb16896acd058bc4698e293ab874f5b4f5a8462d38c94466eca34887ae80ec5 .agent/agents/research-pi.md
94227bbe7eb7d4257d12cf3c5b80ec7ebd41f6315211bcb282853a72039a9447 .agent/agents/research-scout.md
1af050ca8bd89774f3abd418dd8ded64b76e5f1bcf9feaee4702ba2f78607212 .agent/agents/scientific-critic.md
66060c90f350b0c2a98879c287191ddbcf248d5989d1d9d8037b1e601a74a45c .agent/agents/statistical-reviewer.md
c662ec74fdf4fab609ba622770acbdf23db93b9c25ca3b0fd8f9e5abf78cec96 .agent/routing/FALLBACKS.md
5c15d1e1d10747a4685ecaf1a15e9ac05dc113a24e74cbbfe6e3b5a2d26f2bd9 .agent/routing/MODEL_ROUTING.md
c13723031266d43eaaaeab185216a05a5eadaca5ada5c7e8cebffc10bfbf3aee .agent/rules/08-routing-and-delegation.md
096795b098b4a9ba3798e2cd2bcec427538a2e69d2dfc4b4874303d025f71fd1 .agent/rules/09-subagent-policy.md
8f5101476513d087db15ea68baa099db4017e873c2883c2d280dbb9b6f0a39c8 .agent/skills/autonomous-research-cycle/SKILL.md
6a78a16cabbfef3f403dea53e07806db27d37b75678774f39c9d88bacf7b9faf .agent/skills/evidence-compression/SKILL.md
7549ec518929bd1c9c2f83d2e12ec362298579bfc3300070b10695bb6542e255 .ai/workers/README.md
4a223a2fc21510573f653da6e00ff96127ef2548763e01ae5100dfc8939a1e54 .ai/workers/gemini.sh
bb72ea469c33cd3383447b6d3df7b902ea86ad9d39c4d446c3ab1193313d7b13 .codex/README.md
3d35bcba7b5f5e97fef25b8b452414a1f7b7296e9d10db1a6f3df4f0ec4f4f1c .codex/rules/ai-workers.rules
8ef939daef237c40291f0bf1e8635be91e28e2ff4f9048d15efd14535992d724 CLAUDE.md
432d500bf2b1eb6b7576830582489ede4371ba51d3c4cf8c83c870fadb98fcae GEMINI.md
dcd26803e037b8a4c04214a883fdf84c4983bcf26301df2bb8ae0a8f10945c69 GPU_RUNmultiAI/RESEARCH_LOOP.md
b873f9d960c03a94c9bd3b59e2fd42bd00d4107e03fcc76b9288ab6779807016 GPU_RUNmultiAI/cycles/C0001/routing_refresh_broker_packet.md
1829b99dfb62888de7c71e78b237d8380670e3490f46fa75e11b4aa45f38f6ef GPU_RUNmultiAI/cycles/C0001/routing_refresh_claude_smoke.md
28c226f71520cc3f43a45d9ec7df3f97764d5c55ec646c9d2a30290bf81170c8 GPU_RUNmultiAI/cycles/C0001/routing_refresh_cursor_smoke.md
f6679b7bc85441ab63bd240833dfff3b22d4b4941125e9faa553c22b249f5664 GPU_RUNmultiAI/cycles/C0001/routing_refresh_gemini_broker_smoke.md
64f3f2dfe2ee7bebc4ca7ab87ba4cec89524cf458e360f9f2683a6439c31432a GPU_RUNmultiAI/cycles/C0001/routing_refresh_gemini_broker_smoke.provenance.json
a92bfe22621e9589f130a7ad84f048303921f4365f4eac9c8f3b72ffc164aec2 GPU_RUNmultiAI/cycles/C0001/routing_refresh_gemini_fs_e2e.md
b8529811587ebfb1c26f88d24a18e2c7f4f12780e56f93b22089036327acc4d5 GPU_RUNmultiAI/cycles/C0001/routing_refresh_handoff.md
b86bfe558d8a0467066be421f6044ce2a0f2c11e98061129ed168d473d0b1f5e GPU_RUNmultiAI/research_state.md
b582b606543001b838eb68736f493bb4be98a8ebfd4c77908e08165c20b72b91 GPU_RUNmultiAI/task_board.md
9e0ec1a4670de440192d27cb18d83c447fb501e8c9c5fa96bcea3017a783789d MANIFEST.sha256
402e2a08417ae2fdb4988efd5c074d497441495d646bfa53f76a1c8d0f72e77b tests/test_ai_workers_gemini_broker.py

## Focused tests
```text
..........                                                               [100%]
10 passed in 0.32s
```

## Claude smoke (wrapper default model)
```text
worker=claude mode=read output_format=json model=claude-opus-5-5
worker=claude exit_code=0
result ROUTING_MODEL_55_OK
canonicalModel claude-opus-5-5
```

## Gemini FS E2E five-step
```text
disposable_worktree=/tmp/gemini-fs-e2e-1l1HQ6
agy_version=1.2.9
started_utc=2026-09-23T06:55:19Z
--- step 1: list ---
exit_code=0
jetski: no output produced — a tool required the "command" permission that headless mode cannot prompt for, so it was auto-denied. Add an allow-rule under permissions.allow in settings.json (e.g. command(<target>)). Alternatively, re-run with --dangerously-skip-permissions to auto-approve all tools.
FIRST_FAILURE_STEP=1 (list)
```
