# C0001 v10 preregistration amendment decision

- decision owner: Research PI / Codex
- date: 2026-09-14
- status: **approved for drafting; not yet frozen**
- superseded binding plan: `preregistration_draft_v9.md`
- reason: pre-confirmatory protocol identifiability defect F3
- scientific result observed: **none**

## Integrity classification

No full confirmatory run, final evaluation, or sealed GPU_RUN5 artifact was
accessed. The defect was exposed by bounded implementation smoke and contract
review: documented four-decimal production quantization conflicts with the v9
E2 exact-equivalence rule. Under `.agent/rules/04-preregistration-and-metric-freeze.md`,
the amendment is a recorded pre-confirmatory deviation. v9 remains immutable
and its smoke outputs are not scientific evidence.

## Binding PI choices for the v10 draft

1. Retain all 330 truth-side strict-Hill components and all four scales. The
   primary denominator remains exactly 1,320; no pair is removed after E2.
2. E1 must remain analytically **and** numerically equivalent to the original,
   unquantized truth under the exact-rational oracle.
3. Introduce an audit-owned, deterministic `Q4(E1)` reference that independently
   reproduces only the documented production transform `parse_expr(evaluate=True)`
   followed by `Float.round(4)`. It must not call the production simplifier or
   reuse its returned tree.
4. E2 equivalence is evaluated against `Q4(E1)`, not against unquantized truth.
   It still requires analytic **and** numeric equivalence after decimal tokens
   are converted directly to exact rationals.
5. Preserve original-truth versus Q4 numeric error as a separate descriptive
   field. Never relabel coefficient quantization as structural false negative.
6. Freeze a truth-side quantization stratum before the full audit:
   `quantization_neutral` or `quantization_active`, with counts and deterministic
   membership artifacts. Strata are reporting dimensions, not exclusions.
7. A failed Q4 construction, nonfinite Q4 value, or oracle failure is terminal
   non-diagnostic evidence under the fixed denominator. It never reduces the
   denominator.
8. Primary outcomes remain mutually exclusive. `structural_false_negative`
   requires E1-original equivalence, E2-Q4 equivalence, and `hill_form=false`.
   `preserved` has the same prerequisites and `hill_form=true`.
9. Preserve the supported/unsupported/undecidable order, but prove in the v10
   closure review that both supported and unsupported outcomes are reachable by
   fixtures under the amended contract.
10. Update counted-call budgets, schemas, IDs, manifests, controls, and resume
    keys for every new Q4 primitive before freezing. Do not inherit 23,550 or
    25,860 without a complete recount.
11. Keep the original B4 truth-copy sanity check and add the minimum Q4-reference
    control needed to detect reference-construction or serialization failure.
12. F1, F2, and F4–F8 from `implementation_review_round5.md` remain separate
    implementation requirements after v10 freezes.

## Independent input and PI resolution

- Claude independently identified the v9 incompatibility and required a PI
  decision rather than an implementation-side endpoint change.
- Gemini independently proposed retaining all 1,320 pairs and truth-side
  quantization stratification. The PI adopts those elements.
- Gemini's proposal to count simplifier non-equivalence itself as an SFN and to
  adjust the effective denominator is rejected because it conflates mechanisms
  and permits post hoc denominator change.
- A second Claude methodology-comparison call was stopped after more than seven
  minutes without output. This is recorded as a worker retry/fallback, not a
  hard stop.

## Required sequence

1. Draft v10 and a v9-to-v10 change table.
2. Obtain independent methodological review, including reachable positive and
   negative fixtures and the full call recount.
3. Revise and freeze v10 at an exact path, audit ID, source commit, and SHA256.
4. Only then revise code/tests and create a new bounded `smoke_r6` from a clean
   code commit.
5. Repeat independent implementation and reproducibility review before any full
   confirmatory audit.
