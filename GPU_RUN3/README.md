# GPU_RUN3

GPU_RUN3は、**ND²の公式再現** と **NDformerの層解析** を同格の主目的とする実験キャンペーンである。
計画の正本は [`plan.md`](plan.md)。DREAM4、ヒトデータ、PySR / TPSR 比較は扱わない。

実行環境はローカルPC（Python 3.10 の `lansr310`、RTX 2070）である。公式ND²実装は
[`third_party/nd2`](../third_party/nd2/) の固定コピーだけを import する。
`GitHubSourceCode/ND2` は調査用であり、実行時に使わない。

## 実行順

| Phase | 入口 | 内容 |
|---|---|---|
| 0 | [`scripts/phases/gpu_run3_phase0_preflight.py`](../scripts/phases/gpu_run3_phase0_preflight.py) | 環境、upstream freeze、checkpoint、architecture inventory、parser / MCTS smoke |
| 1 | [`scripts/phases/gpu_run3_phase1_policy.py`](../scripts/phases/gpu_run3_phase1_policy.py) | NDformer teacher-forcing policy reproduction |
| 2 | [`scripts/phases/gpu_run3_phase2_pipeline.py`](../scripts/phases/gpu_run3_phase2_pipeline.py) | NDformer-guided MCTS pipeline |
| 3 | [`scripts/phases/gpu_run3_phase3_benchmark.py`](../scripts/phases/gpu_run3_phase3_benchmark.py) | 公式10 synthetic systems の formula recovery |
| 4 | [`scripts/phases/gpu_run3_phase4_probes.py`](../scripts/phases/gpu_run3_phase4_probes.py) | hidden state、linear probe、gradient norm、CKA |
| 5 | [`scripts/phases/gpu_run3_phase5_decoderlens.py`](../scripts/phases/gpu_run3_phase5_decoderlens.py) | encoder intermediate decode、decoder logit-lens |
| 6 | [`scripts/phases/gpu_run3_phase6_causal.py`](../scripts/phases/gpu_run3_phase6_causal.py) | IOLE、ablation、activation intervention、update sensitivity |
| 7 | [`scripts/phases/gpu_run3_phase7_selective_ft.py`](../scripts/phases/gpu_run3_phase7_selective_ft.py) | validation ranking freeze、frozen/full/top1/top3/random3 |
| 8 | [`scripts/phases/gpu_run3_phase8_test.py`](../scripts/phases/gpu_run3_phase8_test.py) | 固定後の analysis-test 一度きり評価 |
| 9 | [`scripts/phases/gpu_run3_phase9_pretrain_dist.py`](../scripts/phases/gpu_run3_phase9_pretrain_dist.py) | optional retrieved nearest TED |

```bash
conda activate lansr310
bash scripts/ops/run_gpu_run3.sh --smoke --run-id gpu_run3_smoke_01 --allow-cpu
bash scripts/ops/run_gpu_run3.sh --run-id <fixed-commit-run-id>
```

`--dry-run` はcheckpointを読まず、schema用のdummy出力だけを書く。
`--from-phase N` で途中再開できる。Phase 1以降はPhase 0の `preflight.json` を要求する。

## 設定

| パス | 内容 |
|---|---|
| [`configs/gpu_run3/base.yaml`](../configs/gpu_run3/base.yaml) | seed、timeout、checkpoint URL、smoke/full budget |
| [`configs/gpu_run3/mcts.yaml`](../configs/gpu_run3/mcts.yaml) | NDformer-guided MCTS |
| [`configs/gpu_run3/systems.yaml`](../configs/gpu_run3/systems.yaml) | 論文10 systems と公式 `synthetic.yaml` の対応 |

checkpointは `assets/nd2/weights/checkpoint.pth`（gitignore）。Phase 0が未取得なら公式Releaseから取得する。

## テスト

```bash
python -m pytest -q GPU_RUN3/tests
```
