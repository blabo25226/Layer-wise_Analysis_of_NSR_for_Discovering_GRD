# C0001 Stage 7 前提条件の検証記録

Stage 6 smoke は `PROCEED_TO_FULL_RUN` を条件 3 件付きで返した。実験エージェントは本実験を起動したが
これら 3 件の結果を報告しなかったため、supervisor が直接検証する。

## 前提条件 1 — `prior_information_disclosed` の v2.1 参照

**充足（supervisor が修正済み）。** `scripts/phases/gpu_runclaude1_c0001_phase1_parta.py` は
`C0001_preregistration_v2.1.md §0.1-§0.4` を書き出す。v2.1 §0.5 の要求どおり。
コミット `4e91b5f`。

## 前提条件 2 — 全スコープ hard-abort がセル採点前に Phase 1 を停止させるか

**充足（静的検証）。** `gpu_runclaude1_c0001_phase1_parta.py` の該当箇所:

- 165-171 行: `hard_abort_reasons` を PC0（マッチャ破損）、PC2a（ハーネス差異）、
  PC4（増分指標が実証されていない）の 3 ゲートから構築する
- **172 行: `if hard_abort_reasons and not args.smoke:`** で中止
- 177 行: `go_conditions={"hard_abort": True, "reasons": hard_abort_reasons}` を書き出す
- 182 行: `Phase 1 undecidable (hard abort before endpoint pass)` を出力
- **185 行: `cells_for_matching_paths` の算出は中止判定より後**

したがって中止はセルを 1 つも採点する前に起こる。v2.1 §7.10 項目 4 / §7.7.3 の要求どおり。

**smoke で観測された異常の説明**: smoke では `args.smoke` が真であるため 172 行の中止が発火せず、
`gates_ok: false` とエンドポイント判定が同時に出力される。8 系統部分集合では PC4 の凍結閾値
（`gain_total >= 40`）を満たせないため、これは設計どおりの挙動であり本番実行では起こらない。
160-164 行のコメントがこの意図を明記している。

**限界**: これはコード配置の静的確認である。強制失敗による実行時テストのほうが強い証拠になるが、
本実行では PC0/PC2a/PC4 が通れば中止経路は通らない。重要なのは配置であり、それは確認できた。

## 前提条件 3 — PC0-CAS のプロセス内 monkeypatch（実装ノート §2.5）

**未検証。** Phase 1 の 6 ワーカー実行と CPU を競合させ、計測時間を歪めるため、本実行の完了後に
検証する。PC0-CAS の報告値は、この検証が済むまで信頼してはならない。
Stage 8 の解析に入る前に discharge すること。

## 併せて確認した Gate 0 実測値（`phase0/` 成果物より）

| 項目 | 値 |
|---|---|
| checkpoint SHA256 | `56754040be5aa92ed4767fc43ee2008faa293f87c12b643e66c7df3e1623a5e8`、`sha256_matches_frozen = True` |
| `sealed_paths_read_count` | **0** |
| `known_sealed_files_count` | **7**（ディスクから列挙、ハードコードなし） |
| `allowlist_has_no_sealed_path` | True |
| M3 一致ゲート | `n_pairs_realized = 1178`、`n_disagreements = 0`、`reduced_scope_smoke = False` |
| validation セル数 | 960（`validation_cell_count_ok = True`） |

run id: `gpu_runclaude1_c0001_b731cdd`
