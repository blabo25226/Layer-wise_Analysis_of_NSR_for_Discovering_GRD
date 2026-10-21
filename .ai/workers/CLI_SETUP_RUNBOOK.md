# 4 CLI 運用手順書（Codex / Claude Code / Cursor Agent / Antigravity）

対象: 人間オペレーターとエージェント AI。Codex がオーケストレータとなり、`.ai/workers/*.sh` 経由で
他 3 CLI を呼ぶ（詳細は [README.md](README.md) と [../../FULL_ACCESS_SETUP.md](../../FULL_ACCESS_SETUP.md)）。

確認日: 2026-10-21（この環境 Linux x86_64 で実測）。

| CLI | コマンド | 確認バージョン | 認証方式 | 状態確認コマンド |
|---|---|---|---|---|
| Codex | `codex` | 0.163.0 | ChatGPT アカウント（ブラウザ） | `codex login status` |
| Claude Code | `claude` | 2.1.280 | claude.ai アカウント（チームシート） | `claude auth status` |
| Cursor Agent | `agent` / `cursor-agent` | 2026.09.23 | Cursor アカウント（ブラウザ） | `agent status` |
| Antigravity (Gemini) | `agy` | 1.3.2 | Google AI Pro アカウント | 下記「agy」参照 |

## 0. 共通原則

- 認証は各公式 CLI が所有する。パスワード・トークン・API キーをリポジトリ、ログ、プロンプトに書かない。
  `~/.codex/auth.json` 等の中身を `cat` しない。
- **ログイン（ブラウザ操作）は人間だけが行う。** エージェントはログイン切れを検知したら
  `.agent/rules/13-retry-fallback-and-hard-stops.md` と `.agent/rules/14-human-intervention-and-review-queue.md`
  に従い、`GPU_RUNmultiAI/human_review_queue.md` に記録して人間に引き継ぐ（キャンペーンは止めず、他タスクへ進む）。
- API キーで回避しない（チームシート運用のため。`claude` は `ANTHROPIC_API_KEY` を設定しない）。
- ラッパーは既定が読み取り専用。`--write` は隔離 worktree/ブランチと書き込み範囲を宣言したタスクのみ。

## 1. 初回セットアップ（初めてのログインを含む）— 人間が実施

### 1-1. Codex CLI のインストール

公式インストーラ（`~/.local/bin/codex` と `~/.codex/` に配置。sudo 不要・Node 不要）:

```bash
curl -fsSL https://chatgpt.com/codex/install.sh -o /tmp/codex_install.sh
less /tmp/codex_install.sh                      # 内容を確認
CODEX_NON_INTERACTIVE=true sh /tmp/codex_install.sh
codex --version                                 # codex-cli 0.163.0 など
```

代替: `npm install -g @openai/codex`（Node が必要。この環境は conda 環境 `ai-workers-node` にのみ Node がある）。
更新は同じインストーラを再実行する。

### 1-2. 各 CLI の初回ログイン

ブラウザが開ける端末（デスクトップ、または SSH なら手元 PC でポート転送/URL 手動オープン）で実施。

```bash
# Codex: 初回は対話 UI を起動して "Sign in with ChatGPT" を選ぶ
codex
codex login status                  # "Logged in using ChatGPT" を確認

# Claude Code
claude auth login                   # claude.ai アカウントを選ぶ（Console/API ではない）
claude auth status                  # loggedIn: true, authMethod: claude.ai

# Cursor Agent（ブラウザが開けない場合は NO_OPEN_BROWSER=1 を付け、表示 URL を手動で開く）
agent login
agent status

# Antigravity CLI（未導入なら先にインストール）
curl -fsSL https://antigravity.google/cli/install.sh | bash
agy                                 # 初回起動時の Google ログイン案内に従う（Google AI Pro アカウント）
agy models                          # 利用可能モデルが出ればログイン成功
```

注意:

- Cursor 未導入なら `curl https://cursor.com/install -fsS | bash`。
- Gemini 単体 CLI（`gemini`）は Google AI Pro のログインが非対応のため使わない（診断用のみ）。
- `agy` のログイン手順と専用の status サブコマンドは、この環境では未検証（`agy --help` に auth 系サブコマンドなし）。
  初回ログイン時に実際の画面を確認し、本書を更新すること。

### 1-3. Codex にワーカーを許可する（初回のみ）

1. リポジトリルートで Codex を起動し、プロジェクトを **trusted** にする（`~/.codex/config.toml` の
   `[projects."<repo path>"] trust_level = "trusted"`。本リポジトリは設定済み）。
2. [`.codex/rules/ai-workers.rules`](../../.codex/rules/ai-workers.rules) を追加・変更した後は **Codex を再起動**する。
3. 動作確認（読み取り専用、ファイルは変更されない）:

```bash
.ai/workers/claude.sh "Reply with exactly: CLAUDE_OK"
.ai/workers/cursor.sh "Reply with exactly: CURSOR_OK"
.ai/workers/gemini.sh "Reply with exactly: GEMINI_OK"
```

3 つとも応答が返れば完了。1 つでも認証エラーなら 1-2 の該当 CLI をやり直す。

## 2. 2 回目以降（ログイン済みの日常運用）

### 2-1. 人間: セッション開始時チェック（約 1 分）

```bash
codex login status && claude auth status && agent status && agy models | head -3
```

- すべて成功 → そのまま作業開始。ログインは不要（トークンは各 CLI が自動更新する）。
- 失敗した CLI のみ 1-2 の該当コマンドで再ログイン。

人間が直接使う:

```bash
cd /home/blabo/Layer-wise_Analysis_of_NSR_for_Discovering_GRD
codex                       # 対話（Codex が .ai/workers/*.sh で他 CLI を委譲）
codex exec "<task>"         # 非対話
claude                      # 対話 / claude -p "<prompt>" で非対話
agent                       # 対話 / agent -p "<prompt>" で非対話
agy                         # 対話 / agy -p "<prompt>" で非対話（--mode plan で読み取り専用）
```

### 2-2. エージェント AI: ワーカー呼び出し（ログイン操作はしない）

常にリポジトリルートから、ラッパー経由で呼ぶ。直接 `claude`/`agent`/`agy` を `--dangerously-skip-permissions`、
`--force`/`--yolo` 付きで呼ばない。

```bash
# 読み取り専用（既定）
.ai/workers/claude.sh "Review the design without changing files."
.ai/workers/claude.sh --model claude-sonnet-5 "Implement the bounded scientific change."
.ai/workers/cursor.sh "Check this implementation without changing files."
.ai/workers/gemini.sh "Summarize this log without changing files."

# 書き込み（隔離 worktree/ブランチ + 書き込み範囲を宣言したタスクのみ）
.ai/workers/cursor.sh --write "Implement the requested change and run focused tests."

# Gemini は直接書き込み不可。ブローカー経由でローカルシェルが成果物を保存する
.ai/workers/gemini.sh --broker --prompt-file <packet.md> --output-file <out.md> --acceptance headings
```

成功判定: 終了コード 0 だけで成功としない。期待成果物、受け入れテスト、必要なコミットを確認する
（`.agent/rules/09-subagent-policy.md`、`.agent/schemas/task-handoff-schema.md`）。
Gemini ブローカーの失敗は終了コード 70–77。

### 2-3. 認証エラー時のエージェントの動き

| 症状 | 動き |
|---|---|
| ラッパーが認証/ログインエラーを返す | 1 回だけ再試行。同じなら該当ワーカーを別ロールへフォールバック（`.agent/rules/08-routing-and-delegation.md`） |
| フォールバック先もない | `human_review_queue.md` に「どの CLI の再ログインが必要か」を記録し、ログイン不要の他タスクを続行 |
| 容量/レート制限 | `.agent/rules/13-retry-fallback-and-hard-stops.md` に従う |

人間は通知を受けたら 1-2 の該当コマンドだけ実行し、キューの項目を閉じる。

## 3. 現状メモ（この環境）

- 2026-10-21 時点で Codex は導入済み（0.163.0）、ChatGPT ログイン済み（既存の `~/.codex/auth.json` を再利用）。
  よって Codex については 1-2 のログインは不要で、2 章から開始できる。
- `.ai/workers/README.md` の「Installed commands」表（2026-09-23 時点）は旧バージョンのまま。
  本書の表が最新。
