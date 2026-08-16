# GPU_RUN2 研究結果レポート

**研究名:** Layer-wise Analysis of Neural Symbolic Regression for Discovering Gene Regulatory Dynamics (LANSR)  
**実験:** GPU_RUN2  
**run ID:** `gpu_run2_20260815_1d91927`  
**実行日:** 2026-08-15–2026-08-16  
**レポート作成日:** 2026-08-16  
**実験に使用したGit commit:** `1d919278b61172bec9e09465e7c04e3c46ef0892`  
**実験時branch:** `main`（実行時clean）  
**Repository:** `https://github.com/blabo25226/Layer-wise_Analysis_of_NSR_for_Discovering_GRD`

---

## 0. 要約

GPU_RUN2は、GPU_RUN1で残った「上位層を選ぶこと自体に意味があるのか」「数値誤差が低いだけでなく正しい数式構造を回復できるのか」「NeSymReS内部のどの層が何を担うのか」という問題を、**GeneNetWeaver (GNW) に由来する既知真式付き合成データだけに限定して検証した実験**である。

今回のrunは`status=complete`で終了し、最終化時に8,940 recordsが保存され、finalize時のissuesは0件だった。GPU_RUN2ではDREAM4、ヒト時系列、有限差分、empirical regulator selection、TPSRなどを意図的に除外している。したがって本レポートの結論は、**oracle変数と解析的な真の微分値が与えられるGNW合成問題上でのNeSymReS層解析とfine-tuning**に限定される。

主な結果は次の通りである。

1. **層表現には明確なdecoder優位の信号がある。**  
   main validationのlinear probeでは全decoder層でalgebraic template accuracyが1.0となり、operator数の回帰でも`decoder_0`–`decoder_4`は \(R^2 \approx 0.91\)–0.95だった。encoderの同指標は概ね0.49–0.64であり、decoder表現から数式全体の構造情報を強く読み出せた。

2. **単一層fine-tuning (IOLE) では`decoder_4`が最も安定した適応先だった。**  
   main viewではTop 1=`decoder_4`、Top 3=`decoder_4, decoder_1, decoder_0`、structure-holdout viewでもTop 1=`decoder_4`、Top 3=`decoder_4, decoder_2, decoder_1`だった。異なる候補選択viewでも`decoder_4`がTop 1、`decoder_1`がTop 3に共通して残った。

3. **selective FTはmain testのdomain-ID数値精度でFull FTを上回った。**  
   noise=0.0ではfailure-aware median NMSEがTop 1=0.0339、Top 3=0.0397に対しFull=0.0837、noise=0.1でもTop 1=0.0407、Top 3=0.0394に対しFull=0.0645だった。Top 1/3のvalid rateは両noiseで100%だった。

4. **ただし「Top 1–3はFull FTと同等」という事前判定はmain testでは確立しなかった。**  
   保存recordをseedごとにfailure-aware medianへ集約してStudentのt区間を再計算すると、Top 1/3 − Fullの95% CIは事前margin `[-0.05, 0.05]`へ完全には入らなかった。平均差はTop側が良い方向だったが、3 seedsではFullの不安定性が大きい。

5. **rankingの付加価値はnoise依存だった。**  
   main testのTop 3 − fixed Random 3はnoise=0.0で平均差−0.00871、95% CI `[-0.01213, -0.00529]`となりTop 3が一貫して良かった。一方noise=0.1では−0.00373、95% CI `[-0.02139, 0.01393]`で0を跨いだ。よって「上位層選択はrandomより常に優れる」とは言えず、**clean条件では支持、10% noise条件では未支持**である。

6. **数値精度とsymbolic recoveryは強く乖離した。**  
   main testで得られたskeleton recoveryはほぼすべて単純な`G01` basal familyに由来した。nontrivialなHill制御を含む`G02`–`G08`について、今回確認した主条件ではskeleton recoveryは0だった。

7. **structure-OOD (`G07`–`G08`) の数式構造回復は全条件0%だった。**  
   一方でTop 3のdomain-ID NMSEはnoise=0.0で0.0469、noise=0.1で0.0467まで下がった。つまり、未知構造を正しく発見できなくても、別構造の式で観測領域内の数値を近似できた。

8. **fine-tuningはdomain-IDを改善する一方、domain-OODを悪化させた。**  
   main testでfrozenのdomain-OOD NMSEはnoise=0.0/0.1で約0.050/0.052だったが、Top 1/3は約0.11、Fullは約6.65/3.92まで悪化した。structure-OODでも同傾向が強い。selective FTはFullよりは大幅に頑健だが、pretrained priorの外挿性を一部失っている。

9. **Full FTは特にstructure-OODで不安定だった。**  
   structure-OOD testのvalid rateはFullがnoise=0.0で71.1%、noise=0.1で67.2%だったのに対し、Top 1は100%/98.9%、Top 3は97.2%/98.3%だった。少数層FTには、少なくとも生成安定性の面でFull FTより強い正則化効果が示唆される。

10. **Phase 4のablation/intervention順位には実装上の解釈問題がある。**  
    実行commitの`ablation_ranking()`は介入後NMSEの**小さい順**に並べ、`intervention_ranking()`も劣化の小さい層を上位にする実装だった。したがって保存された順位は「重要度順」ではなく、実質的に**介入への頑健性順**である。前処理済み`rank_agreement`をそのまま「因果的重要度の一致」と解釈してはいけない。このコードはレポート作成時点のcurrent `main`でも同じだった。なおPhase 5のTop層はIOLE順位から選ばれているため、この向きの問題はPhase 5のTop 1/Top 3層集合そのものには影響しない。

総合すると、GPU_RUN2は、**「NeSymReSのGRN適応はdecoder側、とくに`decoder_4`周辺へ強く局在し、少数decoder層のFTはFull FTより安定してdomain-ID性能を改善し得る」**ことを支持した。一方で、**「正しいGNW数式構造を未知構造まで回復できる」ことは支持されず、数値近似と数式発見が明確に分離した。**

---

## 1. GPU_RUN2の目的と研究範囲

GPU_RUN2の更新済み計画では、主目的を次の3点に限定している。

1. encoder・decoder各層の役割をprobe、single-layer fine-tuning (IOLE)、ablation、CKA、activation intervention、DecoderLensから解析する。
2. 少数の重要層だけをfine-tuningする条件をFull FTおよびfixed Random FTと比較し、数値精度とsymbolic recoveryの両方を評価する。
3. 真式と予測式をproblem単位で直接比較できる成果物を保存する。

GPU_RUN2では以下を扱っていない。

- 有限差分による微分値近似
- DREAM4
- ヒト時系列データ
- empirical regulator selector
- 実データからの新規GRN候補式提案
- TPSR
- NSR-gvs
- large beamその他のtest-time computation

したがって本runは、実データ適用の結論を出す実験ではなく、**NeSymReS内部解析とGNW合成式への適応を独立して検証するためのmechanistic / methodological run**である。

---

## 2. 実行provenance

### 2.1 実行環境

root `manifest.json`に保存された実環境は次の通りである。

| 項目 | 実値 |
|---|---|
| run ID | `gpu_run2_20260815_1d91927` |
| status | `complete` |
| Python | 3.10.20 |
| PyTorch | 2.5.1+cu124 |
| GPU | NVIDIA GeForce RTX 2070 |
| CPU | Intel Core i7-8700 @ 3.20 GHz |
| OS | Linux 7.0.0-29-generic x86_64 |
| source branch | `main` |
| source commit | `1d919278b61172bec9e09465e7c04e3c46ef0892` |
| git working tree | clean |
| decode timeout | 30 s/problem |
| NeSymReS checkpoint | `100M.ckpt` |
| checkpoint SHA256 | `62aedc41fdb67ecbe3679f5ef030e7ef2bf0f4471c461b68d8814358968b324f` |
| GNW source commit | `5016f55ab04c111f29d7d0b3a4881d4725d49467` |
| final record数 | 8,940 |
| finalize issues | 0 |
| archive SHA256 | `958814de24ca61b8c6787b806d6b2ed57e46342fa9c0e22bc58f4ccda925b58f` |

レポート作成時点のGitHub `main`は実験後のcommitまで進んでいる。したがって、**結果の再現性を議論するときはcurrent mainではなく上記source commitを基準にする。**

### 2.2 seedとnoise

固定されたseed bundleは次の3組である。

- data seed 101 / model seed 0
- data seed 202 / model seed 1
- data seed 303 / model seed 2

noiseは独立に

- `0.0`
- `0.1`

の2条件を実行した。

計画書ではnoise条件を混ぜて主性能を集計しないことが明記されているため、本レポートの主要表もnoise別に示す。

---

## 3. 合成データと評価設計

### 3.1 GNW family

GPU_RUN2ではGeneNetWeaver由来の8 familyを固定した。

| Family | 構造 |
|---|---|
| G01 | basal transcription + degradation |
| G02 | single activator |
| G03 | single repressor |
| G04 | two independent activators |
| G05 | two complex-forming activators |
| G06 | activator + deactivator |
| G07 | enhancer + repressor, two-module mixture |
| G08 | two enhancer modules, two-module mixture |

各family 30 parameter variants、合計240 problemsを生成し、familyごとに18 train / 6 validation / 6 testへ分割した。

### 3.2 structure holdout

未見構造への一般化を別軸で評価するため、

- structure-train: G01–G05
- structure-validation: G06
- structure-test: G07–G08

を固定した。

structure-testではG07/G08を層選択にもhyperparameter選択にも使用していない。

### 3.3 入力と教師値

- oracle regulatorのみをNeSymReS/PySRへ入力
- 対象遺伝子自身 \(x_i\) は常に入力
- 解析的な真式 \(f(x)\) を直接評価して教師値を作成
- 有限差分は不使用
- train points: 1,024
- independent domain-ID points: 256
- independent domain-OOD points: 256
- domain-ID range: `[0.1, 2.0]`
- domain-OOD range: `[0.05, 2.5]`

よって今回の誤差は有限差分やregulator selection誤差を含まない。これは実データよりかなり理想化された上限評価である。

### 3.4 operator制約

主実行の意味上のoperatorは

- `add`
- `sub`
- `mul`
- `div`
- integer power 2–5
- constants

に制限した。

`sin`, `cos`, `tan`, `exp`, `log`, `sqrt`, `abs`等は除外された。GPU_RUN1で問題になった不要な`tan`や危険な自由べき乗を主探索空間から除いた設計である。

---

## 4. 評価指標の読み方

GPU_RUN2の`aggregate_prediction_scores()`では、主`penalized_nmse`は**平均ではなく中央値**である。

invalid decodeには

- NMSE = \(10^6\)
- \(R^2=-1\)

相当のfailure penaltyを入れたうえで中央値を取る。

この設計には2つの意味がある。

1. 極端な有限NMSE外れ値に平均が支配されることを防ぐ。
2. decode failureを完全に除外しない。

一方で、failure率が50%未満なら中央値がfailure penaltyへ到達しないため、**20–30%程度のfailureでもpenalized median自体は良好に見えることがある。**  
そのため本レポートではNMSEとvalid rateを必ず併記する。

---

# 5. Phase 2: baseline

## 5.1 NeSymReS pretrainedとPySR

保存済みtest recordsをnoise別に再集計した。

| noise | Method | domain-ID penalized median NMSE | domain-OOD penalized median NMSE | valid rate | skeleton | symbolic equivalence |
|---:|---|---:|---:|---:|---:|---:|
| 0.0 | NeSymReS pretrained | 0.04947 | 0.04901 | 1.000 | 0.000 | 0.000 |
| 0.0 | PySR | **0.01419** | **0.02168** | 0.701 | **0.125** | **0.125** |
| 0.1 | NeSymReS pretrained | 0.05123 | 0.05009 | 1.000 | 0.000 | 0.000 |
| 0.1 | PySR | **0.00768** | **0.01351** | 0.792 | **0.125** | 0.000 |

PySRはmedian NMSEではNeSymReS pretrainedを大きく上回ったが、valid rateは70–79%に留まった。したがって「PySRが全面的に優れる」とは言えず、**精度と生成成功率のtrade-off**がある。

さらにfamily別に確認すると、PySRの12.5% skeleton recoveryはG01だけであり、G02–G08のnontrivial GNW構造を回復したものではなかった。

---

# 6. Phase 3: 表現解析と候補層固定

## 6.1 Linear probe

main validationで保存された主probe結果は次の通りである。

### Algebraic template classification

- `decoder_0`–`decoder_4`: **accuracy 1.0**
- best encoder: `encoder_3` = 0.781
- `encoder_4` = 0.760

### Operator数回帰

- `decoder_0`: \(R^2=0.909\)
- `decoder_1`: \(R^2=0.922\)
- `decoder_2`: \(R^2=0.944\)
- `decoder_3`: \(R^2=0.951\)
- `decoder_4`: \(R^2=0.948\)
- best encoder `encoder_4`: \(R^2=0.638\)

### Next-token classification

next-tokenではencoder後半も強く、

- `encoder_4`: 0.698
- `encoder_pma`: 0.677
- `encoder_3`: 0.656
- `decoder_0`: 0.615
- `decoder_3`, `decoder_4`: 0.604

だった。

この組合せから、少なくともlinear probeで読み出せる情報について、

- **decoder hidden stateは数式全体のtemplateやoperator構成を非常に強く持つ**
- encoder後半は次tokenに関係する情報も持つ
- 「式構造情報がencoderだけで完成してdecoderが単純に出力する」というモデルではない

ことが示唆される。

### main probe ranking

mean rankによるmain rankingは

1. `decoder_0`
2. `decoder_3`
3. `encoder_4`
4. `decoder_1`
5. `decoder_4`
6. `decoder_2`
7. `encoder_3`
8. `encoder_5`
9. `encoder_pma`
10. `encoder_1`
11. `encoder_2`
12. `encoder_0`

であり、Top 5をPhase 4候補としてtestを見る前に固定した。

候補は

```text
decoder_0
decoder_3
encoder_4
decoder_1
decoder_4
```

である。

`output_head`は候補層に含めていない。

## 6.2 CKA

encoder表現のlinear CKAは`encoder_0`を基準に概ね高かった。

| Layer | CKA |
|---|---:|
| encoder_0 | 1.000 |
| encoder_1 | 0.936 |
| encoder_2 | 0.974 |
| encoder_3 | 0.957 |
| encoder_4 | 0.965 |
| encoder_5 | 0.940 |
| encoder_pma | 0.972 |

したがってencoder内部表現のgeometryは層間で大幅に完全別物になるわけではない。

一方、CKA rankingとprobe rankingの相関は強くなく、**「表現が似ていること」と「特定の数式属性が線形に読み出せること」は別の概念**である。

## 6.3 DecoderLens

DecoderLensの保存summaryは

- decode steps: 27,281
- parseable: 3,436
- parseable rate: 12.59%

だった。

encoder layer rankingは

```text
encoder_5
encoder_4
encoder_3
encoder_0
encoder_1
encoder_2
```

で、probeとのSpearman相関は約0.657だった。

後段encoder (`encoder_3`–`encoder_5`) が比較的上位に来る点は、decoderが利用可能な表現がencoder後半で形成される可能性と整合する。

ただしDecoderLensでは本来最終encoder表現を受けるdecoderへ中間表現を直接渡すためdistribution shiftがある。parseable rate 12.6%をそのまま通常decode性能として解釈してはいけない。

## 6.4 Gradient norm

保存値ではdecoder側のgradient normも大きく、

- `decoder_2`: 3.107
- `decoder_3`: 2.911
- `decoder_1`: 2.616
- `decoder_4`: 2.393
- `decoder_0`: 1.700

だった。

gradient norm自体は候補選択指標ではないが、GRNへの教師あり適応でdecoder blockへ大きな更新信号が流れることを示す補助的観測である。

---

# 7. Phase 4: IOLE・ablation・activation intervention

## 7.1 IOLEによる単一層fine-tuning

main viewの保存IOLE rankingは

```text
decoder_4
decoder_1
decoder_0
encoder_4
decoder_3
```

だった。

これに基づいてPhase 5条件は次のように固定された。

```text
Top 1  = [decoder_4]
Top 3  = [decoder_4, decoder_1, decoder_0]
Random 3 = [decoder_0, decoder_4, decoder_3]
```

structure-holdout viewではG07/G08を候補選択から除外し、

```text
Top 1  = [decoder_4]
Top 3  = [decoder_4, decoder_2, decoder_1]
Random 3 = [decoder_3, encoder_5, decoder_1]
```

となった。

**`decoder_4`がmainとstructure-holdoutの両方でTop 1になったことは、GPU_RUN2の層解析で最も頑健な結果の一つである。**  
また`decoder_1`も両Top 3に含まれた。

## 7.2 Phase 4 raw scoreの問題

main Phase 4 panelのraw IOLE scoreは次のようになった。

| Condition | raw mean NMSE |
|---|---:|
| pretrained | 0.0804 |
| decoder_4 | **0.0486** |
| decoder_1 | 0.1228 |
| decoder_0 | 0.7996 |
| encoder_4 | \(3.94\times10^6\) |
| decoder_3 | \(3.55\times10^{15}\) |
| all_params | \(4.70\times10^{263}\) |

Full FTのscoreがpretrainedより悪いため、事前に想定した

\[
C_l=\frac{L_{\rm base}-L_l}{L_{\rm base}-L_{\rm full}}
\]

型のnormalized contributionは全候補で`NaN`となった。保存`contributions.json`も全層`NaN`である。

コードはこの場合、候補をraw layer score昇順へfallbackしてIOLE rankingを作る。

したがってPhase 4のTop 3は「Full改善量を何%回復した層」ではなく、**outlierを含むraw mean panel NMSEが相対的に小さかった層**である。ここはGPU_RUN1の寄与度解釈とは区別すべきである。

なおPhase 5ではTop 1/Top 3が実testで良好だったため、層集合そのものが無意味だったわけではない。しかし、**層選択統計量を今後よりrobustにする必要がある。**

## 7.3 Ablation / interventionの実スコア

main候補5層の集約ablation NMSEは

| Layer | zero-ablation NMSE |
|---|---:|
| encoder_4 | 111.23 |
| decoder_0 | 416,666.99 |
| decoder_3 | 1,000,000 |
| decoder_1 | 1,000,000 |
| decoder_4 | 1,000,000 |

activation replacementでは

| Layer | intervention NMSE |
|---|---:|
| encoder_4 | 0.1559 |
| decoder_0 | 2648.51 |
| decoder_3 | 2648.51 |
| decoder_1 | 2648.51 |
| decoder_4 | 2668.89 |

pretrained baselineは0.0804である。

したがって**絶対的な介入効果**を見ると、

- `encoder_4`への介入は性能を悪化させるが、decoder介入よりはるかに軽い
- decoder blockを壊すと生成性能が桁違いに崩壊する
- hard ablationでは`decoder_1/3/4`がfailure penalty \(10^6\)へ飽和し、これら3層の相対的な重要度は識別できない
- activation interventionでは`decoder_4`が最大劣化、他decoderもほぼ同程度に大きく劣化

と読むのが自然である。

この結果は、probeと合わせると**NeSymReSの数式生成機能がdecoder側へ強く依存する**ことを支持する。

---

## 7.4 重要: 保存rankingsの向きに実装上の問題がある

実行commitの`src/evaluation/gpu_run2_rankings.py`では、

```python
def ablation_ranking(...):
    return sorted(candidates, key=lambda name: ablation_scores[name])
```

となっており、NMSEの**小さい層を上位**にしている。

activation interventionも、lower-is-better NMSEに対して

```text
delta = baseline - intervened
```

を計算した後に降順sortするため、結果として**劣化の小さい層が上位**になる。

そのため保存`rankings.json`の

```text
ablation:
encoder_4 > decoder_0 > decoder_3 > decoder_1 > decoder_4

intervention:
encoder_4 > decoder_0 > decoder_3 > decoder_1 > decoder_4
```

は「重要度ranking」ではなく、実質的には**介入に対するrobustness ranking**である。

保存されたablation–intervention Spearman=1.0を

> 「2種類の因果解析が同じ重要層を完全に再現した」

と解釈するのは不適切である。

さらにhard ablationには \(10^6\) のtieが複数あるため、順位相関自体もtie-breakingの影響を受ける。

### 修正した科学的解釈

実スコアの劣化量を基準にすると、概略は

```text
強く必要:
decoder_4 / decoder_3 / decoder_1 / decoder_0

介入に比較的頑健:
encoder_4
```

である。

とくに`decoder_4`は

- main IOLE Top 1
- structure-holdout IOLE Top 1
- activation interventionで最大劣化群
- probeで高いtemplate/operator情報

という複数の観点を併せ持つ。

したがってGPU_RUN2から現時点で最も強く主張できるのは、**encoder_4が最重要なのではなく、decoder中後段、とくにdecoder_4周辺が「適応可能性」と「生成への機能依存」の両方で重要である**という方向である。

### Phase 5への影響

Phase 5のTop 1/Top 3は**IOLE ranking**から構築されており、ablation/intervention rankingからは選ばれていない。

したがってこのranking方向の問題は、

- Phase 4の因果的重要度の文章解釈
- method間rank agreement
- ablation/intervention順位図

には影響するが、

- Top 1=`decoder_4`
- Top 3の実学習
- Phase 5 testの予測record

自体を無効化するものではない。

レポート作成時点のcurrent `main`でも、このranking helperは実行commitと同じ向きのままだった。

---

## 7.5 seed安定性の再検討

保存`seed_snapshots.json`には

- 3 seed bundles
- 2 noise条件

の合計6 snapshotsがある。

元の`ranking_stability`出力はこの6 snapshots間の全pairを集計するため、**noise=0とnoise=0.1のcross-noise pairも含む。**  
これは「noiseは混ぜずに報告する」というGPU_RUN2計画と完全には整合しない。

本レポートでは保存snapshotからnoise別に再計算した。

### IOLE ranking

| noise | mean pairwise Spearman | mean Kendall |
|---:|---:|---:|
| 0.0 | 0.600 | 0.467 |
| 0.1 | 0.867 | 0.733 |

noise=0.1ではかなり高い一方、cleanでは中程度である。

ただし`decoder_4`はnoise=0.0の全3 seedで1位、noise=0.1でも2 seedで1位、残る1 seedで2位だった。

### 介入結果

ablationはdecoder側がfailure penaltyへtieするため、見かけ上の順位安定性1.0を強く解釈すべきではない。

activation interventionを「劣化の大きい順」に直して見ると、`encoder_4`は全snapshotで最下位、decoder群が上位だった。decoder内部の細かい順序はseedで変わる。

このため、**encoder対decoderという粗い機能差は安定しているが、decoder_0/1/3/4の厳密な因果順位までは確定していない**とするのが妥当である。

---

# 8. Phase 5: main test

## 8.1 noise=0.0

| Condition | domain-ID penalized median NMSE | domain-OOD penalized median NMSE | valid rate | skeleton | symbolic equiv. | mean complexity |
|---|---:|---:|---:|---:|---:|---:|
| Frozen | 0.05329 | **0.04974** | **1.000** | 0.000 | 0.000 | 29.34 |
| Full | 0.08372 | 6.65167 | 0.958 | **0.125** | 0.0556 | 38.87 |
| Top 1 | **0.03387** | 0.11111 | **1.000** | **0.125** | 0.0625 | 30.37 |
| Top 3 | 0.03970 | 0.12046 | **1.000** | **0.125** | **0.0694** | 32.38 |
| Random 3 | 0.05048 | 0.19592 | 0.993 | **0.125** | 0.0625 | 36.47 |

### 観測

- domain-IDではTop 1が最良、Top 3が次点。
- Top 1/Top 3はFullより低NMSEかつ高valid rate。
- FrozenはIDでは劣るがdomain-OODでは最良。
- Full FTのdomain-OOD悪化が非常に大きい。
- skeleton recovery 12.5%は後述の通りG01だけである。

## 8.2 noise=0.1

| Condition | domain-ID penalized median NMSE | domain-OOD penalized median NMSE | valid rate | skeleton | symbolic equiv. | mean complexity |
|---|---:|---:|---:|---:|---:|---:|
| Frozen | 0.05299 | **0.05161** | **1.000** | 0.000 | 0.000 | 28.76 |
| Full | 0.06455 | 3.92346 | 0.986 | 0.0208 | 0.000 | 40.75 |
| Top 1 | 0.04066 | 0.11326 | **1.000** | 0.000 | 0.000 | 32.91 |
| Top 3 | **0.03936** | 0.10667 | **1.000** | 0.000 | 0.000 | 33.19 |
| Random 3 | 0.04340 | 0.14169 | 0.986 | 0.0347 | 0.000 | 37.49 |

### 観測

- 10% noise下でもTop 1/Top 3のID NMSEはFrozen/Fullより良い。
- Top 1/Top 3のvalid rateは100%。
- 一方、Top 1/Top 3のskeleton / symbolic equivalenceは0へ落ちた。
- **数値精度は保たれているのに構造回復が消失しており、noiseが「数値近似」と「構造同定」に異なる影響を与える。**
- domain-OODは依然Frozenより悪い。

---

# 9. 事前判定に対する統計的評価

本レポートでは、独立性を過大評価しないため、各noiseについてまず48 main test equationsを**seedごとのfailure-aware median NMSE**へ集約し、その3 seed値のpaired差にStudentのt区間を計算した。

これは保存aggregateに直接書かれていたCIではなく、**保存済みproblem recordsから本レポートで再計算した評価**である。

## 9.1 Top 1 / Top 3 vs Full: 同等性

事前equivalence margin:

```text
[-0.05, 0.05]
```

### noise=0.0

| 比較 | mean paired difference | 95% t CI |
|---|---:|---:|
| Top 1 − Full | -0.06109 | [-0.19799, 0.07581] |
| Top 3 − Full | -0.05429 | [-0.17373, 0.06515] |

### noise=0.1

| 比較 | mean paired difference | 95% t CI |
|---|---:|---:|
| Top 1 − Full | -0.02669 | [-0.07326, 0.01988] |
| Top 3 − Full | -0.02779 | [-0.06866, 0.01308] |

いずれもCI全体が`[-0.05,0.05]`へ入らない。

したがってmain testについて、

> **Top 1/Top 3がFull FTと事前margin内で統計的に同等**

という判定は成立しない。

ただし平均差は全て負であり、点推定上はTop 1/3の方が良い。問題は「選択FTがFullに届かない」のではなく、むしろ**Fullのseed間不安定性が大きく、狭い結論を3 seedsで確定できない**ことである。

## 9.2 Top 3 vs fixed Random 3: rankingの付加価値

### noise=0.0

seed別Top3−Random3:

```text
-0.00835
-0.01023
-0.00755
```

平均:

```text
-0.00871
```

95% t CI:

```text
[-0.01213, -0.00529]
```

0を跨がないため、**clean条件ではTop 3がこのfixed Random 3より良い**。

### noise=0.1

seed別差:

```text
-0.00390
+0.00346
-0.01075
```

平均:

```text
-0.00373
```

95% t CI:

```text
[-0.02139, 0.01393]
```

0を跨ぐため、計画通り優越性を主張しない。

### 結論

ranking付加価値は

- noise=0.0: **支持**
- noise=0.1: **未支持**

である。

GPU_RUN1で未支持だったTop-vs-random仮説に対し、GPU_RUN2ではclean条件で初めて明瞭な支持が出たが、noise robustnessまでは示されなかった。

---

## 9.3 Random 3対照の弱点

mainの層集合は

```text
Top 3    = decoder_4, decoder_1, decoder_0
Random 3 = decoder_0, decoder_4, decoder_3
```

であり、**3層中2層 (`decoder_0`, `decoder_4`) が重複する。**

したがってmainのTop3-vs-Random3比較は実質的に

```text
decoder_1 を追加するか
decoder_3 を追加するか
```

の差にかなり近い。

これは恣意的に選び直したものではなく、事前固定seedで生成された正当なrandom controlである。しかし、**「ranked selection全体 vs random selection全体」を強く識別する対照としては弱い。**

次runでは、testを見る前に複数のrandom setを固定し、random-set varianceを推定する設計が望ましい。

---

# 10. Symbolic recoveryの詳細

## 10.1 main testのrecoveryはG01に集中

main testをfamily別に確認すると、noise=0.0のTop 1/Top 3/Full/Random 3で得られた12.5% skeleton recoveryは、**G01の18/18 recordsに対応し、G02–G08は0%だった。**

G01は

\[
V-\delta x_1
\]

という最も単純なbasal transcription + degradation familyである。

つまり、aggregateだけを見ると「12.5%のGNW構造を回復した」と読めるが、より正確には

> **8 familyのうち最も単純なG01だけを回復し、Hill型制御を含むG02–G08は回復できなかった**

という結果である。

noise=0.1ではTop 1/Top 3のG01 skeleton recoveryすら0になった。

## 10.2 exact recovery

全主要条件でexact recoveryは0だった。

これは係数がわずかに異なるだけでもexact一致しないため、exact=0だけで失敗を断定すべきではない。ただし、G02–G08ではskeleton / symbolic equivalenceも0なので、単なる係数誤差ではない。

---

# 11. CTC_NSR-style reproduction bias

GPU_RUN2のreproduction判定はNeSymReSの未知の100M pretraining corpusではなく、**今回のfine-tuning corpusに対するtemplate membership**である。

main testでは、

| Condition | reproduced rate | novel recovery rate |
|---|---:|---:|
| Frozen | 0.0000 | 0.0000 |
| Full | 0.0729 | 0.0000 |
| Top 1 | 0.0625 | 0.0000 |
| Top 3 | 0.0625 | 0.0000 |
| Random 3 | 0.0799 | 0.0000 |

さらに、reproduced predictionに限るとFull/Top1/Top3/Random3の`reproduced_skeleton_rate`は1.0だった。

一方、novel predictionのskeleton recoveryは0だった。

したがってGPU_RUN2 main testで観測された構造回復は、

> **fine-tuning corpusに存在するtemplateを再現したケース**

で説明され、新しい構造を生成して正解へ到達した証拠は得られなかった。

これは「fine-tuningが悪い」という意味ではない。main test自体がstructure-IDなので、train familyの構造を再利用することは合理的である。

しかし本研究が将来的に「未知の遺伝子制御式を発見する」ことを目標にするなら、**template reproductionとnovel structural discoveryを分ける必要がある**ことを実データが示した。

---

# 12. Structure-OOD test: G07–G08

structure-OODではG07/G08をfine-tuning trainにも層選択にも使用していない。

## 12.1 noise=0.0

| Condition | domain-ID penalized median NMSE | domain-OOD penalized median NMSE | valid rate | skeleton / symbolic equiv. |
|---|---:|---:|---:|---:|
| Frozen | 0.06592 | **0.04833** | **1.000** | 0 / 0 |
| Full | 0.07354 | 3.16786 | 0.711 | 0 / 0 |
| Top 1 | 0.05112 | 0.34290 | **1.000** | 0 / 0 |
| Top 3 | **0.04686** | 0.74988 | 0.972 | 0 / 0 |
| Random 3 | 0.05056 | 0.47436 | 0.894 | 0 / 0 |

## 12.2 noise=0.1

| Condition | domain-ID penalized median NMSE | domain-OOD penalized median NMSE | valid rate | skeleton / symbolic equiv. |
|---|---:|---:|---:|---:|
| Frozen | 0.06024 | **0.04763** | **1.000** | 0 / 0 |
| Full | 0.07729 | 3.87417 | 0.672 | 0 / 0 |
| Top 1 | 0.05075 | 0.37021 | 0.989 | 0 / 0 |
| Top 3 | **0.04670** | 0.30560 | 0.983 | 0 / 0 |
| Random 3 | 0.05094 | 0.28016 | 0.900 | 0 / 0 |

### 主要結論

1. **Top 3は未知構造でもdomain-ID数値近似を改善した。**
2. **しかし正しいG07/G08 skeletonは1件も回復しなかった。**
3. Full FTはvalid rateが約67–71%まで崩れた。
4. selective FTはFullより大幅に安定。
5. すべてのFT条件でdomain-OODはFrozenより悪化。

CTC_NSR-style reproductionでもstructure-OOD全条件の`reproduced_rate`は0、`novel_recovery_rate`も0だった。

したがって、

> **未知構造を「発見」できたのではなく、未知構造が生む数値関係を別の式で近似した**

という解釈が最も結果に忠実である。

---

# 13. 真式と予測式の具体例

## 13.1 G01: 構造回復成功例

Top 1, noise=0.0, `G01_variant_026`

True:

```text
0.0410681713041529 - 0.0410681713041529*x_1
```

Predicted:

```text
0.0410681595705224 - 0.0410681537570291*x_1
```

- domain-ID NMSE: \(\approx2.7\times10^{-13}\)
- skeleton: 1
- symbolic equivalence: 1
- exact: 0

係数は数値的にほぼ一致しているがexact文字列一致ではない。これはskeleton/equivalenceをexactと分離する必要性を示す良い成功例である。

## 13.2 G02: IDでは良いが構造が違う例

Top 1, noise=0.0, `G02_variant_027`

True:

```text
(-1.70506136426005*x_1*x_2**2
 -0.0285400104160785*x_1
 +1.70506136426005*x_2**2)
/
(59.742843096493*x_2**2 + 1.0)
```

Predicted:

```text
-0.0291459738629776*x_1
+0.00899703019905816*x_2**2*(0.360106348553146*x_2**2 - 1)**2
+0.0254200718899665
```

- domain-ID NMSE: 0.0304
- domain-OOD NMSE: 0.651
- skeleton: 0
- symbolic equivalence: 0

真式はHill型の有理式だが、予測は多項式的なsurrogateである。観測範囲では近似できても、範囲を広げると急速に悪化する。

## 13.3 G07: 未知構造を数値近似した例

Top 1, noise=0.0, `G07_variant_026`

- domain-ID NMSE: 0.0515
- domain-OOD NMSE: 1.575
- skeleton: 0
- symbolic equivalence: 0

予測式は真のtwo-module rational mixtureではなく、多項式的な代替式だった。

この例はGPU_RUN2全体の核心をよく表す。

> **NeSymReSは未知GNW構造をそのまま回復しなくても、学習領域内で低NMSEの代替式を生成できる。**

したがって低NMSEをmechanistic discoveryと呼ぶことはできない。

---

# 14. Fine-tuningと外挿性能

今回最も重要な副次結果の一つは、**fine-tuningによるdomain-ID改善とdomain-OOD悪化の同時発生**である。

main test, noise=0.0:

```text
Frozen OOD  = 0.0497
Top 1 OOD   = 0.1111
Top 3 OOD   = 0.1205
Random 3 OOD= 0.1959
Full OOD    = 6.6517
```

main test, noise=0.1でも同様である。

この結果は、fine-tuningがGNW training range `[0.1,2.0]`へ適応する過程で、

- pretrainedモデルが持っていた比較的穏やかな関数prior
- 範囲外での安定性

を損なっている可能性を示す。

とくにFull FTでは、観測範囲内の誤差を下げようとする自由度が大きく、外挿で発散する高次式・不適切な近似へ移りやすいと考えられる。

一方selective FTはFullより明らかに外挿崩壊を抑える。

したがってselective FTの利点は単なるparameter削減だけでなく、

> **pretrained priorを部分的に保持するregularization**

として理解できる可能性がある。

ただしFrozenのOOD性能には届いていないため、「selective FTで外挿性も改善した」とは言えない。

---

# 15. Noiseの影響

noise=0.0から0.1への変化で最も顕著なのはNMSEではなくsymbolic recoveryだった。

Top 1/Top 3では

```text
noise=0.0:
skeleton = 12.5%

noise=0.1:
skeleton = 0%
```

となった一方、domain-ID median NMSEは約0.034–0.040から約0.039–0.041へしか変化していない。

つまり10% noiseは、

- 数値予測能力を完全には壊さない
- しかし正しい式構造を選ぶ能力を大きく壊す

という非対称な影響を持った。

これはsymbolic regressionにおいて非常に重要である。

数値回帰なら「NMSEがほぼ同じなので頑健」と評価され得るが、**科学的方程式発見としては頑健ではない。**

---

# 16. Selective FTとFull FT

GPU_RUN2ではFull FTよりTop 1/3が良い場面が多かった。

特に、

- main test ID NMSE
- main valid rate
- structure-OOD ID NMSE
- structure-OOD valid rate

でselective FTが優位だった。

考えられる機序は以下である。

### 16.1 過適合の抑制

合成GNW corpusはNeSymReSの元の100M pretrainingに比べれば極めて小さい。全層を更新すると、事前学習で得た一般的なsymbolic priorを大きく壊す可能性がある。

### 16.2 Decoder中心の局所適応

probeとIOLEは、GRN domainへの適応に必要な変更がdecoder側へ集中し得ることを示す。数値集合を解釈するencoder全体を作り直さず、式token分布を作るdecoderの一部だけを動かす方が合理的である可能性がある。

### 16.3 Catastrophic forgetting

Full FTのdomain-OOD崩壊とstructure-OOD valid-rate低下は、catastrophic forgettingに整合的である。

ただしGPU_RUN2だけではweight-spaceのforgettingを直接測定していないため、これは**結果から導かれる仮説**であって確定事実ではない。

---

# 17. GPU_RUN1との関係

GPU_RUN1では`decoder_2`–`decoder_4`が高寄与層として現れ、少数層FTはFull FTへ近い数値性能を示した。しかしTop 3 vs Random 3は95% CIが0を跨ぎ、ranking付加価値は未支持だった。

GPU_RUN2では実験設計を大幅に厳密化した結果、

- main/structure両方で`decoder_4`がIOLE Top 1
- decoder側のprobe信号が非常に強い
- clean main testではTop 3 > fixed Random 3が95% CIで支持

となった。

したがって、**「decoder中後段が適応上重要」というGPU_RUN1の大方向は再現した**と評価できる。

一方、

- 具体的な層順位は完全一致しない
- noise=0.1ではTop-vs-random優越性が消える
- Phase 4のcontribution定義はFullの崩壊によりNaN
- causal ranking helperに方向問題がある

ため、「decoder_4が普遍的に唯一の重要層」と一般化するのはまだ早い。

---

# 18. 計算時間

保存されたwall-timeファイルを単純合計すると、

```text
39,626 s = 約11.01 h
```

だった。

| Segment | seconds | hours | 全体比 |
|---|---:|---:|---:|
| Phase 0 | 6 | 0.002 | 0.02% |
| Phase 1 | 16 | 0.004 | 0.04% |
| Phase 2 validation | 4,453 | 1.237 | 11.24% |
| Phase 2 test | 4,184 | 1.162 | 10.56% |
| Phase 3 interpret | 200 | 0.056 | 0.50% |
| Phase 4 contribution | 7,950 | 2.208 | 20.06% |
| Phase 5 main validation | 86 | 0.024 | 0.22% |
| Phase 5 main test | 8,480 | 2.356 | 21.40% |
| Phase 5 structure validation | 4,743 | 1.318 | 11.97% |
| Phase 5 structure test | 9,508 | 2.641 | 23.99% |

最も高価なのは

1. structure test
2. main test
3. Phase 4 contribution

だった。

Phase 3のprobe/CKA/DecoderLens自体は全体の約0.5%であり、**層候補の表現解析は比較的安価で、decodeを多数繰り返す介入・test評価が支配的**だった。

---

# 19. 研究仮説ごとの判定

## H1. 層ごとに異なる役割・安定した信号があるか

**部分的に支持。**

支持する事実:

- decoder全層でtemplate probe accuracy=1.0
- decoder operator-count \(R^2\) ≈0.91–0.95
- `decoder_4`がmain/structure両IOLEでTop 1
- decoder介入はencoder_4介入より桁違いに性能を壊す
- gradient normもdecoder中後段で大きい

未解決:

- ablation/interventionの保存ranking方向がimportanceと逆
- decoder層同士はfailure saturation/tieがあり厳密順位を決められない
- CKAとの対応は弱い

したがって、

> **decoder側がGRN数式生成・適応に重要**

は支持されるが、

> **decoder_4 > decoder_3 > decoder_1 ...という厳密な因果順位**

までは確定していない。

## H2. Top 1–3がFull FTと同等か

**main testでは事前基準を満たさず、未確立。**

点推定ではTop 1/3がFullより良いが、3-seed t CIがequivalence marginへ完全には入らない。

## H3. rankingにはrandom selectionを超える付加価値があるか

**部分的に支持。**

- noise=0.0: 支持
- noise=0.1: 未支持
- structure-OOD: Top3−Random3 CIは0を跨ぐ

またmain Random3はTop3と2/3層重複するため、強い対照ではない。

## H4. selective FTはsymbolic recoveryを改善するか

**限定的に支持。**

main clean条件ではG01 skeletonを回復したが、G02–G08のnontrivial構造は回復できなかった。

10% noiseではTop 1/3のskeleton recoveryは0。

## H5. 未知構造を回復できるか

**未支持。**

structure-OOD G07–G08では全条件:

```text
skeleton recovery = 0
symbolic equivalence = 0
novel recovery = 0
```

だった。

## H6. 数値精度改善は科学的方程式発見成功を意味するか

**明確に否定された。**

structure-OODでTop 3はNMSEを改善したが正しい構造は0件だった。

これはGPU_RUN2で最も明瞭な科学的結論の一つである。

---

# 20. 重要な実装・解析上の限界

## 20.1 Ablation/intervention rankingの方向

**Critical for interpretation.**

保存rankingはimportanceではなくrobustness方向になっている。現在のmainでも同じ実装を確認した。

既存runを捨てる必要はなく、保存raw scoreから正しい劣化量を再計算できる。

## 20.2 Phase 4のmeanとPhase 5のmedianが不一致

Phase 4 IOLE rankingは極端なfinite outlierを含むmean NMSEに依存し、Phase 5の主評価はfailure-aware medianである。

FullのPhase 4 meanが \(4.7\times10^{263}\)となった結果、normalized contributionが全てNaNとなりfallback rankingが使われた。

今後は層選択と最終評価で同じrobust metricを使う方が解釈しやすい。

## 20.3 Noiseを跨いだranking stability

保存のglobal seed stabilityはnoise 0/0.1間のpairも含む。

主レポートではnoise別安定性を出すべきである。

## 20.4 Random 3は1集合のみ

計画通りの事前固定controlではあるが、random-set varianceを測れない。

さらにmainではTop3と2/3層が重複する。

## 20.5 3 seeds

95% Student t CIは計算できるが、自由度2で非常に不確実である。とくにFullの不安定性がCIを広げている。

## 20.6 Median failure penaltyの限界

PySRのように20–30% failureがあっても、failureが50%未満ならmedian NMSEは低く保たれ得る。

したがってvalid rateは補助指標ではなく、主結果と同格に読む必要がある。

## 20.7 Oracle条件

入力変数集合は正解から与えている。

よって本runはregulator selection性能を何も示さない。

## 20.8 解析的微分

真の \(dx/dt\) を直接使用している。

実データで発生する有限差分・gradient matching誤差への頑健性は未評価。

## 20.9 合成データのみ

DREAM4・ヒトデータへの転移はGPU_RUN2から主張できない。

---

# 21. 今後優先すべき修正・追試

## 優先度A: 既存GPU_RUN2を再解釈するだけでできるもの

1. `ablation_ranking()`を「NMSE増加が大きいほど重要」に修正する。
2. `intervention_ranking()`の符号・sort方向をimportance方向へ修正する。
3. tie-aware rankingまたはrank groupを導入する。
4. 保存`raw_scores`からcorrected causal rankingを再生成する。
5. noise別のrank stability表を正式成果物として保存する。
6. main/structure testのseed-level paired t CIを正式JSON/CSVへ保存する。
7. family別recovery tableを正式成果物へ追加する。
8. `G01`と`G02–G08`を分けてsymbolic recoveryを報告する。

これらは保存済みrecordから可能であり、長時間GPU再実行は基本的に不要である。

## 優先度B: 小規模confirmation run

1. Phase 4層rankingをfailure-aware medianまたは別の事前固定robust scoreで再計算する。
2. ranking metricをPhase 5主指標と一致させる。
3. 複数fixed random setsをtest前に生成する。
4. domain-OOD性能もvalidation段階で**評価指標として記録**する。ただしtestで層選択しない。
5. hard zero ablationだけでなく、より局所的なactivation patchingを追加し、完全破壊によるsaturationを避ける。
6. decoder_1/3/4間の因果差を識別できる介入強度を使う。

## 優先度C: symbolic discovery改善

GPU_RUN3以降では、単にNMSEを下げるより

- structure-OOD skeleton recovery
- novel recovery
- domain-OOD安定性

を改善することを中心目標にした方がよい。

候補として、

- test-time search (TPSR等)
- structure-aware reranking
- symbolic equivalenceを利用した候補選択
- curriculum / template diversity
- noise-aware training
- pretrained priorを保つregularization
- selective FT + constrained search

を比較する価値がある。

ただしGPU_RUN2の結果から最も重要なのは、**探索を強くする前に「低NMSEの間違った式」を成功扱いしない評価設計を保つこと**である。

---

# 22. 総合考察

GPU_RUN2によって、LANSRの研究ストーリーはGPU_RUN1時点より明確になった。

当初は、

> 「寄与度の高い数層をfine-tuningすればFull FTを低コストで再現できるか」

という効率化の問いが中心だった。

しかし今回の結果は、それより深い構造を示している。

## 22.1 NeSymReS内部にはdecoder中心の適応ボトルネックがある可能性

decoderからはtemplateとoperator数が極めて高精度にlinear probeでき、`decoder_4`は異なるviewでも単一層FTの最良候補だった。

これはGRN domain shiftのかなりの部分が、

> 「数値点集合を理解する能力を一から変える」

より、

> 「内部表現をどの数式token構造へ写像するかを変える」

ことで吸収できる可能性を示す。

この仮説は今後、attention pattern、token-specific intervention、decoder-side logit lens等でさらに検証できる。

## 22.2 Selective FTの価値はparameter efficiencyだけではない

Full FTはstructure-OODでvalid rateを大きく失い、domain-OODも壊れた。

Top 1/3は

- ID性能を改善
- valid rateを維持
- Fullより外挿崩壊を抑制

した。

したがってselective FTは単なる「安いFull FT」ではなく、

> **事前学習priorを壊しすぎない制約付きadaptation**

として価値がある可能性が高い。

## 22.3 しかしselective FTだけでは「数式発見」になっていない

最も重要な否定的結果は、G02–G08の構造回復失敗である。

NeSymReSは非常に低いNMSEを出す代替式を生成できるため、数値精度だけを見れば成功に見える。

しかし真式との比較では、

- 分母構造が違う
- Hill rational formを多項式で近似する
- structure-OODで全く異なる式を出す

ケースが多数ある。

この意味でGPU_RUN2は、

> **ニューラルシンボリック回帰において、predictionとdiscoveryは別問題である**

ことを実証したrunと位置付けられる。

## 22.4 LANSRの新規性は「どの層が重要か」だけではない

今後のLANSRは、

1. どの層に数式構造情報があるか
2. どの層を更新するとdomain adaptationできるか
3. どの層を壊すと生成機能が崩れるか
4. その適応が真のsymbolic structure recoveryにつながるか
5. なぜID fitとOOD / symbolic recoveryが乖離するか

を分けて扱うと、研究としてより強くなる。

GPU_RUN2は特に4–5の問題を明確に露出させた。

---

# 23. 最終結論

GPU_RUN2から、現時点で次の結論を採用する。

> **NeSymReSをGNW由来GRN方程式へ適応する際、decoder層、とくに`decoder_4`を中心とする少数層のfine-tuningは、Full FTより安定したdomain-ID数値性能を示した。clean条件ではTop 3が事前固定Random 3より有意に低いseed-level median NMSEを示し、層rankingの付加価値が部分的に支持された。**

一方で、

> **正しい数式構造の回復は単純なG01 basal familyにほぼ限定され、未知構造G07/G08のsymbolic recoveryは0だった。fine-tuningはdomain-IDを改善する一方でdomain-OODを悪化させ、低NMSEとmechanistic equation discoveryが明確に乖離した。**

またPhase 4のablation/intervention rankingには方向の実装問題が確認されたため、

> **「encoder_4が因果的に最重要」という解釈は撤回し、実介入スコアからはdecoder群の方が生成に強く必要と解釈する。**

GPU_RUN2の最大の成果は、単に「Top層FTが速い・精度が良い」と示したことではない。

**Neural Symbolic Regressionにおける層適応、生成安定性、数値近似、構造回復、外挿性が互いに異なる現象であることを、同一の固定GNW benchmark上で分離して観測できたこと**にある。

この結果を踏まえると、次の研究段階では「さらにNMSEを下げる」より、**decoder中心の層機能を正しく再解析し、structure-OOD / novel symbolic recoveryを改善すること**が最も重要である。

---

# 付録A. 本レポートで監査した主要成果物

## 計画・repository

- `GPU_RUN2/plan.md`
- `README.md`
- `AGENTS.md`
- repository current `main`
- actual run source commit `1d919278b61172bec9e09465e7c04e3c46ef0892`

## Root

- `manifest.json`
- `finalize.json`
- `phase*_wall_seconds.txt`
- archive / archive SHA256

## Phase 2

- `nesymres_validation_records.json`
- `nesymres_test_records.json`
- `pysr_validation_records.json`
- `pysr_test_records.json`

## Phase 3

- `probe_scores.json`
- `candidate_layers_main.json`
- `candidate_layers_structure_holdout.json`
- `decoder_lens.json`
- `decoder_lens_summary.json`
- `finetune_corpus_fingerprint.json`

## Phase 4

- `raw_scores.json`
- `contributions.json`
- `ablation_scores.json`
- `intervention_scores.json`
- `rankings.json`
- `seed_snapshots.json`
- `conditions.json`
- `conditions_structure_holdout.json`
- `equation_records.json`

## Phase 5

- `main_test_*_records.json`
- `main_test_*_aggregate.json`
- `structure_holdout_test_*_records.json`
- `structure_holdout_test_*_aggregate.json`
- `reproduction_main_test.json`
- `reproduction_structure_holdout_test.json`
- `true_vs_pred_main_test.json`
- `true_vs_pred_structure_holdout_test.json`
- validation-selected HP files and reused model checkpoints

---

# 付録B. 直接確認した実装

actual run commitで少なくとも以下を確認した。

- `scripts/phases/gpu_run2_phase3_interpret.py`
  - probe candidate selection
  - G07/G08 exclusion for structure selection
  - validation内probe train/eval分離
  - candidate freeze before test

- `scripts/phases/gpu_run2_phase4_contribution.py`
  - IOLE
  - zero-output ablation
  - mean-activation replacement intervention
  - fixed random3生成
  - test未使用
  - structure候補選択でG07/G08未使用

- `scripts/phases/gpu_run2_phase5_selective_ft.py`
  - validationでHP選択
  - testはvalidation checkpointを再利用
  - testで再学習・再選択しない
  - condition別record保存

- `src/evaluation/aggregation.py`
  - failure-aware aggregation
  - primary penalized NMSEがmedian
  - invalid NMSE penalty \(10^6\)

- `src/evaluation/reproduction_bias.py`
  - fine-tuning corpusに対するreproduction判定
  - reproduced / novel / novel recovery集計

- `src/evaluation/gpu_run2_rankings.py`
  - IOLE ranking fallback
  - ablation/intervention ranking方向の問題

- `src/interpretability/interventions.py`
  - zero output
  - mean activation replacement
  - intervention deltaの符号

---

# 付録C. 本レポート独自の再集計

保存済みrecordを変更せず、以下を本レポート作成時に再計算した。

1. noise=0.0 / 0.1を分けたPhase 2 / Phase 5性能
2. family別skeleton / symbolic equivalence
3. seed別failure-aware median NMSE
4. Top 1/Top 3 vs Fullのpaired Student t CI
5. Top 3 vs fixed Random 3のpaired Student t CI
6. noise別IOLE ranking stability
7. ablation/intervention raw effectから見たcorrected importance方向

これらは**post-hocな方法選択には使用せず、すでに固定・実行されたGPU_RUN2の事前判定を評価するための再集計**である。
