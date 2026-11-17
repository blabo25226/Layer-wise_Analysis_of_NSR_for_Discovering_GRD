# GPU_RUN6：酵素反応速度論の有効法則と ODEFormer の層別解析

公開 ODEFormer が酵素反応の有効法則（Michaelis–Menten 型の有理式）の構造を回復できるかを、複雑さをそろえた
多項式と比べる。あわせて、層別解析の各手法が何を明らかにし、互いに一致するかを調べる。

| 文書 | 内容 |
| --- | --- |
| [`plan.md`](plan.md) | 事前登録（仮説 H1〜H9、指標、判定基準、予備観察の開示） |
| [`literature.md`](literature.md) | 文献レビューと研究上の空白 |
| [`GPU_RUN6_report.md`](GPU_RUN6_report.md) | 結果レポート |
| [`tests/`](tests/) | データ生成と構造クラス判定の単体テスト |

## 実行

Python 3.10 の環境（`lansr310`）と GPU で、リポジトリの root から実行する。

```bash
RUN=gpu_run6_20261118_6bd40da
python scripts/phases/gpu_run6.py all --run-id $RUN       # data → behavior → tunedlens → lens → probe → patch → adapt
python scripts/reports/gpu_run6_report.py --run-id $RUN    # 統計・表・図
```

phase は個別にも実行できる（`data`, `behavior`, `tunedlens`, `lens`, `probe`, `patch`, `adapt`）。
`--smoke` は各サイズを縮小した動作確認用で、結果は解釈しない。行動評価と適応は途中から再開できる。

## 成果物

- 生の結果（git 管理外）：`results/runs/<run-id>/`
  - `data/` 生成データ、`behavior/` beam 評価、`lens/`、`probe_features.npz`、`patch/`、`adapt/`、`tuned_lens.pt`
  - `provenance_<phase>.json` に commit、コードの未 commit 変更の有無、設定、GPU を記録する。
- 図表（git 管理）：[`graphs/gpu_run6_20261118_6bd40da/`](../../graphs/gpu_run6_20261118_6bd40da/)
- コード：`src/gpu_run6/`（`enzyme.py` データと構造クラス、`behavior.py` beam 評価、`layers.py` lens・probe 特徴・
  block skip・patching、`adapt.py` FT と層移植）。RUN4 の ODEFormer ユーティリティ（`src/gpu_run4/`）を再利用する。
