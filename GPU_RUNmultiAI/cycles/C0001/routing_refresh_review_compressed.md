# C0001-INFRA-T003 compressed review evidence (mechanical fallback)

```yaml
compression_source: repo_operator_mechanical_fallback
reason: >
  Live `.ai/workers/gemini.sh --broker` rejected agy stdout (exit 70 empty/deny-marker) at 2026-09-23T07:10Z
  after remediation; see routing_refresh_review_broker.stderr.log. Facts below match
  routing_refresh_review_evidence.md; Gemini speculation is not included.
broker_live_verdict: FAIL
evidence_packet: GPU_RUNmultiAI/cycles/C0001/routing_refresh_review_evidence.md
```

## Evidence

- Claude Opus 5.5 independent review (`routing_refresh_claude_review.md`) returned **BLOCK**; P1 items remediated on `ai/C0001/repo-operator/routing-refresh` without touching frozen v16 or the scientific worktree.
- `.ai/workers/gemini.sh` now uses `set -euo pipefail`, fail-closed broker persistence (staging + ordered provenance/artifact copy), deny-marker rejection, structured acceptance for evidence/packet paths, blocks `--broker --write`, and blocks direct `--write` until `GPU_RUNmultiAI/.runtime/gemini_direct_fs_e2e.pass` exists.
- `.codex/rules/ai-workers.rules` denies `gemini.sh --write`; broker allow-list requires `--acceptance headings`.
- `.agent/routing/MODEL_ROUTING.md` PI fallback is **GPT-6 Astra or explicit human PI decision**, not Claude Opus 5.5.
- Direct filesystem E2E (`routing_refresh_gemini_fs_e2e.md`): **FAIL** (0/5 steps; first failure list/auto-denied). **Broker mode** prior smoke remains **PASS** (local persistence path).
- Focused tests: `tests/test_ai_workers_gemini_broker.py` — **14 passed** (includes stale-artifact, mkdir, provenance failure, deny-marker, write-gate cases).

## Inference

- Infrastructure routing refresh is acceptable for PI integration review when paired with updated evidence packet, manifest verification, and honest broker-live limitation above.
- Scientific track `C0001-T023` should resume only after human PI integrates this branch to `20260912_multiAI_research`; repo-operator must not self-integrate to PR #5.

## Speculation

- None (mechanical compression only).
