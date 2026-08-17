"""Layer-analysis corpus: formula-unit splits without leaking prefix variants."""

from __future__ import annotations

import hashlib
from typing import Any, Sequence

import numpy as np

from gpu_run3.formulas import formula_views, teacher_forcing_steps
from gpu_run3.synthetic import er_adjacency


def _formula_id(prefix: Sequence[str]) -> str:
    views = formula_views(prefix)
    key = views["canonical_expr"] or ",".join(prefix)
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()[:12]
    return f"F_{digest}"


def split_formula_ids(formula_ids: Sequence[str], *, seed: int, fractions: tuple[float, float, float]) -> dict[str, str]:
    ids = sorted(set(formula_ids))
    rng = np.random.default_rng(int(seed))
    perm = rng.permutation(len(ids))
    n = len(ids)
    n_train = int(round(fractions[0] * n))
    n_val = int(round(fractions[1] * n))
    if n >= 3:
        n_train = max(1, n_train)
        n_val = max(1, n_val)
        n_test = n - n_train - n_val
        if n_test < 1:
            n_test = 1
            if n_train > 1:
                n_train -= 1
            else:
                n_val -= 1
    else:
        n_train, n_val, n_test = n, 0, 0
    assignment: dict[str, str] = {}
    cuts = [n_train, n_train + n_val, n]
    labels = ["analysis_train", "analysis_validation", "analysis_test"]
    start = 0
    for label, cut in zip(labels, cuts):
        for index in perm[start:cut]:
            assignment[ids[int(index)]] = label
        start = cut
    return assignment


def default_analysis_formulas() -> list[dict[str, Any]]:
    """Small official-style prefix set used when pretrain CSVs are absent."""
    return [
        {"system_id": "KUR", "root_type": "node", "prefix": ["add", "omega", "aggr", "sin", "sub", "sour", "x", "targ", "x"], "vars_node": ["x", "omega"]},
        {"system_id": "SIS", "root_type": "node", "prefix": ["add", "mul", "neg", "delta", "x", "aggr", "mul", "sub", "1", "targ", "x", "sour", "x"], "vars_node": ["x", "delta"]},
        {"system_id": "MM", "root_type": "node", "prefix": ["add", "neg", "x", "aggr", "sour", "regular", "x", "2"], "vars_node": ["x"]},
        {"system_id": "WC", "root_type": "node", "prefix": ["add", "neg", "x", "aggr", "sour", "sigmoid", "mul", "5", "sub", "x", "1"], "vars_node": ["x"]},
        {"system_id": "GR", "root_type": "node", "prefix": ["add", "sub", "0.2", "mul", "0.9", "x", "mul", "2.0", "aggr", "sour", "regular", "div", "x", "1.5", "2"], "vars_node": ["x"]},
        {"system_id": "simple_add", "root_type": "node", "prefix": ["add", "x", "omega"], "vars_node": ["x", "omega"]},
        {"system_id": "simple_mul", "root_type": "node", "prefix": ["mul", "x", "omega"], "vars_node": ["x", "omega"]},
        {"system_id": "sin_x", "root_type": "node", "prefix": ["sin", "x"], "vars_node": ["x"]},
        {"system_id": "aggr_sour", "root_type": "node", "prefix": ["aggr", "sour", "x"], "vars_node": ["x"]},
        {"system_id": "pow2", "root_type": "node", "prefix": ["pow2", "x"], "vars_node": ["x"]},
    ]


def generate_var_dict(prefix: Sequence[str], vars_node: Sequence[str], *, seed: int, n_nodes: int = 6, n_edges: int = 10, n_time: int = 12) -> dict[str, Any]:
    rng = np.random.default_rng(int(seed))
    A = er_adjacency(n_nodes, n_edges, directed=False, dag=False, rng=rng)
    G = np.stack(np.nonzero(A), axis=-1)
    Xv = {name: rng.uniform(-1.0, 1.0, size=(n_time, n_nodes)) for name in vars_node}
    try:
        from gpu_run3_runtime import install_nd2_path

        install_nd2_path()
        from ND2.GDExpr import GDExpr

        var_dict = {"A": A, "G": G, **Xv}
        Y = np.asarray(GDExpr.eval(list(prefix), var_dict, [], strict=False), dtype=float)
        if Y.ndim == 1:
            Y = np.broadcast_to(Y, (n_time, n_nodes)).copy()
        if not np.isfinite(Y).all():
            Y = rng.normal(size=(n_time, n_nodes))
    except Exception:
        Y = rng.normal(size=(n_time, n_nodes))
    return {"A": A, "G": G, "Xv": Xv, "Xe": {}, "Y": Y}


def build_analysis_corpus(
    *,
    seed: int,
    fractions: tuple[float, float, float] = (0.6, 0.2, 0.2),
    n_nodes: int = 6,
    n_edges: int = 10,
    n_time: int = 12,
    formulas: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    formulas = formulas or default_analysis_formulas()
    formula_ids = []
    items = []
    for row in formulas:
        prefix = list(row["prefix"])
        fid = _formula_id(prefix)
        formula_ids.append(fid)
        items.append({**row, "formula_id": fid, "views": formula_views(prefix)})
    assignment = split_formula_ids(formula_ids, seed=seed, fractions=fractions)
    records = []
    for index, item in enumerate(items):
        split = assignment[item["formula_id"]]
        data = generate_var_dict(
            item["prefix"],
            item["vars_node"],
            seed=seed * 1000 + index,
            n_nodes=n_nodes,
            n_edges=n_edges,
            n_time=n_time,
        )
        steps = teacher_forcing_steps(item["prefix"], item.get("root_type", "node"))
        records.append(
            {
                "problem_id": f"{item['formula_id']}_{index:03d}",
                "formula_id": item["formula_id"],
                "system_id": item["system_id"],
                "split": split,
                "root_type": item.get("root_type", "node"),
                "prefix": item["prefix"],
                "vars_node": item["vars_node"],
                "teacher_forcing": steps,
                **data,
                **item["views"],
            }
        )
    return {
        "seed": int(seed),
        "assignment": assignment,
        "records": records,
        "n_formulas": len(set(formula_ids)),
        "n_records": len(records),
        "split_counts": {
            name: sum(1 for row in records if row["split"] == name)
            for name in ("analysis_train", "analysis_validation", "analysis_test")
        },
    }


def select_fixed_panel(records: list[dict[str, Any]], *, split: str, n: int) -> list[dict[str, Any]]:
    selected = [row for row in records if row["split"] == split]
    selected.sort(key=lambda row: row["problem_id"])
    return selected[:n]
