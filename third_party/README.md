# third_party/

研究ランタイムが import する外部実装の **vendored コピー** である。

| パス | 由来 | 用途 |
|---|---|---|
| `nesymres/` | `GitHubSourceCode/NSRS/src` から抽出 | `pip install -e third_party/nesymres` |
| `tpsr/` | `GitHubSourceCode/TPSR` から実行に必要な一部 | `sys.path` に載せて `rl_env` 等を import |

## 重要な区別

- `GitHubSourceCode/NSRS`・`GitHubSourceCode/TPSR` … 調査用の完全クローン。**実行時に import しない**
- `third_party/` … 実行用に切り出したコピー。アルゴリズムはここだけを見る
- `assets/nesymres/` … config / eq_setting / weights（weightsはgitignore）

上流を更新した場合は、差分を確認したうえでこのdirectoryへ再コピーし、LANSR側の互換パッチを残す。
`GitHubSourceCode/` へのパスをコードへ戻さない。
