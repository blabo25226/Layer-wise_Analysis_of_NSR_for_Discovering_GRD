# Independent Claude Opus 5.5 review — C0001-T026 r1

- Source: `56cf8efea8c1c247d4f6772c490b00dc76e23ead`, base `ba3ef3dd26ba3ae0dd36a2c7165d7476e11a2432`.
- Implementer: Cursor Agent. Reviewer: Claude Opus 5.5, read-only; `reviewer_diff_assertion=true`.
- Method: direct side-by-side reading of changed source/tests and prior reviews; no shell, Git diff, hash computation, or test execution by reviewer.
- Verdict: **REVISE**. The PI separately observed `159 passed in 2181.06s` for the full focused conda suite on this commit; passing tests do not override the review finding.

## MAJOR — orphan-reconcile read failure can lose guard evidence

`src/gpu_runmultiai/reachability.py` `_reconcile_orphan_child_process_guard_side_channel` still calls `load_guard_attempts` after `stat` and catches only `AuditInvariantError`. A subsequent read `OSError` may escape the live observation, be downgraded to `error_isolated=true`, and leave child-denial rows unaccounted while synthetic reachability still passes. Use the fail-closed durable loader and add direct read-error/directory regressions for this exact path. The new helper closes the simplifier path, not this path.

## Remaining pre-closure issues

1. `audit.py` residual auxiliary check also uses the older loader; read failure globally aborts but is not a typed gate failure, and directory handling depends on earlier ordering. Use the durable loader.
2. Acceptance freshness is recorded rather than enforced; the next packet must use a fresh output directory with `--fail-if-exists`, and manifest fields must show no old log/cache was cleared. Consider making this mandatory in acceptance mode.
3. `manifest.py` leaves `fingerprint_payload_bytes_hash` populated when acceptance writes no fingerprint artifacts; null it or explicitly distinguish the identity field.
4. Add direct propagation/manifest tests and stronger first-call/worker termination regression where feasible. New tests currently touch the shared `.runtime` guard channel; redirect them to `tmp_path` so failing tests cannot leave or delete unrelated evidence.

The reviewer found no scientific endpoint change. Frozen preregistration hash was independently checked by PI as `67017f5c8bac861664fc867b70cf229d43be3d052d266ffd0d575e20e6c12078`.

No implementation closure or fresh acceptance is authorized on r1. Repair in the isolated task worktree; rerun final-source focused tests and independent review. Preserve all historical run artifacts and any shared runtime content.
