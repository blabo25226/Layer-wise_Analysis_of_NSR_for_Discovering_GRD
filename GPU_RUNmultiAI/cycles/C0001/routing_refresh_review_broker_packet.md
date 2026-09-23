# Broker packet — routing refresh review compression (post-remediation)

Compress the evidence below. Do not invent numbers or SHAs. Separate verified facts from inference.

## Required response format

Respond with exactly: ## Evidence, ## Inference, ## Speculation (markdown headings).

---

# C0001-INFRA-T003 routing diff review evidence (deterministic)

```yaml
generated_at_utc: 2026-09-23T07:07:36Z
integration_base: df39f61f862da3329f29257b573659a19477601c
branch_head: 6ea568c4a8e36cf386e56042341180a9f89290b9
diff_range: df39f61...HEAD plus uncommitted remediation
```

## Changed paths and blob SHA256 (working tree)
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
06401719e793d355f452a28a84d9393048bfcd08fda6182319dfadfecb2f0006 .agent/routing/MODEL_ROUTING.md
0de5c31504e5935f62911556c977cdba957e2abd0fa44722b021fe3b682c22d3 .agent/rules/08-routing-and-delegation.md
096795b098b4a9ba3798e2cd2bcec427538a2e69d2dfc4b4874303d025f71fd1 .agent/rules/09-subagent-policy.md
8f5101476513d087db15ea68baa099db4017e873c2883c2d280dbb9b6f0a39c8 .agent/skills/autonomous-research-cycle/SKILL.md
6a78a16cabbfef3f403dea53e07806db27d37b75678774f39c9d88bacf7b9faf .agent/skills/evidence-compression/SKILL.md
1ae9ec72b61fbb0af5c097c46ab0e0a6a4efbe65b4bc19125b69389b37bfb9ba .agent/skills/literature-evidence/SKILL.md
f9c67fd1066cf2e8acfebce5e8639656f763580aa16edd7840587e5623556ece .ai/workers/README.md
c6fa3652fe8ee662a76c0fc51409452f196b133de9aa7336da03ae6db7e81dce .ai/workers/claude.sh
63f9b4aa852a86f73b4677605d80a750a080932722419e1bab9eaeb1de9226fb .ai/workers/gemini.sh
bb72ea469c33cd3383447b6d3df7b902ea86ad9d39c4d446c3ab1193313d7b13 .codex/README.md
b6f45ef56a88d655137155c781777748609400afeec9509c8818c69dc4bf7733 .codex/rules/ai-workers.rules
8ef939daef237c40291f0bf1e8635be91e28e2ff4f9048d15efd14535992d724 CLAUDE.md
432d500bf2b1eb6b7576830582489ede4371ba51d3c4cf8c83c870fadb98fcae GEMINI.md
dcd26803e037b8a4c04214a883fdf84c4983bcf26301df2bb8ae0a8f10945c69 GPU_RUNmultiAI/RESEARCH_LOOP.md
b873f9d960c03a94c9bd3b59e2fd42bd00d4107e03fcc76b9288ab6779807016 GPU_RUNmultiAI/cycles/C0001/routing_refresh_broker_packet.md
ba68f6c442a1d59117e28ac761a3cb0a1afe1073698e325fa6bd46550a692eb9 GPU_RUNmultiAI/cycles/C0001/routing_refresh_claude_smoke.json.raw
1022b3d75097e96720f079d00a0801f6b9581945240480bf6de5e357d4441f04 GPU_RUNmultiAI/cycles/C0001/routing_refresh_claude_smoke.md
77c66944172a27c151117b7cbd08f6633a98e43c89850d7d15157b069c41f7ee GPU_RUNmultiAI/cycles/C0001/routing_refresh_cursor_smoke.md
f6679b7bc85441ab63bd240833dfff3b22d4b4941125e9faa553c22b249f5664 GPU_RUNmultiAI/cycles/C0001/routing_refresh_gemini_broker_smoke.md
64f3f2dfe2ee7bebc4ca7ab87ba4cec89524cf458e360f9f2683a6439c31432a GPU_RUNmultiAI/cycles/C0001/routing_refresh_gemini_broker_smoke.provenance.json
2578054decf673fb0a57b5dce328826aa2c7f207304bd47dd71b1c72cdabd945 GPU_RUNmultiAI/cycles/C0001/routing_refresh_gemini_fs_e2e.md
0fef8e750b445dd11f0cc8a9c0c22b09c882684caa2a598e4f6087e40e3d5b37 GPU_RUNmultiAI/cycles/C0001/routing_refresh_handoff.md
18a461adb3b9766399468cb115a3417c70342df1444da8bcfbf5724743f6dcaf GPU_RUNmultiAI/cycles/C0001/routing_refresh_review_broker_packet.md
c548572801008f3b4783979c3abf55f4cdbe89d16475694e991bfe342bc83b28 GPU_RUNmultiAI/cycles/C0001/routing_refresh_review_compressed.md
cb5d7c141dd0a3f9b79109f33fe67f096a6b6c8d2a6aeee59d146c8ab4eb5139 GPU_RUNmultiAI/cycles/C0001/routing_refresh_review_compressed.md.provenance.json
0ee20830ac3434fef2931db3b6e3f56fff23575f36f0b120233f849c5ebee2ab GPU_RUNmultiAI/cycles/C0001/routing_refresh_review_evidence.md
37a7fd95cb5fad895bc2e1131214d6a5566f8d18f627602d0ab46abecb9f3b98 GPU_RUNmultiAI/research_state.md
b02dd5767f44abe51563897edfa7c57ef815e9fe3f3d3ff5b15e867e09cde6e3 GPU_RUNmultiAI/task_board.md
86f068a3893daac469d668dbec413c013a2897afc309062ae34d7a5e594acbd5 MANIFEST.sha256
9cd479406ae5b66153529feff16b0fae687a54070d4f27eeec5a80dbdafaab9a tests/test_ai_workers_claude_wrapper.py
173d408f835a2d4652d7782ac9e23b4fd51cce1d4a8d0629d652ec8d82705c61 tests/test_ai_workers_gemini_broker.py

## Focused tests
```text
..............                                                           [100%]
14 passed in 0.59s
```

## Claude independent review
```text
artifact: GPU_RUNmultiAI/cycles/C0001/routing_refresh_claude_review.md
verdict_at_review: BLOCK; remediation commit closes P1 + feasible P2 on routing-refresh branch
```

## Gemini direct FS vs broker
```text
```yaml
task_id: C0001-INFRA-T003-FS-E2E
direct_filesystem_verdict: FAIL
direct_filesystem_steps_passed: 0
broker_mode_verdict: PASS
status: direct_FS_FAIL_broker_PASS
verdict: broker_mode_remains_standard
agy_version: 1.2.9
model_flag: gemini-3.8-flash-high
tested_at_utc: 2026-09-23T06:55:19Z
disposable_worktree: /tmp/gemini-fs-e2e-1l1HQ6
first_failure_step: 1 (list)
```
