# GPU_RUN3 — ND² 再現レポート

Run ID: `gpu_run3_extended_1800s_groupB_20260818`  
キャンペーン: GPU_RUN3  
provenance: `upstream_reproduction`（公式実装の再現）

## 1. 実行環境とprovenance

| 項目 | 値 |
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

> `phase1/summary.json` がこのrunディレクトリに存在しません。以下のセクションは不完全です。

## 3. パイプライン再現（Phase 2、KUR）

> `phase2/summary.json` がこのrunディレクトリに存在しません。以下のセクションは不完全です。


## 4. RQ1 — synthetic benchmarkの再現（Phase 3）

| 指標 | 値 |
|---|---|
| seeds | 101, 202, 303 |
| guided runs | 9 |
| systems | 3 |
| valid | 9 |
| exact recoveries | 0 |
| skeleton recoveries | 0 |
| mean ted_raw | 13.2222 |
| mean R2 | 0.7875 |

### システム別

`exact` / `skeleton` / `平均TED` は再正規化後の値（第5節）。
`exact（記録時）` はPhase 3が再スコアリング前に書いた値。

| システム | n | valid | exact | exact（記録時） | skeleton | 平均TED | 平均RMSE | 平均R2 | 平均ノード数 | 平均秒 |
|---|---|---|---|---|---|---|---|---|---|---|
| coupled_Rossler | 3 | 3 | 0 | 0 | 0 | 14.6667 | 1.4685 | 0.7484 | 7121.3333 | 1800.5848 |
| homogeneous_coupled_Rossler | 3 | 3 | 1 | 0 | 1 | 5.3333 | 0.3259 | 0.9816 | 11365.6667 | 1801.9927 |
| mutualistic_population | 3 | 3 | 0 | 0 | 0 | 15.3333 | 4.2910 | 0.6324 | 10781.3333 | 1803.3161 |

### 真の式と回復された式

**coupled_Rossler**

- 真値: `((0.5000*aggr(sin((sour(x)-targ(x)))))-(z+(omega*y)))`
- 予測（run 1）: `(((0.0679*x)+((omega*y)*-0.8720))-z)`
- 予測（run 2）: `(((-0.7841*z)-(-0.3016*sin(x)))+(-0.7185*(omega*y)))`
- 予測（run 3）: `(((-0.6543*y)*omega)-z)`

**homogeneous_coupled_Rossler**

- 真値: `((0.5000*aggr(sin((sour(x)-targ(x)))))-(y+z))`
- 予測（run 1）: `(((-1.0000*z)-y)+(0.5000*aggr(sin((sour(x)-targ(x))))))`
- 予測（run 2）: `((y*-0.9946)+(0.4991*aggr(sin((sour(x)-((1/5)+targ(x)))))))`
- 予測（run 3）: `((y*-0.9924)+(0.5104*aggr(sin((sour((x+-0.1583))-targ(x))))))`

**mutualistic_population**

- 真値: `((x*(alpha-(theta*x)))+aggr((sour(regular(x, 2))*targ(x))))`
- 予測（run 1）: `(((-1.5056-x)*(3.0579*theta))+(4.8996*aggr(sour((1.3769-alpha)))))`
- 予測（run 2）: `((((alpha**3)*6.1279)-x)+(2.0826*aggr((sour(theta)/targ(theta)))))`
- 予測（run 3）: `((((x*-4.6792)*-0.6096)+(-0.5184*((x**2)*theta)))-alpha)`

## 5. 単一の正規化による構造メトリクス

フェーズごとに異なる正規化リビジョンで結果が書かれうるため、保存されたprefixから
全ての式を一度だけ一律に再スコアリングしている。定数は
4桁の有効数字で比較し、恒等式
0+x -> x, x-0 -> x, 1*x -> x, 0*x -> 0, x/1 -> x, x**1 -> x を畳み込む（許容誤差 0.0001）。

| 指標 | 記録時 | 再正規化後 |
|---|---|---|
| exact回復数 | 0 | 1 |
| 再スコアリング件数 | 9 | 9 |
| スコアが変化した件数 | - | 5 |
| skeleton回復数 | - | 1 |

### 再スコアリングされたレコード

| 問題 | 条件 | exact | skeleton | TED | 記録時exact | 記録時TED | RMSE |
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

## 6. 数値の読み方

- fit errorと式の回復は分けて報告している。RMSEが小さくても真のnetwork dynamics式を
  回復したとは限らない（plan §6.5）。
- 全runはproblem単位で `phase3/records.jsonl` に保存され、失敗・timeout・invalidな式も
  除外せず含まれる（plan §6.4）。
- KURの公式ネットワークファイルはZenodoアーカイブにのみ同梱される。存在しない場合は
  Erdős–Rényiグラフにフォールバックし、`used_er_fallback` を立てる。

