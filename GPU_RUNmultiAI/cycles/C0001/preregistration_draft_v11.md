# C0001 事前登録 v11 — メトリック同定可能性監査（自己完結改訂）

- campaign: GPU_RUNmultiAI
- cycle: C0001
- task: C0001-T010
- audit_id: `c0001_metric_identifiability_audit_v11`
- supersedes: `preregistration_draft_v10.md`（未凍結ドラフト；本書が binding 草案）
- 作成日: 2026-09-15
- 状態: **draft v11（未凍結・未承認）**
- binding_plan: null（凍結後に `research_state.md` へ記録）
- amendment_authority: `preregistration_v10_independent_review.md`（B1–B9）；`preregistration_v11_revision_handoff.md`

本書は `.agent/rules/04-preregistration-and-metric-freeze.md` の全フィールドを
**メトリック監査** 向けに具体化した **自己完結** v11 ドラフトである。
v10 independent closure review の B1–B9 を閉じる。
**normative 本文に「v9/v10 と同一」「same as v9 section X」は使用しない。**
歴史文書への参照は §18 のみ。

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
- truth-side **quantization stratum**（`quantization_neutral` / `quantization_active`）は
  **報告次元のみ**であり、分母除外・primary 判定の conjunct ではない。
- Hill 分類と exact-tree / skeleton 回復は **別 endpoint** として報告する。
- **存在ゲートは薄い confirmatory 証拠**である。系統的/prevalence 主張は本監査の範囲外。

**監査限界（B7）**:

- audit-owned Q4 は、production `parse_expr` + `Float.round(4)` + **凍結 `sympy_to_prefix` 規則**（§3.4.6）を
  **意図的に mirror** する。両経路で共有される parse/round/serialize 欠陥は **非可視** になり得る。
- production simplifier は internal 1s timeout を **握り潰し**、入力 tree を返し得る（§3.6）。
  audit Q4 は external-only timeout で **完了失敗**として記録する（§3.4）。
  この **timeout 非対称** により、E2 raw==E1 raw でも internal fallback か正常同値かを timeout だけでは区別できない。
  本監査は `e2_identity_fallback_candidate`（§2.2）で **非 diagnostic** を分類するが、
  **internal timeout を直接主張しない**。

---

## 1. 主仮説（primary hypothesis）— 唯一の仮説規則

**H0001-METRIC（v11）**:
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

| 層 | 成分数 | primary grid ペア | 用途 |
|---|---:|---:|---|
| **strict-Hill primary** | 330 | **1,320** | primary 仮説の固定分母 |
| non-strict Hill-bearing secondary | 60 | 240 | 記述 tier（§4.1） |
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

**`e2_identity_fallback_candidate`（B1）**:

| 項目 | 凍結定義 |
|---|---|
| 判定 | `e2_prefix_raw == e1_prefix_raw`（byte-identical comma-separated prefix 文字列） |
| 追加条件 | E1 が `Q4(E1)` と **SymPy 式レベルで非同値**（§3.4.7 oracle；`q4_sympy_expr_canonical` 使用） |
| 分類 | **`execution_failure`**（precedence 順位 2；`semantic_drift` より前） |
| 禁止 | raw E2==E1 だけで internal simplifier timeout を **主張** すること |
| unsupported 要件 | unsupported 到達には **non-diagnostic ペア（本候補含む）が 0 件** であること |

**固定分母 1,320 ペアの mutually exclusive partition**（各ペアはちょうど 1 つ）:

| Outcome category | 定義 |
|---|---|
| `construction_incomplete` | truth parse、rewrite preverify、E0 構築、**E1 構築または E1 parse 不能**（production simplifier **実行前**） |
| `execution_failure` | `q4_construction_completed=false`、**`e2_identity_fallback_candidate=true`**、**`classifier_parse_valid=false`**、E2 parse 失敗、NaN/Inf、**`rescale_incomplete=true`**（§5.2 全条件）、external simplifier timeout、**E1-original または E2–`Q4` oracle `completed=false`** |
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
| `partition_scope` | §2.5 |

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

### 2.5 非 primary 行の `partition_scope` と terminal 語彙（B5）

**`partition_scope` 凍結値**（`pair_results.csv` 必須列）:

| condition | `partition_scope` | 許可 terminal / control 語彙 | `unknown` |
|---|---|---|---|
| **B0** | `primary` | §2.2 の 5 outcome | **禁止** |
| **B1** | `control` | `control_pass` **または** `control_failure` のみ | **禁止** |
| **B2** | `ablation` | `ablation_pass` **または** `ablation_failure` のみ | **禁止** |
| **B3** | `diagnostic` | `diagnostic_complete` **または** `diagnostic_failed` のみ | **禁止** |
| **B4** | `metric_sanity` | `sanity_pass` **または** `sanity_failure` のみ | **禁止** |
| **N1** | `negative_control` | `negative_reject`（oracle `completed=true` かつ `equivalent=false`）**または** `negative_failed` | **禁止** |
| **C_q4** | `q4_fixture` | `fixture_pass` **または** `fixture_failure` のみ | **禁止** |
| **D2** | `descriptive` | `descriptive_recorded` **または** `descriptive_failed` のみ | **禁止** |

**B1 `control_pass` 定義**: `control_failure` の否定 **かつ** §10 **G_b1** の全 conjunct が true。
**B1 `control_failure`**: G_b1 のいずれかが false。

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
| **B0 primary** | preverified **非自同値 rewrite**（`audit_rewrite_seed=61003`）から full-system analytic E0 | `rewrite_sha256:{digest_hex}` |
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
`parse_expr(evaluate=True)` → `Float.round(4)` → **凍結 `sympy_to_prefix`** を、
**最小非循環参照**として再現する。
production `simplify_tree` またはその返却 tree を **参照・呼び出し・再利用してはならない**。

**凍結 algorithm `audit_q4_decimal_round_reference`**:

| 手順 | 操作 | 失敗時 |
|---:|---|---|
| 1 | E1 prefix を audit-owned `prefix_to_sympy_infix`（§3.4.1）で SymPy 互換 infix へ変換 | `q4_construction_completed=false` |
| 2 | `sympy.parsing.sympy_parser.parse_expr(infix, evaluate=True, local_dict=FROZEN_Q4_LOCAL_DICT)` | 同上 |
| 3 | `audit_round_float_atoms(expr, decimals=4)`（§3.4.2） | nonfinite → 同上 |
| 4 | 丸め後 expr を `audit_sympy_to_prefix`（§3.4.6）で prefix へ再射影 | 同上 |
| 5 | prefix を `prefix_to_sympy_infix` で infix へ；**SymPy 式 canonical 比較**用に `q4_sympy_expr_canonical` を保存 | — |

**external Q4 timeout**: `10.0` 秒 / 呼び出し → `q4_construction_completed=false` → `execution_failure`。

#### 3.4.1 `prefix_to_sympy_infix`（audit-owned）

`third_party/odeformer/odeformer/envs/simplifiers.py` の
`_prefix_to_sympy_compatible_infix` / `prefix_to_sympy_compatible_infix` と
**同一の再帰規則**を audit 実装が再実装する（コードコピー可、production import 禁止）。

| 規則 | 内容 |
|---|---|
| 演算子 arity | production `all_operators` dict と同一 |
| leaf numeric | `float(token)` 成功時は `str(token)` を leaf 文字列とする |
| leaf 変数 | 非 numeric leaf はそのまま |
| 出力 | 全体を `({infix})` で包む |

#### 3.4.2 `audit_round_float_atoms`

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
| `Rational` / `Integer` | 変更しない |
| internal 1s timeout | **使用しない** |

#### 3.4.3 `FROZEN_Q4_LOCAL_DICT`

| キー | 値 |
|---|---|
| `n` | `Symbol("n", real=True, nonzero=True, positive=True, integer=True)` |
| `e`, `pi`, `euler_gamma` | SymPy 定数 |
| `arcsin`, `arccos`, `arctan`, `step`, `sign` | 対応 SymPy 関数 |
| `x_0` … `x_9` | `Symbol("x_k", real=True, integer=False)` |
| 系変数 | コーパス次元 `d` に応じて `x_0`…`x_{d-1}` を追加 |

#### 3.4.4 凍結 SymPy StrPrinter / Float atom 規則（B2）

production `Simplifier.sympy_to_prefix` の **Float 分岐**を mirror する:

| SymPy 型 | prefix 出力規則 |
|---|---|
| `sp.Symbol` | `[str(expr)]` |
| `sp.Integer` | `[str(expr)]` |
| **`sp.Float`** | `s = str(expr)`（SymPy 既定 StrPrinter）；`[s]` |
| **`sp.Rational`** | `["mul", str(expr.p), "pow", str(expr.q), "-1"]` |
| `sp.EulerGamma` | `["euler_gamma"]` |
| `sp.E` | `["e"]` |
| `sp.pi` | `["pi"]` |
| 演算子 | `SYMPY_OPERATORS` マップ（`Add→add`, `Mul→mul`, `Pow→pow`, …）に従い `_sympy_to_prefix(op_name, expr)` で子を再帰 |

**禁止**: `word_to_infix` 意味同等だけで Float 表現を凍結しないこと。
**必須**: 丸め後 SymPy expr への **直接 `simplify(expand=True)` 比較**（§3.4.7）を primary oracle とし、
emit された reference token は **保存のみ**（トークン節約）。

#### 3.4.5 `audit_sympy_to_prefix`

§3.4.4 の規則を audit 実装に **verbatim 再実装**する（production `sympy_to_prefix` import 禁止）。

#### 3.4.6 Q4 parity fixtures（SymPy 式比較 + 代表 token）

| ID | 入力 | 期待 |
|---|---|---|
| **Q4-R1** | E1 prefix `mul,0.04598,x_0` | 丸め後 SymPy expr が `0.0460*x_0` と同値；emit token に `0.0460` |
| **Q4-R2** | `mul,10.0,x_0` | `10.0*x_0` 同値 |
| **Q4-R3** | `pow2,div,mul,10.0,x_0,10.0` | 構築成功；compound power arity 保持 |
| **Q4-R4** | Rational `1/3` を含む expr（prefix 経由） | Float atom `str(sp.Float(Rational(1,3)))` → round(4) → **`0.3333`** token |

**Fixture Q4-R4 詳細**:

```text
e1_infix=(1/3)*x_0
after_round_expected_float_token=0.3333
rational_prefix=mul,1,pow,3,-1
note=Rational は §3.4.4 の mul,p,q,pow,-1 規則で prefix 化してから algorithm 適用
```

#### 3.4.7 E1 vs Q4(E1) SymPy canonical oracle（非循環）

| 項目 | 凍結値 |
|---|---|
| 左辺 | E1 から §3.4.1–3 で得た SymPy expr（round 前） |
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

**禁止**: `completed=true`, `equivalent=false` を `execution_failure` に分類しない。

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
| **REACH-SFN-1** | hand algebraic | **original_truth** infix: `2*x_0**2/(1+x_0**2)`；**E2 readout** infix（synthetic）: `4*x_0**2/(2+2*x_0**2)` | E1≡original_truth、E2≡Q4(E1)、**`hill_form=false`**（2026-09-15 recheck: `classify_formula` on candidate → false） |
| **REACH-PRESERVED-1** | hand algebraic | infix: `x_0**2/(1+x_0**2)` | E1≡truth、E2≡Q4(E1)、**`hill_form=true`**（recheck: true） |
| **REACH-UNS-1** | synthetic grid | **exactly 1,320** terminal rows；各 row が fully diagnostic かつ `hill_form=true` | primary **unsupported** 分岐到達（decision-function proof） |
| **REACH-SUP-1** | synthetic single | **1** fully diagnostic SFN row（REACH-SFN-1 相当） | primary **supported** 分岐到達 |
| **REACH-DRIFT-E2** | synthetic | E2≢Q4(E1) | `semantic_drift` |
| **REACH-Q4FAIL-1** | synthetic | Q4 構築失敗 | `execution_failure` |
| **REACH-IDENT-FALLBACK-1** | synthetic | E2 raw==E1 raw かつ E1≢Q4(E1) | `e2_identity_fallback_candidate=true` → `execution_failure` |
| **REACH-PARSE-1** | synthetic | `classifier_parse_valid=false` | `execution_failure`（順位 2） |
| **REACH-RESCALE-1** | synthetic | `rescale_incomplete=true`（§5.2） | `execution_failure` |
| **REACH-POW-COMP-1** | prefix | `pow2,div,mul,10.0,x_0,10.0` | Q4 構築成功 |

**G_impl**（§10）: full confirmatory 実行前に上表 **および** post-freeze F1–F8 受け入れ evidence が PASS すること。

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

### 4.2 Scale 設計

| 区分 | isotropic `traj_scale` | 用途 |
|---|---|---|
| **Primary grid** | `{0.1, 0.5, 1.0, 2.0}` | confirmatory |
| **Stress** | `{5.0}` | D2 descriptive |

`feature_scale = 1`；primary grid は全成分の決定論的直積。

### 4.3 負対照・探索

| 集合 | 件数 | 用途 |
|---|---:|---|
| N1 | 100 | 意図非同値 rewrite |
| S5 | 1 | 探索的再現（primary 非連動） |

**N1 凍結選択**: 全 510 成分；`audit_negative_seed=61004`；
canonical_key `audit_negative_seed=61004|system_id={system_id}|component_idx={component_idx}`；
digest 昇順先頭 100；`COEFFS = [1,2,3,5,7]`；`negative_id=negative_sha256:{digest}`。

### 4.4 Quantization stratum 規則（B9）

**`fractional_digit_count(token)`** — numeric leaf **raw token 文字列**に適用:

| 手順 | 規則 |
|---:|---|
| 0 | token に `e` または `E` が含まれる → **reject**（`quantization_stratum_assign` は `construction_incomplete`） |
| 1 | 先頭の `+` / `-` を除去（符号は桁数に含めない） |
| 2 | `.` が無い → **0** |
| 3 | 元 token を `.` で分割；**小数部 substring** のみ対象 |
| 4 | 小数部の **末尾ゼロを除去**（`rstrip('0')`） |
| 5 | 残余文字数 = `fractional_digit_count` |

**禁止**: `format(rational, 'f')` 等の間接表現のみで定義すること。

**成分 stratum**: いずれか leaf で count > **4** → `quantization_active`；else `quantization_neutral`。

**期待カウント**（truth-side 静的棚卸し；v10 drafting で PASS）:

- `quantization_active`: **46** 成分、**184** primary ペア
- `quantization_neutral`: **284** 成分、**1,136** primary ペア
- 合計: **330** / **1,320**

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

### 5.2 `rescale_incomplete` 凍結条件（B4）

production `Scaler.rescale_function` が **入力 tree を未変換で返す** すべての経路:

| # | 条件 | 検出 |
|---:|---|---|
| 1 | `len(nodes) > len(scale)`（multi-component system で component 数超過） | 返却 tree == 入力 tree |
| 2 | 変数 `x_k` の `k >= len(scale)`（index が scale 外） | 同上 |
| 3 | production が component-count mismatch で early return するその他の経路 | 実装が tree 同一性 + 上記 1–2 を検査 |

`rescale_incomplete=true` → **`execution_failure`**（precedence 2）。

---

## 6. ベースライン、ablation、controls

| 条件 | 説明 | スコア段 | 単位 | `rewrite_id` |
|---|---|---|---|---|
| **B0** | rewrite E0 → rescale → **Q4** → simplify → classify + metrics | E2 | 2,040 pairs | `rewrite_sha256:{digest}` |
| **B1** | identity E0 → production identity rescale → **Q4** → simplify | E2 | **510 components** | **`identity`** |
| **B2** | B0 と同 E0/E1；simplifier 省略；**E1-only** 分類 | E1 | 2,040 pairs | `rewrite_sha256:{digest}` |
| **B3** | `compare_formulas(..., skip_cas=False)` | 診断 | 500 strict-Hill pairs | n/a |
| **B4** | 真値 infix を pred にコピー | 指標健全性 | **510 components** | **`truth_copy`** |
| **C_q4** | Q4 参照健全性（§6.1） | Q4 | **6 fixtures** | n/a |

### 6.1 C_q4 — Q4 参照健全性 control

| 項目 | 凍結値 |
|---|---|
| fixture 数 | **6** |
| primitive | P11 のみ |
| **`unit_type`** | **`fixture`**（§7.1） |
| `unit_id` | `q4_fixture_{01..06}` |

| fixture_id | E1 prefix（代表） | 必須検証 |
|---|---|---|
| `q4_fixture_01` | `mul,0.04598,x_0` | SymPy 同値 + token `0.0460` |
| `q4_fixture_02` | `mul,10.0,x_0` | `10.0` 保持 |
| `q4_fixture_03` | `add,1.0,x_0` | 構築成功 |
| `q4_fixture_04` | `pow2,x_0` | 構築成功 |
| `q4_fixture_05` | `pow2,div,mul,10.0,x_0,10.0` | compound power 成功 |
| `q4_fixture_06` | `mul,0.33333,x_0` | 4 桁丸め **`0.3333`**（Q4-R4 連動） |

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
| R1/R2 | `component` | `component_id` |
| B0/B1/B2/B4/D2 | `pair` | `pair_id` |
| B3 | `pair` | `pair_id` |
| N1 | `negative` | `negative_id` |
| **C_q4** | **`fixture`** | **`q4_fixture_{01..06}`** |

**`component_id`**: `component_sha256:{SHA256(UTF-8(component_key))}`；
`component_key=corpus_hash={h}|system_id={sid}|component_idx={idx}`。

**`pair_id`**: `pair_sha256:{SHA256(UTF-8(pair_key))}`；
`pair_key=corpus_hash={h}|system_id={sid}|component_idx={idx}|scale={scale}|rewrite_id={rewrite_id}`。

---

## 8. 計算上限と counted-call 表

### 8.1 Counted call の定義

§8.2 named primitive への **1 回の論理呼び出し**。メモ化でも `call_log.jsonl` に 1 行。

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
| C_q4 | P11 | C_q4 | fixtures | **6** |
| B3 | P10 | B3 | pairs | 500 |
| N1 | P7 | N1 | negatives | 100 |
| | | | **Confirmatory total** | **27,636** |

算術: $`1{,}530 + 16{,}320 + 4{,}080 + 4{,}080 + 1{,}020 + 6 + 600 = 27{,}636`$。

### 8.4 Descriptive tier

| 行 | 内容 | 追加 calls |
|---|---|---:|
| D1 | non-strict filtered aggregation | **0** |
| D2 | strict-Hill stress `5.0` B0 path（8 primitives/pair） | **2,640** |
| | **Grand maximum** | **30,276** |

D2: $`330 \times 8 = 2{,}640`$。

### 8.5 Resource ceiling

| 項目 | 上限 |
|---|---|
| GPU / decode | **0** |
| CPU wall | ≤ **5** CPU-hours |
| Confirmatory counted calls | **27,636** |
| Grand maximum | **30,276** |
| ディスク | ≤ **1.2 GB** |

超過時 **abort**（G1）。

---

## 9. 除外・失敗ポリシー

| 事象 | Outcome |
|---|---|
| Truth / rewrite / E0 / E1 構築・parse 不能（simplifier 前） | `construction_incomplete` |
| `q4_construction_completed=false` | `execution_failure` |
| **`e2_identity_fallback_candidate=true`** | `execution_failure` |
| **`classifier_parse_valid=false`** | `execution_failure` |
| **`rescale_incomplete=true`**（§5.2 全経路） | `execution_failure` |
| External oracle / CAS / simplifier timeout | `execution_failure` |
| E1/E2 oracle `completed=false` | `execution_failure` |
| E1 または E2 oracle `completed=true`, `equivalent=false` | `semantic_drift` |
| E2≠truth だが E2≡`Q4(E1)` | **not** `semantic_drift` |
| `original_vs_q4_numeric_max_abs_error` > 0 のみ | 記述のみ |

**禁止**: Q4 失敗・non-diagnostic 行を分母から除外すること。

---

## 10. Validity gates

**評価順序**: G_corpus → G0 → G4 → G1 → **G_impl** → **G_q4ref** → G_n1 → **G_b1** → G_b4 → linear controls → G_term → primary rule

| Gate | 条件 | FAIL 時 |
|---|---|---|
| **G_corpus** | §4.1（240/510；rejection≤0.30；fingerprint 一致） | abort |
| G0 | §5 Scaler assert | abort |
| G4 | sealed-path access guard 試行 0 | undecidable |
| G1 | counted calls ≤ **27,636** | abort |
| **G_impl** | §3.8 REACH-* **すべて** PASS；post-freeze **F1–F8** acceptance PASS（§16） | undecidable |
| **G_q4ref** | C_q4 **6/6** 成功；`q4_fixture_01` 丸め；`q4_fixture_06` → `0.3333` | undecidable |
| G_n1 | N1 **100/100** `completed=true` かつ `equivalent=false` | undecidable |
| **G_b1** | B1 **510/510**: Q4 完了、E1-original 同値、E2–Q4 同値、`classifier_parse_valid=true`、`formula_metrics_valid=true`；terminal ∈ {`control_pass`,`control_failure`}；**`unknown` 0** | undecidable |
| G_b4 | B4 **510/510** `valid=true` かつ `canonical_exact=1` | undecidable |
| G_ctrl_cov | 線形 **480/480** parse+metrics valid | undecidable |
| G_ctrl_fp | 線形 FP rate = 0 | undecidable |
| G_ctrl_lin | linear canonical noninvariance = 0 | undecidable |
| G_term | strict-Hill **1,320/1,320** terminal outcome ちょうど 1 つ；**`unknown` 0** | undecidable |
| G_inc | `construction_incomplete` ≤ 5% | undecidable |

**G_b1 / G_impl は counted call を追加しない**（既存 B1 行の conjunct 検査のみ）。

---

## 11. Sealed-path access guard

`configs/gpu_run5/base.yaml`: `output_root=results/runs`；`family_holdout.sealed_test_families=[R07,R08]`。

path normalization → `norm_abs` / `real_abs` 両方を matcher へ。
campaign-relative 先頭 `gpu_run5_` 下で `test`/`sealed`/`final_test` 子孫 deny；
`phase8` より前に出現した `predictions` 子孫 deny。
`builtins.open`, `os.open/stat/listdir/scandir`, `pathlib` 読取 API を intercept。
禁止 access 試行 **0 件**（G4）。

---

## 12. 成果物と resume

| 成果物 | 内容 |
|---|---|
| `audit_manifest.json` | `audit_id=v11`、ceiling **27636**/**30276**、P11/P12、Q4 timeout 10.0 |
| `pair_results.csv` | `q4_*`, `e2_identity_fallback_candidate`, `partition_scope`, oracle 二重参照、stratum |
| `quantization_stratum.json` | 510 成分 stratum |
| `q4_reference_controls.json` | C_q4 6 fixtures |
| `reachability_evidence.json` | §3.8 fixture 結果 |
| `call_log.jsonl` | P11/P12；P7 stage `E1-original` / `E2-q4` |

**Resume identity**（`audit_id` 変更）:

| フィールド | v11 凍結値 |
|---|---|
| `audit_id` | `c0001_metric_identifiability_audit_v11` |
| `q4_timeout_sec` | 10.0 |
| `confirmatory_call_ceiling` | 27636 |
| `grand_call_ceiling` | 30276 |

---

## 13. 実行コマンドと provenance

### 13.1 環境

Python 3.10.x；`--allow-cpu`；`LANSR_TED_TIMEOUT_SEC=10`；`LANSR_SYMPY_TIMEOUT_SEC=10`；`LANSR_SYMPY_MAX_NODES=40`。

### 13.2 Source hashes

`src/gpu_run5/grn.py`；`src/evaluation/gpu_run5_structure.py`；
`third_party/odeformer/odeformer/model/utils_wrapper.py`；
`third_party/odeformer/odeformer/envs/simplifiers.py`；
`src/gpu_run5/evaluation.py`；`src/gpu_run4/formulas.py`；`configs/gpu_run5/base.yaml`。

### 13.3 凍結コマンド（実装後；本タスクでは実行しない）

```bash
python -m compileall -q src scripts tests
export LANSR_TED_TIMEOUT_SEC=10
export LANSR_SYMPY_TIMEOUT_SEC=10
export LANSR_SYMPY_MAX_NODES=40
python scripts/phases/gpu_runmultiai_c0001_metric_audit.py \
  --audit-id c0001_metric_identifiability_audit_v11 \
  --output-dir GPU_RUNmultiAI/cycles/C0001/runs/c0001_metric_identifiability_audit_v11 \
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

---

## 14. 承認チェックリスト

| フィールド | v11 ドラフト |
|---|---|
| primary hypothesis | §1 |
| primary endpoint | §2.1 |
| Q4 serialization | §3.4.4–3.4.7（sympy_to_prefix + SymPy oracle） |
| identity fallback | §2.2 `e2_identity_fallback_candidate` |
| reachability | §3.8 + G_impl |
| non-primary partition | §2.5 |
| budgets | §8（**27,636** / **30,276**；5 h / 1.2 GB） |
| gates | §10（G_impl, G_b1） |
| frozen_on | **未** |

---

## 15. Post-freeze 実装要件（§16 参照）

F1–F8 は v10 §16 と同一 ID。full run 前に **すべて** PASS。F3 は本プロトコルで対応済み。

---

## 16. Post-freeze 実装要件（凍結後）

| ID | 要件 |
|---|---|
| F1 | E0 exact decimal rational；E1≡truth @ primary scales |
| F2 | compound pow operand prefix 解析 |
| F4 | round-trip test E1≡truth |
| F5 | B1 production identity rescale |
| F6 | B1 explicit partition；`unknown` 禁止 |
| F7 | B2 immutable pair rebuild |
| F8 | B3 shared `\|` separator |

---

## 17. 凍結整合性宣言

- 歴史 v9 文書 SHA256（変更禁止）: `60cfed79780c6b027192a3da14e69416d72090e0a89dddd22248b0f00f50cf00`
- 歴史 v10 ドラフト SHA256（変更禁止）: `da00004793fc2715b8f54d8a8ba6a7bf24138452d30a5bee54c16f5d69f95f21`
- 本 v11 は v9/v10 ファイルを **編集しない**
- 本 v11 は **未凍結**

---

## 18. 関連ドキュメント（非 binding）

- `preregistration_draft_v9.md` — 凍結済み
- `preregistration_draft_v10.md` — 未凍結ドラフト
- `preregistration_v10_independent_review.md` — B1–B9
- `preregistration_v11_revision_handoff.md` — T010 引き継ぎ
- `implementation_review_round5.md` — F1–F8
