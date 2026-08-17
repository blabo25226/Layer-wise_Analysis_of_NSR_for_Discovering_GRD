# GPU_RUN3/tests/

GPU_RUN3固有テスト。ND²公式実装は `third_party/nd2` から import する。

```bash
conda activate lansr310
python -m pytest -q GPU_RUN3/tests
```

| ファイル | 範囲 |
|---|---|
| `test_gpu_run3_core.py` | formula record schema、TED、Kuramoto prefix、Phase CLI |
