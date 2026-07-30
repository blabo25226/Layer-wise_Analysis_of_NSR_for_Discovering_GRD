# GitHubSourceCode/

関連手法の調査用クローン置き場である。**研究ランタイムの依存先ではない。**

## 方針

| 区分 | パス | 扱い |
|---|---|---|
| 実行に使う参照実装 | リポジトリ直下の `NSRS/`、`TPSR/` | `src/` と `scripts/` から参照する |
| 文献調査用の外部実装 | この `GitHubSourceCode/` | 比較・読書・引用確認用。importしない |
| 文献PDF・訳 | `docs/` 配下のローカル資料 | Git管理外（`.gitignore`） |

`TPSR/` はもともとここに置いていたが、コード契約に合わせてリポジトリ直下へ昇格済みである。
ここに再度置く必要はない。

## 含まれるもの（調査用）

PySR、ODEFormer、ND2、D-CODE、pySINDy、dynGENIE3、SRBench、LoRA、GNW など、
関連手法の公式または公開実装のローカルコピーである。巨大な成果物・データ・checkpointが
混ざっている場合があるため、安易にGitへ追加しない。

## やってよいこと / 避けること

- よい: 論文実装の確認、比較実験の設計、`source.md` との対応確認
- 避ける: `from GitHubSourceCode...` のような実行時依存、成果物の上書き、巨大blobの新規追跡

ランタイムで必要な変更は、原則として `src/` のadapter側、または直下の `NSRS/` / `TPSR/` へ最小限だけ入れる。
