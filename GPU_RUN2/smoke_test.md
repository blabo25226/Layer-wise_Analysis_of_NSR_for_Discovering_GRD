GPU_RUN2 Smoke Test 仕様案
目的

Smoke testは研究結果を得るための実験ではなく、RTX 2070実機上でGPU_RUN2の全pipelineが本番設定に近い状態で正常に動作することを確認し、本実行時間を推定するpilot runとする。

主目的は次の4点。

Phase 0〜5のlive pathがすべて動作すること。
CUDA、VRAM、checkpoint、timeout、NeSymReS decode、fine-tuning、DecoderLens、ablation、activation interventionなどが実機で正常に動くこと。
各処理の実時間を測定し、GPU_RUN2本番が約20時間以内になる設定を決めること。
本実行前にOOM、異常に遅い処理、timeout多発、保存schema不整合を発見すること。

Smokeの結果を研究上の性能比較・層ranking・symbolic recoveryの本結果として使用しない。

Smokeで固定する縮小条件
seed / noise

Smokeでは、

data_seed = 101
model_seed = 0
noise = 0.0

の1 seed bundle × 1 noiseのみを使う。

これは速度・動作確認用であり、noise=0.1 やseed 202/303は本実行で扱う。

現在の iter_seed_noise(..., smoke=True) も先頭seed bundleと先頭noiseだけに縮小しているので、この方針と整合しています。

problem数

研究上の代表性を評価するのが目的ではないので少数にする。ただし、可能なら1 familyだけに偏らず、1変数・2変数・3変数の問題が最低1つずつ通るようにする。

目安は、

Phase	Smoke対象
Phase 0	preflightのみ
Phase 1	本番と同じ240 problem catalogue生成でも可。ただし点生成量は必要なら縮小可能
Phase 2	validation 4件 + test 4件
Phase 3	validation 4件
Phase 4	train 8件、評価panel 2件程度
Phase 5	train 8件、validation 4件、decode対象2件程度

現コードではPhase 2が rows[:4]、Phase 3がvalidation先頭4件、Phase 4がtrain 8 / panel 2、Phase 5がtrain 8 / val 4 / eval 2に縮小されています。

ただし、単純な先頭N件ではG01だけに偏る可能性があるなら、固定smoke manifestを作る方がよいです。

例えば、

smoke problems:
G01: 1件
G02/G03: 1件
G04–G06: 1件
G07/G08: 1件

のように、計4件を事前固定する。

これは性能比較のためではなく、異なる式次元・templateのコードpathを通すためです。

Phaseごとの確認内容
Phase 0: preflight

必須確認：

Python 3.10
RTX 2070をCUDA deviceとして認識
CUDA / PyTorch version
GPU名
VRAM total / available
RAM
CPU型番
NeSymReS checkpointの存在とSHA256
config読込
operator policy
30秒timeout mechanism
Windows上のhard timeout
output schema
run directory作成

失敗したらPhase 1以降へ進まない。

特に、

cuda_available = true
device_name contains RTX 2070
timeout_mechanism_present = true
checkpoint exists

をGo条件にする。

Phase 1: GNW synthetic

確認するもの：

G01〜G08の生成
family_id
template_id
240 problem catalogue
main split
structure-holdout split
oracle inputs
analytic target
paired noise設計
domain-ID / domain-OOD点
fingerprint
NPZ保存・再読み込み
finite differenceを通っていないこと

Phase 1はGPU負荷が小さいため、ここは本番と同じ240 problemsを生成してもよいです。

これによってデータ生成コードそのものを本番前に完全確認できます。

Phase 2: baseline

Smokeでも両方通す。

NeSymReS
PySR

確認項目：

checkpoint load
GPU decode
PySR CPU process
operator restriction
30秒timeout
candidate保存
domain-ID NMSE
domain-OOD NMSE
symbolic metrics
process_seconds
search_seconds
failure_reason
checkpoint/resume

ここで特にNeSymReS 1 decodeの時間とPySR 1 searchの時間を測る。

Phase 3: probe / DecoderLens

最低限、

template-ID probe
next-token probe
operator-count probe
CKA
gradient norm
DecoderLens

を1回以上liveで通す。

候補層はencoder / decoderだけで、output_headが入らないことも確認する。

現コードではsmoke時にrepresentation収集batch数も少なくし、DecoderLensも対象を絞っています。

Smokeで得たlayer rankingは本番rankingとして採用しない。

ここは重要です。

smoke candidate_layers != frozen production candidate_layers

と明示しておくと安全です。

Phase 4: contribution

最も重要なlive-path確認の一つです。

最低限、候補層について、

single-layer FT
ablation
activation intervention

が実際に動くことを見る。

また、

pretrained
full FT
single-layer FT

を少なくとも1回ずつ学習する。

記録する時間を分ける。

full_ft_seconds
single_layer_ft_seconds
decode_seconds
ablation_seconds
intervention_seconds

ここでRTX 2070上のFT 1 runの実測時間を得る。

これは本番時間推定に非常に重要です。

Phase 5: selective FT

5条件すべてのコードpathはsmokeで1回通した方がいいです。

frozen
full
top1
top3
random3

ただし各条件2 problems程度で十分。

main / structure-holdoutについても、

main validation
main test
structure validation
structure test

のpathを最低1回通す。

現在runner自体もこれら4つを呼び出しています。

確認対象は、

conditionごとのcheckpoint生成
validationでHP選択
testでHPを変更しない
structure-holdout用checkpoint分離
symbolic recovery記録
reproduction bias集計
true-vs-pred表生成

です。

特に追加してほしい「時間計測」

ここが今回一番重要です。

Smoke終了時に、

results/runs/<run-id>/smoke_timing_summary.json

などを自動生成する。

最低限、

phase0_seconds
phase1_seconds
phase2_seconds
phase3_seconds
phase4_seconds
phase5_seconds
total_seconds

を保存。

さらに処理種別について、

decode count
decode mean
decode p50
decode p90
decode p95
decode max
timeout count
timeout rate


PySR search mean/p95


full FT run count
full FT mean
single-layer FT run count
single-layer FT mean
top3 FT mean

まで残したいです。

本番20時間の予測もSmoke後に自動計算する

これはかなりおすすめです。

本番予定decode数 N に対して、

T
decode
	​

≈N×t
smoke
	​


で予測。

ただし平均だけだと楽観的なので、

expected
N×p50
conservative
N×p90

の両方を出す。

さらにFTについて、

T
FT
	​

=N
full
	​

t
full
	​

+N
single
	​

t
single
	​

+⋯

を加える。

最終的に、

estimated_full_runtime_hours_p50
estimated_full_runtime_hours_p90

をsmoke summaryへ出す。

目標は20時間程度。

Smoke後の判定

Smokeが成功しただけで即本番にはせず、計算時間も見る。

GO
OOMなし
Phase 0〜5完走
checkpoint/resume正常
NaN/Infが異常多発しない
timeout機構正常
decode p95が十分短い
本番p90推定がおおむね20時間前後、または許容範囲
全必須artifact生成
REVISE

例えば、

estimated runtime > 25–30 h

なら本実行前に、

timeout 30→20秒
Phase 3/4 problem削減
Phase 5条件整理
structure-OOD noise=0.1をExtendedへ
不要なdecode重複の再利用

などを検討する。

NO-GO
OOM
checkpoint不整合
test leakage
timeoutが機能しない
Phase 4/5 live FT失敗
decode timeoutが大量発生
保存結果が欠損
Smokeの時間目標

Smoke自体は、

目標15〜30分、許容上限60分程度

にしたいです。

60分を大幅に超えるなら、それ自体が本番20時間目標に対する警告です。

ただしsmokeを速くするために、

precisionを本番と変える
beam sizeを変える
timeoutをsmokeだけ短くする
FT algorithmを別物にする

のは避けます。

縮小するのはproblem / seed / noise / batch数であって、主要algorithm設定は本番と同じにするのが大事です。

AIへの指示

最新の GPU_RUN2/plan.md と現在のGPU_RUN2実装を正本として確認してください。既存の --smoke 実装を捨てずに拡張し、GPU_RUN2 smoke testを「Phase 0〜5のlive path確認 + 本実行時間推定pilot」として明文化・実装してください。

Smokeは研究結果として使用せず、data seed 101 / model seed 0 / noise 0.0 の1 bundleを基本とし、各Phaseで少数の固定problemのみ使用してください。ただし、可能なら1・2・3変数および異なるGNW templateを通る固定smoke problem集合にしてください。単純な先頭N件でfamilyが偏る場合はsmoke manifestを作ってください。

Phase 0〜5でCUDA、checkpoint、timeout、GNW生成、NeSymReS/PySR、template/next-token/operator-count probe、CKA、DecoderLens、single-layer FT、full FT、ablation、activation intervention、frozen/full/top1/top3/random3、main/structure-holdoutのlive pathを最低1回は通してください。

Smokeでは本番と同じ主要algorithm設定、operator policy、precision、beam、timeoutを使用し、縮小対象はproblem数・seed数・noise数・probe batch数としてください。Smokeで得たlayer rankingや性能値を本番結果として使用しないでください。

各Phaseおよび各decode/search/FTについて実時間を記録し、smoke_timing_summary.json を生成してください。最低限 total/phase別seconds、decode mean/p50/p90/p95/max、timeout率、PySR時間、full FT時間、single-layer FT時間を保存してください。

さらに現在のplanにある本番予定decode数・学習run数を用いて、本番実行時間のp50推定とp90保守推定を自動計算し、hoursで保存してください。GPU_RUN2本番の目標実時間は約20時間です。

Smokeの目標実行時間は15〜30分、許容上限は約60分とします。60分を大きく超える場合や本番p90予測が25〜30時間を超える場合は、勝手に本番条件を変更せず、どのPhase/処理が律速かを報告してください。

plan.md にSmoke Test節を追加し、目的、非研究結果であること、縮小条件、Phase別確認内容、保存するtiming metrics、Go/Revise/No-Go基準、本番20時間目標を記載してください。

実装後は python -m pytest -q GPU_RUN2/tests を実行し、既存テストを壊さないでください。必要なsmoke timing用テストを追加してください。変更ファイル一覧、テスト結果、smokeで実際に実行されるproblem/seed/noise/condition数、本番時間推定式を最後に報告してください。