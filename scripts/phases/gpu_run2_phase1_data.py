"""GPU_RUN2 Phase 1: generate the GNW synthetic benchmark (analytic targets only)."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from data.gnw_synthetic import (  # noqa: E402
    FAMILY_IDS,
    assert_all_teachers_within_length_eq,
    build_paired_noise_problems,
    catalogue_fingerprint,
    define_gnw_problems,
    filter_by_main_split,
    filter_by_structure_split,
    phase4_validation_panel,
    save_problem_npz,
)
from gpu_run2_runtime import (  # noqa: E402
    fingerprint_json,
    load_gpu_run2_configs,
    nesymres_paths,
    resolve_run_dir,
    utc_now,
    write_json,
)


def _load_word2id_and_length_eq(config: dict) -> tuple[dict[str, int], int]:
    import json

    import yaml

    paths = nesymres_paths(config)
    eq_setting = json.loads(paths["eq_setting"].read_text(encoding="utf-8"))
    cfg = yaml.safe_load(paths["config"].read_text(encoding="utf-8"))
    architecture = cfg.get("architecture") or {}
    length_eq = int(architecture.get("length_eq", cfg.get("length_eq", 60)))
    return {str(k): int(v) for k, v in eq_setting["word2id"].items()}, length_eq


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="GPU_RUN2 Phase 1 GNW data")
    parser.add_argument("--run-id", default=os.environ.get("LANSR_RUN_ID"))
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--n-variants", type=int)
    parser.add_argument("--n-train", type=int)
    parser.add_argument("--n-eval", type=int)
    parser.add_argument("--data-seeds", type=int, nargs="*")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = load_gpu_run2_configs()
    run_dir = resolve_run_dir(args.run_id, config=config)
    out_dir = run_dir / "phase1"
    data_dir = out_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    # Smoke needs >=3 variants/family so train/validation/test are all non-empty.
    n_variants = args.n_variants or (3 if args.smoke else int(config["n_variants_per_family"]))
    if args.smoke and n_variants < 3:
        raise ValueError("GPU_RUN2 smoke requires n_variants_per_family >= 3 for non-empty splits")
    n_train = args.n_train or (16 if args.smoke else int(config["n_train_points"]))
    n_eval = args.n_eval or (8 if args.smoke else int(config["n_eval_points"]))
    data_seeds = args.data_seeds or list(config["data_seeds"])
    if args.smoke and not args.data_seeds:
        data_seeds = [int(config["data_seeds"][0])]
    support_id = tuple(config["support_id"])
    support_ood = tuple(config["support_ood"])
    noises = [float(x) for x in config["noises"]]
    if args.smoke:
        # Match smoke_test.md: one seed bundle and noise=0.0 only.
        noises = noises[:1]

    specs = define_gnw_problems(
        n_variants_per_family=n_variants,
        variant_seed=int(config["variant_seed"]),
        family_ids=FAMILY_IDS,
    )
    word2id, length_eq = _load_word2id_and_length_eq(config)
    teacher_audit = assert_all_teachers_within_length_eq(
        specs,
        word2id,
        max_token_len=length_eq,
    )
    write_json(out_dir / "teacher_token_audit.json", teacher_audit)
    catalogue = [spec.to_dict() for spec in specs]
    write_json(out_dir / "catalogue.json", catalogue)
    write_json(
        out_dir / "splits.json",
        {
            "main": {
                "train": [s.eq_id for s in filter_by_main_split(specs, "train")],
                "validation": [s.eq_id for s in filter_by_main_split(specs, "validation")],
                "test": [s.eq_id for s in filter_by_main_split(specs, "test")],
            },
            "structure_holdout": {
                "train": [s.eq_id for s in filter_by_structure_split(specs, "train")],
                "validation": [s.eq_id for s in filter_by_structure_split(specs, "validation")],
                "test": [s.eq_id for s in filter_by_structure_split(specs, "test")],
            },
            "phase4_panel": [s.eq_id for s in phase4_validation_panel(specs)],
            "catalogue_fingerprint": catalogue_fingerprint(specs),
        },
    )
    sampled_index = []
    for data_seed in data_seeds:
        paired = build_paired_noise_problems(
            specs,
            data_seed=int(data_seed),
            noises=noises,
            n_train=n_train,
            n_eval=n_eval,
            support_id=(float(support_id[0]), float(support_id[1])),
            support_ood=(float(support_ood[0]), float(support_ood[1])),
        )
        for problem in paired:
            rel = (
                f"seed{problem.data_seed}/noise{problem.noise:g}/"
                f"{problem.spec.eq_id}.npz"
            )
            path = data_dir / rel
            save_problem_npz(problem, path)
            row = problem.to_manifest_row()
            row["file"] = rel.replace("\\", "/")
            sampled_index.append(row)
    write_json(out_dir / "index.json", sampled_index)
    manifest = {
        "phase": 1,
        "status": "complete",
        "at_utc": utc_now(),
        "n_problems": len(specs),
        "n_families": len(FAMILY_IDS),
        "n_variants_per_family": n_variants,
        "n_train_points": n_train,
        "n_eval_points": n_eval,
        "data_seeds": [int(s) for s in data_seeds],
        "noises": noises,
        "support_id": list(support_id),
        "support_ood": list(support_ood),
        "catalogue_fingerprint": catalogue_fingerprint(specs),
        "index_fingerprint": fingerprint_json(sampled_index),
        "uses_finite_difference": False,
        "analytic_targets": True,
        "oracle_only_inputs": True,
        "smoke": bool(args.smoke),
        "teacher_token_audit": {
            "max_token_len": teacher_audit["max_token_len"],
            "max_observed": teacher_audit["max_observed"],
            "n_ok": teacher_audit["n_ok"],
        },
    }
    write_json(out_dir / "manifest.json", manifest)
    print(f"Phase 1 complete: {len(specs)} problems, {len(sampled_index)} sampled records")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
