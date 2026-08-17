"""GPU_RUN3 Phase 0: environment freeze, checkpoint load, architecture inventory, MCTS smoke."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from gpu_run3.architecture import inventory_ndformer  # noqa: E402
from gpu_run3.formulas import formula_views, parse_to_prefix, vocabulary_inventory  # noqa: E402
from gpu_run3.records import dummy_formula_record, missing_required_fields  # noqa: E402
from gpu_run3.search import run_mcts  # noqa: E402
from gpu_run3.synthetic import problem_from_simulation, simulate_system  # noqa: E402
from gpu_run3_runtime import (  # noqa: E402
    assert_nd2_not_from_github_source,
    configure_nd2_logging,
    cpu_identity,
    directory_fingerprint,
    download_checkpoint,
    git_info,
    install_nd2_path,
    load_gpu_run3_configs,
    load_ndformer,
    nd2_paths,
    require_python_310,
    resolve_run_dir,
    select_device,
    sha256_file,
    software_versions,
    utc_now,
    write_json,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="GPU_RUN3 Phase 0 preflight")
    parser.add_argument("--run-id", default=os.environ.get("LANSR_RUN_ID"))
    parser.add_argument("--allow-cpu", action="store_true")
    parser.add_argument("--skip-download", action="store_true")
    parser.add_argument("--skip-mcts", action="store_true")
    return parser.parse_args()


def _schema_smoke() -> dict:
    dummy = dummy_formula_record("phase0_schema")
    return {"record_schema_missing": missing_required_fields(dummy), "dummy_valid": dummy["valid"] is not None}


def main() -> int:
    args = parse_args()
    require_python_310()
    config = load_gpu_run3_configs()
    run_dir = resolve_run_dir(args.run_id, config=config)
    out_dir = run_dir / "phase0"
    out_dir.mkdir(parents=True, exist_ok=True)
    configure_nd2_logging(out_dir / "nd2.log")
    paths = nd2_paths(config)
    install_nd2_path(paths["package"])
    schema = _schema_smoke()
    if schema["record_schema_missing"]:
        write_json(out_dir / "preflight_failed.json", {"error": "schema", "missing": schema["record_schema_missing"]})
        print(f"formula schema missing fields: {schema['record_schema_missing']}")
        return 1

    go = {
        "checkpoint_load_ok": False,
        "forward_ok": False,
        "policy_shape_ok": False,
        "vocab_ok": False,
        "parser_ok": False,
        "mcts_valid_formula_ok": False,
    }
    failures: list[str] = []
    checkpoint_path = paths["checkpoint"]
    if not checkpoint_path.is_file() and not args.skip_download:
        try:
            download_checkpoint(str(config["nd2_checkpoint_url"]), checkpoint_path)
        except Exception as exc:
            failures.append(f"MissingCheckpoint:{exc}")

    device = None
    try:
        device = select_device(allow_cpu=bool(args.allow_cpu or config.get("allow_cpu")))
    except Exception as exc:
        failures.append(f"CUDAUnavailable:{exc}")
        write_json(out_dir / "preflight_failed.json", {"error": str(exc), "at_utc": utc_now()})
        print(str(exc))
        return 1

    vocab = vocabulary_inventory()
    go["vocab_ok"] = bool(vocab["operator_unary"].get("aggr") and vocab["operator_unary"].get("sour"))
    parser_prefix = None
    try:
        parser_prefix = parse_to_prefix("omega + aggr(sin(sour(x)-targ(x)))", root_type="node")
        views = formula_views(parser_prefix)
        go["parser_ok"] = bool(views["valid"] and "aggr" in parser_prefix)
        write_json(out_dir / "parser_smoke.json", {"prefix": parser_prefix, **{k: v for k, v in views.items() if k != "expression_tree"}})
    except Exception as exc:
        failures.append(f"ParseError:{exc}")
        go["parser_ok"] = False

    model = None
    inventory = None
    checkpoint_sha = sha256_file(checkpoint_path) if checkpoint_path.is_file() else None
    if checkpoint_path.is_file() and device is not None:
        try:
            model = load_ndformer(checkpoint_path, device=device)
            assert_nd2_not_from_github_source()
            inventory = inventory_ndformer(model)
            go["checkpoint_load_ok"] = True
            write_json(out_dir / "architecture_inventory.json", inventory)
        except Exception as exc:
            failures.append(f"CheckpointLoadError:{exc}")
    else:
        failures.append("MissingCheckpoint")

    mcts_record = None
    if model is not None and not args.skip_mcts:
        try:
            from gpu_run3.synthetic import load_official_systems

            official_cfg = load_official_systems(paths["synthetic_config"])
            kur = official_cfg["KUR"]
            smoke = config["smoke"]
            simulated = simulate_system(
                "KUR",
                kur,
                seed=0,
                n_steps=int(smoke["simulate_steps"]),
                n_nodes=int(smoke["n_nodes"]),
                n_edges=int(smoke["n_edges"]),
            )
            problem = problem_from_simulation(simulated, target_var="omega", input_vars=["x", "omega0"])
            # Official KUR uses omega0 in GD_expr via dependent omega; map omega0->omega for NDformer vars.
            problem["Xv"] = {"x": problem["Xv"]["x"], "omega": problem["Xv"]["omega0"]}
            problem["vars_node"] = ["x", "omega"]
            model.set_data(
                Xv=problem["Xv"],
                Xe={},
                A=problem["A"],
                G=problem["G"],
                Y=problem["Y"],
                root_type="node",
                cache_data_emb=True,
            )
            policy = model.get_policy([["node"]])
            go["forward_ok"] = True
            expected_words = int(model.decoder.n_words)
            go["policy_shape_ok"] = (
                getattr(policy, "ndim", 0) == 2
                and int(policy.shape[0]) == 1
                and int(policy.shape[1]) == expected_words
            )
            mcts_record = run_mcts(
                model=model,
                Xv=problem["Xv"],
                A=problem["A"],
                G=problem["G"],
                Y=problem["Y"],
                vars_node=problem["vars_node"],
                true_prefix=problem["true_prefix"],
                episode_limit=int(smoke["mcts_episode_limit"]),
                time_limit_sec=float(smoke["mcts_time_limit_sec"]),
                mcts_config=config["mcts"],
                problem_id="phase0_kur_smoke",
                system_name="KUR",
                condition="upstream_reproduction",
            )
            go["mcts_valid_formula_ok"] = bool(mcts_record.get("valid") or mcts_record.get("pred_formula_raw"))
            write_json(out_dir / "mcts_smoke.json", mcts_record)
            write_json(out_dir / "policy_smoke.json", {"shape": list(policy.shape), "sum": float(policy.sum())})
        except Exception as exc:
            failures.append(f"MCTSTimeout_or_forward:{type(exc).__name__}:{exc}")
            go["forward_ok"] = go["forward_ok"] or False

    status = "complete" if all(go.values()) else "incomplete"
    manifest = {
        "phase": 0,
        "status": status,
        "campaign": "GPU_RUN3",
        "provenance": "upstream_reproduction",
        "at_utc": utc_now(),
        "run_dir": str(run_dir),
        "git": git_info(),
        "cpu": cpu_identity(),
        "software": software_versions(),
        "device": device,
        "nd2_paths": {k: str(v) for k, v in paths.items()},
        "nd2_package_fingerprint": directory_fingerprint(paths["package"]),
        "checkpoint_sha256": checkpoint_sha,
        "checkpoint_exists": checkpoint_path.is_file(),
        "nd2_upstream_url": config.get("nd2_upstream_url"),
        "nd2_checkpoint_url": config.get("nd2_checkpoint_url"),
        "nd2_zenodo": config.get("nd2_zenodo"),
        "vocabulary": {
            "n_words_table": vocab["n_words_table"],
            "network_operators": vocab["network_operators"],
            "operator_unary": vocab["operator_unary"],
            "operator_binary": vocab["operator_binary"],
        },
        "go_conditions": go,
        "failures": failures,
        "schema": schema,
        "seed_bundles": config.get("seed_bundles"),
        "timeouts": config.get("timeouts"),
        "parser_prefix": parser_prefix,
        "architecture_summary": None
        if inventory is None
        else {
            "n_encoder_transformer_layers": inventory["n_encoder_transformer_layers"],
            "n_decoder_transformer_layers": inventory["n_decoder_transformer_layers"],
            "ranking_layers": inventory["ranking_layers"],
            "total_parameters": inventory["total_parameters"],
        },
    }
    write_json(out_dir / "preflight.json", manifest)
    write_json(run_dir / "manifest.json", {"status": "running", "phase0": manifest, "at_utc": utc_now()})
    print(f"Phase 0 {status}: {out_dir / 'preflight.json'}")
    if not go["checkpoint_load_ok"]:
        print("Go 1 failed: official checkpoint did not load.")
        return 1
    if not go["forward_ok"] or not go["policy_shape_ok"] or not go["vocab_ok"]:
        print("Go 1 failed: policy forward / vocabulary mismatch.")
        return 1
    if not go["mcts_valid_formula_ok"]:
        print("Go 2 warning: small MCTS did not produce a valid formula; recorded failure.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
