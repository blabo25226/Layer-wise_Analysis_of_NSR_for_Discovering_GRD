# assets/odeformer/

ODEFormer の実行用重み置き場。巨大ファイルはGit管理外。

| パス | 内容 |
|---|---|
| `weights/odeformer.pt` | 公式pretrained pickle（`SymbolicTransformerRegressor(from_pretrained=True)` が取得するファイル） |

取得元（公式README / `sklearn_wrapper.load_pretrained`）:

- Google Drive ID: `1L_UZ0qgrBVkRuhg5j3BQoGxlvMk_Pm1W`
- URL: `https://drive.google.com/uc?id=1L_UZ0qgrBVkRuhg5j3BQoGxlvMk_Pm1W`

SHA256: `56754040be5aa92ed4767fc43ee2008faa293f87c12b643e66c7df3e1623a5e8`（444MB、日付スタンプ 2023-09-28）。

Phase 0が未取得なら同じIDから `gdown` でダウンロードする。parser defaultではなく、このcheckpointの実model objectをarchitectureの根拠にする。

Phase 0で確認した実体は論文Table（4 encoder + 16 decoder / dim 512 / 約86M）ではなく、
**4 encoder (dim 256) + 12 decoder (dim 512)、16 heads、60,646,773 parameters、beam sampling 50 / 0.1** である。
sklearn_wrapperに残る旧Drive IDはNeSymReS系 `symbolicregression` pickleであり、論文サイズのODEFormerではない。
