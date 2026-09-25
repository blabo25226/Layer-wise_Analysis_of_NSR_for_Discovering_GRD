# C0001-T026 — post-r6 implementation closure hardening

```yaml
task_id: C0001-T026
cycle: C0001
role: repo-operator
preferred_worker: Cursor Agent
objective: Repair closure-blocking evidence durability and acceptance-manifest semantics without changing frozen scientific design.
branch: ai/C0001/repo-operator/closure-hardening-r1
worktree: /tmp/lansr-multiai-C0001-closure-hardening-r1
base_commit: ba3ef3dd26ba3ae0dd36a2c7165d7476e11a2432
write_scope: [C0001 runtime and focused tests, task-specific handoff]
read_scope: [frozen v16 plan, independent r7 source review, independent r6 packet review, r6 PI gate]
implementer_identity: Cursor Agent
independent_reviewer_identity: Claude Opus 5.5
reviewer_diff_assertion: true
status: assigned
retry_count: 0
```

Authoritative review findings are in `GPU_RUNmultiAI/cycles/C0001/implementation_review_v16_child_guard_durability_r7.md`, `implementation_review_v16_round7_acceptance_r6.md`, and `implementation_acceptance_r6_pi_gate.md` in the integration worktree. The task worktree starts at reviewed source `ba3ef3d`; read those three review files via the absolute integration path if not present in the task branch. The v16 preregistration bytes and SHA256 `67017f5c8bac861664fc867b70cf229d43be3d052d266ffd0d575e20e6c12078` are frozen.

Fix r7 closure-blocking issues 1–5: side-channel read OSError after stat, unguarded `is_file()`/`unlink()` cleanup, pre-guard stale-row unlink, directory-as-side-channel ambiguity, and missing direct/stat/termination regression fixtures. Fix or make explicit r6 review MINOR 1–4: acceptance fingerprint payload/bytes identity semantics, manifest CLI freshness/`--fail-if-exists` and log-clearing behavior, G4 guard-attempt evidence, and not-evaluated full-audit gates as null/not-evaluated. Document MINOR 5–9 accurately. Add focused regressions and run them in the pinned `lansr310` environment where feasible. Recheck timing calibration for all B0 scales before proposing bounded smoke.

Do not run acceptance, bounded smoke, or the full 27,637-call scientific audit in this task. Do not modify or resume r6, interrupted r4, failed-before-output r5, r2, or any prior output. Do not edit frozen preregistration, test endpoint selection, or metric definitions. Preserve abort manifests and fail-closed guard evidence on all paths. If a fix would alter frozen science or requires a new compute ceiling, stop that edit and report the conflict to PI.

Commit cohesive implementation and test changes on this branch. Push non-force and verify remote SHA. Return a completion record with commit SHA, changed files, exact tests/commands/results, remaining risks, acceptance-behavior-change assessment, and the required 91-path source inventory impact. PI will inspect diff/tests and route the closure diff to independent Claude Opus before deciding on a new-suffix acceptance; no worker may self-authorize that gate.
