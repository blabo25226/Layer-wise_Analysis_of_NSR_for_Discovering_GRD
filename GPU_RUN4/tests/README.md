# GPU_RUN4/tests/

GPU_RUN4固有テスト。ODEFormer公式実装は `third_party/odeformer` から import する。

```bash
conda activate lansr310
python -m pytest -q GPU_RUN4/tests
```

| ファイル | 範囲 |
|---|---|
| `test_gpu_run4_core.py` | formula record schema、architecture audit、ODEBench 63 systems、Phase 0 CLI |
