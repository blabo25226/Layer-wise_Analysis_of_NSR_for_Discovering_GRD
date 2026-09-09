# assets/nd2/

ND² / NDformer の実行用重み置き場。巨大ファイルはGit管理外。

| パス | 内容 |
|---|---|
| `weights/checkpoint.pth` | 公式NDformer checkpoint |

取得元（公式README）:

- URL: `https://github.com/yuzhTHU/ND2/releases/download/checkpoint.pth/checkpoint.pth`
- 論文資産: Zenodo `10.5281/zenodo.16995963`

Phase 0が未取得なら同じURLからダウンロードする。checksumはrunの `phase0/preflight.json` に保存する。

## Checkpoint identity

| field | value |
|---|---|
| path | `assets/nd2/weights/checkpoint.pth` |
| size | 81,136,260 bytes |
| SHA256 | `619d419b449a309c97d5b9ab6b8c9f53c91b45a409a3a9bf5b6ac79cb4f625d4` |

Recorded 2026-09-09 by the GPU_RUNclaude1 autonomous track (cycle C0001, Stage 3), closing the
provenance gap noted in `GPU_RUNclaude1/research_state.md` §8 item 2: ODEFormer and NeSymReS both had
pinned hashes while ND2 had none. The hash was computed from the file already on disk; it is an
identity record for the artifact in use, **not** an independent verification against an upstream
published checksum. If an official checksum is located, compare and record the result here.
