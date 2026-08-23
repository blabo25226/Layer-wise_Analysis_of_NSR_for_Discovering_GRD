"""Deterministic, failure-aware fine-tuning helpers for GPU_RUN5.

This module intentionally does not know about phase directories or sealed test
artifacts.  Phase 6--8 scripts provide already-authorized train/validation
records and persist the returned records themselves.
"""

from __future__ import annotations

import hashlib
import itertools
import json
import math
import os
import random
import time
from copy import deepcopy
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence

# This must be set before torch creates any CUDA/cuBLAS context.  GPU_RUN5
# phase launchers import this module before loading a model onto CUDA.
os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")

import numpy as np
import torch

from gpu_run4.architecture import set_trainable_layers
from gpu_run4.training import teacher_forcing_loss


OFFICIAL_SNAPSHOT_STEPS = (50, 200, 1000)
DELTA_SCHEMA_VERSION = "gpu_run5_parameter_delta_v1"
OFFICIAL_LAYER_REGISTRY = tuple(
    [f"encoder_{index}" for index in range(4)]
    + [f"decoder_{index}" for index in range(12)]
)
TRIAL_IDENTITY_KEYS = (
    "condition",
    "view",
    "bundle_indices",
    "base_model_state_sha256",
    "training_corpus_sha256",
    "training_order_sha256",
    "model_seed",
    "validation_panel_sha256",
    "candidate_seed_map_sha256",
)


def _record_id(row: Mapping[str, Any]) -> str:
    for key in ("system_id", "problem_id", "eq_id"):
        value = row.get(key)
        if value is not None and str(value):
            return str(value)
    raise ValueError("training record has no system_id, problem_id, or eq_id")


def adapt_input_training_records(
    records: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Normalize records while admitting only the clean input-role trajectory.

    GRN records must contain exactly one ``role=input`` trajectory.  Official
    generator records instead carry ``times`` and ``trajectory`` at top level.
    Selection/generalization trajectories are never returned.
    """
    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()
    for source in records:
        row = dict(source)
        record_id = _record_id(row)
        if record_id in seen:
            raise ValueError(f"duplicate training record id: {record_id}")
        seen.add(record_id)

        trajectories = row.get("trajectories")
        if trajectories is not None:
            inputs = [item for item in trajectories if item.get("role") == "input"]
            if len(inputs) != 1:
                raise ValueError(
                    f"GRN training record {record_id} must have exactly one input trajectory"
                )
            trajectory_row = inputs[0]
            times = np.asarray(trajectory_row.get("times"), dtype=float)
            trajectory = np.asarray(trajectory_row.get("trajectory"), dtype=float)
            source_checksum = trajectory_row.get("checksum")
            source_role = "input"
        else:
            if "times" not in row or "trajectory" not in row:
                raise ValueError(f"official training record {record_id} has no trajectory")
            times = np.asarray(row["times"], dtype=float)
            trajectory = np.asarray(row["trajectory"], dtype=float)
            source_checksum = row.get("checksum")
            source_role = "official_top_level"

        tree = list(row.get("tree_encoded") or [])
        if not tree:
            raise ValueError(f"training record {record_id} has no teacher prefix")
        if times.ndim != 1 or trajectory.ndim != 2 or len(times) != len(trajectory):
            raise ValueError(
                f"invalid training trajectory shape for {record_id}: "
                f"times={times.shape}, trajectory={trajectory.shape}"
            )
        if len(times) < 2 or not np.isfinite(times).all() or not np.isfinite(trajectory).all():
            raise ValueError(f"non-finite or too-short training trajectory: {record_id}")
        normalized.append(
            {
                "record_id": record_id,
                "times": times,
                "trajectory": trajectory,
                "tree_encoded": tree,
                "source_role": source_role,
                "source_checksum": source_checksum,
            }
        )
    if not normalized:
        raise ValueError("training corpus is empty")
    return sorted(normalized, key=lambda row: row["record_id"])


def training_order(
    records: Sequence[Mapping[str, Any]],
    *,
    steps: int,
    seed: int,
) -> dict[str, Any]:
    """Return an epoch-shuffled batch-1 schedule and its condition-free hash."""
    n_steps = int(steps)
    if n_steps <= 0:
        raise ValueError("steps must be positive")
    identifiers = [str(row["record_id"]) for row in records]
    if not identifiers or len(set(identifiers)) != len(identifiers):
        raise ValueError("training records must have unique record_id values")
    rng = np.random.default_rng(int(seed))
    indices: list[int] = []
    while len(indices) < n_steps:
        indices.extend(int(value) for value in rng.permutation(len(identifiers)))
    indices = indices[:n_steps]
    scheduled_ids = [identifiers[index] for index in indices]
    record_hashes = []
    for row in records:
        digest = hashlib.sha256()
        digest.update(str(row["record_id"]).encode("utf-8"))
        for key in ("times", "trajectory"):
            array = np.asarray(row[key]).astype(float, copy=False)
            digest.update(key.encode("ascii"))
            digest.update(json.dumps(list(array.shape), separators=(",", ":")).encode("ascii"))
            digest.update(array.tobytes(order="C"))
        digest.update(json.dumps(list(row["tree_encoded"]), separators=(",", ":")).encode("utf-8"))
        digest.update(str(row.get("source_role")).encode("utf-8"))
        digest.update(str(row.get("source_checksum")).encode("utf-8"))
        record_hashes.append(digest.hexdigest())
    corpus_encoded = json.dumps(
        list(zip(identifiers, record_hashes)), separators=(",", ":")
    ).encode("utf-8")
    corpus_sha256 = hashlib.sha256(corpus_encoded).hexdigest()
    encoded = json.dumps(
        {
            "seed": int(seed), "record_ids": identifiers,
            "record_sha256": record_hashes, "schedule": scheduled_ids,
            "corpus_sha256": corpus_sha256,
        },
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return {
        "indices": indices,
        "record_ids": scheduled_ids,
        "order_sha256": hashlib.sha256(encoded).hexdigest(),
        "training_corpus_sha256": corpus_sha256,
        "record_sha256": record_hashes,
        "seed": int(seed),
        "steps": n_steps,
    }


def seed_training_rng(seed: int) -> None:
    """Reset every RNG and require deterministic PyTorch/CUDA algorithms."""
    if os.environ.get("CUBLAS_WORKSPACE_CONFIG") != ":4096:8":
        raise RuntimeError("CUBLAS_WORKSPACE_CONFIG must be :4096:8 before training")
    value = int(seed)
    random.seed(value)
    np.random.seed(value)
    torch.manual_seed(value)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(value)
    torch.use_deterministic_algorithms(True)
    if hasattr(torch.backends, "cudnn"):
        torch.backends.cudnn.benchmark = False
        torch.backends.cudnn.deterministic = True


def torch_determinism_record() -> dict[str, Any]:
    """Return the determinism contract persisted by every training trial."""
    return {
        "deterministic_algorithms": bool(torch.are_deterministic_algorithms_enabled()),
        "cudnn_benchmark": bool(torch.backends.cudnn.benchmark),
        "cudnn_deterministic": bool(torch.backends.cudnn.deterministic),
        "cublas_workspace_config": os.environ.get("CUBLAS_WORKSPACE_CONFIG"),
    }


def trainable_parameter_keys(model: torch.nn.Module) -> list[str]:
    return sorted(name for name, parameter in model.named_parameters() if parameter.requires_grad)


def _parameter_state(
    model: torch.nn.Module,
    keys: Sequence[str],
) -> dict[str, torch.Tensor]:
    parameters = dict(model.named_parameters())
    missing = sorted(set(keys) - set(parameters))
    if missing:
        raise KeyError(f"parameter allowlist is not present in model: {missing}")
    return {
        key: parameters[key].detach().cpu().clone()
        for key in sorted(keys)
    }


def restore_parameter_state(
    model: torch.nn.Module,
    state: Mapping[str, torch.Tensor],
    *,
    allowed_parameter_keys: Sequence[str],
) -> None:
    """Restore exactly an allowlisted parameter delta, rejecting extra keys."""
    expected = sorted(str(key) for key in allowed_parameter_keys)
    observed = sorted(str(key) for key in state)
    if observed != expected:
        raise ValueError(
            f"delta parameter allowlist mismatch: observed={observed}, expected={expected}"
        )
    parameters = dict(model.named_parameters())
    if any(key not in parameters for key in expected):
        raise KeyError("delta contains a parameter absent from the target model")
    with torch.no_grad():
        for key in expected:
            source = state[key]
            target = parameters[key]
            if tuple(source.shape) != tuple(target.shape) or source.dtype != target.dtype:
                raise ValueError(
                    f"delta tensor mismatch for {key}: "
                    f"{tuple(source.shape)}/{source.dtype} != {tuple(target.shape)}/{target.dtype}"
                )
            target.copy_(source.to(device=target.device))


def _default_loss(model: Any, record: Mapping[str, Any]) -> torch.Tensor:
    return teacher_forcing_loss(
        model,
        np.asarray(record["times"], dtype=float),
        np.asarray(record["trajectory"], dtype=float),
        list(record["tree_encoded"]),
    )


def train_adam_with_snapshots(
    model: torch.nn.Module,
    records: Sequence[Mapping[str, Any]],
    *,
    trainable_layers: set[str] | None,
    lr: float,
    max_steps: int = 1000,
    snapshot_steps: Sequence[int] = OFFICIAL_SNAPSHOT_STEPS,
    data_order_seed: int,
    model_seed: int,
    loss_fn: Callable[[torch.nn.Module, Mapping[str, Any]], torch.Tensor] | None = None,
    configure_trainable: Callable[[torch.nn.Module, set[str] | None], Any] = set_trainable_layers,
    snapshot_callback: Callable[[int, Mapping[str, torch.Tensor]], None] | None = None,
    keep_snapshots: bool = True,
) -> dict[str, Any]:
    """Run deterministic Adam batch-1 training and capture exact-step deltas.

    The function stops visibly on a non-finite loss, gradient, or updated
    parameter.  Earlier exact-step snapshots remain available; a failed run is
    never silently treated as a shorter successful candidate.
    """
    rate = float(lr)
    n_steps = int(max_steps)
    checkpoints = sorted({int(step) for step in snapshot_steps})
    if not math.isfinite(rate) or rate <= 0:
        raise ValueError("lr must be finite and positive")
    if n_steps <= 0 or not checkpoints or checkpoints[-1] > n_steps or checkpoints[0] <= 0:
        raise ValueError("snapshot_steps must be positive and within max_steps")
    if not keep_snapshots and snapshot_callback is None:
        raise ValueError("snapshot_callback is required when keep_snapshots is false")
    normalized = adapt_input_training_records(records)
    schedule = training_order(normalized, steps=n_steps, seed=int(data_order_seed))
    seed_training_rng(int(model_seed))
    configure_trainable(model, trainable_layers)
    parameter_keys = trainable_parameter_keys(model)
    if not parameter_keys:
        raise ValueError("trainable layer selection produced no parameters")
    parameters = [dict(model.named_parameters())[key] for key in parameter_keys]
    optimizer = torch.optim.Adam(parameters, lr=rate)
    losses: list[float] = []
    snapshots: dict[int, dict[str, torch.Tensor]] = {}
    failure_reason: str | None = None
    completed_steps = 0
    started = time.perf_counter()
    model.train()

    for step, record_index in enumerate(schedule["indices"], start=1):
        optimizer.zero_grad(set_to_none=True)
        try:
            loss = (loss_fn or _default_loss)(model, normalized[record_index])
        except torch.cuda.OutOfMemoryError:
            # GPU_RUN5 is configured to fail fast on OOM; it must never be
            # reclassified as an ordinary problem-level training failure.
            raise
        except Exception as exc:
            failure_reason = f"LossError:{type(exc).__name__}:{exc}"
            break
        if not isinstance(loss, torch.Tensor) or loss.numel() != 1:
            failure_reason = "InvalidLossTensor"
            break
        loss_value = float(loss.detach().cpu())
        if not math.isfinite(loss_value):
            failure_reason = "NonFiniteLoss"
            break
        loss.backward()
        if any(
            parameter.grad is not None and not torch.isfinite(parameter.grad).all()
            for parameter in parameters
        ):
            failure_reason = "NonFiniteGradient"
            optimizer.zero_grad(set_to_none=True)
            break
        optimizer.step()
        if any(not torch.isfinite(parameter).all() for parameter in parameters):
            failure_reason = "NonFiniteParameter"
            break
        completed_steps = step
        losses.append(loss_value)
        if step in checkpoints:
            state = _parameter_state(model, parameter_keys)
            if snapshot_callback is not None:
                snapshot_callback(step, state)
            if keep_snapshots:
                snapshots[step] = state

    model.eval()
    return {
        "status": "complete" if failure_reason is None and completed_steps == n_steps else "failed",
        "failure_reason": failure_reason,
        "lr": rate,
        "requested_steps": n_steps,
        "completed_steps": completed_steps,
        "snapshot_steps_requested": checkpoints,
        "snapshot_steps_completed": sorted(snapshots) if keep_snapshots else [
            step for step in checkpoints if step <= completed_steps
        ],
        "snapshots": snapshots,
        "losses": losses,
        "final_loss": losses[-1] if losses else None,
        "trainable_parameter_keys": parameter_keys,
        "trainable_parameters": int(sum(parameter.numel() for parameter in parameters)),
        "data_order_seed": int(data_order_seed),
        "model_seed": int(model_seed),
        "order_sha256": schedule["order_sha256"],
        "training_corpus_sha256": schedule["training_corpus_sha256"],
        "scheduled_record_ids": schedule["record_ids"],
        "batch_size": 1,
        "optimizer": "Adam",
        "determinism": torch_determinism_record(),
        "wall_time_sec": time.perf_counter() - started,
    }


def _tensor_digest(state: Mapping[str, torch.Tensor]) -> str:
    digest = hashlib.sha256()
    for key in sorted(state):
        tensor = state[key].detach().cpu().contiguous()
        digest.update(key.encode("utf-8"))
        digest.update(str(tensor.dtype).encode("ascii"))
        digest.update(json.dumps(list(tensor.shape), separators=(",", ":")).encode("ascii"))
        digest.update(tensor.view(torch.uint8).numpy().tobytes())
    return digest.hexdigest()


def model_state_sha256(model: torch.nn.Module) -> str:
    """Hash all parameters and buffers of a concrete model state."""
    return _tensor_digest(model.state_dict())


def make_delta_checkpoint(
    model: torch.nn.Module,
    *,
    allowed_parameter_keys: Sequence[str],
    identity: Mapping[str, Any],
    trainable_layers: set[str] | None,
    base_model_state_sha256: str,
) -> dict[str, Any]:
    """Create a self-hashing parameter-only checkpoint with an exact allowlist."""
    keys = sorted(str(key) for key in allowed_parameter_keys)
    if keys != trainable_parameter_keys(model):
        raise ValueError("allowed_parameter_keys must exactly equal currently trainable parameters")
    state = _parameter_state(model, keys)
    normalized_identity = json.loads(json.dumps(dict(identity), sort_keys=True, default=str))
    payload = {
        "schema_version": DELTA_SCHEMA_VERSION,
        "identity": normalized_identity,
        "identity_sha256": hashlib.sha256(
            json.dumps(normalized_identity, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest(),
        "trainable_layers": None if trainable_layers is None else sorted(trainable_layers),
        "base_model_state_sha256": str(base_model_state_sha256),
        "parameter_keys": keys,
        "parameter_state": state,
        "delta_sha256": _tensor_digest(state),
    }
    payload["checkpoint_sha256"] = _checkpoint_metadata_digest(payload)
    return payload


def _checkpoint_metadata_digest(checkpoint: Mapping[str, Any]) -> str:
    metadata = {
        "schema_version": checkpoint.get("schema_version"),
        "identity": checkpoint.get("identity"),
        "identity_sha256": checkpoint.get("identity_sha256"),
        "trainable_layers": checkpoint.get("trainable_layers"),
        "base_model_state_sha256": checkpoint.get("base_model_state_sha256"),
        "parameter_keys": checkpoint.get("parameter_keys"),
        "delta_sha256": checkpoint.get("delta_sha256"),
    }
    return hashlib.sha256(
        json.dumps(metadata, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def apply_delta_checkpoint(
    model: torch.nn.Module,
    checkpoint: Mapping[str, Any],
    *,
    allowed_parameter_keys: Sequence[str],
    expected_identity: Mapping[str, Any],
) -> torch.nn.Module:
    """Verify and apply a delta to a fresh base model."""
    if checkpoint.get("schema_version") != DELTA_SCHEMA_VERSION:
        raise ValueError("unsupported delta checkpoint schema")
    expected_keys = sorted(str(key) for key in allowed_parameter_keys)
    if list(checkpoint.get("parameter_keys") or []) != expected_keys:
        raise ValueError("delta checkpoint parameter allowlist mismatch")
    identity = json.loads(json.dumps(dict(expected_identity), sort_keys=True, default=str))
    if checkpoint.get("identity") != identity:
        raise ValueError("delta checkpoint identity mismatch")
    identity_sha = hashlib.sha256(
        json.dumps(identity, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    if checkpoint.get("identity_sha256") != identity_sha:
        raise ValueError("delta checkpoint identity hash mismatch")
    if checkpoint.get("checkpoint_sha256") != _checkpoint_metadata_digest(checkpoint):
        raise ValueError("delta checkpoint metadata hash mismatch")
    observed_base_sha = model_state_sha256(model)
    if checkpoint.get("base_model_state_sha256") != observed_base_sha:
        raise ValueError(
            "delta checkpoint base model state mismatch: "
            f"observed={observed_base_sha}"
        )
    state = checkpoint.get("parameter_state")
    if not isinstance(state, Mapping) or checkpoint.get("delta_sha256") != _tensor_digest(state):
        raise ValueError("delta checkpoint tensor hash mismatch")
    restore_parameter_state(model, state, allowed_parameter_keys=expected_keys)
    return model


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def save_delta_checkpoint(path: Path, checkpoint: Mapping[str, Any]) -> dict[str, str]:
    """Atomically save a delta and return both tensor and file identities."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(target.name + ".partial")
    torch.save(dict(checkpoint), temporary)
    temporary.replace(target)
    return {
        "file_sha256": _file_sha256(target),
        "delta_sha256": str(checkpoint["delta_sha256"]),
    }


def load_delta_checkpoint(path: Path, *, expected_file_sha256: str) -> dict[str, Any]:
    """Load a delta only after verifying its serialized file identity."""
    source = Path(path)
    observed = _file_sha256(source)
    if observed != str(expected_file_sha256):
        raise ValueError(f"delta checkpoint file hash mismatch: {observed}")
    try:
        payload = torch.load(source, map_location="cpu", weights_only=True)
    except TypeError:  # pragma: no cover - compatibility with older torch
        payload = torch.load(source, map_location="cpu")
    if not isinstance(payload, dict):
        raise ValueError("delta checkpoint payload is not a mapping")
    return payload


def _component_values(row: Mapping[str, Any]) -> tuple[float, float, float]:
    exact = list(row.get("component_exponent_aware_skeleton_exact") or [])
    ted = list(row.get("component_normalized_variable_aware_ted") or [])
    valid = list(row.get("component_valid") or [])
    count = max(len(exact), len(ted), len(valid), int(row.get("dimension") or 0), 1)
    values: list[tuple[float, float, float]] = []
    for index in range(count):
        is_valid = bool(valid[index]) if index < len(valid) else False
        exact_value = float(exact[index]) if is_valid and index < len(exact) else 0.0
        ted_value = float(ted[index]) if is_valid and index < len(ted) else 1.0
        if not math.isfinite(exact_value):
            exact_value = 0.0
        if not math.isfinite(ted_value):
            ted_value = 1.0
        values.append((min(max(exact_value, 0.0), 1.0), min(max(ted_value, 0.0), 1.0), float(is_valid)))
    array = np.asarray(values, dtype=float)
    return float(array[:, 0].mean()), float(array[:, 1].mean()), float(array[:, 2].mean())


def formula_score_vector(
    rows: Sequence[Mapping[str, Any]],
    *,
    validation_ce: float | None = None,
    expected_cell_ids: Sequence[str],
) -> tuple[float, float, float, float]:
    """Return ``(exact, -failure-aware TED, valid, -CE)`` macro system→seed."""
    expected = sorted(str(value) for value in expected_cell_ids)
    if not expected or len(expected) != len(set(expected)):
        raise ValueError("expected_cell_ids must be non-empty and unique")
    observed = []
    for row in rows:
        cell_id = row.get("cell_id")
        if cell_id is None:
            cell_id = ":".join(
                str(row.get(key, ""))
                for key in ("system_id", "bundle_index", "corruption_id")
            )
        observed.append(str(cell_id))
    if sorted(observed) != expected:
        raise ValueError(
            "validation formula coverage mismatch: "
            f"observed={len(observed)}/{len(set(observed))}, expected={len(expected)}"
        )
    if not rows:
        ce = float(validation_ce) if validation_ce is not None else float("inf")
        return 0.0, -1.0, 0.0, -ce
    grouped: dict[int, dict[str, list[tuple[float, float, float]]]] = {}
    ce_grouped: dict[int, dict[str, list[float]]] = {}
    for row in rows:
        seed = int(row.get("bundle_index", row.get("seed", 0)))
        system_id = str(row.get("system_id") or row.get("problem_id") or "")
        if not system_id:
            raise ValueError("formula score row has no system identity")
        grouped.setdefault(seed, {}).setdefault(system_id, []).append(_component_values(row))
        if validation_ce is None:
            raw_ce = row.get("validation_teacher_forcing_ce", row.get("ce"))
            value = float(raw_ce) if raw_ce is not None else float("inf")
            ce_grouped.setdefault(seed, {}).setdefault(system_id, []).append(value)
    seed_scores: list[tuple[float, float, float]] = []
    for systems in grouped.values():
        system_scores = [
            tuple(float(np.mean([cell[index] for cell in cells])) for index in range(3))
            for cells in systems.values()
        ]
        seed_scores.append(
            tuple(float(np.mean([score[index] for score in system_scores])) for index in range(3))
        )
    exact, ted, valid = (
        float(np.mean([score[index] for score in seed_scores])) for index in range(3)
    )
    if validation_ce is not None:
        ce = float(validation_ce)
    else:
        seed_ce: list[float] = []
        for systems in ce_grouped.values():
            system_ce = [
                float(np.mean(values)) if values and all(map(math.isfinite, values)) else float("inf")
                for values in systems.values()
            ]
            seed_ce.append(
                float(np.mean(system_ce)) if system_ce and all(map(math.isfinite, system_ce)) else float("inf")
            )
        ce = float(np.mean(seed_ce)) if seed_ce and all(map(math.isfinite, seed_ce)) else float("inf")
    if not math.isfinite(ce):
        ce = float("inf")
    return exact, -ted, valid, -ce


def select_formula_candidate(
    candidates: Sequence[Mapping[str, Any]],
    *,
    expected_count: int = 9,
    expected_lrs: Sequence[float] = (1e-6, 1e-5, 1e-4),
    expected_steps: Sequence[int] = OFFICIAL_SNAPSHOT_STEPS,
    quantization_digits: int = 12,
    expected_validation_cell_ids: Sequence[str],
) -> dict[str, Any]:
    """Validate and select the complete 3x3 grid by failure-aware formula score."""
    if len(candidates) != int(expected_count):
        raise ValueError(f"expected {expected_count} hyperparameter candidates, got {len(candidates)}")
    expected_grid = {
        (float(lr), int(step)) for lr in expected_lrs for step in expected_steps
    }
    if len(expected_grid) != int(expected_count):
        raise ValueError("expected lr x step grid does not match expected_count")
    keyed: dict[tuple[float, int], dict[str, Any]] = {}
    successful_coverages: list[tuple[str, ...]] = []
    shared_identity: dict[str, Any] | None = None
    expected_coverage = tuple(sorted(str(value) for value in expected_validation_cell_ids))
    if not expected_coverage or len(expected_coverage) != len(set(expected_coverage)):
        raise ValueError("expected_validation_cell_ids must be non-empty and unique")
    for source in candidates:
        row = deepcopy(dict(source))
        config = dict(row.get("config") or {})
        key = (float(config.get("lr", float("nan"))), int(config.get("steps", -1)))
        if key in keyed:
            raise ValueError(f"duplicate hyperparameter candidate: {key}")
        status = str(row.get("status") or "")
        if status not in {"complete", "failed"}:
            raise ValueError(f"candidate {key} has invalid status: {status}")
        coverage = tuple(sorted(str(value) for value in row.get("validation_cell_ids") or []))
        if status == "complete":
            if coverage != expected_coverage:
                raise ValueError(f"successful candidate {key} validation coverage mismatch")
            successful_coverages.append(coverage)
        elif not row.get("failure_reason"):
            raise ValueError(f"failed candidate {key} has no failure_reason")
        identity = dict(row.get("trial_identity") or {})
        missing_identity = [
            name for name in TRIAL_IDENTITY_KEYS
            if name not in identity or identity[name] is None or identity[name] == ""
        ]
        if missing_identity:
            raise ValueError(f"candidate {key} trial identity missing: {missing_identity}")
        normalized_identity = {
            name: identity[name] for name in TRIAL_IDENTITY_KEYS
        }
        if shared_identity is None:
            shared_identity = normalized_identity
        elif normalized_identity != shared_identity:
            raise ValueError(f"candidate {key} trial identity is not paired")
        keyed[key] = row
    if set(keyed) != expected_grid:
        raise ValueError(
            f"hyperparameter grid mismatch: observed={sorted(keyed)}, expected={sorted(expected_grid)}"
        )
    if successful_coverages and any(
        coverage != successful_coverages[0] for coverage in successful_coverages[1:]
    ):
        raise ValueError("successful candidates do not share identical validation coverage")
    retained: list[dict[str, Any]] = []
    best_index = -1
    best_vector: tuple[float, float, float, float] | None = None
    digits = int(quantization_digits)
    for index, key in enumerate(sorted(keyed)):
        row = keyed[key]
        vector = tuple(float(value) for value in row.get("score_vector", ()))
        if len(vector) != 4 or any(math.isnan(value) for value in vector):
            raise ValueError(f"invalid formula score vector at candidate {index}: {vector}")
        exact, negative_ted, valid, negative_ce = vector
        if not (
            math.isfinite(exact) and 0.0 <= exact <= 1.0
            and math.isfinite(negative_ted) and -1.0 <= negative_ted <= 0.0
            and math.isfinite(valid) and 0.0 <= valid <= 1.0
            and negative_ce <= 0.0 and negative_ce != float("inf")
        ):
            raise ValueError(f"formula score vector is outside its valid range: {vector}")
        if row["status"] == "failed" and vector != (0.0, -1.0, 0.0, -float("inf")):
            raise ValueError(f"failed candidate {key} must carry the worst score vector")
        quantized = tuple(
            round(value, digits) if math.isfinite(value) else value for value in vector
        )
        row["score_vector"] = list(vector)
        row["quantized_score_vector"] = list(quantized)
        row["candidate_index"] = index
        retained.append(row)
        if best_vector is None or quantized > best_vector:
            best_index, best_vector = index, quantized
    if not successful_coverages:
        raise ValueError("all hyperparameter candidates failed; no candidate may be selected")
    for index, row in enumerate(retained):
        row["selected"] = index == best_index
    return {
        "criterion": "validation_formula_lexicographic_exact_ted_valid_ce",
        "candidate_count": len(retained),
        "selected_index": best_index,
        "selected": deepcopy(retained[best_index]),
        "trials": retained,
        "quantization_digits": digits,
        "validation_cell_ids": list(successful_coverages[0]) if successful_coverages else [],
        "trial_identity": deepcopy(shared_identity),
    }


def deterministic_random_layer_sets(
    layers: Sequence[str],
    *,
    seed: int = 5101,
    n_sets: int = 5,
    k: int = 3,
) -> list[list[str]]:
    """Sample distinct random-k sets; overlap between different sets is allowed."""
    names = list(dict.fromkeys(str(layer) for layer in layers))
    if len(names) != len(layers) or set(names) != set(OFFICIAL_LAYER_REGISTRY):
        raise ValueError("layers must exactly match the frozen 16-layer registry")
    names = list(OFFICIAL_LAYER_REGISTRY)
    if not 0 < int(k) <= len(names):
        raise ValueError("k must fit the registry")
    if math.comb(len(names), int(k)) < int(n_sets):
        raise ValueError("not enough distinct layer combinations")
    rng = np.random.default_rng(int(seed))
    output: list[list[str]] = []
    seen: set[tuple[str, ...]] = set()
    while len(output) < int(n_sets):
        indices = sorted(int(index) for index in rng.choice(len(names), size=int(k), replace=False))
        key = tuple(names[index] for index in indices)
        if key not in seen:
            seen.add(key)
            output.append(list(key))
    return output


def tie_aware_vector_ranking(
    scores: Mapping[str, Sequence[float]],
    *,
    quantization_digits: int = 12,
) -> dict[str, Any]:
    """Rank higher-is-better vectors with dense tie groups and average ranks."""
    digits = int(quantization_digits)
    prepared: list[tuple[str, tuple[float, ...] | None]] = []
    for name, raw in scores.items():
        values = tuple(float(value) for value in raw)
        vector = tuple(round(value, digits) for value in values) if values and all(map(math.isfinite, values)) else None
        prepared.append((str(name), vector))
    prepared.sort(
        key=lambda item: (
            item[1] is None,
            tuple(-value for value in item[1]) if item[1] is not None else (),
            item[0],
        )
    )
    group_by_vector: dict[tuple[float, ...] | None, list[int]] = {}
    for position, (_name, vector) in enumerate(prepared, start=1):
        group_by_vector.setdefault(vector, []).append(position)
    dense_groups: dict[tuple[float, ...] | None, int] = {}
    rows = []
    for position, (name, vector) in enumerate(prepared, start=1):
        if vector not in dense_groups:
            dense_groups[vector] = len(dense_groups) + 1
        positions = group_by_vector[vector]
        rows.append(
            {
                "name": name,
                "rank": position,
                "average_rank": float(np.mean(positions)),
                "tie_group": dense_groups[vector],
                "quantized_score_vector": list(vector) if vector is not None else None,
            }
        )
    return {
        "ranking": [row["name"] for row in rows],
        "rows": rows,
        "quantization_digits": digits,
        "tie_group_count": len(dense_groups),
    }


def rank_correlations(
    left: Mapping[str, float],
    right: Mapping[str, float],
) -> dict[str, Any]:
    """Compute Spearman and Kendall tau-b, returning null for constant ranks."""
    names = sorted(set(left) & set(right))
    if len(names) < 2:
        return {"spearman": None, "kendall_tau_b": None, "reason": "fewer_than_two_layers", "n_layers": len(names)}
    x = np.asarray([float(left[name]) for name in names], dtype=float)
    y = np.asarray([float(right[name]) for name in names], dtype=float)
    if not np.isfinite(x).all() or not np.isfinite(y).all():
        return {"spearman": None, "kendall_tau_b": None, "reason": "non_finite_rank", "n_layers": len(names)}
    if np.all(x == x[0]) or np.all(y == y[0]):
        return {"spearman": None, "kendall_tau_b": None, "reason": "constant_rank", "n_layers": len(names)}
    from scipy.stats import kendalltau, spearmanr

    spearman = float(spearmanr(x, y).statistic)
    kendall = float(kendalltau(x, y, variant="b").statistic)
    if not math.isfinite(spearman) or not math.isfinite(kendall):
        return {"spearman": None, "kendall_tau_b": None, "reason": "non_finite_correlation", "n_layers": len(names)}
    return {"spearman": spearman, "kendall_tau_b": kendall, "reason": None, "n_layers": len(names)}


def pairwise_rank_stability(
    scores_by_seed: Mapping[int | str, Mapping[str, Sequence[float]]],
    *,
    quantization_digits: int = 12,
) -> dict[str, Any]:
    """Create tie-aware ranks per seed and all pairwise stability records."""
    rankings = {
        str(seed): tie_aware_vector_ranking(scores, quantization_digits=quantization_digits)
        for seed, scores in scores_by_seed.items()
    }
    layer_sets = [set(ranking["ranking"]) for ranking in rankings.values()]
    if layer_sets and any(layers != layer_sets[0] for layers in layer_sets[1:]):
        raise ValueError("rank stability requires the identical layer registry for every seed")
    pairs = []
    for left_seed, right_seed in itertools.combinations(sorted(rankings), 2):
        left = {row["name"]: row["average_rank"] for row in rankings[left_seed]["rows"]}
        right = {row["name"]: row["average_rank"] for row in rankings[right_seed]["rows"]}
        pairs.append(
            {
                "left_seed": left_seed,
                "right_seed": right_seed,
                **rank_correlations(left, right),
            }
        )
    finite_spearman = [row["spearman"] for row in pairs if row["spearman"] is not None]
    finite_kendall = [row["kendall_tau_b"] for row in pairs if row["kendall_tau_b"] is not None]
    return {
        "rankings": rankings,
        "pairs": pairs,
        "mean_spearman": float(np.mean(finite_spearman)) if finite_spearman else None,
        "mean_kendall_tau_b": float(np.mean(finite_kendall)) if finite_kendall else None,
    }
