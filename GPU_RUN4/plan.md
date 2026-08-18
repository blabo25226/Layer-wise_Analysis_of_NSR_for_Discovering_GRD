# GPU_RUN4 計画

作成日: 2026-08-18  
状態: Draft v0.2（別観点レビュー反映版）

## 方針

GPU_RUN4は、次の **二大目標を同格の主目的** とする。

1. **公開済みODEFormerを、原論文・公式実装・公開checkpoint・ODEBenchに基づいて再現する。**
2. **再現したODEFormerのTransformerを、encoder / decoder全層にわたって体系的に層解析する。**

再現では単に「ODEのtrajectoryへよくfitする」ことだけを目標にしない。GPU_RUN4では、ODEFormer論文が重視する
**reconstruction / generalization** を再現した上で、LANSR独自に **symbolic recovery** を詳細に測り、
正しい数式構造へどこまで到達したかを評価する。

層解析では、GPU_RUN2 / GPU_RUN3で整備した考え方を引き継ぎ、

- linear probe
- gradient norm
- CKA
- encoder intermediate decoding（DecoderLens型）
- decoder-side intermediate readout / logit-lens型解析
- single-layer fine-tuning（IOLE条件）
- layer ablation
- activation intervention / activation patching
- parameter update sensitivity
- selective fine-tuning

をODEFormerへ移植する。

ODEFormer原論文の最終モデルは **4 encoder layers + 16 decoder layers** の非対称なencoder-decoder Transformerである。
したがってGPU_RUN4では20個のTransformer blockを主解析対象とし、特に16層あるdecoderで、
**数式構造、演算子、変数、数値定数に関する情報が深さに沿ってどのように形成されるか** を中心的に調べる。

---

# 1. 目的と範囲

## 1.1 主目的A: ODEFormerの再現

Stéphane d’Ascoli et al., “ODEFormer: Symbolic Regression of Dynamical Systems with Transformers,” ICLR 2024で提案された
ODEFormerについて、公式code、公開pretrained model、ODEBench、公式evaluation protocolを可能な限りそのまま利用し、
論文で報告された主要な挙動を再現する。

再現対象は少なくとも次を含む。

1. 公開checkpointのloadとforward / beam sampling
2. trajectoryから直接ODEを生成するend-to-end inference
3. ODEBenchでのreconstruction
4. ODEBenchでのnew initial conditionへのgeneralization
5. noise / irregular subsamplingへのrobustness
6. Strogatz benchmarkでの副次的再現
7. beamから生成された全候補式の保存
8. 真式と予測式のsymbolic recovery評価
9. ODEFormerと`ODEFormer (opt)`の分離比較
10. wall time、candidate数、integration failure等の保存

GPU_RUN4では約50M synthetic examplesを用いた事前学習そのものの完全再実行は主目的にしない。
原論文では事前学習に単一A100 80GBで約3日を要しており、公開pretrained modelが提供されているため、
**公開checkpointからのinference reproductionを主たる再現対象** とする。

事前学習distributionのgeneratorは、層解析用の独立synthetic corpusを生成する目的で再利用する。

## 1.2 主目的B: ODEFormerの層解析

ODEFormerについて、encoder / decoder各層がtrajectoryからsymbolic ODEを生成するとき、
どの情報を表現し、どの程度最終出力へ因果的に寄与するかを解析する。

特に次を区別する。

- probeで情報が **readout可能** であること
- CKAでrepresentationが **類似** していること
- gradient normが大きくlossへ **感度を持つ** こと
- single-layer FTでその層が **適応能力を持つ** こと
- ablationでその層が **必要** であること
- activation interventionでその層のrepresentationが出力へ **因果的影響を持つ** こと

これらを一つの「層重要度」として混同せず、それぞれのlayer rankingと一致度を比較する。

## 1.3 GPU_RUN4の中心的な問い

> **A. 公開ODEFormerは、原論文のODE benchmarkに対してtrajectoryだけでなく真のODE数式をどの程度回復できるか。**

> **B. ODEFormerの4 encoder + 16 decoder層では、数式に必要な情報がどの層で形成され、どの層が最終的なsymbolic recoveryに因果的に寄与するか。**

さらに両者を接続して、

> **層解析で重要と判断された層だけをfine-tuningまたは介入したとき、最終的なODEの数式回復とdynamical generalizationは実際に変化するか。**

まで確認する。

## 1.4 GPU_RUN4で主対象にしないもの

研究質問をODEFormer再現と層解析へ集中させるため、次は主実験から外す。

- 約50M examplesを用いたpretrainingの完全な再実行
- 原論文に含まれる全baseline手法の再実装・全比較
- DREAM4 / ヒト遺伝子発現時系列への適用
- 新規GRN候補式の生物学的主張
- 6次元を超えるODEへのarchitecture拡張
- multi-trajectory入力へmodel自体を改造する研究
- ground truthを用いるstructural oracleを実用的selection methodとして使うこと

これらは必要に応じてGPU_RUN5以降または別campaignへ回す。

---

# 2. ODEFormer原論文から固定する重要事項

## 2.1 問題設定

ODEFormerは、通常のfunctional symbolic regressionのように
$`(x,\dot{x})`$ を入力するのではなく、1本の観測trajectory

```math
\{(t_i,\mathbf{x}(t_i))\}_{i=1}^{N}
```

から直接

```math
\dot{\mathbf{x}}=\mathbf{f}(\mathbf{x})
```

をsymbolic formで推定する。

したがってODEFormer本体の推論では有限差分で $`\dot{x}`$ を作らない。
GPU_RUN4ではこのend-to-end設定を維持する。

## 2.2 事前学習distribution

原論文のgeneratorでは、各ODE componentをrandom unary-binary expression treeとして生成する。
主な設定は次のとおりである。

- system dimension: $`D\le 6`$
- binary operators: `+`, `*`
- binary operator数: 最大5
- unary operators: `sin(x)`, `x^-1`, `x^2`
- unary operator数: 最大3
- subtraction: 負の係数を用いた加算として表現
- division: reciprocalを用いた乗算として表現
- constants: log-uniform `[0.05, 20]`
- initial condition: standard normal
- integration interval: `[1, 10]`
- observations: 50–200 points
- solver: SciPy `solve_ivp`の既定RK45
- divergence filter: state magnitudeが100を超えたexampleを除外
- rapidly convergent trajectoryの大部分を確率的に除外
- multiplicative Gaussian noiseを付加
- uniform random subsamplingを付加

training corruptionは

- noise level $`\sigma\sim U(0,0.1)`$
- subsampling ratio $`\rho\sim U(0,0.5)`$

である。

このdistributionを再現用benchmarkそのものには使用せず、主としてlayer-analysis corpus生成に利用する。

## 2.3 モデルarchitecture

原論文の最終モデルは次を持つ。

- encoder-decoder Transformer
- total parameters: 約86M
- embedding dimension: 512
- attention heads: 16
- encoder layers: 4
- decoder layers: 16
- encoder positional embedding: なし
- symbolic output: prefix notation
- multidimensional ODE component separator: `|`

数値は4 significant digitsへ丸め、sign / mantissa / exponentの3 tokenへ分解する。

**重要:** 公式repositoryのargument parserには論文checkpointと異なるdefault値が含まれる可能性がある。
調査時点のsourceでは、例えばdecoder layer数やembedding dimensionのparser defaultが論文記載値と一致しない。
したがってGPU_RUN4では **parser defaultをarchitectureの根拠にせず、公開checkpointの実model object / state dictと論文Tableを照合する。**

architecture mismatchがある場合はfail-fastし、どのversionを再現しているかを確定してから長時間runへ進む。

## 2.4 推論

原論文の標準推論はbeam searchではなく **beam sampling** を用いる。
標準設定は、原則として

- beam size: 50
- beam temperature: 0.1

を使用し、候補の中から **observed trajectoryのreconstruction $`R^2`$ が最大の式** を選ぶ。

公式wrapperは入力trajectoryの点順序をrandom permutationしてからmodelへ渡すため、
GPU_RUN4ではNumPyを含むpermutation seedを明示的に保存し、paired comparisonでは同じpermutationを共有する。

## 2.5 `ODEFormer (opt)`

原論文では通常のODEFormerとは別に、生成後の式の数値定数をBFGSで追加最適化する`ODEFormer (opt)`を評価している。

GPU_RUN4では

- `ODEFormer`: transformerが直接生成した式
- `ODEFormer (opt)`: post-hoc constant optimization後の式

を別conditionとして保存し、混ぜて集計しない。

## 2.6 ReconstructionとGeneralization

ODEFormer論文は次の二つを明確に区別する。

### Reconstruction

観測時と同じinitial conditionから予測ODEを積分し、clean dense ground-truth trajectoryと比較する。

### Generalization

異なるinitial conditionからground-truth ODEと予測ODEを積分し、未観測trajectory上で比較する。

GPU_RUN4でもこの区別を維持する。
特に、reconstructionが良くてもgeneralizationが悪ければ真のdynamicsを同定したとは扱わない。

---

# 3. 研究質問

## RQ1: 原論文再現

**RQ1. 公開pretrained ODEFormerは、ODEBench / Strogatzにおけるreconstruction、generalization、noise / subsampling robustnessをどの程度再現できるか。**

主指標:

- reconstruction $`R^2`$
- generalization $`R^2`$
- accuracy `$R^2 > 0.9$`
- complexity
- inference time
- integration success rate

## RQ2: Symbolic recovery

**RQ2. trajectory predictionが良いODEFormerの出力は、真のODE数式をどの程度正しく回復しているか。**

主指標:

- raw prefix exact
- canonical exact
- skeleton recovery
- symbolic equivalence
- TED
- variable recovery
- coefficient error（skeletonが一致した場合）

component単位とsystem全体の両方で評価する。

## RQ3: Candidate generationとcandidate selection

**RQ3. 正しい式をbeam内には生成しているが、reconstruction $`R^2`$ によるselectionで取り逃がしているケースはどの程度あるか。**

各beamについて、

- official-selected candidate
- beam内のunique skeleton数
- true skeletonがbeam内に存在するか
- true / best-symbolic candidateのbeam rank
- structural oracle best candidate

を保存する。

`structural oracle`はground truthを用いるため **診断専用** とし、最終性能として報告するprediction selectionには絶対に使わない。
これにより、

- generation failure
- ranking / selection failure

を区別する。

## RQ4: 層ごとの情報表現

**RQ4. encoder / decoder各層には、ODE数式のdimension、operator、variable、tree structure、next token、numeric constantに関するどの情報が表現されているか。**

主手法:

- linear probe
- gradient norm
- CKA
- encoder intermediate decoding
- decoder-side intermediate readout

## RQ5: 因果的な層寄与

**RQ5. probeで情報が読み出せる層は、ablation / activation interventionでも最終tokenやODE構造へ大きな因果効果を持つか。**

主手法:

- block ablation / bypass
- zero / mean activation intervention
- matched activation replacement
- activation patching
- single-layer FT

## RQ6: 数式構造はdecoder 16層でどう形成されるか

**RQ6. decoder depthに沿って、正解operator・variable・constant tokenと正解expression treeへの距離はどのように変化するか。**

特に、

- early decoder
- middle decoder
- late decoder

で役割が分化するかを調べる。

## RQ7: 少数層fine-tuning

**RQ7. 重要層1–3層だけのfine-tuningで、full fine-tuningに近いsymbolic recovery / generalization改善を得られるか。またtop層はrandom層より有効か。**

## RQ8: 難易度依存性

**RQ8. 層重要度とsymbolic recoveryは、dimension、式複雑度、noise、subsamplingによって変化するか。**

---

# 4. 参照資料

## 4.1 ODEFormer

主参照:

- Stéphane d’Ascoli, Sören Becker, Alexander Mathis, Philippe Schwaller, Niki Kilbertus, “ODEFormer: Symbolic Regression of Dynamical Systems with Transformers,” ICLR 2024 / arXiv:2310.05573
- official repository: `sdascoli/odeformer`
- official pretrained model
- ODEBench

GPU_RUN4では論文本文、appendix、公式source、checkpointを一次資料とする。

## 4.2 層解析

GPU_RUN2 / GPU_RUN3で採用した次の文献・設計を継承する。

- DecoderLens
- CKA
- Designing and Interpreting Probes with Control Tasks
- IOLE
- activation patching best-practice literature
- Tree Edit Distance with Variables

ただしODEFormerのarchitectureに合わせてhook位置やtaskを再設計し、NeSymReS / NDformerのmodule名をそのまま移植しない。

---

# 5. 研究上の絶対条件

## 5.1 Upstream reproductionとLANSR解析runを分ける

次を別runとして保存する。

- `upstream_reproduction`
- `layer_analysis`
- `fine_tuning_analysis`

公式再現runにLANSR独自hookや改変を混ぜない。

## 5.2 ODEBenchをfine-tuning corpusにしない

ODEBench / Strogatzは再現・外部評価benchmarkとして保持し、layer rankingやfine-tuningのtraining dataへ使用しない。

層解析・single-layer FTにはODEFormer公式generatorから独立生成したsynthetic corpusを使用する。

## 5.3 Validation / test分離

- probe hyperparameter: validationのみ
- layer ranking: validationのみ
- intervention方式: validationのみ
- selective FT hyperparameter: validationのみ
- random layer set: testを見る前に固定
- test: 全設定固定後に一度だけ評価

## 5.4 Failureを隠さない

以下を除外して成功例だけ平均しない。

- invalid prefix
- parse failure
- candidate integration failure
- generalization integration failure
- BFGS failure
- NaN / Inf
- timeout
- symbolic equivalence timeout
- TED failure
- hook failure
- OOM

valid rateとfailure reasonを保存する。

## 5.5 数値fitと数式回復を区別する

低いtrajectory errorや高いreconstruction $`R^2`$ だけからsymbolic recovery成功を主張しない。

必ず

- reconstruction
- generalization
- symbolic recovery
- complexity
- validity

を別に報告する。

## 5.6 相関的解析と介入的解析を区別する

- probe / gradient / CKA / lens: 観察的
- ablation / intervention / patching: 介入的
- single-layer FT: 適応能力

と解釈する。

---

# 6. Upstream / environment / architecture inventory

Phase 0で最低限次を保存する。

- LANSR repository commit
- ODEFormer upstream URL / branch / commit
- checkpoint SHA256
- ODEBench checksum / fingerprint
- Python version
- PyTorch version
- SciPy version
- scikit-learn version
- CUDA version
- GPU / CPU / RAM / OS
- beam size / temperature
- candidate selection metric
- rescaling on/off
- `ODEFormer (opt)` on/off
- ODE solver settings
- all random seeds

## 6.1 Architecture inventory

checkpointからmachine-readableに次を抽出する。

- total parameter count
- embedding dimension
- attention head count
- encoder layer count
- decoder layer count
- each module name
- parameter count by block
- hidden input / output shape
- normalization位置
- self-attention位置
- cross-attention位置
- FFN位置
- final projection / tied embeddingの有無
- trainable status

原論文の **4 encoder + 16 decoder / dim 512 / 16 heads / 約86M** と照合する。

主layer ranking対象はTransformer blockだけとする。

次はcontrolとして別扱いする。

- numerical embedder
- encoder input projection
- final projection / output head
- embedding layer
- normalization only module

---

# 7. データ

## 7.1 Reproduction Track A: ODEBench

ODEBench 63 systemsを主benchmarkとする。

内訳:

- 1D: 23
- 2D: 28
- 3D: 10
- 4D: 2

各ODEにはreconstruction用initial conditionとgeneralization用の別initial conditionを使用する。
公式dataset / official evaluation codeのtrajectoryを優先し、独自にparameterを変更しない。

### corruption grid

原論文Figure 4と同じ範囲を基本とする。

- $`\sigma\in\{0,0.01,0.02,0.03,0.04,0.05\}`$
- $`\rho\in\{0,0.5\}`$

実行前にofficial evaluation scriptと照合し、異なる場合はofficial codeを優先してplanを更新する。

corruption random seedを保存し、全conditionでpairedにする。

## 7.2 Reproduction Track B: Strogatz

7 unique 2D systems × official initial conditionsを副benchmarkとして使用する。

ODEBenchを主結果、Strogatzをsecondary reproductionとする。

## 7.3 Representative qualitative panel

原論文Figure 1相当の代表ODEを固定panelにする。

- Language death
- Landau
- Lotka–Volterra
- Duffing
- Maxwell–Bloch
- Lorenz periodic regime
- Binocular rivalry with adaptation
- SEIR

原論文に合わせ、5% noise + 50% subsamplingの条件を再現する。

各problemで

- observed points
- ground-truth trajectory
- predicted trajectory
- true ODE
- selected ODE
- beam candidate formulas

を保存する。

## 7.4 Layer-analysis synthetic corpus

ODEFormer公式generatorを使って、pretraining distributionに準拠した独立corpusを生成する。

最低限、

- `analysis_train`
- `analysis_validation`
- `analysis_test`

へ式単位で分割する。

同一canonical formula / skeletonがsplitをまたぐかをhashで監査し、
structure-generalizationを測るanalysisではskeleton leakageを防ぐ。

exact sample数はPhase 0–2でthroughputを測定後、testを見る前に固定する。
初期目安は、

- train: 20,000 formulas
- validation: 5,000 formulas
- test: 5,000 formulas

とするが、これはprovisionalであり、本実験開始前にwall time / storage / GPU memoryに基づき確定する。

## 7.5 Fixed intervention panel

DecoderLens型rollout、ablation、activation patching等の高価な解析には固定panelを使う。

- dimension
- complexity
- unary operator presence
- binary operator count
- noise
- subsampling

で層別化し、ID順またはfixed seedで機械的に抽出する。

成功例を後から恣意的に選ばない。

---

# 8. 評価指標

## 8.1 原論文互換metric

### Reconstruction

- $`R^2_{\mathrm{recon}}`$
- accuracy: `$R^2_{\mathrm{recon}}>0.9$` の割合

### Generalization

- $`R^2_{\mathrm{gen}}`$
- accuracy: `$R^2_{\mathrm{gen}}>0.9$` の割合

### その他

- expression complexity
- inference time
- integration success rate

原論文と比較する表では、まず原論文metricを優先する。

## 8.2 Symbolic recovery

各componentとODE system全体について次を保存する。

- `raw_prefix_exact`
- `canonical_exact`
- `skeleton_exact`
- `symbolic_equivalent`
- `ted_raw`
- `ted_skeleton`
- `normalized_ted`
- variable precision / recall / F1
- complexity

system-level exactは **全componentが成功した場合のみ1** とする。
component-level metricも併記する。

## 8.3 Constant accuracy

skeletonが一致したpredictionについて、対応付け可能な定数に対して

- absolute error
- relative error

を保存する。

`ODEFormer`と`ODEFormer (opt)`でconstant accuracyがどう変化するかを見る。

## 8.4 Beam diagnostics

各beamについて次を保存する。

- candidate count
- valid candidate count
- unique canonical formulas
- unique skeleton count
- selected candidate rank
- true skeleton present / absent
- best symbolic candidate rank
- candidate reconstruction $`R^2`$
- candidate generalization $`R^2`$（ground truthを用いる診断値としてのみ）

これによりcandidate generationとselectionを分解する。

## 8.5 Layer-level token metrics

- cross entropy
- top-1 accuracy
- top-k accuracy
- true token probability
- true token rank
- token entropy

token category別にも集計する。

- operator
- variable
- sign
- mantissa
- exponent
- separator `|`
- EOS

## 8.6 Layer intervention metrics

各layer $`l`$ についてbaselineとの差を保存する。

- `delta_ce`
- `delta_true_token_probability`
- `delta_true_token_rank`
- `delta_symbolic_equivalence`
- `delta_ted`
- `delta_reconstruction_r2`
- `delta_generalization_r2`
- `delta_valid_rate`

---

# 9. 数式canonicalization / symbolic equivalence / TED

ODEFormer論文自身もsymbolic equalityの曖昧さを指摘しているため、GPU_RUN4では評価pipelineを独立に検証する。

各formulaについて最低限次を保存する。

1. model raw prefix
2. parsed tree
3. infix expression
4. canonical expression
5. skeleton expression
6. expression tree

canonicalizationでは、

- commutative operationのchild順
- associative flattening
- subtraction / negative constant
- division / reciprocal
- constant representation
- variable labels
- component separator

の扱いを固定する。

symbolic equivalenceはCAS simplificationだけへ依存せず、必要に応じて安全なdomain上の高精度数値確認を補助的に使う。
CAS timeoutやsingularityがある場合はfailure reasonを保存し、強制的にequivalentへしない。

TEDは少なくとも

- raw canonical tree
- constant-placeholder skeleton tree

で計算する。

`normalized_ted`の正規化式はvalidation pilotで固定し、testを見て変更しない。

---

# 10. 層解析設計

## 10.1 解析対象

主解析対象:

- `encoder_0`–`encoder_3`
- `decoder_0`–`decoder_15`

合計20 blocks。

encoder 4層とdecoder 16層で層数が大きく異なるため、

- global rank
- encoder-only rank
- decoder-only rank

を分けて報告する。

## 10.2 Hidden-state extraction

全raw activationを全datasetについて無制限保存しない。

- probe training用はstreaming / batched extraction
- CKAはfixed panel
- detailed per-token activationはfixed intervention panel
- 保存時は必要に応じて圧縮 / fp16

とし、storage爆発を避ける。

## 10.3 Linear probe

同一capacityのprobeを全層へ適用する。

### Encoder probe候補

trajectoryだけから内部に形成される情報として、

- system dimension
- root operator class
- unary operator presence
- operator histogram
- formula tree depth
- formula size
- variable usage
- clean / noisy condition

を評価する。

### Decoder probe候補

teacher-forcingされたprefix位置について、

- next token
- next token category
- remaining tree depth
- current subtree completion state
- root operator
- total formula complexity

を評価する。

random-label / control taskを入れ、probe capacityそのもののmemorizationと区別する。

## 10.4 Gradient norm

固定validation batchについて、各blockの

- raw gradient norm
- parameter-count-normalized gradient norm
- relative gradient norm

を保存する。

## 10.5 CKA

主に

- encoder内layer間
- decoder内layer間

で計算する。

encoderとdecoderではsequence semantics / lengthが異なるため、raw token matrixを直接比較するcross-module CKAを主結果にしない。
必要ならpooled / aligned representationによる探索的解析として分離する。

比較:

- adjacent layers
- early / middle / late decoder
- successful symbolic recovery vs failure
- clean vs noisy
- low vs high complexity

## 10.6 Encoder intermediate decoding

DecoderLensの考え方を参考に、encoder中間層のrepresentationを通常decoderのmemoryとして使用し、
最終formulaがどう変化するかを見る。

ODEFormer source上で原DecoderLensと同一の前提を満たす場合のみ`DecoderLens`と呼ぶ。
normalization位置等が異なる場合は`encoder_intermediate_decode`として区別する。

保存:

- top-k token
- true token probability / rank
- candidate prefix
- predicted formula
- exact / skeleton / equivalence
- TED
- reconstruction / generalization

## 10.7 Decoder-side intermediate readout

各decoder blockのhidden stateへ最終projectionを適用できる場合、logit-lens型のreadoutを行う。

保存:

- next-token logits
- top-k
- true token rank / probability
- token category accuracy
- entropy

中間層hidden stateはfinal headが想定するdistributionと異なるため、これは観察的解析とする。

可能であっても中間decoder hiddenから無条件にfull rolloutして「その層の生成式」と解釈しない。
full formula評価を行う場合は別のvalidated procedureとして実施する。

---

# 11. 因果的層解析

## 11.1 Layer ablation

ODEFormerのresidual / normalization構造を確認後、tensor shapeを保つablation方法をvalidationで固定する。

候補:

- block bypass
- block-output replacement

zeroingとblock skipを同じablationとして混ぜない。

全20 Transformer blocksについて実施する。

## 11.2 Activation intervention

主介入:

- zero intervention
- mean intervention
- matched-control replacement

介入前後でbaseline outputが同一になるcontrol hookを必ず確認する。

## 11.3 Activation patching

source / target pairを事前生成する。

pair候補:

- dimension同一、root operatorだけ異なる
- skeletonが一演算子だけ異なる
- `sin`の有無だけ異なる
- reciprocalの有無だけ異なる
- variable dependencyだけ異なる
- complexityを揃えた正解 / 不正解pair

patch後に

- source token probability
- target true token probability
- final TED
- symbolic equivalence
- generalization

がどの方向へ変わるかを見る。

単一のpatch結果から層の完全な意味を断定しない。

## 11.4 Parameter update sensitivity

controlled full FTで各blockの

- $`\|\Delta\theta_l\|_2`$
- $`\|\Delta\theta_l\|_2 / \|\theta_l\|_2`$

を保存する。

---

# 12. Single-layer / selective fine-tuning

## 12.1 IOLE条件

全20 Transformer blocksについて、1 blockだけtrainableとし、他をfreezeする。

比較:

- frozen
- each single encoder layer
- each single decoder layer
- full FT

fine-tuning dataにはlayer-analysis synthetic corpusを使い、ODEBench / Strogatzは使わない。

## 12.2 適応条件

pretrained modelが既に公式synthetic distributionを学習しているため、単純な同分布FTでは改善余地が小さい可能性がある。
そのためvalidation pilotで、

- clean synthetic
- corruption-heavy synthetic（例: 5% noise + 50% subsampling）

のどちらを主IOLE taskとするかをtest前に固定する。

設定を選ぶ理由とpilot結果をmanifestへ残す。

## 12.3 Layer ranking

最終top layerはprobe単独で選ばない。

validation上で、主として

- ablation effect
- activation intervention effect
- IOLE adaptation score

のrankを用い、probe / gradient / lensは補助的整合性として見る。

composite rankの正確な定義はtest前に固定する。

## 12.4 Selective FT条件

主比較:

- `frozen`
- `full`
- `top 1`
- `top 3`
- `bottom 3`
- `random 3`

20層あるため、random controlを1集合だけに依存しない。
原則として **事前生成した5個のrandom 3-layer sets** を使用し、top 3とrandom分布を比較する。
計算量が大きい場合も最低3集合とし、実行数はwall-time pilot後、test前に固定する。

追加の解析controlとして、

- best encoder 1
- best decoder 1

を比較してよい。

## 12.5 Fine-tuning efficiency

- trainable parameter count
- trainable parameter ratio
- peak GPU memory
- training wall time
- inference wall time

を保存する。

---

# 13. Phase構成

## Phase 0: Environment / upstream freeze / architecture audit

目的: **ODEFormerを正しいversionで再現できる状態を固定する。**

実施:

- LANSR commit固定
- ODEFormer upstream commit固定
- checkpoint SHA256
- ODEBench fingerprint
- software / hardware記録
- official demo smoke
- architecture inventory
- paper-vs-source-vs-checkpoint差分確認
- beam 50 / temperature 0.1確認
- rescaling確認
- random trajectory permutation確認
- formula parser / integration smoke
- failure / resume schema確認

Go条件:

- checkpoint load成功
- architectureが特定できる
- official demo inference成功
- valid ODE候補を生成できる
- predicted ODEを再積分できる

---

## Phase 1: Evaluation / canonicalization validation

目的: **GPU_RUN4のsymbolic evaluationを本実験前に固定する。**

実施:

- ODEBench true equations parse
- raw prefix / infix / canonical変換
- skeleton変換
- symbolic equivalence tests
- TED tests
- algebraically equivalent gold examples
- reciprocal / negative constant / commutative operator tests
- multi-component separator tests
- timeout / singularity tests

Go条件:

- gold equivalent式が正しく一致
- intentionally different式を誤一致しない
- component orderingが保持される
- failureが理由付き保存される

---

## Phase 2: ODEFormer upstream reproduction

目的: **LANSR改変なしでODEFormerの主要挙動を再現する。**

実施:

1. Figure 1 qualitative panel
2. ODEBench clean
3. ODEBench noise / subsampling grid
4. ODEBench generalization
5. Strogatz secondary reproduction
6. `ODEFormer` vs `ODEFormer (opt)`

保存:

- all candidates
- selected formula
- reconstructed trajectory
- generalized trajectory
- official metrics
- wall time
- failures

Phase 2をもって主目的Aの「原論文互換performance reproduction」を成立させる。

---

## Phase 3: Beam-level symbolic recovery diagnosis

目的: **数式が当たらない原因をgenerationとselectionへ分解する。**

各ODE / seed / corruptionについて、beam 50全候補へsymbolic metricsを計算する。

比較:

- official-selected
- best reconstruction
- structural oracle（診断のみ）
- `ODEFormer (opt)`

主成果:

- true skeleton in beam rate
- symbolic oracle gap
- selected-vs-oracle TED gap
- unique skeleton diversity
- reconstruction / generalization / TED相関

---

## Phase 4: Layer-analysis corpus / teacher-forcing baseline

目的: **層解析専用の独立synthetic corpusを固定する。**

実施:

- official generator reproduction
- formula-level split
- skeleton leakage audit
- corruption conditions生成
- teacher-forcing CE baseline
- token category metrics
- fixed validation / test intervention panels生成
- data fingerprint保存

---

## Phase 5: Observational layer analysis

目的: **20層すべてについて情報表現を測る。**

実施:

- hidden-state extraction
- linear probes
- control probes
- gradient norm
- encoder CKA
- decoder CKA
- encoder intermediate decoding
- decoder intermediate readout

主成果:

- encoder 4-layer table
- decoder 16-layer table
- probe heatmap
- CKA matrix
- token-category depth curves
- encoder-intermediate formula TED curve

---

## Phase 6: Causal layer analysis

目的: **全20層の因果的寄与を測る。**

実施:

- layer ablation
- zero / mean intervention
- matched replacement
- fixed-pair activation patching
- formula-level decode after intervention

保存:

- token effect
- TED effect
- symbolic recovery effect
- reconstruction effect
- generalization effect

Phase 5のobservational rankとPhase 6のcausal rankを比較する。

---

## Phase 7: IOLE / parameter update sensitivity

目的: **各層の適応能力を測る。**

- 20 single-layer FT
- full FT
- frozen
- parameter update sensitivity
- memory / wall time

paired data order / seedを使用する。

---

## Phase 8: Selective fine-tuning

目的: **層解析の知見が実用的なperformanceへつながるか確認する。**

validationだけでrankingを固定後、

- frozen
- full
- top 1
- top 3
- bottom 3
- multiple random 3

を比較する。

最終的にfull decodingを行い、

- symbolic recovery
- reconstruction
- generalization
- complexity
- valid rate
- memory / time

を比較する。

---

## Phase 9: Final test / integrated analysis

Phase 4–8のmethod / layer / hyperparameterを固定後、analysis-testを一度だけ評価する。

最終結果は二本立てにする。

### Result A: ODEFormer reproduction

- paper-compatible benchmark
- Figure 1 examples
- ODEBench reconstruction / generalization
- noise / subsampling robustness
- symbolic recovery
- beam selection diagnosis

### Result B: ODEFormer layer analysis

- probe
- CKA
- intermediate decoding
- IOLE
- ablation
- activation intervention
- rank stability
- selective FT
- symbolic TED trajectory

最後に、

> **ODEFormerがtrajectoryから数式へ変換するとき、どの深さで何が形成され、どの層が正しいODEの生成に必要か**

をまとめる。

---

# 14. 統計設計

## 14.1 Seed

beam sampling、trajectory permutation、corruptionに乱数が入るため、seedを明示する。

主要結果は原則3 seeds以上を目標とする。
正確なseed数はPhase 2のwall timeを測定後、testを見る前に固定する。

## 14.2 Paired comparison

同一

- ODE
- initial condition
- corruption realization
- point permutation
- model seed

をpairedにしてcondition差を計算する。

## 14.3 集計単位

decoder tokenを独立sampleとして統計検定しない。

token-level metricはまずformula / ODE単位に集約し、その後condition比較する。
これによりpseudo-replicationを避ける。

## 14.4 報告

最低限:

- mean
- median
- standard deviation
- paired difference
- 95% CI

seed-levelの少数標本CIにはStudentのt分布を用いる。
必要に応じてODE単位paired bootstrap CIも補助的に報告する。

## 14.5 Rank stability

- Spearman
- Kendall
- top-k overlap

をseed間で保存する。

20層の個別検定を多数行う場合はmultiple comparisonを考慮するが、
重要層の判断をp値だけに依存させず、effect size、rank stability、複数解析法の一致を重視する。

---

# 15. Timeout / failure / resume

## 15.1 Timeout

次を別に持つ。

- model forward / beam decode timeout
- candidate integration timeout
- generalization integration timeout
- BFGS timeout
- symbolic equivalence timeout
- TED timeout
- layer intervention decode timeout

具体値はsmokeの実測後、test前に固定する。

## 15.2 Failure reasons

最低限:

- `CheckpointDownloadError`
- `CheckpointLoadError`
- `ArchitectureMismatch`
- `OfficialConfigMismatch`
- `InputRescaleError`
- `BeamDecodeTimeout`
- `InvalidPrefix`
- `ParseError`
- `CandidateIntegrationFailure`
- `GeneralizationIntegrationFailure`
- `ConstantOptimizationFailure`
- `NaN`
- `Inf`
- `SymbolicEquivalenceTimeout`
- `TEDParseError`
- `TEDTimeout`
- `ActivationHookError`
- `ActivationPatchError`
- `OOM`

を区別する。

## 15.3 Resume単位

- reproduction: seed × benchmark × ODE × noise × subsampling
- beam diagnosis: seed × ODE × condition
- probe: seed × layer × task
- CKA: seed × layer pair
- intermediate decode: seed × layer × problem
- ablation: seed × layer × problem
- intervention: seed × layer × problem
- IOLE: seed × layer
- selective FT: seed × condition

完了済みrecordをresumeで再計算しない。

---

# 16. 保存schema

## 16.1 Provenance

- `run_id`
- `campaign = GPU_RUN4`
- `run_type`
- `source_commit`
- `odeformer_upstream_commit`
- `checkpoint_sha256`
- `odebench_fingerprint`
- `analysis_data_fingerprint`
- `config_fingerprint`
- `seed`
- `corruption_seed`
- `permutation_seed`
- `hardware`
- `software_versions`

## 16.2 Problem

- `problem_id`
- `benchmark`
- `system_name`
- `dimension`
- `split`
- `true_formula_raw`
- `true_formula_prefix`
- `true_formula_canonical`
- `true_formula_skeleton`
- `true_expression_tree`
- `initial_condition_reconstruction`
- `initial_condition_generalization`
- `noise_sigma`
- `subsample_rho`

## 16.3 Prediction

- `condition`
- `beam_size`
- `beam_temperature`
- `candidate_index`
- `candidate_model_score`
- `candidate_formula_raw`
- `candidate_formula_canonical`
- `candidate_formula_skeleton`
- `selected`
- `reconstruction_r2`
- `generalization_r2`
- `canonical_exact`
- `skeleton_exact`
- `symbolic_equivalent`
- `ted_raw`
- `ted_skeleton`
- `complexity`
- `valid`
- `failure_reason`
- `wall_time`

## 16.4 Layer analysis

- `module_name`
- `module_group`
- `layer_index`
- `analysis_type`
- `probe_task`
- `probe_score`
- `gradient_norm`
- `normalized_gradient_norm`
- `cka`
- `true_token_rank`
- `true_token_probability`
- `token_entropy`
- `intermediate_ted`
- `ablation_delta_ted`
- `ablation_delta_generalization_r2`
- `intervention_delta_probability`
- `intervention_delta_ted`
- `update_norm`
- `relative_update_norm`
- `iole_score`

---

# 17. 主成果物

GPU_RUN4終了時に最低限次を作成する。

## 17.1 ODEFormer reproduction report

- environment / provenance
- architecture verification
- paper protocol reproduction
- Figure 1 qualitative examples
- ODEBench reconstruction
- ODEBench generalization
- noise / subsampling robustness
- Strogatz secondary result
- `ODEFormer` vs `ODEFormer (opt)`
- failure一覧

## 17.2 Symbolic recovery report

- true / selected formula table
- exact / skeleton / equivalence
- TED
- coefficient error
- beam oracle diagnostic
- selection failure vs generation failure
- reconstruction / generalization / symbolic recoveryの関係

## 17.3 Layer-analysis report

- architecture map
- encoder / decoder probe heatmaps
- gradient norms
- CKA matrices
- encoder intermediate decoding
- decoder token trajectories
- all-layer IOLE curve
- all-layer ablation curve
- activation intervention effects
- layer rank stability
- selective FT comparison

## 17.4 Problem-level formula table

最低限:

| problem | condition | true formula | selected formula | exact | skeleton | symbolic eq. | TED | recon R² | gen R² | valid/failure |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---|

成功例だけでなく、

- 数値的成功だが構造誤り
- beam内に正解があるのにselection失敗
- constantだけ誤り
- variable誤り
- invalid
- integration failure

を残す。

---

# 18. Go / No-Go基準

## Go 1: Reproductionへ進む条件

- official checkpoint load成功
- architecture特定成功
- official demo成功
- beam 50 inference成功
- predicted ODE integration成功

## Go 2: Symbolic benchmarkへ進む条件

- ODEBench true formula parse成功
- canonicalization gold tests成功
- symbolic equivalence / TEDが安定
- all beam candidatesを保存できる

## Go 3: Layer analysisへ進む条件

- encoder / decoder全層hidden取得成功
- hookを付けてもbaseline outputが変わらない
- teacher-forcing token alignment確認
- fixed analysis panel生成完了

## Go 4: Causal analysisへ進む条件

- ablation / intervention baseline control成功
- interventionによるshape mismatchなし
- failureがproblem単位で保存される

## Go 5: Full selective FTへ進む条件

- 20 single-layer FTのsmoke成功
- full FTのmemory内実行確認
- training budget / seed数をtest前に固定

## No-Go / redesign

次の場合は長時間runを開始せず計画を改訂する。

- paper architectureとreleased checkpointの不一致を説明できない
- official benchmark reproductionがsource/config差により成立しない
- canonicalizationが同値式を安定評価できない
- intervention hook自体がbaseline outputを変える
- fine-tuningがODEBench test情報を利用する設計になっている
- storage / wall timeが想定を大きく超え、途中で条件を恣意的に削る必要がある

---

# 19. 別観点レビューで反映した修正

本planは初稿作成後、同一セッション内で以下の4観点を分離した別レビュー・パスとして批判的に見直した。

1. **再現性**
2. **統計・data leakage**
3. **層解析の因果性**
4. **計算量・運用可能性**

そのレビューから次を反映した。

### 19.1 Official reproductionと独自解析を完全分離

公式protocolの再現にLANSR独自hook / FTを混ぜない。

### 19.2 Beam selection failureを独立診断

ODEFormerはreconstruction $`R^2`$ でbeam候補を選ぶため、正しい数式がbeam内にあっても選ばれない可能性がある。
そこで全候補を保存し、ground truthを使う`structural oracle`を **診断専用** として導入した。

### 19.3 ODEBenchでfine-tuningしない

benchmarkへの適応によって再現性能が過大評価されることを防ぐ。

### 19.4 Parser defaultを信用しない

paper / released checkpoint / source defaultの差をPhase 0で監査し、checkpoint実体をarchitectureの最終根拠にする。

### 19.5 Random 3を複数集合へ拡張

層数が20あるため、random 3を1セットだけ引いた比較は分散が大きい。
複数の固定random setsを用いてtop-layer selectionの付加価値をより堅牢に評価する。

### 19.6 Encoder 4層とdecoder 16層の不均衡を考慮

global rankだけでなくencoder-only / decoder-only rankを保存する。

### 19.7 Token pseudo-replicationを防止

tokenを独立標本として有意差を水増しせず、formula / ODE単位へ集約する。

### 19.8 CKAのcross-module乱用を避ける

encoder / decoderではsequence semanticsが異なるため、主CKAは各module内で行う。

### 19.9 Raw hidden state保存量を制御

fixed panel / streaming extractionを導入し、全dataset × 20層のactivationを無制限保存しない。

### 19.10 因果主張を単一ablationに依存しない

ablation、activation intervention、patching、IOLEを横断して解釈する。

---

# 20. 現時点で未確定の項目

Phase 0（`gpu_run4_phase0_01`）で次は確定した。

- 公開checkpoint SHA256: `56754040be5aa92ed4767fc43ee2008faa293f87c12b643e66c7df3e1623a5e8`
- 公開checkpoint実体: 4 encoder (dim 256) + 12 decoder (dim 512)、16 heads、60,646,773 parameters
- 推論pickle設定: beam sampling、beam size 50、temperature 0.1
- ODEBench fingerprint: `strogatz_equations.py` SHA256 `06bbb9dae2886a82f0a1d4b0cd062d063241bcfed56c01ef2a3a01d863bcf8b4`（63 systems）
- 公式demoは成功（reconstruction $`R^2\approx 0.997`$）
- 論文Table（4+16 / dim 512 / 約86M）とは不一致。長時間runの前に、公開checkpointを再現対象とするか、論文サイズ重みを探すかを決める。

以下はPhase 0–2のsmoke / throughput測定後、**testを見る前にplanを改訂して固定する。**

- experimentで固定するupstream commit
- analysis synthetic corpusの最終sample数
- reproduction seed数
- layer-analysis seed数
- fixed intervention panel数
- random 3-layer set数（目標5、最低3）
- fine-tuning learning rate / epoch / early stopping
- IOLEの主adaptation condition
- block ablationの正確な実装
- activation patch位置
- normalized TEDの定義
- symbolic equivalence timeout
- decode / integration / BFGS timeout
- hidden-state保存precision

これらは「結果を見ながら自由に変える」という意味ではなく、
**validation / smokeだけで固定し、final test以後は変更しない項目** とする。

---

# 21. GPU_RUN4の研究上の位置付け

GPU_RUN4は、

> **ODEFormerというtrajectory-to-equation型の強力なpretrained symbolic regression modelを再現し、その深いencoder-decoder Transformer内部で、正しいODE数式がどのように形成されるかを層別に解析する研究**

として位置付ける。

GPU_RUN4ではGRN固有の生物学的主張は行わない。
まず一般ODEで、

- 高精度なdynamical prediction
- 正しいsymbolic equation recovery
- model内部のlayer-wise mechanism

を同時に理解する。

この結果を、GPU_RUN5以降でgene regulatory dynamicsへ再接続するための基盤とする。
