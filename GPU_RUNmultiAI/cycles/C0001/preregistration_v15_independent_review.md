# C0001 preregistration v15 targeted independent closure review

- task: `C0001-T014-REVIEW`
- reviewed tip: `7201e874d51f202e34fd581de9f8196ab7dc3446`
- reviewed plan SHA256: `dd986ab519eb3097b0978368482b02fc9e94f5514f89c2ad35e56d6870d8ecf2`
- reviewers: Codex independent subagent; Codex PI
- Claude status: bounded read-only call returned no review body
- verdict: **BLOCK_AND_REVISE_TO_V16**
- freeze/full audit: **PROHIBITED**

## PASS

- R14-1 right-nested outputs and seven executable fixtures.
- R14-2 operator/leaf/remainder semantics.
- R14-4 C_q4, B0/B1/D2 oracle, and deviation schemas.
- Source inventory direction, counts 27,637/2,640/30,277, historical hashes,
  and local/tracking/remote parity.

## Blockers

### R15-1 — P0: guard bootstrap ordering and ownership are circular

v15 says the bootstrap is implemented after G_contract passes, but G_contract
requires the bootstrap test to pass. It also requires a stdlib-only module to
construct the current `SealedPathGuard`, whose module imports forbidden package
dependencies. Finally, `install_guard_from_entry(...)->None` gives no handle to
the attempt ledger needed for child merge and G4.

v16 must require implementation **post-freeze but before G_contract evaluation**.
The standalone stdlib-only module must implement its own matcher/interceptors,
return a `BootstrapGuardHandle`, retain it in a module singleton, and expose
`get_installed_guard()`. The parent uses that exact handle for attempt merge and
G4; no second guard installation may replace or hide it.

### R15-2 — P1: two stale references remain

- The title prose calls v15 a v14 draft.
- The oracle grid points to §13.1 instead of §3.5.2.

## Gate decision

Produce v16 with only R15-1 and R15-2 changes and re-review. No implementation,
freeze, smoke, or full audit is authorized before PASS.
