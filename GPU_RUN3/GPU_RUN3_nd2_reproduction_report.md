# GPU_RUN3 — ND² 再現レポート

Run ID: `gpu_run3_full_20260817`  
キャンペーン: GPU_RUN3  
provenance: `upstream_reproduction`（公式実装の再現）

## 1. 実行環境とprovenance

| 項目 | 値 |
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

### NDformer アーキテクチャ

| 項目 | 値 |
|---|---|
| encoder Transformer blocks | 2 |
| decoder Transformer blocks | 2 |
| total parameters | 17715713 |
| ranking layers | encoder.Transformer.layers.0, encoder.Transformer.layers.1, decoder.decoder.layers.0, decoder.decoder.layers.1 |

### Go条件（Phase 0）

| 条件 | 結果 |
|---|---|
| checkpoint_load_ok | yes |
| forward_ok | yes |
| policy_shape_ok | yes |
| vocab_ok | yes |
| parser_ok | yes |
| mcts_valid_formula_ok | yes |

## 2. RQ2 — NDformer policyの再現（Phase 1）

| 指標 | 値 |
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

シード別:

| seed | 問題数 | 例数 | CE | top-1 | top-5 | valid率 |
|---|---|---|---|---|---|---|
| 101 | 21 | 175 | 1.8692 | 0.4426 | 0.8335 | 1.0000 |
| 202 | 22 | 199 | 2.2938 | 0.3709 | 0.7351 | 1.0000 |
| 303 | 22 | 227 | 2.1166 | 0.3588 | 0.7838 | 1.0000 |

policyレベルの失敗: なし

## 3. パイプライン再現（Phase 2、KUR）

| 項目 | 値 |
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

同一問題・同一予算での unguided（一様）MCTS 対照:

| 項目 | 値 |
|---|---|
| pred | (-0.7865*(-(-0.2508+omega0))) |
| exact | 0.0000 |
| ted_raw | 10.0000 |
| fit_error | 1.2075 |
| search_nodes | 3564 |
| candidate_count | 25312 |
| wall_time | 300.0486 |

## 4. RQ1 — synthetic benchmarkの再現（Phase 3）

| 指標 | 値 |
|---|---|
| seeds | 101, 202, 303 |
| guided runs | 30 |
| systems | 10 |
| valid | 30 |
| exact recoveries | 0 |
| skeleton recoveries | 0 |
| mean ted_raw | 12.9333 |
| mean R2 | 0.8602 |

### システム別

`exact` / `skeleton` / `平均TED` は再正規化後の値（第5節）。
`exact（記録時）` はPhase 3が再スコアリング前に書いた値。

| システム | n | valid | exact | exact（記録時） | skeleton | 平均TED | 平均RMSE | 平均R2 | 平均ノード数 | 平均秒 |
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

### 真の式と回復された式

**Kuramoto**

- 真値: `(omega0+(1.0000*aggr(sin((sour(x)-targ(x))))))`
- 予測（run 1）: `((-0.0000+omega0)+(1.0000*aggr(sin((sour(x)-targ(x))))))`
- 予測（run 2）: `((omega0+-0.0000)+(1.0000*aggr(sin((sour(x)-targ(x))))))`
- 予測（run 3）: `((1.0000*omega0)+(1.0000*aggr(sin((sour(x)-targ(x))))))`

**coupled_Rossler**

- 真値: `((0.5000*aggr(sin((sour(x)-targ(x)))))-(z+(omega*y)))`
- 予測（run 1）: `(((0.8374*omega)*(sigmoid(x)-y))-(z*1.2134))`
- 予測（run 2）: `(-((((0.0235*x)-(y*omega))+(-z))*-0.7245))`
- 予測（run 3）: `(((-0.6543*y)*omega)-z)`

**homogeneous_coupled_Rossler**

- 真値: `((0.5000*aggr(sin((sour(x)-targ(x)))))-(y+z))`
- 予測（run 1）: `((0.1504-z)+(-0.7758*y))`
- 予測（run 2）: `((((-0.5259*y)+(-0.9319*z))-(0.0490*x))+(-0.0087*(y**3)))`
- 予測（run 3）: `(((-0.7387*y)+(0.4177*sin(x)))-z)`

**FitzHugh_Nagumo**

- 真値: `(x-((y+(x**3))+(aggr((sour(x)-targ(x)))/aggr(1))))`
- 予測（run 1）: `(((-4.3513*x)+(6.1830*sin(x)))-(0.8878*(y+-0.3304)))`
- 予測（run 2）: `(((4.8078*sin(x))-(y*0.6805))-(3.4839*x))`
- 予測（run 3）: `(((x-y)-(x**3))+(-0.1111*aggr((sour(x)-targ(x)))))`

**Wilson_Cowan**

- 真値: `(aggr(sour(sigmoid(((5.1000*x)-5.1000))))-x)`
- 予測（run 1）: `((0.0007-x)+(1.0015*aggr(sigmoid(sour((8.1096-((-3.8503+x)**2)))))))`
- 予測（run 2）: `((x*-0.9992)+(0.9991*aggr(sour(sigmoid((-0.9613+(x**3)))))))`
- 予測（run 3）: `(((-x)*1.0018)+(1.0032*aggr(sour(regular(((x**2)**2), 1.5693)))))`

**gene_regulatory**

- 真値: `((0.2000+(2.0000*aggr(sour(regular((0.6667*x), 2)))))-(0.9000*x))`
- 予測（run 1）: `((x*-0.9021)+(2.0230*aggr(regular(sour((x/1.4850)), 1.9677))))`
- 予測（run 2）: `((0.3093-x)+(4.5180*aggr(sour(sigmoid((-1.8000/x))))))`
- 予測（run 3）: `((0.3501-x)+(1.9495*aggr(sour((2.3124*sigmoid((-2.3907/(1.3249*x))))))))`

**Michaelis_Menten**

- 真値: `(aggr(sour(regular(x, 2)))-x)`
- 予測（run 1）: `((-1.0000*x)+(1.0000*aggr(sour(regular(x, 2)))))`
- 予測（run 2）: `((-0.0058-x)+(1.0065*aggr(sour(regular(x, 1.9459)))))`
- 予測（run 3）: `((-1.0000*x)+(0.0000+aggr(sour(regular(x, 2.0000)))))`

**Lotka_Volterra**

- 真値: `((x*(alpha-(theta*x)))-aggr((sour(x)*targ(x))))`
- 予測（run 1）: `(((((((1.1371*alpha)+(0.0310*theta))+x)-alpha)-(0.3566*aggr(targ(x))))-(0.6916*x))-(0.7377*(sin(alpha)-(alpha**2))))`
- 予測（run 2）: `(x*(sin(alpha)-(sin((((alpha*theta)**2)+0.3509))*aggr(sour(((-(x+sigmoid(alpha)))**2))))))`
- 予測（run 3）: `((((((alpha-sin(x))+x)+(-1.9617*alpha))-(0.3259*aggr(targ(x))))+(0.9154*alpha))+(0.2388*theta))`

**mutualistic_population**

- 真値: `((x*(alpha-(theta*x)))+aggr((sour(regular(x, 2))*targ(x))))`
- 予測（run 1）: `(((-4.2793*x)*(-0.0895-sin((-theta))))+(8.1084*aggr(sour(sigmoid((aggr(targ(alpha))/(-2.7594*x)))))))`
- 予測（run 2）: `(((0.0446*x)-(-5.8091*alpha))+(-2.3585*aggr(sour(sin((theta*(-0.7327*x)))))))`
- 予測（run 3）: `((sin(theta)+(x*((-4.4216*theta)--2.8492)))+(alpha+((theta-(x**2))*0.0525)))`

**susceptible_infected_susceptible**

- 真値: `(aggr(((1-targ(x))*sour(x)))-(delta*x))`
- 予測（run 1）: `(((-0.7972*x)*delta)+(0.4959*aggr((sour((x/x))-targ(x)))))`
- 予測（run 2）: `((((8.4425*sigmoid(x))-(0.5349*delta))-(7.3123*x))-(-0.2356*aggr(sour((x**3)))))`
- 予測（run 3）: `((x*-2.8985)+(5.7352*sin(tan(sigmoid((delta*-0.2348))))))`

### NDformer誘導あり vs unguided MCTS

| 項目 | 値 |
|---|---|
| n | 10 |
| n_exact | 0 |
| mean_ted_raw | 18.3000 |
| mean_r2 | 0.5755 |
| mean_search_nodes | 4102.9000 |

## 5. 単一の正規化による構造メトリクス

フェーズごとに異なる正規化リビジョンで結果が書かれうるため、保存されたprefixから
全ての式を一度だけ一律に再スコアリングしている。定数は
4桁の有効数字で比較し、恒等式
0+x -> x, x-0 -> x, 1*x -> x, 0*x -> 0, x/1 -> x, x**1 -> x を畳み込む（許容誤差 0.0001）。

| 指標 | 記録時 | 再正規化後 |
|---|---|---|
| exact回復数 | 3 | 11 |
| 再スコアリング件数 | 82 | 82 |
| スコアが変化した件数 | - | 43 |
| skeleton回復数 | - | 11 |

### 再スコアリングされたレコード

| 問題 | 条件 | exact | skeleton | TED | 記録時exact | 記録時TED | RMSE |
|---|---|---|---|---|---|---|---|
| phase2_kur | ndformer_mcts | 1.0000 | 1.0000 | 0.0000 | 0.0000 | 5.0000 | 0.0000 |
| phase2_kur_unguided | unguided_mcts | 0.0000 | 0.0000 | 10.0000 | 0.0000 | 10.0000 | 1.2075 |
| phase3_KUR_s101_ndformer_mcts | ndformer_mcts | 1.0000 | 1.0000 | 0.0000 | 0.0000 | 5.0000 | 0.0000 |
| phase3_KUR_s101_unguided_mcts | unguided_mcts | 0.0000 | 0.0000 | 9.0000 | 0.0000 | 10.0000 | 1.2756 |
| phase3_CR_s101_ndformer_mcts | ndformer_mcts | 0.0000 | 0.0000 | 13.0000 | 0.0000 | 12.0000 | 1.4974 |
| phase3_CR_s101_unguided_mcts | unguided_mcts | 0.0000 | 0.0000 | 13.0000 | 0.0000 | 12.0000 | 1.5967 |
| phase3_HCR_s101_ndformer_mcts | ndformer_mcts | 0.0000 | 0.0000 | 13.0000 | 0.0000 | 11.0000 | 1.5179 |
| phase3_HCR_s101_unguided_mcts | unguided_mcts | 0.0000 | 0.0000 | 11.0000 | 0.0000 | 13.0000 | 1.5251 |
| phase3_FHN_s101_ndformer_mcts | ndformer_mcts | 0.0000 | 0.0000 | 19.0000 | 0.0000 | 18.0000 | 0.3824 |
| phase3_FHN_s101_unguided_mcts | unguided_mcts | 0.0000 | 0.0000 | 18.0000 | 0.0000 | 15.0000 | 0.7960 |
| phase3_WC_s101_ndformer_mcts | ndformer_mcts | 0.0000 | 0.0000 | 17.0000 | 0.0000 | 12.0000 | 0.0105 |
| phase3_WC_s101_unguided_mcts | unguided_mcts | 0.0000 | 0.0000 | 27.0000 | 0.0000 | 25.0000 | 0.4635 |
| phase3_GR_s101_ndformer_mcts | ndformer_mcts | 0.0000 | 0.0000 | 15.0000 | 0.0000 | 14.0000 | 0.0551 |
| phase3_GR_s101_unguided_mcts | unguided_mcts | 0.0000 | 0.0000 | 31.0000 | 0.0000 | 29.0000 | 3.2471 |
| phase3_MM_s101_ndformer_mcts | ndformer_mcts | 1.0000 | 1.0000 | 0.0000 | 0.0000 | 7.0000 | 0.0000 |
| phase3_MM_s101_unguided_mcts | unguided_mcts | 0.0000 | 0.0000 | 22.0000 | 0.0000 | 24.0000 | 0.3151 |
| phase3_LV_s101_ndformer_mcts | ndformer_mcts | 0.0000 | 0.0000 | 26.0000 | 0.0000 | 23.0000 | 0.0705 |
| phase3_LV_s101_unguided_mcts | unguided_mcts | 0.0000 | 0.0000 | 15.0000 | 0.0000 | 13.0000 | 0.1298 |
| phase3_MP_s101_ndformer_mcts | ndformer_mcts | 0.0000 | 0.0000 | 17.0000 | 0.0000 | 19.0000 | 3.5622 |
| phase3_MP_s101_unguided_mcts | unguided_mcts | 0.0000 | 0.0000 | 18.0000 | 0.0000 | 19.0000 | 4.4439 |
| phase3_SIS_s101_ndformer_mcts | ndformer_mcts | 0.0000 | 0.0000 | 10.0000 | 0.0000 | 10.0000 | 0.1814 |
| phase3_SIS_s101_unguided_mcts | unguided_mcts | 0.0000 | 0.0000 | 22.0000 | 0.0000 | 23.0000 | 0.4922 |
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
| phase7_frozen_F_054bebdfa4d4_011 | frozen | 0.0000 | 0.0000 | 10.0000 | 0.0000 | 11.0000 | 4.6799 |
| phase7_frozen_F_0db52fe06164_054 | frozen | 0.0000 | 0.0000 | 5.0000 | 0.0000 | 5.0000 | 0.0000 |
| phase7_frozen_F_3e0dd8f67eb6_080 | frozen | 1.0000 | 1.0000 | 0.0000 | 1.0000 | 0.0000 | 0.0000 |
| phase7_full_F_02f34ed8dc27_021 | full | 1.0000 | 1.0000 | 0.0000 | 0.0000 | 3.0000 | 0.0000 |
| phase7_full_F_054bebdfa4d4_011 | full | 0.0000 | 0.0000 | 11.0000 | 0.0000 | 13.0000 | 2.2606 |
| phase7_full_F_0db52fe06164_054 | full | 0.0000 | 0.0000 | 2.0000 | 0.0000 | 2.0000 | 0.0000 |
| phase7_full_F_3e0dd8f67eb6_080 | full | 0.0000 | 0.0000 | 3.0000 | 0.0000 | 3.0000 | 0.0000 |
| phase7_top_1_F_02f34ed8dc27_021 | top_1 | 1.0000 | 1.0000 | 0.0000 | 0.0000 | 3.0000 | 0.0000 |
| phase7_top_1_F_054bebdfa4d4_011 | top_1 | 0.0000 | 0.0000 | 9.0000 | 0.0000 | 9.0000 | 1.8050 |
| phase7_top_1_F_0db52fe06164_054 | top_1 | 0.0000 | 0.0000 | 5.0000 | 0.0000 | 8.0000 | 0.0000 |
| phase7_top_1_F_3e0dd8f67eb6_080 | top_1 | 0.0000 | 0.0000 | 4.0000 | 0.0000 | 4.0000 | 0.0000 |
| phase7_top_3_F_02f34ed8dc27_021 | top_3 | 1.0000 | 1.0000 | 0.0000 | 1.0000 | 0.0000 | 0.0000 |
| phase7_top_3_F_054bebdfa4d4_011 | top_3 | 0.0000 | 0.0000 | 9.0000 | 0.0000 | 9.0000 | 4.1399 |
| phase7_top_3_F_0db52fe06164_054 | top_3 | 0.0000 | 0.0000 | 5.0000 | 0.0000 | 5.0000 | 0.0000 |
| phase7_top_3_F_3e0dd8f67eb6_080 | top_3 | 0.0000 | 0.0000 | 7.0000 | 0.0000 | 7.0000 | 0.0000 |
| phase7_random_3_F_02f34ed8dc27_021 | random_3 | 1.0000 | 1.0000 | 0.0000 | 1.0000 | 0.0000 | 0.0000 |
| phase7_random_3_F_054bebdfa4d4_011 | random_3 | 0.0000 | 0.0000 | 11.0000 | 0.0000 | 12.0000 | 4.5878 |
| phase7_random_3_F_0db52fe06164_054 | random_3 | 0.0000 | 0.0000 | 5.0000 | 0.0000 | 5.0000 | 0.0000 |
| phase7_random_3_F_3e0dd8f67eb6_080 | random_3 | 0.0000 | 0.0000 | 5.0000 | 0.0000 | 5.0000 | 0.0000 |
| phase8_frozen_F_0c0267846e35_063 | frozen | 0.0000 | 0.0000 | 15.0000 | 0.0000 | 15.0000 | 1275.3994 |
| phase8_frozen_F_322102fa9b39_029 | frozen | 0.0000 | 0.0000 | 8.0000 | 0.0000 | 8.0000 | 0.0000 |
| phase8_frozen_F_458d8837321f_057 | frozen | 0.0000 | 0.0000 | 16.0000 | 0.0000 | 16.0000 | 4.7069 |
| phase8_frozen_F_4a0a28cfc3e7_052 | frozen | 0.0000 | 0.0000 | 11.0000 | 0.0000 | 11.0000 | 3.4880 |
| phase8_full_F_0c0267846e35_063 | full | 0.0000 | 0.0000 | 15.0000 | 0.0000 | 14.0000 | 830.5518 |
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

## 6. 数値の読み方

- fit errorと式の回復は分けて報告している。RMSEが小さくても真のnetwork dynamics式を
  回復したとは限らない（plan §6.5）。
- 全runはproblem単位で `phase3/records.jsonl` に保存され、失敗・timeout・invalidな式も
  除外せず含まれる（plan §6.4）。
- KURの公式ネットワークファイルはZenodoアーカイブにのみ同梱される。存在しない場合は
  Erdős–Rényiグラフにフォールバックし、`used_er_fallback` を立てる。

