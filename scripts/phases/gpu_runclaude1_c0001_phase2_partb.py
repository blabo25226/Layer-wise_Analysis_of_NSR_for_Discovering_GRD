"""GPU_RUNclaude1 C0001 Phase 2: Part B -- generator-support accounting (v2 §8.1).

CPU-only, deterministic census over the 320 train+validation truths (or, for
``--smoke``, the 80 validation truths only). Every value is a function of a
fixed corpus; intervals here describe generator sampling variability, not
measurement error (``interval_interpretation:
"generator_sampling_not_measurement_error"``, v2 §8.1).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from gpu_runclaude1 import config as c0001_config  # noqa: E402
from gpu_runclaude1.io_allowlist import GPU_RUN5_ALLOWLIST_RELATIVE, InstrumentedOpener, install_sealed_audit_hook, sealed_open_guard  # noqa: E402
from gpu_runclaude1.ladder import wilson_interval  # noqa: E402
from gpu_runclaude1.partb import analyze_system  # noqa: E402

GPU_RUN5_SOURCE_RUN = ROOT / "results" / "runs" / "gpu_run5_20260823_ddd267b0"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="GPU_RUNclaude1 C0001 Phase 2 (Part B)")
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--smoke", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    run_root = c0001_config.resolve_run_dir_for_phase(args.run_id, is_first_phase=False)
    out_dir = c0001_config.phase_dir(run_root, 2)

    if args.dry_run:
        c0001_config.write_manifest(out_dir, 2, "dry_run", note="dry-run: no data touched")
        print(f"Phase 2 dry-run: {out_dir}")
        return 0

    install_sealed_audit_hook()  # v2.1 §2.4 item 7a: process-wide, before any file access
    allowlist = [GPU_RUN5_SOURCE_RUN / rel for rel in GPU_RUN5_ALLOWLIST_RELATIVE]
    opener = InstrumentedOpener(allowlist)
    with sealed_open_guard():
        validation_rows = opener.read_json(GPU_RUN5_SOURCE_RUN / "phase2" / "validation.json")
        train_rows = [] if args.smoke else opener.read_json(GPU_RUN5_SOURCE_RUN / "phase2" / "train.json")

    all_rows = validation_rows + train_rows
    component_records = []
    for row in all_rows:
        for record in analyze_system(row):
            component_records.append(
                {
                    "system_id": record.system_id,
                    "family": row["family"],
                    "split": row["split"],
                    "component_index": record.component_index,
                    "u_mult": record.u_mult,
                    "u_affine": record.u_affine,
                    "u_min": record.u_min,
                    "in_support": record.in_support,
                    "realized_hill_exponents": list(record.realized_hill_exponents),
                    "unary_depth": record.unary_depth,
                    "binary_ops_per_dim": record.binary_ops_per_dim,
                    "uses_only_in_support_operators": record.uses_only_in_support_operators,
                    "affine_available": record.affine_available,
                    "n_rewrite_attempts": len(record.rewrite_attempts),
                }
            )

    validation_components = [r for r in component_records if r["split"] == "validation"]
    n_val = len(validation_components)
    n_out = sum(1 for r in validation_components if not r["in_support"])
    component_rate = (n_out / n_val) if n_val else float("nan")
    component_wilson = wilson_interval(n_out, n_val) if n_val else (float("nan"), float("nan"))

    systems_out = {}
    for r in validation_components:
        systems_out.setdefault(r["system_id"], True)
        systems_out[r["system_id"]] = systems_out[r["system_id"]] and r["in_support"]
    n_sys = len(systems_out)
    n_sys_out = sum(1 for ok in systems_out.values() if not ok)
    system_wilson = wilson_interval(n_sys_out, n_sys) if n_sys else (float("nan"), float("nan"))

    endpoints = {
        "B2-S1_system_out_of_support_rate": {
            "n": n_sys,
            "n_out": n_sys_out,
            "rate": (n_sys_out / n_sys) if n_sys else float("nan"),
            "wilson_95": list(system_wilson),
            "interval_interpretation": "generator_sampling_not_measurement_error",
        },
        "B2-S2_component_out_of_support_rate": {
            "n": n_val,
            "n_out": n_out,
            "rate": component_rate,
            "wilson_95": list(component_wilson),
            "interval_interpretation": "generator_sampling_not_measurement_error",
        },
        "note": "out of support is scoped to the preregistered rewrite set B-R1..B-R4 (v2 §8.1); "
        "never claimed as out of support absolutely.",
        "reduced_to_validation_only_smoke": args.smoke,
    }

    (out_dir / "partB_component_records.jsonl").write_text(
        "\n".join(json.dumps(r) for r in component_records), encoding="utf-8"
    )
    (out_dir / "partB_endpoints.json").write_text(json.dumps(endpoints, indent=2), encoding="utf-8")
    n_in_support_systems = [sid for sid, ok in systems_out.items() if ok]
    (out_dir / "partB_in_support_systems.json").write_text(
        json.dumps({"n_in_support": len(n_in_support_systems), "system_ids": n_in_support_systems}, indent=2),
        encoding="utf-8",
    )
    c0001_config.write_manifest(out_dir, 2, "complete", n_components=len(component_records), n_validation_components=n_val)
    print(f"Phase 2 complete: {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
