# GPU_RUN5 実験総まとめレポート

## 0. 報告対象

- campaign: `GPU_RUN5`
- run ID: `gpu_run5_20260823_ddd267b0`
- 実行期間: 2026年8月23日から2026年9月1日
- 主な計算環境: Python 3.10.20、PyTorch 2.5.1 + CUDA 12.4、NVIDIA GeForce RTX 2070 8 GB
- 主モデル: 公開ODEFormer checkpoint、4 encoder + 12 decoder、60,646,773 parameters
- 計画正本: [`plan.md`](plan.md)
- 機械判定正本: `results/runs/gpu_run5_20260823_ddd267b0/phase9/preregistration_outcome.json`
- 最終集約: `results/runs/gpu_run5_20260823_ddd267b0/phase9/manifest.json`

本レポートは、Phase 0–9の保存済みmanifest、64,620個の署名済みshard、Phase 9の5分冊レポートを統合した実験報告である。
観測事実、解釈、限界を分け、支持されなかった仮説と失敗記録も残す。

## 1. 要旨

GPU_RUN5の目的は、時系列軌道から常微分方程式を生成するTransformer **ODEFormer** を、
Hill型制御を含む閉じた遺伝子制御ネットワーク（GRN）へ適応し、少数の重要層だけをfine-tuningする方法が
全層fine-tuningより良い式構造回復と事前学習能力の保持を両立できるか検証することだった。

実験は、候補を生成できるか、複数軌道から正しい候補を選べるか、GRN向け学習で構造回復を改善できるか、の3段階を分離した。
さらに、probe、DecoderLens、CKA、gradient、activation intervention、formula-level IOLEを用いて16層を解析した。

主な結果は次のとおりである。

1. ODEFormerは変数分母を含む候補を生成できたが、真の変数分母構造は56 cell中0件しかbeam内へ入らず、選択後のexact回復も0件だった。
2. 複数初期条件による候補選択は、単一軌道選択よりgeneralization errorを平均0.2028改善した
   （paired system-cluster Student-t 95%区間: -0.3232から-0.0823）。
3. main testではGRN全層FTが式構造指標で最良だった。top 3層FTは高いvalid rateと数値再構成を保ったが、全層FTのformula scoreを上回らなかった。
4. top 3層FTはODEBench forgettingを全層FTより抑えたが、formula recoveryとの同時優位を要求したP7は外れた。
5. 固定24-system panelの16層では、teacher-forcing CEの層順位と介入後TEDの順位にほぼ対応がなかった
   （Spearman $`\rho=0.00896`$）。
6. Go 8はNO-GOだった。非自明なR03–R08のexact回復、family-holdout改善、generalization維持の条件を満たさず、DREAM4・実データへの追加実験は行わなかった。

前向き予測P3–P7とretrospective hypothesis R4–R5の機械判定は、6 hit、1 miss、0 undecidableだった。
これは「selective FTは無意味」という結果ではない。忘却抑制は確認された一方、本runの合成benchmark・固定beam条件では、
それだけで未知構造に相当する非自明GRN式を正しく回復できなかったことを示す負／混合結果である。

## 2. 目的

### 2.1 主目的

公開ODEFormerを閉じたHill型GRNへ適応し、次の連鎖を検証することを主目的とした。

```text
GRN構造を候補として生成する
  → 複数軌道から真式に近い候補を選ぶ
  → GRN向けfine-tuningで最終式回復を改善する
```

### 2.2 層解析の目的

モデル内部については、次の異なる問いを一つの曖昧な「重要度」へ混ぜずに評価した。

- probe: 層表現から数式属性を読み出せるか
- DecoderLens: decoder深度に沿って正解token順位がどう変化するか
- CKA: 同一module内の層表現がどの程度似ているか
- gradient: 学習信号がどのparameterへ流れるか
- activation intervention: 層を操作すると式と軌道評価がどれだけ壊れるか
- IOLE: その1層だけを更新したときGRNへ適応できるか

### 2.3 研究質問

主な研究質問は以下だった。

- ODEFormerはHill型・変数分母型のGRN式をbeam内へ生成できるか。
- 回復失敗はgeneration failureかselection failureか。
- 複数初期条件は、観測軌道だけに合う代替式を排除できるか。
- GRN全層FT、少数層FT、random層FTのどれが式構造を最も改善するか。
- 少数層FTはODEBench能力を守りながらGRN構造回復も改善できるか。
- teacher-forcing CEとsymbolic recoveryは同じ層順位を与えるか。

## 3. 背景

### 3.1 GRN方程式発見

遺伝子 $`i`$ の発現量を $`x_i(t)`$ とすると、閉じたGRNの時間発展は次の形で表される。

```math
\frac{dx_i}{dt}=f_i(x_1,\ldots,x_d)
```

シンボリック回帰の目標は、未知関数 $`f_i`$ を数値予測器のまま残すのではなく、人間が読める数式として回復することである。
Hill型制御では、飽和、抑制、協調性を表す分母や整数指数が機構上重要になる。

しかし、軌道上のNMSEや $`R^2`$ が良くても、真の変数、分母、指数、演算子構造を回復したとは限らない。
限られた軌道では、異なる式が同じ軌道へ近似できるためである。このためGPU_RUN5では、数値適合と式構造回復を分離した。

### 3.2 ODEFormerとGPU_RUN4からの課題

ODEFormerは、軌道 $`\mathbf{x}(t)`$ を直接入力し、微分推定を介さずODEを生成するTransformerである。
GPU_RUN4では公開checkpointの再現と評価器整備に成功した一方、GRN適応とformula-level層解析は未解決だった。

また、本runで使用した公開checkpointは4 encoder + 12 decoder、約61M parametersである。
論文表に記載された4 + 16層、約86Mの構成ではない。この相違を保ったまま「論文モデル完全再現」とは呼ばない。

### 3.3 GPU_RUN5の設計上の重点

GPU_RUN5では次の問題を特に重視した。

- testを層選択やhyperparameter選択へ使わない。
- 同一candidate setを使い、generationとselectionを分離する。
- 全trainable条件へ同じhyperparameter候補数を与える。
- 生成失敗、ParseError、NaN、timeout、trajectory積分失敗を除外せず保存する。
- 少数seedの区間推定を過大解釈しない。
- Go条件を満たさない場合、より難しい実データへ進んで失敗原因を混同しない。

## 4. 方法

### 4.1 モデルと実行環境

実行用ODEFormerは `third_party/odeformer/`、checkpointは `assets/odeformer/` の固定資産を使用した。
Phase 8 final testの環境はPython 3.10.20、PyTorch 2.5.1 + CUDA 12.4、NumPy 2.2.6、SciPy 1.15.3、SymPy 1.13.1で、
GPUはNVIDIA GeForce RTX 2070だった。

run IDはPhase 0開始commit `ddd267b0` を含む。長時間campaign中に監査・timeout境界の実装修正が必要になったため、
Phase 4、5、6以降はmanifestで個別commitを固定した。Phase 6–8は `e74d203`、Phase 9最終集約は `95ef259` で実行した。
したがって本runは「全Phaseが単一commit」ではないが、各Phaseのproducer manifest、上流artifact SHA256、checkpoint SHA256、
cell identityを連鎖的に検証している。Phase 8のvalidationと一度限りのfinal testは同じ `e74d203` で固定した。

### 4.2 データ

#### ODEBench

Track Aとforgetting評価には63 ODE systemからなるODEBenchを用いた。Track Aは63 system × 4 corruptionからなる
GPU_RUN4の保存済み252 cell、12,600 candidateの再解析であり、新規推論ではない。これらへ
変数分母、Hill型、modulated Hill型、代数的有理式などを分類した。

#### 閉じた合成GRN

GRN corpusはR01–R08の8式族から構成した。自己活性・抑制、toggle、cascade、相互活性、repressilator、
feed-forward、複合活性を含み、Hill指数は1、2、4を用いた。次元1–3の閉じた系として生成し、teacher式とcanonical truthの同値性、
非負性、特異点、積分可能性を監査した。各systemにinput、selection、generalization用の初期条件を分けて持たせた。
各systemはinput IC 1個、selection IC 2個、generalization IC 2個を持ち、noise 0 / 0.05とsubsampling 0 / 0.5の
4 corruptionで評価した。軌道はRK45、相対許容誤差 $`10^{-8}`$ で積分し、有限差分による微分推定は使用していない。

main splitはtrain 240、validation 80、test 80 systemで構成し、system、parameter variant、trajectoryの重複を0にした。
family viewはR01–R05のtrain 150、R06のvalidation 10、R07/R08のtest 20 systemで構成した。
main viewとfamily viewではselection contract、layer rank、checkpointを分離し、一方のviewのvalidation結果で他方を選び直さなかった。
ただしfinalのfamily-holdout 20 systemはmain test 80 systemの部分集合であり、独立な第2 testではない。
正しい表現は `system-structure-OOD_partial-component-overlap` である。
family viewのtrain–test間ではsystem-level canonical skeletonの重複は0だったが、component skeletonは4 fingerprintが重複したため、
完全なcomponent OODとは呼ばない。軌道生成時の棄却率は1.4778%で、棄却理由も保存した。

### 4.3 実験条件

最終testでは次の5条件を事前固定した。

| 条件 | 意味 |
|---|---|
| `frozen` | 公開checkpointを更新しない |
| `official_continued_full` | 公式分布で全層を継続学習する対照 |
| `grn_full` | GRN corpusで全層をfine-tuning |
| `grn_top3` | validationで凍結した上位3層だけをGRN fine-tuning |
| `grn_random3_0` | 事前固定random 3層集合のtest代表 |

Phase 7で凍結されたmain IOLE top 3は `decoder_11`、`decoder_10`、`decoder_8`、
family-holdout top 3は `decoder_8`、`decoder_9`、`decoder_10` だった。
main causal top 3は `decoder_11`、`decoder_3`、`encoder_3` であり、IOLE top 3とは一致しなかった。

### 4.4 Phase構成

| Phase | 内容 | 主な保存単位 |
|---:|---|---|
| 0 | commit、checkpoint、architecture、予測、schemaの凍結 | manifest、preregistration |
| 1 | ODEBench decoded support再解析 | 252 cell、12,600 candidate |
| 2 | 閉じたGRN corpus、split、評価器 | system、trajectory、truth |
| 3 | frozen baseline、generation / selection診断 | beam 50 candidate、P6 |
| 4 | probe、gradient、CKA、DecoderLens | 16層の観測的指標 |
| 5 | activation interventionと介入後decode | $`\Delta`$CE、$`\Delta`$TED、P5 |
| 6 | full / decoder-all適応とhyperparameter固定 | 7,992 decode shard |
| 7 | 16層IOLE、rankと層集合の凍結 | 26,112 decode shard |
| 8 | selective validation、一度限りのfinal test、forgetting | validation 20,736、GRN test 6,000、ODEBench 3,780 |
| 9 | 統合解析、機械判定、図表、provenance | Result A–E、5レポート |

### 4.5 候補選択

各cellでbeam候補を保存し、単一input軌道だけでなく、別初期条件のselection軌道を使って候補をrerankした。
testのcandidate budgetはbeam 50、学習bundleは3個で固定した。generalization軌道は選択へ使わず、選択後の外挿評価だけに使った。

### 4.6 評価指標

主要指標は次のとおりである。

- exponent-aware skeleton exact: 数値定数を抽象化しても整数指数を保持する構造一致
- normalized variable-aware TED: 変数と指数を考慮した正規化木編集距離
- component valid rate: 多次元式の各成分が評価可能だった割合
- reconstruction $`R^2`$: 入力軌道の再構成
- generalization NRMSE: 未使用初期条件の軌道誤差
- formula score: exact、負のfailure-aware TED、valid rateなどを事前順序で比較するlexicographic score

低NMSEとexact recoveryを同一視せず、failure-aware TEDを主集計へ含めた。

### 4.7 統計

- P6は80 system clusterを単位とするpaired差へStudent-t 95%区間を用いた。
- 3 bundle集計はsystem内を先に平均し、その後seed macroを計算した。
- n=3の区間は自由度2で広く、同一system corpusを3 bundleで共有するためsystem sampling uncertaintyを含まない。
- 率のWilson 95%区間は、反復corruptionやcomponent依存を無視した記述的naive区間としてのみ報告した。

### 4.8 test firewallと再現性

層順位、random集合、hyperparameter、checkpoint、beam budgetをvalidationだけで固定した。
Go 6とGo 7が通った後、sealed testを1回だけ開いた。台帳は `open_count=1`、`resume_count=0` である。
Phase 9はsealed test本体を再読せず、署名済みfinal artifactだけを集約した。

Phase 9は次の64,620 shardをpath confinement、byte数、SHA256までstream検証した。

- Phase 6: 7,992
- Phase 7: 26,112
- Phase 8 validation: 20,736
- Phase 8 final GRN: 6,000
- ODEBench forgetting: 3,780

## 5. 結果

### 5.1 実行完了性

Phase 0–9はすべてcompleteとなった。Phase 8 validationは20,736 / 20,736 cell、
final GRNは6,000 / 6,000 cell、ODEBench forgettingは3,780 / 3,780 cellを保存した。
Phase 9の全機械gateはtrueだった。

### 5.2 Result A: ODEBench decoded support

12,600 candidateのうち、変数分母を含む候補は1,860件、14.76%だった。
したがって、公開ODEFormerの語彙とdecoderは変数分母表現を完全には排除していない。

一方、全252 beam groupで真のexponent-aware skeletonがbeam内にあったのは4件、1.59%にとどまった。
変数分母truth 56 cellに限ると、真構造がbeam内にあったcellもselected exactも0件だった。
R4「変数分母候補率5%以上」はhit、R5「変数分母56 cellのselected exactは0件」もhitだった。

この結果は、**候補形式を出せること** と **対象の真構造を出せること** が別問題であることを示す。

### 5.3 Result B: generationとselection

frozen GRN validationではtrue exponent-aware skeleton in beam率が0だったため、主なボトルネックはselection以前のgenerationにあった。
ただし、既存候補の中からより外挿可能な式を選ぶ点ではmulti-IC selectionが有効だった。

P6のmulti-IC minus single-trajectory failure-aware generalization NRMSEは平均 -0.2028で、
95%区間は[-0.3232, -0.0823]だった。
符号はmulti-IC側の誤差が小さいことを表す。80 system clusterで区間上端も0未満だったためP6はhitとなった。

したがって、複数初期条件は固定beam内の候補rerankingにおけるgeneralization errorを改善した。
しかしformal identifiabilityや真構造識別率の改善を示す結果ではなく、beam内に存在しない真構造を回復することもできなかった。

### 5.4 Result D: 層解析

mainのformula-level IOLE top 3はdecoder最終部の `decoder_11`、`decoder_10`、`decoder_8` に集中した。
family-holdoutでも `decoder_8`、`decoder_9`、`decoder_10` が上位であり、decoder中後段への局在は共通していた。

ただし、順位安定性はmainで平均Spearman 0.480、Kendall $`\tau_b=0.389`$、family-holdoutで0.781と0.622だった。
完全に安定した単一順位ではない。

さらに、異なるestimandのtop層は一致しなかった。

| estimand | main top 3 |
|---|---|
| next-token probe | `decoder_11`, `decoder_10`, `decoder_9` |
| formula IOLE | `decoder_11`, `decoder_10`, `decoder_8` |
| causal intervention | `decoder_11`, `decoder_3`, `encoder_3` |

P5では16層の $`\Delta`$CE順位とfailure-aware $`\Delta`$TED順位のSpearman相関が0.00896、
両側p値が0.9737だった。P5の「相関0.5以下」はhitである。
これは無相関を一般的に証明するものではないが、固定panelではCEがsymbolic damage順位の十分な代理でなかったことを示す。

### 5.5 Phase 8 validationとGo 6 / Go 7

main validationで `grn_top3` はfrozenを上回り、5個の固定random集合のうち
`grn_random3_1`、`grn_random3_3`、`grn_random3_4` の3集合を上回ったためGo 6を通過した。
checkpoint、2 view、beam 50、3 bundle、test未参照、freeze hashの検査もすべて通り、Go 7を通過した。

この時点ではselective FTをfinal testへ送る合理的根拠があった。final結果が逆転したことは、testを見て条件を選び直さなかった証拠でもある。

### 5.6 Result C: main final test

main testの主要結果を以下に示す。exact macroはsystem内component/corruptionをまとめた後のseed macroである。

| 条件 | exact macro | failure-aware TED | valid rate | reconstruction $`R^2`$ 中央値 | generalization NRMSE |
|---|---:|---:|---:|---:|---:|
| frozen | 0.02396 | 0.47917 | 1.00000 | 0.93582 | 1.40764 |
| official continued full | 0.05972 | 0.46147 | 1.00000 | 0.94164 | 1.44240 |
| GRN full | **0.15972** | **0.36865** | 0.97157 | 0.22203 | 2.19822 |
| GRN top 3 | 0.10938 | 0.46111 | 0.99118 | 0.93064 | 2.29097 |
| GRN random 3 | 0.10764 | 0.44223 | **1.00000** | 0.89959 | **1.26859** |

GRN fullはexact macroとTEDで最良だったが、valid rate、再構成、generalizationは悪化した。
GRN top 3は再構成 $`R^2`$ とvalid rateを比較的保ったが、exactとTEDではGRN fullに負け、generalization NRMSEも最悪だった。
random 3代表はtop 3と近いexactを示し、generalizationでは最良だった。

ここでexact macro 0.15972を「非自明GRNの16%を回復した」と解釈してはならない。
R03–R08の非自明なHill・変数分母成分に限定したexact component countは、全final条件で0件だった。

このため「validationで選んだ少数層が、全層FTとrandom層FTを一貫して上回る」という強い主張は支持されない。

### 5.7 family-holdout

family-holdoutの結果は次のとおりだった。

| 条件 | exact macro | failure-aware TED | valid rate | generalization NRMSE |
|---|---:|---:|---:|---:|
| frozen | 0.06250 | 0.48817 | 1.00000 | 0.93131 |
| official continued full | 0.14306 | 0.47044 | 1.00000 | 0.68116 |
| GRN full | **0.18750** | **0.45672** | 1.00000 | **0.49330** |
| GRN top 3 | 0.05278 | 0.49145 | 1.00000 | 0.53747 |
| GRN random 3 | 0.03472 | 0.50196 | 1.00000 | 0.89513 |

GRN top 3はfrozenよりexactが低く、TEDも悪かった。したがってGo 8のfamily-holdout改善条件を満たさなかった。
ただし、このviewはmain testのR07/R08 subsetであり、独立再現とは数えない。

### 5.8 ODEBench forgettingとP7

ODEBench exponent-aware exact rateはfrozen 0.08466、GRN top 3が0.06085、GRN fullが0.00794だった。
frozenからの低下はtop 3が0.02381、fullが0.07672であり、少数層FTは全層FTより事前学習能力を保持した。

しかしP7は、forgettingが小さいだけでなく、GRN formula scoreでもtop 3がfullを上回ることを要求した。
formula scoreはtop 3が `[0.109375, -0.470379, 0.992708]`、fullが
`[0.159722, -0.379755, 0.964236]` で、事前順序のlexicographic比較ではfullが上だった。
よってP7はmissとなった。

### 5.9 P3–P7、R4–R5の機械判定

| ID | 判定 | 要点 |
|---|---|---|
| P3 | hit | frozen test exact macro 0.02396で事前閾値0.05未満 |
| P4 | hit | frozen reconstruction $`R^2`$ 中央値0.93582、かつP3 hit |
| P5 | hit | $`\Delta`$CEと $`\Delta`$TEDのSpearman 0.00896 |
| P6 | hit | multi-ICのgeneralization error改善区間上端 -0.0823 |
| P7 | **miss** | top 3はforgettingを抑えたがformula scoreでfullに負けた |
| R4 | hit | 変数分母candidate率14.76% |
| R5 | hit | 変数分母56 cellでselected exact 0件 |

合計は6 hit、1 miss、0 undecidableである。hit数を「方法が成功した仮説数」と単純解釈してはならない。
P3、R5のように、低い構造回復を予測どおり確認した項目もhitに含まれる。

### 5.10 Go 8

Go 8の判定はNO-GOだった。

| 判定条件 | 結果 |
|---|---|
| 非自明R03–R08でexactを1成分以上回復 | 不成立 |
| family-holdoutでtop 3がfrozenよりexact改善またはTED低下 | 不成立 |
| P6を支持 | 成立 |
| main valid rate低下が0.05以内 | 成立。低下0.00729 |
| main generalization NRMSE比が1.10以内 | 不成立。比1.62752 |
| validationでfrozenとrandom 3/5以上に優位 | 成立 |

6条件中3条件が不成立だったため、DREAM4・実データへの追加実験は実施しなかった。
これは計算不足ではなく、性能不足を実データの難しさと混同しないための事前固定停止である。

### 5.11 failureと監査結果

Phase 9はPhase 6–8の署名済みGRN shardから128,007件のphysical failure eventを一意IDで書き出した。
selectedか否かは別eventとして二重計上せず、属性として保持した。

final GRNでは292,618 candidateを保存し、beam 50に対するshortfallは7,382 candidateだった。
generation failureは0、cell timeout発火は1 cell、candidate failureは610件、selected trajectory failureは276件だった。

ODEBench forgettingは上記128,007件とは別に監査した。182,772 candidateを保存し、shortfallは6,228、`EmptyCandidateSet` は27 cell、
candidate failureは5,187件で、そのうちtimeout系は852件だった。これらを成功式だけの中央値から除外せず、failure-aware集計へ残した。

## 6. 考察

### 6.1 最大の障害はgeneration supportである

変数分母tokenを含むcandidateが14.76%あったにもかかわらず、変数分母truthの真構造は56 cell中0件だった。
これは「演算子が出る」ことと「必要な構造を組み立てられる」ことの差である。
candidate selectionを改善しても、真構造がbeamに存在しなければexact recoveryには到達できない。

次runではrerankingだけでなく、GRN構造をpretraining / adaptation distributionへ入れる方法、
beam diversity、構造制約付きdecode、指数と分母を明示的に扱う表現を検討する必要がある。

### 6.2 multi-IC selectionは有効だが十分ではない

P6は明確に支持された。複数初期条件を使うrerankingは、入力軌道だけに合う候補を減らした可能性があり、
固定beam候補のgeneralization errorを改善した。ただしformal identifiabilityや真構造識別率は評価していない。

一方、Phase 3でtrue skeleton in beamが0だったため、selection改善だけでは構造回復問題を解けなかった。
generationとselectionを分離したことで、この限界を明確にできた。

### 6.3 全層FTと少数層FTのtrade-off

GRN fullはformula recoveryを最も改善したが、再構成、generalization、valid rate、ODEBench能力を傷つけた。
top 3は忘却と再構成を相対的に抑えたが、構造回復はfullに届かなかった。

したがってselective FTの価値は、今回の設定では「全層FTより強いGRN式回復」ではなく、
「事前学習能力の損失を小さくするregularization」に近い。ただしrandom 3代表も強く、選んだ3層固有の優位は確立していない。

### 6.4 層重要度は単一ではない

probe、IOLE、causal interventionのtop層は部分的に重なったが一致しなかった。
特に固定24-system panelの16層ではCEとTEDの順位対応がほぼ観測されなかった。
この結果は、teacher-forcingでtokenを当てる指標を、自由生成された式の構造・積分安定性の代理として扱えなかったことを示す。

この不一致をノイズとして平均するのではなく、各指標が測るestimandの違いとして扱うべきである。
GPU_RUN2–5の横断結果も、モデル世代を越えた単一の「普遍的重要層」を支持しなかった。

### 6.5 P7 missが示す研究上の修正

GPU_RUN2では少数層FTが数値性能と安定性を改善する傾向があった。しかしODEFormerを用いたGPU_RUN5では、
prior保持とGRN formula recoveryの同時優位は成立しなかった。
よって「少数層だけ学習すれば全層FTより常に良い」という一般化は棄却すべきである。

より限定的には、「少数層FTはforgettingを抑え得るが、本runではformula recoveryとの両立に失敗した」と解釈できる。
全層FTも非自明構造のexact回復は0件でgeneralizationとforgettingを悪化させたため、全層FTを十分な解決策とはみなさず、
構造回復とprior保持を両立する別設計が必要である。

### 6.6 Go 8 NO-GOの意味

Go 8 NO-GOは実験失敗を隠すための打ち切りではない。合成環境で非自明構造のexact回復と外挿安定性を満たせない段階で、
DREAM4やヒト時系列へ進むと、モデル能力不足、有限差分、観測不足、domain shiftを分離できなくなる。

一度限りのtestを保持し、結果を見た後に条件を足さなかったこと自体が、本runの研究上の重要な成果である。

## 7. 限界

1. **checkpointの世代差**: 使用モデルは公開4 + 12層、約61Mであり、論文表の約86M構成ではない。
2. **合成GRN**: 最終主評価はR01–R08合成系であり、実在GRNの真の制御ODEを示さない。
3. **少数bundle**: 3 bundle区間は広く、system corpusを共有するためsystem sampling uncertaintyを含まない。
4. **family-holdoutの非独立性**: R07/R08はmain testのsubsetであり、独立な再現証拠ではない。
5. **Wilson区間**: componentとcorruptionの依存を無視した記述的区間であり、独立systemへの推測区間ではない。
6. **固定beam**: beam 50で真構造がないことは、無限探索でも生成不能であることを意味しない。
7. **fine-tuning範囲**: full FTとblock単位FTを比較したが、LoRA、adapter、構造制約付き学習は扱っていない。
8. **campaign commit**: Phaseごとに監査済みcommitは固定したが、Phase 0–9全体が単一commitではない。
9. **層順位のpanel依存**: causal順位とIOLE順位は固定validation panelに依存し、別corpusでの普遍性は未確認である。
10. **DREAM4・実データ未実施**: Go 8に従った結果であり、GPU_RUN5単独から生物学的機構を主張できない。

## 8. まとめ

GPU_RUN5は、ODEFormerのGRN式回復をgeneration、selection、adaptationへ分解し、層解析と一度限りのtest評価を接続した。

確認できた肯定的結果は、multi-IC selectionがgeneralizationを改善したこと、GRN full FTが式構造指標を改善したこと、
少数層FTがODEBench forgettingを全層FTより抑えたこと、decoder中後段にformula-level適応信号が集中したことである。

一方、最重要の否定的結果は、非自明なGRN構造のexact回復がなく、top 3層FTが全層FTをformula scoreで上回らず、
family-holdoutとgeneralizationのGo条件も満たさなかったことである。

したがって本runの結論は次の一文に要約できる。

> 本runの公開ODEFormer checkpoint、R01–R08合成benchmark、beam 50、3 bundleという条件では、
> 少数decoder層の更新は事前学習能力の保持に役立ったが、非自明なHill型GRN構造の安定した生成・回復には至らず、
> generation supportそのものの改善が次の主要課題である。

この結論に基づき、DREAM4・実データへは進まず、次runではGRN構造を候補集合へ入れる学習・探索設計を先に改善する。

## 9. 成果物と再現方法

### 9.1 分冊レポート

- [Decoded support（Result A）](GPU_RUN5_decoded_support_report.md)
- [GRN generation / selection（Result B）](GPU_RUN5_grn_benchmark_report.md)
- [GRN adaptation（Result C）](GPU_RUN5_grn_adaptation_report.md)
- [Layer analysis（Result D）](GPU_RUN5_layer_analysis_report.md)
- [Cross-model synthesis（Result E）](GPU_RUN5_cross_model_synthesis.md)

### 9.2 図表

- [図表provenance](../graphs/gpu_run5_20260823_ddd267b0/README.md)
- [failure funnel](../graphs/gpu_run5_20260823_ddd267b0/figures/phase9_failure_funnel.svg)
- [final condition formula scores](../graphs/gpu_run5_20260823_ddd267b0/figures/phase9_final_condition_formula_scores.svg)
- [input IC vs generalization IC](../graphs/gpu_run5_20260823_ddd267b0/figures/phase9_input_vs_generalization.svg)
- [$`\Delta`$CE vs $`\Delta`$TED](../graphs/gpu_run5_20260823_ddd267b0/figures/phase9_delta_ce_vs_delta_ted.svg)

### 9.3 実行

```bash
conda activate lansr310
export CUDA_VISIBLE_DEVICES=0
bash scripts/ops/run_gpu_run5.sh --run-id gpu_run5_<date>_<commit8>
```

Phase 9だけを署名済み成果物から再生成する場合は次を使う。

```bash
python scripts/phases/gpu_run5_phase9.py \
  --run-id gpu_run5_20260823_ddd267b0
```

## 10. 参考文献

1. d'Ascoli, S., Becker, S., Mathis, A., Schwaller, P., & Kilbertus, N. (2024).
   **ODEFormer: Symbolic Regression of Dynamical Systems with Transformers.** ICLR 2024.
   <https://openreview.net/forum?id=TzoHLiGVMo>
2. d'Ascoli et al. **ODEFormer official repository.**
   <https://github.com/sdascoli/odeformer>
3. GPBench. **ODEBench: an ODE benchmark for system identification.**
   <https://github.com/GPBench/ODEBench>
4. Schaffter, T., Marbach, D., & Floreano, D. (2011).
   **GeneNetWeaver: In Silico Benchmark Generation and Performance Profiling of Network Inference Methods.**
   *Bioinformatics*, 27(16), 2263–2270. <https://doi.org/10.1093/bioinformatics/btr373>
5. Kornblith, S., Norouzi, M., Lee, H., & Hinton, G. (2019).
   **Similarity of Neural Network Representations Revisited.** ICML 2019.
   <https://arxiv.org/abs/1905.00414>
6. GPU_RUN5計画正本: [`plan.md`](plan.md)
7. GPU_RUN4結果: [`../GPU_RUN4/GPU_RUN4_research_report_20260819.md`](../GPU_RUN4/GPU_RUN4_research_report_20260819.md)
8. 研究全体の背景と用語: [`../README.md`](../README.md)
