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
- TPSR、NSR-gvs、large beam、その他のtest-time computation比較

したがって、GPU_RUN2の主張は「既知の真式を持つ合成データ上での層解析とsymbolic recovery」に限定する。
DREAM4やヒトデータへの転移性能、有限差分誤差への頑健性、regulator selection性能はGPU_RUN2の結果から主張しない。

GPU_RUN1の確定結果と限界は
[`results/GPU_RUN1_report.md`](../results/GPU_RUN1_report.md)を参照する。

### 1.1 GPU_RUN1からの出発点

| 観測 | GPU_RUN2での扱い |
|---|---|
| `decoder_2`〜`decoder_4`の寄与が高かった | 独立runのprobe、fine-tuning、ablationで再確認し、testを見る前に候補を固定する |
| Top 1〜3は全層FTとNMSE同等性margin内で同等だった | 独立runで再現性、symbolic recovery、計算資源削減を確認する |
| Top 3対random 3の差は未確定だった | 事前生成した1個のrandom 3層集合とpaired比較する |
| symbolic recoveryは全条件で0だった | 真式対予測式の比較を主成果物にし、失敗理由まで保存する |
| TPSRの追加改善に大きな計算時間を要した | 層解析へ直接必要でないため、NSR-gvsとともにGPU_RUN3以降へ回す |
| DREAM4の経験的selector F1が低かった | GPU_RUN2では変数選択問題を切り離し、oracle変数だけを入力する |
| `tan`と危険な除算を含む式が多かった | 合成データの真式と整合するoperator allowlist、安全性検査を使う |

### 1.2 事前に固定する主判定

1. **層の役割と再現性**：probe、単一層fine-tuning、ablation、表現類似度、activation介入が示す
   重要層と機能を比較し、encoder層ではDecoderLensの結果も照合する。相関的な結果と介入結果を区別する。
2. **全層同等性**：Top 1〜3と全層FTのfailure-penalized NMSE差について、95% Studentのt区間全体が
   事前margin `[-0.05, 0.05]`へ入るかを判定する。
3. **rankingの付加価値**：Top 3条件と事前生成したrandom 3層条件のpaired NMSE差を報告する。
   95% t区間が0をまたぐ場合、優越性または同等性を主張しない。
4. **構造回復**：exact、skeleton、symbolic equivalence、complexityを条件別に報告する。
   NMSEが小さくても構造回復が失敗した場合は、数式回復成功と判定しない。
5. **noise頑健性**：`noise=0.0`と`noise=0.1`を独立条件として比較し、結果を混ぜて集計しない。

seed数、random層集合、学習budget、decode budgetはvalidation pilot後かつtest評価前に固定する。

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
| 再現バイアス評価 | Sato and Sato, “Can Test-time Computation Mitigate Reproduction Bias in Neural Symbolic Regression?”, arXiv:2505.22081v2（[`CTC_NSR_translated.md`](../docs/translated_paper/CTC_NSR_translated.md)） | template再現率とincluded / not-included相当の評価定義だけを参照する。TPSRとNSR-gvsの実行はGPU_RUN3以降 |

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
NeSymReSとPySRへ直接与える実験条件を指す。対象遺伝子を$`i`$、真式を$`f_i`$とすると、
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
主性能指標にしない。代わりにexact、skeleton、symbolic equivalence、domain-ID / domain-OOD NMSE、
complexity、valid rateを
主に報告する。oracle metadataはtest problemにも使用するが、これは事前宣言した実験条件であり、
層選択、hyperparameter選択、early stoppingにtestの予測結果を使うこととは区別する。

## 3. 合成データ仕様

### 3.1 観測値の作り方

GPU_RUN2では、ODE軌道から有限差分を計算しない。各problemについてoracle変数の入力点
$`\mathbf{x}`$を生成し、既知の真式$`f(\mathbf{x})`$を直接評価して教師値$`y`$を作る。

評価用の真式（`canonical_expr`）と、NeSymReS fine-tuning用の教師式（`teacher_expr`）は分離する。
`teacher_expr`は`canonical_expr`と代数的に同値だが、NeSymReSのprefixが短くなる形にする。
具体的にはKnを融合したHill項と、G07/G08では入れ子の多重線形形
$`(A_0+A_1 m_1)+m_2(A_2+A_3 m_1)-\delta x_1`$を使う（`cancel`後の有理式や素の因数分解形ではない）。
単純な「因数分解したcanonical」や`cancel`前の生Hillをそのまま`str`すると、SymPy経由のtoken化で
かえって長くなり`length_eq=60`を超える。真式と教師式はSymPy上で同値であることをテストし、
Phase 1で全problemのtoken長をfail-fast検査する。評価指標・真式対予測式の比較は常に
`canonical_expr`を用いる。

```math
y=f(\mathbf{x})+\epsilon
```

- 各入力変数の範囲は`[0.1, 2.0]`とする。
- data seedは`101`、`202`、`303`の3個、model training seedは`0`、`1`、`2`の3個とする。
- 各problem・各data seedについて、学習用1,024点、独立したdomain-ID評価用256点、
  domain-OOD評価用256点を
  Latin hypercube samplingで生成する。
- `noise=0.0`では$`\epsilon=0`$とする。
- `noise=0.1`では、clean targetの学習用1,024点における標準偏差を$`s_y`$として、
  $`\epsilon\sim\mathcal{N}(0,(0.1s_y)^2)`$とする。
- 入力点とnoiseのseedをmanifestへ保存する。
- 同一のclean入力点を`noise=0.0`と`noise=0.1`で共有し、noiseだけを変えるpaired設計にする。
- train、validation、testはproblem ID単位で分離する。行を混ぜてproblemの分割を作らない。
- domain-ID評価点は`[0.1, 2.0]`、domain-OOD評価点は`[0.05, 2.5]`から生成し、学習点とは共有しない。

#### 3.1.1 domain OODとstructure OODの名称

GPU_RUN2では、入力値域の外挿と未見数式構造への一般化を混同しないよう、次の2軸を独立に記録する。

- **domain-ID**：学習入力と同じ値域`[0.1, 2.0]`にある独立評価点。
- **domain-OOD**：同じ式構造・同じparameter variantを保ったまま、入力値域だけを`[0.05, 2.5]`へ広げた評価点。
- **structure-ID**：fine-tuning時に出現したGNW familyに属する式。主splitのtestはparameter variantが未見でも
  familyは既知なのでstructure-IDとする。
- **structure-OOD**：fine-tuning時に出現しないGNW familyに属する式。第3.2節の`G07`–`G08`だけを指す。

各評価recordには`domain_regime={id,ood}`、`structure_regime={id,ood}`、`parameter_split`を別fieldで保存する。
したがってstructure-OOD problemにもdomain-ID点とdomain-OOD点の両方が存在する。表と本文では裸の「OOD」や
`ood_nmse`を使用せず、`domain_ood_nmse`、`structure_ood`、または
`structure-OOD / domain-OOD`のように対象軸を必ず明記する。

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

単一regulatorで$`\alpha_0=0,\alpha_1=1`$または$`\alpha_0=1,\alpha_1=0`$とした特殊ケースには、
上式から次の標準的なHill活性化・抑制を得る。

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

| family ID | algebraic template ID | GNW由来の構造 | oracle入力 | module構成 |
|---|---|---|---|---|
| `G01` | `T01_basal` | 入力なし | $`x_1`$ | basal transcriptionとmRNA分解 |
| `G02` | `T02_single_regulator` | 単一activator | $`x_1,x_2`$ | enhancer module 1個 |
| `G03` | `T02_single_regulator` | 単一repressor | $`x_1,x_2`$ | repressor module 1個 |
| `G04` | `T04_two_independent_activators` | 2 activators、独立結合 | $`x_1,x_2,x_3`$ | enhancer module 1個、`bindsAsComplex=false` |
| `G05` | `T05_two_complex_activators` | 2 activators、複合体結合 | $`x_1,x_2,x_3`$ | enhancer module 1個、`bindsAsComplex=true` |
| `G06` | `T06_activator_deactivator` | activator＋deactivator | $`x_1,x_2,x_3`$ | enhancer module 1個、独立結合 |
| `G07` | `T07_two_module_mixture` | enhancer＋repressor | $`x_1,x_2,x_3`$ | 独立なmodule 2個 |
| `G08` | `T07_two_module_mixture` | 2 enhancer modules | $`x_1,x_2,x_3`$ | 独立なenhancer module 2個 |

#### 3.2.1 G01–G08のtemplate式

各familyの正解templateを次のように固定する。これは新しい制御式を考案したものではなく、上記GNWのmodule活性と
状態混合を、G01–G08のmodule構成へ代入した式である。まずregulator $`r\in\{2,3\}`$について次を定義する。

```math
q_r=\left(\frac{x_r}{K_r}\right)^{n_r},
\qquad
h_r=\frac{q_r}{1+q_r}
```

単一moduleのinactive / active状態を混合する関数を$`A`$、2 moduleの4状態を混合する関数を$`B`$とする。

```math
A(m;\alpha_0,\alpha_1)
=\alpha_0(1-m)+\alpha_1m
```

```math
\begin{aligned}
B(m_1,m_2;\alpha_{00},\alpha_{10},\alpha_{01},\alpha_{11})
={}&\alpha_{00}(1-m_1)(1-m_2)
+\alpha_{10}m_1(1-m_2)\\
&+\alpha_{01}(1-m_1)m_2
+\alpha_{11}m_1m_2 .
\end{aligned}
```

この記法を用いた8 familyのtemplateは次である。

```math
\begin{aligned}
G01:\quad f_1(x_1)
&=V-\delta x_1,\\[2mm]
G02:\quad f_1(x_1,x_2)
&=V A(h_2;\alpha_0,\alpha_1)-\delta x_1,
\qquad \alpha_1>\alpha_0,\\[2mm]
G03:\quad f_1(x_1,x_2)
&=V A(h_2;\alpha_0,\alpha_1)-\delta x_1,
\qquad \alpha_1<\alpha_0,\\[2mm]
G04:\quad f_1(x_1,x_2,x_3)
&=V A\!\left(
\frac{q_2q_3}{(1+q_2)(1+q_3)};
\alpha_0,\alpha_1\right)-\delta x_1,
\qquad \alpha_1>\alpha_0,\\[2mm]
G05:\quad f_1(x_1,x_2,x_3)
&=V A\!\left(
\frac{q_2q_3}{1+q_2q_3};
\alpha_0,\alpha_1\right)-\delta x_1,
\qquad \alpha_1>\alpha_0,\\[2mm]
G06:\quad f_1(x_1,x_2,x_3)
&=V A\!\left(
\frac{q_2}{(1+q_2)(1+q_3)};
\alpha_0,\alpha_1\right)-\delta x_1,
\qquad \alpha_1>\alpha_0,\\[2mm]
G07:\quad f_1(x_1,x_2,x_3)
&=V B(h_2,h_3;
\alpha_{00},\alpha_{10},\alpha_{01},\alpha_{11})-\delta x_1,\\[2mm]
G08:\quad f_1(x_1,x_2,x_3)
&=V B(h_2,h_3;
\alpha_{00},\alpha_{10},\alpha_{01},\alpha_{11})-\delta x_1.
\end{aligned}
```

G06では$`x_2`$をenhancer moduleのactivator、$`x_3`$を同じmoduleのdeactivatorとする。
G07では第1 moduleを$`x_2`$のenhancer、第2 moduleを$`x_3`$のrepressorとし、GNW初期化により
$`\alpha_{10}>\alpha_{00}`$、$`\alpha_{01}<\alpha_{00}`$となる向きを持たせる。G08では両moduleをenhancerとし、
$`\alpha_{10}>\alpha_{00}`$、$`\alpha_{01}>\alpha_{00}`$となる向きを持たせる。$`\alpha_{11}`$を含む全状態係数は、
GNWのmodule効果の加算と`[0,1]`へのtruncateに従って生成し、独立な自由係数として無制約にsamplingしない。

G07とG08は同じ4状態混合の代数templateを持つが、moduleの符号と$`\alpha`$の制約が異なるため別familyとする。
G02とG03も同じ単一regulatorの $`A(h_2)`$ templateを共有し、係数の向きだけが異なる。
manifestの `template_id` はこの代数templateであり、`family_id` と同一ではない。
G02/G03は `T02_single_regulator`、G07/G08は `T07_two_module_mixture` を共有する。
各problem manifestには上記template IDだけでなく、$`q_r`、$`A`、$`B`$を展開したraw真式、
全定数を代入した式、canonical SymPy式をすべて保存する。

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
- structure-test（structure-OOD、`not included`相当）: `G07`–`G08`

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
| NeSymReS token列 | `add`、`sub`、`mul`、`div`、および指数childがliteral `2`–`5`の`pow` |
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
- 除算候補は分母の最小絶対値、train / validation / domain-ID / domain-OOD点上の有限性、および事前固定した
  denominator marginを検査する。0除算、NaN、Inf、評価範囲内の特異点は理由付きfailureとする。
- NeSymReSとPySRへ同じ意味上の探索空間を与え、表記上の違いによる候補数の差をmanifestへ記録する。
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

- 各層hidden stateに対するlinear probe。目的変数は algebraic template ID（分類）、
  teacher-forcingの次token（分類）、演算子数（回帰）に限定する。
  入力点の平均など、数式構造と無関係なスカラーは層選択に使わない。
- 候補層凍結は上記probeのmean rankによる。因果的な層寄与の主判定はPhase 4の
  IOLE / ablation / activation介入に残す。
- 固定validation problemに対する層ごとのgradient norm
- CKAなどによる層表現類似度
- 層ablationと固定したactivation介入
- parameter update感度

selective-FTの候補はencoder / decoder blockだけとする。`output_head`（`fc_out`）は
別controlであり、top 3 / random 3の層集合に混ぜない。

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

### 4.3 CTC_NSR：再現バイアス評価

ここでCTC_NSRとは、Sato and Sato, “Can Test-time Computation Mitigate Reproduction Bias in Neural Symbolic
Regression?”, arXiv:2505.22081v2 (2026)を指す。ローカル資料は
[`docs/translated_paper/CTC_NSR_translated.md`](../docs/translated_paper/CTC_NSR_translated.md)、原文は
`docs/paper/CTC_NSR_paper.pdf`、公式実装は
[Shun-0922/Mem-Bias-NSR](https://github.com/Shun-0922/Mem-Bias-NSR)である。

同論文は、定数を除いた生成式の構造が学習template集合に含まれる場合を「再現」と定義し、
素朴なNSR生成が学習式をコピーする再現バイアスを持つことを報告している。GPU_RUN2では同論文の評価定義だけを使い、
少数層fine-tuningがこの再現バイアスを強めるか弱めるかを、数値精度およびsymbolic recoveryとは別に調べる。

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
- reproduced / novel別のdomain-ID / domain-OOD NMSEと$`R^2`$
- 正しい未見GNW構造を回復したnovel predictionの割合
- 標準beamのbeam size、候補評価数、wall time、timeout率
- frozen、full、top、random間のpaired差

GPU_RUN2では全条件に同じ標準beam searchだけを使う。large beam、TPSR、NSR-gvs、MCTS、subtree prompt、
反復推論などのtest-time computation比較は層解析の主質問から外れるため、GPU_RUN3以降へ保留する。
したがってGPU_RUN2の再現バイアス結果は、test-time探索法の優劣ではなくfine-tuning条件間の差として解釈する。

## 5. symbolic recoveryの記録と比較

各problemの出力は集約値だけでなく、最低限次を含む1 recordとして保存する。

- `eq_id`、motif、split、noise、data seed、training seed、condition
- oracle変数名とモデル内変数名の対応
- 正しい式のraw表記、canonical表記、skeleton
- 予測式のraw表記、簡約後表記、canonical表記、skeleton
- beamまたは探索で得た候補式と順位
- exact、skeleton、symbolic equivalence
- domain-ID / domain-OOD NMSE、$`R^2`$、complexity、valid判定
- timeout、parse error、NaN、Inf、特異点などのfailure reason
- search時間、総process時間、候補評価数

レポートには、全problemについて少なくとも次の比較表を機械的に生成する。

| eq_id | condition | noise | structure regime | 正しい式 | 予測式 | exact | skeleton | symbolic equivalent | domain-ID NMSE | domain-OOD NMSE | valid / failure |
|---|---|---:|---|---|---|---:|---:|---:|---:|---:|---|
| `G02_variant_001` | TBD | 0.0 | structure-ID | GNW single-activator式 | TBD | TBD | TBD | TBD | TBD | TBD | TBD |

成功例だけを抜粋せず、各条件の代表的な成功、近似的成功、構造誤り、decode失敗を併記する。
係数違いだけ、代数的に同値、不要項を含む、正しい変数だが演算子が違う、という失敗型を区別する。

## 6. timeoutとcheckpoint

### 6.1 timeout

GPU_RUN2の1 problemあたりの基本decode/search timeoutを**30秒**とする。

```text
LANSR_DECODE_TIMEOUT_SEC=30
```

- 同じ比較に含めるseed、condition、noiseでは同じ30秒を使う。
- search内部timeoutと親processのhard timeoutを区別し、親process側には終了処理用のgraceを加える。
- timeoutを空の成功結果として扱わず、`DecodeTimeout`として保存する。
- valid rateとfailure-penalized指標へ反映する。
- p50、p90、p95、最大時間、timeout率を条件別に保存する。
- 30秒で完了しないproblemだけを結果確認後に延長して主集計へ混ぜない。

30秒の動作確認として、validation subsetで15秒、30秒、60秒を測定してもよい。ただし主実行の30秒は
test結果を見て変更しない。変更が必要な場合は本実行前に計画を改訂する。

### 6.2 checkpoint / resume

最低保存単位は次とする。

- Phase 4: seed × layer × condition × noise
- Phase 5: seed × condition × noise × problem

各checkpointには完了problem ID、固有seed、elapsed、真式、raw/simplified予測式、候補式、metrics、
failure reason、timeout flag、候補評価数を保存する。resume時に完了problemを再計算しない。

## 7. Phase別実行案

### Phase 0: environment / preflight

- Python 3.10、source commit、checkpoint SHA256を固定する。
- RTX 2070、CUDA、64 GB RAM、CPU情報を確認する。
- Intel Core i7の正確な世代・型番はOSから取得し、manifestへ記録する。
- operator mask、30秒timeout、出力schema、checkpoint/resume、failure保存をsmokeで確認する。

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
- 高価なPhase 4へ渡す候補層をview別に凍結する。
  `candidate_layers_main.json`はmain validation（G01–G08）から、
  `candidate_layers_structure_holdout.json`はG07/G08を一切使わないvalidation部分集合（G01–G06）から選ぶ。
- test problemを層選択や可視化対象の選別に使わない。
- fine-tuning train template集合のfingerprintとCTC_NSR再現判定規則を凍結する。

### Phase 4: contribution

- G01–G08の各familyについて、主splitのvalidation variantを`eq_id`のvariant番号で昇順に並べ、
  最小の2件を選ぶ。計16 problemsの固定パネルを、予測値や難易度を確認する前にmanifestへ保存する。
- probeで残った候補5層を、この16 problemsとpaired seedで比較する。
- IOLE条件（単一層fine-tuning）、層ablation、固定したactivation介入を比較する。
- probe順位、fine-tuning順位、ablation効果、介入効果の一致度をseed別に報告し、encoder層については
  DecoderLens上の変化との一致度も報告する。
- full FTがbaseを改善しない指標は正規化rankingへ混ぜず、raw scoreを保存する。
- structure-OOD用の層・設定固定では、この16件のうちG01–G06の12件だけを集計し、G07–G08の結果を参照しない。
  全familyを用いる主解析と、structure-OOD用のleakage-free解析を別名・別manifestで保存する。

### Phase 5: selective fine-tuning / symbolic recovery / reproduction-bias analysis

- 比較条件を`frozen`、`full`、`top 1`、`top 3`、`random 3`の5条件へ限定する。
- `random 3`は`top 3`とtrainable層数をそろえる。全候補層から3層を重複なしで固定seedにより1回だけ抽出し、
  `top 3`と完全一致した場合だけ再抽出する。抽出規則と結果をvalidation評価前にmanifestへ固定する。
- random集合が1個だけなので、random層集合全体に対する平均性能や一般的優越性は主張せず、固定controlとの比較と呼ぶ。
- early stoppingと選択はvalidationだけで行い、testは条件固定後に一度だけ評価する。
- validationでFTしたモデル重みをcheckpoint保存し、testでは再学習せずそのcheckpointを読み込んでdecodeする。
  `hp_selected_<view>.json`が無いtest呼び出しはfail-fastする。
- `noise=0.0`と`noise=0.1`を別々に集計する。
- 真式対予測式の全problem比較表を生成する。
- CTC_NSR評価用には、同じ5条件をstructure-trainだけで学習し、G06でearly stoppingした別checkpointを作る。
  条件固定後にG07–G08の60 structure-OOD problemsを標準beamで一度だけdecodeする。
- Sato and SatoのCTC_NSR論文（[`CTC_NSR_translated.md`](../docs/translated_paper/CTC_NSR_translated.md)）から、
  template再現率とincluded / not-included相当の評価定義だけを参照する。
- Phase 5の保存済み標準beam予測式から、追加decodeなしでreproduced / novelを集計する。
- 主splitとstructure-OODを分け、5条件の再現率、novel recovery、数値精度をpaired比較する。
- TPSR、NSR-gvs、large beam、その他のtest-time computation比較はGPU_RUN3以降へ保留する。

### run完了処理

以下は独立した実験Phaseとせず、Phase 0–5の全必須処理が完了した後に共通処理として1回実行する。

- 必須ファイル、equation schema、failure reasonを検査する。
- config、commit、data checksum、checkpoint checksumを照合する。
- 真式対予測式の表、DecoderLens図、集約表を生成する。
- archiveとSHA256を作成する。

### Phaseごとの予定decode数と概算計算量

資源見積もりでは、data seedとmodel/search seedを`(101,0)`、`(202,1)`、`(303,2)`の3組として対応させる。
1条件・1splitあたりの基本単位は`48 problems × 3 seed bundles × 2 noise = 288 decodes`である。
Phase 3のencoder層数はcheckpoint設定どおり5とする。Phase 4はG01–G08から機械的に2件ずつ選んだ16 problems、
候補層5、IOLE・ablation・activation介入の3解析を使う。Phase 5は`frozen`、`full`、`top 1`、`top 3`、
`random 3`の5条件とする。候補層数とrandom 3の実体はvalidation pilot後かつtest前に凍結する。

| Phase | decode数の算出 | 予定decode / search数 | 追加学習run | 30秒timeoutを全件使った直列上限 | 主なdevice・備考 |
|---|---|---:|---:|---:|---|
| 0: preflight | smoke最大10件 | 最大10 | 0 | 0.08時間 | RTX 2070 / CPU。機能確認だけ |
| 1: synthetic data | 数式を解析評価するためdecodeなし | 0 | 0 | 0時間 | CPU。240 problemsと評価点を生成 |
| 2: baseline | 48 × 2 splits × 3 bundles × 2 noise × 2 methods | 1,152 | 0 | 9.6時間 | NeSymReSはGPU、PySRはCPU |
| 3: probing / DecoderLens | 48 validation × 3 bundles × 2 noise × 5 encoder layers | 1,440 | 0 | 12.0時間 | RTX 2070。通常forwardだけのprobeはdecode数に含めない |
| 4: contribution | 16 fixed validation × 3 bundles × 2 noise × 5 candidate layers × 3 analyses | 1,440 | 最大30 | 12.0時間 | RTX 2070。各G01–G08からvariant番号最小の2件 |
| 5: selective FT / symbolic recovery / reproduction bias | 主split: 48 × 2 splits × 3 bundles × 2 noise × 5 conditions、structure-OOD: 60 × 3 × 2 × 5 | 4,680 | 最大48 | 39.0時間 | RTX 2070。mainとstructure-holdoutは別checkpoint。再現バイアス集計自体は追加decodeなし |
| **合計** | Phase 0–5 | **最大8,722** | **最大78** | **72.7時間** | 学習時間、run完了処理、batch化による短縮、CPU/GPU並行実行は直列上限に含めない |

30秒から得た時間は予想実時間ではなく、安全側のsearch/decode上限である。追加学習時間はRTX 2070 smokeから
IOLE、少数層、full FTを別々に実測し、`学習run数 × 条件別中央値`として本実行前に追記する。
seedを3組ではなくdata seedとmodel seedの全直積9通りに変更する場合、上表のseed依存decode数と学習run数は
原則3倍になるため、計画改訂なしに変更しない。Phase間でcheckpointやdecode結果を再利用する場合は、source、data、
operator、seed、noise、budgetのfingerprintが完全一致した場合だけ重複計算を省く。

旧計画のDREAM4 Phase、human LODO Phase、有限差分評価は削除せず、GPU_RUN3以降の計画で再設計する。
GPU_RUN2のPhase 0–5をGPU_RUN1の同番号Phaseと対応するものとして解釈しない。

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

- [x] GNW synthetic benchmark v1の機械可読なmodule・式定義と生成器
- [x] GNW source commitとの数式一致を検証するgolden test
- [x] analytic targetとnoise 2条件のpaired生成
- [x] oracle変数だけを渡す入力schema
- [x] 有限差分コードを通らないことのテスト
- [x] 主splitとCTC_NSR用structure-holdout viewの固定manifest
- [x] 全手法共通operator allowlist
- [x] NeSymReS decode token maskまたは候補filter
- [x] PySRへの同一operator制限
- [x] 共通30秒decode/search timeout
- [x] 全Phase共通problem timing schema
- [x] problem単位checkpoint / resume
- [x] 完了archiveのGoogle Drive同期とSHA256照合（同期を使用する場合）
- [x] probing scriptと保存schema
- [x] DecoderLensのencoder layer・decode step別出力と可視化
- [x] 層別linear probe、表現類似度、ablation、activation介入の固定プロトコル
- [x] probe・DecoderLens・fine-tuning・ablation・介入順位の一致度集計
- [x] random 3層集合1個の固定seed、抽出規則、限界の事前記録
- [x] 真式対予測式の比較表を生成するreporter
- [x] exact / skeleton / symbolic equivalenceの検証テスト
- [x] domain-ID / domain-OOD安全性と除算分母marginの検査
- [x] CTC_NSR準拠のtemplate canonicalizationとcorpus fingerprint
- [x] reproduced / novel別の性能集計
- [x] GPU_RUN2用run ID、source commit、環境manifestの固定

## 10. Go / No-Go条件

本実行開始条件:

- GNW由来の全真式、module構成、canonical式が出典実装と照合済みである。
- `noise=0.0`と`noise=0.1`の生成、paired入力、data fingerprintが確認済みである。
- oracle以外の変数がモデル入力へ入らない。
- 有限差分処理がGPU_RUN2 pipelineから呼ばれない。
- operator set、30秒timeout、seed、random 3層集合、budgetが固定済みである。
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
- domain-ID / domain-OOD NMSE、$`R^2`$、特異点、分母margin、domain-OOD validity
- paired seed比較とnoise別集計
- CTC_NSR準拠のfine-tuning-corpus reproduced / novel集計
- structure-OODにおけるnovel symbolic recoveryとfine-tuning条件比較
- PySR結果
- CTC_NSR原典、fine-tuning corpus fingerprint、再現判定規則
- validation report、figures、tables、archive
- Google Drive同期を使用した場合の`backup_status`、同期日時、保存先、SHA256照合結果

独立した図表は`graphs/<run-id>/figures/`と`graphs/<run-id>/tables/`へ保存する。

## 12. 既存・新規ファイルの配置計画

実装時は共通機能を`src/`、Phase入口を`scripts/phases/`、運用処理を`scripts/ops/`、設定を`configs/`、
GPU_RUN2固有テストを`GPU_RUN2/tests/`へ置く。次表の「新規」は予定であり、この計画書更新時点では未作成である。

| パス | 状態 | 用途 |
|---|---|---|
| `GPU_RUN2/plan.md` | 既存・更新 | 本計画の正本 |
| `GPU_RUN2/README.md` | 既存・更新予定 | 実行順、run ID、主要入口への案内。Colab前提の記述をローカルPC用へ直す |
| `GPU_RUN2/notebooks/` | 既存 | 任意の結果閲覧用。実験実行の必須入口にはしない。実file追加時は不要な`.gitkeep`を削除する |
| `GPU_RUN2/tests/README.md` | 既存・更新予定 | GPU_RUN2固有テストの範囲と実行方法 |
| `GPU_RUN2/tests/test_gnw_synthetic.py` | 新規 | GNW式、240 problems、noise、domain範囲のgolden test |
| `GPU_RUN2/tests/test_oracle_and_splits.py` | 新規 | oracle入力、主split、structure-OOD split、seed bundleの検査 |
| `GPU_RUN2/tests/test_operator_policy.py` | 新規 | 制限付き`pow`、除算安全性、手法間operator対応の検査 |
| `GPU_RUN2/tests/test_records_and_resume.py` | 新規 | equation record、2軸OOD field、failure、checkpoint / resumeの検査 |
| `configs/gpu_run2/base.yaml` | 新規 | seed、noise、timeout、budget、checkpoint、出力先の共通設定 |
| `configs/gpu_run2/operators.yaml` | 新規 | semantic allowlistとNeSymReS / PySRのoperator mapping |
| `configs/gpu_run2/splits.yaml` | 新規 | 主split、structure-holdout、domain-ID / domain-OOD範囲 |
| `src/data/synthetic_grn.py` | 既存・再利用 | samplingとnoise処理。legacy挙動を壊さず共通処理だけを再利用する |
| `src/data/gnw_synthetic.py` | 新規 | G01–G08、GNW parameter生成、canonical真式、oracle metadata |
| `src/data/splits.py` | 既存・拡張 | problem単位splitとstructure-holdout view |
| `src/evaluation/equation_metrics.py` | 既存・拡張 | exact、skeleton、symbolic equivalence、domain別数値指標 |
| `src/evaluation/equation_records.py` | 既存・拡張 | 真式・予測式、`domain_regime`、`structure_regime`、failure schema |
| `src/evaluation/decode_timeout.py` | 既存・再利用 | 共通30秒timeoutとfailure記録 |
| `src/evaluation/layer_contribution.py` | 既存・拡張 | probe、IOLE、ablation、介入の層別集計 |
| `src/evaluation/reproduction_bias.py` | 新規 | CTC_NSR準拠template canonicalizationとreproduced / novel集計 |
| `src/interpretability/__init__.py` | 新規 | 層解釈moduleの公開入口 |
| `src/interpretability/decoder_lens.py` | 新規 | encoder中間表現を元のdecoderへ渡すDecoderLens |
| `src/models/nesymres_adapter.py` | 既存・拡張 | operator制約、層hook、共通decode出力 |
| `src/baselines/pysr_runner.py` | 既存・拡張 | PySR operator制約、search budget、候補式保存 |
| `src/training/single_layer.py` | 既存・拡張 | IOLE条件の単一層freeze / train制御 |
| `src/training/selective_layers.py` | 既存・拡張 | top 1、top 3、random 3条件の学習制御 |
| `src/resumable_evaluation.py` | 既存・拡張 | problem単位checkpoint、fingerprint検証、resume |
| `scripts/phases/gpu_run2_phase0_preflight.py` | 新規 | ローカルRTX 2070のpreflightとsmoke |
| `scripts/phases/gpu_run2_phase1_data.py` | 新規 | GNW synthetic benchmark生成 |
| `scripts/phases/gpu_run2_phase2_baseline.py` | 新規 | NeSymReS / PySR baseline |
| `scripts/phases/gpu_run2_phase3_interpret.py` | 新規 | probing、CKA、DecoderLens |
| `scripts/phases/gpu_run2_phase4_contribution.py` | 新規 | IOLE、ablation、activation介入 |
| `scripts/phases/gpu_run2_phase5_selective_ft.py` | 新規 | selective FT、symbolic recovery、CTC_NSR準拠の再現バイアス集計 |
| `scripts/ops/finalize_gpu_run2.py` | 新規 | Phase 0–5完了後のschema検査、集計、真式対予測式表、archive |
| `scripts/ops/run_gpu_run2.ps1` | 新規 | WindowsローカルPCでのPhase順次実行と停止・再開 |
| `scripts/ops/backup_gpu_run2.py` | 新規 | 完了archiveのGoogle Drive同期用stagingとSHA256照合 |
| `results/runs/<run-id>/` | 実行時生成・Git管理外 | manifest、problem records、checkpoint、logs、archive |
| `graphs/<run-id>/figures/` | 実行時生成 | DecoderLens、層解析、性能図 |
| `graphs/<run-id>/tables/` | 実行時生成 | 真式対予測式、集約値、計算量、failure表 |

同名機能が既存moduleにある場合は新規fileを増やさず既存moduleを拡張する。`GitHubSourceCode/`、
Google Drive同期folder、`GPU_RUN2/notebooks/`をruntime import先にしない。
