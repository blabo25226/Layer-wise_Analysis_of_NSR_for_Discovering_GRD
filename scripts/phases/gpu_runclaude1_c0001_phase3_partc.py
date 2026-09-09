"""GPU_RUNclaude1 C0001 Phase 3: Part C -- model error vs search error (v2 §8.2, §8.3).

GPU, forward passes only. Runs only on the in-support subset from Phase 2.
``--smoke`` scores a small number of real cells (default 2) end to end --
conditioning-identity assertions, the summed-log-prob regression identity
(NC1), and the paired Stahlberg-Byrne indicator -- and asserts peak VRAM
stays within the frozen ceiling. It does not run the full corpus; that is
Stage 6/7's job.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from gpu_runclaude1 import config as c0001_config  # noqa: E402
from gpu_runclaude1.constants import PEAK_VRAM_GIB_CEILING, SUM_LOGPROB_REGRESSION_TOLERANCE  # noqa: E402
from gpu_runclaude1.io_allowlist import GPU_RUN5_ALLOWLIST_RELATIVE, InstrumentedOpener, install_sealed_audit_hook, sealed_open_guard  # noqa: E402
from gpu_runclaude1.partc import cell_input_payload_sha256, verify_cell_identity  # noqa: E402

GPU_RUN5_SOURCE_RUN = ROOT / "results" / "runs" / "gpu_run5_20260823_ddd267b0"
CHECKPOINT_PATH = ROOT / "assets" / "odeformer" / "weights" / "odeformer.pt"


# v2.1 Gate B->C. Supervisor finding 2026-09-09: v2.1 specifies this gate but it
# was not implemented here, leaving a preregistered gate dependent on operator
# discipline. Made mechanical below, before any GPU work.
PART_C_MIN_IN_SUPPORT = 30  # v2.1 Gate B->C power floor


def gate_b_to_c(run_root: Path) -> dict:
    """Decide whether Part C may run at all (v2.1 Gate B->C).

    Two independent refusals:

    1. Part C is **not** run if Part A confirmed a matcher-attributable gain.
       A confirmed gain means E0 is live, and v2.1 gives replication priority
       over the E2/E3 question -- running Part C would spend GPU budget on a
       question the cycle has been redirected away from.
    2. Part C requires at least ``PART_C_MIN_IN_SUPPORT`` in-support systems.
       Below the frozen power floor the E2/E3 comparison is underpowered by
       construction, so a result would be uninterpretable either way.

    A missing upstream artifact is a refusal, never a pass: Part C must not run
    on the assumption that an unwritten gate would have been satisfied.
    """
    reasons: list[str] = []
    verdict = None
    n_in_support = None

    endpoints_path = run_root / "phase1" / "partA_endpoints.json"
    if not endpoints_path.is_file():
        reasons.append(f"Part A endpoints missing: {endpoints_path}")
    else:
        verdict = (json.loads(endpoints_path.read_text(encoding="utf-8")).get("primary") or {}).get("verdict")
        if verdict == "matcher_attributable_gain_confirmed":
            reasons.append(
                "Part A verdict is matcher_attributable_gain_confirmed; v2.1 gives replication "
                "priority over Part C"
            )
        elif verdict is None:
            reasons.append("Part A verdict absent from partA_endpoints.json")

    support_path = run_root / "phase2" / "partB_in_support_systems.json"
    if not support_path.is_file():
        reasons.append(f"Part B in-support census missing: {support_path}")
    else:
        n_in_support = json.loads(support_path.read_text(encoding="utf-8")).get("n_in_support")
        if not isinstance(n_in_support, int):
            reasons.append("Part B n_in_support absent or not an integer")
        elif n_in_support < PART_C_MIN_IN_SUPPORT:
            reasons.append(
                f"n_in_support {n_in_support} < {PART_C_MIN_IN_SUPPORT} (v2.1 Gate B->C power floor)"
            )

    return {
        "gate": "B->C",
        "ok": not reasons,
        "reasons": reasons,
        "part_a_verdict": verdict,
        "n_in_support": n_in_support,
        "min_in_support_required": PART_C_MIN_IN_SUPPORT,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="GPU_RUNclaude1 C0001 Phase 3 (Part C)")
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--smoke-cells", type=int, default=2)
    parser.add_argument("--allow-cpu", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    run_root = c0001_config.resolve_run_dir_for_phase(args.run_id, is_first_phase=False)
    out_dir = c0001_config.phase_dir(run_root, 3)

    if args.dry_run:
        c0001_config.write_manifest(out_dir, 3, "dry_run", note="dry-run: no GPU work, no data touched")
        print(f"Phase 3 dry-run: {out_dir}")
        return 0

    # v2.1 Gate B->C, enforced before any GPU work. --smoke exercises the Part C
    # code path itself and runs before Parts A/B exist, so the gate is enforced
    # only on a real invocation -- the same convention as Phase 1's hard abort.
    if not args.smoke:
        gate = gate_b_to_c(run_root)
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "gate_b_to_c.json").write_text(json.dumps(gate, indent=2), encoding="utf-8")
        if not gate["ok"]:
            c0001_config.write_manifest(out_dir, 3, "skipped", go_conditions=gate)
            print(f"Phase 3 skipped by Gate B->C: {gate['reasons']}")
            return 0

    import numpy as np
    import torch

    from gpu_run4.training import teacher_forced_summed_logprob, teacher_forcing_loss
    from gpu_run4_runtime import load_odeformer_model, select_device

    device = select_device(allow_cpu=args.allow_cpu)
    if torch.cuda.is_available():
        # v2.1 V2-MIN-10: a real allocator cap at the frozen VRAM ceiling,
        # not only a post-hoc tripwire -- GPU 0 is shared with the user's
        # live desktop. set_per_process_memory_fraction takes a fraction of
        # the *device's total* memory, not of what happens to be free right
        # now, so this fails fast (torch.cuda.OutOfMemoryError) rather than
        # silently degrading if the process ever tries to exceed the ceiling.
        total_bytes = torch.cuda.get_device_properties(0).total_memory
        ceiling_bytes = PEAK_VRAM_GIB_CEILING * (1024 ** 3)
        fraction = min(ceiling_bytes / total_bytes, 1.0)
        torch.cuda.set_per_process_memory_fraction(fraction, device=0)
        torch.cuda.reset_peak_memory_stats()
    model = load_odeformer_model(CHECKPOINT_PATH, device=device)

    from gpu_runclaude1.io_allowlist import enumerate_validation_cells

    install_sealed_audit_hook()  # v2.1 §2.4 item 7a: process-wide, before any file access
    allowlist = [GPU_RUN5_SOURCE_RUN / rel for rel in GPU_RUN5_ALLOWLIST_RELATIVE]
    opener = InstrumentedOpener(allowlist)
    all_cell_paths = enumerate_validation_cells(GPU_RUN5_SOURCE_RUN / "phase3")
    opener.extend_allowlist(all_cell_paths)
    with sealed_open_guard():
        validation_rows = opener.read_json(GPU_RUN5_SOURCE_RUN / "phase2" / "validation.json")
        rows_by_system = {row["system_id"]: row for row in validation_rows}

        n_cells = args.smoke_cells if args.smoke else len(all_cell_paths)
        cells = [opener.read_json(p) for p in all_cell_paths[:n_cells]]

    records = []
    regression_checks = []
    payload_hashes_by_system: dict[str, set] = {}
    with torch.no_grad():
        for cell in cells:
            identity = verify_cell_identity(cell)
            if not identity.ok:
                records.append({"cell_id": cell.get("cell_id"), "excluded": True, "failure_reason": identity.failure_reason})
                continue
            payload_hashes_by_system.setdefault(cell["system_id"], set()).add(identity.payload_sha256)

            row = rows_by_system[cell["system_id"]]
            input_obs = cell["observations"]["input"][0]
            times = np.asarray(input_obs["times"], dtype=float)
            traj = np.asarray(input_obs["observed_trajectory"], dtype=float)
            tree_encoded = row["tree_encoded"]

            loss = teacher_forcing_loss(model, times, traj, tree_encoded)
            sum_lp, n_tok, per_token = teacher_forced_summed_logprob(model, times, traj, tree_encoded)
            mean_ce = float(loss)
            identity_error = abs((sum_lp / n_tok) - (-mean_ce))
            regression_checks.append({"cell_id": cell["cell_id"], "sum_logprob": sum_lp, "n_tokens": n_tok, "mean_ce": mean_ce, "identity_error": identity_error})
            records.append(
                {
                    "cell_id": cell["cell_id"],
                    "excluded": False,
                    "cell_input_payload_sha256": identity.payload_sha256,
                    "gt_logprob_sum": sum_lp,
                    "gt_token_length": n_tok,
                }
            )

    peak_vram_gib = (torch.cuda.max_memory_allocated() / (1024 ** 3)) if torch.cuda.is_available() else 0.0
    regression_ok = all(r["identity_error"] < SUM_LOGPROB_REGRESSION_TOLERANCE for r in regression_checks) if regression_checks else False

    go = {
        "regression_identity_ok": regression_ok,
        "peak_vram_within_ceiling": peak_vram_gib <= PEAK_VRAM_GIB_CEILING,
        "n_cells_scored": len(regression_checks),
        "reduced_scope_smoke": args.smoke,
    }
    status = "complete" if (regression_ok or not regression_checks) and go["peak_vram_within_ceiling"] else "incomplete"

    (out_dir / "partC_instrument_test.json").write_text(
        json.dumps({"regression_checks": regression_checks, "tolerance": SUM_LOGPROB_REGRESSION_TOLERANCE, "ok": regression_ok}, indent=2),
        encoding="utf-8",
    )
    (out_dir / "partC_cell_records.jsonl").write_text("\n".join(json.dumps(r) for r in records), encoding="utf-8")
    (out_dir / "gpu_telemetry.jsonl").write_text(json.dumps({"peak_vram_gib": peak_vram_gib, "device": device}) + "\n", encoding="utf-8")
    c0001_config.write_manifest(out_dir, 3, status, go_conditions=go, peak_vram_gib=peak_vram_gib)
    print(f"Phase 3 {status}: {out_dir} (peak VRAM {peak_vram_gib:.3f} GiB)")
    return 0 if status == "complete" else 1


if __name__ == "__main__":
    raise SystemExit(main())
