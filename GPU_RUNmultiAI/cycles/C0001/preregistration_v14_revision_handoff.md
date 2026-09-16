# C0001-T013 v14 revision handoff

## Objective

Create self-contained `preregistration_draft_v14.md` and close R13-1 through
R13-6 from `preregistration_v13_independent_review.md`. Preserve v9-v13 bytes.

## Isolation and scope

- worker: Cursor repo-operator / scientific document implementer
- worktree: `/tmp/lansr-multiai-C0001-implement-audit`
- branch: `ai/C0001/research-engineer/implement-metric-audit`
- write: v14 plan, v13 response, v14 completion, durable state
- prohibited: historical plan edits, scientific code/tests, smoke/full audit,
  freeze claim, GPU_RUN5 results, untracked v9 smoke directory

## Required changes

1. Keep C_q4 at seven calls. Make fixture 03 input
   `add,add,x_0,x_1,x_2` with output `add,x_0,add,x_1,x_2`; fixture 04 input
   `mul,mul,2,x_0,x_1` with output `mul,2,mul,x_0,x_1`. Retain compound pow2
   as fixture 05, decimal Float as 06, and make Rational fixture 07 input
   `mul,div,1,3,x_0` with complete expected output
   `mul,mul,1,pow,3,-1,x_0`. Gate all seven at G_q4ref.
2. Inline exact `write_infix` rendering for add/sub/mul/div/pow/abs/id/inv/
   pow2/pow3 and the remaining unary production operators. Require empty
   remainder after recursive parse. Define leaf and unknown-token behavior.
3. Any Q4-emitted operator or prefix that cannot be reparsed by the frozen Q4
   dialect causes global `Q4ContractError` abort before pair outcome reuse.
4. Freeze parent/child guard bootstrap before non-bootstrap imports, config/plan/
   corpus reads, output-dir access, ODEFormer loading, and task code. Explicitly
   list the minimal standard-library/guard bootstrap allowed before install.
5. Freeze a sorted path-inventory algorithm, not current broken implementation
   hashes. Cover all `src/gpu_runmultiai/*.py`; shared
   `experiment_runtime.py`, `gpu_run2_runtime.py`, `gpu_run3_runtime.py`,
   `gpu_run4_runtime.py`; named gpu_run4/gpu_run5/evaluation files; and recursive
   `third_party/odeformer/**/*.py` including top-level `parsers.py`.
6. State that accepted per-file hashes and implementation commit are bound only
   after post-freeze implementation closure PASS. Full audit/resume must match
   that record exactly. Current hashes are non-normative and may be omitted.
7. Enumerate exact row schemas for every artifact used by a predicate/gate,
   including registration, B3, B4, N1, C_q4, reachability, oracle, summary,
   guard, deviation, and abort. Add all predicate flags to their durable rows.
8. Freeze JSONL recovery: UTF-8 bytes; newline-terminated canonical JSON;
   append then flush+`os.fsync`; on resume truncate an incomplete final byte
   suffix to the last newline and fsync before parsing; malformed complete line
   or duplicate key aborts. Never merely ignore a partial suffix and append.
9. Define manifest states `initializing`, `running`, `completed`, `aborted` and
   atomic replacement. Every global abort writes `abort_manifest.json` with
   reason/type, UTC time, elapsed, bytes, call counts, and last durable keys.
   Define `deviation_log.md` creation before run and append/finalize behavior.
10. Resume re-reads/byte-compares payload JSON and bytes file, regenerates corpus
    and compares hash/payload, and includes Python, NumPy, SciPy, SymPy,
    scikit-learn, numexpr, torch plus OS/CPU and frozen env.
11. Add pre-full-audit `G_contract` acceptance for Q4, early guard install and
    side channel, complete source inventory, artifact schemas, crash recovery,
    resume mismatches, and abort/deviation lifecycle. Keep G_impl exactly the
    prior seven requirements.
12. Apply all required same-pass cleanup from the review. No historical
    normative cross-reference and no “same as production” shortcut.

## Stable quantities

- C_q4: 7 counted calls
- confirmatory: 27,637
- D2: 2,640
- grand: 30,277
- wall: 18,000 monotonic seconds
- disk: 1,200,000,000 decimal bytes
- GPU/decode: zero

## Commit and push protocol

Use exactly two commits at most:

1. content commit: v14, v13 response, and state;
2. optional completion commit: completion file records the content commit and
   verification that the content commit was pushed. It must not claim its own
   SHA or update state to chase the new tip.

Push once after each used commit. Stop after the optional completion push.
The PI will record the final remote tip in the subsequent review artifact.

## Acceptance

- audit ID `c0001_metric_identifiability_audit_v14` only;
- v9-v13 hashes unchanged;
- R13-1 through R13-6 mapped to exact v14 sections;
- seven Q4 fixtures and 27,637/2,640/30,277 reconcile;
- document consistency searches and `git diff --check` PASS;
- local/tracking/remote parity verified after the final push;
- v14 remains unfrozen pending independent review.
