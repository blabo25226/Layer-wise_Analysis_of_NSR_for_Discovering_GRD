# assets/nesymres/

NeSymReS実行用の設定とcheckpoint置き場。

| パス | 内容 | Git |
|---|---|---|
| `jupyter/100M/config.yaml` | モデル設定 | 追跡 |
| `jupyter/100M/eq_setting.json` | 語彙・演算子設定 | 追跡 |
| `weights/*.ckpt` | checkpoint | 管理外 |

既定パス（環境変数未設定時）:

```text
assets/nesymres/weights/100M.ckpt
assets/nesymres/jupyter/100M/config.yaml
assets/nesymres/jupyter/100M/eq_setting.json
```

調査用クローンからローカルへcheckpointを用意するときは:

```powershell
powershell -File scripts/ops/setup_phase0_links.ps1
```
