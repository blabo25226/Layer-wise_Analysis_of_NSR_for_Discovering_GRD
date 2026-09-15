# C0001 事前登録 v13 — メトリック同定可能性監査（自己完結改訂）

- campaign: GPU_RUNmultiAI
- cycle: C0001
- task: C0001-T012
- audit_id: `c0001_metric_identifiability_audit_v13`
- 作成日: 2026-09-16
- 状態: **draft v13（未凍結・未承認）**
- binding_plan: null（凍結後に `research_state.md` へ記録）

本書は `.agent/rules/04-preregistration-and-metric-freeze.md` の全フィールドを
**メトリック監査** 向けに具体化した **自己完結** v13 ドラフトである。
v12 targeted independent review の R12-1 から R12-5 を閉じる。
**normative 本文に歴史文書への委譲・「同一」参照は使用しない。**

GPU_RUN5 の sealed test 生成果物は読まない。GPU_RUN5 の結論を再解釈しない。
**本監査は decode を含まない**（CPU の決定論的 Scaler 往復のみ）。

---

## 0. 科学的クレームの校正

**主張の範囲**:

- 本監査が検証するのは、**凍結された whole-chain readout**
  （production simplifier → `classify_formula` の **合成連鎖全体**）が、
  **truth-side strict-Hill 登録ペア**の固定分母において、
  **E1 が独立 oracle で元の真値（未量子化 truth）と同値かつ E2 が独立 oracle で audit-owned `Q4(E1)` と同値**
  である strict-Hill ペアにおいて、
  component-level `hill_form` を誤って `false` とする **構造的偽陰性** を生むかどうかのみである。
- **係数の四桁量子化そのものは構造的偽陰性ではない**。
  元 truth と `Q4(E1)` の差は **記述フィールド** `original_vs_q4_numeric_max_abs_error` として保存し、
  primary partition へ混ぜない。
- **因果的 stage attribution は主張しない**。Stage A 出力と Stage B の parse 成否・`hill_form` のみ保存する。
- `canonical_exact` / `exponent_aware_skeleton_exact` は **構文木・正規化表現** の一致指標であり、
  一般代数同値性の oracle ではない。
- truth-side **quantization stratum** は **報告次元のみ**であり、分母除外・primary 判定の conjunct ではない。
- Hill 分類と exact-tree / skeleton 回復は **別 endpoint** として報告する。
- **存在ゲートは薄い confirmatory 証拠**である。系統的/prevalence 主張は本監査の範囲外。

**監査限界**:

- audit-owned Q4 は production `parse_expr` + `Float.round(4)` + **凍結 `sympy_to_prefix` 規則**（§3.4.6）を
  **意図的に mirror** する。両経路で共有される parse/round/serialize 欠陥は **非可視** になり得る。
- production simplifier は internal 1s timeout を **握り潰し**、入力 tree を返し得る（§3.6）。
  audit Q4 は external-only timeout で **完了失敗**として記録する（§3.4）。
  この **timeout 非対称** により、E2 raw==E1 raw でも internal fallback か正常同値かを timeout だけでは区別できない。
  本監査は `e2_identity_fallback_candidate`（§2.2）で **非 diagnostic** を分類するが、
  **internal timeout を直接主張しない**。

---

## 1. 主仮説（primary hypothesis）— 唯一の仮説規則

**H0001-METRIC（v13）**:
ODEFormer 推論プロトコルに対応する決定論的監査連鎖
（preverified 非自同値 rewrite からの full-system E0 → `Scaler.rescale_function` →
audit-owned `Q4(E1)` 参照構築 → instrumented `simplifier.simplify_tree` subprocess →
component-level `classify_formula` readout）
は、**truth-side strict-Hill 登録ペア**の固定分母において、
独立 equivalence oracle で **E1 が元 truth と同値かつ E2 が `Q4(E1)` と同値** と確認された成分に対し、
`component_flags[component_idx]["hill_form"] == false` となる **構造的偽陰性** を少なくとも 1 件生む。

**帰無仮説（監査用）**:
固定分母 **1,320** primary strict-Hill scale ペアについて、
`structural_false_negative` は **0 件**（不在結論は §1 順位 3 の条件を参照）。

**diagnostic coverage の定義**:

| 用語 | 定義 |
|---|---|
| **fully diagnostic pair** | terminal outcome が `preserved` または `structural_false_negative`（`construction_incomplete=0` かつ `execution_failure=0` かつ `semantic_drift=0` かつ **E1-original 同値** かつ **E2–`Q4(E1)` 同値** が確認済み） |
| **non-diagnostic pair** | `construction_incomplete`、`execution_failure`、`semantic_drift` のいずれか |

**primary decision rule（唯一・排他的評価順序）**:

| 順位 | 判定 | 条件 |
|---:|---|---|
| 1 | **H0001 undecidable** | §10 の **validity gate のいずれかが FAIL**、または terminal coverage 不成立（1,320 一意 pair の欠落・重複・`unknown`） |
| 2 | **H0001 supported** | （順位 1 が false）**かつ** **fully diagnostic** な `structural_false_negative` ≥ 1 |
| 3 | **H0001 unsupported** | （（順位 1 が false）**かつ**（順位 2 が false））**かつ** `structural_false_negative`=0 **かつ** 固定分母 1,320 件 **すべて** fully diagnostic |
| 4 | **H0001 undecidable** | 上記のいずれにも該当しない（例: SFN=0 だが non-diagnostic pair が 1 件以上残る） |

**存在 vs 不在の非対称ロジック**:

- **supported**: fully diagnostic SFN が **1 件でもあれば** 十分。
- **unsupported**: SFN=0 だけでは不十分。**1,320 件すべて** fully diagnostic が必須。
  `e2_identity_fallback_candidate` 等の non-diagnostic が 1 件でも残れば unsupported に到達できず **undecidable**。
- **global zero-rate gate は禁止**: non-diagnostic 率で otherwise valid positive evidence を棄却しない。

Controls（§10）は **validity gates** であり、primary 仮説判定の conjunct ではない。

---

## 2. 一次エンドポイントと統計単位

### 2.1 一次 readout（C-A）— whole-chain observable

| 段 | 処理 | 保存フィールド |
|---|---|---|
| **Stage A-pre** | audit-owned `Q4(E1)` 参照構築（§3.4） | `q4_construction_completed`, `q4_emitted_infix`, `q4_sympy_expr_canonical`, `q4_construction_failure_reason` |
| **Stage A** | production `simplifier.simplify_tree(E1)` → emitted infix | `e2_infix_pre_classifier`, `e2_prefix_raw` |
| **Stage B** | `classify_formula(e2_infix_pre_classifier)` | `classifier_parse_valid`, `classifier_parse_failure_reason`, `hill_form` |

| 項目 | 定義 |
|---|---|
| **Primary readout** | `classify_formula(e2_infix_pre_classifier)["component_flags"][component_idx]["hill_form"]` |
| **禁止** | system-level OR、`formula_metrics` の `hill_form` |
| **Secondary** | `formula_metrics(true_infix, predicted_infix)` による exact/skeleton 系 |
| **記述（primary 非連動）** | `original_vs_q4_numeric_max_abs_error`（§3.5.3） |

`formula_metrics` signature: `formula_metrics(true_infix: str, predicted_infix: str)`。
内部で `compare_formulas(..., skip_cas=True)` を固定呼び出し。返却 dict に `hill_form` は含まれない。

### 2.2 固定分母と mutually exclusive outcome partition

**Eligibility は truth-side で凍結**（E0/E1/E2 実行前）:

| `eligibility_layer` | 成分数 | primary grid ペア | 用途 |
|---|---:|---:|---|
| `strict_hill_primary` | 330 | **1,320** | primary 仮説の固定分母 |
| `non_strict_hill_secondary` | 60 | 240 | 記述 tier |
| `linear_control` | 120 | 480 | validity gate のみ |

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
| R07 modulated | 30 | `modulated_hill_form=true` |
| R08 product-base | 30 | Hill-bearing だが strict ではない |

導出: $`11 \times 3 \times 10 = 330`$ strict-Hill 成分、$`330 \times 4 = 1{,}320`$ primary scale ペア。

**truth-side quantization stratum**（報告のみ）:

| stratum | 成分レベル定義 | 期待 strict-Hill 成分数 | 期待 primary ペア数 |
|---|---|---:|---:|
| `quantization_neutral` | 成分の **すべて** の numeric leaf トークンが §4.4 の `fractional_digit_count` ≤ 4 | 284 | 1,136 |
| `quantization_active` | **少なくとも 1 つ** の numeric leaf で `fractional_digit_count` > 4 | 46 | 184 |

stratum は registration 段 P12 で **全 510 成分**に決定論的付与する。
`quantization_stratum.json` を成果物として保存する（§12）。
**分母から除外しない**。

**`e2_identity_fallback_candidate`**:

| 項目 | 凍結定義 |
|---|---|
| 判定 | `e2_prefix_raw == e1_prefix_raw`（byte-identical comma-separated prefix 文字列） |
| 追加条件 | E1 が `Q4(E1)` と **SymPy 式レベルで非同値**（§3.4.8 oracle；`q4_sympy_expr_canonical` 使用） |
| 分類 | **`execution_failure`**（precedence 順位 2；`semantic_drift` より前） |
| 禁止 | raw E2==E1 だけで internal simplifier timeout を **主張** すること |
| unsupported 要件 | unsupported 到達には **non-diagnostic ペア（本候補含む）が 0 件** であること |

**固定分母 1,320 ペアの mutually exclusive partition**（各ペアはちょうど 1 つ）:

| Outcome category | 定義 |
|---|---|
| `construction_incomplete` | truth parse、rewrite preverify、E0 構築、**E1 構築または E1 parse 不能**（production simplifier **実行前**） |
| `execution_failure` | `q4_construction_completed=false`、**`e2_identity_fallback_candidate=true`**、**`classifier_parse_valid=false`**、E2 parse 失敗、NaN/Inf、**`rescale_incomplete=true`**（§5.2）、external simplifier timeout、**E1-original または E2–`Q4` oracle `completed=false`** |
| `semantic_drift` | （`e1_oracle_completed=true` **AND** `e1_oracle_equivalent=false`）**OR**（`e2_oracle_completed=true` **AND** `e2_oracle_equivalent=false`） |
| `structural_false_negative` | （`e1_oracle_equivalent=true` **AND** `e2_oracle_equivalent=true` **AND** `hill_form=false`） |
| `preserved` | （`e1_oracle_equivalent=true` **AND** `e2_oracle_equivalent=true` **AND** `hill_form=true`） |

**凍結 precedence**（上から順に最初に真）:

| 順位 | カテゴリ | 条件 |
|---:|---|---|
| 1 | `construction_incomplete` | registration 段の truth/E0/E1 構築・parse 不能（simplifier 前） |
| 2 | `execution_failure` | `q4_construction_completed=false` **OR** `e2_identity_fallback_candidate=true` **OR** `classifier_parse_valid=false` **OR** E2 parse/NaN/Inf **OR** `rescale_incomplete=true` **OR** external simplifier timeout **OR**（`e1_oracle_completed=false` **OR** `e2_oracle_completed=false`） |
| 3 | `semantic_drift` | （`e1_oracle_completed=true` **AND** `e1_oracle_equivalent=false`）**OR**（`e2_oracle_completed=true` **AND** `e2_oracle_equivalent=false`） |
| 4 | `structural_false_negative` | `e1_oracle_equivalent=true` **AND** `e2_oracle_equivalent=true` **AND** `hill_form=false` |
| 5 | `preserved` | `e1_oracle_equivalent=true` **AND** `e2_oracle_equivalent=true` **AND** `hill_form=true` |

**stage observability 用フラグ**:

| フィールド | 定義 |
|---|---|
| `e1_oracle_reference` | **凍結値** `original_truth` |
| `e2_oracle_reference` | **凍結値** `q4_e1` |
| `e1_oracle_completed` / `e1_oracle_equivalent` | E1 vs **元 truth** |
| `e2_oracle_completed` / `e2_oracle_equivalent` | E2 vs **`Q4(E1)`** |
| `e2_identity_fallback_candidate` | §2.2 定義 |
| `q4_construction_completed` | P11 が §3.4 契約どおり完了 |
| `quantization_stratum` | `quantization_neutral` または `quantization_active` |
| `original_vs_q4_numeric_max_abs_error` | 記述（§3.5.3）；primary 判定に不使用 |
| `is_fully_diagnostic` | outcome が `preserved` または `structural_false_negative` |
| `eligibility_layer` | §2.5 truth-side 層（非循環） |
| `partition_scope` | §2.5 条件と層から導出 |

**禁止**: E2≠truth のみを根拠に `structural_false_negative` と判定してはならない。

### 2.3 統計単位

| レベル | 定義 |
|---|---|
| **Primary sampling unit** | パラメータ化 GRN **系**（240 系） |
| **Within-system unit** | 系内 **成分**（510 成分） |
| **Confirmatory pair** | $`(f_{\mathrm{true}}, f_{\mathrm{pred,E2}})`$ を **固定成分 ID** でスコア |

forward scaling は **全成分 ordered system** 上で実行する。

### 2.4 二次 endpoint

| 名称 | 定義 | 用途 |
|---|---|---|
| `skeleton_false_negative_rate` | E2 同値 strict-Hill ペアで `exponent_aware_skeleton_exact=0` | secondary |
| `canonical_false_negative_rate` | E2 同値 strict-Hill ペアで `canonical_exact=0` | secondary |
| `semantic_drift_rate` | `semantic_drift` / 1,320 | 説明用 |
| `hill_false_positive_rate` | 線形 480 ペアで `hill_form=true` | control gate |
| `linear_canonical_noninvariance_rate` | 線形 480 ペアで `canonical_exact=0` | control gate |
| `quantization_active_rate` | `quantization_active` strict-Hill ペア / 1,320 | stratum 報告 |
| `original_vs_q4_error_rate_nonzero` | `original_vs_q4_numeric_max_abs_error` > 0 の strict-Hill ペア率 | 記述 |
| `e2_identity_fallback_rate` | `e2_identity_fallback_candidate` / 1,320 | 記述 |

### 2.5 `eligibility_layer`、非循環 row predicate、`partition_scope` 導出

**`pair_results.csv` 必須列**: `eligibility_layer`, `partition_scope`。

#### 2.5.1 Truth-side row predicate（非循環；ゲート定義に依存しない）

各成分 $`c`$（`system_id`, `component_idx`）について、registration 前に次を決定論的評価する。

| Predicate | 真となる条件 |
|---|---|
| `P_strict_hill(c)` | 族内訳表（§2.2）により strict-Hill 成分に分類される |
| `P_non_strict_hill(c)` | R07 modulated（component 3）**または** R08 product-base（component 3） |
| `P_linear(c)` | 上記 2 つが false の残り 120 成分 |

**凍結 zero-based `component_idx` 集合**（registration 段 P1 で全 510 成分に適用；`src/gpu_runmultiai/strata.py` と同一）:

| 族 | strict-Hill indices | non-strict Hill indices | linear indices |
|---|---|---|---|
| R01 | `{0}` | `{}` | `{}` |
| R02 | `{0}` | `{}` | `{}` |
| R03 | `{0, 1}` | `{}` | `{}` |
| R04 | `{1}` | `{}` | `{0}` |
| R05 | `{0, 1}` | `{}` | `{}` |
| R06 | `{0, 1, 2}` | `{}` | `{}` |
| R07 | `{1}` | `{2}` | `{0}` |
| R08 | `{}` | `{2}` | `{0, 1}` |

**排他性検査（registration 開始前；G_eligibility）**:

| 検査 | 期待 | 不一致時 |
|---|---|---|
| 各 `(family, component_idx)` が strict / non-strict / linear の **ちょうど 1 つ** に属する | 510/510 | **abort** |
| strict-Hill 成分総数 | **330** | **abort** |
| non-strict Hill 成分総数 | **60** | **abort** |
| linear 成分総数 | **120** | **abort** |


| `P_primary_scale(s)` | $`s \in \{0.1, 0.5, 1.0, 2.0\}`$ |
| `P_stress_scale(s)` | $`s = 5.0`$ |

**排他性**: 各成分はちょうど 1 つの `eligibility_layer` に属する。

| `eligibility_layer` | Predicate |
|---|---|
| `strict_hill_primary` | `P_strict_hill(c)` |
| `non_strict_hill_secondary` | `P_non_strict_hill(c)` |
| `linear_control` | `P_linear(c)` |

#### 2.5.2 `partition_scope` 導出（条件 × 層）

| condition | `eligibility_layer` | `partition_scope` | 許可 terminal / control 語彙 | `unknown` |
|---|---|---|---|---|
| **B0** | `strict_hill_primary` | `primary` | §2.2 の 5 outcome | **禁止** |
| **B0** | `non_strict_hill_secondary` | `secondary` | §2.2 の 5 outcome | **禁止** |
| **B0** | `linear_control` | `control_linear` | §2.2 の 5 outcome | **禁止** |
| **B1** | （全 510 成分；scale 非依存） | `control` | `control_pass` **または** `control_failure` のみ | **禁止** |
| **B2** | `strict_hill_primary` | `primary` | §2.2 の 5 outcome | **禁止** |
| **B2** | `non_strict_hill_secondary` | `secondary` | §2.2 の 5 outcome | **禁止** |
| **B2** | `linear_control` | `control_linear` | §2.2 の 5 outcome | **禁止** |
| **B3** | `strict_hill_primary` | `diagnostic` | `diagnostic_complete` **または** `diagnostic_failed` のみ | **禁止** |
| **B4** | （全 510 成分） | `metric_sanity` | `sanity_pass` **または** `sanity_failure` のみ | **禁止** |
| **N1** | n/a | `negative_control` | `negative_reject` **または** `negative_failed` | **禁止** |
| **C_q4** | n/a | `q4_fixture` | `fixture_pass` **または** `fixture_failure` のみ | **禁止** |
| **D2** | `strict_hill_primary` | `descriptive` | `descriptive_recorded` **または** `descriptive_failed` のみ | **禁止** |


#### 2.5.3 凍結 canonical `scale` token（`pair_id` 用）

| 用途 | 許可 token | 禁止 |
|---|---|---|
| primary grid | **`0.1`**, **`0.5`**, **`1.0`**, **`2.0`**（JSON shortest round-trip 文字列） | 別表記（`1`, `2`, `0.50` 等） |
| D2 stress | **`5.0`** | 同上 |
| B1 identity | **`identity`**（`pair_key` の `scale=` フィールド） | numeric scale |
| B4 truth copy | **`identity`** | numeric scale |

`pair_key` の `scale={scale}` は上表 token を **verbatim** 使用する。

#### 2.5.4 直接 row predicate（B3 / B4 / N1 / C_q4 / D2）

各制御行は **行フラグのみ** から terminal outcome を決定する（ゲート定義と非循環）。

**B3**（`partition_scope=diagnostic`；500 strict-Hill primary ペア）:

```text
diagnostic_complete_row =
  classifier_parse_valid
  AND formula_metrics_valid
  AND cas_compare_completed
  AND cas_compare_valid
terminal = diagnostic_complete_row ? diagnostic_complete : diagnostic_failed
```

**B4**（`partition_scope=metric_sanity`；510 components）:

```text
sanity_pass_row =
  classifier_parse_valid
  AND formula_metrics_valid
  AND canonical_exact == 1
terminal = sanity_pass_row ? sanity_pass : sanity_failure
```

**N1**（`partition_scope=negative_control`；100 negatives）:

```text
negative_reject_row =
  oracle_completed
  AND NOT oracle_equivalent
terminal = negative_reject_row ? negative_reject : negative_failed
```

**C_q4**（`partition_scope=q4_fixture`；7 fixtures）:

```text
fixture_pass_row =
  q4_construction_completed
  AND fixture_specific_assertions_pass
terminal = fixture_pass_row ? fixture_pass : fixture_failure
```

`fixture_specific_assertions_pass` は §6.1 の fixture 表どおり（`q4_fixture_07` は Rational 不変性を含む）。

**D2**（`partition_scope=descriptive`；330 strict-Hill stress ペア）:

```text
descriptive_recorded_row =
  construction_incomplete == false
  AND outcome_category IN {preserved, structural_false_negative, semantic_drift, execution_failure}
terminal = descriptive_recorded_row ? descriptive_recorded : descriptive_failed
```

D2 は **記述 tier** のみ。primary 仮説判定の conjunct ではない。

#### 2.5.5 B1 `control_pass`（行フラグから直接計算；ゲートと非循環）

各 B1 行について、次を **行フラグのみ** から計算する（G_b1 定義に先立つ）:

```text
control_pass_row =
  q4_construction_completed
  AND e1_oracle_completed AND e1_oracle_equivalent
  AND e2_oracle_completed AND e2_oracle_equivalent
  AND classifier_parse_valid
  AND formula_metrics_valid
```

| terminal outcome | 条件 |
|---|---|
| `control_pass` | `control_pass_row == true` |
| `control_failure` | `control_pass_row == false` |

**G_b1**（§10）は `sum(control_pass_row) == 510` を要求する。`control_pass` と G_b1 を相互定義してはならない。

---

## 3. E0 / E1 / E2 / Q4 パイプライン

### 3.1 記法と自律系前提

- 物理変数 $`x_j`$、scaled 変数 $`z_j = s_j x_j`$
- 真値 $`f_i(x)`$ は **自律系**（$`t`$ を明示しない）。時間は rescaling のみで $`\tau = a_t t + b_t`$。
- E0 forward（成分 $`i`$）:

```math
g_i(z)=\frac{s_i}{a_t}\, f_i\!\left(\frac{z_1}{s_1},\ldots,\frac{z_d}{s_d}\right)
```

### 3.2 Primary E0 源と凍結 rewrite

| 条件 | E0 構築 | `rewrite_id` |
|---|---|---|
| **B0 primary/secondary/linear** | preverified **非自同値 rewrite**（`audit_rewrite_seed=61003`）から full-system analytic E0 | `rewrite_sha256:{digest_hex}` |
| **B1** | **identity パラメータ**（$`s=1`$, $`a_t=1`$, $`b_t=0`$）で truth から identity E0 を **成分ごとに 1 回** 構築 | **`identity`** |
| **B4** | 真値 infix を pred にコピー（指標健全性） | **`truth_copy`** |

**凍結 canonical serialization 契約**:

| 項目 | 凍結値 |
|---|---|
| 区切り | ASCII pipe byte `0x7c`（backslash byte 数 = 0） |
| フィールド形式 | `{field_name}={value}` |
| 空白 | field label と value の間、区切りの前後に **空白なし** |
| escaping | **禁止** |
| UTF-8 | すべての canonical byte 列は UTF-8 |

**凍結 rewrite 生成規則**:

| 項目 | 凍結値 |
|---|---|
| seed フィールド | `audit_rewrite_seed=61003` |
| 成分キー | `(system_id, component_idx)` |
| 素数集合 | `PRIMES = [2, 3, 5, 7, 11]` |
| 選択 | `digest = SHA256(UTF-8(canonical_key_string))`；`r = PRIMES[int.from_bytes(digest[:8], "big") % 5]` |
| canonical_key_string | `audit_rewrite_seed=61003|system_id={system_id}|component_idx={component_idx}` |
| `rewrite_id` | `rewrite_sha256:{digest_hex}` |

**representative fixture**（`system_id=R01_train_d61001_000`, `component_idx=0`）:

```text
canonical_key_string=audit_rewrite_seed=61003|system_id=R01_train_d61001_000|component_idx=0
sha256=91a3f6eb6ae668bbefd4a9d9cfc0242032549f5e9346450e932c09129bdf4d90
selected_r=3
rewrite_id=rewrite_sha256:91a3f6eb6ae668bbefd4a9d9cfc0242032549f5e9346450e932c09129bdf4d90
prefix_template=div,mul,{r},{E_prefix...},{r}
```

P2 `rewrite_oracle_precheck`: lexical non-identity **かつ** §3.5 oracle 同値。失敗 → `construction_incomplete`。

### 3.3 E1 / E2

| 段 | 定義 |
|---|---|
| **E1** | `Scaler.rescale_function(env, E0_tree, a_t, b_t, scale)` |
| **Q4(E1)** | §3.4 audit-owned 参照（production simplifier **非呼び出し**） |
| **E2** | instrumented subprocess 内 `simplifier.simplify_tree(E1, expand=False, resimplify=False)` |

### 3.4 Audit-owned `Q4(E1)` 参照

**目的**: production `tree_to_sympy_expr(round=True)` の
`parse_expr(evaluate=True)` → `Float.round(4)` → **凍結 `sympy_to_prefix` 規則**（§3.4.6）を、
**最小非循環参照**として再現する。
production `simplify_tree` またはその返却 tree を **参照・呼び出し・再利用してはならない**。

**凍結 algorithm `audit_q4_decimal_round_reference`**:

| 手順 | 操作 | 失敗時 |
|---:|---|---|
| 1 | E1 prefix を audit-owned `prefix_to_sympy_infix`（§3.4.2）で SymPy 互換 infix へ変換 | `q4_construction_completed=false` |
| 2 | `sympy.parsing.sympy_parser.parse_expr(infix, evaluate=True, local_dict=FROZEN_Q4_LOCAL_DICT)` | 同上 |
| 3 | `audit_round_float_atoms(expr, decimals=4)`（§3.4.3） | nonfinite → 同上 |
| 4 | 丸め後 expr を `audit_sympy_to_prefix`（§3.4.6）で prefix へ再射影 | 同上 |
| 5 | prefix を `prefix_to_sympy_infix` で infix へ；**SymPy 式 canonical 比較**用に `q4_sympy_expr_canonical` を保存 | — |

**external Q4 timeout**: `10.0` 秒 / 呼び出し → `q4_construction_completed=false` → `execution_failure`。

#### 3.4.1 凍結 prefix operator arity（`all_operators`）

| token | arity |
|---|---:|
| `add`, `sub`, `mul`, `div` | 2 |
| `abs`, `inv`, `sqrt`, `log`, `exp`, `sin`, `arcsin`, `cos`, `arccos`, `tan`, `arctan`, `pow2`, `pow3`, `id` | 1 |
| `pow` | 2 |

#### 3.4.2 `prefix_to_sympy_infix`（audit-owned）

production `_prefix_to_sympy_compatible_infix` / `prefix_to_sympy_compatible_infix` と
**同一の再帰規則**を audit 実装が再実装する（production import 禁止）。

| 規則 | 内容 |
|---|---|
| 演算子 arity | §3.4.1 |
| 子の取り出し | 演算子 token の直後から arity 個の subtree を **左から順に** 再帰解析 |
| leaf numeric | `float(token)` 成功時は `str(token)` を leaf 文字列とする |
| leaf 変数 | 非 numeric leaf はそのまま |
| 出力 | 全体を `({infix})` で包む |
| 空リスト | `InvalidPrefixExpression` |

#### 3.4.3 `audit_round_float_atoms`

```python
def audit_round_float_atoms(expr, decimals: int = 4):
    return expr.xreplace(
        Transform(
            lambda x: x.round(decimals),
            lambda x: isinstance(x, sp.Float),
        )
    )
```

| 項目 | 凍結値 |
|---|---|
| `decimals` | **4** |
| 対象 | `sympy.Float` インスタンスのみ |
| `Rational` / `Integer` | **変更しない** |
| internal 1s timeout | **使用しない** |

#### 3.4.4 `FROZEN_Q4_LOCAL_DICT`

| キー | 値 |
|---|---|
| `n` | `Symbol("n", real=True, nonzero=True, positive=True, integer=True)` |
| `e`, `pi`, `euler_gamma` | SymPy 定数 |
| `arcsin`, `arccos`, `arctan`, `step`, `sign` | 対応 SymPy 関数 |
| `x_0` … `x_9` | `Symbol("x_k", real=True, integer=False)` |
| 系変数 | コーパス次元 `d` に応じて `x_0`…`x_{d-1}` を追加 |

#### 3.4.5 凍結 SymPy → prefix 規則（`SYMPY_OPERATORS`）

| SymPy 型 | prefix 演算子名 |
|---|---|
| `sp.Add` | `add` |
| `sp.Mul` | `mul` |
| `sp.Mod` | `mod` |
| `sp.Pow` | `pow` |
| `sp.Abs` | `abs` |
| `sp.sign` | `sign` |
| `sp.Heaviside` | `step` |
| `sp.exp` | `exp` |
| `sp.log` | `log` |
| `sp.sin` | `sin` |
| `sp.cos` | `cos` |
| `sp.tan` | `tan` |
| `sp.asin` | `arcsin` |
| `sp.acos` | `arccos` |
| `sp.atan` | `arctan` |

**leaf / 特殊 atom 規則**:

| SymPy 型 | prefix 出力規則 |
|---|---|
| `sp.Symbol` | `[str(expr)]` |
| `sp.Integer` | `[str(expr)]` |
| **`sp.Float`** | `s = str(expr)`（SymPy 既定 StrPrinter）；`[s]` |
| **`sp.Rational`** | `["mul", str(expr.p), "pow", str(expr.q), "-1"]`（**production 互換順序**） |
| `sp.EulerGamma` | `["euler_gamma"]` |
| `sp.E` | `["e"]` |
| `sp.pi` | `["pi"]` |
| 演算子 | 上表 `SYMPY_OPERATORS` に従い `_sympy_to_prefix(op_name, expr)` で子を再帰 |

**禁止**: `word_to_infix` 意味同等だけで Float 表現を凍結しないこと。

#### 3.4.6 凍結 production n-ary `_sympy_to_prefix` fold（SymPy → prefix）

production `third_party/odeformer/odeformer/envs/simplifiers.py` の `_sympy_to_prefix` を
audit `audit_sympy_to_prefix` が **byte-faithful に再実装**する（import 禁止）。
source hash: `third_party/odeformer/odeformer/envs/simplifiers.py`（§13.2）。

```python
def audit_sympy_to_prefix_nary_fold(op: str, expr) -> list[str]:
    n_args = len(expr.args)
    parse_list: list[str] = []
    for i in range(n_args):
        if i == 0 or i < n_args - 1:
            parse_list.append(op)
        parse_list += audit_sympy_to_prefix(expr.args[i])
    return parse_list
```

| 項目 | 凍結値 |
|---|---|
| 子の順序 | `expr.args` の **左から右**（SymPy 既定順） |
| 演算子出現回数 | `n_args - 1` 回（`n_args >= 2` の `add` / `mul`） |
| 適用演算子 | §3.4.1 production 表の `add`, `mul` および §3.4.5 `SYMPY_OPERATORS` 由来の全演算子 |

**3-child n-ary parity fixture（Q4-NARY-3）**:

| 入力 SymPy | 期待 prefix |
|---|---|
| `sp.Add(x_0, x_1, x_2)` | `add,add,x_0,x_1,x_2` |
| `sp.Mul(2, x_0, x_1)` | `mul,mul,2,x_0,x_1` |

`audit_sympy_to_prefix` は §3.4.5 leaf/特殊 atom 規則を適用した後、演算子ノードで上記 fold を呼ぶ。

#### 3.4.7 audit-oracle extended operator arity（F2 回帰；production Q4 とは別名）

**production Q4 表（§3.4.1）に `pow4` は存在しない。** F2 compound-power 回帰は **audit-owned equivalence parser** の拡張表で扱う。

| token | arity | 用途 |
|---|---:|---|
| §3.4.1 全 token | §3.4.1 と同値 | production Q4 emit / reparse |
| **`pow4`** | **1** | **audit-oracle parser のみ**（`pow4,x_0` → internal `pow(x_0,4)`） |

| 経路 | 許可演算子表 | `pow4` |
|---|---|---|
| `audit_q4_decimal_round_reference` emit | §3.4.1 **のみ** | **禁止**（emit してはならない） |
| `audit_parse_prefix_component` / oracle | §3.4.1 **+** `pow4` unary | 許可（F2） |

**Q4 emit 後 reparse 失敗時**: `q4_emitted_infix` を §3.4.2 `prefix_to_sympy_infix` + §3.4.1 arity で再解析し、
未知演算子・arity 不一致・`InvalidPrefixExpression` のとき **`q4_construction_completed=false`**、
`q4_construction_failure_reason=UnparseableEmittedOperator` → **`execution_failure`**（監査は続行可；当該ペアは non-diagnostic）。

#### 3.4.8 n-ary multi-component serialization

| 項目 | 凍結値 |
|---|---|
| system separator | ASCII pipe `|`（byte `0x7c`） |
| component prefix 連結 | `nodes = tree.prefix().split("|")`；各 component を `,|,` で join 後 split |
| rescale 前処理 | production `Scaler.rescale_function` と同一の `nodes[dim] = f"mul,{1/scale[dim]},"+...` 規則 |
| `word_to_infix` | `env.word_to_infix(prefix, is_float=False, str_array=False)` |

#### 3.4.9 Q4 parity fixtures

| ID | 入力 | 期待 |
|---|---|---|
| **Q4-R1** | E1 prefix `mul,0.04598,x_0` | 丸め後 SymPy expr が `0.0460*x_0` と同値；emit token に `0.0460` |
| **Q4-R2** | `mul,10.0,x_0` | `10.0*x_0` 同値 |
| **Q4-R3** | `pow2,div,mul,10.0,x_0,10.0` | 構築成功；compound power arity 保持 |
| **Q4-R4a** | infix `(1/3)*x_0`（Rational） | 丸め後も **Rational** `x_0/3`；**Float atom `0.3333` は出現しない**；Rational prefix は `mul,1,pow,3,-1` |
| **Q4-R4b** | E1 prefix `mul,0.33333,x_0`（decimal Float leaf） | 丸め後 SymPy expr が `0.3333*x_0` と同値；emit token に **`0.3333`** |
| **Q4-NARY-3** | §3.4.6 の `sp.Add(x_0,x_1,x_2)` / `sp.Mul(2,x_0,x_1)` | prefix が `add,add,...` / `mul,mul,...` と一致 |


**Q4-R4a / Q4-R4b 分離理由**: Float-only Q4 rounder は `Rational(1,3)` を変更しない。
decimal `0.33333` のみが四桁 Float 丸めの対象である。

#### 3.4.10 E1 vs Q4(E1) SymPy canonical oracle（非循環）

| 項目 | 凍結値 |
|---|---|
| 左辺 | E1 から §3.4.2–3 で得た SymPy expr（round 前） |
| 右辺 | `q4_sympy_expr_canonical`（手順 3 出力） |
| 判定 | `simplify(lhs - rhs, expand=True) == 0` |
| 用途 | `e2_identity_fallback_candidate` の「E1 not equivalent to Q4」条件 |
| 禁止 | production simplifier tree / E2 を入力に使うこと |

### 3.5 統一 numeric parser と独立 equivalence oracle

#### 3.5.1 `audit_rational_parse`

| 規則 | 内容 |
|---|---|
| 対象 | numeric leaf の **元トークン文字列** |
| 変換 | `sympy.Rational(token_string)` — binary float 経由禁止 |
| 失敗 | `completed=false` → `execution_failure` |

#### 3.5.2 二参照 oracle

| 呼び出し | 左辺 | 右辺 | 保存 prefix |
|---|---|---|---|
| **E1-original** | E1 emitted infix | **元 truth** 成分 infix | `e1_oracle_*` |
| **E2–`Q4`** | E2 emitted infix | **`q4_emitted_infix`** | `e2_oracle_*` |

**oracle 結果スキーマ**:

| フィールド | 定義 |
|---|---|
| `completed` | parse/timeout/nonfinite/exception なく正常終了 |
| `analytic_equivalent` | analytic 部分が完了し同値 |
| `numeric_equivalent` | numeric grid が完了し同値 |
| `equivalent` | **`analytic_equivalent AND numeric_equivalent`**（`completed=true` のときのみ） |

| 項目 | 凍結値 |
|---|---|
| Analytic | `simplify(expand=True)` exact rational |
| Numeric grid | $`x_j \in \{0.01, 0.1, 0.5, 1.0, 2.0\}`$ 直積、$`t \in \{0, 5, 10\}`$ |
| `atol` / `rtol` | `1e-8` / `1e-8` |
| External oracle timeout | `30.0` 秒 / 呼び出し |

**pointwise finite 要件**（numeric 段）:

| 手順 | 規則 | 失敗時 |
|---:|---|---|
| 1 | 変数集合を truth / candidate 両 tree から決定論的抽出（`x_k` 昇順） | `completed=false`, `failure_reason=ParseError` |
| 2 | grid = $`\prod_{x_j}`$ ORACLE_X_GRID × ORACLE_T_GRID（直積；§13.1 凍結値） | — |
| 3 | 各 grid 点で `float(truth_expr.subs(...))` と `float(cand_expr.subs(...))` を評価 | いずれかが nonfinite（NaN/Inf）→ `completed=false`, `numeric_equivalent=false`, `failure_reason=NonFinite` |
| 4 | 全点で $`|truth - cand| \le atol + rtol \times |truth|`$（$`atol=rtol=10^{-8}`$） | 1 点でも超過 → `completed=true`, `numeric_equivalent=false` |
| 5 | 全点合格かつ analytic 合格 | `equivalent=true` |

| 事象 | `completed` | `equivalent` | outcome 分類 |
|---|---|---|---|
| parse / arity / rational token 失敗 | false | false | `execution_failure` |
| SIGALRM oracle timeout | false | false | `execution_failure` |
| 未処理 exception | false | false | `execution_failure` |
| analytic 非同値（numeric 未実行または失敗） | true | false | `semantic_drift` |
| analytic 同値・numeric 非同値 | true | false | `semantic_drift` |
| nonfinite grid 点 | false | false | `execution_failure` |

**禁止**: `completed=true`, `equivalent=false` を `execution_failure` に分類しない（`semantic_drift` を使用）。

**G1 confirmatory-only 集計**: `call_log.jsonl` の counted 行から **`condition NOT IN {D2}`** の行のみを G1 に使用する。D2 の 2,640 行は **G_grand** のみに加算する。

#### 3.5.3 `original_vs_q4_numeric_max_abs_error`

元 truth infix と `q4_emitted_infix` の §3.5.2 同一 grid 上の max abs error。
`q4_construction_completed=true` のときのみ。primary 使用 **禁止**。

### 3.6 Simplifier 実装契約（Stage A）

- `expand=False`, `resimplify=False`
- SymPy `parse_expr(evaluate=True)` → `round_expr(decimals=4)` → **production `sympy_to_prefix`**
- **internal 1 秒 timeout** は `except TimeoutError: pass` で握り潰され、**入力 tree を返し得る**
- **external frozen timeout** = `5.0` 秒
- **E2 raw==E1 raw だけでは internal timeout を証明しない**（§2.2 `e2_identity_fallback_candidate` を使用）

### 3.7 Serialization / prefix dialect

各段で **raw prefix** と **emitted infix** を保存。
`neg` ノード明示処理；truth は `pow2` 入れ子；production `env.word_to_infix` と同一 API。

### 3.8 Reachability fixtures（B3；closure 必須）

| ID | 種別 | 凍結内容 | 期待 |
|---|---|---|---|
| **REACH-SFN-1** | hand algebraic | **original_truth** infix: `2*x_0**2/(1+x_0**2)`；**E2 readout** infix（synthetic）: `4*x_0**2/(2+2*x_0**2)` | E1≡original_truth、E2≡Q4(E1)、**`hill_form=false`** |
| **REACH-PRESERVED-1** | hand algebraic | infix: `x_0**2/(1+x_0**2)` | E1≡truth、E2≡Q4(E1)、**`hill_form=true`** |
| **REACH-UNS-1** | synthetic decision grid | **exactly 1,320** unique `pair_id` rows；各 row **fully diagnostic** かつ `hill_form=true`；**すべての validity gate PASS** | primary **unsupported** 分岐到達 |
| **REACH-SUP-1** | synthetic decision grid | **exactly 1,320** unique `pair_id` rows：**1** fully diagnostic SFN（REACH-SFN-1 相当）**+ 1,319** fully diagnostic `preserved`；**すべての validity gate PASS** | primary **supported** 分岐到達 |
| **REACH-DRIFT-E2** | synthetic | E2≢Q4(E1) | `semantic_drift` |
| **REACH-Q4FAIL-1** | synthetic | Q4 構築失敗 | `execution_failure` |
| **REACH-IDENT-FALLBACK-1** | synthetic | E2 raw==E1 raw かつ E1≢Q4(E1) | `e2_identity_fallback_candidate=true` → `execution_failure` |
| **REACH-PARSE-1** | synthetic | `classifier_parse_valid=false` | `execution_failure`（順位 2） |
| **REACH-RESCALE-1** | synthetic | `rescale_incomplete=true`（§5.2） | `execution_failure` |
| **REACH-POW-COMP-1** | prefix | `pow2,div,mul,10.0,x_0,10.0` | Q4 構築成功 |

**REACH preflight と counted-call ledger の分離**:

- REACH-* fixture 検証呼び出しは **post-freeze preflight test** として実行する。
- これらは **audit invocation の counted-call ledger に含めない**（§8.1）。
- **C_q4** の P11 呼び出しは confirmatory として **counted**（§8.3）。

**G_impl**（§10）: full confirmatory 実行前に上表 **および** post-freeze **F1, F2, F4, F5, F6, F7, F8** acceptance evidence が PASS すること。

---

## 4. データセットとコーパス

### 4.1 凍結コーパス

```python
corpus = generate_corpus(
    variants={"train": 30},
    n_points=150,
    t_span=(0.0, 10.0),
    seed=61001,
    trajectory_seed=61002,
    rtol=1e-8,
    atol=1e-10,
    minimum_variance=1e-5,
    maximum_abs_state=100.0,
)
```

| 項目 | 凍結値 |
|---|---|
| split | **`train` のみ** |
| 系数 | **240** 系（8 族 × 30） |
| 成分数 | **510** |
| `rejection_rate` | ≤ **0.30** |
| `corpus_hash` | `corpus["fingerprint"]` lowercase hex |
| `fingerprint_bytes` | `json.dumps(fingerprint_payload, sort_keys=True).encode()`（Python 3.10 既定） |
| G_corpus | `SHA256(fingerprint_bytes) == corpus_hash` |

`system_id` = source record verbatim（例: `R01_train_d61001_000`）。
`source_variant_index` 0..29；`tier_index = source_variant_index % 3`；Hill 指数 `(1,2,4)[tier_index]`。

**系順序**: コーパス `records` の `(family, system_id)` 辞書順（family は R01→R08）。

### 4.2 Scale 設計

| 区分 | isotropic `traj_scale` | 用途 |
|---|---|---|
| **Primary grid** | `{0.1, 0.5, 1.0, 2.0}` | confirmatory |
| **Stress** | `{5.0}` | D2 descriptive |

`feature_scale = 1`；primary grid は全成分の決定論的直積。
scale token 文字列は **JSON 浮動小数点の shortest round-trip**（例: `0.1`, `0.5`, `1.0`, `2.0`, `5.0`）。
`pair_id` 内 `scale={scale}` はこの token を verbatim 使用する。

### 4.3 N1 負対照（完全 inline）

| 項目 | 凍結値 |
|---|---|
| 母集団 | 全 **510 成分** |
| 成分キー | `(system_id, component_idx)` |
| canonical_key_string | `audit_negative_seed=61004|system_id={system_id}|component_idx={component_idx}` |
| digest | `SHA256(UTF-8(canonical_key_string))` |
| 選択 | digest 昇順 **先頭 100 成分** |
| 係数集合 | `COEFFS = [1, 2, 3, 5, 7]` |
| 係数選択 | `c = COEFFS[int.from_bytes(digest[:8], "big") % 5]` |
| `negative_id` | `negative_sha256:{digest_hex}` |
| prefix テンプレート | `add,{E_prefix...},{c}` |
| infix テンプレート | `(({E_infix})+({c}))` |
| 代数制約 | E0 構築前に **簡約・約分・定数畳み込み禁止** |
| G_n1 成功条件 | 100/100 で oracle **`completed=true` かつ `equivalent=false`** |

**representative fixture**（`system_id=R01_train_d61001_000`, `component_idx=0`）:

```text
canonical_key_string=audit_negative_seed=61004|system_id=R01_train_d61001_000|component_idx=0
sha256=ce6d15ac5f359552092e79614df18a4f743cead7cdf6454fefd79d3455888bc8
selected_c=3
negative_id=negative_sha256:ce6d15ac5f359552092e79614df18a4f743cead7cdf6454fefd79d3455888bc8
```

### 4.4 Quantization stratum 規則

**`fractional_digit_count(token)`** — numeric leaf **raw token 文字列**に適用:

| 手順 | 規則 |
|---:|---|
| 0 | token に `e` または `E` が含まれる → **exponent token**（§4.5 で abort） |
| 1 | 先頭の `+` / `-` を除去（符号は桁数に含めない） |
| 2 | `.` が無い → **0** |
| 3 | 元 token を `.` で分割；**小数部 substring** のみ対象 |
| 4 | 小数部の **末尾ゼロを除去**（`rstrip('0')`） |
| 5 | 残余文字数 = `fractional_digit_count` |

**成分 stratum**: いずれか leaf で count > **4** → `quantization_active`；else `quantization_neutral`。

### 4.5 Pre-pair reproducibility gate `G_stratum`（§10）

**ペア処理開始前**に、凍結コーパスを再生成し次を検証する:

| 検査 | 期待 | 不一致時 |
|---|---|---|
| strict-Hill 成分数 | **330** | **abort**（registration 開始不可） |
| `quantization_active` 成分 | **46** | **abort** |
| `quantization_neutral` 成分 | **284** | **abort** |
| 全 numeric leaf の exponent token（`e`/`E`） | **0 件** | **abort** |

**重要**: exponent token の存在は **コーパス/serialization drift** を示す。
個別ペアを `construction_incomplete` に落とさず、**監査全体を abort** する。

---

## 5. Scaler 構築

**production パス**: `SymbolicTransformerRegressor(params=None)` →
`Scaler(time_range=[1, 10], feature_scale=1, rescale_features=True)`。

```python
time = np.linspace(0.0, 10.0, 150)
trajectory = np.full((150, d), s, dtype=float)
scaler.fit(time, trajectory)
```

| assert | 期待値 |
|---|---|
| `time_scale` | 9 |
| `time_shift` | 1 |
| `a_t` | 0.9 |
| `b_t` | 1.0 |
| `rescale_features` | true |

### 5.2 `rescale_incomplete` 凍結条件

production `Scaler.rescale_function` が **入力 tree を未変換で返す** 経路は **次の 2 つのみ**:

| # | 条件 | 検出 |
|---:|---|---|
| 1 | `len(nodes) > len(scale)`（multi-component system で component 数超過） | 返却 tree が入力 tree と **同一**（推奨: Python `rescaled_tree is input_tree`） |
| 2 | 変数 `x_k` の `k >= len(scale)`（index が scale 外） | 同上 |

**禁止**: 上記 2 条件以外の catch-all 経路を `rescale_incomplete` と定義してはならない。
**禁止**: 返却 tree の lexical/algebraic 等価性チェックを `rescale_incomplete` 判定に使用してはならない。

`rescale_incomplete=true` → **`execution_failure`**（precedence 2）。

---

## 6. ベースライン、ablation、controls

| 条件 | 説明 | スコア段 | 単位 | `rewrite_id` |
|---|---|---|---|---|
| **B0** | rewrite E0 → rescale → **Q4** → simplify → classify + metrics | E2 | 2,040 pairs（1320+240+480） | `rewrite_sha256:{digest}` |
| **B1** | identity E0 → production identity rescale → **Q4** → simplify | E2 | **510 components** | **`identity`** |
| **B2** | B0 と同 E0/E1；simplifier 省略；**E1-only** 分類 | E1 | 2,040 pairs | `rewrite_sha256:{digest}` |
| **B3** | `compare_formulas(..., skip_cas=False)` | 診断 | 500 strict-Hill pairs | n/a |
| **B4** | 真値 infix を pred にコピー | 指標健全性 | **510 components** | **`truth_copy`** |
| **C_q4** | Q4 参照健全性（§6.1） | Q4 | **7 fixtures** | n/a |

### 6.1 C_q4 — Q4 参照健全性 control

| 項目 | 凍結値 |
|---|---|
| fixture 数 | **7** |
| primitive | P11 のみ |
| **`unit_type`** | **`fixture`** |
| `unit_id` | `q4_fixture_{01..07}` |
| counted-call | **yes**（§8.3） |

| fixture_id | E1 prefix（代表） | 必須検証 |
|---|---|---|
| `q4_fixture_01` | `mul,0.04598,x_0` | SymPy 同値 + token `0.0460` |
| `q4_fixture_02` | `mul,10.0,x_0` | `10.0` 保持 |
| `q4_fixture_03` | `add,1.0,x_0` | 構築成功 |
| `q4_fixture_04` | `pow2,x_0` | 構築成功 |
| `q4_fixture_05` | `pow2,div,mul,10.0,x_0,10.0` | compound power 成功 |
| `q4_fixture_06` | `mul,0.33333,x_0` | 4 桁丸め **`0.3333`**（Q4-R4b 連動；Rational ではない） |
| `q4_fixture_07` | infix `(1/3)*x_0`（Rational；Q4-R4a） | 丸め後 SymPy が **Rational** `x_0/3`；Float `0.3333` **不出現**；prefix `mul,1,pow,3,-1` |

### 6.2 B3 CAS 診断 subset（完全 inline）

| 項目 | 凍結値 |
|---|---|
| 母集団 | `eligibility_layer=strict_hill_primary` の **1,320** primary ペア |
| 順序キー | `pair_id` 文字列中の digest 部分（`pair_sha256:` 以降）の **昇順** |
| 選択 | 先頭 **500** ペア |
| primitive | P10 `compare_formulas_cas` |
| timeout | **60.0** 秒 / 呼び出し |
| `skip_cas` | **false** |
| terminal | `diagnostic_complete` または `diagnostic_failed` |

---

## 7. シード、typed unit ID、決定論

| 用途 | キー | 値 |
|---|---|---|
| GRN LHS / data seed | `audit_data_seed` | 61001 |
| Trajectory IC seed | `audit_trajectory_seed` | 61002 |
| Rewrite 生成 | `audit_rewrite_seed` | 61003 |
| N1 選択 | `audit_negative_seed` | 61004 |
| B3 CAS subset | `audit_cas_subset_seed` | 61005 |

**Allowed `unit_type` tokens**（**4 つのみ**）: `component`, `pair`, `negative`, **`fixture`**.

**Resume / dedup キー**: `(primitive, condition, stage, unit_type, unit_id)`.

| 操作 | `unit_type` | `unit_id` |
|---|---|---|
| R1/R2/P12 | `component` | `component_id` |
| B0/B1/B2/B4/D2 | `pair` | `pair_id` |
| B3 | `pair` | `pair_id` |
| N1 | `negative` | `negative_id` |
| **C_q4** | **`fixture`** | **`q4_fixture_{01..07}`** |

**`component_id`**: `component_sha256:{SHA256(UTF-8(component_key))}`；
`component_key=corpus_hash={h}|system_id={sid}|component_idx={idx}`。

**`pair_id`**: `pair_sha256:{SHA256(UTF-8(pair_key))}`；
`pair_key=corpus_hash={h}|system_id={sid}|component_idx={idx}|scale={scale}|rewrite_id={rewrite_id}`。

---

## 8. 計算上限と counted-call 表

### 8.1 Counted call の定義

§8.2 named primitive への **1 回の論理呼び出し**。メモ化でも `call_log.jsonl` に 1 行。

**ledger 外**（counted に **含めない**）:

- REACH-* preflight fixture 検証（§3.8）
- resource monitor の directory byte 走査
- resume identity 比較・manifest 読取

**ledger 内**（counted）:

- 全 confirmatory 行（§8.3）および D2（§8.4）
- **C_q4** の P11（**7** 回）

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
| P11 | `q4_decimal_round_reference` |
| P12 | `quantization_stratum_assign` |

### 8.3 Confirmatory operations table

| 行 | Primitive | Condition | 単位 | 回数 |
|---|---|---|---|---:|
| R1 | P1 | registration | components | 510 |
| R2 | P2 | registration | components | 510 |
| R3 | P12 | registration | components | 510 |
| B0a–B0h | P3,P5,P11,P6,P7×2,P8,P9 | B0 | pairs | 2,040 each |
| B1a–B1h | P4,P5,P11,P6,P7×2,P8,P9 | B1 | components | 510 each |
| B2a–B2b | P8,P9 | B2 | pairs | 2,040 each |
| B4a–B4b | P8,P9 | B4 | components | 510 each |
| C_q4 | P11 | C_q4 | fixtures | **7** |
| B3 | P10 | B3 | pairs | 500 |
| N1 | P7 | N1 | negatives | 100 |
| | | | **Confirmatory total** | **27,637** |

算術: $`1{,}530 + 16{,}320 + 4{,}080 + 4{,}080 + 1{,}020 + 7 + 600 = 27{,}637`$。

### 8.4 Descriptive tier

| 行 | 内容 | 追加 calls |
|---|---|---:|
| D1 | non-strict filtered aggregation | **0** |
| D2 | strict-Hill stress `5.0` B0 path（8 primitives/pair） | **2,640** |
| | **Grand maximum** | **30,277** |

D2: $`330 \times 8 = 2{,}640`$。

### 8.5 Resource ceiling と abort 計測

| 項目 | 上限 | 計測 |
|---|---|---|
| GPU / decode | **0** | — |
| Elapsed wall | ≤ **18,000** 秒 | `time.monotonic() - audit_start_monotonic` |
| Confirmatory counted calls | **27,637** | `call_log.jsonl` 行数（G1） |
| Grand counted calls | **30,277** | confirmatory + D2（G_grand） |
| Output directory bytes | ≤ **1,200,000,000** bytes | **decimal 1.2 GB** 規約（$`1.2 \times 10^9`$） |

**byte 規約**: 本監査は **decimal GB** を使用する。$`1.2\ \mathrm{GB} = 1{,}200{,}000{,}000`$ bytes。
binary GiB（$`1.2 \times 2^{30}`$）は **使用しない**。

**計測タイミング**（各 primitive 実行前後、各 artifact 書込前後）:

1. `elapsed_sec = time.monotonic() - audit_start_monotonic`；`elapsed_sec > 18000` → **abort**
2. `dir_bytes = recursive_sum_file_sizes(output_dir)`；`dir_bytes > 1200000000` → **abort**
3. abort 時は `audit_manifest.json` に `abort_reason`, `elapsed_sec`, `dir_bytes` を記録し **非ゼロ exit**

**G1** は confirmatory ceiling のみ。**G_grand** は D2 込み grand ceiling。

---

## 9. 除外・失敗ポリシー

| 事象 | Outcome |
|---|---|
| Truth / rewrite / E0 / E1 構築・parse 不能（simplifier 前） | `construction_incomplete` |
| `q4_construction_completed=false` | `execution_failure` |
| **`e2_identity_fallback_candidate=true`** | `execution_failure` |
| **`classifier_parse_valid=false`** | `execution_failure` |
| **`rescale_incomplete=true`**（§5.2 の 2 条件のみ） | `execution_failure` |
| External oracle / CAS / simplifier timeout | `execution_failure` |
| E1/E2 oracle `completed=false` | `execution_failure` |
| E1 または E2 oracle `completed=true`, `equivalent=false` | `semantic_drift` |
| E2≠truth だが E2≡`Q4(E1)` | **not** `semantic_drift` |
| `original_vs_q4_numeric_max_abs_error` > 0 のみ | 記述のみ |
| G_stratum exponent token | **abort**（ペア outcome なし） |

**禁止**: Q4 失敗・non-diagnostic 行を分母から除外すること。

---

## 10. Validity gates

**評価順序**: G_corpus → **G_eligibility** → **G_stratum** → G0 → G4 → G1 → G_grand → **G_impl** → **G_q4ref** → G_n1 → **G_b1** → G_b4 → linear controls → G_term → primary rule

| Gate | 条件 | FAIL 時 |
|---|---|---|
| **G_corpus** | §4.1（240/510；rejection≤0.30；fingerprint 一致） | abort |
| **G_eligibility** | §2.5.1（330/60/120；各成分がちょうど 1 層） | **abort** |
| **G_stratum** | §4.5（330 strict-Hill；46/284；exponent token 0） | **abort** |
| G0 | §5 Scaler assert | abort |
| G4 | sealed-path access guard 試行 0 | undecidable |
| **G1** | confirmatory counted calls ≤ **27,637** | abort |
| **G_grand** | grand counted calls ≤ **30,277** | abort |
| **G_impl** | §3.8 REACH-* **すべて** PASS；post-freeze **F1, F2, F4, F5, F6, F7, F8** acceptance PASS（§16） | undecidable |
| **G_q4ref** | C_q4 **7/7** 成功；`q4_fixture_01` 丸め；`q4_fixture_06` → `0.3333`；`q4_fixture_07` Rational 不変（Q4-R4a） | undecidable |
| G_n1 | N1 **100/100** `completed=true` かつ `equivalent=false` | undecidable |
| **G_b1** | B1 **510/510** で `control_pass_row=true`（§2.5.5）；terminal ∈ {`control_pass`,`control_failure`}；**`unknown` 0** | undecidable |
| G_b4 | B4 **510/510** `valid=true` かつ `canonical_exact=1` | undecidable |
| G_ctrl_cov | 線形 **480/480** parse+metrics valid | undecidable |
| G_ctrl_fp | 線形 FP rate = 0 | undecidable |
| G_ctrl_lin | linear canonical noninvariance = 0 | undecidable |
| G_term | strict-Hill **1,320/1,320** terminal outcome ちょうど 1 つ；**`unknown` 0** | undecidable |
| G_inc | `construction_incomplete` ≤ 5% | undecidable |

**G_b1 / G_impl は counted call を追加しない**（既存 B1 行の conjunct 検査のみ）。

---

## 11. Sealed-path access guard

`configs/gpu_run5/base.yaml` から派生:

| Config キー | 凍結値 |
|---|---|
| `output_root` | `results/runs` |
| `family_holdout.sealed_test_families` | `[R07, R08]` |

**path normalization**:

1. repo root 相対なら absolute 化
2. `norm_abs = os.path.normpath(absolute_path)`
3. `real_abs = os.path.realpath(norm_abs)`
4. **`norm_abs` と `real_abs` の両方** を matcher へ渡す

**deny matcher**（campaign-relative；glob 列挙禁止）:

`output_root_abs` 下で先頭 component が `gpu_run5_` で始まるとき:

1. `test`, `sealed`, `final_test` が出現した directory **自身と全子孫** を deny
2. `phase8` が `predictions` より前に出現したとき、その `predictions` **自身と全子孫** を deny

**intercept API**: `builtins.open`；`os.open/stat/listdir/scandir`；
`pathlib.Path.open/stat/iterdir/glob/rglob`。

**mandatory install 順序**:

| プロセス | install タイミング | 禁止 |
|---|---|---|
| parent audit (`run_audit`) | `SealedPathGuard.install()` を **いかなる counted primitive / corpus 処理より前** | guard なしで `open` / `os.stat` 等 |
| simplifier child (`simplifier_worker.py`) | **ODEFormer / simplifier import より前** に `guard.install()` | child 内 task code が guard なしで実行 |
| その他 subprocess | ファイル I/O を行うなら同一規則 | — |

**deny-on-attempt**: matcher が deny した path への access は **`PermissionError` で即 block** し、
`AccessAttempt(attempted_operation, attempted_path_norm, attempted_path_real)` を親 `attempts` へ append。

**child side-channel artifact**:

| 項目 | 凍結値 |
|---|---|
| 親 run 内ファイル名 | `guard_attempts_side_channel.jsonl`（`output_dir` 直下） |
| child 一時ファイル | `GPU_RUNmultiAI/.runtime/guard_attempts_side_channel.jsonl` |
| 行スキーマ | `{"attempted_operation","attempted_path_norm","attempted_path_real"}`（UTF-8 JSONL） |
| merge タイミング | **G4 評価前**に `load_guard_attempts` → `guard.extend_child_attempts` |
| child 終了時 | worker は side channel へ append 後、親へ `guard_attempts` を返す |

禁止 access 試行 **0 件**（G4）。既存 sealed artifact の存在だけでは FAIL にならない。

---

## 12. 成果物と resume

### 12.1 成果物一覧

| 成果物 | 必須内容 |
|---|---|
| `audit_manifest.json` | §12.2 |
| `pair_results.csv` | §12.3 |
| `registration_truth.json` | P1 510 成分 truth / classify 登録 |
| `registration_rewrites.json` | P2 510 rewrite 行 |
| `quantization_stratum.json` | P12 510 成分 `{component_id, quantization_stratum}` |
| `q4_reference_controls.json` | C_q4 7 fixtures（§6.1） |
| `reachability_evidence.json` | §3.8 REACH-*（post-freeze G_impl） |
| `call_log.jsonl` | counted-call ledger（§12.4） |
| `stage_cache.jsonl` | stage primitive メモ（§12.5） |
| `pair_cache.jsonl` | 完了 pair 行スナップショット（§12.5） |
| `guard_attempts_side_channel.jsonl` | child guard deny 試行（§11） |
| `fingerprint_payload.json` | corpus fingerprint verbatim |
| `fingerprint_bytes.bin` | `json.dumps(fingerprint_payload, sort_keys=True).encode()` の **exact bytes** |
| `b3_results.json` | B3 500 行 CAS 診断 |
| `b4_results.json` | B4 510 行 metric sanity |
| `condition_summary.json` | primary partition 比率・diagnostic coverage |
| `equivalence_oracle.json` | B0+D2 oracle 詳細 |
| `negative_controls.json` | N1 100 行 |
| `deviation_log.md` | 凍結後プロトコル逸脱 |
| `abort_manifest.json` | resource ceiling abort 時のみ（`abort_reason`, `elapsed_sec`, `dir_bytes`） |

### 12.2 `audit_manifest.json` 必須フィールド

`audit_id`, `plan_hash`, `commit`, `status`, `resume_identity`（§12.6）, 全シード（§7）,
`corpus_hash`, `corpus_system_count`, `corpus_component_count`, `corpus_rejection_rate`,
`fingerprint_payload`（verbatim dict）, `fingerprint_payload_path`, `fingerprint_bytes_path`,
`fingerprint_payload_bytes_hash`, `source_hashes`（§13.2 sorted inventory）,
`access_guard_attempts`, `confirmatory_call_ceiling=27637`, `grand_call_ceiling=30277`,
`elapsed_wall_ceiling_sec=18000`, `output_dir_byte_ceiling=1200000000`, `byte_convention=decimal_gb`,
`primitive_table`, `cli_args_normalized`, `dependency_versions`, `environment`, `runtime_provenance`,
`oracle_timeout_sec`, `q4_timeout_sec`, `simplifier_subprocess_timeout_sec`, `cas_timeout_sec`,
`validity_gates`, `primary_decision`, `confirmatory_calls`, `descriptive_calls`.

### 12.3 `pair_results.csv` 必須列（順序固定）

`condition`, `pair_id`, `component_id`, `system_id`, `component_idx`, `scale`, `rewrite_id`,
`eligibility_layer`, `partition_scope`, `stratum`, `outcome_category`, `is_fully_diagnostic`, `failure_reason`,
`rescale_incomplete`, `formula_metrics_valid`,
`q4_construction_completed`, `q4_emitted_infix`, `q4_sympy_expr_canonical`, `q4_construction_failure_reason`,
`e2_identity_fallback_candidate`,
`e1_oracle_completed`, `e1_oracle_equivalent`, `e1_analytic_equivalent`, `e1_numeric_equivalent`, `e1_oracle_failure_reason`,
`e2_oracle_completed`, `e2_oracle_equivalent`, `e2_analytic_equivalent`, `e2_numeric_equivalent`, `e2_oracle_failure_reason`,
`e0_status`, `e1_status`, `e2_status`,
`e0_prefix_raw`, `e1_prefix_raw`, `e2_prefix_raw`,
`e0_infix`, `e1_infix`, `e2_infix`,
`e2_infix_pre_classifier`, `classifier_parse_valid`, `classifier_parse_failure_reason`, `hill_form`,
`canonical_exact`, `exponent_aware_skeleton_exact`,
`original_vs_q4_numeric_max_abs_error`, `quantization_stratum`, `control_pass_row`（B1 のみ）.

### 12.4 `call_log.jsonl` 行スキーマ

`primitive`, `condition`, `stage`, `unit_type`, `unit_id`, `status`, `duration_sec`, `rewrite_id`（該当時）。
resume dedup キー: `(primitive, condition, stage, unit_type, unit_id)`。

### 12.5 JSONL durability（`call_log.jsonl`, `stage_cache.jsonl`, `pair_cache.jsonl`, `guard_attempts_side_channel.jsonl`）

| 規則 | 凍結値 |
|---|---|
| 書込 | 各行 `json.dumps(..., sort_keys=True) + "\n"` を **append** |
| 耐久 | 各行書込後 **`flush()`**（可能なら `os.fsync`） |
| 読込 | UTF-8 で splitlines；**空行は skip** |
| trailing partial line | 最終行が `json.loads` 不能なら **無視**（未完了行として再実行時に上書きされ得る） |
| duplicate key | resume 時に同一 5-tuple / `pair_id` / `cache_key` が重複したら **abort** |

`stage_cache.jsonl` 行: `{"cache_key","payload"}`（`cache_key = primitive|condition|stage|unit_type|unit_id`）。
`pair_cache.jsonl` 行: 完了 `pair_results` 行の superset（`pair_id` 必須）。

### 12.6 Resume identity（`--resume` 前に **すべて一致必須**；不一致は reuse 前に **abort**）

| フィールド | 凍結値 |
|---|---|
| `audit_id` | `c0001_metric_identifiability_audit_v13` |
| `plan_hash` | 本 preregistration SHA256 |
| `commit` | 初回 run の git commit SHA |
| `audit_script_hash` | `scripts/phases/gpu_runmultiai_c0001_metric_audit.py` SHA256 |
| `config_hash` | `configs/gpu_run5/base.yaml` SHA256 |
| `source_hashes` | §13.2 **sorted** inventory（全エントリ一致） |
| `corpus_hash` | 凍結コーパス fingerprint |
| `fingerprint_payload_path` | `output_dir/fingerprint_payload.json` |
| `fingerprint_bytes_path` | `output_dir/fingerprint_bytes.bin` |
| `fingerprint_payload_bytes_hash` | `SHA256(fingerprint_bytes)` == `corpus_hash` |
| `seeds` | §7 全 5 シード |
| `primitive_table` | §8.2–§8.3 順序付き表 |
| `cli_args_normalized` | 初回 semantic 引数（`--resume`, `--fail-if-exists` **除外**） |
| `oracle_timeout_sec` | 30.0 |
| `q4_timeout_sec` | 10.0 |
| `simplifier_subprocess_timeout_sec` | 5.0 |
| `cas_timeout_sec` | 60.0 |
| `confirmatory_call_ceiling` | 27637 |
| `grand_call_ceiling` | 30277 |
| `dependency_versions` | python, numpy, scipy, sympy, torch（存在時）, os, cpu |
| `environment` | `LANSR_TED_TIMEOUT_SEC=10`, `LANSR_SYMPY_TIMEOUT_SEC=10`, `LANSR_SYMPY_MAX_NODES=40` |
| `runtime_provenance` | `os`, `cpu` |

**semantic CLI identity**: resume 時は初回と **同一 semantic 引数集合** を要求する。

---

## 13. 実行コマンドと provenance

### 13.1 環境

| 項目 | 凍結値 |
|---|---|
| Python | 3.10.x |
| CPU | `--allow-cpu` 必須 |
| `LANSR_TED_TIMEOUT_SEC` | **10** |
| `LANSR_SYMPY_TIMEOUT_SEC` | **10** |
| `LANSR_SYMPY_MAX_NODES` | **40** |
| `oracle_timeout_sec` | 30.0 |
| `q4_timeout_sec` | 10.0 |
| `simplifier_subprocess_timeout_sec` | 5.0 |
| `cas_timeout_sec` | 60.0 |

### 13.2 Source hashes（manifest 必須；sorted recursive inventory）

実装は **初回 run 時** に下表を再計算し、不一致なら abort する。
手動編集は監査再現用の **観測スナップショット** であり、runtime が常に再計算する。

| パス（repo-relative） | SHA256（content commit 観測） |
|---|---|
| `configs/gpu_run5/base.yaml` | `2ffee235ff1403ce62961cdd35e022c01fa56b2772785f81f60e08e009d006d2` |
| `scripts/phases/gpu_runmultiai_c0001_metric_audit.py` | `5dd8c6b5f3153bed4bc7b441c1e9f6997d5372657b26399acc5e9394fbb3b46f` |
| `src/evaluation/gpu_run5_structure.py` | `af63fa853badf40c7ed50867567b7f54d21e51cf9dcc97d93b1d277a122b9443` |
| `src/gpu_run4/formulas.py` | `3a25ea3e3cc19f7c6bba0fd6d7446ad705fd57088ada4cbd61fbcd10c115a8ed` |
| `src/gpu_run4/ted.py` | `18fd3b67fc2824a2323f21a405f6fcaa2b9b7c51baa2ab56cee9b2095ccfcb04` |
| `src/gpu_run5/evaluation.py` | `cb13acee2797a1c7a31c039513f23384f9943268ad5fa31ae21addb8540eb988` |
| `src/gpu_run5/grn.py` | `0daac34f72753add65662eed3a09b3a897cd585c1826a2547f5c48772c89bdfb` |
| `src/gpu_runmultiai/__init__.py` | `8971ef45ad491bff849139205aa28ab5ee9f9998a8010e6973a35ef15dd57c7a` |
| `src/gpu_runmultiai/audit.py` | `6e17c8a0f0c300a13ed895466717fdd625d34e5491f247d3f882a5defcfe5c9b` |
| `src/gpu_runmultiai/calls.py` | `9c4439d2c55ab3c3c6dc4e5f460e14939e36f2289c9c627d821e3aeca8f7429d` |
| `src/gpu_runmultiai/config_paths.py` | `8f9b00a47cc7d1e231c5df2566b5b956e557fbdee303f3bfe97f4ca2d6a50e7c` |
| `src/gpu_runmultiai/constants.py` | `7fdd9beb376079dd1c1c3734b3f5fceca4239e794e003dc79d77f330a2ac6b80` |
| `src/gpu_runmultiai/controls.py` | `1146654498951e0a910f605c5934dd027add3d7ab636ee40dfd813e590400e69` |
| `src/gpu_runmultiai/corpus.py` | `d5af1d188170a9c2e3ef2273975459ae5720a743efa91ba2dd0ea71735bb81cc` |
| `src/gpu_runmultiai/guard_side_channel.py` | `d918bcbed0fd7d3aee02282fd1253e0eed8446b4796a9c1377a1bd227e83f835` |
| `src/gpu_runmultiai/ids.py` | `b82bcb0c660e457acac56f76fdaedce350e17a8bbbee19043ece11435741f2af` |
| `src/gpu_runmultiai/invariants.py` | `9d93c3d9dc6c8736fcca3ce872e7faa8ddda6d7c4ce584ca600c91e7128c8b14` |
| `src/gpu_runmultiai/manifest.py` | `42948f603fe035441d9b2983aa5cba4cbeb7279aab76b4de9aec593f39d2c33e` |
| `src/gpu_runmultiai/odeformer_runtime.py` | `43447e7945f10d812b48fa8615c7ceb8e15fa2303e6e1ed89af7451534a4caa1` |
| `src/gpu_runmultiai/oracle.py` | `cc8bed4b09fbed3002900aed0fe1c9d9a9f92992c731127119d81fcdd2f988e6` |
| `src/gpu_runmultiai/outcomes.py` | `32b89f996669ab3081aa2a83649a3813fdfd8cd49c960db2df905cce169ae409` |
| `src/gpu_runmultiai/pipeline.py` | `f4d32500a701069e07652952728716fd37952da3518489b37d4c1614f37cae19` |
| `src/gpu_runmultiai/resources.py` | `c9d2414b27b2cf0fe107c0a83ff2284434001c6369e4c90461c2fd200fffdf61` |
| `src/gpu_runmultiai/rewrites.py` | `d517d9c081f3d69fc27345866e70574136363212921105e06ffcf3e9e6bbb74b` |
| `src/gpu_runmultiai/sealed_guard.py` | `be5eddb343fbbbe2365cf7f807a995a9e69e31ad4df078add48250f56c0dbb39` |
| `src/gpu_runmultiai/serialization.py` | `b4e96e151420a320024fd353c873ee015ba1262122e05359c2ed3c6e9a7fa74a` |
| `src/gpu_runmultiai/simplifier_worker.py` | `a1e91a1c65a1df65679c5e2bafcbd3d1bde69fa4b1517cc96377bc4b4ea1dd27` |
| `src/gpu_runmultiai/stage_cache.py` | `93ec35a5ae488b09ed5e3d926302fa5420cb0680eee15d20a4f6778bd0a09e66` |
| `src/gpu_runmultiai/strata.py` | `2e8bb8a29b55154995ab080f3e199a2fa88e36b3a39931f44369e6a9fceb6ae3` |
| `third_party/odeformer/odeformer/envs/environment.py` | `6e87d9683a1138b231129fa7d1707b06708542df6f6864d4b3249b872b67bd69` |
| `third_party/odeformer/odeformer/envs/generators.py` | `3f7bb5d5f6b27f3c8382946329b9c8baa6e0195c60ce06788719cb0f9273a3cb` |
| `third_party/odeformer/odeformer/envs/simplifiers.py` | `c146bb8b966561b952e6d0f6283003ed3ffa2f4cdfb73efc062ea3991273e6b1` |
| `third_party/odeformer/odeformer/model/sklearn_wrapper.py` | `a4f26e0f2f1c33122c928b410e29488314f1be28724b87d08115048038c9b4de` |
| `third_party/odeformer/odeformer/model/utils_wrapper.py` | `4a3ad6a36d21ad12e166d29797285132396f4cfad2971d67f68a3fa50a979872` |

### 13.3 凍結コマンド（実装後；本タスクでは実行しない）

```bash
python -m compileall -q src scripts tests
export LANSR_TED_TIMEOUT_SEC=10
export LANSR_SYMPY_TIMEOUT_SEC=10
export LANSR_SYMPY_MAX_NODES=40
python scripts/phases/gpu_runmultiai_c0001_metric_audit.py \
  --audit-id c0001_metric_identifiability_audit_v13 \
  --output-dir GPU_RUNmultiAI/cycles/C0001/runs/c0001_metric_identifiability_audit_v13 \
  --audit-data-seed 61001 \
  --audit-trajectory-seed 61002 \
  --audit-rewrite-seed 61003 \
  --audit-negative-seed 61004 \
  --audit-cas-subset-seed 61005 \
  --allow-cpu \
  --oracle-timeout-sec 30.0 \
  --q4-timeout-sec 10.0 \
  --simplifier-subprocess-timeout-sec 5.0 \
  --cas-timeout-sec 60.0 \
  --fail-if-exists
```

**Resume コマンド**（semantic 引数完全再掲；`--resume` と `--fail-if-exists` のみ差分）:

```bash
export LANSR_TED_TIMEOUT_SEC=10
export LANSR_SYMPY_TIMEOUT_SEC=10
export LANSR_SYMPY_MAX_NODES=40
python scripts/phases/gpu_runmultiai_c0001_metric_audit.py \
  --audit-id c0001_metric_identifiability_audit_v13 \
  --output-dir GPU_RUNmultiAI/cycles/C0001/runs/c0001_metric_identifiability_audit_v13 \
  --audit-data-seed 61001 \
  --audit-trajectory-seed 61002 \
  --audit-rewrite-seed 61003 \
  --audit-negative-seed 61004 \
  --audit-cas-subset-seed 61005 \
  --allow-cpu \
  --oracle-timeout-sec 30.0 \
  --q4-timeout-sec 10.0 \
  --simplifier-subprocess-timeout-sec 5.0 \
  --cas-timeout-sec 60.0 \
  --resume
```

---

## 14. 承認チェックリスト

| フィールド | v13 ドラフト |
|---|---|
| primary hypothesis | §1 |
| primary endpoint | §2.1 |
| eligibility_layer / partition_scope | §2.5 |
| Q4 Rational vs Float fixtures | §3.4.7–3.4.8（Q4-R4a/R4b 分離） |
| reachability decision fixtures | §3.8（REACH-SUP-1: 1+1319；REACH-UNS-1: 1320 preserved） |
| rescale early return | §5.2（2 条件 + optional `is`） |
| budgets | §8（27,637 / 30,277；18,000 s；1,200,000,000 bytes） |
| Q4 Rational fixture gate | §6.1 `q4_fixture_07` / §10 G_q4ref 7/7 |
| n-ary fold + audit-oracle pow4 | §3.4.6–3.4.7 |
| truth-side index sets | §2.5.1 G_eligibility |
| guard side channel | §11 / §12.1 |
| gates | §10（G_stratum, G1, G_grand, G_impl, G_b1） |
| frozen_on | **未** |

---

## 15. Post-freeze 実装要件

**F3 は本プロトコル改訂で対応済み**（E2–`Q4` oracle）。G_impl は **次の 7 要件のみ** を名指しする:
**F1, F2, F4, F5, F6, F7, F8**。

---

## 16. Post-freeze 実装要件（凍結後；完全 inline）

| ID | 要件 | 受け入れ基準 |
|---|---|---|
| **F1** | E0 forward を exact decimal token から explicit rational 構築；production rescaling が emit する reciprocal を rounded decimal quotient ではなく rational 式で表現 | 全 primary scale で E1 が **E1-original** analytic **かつ** numeric 同値 |
| **F2** | compound `pow2`/`pow3`/`pow4` operand の prefix tree を arity 保持で解析；token splicing 禁止 | 非対称 nested fixture（例: `pow2,div,mul,10.0,x_0,10.0`）で構築前後の subtree arity が一致 |
| **F4** | round-trip acceptance test が **E1≡truth** を期待 | `test_e0_e1_round_trip_primary_scales` が E1 analytic+numeric 同値を assert |
| **F5** | B1 が production `Scaler.rescale_function` を identity パラメータ（`a_t=1`, `b_t=0`, `scale=1`）で実行 | B1 E1 が oracle-equivalent to truth；identity bypass 禁止 |
| **F6** | B1 に explicit outcome partition；`unknown` 禁止 | 510/510 行が `control_pass` または `control_failure` |
| **F7** | B2 を immutable `pair_id` + E1 フィールドから再構築；B0 E2 フラグのコピー禁止 | B2 分類が E1-only 入力のみから決定 |
| **F8** | B3 component 抽出が shared `|` 分割を使用 | multi-component fixture で正しい成分が抽出される |

---

## 17. 整合性宣言

- 本 v13 は **未凍結**
- 本 v13 の `audit_id` は **`c0001_metric_identifiability_audit_v13`** のみ
- 歴史 preregistration ファイル（v9–v12）は **編集しない**
