# C0001 implementation review — round 1

Date: 2026-09-13
Reviewed task branch: `ai/C0001/research-engineer/implement-metric-audit`
Reviewed commit: `88720c1d905fd65848222e0c67a5812ac21f1385`
Frozen preregistration: `preregistration_draft_v9.md`
Frozen SHA256: `60cfed79780c6b027192a3da14e69416d72090e0a89dddd22248b0f00f50cf00`

## PI decision

`BLOCK_CURRENT_IMPLEMENTATION_AND_REVISE`

This is a recoverable implementation failure, not a scientific result and not a
hard stop under rule 13.  Do not run or interpret the confirmatory audit from
commit `88720c1`.  The branch must be revised and independently reviewed again
before integration.

Three independent review paths were used:

1. Claude critic/reviewer: completed with `BLOCK`.
2. Codex contract-review subagent: completed with `BLOCK`.
3. Codex reproducibility-review subagent: returned reproducible critical
   findings, then exhausted its service usage before its final formatted report.

## Blocking findings

### R1. The frozen E0 -> E1 -> E2 chain is not executed

- `src/gpu_runmultiai/pipeline.py` constructs E0 from the rewritten truth system
  without the frozen analytic forward transformation
  `g_i(z) = (s_i/a_t) f_i(z/s)`.
- The production inverse-rescaling result E1 is not the input to the simplifier.
  The pipeline passes E0 prefixes to the subprocess, so E2 is not
  `simplify_tree(E1)` and can be scale-independent.
- Scaler assertions are discarded and G0 is later populated from expected
  literals, rather than measured values.

### R2. Full-system/component indexing is inconsistent

- Several paths classify or compare a one-component expression while retaining
  the original full-system `component_idx`.
- Components with `component_idx > 0` can raise `IndexError` or become oracle
  parse failures.
- Truth/component and candidate/full-system metric comparisons are asymmetric.

### R3. The independent oracle is not usable as frozen

- Substitutions use string keys rather than the parsed SymPy symbols, so even a
  self-equivalence check can finish with `completed=false`.
- `pow2`/higher-tier formula syntax is not normalized for the parser.
- Numeric leaves pass through a float and `.4g` path rather than a dedicated
  raw-token-to-`sympy.Rational` parser.  Raw tokens and parsed rational values are
  not persisted.
- Analytic partial results are overwritten on numeric mismatch instead of being
  retained in the required tri-state record.

### R4. The declared 23,550-call confirmatory design is not connected

- B0 runs only the 330 strict-Hill components at four scales (1,320 pairs), not
  all 510 components at four scales (2,040 pairs).
- B1, B2, B3 and D2 have no live runner path.
- Linear and non-strict controls are omitted; the linear-control gates therefore
  necessarily fail or operate on empty rows.
- The static call table sums correctly, but it does not verify runner behavior.

### R5. Failure classification and mandatory artifacts are incomplete

- Classifier parse failure can be treated as non-Hill and become a false
  `structural_false_negative`; it must be `execution_failure`.
- Timeout and other problem-level failures are not consistently converted to a
  terminal row according to the frozen precedence.
- External simplifier timeout is effectively seven seconds rather than the
  frozen five seconds.
- `equivalence_oracle.json`, `deviation_log.md`, fixed pair-result columns, raw
  E0/E1/E2 prefixes, classifier failure reason and required validity fields are
  absent.

### R6. Resume and counted-call ceilings are not enforced

- Resume creates an empty logger instead of loading and appending to the existing
  call log; deduplication and ceiling accounting are therefore lost.
- Tuple/list JSON round-tripping can cause an identity mismatch even for an
  otherwise matching run.
- The actual ceiling assertion is not connected to the live audit.
- Required corpus fingerprint paths/hashes are absent from resume identity.

### R7. The sealed-access guard breaks the host process and is incomplete

- Patched `os.stat`/`os.scandir` wrappers do not preserve valid signatures such
  as `dir_fd` and integer file descriptors.  Pytest cleanup raises `TypeError`.
- The guard is not reliably restored in `finally`.
- Child-process attempts are not aggregated into parent G4 evidence.
- Normalized and real-path checks are not independent enough, and write modes
  are not fully intercepted.

### R8. Current smoke and test claims are not acceptance evidence

- The focused pytest command exits nonzero after 14 test bodies because teardown
  crashes in the sealed guard.  Therefore “14 passed” is not a valid claim.
- Tests do not exercise oracle positive/negative cases, full scale round-trips,
  E1-to-E2 provenance, actual call totals, full controls or true resume.
- The untracked smoke manifest records base commit `9e692c2`, Python 3.14.6,
  missing torch and no valid ODEFormer path.  Oracle calls failed and primary
  coverage is zero.  It is retained only as failure evidence.
- The frozen environment requires Python 3.10.x; this has not been verified on
  the current host.

## Required acceptance checks for round 2

1. Execute the exact full-system analytic forward transformation and production
   inverse rescaling; prove E1 equivalence to truth for every primary scale in
   representative tests.
2. Produce E2 only from serialized E1 and prove the dependency with a regression
   test.
3. Use a dedicated exact-rational oracle parser and test self/positive/negative
   equivalence across representative families, tiers and nonzero components.
4. Connect B0/B1/B2/B3/B4/N1 and optional D2 exactly as frozen; assert observed
   condition counts and live counted-call totals against the operation table.
5. Evaluate all gates from observed data, preserve the five terminal categories,
   and make every attempted pair terminal.
6. Implement true append/resume with normalized identity, 5-tuple deduplication
   and active ceilings.
7. Emit every mandatory artifact with fixed schemas and provenance.
8. Make the sealed guard signature-safe, parent/child auditable and always
   restored.  Verify that the test process exits zero.
9. Fail fast on frozen CLI/environment mismatches.  Do not silently change the
   frozen protocol; record any unavoidable deviation for PI decision.
10. Run a new bounded smoke only from a clean committed implementation.  Its
    manifest must contain that exact commit.  A dependency-unavailable smoke is
    diagnostic only, not whole-chain acceptance.

## Evidence policy

No PR #4 or `GPU_RUNclaude1` scientific results and no historical sealed GPU_RUN5
results were used.  The untracked smoke output was inspected only as execution
provenance and failure evidence.  No confirmatory result was produced.
