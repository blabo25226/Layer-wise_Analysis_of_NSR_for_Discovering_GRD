# GPU_RUNclaude1 Persistent Research State

## Campaign
- branch: `20260909_researce_GPU_RUNclaude1`
- head commit at C0001 Stage 0: `94a571b` ("prepare for claude"), working tree clean
- status: `C0001 in progress`
- current_cycle: `C0001`
- last_completed_cycle: none
- last_synthesis: none
- state last reconstructed: 2026-09-09 (Stage 0 of C0001), from repository files (not chat memory)

## Human intent

Run an AI-led research line independently of the human-led LANSR line.

Claude autonomously repeats:
hypothesis → literature → preregistration → implementation → experiment → analysis
→ independent review → replication when needed → cycle report → reflection → next hypothesis.

Humans mainly inspect reports periodically. Routine scientific failure is not a stop condition.

---

## 1. Verified model identity (constrains every ODEFormer cycle)

`assets/odeformer/weights/odeformer.pt`, 464,822,385 B, mtime 2023-09-28
- SHA256 `56754040be5aa92ed4767fc43ee2008faa293f87c12b643e66c7df3e1623a5e8`
  (pinned in `configs/gpu_run4/base.yaml:11` and `configs/gpu_run5/base.yaml:8`; verified in
  `results/runs/gpu_run5_20260823_ddd267b0/phase0/checkpoint_audit.json`)
- TRUE architecture read from the state dict: **4 encoder layers (dim 256) + 12 decoder layers (dim 512)**,
  16 heads, **60,646,773 parameters**, 16 ranked layers `encoder_0..3`, `decoder_0..11`.
  Per-block: encoder 789,760 params each; decoder 3,941,888 each.
- NOT the paper's 4+16 / dim 512 / ~86M configuration. The 86M weights are not present locally and
  have never been located. `configs/gpu_run4/base.yaml` therefore pins
  `architecture_target: released_checkpoint_4enc_12dec_61M`.
- `tied_output_embedding: true`, `decoder_n_words: 10293`, `encoder_positional_embeddings: false`
- decode defaults: `beam_size: 50`, `beam_type: sampling`, `beam_temperature: 0.1`,
  `max_generated_output_len: 200`
- **generation constraints (central to the current bottleneck):**
  `operators_to_use: "sin:1,inv:1,pow2:1,id:3,add:3,mul:1"`, `max_dimension: 6`, `max_int: 10`.
  There is **no general learnable-exponent `pow`**: Hill exponent 4 must be written `pow2(pow2(x))`.

Other checkpoints: `assets/nesymres/weights/100M.ckpt` 317,003,151 B SHA256
`62aedc41fdb67ecbe3679f5ef030e7ef2bf0f4471c461b68d8814358968b324f`;
`assets/nd2/weights/checkpoint.pth` 81,136,260 B — **no SHA256 recorded anywhere in the repo** (open defect).

---

## 2. Prior constraints (treat as observed unless superseded by a verified result)

### GPU_RUN4 (`results/runs/gpu_run4_phase0_01`, 1 seed, ODEBench 63 systems x 4 corruptions = 252 cells)
- valid 232/252 = 0.921; reconstruction R2 median 0.980; generalization R2 median 0.696
- **canonical exact 0/252; CAS-symbolic-equivalent 0/252**; skeleton exact 19/252 = 0.075, confined to
  6 easy systems (RC circuit, population growth, autocatalysis, language death, laser photons, SIR-2D)
- TED median 16; complexity median 17; variable F1 median 1.0 (metric has no discriminative power here)
- dimension scaling: 1D recon 0.997, skeleton 17/92; 2D 0.946, 2/112;
  **3D valid only 25/40, R2>0.9 8/40, skeleton 0/40**; 4D 0.906, 0/8
- generation vs selection: truth skeleton in beam 23/252 = 9.1%; selection then picked it in 18, missed 5.
  **57 of 63 systems never in beam.** unique skeletons per beam mean 9.19;
  mean selected TED 17.26 vs mean oracle-best-in-beam TED 14.31
- layer estimands (encoder-only probes, n_val = 16): probe top3 `encoder_0/1/2`;
  CKA all pairs 0.921-0.978 (no separation); gradient top `encoder_0/3/2`;
  residual-zero causal ablation top `encoder_3` (dCE 10.40), `decoder_3` (2.47), `decoder_0` (1.89);
  IOLE top `decoder_7`, `encoder_0`, `encoder_2` (deltas only ~1e-3)
- selective FT on analysis-test (4 steps, teacher-forcing CE only):
  frozen **1.674 BEST** < causal_top3 1.679 < top1 1.682 < random3_1 1.683 < random3_0 1.690
  < bottom3 1.692 < random3_2 1.693 < top3 1.696 < full **1.797 WORST**.
  Every FT condition was worse than frozen; validation-to-test rank inverted.
- **criterion disagreement is large, not noise**: probe #1 `encoder_0` ranks 11th on causal dCE;
  causal #1 `encoder_3` is bottom of the probe ranking. No criterion pair shares a top-3 ordering.
- known provenance defect: root `manifest.json` status stuck at `running`, commit `0641fa7`.

### GPU_RUN5 (`results/runs/gpu_run5_20260823_ddd267b0`, 3 bundles, phases 0-9 complete)
- ODEBench decoded support (re-analysis of GPU_RUN4's same single-seed 252 cells, no new inference):
  variable-denominator candidates 1,860/12,600 = 14.76% [0.1415, 0.1539];
  **true exponent-aware skeleton in beam 4/252 = 1.59% [0.0062, 0.0401]**;
  **variable-denominator truth subset (56 cells): truth-in-beam 0/56, selected exact 0/56**
- **GRN frozen validation (960 cells, 47,987 candidates): `true_exponent_aware_skeleton_in_beam_rate = 0.0`
  — not once.** unique exponent-skeletons per beam mean 9.28.
  => Selection cannot be the binding constraint for Hill-type GRN. **The bottleneck is generation.**
- multi-IC selection (P6 HIT): mean clustered difference in failure-aware generalization NRMSE
  **-0.20278**, paired Student-t 95% CI **[-0.32323, -0.08233]**, 80 system clusters.
  Improves extrapolation error among existing candidates; cannot create absent structures.
- GRN final test (opened once, 2026-09-01): frozen exact-macro 0.02396 / faTED 0.47917 / genNRMSE 1.40764;
  official_continued_full 0.05972/0.46147/1.44240; **grn_full 0.15972/0.36865/2.19822 (recon R2 collapsed
  to 0.222)**; grn_top3 0.10938/0.46111/2.29097; grn_random3_0 0.10764/0.44223/1.26859
- **exact component count for nontrivial Hill / variable-denominator components of R03-R08 = 0 in EVERY
  final condition.** The 0.15972 exact-macro must not be read as "16% of nontrivial GRNs recovered".
- forgetting (ODEBench exponent-aware exact rate, secondary): frozen 0.08466, grn_top3 0.06085 (-0.0238),
  grn_full 0.00794 (-0.0767) => selective FT forgets less, full FT forgets much more
- **P7 MISS** (full beat top3 on the first lexicographic key). **Go 8 NO-GO**: 3/6 conditions false,
  including generalization-NRMSE ratio top3/frozen = 1.6275 vs cap 1.10.
  DREAM4 and real data were deliberately NOT run — a preregistered stop, not a compute failure.
- layer estimands (main view, 16 layers): decoder next-token probe top3 `decoder_11` 0.6420,
  `decoder_10` 0.6215, `decoder_9` 0.5975; gradient/sqrt(param) top `encoder_0/3/1`;
  formula-IOLE top3 `decoder_11`, `decoder_10`, `decoder_8`;
  causal mean-ablation (alpha = 0.5) top3 `decoder_11`, `decoder_3`, `encoder_3`
- **P5 HIT — the campaign's strongest layer result:** Spearman between the post-intervention dCE ranking
  and the failure-aware dTED ranking = **0.008956, two-sided p = 0.97374**, n_layers = 16.
  Teacher-forcing CE is not a usable proxy for symbolic damage ordering on this panel.
  `decoder_11` caused faTED +0.52692, component_valid_loss 1.0, gen R2 loss 10.466, but
  **damage_CE = -1.61708 — CE IMPROVED while formulas were destroyed.**
- internal inconsistency to keep in view: IOLE rank-1 `decoder_11` has normalized contribution
  C_l = **-0.0378 (negative)** in the main view, while `decoder_10` = 0.3298 and `decoder_0` = -0.4157.
  The lexicographic IOLE score and C_l do not agree.
- rank stability across 3 bundles: main Spearman 0.480 / Kendall 0.389; family-holdout 0.781 / 0.622
- **DecoderLens fully saturated: median normalized variable-aware TED = 1.0 at all 12 decoder layers**
  (288 formula rows, 20,352 token rows, 0 failures) — zero depth signal recovered
- within-module mean off-diagonal CKA: encoder 0.94377 (4 layers) vs decoder 0.57762 (12 layers)
- causal `component_exact_loss = 0.0` for all 16 layers (floor effect — exact was already 0)
- volumes: 128,007 physical failure events; 292,618 final-GRN candidates; 182,772 ODEBench-forgetting
  candidates; all 64,620 shards stream-verified by path, byte count and SHA256 in phase9
- family-holdout is a **subset** of the main 80-system test (R07/R08), explicitly **not** independent evidence

### Cross-run layer-ranking disagreement (Result E)
| run | model | probe top3 | causal top3 | IOLE top3 |
|---|---|---|---|---|
| GPU_RUN2 | NeSymReS | decoder_0, decoder_3, encoder_4 | (none; stored ablation is an inverted robustness order — known defect) | decoder_4, decoder_1, decoder_0 |
| GPU_RUN3 | NDformer | dec.1, dec.0, enc.1 | enc.0, enc.1, dec.0 | dec.1, dec.0, enc.1 |
| GPU_RUN4 | ODEFormer | encoder_0, encoder_1, encoder_2 | encoder_3, decoder_3, decoder_0 | decoder_7, encoder_0, encoder_2 |
| GPU_RUN5 | ODEFormer | decoder_11, decoder_10, decoder_9 | decoder_11, decoder_3, encoder_3 | decoder_11, decoder_10, decoder_8 |

The RUN4 -> RUN5 flip on the **same checkpoint** is an estimand change, not a contradiction:
RUN4 probed only the encoder with a dimension-classification target at n_val = 16; RUN5 used a decoder
next-token target on 500 validation formulas. Rule 04 forbids averaging these into one ranking.

---

## 3. Open high-level research problems (re-prioritized after Stage 0)

1. **Generation support / reachability** — why is the true Hill skeleton never in the beam? (now top priority)
2. Expressibility vs prior mass vs search budget as competing explanations of (1).
3. Candidate selection identifiability (largely *not* the binding constraint for GRN; still open for ODEBench).
4. Structural OOD generalization.
5. **Layer-importance criterion divergence** — the P5 orthogonality result and the CE-improves-while-formulas-break
   phenomenon need mechanism, not just correlation.
6. Adaptation-forgetting tradeoff (selective FT forgets less but did not win on formula score).
7. Fair baseline evaluation at matched budget.
8. Real-data readiness gates (blocked behind Go 8; do not escalate without new information).
9. Connection to derivative-free biological dynamics methods.
10. ND2 checkpoint has no recorded SHA256 (provenance defect, cheap to fix).

---

## 4. Sealed resources and test-access ledger

| artifact | content | status |
|---|---|---|
| `results/runs/gpu_run5_20260823_ddd267b0/phase2/sealed_test.json` | main GRN test, 80 systems, SHA256 `881f784b14cafa2d8617679c573be8ed68f63dbab6d7fa9182e4f5b510464ce0` | **SPENT** — opened once 2026-09-01 (`open_count: 1`) |
| `.../phase2/sealed_family_holdout_test.json` | 20 systems R07/R08, SHA256 `fa8fe375fd273e807e22d7d0def7c1d0c866ad006081d207359cb97d1bcbaf91` | **SPENT**, and a *subset* of the 80 — never count as independent evidence |
| `.../phase4/sealed_official_test.json` | 500 official ODEFormer-generator formulas, artifact SHA256 `2860d829d9077d01258489fb68ed8dcd8a333d6a0e150b8e36b301f28bb1e070` | **GENERATED, NEVER EVALUATED** — see the correction below. Not "untouched". |

**CORRECTION (C0001 Stage 5, 2026-09-09)** — my earlier characterization of the phase-4 seal as
"UNSPENT — never evaluated — the only clean seal available" was imprecise and is withdrawn.
Verified: `scripts/phases/gpu_run5_phase4.py:119` and `:152` compute `sha256_file()` over
`sealed_official_test.json` alongside its non-sealed siblings — once for a cache-validity check and
once to populate `official_corpus_meta.json:artifact_sha256`. So the digest `2860d829...` that I cited
as evidence of the seal's cleanliness **was computed by the seal's own producing phase, outside any
test-open ledger**. There is no ledger entry for it.

The precise, defensible status is:
- its **outcomes were never analyzed** (`test_generated_not_evaluated: true`, and Phase 4's Go asserts
  `official_test_outcomes_not_analyzed: true` / `official_test_used_only_for_split_leakage_audit: true`);
- its **bytes were read** by its producing phase to hash them, which GPU_RUN5's own Phase 8 treats as
  the test-open event for the *other* seals;
- whether that constitutes consumption is an **open campaign-level question**, not something I should
  assert either way.
Nothing in C0001 reads it regardless.

**Seal inventory correction**: there are **7** sealed files under `results/`, not 3. The extra four
belong to two abandoned/partial GPU_RUN5 runs (`gpu_run5_20260823_8cd0b6fa`,
`gpu_run5_20260823_fec3a894`), each carrying its own `phase2/sealed_test.json` and
`phase2/sealed_family_holdout_test.json`. Only `ddd267b0` is authoritative. Any allowlist or guard must
enumerate all 7 from the filesystem and never rely on a hardcoded three-path list:

```
results/runs/gpu_run5_20260823_8cd0b6fa/phase2/sealed_family_holdout_test.json
results/runs/gpu_run5_20260823_8cd0b6fa/phase2/sealed_test.json
results/runs/gpu_run5_20260823_ddd267b0/phase2/sealed_family_holdout_test.json
results/runs/gpu_run5_20260823_ddd267b0/phase2/sealed_test.json
results/runs/gpu_run5_20260823_ddd267b0/phase4/sealed_official_test.json
results/runs/gpu_run5_20260823_fec3a894/phase2/sealed_family_holdout_test.json
results/runs/gpu_run5_20260823_fec3a894/phase2/sealed_test.json
```
| `results/runs/gpu_run4_phase0_01/phase4/corpus.json` test split | 16 formulas | spent (evaluated once in RUN4 phase 9) |
| ODEBench 63 systems | `third_party/odeformer/odeformer/odebench/` | not sealed, but **forbidden** as adaptation / layer-selection / hyperparameter data. Post-adaptation ODEBench evaluation is a *forgetting* secondary outcome only. |

**Consequence for this campaign**: any cycle needing a clean confirmation set must **generate a new sealed
set under a new run ID**. Re-using GPU_RUN5's GRN seals for selection or a second evaluation would violate
rules 01 and 02.

Test firewall machinery already exists and must be used: `src/gpu_run5/config.py load_sealed_test` raises
`PermissionError` when `phase < 8`; `src/gpu_run5/phase8.py` takes an `fcntl` single-open claim and writes
`phase8/test_open_ledger.json`.

---

## 5. Compute state (measured 2026-09-09, C0001 Stage 0)

- python env: conda `lansr310`, Python 3.10.20.
  Activate with `source /home/blabo/miniconda3/etc/profile.d/conda.sh && conda activate lansr310`
- torch 2.5.1+cu124, CUDA available. Driver 580.173.02, CUDA runtime 13.0
- **GPU 0: NVIDIA GeForce RTX 2070, 7782 MiB total, cc 7.5, 54 C idle, 888 MiB already held by the
  desktop session (gnome-shell / Xwayland / gnome-remote-desktop) => ~6.5 GiB usable, and it is SHARED
  with the user's live desktop.**
- GPU 1: NVIDIA GeForce GTX 1060 3GB, 3006 MiB, cc 6.1, 30 C, idle. Too small to train 61M params;
  usable for forward-only work.
- RAM 60 GiB total, ~52 GiB available; swap 7 GiB
- Disk `/dev/nvme0n1p2` 233 G, **117 G available** (48% used). `results/` already 25 G.
- libs: sympy 1.13.1, numpy 2.2.6, scipy 1.15.3, hydra-core 1.0.0, omegaconf 2.1.2, pysr 1.5.10,
  scikit-learn 1.7.2, pandas 2.3.3, matplotlib 3.10.9, zss 1.2.0, pytorch-lightning 1.9.5
- `odeformer` is **not** pip-installed; `third_party/odeformer` is injected by
  `src/gpu_run4_runtime.py:93 install_odeformer_path`, guarded by `:107
  assert_odeformer_not_from_github_source()`. `nesymres` IS pip-installed editable from `third_party/nesymres`.

### Standing design constraint
GPU_RUN4/5 ran on a 24 GB Colab L4. This campaign has ~6.5 GiB usable VRAM on a desktop-shared GPU.
Every cycle must fit that envelope or run on CPU. This is a design constraint, **not** a hard stop.

### Per-cycle compute ceiling (C0001 onward, revisable per preregistration)
- <= 4 GPU-hours on GPU 0 per cycle, peak VRAM <= 5.5 GiB
- <= 24 CPU-core-hours per cycle
- <= 15 GiB new disk under `results/runs/<new-run-id>/`
- crash-loop rule: 3 consecutive identical fatal failures with no new diagnostic information => stop and
  reassess rather than re-run (rule 06)

---

## 6. Reusable artifacts (verified present; enable near-zero-GPU cycles)

Under `results/runs/gpu_run5_20260823_ddd267b0/` (15 G total):
- `phase1/candidates_annotated.json` (44 M) — 12,600 ODEBench candidates with frozen structural form flags;
  `phase1/decoded_support.json`
- `phase3/all_candidates.json` (174 M) — 47,987 GRN candidates; `phase3/cells/` (230 M);
  `beam_groups.json`, `failure_funnel*.json`, `lambda_selection.json`, `p6_validation.json`
- `phase4/train_features.npz` (229 M) + `validation_features.npz` (58 M) — cached 16-layer features for
  2,000 + 500 official formulas => **any new probe/CKA question is CPU-only**;
  `probes.json`, `cka.json`, `gradient_norms.json`, `decoder_logit_lens.json`, `teacher_forcing_ce.json`,
  `fixed_grn_validation_panel.json` (the 24-system intervention panel), `fixed_official_validation_panel.json`
- `phase5/corpus_means.npz` — 16-layer corpus means for mean-ablation, **alpha = 0.5 already calibrated**;
  `layer_effects.json`, `causal_ranking.json`, `holdout_*`, `hook_controls.json`, `cell_cache/` (220 M)
- `phase6/` + `phase7/` + `phase8/checkpoints/` (6.9 G) — adapted checkpoints: `grn_full`,
  `grn_decoder_all`, `official_continued_full`, per-single-layer IOLE deltas for all 16 layers,
  `grn_top1/top3/random3_0..4`, x 3 bundles x 2 views. Reusable for new *evaluations* without retraining.
- `phase2/train.json` (240 systems) + `validation.json` (80) + `family_holdout_train.json` (150, R01-R05)
  + `family_holdout_validation.json` (10, R06) — the R01-R08 generator corpus, RK45 rtol 1e-8, atol 1e-10,
  zero system / parameter-variant / trajectory overlap (`audit.json`), fingerprint `e5edac34...ba8af`,
  rejection rate 0.0148
- `phase9/preregistration_outcome.json` — the machine verdict of record; `result_{a..e}.json`,
  `integrated_results.json`, `failure_analysis.json`, `condition_uncertainty.json`,
  `source_artifact_audit.json`

Under `results/runs/gpu_run4_phase0_01/` (44 M):
- `phase1/` — the frozen symbolic evaluator (`eval.json`, `gold_cases.json`, `odebench_parsed.json`,
  `identity_records.json`); `phase2/all_candidates.json` (20 M) + 252 per-cell JSONs;
  `phase3/beam_groups.json`; `phase4/corpus.json` (the 48/16/16 corpus)

Committed companion (Git-tracked): `graphs/gpu_run5_20260823_ddd267b0/` (59 M) —
`tables/phase9_failure_events.csv` (128,007 events), `phase9_formula_examples.csv`
(true / raw predicted / variable mapping), `phase9_condition_metrics.csv`, `phase9_failure_funnel.csv`,
`phase9_cross_run_rankings.csv`, `phase9_preregistration_outcomes.csv`, plus 10 SVGs.

**Do not overwrite** any of the 29 existing `results/runs/*` directories (rule 05). Use new run IDs.

---

## 7. Reusable code (do not reimplement)

- **metrics**: `src/evaluation/equation_metrics.py` — `nmse:97`, `nmse_vs_variance:105`, `r2_score:113`,
  `variable_recovery:125`, `complexity:141`, `to_skeleton:153`, `symbolic_recovery:169`
  (exact/skeleton/equiv), `expression_safety:250` (singularity/extrapolation),
  `score_prediction:295`, `failure_penalized_nmse:358`, `score_domain_predictions:364`.
  All SymPy paths are wall-clock guarded (`_timed_simplify:56`, `_timed_equals:62`).
- **structural distance**: `src/gpu_run4/ted.py:313 system_ted` (index-aligned, ODE systems),
  `src/gpu_run3/ted.py:249 ted_metrics` (prefix, variable-aware). Backed by `zss==1.2.0`.
- **failure-aware aggregation with `valid_rate`**: `src/evaluation/aggregation.py:19` —
  bare `nmse`/`r2` aliases deliberately point at the *penalized* values to prevent survivorship bias.
- **CIs / paired-seed stats**: `src/gpu_run4/aggregation.py:22 student_t_ci`,
  `src/evaluation/generalization.py:55 aggregate_lodo`,
  `src/evaluation/layer_contribution.py:120 rank_correlations` / `:150 ranking_stability`,
  `src/gpu_run5/training.py:803 pairwise_rank_stability`,
  `src/gpu_run5/interventions.py:269 paired_layer_effects` / `:328 p5_damage_spearman`
- **SR record schema (satisfies rule 03)**: `src/gpu_run4/records.py:7 GPU_RUN4_REQUIRED_FIELDS`
  (30 fields incl. `candidate_index` + `selected` to separate generation from selection, and a
  22-entry `FAILURE_REASONS` enum), `:76 make_formula_record`;
  `src/evaluation/equation_records.py:64 make_equation_record`
- **frozen structural classifier**: `src/evaluation/gpu_run5_structure.py:206 classify_formula` —
  `hill_form`, `modulated_hill_form`, `variable_denominator_form`, polynomial degree, sigmoid,
  exponent-aware skeleton. **This is the definition of record for "true skeleton in beam".**
- **frozen selection key**: `src/evaluation/gpu_run5_selection.py:11 formula_selection_key`
- **reproduction bias (CTC_NSR)**: `src/evaluation/reproduction_bias.py:140 classify_reproduction`
- **splits**: `src/data/splits.py` (5 granularities: group, motif/family, fixed problem-variant,
  frozen structure holdout G01-G08, `assert_problem_splits_disjoint:83`);
  trajectory-level `src/data/dream4.py:153`; parameterized-system-level `src/gpu_run5/grn.py:223`
- **layer analysis, all six contract estimands, per model** — ODEFormer stack:
  probe `src/gpu_run5/observational.py:124/:266`, CKA `:314`, gradient `:328`,
  DecoderLens `:365`/`:427`; causal hooks `src/gpu_run4/hooks.py:23/:47/:62/:87` and
  `src/gpu_run5/interventions.py:39/:88/:129/:222/:382`; IOLE `src/gpu_run4/training.py:23/:58`,
  `src/gpu_run5/training.py:260`, `src/gpu_run5/phase7.py`; selective FT `src/gpu_run5/phase8.py`,
  `src/gpu_run5/training.py:707 deterministic_random_layer_sets`
- **ODEFormer formula handling**: `src/gpu_run4/formulas.py` (721 lines; parse / instantiate /
  canonicalize / compare, `:528 instantiate_odebench_item`); architecture audit
  `src/gpu_run4/architecture.py:238`, `:89 ranking_layer_names`, `:391 set_trainable_layers`
- **provenance**: `scripts/ops/run_manifest.py` (`start|finish|stage|resume`, records git commit/branch,
  `pip freeze`, GPU + driver, checkpoint SHA256, recursive data-tree fingerprints, `--strict` resume
  refuses on commit mismatch / dirty tree / changed `LANSR_*` params);
  `scripts/ops/validate_gpu_run.py`; `scripts/ops/export_run_summary.py`
- **phase scaffolding template**: `src/gpu_run4/cli.py` (`common_parser`, `phase_budget`,
  `write_phase_manifest`, `require_previous`, `dummy_phase_output`); `src/gpu_run5/config.py`
  (`load_config`, `run_dir`, `phase_dir`, `write_manifest`, `budget`, `require_artifact`,
  `load_sealed_test` firewall, `sanitize_nonfinite`)

`third_party/` all four vendored packages import cleanly under `lansr310`:
`nesymres` (pip editable), `odeformer` (path-injected), `nd2` (package dir `ND2/`), `tpsr`
(flat: `symbolicregression`, `dyna_gym`). `GitHubSourceCode/` is reference-only and must never be a
runtime dependency.

---

## 8. Known defects and cheap fixes (candidates for safe repo-level changes)

1. ~~**`pytest.ini` omits `GPU_RUN5/tests`.**~~ **FIXED (C0001)**: `GPU_RUN5/tests` added to
   `testpaths` and `pythonpath = .` added. The default suite now runs **301 passed, 1 skipped**
   (the skip is the optional DREAM4 archive), up from 178 collected, so the 124 GPU_RUN5 tests
   including the sealed-test firewall coverage now execute by default.
   Note on the audit's related claim: `ModuleNotFoundError: No module named 'scripts'` did **not**
   reproduce here — `GPU_RUN5/tests` collected 124 and passed 124 bare, because
   `GPU_RUN5/tests/conftest.py` inserts `src/` on `sys.path`. It does not insert the repo root, which is
   the latent fragility, so `pythonpath = .` was added defensively to make that assumption explicit
   rather than to fix an observed failure.
2. ~~`assets/nd2/weights/checkpoint.pth` has no recorded SHA256 anywhere.~~ **FIXED (C0001)**: recorded
   as `619d419b449a309c97d5b9ab6b8c9f53c91b45a409a3a9bf5b6ac79cb4f625d4` (81,136,260 B) in
   `assets/nd2/README.md`. Identity record for the artifact on disk, not verification against an
   upstream published checksum.
3. `GPU_RUN5/README.md` and `GPU_RUN5_summary_report.md` §9.1 link six report filenames that do not exist
   (`GPU_RUN5_experiment_summary_report.md`, `..._decoded_support_report.md`, `..._grn_benchmark_report.md`,
   `..._grn_adaptation_report.md`, `..._layer_analysis_report.md`, `..._cross_model_synthesis.md`).
   The real files are `GPU_RUN5_summary_report.md` and `GPU_RUN5_{A,B,C,D,E}_*.md`.
4. `results/runs/gpu_run4_phase0_01/manifest.json` status stuck at `running`, commit `0641fa7`.
5. There is **no `data/` directory** (gitignored and absent). DREAM4 lives at
   `GitHubSourceCode/dynGENIE3/data/dream4/` (224 M, size-10 x5 + size-100 x5 + gold standards) and
   GSE112372 at `GitHubSourceCode/dynGENIE3/data/human/gse112372_lps/`. Because `GitHubSourceCode/` must
   not be a runtime dependency, using either requires **copying** into `third_party/`/`assets/` first.
   `src/data/dream4.py:16 DREAM4_ROOT_CANDIDATES = (Path("data/dream4"),)` currently raises
   `FileNotFoundError`. Only a Windows link helper exists (`scripts/ops/setup_phase0_links.ps1`).

None of these are hard stops. Items 1, 2 and 4 are safe to fix inside a cycle.

6. ~~`pytest GPU_RUN5/tests` fails collection without `PYTHONPATH=.`~~ **NOT REPRODUCED, and now moot.**
   The audit reported 6 files raising `ModuleNotFoundError: No module named 'scripts'`. This did not
   reproduce: `GPU_RUN5/tests` collected 124 and passed 124 bare, because
   `GPU_RUN5/tests/conftest.py` inserts `src/` on `sys.path`. It does not insert the repo root, which is
   the real latent fragility, so `pythonpath = .` was added defensively in the defect-1 fix. Both are
   now in `pytest.ini` and the default suite is 301 passed / 1 skipped.
7. **`scripts/ops/run_manifest.py:28 tree_sha256` byte-reads every file under a `--data-path` via
   `rglob("*")`.** Pointing it at a GPU_RUN5 run directory would open all three sealed test artifacts,
   including the campaign's only **unspent** seal. GPU_RUN5's own phase 8 treats hashing sealed bytes as
   the test-open event. Any C0001 manifest call must pass an explicit narrow path list, never the run
   root. (Found in C0001 Stage 3 reproducibility audit; leakage-relevant.)
8. **`src/gpu_run4/formulas.py` CAS equivalence has a silent-failure surface.**
   `SYMPY_MAX_NODES = 40` is a *combined* truth+candidate node budget and `formulas.py:434` returns
   `0.0, None` on exceeding it — no failure reason recorded. Asked whether a GRN truth equals *itself*,
   the CAS path answers no for 52/80 systems (R05-R08: 0/10 each); over 3,000 real pairs 55.1% exceed
   the cap (R06/R07/R08 at 100%). Every bare `except Exception` in that path likewise returns an
   unlabelled non-match. This is *conservative for a recovery score* but **anti-conservative for any
   null-shaped claim**, and no monotonicity or failure-budget check can detect it because a spuriously
   empty result is monotonicity-consistent. Must be fixed or explicitly bounded before any CAS-based
   null is reported. (Found in C0001 Stage 3 reproducibility audit.)

---

## 8b. Standing campaign rules adopted from cycle experience

**R1 (adopted 2026-09-09, C0001, after a supervisor retraction).**
Before reporting any re-measurement of a prior run as new:
(a) verify that both sides of any comparison come from the **same derivation path** — do not compare a
prefix-derived string against an infix-derived string, and do not test for an operator by searching a
canonicalized string for its surface token; and
(b) **grep the source run's stored artifacts for the quantity itself** before claiming to have measured
it. Re-deriving an already-published number is a *positive control*, not a finding, and should be run
and labeled as such.
Origin: `GPU_RUNclaude1/analyses/C0001_RETRACTION_neg_finding.md`. Two errors of exactly this shape
occurred in C0001 Stage 1 (the `pow2` surface-token search and the prefix-vs-infix skeleton comparison).

**R2 (adopted 2026-09-09, C0001, from the v2 audit's control-battery findings).**
A control is not well-posed until the population it runs on has been *verified* to have the property
the control assumes. Concretely: positive-control rewrites must be verified function-**preserving**,
negative-control alterations verified function-**changing**, and every threshold expressed as a fraction
of the **realized eligible set** rather than as an absolute count against an assumed population size.
Freeze a minimum eligible-set size below which the control is `not_measurable` and non-gating.
Origin: both V2-CRIT-1 (a gate at 76/80 against a population that measures 0) and V2-CRIT-2 (10 of 60
negative-control cases were commutative no-ops where matching is correct) had exactly this shape.
Corollary adopted with it: run the control battery **before** the expensive endpoint pass, so a
hard-abort costs the battery rather than the whole budget.

**R4 (adopted 2026-09-09, C0001, from the PC2b discrepancy).**
A control's reduction level must match its endpoint's reduction level. Scoring a *system* while
counting *components* lets untouched components match themselves and inflates the result to a
trivial-match count reported against the wrong denominator. State each control's unit explicitly, and
when a rewrite or alteration fires on only part of a system, compare **only the parts where it fired**.
Corollary: any rewrite used by both a control and a reported endpoint must be identity-verified per
instance, because a rewrite that is not an identity corrupts both.
Origin: `GPU_RUNclaude1/analyses/C0001_pc2b_discrepancy_resolution.md`.

**R3 (adopted 2026-09-09, C0001).**
Before asserting that a sealed or otherwise restricted artifact is untouched, verify how its recorded
digest was produced. A hash present in a run's metadata may have been computed by the producing phase
itself, outside any access ledger — in which case "never touched" is false even though "never evaluated"
is true. Origin: the phase-4 seal correction in §4 above.


---

## 9. Hard-stop status

No hard-stop condition is active as of C0001 Stage 0:
branch correct; working tree clean; no destructive operation required; no confidential data encountered;
no new credentials or paid access needed; test leakage preventable (firewall code exists and the spent
seals are documented); compute ceiling not exceeded; GPU/storage state healthy (54 C, 117 G free);
no prior results need overwriting (new run IDs will be used); no licensing/ethics question open;
no crash loop.

## Human review queue
See `human_review_queue.md` — currently empty.

## Next action
C0001 Stage 1 (hypothesis tree) and Stage 2 (literature) are running.
Then Stage 3 preregistration, Stage 5 reproducibility audit, Stage 6 smoke, Stage 7 full run.
