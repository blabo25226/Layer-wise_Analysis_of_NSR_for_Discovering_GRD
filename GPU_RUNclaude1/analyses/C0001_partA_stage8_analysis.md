# C0001 Part A — Stage 8 分析（独立導出）

- 拘束契約: `GPU_RUNclaude1/plans/C0001_preregistration_v2.1.md`（および同 `.json`）のみ。v1 / v2 は
  superseded な歴史記録であり、本文書では引用しない。
- run id: `gpu_runclaude1_c0001_b731cdd`
- branch: `20260909_researce_GPU_RUNclaude1`
- phase1 manifest commit: `8ff622defc227b4598e0094fc000b8227c4ffdad`
  / phase0 manifest commit: `b731cddd168390c973dbb0974349e4a2c55b9113`
- `component_strata.json` の `sha256_of_component_assignment`:
  `29a9b0f14069f59909261c7a79dcd49116a069b6a11d209ab9eb31a9a13bd546`
  （`partA_ladder_realized.json` の `sha256_of_component_strata_input` と一致）
- 本分析は supervisor の結論を一切参照せず、凍結契約と生アーティファクトのみから導出した。
- 封印テストへのアクセスは発生していない。`phase0/firewall_test.json` は
  `sealed_paths_read: []`, `sealed_paths_read_count: 0`, `known_sealed_files_count: 7` を記録する。
  本分析が読んだのは `phase1/cell_cache/`（960 ファイル）、`phase1/*.json`、`phase0/*.json`、
  および開放されている `results/runs/gpu_run5_20260823_ddd267b0/phase3/cells/*_validation_*.json` と
  `phase2/validation.json` のみで、いずれもファイル名が `sealed` で始まらない
  （`src/gpu_runclaude1/io_allowlist.py:81 is_sealed_path` の判定基準）。

---

## 0. 結論の要約

| 項目 | 値 |
|---|---|
| 一次エンドポイント `K` | **0** / `\|H\| = 130` |
| ladder cutpoint `C` | 3 |
| **v2.1 が命じる verdict of record** | **`undecidable`** |
| `partA_endpoints.json` の `verdict` フィールド | `no_gain_observed_bound_only` |
| 差異の原因 | v2.1 §7.5 item 3 / §10.3 の「両側感度解析が rung 上で不一致なら `undecidable`」を実装が適用していない |
| Gate A→B (i)–(ix) | (i)(ii)(iii)(iv)(vi)(vii)(viii)(ix) は成立。(v) は数値上成立するが §7.7 の short-circuit 規則により **gate として無効** |
| Gate B→C | (i) 違反。Part A が `undecidable` であるため Part C は実行されてはならなかったが、`phase3/` は `status: complete` で完走している |

---

## 1. タスク 1 — verdict of record の独立導出

### 1.1 v2.1 が `undecidable` を強制しうる条件の全列挙と照合

§10.3 の verdict テーブル `undecidable` 行、§7.2、§7.5 item 2/3、§7.6、§7.7.1、§7.7.3、§7.10 item 4
を突き合わせて列挙した。各条件の判定は下表のとおり。

| # | v2.1 の条件（出所） | 実現値 | 成立 |
|---|---|---|---|
| U1 | **PC4 fails** ⇒ `undecidable (gain indicator not demonstrated)`（§7.7.1, §10.1 (iii), §1 「唯一の条件」） | `gain_total = 100` (≥ 40), `gain_h = 100` (≥ 20), 寄与ファミリー 6（≥ 3）, `gates_ok = true` | 否 |
| U2 | **PC0 ≠ 170/170**（§7.7.1 HARD ABORT） | `n_eligible = 170`, `n_pass = 170`, note `systems: 80/80` | 否 |
| U3 | **PC2a ≠ その 2 つの既知値**（harness identity, §7.7.1, §10.1 (iv)） | M3 = 170/170 components / 80/80 systems, M0 = 170/170 / 80/80 | 否 |
| U4 | `K = 0` かつ **PC2c または PC2d < 95%** ⇒ `undecidable (matcher sensitivity insufficient)`（§7.7.3 null branch） | PC2c 170/170 = 100%, PC2d 170/170 = 100% | 否（ただし §3.6 の無効化議論を参照） |
| U5 | `K ≥ 1` かつ **PC3a または PC3b < 95%** ⇒ `undecidable (matcher specificity insufficient)` | `K = 0` のため非該当。値自体は PC3a 48/48 = 100%, PC3b 60/60 = 100% | 否 |
| U6 | **M0 が exact reproduction に失敗**（§7.6） | 独立再計算で 47,987 / 101,963 / 2,235 / 0-of-960 / 107-of-2040 / 8 ファミリー全て一致、mismatch 0 | 否 |
| U7 | **`\|H\|` / `\|L\|` が凍結 Q16 値と異なる** | `\|H\| = 130`, `\|L\| = 40` | 否 |
| U8 | **`m3_implementation_agreement` < 100%**（§7.4(b), A2-S6c） | `n_checked = 480`, `n_disagreements = 0`, agreement `1.0` | 否（ただし §5.3 の空洞性を参照） |
| U9 | **`could_not_evaluate_rate` > 2.0%**（§7.5 item 2） | 報告値 `0.00011540976879576318`（= 9/77983）。契約通りの分母では 9/101963 = `8.82673126526289e-05`。いずれも 2.0% を大きく下回る | 否 |
| **U10** | **§7.5 item 3 の両側感度解析が rung 上で不一致**（§7.5 item 3 本文＋§10.3 verdict テーブル） | `could_not_evaluate_rate > 0`（9 triples）。非マッチ方向 `K = 0` ⇒ `no_gain_observed_bound_only`。マッチ方向 `K_adv = 6 > C = 3` ⇒ `matcher_attributable_gain_confirmed`。`sensitivity_agrees = false` | **成立** |
| U11 | strata / ladder アーティファクト未書出、または token 未取得のまま照合を実行（§7.2 step 4–5, §14 item 8） | 両ファイルが書出・ハッシュ済。`require_strata_frozen` 経由の `StrataFrozenToken` が `score_cell` の必須引数で機構的に強制されている（`src/gpu_runclaude1/partA_driver.py:24 _require_token`） | 否 |
| U12 | `\|H\| < 40` かつ fallback も測定不能（§7.2 frozen fallbacks） | `\|H\| = 130`。`frozen_fallback_disposition: stratified_primary` | 否 |
| U13 | 一次エンドポイント計算前の abort（§10.2） | `phase1/manifest.json` `status: complete`, `n_cells_scored: 960`, `partA_cell_failures.json` は空配列 | 否 |

**成立する条件は U10 のみ。** したがって v2.1 が命じる Part A の **verdict of record は
`undecidable`** である。

### 1.2 §7.5 item 3 の逐語と、それがここで何を意味するか

> **Two-sided sensitivity analysis, mandatory whenever `could_not_evaluate_rate > 0`**: recompute
> the primary counting every could-not-evaluate triple as a **non-match** (the primary of record,
> the direction that does not inflate the gain) **and** as a **match** (the adversarial direction).
> If the two land on different ladder rungs, the verdict is **`undecidable`**.

`could_not_evaluate_rate > 0` は成立している（9 triples）。よって感度解析は義務であり、実際に
`src/gpu_runclaude1/endpoints.py` の `compute_primary_endpoint` はそれを実行して
`sensitivity_agrees = False` を得ている。しかし同関数は

```
verdict=verdict_non_match_direction,
```

と、非マッチ方向の label をそのまま `verdict` に代入しており、`sensitivity_agrees` が偽のときに
`undecidable` へ落とす分岐が **存在しない**。`scripts/phases/gpu_runclaude1_c0001_phase1_parta.py`
も `primary.verdict` をそのまま `partA_endpoints.json` に書き出す。

したがって `partA_endpoints.json:primary.verdict = "no_gain_observed_bound_only"` は
**スクリプトの出力であって契約の verdict of record ではない**。両者は食い違っており、これを
CRITICAL 所見として扱う（§6 CRIT-1）。

### 1.3 マッチ方向の再計数がここで実際に何をするか

`endpoints.py` の adversarial 再計数は次のとおり実装されている。

```
adversarial_gains = [
    1 if (gain == 0 and component.n_could_not_evaluate > 0) else gain
    for component, gain in zip(h_components, gains)
]
```

すなわち **`n_could_not_evaluate > 0` かつ `gain == 0` の H component を一律に `gain = 1` へ反転**
する。`could_not_evaluate` を保持する H component は 6 個で、その 6 個すべてが `m0_any = 0` である
（下表）。ゆえにこの反転は本コーパスでは契約の定義
$gain(s,i) = 1[\,m3\_any(s,i) = 1 \ \wedge\ m0\_any(s,i) = 0\,]$
と一致し、$K_{adv} = 0 + 6 = 6$、$6 > C = 3$ で最上段 rung
`matcher_attributable_gain_confirmed` に着地する。

- 潜在バグ（本コーパスでは不発）: 上記コードは `m0_any = 1` の component も反転しうる。契約上
  `gain` は `m0_any = 0` を要求するので、`m0_any = 1` の component は
  could-not-evaluate をマッチと数えても `gain = 0` のままでなければならない。stratum L の
  could-not-evaluate は 0 件、`m0_any = 1` の 13 component（すべて L）は could-not-evaluate を
  1 件も持たないため、この過剰 adversarial 性は本 run では顕在化していない。MAJOR（潜在）として
  記録する。

- rung 不一致は「際どい」ものではない。非マッチ方向は最下段、マッチ方向は中段を飛び越えて
  **最上段**である。9 triple / 101,963 triple（0.0088%）が verdict を最下段から最上段へ動かす。

---

## 2. タスク 2 — Gate A→B の逐項評価

（(i)–(ix) は v2.1 §10.1 「Gate A → B」表。数値は本分析が `cell_cache/` 960 ファイルから
独立に再計算したもので、要約フィールドを信用していない。）

| # | 条件 | 実現値（独立再計算） | 判定 |
|---|---|---|---|
| **(i)** | M0 arm が 47,987 の per-candidate フィールドと 101,963 の component 比較を **exactly** 再現、2,235 の component hit を含み、還元値 0/960（system）・107/2040（component）・8 ファミリー値も再現 | 候補 **47,987**、component 比較 **101,963**、M0 component hit **2,235**、格納フィールドとの mismatch **0**（`exponent_aware_skeleton_exact` 47,987 件、`component_exponent_aware_skeleton_exact` 101,963 件を全件突合）。cell 単位 ANY 還元: system **0/960**、component **107/2040**。ファミリー別 component: R01 **0/120**, R02 **0/120**, R03 **0/240**, R04 **56/240**, R05 **0/240**, R06 **0/360**, R07 **17/360**, R08 **34/360** — §7.6 の凍結値と完全一致 | **PASS** |
| **(ii)** | HARD — PC0 = 170/170 components かつ 80/80 systems | `PC0`: `n_eligible 170`, `n_pass 170`, note `systems: 80/80` | **PASS** |
| **(iii)** | HARD — PC4: `gain_pc4_total ≥ 40` かつ `gain_pc4_H ≥ 20` かつ寄与ファミリー ≥ 3 | `gain_total 100`, `gain_h 100`, `n_families_contributing 6`（R02, R03, R04, R06, R07, R08）, `n_ineligible_unverified 0`, `gates_ok true` | **PASS** |
| **(iv)** | HARD — PC2a harness identity: M3 = 170/170 & 80/80 かつ M0 = 170/170 & 80/80 | `PC2a`: `n_eligible 170`, `n_pass 170`, note に「M3 pass 80/80, M0 pass 80/80」。非 short-circuit 部分集合は空（構成上 `gain_pc2a = 0/170`） | **PASS**（harness identity としてのみ） |
| **(v)** | PC2c ≥ 95% かつ PC2d ≥ 95%（**null branch のみ**、`K = 0` で拘束） | PC2c **170/170 = 100%**, PC2d **170/170 = 100%**。ただし両者は `short_circuited: true`（`canonical_exact` が吸収）で、**非 short-circuit 部分集合は空** | 数値上 **PASS**、しかし §7.7 の「非 short-circuit 部分集合が空の control に gate を置いてはならない」規則により **gate として無効**（§6 CRIT-2） |
| **(vi)** | PC3a ≥ 95% かつ PC3b ≥ 95%（**gain branch のみ**、`K ≥ 1` で拘束） | PC3a **48/48 = 100%**（`ineligible_alteration_is_noop` 0）, PC3b **60/60 = 100%** | **PASS**（`K = 0` なので拘束しないが、非マッチ方向の verdict を守る向きに満たされている） |
| **(vii)** | `could_not_evaluate_rate ≤ 2.0%` | 報告値 `1.1541e-04`（9/77983、H 限定分母）。§7.5 item 2 の契約分母（全 scored triple）では **9/101963 = 8.82673e-05** | **PASS**（分母の逸脱は §6 MAJ-3） |
| **(viii)** | `m3_implementation_agreement = 100%` | `n_checked 480`, `n_disagreements 0`, `m3_implementation_agreement 1.0` | **PASS**（ただし 480 のうち 360 は空洞、§5.3） |
| **(ix)** | §7.6 の reproduction protocol が発火していない、または発火して解決済 | 発火せず（`m0_reproduction.json`: `n_cells_checked 960`, `n_mismatches 0`、全 report `ok: true`。`m0_reproduction_failures.jsonl` は §12.1 の規定通り不存在） | **PASS** |

**Gate A→B の総合**: 数値上は全項成立し、Part B への進行は許される。ただし (v) は
null branch を守るための唯一の sensitivity gate であり、それが §7.7 自身の規則で無効化されている
ことが Gate 通過の実質的な意味を大きく削る。null branch の sensitivity 保証は実際には
**PC0（identity 170/170）と PC4（gain 100/170、うち H 100）** が担っている。

**Gate A→B は verdict of record を決めない。** §10.3 は Gate 通過とは独立に U10 で
`undecidable` を命じる。両者は別の判定である。

---

## 3. タスク 3 — rule 03 / rule 04 に沿った分解

### 3.1 rule 04 の宣言（どの問いを測ったか）

本サイクルは **probe/readout、CKA/similarity、gradient、ablation/intervention、IOLE/single-layer FT、
selective FT のいずれも測定していない**。Part A が測るのは
**「評価器（matcher）が構造的に正しい候補を miss と採点していたか」** という
評価器妥当性のみである（v2.1 §16、§1.2「No layer-importance claim」）。層重要度に関する主張は
本分析からは一切導けない。

### 3.2 generation coverage / oracle candidate / selected candidate

`selected candidate` の定義について: v2.1 §7.8 A2-S5 は「the frozen selection rule
(`gpu_run5_selection.py:11`)」を参照するが、`src/evaluation/gpu_run5_selection.py:11
formula_selection_key` は **レコード群を system × seed でマクロ平均する構成選択キー**であり、
1 cell の beam 内部で候補を 1 つ選ぶ関数ではない。したがって cell 内 `selected candidate` は
その関数からは定義されない（契約の記述上の欠落、§6 MIN-2）。本分析では
**`selected = candidate_index == 0`（beam 順位 1 位）** と明示的に定義して報告する。

| 解像度 | 分母 | generation coverage / oracle（cell 内全候補の ANY） | selected（`candidate_index = 0`） |
|---|---|---|---|
| system, per cell — M0 | 960 | **0** | **0** |
| system, per cell — M1 | 960 | **0** | **0** |
| system, per cell — M3 | 960 | **0** | **0** |
| component, per (cell, component) — M0 | 2,040 | **107** | **58** |
| component, per (cell, component) — M1 | 2,040 | **0** | **0** |
| component, per (cell, component) — M3 | 2,040 | **107** | **58** |
| component, per (cell, component)、**stratum H のみ** — M0 / M1 / M3 | 1,560 | **0 / 0 / 0** | **0 / 0 / 0** |

- **generation vs selection の分離**: component 解像度では oracle 107/2040 に対し selected
  58/2040。すなわち beam 内に存在する構造一致の **45.8%（49/107）は top-1 に来ていない**。
  これは selection の損失であり、generation の損失とは別物である。
- **stratum H では oracle が全解像度でゼロ**。50 候補 beam 全体を見ても、H component に対する
  構造一致は M0・M1・M3 のいずれでも 1 件も存在しない。H に関しては
  **selection の問題ではなく、beam に何も無い**。
- 参考（rule 03、数値当てはめとの分離）: top-1 selected 候補の軌道当てはめは
  `input_r2` 中央値 **0.954**（p25 0.8988 / p75 0.9857）、`generalization_r2` 中央値 **0.3388**、
  `generalization_r2 > 0.9` の cell が **306/960**、`> 0.99` が **52/960**。cell ごとに
  `generalization_r2` 最良の候補を取ると `> 0.9` が **412/960**。
  それでも system 解像度の記号回復は全 matcher で **0/960**、H component 解像度で **0/1,560**。
  **数値当てはめは記号回復ではない**という区別が、同一コーパス上で定量的に示されている。

### 3.3 M0 / M1 / M3 を 3 つの集合として（nested cascade として提示することは v2.1 §7.8 A2-S5 が禁止）

**(a) candidate 解像度（system 指標、n = 47,987）**

| 量 | 値 |
|---|---|
| $\|M0\|$ / $\|M1\|$ / $\|M3\|$ | 0 / 0 / 0 |
| すべての対の共通部分・差 | 0 |

**(b) component 解像度（(cell, candidate, component) triple、n = 101,963）**

| 量 | 値 |
|---|---|
| $\|M0\|$ | **2,235** |
| $\|M1\|$ | **0** |
| $\|M3\|$ | **2,235** |
| $\|M0 \cap M1\|$ / $\|M0 \setminus M1\|$ / $\|M1 \setminus M0\|$ | 0 / **2,235** / 0 |
| $\|M0 \cap M3\|$ / $\|M0 \setminus M3\|$ / $\|M3 \setminus M0\|$ | **2,235** / **0** / **0** |
| $\|M1 \cap M3\|$ / $\|M1 \setminus M3\|$ / $\|M3 \setminus M1\|$ | 0 / 0 / **2,235** |

**(c) system 解像度**

| 量 | 値 |
|---|---|
| cell 単位 ANY（分母 960） M0 / M1 / M3 | 0 / 0 / 0 |
| system 単位 ANY over 12 cells（分母 80） M0 / M1 / M3 | 0 / 0 / 0 |

**(d) ANY-reduced per-component（12 cell × 全候補を OR、分母 170 = 一次エンドポイントの解像度）**

| 量 | 全体 (170) | H (130) | L (40) |
|---|---|---|---|
| $\|M0\|$ | **13** | **0** | **13** |
| $\|M1\|$ | **0** | 0 | 0 |
| $\|M3\|$ | **13** | **0** | **13** |
| $\|M3 \setminus M0\|$ = **`K` に相当する量** | **0** | **0**（= 一次エンドポイント `K`） | **0**（= A2-S1） |
| $\|M0 \setminus M3\|$ = **A2-S6b** | **0** | **0** | **0** |
| $\|M0 \setminus M1\|$ | **13** | 0 | 13 |

**(e) ファミリー別 ANY-reduced（分母は各ファミリーの component 数）**

| family | n | nH | M0 ANY | M3 ANY | M3 ANY (H) | gain |
|---|---|---|---|---|---|---|
| R01 | 10 | 10 | 0 | 0 | 0 | 0 |
| R02 | 10 | 10 | 0 | 0 | 0 | 0 |
| R03 | 20 | 20 | 0 | 0 | 0 | 0 |
| R04 | 20 | 10 | 6 | 6 | 0 | 0 |
| R05 | 20 | 20 | 0 | 0 | 0 | 0 |
| R06 | 30 | 30 | 0 | 0 | 0 | 0 |
| R07 | 30 | 20 | 2 | 2 | 0 | 0 |
| R08 | 30 | 10 | 5 | 5 | 0 | 0 |
| 計 | 170 | 130 | **13** | **13** | **0** | **0** |

**この分解の中心的事実**: 実データ上で **M3 集合と M0 集合は完全に一致する**。triple 解像度で
2,235 = 2,235、対称差 0。cell×component で 107 = 107。ANY-reduced で 13 = 13。system で 0 = 0。
M3 は実 beam 候補に対して **M0 に何も足していない**。同時に M1 は全解像度で空であり、
$M0 \subseteq M1$ は 2,235 回破れている（§3.5）。

### 3.4 stratum H (130) / L (40) 別

| 量 | H (130) | L (40) |
|---|---|---|
| gain（一次 / A2-S1） | **0** | **0** |
| gain rate | 0.0（Wilson 95% [0.0000, 0.0287]） | 0.0（Wilson 95% [0.0000, 0.0876]） |
| H − L 差（A2-S1） | **0.0** | — |
| M3 level（A2-S2、ANY-reduced） | **0/130 = 0.0** | **13/40 = 0.325** |
| M3 level 全体（A2-S2） | **13/170 = 0.07647058823529412** | — |
| scored triples | 77,983 | 23,980 |
| could-not-evaluate triples | **9** | **0** |
| could-not-evaluate を持つ component | **6** | 0 |

- `partA_endpoints.json:secondaries` の値（`l_stratum_gain_rate 0.0`, `l_stratum_n 40`,
  `h_minus_l_difference 0.0`, `m3_level_overall 0.07647058823529412`, `m3_level_h 0.0`,
  `m3_level_l 0.325`）は独立再計算と一致する。
- **A2-S1 の構造的弱さ（v2.1 §7.8 が事前に警告した通り）**: L は R04 / R07 / R08 にのみ存在し、
  その 3 ファミリーが 107 hit のすべてを担う。L の 13/40 component は `m0_any = 1` であるため
  `gain` に寄与できない。H − L 差 0 は「gain が H に住む」根拠には読めない。
- Bonferroni 補正（§9.4 item 2、Part A は `m = 9`、$\alpha/9 = 0.005555555555555556$,
  $z = 2.7729212946086634$）— アーティファクトには未記載のため本分析で計算した:

| endpoint | 点推定 | Wilson 95% | Bonferroni $\alpha/9$ |
|---|---|---|---|
| A2-S1 L-stratum gain 0/40 | 0.0 | [0.000000, 0.087622] | [0.000000, 0.161234] |
| A2-S2 M3 level overall 13/170 | 0.0764706 | [0.045232, 0.126427] | [0.036558, 0.153038] |
| A2-S2 M3 level H 0/130 | 0.0 | [0.000000, 0.028702] | [0.000000, 0.055844] |
| A2-S2 M3 level L 13/40 | 0.325 | [0.200845, 0.479823] | [0.163040, 0.543392] |
| A2-S3 system M3 ANY 0/80 | 0.0 | [0.000000, 0.045818] | [0.000000, 0.087686] |

これらの区間は多重性制御されておらず、いかなる secondary も confirmatory な主張を支えない
（§9.4 item 2 の凍結文）。

### 3.5 単調性（A2-S6b と monotonicity audit）

| 量 | 値 |
|---|---|
| `n_checked` | 149,950（= 47,987 system 行 + 101,963 component 行） |
| `n_violations` | **2,235** |
| `violation_rate` | **0.014904968322774258** |
| `severity`（コード出力） | `CRITICAL` |
| 違反の内訳 | すべて component 解像度の `M0->M1`（2,235 件）。`M1->M3` 違反は 0 件 |
| **A2-S6b（`m0_any = 1` かつ `m3_any = 0` の component 数）** | **0** |
| triple 解像度の $\|M0 \setminus M3\|$ | **0** |

- 違反の正体は「M3 が M0 より非寛容」ではなく、**M1 が定数を collapse しない厳格レベル**である
  ことに尽きる。M0 は定数 collapse 付き exponent-aware canonical skeleton、M1 は
  `canonical_exact`（定数まで一致）である。よって $M0 \subseteq M1$ は **設計上偽**であり、
  2,235 件の違反は M0 hit 集合そのものである。v2.1 §7.5 item 4 はこの tripwire を明示的に
  削除しており、`monotonicity_severity: CRITICAL` は **いかなる gate も駆動しない**。
- ただし `manifest.json:go_conditions.monotonicity_severity = "CRITICAL"` という文字列が
  マニフェストに残っているのは、契約が「non-gating」と宣言した量に CRITICAL ラベルを付けて
  下流へ流す危険である（§6 MIN-1）。
- **audit の設計上の空洞**: `audit_monotonicity` は `M0->M1` と `M1->M3` の連鎖のみを検査し、
  `M0->M3` を直接検査しない。M1 が恒等的に空である本コーパスでは `M1->M3` の検査は
  **空虚に成立**する。したがって「撤回されたバグを捕まえたはずの検査」（§7.5 item 4）は
  monotonicity audit 側では機能していない。$\|M0 \setminus M3\| = 0$ を実際に確立したのは
  本分析による直接計算であり、その値は `matcher_monotonicity.json` にも
  `partA_endpoints.json` にも記録されていない（§6 MAJ-2）。

### 3.6 E0 / E1' / E2 / E3 に対して、これが何を言い、何を言わないか

**言えること。**

1. **E0（評価器アーティファクト）について、v2.1 §1.3 M-iii の書換クラスに限って**:
   H stratum の 130 component 全体で `gain = 0`。さらに、そもそも H では
   **oracle（beam 全体の ANY）が M0・M1・M3 すべてでゼロ**である。M3 が M0 に何も足さなかったのは
   「M3 が候補を見落としたから」ではなく、**H に対して beam の中に一致構造が存在しないから**である。
   これは E0 に対する（この書換クラス内での）強い制約である。
2. **M-i（P4 の符号非対称）については何も言えない。** M0 が 170/170 で吸収するため
   `gain` は構成上恒等的に 0（§1.3）。
3. **M-ii（Hill 項のアフィン分解）については何も言えない。** どの matcher も証明できない
   （PC2b: 60 eligible / 0 matched、凍結期待値 0 と一致）。C0001 は E0 がこの機構で働くことを
   確認も反証もできない（§1.3 の凍結制限）。
4. **E1'（生成器サポート除外）**: Part A は直接測らない。ただし H で oracle = 0 という事実は
   E1' と整合的である。Part B（`partB_endpoints.json`, `n_in_support = 71`）が担う問いであり、
   本分析は Part A の範囲に留める。
5. **E2（事前確率質量）/ E3（探索誤差）**: Part A は測定していない。H で oracle = 0 は
   「生成されなかった」ことを示すが、「サポート外だから（E1'）」「確率が低いから（E2）」
   「beam が届かなかったから（E3）」を区別しない。§10.3 の 5 バケット分割は Part B / Part C の
   結果を要し、しかも Part C は Gate B→C 違反下で走っている（§4.4）。

**言えないこと。**

- 「E0 は偽」「canonicalization は不要」「M0 と M3 は同等」— いずれも §9.5 item 1 が明示的に
  禁じる。M0 と M3 が実データ上で同一集合を与えたことは **等価性の証明ではない**（rule 01 item 8）。
  PC4 は同じ code path で 100/170 の gain を出しており、両者は同じ関係ではない。
- 「原因は X」という単一原因の主張（§10.3、§1.1）。E0 / E1' / E2 / E3 は排他ではない。
- 生物学的因果に関するいかなる主張（rule 01 item 7、§1.2）。対象は合成 Hill 系である。
- 層重要度に関するいかなる主張（rule 04、§16）。

**さらに、この cycle の verdict が `undecidable` であるため、上記 1. は
「E0 に対する証拠」として引用してはならない。** §9.5 item 0 が `K` の引用可能性を PC4 の
通過に条件付けているのと同じ理由で、§10.3 は rung 不一致下の `K` に verdict を与えない。
上記 1. は **measured fact（測定事実）** として記録できるが、**verdict-bearing claim** ではない。

---

## 4. タスク 4 — 一次エンドポイントの脆弱性

### 4.1 could-not-evaluate triple の全列挙

全 9 triple。失敗理由は **全件 `SymbolicEquivalenceTimeout`**（`ParseError`,
`SkeletonParseFailure`, `SkeletonEvaluationFailure` は 0 件）。
`ComponentCountMismatch` は 0 件（`(true_dim, n_pred_components)` が全 47,987 候補で対角、
§7.4 の記述通り）。`valid == false` の候補も 0 件。

| # | cell_id | cand idx | comp idx | system_id | family | stratum | failure_reason |
|---|---|---|---|---|---|---|---|
| 1 | `R03_validation_d101_005_b2_n0p05_r0` | 14 | 0 | `R03_validation_d101_005` | R03 | H | `SymbolicEquivalenceTimeout` |
| 2 | `R05_validation_d101_000_b2_n0p05_r0p5` | 9 | 1 | `R05_validation_d101_000` | R05 | H | `SymbolicEquivalenceTimeout` |
| 3 | `R07_validation_d101_000_b1_n0_r0` | 47 | 1 | `R07_validation_d101_000` | R07 | H | `SymbolicEquivalenceTimeout` |
| 4 | `R07_validation_d101_002_b2_n0_r0p5` | 16 | 2 | `R07_validation_d101_002` | R07 | H | `SymbolicEquivalenceTimeout` |
| 5 | `R07_validation_d101_003_b0_n0_r0p5` | 35 | 1 | `R07_validation_d101_003` | R07 | H | `SymbolicEquivalenceTimeout` |
| 6 | `R07_validation_d101_003_b2_n0_r0p5` | 19 | 1 | `R07_validation_d101_003` | R07 | H | `SymbolicEquivalenceTimeout` |
| 7 | `R07_validation_d101_009_b0_n0_r0` | 6 | 2 | `R07_validation_d101_009` | R07 | H | `SymbolicEquivalenceTimeout` |
| 8 | `R07_validation_d101_009_b1_n0_r0` | 12 | 2 | `R07_validation_d101_009` | R07 | H | `SymbolicEquivalenceTimeout` |
| 9 | `R07_validation_d101_009_b1_n0p05_r0` | 29 | 2 | `R07_validation_d101_009` | R07 | H | `SymbolicEquivalenceTimeout` |

**触れる component（6 個、すべて stratum H、すべて `m0_any = 0` / `m1_any = 0` / `m3_any = 0`）**

| system_id | comp idx | family | stratum | n_could_not_evaluate | n_scored |
|---|---|---|---|---|---|
| `R03_validation_d101_005` | 0 | R03 | H | 1 | 600 |
| `R05_validation_d101_000` | 1 | R05 | H | 1 | 600 |
| `R07_validation_d101_000` | 1 | R07 | H | 1 | 600 |
| `R07_validation_d101_002` | 2 | R07 | H | 1 | 600 |
| `R07_validation_d101_003` | 1 | R07 | H | 2 | 600 |
| `R07_validation_d101_009` | 2 | R07 | H | 3 | 600 |

**触れる family**: R03（1 component）、R05（1 component）、R07（4 component）。
R01 / R02 / R04 / R06 / R08 は 1 件も含まない。

### 4.2 verdict が pivot する triple 数

- **9 triple**（101,963 triple のうち 0.008827%）、**6 component**（130 のうち 4.6%）、
  **3 family**（8 のうち）。
- この 9 triple が一つも存在しなければ `could_not_evaluate_rate = 0` となり、§7.5 item 3 の
  感度解析は義務でなくなり（実装も `verdict_match_direction = verdict_non_match_direction` を
  返し）、verdict of record は `no_gain_observed_bound_only` になっていた。
- 逆に adversarial 方向は最下段から **最上段**へ飛ぶ。中段（`weak_gain`, 1–3）を経由しない。
  6 > C = 3 だからである。`C` は `\|H\|` のみから決まる凍結値であり、動かしていない。

### 4.3 これら 9 triple が実際にどういう比較なのか（生の式）

9 件すべてで、候補側の該当 component は **`sin(...)` を含む三角関数項 + 二次形式**であり、
真値側は Hill 有理式である。例（#3）:

- truth component: `1.581 * x_0 * 1/(0.7293 + x_0) + -1 * 0.62 * x_1`
- candidate component: `0.0966 * sin(1.0420 + 0.0258 * x_1) + -0.0032 * (-0.9778 + -1 * x_2)**2`

Hill-4 の綴りについて（正規化形の確認）: 例 #4 の truth component は
`1.188 * ((x_0)**2)**2 * 1/(0.8272 + ((x_0)**2)**2) * 1 * ((x_1)**2)**2 * 1/(0.5399 + ((x_1)**2)**2) + -1 * 0.658 * x_2`
であり、指数 4 は `((x_i)**2)**2`（prefix では `pow,pow,x_i,2,2`）として綴られている。
`pow4` というトークンは存在しない。**比較は R1 に従い両側 infix**である
（`score_pair` は `parse_system(..., as_prefix=False)` を両側に適用し、M3 は
`skeleton_equivalence_with_reason(true_raw[index], cand_raw[index])` を infix 文字列に適用する）。
`true_structure.exponent_aware_skeleton`（prefix 由来）は matcher に到達していない。

**探索的診断（凍結計器の出力ではない。verdict を変更しない）**: 9 件の skeleton 差
$sk_{true} - sk_{pred}$ を 2 通りの独立な代入点で数値評価したところ、9 件すべてで有意にゼロから
離れた（$|d|$ は 0.4485 〜 20.52）。すなわちこの 9 件は実質的には `proved_different` である。
ただし **凍結された M3 の出力は `could_not_evaluate` であり、それを書き換えることはしない**。
timeout（`SYMPY_OP_TIMEOUT_SEC = 10.0`）を上げて結果を救済することは rule により禁じられており、
本分析は行っていない。そして重要なことに、この診断は **verdict of record を変えない**:
§7.5 item 3 の規則は機械的であり、`could_not_evaluate_rate > 0` かつ rung 不一致という
2 条件のみを見る。

したがって Part A の verdict `undecidable` は、**データの曖昧さではなく、契約自身の
感度解析規則と cutpoint `C = 3` の相互作用**によって生じている。これは正直に述べるべき点である:
9 件の timeout は科学的には非マッチであって gain 候補ではないが、契約が事前に選んだ
adversarial 再計数はそれらを一律に gain と数え、そのため rung が動く。**これは事後的に
規則を緩める理由にはならない**（rule 01 item 3）。規則は凍結時に選ばれたものである。

### 4.4 波及: Gate B→C

v2.1 §10.1 Gate B→C (i) は「Part A is **not** `undecidable`」を要求する。verdict of record は
`undecidable` であるから、**Part C は C0001 では走ってはならなかった**。実際には
`phase3/gate_b_to_c.json` が

```
"ok": true, "reasons": [], "part_a_verdict": "no_gain_observed_bound_only",
"n_in_support": 71, "min_in_support_required": 30
```

を記録し、`phase3/manifest.json` は `status: complete`, `n_cells_scored: 960` である。
原因は 2 段:

1. `gate_b_to_c` は `partA_endpoints.json:primary.verdict` を読む。そのフィールドが
   §1.2 の理由で誤っている。
2. `scripts/phases/gpu_runclaude1_c0001_phase3_partc.py:36 gate_b_to_c` は
   `verdict == "matcher_attributable_gain_confirmed"` と `verdict is None` のみを refusal と
   しており、**`undecidable` の検査が存在しない**。仮に (1) が正しく `undecidable` を
   書いていても、この gate は通してしまう。

加えて Gate B→C (ii) は「`n_in_support ≥ 30` **かつ** Part A component gain = 0」を要求するが、
実装は `n_in_support` のみを検査する。本 run では `K = 0` のため後段の連言は自明に真であり、
実害はない（MINOR）。

---

## 5. タスク 5 — PC4 陽性対照の実現値と、それが与える解釈上の licence

### 5.1 実現値

| 量 | 値 | 凍結閾値 |
|---|---|---|
| `n_eligible` | **170** / 170 components（`n_ineligible_rewrite_unverified = 0`, `textually_unchanged = 0`） | ≥ 40 components（最小 eligible set） |
| `gain_total` | **100** | ≥ 40（2.5× マージン） |
| `gain_h` | **100** | ≥ 20（5× マージン） |
| `n_families_contributing` | **6**（R02, R03, R04, R06, R07, R08） | ≥ 3（2× マージン） |
| `gates_ok` | **true** | HARD ABORT gate |
| `rate` | 100/170 = **0.5882352941176471** | — |

§7.3 の凍結予測「total 100, H 100, L 0, 6 of 8 families」（Q12 の検証）と完全一致。
PC4 の `gain` は `gpu_runclaude1.endpoints.gain_indicator` を直接呼び、一次エンドポイントと
**同一の関数オブジェクト**を使っている（`src/gpu_runclaude1/controls.py:507`）。§7.10 item 3 を満たす。

**PC4 の 170 instance の内訳（本分析が独立に再計算。`partA_controls.json` には未記載）**

| stratum | 分類 | n | family |
|---|---|---|---|
| H | `gain`（M0 miss かつ M3 match） | **100** | R02 10, R03 20, R04 10, R06 30, R07 20, R08 10 |
| H | `no_gain_m3_failed`（M0 miss かつ **M3 も `proved_different`**、`failure_reason` は `None`） | **30** | **R01 10, R05 20** |
| L | `no_gain_m0_also_matched`（M0 が書換を吸収、short-circuit） | **40** | R04 10, R07 10, R08 20 |
| 計 | | 170 | |

これは PC4 が同時に **計器の限界も測っている**ことを意味する。`sympy.together` による
共通分母書換は 30 個の H component（R01 全 10、R05 全 20）で **M3 が証明に失敗する**。
理由は定数 collapse そのものである。例（R01）:

- 元: `0.1954 + 0.8878 * x_0 * 1/(0.8392 + x_0) + -1 * 0.3968 * x_0`
- `together` 後: `(-0.3968*x_0*(x_0 + 0.8392) + 1.0832*x_0 + 0.16397968)/(x_0 + 0.8392)`

3 個以上の異なる定数が単一の記号 `c` に collapse されると恒等式が崩れる。したがって
**M3 の H 上での sensitivity は 100/130 = 0.7692307692307693（Wilson 95% [0.6897, 0.8333]）
であって 1.0 ではない**。R01 と R05 では 0/10 と 0/20 である。

### 5.2 PC4 が `K = 0` に与える licence と、与えない licence

**与えるもの。**

- §9.5 item 0 / §1「唯一の条件」の前提が満たされた。すなわち `K = 0` を **E0 に対する証拠として
  報告する資格の必要条件**はクリアした。gain 指標は実際に発火しうることが、
  **同一 code path・同一 `gain` 関数・同一 infix 表現・同一 timeout** の下で示された。
  `K = 0` は「gain を出せない計器が作った 0」ではない。
- その発火は stratum H の上で示された（100/100 が H）。H が一次エンドポイントの母集団である
  から、これは正しい stratum 上の実証である。

**与えないもの（§7.7.2 が明記、および本分析が追加するもの）。**

- **機構の検証ではない。** 実 beam 候補にそのような書換が現れることを示していない。それを測るのが
  一次エンドポイントであり、その答えは H で 0 である（しかも beam 全体の oracle が 0）。
- **開示済み値の検証にすぎない。** Q12 の再現であり、非失敗は発見ではない。
- **E0 の 2 つの開示機構を復活させない。** M-i は M0 に吸収され、M-ii は届かない（§1.3）。
- **一様な sensitivity を意味しない。** 上記の 100/130 が示す通り、demonstrated class 内でも
  M3 は H の 30 component（R01, R05）で発火不能である。したがって
  **`K = 0` の「H の 130 component すべてで gain が観測されなかった」という文言は、
  demonstrated rewrite class に関しては実効的に 100 component についての言明**である。
  探索的補正（凍結表ではない）:

| 真の per-component gain rate $p$ | $1-(1-p)^{130}$（§7.3 凍結表） | $1-(1-p)^{100}$（PC4-sensitive H のみ、探索的） |
|---|---|---|
| 0.0525 | 0.9991 | 0.9955 |
| 0.03 | 0.9809 | 0.9524 |
| 0.02 | 0.9277 | 0.8674 |
| 0.01 | 0.7292 | 0.6340 |
| 0.005 | 0.4788 | 0.3942 |

  検出力は依然高いが、§7.3 の表は demonstrated class に対する検出力をやや過大に述べている。
  これは **探索的所見**であり、凍結表を置き換えるものではない。
- **`K = 0` を verdict として引用する資格を与えない。** PC4 は §10.3 の `undecidable` トリガー
  U1 を否定するだけで、U10 には触れない。verdict of record は依然 `undecidable` である。

### 5.3 A2-S6c（in-pass agreement census）の空洞性 — PC4 とは別だが licence に関わる

`m3_implementation_agreement_census.json`: `n_checked 480`, `n_disagreements 0`,
`m3_implementation_agreement 1.0`, `ok true`。

- §7.4(b) は「every 100th **(cell, candidate, component)** triple」を要求する。実装
  （`scripts/phases/gpu_runclaude1_c0001_phase1_parta.py` の `census_triples`）は
  **(cell, candidate) ペア**を数えており、47,987 / 100 = **480** 件を抽出した。
  triple 解像度なら約 1,020 件になる。契約本文の「≈ 480 extra M3 calls」というコスト見積は
  candidate 解像度と整合しており、契約自身に内部不整合がある。
- さらに重大な点: census は **system 全体の文字列**（`true_formula` 対
  `candidate_formula_raw`）を `symbolic_recovery` に渡す。多成分系の文字列は `" | "` を含むため
  **恒等ペアですら** `skeleton = 0.0`, reason `SkeletonParseFailure` を返す（本分析で確認:
  `symbolic_recovery(tf, tf)["skeleton"] == 0.0`）。抽出された 480 件のうち
  **360 件（dim 2 が 180、dim 3 が 180）が多成分系**であり、両実装が同じ parse 失敗を返して
  **空虚に一致**している。genuine な単一成分比較は dim-1 の **120 件**のみで、
  これは一次エンドポイントの 101,963 triple の **0.12%** にあたる。
- 実質的な保証は Gate 0 item 11 の側にある: `phase0/m3_agreement_test.json` は
  `n_pairs_realized 1178`（`n_pairs_target_v2_1 910`）, `n_disagreements 0`,
  `disagreement_rate 0.0` を記録し、こちらは `teacher_components_infix` の
  **component 単位**ペア（PC0 170, PC2a 170, PC2b 60, PC2c 170, PC2d 170, PC4 170, PC4b 60,
  PC3a 78, PC3b 130）である。`skeleton_equivalence_with_reason` を
  `symbolic_recovery(...)["skeleton"]` の代替として使う根拠は、A2-S6c ではなく
  **この 1,178 ペアのテスト**が支えている。

---

## 6. 所見（CRITICAL / MAJOR / MINOR）

### CRITICAL

**CRIT-1 — verdict of record と実装出力の不一致。**
`could_not_evaluate_rate = 1.1541e-04 > 0` かつ `sensitivity_agrees = false`。
§7.5 item 3 と §10.3 は `undecidable` を命じる。`partA_endpoints.json:primary.verdict` は
`no_gain_observed_bound_only`。`src/gpu_runclaude1/endpoints.py:compute_primary_endpoint` は
`sensitivity_agrees` を計算しながら verdict 決定に反映しない。
影響: Part A の verdict、Gate B→C、下流の全アーティファクトの label。
**`no_gain_observed_bound_only` を引用したいかなる主張も、訂正されるまで支持されない。**

**CRIT-2 — null branch の sensitivity gate が契約自身の規則で無効。**
Gate A→B (v) は PC2c / PC2d に置かれた gate であり、`K = 0` で拘束される唯一の
matcher-sensitivity gate である。しかし両 control は `short_circuited: true` で
**非 short-circuit 部分集合が空**であり、§7.7 は「no gate may be placed on a control whose
non-short-circuited subset is empty」と定める（§7.7.1 はこの規則で PC2a の sensitivity gate を
削除した）。したがって null branch には契約上有効な sensitivity gate が存在しない。
緩和: PC0（170/170）と PC4（100/170、うち H 100、非 short-circuit）が実質的な保証を与える。
だが §5.1 の内訳が示すように PC4 の H sensitivity は 100/130 であり、
R01 / R05 の 30 component では demonstrated class ですら発火不能である。

**CRIT-3 — Gate B→C 違反下で Part C が完走している。**
Gate B→C (i) は「Part A is not `undecidable`」。verdict of record は `undecidable`。
`phase3/gate_b_to_c.json` は `ok: true` を記録し、`phase3/manifest.json` は
`status: complete`。加えて `gate_b_to_c` の実装には `undecidable` の検査自体が存在しない
（`matcher_attributable_gain_confirmed` と `None` のみを refusal とする）。
Part C の結果は Part A の verdict が訂正されるまで前提が成立していない。

### MAJOR

**MAJ-1 — 義務付けられた逐語文が 1 つも書かれていない。**
§12.1 は `partA_endpoints.json` に「the verdict with **both** mandated sentences
(§9.5 items 0/1 and 6) in machine-readable fields」を要求する。実際に書かれている
`verdict_scope_sentence` は初期条件に関する別の文であり、
§9.5 item 0 の逐語文（PC4 条件）、§9.5 item 1 の `K = 0` 変種、§9.5 item 6 の scope 文、
§9.3 の frozen disclosure sentence のいずれも存在しない。
§9.3 自身が理由を述べている: 「labels travel downstream and caveats do not」。

**MAJ-2 — §9.5 item 1 の `[value]`（family-clustered power）が計算されていない。**
§7.3 は「the cluster bootstrap must report the family-clustered power at `\|H\| = 130`
alongside them, and the **smaller** of the two is the number the report quotes」と定めるが、
`ladder.py` にもアーティファクトにもこの量は存在しない。
また契約は clustered power の統計モデル（ICC の想定）を指定していないため、指示は
現状では実行不能である。探索的な範囲だけは示せる: family 単位で完全にクラスタ化した
極限（実効 n = 8、ICC = 1）では $1-(1-0.0525)^8 = 0.3504$、独立仮定では 0.9991。
すなわち family-clustered power は **[0.3504, 0.9991]** のどこかにあり、
「小さい方を引用する」規則は現時点で数値を持たない。
`icc_not_estimable_zero_count`（§12.1 が要求）も未記載である。

**MAJ-3 — `could_not_evaluate_rate` の分母が契約と異なる。**
§7.5 item 2 は分母を「all scored (cell, candidate, component) triples」と定める（= 101,963）。
実装は H stratum の scored triple のみを合計する（= 77,983）。
報告値 `1.1541e-04` に対し契約値は `8.82673e-05`。gate (vii) の判定は変わらない
（どちらも 2.0% 未満）が、A2-S6 は報告エンドポイントであり、値が違う。

**MAJ-4 — A2-S6c は 75% が空虚。**
§5.3 の通り、480 件中 360 件が両実装同一の `SkeletonParseFailure`。genuine な
component 単位の二重計算は 0 件、単一成分系の 120 件のみが実質的。
gate (viii) は満たされるが、その保証内容は endpoint の解像度をカバーしていない。

**MAJ-5 — 報告義務のある secondary / アーティファクトが欠落。**
`partA_endpoints.json` に存在しない: A2-S3、A2-S4、A2-S5（cascade 3 集合表、oracle vs selected）、
A2-S6b、A2-S6c、A2-S8、interval (a)/(b)/(c) の選定理由、Bonferroni $\alpha/9$ 区間、ICC 欄。
`phase1/` に存在しない §12.1 指定ファイル: `partA_records.jsonl`、
`partA_component_summary.json`、`partA_system_summary.json`、`partA_failures.jsonl`、
`m0_hits_stratification.json`（§7.10 step 7）。run root の `manifest.json` も不在
（phase 別 manifest のみ）。`phase0/sealed_inventory.json` も不在（内容は
`firewall_test.json` に 7 件として含まれる）。
本分析の §3.3・§3.5・§4.1 はこれらを `cell_cache/` から再構成したものである。

**MAJ-6 — adversarial 再計数の潜在バグ。**
`m0_any = 1` の component も反転しうる実装であり、契約の `gain` 定義より過剰に adversarial。
本コーパスでは L に could-not-evaluate が 0 件のため不発。将来の run では verdict を
誤って `undecidable` 側へ倒しうる。

**MAJ-7 — monotonicity audit は `M0 -> M3` を直接検査しない。**
`M0->M1` と `M1->M3` の連鎖のみ。M1 が恒等的に空のため後段は空虚に成立。
「撤回されたバグを捕まえたはずの検査」（§7.5 item 4）は audit 側では機能しておらず、
A2-S6b = 0 および triple 解像度の $\|M0 \setminus M3\| = 0$ を確立したのは本分析の直接計算のみで、
どのアーティファクトにも記録されていない。

### MINOR

- **MIN-1** — `manifest.json:go_conditions.monotonicity_severity = "CRITICAL"`。
  §7.5 item 4 は tripwire を削除済で non-gating。CRITICAL という文字列が下流へ流れる危険。
- **MIN-2** — §7.8 A2-S5 の `selected candidate` は `gpu_run5_selection.py:11
  formula_selection_key` からは定義できない（構成選択キーであり cell 内候補選択ではない）。
  本分析は `candidate_index == 0` と明示定義した。
- **MIN-3** — §7.4(b) の「triple」と「≈ 480 extra M3 calls」が契約内部で不整合。
- **MIN-4** — phase0 manifest commit `b731cddd168390c973dbb0974349e4a2c55b9113` と
  phase1 manifest commit `8ff622defc227b4598e0094fc000b8227c4ffdad` が異なる。
  差分は `GPU_RUNclaude1/analyses/C0001_precondition_verification.md`、
  `research_state.md`、`GPU_RUNclaude1/tests/test_gate_b_to_c.py`、
  `scripts/phases/gpu_runclaude1_c0001_phase3_partc.py` の 4 ファイル・329 行の追加のみで、
  Part A の matcher path には触れていない。Part A の再現性への影響なし。
- **MIN-5** — Gate B→C (ii) の「かつ Part A component gain = 0」の連言が実装で未検査。
  `K = 0` のため実害なし。
- **MIN-6** — §12.1 は Stage 8 分析を `GPU_RUNclaude1/analyses/C0001_analysis.md` と命名する。
  本文書は指示されたパス `C0001_partA_stage8_analysis.md` に置かれている（Part A 限定であるため）。

---

## 7. 検証できなかったもの（`unverified`）

- 9 件の `SymbolicEquivalenceTimeout` が、timeout を伸ばしたときに M3 で
  `proved_different` になるか — **測定していない**（rule により timeout の変更を禁止）。
  §4.3 の数値診断は skeleton 差の非ゼロ性を示すが、凍結 M3 の出力ではない。`unverified`。
- family-clustered power の実値 — 契約がモデルを指定しておらず、アーティファクトにも無い。
  §6 MAJ-2 の区間 [0.3504, 0.9991] は探索的な両端であり、契約の言う「小さい方」ではない。`unverified`。
- H で oracle = 0 である理由の E1' / E2 / E3 への帰属 — Part A は測定していない。`unverified`。
- 「M3 は R01 / R05 の Hill 形状に対して原理的に発火不能」という一般化 — 本分析は
  `sympy.together` の 1 書換クラスについて 30/30 の失敗を測ったのみ。他の書換クラスは未測定。`unverified`。

---

## 8. 訂正されるべきこと（次アクションの候補、優先順）

1. **`partA_endpoints.json` の verdict を契約の verdict of record に合わせる。**
   コードを変えて再計算するのではなく（一次エンドポイントの数値は正しい）、
   §7.5 item 3 の判定を適用した verdict を記録し、`sensitivity_verdict_non_match_direction`
   / `sensitivity_verdict_match_direction`（`endpoints.py` は既に計算している）を
   機械可読フィールドとして書き出す。同時に §9.5 items 0/1/6 と §9.3 の逐語文を追加する。
2. **Gate B→C に `undecidable` の検査を追加し、Part C の前提が崩れていることを記録する。**
   Part C の生データは保存する（rule 01 item 4/5）。
3. **A2-S6b、A2-S5 の 3 集合表、A2-S3/S4/S8、Bonferroni 区間、ICC 欄、
   §12.1 の欠落ファイルを書き出す。** 本文書 §3.3–§3.5、§4.1 の数値がその内容である。
4. **`could_not_evaluate_rate` の分母を契約通り（101,963）に直す。**
5. **PC4 の per-instance 内訳（gain 100 / m3_failed 30 / m0_also_matched 40、family 別）を
   `partA_controls.json` に記録する。** これは計器の限界に関する再利用可能な事実である
   （§10.4 が Part A の「reusable instrument characterization」として要求するもの）。
6. **CRIT-2 について**: null branch の sensitivity gate を PC2c/PC2d から
   非 short-circuit な control（PC4 の系列）に移すか、あるいは
   「null branch に有効な sensitivity gate は存在しない」ことを制限として明記するか。
   これは preregistration の変更にあたるので新 cycle ID を要する（§2.5）。

---

## 9. 厳守した区別（rule 01）

- **数値当てはめは記号回復ではない。** top-1 の `input_r2` 中央値 0.954、
  `generalization_r2 > 0.9` が 306/960 であっても、system 記号回復は 0/960、
  H component 記号回復は 0/1,560 である。
- **記号回復は生物学的因果ではない。** 対象は合成 Hill 型 GRN であり、
  遺伝子調節に関する主張は一切していない。
- **非有意は同等ではない。** M0 集合と M3 集合が実データ上で一致したことは
  「M0 と M3 は同等」を意味しない。PC4 が同一 code path で 100/170 の gain を出している。
  `K = 0` の bound of record は family-clustered の [0, 0.3244075683414076] であり **広い**。
  その幅こそが所見である（§9.5 item 5）。
- **生成と選択、oracle と selected を分離した**（§3.2）。
- **無効・失敗した生成式を保持した**（`valid == false` 0 件、`ComponentCountMismatch` 0 件、
  `SymbolicEquivalenceTimeout` 9 件をすべて式付きで列挙、§4.1・§4.3）。
- **探索的解析は探索的と明記した**（§4.3 の数値診断、§5.2 の検出力補正、§6 MAJ-2 の power 区間）。
