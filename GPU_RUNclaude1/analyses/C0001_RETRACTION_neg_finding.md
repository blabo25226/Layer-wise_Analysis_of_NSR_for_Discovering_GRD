# 撤回 — C0001 の `neg` 正規化「発見」は私自身の分析が生んだ人工物だった

**発行**: 2026-09-09、supervisor により、C0001 Stage 3 レビュー中。
**重大度**: material（実質的）。撤回する主張は、コミットメッセージ (`bfbf727`)、
`human_review_queue.md` (HRQ-0002)、`C0001_stage1_preobservation.md`、
`C0001_exploratory_neg_canonicalization.md` に現れ、C0001 を説明 E0 中心に再構成する根拠に使われた。
**発見者**: `lansr-reproducibility-auditor` (CRIT-1, CRIT-2)、supervisor が独立に検証。

---

## 私が主張したこと

以下は撤回対象の主張の原文（verbatim）である。

> "All 960 truth skeletons contain a `neg` node versus 3.2% of candidates. Folding that asymmetry
> leaves the system-level truth-in-beam rate at 0/960 but raises the component-level rate from
> **0/2040 to 107/2040**, so GPU_RUN5's component floor effect was matcher-induced."

より具体的には、次のように述べた。

> "107 of 2040 components (5.25%) are structural matches that the frozen string matcher scored as
> complete misses."

## なぜ誤りなのか

**1. 0/2040 というベースラインは、二つの表現形式を混ぜたことによる人工物だった。**

`phase3/cells/*.json -> true_structure.exponent_aware_skeleton` は **`true_prefix`**（前置記法）から
導出される。一方、候補側の骨格は **infix**（中置記法）の数式文字列から導出される。
検証用 960 セルすべてで確認した結果:

| 保存された真値の骨格を再現した元 | 一致 |
|---|---|
| `true_prefix` | **960 / 960** |
| `true_formula`（infix） | **0 / 960** |

例 (R01)、同一システムの二つの表現:

```
from true_prefix : add,add,CONST,mul,mul,CONST,inv,add,CONST,x_0,x_0,neg,mul,CONST,x_0
from true_formula: add,add,CONST,mul,CONST,x_0,mul,mul,CONST,inv,add,CONST,x_0,x_0
```

prefix 由来の形には `neg` が含まれるが、infix 由来の形には含まれない。私は
**prefix 由来の真値** を **infix 由来の候補** と比較していた。この比較は、モデルにもマッチャーにも
無関係な理由で一致し得ない。私の「生の 0/2040」が測っていたのは、私自身の表現形式の不一致である。

**2. 107/2040 という数値は新しくない — GPU_RUN5 がすでに公表していた値である。**

`results/runs/gpu_run5_20260823_ddd267b0/phase3/beam_groups.json` のフィールド
`component_true_exponent_aware_skeleton_in_beam` は、960 グループ全体で次を保持している:

```
component_true_exponent_aware_skeleton_in_beam : 107/2040 = 0.0525
true_exponent_aware_skeleton_in_beam           :   0/960  = 0.0000
by family: R01 0/120, R02 0/120, R03 0/240, R04 56/240, R05 0/240,
           R06 0/360, R07 17/360, R08 34/360
```

GPU_RUN5 は両方の数値をすでに測定し保存していた。私の `neg` 畳み込みは、偶然にも prefix 形を
infix 形の側へ変換し、その結果 **公表済みの値を再導出** したにすぎない。私は再導出を発見と
取り違えた。

## 何を撤回するか

- **撤回**: 凍結された文字列マッチャーが、実在する 107 件の成分一致を「不一致」と採点していたという主張。
  GPU_RUN5 のマッチャーは infix 同士を正しく比較し、107 件すべてを記録していた。
- **撤回**: GPU_RUN5 の成分レベルの測定が「マッチャーによって正確にゼロへ偏らせられていた」という主張。
  ゼロだったことは一度もない。ゼロは私のものだった。
- **撤回**: 「GPU_RUN5 の `component_exact_loss = 0.0` という床効果はマッチャー由来である」という主張。
  これはさらに二つの別個の量を混同していた。すなわち *ビーム内の成分カバレッジ*（107/2040）と、
  因果介入下での *選択された候補の完全一致による回復*（`component_exact_loss`）である。
  両者は異なる推定対象（estimand）であり、私の推論は両者の間を不当に行き来していた。
  この因果介入下の床効果が本物かどうかは **未解決・未検証** のままである。
- **帰結**: 説明 **E0（評価器・測定の人工物という説明）は、成分レベルの経験的裏づけを失う。**
  これは反証されたわけではない — 正規化を行う CAS マッチャーはまだ誰も走らせていない — が、
  私がその根拠として提示した証拠は存在しない。

## 生き残るもの、影響を受けないもの

- **`neg` の表現上の非対称性そのものは実在する**。これは二つの符号化についての事実である。
  GRN の生成器は減衰項を明示的に `-1 * k * x` と書くが、ODEFormer は符号付き定数を使うしかない。
  なぜなら `sub` と `div` はこのチェックポイントで生成確率が正確にゼロだからである。
  これはモデルの表現経路についての正しく関連する観察であり続ける。
  ただし GPU_RUN5 の測定における欠陥では **ない**。
- **生成確率ゼロの演算子に関する発見は有効なまま**（HRQ-0001）: チェックポイント自身が保持する
  生成器設定のもとで、18 個の演算子のうち 12 個がサンプリング確率ちょうど 0.0 である。
  `env.generator` から直接検証しており、骨格比較には依存しない。
- **符号化可能性に関する発見は有効なまま**（HRQ-0002 の前半）: GRN の真値 320/320
  （Stage 1 では 560/560）がトークナイザを往復できる。保存済みの `teacher_valid` フィールドから検証。
- **Hill-4 の訂正は有効なまま**: 入れ子の `pow,pow,x_i,2,2` が 39/170 成分、24/80 システムに存在する。
  したがって E1'（生成器サポートによる除外）は生きた説明である。構文解析済み構造上で検証。
- **システムレベルの主張は有効なまま**: truth-in-beam は 0/960 であり、GPU_RUN5 の公表どおりである。

## 根本原因と、そこから生まれる常設規則

二つの誤りが重なった。いずれも私のものである:

1. 導出された文字列表現を、同じ導出経路で作られたかを先に確認せずに比較した。先の Hill-4 の誤りも
   まったく同じ形をしていた — 正規化済み文字列の中を表層トークンで検索する、というものである。
2. 自分が「発見」しようとしている量が、元となった run の成果物にすでに保存されていないかを確認しなかった。
   `beam_groups.json` は最初から答えを持っており、私が読んでいたファイルからフィールド一つ隣にあった。

**本キャンペーンの常設規則（即時発効）:**

> 先行 run の再測定を新しい結果として報告する前に、(a) 比較の両側が同じ導出経路から来ていることを
> 検証し、(b) その量そのものを元 run の保存済み成果物に対して grep すること。公表済みの数値の
> 再導出は *ポジティブコントロール* であって発見ではない — その位置づけを明示して実行し、
> そのようにラベル付けすべきである。

この規則は `research_state.md` §8b に追加され、以降すべてのサイクルの実装段階と分析段階で適用される。
