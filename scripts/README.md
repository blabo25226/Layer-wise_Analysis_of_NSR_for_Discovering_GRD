# scripts/

研究実験のエントリポイント一覧である。共通処理は `src/` に置き、ここにはPhase実行・運用・旧issue用の薄い入口だけを置く。

## Phase 実験

| スクリプト | 内容 |
|---|---|
| `phase0_check_environment.py` | 環境・checkpoint確認 |
| `phase0_nesymres_smoke.py` | NeSymReS smoke |
| `phase0_pysr_smoke.py` | PySR smoke |
| `phase0_tpsr_smoke.py` | TPSR smoke |
| `phase0_run_all.py` | Phase 0一括 |
| `generate_diverse_suite.py` | 構造分離した合成GRN生成 |
| `phase2_run_baselines.py` | NeSymReS / PySR baseline |
| `phase3_layer_scan.py` | 層スキャン |
| `phase4_layer_contribution.py` | 層寄与度（単一seed系） |
| `phase4_multiseed.py` | validation上の多seed層寄与 |
| `phase5_selective_train.py` | 独立testでの選択的FT比較 |
| `phase6_tpsr_2x2.py` | selective FT × TPSR の2×2 |
| `phase6_noise_sweep.py` | ノイズ条件sweep |
| `phase7_generate_dreamlike.py` | DREAM風合成データ |
| `phase7_package_a.py` | Phase 7 package A |
| `phase7_run_oracle.py` | oracle変数条件 |
| `phase7_dream4_size10.py` | DREAM4 Size10 |
| `phase7_dream4_size100.py` | DREAM4 Size100 |
| `phase7_sbml_supervised_ft.py` | SBML teacher FT |
| `phase8_run_human.py` | ヒト時系列 |
| `phase8_lodo.py` | leave-one-donor-out |
| `phase8_pysr_lodo_local.py` | ローカルPySR LODO |
| `phase8_pysr_target_worker.py` | PySR target worker |

## GPU / 運用

| スクリプト | 内容 |
|---|---|
| `preflight_gpu.py` | GPU実験前検査 |
| `run_gpu_pipeline.sh` | GPU一括パイプライン |
| `run_gpu_campaign.sh` | campaign実行 |
| `run_manifest.py` | run manifest操作 |
| `validate_gpu_run.py` | GPU run検証 |
| `export_run_summary.py` | run要約の出力 |
| `build_colab_notebooks.py` | Colab Notebook生成 |
| `reanalysis_gpu_run1_figures.py` | GPU_RUN1図表再生成 |
| `aggregate_phase5_runs.py` | Phase 5集約 |
| `aggregate_phase6_runs.py` | Phase 6集約 |
| `aggregate_phase7_runs.py` | Phase 7集約 |
| `aggregate_phase8_runs.py` | Phase 8集約 |
| `setup_phase0_links.ps1` | Windows向けリンク準備 |

## Legacy / 初期issue

初期開発時のissue対応スクリプト。新規実験の入口としては使わない。

- `issue3_list_layers.py`
- `issue4_5_freeze_check.py`
- `issue6_generate_synthetic.py`
- `issue7_pysr_smoke.py`

## 実行の目安

```bash
python -m compileall -q src scripts tests
python -m pytest -q
python scripts/preflight_gpu.py --checkpoint /path/to/model.ckpt
bash -n scripts/run_gpu_pipeline.sh
```

GPU手順の本文は [`docs/runbooks/GPU_RUN1.md`](../docs/runbooks/GPU_RUN1.md) を参照する。
次の確認実験計画は [`docs/plans/20260729_GPU_RUN2.md`](../docs/plans/20260729_GPU_RUN2.md) にある。
