"""GPU_RUN5 Phase 0: freeze provenance, feasibility, seeds, and throughput."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

import numpy as np  # noqa: E402

from gpu_run4.architecture import inventory_odeformer  # noqa: E402
from gpu_run4.training import teacher_forcing_loss  # noqa: E402
from gpu_run4_runtime import (  # noqa: E402
    candidate_infix,
    capture_numpy_permutation,
    directory_fingerprint,
    git_info,
    hardware_identity,
    load_odeformer_model,
    make_symbolic_regressor,
    official_demo_arrays,
    seed_everything,
    sha256_file,
    software_versions,
    utc_now,
    write_json,
)
from gpu_run5.config import CONFIG_PATH, budget, load_config, phase_dir  # noqa: E402
from gpu_run5.grn import FAMILIES, _evaluate_prefix, system_definition  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="GPU_RUN5 Phase 0 preflight")
    parser.add_argument("--run-id", default=os.environ.get("LANSR_RUN_ID"))
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--allow-cpu", action="store_true")
    parser.add_argument("--skip-throughput", action="store_true")
    return parser.parse_args()


def _git_tree(path: str) -> str | None:
    result = subprocess.run(["git", "rev-parse", f"HEAD:{path}"], cwd=ROOT, text=True, capture_output=True)
    return result.stdout.strip() if result.returncode == 0 else None


def _checkpoint_params(model) -> dict:
    params = getattr(getattr(model, "env", None), "params", None)
    if params is None:
        params = getattr(model, "params", None)
    names = ["operators_to_use", "max_dimension", "max_generated_output_len", "max_len", "max_int"]
    values = {name: getattr(params, name, None) for name in names}
    values["model_max_generated_output_len"] = getattr(model, "max_generated_output_len", None)
    return values


def _finalize_gpu_run4(config: dict) -> dict:
    source = ROOT / str(config["gpu_run4_source_run"])
    phase_status = {}
    for phase in range(1, 10):
        path = source / f"phase{phase}" / "manifest.json"
        data = json.loads(path.read_text()) if path.is_file() else {}
        phase_status[str(phase)] = data.get("status")
    selected = source / "phase2" / "selected.json"
    candidates = source / "phase2" / "all_candidates.json"
    selected_rows = json.loads(selected.read_text()) if selected.is_file() else []
    candidate_rows = json.loads(candidates.read_text()) if candidates.is_file() else []
    record_counts = {
        "selected_total": len(selected_rows),
        "selected_odeformer": sum(row.get("condition") == "odeformer" for row in selected_rows),
        "candidates_total": len(candidate_rows),
        "candidates_odeformer": sum(row.get("condition") == "odeformer" for row in candidate_rows),
    }
    complete = all(value == "complete" for value in phase_status.values()) and record_counts == {
        "selected_total": 284, "selected_odeformer": 252, "candidates_total": 12632, "candidates_odeformer": 12600,
    }
    root_manifest = source / "manifest.json"
    previous = json.loads(root_manifest.read_text()) if root_manifest.is_file() else {}
    if complete:
        write_json(
            root_manifest,
            {
                **previous,
                "status": "complete",
                "finalized_at_utc": utc_now(),
                "completion_scope": "released_checkpoint_4enc_12dec_61M",
                "architecture_matches_paper": False,
                "phase_status": phase_status,
            },
        )
    return {
        "source": str(source), "phase_status": phase_status, "record_counts": record_counts,
        "selected_sha256": sha256_file(selected), "all_candidates_sha256": sha256_file(candidates),
        "complete": complete, "previous_root_status": previous.get("status"),
    }


def _teacher_audit(model) -> dict:
    env = model.env
    records = []
    for exponent in (1, 2, 4):
        params = {"a1": 1.234, "a2": 1.357, "a3": 1.479, "k1": 0.8123, "k2": 0.9345, "k3": 1.056,
                  "b1": 0.5123, "b2": 0.6234, "b3": 0.7345, "basal": 0.1234, "n": exponent}
        for family, spec in FAMILIES.items():
            rhs, components = system_definition(family, params)
            raw_tokens = ",|,".join(components).split(",")
            tree = env.equation_encoder.decode(raw_tokens)
            encoded = env.equation_encoder.encode(tree) if tree is not None else []
            decoded = env.equation_encoder.decode(encoded) if encoded else None
            decoded_components = decoded.prefix().split(",|,") if decoded is not None else []
            max_abs_error = 0.0
            finite_projection = True
            for point_scale in (0.2, 0.7, 1.4):
                point = np.linspace(point_scale, point_scale + 0.5, spec.dimension)
                truth = rhs(0.0, point)
                projected = np.asarray([_evaluate_prefix(item, point) for item in decoded_components]) if decoded_components else np.asarray([])
                finite_projection &= bool(projected.shape == truth.shape and np.isfinite(projected).all())
                if projected.shape == truth.shape:
                    max_abs_error = max(max_abs_error, float(np.max(np.abs(projected - truth))))
            missing = [token for token in encoded if not (token in env.equation_word2id or token.lstrip("+-").replace(".", "", 1).isdigit())]
            equivalent = max_abs_error <= 1e-12
            records.append({
                "family": family,
                "hill_exponent": exponent,
                "dimension": spec.dimension,
                "teacher_prefix": ",|,".join(components),
                "encoded": list(encoded),
                "token_length": len(encoded),
                "max_length": int(getattr(model, "max_generated_output_len", 200)),
                "roundtrip_prefix": decoded.prefix() if decoded is not None else None,
                "missing_tokens": missing,
                "finite_projection": finite_projection,
                "max_roundtrip_numeric_error": max_abs_error,
                "roundtrip_numerically_equivalent": equivalent,
                "nested_pow2_for_n4": exponent != 4 or "pow2,pow2" in ",|,".join(components),
                "ok": bool(decoded is not None and not missing and len(encoded) <= int(getattr(model, "max_generated_output_len", 200)) and finite_projection and equivalent),
            })
    return {"records": records, "all_ok": all(row["ok"] for row in records), "max_token_length": max(row["token_length"] for row in records)}


def _throughput(model, config: dict, run_budget: dict, device: str) -> dict:
    import torch

    protocol = config["paper_protocol"]
    beam_size = int(run_budget["beam_size"])
    seed_a = int(config["seed_bundles"][0]["candidate_seed"])
    seed_b = int(config["seed_bundles"][1]["candidate_seed"])
    model.generation_seed = seed_a
    regressor = make_symbolic_regressor(
        model,
        rescale=bool(protocol["rescale"]),
        beam_size=beam_size,
        beam_temperature=float(protocol["beam_temperature"]),
        beam_type=str(protocol["beam_type"]),
        generation_seed=seed_a,
    )
    times, trajectory, _ = official_demo_arrays(n_points=int(run_budget["n_points"]))
    if device == "cuda":
        torch.cuda.reset_peak_memory_stats()
        torch.cuda.synchronize()
    started = time.perf_counter()
    with capture_numpy_permutation(1001):
        candidates = regressor.fit(times, trajectory)
    if device == "cuda":
        torch.cuda.synchronize()
    decode_seconds = time.perf_counter() - started
    trees = list(candidates.get(0) or [])
    formulas_a = [candidate_infix(tree) for tree in trees]
    model.generation_seed = seed_a
    with capture_numpy_permutation(1001):
        repeat = regressor.fit(times, trajectory)
    formulas_repeat = [candidate_infix(tree) for tree in list(repeat.get(0) or [])]
    model.generation_seed = seed_b
    with capture_numpy_permutation(1001):
        alternate = regressor.fit(times, trajectory)
    formulas_b = [candidate_infix(tree) for tree in list(alternate.get(0) or [])]

    # One representative forward/backward gives a bounded VRAM feasibility check.
    model.env.rng = np.random.RandomState(101)
    sample = None
    for _ in range(20):
        sample = model.env.gen_expr(train=True)[0]
        if sample and sample.get("tree_encoded"):
            break
    if not sample:
        raise RuntimeError("official generator failed to yield a throughput sample in 20 attempts")
    train_started = time.perf_counter()
    loss = teacher_forcing_loss(model, sample["times"], sample["trajectory"], sample["tree_encoded"])
    loss.backward()
    if device == "cuda":
        torch.cuda.synchronize()
    train_seconds = time.perf_counter() - train_started
    model.zero_grad(set_to_none=True)
    peak = int(torch.cuda.max_memory_allocated()) if device == "cuda" else None
    per_cell_estimate = decode_seconds * (50 / max(beam_size, 1))
    return {
        "device": device,
        "beam_size": beam_size,
        "decode_seconds": decode_seconds,
        "candidate_count": len(trees),
        "first_candidate": candidate_infix(trees[0]) if trees else None,
        "sampling_seed_a": seed_a,
        "sampling_seed_b": seed_b,
        "same_seed_reproducible": formulas_a == formulas_repeat,
        "different_seed_changes_candidates": formulas_a != formulas_b,
        "one_forward_backward_seconds": train_seconds,
        "teacher_forcing_loss": float(loss.detach().cpu()),
        "peak_memory_bytes": peak,
        "estimated_beam50_seconds_per_cell": per_cell_estimate,
        "estimate_exceeds_plan_by_2x": per_cell_estimate > 14.0,
    }


def main() -> int:
    args = parse_args()
    if sys.version_info[:2] != (3, 10):
        raise RuntimeError(f"GPU_RUN5 requires Python 3.10, found {sys.version.split()[0]}")
    config = load_config()
    out = phase_dir(args.run_id, 0)
    run_budget = budget(config, args.smoke)
    checkpoint = ROOT / str(config["odeformer_checkpoint"])
    device = "cuda"
    import torch
    if not torch.cuda.is_available():
        if not args.allow_cpu:
            raise RuntimeError("CUDAUnavailable")
        device = "cpu"
    seed_everything(int(config["seed_bundles"][0]["model_seed"]))
    model = load_odeformer_model(checkpoint, device=device)
    inventory = inventory_odeformer(model)
    params = _checkpoint_params(model)
    vocabulary = sorted(model.env.equation_word2id)
    teacher = _teacher_audit(model)
    run4 = _finalize_gpu_run4(config)
    throughput = {"skipped": True} if args.skip_throughput else _throughput(model, config, run_budget, device)
    current_git = git_info()
    commit = str(current_git.get("commit") or "")
    expected_run_id = bool(args.run_id and re.fullmatch(r"gpu_run5_\d{8}_[0-9a-f]{8}", args.run_id))
    run_id_matches_commit = bool(expected_run_id and str(args.run_id).endswith(commit[:8]))
    prereg_path = ROOT / "GPU_RUN5" / "preregistration.json"
    prereg = json.loads(prereg_path.read_text()) if prereg_path.is_file() else {}
    checkpoint_audit = {
        "sha256": sha256_file(checkpoint),
        "expected_sha256": config["odeformer_checkpoint_sha256"],
        "params": params,
        "architecture": inventory,
        "vendored_git_tree": _git_tree("third_party/odeformer"),
        "vendored_directory_fingerprint": directory_fingerprint(ROOT / "third_party" / "odeformer"),
        "upstream_commit": None,
        "upstream_commit_unavailable_reason": "vendored snapshot has no .git metadata",
    }
    vocabulary_audit = {
        "size": len(vocabulary),
        "required_present": {token: token in vocabulary for token in ["inv", "pow2", "pow3", "pow", "div", "sub", "|", "x_0", "x_5"]},
        "pow4_present": "pow4" in vocabulary,
        "decode_operator_mask_present": False,
    }
    go = {
        "authoritative_mode": not args.smoke and not args.skip_throughput,
        "cuda": device == "cuda",
        "clean_git": not bool(current_git.get("status_short")),
        "run_id_format_ok": expected_run_id,
        "run_id_matches_commit": run_id_matches_commit,
        "checkpoint_sha_ok": checkpoint_audit["sha256"] == checkpoint_audit["expected_sha256"],
        "architecture_4_plus_12": len(inventory["ranking_layers"]) == 16,
        "checkpoint_params_ok": params["operators_to_use"] == "sin:1,inv:1,pow2:1,id:3,add:3,mul:1" and params["max_dimension"] == 6,
        "gpu_run4_finalized": run4["complete"],
        "teacher_tokenization_ok": teacher["all_ok"],
        "vocabulary_ok": all(vocabulary_audit["required_present"].values()) and not vocabulary_audit["pow4_present"],
        "throughput_ok": bool(not args.skip_throughput and not throughput.get("estimate_exceeds_plan_by_2x", True)),
        "candidate_seed_control_ok": bool(not args.skip_throughput and (
            throughput.get("same_seed_reproducible") and throughput.get("different_seed_changes_candidates")
        )),
        "preregistration_schema_ok": set(prereg.get("predictions", {})) == {"P3", "P4", "P5", "P6", "P7"},
    }
    status = "complete" if all(go.values()) else ("smoke" if args.smoke else "incomplete")
    write_json(out / "checkpoint_audit.json", checkpoint_audit)
    write_json(out / "vocabulary_audit.json", vocabulary_audit)
    write_json(out / "teacher_tokenization_audit.json", teacher)
    write_json(out / "throughput.json", throughput)
    write_json(out / "freeze_decision.json", {
        "seed_bundles": config["seed_bundles"],
        "corruptions": config["corruptions"],
        "grn_system_counts": {
            "train": run_budget["train_variants_per_family"] * len(FAMILIES),
            "validation": run_budget["validation_variants_per_family"] * len(FAMILIES),
            "test": run_budget["test_variants_per_family"] * len(FAMILIES),
        },
        "official_corpus": {
            "train": run_budget["official_corpus_train"],
            "validation": run_budget["official_corpus_validation"],
            "test": run_budget["official_corpus_test"],
            "stretch_30000": False,
        },
        "model_selection_score": config["training"]["model_selection_score"],
        "candidate_seed_rule": "bundle.candidate_seed + stable_problem_hash",
        "random_test_representative": "random3_0",
        "family_holdout_requires_separate_checkpoint": True,
        "deeper_reduction_applied": bool(throughput.get("estimate_exceeds_plan_by_2x", False)),
    })
    write_json(out / "gpu_run4_finalize_audit.json", run4)
    write_json(out / "go.json", go)
    shutil.copy2(CONFIG_PATH, out / "config_frozen.yaml")
    shutil.copy2(prereg_path, out / "preregistration.json")
    write_json(out / "manifest.json", {
        "campaign": "GPU_RUN5", "phase": 0, "status": status, "at_utc": utc_now(),
        "run_id": args.run_id, "git": current_git, "hardware": hardware_identity(), "software": software_versions(),
        "device": device, "smoke": bool(args.smoke), "skip_throughput": bool(args.skip_throughput),
        "test_accessed": False, "config_sha256": sha256_file(CONFIG_PATH),
        "preregistration_sha256": sha256_file(prereg_path), "go_conditions": go,
    })
    print(f"GPU_RUN5 Phase 0 {status}: {go}")
    return 0 if status == "complete" else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception as exc:
        failure_args = parse_args()
        failure_out = phase_dir(failure_args.run_id, 0)
        write_json(failure_out / "manifest.json", {
            "campaign": "GPU_RUN5", "phase": 0, "status": "failed", "at_utc": utc_now(),
            "run_id": failure_args.run_id, "failure_reason": f"{type(exc).__name__}:{exc}", "test_accessed": False,
        })
        raise
