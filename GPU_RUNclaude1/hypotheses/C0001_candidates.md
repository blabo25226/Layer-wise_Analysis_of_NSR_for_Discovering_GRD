# C0001 — Candidate Hypotheses (Stage 1)

- Cycle: `C0001`
- Branch: `20260909_researce_GPU_RUNclaude1`
- Commit: `94a571b6944e4ebb383ea112a2c9032e3dd6b68e`
- Date: 2026-09-09
- Tree: `GPU_RUNclaude1/hypothesis_tree.md`
- Run root for reusable artifacts: `results/runs/gpu_run5_20260823_ddd267b0/` (abbreviated `R5/` below)
- GPU_RUN4 root: `results/runs/gpu_run4_phase0_01/` (abbreviated `R4/` below)

Nine candidates, `H0001`-`H0009`. They are designed to be **mutually discriminating**, not
variations of one idea. Five of them (`H0001`, `H0002`, `H0003`, `H0004`, `H0005`) are
competing explanations of the *same* observation — the generation failure — and each one's
support constitutes evidence against the others. `H0006` audits whether that observation is
even measured correctly. `H0007` is the layer-side candidate exploiting the P5 result.
`H0008` and `H0009` are lower-priority.

Compute figures assume the C0001 envelope: RTX 2070, **~6.5 GiB usable VRAM shared with the
live desktop**, per-cycle ceiling of a few GPU-hours.

---

## H0001 — Within-support prior mass (representational reachability)

- **id**: `H0001`
- **statement**: For GRN validation systems, the pretrained ODEFormer decoder assigns the ground-truth token sequence a teacher-forced sequence log-probability **below the minimum log-probability among its own 50 sampled beam candidates** for **>= 80%** of systems (n = 80), and the mean per-token ground-truth log-probability is **more than 0.5 nats/token worse** than the mean per-token log-probability of the selected candidate. Direction: truth is ranked *below everything the model itself samples*.
- **parent_branch**: `H-F1` (new branch H-F; parent of record `H-A`)
- **why_it_follows**: GRN `true_exponent_aware_skeleton_in_beam_rate = 0.0` over 960 cells and 47,987 candidates — never once. Stage-1 fact F2 proves this is not expressibility (560/560 ground truths encode and round-trip exactly, constants included) and F1/F3 prove it is not operator support (every GRN truth uses only `add`/`mul`/`inv`/`pow2`/`id`, all of which have nonzero sampling probability). With those two eliminated, only prior mass and search budget remain live, and no experiment to date has measured *where the truth actually sits* in the model's own probability distribution. Unique skeletons per beam is 9.28, consistent with either explanation, so diversity statistics cannot settle it.
- **competing_alternatives**:
  - vs **H0003** (search budget): decisive. If truth log-prob is below the model's own sampled minimum, no realistic temperature or beam increase can surface it and H0003 must fail. If truth log-prob lies *inside* the sampled range, H0001 is refuted and H0003 becomes the leading explanation. These two cannot both be true.
  - vs **H0002** (operator support): H0001 holds the encoding fixed and in-support, so support is not a free parameter; H0002 predicts failure is categorical and out-of-support-driven, H0001 predicts it is graded and occurs *within* support.
  - vs **H0004** (encoder conditioning): H0001 localizes the deficit in the decoder prior given the encoder's output; if H0004 is supported instead, the fix is upstream and H0001's low mass is a symptom rather than the cause.
  - vs **H0006** (canonicalization): H0006 is the null-hypothesis audit of H0001's own instrument; H0001 must be interpreted conditionally on H0006.
- **primary_endpoint**: per-system indicator `1[logP(truth) < min_k logP(candidate_k)]`, and the percentile rank of `logP(truth)` within the empirical candidate log-prob distribution. Secondary: mean per-token log-prob gap (nats/token), truth vs selected candidate.
- **statistical_unit**: GRN system (n = 80, `R5/phase2/validation.json`), clustered by family R01-R08 for inference (8 clusters). Report per-family rates; families are the replicate unit for any cross-family claim.
- **what_supported_looks_like**: >= 64/80 systems have truth below the sampled minimum; percentile rank concentrated near 0; per-token gap > 0.5 nats. Interpretation: the target structures are effectively unreachable under the pretrained prior, and the campaign's remedy must change the *distribution* (pretraining/adaptation distribution, structure-constrained decoding), not the search.
- **what_unsupported_looks_like**: truth log-prob falls inside the sampled candidate range for a substantial minority (>= 20/80), i.e. the model does assign the truth competitive mass but sampling at temperature 0.1 never realizes it. Interpretation: reachability is intact, the failure is search, and H0003 is promoted.
- **informative_on_failure**: **yes.** The two outcomes point to opposite and non-overlapping remedies (change the distribution vs change the search). There is no outcome in which the cycle learns nothing, because the endpoint is a measurement of a quantity that has never been measured in this campaign, not a comparison against a baseline.
- **estimated_compute**: forward-passes only. 80 systems x (1 ground-truth pass + 50 candidate passes) ~ 4,080 teacher-forced forward passes on a 60.6M-param model with short target sequences. **~0.3-0.7 GPU-hours, peak VRAM < 2 GiB** at batch 1-4 fp32 (weights ~250 MB; activations dominated by the point-bag encoder input). Comfortably inside the shared 6.5 GiB. Can also run on GPU 1 (GTX 1060 3 GB) if the desktop needs GPU 0.
- **engineering_cost**: **low.** `teacher_forcing_loss(model, times, trajectory, tree_encoded)` already exists at `src/gpu_run4/training.py:23-48` and does exactly the required forward computation. One change is needed: it returns the *mean* CE from `decoder("predict", ...)`, so a summed / per-token variant must be added (call with `get_scores=True`, or gather log-softmax at the `pred_mask` positions). Ground-truth token sequences are already stored as the `tree_encoded` field, so nothing needs to be re-encoded. **To verify in Stage 3/4**: whether per-candidate log-probs are already persisted in `R5/phase3/all_candidates.json` (ODEFormer's sampling path returns scores); if so, the 50 candidate re-scoring passes are unnecessary and cost drops by ~50x. Note that any stored score must be checked for length-normalization before use.
- **reusable_artifacts**:
  - `results/runs/gpu_run5_20260823_ddd267b0/phase2/validation.json` (80 GRN systems; fields `tree_encoded`, `effective_teacher_prefix`, `teacher_components_prefix`, `trajectories`, `teacher_token_length`, `teacher_valid`)
  - `results/runs/gpu_run5_20260823_ddd267b0/phase3/all_candidates.json` (181 MB, 47,987 GRN candidates)
  - `results/runs/gpu_run5_20260823_ddd267b0/phase3/beam_groups.json`, `phase3/selected.json`, `phase3/failure_funnel_records.json`
  - `results/runs/gpu_run5_20260823_ddd267b0/phase4/fixed_grn_validation_panel.json` (24-system stratified panel, for a smoke subset)
  - `src/gpu_run4/training.py` (`teacher_forcing_loss`, `_point_bag`), `src/gpu_run5/observational.py` (`token_category`, feature/hook plumbing)
  - `assets/odeformer/weights/odeformer.pt`
- **novelty_status**: **adjacent**. Teacher-forced scoring of held-out ground-truth sequences is standard practice in machine-translation and language-model analysis, and "the model cannot sample what it assigns no mass" is a known idea. Its specific use to *dissociate reachability from search budget as competing explanations of neural symbolic regression recovery failure* is **unverified** — Stage 2 must check the ODEFormer paper, the NeSymReS/SymbolicGPT line, and the beam-search-for-SR literature before any novelty claim. Do not label novel on repository absence (rule 11).
- **depends_on_unverified_assumptions**:
  1. That the stored `tree_encoded` sequence is the encoding the model's own decoder would treat as canonical (audited by H0006 — this is the main threat).
  2. That `teacher_forcing_loss`'s point-bag construction matches the inference-time embedder input exactly (verify against the `phase3` generation path; a mismatch would make the two log-probs incomparable).
  3. That candidate log-probs, if reused from storage, are not length-normalized differently from the ground-truth score.
  4. F1's "zero probability" is confirmed for the checkpoint's generator config but not from published training logs (see tree, Model identity).
- **expected_information_gain**: **high.** It measures the single unmeasured quantity that separates the only two surviving explanations of the campaign's headline negative, and it does so on the corpus where the negative is strongest (0/960).
- **information_gain_per_cost**: **9**

---

## H0002 — Operator-support attribution (expressibility retargeted to ODEBench)

- **id**: `H0002`
- **statement**: Among the 63 ODEBench systems, requiring at least one **zero-sampling-probability** operator (`div` with a variable denominator, `sub`, `pow3`/integer powers >= 3, `exp`, `log`, `sqrt`, `abs`, `cos`, `tan`, inverse trig) is **sufficient but not necessary** for generation failure. Two-part prediction: (a) out-of-support systems have truth-in-beam rate **<= 2%**; (b) in-support systems have truth-in-beam rate **>= 15%**. Part (b) is the falsifier for "operator support is the main explanation".
- **parent_branch**: `H-F2` (parent of record `H-A1`/`H-A3`)
- **why_it_follows**: Stage-1 fact F1 established from the checkpoint's own generator that 12 operators have sampling probability **exactly 0.0000** while sitting in a 10293-word vocabulary. Fact F4's preliminary CPU classification splits ODEBench 18 out-of-support / 45 in-support. GPU_RUN4/5 found 57/63 systems never had truth in beam and skeleton-exact hits concentrated in exactly 6 easy 1D systems (RC circuit, population growth, autocatalysis, language death, laser photons, SIR-2D). So the in-support in-beam rate is expected near 6/45 ~ 13% and part (b) is expected to *fail marginally* — which is the informative outcome, because it forces the conclusion that ~39 of 45 in-support systems fail for reasons internal to the learned distribution, i.e. H0001.
- **competing_alternatives**:
  - vs **H0001**: complementary and dissociating. GRN is 100% in-support (F2) yet 0/960, so H0002 is already refuted *for GRN*; if H0002 also fails part (b) on ODEBench, prior mass (H0001) is left as the only explanation on both corpora — a two-corpus convergence that neither candidate can deliver alone.
  - vs **H0008** (dimensionality): H0002 supplies the ground-truth token lengths and operator counts that H0008 needs as covariates; if operator support absorbs the apparent dimension effect, H-A4 is demoted.
  - vs **H0003**: if failure is categorical (out-of-support), budget increases are irrelevant for that subset regardless of temperature.
- **primary_endpoint**: difference in truth-in-beam rate between the in-support and out-of-support groups, with Wilson intervals; secondary, the *residual* in-support never-in-beam rate (the quantity that motivates H0001).
- **statistical_unit**: ODEBench system (n = 63). Cell-level rates (252 cells = 63 x 4 corruptions) reported as secondary, clustered by system — cells within a system are not independent.
- **what_supported_looks_like**: out-of-support truth-in-beam <= 2% **and** in-support >= 15%, with a group difference whose Wilson intervals do not overlap. Interpretation: fixing the operator distribution is a high-yield intervention.
- **what_unsupported_looks_like**: in-support rate also very low (< 15%, expected ~13%). Interpretation: operator support is a real but minor and *sufficient-only* cause; the dominant failure is within-support prior mass. This is a partial result and it is preregistered as the *expected* one.
- **informative_on_failure**: **yes.** The design deliberately preregisters a threshold it is likely to miss, because missing it is the result that converts a vague "the grammar is wrong" intuition into a quantified attribution and hands the cycle a clean motivation for H0001. There is also a genuine surprise channel: if out-of-support systems *do* sometimes reach truth, the model generalizes beyond its own generation support, which would be a notable positive claim about vocabulary tokens that were never sampled in training.
- **estimated_compute**: **CPU only, minutes (< 0.1 CPU-hours). Zero VRAM.** No model execution: parse the 63 ground truths with sympy, convert to ODEFormer prefix, and test operator membership.
- **engineering_cost**: **low.** Needs a sympy-expression to ODEFormer-prefix converter plus a support-membership check. **To verify in Stage 3/4**: GPU_RUN5 already computed a canonical exponent-aware truth skeleton for ODEBench in order to report `all_group_true_exponent_skeleton_in_beam_rate`, so a truth prefix representation very likely already exists and can be reused instead of written — check `R5/phase1/decoded_support.json` (keys include `truth_form_system_ids`, `truth_form_component_counts`, `variable_denominator_system_ids`) and `R4/phase4/corpus.json` (which carries `tree_encoded` and `skeleton_tree_encoded`). Reuse first (rule: reuse repository utilities).
- **reusable_artifacts**:
  - `third_party/odeformer/odeformer/odebench/strogatz_extended.json` (63 systems; `substituted`, `eq`, `dim`, `consts`)
  - `results/runs/gpu_run5_20260823_ddd267b0/phase1/decoded_support.json` (`variable_denominator_system_ids`, `rational_with_variable_denominator_system_ids`, `truth_form_system_ids`, `candidate_support_by_form_dimension_corruption`)
  - `results/runs/gpu_run5_20260823_ddd267b0/phase1/candidates_annotated.json` (46 MB, 12,600 ODEBench candidates with form flags), `phase1/selected_annotated.json`
  - `results/runs/gpu_run4_phase0_01/phase4/corpus.json` (`tree_encoded`, `skeleton_tree_encoded`)
  - `third_party/odeformer/odeformer/envs/generators.py`, `envs/encoders.py` (`Equation.encode` / `_decode`)
- **novelty_status**: **known** as a general principle (training-distribution support limits symbolic recovery; the ODEFormer paper's own operator configuration is public). The *specific quantified attribution* for this checkpoint and the in-support residual is **unverified**. Claim no novelty for the principle.
- **depends_on_unverified_assumptions**:
  1. That `params.operators_to_use` in the released checkpoint governed the actual pretraining run (see tree, Model identity) — this is the load-bearing unverified assumption and Stage 2 must address it.
  2. That the sympy-to-prefix conversion does not silently rewrite an out-of-support truth into an in-support form (e.g. `sub` to `add`+`mul(-1)`, `div` to `mul`+`inv`); the classification must be defined over the *minimal in-support encoding exists / does not exist* predicate, not over surface syntax. `cos` is a boundary case: `cos(x) = sin(x + pi/2)` is in-support in principle, so it must be classified explicitly and consistently, not by string match.
  3. That the F4 preliminary string-based split survives a proper symbolic classification (F4 used regular expressions and is explicitly labelled preliminary).
- **expected_information_gain**: **medium-high.** Part of the answer is already implied by the known "6 systems ever in beam" figure, which caps the surprise; the increment is the mechanistic attribution, the boundary-case handling, and the two-corpus dissociation with GRN.
- **information_gain_per_cost**: **9** (modest absolute gain divided by an almost negligible cost)

---

## H0003 — Search budget and sampling diversity

- **id**: `H0003`
- **statement**: Raising sampling temperature from 0.1 to {0.5, 1.0} and beam budget from 50 to 200 raises the GRN true-exponent-aware-skeleton-in-beam rate from **0.0** to **> 0.5%** (>= 5 hits at 960-cell-equivalent exposure) and raises unique skeletons per beam from **9.28** to **> 25**.
- **parent_branch**: `H-A2`
- **why_it_follows**: Generation uses `beam_size=50`, `beam_type=sampling`, `beam_temperature=0.1`. A temperature of 0.1 makes sampling near-deterministic, which is quantitatively consistent with the observed 9.28 unique skeletons per beam (ODEBench 9.19). Low measured diversity is therefore predicted by *both* low prior mass and inadequate sampling, so the diversity statistic alone cannot separate them — but a direct budget/temperature sweep can, and it was explicitly deferred by GPU_RUN5 to "next run, prefixed in advance".
- **competing_alternatives**: The direct complement of **H0001**. If H0001 is supported (truth below the model's own sampled minimum), H0003 must fail; if H0003 succeeds, H0001 is refuted. Also discriminates against **H0002** on the in-support subset, where support is not the issue.
- **primary_endpoint**: truth-in-beam count at each (temperature, budget) setting; secondary, unique exponent-aware skeletons per beam, and the validity rate (raising temperature is expected to trade validity for diversity, which must be reported, not hidden).
- **statistical_unit**: cell, **paired** across settings by system and initial condition (identical ICs across arms). Clustered by system for inference.
- **what_supported_looks_like**: monotone increase in truth-in-beam with temperature/budget, crossing >= 5 hits. Interpretation: the truth was reachable all along and the campaign's decode configuration was the limiting factor — a cheap and immediately actionable fix.
- **what_unsupported_looks_like**: truth-in-beam remains 0 (or < 5) even at temperature 1.0 and beam 200, while unique skeletons rise well past 25. Interpretation: diversity increased without ever touching the truth, which closes the "we did not search hard enough" explanation permanently and is strong corroboration of H0001.
- **informative_on_failure**: **yes, and unusually valuable.** "Insufficient search" is an explanation that can otherwise be invoked indefinitely to excuse any negative. Measuring it once at 4x budget and 10x temperature converts it from a standing excuse into a closed-off, cited result.
- **estimated_compute**: this is the only generation-side candidate, so it costs real GPU: 24-system fixed panel x 4 settings x beam up to 200. Beam 200 with short sequences and a small encoder is memory-light, but decode is sequential. **~1-2 GPU-hours, peak VRAM ~2-3 GiB** (beam 200 KV cache at dim 512 x 12 layers). Fits the envelope but is 3-4x H0001.
- **engineering_cost**: **low-medium.** The generation path already exists (`R5/phase3` produced 47,987 candidates); only the decode configuration is swept. Must reuse the existing exponent-aware skeleton matcher so the new rate is comparable to the 0.0 baseline. Guard against silently changing `max_generated_output_len` (200).
- **reusable_artifacts**:
  - `results/runs/gpu_run5_20260823_ddd267b0/phase4/fixed_grn_validation_panel.json` (24-system stratified panel — the correct smoke/panel unit)
  - `results/runs/gpu_run5_20260823_ddd267b0/phase2/validation.json`
  - `results/runs/gpu_run5_20260823_ddd267b0/phase3/all_candidates.json`, `phase3/beam_groups.json`, `phase3/failure_funnel.json`, `phase3/lambda_selection.json` (baseline at beam 50 / temp 0.1)
  - `src/gpu_run5/observational.py`, `src/gpu_run5/evaluation.py`
- **novelty_status**: **known** (beam/temperature sweeps are routine). Value here is closing a specific deferred item, not novelty.
- **depends_on_unverified_assumptions**: that the 24-system panel is representative of the 80-system validation set (it was constructed as stratified, so this is reasonable but should be stated); that raising temperature does not push outputs outside the evaluator's validity handling in a way that biases the truth-match test.
- **expected_information_gain**: **medium-high**, but **largely conditional on H0001**. Run after H0001, not before: rule (negative-result-recovery) says do not simply increase compute unless evidence specifically points to a budget limitation, and H0001 is precisely the evidence that would point there. Running H0003 first risks spending 2 GPU-hours to answer a question H0001 answers for 0.5.
- **information_gain_per_cost**: **7**

---

## H0004 — Encoder input-conditioning failure

- **id**: `H0004`
- **statement**: Hill exponent class (1 / 2 / 4) and variable-denominator presence are **not** linearly decodable above **majority-baseline + 10 percentage points** from encoder final-layer pooled states (`encoder_3`), while being decodable above that margin from mid-to-late decoder states — i.e. the encoder does not extract the structural evidence needed to raise the truth's probability.
- **parent_branch**: `H-F3`
- **why_it_follows**: The encoder is only 4 layers of dim 256 (verified architecture) and GPU_RUN4 found all encoder CKA pairs in 0.921-0.978 with within-module mean off-diagonal 0.94377 (vs decoder 0.57762) — the encoder's layers are nearly indistinguishable from one another, consistent with weak structural differentiation (though CKA similarity is not itself evidence of missing information). If the truth's low probability originates in conditioning rather than in the decoder prior, the remedy is a different input representation, not a different decoding distribution.
- **competing_alternatives**:
  - vs **H0001**: a clean dissociation. If the encoder *does* linearly encode exponent and denominator presence while the decoder still refuses to emit them, the deficit is isolated to the decoder prior and H0001 is strengthened while H0004 is refuted. If the encoder does not, H0001's low mass is downstream of a conditioning failure and the causal story reverses.
  - vs **H0005**: H0004 asks whether the information is present in the current input; H0005 asks whether *adding* input raises truth mass. Both can be true; if H0004 is refuted and H0005 supported, the information is present but underused.
  - Respects **rule 04**: this is the **probe/readout estimand only** — information availability. It is explicitly *not* a layer-importance ranking and must not be averaged with causal, gradient, or IOLE rankings.
- **primary_endpoint**: balanced accuracy of a ridge/logistic probe per layer (`encoder_0..3`, `decoder_0..11`) minus the majority baseline, on held-out systems. Report all 16 layers separately; no aggregation.
- **statistical_unit**: system/formula. Train/eval split at the **system** level (rule 02: split before constructing derived rows), with family-held-out reporting as a secondary view.
- **what_supported_looks_like**: encoder probes at or near majority baseline (< +10 pp) while decoder probes clear it substantially. Interpretation: fix the input representation / encoder.
- **what_unsupported_looks_like**: encoder probes clear the baseline comfortably. Interpretation: the structural evidence *is* extracted and the failure is purely generative — a strong, clean corroboration of H0001 and a genuine narrowing of the search space.
- **informative_on_failure**: **yes, strongly** — it is a dissociation whose two outcomes assign the deficit to different modules, and one of them (encoder is fine) materially strengthens the cycle's primary hypothesis.
- **estimated_compute**: probe fitting is **CPU-minutes** (code exists). The cached features in `R5/phase4/train_features.npz` (229 MB) and `validation_features.npz` (58 MB) cover the **official** formula corpus, not GRN, so GRN-labelled features must be extracted for the 24-system panel (or the 80-system validation set): forward-only, **~0.1-0.3 GPU-hours, peak VRAM < 2 GiB**. Total well under 0.5 GPU-hours.
- **engineering_cost**: **low.** `fit_layer_probes` (`src/gpu_run5/observational.py:266`), `collect_layer_features` (`:124`), `capture_layer_outputs`, `_factored_classifier` (`:215`) and `token_category` (`:75`) already exist and were used for the GPU_RUN5 probe panel. Needs GRN structural labels, which are derivable from the `structure` and `family` fields already present in `R5/phase2/validation.json`.
- **reusable_artifacts**:
  - `results/runs/gpu_run5_20260823_ddd267b0/phase4/train_features.npz`, `phase4/validation_features.npz` (cached 16-layer features, official corpus)
  - `results/runs/gpu_run5_20260823_ddd267b0/phase4/probes.json`, `phase4/cka.json`, `phase4/teacher_forcing_ce.json`, `phase4/fixed_grn_validation_panel.json`
  - `results/runs/gpu_run5_20260823_ddd267b0/phase2/validation.json` (fields `structure`, `family`, `variable_to_gene`, `tree_encoded`)
  - `src/gpu_run5/observational.py`
- **novelty_status**: **adjacent** (layer-wise linear probing is standard; DecoderLens/logit-lens known). The specific target properties (Hill exponent class, variable-denominator presence) are **unverified** as a probing task.
- **depends_on_unverified_assumptions**: that mean/pooled sequence representations retain the property (`_pool_sequence` at `src/gpu_run5/observational.py:114` averages, which can destroy positional structure); that linear decodability is the right operationalization of "available" — a negative linear probe does not prove the information is absent, only that it is not linearly available, and the report must state this (non-significance is not equivalence, rule 01.8).
- **expected_information_gain**: **medium-high.** Cheap and dissociative, but its interpretation is weaker in the negative direction because of the linear-probe caveat.
- **information_gain_per_cost**: **7**

---

## H0005 — Identifiability: does richer conditioning raise the truth's probability?

- **id**: `H0005`
- **statement**: Conditioning on richer input (multi-initial-condition point bags, or intervention trajectories) increases the teacher-forced ground-truth **mean per-token log-probability by >= 0.15 nats/token** relative to single-IC conditioning, on the same systems (paired).
- **parent_branch**: `H-E1` / `H-E2`, with a direct link to `H-B1`
- **why_it_follows**: The one clean positive in the campaign is GPU_RUN5's P6 HIT: multi-IC selection improved failure-aware generalization NRMSE by **-0.20278**, paired-t 95% CI **[-0.32323, -0.08233]** over 80 system clusters. But P6 measured a *selection* outcome. It is unknown whether multi-IC helps because it disambiguates among already-generated candidates (pure selection) or because it also shifts the generative distribution toward the truth. That decomposition is scientifically important and currently unmeasured.
- **competing_alternatives**:
  - vs **H0001**: if truth mass is data-limited, better conditioning should move it; if the deficit is a fixed decoder prior, conditioning will not. A null here is direct corroboration of H0001.
  - vs **H0004**: H0004 probes what the encoder currently holds; H0005 tests whether *more* input changes the decoder's output distribution. Together they separate "information absent" / "information present but unused" / "information insufficient".
  - vs **H0003**: H0005 changes the conditioning, not the search — if both fail, the failure is intrinsic to the trained distribution.
- **primary_endpoint**: paired difference in mean per-token ground-truth log-probability, multi-IC minus single-IC. Secondary: change in truth-in-beam under multi-IC conditioning.
- **statistical_unit**: system, paired (n = 80, or the 24-system panel for a reduced arm), clustered by family. Paired design mirrors P6's clustered-difference analysis so the two results are directly comparable.
- **what_supported_looks_like**: paired gain >= 0.15 nats/token with a CI excluding 0. Interpretation: the P6 benefit is at least partly generative, and improving conditioning is a route to raising generation support — which is exactly what GPU_RUN5 named as the next main problem.
- **what_unsupported_looks_like**: gain near zero or negative. Interpretation: P6's benefit is **purely a selection effect**, which sharpens the interpretation of the campaign's only clear positive and simultaneously supports H0001.
- **informative_on_failure**: **yes.** A null re-characterizes an existing headline positive rather than merely failing, which is a genuine gain about a result the campaign already relies on.
- **estimated_compute**: forward-only. 80 systems x 2 conditioning modes (x optionally a 3rd intervention mode) ~ 160-240 teacher-forced passes plus optional re-generation. **~0.2-0.4 GPU-hours, peak VRAM < 2 GiB** for scoring; add ~0.5 GPU-hours if truth-in-beam under multi-IC is also generated.
- **engineering_cost**: **medium.** ODEFormer conditions on a single trajectory point bag; multi-IC input requires constructing a concatenated/stacked point bag and checking it against `max_generated_output_len`, the embedder's length handling, and `_point_bag` (`src/gpu_run4/training.py`). GPU_RUN5 already implemented a multi-IC *selection* path and `src/gpu_run5/interventions.py` exists, so precedent exists but the generative conditioning path is new. This is the highest engineering risk among the cheap candidates.
- **reusable_artifacts**:
  - `results/runs/gpu_run5_20260823_ddd267b0/phase2/validation.json` (multi-IC `trajectories` already stored per system)
  - `results/runs/gpu_run5_20260823_ddd267b0/phase3/p6_validation.json` (the P6 multi-IC selection result to compare against)
  - `results/runs/gpu_run5_20260823_ddd267b0/phase3/lambda_selection.json`
  - `src/gpu_run5/interventions.py`, `src/gpu_run5/observational.py`, `src/gpu_run4/training.py`
- **novelty_status**: **plausibly_novel** as a decomposition (separating the generative from the selective component of a multi-IC benefit in neural SR), but recorded as **unverified** pending Stage 2. Multi-IC / multi-trajectory SR itself is **known**.
- **depends_on_unverified_assumptions**: that a multi-IC point bag is in-distribution for an embedder trained on single trajectories — if it is not, a null could reflect distribution shift in the *input format* rather than an absence of identifiability gain. This confound must be preregistered with a control (e.g. same total point count, single IC, to separate "more points" from "more ICs").
- **expected_information_gain**: **high**, because either outcome revises the interpretation of the campaign's only clean positive.
- **information_gain_per_cost**: **8**

---

## H0006 — Encoding canonicalization audit (measurement validity)

- **id**: `H0006`
- **statement**: The **maximum** teacher-forced ground-truth log-probability taken over the set of semantically equivalent token encodings exceeds the single canonical encoding's log-probability by **>= 0.10 nats/token for >= 30%** of GRN systems; and re-scoring truth-in-beam under equivalence-class (canonical-form) matching raises the measured GRN rate **above 0**.
- **parent_branch**: `H-G1` (= residual `H-A3'`)
- **why_it_follows**: Stage-1 fact F1 shows the decoder vocabulary contains `div`, `pow3`, `sub`, `pow` alongside the in-support `inv`, `mul`, `add`, `pow2`. A denominator can be written `div(a,b)` or `mul(a, inv(b))`; x^3 as `pow3(x)` or `mul(x, pow2(x))`; x^4 as `pow2(pow2(x))` or `pow(x,4)`; subtraction as `sub` or `add(a, mul(-1,b))`. The GRN corpus committed to exactly one encoding per truth (F2 showed it used `inv`/`mul`/`add`/`pow2`). If prior mass and truth-in-beam are scored against that one encoding only, both are biased **downward**, and the 0/960 headline could be partly an artifact of the encoding choice rather than a property of the model.
- **competing_alternatives**: This is the **null-hypothesis audit of H0001's instrument**, not a rival explanation of the biology. It discriminates "the model has no mass on the structure" (H0001) from "we measured mass on one spelling of the structure". Every other generation candidate inherits the same instrument, so H0006 conditions the interpretation of H0001, H0003 and H0005 alike.
- **primary_endpoint**: per-system Δ log-prob (max-over-encodings minus canonical), and the recomputed truth-in-beam rate under canonical-form matching.
- **statistical_unit**: GRN system (n = 80), clustered by family.
- **what_supported_looks_like**: a substantial max-over-encodings gap. Interpretation: **the campaign's headline negatives require restatement**, and all prior-mass figures must be reported as equivalence-class maxima. This would be a CRITICAL-severity finding against prior analyses and would trigger the replication gate.
- **what_unsupported_looks_like**: the canonical encoding is already the argmax or nearly so, and equivalence-class matching leaves truth-in-beam at 0. Interpretation: **0/960 is hardened as a genuine model property**, and every downstream claim built on it (including H0001) becomes materially more defensible.
- **informative_on_failure**: **yes, and it is the most leveraged null in the set.** A null does not merely fail to find an effect; it removes the single most plausible measurement objection to the campaign's central negative result. Rule 07 and the independent-review contract effectively demand this check before the negative is promoted.
- **estimated_compute**: enumeration of equivalent encodings is **CPU-minutes**; scoring is forward-only, ~80 systems x (3-8 encodings) ~ 250-650 passes. **~0.1-0.2 GPU-hours, peak VRAM < 2 GiB.** Shares its entire instrument with H0001, so marginal cost when run alongside H0001 is close to zero.
- **engineering_cost**: **low-medium.** Needs a small rewrite-rule enumerator over the prefix tree (`div` <-> `mul`+`inv`, `sub` <-> `add`+`mul(-1)`, `pow3` <-> `mul`+`pow2`, `pow2∘pow2` <-> `pow(·,4)`, plus `add`/`mul` commutation and `id` insertion) with a cap on enumeration depth, and a semantic check via `sympy` that each rewrite is truly equivalent. `Equation.encode`/`_decode` (`third_party/odeformer/odeformer/envs/encoders.py:260,275`) provide the round-trip. Commutation alone can explode combinatorially, so the enumeration must be bounded and the bound preregistered.
- **reusable_artifacts**:
  - `results/runs/gpu_run5_20260823_ddd267b0/phase2/validation.json` (`tree_encoded`, `teacher_roundtrip_prefix`, `effective_teacher_prefix`, `teacher_components_prefix`)
  - `results/runs/gpu_run5_20260823_ddd267b0/phase3/all_candidates.json`, `phase3/beam_groups.json`
  - `third_party/odeformer/odeformer/envs/encoders.py`, `envs/simplifiers.py`
  - `graphs/gpu_run5_.../tables/phase9_formula_examples.csv` (true / raw predicted / variable mapping — for manual adjudication of a sample)
- **novelty_status**: **plausibly_novel** as a specific measurement-validity check for neural symbolic regression recovery metrics; recorded **unverified** pending Stage 2. The underlying issue (multiple prefix spellings of one expression) is **known** in the SR literature and motivates skeleton/canonical-form metrics generally.
- **depends_on_unverified_assumptions**: that the equivalence enumeration is semantically sound (must be sympy-verified, not assumed); that bounded enumeration does not miss the true argmax encoding, which means a null is only ever "no gap within the preregistered rewrite set" — that limitation must be stated explicitly rather than reported as "no gap".
- **expected_information_gain**: **high**, because it gates the credibility of the campaign's central negative in both directions.
- **information_gain_per_cost**: **8**

---

## H0007 — LAYER: the CE-vs-formula divergence is token-role-systematic, not noise

- **id**: `H0007`
- **statement**: The per-layer divergence between teacher-forcing CE damage and formula-level damage is **systematically explained by token role**. Partitioning the intervention-induced CE change by token category (operator / variable / int / mantissa / exponent / separator), across the 16 layers: Spearman ρ between Δ(operator-token CE) and Δ(failure-aware TED) is **>= 0.6 (p < 0.05)**, while ρ between Δ(mantissa-token CE) and Δ(failure-aware TED) is **<= 0.2** — i.e. the observed overall ρ = **0.008956** is a **cancellation of opposing components**, not an absence of structure.
- **parent_branch**: `H-D4`
- **why_it_follows**: GPU_RUN5's P5 HIT found Spearman between post-intervention ΔCE ranking and failure-aware ΔTED ranking = **0.008956**, two-sided **p = 0.97374**, n_layers = 16. The decisive clue is `decoder_11`: it caused faTED **+0.52692**, `component_valid_loss` 1.0, gen R2 loss 10.466, while `damage_CE` = **-1.61708** — CE *improved* while formulas were destroyed. That is a **sign inversion**, which noise does not produce. A mechanism is available: teacher-forcing CE is dominated *by token count* by numeric mantissa/exponent tokens (the GRN encodings observed in F2 spend 3 tokens per constant, e.g. `+ N1954 E-4`), whereas failure-aware TED is dominated by operator and variable structure. If late decoder layers carry structure while numeric tokens are carried elsewhere, an aggregate correlation near zero is exactly what a cancellation would look like. Supporting: normalized `C_l` disagrees with lexicographic IOLE (`decoder_11` `C_l` = -0.0378 negative while IOLE rank 1; `decoder_10` = 0.3298; `decoder_0` = -0.4157).
- **competing_alternatives**:
  - vs "**the criteria disagree because the interventions are noisy or floored**": directly discriminating. GPU_RUN5's `component_exact_loss` was 0.0 for all 16 layers (a floor) and DecoderLens normalized TED was 1.0 at all 12 decoder layers (saturated), so a floor/noise account is live and must be beaten. H0007's endpoint is chosen to have demonstrated variance (`damage_CE` and faTED both vary substantially across layers).
  - vs "**CE is simply the wrong objective**": H0007 is the stronger, more useful claim — not that CE is wrong, but that a *specific measurable component* of CE is right. If supported it yields an immediately usable, cheap layer-ranking criterion (operator-token CE) with no intervention required.
  - Respects **rule 04**: it does not average estimands. It makes a falsifiable claim about the *relationship between two named estimands* (causal-intervention CE vs causal-intervention formula damage), which is precisely the preregistered scientific justification rule 04 asks for.
- **primary_endpoint**: the two Spearman correlations across 16 layers, and their difference, with a bootstrap CI.
- **statistical_unit**: **dual, and this must be preregistered.** Layer (n = 16) for the correlation itself — underpowered, so the primary inferential unit is the **system-level bootstrap** (resample the 24-system panel, recompute both correlations, report the difference's CI). Reporting a p-value on n = 16 alone would repeat the power problem that makes P5 hard to interpret.
- **what_supported_looks_like**: operator-token ρ >= 0.6 while mantissa-token ρ <= 0.2, with a bootstrap CI on the difference excluding 0. Interpretation: **H-D4 is supported** — criterion disagreement is predictable from token role, the `decoder_11` inversion is explained, and a cheap structural-CE layer criterion becomes available.
- **what_unsupported_looks_like**: both correlations near zero. Interpretation: the divergence is **not** token-role-mediated. This kills the most natural mechanistic story and promotes the stronger reading of rule 04 — that layer importance is irreducibly multi-dimensional and no single scalar readout, however decomposed, will reconcile the criteria.
- **informative_on_failure**: **yes, strongly.** The negative outcome is a substantive claim about the structure of the problem, not an absence of result, and it would justify abandoning the search for a unifying layer criterion — saving future cycles.
- **estimated_compute**: needs per-token CE under each of the 16 single-layer interventions on the 24-system panel. Forward-only with hooks; `alpha = 0.5` mean-ablation is **already calibrated** and the corpus means are already computed. 16 layers x 24 systems x (1 pass) plus a clean baseline ~ 400 passes with per-token score extraction. **~0.5-1.0 GPU-hours, peak VRAM < 2.5 GiB.**
- **engineering_cost**: **low-medium.** Most of it exists: `token_category` (`src/gpu_run5/observational.py:75`) already implements the exact partition needed; `phase5/corpus_means.npz` supplies the mean-ablation vectors at the calibrated alpha; `capture_layer_outputs` and the hook controls exist (`phase5/hook_controls.json`). The new work is extracting **per-token** log-probs under intervention (`get_scores=True` in the `decoder("predict", ...)` call) and aligning them to token categories — the same instrument change H0001 needs, so the two share it.
- **reusable_artifacts**:
  - `results/runs/gpu_run5_20260823_ddd267b0/phase5/corpus_means.npz`, `phase5/corpus_means_meta.json` (alpha=0.5 calibrated)
  - `results/runs/gpu_run5_20260823_ddd267b0/phase5/layer_effects.json`, `phase5/causal_ranking.json`, `phase5/holdout_causal_ranking.json`, `phase5/holdout_layer_effects.json`, `phase5/hook_controls.json`, `phase5/cell_cache/`, `phase5/ce_sweep_records.json`, `phase5/grn_ce_records.json`
  - `results/runs/gpu_run5_20260823_ddd267b0/phase4/teacher_forcing_ce.json`, `phase4/fixed_grn_validation_panel.json`, `phase4/decoder_logit_lens.json`
  - `src/gpu_run5/observational.py` (`token_category`), `src/gpu_run4/training.py`
  - `graphs/gpu_run5_.../tables/phase9_failure_events.csv` (128,007 failure events)
- **novelty_status**: **plausibly_novel** — the specific claim that a near-zero CE/formula rank correlation decomposes into opposing token-role components, in a neural SR decoder, is not something I can attribute to a source. Recorded **unverified**; Stage 2 must check the mechanistic-interpretability literature on token-position/role-specific layer attribution and the logit-lens line before any novelty claim (rule 11).
- **depends_on_unverified_assumptions**: that `token_category` as implemented partitions the GRN token stream into the intended categories (verify against F2's observed encodings, which use `+`/`N####`/`E-4`/`INT-` forms); that the 24-system panel yields enough per-category token counts for stable per-category CE (mantissa tokens are plentiful, but separator and int tokens may be sparse — a minimum-count exclusion rule must be preregistered); that mean-ablation at alpha=0.5 is a meaningful causal manipulation rather than a distribution-shift artifact (`phase5/hook_controls.json` exists to check this and must be inspected).
- **expected_information_gain**: **high.** It is the only candidate that attacks the campaign's most striking unexplained result, and both outcomes are substantive.
- **information_gain_per_cost**: **9**

---

## H0008 — Dimensionality versus token-length confound

- **id**: `H0008`
- **statement**: The 1D-to-3D recovery collapse is explained by **ground-truth token length and required-operator count** rather than by dimension per se: in a logistic model of skeleton-exact recovery including GT token length and operator count, the standardized coefficient on dimension has **|β| < 0.3** and is non-significant at α = 0.05.
- **parent_branch**: `H-A4`
- **why_it_follows**: GPU_RUN4's dimension scaling is stark — 1D recon 0.997 / skeleton 17-of-92; 2D 0.946 / 2-of-112; 3D valid only 25/40, R2>0.9 8/40, skeleton 0; 4D 0.906 / 0. But dimension is confounded with target sequence length, component count, and the `|`-separated multi-component format (`pad_to_max_dim=True`, `max_dimension=6`). GPU_RUN5 also reports `teacher_token_length` per system, so the covariate is already available.
- **competing_alternatives**: discriminates **H-A4 as a primitive cause** from length/complexity as the operative variable. Consumes H0002's output (GT prefixes and operator classification) as covariates, so it is naturally a companion analysis rather than a standalone cycle.
- **primary_endpoint**: standardized logistic coefficient on dimension, controlling for GT token length and out-of-support operator count, with CI.
- **statistical_unit**: ODEBench cell (n = 252), clustered by system (63 clusters) — cells within a system share the ground truth and are not independent.
- **what_supported_looks_like**: dimension coefficient shrinks toward zero once length is controlled. Interpretation: "dimensionality" is not a separate mechanism; target length/complexity is, which redirects effort to sequence-length handling.
- **what_unsupported_looks_like**: dimension survives length-matching with a substantial coefficient. Interpretation: there is a genuine multivariate deficit — plausibly in the multi-component `|` format or the padded dimension handling — which is a concrete new target.
- **informative_on_failure**: **yes**, though the claim is correlational either way and n = 63 systems limits power for a multivariate model with a strongly collinear covariate set (dimension and length are correlated by construction). This is the candidate most at risk of an UNDECIDABLE verdict.
- **estimated_compute**: **CPU-only, minutes. Zero VRAM.** Requires H0002's GT encodings.
- **engineering_cost**: **low** (statistical modelling only), conditional on H0002 having produced GT prefixes.
- **reusable_artifacts**:
  - `results/runs/gpu_run4_phase0_01/phase4/corpus.json` (`tree_encoded`, `skeleton_tree_encoded`, `dimension`, `complexity`)
  - `results/runs/gpu_run5_20260823_ddd267b0/phase1/candidates_annotated.json`, `phase1/decoded_support.json` (`candidate_support_by_form_dimension_corruption`)
  - `results/runs/gpu_run5_20260823_ddd267b0/phase2/validation.json` (`teacher_token_length`, `dimension`)
  - `third_party/odeformer/odeformer/odebench/strogatz_extended.json`
- **novelty_status**: **known** in principle (sequence length limits seq2seq accuracy). **unverified** for this specific attribution.
- **depends_on_unverified_assumptions**: that dimension and token length are separable at all in this corpus — if collinearity is near-total the model is unidentifiable and the result must be reported as UNDECIDABLE rather than as support for either side. Check the variance inflation factor before fitting and preregister an identifiability threshold.
- **expected_information_gain**: **medium.** Cheap and clarifying, but correlational, collinearity-threatened, and it does not change the immediate remedy.
- **information_gain_per_cost**: **6**

---

## H0009 — Parameter-efficient adaptation on the recovery/forgetting Pareto

- **id**: `H0009`
- **statement**: LoRA (rank 8) on decoder attention and FFN projections, trained on `R5/phase2/train.json`, achieves GRN exact-macro **>= 0.15972** (matching `grn_full`) while retaining ODEBench exact rate **>= 0.06** (versus `grn_full`'s catastrophic 0.00794) — i.e. it **dominates** full fine-tuning on the joint recovery/forgetting objective.
- **parent_branch**: `H-C3`
- **why_it_follows**: GPU_RUN5 established a genuine Pareto tradeoff with no dominating condition: `grn_full` recovers best (0.15972) but forgets worst (ODEBench exact 0.08466 → 0.00794, -0.0767), while `grn_top3` recovers less (0.10938) and forgets less (-0.0238). Layer *selection* is not the operative variable (`grn_top3` 0.10938 ≈ `grn_random3_0` 0.10764; GPU_RUN4 found every FT condition worse than frozen), so H-C2 is closed and H-C3 is the untested remaining route. The ~6.5 GiB ceiling also makes PEFT the only affordable adaptation method for a 60.6M-param model this campaign.
- **competing_alternatives**: discriminates **H-C3** from **H-C1** (selective-layer FT) and **H-C2** (layer criterion). It does **not** compete with the generation candidates — and that is precisely its weakness this cycle.
- **primary_endpoint**: the bivariate pair (GRN exact-macro, ODEBench exact rate), evaluated as joint dominance over `grn_full` and `grn_top3`. Component-stratified secondary endpoint is **mandatory**: exact count for the nontrivial Hill / variable-denominator components of R03-R08 (rule H-G3).
- **statistical_unit**: GRN system, clustered by family. **Requires a NEW sealed test set.**
- **what_supported_looks_like**: joint dominance on both axes, *and* a nonzero exact count for nontrivial Hill components.
- **what_unsupported_looks_like**: LoRA lands inside the existing Pareto frontier, or improves aggregate exact-macro while the nontrivial-Hill component count stays at 0 (the outcome every GPU_RUN5 condition produced).
- **informative_on_failure**: **only moderately.** A null is substantially expected: exact component count for nontrivial Hill / variable-denominator components was **0 in every single final condition** of GPU_RUN5, and H-A/H-F now identify generation as the binding constraint — adaptation cannot make the model emit a structure it never generates. There is a real risk this is benchmark hill-climbing on exact-macro, which the aggregate/component decoupling (H-G3) shows is a misleading target. This is the weakest failure-informativeness in the set.
- **estimated_compute**: the only training candidate. LoRA rank 8 adds ~1-2M trainable params; optimizer state is small but activations for a 12-layer dim-512 decoder plus the encoder still dominate. Feasible at small batch with gradient checkpointing in ~4-5 GiB, but it is **shared with the live desktop**, which makes a multi-hour training job the riskiest use of GPU 0 in this set. **~2-4 GPU-hours, peak VRAM ~4-5 GiB.**
- **engineering_cost**: **high.** Must build a LoRA injection layer for the ODEFormer decoder (no PEFT integration exists in the repo), a new training loop or an adaptation of `src/gpu_run5/training.py`, **and generate and seal a new GRN test set** before methods are fixed (rule 02). The sealing requirement alone makes this a multi-stage commitment.
- **reusable_artifacts**:
  - `results/runs/gpu_run5_20260823_ddd267b0/phase2/train.json`, `phase2/validation.json` (240 + 80 systems, RK45 rtol 1e-8)
  - `results/runs/gpu_run5_20260823_ddd267b0/phase6/`, `phase7/`, `phase8/` checkpoints (6.9 GB: `grn_full`, `grn_decoder_all`, `official_continued_full`, `grn_top1`/`top3`/`random3_0..4`, per-layer IOLE deltas) — as **baselines already computed**, which is this candidate's one real efficiency
  - `src/gpu_run5/training.py`, `src/gpu_run5/phase6.py`, `phase7.py`, `phase8.py`
  - `results/runs/gpu_run5_20260823_ddd267b0/phase2/` generator corpus for constructing the new seal
- **novelty_status**: **known** (LoRA and PEFT-vs-full-FT forgetting comparisons are well established). No novelty claim available; the contribution would be domain-specific evidence only.
- **depends_on_unverified_assumptions**: that LoRA rank 8 on the decoder has the capacity to acquire Hill structure that full FT acquired only partially; that a newly generated seal is distributionally comparable to the spent one (otherwise the comparison to `grn_full`'s 0.15972 is not valid — a **serious** threat, since the published `grn_full` number was measured on the now-spent seal and cross-seal comparison is not like-for-like).
- **expected_information_gain**: **low-medium**, and premature. It targets the adaptation branch while the binding constraint is generation.
- **information_gain_per_cost**: **4**

---

## Ranked table (by information gain per cost)

| rank | id | one-line statement | branch | cost | new seal? | IG/cost |
|---|---|---|---|---|---|---|
| 1 | **H0001** | Ground-truth token sequence scores below the model's own sampled candidates → truth is unreachable, not merely unsampled | H-F1 | 0.3-0.7 GPU-h, <2 GiB | no | **9** |
| 2 | **H0002** | Zero-probability operators are sufficient but not necessary for ODEBench generation failure | H-F2 | <0.1 CPU-h, 0 VRAM | no | **9** |
| 3 | **H0007** | The P5 near-zero CE/formula correlation decomposes into opposing token-role components | H-D4 | 0.5-1.0 GPU-h, <2.5 GiB | no | **9** |
| 4 | **H0005** | Richer conditioning raises ground-truth log-prob → P6's benefit is generative, not only selective | H-E1/H-B1 | 0.2-0.4 GPU-h (+0.5), <2 GiB | no | **8** |
| 5 | **H0006** | Equivalent token encodings bias prior-mass and truth-in-beam downward (instrument audit) | H-G1 | 0.1-0.2 GPU-h, <2 GiB | no | **8** |
| 6 | **H0003** | Temperature/beam sweep surfaces truth that beam-50 at T=0.1 misses | H-A2 | 1-2 GPU-h, 2-3 GiB | no | **7** |
| 7 | **H0004** | Hill exponent / variable-denominator not linearly decodable from the encoder | H-F3 | <0.5 GPU-h, <2 GiB | no | **7** |
| 8 | **H0008** | The dimension effect is really a token-length effect | H-A4 | <0.1 CPU-h, 0 VRAM | no | **6** |
| 9 | **H0009** | LoRA dominates full FT on the recovery/forgetting Pareto | H-C3 | 2-4 GPU-h, 4-5 GiB | **YES** | **4** |

**Candidates requiring a NEW sealed test set**: **H0009 only.** The GPU_RUN5 GRN seals
(`phase2/sealed_test.json`, `phase2/sealed_family_holdout_test.json`) were opened on
2026-09-01 and are SPENT. All of H0001-H0008 are validation-only or diagnostic and consume no
seal; `phase4/sealed_official_test.json` (500 official formulas, the only unspent seal) is
**not** required by any of them and should be preserved.

---

## TOP RECOMMENDATION for C0001

**Primary: `H0001` — within-support prior mass / representational reachability, with `H0002`
executed as a mandatory near-free CPU companion, and `H0006` folded in as the instrument
audit if the shared scoring code is ready in time.**

Justification. Stage 1 did not merely re-rank the existing tree; it eliminated two of the five
competing explanations of the generation failure before any GPU time was spent. Expressibility
and tokenization are refuted for the GRN corpus — all 560 ground truths encode to valid token
sequences and round-trip exactly, constants included — and operator support cannot be the GRN
cause either, because every GRN truth uses only operators with nonzero sampling probability,
yet truth-in-beam is 0.0 over 960 cells and 47,987 candidates. That leaves exactly two live
explanations, prior mass and search budget, and they are separated by a single quantity that
this campaign has never measured: where the ground truth actually sits in the model's own
log-probability distribution. H0001 measures it with forward passes only, on ground-truth token
sequences that are *already stored* in `phase2/validation.json`, using a `teacher_forcing_loss`
function that *already exists* in `src/gpu_run4/training.py` — roughly half a GPU-hour and a
low-risk instrument change, which matters because the 6.5 GiB budget is shared with the user's
live desktop and a long training job is the worst use of it. Both outcomes are decisive and
point to non-overlapping remedies: if truth ranks below everything the model samples, the
remedy is distributional (structure-constrained decoding, changing the adaptation distribution)
and H0003 is closed off in advance; if truth ranks inside the sampled range, reachability is
refuted, the failure is search, and H0003 is promoted with evidence rather than on the standing
excuse that we simply did not search hard enough. H0002 rides along for essentially nothing —
CPU-minutes — and supplies the second corpus needed to turn a single-corpus finding into a
dissociation, with the honest expectation, preregistered, that its own threshold will be missed
because ~39 of 45 in-support ODEBench systems also fail. This directly serves GPU_RUN5's own
stated next step, that "improving generation support itself is the next main problem", by
diagnosing *why* the support is missing before spending compute trying to add it. Per rule 03,
nothing here will be claimed as equation discovery: the endpoints are log-probabilities and
in-beam rates, not R2 or NMSE.

**Runner-up: `H0007` — token-role decomposition of the P5 CE-versus-formula divergence.**

Why it lost, narrowly. H0007 is the most scientifically striking candidate and it is the only
one that attacks the campaign's strangest unexplained result: a Spearman of 0.008956 (p =
0.97374) between CE damage and formula damage, with `decoder_11` improving CE by 1.61708 while
destroying formulas (faTED +0.52692, `component_valid_loss` 1.0). It has a real mechanism
behind it, its main tool (`token_category`) and its calibrated mean-ablation vectors already
exist, and both outcomes are substantive — supporting it would deliver a cheap structural-CE
layer criterion and satisfy H-D4, while refuting it would justify abandoning the search for any
unifying layer criterion. It lost on three counts. First, ordering: the layer question is
downstream of the generation question, because knowing which layers destroy structure does not
change the fact that the truth is never generated in the first place, and C0001 should resolve
the binding constraint. Second, statistical power: the correlation lives on n = 16 layers, the
same power problem that makes P5 itself hard to interpret, so it needs a system-level bootstrap
and a preregistered minimum-token-count rule to be worth running once — design work better done
with a cycle's lead time. Third, known floor effects in this exact measurement family
(`component_exact_loss` = 0.0 at all 16 layers; DecoderLens normalized TED = 1.0 at all 12
decoder layers) mean the endpoint must be shown to have variance before it is trusted, and that
check is cheaper to do as part of a dedicated cycle. H0007 is therefore queued as the primary
candidate for **C0002**, and it shares its one required instrument change — per-token log-prob
extraction via `get_scores=True` — with H0001, so building it now for H0001 lowers H0007's cost
next cycle.

**Explicitly deprioritized: `H0009`.** It is the only candidate needing a new sealed test set,
the only one needing hours of training on a desktop-shared GPU, the only one with high
engineering cost, and its null is substantially expected — nontrivial Hill and
variable-denominator component recovery was 0 in *every* GPU_RUN5 final condition. Worse, its
headline comparison target (`grn_full` exact-macro 0.15972) was measured on a seal that is now
spent, so a new seal would not give a like-for-like comparison. Pursuing it now would be
adaptation work aimed at an aggregate metric that H-G3 already shows to be decoupled from the
structures this campaign is about.
