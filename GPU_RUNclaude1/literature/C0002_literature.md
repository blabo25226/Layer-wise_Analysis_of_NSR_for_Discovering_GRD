# C0002 — Literature and Novelty Evidence Record

- cycle: `C0002`
- stage: 2 (literature and novelty evidence)
- branch: `20260909_researce_GPU_RUNclaude1`
- base commit at time of writing: `0f2afca` ("Select H0001-R and H0010 as the C0002 hypotheses")
- date: 2026-09-11
- skill: `literature-evidence`
- rules applied: `.claude/rules/11-literature-and-novelty.md`, `.claude/rules/01-research-integrity.md`,
  `.claude/rules/03-symbolic-regression-contract.md`, `.claude/rules/15-document-language.md`
  (this is an agent-facing technical document, therefore English)
- root reference index cross-checked: `/home/blabo/Layer-wise_Analysis_of_NSR_for_Discovering_GRD/source.md` (734 lines)
- brief this record closes: `GPU_RUNclaude1/hypotheses/C0002_design_brief.md` §10 ("文献状況と novelty ラベル")

## Labelling conventions

- `SOURCE` — supported by the cited primary source (paper text, official repository code,
  official documentation, or an official released artifact). A quotation is given wherever the
  wording carries the load.
- `INFERENCE` — my reasoning over `SOURCE` facts. **Not** asserted by any cited source.
- Novelty labels are the `literature-evidence` skill's four: `known`, `adjacent`,
  `plausibly_novel`, `unverified`. Absence from this repository is never a novelty argument
  (rule 11). Where a label could be argued either way, the **weaker** label is taken.

## Scope limits of this record

- This record preregisters nothing. Stage 3 (`lansr-research-methodologist`) freezes the contract.
- It does not touch `phase4/sealed_official_test.json` or any sealed artifact, and reads no
  final-test example.
- It does not edit `plans/C0001_preregistration_v2.1.md`, `reports/C0001_report.md`,
  `reviews/`, `replications/`, or `results/runs/gpu_runclaude1_c0001_b731cdd/`.

---

# Q1 — Stahlberg & Byrne: DOI verification and what the paper actually licenses

## Q1.1 Bibliographic verification (`SOURCE`)

| Field | Value | How verified |
|---|---|---|
| Title | **On NMT Search Errors and Model Errors: Cat Got Your Tongue?** | ACL Anthology landing page |
| Authors | **Felix Stahlberg, Bill Byrne** (University of Cambridge, Department of Engineering) | Anthology page + PDF title block |
| Year / venue | **2019**, Proceedings of EMNLP-IJCNLP 2019, Hong Kong, China, November 3–7 2019 | PDF page footer, p. 3356 |
| Pages | **3356–3362** | PDF page footer |
| DOI | **10.18653/v1/D19-1331** | ACL Anthology landing page |
| URL | https://aclanthology.org/D19-1331/ | fetched |
| PDF | https://aclanthology.org/D19-1331.pdf | downloaded, `pdftotext -layout`, 499 lines |
| Official implementation | **SGNMT**, http://ucam-smt.github.io/sgnmt/html/ , `simpledfs` decoding strategy (paper footnote 4) | PDF p. 3358 footnote 4 |

**The DOI in `C0002_design_brief.md` §4.2 and §10 is correct.** Title, author list, year, venue and
page range are all correct as cited there. No correction is needed. (`SOURCE`)

`source.md` relationship: **Stahlberg & Byrne is not in `source.md`.** It is cited only inside
`GPU_RUNclaude1/`. Recommend adding it to `source.md` group 6 (補助・基礎文献) — see §6 below.

## Q1.2 The paper's own operational definitions (`SOURCE`, verbatim)

1. **Search error.** Footnote 5, p. 3358:
   > "A sentence is classified as search error if the decoder does not find the global best model score."

   The *global best model score* is obtained by the paper's **exact** inference procedure
   (Alg. 2, depth-first search with the admissible bound γ), not by any approximation.

2. **γ — the quantity the returned hypotheses contribute.** §2, p. 3357:
   > "Let γ be the model score found by beam search (p̃ in line 12, Alg. 1), which is a lower bound
   > on the global best model score: γ ≤ log P(ŷ|x)."

   And Alg. 1 line 12 is:
   > "(ỹ, p̃) ← arg max_{(y,p)∈H_cur} p"

   i.e. **γ is the maximum model score over the hypothesis set the procedure holds** — an
   `arg max` over a returned set, nothing more.

3. **Why γ is an admissible lower bound.** §2, Eq. 3:
   > "∀j ∈ [2, J] : log P(y₁^{j−1}|x) > log P(y₁^{j}|x)."

   This monotonicity holds because the per-token conditionals are log-probabilities and hence
   non-positive. The paper states it **fails** under length normalization or word rewards:
   > "While this monotonicity condition is true for vanilla NMT (Eq. 3), it does not hold for
   > methods like length normalization … or word rewards …"

4. **The reference translation is NOT the comparison point for search errors.** Reading the whole
   paper, the reference is used in exactly two places: the length-ratio histograms (Figs. 3 and 5),
   and one *oracle* experiment where exact search is constrained to the reference length
   (Tab. 3, row "Exact for reference length", BLEU 37.9 / ratio 1.01). The search-error counts in
   Tab. 1 (Greedy 73.6%, Beam-10 57.7%, Exact 0.0%) and Tab. 2 are all against the exact global
   best, never against the reference. (`SOURCE`, by exhaustive reading of the 7-page paper.)

5. **Approximating the global best by a returned list is a named, superseded approximation.** §5:
   > "To the best of our knowledge, this is the first work that reports the exact number of search
   > errors in NMT as prior work often relied on approximations, e.g. via n-best lists
   > (Niehues et al., 2017) or constraints (Stahlberg et al., 2018b)."

6. **Headline numbers** (`SOURCE`, Tab. 1 / §3): Transformer-Base on WMT15 en-de news-test2015
   (2,169 sentences). Greedy: BLEU 29.3, 73.6% search errors. Beam-10: BLEU 30.3, 57.7% search
   errors. Exact: BLEU 2.1, 0.0% search errors, **51.8% empty translations**. Beam-100 still
   produces **53.62%** search errors.

7. **Length bias is the diagnosed model error.** §4:
   > "This suggests that the problem of empty translations is the consequence of an inherent model
   > bias towards shorter hypotheses and cannot be fixed with a length constraint."

## Q1.3 Answer to the question as asked

> *Does comparing `logP(reference)` against `logP(what search returned)` require the returned
> sequence to come from a search procedure, or is a temperature-sampled set admissible?*

**`SOURCE`:** The paper **never performs this comparison** and **never defines a search error this
way**. Its search-error rate is defined against the exact global argmax found by DFS. So the paper
does not, on its own terms, license a reference-vs-returned comparison at all — under *any*
decoding procedure. Anyone citing D19-1331 for a reference-based search-error rate is citing it for
something it does not say, and that must be stated in the preregistration.

**`INFERENCE` (mine, derived from the paper's own γ argument):** what the paper *does* license is
the inequality chain. The only properties used to make γ an admissible bound are

- (a) γ is the `arg max` model score over the set the procedure returned, and
- (b) the model score of any complete sequence is ≤ the global best, i.e. γ ≤ log P(ŷ|x).

**Neither property mentions how the set was produced.** Beam search enters only as the thing that
happened to fill `H_cur`. A temperature-sampled set of 50 complete sequences satisfies (a) and (b)
identically. Therefore a sampled candidate set **is admissible** as the source of γ, provided γ is
taken as the **maximum** over the set.

What is *not* admissible under the paper's own definition is substituting an **arbitrary member**
of the returned set for γ. Alg. 1 line 12 is an `arg max`; an arbitrary member is not, and it
destroys the property that makes the comparison informative. That is exactly the CRITICAL-R3
defect, treated next.

---

# Q2 — CRITICAL-R3: what the reference set must be when candidates are sampled

**This section is the gating answer for the C0002 endpoint.**

## Q2.1 The defect is real in the stored data and in the vendored code (`SOURCE`)

`GitHubSourceCode/ODEFormer/odeformer/model/model_wrapper.py` — read directly:

- Lines 95–131, the `self.beam_type == "search"` branch, sorts:
  ```
  search_generations = [
      sorted(
          [hyp for hyp in search_generations[i].hyp],
          key=lambda s: s[0],
          reverse=True,
      )
      for i in range(bs)
  ]
  ```
  i.e. descending by score. Index 0 of that list **is** an `arg max`.
- Line 133 onward, the `elif self.beam_type == "sampling"` branch, calls `decoder.generate(...,
  sample_temperature=self.beam_temperature, ...)`, then transposes and filters. **There is no
  `sorted` anywhere in this branch.** Index 0 is sample order.

Combined with the already-recorded fact that GPU_RUN5 `phase3/config_snapshot.json` has
`beam_type = "sampling"`, `beam_temperature = 0.1`, `beam_size = 50`, the design brief's §5.2
diagnosis is confirmed at the source level: `candidate_index == 0` is the **first sampled**
candidate, not a selected one. (`SOURCE`)

## Q2.2 What the literature says the reference set must be

**`SOURCE`:** there is **no accepted reference set for sampled candidates** in D19-1331, because
the paper's reference is the exact global argmax, which is unavailable here (the DFS of Alg. 2
relies on a bounded vocabulary and monotone scores; it is not run for SR in any paper I found).

**`SOURCE`:** approximating the global best by *what a decoder returned* is a named approximation
family — "approximations, e.g. via n-best lists" (§5) — which D19-1331 supersedes rather than
forbids. And the paper quantifies the direction of the approximation's error: Beam-100 returns
sets whose max is still not the global best for **53.62%** of sentences. So an approximation built
on a returned set **systematically undercounts** search errors.

**`INFERENCE`:** therefore `lp_best = max over the returned set` is the correct functional — it is
γ, verbatim — and `sb_best = 1[lp_gt > lp_best]` is a **conservative, one-sided lower bound** on
the true search-error rate. It cannot inflate E3. Reporting it as an *estimate* of the search-error
rate would be wrong; reporting it as a **certified lower bound** is exactly what D19-1331's
inequality supports.

## Q2.3 The certificate is two-sided, and that is the useful part

Let `L* = log P(ŷ|x)` be the model's (unknown) global best score for the cell, `B = lp_best` the
maximum over the 50 realized candidates, `G = lp_gt` the teacher-forced score of the truth.
`SOURCE` gives `B ≤ L*`.

- **If `G > B`:** then `L* ≥ G > B`, so the procedure did not return the global best. By the
  paper's own footnote-5 definition, **a search error is certified** for that cell. → E3 evidence.
- **If `G < B`:** then `L* ≥ B > G`, so `ŷ ≠ truth`: **the model's own argmax is not the ground
  truth**, and no improvement to search can make it so under this model. → E2 evidence.

(`INFERENCE`, elementary, from the `SOURCE` inequality `γ ≤ log P(ŷ|x)`. The paper does not state
the second branch; it is the contrapositive of its own bound.)

Both branches hold **regardless of how the candidate set was produced**. This is the substantive
answer: **sampling is admissible, and `lp_best`/`sb_best` — option (A) in design brief §5.2 — is
defensible on primary-source grounds.** Option (B) (`beam_type = "search"` re-decode) is a
*different* experiment on a *different* candidate set, exactly as the brief says; it is not needed
to make option (A) valid.

## Q2.4 Five caveats that must be preregistered with it

1. **Neither branch is an equivalence claim.** `G < B` does not bound how much probability mass the
   truth has, only that it is not the argmax. `G > B` does not say that more search would find the
   truth — D19-1331's central result is that the global best can be a **degenerate** sequence
   (51.8% empty translations, BLEU 2.1). The SR analogue of "the empty translation" is a
   degenerately short expression, and it is not ruled out. (`SOURCE` for the degeneracy;
   `INFERENCE` for the analogue.) Rule 01 item 8 applies verbatim.

2. **Temperature 0.1 makes the instrument anti-conservative *toward E2*.** (`SOURCE`: ODEFormer
   §4 uses beam size 50 and temperature 0.1; `C0001_literature.md` Q1.1 item 7 already records
   this.) `INFERENCE`: sampling at T = 0.1 draws from a sharpened distribution, so the realized set
   sits in the extreme upper tail and `B` is a *tight* lower bound on `L*` — close to greedy. The
   `G > B` branch therefore becomes harder to trip. Consequence: **`sb_best` under-detects E3 and
   correspondingly over-attributes to E2.** Since E2 is the campaign's currently favoured
   explanation, the instrument is biased *in favour of the preferred hypothesis*. This must be
   stated in the preregistration as a directional bias, not buried. The brief's own secondary
   observable — the percentile rank of `lp_gt` among the 50 — is the right mitigation and should be
   promoted to a co-primary report, since it is bias-free in a way the binary indicator is not.

3. **Sum-log-probability is length-confounded, and D19-1331 is the paper that proves it.**
   (`SOURCE`: Tab. 1, Figs. 1/3, and §4's conclusion that there is "an inherent model bias towards
   shorter hypotheses".) `INFERENCE`: GRN Hill truths are token-longer than the polynomial
   candidates that dominate the realized vocabulary (`c*x_0 + c*x_1` 23,931 occurrences etc.).
   A raw `G < B` is therefore partly the generic length bias, not a GRN-specific prior-mass
   deficit, and an unqualified E2 conclusion would be confounded. The **source-licensed control**
   is the paper's own §4 device: compare under a length constraint (Tab. 3 contrasts "Exact for
   Beam-10 length" 37.0 against "Exact for reference length" 37.9). Practical translation for
   Stage 3: report `G` and `B` both as sums and as per-token means, and additionally compare `G`
   against the best candidate of comparable token length. Length normalization itself breaks the
   monotonicity that makes γ admissible (`SOURCE`, §2), so it must be a *reported side analysis*,
   never a replacement for the raw-score certificate.

4. **The encoding precondition has no analogue in D19-1331, and it is load-bearing.**
   `G` is the log-probability of **one spelling** of the truth. In NMT a reference is a string with
   a canonical segmentation, so D19-1331 never faces this. C0001 already measured that the GRN
   truth has at least two inequivalent tokenizations under the frozen code (Hill-4 as `pow,x_0,4`
   on the infix path vs `pow,pow,x_0,2,2` on the prefix path; `neg` nodes appearing only on the
   prefix path; `classify_formula(true_prefix)` and `classify_formula(true_formula)` disagree on
   80/80 inspected systems). `INFERENCE`: using a single arbitrary encoding makes `G` a **lower
   bound** on the truth's probability under the model, which biases the comparison **toward E2 for
   a third time**. `G` should be the log-sum-exp (or at minimum the max) over a preregistered,
   enumerated set of admissible encodings. **This is why `H0006` is a genuine precondition for
   `H0001-R`, not an optional companion.** The SR literature *does* recognize this hazard — Sato &
   Sato Remark 5.2 and TSRM's 31.8% / 39.2% round-trip re-creation failure, both in §Q5.4 and
   §Q4.5 — but the only published way out of it (choose operators so that structure determines
   function) is unavailable when the operator set is fixed by a released checkpoint.

5. **`lp_sel` must not be resurrected.** Nothing in D19-1331 supports using a non-argmax member of
   a returned set. Design brief §8 items 5 and 6 and the MAJOR-R5 retraction stand, and this record
   adds a literature reason for them rather than only a code reason.

## Q2.5 Resolved: design brief §11 item 4 (per-candidate model scores)

The brief lists as `unverified`: *"whether a per-candidate model score is recorded anywhere in
GPU_RUN5 such that `candidate_index == 0` could be restored as an argmax"*. I checked directly.

`SOURCE`, read-only inspection of `results/runs/gpu_run5_20260823_ddd267b0/phase3/`:

- The per-candidate record schema (960 `cells/*.json`, sampled 40 exhaustively for key union, plus
  `all_candidates.json`) has exactly these fields: `candidate_index`, `candidate_formula_raw`,
  `valid`, `failure_reason`, `canonical_exact`, `skeleton_exact`,
  `exponent_aware_skeleton_exact`, `component_exponent_aware_skeleton_exact`, `ted_raw`,
  `ted_skeleton`, `normalized_ted`, `component_ted_raw`, `component_ted_skeleton`,
  `component_normalized_variable_aware_ted`, `component_valid`, `component_failure_reason`,
  `normalized_variable_aware_ted`, `variable_aware_ted_definition`, `complexity`,
  `candidate_formula_canonical`, `candidate_formula_skeleton`,
  `candidate_exponent_aware_skeleton`, `structure`, `trajectory_metrics`.
  **No score, log-probability, likelihood, NLL or rank field exists.**
- A recursive grep over all of `phase3/` for any key matching
  `"[a-z_]*(score|log_?prob|logp|nll|likelihood)[a-z_]*"` returns exactly **one** hit,
  `model_selection_score` in `config_snapshot.json`. Inspected in context, it is the run-level
  `failure_aware_formula_lexicographic_v1` scorer with `"unit": "component_within_system"` and
  `"aggregation": "macro_mean_by_system_then_seed"` — i.e. the cross-run model-selection scorer,
  **not** a per-candidate decoder score. This independently corroborates design brief §5.2's
  contract-citation diagnosis from the data side.

**Verdict: no per-candidate model score is stored.** `candidate_index == 0` cannot be rehabilitated
into an `arg max` by post-hoc sorting under any reading of the stored artifacts. `INFERENCE`:
therefore arm (A) of `H0001-R` requires the full teacher-forced re-scoring pass the brief already
budgets (960 truth sequences + 47,987 candidate sequences), and there is no cheaper path. The
brief's §9 GPU estimate of 0.3–1.0 h stands unchallenged by this check, but also unconfirmed — it
is still an estimate and still needs the Stage 4/5 smoke test (brief §11 item 3).

## Q2.6 Two further instrument facts read from the official released checkpoint

Read directly from `assets/odeformer/weights/odeformer.pt` (the official released weights) by
parsing the embedded `data.pkl` opcodes. Complements the `env.generator` reading already in
`C0001_literature.md`. (`SOURCE`.)

| Stored parameter | Pickle opcode | Value |
|---|---|---|
| `use_two_hot` | `0x89` NEWFALSE | **`False`** |
| `beam_type` | SHORT_BINUNICODE(8) | **`"sampling"`** |
| `beam_temperature` | `0x47` BINFLOAT | **`0.1`** |
| `beam_size` | `0x4b` BININT1 | `1` |
| `beam_length_penalty` | `0x4b` BININT1 | `1` |

Two consequences, both bearing on `H0001-R`:

1. **`use_two_hot = False` in the released checkpoint.** `SOURCE`: the vendored decoder's
   `generate` path branches on `self.use_two_hot` (`GitHubSourceCode/ODEFormer/odeformer/model/
   transformer.py:501, 550-554`) and, when enabled, emits constants through
   `env.topk_decode_two_hot` with a companion `two_hot_constant_masks` tensor rather than through
   the ordinary softmax over the token vocabulary. `INFERENCE`: had it been `True`, the
   teacher-forced log-probability of a ground-truth sequence would not be a plain sum of
   categorical log-probabilities and `lp_gt` would not be commensurable with `lp_best` at all —
   the Stahlberg–Byrne inequality of §Q2.3 needs one scoring function, not two. Because it is
   `False`, constants are ordinary vocabulary tokens and the certificate argument goes through.
   **This removes a hazard the design brief had not identified.** It does not remove the
   *encoding-choice* hazard of §Q2.4 item 4, which is about which spelling of the truth is scored,
   not about how constants are emitted.
2. **`beam_type = "sampling"` and `beam_temperature = 0.1` are the checkpoint's own stored
   defaults**, not choices GPU_RUN5 introduced. `INFERENCE`: the T = 0.1 upper-tail bias described
   in §Q2.4 item 2 is therefore a property of how ODEFormer is shipped and normally run, which
   makes the corresponding caveat more, not less, important to report — it is not an artifact of
   this campaign's configuration that could simply be changed away. (`beam_size` differs: the
   checkpoint stores `1`, GPU_RUN5 used `50`, matching the ODEFormer paper's §4 stated setting.)

## Q2.7 One-line answer for the supervisor

`lp_best` over the stored temperature-0.1 sampled set **is** Stahlberg & Byrne's γ, so option (A)
is sound and sampling is admissible; but the resulting `sb_best` is a **certified lower bound on
the search-error rate**, not an estimate of it, and three separate mechanisms (T = 0.1 tail
sampling, sequence-length bias, single-encoding `lp_gt`) all bias the read **toward E2**, which is
the campaign's preferred answer. The percentile rank of `lp_gt` within the 50 and a
length-controlled companion comparison must be co-reported, or the E2 conclusion is not defensible.

---

# Q3 — Deterministic budgets for CAS equivalence checking

## Q3.1 What the SR benchmarks actually use: wall clock, in every case I could verify

### SRBench 1.0 (the field-standard ground-truth protocol)

- Title: **Contemporary Symbolic Regression Methods and their Relative Performance**
- Authors: William La Cava, Patryk Orzechowski, Bogdan Burlacu, Fabrício Olivetti de França,
  Marco Virgolin, Ying Jin, Michael Kommenda, Jason H. Moore
- Year / venue: **2021**, NeurIPS 2021 Track on Datasets and Benchmarks
- arXiv: https://arxiv.org/abs/2107.14351 · DOI https://doi.org/10.48550/arXiv.2107.14351
- Official repository: https://github.com/cavalab/srbench · project page https://cavalab.org/srbench/
- `source.md` relationship: **absent**. Recommend adding (see §6).

`SOURCE`, Definition 4.1 (p. 6 of the arXiv PDF), verbatim:
> "Definition 4.1 (Symbolic Solution). A model φ̂(x, θ̂) is a Symbolic Solution to a problem with
> ground-truth model y = φ*(x, θ*) + ϵ, if φ̂ does not reduce to a constant, and if either of the
> following conditions are true: 1) φ* − φ̂ = a; or 2) φ*/φ̂ = b, b ≠ 0, for some constants a and b."

`SOURCE`, same section, the paper's own reliability disclaimer:
> "However, because models can be represented in myriad ways, and sympy's simplification procedure
> is non-optimal, we cannot guarantee that all symbolic solutions are captured with perfect
> fidelity by this metric."

`SOURCE`, Appendix A.5 "Additional Experiment Details" — **this is the budget**:
> "For the ground-truth problems, the final models from each method were given an additional hour
> of computing time with 8GB of RAM to be simplified with sympy and assessed by the solution
> criteria (see Def. 4.1)."

So SRBench's budget is **wall-clock (1 hour) plus a memory cap (8 GB)**. There is no node count,
no operation count, and no determinism claim. (`SOURCE`)

`SOURCE`, official repo `experiment/symbolic_utils.py` (fetched from
`https://raw.githubusercontent.com/cavalab/srbench/master/experiment/symbolic_utils.py`) line 221:
```python
model_sym = simplify(model_sym, ratio=1)
```
`ratio=1` is a **deterministic acceptance criterion on output size**, documented in SymPy's own
`simplify` docstring: "if (result length)/(input length) > ratio, then input is returned
unmodified", with `measure=count_ops` as the default length. (`SOURCE`, SymPy source
`sympy/simplify/simplify.py`.) `INFERENCE`: this bounds *output growth*, not *effort*, so it does
not make the check terminate deterministically and is not the budget C0002 needs.

### SRSD (the benchmark that reacted to SRBench's CAS problem)

- Title: **Rethinking Symbolic Regression Datasets and Benchmarks for Scientific Discovery**
- Authors: Yoshitomo Matsubara, Naoya Chiba, Ryo Igarashi, Yoshitaka Ushiku
- Status: arXiv **2206.10540** v5 (5 Mar 2024); reviewed on OpenReview
  https://openreview.net/forum?id=qrUdrXsiXX (TMLR)
- arXiv: https://arxiv.org/abs/2206.10540
- Official repository: https://github.com/omron-sinicx/srsd-benchmark
- `source.md` relationship: **absent**. Recommend adding.

`SOURCE`, abstract: they "propose to use normalized edit distances (NED) between a predicted
equation and the true equation trees for addressing a critical issue that existing SR metrics are
either binary or errors between the target values and an SR model's predicted values".

`SOURCE`, official repo `eq_comparator.py` (the file the paper's footnote 14 points at,
https://github.com/omron-sinicx/srsd-benchmark/blob/main/eq_comparator.py), `compare_equation`:
```python
p = Process(target=load_eq_as_tree, args=[est_eq_file_path, decrements_idx, False])
p.start()
p.join(timeout=120)
p.terminate()
if p.exitcode is None:
    print(f'Failed to load `{est_eq_file_path}`')
```
**A 120-second wall-clock timeout on a subprocess**, with failure mapped to maximal edit distance.
Same failure mode as C0001's `SIGALRM`: the outcome is a function of how long the call happened to
take. (`SOURCE`)

`SOURCE`, `load_eq_as_tree`:
```python
eq_sympy = eq_sympy.subs(sympy.pi, sympy.pi.evalf()).evalf().factor().simplify().subs(1.0, 1)
```
so SymPy is still used, but only to *canonicalize before* a deterministic tree comparison — not as
the decision rule. The decision rule itself is **Zhang–Shasha tree edit distance**:
- Kaizhong Zhang, Dennis Shasha, "Simple fast algorithms for the editing distance between trees and
  related problems", **SIAM Journal on Computing 18(6):1245–1262, 1989**, DOI
  **10.1137/0218082**.
`INFERENCE`: Zhang–Shasha is a deterministic dynamic program with a fixed `O(|T1|·|T2|·min(depth,
leaves)²)` cost. It is the one primitive in this literature whose result is *provably* independent
of wall clock, machine load and library cache state. That is a real precedent for C0002's
requirement, but it answers a **different question** (structural distance, not equivalence).

### SRBench 2025 / "Call for Action"

- Title: **Call for Action: Towards the Next Generation of Symbolic Regression Benchmark**
- Authors: Guilherme Seidyo Imai Aldeia, Hengzhe Zhang, Geoffrey Bomarito, Miles Cranmer,
  Alcides Fonseca, Bogdan Burlacu, William G. La Cava, Fabrício Olivetti de França
- arXiv **2505.03977** v1 (6 May 2025) · DOI https://doi.org/10.48550/arXiv.2505.03977
- Also GECCO '25 Companion, DOI https://doi.org/10.1145/3712255.3734309
- `source.md` relationship: **absent**.

`SOURCE`, §3.4 (model size), verbatim:
> "The expression was not simplified (except for trivial simplifications such as constant merging)
> before counting the nodes, as simplification using SymPy is unreliable and can increase the model
> size in the process [13]."

`INFERENCE`: the successor to SRBench explicitly **withdraws** from SymPy simplification where it
can, rather than budgeting it better. This is direct evidence that the field's response to the
problem C0002 is trying to fix has so far been avoidance, not a deterministic budget.

Their reference [13] is the equality-saturation work, which is the productive lead:

## Q3.2 The one place a deterministic resource bound for equivalence checking is specified

**Equality saturation over e-graphs.** This is the answer to "is there a primary source that
specifies a deterministic resource bound, and what is it?"

- Title: **egg: Fast and Extensible Equality Saturation**
- Authors: Max Willsey, Chandrakana Nandi, Yisu Remy Wang, Oliver Flatt, Zachary Tatlock,
  Pavel Panchekha
- Venue: **Proceedings of the ACM on Programming Languages, Vol. 5, Issue POPL, Article 23,
  pp. 1–29, January 2021** · DOI **10.1145/3434304**
- arXiv: https://arxiv.org/abs/2004.03082 (v3, 7 Nov 2020)
- Official implementation: https://github.com/egraphs-good/egg
- `source.md` relationship: **absent**.

`SOURCE`, §5.1, verbatim — this is the sentence that matters:
> "egg provides these functionalities through its Runner and Extractor interfaces. Runners
> automatically detect saturation, and can be configured to stop after a time, e-graph size, or
> iterations limit."

`SOURCE`, §5.3, on using it specifically as an *equality decision* procedure:
> "The Runner interface also supports user hooks that can stop the equality saturation after some
> arbitrary condition. This can be useful when using equality saturation to prove terms equal;
> once they are unified, there is no point in continuing."

`SOURCE`, the "Evaluating Rebuilding" experiment (p. 12), showing the deterministic budget in use
as a reported experimental quantity:
> "Of the 32 total tests, 8 hit the iteration limit of 100 and the remainder saturated."

`SOURCE`, §6.1, on what the prior wall-clock regime cost Herbie:
> "Herbie sharply limits the simplification process, placing a size limit on the e-graph itself and
> a time limit on the whole procedure. When the timeout is exceeded, simplification fails
> altogether."

**`INFERENCE`, and this is the concrete recommendation to Stage 3:** e-graph **size** (node count)
and **iteration count** are exactly the two deterministic budgets design brief §5.1 item 1 asks
for, they are first-class in a maintained official implementation, and they are used in this
literature *for term equality specifically*. The outcome under a node/iteration budget is a
function of the input terms and the rewrite set only — not of the clock, machine load, or library
cache state. Reaching the budget yields a principled third outcome ("not proved equal within
budget") that is reproducible by construction, which is precisely what
`analyses/C0001_endpoint_irreproducibility.md` shows `could_not_evaluate` is not.

**The bridge into symbolic regression already exists** (so this is not an exotic import):

- Fabrício Olivetti de França, Gabriel Kronberger, **"Reducing Overparameterization of Symbolic
  Regression Models with Equality Saturation"**, GECCO '23, Lisbon, pp. 1064–1072,
  DOI **10.1145/3583131.3590346**.
- Fabrício Olivetti de França, Gabriel Kronberger, **"Improving Genetic Programming for Symbolic
  Regression with Equality Graphs"**, arXiv **2501.17848**, https://arxiv.org/abs/2501.17848
  (GECCO '25). `SOURCE`, §1: equality saturation "can produce all the equivalent expressions of a
  given expression"; §3: "a single step of equality saturation is executed after inserting" each
  expression, because "if we apply more iterations, the e-graph can grow exponentially large" —
  i.e. the SR community already budgets e-graph work by **iteration count**, deterministically.
- `rEGGression`, GECCO '25, DOI https://doi.org/10.1145/3712256.3726385 — `unverified` contents;
  listed for navigation only.

## Q3.3 The other deterministic route the literature supports: a numerical certificate

C0001 already built a numerical fingerprint (seed `77771`, `mpmath.mp.dps = 40`, 10 points,
879 skeleton classes → 877 buckets, zero `BAD`/`ERR` fingerprints). The primary sources that give
this a soundness guarantee rather than a heuristic status:

- J. T. Schwartz, **"Fast Probabilistic Algorithms for Verification of Polynomial Identities"**,
  *Journal of the ACM* **27(4):701–717**, October 1980, DOI **10.1145/322217.322225**.
- Richard Zippel, **"Probabilistic algorithms for sparse polynomials"**, EUROSAM '79,
  Springer LNCS 72, pp. 216–226, DOI **10.1007/3-540-09519-5_72**.

`INFERENCE`: the Schwartz–Zippel bound gives a one-sided guarantee — *unequal* is certain up to a
bounded error probability, *equal* is never proved — which maps exactly onto the arbitration role
design brief §5.1 item 2 proposes, and it is fully deterministic once the evaluation points are
seeded. The caveat that must be written down: the bound is stated for **polynomials over a field**,
and the GRN skeletons are **rational functions with variable denominators**, so the clearing-of-
denominators step and the pole-avoidance argument have to be made explicit before the guarantee
transfers. I did not find a primary SR paper that does this. (`unverified`.)

## Q3.4 Two instrument facts about SymPy, from official source, that C0002 should record

Both were read from the official SymPy repository, not from documentation prose.

1. **`Expr.equals` is documented to return `None`.** `sympy/core/expr.py`, docstring verbatim:
   > "Return True if self == other, False if it does not, or None. If failing_expression is True
   > then the expression which did not simplify to a 0 will be returned instead of None."

   This confirms design brief §5.1 item 3: `bool(a.equals(b))` at
   `src/evaluation/equation_metrics.py:216-222` collapses a documented three-valued return to two.
   (`SOURCE`.)

2. **`Expr.equals` is internally randomised, from an unseeded module-level generator.** `SOURCE`,
   `sympy/core/expr.py`, inside `equals`:
   ```python
   if constant is True:
       # this gives a number whether there are free symbols or not
       ndiff = diff._random()
   ```
   and `_random` "replac[es] free symbols with random complex values … generated by the
   random_complex_number routine". `SOURCE`, `sympy/core/random.py`:
   ```python
   import random as _random
   rng = _random.Random()
   ```
   with the module docstring: *"There is intentionally no Random to import from here. If you want
   to control the state of the generator, import ``seed`` and call it with or without an
   argument to set the state."*

   **`INFERENCE`, and this is new to the campaign:** `rng` is a module-level `random.Random()`
   seeded from OS entropy at import time. Unless `sympy.core.random.seed(k)` is called, `.equals`
   is **not a deterministic function of its inputs**, independently of the `SIGALRM` clock and
   independently of the SymPy expression cache. This is a **third** candidate mechanism for the
   14/101,963 label flips, alongside the cache-state mechanism that
   `analyses/C0001_endpoint_irreproducibility.md` §4 supports and the CPU-contention mechanism it
   rejects in §3. It is also the cheapest to test and to fix: call
   `sympy.core.random.seed(<frozen value>)` in every worker and re-run the 2,191-pair census.
   `H0013`'s stated negative branch ("the source is not the clock") is therefore not a dead end —
   it has a named, testable second suspect. **This is a hypothesis, not a finding: the campaign has
   not yet shown that `_random` is reached on the flipping pairs.** Flagged for Stage 3.

## Q3.5 Answer to the question as asked

> *What do SR benchmarks and CAS-based equivalence protocols actually use — is there a primary
> source that specifies a deterministic resource bound, and what is it?*

- **In symbolic regression: no.** Every equivalence protocol I could verify uses wall clock —
  SRBench 1.0 (1 hour + 8 GB, Appendix A.5), SRSD (`p.join(timeout=120)` in the official
  `eq_comparator.py`). SRBench 2025 responds by *avoiding* SymPy simplification, and SRSD responds
  by *replacing* binary equivalence with deterministic Zhang–Shasha edit distance. ODEFormer itself
  avoids symbolic equivalence entirely in favour of `R² > 0.9` (already `SOURCE` in
  `C0001_literature.md`). (`SOURCE`)
- **Outside symbolic regression: yes, and it is directly importable.** egg (POPL 2021,
  DOI 10.1145/3434304) specifies **e-graph size and iteration limits** as first-class stopping
  criteria and names term-equality proving as a use case; the SR community has already adopted
  e-graphs (de França & Kronberger, GECCO '23 / arXiv 2501.17848) and already budgets them by
  iteration count. (`SOURCE`)
- **Novelty of C0002's move:** redefining `could_not_evaluate` on a node/operation budget is
  `adjacent` — the mechanism is standard in the equality-saturation and proof-assistant literature
  and already present in SR tooling, but I found **no primary source that applies a deterministic
  budget to the equivalence decision in an SR evaluation protocol**. Doing so, and reporting the
  label-set agreement distribution across worker arms, is `plausibly_novel` **as a protocol
  contribution** — and a methodological one, not a scientific finding. It should never be presented
  as a research result.

---

# Q4 — Prior-mass / support diagnostics for pretrained symbolic regression models

> *Has anyone, in a primary paper, measured the coverage of a pretrained SR model's candidate
> distribution against a target structural family it fails on — as opposed to reporting aggregate
> recovery rates?*

**Short answer: no — but three published near-neighbours each hold a piece, and one of them
(ND2) already computes a teacher-forced ground-truth probability under a pretrained SR model.**
The composite C0002 proposes is therefore `adjacent`, not `plausibly_novel`.

This section was researched by a delegated sweep that read the arXiv/proceedings full texts and
cloned the official repositories. Where a claim rests on a paywalled or unfetchable artifact, that
is said.

## Q4.1 NeSymReS — coverage exists, but against the *training* corpus

- Title: **Neural Symbolic Regression that Scales**
- Authors: Luca Biggio, Tommaso Bendinelli, Alexander Neitz, Aurelien Lucchi,
  Giambattista Parascandolo
- Venue: **ICML 2021, PMLR 139:936–945** · arXiv https://arxiv.org/abs/2106.06427
  (arXiv DOI 10.48550/arXiv.2106.06427; **no publisher DOI**, `unverified`)
- Official repository: https://github.com/SymposiumOrganization/NeuralSymbolicRegressionThatScales
- `source.md`: present at line 83 (paper + repo).

`SOURCE`, §4.4:
> "We checked our pre-training dataset, and amongst the 10 million equation skeletons, all
> equations from AIF appear."

> "Unseen Skeletons (SOOSE) This dataset of 200 equations is specifically constructed to have zero
> overlap with the pre-training set, meaning that its equations are all symbolically and
> numerically different from those included in the pre-training set."

`SOURCE`, official repo `nsr/scripts/data_creation/test_presence.py` module docstring, verbatim:
`Simple script that checks that no test equation are in the training dataset`

`SOURCE`, §4.4, the one support statement:
> "There are terms that appear in three ground truth equations that are not included in the set of
> equations that our model can fit, specifically x⁶, and x^y, which therefore caps the maximum
> accuracy that can be reached by our model on this dataset."

`INFERENCE`: skeleton-class coverage is an established, measurable unit in this literature — but
NeSymReS measures **generated-vs-training** overlap (a contamination control), and its one
expressibility statement is asserted at the vocabulary level, not measured as prior mass. A
repo-wide grep for `oracle|coverage|is_in_train|teacher` returned zero hits.

## Q4.2 ND2 / NDformer — the closest published analogue, and it *does* score the ground truth

- Title: **Discovering network dynamics with neural symbolic regression**
- Authors: Zihan Yu, Jingtao Ding (co-first), Yong Li
- Venue: ***Nature Computational Science* 6, 156–168**; received 2025-01-31, accepted 2025-09-19,
  published online 2025-10-23, February 2026 issue
- DOI: **10.1038/s43588-025-00893-8**
- Official repository: https://github.com/tsinghua-fib-lab/ND2 · Zenodo
  10.5281/zenodo.16995963 (DOI resolves; landing page `unverified`, 403 to automated fetch)
- **No arXiv preprint exists** (`SOURCE`, negative: four arXiv API queries over both author names
  returned no match; no preprint link on the Nature page or in the repo).
- `source.md`: present at line 53.

**Naming, settled** (`SOURCE`): **ND2 is the method; NDformer is the pretrained transformer inside
it** — the SI table of contents has "3 Details of NDformer / 3.1 Model architecture /
3.2 Pretraining", and repo `ND2/model/model.py:157` declares `class NDformer(nn.Module):`. They are
not separate works, and downstream C0002 artifacts should not treat "ND2/NDformer" as two
candidates. Three works are routinely confused with it and are **distinct** (`SOURCE`): LLC,
"Learning interpretable network dynamics via universal neural symbolic regression", *Nat Commun*,
DOI 10.1038/s41467-025-61575-7 (`source.md` line 62); PI-NDSR, "Neural Symbolic Regression of
Complex Network Dynamics", arXiv 2410.11185 (`source.md` line 71), which ND2 uses as a baseline;
and an unrelated image-deraining "NDFormer".

`SOURCE`, SI §3.2 — a **teacher-forced probability of ground-truth symbols under a pretrained SR
model**:
> "**Predicted probability** This metric represents the average probability of labels in the
> policies generated by the model, which is evaluated on the test set — i.e., the 10 considered
> model systems…"

`SOURCE`, Supplementary Fig. 6d, relating that prior mass to discovery success:
> "It is always possible to find the target formula when, as indicated by the green area, the
> predicted probability exceeds 6%, top-1 accuracy exceeds 25%, and top-5 accuracy exceeds 65%."

`SOURCE`, official repo `ND2/ND2/model/trainer.py:202` — the same quantity in code:
```python
loss_record.logprob = pd_policies.log_softmax(dim=-1) \
                                 .gather(dim=-1, index=index) \
                                 .squeeze(-1).tolist()
```
with `index = gt_policies.unsqueeze(-1)`, logged alongside `top1_acc` / `top5_acc`.

`SOURCE`, lexical scan of the 72-page SI: `coverage` 0, `oracle` 0, `prior mass` 0,
`log-probability` 0, `teacher forc` 0, `skeleton` 0, `reachab` 0. The 48,390-word Peer Review File
likewise returns 0 for `coverage` and `oracle` — **no reviewer raised the question either**.
Failures are reported only as aggregate success-rate grids (SI §6). Selection in
`ND2/search/mcts.py` is best-by-reward (`Best-RMSE`, `Best-R2`, `Best-Complexity`) — no
oracle-vs-selected split, i.e. rule 03's three-way distinction is absent from the paper.

The one coverage-adjacent admission is qualitative, from the rebuttal (`SOURCE`, Peer Review File):
> "Since the high-order interaction function 𝐻(𝑥ᵢ,𝑥ⱼ,𝑥ₖ,…) has more diverse combinations than the
> binary interaction function 𝐺(𝑥ᵢ,𝑥ⱼ), it is difficult to ensure that NDformer has seen enough
> meaningful high-order function forms to obtain generalization ability by pre-training it with
> only randomly generated formulas."

**How it differs from `H0001-R`** (`INFERENCE`): ND2's quantity is **token-level** average
probability, not a **sequence-level** `log p(ground truth)`; it is swept over **training
checkpoints**, not over held-out cells; and it is measured on the 10 systems ND2 **succeeds** on,
never on a family it fails on. It therefore cannot, and does not, separate prior-mass error from
search error. But the conceptual move — *measure the model's own probability mass on the target,
then relate it to search outcome* — **is already in print**, and that is what caps `H0001-R` at
`adjacent`.

⚠️ **Caveat carried forward:** the main article body is **paywalled and was not read**. SI §2–3
duplicate the Methods in more detail and are lexically silent, but a coverage analysis confined to
the main text cannot be fully excluded. `unverified`.

⚠️ **Incidental finding, flagged for the reproducibility auditor** (`SOURCE`, SI §3.3.1):
> "The basal probability of each symbol being sampled is shown in Supplementary Table 2, which is
> calculated based on their occurrence frequency in the 10 considered model systems."

`INFERENCE`: the pretraining sampling prior is calibrated on the same 10 systems later used to
report recovery and to measure NDformer's test-set predicted probability. This is not formula-level
leakage, but the guidance quality measured there is not an unconditioned generalization estimate.
It is recorded here only because LANSR has analysed ND2 since GPU_RUN3; it changes nothing in
C0002.

## Q4.3 TPSR — the sharpest gap: search improvement without any reachability measurement

- Title: **Transformer-based Planning for Symbolic Regression**
- Authors: Parshin Shojaee, Kazem Meidani, Amir Barati Farimani, Chandan K. Reddy
- Venue: **NeurIPS 2023**, Advances in Neural Information Processing Systems 36, pp. 45907–45919
- arXiv: **2303.06833** v5 (27 Oct 2023) https://arxiv.org/abs/2303.06833
  (arXiv DOI 10.48550/arXiv.2303.06833)
- Proceedings DOI **10.52202/075280-1990** — taken from the proceedings page; the OpenReview
  cross-check (`id=0rVXQEeFEL`) was bot-blocked, so treat as **`unverified`**
- Official repository: https://github.com/deep-symbolic-mathematics/tpsr
- `source.md`: repo present at line 548; **paper URL / arXiv ID / DOI absent** — recommend adding.

`SOURCE`, §4 research questions, all downstream: RQ1 "Does TPSR perform better than other decoding
strategies (beam search/sampling) and competing baseline methods over standard SR benchmark
datasets?"; RQ2 extrapolation/noise; RQ3 caching time; RQ4 MCTS component ablation. §4.2 metrics:
> "We evaluate our model using the following three metrics: R² score, accuracy to tolerance ω …
> and complexity"

`SOURCE`: full-PDF grep for `oracle|coverage|prior mass|reachab|ground truth (present|contained|appear)`
returns **zero hits**. Repo grep for `oracle|log_prob|teacher|coverage` over all `.py` returns only
beam-search internals (`def add(self, hyp, sum_logprobs)` in
`symbolicregression/model/transformer.py:996`; `nesymres/.../beam_search.py:202`) — hypothesis
scoring during decoding, never scoring of the ground truth.

`INFERENCE`: TPSR's entire thesis is that **better search over a fixed pretrained distribution**
yields better equations. It therefore presupposes that search error is the binding constraint, and
never measures whether it is. This is the strongest available literature argument that `H0001-R`
asks a question the field has **skipped** rather than settled — and it is why an E2 result would be
informative beyond LANSR.

## Q4.4 Sato & Sato — the converse measurement, with hard numbers

- Title (v2): **Can Test-time Computation Mitigate Reproduction Bias in Neural Symbolic
  Regression?**
- Authors: Shun Sato, Issei Sato (The University of Tokyo)
- Status: arXiv **2505.22081**, v1 2025-05-28, **v2 2026-02-02**; preprint, ICML-2026 format.
  DOI 10.48550/arXiv.2505.22081. No journal reference.
- Official repository: https://github.com/Shun-0922/Mem-Bias-NSR
- `source.md`: present at line 97 (as `CTC_NSR`).
- `SOURCE`: the repo README still carries the v1 title "…Mitigate **Memorization** Bias…" and the
  repo is named `Mem-Bias-NSR`. `INFERENCE`: the concept was renamed *memorization bias* →
  *reproduction bias* between v1 and v2. Cite the v2 title; expect the v1 name in code.

`SOURCE`, **Definition 5.1**, verbatim:
> "Given an output token sequence s, let e = seq⁻¹(s) be the original expression that is
> represented by s. If strip(e) ∈ E_templ, we say s is a reproduction of expressions seen during
> training."

where `strip` removes constants and `E_templ` is the set of constant-free expressions in the
**training** set. Appendix D adds Definition D.2 for `transformer4sr` using full expressions.

**This is set-membership of *generated* expressions in the *training* corpus — the mirror image of
the coverage question, not the coverage question.** (`INFERENCE`.)

`SOURCE`, measured percentages:

| Figure | Model | Result (verbatim) |
|---|---|---|
| Fig. 1 (left), §5.1 | NeSymReS | "After 1000 epochs of training, **over 97%** of the generated expression trees were direct copies from the training data" |
| Fig. 2, §5.2 | transformer4sr | "less than **12%** of the expressions generated by transformer4sr were novel expressions … and less than **6%** of the expressions had novel tree structures (excluding constants)" |
| App. F.1 Tab. 5 | NeSymReS | novel & R² > 0.99: **0.67%** at beam size 5; **6.25%** at beam size 150 |
| App. F.1 Tab. 5 | NeSymReS+TPSR | **2.02%** novel-and-accurate against **34.31%** novel-but-inaccurate (beam size 5) |

`SOURCE`, beam sizes: §5.1 "We set the beam size to 5 for this experiment."; §6.1 "…we conducted
experiments with a larger beam size of b = 150."; Appendix F.1 sweeps BS = 1, 5, 50, 100, 150.

`SOURCE`, §6.1, bearing directly on `H0003`:
> "Since increasing the beam size does not provide the model [with an] expanded search space,
> simply adopting a decoding strategy with a larger beam size will not alleviate reproduction
> bias."

`INFERENCE`: this is independent published evidence *against* `H0003` (temperature/beam sweep) and
*for* the design brief §4.8 decision to hold `H0003` until `H0001-R` reports. It is not about GRN
Hill structure, so it settles nothing for LANSR — but it removes any "we never tried more search"
objection to deferring `H0003`.

**Do they ever compute a teacher-forced log-probability of the ground truth? No.** (`SOURCE`,
three independent confirmations.)

1. Full-text grep for `log-?prob|log likelihood|teacher|perplexity` finds teacher forcing mentioned
   **once**, as a training detail only: "During training, cross-entropy loss is used as the
   objective function, and teacher forcing (Sutskever…)".
2. The only membership routine in the repo, `memorization_bias_analysis.py`, runs the wrong
   direction — it takes a **generated** expression and asks whether it is in the **training**
   dictionary:
   ```python
   def is_expression_in_train_data(eq_string, dataset_dict_path = "experiments/nopow_dataset_dict/dataset_dict.json"):
       infix = infix_to_standardized_prefix(eq_string)
       if str(infix) in dataset_dict:
           return True
   ```
3. Repo-wide grep for `log_prob|logprob|log_softmax|teacher|nll|score_target|gt_prob`: every hit is
   inside standard beam-search decoding. **No ground-truth scoring path exists.**

`SOURCE`: they report **no exact/symbolic recovery metric at all** (grep for
`exact recover|symbolic recover|exact match` returns zero); accuracy is R² thresholds only. Their
`make_test_set()` `not_included` split filters by whether the ground-truth prefix is absent from
the **training** dictionary — never whether it is absent from the model's candidate set.

`SOURCE`, **their own novelty claim**, Table 1: the column "Assessing Reproduction Bias" is `-` for
Biggio et al. (2021), Kamienny et al. (2022), Shojaee et al. (2023), Li et al. (2024) and
Bendinelli et al. (2023), and `✓` only for their own NSR-gvs. `INFERENCE`: the authors themselves
assert that no prior NSR paper assessed anything in this family of questions.

## Q4.5 Additional sweep beyond the four

- **"Explaining the Explainer: Understanding the Inner Workings of Transformer-based Symbolic
  Regression Models"**, arXiv **2602.03506** (3 Feb 2026) — `source.md` line 293 lists it as `TSRM`, the
  campaign's nearest interpretability neighbour. `SOURCE`, Fig. 8b: "with a beam size of 32, most
  correct solutions appear within the first three beams… Almost no correct solutions are found
  beyond beam 15"; Fig. 7: "a substantial portion of true formulas could not be recreated:
  **31.8%** without constants and **39.2%** with constants." `INFERENCE`: this is beam-**rank** of
  already-correct solutions plus a decoder round-trip failure rate. It is the closest thing to a
  generation-coverage number in the interpretability literature, but it neither conditions on a
  failed structural family nor uses teacher forcing. It is directly relevant to `H0006`: the
  31.8% / 39.2% re-creation failure is a **spelling / round-trip** failure, the same class of
  defect `H0006` audits, and it shows that class of defect is large enough to matter in published
  work.
- **"Analyzing Generalization in Pre-Trained Symbolic Regression"**, arXiv **2509.19849** — its
  OOPD shift is an **input-domain** hypercube shift, not a structural family; beam sizes 1–16
  reported as aggregate recovery. Grep for `oracle|log-probab|teacher` returns zero hits.
- **ODEFormer**, arXiv 2310.05573 — grep for
  `oracle|coverage|log-prob|teacher forc|prior mass|reachab` returns **zero hits**, consistent with
  what `C0001_literature.md` already recorded by absence.

## Q4.6 Answer to the question as asked

**`SOURCE`:** no primary paper performs the composite measurement — coverage of a *pretrained SR
model's realized candidate set* against a *structural family it fails on*, decomposed into
prior-mass versus search error. Across NeSymReS, TPSR, ODEFormer, Voigt et al. and the ND2 SI, a
grep for `oracle|coverage|prior mass|reachab` returns zero, and Sato & Sato's own Table 1 asserts
the same gap from the other side.

**`SOURCE`:** but three ingredients are each published — ND2 SI §3.2 (teacher-forced ground-truth
probability under a pretrained SR model, related to discovery success, with thresholds), NeSymReS
§4.4 (skeleton-class coverage as a measurable quantity, against training), Sato & Sato Def. 5.1
(structural-class membership as the unit of analysis for a pretrained SR decoder, with hard
percentages).

**Therefore `adjacent`, not `plausibly_novel`.** What is genuinely unclaimed (`INFERENCE`, and the
only framing a preregistration should use): applying coverage to the **realized candidate set at
inference** rather than the training corpus; conditioning on a structural family the model
**fails** on; and using **sequence-level** teacher-forced `log p(ground-truth skeleton)` to split
prior-mass error from search error.

---

# Q5 — Novelty labels for the design brief's §4 candidates

Assigned per the `literature-evidence` skill's four labels, weaker label preferred on doubt.
Absence from this repository is not used as evidence (rule 11).

## Q5.1 Summary table

| Candidate | What it measures | Label | One-line justification |
|---|---|---|---|
| **`H0001-R`** — E2 vs E3 by teacher-forced scoring | generation failure, internal decomposition | **`adjacent`** | The *method* (Stahlberg & Byrne) is `known`; the *application* — sequence-level `log p(truth)` under a pretrained SR transformer, related to search outcome — is already in print at token level in **ND2 SI §3.2 / Supp. Fig. 6d**. The unclaimed part is conditioning on a family the model fails on, and the sequence-level model/search split. |
| **`H0010`** — joint vs marginal substructure absence | generation failure, structure of the coverage hole | **`adjacent`** | Structural-class coverage of a pretrained SR decoder is established as a unit of analysis (**Sato & Sato Def. 5.1**, **NeSymReS §4.4 + `test_presence.py`**), but always **generated-vs-training**. Coverage against a **target family the model fails on**, decomposed into marginal predicates vs their conjunction, was not found in any primary source. `plausibly_novel` is arguable; the weaker label is taken per rule 11. |
| **`H0012`** — truth-vs-candidate trajectory-fit contest | identifiability / evaluator validity | **`adjacent`** | The *dissociation* is `known` and stated by the campaign's own model: ODEFormer Appendix G — "Increasing the beam size improves reconstruction, but not generalization" and generalization "is a much better proxy of symbolic recovery than the former". SRBench calls accuracy-based solution "an alternative (and weaker) notion of solution". SRBench 2025 observes ground truths outscored by more complex models on noisy data. **No source found runs the per-cell head-to-head census** across an observation window and a generalization window. |
| **`H0013`** — deterministic budget for the equivalence instrument | instrument reproducibility (not a scientific hypothesis) | **`adjacent`** mechanism / **`plausibly_novel`** as an SR protocol | Deterministic budgets for term equality are standard outside SR (**egg**, POPL 2021: "stop after a time, e-graph size, or iterations limit"; "useful when using equality saturation to prove terms equal") and e-graphs already reach SR (de França & Kronberger). **No SR evaluation protocol found applies a deterministic budget to the equivalence decision** — SRBench uses 1 h + 8 GB, SRSD uses `p.join(timeout=120)`. Methodological, never to be reported as a scientific finding. |
| **`H0006`** — encoding / spelling normalization audit | evaluator validity, precondition for the two above | **`known`** problem / **`adjacent`** audit | **Sato & Sato Remark 5.2** recognizes the structural-vs-functional equivalence hazard explicitly and engineers the operator set around it. **TSRM (arXiv 2602.03506) Fig. 7** measures a round-trip re-creation failure of **31.8% / 39.2%** — the same defect class, at a magnitude that matters. The specific ODEFormer prefix/infix `pow2∘pow2` vs `pow(·,4)` audit is unclaimed. |
| **`H0011`** — covariate structure of missing opportunity | descriptive, exploratory | **`unverified`** | No novelty is claimed and none should be. Design brief §4.6 already labels it exploratory (rule 01 item 9); it must stay labelled exploratory in every downstream artifact. |
| **`H0007`** — layer / token-role decomposition | layer representation + causal contribution | **out of scope here** | Evidence status unchanged by C0001. See `C0001_literature.md`; rule 04 forbids ranking it against the generation-side candidates. |

## Q5.2 The method-level label the design brief already assigned, confirmed

| Item | Brief's label | This record | Verdict |
|---|---|---|---|
| teacher-forced scoring as a search-error indicator | `known` | **`known`** | **confirmed** — Stahlberg & Byrne, DOI 10.18653/v1/D19-1331, verified in full. No novelty may be claimed for the method. |
| ODEFormer checkpoint generator support (F1) | existing fact, `unverified` sub-claim about pretraining | unchanged | The safe statement remains "probability 0 **under the checkpoint's own generator settings**". Nothing found changes this. Additional checkpoint facts in §Q2.6. |
| joint vs marginal substructure absence (`H0010`) | `unverified` | **`adjacent`** | **resolved from `unverified` to `adjacent`** — this is not a novelty upgrade; `adjacent` means near-neighbours exist, which is the *more* constraining finding. |
| truth-vs-candidate trajectory contest (`H0012`) | `unverified` | **`adjacent`** | same: near-neighbours exist, including in ODEFormer's own appendix. |
| constant-folding matcher for GRN components (C0001 subject) | `unverified` | **`unverified`** | not re-examined in this cycle; C0001 report §3's label stands. |

## Q5.3 What may and may not be claimed in C0002

`INFERENCE`, but binding on downstream artifacts unless Stage 3 overrules it with a source:

1. **No C0002 candidate may be described as novel.** The strongest available label for the two
   selected hypotheses (`H0001-R`, `H0010`) is `adjacent`. Design brief §8 item 8 is satisfied by
   this record, and the `unverified` labels it carried are now resolved **downward in novelty**,
   not upward.
2. **`H0001-R`'s framing must credit ND2.** Any claim of the form "we are the first to measure the
   model's own probability mass on the ground truth in symbolic regression" is **false**
   (ND2 SI §3.2). The defensible framing is the three-part gap in §Q4.6.
3. **`H0010`'s framing must credit Sato & Sato and NeSymReS.** Structural-class coverage of a
   pretrained SR decoder is published; only the *target* of the comparison is new.
4. **`H0013` must be reported as methodology.** It is an instrument repair with `adjacent`
   precedent in the equality-saturation literature. It is not a research result and must not appear
   in any results summary as one.
5. **Rule 03's three-way distinction must be carried at the endpoint-name level.** Q4 found that
   ND2 and TPSR both collapse it; that is the field norm this campaign is deliberately breaking
   with, and the distinction is worthless if the endpoint names do not encode it.
6. **Sato & Sato §6.1 may be cited when deferring `H0003`**, but only as evidence that larger beams
   did not relieve reproduction bias **for NeSymReS/transformer4sr on their corpora**. It is not
   evidence about ODEFormer on Hill-type GRN dynamics, and must not be written as if it were.



## Q5.4 Supporting quotation for the `H0006` label

`SOURCE`, Sato & Sato (arXiv 2505.22081) **Remark 5.2**, verbatim:
> "We have defined and measured reproduction bias based on whether the training dataset contains an
> expression that is structurally equivalent to the generated one. However, one may argue that we
> should define and measure reproduction based on functional equivalence; there are many
> expressions that are structurally different but functionally equivalent (e.g., x₁(x₁ + x₂) and
> x₁² + x₁x₂), and that such expressions should also be considered as equivalent expressions. To
> account for both structural and functional equivalence, we choose the operators as described
> below, so that any pair of structurally different expressions is also functionally different."

`INFERENCE`: this is the same hazard `H0006` addresses, recognized and **designed around** in a
primary NSR paper — they restricted the operator set so that structural inequality implies
functional inequality, which makes the CAS question disappear by construction. LANSR cannot take
that route: the operator set is fixed by the released ODEFormer checkpoint
(`sin:1,inv:1,pow2:1,id:3,add:3,mul:1`, `operators_to_not_repeat = ""`, already `SOURCE` in
`C0001_literature.md`), and the Hill family is precisely where `pow2∘pow2` and `pow(·,4)` collide.
So the *problem* is `known` and the *avoidance strategy* is published; the concrete audit —
enumerating the admissible prefix/infix spellings under a released checkpoint's own tokenizer and
re-running truth-in-beam over the resulting equivalence class — is `adjacent`, with no primary
source doing it for ODEFormer.

`INFERENCE`, consequence for Stage 3: Sato & Sato's route (choose operators so structure determines
function) and C0002's route (enumerate spellings, then match over the equivalence class) are the
two known ways out. The first is unavailable. The second is therefore not a nicety — it is the only
remaining option, which strengthens the case in §Q2.4 item 4 for `H0006` being a hard precondition
of `H0001-R` rather than a companion.

---

# Q6 — Recommended `source.md` additions

`source.md` (734 lines, 6 groups + a Tier 1–4 priority list) was cross-checked. None of the
following are in it. All are primary sources used above; adding them is a recommendation to the
supervisor, **not** an edit I made.

| Item | Where it belongs | Why |
|---|---|---|
| Stahlberg & Byrne 2019, DOI 10.18653/v1/D19-1331, https://aclanthology.org/D19-1331/ , impl. http://ucam-smt.github.io/sgnmt/html/ | group 6 (補助・基礎文献) | defines the search-error / model-error split the C0002 primary endpoint is built on |
| SRBench 1.0 — La Cava et al., NeurIPS 2021 D&B, https://arxiv.org/abs/2107.14351 , repo https://github.com/cavalab/srbench | group 5 (シンボリック回帰一般・比較手法) | the field-standard symbolic-solution definition and its wall-clock budget |
| SRSD — Matsubara et al., arXiv 2206.10540, repo https://github.com/omron-sinicx/srsd-benchmark | group 5 | replaces CAS equivalence with deterministic Zhang–Shasha NED; LANSR already uses TED |
| SRBench 2025 "Call for Action" — arXiv 2505.03977, DOI 10.1145/3712255.3734309 | group 5 | states SymPy simplification is unreliable, the reason C0002 is re-specifying the budget |
| egg — Willsey et al., POPL 2021, DOI 10.1145/3434304, arXiv 2004.03082, repo https://github.com/egraphs-good/egg | group 6 | the only primary source found specifying deterministic budgets (e-graph size / iterations) for term equality |
| de França & Kronberger, GECCO '23, DOI 10.1145/3583131.3590346 · and arXiv 2501.17848 | group 2 or 5 | the existing e-graph ↔ symbolic-regression bridge |
| Zhang & Shasha 1989, SIAM J. Comput. 18(6):1245–1262, DOI 10.1137/0218082 | group 6 | the algorithm behind the TED metric already used since GPU_RUN3; `source.md` line 139 cites the TED-with-variables paper but not the base algorithm |
| Schwartz 1980, JACM 27(4):701–717, DOI 10.1145/322217.322225 · Zippel 1979, LNCS 72:216–226, DOI 10.1007/3-540-09519-5_72 | group 6 | soundness basis for the numerical-certificate arbitration in design brief §5.1 item 2 |
| TPSR paper — arXiv 2303.06833, NeurIPS 36:45907–45919 | group 1 or 5, beside the existing repo link at line 548 | `source.md` line 548 gives only the repo URL; the paper has no entry |
| "Analyzing Generalization in Pre-Trained Symbolic Regression", arXiv 2509.19849 | group 5 | OOD generalization for pretrained SR; not currently listed |

`source.md` items **used and confirmed present** (line numbers verified by grep):
ODEFormer (line 43), ND2 (line 53), NeSymReS (line 83), CTC_NSR / reproduction bias (line 97),
GODE (line 109), TED (line 139), TPSR (line 548, repo URL).

Two **corrections** to how `source.md` entries should be read, both `SOURCE` (§Q4.2, §Q4.4):

- `source.md` line 53 (ND2) and the model name **NDformer** refer to the **same work**, not two.
  LLC (line 62) and PI-NDSR (line 71) are **different** papers and must not be merged with it.
- `source.md` line 97 (`CTC_NSR`, arXiv 2505.22081) should be cited by its **v2** title,
  "Can Test-time Computation Mitigate **Reproduction** Bias in Neural Symbolic Regression?".
  The v1 title said *Memorization* Bias and the official repository is still named
  `Mem-Bias-NSR`.

---

# Q7 — Verification failures and honest caveats

Recorded so a reviewer can tell what was actually checked from what was not.

1. `WebFetch` of `https://dl.acm.org/doi/10.1145/3434304` returned **HTTP 403**. The egg quotations
   above are from the arXiv v3 PDF (`https://arxiv.org/pdf/2004.03082`, downloaded and converted
   with `pdftotext`). Venue, volume, article number and DOI were confirmed from the POPL 2021
   programme page and the ACM listing metadata, **not** from the paywalled page itself. The arXiv
   v3 and the camera-ready are assumed identical in the quoted passages; that assumption is
   `unverified`.
2. `WebFetch` of `https://arxiv.org/pdf/2505.03977` and `https://arxiv.org/pdf/2505.22081` both
   returned only PDF object metadata (compressed streams). Both were re-fetched with `curl` and
   converted locally with `pdftotext`; all quotations come from the local conversions.
3. `WebFetch` of the SymPy docs page for `Expr.equals` did not contain the method. The `equals` and
   `_random` quotations are from the **official source**
   (`https://raw.githubusercontent.com/sympy/sympy/master/sympy/core/expr.py` and
   `.../sympy/core/random.py`), which is stronger evidence but tracks `master`, not the version
   pinned in this repository. SymPy is **not importable** in this environment
   (`ModuleNotFoundError: No module named 'sympy'` under the shell's default interpreter), so I
   could not confirm the pinned version's source matches `master` at these lines. Stage 3 must
   re-check against the environment SymPy actually used by `src/evaluation/equation_metrics.py`.
   `unverified`.
4. The de França & Kronberger GECCO '23 paper (DOI 10.1145/3583131.3590346) was **not** read in
   full; only its title, venue, pages and the fact that SRBench 2025 cites it as reference [13] for
   SymPy unreliability are `SOURCE`. The claim that the SR community budgets e-graph work by
   iteration count comes from the companion arXiv 2501.17848, which I did read. Any stronger claim
   about the GECCO '23 paper's own budget is `unverified`.
5. `rEGGression` (DOI 10.1145/3712256.3726385) is listed for navigation only; contents
   `unverified`.
6. The Schwartz–Zippel transfer to **rational** functions with variable denominators is not
   established by either cited paper and is not, as far as I found, established for SR anywhere.
   `unverified`. Do not cite the bound for the GRN skeletons without the clearing-of-denominators
   argument written out.
