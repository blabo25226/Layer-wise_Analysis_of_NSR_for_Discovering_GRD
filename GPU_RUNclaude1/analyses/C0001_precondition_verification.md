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

---

## 追加所見（2026-09-09、Phase 1 実行中に発見）— Gate B->C がコードで強制されていなかった

**重大度: MAJOR。修正済み。**

v2.1 は Gate B->C として次の 2 条件を規定する。

1. Part A が matcher-attributable gain を確認した場合、Part C は**実行しない**（replication を優先）
2. Part C は in-support システムが **30 以上**であることを要する（凍結された検出力の下限）

`scripts/phases/gpu_runclaude1_c0001_phase3_partc.py` を静的に確認したところ、`gain_confirmed`、
`partA_endpoints`、`n_in_support` のいずれへの参照も存在せず、dry-run 判定の直後に torch と
モデルの読み込みへ進んでいた。**事前登録されたゲートが運用者の規律に依存する状態**だった。

Phase 3 は未起動であったため、実行前に機械的な強制へ変更した。

- `gate_b_to_c(run_root)` を追加。`phase1/partA_endpoints.json` の `primary.verdict` と
  `phase2/partB_in_support_systems.json` の `n_in_support` を読み、拒否理由を列挙して返す
- GPU 作業の前に評価し、不合格なら `phase3/gate_b_to_c.json` と `status: skipped` の manifest を
  書き出して `return 0`
- **上流成果物の欠落は「合格」ではなく「拒否」**として扱う。書かれていないゲートが満たされていた
  という仮定の上で Part C を走らせてはならない
- `--smoke` では強制しない。Part C のコード経路自体を Parts A/B の存在前に検証するためで、
  Phase 1 の hard abort と同じ規約である

判定語彙は `src/gpu_runclaude1/ladder.py:45 ladder_verdict` より:
`k == 0` → `no_gain_observed_bound_only`、`k <= C` → `weak_gain`、
`k > C` → `matcher_attributable_gain_confirmed`。ゲートが拒否するのは 3 番目のみで、`weak_gain` は
主張の修正であって方向転換ではないため Part C を実行する。

`GPU_RUNclaude1/tests/test_gate_b_to_c.py` に 9 件のテストを追加（全通過）。境界値
（`n_in_support` がちょうど 30 で合格、29 で拒否）、両上流成果物の欠落、`n_in_support` が
整数でない場合を含む。

---

## インシデント記録（2026-09-09 16:46 頃）— supervisor が実行中の Phase 1 を停止させた

**私の操作ミスである。** 実験を破壊し、さらにそれを「生存している」と誤って報告した。

### 何が起きたか

1. 実験エージェントが「次の通知を待つ」だけを繰り返し、累計 160k トークンを消費して何も進めて
   いなかったため、`TaskStop` で停止した。
2. Phase 1 の Python プロセスはそのエージェントの Bash 呼び出しから起動されていたため、
   **エージェントのプロセスグループごと落ちた**。`cell_cache` の書き込みは **16:46 で停止**、
   ログに `EXIT_CODE` は記録されていない（正常終了なら記録される）。
3. 私は直後に生存確認を行い「YES」と判断して「Phase 1 のプロセスは無事に生存しています」と報告した。
   **これは偽陽性だった。**

### なぜ検出できなかったか — 二重の自己マッチ

生存確認に使った `pgrep -f "gpu_runclaude1_c0001_phase1_parta.py"` は、**その文字列を
コマンドラインに含む自分自身の監視プロセスにマッチする**。私が張った Monitor のコマンド文字列にも
同じ grep パターンが含まれていたため、Monitor の「プロセス消失」検出も永久に発火しない状態だった。

さらに Monitor は「値が変化したときのみ通知する」設計だったため、ストールでも死亡でも**沈黙する**。
Monitor のツール説明が警告していた「沈黙は成功ではない」という失敗形そのものを、自分で作り込んだ。

結果として 16:47 から 17:38 までの 51 分間、進捗ゼロ・load average 0.50（6 ワーカーなら約 6.0）・
GPU 温度 51→44 °C という明白な死亡兆候を、私は「順調」と報告し続けた。

### 被害と復旧

- **科学的な被害はない。** 143/960 セルが完了・キャッシュ済みで、Part A は resume 可能に設計されて
  おり、その resume 動作（バイト単位一致・重複計上なし）は Stage 4 で検証済みである。
  破棄された計算は約 7 分ぶんのみ。
- 対照バッチ（PC0/PC2a/PC4 の hard-abort ゲート）は完了しており、その結果は保持されている。
- 141 セルではなく 143 セルから resume して再開した。harness 管理下のバックグラウンド実行に
  切り替えたため、孤児プロセスにならず完了通知が確実に届く。

### 教訓 — 規則 R6 として採用する

`.claude/rules/` と `research_state.md` §8b に追加すること:

1. **長時間実行を subagent の Bash 呼び出しから起動しない。** そのエージェントを停止すると実行も
   死ぬ。harness 管理下のバックグラウンド実行（`run_in_background`）を使えば、孤児にならず完了
   通知も届く。
2. **`pgrep -f <pattern>` を生存確認に使うとき、パターンが監視側自身のコマンドラインに現れないよう
   にする。** 自己マッチは恒久的な偽陽性になる。`pgrep -f` の代わりに PID を直接保持して
   `kill -0 <pid>`、または `pgrep` の結果から自分自身の PID を除外する。
3. **進捗監視は「変化したとき」ではなく「変化しないとき」も通知できなければならない。**
   ストールと正常実行を沈黙で区別できない設計は監視ではない。無変化が N 回続いたら警告を出す。
4. **プロセスを停止する前に、それが何を子に持つかを確認する。** `TaskStop` はプロセスグループを
   落とす。
