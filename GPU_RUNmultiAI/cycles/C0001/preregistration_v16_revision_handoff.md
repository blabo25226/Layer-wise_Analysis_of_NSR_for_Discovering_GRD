# C0001-T015 v16 surgical revision handoff

Create v16, v15 response, v16 completion, and update state. Preserve v9-v15.
No code/tests/results/smoke/freeze and no touch of the untracked v9 smoke.

Required changes only:

1. Replace every “implementation after G_contract PASS” phrase with
   **post-freeze, before G_contract evaluation**.
2. Freeze `scripts/phases/guard_bootstrap.py` as a self-contained stdlib-only
   guard implementation, not an import of current `gpu_runmultiai` guard code.
   It implements normalization, deny matcher, interceptors, attempt ledger, and
   restore/merge methods required by §11.
3. API:
   `install_guard_from_entry(entry_script_path: str) -> BootstrapGuardHandle`
   and `get_installed_guard() -> BootstrapGuardHandle`. Installation stores the
   exact handle in a module singleton; a second different install aborts.
4. Parent retains returned handle, merges child side-channel attempts into it,
   and evaluates G4 from it. Child uses its returned handle and serializes its
   attempts. Importing package/runtime is allowed only afterward.
5. G_contract verifies install-before-import, singleton identity, no replacement,
   parent/child attempt propagation, deny/block behavior, and G4 ledger source.
6. Correct the document identity to v16 and the oracle grid reference to
   §3.5.2. Search for stale v14/v15 identity and wrong grid references.
7. Keep all other v15 content, audit ID
   `c0001_metric_identifiability_audit_v16`, seven calls, counts
   27,637/2,640/30,277, and exact G_impl list unchanged.

Use at most two commits: content, then optional completion-only. Push each once,
do not chase the final tip in state/completion, and verify local/remote parity.
v16 remains unfrozen pending targeted review.
