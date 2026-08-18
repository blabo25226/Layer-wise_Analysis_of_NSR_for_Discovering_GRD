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
| 1 | [`scripts/phases/gpu_run4_phase1_eval.py`](../scripts/phases/gpu_run4_phase1_eval.py) | ODEBench真式のparse、canonical / skeleton、symbolic equivalence、TED |
| 2 | [`scripts/phases/gpu_run4_phase2_repro.py`](../scripts/phases/gpu_run4_phase2_repro.py) | ODEBench reconstruction / generalization / noise+subsampling、`ODEFormer (opt)` |
| 3 | [`scripts/phases/gpu_run4_phase3_beam.py`](../scripts/phases/gpu_run4_phase3_beam.py) | beam 50 の generation vs selection 診断 |
| 4 | [`scripts/phases/gpu_run4_phase4_corpus.py`](../scripts/phases/gpu_run4_phase4_corpus.py) | 公式generatorの独立corpusとteacher-forcing CE |
| 5 | [`scripts/phases/gpu_run4_phase5_observational.py`](../scripts/phases/gpu_run4_phase5_observational.py) | probe / gradient / CKA |
| 6 | [`scripts/phases/gpu_run4_phase6_causal.py`](../scripts/phases/gpu_run4_phase6_causal.py) | residual-zero ablation、control hook |
| 7 | [`scripts/phases/gpu_run4_phase7_iole.py`](../scripts/phases/gpu_run4_phase7_iole.py) | 16層 IOLE + full FT |
| 8 | [`scripts/phases/gpu_run4_phase8_selective.py`](../scripts/phases/gpu_run4_phase8_selective.py) | validation rankingによる選択FT |
| 9 | [`scripts/phases/gpu_run4_phase9_final.py`](../scripts/phases/gpu_run4_phase9_final.py) | analysis-test 一度きり、Result A / B |

```bash
conda activate lansr310
export CUDA_VISIBLE_DEVICES=0
bash scripts/ops/run_gpu_run4.sh --run-id gpu_run4_phase0_01
bash scripts/ops/run_gpu_run4.sh --smoke --run-id gpu_run4_smoke_01
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

しかし **公開checkpointは論文Tableと一致しない**。Go 1のarchitecture照合は失敗した。以降のPhaseは **公開4+12 / 約61Mモデル** の再現として実施した。論文の4+16 / 約86M Tableの再現ではない。

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

## Phase 2–9の実施結果（`gpu_run4_phase0_01`、公開4+12 checkpoint）

1 seed、 $`\sigma\in\{0,0.05\}`$ 、 $`\rho\in\{0,0.5\}`$ 、beam 50。論文Figure 4の $`\sigma`$ 6点グリッドと3 seedsではない。平均 $`R^2`$ は外れ値で壊れるため、主に中央値を読む。

### Result A: 再現

| 項目 | 値 | 出典 |
|---|---|---|
| ODEBench cells | 63 systems $`\times`$ 4 corruptions = 252 | `phase2/eval.json` |
| valid rate | 0.921（232 / 252） | 同上 |
| reconstruction $`R^2>0.9`$ | 0.647 | 同上 |
| reconstruction $`R^2`$ 中央値 | 0.980（valid） / 0.971（penalized） | 同上 |
| generalization $`R^2`$ 中央値 | 0.696（valid） / 0.593（penalized） | 同上 |
| canonical exact | 0 | 同上 |
| skeleton exact | 0.075 | 同上 |
| TED 中央値 | 16 | 同上 |
| true skeleton in beam | 0.091（252 groups） | `phase3/eval.json` |
| unique skeletons / beam 平均 | 9.19 | 同上 |
| `ODEFormer (opt)` recon $`R^2`$ 中央値 | 0.906（n=32 qualitative panel） | `phase2/eval.json` |
| 失敗 | NaN 18、integration 10（タグ合計28。うち recon 成功で gen のみ失敗が8件。invalid は20） | 同上 |
| Phase 2 wall | 1116 s | runner |

低NMSE/高reconstructionは式回復を意味しない。canonical exactは0、beam内skeletonも約9%である。

### Result B: 層解析（16層 = encoder 4 + decoder 12）

独立corpusは公式 `env.gen_expr` から 48 / 16 / 16、skeleton漏洩0。ODEBenchはFTに使っていない。

| 解析 | 上位 | 出典 |
|---|---|---|
| encoder probe（dimension） | `encoder_0`, `encoder_1`, `encoder_2` | `phase5/eval.json` |
| causal ablation $`\Delta`$ CE | `encoder_3`, `decoder_3`, `decoder_0` | `phase6/eval.json` |
| IOLE | `decoder_7`, `encoder_0`, `encoder_2` | `phase7/eval.json` |

analysis-test CE（4 FT steps、一度きり）:

| 条件 | test CE |
|---|---|
| frozen | 1.674 |
| causal_top3 | 1.679 |
| top1 (`decoder_7`) | 1.682 |
| random3 平均付近 | 1.683–1.693 |
| top3 | 1.696 |
| bottom3 | 1.692 |
| full | 1.797 |

短いFTではfrozenが最も良く、fullが悪化した。これは「少数層がfullに勝つ」証拠ではなく、step数不足と過学習の可能性が高い。control hookはbaselineを変えていない。

因果decodeはbeam 50ではなくteacher-forcing CEである。storage爆発を避けるため中間hiddenの全保存はしていない。

保存先は `results/runs/gpu_run4_phase0_01/phase{2-9}/`（gitignore）。数値は上表のとおり `eval.json` から転記した。

### このrunが計画正本より小さい点

[`plan.md`](plan.md) の論文グリッド（ $`\sigma`$ を 0 から 0.05 まで 0.01刻み、3 seeds、約2万式corpus、介入後beam 50）は未実施である。今回のfull設定は `configs/gpu_run4/base.yaml` の `full:` ブロックであり、再現対象は `architecture_target: released_checkpoint_4enc_12dec_61M` である。

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
