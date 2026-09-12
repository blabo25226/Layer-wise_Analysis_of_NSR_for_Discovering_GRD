# C0001 — Literature and Novelty Evidence Record

- cycle: `C0001`
- stage: 2 (literature and novelty evidence)
- branch: `20260909_researce_GPU_RUNclaude1`
- date: 2026-09-09
- skill: `literature-evidence`
- rules applied: `.claude/rules/11-literature-and-novelty.md`, `.claude/rules/01-research-integrity.md`
- root reference index cross-checked: `/home/blabo/Layer-wise_Analysis_of_NSR_for_Discovering_GRD/source.md` (734 lines, 6 groups + Tier 1–4 priority list)

## Labelling conventions

- `SOURCE` — the statement is supported by the cited primary source (paper text, official repository, official dataset documentation, or the official released model artifact).
- `INFERENCE` — the statement is my reasoning over `SOURCE` facts. It is not asserted by any cited source.
- `unverified` — could not be confirmed from a primary source in this cycle.
- Verification method is stated per source. Where a fetch failed, that is recorded explicitly.

## Verification failures / caveats to record honestly

- `WebFetch` of `https://arxiv.org/html/2310.05573v2` returned HTTP 404. The ODEFormer text was instead obtained from the ICLR 2024 proceedings PDF (`https://proceedings.iclr.cc/paper_files/paper/2024/file/5ed5c3c846f684a54975ad7a2525199f-Paper-Conference.pdf`) and converted locally with `pdftotext -layout`. All ODEFormer quotations below come from that PDF.
- `WebFetch` of `https://openreview.net/forum?id=wENMvIsxNN` returned only an OpenReview bot-verification page; D-CODE metadata was confirmed instead via dblp (`https://dblp.org/rec/conf/iclr/QianKS22.html`) and the official repository README.
- `WebFetch` of `https://doi.org/10.1098/rspa.2020.0279` and `https://doi.org/10.1093/bioinformatics/btr373` returned cross-host redirects; the redirect targets were fetched separately (Royal Society / OUP), and the SINDy-PI abstract was additionally confirmed from `arXiv:2004.02322`.
- `arXiv:2206.08094` is **not** D-CODE (it is "Deep Neural Imputation", Talukder et al.). Any prior note associating that ID with D-CODE would be wrong; `source.md` does not make that error (it lists the OpenReview URL, which is correct).
- The abstract-only pages for NeSymReS, Kamienny et al., and TPSR do not contain the decoding-level detail asked for. Claims below about those three are therefore restricted to what the abstract/venue pages actually support, or marked `unverified`.

---

# Q1 — Generation support / reachability in transformer symbolic regression

## Q1.1 ODEFormer (the campaign's model)

- Title: **ODEFormer: Symbolic Regression of Dynamical Systems with Transformers**
- Authors: Stéphane d'Ascoli, Sören Becker, Philippe Schwaller, Alexander Mathis, Niki Kilbertus (author order as given on the arXiv listing page: d'Ascoli, Becker, Mathis, Schwaller, Kilbertus — `unverified` which ordering the camera-ready uses; do not cite an order without checking the PDF title page)
- Year / venue: 2023 preprint; **published at ICLR 2024** (`SOURCE`: ICLR 2024 proceedings page and PDF header "Published as a conference paper at ICLR 2024")
- arXiv: https://arxiv.org/abs/2310.05573 · DOI https://doi.org/10.48550/arXiv.2310.05573
- OpenReview: https://openreview.net/forum?id=TzoHLiGVMo
- ICLR proceedings: https://proceedings.iclr.cc/paper_files/paper/2024/hash/5ed5c3c846f684a54975ad7a2525199f-Abstract-Conference.html
- Official repository: https://github.com/sdascoli/odeformer
- `source.md` relationship: listed at **line 43** (arXiv PDF only), Tier 1 item #1 (line 683). **New here:** ICLR 2024 venue, OpenReview ID, official repository URL. Recommend adding all three to `source.md`.

### What ODEFormer establishes (`SOURCE`, ICLR 2024 PDF)

1. **Its unary operator set is closed and contains no general power operator.** §3, data generation step 6: unary operators are "sampled uniformly at random from {x ↦ sin(x), x ↦ x⁻¹, x ↦ x²}". Footnote 1: "Subtractions and divisions are included via multiplication with negative numbers and the unary operator x ↦ x⁻¹ respectively."
2. **Binary operators are only + and ×, with × the minority**: step 3, "a binary operator sampled from P(+) = 3/4 and P(×) = 1/4".
3. **The per-component unary budget is small.** §3: "In our experiments, we use D_max = 6, b_max = 5, u_max = 3, (c_min, c_max) = (0.05, 20)", where u is "the number of unary operators … sampled uniformly from [u_max]".
4. **Affine wrapping of unary arguments**: step 8, "prepend a coefficient to each term and wrap the argument of any unary operator in an affine transformation x ↦ a·x + b".
5. **ODEFormer deliberately does not measure symbolic recovery.** §5, Metrics: "When evaluating SR methods, the desired metric is whether the inferred ODE f̂ perfectly agrees symbolically with the ground truth expression f. However, such an evaluation is problematic …" They then adopt "% Accuracy (R² > 0.9)" for reconstruction and generalization. There is **no exact/skeleton recovery number anywhere in the paper**.
6. **They name generalization, not reconstruction, as the recovery proxy.** Appendix G: "Increasing the beam size improves reconstruction, but not generalization." and "This highlights the importance of using both metrics: the two are not necessarily correlated, and the latter is a much better proxy of symbolic recovery than the former."
7. **Decoding config matches the campaign's.** §4: "we use beam sampling … and select the candidate with highest reconstruction R² score. … we perform our experiments with a beam size of 50 and a temperature of 0.1."
8. **They document the beam-diversity failure mode.** Footnote 5: "Beam search tends to produce candidates which all have the same skeleton, and only differ by small variations of the constants, leading to a lack of diversity. Beam sampling ensures that randomness is added at each step of decoding leading to a more diverse set of candidate expressions."
9. **Stated limitations** (§ limitations): only first-order ODEs; "ODEFormer only works when all variables are observed"; struggles with chaotic systems; and "all existing methods for dynamical SR, including ours, perform inference based on a single observed trajectory. In our opinion, one of the most promising directions for future work is to enable inference from multiple solution trajectories of the same ODE. … However, initial experiments with various forms of logit aggregation in ODEFormer's decoder during inference did not yield convincing results."
10. **ODEFormer positions itself as a hypothesis generator**: "Methods like ODEFormer primarily serve as hypothesis generators, ultimately requiring further experimental verification".

### What ODEFormer does *not* establish

- It never asks whether the ground-truth skeleton is present in its own decoder distribution or beam. There is no reachability, coverage, oracle-candidate, or forced-decoding analysis in the paper. (`SOURCE`, by absence — I searched the full converted text for `pow`, `exponent`, `operator`, `recover`, `limitation`.)
- It reports no Hill-type, rational-with-variable-denominator, or gene-regulatory evaluation. (`SOURCE`, by absence: ODEBench is described as 63 ODEs of dimension 1–4 drawn from Strogatz-style physics/biology textbooks.)

### Direct verification against the released checkpoint (strongest evidence in this record)

Read from the campaign's own copy of the official released weights, `assets/odeformer/weights/odeformer.pt`, via `third_party/odeformer` (`ModelWrapper.params`):

```
operators_to_use        = sin:1,inv:1,pow2:1,id:3,add:3,mul:1
min_unary_ops_per_dim   = 0
max_unary_ops_per_dim   = 3
min_binary_ops_per_dim  = 1
max_binary_ops_per_dim  = 5
max_int                 = 10
max_dimension           = 6
max_unary_depth         = 7
operators_to_not_repeat = ""      (i.e. repeats such as pow2(pow2(x)) are allowed)
prob_prefactor          = 1
reduce_num_constants    = True
n_enc_layers = 4, n_dec_layers = 12, enc_emb_dim = 256, dec_emb_dim = 512
```

`SOURCE` (official artifact + official source tree). This independently confirms the campaign's stated config, confirms the paper's u_max = 3 in the *released* checkpoint (not merely the CLI default), and confirms 4-encoder/12-decoder with dims 256/512 — i.e. the released architecture, which `research_state.md` already flags as differing from the paper's description.

Relevant code paths (official repo, vendored at `third_party/odeformer/`):
- `odeformer/envs/environment.py:681` — `--operators_to_use` default `"sin:1,inv:1,pow2:1,id:3,add:3,mul:1"`
- `odeformer/envs/environment.py:837` — `--max_unary_ops_per_dim` default `3`
- `odeformer/envs/generators.py:584-592` — per-component draw `rng.randint(min_unary_ops_per_dim, max_unary_ops_per_dim + 1)` → the per-component unary count is drawn i.i.d. from {0,1,2,3}
- `odeformer/envs/generators.py:628-640` — `add_unaries` inserts candidate unary nodes and then **deletes** the excess so the final count equals the drawn budget; the index list is built from `self.unaries`, which **includes `id`**, so `id` consumes budget

### The support argument for Hill-type terms

`INFERENCE` (built only on the `SOURCE` facts above; not asserted by any cited paper):

Write a Hill-4 activation term in ODEFormer's prefix grammar. The only available unary operators are `sin`, `inv`, `pow2`, `id`; there is no learnable-exponent `pow`. Therefore x⁴ = `pow2(pow2(x))`, costing 2 unary nodes.

- Multiplicative form `α·x⁴/(K⁴+x⁴)` = `mul(α, mul(pow2(pow2(x)), inv(add(K⁴, pow2(pow2(x))))))` requires **5 non-identity unary nodes** (2 + 2 + 1). Since the per-component unary budget is at most 3, this form has **exactly zero probability** under the pretraining generator.
- Repression form `α·K⁴/(K⁴+x⁴)` = `mul(α', inv(add(b, pow2(pow2(x)))))` requires **3** unary nodes (`pow2`, `pow2`, `inv`) — i.e. it sits **exactly at the cap** and is inside the support, though in the extreme tail.
- **The algebraically equivalent additive decomposition of the activation form is also inside the support**: `α·x⁴/(K⁴+x⁴) = α − α·K⁴/(K⁴+x⁴)` = `add(α, mul(−αK⁴, inv(add(K⁴, pow2(pow2(x))))))`, again **3** unary nodes. With `prob_prefactor = 1` and the step-8 affine wrap absorbing K⁴ into `a·x+b`, this is a form the generator can produce.
- Hill-2 activation `α·x²/(K²+x²)` needs `pow2`, `pow2`, `inv` = **3** — at the cap.
- Because `id` carries weight 3 of 6 in the unary distribution and consumes one budget slot each time it is drawn, the *expected* number of non-identity unary operators per component at the cap is ≈ 1.5. So even the 3-unary Hill forms are deep in the tail of the pretraining prior, not merely "allowed".

Two consequences that matter for C0001 design:

- **(a)** The campaign's observed 0/960 skeleton hit rate on synthetic Hill-type GRN cells is *fully consistent with, and partly explained by, a hard support constraint* — not only a learned-bias or search-budget constraint. Increasing beam size or temperature cannot move probability mass onto a sequence the training distribution assigned probability zero, except through generalisation beyond the training support.
- **(b)** **Exact-recovery scoring is form-dependent, and one equivalent form is inside the support while another is not.** If the campaign's "true exponent-aware skeleton" target is the multiplicative form, then 0/960 may be partly a *scoring* artifact: the model could conceivably emit the additive-decomposed equivalent, which a form-sensitive matcher would reject. This is a cheap, high-information check and should be resolved before spending GPU compute on generation-side remedies. (`.claude/rules/03-symbolic-regression-contract.md` requires preserving raw + simplified equation and variable mapping, which is exactly what makes this check possible.)

## Q1.2 NeSymReS

- Title: **Neural Symbolic Regression that Scales**; Biggio, Bendinelli, Neitz, Lucchi, Parascandolo; ICML 2021 (PMLR v139)
- https://arxiv.org/abs/2106.06427 · https://proceedings.mlr.press/v139/biggio21a/biggio21a.pdf
- Official repository: https://github.com/SymposiumOrganization/NeuralSymbolicRegressionThatScales
- `source.md`: **lines 83 and 86**. Already listed; no correction needed.
- `SOURCE`: the paper's stated pipeline is a set-encoder over (X,y) plus an autoregressive decoder producing a distribution over skeletons, with beam search yielding candidates and BFGS fitting constants; final selection is by fit loss among beam candidates.
- `unverified`: whether the paper itself reports any oracle/coverage metric (fraction of problems where *some* beam candidate is the correct skeleton). The abstract page does not support that claim and I did not confirm it in the full text this cycle. Do **not** cite NeSymReS for a coverage metric without checking §Results and the supplement.

## Q1.3 End-to-end symbolic regression with transformers (Kamienny et al.)

- Title: **End-to-end symbolic regression with transformers**; Pierre-Alexandre Kamienny, Stéphane d'Ascoli, Guillaume Lample, François Charton; NeurIPS 2022
- https://arxiv.org/abs/2204.10532 · https://papers.neurips.cc/paper_files/paper/2022/file/42eb37cdbefd7abae0835f4b67548c39-Paper-Conference.pdf
- `source.md`: **line 578** ("ESRT"). Already listed; **new here:** NeurIPS 2022 venue + proceedings URL.
- `SOURCE` (abstract): they predict "the full mathematical expression, constants included", rather than skeleton-then-fit, and report this "yields better results, sometimes even without the refinement step"; performance "approaches … state-of-the-art genetic programming" on SRBench with far faster inference.
- `SOURCE` (by absence in the abstract): no claim that the model's distribution provably contains the target expression, and no reachability diagnostic. `unverified` for the full text.

## Q1.4 TPSR

- Title: **Transformer-based Planning for Symbolic Regression**; Parshin Shojaee, Kazem Meidani, Amir Barati Farimani, Chandan K. Reddy; NeurIPS 2023
- https://arxiv.org/abs/2303.06833 · official repo https://github.com/deep-symbolic-mathematics/tpsr
- `source.md`: **lines 546 and 548**, Tier 3 #8. Already listed.
- `SOURCE` (abstract): TPSR wraps MCTS around the transformer's next-token prior so that non-differentiable feedback (fitting accuracy, complexity) steers decoding, versus "conventional decoding strategies" that rely only on the pretraining objective. Claimed gains in fitting-complexity trade-off and extrapolation.
- **Key limitation for this campaign** (`INFERENCE`): TPSR reweights *search* over the same token vocabulary and the same learned prior. It changes which sequences get explored; it does not add a `pow` operator or extend the support. It is therefore a candidate remedy for a search-budget bottleneck but not for a support bottleneck.

## Q1.5 CTC_NSR — the closest primary source to the campaign's bottleneck

- Title: **Can Test-time Computation Mitigate Reproduction Bias in Neural Symbolic Regression?**
- Authors: Shun Sato, Issei Sato
- Year/status: arXiv preprint, submitted 2025-05-28, revised 2026-02-02. Peer-review status `unverified`.
- https://arxiv.org/abs/2505.22081 · full text read at https://arxiv.org/html/2505.22081
- `source.md`: **line 97**, Tier 1 #9. Already listed and correctly flagged there as directly related to the generation bottleneck.
- `SOURCE`, definition: "If strip(e) ∈ E_templ, we say s is a reproduction of expressions seen during training" — i.e. reproduction bias is measured by whether the generated expression's constant-stripped tree structure already occurs in the training set.
- `SOURCE`, magnitude: in a simplified NeSymReS setting with 100K training expressions, **over 97%** of generated expressions were training copies after 1000 epochs; in a practical `transformer4sr` setting with 1.5M expressions, **<12%** of expressions were novel counting constant positions and **<6%** had novel tree structures. Scaling training data showed diminishing returns.
- `SOURCE`, theory: "Transformers cannot compositionally generate tokens while validating numerical consistency."
- `SOURCE`, remedies tested: **larger beam (b = 150) "provided no additional information"**; MCTS/TPSR generated novel expressions but sometimes reduced accuracy; their proposed NSR-gvs supplies verified subtrees as prompts at inference.
- `SOURCE`, by absence: **"The paper does not explicitly report computing log-probabilities of ground-truth expressions or whether correct expressions appear in the model's distribution."** They measure novelty by *set membership in the training corpus*, not by *probability under the model*.
- Relevance: this is the strongest independent confirmation that the campaign's bottleneck class (structures never generated, not merely never selected) is real and general across neural SR, and that *the two obvious cheap remedies the campaign might reach for — bigger beam, MCTS — are already documented as insufficient*.
- Limitation: it does not study ODEFormer, ODEs, rational/Hill structures, or GRNs, and it does not use the log-probability diagnostic.

## Q1.6 GODE

- Title: **Grammar-based Ordinary Differential Equation Discovery**
- Authors: Karin L. Yu, Eleni Chatzi, Georgios Kissas
- arXiv: https://arxiv.org/abs/2504.02630 (2025-04-03) · DOI https://doi.org/10.48550/arXiv.2504.02630
- Published: *Mechanical Systems and Signal Processing*, 2025 — https://doi.org/10.1016/j.ymssp.2025.113395 (Elsevier PII S0888327025010969). The DOI resolves; I did **not** complete the Elsevier landing-page fetch, so volume/pages are `unverified`.
- Official repository: **https://github.com/ETH-IBK-SMECH/GODE** (`SOURCE`: README states it contains the code for the paper by K. Yu, E. Chatzi and G. Kissas, MSSP 2025).
- `source.md`: **lines 109 and 112**, Tier 1 #8. Already listed. **New here:** the official repository URL — recommend adding.
- `SOURCE` (abstract + README): GODE couples formal grammars with dimensionality reduction and stochastic search; "Grammars allow us to seed domain knowledge and structure in both the generation of large pretrained libraries as well as inference processes, effectively reducing the exploration space." Architecture is a **Grammar Variational Autoencoder (GVAE)**; the repo references `GODE/parser/cfg_parser.py`, indicating **context-free grammars** (`SOURCE`, code path; the README does not name the formalism in prose).
- `SOURCE` (claim): GODE reportedly outperforms transformer-based models in sample and parameter efficiency and produces "more accurate and parsimonious ODE expressions" than genetic programming and grammar-based alternatives, validated on four benchmarks (1-D explicit ODEs; linear/nonlinear ODEs; structural-dynamics nonlinear ODEs; Silverbox).
- **What it establishes vs conjectures** (`INFERENCE`): it establishes that a grammar-seeded generative search can beat a pretrained transformer on *structural-dynamics* ODE benchmarks. It does **not** establish anything about Hill-type / gene-regulatory rational dynamics, and it does **not** demonstrate grammar constraints applied *to a pretrained SR transformer's decoder* — GODE replaces the transformer rather than constraining it. The transfer of GODE's idea to constrained decoding of ODEFormer is a proposal, not a demonstrated result.

---

# Q2 — Is teacher-forced scoring of the ground-truth expression an established diagnostic?

## Q2.1 The closest primary source: Stahlberg & Byrne (NMT)

- Title: **On NMT Search Errors and Model Errors: Cat Got Your Tongue?**
- Authors: Felix Stahlberg, Bill Byrne
- Year/venue: 2019, EMNLP-IJCNLP, pages 3356–3362
- ACL Anthology: https://aclanthology.org/D19-1331/ · **DOI 10.18653/v1/D19-1331** · arXiv preprint: https://arxiv.org/abs/1908.10090 (CoRR abs/1908.10090)
- Verified by fetching the ACL Anthology page. `SOURCE`.
- `source.md`: **not listed**. **NEW SOURCE** — recommend adding to group 6 (auxiliary/foundational) or a new decoding subsection.
- `SOURCE`: they "present an exact inference procedure for neural sequence models based on a combination of beam search and depth-first search", use it to find global-best model scores over the full WMT15 En-De test set, and thereby separate **search errors** ("beam search fails to find these global best model scores in most cases, even with a very large beam size of 100") from **model errors** ("for more than 50% of the sentences, the model in fact assigns its global best score to the empty translation").
- **Why this is the right precedent** (`INFERENCE`): it is the canonical primary source establishing that (i) *whether the decoder can find a sequence* and (ii) *what score the model assigns to that sequence* are different questions requiring different measurements, and that answering (ii) can overturn conclusions drawn from (i). The campaign's proposed diagnostic — compute the model's log-probability of the ground-truth token sequence under forced decoding — is the same *conceptual move* (score a specific hypothesis directly rather than infer its status from search output), applied with a cheaper instrument (a single forced-decoding pass on a known target) rather than exact global inference.
- **Where the analogy breaks** (`INFERENCE`): Stahlberg & Byrne scored the *empty string and global optimum*; the campaign scores a *known ground truth*. Their diagnostic bounds the model's own argmax; the campaign's bounds the ground truth's rank/probability. A high GT log-probability with a 0/960 beam hit rate would be a **search error**; a vanishing GT log-probability would be a **model error** (and, per Q1's support argument, possibly a **support error**, a third category neither source names).

## Q2.2 Adjacent decoding literature

- **Diverse Beam Search: Decoding Diverse Solutions from Neural Sequence Models** — Ashwin K. Vijayakumar, Michael Cogswell, Ramprasath R. Selvaraju, Qing Sun, Stefan Lee, David Crandall, Dhruv Batra; AAAI 2018; https://arxiv.org/abs/1610.02424 · https://doi.org/10.48550/arXiv.1610.02424. `SOURCE`: beam search "explores the search space in a greedy left-right fashion retaining only the top-B candidates - resulting in sequences that differ only slightly from each other", and "producing lists of nearly identical sequences is not only computationally wasteful but also typically fails to capture the inherent ambiguity of complex AI tasks". `source.md`: **not listed** — NEW.
- I did **not** find a primary source that formalises the beam-search curse specifically for equation/skeleton search. `unverified`.

## Q2.3 Is the diagnostic already used in SR?

Searches run (WebSearch): forced-decoding/teacher-forced log-probability of ground-truth expressions in SR; oracle/coverage of the correct skeleton in a beam; pass@k-style upper bounds for neural SR; "probability of the ground truth program" in program synthesis.

- `SOURCE`: teacher forcing with cross-entropy against ground-truth expression tokens is the **standard training objective** for every transformer SR model in this literature (NeSymReS, Kamienny et al., ODEFormer, transformer4sr). That is not in dispute.
- `SOURCE` (by absence, over the searches above): I found **no** primary SR/ODE-discovery source that uses forced-decoding log-probability (or rank) of the ground-truth expression **at evaluation time as a reachability/coverage diagnostic** separating "the target has negligible model probability" from "the target has non-negligible probability but the search never emits it".
- Nearest SR-side moves, all different in kind:
  - CTC_NSR (Q1.5) measures novelty as *training-set membership*, explicitly not as model probability (`SOURCE`).
  - CNSR/NSRwH (Q4.3) *conditions on* ground-truth-derived structural hypotheses to improve generation; it does not *score* the ground truth to diagnose reachability (`SOURCE`, abstract).
  - CTC_NSR's NSR-gvs likewise extracts subtrees from ground-truth expressions and feeds them as prompts (`SOURCE`) — again an intervention, not a diagnostic.
- Caveat on the absence claim: an absence over ~6 targeted web searches is weak evidence. It is **not** proof of novelty, and `.claude/rules/11` forbids inferring novelty from local absence. Treated accordingly below.

**Q2 label: `adjacent`.** The conceptual instrument is established in a neighbouring field with a clean primary source (Stahlberg & Byrne 2019); the constituent machinery (teacher-forced CE over GT expression tokens) is standard inside SR itself; but its *use as an evaluation-time reachability diagnostic for SR skeleton recovery* is not documented in any primary source I could verify. Reporting it as `plausibly_novel` would overstate the search; reporting it as `known` would be false.

---

# Q3 — Hill functions, rational and saturating structures in equation discovery

## Q3.1 implicit-SINDy

- Title: **Inferring biological networks by sparse identification of nonlinear dynamics**
- Authors: Niall M. Mangan, Steven L. Brunton, Joshua L. Proctor, J. Nathan Kutz
- Year/venue: 2016; *IEEE Transactions on Molecular, Biological and Multi-Scale Communications*
- https://arxiv.org/abs/1605.08368 · published DOI https://doi.org/10.1109/TMBMC.2016.2633265
- `source.md`: **lines 166 and 169**, Tier 1 #6. Already listed.
- `SOURCE` (abstract): they "cast dynamical systems with rational nonlinearities in an implicit form, where the equations may be identified in the null-space of a library of mixed nonlinearities including the state and derivative terms", with ℓ1 sparsity. Validated on **Michaelis–Menten enzyme kinetics, a regulatory network for bacterial competence, and a yeast glycolysis metabolic network**.
- `SOURCE`: the abstract does not state noise limitations; the noise-sensitivity finding comes from SINDy-PI (next).

## Q3.2 SINDy-PI

- Title: **SINDy-PI: a robust algorithm for parallel implicit sparse identification of nonlinear dynamics**
- Authors: Kadierdan Kaheman, J. Nathan Kutz, Steven L. Brunton
- Year/venue: 2020; *Proceedings of the Royal Society A*
- DOI https://doi.org/10.1098/rspa.2020.0279 · arXiv https://arxiv.org/abs/2004.02322 · official code https://github.com/dynamicslab/SINDy-PI
- `source.md`: **lines 180 and 183**, Tier 1 #7. Already listed.
- `SOURCE` (abstract, verbatim key clauses): "Although extensions have been developed to identify implicit dynamics, or dynamics described by rational functions, **these extensions are extremely sensitive to noise**." SINDy-PI is "several orders of magnitude more noise robust than previous approaches" and identifies "a class of complex ODE and PDE dynamics that were previously unattainable with SINDy, including for the double pendulum dynamics and the Belousov–Zhabotinsky (BZ) reaction".
- `SOURCE` (by absence in the abstract): Hill functions and gene regulation are **not** mentioned; the demonstrated systems are mechanical/chemical. So SINDy-PI's documented remedy is for *implicit/rational* structure generally, and its GRN applicability is inherited from implicit-SINDy rather than shown by SINDy-PI itself.

### What is established about rational/Hill discovery difficulty

`SOURCE` synthesis across Q3.1–Q3.2 and the two `source.md` items below:
- Rational dynamics require either an implicit/null-space formulation or an explicit rational ansatz; naive sparse regression in an explicit polynomial library cannot express `x^n/(K^n + x^n)`.
- The null-space route is the documented working remedy for the *structure*, and its documented failure mode is *noise sensitivity*, fixed by SINDy-PI's parallel implicit reformulation with principled model selection.
- Already in `source.md` and consistent with the above: **Rational Dynamics SVD** (https://doi.org/10.1049/syb2.70068, open access https://pmc.ncbi.nlm.nih.gov/articles/PMC13175932/, `source.md` lines 198–201), which per `source.md` uses mixed state/derivative libraries and an implicit SVD framework and is validated on Michaelis–Menten, *Bacillus subtilis* competence, penicillin production and yeast glycolysis. I did **not** independently fetch this DOI this cycle → its details are `unverified` here; `source.md` is the only warrant.

## Q3.3 D-CODE

- Title: **D-CODE: Discovering Closed-form ODEs from Observed Trajectories**
- Authors: Zhaozhi Qian, Krzysztof Kacprzyk, Mihaela van der Schaar (`SOURCE`: dblp https://dblp.org/rec/conf/iclr/QianKS22.html and repo README BibTeX)
- Year/venue: ICLR 2022 (Spotlight — https://iclr.cc/virtual/2022/spotlight/7158)
- OpenReview: https://openreview.net/forum?id=wENMvIsxNN · PDF https://openreview.net/pdf?id=wENMvIsxNN
- Official repository: https://github.com/vanderschaarlab/D-CODE-ICLR-2022 (lab org). `source.md` line 215 gives https://github.com/ZhaozhiQIAN/D-CODE-ICLR-2022, which also resolves and whose README carries the paper BibTeX. Both are legitimate; the `vanderschaarlab` org URL is the one the lab advertises. **Recommend recording both.**
- `source.md`: **lines 212 and 215**, Tier 2 #10. Already listed.
- `SOURCE`: D-CODE "uses a novel objective function based on the variational formulation of ODEs to bypass the unobserved time derivative", and the objective is proved to be a valid proxy for the estimation error of the true unknown ODE.
- `unverified`: whether D-CODE's search space covers rational/Hill terms, and which systems it is evaluated on. The OpenReview fetch was blocked by bot verification; I refuse to state evaluation details I did not read.

## Q3.4 Learnable integer exponents / explicit denominator handling in SR

- Searches found no primary transformer-SR paper that adds a learnable-exponent `pow` operator with integer exponents to a pretrained SR decoder. `unverified`.
- Adjacent, verified: **Grammar-based ODE Discovery** (Q1.6) can encode structure as grammar productions, and **CNSR/NSRwH** (Q4.3) conditions on structural hypotheses — but neither adds an exponent operator.
- Adjacent, low-confidence: WebSearch surfaced *Complex Equation Learner (CEQL)*, https://arxiv.org/html/2605.03841v1, on gradient-based SR failing "for operators that introduce singularities or domain constraints, including division, logarithms, and square roots", and *NOMTO*, https://arxiv.org/html/2501.08086v1, on EQL/KAN struggling with singular operations such as division. Both are 2025–2026 preprints I read only as search-result excerpts; I did **not** fetch either landing page. Treat both as `unverified` leads, not citable claims. `source.md`: neither is listed.
- **Documented remedy summary** (`SOURCE`, restrained): the only *demonstrated working* remedies for rational structure in the primary literature I verified are (i) implicit/null-space formulations with the state-and-derivative mixed library (implicit-SINDy), (ii) their noise-robust reformulation (SINDy-PI), and (iii) derivative-free variational objectives (D-CODE, for the derivative-estimation half of the problem, coverage of rational terms `unverified`). Nothing I verified demonstrates a *neural, pretrained, transformer* SR model recovering Hill-type variable denominators.

---

# Q4 — Constrained / grammar-guided decoding and beam diversity as remedies

## Q4.1 Grammar-constrained decoding distorts the model distribution — the essential caveat

- Title: **Grammar-Aligned Decoding**
- Authors: Kanghee Park, Jiayu Wang, Taylor Berg-Kirkpatrick, Nadia Polikarpova, Loris D'Antoni
- Year/venue: **NeurIPS 2024**
- https://proceedings.neurips.cc/paper_files/paper/2024/file/2bdc2267c3d7d01523e2e17ac0a754f3-Paper-Conference.pdf (fetched; parsed locally with `pdftotext`)
- `source.md`: **not listed**. **NEW SOURCE** — strongly recommend adding; it directly bears on the campaign's most likely next intervention.
- `SOURCE` (abstract, verbatim): "we demonstrate that GCD techniques (and in general constrained decoding techniques) **can distort the LLM's distribution**, leading to outputs that are grammatical but appear with likelihoods that are not proportional to the ones given by the LLM, and so ultimately are low-quality. We call the problem of aligning sampling with a grammar constraint, grammar-aligned decoding (GAD), and propose adaptive sampling with approximate expected futures (ASAp) …" They also note (intro) "structured decoding distorts the LLM's learned language distribution", that exact GAD is intractable in general, and that ASAp converges to the LLM's distribution conditioned on the grammar as more samples are observed.
- **Why this matters for C0001** (`INFERENCE`): if the campaign masks ODEFormer's decoder to enforce a Hill-shaped grammar, greedy GCD will produce grammatical Hill candidates whose likelihood ordering no longer reflects the model, so *any* improvement in structural hit rate may come with degraded constant quality and degraded candidate ranking. The correct comparison is constrained decoding *against* an ASAp-style distribution-preserving variant, or at minimum a preregistered check that reconstruction/generalisation NRMSE does not collapse.

## Q4.2 Grammar/structure constraints demonstrably raising exact recovery in SR

- **Symmetry-Constrained Language-Guided Program Synthesis for Discovering Governing Equations from Noisy and Partial Observations** (SymLang) — Mirza Samad Ahmed Baig, Syeda Anshrah Gillani; arXiv preprint, submitted 2026-03-06; https://arxiv.org/abs/2603.06869. `source.md`: **not listed** — NEW.
  - `SOURCE` (abstract): "typed symmetry-constrained grammars that encode dimensional analysis, group-theoretic invariance, and parity constraints as hard production rules", eliminating ~71.3% of candidate expression trees before fitting; a fine-tuned 7B LM proposer; reported "exact structural recovery rate of 83.7% under 10% observational noise — a 22.4 percentage-point improvement" across 133 dynamical systems.
  - **Reliability caveat, stated plainly:** this is a two-author 2026 arXiv preprint with unusually strong headline numbers, no venue, and no code repository URL that I could locate (the abstract claims the framework is "fully open-source and reproducible" but the landing page shows no link). The ablation figure of 83.7% → 66.2% for replacing the symmetry grammar with an unconstrained CFG appeared **only in a WebSearch snippet** and I could **not** confirm it on the paper landing page. **That specific −17.5-point ablation number is `unverified` and must not be cited as established.** Treat SymLang as a directionally relevant lead, not as evidence.
- **GODE** (Q1.6) is the better-warranted grammar result: peer-reviewed in MSSP, with an official repository — but its grammar is used to build a GVAE search, not to constrain a pretrained SR transformer's decoder.

## Q4.3 Controllable neural SR

- Title: **Controllable Neural Symbolic Regression**
- Authors: Tommaso Bendinelli, Luca Biggio, Pierre-Alexandre Kamienny
- Year/venue: 2023; **ICML 2023 (PMLR v202)** — https://proceedings.mlr.press/v202/bendinelli23a/bendinelli23a.pdf · arXiv https://arxiv.org/abs/2304.10336 · OpenReview https://openreview.net/pdf?id=EiHX7MfAG0
- `source.md`: **line 589**, Tier 4 #7. Already listed (arXiv only). **New here:** ICML 2023 / PMLR v202 venue. Given C0001's direction, this deserves promotion out of Tier 4.
- `SOURCE` (abstract): NSRwH incorporates "user-defined prior knowledge" and "assumptions about the expected structure" as conditioning input; the conditioned variant "outperforms its unconditioned counterparts in terms of accuracy while also providing control over the predicted expression structure".
- **Demonstrated vs proposed** (`INFERENCE`): NSRwH demonstrates that *conditioning a pretrained-style SR transformer on structural hypotheses improves accuracy and controllability* — but the model is **trained with that conditioning channel**. Applying structural control to ODEFormer, which has no hypothesis-conditioning input, would require either fine-tuning to add the channel or hard decoder masking (which lands you in Q4.1's distortion problem). No verified source demonstrates the latter for SR.

## Q4.4 Beam diversity as a remedy

- `SOURCE` (ODEFormer footnote 5): the authors already replaced beam search with **beam sampling** precisely because beam search "tends to produce candidates which all have the same skeleton". So the campaign's checkpoint is already using the diversity fix that ODEFormer's authors deemed necessary.
- `SOURCE` (ODEFormer Appendix G): "Increasing the beam size improves reconstruction, but not generalization" — with generalisation described as "a much better proxy of symbolic recovery".
- `SOURCE` (CTC_NSR): beam size 150 "provided no additional information".
- `SOURCE` (Vijayakumar et al. 2018): standard beam search is documented to under-diversify; DBS provides a diversity-augmented objective, demonstrated on captioning/MT/VQG — **not** on SR or equation discovery.
- **Combined verdict** (`INFERENCE`): the literature already answers "will more beam or more diversity alone create the missing Hill structure?" with **no**, from two independent primary sources plus the campaign's own 0/960. Spending C0001 GPU compute on beam-size or temperature sweeps would be re-answering a question the literature and the prior run have both closed.

---

# Q5 — Layer-wise analysis estimand divergence

## Q5.1 The closest SR-specific source: TSRM

- Title: **Explaining the Explainer: Understanding the Inner Workings of Transformer-based Symbolic Regression Models**
- Authors: Arco van Breda, Erman Acar
- Year/status: arXiv preprint, submitted 2026-02-03 (cs.LG). Peer-review status `unverified`.
- https://arxiv.org/abs/2602.03506 · full text read at https://arxiv.org/html/2602.03506v1
- `source.md`: **line 293**, Tier 1 #2. Already listed; author names are **new here**.
- `SOURCE`: the analysed model is **NeSymReS**. They introduce PATCHES for circuit discovery and compare Direct Logit Attribution, mean patching with performance-based (functional) evaluation, and resample patching with functional and logit metrics; they isolate 28 circuits.
- `SOURCE`, the central estimand-divergence finding: "Direct Logit Attribution struggles to produce a faithful circuit, requiring almost all components to meet model and functional faithfulness, creating non-minimal circuits", and "we see no score improvement for the first 50 components" when reintroducing components ranked highly by logit importance. DLA needed ~95% of components versus 40–78% for PATCHES, with worse circuit quality. Conclusion: mean patching with performance-based evaluation "most reliably isolates functionally correct circuits", while other approaches "primarily capture correlational rather than causal features".
- `SOURCE`, probe caveat: "high probing performance does not necessarily imply causal relevance".
- **Scope limits** (`SOURCE`): the analysis is **component-level (attention heads and MLPs), not layer-wise**, and the "functional" criterion is numerical/behavioural correctness of the SR model, not *symbolic structural* correctness scored by an edit distance.

## Q5.2 A loss-based layer ranking failing to predict task outcomes — explicit primary evidence

- Title: **LLM Pruning and Distillation in Practice: The Minitron Approach**
- Year/status: NVIDIA, 2024, arXiv preprint. Author list `unverified` (I read the HTML body, not the full author block).
- https://arxiv.org/abs/2408.11796 · text read at https://arxiv.org/html/2408.11796v3
- `source.md`: **not listed**. **NEW SOURCE** — recommend adding.
- `SOURCE` (§4 Analysis, "Depth Pruning Metrics"), verbatim: **"LM validation loss/PPL-based layer importance fails to produce the most accurate pruned model(s) on downstream tasks"**, and "We do not consider the Block Importance (BI) metric as it was recently shown to under-perform the validation loss/PPL metric". They further report that non-contiguous layer removal achieved better validation loss but that this advantage did not transfer to downstream evaluation, leading them to adopt contiguous dropping.
- **Assessment** (`INFERENCE`): this is the closest thing to a primary source already demonstrating the *general* claim behind the campaign's Q5 result — that a **loss/cross-entropy-based layer-importance ranking does not predict a task-outcome-based layer ranking**. It is demonstrated in LLM depth pruning, with a task-accuracy criterion, and without any correlation statistic. It does **not** cover symbolic/structural damage, does not report an orthogonality test, and does not report a layer that *improves* loss while destroying task correctness.

## Q5.3 Metric choice changes localisation conclusions

- **Towards Best Practices of Activation Patching in Language Models: Metrics and Methods** — Fred Zhang, Neel Nanda; **ICLR 2024**; https://arxiv.org/abs/2309.16042. `source.md` **line 377** (BPAP), Tier 2 #5. `SOURCE` (abstract): "we systematically examine the impact of methodological details in activation patching, including evaluation metrics and corruption methods. In several settings of localization and circuit discovery in language models, **we find that varying these hyperparameters could lead to disparate interpretability results**." **New here:** ICLR 2024 venue and author names.
- **How to use and interpret activation patching** — Stefan Heimersheim, Neel Nanda; 2024, arXiv:2404.15255 tutorial (13 pp.); https://arxiv.org/abs/2404.15255. `source.md` **line 387** (HUIAP). `SOURCE` (abstract): they focus "on what evidence patching experiments provide about circuits, and on the choice of metric and associated pitfalls". Specific metric recommendations are `unverified` (abstract only).
- **Causal Abstraction: A Theoretical Foundation for Mechanistic Interpretability** — Atticus Geiger, Duligur Ibeling, Amir Zur, Maheep Chaudhary, Sonakshi Chauhan, Jing Huang, Aryaman Arora, Zhengxuan Wu, Noah Goodman, Christopher Potts, Thomas Icard; **JMLR 26(83):1–64, 2025**; https://www.jmlr.org/papers/v26/23-0058.html · arXiv https://arxiv.org/abs/2301.04709. `source.md` **lines 398 and 401**, Tier 2 #6. `SOURCE`: unifies "activation and path patching, causal mediation analysis, causal scrubbing, causal tracing, circuit analysis, concept erasure, sparse autoencoders, differential binary masking, distributed alignment search, and steering" under causal abstraction. `SOURCE` (by absence, from the abstract): it does **not** explicitly frame different methods as targeting different *estimands* — that framing, which `.claude/rules/04-layer-analysis-contract.md` adopts, is the campaign's own and is `unverified` as a literature claim from this paper's abstract alone.
- **Designing and Interpreting Probes with Control Tasks** — John Hewitt, Percy Liang; **EMNLP 2019**; https://arxiv.org/abs/1909.03368. `source.md` **line 369** (DIP), Tier 2 #4. `SOURCE` (abstract), and this is a **documented layer-ranking reversal under a criterion change**: "while probes on the first layer of ELMo yield slightly better part-of-speech tagging accuracy than the second, probes on the second layer are substantially more selective, which raises the question of which layer better represents parts-of-speech." Also defines control tasks and selectivity, and finds popular ELMo probes "are not selective".
- **On the Effect of Dropping Layers of Pre-trained Transformer Models** — Hassan Sajjad, Fahim Dalvi, Nadir Durrani, Preslav Nakov; arXiv 2020, published in *Computer Speech & Language* 2022; https://arxiv.org/abs/2004.03844. `source.md`: **not listed** — NEW. `SOURCE`: BERT/RoBERTa/XLNet prunable up to 40% retaining up to 98% performance; "the lower layers are most critical to maintain downstream task performance"; robustness varies by task. `SOURCE` (by absence in the abstract): no comparison of importance criteria and no loss-vs-task disagreement claim.
- **Similarity of Neural Network Representations Revisited** — Simon Kornblith, Mohammad Norouzi, Honglak Lee, Geoffrey Hinton; **ICML 2019**; https://arxiv.org/abs/1905.00414. `source.md` **line 358**, Tier 2 #3. `SOURCE`: CKA measures the relationship between representational similarity matrices, avoids the invertible-linear-invariance limitation of CCA, and "can reliably identify correspondences between representations in networks trained from different initializations". `SOURCE` (by absence): the abstract makes **no** claim that representational similarity implies functional or behavioural equivalence — so CKA cannot be used to license a behavioural layer claim.
- **DecoderLens: Layerwise Interpretation of Encoder-Decoder Transformers** — Anna Langedijk, Hosein Mohebbi, Gabriele Sarti, Willem Zuidema, Jaap Jumelet; 2023; **accepted to Findings of NAACL 2024**; https://arxiv.org/abs/2310.03686. `source.md` **line 331**, Tier 2 #1. `SOURCE`: lets "the decoder … cross-attend representations of intermediate encoder layers instead of using the final encoder output", applied to QA, logical reasoning, speech recognition and MT, revealing "specific subtasks that are solved at low or intermediate layers". Note: DecoderLens as published lenses the **encoder** stack. **New here:** the Findings-of-NAACL-2024 venue. No official repo found on the abs page (`unverified`).
- **Eliciting Latent Predictions from Transformers with the Tuned Lens** — Nora Belrose, Igor Ostrovsky, Lev McKinney, Zach Furman, Logan Smith, Danny Halawi, Stella Biderman, Jacob Steinhardt; 2023; https://arxiv.org/abs/2303.08112 · official code https://github.com/AlignmentResearch/tuned-lens. `source.md` **lines 344 and 347**, Tier 2 #2. `SOURCE`: affine probe per block, "more predictive, reliable and unbiased than the logit lens"; causal experiments show "the tuned lens uses similar features to the model itself".
- **Is One Layer Enough? Training A Single Transformer Layer Can Match Full-Parameter RL Training** — Zijian Zhang, Rizhen Hu, Athanasios Glentis, Dawei Li, Chung-Yiu Yau, Hongzhou Lin, Mingyi Hong; arXiv preprint submitted 2026-07-01; https://arxiv.org/abs/2607.01232. `source.md` **line 306**, Tier 1 #3. `SOURCE`: training a single layer can recover most or exceed full-parameter RL gains; they introduce a "layer contribution" metric; across Qwen models, GRPO/GiGPO/Dr.GRPO, and math/code/agent domains, RL gains concentrate in middle-stack layers with minimal contribution from input/output layers, and "the same structural pattern consistently emerges". Author names and venue status are **new here**. Peer-review status `unverified`.
- **A Layer-wise Analysis of Supervised Fine-Tuning** — Qinghua Zhao, Xueling Gong, Xinyu Chen, Zhongfeng Kang, Xinlu Li; arXiv 2026-04-12 (v1), rev. 2026-08-26; **accepted to ACL 2026 main**; https://arxiv.org/abs/2604.11838 · https://aclanthology.org/2026.acl-long.453/. `source.md` **lines 317 and 320**, Tier 1 #4. `SOURCE`: "middle layers (20%–80%) are stable, whereas final layers exhibit high sensitivity"; they use "information-theoretic, geometric, and optimization metrics" across 1B–32B models and report a **consistent** depth-dependent pattern across measurement types; they propose Mid-Block Efficient Tuning with gains "up to 10.2% on GSM8K (OLMo2-7B)". Author names are **new here**.
  - **This is partially conflicting evidence for the campaign's Q5 claim** (`INFERENCE`): LASF reports *agreement* across information-theoretic, geometric and optimisation layer metrics on LLM SFT, whereas the campaign observes *orthogonality* between CE-based and symbolic-damage-based rankings on ODEFormer. The conflict is not necessarily real — LASF's metric family does not include a symbolic/structural task-correctness criterion, and the models, tasks and intervention types differ entirely — but the campaign must report it rather than cite LASF as support.

## Q5.4 Does the "layer improves loss while destroying task-correct output" phenomenon have a name?

- **"Loss-metric mismatch"** is the established term for the general phenomenon that a surrogate loss is a poor proxy for the evaluation metric: **Addressing the Loss-Metric Mismatch with Adaptive Loss Alignment** — Chen Huang, Shuangfei Zhai, Walter Talbott, Miguel Angel Bautista, Shih-Yu Sun, Carlos Guestrin, Josh Susskind; **ICML 2019**; https://arxiv.org/abs/1905.05895. `SOURCE`: they characterise the problem as the assumption that "a fixed, often handcrafted, loss function is … a good proxy for an underlying evaluation metric" and treat that assumption as the failure. `source.md`: **not listed** — NEW.
- **`unverified` / probably unnamed**: I found **no** primary source naming or documenting the specific phenomenon *"ablating/intervening on a single layer reduces the model's cross-entropy while destroying the structural correctness of its output"*. The Minitron quote (Q5.2) is the nearest documented instance of the *ranking* failure but not of the *sign-flip on an individual layer*.
- **Do not** call this a "documented named phenomenon" in the C0001 report. The honest statement is: the general loss-metric mismatch is named and established; the layer-level sign-flip in symbolic output correctness is not documented in any source I verified.

**Q5 label: `adjacent`** at the level of "loss-based ≠ task-based layer importance", which Minitron (Q5.2) and Hewitt & Liang's ELMo layer reversal (Q5.3) establish in other settings, and which TSRM (Q5.1) establishes at *component* level *inside a transformer SR model*. **`plausibly_novel`** for the three specific elements of the campaign's result: (i) the estimand comparison at **layer** granularity in an **ODE-SR encoder-decoder**, (ii) a **failure-aware symbolic-TED damage** criterion as the second ranking, and (iii) the quantified **orthogonality** (Spearman 0.0090, p = 0.974, n = 16) plus the `decoder_11` sign-flip. Per `.claude/rules/11`, these are `plausibly_novel`, not `novel`, and (iii) is a 16-point rank correlation — an extremely wide confidence interval — so the *statistic* should be presented as "consistent with no monotone association", never as "orthogonal" in a strong sense (`.claude/rules/01` item 8: non-significance is not equivalence).

---

# Q6 — GRN dynamics ground truth and biological framing

## Q6.1 GeneNetWeaver

- Title: **GeneNetWeaver: in silico benchmark generation and performance profiling of network inference methods**
- Authors: Thomas Schaffter, Daniel Marbach, Dario Floreano
- Year/venue: 2011; *Bioinformatics* **27(16):2263–2270**
- DOI https://doi.org/10.1093/bioinformatics/btr373 · https://academic.oup.com/bioinformatics/article/27/16/2263/254752 · software http://gnw.sourceforge.net
- `source.md`: **lines 466 and 469**, Tier 3 #10. Already listed.
- `SOURCE`: GNW models **both transcription and translation** via ODEs for "the rate of change of mRNA concentration" and "the rate of change of protein concentration" per gene, driven by an **activation function** f_i(·) that "computes the relative activation of the gene, which is between 0 (shut off) and 1 (maximally activated)". Regulatory interactions may be **independent or synergistic**. Molecular noise is modelled with the **chemical Langevin equation**; measurement noise uses "Gaussian and log-normal models of experimental noise as well as a model of noise observed in microarrays". Perturbation types: wild type, knockouts (transcription rate → 0), knockdowns (halved), dual knockouts, multifactorial. Data can be "steady states and/or time-series with user-defined duration and number of measurement points".
- `SOURCE`: for the functional form of f_i, GNW defers — "A more detailed description of the activation function used is given by Marbach et al. (2010)."

## Q6.2 The primary source for the GNW dynamical model — missing from `source.md`

- Title: **Revealing strengths and weaknesses of methods for gene network inference**
- Authors: Daniel Marbach, Robert J. Prill, Thomas Schaffter, Claudio Mattiussi, Dario Floreano, Gustavo Stolovitzky
- Year/venue: 2010; **PNAS 107(14):6286–6291**
- https://www.pnas.org/content/107/14/6286 · PubMed https://www.ncbi.nlm.nih.gov/pubmed/20308593 · author PDF https://compbio.mit.edu/marbach/papers/Marbach2010.pdf (fetched and parsed locally with `pdftotext`)
- `source.md`: **not listed**. **NEW SOURCE — and it is the actual primary warrant for what DREAM3/4/5 in silico dynamics are.** Strongly recommend adding to group 4.
- `SOURCE`, verbatim from the Methods: "where m_i is the maximum transcription rate, r_i the translation rate, λ^RNA_i and λ^Prot_i are the mRNA and protein degradation rates, and f_i(·) is the so-called input function of gene i. The input function computes the relative activation of the gene … given the transcription-factor (TF) concentrations y. **The input function is derived using a standard thermodynamic approach (24), where binding of TFs to cis-regulatory sites is approximated using Hill-type kinetics (see SI Methods).**"
- `SOURCE`: "Knockouts were simulated by setting the maximum transcription rate m_i of the deleted gene to zero, knockdowns by dividing it by 2. Time-series experiments were simulated by integrating the networks using different initial conditions. For the networks of size 10, 50, and 100, we provided 4, 23, and 46 different time-series, respectively, with 21 time points each. Gaussian noise was added to the data after the simulation."
- **This confirms Hill-type kinetics are the ground-truth ingredient in GNW/DREAM in silico networks** (`SOURCE`) — which is the biological justification for the campaign's synthetic Hill-type GRN validation cells. It also confirms that the multi-initial-condition setting is native to this benchmark family, not an artificial construct.

## Q6.3 DREAM4 — status as an external benchmark, and what its targets do and do not represent

- Data resource: https://gnw.sourceforge.net/dreamchallenge.html (`SOURCE`: provides a challenge-description PDF and a ZIP with "all challenges (datasets + gold standards) … plus additional information (additional datasets, the datasets without noise, details on the applied perturbations, the signed goldstandards, network graphs …)").
- Official challenge description PDF: https://gnw.sourceforge.net/resources/DREAM4%20in%20silico%20challenge.pdf (fetched; parsed locally with `pdftotext`). `source.md` line 480 lists the challenge page only; **the challenge PDF URL is new here** and is the citable primary document.
- `source.md`: **line 480**, Tier 3 #10, explicitly positioned as the next-stage external benchmark after GPU_RUN5's Go 8 NO-GO. Status confirmed unchanged.

### `SOURCE`, verbatim from the official DREAM4 description

- Subchallenges: `InSilico_Size10`, `InSilico_Size100`, `InSilico_Size100_Multifactorial`; five networks per size.
- Time series (§1.2.5): "For networks of size 10 we provide 5 different time series, for networks of size 100 we provide 10 time series. Each time series has 21 time points. The initial condition always corresponds to a steady-state measurement of the wild-type. At t=0, a perturbation is applied … The first half of the time series (until t=500) shows the response of the network to the perturbation [the perturbation is constantly applied from t=0 until t=500]. At t=500, the perturbation is removed (the wild-type network is restored) … The second half of the time series (until t=1000) shows how the gene expression levels go back from the perturbed to the wild-type state." The perturbations "only affect about a third of all genes, but basal activation of these genes can be strongly increased or decreased".
- Dynamical model (§1.5): "The dynamics of the networks were simulated using a detailed kinetic model of gene regulation. Both independent and synergistic gene regulation occur in the networks. **Both transcription and translation are modeled. However, the protein concentrations are not included in the provided datasets.** As mentioned above, the datasets correspond to the mRNA concentration levels."
- Noise (§1.5): "The simulations are based on **stochastic differential equations (Langevin equations)** to model internal noise in the dynamics of the networks. In addition, we add measurement noise … very similar to a mix of normal and lognormal noise."
- Network topologies are subnetworks of *E. coli* and *S. cerevisiae* regulatory networks, with self-interactions removed.
- Gold standard and scoring: the target is the **directed unsigned topology**; scoring is AUPR/AUROC over edge predictions. The optional bonus round predicts dual-knockout expression values, scored by sum of squared error. **No ground-truth equations or kinetic parameters are the scored target.**

### What DREAM4 finite-difference targets do and do not represent — four independent obstructions

`INFERENCE`, each grounded in a `SOURCE` clause above:

1. **Latent variables.** Protein concentrations are simulated but not provided; only mRNA is observed. ODEFormer's own stated limitation is that it "only works when all variables are observed" (Q1.1 item 9). A finite-difference dmRNA/dt therefore cannot equal any function of the *observed* variables alone; the true right-hand side depends on unobserved protein.
2. **Stochastic, not deterministic, generating process.** The trajectories come from Langevin SDEs plus microarray-like measurement noise. A finite difference of such a trajectory estimates an increment of an Itô process, not an ODE right-hand side; there is no deterministic f for which the finite differences are unbiased targets.
3. **Non-autonomous / switched dynamics.** The perturbation is held constant on t ∈ [0, 500) and removed at t = 500. The 21-point trace is therefore a trajectory of two different vector fields spliced at t = 500, plus a discontinuity. Any single-ODE fit over the full window is misspecified; at minimum the window must be split, leaving ~11 points per regime.
4. **No equation-level gold standard.** The scored ground truth is edges. Exact/skeleton recovery cannot be evaluated on DREAM4 without either recovering the GNW model parameters from the software (possible in principle via GNW 2.0, which generated the data) or restricting to the noise-free ODE variants the resource ZIP reportedly contains.

**Conclusion for C0001** (`INFERENCE`): DREAM4 is a valid external benchmark for *edge inference*, and its ground truth *is* Hill-based (Q6.2), but it is **not** currently a valid external benchmark for *symbolic ODE recovery* by ODEFormer. Using it that way would violate `.claude/rules/03` ("do not claim equation discovery solely from R²/NMSE") and would produce a metric with no ground-truth equation to compare against. The GPU_RUN5 Go 8 NO-GO on DREAM4 is corroborated by the primary documentation, not merely by compute limits.

## Q6.4 Biological framing sources

- **Gene regulatory networks: from correlative models to causal explanations** — Rory J. Maizels, James Briscoe; *Nature Reviews Genetics*, 2026; DOI https://doi.org/10.1038/s41576-026-00939-1 · open access https://pmc.ncbi.nlm.nih.gov/articles/PMC7618986/. `source.md` **lines 420 and 423**, Tier 1 #10. **Both URLs verified to resolve to this article**; the PMC ID looked anomalous for a 2026 paper but the fetch confirms it is correct (author-manuscript deposit). `SOURCE`: the article argues GRNs "which should provide mechanistic explanations, are increasingly reduced to statistical correlations — 'hairballs' that fail to capture molecular causation", and proposes representation-learning models grounded in cellular and evolutionary biology. **Author names are new here.**
  - Relevance (`INFERENCE`): this supplies the campaign's motivation — recovering dynamical equations rather than edges — and simultaneously supplies the discipline required by `.claude/rules/01` item 7: symbolic recovery is not biological causality. Maizels & Briscoe are arguing for mechanistic *explanation*, which a recovered synthetic Hill equation does not by itself deliver.
- **scKINETICS: inference of regulatory velocity with single-cell transcriptomics data** — DOI https://doi.org/10.1093/bioinformatics/btad267 · open access https://pmc.ncbi.nlm.nih.gov/articles/PMC10311321/ · code https://github.com/dpeerlab/scKINETICS. `source.md` **lines 449–455**, Tier 2 #11. Not independently fetched this cycle → details `unverified` here; `source.md` correctly notes it uses a linear, time-homogeneous ODE system with EM, so it is a near-neighbour on the "derivatives are not observed" problem but not a symbolic-regression method. **Relevant to C0001 only as framing**, not as a method or benchmark.
- **Data-driven Discovery of Dynamical Models in Biology** — DOI https://doi.org/10.1038/s42254-026-00955-4, `source.md` **line 436**, Tier 1 #11. Not fetched this cycle → `unverified` here.
- **dynGENIE3** — DOI https://doi.org/10.1038/s41598-018-21715-0, `source.md` **line 493**. Not fetched → `unverified` here. Relevant only as the edge-inference baseline DREAM4 actually scores.

---

# Novelty assessment

Per `.claude/rules/11-literature-and-novelty.md`: nothing below is labelled novel on the grounds of being absent from this repository, and every `plausibly_novel` rests on an explicit statement of what searches were run and what was found.

| Q | Question | Label | Justification |
|---|---|---|---|
| **Q1** | Does the primary literature establish whether a pretrained SR transformer's decoder distribution contains the target skeleton, and how to measure it? | **`known`** for the *existence and severity of a generation-side bottleneck*; **`plausibly_novel`** for the *support-exclusion argument specific to Hill exponents in ODEFormer* | `known`: CTC_NSR quantifies reproduction bias (>97% copies at 100K scale; <6% novel tree structures at 1.5M scale) and reports that beam 150 "provided no additional information" and that MCTS sometimes reduced accuracy — the bottleneck class is established, as is the failure of the two cheapest remedies. ODEFormer independently reports that larger beams improve reconstruction but not generalization, and calls generalization "a much better proxy of symbolic recovery". `plausibly_novel`: no source I verified states that ODEFormer's per-component unary budget of 3 places the multiplicative Hill-4 form outside its pretraining support while placing the additive-decomposed equivalent inside it. This is my inference from the paper §3, the official generator code, and the released checkpoint's own `params`. |
| **Q2** | Is teacher-forced log-probability of the ground-truth expression an established SR diagnostic? | **`adjacent`** | The instrument's logic is established by a clean primary source in a neighbouring field — Stahlberg & Byrne (EMNLP 2019, DOI 10.18653/v1/D19-1331) separate search errors from model errors by directly scoring specific hypotheses rather than reading search output. Teacher-forced CE over ground-truth expression tokens is the standard *training* objective throughout SR. But across six targeted searches I found no primary SR or ODE-discovery source using it as an *evaluation-time* reachability diagnostic; CTC_NSR, the paper closest to the question, explicitly measures training-set membership instead and does not report GT log-probabilities. Absence over six searches is weak evidence, hence `adjacent` rather than `plausibly_novel`. |
| **Q3** | Hill-type / rational structure in equation-discovery method design | **`known`** (difficulty and non-neural remedies); **`plausibly_novel`** (a *neural pretrained transformer* recovering variable-denominator Hill terms) | `known`: implicit-SINDy establishes the null-space formulation over a mixed state-and-derivative library and validates it on Michaelis–Menten, bacterial competence and yeast glycolysis; SINDy-PI states verbatim that such extensions "are extremely sensitive to noise" and delivers "several orders of magnitude more noise robust" identification; `source.md`'s Rational Dynamics SVD entry continues that line. So both the difficulty and the working remedies are documented — outside neural SR. `plausibly_novel`: nothing I verified shows a pretrained transformer SR model recovering Hill-type variable denominators, and I found no primary source adding a learnable integer-exponent operator to such a model (`unverified` for CEQL/NOMTO leads, which I did not fetch). |
| **Q4** | Constrained/grammar-guided decoding and beam diversity raising true-structure recovery **in SR specifically** | **`known`** that beam size/diversity alone is insufficient; **`adjacent`** that grammar constraints help; **`known`** that constrained decoding carries a distribution-distortion cost | `known` (insufficiency): two independent primary sources — ODEFormer Appendix G and CTC_NSR's b=150 result — plus ODEFormer footnote 5, which shows the diversity fix (beam sampling) is *already* in the campaign's checkpoint. `adjacent` (grammar helps): GODE (MSSP 2025, official repo `ETH-IBK-SMECH/GODE`) demonstrates grammar-seeded search beating transformer SR on structural-dynamics ODEs, but *replaces* the transformer rather than constraining it, and covers no Hill/GRN systems; CNSR/NSRwH (ICML 2023) demonstrates that structural conditioning helps, but the conditioning channel is *trained in*, which ODEFormer lacks; SymLang's grammar-vs-CFG exact-recovery ablation is `unverified`. `known` (cost): Grammar-Aligned Decoding (NeurIPS 2024) demonstrates verbatim that GCD "can distort the LLM's distribution". |
| **Q5** | Is CE-based vs symbolic/behavioural layer-importance orthogonality already known? | **`adjacent`** for the general claim; **`plausibly_novel`** for the SR-layer-symbolic-damage instance and the sign-flip | `adjacent`: the Minitron paper states verbatim "LM validation loss/PPL-based layer importance fails to produce the most accurate pruned model(s) on downstream tasks"; Hewitt & Liang document an ELMo layer-ranking reversal between raw probing accuracy and selectivity; TSRM shows Direct Logit Attribution failing where performance-based mean patching succeeds, *inside a transformer SR model*; Zhang & Nanda (ICLR 2024) show that "varying these hyperparameters could lead to disparate interpretability results". So "two layer-importance criteria can disagree" is established. `plausibly_novel`: TSRM is component-level not layer-level and uses functional/numerical rather than symbolic-structural correctness; Minitron uses task accuracy, not equation structure; and **no** verified source reports (a) a symbolic-TED-damage layer ranking, (b) a rank-correlation orthogonality statistic between it and a CE ranking, or (c) an individual layer whose ablation *improves* CE while destroying formula correctness. The general loss-vs-metric divergence *is* named ("loss-metric mismatch", Huang et al., ICML 2019); the layer-level sign-flip is **`unverified` / apparently unnamed**. |
| **Q6** | DREAM4 / GeneNetWeaver status and what finite-difference targets represent | **`known`** — fully answered by official documentation | GNW (Bioinformatics 27(16):2263–2270) and Marbach et al. (PNAS 107(14):6286–6291) establish that the in silico ground truth uses coupled mRNA/protein ODEs with an input function derived from a thermodynamic model in which "binding of TFs to cis-regulatory sites is approximated using **Hill-type kinetics**". The official DREAM4 challenge PDF establishes that protein concentrations are **not provided**, that the simulations "are based on stochastic differential equations (Langevin equations)", that measurement noise is a normal/lognormal mix, that the 21-point traces are non-autonomous (perturbation on [0,500), removed at t=500), and that the scored gold standard is the **directed unsigned topology**, not equations. Nothing here is novel; all of it is decisive. |

## Corrections and additions recommended for root `source.md`

`SOURCE`-verified metadata that `source.md` currently lacks. None of these are errors of fact in `source.md`; they are missing fields.

1. **ODEFormer** (line 43): add venue **ICLR 2024**, OpenReview `https://openreview.net/forum?id=TzoHLiGVMo`, official repo `https://github.com/sdascoli/odeformer`.
2. **GODE** (lines 109–112): add official repo `https://github.com/ETH-IBK-SMECH/GODE`; authors Yu, Chatzi, Kissas.
3. **D-CODE** (line 215): record the lab-org repo `https://github.com/vanderschaarlab/D-CODE-ICLR-2022` alongside the existing one; authors Qian, Kacprzyk, van der Schaar; ICLR 2022 Spotlight.
4. **Causal Abstraction** (line 401): the JMLR version is **26(83):1–64, 2025**.
5. **DecoderLens** (line 331): **Findings of NAACL 2024**.
6. **BPAP / activation patching metrics** (line 377): **ICLR 2024**; Fred Zhang, Neel Nanda.
7. **CNSR** (line 589): **ICML 2023, PMLR v202**; `https://proceedings.mlr.press/v202/bendinelli23a/bendinelli23a.pdf`. Given C0001's direction this should move from Tier 4 to Tier 2.
8. **ESRT / Kamienny et al.** (line 578): **NeurIPS 2022** + proceedings URL.
9. **NEW — Marbach et al. 2010, PNAS 107(14):6286–6291** — the actual primary source for the GNW/DREAM dynamical model and its Hill-type kinetics. Belongs in group 4 next to GNW; arguably Tier 1, since it is the warrant that the campaign's Hill-type synthetic targets are biologically grounded in the benchmark family.
10. **NEW — official DREAM4 challenge PDF**, `https://gnw.sourceforge.net/resources/DREAM4%20in%20silico%20challenge.pdf` — the citable primary document for what DREAM4 data are.
11. **NEW — Stahlberg & Byrne 2019**, `https://aclanthology.org/D19-1331/`, DOI `10.18653/v1/D19-1331` — the precedent for the Q2 diagnostic.
12. **NEW — Grammar-Aligned Decoding**, Park et al., NeurIPS 2024 — required caveat for any constrained-decoding intervention.
13. **NEW — Diverse Beam Search**, Vijayakumar et al., AAAI 2018, `https://arxiv.org/abs/1610.02424`.
14. **NEW — Minitron in practice**, `https://arxiv.org/abs/2408.11796` — the primary quote for loss-based layer importance failing on downstream tasks.
15. **NEW — Sajjad et al., dropping layers**, `https://arxiv.org/abs/2004.03844`.
16. **NEW — Huang et al., loss-metric mismatch**, ICML 2019, `https://arxiv.org/abs/1905.05895`.
17. **NEW (low confidence, mark `unverified`) — SymLang** `https://arxiv.org/abs/2603.06869`; **Breaking the Simplification Bottleneck in Amortized Neural Symbolic Regression** (Paul Saegert, Ullrich Köthe, stated as ICML 2026 camera-ready) `https://arxiv.org/abs/2602.08885` — the latter is relevant because it addresses expression normalisation, which is exactly the machinery the Q1 form-equivalence check needs; I confirmed it does **not** analyse skeleton reachability.

---

# Implications for C0001 design

## Already answered by the literature — do NOT spend GPU compute re-establishing

1. **Larger beam / higher temperature will not create the missing Hill structure.** ODEFormer Appendix G ("Increasing the beam size improves reconstruction, but not generalization") and CTC_NSR (beam 150 "provided no additional information") are two independent primary sources, and the campaign's own 0/960 is a third. A beam/temperature sweep as a *primary* experiment has near-zero expected information gain. (Keep beam size fixed at the preregistered 50 @ 0.1 as a control condition only.)
2. **Beam-sampling-style diversity is already applied.** ODEFormer footnote 5 states the authors adopted beam sampling *because* beam search collapses to one skeleton. The campaign's checkpoint already has the documented diversity fix. Diverse Beam Search would be a marginal variation on an already-mitigated failure mode, and has never been demonstrated for SR.
3. **MCTS/TPSR-style test-time search is documented as an unreliable remedy for reproduction bias.** CTC_NSR reports MCTS generated novel expressions "but sometimes reduced accuracy". And `INFERENCE`: TPSR reweights search over the same vocabulary and prior — it cannot add a `pow` operator or extend the support. Low expected gain against a support bottleneck.
4. **"Reconstruction R² is not recovery" needs no further demonstration.** ODEFormer itself declines to measure symbolic agreement and names generalization the better proxy. `.claude/rules/01` item 6 and `.claude/rules/03` already encode this. Do not design an experiment whose finding is "low NRMSE did not imply recovery".
5. **DREAM4 is not yet usable as a symbolic-recovery benchmark.** Four independent obstructions, each from official documentation: proteins unobserved (vs ODEFormer's stated all-variables-observed requirement); Langevin SDE generation (finite differences do not estimate an ODE right-hand side); non-autonomous switched dynamics with the perturbation removed at t = 500; and an edge-only gold standard. The GPU_RUN5 Go 8 NO-GO is corroborated. If DREAM4 is wanted later, the tractable route is regenerating data with GNW 2.0 under deterministic ODE settings so the equations are known — a data-generation task, not an inference experiment.
6. **Constrained decoding is not free.** Grammar-Aligned Decoding (NeurIPS 2024) demonstrates that grammar-constrained decoding distorts the model distribution. Any masked-decoding arm must be preregistered with a distribution-distortion control (e.g. report GT-conditional likelihood and candidate NRMSE alongside structural hit rate), or the resulting "improvement" will be uninterpretable.

## Genuinely open — worth C0001 compute, in priority order by information-per-FLOP

1. **[Cheapest, highest value, CPU-only] Resolve the form-equivalence confound before anything else.** `α·x⁴/(K⁴+x⁴)` in multiplicative form needs 5 unary operators and is outside the released checkpoint's support (`max_unary_ops_per_dim = 3`); the algebraically identical `α − α·K⁴·inv(K⁴+x⁴)` needs 3 and is inside it. The 0/960 result may be partly a *matcher* artifact. Re-score the existing GPU_RUN5 candidate sets under a canonicalising / algebraically-equivalence-aware matcher, and report exact/skeleton recovery under **both** the literal and the canonical criterion. `.claude/rules/03` already requires raw + simplified + variable mapping to be preserved, so this needs no new generation. This experiment can *invalidate or sharpen the campaign's headline bottleneck claim at essentially zero GPU cost*, which makes it the correct first move.
2. **[Open, well-motivated] Separate support failure from search failure from selection failure with a three-way diagnostic.** No verified primary source does this for SR. The design that discriminates all three simultaneously (`hypothesis-tree` skill: prefer experiments that distinguish multiple explanations at once):
   - **(a) support/prior probe** — the analytic unary-budget count per target skeleton (free, deterministic, from the checkpoint `params` already read);
   - **(b) model probe** — teacher-forced log-probability (and per-token rank) of the ground-truth token sequence, in both the literal and canonical forms from (1). Frame it explicitly as the SR analogue of Stahlberg & Byrne's search-vs-model-error split, and cite it as `adjacent`, not novel;
   - **(c) search probe** — the already-measured beam hit rate.
   Predicted contrasts: high (b) with zero (c) ⇒ search error, remediable by decoding; vanishing (b) with (a) = 0 ⇒ support error, remediable only by grammar/operator extension or fine-tuning; vanishing (b) with (a) > 0 ⇒ learned-prior error, remediable by fine-tuning. These three outcomes imply *different* next cycles, which is precisely the property that makes the experiment worth running. Cost: one forced-decoding pass per validation cell — cheaper than one beam-sampling pass.
3. **[Open] Whether the 14.76% variable-denominator candidate rate is `inv`-of-affine or true variable-denominator structure.** Given step 8's affine wrap (`x ↦ a·x+b`) and `inv` being the only division route, a large share of those candidates may be `inv(a·x+b)` — a saturating but non-Hill form. Classify the existing candidates by denominator arity and exponent structure. No compute beyond re-parsing saved candidates, and it directly tests whether "denominators are reachable in form" is the right description.
4. **[Open, medium cost] Whether an operator/grammar extension is required or whether fine-tuning suffices.** GODE demonstrates grammar-seeded search works for structural-dynamics ODEs but replaces the transformer; CNSR demonstrates structural conditioning works but trains the channel in. Neither demonstrates constraining a pretrained SR decoder. If (2) returns a support error, the discriminating question becomes: does adding a `pow`/exponent operator and continuing pretraining on Hill-type families recover the structure, versus grammar-masking the existing checkpoint (with the Q4.1 distortion control)? This is a real GPU experiment and should wait for (1)–(3).
5. **[Open, but downgrade the statistical claim] The Q5 estimand divergence.** The scientific content is `plausibly_novel` (Q5 above). But the evidence is a 16-point Spearman correlation, and `.claude/rules/01` item 8 forbids reading non-significance as equivalence. Before promotion: (i) re-frame the claim as "the CE ranking does not predict the symbolic-damage ranking" — the form Minitron already supports in another domain — rather than "the rankings are orthogonal"; (ii) treat the `decoder_11` CE-improves-while-structure-breaks observation as the high-value item, since it appears to be undocumented anywhere, and route it through `replication-gate` before any external claim; (iii) report LASF's *agreeing*-metrics result (Q5.3) as conflicting evidence in the cycle report, per `hypothesis-tree`'s requirement to record conflicting observations; (iv) adopt the vocabulary the literature already has — "loss-metric mismatch" (Huang et al., ICML 2019) — rather than coining a term.

## Constraints this record imposes on the C0001 preregistration

- Any exact/skeleton-recovery metric must state **which algebraic form** counts as a match, and report both literal and canonical scoring. Otherwise item (1) above becomes an uncontrolled confound in every downstream claim.
- Any generation-side intervention must report the **support-budget count** for its target skeletons, since the released checkpoint's `max_unary_ops_per_dim = 3` is a hard constraint and is now verified from the artifact itself.
- Any constrained-decoding arm must carry a distribution-distortion control (Q4.1).
- No biological-causality language anywhere in C0001: the targets are synthetic Hill-type cells; DREAM4 is not in play; and Maizels & Briscoe's mechanistic-explanation bar is far above symbolic recovery on synthetic data. (`.claude/rules/01` item 7.)
