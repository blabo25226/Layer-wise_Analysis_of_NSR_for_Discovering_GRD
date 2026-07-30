# GPU_RUN1 (`colab_reduced_20260729_03`) の図表

**世代: GPU_RUN1 のみ。** 3 seeds、noise 0.1 の探索的 reduced run である。
CPU pilot（旧評価設計）および今後の GPU_RUN2 の数値は含まない。
`results/phase_results/*_report.md` の一部は device `cpu` の旧世代であり、
ここの数値と同じ表に載せてはならない。

生成元 run: `results/runs/colab_reduced_20260729_03/`
生成スクリプト: [`scripts/reanalysis_gpu_run1_figures.py`](../../scripts/reanalysis_gpu_run1_figures.py)
解説レポート: [`results/GPU_RUN1_reanalysis_report.md`](../../results/GPU_RUN1_reanalysis_report.md)

再生成:

```bash
python scripts/reanalysis_gpu_run1_figures.py \
    --run-id colab_reduced_20260729_03 \
    --suite diverse_gpu_n0.1 \
    --seeds 0 1 2
```

新規の学習・推論は行わない。入力は保存済み JSON のみである。

## figures/

| file | 内容 | 元データ |
|---|---|---|
| `phase4_layer_contribution.png` / `.svg` | 単層 fine-tuning の寄与プロファイル。(a) failure-penalized NMSE、(b) validation cross-entropy。破線は全層 FT、点線は pretrained。誤差棒は 3 seeds の Student $t$ 95% 区間、点は個別 seed。 | `phase4_multiseed/raw_scores_seed{0,1,2}.json` |
| `phase45_recovery_and_equivalence.png` / `.svg` | (a) 骨格別 skeleton recovery（上段 validation = 訓練済み骨格、下段 test = 未知骨格）と指数多重集合の一致率、(b) 指数多重集合の分布（train pool / test 真値 / test 予測）、(c) 事前指定 equivalence margin に対する paired 差。 | `phase4_multiseed/equations_seed{0,1,2}.json`、`phase5_seed{0,1,2}/selective_results.json`、`phase5_multiseed/summary.json`、`input_data/diverse_gpu_n0.1/index.json` |
| `phase67_baselines_and_transfer.png` / `.svg` | (a) 探索法（beam / TPSR）× fine-tuning の 2×2、wall-clock と valid rate を注記、(b) DREAM4 Size10 / Size100 への転移、破線は平均予測器 NMSE=1、(c) regulator selection の edge F1。 | `phase6_noise_multiseed/summary.json`、`phase7_multiseed/summary.json` |
| `phase8_human_lodo.png` / `.svg` | (a) 方法別の in-donor / held-out-donor NMSE と gap、(b) donor 別の held-out NMSE。有限差分ターゲットに対する値であり、真の ODE 微分ではない。 | `phase8_lodo_seed{0,1,2}/lodo_results.json`、`phase8_lodo_multiseed/summary.json`、`phase8_pysr_seed{0,1,2}/pysr_results.json` |

## tables/

| file | 内容 |
|---|---|
| `phase45_condition_summary.csv` | validation の層別 skeleton recovery（Phase 4、各条件 $n=72$ problems）と test の条件別 failure-penalized NMSE（Phase 5、3 seeds）。`split` 列で両者を区別する。両 split は別の指標系列であり、単一のランキングとして読んではならない。 |
| `phase45_skeleton_recovery.csv` | 骨格別の skeleton recovery と指数多重集合一致率。`mass_action`（一致 1.00 / recovery 0.00）と `toggle_n2`（1.00 / 0.11）は代数的同値だが異なる因数分解形であり、定数プレースホルダ比較で打ち消されない指標側の限界を示す。 |
| `phase8_human_per_donor.csv` | donor 別・方法別の in-donor / holdout NMSE（3 seeds の mean / std / count）。donor 11 で方法間の順序が逆転する。 |

## 読み方の注意

- `sym_recovery` として保存されている値は exact = equiv = 0 であり、実質的に
  **skeleton recovery** である。本図表では `skeleton_recovery` と表記している。
- test の recovery 0 は「fine-tuning が式回復に寄与しない」ではなく
  「訓練分布に無い骨格（Hill 係数 $n=3,4$）へ外挿できない」を測っている。
  train ∩ test の骨格集合は空である。
- validation の骨格はすべて残り train pool にも存在する（suite の motif が定数込みで
  一意なため、グループ分割が実質的に問題単位分割に退化している）。
  したがって validation の recovery は in-distribution 性能である。
- ヒトデータ（GSE112372）は 20 遺伝子・4 donors・5 時点の application demo であり、
  有限差分ターゲットは真の ODE 微分ではない。ここの式を制御 ODE や因果機構と解釈してはならない。
- PySR の budget（12 iterations、15 秒、CPU）は NeSymReS 側（decode 30 秒 + GPU FT）と
  統一されていない。図4 は方法比較として読めない。
- 図中テキストは英語である。生成環境に CJK フォントが無く日本語が豆腐化するためで、
  caption と解説は日本語で記述する。
