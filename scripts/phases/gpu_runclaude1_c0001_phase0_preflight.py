"""GPU_RUNclaude1 C0001 Phase 0: Gate 0 preflight (v2 §10.1, §11.1).

Writes environment/checkpoint/firewall audits and the Part A cost
calibration. Never touches a sealed path (v2 §2.4): every read here goes
through :class:`gpu_runclaude1.io_allowlist.InstrumentedOpener` inside a
:func:`gpu_runclaude1.io_allowlist.sealed_open_guard` block, and
``sealed_paths_read`` is written as the computed field the opener reports,
never a hardcoded ``[]``.

``--dry-run`` writes a dummy manifest only. ``--smoke`` runs every real
check but with a small calibration sample (8 candidates, 1/family) instead
of the frozen 400/50-per-family Gate-0 sample, so Stage 4 can demonstrate the
mechanism without pre-empting Stage 6/7's real calibration run.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from gpu_run2_runtime import cpu_identity, git_info, sha256_file  # noqa: E402
from gpu_run3_runtime import software_versions  # noqa: E402
from gpu_run4_runtime import select_device  # noqa: E402
from gpu_runclaude1 import config as c0001_config  # noqa: E402
from gpu_runclaude1.agreement import collect_agreement_pairs, run_agreement_test  # noqa: E402
from gpu_runclaude1.calibration import run_calibration, sample_candidates  # noqa: E402
from gpu_runclaude1.constants import (  # noqa: E402
    CALIBRATION_N_CANDIDATES,
    CALIBRATION_PER_FAMILY,
    CALIBRATION_SEED,
    CHECKPOINT_SHA256,
    GPU_HOURS_CEILING,
    N_STORED_CANDIDATES,
    PART_A_PROJECTED_CEILING_CORE_HOURS,
    PEAK_VRAM_GIB_CEILING,
)
from gpu_runclaude1.io_allowlist import (  # noqa: E402
    install_sealed_audit_hook,
    GPU_RUN5_ALLOWLIST_RELATIVE,
    InstrumentedOpener,
    enumerate_sealed_paths,
    enumerate_validation_cells,
    sealed_open_guard,
)

GPU_RUN5_SOURCE_RUN = ROOT / "results" / "runs" / "gpu_run5_20260823_ddd267b0"
CHECKPOINT_PATH = ROOT / "assets" / "odeformer" / "weights" / "odeformer.pt"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="GPU_RUNclaude1 C0001 Phase 0 preflight")
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--allow-cpu", action="store_true")
    return parser.parse_args()


def _gpu_status(index: int = 0) -> dict:
    try:
        out = subprocess.check_output(
            [
                "nvidia-smi",
                f"--id={index}",
                "--query-gpu=temperature.gpu,memory.total,memory.used,memory.free",
                "--format=csv,noheader,nounits",
            ],
            text=True,
        ).strip()
        temp, total, used, free = (int(v.strip()) for v in out.split(","))
        return {"gpu_index": index, "temperature_c": temp, "memory_total_mib": total, "memory_used_mib": used, "memory_free_mib": free}
    except (OSError, subprocess.CalledProcessError, ValueError):
        return {"gpu_index": index, "error": "nvidia-smi unavailable"}


def _disk_free_gib(path: Path) -> float:
    import shutil

    usage = shutil.disk_usage(path)
    return round(usage.free / (1024 ** 3), 2)


def environment_audit() -> dict:
    return {
        "git": git_info(),
        "cpu": cpu_identity(),
        "software_versions": software_versions(),
        "gpu": _gpu_status(0),
        "disk_free_gib": _disk_free_gib(ROOT),
    }


def checkpoint_audit(opener: InstrumentedOpener) -> dict:
    actual_sha256 = sha256_file(CHECKPOINT_PATH)
    return {
        "path": str(CHECKPOINT_PATH),
        "sha256": actual_sha256,
        "sha256_matches_frozen": actual_sha256 == CHECKPOINT_SHA256,
        "size_bytes": CHECKPOINT_PATH.stat().st_size,
    }


def firewall_self_test(opener: InstrumentedOpener) -> dict:
    """v2 §2.4 item 5: the C0001-specific firewall test, run here so its
    result is part of the Gate 0 record, not only the pytest suite.
    """
    allowlist_has_no_sealed = not any(
        p.name.lower().startswith("sealed") for p in opener.allowlist
    )
    sealed_paths_read = opener.sealed_paths_read
    cells = enumerate_validation_cells(GPU_RUN5_SOURCE_RUN / "phase3")
    ledger_sealed_files = enumerate_sealed_paths([ROOT / "results" / "runs"])
    return {
        "allowlist_has_no_sealed_path": allowlist_has_no_sealed,
        "sealed_paths_read": sealed_paths_read,
        "sealed_paths_read_count": len(sealed_paths_read),
        "validation_cell_count": len(cells),
        "validation_cell_count_ok": len(cells) == 960,
        "known_sealed_files_on_disk": [str(p) for p in ledger_sealed_files],
        "known_sealed_files_count": len(ledger_sealed_files),
        "ok": allowlist_has_no_sealed and len(sealed_paths_read) == 0 and len(cells) == 960,
    }


def main() -> int:
    args = parse_args()
    run_id = args.run_id or c0001_config.run_id_for()
    run_root = c0001_config.resolve_run_dir_for_phase(args.run_id, is_first_phase=True)
    out_dir = c0001_config.phase_dir(run_root, 0)

    if args.dry_run:
        c0001_config.write_manifest(out_dir, 0, "dry_run", note="dry-run: no data touched")
        print(f"Phase 0 dry-run: {out_dir}")
        return 0

    install_sealed_audit_hook()  # v2.1 §2.4 item 7a: process-wide, before any file access
    allowlist = [GPU_RUN5_SOURCE_RUN / rel for rel in GPU_RUN5_ALLOWLIST_RELATIVE]
    opener = InstrumentedOpener(allowlist)
    opener.extend_allowlist(enumerate_validation_cells(GPU_RUN5_SOURCE_RUN / "phase3"))

    with sealed_open_guard():
        env = environment_audit()
        checkpoint = checkpoint_audit(opener)
        firewall = firewall_self_test(opener)

        all_candidates = opener.read_json(GPU_RUN5_SOURCE_RUN / "phase3" / "all_candidates.json")
        n_calibration = 8 if args.smoke else CALIBRATION_N_CANDIDATES
        per_family = 1 if args.smoke else CALIBRATION_PER_FAMILY
        sampled = sample_candidates(all_candidates, n_total=n_calibration, per_family=per_family, seed=CALIBRATION_SEED)
        calibration = run_calibration(sampled, n_stored_candidates=N_STORED_CANDIDATES)

        # Gate 0 item 11 (v2.1 §7.4 V2-MAJ-2): the M3-implementation agreement
        # test. Scope note (disclosed): v2.1 names a target corpus of 910
        # pairs; collect_agreement_pairs realizes whatever size the actual
        # construction rules produce on the rows given (measured on the full
        # 80-system validation corpus: 1178 pairs -- 170 PC0 identity pairs
        # plus 1008 from the other eight construction rules -- which exceeds
        # 910). Under --smoke a small subset keeps this fast; the realized n
        # is always reported, never silently presented as 910.
        validation_rows = opener.read_json(GPU_RUN5_SOURCE_RUN / "phase2" / "validation.json")
        agreement_rows = validation_rows[:8] if args.smoke else validation_rows
        agreement_pairs = collect_agreement_pairs(agreement_rows)
        agreement_result = run_agreement_test(agreement_pairs)

        fingerprints = opener.fingerprints()

    device = select_device(allow_cpu=args.allow_cpu)

    go = {
        "checkpoint_sha256_ok": checkpoint["sha256_matches_frozen"],
        "firewall_ok": firewall["ok"],
        "gpu_temperature_ok": env["gpu"].get("temperature_c", 999) < 70 if "error" not in env["gpu"] else args.allow_cpu,
        "gpu_free_vram_ok": env["gpu"].get("memory_free_mib", 0) >= 6144 if "error" not in env["gpu"] else args.allow_cpu,
        "disk_free_ok": env["disk_free_gib"] >= 40.0,
        "calibration_projection_within_ceiling": (
            calibration.projected_core_hours <= PART_A_PROJECTED_CEILING_CORE_HOURS if not args.smoke else True
        ),
        "m3_agreement_test_ok": agreement_result.ok,
    }
    status = "complete" if all(go.values()) else "incomplete"

    payload = {
        "device": device,
        "environment_audit": env,
        "checkpoint_audit": checkpoint,
        "firewall_test": firewall,
        "cost_calibration": {
            "n_candidates": calibration.n_candidates,
            "mean_sec": calibration.mean_sec,
            "median_sec": calibration.median_sec,
            "p95_sec": calibration.p95_sec,
            "per_family_mean_sec": calibration.per_family_mean_sec,
            "projected_core_hours": calibration.projected_core_hours,
            "note": "timings and failure labels only; no match indicator produced during calibration is retained (v2 §11.1)",
            "reduced_smoke_sample": args.smoke,
        },
        "input_fingerprints": fingerprints,
        "go_conditions": go,
    }
    (out_dir / "environment_audit.json").write_text(json.dumps(env, indent=2), encoding="utf-8")
    (out_dir / "checkpoint_audit.json").write_text(json.dumps(checkpoint, indent=2), encoding="utf-8")
    (out_dir / "firewall_test.json").write_text(json.dumps(firewall, indent=2), encoding="utf-8")
    (out_dir / "partA_cost_calibration.json").write_text(json.dumps(payload["cost_calibration"], indent=2), encoding="utf-8")
    (out_dir / "input_fingerprints.json").write_text(json.dumps(fingerprints, indent=2), encoding="utf-8")
    (out_dir / "m3_agreement_test.json").write_text(
        json.dumps(
            {
                "n_pairs_realized": agreement_result.n_pairs,
                "n_pairs_target_v2_1": 910,
                "n_disagreements": agreement_result.n_disagreements,
                "disagreement_rate": agreement_result.disagreement_rate,
                "by_source": agreement_result.by_source,
                "disagreements": list(agreement_result.disagreements),
                "reduced_scope_smoke": args.smoke,
                "ok": agreement_result.ok,
                "note": (
                    "Gate 0 item 11 (v2.1 V2-MAJ-2). Realized n reported explicitly, never presented "
                    "as the frozen 910 if it differs; see GPU_RUNclaude1/analyses/C0001_implementation_notes.md."
                ),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    c0001_config.write_manifest(out_dir, 0, status, go_conditions=go, run_root=str(run_root))
    print(f"Phase 0 {status}: {out_dir}")
    if status != "complete":
        print(f"Go conditions failed: {[k for k, v in go.items() if not v]}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
