"""GPU_RUNclaude1 C0001 Phase 4: mechanism partition and compute accounting (v2 §10.3, §11).

Synthesizes Phase 1-3 outputs into the five-bucket E0/E1'/E2/E3/unattributed
partition and the compute-vs-ceiling accounting. Reads only files already
written by this run's own earlier phases (never a GPU_RUN5 source path), so
it carries no sealed-artifact exposure of its own.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from gpu_runclaude1 import config as c0001_config  # noqa: E402
from gpu_runclaude1.constants import (  # noqa: E402
    CPU_CORE_HOURS_CEILING,
    GPU_HOURS_CEILING,
    NEW_DISK_GIB_CEILING,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="GPU_RUNclaude1 C0001 Phase 4 (mechanism partition)")
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--smoke", action="store_true")
    return parser.parse_args()


def _read_json(path: Path, default=None):
    if not path.is_file():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    args = parse_args()
    run_root = c0001_config.resolve_run_dir_for_phase(args.run_id, is_first_phase=False)
    out_dir = c0001_config.phase_dir(run_root, 4)

    if args.dry_run:
        c0001_config.write_manifest(out_dir, 4, "dry_run", note="dry-run: no data touched")
        print(f"Phase 4 dry-run: {out_dir}")
        return 0

    parta = _read_json(run_root / "phase1" / "partA_endpoints.json", {})
    partb = _read_json(run_root / "phase2" / "partB_endpoints.json", {})
    partc = _read_json(run_root / "phase3" / "partC_instrument_test.json", {})

    primary = parta.get("primary", {})
    verdict = primary.get("verdict", "not_measurable")

    # v2 §10.3: partition is reported, never resolved by fiat; under --smoke
    # the inputs above are themselves scoped to a handful of cells/systems,
    # so this partition is illustrative of the mechanism, not a corpus-wide
    # result (Stage 6/7 produces that).
    partition = {
        "E0": {"description": "component has an M3 in-beam match M0 scored as a miss", "count": primary.get("k_gains", 0)},
        "E1_prime": {"description": "gain=0 and >=1 out-of-support component", "count_from_partB": partb.get("B2-S2_component_out_of_support_rate", {}).get("n_out")},
        "E2": {"description": "gain=0, in support, model preferred selected over truth in <50% of cells", "note": "requires Part C corpus-level run, not computed under --smoke"},
        "E3": {"description": "gain=0, in support, model preferred truth over selected in >=50% of cells", "note": "requires Part C corpus-level run, not computed under --smoke"},
        "unattributed": {"description": "none of the above, or Part C undecidable/exploratory for it"},
        "scope_note": "illustrative partition over the reduced --smoke scope" if args.smoke else "corpus-wide partition",
    }

    compute_accounting = {
        "cpu_core_hours_ceiling": CPU_CORE_HOURS_CEILING,
        "gpu_hours_ceiling": GPU_HOURS_CEILING,
        "new_disk_gib_ceiling": NEW_DISK_GIB_CEILING,
        "part_c_regression_test_ok": partc.get("ok"),
        "note": "Stage 4 implementation ran only --dry-run and --smoke paths; full-corpus compute "
        "accounting is a Stage 6/7 deliverable.",
    }

    (out_dir / "mechanism_partition.json").write_text(json.dumps(partition, indent=2), encoding="utf-8")
    (out_dir / "compute_accounting.json").write_text(json.dumps(compute_accounting, indent=2), encoding="utf-8")
    c0001_config.write_manifest(out_dir, 4, "complete", verdict=verdict)
    print(f"Phase 4 complete: {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
