# C0001 preregistration v8 independent closure review

- reviewed commit: `47e92e7fe48ad7b83b9b9911fefc938d105fcdd0`
- reviewer: independent methodological Codex subagent
- verdict: **REVISE**
- firewall: PR #4、`GPU_RUNclaude1`、historical GPU_RUN5 sealed artifacts は未参照

## Closed

v7のgenerator引数、source index写像、rewrite/N1 key、typed unit ID設計は閉じた。decision、outcome partition、oracle、whole-chain、controls、guard、resume、`23,550`/`25,860` arithmeticも維持された。

## Required corrections

1. component/pair fixtureの表示keyは値のみだが、expected SHAはfield label込みbytesのSHAである。canonical bytesとfixtureを同一方式へ統一する。
2. canonical separatorをraw Markdown table内の`\|`で示さず、表外code fenceへexact bytesを置く。separatorはASCII `0x7c` 1 byte、backslashは0 bytesと明示する。
3. D2 descriptive scale `5.0`をpair scale tokenとして許可し、typed call log/resumeへ接続する。
4. fingerprint bytesはsourceと同じ `json.dumps(payload, sort_keys=True).encode()` の既定値までfreezeし、SHAが`corpus["fingerprint"]`と一致することをassertする。
5. validity gate評価順を`G_corpus`から開始する。
