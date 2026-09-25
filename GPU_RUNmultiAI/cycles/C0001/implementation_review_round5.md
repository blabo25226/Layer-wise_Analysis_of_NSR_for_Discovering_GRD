# C0001 implementation review round 5

- task: `C0001-T007-R5`
- audited branch: `ai/C0001/research-engineer/implement-metric-audit`
- audited tip: `086cbd5b465dea08973891776d004bb7a10e1053`
- frozen v9 SHA256: `60cfed79780c6b027192a3da14e69416d72090e0a89dddd22248b0f00f50cf00`
- independent critic: Claude Code (read-only)
- PI verification: Codex
- verdict: **BLOCK_CURRENT_IMPLEMENTATION_AND_AMEND_PROTOCOL**
- full confirmatory audit: **PROHIBITED**

## Provenance and bounded verification

- Local task tip and remote task branch both resolved to
  `086cbd5b465dea08973891776d004bb7a10e1053`.
- The v9 preregistration hash matched the freeze record.
- `git diff --check 67c46df..086cbd5` exited 0.
- PI reran the focused suite with Python 3.10:

```text
PYTHONPATH=src /home/blabo/miniconda3/envs/lansr310/bin/python \
  -m pytest -q tests/test_gpu_runmultiai_c0001_metric_audit.py
51 passed in 424.44s
```

- The committed R5 smoke is bounded engineering evidence only. It records 36
  confirmatory calls and no full audit.
- Both Codex independent-review subagents failed at launch because their shared
  usage limit was exhausted. This is a worker-capacity fallback, not a scientific
  or repository hard stop. Claude supplied the independent review.

## Blocking findings

### F1 — P0: E0 forward factors do not cancel under the frozen exact oracle

`forward_scale_system` serializes independently computed binary-float factors.
The smoke contains an E1 prefix beginning with
`mul,0.9,mul,0.1,mul,11.11111111111111`. As exact rationals their product is
not one. Numeric equivalence passes at `1e-8`, but analytic equivalence fails,
so every primary scale pair can be forced to `semantic_drift` for an
implementation artifact.

Required repair: construct E0 from the exact decimal tokens that production
rescaling will emit and use an explicit rational reciprocal expression, rather
than a rounded decimal quotient. E1 must be analytically and numerically
equivalent to original truth at all four scales.

### F2 — P0: compound `pow2`/`pow3`/`pow4` prefix operands are misparsed

`_normalize_prefix_tokens` assumes a unary power operand is one token. For
`pow2,div,mul,10.0,x_0,10.0`, it changes prefix arity and silently constructs a
different tree. Existing tests cover only leaf operands.

Required repair: parse the prefix tree before normalizing power nodes; support
`pow4` locally without token splicing. Add asymmetric nested and compound power
fixtures whose two oracle sides are not structurally identical.

### F3 — P0: frozen v9 cannot produce an informative negative conclusion

Production simplification rounds SymPy Float atoms to four decimal places.
Frozen v9 nevertheless requires E2 to be exact-rationally equivalent to the
unquantized original truth, and requires all 1,320 primary pairs to be fully
diagnostic before declaring H0001 unsupported. The R5 smoke demonstrates
`0.04598 -> 0.0460` drift. A static truth-token inventory found 46 of 330
strict-Hill components with at least one decimal token having more than four
fractional digits (184 scale pairs); 284 components (1,136 pairs) lack such a
raw token. This inventory does not prove all 184 will drift, but at least one
known protocol-induced drift makes the v9 negative decision unreachable.

This is a preregistration identifiability defect discovered before any full
confirmatory evaluation. It is not a null result and must not be repaired
silently inside implementation.

### F4 — P1: acceptance tests assert the broken outcome

`test_e0_e1_round_trip_primary_scales` asserts `semantic_drift` and false E1
analytic equivalence. Passing 51 tests therefore confirms internal consistency,
not endpoint validity. Invert the acceptance condition after F1 and add the F2
compound-power tests.

### F5 — P1: B1 bypasses production rescaling

The identity scaler returns its input tree directly. The frozen B1 counted
primitive is intended to exercise `Scaler.rescale_function` under identity
parameters. Construct a real production scaler with asserted identity
parameters, and require B1 E1 to be oracle-equivalent to truth.

### F6 — P1: B1 emits `unknown`

B1 disables oracles, falls through outcome classification, and writes
`outcome_category=unknown`. Define an explicit non-primary/control outcome or
partition scope. No completed row may silently remain unknown.

### F7 — P1: B2 inherits E2-only B0 flags

B2 is built by copying the B0 row, so an E2 drift can contaminate the E1-only
ablation. Rebuild B2 from immutable pair identity plus E1 fields and classify it
solely from E1.

### F8 — P1: B3 assumes a spaced system separator

B3 extracts a component only when the prediction contains `" | "`; the
canonical separator elsewhere is bare `"|"`. Always use the shared component
split/extraction path and add a multi-component fixture.

## Findings closed from round 4

R5 materially repaired the exact-decimal parser, registration/N1 power support
for leaf operands, durable call logging and stage-cache serialization, failure
terminalization, child guard side channel, artifact schema/durations/manifest
ordering, frozen environment validation, and resource monitoring. These fixes
remain valuable but do not open the full-audit gate while F1–F8 remain.

## Gate decision

Do not execute the 23,550-call audit. Record a pre-confirmatory deviation,
supersede v9 with an independently reviewed v10 contract, then implement and
review against the new frozen hash. The old `..._smoke/` directory remains
invalid and untracked; `smoke_r5` remains historical engineering evidence.
