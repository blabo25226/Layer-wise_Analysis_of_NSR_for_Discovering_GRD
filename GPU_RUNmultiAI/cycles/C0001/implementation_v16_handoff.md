# C0001-T016 post-freeze v16 implementation handoff

## Binding contract

- plan: `GPU_RUNmultiAI/cycles/C0001/preregistration_draft_v16.md`
- plan SHA256: `67017f5c8bac861664fc867b70cf229d43be3d052d266ffd0d575e20e6c12078`
- freeze commit: `b598cc3c6955f1c2fa071cb49eef034b2a4719a4`
- worktree: `/tmp/lansr-multiai-C0001-implement-audit`
- branch: `ai/C0001/research-engineer/implement-metric-audit`

The plan is immutable. Code may change only to satisfy its post-freeze
requirements. Full 27,637-call audit remains prohibited.

## Required implementation

1. F1, F2, F4, F5, F6, F7, F8 exactly as §16.
2. `scripts/phases/guard_bootstrap.py` and parent/child import ordering exactly
   as §11, including singleton handle, side-channel merge, and G4 ledger source.
3. Audit-owned Q4 reference, all seven C_q4 fixtures, right-nested n-ary output,
   Rational/Float separation, and global Q4 contract abort.
4. G_contract acceptance tests for all seven rows in §10.1.
5. Exact artifact schemas, mandatory flush+fsync, partial-suffix truncate,
   resume mismatch checks, manifest/abort/deviation lifecycle.
6. CLI/constants/audit ID and ceilings for v16: 27,637 / 30,277; D2 2,640;
   q4 timeout 10.0; all frozen environment/CLI fields.
7. Generate post-freeze `reachability_evidence.json` from tests, not hand-edited
   assertions: supported 1 SFN + 1,319 preserved and unsupported 1,320 preserved.

## Outputs

- code under the frozen 82-path inventory;
- focused tests and exact G_contract/G_impl evidence;
- bounded fresh smoke under a new v16 smoke ID, never the untracked v9 smoke;
- `implementation_completion_v16.md` with commands/results and known limits;
- no `implementation_closure_record.json` until independent review PASS.

## Acceptance before independent review

- v16 plan hash unchanged;
- compileall and focused pytest PASS;
- seven C_q4 fixtures PASS;
- G_contract and G_impl preflight evidence PASS;
- smoke manifest uses v16 audit ID, code commit, plan hash, exact ceilings;
- no sealed-path attempt; no GPU/decode call; no full audit;
- `git diff --check` PASS;
- worker commits, pushes, and verifies local/remote equality.

The PI and an independent reviewer will inspect the diff and evidence before
binding accepted source hashes or authorizing the full audit.
