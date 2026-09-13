# C0001 preregistration v3 independent closure review

- reviewed commit: `bcf6412d63bbc4a8191ff964af0af6c0ac8b26a9`
- reviewer role: independent methodological reviewer (Codex subagent fallback)
- review date: 2026-09-13
- verdict: **REVISE**
- firewall: PR #4、`GPU_RUNclaude1`、GPU_RUN5 historical sealed artifacts は未参照

## Reviewer routing note

Claude reviewer を read-only で二回起動したが、初回は15分超、scopeを縮めた再試行は5分超にわたり応答を返さなかったため、retry/fallback rule に従って中断した。どちらも中断時に wrapper は `Execution error` と同時に `exit_code=0` を表示した。この exit code は成功証拠として扱わない。科学的 closure は独立 Codex subagent reviewer へ fallback した。

## Independently confirmed

- 240 systems = 8 families × 3 exponents × 10 draws
- 510 components = (1+1+2+2+2+3+3+3) × 30
- strict-Hill = 11 × 30 = 330 components、primary = 330 × 4 = 1,320 pairs
- linear = 4 × 30 = 120 components
- v3表の算術自体は `840 + 14,280 + 2,550 + 4,080 + 1,020 + 600 = 23,370`
- 23,370 の95%を整数に切り上げた22,202は算術的には正しい

## Blocking findings

### R3-1 — five-way outcome partition が exhaustive ではない

v3 §2.2、§3.5。`E1 oracle 非同値` かつ `E2 oracle 非同値` で、parse・timeout・NaN・`rescale_incomplete` のない正常終了ケースが5分類のどれにも入らない。正常な意味的不一致を `execution_failure` / `construction_incomplete` に入れることも、それらの定義と矛盾する。

**Required:** stage precedence を備えた完全な真理値表をfreezeする。5分類を維持するなら `semantic_drift = E1非同値 OR E2非同値` とし、`structural_false_negative` を E1/E2 ともに同値の場合だけに限定する。別々に帰属するなら6分類以上へ変更する。

### R3-2 — 95% primitive completion では固定分母の0件判定ができない

v3 §1、§2.2、§10。primitive総完了率は primary 1,320 pairs のcoverageではない。controls等で閾値を満たしつつ、一部primary pairの判定が欠け得る。

**Required:** 1,320すべての一意primary pairが exactly one terminal outcome を持つことを primary decision の必須条件にする。未確定pairが1件でもあれば支持/非支持を判定しない。primitive completion は運用指標へ格下げする。

### R3-3 — B0=510 components と rewrite registration=330 components が接続されない

v3 §3.2、§6、§8.3。非自同値rewriteはstrict-Hill 330 componentsだけに付与される一方、B0とcall tableは510 componentsすべてをrewrite E0から処理する。残る180 componentsのE0源が未定義である。

**Required:** 510 componentsすべてのE0 sourceをfreezeする。全510をrewriteするならP2を510へ変更して再計算する。330だけなら残り180のtruth-based E0等を明記し、IDにsourceを含める。

## Major findings

### R3-4 — D1がB0と重複しresource ceilingが曖昧

B0は既にnon-strict 60 components × 4 scalesを含むが、D1が同じ対象を追加logical callsとして数える。D1をB0結果の0-call集計にするか、B0から除いて予算を再導出する。23,370がconfirmatory-only ceilingか全実行ceilingかを明記する。

### R3-5 — `.4f` audit corpus は現行 `grn.py` の `.4g` 生成と一致しない

`src/gpu_run5/grn.py` は定数を `.4g` で出力する。現行表現を監査するならlexical tokenをexact `Rational(token_string)`として読み、production simplifier以外で再量子化しない。独立`.4f` corpusならGPU_RUN5 corpusと別物と明記し、変換前後token/valueを保存する。

### R3-6 — secondary 60 components はすべてmodulated flagではない

R07 component 3の30件は`modulated_hill_form=true`だが、R08 component 3の30件は現行classifierで同flagがfalseとなる。60をnon-strict Hill-bearingへ改称し、R07 modulated 30 / R08 product-base 30へ分ける。

### R3-7 — sealed guardがpath existenceとforbidden accessを混同する

glob matchの存在だけをG4 violationにしてはならない。existence inventoryは情報記録に留め、access auditまたはfilesystem isolationで禁止open/stat/scandir試行が0件であることを検証する。禁止pathをテスト目的で実際に開かない。

### R3-8 — resume keyとprovenanceが不足

`(condition, pair_id)`は同一pairのE1/E2 oracleを区別できない。最低でも `(primitive, condition, stage, pair_id)` とする。`pair_id`にcorpus hash、system ID、component index、scale、rewrite IDを含める。manifestへplan/audit-script hash、全CLI、依存版、environment、ordered primitive tableを保存し、各pair rowにE0/E1/E2 raw prefixとemitted infixを持たせる。

### R3-9 — cross-reference誤り

v3のvalidity gates参照を§10へ、compute ceiling参照を§8.5へ修正し、全heading/cross-referenceを機械検査する。

## Closure conditions

freeze前に、完全なoutcome真理値表、1,320 primary pairsの100% terminal coverage、510 componentsのB0 E0 source、`.4g`/`.4f`監査境界、sealed access guard、resume一意keyを修正し、call tableを再導出する。現行23,370は表の算術としては整合するが、実行可能な固定予算としては未closeである。
