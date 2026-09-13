# C0001 preregistration v4 closure review response

- task: C0001-T005
- implementer: Cursor Agent (repo-operator)
- reviewer packet: `preregistration_v4_closure_review.md`
- revised artifact: `preregistration_draft_v5.md`
- date: 2026-09-13
- verdict requested: fourth independent closure review (`ready_for_independent_closure_review`)

## Summary

v5 closes all eight remaining findings (V4-1–V4-8) from the v4 independent closure review.
The scientific question is unchanged. v5 aligns the primary hypothesis with the
`structural_false_negative` terminal category (E1 **and** E2 oracle equivalence),
adds **fully diagnostic** coverage rules so absence cannot be concluded from non-diagnostic
failures, freezes the SHA256-indexed `(r*E)/r` rewrite template, unifies
`audit_rational_parse` across truth/E0/E1/E2 oracle inputs, models the primary readout as an
explicit two-stage simplifier→classifier chain with persisted attribution fields, restores
config-derived deny patterns with normalized path rules, expands resume identity checks,
corrects `formula_metrics` API wording, and adds N1/B4 oracle-health gates.
Confirmatory budget arithmetic is unchanged (**23,550**; grand max **25,860**).

## Finding closure map

| ID | Review finding (abbrev.) | v5 closure | Status |
|---|---|---|---|
| **V4-1** | Hypothesis text vs `structural_false_negative` mismatch; E1 parse unclassified | §1 H0001 requires E1 **and** E2 oracle equivalence; §2.2 precedence: E0/E1 construction or parse inability before simplifier → `construction_incomplete`; E1/E2 oracle timeout/parse during execution → `execution_failure` | **CLOSED** |
| **V4-2** | Terminal coverage alone permits false unsupported from all failures | §1 diagnostic coverage: supported requires ≥1 **fully diagnostic** SFN; unsupported only when all 1,320 are diagnostic (`construction_incomplete`=0, `execution_failure`=0, `semantic_drift`=0) and SFN=0; otherwise undecidable; fixed denominator preserved | **CLOSED** |
| **V4-3** | Rewrite operationally undefined | §3.2: `PRIMES=[2,3,5,7,11]` via SHA256 of canonical UTF-8 key; frozen prefix `div,mul,{r},{E...},{r}` and infix `(({r}*({E}))/{r})`; no simplification before E0; P2 lexical non-identity + exact equivalence; 510/510 P2 unchanged | **CLOSED** |
| **V4-4** | Exact parsing / classifier requantization boundary open | §3.5 `audit_rational_parse` for all oracle inputs (Rational from token string, no float); §2.1 two-stage chain (simplifier → `parse_system` 4-significant-digit); persist `e2_infix_pre_classifier` and classifier-normalized forms; no claim that classifier avoids requantization | **CLOSED** |
| **V4-5** | Sealed guard patterns not unique | §11: four config-derived patterns under resolved `output_root`; `normpath` + `realpath` dual check; relative path resolution; parent + simplifier child install; intercept open/stat/listdir/scandir/pathlib; zero attempts; no inventory | **CLOSED** |
| **V4-6** | Resume provenance insufficient | §12 resume identity: audit_id, commit, plan/script/config/source/corpus hashes, seeds, primitive table, normalized CLI (exclude only `--resume`/`--fail-if-exists`), all timeouts, deps, environment; `rewrite_id=identity` (B1), `truth_copy` (B4) in §6–§7 | **CLOSED** |
| **V4-7** | `formula_metrics(skip_cas=True)` API inaccurate | §2.1: public signature `formula_metrics(true_infix, predicted_infix)`; `skip_cas=True` fixed internally via `compare_formulas` | **CLOSED** |
| **V4-8** | Oracle health gates missing | §10 G_n1: N1 100/100 reject; G_b4: B4 510/510 valid + canonical self-match; any gate FAIL → undecidable | **CLOSED** |

---

## v4 → v5 disposition (selected)

| v4 element | v5 disposition | Rationale |
|---|---|---|
| Hypothesis: E2 equivalence only | E1 **and** E2 equivalence | V4-1 |
| Unsupported when SFN=0 and gates PASS | Unsupported only if **all 1,320 fully diagnostic** and SFN=0 | V4-2 |
| PRNG `r` from seed | SHA256-indexed prime from `[2,3,5,7,11]` | V4-3 |
| `(r*E)/r` verbal only | Frozen prefix/infix templates; no pre-E0 simplification | V4-3 |
| `Rational(token)` truth-only | `audit_rational_parse` on truth/E0/E1/E2 oracle inputs | V4-4 |
| “No requantization outside simplifier” | Explicit 2-stage chain; classifier 4-significant-digit documented | V4-4 |
| Deny guard without explicit patterns | Four config-derived glob patterns + norm/realpath rules | V4-5 |
| Resume: partial CLI/hash check | Full normalized CLI + timeouts + deps + environment | V4-6 |
| `rewrite_id` unspecified for B1/B4 | `identity` / `truth_copy` | V4-6 |
| `formula_metrics(skip_cas=True)` | `formula_metrics(true_infix, predicted_infix)` | V4-7 |
| No N1/B4 gates | G_n1 + G_b4 | V4-8 |
| `c0001_metric_identifiability_audit_v4` | `c0001_metric_identifiability_audit_v5` | audit_id bump |

v1–v4 drafts and `preregistration_v4_closure_review.md` remain untouched.

---

## Acceptance self-check

| Test | Evidence |
|---|---|
| Hypothesis aligned with SFN (E1+E2 equiv) | §1, §2.2 |
| Diagnostic vs non-diagnostic decision rule | §1, §2.2 `is_fully_diagnostic` |
| 1,320/1,320 terminal coverage required | §1, §2.2, §10 G_term |
| Frozen SHA256 rewrite + templates | §3.2 |
| Unified Rational oracle parser | §3.5 |
| 2-stage readout + attribution fields | §2.1, §12 |
| Config-derived deny patterns + intercepts | §11 |
| Expanded resume identity | §12 |
| G_n1 100/100; G_b4 510/510 | §10 |
| 510 P2; confirmatory 23,550; grand max 25,860 | §3.2, §8.3–§8.5 |
| V4-1–V4-8 closed | table above |

---

## Implementer attestation

- `preregistration_draft_v4.md` and `preregistration_v4_closure_review.md` were not edited.
- No implementation, experiment execution, sealed artifact access, or push was performed.
- Section references verified against `preregistration_draft_v5.md` before commit.
