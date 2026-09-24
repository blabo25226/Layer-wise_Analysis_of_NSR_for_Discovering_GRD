# C0001 v16 §3.8-before-§10 G_impl preflight (implementation note)

This note records implementation interpretation only. It does not amend frozen
`preregistration_draft_v16.md` (SHA256 in `preregistration_v16_freeze_record.md`).

Frozen §3.8 defines reachability fixtures that feed **G_impl**. Frozen §10 defines
the full confirmatory audit disposition. The orchestrator therefore:

1. Builds all ten §3.8 reachability rows (with optional capped live ident-fallback
   observation on implementation-acceptance only) **before** any counted confirmatory
   primitive on acceptance and full (non-smoke) paths.
2. On any fixture `passed=false`, raises `GateAbortError` and routes through the
   global abort handler: `audit_manifest.json` status `aborted`, durable
   `abort_manifest.json`, and **zero** confirmatory counted calls in `call_log.jsonl`.
3. Does **not** emit a `completed` full-audit manifest that would require §10 G_impl
   to adjudicate a run that never satisfied §3.8 preflight.

Implementation-acceptance auxiliary work (registration, G0, G_contract probes,
reachability live probe with isolated `CallLogger`, timing calibration) remains
outside the §8.1 B1 acceptance ledger and is declared in `deviation_log.md`.
