# C0001 — Stage 5 Reproducibility and Leakage Audit

| field | value |
|---|---|
| cycle | `C0001` |
| stage | 5 (reproducibility audit, pre-implementation) |
| object of audit | `GPU_RUNclaude1/plans/C0001_preregistration.md` + `.json` (FROZEN) |
| branch | `20260909_researce_GPU_RUNclaude1` (correct) |
| HEAD at audit | `7cfc0ff63b0bfd2c0339d76260b1437611a0e970` |
| working tree | clean (`git status --short` empty) |
| auditor role | `lansr-reproducibility-auditor`, distinct from methodologist and implementer |
| date | 2026-09-09 |
| **verdict** | **`AMEND_BEFORE_IMPLEMENTATION` — blocking. 4 CRITICAL findings.** |

Every finding below is grounded in a file read or a command run in the `lansr310` environment on
this machine, not in what the preregistration says about itself. Measurements are reproducible from
the snippets given.

**Note on HEAD.** The audit brief states HEAD should be `bfbf727`. During this audit the supervisor
committed `7cfc0ff` ("Freeze C0001 preregistration; retract erroneous Hill-4 claim"), which is the
commit that actually introduces the preregistration. See MIN-1.

---

## 1. CRITICAL findings

CRITICAL blocks the full experiment (rule 07). All four are fixable by amendment; none requires
abandoning the cycle. Two of them (CRIT-1, CRIT-2) alter frozen text and therefore need supervisor
amendment via `DEVIATION-nn`, not an implementer decision.

---

### CRIT-1 — Gate A→B requires M0 to reproduce a comparator value that is factually wrong; a *correct* implementation must fail it

**Evidence.**

`C0001_preregistration.md:269` (comparator table):

```
| **C-M0c** frozen string matcher, component level | 0/2040 | comparator for the component-level secondary |
```

`C0001_preregistration.md:731` (Gate A→B):

```
(i) the M0 arm **reproduces C-M0 exactly** (system-level 0.0 over 960 cells and 0/2040
component level) — a non-reproduction means the harness is wrong and everything downstream is void;
```

The stored value is **107/2040, not 0/2040**. From
`results/runs/gpu_run5_20260823_ddd267b0/phase3/beam_groups.json`, field
`component_true_exponent_aware_skeleton_in_beam`:

```
flattened component-in-beam over 2040 entries: {False: 1933, True: 107}
true_exponent_aware_skeleton_in_beam: {False: 960}          <- system level 0/960 is correct
```

Independently recomputed from `phase3/all_candidates.json`, field
`component_exponent_aware_skeleton_exact`, by OR-ing over candidates per (cell, component-index),
**with no `neg` folding of any kind**:

```
recomputed (cell,component) slots: 2040
raw STRING-matcher component-in-beam TRUE: 107
agreement between recomputed-from-raw-field and stored beam_groups: 2040/2040
IDENTICAL: True
stored raw component-in-beam hits by family: {'R04': 56, 'R07': 17, 'R08': 34}
```

The per-candidate field itself carries 2,235 component hits out of 101,963 component comparisons.

**Defect.** The comparator of record for the component-level secondary is misstated by the
preregistration. Gate A→B (i) then demands that M0 reproduce a number the frozen matcher never
produced. A correct M0 returns 107/2040 and trips the gate; `C0001_preregistration.md:966`
(DEVIATION contingency 6) then applies:

```
6. **M0 fails to reproduce C-M0 = 0.0.** This is a harness defect, not a finding. Halt, diagnose,
   and if unresolved, the entire cycle is `undecidable`
```

**Consequence.** As frozen, the cycle self-destructs at its first gate: a correctly implemented
harness is declared defective and no C0001 endpoint may be reported. Conversely, an implementer who
"fixes" the harness until it returns 0/2040 will have tuned the instrument to a wrong target — a
rule-01 item 3 violation reached by following the plan.

**Required fix.** Amend `C0001_preregistration.md:269` to `C-M0c = 107/2040 = 0.0525` and
`:731` Gate A→B (i) to require reproduction of *system-level 0/960 and component-level 107/2040*.
Also correct §9.1's "M0 is 0 for all 80 systems" — true at system level, false at component level,
which matters because A-S3's comparator is component-level.

---

### CRIT-2 — The `neg`-asymmetry finding that motivates E0's component-level support is a representation-mixing artifact, not a matcher property

**Evidence.** `phase3/cells/*.json:true_structure.exponent_aware_skeleton` is derived from the
**prefix**, while the frozen matcher derives both sides from the **infix**. Measured over all 960
validation cells:

```
stored true_structure reproduced from  true_formula (INFIX) : 0/960
stored true_structure reproduced from  true_prefix  (PREFIX): 960/960
```

Concretely, for `R01_validation_d101_000_b0_n0_r0`, truth
`0.1954 + 0.8878 * x_0 * 1/(0.8392 + x_0) + -1 * 0.3968 * x_0`:

```
stored true_structure['exponent_aware_skeleton']
  = 'add,add,CONST,mul,mul,CONST,inv,add,CONST,x_0,x_0,neg,mul,CONST,x_0'     <- has neg
classify_formula(true_formula)['exponent_aware_skeleton']
  = 'add,add,CONST,mul,CONST,x_0,mul,mul,CONST,inv,add,CONST,x_0,x_0'         <- no neg, reordered
```

Every one of the 960 stored truth skeletons contains `neg`; recomputing from the infix loses it in
960/960 cases (sympy folds `-1 * 0.3968` into a signed coefficient and reorders `Add` args). The
candidate skeletons in `all_candidates.json` are infix-derived (`scripts/phases/gpu_run5_phase3.py:122`
→ `formula_metrics(row["teacher_infix"], raw)` → `src/gpu_run5/evaluation.py:41`).

So `C0001_exploratory_neg_canonicalization.md:16-18`, which compares stored *prefix-derived* truth
skeletons (`neg` 960/960) against *infix-derived* candidate skeletons (`neg` 1,541/47,987 = 3.2% —
this count I confirm), is comparing two incompatible fields.

**What follows.** The exploratory document's central table row
(`C0001_exploratory_neg_canonicalization.md:44`) reads:

```
| per-component truth-in-beam | **0 / 2040 = 0.0000** | **107 / 2040 = 0.0525** |
```

The "raw = 0/2040" column is the mixed-representation artifact. The "`neg`-normalized = 107/2040"
column is **GPU_RUN5's own published raw value**, already stored in `beam_groups.json` (CRIT-1). The
`neg` folding recovered nothing; it merely undid the representation mismatch. Therefore
`C0001_exploratory_neg_canonicalization.md:57-58` —

> "107 of 2040 components (5.25%) are structural matches that the frozen string matcher scored as
> complete misses"

— is **false**. The frozen string matcher scored exactly those 107 as matches.

**Consequence — five places in the frozen plan lose their basis:**

1. `:35` P4 ("`neg` node present in truth exponent-aware skeletons 960/960 vs 1,541/47,987
   candidates") compares incompatible fields; the asymmetry does not exist within the frozen matcher.
2. `:133` — E0's status "partially confirmed at component level (P6)" is unsupported. There is no
   component-level evaluator artifact.
3. `:270` — the C-NEG comparator row attributes GPU_RUN5's published raw value to a new exploratory
   instrument, and calls it "a *lower bound* on what a proper canonicalizer should find".
4. `:104`, `:410`, `:413` — §7.6's expected direction `A-S3 ≥ 0.0525` and its matcher-defect
   protocol are premised on 0.0525 being a *neg-folder* result. Correctly understood, 0.0525 is
   M0's own component rate, so the condition reduces to plain monotonicity `M0 ⊆ M3`. The
   requirement survives; its stated rationale does not.
5. `:101` — the mandated `prior_information_disclosed` string cites
   `C0001_exploratory_neg_canonicalization.md:107/2040=0.0525` as exploratory prior information.
   The number is a *published GPU_RUN5 comparator*. This is an integrity improvement (it was never a
   discovery) but the provenance record is wrong and §0.3's disclosure regime must be re-grounded.

**Required fix.** Amend §0 (P4, P6), §1.1 (E0 status), §4 (C-M0c, C-NEG), §7.6 and §0.3 to record
that 107/2040 is the frozen matcher's own component-level value; retract the "scored as complete
misses" claim in the exploratory analysis with a dated correction (as was correctly done for the
Hill-4 claim in `7cfc0ff`); and re-derive whatever E0 support remains from the *system* level only.
§7.2 must additionally pin the representation fed to `classify_formula` (see the constructive
finding in §4 below), or this exact bug recurs inside Part A.

---

### CRIT-3 — M2's CAS arm cannot return a match for half the corpus, and no diagnostic in the plan can see it

**Evidence.** `src/gpu_run4/formulas.py:427-438`:

```python
def _sympy_components_equal(true_components, pred_components) -> tuple[float, str | None]:
    ...
    nodes = sum(tree_size(tree) for tree in true_components) + sum(tree_size(tree) for tree in pred_components)
    if nodes > SYMPY_MAX_NODES:
        return 0.0, None                    # <-- silent non-match, NO failure reason
```

`src/gpu_run4/ted.py:15`: `SYMPY_MAX_NODES = int(os.environ.get("LANSR_SYMPY_MAX_NODES", "40"))`.
The budget is the **combined** truth + candidate node count, and GRN truths are the largest trees in
the corpus. Measured truth-side totals over the 80 validation systems:

```
min 10  median 25  mean 26.2  max 48       (R07 median 48; 6/10 R07 truths alone exceed 40)
```

Asked whether a GRN truth is equivalent to **itself**, through the CAS path with the M1
short-circuit removed:

```
_sympy_components_equal returns 1.0 : 28/80
pairs exceeding SYMPY_MAX_NODES=40  : 52/80
  R01 10/10   R02 10/10   R03 4/10   R04 4/10   R05 0/10   R06 0/10   R07 0/10   R08 0/10
```

Over 3,000 randomly sampled real (truth, candidate) pairs:

```
EXCEED SYMPY_MAX_NODES=40 -> silent 0.0 non-match with failure_reason=None: 1652/3000 = 55.1%
  R01 0.0%  R02 0.0%  R03 33.0%  R04 14.5%  R05 92.9%  R06 100.0%  R07 100.0%  R08 100.0%
```

**Defect.** M2 (`C0001_preregistration.md:348`, `compare_formulas(..., skip_cas=False)["symbolic_equivalent"]`)
is structurally incapable of returning a match for R05–R08 — half the corpus, and precisely the
multi-component nontrivial-Hill families. The rejection is returned as a plain non-match with
`failure_reason = None`.

**Every guard in the plan is blind to it:**

- **N5** (`:647`) budgets `cas_timeout + ParseError + SymbolicEquivalenceTimeout < 2%`. Node-cap
  rejections carry none of those labels, so N5 reports ≈0% failure and **passes**.
- **§7.3 monotonicity** (`:362`) expects `M0 ≤ M1 ≤ M2 ≤ M3` as sets. `M1 ⊆ M2` holds by
  construction because `compare_formulas` short-circuits `symbolic = 1.0` whenever
  `canonical_exact == 1.0` (`formulas.py:492-493`); `M2 ⊂ M3` is the *expected* direction. A
  spuriously empty M2 is monotonicity-**consistent** and raises no violation.
- **§14 contingency 1** (`:934`) handles only labeled timeouts.
- **§7.2** (`:348`) describes M2 as "internally timeout-guarded `simplify(T_i − C_i)`, then
  `T_i.equals(C_i)`, then `numeric_equivalent(...)`" — it does not mention the node cap or the
  `canonical_exact` short-circuit at all. The plan's description of its own instrument omits the
  mechanism that breaks it.

**Consequence.** Part A would report M2/A-S1 = 0/80, N1–N6 all pass, `null_credible`, with every
diagnostic green — while ~55% of M2 comparisons were never performed. This is exactly the silent
bias in favour of the preregistered null that a null-shaped primary cannot tolerate. The primary
endpoint is M3, which has no node cap (see OK-8), so the primary itself survives; but N1 and N5,
which the plan makes the *preconditions for admitting a null at all* (`:637-655`), are compromised,
and the M2 secondary is void.

**Required fix.** (a) Give the node cap its own recorded outcome: return a distinct
`failure_reason` (e.g. `SymbolicNodeCapExceeded`) and add it to the N5 failure budget and to A-S7.
(b) Do not raise `LANSR_SYMPY_MAX_NODES` silently — it is part of the frozen instrument
(`:353` "No timeout value is changed by C0001"). Either preregister an explicit, justified cap
sufficient for GRN (truth max 48 → a combined cap of ≥ 200 covers the observed range) and record the
deviation, or declare M2/A-S1 `not_measurable_from_stored_artifacts` for R05–R08 and drop A-S1 from
the S1 Holm family. (c) Recompute the compute ceiling if the cap is raised — see MAJ-4.

---

### CRIT-4 — PC1, the plan's hard abort control, does not exercise the code path it is supposed to validate

**Evidence.** `src/gpu_run4/formulas.py:492-497`:

```python
    symbolic = 0.0
    symbolic_failure = None
    if metrics["canonical_exact"] == 1.0:
        symbolic = 1.0                       # <-- CAS is never called
    elif not skip_cas:
        symbolic, symbolic_failure = _sympy_components_equal(...)
```

PC1 injects the truth as its own candidate (`C0001_preregistration.md:380`), so
`canonical_exact == 1.0` always holds and the CAS arm is bypassed. Measured:

```
PC1 (inject the truth as its own candidate) over 80 validation systems
  M1 canonical_exact      : 80/80
  M2 symbolic_equivalent  : 80/80   <-- prereg N1 requires 80/80  (PASSES)
  M3 skeleton (all comps) : 80/80   <-- prereg N1 requires 80/80  (PASSES)
```

versus the same 80 inputs through the CAS path directly: **28/80**.

**Defect.** PC1's M2 pass is entirely attributable to the M1 short-circuit. N1 (`:641`,
"PC1 sensitivity = 80/80 for M1, M2 and M3") is therefore **vacuous for M2** and cannot detect
CRIT-3. This is the failure mode the audit brief names: a control that bypasses the cascade proves
nothing. `C0001_preregistration.md:380` calls PC1 failure grounds to "abort Part A" — the plan
places its strongest safety interlock on a test that cannot fail.

**Consequence.** The plan's own stated precondition for admitting a null ("this is what makes a
null admissible", `:373`) is not met for the M2 arm, and the plan cannot tell.

**Required fix.** Add a mandatory **PC0 cascade-bypass control**: assert
`_sympy_components_equal(truth, truth) == 1.0` for all 80 systems *directly*, bypassing
`compare_formulas`, so the CAS arm is exercised on the endpoint corpus. Preregister its threshold at
80/80 and add it to N1. (This control fails at 28/80 today, which is the point — it is the test that
detects CRIT-3.) Independently verify that PC2a–PC2d are not also short-circuited by
`canonical_exact`; any control whose rewrite canonicalizes back to the truth cannot test M2 either.

---

## 2. MAJOR findings

MAJOR must be resolved, downgraded, or explicitly reported (rule 07).

### MAJ-1 — M3, the primary endpoint's matcher, is not uniquely specified

`C0001_preregistration.md:349` and `.json:matcher_cascade[3].implementation`:

```
src/evaluation/equation_metrics.py:169 symbolic_recovery(T_i_infix, C_i_infix)["skeleton"],
plus :68 _approximately_equivalent(rtol=1e-6) at the fitted constants, plus :153 to_skeleton
```

"plus" is not a composition rule. Verified against the code: `_approximately_equivalent` is private
and has exactly one call site, inside `symbolic_recovery` at `equation_metrics.py:203`, reachable
only through the `["equiv"]` key; `to_skeleton` is called internally to compute `["skeleton"]`.
`symbolic_recovery` returns four keys (`:207-212`): `exact`, `skeleton`, `equiv`,
`recovery = max(exact, skeleton, equiv)`. Three readings of M3 are available and they give different
rates. The **primary endpoint of the cycle** is therefore not determined by the preregistration.

There is also a hidden fallback at `equation_metrics.py:204`:

```python
        except Exception:
            equiv = skeleton  # fall back
```

which silently substitutes one criterion for another — material only if M3 = `["equiv"]`.

**Fix.** Pin M3 to exactly one key. `["skeleton"]` is the reading consistent with the "matched
constants (structural)" definition at `:349` and is what I validated in OK-8; state it explicitly
and delete the "plus ..." clause from both the `.md` and the `.json`.

### MAJ-2 — `run_manifest.py --data-path` recursively byte-reads all three sealed artifacts, including the only UNSPENT seal

`scripts/ops/run_manifest.py:28-33`:

```python
def tree_sha256(path: Path) -> dict:
    files = [path] if path.is_file() else sorted(p for p in path.rglob("*") if p.is_file())
    ...
        digest.update(sha256(file_path).encode("ascii"))
```

and `:119`: `"data_fingerprints": [tree_sha256(path) for path in args.data_path]`.

`sha256()` at `:16-21` opens and reads the file. So `--data-path results/runs/gpu_run5_20260823_ddd267b0`
opens `phase2/sealed_test.json` (7,676,469 B), `phase2/sealed_family_holdout_test.json`
(2,348,312 B) and `phase4/sealed_official_test.json` (11,829,142 B) — the campaign's **only clean
seal**. All three are present and confirmed on disk.

This is not a hypothetical standard. GPU_RUN5's own phase 8 treats precisely this operation as the
test-open event, `scripts/phases/gpu_run5_phase8.py:1171-1176`:

```python
    ledger = claim_test_open(out / "test_open_ledger.json", freeze_sha256=..., sealed_paths=sealed_paths)
    # The sole open event is durably recorded above.  Only now may sealed bytes
    # be hashed or deserialized.
    sealed_hashes = {view: sha256_file(Path(path)) for view, path in sealed_paths.items()}
```

`C0001_preregistration.md:821` mandates `run_manifest.py` for every manifest but never specifies
`--data-path`, while `:224-226` mandates `sealed_paths_read: []` in every phase manifest — a record
that would be false.

**Fix.** Preregister `--data-path` as an explicit **file-level allowlist** (`phase2/train.json`,
`phase2/validation.json`, `phase3/all_candidates.json`, the enumerated `phase3/cells/` files,
`phase4/fixed_grn_validation_panel.json`, `phase1/candidates_annotated.json`), never a directory
that contains a seal. Additionally add an assertion in C0001 code that no opened path matches
`sealed*`, and make `sealed_paths_read` a *computed* record from an instrumented opener rather than a
hardcoded `[]`.

### MAJ-3 — The real glob hazard is `phase2/` and `phase4/`, not `phase3/cells/`

The Part A glob is **safe**, verified exhaustively:

```
phase3/cells/  total: 960   validation-named: 960   test-named: 0
glob *_validation_*.json count: 960     distinct split tokens: {validation}
families: R01..R08 x 120 each
all_candidates.json split values: Counter({'validation': 47987})
```

But the seals sit in the same directories as files C0001 legitimately reads:

```
phase2/: audit.json config_snapshot.json family_holdout_train.json family_holdout_validation.json
         go.json manifest.json rejections.json sealed_family_holdout_test.json sealed_test.json
         train.json validation.json
phase4/: ... fixed_grn_validation_panel.json ... sealed_official_test.json ...
```

Gate 0 item 7 (`:726`) reads `phase4/fixed_grn_validation_panel.json` for the Stage-6 smoke — a
sibling of the unspent seal. Any `phase2/*.json` or `phase4/*.json` glob hits a seal.

**Fix.** Preregister explicit filename allowlists for `phase2/` and `phase4/` plus an assertion that
no resolved input path matches `sealed*`. Keep the `phase3/cells/*_validation_*.json` glob but add
`assert len(files) == 960` and the same `sealed*` assertion, so the guarantee is content-checked
rather than path-shaped.

### MAJ-4 — Part A compute is 6× the preregistered calibration and already exceeds its own allocation; fixing CRIT-3 breaches the cycle ceiling

Measured M1+M2+M3 cascade on 150 randomly sampled real GRN candidates in `lansr310`:

```
total 119.3 s -> mean 795 ms/candidate, median 604 ms
projection for 47,987 candidates: 10.60 single-core-hours
mean ms by family: R01 953  R02 390  R03 1269  R04 399  R05 658  R06 1077  R07 871  R08 604
```

Against P11 (`:42`, 129 ms/candidate → "≈1.72 single-core-hours") and §11 (`:803`, "Part A ≤ 8"
core-hours with a claimed "4.7× margin"): the measurement is **6.2× the calibration** and **10.6 h
already exceeds the 8 h allocation**, before the control battery, the M0 arm and the monotonicity
audit. The plan half-anticipates this (`:200-202`, calibration used ODEBench not the endpoint
corpus) but kept the 4.7×-margin claim.

Worse, these timings are taken **with the node cap short-circuiting R05–R08**. Fixing CRIT-3 pushes
those four families into full `simplify()` on 40–90-node trees at up to `SYMPY_EQUIV_TIMEOUT_SEC = 10 s`
each. Worst case ≈24,000 candidates × 10 s ≈ **66 core-hours**, 2.75× the 24-core-hour cycle
ceiling — a rule-06 hard stop requiring human approval.

**Fix.** Invoke the preregistered reduced design (`:958`, `bundle_index == 0`, 320 cells ≈ 16,000
candidates → ≈3.5 core-h) **before** starting, as §10.2 (`:767`) already requires, and re-derive the
Part A budget from a GRN smoke measurement rather than P11. Explicitly cost the CRIT-3 fix: if the
raised node cap projects over 24 core-hours, that is a ceiling decision for the supervisor, not an
implementer's.

### MAJ-5 — The wall-clock timeout guard silently disappears off the main thread

`src/evaluation/equation_metrics.py:29-45`:

```python
    if (
        seconds <= 0
        or not hasattr(signal, "SIGALRM")
        or threading.current_thread() is not threading.main_thread()
    ):
        yield
        return
```

`C0001_preregistration.md:351-354` asserts "All SymPy paths are already wall-clock guarded ... at
`SYMPY_OP_TIMEOUT_SEC = 10.0`". That is true only single-threaded. The plan never states the Part A
parallelization model, and with ≥10.6 core-hours of work (MAJ-4) it will parallelize. Threads →
guards vanish → the pathological expressions the code comment describes ("dmp_zz_wang Hensel
lifting ... never raise, so try/except cannot stop them") hang unbounded. Processes → guards work.

**Fix.** Preregister **process-based** parallelism for Part A (each worker's main thread keeps
SIGALRM), and add a Stage-6 smoke assertion that `_time_limit` actually fires in a worker.

### MAJ-6 — Silent non-match on any exception, with no failure reason, in both M2 and M3

- `src/gpu_run4/formulas.py:451`: `except Exception: return 0.0, None`
- `src/evaluation/equation_metrics.py:196`: `except Exception: skeleton = 0.0`
- `src/evaluation/equation_metrics.py:153-166`: `to_skeleton` returns `None` on failure → `skeleton = 0.0`

The code states its own rationale at `equation_metrics.py:18-20`: "on timeout we treat the
comparison as 'could not prove equivalence' (the conservative outcome that never inflates a recovery
score)". Conservative for a *recovery* claim; **anti-conservative for C0001's null**, where an
unprovable comparison counted as a miss pushes the primary toward "supported". The plan inherits a
guard whose design intent is the opposite of what this cycle needs, and §14 contingency 1 (`:934`)
covers only labeled timeouts.

**Fix.** Distinguish `proved_different` from `could_not_evaluate` at every level of the cascade;
route the latter into the N5 budget and A-S7; and extend §14 contingency 1's two-sided sensitivity
analysis (currently timeouts-as-miss vs timeouts-as-match) to cover *all* could-not-evaluate
outcomes, not only timeouts.

### MAJ-7 — The Part C re-encoding audit will trip its own abort threshold on a separator convention

Prefix systems are spelled `A|B` in `teacher_prefix` but `A,|,B` after decode. GPU_RUN5's own audit
normalizes for this at `scripts/phases/gpu_run5_phase2.py:189`:

```python
        row["teacher_roundtrip_prefix"] == row["teacher_prefix"].replace("|", ",|,")
```

Measured:

```
raw equality  teacher_roundtrip_prefix == teacher_prefix : 20/80   (only the 1-D systems)
under GPU_RUN5's separator normalization                 : 80/80 validation, 240/240 train
```

`C0001_preregistration.md:549-560` compares `encode(parse(raw)) → decode → canonicalize` against the
stored `candidate_formula_canonical`, with >10% mismatch flagging a cell `unreliable_reencoding` and
>10% of cells forcing **Part C `undecidable`**. An unnormalized comparison reports ~100% mismatch on
every multi-dimensional system and aborts Part C for a cosmetic reason. This is the concrete
component-separator information-loss hazard the audit brief asks about; it is real but benign, and
the plan does not name it.

**Fix.** Preregister the exact normalization (`|` ↔ `,|,`) applied before comparison, and require
the Stage-6 smoke to demonstrate the round-trip audit returning ≥90% exact on a known-good cell
before Part C runs. Note the related positive: `candidate_formula_raw` is `tree.infix()`
(`src/gpu_run4_runtime.py:289-296`) where constants are the decoder's own strings
(`Node.infix` does `s = str(self.value)`, `third_party/odeformer/odeformer/envs/generators.py:102`),
so the model's 4-significant-digit mantissa is preserved verbatim — no float precision is lost.

### MAJ-8 — The replication design's changed factor does not perturb the primary matcher

`C0001_preregistration.md:987` names the replication's independent factor as
`numeric_equivalent(seed = 0 → 1)` plus "an independent safe-domain point set". But
`numeric_equivalent` (`formulas.py:361`) is reached only from M2's fallback (`formulas.py:498`).
M3's numeric check is `_approximately_equivalent`, whose points are hard-coded and non-random
(`equation_metrics.py:72-73`):

```python
        base = np.asarray([0.2, 0.7, 1.3, 1.9], dtype=float)
        args = [base + 0.11 * index for index in range(len(symbols))]
```

There is no seed parameter and no `points` argument. The replication therefore cannot vary the
primary instrument at all; only the corpus and the process differ.

**Fix.** Either state plainly that the primary matcher is deterministic and the replication varies
corpus + process only, or add a `points`/`seed` parameter to `_approximately_equivalent` and
preregister the perturbation. Do not describe the seed change as an independent factor for the
primary.

### MAJ-9 — `pytest GPU_RUN5/tests` currently fails collection, and the substantive firewall tests cannot run; Gate 0 item 2 selects a near-vacuous file

Gate 0 item 2 (`:718`) requires `pytest GPU_RUN5/tests/test_gpu_run5_firewall.py` green. That
invocation **does work** — verified, 2 passed. But:

```
$ pytest GPU_RUN5/tests --collect-only -q
33 tests collected, 6 errors in 2.83s
E   ModuleNotFoundError: No module named 'scripts'
ERROR GPU_RUN5/tests/test_gpu_run5_{grn,phase5,phase6,phase7,phase8,phase9}.py

$ PYTHONPATH=. pytest GPU_RUN5/tests --collect-only -q
124 tests collected in 2.49s
$ PYTHONPATH=. pytest GPU_RUN5/tests/test_gpu_run5_phase8.py -q -k "firewall or sealed or test_open"
4 passed, 10 deselected
```

So (a) `research_state.md` known defect 1's "one-line fix" is insufficient — adding the testpath
without `pythonpath = .` imports 6 collection errors into every bare `pytest`; and (b) the
substantive firewall-ordering assertions live in `test_gpu_run5_phase8.py:541-544` —

```python
    assert "load_sealed_test(" in source
    assert source.index("claim_test_open(") < source.index("load_sealed_test(")
```

— and are **currently un-collectable**.

Meanwhile the file Gate 0 selects is 17 lines with two tests, only one of which is a firewall test:

```python
def test_sealed_test_requires_phase8(tmp_path):
    path = tmp_path / "test.json"
    path.write_text(json.dumps([{"system_id": "held_out"}]))
    with pytest.raises(PermissionError):
        load_sealed_test(path, phase=7)
    assert load_sealed_test(path, phase=8)[0]["system_id"] == "held_out"
```

It exercises a `tmp_path` file, tests only `phase=7`, and validates a 5-line accessor that **C0001
never calls** — C0001 reads its inputs through plain `read_json`. Passing it provides no assurance
about C0001's own file access.

**Fix.** Add `pythonpath = .` and `GPU_RUN5/tests` to `pytest.ini` (safe repo-level fix, research_state
defect 1); extend Gate 0 item 2 to `PYTHONPATH=. pytest GPU_RUN5/tests/test_gpu_run5_firewall.py
GPU_RUN5/tests/test_gpu_run5_phase8.py -k "firewall or sealed or test_open"`; and add a **new C0001
firewall test** that asserts C0001's own input allowlist contains no `sealed*` path and that an
instrumented opener recorded zero sealed reads. A firewall test that does not test C0001's code is
not a gate on C0001.

---

## 3. MINOR findings

| id | finding | evidence |
|---|---|---|
| MIN-1 | `commit_at_freeze` and the run ID are derived from the wrong commit. Prereg `:11` and `.json:/commit_at_freeze` say `94a571b6944e4eb...`; `run_id.value_at_freeze = gpu_runclaude1_c0001_94a571b`. But `94a571b` is "prepare for claude" and the preregistration files were created two commits later in `7cfc0ff`. `git show --stat 7cfc0ff` lists both prereg files as new (1,659 insertions). Fix the recorded freeze commit and re-derive `<short7>` from the commit at run start, as `:814` already specifies. | `git log --oneline -8`; `git show --stat 7cfc0ff` |
| MIN-2 | Run-directory count inconsistent: prereg `:817` says 28, `research_state.md:212` says 29; actual is 27 directories plus one stray log file `gpu_run2_ft_microbench_01_nohup.log` (28 entries). No collision: `ls -d results/runs/gpu_runclaude1*` → no such file. | `ls results/runs/` |
| MIN-3 | Write-path ambiguity that invites a rule-05 violation. §7.6 (`:418`) says store regression cases at `.../phase1/matcher_regression_cases.json`; elsewhere in the same document `...` abbreviates the **GPU_RUN5 run dir** (`:195`, `:608`). §12.1 (`:841`) shows the intent is `R/phase1/`. Replace every `.../` in §7.6 with the explicit `R/` prefix. | prereg `:195`, `:418`, `:608`, `:841` |
| MIN-4 | `src/gpu_run5/config.py:45 write_manifest` hardcodes `{"campaign": "GPU_RUN5", ...}`. C0001 reuses this scaffolding (`research_state.md:7`) and sets `campaign = "GPU_RUNclaude1_C0001"` only in *records* (`:872`), so C0001 phase manifests inside the new run dir would be labelled `GPU_RUN5`. Pass `campaign` through or override. | `src/gpu_run5/config.py:45-49` |
| MIN-5 | `require_artifact` is an unguarded read path. `src/gpu_run5/config.py:56-60` returns any existing path with no firewall check, so `require_artifact(root, "phase2/sealed_test.json")` would hand a caller the sealed path. No current call site does this (full `sealed` grep over `src/ scripts/ configs/ GPU_RUN5/` reviewed), but the prereg's §2.3 item 1 firewall claim rests on routing "every read of a path matching `sealed*` through `load_sealed_test`", and `require_artifact` is the documented bypass. Add a `sealed*` guard there as a cheap repo-level hardening. | `src/gpu_run5/config.py:56-60` |
| MIN-6 | Hardware figures stale. Prereg `:801` and `research_state.md:57` say GPU 0 has 7,782 MiB total; `nvidia-smi` reports **8,192 MiB total, 629 MiB used, 7,154 MiB free, 49 °C**. Gate 0 item 6 (free VRAM ≥ 6.0 GiB, temp < 70 °C) is currently satisfiable; disk 117 G free; RAM 60 G total / 52 G available. | `nvidia-smi`, `df -h`, `free -g` |
| MIN-7 | The consumed run has **no root manifest**: `results/runs/gpu_run5_20260823_ddd267b0/manifest.json` does not exist (only `phase0/`…`phase9/`). Per-phase manifests do exist and `phase3/manifest.json` records commit `ddd267b07a0646140c948c1f4a92ee83e320c772` on branch `main`, `test_accessed: false`, `phase2_validation_sha256: f4644d1d…bb8f64` (matching prereg `:194`), and sympy 1.13.1 / numpy 2.2.6 / torch 2.5.1+cu124 / python 3.10.20 — **identical to the current `lansr310` env**, which is why the re-scoring is reproducible at all. Pin the source commit `ddd267b` in §2.2 and in the C0001 manifest so the re-analysis is traceable to the code that produced its inputs. `research_state.md:8` notes gpu_run4's stuck manifest as defect 4 but not gpu_run5's missing root manifest. | `ls`, `phase3/manifest.json` |
| MIN-8 | Two off-by-one citations: prereg `:40` cites `src/gpu_run5/evaluation.py:40` for `compare_formulas(..., skip_cas=True)`; the call is at `:41` (`:40` is the docstring). Prereg `:910` cites `src/gpu_run4/records.py:47` for `FAILURE_REASONS`; it is at `:50`. All other cited line numbers verified correct (`gpu_run5_structure.py:206`, `evaluation.py:84`, `formulas.py:361/437/479`, `equation_metrics.py:68/153/169/250`, `training.py:16/23`, `records.py:7`, `aggregation.py:22`, `gpu_run5_selection.py:11`, `config.py:63`, `phase3.py:442`, `ted.py:313`). | `sed -n` spot checks |
| MIN-9 | PC3a's denominator is undefined. `:385` requires "≥ 78/80 must be scored NON-match" for a truth "with one realized Hill exponent altered (4→2, or 2→1)", but not all 80 systems have a realizable exponent to alter — the correction of record puts nested `pow` in 24/80 systems, and my crude rewrite reached only 48/80. Define the eligible set and state the threshold against it, as `:386` already does for PC3b (`dimension ≥ 2`, n = 60). | `:385-386`; measured 48/80 alterable |
| MIN-10 | Naming overstates the primary. M3 collapses **all** numeric constants to a single symbol `c` (`equation_metrics.py:161-165`: `re.sub(r"\d+\.?\d*...", "c", ...)` then `re.sub(r"c+", "c", ...)`), so an M3 hit is a *skeleton* match at matched constants — not semantic equivalence. Calling the primary `system_semantic_equivalence_in_beam_rate_M3_ANY` (`:321`) invites exactly the conflation rule 03 forbids. Rename to `..._skeleton_equivalence_...` or add an explicit caveat wherever the endpoint is reported. | `equation_metrics.py:153-166` |
| MIN-11 | Gate A→B wording conflates cell-level and system-level. `:731` says M0 must reproduce "system-level 0.0 over 960 cells"; the comparator at `phase3.py:442` is a **mean over 960 cells** (`np.mean([row[...] for row in groups])`), not over 80 systems. Harmless only because the value is exactly 0, where all reductions coincide — but the corrected component-level target (107/2040, CRIT-1) is *not* zero, so the reduction must be stated precisely. | `scripts/phases/gpu_run5_phase3.py:322, 420-421, 442` |

---

## 4. Constructive finding: M0 *is* exactly reproducible — but only through the path the plan does not name

This is the fix that unblocks CRIT-1 and CRIT-2, so it is recorded as a finding in its own right.

`C0001_preregistration.md:346` defines M0 as "`classify_formula` → `exponent_aware_skeleton` string
equality, exactly as `src/gpu_run5/evaluation.py:84`" without naming the **representation** fed to
`classify_formula`. That single omission is what produced the spurious 0/2040 (CRIT-2). Feeding the
prefix reproduces the *stored cell structure* (960/960); feeding the infix reproduces the *frozen
matcher* (0/960 on the cell structure). Both artifacts exist side by side in the same run directory
with different values.

Going through the path phase 3 actually used — `formula_metrics(teacher_infix, candidate_formula_raw)`
(`scripts/phases/gpu_run5_phase3.py:122` → `src/gpu_run5/evaluation.py:39`) — on 600 randomly
sampled real candidates:

```
system-level exponent_aware_skeleton_exact matches stored : 600/600
component-level vector matches stored                    : 600/600
stored component 1.0 count in sample: 32 ; recomputed: 32
```

**M0 is bit-exactly reproducible in the current environment.** The amended Gate A→B is therefore
achievable and non-trivial: require M0, recomputed via `formula_metrics` on the **infix for both
sides**, to reproduce (a) system-level 0/960, (b) component-level 107/2040, and — the check with
real diagnostic power — (c) the stored per-candidate `exponent_aware_skeleton_exact` and
`component_exponent_aware_skeleton_exact` fields for **all 47,987 candidates**, exactly.

Condition (c) matters because (a) alone is vacuous: every one of the 47,987 stored
`exponent_aware_skeleton_exact`, `canonical_exact` and `skeleton_exact` values is `0.0`, so
"reproduces 0.0" is satisfied by *any* implementation that never returns a match, including a
completely broken one:

```
exponent_aware_skeleton_exact : {0.0: 47987}
canonical_exact               : {0.0: 47987}
skeleton_exact                : {0.0: 47987}
component_exponent_aware_skeleton_exact over 101963 comparisons : {0.0: 99728, 1.0: 2235}
```

The 2,235 component-level ones are the only non-degenerate signal in the stored data, and the plan
currently does not use them. Requiring their exact reproduction converts Gate A→B from a
zero-information aggregate check into a genuine 47,987-way harness test.

---

## 5. What the plan gets right

These are verified positives, recorded so the real defects above are distinguishable from generic
critique.

- **OK-1 — The firewall accessor works exactly as claimed.** `src/gpu_run5/config.py:63-67` raises
  `PermissionError(f"test firewall: phase {phase} cannot read {path}")` for `int(phase) < 8`.
  C0001's declared phases 0–4 are genuinely below the threshold. `pytest
  GPU_RUN5/tests/test_gpu_run5_firewall.py` → 2 passed.
- **OK-2 — The firewall is not bypassed anywhere in the runtime.** A full grep for `sealed` across
  `src/ scripts/ configs/ GPU_RUN5/` (all `.py/.yaml/.yml/.ini`) shows the only reads of the sealed
  GRN artifacts are in `scripts/phases/gpu_run5_phase8.py`, after `claim_test_open` and through
  `load_sealed_test(phase=8)`; phase 9 reads only hashes and asserts
  `sealed_test_files_read_by_phase9: False`; phases 6 and 7 have tests asserting the launchers do not
  even *name* the sealed files (`test_gpu_run5_phase6.py:586-588`, `test_gpu_run5_phase7.py:428-436`).
  No plain `json.load`, `open()`, or `require_artifact` call targets a sealed path. The one gap is
  the recursive fingerprinter (MAJ-2), which hashes rather than deserializes.
- **OK-3 — The Part A glob cannot match test cells.** `phase3/cells/` contains exactly 960 files,
  all `*_validation_*`, zero containing `test`; the only split token present is `validation`;
  `all_candidates.json` is `{'validation': 47987}`. C0001 consumes no seal.
- **OK-4 — Run ID is collision-free.** No `results/runs/gpu_runclaude1*` exists. Nothing in the
  design writes into `results/runs/gpu_run5_*` or `gpu_run4_*` (all destinations in §12.1 are under
  the new run root `R`), with the single wording exception at MIN-3.
- **OK-5 — Checkpoint identity verified exactly.** `sha256sum assets/odeformer/weights/odeformer.pt`
  = `56754040be5aa92ed4767fc43ee2008faa293f87c12b643e66c7df3e1623a5e8`, size 464,822,385 B — both
  match the pin at `:248`.
- **OK-6 — P9 and P10 verified exactly.** No `symbolic_equivalent` field on any of the 47,987
  records; no field matching `logprob|log_prob|score|prob|nll|loss`; `skip_cas=True` confirmed at
  `src/gpu_run5/evaluation.py:41`. Candidate counts 951×50 + 6×49 + 2×48 + 1×47 = 47,987, shortfall
  13, over 80 systems and 960 cells — exactly as `:41` states. The plan's decision to use *usable*
  candidates as the denominator rather than a hardcoded 50 is correct and necessary.
- **OK-7 — P1 verified; E1 is soundly refuted.** `teacher_valid` is 80/80 validation and 240/240
  train, and the prefix round-trip is exact 80/80 and 240/240 under GPU_RUN5's own separator
  normalization (`gpu_run5_phase2.py:189`). Declaring E1 refuted and not re-testing it is justified.
- **OK-8 — M3 is genuinely sensitive and specific, and choosing it as the primary was right.**
  Measured: PC2a (`-1 * k * x_i → (-k) * x_i`, the exact artifact E0 alleges, applied in all 80
  systems) gives M3 **80/80** — the matcher *can* detect the asymmetry, satisfying N2's intent.
  PC3a (altering a realized Hill exponent) gives **48/48 correctly scored NON-match** — the matcher
  is not over-permissive on exponent structure. Crucially, `symbolic_recovery` has **no node cap**,
  which is why the primary survives CRIT-3. The plan's rationale at `:330-332` — pick the most
  permissive criterion so the null is maximally easy to falsify — is the adversarially correct choice.
- **OK-9 — Adding PC3a/PC3b was the right instinct.** `:388-390` correctly identifies that a
  null-shaped primary can be destroyed by an over-permissive matcher and that only a specificity
  control detects it. Those controls were not in the original brief.
- **OK-10 — `run_manifest.py` is the right tool and is correctly identified.** It records commit,
  branch, `git_dirty`, `pip_freeze`, platform, torch/CUDA, GPU name, nvidia driver, checkpoint
  SHA256, `LANSR_*` parameters and resume breadcrumbs; `--strict` resume refuses on commit mismatch,
  dirty worktree, or changed `LANSR_*` params (`:145-193`). The plan reuses it rather than inventing
  a manifest format, as required.
- **OK-11 — Part C's instrument change is handled correctly.** `:541-548` adds a *new* scoring
  function rather than modifying `src/gpu_run4/training.py:23 teacher_forcing_loss` (verified: that
  function returns the mean CE via `get_scores=False` and other phases depend on it), and requires a
  regression test asserting `sum_logprob / n_scored_tokens == -teacher_forcing_loss(...)` to 1e-5 on
  ≥5 fixed examples. `_point_bag` is at `:16` as cited. Caching `src_enc` once per cell and scoring
  GT and all candidates through the identical path in the same process is the correct fairness
  construction.
- **OK-12 — Part C's inputs exist and the VRAM envelope is plausible.** Cell files carry
  `input_trajectory_checksum` and `observations{input, selection, generalization}`;
  `validation.json` carries `tree_encoded` (the corpus multiplicative encoding, e.g.
  `['add','+','N1954','E-4','add','mul','mul','+','N8878','E-4','x_0','inv', ...]`),
  `teacher_token_length` (max 80 on validation, consistent with P3), and `teacher_components_infix`.
  60.6M params in fp32 ≈ 242 MB of weights; forward-only with batch ≤ 8 and seq ≤ 200 comfortably
  fits the ≤ 3.0 GiB target and the ≤ 5.5 GiB cap, and the GPU-1 fallback (3,006 MiB, forward-only)
  is feasible. The three-step fallback chain preserves comparability because it changes *which cells*
  are scored, not the numerics — it stays fp32 throughout and never moves to CPU or fp16, which is
  the right call for log-probability ranking.
- **OK-13 — RAM is not at risk for Part A.** 60 GiB total, 52 GiB available; `all_candidates.json`
  is 174 MB on disk and the cascade holds one comparison at a time. With process-based parallelism
  (MAJ-5) at ≤ 8 workers the resident set stays far below the 60 GiB ceiling. The plan's disk
  estimate (3–6 GiB against a 15 GiB cap and 117 GiB free) is sound.
- **OK-14 — The correction of record (§0.2) is sound and independently verified.** Nested
  `pow,pow` appears in 39/170 validation truth components and 24/80 systems; a literal `pow2` token
  or `4` never appears in a canonical skeleton. The retraction was committed in `7cfc0ff` with a
  dated correction block appended to the exploratory analysis rather than an edit of frozen text —
  exactly the deviation discipline §14 requires. The same discipline should now be applied to CRIT-2.
- **OK-15 — Research-integrity architecture is strong.** The §0 prior-information disclosure, the
  demotion of A-S3 to estimation-only with a mandatory machine-readable provenance field, the §9.1
  degenerate-paired-test warning (M0 ≡ 0 makes the paired difference Bernoulli, not t), the §9.4
  blanket prohibition on equivalence claims absent a preregistered TOST margin, the restriction of
  Part C to Part B's in-support subset, the triple length-normalization with a conjunctive rule that
  forbids picking the tidiest normalization, the retention of invalid/failed candidates in every
  denominator, the crash-loop rule, and the explicit "no layer estimand is measured" statement are
  all correct and go beyond what the rules minimally require.

---

## 6. Findings table by severity

| id | severity | finding | primary evidence |
|---|---|---|---|
| CRIT-1 | **CRITICAL** | Gate A→B demands reproduction of `C-M0c = 0/2040`; the stored value is 107/2040, so a correct M0 must fail the gate and §14.6 voids the cycle | `phase3/beam_groups.json`; prereg `:269`, `:731`, `:966` |
| CRIT-2 | **CRITICAL** | The `neg`-asymmetry finding underpinning E0's component-level support is a prefix-vs-infix representation-mixing artifact; "107 scored as complete misses" is false | 960/960 prefix vs 0/960 infix reproduction; `C0001_exploratory_neg_canonicalization.md:44,57` |
| CRIT-3 | **CRITICAL** | `SYMPY_MAX_NODES = 40` silently zeroes M2 for 55.1% of pairs (R05–R08 at 93–100%) with `failure_reason = None`; N5 and §7.3 are both blind | `formulas.py:434`; `ted.py:15`; 52/80 truth-vs-itself failures |
| CRIT-4 | **CRITICAL** | PC1, the plan's hard abort control, is short-circuited by `canonical_exact` and never exercises M2's CAS path; N1 is vacuous for M2 | `formulas.py:492-497`; PC1 M2 80/80 vs direct CAS 28/80 |
| MAJ-1 | MAJOR | M3, the primary matcher, is not uniquely specified ("skeleton plus `_approximately_equivalent` plus `to_skeleton`"); plus a hidden `equiv = skeleton` fallback | prereg `:349`; `equation_metrics.py:203-205` |
| MAJ-2 | MAJOR | `run_manifest.py --data-path` recursively byte-reads all three seals including the only UNSPENT one; `sealed_paths_read: []` would be a false record | `run_manifest.py:28-33,119`; `gpu_run5_phase8.py:1173-1175` |
| MAJ-3 | MAJOR | Glob hazard is in `phase2/` and `phase4/` (seals beside legitimate inputs), not `phase3/cells/`; Gate 0 item 7 reads a sibling of the unspent seal | `ls phase2/ phase4/`; prereg `:726` |
| MAJ-4 | MAJOR | Part A measured at 795 ms/candidate → 10.6 core-h, 6.2× P11 and above its own 8 h allocation; the CRIT-3 fix projects ~66 core-h, breaching the 24 h ceiling | timed run on 150 real candidates; prereg `:42`, `:803` |
| MAJ-5 | MAJOR | `_time_limit` silently no-ops off the main thread, so §7.2's "all SymPy paths are guarded" fails under thread parallelism | `equation_metrics.py:29-45` |
| MAJ-6 | MAJOR | Bare-exception and `to_skeleton`-None paths return silent non-matches with no failure reason, in a direction that favours the preregistered null | `formulas.py:451`; `equation_metrics.py:153-166,196` |
| MAJ-7 | MAJOR | Part C's re-encoding audit compares across the `\|` ↔ `,\|,` separator convention and would self-abort at ~100% mismatch | 20/80 raw vs 80/80 normalized; `gpu_run5_phase2.py:189`; prereg `:549-560` |
| MAJ-8 | MAJOR | The replication's "changed factor" (`numeric_equivalent` seed) does not touch M3's fixed non-random point grid, so it cannot perturb the primary | `equation_metrics.py:72-73`; prereg `:987` |
| MAJ-9 | MAJOR | `pytest GPU_RUN5/tests` fails collection (6 errors); the substantive firewall tests are un-runnable; Gate 0's chosen file is 2 tests on an accessor C0001 never calls | collection runs; `test_gpu_run5_firewall.py`; `test_gpu_run5_phase8.py:541-544` |
| MIN-1…MIN-11 | MINOR | freeze-commit/run-ID mismatch; run-dir count; `.../phase1` write ambiguity; hardcoded `campaign: GPU_RUN5`; unguarded `require_artifact`; stale VRAM figures; missing gpu_run5 root manifest; two off-by-one citations; PC3a denominator undefined; "semantic equivalence" misnomer; cell-vs-system reduction wording | see §3 |
| OK-1…OK-15 | OK | firewall accessor sound and un-bypassed in the runtime; glob safe; run ID collision-free; checkpoint verified; P1/P9/P10 verified exactly; M3 sensitive (PC2a 80/80) and specific (PC3a 48/48); M0 bit-exactly reproducible; correct manifest tool; additive Part C instrument; plausible VRAM/RAM/disk; sound §0.2 retraction; strong integrity architecture | see §4, §5 |

**Counts: 4 CRITICAL · 9 MAJOR · 11 MINOR · 15 OK.**

---

## 7. Verdict

> ### `AMEND_BEFORE_IMPLEMENTATION`

Per rule 07, CRITICAL findings block a supported conclusion, and Gate 0 item 3
(`C0001_preregistration.md:720`) requires this audit to report **zero CRITICAL** findings before any
endpoint is computed. **Stage 4 implementation and Stage 7 execution must not begin** until CRIT-1
through CRIT-4 are resolved.

The cycle is **not** scientifically dead and no seal has been touched. Three of the four CRITICALs
are instrument defects with identified fixes, and the fourth (CRIT-2) is a correction of record that
*strengthens* the integrity position — the component-level rate was never a discovery, because it was
already published in GPU_RUN5. The primary endpoint's matcher (M3) is sound and was independently
verified sensitive and specific. Most importantly, M0 is bit-exactly reproducible, so a corrected
Gate A→B is both achievable and far more diagnostic than the version currently frozen.

CRIT-1 and CRIT-2 alter frozen text (a comparator value and an explanation's evidential status).
They are **supervisor amendments** requiring dated `DEVIATION-nn` blocks per §14, not implementer
decisions. Because CRIT-2 changes the status of E0 — one of the four explanations the cycle exists to
discriminate — the supervisor should consider whether §14's deviation mechanism suffices or whether
Part A's framing warrants a re-freeze under the same cycle ID.

No hard-stop condition is active: branch correct, tree clean, no destructive operation required, no
seal consumed, no credential or licensing question, GPU/disk/RAM healthy. **If** the CRIT-3 fix
projects Part A above 24 CPU-core-hours (MAJ-4), that *is* a rule-06 ceiling decision and becomes a
hard stop requiring human approval.

---

## 8. Minimum amendment list, in priority order

1. **Correct the comparator of record.** Set `C-M0c = 107/2040 = 0.0525` (`:269`) and rewrite Gate
   A→B (i) (`:731`) to require M0 to reproduce *system-level 0/960* **and** *component-level
   107/2040*. Fix §9.1's "M0 is 0 for all 80 systems" to say *system-level*. **[CRIT-1]**
2. **Make Gate A→B non-vacuous.** Add the requirement that M0, recomputed via
   `formula_metrics(teacher_infix, candidate_formula_raw)`, reproduce the stored per-candidate
   `exponent_aware_skeleton_exact` and `component_exponent_aware_skeleton_exact` fields for all
   47,987 candidates exactly — including all 2,235 component hits. **[CRIT-1, §4]**
3. **Pin the representation in the M0 spec.** §7.2 must state that both truth and candidate go
   through the **infix** path, and must warn that `phase3/cells/*.json:true_structure` is
   prefix-derived and must never be compared against infix-derived skeletons. **[CRIT-2]**
4. **Retract the `neg`-asymmetry claim and re-ground E0.** Amend §0 (P4, P6), §1.1 (E0 status), §4
   (C-NEG), §7.6 and §0.3; append a dated correction to
   `C0001_exploratory_neg_canonicalization.md` retracting the "raw 0/2040" row and the "scored as
   complete misses" interpretation; re-point A-S3's `prior_information_disclosed` at the published
   GPU_RUN5 artifact. **[CRIT-2]**
5. **Fix the node cap and make it visible.** Give `nodes > SYMPY_MAX_NODES` a distinct
   `failure_reason` (`SymbolicNodeCapExceeded`), add it to the N5 budget and A-S7, and either
   preregister a cap sufficient for GRN (≥ 200 combined) with a recorded deviation or declare
   M2/A-S1 unmeasurable for R05–R08 and drop A-S1 from the S1 Holm family. **[CRIT-3]**
6. **Add a cascade-bypass positive control (PC0).** Assert `_sympy_components_equal(truth, truth) == 1.0`
   for all 80 systems, bypassing `compare_formulas`; add it to N1 at an 80/80 threshold; and verify
   PC2a–PC2d are not also short-circuited by `canonical_exact`. **[CRIT-4]**
7. **Pin M3 to exactly one key** of `symbolic_recovery` — `["skeleton"]` recommended — and delete
   the "plus `_approximately_equivalent` plus `to_skeleton`" clause from the `.md` and the `.json`.
   **[MAJ-1]**
8. **Close the fingerprint leakage path.** Preregister `--data-path` as a file-level allowlist that
   never names a directory containing a seal; add a `sealed*` assertion on every resolved input path;
   make `sealed_paths_read` a computed record from an instrumented opener. Add explicit filename
   allowlists for `phase2/` and `phase4/`, and `assert len(files) == 960` on the `phase3/cells` glob.
   **[MAJ-2, MAJ-3]**
9. **Re-derive the Part A budget from a GRN smoke, not P11**, invoke the §14.4 reduced design before
   starting, and separately cost the amendment-5 fix; escalate to the supervisor if it projects over
   24 core-hours. **[MAJ-4]**
10. **Preregister process-based parallelism for Part A** and a Stage-6 assertion that `_time_limit`
    fires inside a worker. **[MAJ-5]**
11. **Separate `proved_different` from `could_not_evaluate`** at every cascade level and extend §14
    contingency 1's two-sided sensitivity analysis to all could-not-evaluate outcomes. **[MAJ-6]**
12. **Specify the `|` ↔ `,|,` normalization** in the §8.2 step-4 re-encoding audit and require the
    smoke to demonstrate ≥90% exact round-trip on a known-good cell before Part C runs. **[MAJ-7]**
13. **Fix the test gate.** Add `pythonpath = .` and `GPU_RUN5/tests` to `pytest.ini`; extend Gate 0
    item 2 to include the `test_gpu_run5_phase8.py` firewall-ordering tests; add a new C0001-specific
    firewall test over C0001's own input allowlist. **[MAJ-9]**
14. **Correct the replication description** so the seed change is not presented as perturbing the
    primary matcher. **[MAJ-8]**
15. **Housekeeping**: correct `commit_at_freeze` and re-derive `<short7>` at run start; pin source
    commit `ddd267b`; replace `.../` with `R/` in §7.6; pass `campaign` through `write_manifest`; add
    a `sealed*` guard to `require_artifact`; refresh the VRAM figures; define PC3a's eligible set;
    rename the primary away from "semantic equivalence"; fix the two off-by-one citations.
    **[MIN-1…MIN-11]**

---

*Audit performed read-only. No file under any `sealed*` path was opened. Files written: this document
only. Two scratch files were written outside the repository under the session scratchpad.*
