"""GPU_RUN5 Phase 2: build the closed GRN corpus and seal test artifacts."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from evaluation.gpu_run5_structure import classify_formula  # noqa: E402
from gpu_run2_runtime import git_info, sha256_file, write_json  # noqa: E402
from gpu_run4_runtime import load_odeformer_model  # noqa: E402
from gpu_run5.config import budget, load_config, phase_dir, read_json, run_dir, write_manifest  # noqa: E402
from gpu_run5.grn import FAMILIES, generate_corpus  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="GPU_RUN5 Phase 2 closed GRN corpus")
    parser.add_argument("--run-id", default=os.environ.get("LANSR_RUN_ID"))
    parser.add_argument("--smoke", action="store_true")
    return parser.parse_args()


def _encode_teacher(model, row: dict) -> dict:
    raw_tokens = row["teacher_prefix"].replace("|", ",|,").split(",")
    tree = model.env.equation_encoder.decode(raw_tokens)
    encoded = model.env.equation_encoder.encode(tree) if tree is not None else []
    decoded = model.env.equation_encoder.decode(encoded) if encoded else None
    structure = classify_formula(row["teacher_prefix"])
    return {
        **row,
        "teacher_infix": decoded.infix() if decoded is not None else None,
        "tree_encoded": list(encoded),
        "teacher_token_length": len(encoded),
        "teacher_roundtrip_prefix": decoded.prefix() if decoded is not None else None,
        "structure": structure,
        "teacher_valid": bool(decoded is not None and structure["valid"]),
    }


def _checksums(rows: list[dict]) -> set[str]:
    return {item["checksum"] for row in rows for item in row["trajectories"]}


def _parameter_fingerprints(rows: list[dict]) -> set[str]:
    return {
        __import__("hashlib").sha256(
            json.dumps(row["sampled_parameters"], sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        for row in rows
    }


def _component_skeletons(rows: list[dict]) -> set[str]:
    values: set[str] = set()
    for row in rows:
        values.update(
            part for part in row["structure"]["exponent_aware_skeleton"].split(" | ") if part
        )
    return values


def main() -> int:
    args = parse_args()
    config = load_config()
    root = run_dir(args.run_id)
    if read_json(root / "phase1" / "manifest.json", {}).get("status") != "complete":
        raise RuntimeError("Phase 1 is not complete")
    out = phase_dir(args.run_id, 2)
    selected_budget = budget(config, args.smoke)
    grn = config["grn"]
    variants = {
        "train": int(selected_budget["train_variants_per_family"]),
        "validation": int(selected_budget["validation_variants_per_family"]),
        "test": int(selected_budget["test_variants_per_family"]),
    }
    bundle = config["seed_bundles"][0]
    corpus = generate_corpus(
        variants=variants,
        n_points=int(selected_budget["n_points"]),
        t_span=tuple(grn["t_span"]),
        seed=int(bundle["data_seed"]),
        trajectory_seed=int(bundle["trajectory_seed"]),
        rtol=float(grn["solve_rtol"]),
        atol=float(grn["solve_atol"]),
        minimum_variance=float(grn["minimum_variance"]),
        maximum_abs_state=float(grn["maximum_abs_state"]),
    )
    model = load_odeformer_model(ROOT / str(config["odeformer_checkpoint"]), device="cpu")
    rows = [_encode_teacher(model, row) for row in corpus["records"]]
    splits = {name: [row for row in rows if row["split"] == name] for name in variants}
    expected = {name: count * len(FAMILIES) for name, count in variants.items()}
    system_sets = {name: {row["system_id"] for row in items} for name, items in splits.items()}
    checksum_sets = {name: _checksums(items) for name, items in splits.items()}
    system_overlap = {
        "train_validation": sorted(system_sets["train"] & system_sets["validation"]),
        "train_test": sorted(system_sets["train"] & system_sets["test"]),
        "validation_test": sorted(system_sets["validation"] & system_sets["test"]),
    }
    trajectory_overlap = {
        "train_validation": sorted(checksum_sets["train"] & checksum_sets["validation"]),
        "train_test": sorted(checksum_sets["train"] & checksum_sets["test"]),
        "validation_test": sorted(checksum_sets["validation"] & checksum_sets["test"]),
    }
    parameter_sets = {name: _parameter_fingerprints(items) for name, items in splits.items()}
    parameter_overlap = {
        "train_validation": sorted(parameter_sets["train"] & parameter_sets["validation"]),
        "train_test": sorted(parameter_sets["train"] & parameter_sets["test"]),
        "validation_test": sorted(parameter_sets["validation"] & parameter_sets["test"]),
    }
    holdout = {
        "train": [row for row in splits["train"] if row["family"] in {"R01", "R02", "R03", "R04", "R05"}],
        "validation": [row for row in splits["validation"] if row["family"] == "R06"],
        "test": [row for row in splits["test"] if row["family"] in {"R07", "R08"}],
    }
    holdout_skeletons = {name: {row["structure"]["exponent_aware_skeleton"] for row in items} for name, items in holdout.items()}
    holdout_overlap = sorted(holdout_skeletons["train"] & holdout_skeletons["test"])
    holdout_component_skeletons = {name: _component_skeletons(items) for name, items in holdout.items()}
    holdout_component_overlap = sorted(holdout_component_skeletons["train"] & holdout_component_skeletons["test"])

    write_json(out / "train.json", splits["train"])
    write_json(out / "validation.json", splits["validation"])
    write_json(out / "sealed_test.json", splits["test"])
    write_json(out / "family_holdout_train.json", holdout["train"])
    write_json(out / "family_holdout_validation.json", holdout["validation"])
    write_json(out / "sealed_family_holdout_test.json", holdout["test"])
    write_json(out / "rejections.json", corpus["rejections"])
    audit = {
        "counts": {name: len(items) for name, items in splits.items()},
        "expected_counts": expected,
        "rejection_rate": corpus["rejection_rate"],
        "corpus_fingerprint": corpus["fingerprint"],
        "system_overlap": system_overlap,
        "trajectory_overlap": trajectory_overlap,
        "parameter_variant_overlap": parameter_overlap,
        "family_holdout_counts": {name: len(items) for name, items in holdout.items()},
        "family_holdout_train_test_system_skeleton_overlap": holdout_overlap,
        "family_holdout_train_test_component_skeleton_overlap": holdout_component_overlap,
        "family_holdout_system_structure_ood": not holdout_overlap,
        "family_holdout_component_structure_ood": not holdout_component_overlap,
        "family_holdout_label": "system-structure-OOD_partial-component-overlap" if not holdout_overlap and holdout_component_overlap else "structure-OOD" if not holdout_overlap else "partial-family-holdout",
        "max_teacher_token_length": max(row["teacher_token_length"] for row in rows),
        "all_teacher_valid": all(row["teacher_valid"] for row in rows),
        "all_teacher_prefix_roundtrips_exactly": all(
            row["teacher_roundtrip_prefix"] == row["teacher_prefix"].replace("|", ",|,")
            for row in rows
        ),
        "corpus_seed_bundle_index": 0,
        "corpus_seed_policy": "one frozen corpus shared across all paired model/candidate bundles; per-bundle data_seed controls training order, not evaluation-system identity",
        "test_generated_not_evaluated": True,
    }
    go = {
        "counts_ok": audit["counts"] == expected,
        "rejection_rate_ok": corpus["rejection_rate"] < float(grn["maximum_rejection_rate"]),
        "teacher_ok": audit["all_teacher_valid"] and audit["all_teacher_prefix_roundtrips_exactly"] and audit["max_teacher_token_length"] <= 200,
        "no_system_leakage": not any(system_overlap.values()),
        "no_parameter_variant_leakage": not any(parameter_overlap.values()),
        "no_trajectory_leakage": not any(trajectory_overlap.values()),
        "sealed_test_written": (out / "sealed_test.json").is_file(),
        "family_holdout_separate": bool(holdout["train"] and holdout["validation"] and holdout["test"]),
    }
    write_json(out / "audit.json", audit)
    write_json(out / "go.json", go)
    status = "complete" if all(go.values()) else "incomplete"
    write_manifest(
        out, 2, status, go_conditions=go, audit=audit, git=git_info(),
        test_accessed=False, test_generated=True,
        artifact_sha256={name: sha256_file(out / name) for name in ["train.json", "validation.json", "sealed_test.json"]},
    )
    print(f"GPU_RUN5 Phase 2 {status}: counts={audit['counts']} rejection={audit['rejection_rate']:.3f}")
    return 0 if status == "complete" else 1


if __name__ == "__main__":
    raise SystemExit(main())
