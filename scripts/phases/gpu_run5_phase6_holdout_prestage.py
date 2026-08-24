"""Sign an R06-only Phase 3 selection protocol before GPU_RUN5 Phase 6.

The process has a deliberately narrow input allowlist: Phase 2 provenance,
the family-holdout validation corpus, the Phase 3 config snapshot, and the 120
R06 cell shards derived explicitly from those system IDs and the frozen grid.
No Phase 3 aggregate or outcome manifest is read.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from time import perf_counter
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from gpu_run2_runtime import (  # noqa: E402
    fingerprint_json,
    git_info,
    sha256_file,
    utc_now,
    write_json as _write_json,
)
from gpu_run5.config import read_json, sanitize_nonfinite  # noqa: E402
from gpu_run5.phase6 import (  # noqa: E402
    build_holdout_selection_artifact,
    corruption_grid,
    phase3_cell_filename,
    verify_holdout_selection_artifact,
)


EXPECTED_R06_SYSTEM_IDS_SHA256 = (
    "7912465f19dd4c2c474c13872985d3c185df227d97f0da510a8b71d98a3d9ade"
)
EXPECTED_R06_CELL_IDS_SHA256 = (
    "33da3beb010d2026d997a2ced25e60f610ba52f5718b05a0f30d6a0e2f9a93f5"
)
EXPECTED_R06_FILENAME_SHA256_INDEX_SHA256 = (
    "7eb37730157d94923336989dbaf88211f3f8d9b495f1b2c009a93415a4ef4945"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", default=os.environ.get("LANSR_RUN_ID"))
    parser.add_argument("--run-dir", default=os.environ.get("LANSR_RUN_DIR"))
    return parser.parse_args()


def write_json(path: Path, payload: Any) -> Path:
    return _write_json(path, sanitize_nonfinite(payload))


def _run_root(args: argparse.Namespace) -> Path:
    """Resolve the run without loading the mutable current campaign config."""
    if args.run_dir:
        return Path(str(args.run_dir)).expanduser().resolve()
    if args.run_id:
        run_id = str(args.run_id)
        if Path(run_id).name != run_id or run_id in {".", ".."}:
            raise ValueError("--run-id must be one path-safe directory name")
        return (ROOT / "results" / "runs" / run_id).resolve()
    raise ValueError("R06 pre-stage requires --run-id or --run-dir/LANSR_RUN_DIR")


def main() -> int:
    args = parse_args()
    started_utc, started_clock = utc_now(), perf_counter()
    root = _run_root(args)
    if not root.is_dir():
        raise FileNotFoundError(f"GPU_RUN5 run directory does not exist: {root}")
    git = git_info()
    if git["status_short"]:
        raise RuntimeError(
            f"authoritative R06 pre-stage requires a clean worktree: {git['status_short']}"
        )

    phase2_manifest_path = root / "phase2" / "manifest.json"
    holdout_validation_path = root / "phase2" / "family_holdout_validation.json"
    phase3_config_path = root / "phase3" / "config_snapshot.json"
    phase2_manifest = read_json(phase2_manifest_path, {})
    if (
        phase2_manifest.get("status") != "complete"
        or not all(phase2_manifest.get("go_conditions", {}).values())
        or phase2_manifest.get("test_accessed") is not False
    ):
        raise RuntimeError("Phase 2 provenance is not complete with an intact firewall")
    if phase2_manifest.get("artifact_sha256", {}).get(
        "family_holdout_validation.json"
    ) != sha256_file(holdout_validation_path):
        raise RuntimeError("family-holdout validation hash does not match Phase 2")
    holdout = read_json(holdout_validation_path)
    if not isinstance(holdout, list) or not holdout:
        raise RuntimeError("family-holdout validation corpus is missing")
    expected_family = "R06"
    if {str(row.get("family")) for row in holdout} != {expected_family}:
        raise RuntimeError("R06 pre-stage received another family")
    phase3_config = read_json(phase3_config_path)
    if not isinstance(phase3_config, dict):
        raise RuntimeError("Phase 3 config snapshot is missing")
    required_config_keys = {
        "odeformer_checkpoint_sha256",
        "paper_protocol",
        "seed_bundles",
        "corruptions",
        "selection",
        "full",
    }
    if not required_config_keys.issubset(phase3_config):
        raise RuntimeError("Phase 3 selection config snapshot is incomplete")

    systems = sorted(str(row["system_id"]) for row in holdout)
    cell_sources: list[tuple[str, Path]] = []
    expected_cell_ids: list[str] = []
    for bundle_index in range(len(phase3_config["seed_bundles"])):
        for system in systems:
            for sigma, rho in corruption_grid(phase3_config):
                filename = phase3_cell_filename(
                    system=system,
                    bundle_index=bundle_index,
                    noise_sigma=sigma,
                    subsample_rho=rho,
                )
                label = (Path("phase3") / "cells" / filename).as_posix()
                cell_sources.append((label, root / label))
                expected_cell_ids.append(filename.removesuffix(".json"))
    if len(cell_sources) != 120:
        raise RuntimeError(f"R06 pre-stage requires exactly 120 shards, got {len(cell_sources)}")

    artifact = build_holdout_selection_artifact(
        cell_sources=cell_sources,
        expected_cell_ids=expected_cell_ids,
        expected_system_ids=systems,
        candidate_lambdas=phase3_config["selection"]["complexity_lambdas"],
        failure_penalty=float(
            phase3_config["selection"]["trajectory_nrmse_failure_penalty"]
        ),
        source_phase2_manifest_sha256=sha256_file(phase2_manifest_path),
        source_phase3_config_snapshot_sha256=sha256_file(phase3_config_path),
        source_holdout_validation_sha256=sha256_file(holdout_validation_path),
        config_fingerprint=fingerprint_json(phase3_config),
        git_provenance=git,
        expected_beam_size=int(phase3_config["full"]["beam_size"]),
        expected_checkpoint_sha256=str(
            phase3_config["odeformer_checkpoint_sha256"]
        ),
    )
    out = root / "phase6_holdout_prestage"
    out.mkdir(parents=True, exist_ok=True)
    selection_path = write_json(out / "selection.json", artifact)
    persisted = read_json(selection_path)
    protocol = verify_holdout_selection_artifact(
        persisted,
        expected_cell_ids=expected_cell_ids,
        expected_system_ids=systems,
        expected_phase2_manifest_sha256=sha256_file(phase2_manifest_path),
        expected_phase3_config_snapshot_sha256=sha256_file(phase3_config_path),
        expected_holdout_validation_sha256=sha256_file(holdout_validation_path),
        source_root=root,
    )
    expected_system_ids_sha = fingerprint_json(systems)
    expected_cell_ids_sha = fingerprint_json(sorted(expected_cell_ids))
    go = {
        "safe_input_allowlist_only": True,
        "R06_family_only": artifact["source_family"] == expected_family,
        "exact_120_shards": artifact["source_cell_count"] == 120,
        "system_id_set_hash_exact": artifact["source_system_ids_sha256"]
        == expected_system_ids_sha
        == EXPECTED_R06_SYSTEM_IDS_SHA256,
        "cell_id_set_hash_exact": artifact["source_cell_ids_sha256"]
        == expected_cell_ids_sha
        == EXPECTED_R06_CELL_IDS_SHA256,
        "ordered_filename_hash_index_exact": artifact[
            "source_filename_sha256_index_sha256"
        ]
        == EXPECTED_R06_FILENAME_SHA256_INDEX_SHA256,
        "all_candidate_set_hashes_recomputed": all(
            len(str(row["candidate_set_sha256"])) == 64
            for row in artifact["source_artifacts"]
        ),
        "paired_cache_projection_and_beam_verified": int(
            artifact["source_phase3_cache_identity_projection"]["beam_size"]
        )
        == int(phase3_config["full"]["beam_size"]),
        "signed_artifact_reloaded": protocol["selection_artifact_signature_sha256"]
        == artifact["signature_sha256"],
        "test_not_accessed": True,
        "git_commit_and_cleanliness_stable": git_info()["commit"] == git["commit"]
        and not git_info()["status_short"],
    }
    status = "complete" if all(go.values()) else "incomplete"
    manifest = sanitize_nonfinite(
        {
            "campaign": "GPU_RUN5",
            "phase": "6_holdout_prestage",
            "status": status,
            "at_utc": utc_now(),
            "started_utc": started_utc,
            "wall_time_sec": perf_counter() - started_clock,
            "git": git_info(),
            "go_conditions": go,
            "test_accessed": False,
            "safe_sources": {
                "phase2_manifest_sha256": sha256_file(phase2_manifest_path),
                "family_holdout_validation_sha256": sha256_file(
                    holdout_validation_path
                ),
                "phase3_config_snapshot_sha256": sha256_file(phase3_config_path),
            },
            "source_access_audit": {
                "allowed_fixed_files": [
                    "phase2/manifest.json",
                    "phase2/family_holdout_validation.json",
                    "phase3/config_snapshot.json",
                ],
                "allowed_shard_paths": [row["path"] for row in artifact["source_artifacts"]],
                "allowed_shard_count": len(artifact["source_artifacts"]),
                "phase3_aggregate_manifest_accessed": False,
                "phase3_aggregate_outcomes_accessed": False,
                "R07_or_R08_shard_accessed": False,
                "directory_discovery_used": False,
                "current_campaign_config_accessed": False,
            },
            "selection_artifact_sha256": sha256_file(selection_path),
            "selection_signature_sha256": artifact["signature_sha256"],
            "source_system_ids_sha256": artifact["source_system_ids_sha256"],
            "source_cell_ids_sha256": artifact["source_cell_ids_sha256"],
            "source_artifact_index_sha256": artifact[
                "source_artifact_index_sha256"
            ],
            "source_path_sha256_index_sha256": artifact[
                "source_path_sha256_index_sha256"
            ],
            "source_filename_sha256_index_sha256": artifact[
                "source_filename_sha256_index_sha256"
            ],
            "source_artifacts": artifact["source_artifacts"],
            "chosen_lambda": artifact["chosen_lambda"],
            "audit": artifact["audit"],
            "retrospective_signing_limitation": artifact[
                "retrospective_signing_limitation"
            ],
        }
    )
    write_json(out / "manifest.json", manifest)
    print(
        f"GPU_RUN5 R06 pre-stage {status}: cells={artifact['source_cell_count']} "
        f"lambda={artifact['chosen_lambda']:g}",
        flush=True,
    )
    return 0 if status == "complete" else 1


if __name__ == "__main__":
    raise SystemExit(main())
