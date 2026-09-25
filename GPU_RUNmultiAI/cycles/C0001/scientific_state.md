# C0001 科学的状態の再構成（授権範囲内）

- cycle: C0001
- task: C0001-T004
- role: research-engineer
- worker: Claude Code
- branch: `ai/C0001/research-engineer/preregister-metric-audit`
- 作成日: 2026-09-12
- 状態: draft（凍結前）

本書は C0001-T001 の状態再構成、C0001-T002 の候補生成、C0001-T003 の批判レビューを、
本ワークツリーでのソース直読による一次確認と合わせて永続化したものである。
`.agent/rules/01-research-integrity.md` に従い、**観測事実 / ソース由来の推論 / 未検証の推測 / 外部文献主張** を分離して記す。

## 0. 授権境界

| 項目 | 状態 |
|---|---|
| 退役 PR #4 / `GPU_RUNclaude1` の科学的内容 | **不使用**（`.agent/README.md` の historical-source boundary） |
| GPU_RUN5 sealed test の生成果物（`results/runs/gpu_run5_*` の final test raw） | **不読** |
| GPU_RUN5 の公開レポート記述（`GPU_RUN5/README.md` 等） | 使用可（本書で引用する範囲に限る） |
| 本タスクでの実験実行 | **不可**（draft only） |
| 本タスクでのコード／設定／テスト編集 | **不可**（write scope は C0001 の 4 Markdown のみ） |

## 1. 観測事実（リポジトリ一次ソースで直接確認したもの）

### 1.1 推論プロトコルは `rescale: true` で固定されている

- `configs/gpu_run5/base.yaml:12-16` — `paper_protocol: {beam_size: 50, beam_temperature: 0.1, beam_type: sampling, rescale: true}`。
- `src/gpu_run4/session.py:37` — `rescale=bool(protocol.get("rescale", True))` で regressor を構築。
- `src/gpu_run4_runtime.py:243` — `SymbolicTransformerRegressor(model=model, from_pretrained=False, rescale=rescale)`。
- `src/gpu_run5/phase8_runtime.py:207`、`scripts/phases/gpu_run5_phase3.py:166`、
  `scripts/phases/gpu_run5_phase5.py:128`、`scripts/phases/gpu_run5_phase6.py:218` も同一プロトコル値を渡す。

したがって GPU_RUN5 の decode 系 Phase は例外なく Scaler 経路を通る。

### 1.2 Scaler は x と t をスケールし、候補木を逆スケールする

- `third_party/odeformer/odeformer/model/sklearn_wrapper.py:56` — `rescale=True` のとき
  `Scaler(time_range=[1, time_range], feature_scale=feature_scale)` を生成（`params` 未指定時は `feature_scale=1`, `time_range=10`）。
- 同 `:118-125` — 各データセットで `scaler.fit_transform(time, trajectory)` を実行し、`scale_params[i] = scaler.get_params()` を保存。
- `third_party/odeformer/odeformer/model/utils_wrapper.py:30-33` — `fit()` は
  `traj_scale = trajectory[argmin(time)]`、すなわち **最初期時刻の状態（初期条件）** を特徴スケールに採る。ゼロ成分のみ 1 に置換。
- 同 `:44-49` — `get_params()` は `scale = feature_scale / traj_scale`、および時間の一次変換係数 `(a_t, b_t)` を返す。
- 同 `:51-79` — `rescale_function()` は
  (i) 各成分の先頭に `mul, 1/scale[dim]` と `mul, a_t` を付加し、
  (ii) prefix 中のすべての `x_d` を `mul, scale[d], x_d` に、`t` を `add, b_t, mul, a_t, t` に置換する。
- `sklearn_wrapper.py:164-166` — 逆スケール後、必ず
  `candidate = self.model.env.simplifier.simplify_tree(candidate)` を `try/except: pass` で適用する。

### 1.3 simplify_tree は sympy 往復＋4 桁丸めであり、代数的因数分解は行わない

- `third_party/odeformer/odeformer/envs/simplifiers.py:73-89` — `simplify_tree(tree, expand=False, resimplify=False)`。
  既定では `expand_expr` も `simplify_expr` も呼ばれず、`tree_to_sympy_expr` → `sympy_expr_to_tree` の往復のみ。
- 同 `:101-111` — `tree_to_sympy_expr` は `parse_expr(..., evaluate=True)` の後 `round_expr(decimals=4)` を適用する。
- 同 `:150-157` — `round_expr` は `sp.Float` を 4 桁に丸める。
- 同 `:296-303`（`sympy_to_prefix` 内） — `Pow` を `inv` に落とす分岐は**コメントアウト**されており、
  出力 prefix では `1/z` は `pow, z, -1` になる。
- 同 `:73` の `with timeout(1)` — 簡約は 1 秒で打ち切られ、`sklearn_wrapper.py:166` の `except: pass` により
  **失敗は無記録で握り潰される**。

### 1.4 指標側は sympy 再パース＋正規化を行うが、代数的同値判定は既定で無効

- 候補は infix 文字列として指標に渡る（`src/gpu_run4_runtime.py:294` の `str(tree.infix())`、
  `scripts/phases/gpu_run5_phase3.py:122`、`src/gpu_run5/phase8_runtime.py:324` など）。
- `src/gpu_run4/formulas.py:218-236` — `parse_infix_component` は `parse_expr(evaluate=True)` →
  `_sympy_to_tree` → `canonicalize_tree`。
- `src/gpu_run4/formulas.py:179-187` — `_sympy_to_tree` は `Pow(base, -1)` を `inv` へ戻す。
  したがって 1.3 の `pow, z, -1` は指標側で `inv` として復元される。
- `src/gpu_run4/ted.py:242-266` — `canonicalize_tree` は符号正規化、可換演算の平坦化・整列、恒等要素畳み込み、
  および `quantize_number`（`:103`、有効数字 `NUMERIC_SIGNIFICANT_DIGITS` 桁への丸め）を行う。
  **代数的因数分解・共通因子の括り出しは行わない。**
- `src/gpu_run5/evaluation.py:41` — `formula_metrics` は `compare_formulas(..., skip_cas=True)` を呼ぶ。
  `src/gpu_run4/formulas.py:493-502` により、`skip_cas=True` では `canonical_exact` が 1.0 でない限り
  sympy 同値判定も数値同値判定も**実行されない**。

### 1.5 構造フラグ（Hill 判定）は分母に「裸のべき」を要求する

- `src/evaluation/gpu_run5_structure.py:104-112` — `_strict_hill_denominator` は
  分母が `add(power, constant)` で、`power` が `_positive_integer_power` を満たすことを要求する。
- 同 `:79-93` — `_positive_integer_power` が受理するのは `x_i`、`pow2/pow3` の入れ子、
  `pow(x_i, 整数)` のみ。**`mul(c, pow(x_i, n))` は受理しない**（`None` を返す）。
- 同 `:127-149` — `_hill_flags` は `inv` 因子に対してのみ判定する。
- 同 `:26-32` — `_denominators` は `inv` と `div` のみを分母として収集する。
- 同 `:199-215` — `_exponent_skeleton` は数値・定数記号を `CONST` に置換するが、
  **木の形状は保存する**。よって定数の値の差は吸収されるが、`mul` ノードが 1 個増える形状差は吸収されない。

### 1.6 GRN 真値の分母は「裸のべき + 定数」である

- `src/gpu_run5/grn.py:60-68` — `_act(x, α, k, n)` = `mul(mul(α, xⁿ), inv(add(kⁿ, xⁿ)))`、
  `_rep(x, α, k, n)` = `mul(αkⁿ, inv(add(kⁿ, xⁿ)))`。
  いずれも分母は `add(定数, 裸のべき)` であり、1.5 の strict Hill 条件をちょうど満たす。
- 同 `:70-71` — `_decay(x, β)` = `mul(-1, mul(β, x))`。線形成分は Hill 分母を持たない。
- 同 `:125-205` — R01/R02 は 1 次元、R03–R05 は 2 次元、R06–R08 は 3 次元。
  R04・R07・R08 の第 1 成分および R08 の第 2 成分は `定数 − β·x` の純線形形。
- 同 `:256` — 初期条件は `rng.uniform(0.05, 2.5)` から引かれる。よって 1.2 の
  `traj_scale`（＝初期状態）は一般に 1 ではなく、`scale = 1/x(0)` は 1 から乖離する。
- `configs/gpu_run5/base.yaml:31` — `t_span: [0.0, 10.0]`。`time_range=[1,10]` と合わせ、時間側は
  `a_t ≈ 0.9`, `b_t ≈ 1.0` 相当の非自明な一次変換になる。

### 1.7 GPU_RUN5 の公開結論（sealed test raw は読まない）

`GPU_RUN5/README.md` の記述より:

- 固定 run `gpu_run5_20260823_ddd267b0` は Phase 0–9 完了、sealed test 開封は `open_count=1`。
- **Go 8 は NO-GO**。理由として「R03–R08 の非自明構造で exact 回復がなく、family-holdout で top3 改善がなく、
  main generalization NRMSE 比が 1.6275 で事前上限 1.10 を超えた」。
- 前向き予測は 6 hit / 1 miss / 0 undecidable。miss は P7。

**「非自明構造で exact 回復ゼロ」**という記述が、本サイクルで検証対象とする現象の中心である。

## 2. ソース由来の推論（未実行・要測定）

以下は 1 節のソース事実からの演繹であり、**本タスクでは実行していない**。C0001 の監査で測定する対象である。

1. **係数吸収による Hill 偽陰性**。scaled 空間で正しい候補 `α'zⁿ/(k'ⁿ+zⁿ)` を
   `rescale_function` で戻すと `z → s·x` の置換により分母は `k'ⁿ + sⁿxⁿ` となる。
   `simplify_tree` は `expand=False, resimplify=False` かつ因数分解を行わないため、
   分母は `add(定数, mul(定数, pow(x,n)))` の形で残る可能性が高い。
   その場合 1.5 より `hill_form=false`、`exponent_aware_skeleton_exact=0` となる。
2. **`skip_cas=True` による救済不能**。1.4 より、代数的に真値と同値であっても
   `canonical_exact` が 0 なら `symbolic_equivalent` は評価されない。
   すなわち係数吸収は CAS で救済されない。
3. **構造依存の非対称性**。純線形成分（`定数 − β·x`）では全体係数 `a_t/s` と `s` の置換が
   sympy の定数畳み込みで完全に吸収されるため、形状差は生じないと予想される。
   逆に Hill 分母を含む成分のみが偽陰性化する。
   これは 1.7 の「R03–R08 の**非自明構造**で exact 回復がない」という観測パターンと整合する。
4. **`rescale_function` の無音スキップ**。`utils_wrapper.py:53-54, 68-69` により、
   成分数が `scale` 長を超える場合や次元インデックスが範囲外の場合、逆スケールは適用されず
   **scaled 空間のままの木が返る**。この分岐は記録されないため、既存 run では検出不能である。

## 3. 上流タスクからの報告（本ワークツリーで再現していない）

- **反復する候補生成失敗**: GPU_RUN2 / GPU_RUN4 / GPU_RUN5 を横断して候補生成側の失敗が繰り返し観測された、
  という独立リポジトリ再構成の報告（C0001-T001/T002）。本書ではこれを**上流報告**として記録し、
  本ワークツリーでの一次確認は行っていない。
- **PI 探索的チェック（confirmatory ではない）**: `formula_metrics` に対し
  真値 `2*x_0**2/(1+x_0**2)-0.5*x_0` と代数的に同一の `4*x_0**2/(2+2*x_0**2)-0.5*x_0` を与えたところ、
  `canonical_exact=0`, `exponent_aware_skeleton_exact=0`, `hill_form=false`, `TED>0` が返った。
  これは 2.1 と 2.2 の機構と整合するが、**探索的**であり、Scaler 実経路の往復は未検証である。

## 4. 未検証の仮定（監査で潰すべきもの）

| # | 仮定 | 危険性 |
|---|---|---|
| A1 | `simplify_tree` が係数を分母内に残す | sympy のバージョン依存。実測必須 |
| A2 | 実データ由来の `scale` が 1 から十分乖離する | `x(0)≈1` の系では効果が消える |
| A3 | `simplify_tree` の 1 秒 timeout が GRN 規模で発火しない | 発火すると別経路になる |
| A4 | 指標側 `canonicalize_tree` が係数を括り出さない | ソース上は行わないが実測で確認 |
| A5 | 純線形成分は往復不変 | 対照条件として測定する |
| A6 | GPU_RUN5 の exact 回復ゼロが本機構で説明できる | **本サイクルでは検証しない**（sealed 非アクセス） |

A6 は重要な制約である。本サイクルの監査は「指標が代数的に正しい候補を偽陰性化するか」を判定するのみで、
**GPU_RUN5 の実結果を再解釈しない**。再解釈は指標修正後の別サイクルの仕事である。

## 5. 次アクション

1. 本書と `hypothesis_review.md` を基に `preregistration_draft.md` を批判レビュー（Claude Opus / statistical-reviewer）へ回す。
2. 凍結後、実装を Cursor に委譲する。
3. `GPU_RUNmultiAI/hypothesis_tree.md` の更新は本タスクの write scope 外であり、親セッションが行う。
