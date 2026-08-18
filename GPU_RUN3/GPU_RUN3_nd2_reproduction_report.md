# GPU_RUN3 — ND2 reproduction report

Run ID: `gpu_run3_full_20260817`  
Campaign: GPU_RUN3  
Provenance: `upstream_reproduction`

## 1. Environment and provenance

| item | value |
|---|---|
| LANSR commit | 20e2b621e007bc46d3e06e25bb01aecf4142770f |
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
| timestamp (UTC) | 2026-08-17T12:35:10.448166+00:00 |

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

| metric | value |
|---|---|
| split | analysis_validation |
| seeds | 101, 202, 303 |
| problems | 65 |
| teacher-forcing examples | 601 |
| valid rate | 1.0000 |
| cross entropy | 2.0966 |
| top-1 accuracy | 0.3900 |
| top-5 accuracy | 0.7834 |
| mean true-symbol rank | 5.6392 |
| mean true-symbol probability | 0.2974 |
| mean policy entropy | 1.9249 |
| std of CE across problems | 0.7854 |

Per seed:

| seed | problems | examples | CE | top-1 | top-5 | valid rate |
|---|---|---|---|---|---|---|
| 101 | 21 | 175 | 1.8692 | 0.4426 | 0.8335 | 1.0000 |
| 202 | 22 | 199 | 2.2938 | 0.3709 | 0.7351 | 1.0000 |
| 303 | 22 | 227 | 2.1166 | 0.3588 | 0.7838 | 1.0000 |

Policy-level failures: none

## 3. Pipeline reproduction (Phase 2, KUR)

| item | value |
|---|---|
| true formula | (omega0+(1.0000*aggr(sin((sour(x)-targ(x)))))) |
| predicted formula (guided) | ((0.0000+omega0)+(1.0000*aggr(sin((sour(x)-targ(x)))))) |
| valid | yes |
| exact | 0.0000 |
| ted_raw | 5.0000 |
| ted_skeleton | 4.0000 |
| fit error (RMSE) | 0.0000 |
| search nodes | 2311 |
| candidates | 11038 |
| wall time (s) | 288.7552 |
| failure reason | - |
| network | {"V": 50, "E": 200, "directed": false, "dag": false, "used_er_fallback": true} |

Unguided (uniform) MCTS control on the same problem and budget:

| item | value |
|---|---|
| pred | (-0.7865*(-(-0.2508+omega0))) |
| exact | 0.0000 |
| ted_raw | 10.0000 |
| fit_error | 1.2075 |
| search_nodes | 3564 |
| candidate_count | 25312 |
| wall_time | 300.0486 |

## 4. RQ1 — synthetic benchmark reproduction (Phase 3)

| metric | value |
|---|---|
| seeds | 101, 202, 303 |
| guided runs | 30 |
| systems | 10 |
| valid | 30 |
| exact recoveries | 0 |
| skeleton recoveries | 0 |
| mean ted_raw | 12.9333 |
| mean R2 | 0.8602 |

### Per system

`exact` / `skeleton` / `mean TED` are recanonicalized (section 5);
`exact (recorded)` is what Phase 3 wrote before that pass.

| system | n | valid | exact | exact (recorded) | skeleton | mean TED | mean RMSE | mean R2 | mean nodes | mean s |
|---|---|---|---|---|---|---|---|---|---|---|
| Kuramoto | 3 | 3 | 3 | 0 | 3 | 0.0000 | 0.0000 | 1.0000 | 1365.3333 | 177.2245 |
| coupled_Rossler | 3 | 3 | 0 | 0 | 0 | 14.3333 | 1.4919 | 0.7431 | 1051.0000 | 301.9998 |
| homogeneous_coupled_Rossler | 3 | 3 | 0 | 0 | 0 | 14.6667 | 1.5118 | 0.7509 | 2233.3333 | 301.7893 |
| FitzHugh_Nagumo | 3 | 3 | 0 | 0 | 0 | 16.6667 | 0.2987 | 0.8383 | 2501.3333 | 227.7648 |
| Wilson_Cowan | 3 | 3 | 0 | 0 | 0 | 14.6667 | 0.0104 | 0.9997 | 1841.0000 | 302.1213 |
| gene_regulatory | 3 | 3 | 0 | 0 | 0 | 15.3333 | 0.1108 | 0.9992 | 1331.6667 | 300.6000 |
| Michaelis_Menten | 3 | 3 | 2 | 0 | 2 | 3.0000 | 0.0005 | 1.0000 | 988.3333 | 187.2095 |
| Lotka_Volterra | 3 | 3 | 0 | 0 | 0 | 22.3333 | 0.0708 | 0.9210 | 1276.0000 | 300.7838 |
| mutualistic_population | 3 | 3 | 0 | 0 | 0 | 18.0000 | 4.8364 | 0.5448 | 2085.0000 | 300.9126 |
| susceptible_infected_susceptible | 3 | 3 | 0 | 0 | 0 | 13.3333 | 0.2522 | 0.8049 | 3946.0000 | 300.8392 |

### True vs recovered formulas

**Kuramoto**

- true: `(omega0+(1.0000*aggr(sin((sour(x)-targ(x))))))`
- predicted (run 1): `((-0.0000+omega0)+(1.0000*aggr(sin((sour(x)-targ(x))))))`
- predicted (run 2): `((omega0+-0.0000)+(1.0000*aggr(sin((sour(x)-targ(x))))))`
- predicted (run 3): `((1.0000*omega0)+(1.0000*aggr(sin((sour(x)-targ(x))))))`

**coupled_Rossler**

- true: `((0.5000*aggr(sin((sour(x)-targ(x)))))-(z+(omega*y)))`
- predicted (run 1): `(((0.8374*omega)*(sigmoid(x)-y))-(z*1.2134))`
- predicted (run 2): `(-((((0.0235*x)-(y*omega))+(-z))*-0.7245))`
- predicted (run 3): `(((-0.6543*y)*omega)-z)`

**homogeneous_coupled_Rossler**

- true: `((0.5000*aggr(sin((sour(x)-targ(x)))))-(y+z))`
- predicted (run 1): `((0.1504-z)+(-0.7758*y))`
- predicted (run 2): `((((-0.5259*y)+(-0.9319*z))-(0.0490*x))+(-0.0087*(y**3)))`
- predicted (run 3): `(((-0.7387*y)+(0.4177*sin(x)))-z)`

**FitzHugh_Nagumo**

- true: `(x-((y+(x**3))+(aggr((sour(x)-targ(x)))/aggr(1))))`
- predicted (run 1): `(((-4.3513*x)+(6.1830*sin(x)))-(0.8878*(y+-0.3304)))`
- predicted (run 2): `(((4.8078*sin(x))-(y*0.6805))-(3.4839*x))`
- predicted (run 3): `(((x-y)-(x**3))+(-0.1111*aggr((sour(x)-targ(x)))))`

**Wilson_Cowan**

- true: `(aggr(sour(sigmoid(((5.1000*x)-5.1000))))-x)`
- predicted (run 1): `((0.0007-x)+(1.0015*aggr(sigmoid(sour((8.1096-((-3.8503+x)**2)))))))`
- predicted (run 2): `((x*-0.9992)+(0.9991*aggr(sour(sigmoid((-0.9613+(x**3)))))))`
- predicted (run 3): `(((-x)*1.0018)+(1.0032*aggr(sour(regular(((x**2)**2), 1.5693)))))`

**gene_regulatory**

- true: `((0.2000+(2.0000*aggr(sour(regular((0.6667*x), 2)))))-(0.9000*x))`
- predicted (run 1): `((x*-0.9021)+(2.0230*aggr(regular(sour((x/1.4850)), 1.9677))))`
- predicted (run 2): `((0.3093-x)+(4.5180*aggr(sour(sigmoid((-1.8000/x))))))`
- predicted (run 3): `((0.3501-x)+(1.9495*aggr(sour((2.3124*sigmoid((-2.3907/(1.3249*x))))))))`

**Michaelis_Menten**

- true: `(aggr(sour(regular(x, 2)))-x)`
- predicted (run 1): `((-1.0000*x)+(1.0000*aggr(sour(regular(x, 2)))))`
- predicted (run 2): `((-0.0058-x)+(1.0065*aggr(sour(regular(x, 1.9459)))))`
- predicted (run 3): `((-1.0000*x)+(0.0000+aggr(sour(regular(x, 2.0000)))))`

**Lotka_Volterra**

- true: `((x*(alpha-(theta*x)))-aggr((sour(x)*targ(x))))`
- predicted (run 1): `(((((((1.1371*alpha)+(0.0310*theta))+x)-alpha)-(0.3566*aggr(targ(x))))-(0.6916*x))-(0.7377*(sin(alpha)-(alpha**2))))`
- predicted (run 2): `(x*(sin(alpha)-(sin((((alpha*theta)**2)+0.3509))*aggr(sour(((-(x+sigmoid(alpha)))**2))))))`
- predicted (run 3): `((((((alpha-sin(x))+x)+(-1.9617*alpha))-(0.3259*aggr(targ(x))))+(0.9154*alpha))+(0.2388*theta))`

**mutualistic_population**

- true: `((x*(alpha-(theta*x)))+aggr((sour(regular(x, 2))*targ(x))))`
- predicted (run 1): `(((-4.2793*x)*(-0.0895-sin((-theta))))+(8.1084*aggr(sour(sigmoid((aggr(targ(alpha))/(-2.7594*x)))))))`
- predicted (run 2): `(((0.0446*x)-(-5.8091*alpha))+(-2.3585*aggr(sour(sin((theta*(-0.7327*x)))))))`
- predicted (run 3): `((sin(theta)+(x*((-4.4216*theta)--2.8492)))+(alpha+((theta-(x**2))*0.0525)))`

**susceptible_infected_susceptible**

- true: `(aggr(((1-targ(x))*sour(x)))-(delta*x))`
- predicted (run 1): `(((-0.7972*x)*delta)+(0.4959*aggr((sour((x/x))-targ(x)))))`
- predicted (run 2): `((((8.4425*sigmoid(x))-(0.5349*delta))-(7.3123*x))-(-0.2356*aggr(sour((x**3)))))`
- predicted (run 3): `((x*-2.8985)+(5.7352*sin(tan(sigmoid((delta*-0.2348))))))`

### NDformer guidance vs unguided MCTS

| item | value |
|---|---|
| n | 10 |
| n_exact | 0 |
| mean_ted_raw | 18.3000 |
| mean_r2 | 0.5755 |
| mean_search_nodes | 4102.9000 |

## 5. Structural metrics under one canonicalization

Phases can be written under different canonicalization revisions, so every
stored formula is re-scored once, uniformly, from its saved prefix. Constants
are compared at 4 significant digits and the identities
0+x -> x, x-0 -> x, 1*x -> x, 0*x -> 0, x/1 -> x, x**1 -> x are folded (tolerance 0.0001).

| metric | as recorded | recanonicalized |
|---|---|---|
| exact recoveries | 3 | 9 |
| records re-scored | 82 | 82 |
| records whose score changed | - | 34 |
| skeleton recoveries | - | 9 |

### Re-scored records

| problem | condition | exact | skeleton | TED | was exact | was TED | RMSE |
|---|---|---|---|---|---|---|---|
| phase2_kur | ndformer_mcts | 1.0000 | 1.0000 | 0.0000 | 0.0000 | 5.0000 | 0.0000 |
| phase2_kur_unguided | unguided_mcts | 0.0000 | 0.0000 | 10.0000 | 0.0000 | 10.0000 | 1.2075 |
| phase3_KUR_s101_ndformer_mcts | ndformer_mcts | 1.0000 | 1.0000 | 0.0000 | 0.0000 | 5.0000 | 0.0000 |
| phase3_KUR_s101_unguided_mcts | unguided_mcts | 0.0000 | 0.0000 | 9.0000 | 0.0000 | 10.0000 | 1.2756 |
| phase3_CR_s101_ndformer_mcts | ndformer_mcts | 0.0000 | 0.0000 | 13.0000 | 0.0000 | 12.0000 | 1.4974 |
| phase3_CR_s101_unguided_mcts | unguided_mcts | 0.0000 | 0.0000 | 12.0000 | 0.0000 | 12.0000 | 1.5967 |
| phase3_HCR_s101_ndformer_mcts | ndformer_mcts | 0.0000 | 0.0000 | 13.0000 | 0.0000 | 11.0000 | 1.5179 |
| phase3_HCR_s101_unguided_mcts | unguided_mcts | 0.0000 | 0.0000 | 14.0000 | 0.0000 | 13.0000 | 1.5251 |
| phase3_FHN_s101_ndformer_mcts | ndformer_mcts | 0.0000 | 0.0000 | 19.0000 | 0.0000 | 18.0000 | 0.3824 |
| phase3_FHN_s101_unguided_mcts | unguided_mcts | 0.0000 | 0.0000 | 18.0000 | 0.0000 | 15.0000 | 0.7960 |
| phase3_WC_s101_ndformer_mcts | ndformer_mcts | 0.0000 | 0.0000 | 17.0000 | 0.0000 | 12.0000 | 0.0105 |
| phase3_WC_s101_unguided_mcts | unguided_mcts | 0.0000 | 0.0000 | 28.0000 | 0.0000 | 25.0000 | 0.4635 |
| phase3_GR_s101_ndformer_mcts | ndformer_mcts | 0.0000 | 0.0000 | 15.0000 | 0.0000 | 14.0000 | 0.0551 |
| phase3_GR_s101_unguided_mcts | unguided_mcts | 0.0000 | 0.0000 | 31.0000 | 0.0000 | 29.0000 | 3.2471 |
| phase3_MM_s101_ndformer_mcts | ndformer_mcts | 1.0000 | 1.0000 | 0.0000 | 0.0000 | 7.0000 | 0.0000 |
| phase3_MM_s101_unguided_mcts | unguided_mcts | 0.0000 | 0.0000 | 22.0000 | 0.0000 | 24.0000 | 0.3151 |
| phase3_LV_s101_ndformer_mcts | ndformer_mcts | 0.0000 | 0.0000 | 26.0000 | 0.0000 | 23.0000 | 0.0705 |
| phase3_LV_s101_unguided_mcts | unguided_mcts | 0.0000 | 0.0000 | 15.0000 | 0.0000 | 13.0000 | 0.1298 |
| phase3_MP_s101_ndformer_mcts | ndformer_mcts | 0.0000 | 0.0000 | 17.0000 | 0.0000 | 19.0000 | 3.5622 |
| phase3_MP_s101_unguided_mcts | unguided_mcts | 0.0000 | 0.0000 | 18.0000 | 0.0000 | 19.0000 | 4.4439 |
| phase3_SIS_s101_ndformer_mcts | ndformer_mcts | 0.0000 | 0.0000 | 10.0000 | 0.0000 | 10.0000 | 0.1814 |
| phase3_SIS_s101_unguided_mcts | unguided_mcts | 0.0000 | 0.0000 | 23.0000 | 0.0000 | 23.0000 | 0.4922 |
| phase3_KUR_s202_ndformer_mcts | ndformer_mcts | 1.0000 | 1.0000 | 0.0000 | 0.0000 | 5.0000 | 0.0000 |
| phase3_CR_s202_ndformer_mcts | ndformer_mcts | 0.0000 | 0.0000 | 16.0000 | 0.0000 | 15.0000 | 1.4975 |
| phase3_HCR_s202_ndformer_mcts | ndformer_mcts | 0.0000 | 0.0000 | 18.0000 | 0.0000 | 17.0000 | 1.4882 |
| phase3_FHN_s202_ndformer_mcts | ndformer_mcts | 0.0000 | 0.0000 | 18.0000 | 0.0000 | 16.0000 | 0.5138 |
| phase3_WC_s202_ndformer_mcts | ndformer_mcts | 0.0000 | 0.0000 | 12.0000 | 0.0000 | 12.0000 | 0.0168 |
| phase3_GR_s202_ndformer_mcts | ndformer_mcts | 0.0000 | 0.0000 | 14.0000 | 0.0000 | 10.0000 | 0.1408 |
| phase3_MM_s202_ndformer_mcts | ndformer_mcts | 0.0000 | 0.0000 | 9.0000 | 0.0000 | 6.0000 | 0.0014 |
| phase3_LV_s202_ndformer_mcts | ndformer_mcts | 0.0000 | 0.0000 | 22.0000 | 0.0000 | 21.0000 | 0.1000 |
| phase3_MP_s202_ndformer_mcts | ndformer_mcts | 0.0000 | 0.0000 | 19.0000 | 0.0000 | 17.0000 | 4.2255 |
| phase3_SIS_s202_ndformer_mcts | ndformer_mcts | 0.0000 | 0.0000 | 16.0000 | 0.0000 | 16.0000 | 0.2598 |
| phase3_KUR_s303_ndformer_mcts | ndformer_mcts | 1.0000 | 1.0000 | 0.0000 | 0.0000 | 3.0000 | 0.0000 |
| phase3_CR_s303_ndformer_mcts | ndformer_mcts | 0.0000 | 0.0000 | 14.0000 | 0.0000 | 12.0000 | 1.4807 |
| phase3_HCR_s303_ndformer_mcts | ndformer_mcts | 0.0000 | 0.0000 | 13.0000 | 0.0000 | 12.0000 | 1.5294 |
| phase3_FHN_s303_ndformer_mcts | ndformer_mcts | 0.0000 | 0.0000 | 13.0000 | 0.0000 | 14.0000 | 0.0000 |
| phase3_WC_s303_ndformer_mcts | ndformer_mcts | 0.0000 | 0.0000 | 15.0000 | 0.0000 | 14.0000 | 0.0040 |
| phase3_GR_s303_ndformer_mcts | ndformer_mcts | 0.0000 | 0.0000 | 17.0000 | 0.0000 | 13.0000 | 0.1366 |
| phase3_MM_s303_ndformer_mcts | ndformer_mcts | 1.0000 | 1.0000 | 0.0000 | 0.0000 | 6.0000 | 0.0000 |
| phase3_LV_s303_ndformer_mcts | ndformer_mcts | 0.0000 | 0.0000 | 19.0000 | 0.0000 | 19.0000 | 0.0419 |
| phase3_MP_s303_ndformer_mcts | ndformer_mcts | 0.0000 | 0.0000 | 18.0000 | 0.0000 | 15.0000 | 6.7216 |
| phase3_SIS_s303_ndformer_mcts | ndformer_mcts | 0.0000 | 0.0000 | 14.0000 | 0.0000 | 14.0000 | 0.3153 |
| phase7_frozen_F_02f34ed8dc27_021 | frozen | 0.0000 | 0.0000 | 4.0000 | 0.0000 | 4.0000 | 0.0000 |
| phase7_frozen_F_054bebdfa4d4_011 | frozen | 0.0000 | 0.0000 | 11.0000 | 0.0000 | 11.0000 | 4.6799 |
| phase7_frozen_F_0db52fe06164_054 | frozen | 0.0000 | 0.0000 | 5.0000 | 0.0000 | 5.0000 | 0.0000 |
| phase7_frozen_F_3e0dd8f67eb6_080 | frozen | 1.0000 | 1.0000 | 0.0000 | 1.0000 | 0.0000 | 0.0000 |
| phase7_full_F_02f34ed8dc27_021 | full | 0.0000 | 0.0000 | 3.0000 | 0.0000 | 3.0000 | 0.0000 |
| phase7_full_F_054bebdfa4d4_011 | full | 0.0000 | 0.0000 | 13.0000 | 0.0000 | 13.0000 | 2.2606 |
| phase7_full_F_0db52fe06164_054 | full | 0.0000 | 0.0000 | 2.0000 | 0.0000 | 2.0000 | 0.0000 |
| phase7_full_F_3e0dd8f67eb6_080 | full | 0.0000 | 0.0000 | 3.0000 | 0.0000 | 3.0000 | 0.0000 |
| phase7_top_1_F_02f34ed8dc27_021 | top_1 | 0.0000 | 0.0000 | 3.0000 | 0.0000 | 3.0000 | 0.0000 |
| phase7_top_1_F_054bebdfa4d4_011 | top_1 | 0.0000 | 0.0000 | 9.0000 | 0.0000 | 9.0000 | 1.8050 |
| phase7_top_1_F_0db52fe06164_054 | top_1 | 0.0000 | 0.0000 | 8.0000 | 0.0000 | 8.0000 | 0.0000 |
| phase7_top_1_F_3e0dd8f67eb6_080 | top_1 | 0.0000 | 0.0000 | 4.0000 | 0.0000 | 4.0000 | 0.0000 |
| phase7_top_3_F_02f34ed8dc27_021 | top_3 | 1.0000 | 1.0000 | 0.0000 | 1.0000 | 0.0000 | 0.0000 |
| phase7_top_3_F_054bebdfa4d4_011 | top_3 | 0.0000 | 0.0000 | 9.0000 | 0.0000 | 9.0000 | 4.1399 |
| phase7_top_3_F_0db52fe06164_054 | top_3 | 0.0000 | 0.0000 | 5.0000 | 0.0000 | 5.0000 | 0.0000 |
| phase7_top_3_F_3e0dd8f67eb6_080 | top_3 | 0.0000 | 0.0000 | 7.0000 | 0.0000 | 7.0000 | 0.0000 |
| phase7_random_3_F_02f34ed8dc27_021 | random_3 | 1.0000 | 1.0000 | 0.0000 | 1.0000 | 0.0000 | 0.0000 |
| phase7_random_3_F_054bebdfa4d4_011 | random_3 | 0.0000 | 0.0000 | 12.0000 | 0.0000 | 12.0000 | 4.5878 |
| phase7_random_3_F_0db52fe06164_054 | random_3 | 0.0000 | 0.0000 | 5.0000 | 0.0000 | 5.0000 | 0.0000 |
| phase7_random_3_F_3e0dd8f67eb6_080 | random_3 | 0.0000 | 0.0000 | 5.0000 | 0.0000 | 5.0000 | 0.0000 |
| phase8_frozen_F_0c0267846e35_063 | frozen | 0.0000 | 0.0000 | 15.0000 | 0.0000 | 15.0000 | 1275.3994 |
| phase8_frozen_F_322102fa9b39_029 | frozen | 0.0000 | 0.0000 | 8.0000 | 0.0000 | 8.0000 | 0.0000 |
| phase8_frozen_F_458d8837321f_057 | frozen | 0.0000 | 0.0000 | 16.0000 | 0.0000 | 16.0000 | 4.7069 |
| phase8_frozen_F_4a0a28cfc3e7_052 | frozen | 0.0000 | 0.0000 | 11.0000 | 0.0000 | 11.0000 | 3.4880 |
| phase8_full_F_0c0267846e35_063 | full | 0.0000 | 0.0000 | 14.0000 | 0.0000 | 14.0000 | 830.5518 |
| phase8_full_F_322102fa9b39_029 | full | 0.0000 | 0.0000 | 8.0000 | 0.0000 | 8.0000 | 0.0000 |
| phase8_full_F_458d8837321f_057 | full | 0.0000 | 0.0000 | 10.0000 | 0.0000 | 10.0000 | 4.7014 |
| phase8_full_F_4a0a28cfc3e7_052 | full | 0.0000 | 0.0000 | 12.0000 | 0.0000 | 12.0000 | 3.6089 |
| phase8_top_1_F_0c0267846e35_063 | top_1 | 0.0000 | 0.0000 | 14.0000 | 0.0000 | 14.0000 | 634.5489 |
| phase8_top_1_F_322102fa9b39_029 | top_1 | 0.0000 | 0.0000 | 11.0000 | 0.0000 | 11.0000 | 0.0000 |
| phase8_top_1_F_458d8837321f_057 | top_1 | 0.0000 | 0.0000 | 16.0000 | 0.0000 | 16.0000 | 4.8009 |
| phase8_top_1_F_4a0a28cfc3e7_052 | top_1 | 0.0000 | 0.0000 | 7.0000 | 0.0000 | 7.0000 | 3.1796 |
| phase8_top_3_F_0c0267846e35_063 | top_3 | 0.0000 | 0.0000 | 12.0000 | 0.0000 | 12.0000 | 1140.4335 |
| phase8_top_3_F_322102fa9b39_029 | top_3 | 0.0000 | 0.0000 | 10.0000 | 0.0000 | 10.0000 | 0.0000 |
| phase8_top_3_F_458d8837321f_057 | top_3 | 0.0000 | 0.0000 | 14.0000 | 0.0000 | 14.0000 | 4.6812 |
| phase8_top_3_F_4a0a28cfc3e7_052 | top_3 | 0.0000 | 0.0000 | 8.0000 | 0.0000 | 8.0000 | 3.4770 |
| phase8_random_3_F_0c0267846e35_063 | random_3 | 0.0000 | 0.0000 | 9.0000 | 0.0000 | 9.0000 | 452.1135 |
| phase8_random_3_F_322102fa9b39_029 | random_3 | 0.0000 | 0.0000 | 4.0000 | 0.0000 | 4.0000 | 0.0000 |
| phase8_random_3_F_458d8837321f_057 | random_3 | 0.0000 | 0.0000 | 16.0000 | 0.0000 | 16.0000 | 4.6928 |
| phase8_random_3_F_4a0a28cfc3e7_052 | random_3 | 0.0000 | 0.0000 | 11.0000 | 0.0000 | 11.0000 | 3.5630 |

## 6. Reading these numbers

- Fit error and formula recovery are reported separately: a low RMSE does not
  mean the true network dynamics formula was recovered (plan section 6.5).
- Every run is stored per problem in `phase3/records.jsonl`, including failures,
  timeouts and invalid formulas (plan section 6.4).
- KUR's official network file ships only in the Zenodo archive; when it is absent
  the run falls back to an Erdos-Renyi graph and flags `used_er_fallback`.

<!-- BEGIN budget-sensitivity -->

## 7. Budget sensitivity: search-limited vs structurally-limited

The systems not recovered in the main benchmark were rerun at 1800s per problem instead of 300s, with the ACC4 early-stop predicate disabled. Without disabling it the search halts as soon as the fit saturates, so the larger budget would never be spent and every system would look equally stuck.

Extended run: `gpu_run3_extended_1800s_groupB_20260818`

| system | seeds | RMSE @base | RMSE @extended | best RMSE @extended | TED @base | TED @extended | mean nodes | solved |
|---|---|---|---|---|---|---|---|---|
| CR | 3 | 1.492 | 1.469 | 1.445 | 13 | 14.67 | 7121.3 | 0/3 |
| HCR | 3 | 1.512 | 0.3259 | 3.349e-08 | 13.33 | 9.667 | 11366 | 1/3 |
| MP | 3 | 4.836 | 4.291 | 3.416 | 17 | 15.33 | 10781 | 0/3 |

### Whether the network-coupling term was found

The ND2 operators (`aggr` / `sour` / `targ` / `rgga`) are what make a formula a
*network* dynamics law rather than a node-local one. Counting how often they
appear at all separates a search that misses a detail from one that never
reaches the coupling term.

| system | true formula has network op | predictions containing one (extended) |
|---|---|---|
| CR | yes | 0/3 |
| HCR | yes | 3/3 |
| MP | yes | 2/3 |

### Per-seed predictions at the extended budget

**CR** — true: `((0.5000*aggr(sin((sour(x)-targ(x)))))-(z+(omega*y)))`

- seed 101: `(((0.0679*x)+((omega*y)*-0.8720))-z)` (RMSE 1.445, TED 15)
- seed 202: `(((-0.7841*z)-(-0.3016*sin(x)))+(-0.7185*(omega*y)))` (RMSE 1.48, TED 15)
- seed 303: `(((-0.6543*y)*omega)-z)` (RMSE 1.481, TED 14)

**HCR** — true: `((0.5000*aggr(sin((sour(x)-targ(x)))))-(y+z))`

- seed 101: `(((-1.0000*z)-y)+(0.5000*aggr(sin((sour(x)-targ(x))))))` (RMSE 3.349e-08, TED 9)
- seed 202: `((y*-0.9946)+(0.4991*aggr(sin((sour(x)-((1/5)+targ(x)))))))` (RMSE 0.4875, TED 10)
- seed 303: `((y*-0.9924)+(0.5104*aggr(sin((sour((x+-0.1583))-targ(x))))))` (RMSE 0.4901, TED 10)

**MP** — true: `((x*(alpha-(theta*x)))+aggr((sour(regular(x, 2))*targ(x))))`

- seed 101: `(((-1.5056-x)*(3.0579*theta))+(4.8996*aggr(sour((1.3769-alpha)))))` (RMSE 3.416, TED 15)
- seed 202: `((((alpha**3)*6.1279)-x)+(2.0826*aggr((sour(theta)/targ(theta)))))` (RMSE 3.841, TED 16)
- seed 303: `((((x*-4.6792)*-0.6096)+(-0.5184*((x**2)*theta)))-alpha)` (RMSE 5.616, TED 15)

### Reading

A system whose RMSE is flat under a six-fold budget increase is not waiting for
more search. Where the predictions also omit the network operators entirely, the
search is settling on the node-local part of the dynamics, which already explains
most of the variance, and never pays the cost of reaching the coupling term.
That is a different failure from one where the structure is reachable but found
only in some seeds.

These runs use the same checkpoint, corpus and configs as the main benchmark;
only the MCTS time limit and the early-stop predicate differ.

<!-- END budget-sensitivity -->
