# 人間レビュー待ちキュー

自律ループは、ハードストップが発動しない限りこのキューを待たない。

## 優先度: 高

### HRQ-0001 — 公開 ODEFormer チェックポイントは 18 個の演算子のうち 12 個に生成確率ちょうどゼロを割り当てている
- 起票: 2026-09-09、C0001 Stage 1（supervisor が検証）
- 証拠: `GPU_RUNclaude1/analyses/C0001_stage1_preobservation.md`（addendum）
- `assets/odeformer/weights/odeformer.pt` の内部に保存された生成器設定（`env.params`）は
  `operators_to_use = 'sin:1,inv:1,pow2:1,id:3,add:3,mul:1'` である。実現されるサンプリング確率は
  `abs, sqrt, log, exp, arcsin, cos, arccos, tan, arctan, pow3, sub, div` について正確に **0.0** であり、
  一方でこれらのトークンは 10,293 語のデコーダ語彙には *存在する*。
- `reload_data = '/data/rcp/odeformer/experiments/datagen_final/datagen_use_sympy_True'` は、これが
  ローカルのパーサ既定値ではなく著者自身の事前学習用データ生成設定であることを示す。同じオブジェクトは
  `n_enc_layers/n_dec_layers = 4/12` を報告しており、GPU_RUN4 のアーキテクチャに関する発見を独立に裏づける。
- 本キャンペーンを越えて重要になり得る理由: このチェックポイントについては「モデルが X を表現できる」を
  語彙に含まれることから推論できない、ということを意味する。また `div`/`sub`/`exp`/`log` — いずれも
  生化学的ダイナミクスで一般的な演算子 — がデータ生成中に一度もサンプルされていない。これは広く使われて
  いる公開チェックポイントの具体的で検証可能な性質であり、すでに文書化済みの 4+12 対 4+16 の
  アーキテクチャ不一致に隣接しつつも別個の事実である。
- 状態: 外部への主張を行う前に、C0001 Stage 2 で一次情報源（論文 / 公式リポジトリ / 学習ログ）による
  確認を待っている。ループは停止していない。

### HRQ-0002 — 合成 GRN の真値 560 件はすべて表現可能だが、truth-in-beam は 0/960 である
- 起票: 2026-09-09、C0001 Stage 1
- 証拠: `GPU_RUNclaude1/analyses/C0001_stage1_preobservation.md`
- 学習+検証の 320 システムについて supervisor が `teacher_valid: True` を検証済み。Stage 1 でこれを
  sealed（封印）および family-holdout の分割を含む 560/560 まで拡張し、完全な往復（round-trip）を確認した。
  GRN の真値はサポート内の演算子のみを使う。それにもかかわらず GPU_RUN5 は 960 セル / 47,987 候補にわたって
  `true_exponent_aware_skeleton_in_beam_rate = 0.0` を測定した。
- これは明快な解離である。表現可能性も演算子サポートも、システムレベルでの GRN 生成失敗を説明しない。
- **訂正 2026-09-09**: 本エントリの以前の版では、成分レベルの比率もマッチャーによってゼロへ偏らせられて
  いたと主張していた。**その主張は撤回された** — `GPU_RUNclaude1/analyses/C0001_RETRACTION_neg_finding.md`
  を参照。GPU_RUN5 は成分レベルの比率を 107/2040 = 0.0525 としてすでに測定し `phase3/beam_groups.json` に
  保存していた。supervisor の「0/2040」というベースラインは、prefix 由来の真値を infix 由来の候補と
  比較したことによる人工物だった。本エントリの表現可能性の側（560/560 が符号化可能）はこの影響を受けず、
  そのまま有効である。
- 状態: 情報提供。生き残ったシステムレベルの解離が C0001 の動機となっている。ループは停止していない。

## 優先度: 通常

### HRQ-0003 — `pytest.ini` がテストファイアウォールのスイートを含む 124 件のテストを黙って飛ばしている
- 起票: 2026-09-09、C0001 Stage 0
- `testpaths = tests GPU_RUN1/tests GPU_RUN2/tests GPU_RUN3/tests GPU_RUN4/tests` は 178 件のテストを収集する。
  `GPU_RUN5/tests` はそれ自体でさらに **124** 件を収集し、その中には封印テストのファイアウォールを
  カバーする `test_gpu_run5_firewall.py` が含まれる。したがって素の `pytest` 実行は、最も新しく、
  最もリーク感度の高いカバレッジを飛ばしている。一行で直る。C0001 内で修正を提案した。

### HRQ-0004 — `assets/nd2/weights/checkpoint.pth` に SHA256 の記録がない
- 起票: 2026-09-09、C0001 Stage 0。ODEFormer と NeSymReS のチェックポイントはどちらもハッシュが
  固定記録されているが、ND2 にはない。

### HRQ-0005 — 古くなった文書リンクと、状態が固まったままの manifest
- 起票: 2026-09-09、C0001 Stage 0
- `GPU_RUN5/README.md` と `GPU_RUN5_summary_report.md` §9.1 が、存在しない六個のレポートファイル名へ
  リンクしている。
- `results/runs/gpu_run4_phase0_01/manifest.json` の status が `running` のまま固まっている。commit `0641fa7`。
- どちらも人間主導トラックの成果物である。ルール 00 により自律トラックは GPU_RUN1-5 の履歴を書き換えては
  ならないため、編集せず報告する。

### HRQ-0006 — supervisor による撤回: `neg` 正規化の発見は分析の人工物だった
- 起票: 2026-09-09、C0001 Stage 3。再現性監査者が発見し、supervisor が検証した。
- 証拠: `GPU_RUNclaude1/analyses/C0001_RETRACTION_neg_finding.md`
- 撤回された主張がコミットメッセージ (`bfbf727`) に到達し、一時的にサイクルの設計を組み替えたため、
  可視性のためここに記録する。supervisor の誤りが二つ重なっていた。文字列表現同士が同じ導出経路から
  来ているかを確認せずに比較したこと、そして「発見」しようとしている量を元 run 自身の成果物に対して
  grep しなかったことである。
- 結果として `research_state.md` §8b に常設のキャンペーン規則を追加した。
- 状態: 自己申告であり、実験が走る前に訂正済み。この件で公表した結果はない。ループは停止していない。

## レビュー済み
なし。

## HRQ-0007: 事前登録 gate の違反下で Part C が実行された（C0001、非ブロッキング）

**2026-09-09。** Part A の記録すべき verdict は `undecidable` であり、v2.1 Gate B→C 項目 (i) は
その場合 Part C を実行してはならないと定めていた。supervisor が実装した `gate_b_to_c()` が
その条件を落としていたため、Part C が完走した。

- 消費 GPU 約 1 分、ピーク VRAM 0.454 GiB、封印テストへの接触なし
- **Part C から導出した科学的主張はゼロ**。決定エンドポイント C2-P はそもそも未計算
- 無効化される結論はない。既存成果物は `INADMISSIBLE.md` を添えて保存
- 契約は変更しない。Part C は C0001 では再実行しない

人間側に確認いただきたい点: 本件を DEVIATION として報告し C0001 を継続する判断が妥当か。
supervisor の判断ではハードストップ条件（`RESEARCH_LOOP.md` §6）に該当しない。
詳細: `analyses/C0001_DEVIATION_gate_b_to_c_violation.md`

## HRQ-0008: 組織設定により Claude Code のサブスクリプション利用が無効化されている（管理者操作が必要）

**2026-09-10。非ブロッキングだが、再発すれば規則 09 のハードストップに該当する。**

`lansr-independent-reviewer` の第一次試行が HTTP 403 `oauth_org_not_allowed` で異常終了した
（request id `req_011CeshpLHg1Yo8WEb1Krvdn`、送信モデル `claude-opus-5`）:

> Your organization has disabled Claude subscription access for Claude Code ·
> Use an Anthropic API key instead, or ask your admin to enable access

**測定した状態**（詳細は `research_state.md` §5b）:

| 項目 | 値 |
|---|---|
| 組織 | Nakamura Lab（`claude_team`） |
| シート | `team_labs_standard` |
| 本ユーザーの権限 | `organizationRole: user`、`workspaceRole: None` |
| `ANTHROPIC_API_KEY` | 未設定 |

**重要な限定**: この 403 は再現していない。再投入した同一種別の subagent は 18 分以上稼働した。
「subagent が使えない状態」ではない。Remote Control は未接続、`SendUserFile` はセッション途中で
利用不可になったが、これらが同一原因かは `unverified`。

### 人間側にお願いしたいこと

1. **Nakamura Lab の管理者に、Claude 管理コンソールで Claude Code のサブスクリプション利用を
   有効化するよう依頼する。** `organizationRole: user` のため利用者自身では変更できない。
2. あるいは `ANTHROPIC_API_KEY` を使うか。ただし課金が組織サブスクリプションから API 従量課金に
   変わる。**本日 1 日の subagent 消費は約 68 万トークン**。費用判断は人間の決定事項とし、
   supervisor は独断で設定しない。

### supervisor が守る約束

403 が再発して subagent を投入できなくなった場合、**実験者・解析者・独立 reviewer の分離要件が
満たせなくなるため、ループを停止して確認を求める。**
supervisor が単独で査読を兼ねて「独立査読を実施した」と記載することは決してしない。
