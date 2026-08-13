# GPU_RUN2 計画

作成日: 2026-07-29

GPU_RUN1結果反映: 2026-07-30

方針改訂: 2026-08-12

## 1. 目的と範囲

GPU_RUN2では、GPU_RUN1で判明した計算量、CPU律速、設定の途中変更、symbolic recoveryが0だった問題を踏まえ、
**合成データだけ**を用いてNeSymReSの層解析と数式構造回復を検証する。

目的は次の3点である。

1. encoder・decoder各層の役割をprobe、fine-tuning、ablation、表現類似度、activation介入から調べ、
   encoder層にはDecoderLensも適用する。
2. 少数の重要層だけをfine-tuningした条件が、全層学習およびrandom層学習と比べて、数値精度だけでなく
   正しい式の構造を回復できるか検証する。
3. 真の式と各手法の予測式をproblem単位で直接見比べられる成果物を残す。

GPU_RUN2では次を扱わず、GPU_RUN3以降へ保留する。

- 有限差分で微分値を近似する問題
- DREAM4
- ヒト時系列データ
- empirical regulator selectorなど、oracle以外の変数選択
- 実データからの新規GRN候補方程式の提案

したがって、GPU_RUN2の主張は「既知の真式を持つ合成データ上での層解析とsymbolic recovery」に限定する。
DREAM4やヒトデータへの転移性能、有限差分誤差への頑健性、regulator selection性能はGPU_RUN2の結果から主張しない。

GPU_RUN1の確定結果と限界は
[`results/GPU_RUN1_report.md`](../results/GPU_RUN1_report.md)を参照する。

### 1.1 GPU_RUN1からの出発点

| 観測 | GPU_RUN2での扱い |
|---|---|
| `decoder_2`〜`decoder_4`の寄与が高かった | 独立runのprobe、fine-tuning、ablationで再確認し、testを見る前に候補を固定する |
| Top 1〜3は全層FTとNMSE同等性margin内で同等だった | 独立runで再現性、symbolic recovery、計算資源削減を確認する |
| Top 3対random 3の差は未確定だった | 事前生成した複数のrandom層集合とpaired比較する |
| symbolic recoveryは全条件で0だった | 真式対予測式の比較を主成果物にし、失敗理由まで保存する |
| TPSRの追加改善に大きな計算時間を要した | profilerとGo/No-Goを通った場合だけ副次比較する |
| DREAM4の経験的selector F1が低かった | GPU_RUN2では変数選択問題を切り離し、oracle変数だけを入力する |
| `tan`と危険な除算を含む式が多かった | 合成データの真式と整合するoperator allowlist、安全性検査を使う |

### 1.2 事前に固定する主判定

1. **層の役割と再現性**：probe、単一層fine-tuning、ablation、表現類似度、activation介入が示す
   重要層と機能を比較し、encoder層ではDecoderLensの結果も照合する。相関的な結果と介入結果を区別する。
2. **全層同等性**：Top 1〜3と全層FTのfailure-penalized NMSE差について、95% Studentのt区間全体が
   事前margin `[-0.05, 0.05]`へ入るかを判定する。
3. **rankingの付加価値**：Top条件と事前生成したrandom層集合平均のpaired NMSE差を報告する。
   95% t区間が0をまたぐ場合、優越性または同等性を主張しない。
4. **構造回復**：exact、skeleton、symbolic equivalence、complexityを条件別に報告する。
   NMSEが小さくても構造回復が失敗した場合は、数式回復成功と判定しない。
5. **noise頑健性**：`noise=0.0`と`noise=0.1`を独立条件として比較し、結果を混ぜて集計しない。

seed数、random集合数、学習budget、decode budgetはvalidation pilot後かつtest評価前に固定する。

### 1.3 特定論文を参照する内容

本計画のうち、特定の論文を直接参照して設計した内容を次に示す。各論文から採用する範囲と、
GPU_RUN2で独自に定める範囲を区別する。表にないoracle条件、noise、split、timeout、保存schema、
Go / No-Go条件は、特定の1論文を再現するものではなく、本研究の目的とGPU_RUN1の結果に基づく計画固有の設計である。

| 対象内容 | 参照論文・ローカル資料 | GPU_RUN2で参照する範囲 |
|---|---|---|
| NeSymReSのモデルと標準decode | Biggio et al., “Neural Symbolic Regression that Scales,” ICML 2021（[`NSRS_translated.md`](../docs/translated_paper/NSRS_translated.md)） | set encoderとautoregressive decoderによる数式生成、事前学習済みモデルの前提 |
| IOLEに基づく単一層fine-tuning | Zhang et al., “Is One Layer Enough? Training a Single Transformer Layer Can Match Full-Parameter RL Training,” arXiv:2607.01232v2（[`IOLE_translated.md`](../docs/translated_paper/IOLE_translated.md)） | 1層だけを更新して全層学習と比較する実験設計。対象モデルと学習設定が異なるため、NeSymReS向けに適応し、同じ結果になる根拠とはしない |
| CKAによる表現類似度 | Kornblith et al., “Similarity of Neural Network Representations Revisited,” ICML 2019（[`CKA_translated.md`](../docs/translated_paper/CKA_translated.md)） | 層表現を比較するCKAの定義と解釈 |
| DecoderLens | Langedijk et al., “DecoderLens: Layerwise Interpretation of Encoder-Decoder Transformers,” arXiv:2310.03686v2（[`DecoderLens_translated.md`](../docs/translated_paper/DecoderLens_translated.md)） | encoder中間層の表現を最終decoderへ渡し、生成結果の変化を観察する解析 |
| GNW合成式 | Schaffter, Marbach, and Floreano, “GeneNetWeaver,” *Bioinformatics* 2011（[`GNW_translated.md`](../docs/translated_paper/GNW_translated.md)） | Hill型転写制御式、regulatory module、状態混合 |
| PySR baseline | Cranmer, “Interpretable Machine Learning for Science with PySR and SymbolicRegression.jl,” arXiv:2305.01582v3（[`PySR_translated.md`](../docs/translated_paper/PySR_translated.md)） | genetic programmingによるbaselineの位置付け。探索budgetとoperatorはGPU_RUN2側で公平に固定する |
| TPSR | Shojaee et al., “Transformer-based Planning for Symbolic Regression,” NeurIPS 2023（[`TPSR_translated.md`](../docs/translated_paper/TPSR_translated.md)） | MCTSを用いるtest-time探索と計算量比較 |
| 再現バイアスとNSR-gvs | Sato and Sato, “Can Test-time Computation Mitigate Reproduction Bias in Neural Symbolic Regression?”, arXiv:2505.22081v2（[`CTC_NSR_translated.md`](../docs/translated_paper/CTC_NSR_translated.md)） | template再現率、included / not-included相当の比較、NSR-gvs feasibility |

## 2. GPU_RUN2で固定する前提

- Python 3.10を維持する。
- データは第3節で定める合成データだけを使用する。
- noiseは`0.0`と`0.1`の2条件とする。
- 変数選択はoracleだけとし、各真式に実際に含まれる変数だけをモデルへ渡す。
- 解析的に計算した真の微分値を教師値とし、有限差分は使用しない。
- Phase 4の層選択とhyperparameter選択にはvalidationだけを使う。
- testは方法、層、operator、timeout、budgetを固定した後に一度だけ評価する。
- 同じseed内の比較条件では、初期checkpoint、データ順、乱数状態をそろえる。
- failure-penalized NMSE、valid rate、真式、予測式、候補式、失敗理由を保存する。
- GPU_RUN1とGPU_RUN2は独立runとして保存し、同一世代のseed反復へ混ぜない。
- 実行中にsource commitまたは主設定を変更しない。

### 2.1 oracle変数条件の定義

GPU_RUN2におけるoracleとは、各problemの真式に実際に現れる入力変数の集合を、変数選択器を介さず
NeSymReS、PySR、TPSRへ直接与える実験条件を指す。対象遺伝子を$`i`$、真式を$`f_i`$とすると、
oracle regulator集合を次で定義する。

```math
R_i^{\mathrm{oracle}}
=\left\{j\ne i\mid x_j\ \text{appears in}\ f_i\right\}
```

モデルへ渡す入力集合は、対象遺伝子自身を先頭に置いた次の集合とする。

```math
X_i^{\mathrm{oracle}}
=\left[x_i,\ \mathrm{sort}\!\left(R_i^{\mathrm{oracle}}\right)\right]
```

ここで「真式に現れる」とは、canonical SymPy式を簡約した後も自由変数として残ることをいう。
係数が0になった項、簡約により消える変数、データ上で相関しているだけの変数は含めない。
同じ変数が複数項に現れても入力列は1本だけとし、regulatorは元のgene IDの昇順へ固定する。
自己変数$`x_i`$は、分解・希釈項を表すためregulator集合とは区別して常に入力へ含める。

oracleが与える情報と与えない情報を次のように固定する。

| 項目 | oracleからモデルへ与えるか | 扱い |
|---|---:|---|
| 真式に現れる変数集合 | 与える | $`x_i`$と真のregulatorだけを入力する |
| 変数のモデル内列順 | 与える | $`x_i`$を先頭、regulatorをgene ID順に固定する |
| regulatorの有無 | 与える | empirical selectorは実行しない |
| 活性化・抑制の符号 | 与えない | モデルが数値点から推定する |
| 係数、Hill係数、閾値 | 与えない | モデルまたは後段の定数最適化が推定する |
| 演算子、式木、skeleton | 与えない | 共通operator allowlist内で探索する |
| 正解token列・正解式 | 与えない | 学習labelとして必要なtrain problemを除き、推論入力には使わない |
| testの評価値 | 与えない | 方法固定後の最終評価だけに使う |

oracle集合は合成problemを生成した機械可読な真式から自動抽出し、手作業で転記しない。
各recordには`target_variable`、`oracle_regulators`、`oracle_inputs`、`variable_order`、
`oracle_source_equation_id`を保存し、全手法へ同一の配列を渡すことをテストする。

この条件はregulator selection誤差を除去し、**与えられた正しい変数集合の下で式構造を回復できるか**を
測る上限評価である。未知データで利用可能な現実的変数選択法ではなく、変数選択に成功したことも意味しない。
したがってGPU_RUN2では、oracle条件のvariable precision、recall、F1は構成上すべて1で情報を持たないため
主性能指標にしない。代わりにexact、skeleton、symbolic equivalence、ID/OOD NMSE、complexity、valid rateを
主に報告する。oracle metadataはtest problemにも使用するが、これは事前宣言した実験条件であり、
層選択、hyperparameter選択、early stoppingにtestの予測結果を使うこととは区別する。

## 3. 合成データ仕様

### 3.1 観測値の作り方

GPU_RUN2では、ODE軌道から有限差分を計算しない。各problemについてoracle変数の入力点
$`\mathbf{x}`$を生成し、既知の真式$`f(\mathbf{x})`$を直接評価して教師値$`y`$を作る。

```math
y=f(\mathbf{x})+\epsilon
```

- 各入力変数の範囲は`[0.1, 2.0]`とする。
- data seedは`101`、`202`、`303`の3個、model training seedは`0`、`1`、`2`の3個とする。
- 各problem・各data seedについて、学習用1,024点、独立したID評価用256点、OOD評価用256点を
  Latin hypercube samplingで生成する。
- `noise=0.0`では$`\epsilon=0`$とする。
- `noise=0.1`では、clean targetの学習用1,024点における標準偏差を$`s_y`$として、
  $`\epsilon\sim\mathcal{N}(0,(0.1s_y)^2)`$とする。
- 入力点とnoiseのseedをmanifestへ保存する。
- 同一のclean入力点を`noise=0.0`と`noise=0.1`で共有し、noiseだけを変えるpaired設計にする。
- train、validation、testはproblem ID単位で分離する。行を混ぜてproblemの分割を作らない。
- ID評価点は`[0.1, 2.0]`、OOD評価点は`[0.05, 2.5]`から生成し、学習点とは共有しない。

### 3.2 GNWから採用する数式

合成式は独自に組み立てず、GeneNetWeaver（GNW）のHill型転写制御モデルから採用する。
出典はSchaffter, Marbach, and Floreano, “GeneNetWeaver: in silico benchmark generation and performance profiling
of network inference methods,” *Bioinformatics* 27(16), 2263–2270 (2011),
[DOI: 10.1093/bioinformatics/btr373](https://doi.org/10.1093/bioinformatics/btr373)とする。
数式の実装上の一次資料はGNW source commit `5016f55ab04c111f29d7d0b3a4881d4725d49467`の
`Gene.java`、`HillGene.java`、`RegulatoryModule.java`である。

GNWでは、gene $`i`$のmRNA量を$`x_i`$、最大転写速度を$`V_i`$、分解率を$`\delta_i`$、
regulatory moduleの平均活性を$`m_{ij}`$とする。GPU_RUN2で回復対象とするmRNA方程式は次である。

```math
\frac{dx_i}{dt}
=V_i\,\alpha_i(m_{i1},\ldots,m_{iM})-\delta_i x_i
```

module $`j`$のregulator $`r`$について、GNWと同じ無次元量を用いる。

```math
\xi_r=\left(\frac{x_r}{K_r}\right)^{n_r}
```

$`A_j`$をactivator集合、$`D_j`$をdeactivator集合とする。regulatorが独立に結合するmoduleの活性は
次である。

```math
m_j
=\frac{\prod_{r\in A_j}\xi_r}
{\prod_{r\in A_j\cup D_j}(1+\xi_r)}
```

activatorが複合体を形成して結合するmoduleでは、GNWの`bindsAsComplex`条件に従い次を用いる。

```math
m_j
=\frac{\prod_{r\in A_j}\xi_r}
{1+\prod_{r\in A_j}\xi_r
+\mathbf{1}_{|D_j|>0}\prod_{r\in A_j\cup D_j}\xi_r}
```

$`M`$個のmoduleのon/off状態を$`s\in\{0,1\}^M`$、その状態に対応する相対転写活性を
$`\alpha_{i,s}\in[0,1]`$とすると、gene全体の相対活性はGNWと同じ状態混合で表す。

```math
\alpha_i(m_{i1},\ldots,m_{iM})
=\sum_{s\in\{0,1\}^M}\alpha_{i,s}
\prod_{j=1}^{M}m_{ij}^{s_j}(1-m_{ij})^{1-s_j}
```

単一regulatorの場合には、上式から次の標準的なHill活性化・抑制を得る。

```math
f_{\mathrm{act}}(x_i,x_r)
=V_i\frac{x_r^{n}}{K^{n}+x_r^{n}}-\delta_i x_i
```

```math
f_{\mathrm{rep}}(x_i,x_r)
=V_i\frac{K^{n}}{K^{n}+x_r^{n}}-\delta_i x_i
```

GPU_RUN2 synthetic benchmark v1では、GNW式から次の8構造を固定する。$`x_1`$は対象mRNA、
$`x_2,x_3`$はoracle regulatorである。

| family ID | GNW由来の構造 | oracle入力 | module構成 |
|---|---|---|---|
| `G01` | 入力なし | $`x_1`$ | basal transcriptionとmRNA分解 |
| `G02` | 単一activator | $`x_1,x_2`$ | enhancer module 1個 |
| `G03` | 単一repressor | $`x_1,x_2`$ | repressor module 1個 |
| `G04` | 2 activators、独立結合 | $`x_1,x_2,x_3`$ | enhancer module 1個、`bindsAsComplex=false` |
| `G05` | 2 activators、複合体結合 | $`x_1,x_2,x_3`$ | enhancer module 1個、`bindsAsComplex=true` |
| `G06` | activator＋deactivator | $`x_1,x_2,x_3`$ | enhancer module 1個、独立結合 |
| `G07` | enhancer＋repressor | $`x_1,x_2,x_3`$ | 独立なmodule 2個 |
| `G08` | 2 enhancer modules | $`x_1,x_2,x_3`$ | 独立なenhancer module 2個 |

NeSymReSの主実行operator集合で真式を厳密に表現できるよう、Hill係数は
$`n\in\{1,2,3,4,5\}`$に制限する。$`n=1`$はべき乗tokenを使わず、$`n=2,3,4,5`$は
第3.3節の制限付き整数べき乗で表す。
これはGNWモデル族を変更するものではなく、GNWが許すparameter範囲の部分集合を使う制約である。
$`K`$、半減期、$`V_i`$、$`\alpha_{i,s}`$はGNWの初期化規則から生成し、採用した値と生成seedを
problem manifestへ保存する。GNW source treeは調査用であり、実行時に`GitHubSourceCode/GNW`へ依存しない。
必要な式生成処理だけを`src/`へ実装し、上記commitの数式と一致することをgolden testで確認する。

各familyについて30個、合計240個のparameter variantを生成する。variant生成seedは`20260812`とし、
familyごとに18 problemsをtrain、6 problemsをvalidation、6 problemsをtestへ割り当てる。
割り当ては一度だけ生成し、`eq_id`、family、module構成、split、全parameter、展開前のGNW式、canonical真式を
manifestへ明示する。同一variantまたはその入力行を複数splitへ入れない。この主splitは同じGNW構造内の
parameter一般化を測る設計であり、未知構造への一般化を測るものではない。

CTC_NSRの再現バイアス診断用に、同じ240 problemsから別の固定viewを作る。

- structure-train: `G01`–`G05`
- structure-validation: `G06`
- structure-test (`not included`相当): `G07`–`G08`

このviewを使うモデルはstructure-trainだけでfine-tuningし、structure-validationだけで設定を固定した後、
structure-testを一度だけ評価する。主splitで学習したcheckpointを流用しない。

### 3.3 operator allowlist

GNW benchmark v1の真式を表現でき、手法間で意味をそろえられる次の演算だけを主実行で許可する。

| 意味上の演算 | 制約 | 用途 |
|---|---|---|
| `add(a,b)` | 制限なし | 項と分母の加算 |
| `sub(a,b)` | 制限なし | 分解項などの減算 |
| `mul(a,b)` | 制限なし | 係数、変数、module項の積 |
| `div(a,b)` | 第3.3.1節の安全性検査を通ること | Hill式と状態混合の有理式 |
| `pow(a,k)` | 指数$`k`$はliteral整数`2`、`3`、`4`、`5`だけ | Hill項$`x^n`$と積の整数べき |
| 数値定数 | 各手法の定数表現を許可し、最終的に同じ定数最適化条件で比較 | $`V`$、$`K`$、$`\delta`$、$`\alpha`$ |

`pow(a,b)=a^b`を一般の二項演算子としては許可しない。指数側が変数、部分式、最適化対象の実数、
または許可範囲外の整数である候補は主実行の文法外とする。したがって、$`a^{x_2}`$、$`a^{0.7}`$、
$`a^{-2}`$などは不許可である。負の整数べきが必要な場合も、主実行では明示的な安全除算として表す。

手法ごとの表記差は次のように吸収する。

| 手法・段階 | 許可する表現 |
|---|---|
| NeSymReS / TPSR token列 | `add`、`sub`、`mul`、`div`、および指数childがliteral `2`–`5`の`pow` |
| PySR探索 | binary `+`、`-`、`*`、`/`と、unary `square`、`cube`、`pow4`、`pow5`。binary `^`は使わない |
| 共通評価 | すべてSymPyの`Add`、`Mul`、`Pow(base,k)`へcanonicalizeして比較 |

NeSymReSについては、Biggio et al., “Neural Symbolic Regression that Scales,” ICML 2021
（[`NSRS_translated.md`](../docs/translated_paper/NSRS_translated.md)）をモデルの参照論文とし、実際のcheckpointが
学習したoperatorは[`eq_setting.json`](../assets/nesymres/jupyter/100M/eq_setting.json)で確認する。同設定の
`pow2`–`pow5`と整数tokenに合わせて上記範囲を採用するが、一般のvariable exponentまで学習済みだとは解釈しない。
PySRの実装とoperator設定の参照論文はCranmerのPySR論文
（[`PySR_translated.md`](../docs/translated_paper/PySR_translated.md)）とする。

#### 3.3.1 文法制約と安全性

- decode中に`pow`を選んだ場合、指数childをliteral `2`–`5`へ制限する。候補filterだけで実装する場合も、
  parse後に同じ規則を再検査し、違反を`DisallowedPowerExponent`として保存する。
- `sin`、`cos`、`tan`、逆三角関数、双曲線関数、`sqrt`、`abs`、`exp`、`ln`、`log`は、
  GNW benchmark v1の真式に不要なため主実行から除外する。
- 除算候補は分母の最小絶対値、train / validation / ID / OOD点上の有限性、および事前固定した
  denominator marginを検査する。0除算、NaN、Inf、評価範囲内の特異点は理由付きfailureとする。
- NeSymReS、PySR、TPSRへ同じ意味上の探索空間を与え、表記上の違いによる候補数の差をmanifestへ記録する。
- 一般の実数べき乗を調べる場合は、主結果へ混ぜず、validationだけで設定を固定した別operator-ablationとする。

## 4. 層解析

### 4.1 probing

表現類似度にはKornblith et al., “Similarity of Neural Network Representations Revisited,” ICML 2019
（[`CKA_translated.md`](../docs/translated_paper/CKA_translated.md)）のCKAを用いる。単一層fine-tuningは
Zhang et al., “Is One Layer Enough?”, arXiv:2607.01232v2
（[`IOLE_translated.md`](../docs/translated_paper/IOLE_translated.md)）を直接参照し、本計画ではこの条件を
**IOLE条件** と呼ぶ。ただし同論文はLLMのreinforcement learning設定であるため、NeSymReSでは
「各候補層のうち1層だけをtrainableにし、他層を凍結してfull FTと比較する」という実験単位を移植する。
optimizer、学習率、学習budgetはNeSymReS用にvalidationで固定し、原論文の結果を再現したとは呼ばない。

validation上で次を実行し、高価なfine-tuningへ渡す候補層と選択規則をtest評価前に凍結する。

- 各層hidden stateに対するlinear probe
- validation NMSEまたはtoken cross entropyの小規模probe
- 固定validation problemに対する層ごとのgradient norm
- CKAなどによる層表現類似度
- 層ablationと固定したactivation介入
- parameter update感度

GPU_RUN1で`decoder_2`〜`decoder_4`が上位だったことは再現対象とし、GPU_RUN2のrankingを上書きする
固定結果としては使わない。

### 4.2 DecoderLens

参照論文はLangedijk et al., “DecoderLens: Layerwise Interpretation of Encoder-Decoder Transformers,”
arXiv:2310.03686v2（[`DecoderLens_translated.md`](../docs/translated_paper/DecoderLens_translated.md)）とする。
同論文の定義に従い、各encoder中間層の出力へ最終encoder normalizationを適用し、それをcross-attentionの
memoryとして**元のdecoder全体**へ渡す。追加学習は行わず、encoder層が最終生成に必要な情報をどの段階で
形成するかを観察する。最低限、problem・encoder layer・decode stepごとに次を保存する。

- top-k tokenと確率またはlogit
- ground-truth tokenの順位
- 当該encoder層をmemoryに用いて生成した暫定token列とparse可否
- 完成可能な場合のraw equationとsimplified equation
- 正しい式とのtoken、skeleton、symbolic equivalenceの差
- noise条件、seed、checkpoint、oracle変数対応

DecoderLensは原則として観察的解析であり、層の因果的役割はablationやactivation介入の結果と分けて解釈する。
中間encoder表現を、通常は最終encoder表現を受け取るdecoderへ入力することによる分布ずれを限界として明記する。
decoder中間層へ最終出力headを直接適用する解析を追加する場合は、DecoderLensとは呼ばず、decoder-side
logit-lens型の探索的解析として結果を分離する。

### 4.3 CTC_NSR：再現バイアスとtest-time computation

ここでCTC_NSRとは、Sato and Sato, “Can Test-time Computation Mitigate Reproduction Bias in Neural Symbolic
Regression?”, arXiv:2505.22081v2 (2026)を指す。ローカル資料は
[`docs/translated_paper/CTC_NSR_translated.md`](../docs/translated_paper/CTC_NSR_translated.md)、原文は
`docs/paper/CTC_NSR_paper.pdf`、公式実装は
[Shun-0922/Mem-Bias-NSR](https://github.com/Shun-0922/Mem-Bias-NSR)である。

同論文は、定数を除いた生成式の構造が学習template集合に含まれる場合を「再現」と定義し、
素朴なNSR生成が学習式をコピーする再現バイアスを持つこと、verified subtreeをtest-time promptとして反復利用する
NSR-gvsがそのバイアスを緩和し得ることを報告している。GPU_RUN2では、少数層fine-tuningがこの再現バイアスを
強めるか弱めるかを、数値精度およびsymbolic recoveryとは別の研究質問として調べる。

GPU_RUN2での再現判定は次のように行う。

1. 予測式とfine-tuning用GNW式を同じcanonical prefix treeへ変換する。
2. 連続定数を共通placeholderへ置換する。
3. commutative演算子の子を規定順へ並べ、同じrewrite規則を全条件へ適用する。
4. 予測templateがfine-tuning train template集合に含まれれば`reproduced=true`とする。
5. exact membership、定数除去後membership、symbolic equivalenceを別々に保存する。

ここで測れるのは**GPU_RUN2 fine-tuning corpusに対する再現率**である。NeSymReS 100Mの正確な事前学習template集合と
fingerprintを入手できない限り、事前学習corpus全体に対する再現率とは呼ばない。CTC_NSRの`not included`条件に
対応する解析には第3.2節のGNW structure-testだけを使い、主splitの係数違いtestを未見構造と呼ばない。

条件別に最低限次を報告する。

- reproduced rateとnovel rate
- reproduced / novel別のexact、skeleton、symbolic equivalence
- reproduced / novel別のID/OOD NMSEと$`R^2`$
- 正しい未見GNW構造を回復したnovel predictionの割合
- beam size、候補評価数、wall time、timeout率
- frozen、full、top、random間のpaired差

test-time strategyは、同じ候補評価数またはwall-time上限を併記して比較する。

- 標準beam search
- validationで事前固定したlarge beam
- Phase 6のGo条件を通ったTPSR
- NSR-gvs feasibility probe

NSR-gvsはsubtree promptを受け取るよう修正したモデルの追加学習と反復推論を必要とする。原論文は100 data points、
30反復、beam size 5を使い、A100上でも1式あたり約3–10分と報告している。したがってRTX 2070、基本60秒timeoutの
GPU_RUN2主比較へ同名の簡略版を混ぜない。まずvalidation 5 problems以下で、公式実装の固定commit、prompt model、
候補数、反復数、実時間を記録するfeasibility probeだけを行う。60秒budgetへ収まらない場合は負の実行可能性結果として
残し、全testへ拡張しない。部分木を単にrerankする独自手法をNSR-gvsと呼ばない。

## 5. symbolic recoveryの記録と比較

各problemの出力は集約値だけでなく、最低限次を含む1 recordとして保存する。

- `eq_id`、motif、split、noise、data seed、training seed、condition
- oracle変数名とモデル内変数名の対応
- 正しい式のraw表記、canonical表記、skeleton
- 予測式のraw表記、簡約後表記、canonical表記、skeleton
- beamまたは探索で得た候補式と順位
- exact、skeleton、symbolic equivalence
- ID/OOD NMSE、$`R^2`$、complexity、valid判定
- timeout、parse error、NaN、Inf、特異点などのfailure reason
- search時間、総process時間、候補評価数

レポートには、全problemについて少なくとも次の比較表を機械的に生成する。

| eq_id | condition | noise | 正しい式 | 予測式 | exact | skeleton | symbolic equivalent | ID NMSE | OOD NMSE | valid / failure |
|---|---|---:|---|---|---:|---:|---:|---:|---:|---|
| `G02_variant_001` | TBD | 0.0 | GNW single-activator式 | TBD | TBD | TBD | TBD | TBD | TBD | TBD |

成功例だけを抜粋せず、各条件の代表的な成功、近似的成功、構造誤り、decode失敗を併記する。
係数違いだけ、代数的に同値、不要項を含む、正しい変数だが演算子が違う、という失敗型を区別する。

## 6. timeoutとcheckpoint

### 6.1 timeout

GPU_RUN2の1 problemあたりの基本decode/search timeoutを**60秒**へ緩和する。

```text
LANSR_DECODE_TIMEOUT_SEC=60
```

- 同じ比較に含めるseed、condition、noiseでは同じ60秒を使う。
- search内部timeoutと親processのhard timeoutを区別し、親process側には終了処理用のgraceを加える。
- timeoutを空の成功結果として扱わず、`DecodeTimeout`として保存する。
- valid rateとfailure-penalized指標へ反映する。
- p50、p90、p95、最大時間、timeout率を条件別に保存する。
- 60秒で完了しないproblemだけを結果確認後に延長して主集計へ混ぜない。

60秒の動作確認として、validation subsetで30秒、60秒、120秒を測定してもよい。ただし主実行の60秒は
test結果を見て変更しない。変更が必要な場合は本実行前に計画を改訂する。

### 6.2 checkpoint / resume

最低保存単位は次とする。

- Phase 4: seed × layer × condition × noise
- Phase 5: seed × condition × noise × problem
- Phase 6: seed × method × noise × problem

各checkpointには完了problem ID、固有seed、elapsed、真式、raw/simplified予測式、候補式、metrics、
failure reason、timeout flag、候補評価数を保存する。resume時に完了problemを再計算しない。

## 7. Phase別実行案

### Phase 0: environment / preflight

- Python 3.10、source commit、checkpoint SHA256を固定する。
- RTX 2070、CUDA、64 GB RAM、CPU情報を確認する。
- Intel Core i7の正確な世代・型番はOSから取得し、manifestへ記録する。
- operator mask、60秒timeout、出力schema、checkpoint/resume、failure保存をsmokeで確認する。

### Phase 1: synthetic data

- 第3節のGNW式、module構成、variant設定を機械可読ファイルへ定義する。
- `noise=0.0`と`noise=0.1`をpaired生成する。
- oracle変数だけを入力へ含める。
- 主splitとCTC_NSR用structure-holdout viewをproblem単位で生成し、data fingerprintを保存する。
- 真式、canonical式、入力範囲、clean/noisy targetを保存し、有限差分を呼び出していないことをテストする。
- GNW source commitの式とgenerator出力が一致するgolden testを実行する。

### Phase 2: baseline

- NeSymReSはBiggio et al.のNSRS論文（[`NSRS_translated.md`](../docs/translated_paper/NSRS_translated.md)）、
  PySRはCranmerのPySR論文（[`PySR_translated.md`](../docs/translated_paper/PySR_translated.md)）を参照実装・手法の
  根拠として明記する。
- NeSymReS baselineとPySR baselineを同じproblem、seed、oracle変数、operator集合で実行する。
- 候補評価回数とwall timeを併記する。
- 成功式だけでなく全problem recordを保存する。

### Phase 3: probing / DecoderLens

- validationだけで軽量probingを実行する。
- DecoderLensでencoder layer・decode stepごとのtoken候補と暫定式を保存する。
- 高価なPhase 4へ渡す候補層と選択規則を凍結する。
- test problemを層選択や可視化対象の選別に使わない。
- fine-tuning train template集合のfingerprintとCTC_NSR再現判定規則を凍結する。

### Phase 4: contribution

- probeで残った候補層をpaired seedで比較する。
- IOLE条件（単一層fine-tuning）、層ablation、固定したactivation介入を比較する。
- probe順位、fine-tuning順位、ablation効果、介入効果の一致度をseed別に報告し、encoder層については
  DecoderLens上の変化との一致度も報告する。
- full FTがbaseを改善しない指標は正規化rankingへ混ぜず、raw scoreを保存する。

### Phase 5: selective fine-tuning / symbolic recovery

- top、random、middle、bottom、full、frozen baselineを公平に比較する。
- random層集合を事前に複数生成し、top対randomのpaired差を検証する。
- early stoppingと選択はvalidationだけで行い、testは条件固定後に一度だけ評価する。
- `noise=0.0`と`noise=0.1`を別々に集計する。
- 真式対予測式の全problem比較表を生成する。

### Phase 6: TPSR / CTC_NSR test-time computation

- TPSRはShojaee et al.のTPSR論文（[`TPSR_translated.md`](../docs/translated_paper/TPSR_translated.md)）、
  再現バイアスとNSR-gvsはSato and SatoのCTC_NSR論文
  （[`CTC_NSR_translated.md`](../docs/translated_paper/CTC_NSR_translated.md)）を参照する。
- TPSRはMCTS、BFGS、Transformer推論を個別にprofileする。
- NeSymReS beamとの候補評価回数またはwall timeを併記する。
- validation subsetで追加NMSE、symbolic recovery、valid rate、complexity、elapsedを確認し、
  費用対効果が低い場合は全規模実行を行わず副次的な結果として残す。
- standard beam、large beam、Go条件を通ったTPSRについて、structure-test上の再現率、novel recovery、
  候補評価数、wall timeを比較する。
- NSR-gvsは第4.3節のvalidation feasibility probeだけを行い、60秒budgetへ収まった場合に限り
  事前固定した小規模比較へ進める。

### Phase 7: validate / archive

- 必須ファイル、equation schema、failure reasonを検査する。
- config、commit、data checksum、checkpoint checksumを照合する。
- 真式対予測式の表、DecoderLens図、集約表を生成する。
- archiveとSHA256を作成する。

旧計画のDREAM4 Phase、human LODO Phase、有限差分評価は削除せず、GPU_RUN3以降の計画で再設計する。
GPU_RUN2のPhase番号をGPU_RUN1のPhase 7・8と対応するものとして解釈しない。

## 8. 計算資源と開発体制

### 8.1 実行環境

常時利用できる次のローカルPCをGPU_RUN2の実行環境とする。

- GPU: NVIDIA GeForce RTX 2070
- memory: 64 GB RAM
- CPU: Intel Core i7（世代・型番はpreflightで取得してmanifestへ記録）

Google ColabとColab Notebookは使用せず、compute unitsを前提とする設計もGPU_RUN2から外す。
Google Drive同期はバックアップと別端末からの閲覧のために使用してよい。ただし実行時の正本はローカルの
`results/runs/<run-id>/`とし、同期folder内のファイルを学習・decode・resumeから直接読み書きしない。
定期checkpointとローカルarchiveで中断へ備え、同期は第8.1.1節の規則に従う。
RTX 2070のVRAMに収まらない設定は暗黙に条件変更せず、batch size、gradient accumulation、precisionを
validation前に決めてmanifestへ記録する。

| 処理 | 実行場所 |
|---|---|
| NeSymReS fine-tuning / decode | ローカルRTX 2070 |
| probing / DecoderLens | ローカルRTX 2070 |
| TPSR | ローカルPC（GPU/CPU内訳をprofile） |
| PySR | ローカルPCのCPU |
| data生成・集計・図表・archive | ローカルPC |

#### 8.1.1 Google Drive同期

Google Driveは実験実行基盤ではなく、完了済み成果物の外部バックアップとして使う。

- 実行中のcheckpoint、JSON、CSVへ同期processが触れないよう、runは常にローカルで完結させる。
- checkpoint単位またはrun完了時にarchiveを一時名で作成し、生成完了後に確定名へrenameしてから同期対象へcopyする。
- 同期対象はmanifest、設定、problem単位結果、レポート、archive、SHA256とする。再生成可能な一時fileやcacheは除外する。
- data本体と大型checkpointを同期する場合は、容量、利用規約、共有範囲を事前確認し、repositoryへはcommitしない。
- upload後にローカルとGoogle Drive側のfile sizeおよびSHA256を照合し、`backup_status`、同期日時、保存先をmanifestへ記録する。
- Google Drive側の未同期・競合copyをresume元として自動選択しない。復元時はローカルへcopyし、checksum検証後に明示的に使う。
- 同期失敗はGPU実験自体の失敗とは分けて記録し、再試行してもローカル正本を上書きしない。

### 8.2 AIとコーディングの役割

- **Cursor**：実装、局所的な修正、テスト作成、短い反復を基本担当とする。
- **ChatGPT / チャッピー**：研究計画の整理、実験設計、結果の統合的レビュー、主張と限界の確認を基本担当とする。
- **その他のAI**：必要に応じて独立レビュー、統計、文献確認を担当する。担当内容と根拠を引き継ぎへ残す。

役割は責任範囲を明確にするための基本方針であり、生成物は担当AIにかかわらず現在のコード、テスト、保存済み結果で検証する。

## 9. 実装が必要な項目

- [ ] GNW synthetic benchmark v1の機械可読なmodule・式定義と生成器
- [ ] GNW source commitとの数式一致を検証するgolden test
- [ ] analytic targetとnoise 2条件のpaired生成
- [ ] oracle変数だけを渡す入力schema
- [ ] 有限差分コードを通らないことのテスト
- [ ] 主splitとCTC_NSR用structure-holdout viewの固定manifest
- [ ] 全手法共通operator allowlist
- [ ] NeSymReS decode token maskまたは候補filter
- [ ] PySR、TPSRへの同一operator制限
- [ ] 共通60秒decode/search timeout
- [ ] 全Phase共通problem timing schema
- [ ] problem単位checkpoint / resume
- [ ] 完了archiveのGoogle Drive同期とSHA256照合（同期を使用する場合）
- [ ] probing scriptと保存schema
- [ ] DecoderLensのencoder layer・decode step別出力と可視化
- [ ] 層別linear probe、表現類似度、ablation、activation介入の固定プロトコル
- [ ] probe・DecoderLens・fine-tuning・ablation・介入順位の一致度集計
- [ ] random層集合反復数と検出力の事前決定
- [ ] 真式対予測式の比較表を生成するreporter
- [ ] exact / skeleton / symbolic equivalenceの検証テスト
- [ ] ID/OOD安全性と除算分母marginの検査
- [ ] TPSR profilerとGo/No-Go
- [ ] CTC_NSR準拠のtemplate canonicalizationとcorpus fingerprint
- [ ] reproduced / novel別の性能集計
- [ ] NSR-gvs公式実装のcommit固定とRTX 2070 feasibility probe
- [ ] GPU_RUN2用run ID、source commit、環境manifestの固定

## 10. Go / No-Go条件

本実行開始条件:

- GNW由来の全真式、module構成、canonical式が出典実装と照合済みである。
- `noise=0.0`と`noise=0.1`の生成、paired入力、data fingerprintが確認済みである。
- oracle以外の変数がモデル入力へ入らない。
- 有限差分処理がGPU_RUN2 pipelineから呼ばれない。
- operator set、60秒timeout、seed、random集合、budgetが固定済みである。
- 主splitとstructure-holdout viewが固定され、template集合のfingerprintが保存される。
- validationだけで層候補とhyperparameterを選択できる。
- RTX 2070でsmokeが成功し、OOM時にfail fastする。
- problem record、真式、予測式、failure、checkpoint/resumeが保存される。

本実行を開始しない条件:

- testを見て層、timeout、operator、係数variantを変更した。
- methodごとに説明のない異なるbudgetがある。
- timeout、parse error、NaN、Infが保存されない。
- run途中でsource commitまたはデータ仕様を変更する必要がある。
- 完了problemをresume時に再計算する。
- DREAM4、ヒトデータ、有限差分結果をGPU_RUN2主集計へ混ぜる。
- empirical selectorの結果をoracle条件と混ぜる。

## 11. GPU_RUN2で残す成果物

- run manifest、source lock、environment versions
- data、checkpoint、archiveのSHA256
- GNW synthetic benchmark仕様、module構成、全真式、canonical式、split、data fingerprint
- noise 2条件のpaired dataと設定
- probing結果
- DecoderLensのencoder layer・decode step別token候補、暫定式、図表
- 層別の表現類似度、ablation、activation介入結果
- 層順位のseed・motif・noise間安定性
- operator allowlist
- problem timingとtimeout分布
- 全problemの真式、raw予測式、簡約式、canonical式、候補式
- 真式対予測式の一覧表
- failure reasons、failure-penalized metrics、valid rate
- exact、skeleton、symbolic equivalence、complexity
- ID/OOD NMSE、$`R^2`$、特異点、分母margin、OOD validity
- paired seed比較とnoise別集計
- CTC_NSR準拠のfine-tuning-corpus reproduced / novel集計
- structure-testにおけるnovel symbolic recoveryとtest-time strategy比較
- PySR結果、Go条件を通った場合のTPSR結果
- CTC_NSR原典、公式実装commit、再現判定規則、NSR-gvs feasibility結果
- validation report、figures、tables、archive
- Google Drive同期を使用した場合の`backup_status`、同期日時、保存先、SHA256照合結果

独立した図表は`graphs/<run-id>/figures/`と`graphs/<run-id>/tables/`へ保存する。
