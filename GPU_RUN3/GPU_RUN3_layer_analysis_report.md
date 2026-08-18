# GPU_RUN3 — NDformer layer-analysis report

Run ID: `gpu_run3_full_20260817`  
Provenance: `layer_analysis`

Interpretations are kept distinct throughout (plan section 6.6): a probe shows
information is linearly readable, ablation shows a block is required, activation
intervention shows it is causally influential, and IOLE shows it can adapt.

## 1. RQ3 — layer-wise information (Phase 4)

Probes fit on `analysis_train` and scored on `analysis_validation`; each score is paired with a shuffled-label control fitted the same way.

### Probe task: `next_symbol`

| layer | score | shuffled-label control | score - control |
|---|---|---|---|
| encoder.Transformer.layers.0 | 0.1129 | 0.0999 | 0.0130 |
| encoder.Transformer.layers.1 | 0.1317 | 0.0933 | 0.0385 |
| decoder.decoder.layers.0 | 0.4093 | 0.1012 | 0.3081 |
| decoder.decoder.layers.1 | 0.4124 | 0.0695 | 0.3430 |

### Probe task: `formula_root_operator`

| layer | score | shuffled-label control | score - control |
|---|---|---|---|
| encoder.Transformer.layers.0 | 0.2784 | 0.1642 | 0.1142 |
| encoder.Transformer.layers.1 | 0.2752 | 0.1393 | 0.1359 |
| decoder.decoder.layers.0 | 0.4875 | 0.1917 | 0.2958 |
| decoder.decoder.layers.1 | 0.3040 | 0.1382 | 0.1658 |

### Probe task: `partial_prefix_length`

| layer | score | shuffled-label control | score - control |
|---|---|---|---|
| encoder.Transformer.layers.0 | -3.1839 | -3.0616 | -0.1223 |
| encoder.Transformer.layers.1 | -3.2860 | -2.9904 | -0.2956 |
| decoder.decoder.layers.0 | -2.4652 | -3.0558 | 0.5906 |
| decoder.decoder.layers.1 | -2.5879 | -3.0725 | 0.4846 |

### Probe task: `tree_depth`

| layer | score | shuffled-label control | score - control |
|---|---|---|---|
| encoder.Transformer.layers.0 | -21.0773 | -18.4469 | -2.6305 |
| encoder.Transformer.layers.1 | -22.4742 | -18.0172 | -4.4569 |
| decoder.decoder.layers.0 | -20.0332 | -18.2669 | -1.7663 |
| decoder.decoder.layers.1 | -19.8221 | -18.1578 | -1.6643 |

### Probe task: `tree_size`

| layer | score | shuffled-label control | score - control |
|---|---|---|---|
| encoder.Transformer.layers.0 | -9.2265 | -8.2273 | -0.9992 |
| encoder.Transformer.layers.1 | -9.9717 | -8.2948 | -1.6769 |
| decoder.decoder.layers.0 | -8.9424 | -8.2618 | -0.6806 |
| decoder.decoder.layers.1 | -9.0084 | -8.3169 | -0.6915 |

### Probe task: `network_op_count`

| layer | score | shuffled-label control | score - control |
|---|---|---|---|
| encoder.Transformer.layers.0 | -0.3331 | -0.7874 | 0.4543 |
| encoder.Transformer.layers.1 | -0.2816 | -0.7587 | 0.4772 |
| decoder.decoder.layers.0 | -0.3503 | -0.7727 | 0.4224 |
| decoder.decoder.layers.1 | -0.1858 | -0.7920 | 0.6061 |

### Gradient norm and feature variation

| layer | gradient norm | per-parameter | parameters | within-problem variation |
|---|---|---|---|---|
| encoder.Transformer.layers.0 | 0.4048 | 0.0000 | 3152384 | 0.0000 |
| encoder.Transformer.layers.1 | 1.3570 | 0.0000 | 3152384 | 0.0000 |
| decoder.decoder.layers.0 | 1.0349 | 0.0000 | 4204032 | 0.1135 |
| decoder.decoder.layers.1 | 7.7150 | 0.0000 | 4204032 | 0.0214 |

Encoder activations do not depend on the decoded prefix, so their within_problem_feature_variation is ~0 and example-level tasks such as next_symbol are only informative for decoder blocks.

### CKA (problem-level representations)

| pair | CKA |
|---|---|
| decoder.decoder.layers.0||decoder.decoder.layers.0 | 1.0000 |
| decoder.decoder.layers.0||decoder.decoder.layers.1 | 0.8566 |
| decoder.decoder.layers.1||decoder.decoder.layers.1 | 1.0000 |
| encoder.Transformer.layers.0||decoder.decoder.layers.0 | 0.5794 |
| encoder.Transformer.layers.0||decoder.decoder.layers.1 | 0.6235 |
| encoder.Transformer.layers.0||encoder.Transformer.layers.0 | 1.0000 |
| encoder.Transformer.layers.0||encoder.Transformer.layers.1 | 0.8539 |
| encoder.Transformer.layers.1||decoder.decoder.layers.0 | 0.6122 |
| encoder.Transformer.layers.1||decoder.decoder.layers.1 | 0.6829 |
| encoder.Transformer.layers.1||encoder.Transformer.layers.1 | 1.0000 |

## 2. RQ6 — where formula structure forms (Phase 5)

### Encoder intermediate decode

| layer | n | true-symbol rank | true-symbol prob. | top-1 | entropy | mean TED |
|---|---|---|---|---|---|---|
| encoder.Transformer.layers.0 | 213 | 34.9155 | 0.0288 | 0.0423 | 1.9195 | 31.0571 |
| encoder.Transformer.layers.1 | 213 | 5.5211 | 0.2931 | 0.3944 | 1.9891 | 8.8889 |

### Decoder logit lens

| layer | n | true-symbol rank | true-symbol prob. | top-1 | entropy | mean TED |
|---|---|---|---|---|---|---|
| decoder.decoder.layers.0 | 213 | 20.0704 | 0.0254 | 0.0235 | 0.0881 | NaN |
| decoder.decoder.layers.1 | 213 | 5.5211 | 0.2931 | 0.3944 | 1.9891 | NaN |

encoder_intermediate_decode feeds each encoder block's memory to the trained decoder; it follows DecoderLens in spirit but is not the identical method, since NDformer has no per-layer decoder alignment.

Failures: 0

## 3. RQ4 — causal layer contribution (Phase 6)

Panel: 16 validation problems, seed 101. Baseline CE 2.2734, top-1 0.3826.

### Layer effects (delta vs the same panel's baseline)

| layer | dCE skip | dCE zero | dCE mean | dCE patch | dtop1 skip | dtrue-prob skip |
|---|---|---|---|---|---|---|
| encoder.Transformer.layers.0 | 0.5599 | 1.2863 | 1.3498 | 1.3569 | -0.1369 | -0.1618 |
| encoder.Transformer.layers.1 | 5.8845 | 1.2633 | 1.2648 | 0.9797 | -0.2921 | -0.2163 |
| decoder.decoder.layers.0 | 0.6536 | 1.3440 | 1.1367 | 1.0421 | -0.1717 | -0.1300 |
| decoder.decoder.layers.1 | 23.2857 | 1.8209 | 0.9459 | 1.1595 | -0.3769 | -0.2752 |

### IOLE single-layer fine-tuning

| condition | cross entropy |
|---|---|
| frozen | 2.2734 |
| iole::encoder.Transformer.layers.0 | 2.2631 |
| iole::encoder.Transformer.layers.1 | 2.2263 |
| iole::decoder.decoder.layers.0 | 2.1941 |
| iole::decoder.decoder.layers.1 | 2.1606 |
| full | 2.1766 |

### Parameter update sensitivity (controlled full fine-tune)

| layer | ||dtheta|| | ||theta|| | relative |
|---|---|---|---|
| encoder.Transformer.layers.0 | 1.1047 | 114.5875 | 0.0096 |
| encoder.Transformer.layers.1 | 1.0478 | 89.0321 | 0.0118 |
| decoder.decoder.layers.0 | 1.3862 | 148.6212 | 0.0093 |
| decoder.decoder.layers.1 | 1.2249 | 106.0741 | 0.0115 |

## 4. RQ5/RQ7 — layer ranking and selective fine-tuning (Phase 7)

Consensus ranking (frozen on validation): decoder.decoder.layers.1, encoder.Transformer.layers.1, decoder.decoder.layers.0, encoder.Transformer.layers.0

Ranking sources: {"probe": "ok", "gradient": "ok", "decoderlens": "ok", "iole": "ok", "ablation": "ok", "intervention": "ok", "update_sensitivity": "ok"}

### Ranking agreement

| pair | spearman | kendall | top-3 overlap |
|---|---|---|---|
| probe_vs_gradient | 0.8000 | 0.6667 | 1.0000 |
| probe_vs_decoderlens | 0.0000 | 0.0000 | 0.6667 |
| probe_vs_iole | 1.0000 | 1.0000 | 1.0000 |
| probe_vs_ablation | 0.8000 | 0.6667 | 1.0000 |
| probe_vs_intervention | -1.0000 | -1.0000 | 0.6667 |
| probe_vs_update_sensitivity | 0.0000 | 0.0000 | 0.6667 |
| gradient_vs_decoderlens | 0.6000 | 0.3333 | 0.6667 |
| gradient_vs_iole | 0.8000 | 0.6667 | 1.0000 |
| gradient_vs_ablation | 1.0000 | 1.0000 | 1.0000 |
| gradient_vs_intervention | -0.8000 | -0.6667 | 0.6667 |
| gradient_vs_update_sensitivity | 0.6000 | 0.3333 | 0.6667 |
| decoderlens_vs_iole | 0.0000 | 0.0000 | 0.6667 |
| decoderlens_vs_ablation | 0.6000 | 0.3333 | 0.6667 |
| decoderlens_vs_intervention | 0.0000 | 0.0000 | 0.6667 |
| decoderlens_vs_update_sensitivity | 1.0000 | 1.0000 | 1.0000 |
| iole_vs_ablation | 0.8000 | 0.6667 | 1.0000 |
| iole_vs_intervention | -1.0000 | -1.0000 | 0.6667 |
| iole_vs_update_sensitivity | 0.0000 | 0.0000 | 0.6667 |
| ablation_vs_intervention | -0.8000 | -0.6667 | 0.6667 |
| ablation_vs_update_sensitivity | 0.6000 | 0.3333 | 0.6667 |
| intervention_vs_update_sensitivity | 0.0000 | 0.0000 | 0.6667 |

### RQ5 random control

`random_3` drew ['decoder.decoder.layers.0', 'decoder.decoder.layers.1', 'encoder.Transformer.layers.1'] and `top_3` is ['decoder.decoder.layers.0', 'decoder.decoder.layers.1', 'encoder.Transformer.layers.1']; the two sets are identical. With 4 ranked blocks there are only a few 3-subsets, so a random draw of 3 overlaps the top 3 by construction and the k=3 comparison cannot answer RQ5 on this architecture.

At k=1 the comparison is well posed, using the Phase 6 IOLE sweep (every block trained alone under the same budget) as the distribution a random single-layer choice draws from:

| quantity | cross entropy |
|---|---|
| top_1 (decoder.decoder.layers.1) | 2.1606 |
| expected random single layer (mean over blocks) | 2.2110 |
| advantage of top_1 | 0.0504 |
| worst single layer | 2.2631 |
| best single layer | 2.1606 |

### Validation fine-tuning comparison

| condition | layers | trainable ratio | CE | top-1 | top-5 | train s |
|---|---|---|---|---|---|---|
| frozen | none | 0.0000 | 2.1593 | 0.3901 | 0.7943 | 0.0000 |
| full | all | 1.0000 | 2.0201 | 0.4397 | 0.8156 | 11.9679 |
| top_1 | decoder.decoder.layers.1 | 0.2373 | 2.0331 | 0.4113 | 0.8085 | 7.3349 |
| top_3 | decoder.decoder.layers.1, encoder.Transformer.layers.1, decoder.decoder.layers.0 | 0.6526 | 2.0384 | 0.4326 | 0.8227 | 8.4307 |
| random_3 | encoder.Transformer.layers.1, decoder.decoder.layers.0, decoder.decoder.layers.1 | 0.6526 | 2.0392 | 0.4184 | 0.8227 | 8.4071 |

## 5. Final held-out test (Phase 8)

analysis_test problems: 24. Evaluated once, after every method, layer ranking and budget was frozen on validation.

| metric | official checkpoint on test |
|---|---|
| cross entropy | 2.2599 |
| top-1 | 0.3600 |
| top-5 | 0.7822 |
| valid rate | 1.0000 |
| examples | 225 |

### Frozen conditions on the test split

| condition | trainable ratio | CE | top-1 | MCTS exact | MCTS mean TED |
|---|---|---|---|---|---|
| frozen | 0.0000 | 2.2599 | 0.3600 | 0 | 12.5000 |
| full | 1.0000 | 2.0744 | 0.4444 | 0 | 11.0000 |
| top_1 | 0.2373 | 2.0940 | 0.4044 | 0 | 12.0000 |
| top_3 | 0.6526 | 2.1383 | 0.4089 | 0 | 11.0000 |
| random_3 | 0.6526 | 2.1343 | 0.4044 | 0 | 10.0000 |

## 6. RQ8 — distance to the pretraining distribution (Phase 9)

| item | value |
|---|---|
| queries | 44 |
| catalog size | 800 |
| catalog source | GDExpr.random_fill_expr (official pretraining grammar) |
| mean retrieved_nearest_ted (skeleton) | 3.9773 |
| mean retrieved_nearest_ted (raw) | 4.1591 |

Approximate retrieval over a sampled catalog from the official formula grammar, not the full 1M-sample pretraining archive; reported as retrieved_nearest_ted per plan section 12.

