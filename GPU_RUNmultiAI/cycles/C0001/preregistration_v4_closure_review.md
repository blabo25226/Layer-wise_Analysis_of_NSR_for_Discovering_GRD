# C0001 preregistration v4 independent closure review

- reviewed commit: `5c67b8fb8fc4cccfa4963f82e6c12ac47a3705d6`
- reviewer: independent methodological Codex subagent
- verdict: **REVISE**
- firewall: PR #4、`GPU_RUNclaude1`、historical GPU_RUN5 sealed artifacts は未参照

## Closed findings

- R3-4: D1はB0の0-call集計となり、confirmatory/full-run ceilingも分離された。
- R3-6: non-strict 60 componentsはR07 modulated 30とR08 product-base 30に分割された。
- R3-9: 節番号、audit ID、見出しは整合した。
- 算術: confirmatory `23,550`、D2 `2,310`、full-run maximum `25,860` は正しい。

## Remaining findings

### V4-1 — 仮説本文とterminal outcomeが同じ事象を定義していない

仮説本文はE2同値のみを要求するが、`structural_false_negative` はE1/E2両同値を要求する。E1 parse失敗の分類も明示されない。

### V4-2 — terminal coverageだけではabsenceを結論できない

`execution_failure`等もterminalであるため、1,320件がすべて失敗でも偽陰性0件としてunsupportedになり得る。存在を1件観測した場合と、存在しないと結論する場合で必要なdiagnostic coverageを区別する必要がある。

### V4-3 — rewriteが操作的に未定義

「非零有理数倍r」は同値変換の構文テンプレートではない。単なる`r*E`なら非同値である。prefix結合順、rの有限集合、seed割当、E0前の簡約禁止をfreezeする必要がある。

### V4-4 — exact parsingとclassifier再量子化の境界が未閉鎖

`Rational(token_string)`はtruthにしか明記されず、E0/E1/E2のnumeric leaf規則がない。現行`classify_formula(E2_infix)`は`parse_system`で4 significant digitsへ量子化するため、「simplifier以外で再量子化しない」と矛盾する。

### V4-5 — sealed guardの禁止パターンが一意でない

path existenceとaccessは分離されたが、configから導く具体的normalized patterns、relative/symlink処理、対象APIが不足する。

### V4-6 — resume provenance照合が不足

resume時に全CLI、全timeout、dependency versions、environmentも一致させる必要がある。B1/B4の`rewrite_id`表現も未定義である。

### V4-7 — formula_metrics API表記が不正確

現行signatureは`formula_metrics(true_infix, predicted_infix)`であるため、`formula_metrics(skip_cas=True)`ではなく、関数内部で`skip_cas=True`を固定することを記す。

### V4-8 — oracle健全性gate不足

予算に含めたN1全100件の非同値検出と、B4全510件のvalid/canonical self-matchを明示的なvalidity gateにする。

## Required closure

V4-1〜V4-8を修正し、仮説・分類・decision rule・実装契約が同じ対象事象を一意に記述すること。call ceilingの算術は変更がなければ維持できる。
