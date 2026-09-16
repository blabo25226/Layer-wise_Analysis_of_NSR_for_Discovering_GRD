# C0001 preregistration v10 independent closure review

- task: `C0001-T010-REVIEW`
- reviewed commit: `85eeac7e6b10335af624042989818b5672e3446f`
- reviewed draft SHA256: `da00004793fc2715b8f54d8a8ba6a7bf24138452d30a5bee54c16f5d69f95f21`
- reviewer: Claude Code, independent read-only critic
- PI: Codex
- verdict: **BLOCK_AND_REVISE_TO_V11**
- freeze/full audit: **PROHIBITED**

## Verified strengths

- The E2–Q4 amendment preserves the whole-chain scientific question while
  separating documented coefficient quantization from structural readout.
- The primary denominator remains 1,320 with no post-E2 exclusion.
- Quantization strata are truth-side, reporting-only, and sum to 1,320.
- Confirmatory arithmetic is correct:
  `1,530 + 16,320 + 4,080 + 4,080 + 1,020 + 6 + 600 = 27,636`.
- D2 is `330 * 8 = 2,640`; grand maximum is 30,276.
- The increase to 5 CPU-hours and 1.2 GB, with GPU/decode fixed at zero, is not
  a substantial compute-ceiling increase and does not require synchronous human
  approval. It is logged at normal priority.
- PI independently verified local/remote commit equality, unchanged v9 SHA256,
  v10 SHA256, and `git diff --check` exit 0.
- Gemini's parallel bulk audit could not access repository commands in headless
  mode and produced no review. Its exit code 0 is not treated as PASS.

## Blocking findings and required v11 repairs

### B1 — P0: production simplifier has silent identity fallbacks

`simplify_tree` can return the input tree on an internal swallowed timeout or
failed tree reconstruction. When Q4(E1) differs from E1, an unchanged E2 is not
the expected rounded output and makes a negative conclusion unreachable for
that pair.

Define and persist `e2_identity_fallback_candidate` as E2 raw prefix equal to E1
raw prefix while E1 is not equivalent to Q4(E1). Classify it as an execution
failure before semantic drift and retain it in the fixed denominator. Preserve
the rule that raw E2==E1 alone does not prove an internal timeout. State
explicitly that unsupported requires zero such non-diagnostic pairs; do not add
a global zero-rate gate that would discard otherwise valid positive evidence.

### B2 — P0: Q4 Float serialization is not frozen to the actual production path

Production serializes SymPy Floats through `str(sp.Float)` in
`Simplifier.sympy_to_prefix`, then reconstructs a tree. v10 instead says only
that audit infix is meaning-equivalent to `word_to_infix`, which is the wrong
stage and is insufficient under exact rational comparison.

Freeze default SymPy StrPrinter semantics for Float atoms, the Rational-to-prefix
rule, audit-side deterministic prefix/infix serialization, and exact parity
fixtures including `1/3 -> 0.3333`. Prefer direct audit SymPy-expression oracle
comparison while still saving the exact emitted reference tokens. Production
`simplify_tree` and its returned tree remain forbidden inputs to Q4.

### B3 — P0: supported and unsupported reachability are asserted, not proven

Pin a concrete algebraic strict-Hill false-negative fixture based on the existing
exploratory example: truth `2*x_0**2/(1+x_0**2)` and equivalent candidate
`4*x_0**2/(2+2*x_0**2)`, subject to an independently rechecked expected
`hill_form=false`. Pin a preserved fixture with expected `hill_form=true`.
Separately prove decision-function reachability with exactly 1,320 synthetic
terminal rows for the unsupported branch and one fully diagnostic SFN for the
supported branch. Add a pre-full `G_impl` gate requiring these fixtures and all
F1/F2/F4–F8 acceptance evidence to PASS.

### B4 — P1: terminal partition misses classifier parse and scaler fallback cases

Put `classifier_parse_valid=false` at execution-failure precedence. Extend
`rescale_incomplete` to every production early-return condition, including a
variable index outside `scale`, not only component-count mismatch. Parenthesize
all mixed AND/OR decision rules.

### B5 — P1: non-primary outcome vocabulary is deferred to implementation

Freeze `partition_scope` and a terminal control/ablation vocabulary. In
particular, all 510 B1 rows must be `control_pass` or `control_failure`; no row
may be `unknown`. Define analogous non-primary handling for B3, B4, N1, C_q4,
and descriptive D2 where applicable.

### B6 — P1: B1 oracle calls need a validity gate; fixture unit type is invalid

Retain B1e/B1f and add `G_b1`: 510/510 B1 rows must have completed Q4,
E1-original equivalence, E2-Q4 equivalence, valid classifier parse, and valid
metrics. This adds no counted calls. Add `fixture` as a fourth allowed unit type
and use it for C_q4 instead of overloading N1's `negative` type.

### B7 — P2: bounded non-independence and timeout asymmetry need claim limits

State that the audit-owned Q4 parser deliberately mirrors the documented
production parse/round semantics, so defects shared by both paths may be
invisible. Record that Q4's external-only timeout differs from production's
swallowed internal one and can itself create a non-diagnostic mismatch.

### B8 — P1: v10 is not self-contained

The draft repeatedly says “v9 section X is the same” for corpus, scale, N1,
guard, provenance, resume, and other binding fields. A frozen contract must be
reconstructable from its own bytes. v11 must inline every binding value and
algorithm. Historical change tables may reference v9; the binding plan may not.

### B9 — P1: quantization-stratum token algorithm is needlessly ambiguous

Replace “`format(rational, 'f')` equivalent” with a frozen raw-token grammar and
algorithm: remove sign, split the original finite decimal token at `.`, strip
trailing zeroes from the fractional substring, and count remaining digits;
integer tokens count zero. Explicitly specify handling or rejection of exponent
notation. Re-derive the 46/284 fixture from this algorithm.

## Gate decision

v10 remains an unfrozen historical draft. Produce v11, an exhaustive
v10-to-v11 change/response record, and a closure packet. Do not edit scientific
implementation or run a full audit until v11 receives independent PASS and is
frozen by exact commit and SHA256.
