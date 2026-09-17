# C0001-T019 implementation completion — v16 round 4

Every number in this report is read from the round-4 validation artifacts under
`GPU_RUNmultiAI/cycles/C0001/runs/c0001_metric_identifiability_audit_v16_round4/`
or from the recorded command output below. No value is transcribed from memory.

| Item | Value |
|---|---|
| Worktree | `/tmp/lansr-multiai-C0001-implement-audit` |
| Branch | `ai/C0001/research-engineer/implement-metric-audit` |
| Runtime + tests commits | `f4b4a1a` (round-3 blocker repairs), `ee670f1` (runtime scratch ignore), `acc1982` (worktree check ordering) |
| Validation runtime tip | `acc1982b4212bbeb7e55ace0ded0a879bb06d0f1` |
| Artifacts + report commit | see `git log -1` on this commit |
| Plan SHA256 | `67017f5c8bac861664fc867b70cf229d43be3d052d266ffd0d575e20e6c12078` (unchanged) |
| Validation run | bounded smoke (`--smoke`), **not** confirmatory evidence |
| Python | 3.10.20 (`/home/blabo/miniconda3/envs/lansr310/bin/python`) |

The preregistration files were not edited, `c0001_metric_identifiability_audit_v9_smoke/`
was not touched, and no `implementation_closure_record.json` was created.

## 1. Round-3 blockers and how each was closed

### B1 — symmetric multi-component E1/E2 prefix dialect and identity-fallback detection

`MULTI_COMPONENT_SEPARATOR = ",|,"` and `canonical_system_prefix_raw()` in
`odeformer_runtime.py` normalize writes. `detect_e2_identity_fallback_candidate()`
compares stored `e1_prefix_raw` and `e2_prefix_raw` byte-identically in that
dialect before the Q4 oracle check, so legacy `|` separators cannot masquerade
as identity fallback. Bounded smoke selects one `d=1` and one live `d=3`
multi-component system (`R06_train_d61001_000`); round-4 `pair_results.csv`
contains three rows whose `e1_prefix_raw` includes `,|,` (both B0 rows for R06,
both B1 rows for R06, and both B2 rows for R06).

### B2 — executable F1/F4/F6 evidence (no grep, no false smoke PASS)

`contract_evidence.py` executes all four primary scales for F1 and F4 in-process
(`executed_scales=['0.1', '0.5', '1.0', '2.0']` while `persisted_scales=['0.1']`
for smoke). F6 requires 510/510 B1 rows; with `b1_rows=2` it reports
`passed=false` and `G_impl=false` — no false smoke PASS.

Round-4 `contract_evidence.json`: `g_contract_pass=true`, `f_acceptance_pass=false`
because F6 is honestly false on the bounded population.

### B3 — closure gating for non-smoke and resume

`require_accepted_closure_for_execution()` refuses non-smoke and resume without an
accepted `implementation_closure_record.json`. Pre-closure bounded smoke remains
allowed. Falsifying test: `test_resume_requires_accepted_closure_record`.

### B4 — immediate pre/post resource checks on every artifact write

`ArtifactWriter` in `audit.py` brackets every JSON, CSV, binary, JSONL append,
deviation write, guard side-channel write, and manifest replacement with
`ResourceMonitor.assert_within_limits()`. `CallLogger.execute_or_record` runs
post-check in `finally`. Falsifying tests include
`test_call_logger_checks_resources_around_every_primitive`.

### B5 — complete global-abort lifecycle

All `BaseException` paths except `KeyboardInterrupt`/`SystemExit` route through
`_handle_global_abort` to `status=aborted` with `abort_manifest.json` and
deviation entries. Expanded `_global_abort_error_types()` covers invariant,
runtime, resume/cache, and unexpected failures without swallowing nonzero exits.

### B6 — unconditional zero-attempt guard side-channel artifact

`ensure_guard_side_channel()` creates `guard_attempts_side_channel.jsonl` before
any attempts. Round-4 artifact exists with 0 bytes (zero attempts, file present).
Executable parent/child import-order evidence runs in `contract_evidence.py` guard
bootstrap check.

### B7 — durable D2 pair cache, resume no-reexecution, B2 recovery

Pair cache keys are composite `("B0"|"B1"|"D2", pair_id)` tuples. D2 rows are
appended to `pair_cache.jsonl`. B2 is derived from B0 E1 fields with separate
`("B2", pair_id)` cache entries. Tests:
`test_resume_skips_reexecution_with_spy`, `test_resume_replays_guard_side_channel`.

### B8 — independent F7 oracle; UNS/SUP gate coverage; production identity reachability

`compute_b2_expected_outcome()` in `outcomes.py` provides an independent F7
oracle from B0 E1 fields. `REACH-IDENT-FALLBACK-1` uses production
`detect_e2_identity_fallback_candidate()`. UNS/SUP reachability fixtures evaluate
every frozen gate (`failed_gates=[]` in round-4 `reachability_evidence.json`).

### B9 — clean tracked worktree provenance

`verify_clean_worktree()` runs before output directory creation, ignores only
`GPU_RUNmultiAI/.runtime/` (frozen scratch) and the protected v9 smoke.
Round-4 manifest `worktree_provenance`:

```json
{"clean": true, "ignored_untracked": [
  "GPU_RUNmultiAI/.runtime/",
  "GPU_RUNmultiAI/cycles/C0001/runs/c0001_metric_identifiability_audit_v9_smoke/"
]}
```

### B10 — actual produced artifact schema validation

`validate_output_artifact_schemas(output_dir)` runs on the real output tree before
finalize. `test_round3_artifact_schemas_present_in_smoke` fails on missing files.

## 2. Source inventory

89 sorted unique paths under `src/gpu_runmultiai/*.py`, entry scripts, and frozen
dependencies. Manifest `source_hashes` recomputes identically to
`source_inventory.json` and to live Git blob SHA256 (0 mismatches on verification).

## 3. Commands and results

```bash
/home/blabo/miniconda3/envs/lansr310/bin/python -m compileall -q src scripts tests
sha256sum GPU_RUNmultiAI/cycles/C0001/preregistration_draft_v16.md
git diff --check
export LANSR_TED_TIMEOUT_SEC=10 LANSR_SYMPY_TIMEOUT_SEC=10 LANSR_SYMPY_MAX_NODES=40
PYTHONPATH=src /home/blabo/miniconda3/envs/lansr310/bin/python -m pytest -q \
  tests/test_gpu_runmultiai_c0001_metric_audit.py
PYTHONPATH=src /home/blabo/miniconda3/envs/lansr310/bin/python \
  scripts/phases/gpu_runmultiai_c0001_metric_audit.py \
  --audit-id c0001_metric_identifiability_audit_v16 \
  --output-dir GPU_RUNmultiAI/cycles/C0001/runs/c0001_metric_identifiability_audit_v16_round4 \
  --audit-data-seed 61001 --audit-trajectory-seed 61002 --audit-rewrite-seed 61003 \
  --audit-negative-seed 61004 --audit-cas-subset-seed 61005 \
  --allow-cpu --oracle-timeout-sec 30.0 --q4-timeout-sec 10.0 \
  --simplifier-subprocess-timeout-sec 5.0 --cas-timeout-sec 60.0 \
  --smoke --fail-if-exists
```

| Check | Result |
|---|---|
| `compileall src scripts tests` | PASS |
| Plan SHA256 | `67017f5c...6c12078`, matches frozen value |
| `git diff --check` | clean (pre-commit) |
| Focused pytest | **101 passed** in ~24.5 min after dialect fix (first full pass: 100 passed, 1 failed `test_multi_component_identity_fallback_uses_canonical_prefix_dialect`; repaired in `f4b4a1a`) |
| Audit CLI | exit 0 |
| Manifest `status` | `completed` |
| Manifest `commit` == runtime tip | `acc1982...` == `acc1982...` PASS |
| `source_hashes` recompute | identical to manifest and `source_inventory.json` (89 paths, 0 blob mismatches) |
| Remote push (runtime) | **BLOCKED** by environment approval gate (local ahead 3 commits at report time) |

## 4. Round-4 artifact values

| Field | Value |
|---|---|
| `audit_id` | `c0001_metric_identifiability_audit_v16` |
| `corpus_hash` | `253dbceb63af0a742c01d16afdecb24a872fdb867f2e4d80c6b833ec87f922dc` |
| `confirmatory_calls` / `descriptive_calls` / `grand_calls` | 57 / 8 / 65 |
| Ceilings (confirmatory / grand / descriptive) | 27637 / 30277 / 2640 |
| `primitive_completion_rate` | 0.0020624525093172197 |
| `elapsed_sec` / `dir_bytes` | 81.42 s / 677,664 bytes |
| `access_guard_attempts` | 0 (`G4` PASS) |
| `primary_decision` | `H0001 undecidable` |
| Deviations | 1 (bounded smoke run) |

Validity gates:

| PASS | FAIL |
|---|---|
| `G_corpus`, `G_eligibility`, `G_stratum`, `G0`, `G4`, `G1`, `G_grand`, `G_contract`, `G_q4ref`, `G_inc` | `G_impl`, `G_n1`, `G_b1`, `G_b4`, `G_ctrl_cov`, `G_ctrl_fp`, `G_ctrl_lin`, `G_term` |

`G_impl=false` is expected: F6 requires 510/510 B1 rows and smoke has 2.

Terminal partition from `pair_results.csv` (7 rows, zero `unknown`):

| condition | terminal | count |
|---|---|---:|
| B0 | `preserved` | 2 |
| B1 | `control_pass` | 2 |
| B2 | `preserved` | 2 |
| D2 | `descriptive_recorded` | 1 |

Live `d=3` multi-component coverage: `R06_train_d61001_000` executed through
B0, B1, B2 with `,|,`-separated three-component prefixes in E0/E1/E2 raw fields.

Other artifacts: `b3_results.json` 2 rows `diagnostic_complete`;
`b4_results.json` 2 rows `sanity_pass`; `negative_controls.json` 2 rows with
non-null `component_id`; `q4_reference_controls.json` 7/7 `fixture_pass`;
`reachability_evidence.json` 10/10 `passed` (UNS/SUP `failed_gates=[]`);
`guard_attempts_side_channel.jsonl` present, 0 bytes;
`condition_summary.json` `primary_partition_counts`
`{'construction_incomplete': 0, 'execution_failure': 0, 'semantic_drift': 0, 'structural_false_negative': 0, 'preserved': 2, 'unknown': 0}`;
`fingerprint_payload.json` byte-identical to `fingerprint_bytes.bin`;
`pair_cache.jsonl` 7 lines (B0, B1, B2, D2 composite keys).

Contract evidence F-rows:

| check | passed | details (from artifact) |
|---|---|---|
| F1 | true | executed all 4 primary scales |
| F2 | true | ok |
| F4 | true | executed all 4 primary scales |
| F5 | true | b1_rows=2, production identity scaler |
| F6 | **false** | b1_rows=2; requires 510/510 |
| F7 | true | independent B0-derived oracle, b2_rows=2 |
| F8 | true | ok |

## 5. Mechanical verification summary

| Check | Result |
|---|---|
| Manifest commit == `git rev-parse HEAD` | PASS |
| 89 source hashes == inventory == Git blobs | PASS |
| `g_contract` all 7 checks | PASS |
| F6 does not false-pass smoke (`G_impl=false`) | PASS (honest fail) |
| Guard side-channel file exists (zero attempts) | PASS |
| Worktree provenance clean (v9 smoke + `.runtime` ignored) | PASS |
| Terminal vocabulary `unknown` count | 0 |
| Reachability UNS/SUP all gates evaluated | PASS |
| No `abort_manifest.json` on completed run | PASS |
| Protected v9 smoke untouched | PASS |

## 6. Failures and retries

- **Validation run failures before success:** two aborted starts left partial
  `c0001_metric_identifiability_audit_v16_round4/` trees because
  `verify_clean_worktree()` originally ran after `output_dir.mkdir()` and because
  `GPU_RUNmultiAI/.runtime/` was not yet ignored. Fixed in `ee670f1` and
  `acc1982`; partial trees removed; final run exit 0.
- **Pytest:** first full `lansr310` pass 100 passed / 1 failed (dialect byte
  compare); four resume tests failed on closure timing (fixed in test helpers).
  Final: 101 passed.
- **Push:** `git push -u origin HEAD` rejected by environment Auto-review gate;
  branch remains local-only ahead of remote.
- **Retries on final validation:** none after `acc1982`; single successful smoke.

## 7. Tests added or updated this round

Falsifying / contract tests added or repaired in
`tests/test_gpu_runmultiai_c0001_metric_audit.py`:

- `test_canonical_prefix_normalizes_pipe_and_comma_dialects`
- `test_multi_component_identity_fallback_uses_canonical_prefix_dialect`
- `test_guard_side_channel_exists_even_with_zero_attempts`
- `test_resume_requires_accepted_closure_record`
- `test_f6_smoke_population_does_not_pass_acceptance`
- Resume tests (`test_resume_appends_call_log`,
  `test_resume_skips_reexecution_with_spy`, `test_resume_replays_guard_side_channel`)
  updated for post-first-run closure record timing

## 8. Not executed / open

- No full confirmatory 27,637-call audit.
- No `implementation_closure_record.json`; resume/non-smoke remain blocked in production.
- Remote parity unverified (push blocked).
- Population gates (`G_n1`, `G_b1`, `G_b4`, `G_ctrl_*`, `G_term`, `G_impl`) remain
  FAIL on bounded smoke by design.
- Historical round-2 and round-3 directories remain frozen negative evidence.
