"""Official ND2 synthetic-system simulation for GPU_RUN3."""

from __future__ import annotations

from typing import Any

import numpy as np

from gpu_run3.formulas import parse_to_prefix, prefix_to_string
from gpu_run3_runtime import install_nd2_path, load_yaml_mapping


def load_official_systems(synthetic_config: Any) -> dict[str, Any]:
    path = synthetic_config
    return load_yaml_mapping(path)


def er_adjacency(n_nodes: int, n_edges: int, *, directed: bool, dag: bool, rng: np.random.Generator) -> np.ndarray:
    A = np.zeros((n_nodes, n_nodes), dtype=int)
    if not directed:
        if n_edges % 2:
            n_edges -= 1
        tmp = np.triu_indices(n_nodes, 1)
        count = min(n_edges // 2, len(tmp[0]))
        idx = rng.choice(len(tmp[0]), count, replace=False)
        A[tmp[0][idx], tmp[1][idx]] = 1
        A[tmp[1][idx], tmp[0][idx]] = 1
    elif dag:
        tmp = np.stack(np.triu_indices(n_nodes, 1), axis=-1)
        count = min(n_edges, len(tmp))
        idx = rng.choice(len(tmp), count, replace=False)
        A[tmp[idx, 0], tmp[idx, 1]] = 1
    else:
        tmp = np.concatenate(
            [
                np.stack(np.triu_indices(n_nodes, 1), axis=-1),
                np.stack(np.tril_indices(n_nodes, -1), axis=-1),
            ],
            axis=0,
        )
        count = min(n_edges, len(tmp))
        idx = rng.choice(len(tmp), count, replace=False)
        A[tmp[idx, 0], tmp[idx, 1]] = 1
    np.fill_diagonal(A, 0)
    return A


def simulate_system(
    system_id: str,
    config: dict[str, Any],
    *,
    seed: int = 0,
    n_steps: int | None = None,
    n_nodes: int | None = None,
    n_edges: int | None = None,
    fallback_nodes: int = 50,
    fallback_edges: int = 200,
) -> dict[str, Any]:
    """Simulate one official synthetic.yaml system.

    ``n_steps`` / ``n_nodes`` / ``n_edges`` of ``None`` keep the official N / V / E.
    Systems whose config points at an external network file (KUR) fall back to an
    ER graph of ``fallback_nodes`` / ``fallback_edges`` and are flagged with
    ``used_er_fallback``.
    """
    install_nd2_path()
    from ND2.GDExpr import GDExpr

    rng = np.random.default_rng(int(seed))
    # Keep numpy.random.seed for official initialize strings that call np.random.*.
    np.random.seed(int(seed))
    network = dict(config.get("network") or {})
    if network.get("use"):
        V = int(n_nodes or fallback_nodes)
        E = int(n_edges or fallback_edges)
        directed = False
        dag = False
    else:
        V = int(n_nodes or network["V"])
        E = int(n_edges or network["E"])
        directed = bool(network.get("direction", False))
        dag = bool(network.get("DAG", False))
    A = er_adjacency(V, E, directed=directed, dag=dag, rng=rng)
    G = np.stack(np.nonzero(A), axis=-1)
    E = int(G.shape[0])
    N = int(n_steps or config["N"])
    dt = float(config["dt"])
    root_type = str(config.get("root_type", "node"))
    independent = dict(config["variables"]["independent"])
    dependent = dict(config["variables"]["dependent"])
    prefixes = {
        var: parse_to_prefix(str(cfg["GD_expr"]), root_type=str(cfg.get("type", "node")))
        for var, cfg in dependent.items()
    }
    simulation: dict[str, list[np.ndarray]] = {var: [] for var in list(independent) + list(dependent)}
    for step_idx in range(N):
        env = {"V": V, "E": E, "N": N, "dt": dt, "np": np}
        for var, cfg in independent.items():
            if step_idx == 0:
                simulation[var].append(np.asarray(eval(str(cfg["initialize"]), {"__builtins__": {}}, env), dtype=float))
            else:
                local = {name: values[-1] for name, values in simulation.items()}
                local.update(env)
                if "update" in cfg:
                    simulation[var].append(np.asarray(eval(str(cfg["update"]), {"__builtins__": {}}, local), dtype=float))
                else:
                    simulation[var].append(np.array(simulation[var][-1], copy=True))
        for var, cfg in dependent.items():
            var_dict = {name: values[-1] for name, values in simulation.items() if name in independent}
            var_dict.update({"A": A, "G": G})
            simulation[var].append(np.asarray(GDExpr.eval(prefixes[var], var_dict, [], strict=False), dtype=float))

    stacked: dict[str, np.ndarray] = {}
    for name, values in simulation.items():
        arr = np.concatenate([np.asarray(item) for item in values], axis=0)
        stacked[name] = arr
    return {
        "system_id": system_id,
        "A": A.astype(int),
        "G": G.astype(int),
        "N": N,
        "dt": dt,
        "root_type": root_type,
        "independent": stacked,
        "dependent": {name: stacked[name] for name in dependent},
        "prefixes": prefixes,
        "gd_expr": {var: str(cfg["GD_expr"]) for var, cfg in dependent.items()},
        "true_formula_raw": {var: prefix_to_string(prefix) for var, prefix in prefixes.items()},
        "network": {"V": V, "E": E, "directed": directed, "dag": dag, "used_er_fallback": bool(network.get("use"))},
        "seed": int(seed),
    }


def problem_from_simulation(
    simulated: dict[str, Any],
    *,
    target_var: str,
    input_vars: list[str],
) -> dict[str, Any]:
    Xv = {name: np.asarray(simulated["independent"][name], dtype=float) for name in input_vars}
    Y = np.asarray(simulated["dependent"][target_var], dtype=float)
    return {
        "system_id": simulated["system_id"],
        "target_var": target_var,
        "Xv": Xv,
        "Xe": {},
        "A": simulated["A"],
        "G": simulated["G"],
        "Y": Y,
        "true_prefix": list(simulated["prefixes"][target_var]),
        "true_formula_raw": simulated["true_formula_raw"][target_var],
        "root_type": simulated["root_type"],
        "vars_node": list(input_vars),
        "network": simulated["network"],
        "seed": simulated["seed"],
    }
