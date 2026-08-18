# GPU_RUN3 — NDformer 層解析レポート

Run ID: `gpu_run3_full_20260817`  
provenance: `layer_analysis`（層解析）

解釈は最後まで区別している（plan §6.6）。probeは情報が線形に読み出せることを、
ablationはそのブロックが必要であることを、activation interventionは因果的に影響することを、
IOLEはその層だけで適応できることを、それぞれ示す。混同しない。

## 1. RQ3 — 層ごとの情報表現（Phase 4）

probeは `analysis_train` で学習し、`analysis_validation` で評価した。各スコアには同じ手順で学習したラベルシャッフル対照を併記している。

### probeタスク: `next_symbol`

| 層 | スコア | ラベルシャッフル対照 | スコア − 対照 |
|---|---|---|---|
| encoder.Transformer.layers.0 | 0.1129 | 0.0999 | 0.0130 |
| encoder.Transformer.layers.1 | 0.1317 | 0.0933 | 0.0385 |
| decoder.decoder.layers.0 | 0.4093 | 0.1012 | 0.3081 |
| decoder.decoder.layers.1 | 0.4124 | 0.0695 | 0.3430 |

### probeタスク: `formula_root_operator`

| 層 | スコア | ラベルシャッフル対照 | スコア − 対照 |
|---|---|---|---|
| encoder.Transformer.layers.0 | 0.2784 | 0.1642 | 0.1142 |
| encoder.Transformer.layers.1 | 0.2752 | 0.1393 | 0.1359 |
| decoder.decoder.layers.0 | 0.4875 | 0.1917 | 0.2958 |
| decoder.decoder.layers.1 | 0.3040 | 0.1382 | 0.1658 |

### probeタスク: `partial_prefix_length`

| 層 | スコア | ラベルシャッフル対照 | スコア − 対照 |
|---|---|---|---|
| encoder.Transformer.layers.0 | -3.1839 | -3.0616 | -0.1223 |
| encoder.Transformer.layers.1 | -3.2860 | -2.9904 | -0.2956 |
| decoder.decoder.layers.0 | -2.4652 | -3.0558 | 0.5906 |
| decoder.decoder.layers.1 | -2.5879 | -3.0725 | 0.4846 |

### probeタスク: `tree_depth`

| 層 | スコア | ラベルシャッフル対照 | スコア − 対照 |
|---|---|---|---|
| encoder.Transformer.layers.0 | -21.0773 | -18.4469 | -2.6305 |
| encoder.Transformer.layers.1 | -22.4742 | -18.0172 | -4.4569 |
| decoder.decoder.layers.0 | -20.0332 | -18.2669 | -1.7663 |
| decoder.decoder.layers.1 | -19.8221 | -18.1578 | -1.6643 |

### probeタスク: `tree_size`

| 層 | スコア | ラベルシャッフル対照 | スコア − 対照 |
|---|---|---|---|
| encoder.Transformer.layers.0 | -9.2265 | -8.2273 | -0.9992 |
| encoder.Transformer.layers.1 | -9.9717 | -8.2948 | -1.6769 |
| decoder.decoder.layers.0 | -8.9424 | -8.2618 | -0.6806 |
| decoder.decoder.layers.1 | -9.0084 | -8.3169 | -0.6915 |

### probeタスク: `network_op_count`

| 層 | スコア | ラベルシャッフル対照 | スコア − 対照 |
|---|---|---|---|
| encoder.Transformer.layers.0 | -0.3331 | -0.7874 | 0.4543 |
| encoder.Transformer.layers.1 | -0.2816 | -0.7587 | 0.4772 |
| decoder.decoder.layers.0 | -0.3503 | -0.7727 | 0.4224 |
| decoder.decoder.layers.1 | -0.1858 | -0.7920 | 0.6061 |

### gradient normと特徴量の変動

| 層 | gradient norm | パラメータ当たり | パラメータ数 | 問題内変動 |
|---|---|---|---|---|
| encoder.Transformer.layers.0 | 0.4048 | 0.0000 | 3152384 | 0.0000 |
| encoder.Transformer.layers.1 | 1.3570 | 0.0000 | 3152384 | 0.0000 |
| decoder.decoder.layers.0 | 1.0349 | 0.0000 | 4204032 | 0.1135 |
| decoder.decoder.layers.1 | 7.7150 | 0.0000 | 4204032 | 0.0214 |

encoderの活性はデコード中のprefixに依存しないため、problem内変動はほぼ0になる。したがってnext_symbolのような例単位のタスクはdecoderブロックについてのみ意味を持つ。

### CKA（問題単位の表現）

| 層ペア | CKA |
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

## 2. RQ6 — 数式構造はどの層で形成されるか（Phase 5）

### encoder中間層のデコード

| 層 | n | 真シンボル順位 | 真シンボル確率 | top-1 | エントロピー | 平均TED |
|---|---|---|---|---|---|---|
| encoder.Transformer.layers.0 | 213 | 34.9155 | 0.0288 | 0.0423 | 1.9195 | 31.0571 |
| encoder.Transformer.layers.1 | 213 | 5.5211 | 0.2931 | 0.3944 | 1.9891 | 8.8889 |

### decoder logit lens

| 層 | n | 真シンボル順位 | 真シンボル確率 | top-1 | エントロピー | 平均TED |
|---|---|---|---|---|---|---|
| decoder.decoder.layers.0 | 213 | 20.0704 | 0.0254 | 0.0235 | 0.0881 | NaN |
| decoder.decoder.layers.1 | 213 | 5.5211 | 0.2931 | 0.3944 | 1.9891 | NaN |

encoder_intermediate_decode は各encoderブロックのmemoryを学習済みdecoderへ渡す手法である。DecoderLensと同じ趣旨だが同一の手法ではない。NDformerには層ごとのdecoder対応が無いためである。

失敗数: 0

## 3. RQ4 — 層の因果的寄与（Phase 6）

パネル: validation 16問題、seed 101。baseline CE 2.2734、top-1 0.3826。

### 層ごとの効果（同一パネルのbaselineとの差分）

| layer | dCE skip | dCE zero | dCE mean | dCE patch | dtop1 skip | dtrue-prob skip |
|---|---|---|---|---|---|---|
| encoder.Transformer.layers.0 | 0.5599 | 1.2863 | 1.3498 | 1.3569 | -0.1369 | -0.1618 |
| encoder.Transformer.layers.1 | 5.8845 | 1.2633 | 1.2648 | 0.9797 | -0.2921 | -0.2163 |
| decoder.decoder.layers.0 | 0.6536 | 1.3440 | 1.1367 | 1.0421 | -0.1717 | -0.1300 |
| decoder.decoder.layers.1 | 23.2857 | 1.8209 | 0.9459 | 1.1595 | -0.3769 | -0.2752 |

### IOLE 単一層fine-tuning

| 条件 | cross entropy |
|---|---|
| frozen | 2.2734 |
| iole::encoder.Transformer.layers.0 | 2.2631 |
| iole::encoder.Transformer.layers.1 | 2.2263 |
| iole::decoder.decoder.layers.0 | 2.1941 |
| iole::decoder.decoder.layers.1 | 2.1606 |
| full | 2.1766 |

### パラメータ更新感度（統制された全層FT）

| 層 | ||Δθ|| | ||θ|| | 相対値 |
|---|---|---|---|
| encoder.Transformer.layers.0 | 1.1047 | 114.5875 | 0.0096 |
| encoder.Transformer.layers.1 | 1.0478 | 89.0321 | 0.0118 |
| decoder.decoder.layers.0 | 1.3862 | 148.6212 | 0.0093 |
| decoder.decoder.layers.1 | 1.2249 | 106.0741 | 0.0115 |

## 4. RQ5/RQ7 — 層ランキングと選択的fine-tuning（Phase 7）

consensusランキング（validationで固定）: decoder.decoder.layers.1, encoder.Transformer.layers.1, decoder.decoder.layers.0, encoder.Transformer.layers.0

ランキングの情報源: {"probe": "ok", "gradient": "ok", "decoderlens": "ok", "iole": "ok", "ablation": "ok", "intervention": "ok", "update_sensitivity": "ok"}

### ランキングの一致度

| ペア | Spearman | Kendall | top-3一致率 |
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

### RQ5 ランダム対照

`random_3` は ['decoder.decoder.layers.0', 'decoder.decoder.layers.1', 'encoder.Transformer.layers.1']、`top_3` は ['decoder.decoder.layers.0', 'decoder.decoder.layers.1', 'encoder.Transformer.layers.1']。両者は同一。ランキング対象が4ブロックしかないため3要素の部分集合は数通りしかなく、ランダムに3層選ぶとtop 3と構造的に重複してしまう。したがってこのアーキテクチャではk=3の比較でRQ5に答えられない。

k=1なら比較は成立する。Phase 6のIOLEスイープ（全ブロックを同一予算で単独学習）が、ランダムに1層選んだ場合の分布そのものなので、これを対照として使う:

| 量 | cross entropy |
|---|---|
| top_1（decoder.decoder.layers.1） | 2.1606 |
| ランダム1層の期待値（全ブロック平均） | 2.2110 |
| top_1の優位 | 0.0504 |
| 最悪の単一層 | 2.2631 |
| 最良の単一層 | 2.1606 |

### validationでのfine-tuning比較

| 条件 | 対象層 | 学習パラメータ比 | CE | top-1 | top-5 | 学習秒 |
|---|---|---|---|---|---|---|
| frozen | none | 0.0000 | 2.1593 | 0.3901 | 0.7943 | 0.0000 |
| full | all | 1.0000 | 2.0201 | 0.4397 | 0.8156 | 11.9679 |
| top_1 | decoder.decoder.layers.1 | 0.2373 | 2.0331 | 0.4113 | 0.8085 | 7.3349 |
| top_3 | decoder.decoder.layers.1, encoder.Transformer.layers.1, decoder.decoder.layers.0 | 0.6526 | 2.0384 | 0.4326 | 0.8227 | 8.4307 |
| random_3 | encoder.Transformer.layers.1, decoder.decoder.layers.0, decoder.decoder.layers.1 | 0.6526 | 2.0392 | 0.4184 | 0.8227 | 8.4071 |

## 5. 最終test評価（Phase 8）

analysis_test の問題数: 24。手法・層ランキング・予算をすべてvalidationで固定した後、一度だけ評価した。

| 指標 | 公式checkpointのtest評価 |
|---|---|
| cross entropy | 2.2599 |
| top-1 | 0.3600 |
| top-5 | 0.7822 |
| valid rate | 1.0000 |
| examples | 225 |

### 固定条件のtest split評価

| 条件 | 学習パラメータ比 | CE | top-1 | MCTS exact | MCTS平均TED |
|---|---|---|---|---|---|
| frozen | 0.0000 | 2.2599 | 0.3600 | 0 | 12.5000 |
| full | 1.0000 | 2.0744 | 0.4444 | 0 | 11.0000 |
| top_1 | 0.2373 | 2.0940 | 0.4044 | 0 | 12.0000 |
| top_3 | 0.6526 | 2.1383 | 0.4089 | 0 | 11.0000 |
| random_3 | 0.6526 | 2.1343 | 0.4044 | 0 | 10.0000 |

## 6. RQ8 — 事前学習分布との距離（Phase 9）

| 項目 | 値 |
|---|---|
| クエリ数 | 44 |
| カタログ数 | 800 |
| カタログ生成元 | GDExpr.random_fill_expr (official pretraining grammar) |
| 平均 retrieved_nearest_ted（skeleton） | 3.9773 |
| 平均 retrieved_nearest_ted（raw） | 4.1591 |

公式の式文法からサンプリングしたカタログに対する近似検索であり、100万件の事前学習アーカイブ全体との厳密な最近傍ではない。そのため plan §12 に従い retrieved_nearest_ted と表記する。

