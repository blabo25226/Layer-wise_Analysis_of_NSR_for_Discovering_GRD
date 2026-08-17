# GPU_RUN3 計画

作成日: 2026-08-17
状態: Draft v0.3

## 方針

GPU_RUN3は、次の **二大目標を同格の主目的** とする。

1. **ND² (Neural Discovery of Network Dynamics) を公式実装・公開資産に基づいて再現する。**
2. **再現したND²の中核モデルNDformerに対して、GPU_RUN2と同程度に体系的なTransformer層解析を行う。**

つまりGPU_RUN3は「ND²再現のついでに層を見る」実験でも、「層解析のために最低限ND²を動かす」実験でもない。
**ND²の再現研究とNDformerの層解析を一本の実験キャンペーンの二本柱として実施する。**

GPU_RUN2までのGRN中心の設計は一度緩め、ND²論文が対象とする一般のnetwork dynamicsへ対象を広げる。
一方でLANSRの中心テーマである層解析は維持し、GPU_RUN2で設計したprobe、CKA、DecoderLens、
単一層fine-tuning、ablation、activation intervention、parameter update sensitivity等をNDformerへ移植する。

数式構造評価には従来のexact / skeleton / symbolic equivalenceに加えて **Tree Edit Distance (TED)** を導入する。

---



# 1. 目的と範囲



## 1.1 主目的A: ND²の再現

Yu, Ding, and Li, “Discovering network dynamics with neural symbolic regression” で提案されたND²について、
公式code、checkpoint、pretraining資産、synthetic benchmarkを可能な限りそのまま利用し、論文の主要な数式発見挙動を再現する。

再現対象は単なるforward動作確認ではなく、少なくとも次を含む。

1. NDformerの公式checkpoint読み込みとpolicy prediction
2. ND²公式symbol set / network dynamical operators / prefix表現の再現
3. NDformer-guided MCTSの実行
4. 定数最適化、reward計算、Pareto front生成
5. ND²論文で用いられたsynthetic network dynamics benchmarkの再現
6. 真式、予測式、fit error、exact / symbolic recovery、search costの保存
7. 可能であればNDformerあり / なしのsearch efficiency比較

ND²論文本文では、pretraining datasetはランダム生成したnetwork dynamics formula、network structure、node activityからなる
約100万sampleとされ、Erdős–Rényi、Watts–Strogatz、Barabási–Albert、complete graph等のnetworkを含む。
NDformerはGNNとTransformer encoder / decoderを用いて、network structure、node activities、incomplete formulaから
次symbolのpolicyを出し、そのpolicyでMCTSを誘導する。

GPU_RUN3ではこのpipelineを「層解析の前提」だけで終わらせず、**ND²再現自体を一つの主要成果として残す。**

## 1.2 主目的B: NDformerの層解析

再現したNDformerについて、Transformer encoder / decoderの各層が、数式生成においてどのような情報を持ち、
どの程度因果的に最終出力へ寄与するかを解析する。

GPU_RUN2で設計した層解析を原則として同様に実装する。

- linear probe
- gradient norm
- CKA
- DecoderLens型encoder解析
- decoder-side intermediate / logit-lens型解析
- parameter update sensitivity
- single-layer fine-tuning（IOLE条件）
- layer ablation
- activation intervention / activation patching
- probe / FT / ablation / intervention間のlayer ranking比較
- `frozen` / `full` / `top 1` / `top 3` / `random 3` fine-tuning比較

ここで重要なのは、

- probeで情報が「読める」こと
- ablationでその層が「必要」であること
- activation interventionでその層が「因果的に影響する」こと
- single-layer FTでその層が「適応能力を持つ」こと

を区別することである。

## 1.3 GPU_RUN3の中心的な問い

GPU_RUN3では、次の二つの問いを同時に扱う。

> **A. ND²は公開された公式資産を用いて、network dynamicsの真の数式をどの程度再現できるか。**

> **B. その数式発見を導くNDformerでは、数式情報と数式回復能力がTransformerのどの層に形成・集中しているか。**

さらに両者を接続して、

> **層解析で重要と判断された層への介入は、ND²全体のMCTSによる最終的な数式発見性能を実際に変化させるか。**

まで確認する。

---



# 2. GPU_RUN2からの変更点


| 項目                           | GPU_RUN2                                | GPU_RUN3                                                |
| ---------------------------- | --------------------------------------- | ------------------------------------------------------- |
| 中心モデル                        | NeSymReS                                | **ND² / NDformer**                                      |
| 主題                           | GRN向けNeSymReS層解析                        | **ND²再現 + NDformer層解析**                                 |
| 事前学習分布                       | NSRS / NeSymReS                         | **ND²公式pretraining distribution**                       |
| 主データ                         | GNW由来合成GRN式                             | **ND²公式pretraining / validation資産 + synthetic systems** |
| network表現                    | 通常の多変数SR                                | **network dynamical operatorsを用いるND²表現**                |
| search                       | standard beam中心                         | **NDformer-guided MCTS**                                |
| GRN oracle regulator         | 使用                                      | 主実験から外す                                                 |
| GNW専用operator                | 使用                                      | ND²公式symbol setへ変更                                      |
| probing                      | 実施                                      | **同様に実施**                                               |
| gradient norm                | 実施                                      | **同様に実施**                                               |
| CKA                          | 実施                                      | **同様に実施**                                               |
| DecoderLens                  | 実施                                      | **NDformerへ移植**                                         |
| ablation                     | 実施                                      | **同様に実施**                                               |
| activation intervention      | 実施                                      | **同様に実施**                                               |
| parameter update sensitivity | 実施                                      | **同様に実施**                                               |
| IOLE単一層FT                    | 実施                                      | **同様に実施**                                               |
| selective FT                 | frozen/full/top/random                  | **同様に実施**                                               |
| symbolic metrics             | exact / skeleton / symbolic equivalence | 左記 +**TED**                                             |
| ND²再現                        | なし                                      | **主要目標として実施**                                           |
| DREAM4 / ヒト                  | 後続候補                                    | GPU_RUN3では扱わない                                          |
| PySR / TPSR                  | 比較候補                                    | 主実験から外す                                                 |


GPU_RUN3では、GPU_RUN2の「層解析の深さ」を維持しつつ、対象モデルとデータ分布をND²へ変更する。

---



# 3. ND²とNDformerの区別

GPU_RUN3では次を明確に区別する。

## ND²

network dynamicsの数式発見pipeline全体。

概念的には、

1. network structure / node activitiesを入力
2. network dynamical operatorsによりnetwork-size-independentなformula spaceを構成
3. NDformerが次symbol policyを出力
4. MCTSがpolicyを使ってformula treeを探索
5. candidate formulaを評価
6. 定数を最適化
7. accuracyとcomplexityからPareto frontを構成
8. 最終formulaを選択

という流れを持つ。

## NDformer

ND²のsearchを導くニューラルモデル。

主に、

- GNN / graph representation
- Transformer encoder
- Transformer decoder
- embedding
- policy MLP / output head

から構成され、network structure、node activities、incomplete formulaを条件として次symbolのpolicyを出す。

**ND²再現ではpipeline全体を評価し、層解析では主としてNDformerのTransformer encoder / decoderを解析する。**

---



# 4. 研究質問



## RQ1: ND²再現性能

**公式code・checkpoint・公開データを用いたND²は、論文のsynthetic systemsで真のnetwork dynamics formulaを再発見できるか。**

評価対象:

- exact formula recovery
- canonical exact recovery
- skeleton recovery
- symbolic equivalence
- TED
- fit error
- formula complexity
- valid rate
- search success rate
- wall time
- candidate / search node count



## RQ2: NDformer policyの再現

**公式checkpointのNDformerは、公式validation分布において正解の次symbolへ高いpolicy probabilityを与えるか。**

評価対象:

- cross entropy
- top-1 accuracy
- top-k accuracy
- ground-truth symbol rank
- ground-truth symbol probability
- policy entropy



## RQ3: 層ごとの情報表現

**NDformerのencoder / decoder各層には、数式構造・operator・tree complexity・次symbolに関するどの情報が表現されるか。**

主手法:

- linear probe
- gradient norm
- CKA
- DecoderLens型解析
- decoder-side intermediate readout



## RQ4: 因果的な層寄与

**probeで情報が強く観測される層は、ablationやactivation interventionでもpolicyや最終formulaへ大きな因果効果を持つか。**

主手法:

- layer ablation
- activation zero / mean intervention
- matched-control activation replacement
- activation patching
- IOLE single-layer FT



## RQ5: 少数層fine-tuning

**NDformerでも、重要層1–3層だけのfine-tuningでfull fine-tuningに近い改善を得られるか。またtop層はrandom層より有効か。**

比較:

- `frozen`
- `full`
- `top 1`
- `top 3`
- `random 3`



## RQ6: 数式構造はどの層で形成されるか

**正解式に近いtree structureは、NDformerのどの層で形成され、どの層への介入で崩れるか。**

exact / skeleton / symbolic equivalenceに加え、TEDを連続的なstructure distanceとして使用する。

## RQ7: 層の重要性はND²全体のsearch性能へつながるか

**policy-levelで重要と判定された層への介入やfine-tuningは、NDformer-guided MCTSの最終formula recoveryも変化させるか。**

これにより「次symbol predictionで重要だった」だけでなく、ND²全体の数式発見へ実際に寄与するかを確認する。

## RQ8: 事前学習分布との関係（副解析）

**ND² pretraining distributionに近い式と遠い式で、層表現・層寄与・最終TEDは変わるか。**

RQ1–RQ7より優先度は低く、計算資源が許す場合に実施する。

---



# 5. 参照資料



## 5.1 ND²

主参照:

- Zihan Yu, Jingtao Ding, Yong Li, “Discovering network dynamics with neural symbolic regression,” *Nature Computational Science* (2025)
- DOI: `10.1038/s43588-025-00893-8`
- 公式実装: `https://github.com/tsinghua-fib-lab/ND2`
- 公式公開資産: Zenodo `10.5281/zenodo.16995963`

GPU_RUN3では次をND²公式仕様から取得する。

- NDformer architecture
- network dynamical operators
- symbol vocabulary
- prefix formula representation
- pretraining data generation
- official checkpoint
- policy prediction task
- MCTS settings
- reward / complexity definition
- constant optimization
- synthetic benchmark systems
- official evaluation definitions



## 5.2 GPU_RUN2から継承する層解析

GPU_RUN2で設計した以下をNDformerへ移植する。

- linear probe
- gradient norm
- CKA
- DecoderLens
- parameter update sensitivity
- layer ablation
- activation intervention / patching
- IOLE single-layer FT
- top / random / full FT比較
- layer rank stability
- probe / FT / ablation / intervention間の順位一致

NDformerとNeSymReSではarchitectureが異なるため、hook位置やmodule名をそのまま移植するのではなく、
**解析原理と比較設計を移植する。**

## 5.3 CKA

Kornblith et al., “Similarity of Neural Network Representations Revisited,” ICML 2019を参照する。

CKAはrepresentation similarityを測る記述的指標とし、CKA単独から層機能を断定しない。

## 5.4 DecoderLens

Langedijk et al., “DecoderLens: Layerwise Interpretation of Encoder-Decoder Transformers,” arXiv:2310.03686v2を参照する。

NDformerのencoder中間representationを通常decoderへ接続できる場合、encoder layerごとの暫定policy / formulaを観測する。
architecture上そのまま適用できない場合は`encoder_intermediate_decode`として実装し、DecoderLensと完全に同一とは呼ばない。

## 5.5 IOLE

Zhang et al., “Is One Layer Enough? Training a Single Transformer Layer Can Match Full-Parameter RL Training,” arXiv:2607.01232v2を参照する。

GPU_RUN3では、

> 1 Transformer blockだけをtrainableとし、他層をfreezeしてfull FTと比較する

という実験単位だけをNDformerへ移植する。

## 5.6 Activation intervention

BPAP / HUIAP等を参考に、介入位置、baseline、metric、patch pairをvalidationで固定する。

## 5.7 TED

主参照:

- Tatsuya Akutsu et al., “Tree Edit Distance with Variables. Measuring the Similarity between Mathematical Formulas,” arXiv:2105.04802
- `docs/paper/TED_paper.pdf`
- `docs/translated_paper/TED_translated.md`

GPU_RUN3では少なくとも次を区別する。

- `ted_raw`
- `ted_skeleton`
- `ted_variable_aware`（実行可能な場合）

TEDはexact recoveryを置き換えず、**「完全一致しなかった式がどの程度正解に近いか」**を測る補助指標とする。

---



# 6. 研究上の絶対条件



## 6.1 ND²再現とLANSR改変を混ぜない

公式再現runでは、可能な限りupstream code / checkpoint / configをそのまま使用する。
層hook、ablation、FT等を加えたLANSR解析runとはrun IDとconfigを分離する。

公式再現結果と改変後結果を同じ表へ混ぜる場合は、`upstream_reproduction` / `layer_analysis`等のprovenanceを明記する。

## 6.2 validation / test分離

- probe task / hyperparameterはvalidationで固定する。
- layer rankingはvalidationだけで決定する。
- activation intervention設定もvalidationで固定する。
- selective FTのlearning rate / epoch / early stoppingもvalidationで固定する。
- testはすべて固定した後に一度だけ評価する。



## 6.3 paired comparison

同じseed内では可能な限り、

- initial checkpoint
- data order
- problem / prefix
- MCTS budget
- timeout
- random state

をそろえる。

## 6.4 failureを隠さない

以下を成功例から除外して平均だけ出すことをしない。

- invalid formula
- parse error
- MCTS timeout
- constant optimization failure
- NaN / Inf
- TED parse failure
- OOM
- activation hook failure

valid rate / failure rateと理由を保存する。

## 6.5 数値精度と式回復を区別する

fit errorが小さくても、真のformulaを回復したとは限らない。

必ず、

- fit error
- exact
- skeleton
- symbolic equivalence
- TED
- complexity
- valid rate

を分けて報告する。

## 6.6 層解析の解釈を分ける

- probe: 情報が線形にreadout可能か
- CKA: representationが似ているか
- gradient norm: loss sensitivityの一側面
- IOLE: その層だけで適応できるか
- ablation: その層を除くと性能が落ちるか
- activation intervention: 内部representationを変えると出力が変わるか

を混同しない。

---



# 7. 実行環境とprovenance

Phase 0で最低限次を保存する。

- LANSR repository commit
- ND² upstream repository URL / branch / commit
- checkpoint SHA256
- dataset / archive checksum
- Python version
- PyTorch version
- CUDA version
- GPU / CPU / RAM / OS
- ND² config
- MCTS config
- random seed
- timestamp

公式codeを調査用directoryから直接変更して使わず、必要なら`third_party/nd2`等へ固定コピーし、upstreamとの差分を記録する。

run途中でsource commit、checkpoint、主configを変更しない。

---



# 8. NDformer architecture inventory

層解析前に公式checkpointとcodeからNDformer構造を機械可読に取得する。

最低限保存する。

- module name
- module type
- GNN / encoder / decoder / embedding / head区分
- layer index
- parameter count
- input / output shape
- normalization位置
- residual構造
- self-attention / cross-attention構造
- trainable parameter status

主なlayer ranking対象は **Transformer encoder block / decoder block** とする。

次は別controlとして扱い、`top 3` / `random 3`へ原則混ぜない。

- GNN
- input embedder
- final normalization
- policy MLP / output head

ただしGNN / headのablation、gradient norm等はTransformerとの比較controlとして保存してよい。

---



# 9. データとsplit



## 9.1 ND²公式pretraining / validation資産

NSRS distributionは主実験に使用せず、ND²公式distributionを基準とする。

公式code / dataから最低限次を取得しmanifestへ保存する。

- sample count
- symbol vocabulary
- grammar
- operator sampling rule
- formula length distribution
- tree depth distribution
- network family
- node count distribution
- degree distribution
- node activity sampling
- constant sampling
- prefix generation rule
- official split



## 9.2 ND² synthetic systems

論文本文で示される10 synthetic systemsを再現対象の基本集合とする。

- Kuramoto
- coupled Rössler oscillator
- homogeneous coupled Rössler
- FitzHugh–Nagumo
- Wilson–Cowan
- gene regulatory
- Michaelis–Menten
- Lotka–Volterra
- mutualistic population
- susceptible-infected-susceptible (SIS)

正確な式、parameter、network、seed、data生成法はofficial sourceを一次資料として固定する。

## 9.3 Layer-analysis corpus

層解析には正解formulaとformula prefixが必要なので、ND²公式pretraining / validation生成系から専用corpusを作る。

最低限:

- `analysis_train`
- `analysis_validation`
- `analysis_test`

をformula単位で分ける。

同一formulaのnetwork違い、node activity違い、prefix違いがsplitをまたいでリークしないようにする。

公式splitがこの条件を満たすなら可能な限り公式splitをそのまま使う。

## 9.4 Fixed analysis panel

MCTS、DecoderLens rollout、ablation後のformula生成、activation patching等の高価な解析には固定panelを用いる。

validation panelは結果を見る前に、system / formula familyで層別化した上でID順または固定seedで機械的に選択する。

成功例だけを後から選ばない。

---



# 10. 評価指標



## 10.1 ND² reproduction metrics

- recovered formula
- exact recovery
- canonical exact
- skeleton recovery
- symbolic equivalence
- `ted_raw`
- `ted_skeleton`
- fit error
- formula length / complexity
- valid rate
- search success rate
- MCTS iterations / nodes / candidate count
- wall time
- timeout rate

公式論文のmetricが別に定義されている場合は、その公式metricも同時に保存する。

## 10.2 Policy-level metrics

- cross entropy
- top-1 accuracy
- top-k accuracy
- ground-truth symbol rank
- ground-truth symbol probability / logit
- policy entropy



## 10.3 Layer intervention metrics

各layer `l`についてbaselineとの差を保存する。

- `delta_ce`
- `delta_top1`
- `delta_correct_symbol_probability`
- `delta_correct_symbol_rank`
- `delta_policy_entropy`
- `delta_ted_raw`
- `delta_ted_skeleton`
- `delta_exact`
- `delta_skeleton`
- `delta_fit_error`
- `delta_search_success`



## 10.4 Fine-tuning efficiency

- trainable parameter count
- trainable parameter ratio
- peak GPU memory
- training wall time
- inference / search wall time

---



# 11. 数式canonicalizationとTED

各formulaについて次を保存する。

1. `raw_expr`
2. `parsed_expr`
3. `canonical_expr`
4. `skeleton_expr`
5. `expression_tree`

ND²固有のnetwork dynamical operatorsは、公式semanticsを保持したtree nodeとして扱うことを原則とする。
勝手に巨大なscalar expressionへ展開しない。

TED評価前に、

- commutative operator
- associative operator
- constants
- signs
- variable labels
- network dynamical operator

の扱いをvalidation前に固定する。

### 11.1 `ted_raw`

canonical expression tree間の通常TED。

### 11.2 `ted_skeleton`

数値定数をplaceholder化したexpression tree間のTED。

### 11.3 `ted_variable_aware`

Akutsu et al.の変数付きTEDに近い評価。

計算量が大きい場合、testを見る前に固定したsubsetへ限定する。
全件実行できない場合は`ted_raw` / `ted_skeleton`を主結果とする。

TED変換に失敗したrecordは除外せず、`TEDParseError`等を保存する。

---



# 12. Phase構成



## Phase 0: Environment / upstream freeze / preflight

目的: **公式ND²を再現可能な状態で固定する。**

実施:

- LANSR commit固定
- ND² upstream commit固定
- checkpoint / data checksum
- Python / PyTorch / CUDA / GPU確認
- official config読み込み
- NDformer architecture inventory
- symbol vocabulary確認
- network dynamical operators確認
- formula parser / evaluator smoke
- MCTS smoke
- output schema / resume / failure保存確認

Go条件:

- checkpointがarchitecture mismatchなくloadできる
- official sampleでforward可能
- policy shape / symbol setが一致
- small MCTSがvalid formulaを生成できる

---



## Phase 1: NDformer policy reproduction

目的: **NDformer単体の公式挙動を再現する。**

実施:

- official validation dataでteacher-forcing評価
- CE
- top-1 / top-k accuracy
- true symbol rank
- true symbol probability
- policy entropy
- prefix長別performance
- formula length / operator別performance

保存:

- problem / formula / prefix単位のpolicy output
- aggregate metrics
- failure

このPhaseは層解析前の単なるsmokeではなく、NDformer reproductionの正式なbaselineとする。

---



## Phase 2: ND² full-pipeline reproduction

目的: **NDformer-guided MCTSを含むND²の公式数式発見pipelineを再現する。**

実施:

- network dynamical operatorによるformula表現
- NDformer-guided MCTS
- reward evaluation
- constant optimization
- Pareto front
- final formula selection

最初にsmall configurationで全pipelineを検証し、その後公式または公式に近いbudgetへ拡張する。

最低保存:

- true formula
- all / top candidate formulas
- final formula
- fit error
- exact / skeleton / symbolic equivalence
- TED
- complexity
- MCTS iterations
- candidate count
- wall time
- failure

---



## Phase 3: ND² synthetic benchmark reproduction

目的: **ND²論文のsynthetic systemsに対するformula recoveryを再現する。**

対象は原則10 systems。

各systemについて複数seed / network条件が公式に存在する場合は、公式条件を優先する。

報告:

- system別formula recovery
- exact / symbolic equivalence
- TED
- fit error
- valid rate
- search cost
- wall time

可能であれば公式論文のaggregateと並べる。

### Optional reproduction ablation

計算資源が許す場合、NDformer-guided MCTSとuniform / unguided MCTSを比較し、NDformer guidanceのsearch accelerationを確認する。

これは層解析とは別に **ND²再現側の成果** とする。

Phase 1–3をもって主目的A「ND²再現」の主要部分完了とする。

---



## Phase 4: Layer-analysis corpus / probe / gradient / CKA

目的: **NDformer各層にどの情報が表現されているかを記述的に解析する。**

### 4A. Hidden-state extraction

全encoder / decoder blockについてhidden stateを保存する。

### 4B. Linear probe

GPU_RUN2と同様に各層へ共通capacityのprobeを学習する。

主task候補:

- next symbol classification
- root operator classification
- operator count
- formula tree depth
- formula tree size
- network dynamical operator count
- formula family / template ID（安定して定義可能な場合）

random-label controlまたはcontrol taskを可能な範囲で入れる。

### 4C. Gradient norm

固定validation batchについて各層の

- raw gradient norm
- parameter-count-normalized gradient norm
- seed rank

を保存する。

### 4D. CKA

比較:

- adjacent layers
- early / middle / late encoder
- early / middle / late decoder
- encoder最終表現 vs 各中間層
- successful recovery vs failed recovery

Phase 4のprobe結果を高価な介入候補の絞り込みへ使うが、probeのみで重要層を結論しない。

---



## Phase 5: DecoderLens / intermediate decoding

目的: **正解数式に必要な情報がdepthに沿ってどのように形成されるかを見る。**

### 5A. Encoder-side DecoderLens型解析

各encoder中間層のmemoryを通常decoderへ渡し、可能ならformulaをrolloutする。

保存:

- top-k symbol
- true symbol rank / probability
- provisional prefix
- raw formula
- canonical formula
- parse success
- exact
- skeleton
- symbolic equivalence
- TED

特に、

`encoder layer -> final formula TED`

のtrajectoryをproblem単位で保存する。

### 5B. Decoder-side intermediate analysis

各decoder層のhidden stateへfinal policy headを適用できる場合、logit-lens型解析を行う。

保存:

- top-k symbol
- true symbol rank
- true symbol probability
- policy entropy

安全にfull rolloutできる場合のみformula / TEDまで評価する。

---



## Phase 6: Causal layer analysis

目的: **GPU_RUN3層解析の中心。probeで見えた情報と因果的重要性を区別する。**

### 6A. IOLE single-layer fine-tuning

全候補Transformer blockについて、1層だけtrainableにする。

比較:

- frozen
- each single encoder layer
- each single decoder layer
- full FT

同じdata / optimizer candidate budget / seedを使用する。

保存:

- CE
- policy metrics
- exact / skeleton / symbolic equivalence
- TED
- trainable parameter count
- memory
- wall time



### 6B. Layer ablation

各Transformer blockを1層ずつablateする。

pre-norm / post-norm / residual構造を確認し、tensor shapeを保つ方法をvalidationで固定する。

主効果:

- ΔCE
- Δtrue-symbol probability
- ΔTED
- Δexact / skeleton
- ΔMCTS search success



### 6C. Activation intervention

GPU_RUN2と同様に、まず単純で再現性の高い介入を主とする。

- zero ablation
- mean ablation
- matched-control activation replacement



### 6D. Activation patching

可能であればsource / target problem pairを事前生成する。

pair例:

- root operatorだけ違う
- one operatorだけ違う
- network dynamical operatorの有無だけ違う
- tree depthだけ違う

patch後の

- target true-symbol probability
- source symbol probability
- final TED
- exact / skeleton

を測定する。

### 6E. Parameter update sensitivity

controlled full FTにおける各層の

- `||Delta theta_l||_2`
- `||Delta theta_l||_2 / ||theta_l||_2`

を保存する。

Phase 6終了時点でprobe / gradient / CKA / DecoderLens / IOLE / ablation / interventionを横断比較する。

---



## Phase 7: Layer ranking / selective fine-tuning

目的: **層解析の知見が実際のfine-tuning効率へ使えるか検証する。**

### 7A. Layer ranking

validationだけを用いて最終rankingを固定する。

最低比較:

- probe rank vs IOLE rank
- probe rank vs ablation rank
- probe rank vs intervention rank
- gradient rank vs update sensitivity rank
- DecoderLens rank vs intervention rank

seedごとに

- Spearman
- Kendall
- top-k overlap

を保存する。

### 7B. 主比較条件

- `frozen`
- `full`
- `top 1`
- `top 3`
- `random 3`

`top`はtestを見る前に固定する。

random 3は固定seedで一度だけ抽出し、manifestへ保存する。

### 7C. 評価

- policy CE
- top-k accuracy
- exact
- skeleton
- symbolic equivalence
- TED
- fit error
- trainable parameter count
- peak memory
- training time



### 7D. ND² full-search evaluation

selective FT後のcheckpointをNDformer-guided MCTSへ戻し、

- frozen
- full
- top 1
- top 3
- random 3

で最終formula recoveryを比較する。

これにより、policy-level改善がND²全体のformula discoveryへつながるか確認する。

---



## Phase 8: Final test / integrated analysis

Phase 4–7で方法・layer・hyperparameterを固定した後、analysis-testを一度だけ評価する。

主結果を二本立てでまとめる。

### Result A: ND² reproduction

- 公式NDformer policy reproduction
- synthetic system formula recovery
- MCTS search performance
- official resultとの比較



### Result B: NDformer layer analysis

- layer-wise probe
- CKA
- DecoderLens
- IOLE
- ablation
- activation intervention
- ranking stability
- selective FT
- TED trajectory

最後に両者を接続し、

> どの層がND²の最終的なformula discoveryを支えているか

をまとめる。

---



## Phase 9: Optional pretraining-distribution analysis

RQ1–RQ7完了後、余力があれば実施する。

各analysis formula `f`について、可能なら

```math
d_{\mathrm{pretrain}}(f)
= \min_{g \in D_{\mathrm{pretrain}}} \mathrm{TED}(f,g)
```

を評価する。

100万式との全pair TEDが困難な場合は、

1. canonical / skeleton hash
2. root operator
3. tree size
4. operator histogram

等でcandidateを絞ってからTEDを計算する。

近似検索なら`nearest_ted`ではなく`retrieved_nearest_ted`等と明記する。

これと

- probe score
- ablation effect
- intervention effect
- final formula TED

との関係を見る。

---



# 13. ND²再現の成功条件

ND²再現は「codeが動いた」だけでは成功としない。

最低条件:

1. official checkpoint / config / symbol vocabularyが整合する
2. official validation dataでpolicy predictionを再現できる
3. NDformer-guided MCTSが公式semanticsのformulaを生成する
4. synthetic benchmarkでground-truth formulaへ到達する例を複数確認できる
5. 全systemについて成功 / 失敗をproblem単位で保存する
6. official resultと大きく異なる場合、その差を明示し原因を調査する

論文値と完全一致しない場合でも、hardware、randomness、budget、version差等を記録した上で、再現できた範囲を正確に報告する。

---



# 14. 層解析の成功条件

層解析は「top layerを1個見つけた」だけでは成功としない。

最低条件:

1. encoder / decoder全層に対してprobeを実行
2. gradient normとCKAを保存
3. encoderへDecoderLens型解析を実施可能な範囲で実装
4. 全候補層でIOLE single-layer FT
5. 全候補層でablation
6. 固定panelでactivation intervention
7. layer rankのseed安定性を評価
8. `top 1 / top 3 / random 3 / full / frozen`を比較
9. policy-levelだけでなくND² MCTSのformula-levelでも検証
10. exact / skeleton / symbolic equivalence / TEDを併記

probeと介入の順位が一致しない場合も、重要な結果としてそのまま報告する。

---



# 15. 統計設計



## 15.1 Seed

seed数はPhase 0–3のwall timeを測定後、testを見る前に固定する。

可能なら主要policy / layer-analysis結果は最低3 seeds以上とする。
MCTS full reproductionでseed数が少なくなる場合は表ごとに`n`を明記する。

## 15.2 Paired comparison

同一problem / seedをpairedにして条件差を計算する。

報告:

- mean
- median
- standard deviation
- paired difference
- 95% CI

少数seedのCIにはStudentのt分布を用いる。

## 15.3 Rank stability

- Spearman
- Kendall
- top-k overlap

をseed間で保存する。

## 15.4 Multiple comparisons

全layer個別検定を行う場合は多重比較を考慮する。

ただし重要層判定をp値だけに依存させず、

- effect size
- rank stability
- 複数解析法間の一致

を重視する。

---



# 16. Timeout / failure / resume



## 16.1 Timeout

次を別に設定する。

- policy forward timeout
- formula rollout timeout
- MCTS timeout
- constant optimization timeout
- TED timeout

具体値はsmokeの実測後、test前に固定する。

## 16.2 Failure reasons

最低限:

- `CheckpointLoadError`
- `ArchitectureMismatch`
- `InvalidPrefix`
- `InvalidSymbol`
- `ParseError`
- `MCTSTimeout`
- `ConstantOptimizationFailure`
- `NaN`
- `Inf`
- `TEDParseError`
- `TEDTimeout`
- `ActivationHookError`
- `ActivationPatchError`
- `OOM`

を区別する。

## 16.3 Resume単位

- ND² reproduction: seed × system × problem
- probe: seed × layer × task
- CKA: seed × layer pair
- DecoderLens: seed × encoder layer × problem
- IOLE: seed × layer
- ablation: seed × layer × problem
- intervention: seed × layer × problem
- selective FT: seed × condition
- MCTS after FT: seed × condition × problem

完了済みrecordをresumeで再計算しない。

---



# 17. 保存schema



## 17.1 Provenance

- `run_id`
- `campaign = GPU_RUN3`
- `source_commit`
- `nd2_upstream_commit`
- `checkpoint_sha256`
- `dataset_fingerprint`
- `config_fingerprint`
- `seed`
- `hardware`
- `software_versions`



## 17.2 Problem

- `problem_id`
- `system_name`
- `formula_id`
- `split`
- `network_id`
- `network_family`
- `true_formula_raw`
- `true_formula_canonical`
- `true_formula_skeleton`
- `true_expression_tree`



## 17.3 Prediction / search

- `condition`
- `prefix`
- `policy_logits`
- `topk_symbols`
- `candidate_formulas`
- `pred_formula_raw`
- `pred_formula_canonical`
- `pred_formula_skeleton`
- `fit_error`
- `exact`
- `skeleton`
- `symbolic_equivalent`
- `ted_raw`
- `ted_skeleton`
- `complexity`
- `valid`
- `failure_reason`
- `search_nodes`
- `candidate_count`
- `wall_time`



## 17.4 Layer analysis

- `module_name`
- `layer_index`
- `analysis_type`
- `probe_task`
- `probe_score`
- `gradient_norm`
- `cka`
- `decoderlens_true_symbol_rank`
- `decoderlens_true_symbol_probability`
- `ablation_delta_ce`
- `ablation_delta_ted`
- `intervention_delta_probability`
- `intervention_delta_ted`
- `update_norm`
- `io_le_score`

---



# 18. 主成果物

GPU_RUN3終了時に最低限次を作成する。

## 18.1 ND² reproduction report

- environment / provenance
- official asset一覧
- NDformer policy reproduction
- synthetic benchmark reproduction
- system別true / predicted formula表
- exact / TED / fit error
- MCTS cost
- failure一覧
- official paperとの比較



## 18.2 NDformer layer-analysis report

- architecture map
- probe heatmap
- gradient norm
- CKA matrix
- DecoderLens trajectories
- layer-wise IOLE
- ablation effect
- activation intervention effect
- layer rank stability
- top / random / full FT
- MCTS formula recovery after FT



## 18.3 問題単位formula比較表

最低限:


| problem | system | condition | true formula | predicted formula | exact | skeleton | symbolic eq. | TED | fit error | valid/failure |
| ------- | ------ | --------- | ------------ | ----------------- | ----- | -------- | ------------ | --- | --------- | ------------- |


成功例だけでなく、近似成功、構造誤り、invalid、timeoutも残す。

## 18.4 Layer summary table


| layer | probe rank | gradient rank | DecoderLens rank | IOLE rank | ablation rank | intervention rank | final consensus |
| ----- | ---------- | ------------- | ---------------- | --------- | ------------- | ----------------- | --------------- |


「consensus」はtest結果から決めず、validationで事前固定した規則による。

---



# 19. Go / No-Go



## Go 1: NDformer reproduction

- official checkpoint load成功
- policy forward成功
- official vocabulary / grammar一致

失敗する場合、層解析へ進まない。

## Go 2: ND² search reproduction

- MCTSがNDformer policyを使用
- valid formula生成
- reward / constant optimization / Pareto frontが動作

失敗する場合、ND² full-search reproductionを修正してからPhase 3へ進む。

## Go 3: Synthetic benchmark

- 複数systemでground-truthに近いformulaを生成できる
- formula-level outputとfailureを保存できる

大きく公式結果から乖離する場合、原因を未解決のまま層解析の最終結論へ進まない。

## Go 4: Layer hooks

- 全encoder / decoder層のhidden stateを取得可能
- intervention前後でbaselineが再現
- hookを外すと元のpredictionへ戻る



## Go 5: Final test

- layer ranking frozen
- selective FT条件 frozen
- activation設定 frozen
- MCTS budget frozen
- TED definition frozen

ここまで固定してからanalysis-testを一度だけ評価する。

---



# 20. GPU_RUN3で扱わないもの

GPU_RUN3を二大目標へ集中させるため、次は原則として扱わない。

- DREAM4
- ヒト遺伝子発現時系列
- GeneNetWeaver専用benchmarkの新規設計
- empirical regulator selection
- 有限差分による実データ微分推定
- 新規GRN候補式の提案
- PySRとの大規模benchmark
- TPSR / NSR-gvs / NeSymReS系search比較
- CTC_NSRの独立した再現バイアス実験
- NSRS-pretrainedモデルとの本格比較

ND² synthetic benchmark中のgene regulatory systemは、あくまでND²の10 systemsの一つとして扱う。

---



# 21. 最終的な研究上の位置づけ

GPU_RUN3は次の二つを同時に達成することを狙う。

### 1. Reproduction

**ND²という最新のneural symbolic regressionによるnetwork dynamics discovery手法を、公開資産から再現し、その成功条件・失敗条件・計算コストを整理する。**

### 2. Interpretation

**その中核モデルNDformerについて、数式情報がTransformerのどの層に形成され、どの層が最終的なformula discoveryを支えるかを、probe・表現類似度・fine-tuning・ablation・activation intervention・TEDを組み合わせて解析する。**

したがってGPU_RUN3の最終的な主張は、

> **ND²を再現した上で、その内部のNDformerを層別に解析し、network dynamicsの数式発見を支えるTransformer内部機構を明らかにする。**

という形を目指す。