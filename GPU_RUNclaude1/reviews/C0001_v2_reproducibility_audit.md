# C0001 — Stage-5 reproducibility audit of preregistration **v2** (fresh audit)

| field | value |
|---|---|
| audit target | `GPU_RUNclaude1/plans/C0001_preregistration_v2.md` (1,617 lines) + `.json` (parses; consistent on every value I cross-checked) |
| this is | **Gate 0 item 3** of v2 itself: "a fresh Stage-5 reproducibility audit of the **v2** design reports **zero CRITICAL** findings" (`v2:1131`) |
| repo / branch | `/home/blabo/Layer-wise_Analysis_of_NSR_for_Discovering_GRD`, `20260909_researce_GPU_RUNclaude1` (verified via `git branch --show-current`) |
| HEAD at audit | `7f507cc` "Re-freeze C0001 as preregistration v2 after two blocking reviews" |
| working tree at audit | **DIRTY** — `M src/evaluation/equation_metrics.py`, `M src/gpu_run4/records.py`, `M src/gpu_run5/config.py`, `?? src/gpu_runclaude1/` (6 modules, 929 lines). See V2-MAJ-7. |
| env | `lansr310` (sympy 1.13.1, numpy 2.2.6, torch 2.5.1+cu124, Python 3.10.20) |
| date | 2026-09-09 |
| relation to prior reviews | fresh audit of the new document. Every one of the 8 prior CRITICALs was re-checked against v2's text **and** against code/data, not against the acceptance claims in `v2:1575-1586` (§18.4). |
| seals touched | **NONE.** No `sealed_*` file was read, hashed, or deserialized by this audit; only `ls`/`stat`. |
| §0.4 integrity ordering | **RESPECTED.** I did **not** compute the H/L stratification of the 107 published M0 component hits. See §3 for the tension this creates and what I verified instead. |
| verdict | **`AMEND_BEFORE_RUN`** — 3 CRITICAL, 7 MAJOR, 10 MINOR |
| Gate 0 item 3 | **NOT SATISFIED** |

A note on filename: the task directed this file to `C0001_v2_reproducibility_audit.md`; `v2:1327` (§12.1) expects
`C0001_reproducibility_audit_v2.md`. One of the two must be corrected so the artifact manifest resolves.

**Amendment is legal right now.** `v2:28` permits amendment without a new cycle ID until Stage 4 begins;
Stage 4 has not begun (`ls -d results/runs/gpu_runclaude1*` → no such file). The three CRITICALs below are
all repairable by amending the control battery and two statistical sentences. None of them requires a new
cycle ID, a ceiling increase, or a redesign of the primary endpoint, which I judge sound (see §2).

---

## 1. Did each of the 8 prior CRITICALs actually get fixed?

Verified one by one against v2's text and then against code or data. "Fixed by design" means the defect
cannot recur; "fixed by wording" means the text changed but the underlying hazard is unaddressed.

### AUDIT-CRIT-1 — Gate A→B demanded reproduction of a factually wrong comparator (`0/2040`)

**v2's handling** (`v2:100`, §4 `C-M0c`, §7.6 `v2:673-680`):
> "**C-M0c** frozen string matcher, component level | **107/2040 = 0.0525** (P0b) … **CORRECTED from v1's
> `0/2040`** (AUDIT-CRIT-1)."
> "The M0 arm … must reproduce the stored `exponent_aware_skeleton_exact` and
> `component_exponent_aware_skeleton_exact` fields for **all 47,987 candidates** and **all 101,963 component
> comparisons** exactly — including all **2,235** stored component-level ones — and must reproduce the reduced
> values **0/960 system-level** and **107/2040 component-level**."

**Verified against data.** Every figure is exact:

| quantity | v2 | measured |
|---|---|---|
| candidates in `phase3/all_candidates.json` | 47,987 | **47,987** |
| component comparisons | 101,963 | **101,963** |
| stored component hits (`==1.0`) | 2,235 | **2,235** |
| stored system-level hits | 0 | **0** |
| `component_true_exponent_aware_skeleton_in_beam` over 960 groups | 107/2040 | **107/2040** |
| per family | R01 0/120, R02 0/120, R03 0/240, R04 56/240, R05 0/240, R06 0/360, R07 17/360, R08 34/360 | **identical, all eight** |

**FIXED BY DESIGN.** The gate is achievable and non-degenerate (the 2,235 are the only non-zero stored
signal, so "reproduces 0.0" no longer suffices). `OK`.

### AUDIT-CRIT-2 — the `neg`-asymmetry finding was a prefix-vs-infix representation artifact

**v2's handling** (`v2:132-142` §0.1, `v2:441-448` §5 item 1, `v2:604` §7.4):
> "**Both sides of every comparison are fed the infix representation** (R1, AUDIT-CRIT-2):
> `formula_metrics(teacher_infix, candidate_formula_raw)` for M0 and the same infix pair for M1/M3.
> `phase3/cells/*.json:true_structure` is **prefix-derived** and must never be compared against an
> infix-derived skeleton."
> Retracted as *findings*: P5, P6, the "0/2040 baseline", `C-NEG`. "No v2 element may depend on a 0/2040
> baseline." (`v2:142`)

**Verified.** `grep` of v2 finds no surviving dependence on 0/2040 as a baseline. The retraction document
(`analyses/C0001_RETRACTION_neg_finding.md:24-40`) is correctly quoted. `formula_metrics` is at
`src/gpu_run5/evaluation.py:39` and calls `compare_formulas(true_infix, predicted_infix, skip_cas=True)` at
`:41` — infix on both sides, as v2 says (v2's corrected citation is right; v1's `:40` was the docstring).
**FIXED BY DESIGN.** `OK`.

But this fix has an unintended consequence v2 did not follow through: because both sides are now infix, the
infix parser folds `-1 * k * x` into `-k * x` **before M0 sees it**, so M0 already absorbs the very asymmetry
E0 rests on. That is V2-CRIT-3, below — a new defect created by a correct fix, not a failure of the fix.

### AUDIT-CRIT-3 — `SYMPY_MAX_NODES = 40` silently zeroes M2 for 55.1% of pairs

**v2's handling**: M2 **cut** (`v2:1528-1559` §18.1), plus a general failure taxonomy (`v2:628-666` §7.5):
> "`SYMPY_MAX_NODES = 40` is a **combined** truth+candidate budget, and `src/gpu_run4/formulas.py:434`
> returns `0.0, None` above it with **no** failure reason. … So M2 as v1 froze it is unusable. Fixing it,
> however, … ≈**66 core-hours** against a **24 core-hour** ceiling."
> "**Every non-match carries an explicit `failure_reason`, and `proved_different` is separated from
> `could_not_evaluate` at every level.**" with a **frozen 2.0% maximum** above which the primary is
> `undecidable`.

**Verified in code.** `src/gpu_run4/formulas.py:433-435`:
```
433      nodes = sum(tree_size(t) for t in true_components) + sum(tree_size(t) for t in pred_components)
434      if nodes > SYMPY_MAX_NODES:
435          return 0.0, None
```
`SYMPY_MAX_NODES = int(os.environ.get("LANSR_SYMPY_MAX_NODES", "40"))` at `src/gpu_run4/ted.py:15`.
`_sympy_components_equal` is defined at `formulas.py:427` and has **exactly one call site repo-wide**
(`:496`), gated by `elif not skip_cas:` at `:495`. `formula_metrics` passes `skip_cas=True`, and
`src/evaluation/equation_metrics.py` does not import `gpu_run4` at all. So **the node cap is genuinely
unreachable from every v2 endpoint path** — the defect is removed, not merely labelled.
**FIXED BY DESIGN** (see §4 for whether cutting M2 was the right call). `OK`.

Residual: `equation_metrics.py:200`'s `_timed_simplify` is a 10-second timeout surface that v2's §7.5 list
omits, because v2 wrongly believes that code does not run. See V2-MAJ-1.

### AUDIT-CRIT-4 — PC1 never exercised the code path it validated

**v2's handling** (`v2:698-701` §7.7):
> "**PC0** identity through M3's own path | call `symbolic_recovery(T_i, T_i)["skeleton"]` **directly**,
> bypassing `compare_formulas` entirely | … **170/170 components and 80/80 systems.** Any failure ⇒ matcher
> broken ⇒ **abort Part A**"
> "**PC1** … retained only to document the artifact; **it gates nothing.**"

**Verified in code and by measurement.** `symbolic_recovery` (`equation_metrics.py:169`) has **no**
short-circuit on `exact`: `skeleton` is computed at `:184-193` from `to_skeleton` results only, independently
of `exact` at `:182`. This is the opposite of `formulas.py:493-494` (`if metrics["canonical_exact"] == 1.0:
symbolic = 1.0`), which is what made v1's PC1 vacuous — v2's `:493` citation is correct for the guard line.
**Measured**: `symbolic_recovery(T_i, T_i)["skeleton"] == 1.0` for **170/170** validation components.
**FIXED BY DESIGN.** PC0 exercises the exact path the primary uses and the hard gate is achievable. `OK`.

### STAT-C1 — the primary's conjunction over components was orthogonal to E0's per-component mechanism

**v2's handling**: v1's primary demoted to `A2-S3` (`descriptive`, `v2:62`), replaced by
`hill_component_matcher_attributable_gain_rate` at component resolution over a frozen Hill stratum
(`v2:496-518` §7.1).

STAT-C1's literal required fix was `component_type_stratified_M3_match_rate` — the *level*, stratified. v2
supplies that as `A2-S2` (`descriptive`) and makes the **gain** the confirmatory primary instead
(`v2:530-534`: "the component-level M3 *level* is bounded below by M0's published 107/2040 under
monotonicity, so a positive level is guaranteed and uninformative"). **This is a superior operationalization,
not a dodge** — I endorse the substitution. **FIXED BY DESIGN**, with the caveats in §2. `OK`.

### STAT-C2 — clustering unmodeled, target population unstated

**v2's handling** (`v2:289-302` §2.2, `v2:959-991` §9.2): superpopulation estimand frozen and named; the
finite-population reading recorded and explicitly rejected; the `deff = 1 + (m−1)·ICC` table with the
critical ICC = **0.011** disclosed; a two-stage cluster bootstrap named the interval of record; the ICC
conditional pre-committed. **FIXED BY DESIGN in substance.** But the designated interval of record is
degenerate at the predicted outcome — see **V2-MAJ-3**. `OK with a MAJOR attached`.

### STAT-C3 — Part C's fairness verification was empirically vacuous

**v2's handling** (`v2:816-829` §8.2 step 1): `input_trajectory_checksum` relabelled a **system-identity**
check; replaced by `cell_input_payload_sha256` over the float64 LE bytes of `times ‖ observed_trajectory ‖
initial_condition`, each preceded by its shape as LE int64; plus the assertion that a system shows exactly
**10** distinct payloads.

**Verified exactly, over all 960 cell files.** I implemented v2's digest as specified:

| v2 claim (P11 / NC3) | measured |
|---|---|
| 12 cells per system | **12/12 in 80/80** |
| distinct `cell_input_payload_sha256` per system == 10 | **10 in 80/80 systems; 0 violations** |
| the 3 clean (σ=0, ρ=0) cells byte-identical across bundles | **1 distinct payload in 80/80** |
| `input_trajectory_checksum` constant across a system's 12 cells | **1 distinct value in 80/80** |

**FIXED BY DESIGN, and the frozen assertion is empirically satisfiable.** This is the single best-verified
amendment in v2. `OK`.

### STAT-C4 — the E2/E3 discriminator did not identify model error

**v2's handling** (`v2:873-933` §8.3): `C-S6` promoted to the paired Stahlberg–Byrne indicator on **summed**
log-probability as the sole discriminator; `C-S1`–`C-S4` and the conjunctive rule demoted to `descriptive`
with the frozen T = 0.1 upper-tail caveat; NC1–NC5 added; a dead zone (`neither_E2_nor_E3_predominant`)
named and distinguished from `undecidable`; the Stahlberg & Byrne precedent cited with DOI.
**FIXED BY DESIGN.** The length policy at `v2:875-884` is correct: summed log-prob is the only variant that
is a probability comparison. `OK`.

**Score on the 8 CRITICALs: 8/8 addressed, 8/8 by design, 0 by wording alone.** Two of them (CRIT-2,
STAT-C2) leave a residue that I raise as new findings, but no prior CRITICAL is falsely claimed fixed.

---

## 2. The new primary endpoint

### 2.1 `|H|` computed — the H definition is unambiguous, seal-free, and matches its prediction

v2 §7.2 (`v2:544-547`) freezes:
> "**H — Hill / variable-denominator** | the component's parsed tree contains **at least one `inv` node whose
> argument subtree contains at least one variable leaf `x_j`**"
> computed "from `phase2/validation.json:teacher_components_infix` through
> `src/gpu_run4/formulas.py formula_views(..., as_prefix=False)["components"]`".

I executed exactly that path. `formula_views(..., as_prefix=False)["components"]` returns
`list[Tree | None]` (`formulas.py:282`, `:295`), and the infix `1/(K + x_0)` does parse to an `inv` node —
verified on R01: `components = [('add', (('add', (('0.1954',()),('mul',(('-0.3968',()),('x_0',()))))),
('mul', (('mul', (('0.8878',()),('inv',(('add',(('0.8392',()),('x_0',()))),)))),('x_0',())))))]`.
So the definition is decidable on the object v2 names. **Result:**

```
n components: 170
|H| = 130   |L| = 40
H by family: R01 10, R02 10, R03 20, R04 10, R05 20, R06 30, R07 20, R08 10
L by family: R04 10, R07 10, R08 20        (R01,R02,R03,R05,R06: zero L components)
H by dim:  1->20, 2->50, 3->60     L by dim: 2->10, 3->30
mismatches vs stored structure.component_flags[i].variable_denominator_form: 0 / 170
```

- **`|H| = 130`**, inside v2's predicted **130–145** (`v2:572`) — at the lower boundary. **`|L| = 40`**,
  inside the predicted **25–40** — at the upper boundary. §7.3's prediction holds; §14 item 7's
  `DEVIATION` for a prediction miss does not fire.
- Independent cross-check: the assignment agrees **170/170** with GPU_RUN5's own precomputed
  `structure.component_flags[i].variable_denominator_form`, which was derived by a different code path.
- `|H| = 130 ≥ 40` and `|L| = 40 ≥ 15`, so §7.2's `not_measurable` fallback does not fire; `|H| ≥ 100`, so
  the `underpowered_bound_only` label does not fire. **`C = ceil(0.02 × 130) = 3`.**
- No seal was touched: only `phase2/validation.json` (on v2's allowlist).

`OK` — the H definition is well-posed, computable, and its predicted size is confirmed.

### 2.2 The gain indicator is well-defined and is measured where M0 *failed*

The task's concern was whether the gain "can be nonzero only where M0 already succeeded". It is the exact
opposite. `gain(s,i) = 1[m3_any = 1 AND m0_any = 0]` requires `m0_any = 0`, so gain is measured **only** on
M0's misses. Quantitatively, from the published per-family M0 counts plus my census:

- **90 of the 130 H components** lie in R01/R02/R03/R05/R06, families with **0** M0 component hits in
  `beam_groups.json` (0/120, 0/120, 0/240, 0/240, 0/360). For those, `m0_any = 0` by published data, so
  `gain = m3_any` outright.
- At most **40** H components (R04 10 + R07 10 + R08 20 … in fact R04 10 + R07 20 + R08 10 = 40 H components
  in the three hit-bearing families) can carry `m0_any = 1` and thereby be structurally barred from
  contributing.

So the endpoint's denominator is at worst 31% inflated by components that cannot contribute, which deflates
the rate — the conservative direction for a null-shaped claim — and the ladder decides on the **count** `K`
against `C = 3`, which the denominator does not touch. **Not structurally near-zero for an uninteresting
reason.** `OK`.

The mirror-image concern *does* land on the **secondary** A2-S1: stratum L exists only in R04/R07/R08, the
three families where M0 already succeeds, so if the 107 sit in L then `m0_any = 1` for many L components and
the predicted "L-stratum gain > 0" contrast (`v2:575`) is structurally suppressed. That is a `MINOR`
weakness in a `descriptive` endpoint, recorded here rather than raised separately.

### 2.3 Monotonicity is **not** guaranteed — and the endpoint is correctly robust to that

v2 §9.4 item 4 (`v2:1077-1082`) rests the multiplicity argument on `M0 ⊆ M1 ⊆ M3`, conditional on §7.5's
audit passing. I tested whether M3 really dominates M0 and found **it does not, in general**:

| synthetic rewrite of the truth | M0 | M3 | gain |
|---|---|---|---|
| `apart` (partial fractions), first 20 systems | **3/20** | **0/20** | 0/20 |

M3 can be **strictly less permissive** than M0, because `to_skeleton` maps every distinct constant to the
same symbol `c`, under which some algebraic identities cease to hold while M0's exponent-aware canonical tree
still matches. This is not a defect in the endpoint: `gain` is an **indicator conjunction**, not a
difference, so it lies in {0,1} regardless and can never be negative; and v2 already requires the
`m0_any = 1, m3_any = 0` census as "the direct sibling of the primary" (`v2:665-666`). The endpoint is
mis-specification-proof here. What the finding does establish is that §7.5's monotonicity audit is a real
gate and not a formality, and that §9.4 item 4's "if M3 returns 0, every level returns 0" is **false as a
mathematical statement** — it holds only empirically, conditional on the audit. v2 says this
("conditional on the monotonicity check of §7.5 actually passing"), so it is `OK` — but the >1% CRITICAL
tripwire in §7.5 item 4 is more likely to fire than v2's "≤ 0.1%" prediction (`v2:578`) implies.

### 2.4 The §0.4 tension, stated explicitly

**I did not compute the H/L stratification of the 107**, and I recommend nobody does before
`R/phase1/component_strata.json` is written and hashed.

But computing `|H|` — which the task required and which v2 §7.2 step 1 requires anyway — **partially
pre-empts §0.4 on its own**, and this must be recorded. Stratum L is non-empty in **exactly and only**
R04, R07 and R08, which are **exactly and only** the three families carrying all 107 published M0 component
hits. The correlation between L-membership and M0 success is therefore *perfect at family resolution*, from
truth-side census plus already-disclosed P0b. §7.3's prediction that "at least 54 of 107" of the hits lie in
L (`v2:576`) is consequently no longer a blind prediction; it is a partly-derivable one.

**What an auditor can verify without violating the ordering** (and what I did verify): `|H|`, `|L|` and
their family/dimension breakdown; that the stratum definition is decidable and agrees with an independent
stored flag; that the §7.6 gate targets (47,987 / 101,963 / 2,235 / 107 / 0 / the eight family counts) are
exact; that PC0 passes; that PC2a/PC2b/PC3b behave as measured on **truth-vs-rewritten-truth** synthetic
pairs, which contain no candidate outcome information at all; the realized per-candidate compute cost; and
every Part C identity assertion. **What cannot be verified without violating it**: the realized primary, the
H/L split of the 107, and therefore §7.3's stratification prediction.

**Required**: add `|H| = 130`, `|L| = 40` and the per-family breakdown to §0.3 as auditor-disclosed prior
information, and downgrade §7.3's stratification prediction from "recorded before the stratification of the
107 was looked at" to "partly derivable from the family-level census plus P0b".

---

## 3. CRITICAL findings

### V2-CRIT-1 — PC2b's frozen **gating** threshold is unachievable by construction; Gate A→B fails deterministically

**Evidence.** `v2:709` (§7.7): "**PC2b** affine decomposition | `a * A^n * inv(K + A^n)` → `a − a*K*inv(K +
A^n)`, SymPy-verified | sensitivity of M3 | **≥ 76/80**". `C0001_preregistration_v2.json`:
`{"id": "PC2b", …, "threshold": ">= 76/80", "gating": true}`. Gate A→B item (iii), `v2:1152`:
"PC2b/PC2c/PC2d ≥ 76/80".

**The defect.** M3 (`symbolic_recovery(...)["skeleton"]`) **cannot** prove an affine decomposition, for a
structural reason. `to_skeleton` (`src/evaluation/equation_metrics.py:153-166`) maps **every** distinct
numeric constant to the **same** symbol `c` (`:162-163`), and the identity
`a·A/(K+A) = a − a·K/(K+A)` is not an identity once `a`, `K` and `a·K` are all the single symbol `c`.
Measured on the corpus with v2's own rewrite:

```
components rewritten by PC2b: 28      of which M3 scores a MATCH: 0
systems where all rewritten components matched under M3: 0/80     [threshold: >= 76/80]

original : 0.1954 + 0.8878 * x_0 * 1/(0.8392 + x_0) + -1 * 0.3968 * x_0
   sk    : c*(x_0 + (c + x_0)*(x_0 + 1))/(c + x_0)
affine   : 0.1954 + 0.8878 - 0.7450417 * 1/(0.8392 + x_0) + -1 * 0.3968 * x_0
   sk    : c*((c + x_0)*(x_0 + 1) + 1)/(c + x_0)          -> M3 = 0.0
```
Leaving `a * K` as two literals rather than folding the product does not help — the skeleton is byte-identical
(`c*((c + x_0)*(x_0 + 1) + 1)/(c + x_0)`) and M3 is still 0.0.

**The consequence.** Gate A→B item (iii) cannot pass. `v2:1156-1158` then applies: "*If the control battery
fails, Part B may still proceed* … but Part A is reported `undecidable` and Part C is **not** run." So the
cycle spends up to 16 CPU-core-hours and cannot deliver its primary, its secondaries, or Part C. And there is
no legal remedy mid-cycle: `v2:1407` and rule 01 item 3 forbid changing a threshold to rescue a result, and
§14 has no named contingency for a control-battery failure.

**Required fix.** Either (a) set `gating: false` and reclassify PC2b as a **documented limitation of M3**,
reported `descriptive` — which is itself a real deliverable, since affine decomposition is E0's second
disclosed mechanism and is `B-R1` of Part B's rewrite set (`v2:770`); or (b) re-derive PC2b's threshold from
a pre-run measurement on the **train** split (240 systems, never an endpoint) so the threshold reflects what
the skeleton algebra can actually prove. (a) is preferred and cheaper.

### V2-CRIT-2 — PC3b's frozen **gating** threshold is failed by a faithful implementation; the control has no eligibility requirement

**Evidence.** `v2:712` (§7.7): "**PC3b** permuted variable (**negative** control) | truth with two variable
indices swapped in one component (`dimension ≥ 2` only, n = 60) | specificity of M3 | **≥ 58/60 NON-match**".
JSON: `"gating": true`. Gate A→B item (iii), `v2:1153`: "PC3b ≥ 58/60".

**The defect.** Implementing the frozen sentence literally — swap the two lowest variable indices in the
first multi-variable component of each dim ≥ 2 system — gives:

```
PC3b: NON-match 50/60      [v2 frozen threshold: >= 58/60]
M3 wrongly matched the swapped truth in 10 systems -- all 10 of R08
e.g. R08_validation_d101_000:
  '1.128 * x_0 * x_1 * 1/(0.4844 + x_0 * x_1) + -1 * 0.5379 * x_2'
  '1.128 * x_1 * x_0 * 1/(0.4844 + x_1 * x_0) + -1 * 0.5379 * x_2'
```
In all 10 R08 systems the swapped pair appears **only inside the commutative product `x_0 * x_1`**, so the
swap is a mathematical **no-op** and M3 is *correct* to return a match. The control, not the matcher, is
broken. Independently, M3 is invariant to variable permutation whenever the coefficient structure is
symmetric, because constants collapse:
`symbolic_recovery("1.0*x_0 + 2.0*x_1", "1.0*x_1 + 2.0*x_0")["skeleton"] == 1.0`.

**The consequence.** Same as V2-CRIT-1: Gate A→B fails, Part A `undecidable`, Part C not run. Worse, whether
the gate passes depends on an **unspecified implementation choice** — swapping `x_0 ↔ x_2` in R08 instead
would change the function and pass. A frozen hard gate whose satisfaction is implementation-dependent is not
frozen.

**Required fix.** Define PC3b's **eligible set** as swaps verified to change the function (SymPy
non-equivalence, or `numeric_equivalent`), enumerate and report it, and state the threshold against it —
exactly the amendment v2 already applied to PC3a for AUDIT-MIN-9 (`v2:711`: "**Eligible set defined** … **48**
under the auditor's rewrite"). v2 applied its own amendment to PC3a and not to PC3b.

### V2-CRIT-3 — the battery contains **no positive control for the gain indicator**, and both controls tied to E0's disclosed mechanisms yield gain = 0 for instrument reasons

**Evidence.** `v2:210-212` (§1): "This is a **null-shaped primary**, so §9 specifies a mandatory control
battery and a null-credibility ladder **without which the null is uninterpretable**." §7.7's battery is
PC0, PC0-CAS, PC1, PC2a–d, PC3a–b. `v2:575` (§7.3) justifies predicting a non-zero L-gain thus:
> "real candidates spell decay as a signed constant (P4), **which M0 cannot match** and M3 can (Q1: PC2a =
> 80/80). Linear-decay components are where that rewrite is the whole component."

**The defect, measured over all 170 validation components** (M0 = `formula_metrics(teacher_infix, ·)`,
M3 = `symbolic_recovery(·)["skeleton"]`, gain = `1[M3 ∧ ¬M0]`):

| control / rewrite | M0 | M3 | **gain** |
|---|---|---|---|
| **PC2a** — `-1*k*x_i → (-k)*x_i`, the P4 asymmetry, all 80 truths changed | **170/170** | 170/170 | **0/170** |
| **PC2b** — affine decomposition (V2-CRIT-1) | — | 0 | **0/170** |
| PC2c-like — reverse `add` operands | 40/170 | 40/170 | **0/170** |
| PC2d-like — reverse `mul` operands | 40/170 | 40/170 | **0/170** |
| `*1.0` wrapper | 170/170 | 170/170 | **0/170** |
| PC0 / PC1 — identity | 1 by construction | 1 | **0** by construction |
| PC3a / PC3b | negative controls | | n/a |

**`M0` scores 170/170 on PC2a.** v2's statement that M0 "cannot match" the P4 rewrite is **false** in v2's own
mandated configuration. The reason is a direct consequence of the AUDIT-CRIT-2 fix: with infix fed to both
sides, `parse_system` folds `-1 * 0.3968 * x_0` into `-0.3968 * x_0` before M0's skeleton is formed
(demonstrated: `formula_views("0.1954 + 0.8878 * x_0 * 1/(0.8392 + x_0) + -1 * 0.3968 * x_0",
as_prefix=False)["true_formula_prefix"]` = `add,add,0.1954,mul,-0.3968,x_0,mul,mul,0.8878,inv,add,0.8392,x_0,x_0`).
M0 is therefore **not a naive string matcher** — it is a canonical-prefix, constant-collapsed,
exponent-aware tree matcher, and it already absorbs E0's flagship mechanism.

**The consequence.** No control in the battery demonstrates that `gain` can ever return 1. A primary of
`K = 0` would be *indistinguishable* from an instrument incapable of producing a gain — precisely the failure
mode `v2:210-212` says the battery exists to exclude. Under v2's own §7.7 short-circuit rule ("A control
whose rewrite is absorbed by `canonical_exact` tests nothing about M3's own path; any such control is reported
as `short_circuited` and its threshold is evaluated on the non-short-circuited subset"), **PC2a is fully
short-circuited and its non-short-circuited subset is empty** — yet Gate A→B (iii) hard-gates on PC2a = 80/80.
The document contains the machinery to detect that its flagship control is vacuous and simultaneously gates
on it.

**A viable positive control exists** — I verified it, so this fix is actionable, not aspirational. A
common-denominator rewrite (`sympy.together` on each truth component) gives, over all 170:

```
M0 40/170    M3 140/170    GAIN 100/170
```

**Required fix.** (i) Add a preregistered **positive control on the `gain` indicator itself** — a rewrite
class M3 proves and M0's canonical tree does not — with its threshold and eligible set developed on the
**train** split. (ii) Correct `v2:575`: M0 *does* match the P4 rewrite. (iii) Record PC2a as
`short_circuited: true` per §7.7's own rule, and remove or restate its Gate A→B hard threshold, since a
control with an empty non-short-circuited subset cannot gate anything.

---

## 4. MAJOR findings

### V2-MAJ-1 — v2 asserts three times that `_approximately_equivalent` and the `:205` fallback do not run; both execute on every M3 comparison

**Evidence.** `v2:409` (§3 seeds): "with M3 pinned to `["skeleton"]` the non-random hard-coded grid in
`_approximately_equivalent` (`equation_metrics.py:72-73`) is not called at all." `v2:620-623` (§7.4):
"`_approximately_equivalent` is **not called** (it is reachable only through `["equiv"]` at `:203`); the
hidden fallback `except Exception: equiv = skeleton` at `:205` is **not reachable**." `v2:1478` (§15) repeats it.

**The defect.** `symbolic_recovery` builds its return dict **eagerly** at `:207-212`; Python has no lazy dict
values. A caller reading only `["skeleton"]` still executes the entire equiv block at `:195-205`: two
`sympify` calls, a `_timed_simplify(true_parsed - pred_parsed)` at `:200` on the **un-skeletonized**
expressions (bounded by `SYMPY_OP_TIMEOUT_SEC = 10.0`, `:21`), and `_approximately_equivalent` at `:203`
whenever `diff != 0 and skeleton == 1.0`. The `:204-205` `except Exception: equiv = skeleton` also executes.

**What survives.** Reading `["skeleton"]` genuinely cannot be contaminated: `skeleton` is finalized at
`:187-193`, strictly before the equiv block, and `:205` writes only to the local `equiv`; data flow is
one-directional (`skeleton → equiv`, never back). And `_approximately_equivalent`'s grid is non-random
(`:84-85`: `base = [0.2, 0.7, 1.3, 1.9]`, `args = [base + 0.11*index …]`), so v2's determinism conclusion
holds. **The AUDIT-MAJ-1 pinning fix is substantively correct.**

**What does not survive.** (a) §7.5's enumeration of "the specific surfaces that must be labeled, each
verified present in the code" omits the `:200` timeout, which is a live 10-second-per-comparison sink;
(b) an implementer reading §7.4 will treat `:195-205` as dead code and will not budget for it;
(c) the compute basis quietly depends on it having been included in Q6's measurement (it was — see V2-OK-8).

**Required fix.** Correct all three sentences; add the `:200` `_timed_simplify` timeout to §7.5's surface
list; fix the citation `:72-73` → `:84-85`.

### V2-MAJ-2 — the in-flight implementation substitutes a different function for the pinned M3, with no equivalence test

**Evidence.** `v2:361` (§2.5) freezes "the primary endpoint, its stratum definitions and its matcher level
(M3, pinned to `symbolic_recovery(...)["skeleton"]`)". The uncommitted working tree adds
`skeleton_equivalence_with_reason` to `src/evaluation/equation_metrics.py` and `src/gpu_runclaude1/matcher.py`
calls **that**, not `symbolic_recovery(...)["skeleton"]`:
```
from evaluation.equation_metrics import skeleton_equivalence_with_reason
```
The new function skips the equiv block entirely, so it is **faster** than the pinned call and returns the
same value on the inputs I checked — but it is not the frozen instrument, and it changes the measured cost
basis. `symbolic_recovery` and `to_skeleton` were themselves **refactored**, not merely extended.

**Consequence.** The instrument of record and the instrument that runs are different functions, with no
preregistered test asserting they agree. §17 imposes exactly this discipline on Part C
("that `teacher_forcing_loss` is **extended, not modified**") and imposes nothing analogous on
`equation_metrics.py`.

**Required fix.** Either freeze M3 as `skeleton_equivalence_with_reason` **plus** a preregistered regression
test asserting bit-identical `["skeleton"]` agreement with `symbolic_recovery` over a fixed corpus sample, or
require the pinned call. Extend §17's "extended, not modified" clause to `equation_metrics.py`.

### V2-MAJ-3 — the designated "interval of record" is degenerate at the predicted outcome and produces the sentence §9.5 forbids

**Evidence.** `v2:516-518` (§7.1): "(b) a **two-stage cluster bootstrap** 95% percentile interval … 10,000
resamples, seed 20260909 — **this is the interval of record**". `v2:1087-1092` (§9.5 item 1) mandates
verbatim: "The family-clustered 95% upper bound on the per-component gain rate is [value]".

**The defect.** At `K = 0` every one of the 130 component indicators is 0, so **every** bootstrap resample
yields 0 and the percentile interval is exactly **[0, 0]**. The mandated sentence then reads "the
family-clustered 95% upper bound … is 0.0000", which licenses precisely what §9.5 item 1 forbids
("the gain rate is zero") — rule 01 item 8. `v2:985-989` (§9.2) tries to cover this — "If the observed count
is zero the ICC is not estimable … the family-clustered bound is **automatically** the bound of record" — but
"the family-clustered bound" is ambiguous between interval (b) (degenerate [0,0]) and interval (c) (the
8-cluster Wilson, `0/8 → [0, 0.3244]`, `v2:975`). Since §7.1 already named (b) the interval of record, the
ambiguity resolves the wrong way.

**Required fix.** Freeze that at `K = 0` the bound of record is interval **(c)**, and add an explicit
prohibition on reporting a bootstrap percentile bound of 0 as an upper bound.

### V2-MAJ-4 — the primary's effect size of record uses the cross-reduction comparison §2.1 explicitly forbids

**Evidence.** `v2:204-207` (§1): "The preregistered effect size E0 requires is **0.0525** — the
component-level in-beam rate the frozen matcher already achieves corpus-wide (P0b)." §7.3's entire power
table and §9.5 item 1's mandated sentence are built on `p = 0.0525`. But `v2:281-284` (§2.1) freezes:
> "(i) an `ANY`-over-12 rate is **not comparable** to GPU_RUN5's per-cell rate except at exactly zero, and no
> artifact may present them as the same quantity improved"

**The defect.** P0b = 107/2040 and I verified `2040 = 170 components × 12 cells` — a per-(component, cell)
rate. The primary is an **ANY-over-12-cells** rate over `|H|` components. M0's own rate under the
*primary's* reduction lies in `[9/170, 107/170] = [0.053, 0.629]` (STAT-M1's admissible range, which v2
itself quotes at `v2:670`). So v2 sets the primary's magnitude, its falsification claim and its power
statement using the exact comparison §2.1 prohibits. The numerical coincidence that `107/2040 ≈ 9/170` (both
≈ 0.053, because there are 12 cells) makes the choice *conservative for the power figure* — a larger true `p`
would give more power, not less — but 0.0525 is not the quantity the sentence names.

**Required fix.** Restate the effect size on the endpoint's own reduction ("M0's ANY-reduced component rate,
bounded below by 0.053"), or state explicitly that 0.0525 is being used as the arithmetic lower bound of
M0's ANY-reduced rate and note the 12-cell coincidence.

### V2-MAJ-5 — v2's firewall rationale rests on a doctrine the repository contradicts, and the "unspent" seal was already hashed pre-ledger

**Evidence.** `v2:341-345` (§2.4 item 2) justifies the `run_manifest.py` prohibition with: "GPU_RUN5's own
phase 8 (`scripts/phases/gpu_run5_phase8.py:1171-1176`) treats hashing sealed bytes as **the test-open
event**." Verified, and the code is emphatic — `claim_test_open(` opens at `:1170`, then
`:1173-1175`: "*The sole open event is durably recorded above. Only now may sealed bytes be hashed or
deserialized.*" `sealed_hashes = {…sha256_file(Path(path))…}`.

**The defect.** `scripts/phases/gpu_run5_phase4.py:118-119` and `:151-152` already hash
`sealed_official_test.json` during **phase 4**, with no `claim_test_open` and no ledger, and persist the
digest to `phase4/official_corpus_meta.json` as
`2860d829d9077d01258489fb68ed8dcd8a333d6a0e150b8e36b301f28bb1e070` — **byte-identical to the hash v2 §2.4
records for the "UNSPENT — the campaign's only clean seal"**. Under the strong doctrine v2 invokes, that seal
was opened before C0001 existed. Under the weak doctrine implied by the same file's own
`"test_generated_not_evaluated": true`, hashing is not opening and phase 8's hash-binding step is ceremonial.
**Both doctrines are live in the tree**, and v2's provenance hash for the untouched seal came from the
pre-ledger event.

Second, factual: **7 sealed files exist, not 3.** `find results/runs -name 'sealed*'` returns, besides v2's
three, `gpu_run5_20260823_8cd0b6fa/phase2/sealed_test.json` + `…_family_holdout_test.json` and
`gpu_run5_20260823_fec3a894/phase2/{same two}` — four files in two abandoned run directories, none with a
ledger. §2.4's table (`v2:325-330`) lists three. v2's guard is a pattern match on the resolved filename
(`sealed*`), which **does** cover all seven, so leakage risk is not increased; the record is what is wrong.

**Required fix.** State which test-open doctrine v2 means (the prohibition is prudent under either).
Correct §2.4's inventory to 7. Add a `research_state.md` §8 defect recording that GPU_RUN5 phase 4 hashed the
"clean" seal outside any ledger — this bears on whether that seal is genuinely clean for a future cycle,
which is a campaign-level fact, not a C0001 one.

### V2-MAJ-6 — `sealed_paths_read` is not a computed guarantee; the instrumented opener is a convention, not an interception (AUDIT-MAJ-2 not fully closed)

**Evidence.** `v2:348-350` (§2.4 item 3): "**An instrumented opener records every path C0001 opens**, and
`sealed_paths_read` is a **computed** field, never a hardcoded `[]`. An assertion raises if any resolved path
matches `sealed*`." Gate 0 item 5 (`v2:1136`) depends on "`sealed_paths_read` computed and empty".

**The defect.** As designed in v2 and as built in the working tree
(`src/gpu_runclaude1/io_allowlist.py:InstrumentedOpener`), the mechanism is a **sanctioned wrapper class**,
not a `builtins.open` / `sys.addaudithook` interception. Any direct `open(...)`, `json.load(open(...))`,
`np.load`, or `pandas.read_*` in the C0001 code path is invisible to the counter, so `sealed_paths_read: []`
is again an assertion about implementer discipline — the exact failure mode v2 warns about for
`run_manifest.py` ("would … make `sealed_paths_read: []` a false record", `v2:346`). v2 preregisters no lint
or test forbidding direct reads of the source-run root.

**Residual leakage risk is nonetheless low**, and I verified each layer separately: the frozen allowlist
(`v2:335-340`) contains no sealed path and no directory; `require_artifact` now refuses `sealed*`-prefixed
names (`src/gpu_run5/config.py:56-72`, working tree — and it had **zero callers repo-wide** before, so
AUDIT-MIN-5 overstated it as a live bypass); `load_sealed_test` (`config.py:63-67`) raises `PermissionError`
for `int(phase) < 8` exactly as claimed, and v2's declared phases are `R/phase0`–`R/phase4`, all below 8 —
though the real protection is that v2 **never calls it**, not the phase gate; `phase3/cells/` contains 960
files, 0 with "test" in the name; `all_candidates.json` split is `{validation: 47987}`.

**One structural hazard remains named but not eliminated** (AUDIT-MAJ-3): `phase4/fixed_grn_validation_panel.json`,
which is on the allowlist and is read by Gate 0 item 7's smoke, is a **directory sibling** of
`phase4/sealed_official_test.json`. v2's file-level allowlist is the right answer; the point is that any
future relaxation to a directory grain re-opens the hole immediately.

**Required fix.** Preregister the interception mechanism — a `sys.addaudithook("open")` for the duration of
Parts A/B/C, or a test asserting that no module on the C0001 code path performs a direct read of the GPU_RUN5
run root — and downgrade "records every path C0001 opens" to what the mechanism actually guarantees.

### V2-MAJ-7 — implementation has begun and has modified the frozen instrument before this Gate 0 item 3 audit returned

**Evidence.** `git status --short` at audit time:
```
 M src/evaluation/equation_metrics.py     (+86/-19; to_skeleton and symbolic_recovery refactored)
 M src/gpu_run4/records.py                (+17;  FAILURE_REASONS extension, additive, correct)
 M src/gpu_run5/config.py                 (+13;  require_artifact sealed guard, correct)
?? src/gpu_runclaude1/                    (6 modules, 929 lines: matcher, strata, ladder, io_allowlist, constants)
```
Gate 0 item 1 (`v2:1129`) requires "`git status --short` clean or fully explained in the manifest".

**Assessment.** I read the full diff. The `equation_metrics.py` refactor is value-preserving for
`["skeleton"]` on every input — the same two skeleton attempts with the same fall-through, and `skeleton`
computed before and independently of `equiv` — and my PC0 = 170/170 measurement was taken against the
modified tree and matches expectation, so **my findings above are unaffected**. The `records.py` and
`config.py` changes are additive and exactly what v2 §13 and §2.4 item 7 specify. The new
`src/gpu_runclaude1/` package is well-built (see V2-OK-11).

**But**: the M3 implementation of record was edited, uncommitted, with no equivalence test, while a Gate 0
item that exists to authorize the run had not returned. That is a process defect against v2's own gate
ordering and against rule 05.

**Required fix.** Commit the changes with a manifest explanation before Gate 0, and add the equivalence test
of V2-MAJ-2. I have not modified or reverted anything (rule 05).

---

## 5. Compute realism, M2, and enforceability (audit items 3, 4, 5)

### 5.1 Is 795 ms/candidate a sound upper bound for M0+M1+M3? — **YES, verified**

`v2:1259-1263` (§11.1) argues: "v2's endpoint pass runs **M0 + M1 + M3** and never calls
`_sympy_components_equal`. Removing M2 strictly removes work from the measured cascade, so **10.60 core-h is
a measured upper bound**." The gap in the argument is that Q6 measured M1+M2+M3 and **M0 was not in it**, so
"strictly removes work" is not automatic. I measured the actual v2 configuration — 120 real candidates,
15 per family, `random.seed(20260909)`, `formula_metrics` + `compare_formulas(skip_cas=True)` +
per-component `symbolic_recovery`:

```
M0 mean  45 ms      M1 mean  16 ms      M3 mean 594 ms
M0+M1+M3 mean 655 ms   median 608   p95 1480   max 1992
projection for 47,987 candidates: 8.73 single-core-hours    (v2's claimed upper bound: 10.60)
by family (ms): R01 770  R02 226  R03 794  R04 338  R05 631  R06 906  R07 927  R08 647
```
M0 adds 45 ms; removing M2 saves more. **The upper-bound claim holds empirically.** The 12 core-h allocation
and the ≤ 16 of 24 total carry real headroom. `OK`.

`_sympy_components_equal` is genuinely unreachable in v2's configuration: one definition
(`formulas.py:427`), one call site (`:496`) behind `elif not skip_cas:` (`:495`), `formula_metrics` passes
`skip_cas=True` (`gpu_run5/evaluation.py:41`), and `equation_metrics.py` never imports `gpu_run4`. `OK`.

### 5.2 Does PC0-CAS actually exercise the CAS path? — **YES**

PC0-CAS calls `_sympy_components_equal(truth, truth)` **directly** (`v2:702`), so the
`canonical_exact == 1.0` short-circuit at `formulas.py:493-494` — which lives in `compare_formulas`, not in
`_sympy_components_equal` — does not apply. The cost bound is right: `_sympy_components_equal` runs its
per-component loop inside a **single** `time_limit(SYMPY_EQUIV_TIMEOUT_SEC)` (`:437`), so 80 calls × 10 s =
800 s = 0.22 core-h worst case, exactly as `v2:702` states. Q7's truth node range (max 48) doubles to ≤ 96
for truth-vs-truth, well inside a cap of 200. `OK` — but see V2-MIN-5 on how the cap must be raised.

### 5.3 Is cutting M2 sound, or does it remove the only instrument that could detect E0? — **SOUND**

Cutting M2 is correct and I endorse it. `v2:1530-1545` (§18.1) is accurate on every measured claim, and rule
06 forbids a ~66 core-h breach for a **secondary**. M3 has no node cap, and PC0-CAS preserves the instrument
fact as a bounded deliverable. M2 was not "the only instrument that could detect E0": it was the *least*
permissive CAS level in the cascade, and it was structurally incapable of matching R05–R08 at all (100% cap
exceedance). Nothing in v2 depends on CAS equivalence in a load-bearing way — `grep` confirms no endpoint,
gate, or verdict references M2 or `symbolic_equivalent`. `OK`.

The genuine gap that cutting M2 leaves is **not** CAS coverage but the one V2-CRIT-3 names: with M2 gone, M3
is the sole permissive level, and M3's constant collapsing cannot prove affine decomposition (V2-CRIT-1).
So E0's *second* disclosed mechanism now has no instrument at all. That should be stated in §18.1 as a
consequence of the cut, alongside the two substitutes v2 already lists.

### 5.4 Is the integrity ordering mechanically enforceable? — **YES in the implementation, only asserted in v2**

`v2:557-561` (§7.2 step 3) asserts the ordering; `v2:1451-1455` (§14 item 8) makes violation terminal. v2
itself specifies **no mechanism**. The working tree supplies one, and it is good:
`src/gpu_runclaude1/strata.py require_strata_frozen` returns a `StrataFrozenToken` whose **only** constructor
is that function, and it refuses unless both artifacts exist on disk, the strata file's recorded
`sha256_of_component_assignment` re-verifies against its own content, and the ladder file records that same
hash as `sha256_of_component_strata_input`. `matcher.py` requires the token. That is a real capability gate,
not a comment. **Required (MINOR)**: v2 should *name* this requirement so it is frozen rather than
incidental to one implementer's choice — as written, a later reimplementation could satisfy §7.2 by ordering
its own function calls and nothing would detect a violation.

**On the calibration's outcome suppression** (`v2:1272-1276`): "the calibration harness must **discard the
match boolean at the call site**". This is only weakly enforceable. Per-candidate wall time is itself a side
channel on the indicator — a proved match exits at `equation_metrics.py:189`, while a non-match additionally
runs `_timed_equals` at `:190` — and §11.1's sample of 400 candidates is drawn from the **same** 47,987 the
primary scores. Per-family aggregates leak little; per-candidate timings would leak materially. See
V2-MIN-8.

### 5.5 RAM and VRAM

**RAM: safe, verified.** `phase3/all_candidates.json` (174 MB on disk) loads to **0.53 GiB** peak process
RSS. Six worker processes ≈ 3.2 GiB against 52 GiB available. `v2:1240` is sound. `OK`.

**VRAM: monitored, not enforced.** `v2:1174-1176` aborts if "Peak VRAM on GPU 0 > **5.5 GiB** at any sample",
with `gpu_telemetry.jsonl` at a ≤ 10 s interval on a GPU shared with a live desktop. A 10-second sampling
interval is detection after the fact, not a cap, and `nvidia-smi`-visible totals include the desktop's own
allocation. Part C's own target (≤ 3.0 GiB for a 60.6M-param fp32 model, batch ≤ 8, seq ≤ 200) is genuinely
far from the ceiling, so the practical risk is low. See V2-MIN-10.

---

## 6. What v2 introduced that is new (audit item 7)

| new machinery | assessment |
|---|---|
| two-stage family→system cluster bootstrap, 10,000 resamples, seed 20260909 | seeded, but the **generator and draw order are never named** (§7.1, §9.1, §3, and the JSON all give only the seed). §11.1 names `numpy.random.default_rng(20260909)` for the calibration; the interval of record gets nothing. **Not reproducible as specified** — V2-MIN-6. And degenerate at `K = 0` — V2-MAJ-3. |
| NC1–NC5 (§8.3) | well-formed and independently checkable. **NC3's hardest clause is empirically satisfiable and I verified it exactly** (10 distinct payloads per system in 80/80). NC5's `n_in_support ≥ 30` correctly downgrades rather than aborts. `OK`. |
| `cell_input_payload_sha256` (§8.2 step 1a) | fully specified — float64 little-endian bytes, frozen concatenation order `times ‖ observed_trajectory ‖ initial_condition`, each preceded by its shape as little-endian int64. I implemented it verbatim and it reproduces v2's P11 structure exactly. This is the strongest new piece of machinery in v2. `OK`. |
| commutation-orbit mitigation at cap 8 (§8.2 step 5) | says "deterministic traversal" but **never defines the enumeration order**, and *which* 8 of the ~26–664 orbit members are chosen determines the reported `logsumexp`. `descriptive`, gates nothing, so consequence is bounded — V2-MIN-7. |
| `no_gain_observed_bound_only` rung, with the §9.5 item 1 sentence mandated verbatim in a machine-readable field | the right mechanism (labels travel, caveats do not), and correctly generalized from `prior_information_disclosed`. Undermined only by V2-MAJ-3, which would fill `[value]` with 0.0000. `OK once MAJ-3 is fixed`. |
| operating-characteristic tables (§9.3) and the mandated disclosure sentence | a genuine improvement over v1, and the corrected Wilson values at n = 80 are right. `OK`. |
| file-level allowlist + instrumented opener + computed `sealed_paths_read` | substantially closes AUDIT-MAJ-2 but not completely — V2-MAJ-6. |
| `StrataFrozenToken` write-before-match gate | real mechanical enforcement, but present only in the implementation, not frozen in v2 — see §5.4. |

---

## 7. MINOR findings

| id | finding | evidence |
|---|---|---|
| **V2-MIN-1** | `commit_at_freeze = de894b4` (`v2:14`, JSON `/commit_at_freeze`), but v2 was introduced by **`7f507cc`** — `git log --oneline --diff-filter=A -- GPU_RUNclaude1/plans/C0001_preregistration_v2.md`. This is the **same error class as AUDIT-MIN-1**, which v2 corrects for v1 in the row directly beneath. Operationally harmless: §12 re-derives `<short7>` at run start. | `git log` |
| **V2-MIN-2** | The `ModuleNotFoundError` claim is **stale and does not reproduce**. `v2:104` and `v2:355-359` state "six files raise `ModuleNotFoundError: No module named 'scripts'` without `PYTHONPATH=.`". Measured at HEAD: `pytest GPU_RUN5/tests --collect-only -q` → **124 collected, 0 errors, bare**, identical with `PYTHONPATH=.`. `pytest.ini:4` already carries `pythonpath = .` and `:2` already lists `GPU_RUN5/tests` (added in `39ab0fd`, *after* v2's claimed freeze commit `de894b4`). `research_state.md:293-297` already records that the claim "did **not** reproduce" and that `GPU_RUN5/tests/conftest.py` inserts `src/`. v2's §2.4 item 6 presents an already-applied fix as pending. | `pytest.ini`, collection runs, `research_state.md` §8 defect 1 |
| **V2-MIN-3** | Gate 0 item 2's test count is wrong. `v2:1130` says the `-k "firewall or sealed or test_open"` selector is "**green (4 tests)**"; it collects **6** — both tests in `test_gpu_run5_firewall.py` match on the *filename*, including `test_nonfinite_values_are_sanitized_for_strict_json`, which is not a firewall test. A gate stated as an exact count that does not match reality cannot be checked as written. | collection run |
| **V2-MIN-4** | The firewall-ordering assertion v2 relies on is weaker than described. `v2:104` calls `test_gpu_run5_phase8.py:541-544` "the substantive firewall-ordering assertions"; the ordering assertion is at **`:542`** and is `source.index("claim_test_open(") < source.index("load_sealed_test(")` — a **lexical** first-occurrence check on source text, not a runtime ordering check. It would pass even if a later call site violated the order. v2's own new C0001-specific firewall test (§2.4 item 5) is the real protection. | `test_gpu_run5_phase8.py:540-544` |
| **V2-MIN-5** | Raising `LANSR_SYMPY_MAX_NODES` to 200 for PC0-CAS (`v2:702`) must happen **before import**. `SYMPY_MAX_NODES` is read from the environment at `src/gpu_run4/ted.py:15` at import time and bound **by value** into `gpu_run4.formulas` (`formulas.py:13`), so monkeypatching `ted.SYMPY_MAX_NODES` in-process leaves `formulas.py:434` at 40 and PC0-CAS would silently re-measure **28/80** while v2 expects 80/80. Harmless to endpoints (the constant is used nowhere else), but it silently voids the diagnostic. | `ted.py:15`, `formulas.py:13`, `:434` |
| **V2-MIN-6** | Bootstrap RNG unnamed — see §6. Specify the generator (`numpy.random.default_rng`), the draw order (families then systems), and whether resampling is with the same generator stream. | `v2:516-518`, `v2:941`, JSON `/model_and_budgets/seeds` |
| **V2-MIN-7** | Commutation-orbit enumeration order undefined — see §6. | `v2:864-871` |
| **V2-MIN-8** | The §11.1 calibration's outcome suppression is weakly enforceable: per-candidate wall time is a side channel on the match indicator, and the sample is drawn from the primary's own candidates. Restrict `R/phase0/partA_cost_calibration.json` to **per-family aggregates** (mean/median/p95) and failure-label counts; forbid per-candidate timings. | `v2:1272-1276`; `equation_metrics.py:189-190` |
| **V2-MIN-9** | `ComponentCountMismatch` is classified three ways. `v2:601` (§7.4) calls it "an automatic **non-match**"; `v2:640` (§7.5 item 1) lists it among the surfaces to label; `v2:645-647` (§7.5 item 2) **excludes** it from the `could_not_evaluate_rate` numerator; the in-flight `matcher.py` classifies it `COULD_NOT_EVALUATE`, which would feed the 2.0% `undecidable` threshold. **Empirically inert on this corpus** — I measured `(true_dim, n_pred_components)` on the diagonal for all 47,987 candidates (12,000 / 17,998 / 17,989) and **0** of the 2,235 stored component hits under a count mismatch, so the §7.4 rule cannot break the §7.6 reproduction gate. But the spec must pick one classification. | `v2:601`, `:640`, `:645`; measured |
| **V2-MIN-10** | The ≤ 5.5 GiB VRAM ceiling is sampled at ≤ 10 s, not enforced — see §5.5. Add `torch.cuda.set_per_process_memory_fraction` or an explicit allocator cap so the ceiling is a cap rather than a tripwire. | `v2:1174-1176` |

Also noted, not raised as separate findings: A2-S1's predicted L-gain contrast is structurally suppressed if
the 107 sit in L (§2.2 above); §7.2's mechanical enforcement should be frozen in v2, not left to the
implementation (§5.4); §18.1 should record that cutting M2 leaves E0's affine-decomposition mechanism with no
instrument (§5.3).

---

## 8. What v2 gets right — verified positives

Each of these I confirmed by running code or reading data, not by reading v2's claim about it.

| id | verified positive |
|---|---|
| **V2-OK-1** | **`\|H\| = 130`, `\|L\| = 40`** over 170 components, via exactly the path §7.2 prescribes; inside the predicted 130–145 / 25–40; cross-agrees **170/170** with the independent stored `variable_denominator_form` flag. The stratum definition is decidable, seal-free, and the fallback thresholds do not fire. `C = 3`. |
| **V2-OK-2** | The primary is measured **on M0's misses**, not on its successes: 90 of 130 H components lie in families with 0/2040 published M0 component hits, so `m0_any = 0` there by published data. Not structurally near-zero for an uninteresting reason. |
| **V2-OK-3** | The gain indicator is a **conjunction, not a difference**, so it cannot be negative regardless of monotonicity — which matters, because I showed M3 is *not* always a superset of M0. The `m0_any=1, m3_any=0` census (§7.5 item 4) is the correct companion and v2 requires it. |
| **V2-OK-4** | The gain indicator **can** fire: a common-denominator rewrite gives gain 100/170. The endpoint is not vacuous — only its *battery* is (V2-CRIT-3). |
| **V2-OK-5** | **§7.6's reproduction gate is exact and non-degenerate**: 47,987 candidates / 101,963 component comparisons / 2,235 stored component hits / 0 system hits / 107/2040 / all eight per-family counts — every single figure confirmed. Replacing v1's `A-S3 ≥ 0.0525` trigger with this is a large improvement. |
| **V2-OK-6** | **PC0 = 170/170** measured. `symbolic_recovery` has **no** short-circuit on `exact` (unlike `compare_formulas` at `:493-494`), so PC0 genuinely exercises the primary's own path. AUDIT-CRIT-4 is fixed by design. |
| **V2-OK-7** | `_sympy_components_equal` is genuinely unreachable from every v2 endpoint path (1 definition, 1 call site, gated by `skip_cas`, no cross-module import). AUDIT-CRIT-3's hazard is removed, not relabelled. PC0-CAS's direct call does exercise the CAS path, with the cost bound (0.22 core-h) correctly derived from the single shared `time_limit`. |
| **V2-OK-8** | **Compute basis confirmed and conservative.** Measured M0+M1+M3 = **655 ms/candidate → 8.73 core-h** against v2's claimed measured upper bound of 10.60. §11.1's argument is sound even though M0 was not in Q6's measurement. |
| **V2-OK-9** | **RAM safe**: 0.53 GiB per process; 6 workers ≈ 3.2 GiB of 52 GiB. Process-based parallelism is the right call — `_time_limit`'s guard genuinely no-ops off the main thread (`equation_metrics.py:36-42`, and the docstring at `:32-34` says so outright), so thread parallelism would silently remove every SymPy wall-clock guard. AUDIT-MAJ-5 fixed by design. |
| **V2-OK-10** | **NC3 / STAT-C3 verified exactly**: 10 distinct `cell_input_payload_sha256` per system in **80/80**; 3 clean cells byte-identical in **80/80**; `input_trajectory_checksum` constant within each system in **80/80**. The relabelling of that field as a system-identity check, and the payload digest that replaces it, are both empirically correct. |
| **V2-OK-11** | **The integrity ordering is mechanically enforced** in the in-flight implementation via a capability token (`strata.py require_strata_frozen` → `StrataFrozenToken`), with self-hash verification of the strata file and cross-hash binding of the ladder file. Better than v2 promised. |
| **V2-OK-12** | Firewall inventory clean where it matters: `phase3/cells/` = 960 files, **0** containing "test", 960 containing "validation"; `all_candidates.json` split `{validation: 47987}`. `load_sealed_test` raises for `phase < 8` exactly as claimed (`config.py:63-67`). `require_artifact`'s `sealed*` guard is applied (and had zero callers before, so AUDIT-MIN-5 overstated the risk). |
| **V2-OK-13** | Housekeeping all verified: branch correct; **27** run directories + 1 stray log = 28 entries (v2's corrected count is right, v1's 28 was wrong); no `results/runs/gpu_runclaude1*`; checkpoint SHA256 `56754040be5aa92ed4767fc43ee2008faa293f87c12b643e66c7df3e1623a5e8` matches; `evaluation.py:39` is the `formula_metrics` def and `:41` the `compare_formulas` call (v2's correction of v1's `:40` is right); `records.py:50` FAILURE_REASONS correct; `formulas.py:493` short-circuit guard correct. The JSON twin parses and agrees with the MD on every value I cross-checked. |
| **V2-OK-14** | The retraction is honestly and completely propagated. No surviving v2 element depends on a 0/2040 baseline; `C-NEG` is deleted with the right reasoning (a re-derivation is a positive control, not a comparator — rule R1); §16 correctly separates in-beam component coverage from `component_exact_loss` under intervention and refuses to move between them; A2-S7 is a statement, not a measurement. |
| **V2-OK-15** | Rule compliance across the board: rule 04 (§16, zero layer estimands, verified — no probe/CKA/gradient/ablation/IOLE/selective-FT anywhere); rule 03 (four recovery resolutions kept distinct, generation/oracle/selected separated, invalid and failed candidates retained in every denominator, the 30-field schema extended not replaced); rule 01 item 5 (`v2:738-742`, no exclusion from the primary, ever); rule 02 (no seal consumed, no training, no tuning, no new decoding); rule 06 (no ceiling increase requested — v2 re-scoped instead, which is the correct response to a projected breach); rule 05 (new run ID, no overwrite, `git reset --hard` and force-push forbidden). |
| **V2-OK-16** | The disclosure architecture is unusually strong and I could not find a hole in it: §0's ledger distinguishes published comparators from reviewer-measured quantities from deductions; Q1 and Q2 are correctly downgraded from controls to **verifications** because their values are now known; `prior_information_disclosed` and `verdict_scope_sentence` are mandatory machine-readable fields; §9.5's wording constraints are specific rather than gestural; §10.4 states what each part delivers **on failure**, which is the mark of an experiment rather than a demonstration. |

---

## 9. Findings table by severity

| id | severity | finding | evidence |
|---|---|---|---|
| **V2-CRIT-1** | **CRITICAL** | PC2b's gating threshold (M3 ≥ 76/80) is unachievable: M3 scores **0** on the affine decomposition because `to_skeleton` collapses all constants to one symbol `c`, under which `a·A/(K+A) = a − a·K/(K+A)` is not an identity. Gate A→B (iii) fails deterministically ⇒ Part A `undecidable`, Part C not run. | `v2:709`, `v2:1152`, JSON `gating:true`; `equation_metrics.py:153-166`; measured 0/28 components, 0/80 systems |
| **V2-CRIT-2** | **CRITICAL** | PC3b's gating threshold (≥ 58/60 NON-match) is failed by a faithful implementation — **50/60** measured, all 10 failures R08, where the swapped pair appears only as the commutative `x_0 * x_1` so the swap is a no-op. No eligibility requirement that the swap change the function; v2 applied that amendment to PC3a and not PC3b. | `v2:712`, `v2:1153`, JSON `gating:true`; measured 50/60 |
| **V2-CRIT-3** | **CRITICAL** | No positive control for the **gain** indicator. **M0 scores 170/170 on PC2a**, so E0's flagship disclosed mechanism (P4) is already absorbed by M0 in v2's own infix configuration, and `v2:575`'s "which M0 cannot match" is false. Every control yields gain 0; a `K = 0` primary would be indistinguishable from an instrument that cannot produce a gain — the exact failure `v2:210-212` says the battery exists to exclude. | `v2:575`, `v2:694-720`, `v2:210-212`; measured PC2a M0 170/170, gain 0/170; viable control found (gain 100/170) |
| **V2-MAJ-1** | MAJOR | v2 asserts 3× that `_approximately_equivalent` and the `:205` fallback do not run; the dict at `:207-212` is eager, so the whole equiv block executes on every M3 call, including a 10 s `_timed_simplify` at `:200` that §7.5's surface list omits. `["skeleton"]` is genuinely uncontaminated, so the pinning fix survives. | `v2:409`, `:620-623`, `:1478`; `equation_metrics.py:195-212` |
| **V2-MAJ-2** | MAJOR | The implementation calls `skeleton_equivalence_with_reason`, not the pinned `symbolic_recovery(...)["skeleton"]`, with no preregistered equivalence test; `to_skeleton` and `symbolic_recovery` were refactored, not extended. | `v2:361`; `git diff src/evaluation/equation_metrics.py`; `matcher.py` imports |
| **V2-MAJ-3** | MAJOR | The designated interval of record (two-stage bootstrap percentile) is exactly **[0, 0]** at the predicted `K = 0`, so §9.5 item 1's mandated sentence would report an upper bound of 0.0000 — licensing the claim §9.5 forbids. §9.2's "family-clustered bound" is ambiguous between intervals (b) and (c). | `v2:516-518`, `:985-989`, `:1087-1092` |
| **V2-MAJ-4** | MAJOR | The effect size of record (0.0525, a per-(component,cell) rate over 2040 = 170×12) is compared against an ANY-over-12 endpoint — the cross-reduction comparison `v2:281-284` explicitly forbids. M0's rate under the primary's own reduction is in [0.053, 0.629]. | `v2:204-207`, `:281-284`, `:568-598`; 2040 = 170×12 verified |
| **V2-MAJ-5** | MAJOR | The firewall rationale invokes GPU_RUN5's "hashing = test-open" doctrine, but `gpu_run5_phase4.py:118-119,151-152` already hashed `sealed_official_test.json` pre-ledger, and its digest `2860d829…` is the very hash v2 records for the "unspent clean seal". Also **7** sealed files exist, not 3. | `v2:325-330`, `:341-346`; `gpu_run5_phase4.py`; `phase8.py:1170-1176`; `find results/runs -name 'sealed*'` |
| **V2-MAJ-6** | MAJOR | `sealed_paths_read` is not a computed guarantee: the instrumented opener is a sanctioned wrapper, not a `builtins.open`/audit-hook interception, so any direct read is invisible to it. AUDIT-MAJ-2 substantially but not completely closed. Residual leakage risk is low (allowlist file-level, directories forbidden, `require_artifact` guarded, `load_sealed_test` never called). | `v2:348-350`, `:1136`; `io_allowlist.py:InstrumentedOpener` |
| **V2-MAJ-7** | MAJOR | Working tree dirty with the frozen instrument modified before Gate 0 item 3 returned: 3 modified `src/` files + 929 lines of new `src/gpu_runclaude1/`. Diff read and judged value-preserving; findings unaffected. Violates Gate 0 item 1 as written. | `git status --short`, `git diff` |
| **V2-MIN-1…10** | MINOR | freeze-commit vs introducing commit; stale `ModuleNotFoundError` claim (124 collect clean, `pytest.ini` already fixed); Gate 0 item 2's "4 tests" is 6; `:542` ordering assertion is lexical not runtime; `LANSR_SYMPY_MAX_NODES` must be set pre-import; bootstrap RNG unnamed; orbit enumeration order undefined; calibration timing side channel; `ComponentCountMismatch` classified three ways (empirically inert); VRAM cap sampled not enforced | see §7 |
| **V2-OK-1…16** | OK | see §8 | see §8 |

**Counts: 3 CRITICAL · 7 MAJOR · 10 MINOR · 16 verified positives.**

---

## 10. Verdict

# `AMEND_BEFORE_RUN`

v2 is a substantially better document than v1. All 8 prior CRITICALs are addressed **by design**, not by
wording; the new primary endpoint is a genuine improvement on the one it replaces and is well-posed; the
compute basis is honest and I independently confirmed it is conservative; the Part C identity protocol is the
best-verified piece of machinery in the cycle; and the disclosure architecture is strong. I found no leakage
path to a seal, no training, no tuning, no final-test access, and no layer-estimand claim.

The three CRITICALs are not design-philosophy objections. They are a single concrete cluster: **the control
battery cannot validate the endpoint it exists to validate, and two of its thresholds are unachievable, so
Gate A→B fails deterministically and the cycle would burn its full CPU budget to report `undecidable`.** All
three share one root cause that v2 never states: `to_skeleton` collapses **every** constant to the same
symbol `c`, which makes M3 (a) unable to prove affine decomposition, (b) invariant to symmetric variable
permutation, and (c) not a strict superset of M0 — while the AUDIT-CRIT-2 fix simultaneously made M0 a
canonicalizing tree matcher that already absorbs E0's flagship mechanism. v2 describes M0 as "the frozen
**string** matcher" throughout; it is not one, and the whole M0-vs-M3 contrast needs restating in those terms.

All three are fixable now, before Stage 4, without a new cycle ID, without a ceiling increase, and without
touching the primary endpoint, the strata definitions, the aggregation order, or the ladder.

## 11. Minimum amendment list, in priority order

1. **PC2b**: set `gating: false`; reclassify as a **documented limitation of M3** (`descriptive`) and record
   that M3 cannot prove affine decomposition under constant collapsing — or re-derive its threshold from a
   train-split measurement. Remove it from Gate A→B (iii). *(V2-CRIT-1)*
2. **PC3b**: define the **eligible set** as swaps verified to change the function; enumerate and report it;
   state `≥ 58/60`-equivalent threshold against that set. *(V2-CRIT-2)*
3. **Add a positive control on the `gain` indicator itself** (a rewrite class M3 proves and M0's canonical
   tree does not; `sympy.together` gives gain 100/170 and is a candidate), threshold developed on the train
   split. Correct `v2:575` ("which M0 cannot match" — M0 matches it 170/170). Mark PC2a
   `short_circuited: true` per §7.7's own rule and remove its Gate A→B hard threshold. *(V2-CRIT-3)*
4. Freeze that at `K = 0` the **bound of record is interval (c)**, the 8-cluster Wilson; forbid reporting a
   bootstrap percentile upper bound of 0. *(V2-MAJ-3)*
5. Restate the primary's effect size on the endpoint's own ANY-over-12 reduction (≥ 0.053), or label the
   0.0525 coincidence explicitly as the arithmetic lower bound of M0's ANY-reduced rate. *(V2-MAJ-4)*
6. Correct §3, §7.4 and §15: `_approximately_equivalent` and the `:205` fallback **do** execute; add the
   `:200 _timed_simplify` timeout to §7.5's failure-surface list; fix `:72-73` → `:84-85` and
   `:38-45` → `:36-42`. *(V2-MAJ-1)*
7. Resolve the M3-implementation divergence: freeze `skeleton_equivalence_with_reason` **plus** an equivalence
   regression test against `symbolic_recovery(...)["skeleton"]`, or require the pinned call. Extend §17's
   "extended, not modified" clause to `equation_metrics.py`. Commit the working tree or explain it fully in
   the manifest before Gate 0. *(V2-MAJ-2, V2-MAJ-7)*
8. Specify the instrumented opener's **interception mechanism** (`sys.addaudithook("open")`, or a test
   forbidding direct reads of the GPU_RUN5 run root) and downgrade the "records every path C0001 opens"
   claim to what the mechanism guarantees. *(V2-MAJ-6)*
9. Correct §2.4's sealed inventory to **7** files; state which test-open doctrine v2 means; add a
   `research_state.md` §8 defect recording GPU_RUN5 phase 4's pre-ledger hashing of
   `sealed_official_test.json`. *(V2-MAJ-5)*
10. Freeze the §7.2 enforcement mechanism (the `StrataFrozenToken` gate) in v2 rather than leaving it to the
    implementation; name the bootstrap generator and draw order; define the commutation-orbit enumeration
    order; require `LANSR_SYMPY_MAX_NODES=200` to be set **before import** for PC0-CAS; restrict
    `partA_cost_calibration.json` to per-family aggregates; resolve `ComponentCountMismatch`'s
    classification; add a hard VRAM cap. *(V2-MIN-5…10, §5.4)*
11. Correct `commit_at_freeze` to the commit that introduces v2; drop the stale `ModuleNotFoundError` claim
    (already contradicted by `research_state.md` §8 defect 1 and by measurement); fix Gate 0 item 2's
    "(4 tests)" → 6. Reconcile this file's name with §12.1's
    `C0001_reproducibility_audit_v2.md`. *(V2-MIN-1…3)*
12. Record `|H| = 130`, `|L| = 40` and the per-family H/L breakdown in **§0.3** as auditor-disclosed prior
    information, and downgrade §7.3's stratification prediction from fully blind to "partly derivable from
    the family-level census plus P0b" — because L is non-empty in exactly and only the three families that
    carry all 107 M0 hits. *(§2.4)*
13. Add to §18.1 that cutting M2 leaves E0's affine-decomposition mechanism with **no** instrument, given
    V2-CRIT-1. *(§5.3)*

Items 1–3 are the blockers. Items 4–5 must be fixed before any result is reported. Items 6–13 should be
folded into the same amendment pass.

## 12. Gate 0 item 3

> **NOT SATISFIED.** Gate 0 item 3 requires "a fresh Stage-5 reproducibility audit of the **v2** design
> reports **zero CRITICAL** findings". This fresh audit reports **3 CRITICAL** findings (V2-CRIT-1,
> V2-CRIT-2, V2-CRIT-3). Under v2's own Gate 0 and under rule 07, **the full run is blocked** until they are
> amended and re-audited. The re-audit can be narrow: it needs to confirm only the amended control battery,
> the `K = 0` bound of record, and the restated effect size. Everything else in §8 is already verified.

---

## 13. Reproduction

Environment: `source /home/blabo/miniconda3/etc/profile.d/conda.sh && conda activate lansr310`; run from the
repo root with `PYTHONPATH=src` for the `gpu_run4`/`gpu_run5`/`evaluation` imports. Source run root
`R5 = results/runs/gpu_run5_20260823_ddd267b0`. No file was modified by this audit; no sealed artifact was
read, hashed, or deserialized.

| claim | how to reproduce |
|---|---|
| `\|H\| = 130`, `\|L\| = 40`, family/dim breakdown, 170/170 agreement with the stored flag | for each of the 80 rows of `R5/phase2/validation.json`, for each `teacher_components_infix[i]`, take `gpu_run4.formulas.formula_views(c, as_prefix=False)["components"][0]` and walk the tree for an `inv` node with a variable leaf in its argument subtree; compare with `row["structure"]["component_flags"][i]["variable_denominator_form"]` |
| 47,987 / 101,963 / 2,235 / 0 system hits; count-mismatch diagonal | iterate `R5/phase3/all_candidates.json`, summing `len(component_exponent_aware_skeleton_exact)` and its `==1.0` entries, and `Counter((dimension, len(candidate_exponent_aware_skeleton.split(" \| "))))` |
| 107/2040 and the eight per-family counts | sum `component_true_exponent_aware_skeleton_in_beam` over the 960 records of `R5/phase3/beam_groups.json`, grouped by `family` |
| PC0 = 170/170 | `evaluation.equation_metrics.symbolic_recovery(c, c)["skeleton"]` for all 170 `teacher_components_infix` |
| **PC2a: M0 170/170, gain 0/170** | rewrite `-1 * k * x_i` → `(-k) * x_i` by regex in `teacher_infix` and each `teacher_components_infix`; M0 = `gpu_run5.evaluation.formula_metrics(teacher_infix, rewritten)["component_exponent_aware_skeleton_exact"][i]`, M3 = `symbolic_recovery(orig_i, rewritten_i)["skeleton"]`; gain = `M3 ∧ ¬M0` |
| **PC2b: M3 0/28 components, 0/80 systems** | apply `a * A * 1/(K + A) → a - (a*K) * 1/(K + A)` to each component; also test the unfolded `a - a * K * 1/(K + A)`; compare `to_skeleton` of both sides |
| **PC3b: 50/60 NON-match, 10 R08 failures** | for each dim ≥ 2 system, swap the two lowest variable indices in the first component containing ≥ 2 distinct variables; `symbolic_recovery(orig, swapped)["skeleton"]` |
| M3 invariant to symmetric variable permutation | `symbolic_recovery("1.0*x_0 + 2.0*x_1", "1.0*x_1 + 2.0*x_0")["skeleton"]` → `1.0` |
| gain **is** achievable: 100/170 | rewrite each component with `sympy.together(sympify(c))`; same M0/M3/gain computation as PC2a |
| M3 not a superset of M0 (M0 3/20 vs M3 0/20) | same, with `sympy.apart(expr, first_free_symbol)` on the first 20 systems |
| M0+M1+M3 = 655 ms → 8.73 core-h | `random.seed(20260909)`; 15 candidates per family from `all_candidates.json`; `perf_counter` around `formula_metrics`, then `compare_formulas(..., skip_cas=True)`, then per-component `symbolic_recovery(true_component_raw, cand_component_raw)` using `formula_views(..., as_prefix=False)["components_raw"]` |
| RSS 0.53 GiB | `resource.getrusage(RUSAGE_SELF).ru_maxrss` after `json.load` of `all_candidates.json` |
| NC3: 10 distinct payloads per system in 80/80 | for each of the 960 `R5/phase3/cells/*_validation_*.json`, SHA256 over `np.asarray(o[k], dtype="<f8")` for `k` in `("times","observed_trajectory","initial_condition")` from `observations["input"][0]`, each array preceded by `np.asarray(a.shape, dtype="<i8").tobytes()`; group by `system_id` |
| 124 tests collect clean; 6 selected by Gate 0 item 2 | `python -m pytest GPU_RUN5/tests/ --collect-only -q`; then with `-k "firewall or sealed or test_open"` on the two named files |
| 7 sealed files | `find results/runs -name 'sealed*'` (stat only — do not read) |
| phase-4 pre-ledger hashing | `sed -n '110,155p' scripts/phases/gpu_run5_phase4.py`; compare `phase4/official_corpus_meta.json:sealed_official_test.json` against v2 §2.4's recorded hash |
