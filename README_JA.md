# Multi-AI Research OS — ai_book v1

このパッケージは、LANSR リポジトリ上の `GPU_RUNmultiAI/` を作業キャンペーン領域として、
複数のAIを継続的な研究ループで協調させるための AI-readable configuration 一式です。

## 基本思想

- **GPT-5.6 Sol**: Leader / Research PI。研究方向、委譲、統合、最終判断を担当。
- **Claude Opus 5**: Critic / Reviewer / Final Auditor。独立反証、統計・方法論監査、最終監査。
- **Claude Sonnet 5**: Research Engineer / Writer。実験設計の具体化、研究コード実装、研究文書。
- **Cursor Composer 2.5**: Repo Operator。大規模なコード編集、テスト、refactor、Git作業の主担当。
- **GPT-5.6 Luna**: Fast Worker。軽量な修正、検索、テスト、機械的処理。
- **Gemini 3.8 Flash**: Scout / Bulk Worker。大量探索、ログ整理、文献候補、artifact索引、反復的な雑用。

モデル名は論理routingの希望値です。実際のCLI/API上のmodel identifierはローカル環境に合わせて設定してください。

## 重要な設計

1. 全AIは、担当worktree内では **full operational access** を前提にします。
2. 安全性はpermission縮小ではなく、**Git worktree・branch・write-scope分離**で確保します。
3. 全AIが同一working treeを同時編集することは禁止します。
4. 研究状態は会話ではなく `GPU_RUNmultiAI/research_state.md` を正とします。
5. AIセッションが自然終了しても、次回起動時に状態を復元できるよう、終了前に必ずcheckpointを書きます。
6. 通常のnull result、コードバグ、worker失敗、reviewer disagreementは研究停止理由ではありません。
7. PR #4 の旧自律研究ブランチからは **研究結果を持ち込みません**。再利用するのはプロセス設計だけです。
8. 既存の `GPU_RUN5/` と同様に、計画・実験記録・report・reproduction informationを
   `GPU_RUNmultiAI/` 内で明示的に管理し、共通コードは通常の `src/`, `scripts/`, `configs/`, `tests/` を利用します。

## 設置

`ai_book/` の中身をリポジトリrootへコピーしてください。ただし以下はmergeしてください。

- 既存 `AGENTS.md` は上書きせず、`ROOT_SNIPPETS/AGENTS_APPEND.md` の内容を末尾付近へ統合。
- 既存 `GPU_RUNmultiAI/` は削除せず、このパッケージ内のテンプレートの不足ファイルのみ追加。
- 既存 `.codex/rules/ai-workers.rules` がある場合、
  `ai-workers-full-access.rules` と矛盾しないように、write invocation の `prompt` を削除/置換。
- `.ai/workers/` のwrapper自体はこのパッケージには含めません。既存PR #5のwrapperを利用します。

## ディレクトリ

- `.agent/`: vendor-neutralな研究OS本体。ここがsingle source of truth。
- `.codex/`: Research PI / delegation用adapter。
- `.claude/`: Claude Opus/Sonnet用adapter。
- `.cursor/`: Cursor用native rules/agents/skills。
- `.gemini/`: 人間が見やすいGemini用mirror/notes。
- `.agents/`: Google Antigravity がworkspace customizationsとして読むnative path。
- `GEMINI.md`: Antigravity/Gemini起動時のroot bootstrap。
- `CLAUDE.md`: Claude Code起動時のroot bootstrap。
- `GPU_RUNmultiAI/`: 自律研究campaignのpersistent stateと成果物。

## full accessについて

この設計でいうfull accessは「repo/worktree内のread/write、shell、Git、test、experiment、networkを
通常作業で人間承認なしに使える」という意味です。共有履歴を破壊するforce push、他workerの未統合作業を
消すreset/clean、資格情報の読出しなどは、能力不足ではなく研究OSの安全規約として禁止しています。

## 継続性

AIに「続けろ」と書くだけでは、CLI turn/sessionの終了を防げません。
本パッケージは **state checkpoint contract** を定義しますが、Codex自体を再起動する外側watchdogは
別途実装が必要です。watchdogは `GPU_RUNmultiAI/research_state.md` の `hard_stop` と `next_action`
だけを見て再起動できる設計を前提にしています。
