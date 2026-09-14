# C0001 事前登録 v10 — メトリック同定可能性監査（Q4 参照改訂）

- campaign: GPU_RUNmultiAI
- cycle: C0001
- task: C0001-T009
- audit_id: `c0001_metric_identifiability_audit_v10`
- supersedes: `preregistration_draft_v9.md`（v9 は凍結済み・変更禁止；`preregistration_v9_freeze_record.md`）
- 作成日: 2026-09-14
- 状態: **draft v10（未凍結・未承認）**
- binding_plan: null（凍結後に `research_state.md` へ記録）
- amendment_authority: `preregistration_v10_amendment_decision.md`

本書は `.agent/rules/04-preregistration-and-metric-freeze.md` の全フィールドを
**メトリック監査** 向けに具体化した v10 ドラフトである。
v9 凍結契約（SHA256 `60cfed79780c6b027192a3da14e69416d72090e0a89dddd22248b0f00f50cf00`）の
**事前確認的同定可能性欠陥 F3**（`implementation_review_round5.md`）を閉じる改訂である。
v9 independent closure review の退行しない要素（固定分母、排他 partition、whole-chain 主張、
sealed guard、typed unit IDs、N1/B4/linear gates の骨格）は維持する。

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

**v9 からの科学的境界の変更**:

| 項目 | v9 | v10 |
|---|---|---|
| E1 oracle 参照 | 元 truth | **元 truth（変更なし）** |
| E2 oracle 参照 | 元 truth | **`Q4(E1)`（audit-owned 参照）** |
| 四桁量子化 | E2≠truth を `semantic_drift` | E2≠`Q4(E1)` を `semantic_drift`；truth≠`Q4` は記述のみ |
| unsupported 到達性 | 量子化により原理的に不可 | E2–`Q4` 同値下で **constructively reachable** |

---

## 1. 主仮説（primary hypothesis）— 唯一の仮説規則

**H0001-METRIC（v10）**:
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

**diagnostic coverage の定義**（v10）:

| 用語 | 定義 |
|---|---|
| **fully diagnostic pair** | terminal outcome が `preserved` または `structural_false_negative`（`construction_incomplete=0` かつ `execution_failure=0` かつ `semantic_drift=0` かつ **E1-original 同値** かつ **E2–`Q4(E1)` 同値** が確認済み） |
| **non-diagnostic pair** | `construction_incomplete`、`execution_failure`、`semantic_drift` のいずれか |

**primary decision rule（唯一・排他的評価順序）**:

| 順位 | 判定 | 条件 |
|---:|---|---|
| 1 | **H0001 undecidable** | §10 の **validity gate のいずれかが FAIL**、または terminal coverage 不成立（1,320 一意 pair の欠落・重複・`unknown`） |
| 2 | **H0001 supported** | 順位 1 が false **かつ** **fully diagnostic** な `structural_false_negative` ≥ 1 |
| 3 | **H0001 unsupported** | 順位 1–2 が false **かつ** `structural_false_negative`=0 **かつ** 固定分母 1,320 件 **すべて** fully diagnostic |
| 4 | **H0001 undecidable** | 上記のいずれにも該当しない（例: SFN=0 だが non-diagnostic pair が 1 件以上残る） |

**存在 vs 不在の非対称ロジック**（v10 凍結；v9 維持）:

- **supported**: fully diagnostic SFN が **1 件でもあれば** 十分。
- **unsupported**: SFN=0 だけでは不十分。**1,320 件すべて** fully diagnostic が必須。
- **Q4 構築失敗・oracle 失敗は non-diagnostic** であり、分母を減らさない（PI 選択 7）。

**reachable decision fixtures**（closure review で検証必須；§3.7）:

| 到達したい判定 | 最小 fixture クラス |
|---|---|
| **supported** | E1≡truth、E2≡`Q4(E1)`、`hill_form=false` の synthetic/corpus ペア |
| **unsupported** | 1,320 件すべて E1≡truth、E2≡`Q4(E1)`、`hill_form=true`（F1 修復後の primary grid） |
| **undecidable (non-diagnostic)** | `q4_construction_completed=false`、oracle timeout、construction_incomplete |
| **semantic_drift** | E1≢truth **または** E2≢`Q4(E1)`（正常完了非同値） |

Controls（§10）は **validity gates** であり、primary 仮説判定の conjunct ではない。

---

## 2. 一次エンドポイントと統計単位

### 2.1 一次 readout（C-A）— whole-chain observable

| 段 | 処理 | 保存フィールド |
|---|---|---|
| **Stage A-pre** | audit-owned `Q4(E1)` 参照構築（§3.4） | `q4_construction_completed`, `q4_emitted_infix`, `q4_construction_failure_reason` |
| **Stage A** | production `simplifier.simplify_tree(E1)` → emitted infix | `e2_infix_pre_classifier` |
| **Stage B** | `classify_formula(e2_infix_pre_classifier)` | `classifier_parse_valid`, `classifier_parse_failure_reason`, `hill_form` |

| 項目 | 定義 |
|---|---|
| **Primary readout** | `classify_formula(e2_infix_pre_classifier)["component_flags"][component_idx]["hill_form"]` |
| **禁止** | system-level OR、`formula_metrics` の `hill_form` |
| **Secondary** | `formula_metrics(true_infix, predicted_infix)` による exact/skeleton 系 |
| **記述（primary 非連動）** | `original_vs_q4_numeric_max_abs_error`（§3.5.3） |

### 2.2 固定分母と mutually exclusive outcome partition

**Eligibility は truth-side で凍結**（E0/E1/E2 実行前）:

| 層 | 成分数 | primary grid ペア | 用途 |
|---|---:|---:|---|
| **strict-Hill primary** | 330 | **1,320** | primary 仮説の固定分母 |
| non-strict Hill-bearing secondary | 60 | 240 | 記述 tier（§4.1） |
| linear control | 120 | 480 | validity gate のみ |

truth-side strict-Hill 内訳・non-strict 内訳・導出算術は v9 §2.2 と同一（$`330 \times 4 = 1{,}320`$）。

**truth-side quantization stratum**（PI 選択 6；報告のみ）:

| stratum | 成分レベル定義 | 期待 strict-Hill 成分数 | 期待 primary ペア数 |
|---|---|---:|---:|
| `quantization_neutral` | 成分の **すべて** の numeric leaf トークンが §4.4 の `fractional_digit_count` ≤ 4 | 284 | 1,136 |
| `quantization_active` | **少なくとも 1 つ** の numeric leaf で `fractional_digit_count` > 4 | 46 | 184 |

stratum は registration 段 P12 で **全 510 成分**に決定論的付与する。
`quantization_stratum.json` を成果物として保存する（§12）。
**分母から除外しない**。

**固定分母 1,320 ペアの mutually exclusive partition**（各ペアはちょうど 1 つ）:

| Outcome category | 定義 |
|---|---|
| `construction_incomplete` | truth parse、rewrite preverify、E0 構築、**E1 構築または E1 parse 不能**（production simplifier **実行前**） |
| `execution_failure` | **`q4_construction_completed=false`**、E2 parse 失敗、NaN/Inf、`rescale_incomplete`、external simplifier timeout、**E1-original または E2–`Q4` oracle `completed=false`** |
| `semantic_drift` | **E1-original oracle** `completed=true` **かつ** `equivalent=false` **OR** **E2–`Q4` oracle** `completed=true` **かつ** `equivalent=false` |
| `structural_false_negative` | **E1-original** `equivalent=true` **かつ** **E2–`Q4`** `equivalent=true` **かつ** `hill_form=false` |
| `preserved` | **E1-original** `equivalent=true` **かつ** **E2–`Q4`** `equivalent=true` **かつ** `hill_form=true` |

**凍結 precedence**（上から順に最初に真）:

| 順位 | カテゴリ | 条件 |
|---:|---|---|
| 1 | `construction_incomplete` | registration 段の truth/E0/E1 構築・parse 不能（simplifier 前） |
| 2 | `execution_failure` | `q4_construction_completed=false`、E2 parse/NaN/Inf/`rescale_incomplete`/timeout、**いずれかの oracle `completed=false`** |
| 3 | `semantic_drift` | `e1_oracle_completed=true` **AND** `e1_oracle_equivalent=false` **OR** `e2_oracle_completed=true` **AND** `e2_oracle_equivalent=false` |
| 4 | `structural_false_negative` | `e1_oracle_equivalent=true` **AND** `e2_oracle_equivalent=true` **AND** `hill_form=false` |
| 5 | `preserved` | `e1_oracle_equivalent=true` **AND** `e2_oracle_equivalent=true` **AND** `hill_form=true` |

**stage observability 用フラグ**:

| フィールド | 定義 |
|---|---|
| `e1_oracle_reference` | **凍結値** `original_truth` |
| `e2_oracle_reference` | **凍結値** `q4_e1` |
| `e1_oracle_completed` / `e1_oracle_equivalent` | E1 vs **元 truth** |
| `e2_oracle_completed` / `e2_oracle_equivalent` | E2 vs **`Q4(E1)`** |
| `e1_analytic_equivalent`, `e1_numeric_equivalent` | E1-original 部分結果 |
| `e2_analytic_equivalent`, `e2_numeric_equivalent` | E2–`Q4` 部分結果 |
| `q4_construction_completed` | P11 が §3.4 契約どおり完了 |
| `quantization_stratum` | `quantization_neutral` または `quantization_active` |
| `original_vs_q4_numeric_max_abs_error` | 記述（§3.5.3）；primary 判定に不使用 |
| `is_fully_diagnostic` | outcome が `preserved` または `structural_false_negative` |

**禁止**: E2≠truth のみを根拠に `structural_false_negative` と判定してはならない（v9 欠陥の再発防止）。

### 2.3 統計単位

v9 §2.3 と同一（系 240、成分 510、confirmatory pair は固定成分 ID）。

### 2.4 二次 endpoint

v9 §2.4 を維持。追加記述列:

| 名称 | 定義 | 用途 |
|---|---|---|
| `quantization_active_rate` | `quantization_active` strict-Hill ペア / 1,320 | stratum 報告 |
| `original_vs_q4_error_rate_nonzero` | `original_vs_q4_numeric_max_abs_error` > 0 の strict-Hill ペア率 | 記述 |

---

## 3. E0 / E1 / E2 / Q4 パイプライン

### 3.1 記法と自律系前提

v9 §3.1 と同一。

### 3.2 Primary E0 源と凍結 rewrite

v9 §3.2 と同一（`audit_rewrite_seed=61003`、canonical serialization、representative fixtures 不変）。

### 3.3 E1 / E2

| 段 | 定義 |
|---|---|
| **E1** | `Scaler.rescale_function(env, E0_tree, a_t, b_t, scale)` |
| **Q4(E1)** | §3.4 audit-owned 参照（production simplifier **非呼び出し**） |
| **E2** | instrumented subprocess 内 `simplifier.simplify_tree(E1, expand=False, resimplify=False)` |

### 3.4 Audit-owned `Q4(E1)` 参照（v10 新規；PI 選択 3–4）

**目的**: production `tree_to_sympy_expr(round=True)` が行う
`parse_expr(evaluate=True)` → `Float.round(4)` のみを、**最小非循環参照**として再現する。
production `simplify_tree` またはその返却 tree を **参照・呼び出し・再利用してはならない**。

**入力**: P5 完了後の E1 `raw_prefix` および `emitted_infix`（記録用；算法は prefix を主入力とする）。

**凍結 algorithm `audit_q4_decimal_round_reference`**:

| 手順 | 操作 | 失敗時 |
|---:|---|---|
| 1 | E1 prefix を **audit-owned** `prefix_to_sympy_infix`（§3.4.1）で SymPy 互換 infix へ変換 | `q4_construction_completed=false` |
| 2 | `sympy.parsing.sympy_parser.parse_expr(infix, evaluate=True, local_dict=FROZEN_Q4_LOCAL_DICT)` | 同上 |
| 3 | `audit_round_float_atoms(expr, decimals=4)`（§3.4.2） | nonfinite 結果 → 同上 |
| 4 | 丸め後 expr を `sympy_expr_to_audit_infix`（§3.4.3）で infix へ再射影 | 同上 |
| 5 | infix を `audit_rational_parse` 入力として oracle 側参照式を構成 | — |

**external Q4 timeout**: `10.0` 秒 / 呼び出し → `q4_construction_completed=false` → `execution_failure`。

#### 3.4.1 `prefix_to_sympy_infix`（audit-owned；production 非呼び出し）

`third_party/odeformer/odeformer/envs/simplifiers.py` の
`_prefix_to_sympy_compatible_infix` / `prefix_to_sympy_compatible_infix` と
**同一の再帰規則**を audit 実装が再実装する（コードコピー可、import による production 呼び出しは禁止）。

| 規則 | 内容 |
|---|---|
| 演算子 arity | `all_operators` dict と同一 |
| leaf numeric | `float(token)` 成功時は `str(token)` を leaf 文字列とする |
| leaf 変数 | 非 numeric leaf はそのまま |
| 出力 | 全体を `({infix})` で包む |

#### 3.4.2 `audit_round_float_atoms`

```python
# 擬似コード（凍結契約）
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
| internal 1s timeout | **使用しない**（audit Q4 は external timeout のみ） |

**production との意図的差分**: production `round_expr` は `timeout(1)` で握り潰す。
audit Q4 は timeout を **完了失敗**として記録する。

#### 3.4.3 `sympy_expr_to_audit_infix`

oracle 比較用に、丸め後 SymPy expr から **決定論的 infix** を emit する。
演算子・括弧・符号規則は production `word_to_infix` と **意味同等**でなければならないが、
production API の直接呼び出しは禁止（audit 側に凍結実装を置く）。

#### 3.4.4 `FROZEN_Q4_LOCAL_DICT`

| キー | 値 |
|---|---|
| `n` | `Symbol("n", real=True, nonzero=True, positive=True, integer=True)` |
| `e`, `pi`, `euler_gamma` | SymPy 定数 |
| `arcsin`, `arccos`, `arctan`, `step`, `sign` | 対応 SymPy 関数 |
| `x_0` … `x_9` | `Symbol("x_k", real=True, integer=False)` |
| 系変数 | コーパス次元 `d` に応じて `x_0`…`x_{d-1}` を追加 |

`d` は当該系の変数数（コーパス record から決定論的取得）。

#### 3.4.5 凍結 representative fixtures

**Fixture Q4-R1（四桁丸め）**:

```text
e1_prefix=mul,0.04598,x_0
expected_q4_infix_contains=0.0460
input_token=0.04598
rounded_token=0.0460
```

**Fixture Q4-R2（四桁超過なし）**:

```text
e1_prefix=mul,10.0,x_0
expected_q4_infix_contains=10.0
fractional_digit_count=0
```

**Fixture Q4-R3（compound power；F2 連動）**:

```text
e1_prefix=pow2,div,mul,10.0,x_0,10.0
q4_construction_completed=true
note=operand が複数トークンでも prefix tree を先に構築してから infix 化
```

### 3.5 統一 numeric parser と独立 equivalence oracle

#### 3.5.1 `audit_rational_parse`

v9 §3.5 と同一（`sympy.Rational(token_string)`、binary float 経由禁止）。

#### 3.5.2 二参照 oracle（v10）

各 pair で **2 つの独立 counted P7 呼び出し**を行う。

| 呼び出し | 左辺 | 右辺（参照） | 保存 prefix |
|---|---|---|---|
| **E1-original** | E1 emitted infix | **元 truth** 成分 infix（§4.1 コーパス） | `e1_oracle_*` |
| **E2–`Q4`** | E2 emitted infix | **`q4_emitted_infix`**（P11 出力） | `e2_oracle_*` |

**oracle 結果スキーマ**（各呼び出し）:

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
| nonfinite | `completed=false` |
| External oracle timeout | `30.0` 秒 / 呼び出し |

**禁止**: `completed=true`, `equivalent=false` を `execution_failure` に分類しない。

#### 3.5.3 `original_vs_q4_numeric_max_abs_error`（記述）

| 項目 | 定義 |
|---|---|
| 左辺 | 元 truth infix |
| 右辺 | `q4_emitted_infix` |
| 評価 | §3.5.2 と同一 numeric grid 上の $\max \lvert f_{\mathrm{truth}} - f_{Q4}\rvert$ |
| 条件 | `q4_construction_completed=true` のときのみ計算 |
| primary 使用 | **禁止**（係数量子化を SFN と混同しない；PI 選択 5） |

### 3.6 Simplifier 実装契約（Stage A）

v9 §3.4 と同一（`expand=False`, `resimplify=False`、external timeout `5.0` s、internal 1s は観測不能）。

### 3.7 Serialization / prefix dialect

v9 §3.6 と同一。

### 3.8 Reachability fixtures（closure review 必須）

| ID | 目的 | 期待 outcome / gate |
|---|---|---|
| `REACH-SFN-1` | supported 到達 | E1≡truth、E2≡`Q4(E1)`、`hill_form=false` |
| `REACH-UNS-1` | unsupported 到達 | strict-Hill 全件 diagnostic、`SFN=0`（F1 修復後 smoke で実証） |
| `REACH-DRIFT-E2` | E2–`Q4` 非同値 | `semantic_drift`（`e2_oracle_equivalent=false`） |
| `REACH-Q4FAIL-1` | Q4 構築失敗 | `execution_failure`（分母維持） |
| `REACH-TIMEOUT-1` | simplifier external timeout | `execution_failure` |
| `REACH-POW-COMP-1` | compound `pow2` operand（F2） | Q4 構築成功、prefix arity 破壊なし |

---

## 4. データセットとコーパス

### 4.1 凍結コーパス

v9 §4.1 と **完全同一**（`generate_corpus` 引数、`corpus_hash`、`system_id` 規則、240 系 / 510 成分）。

### 4.2 Scale 設計

v9 §4.2 と同一（primary `{0.1, 0.5, 1.0, 2.0}`、stress `5.0` descriptive）。

### 4.3 負対照・探索

v9 §4.3 と同一（N1 100 件、`audit_negative_seed=61004`）。

### 4.4 Quantization stratum 規則（v10 新規）

**`fractional_digit_count(token)`**（numeric leaf トークン文字列 `token`）:

| 手順 | 規則 |
|---:|---|
| 1 | `audit_rational_parse` 成功を要求 |
| 2 | 正規化 decimal 文字列を `format(rational, 'f')` 相当の **有限小数表現**で得る |
| 3 | 小数点以下の末尾ゼロを除去した残余桁数を数える |
| 4 | 整数トークンは **0** |

**成分 stratum**:

- いずれかの leaf で `fractional_digit_count` > **4** → `quantization_active`
- それ以外 → `quantization_neutral`

**期待カウント**（truth-side 静的棚卸し；`implementation_review_round5.md`）:

- strict-Hill `quantization_active` 成分 **46**（ペア **184**）
- strict-Hill `quantization_neutral` 成分 **284**（ペア **1,136**）

これらは **報告の期待値**であり、gate 条件ではない。

---

## 5. Scaler 構築

v9 §5 と同一（production パス、`time_scale=9`, `a_t=0.9`, `b_t=1.0`）。

**v10 実装注記（post-freeze F1/F5）**: E0 forward は exact decimal token からの明示 rational 構築を要求（§16）。

---

## 6. ベースライン、ablation、controls

| 条件 | 説明 | スコア段 | 単位 | `rewrite_id` |
|---|---|---|---|---|
| **B0** | rewrite E0 → rescale → **Q4** → simplify → classify + metrics | E2 | 2,040 pairs | `rewrite_sha256:{digest}` |
| **B1** | identity E0 → production identity rescale → **Q4** → simplify | E2 | **510 components** | **`identity`** |
| **B2** | B0 と同 E0/E1；simplifier 省略；**E1-only** 分類 | E1 | 2,040 pairs | `rewrite_sha256:{digest}` |
| **B3** | `compare_formulas(..., skip_cas=False)` | 診断 | 500 strict-Hill pairs | n/a |
| **B4** | 真値 infix を pred にコピー | 指標健全性 | **510 components** | **`truth_copy`** |
| **C_q4** | **Q4 参照健全性**（§6.1） | Q4 | **6 fixtures** | n/a |

### 6.1 C_q4 — Q4 参照健全性 control（PI 選択 11）

| 項目 | 凍結値 |
|---|---|
| fixture 数 | **6** |
| 選択 | 下表の **固定 ID 順**（hash 選択なし） |
| primitive | P11 `q4_decimal_round_reference` のみ |
| unit_type | `negative` |
| unit_id | `q4_fixture_{01..06}` |

| fixture_id | E1 prefix（代表） | 必須検証 |
|---|---|---|
| `q4_fixture_01` | `mul,0.04598,x_0` | 出力 infix に `0.0460` を含む |
| `q4_fixture_02` | `mul,10.0,x_0` | `10.0` 保持 |
| `q4_fixture_03` | `add,1.0,x_0` | 構築成功 |
| `q4_fixture_04` | `pow2,x_0` | 構築成功 |
| `q4_fixture_05` | `pow2,div,mul,10.0,x_0,10.0` | compound power 構築成功 |
| `q4_fixture_06` | `mul,0.33333,x_0` | 出力は 4 桁丸め |

**G_q4ref**（§10）: 6/6 で `q4_construction_completed=true`；fixture 01 の丸め検証必須。

---

## 7. シード、typed unit ID、決定論

v9 §7 と同一（seeds 61001–61005、component/pair serialization、representative fixtures 不変）。

**追加 unit_id**（C_q4）:

| 操作 | `unit_type` | `unit_id` |
|---|---|---|
| C_q4 | `negative` | `q4_fixture_{01..06}` |

**Resume / dedup キー**: `(primitive, condition, stage, unit_type, unit_id)`（変更なし）。

---

## 8. 計算上限と counted-call 表

### 8.1 Counted call の定義

v9 §8.1 と同一。P11 / P12 を追加。

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
| **P11** | **`q4_decimal_round_reference`** |
| **P12** | **`quantization_stratum_assign`** |

### 8.3 Confirmatory operations table（v10 完全導出）

| 行 | Primitive | Condition | 単位 | 回数 |
|---|---|---|---|---:|
| R1 | P1 `truth_register_classify` | registration | components | 510 |
| R2 | P2 `rewrite_oracle_precheck` | registration | components | 510 |
| R3 | P12 `quantization_stratum_assign` | registration | components | 510 |
| B0a | P3 `e0_analytic_construct` | B0 | pairs | 2,040 |
| B0b | P5 `scaler_rescale_function` | B0 | pairs | 2,040 |
| B0c | **P11 `q4_decimal_round_reference`** | B0 | pairs | 2,040 |
| B0d | P6 `simplifier_subprocess` | B0 | pairs | 2,040 |
| B0e | P7 `oracle_equivalence` | B0 → **E1-original** | pairs | 2,040 |
| B0f | P7 `oracle_equivalence` | B0 → **E2–`Q4`** | pairs | 2,040 |
| B0g | P8 `classify_component_flags` | B0 → E2 | pairs | 2,040 |
| B0h | P9 `formula_metrics_pair` | B0 → E2 | pairs | 2,040 |
| B1a | P4 `e0_identity_construct` | B1 | components | 510 |
| B1b | P5 `scaler_rescale_function` | B1 identity | components | 510 |
| B1c | **P11 `q4_decimal_round_reference`** | B1 | components | 510 |
| B1d | P6 `simplifier_subprocess` | B1 | components | 510 |
| B1e | P7 `oracle_equivalence` | B1 → **E1-original** | components | 510 |
| B1f | P7 `oracle_equivalence` | B1 → **E2–`Q4`** | components | 510 |
| B1g | P8 `classify_component_flags` | B1 → E2 | components | 510 |
| B1h | P9 `formula_metrics_pair` | B1 → E2 | components | 510 |
| B2a | P8 `classify_component_flags` | B2 → E1 | pairs | 2,040 |
| B2b | P9 `formula_metrics_pair` | B2 → E1 | pairs | 2,040 |
| B4a | P8 `classify_component_flags` | B4 | components | 510 |
| B4b | P9 `formula_metrics_pair` | B4 | components | 510 |
| C_q4 | **P11 `q4_decimal_round_reference`** | C_q4 | fixtures | **6** |
| B3 | P10 `compare_formulas_cas` | B3 | strict-Hill pairs | 500 |
| N1 | P7 `oracle_equivalence` | N1 | negative controls | 100 |
| | | | **Confirmatory total** | **27,636** |

**算術検証**:

- Registration: $`510 + 510 + 510 = 1{,}530`$
- B0: $`2{,}040 \times 8 = 16{,}320`$
- B1: $`510 \times 8 = 4{,}080`$
- B2: $`2{,}040 \times 2 = 4{,}080`$
- B4: $`510 \times 2 = 1{,}020`$
- C_q4: **6**
- B3 + N1: $`500 + 100 = 600`$
- **合計**: $`1{,}530 + 16{,}320 + 4{,}080 + 4{,}080 + 1{,}020 + 6 + 600 = 27{,}636`$

### 8.4 Descriptive tier

| 行 | 内容 | 追加 counted calls |
|---|---|---:|
| D1 | non-strict Hill-bearing filtered aggregation | **0** |
| D2 | strict-Hill stress `5.0` B0 path（**8 primitives**/pair） | **2,640** |
| | **Descriptive subtotal** | **2,640** |
| | **Full-run grand maximum** | **30,276** |

D2 算術: $`330 \times 8 = 2{,}640`$（v9 の 7 primitive から P11 追加）。

### 8.5 Resource ceiling（v10 再考）

| 項目 | v9 | v10 | 根拠 |
|---|---:|---:|---|
| Confirmatory counted calls | 23,550 | **27,636** | §8.3 完全導出（+4,086） |
| Grand maximum | 25,860 | **30,276** | +4,416（D2 含む） |
| CPU wall | 4 h | **5 h** | +17% calls、Q4 SymPy 作業 |
| ディスク | 1 GB | **1.2 GB** | `quantization_stratum.json`、Q4 列、oracle 二重保存 |
| GPU / decode | 0 | 0 | 変更なし |

超過時は **abort**（G1）。

### 8.6 Primitive completion（運用指標のみ）

v9 §8.6 と同一。confirmatory ceiling は **27,636**。

---

## 9. 除外・失敗ポリシー

v9 §9 に以下を **追加**:

| 事象 | Outcome |
|---|---|
| `q4_construction_completed=false` | `execution_failure`（**分母維持**） |
| Q4 nonfinite / external Q4 timeout | `execution_failure` |
| E2≠truth だが E2≡`Q4(E1)` | **not** `semantic_drift`（`preserved`/`SFN` 候補） |
| E2≡`Q4(E1)` だが E1≢truth | `semantic_drift` |
| `original_vs_q4_numeric_max_abs_error` > 0 のみ | **記述**；outcome 変更なし |

**禁止**: Q4 失敗・non-diagnostic 行を分母から除外すること（PI 選択 7）。

---

## 10. Validity gates

**評価順序**: G_corpus → G0 → G4 → G1 → **G_q4ref** → G_n1 → G_b4 → linear controls → G_term → primary rule

| Gate | 条件 | FAIL 時 |
|---|---|---|
| **G_corpus** | v9 と同一 | abort |
| G0 | v9 と同一 | abort |
| G4 | v9 と同一 | undecidable |
| G1 | confirmatory counted calls ≤ **27,636** | abort |
| **G_q4ref** | C_q4 **6/6** `q4_construction_completed=true`；fixture `q4_fixture_01` が `0.0460` 丸めを満たす | undecidable |
| **G_n1** | N1 **100/100** `completed=true` かつ `equivalent=false` | undecidable |
| **G_b4** | B4 **510/510** `valid=true` かつ `canonical_exact=1` | undecidable |
| **G_ctrl_cov** | 線形 **480/480** parse+metrics valid | undecidable |
| G_ctrl_fp | 線形 FP rate = 0 | undecidable |
| G_ctrl_lin | linear canonical noninvariance = 0 | undecidable |
| G_term | strict-Hill **1,320/1,320** terminal outcome ちょうど 1 つ | undecidable |
| G_inc | `construction_incomplete` ≤ 5% | undecidable |

---

## 11. Sealed-path access guard

v9 §11 と **完全同一**。

---

## 12. 成果物と resume

v9 §12 に以下を **追加 / 変更**:

| 成果物 | 追加内容 |
|---|---|
| `audit_manifest.json` | `audit_id=v10`、`q4_timeout_sec=10.0`、primitive 表に P11/P12、ceiling **27,636** / **30,276** |
| `pair_results.csv` | `q4_*`、`e1_oracle_reference`、`e2_oracle_reference`、`quantization_stratum`、`original_vs_q4_numeric_max_abs_error` |
| `quantization_stratum.json` | 全 510 成分の stratum、strict-Hill 集計 |
| `q4_reference_controls.json` | C_q4 6 fixture 結果 |
| `call_log.jsonl` | P11/P12 行；P7 stage に `E1-original` / `E2-q4` |

**Resume identity**（`audit_id` 変更）:

| フィールド | v10 凍結値 |
|---|---|
| `audit_id` | `c0001_metric_identifiability_audit_v10` |
| `plan_hash` | 本 preregistration SHA256（凍結後） |
| `q4_timeout_sec` | 10.0 |
| `confirmatory_call_ceiling` | 27636 |
| `grand_call_ceiling` | 30276 |

その他 resume フィールドは v9 §12 と同一構造。

---

## 13. 実行コマンドと provenance

### 13.1 環境

v9 §13.1 と同一。

### 13.2 Source hashes

v9 §13.2 と同一（Q4 は audit 実装に内蔵；production simplifier hash は Stage A 用に引き続き必須）。

### 13.3 凍結コマンド（実装後）

```bash
python -m compileall -q src scripts tests
export LANSR_TED_TIMEOUT_SEC=10
export LANSR_SYMPY_TIMEOUT_SEC=10
export LANSR_SYMPY_MAX_NODES=40
python scripts/phases/gpu_runmultiai_c0001_metric_audit.py \
  --audit-id c0001_metric_identifiability_audit_v10 \
  --output-dir GPU_RUNmultiAI/cycles/C0001/runs/c0001_metric_identifiability_audit_v10 \
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

Resume（semantic 引数再掲；`--resume` と `--fail-if-exists` のみ除外）:

```bash
export LANSR_TED_TIMEOUT_SEC=10
export LANSR_SYMPY_TIMEOUT_SEC=10
export LANSR_SYMPY_MAX_NODES=40
python scripts/phases/gpu_runmultiai_c0001_metric_audit.py \
  --audit-id c0001_metric_identifiability_audit_v10 \
  --output-dir GPU_RUNmultiAI/cycles/C0001/runs/c0001_metric_identifiability_audit_v10 \
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

（スクリプト改訂は v10 凍結後の実装タスク。本タスクでは実行しない。）

---

## 14. 承認チェックリスト

| フィールド | v10 ドラフト |
|---|---|
| primary hypothesis | §1（E1-original + E2–`Q4`；reachable fixtures §3.8） |
| primary endpoint | §2.1 whole-chain `hill_form` |
| statistical unit | §2.3 |
| datasets | §4（stratum §4.4） |
| Q4 reference | §3.4（production 非呼び出し） |
| oracle dual-reference | §3.5.2 |
| baselines/ablations | §6（C_q4 追加） |
| seeds | §7 |
| budgets | §8.3–§8.5（**27,636** / **30,276**） |
| failure policy | §9（Q4 失敗は分母維持） |
| support criteria | §1 + §10 |
| Go/No-Go | §10（**G_q4ref** 追加） |
| post-freeze implementation | §16 |
| reviewer sign-off | 未 |
| frozen_on | 未 |

---

## 15. 関連ドキュメント

- `preregistration_draft_v9.md` — 凍結済み（変更禁止）
- `preregistration_v9_freeze_record.md` — v9 SHA256 権威
- `preregistration_v10_amendment_decision.md` — PI 12 選択
- `preregistration_v9_to_v10_change_table.md` — 差分表
- `implementation_review_round5.md` — F3 欠陥根拠；F1–F8 post-freeze
- `preregistration_v10_handoff.md` — T009 引き継ぎ

---

## 16. Post-freeze 実装要件（v10 凍結後；本監査実行前）

以下は **プロトコル改訂とは分離**された実装修復である（PI 選択 12）。
v10 凍結時点ではコード未修復を許容するが、full confirmatory 実行前に **すべて** を満たす。

| ID | 要件 | 出典 |
|---|---|---|
| **F1** | E0 forward を exact decimal token から explicit rational 構築；E1 が全 primary scale で **E1-original** analytic+numeric 同値 | round5 P0 |
| **F2** | compound `pow2`/`pow3`/`pow4` operand の prefix tree 解析；非対称 nested fixture テスト | round5 P0 |
| **F4** | `test_e0_e1_round_trip_primary_scales` を **E1≡truth** 期待へ反転 | round5 P1 |
| **F5** | B1 が production `Scaler.rescale_function` を identity パラメータで実行 | round5 P1 |
| **F6** | B1 に explicit outcome partition；`unknown` 禁止 | round5 P1 |
| **F7** | B2 を immutable pair identity + E1 フィールドから再構築；E2 汚染禁止 | round5 P1 |
| **F8** | B3 component 抽出が shared `|` 分割を使用；multi-component fixture | round5 P1 |

**F3 は本 v10 プロトコル改訂で対応**（E2–`Q4` oracle；§3.5.2）。

---

## 17. v9 凍結整合性宣言

- v9 文書パス: `GPU_RUNmultiAI/cycles/C0001/preregistration_draft_v9.md`
- v9 SHA256（変更禁止）: `60cfed79780c6b027192a3da14e69416d72090e0a89dddd22248b0f00f50cf00`
- 本 v10 ドラフトは v9 ファイルを **編集しない**
- v9 `audit_id` `c0001_metric_identifiability_audit_v9` の smoke 出力は **科学証拠ではない**
