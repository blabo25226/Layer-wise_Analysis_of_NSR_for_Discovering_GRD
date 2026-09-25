# C0001 preregistration v7 closure review response

- task: C0001-T005
- implementer: Cursor Agent (repo-operator)
- reviewer packet: `preregistration_v7_closure_review.md`
- revised artifact: `preregistration_draft_v8.md`
- date: 2026-09-13
- verdict requested: seventh independent closure review (`ready_for_independent_closure_review`)

## Summary

v8 closes all three required revisions from the v7 independent closure review.
The scientific question, decision rules, whole-chain readout, validity gates, and confirmatory
budget arithmetic are unchanged (**23,550** confirmatory; **25,860** grand maximum).
v8 freezes **`generate_corpus`** invocation and **`corpus_hash == corpus["fingerprint"]`**
with verbatim **`fingerprint_payload`** persistence and SciPy/NumPy version recording;
aligns **source `system_id`**, **rewrite/N1 keys**, and **tier/draw indexing** to corpus records;
introduces typed **`unit_type` / `unit_id`** resume and call-log identity; and bumps **`audit_id`**
to v8 with updated initial/resume commands including **`--audit-trajectory-seed 61002`**.

## Finding closure map

| ID | Review finding (abbrev.) | v8 closure | Status |
|---|---|---|---|
| **V7-1** | Frozen corpus not uniquely regenerable | §4.1: exact `generate_corpus(variants={"train":30}, n_points=150, t_span=(0.0,10.0), seed=61001, trajectory_seed=61002, rtol=1e-8, atol=1e-10, minimum_variance=1e-5, maximum_abs_state=100.0)`; train split only; 240 systems / 510 components / `rejection_rate` ≤ 0.30 or abort; `corpus_hash == corpus["fingerprint"]`; verbatim `fingerprint_payload` JSON + canonical sorted-key bytes hash; SciPy/NumPy in manifest; §7/`§13.3`/`§12` add `audit_trajectory_seed=61002`; **G_corpus** gate §10 | **CLOSED** |
| **V7-2** | Source index, canonical system ID, N1 ID mismatch | §4.1: `source_variant_index` 0..29; `tier_index = source_variant_index % 3`; `draw_index = source_variant_index // 3`; `exponent = (1,2,4)[tier_index]`; **`system_id` verbatim from source record** (e.g. `R01_train_d61001_000`); §3.2 rewrite key `audit_rewrite_seed=61003\|system_id=...\|component_idx=...` → digest `91a3f6eb...`, `r=3`; §4.3 N1 key `audit_negative_seed=61004\|system_id=...\|component_idx=...` → digest `ce6d15ac...`, `c=3`, `negative_id=negative_sha256:...` | **CLOSED** |
| **V7-3** | All counted calls forced through `pair_id` | §7.1: allowed `unit_type` tokens `component` / `pair` / `negative`; resume/dedup/call_log key `(primitive, condition, stage, unit_type, unit_id)`; R1/R2 → `component_id`; pair ops + B3 → `pair_id`; N1 → `negative_id`; R2 records **`rewrite_id` separately**; removed “every call uses `pair_id`”; frozen fixtures for `component_id` (`2eadb0ad...`) and updated `pair_id` (`2c5158b4...`) | **CLOSED** |

---

## v7 → v8 disposition (selected)

| v7 element | v8 disposition | Rationale |
|---|---|---|
| Informal `grn.py` corpus mention | Exact `generate_corpus` args + G_corpus | V7-1 |
| `system_id={family}:variant_index=...:draw_index=...` | Verbatim source `system_id` (`R01_train_d61001_000`) | V7-2 |
| Rewrite/N1 keys on `(family, variant_index, component_idx)` | Keys on `(system_id, component_idx)` with frozen digests | V7-2 |
| Resume key `(primitive, condition, stage, pair_id)` | Typed 5-tuple with `unit_type` / `unit_id` | V7-3 |
| `c0001_metric_identifiability_audit_v7` | `c0001_metric_identifiability_audit_v8` | audit_id bump |
| Missing `audit_trajectory_seed` | `61002` in seed table, CLI, manifest, resume | V7-1 |

v1–v7 drafts and `preregistration_v7_closure_review.md` remain untouched.

---

## Acceptance self-check

| Test | Evidence |
|---|---|
| Frozen `generate_corpus` + fingerprint identity | §4.1, §10 G_corpus, §12 |
| Verbatim `system_id` + tier/draw mapping | §4.1, §7 |
| Rewrite/N1 frozen digests (`91a3f6eb...` / `ce6d15ac...`) | §3.2, §4.3 |
| Typed unit IDs + 5-tuple resume key | §7.1, §8.1, §12 |
| `component_id` / `pair_id` representative fixtures | §7.1 |
| `audit_trajectory_seed` in seeds/CLI/manifest/resume | §7, §12, §13.3 |
| Confirmatory 23,550; grand max 25,860 | §8.3–§8.5 |
| V7-1–V7-3 closed | table above |

---

## Implementer attestation

- `preregistration_draft_v7.md` and `preregistration_v7_closure_review.md` were not edited.
- No implementation, experiment execution, sealed artifact access, push, or freeze was performed.
- Prior drafts v1–v6 and all prior review packets remain preserved.
