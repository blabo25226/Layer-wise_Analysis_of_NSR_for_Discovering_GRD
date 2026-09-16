# C0001 preregistration v14 targeted independent closure review

- task: `C0001-T013-REVIEW`
- reviewed tip: `a296ffd67cff8ea71530ee234e9d04581f79b9f1`
- reviewed plan SHA256: `0650d7a5e2af666c2036ee96a8b5137e9d325aac3ac70d076244ac2f1f74968c`
- reviewers: Codex independent subagent; Codex PI
- Claude status: read-only call returned no review body before bounded stop
- verdict: **BLOCK_AND_REVISE_TO_V15**
- freeze/full audit: **PROHIBITED**

## Verified PASS

- Local, tracking, and remote tips matched at the reviewed SHA.
- Historical v9-v13 SHA256 values remained unchanged.
- Source inventory deterministically reproduced 81 paths and now covers the
  previously omitted shared and vendored runtime sources.
- Per-file hashes are correctly deferred until accepted post-freeze
  implementation closure.
- Call arithmetic remains 27,637 confirmatory + 2,640 D2 = 30,277.
- §6.1 contains executable seven-fixture prefix inputs and correct full emitted
  prefixes, including the Rational fixture.
- G_contract, JSONL truncate+fsync direction, resume dependency expansion, and
  global Q4 abort direction are acceptable.

## Blocking findings

### R14-1 — P0: duplicate n-ary expectations contradict the executable fixtures

The frozen fold emits `add,x_0,add,x_1,x_2` and
`mul,2,mul,x_0,x_1`. §6.1 uses those correct outputs, but §3.4.6 and §3.4.9
retain stale `add,add,...` / `mul,mul,...` expected outputs. Every normative
occurrence must use the right-nested production order and be gated consistently.

### R14-2 — P0: leaf and unknown-token rules are mutually contradictory

The recursive parser accepts any nonnumeric token as a leaf, then a later rule
rejects every token absent from the operator tables, which includes `x_0`.
Freeze production-compatible leaf behavior: a token is parsed as an operator
only when it is in the arity table; otherwise it is a leaf string. Unknown
**emitted operator-shaped nodes** are detected because their following tokens
remain unconsumed and the mandatory empty-remainder check aborts. Optionally add
an emitted-leaf allowlist, but do not reject valid variables.

### R14-3 — P0: guard bootstrap cannot be constructed under its own rules

The plan calls `SealedPathGuard.install()` without constructing an instance or
obtaining `output_root_abs`, while it forbids the imports and reads currently
needed to do so. Importing `gpu_runmultiai.sealed_guard` also executes package
initialization and `experiment_runtime` dependencies.

Freeze a new dependency-free bootstrap module as a post-freeze implementation
requirement. It may import only stdlib, derive repo root from the entry script,
construct the matcher from the literal `repo_root/results/runs`, install it,
then import the package/runtime. Child startup follows the same sequence. Add a
G_contract test that package/runtime imports do not occur before installation.

### R14-4 — P1: exact artifact schemas remain incomplete

- `q4_reference_controls.json` must persist `terminal_outcome`.
- `equivalence_oracle.json` must include B1 E1/E2 oracle rows, not only B0+D2.
- `deviation_log.md` needs an exact entry schema, not only lifecycle prose.

### R14-5 — P1: required cleanup and normative shortcuts remain

Repair stale section references, replace 1-based “component 3” wording with
zero-based `component_idx=2`, and inline the remaining rescale/serialization
rules currently described as “same as production.”

## Gate decision

Produce v15 with only R14-1 through R14-5 changes and re-review those sections.
No implementation, freeze, smoke, or full audit is authorized before PASS.
