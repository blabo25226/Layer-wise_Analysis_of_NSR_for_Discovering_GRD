# GPU_RUN4 研究結果まとめ

- 作成日: 2026-08-19
- 対象run: `results/runs/gpu_run4_phase0_01`（gitignore。数値の正本は各Phaseの `eval.json`）
- 計画書: [`plan.md`](plan.md)
- 実行入口: [`README.md`](README.md)
- 実行環境: Linux / Python 3.10.20 / torch 2.5.1+cu124 / NVIDIA GeForce RTX 2070 / Intel Core i7-8700
- 対象モデル: 公開ODEFormer checkpoint（SHA256 `56754040be5aa92ed4767fc43ee2008faa293f87c12b643e66c7df3e1623a5e8`）
- アーキテクチャ: 4 encoder（dim 256）+ 12 decoder（dim 512）、16 heads、60,646,773 parameters、ranking対象16層
- 世代: **GPU_RUN4**。GPU_RUN1 / GPU_RUN2 / GPU_RUN3 と評価設計・モデルが異なるため、数値を同一表に混ぜてはならない。

本レポートは、§1–§4 を事実（保存JSONからの転記と、同じJSON上の再集計）、§5 をRQ判定、§6 を考察、§7 を限界、§8 を提案として区別する。

---

## 0. 要旨

GPU_RUN4は plan の二大目標——**公開ODEFormerの再現** と **encoder / decoder全層の層解析** ——を、公開checkpointで Phase 0–9 まで実施した。

**再現について。** 公式demoは reconstruction $`R^2\approx 0.997`$ で成功した。ODEBench 63系 × 4 corruption（ $`\sigma\in\{0,0.05\}`$ 、 $`\rho\in\{0,0.5\}`$ 、1 seed）では valid 0.921、reconstruction $`R^2`$ 中央値 0.980、 $`R^2>0.9`$ は 0.647 である。一方 canonical exact は 0、skeleton exact は 0.075（19/252、実質6系）、beam 50 内に真skeletonがある割合は 0.091 である。高reconstructionは式回復を意味しない。

**層解析について。** 公式generatorから独立corpus 48/16/16 を作り、skeleton漏洩は0、ODEBenchはfine-tuningに使っていない。probe（encoderのみ）、causal ablation、IOLE の上位層は一致しない。4 Adam step の選択FTでは frozen の analysis-test CE が最も良く、full は悪化した。「少数層がfull / randomに勝つ」は支持されない。

**論文アーキテクチャについて。** 公開重みは論文Tableの 4+16 / dim 512 / 約86M と一致しない。本runの結果は **公開4+12 / 約61Mモデル** のreduced再現であり、論文サイズモデルの再現ではない。

---

## 1. 実験の位置づけ

### 1.1 二大目標

| 目標 | 計画上の内容 | 本runでの到達 |
|---|---|---|
| A. 再現 | 公開checkpoint、ODEBench、beam sampling 50、reconstruction / generalization / symbolic recovery | reduced gridで実施。論文Figure 4の $`\sigma`$ 6点・3 seedsではない |
| B. 解釈 | 20層（論文4+16）のprobe / CKA / DecoderLens / IOLE / ablation / 介入 / 選択FT | 公開checkpointの **16層** で実施。DecoderLens、logit-lens、activation patching、更新感度は未実施 |

中心的な問い（plan §1.3）は次の3つである。

1. 公開ODEFormerは、trajectoryだけでなく真のODE数式をどの程度回復できるか。
2. どの層に数式情報が形成され、どの層が因果的に寄与するか。
3. 重要層だけのfine-tuningまたは介入で、数式回復とgeneralizationは変わるか。

本runが直接答えられるのは (1) のreduced版と、(2)(3) の **teacher-forcing CE 上の短いFT** までである。介入後のbeam 50 decodeは行っていない。

### 1.2 論文Tableとの不一致（Phase 0で確定）

Go 1のarchitecture照合は失敗した。以降は `architecture_target: released_checkpoint_4enc_12dec_61M` に固定した。

| 項目 | 論文 | parser default | 公開checkpoint |
|---|---|---|---|
| encoder層 | 4 | 4 | 4 |
| decoder層 | 16 | 12 | 12 |
| encoder dim | 512 | 256 | 256 |
| decoder dim | 512 | 256 | 512 |
| heads | 16 | 16 | 16 |
| パラメータ | 約86M | — | 60,646,773 |
| beam | sampling 50 / 0.1 | sampling 1 / 0.1 | sampling 50 / 0.1 |

コメントアウトされていた旧Google Drive ID `18CwlutaFF_tAOObsIukrKVZMPmsjwNwF` はODEFormerではなく `symbolicregression` pickleであり、86Mモデルではない。

公式demo（READMEの2D軌跡、50点）: 50候補、再積分 $`R^2=0.9966`$、約1.93秒。選択式は線形式 `-2.0213 * x_1 + -0.3184 * x_0 \| 0.5587 * x_0 + 0.3372 * x_1`。真の軌道は $`2.3\cos(t+0.5)`$ / $`1.2\sin(t+0.1)`$ であり、線形ODEでよくfitできる例である。

---

## 2. 事実：provenance と予算

| 項目 | 値 |
|---|---|
| run-id | `gpu_run4_phase0_01` |
| checkpoint SHA256 | `56754040be5aa92ed4767fc43ee2008faa293f87c12b643e66c7df3e1623a5e8` |
| ODEBench fingerprint | `strogatz_equations.py` SHA256 `06bbb9dae2886a82f0a1d4b0cd062d063241bcfed56c01ef2a3a01d863bcf8b4`（63 systems） |
| corpus fingerprint | `a510a889…5217f7` |
| 実行開始時git | ルート `manifest.json` は commit `0641fa7`、status は `running` のまま |
| 文書化commit | `7b9393d`（Phase 2–9実装。実行後の記録） |
| seed | data_seed 101 のみ（bundleは3つ定義済みだが本runは1 seed） |
| 推論 | beam sampling 50、temperature 0.1、rescaleあり、候補選択は reconstruction $`R^2`$ |
| 層解析corpus | 公式 `env.gen_expr`、train 48 / val 16 / test 16 |
| FT | Adam 4 steps、lr $`10^{-4}`$、teacher-forcing CE |

### 2.1 計画正本より小さい点

[`configs/gpu_run4/base.yaml`](../configs/gpu_run4/base.yaml) の `full:` が本runの実施予算である。plan の論文グリッド（ $`\sigma`$ を 0 から 0.05 まで 0.01刻み、3 seeds、約2万式corpus、介入後beam 50）は未実施である。

### 2.2 計算時間（runnerが書いた wall seconds）

| Phase | 内容 | 秒 |
|---|---|---|
| 1 | 評価器freeze | 3 |
| 2 | ODEBench 252 cells + opt 32 | 1116 |
| 3 | beam診断（保存候補の再集計） | 0 |
| 4 | corpus生成 | 99 |
| 5 | probe / CKA / gradient | 4 |
| 6 | residual-zero ablation | 8 |
| 7 | IOLE + full FT | 15 |
| 8 | 選択FT（validation） | 9 |
| 9 | analysis-test 一度きり | 12 |

Phase 2の選択recordの推論時間中央値は約1.89秒/cell、合計約874秒である。残りは積分・評価・optのオーバーヘッドである。

### 2.3 評価器（Phase 1、本実験前に凍結）

ODEBench 63式をすべてparseし、恒等比較のcanonical TEDは0、prefix往復は63/63。gold 11件成功。component順 `x_0 | x_1` と `x_1 | x_0` は並べ替えず非同値とする。

- `normalized_ted` = $`\mathrm{ted}_{raw} / (\mathrm{size}_{true} + \mathrm{size}_{pred})`$ 。多次元では比較用に `system` ノードを1つ足す。
- skeletonは数値葉と `c_i` を `CONST` にする。整数指数も対象なので、 $`x^2`$ と $`x^3`$ はskeleton一致になる。
- Inf/NaNをequivalentへ強制しない。CASは合算ノード数40超で省略。

test結果を見てからこの定義は変えていない。

---

## 3. 事実：Result A（再現）

出典: `phase2/eval.json`、`phase2/selected.json`、`phase3/eval.json`、`phase3/beam_groups.json`。

主集計は ODEFormer（optなし）の 252 cells である。平均 $`R^2`$ は外れ値で壊れる（reconstruction mean $`-6.42`$）ため、主に中央値と率を読む。Studentのt区間は252点を独立標本とみなしており、同一モデル・関連する系の間では過信できない。

### 3.1 全体

| 項目 | 値 |
|---|---|
| cells | 63 systems × 4 corruptions = 252 |
| valid | 232 / 252 = 0.921 |
| reconstruction $`R^2>0.9`$ | 163 / 252 = 0.647 |
| reconstruction $`R^2`$ 中央値 | 0.980（valid n=232） / 0.971（invalidを $`-1`$ に罰則、n=252） |
| generalization $`R^2`$ 中央値 | 0.696（有限値 n=226） / 0.593（罰則 n=252） |
| canonical exact | 0 / 252 |
| symbolic equivalent | 0 / 252 |
| skeleton exact | 19 / 252 = 0.075 |
| TED 中央値 | 16 |
| 予測complexity 中央値 | 17 |
| 失敗タグ | NaN 18、CandidateIntegrationFailure 10（合計28。recon成功でgenのみ失敗が8件。invalidは20） |

variable F1の中央値は1.0（247/252が1.0）である。観測次元の変数をほぼ全部使う予測が多く、変数選択の識別力は低い。

### 3.2 noise / subsampling（各63系）

valid行のreconstruction中央値である。

| $`\sigma`$ | $`\rho`$ | valid | $`R^2>0.9`$ | skeleton | recon中央値 | gen中央値 |
|---|---|---|---|---|---|---|
| 0 | 0 | 59/63 | 42 | 6 | 0.986 | 0.699 |
| 0 | 0.5 | 59/63 | 41 | 6 | 0.981 | 0.711 |
| 0.05 | 0 | 58/63 | 44 | 3 | 0.969 | 0.759 |
| 0.05 | 0.5 | 56/63 | 36 | 4 | 0.980 | 0.678 |

reconstruction中央値は4セルとも高い。skeletonは無ノイズで6/63、ノイズありで3–4/63へ減る。 $`R^2>0.9`$ は $`\sigma=0.05,\rho=0.5`$ で36/63と最も低い。

### 3.3 次元別

| 次元 | n | valid | $`R^2>0.9`$ | skeleton | recon中央値（valid） |
|---|---|---|---|---|---|
| 1 | 92 | 88 | 82 | 17 | 0.997 |
| 2 | 112 | 111 | 67 | 2 | 0.946 |
| 3 | 40 | 25 | 8 | 0 | 0.698 |
| 4 | 8 | 8 | 6 | 0 | 0.906 |

1次元は当てはまりもskeletonも相対的に良い。3次元はvalidが25/40まで落ち、skeletonは0である。

### 3.4 skeletonが一致した系

19件は次の6系に集中する（ $`\sigma=0,\rho=0`$ の代表）。canonical exactはいずれも0で、定数の数値は真の $`c_i`$ と一致していない。

| 系 | 名前 | 真式（要約） | 予測（要約） | recon $`R^2`$ | TED |
|---|---|---|---|---|---|
| 1 | RC-circuit | $`(c_0-x_0/c_1)/c_2`$ | $`0.2835-0.3557 x_0`$ | 0.9999 | 2 |
| 2 | Population growth | $`c_0 x_0`$ | $`0.2309 x_0`$ | 0.9998 | 1 |
| 6 | Autocatalysis | $`c_0 x_0-c_1 x_0^2`$ | $`2.32 x_0-0.557 x_0^2`$ | 0.990 | 2 |
| 9 | Language death | $`(1-x_0)c_0-x_0 c_1`$ | $`0.3315-0.6238 x_0`$ | 0.9994 | 2 |
| 12 | Photons in a laser | $`c_0 x_0-c_1 x_0^2`$ | $`1.68 x_0-0.104 x_0^2`$ | 0.971 | 2 |
| 31 | SIR (2D) | $`-c_0 x_0 x_1 \mid c_0 x_0 x_1-c_1 x_1`$ | 同skeletonの数値版 | 0.989 | 3 |

1次元の線形・二次と、双線形の感染モデル1つである。これ以外の57系では、4 corruptionのどこでも真skeletonがbeam内に毎回は出ていない（後述）。

### 3.5 当てはまるが式が違う例（qualitative panel、 $`\sigma=0,\rho=0`$）

planが指定したパネル `[9, 16, 27, 40, 52, 54, 62, 63]`。

| 系 | 名前 | skeleton | recon | gen | TED | 要点 |
|---|---|---|---|---|---|---|
| 9 | Language death | 一致 | 0.999 | 0.809 | 2 | 線形skeleton。定数は異なる |
| 16 | Landau | 不一致 | 0.998 | 0.969 | 16 | 5次を入れ子多項式で近似 |
| 27 | Lotka–Volterra | 不一致 | 0.928 | $`-2.54`$ | 15 | 再構成は良いが新初期値で崩壊 |
| 40 | Duffing | 不一致 | 0.949 | 0.632 | 18 | $`\sin`$ を挿入 |
| 52 | Maxwell–Bloch | 不一致 | 0.868 | $`-48.0`$ | 17 | genが大きく負 |
| 54 | Lorenz | 不一致 | 0.468 | 0.310 | 18 | 再構成自体が低い |
| 62 | Binocular rivalry | 不一致 | 0.982 | 0.892 | 36 | sigmoidを線形で代用 |
| 63 | SEIR | 不一致 | 0.900 | $`-0.024`$ | 21 | 再構成0.9でもgenは0付近 |

`ODEFormer (opt)` は同パネル × 4 corruption の32件である。recon中央値0.906、skeleton exact 0.125。 $`\sigma=0,\rho=0`$ では上表と同じ予測式になっており、このパネルでは定数再最適化が式構造を変えていない。

### 3.6 RQ3: generation 対 selection

出典: `phase3/beam_groups.json`（252 groups）。

| 項目 | 値 |
|---|---|
| 真skeletonがbeam内 | 23 / 252 = 0.091 |
| うち selection gap TED = 0 | 18 |
| うち gap > 0（取り逃がし） | 5 |
| 系として常にin-beam | 5系（2, 6, 9, 12, 31） |
| ときどきin-beam | 1系（1） |
| 一度もin-beam | 57系 |
| unique skeletons / beam 平均 | 9.19 |
| 平均 selection gap TED | 2.94 |
| 平均 selected TED | 17.26 |
| 平均 oracle TED（beam内最良） | 14.31 |

取り逃がし5件は系1, 9, 12, 31のノイズあり条件に限られる。 **失敗の主因は選択ではなく、真skeletonをbeamに出せていないこと** である。ただしoracle TEDの平均も14.3であり、真skeletonが無いbeamでも「より近い木」は少し選べている。

---

## 4. 事実：Result B（層解析）

出典: `phase4/eval.json`、`phase5/eval.json`、`phase6/eval.json`、`phase7/eval.json`、`phase8/eval.json`、`phase9/result_b.json`。

層解析はODEBenchではなく独立corpusである。rankingはvalidationのみ。analysis-testはPhase 9で一度だけ評価した。

### 4.1 corpus（Phase 4）

| 項目 | 値 |
|---|---|
| train / val / test | 48 / 16 / 16 |
| skeleton漏洩 | train–val 0、train–test 0、val–test 0 |
| 生成失敗 | 0 |
| teacher-forcing CE（4本の記録） | 1.202、1.726、1.696、1.518 |

ODEBenchはFTに使っていない。generatorは `gen_expr(train=True)` をtest分割にも使っている。skeleton漏洩は0だが、公式のtrain/test生成モード切替ではない。

### 4.2 観測的解析（Phase 5）

probeは **encoder 4層だけ** である。decoder hiddenの抽出は本runの実装に含まれない。タスクはdimension分類、complexity回帰、`sin` の有無。n_val=16、dimensionは6クラス、majority baselineは0.208。

dimension accuracy（validation）:

| 層 | probe | ラベルシャッフル対照 |
|---|---|---|
| encoder_0 | 0.8125 | 0.1875 |
| encoder_1 | 0.6875 | 0.1875 |
| encoder_2 | 0.625 | 0.125 |
| encoder_3 | 0.625 | 0.1875 |

complexity $`R^2`$ は encoder_2 が 0.562 で最高、encoder_0 は負である。`has_sin` accuracyは0.56–0.69で、majority 0.604を大きくは超えない。

encoder CKA（validation）は全対で 0.921–0.978 と高い。表現は近いが、dimension probe順位は encoder_0 が最上位である。

gradient norm（validation CE）はencoderがdecoderより大きい。上位は `encoder_0`, `encoder_3`, `encoder_2`, `encoder_1`、その次が `decoder_8`。絶対値は $`10^{-8}`$–$`10^{-6}`$ である。

### 4.3 因果ablation（Phase 6）

各層のattention/FFN残差を0にする。指標は **介入後のteacher-forcing CE増分** であり、beam 50 decodeではない。control hook（恒等）はbaselineを変えていない（`control_hook_ok: true`）。

$`\Delta`$ CE 上位:

| 層 | $`\Delta`$ CE |
|---|---|
| encoder_3 | 10.40 |
| decoder_3 | 2.47 |
| decoder_0 | 1.89 |
| decoder_2 | 1.16 |
| encoder_2 | 0.93 |

encoder_3 のゼロ化は桁違いにCEを壊す。IOLE上位の `decoder_7` は $`\Delta`$ CE 0.43 で中位である。

### 4.4 IOLE と full FT（Phase 7、validation、4 steps）

frozen val CE = 1.703。iole_score は frozenからの改善（下がると正）。

| 条件 | val CE | $`\Delta`$ vs frozen |
|---|---|---|
| decoder_7 | 1.697 | $`-0.0061`$ |
| encoder_0 | 1.699 | $`-0.0045`$ |
| encoder_2 | 1.700 | $`-0.0036`$ |
| encoder_1 | 1.700 | $`-0.0035`$ |
| … | … | 変化は $`10^{-3}`$ 以下 |
| decoder_9 | 1.706 | $+0.0025$ |
| full（61M） | 1.713 | $+0.0096$ |

4 stepではどの単層も改善が小さく、fullはvalidationでも悪化する。IOLE順位の先頭は `decoder_7`, `encoder_0`, `encoder_2`。

### 4.5 選択FT（Phase 8 validation freeze → Phase 9 test一度きり）

Phase 8で層集合をvalidation rankingから固定した。random 3集合は3つ。test CE:

| 条件 | 層 | trainable パラメータ | test CE |
|---|---|---|---|
| frozen | なし | 0 | **1.674** |
| causal_top3 | encoder_3, decoder_3, decoder_0 | 8,668,928 | 1.679 |
| top1 | decoder_7 | 3,939,840 | 1.682 |
| random3_1 | decoder_1, 5, 6 | 11,819,520 | 1.683 |
| random3_0 | decoder_0, 7, 10 | 11,819,520 | 1.690 |
| bottom3 | decoder_9, 10, 11 | 11,819,520 | 1.692 |
| random3_2 | decoder_1, 8, 9 | 11,819,520 | 1.693 |
| top3 | decoder_7, encoder_0, encoder_2 | 5,518,336 | 1.696 |
| full | 全パラメータ | 60,646,773 | 1.797 |

**すべてのFT条件がfrozenより悪い。** fullが最悪である。validationでは top3 が 1.690 でfrozen 1.703より良かったが、testでは逆転した。

指標間の上位3層:

| 指標 | 1位 | 2位 | 3位 |
|---|---|---|---|
| probe dimension（encoderのみ） | encoder_0 | encoder_1 | encoder_2 |
| gradient norm | encoder_0 | encoder_3 | encoder_2 |
| causal $`\Delta`$ CE | encoder_3 | decoder_3 | decoder_0 |
| IOLE | decoder_7 | encoder_0 | encoder_2 |

一致していない。planが求めた「一つの層重要度」にはまとまらない。

---

## 5. 研究質問ごとの判定

判定は本runの予算に対して行う。論文アーキテクチャ・3 seeds・beam介入は対象外である。

| RQ | 問い | 判定 | 根拠 |
|---|---|---|---|
| RQ1 | reconstruction / generalization / robustness | **部分的に支持** | recon中央値は高い。gen中央値は0.70で reconより低い。 $`\sigma=0.05`$ でもrecon中央値は維持。3次元と一部パネルでgenが崩壊 |
| RQ2 | 真のODE数式の回復 | **未支持** | canonical / CAS exact 0。skeleton 7.5%で6系に集中。高reconは構造回復を含意しない |
| RQ3 | beam内生成 vs 選択の取り逃がし | **生成失敗が主** | in-beam 9.1%、取り逃がしは5/252。57系は一度も真skeletonを出していない |
| RQ4 | 層ごとの情報表現 | 判定不能（部分観測） | encoderのdimensionは読める。decoder probe、演算子・変数・木構造・next tokenは未測定 |
| RQ5 | readout可能な層は因果的にも効くか | **本データでは一致しない** | probe上位 encoder_0 は因果 $`\Delta`$ CEでは11位。因果1位 encoder_3 はprobeでは最下位側 |
| RQ6 | decoder深さに沿った式構造の形成 | **未実施** | DecoderLens / TED軌跡なし |
| RQ7 | 少数層FTがfullに近づき、topがrandomより良いか | **未支持** | 4 stepではfrozenが最良。top3はrandom3よりtest CEが悪い |
| RQ8 | 難易度（次元・noise）依存 | **観察のみ** | 1Dでskeletonが集まり、3Dでvalidとreconが落ちる。seed=1のため一般化しない |

接続問い（重要層FTで数式回復が変わるか）は、CE以外のsymbolic指標をtestで測っていないため **判定不能** である。

---

## 6. 考察（推測）

ここから先はJSONから論理的に読み取れる解釈であり、追加実験で覆り得る。

1. **ODEFormerの公開モデルは「軌道を説明する近似ODE」は出せるが、「真の支配方程式」はほとんど出せない。** 1D線形・二次とSIR型の双線形だけがskeleton一致する。LandauやBinocular rivalryのように recon $`R^2>0.98`$ でも木構造は別物である。これはGPU_RUN2がGNW有理式で見た「数値は合うが構造は回復しない」と同型の観察だが、モデルもデータも違うので数値の比較はしない。

2. **generalizationの崩壊は、誤った式が観測軌道上でだけ合うときに起きる。** Lotka–Volterra（recon 0.928、gen $`-2.54`$）とMaxwell–Bloch（gen $`-48`$）が典型である。論文が reconstruction と generalization を分ける理由は、本runでも必要である。

3. **beam 50 を増やせば式が直る、とはこの結果から言えない。** 平均9個の異なるskeletonしか出ておらず、57系では真skeletonが一度も無い。選択関数をTED oracleに変えても平均TEDは17.3→14.3にしかならない。

4. **層順位の不一致は、指標が別物を測っているためで、どれかが実装バグだとまでは言えない。** probeはencoder pooled hiddenから次元を読む。causalは残差ゼロ化後のTF CEである。IOLEは4 stepの微小なCE差（ $`10^{-3}`$ ）で並べている。このIOLE差はn_val=16とstep数に対して小さすぎ、順位の安定性は未知である。

5. **frozenがFTに勝った主因は、学習不足というより短いFTが事前学習を壊した可能性が高い。** fullはvalでもtestでも悪化し、train lossの最終値はfrozen CEより高い（約1.88）。4 step・lr $`10^{-4}`$ ・train 48式では、選択FTの仮説検定になっていない。

6. **encoder_3 の因果スコアが大きいことは、「最終ブロックが必要」以上の機能分解ではない。** 出力に近いencoder段をゼロにすれば表現が壊れるのは予想できる。decoder_7 がIOLE首位でも因果中位なのは、短いFTで動く場所と、ゼロ化すると壊れる場所が違う、というGPU_RUN3でも見た乖離と同方向である。ここもモデルが違うので強度の比較はしない。

---

## 7. 限界（事実）

- 公開4+12 / 61M であり、論文4+16 / 86M ではない。ranking層数は16であり20ではない。
- 1 seed。corruptionは $`\sigma`$ 2点 × $`\rho`$ 2点だけ。
- Phase 2のrecordは `split=validation` とラベルされているが、ODEBench再現の報告用であり層選択には使っていない。名前は紛らわしい。
- `valid` は parse + reconstruction成功であり、gen失敗は別タグである。`penalized_*` は $`R^2`$ 以外でNaNを落とし、分母が232になることがある。skeleton率の主報告は未罰則の 19/252 を使う。
- probeはencoderのみ。decoder probe、DecoderLens、logit-lens、activation patching、update sensitivity、介入後beamは未実施。
- 因果指標とFT指標はTF CEであり、TED / skeleton / gen $`R^2`$ ではない。
- IOLE/選択FTは4 step、corpus 80式。planの大規模corpusではない。
- ルート `manifest.json` のstatusは `running`、実行commitはコード最終版と一致しない。
- ヒトデータ・DREAM4・NeSymReS比較・生物学的機構の主張は対象外。

---

## 8. 提案（未実施）

科学的に望ましい順で、本リポジトリで実行可能なものに限る。

1. **式回復を主指標にした報告を維持する。** reconstruction中央値だけを「再現成功」と書かない。本レポートのResult A表を論文下書きの既定にする。
2. **選択FTを主張するなら、validationでstep数とlrを探索し、analysis-testは一度だけ、指標をskeleton / TED / gen $`R^2`$ にする。** 4 step CEの再掲ではRQ7は閉じない。
3. **decoder hiddenのprobeとDecoderLensを追加してからRQ4/RQ6を再判定する。** 現状の「encoder_0がdimensionを持つ」だけでは16層解析になっていない。
4. **論文グリッドへ拡大する前に、公開4+12を対象とする旨を図表キャプションへ固定する。** 86M重みが見つかった場合は別run-idにする。
5. Result Aの valid 率、 $`R^2>0.9`$、skeleton 率に対して 3 seeds を先に足す。層FTの前に、beamの生成失敗がseedで動くかを見る方が安い。

---

## 9. 出典ファイル

すべて `results/runs/gpu_run4_phase0_01/` 配下。

| 内容 | ファイル |
|---|---|
| 環境・checkpoint・Go 1 | `phase0/preflight.json`, `phase0/architecture_audit.json`, `phase0/official_demo.json` |
| 評価器freeze | `phase1/eval.json` |
| Result A 集計 | `phase2/eval.json`, `phase2/selected.json` |
| beam診断 | `phase3/eval.json`, `phase3/beam_groups.json` |
| 解析corpus | `phase4/eval.json`, `phase4/corpus.json` |
| probe / CKA / grad | `phase5/eval.json` |
| ablation | `phase6/eval.json` |
| IOLE | `phase7/eval.json` |
| 選択FT（val） | `phase8/eval.json`, `phase8/conditions.json` |
| 統合 | `phase9/eval.json`, `phase9/result_a.json`, `phase9/result_b.json` |

実行手順と短縮表は [`README.md`](README.md)、計画の正本は [`plan.md`](plan.md) である。
