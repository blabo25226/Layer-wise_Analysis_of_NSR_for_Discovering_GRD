# C0001 v16 round-7 PI resolution: identity-fallback reachability

Date: 2026-09-23. Track: scientific implementation gate, **not** a scientific result.
Frozen plan: `preregistration_draft_v16.md`, SHA256 `67017f5c8bac861664fc867b70cf229d43be3d052d266ffd0d575e20e6c12078` (immutable).

## Evidence and conflict

- Frozen §3.8 labels `REACH-IDENT-FALLBACK-1` **synthetic** and requires an E2 raw prefix byte-identical to E1 raw, E1 not SymPy-equivalent to Q4(E1), detection of `e2_identity_fallback_candidate=true`, and `execution_failure` precedence. Frozen §3.6 explicitly forbids inferring internal simplifier timeout solely from E2==E1.
- Round-6 review R6-1 correctly rejected an artifact that reported a changed production E2 while replacing the stored E2 with E1 and calling the result a live production fixed point.
- The later round-7 handoff requires a deterministic live production simplifier fixed point that is also non-Q4-equivalent. Claude Opus 5.5's read-only methodological check of the current code found that normal simplifier completion rounds to four decimal places; a non-Q4-equivalent identity requires a timing-dependent fallback path. The current uncommitted second search loop uses a simplifier-produced E1 instead of production B0 E1, and must not be labelled production.
- Existing round-7 acceptance shows `REACH-IDENT-FALLBACK-1=false`, `G_impl=false`. It remains an honest failed implementation packet. No counted full audit is authorized.

## PI decision

1. Satisfy the **frozen synthetic decision-rule fixture** honestly. Construct a deterministic d>=2 E1 prefix with a >4-decimal numeric leaf and compute Q4 independently; use an explicitly synthetic E2 raw string equal to E1 raw. Feed these values through the unmodified production detector and outcome-precedence code. Assert the exact frozen predicates, including E1≢Q4(E1), and preserve input, raw strings, Q4, detector result, and outcome. Label the E2 as synthetic injection, **not** a production simplifier output or timeout.
2. Keep a separate **live production observation** using `run_b0_pair` and its actual E1/E2. Preserve real E2 unchanged. Record whether a valid live identity fallback was found; absence is an observed negative reachability result, not a synthetic-fixture failure and not evidence of timeout. Never replace production E2.
3. Remove or supersede the uncommitted second loop that labels a simplifier-produced E1 as production. Do not convert a failure to PASS by altering field names or booleans.
4. This resolves a stricter post-freeze handoff requirement against the binding frozen plan; it does **not** amend v16. Request explicit Claude Opus 5.5 independent review of the split and all primary evidence before implementation closure. If the reviewer finds the frozen synthetic criterion itself inadequate for the research question, record that limitation and open a new preregistration version rather than silently changing v16.

Implementation author: Cursor Agent. Independent reviewer: Claude Opus 5.5. Research PI owns this protocol interpretation and the final Go/No-Go. Until independent PASS and other G/F gates close, the 27,637-call audit remains prohibited.
