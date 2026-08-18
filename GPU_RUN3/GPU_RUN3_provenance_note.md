# Provenance note — `gpu_run3_full_20260817`

plan.md section 7 says source commit, checkpoint and main config must not change
during a run. **That was not fully honoured here.** The checkpoint and configs were
fixed throughout, but analysis code changed between phases, and this note records
exactly what changed and when so results are not read as coming from one frozen
commit.

Phase 0's `preflight.json` records the LANSR commit as
`20e2b621e007bc46d3e06e25bb01aecf4142770f`. That is accurate for Phases 0-3 only.

## What was constant across every phase

| item | value |
|---|---|
| NDformer checkpoint SHA256 | `619d419b449a309c97d5b9ab6b8c9f53c91b45a409a3a9bf5b6ac79cb4f625d4` |
| vendored ND2 fingerprint | `2b6c1b825ab56123a09bf05963da522fa9e7be8e85888e455ca0544650de4c22` |
| `configs/gpu_run3/*.yaml` | unchanged after the run started |
| analysis corpus generator | unchanged after the run started |
| seeds | 101 / 202 / 303 |

## Phase to commit mapping

| phase | ran (local) | code revision in effect |
|---|---|---|
| 0 preflight | 08-17 21:35 | `20e2b62` |
| 1 policy | 08-17 21:35 | `20e2b62` |
| 2 pipeline | 08-17 21:35-21:45 | `20e2b62` |
| 3 benchmark | 08-17 21:45 - 08-18 00:50 | `20e2b62` (module state loaded at process start) |
| 4 probes | 08-18 00:50-00:51 | `662bee3` (adds inner-split probe ridge, identity folding) |
| 6 causal | 08-18 00:51-00:52 | `662bee3` |
| 7 selective FT | 08-18 00:52-01:09 | `662bee3` |
| 8 test | 08-18 01:09-01:52 | `662bee3` |
| 9 pretrain dist | 08-18 01:52-01:54 | `662bee3` |
| 5 decoderlens (re-run) | 08-18 02:0x | `c44386d` + TED timeout |

## The three changes, and why they were made mid-run

1. **`d0f1fd9` — probe ridge selected on an inner split of `analysis_train`.**
   A fixed small penalty on 512-dimensional activations gave held-out R2 of order
   -1e13. Affects Phase 4 only, which had not yet run.

2. **`662bee3` / `c44386d` — canonicalization folds numeric identities and
   normalizes signs.** MCTS returns BFGS-fitted constants, so a correct recovery
   arrives as `(7.7e-09 + omega0) + (0.99999997 * aggr(...))` and, for
   Michaelis-Menten, as `(-1*x) + aggr(...)` against a ground truth of
   `aggr(...) - x`. Compared literally both scored as misses. plan.md section 11
   requires the treatment of constants, commutativity and **signs** to be fixed
   before evaluation; the implementation never handled signs, so this closes a gap
   in the spec rather than tuning a threshold after seeing results.
   These changes were made **after** Phases 2-3 had been written.

3. **Phase 5 greedy rollout + TED timeout.** `encoder_ted_trajectory` appended only
   the top-1 next symbol, leaving placeholders in the prefix, so it never parsed and
   every TED was NaN — the `encoder layer -> final formula TED` trajectory of
   plan.md section 5A did not exist. Adding a real rollout then exposed a second
   defect: a degenerate 30-token rollout formula sent sympy's `equals()`/`simplify()`
   into an unbounded computation that stalled a Phase 5 run for over eight hours.
   plan.md section 16.1 requires a TED timeout and there was none. Phase 5 was
   re-run from scratch with both fixes; the original output is preserved at
   `phase5_before_rollout_fix/`.

## How the inconsistency is contained

`structural_metrics_recomputed.json` re-derives exact / skeleton / symbolic
equivalence / TED for **every stored formula in the run** — Phase 2, Phase 3, and
the post-fine-tuning MCTS records inside Phase 7 and Phase 8 — from the saved
prefixes, under one canonicalization. Original values are kept beside the new ones
as `*_as_recorded`. Reported structural metrics come from that pass; the reports
show both columns.

Numeric metrics that do not depend on canonicalization (cross entropy, top-k,
RMSE, R2, search nodes, wall time) are unaffected by any of these changes.

## What this does *not* excuse

The test split was evaluated once, in Phase 8, and no condition was added or
re-scored against it afterwards. But the canonicalization used to report Phase 8's
formula-level metrics was finalized after Phase 3 results had been seen. A reader
who wants a fully pre-registered structural metric should treat the
`*_as_recorded` column as the pre-change value and the recanonicalized column as a
post-hoc correction, and note that the correction was justified by a spec
requirement (section 11) rather than by the results it produced.
