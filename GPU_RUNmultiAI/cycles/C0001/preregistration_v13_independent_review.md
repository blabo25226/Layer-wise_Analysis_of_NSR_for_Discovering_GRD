# C0001 preregistration v13 targeted independent closure review

- task: `C0001-T012-REVIEW`
- reviewed tip: `ad4dc017c9ed8e11342f0e958c682c26cf362b75`
- reviewed plan SHA256: `c70502e194cac0420a5724b8ca7608ab92006aaad9f8c19faccf0d412447a962`
- reviewers: Claude Code read-only critic; Codex independent subagent; Codex PI
- verdict: **BLOCK_AND_REVISE_TO_V14**
- freeze/full audit: **PROHIBITED**

## Independently verified

- Local HEAD, tracking ref, and remote ref matched at the reviewed tip.
- Historical v9-v12 hashes remained unchanged.
- v13 arithmetic reconciled at confirmatory 27,637, D2 2,640, grand 30,277.
- Production-Q4 and audit-oracle `pow4` tables are separated correctly.
- The zero-based truth-side index sets, pointwise finite/tolerance oracle,
  row predicates, canonical scale tokens, and confirmatory-only G1 direction
  are substantially correct.
- Missing post-freeze reachability evidence is non-blocking by PI decision.

## Blocking findings

### R13-1 — P0: Q4 fixtures contradict their input API and frozen n-ary fold

`audit_q4_decimal_round_reference` accepts E1 prefix, but `q4_fixture_07` supplies
infix `(1/3)*x_0`. Its expected `mul,1,pow,3,-1` is only the Rational atom
serialization, not the whole expression. A valid prefix input is
`mul,div,1,3,x_0`; after SymPy evaluation and the production fold, the complete
expected prefix is `mul,mul,1,pow,3,-1,x_0`.

The frozen production fold appends `op`, child 0, `op`, child 1, child 2 for a
three-argument node. Therefore the correct fixtures are
`add,x_0,add,x_1,x_2` and `mul,2,mul,x_0,x_1`, not the left-nested expectations
in v13. The n-ary fixture is also disconnected from an acceptance gate.

Keep seven counted C_q4 calls by replacing the weak binary construction
fixtures with three-argument Add and Mul prefix fixtures. Counts remain
27,637/2,640/30,277.

### R13-2 — P0: prefix-to-infix and Q4 failure behavior are not self-contained

The plan gives arity and recursion but omits exact token-to-infix rendering.
Inline the production `write_infix` mapping for every frozen token, the full
residual-token check, leaf behavior, and unknown-token behavior. Remove the
normative “same as production” shorthand.

The review response says an unreparseable Q4 emitted operator aborts, while v13
continues with a per-row execution failure. The PI adopts **global abort before
pair outcome reuse** because such an emission means the frozen Q4 dialect is
violated, not an ordinary model failure.

### R13-3 — P0: guard installation occurs after task initialization

The parent contract only requires installation before corpus/counting, and the
current entry path imports audit/runtime and performs output/runtime work first.
Freeze a minimal bootstrap: after standard-library and guard-bootstrap imports,
install the guard before importing audit/runtime modules, reading plan/config or
corpus, creating/reading output artifacts, loading ODEFormer, or executing any
task code. Apply the analogous rule to every child. Enumerate the only allowed
pre-install bootstrap operations.

### R13-4 — P1: source-hash contract is incomplete and blocks required implementation

The “recursive” inventory omits directly and transitively imported sources,
including `src/experiment_runtime.py`, `src/gpu_run2_runtime.py`,
`src/gpu_run3_runtime.py`, `src/gpu_run4_runtime.py`,
`src/gpu_run5/config.py`, `third_party/odeformer/parsers.py`, and ODEFormer
modules loaded by `FunctionEnvironment`.

More importantly, v13 freezes hashes of the known-broken pre-F1/F2 runtime and
says any change aborts. That makes the mandatory post-freeze implementation
logically impossible. Freeze the **path inventory and inventory algorithm** in
the preregistration. After F1/F2/F4-F8 and all protocol-contract acceptance
checks PASS, pin the accepted implementation commit and computed per-file
hashes in an implementation closure record and run manifest. Full audit and
resume must require exact equality to that accepted hash set.

Use a deterministic sorted recursive inventory over all
`src/gpu_runmultiai/*.py`, the named shared `src` runtime files, and all vendored
ODEFormer Python sources reachable by the audit, including top-level
`third_party/odeformer/parsers.py`. Current content hashes may be retained only
as explicitly non-normative observations.

### R13-5 — P1: artifact, durability, and resume contracts remain incomplete

- Row predicates reference fields absent from durable schemas. Enumerate schemas
  for B3, B4, N1, C_q4, registration, reachability, summary, oracle, and abort
  artifacts, not only filenames.
- `pair_results.csv` must include `construction_incomplete` and all direct flags
  used by applicable predicates; remove or define duplicate `stratum` fields.
- Append plus “ignore trailing partial line” is not recoverable: later appends
  turn it into a malformed middle line. Before resume, truncate to the last
  newline and fsync; any malformed complete line aborts. Every appended line
  must flush and `os.fsync` unconditionally.
- `abort_manifest.json` must cover every global abort and identify the last
  durable call/cache boundary. Define manifest and `deviation_log.md` lifecycle.
- Resume must re-read and byte-compare the verbatim fingerprint payload and
  exact bytes, regenerate/compare the corpus, and include scikit-learn,
  numexpr, and all runtime dependencies in addition to the existing fields.

### R13-6 — P1: implementation acceptance does not cover the new protocol contracts

G_impl correctly retained the seven historical repairs, but the v13 additions
can remain unimplemented while G_impl passes. Add a separate pre-full-audit
`G_contract` gate for Q4 fixtures, guard bootstrap/side-channel, complete source
inventory capture, artifact schemas, JSONL crash recovery, resume mismatch
tests, and abort/deviation lifecycle. Keep G_impl naming exactly
F1/F2/F4/F5/F6/F7/F8 to preserve the earlier conflict resolution.

## Required same-pass cleanup

- Fix orphaned scale-predicate table rows and zero-based component wording.
- Repair stale section references.
- Make object identity mandatory, not recommended.
- Remove or define `neg` consistently with the frozen production dialect.
- Use `formula_metrics_valid` consistently in G_b4.
- Treat the multiple completion-only commits after `9ebb775` as non-scientific
  metadata churn. Do not repeat it in v14.

## Gate decision

Produce v14 and re-review R13-1 through R13-6. Do not freeze, edit scientific
implementation, run smoke, or run the full audit before a PASS closure review.
