# LANSR 新GPU PC 環境構築 引き継ぎ

## 目的

新しく用意したUbuntu GPUデスクトップPC上で、LANSRリポジトリを実行できる環境を構築している。

ここまでで、

* Ubuntu導入
* NVIDIA GPU 2枚の認識
* NVIDIAドライバ設定
* SSH
* Tailscale
* Remote Desktop
* Python 3.10 Conda環境
* PyTorch + CUDA + 2GPU認識

まで完了した。

**これ以降、LANSR固有の依存関係インストール・テスト・GPU preflight・実行準備を進めてほしい。**

---

# 1. PC構成

新しいデスクトップPC。

## CPU

```text
Intel Core i7-8700
```

## RAM

```text
64 GB
```

## GPU

```text
GPU 0: NVIDIA GeForce RTX 2070
VRAM: 8 GB
Compute Capability: 7.5

GPU 1: NVIDIA GeForce GTX 1060 3GB
VRAM: 3 GB
Compute Capability: 6.1
```

## マザーボード

```text
ASUS PRIME H370-A
```

## ストレージ

M.2 NVMe SSD。

BIOSでは当初認識確認が難しかったが、一度M.2 SSDを挿し直した。
Ubuntu Installerでは、

```text
nvme0n1
```

として正常認識され、そのSSDへUbuntuをインストール済み。

---

# 2. OS

```text
Ubuntu Desktop 26.04 LTS
```

Ubuntu専用PCとしてインストール。

ディスク暗号化は行っていない。

PC名：

```text
blabo-gpu-pc
```

Ubuntuユーザー：

```text
blabo
```

---

# 3. NVIDIAドライバ

最初はUbuntuが推奨した595系ドライバを入れた。

しかし、

```text
RTX 2070
```

しか `nvidia-smi` に現れず、

```text
GTX 1060 3GB
```

が使えなかった。

`ubuntu-drivers devices` では、

RTX 2070:

```text
nvidia-driver-595-open
nvidia-driver-580
...
```

GTX 1060 3GB:

```text
nvidia-driver-580
nvidia-driver-580-server
```

のみだった。

そのためドライバを580系へ変更した。

現在：

```text
Driver Version: 580.173.02
```

`nvidia-smi` では2GPUとも正常認識。

```text
GPU 0: NVIDIA GeForce RTX 2070
GPU 1: NVIDIA GeForce GTX 1060 3GB
```

---

# 4. SSH

UbuntuにOpenSSH Serverを導入済み。

WindowsノートPCからSSH接続成功。

例：

```powershell
ssh blabo@<IP>
```

SSHでUbuntu側のCLIを通常通り操作可能。

---

# 5. Tailscale

WindowsノートPCには以前からTailscale導入済み。

新Ubuntu PCにもTailscaleを導入して、既存tailnetへ追加済み。

Ubuntu PCのTailscale IPv4：

```text
100.94.123.36
```

Tailscale経由でSSH可能。

今後はLAN IPよりTailscale IP / MagicDNSを優先してよい。

---

# 6. Remote Desktop

最初に `xrdp` を試したが、Ubuntu 26.04 + GNOMEとの相性問題でセッションが終了した。

その後、xrdpを停止。

```bash
sudo systemctl disable --now xrdp
```

Ubuntu標準の

```text
Settings
→ System
→ Remote Desktop
→ Remote Login
```

を使用。

3389番ポートで、

```text
gnome-remote-desktop
```

がLISTENしていることを確認済み。

```bash
sudo ss -ltnp | grep 3389
```

で、

```text
*:3389
gnome-remote-desktop
```

を確認。

Windowsから、

```powershell
Test-NetConnection 100.94.123.36 -Port 3389
```

結果：

```text
TcpTestSucceeded : True
```

Remote Loginのsystem credentialsが最初空だった。

```bash
sudo grdctl --system status
```

で、

```text
Username: (empty)
Password: (empty)
```

だったため、

```bash
sudo grdctl --system rdp set-credentials
```

でRDP用credentialsを設定。

その後Windows標準 `mstsc` からTailscale経由でRemote Desktop接続成功。

現在Remote Desktopセッションは閉じている。

---

# 7. LANSRリポジトリ

clone済み。

場所：

```text
~/Layer-wise_Analysis_of_NSR_for_Discovering_GRD
```

確認時：

```bash
git status --short
```

出力なし。

つまりclean。

```bash
git branch --show-current
```

結果：

```text
main
```

確認時のHEAD：

```text
88fa01f GPU_RUN2 coding 3
```

つまり、

```text
88fa01f (HEAD -> main, origin/main, origin/HEAD)
```

だった。

**作業開始時に必ず現在の `git status`, branch, commit を再確認すること。**

---

# 8. LANSRのPython要件

リポジトリはPython 3.10基準。

Hydra / NeSymReS互換性の都合でPython 3.12+を本実験用に使わない。

そのためMinicondaを導入済み。

Miniconda：

```text
conda 26.5.3
```

base環境はPython 3.14だが、LANSRには使用しない。

LANSR用Conda環境：

```text
lansr310
```

作成済み。

有効化：

```bash
conda activate lansr310
```

Python：

```text
Python 3.10.x
```

---

# 9. PyTorch / CUDA構築時に起きた問題

ここは重要。

## 最初の試行

`requirements/gpu.txt` は以下：

```text
# Install the CUDA build from the official PyTorch index first, for example:
# pip install torch==2.5.1 --index-url https://download.pytorch.org/whl/cu124
-r base.txt
```

つまりリポジトリ側は、

```text
PyTorch 2.5.1 + CUDA 12.4
```

を想定している。

最初にCondaから、

```bash
conda install pytorch==2.5.1 torchvision==0.20.1 torchaudio==2.5.1 pytorch-cuda=12.4 -c pytorch -c nvidia -y
```

を実行した。

しかしConda版PyTorchで、

```text
ImportError:
libtorch_cpu.so: undefined symbol: iJIT_NotifyEvent
```

が発生。

原因は、

```text
mkl 2025.0.0
```

とPyTorch 2.5.1との既知の非互換。

---

# 10. MKL修正時の注意

MKLを、

```text
2024.0.0
```

へ下げた。

ただし、

```bash
conda install -c conda-forge "mkl=2024.0.0"
```

を実行するとconda-forgeがPyTorchまでCPU版へ置換した。

その時は、

```text
pytorch 2.5.1 cpu_generic...
torch.version.cuda == None
CUDA available == False
```

になった。

つまり、

**conda-forge版PyTorchを使ってはいけない。**

---

# 11. 現在の正しいPyTorch構成

最終的に、PyTorchをCondaではなくPyPI + PyTorch CUDA indexからpipで導入した。

現在：

```text
torch         2.5.1+cu124
torchvision   0.20.1+cu124
torchaudio    2.5.1+cu124
```

確認：

```bash
python -c "import torch; print(torch.__version__); print(torch.version.cuda)"
```

結果：

```text
2.5.1+cu124
12.4
```

GPU確認：

```bash
python - <<'PY'
import torch

print("CUDA available:", torch.cuda.is_available())
print("GPU count:", torch.cuda.device_count())

for i in range(torch.cuda.device_count()):
    print(i, torch.cuda.get_device_name(i), torch.cuda.get_device_capability(i))
PY
```

結果：

```text
CUDA available: True
GPU count: 2
0 NVIDIA GeForce RTX 2070 (7, 5)
1 NVIDIA GeForce GTX 1060 3GB (6, 1)
```

したがって、

```text
Python 3.10
PyTorch 2.5.1
CUDA runtime 12.4
RTX 2070
GTX 1060 3GB
```

はPyTorchから正常認識済み。

---

# 12. 現在のMKLについて

MKLは、

```text
mkl 2024.0.0
```

へ変更済み。

これは `iJIT_NotifyEvent` エラー対策。

ただしconca-forgeを使った過程で一部BLAS/OpenBLAS等の依存関係が変更されている可能性がある。

現在PyTorch自体はpip版CUDA 12.4で正常import・CUDA認識できている。

LANSRの依存関係導入後に、

```bash
pip check
conda list
```

等で整合性を確認してほしい。

---

# 13. 現在地

ここまで完了。

```text
Ubuntu 26.04        OK
SSD                 OK
Wi-Fi               OK
SSH                 OK
Tailscale           OK
Remote Desktop      OK
NVIDIA driver 580   OK
RTX 2070            OK
GTX 1060 3GB        OK
Conda               OK
Python 3.10 env     OK
PyTorch 2.5.1       OK
CUDA 12.4 runtime   OK
PyTorch 2GPU認識    OK
```

**まだ行っていない：**

```text
LANSR requirementsインストール
third_party/nesymresインストール
dev requirements
LANSR test
checkpoint確認
GPU preflight
GPU_RUN2 smoke test
本実験
```

---

# 14. 次にやってほしいこと

まず現在状態を確認。

```bash
cd ~/Layer-wise_Analysis_of_NSR_for_Discovering_GRD

git status --short
git branch --show-current
git log -1 --oneline

conda activate lansr310

python --version

python -c "import torch; print(torch.__version__, torch.version.cuda, torch.cuda.is_available(), torch.cuda.device_count())"

nvidia-smi
```

その後、リポジトリのREADME、AGENTS.md、GPU_RUN2関連ファイルを読んでから進めること。

特にLANSRでは、AGENTS.mdの作業ルールを必ず守る。

---

# 15. 依存関係の次候補

現在考えている次の手順は、

```bash
pip install -r requirements/gpu.txt
pip install -e third_party/nesymres
pip install -r requirements/dev.txt
```

ただし、**実行前に必ず中身を確認すること。**

特に重要：

現在正常に動いている

```text
torch==2.5.1+cu124
```

を別のPyTorchへ上書きしないこと。

まず、

```bash
cat requirements/base.txt
cat requirements/gpu.txt
cat requirements/dev.txt
```

を読み、PyTorchを再インストールしないことを確認する。

依存関係導入後、

```bash
python -c "import torch; print(torch.__version__, torch.version.cuda, torch.cuda.is_available(), torch.cuda.device_count())"
```

を再度実行する。

---

# 16. GPU実計算確認

2GPU認識までは確認済み。

必要なら、まずこのsmoke testを行う。

```bash
python - <<'PY'
import torch

for i in range(torch.cuda.device_count()):
    device = f"cuda:{i}"
    x = torch.randn(1000, 1000, device=device)
    y = x @ x
    print(
        i,
        torch.cuda.get_device_name(i),
        y.device,
        y.mean().item(),
    )
PY
```

RTX 2070とGTX 1060の両方で成功することを確認する。

---

# 17. GPUの使い方に関する注意

GPUは、

```text
RTX 2070: 8GB
GTX 1060: 3GB
```

と性能・VRAM差が大きい。

2GPUだからといってVRAMが、

```text
8GB + 3GB = 11GB
```

になるわけではない。

LANSR本実験ではRTX 2070を主GPUにするのが妥当。

GTX 1060は、

* 小規模ジョブ
* 独立した別seed
* 軽い推論
* smoke test
* 他の補助処理

などに使う方がよい可能性がある。

DataParallel/DDPで無理に2枚を束ねる前に、既存コードがmulti-GPU前提か確認すること。

---

# 18. LANSRリポジトリ固有の重要事項

LANSRはNeSymReSを中心とした研究。

実行用NeSymReS：

```text
third_party/nesymres
```

設定/checkpoint：

```text
assets/nesymres/
```

調査用コード：

```text
GitHubSourceCode/
```

`GitHubSourceCode/` を実行依存として直接importしないこと。

GPU実験前はリポジトリにあるpreflightを利用する。

想定：

```bash
python scripts/ops/preflight_gpu.py \
  --weights <checkpoint> \
  --config assets/nesymres/jupyter/100M/config.yaml \
  --eq-setting assets/nesymres/jupyter/100M/eq_setting.json
```

checkpointの実ファイル位置はリポジトリを確認して特定すること。

以前の研究環境では `10M.ckpt` という名前でも、実際のstate dictはencoder/decoder各5層の100M設定側アーキテクチャだったため、

```text
assets/nesymres/jupyter/100M/config.yaml
```

との組み合わせが必要だった。

名前だけでcheckpoint architectureを判断しないこと。

---

# 19. テスト方針

依存関係を入れたらまず、

```bash
python -m compileall -q src scripts tests
```

その後、

```bash
python -m pytest -q
```

GPUを使う長時間計算をいきなり開始しない。

GPU preflight → smoke test → 小規模runの順に進める。

---

# 20. Git運用

現在clone直後はcleanだった。

既存のユーザー変更を消さないこと。

作業前後で必ず、

```bash
git status --short
```

を確認。

勝手に、

```text
git reset --hard
rebase
force push
```

などを行わないこと。

コード変更が必要な場合は、研究設計・README・GPU_RUN2・testsとの整合性も確認する。

---

# 21. 最終的な目標

このPCを、

```text
Tailscale
    ↓
SSH
    ↓
tmux
    ↓
LANSR GPU experiment
```

という研究用マシンとして運用したい。

GUIが必要なときだけ、

```text
Tailscale + GNOME Remote Login
```

を使う。

長時間GPU計算はRemote Desktopセッションではなく、

```text
SSH + tmux
```

等で実行し、SSH切断後も計算が続くようにする。

---

# Cursor / Codexへの依頼

以上の現在状態を前提として、

1. 現在のリポジトリと環境を実際に確認する。
2. AGENTS.md、README.md、GPU_RUN2関連ドキュメントを読む。
3. 現在正常な `torch 2.5.1+cu124` を壊さずLANSR依存関係を導入する。
4. 依存関係競合があれば原因を調査し、勝手にPyTorch/CUDAを変更しない。
5. compile/testを実行する。
6. NeSymReS checkpoint/configを確認する。
7. GPU preflightを実行する。
8. RTX 2070を主GPUとしてsmall/smoke runを行う。
9. 問題がなければGPU_RUN2の実行方法を提案する。
10. 長時間本実験を勝手に開始せず、その直前で設定・予想時間・使用GPUを報告する。

作業中は既存の研究結果・Git履歴・GPU_RUN1成果物を上書きしないこと。
