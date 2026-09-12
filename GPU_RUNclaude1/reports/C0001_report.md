# C0001 サイクルレポート（Stage 11）

**発行**: 2026-09-11、supervisor。`.claude/rules/08-cycle-persistence.md` により、
本レポートは結果が負・null・無効・`undecidable` であっても必須である。本サイクルの結果は
**`undecidable`** であり、以下は全文をその前提で書く。

| 項目 | 値 |
|---|---|
| サイクル | `C0001` |
| 拘束契約 | `GPU_RUNclaude1/plans/C0001_preregistration_v2.1.md`（および同 `.json`）。v1・v2 は失効し、履歴としてのみ保存 |
| branch | `20260909_researce_GPU_RUNclaude1` |
| run id | `gpu_runclaude1_c0001_b731cdd`（phase0 manifest commit `b731cddd168390c973dbb0974349e4a2c55b9113`、phase1/2/3 manifest commit `8ff622defc227b4598e0094fc000b8227c4ffdad`） |
| **本サイクルの verdict of record** | **`undecidable`**（v2.1 §7.5 item 3 / §10.3。二方向感度分析が異なる ladder rung に落ちたため） |
| 独立レビュー（Stage 9） | `GPU_RUNclaude1/reviews/C0001_independent_review.md`（1,039 行）。勧告 **`REPLICATE`（ブロッキング）** → instrument fact に限り **`ACCEPT_AS_PRELIMINARY`** |
| Stage 10 追試 | `GPU_RUNclaude1/replications/C0001_opportunity_census_replication.md`。エンドポイント算術は REPLICATED、独立レビュー自身の機会センサス定量は FAILED REPLICATION（結論の向きは維持） |

---

## 1. 要旨（Executive summary）

C0001 は、GPU_RUN5 が公表した「Hill 型 GRN 成分の骨格がビームに一度も入らない」という測定
（`true_exponent_aware_skeleton_in_beam_rate = 0.0`、`component_true_exponent_aware_skeleton_in_beam`
= 107/2040）が、凍結された指数考慮の正規木マッチャ（M0）自身の限界による**測定artifact**なのか
（説明 E0）を、定数畳み込みマッチャ（M3）で検定する目的の事前登録サイクルである。

**主エンドポイントの verdict of record は `undecidable` である。** 二方向感度分析
（`could_not_evaluate` を不一致とみなす記録上の方向と、一致とみなす敵対的方向）が異なる ladder rung
（`no_gain_observed_bound_only` 対 `matcher_attributable_gain_confirmed`）に落ちたためであり、
v2.1 §7.5 item 3 が事前に定めた `undecidable` トリガそのものである。**したがって仮説 H-C0001-P は
supported でも unsupported でも refuted でもない。** `K = 0` という生の観測は `undecidable` の
ラベルとともに報告してよいが、**E0 の賛否いずれにも引用してはならない**。

さらに重要な点として、独立レビューと Stage 10 追試は、130 の分析単位（Hill 層 `\|H\| = 130`
成分）のうち **大半で実は測定機会自体が存在しなかった**ことを明らかにした。すなわち本サイクルは
**負の結果ではない**。負の結果が存在するには、その母集団の上で試行が行われている必要があるが、
妥当性が検証されたスクリーンによれば機会があった成分は高々 88/130 であり（下限は検証されて
いない）、独立査読が最初に報告した「121/130 に機会なし」という定量そのものも Stage 10 で
無効化された（下記 §7、§10）。独立レビューアの最終処分は **REPLICATE（ブロッキング）**、
その後 instrument fact に限り **ACCEPT_AS_PRELIMINARY** であり、**INVALIDATE にも
ACCEPT_AS_NEGATIVE にも該当しない**。

サイクルが確定的に確立したのは、マッチャについての知見ではなく、**候補生成器についての知見**
である。PC4（gain 指標の陽性対照）は、正しい書き換え形が存在すれば指標が 100/170 件発火する
ことを示した。ビームはその形を一度も提案しなかった。

本サイクル中、supervisor 自身の分析に **7 件の撤回**が生じた（§9）。撤回はいずれも
未検証の比較手法から偽陰性・誤った機構主張を導いたという同一の失敗様式であり、主エンドポイントが
null 型であることと合わせて、rule R5 の妥当性への脅威として開示する。また事前登録された
Gate B→C を無視して Part C が実行される逸脱が発生し（§5）、Part C の成果物は
`INADMISSIBLE` として保存され、いかなる帰属主張にも使用していない。

---

## 2. 仮説（Hypothesis）

**H-C0001-P（主仮説、確認的）**（v2.1 §1、原文）:

> E0 does not explain the Hill-component generation failure. Among the Hill / variable-denominator
> truth components of the 80 GRN validation systems, a canonicalizing constant-collapsing matcher
> (M3) recovers no in-beam structural matches that GPU_RUN5's frozen exponent-aware canonical-tree
> matcher (M0) scored as misses, at the magnitude E0 requires. Predicted value of the primary
> endpoint: 0.

falsifier: `C = ceil(0.02 × 130) = 3` 件を超える Hill 成分がマッチャ起因の gain を示せば
H-C0001-P は refuted。1〜3 件は unsupported（refuted ではない）。

四つの競合説明（v2.1 §1.1）:

| id | 説明 | v2.1 開始時点の状態 | 判定パート |
|---|---|---|---|
| E0 | 評価器・測定artifact | LIVE、成分水準の経験的裏づけは撤回済み（`C0001_RETRACTION_neg_finding.md`） | Part A |
| E1 | 生表現能力 | **REFUTED**（P1）。再検定せず | 引用のみ |
| E1' | 生成器サポート除外 | LIVE（P5, P6） | Part B |
| E2 | 事前確率質量 / モデル誤差 | LIVE | Part C |
| E3 | 探索誤差 | LIVE | Part C |

E0・E1'・E2・E3 は互いに排他ではなく、単一勝者の主張は禁止（v2.1 §1、§10.3）。

**§1.3 の凍結スコープ制限（本サイクルが実際に検定できる範囲）**: E0 は 2 つの開示済み機構を持つ。
(M-i) P4 符号化非対称は M0 に **170/170 で吸収済み**（Q12b）であり、gain 指標は構成上恒等的に 0
— `K = 0` はこの機構について**何も語らない**。(M-ii) アフィン分解は定数畳み込みの下で
**いかなるマッチャでも検出不能**（M3・M1・M0 いずれも不可、M2 は rule 06 によりカット済み）。
本サイクルが実際にテストするのは (M-iii) 代数的再結合・共通分母化のみであり、PC4 がその実証済みの
陽性対照である。**verdict をこれら以外の一般命題（「E0 は偽」「正規化に意味がない」等）へ拡張して
はならない。**

---

## 3. 文献と novelty の文脈

- 教師強制スコアリング（Part C の手法）は novelty 主張の対象外: Stahlberg & Byrne,
  EMNLP-IJCNLP 2019, pp. 3356–3362, **DOI 10.18653/v1/D19-1331**
  (https://aclanthology.org/D19-1331/)。v2.1 §1.2 が明示的に引用を義務付けている。
- 本サイクルはビームサイズ・温度の掃引を行わない（既存文献が答えを与えるため、v2.1 §1.2）。
- 生物学的因果性の主張は一切行わない（rule 01 item 7）。対象は合成 Hill 型 GRN システムである。
- **`INFERENCE`**: 定数畳み込みマッチャによる GRN 成分再評価という組み合わせ自体がキャンペーン
  内で novel かどうかは、リポジトリ内に類例が無いことのみから判断しておらず、`unverified` として
  扱う（`.claude/rules/11-literature-and-novelty.md`）。本サイクルはこの点について文献レビュー
  agent を個別に走らせていない。

---

## 4. 事前登録された設計（Preregistered design）

拘束契約は **`GPU_RUNclaude1/plans/C0001_preregistration_v2.1.md`** のみ（v1・v2 は失効した
歴史記録）。v2.1 は v2 の Stage-5 監査（`reviews/C0001_v2_reproducibility_audit.md`、3 CRITICAL /
7 MAJOR / 10 MINOR、verdict `AMEND_BEFORE_RUN`）への応答であり、主エンドポイント・層定義・
集計順序・ladder cutpoint・Part B/C 設計は変更せず、コントロール電池と 2 つの統計文・M0 の性格
づけ・開示記録のみを修正した。

**主エンドポイント**（v2.1 §7.1、不変）: `hill_component_matcher_attributable_gain_rate`。
Hill / 変数分母型の真値成分の集合 `H`（`\|H\| = 130`）について、cell 内 usable candidate に対する
`ANY` 還元後、`gain(s,i) = 1[m3_any(s,i) ∧ ¬m0_any(s,i)]` を成分ごとに評価し、`K = Σ gain` を
集計する。

**統計単位の三層構造**（v2.1 §2.1）: truth component（n=170、主エンドポイントの解析要素）、
parameterized system（n=80、10/家系、リサンプリング・クラスタ）、family（n=8、R01–R08、
第二クラスタ、次元と完全に交絡）。集計順序は「cell 内 ANY → 成分の 12 cell 間 ANY →
成分横断集計、system・family クラスタリング」で凍結。

**区間**: (a) Wilson score、(b) 二段クラスタブートストラップ（`numpy.random.default_rng(20260909)`、
10,000 resample、家系→家系内 system の順）、(c) 8-cluster family-level Wilson。
**記録上の bound: `K ≥ 1` なら (b)、`K = 0` なら (c)**（v2.1 §7.1、V2-MAJ-3。退化した
percentile 上限 0 を報告することを禁止）。

**効果量の改訂**（V2-MAJ-4）: E0 が超えるべき量は M0 自身の `ANY`-over-12 還元後の成分率であり、
公表された 107 件について**この量自体は同定されていない**。admissible range は
`[9/170, 107/170] = [0.053, 0.629]`。0.0525 はこの範囲の**算術的下限としてのみ**使用する（保守的な
方向、検定力計算に用いる）。

**コントロール電池**（v2.1 §7.7、Gate A→B に統合）: PC0（M0 破損検知、170/170）、PC0-CAS
（CAS 自己同一性、cap=200 で 80/80）、PC1、PC2a（harness identity、M0=M3=170/170・80/80、
`short_circuited: true`）、PC2b（アフィン分解限界、非ゲート、期待値 0）、PC2c/PC2d（可換順列、
170/170）、PC3a/PC3b（指数・変数置換の特異性、48/48・60/60）、**PC4**（gain 指標陽性対照、
hard-abort gate: `gain_pc4_total ≥ 40 ∧ gain_pc4_H ≥ 20 ∧ ≥3 家系寄与`）、PC4b。

**Gate 構造**（v2.1 §10.1）: Gate 0（事前）→ Gate A→B（9 項目、PC0/PC4/PC2a は HARD）→
Gate B→C（(i) Part A が `undecidable` でないこと、(ii) `n_in_support ≥ 30`）→ Gate C→report。

**verdict 基準**（v2.1 §10.3）: `supported`（Gate A→B 全通過かつ PC4 通過かつ `K=0`）、
`unsupported`（`1 ≤ K ≤ 3`）、`refuted`（`K > 3`）、**`undecidable`**（PC4 不合格、PC0/PC2a 不一致、
`could_not_evaluate_rate > 2.0%`、**§7.5 item 3 の二方向感度分析が異なる rung に落ちる場合を含む**、
他多数の条件）。

**計算上限**（不変、v2.1 §11）: GPU 0 で ≤ 4.0 GPU 時間・ピーク VRAM ≤ 5.5 GiB（アロケータキャップ
として強制）、CPU ≤ 24 core-hours、新規ディスク ≤ 15 GiB。測定基準は Q17: M0+M1+M3 で
120 候補あたり平均 655 ms、47,987 候補への投影 8.73 single-core-hours。

**封印テスト**: C0001 はいかなる封印済み成果物も読まない（`phase < 8`、v2.1 §2.4）。7 個の封印
ファイルが実在し、実行時に列挙・許可リスト外として扱われた。C0001 は 0 件の封印パスを開いた
（`phase0/firewall_test.json: sealed_paths_read: []`）。

---

## 5. 逸脱（Deviations）

### 5.1 DEVIATION — Gate B→C 違反下での Part C 実行

出典: `GPU_RUNclaude1/analyses/C0001_DEVIATION_gate_b_to_c_violation.md`。

Part A の記録すべき verdict は `undecidable`（v2.1 §7.5 item 3）だったが、supervisor が実装した
`gate_b_to_c()` は項目 (i) の第一文（「Part A is **not** `undecidable`」）を実装しておらず、
かつ参照先の `partA_endpoints.json:primary.verdict` フィールド自体が二方向感度分析の override を
適用していない欠陥フィールドだった（二重の失敗）。結果として `phase3/gate_b_to_c.json` は
`ok: true` を書き、Part C は完走した。

**被害の範囲**（同分析より逐語）:

| 項目 | 実際 |
|---|---|
| 消費した GPU 時間 | 約 1 分（上限 4.0 h に対して無視できる） |
| ピーク VRAM | 0.454 GiB（上限 5.5 GiB 内） |
| 封印テストへの接触 | なし（`sealed_paths_read: []`） |
| Part C から導出した科学的主張 | なし |
| 無効化される結論 | なし |

Part C の決定エンドポイント C2-P はそもそも計算されていない。`phase3` スクリプトは
`gt_logprob_sum` と計器監査のみを出力し、`lp_sel`（選択候補）・`lp_best`（最良候補）を採点して
いないため、`stahlberg_byrne_indicator` は一度も呼ばれていない。**したがって撤回すべき Part C
由来の主張は存在しない。** `phase3/` の成果物は破棄せず、`results/runs/gpu_runclaude1_c0001_b731cdd/phase3/INADMISSIBLE.md`
として帰属使用不可のマークを付けて保存した:

> この phase3 成果物は帰属に使用できない (INADMISSIBLE)。v2.1 Gate B→C 項目 (i)「Part A is not
> undecidable」に違反して実行された。保存は監査のため。いかなる E2/E3 帰属にも使用してはならない。

対応: `gate_b_to_c()` を項目 (i)(ii) の全文に合わせて修正、`endpoints.py` の `verdict` を
`sensitivity_agrees == false` のとき `undecidable (two-sided sensitivity disagreement)` に修正
（凍結契約は一切変更していない）、C0001 内での Part C 再実行はしない。

### 5.2 供給側の欠陥（研究状態に記録済み、契約は変更していない）

- `partA_endpoints.json` の `verdict` フィールドは v2.1 §7.5 item 3 の override を適用していない
  実装欠陥である（§5.1 の遠因）。`sensitivity_verdict_non_match_direction` /
  `sensitivity_verdict_match_direction` は `PrimaryEndpointResult` に存在するが成果物に
  永続化されておらず、`cell_cache` からの再計算でのみ復元できた。
- v2.1 §8.3 は「the frozen selection rule (`gpu_run5_selection.py:11`)」を `lp_sel` の定義に
  用いているが、その関数 `formula_selection_key`（`src/evaluation/gpu_run5_selection.py:9`）は
  run 間モデル選択スコアラであり、セルごとの候補選択器ではない。実装エージェントは
  `src/gpu_run5/evaluation.py:107 select_candidate`（比較子 `"official_reconstruction"` が
  無条件に `candidate_index == 0` を返す）を採用し、引用不一致をコードに記録した。**契約側は
  修正していない**。詳細は §11 の CRITICAL-R3 を参照。
- `phase1/partA_component_summary.json` が書かれていない（v2.1 §12.1 が要求）。詳細は §14。

---

## 6. 実際に実行した手法（Methods actually run）

**Part A**（CPU のみ）: M0 / M1 / M3 の 3 マッチャを、47,987 件の保存済み候補・170 個の真値成分・
960 cell に対して独立に（カスケードではなく並行して）適用した。両側とも infix 表現を使用
（AUDIT-CRIT-2 の要求）。process ベース並列、最大 6 ワーカー。

**Part B**（CPU のみ）: 生成器のサポート内外を、保存済み真値に対する解析的な unary budget
センサス（B-R1..B-R4、200 通りの書き換え上限、`numeric_equivalent(seed=0)` による検証）で判定。

**Part C**（GPU、Gate B→C 違反下で実行、**帰属には使用不可**）: 教師強制の対数確率の総和のみを
計算し、決定エンドポイント C2-P は計算していない。

**Stage 8 の独立解析**: `lansr-results-analyst` による独立導出（`analyses/C0001_partA_stage8_analysis.md`）、
`lansr-statistical-reviewer` による独立レビュー（`reviews/C0001_partA_statistical_review.md`）。

**Stage 9 独立敵対的査読**: `lansr-independent-reviewer`
（`reviews/C0001_independent_review.md`、1,039 行）。実装・一次解析・統計レビュー・supervisor の
いずれとも別のエージェント。第一次試行は `oauth_org_not_allowed`（HTTP 403、request id
`req_011CeshpLHg1Yo8WEb1Krvdn`）で異常終了し、再投入で完走した（§13）。

**Stage 10 追試**: 独立の役割（実装者・一次解析者・統計レビュア・独立レビュアのいずれとも別）が
`results/runs/` に一切書き込まずスクラッチパスで実行し、機会センサスと `could_not_evaluate` の
非決定性を独立測定した（`replications/C0001_opportunity_census_replication.md`）。

**探索的（exploratory、凍結計器の外）**: `could_not_evaluate` のタイムアウト再採点
（`analyses/C0001_endpoint_irreproducibility.md`）。凍結タイムアウト値 `SYMPY_OP_TIMEOUT_SEC = 10.0`
は一切変更していない。この再採点はエンドポイントを差し替える根拠には**ならない**。

---

## 7. 結果（Results）

### 7.1 Part A の実現値（`gpu_runclaude1_c0001_b731cdd/phase1/`）

Gate A→B は 9 項目すべて通過。項目 (i)（M0 の厳密再現）は `cell_cache` から独立に再計算して一致を
確認した。

| 量 | 実現値 | 凍結された期待値 |
|---|---|---|
| 採点済み候補 | 47,987 | 47,987 |
| 成分比較 | 101,963 | 101,963 |
| system 水準 M0 一致 | 0 / 960 セル | 0 / 960 |
| 成分水準 M0 一致 | 2,235 | 2,235 |
| 家系別 M0 一致 | R04 1,736 / R07 330 / R08 169 | — |

三マッチャの集合分解（入れ子カスケードではなく三つの独立集合として）:

| 分解 | system 水準 | 成分水準 | ANY 還元後の成分 |
|---|---|---|---|
| M0 一致 | 0 | 2,235 | 13 / 170 |
| M1 一致 | 0 | **0** | — |
| M3 一致 | 0 | 2,235 | 13 / 170 |
| M3 のみ（M0 は不一致） | 0 | 0 | **0** |
| どちらも不一致 | 960 | 99,728 | 157 / 170 |

主エンドポイント: `n_h = 130`、`k_gains = 0`、`ladder_cutpoint = 3`。
`wilson_95 = [0.0, 0.028701561634224194]`。cluster bootstrap は点推定 0.0、CI `[0.0, 0.0]`
（10,000 resample、seed 20260909）— **退化のため記録上の bound には使わない**。記録上の
bound of record は `family_level_wilson_8_cluster = [0.0, 0.3244075683414076]`。
`could_not_evaluate_rate = 0.00011540976879576318`（H のみの分母。契約上の分母
`9/101,963 = 0.0000882673126526289` とは異なる — Stage 8 統計レビュー MAJOR-2）。

二次: `m3_level_h = 0.0`、`m3_level_l = 0.325`、`l_stratum_gain_rate = 0.0`、
`h_minus_l_difference = 0.0`、`m3_level_overall = 0.07647058823529412`。
`m3_implementation_agreement = 1.0`（480 件照合、不一致 0。`phase0/m3_agreement_test.json` は
`n_pairs_realized: 1178`、`n_disagreements: 0`。※ この数値は v2.1 §12.1 が名指す
`m3_implementation_agreement.json` ではなく `m3_agreement_test.json` というファイル名で保存
されている — 名称の逸脱であり内容は要求どおり）。

コントロール電池: PC0 170/170、PC0-CAS 80/80、PC1 80/80、PC2a 80/80、PC2b 0/60（凍結期待値どおり）、
PC2c 170/170、PC2d 170/170、PC3a 48/48、PC3b 60/60、**PC4 gain 100/170（H 100、寄与家系 6、
`gates_ok=True`）**、PC4b 60/60。

### 7.2 verdict の独立導出（3 者、規則の適用に注意 — §9 訂正2 参照）

| 方向 | k | rung |
|---|---|---|
| 記録上の方向（`could_not_evaluate` を不一致と数える） | 0 | `no_gain_observed_bound_only` |
| 敵対方向（`could_not_evaluate` を一致と数える） | 6 | `matcher_attributable_gain_confirmed` |

判定を左右しているのは **9 件のトリプルのみ**（すべて `SymbolicEquivalenceTimeout`）。影響を受ける
H 成分は 6 件。凍結コードの敵対的再計数は成分粒度で、その成分に `could_not_evaluate` トリプルが
1 件でもあれば成分全体を `gain=1` に反転させる。cutpoint が 3 のため、9 件のトリプルで rung が動く。

v2.1 は timeout 値の mid-cycle 引き上げを明示的に禁じている（named contingency 1）。本サイクル内
での解決手段はない。**したがって H-C0001-P は supported でも unsupported でも refuted でもない。**

### 7.3 Part B の実現値

`B2-S2_component_out_of_support_rate = 9 / 170 = 0.052941176470588235`、
Wilson `[0.02809938268872226, 0.09754072078170467]`。サポート外 9 成分はすべて H に属し、
すべて `component_index = 2`、家系は R07 が 6・R08 が 3（`u_min` は R07 で 6 または 10、R08 で 5、
`uses_only_in_support_operators` は全件 `True`）。

### 7.4 生成 vs 選択（rule 03 の区別。両方とも H の外側にあることに注意）

component 解像度で **oracle（cell 内全候補の ANY）107/2040** に対し **selected
（`candidate_index == 0`）58/2040**。H 層では oracle が全解像度でゼロ。

**この「selected」読みは安全ではない**（§11 CRITICAL-R3）: 保存された候補集合は
`beam_type = "sampling"` であり、`model_wrapper.py:107-113` でスコア順に並べ替えるのは
`"search"` 分岐のみ。したがって `candidate_index == 0` は選択の結果ではなく単なる標本順であり、
「oracle 107 のうち 49 件が top-1 に届かない」という選択失敗の読みは**supervisor の撤回済みの
誤り**である（§9 訂正1）。

### 7.5 機会センサス — 見出し量と、その定量の撤回

独立レビューは統計レビュー CRITICAL-2（「M3 が M0 と異なる機会が実際に何回あったか、一度も
測られていない」）に応答し、この量を測定した(§7.5.1)。**この定量は Stage 10 追試で無効化
された(§7.5.2)。結論の向き自体は維持される。**

#### 7.5.1 独立レビューの当初の測定（`reviews/C0001_independent_review.md` §2.2）

| スクリーン | 通過した H トリプル | 通過した H 成分 |
|---|---|---|
| M3 が一致しうるための必要条件（変数を含む分母。書き換え不変） | 5,851 / 77,983（92.50% が構造的に不可能） | **88 / 130** |
| 演算子多重集合の一致（M0/M1 の必要条件。realized 2,235 件すべてが充足、偽陰性 0） | **187 / 77,983（0.24%）** | **9 / 130** |

`n_eff ∈ [9, 88]`、`Wilson(0, 9) = [0, 0.299145]`、`p = 0.0525` での検定力は **0.38452**
（報告値 0.99910 に対して）。「121/130 の H 成分に機会が存在しなかった。うち 112 は生成器サポート
の内側」。独立レビューはこれを「サイクル中で最も情報量の多い事実」と位置づけ、
`ACCEPT_AS_PRELIMINARY` の条件として一次結果扱いを要求した。

#### 7.5.2 Stage 10 追試による撤回（`replications/C0001_opportunity_census_replication.md` §5, §8 CRITICAL-1）

> **撤回: 演算子多重集合スクリーンによる定量。** `n_eff = 9`、`Wilson(0,9)`、検定力 0.38452、
> 「121/130 に機会なし」「うち 112 がサポート内」は**すべて無効**。根拠となる演算子多重集合
> スクリーンは **M0 の必要条件であって M3 の必要条件ではなく**、H 層で唯一の非循環な陽性例である
> PC4 の gain 100 件を **100/100 すべて棄却する**。スクリーンの妥当性検証（「realized 2,235 件で
> 偽陰性 0」）は構成上循環している — 2,235 件は全て M0 = 1 であり、スクリーンは M0 必要条件なので
> 偽陰性 0 は定理であって証拠ではない。凍結コード上の反例:
> `symbolic_recovery("1.0 * (x_0 + x_1)", "2.0 * x_0 + 3.0 * x_1")["skeleton"] == 1.0` かつ
> `M0 = 0.0`（真の gain だが演算子多重集合は不一致）。
>
> **正しい定量: `n_eff ≤ 88`、検証された下限は存在しない。** 88 は**上限**であり、これを代入して
> 「許容域を除外した」と論じることはできない。

**訂正された E1' 帰属**（妥当なスクリーン S1 基準、機会なし 42/130）:

| 帰属 | 妥当なスクリーン S1 基準 | 類解像度（`K=0` と同値、参考） |
|---|---|---|
| 機会なし H 成分 | 42 / 130 | 130 / 130 |
| うち E1'（サポート外） | **4** | **9** |
| うち E2 / E3 | **38** | **121** |

「121」という数字は**同じ大きさの別集合 2 つの混同**だった（Stage 10 追試 MAJOR-2）:
サポート内 H 成分が 121、S3' スクリーンの機会なし成分が 121 であり、別物である。

**いずれの基準でも主因は E1' ではなく E2/E3** であり、結論の向きは維持される。追試の総合判定
（§8）: 「REPLICATED（算術）／ FAILED REPLICATION（`CRITICAL-R2` の定量）／
DIRECTIONALLY REPLICATED（`CRITICAL-R2` の結論）」。

### 7.6 M0 ≡ M3 の機構 — 骨格語彙の実質的な恒等収束（Stage 10 追試 CRITICAL-2、新規計測）

実現語彙上、89,349 件の成分文字列は **879 個**の定数畳み込み骨格クラスに collapse する。凍結
M3 関係はその 879 から **877 クラス**しか作らず、統合された 2 件はいずれも**候補↔候補の符号変異**
である。すなわち **M3 の定数畳み込み機構は、真の式と候補の対に対して一度も仕事をしていない。**
M0 対 M3 の対比は、ほぼ等価な 2 つの構文正規化の対比に退化していた。これは循環ではない測定であり、
「M0-M3 の一致が情報を持たない」ことの機構的説明を与える。

### 7.7 `could_not_evaluate` の非決定性（`analyses/C0001_endpoint_irreproducibility.md`、Stage 10 で数値付き再現）

同一入力・同一 10.0 秒上限で、**101,963 件中 14 件**の `match_outcome_m3` ラベルが双方向に揺れた
（確実な方向は 8 件）。`could_not_evaluate_rate` は再現しない（記録 run 9 件 対 追試 7 件、共通は
1 件のみ）。**ただし M3 の値そのものは 101,963 件すべてで一致したため `K = 0` は影響を受けない。**
9 件の `could_not_evaluate` は 9/9 が高精度数値評価で真の非一致と確認された（最小
`max\|gap\| = 5.725515111320960892531905883570670315132`）。**未決比較 1 件で verdict が
反転するという懸念は解消された**が、verdict `undecidable` 自体は 9 件のタイムアウトの計上
そのものに依存しており、その計上が非決定的であることは別の事実として残る。

機構の検証結果:

| 候補機構 | 検証 | 結論 |
|---|---|---|
| CPU 競合（6 ワーカー並列） | 競合 0 vs 6、各 6 反復 | **棄却**（平均 1.5 → 1.67） |
| SymPy キャッシュ状態 | 温 vs 冷 | **支持**（成分 1.5 → 2.0、トリプル 0.6 → 3.0） |
| メモリ圧・47,987 候補分のキャッシュ充填 | 未測定 | `unverified` |

再採点は凍結計器の**外**にあり、かつ 1 プロセス 9 ペアは 6 ワーカー 47,987 候補の忠実な再現では
ないため**探索的**であり、エンドポイントの差し替え根拠にはしない。

---

## 8. 統計レビュー（Stage 8、`reviews/C0001_partA_statistical_review.md`）

統計レビューの CRITICAL 3 件・MAJOR 9 件（要旨、独立査読による再確認・格付け込み）:

| id | 内容 | 独立査読による評価 |
|---|---|---|
| CRITICAL-1 | `partA_endpoints.json:primary.verdict` が v2.1 の mandated verdict（`undecidable`）と矛盾する | **正しく、過大評価でもない** |
| CRITICAL-2 | 主エンドポイントがこのコーパス上で実現した識別力を持たず、Bernoulli モデルの前提が崩れる | **正しく、過小評価**（独立査読が §2.2 で `[9, 88]/130` を実測。ただしこの実測自体が Stage 10 で部分的に無効化 — §7.5.2） |
| CRITICAL-3 | 弱い区間から検定力主張への fallback が循環しており、mandated な family-clustered power が未計算 | **正しい** |
| MAJOR-1〜9 | `K=0` の必須文言欠落、`could_not_evaluate_rate` の分母不一致、§7.5 item 3 の scale mismatch、verdict の非決定性、ICC 設計効果表の anchoring 誤り、interval(c) のモデルと §2.2 の estimand の矛盾、null-branch gate の空虚性、secondary の区間・多重性開示欠如、非ゲートの `severity: "CRITICAL"` 文字列が `go_conditions` に残存 | 独立査読 §6 が個別に再確認・格付け（本文参照） |

統計レビューの MAJOR-3（「食い違いには 4 成分が必要」）は独立査読により**誤りかつ過小評価**と
訂正された（§11 CRITICAL-R1 を参照。実際の閾値は 1 成分）。

---

## 9. 独立レビュー（Stage 9、`GPU_RUNclaude1/reviews/C0001_independent_review.md`）

査読者: `lansr-independent-reviewer`。実装・一次解析・統計レビュー・supervisor のいずれとも別。
**Bottom line**（原文の表、逐語訳せず要旨のみ日本語化）:

| 攻撃対象の主張 | 判定 |
|---|---|
| 1. Part A の verdict of record は `undecidable` | **成立するが、契約が挙げる理由より狭い理由による。かつ run of record 限定** |
| 2. M0 ≡ M3 pointwise、対称差 0（101,963 件） | **算術としては成立、証拠としては不成立**（H 層で 77,983 件中 187 件のみ、H 成分では 130 中 9 件のみが比較可能で、M3 はそのいずれにも一致していない） |
| 3. E1' は高々 9/170 成分を説明する | **成立**（H 内 9/130、Hill-4 の綴りは正しいと検証済み） |
| 4. Gate B→C 違反は科学的被害を生まなかった | **被害については成立、残存物のラベリングについては不成立** |
| 5. supervisor の信頼性割引 | **一様ではない**。二つの主要な結論は影響を受けず、撤回の作法は健全 |

**新規 CRITICAL 3 件**:

- **CRITICAL-R1**: 凍結契約は自らの verdict を決定できない。実時間エンドポイント + 実行環境の
  未固定（≤6 ワーカーが凍結されていない）+ 「非ゼロなら発動」トリガ + 3 段 ladder の組み合わせ。
  独立査読自身の再計測では 8 反復中 6 回が `undecidable`、2 回が `no_gain_observed_bound_only`。
  `k_adv ∈ {1,2,3}` はすでに `weak_gain` で `k=0` と別 rung なので、**枢軸は 9 対 3 ではなく
  1 対 0**（H 成分 1 件のタイムアウトで `undecidable` が決まる）。
- **CRITICAL-R2**: 130 分析単位のうち多数（当初報告 121）で試行が実現していない。すべての区間と
  検定力が `n=130` を仮定している。**この定量自体が Stage 10 で FAILED REPLICATION と判定された
  （§7.5.2）が、結論（支持された結論をブロックする）は Stage 10 で REPLICATED、かつ強化された。**
- **CRITICAL-R3**: `lp_sel` を `candidate_index == 0` で取ると search error を測れない
  （`beam_type = "sampling"`）。`sb_sel` は `search_error_system_rate` を 1 に膨らませ **E3 を
  捏造しうる**。C0001 は未汚染（C2-P を計算していないため）だが、**C0002 でこれを凍結して
  はならない**。

推奨: **`REPLICATE`（ブロッキング）** → その後 instrument fact に限り **`ACCEPT_AS_PRELIMINARY`**。
根拠（§12、逐語要旨）: (1) verdict は 8 反復中 6 回のみ `undecidable`、(2) 主エンドポイントの
実現分母は名目 130 のうち 9〜88、(3) CRITICAL-R3 は C0002 の決定エンドポイントを拘束する、
(4) Stage 8 の 2 件の CRITICAL は成果物レベルでは未修復のまま。**`INVALIDATE` には該当しない**
（リーク・除外バイアス・事後閾値変更なし、決定論的部分は厳密に再現）。**`ACCEPT_AS_NEGATIVE` にも
該当しない**（130 中の多くの単位で測定が成立していないため、そもそも負の結果が存在しない）。

`ACCEPT_AS_PRELIMINARY` として報告してよい instrument fact（独立査読 §12 が列挙、全て決定論的）:
M0 の厳密再現、三集合の関係（`\|M0\|=\|M3\|=2,235`、`\|M1\|=0`、対称差 0）、機会センサス
（訂正済みの数値。§7.5.2）、PC4 とその限界（M3 は R01 10/10・R05 20/20 を含む 30/130 H 成分で
`sympy.together` に失敗）、Part B の 9/170、および計器の欠陥一覧（実時間依存の verdict、
`.equals`-`None` の穴、空虚な PC2c/PC2d gate、`M1→M3` の空虚な単調性脚、`lp_sel` を無効化する
サンプリング順序）。

---

## 10. 追試状況（Replication status）

**トリガ条件**: v2.1 §15 (ii)「独立レビュアが Part A の結果を fragile とマークした場合」に該当
（CRITICAL-R1）。実行: `GPU_RUNclaude1/replications/C0001_opportunity_census_replication.md`。
追試者は実装者・一次解析者・統計レビュア・独立レビュアのいずれとも別。科学的設定
（閾値・キャップ・タイムアウト・シード）は一切変更していない。変更した独立因子: プロセス /
成果物パス（新規スクラッチパス、`results/runs/` へは一切書かない）、導出経路（三つ組ごとの評価から
定数畳み込み骨格の同値類メモ化へ）、真値側の派生元（`true_structure` prefix 派生から
`true_formula` infix 派生へ、規則 R1 準拠）、補助シード。

**総合判定**: 「見出し主張（M0 ≡ M3 pointwise）は算術として REPLICATED、証拠としては FAILED」
「`CRITICAL-R2` の結論（支持された結論をブロックする）は REPLICATED かつ強化された」
「`CRITICAL-R2` の定量（`n_eff=9`、130 中 121）は FAILED REPLICATION」
「`CRITICAL-R1`（壁時計依存）は REPLICATED、101,963 件中 14 件のラベル不一致という定量を付与」。

追試は `results/runs/gpu_runclaude1_c0001_b731cdd/` を一切変更していない（`git status --short`
で確認）。`GPU_RUNclaude1/reports/C0001_replication.md` という個別ファイルは v2.1 §12.1 に
記載があるが、本追試は `GPU_RUNclaude1/replications/C0001_opportunity_census_replication.md` として
保存されている（§14 に記録する命名の逸脱）。

---

## 11. 解釈（Interpretation）

**verdict `undecidable` の意味**: 二方向感度分析（`could_not_evaluate` を不一致とみなす記録上の
方向 `K=0` と、一致とみなす敵対方向 `K_adv=6`）が異なる ladder rung に落ちたため、v2.1 が事前に
定めた `undecidable` 条件が発火した。この機械的規則はデータの本質的な曖昧さからではなく、
**9 件のタイムアウトの計上が実行環境（≤6 ワーカーの未固定な実行、SymPy キャッシュ状態）に
依存して非決定的である**という計器の性質から生じている（§7.7）。**`K=0` は E0 の賛否いずれにも
引用してはならない**（v2.1 §9.5 item 0）。

**サイクルが実際に確立した事実**（すべて決定論的、独立再計算で確認済み）:

1. M0 の厳密再現（47,987 候補 / 101,963 成分比較 / 2,235 成分一致 / 0/960 system、全八家系カウント）
2. M0 ≡ M3 pointwise（対称差 0、101,963 件）、M1 は 0/101,963
3. 879 個の定数畳み込み骨格クラスが M3 のもとでは 877 クラスにしか collapse せず、統合はすべて
   候補↔候補の対（真値↔候補の対では M3 固有の機構が一度も発火していない）
4. PC4 の gain 100/170（H 100、寄与家系 6）
5. Part B の 9/170 が生成器サポート外

**サイクルの net の科学的内容はマッチャではなく候補生成器についてである。** PC4 は指標が
発火可能であることを示した。ビームがその形を一度も提案しなかったことが、正味の観測である。
機会センサスの訂正後の定量（§7.5.2）は、この読みを補強する:機会なし 42 成分のうち E1'
（サポート外）は 4 件のみであり、残り 38 件は E2/E3 の領域にある。

**繰り返し強調すべき境界**: 数値的な一致（`K=0`）は記号的回復を意味せず、記号的回復が生物学的
機構を意味することもない（rule 01 items 6-7）。非有意（あるいは本サイクルの場合 `undecidable`）は
同等性を意味しない（rule 01 item 8）。E0 の (M-i) 機構は M0 に吸収済みで gain 指標が構成上 0 に
固定されており、(M-ii) アフィン分解機構は本サイクルのいかなるマッチャでも検出不能である
（v2.1 §1.3）。したがって verdict は「代数的再結合・共通分母化という書き換えクラスについての
陳述」に限定され、それ以外へ一般化してはならない。

---

## 12. 限界（Limitations）

1. **`could_not_evaluate` の計上が非決定的**（§7.7）。verdict `undecidable` は再採点でも比較的
   頑健（冷キャッシュ 6 反復中 5 回）だが、機構は未解明（`unverified`）である。
2. **機会センサスの下限は未検証**（§7.5.2）。妥当なスクリーン S1 は上限 `n_eff ≤ 88` のみを与え、
   下限は存在しない。したがって `K=0` が凍結許容域 `[0.053, 0.629]` を排除したとは主張できない。
3. **`lp_sel` は search error を測れない**（CRITICAL-R3）。`beam_type = "sampling"` のため
   `candidate_index == 0` は選択の結果ではなく標本順である。C0001 は C2-P を計算していないため
   汚染されていないが、C0002 でこの実装を凍結してはならない。
4. **アフィン分解機構（M-ii）は本サイクルのいかなるマッチャでも検出不能**（v2.1 §1.3、Q14）。
   M2（CAS with constants）は rule 06 の計算上限（≈66 core-hours 対 24 core-hour ceiling）により
   カットされている。
5. **Part C の全成果物は帰属使用不可**（Gate B→C 違反、§5.1）。決定エンドポイント C2-P は
   計算されていない。E2/E3 の system 単位帰属は本サイクルでは得られていない。
6. **§12.1 が要求する成果物の一部が書かれていない**（§14 に一覧）。特に
   `phase1/partA_component_summary.json` の欠落により、下流の成分要約に依存する監査・
   Gate B→C 項目 (ii) 後半の機械的検証が制約される。
7. **supervisor の偽陰性 3 件が本サイクル内で発生**（rule R5、§9）、主エンドポイントは null 型
   であるため、supervisor の誤り方向と主仮説は同じ向きを指す。妥当性への脅威として開示する。
8. **運用基盤の制約**（`research_state.md` §5b）: アカウントは `team_labs_standard` シート
   （`organizationRole: user`）であり、Claude Max プランではない。本日 1 度、subagent 投入時に
   `oauth_org_not_allowed`（HTTP 403）が発生し再現しなかった。Remote Control は接続されていない
   （`ListAgents` で 0 件）。これらは本サイクルの結論を変えないが、査読の実行過程に記録すべき
   運用事実である。

---

## 13. 決定（Decision）

**`undecidable`**。

H-C0001-P は supported でも unsupported でも refuted でもない。理由: v2.1 §7.5 item 3 が
事前に定めた「二方向感度分析が異なる ladder rung に落ちた場合は `undecidable`」という条件が
発火した（§7.2）。加えて、独立レビューと Stage 10 追試により、130 の分析単位の大半で測定機会
自体が成立していなかったことが判明した（§7.5）。**本サイクルは負の結果ではなく、負の結果を
主張することも禁止する。** 独立レビューの処分は `REPLICATE`（ブロッキング）→
`ACCEPT_AS_PRELIMINARY`（instrument fact のみ）であり、`INVALIDATE` にも
`ACCEPT_AS_NEGATIVE` にも該当しない。

サイクルレポートは `.claude/rules/08-cycle-persistence.md` により必須であり、本文書がそれを
満たす。**サイクル結論には進めない**（研究状態 §「Stage 10 replication gate」を参照）。

---

## 14. 再現コマンド（Reproduction commands）

```bash
source /home/blabo/miniconda3/etc/profile.d/conda.sh && conda activate lansr310
git status --short   # クリーンであることを確認
git rev-parse HEAD
python -m pytest -q  # 467 passed, 1 skipped, 4 warnings（Stage 10 時点）
```

主要な生成物への参照（読み取り専用、封印パスは含まれない）:

```
results/runs/gpu_runclaude1_c0001_b731cdd/phase0/{environment_audit,checkpoint_audit,firewall_test,input_fingerprints,partA_cost_calibration,m3_agreement_test,manifest}.json
results/runs/gpu_runclaude1_c0001_b731cdd/phase1/{component_strata,m0_reproduction,matcher_monotonicity,partA_cell_failures,partA_controls,partA_endpoints,partA_ladder_realized,m3_implementation_agreement_census,manifest}.json
results/runs/gpu_runclaude1_c0001_b731cdd/phase1/cell_cache/*.json  (960 files)
results/runs/gpu_runclaude1_c0001_b731cdd/phase2/{partB_endpoints,partB_in_support_systems,manifest}.json
results/runs/gpu_runclaude1_c0001_b731cdd/phase2/partB_component_records.jsonl
results/runs/gpu_runclaude1_c0001_b731cdd/phase3/{gate_b_to_c,partC_instrument_test,manifest}.json
results/runs/gpu_runclaude1_c0001_b731cdd/phase3/{gpu_telemetry.jsonl,partC_cell_records.jsonl,INADMISSIBLE.md}
results/runs/gpu_run5_20260823_ddd267b0/phase3/{beam_groups.json,all_candidates.json}
results/runs/gpu_run5_20260823_ddd267b0/phase2/validation.json
```

Stage 10 追試のスクリプトはセッションスクラッチパス配下にあり、リポジトリにはコミットしていない
（`GPU_RUNclaude1/replications/C0001_opportunity_census_replication.md` §9 に一覧）。
`results/runs/` への書き込みは 0 件。

### 14.1 v2.1 §12.1 が要求し、本 run では書かれていない成果物

契約 §12.1 の完全な artifact リストと、`results/runs/gpu_runclaude1_c0001_b731cdd/` の実際の内容を
突き合わせた結果、以下が**書かれていない**（`find results/runs/gpu_runclaude1_c0001_b731cdd -type f`
で確認、2026-09-11）:

| 契約上のパス | 状態 |
|---|---|
| `R/manifest.json`（run-root の統合マニフェスト） | 欠落。phase ごとの `manifest.json` のみ存在 |
| `R/phase0/sealed_inventory.json` | 欠落 |
| `R/phase1/partA_records.jsonl`（per (cell, candidate, component) レコード） | 欠落 |
| `R/phase1/partA_component_summary.json` | 欠落（研究状態 §8 に既知欠陥として記録済み） |
| `R/phase1/partA_system_summary.json` | 欠落 |
| `R/phase1/m0_hits_stratification.json` | 欠落 |
| `R/phase2/partB_rewrites.jsonl` | 欠落 |
| `R/phase3/partC_identity_audit.json` | 欠落 |
| `R/phase3/partC_reencoding_audit.json` | 欠落 |
| `R/phase3/partC_endpoints.json` | 欠落（Gate B→C 違反下で C2-P が計算されなかったことと整合） |
| `R/phase4/mechanism_partition.json` | 欠落（`phase4/` ディレクトリ自体が存在しない） |
| `R/phase4/compute_accounting.json` | 欠落（同上） |

**名称が逸脱しているが内容が存在するもの**（欠落ではない）: 契約の
`R/phase0/m3_implementation_agreement.json` は実際には `phase0/m3_agreement_test.json` として、
契約の `R/phase1/partA_failures.jsonl` は `phase1/partA_cell_failures.json` として保存されている。
契約の `GPU_RUNclaude1/reports/C0001_replication.md` は実際には
`GPU_RUNclaude1/replications/C0001_opportunity_census_replication.md` として保存されている。

---

## 15. 成果物一覧（Artifact manifest）

Stage 12（`artifact-archive` スキル、`GPU_RUNclaude1/manifests/C0001_artifact_manifest.json` /
`C0001_checksums.sha256`）は本レポートの後続ステージであり、本文書の時点では未作成である
（`GPU_RUNclaude1/manifests/` は空）。以下は本レポートが参照した一次成果物の一覧。

**契約・審査・分析**:
- `GPU_RUNclaude1/plans/C0001_preregistration_v2.1.md` / `.json`（拘束契約）
- `GPU_RUNclaude1/plans/C0001_preregistration_v2.md` / `.json`、`C0001_preregistration.md` / `.json`（失効、歴史記録）
- `GPU_RUNclaude1/analyses/C0001_partA_stage8_analysis.md`
- `GPU_RUNclaude1/analyses/C0001_endpoint_irreproducibility.md`
- `GPU_RUNclaude1/analyses/C0001_DEVIATION_gate_b_to_c_violation.md`
- `GPU_RUNclaude1/analyses/C0001_RETRACTION_neg_finding.md`
- `GPU_RUNclaude1/analyses/C0001_pc2b_discrepancy_resolution.md`
- `GPU_RUNclaude1/analyses/C0001_precondition_verification.md`
- `GPU_RUNclaude1/analyses/C0001_exploratory_neg_canonicalization.md`
- `GPU_RUNclaude1/analyses/C0001_stage1_preobservation.md`
- `GPU_RUNclaude1/analyses/C0001_implementation_notes.md`

**レビュー**:
- `GPU_RUNclaude1/reviews/C0001_independent_review.md`
- `GPU_RUNclaude1/reviews/C0001_partA_statistical_review.md`
- `GPU_RUNclaude1/reviews/C0001_statistical_review.md`（v1 対象、歴史記録）
- `GPU_RUNclaude1/reviews/C0001_reproducibility_audit.md`（v1 対象、歴史記録）
- `GPU_RUNclaude1/reviews/C0001_v2_reproducibility_audit.md`
- `GPU_RUNclaude1/reviews/C0001_v2.1_focused_audit.md`

**追試**:
- `GPU_RUNclaude1/replications/C0001_opportunity_census_replication.md`

**生データ（読み取り専用）**:
- `results/runs/gpu_runclaude1_c0001_b731cdd/{phase0,phase1,phase2,phase3}/`
  （§14 に列挙した既知の欠落を除く）
- `results/runs/gpu_run5_20260823_ddd267b0/phase3/{beam_groups.json,all_candidates.json,cells/}`
  （比較対象、GPU_RUN5 の公表値。C0001 はこれらを書き換えていない）

**状態**:
- `GPU_RUNclaude1/research_state.md`（§5b、§8、§8b、再開ポイント）

---

## 16. 次の仮説（Next hypotheses）

以下は `hypothesis_tree.md` へのルーティング候補として記録する（本レポートでは決定しない）。

1. **`could_not_evaluate` の決定論的再定義（C0002 の最有力候補）**: 本サイクルで verdict を
   左右した 9 件の `SymbolicEquivalenceTimeout` を、実時間ではなくノード数・演算回数などの
   決定論的予算で再定義し、事前登録の上で解決する。比較は 9 件のみで計算費用は無視できる。
   これは threshold を後から動かして本サイクルの結果を救済する行為ではなく、**新しい事前登録
   サイクル**として実行する（v2.1 named contingency 1 が指定する唯一の正規経路）。
2. **定数保存 CAS 等価判定**（v2.1 §1.3 M-ii、§18.1）: GRN コーパスを覆うノード予算と、それを
   許す計算上限のもとでの、定数を畳み込まない CAS レベルの等価判定。E0 のアフィン分解機構に
   初めて計測手段を与える。
3. **`lp_sel` の修正**（CRITICAL-R3）: `lp_best` / `sb_best` を使うか、`beam_type = "search"` で
   再デコードして、C0002 の決定エンドポイント C2-P が実際に search error を測れるようにする。
   C0001 のまま凍結してはならない。
4. **候補生成器そのものの調査**: 本サイクルの net の内容はマッチャではなく生成器についてである。
   PC4 は正しい書き換え形が存在すれば指標が発火することを示した。ビームが一度もその形を提案
   しなかった理由（事前確率質量 E2 か探索誤差 E3 か）を、修正済みの `lp_sel` で切り分ける
   実験が C0002 以降の優先候補になる。
5. **Part D（ODEBench 変数分母候補の分母次数分類）**、**A2-S7**（`component_exact_loss = 0.0`
   の床効果が介入下で本物かの検証）は既に `hypothesis_tree.md` へルーティング済み（v2.1 §16, §18.2）。

---

## 17. `human_review_priority`

**優先度: 高（HIGH）**。理由:

1. 主エンドポイントの verdict of record が `undecidable` であり、`.claude/rules/09-human-intervention-policy.md`
   のハードストップには該当しないが、独立レビューが `REPLICATE`（ブロッキング）を勧告した
   高影響所見（CRITICAL-R1〜R3）を含む。
2. 本サイクル内で supervisor 自身の分析に **7 件の撤回**が生じており（§9 参照）、null 型の
   主エンドポイントと同じ誤り方向を持つ（rule R5）。人間による定期点検の対象として明示する。
3. `research_state.md` §5b に記録されたアカウント権限の制約（`organizationRole: user`、
   `team_labs_standard` シート）は、`organizationRole` の変更が必要な場合
   Nakamura Lab 管理者の操作を要する（`human_review_queue.md` HRQ-0008、未解決）。
4. C0002 の設計判断（`could_not_evaluate` の決定論的再定義、`lp_sel` の修正）は、事前登録前に
   人間の確認を経ることが望ましい。ただし通常の科学的判断であり、停止条件ではない
   （`.claude/rules/09-human-intervention-policy.md` の「通常の科学的代替案では停止しない」原則
   に従い、supervisor は事前登録草案の作成を自律的に継続する）。

`GPU_RUNclaude1/human_review_queue.md` への追記は本レポートとは別ステージ（Stage 13 以降）で
supervisor が行う。
