# C0001 v16 implementation independent review — round 1

- reviewed task tip: `9c19b3b53ebd18239d83bce0d8a56f887bf966de`
- frozen plan: `preregistration_draft_v16.md`
- frozen plan SHA256: `67017f5c8bac861664fc867b70cf229d43be3d052d266ffd0d575e20e6c12078`
- Claude role: hostile independent implementation and scientific-method reviewer
- Codex subagent: attempted; unavailable because the account usage limit was reached
- PI decision: **BLOCK**
- full audit authorization: **DENIED**

The fresh smoke is post-fix: `audit_manifest.json` binds runtime commit
`e483c788885e32f8248a52a23c79b9b7508f7c7f`.  It is nevertheless negative
implementation evidence, not an acceptance artifact.

## P0 blockers

1. **F5 / B1 identity construction is wrong.**
   `pipeline.py` builds B1 E0 with `build_production_scaler(1.0, d)`, whose
   frozen production `a_t` is 0.9, and only asks the inverse step to use
   identity parameters.  Both tracked smoke B1 rows therefore have
   `e1_oracle_equivalent=false`, `control_pass_row=false`, and
   `outcome_category=control_failure`.  `G_b1` also checks only terminal
   vocabulary rather than 510 `control_pass_row=true` rows.

2. **Five mandatory validity gates do not exist.**
   `G_eligibility`, `G_stratum`, `G_grand`, `G_contract`, and `G_impl` are
   absent from the runtime and smoke manifest, so `any_gate_failed` cannot
   enforce the preregistered closure and global-abort rules.

3. **P12 / quantization stratum is unimplemented.**
   The call table reserves 510 calls, but there is no
   `fractional_digit_count`, no populated `quantization_stratum` field, and
   no `quantization_stratum.json`.  The exponent-token drift abort cannot
   fire.

4. **The second production-rescale early-return condition is not detected.**
   `rescale_system` never checks `rescaled_tree is input_tree`, permitting a
   no-op inverse to be classified as a normal pair.

5. **Parent guard bootstrap ordering violates the frozen contract.**
   The entry point imports `gpu_runmultiai` modules and reads/verifies the
   plan before installing the bootstrap guard.  `run_audit` later creates a
   different guard after other reads.  Required import-order,
   no-replacement, child-merge, and G4-ledger-source tests are absent.

6. **G_impl reachability evidence is incomplete.**
   Four rows are emitted instead of the required ten.  `REACH-SFN-1` and six
   other required fixtures are missing, and the supported/unsupported rows
   bypass real gate evaluation.

7. **Resource limits use prohibited values and units.**
   `resources.py` uses 14,400 seconds and binary 1 GiB instead of 18,000
   monotonic seconds and 1,200,000,000 decimal bytes.  The frozen constants
   are not used by the monitor.

## Required contract repairs

- Route every global abort through a complete `abort_manifest.json`, set
  manifest status to `aborted`, and write the frozen deviation schema and
  final status line.  Use only `initializing`, `running`, `completed`, or
  `aborted`.
- Produce the missing `negative_controls.json` and
  `quantization_stratum.json`; make `equivalence_oracle.json`, B3, B4, N1,
  `condition_summary.json`, and the manifest match the frozen schemas.
- Persist the frozen ceiling values and `byte_convention=decimal_gb`.
- Make resume identity checkout-independent and perform the required
  byte-identical fingerprint payload/bytes rereads.
- Compute `original_vs_q4_numeric_max_abs_error`; abort on an unclassified
  stratum rather than silently mapping it to `linear_control`.
- Restore the exact frozen dialect by removing non-frozen `idiv`, `mod`, and
  `neg`; compare the Q4-emitted infix in the oracle; do not fabricate E2
  prefix identity when the child emits none.
- Load pair-cache JSONL through the durable loader and run identity fallback
  comparison with the frozen local dictionary under a timeout.
- Exercise B2 and D2 in a fresh bounded validation run; the prior smoke
  explicitly skipped both and cannot establish those paths.

## Checks that passed

- Frozen plan hash, audit ID, environment arguments, and exact call ceilings
  27,637 / 30,277 are bound.
- Canonical IDs, digest selection, decision-grid rank ordering, Q4 seven
  reference fixtures, F1/F2/F4 B0 behavior, F7, F8, corpus fingerprint, and
  core durable JSONL helper are materially implemented.
- The fresh smoke is not a full audit and no
  `implementation_closure_record.json` exists.
- At review time, local, tracking, and remote tips all equal `9c19b3b` and
  the only untracked path is the protected historical v9 smoke directory.

## Acceptance rule

All P0 and required contract repairs must be implemented, covered by focused
tests in Python 3.10, demonstrated in new non-confirmatory validation
artifacts, independently reviewed, committed, pushed, and remotely verified.
Only then may the PI create the implementation closure record or authorize
the full 27,637-call audit.
