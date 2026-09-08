# Human Review Queue

The autonomous loop does not wait on this queue unless a hard stop is triggered.

## High priority

### HRQ-0001 — Released ODEFormer checkpoint assigns exactly zero generation probability to 12 of 18 operators
- raised: 2026-09-09, C0001 Stage 1 (supervisor-verified)
- evidence: `GPU_RUNclaude1/analyses/C0001_stage1_preobservation.md` (addendum)
- The generator config persisted inside `assets/odeformer/weights/odeformer.pt` (`env.params`) is
  `operators_to_use = 'sin:1,inv:1,pow2:1,id:3,add:3,mul:1'`. Realized sampling probabilities are
  exactly **0.0** for `abs, sqrt, log, exp, arcsin, cos, arccos, tan, arctan, pow3, sub, div`,
  while those tokens *are* present in the 10,293-word decoder vocabulary.
- `reload_data = '/data/rcp/odeformer/experiments/datagen_final/datagen_use_sympy_True'` indicates this
  is the authors' own pretraining datagen configuration, not a local parser default. The same object
  reports `n_enc_layers/n_dec_layers = 4/12`, independently corroborating GPU_RUN4's architecture finding.
- Why it may matter beyond this campaign: it means "the model can express X" cannot be inferred from
  vocabulary membership for this checkpoint, and that `div`/`sub`/`exp`/`log` — all common in biochemical
  dynamics — were never sampled during data generation. This is a concrete, checkable property of a widely
  used public checkpoint and is adjacent to, but distinct from, the already-documented 4+12 vs 4+16
  architecture discrepancy.
- status: awaiting primary-source (paper / official repo / training logs) confirmation in C0001 Stage 2
  before any external claim. Loop is NOT blocked.

### HRQ-0002 — All 560 synthetic GRN ground truths are expressible, yet truth-in-beam is 0/960
- raised: 2026-09-09, C0001 Stage 1
- evidence: `GPU_RUNclaude1/analyses/C0001_stage1_preobservation.md`
- 320 train+validation systems verified `teacher_valid: True` by the supervisor; Stage 1 extended this to
  560/560 including sealed and family-holdout splits, with exact round-trip. GRN truths use only
  in-support operators. Yet GPU_RUN5 measured
  `true_exponent_aware_skeleton_in_beam_rate = 0.0` over 960 cells / 47,987 candidates.
- This is a clean dissociation: neither expressibility nor operator support explains the GRN generation
  failure. It leaves exactly two live explanations (prior mass vs search budget), which C0001 is designed
  to discriminate.
- status: informational; this is the motivation for C0001. Loop is NOT blocked.

## Normal priority

### HRQ-0003 — `pytest.ini` silently skips 124 tests including the test-firewall suite
- raised: 2026-09-09, C0001 Stage 0
- `testpaths = tests GPU_RUN1/tests GPU_RUN2/tests GPU_RUN3/tests GPU_RUN4/tests` collects 178 tests.
  `GPU_RUN5/tests` collects a further **124** on its own — including `test_gpu_run5_firewall.py`, which
  covers the sealed-test firewall. A bare `pytest` run therefore skips the newest and most
  leakage-sensitive coverage. One-line fix, proposed inside C0001.

### HRQ-0004 — `assets/nd2/weights/checkpoint.pth` has no recorded SHA256
- raised: 2026-09-09, C0001 Stage 0. ODEFormer and NeSymReS checkpoints both have pinned hashes; ND2 does not.

### HRQ-0005 — Stale documentation links and a stuck manifest
- raised: 2026-09-09, C0001 Stage 0
- `GPU_RUN5/README.md` and `GPU_RUN5_summary_report.md` §9.1 link six report filenames that do not exist.
- `results/runs/gpu_run4_phase0_01/manifest.json` status is stuck at `running`, commit `0641fa7`.
- Both are human-led-track artifacts. Per rule 00 the autonomous track must not rewrite GPU_RUN1-5
  history, so these are reported rather than edited.

## Reviewed
None.
