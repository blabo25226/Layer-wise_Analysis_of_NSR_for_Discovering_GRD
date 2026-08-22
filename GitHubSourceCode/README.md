# GitHubSourceCode/

関連手法の調査用クローン置き場である。**研究ランタイムの依存先ではない。**

## 方針

| 区分 | パス | 扱い |
|---|---|---|
| 調査用の完全クローン | `GitHubSourceCode/NSRS`、`GitHubSourceCode/TPSR` ほか | 読書・比較・引用確認用。**importしない** |
| 実行用の切り出し | `third_party/nesymres`、`third_party/tpsr`、`third_party/nd2`、`third_party/odeformer` | アルゴリズムが使うコピー |
| 実行用設定・重み | `assets/nesymres/`、`assets/nd2/`、`assets/odeformer/` | config / eq_setting / weights |

コードから `GitHubSourceCode/...` を `sys.path` に載せる、または `from GitHubSourceCode...` する変更は行わない。

## 含まれるもの（調査用）

NeSymReS（NSRS）、TPSR、PySR、ODEFormer、ND2、D-CODE、pySINDy、dynGENIE3、SRBench、LoRA、GNW など。
巨大な成果物・データ・checkpointが混ざっている場合があるため、安易にGitへ追加しない。

## やってよいこと / 避けること

- よい: 論文実装の確認、比較実験の設計、`source.md` との対応確認、setupスクリプトでassetsへcheckpointを用意
- 避ける: 実行時依存、`GitHubSourceCode` をアルゴリズムへ混ぜる、成果物の上書き、巨大blobの新規追跡

ランタイムで必要な互換修正は `third_party/` または `src/` のadapter側へ入れる。
