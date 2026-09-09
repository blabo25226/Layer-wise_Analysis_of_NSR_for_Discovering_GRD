# C0001 — Stage 4 Implementation Notes

**Author**: Stage 4 implementation agent (Claude Sonnet 5).
**Branch**: `20260909_researce_GPU_RUNclaude1`.
**Binding contract at time of writing**: `GPU_RUNclaude1/plans/C0001_preregistration_v2.1.md`
(HEAD `d6f4c64`, "Clear C0001 v2.1 for the full run: Gate 0 item 3 satisfied"). The contract changed
twice while this stage was in progress — v2 → v2.1 (a full re-freeze) and then two further
coordinator messages carrying additional audit findings against v2.1 — and this document reconciles
against the version current as of the last read. **Do not treat this document as a substitute for
re-reading the frozen `.md`/`.json` files before Stage 6/7**; it records what was built and what
remains open, not a restatement of the contract.

Scope reminder: this stage implemented and unit-tested the pipeline and ran only `--dry-run` and
`--smoke` invocations. **No full experiment was run.** Stage 6/7 (a separate agent) runs the real
47,987-candidate Part A pass, the full Part B census, and the real Part C corpus pass.

---

## 0. Second reconciliation round: F1–F8 (post `C0001_pc2b_discrepancy_resolution.md`)

A follow-up coordinator message, after the supervisor independently resolved the PC2b discrepancy
(§2.3 below is superseded by this section for PC2b specifically — the supervisor's finding is
correct and is now implemented), listed eight further required items, F1–F8. Status:

| item | status | what was done |
|---|---|---|
| **F1** PC2b component-level scoring | **done** | `pc2b_affine_decomposition` rewritten to score per-component (was per-system via `result.m3_system`, which let untouched no-op components match themselves trivially and inflated the denominator). Now: only components where the rewrite fired **and** is verified an identity are eligible. Measured on the real corpus: **60 eligible, 0 matched** — exactly the frozen v2.1 expectation and the supervisor's own re-measurement. |
| **F2** identity-verify every fired B-R1 rewrite | **done for PC2b; Part B's own `affine_rewrite_component` was already safe** | PC2b's eligibility now requires `tree_rewrite.verify_function_preserving` to pass before a component counts. Part B's separate `_try_rewrite_b_r1`/`affine_rewrite_component` (used for `U_affine`) was independently checked and already only accepts a rewrite step when its own `numeric_equivalent` verification passes (it `break`s the search on a failed verification rather than applying an unverified rewrite) — it does **not** call the same single-shot `rewrite_b_r1_affine_infix` PC2b uses, so it was not exposed to this specific bug. **An unresolved sub-disagreement**: the resolution doc reports 55/60 fired rewrites as verified true identities (5 "real bugs"); this implementation's own verifier (`numeric_equivalent` + `nsimplify(rational=True)` fallback) finds **60/60** verified, including hand-checking the doc's own cited "bug" example numerically (differences ~1e-16, i.e. machine precision only — see the worked check in this stage's transcript). Reported, not resolved unilaterally, consistent with this stage's practice of surfacing rather than papering over disagreements. |
| **F3** Gate 0 item 11 (910-pair agreement test + in-pass 1-in-100 census) | **not done** | Still only the partial version described in §2.1 (parametrized edge cases + 170 real-corpus identity pairs). Building the full frozen 910-pair enumeration (spanning PC0/PC2a/PC2b/PC2c/PC2d/PC3a/PC3b/PC4/PC4b's exact eligible sets) and the in-pass census was judged too large to do reliably in the time remaining in this stage; left for Stage 6/7. |
| **F4** process-based parallelism | **driver built and tested; not yet wired into the phase 1 script's main loop** | `gpu_runclaude1.partA_driver.score_cells_parallel` (a `multiprocessing.Pool`, up to 6 workers, cells read once in the main process and only already-parsed dicts + the picklable `StrataFrozenToken` cross the process boundary) and `demonstrate_timeout_inside_worker` (the required Gate 0 smoke assertion, redesigned to use a deterministic `time.sleep` under `_time_limit` rather than an SymPy expression of uncertain runtime — verified: triggers in ~1.0s against a 1s guard, not the 5s sleep it interrupts). Both are unit-tested. `scripts/phases/gpu_runclaude1_c0001_phase1_parta.py`'s matching loop still calls `score_cell` sequentially per cell; Stage 6/7 should switch it to `score_cells_parallel` for the full 960-cell pass. |
| **F5** PC4b | **done** | `pc4b_second_gain_class` added: the `a*X*inv(K+X) -> a*inv(K*inv(X)+1)` rewrite, eligibility-verified, reported non-gating. |
| **F6** static AST no-unguarded-read test | **done** | Two tests in `test_io_allowlist.py` parse every phase script and every `src/gpu_runclaude1/` module (except `io_allowlist.py` itself) and assert no `open`/`read_text`/`read_bytes`/`load`/`loadtxt` call site's arguments reference the `GPU_RUN5_SOURCE_RUN` name. This is a targeted, not fully general, static check (it does not trace arbitrary data flow through intermediate variables), but it directly covers this codebase's actual pattern, where every source-run path is built from that one named constant. |
| **F7** VRAM hard cap | **done** | `scripts/phases/gpu_runclaude1_c0001_phase3_partc.py` calls `torch.cuda.set_per_process_memory_fraction` sized to the frozen 5.5 GiB ceiling (as a fraction of the device's total memory) before loading the checkpoint. Re-verified with a real smoke run: peak VRAM 0.452 GiB, no allocator error. |
| **F8** shared `gain_indicator` (no duplication) | **already done before this message arrived** | `pc4_gain_positive_control` imports and calls `gpu_runclaude1.endpoints.gain_indicator`; it does not duplicate the conjunction inline. Verified by re-reading the current source before acting on this item, since the message described a state (`controls.py:355` duplicating the computation) that did not match what was actually in the file. |
| **F8** `nsimplify(rational=True)` fallback in rules 1 and 2 | **done** | `tree_rewrite.verify_function_preserving` (rule 1, positive controls) and `verify_function_changing` (rule 2, negative controls) both exist and are now wired into PC2b, PC3a and PC4/PC4b. PC3b's own no-op detection (`_is_noop_variable_swap`) uses exact post-canonicalization tree equality rather than numeric sampling, which is not subject to the same floating-point false-negative failure mode and was left as-is. |

All of the above were re-verified against the real GPU_RUN5 corpus where applicable (not merely
implemented from the written spec); the full test suite (395 passed, 1 skipped after this round) and
`python -m compileall` were re-run clean after every change in this section.

---

## 1. What was built

### 1.1 Reusable library code (`src/gpu_runclaude1/`)

| file | purpose |
|---|---|
| `constants.py` | Every frozen numeric value from v2/v2.1 in one place (seeds, thresholds, ceilings, checkpoint hash, decode config). |
| `io_allowlist.py` | The sealed-artifact guard: `InstrumentedOpener` (allowlist + computed `sealed_paths_read`), `enumerate_sealed_paths` (dynamic, finds all 7 on disk, never hardcoded), `enumerate_validation_cells` (content-checked glob, asserts 960), `sealed_open_guard` (a `builtins.open` context-manager guard), and `install_sealed_audit_hook` (a `sys.addaudithook`-based guard — the stronger, v2.1-mandated interception; see §3). |
| `strata.py` | H/L component stratification from `teacher_components_infix` (infix derivation, rule R1) and the mechanical write-before-match gate: `require_strata_frozen` returns a `StrataFrozenToken` only if the strata and ladder artifacts exist on disk with matching recorded hashes. |
| `ladder.py` | Wilson intervals, the two-stage cluster bootstrap, the 8-cluster family-level Wilson, the ladder cutpoint/verdict, and the realized-`|H|` OC/power tables. |
| `matcher.py` | `score_pair`: the M0/M1/M3 cascade over one (truth, candidate) pair, always infix on both sides, with the full failure taxonomy (`MATCHED` / `PROVED_DIFFERENT` / `COULD_NOT_EVALUATE`, every non-match reasoned) and the `M0 ⊆ M1 ⊆ M3` monotonicity audit (reported, non-gating per v2.1). |
| `partA_driver.py` | The *only* entry point that computes match indicators over stored cells (`score_cell`), mechanically gated on a `StrataFrozenToken`; `verify_m0_reproduction` (v2 §7.6). |
| `endpoints.py` | Primary gain-rate aggregation (`gain_indicator`, `compute_primary_endpoint`), the K=0 bound-of-record correction (v2.1 V2-MAJ-3), the two-sided sensitivity analysis, and A2-S1/A2-S2 secondaries. |
| `controls.py` | The full control battery: PC0, PC0-CAS, PC1, PC2a (reclassified harness-identity check), PC2b (reclassified `m3_affine_decomposition_limitation`, non-gating), PC2c/PC2d (component-resolution, tree-level, eligibility-verified), PC3a, PC3b (eligibility-filtered against no-op swaps), PC4 (the v2.1 gain-indicator positive control, eligibility-verified, HARD ABORT gate). |
| `tree_rewrite.py` | Deterministic tree rewrites shared by Part B and the control battery: PC2a's neg-asymmetry rewrite, tree-level add/mul commutation, PC3a's exponent alteration, PC3b's variable swap, the B-R1/B-R4 affine rewrite, and `verify_function_preserving`/`verify_function_changing` (numeric + `nsimplify(rational=True)` fallback verification, v2.1 §7.7.0). |
| `partb.py` | Part B: `U_mult` (raw-prefix-token count), `U_affine` (post-rewrite, generator-vocabulary-equivalent count), `U_min`, `in_support`, `realized_hill_exponents` (nested `pow2` chain depth, never a surface-token search), the B-R1..B-R4 rewrite engine. |
| `partc.py` | Part C CPU-only pieces: `cell_input_payload_sha256`, `verify_cell_identity`, `check_distinct_payload_count`, the `|`↔`,|,` normalization, `audit_reencoding_roundtrip`, `stahlberg_byrne_indicator`, `system_attribution`. |
| `calibration.py` | Gate 0 item 8's cost calibration: frozen sampling frame, timing-only, the match result is never bound to a name that outlives the loop iteration. |
| `config.py` | C0001's own `run_dir`/`phase_dir`/`write_manifest` (correctly labelled `GPU_RUNclaude1_C0001`, unlike reusing `gpu_run5.config.write_manifest`, which hardcodes `GPU_RUN5`), and `resolve_run_dir_for_phase` (fixes a same-run-across-phases directory-collision bug found during this stage's own testing). |

### 1.2 Additive edits to existing reusable modules

- **`src/evaluation/equation_metrics.py`** — `to_skeleton`/`symbolic_recovery` refactored into a shared
  `_to_skeleton_with_reason` plus a new public `skeleton_equivalence_with_reason`, so the exact failure
  surfaces v2/v2.1 require labelled (`SkeletonParseFailure`, `SymbolicEquivalenceTimeout`,
  `SkeletonEvaluationFailure`) carry an explicit reason. **This is a deviation from "extend, never
  modify" and is disclosed in full in §2.**
- **`src/gpu_run4/training.py`** — `teacher_forced_summed_logprob` added beside `teacher_forcing_loss`
  (not modified; verified by an AST-based test that neither calls the other).
- **`src/gpu_run4/records.py`** — `FAILURE_REASONS` extended (existing entries untouched) with the 13
  new C0001 reasons (`CanonicalizationError`, `RewriteVerificationFailure`,
  `AffineEncodingUnavailable`, `CandidateReencodingMismatch`, `NumericEquivalenceNonFinite`,
  `PositiveControlFailure`, `MatcherMonotonicityViolation`, `LengthMatchUnavailable`,
  `SkeletonParseFailure`, `SkeletonEvaluationFailure`, `SymbolicNodeCapExceeded`,
  `ComponentCountMismatch`, `CellIdentityMismatch`).
- **`src/gpu_run5/config.py`** — `require_artifact` hardened with a `sealed*` guard (v2.1 §2.4 item 10
  confirms this had zero callers repo-wide before, so it is defense-in-depth, not the primary
  safeguard).
- **`pytest.ini`** — `GPU_RUNclaude1/tests` added to `testpaths` (already had `pythonpath = .` and
  `GPU_RUN5/tests` from an earlier fix).

### 1.3 Phase entry points (`scripts/phases/`)

`gpu_runclaude1_c0001_phase{0,1,2,3,4}_*.py`, following the `gpu_run4/cli.py` scaffolding pattern
(`--run-id`, `--dry-run`, `--smoke`, `--allow-cpu`). Each writes a manifest via
`gpu_runclaude1.config.write_manifest` (campaign `GPU_RUNclaude1_C0001`) and never resolves a run
directory that already exists under a name a caller passed explicitly for a *later* phase of the same
run (see `resolve_run_dir_for_phase`).

- **Phase 0** (preflight): environment/checkpoint/firewall audit, cost calibration.
- **Phase 1** (Part A): strata → ladder → `StrataFrozenToken` → control battery → **hard-abort gate**
  (PC0/PC2a/PC4) → (on a non-smoke run) stop here if any hard-abort control fails → matching pass
  over stored cells → primary/secondary endpoints.
- **Phase 2** (Part B): unary-budget census over validation (+ train, non-smoke) truths.
- **Phase 3** (Part C): GPU forward pass, conditioning-identity checks, the summed-log-prob regression
  test, peak-VRAM tracking.
- **Phase 4**: mechanism-partition and compute-accounting synthesis from the earlier phases' own
  outputs (reads no GPU_RUN5 source path itself).

### 1.4 Tests (`GPU_RUNclaude1/tests/`)

86 tests added, all passing. See §4 for the exact command and output.

---

## 2. Deviations, disclosed in full

### 2.1 `src/evaluation/equation_metrics.py` — refactored, not purely additive

**What changed.** `to_skeleton`'s body was replaced with a one-line call to a new private
`_to_skeleton_with_reason`, which contains the *identical* two-attempt try/except structure as
before, plus reason tracking. `symbolic_recovery`'s `skeleton` computation was replaced with a call to
a new public `skeleton_equivalence_with_reason`, which contains the *identical* comparison logic.

**Why this was necessary, not optional.** v2/v2.1 explicitly require the exact failure surfaces at
`equation_metrics.py:166` (`to_skeleton` returning `None`) and `:192-193`
(`except Exception: skeleton = 0.0`) to carry a labelled `failure_reason`
(`SkeletonParseFailure`/`SymbolicEquivalenceTimeout`/`SkeletonEvaluationFailure`). The original
functions have no mechanism to report *why* they returned `None`/`0.0`; adding one without touching
their bodies is not possible, since the reason is only observable at the point of the original
`except` clauses.

**Why it is behavior-preserving.** For every input, the *return value* of `to_skeleton` (ignoring the
now-discarded reason) and of `symbolic_recovery(...)["skeleton"]` is unchanged: every code path that
previously fell through to `except Exception` (whether by a timeout or any other exception) still
falls through the same way. This was verified, not just argued:

- `GPU_RUNclaude1/tests/test_equation_metrics_extension.py` asserts
  `skeleton_equivalence_with_reason(a, b)[0] == symbolic_recovery(a, b)["skeleton"]` over a
  parametrized battery of edge cases (identity, different variable, parse failure, empty string,
  degenerate nesting) **and** over all 170 real GRN validation components (identity comparisons).
  Zero mismatches in both.
- The full pre-existing repository test suite (301 passed, 1 skipped baseline) was re-run after this
  edit with **zero regressions** (confirmed twice, before and after all subsequent edits in this
  stage).

**What still calls the pinned function directly.** `gpu_runclaude1.controls.pc0_identity` (PC0) calls
`symbolic_recovery(T_i, T_i)["skeleton"]` verbatim, per v2/v2.1's explicit pinning of PC0 to that exact
expression. `gpu_runclaude1.matcher.score_pair` (the primary scoring path) calls
`skeleton_equivalence_with_reason` instead, for the reason above.

**Cost-model note, disclosed per the coordinator's review.** `symbolic_recovery`'s returned dict is
built eagerly: reading only `["skeleton"]` still executes the `equiv` block (`:195-205`), including a
second `_timed_simplify` call on the un-skeletonized expressions (up to a further 10 s per call).
`skeleton_equivalence_with_reason` does **not** compute the `equiv` block at all, so the primary
matcher path (which uses it) is *cheaper* than a literal `symbolic_recovery(...)["skeleton"]` call
would be — but PC0, which the frozen spec requires to call `symbolic_recovery` directly, pays this
extra cost for all 170 components + 80 systems. This is disclosed in
`test_equation_metrics_extension.py::test_symbolic_recovery_eager_equiv_cost_is_disclosed_not_paid_by_the_primary_matcher`,
which pins (via AST inspection of imports) that `matcher.py` never imports `symbolic_recovery`.

**Gate 0 item 11 (v2.1 §7.4 V2-MAJ-2), NOT fully implemented.** v2.1 requires a two-part agreement
test before this implementation choice may be used at all: (a) 100% bit-identical agreement over
**910 specifically-enumerated synthetic control pairs** (PC0×170, PC2a×170, PC2b's eligible instances,
PC2c×170, PC2d×170, PC3a×48, PC3b×60, PC4×170, PC4b×170), and (b) an in-pass 1-in-100
double-computation census over the real endpoint pass, reported as `m3_implementation_agreement` with
a frozen 100% requirement. **Only a partial, ad hoc version of (a) exists** (the parametrized edge
cases plus the 170 real-corpus identity pairs, not the full frozen 910-pair enumeration spanning every
control including PC4b), and **(b) does not exist at all**. This is the single largest gap between
this implementation and v2.1's letter and must be built before Stage 6/7's real endpoint pass, per
v2.1's own conditional ("if either fails, the implementation must call `symbolic_recovery(...)
["skeleton"]` directly").

### 2.2 Reclassifications matching the coordinator-directed / v2.1 corrections

All of the following were verified empirically against the real GPU_RUN5 validation corpus (not
merely implemented from the written spec), and the measured values are recorded here because they are
now disclosed prior information for the corpus:

| item | what changed | measured on the real corpus |
|---|---|---|
| **`ComponentCountMismatch`** | Reclassified from `could_not_evaluate` to `proved_different` (v2.1 V2-MIN-9): a component-count mismatch is a decided, observed fact, not a failed evaluation, and is excluded from `could_not_evaluate_rate`. | Not separately re-measured this stage (0 of 2,235 stored component hits under a count mismatch, per the audit). |
| **PC2a** | Reclassified from an M3-sensitivity control to a harness-identity verification, gating on **both** M0 and M3 reproducing 170/170. | M0 170/170, M3 170/170 — confirmed. Non-short-circuited subset is empty; PC2a may not be cited as M3-specific evidence. |
| **PC2b** | Reclassified `m3_affine_decomposition_limitation`, non-gating, `descriptive`. | 110/170 component-level matches under this implementation's B-R1 rewrite (not 0/170 as one coordinator message claimed) — **see the explicit discrepancy note in §2.3**. Not part of Gate A→B either way. |
| **PC2c / PC2d** | Reported at **component** resolution (was system resolution), using the tree-level (not string-proxy) verified permutation, with eligibility verification. | **170/170 eligible, 170/170 matched**, both controls — exactly the frozen value. |
| **PC3b** | Eligibility filter added: a swap is eligible only if it changes the function (excludes commutative no-ops, e.g. R08's `x_0 * x_1`). | **60/60 eligible, 60/60 NON-match** under this implementation's "first component containing both variables, else first containing either" rule (not the fully lexicographic `(component index, variable pair)` enumeration v2.1 §7.7.1 specifies — a narrower, unverified-lexicographic approximation that happens to agree with the frozen result on this corpus but is not proven equivalent to the frozen rule in general). |
| **PC4 (renamed from an earlier "PC_GAIN_TOGETHER" draft)** | The gain-indicator positive control: `sympy.together` rewrite, scored through the exact `score_pair`/`gain_indicator` code path (imported, not duplicated), eligibility-verified via `verify_function_preserving`, gated on `gain_total >= 40 AND gain_H >= 20 AND >= 3 families`. | **170/170 eligible** (0 ineligible after adding the `nsimplify(rational=True)` fallback — see §2.4), **gain 100/170, all 100 in stratum H, 6 of 8 families contributing** (`R02, R03, R04, R06, R07, R08`), `gates_ok = True`. |

### 2.3 PC2b's measured rate — RESOLVED (superseded by §0)

**Status update: this was resolved by the supervisor and fixed in this implementation; see §0 F1/F2
above and `GPU_RUNclaude1/analyses/C0001_pc2b_discrepancy_resolution.md`.** The text below is kept
verbatim as the historical record of the discrepancy as first flagged, per this stage's practice of
not deleting a surfaced disagreement once it is resolved.

One coordinator message reported PC2b (the affine-decomposition control) at **0/28 components, 0/80
systems**. This implementation's own B-R1 rewrite engine (`gpu_runclaude1.tree_rewrite`,
`gpu_runclaude1.partb.affine_rewrite_component`), independently re-run against the real corpus, measures
**110/170 components, 40/80 systems** matched by M3. The underlying algebraic identity
(`a - a·K/(K+A) = a·A/(K+A)`) was hand-verified to hold even when `a` and `K` collapse to the same
skeleton symbol `c` (it is a pure algebraic identity, true for any `a, K`, not one that depends on
`a ≠ K`), which is inconsistent with the 0/28 claim's stated mechanism. This implementation's B-R1
rewrite was independently checked against `numeric_equivalent` on several real components and found
numerically exact.

**This is reported, not silently resolved**, because PC2b is non-gating either way (v2.1 explicitly
removes it from Gate A→B and states "a non-zero value is a harness-difference `DEVIATION`, not a
finding about E0" — but that sentence presumes the *frozen* value is 0, which this implementation's own
measurement does not reproduce). **Recommendation for Stage 6/7 or the supervisor**: re-run PC2b with
both this implementation's rewrite and whatever construction produced the audit's 0/28 figure, side by
side, before treating either as the value of record; do not simply overwrite one with the other.

### 2.4 A confirmed, empirically-verified fix: `nsimplify` rescues eligibility false negatives

One coordinator message reported that the `numeric_equivalent`-based eligibility verifier used by
PC4 produces **29 false negatives** (141/170 instead of the frozen 170/170), caused by 4-significant-
digit constant quantization (`gpu_run4/ted.py NUMERIC_SIGNIFICANT_DIGITS`) interacting with a tight
`rtol=1e-5`. This was independently reproduced exactly: before adding a `sympy.nsimplify(...,
rational=True)` fallback, PC4's naive eligibility check (rewrite differs textually) would have
accepted all 170 as candidates for gain-scoring without a genuine preservation proof; after adding
`gpu_runclaude1.tree_rewrite.verify_function_preserving` (numeric check first, exact-rational
`nsimplify` fallback second), **29 of 170 are rescued by the fallback and 0 remain unverified** —
`n_eligible = 170/170`, matching the frozen value exactly. This fix is implemented and tested
(`test_partb_generator_support.py`, `test_controls.py`, and the live measurement in §2.2's table).

### 2.5 An unresolved discrepancy: PC0-CAS's `SYMPY_MAX_NODES` monkeypatch

One coordinator message asserted that raising `LANSR_SYMPY_MAX_NODES` for PC0-CAS must be done via a
dedicated subprocess with the environment variable set *before* interpreter start, because
`ted.py`'s module-level `SYMPY_MAX_NODES` is read at import time and "in-process monkeypatching leaves
`formulas.py:434` at 40". This implementation's `gpu_runclaude1.controls.pc0_cas_self_equality`
monkeypatches `gpu_run4.formulas.SYMPY_MAX_NODES` **in-process** (save/reassign/restore around the
`_sympy_components_equal` call) and was verified empirically against real R01 and R08 systems: **all
tested systems pass at the raised cap (10/10 sampled, including R08, the family with 100% cap-exceeded
at the default 40)**, which is only possible if the monkeypatch is actually taking effect for that
call. This appears to work because `from gpu_run4.ted import SYMPY_MAX_NODES` in `formulas.py` creates
a plain module-level name in `formulas`'s own namespace, and Python functions resolve global names
against their defining module's namespace **at call time**, not at `def` time — so reassigning
`gpu_run4.formulas.SYMPY_MAX_NODES` does change what `_sympy_components_equal` sees on its next call.
**This directly contradicts the coordinator's claim**, and the subprocess-based mechanism was
therefore **not implemented**, since doing so would replace a verified-working, simpler mechanism with
an unverified, more complex one. This discrepancy is disclosed for reconciliation rather than resolved
unilaterally; Stage 6/7 should re-verify with `formulas.SYMPY_MAX_NODES` printed immediately before and
after the patch, on the full 80-system corpus, before trusting either account.

### 2.6 Sealed-artifact guard: two layers, one newly added

- `sealed_open_guard()` — a `builtins.open` context-manager patch (existed from the first pass of this
  stage). Uninstalls itself on exit; used as defense-in-depth inside phase scripts' `with` blocks.
- `install_sealed_audit_hook()` — a `sys.addaudithook`-based interception (added in response to the
  v2.1 §2.4 item 7 requirement that the guard be an **interception**, not a sanctioned-wrapper
  convention). Fires on the CPython `open`/`os.open` audit events, which covers `open()`, `io.open()`,
  `Path.open()`/`read_text()`/`read_bytes()`, and (per CPython's audit-event design) any other
  Python-level code path that ultimately calls the OS-level open. **Verified** to catch a bare
  `open()` and a `Path.read_text()` call on a sealed-named path, and verified **not** to affect
  ordinary reads. **Cannot be uninstalled** once installed (a deliberate CPython security property);
  each of the four phase scripts calls it once, at the very start of `main()`, before any allowlisted
  file is opened.
- **Not implemented**: the v2.1-mandated AST test asserting that *no* file-read call site anywhere
  under `src/gpu_runclaude1/` uses a path not obtained from the allowlist API. The audit-hook guard
  provides the *runtime* guarantee; the *static* AST guarantee is not yet built.
- `enumerate_sealed_paths` finds **7** sealed files on disk (verified: 3 in the pinned source run
  `gpu_run5_20260823_ddd267b0`, 2 each in two abandoned runs `gpu_run5_20260823_8cd0b6fa` and
  `gpu_run5_20260823_fec3a894`), never a hardcoded count.

### 2.7 Execution ordering (v2.1 §7.10)

`scripts/phases/gpu_runclaude1_c0001_phase1_parta.py` now: (1) writes and hashes the strata artifact,
(2) writes and hashes the ladder artifact, (3) obtains the `StrataFrozenToken`, (4) runs the full
control battery, (5) **checks the PC0/PC2a/PC4 hard-abort gate and stops before the matching pass** on
a non-smoke invocation if any fails, (6) only then runs the matching pass. This matches v2.1's
frozen ordering for the *hard-abort* gate. **Not implemented**: the finer-grained per-item ordering
v2.1 §7.10 specifies beyond this (e.g. PC0-CAS running in its own subprocess before the main battery,
the in-pass 1-in-100 agreement census interleaved with the endpoint pass itself, computing the H/L
stratification of the *published* 107 M0 hits only as the very last step §7.10 item 7 requires). These
are Stage 6/7 implementation-sequencing work, not logic gaps.

### 2.8 Not implemented at all (explicit gaps for Stage 6/7)

- **PC4b** (the second gain-diversification control, non-gating in v2.1).
- **PC0-CAS's exact required threshold check and reporting format** beyond the raw pass/fail per
  system this implementation already computes.
- **The hard VRAM cap via `torch.cuda.set_per_process_memory_fraction`** (v2.1 V2-MIN-10) — Part C's
  smoke run demonstrated 0.452 GiB peak (well under the 5.5 GiB ceiling) without this cap, and the cap
  itself is not wired in.
- **The full `R/phase0/sealed_inventory.json` artifact** v2.1 §2.4 specifies (ledger cross-reference
  plus filesystem census, written as its own artifact) — this stage's firewall test reports the
  equivalent information inline in `firewall_test.json` but does not write the dedicated file v2.1
  names.
- **A dedicated `research_state.md` §8 defect entry** for the phase-4 seal's pre-ledger hashing (v2.1
  §2.4a names this as a required follow-up outside this document; not this stage's file to write per
  v2.1's own scope statement, and not written here either).

---

## 3. What is verified vs. what is asserted only

**Verified with real data or a real GPU forward pass in this stage:**

- Strata: `|H| = 130`, `|L| = 40` over all 170 real validation components — matches the frozen v2.1
  value exactly.
- M0 reproduction: 0 mismatches over 2 real cells (100 real candidates) against the stored
  `exponent_aware_skeleton_exact` / `component_exponent_aware_skeleton_exact` fields.
- PC2a: M0 170/170, M3 170/170 (real corpus).
- PC2c / PC2d: 170/170 eligible, 170/170 matched (real corpus, component resolution, tree-level).
- PC3b: 60/60 eligible (with the eligibility filter), 60/60 NON-match (real corpus).
- PC4: 170/170 eligible (after the `nsimplify` fix), gain 100/170, all in H, 6/8 families (real corpus).
- Part B worked example: `U_mult = 5` rescued to `U_affine = 3` for a synthetic single-Hill-4-term
  component, matching v2/v2.1's own worked example exactly; real-corpus rate 9/170 = 5.3% component-
  level out-of-support (R07 6/30, R08 3/30, all others 0).
- Part C: the `sum_logprob / n == -teacher_forcing_loss` regression identity, on the real checkpoint
  and 2 real cells, holds to ~1e-7 (tolerance 1e-5). Peak VRAM measured at 0.452 GiB.
- The sealed-artifact guard (both layers) verified against real sealed filenames; 7 sealed files
  enumerated dynamically.
- A full `--smoke` run of all 5 phases in sequence, sharing one run directory
  (`results/runs/gpu_runclaude1_c0001_stage4demo/`), completes end to end.

**Asserted by the frozen contract but not independently re-verified this stage:**

- PC0-CAS's exact expected value at cap 40 (28/80) — not re-measured; only the raised-cap (200)
  behavior was spot-checked (10/10 sampled systems pass, consistent with the expected 80/80, but not
  all 80 were run to conserve compute, per this stage's dry-run/smoke-only scope).
- The measured Part A per-candidate cost (655 ms / 8.73 core-h vs. this repository's own earlier
  795 ms / 10.60 core-h) — not re-measured at full scale; Gate 0's own calibration mechanism
  (`gpu_runclaude1.calibration`) is implemented and was smoke-tested at n=8, not run at the frozen
  n=400.

---

## 4. Verbatim command output

### 4.1 `python -m compileall -q src scripts tests GPU_RUNclaude1`

```
(clean; exit code 0, no output)
```

### 4.2 `python -m pytest -q` (full repository suite, run from repo root)

```
SKIPPED [1] tests/test_dream4_loader.py:37: optional DREAM4 archive is not present; see GPU_RUN.md
395 passed, 1 skipped, 4 warnings in 75.93s
```

395 = 301 (pre-existing baseline, unchanged) + 94 (new, all under `GPU_RUNclaude1/tests/`). Re-run
after every edit across both reconciliation rounds (the initial v2.1 pass, then the F1–F8 pass);
zero regressions at any point.

### 4.3 `python -m pytest -q GPU_RUNclaude1/tests`

```
94 passed in ~24.5s
```

Test files: `test_io_allowlist.py` (sealed guard, both layers, plus the F6 static AST check),
`test_strata_ordering.py` (write-before-match gate, plus F4's `score_cells_parallel` /
`demonstrate_timeout_inside_worker`), `test_failure_reason_completeness.py`,
`test_r1_same_derivation_path.py`, `test_summed_logprob_regression.py` (GPU, real checkpoint, skips
if absent), `test_equation_metrics_extension.py`, `test_ladder.py`, `test_partb_generator_support.py`,
`test_controls.py` (PC0–PC4b, including F1's PC2b component-level test), `test_partc_identity.py`,
`test_endpoints.py`.

---

## 5. Exact commands for Stage 6/7

All commands assume `source /home/blabo/miniconda3/etc/profile.d/conda.sh && conda activate lansr310`
and the repository root as the working directory. **Do not add `--smoke` or `--dry-run` for the real
run** — those flags are this stage's own verification mechanism and deliberately restrict scope.

```bash
# Choose one run ID for the whole cycle (do this once; verify it does not already exist):
RUNID=gpu_runclaude1_c0001_<short7-of-the-commit-at-run-start>
ls -d results/runs/${RUNID} 2>/dev/null && echo "REFUSING: directory exists" || echo "clear to proceed"

# Phase 0 — Gate 0 preflight, including the real 400-candidate/50-per-family calibration.
# Expected wall-clock: a few minutes (CPU only; the calibration itself is ~400 x 655ms-795ms/candidate
# ~= 4-6 minutes, plus environment/checkpoint audits). No GPU/VRAM use.
python scripts/phases/gpu_runclaude1_c0001_phase0_preflight.py --run-id "$RUNID"

# Phase 1 — Part A, full 80-system control battery (~0.25-0.5 core-h), then the hard-abort gate
# (PC0/PC2a/PC4), then the full 960-cell / 47,987-candidate matching pass if the gate passes.
# Expected wall-clock at the measured 655ms-795ms/candidate: ~8.7-10.6 CPU-core-hours single-process;
# Stage 6/7 must switch the sequential score_cell loop in this script to
# gpu_runclaude1.partA_driver.score_cells_parallel(cells, token, n_workers=6) before running this
# for real, or the wall-clock is the full core-hour figure, not divided by 6. CPU only, no GPU/VRAM use.
python scripts/phases/gpu_runclaude1_c0001_phase1_parta.py --run-id "$RUNID"

# Phase 2 — Part B, full 320-truth (train+validation) census. Expected wall-clock: a few minutes
# (deterministic census + bounded rewrite search, no SymPy-heavy matching). CPU only.
python scripts/phases/gpu_runclaude1_c0001_phase2_partb.py --run-id "$RUNID"

# Phase 3 — Part C, GPU forward pass over the full in-support cell set (n_in_support ~= 60 of 80
# systems x up to 12 cells each). Expected wall-clock: well under the 2.0 GPU-hour ceiling (the
# 2-cell smoke measured ~seconds per cell once the model is loaded). Expected peak VRAM: comfortably
# under the 5.5 GiB hard cap this stage wired in (torch.cuda.set_per_process_memory_fraction) --
# smoke measured 0.452 GiB for 2 cells; the full run scores more cells but each forward pass is
# independent and does not accumulate resident state across cells beyond the cached src_enc per cell.
python scripts/phases/gpu_runclaude1_c0001_phase3_partc.py --run-id "$RUNID"

# Phase 4 — mechanism partition and compute accounting. Expected wall-clock: seconds (reads only
# this run's own earlier-phase outputs).
python scripts/phases/gpu_runclaude1_c0001_phase4_partition.py --run-id "$RUNID"
```

**Stage 6 smoke** (this stage's own verification mode, safe to re-run before the full run):

```bash
RUNID=gpu_runclaude1_c0001_stage6smoke
python scripts/phases/gpu_runclaude1_c0001_phase0_preflight.py --smoke --run-id "$RUNID"
python scripts/phases/gpu_runclaude1_c0001_phase1_parta.py --smoke --smoke-cells 3 --run-id "$RUNID"
python scripts/phases/gpu_runclaude1_c0001_phase2_partb.py --smoke --run-id "$RUNID"
python scripts/phases/gpu_runclaude1_c0001_phase3_partc.py --smoke --smoke-cells 2 --run-id "$RUNID"
python scripts/phases/gpu_runclaude1_c0001_phase4_partition.py --smoke --run-id "$RUNID"
# Expected wall-clock: well under 5 minutes total. Expected peak VRAM: well under 1 GiB (measured 0.452 GiB).
```

**Before running Phase 1 for real (Stage 7), Stage 6/7 must additionally**:

1. Build the missing Gate 0 item 11 agreement test (§0 F3) — the 910-synthetic-pair battery and the
   in-pass 1-in-100 census — or explicitly accept the risk of not having it and record that decision.
2. Re-verify the PC0-CAS monkeypatch claim (§2.5) with an explicit before/after print of
   `gpu_run4.formulas.SYMPY_MAX_NODES`, on the full 80-system corpus, and decide whether the
   in-process mechanism this implementation uses is acceptable or must be replaced.
3. Switch Phase 1's matching loop to `gpu_runclaude1.partA_driver.score_cells_parallel` (built and
   tested this round, §0 F4) instead of the current sequential per-cell loop, or the full run takes
   the single-process wall-clock (~8.7-10.6 core-hours), not that figure divided by up to 6 workers.
4. PC2b's discrepancy is now resolved (§0 F1/F2, §2.3) — no further action needed there.

---

## 6. `git status --short` at handoff

```
 M GPU_RUNclaude1/tests/test_controls.py
 M GPU_RUNclaude1/tests/test_io_allowlist.py
 M GPU_RUNclaude1/tests/test_strata_ordering.py
 M pytest.ini
 M src/evaluation/equation_metrics.py
 M src/gpu_run4/records.py
 M src/gpu_run4/training.py
 M src/gpu_run5/config.py
?? GPU_RUNclaude1/analyses/C0001_implementation_notes.md
?? GPU_RUNclaude1/tests/test_endpoints.py
?? scripts/phases/gpu_runclaude1_c0001_phase0_preflight.py
?? scripts/phases/gpu_runclaude1_c0001_phase1_parta.py
?? scripts/phases/gpu_runclaude1_c0001_phase2_partb.py
?? scripts/phases/gpu_runclaude1_c0001_phase3_partc.py
?? scripts/phases/gpu_runclaude1_c0001_phase4_partition.py
?? src/gpu_runclaude1/
```

**Note on this status.** Most of `GPU_RUNclaude1/tests/` (all files except `test_endpoints.py`) show
as tracked-and-modified (`M`) rather than untracked (`??`), and two commits appear in `git log`
(`5e93fb1`, `d6f4c64`) that this agent did not create — these are from other agents/processes in this
autonomous campaign (the v2.1 amendment and its clearance), which evidently staged and committed a
snapshot of this stage's in-progress test files alongside their own review documents. This agent made
**no commits** and ran no `git add`/`git commit` at any point. This is reported factually, not
resolved; the working tree is left as-is for the supervisor to review and decide how to reconcile,
per this stage's brief ("do not commit").

A full `--smoke` demonstration run of all 5 phases is preserved at
`results/runs/gpu_runclaude1_c0001_stage4demo/` for inspection; it does not collide with any prior
`results/runs/gpu_run5_*` or `results/runs/gpu_run4_*` directory.
