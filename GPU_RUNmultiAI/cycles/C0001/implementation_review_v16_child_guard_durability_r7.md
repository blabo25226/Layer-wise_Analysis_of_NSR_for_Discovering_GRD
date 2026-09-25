# C0001 v16 child-guard durability: independent review r7

- Reviewer: Claude Opus 5.5, read-only independent source review.
- Reviewed task branch: `ai/C0001/repo-operator/child-guard-durability` at `ba3ef3dd26ba3ae0dd36a2c7165d7476e11a2432`.
- Verdict: **PASS_TO_ONE_FRESH_ACCEPTANCE_ONLY**, conditional on the PI's full focused conda suite passing on this same commit. This is neither implementation closure nor a scientific result.
- The r6 Python 3.10 `Path.is_file()`/`stat()` fail-closed blocker is closed at all three reviewed sites. The earlier empty-output timeout/crash and first/later/count-path uncertainty blockers are also closed for the one-shot acceptance gate.

Remaining closure work identified by the reviewer:

1. An `OSError` after successful side-channel `stat()` during durable JSONL reading could escape as an ordinary failure, or be isolated as `error_isolated=true`, losing guard-attempt accounting.
2. `odeformer_runtime.py` still has an unguarded `is_file()`/`unlink()` cleanup path; a failure there may be counted as an ordinary model failure.
3. `reachability.py` still has an unguarded stale side-channel `unlink()` before the guard.
4. A directory at the side-channel path can pass `stat()` and be interpreted as empty; this is pathological but should be fail-closed before closure.
5. Add a direct test for `_load_child_side_channel_attempts` stat failure and strengthen first-call/real-worker termination fixtures.
6. Operationally, focused tests can write `GPU_RUNmultiAI/.runtime/guard_attempts_side_channel.jsonl`. Do not run another test concurrently; inspect this channel and require it to be missing or empty before a fresh acceptance. Do not silently delete historical evidence.

Carried limitations: content-key deduplication can undercount identical repeated denials; pre-existing rows can obscure a missing-receipt uncertainty even though any denial still fails G4; resume can lose child-denial evidence and is therefore not authorized for acceptance or full audit. The reviewer did not run tests or independently verify the preregistration hash. The PI must do both operational checks before acceptance. No prior r2 output is reusable as final-source acceptance.
