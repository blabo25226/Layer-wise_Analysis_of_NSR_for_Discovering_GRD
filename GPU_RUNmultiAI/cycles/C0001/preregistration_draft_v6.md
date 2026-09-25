# C0001 事前登録 v6 — メトリック同定可能性監査

- campaign: GPU_RUNmultiAI
- cycle: C0001
- task: C0001-T005
- audit_id: `c0001_metric_identifiability_audit_v6`
- supersedes: `preregistration_draft_v5.md`（v5 は未凍結・参照のみ）
- 作成日: 2026-09-13
- 状態: **draft v6（未凍結・未承認）**
- binding_plan: null（凍結後に `research_state.md` へ記録）

本書は `.agent/rules/04-preregistration-and-metric-freeze.md` の全フィールドを
**メトリック監査** 向けに具体化した v6 ドラフトである。
v5 independent closure review（`preregistration_v5_closure_review.md`）の 8 必須修正をすべて閉じる。
v4 independent closure review（`preregistration_v4_closure_review.md`）の V4-1–V4-8 も引き続き満たす。
GPU_RUN5 の sealed test 生成果物は読まない。GPU_RUN5 の結論を再解釈しない。
**本監査は decode を含まない**（CPU の決定論的 Scaler 往復のみ）。

---

## 0. 科学的クレームの校正

**主張の範囲**:

- 本監査が検証するのは、**凍結された whole-chain readout**
  （production simplifier → `classify_formula` の **合成連鎖全体**）が、
  **E1 と E2 の両方が独立 oracle で truth と同値** である strict-Hill ペアにおいて、
  component-level `hill_form` を誤って `false` とする **構造的偽陰性** を生むかどうかのみである。
- **因果的 stage attribution は主張しない**。Stage A 出力と Stage B の parse 成否・`hill_form` のみ保存する。
  simplifier 単体 vs classifier 単体の帰属は **別途予算化された ablation readout** が必要（本監査の範囲外）。
- `canonical_exact` / `exponent_aware_skeleton_exact` は **構文木・正規化表現** の一致指標であり、
  一般代数同値性の oracle ではない。
- GPU_RUN5 等の過去 syntactic exact 結果を一括無効化しない。
- Hill 分類（component-level `hill_form`）と exact-tree / skeleton 回復は **別 endpoint** として報告する。
- **存在ゲートは薄い confirmatory 証拠**である。系統的/prevalence 主張は本監査の範囲外であり、
  別途凍結された prevalence 閾値を結果後に代入しない。

---

## 1. 主仮説（primary hypothesis）— 唯一の仮説規則

**H0001-METRIC（v6）**:
ODEFormer 推論プロトコルに対応する決定論的監査連鎖
（preverified 非自同値 rewrite からの full-system E0 → `Scaler.rescale_function` →
instrumented `simplifier.simplify_tree` subprocess → component-level `classify_formula` readout）
は、**truth-side strict-Hill 登録ペア**の固定分母において、
独立 equivalence oracle で **E1 が真値と同値かつ E2 が真値と同値** と確認された成分に対し、
`component_flags[component_idx]["hill_form"] == false` となる **構造的偽陰性** を少なくとも 1 件生む。

**帰無仮説（監査用）**:
固定分母 1,320 primary strict-Hill scale ペアのうち、
**fully diagnostic** なペア（§2.2）のみを分母として `structural_false_negative` は **0 件**。

**diagnostic coverage の定義**（v6）:

| 用語 | 定義 |
|---|---|
| **fully diagnostic pair** | terminal outcome が `preserved` または `structural_false_negative`（すなわち `construction_incomplete=0` かつ `execution_failure=0` かつ `semantic_drift=0` かつ E1/E2 oracle 同値が確認済み） |
| **non-diagnostic pair** | `construction_incomplete`、`execution_failure`、`semantic_drift` のいずれか |

**primary decision rule（唯一・排他的評価順序）**:

以下を **上から順に 1 回だけ** 評価し、最初に真になった判定を採用する。

| 順位 | 判定 | 条件 |
|---:|---|---|
| 1 | **H0001 undecidable** | §10 の **validity gate のいずれかが FAIL**、または terminal coverage 不成立（1,320 一意 pair の欠落・重複・`unknown`） |
| 2 | **H0001 supported** | 順位 1 が false **かつ** **fully diagnostic** な `structural_false_negative` ≥ 1（他ペアが non-diagnostic でも可） |
| 3 | **H0001 unsupported** | 順位 1–2 が false **かつ** `structural_false_negative`=0 **かつ** 固定分母 1,320 件 **すべて** fully diagnostic |
| 4 | **H0001 undecidable** | 上記のいずれにも該当しない（例: SFN=0 だが non-diagnostic pair が 1 件以上残る） |

**存在 vs 不在の非対称ロジック**（v6 凍結）:

- **supported（存在証明）**: fully diagnostic SFN が **1 件でもあれば** 十分。non-diagnostic pair が混在しても supported を妨げない。
- **unsupported（不在証明）**: SFN=0 だけでは不十分。**1,320 件すべて** が fully diagnostic であることが必須。non-diagnostic が 1 件でもあれば unsupported に到達できず **undecidable**。
- この非対称性は、構造的偽陰性の **存在** と **完全な不在** で証明負荷が異なることを反映する。

**terminal coverage は primary 判定の必須前提**である。
1,320 一意 strict-Hill pair のいずれかが欠落・重複・未確定の場合、supported/unsupported を判定しない（順位 1 → undecidable）。
primitive 完了率は **運用指標のみ**（§8.6）であり、primary 判定の代替にならない。

Controls（§10）は **validity gates** であり、primary 仮説判定の conjunct ではない。
control FAIL → **undecidable**（unsupported ではない）。

---

## 2. 一次エンドポイントと統計単位

### 2.1 一次 readout（C-A）— whole-chain observable

本監査の primary readout は **凍結 whole-chain**（simplifier + classifier）を対象とする（simplifier 単体ではない）。

| 段 | 処理 | 保存フィールド |
|---|---|---|
| **Stage A** | production `simplifier.simplify_tree(E1)` → emitted infix | `e2_infix_pre_classifier` |
| **Stage B** | `classify_formula(e2_infix_pre_classifier)` → component-level flags | `classifier_parse_valid`, `classifier_parse_failure_reason`, `hill_form` |

| 項目 | 定義 |
|---|---|
| **Primary readout** | `classify_formula(e2_infix_pre_classifier)["component_flags"][component_idx]["hill_form"]` |
| **禁止** | `formula_metrics` の system-level OR、`classify_formula` の system-level `hill_form` |
| **Secondary** | `formula_metrics(true_infix, predicted_infix)` による `canonical_exact`, `exponent_aware_skeleton_exact`, TED 系 |
| **帰属の限界** | `classify_formula` は normalized infix を返さない。Stage B では parse 成否と `hill_form` のみ保存し、**どの段が hill_form を決定したかは主張しない** |

`formula_metrics` の公開 signature は `formula_metrics(true_infix: str, predicted_infix: str)` であり、
内部で `compare_formulas(..., skip_cas=True)` を **固定** 呼び出す（呼び出し側は `skip_cas` を渡さない）。
返却 dict に `hill_form` は含まれない。primary 判定は **component_flags のみ**。

**内部再量子化の記録**: Stage B 内部の `parse_system` は numeric leaf を `quantize_number`（4 significant-digit `.4g`）へ正規化し得る。
本監査は **whole-chain** を対象とし、classifier 内部正規化の有無を **主張の前提としない**。
Stage A 出力（`e2_infix_pre_classifier`）と Stage B の parse 成否・`hill_form` を保存する。
simplifier vs classifier の **因果帰属** は別途予算化された ablation が必要（本監査の confirmatory budget 外）。

### 2.2 固定分母と mutually exclusive outcome partition（C-B, C-F, R3-1, V4-1, V4-2）

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
| `construction_incomplete` | truth parse、rewrite preverify、**E0 構築**、**E1 構築または E1 parse 不能**（production simplifier **実行前**） |
| `execution_failure` | production simplifier 実行後の E2 parse 失敗、NaN/Inf、`rescale_incomplete`、external simplifier timeout、**E1/E2 oracle が `completed=false`**（parse/timeout/nonfinite/exception のみ） |
| `semantic_drift` | E1 または E2 oracle が **`completed=true` かつ `equivalent=false`**（正常完了した非同値；B0 では drift、N1 では期待 reject） |
| `structural_false_negative` | E1 oracle 同値 **かつ** E2 oracle 同値 **かつ** `hill_form=false`（fully diagnostic） |
| `preserved` | E1 oracle 同値 **かつ** E2 oracle 同値 **かつ** `hill_form=true`（fully diagnostic） |

5 カテゴリの件数は固定分母 1,320 上で合計 1 になる（proportion は各カテゴリ / 1,320）。
E2 非同値ペアは `semantic_drift` に分類し、**分母から除外しない**。

**凍結 precedence / 真理値表**（上から順に最初に真になったカテゴリを採用）:

| 順位 | カテゴリ | 条件 |
|---:|---|---|
| 1 | `construction_incomplete` | registration 段の truth parse / rewrite preverify / E0 構築失敗 / **E1 構築または E1 parse 不能（simplifier 実行前）** |
| 2 | `execution_failure` | E2 parse 失敗、NaN/Inf、`rescale_incomplete`、external simplifier timeout、**E1 または E2 oracle `completed=false`** |
| 3 | `semantic_drift` | `e1_oracle_completed=true` **AND** `e1_oracle_equivalent=false` **OR** `e2_oracle_completed=true` **AND** `e2_oracle_equivalent=false` |
| 4 | `structural_false_negative` | `e1_oracle_equivalent=true` **AND** `e2_oracle_equivalent=true` **AND** `hill_form=false` |
| 5 | `preserved` | `e1_oracle_equivalent=true` **AND** `e2_oracle_equivalent=true` **AND** `hill_form=true` |

**stage observability 用に保存するフラグ**（因果帰属ではない）:

| フィールド | 定義 |
|---|---|
| `e1_oracle_completed` | E1 oracle 呼び出しが parse/timeout/nonfinite/exception なく正常終了 |
| `e2_oracle_completed` | E2 oracle 呼び出しが parse/timeout/nonfinite/exception なく正常終了 |
| `e1_oracle_equivalent` | E1 が truth と独立 oracle 同値（`completed=true` のときのみ意味を持つ） |
| `e2_oracle_equivalent` | E2 が truth と独立 oracle 同値（`completed=true` のときのみ意味を持つ） |
| `e1_analytic_equivalent`, `e1_numeric_equivalent` | E1 oracle 部分結果 |
| `e2_analytic_equivalent`, `e2_numeric_equivalent` | E2 oracle 部分結果 |
| `is_fully_diagnostic` | outcome が `preserved` または `structural_false_negative` |

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

### 3.2 Primary E0 源と凍結 rewrite（C-D, M-d, R3-3, V4-3）

| 条件 | E0 構築 | `rewrite_id` |
|---|---|---|
| **B0 primary** | preverified **非自同値 rewrite**（`audit_rewrite_seed=61003`）から full-system analytic E0 | `rewrite_sha256:{digest_hex}` |
| **B1** | **identity パラメータ**（$`s=1`$, $`a_t=1`$, $`b_t=0`$）で truth から identity E0 を **成分ごとに 1 回** 構築 | **`identity`** |
| **B4** | 真値 infix を pred にコピー（指標健全性） | **`truth_copy`** |

B1 は scaled primary-grid E0 を identity scaler に通す比較 **ではない**（旧 v2 B1 の禁止比較）。

**全 510 成分**に決定論的・seeded・非自同値 rewrite を **1 本ずつ** 付与する（B0 用）。
rewrite は registration 段（P2）で独立 oracle 同値を preverify する。
`pair_id` と成果物 ID に **rewrite provenance**（`rewrite_id`）を含める。

**凍結 rewrite 生成規則**（v6）:

| 項目 | 凍結値 |
|---|---|
| seed フィールド | `audit_rewrite_seed=61003` |
| 成分キー | `(family, variant_index, component_idx)` の辞書順 |
| index 表記 | `variant_index` と `component_idx` は **zero-based 十進整数**（leading zero 禁止） |
| 素数集合 | `PRIMES = [2, 3, 5, 7, 11]`（昇順、正の素数） |
| 選択関数 | `digest = SHA256(UTF-8(canonical_key_string))`；`r = PRIMES[int.from_bytes(digest[:8], "big") % 5]` |
| canonical_key_string | `audit_rewrite_seed=61003|family={family}|variant_index={variant_index}|component_idx={component_idx}` — 区切りは **リテラル ASCII pipe 文字** `|`（空白なし；エスケープや backslash なし） |
| `rewrite_id` | `rewrite_sha256:{digest_hex}` — **`digest_hex` は canonical_key_string の UTF-8 bytes 全体の SHA256 完全 digest** |

**凍結 UTF-8 例**（検証用）:

| 項目 | 値 |
|---|---|
| canonical_key_string | `audit_rewrite_seed=61003|family=R01|variant_index=0|component_idx=0` |
| SHA256 | `57f7c55b2de5a6e9e10c1c7518ada07890eb00d3588c045ca3d531dfbae0187c` |
| 選択素数 `r` | `2` |
| `rewrite_id` | `rewrite_sha256:57f7c55b2de5a6e9e10c1c7518ada07890eb00d3588c045ca3d531dfbae0187c` |

**非簡約 prefix テンプレート**（成分 truth prefix を `E` とする。E0 構築前に **代数簡約・約分・定数畳み込み禁止**）:

| 形式 | 凍結テンプレート |
|---|---|
| **prefix** | `div,mul,{r},{E_prefix...},{r}` — `{E_prefix...}` は truth 成分の comma-separated prefix トークン列を **そのまま** 挿入（`mul` と `div` は binary ノード、`r` は decimal 文字列 `"2"`/`"3"`/`"5"`/`"7"`/`"11"`） |
| **infix** | `(({r}*({E_infix}))/{r})` — `{E_infix}` は production `env.word_to_infix` が truth 成分から emit する infix（外側の二重括弧はテンプレート固定） |

**P2 `rewrite_oracle_precheck` 必須検証**:

1. **lexical non-identity**: rewrite prefix 文字列 ≠ truth 成分 prefix；rewrite infix ≠ truth 成分 infix
2. **exact equivalence**: §3.5 oracle が rewrite 成分と truth 成分の同値を返す
3. 非同値または lexical identity → `construction_incomplete`（当該成分の B0 ペアすべて）

`r ≠ 1` は素数集合の定義により常に成立する。

### 3.3 E1 / E2

| 段 | 定義 |
|---|---|
| **E1** | `Scaler.rescale_function(env, E0_tree, a_t, b_t, scale)` |
| **E2** | instrumented single-thread subprocess 内の `simplifier.simplify_tree(E1, expand=False, resimplify=False)` |

### 3.4 Simplifier 実装契約（C-E, M-c, R3-5, V4-4）

**production 既定**（`third_party/odeformer/odeformer/envs/simplifiers.py`）:

- `expand=False`, `resimplify=False`
- SymPy `parse_expr(evaluate=True)` → `round_expr(decimals=4)` → prefix 再構築
- **内部 1 秒 timeout** は `except TimeoutError: pass` で握り潰され、**呼び出し側から観測不能**

**監査契約（Stage A）**:

1. 真値コーパスは `src/gpu_run5/grn.py` の **lexical `.4g` トークン**を忠実に使用する（§4.1）
2. **独立 `.4f` コーパスは作成しない**
3. simplification は **single-thread** subprocess のみ（signal ベース timeout と thread 併用禁止）
4. **external frozen timeout** = `5.0` 秒（subprocess kill；manifest に記録）
5. internal 1 秒 timeout の存在は記録するが、**E2==E1 から timeout を推論しない**
6. timeout 挙動（internal 1s swallowed、external 5s kill）を凍結する

**classifier 契約（Stage B）**:

- `classify_formula(infix)` → `component_flags[component_idx]["hill_form"]` および parse 成否
- **normalized infix の返却を要求しない**（現行 API に存在しない）
- 本監査は **whole-chain** を仮説対象とするが、保存する Stage B 観測値は parse 成否と `hill_form` のみ

### 3.5 統一 numeric parser と独立 equivalence oracle（C-C, M-c, V4-4, v5-R2）

**`audit_rational_parse`（truth / E0 / E1 / E2 の oracle 入力に共通）**:

| 規則 | 内容 |
|---|---|
| 対象 | 各 numeric leaf の **元トークン文字列**（decimal または integer 表記） |
| 変換 | `sympy.Rational(token_string)` — **binary float 経由禁止** |
| 非数 leaf | 変数・演算子は既存 prefix/infix dialect に従う |
| 失敗 | oracle 呼び出し中の parse 不能 → **`completed=false`** → pair outcome は `execution_failure`（precedence 順位 2） |

**oracle 結果スキーマ**（各 E1/E2 呼び出しごとに保存）:

| フィールド | 型 | 定義 |
|---|---|---|
| `completed` | bool | parse/timeout/nonfinite/exception なく oracle 評価が正常終了 |
| `analytic_equivalent` | bool | analytic 部分が完了し同値 |
| `numeric_equivalent` | bool | numeric grid 部分が完了し同値 |
| `equivalent` | bool | **`analytic_equivalent AND numeric_equivalent`**（`completed=true` のときのみ評価） |

| 項目 | 凍結値 |
|---|---|
| Analytic | sympy `simplify(expand=True)` exact rational |
| Numeric grid | 各 $`x_j \in \{0.01, 0.1, 0.5, 1.0, 2.0\}`$ 直積、$`t \in \{0, 5, 10\}`$、tol $`10^{-8}`$ |
| **`completed=false`** | parse 失敗、timeout、nonfinite、未捕捉 exception のみ |
| **`completed=true`, `equivalent=false`** | analytic または numeric の **正常完了した非同値**（disagreement）。B0 では `semantic_drift`、N1 では **期待 reject** |
| **`completed=true`, `equivalent=true`** | analytic **かつ** numeric の両方 PASS |
| Analytic 未完了または numeric 未完了 | `completed=false` → `execution_failure` |
| **External oracle timeout** | `30.0` 秒 / 呼び出し → `completed=false` |

**禁止**: 正常完了した非同値（`completed=true`, `equivalent=false`）を `execution_failure` に分類してはならない。

E2 oracle と E1 oracle は **別 counted call**（drift 分類に必須）。
`e1_oracle_*` / `e2_oracle_*` フィールドを pair row に保存する。

各 numeric leaf について **raw token string** と **parsed rational value** を保存する。

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

**lexical token 監査境界**:

- `grn.py` は定数を `{:.4g}` で出力する（例: `f"{alpha:.4g}"`, `f"{k**n:.4g}"`, `f"{p['basal']:.4g}"`）
- 各 numeric leaf トークンについて **raw token string** と **parsed rational value** を保存する
- oracle は §3.5 の `audit_rational_parse` を使用する
- `.4f` コーパスは追加しない

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
| N1 | 100 | 意図非同値 rewrite；oracle が **`completed=true` かつ `equivalent=false`** を返すことを確認（§10 G_n1） |
| S5 | 1 hand-check ペア | 探索的再現（G2）；primary 非連動 |

**N1 凍結選択規則**（v6）:

| 項目 | 凍結値 |
|---|---|
| 母集団 | 全 **510 成分** |
| 成分キー | `(family, variant_index, component_idx)` — zero-based 十進整数、padding なし |
| 順序キー | `digest = SHA256(UTF-8(canonical_key_string))` |
| canonical_key_string | `audit_negative_seed=61004|family={family}|variant_index={variant_index}|component_idx={component_idx}` — リテラル ASCII pipe 区切り（空白なし） |
| 選択 | digest 昇順で **先頭 100 成分** |
| 係数集合 | `COEFFS = [1, 2, 3, 5, 7]` |
| 係数選択 | `c = COEFFS[int.from_bytes(digest[:8], "big") % 5]`（**rewrite 用 PRIMES とは別集合**） |
| `negative_id` | `negative_sha256:{digest_hex}` — 完全 digest を含む |
| prefix テンプレート | `add,{E_prefix...},{c}` — `{E_prefix...}` は truth 成分 prefix を **そのまま** 挿入 |
| infix テンプレート | `(({E_infix})+({c}))` — `{E_infix}` は production `env.word_to_infix` 出力 |
| 代数制約 | E0 構築前に **簡約・約分・定数畳み込み禁止** |
| G_n1 成功条件 | 100/100 で oracle **`completed=true` かつ `equivalent=false`** |

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

| 条件 | 説明 | スコア段 | 単位 | `rewrite_id` |
|---|---|---|---|---|
| **B0** | rewrite E0 → rescale → simplify → classify + metrics | E2 | 510 成分 × 4 scales = 2,040 ペア | `rewrite_sha256:{digest_hex}` |
| **B1** | identity E0（1 回/成分）→ identity rescale → simplify | E2 | **510 成分**（scale 非依存） | **`identity`** |
| **B2** | B0 と同 E0/E1；simplifier 省略 | E1 | 2,040 ペア | `rewrite_sha256:{digest_hex}` |
| **B3** | `compare_formulas(..., skip_cas=False)` | 診断 | strict-Hill 500 ペア（hash 順） | n/a |
| **B4** | 真値 infix を pred にコピー | 指標健全性 | **510 成分**（scale 非依存） | **`truth_copy`** |

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
| `rewrite_id` | 成分に割当された rewrite の決定論 ID（B1=`identity`、B4=`truth_copy`） |

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
| `diagnostic_coverage_rate` | fully diagnostic pair 数 / 1,320 | absence 証明可否の監視 |

`primitive_completion_rate` は validity gate **ではない**。
primary 判定は **terminal coverage の 100%**（1,320/1,320）のみを要求する（§1, §2.2）。

---

## 9. 除外・失敗ポリシー

| 事象 | Outcome |
|---|---|
| Truth / rewrite / E0 / **E1 構築・parse 不能（simplifier 前）** | `construction_incomplete` |
| External oracle / CAS / simplifier timeout | `execution_failure` |
| Internal 1s simplifier timeout（観測不能） | 記録のみ；external timeout で分類 |
| E2 parse / NaN / Inf | `execution_failure` |
| `rescale_incomplete` | `execution_failure`（**never** structural FN） |
| E1/E2 oracle parse 失敗 / oracle timeout / nonfinite / exception | `execution_failure`（`completed=false`） |
| E1 または E2 oracle 正常完了非同値（`completed=true`, `equivalent=false`） | `semantic_drift`（B0）または N1 期待 reject |

---

## 10. Validity gates（controls；M-a, V4-8）

**評価順序**: G0 → G4 → G1 → G_n1 → G_b4 → linear controls → **terminal coverage check（G_term）** → **primary rule（§1 排他順序）**

| Gate | 条件 | FAIL 時 |
|---|---|---|
| G0 | §5 Scaler assert 4 値 + `rescale_features=true` | abort |
| G4 | sealed-path **access guard** 違反（禁止 open/stat/listdir/scandir 試行 > 0） | undecidable |
| G1 | confirmatory counted calls が hard ceiling 23,550 を超過 | abort |
| **G_n1** | N1 100 件すべてで oracle が **`completed=true` かつ `equivalent=false`**（**100/100**） | undecidable |
| **G_b4** | B4 510 件すべてで `valid=true` かつ `canonical_exact=1`（**510/510 self-match**） | undecidable |
| **G_ctrl_cov** | 線形 **480/480** ペアで `classifier_parse_valid=true` **かつ** `formula_metrics.valid=true`（失敗は分母から除外しない） | undecidable |
| G_ctrl_fp | 線形 480 ペアで `hill_false_positive_rate = 0` | undecidable |
| G_ctrl_lin | 線形 480 ペアで `linear_canonical_noninvariance_rate = 0` | undecidable |
| G_term | strict-Hill 1,320 pair すべてが terminal outcome を **ちょうど 1 つ** 持つ | undecidable |
| G_inc | strict-Hill 1,320 で `construction_incomplete` ≤ 5% | undecidable |

**いずれかの gate FAIL → §1 順位 1（undecidable）**（unsupported ではない）。
Gates PASS **かつ** G_term PASS 後のみ §1 順位 2–4 を評価する。

---

## 11. Sealed-path access guard（M-f, R3-7, V4-5, v5-R5）

`configs/gpu_run5/base.yaml` から派生:

| Config キー | 凍結値 |
|---|---|
| `output_root` | `results/runs`（repo root 相対；実行時に absolute へ resolve） |
| `family_holdout.sealed_test_families` | `[R07, R08]`（コーパス生成の holdout ラベル；path deny とは別） |

**path normalization（deny 判定前に必須）**:

1. 入力 path を repo root 相対なら `os.path.join(repo_root, path)` で absolute 化
2. `norm_abs = os.path.normpath(absolute_path)`
3. `real_abs = os.path.realpath(norm_abs)`（symlink 展開）
4. **`norm_abs` と `real_abs` の両方** を matcher へ渡す（どちらか一方が deny なら deny）

**凍結 deny matcher（POSIX component-based；glob 列挙禁止）**:

`is_denied(path_norm, path_real, output_root_abs)` は次を **すべて** 満たすとき deny とする。

1. `path_norm` **または** `path_real` が `output_root_abs` の下（strict prefix；同一 path は許可）
2. `output_root_abs` からの **相対 path** の **先頭 component** が `gpu_run5_` で始まる（campaign run directory）
3. 次の **directory 名 component** に対し、**その directory 自身とすべての子孫 path** を deny:
   - **`test`**, **`sealed`**, **`final_test`**: campaign run 配下の **任意深さ** で出現した時点から deny（列挙しない）
   - **`predictions`**: **直前 component が `phase8`** のときのみ、その `predictions` directory 自身と子孫を deny

**列挙禁止**: 既存 filesystem path の inventory、walk、glob による sealed artifact 発見は行わない。
matcher は **試行 path の component 分解のみ** で判定する。

**deny-on-attempt access guard**:

1. 監査コード（コーパス作業）開始 **前** に、親プロセスと **すべての child process**（simplifier subprocess 含む）が **同一 matcher** を初期化する。**child は task コード実行前に guard を必ず install する。**
2. 次の API を intercept し、**試行時**に normalized path を matcher へ照合:
   - `builtins.open`
   - `os.open`, `os.stat`, `os.listdir`, `os.scandir`
   - `pathlib.Path.open`, `Path.stat`, `Path.iterdir`, `Path.glob`, `Path.rglob`（および同等の pathlib 読取 API）
3. deny 一致試行を **ブロック**し、`attempted_operation` と `attempted_path`（norm と real）をログ
4. 監査完了時点で **禁止アクセス試行が 0 件**であることを G4 で要求

**既存 sealed artifact の存在だけでは G4 FAIL にならない**。
禁止 path への実際の access 試行のみが violation である。
本タスクおよび監査実行では sealed 生成果物へアクセスしない。

**許可**: `src/gpu_run5/grn.py` から `audit_data_seed` で **新規** R07/R08 を生成
（歴史 sealed holdout の生成果物へはアクセスしない）。

---

## 12. 成果物と resume（M-h, R3-8, V4-6, v5-R6）

| 成果物 | 内容 |
|---|---|
| `audit_manifest.json` | audit_id, commit, 全シード, Scaler assert, corpus counts, source hashes, access-guard attempt log, timeouts, plan hash, audit-script hash, normalized CLI, dependency versions, environment, ordered primitive table |
| `pair_results.csv` | `condition`, `pair_id`, stratum, outcome_category, `is_fully_diagnostic`, `e1_oracle_completed`, `e1_oracle_equivalent`, `e1_analytic_equivalent`, `e1_numeric_equivalent`, `e2_oracle_*`（同構造）, E0/E1/E2 status, `e2_infix_pre_classifier`, `classifier_parse_valid`, `classifier_parse_failure_reason`, primary `hill_form`, secondary metrics, E0/E1/E2 raw prefix, E0/E1/E2 emitted infix |
| `call_log.jsonl` | 各行 = 1 counted call（primitive, condition, stage, pair_id, duration, status） |
| `condition_summary.json` | 固定分母上の 5-way partition 比率と diagnostic coverage |
| `equivalence_oracle.json` | E1/E2 oracle 判定（`completed`, `analytic_equivalent`, `numeric_equivalent`, `equivalent`） |
| `negative_controls.json` | N1 100 件の `negative_id`, canonical key, oracle 結果 |
| `deviation_log.md` | 凍結後変更 |

**Resume identity 検証**（`--resume` 前に **すべて一致必須**；不一致は abort）:

| フィールド | 内容 |
|---|---|
| `audit_id` | `c0001_metric_identifiability_audit_v6` |
| `commit` | git commit SHA |
| `plan_hash` | 本 preregistration 文書 SHA256 |
| `audit_script_hash` | `scripts/phases/gpu_runmultiai_c0001_metric_audit.py` SHA256 |
| `config_hash` | `configs/gpu_run5/base.yaml` SHA256 |
| `source_hashes` | §13.2 の全ファイル SHA256 |
| `corpus_hash` | 凍結コーパス SHA256 |
| `seeds` | §7 の全シード |
| `primitive_table` | §8.2–§8.3 の順序付き primitive 表（内容と順序） |
| `cli_args_normalized` | 初回起動 CLI の **semantic 引数の正規化コピー**（`--resume` と `--fail-if-exists` **のみ除外**；他引数の欠落・追加・値変更は不一致） |

**semantic CLI identity**: resume 時は初回と **同一 semantic 引数集合** を要求する。
比較対象から除外するのは `--resume` と `--fail-if-exists` のみ。
§13.3 の resume コマンドは **初回の全 semantic フラグを再掲** し、末尾に `--resume` を付ける。
| `oracle_timeout_sec` | 30.0 |
| `simplifier_subprocess_timeout_sec` | 5.0 |
| `cas_timeout_sec` | 60.0 |
| `dependency_versions` | Python, sympy, numpy, torch 等 |
| `environment` | OS, CPU, git commit |

- キー: **`(primitive, condition, stage, pair_id)`**（`pair_id` 単独は不可）
- `pair_id` は §7 の必須フィールドをすべて含む
- デフォルト `--fail-if-exists`

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
| `src/gpu_run4/formulas.py` | compare_formulas / parse_system |
| `src/gpu_run4/ted.py` | quantize_number / NUMERIC_SIGNIFICANT_DIGITS |
| `configs/gpu_run5/base.yaml` | sealed-path 派生 |

### 13.3 凍結コマンド（実装後）

```bash
python -m compileall -q src scripts tests
python scripts/phases/gpu_runmultiai_c0001_metric_audit.py \
  --audit-id c0001_metric_identifiability_audit_v6 \
  --output-dir GPU_RUNmultiAI/cycles/C0001/runs/c0001_metric_identifiability_audit_v6 \
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

Resume（**初回の全 semantic 引数を再掲**；比較から `--resume` と `--fail-if-exists` のみ除外）:

```bash
python scripts/phases/gpu_runmultiai_c0001_metric_audit.py \
  --audit-id c0001_metric_identifiability_audit_v6 \
  --output-dir GPU_RUNmultiAI/cycles/C0001/runs/c0001_metric_identifiability_audit_v6 \
  --audit-data-seed 61001 \
  --audit-rewrite-seed 61003 \
  --audit-negative-seed 61004 \
  --audit-cas-subset-seed 61005 \
  --allow-cpu \
  --oracle-timeout-sec 30.0 \
  --simplifier-subprocess-timeout-sec 5.0 \
  --cas-timeout-sec 60.0 \
  --resume
```

（スクリプトは prereg 凍結後の実装タスク。本タスクでは実行しない。）

---

## 14. 承認チェックリスト

| フィールド | v6 ドラフト |
|---|---|
| primary hypothesis | §1（排他 decision order；存在/不在の非対称ロジック） |
| primary endpoint | §2.1 whole-chain component `hill_form` |
| statistical unit | §2.3 |
| datasets | §4（N1 凍結規則 §4.3） |
| checkpoints | 参照のみ（decode 不使用） |
| baselines/ablations | §6 |
| seeds | §7 |
| budgets | §8.3–§8.5（confirmatory 23,550；grand max 25,860） |
| operator constraints | §3, §5 |
| failure policy | §9（oracle tri-state） |
| support criteria | §1 排他順序 + §10 gates + G_term |
| Go/No-Go | §10（G_ctrl_cov 含む） |
| compute ceiling | §8.5 |
| required artifacts | §12 |
| reviewer sign-off | 未 |
| frozen_on | 未 |

---

## 15. 関連ドキュメント

- `preregistration_draft.md` — v1（変更しない）
- `preregistration_draft_v2.md` — v2（変更しない）
- `preregistration_draft_v3.md` — v3（変更しない）
- `preregistration_draft_v4.md` — v4（変更しない）
- `preregistration_draft_v5.md` — v5（変更しない）
- `preregistration_v4_closure_review.md` — v5 が閉じたレビュー
- `preregistration_v4_review_response.md` — v4 finding-by-finding 対応表
- `preregistration_v5_closure_review.md` — 本 v6 が閉じるレビュー
- `preregistration_v5_review_response.md` — v5 finding-by-finding 対応表
- `preregistration_v3_independent_review.md` — v4 が閉じたレビュー
- `preregistration_v3_review_response.md` — v3 対応表
- `preregistration_v2_closure_review.md` — v3 が閉じたレビュー
- `preregistration_v2_review_response.md` — v2 対応表
