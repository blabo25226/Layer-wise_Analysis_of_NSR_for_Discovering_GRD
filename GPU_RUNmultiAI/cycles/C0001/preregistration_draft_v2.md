# C0001 事前登録 v2 — メトリック同定可能性監査

- campaign: GPU_RUNmultiAI
- cycle: C0001
- task: C0001-T005
- audit_id: `c0001_metric_identifiability_audit_v2`
- supersedes: `preregistration_draft.md`（v1、未凍結・参照のみ）
- 作成日: 2026-09-13
- 状態: **draft v2（未凍結）**
- binding_plan: null（凍結後に `research_state.md` へ記録）

本書は `.agent/rules/04-preregistration-and-metric-freeze.md` の全フィールドを
**メトリック監査** 向けに具体化した改訂ドラフトである。
独立レビュー（`preregistration_independent_review.md`）の C1–C3 / M1–M7 をすべて閉じる。
GPU_RUN5 の sealed test 生成果物は読まない。GPU_RUN5 の結論を再解釈しない。
**本監査は decode を含まない**（CPU の決定論的 Scaler 往復のみ）。

---

## 0. 科学的クレームの校正（M1）

**主張の範囲**:
- 本監査が検証するのは、評価連鎖が **代数的同値な Hill 表現に対して非不変** であること、
  および **Hill 分類の系統的 undercounting** のみである。
- `canonical_exact` / `exponent_aware_skeleton_exact` は **構文木・正規化表現** の一致指標であり、
  一般代数同値性の oracle ではない。これらの syntactic 指標が意図通りに機能していること自体は、
  本監査の棄却対象ではない。
- GPU_RUN5 等の **過去 syntactic exact 結果を一括無効化しない**。
  本監査が支持されても「モデルが式を生成できなかった」とは言わず、
  「同値 Hill 候補が構造指標で偽陰性化される」に限定する。
- Hill 分類（`hill_form`）と exact-tree / skeleton 回復は **別 endpoint** として報告する。

---

## 1. 主仮説（primary hypothesis）

**H0001-METRIC（校正版）**:
ODEFormer 推論プロトコルに対応する決定論的監査連鎖
（全成分 ordered system 上の forward scaling → `Scaler.rescale_function` → `simplify_tree` →
`formula_metrics(skip_cas=True)`）は、独立 equivalence oracle で **E2 段階が真値と同値** と確認された
Hill 型成分に対し、`hill_form=false` を系統的に返す（偽陰性を生む）。

**帰無仮説（監査用）**:
登録 oracle-eligible Hill ペア集合において、
E2 同値かつ `hill_form=false` となる **非自明例が 1 件も存在しない**。

---

## 2. 一次エンドポイントと統計単位（M2, C3, M4）

### 2.1 一次エンドポイント（confirmatory、唯一）

| 項目 | 定義 |
|---|---|
| **Primary endpoint** | `hill_false_negative_rate` |
| **分子** | oracle-eligible Hill ペアのうち、E2 候補が独立 oracle で真値と同値、かつ `hill_form=false` |
| **分母** | **登録された oracle-eligible Hill ペア全件**（failure-aware；C3） |
| **Failure として分子に計上** | 予測側 E2 の parse 失敗、timeout、NaN/Inf、`rescale_incomplete`、評価不能 |
| **Primary decision rule** | 分母集合内に **≥ 1 件** の Hill 偽陰性が存在 → **H0001 supported** |

本監査は決定論的生成器であるため、一次判定に **信頼区間を付さない**（存在証明）。
率そのものは報告するが、Go/No-Go の primary gate は上記存在規則のみ。

### 2.2 統計単位（C2）

| レベル | 定義 |
|---|---|
| **Primary sampling unit** | パラメータ化 GRN **系**（240 系） |
| **Within-system replicate** | 系内 **成分**（510 成分；Hill 390 + 線形 120） |
| **Confirmatory pair** | $`(f_{\mathrm{true}}, f_{\mathrm{pred,E2}})`$ を **固定成分 ID** でスコア |

forward / reverse scaling は **全成分 ordered system** 上で実行し、
`rescale_function` の NodeList 位置依存スケール（単独成分への誤適用）を回避する（C1, C2）。

### 2.3 二次 endpoint（conditional 命名必須）

| 名称 | 定義 | 用途 |
|---|---|---|
| `hill_false_negative_rate_valid_pairs_only` | 分母 = E2 が valid かつ oracle 同値の Hill ペアのみ | **secondary**；primary 判定に不使用 |
| `skeleton_false_negative_rate` | E2 同値ペアで `exponent_aware_skeleton_exact=0` | 説明用 |
| `canonical_false_negative_rate` | E2 同値ペアで `canonical_exact=0` | 説明用 |
| `simplifier_semantic_drift_rate` | E1 は oracle 同値だが E2 は非同値 | simplifier 起因の別経路（C1） |
| `hill_false_positive_rate` | 非 Hill 真値（線形 120 成分）で `hill_form=true` | M4 診断 |
| `linear_canonical_invariance_rate` | 線形 120 成分で `canonical_exact=0` | 形状不変対照 |

### 2.4 記述統計（primary gate に含めない）

- 族 × 指数 × scale ビン別の偽陰性率
- stress scale `5.0` 条件の率
- `ted_raw`, `normalized_variable_aware_ted`

---

## 3. E0 / E1 / E2 パイプラインと独立 oracle（C1）

### 3.1 記法

- 物理変数 $`x_j`$、scaled 変数 $`z_j = s_j x_j`$（$`s_j = \mathrm{feature\_scale}/\mathrm{traj\_scale}_j`$）
- 時間 $`t`$、scaled 時間 $`\tau = a_t t + b_t`$
- 系 $`i`$ の成分 $`f_i(x)`$（unscaled prefix 真値）

### 3.2 Forward scaling（E0）

全成分 ordered system に対し、成分 $`i`$ の valid scaled-space 候補:

```math
g_i(z)=\frac{s_i}{a_t}\, f_i\!\left(\frac{z_1}{s_1},\ldots,\frac{z_d}{s_d}\right)
```

**E0** = 上式を exact rational 構築で得た **full-system** prefix 候補（単独成分 tree への部分適用禁止）。

### 3.3 実装 rescaling（E1）

**E1** = `Scaler.rescale_function(env, E0_tree, a_t, b_t, scale)` の出力
（production `third_party/odeformer/odeformer/model/utils_wrapper.py` と同一 API）。

### 3.4 Simplifier（E2）

**E2** = `env.simplifier.simplify_tree(E1)` の出力
（production `sklearn_wrapper.py:166` と同じ `try/except` 記録版；握り潰し禁止）。

### 3.5 独立 equivalence oracle（C1）

E2 候補の eligibility は **監査対象 CAS とは独立** の oracle で判定する:

1. **Analytic**: sympy `simplify(expand=True)` による exact rational 同値（監査専用；`skip_cas=True` 本番経路とは分離）
2. **Numeric**: 決定論的固定点グリッド（各変数 $`\{0.01, 0.1, 0.5, 1.0, 2.0\}`$、$`d`$ 次元直積、$`t=0,5,10`$）で
   $|f_{\mathrm{true}}-f_{\mathrm{pred}}| < 10^{-8}$

**Primary structural false negative** の対象は **E2 が oracle 同値** の Hill ペアのみ。
E1 同値 / E2 非同値は `simplifier_semantic_drift` へ分離。

### 3.6 真値・oracle 構築失敗（C3）

真値 parse 失敗、E0 構築失敗、oracle 同値判定不能 → 当該ペアは **incomplete**。
incomplete 率 > 5% → 監査 **undecidable**（偽陰性と混同しない）。

---

## 4. データセットとコーパス（C2, M5）

### 4.1 凍結コーパス（一次 confirmatory）

| 集合 | 内容 | 系 | 成分 | Hill | 線形 |
|---|---|---:|---:|---:|---:|
| **C** | `src/gpu_run5/grn.py` から生成する canonical 真式 | 240 | 510 | 390 | 120 |

**240 系の内訳**: 8 族 × 3 Hill 指数 $`\{1,2,4\}`$ × 10 パラメータ draw（`audit_data_seed=61001`）。

**成分内訳（系あたり）**:

| 族 | 次元 | 成分数 | Hill | 線形 |
|---|---:|---:|---:|---:|
| R01, R02 | 1 | 1 | 1 | 0 |
| R03, R05 | 2 | 2 | 2 | 0 |
| R04 | 2 | 2 | 1 | 1 |
| R06 | 3 | 3 | 3 | 0 |
| R07 | 3 | 3 | 2 | 1 |
| R08 | 3 | 3 | 1 | 2 |

各 Hill 成分に **非自明代数同値 rewrite** を 1 本ずつ付与（分子・分母の非零有理数倍）。
rewrite も oracle で真値と同値であることを事前検証する。

### 4.2 Scale 設計（M5）

| 区分 | isotropic `traj_scale` 値 | 用途 |
|---|---|---|
| **Primary grid** | `{0.1, 0.5, 1.0, 2.0}` | confirmatory（生成 IC 範囲 `[0.05, 2.5]` 内） |
| **Stress label** | `{5.0}` | **記述のみ**；primary gate 不使用 |

- $`d`$ 次元系では `traj_scale = [s,\ldots,s]`、`scale = feature_scale / traj_scale`（isotropic）
- `feature_scale = 1` 固定
- 各成分 × primary grid 点 = 1 oracle-eligible ペア

**Primary confirmatory ペア数**:

| 分母集合 | 計算 | 件数 |
|---|---|---:|
| Hill oracle-eligible | 390 成分 × 4 scales | **1,560** |
| 線形 invariance control | 120 成分 × 4 scales | 480 |
| Stress（記述） | 390 × 1 | 390 |

### 4.3 負対照（secondary）

| 集合 | 内容 | 件数 |
|---|---|---:|
| N1 | 意図的非同値 rewrite | 100 |

N1 は primary endpoint 分母に **含めない**。

### 4.4 探索的再現（confirmatory 外）

| 集合 | 内容 |
|---|---|
| S5 | PI hand-check ペア `2*x_0**2/(1+x_0**2)` vs `4*x_0**2/(2+2*x_0**2)`（成分抜粋） |

S5 は primary corpus・decision gate に **混ぜない**（M7）。

### 4.5 データリークと sealed-path guard（M7）

**禁止読取パス**（実行時 assert）:

- `results/runs/gpu_run5_*/**/test/**`
- `results/runs/gpu_run5_*/**/sealed/**`
- GPU_RUN5 問題単位の実 decode 予測式 JSON/CSV

**許可**: 公開 README、本監査用合成生成、`src/`・`third_party/` ソース。

監査 manifest に `sealed_path_guard: enforced` と試行した glob を記録する。

---

## 5. Scaler 構築と runtime assert（M6）

本監査は production と同型の Scaler を **明示構築** する:

```python
Scaler(time_range=[1, 10], feature_scale=1)
```

`t_span=[0, 10]`、`MinMaxScaler` fit 後に **必ず assert して manifest へ保存**:

| フィールド | 期待値 |
|---|---|
| `time_scale` | 9 |
| `time_shift` | 1 |
| `a_t` | 0.9 |
| `b_t` | 1.0 |

assert 失敗 → 監査 **即 abort**（silent wrong-range Scaler 禁止）。

`SymbolicTransformerRegressor(params=None)` の暗黙 `[1,5]` デフォルトは **使用禁止**。

---

## 6. ベースラインと ablation（M3）

| 条件 | 説明 | スコア段 |
|---|---|---|
| **B0** | E0 → `rescale_function` → `simplify_tree` → `formula_metrics(skip_cas=True)` | **E2**（primary） |
| **B1** | identity scaler $`(a_t=1, b_t=0, scale=\mathbf{1})`$ で E0 を rescale → `simplify_tree` | E2（リスケール主因性対照） |
| **B2** | B0 と同じ生成だが **simplifier 省略** | **E1** |
| **B3** | B0 の E2 に対し `compare_formulas(..., skip_cas=False)` | 診断のみ |
| **B4** | 真値 infix を pred にコピーし指標のみ | 指標健全性 |

**禁止**:

- `rescale=false` で scaled 候補を unscaled 真値と比較（旧 B1；無効 counterfactual）
- B3 の CAS 結果を primary Hill endpoint の救済に使用
- 冗長な「文字列完全一致」baseline（旧 B5）

**線形 120 成分**は Hill FNR 分母に **含めない**（M4）。
線形は `linear_canonical_invariance_rate` 対照として評価する。

---

## 7. シードと決定論（M7）

| 用途 | シード | 値 |
|---|---|---|
| GRN パラメータ LHS | `audit_data_seed` | 61001 |
| Primary isotropic scale 割当 | `audit_scale_seed` | 61002 |
| 負対照 N1 選択 | `audit_negative_seed` | 61004 |
| B3 CAS 診断 subset | `audit_cas_subset_seed` | 61005 |

**系順序**: `FAMILIES` dict 順（R01→R08）。
**浮動小数**: `grn.py` と同じ `{:.4g}` 量子化。
**B3 subset**: Hill primary 1,560 ペアを `(pair_id)` の SHA256 昇順で並べ、先頭 500 件（result-independent）。

---

## 8. 計算上限と call-count 表（M5, CPU-only, no decode）

| 項目 | 上限 |
|---|---|
| GPU / decode | **0**（本 prereg では禁止） |
| CPU | ≤ 4 CPU-hours |
| 評価呼び出し | ≤ 10,000 |
| ディスク | ≤ 1 GB |

### 8.1 凍結 call-count 表

| 操作 | 条件 | 回数 |
|---|---|---:|
| Oracle 同値判定 | Hill+linear primary 2,040 ペア | 2,040 |
| B0 `formula_metrics` | 510 成分 × 4 primary scales | 2,040 |
| B1 identity scaler | 同上 | 2,040 |
| B2 E1-only | 同上 | 2,040 |
| B3 CAS diagnostic | hash-order 先頭 500 Hill ペア | 500 |
| B4 metrics-only | 510 × 4 | 2,040 |
| N1 負対照 | 固定 100 | 100 |
| Stress scale 記述 | 390 Hill × 1 | 390 |
| **合計** | | **11,190** |

**Ceiling 調整**: Stress 390 と B4 2,040 は **post-hoc 記述** tier とし、
confirmatory tier（Oracle + B0 + B1 + B2 + B3 + N1 = 2,040×4 + 500 + 100 = **8,260**）を
**hard ceiling** とする。実装は confirmatory tier を先に完了させ、
余裕があれば記述 tier を実行する。confirmatory tier 超過 → abort。

---

## 9. 除外・失敗ポリシー（C3）

| 事象 | 扱い |
|---|---|
| E2 parse 失敗 / timeout / NaN / Inf | **failure**（primary 分子） |
| `rescale_incomplete`（`len(nodes)>len(scale)` 等） | **failure** |
| Oracle 同値でない E2 | primary Hill FNR 対象外（別集計） |
| 真値・E0・oracle 構築失敗 | **incomplete**（分母から除外し incomplete 率を報告） |
| valid のみ率 | `*_valid_pairs_only` として **secondary** 命名 |

---

## 10. 支持／不支持／判定不能（M1, M2）

| 判定 | 条件 |
|---|---|
| **H0001 supported** | Primary: Hill oracle-eligible 1,560 ペアの `hill_false_negative_rate` に **≥1 件**、
  かつ線形 480 ペアで `hill_false_positive_rate = 0`、
  かつ `linear_canonical_invariance_rate = 0`、
  かつ incomplete ≤ 5% |
| **H0001 unsupported** | 上記 Hill 偽陰性 **0 件** かつ G1 完全性達成 |
| **H0001 undecidable** | incomplete > 5%、または confirmatory tier 未完了 |
| **部分所見** | skeleton/canonical のみ偽陰性 → 報告するが primary 判定は `hill_form` のみ |

**明示的に言わないこと**: 「GPU_RUN5 exact 回復ゼロの完全説明」「過去 syntactic exact 結果の無効化」。

---

## 11. Go/No-Go ゲート

| Gate | 条件 | 結果 |
|---|---|---|
| G0 Scaler assert | §5 の 4 値一致 | 失敗 → abort |
| G1 実行完全性 | confirmatory tier ≥ 95% 完了 | 未達 → incomplete |
| G2 再現性 | 同一 commit・seed で S5 が hand-check と一致 | 探索的；primary 非連動 |
| G3 Primary | §10 supported / unsupported | 存在規則のみ |
| G4 封鎖 | sealed-path guard 違反なし | 違反 → invalid |
| G5 記述 tier | Stress / B4 は primary 判定に不使用 | — |

---

## 12. 必須成果物と resume 規則（M7）

| 成果物 | 内容 |
|---|---|
| `audit_manifest.json` | commit, シード, Scaler assert, コーパス件数, source hashes, sealed-path guard |
| `pair_results.csv` | pair_id, system_id, component_idx, scale, E0/E1/E2 ステータス, 全 endpoint, 失敗理由 |
| `condition_summary.json` | 率（failure-aware 分母明示） |
| `equivalence_oracle.json` | ペアごとの analytic/numeric 判定 |
| `deviation_log.md` | 凍結後変更 |

**Overwrite / resume**:

- デフォルト `--fail-if-exists`: 出力ディレクトリに `audit_manifest.json` がある場合 **exit 1**
- `--resume`: 既存 `pair_results.csv` の `pair_id` をスキップし追記
- 部分 manifest の上書き禁止；resume は同一 `audit_id` のみ

---

## 13. 実行コマンドと provenance（M7）

### 13.1 環境

| 項目 | 凍結値 |
|---|---|
| Python | 3.10.x |
| `allow_cpu` | true（本監査） |
| OS / arch | manifest に記録 |

実行時に `pip freeze` または `python -m pip list --format=freeze` を保存する。

### 13.2 Source hashes（manifest 必須）

| ファイル | 用途 |
|---|---|
| `src/gpu_run5/grn.py` | 真値生成 |
| `third_party/odeformer/odeformer/model/utils_wrapper.py` | Scaler |
| `third_party/odeformer/odeformer/model/sklearn_wrapper.py` | 連鎖 |
| `third_party/odeformer/odeformer/envs/simplifiers.py` | simplify_tree |
| `src/gpu_run5/evaluation.py` | formula_metrics |
| `src/gpu_run4/formulas.py` | compare_formulas |
| `src/evaluation/gpu_run5_structure.py` | hill_form |

### 13.3 凍結コマンド（実装後）

```bash
python -m compileall -q src scripts tests
python scripts/phases/gpu_runmultiai_c0001_metric_audit.py \
  --audit-id c0001_metric_identifiability_audit_v2 \
  --output-dir GPU_RUNmultiAI/cycles/C0001/runs/c0001_metric_identifiability_audit_v2 \
  --audit-data-seed 61001 \
  --audit-scale-seed 61002 \
  --fail-if-exists
```

Resume:

```bash
python scripts/phases/gpu_runmultiai_c0001_metric_audit.py \
  --audit-id c0001_metric_identifiability_audit_v2 \
  --output-dir GPU_RUNmultiAI/cycles/C0001/runs/c0001_metric_identifiability_audit_v2 \
  --resume
```

（スクリプトは **本 prereg 凍結後の実装タスク** で追加する。本タスクでは実行しない。）

### 13.4 参照 checkpoint（decode 不使用）

| 項目 | 値 |
|---|---|
| checkpoint | `assets/odeformer/weights/odeformer.pt` |
| SHA256 | `56754040be5aa92ed4767fc43ee2008faa293f87c12b643e66c7df3e1623a5e8` |

---

## 14. 探索的観察との区別

| 項目 | 探索的 | confirmatory v2 |
|---|---|---|
| S5 hand-check | 成分抜粋・Scaler 未検証 | 封鎖外；G2 のみ |
| Stress scale 5.0 | — | 記述 tier |
| GPU_RUN5 公開数値 | 背景 | 再解釈禁止 |

---

## 15. 競合仮説

H0002–H0010 は本サイクルで検証しない。
H0001 supported → 指標修正サイクル優先。
H0001 unsupported → H0004 / H0003 を次候補。

---

## 16. 承認チェックリスト

| フィールド | v2 ドラフト |
|---|---|
| primary hypothesis | §1 H0001-METRIC（校正版） |
| primary endpoint | §2.1 `hill_false_negative_rate`（存在規則） |
| statistical unit | §2.2 系（240）／成分（510） |
| datasets | §4 C + N1 + S5（探索） |
| checkpoints | §13.4（参照のみ） |
| baselines/ablations | §6 B0–B4 |
| seeds | §7 |
| budgets | §8 CPU-only, no decode |
| operator constraints | §3–§5 |
| failure policy | §9 |
| support criteria | §10 |
| Go/No-Go | §11 |
| compute ceiling | §8.1 confirmatory 8,260 |
| required artifacts | §12 |
| reviewer sign-off | 未 |
| frozen_on | 未 |
| binding_plan path | 未 |

---

## 17. 関連ドキュメント

- `preregistration_draft.md` — v1（変更しない）
- `preregistration_independent_review.md` — 本 v2 が閉じるレビュー
- `preregistration_review_response.md` — finding-by-finding 対応表
- `scientific_state.md`, `hypothesis_review.md`
