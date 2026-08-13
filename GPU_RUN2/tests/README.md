# GPU_RUN2/tests/

GPU_RUN2固有テスト。共通の `src/` 単体テストはリポジトリ直下の `tests/` に置く。

```powershell
python -m pytest -q GPU_RUN2/tests
```

| ファイル | 範囲 |
|---|---|
| `test_gnw_synthetic.py` | GNW式、240 problems、paired noise、domain範囲、有限差分非使用 |
| `test_oracle_and_splits.py` | oracle入力、主split、structure-OOD、seed bundle |
| `test_operator_policy.py` | 制限付き`pow`、除算安全性、NeSymReS / PySR operator対応 |
| `test_records_and_resume.py` | equation record、2軸OOD field、failure、checkpoint / resume、random 3 |
| `test_live_paths.py` | GNW→fine-tune式、dummy record、DecoderLens parse、ablation hook、Phase 4 ranking / runner test split |
