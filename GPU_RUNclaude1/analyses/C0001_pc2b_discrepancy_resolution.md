# C0001 — resolution of the PC2b discrepancy (110/170 vs 0/28)

**Date**: 2026-09-09. **Resolved by**: supervisor, by direct measurement.
**Status**: closed. The frozen v2.1 expectation stands; the implementation's measurement was wrong.

## The disagreement

Two agents reported incompatible values for PC2b, the affine-decomposition control:

- `lansr-reproducibility-auditor` (v2 audit, V2-CRIT-1): M3 scores **0**; measured 0/28 components,
  0/80 systems. On that basis v2.1 froze PC2b's expected value at **0 matches on every eligible
  instance**, made it non-gating and descriptive, and declared E0's affine-decomposition mechanism
  (M-ii) **uninstrumented in C0001**, routing it to C0002.
- `lansr-implementation-engineer` (Stage 4): measured **110/170** and flagged it unresolved rather than
  silently overwriting its own hand-verified algebra. That was the correct thing to do — the flag is
  what made this resolvable.

The stake is not cosmetic. If M3 *can* prove affine decomposition, then M-ii has an instrument, and
v2.1 §1.3's scope restriction is wrong.

## Decisive measurement

First, the bare algebra. For a true Hill identity `a*A/(K+A) = a - a*K/(K+A)`:

```
mult : 2.05*x_0/(1.676 + x_0)              skeleton -> c*x_0/(c + x_0)
aff  : 2.05 - 2.05*1.676/(1.676 + x_0)     skeleton -> c*(c + x_0 + 1)/(c + x_0)
numerically identical : True
M3 skeleton match     : 0.0
```

Exactly identical as functions, and M3 still does not match. Constant collapse maps both `a` and `a*K`
to the same symbol `c`, and the rearrangement introduces a `+ 1` term, so the two skeletons are
structurally different trees.

Second, the same question over the real corpus, using the implementation's own rewrite
(`src/gpu_runclaude1/partb.py:349 rewrite_b_r1_affine_infix`) on all 170 validation truth components,
scored **component-wise**:

| quantity | value |
|---|---|
| components total | 170 |
| rewrite fired | **60** |
| of those, verified **true algebraic identity** | **55** |
| of those, **M3 matched** | **0** |

## Verdict

**The auditor is right and v2.1's frozen expectation of 0 is correct.** M3 cannot prove affine
decomposition, even on 55 verified-identical rewrites. E0's M-ii mechanism genuinely has no instrument
in C0001, and routing it to C0002 is the correct call.

**Why the implementation got 110/170.** `src/gpu_runclaude1/controls.py:191 pc2b_affine_decomposition`
rewrites every component of a system, then scores the **whole system** via `result.m3_system`:

```python
for c in components:
    new_c, did = rewrite_b_r1_affine_infix(c)
    rewritten.append(new_c)
    any_rewrite = any_rewrite or did
n_eligible += int(any_rewrite)
result = score_pair(_join(components), _join(rewritten))
passed = result.m3_system == 1.0
n_pass += int(passed and any_rewrite)
```

Components where the rewrite is a no-op are appended unchanged, so they are compared against
themselves and match trivially. `any_rewrite` is an OR across the system, so a system qualifies as
eligible if *any* component was rewritten while the system score is dominated by the untouched ones.
The result is a system-level trivial-match count reported against a component-level denominator. It
measures neither the audit's quantity nor the preregistered one.

## Second finding: a real bug in the rewrite, affecting Part B

**5 of the 60 fired rewrites are not true algebraic identities** (55/60 verified identical). Example
where it fails:

```
orig : 0.1954 + 0.8878 * x_0 * 1/(0.8392 + x_0) + -1 * 0.3968 * x_0
rewr : ((0.1954 + (-0.3968 * x_0)) + (0.8878 + (-((0.8878 * 0.8392) * (1 / (0.8392 + x_0))))))
true identity: False
```

This matters beyond PC2b: **Part B's B-R1 endpoint uses the same function** to count the affine-form
unary budget. A rewrite that is not an identity produces a wrong unary count for those components, so
B-R1 must not be reported until this is fixed and every fired rewrite is identity-verified.

## Required actions

1. Re-specify PC2b's measurement as **component-level**, comparing only components where the rewrite
   actually fired, and reporting `0/60` as the realized eligible set — consistent with v2.1's frozen
   expectation of 0. The frozen expectation does not change; only the implementation's measurement does.
2. Fix `rewrite_b_r1_affine_infix` so every fired rewrite is a verified algebraic identity, and gate
   B-R1 on that verification. Components where a correct affine rewrite cannot be constructed must be
   recorded as such, not silently rewritten wrongly.
3. Keep v2.1 §14 item 11's reading: a non-zero PC2b would indicate a harness difference, not a
   scientific finding. This episode is exactly that case, and it was a harness difference.

## Note on process

Neither agent was careless. The auditor measured the right quantity on a smaller construction (28
components); the implementer measured a different quantity on a larger one and **declined to overwrite
its own contradicting algebra**, surfacing the conflict instead. Two independent measurements of a
frozen control disagreeing is precisely the signal the control battery exists to produce, and it fired
before the run rather than after. Standing rule R2's "verify the population has the assumed property"
would not have caught this one; the operative lesson is narrower and is added as R4.
