# GPU_RUN2

GPU_RUN2は、合成GNW式だけを使った層解析とsymbolic recoveryの確認実験である。
実行環境はローカルPC（RTX 2070、64 GB RAM）であり、Google Colabは使わない。

計画の正本は [`plan.md`](plan.md)。DREAM4、ヒトデータ、有限差分、TPSR / NSR-gvs は GPU_RUN3 以降へ保留する。

## 実行順

| Phase | 入口 | 内容 |
|---|---|---|
| 0 | [`scripts/phases/gpu_run2_phase0_preflight.py`](../scripts/phases/gpu_run2_phase0_preflight.py) | 環境、checkpoint SHA256、30秒timeout、operator、schema smoke |
| 1 | [`scripts/phases/gpu_run2_phase1_data.py`](../scripts/phases/gpu_run2_phase1_data.py) | GNW G01–G08、240 problems、oracle入力、paired noise |
| 2 | [`scripts/phases/gpu_run2_phase2_baseline.py`](../scripts/phases/gpu_run2_phase2_baseline.py) | NeSymReS / PySR baseline |
| 3 | [`scripts/phases/gpu_run2_phase3_interpret.py`](../scripts/phases/gpu_run2_phase3_interpret.py) | template / next-token / n_operators probe、CKA、DecoderLens（validationのみ。候補はencoder/decoderのみ） |
| 4 | [`scripts/phases/gpu_run2_phase4_contribution.py`](../scripts/phases/gpu_run2_phase4_contribution.py) | IOLE、ablation、activation介入 |
| 5 | [`scripts/phases/gpu_run2_phase5_selective_ft.py`](../scripts/phases/gpu_run2_phase5_selective_ft.py) | frozen / full / top1 / top3 / random3、再現バイアス |
| 完了 | [`scripts/ops/finalize_gpu_run2.py`](../scripts/ops/finalize_gpu_run2.py) | schema検査、真式対予測式表、archive |
| バックアップ | [`scripts/ops/backup_gpu_run2.py`](../scripts/ops/backup_gpu_run2.py) | 完了archiveのDrive stagingとSHA256照合 |

Windowsでの一括実行:

```powershell
powershell -File scripts/ops/run_gpu_run2.ps1 -Smoke -AllowCpu -DryRun
powershell -File scripts/ops/run_gpu_run2.ps1
```

`-FromPhase 3` で途中再開できる。実行中の正本は常にローカルの `results/runs/<run-id>/` である。
Phase 2 と Phase 5 は validation のあと、条件凍結済みの **test を一度だけ** 評価する。Phase 5 の structure-holdout は Phase 4 の `conditions_structure_holdout.json`（G01–G06 パネル）を使う。

`--dry-run` はcheckpointを読まず、schema用のdummy出力だけを書く。checkpointがある live run（`--dry-run` なし）では、Phase 3 が validation probe / DecoderLens、Phase 4 が IOLE・ablation・activation介入、Phase 5 が selective FT + beam decode を実行する。OOM時はbatch/precisionを変えず fail fast する。

## 設定

| パス | 内容 |
|---|---|
| [`configs/gpu_run2/base.yaml`](../configs/gpu_run2/base.yaml) | seed bundle、noise、timeout、budget |
| [`configs/gpu_run2/operators.yaml`](../configs/gpu_run2/operators.yaml) | 共通operator allowlist |
| [`configs/gpu_run2/splits.yaml`](../configs/gpu_run2/splits.yaml) | 主splitとstructure-holdout |

## テスト

```powershell
python -m pytest -q GPU_RUN2/tests
```

詳細は [`tests/README.md`](tests/README.md)。

## 構成

| パス | 内容 |
|---|---|
| [`plan.md`](plan.md) | GPU_RUN2計画の正本 |
| [`tests/`](tests/) | GPU_RUN2固有テスト |
| [`notebooks/`](notebooks/) | 任意の結果閲覧用。実験実行の必須入口ではない |

## 参照

- GPU_RUN1結果: [`results/GPU_RUN1_report.md`](../results/GPU_RUN1_report.md)
- 共通コード: [`src/`](../src/)
- 共通Phase入口: [`scripts/phases/`](../scripts/phases/)
