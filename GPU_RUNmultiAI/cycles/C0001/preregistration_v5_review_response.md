# C0001 preregistration v5 closure review response

- task: C0001-T005
- implementer: Cursor Agent (repo-operator)
- reviewer packet: `preregistration_v5_closure_review.md`
- revised artifact: `preregistration_draft_v6.md`
- date: 2026-09-13
- verdict requested: fifth independent closure review (`ready_for_independent_closure_review`)

## Summary

v6 closes all eight required revisions from the v5 independent closure review.
The scientific question is unchanged. v6 freezes an **exclusive primary decision order**
with explicit existence-versus-absence asymmetry, introduces a tri-state oracle result schema
(`completed`, `analytic_equivalent`, `numeric_equivalent`, `equivalent`), corrects rewrite
canonical keys (literal ASCII pipe, zero-based unpadded indices, frozen UTF-8 digest example),
limits the primary claim to the **whole simplifier + classifier chain** without causal stage
attribution, replaces glob deny patterns with a **POSIX component-based sealed matcher** inherited
by all child processes, expands resume to repeat all semantic CLI flags, freezes N1 component
selection and non-equivalence templates, and adds a linear control coverage gate
(**480/480** parser-valid and metric-valid). Confirmatory budget arithmetic is unchanged
(**23,550**; grand max **25,860**).

## Finding closure map

| ID | Review finding (abbrev.) | v6 closure | Status |
|---|---|---|---|
| **v5-R1** | Decision precedence overlap between supported and undecidable | §1 exclusive order: gate/terminal fail → undecidable; else diagnostic SFN ≥1 → supported (non-diagnostic pairs allowed); else SFN=0 and all 1,320 diagnostic → unsupported; else undecidable. Asymmetric existence vs absence explained. | **CLOSED** |
| **v5-R2** | Completed non-equivalence misclassified as execution failure | §3.5 oracle schema: `completed=false` only for parse/timeout/nonfinite/exception; `completed=true`, `equivalent=false` → `semantic_drift` (B0) or expected N1 reject; `equivalent = analytic_equivalent AND numeric_equivalent` | **CLOSED** |
| **v5-R3** | Rewrite canonical key pipe/backslash and index padding | §3.2: literal ASCII `\|` in key string (no backslash in bytes); zero-based decimal indices without padding; frozen example `audit_rewrite_seed=61003\|family=R01\|variant_index=0\|component_idx=0` → SHA256 `57f7c55b2de5a6e9e10c1c7518ada07890eb00d3588c045ca3d531dfbae0187c`, `r=2`; `rewrite_id=rewrite_sha256:{full_digest}` | **CLOSED** |
| **v5-R4** | Classifier normalized infix requirement impossible; causal attribution | §0, §2.1: primary claim is whole-chain only; store Stage A infix and Stage B parse flags/`hill_form`; no causal stage attribution; future ablation separately budgeted | **CLOSED** |
| **v5-R5** | Deny matcher ambiguity | §11: absolute POSIX component matcher after normpath/realpath under `output_root`; first component `gpu_run5_*`; block `test`/`sealed`/`final_test` directory + descendants anywhere after campaign; block `predictions` + descendants only when preceded by `phase8`; no enumeration; all child processes install guard before task code | **CLOSED** |
| **v5-R6** | Resume CLI semantic identity | §12–§13: compare semantic CLI excluding only `--resume` and `--fail-if-exists`; resume command repeats all initial semantic flags plus `--resume` | **CLOSED** |
| **v5-R7** | N1 selection/template/ID undefined | §4.3: first 100 of 510 by SHA256(`audit_negative_seed=61004\|...`); prefix `add,{E...},{c}`, infix `(({E})+({c}))`; `c` from `[1,2,3,5,7]` via digest mod 5; no simplification; `negative_sha256:{full_digest}`; G_n1 requires `completed=true` and `equivalent=false` 100/100 | **CLOSED** |
| **v5-R8** | Linear controls missing parse/metric coverage | §10 G_ctrl_cov: 480/480 `classifier_parse_valid` and `formula_metrics.valid`; failures remain in denominator; plus existing FP and canonical non-invariance gates | **CLOSED** |

---

## v5 → v6 disposition (selected)

| v5 element | v6 disposition | Rationale |
|---|---|---|
| Conjunctive supported/unsupported table | Exclusive 4-step order | v5-R1 |
| Oracle disagreement → execution_failure | Tri-state `completed` / `equivalent` | v5-R2 |
| `\|` escaped in canonical key doc | Literal pipe in UTF-8 bytes | v5-R3 |
| `e2_infix_classifier_normalized` required field | Removed; Stage B flags only | v5-R4 |
| Glob deny patterns P_test…P_final_test | Component-based matcher | v5-R5 |
| Resume: `--audit-id`, `--output-dir`, `--resume` only | Full semantic flag replay | v5-R6 |
| N1 “100 reject” verbal | Frozen selection key, template, coefficient domain, ID | v5-R7 |
| Linear gates: FP + canonical only | Add G_ctrl_cov 480/480 parse+metric valid | v5-R8 |
| `c0001_metric_identifiability_audit_v5` | `c0001_metric_identifiability_audit_v6` | audit_id bump |

v1–v5 drafts and `preregistration_v5_closure_review.md` remain untouched.

---

## Acceptance self-check

| Test | Evidence |
|---|---|
| Exclusive decision order + asymmetric logic | §1 |
| Oracle tri-state schema | §3.5, §2.2, §9 |
| Frozen rewrite UTF-8 example + rewrite_id | §3.2 |
| Whole-chain claim; no causal attribution | §0, §2.1 |
| Component-based sealed matcher + child guard | §11 |
| Semantic CLI resume replay | §12, §13.3 |
| N1 100/100 completed non-equivalent | §4.3, §10 G_n1 |
| Linear 480/480 parse+metric coverage | §10 G_ctrl_cov |
| Confirmatory 23,550; grand max 25,860 | §8.3–§8.5 |
| v5-R1–v5-R8 closed | table above |

---

## Implementer attestation

- `preregistration_draft_v5.md` and `preregistration_v5_closure_review.md` were not edited.
- No implementation, experiment execution, sealed artifact access, or push was performed.
- Prior drafts v1–v4 and all prior review packets remain preserved.
