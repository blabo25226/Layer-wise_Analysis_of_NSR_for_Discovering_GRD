# C0001 preregistration v7 independent closure review

- reviewed commit: `fa270251c48835518634056fdfc7acdc1e048d4b`
- reviewer: independent methodological Codex subagent
- verdict: **REVISE**
- firewall: PR #4、`GPU_RUNclaude1`、historical GPU_RUN5 sealed artifacts は未参照

## Closed

v6の5指摘（deep phase8 deny、pair fixture、環境変数とresume command、numeric tolerance/finite規則、固定1,320分母）はすべて局所的に閉じた。decision、whole-chain、rewrite、N1/B4/linear gates、`23,550`/`25,860` arithmeticも維持された。

## Required corrections

### V7-1 — 凍結corpusを一意に再生成できない

`generate_corpus`の`variants`, `n_points`, `t_span`, `seed`, `trajectory_seed`, `rtol`, `atol`, `minimum_variance`, `maximum_abs_state`、使用splitをすべてfreezeする。`corpus_hash`が返却`fingerprint`かfile bytes SHAかも明示する。

### V7-2 — source index、canonical system ID、N1 IDが不整合

source `variant_index`は採択順0–29で、指数tierは`variant_index % 3`、drawは`variant_index // 3`である。canonical IDはsource recordの`system_id`を用いるか、これと一対一の定義にする。N1 keyへcanonical system IDを含め、510 componentsでdigest/negative IDが一意になるようにする。

### V7-3 — 全counted callにpair_idを要求してregistration/N1が表現不能

typed `unit_id`を導入する。registrationはcomponent ID、pair段はpair ID、N1はnegative IDを用い、call log/resume key/duplicate規則を`(primitive, condition, stage, unit_type, unit_id)`で統一する。
