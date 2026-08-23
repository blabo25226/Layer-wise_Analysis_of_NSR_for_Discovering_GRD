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
