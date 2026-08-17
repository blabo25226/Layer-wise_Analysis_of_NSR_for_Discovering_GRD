# third_party/

研究ランタイムが import する外部実装の **vendored コピー** である。

| パス | 由来 | 用途 |
|---|---|---|
| `nesymres/` | [NeuralSymbolicRegressionThatScales](https://github.com/SymposiumOrganization/NeuralSymbolicRegressionThatScales) の `GitHubSourceCode/NSRS/src` から抽出 | `pip install -e third_party/nesymres` |
| `tpsr/` | [tpsr](https://github.com/deep-symbolic-mathematics/tpsr) の `GitHubSourceCode/TPSR` から実行に必要な一部を抽出 | `sys.path` に載せて `rl_env` 等を import |
| `nd2/` | [ND2](https://github.com/tsinghua-fib-lab/ND2) の `GitHubSourceCode/ND2` から、baseline / plot / 画像 / 出力埋め込みnotebookを除いてコピー | `sys.path` に載せて `ND2` を import。`pip install -e` は公式 `setup.py` のCUDA pinがあるため使わない |

実装はMIT Licenseであり、著作権表示と許諾文は各directoryの`LICENSE`に保持する。

## 取り込み時のprovenance

整理commit `1e5c74b` における調査用snapshotと実行用copyは、次のGit tree objectで固定される。
調査用directoryには上流repositoryの`.git`が残っていないため、元のupstream commitは特定できない。

| 対象 | LANSR tree object |
|---|---|
| `GitHubSourceCode/NSRS/src` | `22f733c83e022cecf9f2af0207095d21572b112a` |
| `third_party/nesymres` | `8fec4f5345aa1fdf9dc8b1da7acdf1e8461b6c2d` |
| `GitHubSourceCode/TPSR` | `1fc652e426845203c30c054b8704e325787ee91c` |
| `third_party/tpsr` | `b52f9f6955b278261d96447111930e6ac7a4f680` |

取り込み時のLANSR側差分は次のとおりである。

- NeSymReS: 生成済み`nesymres.egg-info/`を除外し、package importを安定させる空の`__init__.py`を3件追加した。その他の収録ソースは調査用snapshotと同一である。
- TPSR: LANSRのMCTS実行に必要なsubsetだけを収録し、`reward.py`のBFGS importをinstall後の`nesymres.architectures`へ合わせた。
- ND2: 調査用snapshot `GitHubSourceCode/ND2` から実行に必要なpackage / config / search / simulate をコピーした。`scripts/*.ipynb` は出力埋め込みで数十MBになるため実行用copyから除外し、調査用treeに残す。upstream `.git` は無く、公式commitはPhase 0のtree fingerprintで固定する。LANSR側は `src/gpu_run3_runtime.py` のcheckpoint loaderで、公式 `src` pickle名を `ND2` へ置換する互換処理を行う。コピーしたND2ソース自体は変更していない。

## 重要な区別

- `GitHubSourceCode/NSRS`・`GitHubSourceCode/TPSR`・`GitHubSourceCode/ND2` … 調査用の完全クローン。**実行時に import しない**
- `third_party/` … 実行用に切り出したコピー。アルゴリズムはここだけを見る
- `assets/nesymres/` … config / eq_setting / weights（weightsはgitignore）
- `assets/nd2/` … NDformer checkpoint（weightsはgitignore）

上流を更新した場合は、差分を確認したうえでこのdirectoryへ再コピーし、LANSR側の互換パッチを残す。
`GitHubSourceCode/` へのパスをコードへ戻さない。
