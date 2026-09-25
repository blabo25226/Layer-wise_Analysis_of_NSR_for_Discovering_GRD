# C0001 preregistration v8 closure review response

- task: C0001-T005
- implementer: Cursor Agent (repo-operator)
- reviewer packet: `preregistration_v8_closure_review.md`
- revised artifact: `preregistration_draft_v9.md`
- date: 2026-09-13
- verdict requested: eighth independent closure review (`ready_for_independent_closure_review`)

## Summary

v9 closes all five required revisions from the v8 independent closure review.
The scientific question, decision rules, whole-chain readout, validity gates, and confirmatory
budget arithmetic are unchanged (**23,550** confirmatory; **25,860** grand maximum).
v9 unifies **field-labeled canonical bytes** across rewrite, N1, component, and pair serialization;
moves templates and representative fixtures into **plain-text code fences** outside tables;
freezes **corpus fingerprint bytes** as `json.dumps(fingerprint_payload, sort_keys=True).encode()`
with a **G_corpus** assert that `SHA256(fingerprint_bytes) == corpus["fingerprint"]`;
adds descriptive pair scale token **`5.0`** with D2 `unit_type=pair` / canonical `pair_id`;
fixes validity-gate evaluation order to **G_corpus → G0 → …**; and bumps **`audit_id`**
to v9 with updated initial/resume commands.

## Finding closure map

| ID | Review finding (abbrev.) | v9 closure | Status |
|---|---|---|---|
| **V8-1** | component/pair fixture keys value-only but SHA expects field labels | §3.2 canonical serialization contract; §7.1 `component_key` / `pair_key` templates use `{field}={value}`; labeled fixtures in code fences; preserved digests `2eadb0ad...` / `2c5158b4...` | **CLOSED** |
| **V8-2** | Show exact bytes outside tables; pipe `0x7c` only, zero backslashes | §3.2 contract: ASCII pipe byte `0x7c`, backslash byte count = 0; rewrite/N1/component/pair templates and fixtures in `text` code fences; pipe counts rewrite=2, N1=2, component=2, pair=4 | **CLOSED** |
| **V8-3** | D2 descriptive scale `5.0` as pair scale token in typed call log/resume | §4.2 stress `{5.0}`; §7.1 scale tokens include **`5.0`**; D2 row `unit_type=pair`, `unit_id=pair_id`; §8.4 D2 note | **CLOSED** |
| **V8-4** | Freeze fingerprint bytes to Python `json.dumps` defaults; assert SHA equals `corpus["fingerprint"]` | §4.1 `fingerprint_bytes` / `fingerprint_payload_bytes_hash` / **G_corpus assert**; §10 G_corpus; §12 manifest/resume fields + exact bytes path | **CLOSED** |
| **V8-5** | Validity gate order must start with G_corpus | §10 evaluation order: **G_corpus → G0 → G4 → …** (removed contradictory G0-first intro) | **CLOSED** |

---

## v8 → v9 disposition (selected)

| v8 element | v9 disposition | Rationale |
|---|---|---|
| Value-only `component_key` / `pair_key` fixtures | Field-labeled canonical bytes in code fences | V8-1, V8-2 |
| `\|` separator notation in tables | `0x7c` pipe contract; exact bytes in fences | V8-2 |
| D2 scale `5.0` descriptive only | Allowed `pair_id` scale token + typed D2 call log | V8-3 |
| Informal fingerprint hash mention | Frozen `json.dumps(..., sort_keys=True).encode()` + assert | V8-4 |
| Gate intro `G0 → G4 → …` | `G_corpus → G0 → G4 → …` | V8-5 |
| `c0001_metric_identifiability_audit_v8` | `c0001_metric_identifiability_audit_v9` | audit_id bump |

v1–v8 drafts and `preregistration_v8_closure_review.md` remain untouched.

---

## Acceptance self-check

| Test | Evidence |
|---|---|
| Field-labeled canonical bytes + preserved fixture digests | §3.2, §4.3, §7.1 code fences |
| Pipe `0x7c` only; backslash count 0; pipe counts 2/2/2/4 | §3.2 contract; fixture `pipe_count` / `backslash_count` lines |
| D2 `scale=5.0` + `unit_type=pair` / `pair_id` | §4.2, §7.1, §8.4 |
| Fingerprint bytes freeze + G_corpus assert | §4.1, §10, §12 |
| Gate order G_corpus first | §10 |
| Confirmatory 23,550; grand max 25,860 | §8.3–§8.5 |
| V8-1–V8-5 closed | table above |

---

## Implementer attestation

- `preregistration_draft_v8.md` and `preregistration_v8_closure_review.md` were not edited.
- No implementation, experiment execution, sealed artifact access, push, or freeze was performed.
- Prior drafts v1–v7 and all prior review packets remain preserved.
