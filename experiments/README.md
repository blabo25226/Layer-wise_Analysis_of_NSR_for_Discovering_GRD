# experiments/

終了した実験キャンペーンごとの計画・runbook・レポート・固有テストを置く。共通コードは `src/`、Phase入口は `scripts/`、
生成物は `results/` と `graphs/` にある。2026-11-17 にrootからこのフォルダへ移動した（中身は変更していない）。

| フォルダ | 内容 |
| --- | --- |
| [`CPU_RUN/`](CPU_RUN/) | CPU上のPhase 0–8 pilot |
| [`GPU_RUN1/`](GPU_RUN1/) | Colab L4 での NeSymReS reduced run（notebook・runbook） |
| [`GPU_RUN2/`](GPU_RUN2/) | NeSymReS 固定commit run（GNW synthetic、remote GPU） |
| [`GPU_RUN3/`](GPU_RUN3/) | ND2 / NDformer 再現と層解析 |
| [`GPU_RUN4/`](GPU_RUN4/) | 公開 ODEFormer checkpoint の再現と16層解析 |
| [`GPU_RUN5/`](GPU_RUN5/) | ODEFormer の閉じたHill型GRNへの適応 |
| [`GPU_RUN6/`](GPU_RUN6/) | 酵素反応速度論の有効法則（有理式）と ODEFormer の層別解析手法の比較 |

進行中の Multi-AI 自律研究キャンペーンは root の [`GPU_RUNmultiAI/`](../GPU_RUNmultiAI/) にある。
