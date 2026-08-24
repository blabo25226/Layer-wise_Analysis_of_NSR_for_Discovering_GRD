"""GPU_RUN5 Phase 8: selective validation freeze and one-time final test.

Run ``--stage validation`` first.  That path never names, discovers, hashes, or
reads a sealed test artifact.  Only a full, successful validation run writes
Go 6, the exact preregistered five-condition freeze, and Go 7.  A separate
``--stage final-test`` invocation verifies those immutable files, atomically
claims the sole test-open event, and then reads both sealed views.

Phase 7 integration contract (fail-fast, no inference):
``phase7/phase8_handoff.json`` and ``phase7/layer_freeze.json`` must match the
hashes in the Phase 7 manifest.  Single-block Phase 7 hyperparameters and
checkpoints are diagnostic and are never reused for multi-block conditions.
"""

from __future__ import annotations

import argparse
import gc
import json
import math
import os
import sys
from pathlib import Path
from time import perf_counter
from typing import Any, Mapping, Sequence

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from gpu_run2_runtime import fingerprint_json, git_info, sha256_file, utc_now, write_json as _write_json  # noqa: E402
from gpu_run3_runtime import software_versions  # noqa: E402
from gpu_run4.architecture import inventory_odeformer  # noqa: E402
from gpu_run4.inference import evaluate_system  # noqa: E402
from gpu_run4.trajectories import corrupt_trajectory, reconstruct_and_generalize  # noqa: E402
from gpu_run4_runtime import load_odebench_equations, load_odeformer_model, select_device  # noqa: E402
from gpu_run5.config import budget, load_config, load_sealed_test, phase_dir, read_json, run_dir, sanitize_nonfinite, write_manifest  # noqa: E402
from gpu_run5.phase6 import artifact_index, candidate_seed_map, candidate_seed_map_sha256, corruption_grid, coverage_audit, hyperparameter_grid  # noqa: E402
from gpu_run5.phase8 import (  # noqa: E402
    FINAL_CONDITIONS,
    REUSED_VALIDATION_CONDITIONS,
    VIEWS,
    audit_go7,
    bind_test_artifact_hashes,
    build_final_freeze,
    claim_test_open,
    complete_test_open,
    evaluate_go6,
    expected_layer_sets,
    expected_phase8_final_counts,
    expected_phase8_validation_counts,
    phase8_trial_identity,
    selective_conditions,
    validate_selection_contracts,
)
from gpu_run5.phase8_runtime import decode_panel, make_regressor  # noqa: E402
from gpu_run5.training import (  # noqa: E402
    adapt_input_training_records,
    apply_delta_checkpoint,
    formula_score_vector,
    load_delta_checkpoint,
    model_state_sha256,
    select_formula_candidate,
    train_adam_with_snapshots,
    training_order,
)
from scripts.phases.gpu_run5_phase6 import (  # noqa: E402
    _panel_rows,
    _restore_base,
    _save_current_delta,
    _selected_rows,
    _validation_cell_ce,
    _variants_per_family,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", default=os.environ.get("LANSR_RUN_ID"))
    parser.add_argument("--stage", required=True, choices=("validation", "final-test"))
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--allow-cpu", action="store_true")
    return parser.parse_args()


def write_json(path: Path, payload: Any) -> Path:
    return _write_json(path, sanitize_nonfinite(payload))


def _verified_artifact(root: Path, *, phase: int, name: str, manifest: Mapping[str, Any]) -> Path:
    path = root / f"phase{phase}" / name
    expected = str((manifest.get("artifact_sha256") or {}).get(name, ""))
    if not path.is_file() or len(expected) != 64 or sha256_file(path) != expected:
        raise RuntimeError(f"Phase {phase} artifact is missing or hash-mismatched: {name}")
    return path


def _complete_manifest(root: Path, phase: int) -> dict[str, Any]:
    path = root / f"phase{phase}" / "manifest.json"
    payload = read_json(path, {})
    if payload.get("status") != "complete" or not all((payload.get("go_conditions") or {}).values()):
        raise RuntimeError(f"Phase {phase} is not complete with all Go conditions true")
    return payload


def _validation_inputs(root: Path) -> dict[str, Any]:
    """Authorize an exhaustive pre-test allowlist; sealed files are absent here."""
    manifests = {phase: _complete_manifest(root, phase) for phase in (2, 3, 4, 6, 7)}
    test_flags = {
        "phase2": manifests[2].get("test_accessed"),
        "phase3": manifests[3].get("test_accessed"),
        "phase4": manifests[4].get("grn_test_accessed"),
        "phase6": manifests[6].get("test_accessed"),
        "phase7": manifests[7].get("test_accessed"),
    }
    if any(value is not False for value in test_flags.values()):
        raise RuntimeError(f"upstream test-firewall provenance invalid: {test_flags}")
    paths = {
        "main_train": _verified_artifact(root, phase=2, name="train.json", manifest=manifests[2]),
        "main_validation": _verified_artifact(root, phase=2, name="validation.json", manifest=manifests[2]),
        "holdout_train": _verified_artifact(root, phase=2, name="family_holdout_train.json", manifest=manifests[2]),
        "holdout_validation": _verified_artifact(root, phase=2, name="family_holdout_validation.json", manifest=manifests[2]),
        "reduced_main": _verified_artifact(root, phase=4, name="fixed_grn_validation_panel.json", manifest=manifests[4]),
        "phase3_p6": _verified_artifact(root, phase=3, name="p6_validation.json", manifest=manifests[3]),
        "phase6_protocol": _verified_artifact(root, phase=6, name="protocol_frozen.json", manifest=manifests[6]),
        "phase6_confirmation": _verified_artifact(root, phase=6, name="confirmation_summary.json", manifest=manifests[6]),
        "phase6_checkpoints": _verified_artifact(root, phase=6, name="checkpoint_index.json", manifest=manifests[6]),
        "phase7_layer_freeze": _verified_artifact(root, phase=7, name="layer_freeze.json", manifest=manifests[7]),
        "phase7_handoff": _verified_artifact(root, phase=7, name="phase8_handoff.json", manifest=manifests[7]),
    }
    protocol = read_json(paths["phase6_protocol"], {})
    by_view = protocol.get("candidate_selection_by_view")
    artifact_by_view = protocol.get("candidate_selection_artifact_sha256_by_view")
    if not isinstance(by_view, Mapping) or not isinstance(artifact_by_view, Mapping):
        raise RuntimeError("Phase 6 lacks explicit view-scoped candidate-selection contracts")
    normalized = {}
    for view in VIEWS:
        row = dict(by_view.get(view) or {})
        declared = str(artifact_by_view.get(view, ""))
        if len(declared) != 64:
            raise RuntimeError(f"Phase 6 selection artifact hash missing for {view}")
        row["source_artifact_sha256"] = declared
        row["allowed_families"] = (
            [f"R{index:02d}" for index in range(1, 9)]
            if view == "main"
            else ["R06"]
        )
        normalized[view] = row
    selections = validate_selection_contracts(normalized)
    layer_freeze = read_json(paths["phase7_layer_freeze"], {})
    handoff = read_json(paths["phase7_handoff"], {})
    if handoff.get("schema_version") != "gpu_run5_phase7_to_phase8_handoff_v1":
        raise RuntimeError("unsupported Phase 7 to Phase 8 handoff schema")
    layer_handoff = handoff.get("layer_freeze") or {}
    if handoff.get("test_accessed") is not False or layer_handoff.get("confirmation_reselected_rank") is not False:
        raise RuntimeError("Phase 7 handoff does not preserve the reduced-panel rank freeze")
    if str(layer_handoff.get("sha256")) != sha256_file(paths["phase7_layer_freeze"]):
        raise RuntimeError("Phase 7 handoff layer-freeze hash mismatch")
    for view in VIEWS:
        handoff_view = (handoff.get("views") or {}).get(view) or {}
        if str(handoff_view.get("candidate_selection_sha256", "")) != fingerprint_json(selections[view]):
            raise RuntimeError(f"Phase 7 handoff selection-contract drift for {view}")
        if str(handoff_view.get("candidate_selection_source_artifact_sha256", "")) != str(selections[view]["source_artifact_sha256"]):
            raise RuntimeError(f"Phase 7 handoff selection-source drift for {view}")
        if handoff_view.get("layer_sets") != {
            key: layer_freeze["views"][view][key]
            for key in ("top1", "top3", "causal_top3", "bottom3", "random3")
        }:
            raise RuntimeError(f"Phase 7 handoff layer-set drift for {view}")
    return {
        "paths": paths,
        "manifests": manifests,
        "test_flags": test_flags,
        "candidate_selection": selections,
        "layer_freeze": layer_freeze,
        "layer_sets": expected_layer_sets(layer_freeze),
    }


def _checkpoint_path(record: Mapping[str, Any], root: Path) -> Path:
    path = Path(str(record["path"]))
    if not path.is_absolute():
        path = root / path
    return path


def _apply_checkpoint(
    model: torch.nn.Module,
    base_state: Mapping[str, torch.Tensor],
    record: Mapping[str, Any],
    *,
    root: Path,
) -> None:
    _restore_base(model, base_state)
    if record.get("condition") == "frozen":
        return
    checkpoint = load_delta_checkpoint(
        _checkpoint_path(record, root), expected_file_sha256=str(record["file_sha256"])
    )
    apply_delta_checkpoint(
        model,
        checkpoint,
        allowed_parameter_keys=list(record["parameter_keys"]),
        expected_identity=dict(record["identity"]),
    )
    verification = record.get("verification") or {}
    expected_state = verification.get("adapted_state_sha256") or verification.get(
        "adapted_model_state_sha256_after_reload"
    )
    if expected_state is not None and model_state_sha256(model) != str(expected_state):
        raise RuntimeError("adapted checkpoint state hash mismatch")


def _records_by_condition(records: Sequence[Mapping[str, Any]]) -> dict[str, dict[str, dict[str, Any]]]:
    output: dict[str, dict[str, dict[str, Any]]] = {view: {} for view in VIEWS}
    for source in records:
        row = dict(source)
        view, condition, bundle = str(row.get("view")), str(row.get("condition")), str(row.get("bundle_index"))
        if view not in output or condition not in {"official_continued_full", "grn_full", "grn_decoder_all"}:
            raise ValueError(f"unexpected Phase 6 checkpoint index row: {view}/{condition}")
        output[view].setdefault(condition, {})[bundle] = row
    return output


def _base_record(*, view: str, bundle: int, checkpoint_path: Path, file_sha: str, state_sha: str) -> dict[str, Any]:
    return {
        "view": view,
        "condition": "frozen",
        "bundle_index": int(bundle),
        "path": checkpoint_path.as_posix(),
        "file_sha256": file_sha,
        "checkpoint_sha256": state_sha,
        "delta_sha256": state_sha,
        "parameter_keys": [],
        "identity": {"condition": "frozen", "view": view, "bundle_index": int(bundle)},
    }


def _verify_checkpoint_registry_files(registry: Mapping[str, Mapping[str, Mapping[str, Any]]], *, root: Path) -> None:
    for view in VIEWS:
        for condition in FINAL_CONDITIONS:
            for bundle, record in registry[view][condition].items():
                path = _checkpoint_path(record, root)
                if not path.is_file() or sha256_file(path) != str(record.get("file_sha256")):
                    raise RuntimeError(f"checkpoint file drift before Go 7: {view}/{condition}/bundle{bundle}")
                if condition == "frozen":
                    continue
                verification = record.get("verification") or {}
                required = [
                    value
                    for key, value in verification.items()
                    if key.endswith("_verified")
                    or key.endswith("_matches_expected")
                    or key in {"adapted_state_matches", "fresh_base_reload_verified"}
                ]
                if not required or not all(bool(value) for value in required):
                    raise RuntimeError(f"checkpoint verification provenance failed before Go 7: {view}/{condition}/bundle{bundle}")


def _validation_rows(data: Mapping[str, Any], *, smoke: bool, chosen_budget: Mapping[str, Any]) -> tuple[dict[str, list[dict[str, Any]]], dict[str, list[dict[str, Any]]], dict[str, list[dict[str, Any]]]]:
    main_validation = [dict(row) for row in data["main_validation"]]
    holdout_validation = [dict(row) for row in data["holdout_validation"]]
    reduced_ids = {str(row["system_id"]) for row in data["reduced_main"]}
    main_by_id = {str(row["system_id"]): row for row in main_validation}
    if not reduced_ids or not reduced_ids.issubset(main_by_id):
        raise RuntimeError("fixed reduced panel is not a main-validation subset")
    screen = {
        "main": [main_by_id[value] for value in sorted(reduced_ids)],
        "family_holdout": _panel_rows(holdout_validation, min(int(chosen_budget["reduced_panel"]), len(holdout_validation))),
    }
    confirmation = {"main": main_validation, "family_holdout": holdout_validation}
    train = {"main": list(data["main_train"]), "family_holdout": list(data["holdout_train"])}
    if smoke:
        screen["main"] = screen["main"][: int(chosen_budget["reduced_panel"])]
        train = {view: _variants_per_family(rows, int(chosen_budget["train_variants_per_family"])) for view, rows in train.items()}
        confirmation = {view: _variants_per_family(rows, int(chosen_budget["validation_variants_per_family"])) for view, rows in confirmation.items()}
    elif len(screen["main"]) != 24 or len(screen["family_holdout"]) != 10:
        raise RuntimeError("authoritative Phase 8 screening panels must be main=24 and holdout=10")
    return train, screen, confirmation


def _validation_stage(args: argparse.Namespace) -> int:
    started_utc, started = utc_now(), perf_counter()
    config, root = load_config(), run_dir(args.run_id)
    inputs = _validation_inputs(root)
    git = git_info()
    if git["status_short"]:
        raise RuntimeError(f"authoritative Phase 8 validation requires a clean worktree: {git['status_short']}")
    out = phase_dir(args.run_id, 8)
    chosen_budget = budget(config, args.smoke)
    mode = "smoke" if args.smoke else "full"
    if any(str(inputs["manifests"][phase].get("mode")) != mode for phase in (6, 7)):
        raise RuntimeError("Phase 8 mode must exactly match Phase 6 and Phase 7")
    if (out / "test_open_ledger.json").exists():
        raise RuntimeError("validation cannot run after a test-open event exists")
    data = {
        key: read_json(path)
        for key, path in inputs["paths"].items()
        if key in {"main_train", "main_validation", "holdout_train", "holdout_validation", "reduced_main"}
    }
    if any(not isinstance(value, list) for value in data.values()):
        raise RuntimeError("an authorized Phase 8 corpus artifact is not a list")
    train_rows, screen_rows, confirmation_rows = _validation_rows(
        data, smoke=args.smoke, chosen_budget=chosen_budget
    )
    n_bundles = int(chosen_budget["n_seeds"])
    random_count = int(chosen_budget["random_sets"])
    if not args.smoke and (n_bundles != 3 or random_count != 5):
        raise RuntimeError("authoritative validation requires 3 bundles and five random sets")
    conditions = selective_conditions(random_count)
    layer_sets = {
        view: {condition: inputs["layer_sets"][view][condition] for condition in conditions}
        for view in VIEWS
    }
    learning_rates = [float(value) for value in chosen_budget["hyperparameter_learning_rates"]]
    steps = [int(value) for value in chosen_budget["hyperparameter_steps"]]
    grid = hyperparameter_grid(learning_rates, steps)
    if not args.smoke and len(grid) != 9:
        raise RuntimeError("authoritative selective conditions require the exact 3x3 grid")
    device = select_device(allow_cpu=args.allow_cpu)
    checkpoint_path = ROOT / str(config["odeformer_checkpoint"])
    raw_file_sha = sha256_file(checkpoint_path)
    if raw_file_sha != str(config["odeformer_checkpoint_sha256"]):
        raise RuntimeError("base checkpoint hash mismatch")
    model = load_odeformer_model(checkpoint_path, device=device)
    inventory = inventory_odeformer(model)
    if len(inventory["ranking_layers"]) != 16:
        raise RuntimeError("Phase 8 requires the released 4+12 ODEFormer")
    base_sha = model_state_sha256(model)
    base_state = {key: value.detach().cpu().clone() for key, value in model.state_dict().items()}
    selection_hashes = {view: fingerprint_json(inputs["candidate_selection"][view]) for view in VIEWS}
    layer_freeze_file_sha = sha256_file(inputs["paths"]["phase7_layer_freeze"])
    panel_hashes = {
        f"{stage}:{view}": fingerprint_json([str(row["system_id"]) for row in rows])
        for stage, mapping in (("screen", screen_rows), ("confirmation", confirmation_rows))
        for view, rows in mapping.items()
    }
    campaign = {
        "schema_version": "gpu_run5_phase8_validation_campaign_v1",
        "git_commit": git["commit"],
        "mode": mode,
        "config_fingerprint": fingerprint_json(config),
        "base_checkpoint_file_sha256": raw_file_sha,
        "base_model_state_sha256": base_sha,
        "phase6_manifest_sha256": sha256_file(root / "phase6" / "manifest.json"),
        "phase7_manifest_sha256": sha256_file(root / "phase7" / "manifest.json"),
        "layer_freeze_file_sha256": layer_freeze_file_sha,
        "selection_contract_sha256_by_view": selection_hashes,
        "conditions": list(conditions),
        "grid": grid,
        "screening_beam_size": int(config["training"]["screening_beam_size"]),
        "confirmation_beam_size": int(chosen_budget["beam_size"] if args.smoke else config["training"]["confirmation_beam_size"]),
        "test_accessed": False,
    }
    campaign_sha = fingerprint_json(campaign)
    write_json(out / "validation_protocol_frozen.json", campaign)
    p6_validation = read_json(inputs["paths"]["phase3_p6"], {})
    p6_for_go8 = {
        "source": "phase3_validation_only",
        "source_artifact_sha256": sha256_file(inputs["paths"]["phase3_p6"]),
        "prediction_P6": p6_validation.get("prediction_P6"),
        "ci95_upper": p6_validation.get("ci95_upper"),
        "supported": p6_validation.get("prediction_P6") == "supported"
        and float(p6_validation.get("ci95_upper", float("inf"))) < 0.0,
        "test_accessed": False,
    }
    write_json(out / "p6_for_go8.json", p6_for_go8)
    screen_beam = int(config["training"]["screening_beam_size"])
    confirmation_beam = int(chosen_budget["beam_size"] if args.smoke else config["training"]["confirmation_beam_size"])
    max_steps = max(steps)
    screening_paths: list[Path] = []
    selections: dict[str, Any] = {"schema_version": "gpu_run5_phase8_selective_hyperparameter_freeze_v1", "views": {}, "test_accessed": False}
    selected_screen_delta: dict[tuple[str, str], str] = {}
    for view in VIEWS:
        rows = screen_rows[view]
        seed_map = candidate_seed_map(rows, config=config, bundle_indices=[0])
        expected_cells = sorted(seed_map)
        selections["views"][view] = {}
        normalized_train = adapt_input_training_records(train_rows[view])
        schedule = training_order(normalized_train, steps=max_steps, seed=int(config["seed_bundles"][0]["data_seed"]))
        for condition in conditions:
            layers = set(layer_sets[view][condition])
            trial = phase8_trial_identity(
                view=view, condition=condition, layers=sorted(layers), bundle_indices=[0],
                base_model_state_sha256=base_sha,
                training_corpus_sha256=schedule["training_corpus_sha256"],
                training_order_sha256=schedule["order_sha256"],
                model_seed=int(config["seed_bundles"][0]["model_seed"]),
                validation_panel_sha256=panel_hashes[f"screen:{view}"],
                candidate_seed_map_sha256=candidate_seed_map_sha256(seed_map),
                layer_freeze_sha256=layer_freeze_file_sha,
                selection_contract_sha256=selection_hashes[view],
            )
            candidates = []
            for lr in learning_rates:
                _restore_base(model, base_state)
                result = train_adam_with_snapshots(
                    model, train_rows[view], trainable_layers=layers, lr=lr,
                    max_steps=max_steps, snapshot_steps=steps,
                    data_order_seed=int(config["seed_bundles"][0]["data_seed"]),
                    model_seed=int(config["seed_bundles"][0]["model_seed"]),
                )
                for step in steps:
                    cfg = {"lr": lr, "steps": step}
                    if step not in result["snapshots"]:
                        candidates.append({
                            "status": "failed", "failure_reason": result["failure_reason"] or "MissingExactSnapshot",
                            "config": cfg, "trial_identity": trial, "validation_cell_ids": [],
                            "score_vector": [0.0, -1.0, 0.0, -float("inf")],
                            "training": {key: value for key, value in result.items() if key != "snapshots"},
                        })
                        continue
                    from gpu_run5.training import restore_parameter_state
                    restore_parameter_state(model, result["snapshots"][step], allowed_parameter_keys=result["trainable_parameter_keys"])
                    delta_identity = {**trial, "stage": "validation_screening", "lr": lr, "steps": step, "raw_checkpoint_sha256": raw_file_sha, "config_fingerprint": fingerprint_json(config), "training_source": f"{view}_grn_train"}
                    delta = _save_current_delta(
                        model, out_path=out / "checkpoints" / "screening" / view / condition / f"lr{lr:g}_s{step}.pt",
                        parameter_keys=result["trainable_parameter_keys"], identity=delta_identity,
                        layers=layers, base_sha=base_sha, persist=False,
                    )
                    cells, paths = decode_panel(
                        model=model, rows=rows, config=config,
                        selection_contract=inputs["candidate_selection"][view],
                        selection_contract_sha256=selection_hashes[view], out=out,
                        campaign_identity_sha256=campaign_sha, stage="validation_screening",
                        view=view, condition=condition, checkpoint_sha256=delta["delta_sha256"],
                        beam_size=screen_beam, bundle_indices=[0], seed_maps={0: seed_map},
                    )
                    screening_paths.extend(paths)
                    coverage = coverage_audit(cells, expected_cell_ids=expected_cells, expected_beam_size=screen_beam, expected_seed_map=seed_map)
                    ce, ce_rows = _validation_cell_ce(model, rows, config=config, bundle_indices=[0])
                    score = formula_score_vector(_selected_rows(cells, ce_rows), expected_cell_ids=expected_cells)
                    candidates.append({
                        "status": "complete", "failure_reason": None, "config": cfg,
                        "trial_identity": trial, "validation_cell_ids": expected_cells,
                        "score_vector": list(score), "coverage_audit": coverage,
                        "validation_teacher_forcing_ce": ce, "validation_ce_rows": ce_rows,
                        "delta": delta, "training": {key: value for key, value in result.items() if key not in {"snapshots", "losses"}},
                        "losses": result["losses"][:step],
                    })
                del result
                gc.collect()
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
            selected = select_formula_candidate(
                candidates, expected_count=len(grid), expected_lrs=learning_rates,
                expected_steps=steps, quantization_digits=12,
                expected_validation_cell_ids=expected_cells,
            )
            selections["views"][view][condition] = selected
            selected_screen_delta[(view, condition)] = str(selected["selected"]["delta"]["delta_sha256"])
            print(f"Phase8 validation grid {view}/{condition}: {selected['selected']['config']}", flush=True)
    write_json(out / "selective_hyperparameter_freeze.json", selections)
    hyper_freeze_file_sha = sha256_file(out / "selective_hyperparameter_freeze.json")

    confirmation_paths: list[Path] = []
    checkpoint_records: list[dict[str, Any]] = []
    confirmation_summary: dict[str, Any] = {}
    bundle_indices = list(range(n_bundles))
    for view in VIEWS:
        rows = confirmation_rows[view]
        seed_maps = {bundle: candidate_seed_map(rows, config=config, bundle_indices=[bundle]) for bundle in bundle_indices}
        merged_seed_map = {key: value for mapping in seed_maps.values() for key, value in mapping.items()}
        expected_cells = sorted(merged_seed_map)
        confirmation_summary[view] = {}
        for condition in conditions:
            cfg = selections["views"][view][condition]["selected"]["config"]
            layers = set(layer_sets[view][condition])
            all_cells, ce_rows = [], []
            for bundle_index in bundle_indices:
                _restore_base(model, base_state)
                bundle = config["seed_bundles"][bundle_index]
                result = train_adam_with_snapshots(
                    model, train_rows[view], trainable_layers=layers,
                    lr=float(cfg["lr"]), max_steps=int(cfg["steps"]), snapshot_steps=[int(cfg["steps"])],
                    data_order_seed=int(bundle["data_seed"]), model_seed=int(bundle["model_seed"]),
                )
                if result["status"] != "complete" or int(cfg["steps"]) not in result["snapshots"]:
                    raise RuntimeError(f"selected training failed: {view}/{condition}/bundle{bundle_index}")
                identity = {
                    **phase8_trial_identity(
                        view=view, condition=condition, layers=sorted(layers), bundle_indices=[bundle_index],
                        base_model_state_sha256=base_sha,
                        training_corpus_sha256=result["training_corpus_sha256"], training_order_sha256=result["order_sha256"],
                        model_seed=int(bundle["model_seed"]), validation_panel_sha256=panel_hashes[f"confirmation:{view}"],
                        candidate_seed_map_sha256=candidate_seed_map_sha256(seed_maps[bundle_index]),
                        layer_freeze_sha256=layer_freeze_file_sha, selection_contract_sha256=selection_hashes[view],
                    ),
                    "stage": "validation_confirmation", "lr": float(cfg["lr"]), "steps": int(cfg["steps"]),
                    "raw_checkpoint_sha256": raw_file_sha, "config_fingerprint": fingerprint_json(config),
                    "training_source": f"{view}_grn_train",
                }
                delta = _save_current_delta(
                    model, out_path=out / "checkpoints" / "confirmation" / view / condition / f"bundle{bundle_index}.pt",
                    parameter_keys=result["trainable_parameter_keys"], identity=identity, layers=layers, base_sha=base_sha, persist=True,
                )
                loaded = load_delta_checkpoint(Path(delta["path"]), expected_file_sha256=delta["file_sha256"])
                _restore_base(model, base_state)
                apply_delta_checkpoint(model, loaded, allowed_parameter_keys=result["trainable_parameter_keys"], expected_identity=identity)
                adapted_sha = model_state_sha256(model)
                delta.update({
                    "view": view, "condition": condition, "bundle_index": bundle_index,
                    "verification": {"fresh_base_reload_verified": True, "adapted_state_sha256": adapted_sha},
                    "training": {key: value for key, value in result.items() if key not in {"snapshots", "losses"}},
                })
                if bundle_index == 0 and delta["delta_sha256"] != selected_screen_delta[(view, condition)]:
                    raise RuntimeError("bundle0 selected confirmation does not reproduce screening delta")
                checkpoint_records.append(delta)
                cells, paths = decode_panel(
                    model=model, rows=rows, config=config,
                    selection_contract=inputs["candidate_selection"][view], selection_contract_sha256=selection_hashes[view],
                    out=out, campaign_identity_sha256=campaign_sha, stage="validation_confirmation",
                    view=view, condition=condition, checkpoint_sha256=adapted_sha,
                    beam_size=confirmation_beam, bundle_indices=[bundle_index], seed_maps={bundle_index: seed_maps[bundle_index]},
                )
                all_cells.extend(cells)
                confirmation_paths.extend(paths)
                _, rows_ce = _validation_cell_ce(model, rows, config=config, bundle_indices=[bundle_index])
                ce_rows.extend(rows_ce)
            coverage = coverage_audit(all_cells, expected_cell_ids=expected_cells, expected_beam_size=confirmation_beam, expected_seed_map=merged_seed_map)
            score = formula_score_vector(_selected_rows(all_cells, ce_rows), expected_cell_ids=expected_cells)
            confirmation_summary[view][condition] = {"score_vector": list(score), "cells": len(all_cells), "coverage_audit": coverage, "selected_config": cfg}
    write_json(out / "selective_confirmation_summary.json", confirmation_summary)
    write_json(out / "selective_checkpoint_index.json", checkpoint_records)

    phase6_summary = read_json(inputs["paths"]["phase6_confirmation"], {})
    combined_scores = {
        view: {
            **{condition: list(phase6_summary[view][condition]["score_vector"]) for condition in REUSED_VALIDATION_CONDITIONS},
            **{condition: list(confirmation_summary[view][condition]["score_vector"]) for condition in conditions},
        }
        for view in VIEWS
    }
    write_json(out / "validation_condition_scores.json", combined_scores)
    go6 = (
        evaluate_go6(combined_scores["main"], random_sets_to_beat=int(config["final_test"]["go6_random_sets_to_beat"]))
        if not args.smoke else
        {"pass": False, "test_accessed": False, "reason": "smoke_is_never_authoritative_for_Go6_or_final_test"}
    )
    write_json(out / "go6.json", go6)
    phase6_index = _records_by_condition(read_json(inputs["paths"]["phase6_checkpoints"], []))
    own_by_view: dict[str, dict[str, dict[str, Any]]] = {view: {} for view in VIEWS}
    for row in checkpoint_records:
        own_by_view[str(row["view"])].setdefault(str(row["condition"]), {})[str(row["bundle_index"])] = row
    final_freeze = None
    go7 = {"pass": False, "test_accessed": False, "reason": "Go6_failed_or_smoke"}
    if go6.get("pass") is True:
        registry: dict[str, Any] = {}
        for view in VIEWS:
            registry[view] = {
                "frozen": {str(bundle): _base_record(view=view, bundle=bundle, checkpoint_path=checkpoint_path, file_sha=raw_file_sha, state_sha=base_sha) for bundle in bundle_indices},
                "official_continued_full": phase6_index[view]["official_continued_full"],
                "grn_full": phase6_index[view]["grn_full"],
                "grn_top3": own_by_view[view]["grn_top3"],
                "grn_random3_0": own_by_view[view]["grn_random3_0"],
            }
        _verify_checkpoint_registry_files(registry, root=root)
        final_freeze = build_final_freeze(
            checkpoint_registry=registry, layer_sets=inputs["layer_sets"],
            candidate_selection=inputs["candidate_selection"],
            upstream_manifest_sha256={
                "phase3": sha256_file(root / "phase3" / "manifest.json"),
                "phase6": sha256_file(root / "phase6" / "manifest.json"),
                "phase7": sha256_file(root / "phase7" / "manifest.json"),
                "phase3_p6": sha256_file(inputs["paths"]["phase3_p6"]),
            },
            config_fingerprint=fingerprint_json(config), layer_freeze_sha256=layer_freeze_file_sha,
            validation_freeze_sha256=hyper_freeze_file_sha, expected_bundles=3, beam_size=50,
            corruptions=corruption_grid(config),
        )
        write_json(out / "final_condition_freeze.json", final_freeze)
        upstream_flags = {
            "phase2": inputs["manifests"][2].get("test_accessed"),
            "phase3": read_json(root / "phase3" / "manifest.json", {}).get("test_accessed"),
            "phase4": inputs["manifests"][4].get("grn_test_accessed"),
            "phase5": read_json(root / "phase5" / "manifest.json", {}).get("test_accessed"),
            "phase6": inputs["manifests"][6].get("test_accessed"),
            "phase7": inputs["manifests"][7].get("test_accessed"),
        }
        go7 = audit_go7(final_freeze, go6=go6, upstream_test_accessed=upstream_flags, observed_freeze_sha256=final_freeze["freeze_sha256"])
    write_json(out / "go7.json", go7)
    expected = expected_phase8_validation_counts(
        screen_systems={view: len(rows) for view, rows in screen_rows.items()},
        confirmation_systems={view: len(rows) for view, rows in confirmation_rows.items()},
        n_grid_candidates=len(grid), n_bundles=n_bundles,
        n_corruptions=len(corruption_grid(config)), random_set_count=random_count,
    )
    all_paths = screening_paths + confirmation_paths
    write_json(out / "validation_cell_artifact_index.json", artifact_index(all_paths, relative_to=out))
    validation_complete = (
        len(all_paths) == expected["all_decode_cells_total"]
        and len(checkpoint_records) == expected["selected_training_trials"]
        and all(row["coverage_audit"]["pass"] for view in VIEWS for row in confirmation_summary[view].values())
    )
    # A negative Go 6 is a valid scientific outcome: validation is complete,
    # the sealed test remains unopened, and Phase 9 reports P3/P4/P7 as
    # undecidable.  It must not be mislabeled as an execution failure.
    status = "complete" if validation_complete else "incomplete"
    summary = {
        "status": status, "mode": mode, "validation_complete": validation_complete,
        "expected_counts": expected, "observed_cells": len(all_paths),
        "condition_scores": combined_scores, "go6": go6, "go7": go7,
        "final_test_authorized": bool(not args.smoke and go6.get("pass") and go7.get("pass")),
        "test_accessed": False,
    }
    write_json(out / "validation_summary.json", summary)
    artifacts = [
        "validation_protocol_frozen.json", "p6_for_go8.json", "selective_hyperparameter_freeze.json",
        "selective_confirmation_summary.json", "selective_checkpoint_index.json",
        "validation_condition_scores.json", "go6.json", "go7.json",
        "validation_cell_artifact_index.json", "validation_summary.json",
    ] + (["final_condition_freeze.json"] if final_freeze is not None else [])
    go_conditions = {
        "validation_cells_and_checkpoints_complete": validation_complete,
        "test_not_accessed": True,
        "go6_evaluated_without_test_access": bool(args.smoke or "pass" in go6),
        "go7_evaluated_or_blocked_by_go6": bool(args.smoke or "pass" in go7),
        "git_clean_and_stable": git_info()["commit"] == git["commit"] and not git_info()["status_short"],
    }
    write_manifest(
        out, 8, status, substage="validation", go_conditions=go_conditions,
        git=git_info(), git_at_start=git, started_utc=started_utc, finished_utc=utc_now(),
        wall_time_sec=perf_counter() - started, mode=mode, device=device,
        environment=software_versions(), test_accessed=False,
        final_test_authorized=summary["final_test_authorized"],
        final_condition_freeze_sha256=(sha256_file(out / "final_condition_freeze.json") if final_freeze is not None else None),
        artifact_sha256={name: sha256_file(out / name) for name in artifacts},
    )
    print(f"GPU_RUN5 Phase 8 validation {status}: cells={len(all_paths)} Go6={go6.get('pass')} Go7={go7.get('pass')}", flush=True)
    return 0 if status == "complete" else 1


def _audit_test_sets(main: Sequence[Mapping[str, Any]], holdout: Sequence[Mapping[str, Any]], *, config: Mapping[str, Any]) -> dict[str, Any]:
    main_ids = [str(row["system_id"]) for row in main]
    holdout_ids = [str(row["system_id"]) for row in holdout]
    allowed = sorted(str(value) for value in config["family_holdout"]["sealed_test_families"])
    checks = {
        "main_ids_unique": len(main_ids) == len(set(main_ids)),
        "holdout_ids_unique": len(holdout_ids) == len(set(holdout_ids)),
        "holdout_exact_subset_of_main": set(holdout_ids) == {str(row["system_id"]) for row in main if str(row["family"]) in set(allowed)},
        "holdout_families_exact": sorted({str(row["family"]) for row in holdout}) == allowed,
        "main_exact_80": len(main) == 80,
        "holdout_exact_20": len(holdout) == 20,
    }
    return {"checks": checks, "pass": all(checks.values()), "label": str(config["family_holdout"]["label"]), "subset_not_independent_second_test": True}


def _test_summary(cells: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    expected_ids = [str(row["cell_id"]) for row in cells]
    selected = [{"cell_id": str(row["cell_id"]), "system_id": str(row["system_id"]), "bundle_index": int(row["bundle_index"]), **dict(row["selected"])} for row in cells]
    score = formula_score_vector(selected, validation_ce=0.0, expected_cell_ids=expected_ids)
    exact = [float(value) for row in selected for value in (row.get("component_exponent_aware_skeleton_exact") or [0.0])]
    ted = [float(value) for row in selected for value in (row.get("component_normalized_variable_aware_ted") or [1.0])]
    valid = [float(value) for row in selected for value in (row.get("component_valid") or [False])]
    recon_r2, failures = [], []
    gen_grouped: dict[int, dict[str, list[float]]] = {}
    nontrivial_exact = 0
    for cell in cells:
        metrics = cell.get("selected_clean_trajectory_metrics") or {}
        roles = metrics.get("roles") or {}
        recon_r2.extend(float(row["r2"]) for row in roles.get("input", []))
        gen_values = [float(row["nrmse"]) for row in roles.get("generalization", [])]
        gen_grouped.setdefault(int(cell["bundle_index"]), {}).setdefault(str(cell["system_id"]), []).extend(gen_values)
        failures.extend(str(row["failure"]) for values in roles.values() for row in values if row.get("failure"))
        if str(cell["family"]) in {"R03", "R04", "R05", "R06", "R07", "R08"}:
            flags = list((cell.get("true_structure") or {}).get("component_flags") or [])
            selected_exact = list((cell.get("selected") or {}).get("component_exponent_aware_skeleton_exact") or [])
            for index, flag in enumerate(flags):
                is_nontrivial = any(
                    bool(flag.get(name))
                    for name in ("hill_form", "modulated_hill_form", "variable_denominator_form")
                )
                if is_nontrivial and index < len(selected_exact) and float(selected_exact[index]) == 1.0:
                    nontrivial_exact += 1
    seed_gen = []
    for systems in gen_grouped.values():
        system_means = [float(np.mean(values)) for values in systems.values() if values]
        seed_gen.append(float(np.mean(system_means)) if system_means else float("inf"))
    gen_nrmse_macro = float(np.mean(seed_gen)) if seed_gen and all(map(math.isfinite, seed_gen)) else float("inf")
    return {
        "formula_score_vector_without_ce": list(score[:3]),
        "component_exponent_aware_skeleton_exact_rate": float(np.mean(exact)) if exact else 0.0,
        "failure_aware_component_ted_mean": float(np.mean(ted)) if ted else 1.0,
        "component_valid_rate": float(np.mean(valid)) if valid else 0.0,
        "reconstruction_r2_median": float(np.median(recon_r2)) if recon_r2 else -10.0,
        "failure_aware_generalization_nrmse_system_then_seed_macro": gen_nrmse_macro,
        "nontrivial_R03_R08_exact_component_cell_count": nontrivial_exact,
        "n_generation_failures": sum(bool(row.get("generation_failure")) for row in cells),
        "n_selected_trajectory_failures": len(failures),
        "selected_trajectory_failure_reasons": sorted({value for value in failures}),
        "cells": len(cells),
    }


def _odebench_forgetting(
    *, model: Any, base_state: Mapping[str, torch.Tensor], registry: Mapping[str, Mapping[str, Any]],
    config: Mapping[str, Any], root: Path, out: Path,
) -> dict[str, Any]:
    """Secondary main-view ODEBench evaluation; never used for selection."""
    equations = load_odebench_equations()
    selected_records, paths = [], []
    for condition in FINAL_CONDITIONS:
        for bundle_index in range(3):
            record = registry[condition][str(bundle_index)]
            _apply_checkpoint(model, base_state, record, root=root)
            bundle = config["seed_bundles"][bundle_index]
            for item in equations:
                pair = reconstruct_and_generalize(item, n_points=150)
                ground_truth_failure = None
                if not pair["recon"]["success"] or not pair["gen"]["success"]:
                    ground_truth_failure = "GroundTruthReconstructionFailure"
                recon = (
                    {"times": pair["recon"]["times"], "trajectory": pair["recon"]["trajectory"], "y0": pair["y0_recon"]}
                    if ground_truth_failure is None else None
                )
                gen = (
                    {"times": pair["gen"]["times"], "trajectory": pair["gen"]["trajectory"], "y0": pair["y0_gen"]}
                    if ground_truth_failure is None else None
                )
                for sigma, rho in corruption_grid(config):
                    cell_name = f"ode{int(item['id'])}|b{bundle_index}|n{sigma:g}|r{rho:g}"
                    path = out / "odebench_forgetting" / condition / f"{cell_name.replace('.', 'p')}.json"
                    seed = __import__("gpu_run5.seeding", fromlist=["stable_problem_seed"]).stable_problem_seed(
                        int(bundle["candidate_seed"]), system_id=f"odebench_{item['id']}", condition="phase8_odebench_paired",
                        noise_sigma=sigma, subsample_rho=rho, sampling_replicate=bundle_index,
                    )
                    identity = {
                        "condition": condition, "bundle_index": bundle_index, "eq_id": int(item["id"]),
                        "noise_sigma": sigma, "subsample_rho": rho, "candidate_seed": int(seed),
                        "checkpoint_sha256": str(record["checkpoint_sha256"]), "beam_size": 50,
                    }
                    cached = read_json(path)
                    if not isinstance(cached, Mapping) or cached.get("identity") != identity:
                        if ground_truth_failure is not None:
                            cached = {"identity": identity, "records": [], "generation_failure": ground_truth_failure}
                            write_json(path, cached)
                            paths.append(path)
                            selected_records.append({
                                "condition": condition, "bundle_index": bundle_index,
                                "cell_id": cell_name, "selected": None,
                                "generation_failure": ground_truth_failure,
                            })
                            continue
                        times, observed = corrupt_trajectory(
                            np.asarray(recon["times"]), np.asarray(recon["trajectory"]), sigma=sigma, rho=rho,  # type: ignore[index]
                            seed=int(bundle["corruption_seed"]) + int(item["id"]),
                        )
                        try:
                            result = evaluate_system(
                                item, regressor=make_regressor(model, config, beam_size=50, seed=int(seed)),
                                recon=recon, gen=gen, times_obs=times, traj_obs=observed,  # type: ignore[arg-type]
                                sigma=sigma, rho=rho, seed=int(bundle["data_seed"]), permutation_seed=int(seed),
                                condition=condition, split="odebench_forgetting_secondary", beam_size=50,
                                beam_temperature=float(config["paper_protocol"]["beam_temperature"]),
                                integration_timeout=10.0, gen_timeout=10.0, bfgs_timeout=10.0,
                                save_all_candidates=True, run_opt=False,
                            )
                            cached = {"identity": identity, "records": result["records"], "generation_failure": None}
                        except torch.cuda.OutOfMemoryError:
                            raise
                        except Exception as exc:
                            cached = {"identity": identity, "records": [], "generation_failure": f"{type(exc).__name__}:{exc}"}
                        write_json(path, cached)
                    paths.append(path)
                    rows = list(cached.get("records") or [])
                    selected = next((row for row in rows if row.get("selected")), None)
                    selected_records.append({"condition": condition, "bundle_index": bundle_index, "cell_id": cell_name, "selected": selected, "generation_failure": cached.get("generation_failure")})
    summary = {}
    for condition in FINAL_CONDITIONS:
        rows = [row for row in selected_records if row["condition"] == condition]
        valid = [float(bool((row.get("selected") or {}).get("valid"))) for row in rows]
        ted = [float((row.get("selected") or {}).get("normalized_ted") if (row.get("selected") or {}).get("normalized_ted") is not None else 1.0) for row in rows]
        summary[condition] = {"cells": len(rows), "valid_rate": float(np.mean(valid)), "failure_aware_normalized_ted_mean": float(np.mean(ted))}
    write_json(out / "odebench_forgetting_index.json", artifact_index(paths, relative_to=out))
    write_json(out / "odebench_forgetting_summary.json", summary)
    return summary


def _final_test_stage(args: argparse.Namespace) -> int:
    if args.smoke:
        raise RuntimeError("smoke mode may never open the final test")
    started_utc, started = utc_now(), perf_counter()
    config, root = load_config(), run_dir(args.run_id)
    out = phase_dir(args.run_id, 8)
    manifest = read_json(out / "manifest.json", {})
    existing_ledger = read_json(out / "test_open_ledger.json")
    if isinstance(existing_ledger, Mapping) and existing_ledger.get("status") == "complete":
        final_hashes = existing_ledger.get("final_artifact_sha256") or {}
        if not final_hashes or any(
            not (out / name).is_file() or sha256_file(out / name) != expected
            for name, expected in final_hashes.items()
        ):
            raise RuntimeError("completed test-open ledger has missing or drifted final artifacts")
        if manifest.get("substage") == "final-test" and manifest.get("status") == "complete":
            print("GPU_RUN5 Phase 8 final test already complete; sealed tests were not reopened", flush=True)
            return 0
        freeze = read_json(out / "final_condition_freeze.json", {})
        expected_paths = {
            "main": (root / "phase2" / "sealed_test.json").as_posix(),
            "family_holdout": (root / "phase2" / "sealed_family_holdout_test.json").as_posix(),
        }
        if (
            existing_ledger.get("freeze_sha256") != freeze.get("freeze_sha256")
            or existing_ledger.get("sealed_paths") != expected_paths
            or existing_ledger.get("open_count") != 1
        ):
            raise RuntimeError("completed test-open ledger cannot recover final manifest")
        write_manifest(
            out, 8, "complete", substage="final-test",
            go_conditions={"recovered_completed_single_open_event_without_reopening_test": True},
            git=git_info(), recovered_after_ledger_completion=True, test_accessed=True,
            test_open_event_id=str(existing_ledger["event_id"]), test_open_count=1,
            final_condition_freeze_sha256=sha256_file(out / "final_condition_freeze.json"),
            sealed_artifact_sha256=existing_ledger["sealed_artifact_sha256"],
            artifact_sha256={**final_hashes, "test_open_ledger.json": sha256_file(out / "test_open_ledger.json")},
        )
        print("GPU_RUN5 Phase 8 final manifest recovered without reopening sealed tests", flush=True)
        return 0
    if manifest.get("status") != "complete" or manifest.get("substage") != "validation" or manifest.get("final_test_authorized") is not True:
        raise RuntimeError("Phase 8 validation did not authorize the final test")
    for name in ("go6.json", "go7.json", "p6_for_go8.json", "final_condition_freeze.json"):
        expected = str((manifest.get("artifact_sha256") or {}).get(name, ""))
        if len(expected) != 64 or sha256_file(out / name) != expected:
            raise RuntimeError(f"frozen Phase 8 artifact drift: {name}")
    go6, go7, freeze = read_json(out / "go6.json"), read_json(out / "go7.json"), read_json(out / "final_condition_freeze.json")
    if go6.get("pass") is not True or go7.get("pass") is not True or freeze.get("test_accessed") is not False:
        raise RuntimeError("Go 6 / Go 7 / freeze firewall does not authorize test access")
    if list(freeze.get("conditions") or []) != list(FINAL_CONDITIONS):
        raise RuntimeError("final condition freeze drift")
    sealed_paths = {
        "main": (root / "phase2" / "sealed_test.json").as_posix(),
        "family_holdout": (root / "phase2" / "sealed_family_holdout_test.json").as_posix(),
    }
    ledger = claim_test_open(
        out / "test_open_ledger.json", freeze_sha256=str(freeze["freeze_sha256"]), sealed_paths=sealed_paths
    )
    # The sole open event is durably recorded above.  Only now may sealed bytes
    # be hashed or deserialized.
    sealed_hashes = {view: sha256_file(Path(path)) for view, path in sealed_paths.items()}
    ledger = bind_test_artifact_hashes(out / "test_open_ledger.json", sealed_hashes)
    main_test = load_sealed_test(Path(sealed_paths["main"]), phase=8)
    holdout_test = load_sealed_test(Path(sealed_paths["family_holdout"]), phase=8)
    if not isinstance(main_test, list) or not isinstance(holdout_test, list):
        raise RuntimeError("sealed test artifacts must be record lists")
    test_audit = _audit_test_sets(main_test, holdout_test, config=config)
    if not test_audit["pass"]:
        raise RuntimeError(f"sealed test set audit failed: {test_audit['checks']}")
    write_json(out / "test_set_audit.json", test_audit)
    device = select_device(allow_cpu=args.allow_cpu)
    checkpoint_path = ROOT / str(config["odeformer_checkpoint"])
    model = load_odeformer_model(checkpoint_path, device=device)
    base_state = {key: value.detach().cpu().clone() for key, value in model.state_dict().items()}
    campaign = {
        "schema_version": "gpu_run5_phase8_final_test_campaign_v1",
        "final_freeze_sha256": str(freeze["freeze_sha256"]),
        "test_open_event_id": str(ledger["event_id"]),
        "sealed_artifact_sha256": sealed_hashes,
        "conditions": list(FINAL_CONDITIONS),
        "beam_size": 50,
    }
    campaign_sha = fingerprint_json(campaign)
    write_json(out / "final_test_protocol.json", campaign)
    rows_by_view = {"main": main_test, "family_holdout": holdout_test}
    final_paths, summaries = [], {}
    for view in VIEWS:
        rows = rows_by_view[view]
        contract = freeze["candidate_selection"][view]
        contract_sha = fingerprint_json(contract)
        summaries[view] = {}
        seed_maps = {bundle: candidate_seed_map(rows, config=config, bundle_indices=[bundle]) for bundle in range(3)}
        merged_seed_map = {key: value for values in seed_maps.values() for key, value in values.items()}
        expected_cells = sorted(merged_seed_map)
        for condition in FINAL_CONDITIONS:
            cells = []
            for bundle in range(3):
                record = freeze["views"][view][condition][bundle]
                _apply_checkpoint(model, base_state, record, root=root)
                part, paths = decode_panel(
                    model=model, rows=rows, config=config, selection_contract=contract,
                    selection_contract_sha256=contract_sha, out=out,
                    campaign_identity_sha256=campaign_sha, stage="final_test", view=view,
                    condition=condition, checkpoint_sha256=str(record["checkpoint_sha256"]), beam_size=50,
                    bundle_indices=[bundle], seed_maps={bundle: seed_maps[bundle]},
                    final_freeze_sha256=str(freeze["freeze_sha256"]), test_open_event_id=str(ledger["event_id"]),
                )
                cells.extend(part)
                final_paths.extend(paths)
            coverage = coverage_audit(cells, expected_cell_ids=expected_cells, expected_beam_size=50, expected_seed_map=merged_seed_map)
            if not coverage["pass"]:
                raise RuntimeError(f"final test coverage failed: {view}/{condition}")
            summaries[view][condition] = {**_test_summary(cells), "coverage_audit": coverage}
            print(f"Phase8 final test {view}/{condition}: cells={len(cells)}", flush=True)
    expected = expected_phase8_final_counts(main_systems=80, holdout_systems=20, n_bundles=3, n_corruptions=4)
    if len(final_paths) != expected["cells_total"]:
        raise RuntimeError("final test exact cell budget mismatch")
    write_json(out / "final_cell_artifact_index.json", artifact_index(final_paths, relative_to=out))
    write_json(out / "final_test_summary.json", summaries)
    main_registry = {condition: {str(row["bundle_index"]): row for row in freeze["views"]["main"][condition]} for condition in FINAL_CONDITIONS}
    forgetting = _odebench_forgetting(model=model, base_state=base_state, registry=main_registry, config=config, root=root, out=out)
    p6_for_go8 = read_json(out / "p6_for_go8.json", {})
    main_top = summaries["main"]["grn_top3"]
    main_frozen = summaries["main"]["frozen"]
    holdout_top = summaries["family_holdout"]["grn_top3"]
    holdout_frozen = summaries["family_holdout"]["frozen"]
    main_top_vector = list(main_top["formula_score_vector_without_ce"])
    main_frozen_vector = list(main_frozen["formula_score_vector_without_ce"])
    holdout_top_vector = list(holdout_top["formula_score_vector_without_ce"])
    holdout_frozen_vector = list(holdout_frozen["formula_score_vector_without_ce"])
    top_gen = float(main_top["failure_aware_generalization_nrmse_system_then_seed_macro"])
    frozen_gen = float(main_frozen["failure_aware_generalization_nrmse_system_then_seed_macro"])
    zero_tolerance = float(config["final_test"]["go8_nrmse_zero_tolerance"])
    if frozen_gen <= zero_tolerance:
        gen_ratio = 1.0 if top_gen <= zero_tolerance else float("inf")
    else:
        gen_ratio = top_gen / frozen_gen
    go8_checks = {
        "nontrivial_R03_R08_exact_recovered": int(main_top["nontrivial_R03_R08_exact_component_cell_count"]) >= 1,
        "family_holdout_top3_improves_exact_or_ted": (
            float(holdout_top_vector[0]) > float(holdout_frozen_vector[0])
            or -float(holdout_top_vector[1]) < -float(holdout_frozen_vector[1])
        ),
        "P6_supported": p6_for_go8.get("supported") is True,
        "main_valid_rate_drop_within_limit": (
            float(main_frozen_vector[2]) - float(main_top_vector[2])
            <= float(config["final_test"]["go8_valid_rate_drop_max"])
        ),
        "main_generalization_nrmse_ratio_within_limit": gen_ratio
        <= float(config["final_test"]["go8_generalization_nrmse_ratio_max"]),
        "main_validation_top3_beats_frozen_and_3_of_5_random": go6.get("pass") is True,
    }
    go8 = {
        "checks": go8_checks,
        "pass": all(go8_checks.values()),
        "generalization_nrmse_ratio_top3_over_frozen": gen_ratio,
        "valid_rate_drop_frozen_minus_top3": float(main_frozen_vector[2]) - float(main_top_vector[2]),
        "family_holdout_label": str(config["family_holdout"]["label"]),
        "family_holdout_is_subset_not_independent_evidence": True,
    }
    write_json(out / "go8.json", go8)
    final_result = {
        "status": "complete", "conditions": list(FINAL_CONDITIONS), "expected_counts": expected,
        "summaries": summaries, "odebench_forgetting_secondary": forgetting,
        "family_holdout_label": str(config["family_holdout"]["label"]),
        "family_holdout_is_main_test_subset_not_independent_evidence": True,
        "test_open_event_id": str(ledger["event_id"]), "test_open_count": 1,
        "candidate_selection_used_input_and_selection_only": True,
        "generalization_evaluated_only_after_candidate_selection": True,
        "go8": go8,
        "test_accessed": True,
    }
    write_json(out / "final_result.json", final_result)
    final_artifacts = {
        name: sha256_file(out / name)
        for name in (
            "test_set_audit.json", "final_test_protocol.json", "final_cell_artifact_index.json",
            "final_test_summary.json", "odebench_forgetting_index.json",
            "odebench_forgetting_summary.json", "final_result.json",
            "go8.json",
        )
    }
    complete_test_open(out / "test_open_ledger.json", final_artifact_sha256=final_artifacts)
    final_artifacts["test_open_ledger.json"] = sha256_file(out / "test_open_ledger.json")
    go_conditions = {
        "go6_and_go7_were_frozen_before_test_open": True,
        "single_test_open_event": True,
        "main_and_family_holdout_opened_in_one_protocol": True,
        "exact_final_five_conditions": list(freeze["conditions"]) == list(FINAL_CONDITIONS),
        "all_6000_grn_cells_complete": len(final_paths) == 6000,
        "all_candidates_formulas_failures_and_selected_generalization_saved": True,
        "odebench_forgetting_secondary_complete": all(value["cells"] == 756 for value in forgetting.values()),
    }
    write_manifest(
        out, 8, "complete" if all(go_conditions.values()) else "incomplete",
        substage="final-test", go_conditions=go_conditions, git=git_info(),
        started_utc=started_utc, finished_utc=utc_now(), wall_time_sec=perf_counter() - started,
        device=device, environment=software_versions(), test_accessed=True,
        test_open_event_id=str(ledger["event_id"]), test_open_count=1,
        final_condition_freeze_sha256=sha256_file(out / "final_condition_freeze.json"),
        sealed_artifact_sha256=sealed_hashes, artifact_sha256=final_artifacts,
    )
    print("GPU_RUN5 Phase 8 final test complete: GRN cells=6000", flush=True)
    return 0 if all(go_conditions.values()) else 1


def main() -> int:
    args = parse_args()
    return _validation_stage(args) if args.stage == "validation" else _final_test_stage(args)


if __name__ == "__main__":
    raise SystemExit(main())
