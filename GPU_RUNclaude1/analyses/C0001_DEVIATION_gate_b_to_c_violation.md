# 逸脱記録: Gate B→C 違反下での Part C 実行（C0001）

**分類**: DEVIATION（事前登録された gate の違反）。ハードストップ条件には該当しない
（`RESEARCH_LOOP.md` §6 のいずれにも当たらない）。
**発見**: 2026-09-09、Stage 8 の独立解析（`lansr-results-analyst`）による。
**責任**: supervisor の実装ミス。実装エージェントや解析者の過失ではない。
**run id**: `gpu_runclaude1_c0001_b731cdd`

## 何が起きたか

`GPU_RUNclaude1/plans/C0001_preregistration_v2.1.md:1767` の Gate B→C は原文でこう定める:

> **Gate B → C.** Proceed to Part C only if **both**:
> (i) Part A is **not** `undecidable`. If Part A lands on `matcher_attributable_gain_confirmed`,
> **Part C is not run in C0001**: ...
> (ii) `n_in_support ≥ 30` validation systems are fully in support **and** have Part A component
> gains = 0 ...

supervisor が `scripts/phases/gpu_runclaude1_c0001_phase3_partc.py` に実装した `gate_b_to_c()` は、
項目 (i) のうち **第二文（`matcher_attributable_gain_confirmed` の場合）だけを実装し、
第一文（`undecidable` でないこと）を丸ごと落としていた**。項目 (ii) も後半
（「Part A component gains = 0 であること」）を実装していない。

Part A の記録すべき verdict は `undecidable`（v2.1 §7.5 item 3、二方向感度分析が異なる rung に
落ちたため）。したがって **Part C は C0001 では実行してはならなかった**。
実際には `phase3/gate_b_to_c.json` が `ok: true` を書き、Part C は完走した。

### 二重の失敗であること

gate が見逃した理由は二つ重なっている。どちらか一方だけでも Part C は止まらなかった。

1. `gate_b_to_c()` に `undecidable` の条件が存在しない。
2. gate が参照する `partA_endpoints.json:primary.verdict` **それ自体が欠陥**である。
   `endpoints.py:compute_primary_endpoint` は `sensitivity_agrees` を計算した後、
   `verdict` には非敵対方向の ladder rung を代入し、`undecidable` へ分岐しない。
   よって成果物は `no_gain_observed_bound_only` を提示する。

つまり項目 (i) を正しく実装していたとしても、参照先のフィールドが誤っているため
**やはり通過していた**。gate は verdict of record を導出しなければならない。

## 被害の範囲

| 項目 | 実際 |
|---|---|
| 消費した GPU 時間 | 約 1 分（上限 4.0 h に対して無視できる） |
| ピーク VRAM | 0.454 GiB（上限 5.5 GiB 内） |
| 封印テストへの接触 | **なし**（`sealed_paths_read: []`） |
| Part C から導出した科学的主張 | **なし** |
| 無効化される結論 | **なし** |

**Part C の決定エンドポイント C2-P はそもそも計算されていない。**
phase3 スクリプトは真の式の教師強制対数確率 `gt_logprob_sum` と計器監査しか出力せず、
`lp_sel`（選択候補）・`lp_best`（最良候補）を採点していないため、
`stahlberg_byrne_indicator` は一度も呼ばれていない（supervisor が独立に発見）。
したがって違反実行が生んだのは**帰属を一切伴わないデータ**であり、
撤回すべき主張は存在しない。

## 対応

1. `gate_b_to_c()` を項目 (i)(ii) の全文に合わせて修正する。verdict は成果物のフィールドを
   信用せず導出する（`sensitivity_agrees == false` を `undecidable` として扱う）。
2. `endpoints.py` を修正し、`sensitivity_agrees == false` のとき `verdict` を
   `undecidable (two-sided sensitivity disagreement)` として書き、両方向の rung を永続化する。
3. **Part C は C0001 では再実行しない。** 約 50 分の GPU を要する discriminator の本実行を
   停止させた。§8.3 の配線はコードとテストとしては着地させる（将来のサイクルのため）。
4. `phase3/` の既存成果物は**破棄しない**。gate 違反下で生成された記録として保存し、
   帰属には使用不可（inadmissible）として扱う。
5. **凍結契約は一切変更しない。** gate を後から緩めて実行を正当化することはしない。

## 教訓（常設規則の候補）

**事前登録された gate を実装するときは、要約ではなく契約の原文を引用して実装し、
条文と実装を 1 対 1 で対応付けて残すこと。** 本件で supervisor は Gate B→C を
自身の要約メモ（「Part A が gain_confirmed なら Part C を実行しない」）から実装し、
原文の第一文を読まなかった。要約は条件を落とす。

**gate が参照する値が、別の欠陥の影響下にないことを確認すること。** 派生フィールドを
gate の入力にする場合、そのフィールドを生成するコードが契約どおりかを併せて検証する。
