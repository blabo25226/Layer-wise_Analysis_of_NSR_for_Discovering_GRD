# GPU_RUN2 計画

作成日: 2026-07-29

GPU_RUN1結果反映: 2026-07-30

方針改訂: 2026-08-12

## 1. 目的と範囲

GPU_RUN2では、GPU_RUN1で判明した計算量、CPU律速、設定の途中変更、symbolic recoveryが0だった問題を踏まえ、
**合成データだけ**を用いてNeSymReSの層解析と数式構造回復を検証する。

目的は次の3点である。

1. encoder・decoder各層の役割をprobe、DecoderLens、fine-tuning、ablation、表現類似度、activation介入から調べる。
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
| `decoder_2`〜`decoder_4`の寄与が高かった | 独立runのprobeとDecoderLensで再確認し、testを見る前に候補を固定する |
| Top 1〜3は全層FTとNMSE同等性margin内で同等だった | 独立runで再現性、symbolic recovery、計算資源削減を確認する |
| Top 3対random 3の差は未確定だった | 事前生成した複数のrandom層集合とpaired比較する |
| symbolic recoveryは全条件で0だった | 真式対予測式の比較を主成果物にし、失敗理由まで保存する |
| TPSRの追加改善に大きな計算時間を要した | profilerとGo/No-Goを通った場合だけ副次比較する |
| DREAM4の経験的selector F1が低かった | GPU_RUN2では変数選択問題を切り離し、oracle変数だけを入力する |
| `tan`と危険な除算を含む式が多かった | 合成データの真式と整合するoperator allowlist、安全性検査を使う |

### 1.2 事前に固定する主判定

1. **層の役割と再現性**：probe、DecoderLens、単一層fine-tuning、ablation、表現類似度、
   activation介入が示す重要層と機能を比較する。相関的な結果と介入結果を区別する。
2. **全層同等性**：Top 1〜3と全層FTのfailure-penalized NMSE差について、95% Studentのt区間全体が
   事前margin `[-0.05, 0.05]`へ入るかを判定する。
3. **rankingの付加価値**：Top条件と事前生成したrandom層集合平均のpaired NMSE差を報告する。
   95% t区間が0をまたぐ場合、優越性または同等性を主張しない。
4. **構造回復**：exact、skeleton、symbolic equivalence、complexityを条件別に報告する。
   NMSEが小さくても構造回復が失敗した場合は、数式回復成功と判定しない。
5. **noise頑健性**：`noise=0.0`と`noise=0.1`を独立条件として比較し、結果を混ぜて集計しない。

seed数、random集合数、学習budget、decode budgetはvalidation pilot後かつtest評価前に固定する。

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

### 3.2 正しい式を持つ基準problem

次をGPU_RUN2 synthetic benchmark v1の基準式とする。$`x_1`$は対象変数、$`x_2,x_3`$は
oracle regulatorである。モデルへ渡す変数は「oracle入力」列だけとし、不要変数を追加しない。

| eq_id | motif | oracle入力 | 正しい式 $`f(\mathbf{x})`$ |
|---|---|---|---|
| `S01` | 自己減衰 | $`x_1`$ | $`-0.7x_1`$ |
| `S02` | 線形活性化＋減衰 | $`x_1,x_2`$ | $`1.2x_2-0.7x_1`$ |
| `S03` | 線形抑制＋減衰 | $`x_1,x_2`$ | $`1.4-0.9x_2-0.6x_1`$ |
| `S04` | Hill活性化＋減衰 | $`x_1,x_2`$ | $`2.0x_2^2/(0.5^2+x_2^2)-0.8x_1`$ |
| `S05` | Hill抑制＋減衰 | $`x_1,x_2`$ | $`1.5\,0.7^2/(0.7^2+x_2^2)-0.6x_1`$ |
| `S06` | 2因子加算制御 | $`x_1,x_2,x_3`$ | $`1.1x_2/(0.4+x_2)+0.8x_3-0.5x_1`$ |
| `S07` | 2因子積制御 | $`x_1,x_2,x_3`$ | $`1.3x_2x_3-0.6x_1`$ |
| `S08` | 活性化・抑制混合 | $`x_1,x_2,x_3`$ | $`1.8x_2^2/(0.6^2+x_2^2)+1.0\,0.8^2/(0.8^2+x_3^2)-0.7x_1`$ |

この表は、実装時に式文字列、canonical SymPy式、使用変数、operator集合、係数を機械可読な設定ファイルへ
一度だけ定義する。文書と実装に式を重複して手入力したままにせず、テストで表との一致を確認する。

8式だけでは統計的検出力が不足するため、各motifについて30個、合計240個の係数variantを生成する。
各非ゼロ係数は表の基準値の`[0.8, 1.2]`倍から一様分布で生成し、符号と式構造は維持する。
variant生成seedは`20260812`とし、motifごとに18 problemsをtrain、6 problemsをvalidation、
6 problemsをtestへ割り当てる。割り当ては同じseedから一度だけ生成し、`eq_id`、split、全係数、展開前の真式、
canonical真式をmanifestへ明示する。同一variantまたはその入力行を複数splitへ入れない。

このsplitは同じmotif内の係数一般化を測る設計であり、未知の式構造への一般化を測るものではない。
式構造そのものをholdoutする評価はGPU_RUN2の主集計へ後付けせず、別設定として事前計画した場合だけ副次的に行う。
基準式8個は可読性と実装検証のgolden problemsとして必ず全て保存し、探索結果の都合で削除しない。

### 3.3 operator allowlist

基準式を表現できる次の演算子だけを主実行で許可する。

- `+`
- `-`
- `*`
- `/`
- `square`

`sin`、`cos`、`tan`、逆三角関数、任意実数べき乗、`exp`、`log`は主実行から除外する。
除算候補は分母の最小絶対値、ID/OOD grid上の有限性を検査する。許可外operatorを含む候補や
特異点を持つ候補は成功扱いにせず、理由付きfailureとして保存する。

## 4. 層解析

### 4.1 probing

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

DecoderLensを追加し、decoderの各中間層表現から最終出力headを通して、token候補と式候補がどのように
変化するかを観察する。最低限、problem・layer・decode stepごとに次を保存する。

- top-k tokenと確率またはlogit
- ground-truth tokenの順位
- その層までの暫定token列とparse可否
- 完成可能な場合のraw equationとsimplified equation
- 正しい式とのtoken、skeleton、symbolic equivalenceの差
- noise条件、seed、checkpoint、oracle変数対応

DecoderLensは原則として観察的解析であり、層の因果的役割はablationやactivation介入の結果と分けて解釈する。
最終出力headを中間層へ直接適用することによる分布ずれを限界として明記する。

### 4.3 CTC_NSRの参照

CTC_NSRは、層解析またはsymbolic recovery設計を検討する際の参照候補に加える。
現時点では採用する構成要素、比較条件、実装範囲が未確定であるため、GPU_RUN2の必須ベースラインにはしない。
本実行前に原典と利用可能な実装を確認し、採用する場合は次を計画へ追記してからsource commitを固定する。

- 参照する論文・実装・version
- 借用する考え方または比較対象
- NeSymReS、TPSR、PySRとのbudget対応
- operator、入力変数、データsplit、評価指標の差

未確定のまま結果説明へCTC_NSRとの性能比較や優劣を記載しない。

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
| `S01` | TBD | 0.0 | $`-0.7x_1`$ | TBD | TBD | TBD | TBD | TBD | TBD | TBD |

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

- 第3節の基準式とvariant設定を機械可読ファイルへ定義する。
- `noise=0.0`と`noise=0.1`をpaired生成する。
- oracle変数だけを入力へ含める。
- motif・式構造・problem単位splitとdata fingerprintを保存する。
- 真式、canonical式、入力範囲、clean/noisy targetを保存し、有限差分を呼び出していないことをテストする。

### Phase 2: baseline

- NeSymReS baselineとPySR baselineを同じproblem、seed、oracle変数、operator集合で実行する。
- 候補評価回数とwall timeを併記する。
- 成功式だけでなく全problem recordを保存する。

### Phase 3: probing / DecoderLens

- validationだけで軽量probingを実行する。
- DecoderLensでlayer・decode stepごとのtoken候補と暫定式を保存する。
- 高価なPhase 4へ渡す候補層と選択規則を凍結する。
- test problemを層選択や可視化対象の選別に使わない。

### Phase 4: contribution

- probeで残った候補層をpaired seedで比較する。
- 単一層fine-tuning、層ablation、固定したactivation介入を比較する。
- probe順位、DecoderLens上の変化、fine-tuning順位、ablation効果、介入効果の一致度をseed別に報告する。
- full FTがbaseを改善しない指標は正規化rankingへ混ぜず、raw scoreを保存する。

### Phase 5: selective fine-tuning / symbolic recovery

- top、random、middle、bottom、full、frozen baselineを公平に比較する。
- random層集合を事前に複数生成し、top対randomのpaired差を検証する。
- early stoppingと選択はvalidationだけで行い、testは条件固定後に一度だけ評価する。
- `noise=0.0`と`noise=0.1`を別々に集計する。
- 真式対予測式の全problem比較表を生成する。

### Phase 6: TPSR / CTC_NSR参照

- TPSRはMCTS、BFGS、Transformer推論を個別にprofileする。
- NeSymReS beamとの候補評価回数またはwall timeを併記する。
- validation subsetで追加NMSE、symbolic recovery、valid rate、complexity、elapsedを確認し、
  費用対効果が低い場合は全規模実行を行わず副次的な結果として残す。
- CTC_NSRは第4.3節の未確定事項が解消した場合だけ、固定した範囲で参照または比較する。

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

Google Colabは使用しない。Google Drive同期、Colab Notebook、compute unitsを前提とする設計もGPU_RUN2から外す。
成果物は`results/runs/<run-id>/`へ保存し、定期checkpointとローカルarchiveで切断・中断へ備える。
RTX 2070のVRAMに収まらない設定は暗黙に条件変更せず、batch size、gradient accumulation、precisionを
validation前に決めてmanifestへ記録する。

| 処理 | 実行場所 |
|---|---|
| NeSymReS fine-tuning / decode | ローカルRTX 2070 |
| probing / DecoderLens | ローカルRTX 2070 |
| TPSR | ローカルPC（GPU/CPU内訳をprofile） |
| PySR | ローカルPCのCPU |
| data生成・集計・図表・archive | ローカルPC |

### 8.2 AIとコーディングの役割

- **Cursor**：実装、局所的な修正、テスト作成、短い反復を基本担当とする。
- **ChatGPT / チャッピー**：研究計画の整理、実験設計、結果の統合的レビュー、主張と限界の確認を基本担当とする。
- **その他のAI**：必要に応じて独立レビュー、統計、文献確認を担当する。担当内容と根拠を引き継ぎへ残す。

役割は責任範囲を明確にするための基本方針であり、生成物は担当AIにかかわらず現在のコード、テスト、保存済み結果で検証する。

## 9. 実装が必要な項目

- [ ] synthetic benchmark v1の機械可読な式定義と生成器
- [ ] analytic targetとnoise 2条件のpaired生成
- [ ] oracle変数だけを渡す入力schema
- [ ] 有限差分コードを通らないことのテスト
- [ ] 全手法共通operator allowlist
- [ ] NeSymReS decode token maskまたは候補filter
- [ ] PySR、TPSRへの同一operator制限
- [ ] 共通60秒decode/search timeout
- [ ] 全Phase共通problem timing schema
- [ ] problem単位checkpoint / resume
- [ ] probing scriptと保存schema
- [ ] DecoderLensのlayer・step別出力と可視化
- [ ] 層別linear probe、表現類似度、ablation、activation介入の固定プロトコル
- [ ] probe・DecoderLens・fine-tuning・ablation・介入順位の一致度集計
- [ ] random層集合反復数と検出力の事前決定
- [ ] 真式対予測式の比較表を生成するreporter
- [ ] exact / skeleton / symbolic equivalenceの検証テスト
- [ ] ID/OOD安全性と除算分母marginの検査
- [ ] TPSR profilerとGo/No-Go
- [ ] CTC_NSRの原典、実装、採用範囲の確定
- [ ] GPU_RUN2用run ID、source commit、環境manifestの固定

## 10. Go / No-Go条件

本実行開始条件:

- synthetic benchmarkの全真式とcanonical式がテスト済みである。
- `noise=0.0`と`noise=0.1`の生成、paired入力、data fingerprintが確認済みである。
- oracle以外の変数がモデル入力へ入らない。
- 有限差分処理がGPU_RUN2 pipelineから呼ばれない。
- operator set、60秒timeout、seed、random集合、budgetが固定済みである。
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
- synthetic benchmark仕様、全真式、canonical式、split、data fingerprint
- noise 2条件のpaired dataと設定
- probing結果
- DecoderLensのlayer・step別token候補、暫定式、図表
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
- PySR結果、Go条件を通った場合のTPSR結果
- CTC_NSRを参照した場合の原典、version、比較条件
- validation report、figures、tables、archive

独立した図表は`graphs/<run-id>/figures/`と`graphs/<run-id>/tables/`へ保存する。
