# Hypothesis Tree

Persistent tree of competing explanations for the GPU_RUNclaude1 autonomous campaign.

- Branch: `20260909_researce_GPU_RUNclaude1`
- Commit at last update: `94a571b6944e4ebb383ea112a2c9032e3dd6b68e`
- Last updated: 2026-09-09 (Stage 1 of cycle `C0001`)
- Candidate ranking for this cycle: `GPU_RUNclaude1/hypotheses/C0001_candidates.md`

## Status labels

`OPEN` `ACTIVE` `SUPPORTED` `UNSUPPORTED` `UNDECIDABLE` `REFUTED` `INVALIDATED` `DEFERRED` `ABANDONED`

`REFUTED` is used where prior evidence is strong enough that the node is no longer a live
explanation *as stated*; a residual weaker form is recorded where one survives.

## Root problem

Why do current neural symbolic regression systems often achieve good trajectory fit while
failing robust structural/formula recovery for GRN-like dynamics?

---

## Stage-1 verified facts established during C0001 (new, cheap, CPU-only)

These were established in Stage 1 by direct inspection of the checkpoint and stored corpora.
They are **not** re-derivations of GPU_RUN4/5 results; they change the tree materially and
they eliminate two candidate explanations before any GPU time is spent.

### F1 — Pretraining generation support is severely restricted, and the restriction is exact zero

From the loaded checkpoint's own generator
(`assets/odeformer/weights/odeformer.pt`, `env.generator`), the operator sampling
probabilities are:

- unaries with nonzero probability: `id` 0.5000, `inv` 0.1667, `sin` 0.1667, `pow2` 0.1667
- binaries with nonzero probability: `add` 0.7500, `mul` 0.2500
- **probability exactly 0.0000**: `abs`, `sqrt`, `log`, `exp`, `arcsin`, `cos`, `arccos`,
  `tan`, `arctan`, `pow3`, `sub`, `div`

Mechanism (`third_party/odeformer/odeformer/envs/generators.py:369-400`):
`operators_downsample_ratio` is a `defaultdict(float)` populated only from
`params.operators_to_use` (`sin:1,inv:1,pow2:1,id:3,add:3,mul:1`); every operator absent
from that string is assigned sampling probability `0.0`.

Consequence: `div`, `sub`, `pow3`, `exp`, `log`, `sqrt`, `abs` and the inverse trig
operators are **present in the decoder vocabulary** (10293 words; operator-like tokens
include `div`, `pow`, `pow3`, `exp`, `log`, `sqrt`, `sub`, `abs`, `tanh`-family trig) but
were **never generated in training targets**. Vocabulary membership and learned prior mass
must therefore be treated as different quantities.

### F2 — Expressibility/tokenization is REFUTED as the GRN bottleneck (560/560)

All GPU_RUN5 GRN ground truths encode to valid ODEFormer token sequences and round-trip
exactly:

| corpus | separator-normalized exact round-trip |
|---|---|
| `phase2/train.json` | 240/240 |
| `phase2/validation.json` | 80/80 |
| `phase2/sealed_test.json` | 80/80 |
| `phase2/family_holdout_train.json` | 150/150 |
| `phase2/family_holdout_validation.json` | 10/10 |
| **total** | **560/560** |

`teacher_valid` is true for 560/560 including all of R03-R08 (the nontrivial Hill /
variable-denominator families). The apparent 25% raw round-trip rate is a cosmetic
artifact of how the multi-component separator `|` is joined (`...x_0|add,...` vs
`...x_0,|,add,...`); after normalizing the separator, agreement is exact, **including
constants** (the generator pre-quantized parameters to the 4-significant-figure
tokenizer grid, so `sampled_parameters` survive encoding losslessly).

Additionally, every GRN truth uses **only in-support operators** (`add`, `mul`, `inv`,
`pow2`, `id`, `INT-`); Hill exponents appear as `pow2` and `pow2∘pow2` (x^2, x^4).

### F3 — The GRN dissociation that drives this cycle

F1 and F2 together create a hard dissociation:

- the GRN corpus is **100% expressible** and **100% within the nonzero-probability operator support**,
- yet GPU_RUN5 measured `true_exponent_aware_skeleton_in_beam_rate = 0.0` over **960 cells / 47,987 candidates** — not once.

Therefore neither expressibility (F2) nor operator support (F1) can explain the GRN
generation failure. The surviving live explanations are **within-support prior mass**
(H-F1) and **search budget/diversity** (H-A2), and these two are not yet discriminated.

### F4 — ODEBench operator-support split (for contrast)

Of the 63 ODEBench systems (`third_party/odeformer/odeformer/odebench/strogatz_extended.json`),
a preliminary CPU classification gives **18 out-of-support** (requiring `exp`, `log`, `cos`,
`Abs`, or integer powers >= 3) and **45 in-support**. Since GPU_RUN4/5 found only ~6 systems
ever had truth in beam, roughly **39 of the 45 in-support systems also never reach truth** —
so out-of-support status is at most *sufficient, not necessary*, for generation failure.

---

## H-A — Generation bottleneck

**Status: SUPPORTED — and promoted to the binding constraint for GRN.**

The true structure is often absent from the candidate set, so no selection procedure can
recover it.

Supporting observations:
- GRN frozen validation: truth-in-beam `0.0` over 960 cells / 47,987 candidates.
- ODEBench exponent-aware truth-in-beam 4/252 = 1.59% [0.0062, 0.0401].
- ODEBench variable-denominator truth subset (56 cells): truth-in-beam **0/56**, selected exact **0/56** (Wilson upper 0.0642).
- 57 of 63 ODEBench systems never had truth in beam; canonical exact 0/252, symbolic CAS-equivalent 0/252.
- Unique skeletons per beam: 9.19 (ODEBench, beam 50), 9.28 (GRN) — beam-50 sampling at temperature 0.1 yields ~9 distinct structures.

Conflicting observations: none. Reconstruction R2 median 0.980 coexists with exact 0/252,
which is a fit/recovery decoupling (rule 03), not counter-evidence.

### H-A1 — Pretrained grammar/distribution underrepresents Hill/variable-denominator structures
**Status: SUPPORTED, mechanism identified (see F1); superseded in specificity by new branch H-F.**
Retained as the qualitative parent claim. F1 gives the exact mechanism (zero sampling
probability for `div`/`pow3`/`sub` and all transcendentals), but F3 shows this cannot be the
whole story for GRN.

### H-A2 — Beam/search budget is insufficient
**Status: OPEN — now one of only two live GRN explanations.**
Not discriminated from H-F1. Beam 50, `beam_type=sampling`, `beam_temperature=0.1`. A
temperature of 0.1 makes sampling near-deterministic, which is consistent with the observed
~9 unique skeletons per beam; low measured diversity is therefore expected under *either*
low prior mass or inadequate sampling, and does not by itself separate them.
Discriminating experiment: **H0001** (measure where truth sits in the model's own log-prob
distribution), then **H0003** conditionally.
Rejected if truth log-prob lies below the minimum log-prob of the model's own sampled
candidates (then no realistic budget increase can surface it).

### H-A3 — Tokenization/constant representation hinders recovery
**Status: REFUTED for the GRN corpus (F2, 560/560 exact round-trip incl. constants).**
Residual surviving form — **H-A3' encoding canonicalization**: a truth admits several
semantically equivalent token encodings (`div` vs `mul∘inv`, `pow3` vs `mul(x,pow2(x))`,
`sub` vs `add∘mul(-1)`, `pow2∘pow2` vs `pow(·,4)`). If prior-mass and truth-in-beam are
scored against only one canonical encoding, both are biased downward and the headline
negatives are partly measurement artifacts.
Status of H-A3': **OPEN**. Discriminating experiment: **H0006**.

### H-A4 — Dimensionality causes candidate coverage collapse
**Status: SUPPORTED descriptively, UNDECIDABLE causally.**
- 1D: recon R2 0.997, skeleton 17/92. 2D: 0.946, 2/112. 3D: valid only 25/40, R2>0.9 8/40, skeleton 0. 4D: 0.906, 0.
Confounded with target token length, component count, and the `|`-separated multi-component
format (`pad_to_max_dim=True`, `max_dimension=6`). Discriminating experiment: **H0008**.

---

## H-B — Selection bottleneck

**Status: REFUTED as the binding constraint for GRN. Residual second-order form survives.**

The true structure enters the candidate set but trajectory-local scoring picks something else.

Decisive conflicting observation: GRN truth-in-beam is `0.0` over 960 cells. When the truth
is never generated, **no selection rule can recover it**, so selection cannot be the binding
constraint on the GRN corpus. This closes H-B as a primary target and is recorded here so
the campaign does not re-litigate it.

Residual surviving form — **conditional selection quality given truth is present**, which is
real but bounded:
- ODEBench: truth in beam for 23/252 cells; selection picked it in 18, missed it in 5 → conditional selection accuracy 18/23 ≈ 78%.
- Mean selected TED 17.26 vs mean oracle-best-in-beam TED 14.31 → ~17% TED headroom.
So a perfect selector buys at most the oracle gap, which is small relative to the ~98%
generation gap. Selection work is therefore **DEFERRED** behind generation.

### H-B1 — Multiple initial conditions improve identifiability
**Status: SUPPORTED for generalization; NOT demonstrated for exact recovery.**
GPU_RUN5 P6 HIT: mean clustered difference in failure-aware generalization NRMSE
**-0.20278**, paired-t 95% CI **[-0.32323, -0.08233]**, 80 system clusters. This is the
campaign's one clean positive. Its *mechanism* is unresolved: it may act on selection only,
or it may also raise generation mass. Discriminating experiment: **H0005**.

### H-B2 — Structural regularization improves selection
**Status: OPEN, untested.** Deferred behind generation (bounded by the 18-vs-23 oracle gap).

### H-B3 — Out-of-trajectory evaluation improves selection
**Status: SUPPORTED** (largely the same evidence as H-B1).

---

## H-C — Adaptation bottleneck

**Status: SUPPORTED that a recovery/forgetting tradeoff exists; selective-FT superiority REFUTED; adaptation has NOT solved the target problem.**

GRN final test (opened once, 2026-09-01 — these seals are now SPENT):

| condition | exact-macro | faTED | gen NRMSE | note |
|---|---|---|---|---|
| frozen | 0.02396 | 0.47917 | 1.40764 | |
| official_continued_full | 0.05972 | 0.46147 | 1.44240 | |
| `grn_full` | **0.15972** | **0.36865** | 2.19822 | recon R2 collapsed to 0.222 |
| `grn_top3` | 0.10938 | 0.46111 | 2.29097 | |
| `grn_random3_0` | 0.10764 | 0.44223 | 1.26859 | |

Forgetting (ODEBench exact rate): frozen 0.08466 → `grn_top3` 0.06085 (-0.0238) →
`grn_full` 0.00794 (-0.0767).

**The decisive qualifier: exact component count for the nontrivial Hill /
variable-denominator components of R03-R08 is 0 in EVERY final condition.** All adaptation
gains came from the easy (R01/R02-like) components. Adaptation moved the aggregate metric
without touching the structures the campaign is about — and `grn_full` raised exact-macro
while its reconstruction R2 collapsed to 0.222, a fit/recovery decoupling in the opposite
direction (rule 03).

### H-C1 — Selective FT improves the Pareto tradeoff
**Status: PARTIALLY SUPPORTED (forgetting axis only); UNSUPPORTED on the recovery axis.**
`grn_top3` forgets less than `grn_full` (-0.0238 vs -0.0767) but recovers less
(0.10938 vs 0.15972). GPU_RUN5 P7 was a MISS. No dominance.

### H-C2 — Layer selection criterion is the main limitation
**Status: UNSUPPORTED.**
- GPU_RUN5: `grn_top3` 0.10938 vs `grn_random3_0` 0.10764 — random three layers ≈ causal top three.
- GPU_RUN4 selective FT on analysis-test: **every** FT condition was worse than frozen
  (frozen 1.674 best; full 1.797 worst), and the validation→test ranking inverted.
Layer *choice* explains very little of adaptation outcome. Do not spend further cycles
searching layer subsets for adaptation gain.

### H-C3 — Parameter-efficient adaptation outperforms literal layer selection
**Status: OPEN, untested.** Now the only feasible adaptation route under the ~6.5 GiB
ceiling. Candidate **H0009**, but explicitly deprioritized: it requires a NEW sealed test
set and it does not address the generation constraint that H-A/H-F identify as binding.

---

## H-D — Layer interpretation mismatch

**Status: STRONGLY SUPPORTED. Rule 04 is empirically vindicated, not merely a policy.**

Different "important layer" metrics answer different questions rather than noisily
estimating one latent ranking.

Supporting observations:
- **GPU_RUN5 P5 HIT**: Spearman between post-intervention ΔCE ranking and failure-aware ΔTED ranking = **0.008956**, two-sided **p = 0.97374**, n_layers = 16. Effectively zero association.
- **`decoder_11`**: caused faTED **+0.52692**, `component_valid_loss` 1.0, gen R2 loss 10.466 — while **`damage_CE` = -1.61708**, i.e. teacher-forcing CE *improved* while formulas were destroyed. A sign inversion, not merely a rank disagreement.
- GPU_RUN4: probe #1 `encoder_0` ranks 11th on causal ΔCE; causal #1 `encoder_3` sits at the bottom of the probe ranking. **No criterion pair shares a top-3 ordering.**
- Normalized single-layer contribution `C_l` disagrees with lexicographic IOLE: IOLE rank-1 `decoder_11` has `C_l` = -0.0378 (negative) while `decoder_10` = 0.3298 and `decoder_0` = -0.4157.
- Per-criterion top-3 (GPU_RUN5 main view): decoder next-token probe → `decoder_11`/`decoder_10`/`decoder_9`; gradient/sqrt(param) → `encoder_0`/`encoder_3`/`encoder_1`; formula-IOLE → `decoder_11`/`decoder_10`/`decoder_8`; causal mean-ablation (alpha=0.5) → `decoder_11`/`decoder_3`/`encoder_3`.
- Rank stability across 3 bundles: main Spearman 0.480 / Kendall 0.389; family-holdout 0.781 / 0.622 — so disagreement is not merely instability.

Known measurement limitations that must be respected by any successor experiment:
- **CKA has no discriminative power** in the encoder: all pairs 0.921-0.978 (GPU_RUN4); within-module mean off-diagonal encoder 0.94377 vs decoder 0.57762.
- **DecoderLens is fully saturated**: median normalized variable-aware TED = **1.0 at all 12 decoder layers** — zero depth signal. Do not reuse as an estimand without changing the readout.
- **`component_exact_loss` = 0.0 for all layers** in the causal intervention — a floor effect; it cannot discriminate anything.

### H-D1 probe = representational availability — SUPPORTED as a definition; kept separate.
### H-D2 ablation = causal necessity — SUPPORTED as a definition; kept separate.
### H-D3 IOLE = adaptation capacity — SUPPORTED as a definition; note GPU_RUN4 IOLE deltas were ~1e-3, near the noise floor.
### H-D4 — Their disagreement is predictable from task stage or token position
**Status: OPEN — and now the highest-value question on the layer side.**
The `decoder_11` sign inversion is the key clue: teacher-forcing CE is dominated *by token
count* by numeric mantissa/exponent tokens, whereas failure-aware TED is dominated by
operator/variable structure. If late decoder layers carry structure while numeric tokens are
carried elsewhere, the aggregate ρ = 0.008956 would be a **cancellation of opposing
components**, not an absence of structure. Discriminating experiment: **H0007**.
Rejected if per-token-category decomposition leaves both structural and numeric correlations
near zero — which would mean the divergence is not token-role-mediated and layer importance
is irreducibly multi-dimensional.

---

## H-E — Identifiability/data bottleneck

**Status: PARTIALLY SUPPORTED, but downstream-blocked by H-A; priority downgraded.**

Formula ambiguity arises from insufficient trajectory excitation rather than model weakness.

Supporting: H-B1/H-E1 multi-IC result (P6 HIT, above).

Blocking argument: with GRN truth-in-beam at `0.0` over 960 cells, richer or better-excited
data cannot produce the truth if the decoder will not emit the structure at all. H-E can only
become binding once H-F1/H-A2 are resolved. Its one live near-term use is *mechanistic*:
H0005 asks whether better conditioning raises the truth's log-prob, which is simultaneously
a test of H-E and a mechanism test for the P6 HIT.

### H-E1 — IC diversity matters more than sample density — SUPPORTED (P6), mechanism open (H0005).
### H-E2 — Intervention trajectories reduce equivalence classes — OPEN. `src/gpu_run5/interventions.py` exists.
### H-E3 — Noise/subsampling interacts nonlinearly with structural ambiguity — OPEN, DEFERRED.

---

## H-F — Pretraining support and representational reachability (NEW BRANCH)

**Status: ACTIVE — the load-bearing branch for C0001.**

Promoted out of H-A1 because F1/F2/F3 make it a first-class, mechanistically specified claim
that deserves its own subtree: the pretrained decoder's *learned distribution*, not the
grammar and not the tokenizer, is what excludes the target structures.

### H-F1 — Within-support prior mass is the binding constraint
**Status: OPEN — primary candidate for C0001.**
The truth is expressible (F2), uses only nonzero-probability operators (F2), yet has
near-zero probability under the pretrained decoder conditioned on the trajectory. Testable
directly by teacher-forced scoring of the stored ground-truth token sequences.
Experiment: **H0001**. Rejected if truth log-prob falls inside the range spanned by the
model's own sampled candidates.

### H-F2 — Out-of-support operators explain generation failure
**Status: REFUTED for GRN (F2/F3: GRN is 100% in-support yet 0/960). OPEN for ODEBench (F4: 18/63 out-of-support).**
Expected to be *sufficient but not necessary*: F4 implies ~39 of 45 in-support ODEBench
systems also fail. Experiment: **H0002**.

### H-F3 — Encoder input-conditioning failure
**Status: OPEN.** The encoder may not extract the structural evidence (Hill exponent,
variable-denominator presence) needed to raise truth's probability, in which case the
decoder prior is not the right locus. Experiment: **H0004**.
Note the encoder is only 4 layers of dim 256 and shows near-uniform CKA (0.921-0.978),
consistent with — but not evidence for — weak structural differentiation.

---

## H-G — Evaluator and measurement adequacy (NEW BRANCH)

**Status: ACTIVE — audit branch. Must be checked before any headline negative is promoted.**

Some campaign conclusions may be properties of the measurement rather than the model.

### H-G1 — Encoding canonicalization bias (= residual H-A3')
**Status: OPEN.** Experiment: **H0006**. If supported, prior-mass and truth-in-beam figures
(including 0/960) require restatement; if refuted, those negatives are hardened.

### H-G2 — Floor effects mask layer differences
**Status: SUPPORTED, already observed.** `component_exact_loss` = 0.0 for all 16 layers;
DecoderLens normalized TED = 1.0 at all 12 decoder layers; GPU_RUN4 variable F1 median 1.0
(no discriminative power); GPU_RUN4 IOLE deltas ~1e-3. Any successor layer experiment must
preregister an endpoint with demonstrated variance. H0007 is designed against this.

### H-G3 — Aggregate metrics decouple from target structures
**Status: SUPPORTED, already observed.** `grn_full` exact-macro rose to 0.15972 while recon
R2 collapsed to 0.222, and exact count for nontrivial Hill / variable-denominator components
was 0 in every condition. Component-stratified reporting is mandatory going forward.

---

## Sealed-resource ledger (constrains what may be proposed)

| resource | state |
|---|---|
| `gpu_run5.../phase2/sealed_test.json` (80 GRN) | **SPENT** (opened 2026-09-01) |
| `gpu_run5.../phase2/sealed_family_holdout_test.json` (20, subset of the 80) | **SPENT** |
| `gpu_run5.../phase4/sealed_official_test.json` (500 official formulas) | **UNSPENT — the only remaining seal** |
| ODEBench (63 systems) | not sealed; forbidden as adaptation/selection data; reference eval and forgetting secondary outcome only |

Any hypothesis whose primary endpoint is a GRN *final-test* comparison requires a **NEW
sealed test set** to be generated and sealed before methods are fixed. In C0001 this applies
to **H0009** only. All other C0001 candidates are validation-only or diagnostic and consume
no seal.

---

## Compute envelope for this campaign

Materially tighter than GPU_RUN4/5 (which used a 24 GB L4):
- GPU 0: RTX 2070, 7782 MiB total, ~888 MiB held by the live desktop session → **~6.5 GiB usable, shared with the desktop**
- GPU 1: GTX 1060 3 GB — forward-only small work
- 60 GiB RAM; 117 GiB free disk (`results/` already 25 GiB)
- env `lansr310`: Python 3.10.20, torch 2.5.1+cu124, sympy 1.13.1, numpy 2.2.6, scipy 1.15.3, pysr 1.5.10
- **Per-cycle ceiling: a few GPU-hours.** Prefer CPU-only or forward-pass-only designs.
Full fine-tuning of the 60,646,773-parameter model at GPU_RUN5 scale is no longer
affordable; this is an independent reason to prefer diagnosis over adaptation this cycle.

---

## Model identity (fixed for the campaign)

- `assets/odeformer/weights/odeformer.pt`, SHA256 `56754040be5aa92ed4767fc43ee2008faa293f87c12b643e66c7df3e1623a5e8`
- TRUE architecture from the state dict: **4 encoder layers dim 256, 12 decoder layers dim 512, 16 heads, 60,646,773 params** — NOT the paper's 4+16/86M
- 16 ranked layers: `encoder_0..3`, `decoder_0..11`
- decoder vocabulary 10293 words; `tied_output_embedding` true
- generation config: `operators_to_use="sin:1,inv:1,pow2:1,id:3,add:3,mul:1"`, `max_dimension=6`,
  `max_generated_output_len=200`, `max_int=10`, `float_precision=3`, `float_descriptor_length=3`,
  `use_two_hot=False`, `pad_to_max_dim=True`, beam_size 50, beam_type sampling, beam_temperature 0.1

**Unverified assumption flagged for Stage 2/3**: it is confirmed that the *checkpoint's
attached generator object* assigns zero probability to `div`/`sub`/`pow3`/transcendentals
(F1). It is **not** independently confirmed from the published training logs that this same
`operators_to_use` string governed the released model's actual pretraining run. If the
released weights were in fact trained under a wider operator distribution, H-F1's
interpretation changes (the tokens would be trained but disfavoured rather than untrained).
Literature/primary-source verification against the ODEFormer paper and official repository is
required before any claim about "never trained" is published. Until then the safe statement is
"zero probability under the checkpoint's own generator configuration".

---

## Cycle C0001 decision

Selected primary hypothesis: **H0001** (within-support prior mass / representational
reachability), with **H0002** (operator-support attribution) executed as a near-free CPU
companion in the same cycle. Runner-up **H0007** (token-role decomposition of the P5
CE-vs-formula divergence) is queued for C0002. Rationale, full field records, and the ranked
table are in `GPU_RUNclaude1/hypotheses/C0001_candidates.md`.
