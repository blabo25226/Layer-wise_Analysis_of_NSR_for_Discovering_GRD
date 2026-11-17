# provenance note — `gpu_run3_full_20260817`

plan.md §7 は「run途中でsource commit、checkpoint、主configを変更しない」と定めている。
**本runではこれが完全には守られていない。** checkpointとconfigは終始固定されていたが、
解析コードがフェーズ間で変更された。結果が単一の凍結commitから得られたものと誤読されないよう、
何がいつ変わったかをここに記録する。

Phase 0の `preflight.json` はLANSR commitを
`20e2b621e007bc46d3e06e25bb01aecf4142770f` と記録しているが、これが正確なのは Phase 0〜3 だけである。

## 全フェーズを通じて不変だったもの

| 項目 | 値 |
|---|---|
| NDformer checkpoint SHA256 | `619d419b449a309c97d5b9ab6b8c9f53c91b45a409a3a9bf5b6ac79cb4f625d4` |
| vendored ND2 fingerprint | `2b6c1b825ab56123a09bf05963da522fa9e7be8e85888e455ca0544650de4c22` |
| `configs/gpu_run3/*.yaml` | run開始後は未変更 |
| 解析corpusの生成器 | run開始後は未変更 |
| シード | 101 / 202 / 303 |

## フェーズとcommitの対応

| phase | 実行時刻（ローカル） | 有効だったコードリビジョン |
|---|---|---|
| 0 preflight | 08-17 21:35 | `20e2b62` |
| 1 policy | 08-17 21:35 | `20e2b62` |
| 2 pipeline | 08-17 21:35-21:45 | `20e2b62` |
| 3 benchmark | 08-17 21:45 - 08-18 00:50 | `20e2b62`（モジュールはプロセス起動時に読み込み） |
| 4 probes | 08-18 00:50-00:51 | `662bee3`（inner-split probe ridge、恒等式畳み込みを追加） |
| 6 causal | 08-18 00:51-00:52 | `662bee3` |
| 7 selective FT | 08-18 00:52-01:09 | `662bee3` |
| 8 test | 08-18 01:09-01:52 | `662bee3` |
| 9 pretrain dist | 08-18 01:52-01:54 | `662bee3` |
| 5 decoderlens（再実行） | 08-18 10:2x | `b31d906`（貪欲rollout + TED timeout） |
| 構造メトリクス再計算 | 08-18 16:2x | `823e314`（否定の分配まで含む最終正規化） |

## run途中に行った4つの変更と、その理由

1. **`d0f1fd9` — probeのridgeを `analysis_train` の内側分割で選択。**
   512次元の活性に固定の小さいペナルティを使うと、hold-out R²が-1e13のオーダーになっていた。
   影響するのはPhase 4のみで、変更時点で未実行だった。

2. **`662bee3` / `c44386d` — 正規化が数値の恒等式を畳み込み、符号を正規化。**
   MCTSはBFGSで最適化した定数を返すため、正しい回復が
   `(7.7e-09 + omega0) + (0.99999997 * aggr(...))` の形で、Michaelis–Mentenでは
   真値 `aggr(...) - x` に対し `(-1*x) + aggr(...)` の形で出てくる。
   字面どおり比較すると、どちらも失敗として採点されていた。
   plan.md §11 は定数・可換性・**符号**の扱いを評価前に固定することを要求しているが、
   実装は符号を一切扱っていなかった。結果を見てから閾値を調整したのではなく、
   仕様の欠落を埋めた変更である。これらは Phase 2〜3 が書かれた **後** に行われた。

3. **Phase 5の貪欲rollout + TED timeout（`b31d906`）。**
   `encoder_ted_trajectory` はtop-1シンボルを1つ足すだけだったため、prefixにplaceholderが残り
   パースに失敗し、TEDが全件NaNだった。plan.md §5A が要求する
   「encoder層 → 最終formula TED」の軌跡が存在していなかったことになる。
   実際のrolloutを入れたところ第二の欠陥が露呈した。退化した30トークンのrollout式が
   sympyの `equals()` / `simplify()` を無限に近い計算へ落とし込み、Phase 5の実行を8時間以上停止させた。
   plan.md §16.1 はTED timeoutを要求しているが実装が無かった。両方を修正してPhase 5を最初から再実行した。
   元の出力は `phase5_before_rollout_fix/` に保存してある。

4. **`823e314` — 否定を加算に分配（`neg(a+b) → neg(a)+neg(b)`）。**
   延長予算のrunでHCRが真値を厳密に回復したが、
   `neg(add(y,z))` と `add(neg(y),neg(z))` の差だけで exact 0 / TED 9 と採点されていた。
   2番の符号正規化の積み残しである。この修正が無ければ、本キャンペーン最大の成功例が
   失敗として報告されていた。分配は加算に限定し、乗除には適用していない
   （`-(x*y)` と `(-x)*(-y)` は別物であるため）。
   これは結果が出た後に見つかった符号・恒等式の欠落として3件目にあたる。

## 不整合をどう封じ込めているか

`structural_metrics_recomputed.json` が、保存されたprefixから
**run内の全ての式** —— Phase 2、Phase 3、およびPhase 7・Phase 8内のfine-tuning後MCTSレコード ——
について exact / skeleton / symbolic equivalence / TED を単一の正規化で再導出している。
元の値は `*_as_recorded` として併置され、上書きはしていない。
報告される構造メトリクスはこの再計算パスの結果であり、レポートには両方の列を表示している。

正規化に依存しない数値指標（cross entropy、top-k、RMSE、R²、探索ノード数、実行時間）は
これらの変更の影響を受けない。

## これで免責されないこと

test splitはPhase 8で一度だけ評価され、その後に条件を追加したり再採点したりはしていない。
しかし、Phase 8の式レベル指標を報告するために使った正規化は、
Phase 3の結果を見た後に確定したものである。
完全に事前登録された構造メトリクスを求める読者は、
`*_as_recorded` 列を変更前の値、再正規化後の列を事後的な訂正として扱い、
その訂正が「結果」ではなく「仕様上の要求（§11）」によって正当化されたものであることに留意されたい。
