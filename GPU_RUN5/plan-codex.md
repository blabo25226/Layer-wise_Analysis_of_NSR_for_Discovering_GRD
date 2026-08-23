# GPU_RUN5 計画案 — ODEFormerのGRN向け構造適応と多軌道候補選択

- 作成日: 2026-08-23
- 状態: **Codex案・未確定**
- 主モデル: 公開ODEFormer checkpoint（4 encoder + 12 decoder、約61M parameters）
- 前段run: [`GPU_RUN4`](../GPU_RUN4/README.md)
- 関連する合成GRN設計: [`GPU_RUN2/plan.md`](../GPU_RUN2/plan.md)

> この文書はGPU_RUN5の候補計画であり、まだ実行条件の正本ではない。
> Phase 0のauditとsmall pilotを終え、計算量、データ規模、効果margin、最終test条件を固定してから実行版へ昇格する。
> test結果を見た後に本計画の選択規則、主要指標、層集合、hyperparameterを変更しない。

---

# 1. 方針

GPU_RUN5では、ODEFormerを今後の中心モデルとして採用し、**軌道への高い適合を、遺伝子制御ODEの構造回復へつなげられるか**を検証する。

ODEFormerを選ぶ理由は次のとおりである。

1. 観測された $`(t,\mathbf{x}(t))`$ から多次元ODEを直接生成でき、有限差分で $`d\mathbf{x}/dt`$ を推定することを必須としない。
2. 公開checkpoint、推論コード、ODEBench、再積分を含む評価経路をGPU_RUN4で動作確認済みである。
3. GPU_RUN4ではreconstruction $`R^2`$ 中央値0.980を得ており、観測軌道を説明する候補ODEを生成する能力は高い。
4. 生成後に候補式を再積分できるため、複数初期条件、外挿、安全性を候補選択へ組み込みやすい。

ただし、GPU_RUN4ではcanonical exact 0、skeleton exact 0.075、true skeleton in beam 0.091であった。
したがって「軌道予測精度が高い」ことを「真の支配方程式を回復できる」ことと同一視しない。

GPU_RUN5の中心仮説は次である。

> ODEFormerによる遺伝子制御式の回復には、
> **GRN式を候補として生成できること** と **複数軌道から真式と近似式を識別できること** の2つが必要であり、
> selective fine-tuningの効果はこの2条件を満たした後にformula-levelで現れる。

GPU_RUN5は次の3段階を分離する。

1. **Generation**: 真のGRN構造をbeam内へ生成できるか。
2. **Selection / identifiability**: 真構造がbeam内にあるとき、軌道情報だけで選べるか。
3. **Adaptation**: GRN向けFTと層選択FTがgenerationと最終式回復を改善するか。

---

# 2. GPU_RUN4から固定して引き継ぐ事実

GPU_RUN5の出発点は[`GPU_RUN4研究結果`](../GPU_RUN4/GPU_RUN4_research_report_20260819.md)とする。

| 項目 | GPU_RUN4で確認した事実 | GPU_RUN5への含意 |
|---|---|---|
| checkpoint | 公開4 encoder + 12 decoder、60,646,773 parameters | 論文Tableの4+16 / 約86Mとは分ける |
| ODEBench | 63 systems × 4 corruption、1 seed | 再現の全面反復を主目的にしない |
| reconstruction | valid中央値 $`R^2=0.980`$ | 数値fitのbaselineとして維持 |
| generalization | valid中央値 $`R^2=0.696`$ | 入力軌道外の評価が必要 |
| symbolic recovery | canonical exact 0、skeleton 19/252 | 構造回復を主指標へ置く |
| beam | true skeleton in beam 23/252 | generation failureを独立評価する |
| selection gap | 取り逃がしは5/252 | rerankingだけでは全失敗を直せない |
| FT | 80式、4 Adam steps | 選択FT仮説の検定として不十分 |
| final CE | frozenが全FT条件より良い | CEだけで層FTの価値を判定しない |
| layer analysis | encoder probe、zero ablation、短いIOLEまで | decoder readoutと介入後decodeが未完 |

GPU_RUN5ではODEBenchをfine-tuningに使わない。ODEBenchは公開モデルの固定reference benchmarkとしてのみ扱い、
GRN適応前後のcatastrophic forgetting確認に限定する。

---

# 3. 目的と非目的

## 3.1 主目的A: ODEFormerのGRN generation supportを測る

公開ODEFormerが、GNW由来のHill型・有理式を既に候補として生成できるかを測る。
最終選択式だけでなく全beam候補を保存し、次を分離する。

- 真の式構造が候補集合に存在しないgeneration failure
- 真の式構造は存在するが選ばれないselection failure
- parse、再積分、特異点によるevaluation failure

## 3.2 主目的B: 多軌道候補選択を検証する

単一の入力軌道上だけで候補を選ぶ条件と、別初期条件の軌道も使う条件を比較する。
ground truth式を使うstructural oracleは診断専用とし、実運用の候補選択には使わない。

## 3.3 主目的C: GRN向けselective fine-tuningを検証する

GRN合成ODEで公開checkpointを適応し、次を比較する。

- frozen
- full fine-tuning
- decoder-all fine-tuning
- top 1 block
- top 3 blocks
- causal top 3 blocks
- bottom 3 blocks
- 複数のrandom 3-block集合

selective FTの価値はteacher-forcing CEではなく、最終decode後のskeleton recovery、TED、generalization、valid rateで判定する。

## 3.4 GPU_RUN5で主対象にしないもの

- 論文Tableの4+16 / 約86M ODEFormerの再現
- ODEFormerを最初から大規模事前学習すること
- DREAM4 Size10 / Size100全系をそのまま一括入力すること
- regulator selectionとODE discoveryを同時に最適化すること
- ヒトRNA-seqから因果的な真のODEを主張すること
- ODEFormer、NeSymReS、ND2の数値を同一表で直接順位付けすること
- test結果を見ながら層、learning rate、step数、候補選択重みを選び直すこと

---

# 4. 研究質問

## RQ1: Frozen ODEFormerのGRN生成能力

**RQ1. 公開ODEFormerは、変数分母とHill型制御を含むGRN式をbeam内へどの程度生成できるか。**

主指標:

- true canonical formula in beam rate
- true skeleton in beam rate
- variable-aware oracle TED
- variable-denominator candidate rate
- Hill-pattern candidate rate
- unique canonical / skeleton candidates per beam
- valid candidate rate

## RQ2: Candidate generationとselection

**RQ2. GRN式の回復失敗は、候補を生成できないためか、生成した候補を選べないためか。**

比較:

- official-selected candidate
- input-trajectory best candidate
- selection-trajectory best candidate
- multi-trajectory best candidate
- structural oracle best candidate（診断のみ）

## RQ3: 多軌道による識別可能性

**RQ3. 別初期条件の軌道を候補選択へ追加すると、観測軌道上だけで合う代替式を排除できるか。**

主指標:

- selected skeleton recovery
- selected variable-aware TED
- held-out initial condition上のreconstruction / generalization
- 選択前後の特異点率
- 入力軌道とselection軌道の性能差

## RQ4: GRN向けfine-tuning

**RQ4. GRN合成ODEによるfine-tuningは、同じstep数の公式分布continued-FT対照よりGRN式回復を改善するか。**

単なる追加学習の効果とGRN domain adaptationの効果を分けるため、公式generator由来continued-FTを対照に含める。

## RQ5: Selective fine-tuning

**RQ5. 少数blockだけのGRN向けFTは、full FTより事前学習性能を保ちながら、GRNのsymbolic recoveryを改善できるか。**

## RQ6: Layer rankingの付加価値

**RQ6. Validationで選んだtop block集合は、複数の固定random集合よりformula-level指標で良いか。**

## RQ7: Decoder深度とGRN token生成

**RQ7. 変数、`inv`、整数べき、乗算、加算、定数tokenの正解順位と式TEDは、decoder深度に沿ってどう変化するか。**

## RQ8: 難易度依存性

**RQ8. 効果は、式族、次元、変数分母、noise、subsampling、structure/family holdoutで変わるか。**

---

# 5. 研究上の絶対条件

## 5.1 Validation / test分離

- corpus生成後、ODEまたはskeleton単位でtrain / validation / testへ分ける。
- trajectory行や時点をランダムにsplitしない。
- layer ranking、hyperparameter、FT step数、候補選択重み、early stoppingはvalidationだけで決める。
- final testは条件を固定した後に一度だけ評価する。
- test式、test family、test初期条件をrankingへ使わない。

## 5.2 ODEBenchを適応データにしない

ODEBenchは公開checkpointのreference評価に使い、FT corpus、層選択、hyperparameter選択には使わない。
適応後ODEBench評価は、既存能力の保持を測るsecondary outcomeとする。

## 5.3 数値fitと式回復を分ける

高いreconstruction $`R^2`$ を式回復と呼ばない。少なくとも次を別々に保存・報告する。

- trajectory reconstruction
- initial-condition generalization
- canonical / symbolic equivalence
- skeleton recovery
- variable-aware TED
- variable recovery
- complexity
- valid rate
- singularity / integration failure

## 5.4 Generationとselectionを分ける

selected formulaだけでなく全候補を保存する。ground truthを使うoracleは診断専用とし、実用条件の成績に混ぜない。

## 5.5 複数軌道の役割を固定する

各ODEについて、初期条件を次の役割へ事前分割する。

| 軌道 | 用途 | 選択への利用 |
|---|---|---|
| input trajectory | ODEFormerへの入力 | 可 |
| selection trajectory | candidate reranking / validation | 可 |
| generalization trajectory | 最終評価 | 不可 |

test ODEのgeneralization trajectoryを候補選択へ使わない。

## 5.6 Failureを隠さない

- parse失敗、NaN、Inf、積分失敗、timeout、特異点をproblem単位で保存する。
- 成功候補だけの中央値に加え、failure-penalized指標を主表へ含める。
- 全候補が失敗したproblemを集計から除外しない。

## 5.7 条件比較を公平にする

- 同一seed内の条件は同じ初期checkpoint、data order、trajectory、candidate budgetを使う。
- 各trainable条件に同じhyperparameter候補数を与える。
- 主比較は同じoptimizer step数と例順を使うstep-matched比較とする。
- wall time、peak memory、trainable parameter数を保存し、time-matched副解析も可能にする。
- random block集合はtest前に複数固定する。

---

# 6. モデルと語彙

## 6.1 対象checkpoint

GPU_RUN4と同じ公開checkpointを使う。

| 項目 | 固定値 |
|---|---|
| encoder | 4 blocks、dim 256 |
| decoder | 12 blocks、dim 512 |
| heads | 16 |
| parameters | 60,646,773 |
| checkpoint SHA256 | `56754040be5aa92ed4767fc43ee2008faa293f87c12b643e66c7df3e1623a5e8` |
| main beam | sampling 50、temperature 0.1 |

Phase 0でcheckpoint実体から再監査し、parser defaultを根拠にしない。

## 6.2 既存語彙内でのGRN表現

GPU_RUN5の主実験では新しい`hill` tokenを追加しない。Hill式を既存語彙の
`add`、`mul`、`inv`、整数べき、変数、定数で表現する。

新token追加はembeddingと出力headの変更を伴い、公開checkpointの比較可能性を大きく変えるため、別campaignとする。

Phase 0で次をfail fast確認する。

- G01–G08のcompact teacher expressionが語彙へencodeできる。
- target token lengthがcheckpointの上限内である。
- 1–3変数の閉じたODE系を入力・出力できる。
- `inv` と整数べきがdecode候補としてmaskされていない。
- 多成分区切りと成分順が保存される。

---

# 7. GRN合成ODE corpus

## 7.1 G01–G08の再利用

[`src/data/gnw_synthetic.py`](../src/data/gnw_synthetic.py) のGNW由来8式族を再利用する。

| 族 | 入力変数 | 構造 |
|---|---:|---|
| G01 | 1 | basal transcription + degradation |
| G02 | 2 | single activator Hill |
| G03 | 2 | single repressor Hill |
| G04 | 3 | two independent activators |
| G05 | 3 | two complex-forming activators |
| G06 | 3 | activator + deactivator |
| G07 | 3 | enhancer + repressor、two-module mixture |
| G08 | 3 | two enhancer modules、two-module mixture |

G01以外は変数を分母に含む。canonical expressionは構造評価用、compact teacher expressionはtoken教師用とし、
両者が代数的に同値であることをtestする。

## 7.2 右辺関数を閉じたODE系へ変換する

G01–G08は主に対象遺伝子 $`x_1`$ の右辺 $`f_1(x_1,x_2,x_3)`$ を定める。
ODEFormerへ軌道を入力するには、regulator $`x_2,x_3`$ を含む全成分の時間発展を定めた閉じた系が必要である。

したがって各target equationへ、事前登録したregulator dynamicsを組み合わせる。

```math
\frac{dx_1}{dt}=f_{\mathrm{GNW}}(x_1,x_2,x_3),\qquad
\frac{dx_j}{dt}=g_j(\mathbf{x}),\quad j=2,3.
```

主条件では $`g_j`$ を安定な低複雑度ODEの固定poolから選ぶ。候補例は線形緩和、弱い相互作用、周期入力を自律系として表す補助成分である。
最終pool、係数範囲、安定性条件はPhase 1で固定し、test familyだけに特有のregulator dynamicsを置かない。

重要な評価単位を分ける。

- **target-component recovery**: $`dx_1/dt`$ のGNW構造回復。GPU_RUN5の主指標。
- **system recovery**: 全成分を含むODE系全体の回復。副指標。
- **regulator-component recovery**: 追加した $`g_j`$ の回復。難易度監査用。

regulator dynamicsの選択が結果を支配しないよう、GNW familyとregulator backgroundを交差させ、familyごとに同じ背景分布を使う。

## 7.3 Corpus規模

Phase 0–1のthroughput pilot後、testを見る前に規模を固定する。初期案は次とする。

| split | family当たりvariant | 合計ODE systems | 1 system当たり初期条件 |
|---|---:|---:|---:|
| train | 60 | 480 | 4以上 |
| validation | 20 | 160 | 4以上 |
| test | 20 | 160 | 4以上 |

最低限、各systemへinput、selection、generalizationの独立初期条件を割り当てる。
同一systemの異なる初期条件を異なる式splitへまたがせない。

規模を変更する場合はGPU memory、wall time、valid trajectory率を根拠にし、結果を見る前にmanifestへ記録する。

## 7.4 Split views

### Main variant split

各family内でvariantをtrain / validation / testへ分け、未知係数・未知初期条件への一般化を測る。

### Family holdout

- train: G01–G05
- validation: G06
- test: G07–G08

G02/G03、G07/G08は一部の代数templateを共有するため、このviewを無条件に「完全なskeleton-OOD」と呼ばない。
canonical skeleton fingerprintを監査し、trainとtestのskeletonが本当に非重複の場合だけstructure-OODと記載する。

### Rational vs non-rational view

- G01
- G02–G08

を分けて報告する。全family平均だけで回復率を示さない。

## 7.5 軌道生成

- 真のODEを数値積分して軌道を生成する。
- 生成前に係数、初期条件、時間範囲を固定する。
- 発散、負値、定常点への即時収束、情報量不足を理由付きで記録する。
- 生成後に都合の良い軌道だけを手作業で選ばない。
- train / validation / testで同じ軌道品質基準を適用する。
- trajectory checksumと生成設定を保存する。

遺伝子発現量は原則非負領域で生成する。負値へ出る系は、数値的に積分できても生物学的GRN主結果から分ける。

## 7.6 Corruption条件

主grid候補:

| 要因 | 水準 |
|---|---|
| observation noise | 0、0.05 |
| subsampling | 0、0.5 |
| sampling interval | regular、irregular |

noise 0.1はstress test候補とし、主gridへ入れるかはPhase 0のwall-time pilot後、test前に固定する。

---

# 8. Candidate generationと多軌道selection

## 8.1 Candidate budget

主条件はGPU_RUN4互換のbeam sampling 50、temperature 0.1とする。

generation diversityの副比較候補:

- 1回のsamplingで50候補
- 独立samplingを複数回行い、合計50候補
- 合計200候補
- validationで固定したtemperature候補

候補数が異なる条件は推論時間とcandidate evaluation回数も報告する。
beamを増やした場合、selected scoreだけでなくunique skeleton数とoracle TEDが改善したかを確認する。

## 8.2 Selection条件

候補式 $`f_k`$ を同じcandidate setから選ぶ。

1. `official_reconstruction`: input trajectoryの再積分 $`R^2`$
2. `input_robust`: input trajectoryのfailure-aware normalized error
3. `selection_ic`: 独立selection trajectoryのerror
4. `multi_ic`: input + selection trajectoriesのrobust集約
5. `multi_ic_complexity`: multi-IC error + validationで固定したcomplexity penalty
6. `structural_oracle`: ground truth TED最小（診断専用）

主multi-trajectory scoreの候補は次とする。

```math
S(f_k)=\mathrm{median}_{j\in\mathcal{J}_{\mathrm{select}}}
\left[\mathrm{NRMSE}\left(\hat{\mathbf{x}}_{k,j},\mathbf{x}_j\right)\right]
+\lambda C(f_k).
```

$`\lambda`$、trajectory集約方法、failure penaltyはvalidationだけで固定する。
平均だけでなくmedianまたはtrimmed集約を候補とし、積分失敗を除外しない。

## 8.3 Selection failureの定義

- `generation_failure`: true skeletonがcandidate setにない。
- `selection_failure`: true skeletonがcandidate setにあるが選択されない。
- `integration_failure`: candidateはparse可能だがselection trajectoryを積分できない。
- `metric_failure`: scoreを有限値として計算できない。

各failureをsystem / component / seed / corruption単位で保存する。

---

# 9. Fine-tuning設計

## 9.1 FT corpus条件

追加学習そのものの効果とGRN domain adaptationを分ける。

| 条件 | 学習データ | 目的 |
|---|---|---|
| frozen | なし | 公開checkpoint baseline |
| official-continued | 公式generator分布 | 追加stepだけの対照 |
| GRN-adapted | G01–G06またはmain train | GRN構造適応 |

Family holdout viewではG07/G08を一切FTに使わない。

## 9.2 学習目的

主目的は正解prefix列のteacher-forcing cross entropyとする。
ただし最終的なmodel selectionはCE単独では行わず、validation full decodeのformula-level scoreを使う。

補助的にtoken category別CEを保存する。

- variable
- `inv`
- integer power
- multiplication
- addition / subtraction
- constants
- component separator
- end-of-sequence

## 9.3 Hyperparameter探索

初期候補:

- learning rate: $`10^{-6}`$、$`10^{-5}`$、$`10^{-4}`$
- optimizer steps: 50、200、1000
- clean / corruption-heavy mixture
- early stopping patience
- full、decoder-all、single-blockで同数の候補

これは候補案であり、smokeで明らかに無効またはOOMとなる条件を除いた後、validation実行前に最終gridを固定する。
各trainable条件へ同じ候補数を与える。

## 9.4 Step-matchedとtime-matched

主比較は同じbatch、data order、optimizer step数を使うstep-matched比較とする。
副解析として同じwall timeまたは同じtrainable parameter-update量に近づけた比較を行ってよい。
どちらを主比較とするかを結果後に入れ替えない。

---

# 10. 層解析とranking

## 10.1 対象block

公開checkpointの全16 Transformer blocksを対象とする。

- encoder 4 blocks
- decoder 12 blocks

「16 decoder層」または「20層」と記載しない。

## 10.2 GPU_RUN4から補完する解析

- decoder hidden probe
- label-shuffle control probe
- decoder logit lens / intermediate readout
- token-category別の正解token順位
- decoder深度に沿ったgreedy formula TED
- mean activation intervention
- fixed-pair activation patching
- 介入後のbeam decodeとformula-level metrics

hard zero ablationは必要性を測るが破壊が強すぎるため、単独で機能分解を主張しない。

## 10.3 IOLE

各blockを1つだけtrainableにし、同じデータ順・step数・hyperparameter候補数でFTする。

IOLE rankingの主scoreはvalidation full decodeから作るfailure-aware formula scoreとし、CE順位は副指標とする。
scoreの正確な定義はtest前に固定する。

## 10.4 Layer ranking

主top集合はvalidation上のIOLE formula scoreで決める。
causal top集合は介入後のformula-level劣化で別に定義する。
probe、gradient、CKA、CEは補助的整合性として扱い、一つの曖昧な総合順位へ無理に統合しない。

保存するrank:

- IOLE formula rank
- teacher-forcing CE rank
- causal intervention rank
- decoder lens rank
- encoder-only / decoder-only rank
- tie-aware rank group

## 10.5 Selective FT条件

主比較:

- frozen
- official-distribution continued full FT
- GRN full FT
- GRN decoder-all FT
- GRN top 1
- GRN top 3
- GRN causal top 3
- GRN bottom 3
- GRN random 3 × 5集合以上

random集合はtop集合との重複数も保存する。top 3とほぼ同じrandom集合だけを対照にしない。

---

# 11. 評価指標

## 11.1 Formula-level primary metrics

- target-component canonical exact
- target-component symbolic equivalence
- target-component skeleton exact
- target-component variable-aware TED
- system-level exact / skeleton / TED
- variable precision / recall / F1
- coefficient error（skeleton一致時のみ）
- expression complexity
- valid rate

G01とG02–G08を分ける。family macro-averageとproblem micro-averageの両方を保存する。

## 11.2 Candidate-level metrics

- true formula / skeleton in beam
- oracle best TED
- selected-vs-oracle TED gap
- true candidate rank
- unique canonical / skeleton candidates
- rational candidate rate
- selection failure rate

## 11.3 Trajectory metrics

- input reconstruction $`R^2`$ / NRMSE
- selection-IC $`R^2`$ / NRMSE
- generalization-IC $`R^2`$ / NRMSE
- short-horizon / long-horizon error
- integration success rate
- divergence time

平均 $`R^2`$ は大きな負の外れ値で壊れるため、median、quantile、failure-aware集約を主にする。

## 11.4 Safety metrics

- NaN / Inf
- denominator near zero
- integration divergence
- negative-state violation
- out-of-domain blow-up
- timeout

## 11.5 Efficiency metrics

- trainable parameter count / ratio
- optimizer steps
- examples seen
- peak GPU memory
- training wall time
- decode wall time
- candidate integration回数
- total candidate-evaluation budget

---

# 12. 統計設計

## 12.1 Seed

smokeとhyperparameter pilotは1 seedでよい。最終比較は原則5 paired seed bundlesを使う。
計算資源により3 seedsへ減らす場合、Studentのt区間は報告するが、margin同等性や安定した優位を強く主張しない。

各bundleは少なくとも次を持つ。

- data seed
- trajectory / initial-condition seed
- model / dropout seed
- candidate sampling seed
- corruption seed
- random-layer-set seed

## 12.2 集計単位

- tokenを独立標本としない。
- 同一ODEの複数初期条件を独立な式回復標本として水増ししない。
- component指標とsystem指標を分ける。
- seed平均、ODE単位、family単位の集計を保存する。
- 必要に応じてODEまたはfamilyでcluster bootstrapする。

## 12.3 Paired comparison

同じODE、初期条件、corruption、seed、candidate budgetで条件をpaired比較する。
主比較候補:

- GRN full FT vs frozen
- GRN full FT vs official-continued FT
- top 1 / top 3 vs GRN full FT
- top 3 vs各random 3集合およびrandom集合分布
- multi-IC selection vs single-trajectory selection

## 12.4 Multiple outcomes

主要評価軸を事前に次の順へ固定する。

1. target-component skeleton recovery
2. target-component variable-aware TED
3. true skeleton in beam
4. generalization-IC failure-aware error
5. valid rate

CE、probe、CKA、個別token精度は副解析とする。

---

# 13. Phase構成

## Phase 0: Freeze / architecture / feasibility audit

目的: GPU_RUN5を実行可能な固定条件へ落とす。

実施:

- git branch / commit、dirty status
- checkpoint SHA256とarchitecture inventory
- ODEFormer upstream / vendored fingerprint
- 公開demoとGPU_RUN4 baseline smoke
- G01–G08 teacher tokenization
- target length / dimension / vocabulary audit
- `inv` / integer power decode audit
- RTX 2070でのmemory / throughput pilot
- corpus規模、seed数、主grid、効果marginの凍結
- run-idと保存schemaの凍結

## Phase 1: Closed-GRN corpus and evaluator

目的: G01–G08を閉じた多次元ODEと複数初期条件軌道へ変換する。

実施:

- regulator dynamics pool
- main / family-holdout split
- skeleton leakage audit
- input / selection / generalization IC split
- canonical / teacher equivalence tests
- target-component / system-level TED
- singularity / nonnegative / integration validation
- corpus fingerprint

## Phase 2: Frozen ODEFormer GRN baseline

目的: 適応前のgeneration supportと軌道性能を確定する。

実施:

- beam 50 full candidates
- single-trajectory official selection
- multi-IC diagnostic selection
- target / system formula metrics
- family、dimension、rational、corruption別集計

## Phase 3: Generation and selection diagnosis

目的: generation、selection、identifiabilityを分離する。

実施:

- candidate budget / diversity比較
- official / input-robust / selection-IC / multi-IC reranking
- structural oracle gap
- unique skeletonとoracle TEDのbudget curve
- failure taxonomy

## Phase 4: GRN adaptation pilot

目的: FT taskとhyperparameterをvalidationだけで固定する。

実施:

- official-continued対GRN-continued
- lr / step / corruption mixture
- frozen / full / decoder-all smoke
- validation full decode
- ODEBench forgetting check
- early stopping rule固定

## Phase 5: Decoder analysis completion

目的: GPU_RUN4で未実施だったdecoder-side解析をGRN validation panelで補う。

実施:

- decoder probe + shuffle control
- logit lens
- token-category depth curve
- decoder formula TED trajectory
- mean intervention / activation patching
- formula-level intervention decode

## Phase 6: IOLE and layer freeze

目的: 全16 blocksの適応能力をformula-levelで測り、test前に条件を固定する。

実施:

- 16 single-block FT
- formula-level IOLE ranking
- causal ranking
- top / bottom / random sets固定
- ranking stability

## Phase 7: Selective FT validation

目的: 全条件をvalidationで比較し、最終testへ進む条件を決める。

実施:

- frozen / controls / full / decoder-all / selective / random
- full candidate decode
- multi-IC selection
- GRN primary metrics
- ODEBench forgetting secondary metrics
- 最終checkpointと選択規則のfreeze

## Phase 8: Final test

目的: 固定済み条件をmain testとfamily-holdout testで一度だけ評価する。

test後に新しい条件を追加しない。追加仮説は次runへ送る。

## Phase 9: Integrated analysis and report

結果を次の三部へ分ける。

1. Frozen ODEFormerのGRN generation support
2. Multi-trajectory candidate selection
3. GRN selective fine-tuning

事実、RQ判定、考察、限界、未実施提案を明確に分ける。

---

# 14. Go / No-Go基準

## Go 1: Corpus生成

- 全teacher式がcheckpoint語彙でencodeできる。
- 全成分が指定token長内に収まる。
- split間の式・trajectory漏洩がない。
- input / selection / generalization ICが分離される。
- trajectory generation failureが理由付き保存される。

失敗時は、新tokenを追加せず、既存語彙内の代数的に同値なcompact teacher表現を先に検討する。

## Go 2: Frozen baseline

- beam候補、選択式、全trajectory、failureを保存できる。
- target-componentとsystem-level評価が一致したschemaで出力される。
- control rerankingが同一candidate setを使う。

true skeleton in beamがほぼ0の場合も結果を隠さない。その場合、selection実験を主結論にせずGRN adaptationを優先する。

## Go 3: Selective FT

validationで少なくとも1つのGRN適応条件が、事前固定したformula-level scoreをfrozenより改善すること。
CEだけの改善ではGoとしない。

改善がない場合は長いfinal testを行わず、generation support、語彙、corpus表現を再設計する。

## Go 4: Final test

- hyperparameterとearly stopping固定
- top / causal top / bottom / random集合固定
- selection scoreとcomplexity penalty固定
- candidate budget固定
- 全条件のcheckpoint provenance保存
- test未参照をmanifestで確認

## Go 5: DREAM4または実データへ進む条件

- G02–G08の非自明なHill構造で回復が生じる。
- family-holdoutでTEDまたはskeleton recoveryが改善する。
- multi-IC selectionがsingle-trajectory選択より安定する。
- generalizationとvalid rateを大きく悪化させない。
- selective FTの優位が複数random集合に対して再現する。

満たさない場合、DREAM4 Size10 / Size100へ進んで性能不足をデータ側の難しさと混同しない。

---

# 15. 保存schema

## 15.1 Provenance

- run_id / phase / status
- git branch / commit / dirty diff summary
- checkpoint path / SHA256
- upstream fingerprint
- Python / PyTorch / CUDA / GPU
- config snapshot
- seed bundle
- corpus / split / trajectory fingerprint
- start / end time

## 15.2 System record

- eq_id / family / template / split
- full true ODE system
- target-component true equation
- canonical / compact teacher expressions
- variable and gene-name mapping
- coefficient set
- regulator dynamics ID
- initial-condition role
- noise / subsampling / irregular sampling

## 15.3 Candidate record

- raw prefix / infix
- parsed / canonical / skeleton formula
- beam rank / sampling seed
- target-component and system metrics
- input / selection / generalization trajectory metrics
- complexity / variable set
- rational / Hill-pattern tags
- valid flag / failure reason
- selection scores by rule

## 15.4 Training record

- condition / trainable blocks
- trainable parameters
- optimizer / lr / steps
- data order seed
- train / validation loss trajectory
- selected checkpoint
- peak memory / wall time
- layer ranking source

集約JSONだけでなくproblem-levelとcandidate-level recordを残す。

---

# 16. 主成果物

```text
results/runs/<gpu-run5-run-id>/
  manifest.json
  config_frozen.yaml
  phase0/
  phase1/
  ...
  phase9/
  records/
    systems.jsonl
    candidates.jsonl
    failures.jsonl
    training.jsonl

graphs/<gpu-run5-run-id>/
  figures/
  tables/
```

最低限の図表:

1. generation → selection → integrationのfailure funnel
2. family別true skeleton in beam / selected skeleton recovery
3. single-trajectory対multi-IC selectionのpaired比較
4. frozen / full / selective / randomのformula-level比較
5. decoder深度に沿ったtoken rank / TED
6. reconstruction対TEDの散布図
7. input-IC対generalization-IC性能
8. parameter数・時間・回復性能のPareto図
9. 代表的成功式と代表的失敗式の表

---

# 17. 実装配置案

共通処理をGPU_RUN5直下へ複製しない。

| 種類 | 配置候補 |
|---|---|
| ODEFormer共通拡張 | `src/gpu_run5/` または再利用可能なら `src/gpu_run4/` を一般化 |
| GRN closed-system生成 | `src/data/` |
| candidate selection | `src/evaluation/` またはODEFormer共通module |
| Phase入口 | `scripts/phases/gpu_run5_phase*.py` |
| runner | `scripts/ops/run_gpu_run5.sh` |
| config | `configs/gpu_run5/` |
| campaign固有tests | `GPU_RUN5/tests/` |

GPU_RUN4コードを変更するときは、既存GPU_RUN4結果の再現経路を壊さない。必要なら共通関数を新moduleへ抽出し、GPU_RUN4互換testを残す。

---

# 18. 既知のリスクと対策

## リスク1: Hill式がcheckpoint語彙または長さ上限に収まらない

対策: 新token追加より先に、既存語彙内のcompact teacher expression、定数融合、代数的に同値な短い表現を使う。
canonical truthとteacher expressionの同値性testを必須にする。

## リスク2: Regulator dynamicsがtarget equationより強く結果を支配する

対策: familyとregulator backgroundを交差させ、target-component指標を主とし、background別感度を報告する。

## リスク3: 単一軌道で式を識別できない

対策: selection trajectoryとgeneralization trajectoryを分離し、複数初期条件selectionを主比較に含める。

## リスク4: Full FTが事前学習能力を壊す

対策: frozen、official-continued、decoder-all、selectiveを置き、ODEBench forgettingとGRN generalizationを同時に測る。

## リスク5: Beamを増やしても候補多様性が増えない

対策: candidate countだけでなくunique skeleton、oracle TED、sampling反復を測る。候補評価budgetを報告する。

## リスク6: 3次元GRNで性能が崩れる

対策: 1D、2D、3Dを分け、まずG01–G03の低次元でpipelineを確立する。3D失敗を全体平均で隠さない。

## リスク7: Test decodeの計算量が大きい

対策: smoke → validation pilot → condition freezeの順に進み、Go条件を満たさない条件をtestへ持ち込まない。
ただしvalidationで不利だった結果も保存し、恣意的除外をしない。

---

# 19. 完了条件

GPU_RUN5は次を満たしたとき完了とする。

- 公開4+12 checkpointのprovenanceを固定した。
- G01–G08を閉じたODE系として生成し、split漏洩を監査した。
- input / selection / generalization軌道を分離した。
- frozen baselineの全beam候補とfailureを保存した。
- generation failureとselection failureを分離した。
- multi-trajectory selectionをsingle-trajectory selectionとpaired比較した。
- FT hyperparameterと層集合をvalidationだけで固定した。
- full / selective / multiple random controlsをformula-levelで比較した。
- final testを一度だけ評価した。
- target-componentとsystem-levelの式・数値・安全性指標を保存した。
- 事実、推測、未支持仮説、限界を分けたreportを作成した。
- GPU_RUN4、GPU_RUN2、READMEの更新要否を確認した。

---

# 20. GPU_RUN5の研究上の位置づけ

GPU_RUN5で示したいのは、単に「ODEFormerの精度が高い」ことではない。

理想的な成果は次である。

1. ODEFormerがGRN式を候補として生成できる条件を特定する。
2. 単一軌道上で等価に見える代替式を、複数初期条件によって識別する。
3. GRN向けselective FTが、full FTより少ない更新でsymbolic recoveryを改善し、公開モデルの一般能力を保つことを検証する。

中心仮説が支持されなかった場合も、次の切り分けは独立した成果になる。

- checkpoint語彙・priorにGRN構造がない。
- GRN構造はbeam内にあるが選択できない。
- 多軌道でも識別できない。
- CEは改善するがformula recoveryへ波及しない。
- full FTとselective FTのどちらも事前学習priorを壊す。

この切り分けにより、次段階が追加事前学習、candidate selection、探索、データ取得設計、または別architectureのどれであるべきかを判断する。

---

# 21. 参照資料

- d'Ascoli et al., “ODEFormer: Symbolic Regression of Dynamical Systems with Transformers,” ICLR 2024.  
  https://openreview.net/forum?id=TzoHLiGVMo
- ODEFormer official repository.  
  https://github.com/sdascoli/odeformer
- ODEBench standalone repository.  
  https://github.com/GPBench/ODEBench
- GPU_RUN4計画: [`GPU_RUN4/plan.md`](../GPU_RUN4/plan.md)
- GPU_RUN4結果: [`GPU_RUN4/GPU_RUN4_research_report_20260819.md`](../GPU_RUN4/GPU_RUN4_research_report_20260819.md)
- GPU_RUN2計画: [`GPU_RUN2/plan.md`](../GPU_RUN2/plan.md)
- 研究全体: [`README.md`](../README.md)
