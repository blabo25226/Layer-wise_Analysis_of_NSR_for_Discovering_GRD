"""GPU_RUN5 Phase 4: official corpus and observational layer analyses."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from time import perf_counter
from typing import Any

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from gpu_run2_runtime import fingerprint_json, git_info, sha256_file, utc_now, write_json  # noqa: E402
from gpu_run3_runtime import software_versions  # noqa: E402
from gpu_run4.architecture import inventory_odeformer  # noqa: E402
from gpu_run4.corpus import build_analysis_corpus, select_fixed_panel  # noqa: E402
from gpu_run4.training import teacher_forcing_loss  # noqa: E402
from gpu_run4_runtime import load_odeformer_model, select_device  # noqa: E402
from gpu_run5.config import (  # noqa: E402
    budget, load_config, phase_dir, read_json, run_dir, sanitize_nonfinite, write_manifest,
)
from gpu_run5.observational import (  # noqa: E402
    collect_layer_features, decoder_logit_lens, encoder_intermediate_greedy,
    fit_layer_probes, gradient_norms_by_layer, token_category, within_module_cka,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", default=os.environ.get("LANSR_RUN_ID"))
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--allow-cpu", action="store_true")
    return parser.parse_args()


def _serialize(row: dict[str, Any]) -> dict[str, Any]:
    return {
        **{key: value for key, value in row.items() if key not in {"times", "trajectory"}},
        "times": np.asarray(row["times"], dtype=float).tolist(),
        "trajectory": np.asarray(row["trajectory"], dtype=float).tolist(),
        "tree_encoded": list(row["tree_encoded"]) if row.get("tree_encoded") is not None else None,
    }


def _arrays(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {**row, "times": np.asarray(row["times"], dtype=float), "trajectory": np.asarray(row["trajectory"], dtype=float)}
        for row in rows
    ]


def _grn_panel(rows: list[dict[str, Any]], n: int) -> list[dict[str, Any]]:
    by_family: dict[str, list[dict[str, Any]]] = {}
    for row in sorted(rows, key=lambda item: str(item["system_id"])):
        by_family.setdefault(str(row["family"]), []).append(row)
    base = n // max(len(by_family), 1)
    remainder = n % max(len(by_family), 1)
    output = []
    for index, family in enumerate(sorted(by_family)):
        output.extend(by_family[family][: base + int(index < remainder)])
    return output[:n]


def _save_features(path: Path, prefix: str, payload: dict[str, Any]) -> None:
    arrays = {}
    for group in ("expression_features", "token_features", "expression_labels", "token_labels"):
        for key, value in payload[group].items():
            arrays[f"{group}__{key}"] = np.asarray(value)
    np.savez_compressed(path / f"{prefix}_features.npz", **arrays)


def main() -> int:
    args = parse_args()
    started_utc = utc_now()
    started_clock = perf_counter()
    config = load_config()
    chosen_budget = budget(config, args.smoke)
    root = run_dir(args.run_id)
    phase3_manifest = read_json(root / "phase3" / "manifest.json", {})
    if phase3_manifest.get("status") != "complete" or not all(phase3_manifest.get("go_conditions", {}).values()):
        raise RuntimeError("Phase 3 is not complete with every Go condition true")
    if phase3_manifest.get("test_accessed") is not False:
        raise RuntimeError("Phase 3 test firewall provenance is invalid")
    phase2_manifest = read_json(root / "phase2" / "manifest.json", {})
    phase2_validation_path = root / "phase2" / "validation.json"
    if phase2_manifest.get("artifact_sha256", {}).get("validation.json") != sha256_file(phase2_validation_path):
        raise RuntimeError("Phase 2 validation hash does not match its manifest")
    git = git_info()
    if git["status_short"]:
        raise RuntimeError(f"authoritative Phase 4 requires a clean worktree: {git['status_short']}")
    out = phase_dir(args.run_id, 4)
    write_json(out / "config_snapshot.json", config)
    device = select_device(allow_cpu=args.allow_cpu)
    checkpoint = ROOT / str(config["odeformer_checkpoint"])
    model = load_odeformer_model(checkpoint, device=device)
    environment = software_versions()
    inventory = inventory_odeformer(model)
    layers = list(inventory["ranking_layers"])
    encoder_layers = [name for name in layers if name.startswith("encoder_")]
    decoder_layers = [name for name in layers if name.startswith("decoder_")]

    corpus_identity = {
        "schema_version": "gpu_run5_official_corpus_v1", "git_commit": git["commit"],
        "config_fingerprint": fingerprint_json(config), "checkpoint_sha256": sha256_file(checkpoint),
        "environment_fingerprint": fingerprint_json(environment),
        "counts": {
            "train": int(chosen_budget["official_corpus_train"]),
            "validation": int(chosen_budget["official_corpus_validation"]),
            "test": int(chosen_budget["official_corpus_test"]),
        },
        "seed": int(config["seed_bundles"][0]["data_seed"]), "generator_train_flag": True,
    }
    corpus_paths = [out / name for name in (
        "official_train.json", "official_validation.json", "sealed_official_test.json",
        "official_corpus_meta.json", "official_corpus_identity.json",
    )]
    cached_identity = read_json(out / "official_corpus_identity.json", {})
    cached_meta = read_json(out / "official_corpus_meta.json", {})
    cache_hashes = cached_meta.get("artifact_sha256", {})
    cache_valid = (
        cached_identity == corpus_identity and all(path.is_file() for path in corpus_paths)
        and all(
            cache_hashes.get(name) == sha256_file(out / name)
            for name in ("official_train.json", "official_validation.json", "sealed_official_test.json")
        )
    )
    if cache_valid:
        train = _arrays(read_json(out / "official_train.json"))
        validation = _arrays(read_json(out / "official_validation.json"))
        corpus_meta = read_json(out / "official_corpus_meta.json")
        n_official_test = int(corpus_meta["counts"]["test"])
        corpus_wall = float(corpus_meta["corpus_wall_time_sec"])
    else:
        corpus_started = perf_counter()
        corpus = build_analysis_corpus(
            model,
            n_train=int(chosen_budget["official_corpus_train"]),
            n_validation=int(chosen_budget["official_corpus_validation"]),
            n_test=int(chosen_budget["official_corpus_test"]),
            seed=int(config["seed_bundles"][0]["data_seed"]),
        )
        corpus_wall = perf_counter() - corpus_started
        train = [row for row in corpus["records"] if row["split"] == "analysis_train"]
        validation = [row for row in corpus["records"] if row["split"] == "analysis_validation"]
        official_test = [row for row in corpus["records"] if row["split"] == "analysis_test"]
        n_official_test = len(official_test)
        write_json(out / "official_train.json", [_serialize(row) for row in train])
        write_json(out / "official_validation.json", [_serialize(row) for row in validation])
        write_json(out / "sealed_official_test.json", [_serialize(row) for row in official_test])
        corpus_meta = {
            "counts": {"train": len(train), "validation": len(validation), "test": n_official_test},
            "fingerprint": corpus["fingerprint"], "n_failures": corpus["n_failures"],
            "skeleton_leakage": corpus["skeleton_leakage"], "corpus_wall_time_sec": corpus_wall,
            "test_generated_not_evaluated": True,
            "artifact_sha256": {
                name: sha256_file(out / name)
                for name in ("official_train.json", "official_validation.json", "sealed_official_test.json")
            },
        }
        write_json(out / "official_corpus_meta.json", corpus_meta)
        write_json(out / "official_corpus_identity.json", corpus_identity)

    n_panel = int(chosen_budget["intervention_panel"])
    official_panel = select_fixed_panel(validation, n_panel, seed=int(config["seed_bundles"][0]["data_seed"]))
    grn_validation = read_json(phase2_validation_path)
    grn_panel = _grn_panel(grn_validation, n_panel)
    write_json(out / "fixed_official_validation_panel.json", [_serialize(row) for row in official_panel])
    write_json(out / "fixed_grn_validation_panel.json", grn_panel)

    ce_rows = []
    for row in validation:
        try:
            value = teacher_forcing_loss(
                model, np.asarray(row["times"]), np.asarray(row["trajectory"]), row["tree_encoded"]
            )
            ce_rows.append({"problem_id": row["problem_id"], "ce": float(value.detach().cpu()), "failure_reason": None})
        except Exception as exc:
            ce_rows.append({"problem_id": row["problem_id"], "ce": None, "failure_reason": f"{type(exc).__name__}:{exc}"})
    write_json(out / "teacher_forcing_ce.json", sanitize_nonfinite(ce_rows))

    train_features = collect_layer_features(model, train, layers)
    validation_features = collect_layer_features(model, validation, layers)
    _save_features(out, "train", train_features)
    _save_features(out, "validation", validation_features)
    probes = fit_layer_probes(train_features, validation_features)
    write_json(out / "probes.json", sanitize_nonfinite(probes))
    gradients = gradient_norms_by_layer(model, validation, layers)
    write_json(out / "gradient_norms.json", sanitize_nonfinite(gradients))
    cka = {
        "encoder_layers": encoder_layers,
        "encoder": within_module_cka(validation_features["expression_features"], encoder_layers),
        "decoder_layers": decoder_layers,
        "decoder": within_module_cka(validation_features["expression_features"], decoder_layers),
        "cross_module_not_computed": True,
    }
    write_json(out / "cka.json", sanitize_nonfinite(cka))
    logit_lens = decoder_logit_lens(model, official_panel, decoder_layers)
    write_json(out / "decoder_logit_lens.json", sanitize_nonfinite(logit_lens))
    encoder_lens = encoder_intermediate_greedy(model, official_panel, encoder_layers)
    write_json(out / "encoder_intermediate_decode.json", sanitize_nonfinite(encoder_lens))

    feature_failures = train_features["failures"] + validation_features["failures"]
    finite_ce = [row["ce"] for row in ce_rows if row["ce"] is not None and np.isfinite(row["ce"])]
    throughput = {
        "corpus_wall_time_sec": corpus_wall,
        "corpus_sec_per_formula": corpus_wall / max(len(train) + len(validation) + n_official_test, 1),
        "stretch_to_30000": False,
        "decision": "retain preregistered 3000-formula default; stretch is optional and not needed for the planned tests",
    }
    probes_complete = (
        set(probes["encoder_expression"]) == set(encoder_layers)
        and set(probes["decoder_expression"]) == set(decoder_layers)
        and set(probes["decoder_token"]) == set(decoder_layers)
        and all(
            "label_shuffle_control" in result
            for module in ("encoder_expression", "decoder_expression", "decoder_token")
            for tasks in probes[module].values()
            for result in tasks.values()
        )
    )
    def cka_matrix_complete(matrix: list[list[float | None]]) -> bool:
        array = np.asarray(matrix, dtype=float)
        return (
            array.ndim == 2 and array.shape[0] == array.shape[1]
            and np.isfinite(array).all() and np.allclose(array, array.T, rtol=1e-7, atol=1e-8)
            and np.allclose(np.diag(array), 1.0, rtol=1e-5, atol=1e-6)
        )

    gradient_rows = gradients["layers"]
    expected_layer_parameters = {
        row["ranking_name"]: int(row["parameter_count"])
        for row in inventory["encoder_blocks"] + inventory["decoder_blocks"]
    }
    gradients_complete = (
        set(gradient_rows) == set(layers) and gradients["n_records"] == 8
        and all(
            int(row.get("n_parameters", 0)) == expected_layer_parameters[layer]
            and np.isfinite(float(row.get("raw_l2")))
            and np.isfinite(float(row.get("per_sqrt_parameter")))
            for layer, row in gradient_rows.items()
        )
        and any(float(row["raw_l2"]) > 0 for row in gradient_rows.values())
    )
    expected_token_ranks = sum(len(row["tree_encoded"]) + 1 for row in official_panel) * len(decoder_layers)
    token_rank_rows = logit_lens["token_rows"]
    token_ranks_complete = (
        len(token_rank_rows) == expected_token_ranks
        and all(int(row.get("target_rank", 0)) >= 1 and row.get("target_category") for row in token_rank_rows)
        and all(row["target_category"] == token_category(row["target_token"]) for row in token_rank_rows)
    )
    go = {
        "official_counts_exact": len(train) == int(chosen_budget["official_corpus_train"])
        and len(validation) == int(chosen_budget["official_corpus_validation"])
        and n_official_test == int(chosen_budget["official_corpus_test"]),
        "no_skeleton_leakage": all(value == 0 for value in corpus_meta["skeleton_leakage"].values()),
        "grn_test_not_accessed": True,
        "official_test_outcomes_not_analyzed": True,
        "official_test_used_only_for_split_leakage_audit": True,
        "teacher_forcing_all_finite": len(finite_ce) == len(ce_rows) == len(validation),
        "released_4_encoder_12_decoder_layers_captured": len(encoder_layers) == 4
        and len(decoder_layers) == 12 and not feature_failures,
        "label_shuffle_controls_saved": probes_complete,
        "gradient_raw_and_normalized_saved": gradients_complete,
        "within_module_cka_saved": cka_matrix_complete(cka["encoder"]) and cka_matrix_complete(cka["decoder"]),
        "fixed_validation_panels_saved": len(official_panel) == n_panel and len(grn_panel) == n_panel,
        "decoder_and_encoder_lens_saved": len(logit_lens["formula_rows"]) == n_panel * len(decoder_layers)
        and len(encoder_lens["rows"]) == n_panel * len(encoder_layers)
        and token_ranks_complete and not logit_lens["failures"] and not encoder_lens["failures"],
    }
    status = "complete" if all(go.values()) else "incomplete"
    summary = {
        "status": status, "counts": {"train": len(train), "validation": len(validation), "test": n_official_test},
        "corpus_fingerprint": corpus_meta["fingerprint"], "corpus_failures": corpus_meta["n_failures"],
        "skeleton_leakage": corpus_meta["skeleton_leakage"], "teacher_forcing_ce_mean": float(np.mean(finite_ce)),
        "feature_failures": feature_failures, "throughput": throughput, "go_conditions": go,
        "official_corpus_cache_reused": cache_valid,
        "official_generator_split_policy": "gen_expr(train=True) for all formula-disjoint splits; test is in-distribution, not generator-distribution OOD",
    }
    write_json(out / "summary.json", sanitize_nonfinite(summary))
    write_json(out / "go.json", go)
    artifact_names = [
        "config_snapshot.json", "official_train.json", "official_validation.json", "sealed_official_test.json",
        "official_corpus_meta.json", "official_corpus_identity.json",
        "fixed_official_validation_panel.json", "fixed_grn_validation_panel.json", "teacher_forcing_ce.json",
        "train_features.npz", "validation_features.npz", "probes.json", "gradient_norms.json", "cka.json",
        "decoder_logit_lens.json", "encoder_intermediate_decode.json", "summary.json", "go.json",
    ]
    write_manifest(
        out, 4, status, go_conditions=go, summary=summary, git=git,
        started_utc=started_utc, finished_utc=utc_now(), wall_time_sec=perf_counter() - started_clock,
        checkpoint={"path": str(checkpoint), "sha256": sha256_file(checkpoint)},
        config_fingerprint=fingerprint_json(config), environment=environment, device=device,
        phase3_manifest_sha256=sha256_file(root / "phase3" / "manifest.json"),
        phase2_validation_sha256=sha256_file(phase2_validation_path),
        official_corpus_cache_reused=cache_valid,
        grn_test_accessed=False, official_test_generated=True,
        official_test_split_metadata_accessed=True, official_test_outcomes_analyzed=False,
        artifact_sha256={name: sha256_file(out / name) for name in artifact_names},
    )
    print(f"GPU_RUN5 Phase 4 {status}: corpus={len(train) + len(validation) + n_official_test} CE={summary['teacher_forcing_ce_mean']:.4f}")
    return 0 if status == "complete" else 1


if __name__ == "__main__":
    raise SystemExit(main())
