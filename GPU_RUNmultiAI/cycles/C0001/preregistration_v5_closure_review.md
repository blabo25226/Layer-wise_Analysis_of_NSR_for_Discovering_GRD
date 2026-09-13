# C0001 preregistration v5 independent closure review

- reviewed commit: `cee3bea5d5f4ed1b1051f6d6093e9731993b8e6d`
- reviewer: independent methodological Codex subagent
- verdict: **REVISE**
- firewall: PR #4、`GPU_RUNclaude1`、historical GPU_RUN5 sealed artifacts は未参照

## Closed

- 仮説本文はE1/E2両同値条件へ揃った。
- 非支持判定は全1,320件のdiagnostic coverageを要求する。
- rewrite prefix `div,mul,r,E,r` は `(r E)/r` を表す。
- `formula_metrics` API、B4 gate、call arithmeticは整合した。
- confirmatory `23,550`、D2 `2,310`、grand maximum `25,860` は正しい。

## Required revisions

1. **Decision precedence:** false negativeとsemantic driftが共存するとsupportedとundecidableが重複する。gate/terminal不成立→undecidable、FN≥1→supported、FN=0かつ全件diagnostic→unsupported、その他→undecidableの順序をfreezeする。
2. **Oracle tri-state:** 正常完了した非同値を`execution_failure`へ入れない。`completed=true/equivalent=false`はB0の`semantic_drift`、N1の正常reject。parse/timeout/nonfinite/exceptionだけ`completed=false`→`execution_failure`。analytic/numericの一方でもfalseならcompleted non-equivalentとする。
3. **Rewrite digest:** canonical keyのpipeにbackslashを含めない。indexはzero-based・無padding、UTF-8 bytesをfreezeし、digest例と`rewrite_id`算出対象を明記する。
4. **Classifier scope:** 現行classifierはnormalized infixを返さない。primary claimをwhole-chainに限定し、pre/post保存だけで因果的stage attributionを主張しない。帰属をするなら別readoutを予算化する。
5. **Deny matcher:** absolute pattern表記へ統一し、禁止directory自身と全子孫をcomponent-based matcherでblockする。全child processへguardを継承する。
6. **Resume:** 初回とresumeで比較対象semantic CLI/effective configを一致させる。resume commandに全semantic引数を再掲するかresolved config比較をfreezeする。
7. **N1:** 100 componentsの選択key、順序、非同値template、係数domain、IDをfreezeする。
8. **Linear controls:** 480/480のparse-valid・metric-valid coverageをgateへ追加し、failureを分母から除外しない。

## Closure condition

上記8項目を一意な実装契約として修正後、再度独立closure reviewを行う。
