# C0001 v16 round7 r6: PI mechanical packet verification

Scope: **implementation acceptance only**, not scientific result, source closure, or full-audit authorization. Primary output is in isolated worktree `/tmp/lansr-multiai-C0001-acceptance-r6/GPU_RUNmultiAI/cycles/C0001/runs/c0001_metric_identifiability_audit_v16_round7_acceptance_r6/` on reviewed/pushed source `ba3ef3dd26ba3ae0dd36a2c7165d7476e11a2432`. The frozen v16 plan SHA256 was recomputed as `67017f5c8bac861664fc867b70cf229d43be3d052d266ffd0d575e20e6c12078`. The worktree branch remote SHA matched source. The user-systemd service ended with `Result=success`, `ExecMainStatus=0`; completion at 2026-09-24 17:15:35 UTC.

Direct PI `jq`, `wc`, `rg`, `sha256sum -c` and service-journal checks:

| Evidence | Observed |
|---|---|
| `audit_manifest.json` | `status=completed`, `mode=implementation_acceptance`, full 40-character commit and frozen plan SHA match, `b1_rows=510`, `confirmatory_calls=grand_calls=4080`, `elapsed_sec=2116.585450179875` (<18,000), `dir_bytes=8735960` (<1,200,000,000), `timing_calibration_status=PASS`, worktree provenance clean |
| `call_log.jsonl` | 4,080 valid JSONL rows; 4,080 unique `(primitive,condition,stage,unit_type,unit_id)` tuples; 510 unique units; all B1/completed; oracle 1,020 calls and six other primitives 510 each |
| `b1_evidence.json` | 510 rows, 510 unique pairs and components, 510 `control_pass_row=true`, 510 `outcome_category=control_pass`, 0 unknown |
| Q4 / reachability | `q4_reference_controls.json` 7 distinct PASS fixtures; `reachability_evidence.json` 10 distinct PASS fixtures, with synthetic and live-production-rescale types labelled separately |
| Contract/implementation | `contract_evidence.json`: G_contract 7/7 and F1/F2/F4–F8 7/7 PASS; manifest `validity_gates` has G_contract, G_impl, G_b1, G4 and the other applicable acceptance gates true; full-audit-only gates remain false by design |
| Provenance | `source_inventory.json` 91 distinct paths; each recorded SHA256 recomputed against current worktree via `sha256sum -c --status`, exit 0; no `abort_manifest.json`; `primary_decision` absent; closure source hashes absent pre-closure |
| Guard/failure visibility | Both run guard side-channel JSONL files are zero bytes; no literal `"error_isolated": true` in run JSON/JSONL/CSV files; deviation log records reduced mode, excluded auxiliary preflight, and ordering |

Primary artifact SHA256: `audit_manifest.json` `d29f0cd3af84b1631fefe015c9bf680f6a7b952490c96c16f21bda322189aa89`; `call_log.jsonl` `6effe2defb8c1e011c6e35825db8c844ee0b3b114e8d9d63837e851a1fd8823c`; `b1_evidence.json` `8b775e93f9b2b28f6482be602aade1eecc8baaa48d6f63a3e4d841474bed3b92`; `source_inventory.json` `978a8969449a4a71bad5cc50d0d10a052d10b76c87e39b97b49bb547e55c454c`.

Gemini broker compressed the supplied PI packet as a secondary index; it did **not** inspect primary files. Two Gemini statements are rejected: the manifest commit is not truncated (it stores the full SHA), and a frozen-plan edit is not implied by the 82→91 path delta. The v16 recursive source-inventory algorithm is normative; 82 was an observed pre-implementation snapshot, and the nine added implementation files still need explicit accepted closure reconciliation. Synthetic reachability fixtures are not interchangeable with live production checks.

**PI status: mechanically consistent packet, independent post-packet Claude review pending.** Do not promote r6 to implementation closure, full audit, or scientific evidence until reviewer findings and the remaining closure/replication gates are resolved. Interrupted r4 and failed-before-output r5 are preserved separately.
