# GPU_RUN5 計画

作成日: 2026-08-23
状態: Draft v0.1（Claude Code案）
前世代: [`GPU_RUN4/plan.md`](../GPU_RUN4/plan.md) / [`GPU_RUN4/GPU_RUN4_research_report_20260819.md`](../GPU_RUN4/GPU_RUN4_research_report_20260819.md)

## 方針

GPU_RUN5は、次の **二大目標を同格の主目的** とする。

1. **「事前学習priorに有理式が希薄である」という仮説を、モデル横断で決定的に検証する。**
   GPU_RUN2はNeSymReSでこれを *推測* として提出したが（README §9.2）、検証していない。
   GPU_RUN4はODEFormerで大量のbeam候補を保存したが、この観点で集計していない。
   GPU_RUN5はこれを主結果へ昇格させ、さらにGRN（Hill型）閉じた系へ適用範囲を広げる。

2. **GPU_RUN4の層解析の検出力を回復し、層解析と数式回復を接続する。**
   GPU_RUN4のResult Bは corpus 80式・4 Adam step・指標がteacher-forcing CEのみであり、
   RQ7（少数層FTがfullに勝つか）とRQ4/RQ6（層ごとの情報表現）に答えられていない
   （GPU_RUN4レポート §7 が自認）。**介入後にbeam 50でdecodeし、skeleton / TED / generalization $`R^2`$ で評価する**
   ことを本runの必須要件とする。これが無い限り、本研究の中心的な問い
   「重要層への介入で数式回復は変わるか」は永久に判定不能である。

副次目標として、GPU_RUN2 / GPU_RUN3 / GPU_RUN4 の3モデル横断で
**「読み出せる層」「因果的に効く層」「適応できる層」が一致しない** という現象を統合報告する（§2.3、Track C）。
これはGPU不要であり、現時点で本研究の最も新規性のある成果になり得る。

GPU_RUN5は GPU_RUN4 と同じ公開ODEFormer checkpoint（4 encoder + 12 decoder、60,646,773 parameters、
SHA256 `56754040be5aa92ed4767fc43ee2008faa293f87c12b643e66c7df3e1623a5e8`）を対象とする。
論文Tableの 4+16 / 約86M モデルは対象にしない（§2.4）。

---

# 1. GPU_RUN4から引き継ぐ確定事項

以下はGPU_RUN4で確定済みであり、GPU_RUN5では再検証しない。

| 項目 | 確定値 | 出典 |
|---|---|---|
| architecture | 公開4 encoder + 12 decoder、dim 256/512、16 heads、60,646,773 params | `phase0/architecture_audit.json` |
| 論文Tableとの不一致 | 4+16 / dim 512 / 約86M とは一致しない。旧Drive IDは別pickle | GPU_RUN4 §1.2 |
| 評価器 | parse 63/63、恒等canonical TED 0、prefix往復 63/63、gold 11件成功 | `phase1/eval.json` |
| `normalized_ted` 定義 | $`\mathrm{ted}_{raw}/(\mathrm{size}_{true}+\mathrm{size}_{pred})`$、多次元は `system` ノード1個追加 | GPU_RUN4 §2.3 |
| skeleton定義 | 数値葉と `c_i` を `CONST` 化。整数指数も対象（$`x^2`$ と $`x^3`$ は一致） | 同上 |
| ODEBench再現（reduced） | valid 0.921、recon中央値 0.980、gen中央値 0.696、canonical exact 0、skeleton 0.075 | `phase2/eval.json` |
| beam診断 | true skeleton in beam 0.091、unique skeleton/beam 平均 9.19、取り逃がし 5/252 | `phase3/eval.json` |

**評価器（Phase 1相当）はGPU_RUN5でも再凍結せずそのまま使う。** 定義を変えると世代間の唯一の比較可能軸を失う。
ただしGPU_RUN5で新たに導入する `rational_form` 判定（§4.3）だけは本runのPhase 0で定義を固定し、test前に凍結する。

## 1.1 実行上の前提条件

- GPU_RUN4の `results/runs/gpu_run4_phase0_01/` は **gitignoreであり、本リポジトリの作業ツリーには存在しない**。
  Phase 0はまず実行機からこのディレクトリを同期することから始める。同期できない場合、Phase 1（GPU不要の再解析）は
  Phase 2の再実行に置き換わり、予算が約20分増える。
- GPU_RUN4の `manifest.json` の `status` が `running` のままである（GPU_RUN4 §7）。GPU_RUN5のPhase 0で
  finalizeを完走させ、`complete` へ更新してからGPU_RUN5のrecordを書き始める。

---

# 2. 目的と範囲

## 2.1 主目的A: 有理式prior仮説の検証とGRNへの適用

GPU_RUN2の最終結論（README §10）は次だった。

> GNW由来の真式の87.5%（G02–G08）が変数を分母に含む有理式であるのに、NeSymReSは3,000件を超える有効式で
> **一度も変数分母の式を出していない。** …律速は層の選び方でも学習量でもなく、事前学習の式priorと
> Hill型ODEという対象クラスの不一致にある可能性が高い。

これは1モデル・1データセットの観察に基づく推測である。GPU_RUN5はこれを次の3段階で検証する。

**A-1（GPU不要）。** ODEBench 63系のうち変数分母を持つ系は、本計画作成時の暫定集計で **15系** である。

| id | dim | 内容 | 真式（抜粋） |
|---|---|---|---|
| 4 | 1 | RC-circuit with non-linear resistor | `1/(1+exp(c_0 - x_0/c_1)) - 0.5` |
| 14 | 1 | Budworm outbreak with predation | `c_0*x_0*(1-x_0/c_1) - c_3*x_0^2/(c_2^2+x_0^2)` |
| 15 | 1 | Budworm outbreak (dimensionless) | `c_0*x_0*(1-x_0/c_1) - x_0^2/(1+x_0^2)` |
| 18 | 1 | Logistic with harvesting | `c_0*x_0*(1-x_0/c_1) - c_2*x_0/(c_3+x_0)` |
| 19 | 1 | Logistic with harvesting (dimensionless) | `x_0*(1-x_0) - c_0*x_0/(c_1+x_0)` |
| **20** | 1 | **Autocatalytic gene switching** | `c_0 - c_1*x_0 + x_0^2/(1+x_0^2)` |
| **22** | 1 | **Hysteretic activation of a protein expression** | `c_0 + c_1*x_0^5/(c_2+x_0^5) - c_3*x_0` |
| 33 | 2 | Glider | `... \| x_0 - cos(x_1)/x_0` |
| 38 | 2 | Van der Pol (simplified) | `c_0*(x_1 - x_0^3/3 + x_0) \| -x_0/c_0` |
| 42 | 2 | Chlorine dioxide–iodine–malonic acid | `c_0 - x_0 - c_1*x_0*x_1/(1+x_0^2) \| ...` |
| 47 | 2 | Binocular rivalry (no oscillations) | `-x_0 + 1/(1+exp(c_0*x_1-c_1)) \| ...` |
| 48 | 2 | Bacterial respiration | `c_0 - x_0 - x_0*x_1/(1+c_1*x_0^2) \| ...` |
| 53 | 3 | Apoptosis | `c_0 - c_5*x_1*x_0/(c_9+x_0) - c_4*x_0 \| ...` |
| 60 | 3 | Aizawa attractor | `... \| c_2 + c_0*x_2 - x_2^3/3 - (x_0^2+x_1^2)*(...)/...` |
| 62 | 4 | Binocular rivalry with adaptation | `-x_0 + 1/(1+exp(c_0*x_2+c_1*x_1-c_2)) \| ...` |

**#20 と #22 は、README §2.1 が定義するHill型遺伝子制御式そのものである。**
そしてGPU_RUN4でskeleton一致した6系（1 RC-circuit、2 Population growth、6 Autocatalysis、
9 Language death、12 Photons in a laser、31 SIR）は、**この15系と1つも重複しない。**
さらに定性パネルの系62について、GPU_RUN4 §3.5 は「sigmoidを線形で代用」（TED 36）と記録している。
これはGPU_RUN2で観測した「飽和構造を多項式で代用する」失敗様式が、別モデル・別データで再現していることを示唆する。

A-1では、GPU_RUN4の保存 `phase2/selected.json` と `phase3/beam_groups.json`（252 group × 最大50候補 ≒ 12,600候補）に対し、
**真式が有理式か否かで層別した集計** と、**予測式に変数分母が現れる率** を計算する。追加のGPU推論を必要としない。

**A-2（GPU、小規模）。** ODEBenchは有理式を15/63しか含まず、そのうち1次元は7系である。
統計的検出力が足りないため、**Hill型の閉じた低次元GRN系を新規に構築し、ODEFormerで評価する**。
設計は §5.2。GPU_RUN2のGNW G01–G08 とは**別の生成物**であり、数値を同一表に混ぜない（§3.2）。

**A-3（条件付き）。** DREAM4 size-10 への適用。ただしODEFormerの次元上限という強い制約がある（§5.3）。
Go 3 を通らない場合は実施しない。

## 2.2 主目的B: 層解析の検出力回復と、式回復との接続

GPU_RUN4のResult Bの問題点と、GPU_RUN5での修正を対応させる。

| # | GPU_RUN4の問題 | 影響 | GPU_RUN5の修正 |
|---|---|---|---|
| B1 | 解析corpus 48/16/16 = 80式 | IOLE差が $`10^{-3}`$ でn_val=16、順位が偶然と区別できない | train 2,000 / val 500 / test 500（stretch 20,000/5,000/5,000） |
| B2 | FT 4 step固定、lr $`10^{-4}`$ のみ | 全FT条件がfrozenに負け、RQ7が検定になっていない | validationで lr × step数 を grid探索。testは一度だけ |
| B3 | probeがencoder 4層のみ | 「16層解析」を名乗れない。RQ4/RQ6が判定不能 | decoder 12層のhidden probe + DecoderLens型 + decoder-side readout |
| B4 | 全指標がteacher-forcing CE | 層解析と式回復が接続されない。中心的問いが判定不能 | **固定介入パネルに対し介入後beam 50 decode**、skeleton / TED / gen $`R^2`$ で評価 |
| B5 | 1 seed | 順位安定性が測れない | data_seed 101 / 202 / 303 の3 seed |
| B6 | ablationがresidual-zero のみ | encoder_3 の $`\Delta`$CE 10.40 は「最終encoder段を壊した」以上を意味しない | mean-activation patching と補間強度 $`\alpha`$ を追加し、飽和を避ける |

**B4がGPU_RUN5の最重要項目である。** そしてこれは高価ではない。GPU_RUN4の実測で推論は約1.89秒/cell、
固定パネル24問題 × 17条件（16層 + baseline）× 3 seed = 1,224 decode ≒ **約39分**である。
GPU_RUN4がこれを実施しなかったのは予算ではなく設計上の欠落である。

## 2.3 副次目標C: 3モデル横断の統合（GPU不要）

GPU_RUN2 / GPU_RUN3 / GPU_RUN4は評価設計が異なるため **数値を同一表に混ぜてはならない**（README §1.2）。
しかし「指標間の順位不一致パターン」は混ぜられる。

| run | モデル | probe上位 | 因果上位 | IOLE / FT上位 | 観測された乖離 |
|---|---|---|---|---|---|
| GPU_RUN2 | NeSymReS (26M) | decoder全層 template 1.000 | decoder_1/3/4（罰則値へ飽和） | `decoder_4` | ranking向きの実装問題、contribution全層NaN |
| GPU_RUN3 | NDformer (17.7M) | — | — | decoder最終ブロック（full改善の89%） | probe vs intervention の順位相関 **−1.0** |
| GPU_RUN4 | ODEFormer (60.6M) | `encoder_0` | `encoder_3` | `decoder_7` | 上位3層が3指標すべてで不一致 |

3つの異なるアーキテクチャ（点集合SR / MCTS誘導 / 軌道ODE）、3つの異なる事前学習分布で
**同じ乖離が再現する** なら、これは単一runの実装バグではなく手法論的主張になる。
逆に3モデルで乖離のパターンが違うなら、それ自体がモデル依存性の知見である。
成果物は統合表1つと図1枚であり、既存JSONの再集計のみで済む。

## 2.4 GPU_RUN5で主対象にしないもの

- **論文4+16 / 約86M重みの捜索。** GPU_RUN4で旧Drive IDが `symbolicregression` pickleと確定済み。
  発見された場合は別run-idを起こす。本runは公開4+12を対象と明記する。
- **論文Figure 4のフルグリッド（$`\sigma`$ 6点 × 3 seeds）への拡大。** valid率と $`R^2`$ の再現精度を上げても
  canonical exact 0 という主結果は動かない。予算をA-2とB4へ回す。
- **NMSE / reconstruction $`R^2`$ をさらに下げる方向の改善。** README §10 が既に「次の主課題ではない」と結論している。
- **ODEFormerの事前学習の再実行。** A100 3日相当。公開checkpointからのinferenceのみ。
- **ヒト時系列、NeSymReS比較、TPSR、生物学的機構の主張。**

---

# 3. 研究上の絶対条件

GPU_RUN4 §5 を継承したうえで、GPU_RUN5で追加する条件を示す。

## 3.1 事前登録した予測をtest前に固定する（新規・最重要）

GPU_RUN5の主結果は **否定的結果になる可能性が高い**（§4）。否定的結果を事後解釈でなく報告するため、
**Phase 0で予測を数値つきで書き、commitしてから測る。** 予測を外した場合も予測表をそのまま残す。

## 3.2 世代間で数値を混ぜない

- GPU_RUN5のGRN suite は GPU_RUN2 の GNW G01–G08 と **別の生成物** である。閉じた系である、
  軌道入力である、oracle変数を与えない、有限差分を使わない、という4点で設計が異なる。
  同一表に置かず、比較は「有理式を1件でも出したか」という質的な軸に限る。
- GPU_RUN4のODEBench数値とGPU_RUN5のODEBench再解析は、**同一recordの再集計であるため混ぜてよい**。
  再推論した場合は別run-idにして混ぜない。

## 3.3 ODEBenchをfine-tuning corpusにしない

GPU_RUN4 §5.2 を継承する。GRN suite も同様に層rankingやFTのtraining dataへ使わない。
層解析corpusはODEFormer公式 `env.gen_expr` からのみ生成する。

## 3.4 Validation / test分離

- probe hyperparameter、layer ranking、介入方式、FTのlr / step数、random layer set: **validationのみ**
- analysis-test: 全設定凍結後に **一度だけ**
- GRN suite / ODEBench: 外部評価benchmarkであり、層選択に使わない

## 3.5 相関的解析と介入的解析を混同しない

GPU_RUN4 §5.6 を継承する。GPU_RUN5では加えて、**「介入後CE」と「介入後symbolic recovery」を別指標として報告する。**
両者が一致しないこと自体がRQ6への回答になり得る。

## 3.6 Failureを隠さない

GPU_RUN4 §5.4 の失敗タグ一覧を継承し、`rational_parse_failure` と `intervened_decode_failure` を追加する。

---

# 4. 事前登録した予測

**testを見る前に確定する。** 各予測に反証条件を明記する。Phase 9で「的中 / 外れ / 判定不能」を機械的に判定する。

| # | 予測 | 反証条件 |
|---|---|---|
| **P1** | ODEBench有理式15系のうち、GPU_RUN4のselected予測に変数分母が現れる系は **3系以下** である | 4系以上で現れたらP1は外れ |
| **P2** | ODEBench有理式15系のskeleton exact率は、非有理式48系の率より低い。点推定で **0/60 cell** と予測する | 有理式側で1件でもskeleton exactが出たらP1/P2の主張は弱まる |
| **P3** | beam 50全候補（約12,600件）のうち、変数分母を持つ候補の割合は **5%未満** である | 5%以上ならODEFormerのpriorは有理式を含んでおり、GPU_RUN2の推測はODEFormerへ一般化しない |
| **P4** | GRN suite（Hill型閉じた系、dim 2–4）のskeleton exact率は **0.05未満** である | 0.05以上ならODEFormerはGRN構造を回復できており、本研究の主課題が変わる |
| **P5** | GRN suiteのreconstruction $`R^2`$ 中央値は **0.9以上** である一方、skeleton exactは低い（P4）。すなわち「当てはまるが構造は違う」がGRNでも再現する | recon中央値が0.9未満なら、失敗の原因が構造priorではなく軌道の当てはめ自体になり、解釈が変わる |
| **P6** | 介入後beam decodeにおいて、causal $`\Delta`$CE 上位層への介入は、**TED増分でも上位**になる（順位相関 Spearman $`\rho > 0.5`$） | $`\rho \le 0.5`$ なら、CEとsymbolic recoveryは別の層構造に依存しており、これ自体が主要な知見になる |
| **P7** | 拡大corpus（train 2,000）とlr/step探索の後でも、**選択FTはfullに勝つがfrozenには勝てない** | 選択FTがfrozenに勝てばRQ7が初めて支持される。fullが勝てばGPU_RUN4の解釈（短いFTが事前学習を壊した）が誤り |

P1–P3はGPU不要であり、Phase 1で判定する。**P3が外れた場合（有理式候補が5%以上出る）、Track Aの前提が崩れるので
Phase 2以降のGRN suiteは設計を見直す**（§13 Gate 1）。

---

# 5. データ

## 5.1 D1: ODEBench（再解析、GPU不要）

GPU_RUN4の `phase2/selected.json` / `phase3/beam_groups.json` をそのまま使う。新規推論なし。

- 層別軸1: 真式が変数分母を持つか（15 / 48）
- 層別軸2: 次元（1 / 2 / 3 / 4）
- 層別軸3: corruption（$`\sigma\in\{0,0.05\}`$ × $`\rho\in\{0,0.5\}`$）
- 集計単位: 252 cell、および 252 group × 最大50候補

有理式判定は §4.3 の `rational_form` 定義に従い、真式・selected予測・全beam候補の3者に対して計算する。

## 5.2 D2: GRN suite（新規生成、Hill型の閉じた低次元系）

GPU_RUN2のG01–G08は **対象遺伝子1個のRHS** であり、oracle regulatorを入力する設計だった。
ODEFormerは **閉じた $`d`$ 次元系の軌道** $`x(t)\in\mathbb{R}^d`$ を入力とし、$`d`$ 本の成分式を出力する。
したがってG01–G08をそのまま流用できない。GPU_RUN5では閉じた系を新規に構築する。

既存資産を使う。[`src/data/synthetic_grn.py`](../src/data/synthetic_grn.py) は toggle switch と repressilator を、
[`src/data/dreamlike_grn.py`](../src/data/dreamlike_grn.py) は多遺伝子GRNのHill型RHSを持つ。

| family | dim | 構造 | 真式の形 |
|---|---|---|---|
| R01 | 1 | 自己活性化 + 分解 | $`\alpha x^n/(K^n+x^n) - \beta x`$（ODEBench #20/#22 と同型） |
| R02 | 2 | toggle switch（相互抑制） | $`\alpha K^n/(K^n+y^n) - \beta x`$ × 2 |
| R03 | 2 | 活性化カスケード | $`\alpha_1 - \beta_1 x \mid \alpha_2 y_{\mathrm{in}}^n/(K^n+x^n) - \beta_2 y`$ |
| R04 | 3 | repressilator（環状抑制） | 抑制Hill × 3 |
| R05 | 3 | 2活性化因子の複合体形成 | 分母に積を含むHill |

各familyについて Hill係数 $`n\in\{1,2,4\}`$ とパラメータをLatin hypercubeで振り、**12 variant** を生成する。
計 5 family × 12 variant = **60系**。corruptionはODEBenchと同一グリッド（$`\sigma\in\{0,0.05\}`$ × $`\rho\in\{0,0.5\}`$）。
3 seedで **60 × 4 × 3 = 720 cell**。

生成の必須要件:

- 軌道は数値積分（`scipy.integrate.solve_ivp`、RK45、rtol $`10^{-8}`$）で作る。**有限差分は使わない**が、
  ODEFormerは軌道を直接受け取るため微分推定は不要である。これがGPU_RUN2のoracle条件[2]を
  **理想化ではなく設計上不要にする**点であり、本runの実データ方向への前進にあたる。
- 初期値は生物学的に妥当な非負領域から取り、**generalization評価用に別の初期値を2組保存する**（ODEFormerプロトコル準拠）。
- 定常状態に張り付いた軌道は情報量が無いため、軌道の分散が閾値未満のvariantは生成時点で棄却し、棄却数を記録する。
- 各系の真式を `x_0 | x_1 | ...` 形式のinfixで保存し、GPU_RUN4の評価器でparse・canonical・skeleton・TEDが
  計算できることをPhase 2のGo条件として確認する。

## 5.3 D3: DREAM4（条件付き、Go 3 が必要）

[`src/data/dream4_sbml.py`](../src/data/dream4_sbml.py) はSBMLのkineticLaw parameterから
gene ODEを再構成し `expression_string()` を返す。すなわち **DREAM4 size-10 は真式が復元可能** である。
これが成立すれば、DREAM4上で reconstruction だけでなく **symbolic recovery** を測れる。

ただし2つの障害がある。

1. **次元。** DREAM4 size-10 は10遺伝子系である。ODEFormerのparser defaultは `max_dimension=2` であり、
   公開checkpointの実際の学習上限はPhase 0で `architecture_audit.json` から確認する。
   GPU_RUN4の実測では既に3次元で valid 25/40・skeleton 0 まで劣化している。
   **10次元は範囲外である可能性が高い。**
2. **部分系の非閉性。** 2–4遺伝子の部分ネットワークを切り出すと、外部からの制御入力が失われ、
   その部分系の真式は元のODEと一致しない。切り出しは「真式を持つ問題」を作らない。

したがってD3は次のいずれかへ縮退させる。

- **D3a**: 復元した真式が、GNW公開の無ノイズ時系列を再現できるかを検証するだけに留める（GPU不要、真式復元の妥当性検査）。
- **D3b**: checkpointの次元上限が10以上であることをPhase 0で確認できた場合のみ、size-10 全系へ適用する。
- **D3c**: 実施しない。

**既定はD3a + D3c である。** D3bはGo 3が通った場合のオプションとする。実施しない場合はその旨をレポートへ明記する。

## 5.4 D4: 層解析corpus（ODEFormer公式generator）

GPU_RUN4 §7.4 の設計に戻す。公式 `env.gen_expr` から式単位で分割する。

| split | GPU_RUN4実績 | GPU_RUN5既定 | stretch |
|---|---|---|---|
| analysis_train | 48 | 2,000 | 20,000 |
| analysis_validation | 16 | 500 | 5,000 |
| analysis_test | 16 | 500 | 5,000 |

GPU_RUN4のPhase 4は80式で99秒（約1.24 s/式）だった。既定の3,000式は約62分、stretchの30,000式は約10時間である。
**既定で開始し、Phase 5でthroughputを実測してからstretchの可否をtest前に決める。**

- skeleton漏洩をhashで監査する（train–val / train–test / val–test すべて0を要求）。
- GPU_RUN4は `gen_expr(train=True)` をtest分割にも使っていた。GPU_RUN5では公式のtrain/test生成モード切替を
  使えるか調査し、使えない場合はその事実を限界として明記する。

## 5.5 D5: 固定介入パネル（B4用）

介入後beam decodeは高価なので固定パネルを使う。**成功例を後から選ばない。**

analysis_validation と analysis_test それぞれから、次で層別してID順に機械的に抽出する。

- dimension（1 / 2 / 3）: 各8問題
- そのうち有理式を含むものを最低4問題含める

計 **24問題**（validation用24 + test用24を別に固定）。介入条件は 16層 + baseline = 17。

---

# 6. 評価指標

GPU_RUN4 §8 を継承する。GPU_RUN5で追加・変更する指標のみ示す。

## 6.1 rational_form（新規、Phase 0で定義凍結）

式木に対して次を判定する。

```text
rational_form(e) = True  ⟺  e の部分木に div ノードが存在し、
                            その右子（分母）の部分木が変数ノードを1つ以上含む
```

- `x_0 / c_1`（定数分母）は **False**。`c_0 / x_0`、`x_0^2/(1+x_0^2)` は **True**。
- `exp` を含むsigmoid `1/(1+exp(...))` は分母に変数を含むので **True** だが、
  `saturating_form` という別フラグでも記録し、Hill型有理式と区別して集計できるようにする。
- 多成分系では **成分ごとに判定し、系レベルでは「いずれかの成分がTrue」** とする。成分別の内訳も保存する。

報告する率:

| 指標 | 定義 |
|---|---|
| `true_rational_rate` | 真式が有理式である系の割合（ODEBench: 15/63 の再確認） |
| `selected_rational_rate` | selected予測が有理式である cell の割合 |
| `beam_rational_rate` | beam全候補のうち有理式である候補の割合 |
| `rational_hit_rate` | 真式が有理式のとき、beam内に有理式候補が1件以上ある割合 |
| `rational_skeleton_exact` | 真式が有理式の cell における skeleton exact 率 |

## 6.2 介入後symbolic metrics（新規、B4）

各介入条件 $`l`$、各パネル問題 $`p`$ について、beam 50 decodeを行い次を記録する。

```math
\Delta\mathrm{TED}_l = \mathrm{median}_p\bigl(\mathrm{ted}_{l,p}\bigr) - \mathrm{median}_p\bigl(\mathrm{ted}_{\mathrm{baseline},p}\bigr)
```

同様に $`\Delta`$ skeleton exact率、$`\Delta`$ valid率、$`\Delta`$ recon $`R^2`$ 中央値、$`\Delta`$ gen $`R^2`$ 中央値、
$`\Delta`$ unique skeleton数を記録する。**$`\Delta`$CEとの順位相関（Spearman / Kendall）がP6の判定材料である。**

## 6.3 継承する指標

reconstruction / generalization $`R^2`$、valid rate、canonical exact、symbolic equivalent、skeleton exact、
normalized TED、complexity、variable F1、beam diagnostics（in-beam rate、selection gap、oracle TED）は
GPU_RUN4の定義をそのまま使う。

**GPU_RUN2の variable F1 が oracle変数により飽和した問題（README §11.2）は、GPU_RUN5では発生しない。**
ODEFormerは観測次元の全変数を入力として受け取るため、変数選択は予測の一部である。
ただしGPU_RUN4では variable F1 中央値が1.0（247/252）で識別力が低かったので、補助指標として扱う。

---

# 7. 層解析設計

## 7.1 解析対象

16層（encoder 4 + decoder 12）。GPU_RUN4と同一。GPU_RUN4で未実施だったdecoder側を追加する。

## 7.2 Probe（B3）

| 対象 | GPU_RUN4 | GPU_RUN5 |
|---|---|---|
| encoder 4層 pooled hidden | dimension分類、complexity回帰、`has_sin` | 継続 + `rational_form` 分類を追加 |
| decoder 12層 hidden | **未実施** | next token分類、演算子カテゴリ分類、木の深さ回帰、`rational_form` 分類 |

- **control task を必ず置く。** GPU_RUN2はこれを欠き、probeスコアが「層の情報」か「probeの表現力」かを
  分離できなかった（README §11.2）。GPU_RUN4はラベルシャッフル対照を持っていたので、これを全タスクへ拡張する。
- **token pseudo-replication を防ぐ。** decoder hiddenは1式あたり数十token出るため、同一式のtokenを
  独立標本として扱うとnが水増しされる。probeのfit / 評価は **式単位で分割** し、
  式内tokenは同一splitへ入れる。GPU_RUN4 §19.7 の方針を継承する。
- `n_val` は500式であり、GPU_RUN4の16式から大幅に増える。IOLE差 $`10^{-3}`$ の有意性が初めて議論可能になる。

## 7.3 DecoderLens / decoder-side readout

- **encoder intermediate decoding**: encoder各層の出力をPMA poolingへ通してdecoderのcross-attention memoryへ与える。
  GPU_RUN2の実装（[`src/interpretability/decoder_lens.py`](../src/interpretability/decoder_lens.py)）を移植する。
  **限界を明記する**: decoderは最終encoder表現を受け取るよう学習されているため、これはdistribution shiftである。
  パース率の絶対値を通常のdecode性能として読まない。層間の相対比較にのみ使う（README §6.3）。
- **decoder-side intermediate readout**: decoder各層のhiddenを最終層のoutput projectionへ通し、
  各深さでのtoken分布を得る。RQ6（数式構造がdecoder深さに沿ってどう形成されるか）の主データになる。
  GPU_RUN3はこの型の解析で「TEDが31.1 → 8.9へ急変する」というencoder段の構造形成を捉えている。

## 7.4 CKA

encoder内、decoder内をそれぞれ計算する。**encoder–decoder間のcross-module CKAは主張に使わない**
（GPU_RUN4 §19.8）。GPU_RUN4ではencoder CKAが全対で0.921–0.978と高く、識別力が低かった。
decoder 12層でも同様に飽和する可能性が高いので、**CKAは補助指標であり層rankingに使わない** と事前に決める。

## 7.5 Gradient norm / parameter update sensitivity

GPU_RUN4のgradient normは絶対値が $`10^{-8}`$–$`10^{-6}`$ と極端に小さかった。
層ごとのパラメータ数で正規化した値と、生の値の両方を保存する。

---

# 8. 因果的層解析

## 8.1 介入方式（B6）

| 方式 | 内容 | GPU_RUN4 |
|---|---|---|
| residual-zero ablation | attention / FFN残差を0にする | 実施済み。encoder_3 で $`\Delta`$CE 10.40 |
| mean-activation patching | 層の活性化をcorpus平均へ置換 | **未実施** |
| 補間 patching | $`\tilde h = (1-\alpha)h + \alpha\bar h`$、$`\alpha\in\{0.25,0.5,0.75,1.0\}`$ | **未実施** |

zero ablationは学習時に一度も経験しない状態へモデルを追い込むため、「その層の機能」ではなく
「壊れたモデルの挙動」を測る危険がある（README §6.4）。
GPU_RUN4の encoder_3 の $`\Delta`$CE 10.40 は他層より桁違いに大きく、この危険が現実化した可能性が高い。
**補間強度 $`\alpha`$ を振り、飽和しない領域で層間の因果差を識別する。**

## 8.2 control hook

GPU_RUN4の `control_hook_ok: true`（恒等hookがbaselineを変えない）を継承し、全介入方式で検証する。

## 8.3 介入後beam decode（B4、本runの最重要項目）

固定パネル24問題 × 17条件 × 3 seed。各decodeでbeam 50全候補を保存し、§6.2の指標を計算する。

予算: 約1.89 s/decode × 1,224 = **約39分**（validationパネル）。testパネルも同規模。

**この結果が「重要層への介入で数式回復は変わるか」への直接の回答になる。**
GPU_RUN2 / GPU_RUN3 / GPU_RUN4 のいずれもこれを持っていない。

---

# 9. Single-layer / selective fine-tuning

## 9.1 Hyperparameter探索（B2）

GPU_RUN4は lr $`10^{-4}`$ × 4 step の1点のみで、全FT条件がfrozenに負けた。
GPU_RUN2は探索を行ったと記述しながら実際には行っていなかった（README §11.3）。**同じ失敗を繰り返さない。**

validationのみで次を探索する。

- lr: $`\{10^{-6}, 10^{-5}, 10^{-4}\}`$
- step数: $`\{50, 200, 800\}`$（early stoppingをvalidation CEで有効化）
- optimizer: Adam固定

9条件 × full FT で最良点を決め、その設定を全層条件へ適用する。**探索結果（負けた条件も含む）を全て保存する。**

## 9.2 Go 5 の前提

fullがvalidationで frozen を **上回る** 設定が1つも見つからない場合、IOLE寄与度
$`C_l = (L_{\mathrm{base}}-L_l)/(L_{\mathrm{base}}-L_{\mathrm{full}})`$ の分母が成立しない。
これはGPU_RUN2で実際に起き、contributionが全層NaNになった（README §2.4、§11.3）。
その場合は **正規化寄与度を報告せず、raw scoreの順序としてのみ読む** ことを事前に決めておく。

## 9.3 選択FT条件

| 条件 | 層 |
|---|---|
| frozen | なし |
| full | 全パラメータ |
| top1 / top3 | 各指標（probe / causal / IOLE）ごとに別条件として定義 |
| causal_top3 | 因果 $`\Delta`$CE 上位3層 |
| symbolic_top3（新規） | 介入後 $`\Delta`$TED 上位3層 |
| random3 × 5集合 | **testを見る前に固定。上位集合との重複を制御し、random-set varianceを推定する** |
| bottom3 | 最下位3層 |

GPU_RUN2ではrandom対照が1集合のみで、上位3層と2/3が重複していた（README §9.7）。
GPU_RUN4ではrandom 3集合だった。**GPU_RUN5では5集合とし、上位3層との重複数を記録する。**

---

# 10. Phase構成

run-id: `gpu_run5_<yyyymmdd>_<commit8>`。予算はGPU_RUN4の実測（推論 1.89 s/cell、corpus生成 1.24 s/式）から見積もる。

## Phase 0: 前提固定・予測登録・GPU_RUN4 finalize

目的: **GPU_RUN5の主張を後から動かせない状態にする。**

実施:

- LANSR commit固定、ODEFormer upstream commit固定、checkpoint SHA256確認
- GPU_RUN4 `results/runs/gpu_run4_phase0_01/` の同期と finalize 完走（`status: complete`）
- `architecture_audit.json` から checkpoint の `max_dimension` を確認（D3の可否を決める）
- **`rational_form` / `saturating_form` の定義を凍結**（§6.1）
- **§4 の予測 P1–P7 を数値つきでcommit**
- ODEBench 63系の有理式判定を実行し、暫定集計15系を正式に確定
- failure / resume schema確認

Go条件: 上記すべて完了、かつ予測がcommit済み。予算: **1日、GPU不要**。

---

## Phase 1: ODEBench再解析（Track A-1）

目的: **P1–P3を判定する。**

実施:

- `phase2/selected.json` の252 cellへ `rational_form` を付与し、真式の有理性で層別集計
- `phase3/beam_groups.json` の全候補（約12,600件）へ `rational_form` を付与
- §6.1 の5指標を算出。次元・corruptionでも層別
- 有理式15系の skeleton exact / TED / recon / gen の分布を非有理式48系と比較
- 系62（sigmoidを線形で代用、TED 36）を含む有理式系の予測式を定性表として保存

主成果: `phase1/rational_prior.json`、有理式 vs 非有理式の比較表。

Go条件: 252 cell と全beam候補について判定が付き、失敗が理由付きで保存されている。
予算: **数分、GPU不要**（同期できない場合はPhase 2再実行で約20分）。

---

## Phase 2: GRN suite生成（Track A-2）

目的: **Hill型の閉じた低次元系を、評価器で扱える形で固定する。**

実施:

- R01–R05 × 12 variant = 60系を生成、数値積分で軌道化（§5.2）
- 定常張り付きvariantの棄却と棄却数記録
- corruptionグリッド適用、generalization用の別初期値2組を保存
- 真式60本をGPU_RUN4評価器でparse → canonical → skeleton → TED往復
- data fingerprint保存

Go条件:

- 60/60 系がparse成功し、恒等比較のcanonical TEDが0
- 全variantが `rational_form: True`（Hill型なので当然。Falseが出たら生成バグ）
- 軌道に NaN / Inf が無い

予算: **CPU数分**。

---

## Phase 3: GRN suiteでのODEFormer評価（Track A-2）

目的: **P4・P5を判定する。**

実施: 60系 × 4 corruption × 3 seed = 720 cell、beam 50 sampling、temperature 0.1、rescaleあり。
全候補保存。`ODEFormer (opt)` は代表パネルのみ。

主成果: reconstruction / generalization / skeleton exact / TED / `beam_rational_rate` / in-beam rate。

予算: 720 × 1.89 s ≒ **約23分**（推論のみ）。積分・評価・optのオーバーヘッドを含めて **約60分**。

---

## Phase 4: DREAM4（条件付き、Go 3が必要）

既定は D3a のみ: SBML復元した真式がGNW公開の無ノイズ時系列を再現するかを検証する（GPU不要）。
Go 3 が通った場合のみ D3b を実施する。通らない場合はレポートへ「実施せず、理由は次元上限」と明記する。

予算: D3a **CPU数分** / D3b **約30分**。

---

## Phase 5: 層解析corpus生成と観測的解析（Track B）

目的: **検出力のあるcorpusを固定し、16層すべてを観測する。**

実施:

- 公式generatorから train 2,000 / val 500 / test 500 を生成、skeleton漏洩監査
- teacher-forcing CE baseline（3 seed）
- encoder 4層 + **decoder 12層** のhidden probe（§7.2）、control task付き
- 式単位分割によるtoken pseudo-replication防止
- gradient norm、CKA（module内のみ）
- encoder intermediate decoding、decoder-side readout
- 固定介入パネル（validation用24 + test用24）を生成し凍結
- **throughput実測 → stretch corpus（20,000）の可否をtest前に決定**

予算: corpus生成 **約62分**、probe / CKA / gradient **数十分**、lens系 **1–2時間**。

---

## Phase 6: 因果解析と介入後beam decode（Track B、最重要）

目的: **層への介入が数式回復を変えるかを直接測る。**

実施:

- residual-zero ablation（16層、control hook検証）
- mean-activation patching、補間 $`\alpha\in\{0.25,0.5,0.75,1.0\}`$
- **validationパネル24問題 × 17条件 × 3 seed の介入後beam 50 decode**
- $`\Delta`$CE と $`\Delta`$TED / $`\Delta`$skeleton / $`\Delta`$gen $`R^2`$ の順位相関を計算（**P6の判定**）

予算: ablation / patching **数十分**、介入後decode **約39分/パネル**。

---

## Phase 7: IOLE + hyperparameter探索（Track B）

目的: **RQ7を検定可能な形にする。**

実施:

- lr × step数のgrid探索（9条件、validationのみ、early stopping）
- 16層 IOLE を最良設定で実行、3 seed
- full FT を同設定で実行
- $`C_l`$ の分母成立を確認。不成立ならraw score順序のみ報告（§9.2）
- parameter update sensitivity

予算: throughputをPhase 5で実測してから確定する。**暫定で3–6時間**。

---

## Phase 8: 選択FT（validation、layer set凍結）

目的: **test前に全条件を凍結する。**

実施: §9.3 の条件をvalidationで評価し、random 5集合を含めて層集合を確定。
上位集合との重複数を記録。凍結後は変更しない。

---

## Phase 9: analysis-test 一度きり + 統合（Track B + C）

実施:

- analysis-test（500式）と test介入パネル（24問題）を **一度だけ** 評価
- 予測 P1–P7 の的中判定を機械的に出力
- **Track C: GPU_RUN2 / RUN3 / RUN4 / RUN5 の指標間順位不一致の統合表と図**（GPU不要）
- Result A（有理式prior + GRN）、Result B（層解析）、Result C（3モデル横断）を分離して保存

---

# 11. 統計設計

## 11.1 Seed

data_seed 101 / 202 / 303 の3 seed。GPU_RUN4は1 seedだった。
**n=3では95% Studentのt区間は自由度2で非常に広い**（README §11.1）。
したがって margin判定を主結論に使わず、**点推定と区間を併記し、区間の広さを明示する**。
「有理式候補が1件も出ない」のような **率が0か非0か** の質的判定は、n=3でも十分に強い主張になる。

## 11.2 集計単位

- ODEBench / GRN suite: cell単位で中央値と率。**平均 $`R^2`$ は外れ値で壊れるため主指標にしない**
  （GPU_RUN4のreconstruction mean $`-6.42`$）。
- 層解析: 式単位。token単位を独立標本として扱わない。
- paired比較: 同一seed・同一問題で条件を比べる。

## 11.3 報告

- 未罰則値と penalized 値の両方を報告し、どちらが主かを明記する（GPU_RUN4 §7 の混乱を繰り返さない）。
- 率については Wilson 区間を使う（正規近似は0や1の近くで壊れる）。
- **失敗タグの内訳を必ず併記する。**

## 11.4 Rank stability

3 seed間の層rankingについて Spearman / Kendall を計算する。
**tie（同順位）がある場合はtie-aware rankingを使う。** GPU_RUN2では罰則値への飽和により
Spearman = 1.0 が見かけ上出た（README §6.7）。同じ罠を避ける。

---

# 12. 保存schema

GPU_RUN4 §16 を継承し、次を追加する。

```json
{
  "prediction": {
    "rational_form": true,
    "saturating_form": false,
    "rational_components": [true, false],
    "div_nodes": 1,
    "variable_denominator_depth": 2
  },
  "intervention": {
    "layer": "decoder_7",
    "method": "mean_patch",
    "alpha": 0.5,
    "delta_ce": 0.43,
    "delta_ted_median": 2.1,
    "delta_skeleton_exact": -0.04,
    "delta_gen_r2_median": -0.11,
    "beam_candidates_saved": 50,
    "decode_failures": []
  },
  "preregistration": {
    "id": "P3",
    "statement": "beam_rational_rate < 0.05",
    "committed_at_commit": "<sha>",
    "outcome": "hit | miss | undecidable"
  }
}
```

run-idは `gpu_run5_<yyyymmdd>_<commit8>`。Phase単位でresume可能にする。

---

# 13. Go / No-Go基準

## Go 1: Track A-2（GRN suite）へ進む条件 — Phase 1後

- P1–P3の判定が出ている
- **P3が的中（`beam_rational_rate < 0.05`）した場合**: 仮説は支持。予定どおりPhase 2–3へ進む
- **P3が外れた場合（有理式候補が5%以上）**: ODEFormerのpriorは有理式を含む。
  この場合、GRN回復失敗の原因は prior ではなく別（次元、識別可能性、選択関数）にある。
  Phase 2–3の設計を「なぜ有理式を出せるのに正しい有理式を出せないか」へ組み替えてから進む

## Go 2: Phase 3の結果をResult Aとする条件

- 720 cell すべてに失敗理由が付いている
- 真式60本のparse / canonical / skeletonがPhase 2で検証済み
- reconstruction中央値だけで「再現成功」と書いていない

## Go 3: DREAM4（D3b）へ進む条件

- checkpointの `max_dimension` が10以上であることをPhase 0で確認できた
- SBML復元した真式がGNW公開無ノイズ時系列を再現する（D3a成功）
- **いずれか1つでも不成立ならD3bは実施しない。** 部分ネットワークの切り出しで代替しない

## Go 4: 介入後beam decode（Phase 6）へ進む条件

- control hookが全介入方式でbaselineを変えない
- 補間 $`\alpha`$ について $`\Delta`$CEが飽和していない領域が存在する
- 固定パネルがPhase 5で凍結済みであり、成功例の事後選択が起きていない

## Go 5: 選択FTを主張として報告する条件

- validationで full が frozen を上回る設定が存在する（$`C_l`$ の分母が成立）
- **不成立の場合**: 「本モデル・本corpus規模ではRQ7を検定できない」と明記して打ち切る。
  GPU_RUN4と同じ表を再掲しない

## No-Go / redesign

次のいずれかが起きたらPhaseを止め、計画を書き直す。

- GRN suiteの軌道の30%以上が定常張り付きまたは発散
- 介入後decodeのvalid rateがbaselineで0.5未満（パネル設計の失敗）
- 拡大corpusでもIOLE差が $`10^{-3}`$ のままで、seed間順位相関が0近傍（層rankingが雑音）
- 予測P1–P7のうち4つ以上が外れる（前提の理解が誤っている。再解釈してから進む）

---

# 14. 主成果物

| # | 成果物 | 内容 |
|---|---|---|
| 1 | `GPU_RUN5_rational_prior_report.md` | Track A。ODEBench再解析 + GRN suite。P1–P5の判定 |
| 2 | `GPU_RUN5_layer_analysis_report.md` | Track B。16層のprobe / lens / 因果 / IOLE / 選択FT。P6–P7の判定 |
| 3 | `GPU_RUN5_cross_model_synthesis.md` | Track C。RUN2–RUN5の指標間順位不一致の統合 |
| 4 | `preregistration_outcome.json` | P1–P7の的中判定（機械生成） |
| 5 | problem-level formula table | 真式 / selected予測 / beam oracle / TED / rational_form のCSV |
| 6 | README §13 の更新 | 「未決の一覧」から、確定した項目を計画書へ移す |

レポートはGPU_RUN4と同じく **§事実 / §RQ判定 / §考察 / §限界 / §提案** を分離する。

---

# 15. 現時点で未確定の項目

Phase 0–2で決めてから本実験へ入る。**test結果を見てから変えない。**

1. checkpointの `max_dimension`（D3の可否を左右する）
2. 層解析corpusを既定3,000式にするかstretch 30,000式にするか（Phase 5でthroughput実測後）
3. GRN suiteのHill係数グリッド $`n\in\{1,2,4\}`$ が妥当か（$`n=1`$ はMichaelis–Menten型で分母の非線形性が弱い）
4. 公式generatorのtrain/testモード切替が使えるか（使えない場合は限界として明記）
5. 介入後beam decodeのパネルを24問題より増やせるか（予算に余裕があれば48へ）
6. `saturating_form`（sigmoid型）をHill型有理式と同じ集計に含めるか分けるか
7. GPU_RUN2のGNW G01–G08 を、閉じた系へ拡張して再利用できるか（できればRUN2との橋渡しになるが、
   数値は混ぜない）

---

# 16. GPU_RUN5の研究上の位置付け

GPU_RUN2はNeSymReSで「数値は合うが構造は回復しない」を観測し、その原因を **有理式priorの欠落** と推測した。
GPU_RUN3はNDformerで「読み出せる層と因果的に効く層が逆転する」を観測した。
GPU_RUN4はODEFormerで前者を再確認したが、後者については検出力不足で判定できなかった。

GPU_RUN5は、**この2つの推測をそれぞれ検定可能な形にする** runである。

- 有理式prior仮説は、**既に保存されている約12,600件のbeam候補**で今日にでも判定できる。
  これがGPU_RUN4の最大の未回収資産である。
- 層解析と式回復の接続は、**約39分の介入後beam decode**で得られる。
  これが3世代にわたって欠落していた1つの実験である。

したがってGPU_RUN5は、新しいモデルや新しいベンチマークを増やす run ではなく、
**既に持っているデータと既に作った評価器から、まだ引き出していない答えを引き出す** run である。

予測が外れた場合も成果になる。P3が外れれば「ニューラルSRのpriorは有理式を含むが正しい有理式を選べない」
という別の失敗機序へ研究が移る。P6が外れれば「CEで測った層重要度は数式回復の層重要度と別物」という、
層解析の方法論そのものへの警告になる。**どちらに転んでも報告できるよう、予測をtest前に固定することが本計画の要点である。**
