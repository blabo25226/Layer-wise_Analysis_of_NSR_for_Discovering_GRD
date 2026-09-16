# C0001-T017 implementation completion (v16 round 2)

- task: C0001-T017
- branch: `ai/C0001/research-engineer/implement-metric-audit`
- plan SHA256: `67017f5c8bac861664fc867b70cf229d43be3d052d266ffd0d575e20e6c12078`
- audit_id: `c0001_metric_identifiability_audit_v16`
- prior review: `implementation_review_v16_round1.md` (BLOCK)

## Initial failures (round-1 blockers)

| ID | Symptom | Root cause |
|---|---|---|
| P0-1 | B1 `control_pass_row=false` | E0 used production scaler (`a_t=0.9`); identity rescale returned same tree object → `rescale_incomplete` |
| P0-2 | Missing `G_eligibility`/`G_stratum`/`G_grand`/`G_contract`/`G_impl` | Gates absent from `controls.py` and manifest |
| P0-3 | No P12 / `quantization_stratum.json` | Quantization module and registration P12 calls missing |
| P0-4 | Second rescale early-return undetected | `rescale_system` only checked `len(nodes)>len(scale)` |
| P0-5 | Guard installed after package imports | Entry script imported `gpu_runmultiai` before `install_guard_from_entry` |
| P0-6 | 4/10 reachability rows | Synthetic-only UNS/SUP; missing SFN/PRESERVED/synthetic outcome fixtures |
| P0-7 | 14400 s / binary GiB ceilings | `resources.py` used wrong constants |

Additional contract gaps repaired: durable `pair_cache` loader, resume fingerprint byte reread, `negative_controls.json`, expanded `equivalence_oracle.json` schema (B1 rows), Q4 dialect (`idiv`/`mod` removed), `original_vs_q4_numeric_max_abs_error`, B2/D2 in bounded smoke, abort/deviation lifecycle fields, manifest resource ceilings.

## Commands

```bash
/home/blabo/miniconda3/envs/lansr310/bin/python -m compileall -q src scripts tests
sha256sum GPU_RUNmultiAI/cycles/C0001/preregistration_draft_v16.md
git diff --check
export LANSR_TED_TIMEOUT_SEC=10 LANSR_SYMPY_TIMEOUT_SEC=10 LANSR_SYMPY_MAX_NODES=40
PYTHONPATH=src /home/blabo/miniconda3/envs/lansr310/bin/python -m pytest -q tests/test_gpu_runmultiai_c0001_metric_audit.py
PYTHONPATH=src /home/blabo/miniconda3/envs/lansr310/bin/python scripts/phases/gpu_runmultiai_c0001_metric_audit.py \
  --audit-id c0001_metric_identifiability_audit_v16 \
  --output-dir GPU_RUNmultiAI/cycles/C0001/runs/c0001_metric_identifiability_audit_v16_round2 \
  --audit-data-seed 61001 --audit-trajectory-seed 61002 --audit-rewrite-seed 61003 \
  --audit-negative-seed 61004 --audit-cas-subset-seed 61005 \
  --allow-cpu --oracle-timeout-sec 30.0 --q4-timeout-sec 10.0 \
  --simplifier-subprocess-timeout-sec 5.0 --cas-timeout-sec 60.0 \
  --smoke --fail-if-exists
```

## Final results

| Check | Result |
|---|---|
| compileall | PASS |
| plan hash | `67017f5c8bac861664fc867b70cf229d43be3d052d266ffd0d575e20e6c12078` |
| focused pytest (Python 3.10) | **68 passed** |
| git diff --check | PASS |
| source inventory | `scripts/phases/guard_bootstrap.py` present (82-path inventory) |
| bounded round2 smoke | `GPU_RUNmultiAI/cycles/C0001/runs/c0001_metric_identifiability_audit_v16_round2` |

## Round2 smoke snapshot

- `status`: `completed`
- `confirmatory_calls`: 45 (bounded; `< 27637`)
- `validity_gates`: `G_eligibility`, `G_stratum`, `G_grand`, `G_contract`, `G_impl`, `G_q4ref` = **true**; `G_b1`/`G_n1`/partition gates **false** (smoke subset; expected)
- paths exercised: **B0**, **B1** (`control_pass_row=true` on 2/2 smoke rows), **B2**, **C_q4**, **N1**, **B3**, **B4**, **D2**
- artifacts include: `quantization_stratum.json`, `negative_controls.json`, `reachability_evidence.json` (10/10 PASS)
- resource manifest: `elapsed_wall_ceiling_sec=18000`, `output_dir_byte_ceiling=1200000000`, `byte_convention=decimal_gb`
- protected untracked v9 smoke: **not touched**
- `implementation_closure_record.json`: **not created** (by design)

## Limitations

- Full 27,637-call confirmatory audit not executed (prohibited pre independent review).
- `G_b1` requires 510/510 rows; bounded smoke cannot satisfy this gate (2 B1 rows only).
- `G_n1` requires 100 negatives; smoke runs 2.
- Independent implementation review still required before closure record or full audit authorization.
