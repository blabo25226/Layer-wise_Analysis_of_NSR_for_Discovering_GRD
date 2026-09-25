# C0001 preregistration v3 independent review response

- task: C0001-T005
- implementer: Cursor Agent (repo-operator)
- reviewer packet: `preregistration_v3_independent_review.md`
- revised artifact: `preregistration_draft_v4.md`
- date: 2026-09-13
- verdict requested: third independent closure review (`ready_for_independent_closure_review`)

## Summary

v4 closes all blocking (R3-1–R3-3) and major (R3-4–R3-9) findings from the v3 independent
closure review. The scientific question is unchanged. v4 adds an exhaustive five-category
precedence table, 100% terminal-coverage primary decision rule, 510-component rewrite
registration, lexical `.4g` truth corpus boundary, deny-on-attempt sealed access guard,
expanded resume/provenance contract, and recomputed budgets (**23,550** confirmatory;
**25,860** full-run grand maximum).

## Reviewer routing note

Two Claude scientific-critic wrapper attempts were made for v3 independent review.
Both exceeded the retry budget (15 min full scope; 5 min reduced scope) and returned
`Execution error` with misleading `exit_code=0`. These are recorded as **recoverable
reviewer-routing failures**; exit code 0 is not success evidence. Scientific closure
fell back to an independent Codex subagent reviewer (`preregistration_v3_independent_review.md`).

---

## Finding closure map

| ID | Review finding (abbrev.) | v4 closure | Status |
|---|---|---|---|
| **R3-1** | Five-way partition not exhaustive | §2.2 frozen precedence table; `semantic_drift` = E1 or E2 non-equivalent; `structural_false_negative` only when both equivalent and `hill_form=false`; `preserved` otherwise; `e1/e2_oracle_equivalent` stored | **CLOSED** |
| **R3-2** | 95% primitive completion insufficient for 0-count primary rule | §1, §2.2, §10 G_term: exactly 1,320 unique pairs with exactly one terminal outcome; any missing/unknown → undecidable; §8.6 primitive completion operational only | **CLOSED** |
| **R3-3** | B0=510 vs rewrite registration=330 disconnected | §3.2, §6, §8.3: all 510 components get deterministic seeded non-identity rewrite; P2 = 510; `rewrite_id` in `pair_id` | **CLOSED** |
| **R3-4** | D1 duplicates B0; ceiling ambiguous | §8.4 D1 = 0-call filtered B0 aggregation; §8.5 confirmatory hard ceiling 23,550; full-run grand max 25,860 | **CLOSED** |
| **R3-5** | `.4f` corpus mismatches `grn.py` `.4g` | §3.4, §4.1: lexical `.4g` tokens; `Rational(token_string)` oracle; no `.4f` corpus; no requantization outside production simplifier; raw token + value stored | **CLOSED** |
| **R3-6** | Secondary 60 not all modulated | §2.2, §4.1: renamed non-strict Hill-bearing; R07 modulated 30 / R08 product-base 30 | **CLOSED** |
| **R3-7** | Sealed guard conflates existence and access | §11 deny-on-attempt guard before corpus work; normalized path vs config-derived forbidden patterns; blocks open/stat/listdir/scandir; zero attempts required; presence alone not failure | **CLOSED** |
| **R3-8** | Resume key and provenance insufficient | §7 `pair_id` fields; §12 resume `(primitive, condition, stage, pair_id)`; manifest plan/audit-script hashes, CLI, deps, environment, ordered primitive table; per-pair E0/E1/E2 raw prefix + emitted infix | **CLOSED** |
| **R3-9** | Cross-reference errors | §10 validity gates, §8.5 compute ceiling; audit_id v4 throughout; headings verified | **CLOSED** |

---

## v3 → v4 disposition (selected)

| v3 element | v4 disposition | Rationale |
|---|---|---|
| `simplifier_drift` / `oracle_equivalent_and_flagged` | `semantic_drift` / `preserved` | R3-1 exhaustive partition |
| 95% primitive completion gate (G1) | operational metric only; G_term = 100% terminal coverage | R3-2 |
| P2 = 330 strict-Hill only | P2 = 510 all components | R3-3 |
| Confirmatory 23,370 | 23,550 (+180 P2) | R3-3 |
| D1 = 1,680 extra calls | D1 = 0-call B0 aggregation | R3-4 |
| Grand max 27,360 | 25,860 (23,550 + D2 2,310) | R3-4 |
| `{:.4f}` quantization | lexical `.4g` token audit | R3-5 |
| modulated-Hill secondary 60 | non-strict Hill-bearing; R07/R08 split | R3-6 |
| glob match-count guard | deny-on-attempt access guard | R3-7 |
| Resume `(condition, pair_id)` | `(primitive, condition, stage, pair_id)` | R3-8 |
| `c0001_metric_identifiability_audit_v3` | `c0001_metric_identifiability_audit_v4` | R3-9 |

v1, v2, and v3 drafts remain untouched.

---

## Acceptance self-check

| Test | Evidence |
|---|---|
| Exhaustive mutually exclusive 5-way partition | §2.2 precedence table |
| 1,320/1,320 terminal coverage required | §1, §2.2, §10 G_term |
| 510-component rewrite + P2=510 | §3.2, §8.3 |
| Confirmatory 23,550; grand max 25,860 | §8.3–§8.5 |
| Lexical `.4g` truth boundary | §3.4, §4.1 |
| Deny-on-attempt sealed guard | §11 |
| Expanded resume/provenance | §7, §12 |
| R3-1–R3-9 closed | table above |

---

## Implementer attestation

- `preregistration_draft_v3.md` was not edited.
- No implementation, experiment execution, sealed artifact access, or push was performed.
- Section references verified against `preregistration_draft_v4.md` before commit.
