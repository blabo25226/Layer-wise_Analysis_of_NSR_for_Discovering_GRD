"""Live GPU_RUN2 helpers for NeSymReS probe, IOLE, ablation, and selective FT.

Phase scripts import this module. Nothing here starts a Phase on import.
``--dry-run`` must keep dummy outputs; missing checkpoints fail fast on live runs.
"""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import numpy as np

from data.gnw_synthetic import sampled_dataset_from_npz, structure_regime_for
from evaluation.equation_metrics import eval_expression, score_domain_predictions
from evaluation.equation_records import make_gpu_run2_equation_record
from evaluation.operator_policy import validate_candidate_expression
from gpu_run2_runtime import nesymres_paths, seed_bundles


def reraise_oom(exc: BaseException) -> None:
    if isinstance(exc, RuntimeError) and "out of memory" in str(exc).lower():
        raise RuntimeError(
            "GPU OOM: fail fast. Do not silently reduce batch size or switch precision."
        ) from exc
    raise exc


def seed_everything(seed: int) -> None:
    import torch

    random.seed(int(seed))
    np.random.seed(int(seed))
    torch.manual_seed(int(seed))
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(int(seed))


def require_nesymres_checkpoint(config: Mapping[str, Any]) -> dict[str, Path]:
    paths = nesymres_paths(config)
    missing = [name for name, path in paths.items() if not path.is_file()]
    if missing:
        detail = ", ".join(f"{name}={paths[name]}" for name in missing)
        raise FileNotFoundError(f"NeSymReS asset missing for live GPU_RUN2: {detail}")
    return paths


def load_nesymres_gpu_run2(config: Mapping[str, Any]):
    from models.nesymres_adapter import load_nesymres

    paths = require_nesymres_checkpoint(config)
    try:
        return load_nesymres(
            paths["weights"],
            paths["config"],
            paths["eq_setting"],
            beam_size=int(config.get("beam_size", 2)),
        )
    except RuntimeError as exc:
        reraise_oom(exc)
        raise


def load_phase1_index(phase1_dir: Path) -> list[dict[str, Any]]:
    path = Path(phase1_dir) / "index.json"
    if not path.is_file():
        raise FileNotFoundError(f"Phase 1 index missing: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError(f"Phase 1 index must be a list, got {type(payload).__name__}")
    return payload


def filter_index_rows(
    rows: Sequence[Mapping[str, Any]],
    *,
    split: str | None = None,
    split_view: str = "main",
    data_seed: int | None = None,
    noise: float | None = None,
    eq_ids: Iterable[str] | None = None,
) -> list[dict[str, Any]]:
    allowed = None if eq_ids is None else set(str(eq_id) for eq_id in eq_ids)
    split_field = "main_split" if split_view == "main" else "structure_split"
    out: list[dict[str, Any]] = []
    for row in rows:
        if allowed is not None and str(row["eq_id"]) not in allowed:
            continue
        if split is not None and str(row.get(split_field)) != str(split):
            continue
        if data_seed is not None and int(row["data_seed"]) != int(data_seed):
            continue
        if noise is not None and abs(float(row["noise"]) - float(noise)) > 1e-12:
            continue
        out.append(dict(row))
    return out


def row_to_sampled(phase1_dir: Path, row: Mapping[str, Any], *, xy: str = "train"):
    return sampled_dataset_from_npz(Path(phase1_dir) / "data" / row["file"], xy=xy)


def build_finetune_loader(
    phase1_dir: Path,
    rows: Sequence[Mapping[str, Any]],
    word2id: Mapping[str, int],
    *,
    max_points: int,
    batch_size: int,
    seed: int,
    shuffle: bool,
    max_token_len: int | None = None,
):
    from torch.utils.data import DataLoader

    from data.finetune_dataset import GRNFinetuneDataset, collate_finetune

    problems = [row_to_sampled(phase1_dir, row, xy="train") for row in rows]
    dataset = GRNFinetuneDataset(
        problems,
        dict(word2id),
        max_points=int(max_points),
        seed=int(seed),
        max_token_len=max_token_len,
    )
    if len(dataset) == 0:
        detail = []
        if getattr(dataset, "skipped_long", None):
            detail.append(f"too_long={dataset.skipped_long}")
        if getattr(dataset, "skipped_tokenize", None):
            detail.append(f"tokenize_fail={dataset.skipped_tokenize}")
        raise RuntimeError(
            "GRNFinetuneDataset is empty after tokenizing GNW expressions. "
            "Check operator allowlist / teacher formulas / length_eq. "
            + (" ".join(detail) if detail else "")
        )
    return DataLoader(
        dataset,
        batch_size=max(1, min(int(batch_size), len(dataset))),
        shuffle=bool(shuffle),
        collate_fn=collate_finetune,
    )


def try_build_finetune_loader(
    *args: Any,
    **kwargs: Any,
):
    """Like :func:`build_finetune_loader`, but return ``None`` when every formula is skipped."""
    try:
        return build_finetune_loader(*args, **kwargs)
    except RuntimeError as exc:
        if "GRNFinetuneDataset is empty" in str(exc):
            return None
        raise



def finetune_hparams(config: Mapping[str, Any]) -> dict[str, Any]:
    block = dict(config.get("finetune") or {})
    return {
        "lr": float(block.get("lr", 1e-4)),
        "epochs": int(block.get("epochs", 5)),
        "patience": int(block.get("patience", 2)),
        "min_delta": float(block.get("min_delta", 1e-4)),
        "max_points": int(block.get("max_points", 80)),
        "lr_grid": [float(x) for x in block.get("lr_grid", [block.get("lr", 1e-4)])],
        "epoch_grid": [int(x) for x in block.get("epoch_grid", [block.get("epochs", 5)])],
        "batch_size": int(config.get("train_batch_size", 16)),
    }


def eval_teacher_forcing_ce(model, loader, *, device=None) -> float:
    import torch

    device = device or getattr(model, "device", torch.device("cuda" if torch.cuda.is_available() else "cpu"))
    model = model.to(device)
    model.eval()
    losses: list[float] = []
    try:
        with torch.no_grad():
            for batch in loader:
                nums, tokens = batch[0].to(device), batch[1].to(device)
                output, trg = model.forward([nums, tokens])
                losses.append(float(model.compute_loss(output, trg).cpu()))
    except RuntimeError as exc:
        reraise_oom(exc)
    return float(sum(losses) / max(len(losses), 1)) if losses else float("nan")


def dummy_gnw_record(
    row: Mapping[str, Any],
    *,
    condition: str,
    timeout_sec: float,
    split_view: str = "main",
    training_seed: int = 0,
    decoder: str | None = None,
    failure_reason: str | None = None,
) -> dict[str, Any]:
    """Schema-complete placeholder used only with ``--dry-run``."""
    valid = failure_reason is None
    return make_gpu_run2_equation_record(
        eq_id=str(row["eq_id"]),
        predicted_expr="" if failure_reason else str(row.get("canonical_expr") or "x_1"),
        variable_names=list(row["oracle_inputs"]),
        scores={
            "valid_pred": 1.0 if valid else 0.0,
            "nmse": 0.0 if valid else float("inf"),
            "r2": 1.0 if valid else -1.0,
            "sym_exact": 0.0,
            "sym_skeleton": 0.0,
            "sym_equiv": 0.0,
            "complexity": 1.0,
            "var_f1": 1.0,
            "var_precision": 1.0,
            "var_recall": 1.0,
            "domain_id_nmse": 0.0 if valid else float("inf"),
            "domain_ood_nmse": 0.0 if valid else float("inf"),
        },
        true_expr=str(row.get("canonical_expr") or ""),
        true_raw=str(row.get("raw_gnw_formula") or ""),
        true_canonical=str(row.get("canonical_expr") or ""),
        true_skeleton=str(row.get("skeleton_expr") or ""),
        motif=str(row["family_id"]),
        split=str(row["main_split"] if split_view == "main" else row["structure_split"]),
        split_view=str(split_view),
        noise=float(row.get("noise", 0.0)),
        data_seed=int(row.get("data_seed", 101)),
        training_seed=int(training_seed),
        condition=str(condition),
        domain_regime="id",
        structure_regime=structure_regime_for(split_view, str(row["family_id"])),
        parameter_split="main" if split_view == "main" else "structure_holdout",
        target_variable=str(row["target_variable"]),
        oracle_regulators=list(row["oracle_regulators"]),
        oracle_inputs=list(row["oracle_inputs"]),
        variable_order=list(row["variable_order"]),
        oracle_source_equation_id=str(row["oracle_source_equation_id"]),
        decoder=decoder or str(condition),
        failure_reason=failure_reason,
        timeout_budget_sec=float(timeout_sec),
    )


def score_gnw_prediction(
    phase1_dir: Path,
    row: Mapping[str, Any],
    predicted_expr: str,
    *,
    condition: str,
    timeout_sec: float,
    split_view: str,
    training_seed: int,
    decoder: str,
    failure_reason: str | None = None,
    candidate_expressions: Sequence[str] | None = None,
    search_seconds: float = 0.0,
    n_candidate_evals: int = 0,
    timeout: bool = False,
) -> dict[str, Any]:
    npz = _load_npz(phase1_dir, row)
    names = list(row["oracle_inputs"])
    pred = str(predicted_expr or "")
    reason = failure_reason
    if pred:
        ok, op_reason = validate_candidate_expression(
            pred,
            point_sets={
                "train": (npz["X_train"], names),
                "id": (npz["X_id"], names),
                "ood": (npz["X_ood"], names),
            },
        )
        if not ok:
            reason = op_reason
            pred = ""
    pred_id = eval_expression(pred, npz["X_id"], names) if pred else None
    pred_ood = eval_expression(pred, npz["X_ood"], names) if pred else None
    scores = score_domain_predictions(
        y_id=npz["y_id"],
        pred_id=pred_id,
        y_ood=npz["y_ood"],
        pred_ood=pred_ood,
        predicted_expr=pred,
        true_vars=names,
        true_expr=str(row.get("canonical_expr") or ""),
        X_id=npz["X_id"],
        X_ood=npz["X_ood"],
        variable_names=names,
    )
    if reason:
        scores["valid_pred"] = 0.0
    return make_gpu_run2_equation_record(
        eq_id=str(row["eq_id"]),
        predicted_expr=pred,
        variable_names=names,
        scores=scores,
        true_expr=str(row.get("canonical_expr") or ""),
        true_raw=str(row.get("raw_gnw_formula") or ""),
        true_canonical=str(row.get("canonical_expr") or ""),
        true_skeleton=str(row.get("skeleton_expr") or ""),
        motif=str(row["family_id"]),
        split=str(row["main_split"] if split_view == "main" else row["structure_split"]),
        split_view=str(split_view),
        noise=float(row["noise"]),
        data_seed=int(row["data_seed"]),
        training_seed=int(training_seed),
        condition=str(condition),
        domain_regime="id",
        structure_regime=structure_regime_for(split_view, str(row["family_id"])),
        parameter_split="main" if split_view == "main" else "structure_holdout",
        target_variable=str(row["target_variable"]),
        oracle_regulators=list(row["oracle_regulators"]),
        oracle_inputs=names,
        variable_order=list(row["variable_order"]),
        oracle_source_equation_id=str(row["oracle_source_equation_id"]),
        decoder=str(decoder),
        failure_reason=reason,
        candidate_expressions=list(candidate_expressions or []),
        search_seconds=float(search_seconds),
        n_candidate_evals=int(n_candidate_evals),
        timeout=bool(timeout),
        timeout_budget_sec=float(timeout_sec),
    )


def decode_gnw_row(
    model,
    params_fit,
    phase1_dir: Path,
    row: Mapping[str, Any],
    *,
    condition: str,
    timeout_sec: float,
    split_view: str,
    training_seed: int,
    decoder: str,
    operator_config: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    from models.nesymres_adapter import predict_equation_gpu_run2

    npz = _load_npz(phase1_dir, row)
    try:
        result = predict_equation_gpu_run2(
            model,
            params_fit,
            npz["X_train"],
            npz["y_train"],
            timeout_sec=float(timeout_sec),
            operator_config=dict(operator_config) if operator_config is not None else None,
        )
    except RuntimeError as exc:
        reraise_oom(exc)
        raise
    return score_gnw_prediction(
        phase1_dir,
        row,
        str(result.get("equation") or ""),
        condition=condition,
        timeout_sec=timeout_sec,
        split_view=split_view,
        training_seed=training_seed,
        decoder=decoder,
        failure_reason=result.get("failure_reason"),
        candidate_expressions=list(result.get("all_preds") or []),
        search_seconds=float(result.get("search_seconds") or 0.0),
        n_candidate_evals=int(result.get("n_candidate_evals") or 0),
        timeout=bool(result.get("timeout")),
    )


def mean_penalized_nmse(
    records: Sequence[Mapping[str, Any]],
    *,
    key: str = "nmse",
    families: Iterable[str] | None = None,
) -> float:
    from evaluation.gpu_run2_rankings import mean_nmse_for_families

    return mean_nmse_for_families(records, families=families, key=key)


def filter_selective_ft_layers(
    registry: Mapping[str, Any],
    *,
    include_head: bool = False,
) -> list[str]:
    """Encoder/decoder blocks only. ``output_head`` is a separate control, not a layer rank."""
    allowed = {"encoder", "decoder"}
    if include_head:
        allowed.add("head")
    return [name for name, spec in registry.items() if getattr(spec, "kind", None) in allowed]


def selectable_layer_names(model, *, include_head: bool = False) -> list[str]:
    from models.layer_selector import get_layer_registry

    return filter_selective_ft_layers(get_layer_registry(model), include_head=include_head)


def head_layer_names(model) -> list[str]:
    from models.layer_selector import get_layer_registry

    return [
        name
        for name, spec in get_layer_registry(model).items()
        if spec.kind == "head"
    ]


def resolve_layer_module(model, layer_name: str):
    from models.layer_selector import get_layer_registry

    registry = get_layer_registry(model)
    if layer_name not in registry:
        raise KeyError(f"unknown layer {layer_name!r}; known={sorted(registry)}")
    return registry[layer_name].resolve(model)


def flatten_activation_to_batch(array: np.ndarray, batch_size: int) -> np.ndarray:
    arr = np.asarray(array)
    if arr.ndim == 1:
        return arr.reshape(1, -1)
    for axis, size in enumerate(arr.shape):
        if size == batch_size:
            moved = np.moveaxis(arr, axis, 0)
            return moved.reshape(batch_size, -1)
    return arr.reshape(arr.shape[0], -1)


def collect_layer_representations(
    model,
    loader,
    *,
    device=None,
    max_batches: int = 8,
    layer_names: Sequence[str] | None = None,
) -> dict[str, Any]:
    """Collect per-example hidden states plus symbolic probe labels.

    Does **not** return point-mean scalar targets. Those are not a valid
    surrogate for symbolic-regression layer importance.
    """
    import torch
    from models.layer_selector import get_layer_registry

    device = device or getattr(model, "device", torch.device("cuda" if torch.cuda.is_available() else "cpu"))
    registry = get_layer_registry(model)
    names = list(layer_names or registry)
    captured: dict[str, list[np.ndarray]] = {name: [] for name in names}
    eq_ids: list[str] = []
    next_token_ids: list[int] = []
    batch_sizes: list[int] = []
    hooks = []

    def make_hook(name: str):
        def hook(_mod, _inp, output):
            tensor = output[0] if isinstance(output, tuple) else output
            captured[name].append(tensor.detach().float().cpu().numpy())

        return hook

    for name in names:
        hooks.append(registry[name].resolve(model).register_forward_hook(make_hook(name)))
    model.eval()
    try:
        with torch.no_grad():
            for i, batch in enumerate(loader):
                if i >= int(max_batches):
                    break
                nums = batch[0].to(device)
                tokens = batch[1].to(device)
                model.forward([nums, tokens])
                batch_eq_ids = list(batch[2]) if len(batch) > 2 else [f"batch{i}_{j}" for j in range(nums.shape[0])]
                eq_ids.extend(str(eq_id) for eq_id in batch_eq_ids)
                token_col = tokens[:, 1] if tokens.shape[1] > 1 else tokens[:, 0]
                next_token_ids.extend(int(value) for value in token_col.detach().cpu().tolist())
                batch_sizes.append(int(nums.shape[0]))
    except RuntimeError as exc:
        reraise_oom(exc)
    finally:
        for handle in hooks:
            handle.remove()
    if not eq_ids:
        raise RuntimeError("no batches available for layer representation collection")
    out: dict[str, np.ndarray] = {}
    for name, chunks in captured.items():
        if not chunks:
            continue
        aligned = [
            flatten_activation_to_batch(chunk, batch_size=int(bsz))
            for chunk, bsz in zip(chunks, batch_sizes)
        ]
        out[name] = np.concatenate(aligned, axis=0)
    n = min(len(eq_ids), min((arr.shape[0] for arr in out.values()), default=len(eq_ids)))
    return {
        "hidden": {name: arr[:n] for name, arr in out.items()},
        "eq_ids": eq_ids[:n],
        "next_token_ids": np.asarray(next_token_ids[:n], dtype=np.int64),
    }


def layer_gradient_norms_from_loader(
    model,
    loader,
    *,
    device=None,
) -> dict[str, float]:
    import torch
    from interpretability.probes import gradient_norms
    from models.layer_selector import get_layer_registry

    device = device or getattr(model, "device", torch.device("cuda" if torch.cuda.is_available() else "cpu"))
    registry = get_layer_registry(model)
    model.train()
    model.zero_grad(set_to_none=True)
    batch = next(iter(loader))
    try:
        nums, tokens = batch[0].to(device), batch[1].to(device)
        output, trg = model.forward([nums, tokens])
        loss = model.compute_loss(output, trg)
        loss.backward()
    except RuntimeError as exc:
        reraise_oom(exc)
    named: dict[str, np.ndarray] = {}
    for name, spec in registry.items():
        grads = [
            p.grad.detach().float().cpu().numpy().ravel()
            for p in spec.resolve(model).parameters()
            if p.grad is not None
        ]
        named[name] = np.concatenate(grads) if grads else np.zeros(1, dtype=np.float64)
    model.zero_grad(set_to_none=True)
    model.eval()
    return gradient_norms(named)


def train_layers(
    config: Mapping[str, Any],
    *,
    layer_names: Sequence[str] | None,
    train_loader,
    val_loader,
    seed: int,
):
    from training.single_layer import train_selective

    seed_everything(seed)
    model, params_fit = load_nesymres_gpu_run2(config)
    hp = finetune_hparams(config)
    try:
        metrics = train_selective(
            model,
            train_loader,
            None if layer_names is None else list(layer_names),
            epochs=int(hp["epochs"]),
            lr=float(hp["lr"]),
            device=getattr(model, "device", None),
            val_loader=val_loader,
            patience=int(hp["patience"]),
            min_delta=float(hp["min_delta"]),
        )
    except RuntimeError as exc:
        reraise_oom(exc)
        raise
    return model, params_fit, metrics


def phase5_model_checkpoint_path(
    phase5_dir: Path,
    *,
    view: str,
    condition: str,
    data_seed: int,
    noise: float,
) -> Path:
    """Validation FT weights reused on test (non-frozen conditions)."""
    return (
        Path(phase5_dir)
        / "models"
        / f"{view}_{condition}_seed{int(data_seed)}_noise{float(noise):g}.pt"
    )


def save_phase5_finetuned_checkpoint(
    path: Path,
    model,
    *,
    metrics: Mapping[str, Any],
    hp: Mapping[str, Any],
    layer_names: Sequence[str] | None,
) -> None:
    import torch

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            "state_dict": {key: value.detach().cpu() for key, value in model.state_dict().items()},
            "metrics": dict(metrics),
            "hp": dict(hp),
            "layer_names": None if layer_names is None else list(layer_names),
        },
        path,
    )


def load_phase5_finetuned_checkpoint(
    config: Mapping[str, Any],
    path: Path,
):
    """Load pretrained architecture then apply a validation FT state_dict."""
    import torch

    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"Phase 5 FT checkpoint missing: {path}")
    model, params_fit = load_nesymres_gpu_run2(config)
    device = getattr(model, "device", torch.device("cpu"))
    payload = torch.load(path, map_location=device)
    if "state_dict" not in payload:
        raise KeyError(f"Phase 5 checkpoint missing state_dict: {path}")
    model.load_state_dict(payload["state_dict"])
    model.eval()
    return model, params_fit, payload


def select_hparams_on_validation(
    config: Mapping[str, Any],
    *,
    layer_names: Sequence[str] | None,
    train_loader,
    val_loader,
    seed: int,
) -> dict[str, Any]:
    """Try the configured grid on validation CE only; return the chosen lr/epochs."""
    hp = finetune_hparams(config)
    lr_grid = list(hp["lr_grid"])
    epoch_grid = list(hp["epoch_grid"])
    if len(lr_grid) == 1 and len(epoch_grid) == 1:
        return {"lr": lr_grid[0], "epochs": epoch_grid[0], "val_ce": float("nan"), "n_candidates": 1}
    best: dict[str, Any] | None = None
    for lr in lr_grid:
        for epochs in epoch_grid:
            trial_config = dict(config)
            trial_ft = dict(config.get("finetune") or {})
            trial_ft["lr"] = float(lr)
            trial_ft["epochs"] = int(epochs)
            trial_config["finetune"] = trial_ft
            _model, _params, metrics = train_layers(
                trial_config,
                layer_names=layer_names,
                train_loader=train_loader,
                val_loader=val_loader,
                seed=seed,
            )
            del _model
            val_ce = float(metrics.get("best_val_ce", metrics.get("final_loss", float("inf"))))
            candidate = {"lr": float(lr), "epochs": int(epochs), "val_ce": val_ce}
            if best is None or val_ce < float(best["val_ce"]):
                best = candidate
    assert best is not None
    best["n_candidates"] = len(lr_grid) * len(epoch_grid)
    return best


def gt_token_ids_for_row(row: Mapping[str, Any], word2id: Mapping[str, int]) -> list[int] | None:
    from data.finetune_dataset import expression_to_tokens, instantiate_expr
    from data.synthetic_grn import EquationSpec, SampledDataset

    sampled = SampledDataset(
        spec=EquationSpec(
            eq_id=str(row["eq_id"]),
            family=str(row["family_id"]),
            target_expr=str(row.get("teacher_expr") or row.get("canonical_expr") or ""),
            variable_names=list(row["oracle_inputs"]),
            parameters={"noise": float(row.get("noise", 0.0))},
            split=str(row.get("main_split") or "validation"),
            motif=str(row.get("canonical_expr") or ""),
        ),
        X=np.zeros((1, max(1, len(row["oracle_inputs"])))),
        y=np.zeros(1),
    )
    expr = instantiate_expr(sampled)
    tokens = expression_to_tokens(expr, dict(word2id))
    return None if tokens is None else list(tokens)


def _load_npz(phase1_dir: Path, row: Mapping[str, Any]) -> dict[str, Any]:
    from data.gnw_synthetic import load_problem_npz

    return load_problem_npz(Path(phase1_dir) / "data" / row["file"])


def iter_seed_noise(config: Mapping[str, Any], *, smoke: bool = False) -> list[tuple[int, int, float]]:
    bundles = seed_bundles(config)
    noises = [float(x) for x in config["noises"]]
    if smoke:
        bundles = bundles[:1]
        noises = noises[:1]
    return [
        (int(bundle["data_seed"]), int(bundle["model_seed"]), float(noise))
        for bundle in bundles
        for noise in noises
    ]
