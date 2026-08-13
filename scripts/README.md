# scripts/

研究実験のエントリポイント。共通処理は `src/`、キャンペーン専用は `GPU_RUN1/` 等へ置く。

## 構成

```text
scripts/
  phases/    Phase 0–8 の実験入口
  ops/       GPU/manifest/集約などの運用スクリプト
  legacy/    初期issue用（新規実験では使わない）
```

ルート直下の同名ファイルは互換wrapperである。新規手順では `phases/` / `ops/` / `legacy/` を明示する。

## phases/

| スクリプト | 内容 |
|---|---|
| `generate_diverse_suite.py` | 構造分離した合成GRN生成 |
| `phase0_*.py` | 環境・NeSymReS/PySR/TPSR smoke |
| `phase2_run_baselines.py` | baseline比較 |
| `phase3_layer_scan.py` | 層スキャン |
| `phase4_*.py` | 層寄与度 |
| `phase5_selective_train.py` | 選択的FT比較 |
| `phase6_*.py` | TPSR 2×2・ノイズ |
| `phase7_*.py` | DREAM4関連 |
| `phase8_*.py` | ヒト時系列・LODO・PySR worker |
| `gpu_run2_phase0_preflight.py` | GPU_RUN2 環境 / schema smoke |
| `gpu_run2_phase1_data.py` | GNW synthetic benchmark 生成 |
| `gpu_run2_phase2_baseline.py` | NeSymReS / PySR baseline |
| `gpu_run2_phase3_interpret.py` | probe、CKA、DecoderLens |
| `gpu_run2_phase4_contribution.py` | IOLE、ablation、介入 |
| `gpu_run2_phase5_selective_ft.py` | selective FT、symbolic recovery、再現バイアス |

## ops/

| スクリプト | 内容 |
|---|---|
| `preflight_gpu.py` | GPU実験前検査 |
| `run_gpu_pipeline.sh` | GPU一括パイプライン |
| `run_gpu_campaign.sh` | campaign実行 |
| `run_manifest.py` | run manifesto操作 |
| `validate_gpu_run.py` | GPU run検証 |
| `export_run_summary.py` | run要約 |
| `aggregate_phase5_runs.py` ほか | Phase集約 |
| `setup_phase0_links.ps1` | Windows向けリンク準備 |
| `run_gpu_run2.ps1` | GPU_RUN2 Phase順次実行 |
| `finalize_gpu_run2.py` | GPU_RUN2 schema検査・表・archive |
| `backup_gpu_run2.py` | 完了archiveのDrive staging |

## legacy/

- `issue3_list_layers.py`
- `issue4_5_freeze_check.py`
- `issue6_generate_synthetic.py`
- `issue7_pysr_smoke.py`

## キャンペーン専用

| 場所 | 内容 |
|---|---|
| [`GPU_RUN1/scripts/`](../GPU_RUN1/scripts/) | Notebook生成・図表再解析 |
| [`GPU_RUN1/tests/`](../GPU_RUN1/tests/) | Colab/GPU_RUN1固有テスト |
| [`GPU_RUN2/tests/`](../GPU_RUN2/tests/) | GPU_RUN2固有テスト |

## 実行の目安

```bash
python -m compileall -q src scripts tests GPU_RUN1/scripts GPU_RUN1/tests GPU_RUN2/tests
python -m pytest -q
python scripts/ops/preflight_gpu.py \
  --weights /path/to/model.ckpt \
  --config assets/nesymres/jupyter/100M/config.yaml \
  --eq-setting assets/nesymres/jupyter/100M/eq_setting.json
bash -n scripts/ops/run_gpu_pipeline.sh
```
