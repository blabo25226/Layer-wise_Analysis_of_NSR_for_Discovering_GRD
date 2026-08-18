"""Shared GPU_RUN4 phase session: config, device, checkpoint, protocol."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from gpu_run4.architecture import inventory_odeformer, unwrap_model
from gpu_run4.cli import phase_budget
from gpu_run4_runtime import (
    load_gpu_run4_configs,
    load_odeformer_model,
    make_symbolic_regressor,
    odeformer_paths,
    paper_model_args,
    require_python_310,
    resolve_run_dir,
    select_device,
)


def open_session(args: Any) -> dict[str, Any]:
    require_python_310()
    config = load_gpu_run4_configs()
    run_dir = resolve_run_dir(args.run_id, config=config)
    budget = phase_budget(config, smoke=bool(getattr(args, "smoke", False)))
    protocol = dict(config.get("paper_protocol") or {})
    timeouts = dict(config.get("timeouts") or {})
    paths = odeformer_paths(config)
    device = select_device(allow_cpu=bool(getattr(args, "allow_cpu", False) or config.get("allow_cpu")))
    model = load_odeformer_model(paths["checkpoint"], device=device)
    inventory = inventory_odeformer(model)
    model_args = paper_model_args(protocol)
    if getattr(args, "smoke", False) and budget.get("beam_size"):
        model_args["beam_size"] = int(budget["beam_size"])
    regressor = make_symbolic_regressor(
        unwrap_model(model),
        rescale=bool(protocol.get("rescale", True)),
        beam_size=int(model_args["beam_size"]),
        beam_temperature=float(model_args["beam_temperature"]),
        beam_type=str(model_args["beam_type"]),
    )
    return {
        "config": config,
        "run_dir": run_dir,
        "budget": budget,
        "protocol": protocol,
        "timeouts": timeouts,
        "paths": paths,
        "device": device,
        "model": model,
        "inventory": inventory,
        "regressor": regressor,
        "model_args": model_args,
        "ranking_layers": list(inventory["ranking_layers"]),
    }


def jsonable(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if hasattr(value, "tolist"):
        return value.tolist()
    if isinstance(value, dict):
        return {str(k): jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(v) for v in value]
    return value
