# GPU_RUN3 — ND2 reproduction report

Run ID: `gpu_run3_extended_1800s_groupB_20260818`  
Campaign: GPU_RUN3  
Provenance: `upstream_reproduction`

## 1. Environment and provenance

| item | value |
|---|---|
| LANSR commit | 8ec8b5d6f8d54e8212d0812f06a74dbb72ba3aef |
| ND2 upstream | https://github.com/tsinghua-fib-lab/ND2 |
| ND2 package fingerprint | 2b6c1b825ab56123a09bf05963da522fa9e7be8e85888e455ca0544650de4c22 |
| checkpoint SHA256 | 619d419b449a309c97d5b9ab6b8c9f53c91b45a409a3a9bf5b6ac79cb4f625d4 |
| Zenodo | 10.5281/zenodo.16995963 |
| Python | 3.10.20 |
| PyTorch | 2.5.1+cu124 |
| CUDA | 12.4 |
| GPU | NVIDIA GeForce RTX 2070 |
| CPU | Intel(R) Core(TM) i7-8700 CPU @ 3.20GHz |
| device | cuda |
| timestamp (UTC) | 2026-08-18T01:16:28.941489+00:00 |

### NDformer architecture

| item | value |
|---|---|
| encoder Transformer blocks | 2 |
| decoder Transformer blocks | 2 |
| total parameters | 17715713 |
| ranking layers | encoder.Transformer.layers.0, encoder.Transformer.layers.1, decoder.decoder.layers.0, decoder.decoder.layers.1 |

### Go conditions (Phase 0)

| condition | result |
|---|---|
| checkpoint_load_ok | yes |
| forward_ok | yes |
| policy_shape_ok | yes |
| vocab_ok | yes |
| parser_ok | yes |
| mcts_valid_formula_ok | yes |

## 2. RQ2 — NDformer policy reproduction (Phase 1)

> `phase1/summary.json` is missing from this run directory; the section below is incomplete.

## 3. Pipeline reproduction (Phase 2, KUR)

> `phase2/summary.json` is missing from this run directory; the section below is incomplete.


## 4. RQ1 — synthetic benchmark reproduction (Phase 3)

| metric | value |
|---|---|
| seeds | 101, 202, 303 |
| guided runs | 9 |
| systems | 3 |
| valid | 9 |
| exact recoveries | 0 |
| skeleton recoveries | 0 |
| mean ted_raw | 13.2222 |
| mean R2 | 0.7875 |

### Per system

`exact` / `skeleton` / `mean TED` are recanonicalized (section 5);
`exact (recorded)` is what Phase 3 wrote before that pass.

| system | n | valid | exact | exact (recorded) | skeleton | mean TED | mean RMSE | mean R2 | mean nodes | mean s |
|---|---|---|---|---|---|---|---|---|---|---|
| coupled_Rossler | 3 | 3 | 0 | 0 | 0 | 14.6667 | 1.4685 | 0.7484 | 7121.3333 | 1800.5848 |
| homogeneous_coupled_Rossler | 3 | 3 | 1 | 0 | 1 | 5.3333 | 0.3259 | 0.9816 | 11365.6667 | 1801.9927 |
| mutualistic_population | 3 | 3 | 0 | 0 | 0 | 15.3333 | 4.2910 | 0.6324 | 10781.3333 | 1803.3161 |

### True vs recovered formulas

**coupled_Rossler**

- true: `((0.5000*aggr(sin((sour(x)-targ(x)))))-(z+(omega*y)))`
- predicted (run 1): `(((0.0679*x)+((omega*y)*-0.8720))-z)`
- predicted (run 2): `(((-0.7841*z)-(-0.3016*sin(x)))+(-0.7185*(omega*y)))`
- predicted (run 3): `(((-0.6543*y)*omega)-z)`

**homogeneous_coupled_Rossler**

- true: `((0.5000*aggr(sin((sour(x)-targ(x)))))-(y+z))`
- predicted (run 1): `(((-1.0000*z)-y)+(0.5000*aggr(sin((sour(x)-targ(x))))))`
- predicted (run 2): `((y*-0.9946)+(0.4991*aggr(sin((sour(x)-((1/5)+targ(x)))))))`
- predicted (run 3): `((y*-0.9924)+(0.5104*aggr(sin((sour((x+-0.1583))-targ(x))))))`

**mutualistic_population**

- true: `((x*(alpha-(theta*x)))+aggr((sour(regular(x, 2))*targ(x))))`
- predicted (run 1): `(((-1.5056-x)*(3.0579*theta))+(4.8996*aggr(sour((1.3769-alpha)))))`
- predicted (run 2): `((((alpha**3)*6.1279)-x)+(2.0826*aggr((sour(theta)/targ(theta)))))`
- predicted (run 3): `((((x*-4.6792)*-0.6096)+(-0.5184*((x**2)*theta)))-alpha)`

## 5. Structural metrics under one canonicalization

Phases can be written under different canonicalization revisions, so every
stored formula is re-scored once, uniformly, from its saved prefix. Constants
are compared at 4 significant digits and the identities
0+x -> x, x-0 -> x, 1*x -> x, 0*x -> 0, x/1 -> x, x**1 -> x are folded (tolerance 0.0001).

| metric | as recorded | recanonicalized |
|---|---|---|
| exact recoveries | 0 | 1 |
| records re-scored | 9 | 9 |
| records whose score changed | - | 5 |
| skeleton recoveries | - | 1 |

### Re-scored records

| problem | condition | exact | skeleton | TED | was exact | was TED | RMSE |
|---|---|---|---|---|---|---|---|
| phase3_CR_s101_ndformer_mcts | ndformer_mcts | 0.0000 | 0.0000 | 14.0000 | 0.0000 | 15.0000 | 1.4446 |
| phase3_HCR_s101_ndformer_mcts | ndformer_mcts | 1.0000 | 1.0000 | 0.0000 | 0.0000 | 9.0000 | 0.0000 |
| phase3_MP_s101_ndformer_mcts | ndformer_mcts | 0.0000 | 0.0000 | 15.0000 | 0.0000 | 15.0000 | 3.4161 |
| phase3_CR_s202_ndformer_mcts | ndformer_mcts | 0.0000 | 0.0000 | 16.0000 | 0.0000 | 15.0000 | 1.4803 |
| phase3_HCR_s202_ndformer_mcts | ndformer_mcts | 0.0000 | 0.0000 | 8.0000 | 0.0000 | 10.0000 | 0.4875 |
| phase3_MP_s202_ndformer_mcts | ndformer_mcts | 0.0000 | 0.0000 | 16.0000 | 0.0000 | 16.0000 | 3.8405 |
| phase3_CR_s303_ndformer_mcts | ndformer_mcts | 0.0000 | 0.0000 | 14.0000 | 0.0000 | 14.0000 | 1.4807 |
| phase3_HCR_s303_ndformer_mcts | ndformer_mcts | 0.0000 | 0.0000 | 8.0000 | 0.0000 | 10.0000 | 0.4901 |
| phase3_MP_s303_ndformer_mcts | ndformer_mcts | 0.0000 | 0.0000 | 15.0000 | 0.0000 | 15.0000 | 5.6162 |

## 6. Reading these numbers

- Fit error and formula recovery are reported separately: a low RMSE does not
  mean the true network dynamics formula was recovered (plan section 6.5).
- Every run is stored per problem in `phase3/records.jsonl`, including failures,
  timeouts and invalid formulas (plan section 6.4).
- KUR's official network file ships only in the Zenodo archive; when it is absent
  the run falls back to an Erdos-Renyi graph and flags `used_er_fallback`.

