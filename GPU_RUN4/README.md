# GPU_RUN4

GPU_RUN4は、**公開ODEFormerの公式再現** と **encoder / decoder全層の層解析** を同格の主目的とする実験キャンペーンである。
計画の正本は [`plan.md`](plan.md)。DREAM4、ヒトデータ、NeSymReS fine-tuning比較は扱わない。

実行環境はローカルPC（Python 3.10 の `lansr310`、RTX 2070）である。公式ODEFormer実装は
[`third_party/odeformer`](../third_party/odeformer/) の固定コピーだけを import する。
`GitHubSourceCode/ODEFormer` は調査用であり、実行時に使わない。

## 実行順

| Phase | 入口 | 内容 |
|---|---|---|
| 0 | [`scripts/phases/gpu_run4_phase0_preflight.py`](../scripts/phases/gpu_run4_phase0_preflight.py) | 環境、upstream freeze、checkpoint、architecture audit、公式demo smoke |
| 1 | [`scripts/phases/gpu_run4_phase1_eval.py`](../scripts/phases/gpu_run4_phase1_eval.py) | ODEBench真式のparse、canonical / skeleton、symbolic equivalence、TED、timeout / 特異点 |
| 2–9 | 未実装 | [`plan.md`](plan.md) の Phase 2 以降 |

```bash
conda activate lansr310
bash scripts/ops/run_gpu_run4.sh --run-id gpu_run4_phase0_01
bash scripts/ops/run_gpu_run4.sh --from-phase 1 --to-phase 1 --run-id gpu_run4_phase0_01
bash scripts/ops/run_gpu_run4.sh --smoke --run-id gpu_run4_smoke_01 --allow-cpu
```

`--dry-run` はcheckpointを読まず、schema用のdummy出力だけを書く。
`--skip-demo` はcheckpoint loadとarchitecture inventoryまでで止める。
`--skip-download` はGoogle Driveからの重み取得を行わない。

Phase 0のGo 1は次をすべて満たしたときだけ成功とする。

- official checkpoint load
- architecture特定
- official demo inference
- beam size 50 / beam sampling
- 予測ODEの再積分

論文Table（4 encoder + 16 decoder / dim 512 / 16 heads / 約86M）との一致は **別ゲート** である。
parserのCLI defaultはarchitectureの根拠にしない。checkpoint実体を読む。

## Phase 0の実施結果（`gpu_run4_phase0_01`）

公式demoは成功した。READMEと同じ2D軌跡でbeam 50 sampling、50候補、再積分 $`R^2\approx 0.997`$、所要約2秒（RTX 2070）。

しかし **公開checkpointは論文Tableと一致しない**。Go 1のarchitecture照合は失敗し、長時間runには進まない。

| 項目 | 論文 | parser default | 公開checkpoint |
|---|---|---|---|
| encoder層 | 4 | 4 | **4** |
| decoder層 | 16 | 12 | **12** |
| encoder dim | 512 | 256 | **256** |
| decoder dim | 512 | 256 | **512** |
| heads | 16 | 16 | **16** |
| パラメータ | 約86M | — | **60,646,773** |
| beam | sampling 50 / 0.1 | sampling 1 / 0.1 | **sampling 50 / 0.1** |

コメントアウトされていた旧Google Drive ID `18CwlutaFF_tAOObsIukrKVZMPmsjwNwF` はODEFormerではなく `symbolicregression` pickleであり、86Mモデルではない。

次の判断が必要である。公開checkpoint（4+12、encoder 256 / decoder 512）を再現対象としてplanを改訂するか、論文サイズの重みを別途探すか。Phase 1の評価器固定はarchitecture一致を必要としない。Phase 2の長時間ODEBench gridは、この判断が終わるまで開始しない。

## Phase 1の実施結果（`gpu_run4_phase0_01`）

CPUで約3秒。ODEBench 63式をすべてparseし、恒等比較のcanonical TEDは0、prefix往復も63/63で一致した。Go条件はすべて成立した。

| 項目 | 結果 |
|---|---|
| parse成功 | 63 / 63 |
| 恒等比較 canonical exact | 63 / 63 |
| prefix往復 | 63 / 63 |
| gold suite | 11件すべて成功 |
| component順 `x_0 \| x_1` vs `x_1 \| x_0` | 非同値（並べ替えない） |
| timeout | `TEDTimeout` を約0.05秒で記録 |
| 特異点 `1/x_0` at `x_0=0` | `Inf` を記録し、equivalentへ強制しない |
| `normalized_ted` | $`\mathrm{ted}_{raw} / (\mathrm{size}_{true} + \mathrm{size}_{pred})`$ |

評価器はODEFormer / ODEBenchの infix、prefix、`|` 区切り、`c_i` 定数、`cot` を扱う。GPU_RUN3のND2演算子（`aggr` / `sour` / `targ`）は使わない。CAS timeoutは10秒、TED timeoutは10秒である。

保存先は `results/runs/gpu_run4_phase0_01/phase1/`（`eval.json`、`gold_cases.json`、`odebench_parsed.json`、`identity_records.json`）。

本実験前に固定した定義と、後続Phaseへ持ち越す限界は次のとおりである。test結果を見てから変えない。

- `normalized_ted` は $`\mathrm{ted}_{raw} / (\mathrm{size}_{true} + \mathrm{size}_{pred})`$ である。多次元ではTED比較用に `system` ノードを1つ足す。したがって `x_0 | x_1` と `x_1 | x_0` の gold は TED 2、正規化 $`2/(3+3)=1/3`$ である。
- skeleton は数値葉と `c_i` を `CONST` にする。整数指数もその対象なので、`x^2` と `x^3` は skeleton 一致になる。Phase 3のbeam診断で次数の違いをskeleton不一致にしたい場合は、そのPhaseのtest評価より前に定義を改める。
- 合算ノード数が40を超える式はCASを省略し、安全域の数値確認へ落とす。timeoutはmain threadの `SIGALRM` であり、worker threadでは効かない。
- inverse-trig（`arcsin` など）の非canonical同値は、現状CAS/数値経路で落とすことがある。ODEBench真式には含まれない。

## 設定

| パス | 内容 |
|---|---|
| [`configs/gpu_run4/base.yaml`](../configs/gpu_run4/base.yaml) | seed、timeout、checkpoint URL、paper protocol |

checkpointは `assets/odeformer/weights/odeformer.pt`（gitignore）。Phase 0が未取得なら公式Google Drive IDから取得する。
SHA256は `56754040be5aa92ed4767fc43ee2008faa293f87c12b643e66c7df3e1623a5e8`。
追加依存は `gdown` と `regex` である。`lansr310` に無ければ Phase 0 の前に入れる。

```bash
conda activate lansr310
pip install gdown regex
```

## テスト

```bash
conda activate lansr310
python -m pytest -q GPU_RUN4/tests
```

## 構成

| パス | 内容 |
|---|---|
| [`plan.md`](plan.md) | GPU_RUN4計画の正本 |
| [`tests/`](tests/) | GPU_RUN4固有テスト |
