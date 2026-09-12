# C0002 preregistration v1 — reproducibility, leakage and provenance audit

| field | value |
|---|---|
| target | `GPU_RUNclaude1/plans/C0002_preregistration_v1.md` (1,199 lines) + `.json` (600 lines), status `DRAFT_PENDING_REVIEW` |
| reviewer role | `lansr-reproducibility-auditor` — independent of the drafting methodologist and of the concurrent `lansr-statistical-reviewer` |
| date | 2026-09-11 |
| branch | `20260909_researce_GPU_RUNclaude1`, HEAD `20e4621` at audit start |
| scope | design audit **before** freeze and **before** any compute (rule 06, skill `reproducibility-audit`) |
| sealed artifacts read | **NONE.** `find results/runs -name "sealed*"` was used to enumerate *names* only (7 files, matching `research_state.md` §4). No sealed path was opened, hashed or byte-read at any point in this audit. |
| draft edited | **NO.** No C0001 artifact and nothing under `results/runs/` was modified. |
| **verdict** | **The draft MUST NOT be frozen as written.** 3 CRITICAL, 14 MAJOR. |

---

## 0. What this audit verified as correct

Stated first, because the draft is unusually well evidenced and most of its factual claims survive
direct checking. Everything below was recomputed or read, not accepted from the draft's prose.

**Realized denominators (§4) — exact.** Independently recounted over
`results/runs/gpu_run5_20260823_ddd267b0/phase3/cells/*_validation_*.json` intersected with
`results/runs/gpu_runclaude1_c0001_b731cdd/phase2/partB_in_support_systems.json`:

| quantity | draft | recounted |
|---|---|---|
| validation cell files | 960 | 960 |
| in-support systems | 71 | 71 |
| in-support cells | 852 | 852 |
| in-support candidates | 42,593 | 42,593 |
| of which `valid: true` | 42,593 | 42,593 |
| candidates per cell | 50 on 846, 49 on 5, 48 on 1 | identical |
| in-support systems per family | R01–R06 = 10, R07 = 4, R08 = 7 | identical |
| all-cell candidates | 47,987 | 47,987 |

**Checkpoint identity (§3) — verified from the artifact itself.**
`sha256sum assets/odeformer/weights/odeformer.pt` =
`56754040be5aa92ed4767fc43ee2008faa293f87c12b643e66c7df3e1623a5e8`, size 464,822,385 bytes. Both
match. Loading the checkpoint (`torch.load`, CPU) and reading its own stored attributes confirms the
decode context the draft calls "the checkpoint's own stored defaults" is exactly that:
`beam_type = sampling`, `beam_temperature = 0.1`, `beam_size = 50`,
`max_generated_output_len = 200`, and `env.params.use_two_hot = False`. Also read out and used
below: `env.params.float_precision = 3`, `float_descriptor_length = 3`, `max_int = 10`,
`max_dimension = 6`. **F-d is confirmed, and it is confirmed from the checkpoint rather than from a
code branch.**

**§5.1 citation corrections — all three verified.**
`src/evaluation/gpu_run5_selection.py:11 formula_selection_key(records, validation_ce)` groups by
`(system_id, seed)` and returns a 4-tuple; it never indexes a candidate. A different
`formula_selection_key(rows)` of arity 1 returning a 3-tuple exists at
`src/gpu_run5/evaluation.py:143`. The real per-cell selector is
`src/gpu_run5/evaluation.py:107 select_candidate(...)`, whose `"official_reconstruction"` branch is
`return 0` at `:111-112`. **The draft cites an object that does what it says it does.**

**§0.2 disclosure — exact.** `phase3/partC_cell_records.jsonl` holds 960 rows with exactly the keys
`cell_id, excluded, cell_input_payload_sha256, gt_logprob_sum, gt_token_length`;
min `-846.0560302734375`, max `-115.8770751953125`, median `-297.5801086425781`. No `lp_sel`,
`lp_best`, `sb_*` or `me_*` field anywhere. `partC_endpoints.json`, `partC_reencoding_audit.json`
and `partC_identity_audit.json` do not exist in that directory. The disclosure is complete and
accurate.

**Instrument facts.** F-a (`sympy/core/random.py:28-29` module-level unseeded `rng`, `seed()` at
`:44` reseeding both generators), F-b (`bool(a.equals(b))` at `equation_metrics.py:65`;
`skeleton_equivalence_with_reason` at `:197` with the call at `:217`; `symbolic_recovery` at `:226`),
F-c (`_time_limit` runs unguarded at `:35-41` when `seconds <= 0`, without `SIGALRM`, or off the main
thread), F-e (24-key stored candidate schema with no score / log-probability / rank / NLL field),
F-g (`Scaler(time_range=[1,10], feature_scale=1)` when `params=None` at `sklearn_wrapper.py:50-56`;
permutation at `:133-136` immediately after `np.random.seed(candidate_seed)` via
`capture_numpy_permutation` wrapping `regressor.fit` at `inference.py:205-206`, with nothing
consuming NumPy randomness in between) — **all verified by direct read**. `Expr.equals` was
additionally shown empirically to return `None` and to consume `sympy.core.random.rng` on real
inputs.

**Leakage / firewall, the parts that hold.** `results/runs` holds exactly 7 `sealed*` files,
matching `research_state.md` §4. `src/gpu_runclaude1/io_allowlist.py` checks the *resolved* filename
(`is_sealed_path`), never a hardcoded list; `enumerate_sealed_paths` globs `sealed*` by name without
reading bytes; `InstrumentedOpener.sealed_paths_read` is a computed property. `phase3/all_candidates.json`
was checked and contains **only** `split == "validation"` rows (47,987) — the `H0010` census corpus
carries no test-split contamination. `src/gpu_run5/config.py load_sealed_test`'s `phase < 8`
`PermissionError` is unchanged and every C0002 phase is `< 8`.

**Gate 0 feasibility.** `python -m pytest -q --collect-only` collects 468 tests with zero collection
errors; `GPU_RUN5/tests` collects 124 with zero errors.

**Scope discipline.** Arm A / Arm B are correctly forbidden from being compared as alternatives
(§1.4 item 1, §6); no layer estimand is measured (§17, rule 04); no selection endpoint is claimed on
GRN (§1.4 item 2, §16.2) — which is the right call given F-e and F-f; no training, no adaptation, no
final test.

---

## CRITICAL

### CRITICAL-1 — `lp_gt` is a logsumexp, so `sb_best` is not a certificate

**Anchor**: §7.2 "`lp_gt(c) = logsumexp over the verified members of E(s)`"; §8.1
`sb_best(c) = 1[lp_gt(c) > lp_best(c)]`; §1.1 "why both directions are certificates"; §8.7 permitted
sentence "**certified lower bound** on the search-error rate".

The certificate argument in §1.1 is: `B = lp_best ≤ L*` because `L*` is the maximum of
`log P(y|x)` over **complete sequences**, therefore `G > B ⇒ L* ≥ G > B` and a search error is
certified. That derivation requires `G` to be `log P(y|x)` for **one** sequence `y`.

§7.2 instead defines `G = lp_gt = log Σ_e P(e|x)` over the verified admissible encodings `e` of the
truth, `|E(s)| ≤ 10` (`e1`, `e2`, orbit cap 8). A logsumexp is not the log-probability of any
sequence. `L* ≥ lp_gt` does **not** hold; what holds is only

$$\max_e \log P(e\mid x) \;>\; B - \log |E(s)|$$

so `sb_best = 1` certifies nothing stronger than "some spelling of the truth beats `lp_best` to
within `log|E(s)| ≤ 2.303` nats". §8.7 makes "certified lower bound" a **binding permitted sentence**
for the cycle report, so the contract as written mandates a claim its own endpoint cannot support.

The `me_best` / E2 branch is **unaffected and sound**: `logsumexp ≥ max`, so
`lp_gt_lse < lp_best ⇒ max_e log P(e) < lp_best`. Only the E3 / falsifier direction breaks.

**Required change.** Define the certificate indicators on `lp_gt_max` (the maximum over verified
encodings), which §7.2 already computes as a descriptive companion, so this costs nothing:
`sb_best(c) = 1[lp_gt_max(c) > lp_best(c)]`. Keep the logsumexp quantity for `me_best`, for `Δ_enc`
and as a descriptive robustness read, and state explicitly in §1.1 that the certificate is claimed
for the single-sequence maximum only. Do **not** weaken §8.7's wording as the alternative fix — the
endpoint should be made to match the claim, not the claim relaxed.

### CRITICAL-2 — Gate 3b has two contradictory dispositions in the same contract

**Anchor**: §7.2 "**If 3b fails**, the logsumexp arm is `not_measurable`, `lp_gt` falls back to `e1`
alone, and every E2 statement in the cycle report is qualified `single_encoding_lower_bound` — **a
downgrade, not an abort**"; versus §11 Gate 3 which lists "3b **≥ 64/71**" as a gate condition, and
§11 Gate 6 "`H0001-R` endpoints are reported only if: ... **Gate 3 passed**; ... Otherwise `H0001-R`
is `undecidable`".

Under §7.2 a 3b failure downgrades the wording. Under Gate 3 + Gate 6 the identical condition makes
the entire primary `undecidable`. **This is the C0001 Gate B→C defect in a new place**: one contract
text, two clauses, and an implementer reading only the gate table will implement the other one. §11
itself opens with "Every condition below is machine-checkable and must be implemented as a machine
check" and R7 requires quoting the contract verbatim beside the check — R7 cannot be satisfied when
two contract passages say opposite things.

**Required change.** Split Gate 3 into *pass conditions* (3a, 3c) and *downgrade conditions* (3b),
state the split in both §7.2 and §11, and remove 3b from the conjunction Gate 6 consults. Do the
same audit for 3c, which has no stated disposition on failure anywhere except via Gate 6 (see
MAJOR-14).

### CRITICAL-3 — §16.1 reinstates the unguarded `run_manifest.py` directory fingerprint that C0001 v2.1 forbade

**Anchor**: §16.1 "`scripts/ops/run_manifest.py` records git commit and branch, `pip freeze`, GPU and
driver, checkpoint SHA256, and **a recursive data-tree fingerprint**."

`scripts/ops/run_manifest.py:28-42 tree_sha256` does
`sorted(p for p in path.rglob("*") if p.is_file())` and then `sha256(file_path)` on every one of
them, and `:119` applies it to each `--data-path`. The function has **no sealed-path guard of its
own** — the guard lives in `io_allowlist.assert_no_directory_argument` /
`safe_run_manifest_data_paths`, which `run_manifest.py` does not import (verified: no reference to
`io_allowlist` in that file, and no call site anywhere in `scripts/phases/` passes through it).

Two aggravating facts:

1. `run_manifest.py` is invoked as a **separate process**. `install_sealed_audit_hook()` and
   `sealed_open_guard()` are per-interpreter and are installed in the *phase* entry point (as at
   `scripts/phases/gpu_runclaude1_c0001_phase3_partc.py:249,:254`). Neither protects a subprocess.
   A directory `--data-path` pointed at `results/runs/gpu_run5_20260823_ddd267b0` would byte-read
   `phase2/sealed_test.json`, `phase2/sealed_family_holdout_test.json` and
   `phase4/sealed_official_test.json`, **while Gate 0's `sealed_paths_read == []` assertion still
   passed**, because that value is computed over what went through `InstrumentedOpener` in the phase
   process.
2. **C0001 already fixed this and C0002 dropped the fix.** `C0001_preregistration_v2.md:337-339` and
   `v2.1.md:522-524` say verbatim that "`scripts/ops/run_manifest.py --data-path` receives only
   individual files from that allowlist. [Passing a directory] is forbidden", and v2.1 `:1719`
   makes "no directory argument was passed to `run_manifest.py`" a checked gate item. The C0002
   draft's §16.1 contains no such clause and its §2.4 firewall list does not mention
   `run_manifest.py` at all. This is the recurrence of `C0001_reproducibility_audit.md` MAJ-2.

**Required change.** (a) Reinstate the v2.1 §2.4 item 6 prohibition verbatim in §2.4 and §16.1;
(b) require every `run_manifest.py` invocation to route its paths through
`safe_run_manifest_data_paths()`; (c) make "no directory argument reached `run_manifest.py`" an
explicit Gate-0 and phase-boundary check; (d) preferably also call `install_sealed_audit_hook()`
inside `run_manifest.py`'s own `main()` so the guard is not conditional on the caller.

---

## MAJOR

### MAJOR-1 — per-worker SymPy seeding does not close the RNG nondeterminism mechanism

**Anchor**: §3 "`SYMPY_RNG_SEED` = `20260911` — passed to `sympy.core.random.seed(...)` **in every
worker process, at worker start**, before any SymPy call (§5.2)"; §5.2 item 2; §5.2 "What this makes
reproducible: the failure classification becomes a function of the inputs and of declared values,
not of machine load, SymPy cache state, or OS entropy."

**The trace.** `sympy/core/random.py` holds one module-level `rng = _random.Random()` per
interpreter. `seed(a)` at `:44` reseeds it and `_assumptions_rng`. Confirmed empirically in the
pinned 1.13.1 that `Expr.equals` does consume it on real inputs, and that the outcome can be `None`:

```
sqrt(x_0**2).equals(Abs(x_0))                    -> None   | rng consumed: True
(sin(x_0)**2 + cos(x_0)**2).equals(1)            -> True   | rng consumed: True
x_0**4/(1+x_0**4)).equals(1 - 1/(1+x_0**4))      -> True   | rng consumed: False
```

Seeding **once per worker at worker start** fixes the RNG's state at `t = 0` of that worker. It does
**not** fix the state at the moment any particular comparison runs, because that state is advanced by
every RNG-consuming call the worker happened to make before it. Demonstrated directly:

```
seed(123); state_before_target                     -> S0
seed(123); (sin^2+cos^2).equals(1); state_before_target -> S1 != S0
```

Under any pool that distributes work by availability (`Pool.map`/`imap`, `ProcessPoolExecutor`), which
items land on which worker, and in which order, is **load-dependent** — exactly the property the
change is supposed to remove. So a given comparison is evaluated against different random sample
points on different runs, and the mechanism that produced C0001's 14 bidirectional
`could_not_evaluate` flips is not closed. (That the RNG *caused* those specific flips remains the
draft's own declared hypothesis; what is established here is that the proposed fix does not make the
per-comparison outcome a function of the input.)

Two further gaps in the same paragraph:

- The draft does not fix the `multiprocessing` **start method**. Under `fork` a worker inherits the
  parent's already-advanced `rng` state (identical across workers, then divergent); under `spawn` it
  gets a fresh unseeded import. The firewall guards have the same dependency: `builtins.open`
  patching and `sys.addaudithook` are inherited on `fork` and **not** on `spawn`. Both the seed
  contract and the §2.4 firewall are therefore conditional on an unspecified value.
- Gate 0 item 7's "a worker-start assertion proves `SYMPY_RNG_SEED` was applied in each of the 6
  workers" proves only that `seed()` was called, which is the part that is not in question.

**Required change.** Reseed **per work item**, deterministically from the item's own identity —
e.g. `sympy.core.random.seed(SYMPY_RNG_SEED ^ int(sha256(normalized_input_key).hexdigest()[:8], 16))`
immediately before the guarded call — so the outcome is a function of the input and `SYMPY_RNG_SEED`
alone regardless of worker assignment and order. Additionally: declare the start method explicitly
(`mp.get_context("fork")` or `"spawn"`), and if `spawn`, require the worker initializer to install
`install_sealed_audit_hook()` as well as the seed. Add a test that two runs with different
`chunksize` produce byte-identical label files.

### MAJOR-2 — `CAS_NODE_BUDGET = 400` is not load-independent on the paths that actually exist

**Anchor**: §5.2 item 1 "Before any SymPy call on the decision path, compute `sympy.count_ops(expr)`
on the input. If it exceeds the frozen bound `CAS_NODE_BUDGET = 400`, the call is **not attempted**";
§21 item 1.

§21 item 1 already concedes that the budget governs admission, not termination. Three further
problems are specific to this codebase and are not conceded:

1. **The inputs on the real paths are strings, not `Expr`.** `sympy.count_ops` accepts a string
   (verified: `count_ops("x_0/(1.0+x_0**4)")` returns `3`) only by calling `sympify` internally
   (verified: `"sympify" in inspect.getsource(sympy.count_ops)`). The C0002 SymPy entry points take
   strings: `src/gpu_runclaude1/partc_reencoding.py:103 sp.sympify(prepared, locals=local,
   evaluate=True)` and `src/evaluation/equation_metrics.py:174,183 _timed_simplify(sympify(sk))`. So
   the admission bound **cannot precede the parse**; the parse is paid unconditionally and is itself
   unbounded.
2. **`_timed_simplify(sympify(...))` evaluates `sympify` outside the guard.** In
   `equation_metrics.py:174` and `:183`, `sympify(...)` is an argument expression, so it is evaluated
   *before* `_timed_simplify` enters the `with _time_limit(...)` block. The parse is therefore
   guarded by neither the node budget nor the wall clock.
3. **`count_ops` is not a cost model for the operations actually called.** Verified that
   `cancel`/`together`/`fraction` and `count_ops` consume no RNG, but their runtime on rational
   functions is not monotone in `count_ops`; a 400-node bound does not bound `cancel` on a rational
   function with many symbols.

**Required change.** State in §5.2 that the admission bound applies to already-parsed `Expr` objects
only, and add an explicit, separately-labelled disposition for the unbounded parse
(`parse_not_admitted_unbounded`, or a guarded parse with its own counted label). Fix
`_timed_simplify` call sites so the `sympify` is inside the guard. Neither change alters any C0001
number and neither relaxes a threshold.

### MAJOR-3 — Gate 6's `wall_clock_guard_fired == 0` has no achievability evidence and couples the primary to a subsystem §5.2 says it does not depend on

**Anchor**: §5.2 item 1 "its firing is recorded under the **separate** label `wall_clock_guard_fired`,
which is counted and **must be 0** for the run to be admissible"; §11 Gate 6 condition 5; §13
"`undecidable` ... or `wall_clock_guard_fired > 0`"; §15 "`wall_clock_guard_fired` | **must be 0**".

Every other threshold in this draft carries a measured "verified achievable" column — §10's six
controls, Gate 3's three conditions, Gate 4's eight conditions. `wall_clock_guard_fired == 0` carries
none, and the only measurement on record points the other way: the C0001 replication
(`replications/C0001_opportunity_census_replication.md` §6.2, and §0.1 of this draft) records
**9 firings** in the recorded run and **7** in the replication over 101,963 comparisons at the
identical 10.0 s `SIGALRM` limit. A comparable amount of SymPy work in C0002 should be expected to
fire it at least once.

Worse, §5.2's own scoping says "**no C0002 endpoint depends on a CAS equivalence decision**", yet
Gate 6 makes a single CAS timeout anywhere — including in the `H0010` census or in any record-schema
recomputation — turn the **GPU log-probability primary** `undecidable`. A gate that can kill the
primary for a reason the contract says is unrelated to it is not a usable gate.

**Required change.** Either (a) scope the condition to the endpoints that actually consume a CAS
decision (i.e. `H0010`), leaving `H0001-R` unaffected, or (b) keep it global but state the measured
basis on which zero is expected and what happens when it is not. Do **not** raise the 10.0 s limit —
that is forbidden and is not the fix.

### MAJOR-4 — §16.2 mandates `expression_safety` diagnostics that are not in the stored data, are not budgeted, are wrong for GRN, and contain a silent fallback

**Anchor**: §16.2 "... and the singularity / integration diagnostics **already produced by**
`expression_safety`."

The stored candidate record has exactly 24 keys (verified, listed in §0 above). None of
`expression_safety`'s outputs (`has_tan`, `has_division`, `near_singularity`,
`extrapolation_valid`, `extrapolation_extreme`) is among them, and `expression_safety` is reached
only from `equation_metrics.py:374,398 score_prediction`, which the GPU_RUN5 phase-3 pipeline does
not call. **"Already produced" is false**; satisfying §16.2 requires running it on 42,593
candidates. Consequences:

- **Not budgeted.** §14's CPU line is "re-encoding / tokenization, 42,593 × 2 → 1.7 core-h",
  derived from a measured 0.07 s/candidate for "tokenization + re-encoding + audit + scaling map".
  `expression_safety` adds `sympify` + `together` + `denom` + `lambdify` + two vectorized evaluations
  per candidate and is in none of the projections.
- **Wrong variables for this corpus.** `equation_metrics.py:329` is
  `lambdify(["x_1", "x_2", "x_3"], denominator, ...)` and `:330-331` pad to 3 columns. GRN systems use
  `x_0 … x_5` with `max_dimension = 6` (read from the checkpoint). Any GRN expression containing
  `x_0`, `x_4` or `x_5` raises inside the `try`.
- **Hidden fallback — a failure recorded as a result.** `:338-339` is
  `except Exception: base["near_singularity"] = 1.0 if base["has_division"] else 0.0`. The
  diagnostic silently degenerates to a substring test on `"/"`, with no label. This is the same class
  of defect as `_timed_equals`'s `bool(a.equals(b))` that the draft correctly identifies as F-b, in a
  routine the draft mandates. §15's failure taxonomy does not cover it.

**Required change.** Either drop the clause (rule 03's singularity item is arguably already carried
by the stored `structure` flags and `trajectory_metrics.*_failures`, which the draft should then cite
instead), or mandate the computation explicitly with its own budget line, its own variable list
(`x_0 … x_5`), and an explicit labelled failure reason replacing `:338-339`. Do not leave §16.2
asserting that an artifact already exists when it does not — that is exactly the C0001 defect where
7 of §12.1's mandated artifacts were never written.

### MAJOR-5 — no input artifact is pinned by hash; the GPU_RUN5 source run is pinned by path only

**Anchor**: §3 (checkpoint SHA256 only); §16.1; §22's "compact statement of what is frozen".

The only SHA256 anywhere in the contract that pins an *input* is the checkpoint's. There is no
recorded digest for `phase2/validation.json`, `phase3/all_candidates.json` (181,594,403 bytes is
recorded — a size, not a hash), any of the 960 `phase3/cells/*.json`, or
`phase2/partB_in_support_systems.json` in the C0001 run. C0001 v2 mandated
`phase0/input_fingerprints.json` (`InstrumentedOpener.fingerprints()` exists for exactly this
purpose, `io_allowlist.py:165-176`); C0002 drops it and §16.1's artifact list does not include it.

Since the source run lives under a gitignored `results/runs/` tree, "pinned by path" is not a
provenance guarantee.

**Required change.** Mandate `phase0/input_fingerprints.json` written from
`InstrumentedOpener.fingerprints()`, listing every input path opened with its SHA256, and make
"every input digest matches the frozen value" a Gate-0 check. Record the digests of
`validation.json`, `all_candidates.json` and `partB_in_support_systems.json` in §3 at freeze time.

### MAJOR-6 — resume semantics are required by a gate but defined nowhere

**Anchor**: §11 Gate 5 "a reduced run on 24 cells completes end to end, writes a manifest, equation
records and failure records, **demonstrates resume**, and projects the full pass ...". That is the
only occurrence of the word in either file (`grep -i resum` over the `.md` and the `.json`).

Nothing in the contract defines: the **resume unit** (cell? cell × context? candidate?); the
**ordering rule** that the unit's record is appended only after the unit completes; how a partially
written `partI_candidate_records.jsonl` line is detected and discarded; how a restarted run avoids
**double-counting** an already-scored cell or **silently skipping** one; or which artifact holds the
completed-unit ledger. `§11`'s abort conditions explicitly contemplate restarts ("GPU 0 > 85 °C
sustained 60 s ⇒ pause, cool, **resume once**"; the VRAM fallback chain), so restarts are an expected
path, not an exceptional one.

C0001 v2.1 had an explicit "write-before-match ordering" requirement (`v2.1.md:2193`). C0002 has none.

**Required change.** Freeze: resume unit = one `(cell_id, scoring_context)` pair; a unit's records
are written and `fsync`ed, then and only then is its id appended to a `phase4/completed_units.jsonl`
ledger; on restart, units present in the ledger are skipped and any `partI_*` lines for units not in
the ledger are truncated; the endpoint denominators are computed from the ledger, not from line
counts. Make "ledger size == number of distinct units == number of record groups" a Gate-6 check.

### MAJOR-7 — NC-CONDITION: the cited evidence is misattributed, and provably-zero-Δ partners exist

**Anchor**: §10.3 NC-CONDITION "**Verified achievable**: C0001's own stored 960 `gt_logprob_sum`
values differ **between bundles of the same system** (e.g. `-159.50254821777344` /
`-160.61439514160156` / `-158.15951538085938` on `R01_validation_d101_000`)".

Read back from `phase3/partC_cell_records.jsonl`, those three values are:

```
R01_validation_d101_000_b0_n0_r0      -159.50254821777344
R01_validation_d101_000_b0_n0_r0p5    -160.61439514160156
R01_validation_d101_000_b0_n0p05_r0   -158.15951538085938
```

All three are **bundle 0**. They differ in `noise_sigma` / `subsample_rho`, not in bundle. The actual
across-bundle comparison at fixed corruption is:

```
R01_validation_d101_000_b0_n0_r0      -159.50254821777344
R01_validation_d101_000_b1_n0_r0      -159.50254821777344
R01_validation_d101_000_b2_n0_r0      -159.50254821777344
```

**byte-identical**. At `noise_sigma = 0, subsample_rho = 0` the three bundles produce the same
observed trajectory, so the conditioning is the same and `Δ = 0` exactly. This is systemic, not local:
`cell_input_payload_sha256` has exactly **10 distinct values per system on all 80 systems** (counted),
i.e. 12 cells collapse to 10 payloads because the three `n0_r0` cells share one.

Consequences:

- The stated achievability evidence for the control **does not support the control**.
- §10.3 says only "score the truth against an encoder pass built from a **different** cell's
  trajectory". It does not say *which* cell. If the partner may be drawn from the same system, a
  same-system `n0_r0` partner gives `|Δ| = 0` deterministically and the cell fails the `> 1 nat` bar.
  With uniform draws over 852 that is not a rare event.
- Even the corruption-grid differences the draft actually exhibits are 1.11 and 1.34 nats against a
  1-nat bar — a ~1.2× margin. That is the MAJOR-R6 shape C0001 nearly died of: a control whose
  observable ceiling is barely above its threshold.

**Required change.** Freeze the partner-selection rule as "a cell of a **different system**, drawn
with `CONTROL_CELL_SEED`", correct the evidence citation to a measured same-truth /
different-system pair, and state the observed Δ distribution that justifies the 1-nat bar. Do not
lower the bar.

### MAJOR-8 — the regression-identity evidence (§10.5, Gate 4) is mis-stated

**Anchor**: §10.5 "**Verified achievable**: C0001's `phase3/partC_instrument_test.json` records
`identity_error` in the range `7.3e-08 … 8.1e-07` on 960 cells, all below `1e-5`"; repeated in
§11 Gate 4 and in the JSON at `.controls.NC1_regression_identity.verified_achievable` and
`.gates.gate_4_controls.conditions[5].achievable_evidence`.

Read back from the artifact (960 `regression_checks` entries, `tolerance: 1e-05`, `ok: true`):

| statistic | draft | artifact |
|---|---|---|
| min `identity_error` | `7.3e-08` | **`0.0`** (17 entries are exactly zero) |
| max `identity_error` | `8.1e-07` | **`2.8991699210223487e-06`** |
| smallest non-zero | — | `1.2226593959496768e-08` |

The conclusion ("all below 1e-5") survives — the gate is still achievable, with ~3.4× margin rather
than the ~12× the draft implies. But a preregistration that quotes a measured range must quote it
correctly (rule 15's "numbers verbatim", rule 01 item 9), and both endpoints of the quoted interval
are wrong.

**Required change.** Correct both numbers in the `.md` and the `.json`, and state the realized
margin honestly.

### MAJOR-9 — every achievability measurement backing the gates was taken in `C_raw`, but the gates bind in `C_gen`

**Anchor**: §7.1 ("`C_gen` — ... **PRIMARY**"); §7.2 Gate 3 evidence column; §8.2 "**Verified
achievable**: exact round trip on **300 / 300** candidates over 6 cells (seed 12345)"; §10.2
"**Verified achievable, measured**: on a disjoint 10-cell probe (`random.seed(4242)`, **`C_raw`**)";
§11 Gate 4's whole "evidence it is achievable" column.

The draft's central methodological argument (§5.3, BA4) is that `C_gen` and `C_raw` are materially
different instruments whose disagreement would make the cycle `conditioning_sensitive`. It then backs
every gate threshold with a `C_raw` (or original-unit) measurement:

| gate condition | binds in | measured in |
|---|---|---|
| Gate 3a/3b (71/71, ≥ 2 distinct) | both contexts ("per context") | `rtol = 1e-3` numeric check on original-unit infix; 3a's corroboration is C0001, i.e. `C_raw` |
| Gate 4 PC-GREEDY ≥ 2/40 | unspecified (see below) | explicitly `C_raw` |
| §8.2 re-encoding round trip ≥ 0.90 | both | stored `candidate_formula_canonical`, i.e. original units |
| Gate 4 "`C_gen` reconstruction ≥ 0.98" | `C_gen` | float map, see below |

Additionally, **PC-GREEDY's own context is never stated.** It is the one hard abort on the primary
(§10.2, §11 Gate 4, §13), so the context it runs in is a frozen design parameter and is missing.

The specific reason `C_raw` evidence does not transfer: under `C_gen` every scored sequence carries
constants multiplied by `scale[d]/a_t` and variables divided by `scale[j]`, i.e. arbitrary reals. The
encoder quantizes every constant to **4 significant digits** — read from the checkpoint:
`env.params.float_precision = 3`, `float_descriptor_length = 3`, and
`odeformer/envs/encoders.py:124` is `(f"%.{precision}e" % value).split("e")` producing
`[sign, "N<4 digits>", "E<exp>"]`. So a `C_gen` encode→decode round trip is accurate to ~1e-4, not
1e-8, and §8.2's "exact" canonical-string comparison is a materially harder test in `C_gen` than the
300/300 measured in original units. If the realized `C_gen` mismatch rate exceeds 10% on more than
10% of cells, §8.2 and §13 make the primary `undecidable` — a live risk with zero evidence either way.

Finally, **Gate 4's "`C_gen` reconstruction" check is vacuous as written**: "forward map + inverse
recovers the original to 1e-8 relative" tests that the closed-form map is invertible in floating
point. Any invertible map passes. It does not test that the scaled-unit expression is the one the
decoder emitted, and it cannot see the tokenizer quantization because it never goes through the
tokenizer.

**Required change.** (a) State PC-GREEDY's context explicitly and measure its achievability there.
(b) Re-express Gate 4's `C_gen` reconstruction condition as a **round trip through
`env.equation_encoder.encode` / `.decode`**, with a numeric-agreement tolerance appropriate to
4-significant-digit constants, and a measured achievability figure. (c) Label every `C_raw`-derived
achievability figure in §7.2/§8.2/§10.2/§11 as `unverified for C_gen`, or measure it in `C_gen`
before freezing.

### MAJOR-10 — under `C_gen`, `e1` cannot be the stored `tree_encoded`, which undermines Gate 3b

**Anchor**: §7.2 "Frozen enumeration `E(s)` per in-support system `s`, **per context**: `e1` = the
stored `tree_encoded` from `phase2/validation.json` (prefix-derived); `e2` = `infix_to_model_tokens(env,
teacher_infix)` (infix-derived)"; §7.1 "Every scored sequence is expressed in **scaled** units by the
closed-form forward map".

`tree_encoded` is a token list in **original** units (verified present in `validation.json`'s row
schema). To score it in `C_gen` it must be decoded to a tree, scaled by the forward map, and
re-encoded — which is precisely `e2`'s `sympy → sympy_expr_to_tree → equation_encoder.encode` path.
The `e1` / `e2` distinction that Gate 3b's "**≥ 2 verified and distinct** encodings" rests on is a
*prefix-derived versus infix-derived* distinction that plausibly collapses once both go through the
same encode step in scaled units. The draft's own 3b evidence ("Token lengths differ (e.g. 25 vs 24,
27 vs 30, 29 vs 30)") is an original-unit measurement.

**Required change.** Specify the exact procedure that produces `e1` in `C_gen`, and measure 3b in
`C_gen` before freezing. If `e1` and `e2` coincide in `C_gen`, Gate 3b must rest on orbit members
alone and its 90% bar needs a fresh achievability check.

### MAJOR-11 — the `C_gen` forward map assumes `rescale_function` was always applied; two silent early-return paths say otherwise

**Anchor**: §7.1 step 4 "the exact inverse of `Scaler.rescale_function`"; F-g / F-h.

`third_party/odeformer/odeformer/model/utils_wrapper.py:54-80 rescale_function` returns the tree
**unchanged** in two branches:

```
56:  if len(nodes)>len(scale):
57:      return tree
...
67:      if dim>=len(scale):
68:          return tree
```

The second fires whenever a candidate references a variable index `≥ dim` — a hallucination ODEFormer
can emit (`max_dimension = 6`, read from the checkpoint, against 1–3-dimensional GRN systems). And
`sklearn_wrapper.py:166-167` is

```
166:  try: candidate = self.model.env.simplifier.simplify_tree(candidate)
167:  except: pass
```

a bare `except: pass`, so for any candidate whose simplification raised, the stored
`candidate_formula_raw` is the un-simplified rescaled tree.

The draft's forward map is applied uniformly to every stored candidate on the assumption that every
one of them is the `rescale_function`-then-`simplify_tree` image of a scaled-unit tree. For the
early-return candidates that assumption is false and the map would **doubly transform** them,
producing a silently wrong `lp_best` contribution. Whether any in-support candidate actually hits
those branches is **unverified** — I did not evaluate it, and the draft does not either.

**Required change.** Add a Gate-4 / per-candidate check that detects the early-return case (e.g.
assert every candidate's free symbols are within the system's dimension before applying the map), and
label the excluded rows with an explicit `failure_reason` per rule 03 rather than transforming them.

### MAJOR-12 — the `H0010` corpus is not frozen to a support, and the falsifier is a hard count

**Anchor**: §4's `H0010` row "exhaustive over realized candidate component strings and their
classes"; §9.2 "End-to-end from the durable artifact `.../phase3/all_candidates.json`"; §9.3
falsifier "`n_class_joint ≥ 6`".

`all_candidates.json` holds all **47,987** validation candidates over **80** systems (verified). The
primary endpoint is restricted to the **71** in-support systems / 42,593 candidates. §9 never says
which corpus `H0010` uses. The difference is 5,394 candidates from 9 systems — and the decision rule
is an integer comparison at 6, not an interval, so including or excluding them can flip the verdict.

This is an unfrozen researcher degree of freedom in a confirmatory count, which rule 01 item 3 exists
to prevent.

**Required change.** Freeze the corpus explicitly (recommend: all 47,987, since `H0010` is about
*generation coverage* and support is a property of the truth, not of what the decoder generated), say
so in §4, §9.2 and §22, and report the other corpus as a preregistered sensitivity.

### MAJOR-13 — no Go/No-Go stops the one unmeasured cost component before it is spent

**Anchor**: §14 "**The `H0010` census is the only unmeasured component.** Its budget is bounded by the
`count_ops` admission rule and by the ≤ 12 CPU core-h Gate-5 projection bar"; §11 Gate 2, Gate 5.

Gate 5 is the **smoke** gate and its projection bar concerns the 852-cell GPU pass. Gate 2 is the
`H0010` census itself, budgeted at "≤ 8" of the 12 projected CPU core-h, and §11 fixes **no execution
order** between them. So the sentence "bounded by the Gate-5 projection bar" does not describe a
mechanism: nothing runs before the census that could stop it. The only protection is the global
24 core-h abort, i.e. the budget is protected by spending it.

MAJOR-2 compounds this: `count_ops` cannot bound the parse, so "bounded by the `count_ops` admission
rule" is also not a mechanism for the dominant cost.

**Required change.** Add a Gate-2a: run the census on a preregistered random subsample (e.g. 5,000 of
the ~89,349 component strings, `GLOBAL_SEED`), record wall time, and require the linear projection to
be ≤ 8 CPU core-h before the full census runs; above it, invoke RD3. Freeze the execution order of
gates 0→1→2a→2→3→4→5→(852-cell pass)→6 in §11, as C0001 v2.1 §7.10 did.

### MAJOR-14 — several Gate-4 and Gate-3 failure dispositions do not exist, so the gates are not machine-checkable

**Anchor**: §11 Gate 4 "**Every other Gate-4 failure is reported and downgrades the affected endpoint
per its own rule**; none of them silently proceeds."

Checking each: PC-GREEDY has a rule (hard abort). `C_gen` reconstruction has one (§18's named
contingency). PC-HOLDOUT, NC-HOLDOUT, NC-CONDITION, PC/NC-H0010, the regression identity and the
control-cell re-encoding round trip **have no stated consequence anywhere** — §10 gives their
thresholds but no disposition, and §13's `undecidable` list mentions none of them. The same holds for
Gate 3c (§15 says only "≤ 20% or Gate 3c fails", and what a 3c failure does is never stated except
transitively through Gate 6 — which CRITICAL-2 shows is itself contradictory).

R7 requires the check to quote the contract verbatim. There is no contract text to quote.

**Required change.** Give every Gate-3 and Gate-4 condition an explicit, single-clause disposition
(abort / downgrade-with-named-qualifier / report-only), in one table, and make Gate 6 consult only
the abort-class conditions.

---

## MINOR

1. **§16.2 does not say the rule-03 fields are copied rather than recomputed.** Every mandated field
   (`candidate_formula_raw/canonical/skeleton`, `candidate_exponent_aware_skeleton`, `canonical_exact`,
   `skeleton_exact`, `exponent_aware_skeleton_exact`, `component_exponent_aware_skeleton_exact`,
   `ted_raw`, `ted_skeleton`, `normalized_ted`, `normalized_variable_aware_ted`,
   `variable_aware_ted_definition`, `complexity`, `valid`, `failure_reason`, `trajectory_metrics`)
   is present in the stored 24-key schema, and `true_formula` / `true_prefix` / `tree_encoded` /
   `variable_to_gene` are present in the cell and `validation.json` rows (all verified). Say
   explicitly that they are copied with provenance and **not** recomputed — otherwise an implementer
   runs `symbolic_recovery` 42,593 times, which reintroduces the 10 s `SIGALRM` into the run and puts
   MAJOR-3 immediately in play.
2. **PC-GREEDY compares unequal spellings.** `lp_greedy` scores the model's own emitted token ids;
   `lp_best` scores re-spellings (F-h). Correct for a positive control, but §10.2 should say so, and
   the `lp_best_is_respelling: true` flag should be accompanied by `lp_greedy_is_respelling: false`.
3. **§10.2 cites `seed=0`; the code uses `seed=self.generation_seed`** (`model_wrapper.py:80`).
   Immaterial at `sample_temperature=None`, but the citation should match. The substantive claim —
   "the greedy pass `ModelWrapper` itself always runs" — is **correct**: `:74-81` is unconditional,
   before the `beam_type` branch at `:101/:140`.
4. **F-f cites `sklearn_wrapper.py:172`; the call is at `:173`** (`:171` is `if sort_candidates:`).
   The substance is verified: `sort_metric="r2"` is passed explicitly at
   `src/gpu_run4/inference.py:202,242`, `sort_candidates` is at `:205-228` with `descending = True`
   for `"r2"`, and it ranks on `times[input_id], trajectories[input_id]` — original units.
5. **§2.4's "`sealed_paths_read == []`" is weaker than it reads.** It is a computed property of
   `InstrumentedOpener` over paths opened *through it*; the `sys.addaudithook` guard **raises** rather
   than accumulating, and reads not routed through the opener (e.g.
   `gpu_runclaude1_c0001_phase3_partc.py:266`'s direct `read_text` of
   `partB_in_support_systems.json`) are invisible to it. `io_allowlist.py`'s own docstring states
   this caveat; §2.4 should carry it too.
6. **§12.2 declares Holm over `{P1, P2}` but no decision rule uses a p-value.** §13's criteria are
   all interval bounds. Holm never enters any decision. Flagged and deferred to the concurrent
   statistical review.
7. **Disclose the replicate structure of the 852 cells.** For each system the three bundles at
   `noise_sigma = 0, subsample_rho = 0` share one `cell_input_payload_sha256` (10 distinct payloads per
   12 cells, on all 80 systems — counted), so 213 of the 852 in-support cells are 71 conditionings
   replicated 3×, and `lp_gt` is identical on them. `sb_rate(s)` averages them as if they were 12
   independent cells. Not a defect, but §2.1 should say it, and it explains Gate 1's otherwise
   unmotivated "10 distinct payloads per system" check.
8. **§14's `< 1 GiB` new-disk projection is not derived.** `partI_candidate_records.jsonl` at
   42,593 candidates × 2 contexts, each carrying the full §16.2 schema plus per-token log-probabilities
   and ranks, is plausibly several GiB. Show the arithmetic.

## NOTE

- `GPU_RUNclaude1/research_state.md`'s header still reads `status: C0001 in progress` /
  `current_cycle: C0001`, while its own §"C0002 の進行状況" records C0002 at Stage 3. Rule 12 requires
  `research_state.md` to be resumable-from at any moment; the header should track the body.
- §14's GPU arithmetic checks out: 960/8 × 7.0 s = 0.233 GPU-h; 852 cells × 2 contexts = 0.414 h;
  orbit members 9/51 × 0.414 = 0.073 h; 0.07 s × 42,593 × 2 = 1.66 CPU core-h. The GPU cost basis is
  a genuine measurement, honestly separated from the projection, and the one unmeasured component is
  named as such (§14, §21). The defect is the missing gate (MAJOR-13), not the arithmetic.
- §0.3's self-reported leakage disclosure, the choice to keep the 8 cells in the corpus rather than
  excluding them post hoc, and the `C_gen`-is-primary containment are all handled correctly from a
  provenance standpoint. Whether the inherited-threshold defence is adequate is the statistical
  reviewer's question, not this audit's.
- §21's list of things "found unimplementable, or implementable only in a weaker form" is the right
  instinct and should be preserved through the revision, with MAJOR-2's three additions folded in.

---

## Answers to the four specific questions asked

**Does the `CAS_NODE_BUDGET = 400` admission bound make the label load-independent?** **No.** The
budget bounds admission, not termination (§21 item 1 concedes this), and additionally: `count_ops` on
the string inputs the real call sites use (`partc_reencoding.py:103`, `equation_metrics.py:174,183`)
sympifies internally, so the parse is paid before the budget can apply and is itself unbounded;
`_timed_simplify(sympify(...))` evaluates the parse **outside** the `_time_limit` guard; and
`count_ops` is not monotone with the runtime of `cancel`/`simplify` on rational functions. The wall
clock therefore still decides in the tail, which is why Gate 6's `wall_clock_guard_fired == 0` is
both load-dependent and unevidenced (MAJOR-2, MAJOR-3).

**Does the SymPy seed reach every worker and close the RNG mechanism?** It reaches every worker as
written, but it **does not close the mechanism**. `sympy.core.random.rng` is one module-level
generator per interpreter; seeding it once at worker start fixes its state at `t = 0`, while the state
at any given comparison is advanced by every RNG-consuming call that worker happened to handle first —
and that assignment is load-dependent under any availability-scheduled pool. Demonstrated directly in
the pinned 1.13.1. The fix is a deterministic **per-item** reseed keyed on the input, plus an explicit
`multiprocessing` start method (on which the firewall guards' inheritance also silently depends)
(MAJOR-1).

**Is the corrected selection-rule citation right?** **Yes, fully verified.**
`src/evaluation/gpu_run5_selection.py:11` is a cross-run 4-tuple model-selection key grouping by
`(system_id, seed)` that never indexes a candidate; a different single-argument
`formula_selection_key` exists at `src/gpu_run5/evaluation.py:143`; and the real per-cell selector is
`src/gpu_run5/evaluation.py:107 select_candidate`, whose `"official_reconstruction"` branch is
`return 0` at `:111-112`. The draft cites the module path, not the bare name, as it requires.

**May the draft be frozen as written?** **No.** Three CRITICAL findings each independently block it:
the primary indicator does not support the certificate language the contract makes binding
(CRITICAL-1); Gate 3b has two contradictory dispositions, reproducing the C0001 Gate B→C defect
(CRITICAL-2); and §16.1 reinstates the unguarded `run_manifest.py` directory fingerprint that C0001
v2.1 explicitly forbade, in a subprocess where the sealed audit hook is not installed (CRITICAL-3).
No CRITICAL or MAJOR here is resolved by relaxing a threshold, a cap or a seed, and none is proposed
that way. A `v1.1` addressing CRITICAL-1/2/3 and MAJOR-1 through MAJOR-14, with the `C_gen`
achievability measurements actually taken in `C_gen`, would in this reviewer's judgement be
freezable — the design's evidentiary discipline is otherwise the strongest in this campaign so far.
