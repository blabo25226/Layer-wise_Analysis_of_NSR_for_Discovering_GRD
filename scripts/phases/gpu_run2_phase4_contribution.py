"""GPU_RUN2 Phase 4: IOLE, ablation, and activation intervention on a fixed panel."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "third_party" / "nesymres"))

from evaluation.gpu_run2_rankings import (  # noqa: E402
    ablation_ranking,
    intervention_ranking,
    iole_ranking,
    phase4_agreement,
    phase4_conditions,
)
from evaluation.layer_contribution import absolute_improvements, ranking_stability  # noqa: E402
from gpu_run2_experiment import (  # noqa: E402
    build_finetune_loader,
    decode_gnw_row,
    eval_teacher_forcing_ce,
    filter_index_rows,
    finetune_hparams,
    iter_seed_noise,
    load_nesymres_gpu_run2,
    load_phase1_index,
    mean_penalized_nmse,
    require_nesymres_checkpoint,
    resolve_layer_module,
    train_layers,
)
from gpu_run2_runtime import git_info, load_gpu_run2_configs, resolve_run_dir, utc_now, write_json  # noqa: E402
from interpretability.interventions import (  # noqa: E402
    capture_module_activation,
    replace_output_context,
    zero_output_context,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="GPU_RUN2 Phase 4 contribution")
    parser.add_argument("--run-id", default=os.environ.get("LANSR_RUN_ID"))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--smoke", action="store_true")
    return parser.parse_args()


def _mean_or_nan(values: list[float]) -> float:
    finite = [float(v) for v in values if np.isfinite(float(v))]
    return float(np.mean(finite)) if finite else float("nan")


def _last_snapshot(tables: dict[str, list[float]]) -> dict[str, float]:
    return {name: float(values[-1]) for name, values in tables.items() if values}


def _decode_panel(model, params, phase1, rows, *, condition, timeout_sec, training_seed, config):
    records = [
        decode_gnw_row(
            model,
            params,
            phase1,
            row,
            condition=condition,
            timeout_sec=timeout_sec,
            split_view="main",
            training_seed=training_seed,
            decoder=f"nesymres_{condition}",
            operator_config=config.get("operators"),
        )
        for row in rows
    ]
    return records, mean_penalized_nmse(records)


def _unit_identity(
    *,
    data_seed: int,
    model_seed: int,
    noise: float,
    analysis: str,
    condition: str,
    panel_ids: list[str],
    timeout_sec: float,
) -> dict:
    return {
        "phase": 4,
        "data_seed": int(data_seed),
        "model_seed": int(model_seed),
        "noise": float(noise),
        "analysis": str(analysis),
        "condition": str(condition),
        "panel_ids": list(panel_ids),
        "timeout_sec": float(timeout_sec),
        "source_commit": git_info().get("commit"),
    }


def _unit_path(out_dir: Path, identity: dict) -> Path:
    noise = str(identity["noise"]).replace(".", "p")
    name = f"{identity['analysis']}_{identity['condition']}.json"
    return out_dir / "checkpoints" / f"seed{identity['data_seed']}_noise{noise}" / name


def _load_unit(path: Path, identity: dict) -> dict | None:
    if not path.is_file():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("identity") != identity:
        raise RuntimeError(
            f"Phase 4 checkpoint identity mismatch: {path}\n"
            f"checkpoint={payload.get('identity')}\nexpected={identity}"
        )
    return payload


def _save_unit(path: Path, identity: dict, **results) -> dict:
    payload = {"identity": identity, "results": results, "status": "complete"}
    write_json(path, payload)
    return payload


def main() -> int:
    args = parse_args()
    config = load_gpu_run2_configs()
    run_dir = resolve_run_dir(args.run_id, config=config)
    phase1 = run_dir / "phase1"
    phase3 = run_dir / "phase3"
    out_dir = run_dir / "phase4"
    out_dir.mkdir(parents=True, exist_ok=True)
    splits = json.loads((phase1 / "splits.json").read_text(encoding="utf-8"))
    main_cand_path = phase3 / "candidate_layers_main.json"
    if not main_cand_path.is_file():
        main_cand_path = phase3 / "candidate_layers.json"
    if not main_cand_path.is_file():
        raise FileNotFoundError(
            f"Phase 3 candidates missing: tried candidate_layers_main.json and candidate_layers.json under {phase3}"
        )
    candidates_main = list(
        json.loads(main_cand_path.read_text(encoding="utf-8"))["candidates"]
    )
    structure_cand_path = phase3 / "candidate_layers_structure_holdout.json"
    if not structure_cand_path.is_file():
        raise FileNotFoundError(
            f"Phase 3 structure-holdout candidates missing (fail-fast): {structure_cand_path}"
        )
    candidates_sh = list(
        json.loads(structure_cand_path.read_text(encoding="utf-8"))["candidates"]
    )
    candidates_union = sorted(set(candidates_main) | set(candidates_sh))
    candidate_sources = {
        "main": main_cand_path.name,
        "structure_holdout": structure_cand_path.name,
    }
    panel_ids = list(splits["phase4_panel"])
    if args.smoke:
        panel_ids = panel_ids[:4]
    structure_ood_families = set(
        config.get("splits", {}).get("phase4_panel", {}).get("structure_ood_families")
        or ["G01", "G02", "G03", "G04", "G05", "G06"]
    )
    catalogue = json.loads((phase1 / "catalogue.json").read_text(encoding="utf-8"))
    by_id = {row["eq_id"]: row for row in catalogue}
    panel_main = [by_id[eq_id] for eq_id in panel_ids if eq_id in by_id]
    panel_structure = [row for row in panel_main if row["family_id"] in structure_ood_families]
    timeout_sec = float(config.get("decode_timeout_sec", 30))
    hp = finetune_hparams(config)
    probe_payload = {}
    probe_scores_path = phase3 / "probe_scores.json"
    if probe_scores_path.is_file():
        probe_payload = json.loads(probe_scores_path.read_text(encoding="utf-8"))
    probe_main = probe_payload.get("main") if isinstance(probe_payload.get("main"), dict) else {}
    probe_ranking = list(
        probe_main.get("probe_ranking")
        or probe_payload.get("probe_ranking")
        or candidates_main
    )
    decoder_lens_ranking = list(probe_payload.get("decoder_lens_ranking") or [])
    seed_snapshots: list[dict[str, dict[str, float]]] = []
    layer_scores_sh: dict[str, float] = {}
    phase4_records: list[dict] = []

    if args.dry_run:
        rng = np.random.default_rng(4)
        base = 0.40
        full = 0.22
        layer_scores = {"pretrained": base, "all_params": full}
        ablation_scores = {"pretrained": base, "all_params": full}
        intervention_scores = {"pretrained": base, "all_params": full}
        ce_scores = {"pretrained": 2.0, "all_params": 1.4}
        for layer in candidates_union:
            layer_scores[layer] = float(full + rng.uniform(-0.03, 0.08))
            ablation_scores[layer] = float(base - rng.uniform(0.0, 0.1))
            intervention_scores[layer] = float(base - rng.uniform(0.0, 0.08))
            ce_scores[layer] = float(1.4 + rng.uniform(-0.05, 0.2))
        layer_scores_sh = {
            name: float(value + rng.uniform(-0.02, 0.02)) for name, value in layer_scores.items()
        }
        for seed_idx in range(3):
            seed_snapshots.append(
                {
                    "iole": {
                        name: float(value + rng.uniform(-0.01, 0.01))
                        for name, value in layer_scores.items()
                        if name not in {"pretrained", "all_params"}
                    },
                    "ablation": {
                        name: float(ablation_scores[name] + rng.uniform(-0.01, 0.01))
                        for name in candidates_union
                    },
                    "intervention": {
                        name: float(intervention_scores[name] + rng.uniform(-0.01, 0.01))
                        for name in candidates_union
                    },
                }
            )
            seed_snapshots[-1]["iole"]["seed_index"] = float(seed_idx)
        live = False
    else:
        require_nesymres_checkpoint(config)
        index = load_phase1_index(phase1)
        iole_nmse: dict[str, list[float]] = {"pretrained": [], "all_params": []}
        iole_ce: dict[str, list[float]] = {"pretrained": [], "all_params": []}
        ablation_nmse: dict[str, list[float]] = {"pretrained": [], "all_params": []}
        intervention_nmse: dict[str, list[float]] = {"pretrained": [], "all_params": []}
        iole_nmse_sh: dict[str, list[float]] = {"pretrained": [], "all_params": []}
        for name in candidates_union:
            iole_nmse.setdefault(name, [])
            iole_ce.setdefault(name, [])
            ablation_nmse.setdefault(name, [])
            intervention_nmse.setdefault(name, [])
            iole_nmse_sh.setdefault(name, [])
        alpha = float(config.get("intervention_alpha", 1.0))
        for data_seed, model_seed, noise in iter_seed_noise(config, smoke=args.smoke):
            train_rows = filter_index_rows(
                index, split="train", split_view="main", data_seed=data_seed, noise=noise
            )
            panel_rows = filter_index_rows(
                index,
                split_view="main",
                data_seed=data_seed,
                noise=noise,
                eq_ids=panel_ids,
            )
            if args.smoke:
                train_rows = train_rows[:8]
                panel_rows = panel_rows[: min(2, len(panel_rows))]
            if not train_rows or not panel_rows:
                continue
            pretrained, params = load_nesymres_gpu_run2(config)
            train_loader = build_finetune_loader(
                phase1,
                train_rows,
                params.word2id,
                max_points=hp["max_points"],
                batch_size=hp["batch_size"],
                seed=model_seed,
                shuffle=True,
                max_token_len=int(pretrained.cfg.length_eq),
            )
            panel_loader = build_finetune_loader(
                phase1,
                panel_rows,
                params.word2id,
                max_points=hp["max_points"],
                batch_size=hp["batch_size"],
                seed=model_seed,
                shuffle=False,
                max_token_len=int(pretrained.cfg.length_eq),
            )
            bundle_panel_ids = [str(row["eq_id"]) for row in panel_rows]
            identity = _unit_identity(
                data_seed=data_seed,
                model_seed=model_seed,
                noise=noise,
                analysis="iole",
                condition="pretrained",
                panel_ids=bundle_panel_ids,
                timeout_sec=timeout_sec,
            )
            unit_path = _unit_path(out_dir, identity)
            unit = _load_unit(unit_path, identity)
            if unit is None:
                pre_ce = eval_teacher_forcing_ce(pretrained, panel_loader)
                _pre_records, pre_nmse = _decode_panel(
                    pretrained,
                    params,
                    phase1,
                    panel_rows,
                    condition="pretrained",
                    timeout_sec=timeout_sec,
                    training_seed=model_seed,
                    config=config,
                )
                unit = _save_unit(
                    unit_path,
                    identity,
                    ce=pre_ce,
                    nmse=pre_nmse,
                    nmse_structure_holdout=mean_penalized_nmse(
                        _pre_records, families=structure_ood_families
                    ),
                    records=_pre_records,
                )
            results = unit["results"]
            pre_ce = float(results["ce"])
            pre_nmse = float(results["nmse"])
            _pre_records = list(results["records"])
            iole_ce["pretrained"].append(pre_ce)
            iole_nmse["pretrained"].append(pre_nmse)
            iole_nmse_sh["pretrained"].append(float(results["nmse_structure_holdout"]))
            ablation_nmse["pretrained"].append(pre_nmse)
            intervention_nmse["pretrained"].append(pre_nmse)
            phase4_records.extend(_pre_records)

            identity = _unit_identity(
                data_seed=data_seed,
                model_seed=model_seed,
                noise=noise,
                analysis="iole",
                condition="all_params",
                panel_ids=bundle_panel_ids,
                timeout_sec=timeout_sec,
            )
            unit_path = _unit_path(out_dir, identity)
            unit = _load_unit(unit_path, identity)
            if unit is None:
                full_model, full_params, _metrics = train_layers(
                    config,
                    layer_names=None,
                    train_loader=train_loader,
                    val_loader=panel_loader,
                    seed=model_seed,
                )
                full_ce = eval_teacher_forcing_ce(full_model, panel_loader)
                _full_records, full_nmse = _decode_panel(
                    full_model,
                    full_params,
                    phase1,
                    panel_rows,
                    condition="all_params",
                    timeout_sec=timeout_sec,
                    training_seed=model_seed,
                    config=config,
                )
                unit = _save_unit(
                    unit_path,
                    identity,
                    ce=full_ce,
                    nmse=full_nmse,
                    nmse_structure_holdout=mean_penalized_nmse(
                        _full_records, families=structure_ood_families
                    ),
                    records=_full_records,
                )
                del full_model
            results = unit["results"]
            full_ce = float(results["ce"])
            full_nmse = float(results["nmse"])
            _full_records = list(results["records"])
            iole_ce["all_params"].append(full_ce)
            iole_nmse["all_params"].append(full_nmse)
            iole_nmse_sh["all_params"].append(float(results["nmse_structure_holdout"]))
            ablation_nmse["all_params"].append(full_nmse)
            intervention_nmse["all_params"].append(full_nmse)
            phase4_records.extend(_full_records)

            ref_batch = next(iter(train_loader))
            for layer in candidates_union:
                identity = _unit_identity(
                    data_seed=data_seed,
                    model_seed=model_seed,
                    noise=noise,
                    analysis="iole",
                    condition=layer,
                    panel_ids=bundle_panel_ids,
                    timeout_sec=timeout_sec,
                )
                unit_path = _unit_path(out_dir, identity)
                unit = _load_unit(unit_path, identity)
                if unit is None:
                    iole_model, iole_params, _iole_metrics = train_layers(
                        config,
                        layer_names=[layer],
                        train_loader=train_loader,
                        val_loader=panel_loader,
                        seed=model_seed,
                    )
                    layer_ce = eval_teacher_forcing_ce(iole_model, panel_loader)
                    _iole_records, layer_nmse = _decode_panel(
                        iole_model,
                        iole_params,
                        phase1,
                        panel_rows,
                        condition=layer,
                        timeout_sec=timeout_sec,
                        training_seed=model_seed,
                        config=config,
                    )
                    unit = _save_unit(
                        unit_path,
                        identity,
                        ce=layer_ce,
                        nmse=layer_nmse,
                        nmse_structure_holdout=mean_penalized_nmse(
                            _iole_records, families=structure_ood_families
                        ),
                        records=_iole_records,
                    )
                    del iole_model
                results = unit["results"]
                layer_nmse = float(results["nmse"])
                _iole_records = list(results["records"])
                iole_ce[layer].append(float(results["ce"]))
                iole_nmse[layer].append(layer_nmse)
                iole_nmse_sh[layer].append(float(results["nmse_structure_holdout"]))
                phase4_records.extend(_iole_records)

                module = resolve_layer_module(pretrained, layer)
                identity = _unit_identity(
                    data_seed=data_seed,
                    model_seed=model_seed,
                    noise=noise,
                    analysis="ablation",
                    condition=layer,
                    panel_ids=bundle_panel_ids,
                    timeout_sec=timeout_sec,
                )
                unit_path = _unit_path(out_dir, identity)
                unit = _load_unit(unit_path, identity)
                if unit is None:
                    with zero_output_context(module):
                        _abl_records, abl_nmse = _decode_panel(
                            pretrained,
                            params,
                            phase1,
                            panel_rows,
                            condition=f"ablation_{layer}",
                            timeout_sec=timeout_sec,
                            training_seed=model_seed,
                            config=config,
                        )
                    unit = _save_unit(
                        unit_path,
                        identity,
                        nmse=abl_nmse,
                        records=_abl_records,
                    )
                results = unit["results"]
                abl_nmse = float(results["nmse"])
                _abl_records = list(results["records"])
                ablation_nmse[layer].append(abl_nmse)
                phase4_records.extend(_abl_records)

                identity = _unit_identity(
                    data_seed=data_seed,
                    model_seed=model_seed,
                    noise=noise,
                    analysis="intervention",
                    condition=layer,
                    panel_ids=bundle_panel_ids,
                    timeout_sec=timeout_sec,
                )
                unit_path = _unit_path(out_dir, identity)
                unit = _load_unit(unit_path, identity)
                if unit is None:
                    captured = capture_module_activation(pretrained, module, ref_batch)
                    reduce_dims = tuple(range(captured.ndim - 1)) if captured.ndim > 1 else (0,)
                    mean_act = captured.mean(dim=reduce_dims, keepdim=True)
                    if abs(alpha - 1.0) > 1e-12:
                        src = captured[:1]
                        seq_dims = tuple(range(1, src.ndim - 1))
                        if seq_dims:
                            src = src.mean(dim=seq_dims, keepdim=True)
                        mean_act = (1.0 - alpha) * src + alpha * mean_act
                    with replace_output_context(module, mean_act):
                        _int_records, int_nmse = _decode_panel(
                            pretrained,
                            params,
                            phase1,
                            panel_rows,
                            condition=f"intervention_{layer}",
                            timeout_sec=timeout_sec,
                            training_seed=model_seed,
                            config=config,
                        )
                    unit = _save_unit(
                        unit_path,
                        identity,
                        nmse=int_nmse,
                        records=_int_records,
                    )
                results = unit["results"]
                int_nmse = float(results["nmse"])
                _int_records = list(results["records"])
                intervention_nmse[layer].append(int_nmse)
                phase4_records.extend(_int_records)
            seed_snapshots.append(
                {
                    "data_seed": float(data_seed),
                    "noise": float(noise),
                    "iole": _last_snapshot(iole_nmse),
                    "ablation": _last_snapshot(ablation_nmse),
                    "intervention": _last_snapshot(intervention_nmse),
                }
            )
            del pretrained
        layer_scores = {name: _mean_or_nan(vals) for name, vals in iole_nmse.items()}
        ce_scores = {name: _mean_or_nan(vals) for name, vals in iole_ce.items()}
        ablation_scores = {name: _mean_or_nan(vals) for name, vals in ablation_nmse.items()}
        intervention_scores = {name: _mean_or_nan(vals) for name, vals in intervention_nmse.items()}
        layer_scores_sh = {name: _mean_or_nan(vals) for name, vals in iole_nmse_sh.items()}
        live = True

    iole_rank, contrib = iole_ranking(layer_scores, candidates_main)
    absolute = absolute_improvements(layer_scores, higher_is_better=False)
    ablation_rank = ablation_ranking(ablation_scores, candidates_main)
    intervention_rank = intervention_ranking(intervention_scores, candidates_main)
    conditions = phase4_conditions(
        iole_rank,
        random_seed=int(config["random_3_seed"]),
        candidate_layers=candidates_main,
    )
    iole_rank_sh, contrib_sh = iole_ranking(layer_scores_sh or layer_scores, candidates_sh)
    conditions_sh = phase4_conditions(
        iole_rank_sh,
        random_seed=int(config["random_3_seed"]),
        candidate_layers=candidates_sh,
    )
    stability_rows = [
        {
            "iole": {k: v for k, v in snap["iole"].items() if k not in {"pretrained", "all_params", "seed_index", "data_seed", "noise"}},
            "ablation": {k: v for k, v in snap["ablation"].items() if k not in {"pretrained", "all_params"}},
            "intervention": {k: v for k, v in snap["intervention"].items() if k not in {"pretrained", "all_params"}},
        }
        for snap in seed_snapshots
        if "iole" in snap
    ]
    write_json(out_dir / "raw_scores.json", layer_scores)
    write_json(out_dir / "val_ce.json", ce_scores)
    write_json(out_dir / "ablation_scores.json", ablation_scores)
    write_json(out_dir / "intervention_scores.json", intervention_scores)
    write_json(out_dir / "absolute_improvements.json", absolute)
    write_json(out_dir / "contributions.json", contrib)
    write_json(
        out_dir / "rankings.json",
        {
            "iole": iole_rank,
            "ablation": ablation_rank,
            "intervention": intervention_rank,
            "probe": probe_ranking,
            "decoder_lens": decoder_lens_ranking,
            "agreement": phase4_agreement(
                iole=iole_rank,
                ablation=ablation_rank,
                intervention=intervention_rank,
                probe=probe_ranking,
                decoder_lens=decoder_lens_ranking,
            ),
            "seed_stability": ranking_stability(
                stability_rows,
                {"iole": "iole", "ablation": "ablation", "intervention": "intervention"},
            )
            if len(stability_rows) >= 2
            else {"note": "need at least two seed snapshots"},
        },
    )
    write_json(out_dir / "seed_snapshots.json", seed_snapshots)
    write_json(out_dir / "equation_records.json", phase4_records)
    write_json(
        out_dir / "conditions.json",
        {
            "conditions": conditions,
            "random_3_seed": int(config["random_3_seed"]),
            "candidate_layers": list(candidates_main),
            "candidate_source": candidate_sources["main"],
            "source_panel": "main_all_families",
            "note": (
                "random_3 is one fixed control set. Do not claim average random-set performance. "
                f"Layer candidates loaded from Phase 3 {candidate_sources['main']}."
            ),
        },
    )
    write_json(out_dir / "panel_main.json", [row["eq_id"] for row in panel_main])
    write_json(
        out_dir / "panel_structure_ood.json",
        [row["eq_id"] for row in panel_structure],
    )
    write_json(out_dir / "raw_scores_structure_holdout.json", layer_scores_sh)
    write_json(out_dir / "contributions_structure_holdout.json", contrib_sh)
    write_json(
        out_dir / "conditions_structure_holdout.json",
        {
            "conditions": conditions_sh,
            "random_3_seed": int(config["random_3_seed"]),
            "candidate_layers": list(candidates_sh),
            "candidate_source": candidate_sources["structure_holdout"],
            "source_panel": "g01_g06_only",
            "selection_families": sorted(structure_ood_families),
            "excluded_families": ["G07", "G08"],
            "iole_ranking": iole_rank_sh,
            "panel_eq_ids": [
                row["eq_id"] for row in panel_main if row["family_id"] in structure_ood_families
            ],
            "note": (
                "Structure-OOD layer freeze uses G01–G06 panel scores only. "
                "G07–G08 panel rows are stored but not used for selection. "
                f"Candidates from Phase 3 {candidate_sources['structure_holdout']} "
                "(G07/G08 excluded at probe selection)."
            ),
        },
    )
    write_json(
        out_dir / "manifest.json",
        {
            "phase": 4,
            "status": "complete",
            "at_utc": utc_now(),
            "n_panel_main": len(panel_main),
            "n_panel_structure_ood": len(panel_structure),
            "n_seed_snapshots": len(seed_snapshots),
            "used_test_problems": False,
            "placeholder_scores": bool(args.dry_run),
            "live_model": live,
            "dry_run": bool(args.dry_run),
            "smoke": bool(args.smoke),
            "candidate_sources": candidate_sources,
            "candidates_main": list(candidates_main),
            "candidates_structure_holdout": list(candidates_sh),
            "candidates_union": list(candidates_union),
        },
    )
    print(f"Phase 4 complete: conditions={list(conditions)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
