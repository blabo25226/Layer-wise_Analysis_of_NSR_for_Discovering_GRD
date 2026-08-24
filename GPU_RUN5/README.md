# GPU_RUN5

GPU_RUN5は、公開ODEFormer（4 encoder + 12 decoder、約61M）を閉じたHill型GRNへ適応し、
多軌道候補選択、formula-level層ranking、介入後decodeを接続する実験である。
計画正本は [`plan.md`](plan.md)、実験前固定値は [`preregistration.json`](preregistration.json) に置く。

## 実行

Python 3.10の`lansr310`環境とCUDA GPUを使う。

```bash
conda activate lansr310
export CUDA_VISIBLE_DEVICES=0
bash scripts/ops/run_gpu_run5.sh --run-id gpu_run5_<date>_<commit8>
```

`--smoke`は配線、保存schema、resume、failure処理の確認用であり、本結果ではない。
各Phaseは`--from-phase` / `--to-phase`で再開できる。結果は
`results/runs/<run-id>/`、独立図表は`graphs/<run-id>/`へ保存する。

Phase 9はGPUを使わず、保存済みartifactをproducing manifestのSHA256と照合してから集約する。
Phase 8でGo 6 / Go 7が成立せずsealed testを開かなかった場合も、P3・P4・P7を推測で埋めず
`undecidable`としてレポートを完結させる。Phase 9自身はsealed testファイルを直接読まない。

```bash
python scripts/phases/gpu_run5_phase9.py --run-id <gpu-run5-run-id>
```

## 統合成果物

Phase 9は次の5結果を別レポートとして生成する。GPU_RUN2 / RUN3 / RUN4 / RUN5の横断表は
各run内の順位不一致だけを並べ、異なるモデル・評価世代のscoreを同一尺度として集約しない。

| Result | レポート | 内容 |
|---|---|---|
| A | [`GPU_RUN5_decoded_support_report.md`](GPU_RUN5_decoded_support_report.md) | ODEBench decoded support、R4・R5 |
| B | [`GPU_RUN5_grn_benchmark_report.md`](GPU_RUN5_grn_benchmark_report.md) | GRN generation / selection、P3・P4・P6 |
| C | [`GPU_RUN5_grn_adaptation_report.md`](GPU_RUN5_grn_adaptation_report.md) | GRN full / selective FT、forgetting、P7 |
| D | [`GPU_RUN5_layer_analysis_report.md`](GPU_RUN5_layer_analysis_report.md) | 観測・介入・formula-level層解析、P5 |
| E | [`GPU_RUN5_cross_model_synthesis.md`](GPU_RUN5_cross_model_synthesis.md) | GPU_RUN2–5の世代を分離した横断整理 |

機械判定の正本は
`results/runs/<run-id>/phase9/preregistration_outcome.json`、図表は
`graphs/<run-id>/figures/` と `graphs/<run-id>/tables/` に生成する。成功式だけでなく、
真式、生の予測式、変数名対応、構造metric、failure reasonを表へ残す。
