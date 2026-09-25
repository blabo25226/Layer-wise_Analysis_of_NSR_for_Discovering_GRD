# C0001 v16 final-source acceptance r4 — PI pre-run gate

Decision at 2026-09-24 15:38 UTC: authorize **one** fresh, non-scientific 510-B1 / 4,080-call implementation acceptance packet, and nothing beyond it.

- Immutable task source: `ai/C0001/repo-operator/child-guard-durability` at `ba3ef3dd26ba3ae0dd36a2c7165d7476e11a2432`, remote SHA verified.
- Frozen v16 preregistration SHA256: `67017f5c8bac861664fc867b70cf229d43be3d052d266ffd0d575e20e6c12078` in the execution worktree.
- Independent Claude Opus 5.5 r7: `PASS_TO_ONE_FRESH_ACCEPTANCE_ONLY`, with closure-only caveats in `implementation_review_v16_child_guard_durability_r7.md`.
- PI full focused Python 3.10 suite at the same commit: `152 passed in 2219.61s`, exit 0. No overlapping test/audit process remained at gate time.
- Shared `GPU_RUNmultiAI/.runtime/guard_attempts_side_channel.jsonl` was absent after the test. Other `.runtime` test fixtures were preserved.
- Output `GPU_RUNmultiAI/cycles/C0001/runs/c0001_metric_identifiability_audit_v16_round7_acceptance_r4/` was absent in all inspected active C0001 worktrees and integration. Earlier r2 and other outputs must remain untouched.
- Storage: execution worktree `/tmp` had about 28 GiB free; persistent root had about 17 GiB free. The frozen output ceiling is 1,200,000,000 bytes and wall ceiling 18,000 seconds.

Run only with the frozen seeds/timeouts/environment, `--allow-cpu --implementation-acceptance --fail-if-exists`, no `--resume`, and the r4 output directory above. Exit code alone is not a PASS: mechanically verify primary artifacts, count and uniqueness, guard/Q4/reachability evidence, provenance, and lifecycle; then obtain independent review. This gate does not authorize the 27,637-call confirmatory audit, source closure, or any scientific claim.
