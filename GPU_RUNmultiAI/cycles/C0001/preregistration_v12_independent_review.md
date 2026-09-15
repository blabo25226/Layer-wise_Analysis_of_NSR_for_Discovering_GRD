# C0001 preregistration v12 targeted independent closure review

- task: `C0001-T011-REVIEW`
- reviewed tip: `7ed72c5a0d10d68a3bb48edb936e7b84a6a98678`
- reviewed plan SHA256: `fc90aef070977e8b889fc9f0f89ae8bbcb92afb011133ab1cbb4e1f3fa78cee0`
- reviewers: Claude Code read-only critic; Codex independent subagent; Codex PI
- verdict: **BLOCK_AND_REVISE_TO_V13**
- freeze/full audit: **PROHIBITED**

## Independently verified

- Local task tip, tracking ref, and remote ref matched at the reviewed SHA.
- v12 hash matched its drafting record; historical v9, v10, and v11 plans were
  not edited.
- Confirmatory 27,636, D2 2,640, and grand 30,276 arithmetic in v12 is correct.
- Corpus regeneration reproduced 240 systems, 510 components, 330 strict-Hill
  components, 46 quantization-active and 284 neutral strict-Hill components,
  zero exponent-form numeric tokens, and 1,320 primary pairs.
- REACH-SUP-1 and REACH-UNS-1 now use 1,320 unique rows with all gates PASS.
  The post-freeze `reachability_evidence.json` remains an implementation gate,
  not a pre-freeze file.
- The two production rescale early-return predicates, object-identity check,
  G1/G_grand separation, wall/disk ceilings, and exact G_impl requirement list
  are acceptable.

## Blocking findings

### R12-1 — P0: Rational Q4 fixture is not connected to an acceptance gate

Q4-R4a correctly states that exact `(1/3)*x_0` stays Rational, while Q4-R4b
tests decimal rounding. However, counted C_q4 contains only the six Float and
construction fixtures and G_q4ref checks only those six. An incorrect Rational
implementation can therefore pass the audit. Add R4a as a seventh counted
fixture and update confirmatory/grand ceilings from 27,636/30,276 to
27,637/30,277 everywhere.

### R12-2 — P0: Q4 and oracle operator contracts are incomplete

The audit-owned SymPy-to-prefix algorithm delegates n-ary Add/Mul emission to an
undefined helper. Freeze the production fold exactly: iterate `expr.args` in
order, append the operator when `i == 0 or i < n_args - 1`, then append the
recursively serialized child. This emits the operator `n_args - 1` times.

The production `all_operators` table has no `pow4`, while F2 requires the
audit-local equivalence parser to support compound `pow4`. Keep the production
Q4 arity table byte-faithful, and freeze a separately named audit-oracle
extension in which `pow4` is unary. Do not silently add `pow4` to the production
table or drop the F2 regression requirement. Define abort behavior for any Q4
emitted operator that cannot be reparsed.

### R12-3 — P1: self-containment regressed for oracle, guard, artifacts, resume, and provenance

v13 must restore executable binding details rather than collection names:

- numeric oracle pointwise tolerance, all-points-finite requirement, and
  nonfinite/timeout `completed=false` behavior;
- mandatory guard installation before audit task code in the parent and every
  child, including simplifier subprocesses, with deny-on-attempt block/log and
  child side-channel aggregation;
- complete `pair_results.csv` columns, exact fingerprint bytes/file, stage
  cache, pair cache where used, call log, guard side channel, abort manifest,
  and deviation-log lifecycle;
- append-and-flush durability and trailing-partial-line recovery for stage cache
  and call log;
- resume identity including git commit, plan/script/config/source hashes,
  corpus/fingerprint payload and exact bytes/hash/path, all seeds, ordered
  primitives, all timeouts, normalized semantic CLI, dependency versions, OS,
  CPU, and frozen environment variables;
- source hashes for every runtime module under `src/gpu_runmultiai/` plus
  `src/gpu_run4/ted.py`, ODEFormer `sklearn_wrapper.py`, `environment.py`,
  `generators.py`, and every other imported runtime source.

### R12-4 — P1: truth-side eligibility is not uniquely specified

The prose references family-level counts but does not bind zero-based component
indices. Inline the exact sets used by the runtime:

- strict: R01 `{0}`, R02 `{0}`, R03 `{0,1}`, R04 `{1}`, R05 `{0,1}`,
  R06 `{0,1,2}`, R07 `{1}`, R08 `{}`;
- non-strict: R07 `{2}`, R08 `{2}`;
- linear: R04 `{0}`, R07 `{0}`, R08 `{0,1}`.

Abort registration if any generated component belongs to zero or multiple
eligibility sets.

### R12-5 — P1: row predicates and typed IDs remain underspecified

Freeze direct row-level pass/failure predicates for B3, B4, N1, C_q4, and D2,
not only their terminal vocabulary. Freeze canonical `scale` tokens used in
pair IDs as exactly `0.1`, `0.5`, `1.0`, `2.0`, and `5.0`, with identity/control
cases specified separately. G1 must count only confirmatory ledger rows even
though D2 shares `call_log.jsonl`.

## PI conflict resolution

Claude considered Rational R4a adequately closed by the normative fixture text;
the Codex reviewer showed it was not connected to any executable gate. The PI
adopts the stricter gated-fixture interpretation because a preregistered
invariant must be capable of failing before the full audit is accepted.

Claude treated `pow4` as removable because it is absent from production
`all_operators`; the implementation review established that F2 is an
audit-oracle parser regression and the current audit parser explicitly supports
`pow4`. The PI therefore separates production-Q4 and audit-oracle operator
tables and retains F2.

## Gate decision

Produce a self-contained v13, update the two call ceilings for the seventh Q4
fixture, and re-review only R12-1 through R12-5. No scientific implementation,
smoke, freeze, or full audit is authorized before a PASS closure review.
