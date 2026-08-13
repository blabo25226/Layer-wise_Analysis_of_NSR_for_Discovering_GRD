"""GPU_RUN2 Phase 5: selective FT, symbolic recovery, and CTC_NSR reproduction bias."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "third_party" / "nesymres"))

from evaluation.aggregation import aggregate_prediction_scores  # noqa: E402
from evaluation.reproduction_bias import aggregate_reproduction, corpus_fingerprint  # noqa: E402
from resumable_evaluation import (  # noqa: E402
    load_problem_json_checkpoint,
    remaining_eq_ids,
    save_problem_json_checkpoint,
)
from gpu_run2_experiment import (  # noqa: E402
    build_finetune_loader,
    decode_gnw_row,
    dummy_gnw_record,
    filter_index_rows,
    finetune_hparams,
    iter_seed_noise,
    load_nesymres_gpu_run2,
    load_phase1_index,
    require_nesymres_checkpoint,
    select_hparams_on_validation,
    train_layers,
)
from gpu_run2_runtime import (  # noqa: E402
    decode_timeout_sec,
    load_gpu_run2_configs,
    resolve_run_dir,
    utc_now,
    write_json,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="GPU_RUN2 Phase 5 selective FT")
    parser.add_argument("--run-id", default=os.environ.get("LANSR_RUN_ID"))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--split", default="validation", choices=["validation", "test"])
    parser.add_argument(
        "--view",
        default="main",
        choices=["main", "structure_holdout"],
    )
    return parser.parse_args()


def _load_conditions(phase4: Path, view: str) -> dict:
    if view == "structure_holdout":
        holdout = phase4 / "conditions_structure_holdout.json"
        if holdout.is_file():
            return json.loads(holdout.read_text(encoding="utf-8"))
    path = phase4 / "conditions.json"
    if not path.is_file():
        raise FileNotFoundError(f"Phase 4 conditions missing: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _problem_key(row: dict) -> str:
    return f"{row['eq_id']}::noise{row['noise']}::seed{row['data_seed']}"


def _true_vs_pred_row(record: dict) -> dict:
    return {
        "eq_id": record["eq_id"],
        "condition": record["condition"],
        "noise": record["noise"],
        "data_seed": record.get("data_seed"),
        "training_seed": record.get("training_seed"),
        "structure_regime": record["structure_regime"],
        "true_expr": record["true_canonical"],
        "pred_expr": record["pred_simplified"] or record["pred_raw"],
        "exact": record["exact"],
        "skeleton": record["skeleton"],
        "symbolic_equivalent": record["symbolic_equivalent"],
        "domain_id_nmse": record["domain_id_nmse"],
        "domain_ood_nmse": record["domain_ood_nmse"],
        "valid_or_failure": "valid" if record["valid_pred"] else record["failure_reason"],
    }


def main() -> int:
    args = parse_args()
    config = load_gpu_run2_configs()
    run_dir = resolve_run_dir(args.run_id, config=config)
    phase1 = run_dir / "phase1"
    phase4 = run_dir / "phase4"
    out_dir = run_dir / "phase5"
    out_dir.mkdir(parents=True, exist_ok=True)
    timeout_sec = decode_timeout_sec(config)
    catalogue = json.loads((phase1 / "catalogue.json").read_text(encoding="utf-8"))
    splits = json.loads((phase1 / "splits.json").read_text(encoding="utf-8"))
    conditions_payload = _load_conditions(phase4, args.view)
    conditions = dict(conditions_payload["conditions"])
    split_key = "main" if args.view == "main" else "structure_holdout"
    selected_ids = list(splits[split_key][args.split])
    if args.smoke:
        selected_ids = selected_ids[:4]
    selected_specs = [row for row in catalogue if row["eq_id"] in set(selected_ids)]
    train_ids = splits[split_key]["train"]
    val_ids = splits[split_key]["validation"]
    train_templates = [
        row["canonical_expr"] for row in catalogue if row["eq_id"] in set(train_ids)
    ]
    corpus = corpus_fingerprint(train_templates)
    write_json(out_dir / f"corpus_{args.view}.json", corpus)

    all_records: list[dict] = []
    by_condition: dict[str, list[dict]] = {}
    hp_choices: dict[str, dict] = {}
    live = not bool(args.dry_run)

    if args.dry_run:
        for condition in conditions:
            records = [
                dummy_gnw_record(
                    row,
                    condition=condition,
                    timeout_sec=timeout_sec,
                    split_view=args.view,
                    decoder=f"nesymres_{condition}",
                )
                for row in selected_specs
            ]
            by_condition[condition] = records
            all_records.extend(records)
            write_json(out_dir / f"{args.view}_{args.split}_{condition}_records.json", records)
            write_json(
                out_dir / f"{args.view}_{args.split}_{condition}_aggregate.json",
                aggregate_prediction_scores(records),
            )
    else:
        if args.split == "test":
            # Layer sets and HP must already be frozen from validation.
            hp_path = out_dir / f"hp_selected_{args.view}.json"
            if hp_path.is_file():
                hp_choices = json.loads(hp_path.read_text(encoding="utf-8"))
        require_nesymres_checkpoint(config)
        index = load_phase1_index(phase1)
        hp = finetune_hparams(config)
        for condition, layer_names in conditions.items():
            condition_records: list[dict] = []
            for data_seed, model_seed, noise in iter_seed_noise(config, smoke=args.smoke):
                train_rows = filter_index_rows(
                    index,
                    split="train",
                    split_view=args.view,
                    data_seed=data_seed,
                    noise=noise,
                    eq_ids=train_ids,
                )
                val_rows = filter_index_rows(
                    index,
                    split="validation",
                    split_view=args.view,
                    data_seed=data_seed,
                    noise=noise,
                    eq_ids=val_ids,
                )
                eval_rows = filter_index_rows(
                    index,
                    split=args.split,
                    split_view=args.view,
                    data_seed=data_seed,
                    noise=noise,
                    eq_ids=selected_ids,
                )
                if args.smoke:
                    train_rows = train_rows[:8]
                    val_rows = val_rows[:4]
                    eval_rows = eval_rows[: min(2, len(eval_rows))]
                if not eval_rows:
                    continue
                eval_keys = [_problem_key(row) for row in eval_rows]
                ckpt_path = (
                    out_dir
                    / f"checkpoint_{args.view}_{args.split}_{condition}_seed{data_seed}_noise{noise:g}.json"
                )
                identity = {
                    "phase": 5,
                    "view": args.view,
                    "split": args.split,
                    "condition": condition,
                    "data_seed": int(data_seed),
                    "noise": float(noise),
                    "timeout_sec": float(timeout_sec),
                }
                payload = load_problem_json_checkpoint(ckpt_path, expected_identity=identity)
                completed = list(payload["completed_eq_ids"]) if payload else []
                stored = list(payload["records"]) if payload else []
                remaining = remaining_eq_ids(eval_keys, completed)
                if not remaining:
                    condition_records.extend(stored)
                    continue
                pretrained, params = load_nesymres_gpu_run2(config)
                if condition == "frozen" or layer_names == []:
                    model, params_fit = pretrained, params
                    metrics = {"trainable": 0, "epochs": 0, "best_val_ce": float("nan")}
                else:
                    train_loader = build_finetune_loader(
                        phase1,
                        train_rows,
                        params.word2id,
                        max_points=hp["max_points"],
                        batch_size=hp["batch_size"],
                        seed=model_seed,
                        shuffle=True,
                    )
                    val_loader = build_finetune_loader(
                        phase1,
                        val_rows,
                        params.word2id,
                        max_points=hp["max_points"],
                        batch_size=hp["batch_size"],
                        seed=model_seed,
                        shuffle=False,
                    )
                    hp_key = f"{condition}::seed{data_seed}::noise{noise:g}"
                    if args.split == "validation" and hp_key not in hp_choices:
                        hp_choices[hp_key] = select_hparams_on_validation(
                            config,
                            layer_names=layer_names,
                            train_loader=train_loader,
                            val_loader=val_loader,
                            seed=model_seed,
                        )
                    chosen = hp_choices.get(hp_key, {"lr": hp["lr"], "epochs": hp["epochs"]})
                    trial_config = dict(config)
                    trial_ft = dict(config.get("finetune") or {})
                    trial_ft["lr"] = float(chosen["lr"])
                    trial_ft["epochs"] = int(chosen["epochs"])
                    trial_config["finetune"] = trial_ft
                    model, params_fit, metrics = train_layers(
                        trial_config,
                        layer_names=layer_names,
                        train_loader=train_loader,
                        val_loader=val_loader,
                        seed=model_seed,
                    )
                    del pretrained
                by_eval_key = {_problem_key(row): row for row in eval_rows}
                for key in remaining:
                    row = by_eval_key[key]
                    record = decode_gnw_row(
                        model,
                        params_fit,
                        phase1,
                        row,
                        condition=condition,
                        timeout_sec=timeout_sec,
                        split_view=args.view,
                        training_seed=model_seed,
                        decoder=f"nesymres_{condition}",
                        operator_config=config.get("operators"),
                    )
                    record["ft_metrics"] = {
                        metric_key: metrics[metric_key]
                        for metric_key in ("trainable", "epochs", "best_val_ce", "best_epoch", "stopped_epoch")
                        if metric_key in metrics
                    }
                    stored.append(record)
                    completed.append(key)
                    save_problem_json_checkpoint(
                        ckpt_path,
                        identity=identity,
                        completed_eq_ids=completed,
                        records=stored,
                    )
                condition_records.extend(stored)
                del model
            by_condition[condition] = condition_records
            all_records.extend(condition_records)
            write_json(
                out_dir / f"{args.view}_{args.split}_{condition}_records.json",
                condition_records,
            )
            write_json(
                out_dir / f"{args.view}_{args.split}_{condition}_aggregate.json",
                aggregate_prediction_scores(condition_records),
            )
        if args.split == "validation" and hp_choices:
            write_json(out_dir / f"hp_selected_{args.view}.json", hp_choices)

    reproduction = {}
    for condition, records in by_condition.items():
        reproduction[condition] = {
            key: value
            for key, value in aggregate_reproduction(
                records, train_templates=train_templates
            ).items()
            if key != "rows"
        }
    write_json(out_dir / f"reproduction_{args.view}_{args.split}.json", reproduction)
    write_json(
        out_dir / f"true_vs_pred_{args.view}_{args.split}.json",
        [_true_vs_pred_row(row) for row in all_records],
    )
    write_json(
        out_dir / "manifest.json",
        {
            "phase": 5,
            "status": "complete",
            "at_utc": utc_now(),
            "view": args.view,
            "split": args.split,
            "conditions": list(conditions),
            "conditions_source": (
                "conditions_structure_holdout.json"
                if args.view == "structure_holdout" and (phase4 / "conditions_structure_holdout.json").is_file()
                else "conditions.json"
            ),
            "n_problems": len(selected_specs),
            "timeout_sec": timeout_sec,
            "dry_run": bool(args.dry_run),
            "smoke": bool(args.smoke),
            "live_model": live,
            "placeholder_decode": bool(args.dry_run),
            "used_test_for_selection": False,
        },
    )
    print(f"Phase 5 complete: view={args.view} split={args.split}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
