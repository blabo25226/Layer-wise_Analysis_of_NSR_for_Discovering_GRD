# C0001 主エンドポイントの再現性の失敗（タイムアウト数の負荷依存）

**分類**: 事前登録エンドポイントの再現性の失敗。保存済み結果は撤回しない（規則 01 item 4）。
**発見の経緯**: Stage 9 独立査読の第一次試行が、インフラ障害で落ちる直前に
「3,444 件の保存値はすべて再現したが、タイムアウトは 9 件ではなく 2 件だった」と報告。
supervisor が独立に測定して確認した。第二次の独立査読でも独立に測定させている。
**run id**: `gpu_runclaude1_c0001_b731cdd`

## 何が再現しないか

C0001 の verdict は、9 件の `SymbolicEquivalenceTimeout` 成分トリプルだけに依存している。
この 9 件が `could_not_evaluate_rate > 0` を成立させ、それが v2.1 §7.5 item 3 の
二方向感度分析を**必須**にし、二方向が異なる rung に落ちるため verdict が `undecidable` になる。

同じ 9 トリプルをアイドル状態のマシンで直列に再採点した結果（5 反復、`SYMPY_OP_TIMEOUT_SEC = 10.0`
は**変更していない**）:

| 三つ組（cell_id / candidate_index / component_index） | タイムアウト頻度 | 再採点時の判定 |
|---|---|---|
| `R03_validation_d101_005_b2_n0p05_r0` / 14 / 0 | 0/5 | `proved_different` |
| `R05_validation_d101_000_b2_n0p05_r0p5` / 9 / 1 | 0/5 | `proved_different` |
| `R07_validation_d101_000_b1_n0_r0` / 47 / 1 | 0/5 | `proved_different` |
| `R07_validation_d101_002_b2_n0_r0p5` / 16 / 2 | **1/5** | 不安定 |
| `R07_validation_d101_003_b0_n0_r0p5` / 35 / 1 | 0/5 | `proved_different` |
| `R07_validation_d101_003_b2_n0_r0p5` / 19 / 1 | 0/5 | `proved_different` |
| `R07_validation_d101_009_b0_n0_r0` / 6 / 2 | 0/5 | `proved_different` |
| `R07_validation_d101_009_b1_n0_r0` / 12 / 2 | **2/5** | 不安定 |
| `R07_validation_d101_009_b1_n0p05_r0` / 29 / 2 | 0/5 | `proved_different` |

反復あたりのタイムアウト数: **[1, 0, 1, 0, 1]**。保存された run の記録値は **9**。
**9 件のうち 7 件は再採点で一度もタイムアウトしない。**

## verdict が反復ごとに変わる

タイムアウトした成分数 `k_adv` に応じて verdict は次のように動く（`n_h = 130`、cutpoint 3）:

| タイムアウト成分数 | 非敵対方向 | 敵対方向 | 一致 | verdict |
|---|---|---|---|---|
| 0 | `no_gain_observed_bound_only` | 感度分析が**必須でない** | — | `no_gain_observed_bound_only` |
| 1–3 | `no_gain_observed_bound_only` | `weak_gain` | 否 | **`undecidable`** |
| 4 以上 | `no_gain_observed_bound_only` | `matcher_attributable_gain_confirmed` | 否 | **`undecidable`** |

上記 5 反復では 3 回が `undecidable`、2 回が `no_gain_observed_bound_only` に落ちた。
**どの反復も `matcher_attributable_gain_confirmed` には届かなかった**（4 成分以上を要するため）。
保存された run は 6 成分が反転して最上位 rung に達していた。

## 機構 — 凍結設計が自らの計器を不安定にしている

原因は CPU 競合である。Part A 本実行は v2.1 が定める**プロセス並列 6 ワーカー**で走っており、
比較あたりの実時間が膨らんで 10.0 秒の `SIGALRM` ガードが 9 回発火した。
アイドルマシンで直列に採点すると 0〜1 回に落ちる。負荷を操作変数とする因果検証を別途実施している。

一般化すると、これは**方法論上の知見**である:

> **並列ワーカープール内の実時間タイムアウトは、タイムアウト回数に依存するあらゆる
> エンドポイントを再現不能にする。**

v2.1 は (a) プロセス並列 6 ワーカーを要求し、(b) 実時間 `SIGALRM` ガードを凍結し、
(c) `could_not_evaluate_rate > 0` を感度分析の起動条件にし、
(d) ladder cutpoint を 3 という小さな値に置いた。この 4 つが組み合わさると、
**マシンの負荷が verdict を決める**。どれか 1 つでも違えば起きない。

さらに §7.5 item 2 の「(0, 2.0%] なら感度分析付きで報告」分岐は、成分あたり 600 トリプルの
ANY レバーがあるため実際上到達不能である（統計レビュアー MAJOR-3）。
2.0% では 130 成分すべてが反転する。

## 何をするか / しないか

**しないこと。**
- タイムアウトを引き上げない。v2.1 named contingency 1 が mid-cycle の変更を明示的に禁じており、
  仮に禁じられていなくても、それは結果を救済する目的の threshold 変更（規則 01 item 3）になる。
- 保存された run of record を書き換えない。9 件のタイムアウトは実際に観測された。
- 「7/9 は実質 `proved_different` だから K = 0 で E0 は棄却できる」と主張しない。
  再採点は**凍結された計器の外**にある。この観察は探索的（exploratory）であり、
  エンドポイントを差し替える根拠にはならない。

**すること。**
- **C0001 の verdict of record は `undecidable` のまま**とする。それが run of record である。
- **併記の開示として、このエンドポイントは再現しないことを報告する。**
  再採点では反復により `undecidable` と `no_gain_observed_bound_only` の間で揺れる。
  これは負の結果ではなく、**計器についての一次的な知見**である。
- 次サイクル（C0002）の事前登録で、`could_not_evaluate` を実時間ではなく**決定論的な予算**
  （ノード数・演算回数など負荷に依存しない量）で定義し直すことを主要な設計変更として提案する。
  これは C0001 の結果を救済するものではなく、**計器を再現可能にする**ための変更である。

## 効力範囲の限定

この所見は `could_not_evaluate` の計上に関するものであり、以下には及ばない。
- M0 の厳密再現（47,987 候補・101,963 成分比較・2,235 一致）は決定論的で、独立に再現済み
- M0 と M3 の集合恒等性（あらゆる解像度で対称差 0）— タイムアウトした 9 件は
  いずれも `m0_any = 0` であり、恒等性の証拠には入っていない
- Part B の out-of-support 9/170 — CAS のタイムアウトを使わない解析的センサス
- 対照電池 PC0 / PC4 など（PC4 gain 100/170 は決定論的な書き換えによる）
