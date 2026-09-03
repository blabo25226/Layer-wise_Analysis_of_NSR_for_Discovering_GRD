# GPU_RUN5 cross-model synthesis（Result E）

Run: `gpu_run5_20260823_ddd267b0`。対象はGPU_RUN2 NeSymReS、GPU_RUN3 NDformer、GPU_RUN4/5 ODEFormerである。

**Go 8 は NO-GO だったため、DREAM4・実データへの追加実験は実施しなかった。** 性能不足をデータ側の難しさと混同しないための事前固定停止であり、Phase 8の一度限りのfinal testは負／混合結果として保持する。

## 事実

| run | model | generation | probe top3 | causal top3 | robustness top3 | IOLE top3 | intervention estimand | probe∩robustness | robustness∩IOLE | status |
|---|---|---|---|---|---|---|---|---:|---:|---|
| GPU_RUN2 | NeSymReS | GPU_RUN2 fixed full run | `["decoder_0", "decoder_3", "encoder_4"]` | `[]` | `["encoder_4", "decoder_0", "decoder_3"]` | `["decoder_4", "decoder_1", "decoder_0"]` | robustness_least_damage | 1 | 0.2 | available |
| GPU_RUN3 | NDformer | GPU_RUN3 full run | `["decoder.decoder.layers.1", "decoder.decoder.layers.0", "encoder.Transformer.layers.1"]` | `["encoder.Transformer.layers.0", "encoder.Transformer.layers.1", "decoder.decoder.layers.0"]` | `[]` | `["decoder.decoder.layers.1", "decoder.decoder.layers.0", "encoder.Transformer.layers.1"]` | causal_importance | — | — | available |
| GPU_RUN4 | ODEFormer | GPU_RUN4 reduced public-checkpoint run | `["encoder_0", "encoder_1", "encoder_2"]` | `["encoder_3", "decoder_3", "decoder_0"]` | `[]` | `["decoder_7", "encoder_0", "encoder_2"]` | causal_importance | — | — | available |
| GPU_RUN5 | ODEFormer | GPU_RUN5 fixed run | `["decoder_11", "decoder_10", "decoder_9"]` | `["decoder_11", "decoder_3", "encoder_3"]` | `[]` | `["decoder_11", "decoder_10", "decoder_8"]` | causal_importance | — | — | available |

## RQ判定

横断表は各run内の順位不一致だけを比較する。モデル間で層番号、score強度、CE、TEDを同一尺度へ置かない。

## 考察

「読み出せる」「壊すと悪化する」「更新すると改善する」は別概念であり、世代ごとの不一致は単一の普遍的重要層を支持しない。

## 限界

GPU_RUN2の保存ablation/intervention順位は重要度と逆向きのrobustness順位という既知問題があり、GPU_RUN4はreduced一seedである。表にgenerationを明示して混在を防いだ。

## 未実施提案

同一corpus・同一定義・同一budgetによるモデル横断実験は別campaignとして設計する。
