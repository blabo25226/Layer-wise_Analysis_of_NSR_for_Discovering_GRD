# C0001 競合仮説レビュー

- cycle: C0001
- task: C0001-T004
- role: research-engineer
- branch: `ai/C0001/research-engineer/preregister-metric-audit`
- 作成日: 2026-09-12
- 状態: draft（凍結前）

本書は C0001-T002（7 候補生成）、C0001-T003（批判レビュー）、および上流 PI 決定
（H0001-METRIC 優先）を統合した競合仮説レビューである。
`scientific_state.md` の観測事実と分離し、各候補に falsifier と情報利得／コストを付す。

## 選択サマリー

| 順位 | ID | 短名 | 情報利得／コスト | 本サイクル |
|---|---|---|---|---|
| 1（選択） | H0001 | メトリック／リスケーリング偽陰性 | 高／低 | **主監査** |
| 2 | H0004 | 多 IC カバレッジ | 中／中 | 保留（説明分離用） |
| 3 | H0002 | クリティカルトークン確率 | 中／高 | 保留 |
| 4 | H0003 | マッチドバジェットサンプリング多様性 | 中／中 | 保留 |
| 5 | H0005 | 構造重み付き損失 | 中／高 | 保留 |
| 6 | H0006 | 更新量 vs 層同一性 | 中／高 | 保留 |
| 7 | H0007 | 層相互作用 | 中／高 | 保留 |
| 8 | H0008 | 真値非依存文法 | 低〜中／中 | 保留 |
| 9 | H0009 | アテンションルーティング | 低〜中／高 | 保留 |
| 10 | H0010 | 埋め込みドリフト | 低／高 | 保留 |

**選択理由（H0001）**: GPU_RUN5 の公開結論「R03–R08 の非自明構造で exact 回復ゼロ」は、
モデル生成失敗だけでなく **評価指標の構造非不変性欠如** でも説明可能である。
ソース直読（`rescale_function` → `simplify_tree` → `formula_metrics(skip_cas=True)` →
`_strict_hill_denominator`）により、偽陰性経路が具体的に特定でき、
追加 GPU 学習なしの **決定論的監査** で falsify／support できる。
情報利得が高く、計算コストが rivals より低い。

---

## H0001 — メトリック／リスケーリング偽陰性（選択）

- **Falsifiable statement**:
  ODEFormer 推論の `rescale=true` 経路（`Scaler.rescale_function` + `simplify_tree`）の後、
  代数的に真の Hill 型 GRN 式と同値な候補に対し、
  `formula_metrics(..., skip_cas=True)` が `canonical_exact=0`、
  `exponent_aware_skeleton_exact=0`、`hill_form=false` を返す。
- **Existing authorized evidence**:
  - `scientific_state.md` 1.1–1.6 のソース直読。
  - GPU_RUN5 公開レポート: R03–R08 で非自明構造の exact 回復ゼロ。
  - PI 探索的チェック（非 confirmatory）: `2*x_0**2/(1+x_0**2)` と
    `4*x_0**2/(2+2*x_0**2)` で `canonical_exact=0`, `hill_form=false`。
    **Scaler 実経路は未検証**。
- **Competing explanations**: H0002–H0010（本書以下）。
- **Falsifier**:
  監査で (i) Scaler 往復後の代数的同値 Hill ペアに対し `canonical_exact=1` または
  `exponent_aware_skeleton_exact=1` が得られる、または
  (ii) `rescale=false` でも同じ偽陰性が生じ、リスケーリングが主因でない。
- **Expected information gain**: 高。
  GPU_RUN5 の構造回復ゼロが「モデル限界」か「指標 artifact」かを分離できる。
- **Compute/engineering cost**: 低（CPU の決定論的往復＋既存 `formula_metrics` 呼び出し）。
- **If supported**: 構造 endpoint の再解釈が必要。指標修正または CAS 救済の設計変更が正当化される。
  **GPU_RUN5 sealed test の再評価は別サイクル**。
- **If unsupported**: リスケーリング仮説は棄却。生成／選択／学習側（H0002–H0007）の優先度が上がる。
- **What a negative result teaches**: 評価パイプラインは Hill 同値性に対して想定より robust。
  偽陰性は別経路（beam 多様性不足、FT 忘却、層選択ミスマッチ等）を疑う。
- **Novelty status**: 実装詳細の組み合わせ起因の仮説。文献は rescaling の一般論と
  構造距離の限界を別々に述べるが、本リポジトリ固有の連鎖は未検証。
- **Unverified assumptions**: `scientific_state.md` 4 節 A1–A5。
- **Dependencies**: `third_party/odeformer` の Scaler、`src/gpu_run5/evaluation.py`、
  `src/evaluation/gpu_run5_structure.py`。
- **Status**: selected for C0001 preregistration

---

## H0002 — クリティカルトークン確率（DecoderLens）

- **Falsifiable statement**:
  Hill 分母トークン（`inv`, `add`, `pow` 連鎖）の teacher-forcing 順位が浅い decoder 層で
  既に低く、構造回復失敗は decode 時の早期分岐ミスに起因する。
- **Existing authorized evidence**:
  GPU_RUN5 層解析: teacher-forcing CE 順位と介入後 TED 順位の Spearman $`\rho \approx 0.009`$。
  変数分母構造は beam 内に稀（56 cell 中 0 件の exact 選択）。
- **Competing explanations**: H0001（指標偽陰性）、H0003（beam 多様性）、H0004（単一 IC 代替式）。
- **Falsifier**: 真構造が beam 内に存在し指標が正しく exact=1 を返すのに選択で落ちる、
  または critical token の順位が高いにも構造不一致。
- **Expected information gain**: 中（生成 vs 選択の分離）。
- **Compute/engineering cost**: 高（層介入・logit 解析の再実行）。
- **If supported**: decode 改善（guided sampling、層別 intervention）が主戦略。
- **If unsupported**: 生成段階で真構造がそもそも出ていない。
- **What a negative result teaches**: CE 順位は構造回復の代理にならない（既に GPU_RUN5 で示唆）。
- **Novelty status**: 既存 run で部分検証済み。
- **Status**: open, deferred

---

## H0003 — マッチドバジェットサンプリング多様性

- **Falsifiable statement**:
  `beam_size=50`, `beam_temperature=0.1` の sampling beam は、
  同予算の多様性最大化と比べて Hill 型分母構造の候補を beam 内に十分含めない。
- **Existing authorized evidence**:
  GPU_RUN5: 変数分母の真構造は beam 内 0 件（R5）。
  `configs/gpu_run5/base.yaml` の固定 beam 設定。
- **Competing explanations**: H0001（beam に入っても指標が落とす）、H0002（token 順位）。
- **Falsifier**: 多様性強化 beam で Hill 構造が増えるが exact は依然 0（H0001 支持）、
  または現 beam でも構造は存在し指標のみ失敗。
- **Expected information gain**: 中。
- **Compute/engineering cost**: 中（matched-budget decode 再実行）。
- **If supported**: beam 設計変更が先決。
- **If unsupported**: 多様性は十分、モデル表現／指標がボトルネック。
- **Status**: open, deferred

---

## H0004 — 多 IC カバレッジ

- **Falsifiable statement**:
  単一初期条件・単一軌道では観測適合の代替式が残り、
  多 IC 選択でも構造 exact は改善しない（真構造が生成されないか指標で落ちる）。
- **Existing authorized evidence**:
  GPU_RUN5 P6 支持: 多 IC は generalization error を改善（CI95 上限 < 0）。
  しかし構造 exact 回復は R03–R08 でゼロ。
- **Competing explanations**: H0001（正しい式が選ばれても指標が 0）、H0003（beam 不足）。
- **Falsifier**: 多 IC で正しい Hill 式が選ばれ指標も exact=1（H0001 棄却方向）。
- **Expected information gain**: 中（selection vs metric の分離）。
- **Compute/engineering cost**: 中。
- **If supported**: IC 数だけでは構造同定は解けない。
- **If unsupported**: 選択が主因、指標は無罪。
- **Status**: open, deferred; **H0001 監査後に再優先**

---

## H0005 — 構造重み付き損失

- **Falsifiable statement**:
  GRN fine-tuning で構造フラグ重み付き損失を使えば、
  通常 CE より Hill 分母構造の生成確率が上がる。
- **Existing authorized evidence**:
  GPU_RUN5 は CE ベース FT。構造重みは未実装。
  全層 FT が formula score 最良だが exact はゼロ。
- **Competing explanations**: H0001（学習後も指標が偽陰性）、H0006–H0007（層選択）。
- **Falsifier**: 構造損失で beam 内 Hill 構造が増え、かつ `formula_metrics` が exact=1。
- **Expected information gain**: 中。
- **Compute/engineering cost**: 高（新損失＋再学習）。
- **Status**: open, deferred

---

## H0006 — 更新量 vs 層同一性

- **Falsifiable statement**:
  formula-level IOLE で見える「重要層」は勾配ノルム順位と一致し、
  top 3 層 FT の式回復劣化は更新量不足ではなく層選択の問題ではない。
- **Existing authorized evidence**:
  GPU_RUN5: top 3 は valid rate と数値再構成は良いが formula score で full に劣る。
  CE と TED の層順位不一致。
- **Competing explanations**: H0007（層相互作用）、H0001（指標）。
- **Falsifier**: 更新量を揃えた層 ablation で full と同等の構造回復。
- **Expected information gain**: 中。
- **Compute/engineering cost**: 高。
- **Status**: open, deferred

---

## H0007 — 層相互作用

- **Falsifiable statement**:
  単層 IOLE の効果は多層同時更新の相乗を捉えられず、
  top 3 選択は相互作用を欠いた部分最適である。
- **Existing authorized evidence**:
  GPU_RUN5 層解析レポート（P5 miss、P7 miss）。
- **Competing explanations**: H0006、H0001。
- **Falsifier**: 相互作用を明示した層集合が構造 exact を改善。
- **Expected information gain**: 中。
- **Compute/engineering cost**: 高。
- **Status**: open, deferred

---

## H0008 — 真値非依存文法

- **Falsifiable statement**:
  ODEFormer の出力文法（prefix 演算子集合）が Hill 型分母を表現可能でも、
  学習分布のバイアスにより `inv(add(const, pow))` 形が低確率である。
- **Existing authorized evidence**:
  ODEFormer は変数分母候補を生成（R4 支持）が exact 選択 0（R5）。
- **Competing explanations**: H0001（表現はあるが指標が落とす）、H0003。
- **Falsifier**: 文法制約を外しても（または oracle 文法で）指標が偽陰性のまま。
- **Expected information gain**: 低〜中。
- **Compute/engineering cost**: 中。
- **Status**: open, deferred

---

## H0009 — アテンションルーティング

- **Falsifiable statement**:
  encoder–decoder attention が時系列のスケール不変特徴を捉えられず、
  rescale 後の軌道から分母構造を復元できない。
- **Existing authorized evidence**:
  間接的（GPU_RUN5 数値再構成は可能、構造は不可）。
  **attention map の系統解析は本ワークツリー未確認**。
- **Competing explanations**: H0001（デコード後指標）、H0010。
- **Falsifier**: attention 介入で Hill 構造生成率が上がり指標も pass。
- **Expected information gain**: 低〜中。
- **Compute/engineering cost**: 高。
- **Status**: open, deferred; attention 主張は **未検証** と明記

---

## H0010 — 埋め込みドリフト

- **Falsifiable statement**:
  GRN fine-tuning による埋め込み空間のドリフトが、
  事前学習で学んだ有理式構造のデコードを破壊する。
- **Existing authorized evidence**:
  GPU_RUN5: top 3 FT は ODEBench forgetting を抑えるが formula recovery は full に劣る。
- **Competing explanations**: H0005–H0007、H0001。
- **Falsifier**: 埋め込みを frozen しても構造 exact が改善しない、または
  ドリフト指標と構造回復の相関がない。
- **Expected information gain**: 低（忘却とは独立の軸）。
- **Compute/engineering cost**: 高。
- **Status**: open, deferred

---

## T003 批判レビューからの横断指摘（監査設計へ反映）

| 指摘 | 重大度 | 本ドラフトでの対応 |
|---|---|---|
| 探索的 hand check を confirmatory と混同しない | 高 | `preregistration_draft.md` 15 節で分離 |
| `skip_cas=True` が偽陰性を固定化 | 高 | 監査の co-primary: `skip_cas=False` 感度分析 |
| sealed test 再解釈の禁止 | 高 | A6 制約を維持 |
| 線形成分対照の欠如 | 中 | 正負対照ペアを事前登録 |
| `simplify_tree` 無音失敗 | 中 | timeout 発火率を成果物に記録 |
| 単一ペアでの一般化 | 中 | パラメータスイープと GRN canonical 形を単位に |

## 次アクション

1. `preregistration_draft.md` の凍結レビュー（statistical-reviewer / scientific-critic）。
2. 凍結後、実装・テストは Cursor へ委譲（本タスクの write scope 外）。
3. `GPU_RUNmultiAI/hypothesis_tree.md` の更新は親セッションが行う（本タスク外）。
