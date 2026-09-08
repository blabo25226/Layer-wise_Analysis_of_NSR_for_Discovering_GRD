# LANSR 参考文献・関連実装一覧

LANSR（Layer-wise Analysis of Neural Symbolic Regression for Discovering Gene Regulatory Dynamics）で参照する論文・公式実装・データ資源の一覧。

GPU_RUN3以前は、NeSymReS・ND2などのニューラルシンボリック回帰とTransformer層解析を中心に整理していた。

GPU_RUN5では公開ODEFormerを閉じたHill型GRNへ適応し、

* trajectoryからODEを直接生成するニューラルシンボリック回帰
* Hill型制御に現れる有理関数・変数分母の構造回復
* generation failureとcandidate selection failureの分離
* 複数初期条件・複数軌道を使ったcandidate selection
* GRN向けfull / selective fine-tuning
* catastrophic forgetting
* probe / DecoderLens / CKA / gradient / activation intervention / IOLE
* 数値再構成とsymbolic recoveryの分離

が中心的な研究課題となった。

そのため、GPU_RUN5以降は文献を以下の6群に分けて管理する。

1. ODE・network dynamics向けニューラルシンボリック回帰
2. 式構造回復・有理関数・ODE discovery
3. Transformer層解析・mechanistic interpretability・selective fine-tuning
4. GRN・生物学的dynamics・生物データへの応用
5. シンボリック回帰一般・比較手法
6. 補助・基礎文献

---

# 1. ODE・network dynamics向けニューラルシンボリック回帰

現在のLANSRに最も直接関係する文献群。

## 最重要

### ODEFormer / ODEFormer: Symbolic Regression of Dynamical Systems with Transformers

GPU_RUN4・GPU_RUN5の中心モデル。
観測された時系列trajectoryを直接Transformerへ入力し、有限差分による微分推定を介さずODEを数式として生成する。

論文
https://arxiv.org/pdf/2310.05573

---

### ND2 / Discovering Network Dynamics with Neural Symbolic Regression

network dynamicsを対象としたニューラルシンボリック回帰。
GPU_RUN3で再現・層解析の対象とした。

論文
https://www.nature.com/articles/s43588-025-00893-8

---

### LNSR / Learning Interpretable Network Dynamics via Universal Neural Symbolic Regression

network dynamicsをニューラルシンボリック回帰によって人間可読な数式として推定する研究。

論文
https://doi.org/10.1038/s41467-025-61575-7

---

### NSRforCND / PI-NDSR / Neural Symbolic Regression of Complex Network Dynamics

複雑ネットワークのdynamics発見へニューラルシンボリック回帰を適用する研究。

論文
https://arxiv.org/pdf/2410.11185

---

### NSRS / NeSymReS / Neural Symbolic Regression that Scales

GPU_RUN1・GPU_RUN2の中心モデル。
大量の人工数式で事前学習したTransformerを使い、数値点集合から数式を生成する。

現在の主モデルはODEFormerだが、LANSRの研究史とTransformer型SRの基盤として重要。

論文
https://arxiv.org/pdf/2106.06427

ソースコード
https://github.com/SymposiumOrganization/NeuralSymbolicRegressionThatScales

---

### CTC_NSR / Can Test-time Computation Mitigate Reproduction Bias in Neural Symbolic Regression?

ニューラルシンボリック回帰におけるreproduction biasとtest-time computationを扱う。

GPU_RUN5で明確になった「真のHill構造がbeam内へ生成されない」というgeneration bottleneckと特に関係が深い。

論文
https://arxiv.org/pdf/2505.22081

---

### GODE / Grammar-based Ordinary Differential Equation Discovery

formal grammarを用いてODE候補の生成空間を制約・誘導するequation discovery手法。

GPU_RUN5ではODEFormerが変数分母を持つ式を生成できても、真のHill skeletonがbeamに入らない問題が観測された。
GODEのようにdomain knowledgeをgrammarとして生成空間へ入れる方法は、今後のGRN向けgeneration改善と直接関係する。

論文
https://arxiv.org/pdf/2504.02630

出版版
https://doi.org/10.1016/j.ymssp.2025.113395

---

# 2. 式構造回復・有理関数・ODE discovery

GPU_RUN5以降、とくに重要度が上がった文献群。

Hill型GRNでは

$$
\frac{\alpha x^n}{K^n+x^n}
$$

のような変数分母を含む有理関数が重要であり、低いtrajectory errorだけでは正しい機構を回復したとはいえない。

---

## 最重要

### TED / Tree Edit Distance with Variables: Measuring the Similarity between Mathematical Formulas

数式をtreeとして比較するTree Edit Distance。

GPU_RUN3以降、exact matchだけでは捉えられない数式構造の近さを評価するために使用。

論文
https://arxiv.org/pdf/2105.04802

---

### SINDy / Discovering Governing Equations from Data by Sparse Identification of Nonlinear Dynamical Systems

データから支配方程式を疎回帰によって発見するequation discoveryの代表的研究。

ニューラルSRとは異なる系列の基準手法として重要。

論文
https://doi.org/10.1073/pnas.1517384113

ソースコード
https://faculty.washington.edu/sbrunton/sparsedynamics.zip

---

### implicit-SINDy / Inferring Biological Networks by Sparse Identification of Nonlinear Dynamics

SINDyを有理関数・implicit dynamicsへ拡張した研究。

Michaelis–Menten kinetics、細菌のregulatory network、yeast glycolysisなどの生物ネットワークを対象とする。

GPU_RUN5で問題となった「Hill型GRNの変数分母・有理構造を正しく回復できない」という課題に非常に直接的に関係する。

論文
https://arxiv.org/pdf/1605.08368

出版版
https://doi.org/10.1109/TMBMC.2016.2633265

---

### SINDy-PI / SINDy-PI: A Robust Algorithm for Parallel Implicit Sparse Identification of Nonlinear Dynamics

implicit equationや有理関数を含むdynamicsを対象とするSINDy系列の手法。

GPU_RUN5以降は、一般的なSINDyよりもHill型GRNとの関係が特に重要。

論文
https://doi.org/10.1098/rspa.2020.0279

ソースコード
https://github.com/dynamicslab/SINDy-PI

---

### Rational Dynamics SVD / Data-Driven Identification of Rational Nonlinear Dynamics in Biochemical Networks via an Implicit Singular Value Decomposition Based Framework

生物・生化学networkに頻出するrational-function dynamicsを対象とした2026年の研究。

stateとderivativeを混合したlibraryを用い、implicitな有理関数構造をSVDによって同定する。

Michaelis–Menten kinetics、Bacillus subtilis competence network、penicillin production kinetics、yeast glycolysisで検証されている。

GPU_RUN5後のLANSRにとって、Hill型・有理関数構造の回復に直接関係する重要文献。

論文
https://doi.org/10.1049/syb2.70068

オープンアクセス版
https://pmc.ncbi.nlm.nih.gov/articles/PMC13175932/

---

### D-CODE / Discovering Closed-form ODEs from Observed Trajectories

観測trajectoryからclosed-form ODEを発見する。

trajectory-to-equationという観点でODEFormerと比較するうえで重要。

論文
https://openreview.net/forum?id=wENMvIsxNN

ソースコード
https://github.com/ZhaozhiQIAN/D-CODE-ICLR-2022

---

### Data-driven Model Discovery / Data-driven Model Discovery and Model Selection for Noisy Biological Systems

noiseやsparse observationを持つ生物データからODE modelを発見・選択する研究。

生物学的priorを利用したmodel discoveryも扱っており、合成GRNから実生物データへ移る際に重要。

論文
https://doi.org/10.1371/journal.pcbi.1012762

ソースコード
https://github.com/maclean-lab/model-discovery

---

## 重要

### Robust SINDy with Multiple Initial Conditions / A Robust Sparse Identification of Nonlinear Dynamics Approach by Combining Neural Networks and an Integral Form

neural network、automatic differentiation、integral constraintを組み合わせ、noise・少数データに強いequation discoveryを行う。

複数initial conditionsから得られたデータにも拡張されている。

GPU_RUN5で複数初期条件を用いたcandidate selectionがsingle-trajectory selectionより良かった結果と関連する。

論文
https://doi.org/10.1016/j.engappai.2025.110360

---

### WeakIdent / Weak Formulation for Identifying Differential Equations Using Narrow-fit and Trimming

微分推定によるnoise amplificationを弱形式によって抑えるequation discovery手法。

論文
https://www.sciencedirect.com/science/article/pii/S002199912300164X

ソースコード
https://github.com/sunghakang/WeakIdent

---

### ODEG / ODE Parameter Inference Using Adaptive Gradient Matching with Gaussian Processes

Gaussian processを利用してODEのgradient matchingを行う。

有限差分以外の導関数推定・ODE inferenceの参考。

論文
https://proceedings.mlr.press/v31/dondelinger13a.html

---

# 3. Transformer層解析・mechanistic interpretability・selective fine-tuning

LANSRの中心テーマである層解析を支える文献群。

GPU_RUN5では「重要層」を一つのscoreとして扱わず、

* 情報が読み出せる層
* gradientを受ける層
* interventionすると性能を壊す層
* 単独fine-tuningすると適応できる層

を区別する必要性が明確になった。

---

## 最重要

### TSRM / Explaining the Explainer: Understanding the Inner Workings of Transformer-based Symbolic Regression Models

Transformer型symbolic regressionそのものを内部解析する、LANSRと最も近いinterpretability研究。

論文
https://arxiv.org/pdf/2602.03506

---

### IOLE / Is One Layer Enough? Training A Single Transformer Layer Can Match Full-Parameter RL Training

単一Transformer層のtrainingでfull-parameter trainingに近い性能を得られる場合を調べた研究。

LANSRのsingle-layer fine-tuning / IOLE解析の主要な着想源。

GPU_RUN5ではselective FTがfull FTよりforgettingを抑える一方、formula recoveryではfull FTを上回らなかったため、「いつone layer / few layersで十分なのか」がより重要な問いとなった。

論文
https://arxiv.org/pdf/2607.01232

---

### LASF / A Layer-wise Analysis of Supervised Fine-Tuning

supervised fine-tuningを層ごとに解析する研究。

層ごとのadaptationとcatastrophic forgettingを考察するうえでGPU_RUN5との関連が強い。

論文
https://arxiv.org/pdf/2604.11838

出版版
https://aclanthology.org/2026.acl-long.453/

---

### DecoderLens / DecoderLens: Layerwise Interpretation of Encoder-Decoder Transformers

encoder-decoder Transformerについて、中間decoder層から出力predictionを読み出して層ごとのprediction refinementを解析する。

GPU_RUN4・GPU_RUN5のDecoderLens解析の主要文献。

論文
https://arxiv.org/pdf/2310.03686

---

### Tuned Lens / Eliciting Latent Predictions from Transformers with the Tuned Lens

各Transformer blockのhidden representationから語彙分布を読み出すaffine probeを学習し、中間層でpredictionがどのように形成されるかを解析する。

通常のlogit lensより安定したlayerwise decodingを目的としている。

GPU_RUN5ではDecoderLensの全decoder層でmedian variable-aware TEDが飽和したため、今後のより精密な中間層prediction解析の参考として重要。

論文
https://arxiv.org/pdf/2303.08112

ソースコード
https://github.com/AlignmentResearch/tuned-lens

---

### CKA / Similarity of Neural Network Representations Revisited

Centered Kernel Alignmentによって層間representation similarityを比較する代表的研究。

GPU_RUN5ではencoderとdecoderでwithin-module CKAに大きな違いが観測された。

論文
https://arxiv.org/pdf/1905.00414

---

### DIP / Designing and Interpreting Probes with Control Tasks

probeが本当に内部representationの情報を測っているのか、probe自身のcapacityによる結果なのかを区別するためのcontrol taskを論じる。

GPU_RUN5でprobe順位とcausal intervention順位が一致しなかったことを解釈するうえで重要。

論文
https://arxiv.org/pdf/1909.03368

---

### BPAP / Towards Best Practices of Activation Patching in Language Models: Metrics and Methods

activation patchingの評価metric・手法設計を扱う。

論文
https://arxiv.org/pdf/2309.16042

---

### HUIAP / How to Use and Interpret Activation Patching

activation patchingをどのように実行し、因果的な主張をどこまで行えるかを整理した研究。

論文
https://arxiv.org/pdf/2404.15255

---

### Causal Abstraction / Causal Abstraction: A Theoretical Foundation for Mechanistic Interpretability

activation patching、causal tracing、causal mediationなどのmechanistic interpretability手法をcausal abstractionという統一的な枠組みで整理する。

GPU_RUN5でprobe、gradient、causal intervention、IOLEを異なるestimandとして扱う理論的背景として重要。

論文
https://arxiv.org/pdf/2301.04709

出版版
https://www.jmlr.org/papers/v26/23-0058.html

---

# 4. GRN・生物学的dynamics・生物データへの応用

LANSRを単なるsymbolic regression研究ではなく、遺伝子制御dynamicsの発見へ接続するための文献群。

---

## 最重要

### Gene Regulatory Networks: From Correlative Models to Causal Explanations

GRNを単なるgene–gene correlationではなく、細胞の挙動を説明するmechanistic / causal modelとして考える2026年のPerspective。

LANSRが辺の推定だけでなく、遺伝子制御の動的方程式そのものを発見しようとする研究意義と非常に近い。

論文
https://doi.org/10.1038/s41576-026-00939-1

オープンアクセス版
https://pmc.ncbi.nlm.nih.gov/articles/PMC7618986/

---

### Data-driven Discovery of Dynamical Models in Biology

生物学におけるdata-driven dynamical model discoveryをまとめた2026年のTechnical Review。

ODE・非線形feedback・data-driven model discovery・machine learningなどを広く俯瞰する。

現在のLANSR全体を生物学的model discoveryの中へ位置付ける際の主要総説。

論文
https://doi.org/10.1038/s42254-026-00955-4

---

### scKINETICS / scKINETICS: Inference of Regulatory Velocity with Single-cell Transcriptomics Data

single-cell transcriptomicsからgene-expression velocityとGRNを同時推定する研究。

gene regulatory dynamicsを直接推定する点でLANSRの最終応用と近い。

scKINETICS自体は線形・time-homogeneousなODE systemとEMを用いるためLANSRのsymbolic regressionとは方法が異なるが、gene expression derivativeが直接観測されない状況でregulatory dynamicsを推定する近縁研究として重要。

論文
https://doi.org/10.1093/bioinformatics/btad267

オープンアクセス版
https://pmc.ncbi.nlm.nih.gov/articles/PMC10311321/

ソースコード
https://github.com/dpeerlab/scKINETICS

---

### GNW / GeneNetWeaver: In Silico Benchmark Generation and Performance Profiling of Network Inference Methods

DREAM系GRN benchmark生成に使用されるGeneNetWeaver。

合成GRNの構造・dynamics・benchmark設計の基盤。

論文
https://doi.org/10.1093/bioinformatics/btr373

ソースコード
http://gnw.sourceforge.net

---

### DREAM4 / DREAM4 In Silico Network Challenge

正解GRN付きの代表的なnetwork inference benchmark。

GPU_RUN5ではGo 8 NO-GOにより追加DREAM4実験へ進まなかったため、現在は次段階の外部benchmarkとして位置付ける。

データ資源
https://gnw.sourceforge.net/dreamchallenge.html

---

## 重要

### dynGENIE3 / dynGENIE3: Dynamical GENIE3 for the Inference of Gene Networks from Time Series Expression Data

時系列gene expressionからGRN edgeを推定する代表的な比較手法。

LANSRはedgeだけでなく制御方程式そのものを発見する点が異なる。

論文
https://doi.org/10.1038/s41598-018-21715-0

ソースコード
http://www.montefiore.ulg.ac.be/~huynh-thu/dynGENIE3.html

---

# 5. シンボリック回帰一般・比較手法

現在の中心テーマそのものではないが、SR全体の位置付け・baseline・generation/search手法の比較に重要。

---

## 重要

### PySR / Interpretable Machine Learning for Science with PySR and SymbolicRegression.jl

進化計算を用いる代表的な実用symbolic regression。

Neural SRとの非ニューラルbaselineとして重要。

論文
https://arxiv.org/pdf/2305.01582

ソースコード
https://github.com/MilesCranmer/PySR

https://github.com/MilesCranmer/SymbolicRegression.jl

---

### SRBench / Contemporary Symbolic Regression Methods and their Relative Performance

多数のsymbolic regression手法を比較したbenchmark研究。

論文
https://arxiv.org/pdf/2107.14351

ソースコード
https://github.com/EpistasisLab/srbench

---

### TPSR / Transformer-based Planning for Symbolic Regression

Transformerのnext-token priorとMonte Carlo Tree Searchを組み合わせたtest-time search。

GPU_RUN1で使用した。

GPU_RUN5では主要手法ではないが、generation failureに対してtest-time search budgetを増やす方向の関連研究として残す。

論文
https://arxiv.org/pdf/2303.06833

ソースコード
https://github.com/deep-symbolic-mathematics/tpsr

---

### ScaleSR / Scalable Neural Symbolic Regression Using Control Variables

多変数symbolic regressionをcontrol variablesによって分解するニューラルSR。

論文
https://arxiv.org/pdf/2306.04718

---

### BSR / Boolformer / Boolformer: Symbolic Regression of Logic Functions with Transformers

Transformerによるsymbolic recoveryを論理関数へ適用する研究。

論文
https://arxiv.org/pdf/2309.12207

ソースコード
https://github.com/arthurenard/Boolformer

---

### ESRT / End-to-end Symbolic Regression with Transformers

Transformerを用いたend-to-end symbolic regression。

論文
https://arxiv.org/pdf/2204.10532

---

### CNSR / Controllable Neural Symbolic Regression

生成する数式へ制約を与えるcontrollable neural SR。

GPU_RUN5後は、GRN向けoperator / grammar constraintを検討する際の参考となる。

論文
https://arxiv.org/pdf/2304.10336

---

### NGDSN / DySymNet / A Neural-Guided Dynamic Symbolic Network for Exploring Mathematical Expressions from Data

neural guidanceを利用して数式構造を探索するsymbolic regression。

論文
https://arxiv.org/pdf/2309.13705

ソースコード
https://github.com/AILWQ/DySymNet

---

### DGSR / Deep Generative Symbolic Regression with Monte-Carlo Tree Search

deep generative modelとMonte Carlo Tree Searchを組み合わせたsymbolic regression。

論文
https://arxiv.org/pdf/2302.11223

---

### UFDSR / A Unified Framework for Deep Symbolic Regression

deep symbolic regressionを統一的なframeworkで扱う研究。

論文
https://proceedings.neurips.cc/paper_files/paper/2022/hash/dbca58f35bddc6e4003b2dd80e42f838-Abstract-Conference.html

ソースコード
https://github.com/dso-org/deep-symbolic-optimization

---

### DSR / Deep Symbolic Regression: Recovering Mathematical Expressions from Data via Risk-seeking Policy Gradients

reinforcement learningを利用した代表的なdeep symbolic regression。

論文
https://arxiv.org/pdf/1912.04871

---

# 6. 補助・基礎文献

LANSRの直接の新規性ではないが、Transformer、set input、parameter-efficient adaptationなどの基礎として参照する。

---

### Transformer / Attention Is All You Need

Transformer architectureを提案した基礎論文。

ODEFormer、NeSymReS、ND2などLANSRで解析するTransformer型モデルの基盤。

論文
https://arxiv.org/pdf/1706.03762

---

### ST_FAPNN / Set Transformer: A Framework for Attention-based Permutation-Invariant Neural Networks

順序を持たないset入力をattentionで処理するarchitecture。

NeSymReSなど、数値点集合を扱うneural symbolic regressionの背景として参照する。

論文
https://arxiv.org/pdf/1810.00825

---

### LoRA / LoRA: Low-Rank Adaptation of Large Language Models

low-rank adaptationによるparameter-efficient fine-tuning。

LANSRのlayer-selective fine-tuningとは異なるが、parameter-efficient adaptationとの比較・発展候補として参照する。

論文
https://arxiv.org/pdf/2106.09685

ソースコード
https://github.com/microsoft/LoRA

---

# GPU_RUN5以降の優先読書順

現在のLANSRを理解・発展させるうえでは、以下を優先する。

## Tier 1：現在の研究に直接必要

1. ODEFormer
2. TSRM / Explaining the Explainer
3. IOLE / Is One Layer Enough?
4. LASF / A Layer-wise Analysis of Supervised Fine-Tuning
5. TED
6. implicit-SINDy
7. SINDy-PI
8. GODE
9. CTC_NSR
10. Gene Regulatory Networks: From Correlative Models to Causal Explanations
11. Data-driven Discovery of Dynamical Models in Biology

## Tier 2：GPU_RUN5の結果解釈・次実験に重要

1. DecoderLens
2. Tuned Lens
3. CKA
4. Designing and Interpreting Probes with Control Tasks
5. Activation Patching関連2報
6. Causal Abstraction
7. Rational Dynamics SVD
8. Data-driven Model Discovery and Model Selection for Noisy Biological Systems
9. Robust SINDy with Multiple Initial Conditions
10. D-CODE
11. scKINETICS

## Tier 3：比較・研究背景

1. ND2
2. LNSR
3. PI-NDSR
4. NeSymReS
5. SINDy
6. PySR
7. SRBench
8. TPSR
9. dynGENIE3
10. GNW / DREAM4

## Tier 4：補助

1. Attention Is All You Need
2. Set Transformer
3. LoRA
4. ScaleSR
5. Boolformer
6. ESRT
7. CNSR
8. DySymNet
9. DGSR
10. UFDSR
11. DSR
