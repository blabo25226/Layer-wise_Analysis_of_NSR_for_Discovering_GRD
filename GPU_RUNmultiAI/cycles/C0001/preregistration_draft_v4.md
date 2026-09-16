# C0001 事前登録 v4 — メトリック同定可能性監査

- campaign: GPU_RUNmultiAI
- cycle: C0001
- task: C0001-T005
- audit_id: `c0001_metric_identifiability_audit_v4`
- supersedes: `preregistration_draft_v3.md`（v3 は未凍結・参照のみ）
- 作成日: 2026-09-13
- 状態: **draft v4（未凍結・未承認）**
- binding_plan: null（凍結後に `research_state.md` へ記録）

本書は `.agent/rules/04-preregistration-and-metric-freeze.md` の全フィールドを
**メトリック監査** 向けに具体化した v4 ドラフトである。
独立 closure review（`preregistration_v3_independent_review.md`）の R3-1–R3-9 をすべて閉じる。
GPU_RUN5 の sealed test 生成果物は読まない。GPU_RUN5 の結論を再解釈しない。
**本監査は decode を含まない**（CPU の決定論的 Scaler 往復のみ）。

---

## 0. 科学的クレームの校正

**主張の範囲**:

- 本監査が検証するのは、評価連鎖が **代数的同値な Hill 表現に対して非不変** であること、
  および **strict-Hill 分類の undercounting** のみである。
- `canonical_exact` / `exponent_aware_skeleton_exact` は **構文木・正規化表現** の一致指標であり、
  一般代数同値性の oracle ではない。
- GPU_RUN5 等の過去 syntactic exact 結果を一括無効化しない。
- Hill 分類（component-level `hill_form`）と exact-tree / skeleton 回復は **別 endpoint** として報告する。
- **存在ゲートは薄い confirmatory 証拠**である。系統的/prevalence 主張は本監査の範囲外であり、
  別途凍結された prevalence 閾値を結果後に代入しない。

---

## 1. 主仮説（primary hypothesis）— 唯一の仮説規則

**H0001-METRIC（v4）**:
ODEFormer 推論プロトコルに対応する決定論的監査連鎖
（preverified 非自同値 rewrite からの full-system E0 → `Scaler.rescale_function` →
instrumented `simplify_tree` subprocess → component-level `classify_formula` readout）
は、**truth-side strict-Hill 登録ペア**の固定分母において、
独立 equivalence oracle で **E2 が真値と同値** と確認された成分に対し、
`component_flags[component_idx]["hill_form"] == false` となる **構造的偽陰性** を少なくとも 1 件生む。

**帰無仮説（監査用）**:
固定分母 1,320 primary strict-Hill scale ペアのうち、
`structural_false_negative` は **0 件**。

**primary decision rule（唯一）**:

| 判定 | 条件 |
|---|---|
| **H0001 supported** | 固定分母 1,320 件すべてが §2.2 の terminal outcome を **ちょうど 1 つ** 持ち、かつ `structural_false_negative` ≥ 1 |
| **H0001 unsupported** | 固定分母 1,320 件すべてが terminal outcome を **ちょうど 1 つ** 持ち、かつ `structural_false_negative` = 0 **かつ** §10 の validity gates すべて PASS |
| **H0001 undecidable** | terminal outcome が 1,320 未満、重複 pair、unknown/missing pair、または validity gate のいずれかが FAIL |

**terminal coverage は primary 判定の必須前提**である。
1,320 一意 strict-Hill pair のいずれかが欠落・重複・未確定の場合、supported/unsupported を判定しない。
primitive 完了率は **運用指標のみ**（§8.6）であり、primary 判定の代替にならない。

Controls（§10）は **validity gates** であり、primary 仮説判定の conjunct ではない。
control FAIL → **undecidable**（unsupported ではない）。

---

## 2. 一次エンドポイントと統計単位

### 2.1 一次 readout（C-A）

| 項目 | 定義 |
|---|---|
| **Primary readout** | `classify_formula(E2_infix)["component_flags"][component_idx]["hill_form"]` |
| **禁止** | `formula_metrics` の system-level OR、`classify_formula` の system-level `hill_form` |
| **Secondary** | `formula_metrics(skip_cas=True)` による `canonical_exact`, `exponent_aware_skeleton_exact`, TED 系 |

`formula_metrics` は `compare_formulas` 経由で `classify_formula` を呼ぶが、
返却 dict に `hill_form` は含まれない。primary 判定は **component_flags のみ**。

### 2.2 固定分母と mutually exclusive outcome partition（C-B, C-F, R3-1）

**Eligibility は truth-side で凍結**（E0/E1/E2 実行前）:

| 層 | 成分数 | primary grid ペア | 用途 |
|---|---:|---:|---|
| **strict-Hill primary** | 330 | **1,320** | primary 仮説の固定分母 |
| non-strict Hill-bearing secondary | 60 | 240 | 記述 tier のみ（§4.1） |
| linear control | 120 | 480 | validity gate のみ |

**truth-side strict-Hill 内訳**（系あたり、全 8 族合計 11 成分 × 30 slice = 330）:

| 族 | strict-Hill / 系 | 備考 |
|---|---:|---|
| R01 | 1 | |
| R02 | 1 | |
| R03 | 2 | |
| R04 | 1 | |
| R05 | 2 | |
| R06 | 3 | |
| R07 | 1 | component 3 は modulated（strict ではない） |
| R08 | 0 | component 3 は product base が strict denominator を満たさない |

**non-strict Hill-bearing 内訳**（60 成分）:

| サブ層 | 成分数 | 備考 |
|---|---:|---|
| R07 modulated | 30 | component 3、`modulated_hill_form=true` |
| R08 product-base | 30 | component 3、Hill-bearing だが strict ではない、`modulated_hill_form=false` |

導出: $`11 \times 3 \times 10 = 330`$ strict-Hill 成分、$`330 \times 4 = 1{,}320`$ primary scale ペア。
残り 60 成分は Hill-bearing だが strict ではない。
線形 120 成分は Hill 分母に含めない。

**固定分母 1,320 ペアの mutually exclusive partition**（各ペアはちょうど 1 つ、**完全排他的**）:

| Outcome category | 定義 |
|---|---|
| `construction_incomplete` | truth parse、rewrite preverify、E0 構築、registration oracle の不能 |
| `execution_failure` | E2 parse 失敗、NaN/Inf、`rescale_incomplete`、external simplifier timeout、external oracle timeout |
| `semantic_drift` | E1 oracle 非同値 **または** E2 oracle 非同値（上記 2 段階に該当しない場合） |
| `structural_false_negative` | E1 oracle 同値 **かつ** E2 oracle 同値 **かつ** `hill_form=false` |
| `preserved` | E1 oracle 同値 **かつ** E2 oracle 同値 **かつ** `hill_form=true` |

5 カテゴリの件数は固定分母 1,320 上で合計 1 になる（proportion は各カテゴリ / 1,320）。
E2 非同値ペアは `semantic_drift` に分類し、**分母から除外しない**。

**凍結 precedence / 真理値表**（上から順に最初に真になったカテゴリを採用）:

| 順位 | カテゴリ | 条件 |
|---:|---|---|
| 1 | `construction_incomplete` | registration 段の truth parse / rewrite preverify / E0 構築 / registration oracle 失敗 |
| 2 | `execution_failure` | E2 parse 失敗、NaN/Inf、`rescale_incomplete`、external simplifier timeout、external oracle timeout |
| 3 | `semantic_drift` | `e1_oracle_equivalent=false` **OR** `e2_oracle_equivalent=false` |
| 4 | `structural_false_negative` | `e1_oracle_equivalent=true` **AND** `e2_oracle_equivalent=true` **AND** `hill_form=false` |
| 5 | `preserved` | `e1_oracle_equivalent=true` **AND** `e2_oracle_equivalent=true` **AND** `hill_form=true` |

**stage attribution 用に保存するフラグ**:

| フィールド | 定義 |
|---|---|
| `e1_oracle_equivalent` | E1 が truth と独立 oracle 同値 |
| `e2_oracle_equivalent` | E2 が truth と独立 oracle 同値 |

`rescale_incomplete`（`len(nodes)>len(scale)` 等）は **execution failure** であり、
`structural_false_negative` には入れない（M-g）。

**terminal coverage 要件**:

- 1,320 一意 strict-Hill primary pair すべてが **exactly one** terminal outcome を持つこと
- missing pair、duplicate pair、`outcome_category=unknown` のいずれか 1 件でも primary 判定は **undecidable**

### 2.3 統計単位（C2）

| レベル | 定義 |
|---|---|
| **Primary sampling unit** | パラメータ化 GRN **系**（240 系） |
| **Within-system unit** | 系内 **成分**（510 成分） |
| **Confirmatory pair** | $`(f_{\mathrm{true}}, f_{\mathrm{pred,E2}})`$ を **固定成分 ID** でスコア |

forward scaling は **全成分 ordered system** 上で実行する（NodeList 位置依存を回避）。

### 2.4 二次 endpoint（conditional 命名必須）

| 名称 | 定義 | 用途 |
|---|---|---|
| `skeleton_false_negative_rate` | E2 同値 strict-Hill ペアで `exponent_aware_skeleton_exact=0` | secondary |
| `canonical_false_negative_rate` | E2 同値 strict-Hill ペアで `canonical_exact=0` | secondary |
| `semantic_drift_rate` | `semantic_drift` / 1,320 | 説明用 |
| `hill_false_positive_rate` | 線形 480 ペアで `hill_form=true` | control gate |
| `linear_canonical_noninvariance_rate` | 線形 480 ペアで `canonical_exact=0` | control gate（M-moderate rename） |

---

## 3. E0 / E1 / E2 パイプライン

### 3.1 記法と自律系前提（moderate）

- 物理変数 $`x_j`$、scaled 変数 $`z_j = s_j x_j`$
- 真値 $`f_i(x)`$ は **自律系**（$`t`$ を明示しない）。時間は rescaling のみで $`\tau = a_t t + b_t`$。
- E0 forward（成分 $`i`$）:

```math
g_i(z)=\frac{s_i}{a_t}\, f_i\!\left(\frac{z_1}{s_1},\ldots,\frac{z_d}{s_d}\right)
```

$`g_i`$ に $`\tau`$ を含めないのは、$`f_i`$ が自律であることに依存する。

### 3.2 Primary E0 源（C-D, M-d, R3-3）

| 条件 | E0 構築 |
|---|---|
| **B0 primary** | preverified **非自同値 rewrite**（`audit_rewrite_seed=61003`）から full-system analytic E0 |
| **B1** | **identity パラメータ**（$`s=1`$, $`a_t=1`$, $`b_t=0`$）で truth から identity E0 を **成分ごとに 1 回** 構築 |

B1 は scaled primary-grid E0 を identity scaler に通す比較 **ではない**（旧 v2 B1 の禁止比較）。

**全 510 成分**に決定論的・seeded・非自同値 rewrite を **1 本ずつ** 付与する。
rewrite は registration 段（P2）で独立 oracle 同値を preverify する。
`pair_id` と成果物 ID に **rewrite provenance**（`rewrite_id`）を含める。

rewrite 生成規則（凍結）:

- seed: `audit_rewrite_seed=61003`
- 成分キー: `(family, variant_index, component_idx)` の辞書順
- 各成分に非零有理数倍 `r` を 1 本割当（`r ≠ 1`、決定論的 PRNG から生成）
- P2 で truth と oracle 同値を確認；非同値は `construction_incomplete`

### 3.3 E1 / E2

| 段 | 定義 |
|---|---|
| **E1** | `Scaler.rescale_function(env, E0_tree, a_t, b_t, scale)` |
| **E2** | instrumented single-thread subprocess 内の `simplifier.simplify_tree(E1, expand=False, resimplify=False)` |

### 3.4 Simplifier 実装契約（C-E, M-c, R3-5）

**production 既定**（`third_party/odeformer/odeformer/envs/simplifiers.py`）:

- `expand=False`, `resimplify=False`
- SymPy `parse_expr(evaluate=True)` → `round_expr(decimals=4)` → prefix 再構築
- **内部 1 秒 timeout** は `except TimeoutError: pass` で握り潰され、**呼び出し側から観測不能**

**監査契約**:

1. 真値コーパスは `src/gpu_run5/grn.py` の **lexical `.4g` トークン**を忠実に使用する（§4.1）
2. **独立 `.4f` コーパスは作成しない**
3. production simplifier 以外で **再量子化しない**
4. simplification は **single-thread** subprocess のみ（signal ベース timeout と thread 併用禁止）
5. **external frozen timeout** = `5.0` 秒（subprocess kill；manifest に記録）
6. internal 1 秒 timeout の存在は記録するが、**E2==E1 から timeout を推論しない**
7. **監査対象の孤立変換**は production simplifier の parse/rounding 連鎖のみである
8. timeout 挙動（internal 1s swallowed、external 5s kill）を凍結する

### 3.5 独立 equivalence oracle（C-C, M-c）

| 項目 | 凍結値 |
|---|---|
| Analytic | sympy `simplify(expand=True)` exact rational |
| Numeric grid | 各 $`x_j \in \{0.01, 0.1, 0.5, 1.0, 2.0\}`$ 直積、$`t \in \{0, 5, 10\}`$、tol $`10^{-8}`$ |
| Truth 入力 | lexical `.4g` トークン文字列を `Rational(token_string)` として解釈 |
| **External oracle timeout** | `30.0` 秒 / 呼び出し |
| Timeout outcome | `execution_failure`（structural FN ではない） |

E2 oracle と E1 oracle は **別 counted call**（drift 分類に必須）。
`e1_oracle_equivalent` / `e2_oracle_equivalent` を pair row に保存する。

### 3.6 Serialization / prefix dialect（M-e）

各段（E0/E1/E2）で **raw prefix** と **emitted infix** を両方保存する。

| 項目 | 規則 |
|---|---|
| `neg` | prefix `neg` ノードを明示処理；infix 変換で符号を保持 |
| べき乗 | truth は `pow2` 入れ子、SymPy は `x**4` を emit し得る；skeleton 文字列が機械的に変わり得ることを secondary として報告 |
| tree→infix | production `env.word_to_infix` と同一 API を使用 |

---

## 4. データセットとコーパス

### 4.1 凍結コーパス

| 集合 | 内容 | 系 | 成分 | strict-Hill | non-strict Hill-bearing | 線形 |
|---|---|---:|---:|---:|---:|---:|
| **C** | `src/gpu_run5/grn.py` 生成 | 240 | 510 | 330 | 60 | 120 |

240 系 = 8 族 × 3 Hill 指数 $`\{1,2,4\}`$ × 10 draw（`audit_data_seed=61001`）。

**lexical token 監査境界**（R3-5）:

- `grn.py` は定数を `{:.4g}` で出力する（例: `f"{alpha:.4g}"`, `f"{k**n:.4g}"`, `f"{p['basal']:.4g}"`）
- 各 numeric leaf トークンについて **raw token string** と **parsed rational value** を保存する
- 独立 oracle は `Rational(token_string)` で truth を構築する
- `.4f` コーパスは追加しない
- production simplifier 以外での再量子化は禁止

### 4.2 Scale 設計

| 区分 | isotropic `traj_scale` | 用途 |
|---|---|---|
| **Primary grid** | `{0.1, 0.5, 1.0, 2.0}` | confirmatory（IC 範囲 `[0.05, 2.5]` 内） |
| **Stress** | `{5.0}` | 記述 tier のみ（D2） |

- $`d`$ 次元: `traj_scale = [s,\ldots,s]`、`scale = feature_scale / traj_scale`
- `feature_scale = 1` 固定
- primary grid は **全成分の決定論的直積**（`audit_scale_seed` は使用しない；moderate）

### 4.3 負対照・探索

| 集合 | 件数 | 用途 |
|---|---:|---|
| N1 | 100 | 意図非同値 rewrite；oracle が reject することを確認 |
| S5 | 1 hand-check ペア | 探索的再現（G2）；primary 非連動 |

---

## 5. Scaler 構築（M-b）

**production パス**: `SymbolicTransformerRegressor(params=None)` →
`Scaler(time_range=[1, 10], feature_scale=1, rescale_features=True)`。
bare `Scaler()` の `[1,5]` デフォルトは **禁止**。

**合成 trajectory**（`Scaler.fit` 用）:

```python
time = np.linspace(0.0, 10.0, 150)
trajectory = np.full((150, d), s, dtype=float)  # s = primary-grid isotropic scale
scaler.fit(time, trajectory)
```

`traj_scale` は `trajectory[argmin(time)]`（= $`[s,\ldots,s]`$）から決まる。

| assert フィールド | 期待値 |
|---|---|
| `time_scale` | 9 |
| `time_shift` | 1 |
| `a_t` | 0.9 |
| `b_t` | 1.0 |
| `rescale_features` | true |

assert 失敗 → abort。

---

## 6. ベースラインと ablation

| 条件 | 説明 | スコア段 | 単位 |
|---|---|---|---|
| **B0** | rewrite E0 → rescale → simplify → classify + metrics | E2 | 510 成分 × 4 scales = 2,040 ペア |
| **B1** | identity E0（1 回/成分）→ identity rescale → simplify | E2 | **510 成分**（scale 非依存） |
| **B2** | B0 と同 E0/E1；simplifier 省略 | E1 | 2,040 ペア |
| **B3** | `compare_formulas(..., skip_cas=False)` | 診断 | strict-Hill 500 ペア（hash 順） |
| **B4** | 真値 infix を pred にコピー | 指標健全性 | **510 成分**（scale 非依存） |

全 B0 成分は §3.2 の preverified rewrite E0 を共有する（510/510）。

---

## 7. シードと決定論

| 用途 | キー | 値 |
|---|---|---|
| GRN LHS | `audit_data_seed` | 61001 |
| Rewrite 生成 | `audit_rewrite_seed` | 61003 |
| N1 選択 | `audit_negative_seed` | 61004 |
| B3 CAS subset | `audit_cas_subset_seed` | 61005 |

系順序: `FAMILIES` dict 順（R01→R08）。
真値定数: `grn.py` の **lexical `.4g` トークン**（§4.1）。
B3 subset: strict-Hill 1,320 ペアを `(pair_id)` SHA256 昇順、先頭 500 件。

**`pair_id` 必須フィールド**（R3-8）:

| フィールド | 内容 |
|---|---|
| `corpus_hash` | 凍結コーパス SHA256 |
| `system_id` | 族・指数・draw を一意にする ID |
| `component_idx` | 系内成分 index |
| `scale` | primary-grid isotropic scale（B1/B4 は `identity`） |
| `rewrite_id` | 成分に割当された rewrite の決定論 ID |

---

## 8. 計算上限と counted-call 表（C-C）

### 8.1 Counted call の定義

**Counted call** = §8.2 の named primitive への **1 回の論理呼び出し**。
実装がメモ化しても `call_log.jsonl` に 1 行記録し ceiling に算入する。
resume キーは **`(primitive, condition, stage, pair_id)`**（§12）。

### 8.2 Named primitives

| ID | Primitive |
|---|---|
| P1 | `truth_register_classify` |
| P2 | `rewrite_oracle_precheck` |
| P3 | `e0_analytic_construct` |
| P4 | `e0_identity_construct` |
| P5 | `scaler_rescale_function` |
| P6 | `simplifier_subprocess` |
| P7 | `oracle_equivalence` |
| P8 | `classify_component_flags` |
| P9 | `formula_metrics_pair` |
| P10 | `compare_formulas_cas` |

### 8.3 Confirmatory operations table（完全導出）

| 行 | Primitive | Condition | 単位 | 回数 |
|---|---|---|---|---:|
| R1 | P1 `truth_register_classify` | registration | components | 510 |
| R2 | P2 `rewrite_oracle_precheck` | registration | **all components** | **510** |
| B0a | P3 `e0_analytic_construct` | B0 | primary-grid pairs | 2,040 |
| B0b | P5 `scaler_rescale_function` | B0 | pairs | 2,040 |
| B0c | P6 `simplifier_subprocess` | B0 | pairs | 2,040 |
| B0d | P7 `oracle_equivalence` | B0 → E2 | pairs | 2,040 |
| B0e | P7 `oracle_equivalence` | B0 → E1 | pairs | 2,040 |
| B0f | P8 `classify_component_flags` | B0 → E2 | pairs | 2,040 |
| B0g | P9 `formula_metrics_pair` | B0 → E2 | pairs | 2,040 |
| B1a | P4 `e0_identity_construct` | B1 | components | 510 |
| B1b | P5 `scaler_rescale_function` | B1 identity | components | 510 |
| B1c | P6 `simplifier_subprocess` | B1 | components | 510 |
| B1d | P8 `classify_component_flags` | B1 → E2 | components | 510 |
| B1e | P9 `formula_metrics_pair` | B1 → E2 | components | 510 |
| B2a | P8 `classify_component_flags` | B2 → E1 | pairs | 2,040 |
| B2b | P9 `formula_metrics_pair` | B2 → E1 | pairs | 2,040 |
| B4a | P8 `classify_component_flags` | B4 | components | 510 |
| B4b | P9 `formula_metrics_pair` | B4 | components | 510 |
| B3 | P10 `compare_formulas_cas` | B3 | strict-Hill pairs | 500 |
| N1 | P7 `oracle_equivalence` | N1 | negative controls | 100 |
| | | | **Confirmatory total** | **23,550** |

算術:

- Registration: $`510 + 510 = 1{,}020`$
- B0: $`2{,}040 \times 7 = 14{,}280`$
- B1: $`510 \times 5 = 2{,}550`$
- B2（E1 上の classify+metrics；E0/E1 は B0 と論理共有だが B0 行に含む）: $`2{,}040 \times 2 = 4{,}080`$
- B4: $`510 \times 2 = 1{,}020`$
- B3 + N1: $`500 + 100 = 600`$
- **合計**: $`1{,}020 + 14{,}280 + 2{,}550 + 4{,}080 + 1{,}020 + 600 = 23{,}550`$

### 8.4 Descriptive tier（primary 判定に不使用）

| 行 | 内容 | 追加 counted calls |
|---|---|---:|
| D1 | non-strict Hill-bearing（R07 modulated 30 + R08 product-base 30）の B0 結果からの **filtered aggregation**（0 追加呼び出し） | **0** |
| D2 | strict-Hill stress scale 5.0 B0 path（330 × 7 primitives） | **2,310** |
| | **Descriptive subtotal** | **2,310** |
| | **Full-run grand maximum** | **25,860** |

D1 は B0 の既存出力を stratum フィルタして集計するのみであり、追加 primitive 呼び出しを行わない。

### 8.5 Resource ceiling

| 項目 | 上限 |
|---|---|
| GPU / decode | **0** |
| CPU wall | ≤ 4 CPU-hours |
| **Confirmatory counted calls** | **23,550**（hard ceiling；超過で abort） |
| **Full-run grand maximum** | **25,860**（confirmatory + D2；超過で abort） |
| Descriptive tier | D2 は余裕時のみ；ceiling 超過禁止 |
| ディスク | ≤ 1 GB |

### 8.6 Primitive completion（運用指標のみ）

| 指標 | 定義 | 用途 |
|---|---|---|
| `primitive_completion_rate` | 完了 counted calls / 23,550 | 運用モニタリング |
| `terminal_coverage_rate` | terminal outcome を持つ primary pair 数 / 1,320 | primary 判定前提の監視 |

`primitive_completion_rate` は validity gate **ではない**。
primary 判定は **terminal coverage の 100%**（1,320/1,320）のみを要求する（§1, §2.2）。

---

## 9. 除外・失敗ポリシー

| 事象 | Outcome |
|---|---|
| External oracle / CAS / simplifier timeout | `execution_failure` |
| Internal 1s simplifier timeout（観測不能） | 記録のみ；external timeout で分類 |
| E2 parse / NaN / Inf | `execution_failure` |
| `rescale_incomplete` | `execution_failure`（**never** structural FN） |
| Truth / rewrite / E0 registration 失敗 | `construction_incomplete` |
| E1 または E2 oracle 非同値（正常終了） | `semantic_drift` |

---

## 10. Validity gates（controls；M-a）

**評価順序**: G0 → G4 → G1 → controls → **terminal coverage check** → **primary rule（§1）**

| Gate | 条件 | FAIL 時 |
|---|---|---|
| G0 | §5 Scaler assert 4 値 + `rescale_features=true` | abort |
| G4 | sealed-path **access guard** 違反（禁止 open/stat/listdir/scandir 試行 > 0） | invalid |
| G1 | confirmatory counted calls が hard ceiling 23,550 を超過 | abort |
| G_term | strict-Hill 1,320 pair すべてが terminal outcome を **ちょうど 1 つ** 持つ | undecidable |
| G_ctrl_fp | 線形 480 ペアで `hill_false_positive_rate = 0` | undecidable |
| G_ctrl_lin | 線形 480 ペアで `linear_canonical_noninvariance_rate = 0` | undecidable |
| G_inc | strict-Hill 1,320 で `construction_incomplete` ≤ 5% | undecidable |

Gates PASS **かつ** G_term PASS 後のみ §1 の supported/unsupported を判定する。

---

## 11. Sealed-path access guard（M-f, R3-7）

`configs/gpu_run5/base.yaml` から派生:

- `output_root = results/runs`
- `sealed_test_families = [R07, R08]`

**deny-on-attempt access guard**（コーパス作業 **前** にインストール）:

1. `configs/gpu_run5/base.yaml` から **禁止パターン**を導出する（glob 相当の normalized path 規則）
2. 禁止ディレクトリを列挙・inventory しない
3. `open` / `os.stat` / `os.listdir` / `os.scandir`（および同等 API）の **試行時**に normalized path を禁止パターンと照合
4. 一致した試行を **ブロック**し、`attempted_operation` と `attempted_path` をログする
5. 監査完了時点で **禁止アクセス試行が 0 件**であることを G4 で要求する

**既存 sealed artifact の存在だけでは G4 FAIL にならない**。
禁止パスへの実際の access 試行のみが violation である。
本タスクおよび監査実行では sealed 生成果物へアクセスしない。

**許可**: `src/gpu_run5/grn.py` から `audit_data_seed` で **新規** R07/R08 を生成
（歴史 sealed holdout の生成果物へはアクセスしない）。

---

## 12. 成果物と resume（M-h, R3-8）

| 成果物 | 内容 |
|---|---|
| `audit_manifest.json` | audit_id, commit, 全シード, Scaler assert, corpus counts, source hashes, access-guard attempt log, timeouts, plan hash, audit-script hash, 全 CLI, dependency versions, environment, ordered primitive table |
| `pair_results.csv` | `condition`, `pair_id`, stratum, outcome_category, `e1_oracle_equivalent`, `e2_oracle_equivalent`, E0/E1/E2 status, primary `hill_form`, secondary metrics, E0/E1/E2 raw prefix, E0/E1/E2 emitted infix |
| `call_log.jsonl` | 各行 = 1 counted call（primitive, condition, stage, pair_id, duration, status） |
| `condition_summary.json` | 固定分母上の 5-way partition 比率 |
| `equivalence_oracle.json` | E1/E2 oracle 判定 |
| `deviation_log.md` | 凍結後変更 |

**Resume**:

- キー: **`(primitive, condition, stage, pair_id)`**（`pair_id` 単独は不可）
- `pair_id` は §7 の必須フィールドをすべて含む
- `--resume` 前に検証: `audit_id`, commit SHA, plan hash, audit-script hash, config/source/corpus hashes, 全シード, ordered primitive table
- デフォルト `--fail-if-exists`

**manifest provenance（凍結）**:

| フィールド | 内容 |
|---|---|
| `plan_hash` | 本 preregistration 文書 SHA256 |
| `audit_script_hash` | `scripts/phases/gpu_runmultiai_c0001_metric_audit.py` SHA256 |
| `cli_args` | 起動時の全 CLI 引数 |
| `dependency_versions` | Python, sympy, numpy, torch 等 |
| `environment` | OS, CPU, git commit |
| `seeds` | §7 の全シード |
| `source_hashes` | §13.2 の全ファイル |
| `corpus_hash` | 凍結コーパス SHA256 |
| `primitive_table` | §8.2–§8.3 の順序付き primitive 表 |

---

## 13. 実行コマンドと provenance

### 13.1 環境

| 項目 | 凍結値 |
|---|---|
| Python | 3.10.x |
| CPU | `allow_cpu: true` は **CLI `--allow-cpu` のみ**（`configs/gpu_run5/base.yaml` の `allow_cpu: false` は変更しない） |
| CAS timeout | 60.0 s（B3） |

### 13.2 Source hashes（manifest 必須）

| ファイル | 用途 |
|---|---|
| `src/gpu_run5/grn.py` | 真値生成（lexical `.4g` トークン） |
| `src/evaluation/gpu_run5_structure.py` | `classify_formula` / strict Hill |
| `third_party/odeformer/odeformer/model/utils_wrapper.py` | Scaler |
| `third_party/odeformer/odeformer/model/sklearn_wrapper.py` | production パス |
| `third_party/odeformer/odeformer/envs/simplifiers.py` | simplify_tree |
| `src/gpu_run5/evaluation.py` | formula_metrics |
| `src/gpu_run4/formulas.py` | compare_formulas |
| `configs/gpu_run5/base.yaml` | sealed-path 派生 |

### 13.3 凍結コマンド（実装後）

```bash
python -m compileall -q src scripts tests
python scripts/phases/gpu_runmultiai_c0001_metric_audit.py \
  --audit-id c0001_metric_identifiability_audit_v4 \
  --output-dir GPU_RUNmultiAI/cycles/C0001/runs/c0001_metric_identifiability_audit_v4 \
  --audit-data-seed 61001 \
  --audit-rewrite-seed 61003 \
  --audit-negative-seed 61004 \
  --audit-cas-subset-seed 61005 \
  --allow-cpu \
  --oracle-timeout-sec 30.0 \
  --simplifier-subprocess-timeout-sec 5.0 \
  --cas-timeout-sec 60.0 \
  --fail-if-exists
```

Resume:

```bash
python scripts/phases/gpu_runmultiai_c0001_metric_audit.py \
  --audit-id c0001_metric_identifiability_audit_v4 \
  --output-dir GPU_RUNmultiAI/cycles/C0001/runs/c0001_metric_identifiability_audit_v4 \
  --resume
```

（スクリプトは prereg 凍結後の実装タスク。本タスクでは実行しない。）

---

## 14. 承認チェックリスト

| フィールド | v4 ドラフト |
|---|---|
| primary hypothesis | §1（唯一の存在規則 + terminal coverage 前提） |
| primary endpoint | §2.1 component `hill_form` |
| statistical unit | §2.3 |
| datasets | §4 |
| checkpoints | 参照のみ（decode 不使用） |
| baselines/ablations | §6 |
| seeds | §7 |
| budgets | §8.3–§8.5（confirmatory 23,550；grand max 25,860） |
| operator constraints | §3, §5 |
| failure policy | §9 |
| support criteria | §1 + §10 gates + G_term |
| Go/No-Go | §10 |
| compute ceiling | §8.5 |
| required artifacts | §12 |
| reviewer sign-off | 未 |
| frozen_on | 未 |

---

## 15. 関連ドキュメント

- `preregistration_draft.md` — v1（変更しない）
- `preregistration_draft_v2.md` — v2（変更しない）
- `preregistration_draft_v3.md` — v3（変更しない）
- `preregistration_v3_independent_review.md` — 本 v4 が閉じるレビュー
- `preregistration_v3_review_response.md` — finding-by-finding 対応表
- `preregistration_v2_closure_review.md` — v3 が閉じたレビュー
- `preregistration_v2_review_response.md` — v2 対応表
