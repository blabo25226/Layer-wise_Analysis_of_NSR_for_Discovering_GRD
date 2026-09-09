# GPU_RUNclaude1 永続研究状態

## キャンペーン
- branch: `20260909_researce_GPU_RUNclaude1`
- C0001 Stage 0 時点の head commit: `94a571b`（"prepare for claude"）、作業ツリーはクリーン
- status: `C0001 in progress`
- current_cycle: `C0001`
- last_completed_cycle: none
- last_synthesis: none
- 状態の最終再構成: 2026-09-09（C0001 の Stage 0）。チャット記憶ではなくリポジトリのファイルから再構成

## 人間の意図

人間主導の LANSR ラインとは独立に、AI 主導の研究ラインを走らせる。

Claude は次を自律的に反復する:
仮説 → 文献 → 事前登録 → 実装 → 実験 → 分析
→ 独立レビュー → 必要な場合は追試 → サイクルレポート → 反省 → 次の仮説。

人間は主に定期的にレポートを点検する。通常の科学的失敗は停止条件ではない。

---

## 1. 検証済みのモデル同一性（すべての ODEFormer サイクルを制約する）

`assets/odeformer/weights/odeformer.pt`、464,822,385 B、mtime 2023-09-28
- SHA256 `56754040be5aa92ed4767fc43ee2008faa293f87c12b643e66c7df3e1623a5e8`
  （`configs/gpu_run4/base.yaml:11` と `configs/gpu_run5/base.yaml:8` に固定記録。
  `results/runs/gpu_run5_20260823_ddd267b0/phase0/checkpoint_audit.json` で検証済み）
- state dict から読み取った真のアーキテクチャ: **エンコーダ 4 層（次元 256）+ デコーダ 12 層（次元 512）**、
  ヘッド数 16、**パラメータ数 60,646,773**、ランキング対象の 16 層は `encoder_0..3`、`decoder_0..11`。
  ブロックあたり: エンコーダ各 789,760 パラメータ、デコーダ各 3,941,888。
- 論文の 4+16 / 次元 512 / 約 86M の構成では **ない**。86M の重みはローカルに存在せず、これまで一度も
  所在が判明していない。したがって `configs/gpu_run4/base.yaml` は
  `architecture_target: released_checkpoint_4enc_12dec_61M` を固定記録している。
- `tied_output_embedding: true`, `decoder_n_words: 10293`, `encoder_positional_embeddings: false`
- デコード既定値: `beam_size: 50`, `beam_type: sampling`, `beam_temperature: 0.1`,
  `max_generated_output_len: 200`
- **生成の制約（現在のボトルネックの中心）:**
  `operators_to_use: "sin:1,inv:1,pow2:1,id:3,add:3,mul:1"`, `max_dimension: 6`, `max_int: 10`。
  一般の学習可能指数 `pow` は **存在しない**。Hill 指数 4 は `pow2(pow2(x))` と書かねばならない。

その他のチェックポイント: `assets/nesymres/weights/100M.ckpt` 317,003,151 B、SHA256
`62aedc41fdb67ecbe3679f5ef030e7ef2bf0f4471c461b68d8814358968b324f`。
`assets/nd2/weights/checkpoint.pth` 81,136,260 B — **リポジトリのどこにも SHA256 の記録がない**（未解決の欠陥）。

---

## 2. 先行の制約（検証済みの結果で置き換えられるまでは観測事実として扱う）

### GPU_RUN4（`results/runs/gpu_run4_phase0_01`、シード 1、ODEBench 63 システム x 4 破損条件 = 252 セル）
- 有効 232/252 = 0.921、再構成 R2 中央値 0.980、汎化 R2 中央値 0.696
- **正規形での完全一致 0/252、CAS による記号的等価 0/252**。骨格の完全一致 19/252 = 0.075 で、
  容易な 6 システム（RC circuit, population growth, autocatalysis, language death, laser photons, SIR-2D）に限られる
- TED 中央値 16、複雑度中央値 17、変数 F1 中央値 1.0（この指標はここでは識別力を持たない）
- 次元によるスケーリング: 1D は再構成 0.997、骨格 17/92。2D は 0.946、2/112。
  **3D は有効が 25/40 のみ、R2>0.9 が 8/40、骨格 0/40**。4D は 0.906、0/8
- 生成 対 選択: 真値の骨格がビーム内にある割合 23/252 = 9.1%。うち選択が実際にそれを選んだのは 18 件、
  取り逃したのは 5 件。**63 システムのうち 57 システムでは一度もビームに入らなかった。**
  ビームあたりのユニーク骨格数の平均 9.19。選択された候補の平均 TED 17.26 に対し、
  ビーム内最良（オラクル）の平均 TED は 14.31
- 層の推定対象（エンコーダのみのプローブ、n_val = 16）: プローブ上位 3 は `encoder_0/1/2`。
  CKA は全ペアで 0.921-0.978（分離なし）。勾配の上位は `encoder_0/3/2`。
  残差ゼロ化による因果アブレーションの上位は `encoder_3`（dCE 10.40）、`decoder_3`（2.47）、`decoder_0`（1.89）。
  IOLE の上位は `decoder_7`、`encoder_0`、`encoder_2`（差はいずれも約 1e-3 のみ）
- 分析用テストでの選択的ファインチューニング（4 ステップ、teacher-forcing の CE のみ）:
  frozen **1.674 が最良** < causal_top3 1.679 < top1 1.682 < random3_1 1.683 < random3_0 1.690
  < bottom3 1.692 < random3_2 1.693 < top3 1.696 < full **1.797 が最悪**。
  すべての FT 条件が frozen より悪く、検証からテストへの順位が反転した。
- **基準どうしの不一致は大きく、ノイズではない**: プローブ 1 位の `encoder_0` は因果 dCE では 11 位。
  因果 1 位の `encoder_3` はプローブ順位の最下位。上位 3 の並びを共有する基準の組は一つもない。
- 既知の来歴（provenance）欠陥: ルートの `manifest.json` の status が `running` のまま固まっている。commit `0641fa7`。

### GPU_RUN5（`results/runs/gpu_run5_20260823_ddd267b0`、3 バンドル、phase 0-9 完了）
- ODEBench のデコード済みサポート（GPU_RUN4 と同一の単一シード 252 セルの再分析であり、新規推論はしていない）:
  変数を分母に持つ候補 1,860/12,600 = 14.76% [0.1415, 0.1539]。
  **真値の指数を考慮した骨格がビーム内にある割合 4/252 = 1.59% [0.0062, 0.0401]**。
  **変数分母をもつ真値の部分集合（56 セル）: truth-in-beam 0/56、選択候補の完全一致 0/56**
- **GRN の frozen 検証（960 セル、47,987 候補）: `true_exponent_aware_skeleton_in_beam_rate = 0.0`
  — 一度も入らなかった。** ビームあたりのユニーク指数骨格数の平均 9.28。
  => Hill 型 GRN において選択が律速の制約ではあり得ない。**ボトルネックは生成である。**
- 複数初期条件（multi-IC）での選択（P6 は HIT）: 失敗を考慮した汎化 NRMSE のクラスタ平均差
  **-0.20278**、対応のある Student-t の 95% 信頼区間 **[-0.32323, -0.08233]**、80 システムクラスタ。
  既存候補の中での外挿誤差は改善するが、存在しない構造を作り出すことはできない。
- GRN の最終テスト（2026-09-01 に一度だけ開封）: frozen は exact-macro 0.02396 / faTED 0.47917 /
  genNRMSE 1.40764。official_continued_full は 0.05972/0.46147/1.44240。
  **grn_full は 0.15972/0.36865/2.19822（再構成 R2 が 0.222 まで崩壊）**。
  grn_top3 は 0.10938/0.46111/2.29097。grn_random3_0 は 0.10764/0.44223/1.26859
- **R03-R08 のうち自明でない Hill 型 / 変数分母型の成分について、完全一致した成分数は、
  すべての最終条件で 0 である。** exact-macro の 0.15972 を「自明でない GRN の 16% を回復した」と
  読んではならない。
- 忘却（ODEBench の指数考慮 exact 率、副次指標）: frozen 0.08466、grn_top3 0.06085 (-0.0238)、
  grn_full 0.00794 (-0.0767) => 選択的 FT は忘却が少なく、全体 FT は忘却がはるかに大きい
- **P7 は MISS**（辞書式の第一キーで full が top3 を上回った）。**Go 8 は NO-GO**: 6 条件のうち 3 条件が偽で、
  その中には汎化 NRMSE の比 top3/frozen = 1.6275（上限 1.10）が含まれる。
  DREAM4 と実データは意図的に実行していない — 事前登録に基づく停止であり、計算の失敗ではない。
- 層の推定対象（main ビュー、16 層）: デコーダの次トークン予測プローブ上位 3 は `decoder_11` 0.6420、
  `decoder_10` 0.6215、`decoder_9` 0.5975。勾配/sqrt(param) の上位は `encoder_0/3/1`。
  式ベースの IOLE 上位 3 は `decoder_11`、`decoder_10`、`decoder_8`。
  因果的な平均アブレーション（alpha = 0.5）の上位 3 は `decoder_11`、`decoder_3`、`encoder_3`
- **P5 は HIT — 本キャンペーン最強の層に関する結果:** 介入後の dCE 順位と、失敗を考慮した dTED 順位の
  Spearman 相関は **0.008956、両側 p = 0.97374**、n_layers = 16。
  このパネルにおいて、teacher-forcing の CE は記号的損傷の順序の代理指標として使えない。
  `decoder_11` は faTED を +0.52692 悪化させ、component_valid_loss 1.0、汎化 R2 の損失 10.466 を生じたが、
  **damage_CE = -1.61708 — 式が破壊される一方で CE は改善した。**
- 視野に入れておくべき内部矛盾: IOLE 1 位の `decoder_11` は main ビューでの正規化寄与が
  C_l = **-0.0378（負）** であり、一方 `decoder_10` は 0.3298、`decoder_0` は -0.4157 である。
  辞書式の IOLE スコアと C_l は一致していない。
- 3 バンドル間での順位安定性: main は Spearman 0.480 / Kendall 0.389、family-holdout は 0.781 / 0.622
- **DecoderLens は完全に飽和: 変数を考慮した正規化 TED の中央値が 12 デコーダ層すべてで 1.0**
  （式 288 行、トークン 20,352 行、失敗 0）— 深さ方向の信号はまったく回収できなかった
- モジュール内の非対角 CKA の平均: エンコーダ 0.94377（4 層）対 デコーダ 0.57762（12 層）
- 因果介入での `component_exact_loss = 0.0` が 16 層すべてで成立（床効果 — exact はもともと 0 だった）
- 規模: 物理的な失敗イベント 128,007 件、最終 GRN 候補 292,618 件、ODEBench 忘却の候補 182,772 件。
  64,620 個のシャードすべてを phase9 でパス・バイト数・SHA256 によりストリーム検証済み
- family-holdout は main の 80 システムテストの **部分集合**（R07/R08）であり、明示的に独立した証拠では **ない**

### run 間での層ランキングの不一致（Result E）
| run | モデル | プローブ上位3 | 因果上位3 | IOLE上位3 |
|---|---|---|---|---|
| GPU_RUN2 | NeSymReS | decoder_0, decoder_3, encoder_4 | （なし。保存されているアブレーションは頑健性の順序が反転したもの — 既知の欠陥） | decoder_4, decoder_1, decoder_0 |
| GPU_RUN3 | NDformer | dec.1, dec.0, enc.1 | enc.0, enc.1, dec.0 | dec.1, dec.0, enc.1 |
| GPU_RUN4 | ODEFormer | encoder_0, encoder_1, encoder_2 | encoder_3, decoder_3, decoder_0 | decoder_7, encoder_0, encoder_2 |
| GPU_RUN5 | ODEFormer | decoder_11, decoder_10, decoder_9 | decoder_11, decoder_3, encoder_3 | decoder_11, decoder_10, decoder_8 |

**同一チェックポイント** 上で起きた RUN4 -> RUN5 の反転は、推定対象（estimand）の変更であって矛盾ではない。
RUN4 はエンコーダのみを、次元分類を目標として n_val = 16 でプローブした。RUN5 は 500 件の検証用数式に対して
デコーダの次トークン予測を目標とした。ルール 04 はこれらを平均して単一の順位にすることを禁じている。

---

## 3. 未解決の上位研究課題（Stage 0 後に再優先付け）

1. **生成のサポート / 到達可能性** — なぜ真の Hill 骨格は一度もビームに入らないのか？（現在の最優先）
2. (1) の競合する説明としての、表現能力 対 事前確率質量 対 探索予算。
3. 候補選択の識別可能性（GRN については律速の制約では *ない* とほぼ判明。ODEBench では未解決）。
4. 構造的な分布外（OOD）汎化。
5. **層重要度の基準どうしの乖離** — P5 の直交性という結果、および「CE は改善するのに式は壊れる」現象には、
   相関ではなく機構の説明が必要。
6. 適応と忘却のトレードオフ（選択的 FT は忘却が少ないが、式のスコアでは勝てなかった）。
7. 予算を揃えた公平なベースライン評価。
8. 実データへの準備ゲート（Go 8 でブロック中。新しい情報なしにエスカレートしない）。
9. 微分を使わない生物ダイナミクス手法との関係。
10. ND2 チェックポイントに SHA256 の記録がない（来歴の欠陥。修正は安価）。

---

## 4. 封印資源とテストアクセス台帳

| 成果物 | 内容 | 状態 |
|---|---|---|
| `results/runs/gpu_run5_20260823_ddd267b0/phase2/sealed_test.json` | main の GRN テスト、80 システム、SHA256 `881f784b14cafa2d8617679c573be8ed68f63dbab6d7fa9182e4f5b510464ce0` | **消費済み（SPENT）** — 2026-09-01 に一度開封（`open_count: 1`） |
| `.../phase2/sealed_family_holdout_test.json` | 20 システム R07/R08、SHA256 `fa8fe375fd273e807e22d7d0def7c1d0c866ad006081d207359cb97d1bcbaf91` | **消費済み**。かつ 80 システムの *部分集合* — 独立した証拠として数えてはならない |
| `.../phase4/sealed_official_test.json` | 公式 ODEFormer 生成器由来の数式 500 件、成果物 SHA256 `2860d829d9077d01258489fb68ed8dcd8a333d6a0e150b8e36b301f28bb1e070` | **生成済みだが一度も評価されていない** — 下の訂正を参照。「未接触」ではない。 |

**訂正（C0001 Stage 5、2026-09-09）** — phase 4 の封印を「未消費（UNSPENT）— 一度も評価されていない —
利用可能な唯一のクリーンな封印」と以前に述べた記述は不正確であり、撤回する。
検証結果: `scripts/phases/gpu_run5_phase4.py:119` と `:152` が、封印されていない兄弟ファイルと並んで
`sealed_official_test.json` に対して `sha256_file()` を計算している。一度はキャッシュ有効性の確認のため、
もう一度は `official_corpus_meta.json:artifact_sha256` を埋めるためである。つまり、封印がクリーンである
証拠として私が引用したダイジェスト `2860d829...` は、**その封印を生成したフェーズ自身が、いかなる
テスト開封台帳の外側で計算したもの** である。これに対応する台帳の記載は存在しない。

正確で擁護可能な状態は次のとおり:
- その **結果（outcome）は一度も分析されていない**（`test_generated_not_evaluated: true`。また Phase 4 の Go は
  `official_test_outcomes_not_analyzed: true` / `official_test_used_only_for_split_leakage_audit: true` を主張する）。
- その **バイト列は読まれた**。読んだのはハッシュを取るための生成フェーズ自身であり、GPU_RUN5 自身の
  Phase 8 は *他の* 封印についてはこれをテスト開封イベントとして扱っている。
- それが消費に当たるかどうかは **キャンペーンレベルの未解決の問い** であり、私がどちらとも断定すべき
  ことではない。
いずれにせよ C0001 はこれを読まない。

**封印の一覧の訂正**: `results/` 配下の封印ファイルは 3 個ではなく **7** 個ある。追加の四つは、放棄または
部分的に終わった二つの GPU_RUN5 run（`gpu_run5_20260823_8cd0b6fa`、`gpu_run5_20260823_fec3a894`）に属し、
それぞれが自身の `phase2/sealed_test.json` と `phase2/sealed_family_holdout_test.json` を持つ。
権威があるのは `ddd267b0` のみ。許可リストやガードは、ファイルシステムから 7 個すべてを列挙しなければならず、
三経路をハードコードしたリストに依存してはならない:

```
results/runs/gpu_run5_20260823_8cd0b6fa/phase2/sealed_family_holdout_test.json
results/runs/gpu_run5_20260823_8cd0b6fa/phase2/sealed_test.json
results/runs/gpu_run5_20260823_ddd267b0/phase2/sealed_family_holdout_test.json
results/runs/gpu_run5_20260823_ddd267b0/phase2/sealed_test.json
results/runs/gpu_run5_20260823_ddd267b0/phase4/sealed_official_test.json
results/runs/gpu_run5_20260823_fec3a894/phase2/sealed_family_holdout_test.json
results/runs/gpu_run5_20260823_fec3a894/phase2/sealed_test.json
```

上表に続く2件（コードフェンスに分断されていたため表として再掲する）:

| 成果物 | 内容 | 状態 |
|---|---|---|
| `results/runs/gpu_run4_phase0_01/phase4/corpus.json` のテスト分割 | 数式 16 件 | 消費済み（RUN4 phase 9 で一度評価） |
| ODEBench 63 システム | `third_party/odeformer/odeformer/odebench/` | 封印されていないが、適応 / 層選択 / ハイパーパラメータのデータとしての使用は **禁止**。適応後の ODEBench 評価は *忘却* の副次アウトカムとしてのみ扱う。 |

**本キャンペーンへの帰結**: クリーンな確認集合を必要とするサイクルは、**新しい run ID のもとで新しい封印集合を
生成しなければならない**。GPU_RUN5 の GRN 封印を選択や二度目の評価に再利用することは、ルール 01 と 02 に違反する。

テストのファイアウォール機構はすでに存在し、必ず使用しなければならない: `src/gpu_run5/config.py load_sealed_test`
は `phase < 8` のとき `PermissionError` を送出する。`src/gpu_run5/phase8.py` は `fcntl` による単一開封権を取得し、
`phase8/test_open_ledger.json` を書き出す。

---

## 5. 計算資源の状態（2026-09-09、C0001 Stage 0 に測定）

- python 環境: conda `lansr310`、Python 3.10.20。
  有効化は `source /home/blabo/miniconda3/etc/profile.d/conda.sh && conda activate lansr310`
- torch 2.5.1+cu124、CUDA 利用可能。ドライバ 580.173.02、CUDA ランタイム 13.0
- **GPU 0: NVIDIA GeForce RTX 2070、合計 7782 MiB、cc 7.5、アイドル 54 C、うち 888 MiB は既に
  デスクトップセッション（gnome-shell / Xwayland / gnome-remote-desktop）が保持 => 実質約 6.5 GiB 利用可能、
  かつユーザの稼働中デスクトップと共有されている。**
- GPU 1: NVIDIA GeForce GTX 1060 3GB、3006 MiB、cc 6.1、30 C、アイドル。61M パラメータの学習には小さすぎるが、
  順伝播のみの作業には使える。
- RAM 合計 60 GiB、約 52 GiB 利用可能。swap 7 GiB
- ディスク `/dev/nvme0n1p2` 233 G、**117 G 利用可能**（48% 使用）。`results/` はすでに 25 G。
- ライブラリ: sympy 1.13.1、numpy 2.2.6、scipy 1.15.3、hydra-core 1.0.0、omegaconf 2.1.2、pysr 1.5.10、
  scikit-learn 1.7.2、pandas 2.3.3、matplotlib 3.10.9、zss 1.2.0、pytorch-lightning 1.9.5
- `odeformer` は pip インストール **されていない**。`third_party/odeformer` は
  `src/gpu_run4_runtime.py:93 install_odeformer_path` がパス注入し、`:107
  assert_odeformer_not_from_github_source()` で守っている。`nesymres` は `third_party/nesymres` から
  editable で pip インストール済み。

### 恒常的な設計制約
GPU_RUN4/5 は 24 GB の Colab L4 上で走った。本キャンペーンは、デスクトップと共有の GPU で実質約 6.5 GiB の
VRAM しかない。すべてのサイクルはこの枠に収まるか、CPU で走らなければならない。これは設計制約であり、
ハードストップでは **ない**。

### サイクルあたりの計算上限（C0001 以降。事前登録ごとに改訂可）
- GPU 0 上でサイクルあたり GPU 時間 4 時間以下、ピーク VRAM 5.5 GiB 以下
- サイクルあたり CPU コア時間 24 時間以下
- `results/runs/<new-run-id>/` 配下の新規ディスク使用 15 GiB 以下
- クラッシュループ規則: 新しい診断情報を生まない同一の致命的失敗が 3 回連続したら、再実行ではなく停止して
  再評価する（ルール 06）

---

## 6. 再利用可能な成果物（存在を検証済み。GPU をほぼ使わないサイクルを可能にする）

`results/runs/gpu_run5_20260823_ddd267b0/` 配下（合計 15 G）:
- `phase1/candidates_annotated.json`（44 M）— 凍結された構造フラグ付きの ODEBench 候補 12,600 件。
  `phase1/decoded_support.json`
- `phase3/all_candidates.json`（174 M）— GRN 候補 47,987 件。`phase3/cells/`（230 M）。
  `beam_groups.json`、`failure_funnel*.json`、`lambda_selection.json`、`p6_validation.json`
- `phase4/train_features.npz`（229 M）+ `validation_features.npz`（58 M）— 公式数式 2,000 + 500 件に対する
  16 層分の特徴量をキャッシュ済み => **新しいプローブ / CKA の問いはすべて CPU のみで扱える**。
  `probes.json`、`cka.json`、`gradient_norms.json`、`decoder_logit_lens.json`、`teacher_forcing_ce.json`、
  `fixed_grn_validation_panel.json`（24 システムの介入パネル）、`fixed_official_validation_panel.json`
- `phase5/corpus_means.npz` — 平均アブレーション用の 16 層コーパス平均。**alpha = 0.5 は既にキャリブレーション済み**。
  `layer_effects.json`、`causal_ranking.json`、`holdout_*`、`hook_controls.json`、`cell_cache/`（220 M）
- `phase6/` + `phase7/` + `phase8/checkpoints/`（6.9 G）— 適応済みチェックポイント: `grn_full`、
  `grn_decoder_all`、`official_continued_full`、16 層すべての単層 IOLE 差分、
  `grn_top1/top3/random3_0..4`、x 3 バンドル x 2 ビュー。再学習なしで新しい *評価* に再利用可能。
- `phase2/train.json`（240 システム）+ `validation.json`（80）+ `family_holdout_train.json`（150、R01-R05）
  + `family_holdout_validation.json`（10、R06）— R01-R08 の生成器コーパス。RK45 は rtol 1e-8、atol 1e-10、
  システム / パラメータ変種 / 軌道の重複はゼロ（`audit.json`）、フィンガープリント `e5edac34...ba8af`、
  棄却率 0.0148
- `phase9/preregistration_outcome.json` — 記録として正となる機械判定。`result_{a..e}.json`、
  `integrated_results.json`、`failure_analysis.json`、`condition_uncertainty.json`、
  `source_artifact_audit.json`

`results/runs/gpu_run4_phase0_01/` 配下（44 M）:
- `phase1/` — 凍結された記号評価器（`eval.json`、`gold_cases.json`、`odebench_parsed.json`、
  `identity_records.json`）。`phase2/all_candidates.json`（20 M）+ セルごとの JSON 252 件。
  `phase3/beam_groups.json`。`phase4/corpus.json`（48/16/16 のコーパス）

Git 管理されている付随物: `graphs/gpu_run5_20260823_ddd267b0/`（59 M）—
`tables/phase9_failure_events.csv`（128,007 イベント）、`phase9_formula_examples.csv`
（真値 / 生の予測 / 変数対応）、`phase9_condition_metrics.csv`、`phase9_failure_funnel.csv`、
`phase9_cross_run_rankings.csv`、`phase9_preregistration_outcomes.csv`、および SVG 10 枚。

既存の `results/runs/*` ディレクトリ 29 個はいずれも **上書きしてはならない**（ルール 05）。新しい run ID を使う。

---

## 7. 再利用可能なコード（再実装しないこと）

- **指標**: `src/evaluation/equation_metrics.py` — `nmse:97`、`nmse_vs_variance:105`、`r2_score:113`、
  `variable_recovery:125`、`complexity:141`、`to_skeleton:153`、`symbolic_recovery:169`
  （exact/skeleton/equiv）、`expression_safety:250`（特異点 / 外挿）、
  `score_prediction:295`、`failure_penalized_nmse:358`、`score_domain_predictions:364`。
  SymPy を通る経路はすべて実時間で監視されている（`_timed_simplify:56`、`_timed_equals:62`）。
- **構造距離**: `src/gpu_run4/ted.py:313 system_ted`（インデックス整合、ODE システム用）、
  `src/gpu_run3/ted.py:249 ted_metrics`（prefix、変数考慮）。`zss==1.2.0` に依存。
- **`valid_rate` を用いた失敗考慮の集約**: `src/evaluation/aggregation.py:19` —
  素の `nmse`/`r2` エイリアスは、生存者バイアスを防ぐため意図的に *ペナルティ付き* の値を指している。
- **信頼区間 / 対応のあるシード統計**: `src/gpu_run4/aggregation.py:22 student_t_ci`、
  `src/evaluation/generalization.py:55 aggregate_lodo`、
  `src/evaluation/layer_contribution.py:120 rank_correlations` / `:150 ranking_stability`、
  `src/gpu_run5/training.py:803 pairwise_rank_stability`、
  `src/gpu_run5/interventions.py:269 paired_layer_effects` / `:328 p5_damage_spearman`
- **SR レコードのスキーマ（ルール 03 を満たす）**: `src/gpu_run4/records.py:7 GPU_RUN4_REQUIRED_FIELDS`
  （30 フィールド。生成と選択を分離するための `candidate_index` と `selected` を含み、
  `FAILURE_REASONS` は 22 項目の列挙）、`:76 make_formula_record`。
  `src/evaluation/equation_records.py:64 make_equation_record`
- **凍結された構造分類器**: `src/evaluation/gpu_run5_structure.py:206 classify_formula` —
  `hill_form`、`modulated_hill_form`、`variable_denominator_form`、多項式次数、シグモイド、
  指数考慮の骨格。**これが「真の骨格がビーム内にある」の定義として記録上正となるものである。**
- **凍結された選択キー**: `src/evaluation/gpu_run5_selection.py:11 formula_selection_key`
- **再現バイアス（CTC_NSR）**: `src/evaluation/reproduction_bias.py:140 classify_reproduction`
- **分割**: `src/data/splits.py`（粒度 5 種: グループ、モチーフ/ファミリ、固定の問題変種、
  凍結構造ホールドアウト G01-G08、`assert_problem_splits_disjoint:83`）。
  軌道レベルは `src/data/dream4.py:153`、パラメータ化システムレベルは `src/gpu_run5/grn.py:223`
- **層分析。契約上の六つの推定対象すべて、モデルごと** — ODEFormer スタック:
  プローブ `src/gpu_run5/observational.py:124/:266`、CKA `:314`、勾配 `:328`、
  DecoderLens `:365`/`:427`。因果フックは `src/gpu_run4/hooks.py:23/:47/:62/:87` と
  `src/gpu_run5/interventions.py:39/:88/:129/:222/:382`。IOLE は `src/gpu_run4/training.py:23/:58`、
  `src/gpu_run5/training.py:260`、`src/gpu_run5/phase7.py`。選択的 FT は `src/gpu_run5/phase8.py`、
  `src/gpu_run5/training.py:707 deterministic_random_layer_sets`
- **ODEFormer の数式処理**: `src/gpu_run4/formulas.py`（721 行。構文解析 / 具体化 /
  正規化 / 比較、`:528 instantiate_odebench_item`）。アーキテクチャ監査は
  `src/gpu_run4/architecture.py:238`、`:89 ranking_layer_names`、`:391 set_trainable_layers`
- **来歴（provenance）**: `scripts/ops/run_manifest.py`（`start|finish|stage|resume`。git の commit/branch、
  `pip freeze`、GPU + ドライバ、チェックポイント SHA256、データツリーの再帰的フィンガープリントを記録。
  `--strict` の resume は commit 不一致 / 作業ツリー汚れ / `LANSR_*` パラメータ変更で拒否する）。
  `scripts/ops/validate_gpu_run.py`、`scripts/ops/export_run_summary.py`
- **フェーズ骨組みのテンプレート**: `src/gpu_run4/cli.py`（`common_parser`、`phase_budget`、
  `write_phase_manifest`、`require_previous`、`dummy_phase_output`）。`src/gpu_run5/config.py`
  （`load_config`、`run_dir`、`phase_dir`、`write_manifest`、`budget`、`require_artifact`、
  `load_sealed_test` ファイアウォール、`sanitize_nonfinite`）

`third_party/` の同梱パッケージ四つはすべて `lansr310` 下で問題なく import できる:
`nesymres`（pip editable）、`odeformer`（パス注入）、`nd2`（パッケージディレクトリ `ND2/`）、`tpsr`
（フラット構成: `symbolicregression`、`dyna_gym`）。`GitHubSourceCode/` は参照専用であり、
実行時依存にしてはならない。

---

## 8. 既知の欠陥と安価な修正（リポジトリレベルの安全な変更の候補）

1. ~~**`pytest.ini` が `GPU_RUN5/tests` を含んでいない。**~~ **修正済み（C0001）**: `GPU_RUN5/tests` を
   `testpaths` に追加し、`pythonpath = .` も追加した。既定スイートは現在 **301 passed, 1 skipped**
   （skip は任意の DREAM4 アーカイブ）であり、以前の 178 collected から増えた。したがって、封印テストの
   ファイアウォールを含む GPU_RUN5 の 124 テストが既定で実行される。
   監査の関連主張についての注記: `ModuleNotFoundError: No module named 'scripts'` は **再現しなかった** —
   `GPU_RUN5/tests` は素の状態で 124 を収集し 124 が通った。`GPU_RUN5/tests/conftest.py` が
   `sys.path` に `src/` を挿入するためである。ただしリポジトリのルートは挿入しておらず、それが潜在的な
   脆さである。そこで、観測された失敗の修正としてではなく、その前提を明示するために防御的に
   `pythonpath = .` を追加した。
2. ~~`assets/nd2/weights/checkpoint.pth` はどこにも SHA256 の記録がない。~~ **修正済み（C0001）**:
   `assets/nd2/README.md` に `619d419b449a309c97d5b9ab6b8c9f53c91b45a409a3a9bf5b6ac79cb4f625d4`
   （81,136,260 B）として記録した。これはディスク上の成果物の同一性の記録であり、上流で公表された
   チェックサムとの照合ではない。
3. `GPU_RUN5/README.md` と `GPU_RUN5_summary_report.md` §9.1 が、存在しない六つのレポートファイル名へ
   リンクしている（`GPU_RUN5_experiment_summary_report.md`、`..._decoded_support_report.md`、
   `..._grn_benchmark_report.md`、`..._grn_adaptation_report.md`、`..._layer_analysis_report.md`、
   `..._cross_model_synthesis.md`）。実在するのは `GPU_RUN5_summary_report.md` と
   `GPU_RUN5_{A,B,C,D,E}_*.md` である。
4. `results/runs/gpu_run4_phase0_01/manifest.json` の status が `running` のまま固まっている。commit `0641fa7`。
5. **`data/` ディレクトリが存在しない**（gitignore され、実体もない）。DREAM4 は
   `GitHubSourceCode/dynGENIE3/data/dream4/`（224 M、size-10 x5 + size-100 x5 + 正解データ）にあり、
   GSE112372 は `GitHubSourceCode/dynGENIE3/data/human/gse112372_lps/` にある。`GitHubSourceCode/` を
   実行時依存にしてはならないため、いずれを使う場合も先に `third_party/`/`assets/` へ **コピー** する必要がある。
   `src/data/dream4.py:16 DREAM4_ROOT_CANDIDATES = (Path("data/dream4"),)` は現在
   `FileNotFoundError` を送出する。存在するのは Windows 用のリンク補助スクリプトのみ（`scripts/ops/setup_phase0_links.ps1`）。

これらはいずれもハードストップではない。項目 1、2、4 はサイクル内で安全に修正できる。

6. ~~`pytest GPU_RUN5/tests` は `PYTHONPATH=.` なしでは収集に失敗する~~ **再現せず、かつ現在は無意味（moot）。**
   監査は 6 ファイルが `ModuleNotFoundError: No module named 'scripts'` を送出すると報告した。これは
   再現しなかった。`GPU_RUN5/tests` は素の状態で 124 を収集し 124 が通った。
   `GPU_RUN5/tests/conftest.py` が `sys.path` に `src/` を挿入するためである。リポジトリのルートは挿入して
   いないのが実際の潜在的な脆さであり、そのため欠陥 1 の修正で防御的に `pythonpath = .` を追加した。
   いずれも現在 `pytest.ini` に入っており、既定スイートは 301 passed / 1 skipped である。
7. **`scripts/ops/run_manifest.py:28 tree_sha256` は `--data-path` 配下の全ファイルを `rglob("*")` で
   バイト読みする。** これを GPU_RUN5 の run ディレクトリに向けると、その run ディレクトリ内の封印テスト
   成果物すべてを開くことになる（§4 のとおり `results/` 配下の封印は計 7 個で、`ddd267b0` には 3 個ある）。
   phase-4 封印については §4 の訂正のとおり「未消費」とは言えず、*結果は未解析* だが *バイトは既読* である。
   いずれにせよ C0001 はどの封印も読まない。GPU_RUN5 自身の phase 8 は、封印されたバイト列の
   ハッシュ計算をテスト開封イベントとして扱う。C0001 の manifest 呼び出しは、run のルートではなく、明示的に
   絞ったパスのリストを渡さなければならない。（C0001 Stage 3 の再現性監査で発見。リーク関連。）
8. **`src/gpu_run4/formulas.py` の CAS 等価判定には、静かに失敗する面がある。**
   `SYMPY_MAX_NODES = 40` は真値と候補を *合わせた* ノード予算であり、`formulas.py:434` は超過時に
   `0.0, None` を返す — 失敗理由は記録されない。GRN の真値がそれ *自身* と等しいかを問うと、
   CAS 経路は 52/80 システムで「否」と答える（R05-R08 は各 0/10）。実在するペア 3,000 件超では 55.1% が
   上限を超える（R06/R07/R08 は 100%）。この経路にある素の `except Exception` も同様に、ラベルのない
   非一致を返す。これは *回復スコアに対しては保守的* だが、**null 型の主張に対しては反保守的** であり、
   単調性チェックや失敗予算チェックでは検出できない。誤って空になった結果も単調性とは整合するからである。
   CAS に基づく null を報告する前に、修正するか明示的に上限を設けなければならない。（C0001 Stage 3 の
   再現性監査で発見。）

- **`partA_endpoints.json` の `verdict` フィールドは、v2.1 §7.5 item 3 の override を適用していない。**
  `endpoints.py:142` は二方向感度分析を計算し `sensitivity_agrees` を書くが、`verdict` フィールドには
  非敵対方向の ladder rung をそのまま書く。v2.1 は「二方向が異なる rung に落ちたら verdict は
  `undecidable`」と事前に定めているため、`sensitivity_agrees == False` のとき成果物の `verdict` は
  **契約上の記録すべき verdict と一致しない**。`manifest.json` の `go_conditions` にも感度の項目がない。
  さらに `sensitivity_verdict_non_match_direction` と `sensitivity_verdict_match_direction` の
  2 フィールドは `PrimaryEndpointResult` に存在するが **成果物に永続化されていない**ため、
  どの rung に落ちたかを成果物だけからは復元できない（`cell_cache` からの再計算が必要だった）。
  修正: 両方向の rung を永続化し、`sensitivity_agrees == False` のとき verdict を
  `undecidable (two-sided sensitivity disagreement)` として書く。**凍結契約側は一切変更しない。**
  （C0001 Stage 8 で発見。この欠陥は結果を変えない — 契約が優先し、supervisor が override を適用する。）

---

## 8b. サイクルの経験から採用した常設キャンペーン規則

**R1（2026-09-09、C0001、supervisor の撤回を受けて採用）。**
先行 run の再測定を新しい結果として報告する前に、
(a) 比較の両側が **同じ導出経路** から来ていることを検証する — prefix 由来の文字列を infix 由来の文字列と
比較してはならず、ある演算子の有無を、正規化済み文字列の中でその表層トークンを検索して判定してもならない。
(b) その量そのものを **元 run の保存済み成果物に対して grep** してから、測定したと主張する。
すでに公表されている数値の再導出は *ポジティブコントロール* であって発見ではなく、そのように位置づけて
実行しラベル付けすべきである。
出典: `GPU_RUNclaude1/analyses/C0001_RETRACTION_neg_finding.md`。C0001 Stage 1 で、まさにこの形の誤りが
二件発生した（`pow2` の表層トークン検索、および prefix 対 infix の骨格比較）。

**R2（2026-09-09、C0001、v2 監査のコントロール群に関する所見から採用）。**
コントロールは、それが走る母集団が、そのコントロールが仮定する性質を実際に持つと *検証* されるまでは、
適切に定義されていない。具体的には、ポジティブコントロールの書き換えは関数を **保存する** ことを検証し、
ネガティブコントロールの改変は関数を **変える** ことを検証し、すべての閾値は仮定した母集団サイズに対する
絶対数ではなく、**実現した適格集合** に対する比率で表現しなければならない。
コントロールが `not_measurable` かつ非ゲートとなる、適格集合サイズの下限を凍結しておく。
出典: V2-CRIT-1（実際には 0 と測定される母集団に対して 76/80 のゲートを設けていた件）と
V2-CRIT-2（ネガティブコントロール 60 件のうち 10 件が可換な no-op であり、一致するのが正しかった件）は、
いずれもまったくこの形をしていた。
これと同時に採用した系（corollary）: コントロール群は高価なエンドポイント計算の **前** に走らせる。そうすれば
ハードアボートの代償は予算全体ではなくコントロール群だけで済む。

**R3（2026-09-09、C0001）。**
封印された、あるいは他の形で制限された成果物が未接触であると主張する前に、記録されたダイジェストが
どのように生成されたかを検証すること。run のメタデータに存在するハッシュは、生成フェーズ自身が
アクセス台帳の外側で計算したものである場合があり、その場合「一度も評価されていない」は真でも
「一度も接触していない」は偽である。出典: 上の §4 における phase 4 の封印の訂正。


---

**R4（2026-09-09、C0001、PC2b の不一致から採用）。**
コントロールの還元レベルは、そのエンドポイントの還元レベルと一致していなければならない。*システム* を
採点しながら *成分* を数えると、手を触れていない成分が自分自身と一致し、誤った分母に対して自明な一致数を
報告することで結果が膨らむ。各コントロールの単位を明示し、書き換えや改変がシステムの一部にしか発火しない
場合は、**発火した部分のみ** を比較すること。
系: コントロールと報告されるエンドポイントの両方が使う書き換えは、インスタンスごとに恒等式であることを
検証しなければならない。恒等式でない書き換えは両方を汚染するからである。
出典: `GPU_RUNclaude1/analyses/C0001_pc2b_discrepancy_resolution.md`。

**R6（2026-09-09、C0001、supervisor が実行中の Phase 1 を停止させた事故から採用）。**
実行中の実験を守るための運用規則。
(a) 長時間実行を subagent の Bash 呼び出しから起動しない。そのエージェントを `TaskStop` すると
プロセスグループごと実行も死ぬ。harness 管理下の `run_in_background` を使えば孤児にならず完了通知も届く。
(b) `pgrep -f <pattern>` を生存確認に使うとき、パターンが監視側自身のコマンドラインに現れないように
する。自己マッチは恒久的な偽陽性になる。PID を保持して `kill -0` するか、自分の PID を除外する。
(c) 進捗監視は無変化のときも通知できなければならない。ストールと正常実行を沈黙で区別できない設計は
監視ではない。
(d) プロセスを停止する前に、それが何を子に持つかを確認する。
経緯: `GPU_RUNclaude1/analyses/C0001_precondition_verification.md` のインシデント記録。
科学的被害はなかった（Part A は resume 可能で、破棄されたのは約 7 分ぶんの計算のみ）が、
私は 51 分間、死んだ実験を「順調」と報告し続けた。

**R5（2026-09-09、C0001、一サイクル内で supervisor の偽陰性が三件起きたことを受けて採用）。**
答えが既知の事例で検証されていない比較手法から、**負の（negative）** 結果を主張してはならない。
まず器具を検証すること。しかも、その負の結果を生じさせる方向で検証する。
具体的に記号処理については、`Float` 係数を持つ式に対する `sympy.simplify(a - b) == 0` から非等価を
結論してはならない — `simplify` は Float を確実に打ち消さず、差がちょうどゼロの場合でも棄却する。
厳密な有理数演算（`nsimplify(..., rational=True)`）に加えて複数点での数値プローブを用い、両手法が食い違う
場合はその不一致を報告する。
出典: サイクル C0001 内で起きた同じ系統の supervisor の誤り三件。いずれも未検証の比較手法から **偽陰性** を
生んだ。(i) 正規化済み文字列の中で表層トークン `pow2` を検索し、Hill-4 が存在しないと結論した。
(ii) prefix 由来の骨格を infix 由来の候補と差分し、0/2040 というベースラインを結論した。
(iii) 素朴な Float の `simplify` 等価判定により、60 件の書き換えのうち 5 件は恒等式でないと結論した。
三件はいずれも他のエージェントによって捕捉された。
**この規則が本キャンペーンで決定的に重要な理由**: C0001 の主エンドポイントは null 型であり、偽陰性はまさに
見かけだけの null を製造する誤りである。この supervisor が実証した誤りの方向と、本サイクルの主仮説は
同じ向きを指しており、これは C0001 レポートで妥当性への脅威として開示しなければならない。

**R7（2026-09-09、C0001、Gate B→C 違反を受けて採用）。**
事前登録された gate を実装するときは、**要約ではなく契約の原文を引用して**実装し、
条文と実装を 1 対 1 で対応付けたコメントを残す。要約は条件を落とす。
本件で supervisor は Gate B→C を自身の要約メモから実装し、原文第一文
（「Part A is not `undecidable`」）を落として Part C を違反実行させた。
併せて、**gate が参照する派生フィールドが別の欠陥の影響下にないことを確認する** —
そのフィールドを生成するコードが契約どおりかを検証しない gate は、正しく実装しても通過しうる。
詳細: `analyses/C0001_DEVIATION_gate_b_to_c_violation.md`

## 9. ハードストップの状態

C0001 Stage 0 時点で、発動中のハードストップ条件はない。
branch は正しい。作業ツリーはクリーン。破壊的操作は不要。機密データに遭遇していない。
新しい資格情報や有料アクセスは不要。テストのリークは予防可能（ファイアウォールのコードが存在し、消費済みの
封印は文書化済み）。計算上限は超えていない。GPU / ストレージの状態は健全（54 C、117 G 空き）。
上書きが必要な既存結果はない（新しい run ID を使う）。ライセンス / 倫理上の未解決問題はない。
クラッシュループもない。

## 人間レビュー待ちキュー
`human_review_queue.md` を参照 — 現在は空。

## 再開ポイント（常に正確に保つ — `.claude/rules/12-session-continuity.md` を参照）

- **サイクル**: `C0001`
- **ステージ**: **Stage 8（解析）実行中。** Stage 7 の Phase 1（Part A）は完走。Phase 2（Part B）実行中。
- **拘束力を持つ契約**: `GPU_RUNclaude1/plans/C0001_preregistration_v2.1.md`（および `.json`）。
  v1・v2 は失効。履歴として保存。
- **run id**: `gpu_runclaude1_c0001_b731cdd`、commit `8ff622defc227b4598e0094fc000b8227c4ffdad`

### Phase 1（Part A）実現値 — 完走、`EXIT_CODE:0`、960/960 セル、セル失敗 0 件

Gate A→B は 9 項目すべて通過。項目 (i) の凍結値を `cell_cache` から独立に再計算して一致を確認した。

| 量 | 実現値 | 凍結された期待値 |
|---|---|---|
| 採点済み候補 | 47,987 | 47,987 |
| 成分比較 | 101,963 | 101,963 |
| system 水準 M0 一致 | 0 / 960 セル | 0 / 960 |
| 成分水準 M0 一致 | 2,235 | 2,235（P0c） |
| 家系別 M0 一致 | R04 1,736 / R07 330 / R08 169 | — |

三つのマッチャを**入れ子のカスケードではなく三つの集合**として（v2.1 の要求どおり）:

| 分解 | system 水準 | 成分水準 | ANY 還元後の成分 |
|---|---|---|---|
| M0 一致 | 0 | 2,235 | 13 / 170 |
| M1 一致 | 0 | **0** | — |
| M3 一致 | 0 | 2,235 | 13 / 170 |
| M3 のみ（M0 は不一致） | 0 | 0 | **0** |
| どちらも不一致 | 960 | 99,728 | 157 / 170 |

- **主エンドポイント**: `n_h = 130`、`k_gains = 0`、`ladder_cutpoint = 3`、
  ladder rung は `no_gain_observed_bound_only`
- `wilson_95 = [0.0, 0.028701561634224194]`、cluster bootstrap は点推定 0.0 / CI `[0.0, 0.0]`
  （10,000 resample、seed 20260909）。**退化しているため**、記録上の限界は
  `family_level_wilson_8_cluster` に置換され `bound_of_record = [0.0, 0.3244075683414076]`
- `could_not_evaluate_rate = 0.00011540976879576318`（78,000 超のトリプル中 9 件）
- **二次**: `m3_level_h = 0.0`、`m3_level_l = 0.325`、`l_stratum_gain_rate = 0.0`、
  `h_minus_l_difference = 0.0`、`m3_level_overall = 0.07647058823529412`
- `m3_implementation_agreement = 1.0`（480 件照合、不一致 0）
- 対照電池: PC0 170/170、**PC0-CAS 80/80**、PC1 80/80、PC2a 80/80、PC2b 0/60（凍結期待値どおり）、
  PC2c 170/170、PC2d 170/170、PC3a 48/48、PC3b 60/60、
  **PC4 gain 100/170（H 100、寄与家系 6、`gates_ok=True`）**、PC4b 60/60

### 未解決の争点 — 主エンドポイントの verdict（Stage 8 で独立導出中）

`partA_endpoints.json` の `verdict` フィールドは ladder rung `no_gain_observed_bound_only` を
書いているが、v2.1 §7.5 item 3 と named contingency 1 は、二方向感度分析が異なる rung に落ちた場合の
verdict を `undecidable` と**事前に**定めている。実現値は `sensitivity_agrees = false`:

| 方向 | k | rung |
|---|---|---|
| 記録上の方向（could-not-evaluate を不一致と数える） | 0 | `no_gain_observed_bound_only` |
| 敵対方向（could-not-evaluate を一致と数える） | 6 | `matcher_attributable_gain_confirmed` |

判定を左右しているのは **9 件のトリプルのみ**で、すべて `SymbolicEquivalenceTimeout`。
影響を受ける H 成分は 6 件（`R03_validation_d101_005` comp0、`R05_validation_d101_000` comp1、
`R07_validation_d101_000` comp1、`R07_validation_d101_002` comp2、`R07_validation_d101_003` comp1、
`R07_validation_d101_009` comp2）。凍結コードの敵対的再計数は**成分粒度**で、その成分に
could-not-evaluate トリプルが 1 件でもあれば成分全体を gain=1 に反転させる（`endpoints.py:117-127`）。
cutpoint が 3 しかないため、9 件のトリプルで rung が動く。

**v2.1 は mid-cycle でのタイムアウト引き上げを明示的に禁じている**（named contingency 1:
"No timeout value is raised mid-cycle — that would change the frozen instrument"）。
したがって本サイクル内での解決手段はない。この争点は `lansr-results-analyst` と
`lansr-statistical-reviewer` に**私の結論を伝えずに**独立導出させている（規則 R5 の理由により）。

### PC0-CAS の検証を discharge（保留を解消）

保留事項だった「in-process monkeypatch が実際に効いているか」を実測で立証した。
`gpu_run4/formulas.py:13` は `from ... import SYMPY_MAX_NODES` で名前を取り込み、
`formulas.py:434` はそれを module global として読むため、`controls.py:83` の属性代入は有効。
実測: 既定 cap 40 では CAS 自己同一性が **28/80 系統**しか通らず、cap 200 では **80/80** 通る。
52 系統で結果が変わったことが、パッチが有効であることの実証である。
**PC0-CAS 80/80 は信頼して良い。**

**規則 R1 に従った位置づけ（重要）。** 「既定 cap 40 で 52/80 系統が CAS 自己同一性を通らない」は
**新しい発見ではない**。§8 の既知欠陥として Stage 3 の再現性監査が既に記録していた数値と一致する。
したがってこれは監査値に対する **ポジティブコントロール**であり、そのようにラベル付けする。
発見として報告してはならない。この一致自体が、監査値と本測定が同じものを測っていることの確認になる。

なお影響範囲は M1 / GPU_RUN4 経路に限られる。M3 は
`evaluation/equation_metrics.py:169 symbolic_recovery` の別経路であり、PC0 = 170/170 がそれを示す。

- **テストスイート**: 413 passed, 1 skipped（Phase 1 実行前に測定）
- **実行中**: Phase 2（Part B、background `bonmef27a`）、`lansr-results-analyst`、
  `lansr-statistical-reviewer`
- **Gate B→C の注意**: Part A が `gain_confirmed` を返した場合、Part C（phase 3）は**実行しない**。
  replication を優先する。`gate_b_to_c()` が機械的に強制する。
- **未検証のまま残る点**: Part C の VRAM は 2 セルでのみ検証済み。実スケール
  （約 60 系統 x 最大 12 セル）は未確認。
- **阻害要因**: なし。ハードストップ条件は非該当。
- **git**: PR #4 は OPEN。routine な push と PR 更新は事前承認済み
  （`.claude/rules/14-push-and-pr.md`）。
- **C0001 レポートに必ず含めること**: 規則 R5 の妥当性への脅威の開示。本サイクル内で supervisor の
  偽陰性が 3 件発生し（未検証の比較手法による）、かつ主エンドポイントは null 型であるため、
  supervisor の誤り方向と主仮説が同じ向きを指している。

### 次の行動
1. Phase 2（Part B）完了を待ち、Gate B→C を評価（`gate_b_to_c()`）。Part A が
   `gain_confirmed` でない限り Part C の実行可否は `n_in_support >= 30` に依存する。
2. Stage 8 の 2 subagent の結果を統合。verdict の独立導出が一致するか確認する。
3. Stage 9 独立敵対的査読（`lansr-independent-reviewer`）、Stage 10 replication gate、
   Stage 11 `reports/C0001_report.md`（結果が負・null・無効でも必須。**日本語**）、
   Stage 12 manifest + SHA256、Stage 13 negative-result-recovery、Stage 14 state と
   hypothesis_tree の更新、その後 C0002 へ。
4. C0002 の有力候補: 本サイクルで verdict を左右した 9 件の `SymbolicEquivalenceTimeout` を、
   引き上げた cap で事前登録の上で解決する。比較は 9 件のみで計算費用は無視できる。
   これは threshold を後から動かして結果を救済する行為ではなく、**新しい事前登録サイクル**である
   （v2.1 named contingency 1 が指定する唯一の正規経路）。
