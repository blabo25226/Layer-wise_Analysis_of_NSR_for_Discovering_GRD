# C0001-T018 implementation completion — v16 round 3

Every number in this report is read from the round-3 validation artifacts under
`GPU_RUNmultiAI/cycles/C0001/runs/c0001_metric_identifiability_audit_v16_round3/`
or from the recorded command output below. No value is transcribed from memory.

| Item | Value |
|---|---|
| Worktree | `/tmp/lansr-multiai-C0001-implement-audit` |
| Branch | `ai/C0001/research-engineer/implement-metric-audit` |
| Runtime + tests commit | `1bd083def321f99b6e99c4fc558beb197f6626ec` |
| Artifacts + report commit | `29b343d4930e25c0f8f57a4e47dda9df239d210e` (this SHA is filled in by the immediately following commit) |
| Plan SHA256 | `67017f5c8bac861664fc867b70cf229d43be3d052d266ffd0d575e20e6c12078` (unchanged) |
| Validation run | bounded smoke, **not** confirmatory evidence |
| Python | 3.10.20 (`/home/blabo/miniconda3/envs/lansr310/bin/python`) |

The preregistration files were not edited, `c0001_metric_identifiability_audit_v9_smoke/`
was not touched, and no `implementation_closure_record.json` was created.

## 1. Round-2 blockers and how each was closed

### B1 — production `Scaler.rescale_function` with identity parameters

`IdentityScaler` is deleted from `src/gpu_runmultiai/odeformer_runtime.py`.
`build_identity_scaler(dimension)` now configures the production
`odeformer.model.utils_wrapper.Scaler` with `time_range=[0, 1]`, `t` sampled on
`[0, 1]`, and a constant unit trajectory, which yields `a_t = 1/(1-0) = 1`,
`b_t = 0`, and a unit feature scale. The measured asserts are
`{'time_scale': 1, 'time_shift': 0, 'a_t': 1.0, 'b_t': 0.0, 'rescale_features': True, 'scale': [1.0, 1.0, 1.0]}`
for `dimension=3`; any deviation raises `ScalerGateError`. The production
configuration is untouched: `build_production_scaler(0.1, 3)` still measures
`{'time_scale': 9, 'time_shift': 1, 'a_t': 0.9, 'b_t': 1.0, 'rescale_features': True, 'scale': [10.0, 10.0, 10.0]}`,
so `G0` is unaffected.

`rescale_system` now
1. verifies that the bound callable is
   `odeformer.model.utils_wrapper.Scaler.rescale_function` and raises
   `ScalerGateError` otherwise,
2. detects **both** §5.2 early returns with `rescaled is tree`, and
3. returns a call proof and stores it in a module-level hook
   (`last_rescale_call_proof()`) for tests.

Round-3 B1 proof read from `pair_cache.jsonl`:

```json
{"a_t": 1.0, "b_t": 0.0, "input_node_count": 1,
 "rescale_callable_module": "odeformer.model.utils_wrapper",
 "rescale_callable_qualname": "Scaler.rescale_function",
 "rescale_incomplete": false, "returned_input_tree": false, "scale": [1.0]}
```

The bypass is gone in the artifact itself: B1 `e1_infix` is no longer identical
to `e0_infix`, because the production rescale really ran with identity
parameters.

```text
e0: 1.0 * (1.0)**-1 * (0.04598 + 2.437 * x_0 / 1.0 * 1/(0.4416 + x_0 / 1.0) + -1 * 0.8487 * x_0 / 1.0)
e1: 1.0 * 1.0 * 1.0 * (1.0)**-1 * (0.04598 + 2.437 * 1.0 * x_0 / 1.0 * 1/(0.4416 + 1.0 * x_0 / 1.0) + -1 * 0.8487 * 1.0 * x_0 / 1.0)
```

Both round-3 B1 rows are `control_pass` and both remain oracle-equivalent to
truth at E1, which is exactly what F5 requires.

### G_contract / G_impl — executable evidence instead of literals

New module `src/gpu_runmultiai/contract_evidence.py` runs all seven §10.1
checks and all seven §16 F-requirements in process. `audit.py` contains no
literal acceptance value; it consumes
`evaluate_g_contract_checks(...)` and `evaluate_f_acceptance(...)` and persists
every row to `contract_evidence.json` with `check_key`, `requirement`, `passed`,
and `details`. A check that cannot execute is reported `passed=False` with the
exception in `details`; it is never silently skipped.

Round-3 `contract_evidence.json` (`g_contract_pass=true`, `f_acceptance_pass=true`):

| check | passed | what actually ran |
|---|---|---|
| `q4_fixtures` | true | 7/7 fixtures, exact emitted prefixes for Q4-NARY-3 / Q4-R4a, `0.0460` and `0.3333` tokens, Rational non-leak, and two `Q4ContractError` paths |
| `guard_bootstrap` | true | singleton identity, re-install rejection, deny matcher, real `PermissionError`, attempt ledger, child side-channel merge (probed under a temporary root) |
| `source_inventory` | true | 89 sorted unique paths, all `src/gpu_runmultiai/*.py` present, `guard_bootstrap.py` and `third_party/odeformer/parsers.py` present, every hash recomputed |
| `artifact_schemas` | true | 11 §12.8 artifact round-trips written and re-read |
| `jsonl_recovery` | true | partial-suffix truncation, malformed-line abort, duplicate-key abort |
| `resume_mismatch` | true | five identity mismatches abort; missing / non-byte-identical / dict-mismatched fingerprints abort |
| `abort_deviation_lifecycle` | true | abort manifest field set, six-field deviation entry, both finalisation lines |

| requirement | passed | evidence |
|---|---|---|
| F1 | true | `rows=2 scales=['0.1']`; exact-rational reciprocal prefix `mul,0.1,pow,0.9,-1`; E1 analytically and numerically equivalent to truth |
| F2 | true | `pow2,div,mul,10.0,x_0,10.0` keeps binary arity through root/`div`/`mul`, and the Q4 emission re-parses |
| F4 | true | round-trip acceptance test exists with both equivalence assertions, and every B0 scale group is E1-equivalent |
| F5 | true | `b1_rows=2`, production callable, `a_t=1`, `b_t=0`, `scale=[1.0]`, no identity return |
| F6 | true | `b1_rows=2 control_pass=2`, only `control_pass`/`control_failure` terminals |
| F7 | true | `b2_rows=2`; no E2 field leaked; terminal reproduced by re-running the E1-only classifier |
| F8 | true | `pipeline.split_components is gpu_run4.formulas.split_components`; `|` split verified on prefix and infix |

### B2 — five-outcome partition from E1-only fields

`b2_inherited_e1_fields()` copies only the frozen `B2_INHERITED_E1_FIELDS`
(construction, Q4, rescale, E1 oracle, quantization). `B2_FORBIDDEN_INHERITED_FIELDS`
is asserted at both the producer and the consumer, so an E2 flag can never reach
a B2 row. `_classify_five_e1_only()` decides the terminal from E1 fields alone.
Round-3 B2 terminals: `['preserved']`, zero `unknown`.

### D2 — descriptive terminals

`classify_outcome` maps the D2 five-outcome result through
`descriptive_terminal()` to `descriptive_recorded` / `descriptive_failed` per
§2.5.4, and stores the underlying five-outcome value in
`descriptive_source_outcome` so nothing is lost. Round-3 D2 terminal:
`descriptive_recorded`.

### B3 — populated from the B0 row plus the executed CAS result

`_b3_payload()` builds the terminal as a conjunct of the B0-row classifier and
metric flags and the executed `compare_formulas` result.
`cas_compare_completed` is set by the executor return value, not by key
presence, and `exponent_aware_skeleton_exact` is carried from the B0
`formula_metrics_pair` call because the CAS comparison does not produce it.
Round-3: 2/2 rows `diagnostic_complete`, `cas_compare_completed=true`.

### Guard singleton, abort lifecycle, resume, schemas, resources, strata

- `run_audit` calls `_require_installed_guard`, which raises
  `GuardBootstrapViolation` when `guard is None` **or** when the handle is not
  the object returned by `install_guard_from_entry`. The `SealedPathGuard`
  fallback is deleted.
- `initializing` is written before any work, `running` before the first counted
  primitive, and `completed` only at the end. `_write_atomic_manifest` rejects
  any status outside `("initializing", "running", "completed", "aborted")`.
  `CorpusGateError`, `ScalerGateError`, `EligibilityGateError`,
  `StratumGateError`, `ResourceCeilingError`, `GateAbortError`,
  `Q4ContractError`, `ExponentTokenError`, `FrozenEnvironmentError`,
  `GuardBootstrapViolation`, `ResumeIdentityError`, `TerminalVocabularyError`,
  and `ContractEvidenceError` all route through `_handle_global_abort`, which
  writes `abort_manifest.json` (including `abort_utc`, `output_dir_bytes`,
  `last_durable_call_key`, `last_durable_cache_key`), appends a six-field
  deviation entry, finalises the log, and flips the manifest to `aborted`.
  `deviation_log.md` is created at run start.
- `resume_identity` stores repo-relative fingerprint paths;
  `verify_fingerprint_artifacts` requires both files to exist, requires
  byte-identical bytes, and compares the payload dict verbatim without
  re-serialising. `dependency_versions()` reports
  `scikit-learn 1.7.2` and `numexpr 2.14.1` alongside python/numpy/scipy/sympy/torch.
  `verify_accepted_closure_source_hashes` is the optional closure hook; round-3
  status is `closure_record_absent`.
- §12.8: `registration_truth.json` carries `component_flags`; rewrite precheck
  fields are flat (`precheck_completed`, `precheck_equivalent`,
  `precheck_failure_reason`); `condition_summary.json` carries
  `confirmatory_calls`, `descriptive_calls`, and `primary_partition_counts`;
  the guard side channel fsyncs each row through `append_jsonl_line`; N1 rows
  carry a non-null `component_id`.
- `CallLogger` measures elapsed wall and output-directory bytes before and
  after every counted primitive, and `write_checked` measures around every
  artifact write.
- `eligibility_layer_for_stratum` raises `StratumGateError` for any unmapped
  stratum instead of falling through to `linear_control`.
- Reachability: all ten fixtures derive their outcome causally.
  `REACH-UNS-1` and `REACH-SUP-1` build synthetic 1320-row grids and call
  `evaluate_validity_gates` (excluding the self-referential `G_contract` and
  `G_impl`) followed by `evaluate_primary_decision`; they report
  `H0001 unsupported` / `H0001 supported` with `failed_gates=[]`.
  `REACH-RESCALE-1` triggers a real §5.2 early return through the production
  `Scaler.rescale_function`.

## 2. Additional defect found and fixed

`get_env()` left ODEFormer's default `max_dimension=2`, so
`env.equation_encoder.decode` returned `None` for any token `x_2`. The frozen
corpus contains 90 three-dimensional systems, so §3.4.8 `audit_word_to_infix`
would have failed for every one of them in a full run. Round-2 never saw this
because its smoke subset is two one-dimensional systems.
`get_env()` now sets `max_dimension = MAX_SYSTEM_DIMENSION = 3`. Decoded output
for `d <= 2` systems is unchanged, verified directly:

```text
['mul,2.0,x_0']                        d2: 2.0 * x_0                    d3: 2.0 * x_0
['add,x_0,x_1']                        d2: x_0 + x_1                    d3: x_0 + x_1
['div,pow2,x_0,add,0.44,pow2,x_0']     d2: (x_0)**2 / (0.44 + (x_0)**2)  d3: (x_0)**2 / (0.44 + (x_0)**2)
['x_0', 'x_1', 'x_2']                  d2: None                         d3: x_0 | x_1 | x_2
```

This is an implementation-capability fix, not a protocol change: §13/§3.4.8 do
not freeze ODEFormer environment parameters, and the frozen rescale/decode
algorithm is unchanged.

## 3. Source inventory reconciliation: 82 → 89

The §13.2 path list in the plan is an observed pre-implementation snapshot of
82 paths. The frozen recursive algorithm is normative. All 82 listed paths are
still present; 7 post-freeze audit modules were added, giving 89.

| # | added path | why it exists |
|---:|---|---|
| 1 | `src/gpu_runmultiai/eligibility.py` | `G_eligibility` layer validation |
| 2 | `src/gpu_runmultiai/jsonl_durable.py` | §12.5 fsync append, partial-suffix recovery, duplicate-key abort |
| 3 | `src/gpu_runmultiai/q4_reference.py` | audit-owned Q4 decimal-round reference and §3.4.10 canonical oracle |
| 4 | `src/gpu_runmultiai/quantization.py` | truth-side quantization stratum and `G_stratum` |
| 5 | `src/gpu_runmultiai/reachability.py` | §10.2 reachability evidence |
| 6 | `src/gpu_runmultiai/source_inventory.py` | the §13.2 algorithm itself |
| 7 | `src/gpu_runmultiai/contract_evidence.py` | **new in round 3**: executable §10.1 and §16 evidence |

Round-2 recorded 88 paths, which is this set minus `contract_evidence.py`.
Per §13.2 the per-file hashes stay non-normative until an implementation
closure PASS pins them, so no hash set is pinned here.

## 4. Commands and results

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
  --output-dir GPU_RUNmultiAI/cycles/C0001/runs/c0001_metric_identifiability_audit_v16_round3 \
  --audit-data-seed 61001 --audit-trajectory-seed 61002 --audit-rewrite-seed 61003 \
  --audit-negative-seed 61004 --audit-cas-subset-seed 61005 \
  --allow-cpu --oracle-timeout-sec 30.0 --q4-timeout-sec 10.0 \
  --simplifier-subprocess-timeout-sec 5.0 --cas-timeout-sec 60.0 \
  --smoke --fail-if-exists
```

| Check | Result |
|---|---|
| `compileall src scripts tests` | PASS |
| Plan SHA256 | `67017f5c...6c12078`, matches the frozen value |
| `git diff --check` | clean |
| Focused pytest | **96 passed** in 542.11 s (exit 0) |
| Audit CLI | exit 0 |
| Manifest `status` | `completed` |
| Manifest `commit` == runtime commit | `1bd083de...` == `1bd083de...` PASS |
| `source_hashes` recompute | identical to the manifest and to `source_inventory.json` (89 paths) |

## 5. Round-3 artifact values

| Field | Value |
|---|---|
| `audit_id` | `c0001_metric_identifiability_audit_v16` |
| `corpus_hash` | `253dbceb63af0a742c01d16afdecb24a872fdb867f2e4d80c6b833ec87f922dc` |
| `confirmatory_calls` / `descriptive_calls` / `grand_calls` | 57 / 8 / 65 |
| Ceilings (confirmatory / grand / descriptive) | 27637 / 30277 / 2640 |
| `primitive_completion_rate` | 0.00206 (bounded smoke) |
| `elapsed_sec` / `dir_bytes` | 31.48 s / 664,943 bytes |
| `access_guard_attempts` | 0 (`G4` PASS) |
| `primary_decision` | `H0001 undecidable` |
| Deviations | 1 (bounded smoke run) |

Validity gates:

| PASS | FAIL |
|---|---|
| `G_corpus`, `G_eligibility`, `G_stratum`, `G0`, `G4`, `G1`, `G_grand`, `G_contract`, `G_impl`, `G_q4ref`, `G_inc` | `G_n1`, `G_b1`, `G_b4`, `G_ctrl_cov`, `G_ctrl_fp`, `G_ctrl_lin`, `G_term` |

The failing gates are all population-shape gates (100 N1 rows, 510 B1/B4 rows,
480 control rows, 1320 strict rows). A two-component smoke run cannot satisfy
them, so `H0001 undecidable` is the correct and expected disposition. **This run
is not confirmatory evidence for or against H0001.**

Terminal partition read from `pair_results.csv` (7 rows, zero `unknown`):

| condition | terminal | count |
|---|---|---:|
| B0 | `preserved` | 2 |
| B1 | `control_pass` | 2 |
| B2 | `preserved` | 2 |
| D2 | `descriptive_recorded` | 1 |

Other artifacts: `b3_results.json` 2 rows `diagnostic_complete`;
`b4_results.json` 2 rows `sanity_pass`; `negative_controls.json` 2 rows with
non-null `component_id`; `q4_reference_controls.json` 7/7 `fixture_pass`;
`reachability_evidence.json` 10/10 `passed`;
`condition_summary.json` `primary_partition_counts`
`{'construction_incomplete': 0, 'execution_failure': 0, 'semantic_drift': 0, 'structural_false_negative': 0, 'preserved': 2, 'unknown': 0}`;
`fingerprint_payload.json` byte-identical to `fingerprint_bytes.bin`.

## 6. Failures and retries

- **Run-level failures: none.** All 65 `call_log.jsonl` rows have
  `status="completed"`; there are no `failed` rows, no `failure_reason` values
  in `pair_results.csv`, no `rescale_incomplete=true` rows, and no
  `e2_identity_fallback_candidate=true` rows. No `abort_manifest.json` exists,
  consistent with `status=completed`.
- **Retries: none.** The audit ran once from a clean committed tip with
  `--fail-if-exists`; `stage_cache.jsonl` holds 65 rows and `pair_cache.jsonl`
  holds 4, one per executed primitive and per durable pair, with no duplicates.
- **Development-time failures fixed before the validation run** (four focused
  tests failed on the first full pass and were repaired):
  `test_guard_bootstrap_singleton_and_deny` asserted an absolute parent-ledger
  count that is order-dependent, so it now asserts the count is unchanged;
  `test_g_contract_abort_and_deviation_lifecycle` still imported the removed
  `_write_abort_manifest`/`_write_deviation_log`; `test_b2_partition_uses_e1_fields_only`
  wrongly required B2's own classifier fields to be absent (only `e2_*`
  inheritance is forbidden); `test_registration_truth_and_rewrite_schema_fields`
  omitted the required `stage_cache`/`cache_path` arguments.

Counted-call breakdown from `call_log.jsonl` (all `completed`):

```text
registration: truth_register_classify 2, rewrite_oracle_precheck 2, quantization_stratum_assign 2
B0: e0_analytic_construct 2, scaler_rescale_function 2, q4_decimal_round_reference 2,
    simplifier_subprocess 2, oracle_equivalence E1 2, oracle_equivalence E2 2,
    classify_component_flags 2, formula_metrics_pair 2
B1: e0_identity_construct 2, scaler_rescale_function 2, q4_decimal_round_reference 2,
    simplifier_subprocess 2, oracle_equivalence 4, classify_component_flags 2,
    formula_metrics_pair 2
B2: classify_component_flags 2, formula_metrics_pair 2
B3: compare_formulas_cas 2
B4: classify_component_flags 2, formula_metrics_pair 2
C_q4: q4_decimal_round_reference 7
N1: oracle_equivalence 2
D2 (descriptive, 8): e0_analytic_construct 1, scaler_rescale_function 1,
    q4_decimal_round_reference 1, simplifier_subprocess 1, oracle_equivalence 2,
    classify_component_flags 1, formula_metrics_pair 1
```

## 7. Tests

`tests/test_gpu_runmultiai_c0001_metric_audit.py`: 96 passed. Contract-first
additions in this round:

- `test_b1_identity_scaler_is_the_production_scaler`,
  `test_b1_rescale_call_proof_records_production_callable`,
  `test_rescale_rejects_non_production_scaler`,
  `test_rescale_detects_both_frozen_early_returns`,
  `test_rescale_complete_on_production_scaler`
- `test_b2_partition_uses_e1_fields_only`,
  `test_d2_terminals_use_descriptive_vocabulary`,
  `test_terminal_vocabulary_rejects_illegal_terminal`,
  `test_unmapped_stratum_aborts_without_linear_fallthrough`
- `test_b3_terminal_requires_executed_cas_compare`,
  `test_negative_controls_carry_component_id`,
  `test_registration_truth_and_rewrite_schema_fields`,
  `test_condition_summary_reports_call_counts_and_absolute_counts`
- `test_run_audit_requires_guard_bootstrap_singleton`,
  `test_manifest_status_lifecycle_rejects_illegal_status`,
  `test_global_abort_routes_gate_errors_through_aborted` (all ten listed error
  types), `test_deviation_entries_have_six_fields`
- `test_dependency_versions_include_sklearn_and_numexpr`,
  `test_resume_identity_paths_are_repo_relative`,
  `test_resume_requires_byte_identical_fingerprint_artifacts`,
  `test_resume_identity_mismatch_raises_resume_identity_error`,
  `test_accepted_closure_source_hash_hook_is_absent_by_default`
- `test_call_logger_checks_resources_around_every_primitive`,
  `test_g_contract_checks_are_executed_not_asserted`,
  `test_f_acceptance_rows_are_computed_from_rows`,
  `test_g_contract_and_g_impl_gates_read_executed_evidence`,
  `test_reachability_uns_sup_use_real_gate_evaluation`,
  `test_round3_artifact_schemas_present_in_smoke`,
  `test_smoke_terminal_vocabulary_has_no_unknown`

The guard denial probe was moved out of `results/runs/` into `tmp_path`, so the
test suite no longer writes into the sealed campaign tree. Repaired tests:
`test_guard_bootstrap_singleton_and_deny`, `test_guard_bootstrap_no_replacement`,
`test_g_contract_abort_and_deviation_lifecycle`, `test_b1_uses_identity_scaler_parameters`,
and every `run_audit` call site now passes the bootstrap singleton through a
session fixture.

## 8. Not executed / open

- No full confirmatory run. The 27,637-call audit was not started; only the
  bounded smoke path is validated, and every population-shape gate is
  consequently FAIL.
- `max_dimension=3` is verified for decode equality on `d <= 2` inputs, but no
  three-dimensional system has been executed end to end through B0/B1/B2/D2.
  A full run is the first place `d = 3` rows will be exercised.
- Per-file source hashes are deliberately unpinned; `implementation_closure_record.json`
  was not created, so `accepted_closure_source_hash_status` is
  `closure_record_absent`.
- `G_n1`, `G_b1`, `G_b4`, `G_ctrl_cov`, `G_ctrl_fp`, `G_ctrl_lin`, and `G_term`
  have never been observed PASS on real data at full population size.
- The retained round-2 directory remains negative implementation evidence; its
  numbers must not be mixed with round-3.
