# GPU_RUN1

GPU_RUN1 reduced run（Colab Pro / NVIDIA L4、3 seeds、noise 0.1）の実行専用資産。

共通ライブラリはリポジトリ直下の `src/`、共通Phase入口は `scripts/` にある。
ここには **このrun専用** の手順・Notebook・補助スクリプトだけを置く。

## 構成

| パス | 内容 |
|---|---|
| [`runbook.md`](runbook.md) | 実行手順と実施記録 |
| [`plan_colab.md`](plan_colab.md) | Colab分割実行の計画 |
| [`notebooks/`](notebooks/) | Phase 0–9 Colab Notebook |
| [`scripts/build_colab_notebooks.py`](scripts/build_colab_notebooks.py) | Notebook生成 |
| [`scripts/reanalysis_figures.py`](scripts/reanalysis_figures.py) | 保存済み結果からの図表再生成 |

## 成果物の場所（ここには置かない）

| 種類 | パス |
|---|---|
| 叙述レポート | [`results/GPU_RUN1_report.md`](../results/GPU_RUN1_report.md) |
| 再解析レポート | [`results/GPU_RUN1_reanalysis_report.md`](../results/GPU_RUN1_reanalysis_report.md) |
| raw run | `results/runs/<run-id>/`（gitignore） |
| 図表 | [`graphs/colab_reduced_20260729_03/`](../graphs/colab_reduced_20260729_03/) |

## 共通スクリプト（移動しない）

`scripts/ops/run_gpu_pipeline.sh`、`scripts/ops/preflight_gpu.py`、`scripts/ops/validate_gpu_run.py` などは
GPU実験共通の入口であり、`scripts/ops/` に置く。Phase入口は `scripts/phases/` にある。
