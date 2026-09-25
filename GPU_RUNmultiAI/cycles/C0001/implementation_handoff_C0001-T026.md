# C0001-T026 implementation handoff — closure hardening r1

```yaml
task_id: C0001-T026
cycle: C0001
branch: ai/C0001/repo-operator/closure-hardening-r1
base_commit: ba3ef3dd26ba3ae0dd36a2c7165d7476e11a2432
scope: r7 closure-blocking guard durability + r6 acceptance-manifest semantics (no frozen science)
frozen_unchanged:
  - GPU_RUNmultiAI/cycles/C0001/preregistration_draft_v16.md (SHA256 67017f5c…)
  - all acceptance/raw run artifact directories
```

## r7 closure-blocking fixes (1–5)

| # | Fix |
|---|-----|
| 1 | `load_durable_side_channel_attempts`: stat-only presence, regular-file check, `GateAbortError` on read `OSError` and malformed rows |
| 2 | `simplify_tree_subprocess`: `remove_side_channel_file` replaces `is_file()`/`unlink()` |
| 3 | Live ident-fallback pre-guard stale row: `remove_side_channel_file` |
| 4 | Directory at side-channel path: fail-closed via `S_ISREG` before read/unlink |
| 5 | Regressions: read/stat/directory/subprocess-stat fixtures in `tests/test_gpu_runmultiai_c0001_metric_audit.py` |

Shared runtime side channel `GPU_RUNmultiAI/.runtime/guard_attempts_side_channel.jsonl` must be missing or empty before fresh acceptance; tests may write it — do not run concurrent tests against acceptance.

## r6 MINOR 1–4 (code)

| # | Change |
|---|--------|
| 1 | Implementation acceptance `resume_identity` uses `fingerprint_artifacts_expected=False` (null fingerprint paths; no byte resume for acceptance mode) |
| 2 | Manifest records `fail_if_exists_requested`, `cli_args_normalization_excludes`, `fresh_run_log_policy` |
| 3 | Completed acceptance manifest records `access_guard_attempts`, `g4_access_attempt_count`, `g4_pass`, `guard_side_channel_path` |
| 4 | Acceptance `validity_gates` uses `"not_evaluated"` for full-audit-only gates via `evaluate_validity_gates(..., mode="implementation_acceptance")` |

## r6 MINOR 5–9 (documented, not expanded)

| # | Status |
|---|--------|
| 5 | Auxiliary guard counter `0` with uninstalled probe-local guard is not meaningful protection; parent bootstrap + child receipts + G_contract are authoritative |
| 6 | Live ident-fallback: bounded 8-trial observation; synthetic fixture covers fallback path; labels remain honest |
| 7 | Timing calibration observes B0 at scale `0.1` only; artifact now lists `b0_primary_scales_frozen`, observed vs extrapolated scales — recheck all four before bounded smoke |
| 8 | Frozen plan body “unfrozen” text unchanged; external freeze record + SHA256 remain authoritative |
| 9 | F4 pytest citation: PI same-commit focused suite (152/152 target) required at closure; not re-run as full module in this task |

## 91-path source inventory impact

Modified tracked sources under `src/gpu_runmultiai/`: `guard_side_channel.py`, `odeformer_runtime.py`, `reachability.py`, `controls.py`, `manifest.py`, `audit.py`, `timing_calibration.py`, plus focused tests. Recompute and bind per-file SHA256 in `implementation_closure_record.json` at accepted closure; do not edit frozen preregistration for inventory reconciliation.

## Acceptance behavior change assessment

Scientific endpoints unchanged. **Process/manifest semantics changed** for `--implementation-acceptance` (resume identity fingerprint fields, gate serialization, explicit G4 ledger fields, freshness metadata). A fresh acceptance packet on the closure commit is required before treating acceptance artifacts as binding on new source.
