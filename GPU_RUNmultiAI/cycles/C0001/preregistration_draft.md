# C0001 事前登録ドラフト — メトリック同定可能性監査

- campaign: GPU_RUNmultiAI
- cycle: C0001
- task: C0001-T004
- audit_id: `c0001_metric_identifiability_audit_v1`
- 作成日: 2026-09-12
- 状態: **draft（未凍結）**
- binding_plan: null（凍結後に `research_state.md` へ記録）

本書は `.agent/rules/04-preregistration-and-metric-freeze.md` の全フィールドを
**メトリック監査** 向けに具体化したドラフトである。
GPU_RUN5 の sealed test 生成果物は読まない。GPU_RUN5 の結論を再解釈しない。

---

## 1. 主仮説（primary hypothesis）

**H0001-METRIC**:
ODEFormer 推論プロトコル（`rescale=true`）における
`Scaler.rescale_function` → `simplify_tree` → `formula_metrics(skip_cas=True)` →
`classify_formula` の連鎖は、代数的に真の Hill 型 GRN 成分と同値な候補に対し、
構造的完全一致（`canonical_exact`, `exponent_aware_skeleton_exact`）および
`hill_form=true` を系統的に拒否する（偽陰性を生む）。

**帰無仮説（監査用）**:
上記連鎖は、監査セット内の代数的同値 Hill ペアに対し、
事前定義された偽陰性率上限を超えない。

---

## 2. 一次エンドポイントと統計単位

### 2.1 一次エンドポイント（confirmatory）

| 順位 | エンドポイント | 定義 |
|---|---|---|
| 1 | `hill_false_negative_rate` | 代数的同値かつ真値が `hill_form=true` のペアのうち、
  予測側が `hill_form=false` となる割合 |
| 2 | `skeleton_false_negative_rate` | 同値ペアのうち `exponent_aware_skeleton_exact=0` となる割合 |
| 3 | `canonical_false_negative_rate` | 同値ペアのうち `canonical_exact=0` となる割合 |

**主要判定**: 3 指標のいずれかが偽陰性率 > 0 かつ事前ゲート（12 節）を満たす → H0001 supported。

### 2.2 共変量 endpoint（説明用、一次判定には含めない）

- `ted_raw`, `normalized_variable_aware_ted`
- `simplify_tree_timeout_rate`
- `rescale_silent_skip_rate`（`len(nodes)>len(scale)` 等の分岐）

### 2.3 感度分析 endpoint（co-primary ではない）

| 分析 | 条件 | 目的 |
|---|---|---|
| CAS 救済 | `compare_formulas(..., skip_cas=False)` | `skip_cas=True` が偽陰性を固定化しているか |
| 無リスケール | `rescale=false` で同一ペア | リスケーリングの主因性 |
| 真値パースのみ | 予測を真値文字列と同一にし指標のみ評価 | 指標単体の健全性 |

### 2.4 統計単位

- **主単位**: 監査ペア $`(f_{\mathrm{true}}, f_{\mathrm{pred}})`$。
  各ペアは rescale パラメータ集合 $`(\mathbf{s}, a_t, b_t)`$ と GRN 族 ID で条件付けされる。
- **集計単位**: 条件（族 × 指数 × scale ビン）ごとのペア集合。
- **報告**: ペア単位の成否表 + 条件別率 + 全体率（単純平均と重み付き平均を併記）。

### 2.5 統計推論

- 本監査は **決定論的生成** が主；確率推論は補助。
- 条件内 $`n \geq 5`$ のときのみ条件別 95% 区間を報告（Clopper–Pearson または Wilson）。
- $`n < 5`$ の条件は探索的とラベルし、一般化しない。

---

## 3. データセットと分割

### 3.1 監査データ（合成・コード生成）

| セット ID | 内容 | 単位数（目安） | 用途 |
|---|---|---|---|
| S1 | GRN canonical 真式（`src/gpu_run5/grn.py` から生成）× ランダム物理パラメータ | 8 族 × 3 指数 × 10 パラメータ = 240 | 主監査 |
| S2 | 代数同値変形ペア（分子分母の共通因子倍） | S1 各成分に 1 変形 = 240 | 主監査 |
| S3 | 線形成分のみ（`_decay`） | 8 族 × 10 = 80 | 対照（形状不変の期待） |
| S4 | 意図的非同値ペア | 100 | 負対照 |
| S5 | 固定探索例の再現 | 1（PI hand check ペア） | 探索的再現のみ（12 節） |

### 3.2 rescale パラメータスイープ

- `traj_scale`（= 初期状態 $`x(t_0)`$）: $\{0.1, 0.5, 1.0, 2.0, 5.0\}$（各次元独立、GRN 生成範囲 `[0.05, 2.5]` 内）
- 時間変換: GPU_RUN5 既定 `time_range=[1,10]`, `t_span=[0,10]` に合わせた `a_t, b_t`
- **データリークなし**: 全ペアは合成。train/val/test 分割は不要。
  ただし S5 は confirmatory 集計から **除外**。

### 3.3 禁止データ

- `results/runs/gpu_run5_*` の sealed test 生 JSON／CSV
- GPU_RUN5 の問題単位の実予測式（監査後の再評価は別サイクル）

---

## 4. チェックポイントとモデル

| 項目 | 値 |
|---|---|
| モデル | 公開 ODEFormer（4 encoder + 12 decoder, ~61M） |
| checkpoint | `assets/odeformer/weights/odeformer.pt` |
| SHA256 | `56754040be5aa92ed4767fc43ee2008faa293f87c12b643e66c7df3e1623a5e8` |
| 実行パッケージ | `third_party/odeformer/` |
| 本監査でのモデル推論 | **必須ではない**（Scaler 往復は決定論的に再現可能） |
| モデル推論を含む条件 | オプション ablation: 実 decode 1 軌道 → rescale 連鎖（計算上限内） |

監査の核心は **評価パイプライン** であり、学習済み重みの再学習は行わない。

---

## 5. ベースラインと ablation

| 条件 ID | 説明 |
|---|---|
| B0 | 完全パイプライン: `rescale_function` → `simplify_tree` → `formula_metrics(skip_cas=True)` |
| B1 | `rescale=false`（逆スケール省略） |
| B2 | `simplify_tree` 省略（rescale のみ） |
| B3 | `skip_cas=False`（CAS／数値同値救済あり） |
| B4 | 指標のみ（真値 infix を pred にコピー；パース・構造フラグの健全性） |
| B5 | 真値同値ペアで文字列完全一致（upper bound = 0% 偽陰性） |

**比較の公平性**: 全条件で同一ペア集合・同一 `formula_metrics` 実装コミットを使用。

---

## 6. シード

| 用途 | シード | 固定値 |
|---|---|---|
| GRN パラメータサンプリング | `audit_data_seed` | 61001 |
| `traj_scale` サンプリング（S1 追加変動） | `audit_scale_seed` | 61002 |
| オプション decode | `audit_decode_seed` | 61003 |

シードは監査 manifest に記録。再実行時は同一シードで同一ペア集合を再現する。

---

## 7. 探索・学習・デコードバジェット

| 項目 | 上限 |
|---|---|
| 学習 | **0**（本監査では学習しない） |
| GPU 推論（オプション ablation） | ≤ 10 軌道 × 1 checkpoint |
| beam（オプション時） | `beam_size=50`, `beam_temperature=0.1`, `beam_type=sampling`（GPU_RUN5 既定） |
| CPU 監査 | 全ペア往復 ≤ 10,000 評価呼び出し |
| CAS 感度分析 | 同値ペアのみ（最大 500 ペア） |

---

## 8. 演算子・式制約

- 真値生成: `src/gpu_run5/grn.py` の prefix 規則（Hill 活性／抑制／線形減衰）。
- 指数: $\{1, 2, 4\}$（GPU_RUN5 既定）。
- 変数: $`x_0, x_1, x_2`$（族の次元に応じる）。
- 禁止演算子（本監査の主セット）: 超越関数（GRN 生成に含まれない）。
- 同値変形: 有理式の分子・分母への非ゼロ定数倍、および $`k^n`$ 項の再パラメータ化。
  sympy `simplify(expand=True)` で同値を事前検証し、同値でないペアは S4 へ。

---

## 9. 除外と失敗ポリシー

### 9.1 除外

- パース不能な真値／予測値（`valid=false`）は **偽陰性率の分子に入れない**。
  別途 `parse_failure_rate` として報告。
- S5（PI 探索ペア）は confirmatory 集計から除外。

### 9.2 失敗の扱い

- `simplify_tree` timeout: 失敗を握り潰さず、**timeout フラグを記録**（現行 `except: pass` の監査版）。
- `rescale_function` 無音スキップ: スキップ発生を記録し、該当ペアは `rescale_incomplete` ラベル。
- NaN/Inf: `valid=false`, 理由を保存。
- **中央値からの除外禁止**: 失敗ペアを集計から黙って除かない。

---

## 10. 支持／不支持／判定不能基準

| 判定 | 条件 |
|---|---|
| **H0001 supported** | B0 で S2 の `hill_false_negative_rate > 0`、かつ
  S3（線形成分）では偽陰性率 = 0（または事前定義の低率）、かつ
  B4（指標のみ）では偽陰性率 = 0 |
| **H0001 unsupported** | B0 で S2 の全偽陰性率 = 0、かつ B5 も 0 |
| **H0001 undecidable** | パース失敗率 > 10%、または `rescale_incomplete` > 5%、
  または実装エラーでペアの 50% 以上が評価不能 |
| **部分支持** | Hill 偽陰性のみ > 0 で skeleton/canonical は 0 → 報告するが
  「Hill フラグ限定の問題」とラベル |

**競合仮説**: H0001 unsupported でも H0002–H0010 は自動棄却されない。
supported の場合のみ、それらの優先度を下げる。

---

## 11. Go/No-Go ゲート（監査完了判定）

| Gate | 条件 | 結果 |
|---|---|---|
| G1 実行完全性 | ≥ 95% の登録ペアが B0–B4 で評価完了 | 未達 → 監査 incomplete |
| G2 再現性 | 同一 commit・シードで S5 探索ペアの指標が hand check と一致 | 未達 → 実装バグ疑い |
| G3 主結果 | S2 の `hill_false_negative_rate` と 95% CI の下限 | 下限 > 0 → metric bug 確定（supported） |
| G4 封鎖 | 本ゲート通過前に GPU_RUN5 sealed test を再評価しない | 違反 → サイクル invalid |

**No-Go（修正サイクルへ）**: G1 未達、または G2 不一致。

---

## 12. 計算上限

| リソース | 上限 |
|---|---|
| GPU 時間 | ≤ 2 GPU-hours（オプション decode のみ） |
| CPU 時間 | ≤ 4 CPU-hours |
| ディスク | ≤ 1 GB（監査 JSON/CSV） |
| 人間レビュー | 凍結前 Opus/statistical-reviewer 1 回 |

---

## 13. 必須成果物

| 成果物 | 内容 |
|---|---|
| `audit_manifest.json` | commit, シード, checkpoint SHA256, ペア定義ハッシュ |
| `pair_results.csv` | ペア ID, 条件, 全 endpoint, 失敗理由, B0–B5 フラグ |
| `condition_summary.json` | 条件別偽陰性率と CI |
| `rescale_trace/` | 代表ペアの prefix 木（往復前後） |
| `exploratory_S5.json` | PI hand check 再現（confirmatory 外） |
| `deviation_log.md` | 凍結後の変更があれば記録 |

図表は必要なら `graphs/c0001_metric_audit/`（本タスクでは生成しない）。

---

## 14. 探索的観察との区別（必須）

| 項目 | 探索的（既存） | 本 confirmatory 監査 |
|---|---|---|
| 出典 | PI hand check（C0001-T003 報告） | 本 preregistration 凍結後 |
| ペア | `2*x_0**2/(1+x_0**2)` vs `4*x_0**2/(2+2*x_0**2)`（成分抜粋） | S1–S4 の事前登録集合 |
| Scaler 往復 | **未実施** | B0 で必須 |
| 結論の用途 | 仮説生成のみ | H0001 の支持／不支持判定 |
| 昇格条件 | なし（自動昇格禁止） | G1–G3 を満たすこと |

探索的観察の結果は、confirmatory 結果に **混ぜて報告しない**。

---

## 15. 競合仮説の扱い

`hypothesis_review.md` の H0002–H0010 は本サイクルでは検証しない。
H0001 の結果は次を決める:

- **supported** → 指標修正サイクル（実装タスク）を優先。生成／層仮説は保留。
- **unsupported** → H0004（多 IC）または H0003（beam 多様性）を次サイクル候補に昇格。

---

## 16. 凍結前レビューで攻撃すべき点（T003 継承）

1. S2 の同値変形が「生物学的に意味のある」か、それとも人工的か。
2. B3 の CAS コストと、本番 `skip_cas=True` 固定の妥当性。
3. `hill_form` を一次 endpoint に含めることの保守性（skeleton のみでも十分か）。
4. 線形対照 S3 が H0001 の機構予測（Hill のみ偽陰性）を試す十分性。
5. オプション decode の有無が結論を変えないことの事前コミット。

---

## 17. 逸脱ポリシー

凍結後の変更は `deviation_log.md` に記録する。
最終結果を見てからペア集合・endpoint・ゲートを変えた場合、
当該監査は **exploratory** に降格し、新サイクルで再 preregister する。

---

## 18. 承認チェックリスト（凍結時に埋める）

| フィールド | 本ドラフト | 凍結時記入 |
|---|---|---|
| primary hypothesis | H0001-METRIC | |
| primary endpoint | 2.1 節 3 率 | |
| statistical unit | ペア | |
| datasets | S1–S5 | |
| checkpoints | ODEFormer pt（監査参照） | |
| baselines/ablations | B0–B5 | |
| seeds | 6 節 | |
| budgets | 7 節 | |
| operator constraints | 8 節 | |
| failure policy | 9 節 | |
| support criteria | 10 節 | |
| Go/No-Go | 11 節 | |
| compute ceiling | 12 節 | |
| required artifacts | 13 節 | |
| reviewer sign-off | 未 | statistical-reviewer / scientific-critic |
| frozen_on | 未 | ISO 日付 |
| binding_plan path | 未 | 凍結版へのパス |

---

## 19. 関連ドキュメント

- `scientific_state.md` — 観測事実と推論の分離
- `hypothesis_review.md` — 競合仮説と H0001 選択理由
- `literature_evidence.md` — 文献根拠
- `.agent/rules/04-preregistration-and-metric-freeze.md` — 凍結要件の正本
