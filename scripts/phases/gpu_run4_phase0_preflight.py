"""GPU_RUN4 Phase 0: environment freeze, checkpoint load, architecture audit, official demo smoke."""

from __future__ import annotations

import argparse
import os
import sys
import time
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from gpu_run4.architecture import (  # noqa: E402
    architecture_audit,
    inventory_odeformer,
    parser_defaults_from_source,
)
from gpu_run4.records import dummy_formula_record, dummy_layer_record, missing_layer_fields, missing_required_fields  # noqa: E402
from gpu_run4_runtime import (  # noqa: E402
    assert_odeformer_not_from_github_source,
    candidate_infix,
    capture_numpy_permutation,
    classify_demo_exception,
    directory_fingerprint,
    download_checkpoint,
    fit_source_uses_permutation,
    fingerprint_json,
    git_info,
    hardware_identity,
    install_odeformer_path,
    load_gpu_run4_configs,
    load_odebench_equations,
    load_odeformer_model,
    make_symbolic_regressor,
    odebench_summary,
    odeformer_paths,
    official_demo_arrays,
    paper_model_args,
    require_python_310,
    resolve_run_dir,
    seed_everything,
    select_device,
    sha256_file,
    software_versions,
    utc_now,
    write_json,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="GPU_RUN4 Phase 0 preflight")
    parser.add_argument("--run-id", default=os.environ.get("LANSR_RUN_ID"))
    parser.add_argument("--allow-cpu", action="store_true")
    parser.add_argument("--skip-download", action="store_true")
    parser.add_argument("--skip-demo", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--smoke", action="store_true")
    return parser.parse_args()


def _schema_smoke() -> dict:
    dummy = dummy_formula_record("phase0_schema")
    layer = dummy_layer_record("encoder_0")
    return {
        "record_schema_missing": missing_required_fields(dummy),
        "layer_schema_missing": missing_layer_fields(layer),
        "dummy_valid": dummy["valid"] is not None,
        "dummy_campaign": dummy["campaign"],
    }


def _demo_record(
    *,
    formula_raw: str | None,
    n_candidates: int,
    reconstruction_r2: float | None,
    valid: bool,
    failure_reason: str | None,
    wall_time: float,
    beam_size: int,
    beam_temperature: float,
) -> dict:
    from gpu_run4.records import make_formula_record

    return make_formula_record(
        problem_id="phase0_official_demo",
        benchmark="official_demo",
        system_name="readme_harmonic_oscillator",
        dimension=2,
        split="smoke",
        condition="upstream_reproduction",
        true_formula_raw="x = 2.3 cos(t+0.5); y = 1.2 sin(t+0.1)",
        true_formula_prefix="",
        true_formula_canonical="",
        true_formula_skeleton="",
        candidate_index=0,
        candidate_formula_raw=formula_raw or "",
        candidate_formula_canonical=formula_raw or "",
        candidate_formula_skeleton="",
        selected=True,
        reconstruction_r2=reconstruction_r2,
        generalization_r2=None,
        canonical_exact=None,
        skeleton_exact=None,
        symbolic_equivalent=None,
        ted_raw=None,
        ted_skeleton=None,
        complexity=None,
        valid=valid,
        failure_reason=failure_reason,
        wall_time=wall_time,
        beam_size=beam_size,
        beam_temperature=beam_temperature,
        candidate_count=n_candidates,
    )


def main() -> int:
    args = parse_args()
    require_python_310()
    config = load_gpu_run4_configs()
    run_dir = resolve_run_dir(args.run_id, config=config)
    out_dir = run_dir / "phase0"
    out_dir.mkdir(parents=True, exist_ok=True)
    schema = _schema_smoke()
    if schema["record_schema_missing"] or schema["layer_schema_missing"]:
        write_json(
            out_dir / "preflight_failed.json",
            {"error": "schema", "missing": schema},
        )
        print(f"formula schema missing fields: {schema}")
        return 1

    if args.dry_run:
        dummy = dummy_formula_record("dry_run_phase0")
        write_json(out_dir / "dummy_records.json", [dummy])
        write_json(
            out_dir / "preflight.json",
            {
                "phase": 0,
                "status": "dry_run",
                "campaign": "GPU_RUN4",
                "at_utc": utc_now(),
                "schema": schema,
                "go_conditions": {},
            },
        )
        print(f"Phase 0 dry_run: {out_dir / 'preflight.json'}")
        return 0

    go = {
        "checkpoint_load_ok": False,
        "architecture_identified": False,
        "architecture_matches_paper": False,
        "official_demo_ok": False,
        "beam50_inference_ok": False,
        "valid_ode_candidate_ok": False,
        "predicted_ode_integration_ok": False,
        "schema_ok": True,
        "odebench_fingerprint_ok": False,
        "permutation_confirmed": False,
        "rescale_confirmed": False,
    }
    failures: list[str] = []
    paths = odeformer_paths(config)
    install_odeformer_path(paths["package"])
    protocol = dict(config.get("paper_protocol") or {})
    model_args = paper_model_args(protocol)
    beam_size = int(model_args["beam_size"])
    beam_temperature = float(model_args["beam_temperature"])
    beam_type = str(model_args["beam_type"])
    rescale = bool(protocol.get("rescale", True))
    permutation_seed = int((config.get("seed_bundles") or [{}])[0].get("permutation_seed", 1001))

    checkpoint_path = paths["checkpoint"]
    if not checkpoint_path.is_file() and not args.skip_download:
        try:
            download_checkpoint(
                checkpoint_path,
                file_id=str(config["odeformer_checkpoint_gdrive_id"]),
                url=str(config.get("odeformer_checkpoint_url")),
            )
        except Exception as exc:
            failures.append(f"CheckpointDownloadError:{exc}")

    try:
        device = select_device(allow_cpu=bool(args.allow_cpu or config.get("allow_cpu")))
    except Exception as exc:
        failures.append(f"CUDAUnavailable:{exc}")
        write_json(out_dir / "preflight_failed.json", {"error": str(exc), "at_utc": utc_now()})
        print(str(exc))
        return 1

    equations = []
    odebench = {}
    try:
        equations = load_odebench_equations(paths["package"])
        odebench = odebench_summary(equations)
        go["odebench_fingerprint_ok"] = odebench.get("n_systems") == 63
        if not go["odebench_fingerprint_ok"]:
            failures.append(f"OfficialConfigMismatch:ODEBench n_systems={odebench.get('n_systems')}")
    except Exception as exc:
        failures.append(f"OfficialConfigMismatch:ODEBench:{exc}")

    parsers_extracted = {}
    if paths["parsers"].is_file():
        parsers_extracted = parser_defaults_from_source(paths["parsers"].read_text(encoding="utf-8"))
    go["permutation_confirmed"] = fit_source_uses_permutation(
        paths["package"] / "odeformer" / "model" / "sklearn_wrapper.py"
    )
    if not go["permutation_confirmed"]:
        failures.append("OfficialConfigMismatch:fit() no longer permutes trajectories")

    seed_everything(permutation_seed)
    model = None
    inventory = None
    audit = None
    checkpoint_sha = sha256_file(checkpoint_path) if checkpoint_path.is_file() else None
    expected_sha = config.get("odeformer_checkpoint_sha256")
    if checkpoint_sha and expected_sha and checkpoint_sha != expected_sha:
        failures.append(
            f"OfficialConfigMismatch:checkpoint sha256 {checkpoint_sha} != expected {expected_sha}"
        )
    if checkpoint_path.is_file():
        try:
            model = load_odeformer_model(checkpoint_path, device=device)
            assert_odeformer_not_from_github_source()
            inventory = inventory_odeformer(model)
            audit = architecture_audit(inventory)
            go["checkpoint_load_ok"] = True
            go["architecture_identified"] = bool(inventory.get("ranking_layers"))
            go["architecture_matches_paper"] = bool(audit["matches_paper"])
            write_json(out_dir / "architecture_inventory.json", inventory)
            write_json(out_dir / "architecture_audit.json", audit)
            if not audit["matches_paper"]:
                failures.append(f"ArchitectureMismatch:{audit['mismatches']}")
        except Exception as exc:
            failures.append(f"CheckpointLoadError:{type(exc).__name__}:{exc}")
            write_json(
                out_dir / "checkpoint_load_error.json",
                {"error": str(exc), "traceback": traceback.format_exc(), "at_utc": utc_now()},
            )
    else:
        failures.append("MissingCheckpoint")

    demo_payload = None
    if model is not None and not args.skip_demo:
        try:
            regressor = make_symbolic_regressor(
                model,
                rescale=rescale,
                beam_size=beam_size,
                beam_temperature=beam_temperature,
                beam_type=beam_type,
            )
            go["rescale_confirmed"] = bool(getattr(regressor, "rescale", False)) and getattr(regressor, "scaler", None) is not None
            times, trajectory, demo_spec = official_demo_arrays(n_points=int(config.get("smoke", {}).get("n_demo_points", 50)))
            started = time.perf_counter()
            with capture_numpy_permutation(permutation_seed) as permutations:
                candidates = regressor.fit(times, trajectory)
            wall_time = time.perf_counter() - started
            trees = list(candidates.get(0) or [])
            selected = trees[0] if trees else None
            formula_raw = candidate_infix(selected)
            infixes = [candidate_infix(tree) for tree in trees]
            n_candidates = len(trees)
            has_multicomponent = any(bool(text) and "|" in str(text) for text in infixes)
            selected_has_separator = bool(formula_raw) and "|" in str(formula_raw)
            go["beam50_inference_ok"] = (
                n_candidates > 0
                and int(getattr(model, "beam_size", 0) or 0) == beam_size
                and str(getattr(model, "beam_type", "")) == beam_type
            )
            go["valid_ode_candidate_ok"] = has_multicomponent
            reconstruction_r2 = None
            integration_ok = False
            integration_failure = None
            try:
                pred_trajectory = regressor.predict(times, trajectory[0])
                import numpy as np
                from sklearn.metrics import r2_score

                if pred_trajectory is None or not np.isfinite(np.asarray(pred_trajectory)).all():
                    integration_failure = "CandidateIntegrationFailure"
                else:
                    reconstruction_r2 = float(r2_score(trajectory, pred_trajectory, multioutput="variance_weighted"))
                    integration_ok = True
            except Exception as exc:
                integration_failure = f"CandidateIntegrationFailure:{type(exc).__name__}:{exc}"
            go["predicted_ode_integration_ok"] = integration_ok
            go["official_demo_ok"] = bool(n_candidates) and formula_raw is not None
            selected_failure = integration_failure
            if formula_raw and not selected_has_separator:
                selected_failure = selected_failure or "ParseError"
            if not has_multicomponent:
                selected_failure = selected_failure or "ParseError"
            demo_record = _demo_record(
                formula_raw=formula_raw,
                n_candidates=n_candidates,
                reconstruction_r2=reconstruction_r2,
                valid=bool(selected_has_separator) and integration_ok,
                failure_reason=selected_failure,
                wall_time=wall_time,
                beam_size=beam_size,
                beam_temperature=beam_temperature,
            )
            demo_payload = {
                "demo_spec": demo_spec,
                "n_candidates": n_candidates,
                "selected_formula": formula_raw,
                "reconstruction_r2": reconstruction_r2,
                "beam_size_applied": int(getattr(model, "beam_size", beam_size)),
                "beam_temperature_applied": float(getattr(model, "beam_temperature", beam_temperature)),
                "beam_type": getattr(model, "beam_type", None),
                "sort_metric_official_demo": "snmse",
                "paper_selection_metric": protocol.get("candidate_selection_metric"),
                "rescale": bool(getattr(regressor, "rescale", False)),
                "scaler_present": getattr(regressor, "scaler", None) is not None,
                "permutation_seed": permutation_seed,
                "n_permutations_captured": len(permutations),
                "first_permutation_head": (permutations[0][:16] if permutations else None),
                "wall_time": wall_time,
                "record": demo_record,
            }
            write_json(out_dir / "official_demo.json", demo_payload)
            write_json(out_dir / "demo_record.json", demo_record)
            if not go["valid_ode_candidate_ok"]:
                failures.append("ParseError:official demo produced no multi-component ODE")
            if not go["predicted_ode_integration_ok"]:
                failures.append(integration_failure or "CandidateIntegrationFailure")
        except Exception as exc:
            tag = classify_demo_exception(exc)
            failures.append(f"{tag}:{type(exc).__name__}:{exc}")
            write_json(
                out_dir / "demo_error.json",
                {"error": str(exc), "traceback": traceback.format_exc(), "at_utc": utc_now()},
            )

    go_1 = [
        go["checkpoint_load_ok"],
        go["architecture_identified"],
        go["architecture_matches_paper"],
        go["official_demo_ok"],
        go["beam50_inference_ok"],
        go["valid_ode_candidate_ok"],
        go["predicted_ode_integration_ok"],
    ]
    status = "complete" if all(go_1) else "incomplete"
    manifest = {
        "phase": 0,
        "status": status,
        "campaign": "GPU_RUN4",
        "provenance": "upstream_reproduction",
        "at_utc": utc_now(),
        "run_dir": str(run_dir),
        "git": git_info(),
        "hardware": hardware_identity(),
        "software": software_versions(),
        "device": device,
        "odeformer_paths": {k: str(v) for k, v in paths.items()},
        "odeformer_package_fingerprint": directory_fingerprint(paths["package"]),
        "odebench_fingerprint": sha256_file(paths["odebench_equations"]) if paths["odebench_equations"].is_file() else None,
        "odebench_extended_fingerprint": sha256_file(paths["odebench_extended"]) if paths["odebench_extended"].is_file() else None,
        "config_fingerprint": fingerprint_json(config),
        "checkpoint_sha256": checkpoint_sha,
        "checkpoint_exists": checkpoint_path.is_file(),
        "odeformer_upstream_url": config.get("odeformer_upstream_url"),
        "odeformer_checkpoint_url": config.get("odeformer_checkpoint_url"),
        "paper_protocol": protocol,
        "parser_defaults_from_source": parsers_extracted,
        "odebench": odebench,
        "go_conditions": go,
        "go_1": {
            "checkpoint_load_ok": go["checkpoint_load_ok"],
            "architecture_identified": go["architecture_identified"],
            "architecture_matches_paper": go["architecture_matches_paper"],
            "official_demo_ok": go["official_demo_ok"],
            "beam50_inference_ok": go["beam50_inference_ok"],
            "valid_ode_candidate_ok": go["valid_ode_candidate_ok"],
            "predicted_ode_integration_ok": go["predicted_ode_integration_ok"],
        },
        "failures": failures,
        "schema": schema,
        "seed_bundles": config.get("seed_bundles"),
        "timeouts": config.get("timeouts"),
        "architecture_summary": None
        if inventory is None
        else {
            "n_encoder_transformer_layers": inventory["n_encoder_transformer_layers"],
            "n_decoder_transformer_layers": inventory["n_decoder_transformer_layers"],
            "encoder_embedding_dim": inventory["encoder_embedding_dim"],
            "decoder_embedding_dim": inventory["decoder_embedding_dim"],
            "encoder_n_heads": inventory["encoder_n_heads"],
            "decoder_n_heads": inventory["decoder_n_heads"],
            "ranking_layers": inventory["ranking_layers"],
            "total_parameters": inventory["total_parameters"],
            "beam_type": inventory.get("beam_type"),
            "beam_size": inventory.get("beam_size"),
            "tied_output_embedding": inventory.get("tied_output_embedding"),
        },
        "official_demo": None
        if demo_payload is None
        else {
            "selected_formula": demo_payload["selected_formula"],
            "n_candidates": demo_payload["n_candidates"],
            "reconstruction_r2": demo_payload["reconstruction_r2"],
            "wall_time": demo_payload["wall_time"],
            "beam_type": demo_payload["beam_type"],
        },
    }
    write_json(out_dir / "preflight.json", manifest)
    write_json(run_dir / "manifest.json", {"status": "running", "phase0": manifest, "at_utc": utc_now()})
    print(f"Phase 0 {status}: {out_dir / 'preflight.json'}")
    if not go["checkpoint_load_ok"]:
        print("Go 1 failed: official checkpoint did not load.")
        return 1
    if not go["architecture_identified"] or not go["architecture_matches_paper"]:
        print("Go 1 failed: architecture could not be identified or does not match the paper table.")
        return 1
    if not go["official_demo_ok"] or not go["beam50_inference_ok"] or not go["valid_ode_candidate_ok"]:
        print("Go 1 failed: official demo / beam-50 inference did not produce a valid ODE candidate.")
        return 1
    if not go["predicted_ode_integration_ok"]:
        print("Go 1 failed: predicted ODE could not be re-integrated.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
