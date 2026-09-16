# C0001 preregistration v11 independent closure review

- task: `C0001-T010-REVIEW`
- reviewed tip: `dca33882fbc6bc0ef9644683645f4a64e8556952`
- reviewed plan SHA256: `f8a31030a9032c204e0043a834f94cbe9e44fafac3ca11553ff38b126fe231d1`
- reviewers: Claude Code read-only critic; Codex independent subagent
- PI: Codex
- verdict: **BLOCK_AND_REVISE_TO_V12**
- freeze/full audit: **PROHIBITED**

## Independently verified

- Local and remote task tip matched at the reviewed SHA.
- v9, v10, and v11 hashes matched their introduction records.
- Corpus regeneration produced 240 systems, 510 components, 330 strict-Hill
  components, 46 quantization-active and 284 neutral components, and zero
  exponent-form numeric tokens.
- The real classifier/oracle fixtures were rechecked independently:
  `2*x_0**2/(1+x_0**2)` is strict-Hill;
  `4*x_0**2/(2+2*x_0**2)` is exactly equivalent but classified false;
  `x_0**2/(1+x_0**2)` is classified true.
- Confirmatory 27,636, D2 2,640, and grand 30,276 arithmetic is correct.
- Q4 direction, identity-fallback candidate, classifier-parse precedence,
  `unit_type=fixture`, bounded non-independence, and 5h/1.2GB non-blocking
  resource increase are scientifically acceptable.

## Blocking findings

### R11-1 — P0: impossible and contradictory Rational fixture

Exact Rational `(1/3)*x_0` remains Rational under the frozen Float-only Q4
rounder. It cannot emit Float token `0.3333`. Direct SymPy verification produced
`x_0/3` with no Float atoms, whereas decimal input `0.33333*x_0` produced
`0.3333*x_0`. Freeze Rational round-trip invariance and keep decimal rounding as
a separate Float fixture. Remove the conflicting `mul,p,q,pow,-1` ordering;
production-compatible ordering is `mul,p,pow,q,-1`.

### R11-2 — P0: supported decision fixture violates terminal coverage

One SFN row alone triggers rank-1 undecidable because 1,319 primary rows are
missing. The supported decision fixture must contain 1 SFN plus 1,319 preserved
rows, all with unique pair IDs and all gates PASS. Unsupported must contain
1,320 unique preserved rows and all gates PASS.

### R11-3 — P1: v11 remains non-self-contained

Binding content is still delegated to v10 or production definitions: F1–F8,
operator arity and SymPy operator mappings, n-ary serialization, full N1 and B3
selection, ordering/scale-token/ID details, pointwise oracle rules, sealed guard
and child installation, artifact schemas, full resume identity/command,
environment comparison, and source-hash manifest requirements. v12 must inline
these normative values. Historical documents remain non-binding only.

### R11-4 — P1: scope and control predicates are incomplete or circular

B0 has 1,320 strict primary, 240 non-strict secondary, and 480 linear-control
rows, but v11 labels all B0 rows primary. Freeze required `eligibility_layer` and
derive `partition_scope` from condition plus layer. Define every non-primary
row predicate. Compute B1 `control_pass` directly from row flags, then define
G_b1 as 510/510 `control_pass`; do not define each through the other.

### R11-5 — P1: rescale early-return detection is ambiguous

Freeze the two actual production preconditions (`len(nodes)>len(scale)` and any
`x_k` with `k>=len(scale)`) and, if checking the return, use Python object
identity `rescaled_tree is input_tree`. Do not use lexical/algebraic equality and
delete the undefined catch-all third path.

### R11-6 — P1: resource and counted-call abort rules are inconsistent

G1 must apply to confirmatory calls only, with a separate grand-total gate for
D2. Freeze monotonic elapsed wall-clock seconds and output-directory byte
measurement points/abort behavior. Explicitly classify REACH-* calls as
post-freeze preflight test calls outside the audit-invocation counted-call
ledger; C_q4 remains inside and counted.

### R11-7 — P1: stratum validation and exponent handling

Re-derived 46/284 counts must be bound to a pre-pair reproducibility gate.
Because the frozen generator produces zero exponent tokens, an exponent token
signals corpus/serialization drift and must abort registration rather than
alter a primary row through `construction_incomplete`.

### R11-8 — P1: normative implementation gate is ambiguous

Inline all seven remaining requirements and have G_impl name exactly
`F1,F2,F4,F5,F6,F7,F8`; F3 is closed by the protocol amendment and is not a
post-freeze implementation check.

### R11-9 — P2: provenance update churn

Three follow-up commits attempted to make `observed_commit` equal a self-changing
tip. This is not a freeze blocker, but must not recur. A freeze record should pin
the reviewed content source commit, plan SHA, freeze commit, and one subsequent
remote verification. `observed_commit` is an observation, not a self-reference.

## PI resolution on preflight evidence

The reviewers disagreed on whether `reachability_evidence.json` must exist before
freeze. The PI accepts the specification and independent hand-fixture checks as
sufficient preregistration closure evidence. The JSON is deliberately a
post-freeze implementation/preflight artifact required by G_impl before the
full audit. It must not be generated by editing the scientific implementation
before the contract freezes.

## Gate decision

Produce v12 and a targeted response. Review the changed sections only. Freeze
only after PASS; then integrate the plan to the research branch, implement, run
G_impl/smoke, and repeat independent implementation review.
