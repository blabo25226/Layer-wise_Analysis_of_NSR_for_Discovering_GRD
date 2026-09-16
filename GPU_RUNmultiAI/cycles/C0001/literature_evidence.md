# C0001 文献・一次ソース根拠

- cycle: C0001
- task: C0001-T004
- 作成日: 2026-09-12
- 状態: draft（凍結前）

本書は C0001 の H0001 監査と競合仮説に関連する文献・一次ソースを整理する。
**PI が検証済み** の primary source はその旨を明記する。
未検証の二次情報は「未検証」とラベルし、数値や結論の根拠に使わない。

## 検証ステータス凡例

| ラベル | 意味 |
|---|---|
| **PI 検証済み** | 本サイクルの PI が原典 URL／DOI を確認済み |
| **リポジトリ直読** | 本ワークツリー内の実行用コピー／ソースを直接確認 |
| **未検証** | 本ワークツリーでは原典を再確認していない |

---

## 1. ODEFormer（推論リスケーリング）

| 項目 | 内容 |
|---|---|
| ステータス | **PI 検証済み** |
| 原典 | d'Ascoli, S. et al. "ODEFormer: Symbolic Regression of Dynamical Systems with Transformers." arXiv:2310.05573, 2023. |
| 公式実装 | https://github.com/sdascoli/odeformer |
| リポジトリ配置 | 実行用: `third_party/odeformer/`、checkpoint: `assets/odeformer/weights/odeformer.pt` |

### 本監査に関係する主張

1. **Transformer による動力学のシンボリック回帰**（論文要旨）— 背景として使用。
2. **入力スケーリング** — 論文・実装は時系列と状態のスケール正規化を前提とする。
   リポジトリ直読: `third_party/odeformer/odeformer/model/utils_wrapper.py` の `Scaler` が
   初期時刻の状態 $`x(t_0)`$ を `traj_scale` に使い、`rescale_function` で候補木を逆変換する。
3. **簡約** — `third_party/odeformer/odeformer/envs/simplifiers.py` の `simplify_tree` は
   sympy 往復＋4 桁丸め。論文の評価詳細より **実装の方が本監査では拘束力が高い**（リポジトリ直読）。

### 監査への含意

- ODEFormer 公式実装の rescaling は **推論時の必須前処理** として設計されている。
- GPU_RUN5 は `rescale: true` を固定（`configs/gpu_run5/base.yaml`）。
- リスケーリング後の式が評価指標の「構造同値」と整合しない場合、
  **モデル性能と指標性能の混同** が生じる（H0001 の根拠）。

---

## 2. Controllable Neural Symbolic Regression（構造制御 SR）

| 項目 | 内容 |
|---|---|
| ステータス | **PI 検証済み** |
| 原典 | Kamienny, P.-A. et al. "Controllable Neural Symbolic Regression." Proceedings of ICML 2023, PMLR 202:15972–16002, 2023. |

### 本監査に関係する主張

1. ニューラル SR では **構造制約・スケール・演算子集合** が生成分布を強く規定する。
2. 数値適合と **構造的同値** は別問題として扱う必要がある。

### 監査への含意

- H0008（真値非依存文法）の背景文献。
- H0001 とは独立だが、「数値は合うが構造指標が不一致」という設計上の緊張を
  文献上も予期される（直接の Hill 偽陰性の記述はない → 本リポジトリ固有仮説）。

---

## 3. Tree Edit Distance with Variables（TED / 構造距離）

| 項目 | 内容 |
|---|---|
| ステータス | **PI 検証済み** |
| 原典 | Akutsu, T., Fukagawa, D., Tanaka, K. "Tree Edit Distance with Variables and Its Application to Molecular Formula Identification." arXiv:2105.04802, 2021; 拡張版 ISAAC 2022, LIPIcs 228:6:1–6:16, DOI:10.4230/LIPIcs.ISAAC.2022.44. |
| リポジトリ実装 | `src/gpu_run4/ted.py`（`canonicalize_tree`, `system_ted`） |

### 本監査に関係する主張

1. 変数付き木の編集距離は **構造的類似** を測るが、係数の代数的同値を保証しない。
2. 正規化（符号・可換演算の整列等）は距離の安定化に必要。

### 監査への含意

- `canonicalize_tree`（`src/gpu_run4/ted.py:242-268`）は恒等畳み込みと数値丸めを行うが、
  **因数分解・共通因子括り出しは行わない**（リポジトリ直読）。
- `formula_metrics` は `skip_cas=True` 既定（`src/gpu_run5/evaluation.py:41`）のため、
  TED／canonical 不一致時に sympy CAS 救済が走らない（`src/gpu_run4/formulas.py:493-502`）。
- Akutsu 系の距離は **代数同値の代替ではない** — H0001 が supported の場合、
  TED 系 endpoint だけでは「生物学的に同じ Hill 式」を捉えられない可能性。

---

## 4. リポジトリ内一次ソース（文献ではないが拘束力あり）

| ソース | ステータス | 監査での用法 |
|---|---|---|
| `scientific_state.md` | リポジトリ直読 | 観測事実の正本 |
| `GPU_RUN5/README.md`, `GPU_RUN5_summary_report.md` | リポジトリ直読 | 公開結論のみ（sealed raw 非使用） |
| `configs/gpu_run5/base.yaml` | リポジトリ直読 | 固定 `rescale: true`, beam 設定 |
| `src/gpu_run5/grn.py` | リポジトリ直読 | 真値 Hill 形の生成規則 |
| `src/evaluation/gpu_run5_structure.py` | リポジトリ直読 | `hill_form`, exponent-aware skeleton |
| `GPU_RUN5/preregistration.json` | リポジトリ直読 | 一次 endpoint 名の参照（本サイクルは再凍結） |

---

## 5. 競合仮説と文献の対応

| 仮説 | 直接文献 | 根拠の強さ |
|---|---|---|
| H0001 メトリック偽陰性 | ODEFormer 実装 + TED 限界 + 本 repo ソース | **高**（実装連鎖が具体） |
| H0002 クリティカルトークン | ODEFormer（decode）+ GPU_RUN5 層解析 | 中（run 内証拠が主） |
| H0003 beam 多様性 | ODEFormer + GPU_RUN5 R4/R5 | 中 |
| H0004 多 IC | GPU_RUN5 P6（支持）+ 文献一般論 | 中 |
| H0005 構造重み損失 | Controllable NSR | 低（未実装） |
| H0006–H0007 層選択 | GPU_RUN5 層解析 | 中 |
| H0008 文法バイアス | Controllable NSR | 低〜中 |
| H0009 attention | ODEFormer | **未検証**（系統解析なし） |
| H0010 埋め込みドリフト | GPU_RUN5 forgetting 結果 | 中 |

---

## 6. 文献が支持しないこと（過大主張の防止）

- ODEFormer 論文・実装は、**本リポジトリの `hill_form` フラグとの整合** を保証しない。
- TED 文献は **有理式の代数同値判定** を提供しない。
- GPU_RUN5 の「exact ゼロ」は、文献だけから H0001 を confirm できない
  （sealed test 非アクセス + 監査未実行）。
- PI 探索的ペアチェックは **文献根拠ではない**（機構整合の手がかりに留める）。

---

## 7. 未検証・追加調査候補（本サイクル外）

| トピック | 理由 |
|---|---|
| NeSymReS / TPSR の rescaling 比較 | 本サイクルは ODEFormer 経路に限定 |
| sympy `parse_expr` バージョン差 | A1 仮定；監査でバージョン固定を記録 |
| Hill 関数の「標準形」生物学文献 | 評価設計の生物学的妥当性は別論点 |

## 8. 引用形式（凍結用）

本サイクルの preregistration およびレポートでは、少なくとも次を引用する。

1. d'Ascoli et al., arXiv:2310.05573 (ODEFormer).
2. Kamienny et al., ICML 2023, PMLR 202 (Controllable NSR).
3. Akutsu et al., arXiv:2105.04802 / LIPIcs ISAAC 2022 (TED with variables).
