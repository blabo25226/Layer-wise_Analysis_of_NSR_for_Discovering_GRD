# 文書の言語

指示日: 2026-09-09。人間が読む研究成果物は日本語、機械・エージェントが消費する契約とコード関連は英語のまま。

## 日本語で書くもの（人間向け成果物）

- `GPU_RUNclaude1/research_state.md`
- `GPU_RUNclaude1/human_review_queue.md`
- `GPU_RUNclaude1/syntheses/*.md`
- `GPU_RUNclaude1/reports/*.md`（cycle report は結果が負・null・無効でも必須。すべて日本語）
- Pull Request の本文・コメント・レビュー返信
- 上記以外でも、**研究結果をまとめ、人間が読むべき文章**は日本語。判断に迷う場合の基準は
  「人間が読んで研究上の判断に使うか」。使うなら日本語。
  - 該当例: 撤回・訂正の記録、サイクルの結論、ボトルネック診断、生物学的解釈
  - `GPU_RUNclaude1/analyses/` 配下は、サイクルの科学的結論を述べるものは日本語

## 英語のままにするもの

- **git commit message**（`.claude/rules/13-commit-message.md` に従い簡潔な英語）
- コード、docstring、コメント、識別子、ログ、テスト名
- `GPU_RUNclaude1/plans/*_preregistration*.md` および `.json` — 凍結契約であり、subagent が
  フィールド名・エンドポイント名で参照する。翻訳は参照を壊すため英語のまま
- `GPU_RUNclaude1/reviews/*.md`、`literature/*.md`、`hypotheses/*.md` — エージェント間の技術文書
- `manifests/*.json`、`*.sha256`
- `.claude/rules/` のうち既存の英語ファイル（本ファイル以降の新規は日本語でよい）

迷ったら現状維持。無用な翻訳で参照を壊さない。

## 翻訳・執筆時の絶対条件

日本語化で研究内容が劣化してはならない。

- **数値、統計量、信頼区間、p値、SHA256、コミットハッシュ、run ID、ファイルパス、
  フィールド名、エンドポイント名、演算子名、識別子は一字一句そのまま**。訳さない、丸めない、
  桁を変えない
- 表は表のまま保持する。行を削らない
- 撤回・訂正は削除せず、撤回であることが分かる形で残す
- `SOURCE`（出典に支持された事実）と `INFERENCE`（推論）の区別を保つ
- 専門語は初出で説明する（AGENTS.md §6.4）。略語だけで進めない
- 数式は TeX を使い、GitHub 表示規則（AGENTS.md §6.6）に従う。README 同様
  `operatorname` 系コマンドは使わない
- 「数値的当てはまりは記号回復ではない」「記号回復は生物学的因果ではない」「非有意は同等ではない」
  といった区別を、訳文でも曖昧にしない

## 検証

人間向け文書を日本語化・更新したら、数値とパスが原文と一致していることを確認する。
特にレポートと synthesis は、保存済み JSON/CSV から数値を照合する（AGENTS.md §6.2）。
