# GPU_RUN5 計画 — ODEFormerのGRN構造適応、多軌道候補選択、層解析の接続

- 作成日: 2026-08-23
- 状態: **Fixed v1.2（Phase 0 Go 1完了、前向き予測・縮退・test firewall固定）**
- 主モデル: 公開ODEFormer checkpoint（4 encoder + 12 decoder、60,646,773 parameters）
- 前世代: [`GPU_RUN4/plan.md`](../GPU_RUN4/plan.md) / [`GPU_RUN4/GPU_RUN4_research_report_20260819.md`](../GPU_RUN4/GPU_RUN4_research_report_20260819.md)
- 成立過程: [`plan-codex.md`](plan-codex.md) と [`plan-claudecode.md`](plan-claudecode.md) の2案、および相互レビューを統合した

> 本文書はGPU_RUN5の計画正本である。Phase 0のauditとpilotを終えて計算量・データ規模・効果margin・最終test条件を固定した時点で
> `status: Fixed` へ昇格させる。**test結果を見た後に、選択規則、主要指標、層集合、hyperparameter、予測を変更しない。**

---

# 0. 本計画の成立過程

GPU_RUN5には独立に作成された2つの案がある。本正本は両案の相互レビューを経て統合したものである。
どちらの案から採ったかを明示しておく。後から「なぜこの設計か」を追える状態を保つためである。

| 設計要素 | 出所 | 理由 |
|---|---|---|
| GRN corpusを実際にFTへ使う二本立て構成 | codex案 + codexレビュー | claudecode案はGRN suiteのFT利用を禁止しており、「GRN向け選択FTが式回復を改善するか」に原理的に答えられなかった |
| 多軌道（複数初期条件）候補選択 | codex案 | GPU_RUN4のgeneralization崩壊（Lotka–Volterra gen $`-2.54`$、Maxwell–Bloch gen $`-48`$）に直接対応する |
| official-continued FT対照 | codex案 | 「追加学習したこと自体の効果」と「GRN domain adaptationの効果」を分離する。GPU_RUN2 / RUN4のどちらにも無かった |
| formula-level IOLE ranking | codex案 | teacher-forcing CEで層を選び、TED / skeletonで主張する不整合を解消する |
| 語彙・token長のfeasibility audit | codex案 | GRN FTを行うなら必須のfail-fast |
| 保存済みbeam候補の先行再解析 | claudecode案 | GPU 0時間で主要な前提を確定でき、下流の設計を決める |
| 介入後beam decode | claudecode案 | 「重要層への介入で数式回復は変わるか」に3世代answerが無い |
| 事前登録した予測と反証条件 | claudecode案 | 否定的結果を事後解釈でなく報告するため |
| 3モデル横断の統合（Track E） | claudecode案 | GPU不要。現時点で最も新規性のある資産 |
| **縮退設計を計画に先に書く** | claudecode案 | GPU_RUN4は1643行の計画に対し実行はreduced版になり、層解析が検定不能な規模へ落ちた。同じ失敗を繰り返さない |
| 構造形式の分類分割と「decoded support」表記 | codexレビュー | 「変数分母がある」と「有理関数である」と「Hill型である」は別概念。beam集計から事前学習priorを断定するのは強すぎる |
| hyperparameter候補数を条件間で揃える | codexレビュー | full FTで選んだlrを単層FTへ押し付けると比較が不公平になる |
| Go条件を `selective > frozen` へ緩和 | codexレビュー | 「fullは悪化するがselectiveは改善する」はselective FTがpriorを保護した強い証拠になり得る。full改善が要るのは $`C_l`$ の分母だけ |
| 介入強度をvalidationで1つに絞ってからdecode | codexレビュー | claudecode案の「17条件・39分」は過小評価だった（zero + mean + $`\alpha`$ 4水準で最大81条件） |
| exponent-aware skeletonとHill指数一致率 | codexレビュー | GPU_RUN4のskeleton定義は整数指数をCONST化するため $`x^2`$ と $`x^4`$ が一致する。Hill係数は機構上重要 |
| preregistrationの二分 | codexレビュー | GPU_RUN4の結果を既に読んだ後の予測を厳密なpreregistrationと呼べない |

---

# 1. 方針

GPU_RUN5は、ODEFormerを本研究の中心モデルとして採用し、
**軌道への高い適合を、遺伝子制御ODEの構造回復へつなげられるか**を検証する。

中心仮説は次である。

> ODEFormerによる遺伝子制御式の回復には、
> **(i) GRN式を候補として生成できること**、**(ii) 複数軌道から真式と近似式を識別できること**、
> **(iii) 適応がGRN構造へ向くこと** の3つが必要である。
> selective fine-tuningの効果は、この3条件のどこが欠けているかを特定した後にformula-levelで現れる。

したがってGPU_RUN5は次の3段階を明示的に分離する。

1. **Generation**: 真のGRN構造をbeam内へ生成できるか。
2. **Selection / identifiability**: 真構造がbeam内にあるとき、軌道情報だけで選べるか。
3. **Adaptation**: GRN向けFTと層選択FTがgenerationと最終式回復を改善するか。

同時に、GPU_RUN4で検出力不足のまま残った**層解析を検定可能な規模へ回復し、層解析と式回復を接続する**。
これは本研究の題目（Layer-wise Analysis of Neural Symbolic Regression）が要求する中核であり、
3世代にわたって「介入後に数式がどう変わるか」を一度も測っていない。

---

# 2. GPU_RUN4から引き継ぐ確定事項

以下はGPU_RUN4で確定済みであり、GPU_RUN5では再検証しない。

| 項目 | 確定値 | 出典 |
|---|---|---|
| architecture | 公開4 encoder + 12 decoder、dim 256 / 512、16 heads、60,646,773 params | `phase0/architecture_audit.json` |
| 論文Tableとの不一致 | 4+16 / dim 512 / 約86M とは一致しない。旧Drive IDは `symbolicregression` pickle | GPU_RUN4 §1.2 |
| 評価器 | ODEBench 63式 parse 63/63、恒等canonical TED 0、prefix往復 63/63、gold 11件成功 | `phase1/eval.json` |
| `normalized_ted` | $`\mathrm{ted}_{raw}/(\mathrm{size}_{true}+\mathrm{size}_{pred})`$、多次元は `system` ノード1個追加 | GPU_RUN4 §2.3 |
| `skeleton`（世代間比較用） | 数値葉と `c_i` を `CONST` 化。**整数指数も対象**（$`x^2`$ と $`x^3`$ は一致） | 同上 |
| ODEBench再現（reduced） | valid 0.921、recon中央値 0.980、gen中央値 0.696、canonical exact 0、skeleton 0.075 | `phase2/eval.json` |
| beam診断 | true skeleton in beam 0.091、unique skeleton/beam 平均 9.19、selection取り逃がし 5/252 | `phase3/eval.json` |
| 次元依存 | dim 3 で valid 25/40、skeleton 0 | GPU_RUN4 §3.3 |

**GPU_RUN4の評価器はそのまま使う。** 定義を変えると世代間の唯一の比較可能軸を失う。
GPU_RUN5で追加する指標（§6）は、既存定義を置き換えるのではなく**併記**する。

## 2.1 実行上の前提条件

- GPU_RUN4の `results/runs/gpu_run4_phase0_01/` はgitignoreだが、Phase 0実体監査時点の実行機に存在する
  （302 files、約44 MB）。Track Aは保存済みrecordを使い、再推論しない。
- GPU_RUN4の `manifest.json` の `status` が `running` のままである（GPU_RUN4 §7）。
  Phase 1--9 manifestがすべて`complete`であることを監査したうえで、Phase 0でroot manifestを`complete`へfinalizeしてから、
  GPU_RUN5のrecordを書き始める。
- Track Aの全候補は `phase2/all_candidates.json` の `condition=odeformer` にある。
  `phase3/beam_groups.json` は252 groupの集約であり、全候補recordではない。
  `phase2/selected.json` は`odeformer` 252件と`odeformer_opt` 32件の計284件なので、主解析では前者へfilterする。

---

# 3. Phase 0で確認する事実 — ODEFormerの演算子分布

Phase 0のcheckpoint実体監査で、公開checkpointの `params.operators_to_use` が次の設定と一致することを確認した。
同時に `max_dimension=6`、`max_generated_output_len=200` を固定した。

[`generators.py:46-70`](../third_party/odeformer/odeformer/envs/generators.py) と
[`environment.py:681`](../third_party/odeformer/odeformer/envs/environment.py) より、演算子サンプリングの既定は

```
operators_to_use = "sin:1, inv:1, pow2:1, id:3, add:3, mul:1"
```

であり、unary と binary は**独立した確率プール**として正規化される（`generators.py:397-419`）。したがって

| プール | 重みが非0の演算子 | 抽選確率 |
|---|---|---|
| unary | `id` 3、`sin` 1、`inv` 1、`pow2` 1 | `id` 1/2、`sin` 1/6、**`inv` 1/6**、`pow2` 1/6 |
| binary | `add` 3、`mul` 1 | `add` 3/4、`mul` 1/4 |

**重要な含意が3つある。**

1. **`div` と `sub` は重み0であり、事前学習corpusで一度も抽選されない。** 有理式は単項 `inv`（$`1/u`$）で表現される。
2. **`inv` は単項抽選の1/6を占め、希薄ではない。** Hill式 $`x^2/(1+x^2)`$ は
   `mul(pow2(x), inv(add(1, pow2(x))))` と書け、**使用する演算子がすべて抽選集合に含まれる**。
3. したがって **GPU_RUN2がNeSymReSで提出した「事前学習priorに有理式が希薄」という推測は、
   ODEFormerには素直に一般化しない可能性が高い。** 問いは「有理式を生成できるか」から
   **「生成できるのに、なぜ正しい有理式を選べないか」** へ移る。

この修正は、claudecode案が主目的Aに置いていた仮説を弱め、**codex案の主目的B（多軌道候補選択）が
狙っていた場所こそが本命である**ことを示す。統合正本がTrack Bを主軸に据える根拠がこれである。

なお、構造判定の実装は `div` だけでなく **単項 `inv` の子を分母として扱わなければならない**（§6.1）。
claudecode案の当初定義は `div` の右子のみを見ており、この点で誤りであった。

---

# 4. 目的と非目的

## 4.1 5つのTrack

| Track | 内容 | GPU | 主な出所 |
|---|---|---|---|
| **A** | 保存済みODEBench beam候補の再解析（構造形式の分類、有理式系の層別集計） | 不要 | claudecode案 |
| **B** | 閉じたGRN benchmarkの構築、frozen baseline、**多軌道候補選択** | 中 | codex案 + claudecode案 |
| **C** | **GRN向け full / selective fine-tuning**、official-continued対照、ODEBench forgetting | 大 | codex案 |
| **D** | decoder層解析、**介入後beam decode**、formula-level layer ranking | 中 | claudecode案 + codex案 |
| **E** | GPU_RUN2 / RUN3 / RUN4 / RUN5 の指標間順位不一致の統合 | 不要 | claudecode案 |

Track A は他のすべてに先行する。GPU 0時間で Track B / C の設計前提を確定できるためである。

## 4.2 corpusの二本立て（codexレビュー修正点1）

claudecode案は「層解析corpusは公式generatorのみ」「GRN suiteはFT・層rankingに使わない」としていた。
この設計では **GRN向けselective FTが式回復を改善するか** に原理的に答えられない。修正する。

| corpus | 用途 | 層rankingへの使用 | FTへの使用 |
|---|---|---|---|
| 公式generator corpus | 一般能力のcontrol、層解析のcontrol、official-continued FT | 可（controlとして） | 可（official-continued条件） |
| **GRN train / validation** | domain adaptation、層ranking、hyperparameter選択 | **可** | **可** |
| **GRN test / family holdout** | 最終的な式回復評価 | **不可** | **不可** |
| ODEBench | 公開モデルのreference。適応前後の catastrophic forgetting 確認 | 不可 | 不可 |

## 4.3 主対象にしないもの

- 論文Table の 4+16 / 約86M ODEFormer の再現（旧Drive IDは別pickleと確定済み。発見時は別run-id）
- ODEFormerの大規模事前学習の再実行
- 新規 `hill` token の追加（embeddingと出力headの変更を伴い、公開checkpointとの比較可能性を壊す。別campaign）
- DREAM4 Size10 / Size100 全系の一括入力（§5.4）
- regulator selection と ODE discovery の同時最適化
- ヒトRNA-seqから因果的な真のODEを主張すること
- ODEFormer / NeSymReS / ND² の数値を同一表で直接順位付けすること
- 論文Figure 4のフルグリッド（$`\sigma`$ 6点 × 3 seeds）への拡大
- test結果を見ながら層、lr、step数、候補選択重みを選び直すこと

---

# 5. データ

## 5.1 D1: ODEBench（Track A、保存済みrecordの再解析）

GPU_RUN4の `phase2/selected.json` から `condition=odeformer` の252 cellを抽出し、
`phase2/all_candidates.json` から同条件の全候補（252 group × 最大50候補）を使う。
新規推論なし。

Phase 0のcanonical tree監査で、ODEBench 63系のうち**変数分母を持つ系は14系**と確定した。
当初表の#38は定数分母のみ、#60は分母なしであり、#35の`cot=cos*inv(sin)`が欠落していた。
この14系のうち代数的な有理式は9系である。

| id | dim | 内容 | 真式（抜粋） | 形式 |
|---|---|---|---|---|
| 4 | 1 | RC-circuit with non-linear resistor | `1/(1+exp(c_0 - x_0/c_1)) - 0.5` | sigmoid |
| 14 | 1 | Budworm outbreak with predation | `c_0*x_0*(1-x_0/c_1) - c_3*x_0^2/(c_2^2+x_0^2)` | **Hill n=2** |
| 15 | 1 | Budworm outbreak (dimensionless) | `c_0*x_0*(1-x_0/c_1) - x_0^2/(1+x_0^2)` | **Hill n=2** |
| 18 | 1 | Logistic with harvesting | `c_0*x_0*(1-x_0/c_1) - c_2*x_0/(c_3+x_0)` | **Hill n=1 (MM)** |
| 19 | 1 | Logistic with harvesting (dimensionless) | `x_0*(1-x_0) - c_0*x_0/(c_1+x_0)` | **Hill n=1 (MM)** |
| **20** | 1 | **Autocatalytic gene switching** | `c_0 - c_1*x_0 + x_0^2/(1+x_0^2)` | **Hill n=2、GRN** |
| **22** | 1 | **Hysteretic activation of a protein expression** | `c_0 + c_1*x_0^5/(c_2+x_0^5) - c_3*x_0` | **Hill n=5、GRN** |
| 33 | 2 | Glider | `... \| x_0 - cos(x_1)/x_0` | 変数分母 |
| 35 | 2 | Driven pendulum | `... cot(x_0) ...` | `cos(x_0)*inv(sin(x_0))`として変数分母 |
| 42 | 2 | Chlorine dioxide–iodine–malonic acid | `c_0 - x_0 - c_1*x_0*x_1/(1+x_0^2) \| ...` | **Hill型** |
| 47 | 2 | Binocular rivalry (no oscillations) | `-x_0 + 1/(1+exp(c_0*x_1-c_1)) \| ...` | sigmoid |
| 48 | 2 | Bacterial respiration | `c_0 - x_0 - x_0*x_1/(1+c_1*x_0^2) \| ...` | **Hill型** |
| 53 | 3 | Apoptosis | `c_0 - c_5*x_1*x_0/(c_9+x_0) - c_4*x_0 \| ...` | **Hill n=1** |
| 62 | 4 | Binocular rivalry with adaptation | `-x_0 + 1/(1+exp(c_0*x_2+c_1*x_1-c_2)) \| ...` | sigmoid |

**#20 と #22 は README §2.1 が定義するHill型遺伝子制御式そのものである。**
GPU_RUN4でskeleton一致した6系（1, 2, 6, 9, 12, 31）は**この14系と1つも重複しない。**
定性パネルの系62について GPU_RUN4 §3.5 は「sigmoidを線形で代用」（TED 36）と記録している。

層別軸: 形式分類（§6.1）、次元（1/2/3/4）、corruption（$`\sigma\in\{0,0.05\}`$ × $`\rho\in\{0,0.5\}`$）。

## 5.2 D2: 閉じたGRN benchmark（Track B / C）

### 5.2.1 なぜGPU_RUN2のG01–G08をそのまま使えないか

G01–G08は**対象遺伝子1個の右辺** $`f_1(x_1,x_2,x_3)`$ を定め、oracle regulatorを入力する設計である。
ODEFormerは**閉じた $`d`$ 次元系の軌道** $`\mathbf{x}(t)\in\mathbb{R}^d`$ を入力とし、$`d`$ 本の成分式を出力する。

codex案は G01–G08 に事前登録した regulator dynamics $`g_j`$ を足して閉じさせる方式を採った。
これはGPU_RUN2との系譜が繋がる利点があるが、**$`g_j`$ の選択が科学を汚染する**懸念がある。
$`g_j`$ を線形緩和にすると $`x_2,x_3`$ が固定点へ落ち、$`dx_1/dt`$ が実質1次元になって
**Hill非線形性が軌道上で励起されない**。周期入力にすれば別のregimeを測ることになる。
「GNWのtarget式に架空の背景力学をボルト留めした系」であって、GRNそのものではない。

**したがって本正本は、系全体がHill型である実在のGRNモチーフを閉じた系として構築する。**
codexレビューもこの選択（claudecode案のR系）を推奨している。

### 5.2.2 GRN family（R01–R08）

既存資産を使う。[`src/data/synthetic_grn.py`](../src/data/synthetic_grn.py) は toggle switch と repressilator を、
[`src/data/dreamlike_grn.py`](../src/data/dreamlike_grn.py) は多遺伝子Hill型RHSを持つ。

| family | dim | 構造 | 真式の形 |
|---|---|---|---|
| R01 | 1 | 自己活性化 + 分解 | $`\alpha x^n/(K^n+x^n) - \beta x + \gamma`$（ODEBench #20 / #22 と同型） |
| R02 | 1 | 自己抑制 + 分解 | $`\alpha K^n/(K^n+x^n) - \beta x`$ |
| R03 | 2 | toggle switch（相互抑制） | $`\alpha_1 K^n/(K^n+y^n) - \beta_1 x \;\mid\; \alpha_2 K^n/(K^n+x^n) - \beta_2 y`$ |
| R04 | 2 | 活性化カスケード | $`\alpha_1 - \beta_1 x \;\mid\; \alpha_2 x^n/(K^n+x^n) - \beta_2 y`$ |
| R05 | 2 | 相互活性化 | 活性化Hill × 2 |
| R06 | 3 | repressilator（環状抑制） | 抑制Hill × 3 |
| R07 | 3 | coherent feed-forward loop | 活性化Hill 2段 + AND型 |
| R08 | 3 | 2活性化因子の複合体形成 | 分母に積を含むHill |

**codexレビューのR03誤記の指摘を反映した。** claudecode案では分子に `y_in` が唐突に現れ分母は `x` だったが、
正しくは上表 R04 の形（$`dx/dt = \alpha_1-\beta_1 x`$、$`dy/dt=\alpha_2 x^n/(K^n+x^n)-\beta_2 y`$）である。

Hill係数は $`n\in\{1,2,4\}`$。パラメータはLatin hypercubeで振る。

### 5.2.3 split

| split | family当たりvariant | 合計systems | 用途 |
|---|---:|---:|---|
| GRN train | 30 | 240 | FT corpus |
| GRN validation | 10 | 80 | 層ranking、hyperparameter、選択規則、early stopping |
| GRN test | 10 | 80 | 最終評価（一度だけ） |

main splitは全splitにR01--R08を含む**parameter / trajectory holdout**であり、family skeletonの重複を許す。
system ID、parameter variant、trajectory checksumの重複は許さない。

**Family holdout view**（構造OOD）: train R01–R05 / validation R06 / test R07–R08。
G02/G03型の代数template共有と同様、R03/R05 や R07/R08 は部分templateを共有し得るため、
**canonical skeleton fingerprintを監査し、trainとtestのskeletonが実際に非重複の場合だけ structure-OOD と記載する。**
無条件に「完全なskeleton-OOD」と呼ばない。
main split用checkpointはR01–R08をtrainに含むため、family-holdout評価へ流用しない。
**family-holdoutはR01–R05だけで学習・rankingした別checkpoint**を作り、R06だけで選択した後にR07–R08を一度だけ評価する。

### 5.2.4 初期条件の役割分割（codex案 §5.5）

各systemについて初期条件を役割ごとに事前分割する。

| 軌道 | 本数 | 用途 | 選択への利用 |
|---|---:|---|---|
| input trajectory | 1 | ODEFormerへの入力 | 可 |
| selection trajectory | 2 | candidate reranking | 可 |
| generalization trajectory | 2 | 最終評価 | **不可** |

**test systemのgeneralization trajectoryを候補選択へ使わない。**
同一systemの異なる初期条件を異なる式splitへまたがせない。

### 5.2.5 軌道生成の必須要件

- `scipy.integrate.solve_ivp`（RK45、rtol $`10^{-8}`$）で真のODEを積分する。**有限差分は使わない。**
  ODEFormerは軌道を直接受け取るため微分推定が不要であり、これがGPU_RUN2のoracle条件[2]を
  **理想化ではなく設計上不要にする**点である。
- 遺伝子発現量は原則非負領域で生成する。負値へ出る系は数値的に積分できても生物学的GRN主結果から分ける。
- 発散、負値、定常点への即時収束、情報量不足（軌道分散が閾値未満）を**理由付きで棄却・記録**する。
- **生成後に都合の良い軌道だけを手作業で選ばない。** train / validation / test で同じ品質基準を適用する。
- trajectory checksum と生成設定を保存する。

### 5.2.6 corruption条件

| 要因 | 水準 |
|---|---|
| observation noise $`\sigma`$ | 0、0.05 |
| subsampling $`\rho`$ | 0、0.5 |

**計4 cell。GPU_RUN4互換。** codex案の irregular sampling（第3因子）は主gridから外す（§8 縮退設計）。
noise 0.1 と irregular sampling は stress test 候補として validation でのみ扱う。

## 5.3 D3: 層解析corpus（公式generator、Track D control）

GPU_RUN4 §7.4 の設計へ戻し、規模を検定可能な水準へ上げる。

| split | GPU_RUN4実績 | GPU_RUN5既定 | stretch |
|---|---:|---:|---:|
| official_train | 48 | 2,000 | 20,000 |
| official_validation | 16 | 500 | 5,000 |
| official_test | 16 | 500 | 5,000 |

GPU_RUN4のPhase 4は80式で99秒（約1.24 s/式）。既定3,000式は約62分、stretch 30,000式は約10時間。
**既定で開始し、throughput実測後にstretchの可否をtest前に決める。**

- skeleton漏洩をhashで監査する（train–val / train–test / val–test すべて0を要求）。
- GPU_RUN4は `gen_expr(train=True)` をtest分割にも使っていた。公式のtrain/test生成モード切替が使えるか調査し、
  使えない場合はその事実を限界として明記する。

## 5.4 D4: DREAM4（条件付き、Go 8が必要）

[`src/data/dream4_sbml.py`](../src/data/dream4_sbml.py) はSBMLの kineticLaw parameter から gene ODE を再構成し
`expression_string()` を返す。すなわち **DREAM4 size-10 は真式が復元可能**であり、symbolic recovery を測れる。

ただし2つの障害がある。

1. **次元。** size-10 は10遺伝子系である。parser default は `max_dimension=2`、
   公開checkpointの実際の上限はPhase 0で確認する。GPU_RUN4では既に dim 3 で valid 25/40・skeleton 0 まで劣化している。
   **10次元は範囲外である公算が高い。**
2. **部分系の非閉性。** 2–4遺伝子の部分ネットワークを切り出すと外部制御入力が失われ、
   その部分系の真式は元のODEと一致しない。**切り出しは「真式を持つ問題」を作らない。**

縮退の選択肢:

- **D4a**: 復元した真式がGNW公開の無ノイズ時系列を再現するかを検証するだけに留める（GPU不要、真式復元の妥当性検査）
- **D4b**: checkpointの次元上限が10以上と確認できた場合のみ、size-10 全系へ適用する
- **D4c**: 実施しない

**既定は D4a のみ。** D4b は Go 8 が通った場合のオプション。実施しない場合はレポートへ理由を明記する。

## 5.5 D5: 固定介入パネル（Track D）

介入後decodeは高価なので固定パネルを使う。**成功例を後から選ばない。**

GRN validationから、次で層別してID順に機械的に抽出する。

- dimension 1 / 2 / 3 から各8 system
- family が偏らないよう family あたり最大4 system

計 **24 system**。公式corpus validation側にも同規模の対照パネルを1つ固定する。
GRN testパネルはPhase 8の一度きりtest後にのみ診断用として生成でき、層・強度・設定の選択へ使わない。

---

# 6. 構造形式の分類と評価指標

## 6.1 形式分類（codexレビュー修正点2）

claudecode案の `rational_form` は「変数を含む分母がある式」をすべてTrueにしており、
$`1/(1+\exp(x))`$ のような**有理関数でないもの**まで含めていた。数学的な有理関数は多項式の商 $`P/Q`$ である。
またODEFormerは `div` をほぼ出さず **単項 `inv`** を出す（§3）。両方を修正し、4つのフラグへ分割する。

```text
denominator(e) = { div ノードの右子 } ∪ { inv ノードの唯一の子 }

variable_denominator_form(e)  ⟺ ある denominator 部分木が変数ノードを1つ以上含む
algebraically_rational(e)     ⟺ e 全体が P(x)/Q(x)（P, Q は多項式）へ書ける。
                                 transcendental（exp, log, sin, cos, tan, sqrt）を含めば False
hill_form(e)                  ⟺ 部分式が c·u^n/(K^n + u^n) または c·K^n/(K^n + u^n) の形
                                 （cとKは数値または定数symbol、uは単一変数、nは明示的な正整数）へ一致する。
                                 状態依存係数を掛けたmodulated Hill項は別タグとし、strict `hill_form`へ含めない
sigmoid_saturating_form(e)    ⟺ 部分式が c/(1 + exp(affine(x))) の形
```

- 多成分系では**成分ごとに判定し、系レベルは「いずれかの成分がTrue」**。成分別内訳も保存する。
- 集計は4フラグを**必ず分けて報告する**。合算した単一の「有理式率」を主表に置かない。
- 「有理式群」は `variable_denominator_form AND algebraically_rational` の積集合を
  `rational_with_variable_denominator` と明記する。$`Q=1`$の多項式をこの群へ含めない。

## 6.2 表記の規律（codexレビュー修正点2後半）

beam候補の集計から観測できるのは、**固定decode protocol（beam sampling 50、temperature 0.1）下の candidate support** である。
事前学習priorそのものではない。したがって本runの指標名・結論では次を守る。

- **使う語**: `decoded support`、`candidate support`、`generation support`
- **使わない語**: 「事前学習priorに有理式が無い」「priorが欠落している」

priorへの言及は、§3 の generator 設定という**独立の証拠**に基づく場合に限り、その旨を明記して行う。

## 6.3 構造指標（codexレビュー修正点7）

GPU_RUN4のskeleton定義は整数指数を `CONST` 化するため $`x^2`$ と $`x^4`$ が一致する。
GRNではHill係数 $`n`$ が協同性という機構を表すため、この定義だけでは不十分である。
**既存定義は世代間比較用に維持し、次を追加する。**

| 指標 | 定義 |
|---|---|
| `skeleton_exact`（継承） | GPU_RUN4定義。整数指数もCONST化。世代間比較用 |
| `exponent_aware_skeleton_exact`（新規） | 数値係数のみCONST化し、**整数指数はリテラルとして保持**して一致判定 |
| `hill_exponent_match`（新規） | 真式・予測式の双方が `hill_form` のとき、Hill指数 $`n`$ が一致する割合 |
| `numerator_ted` / `denominator_ted`（新規） | `hill_form` 部分式について分子・分母を分けたTED |

**主報告は `exponent_aware_skeleton_exact` とし、`skeleton_exact` は世代間比較の補助として併記する。**

## 6.4 Formula-level primary metrics

- canonical exact / symbolic equivalence / skeleton exact / exponent-aware skeleton exact
- variable-aware TED（normalized）、numerator / denominator TED
- variable precision / recall / F1
- coefficient error（skeleton一致時のみ）
- expression complexity
- valid rate

**成分単位（component-level）と系単位（system-level）を分けて保存する。**
family macro-average と system micro-average の両方を保存する。R01/R02（1D）と R03–R08 を分けて報告する。

## 6.5 Candidate-level metrics

true formula / skeleton in beam、oracle best TED、selected-vs-oracle TED gap、true candidate rank、
unique canonical / skeleton candidates、**4形式フラグそれぞれの candidate rate**、selection failure rate。

## 6.6 Trajectory metrics

input reconstruction、selection-IC、generalization-IC の $`R^2`$ / NRMSE、
short-horizon / long-horizon error、integration success rate、divergence time。

**平均 $`R^2`$ は大きな負の外れ値で壊れる**（GPU_RUN4の reconstruction mean $`-6.42`$）。
median、quantile、failure-aware集約を主とする。

## 6.7 Safety metrics

NaN / Inf、denominator near zero、integration divergence、negative-state violation、out-of-domain blow-up、timeout。

## 6.8 Efficiency metrics

trainable parameter count / ratio、optimizer steps、examples seen、peak GPU memory、
training wall time、decode wall time、candidate integration 回数、total candidate-evaluation budget。

## 6.9 介入後symbolic metrics（Track D）

各介入条件 $`l`$、各パネル問題 $`p`$ について

```math
\Delta\mathrm{TED}_l=\mathrm{median}_p(\mathrm{ted}_{l,p})-\mathrm{median}_p(\mathrm{ted}_{\mathrm{baseline},p})
```

同様に $`\Delta`$ skeleton exact、$`\Delta`$ valid rate、$`\Delta`$ recon $`R^2`$、$`\Delta`$ gen $`R^2`$、
$`\Delta`$ unique skeleton を記録する。**$`\Delta`$CE との順位相関がP5の判定材料である。**

---

# 7. 研究質問

| RQ | 問い | Track |
|---|---|---|
| RQ1 | 公開ODEFormerは、変数分母・Hill型制御を含むGRN式をbeam内へどの程度生成できるか（decoded support） | A, B |
| RQ2 | GRN式の回復失敗は、候補を生成できないためか、生成した候補を選べないためか | A, B |
| RQ3 | 別初期条件の軌道を候補選択へ追加すると、観測軌道上だけで合う代替式を排除できるか | B |
| RQ4 | GRN合成ODEによるFTは、同一step数の official-continued 対照より GRN式回復を改善するか | C |
| RQ5 | 少数blockのGRN向けFTは、full FTより事前学習能力を保ちながら symbolic recovery を改善できるか | C |
| RQ6 | validationで選んだtop block集合は、複数の固定random集合より formula-level 指標で良いか | C |
| RQ7 | 変数・`inv`・整数べき・乗算・加算・定数tokenの正解順位と式TEDは、decoder深度に沿ってどう変化するか | D |
| RQ8 | 層への介入は teacher-forcing CE と symbolic recovery に**同じ順序**で効くか | D |
| RQ9 | 効果は family、次元、形式、noise、subsampling、family holdout で変わるか | 全 |

**RQ8がGPU_RUN2 / RUN3 / RUN4のいずれも持っていない実験である。**

---

# 8. 予算と縮退設計

**本節が GPU_RUN4 の失敗を繰り返さないための中核である。**
GPU_RUN4は1643行の計画に対し、実行は corpus 80式・4 Adam step という**検定不能な規模**へ落ちた（GPU_RUN4 §2.1、§7）。
計画の緻密さは縮退を防がない。**縮退の形を先に決めておく。**

## 8.1 単位コスト（GPU_RUN4の実測から）

| 項目 | 実測 | 備考 |
|---|---|---|
| beam 50 推論 | 1.89 s / cell | `phase2` 選択recordの中央値 |
| 評価・積分・opt込み | 4.43 s / cell | 1116 s / 252 cell |
| 多軌道（5 IC）込み | 約7 s / cell | 積分コストが約5倍 |
| corpus生成 | 1.24 s / 式 | `phase4` 99 s / 80式 |

## 8.2 主要な実行単位

| 単位 | 規模 | 概算 |
|---|---:|---:|
| GRN full evaluation（80 system × 4 corruption × 3 seed） | 960 decode | **約1.9 h** |
| GRN reduced panel（24 system × 4 corruption × 1 seed） | 96 decode | **約11 min** |
| 介入後decode（24 × 17条件 × 3 seed） | 1,224 decode | **約2.4 h** |
| 公式corpus生成（3,000式） | — | 約62 min |

## 8.3 事前に決めた縮退規則

| 項目 | 上限案 | **本runの既定** | 縮退の根拠 |
|---|---|---|---|
| corruption | 8 cell（irregular含む） | **4 cell** | GPU_RUN4互換を保ち、irregular は validation stress test へ |
| seed | 5 bundle | **3 bundle** | n=3のt区間の広さを明記し、margin判定を主結論にしない |
| GRN test systems | 160 | **80** | family 8 × 10 variant |
| IOLE の validation 評価 | 16 block × full validation | **16 block × reduced panel**、上位・下位・random の finalist のみ full validation | 30 h → 3 h |
| hyperparameter探索の評価 | full validation | **reduced panel + validation CE** | 同上 |
| **最終testへ進むFT条件** | 10条件 | **5条件**（frozen / official-continued / GRN full / GRN top-k best / GRN random 代表1） | 19 h → 10 h |
| 介入方式 × 強度のdecode | 最大81条件 | **validation CEで非飽和な1方式1強度を選び、17条件のみdecode** | codexレビュー修正点5 |
| 公式corpus | 30,000式 | **3,000式**、throughput実測後にstretch判断 | 10 h → 1 h |

**残る5条件は validation 限りで報告する。** codex案 §18 リスク7 の原則
「validationで不利だった結果も保存し、恣意的除外をしない」は保持したまま、**test の予算だけを削る**。

## 8.4 総予算の見積り

| Track | 概算GPU時間 |
|---|---:|
| A | 0（CPU数分） |
| B（GRN corpus生成 + frozen baseline + 多軌道選択診断） | 約6 h |
| C（hyperparameter + IOLE + selective FT validation + final test） | 約45 h |
| D（公式corpus + probe/lens + 因果 + 介入後decode） | 約12 h |
| E | 0 |
| **合計** | **約63 h** |

RTX 2070 専有で3–4日。**Phase 0 のthroughput pilot で実測し、乖離が2倍を超えたら §8.3 の縮退を1段深める。**

2026-08-23のprovisional pilot（dirty treeのためGo 1には不使用）では、RTX 2070上のbeam 50が
1.78秒/cell、1 forward/backwardが0.179秒、peak allocated VRAMが約0.97 GBだった。
beam推論は§8.1のGPU_RUN4実測1.89秒/cellと整合し、2倍超過ではないため、**§8.3の既定縮退を維持する。**
同一candidate seedでは候補集合が再現し、異なるseedでは候補集合が変わることも確認した。
authoritative Phase 0はcommit `472fa4fd`、run-id `gpu_run5_20260823_472fa4fd` のclean treeで再実行し、
全Go 1条件を満たした。beam 50は1.77秒/cell、1 forward/backwardは0.143秒、peak allocated VRAMは約0.97 GB、
teacher tokenizationはR01--R08 × $`n\in\{1,2,4\}`$ の24条件すべてでroundtrip数値誤差0だった。

---

# 9. 多軌道候補選択（Track B、codex案 §8）

## 9.1 Candidate budget

主条件は GPU_RUN4 互換の beam sampling 50、temperature 0.1。

generation diversity の副比較（validation のみ）: 1回sampling 50候補 / 独立sampling複数回で計50 / 計200 / temperature 候補。
候補数が異なる条件は**推論時間と candidate evaluation 回数も報告する**。
beamを増やした場合、selected score だけでなく **unique skeleton 数と oracle TED が改善したか**を確認する。

## 9.2 Selection条件

同一candidate setから選ぶ。

| # | 規則 | 内容 |
|---|---|---|
| 1 | `official_reconstruction` | input trajectory の再積分 $`R^2`$（GPU_RUN4互換） |
| 2 | `input_robust` | input trajectory の failure-aware normalized error |
| 3 | `selection_ic` | 独立 selection trajectory の error |
| 4 | `multi_ic` | input + selection trajectories の robust 集約 |
| 5 | `multi_ic_complexity` | multi-IC error + validationで固定した complexity penalty |
| 6 | `structural_oracle` | ground truth TED 最小（**診断専用**。実運用の成績へ混ぜない） |

主 multi-trajectory score:

```math
S(f_k)=\mathrm{median}_{j\in\mathcal{J}_{\mathrm{select}}}\left[\mathrm{NRMSE}\!\left(\hat{\mathbf{x}}_{k,j},\mathbf{x}_j\right)\right]+\lambda C(f_k)
```

$`\lambda`$、集約方法（median / trimmed）、failure penalty は **validationだけで固定する**。積分失敗を除外しない。

## 9.3 Failure taxonomy

- `generation_failure`: true skeleton が candidate set に無い
- `selection_failure`: candidate set にあるが選択されない
- `integration_failure`: parse可能だが selection trajectory を積分できない
- `metric_failure`: score を有限値として計算できない

system / component / seed / corruption 単位で保存する。

**GPU_RUN4の「取り逃がしは5/252だから選択は主因でない」という結論は、
真skeletonがbeam内にある場合に限った話である。** oracle TED 14.31 対 selected TED 17.26 という差は、
真skeletonが無いbeamでも「より近い木」を選び損ねていることを示す。多軌道選択はここを狙う。

---

# 10. Fine-tuning設計（Track C）

## 10.1 語彙とtoken長の feasibility（codex案 §6.2、Go 3）

新 `hill` token を追加しない。Hill式を既存語彙の `add`、`mul`、`inv`、整数べき、変数、定数で表現する。
Phase 0で次を **fail fast** 確認する。

- R01–R08 の compact teacher expression が語彙へencodeできる
- target token length が checkpoint の上限内である
- 1–3変数の閉じたODE系を入力・出力できる
- **`inv` と整数べきが decode 候補として mask されていない**
- 多成分区切りと成分順が保存される
- canonical truth と teacher expression が**代数的に同値である**（test必須）

失敗時は、新token追加より先に compact teacher expression、定数融合、代数的に同値な短い表現を検討する。

## 10.2 FT corpus条件

| 条件 | 学習データ | 目的 |
|---|---|---|
| frozen | なし | 公開checkpoint baseline |
| **official-continued** | 公式generator分布 | **追加stepだけの効果を分離する対照** |
| GRN-adapted | GRN train | GRN構造適応 |

Family holdout view では R07 / R08 を一切FTに使わない。

## 10.3 学習目的と model selection（codexレビュー修正点3）

学習の目的関数は正解prefix列の teacher-forcing CE とする。
**ただし model selection と early stopping は CE で行わない。**
主張を TED / skeleton で行いながら CE で選ぶのは不整合である。

- **model selection / early stopping の基準**: GRN validation の **failure-aware formula score**
  （定義は §6.4 の主要軸から Phase 0 で1つに固定し、test前に凍結する）
- CE は補助指標として保存する
- token category 別CE（variable / `inv` / integer power / mul / add-sub / constants / separator / EOS）も保存する

## 10.4 Hyperparameter探索の公平性（codexレビュー修正点3）

GPU_RUN4は lr $`10^{-4}`$ × 4 step の1点のみだった。GPU_RUN2は探索したと記述しながら実施していなかった（README §11.3）。
claudecode案は full FT で選んだ点を全単層条件へ押し付ける設計であり、これも不公平だった。**修正する。**

- 候補: lr $`\{10^{-6},10^{-5},10^{-4}\}`$ × steps $`\{50,200,1000\}`$ = 9候補
- **各 trainable 条件へ同数の候補を与える**（full、decoder-all、single-block、selective のいずれも9候補）
- 探索は GRN validation の reduced panel（§8.3）で行い、finalist のみ full validation で確認する
- 探索結果は**負けた条件も含めて全て保存する**
- smoke で明らかに無効または OOM となる条件を除いた後、validation実行前に最終gridを凍結する

## 10.5 Step-matched と time-matched

主比較は同じbatch、data order、optimizer step数を使う **step-matched** とする。
副解析として wall time または parameter-update量を揃えた比較を行ってよい。
**どちらを主比較とするかを結果後に入れ替えない。**

## 10.6 選択FT条件

| 条件 | 層 |
|---|---|
| frozen | なし |
| official-continued full | 全パラメータ（公式分布） |
| GRN full | 全パラメータ |
| GRN decoder-all | decoder 12 block |
| GRN top1 / top3 | IOLE formula rank 上位 |
| GRN causal_top3 | 介入後 formula 劣化 上位 |
| GRN bottom3 | 最下位3 |
| GRN random3 × **5集合** | **test前に固定。上位集合との重複数を記録する** |

GPU_RUN2ではrandom対照が1集合で上位3層と2/3重複していた（README §9.7）。GPU_RUN4は3集合。
**GPU_RUN5は5集合とし、random-set variance を推定する。**
最終testへ送るrandom代表はvalidation成績で選ばず、事前に`random3_0`へ固定する。

---

# 11. 層解析設計（Track D）

## 11.1 対象block

公開checkpointの全16 Transformer blocks（encoder 4 + decoder 12）。
**「16 decoder層」「20層」と記載しない。**

## 11.2 Probe

| 対象 | GPU_RUN4 | GPU_RUN5 |
|---|---|---|
| encoder 4層 pooled hidden | dimension分類、complexity回帰、`has_sin` | 継続 + 形式フラグ分類（§6.1）を追加 |
| **decoder 12層 hidden** | **未実施** | next token分類、演算子カテゴリ分類、木の深さ回帰、形式フラグ分類 |

- **label-shuffle control task を全タスクへ置く。** GPU_RUN2はこれを欠き、probeスコアが
  「層の情報」か「probeの表現力」かを分離できなかった（README §11.2）。
- **token pseudo-replication を防ぐ。** decoder hidden は1式あたり数十token出る。
  probe の fit / 評価は**式単位で分割**し、式内tokenは同一splitへ入れる（GPU_RUN4 §19.7）。
- $`n_{val}`$ は 500式。GPU_RUN4の16式から大幅に増え、IOLE差 $`10^{-3}`$ の有意性が初めて議論可能になる。

## 11.3 DecoderLens / decoder-side readout

- **encoder intermediate decoding**: encoder各層の出力をPMA pooling（`outatt`）へ通して decoder の
  cross-attention memory として与える。[`src/interpretability/decoder_lens.py`](../src/interpretability/decoder_lens.py) を移植。
  **限界を明記する**: decoder は最終encoder表現を受け取るよう学習されており、これは distribution shift である。
  パース率の絶対値を通常のdecode性能として読まない。層間の**相対比較にのみ**使う（README §6.3）。
- **decoder-side intermediate readout（logit lens）**: decoder各層のhiddenを最終層のoutput projectionへ通す。
  RQ7 の主データ。GPU_RUN3はこの型の解析で「TEDが 31.1 → 8.9 へ急変する」構造形成を捉えている。
- **token category 別の正解token順位**と、**decoder深度に沿った greedy formula TED** を保存する。

## 11.4 CKA / gradient

- CKA は encoder 内・decoder 内をそれぞれ計算する。**cross-module CKA は主張に使わない**（GPU_RUN4 §19.8）。
  GPU_RUN4では encoder CKA が全対 0.921–0.978 と飽和していた。
  **CKAは補助指標であり、層rankingに使わない**と事前に決める。
- gradient norm は GPU_RUN4 で $`10^{-8}`$–$`10^{-6}`$ と極小だった。
  **層ごとのパラメータ数で正規化した値と生の値の両方**を保存する。

## 11.5 IOLE（codex案 §10.3）

各blockを1つだけ trainable にし、**同じデータ順・step数・hyperparameter候補数**でFTする。

**IOLE ranking の主scoreは GRN validation full decode の failure-aware formula score とし、CE順位は副指標とする。**
score の正確な定義は test 前に固定する。

$`C_l=(L_{\mathrm{base}}-L_l)/(L_{\mathrm{base}}-L_{\mathrm{full}})`$ は full が base を上回るときのみ計算する。
不成立の場合（GPU_RUN2で実際に発生し contribution が全層NaNになった）は
**正規化寄与度を報告せず、raw score の順序としてのみ読む。**

## 11.6 Layer ranking

主top集合は GRN validation の IOLE formula score。causal top集合は介入後の formula 劣化で**別に**定義する。
probe / gradient / CKA / CE は補助的整合性として扱い、**一つの曖昧な総合順位へ無理に統合しない。**

保存するrank: IOLE formula rank、teacher-forcing CE rank、causal intervention rank、decoder lens rank、
encoder-only / decoder-only rank、**tie-aware rank group**。

---

# 12. 因果的層解析と介入後decode（Track D）

## 12.1 介入方式

| 方式 | 内容 | GPU_RUN4 |
|---|---|---|
| residual-zero ablation | attention / FFN 残差を0にする | 実施済み。encoder_3 で $`\Delta`$CE 10.40 |
| mean-activation patching | 活性化を corpus 平均へ置換 | **未実施** |
| 補間 patching | $`\tilde h=(1-\alpha)h+\alpha\bar h`$、$`\alpha\in\{0.25,0.5,0.75,1.0\}`$ | **未実施** |
| fixed-pair activation patching | 対応づけた別入力の活性化へ差し替え | **未実施** |

zero ablation は学習時に一度も経験しない状態へモデルを追い込むため、「その層の機能」ではなく
「壊れたモデルの挙動」を測る危険がある（README §6.4）。
GPU_RUN4の encoder_3 の $`\Delta`$CE 10.40 は他層より桁違いであり、この危険が現実化した可能性が高い。
**hard zero ablation 単独で機能分解を主張しない。**

## 12.2 介入強度の絞り込み（codexレビュー修正点5）

claudecode案は「16層 + baseline = 17条件、39分」としていたが、
zero + mean + $`\alpha`$ 4水準を全てdecodeすると **最大81条件**であり、数時間規模になる。**手順を分ける。**

1. **CEスイープ（安価）**: 16層 × (zero, mean, $`\alpha`$ 4水準) = 96条件の teacher-forcing CE を validation で計算する。decodeしない。
2. **強度の選定**: $`\Delta`$CE が**飽和していない**（層間の順序が識別できる）方式・強度を **1つ**選ぶ。
   全方式で飽和する場合は Go 5 を通さず、介入設計を見直す。
3. **decode（本番）**: baseline + 16層 × 選定した1方式 = **17条件**を、固定パネル24問題 × 3 seed で beam 50 decode する。
4. **robustness確認**: 上位3層に限り zero ablation でも decode し、方式依存でないことを確認する（3 × 24 × 3 = 216 decode）。

予算: CEスイープ 数十分、本番decode **約2.4 h**、robustness 約15分。

## 12.3 control hook

GPU_RUN4の `control_hook_ok: true`（恒等hookがbaselineを変えない）を**全介入方式で**検証する。

---

# 13. 事前固定した予測

**codexレビュー修正点6を反映し、2種類に分ける。**
GPU_RUN4の結果と一部の予測式を既に読んだ後の項目を、厳密な preregistration と呼ばない。

## 13.1 R群: 保存済みデータに対する事前固定済み再解析プロトコル

これらは preregistration ではなく、**集計方法を結果を見る前に固定する**ためのものである。

| # | 集計 | 事前に固定する内容 |
|---|---|---|
| **R1** | ODEBench 14系（変数分母）の形式別内訳 | §6.1 の4フラグで分類し、Hill / sigmoid / その他を分けて報告する |
| **R2** | selected 予測と全beam候補（約12,600件）の形式別 candidate support | 4フラグそれぞれの率を、真式の形式・次元・corruption で層別する |
| **R3** | 有理式系 対 非有理式系の skeleton / exponent-aware skeleton / TED / recon / gen | 有理式側の skeleton exact を 0 と仮定せず、そのまま報告する |
| **R4** | ODEBench beam候補の `variable_denominator_form` 率 | 保存済み候補に対するretrospective hypothesisとして5%以上かを判定する |
| **R5** | 変数分母14系（56 cell）の exponent-aware skeleton exact | 保存済みselectedに対するretrospective hypothesisとして0件かを判定する。candidate内truth supportも別に報告する |

## 13.2 P群: 新規データ・新規実験に対する前向き予測

**Phase 0で数値つきでcommitし、その後は変更しない。** Phase 9で「的中 / 外れ / 判定不能」を機械判定する。

| # | 予測 | 反証条件 |
|---|---|---|
| **P3** | GRN test（R01–R08）の frozen `exponent_aware_skeleton_exact` は **0.05未満**である | 0.05以上なら ODEFormer は既にGRN構造を回復できており、本研究の主課題が変わる |
| **P4** | GRN test の frozen reconstruction $`R^2`$ 中央値は **0.85以上**である一方、P3 は成立する（当てはまるが構造は違う） | recon中央値が0.85未満なら、失敗の原因は構造ではなく軌道の当てはめ自体であり解釈が変わる |
| **P5** | 介入後decodeで、$`\Delta`$CE 順位と $`\Delta`$TED 順位の Spearman $`\rho`$ は **0.5以下**である（CEで測った層重要度は式回復の層重要度と別物） | $`\rho>0.5`$ なら CE は symbolic recovery の妥当な代理指標であり、GPU_RUN4の層順位を読み直せる |
| **P6** | multi-IC selection は single-trajectory selection に対し、generalization-IC の failure-aware error を **改善する**（paired比較で95%区間が0を跨がない） | 改善しなければ、GRNの識別不能性は初期条件の追加では解けない |
| **P7** | GRN selective FT は GRN full FT より formula-level score が良く、かつ ODEBench forgetting が小さい | 逆なら「少数層FTがpriorを保護する」というGPU_RUN2の解釈がODEFormerで否定される |

**retrospective R4とR5がともに成立する組み合わせが、本runの中心シナリオである。**
その場合、研究の主課題は「有理式priorの欠落」から **「有理式を出せるのに正しいものを選べない／正しい指数を出せない」** へ移る。

---

# 14. 研究上の絶対条件

## 14.1 Validation / test分離

- corpus生成後、**ODEまたはskeleton単位**で train / validation / test へ分ける。trajectory行や時点をランダムにsplitしない。
- 層ranking、hyperparameter、FT step数、候補選択重み $`\lambda`$、early stopping、介入強度は **validationだけで決める**。
- final test は条件を固定した後に**一度だけ**評価する。
- test式、test family、test初期条件を ranking へ使わない。
- **test system の generalization trajectory を候補選択へ使わない。**

## 14.2 ODEBenchを適応データにしない

ODEBench は公開checkpointの reference 評価に使い、FT corpus・層選択・hyperparameter選択には使わない。
適応後の ODEBench 評価は **catastrophic forgetting を測る secondary outcome** とする。

## 14.3 数値fitと式回復を分ける

高い reconstruction $`R^2`$ を式回復と呼ばない。§6.4–6.7 をすべて別々に保存・報告する。

## 14.4 Generation と selection を分ける

selected formula だけでなく全候補を保存する。**ground truth を使う oracle は診断専用**とし、実用条件の成績に混ぜない。

## 14.5 相関的解析と介入的解析を混同しない

probe / CKA（相関）と ablation / patching（因果）は別の量を測る。不一致は矛盾ではない。
**「介入後CE」と「介入後symbolic recovery」も別指標として報告する。** 両者の不一致自体が RQ8 への回答である。

## 14.6 Failureを隠さない

parse失敗、NaN、Inf、積分失敗、timeout、特異点を problem 単位で保存する。
成功候補だけの中央値に加え failure-penalized 指標を主表へ含める。全候補が失敗した problem を集計から除外しない。
GPU_RUN4の失敗タグに `intervened_decode_failure` と `form_classification_failure` を追加する。

## 14.7 条件比較を公平にする

同一seed内の条件は同じ初期checkpoint、data order、trajectory、candidate budget を使う。
**各trainable条件へ同数のhyperparameter候補を与える。** wall time / peak memory / trainable parameter数を保存する。
random block集合は test 前に5集合固定する。

## 14.8 世代間で数値を混ぜない

- GRN benchmark（R01–R08）は GPU_RUN2 の GNW G01–G08 と**別の生成物**である。
  閉じた系、軌道入力、oracle変数なし、有限差分なし、の4点で設計が異なる。同一表に置かない。
- GPU_RUN4 の ODEBench 数値と Track A の再解析は **同一recordの再集計であるため混ぜてよい**。
  再推論した場合は別run-idとして扱う。

---

# 15. Phase構成

run-id: `gpu_run5_<yyyymmdd>_<commit8>`。Phase単位でresume可能にする。

## Phase 0: Freeze / audit / feasibility / 予測登録

目的: **GPU_RUN5の主張を後から動かせない状態にする。**

- LANSR commit・vendored ODEFormer Git tree / directory fingerprint・dirty status の固定
- checkpoint SHA256 と architecture inventory の再監査（parser default を根拠にしない）
- **checkpoint の `params` から `operators_to_use`、`max_dimension`、`max_generated_output_len` を読み、§3 の記述を検証・訂正する**
- GPU_RUN4 `results/runs/gpu_run4_phase0_01/` の同期と finalize 完走（`status: complete`）
- **§6.1 の4形式フラグと §6.3 の構造指標の定義を凍結**
- **§13.2 の前向き予測 P3–P7を数値つきでcommit**
- R01–R08 teacher tokenization / target length / `inv`・整数べきの decode mask audit（§10.1）
- RTX 2070 での memory / throughput pilot → §8.3 の縮退規則の適用判断
- corpus規模、seed数、主grid、model selection score、run-id、保存schema の凍結

Go: **Go 1**。予算: **1日、GPU ほぼ不要**。

---

## Phase 1: Track A — ODEBench再解析

- `phase2/selected.json` の `condition=odeformer`（252 cell）と
  `phase2/all_candidates.json` の同条件（約12,600候補）へ4形式フラグを付与
- R1–R5 の集計を実行、retrospective R4・R5 を判定
- 変数分母14系の予測式を定性表として保存（系62「sigmoidを線形で代用」TED 36 を含む）

主成果: `phase1/decoded_support.json`、形式別比較表。
Go: **Go 2**。予算: **数分、GPU不要**（同期不能なら Phase 2 再推論で約20分）。

---

## Phase 2: Track B — 閉じたGRN corpus と評価器

- R01–R08 × variant を生成、数値積分で軌道化、棄却理由を記録
- main split のsystem / parameter variant / trajectory漏洩監査、family holdout splitの
  **canonical skeleton fingerprint による構造重複監査**
- input / selection / generalization IC の分割
- canonical truth と teacher expression の代数的同値test
- component-level / system-level TED の算出経路確認
- 特異点・非負性・積分の検証、corpus fingerprint 保存

Go: **Go 3**。予算: **CPU数十分**。

---

## Phase 3: Track B — frozen GRN baseline と生成/選択診断

- beam 50 全候補保存、single-trajectory official selection
- §9.2 の6規則による reranking（同一candidate setを使う）
- candidate budget / diversity 比較（validation のみ）
- structural oracle gap、unique skeleton と oracle TED の budget curve
- failure taxonomy（§9.3）
- validation上でgeneration / selectionを診断し、P6を判定する。
  **P3・P4のGRN test判定は行わず、Phase 8の一度きりtestへ送る**

主成果: generation → selection → integration の failure funnel。
Go: **Go 4**。予算: **約4 h**。

---

## Phase 4: Track D — 公式corpus と観測的層解析

- 公式generator から 2,000 / 500 / 500 を生成、skeleton漏洩監査、teacher-forcing CE baseline
- encoder 4層 + **decoder 12層** の probe（label-shuffle control 付き、式単位分割）
- gradient norm（正規化・生の両方）、CKA（module内のみ）
- encoder intermediate decoding、decoder-side logit lens、token category 深度曲線、greedy formula TED 軌跡
- **固定介入パネル（GRN validation 24 + 公式corpus validation 24）を生成し凍結**。
  GRN testは強度・causal top選定に使わず、Phase 8の最終評価後に限って診断する
- throughput 実測 → stretch corpus の可否を test 前に決定

予算: **約3 h**。

---

## Phase 5: Track D — 因果解析と介入後decode

- §12.2 の4手順: CEスイープ96条件 → 強度選定 → 17条件decode → 上位3層のzero robustness
- validation固定パネルで $`\Delta`$CE と $`\Delta`$TED / $`\Delta`$skeleton / $`\Delta`$gen $`R^2`$ の順位相関（**P5 を判定**）
- causal top集合を formula-level 劣化で定義し、validation で凍結

Go: **Go 5**。予算: **約3 h**。

---

## Phase 6: Track C — GRN適応 pilot と hyperparameter 固定

- official-continued 対 GRN-adapted
- lr × steps 9候補を**各trainable条件へ同数**（reduced panel で screening）
- frozen / full / decoder-all の smoke
- model selection score と early stopping 規則の凍結（**CEではなく formula score**）
- ODEBench forgetting check の経路確認

予算: **約12 h**。

---

## Phase 7: Track C — IOLE と layer freeze

- 16 single-block FT を同一条件で実行（reduced panel 評価）
- finalist（top / bottom / random 5集合）を full validation で評価
- IOLE formula ranking、causal ranking、tie-aware rank group
- $`C_l`$ の分母成立を確認。不成立なら raw score 順序のみ
- ranking stability（3 seed の Spearman / Kendall）
- **top / causal top / bottom / random 5集合を test 前に凍結**

予算: **約15 h**。

---

## Phase 8: Track C — selective FT validation と最終test

- validation: frozen / official-continued / GRN full / decoder-all / top1 / top3 / causal top3 / bottom3 / random3 × 5
- multi-IC selection を適用した full candidate decode
- GRN primary metrics + ODEBench forgetting secondary metrics
- **最終testへ進む5条件を凍結**（§8.3）
- **final test を main test と family-holdout test で一度だけ評価**（**P3・P4・P7 を判定**）

test後に新しい条件を追加しない。追加仮説は次runへ送る。
Go: final test の前に **Go 6**（selective FT を主張として報告できるか）と **Go 7**（凍結の確認）、
test 後に **Go 8**（DREAM4・実データへ進むか）。予算: **約20 h**。

---

## Phase 9: 統合解析とreport

- 前向き予測P3–P7とretrospective R4–R5の判定を機械出力（`preregistration_outcome.json`）
- Result A（decoded support）、B（GRN generation / selection）、C（GRN適応と層FT）、D（層解析）、E（3モデル横断）を分離
- **Track E**: GPU_RUN2 / RUN3 / RUN4 / RUN5 の指標間順位不一致の統合表と図（GPU不要）
- 事実 / RQ判定 / 考察 / 限界 / 未実施提案 を明確に分ける

---

# 16. 統計設計

## 16.1 Seed

**3 paired seed bundles を既定とする**（§8.3）。各bundleは data / trajectory-IC / model-dropout /
candidate-sampling / corruption / random-layer-set の各seedを持つ。

n=3 では95% Studentのt区間は自由度2で非常に広い（README §11.1）。
**margin同等性や安定した優位を強く主張しない。** 点推定と区間を併記し、区間の広さを明示する。
「候補が1件も出ない」のような**率が0か非0かの質的判定**は n=3 でも十分に強い。

## 16.2 集計単位

- token を独立標本としない
- **同一ODEの複数初期条件を独立な式回復標本として水増ししない**
- component 指標と system 指標を分ける
- seed 平均、ODE 単位、family 単位の集計を保存する
- 必要に応じて ODE または family で cluster bootstrap する

## 16.3 Paired comparison

同じODE・初期条件・corruption・seed・candidate budget で比較する。主比較:

- GRN full FT 対 frozen
- **GRN full FT 対 official-continued FT**（domain adaptation の効果の分離）
- top1 / top3 対 GRN full FT
- top3 対 各 random 3集合および random 集合分布
- **multi-IC selection 対 single-trajectory selection**

## 16.4 Multiple outcomes

主要評価軸を**事前に**次の順へ固定する。

1. component-level `exponent_aware_skeleton_exact`
2. component-level variable-aware TED
3. true skeleton in beam（decoded support）
4. generalization-IC failure-aware error
5. valid rate

CE、probe、CKA、個別token精度は**副解析**とする。

## 16.5 報告

- 未罰則値と penalized 値の両方を報告し、どちらが主かを明記する（GPU_RUN4 §7 の混乱を繰り返さない）
- 率には Wilson 区間を使う（正規近似は0や1の近くで壊れる）
- 失敗タグの内訳を必ず併記する
- **tie-aware ranking を使う。** GPU_RUN2では罰則値への飽和で Spearman = 1.0 が見かけ上出た（README §6.7）

---

# 17. Go / No-Go基準

## Go 1: Phase 0 完了

- checkpoint SHA256・architecture・`operators_to_use`・`max_dimension` を実体から確認した
- GPU_RUN4 の finalize が完了し `status: complete` である
- 形式フラグと構造指標の定義を凍結した
- **前向き予測 P3–P7をcommitした**
- R01–R08 の teacher 式が語彙でencodeでき、token長上限内である
- throughput pilot を実施し、§8.3 の縮退判断を記録した

## Go 2: Track A 完了 → Track B の設計確定

- 252 cell と全beam候補に形式判定が付き、失敗が理由付きで保存されている
- retrospective R4・R5の判定と、candidate内truth supportが出ている
- **R4 が成立（`variable_denominator_form` 率 5%以上）した場合**: 中心の問いを
  「生成できるのに選べない／正しい指数を出せない」として Track B を予定どおり進める
- **R4 が不成立の場合**: §3 の generator 読解か checkpoint 設定が想定と異なる。
  Phase 0 へ戻って `operators_to_use` を再確認し、記述を訂正してから進む

## Go 3: GRN corpus 生成

- 全 teacher 式が checkpoint 語彙でencodeでき、token長上限内である
- canonical truth と teacher expression が代数的に同値である
- main split間にsystem ID・parameter variant・trajectory漏洩がない
- family holdoutのtrainとtestにcanonical skeleton fingerprint重複がない場合だけstructure-OODと表記し、
  重複があればその件数を保存して部分的family holdoutと表記する
- input / selection / generalization IC が分離されている
- trajectory generation failure が理由付きで保存されている
- 軌道の棄却率が 30% 未満である（超えたら §18 No-Go）

## Go 4: frozen GRN baseline

- beam候補・選択式・全trajectory・failure を保存できている
- component-level と system-level が一致した schema で出力される
- control reranking が同一 candidate set を使っている

**true skeleton in beam がほぼ0でも結果を隠さない。** その場合、selection 実験を主結論に置かず
Track C（GRN adaptation）を優先する。

## Go 5: 介入後decode

- control hook が全介入方式で baseline を変えない
- **$`\Delta`$CE が飽和していない方式・強度が少なくとも1つ存在する**
- 固定パネルが Phase 4 で凍結済みで、成功例の事後選択が起きていない

全方式で飽和する場合は decode を行わず、介入設計を見直す。

## Go 6: selective FT を主張として報告する条件（codexレビュー修正点4）

**claudecode案の「full が frozen を上回ること」は要求しない。** その条件は $`C_l`$ の分母にのみ必要である。
「full は frozen より悪いが selective は frozen より良い」という結果は、
**selective FT が事前学習priorを保護した強い証拠**になり得る。

Go条件を次へ変更する。

> **GRN validation の formula-level score で、少なくとも1つの GRN 適応条件が
> frozen と複数の random 3集合の両方を上回ること。CEだけの改善では Go としない。**

満たさない場合は長い final test を行わず、generation support・語彙・corpus 表現を再設計する。

## Go 7: final test

hyperparameter・early stopping・top / causal top / bottom / random 集合・selection score と $`\lambda`$・
candidate budget が凍結済みで、全条件の checkpoint provenance が保存され、
manifest で **test 未参照**が確認できること。

## Go 8: DREAM4 または実データへ進む条件

- R03–R08 の非自明なHill構造で回復が生じる
- family holdout で TED または exponent-aware skeleton recovery が改善する
- multi-IC selection が single-trajectory 選択より安定する
- generalization と valid rate を大きく悪化させない
- selective FT の優位が複数 random 集合に対して再現する
- （D4b の場合）checkpoint の `max_dimension` が 10 以上である

満たさない場合、DREAM4 へ進んで**性能不足をデータ側の難しさと混同しない。**

---

# 18. No-Go / redesign

次のいずれかが起きたら Phase を止め、計画を書き直す。

- GRN 軌道の 30% 以上が定常張り付きまたは発散
- teacher 式が語彙または token長上限に収まらない（新token追加より先に compact 表現を検討する）
- 介入後decode の valid rate が baseline で 0.5 未満（パネル設計の失敗）
- 拡大corpusでも IOLE 差が雑音水準のままで、seed 間順位相関が 0 近傍
- **throughput pilot の実測が §8.4 の見積りの2倍を超える**（§8.3 の縮退を1段深める）
- 前向き予測P3–P7のうち3つ以上が外れる（前提の理解が誤っている。再解釈してから進む）

---

# 19. 保存schema

## 19.1 Provenance

run_id / phase / status、git branch / commit / dirty diff summary、checkpoint path / SHA256、
upstream fingerprint、Python / PyTorch / CUDA / GPU、config snapshot、seed bundle、
corpus / split / trajectory fingerprint、start / end time。

## 19.2 System record

eq_id / family / template / split、full true ODE system、component-level true equations、
canonical / compact teacher expressions、variable と gene name の対応、coefficient set、
Hill指数、initial-condition role、noise / subsampling。

## 19.3 Candidate record

```json
{
  "candidate": {
    "raw_prefix": "...", "infix": "...", "canonical": "...", "skeleton": "...",
    "exponent_aware_skeleton": "...",
    "beam_rank": 7, "sampling_seed": 101,
    "form": {
      "variable_denominator_form": true,
      "algebraically_rational": true,
      "hill_form": true,
      "sigmoid_saturating_form": false,
      "denominator_sources": ["inv"],
      "hill_exponent": 2
    },
    "component_metrics": {},
    "system_metrics": {},
    "trajectory_metrics": {"input": {}, "selection": [], "generalization": []},
    "selection_scores": {"official_reconstruction": 0.91, "multi_ic": 0.43},
    "valid": true,
    "failure_reason": null
  }
}
```

## 19.4 Intervention record

```json
{
  "intervention": {
    "layer": "decoder_7", "method": "mean_patch", "alpha": 0.5,
    "selected_on": "validation_ce_nonsaturating",
    "delta_ce": 0.43, "delta_ted_median": 2.1,
    "delta_exponent_aware_skeleton": -0.04, "delta_gen_r2_median": -0.11,
    "beam_candidates_saved": 50, "decode_failures": []
  }
}
```

## 19.5 Training record

condition / trainable blocks / trainable parameters、optimizer / lr / steps、data order seed、
train / validation loss trajectory、**model selection に使った formula score**、selected checkpoint、
peak memory / wall time、layer ranking source。

## 19.6 Preregistration record

```json
{
  "id": "P3",
  "statement": "exponent_aware_skeleton_exact == 0 on 60 rational cells",
  "committed_at_commit": "<sha>",
  "outcome": "hit | miss | undecidable"
}
```

集約JSONだけでなく problem-level と candidate-level の record を残す。

---

# 20. 成果物

```text
results/runs/<gpu-run5-run-id>/
  manifest.json
  config_frozen.yaml
  preregistration.json
  phase0/ ... phase9/
  records/
    systems.jsonl
    candidates.jsonl
    interventions.jsonl
    failures.jsonl
    training.jsonl

graphs/<gpu-run5-run-id>/
  figures/
  tables/
```

| # | レポート | 内容 |
|---|---|---|
| 1 | `GPU_RUN5_decoded_support_report.md` | Track A。形式別 candidate support、有理式系の層別集計。R1–R5 |
| 2 | `GPU_RUN5_grn_benchmark_report.md` | Track B。frozen baseline、多軌道選択。P3・P4・P6 |
| 3 | `GPU_RUN5_grn_adaptation_report.md` | Track C。full / selective FT、forgetting。P7 |
| 4 | `GPU_RUN5_layer_analysis_report.md` | Track D。probe / lens / 因果 / 介入後decode。P5 |
| 5 | `GPU_RUN5_cross_model_synthesis.md` | Track E。RUN2–RUN5 の指標間順位不一致 |
| 6 | `preregistration_outcome.json` | P3–P7、R4–R5の機械判定 |

最低限の図表:

1. generation → selection → integration の failure funnel
2. family別 true skeleton in beam / selected recovery
3. single-trajectory 対 multi-IC selection の paired 比較
4. frozen / official-continued / full / selective / random の formula-level 比較
5. decoder 深度に沿った token rank / TED
6. reconstruction 対 TED の散布図
7. input-IC 対 generalization-IC 性能
8. **$`\Delta`$CE 対 $`\Delta`$TED の層別散布図**（P5 の核心）
9. parameter数・時間・回復性能の Pareto 図
10. 代表的成功式と代表的失敗式の表

レポートは GPU_RUN4 と同じく **§事実 / §RQ判定 / §考察 / §限界 / §提案** を分離する。

---

# 21. 実装配置

共通処理を GPU_RUN5 直下へ複製しない。

| 種類 | 配置 |
|---|---|
| ODEFormer共通拡張 | `src/gpu_run5/`、再利用可能なら `src/gpu_run4/` を一般化 |
| 閉じたGRN系の生成 | `src/data/` |
| 形式分類・構造指標 | `src/evaluation/` |
| 多軌道 candidate selection | `src/evaluation/` |
| Phase入口 | `scripts/phases/gpu_run5_phase*.py` |
| runner | `scripts/ops/run_gpu_run5.sh` |
| config | `configs/gpu_run5/` |
| campaign固有tests | `GPU_RUN5/tests/` |

**GPU_RUN4 コードを変更するときは、既存 GPU_RUN4 結果の再現経路を壊さない。**
必要なら共通関数を新moduleへ抽出し、GPU_RUN4 互換 test を残す。

---

# 22. 既知のリスクと対策

| # | リスク | 対策 |
|---|---|---|
| 1 | Hill式が語彙または token長上限に収まらない | 新token追加より先に compact teacher expression・定数融合を検討。同値testを必須にする |
| 2 | 閉じたGRN系の軌道が定常へ張り付き、Hill非線形性が励起されない | 軌道分散の下限を品質基準に入れ、棄却率を報告。family別に感度を見る |
| 3 | 単一軌道で式を識別できない | selection / generalization trajectory を分離し、multi-IC selection を主比較に含める |
| 4 | full FT が事前学習能力を壊す | frozen / official-continued / decoder-all / selective を置き、ODEBench forgetting と GRN generalization を同時に測る |
| 5 | beam を増やしても候補多様性が増えない | candidate count でなく unique skeleton・oracle TED・sampling反復を測る |
| 6 | 3次元GRNで性能が崩れる | 1D / 2D / 3D を分け、R01–R05 の低次元で pipeline を確立。3D の失敗を全体平均で隠さない |
| 7 | test decode の計算量が大きい | smoke → validation pilot → condition freeze の順。**§8.3 の縮退規則を先に適用する** |
| 8 | 介入強度が全方式で飽和する | Go 5 で止め、decode へ進まない。介入設計を見直す |
| 9 | 計画が実行時に無計画に縮退する（GPU_RUN4の再来） | **§8.3 に縮退の形を先に書いた。縮退したら manifest に「どの規則を適用したか」を記録する** |

---

# 23. 完了条件

- 公開4+12 checkpoint の provenance と `operators_to_use` / `max_dimension` を実体から固定した
- 前向き予測P3–P7を実験前にcommitし、Phase 9でP3–P7とretrospective R4–R5を機械判定した
- 保存済み ODEBench beam 候補を形式別に再解析した
- R01–R08 を閉じたODE系として生成し、split 漏洩を監査した
- input / selection / generalization 軌道を分離した
- frozen baseline の全beam候補と failure を保存した
- generation failure と selection failure を分離した
- multi-trajectory selection を single-trajectory selection と paired 比較した
- **GRN corpus を実際にFTへ使い**、official-continued 対照と比較した
- FT hyperparameter と層集合を validation だけで、条件間で同数の候補を与えて固定した
- full / selective / random 5集合を formula-level で比較した
- **介入後 beam decode を実施し、$`\Delta`$CE と $`\Delta`$TED の順位相関を測った**
- final test を一度だけ評価した
- component-level と system-level の式・数値・安全性指標を保存した
- 事実・推測・未支持仮説・限界を分けたレポートを作成した
- GPU_RUN4 / GPU_RUN2 / README の更新要否を確認した

---

# 24. 現時点で未確定の項目

Phase 0–2 で決めてから本実験へ入る。**test結果を見てから変えない。**

1. checkpoint の実際の `operators_to_use`（§3 の記述の正否を決める）
2. checkpoint の `max_dimension`（D4 の可否を決める）
3. 公式corpus を既定3,000式にするか stretch 30,000式にするか
4. model selection に使う failure-aware formula score の正確な定義（§6.4 の主要軸から1つ）
5. GRN の Hill 係数グリッド $`n\in\{1,2,4\}`$ の妥当性（$`n=1`$ は分母の非線形性が弱い）
6. 公式generator の train/test モード切替が使えるか
7. 介入パネルを24 systemより増やせるか（予算に余裕があれば48）
8. multi-IC score の集約方法（median / trimmed）と $`\lambda`$
9. GPU_RUN2 の G01–G08 を、regulator background 付きで**副次的に**再現し RUN2 との橋渡しにするか
   （実施する場合も数値は混ぜず、質的比較に限る）

---

# 25. GPU_RUN5の研究上の位置づけ

GPU_RUN2 は NeSymReS で「数値は合うが構造は回復しない」を観測し、原因を**有理式priorの欠落**と推測した。
GPU_RUN3 は NDformer で「読み出せる層と因果的に効く層が逆転する」を観測した。
GPU_RUN4 は ODEFormer で前者を再確認したが、後者は検出力不足で判定できなかった。

GPU_RUN5 は次の3つを同時に行う。

1. **RUN2の推測を、正しい形で棄却または修正する。** §3 の generator 設定は、ODEFormer が有理式を
   生成**できる**ことを示唆する。もしそれでも回復しないなら、律速は prior ではなく
   **識別可能性と選択**であり、これは GPU_RUN2 の結論を書き換える。
2. **ODEFormer を GRN モデルとして実際に育てられるかを検証する。** 閉じたHill型GRN系でFTし、
   official-continued 対照と比較し、少数層FTがpriorを保護するかを formula-level で測る。
   ここが本研究のサブ目標1（symbolic recovery の改善）に直接対応する。
3. **層解析と式回復を接続する。** 介入後 beam decode は3世代にわたって欠落していた1実験であり、
   本研究の題目が要求する中核である。

予測が外れても成果になる。
R4 が不成立ならcheckpointの学習設定とdecode supportの理解を修正する。
P5 が外れれば「CE は symbolic recovery の妥当な代理指標」となり、GPU_RUN4 の層順位を読み直せる。
P6 が外れれば「GRN の識別不能性は初期条件の追加では解けない」となり、次段階は探索・データ取得設計へ移る。
P7 が外れれば「少数層FTがpriorを保護する」という GPU_RUN2 の解釈が ODEFormer で否定される。

**どちらに転んでも報告できるよう、予測と縮退規則を実験前に固定することが本計画の要点である。**

---

# 26. 参照資料

- d'Ascoli et al., "ODEFormer: Symbolic Regression of Dynamical Systems with Transformers," ICLR 2024.
  https://openreview.net/forum?id=TzoHLiGVMo
- ODEFormer official repository. https://github.com/sdascoli/odeformer
- ODEBench standalone repository. https://github.com/GPBench/ODEBench
- GPU_RUN4計画: [`GPU_RUN4/plan.md`](../GPU_RUN4/plan.md)
- GPU_RUN4結果: [`GPU_RUN4/GPU_RUN4_research_report_20260819.md`](../GPU_RUN4/GPU_RUN4_research_report_20260819.md)
- GPU_RUN3結果: [`GPU_RUN3/GPU_RUN3_research_report_20260818.md`](../GPU_RUN3/GPU_RUN3_research_report_20260818.md)
- GPU_RUN2計画: [`GPU_RUN2/plan.md`](../GPU_RUN2/plan.md)
- GPU_RUN5 Codex案: [`plan-codex.md`](plan-codex.md)
- GPU_RUN5 Claude Code案: [`plan-claudecode.md`](plan-claudecode.md)
- 研究全体: [`README.md`](../README.md)
