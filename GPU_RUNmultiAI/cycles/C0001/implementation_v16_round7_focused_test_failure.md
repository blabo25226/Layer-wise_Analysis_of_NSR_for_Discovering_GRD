# C0001-T023 full focused test failure (non-scientific)

- Run: 2026-09-23 UTC, single `lansr310` process, `PYTHONPATH=src`, outer `timeout 7200`.
- Command: `conda run --no-capture-output -n lansr310 python -m pytest -q tests/test_gpu_runmultiai_c0001_metric_audit.py`.
- Result: **5 failed, 110 passed in 1672.83 s**. No full audit or new acceptance run was launched.
- Source HEAD during run: `fa1804b32db47a0ac3d57406572fcf582f8740c7`; `src/gpu_runmultiai/manifest.py` remained intentionally dirty from pre-resume work, so this was **not** an immutable accepted source tree.

## Failed tests and observed cause

1. `test_resume_appends_call_log`
2. `test_resume_skips_reexecution_with_spy`
3. `test_resume_replays_guard_side_channel`

These failed with `ResumeIdentityError: accepted closure source hashes ... do not match the recomputed inventory` at `manifest.py:462`. The test closure payload binds the current HEAD while the worktree has an uncommitted `manifest.py` change; the hash mismatch is a correct fail-closed response, not authorization to weaken the gate.

4. `test_accepted_closure_source_hash_hook_is_absent_by_default` expected an output-directory closure record to control `verify_accepted_closure_source_hashes`. Current canonical `accepted_closure_source_hashes` ignores `output_dir` and checks the repository closure path, so the test is stale relative to the canonical-path contract.
5. `test_verify_source_inventory_at_commit_matches_head` correctly detected that dirty `manifest.py` bytes differ from the Git blob at `fa1804b`.

## Required next action

Cursor must review and either commit the intended `manifest.py` closure-record clean-worktree exception with a focused test or reject it with a documented reason. Update only the stale output-directory hook test to the canonical repository closure contract; do not relax accepted-source hash verification. Run the affected tests, then the full focused module once on an immutable committed tree before a fresh acceptance packet. Preserve all historical run trees and frozen v16 bytes.

## T023 resolution (2026-09-24)

**Rejected** the preexisting four-line `verify_clean_worktree()` ignore for
`GPU_RUNmultiAI/cycles/C0001/implementation_closure_record.json`. Frozen v16 round-4
worktree provenance (§B9) allows only `.runtime/` and the protected v9 smoke tree;
a dirty closure record would contradict post-closure pinning of accepted commit +
per-file hashes (prereg §13.2). Round-7 failures were from uncommitted
`manifest.py` bytes vs Git at HEAD, not from closure-record porcelain.

**Applied:** revert that ignore; closure fixtures bind `source_hashes` via
`build_source_inventory()` (runtime recomputation) with `accepted_source_commit` at
HEAD; stale hook test asserts canonical repository path via `monkeypatch` on
`CANONICAL_CLOSURE_RECORD_PATH` without writing the real repo closure file.
