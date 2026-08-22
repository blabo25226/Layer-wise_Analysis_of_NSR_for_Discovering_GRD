"""Layer-analysis corpus: formula-unit splits without leaking prefix variants.

Formulas and data are drawn from the official ND2 pretraining generators
(``GDExpr.random_fill_expr`` for the formula grammar, ``ND2.dataset.Generator``
for network structure and node/edge activities), so the corpus stays inside the
official symbol vocabulary (``v1..v5`` / ``e1..e5`` / ``<C>`` / constants).
Hand-written prefixes with out-of-vocabulary tokens cannot be decomposed by
``GDExpr.decompose`` and silently produce zero teacher-forcing examples.
"""

from __future__ import annotations

import hashlib
from typing import Any, Sequence

import numpy as np

from gpu_run3.formulas import formula_views, teacher_forcing_steps
from gpu_run3.synthetic import er_adjacency  # re-exported for callers

__all__ = [
    "build_analysis_corpus",
    "er_adjacency",
    "sample_official_prefixes",
    "select_fixed_panel",
    "split_formula_ids",
]

NODE_VARS = ("v1", "v2", "v3", "v4", "v5")
EDGE_VARS = ("e1", "e2", "e3", "e4", "e5")


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


def reindex_prefix_variables(prefix: Sequence[str]) -> list[str]:
    """Rename variables to contiguous v1..vk / e1..ek in first-appearance order.

    ``NDformer.set_data`` maps the i-th key of ``Xv`` to ``v{i}``; keeping the
    prefix contiguous makes that mapping the identity and keeps saved formulas
    readable.
    """
    node_seen: list[str] = []
    edge_seen: list[str] = []
    for token in prefix:
        if token in NODE_VARS and token not in node_seen:
            node_seen.append(token)
        elif token in EDGE_VARS and token not in edge_seen:
            edge_seen.append(token)
    mapping = {old: f"v{i}" for i, old in enumerate(node_seen, 1)}
    mapping.update({old: f"e{i}" for i, old in enumerate(edge_seen, 1)})
    return [mapping.get(token, token) for token in prefix]


def sample_official_prefixes(
    n_formulas: int,
    *,
    seed: int,
    root_type: str = "node",
    length_range: tuple[int, int] = (5, 16),
    max_attempts_factor: int = 20,
) -> list[dict[str, Any]]:
    """Sample formulas from the official ND2 grammar (``GDExpr.random_fill_expr``)."""
    from gpu_run3_runtime import install_nd2_path

    install_nd2_path()
    from ND2.GDExpr import GDExpr

    rng = np.random.default_rng(int(seed))
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    attempts = 0
    max_attempts = max(int(n_formulas) * int(max_attempts_factor), 50)
    while len(out) < int(n_formulas) and attempts < max_attempts:
        attempts += 1
        total_len = int(rng.integers(length_range[0], length_range[1] + 1))
        # random_fill_expr uses the global numpy RNG internally.
        np.random.seed(int(rng.integers(0, 2**31 - 1)))
        try:
            prefix = GDExpr.random_fill_expr(total_len, [root_type])
        except Exception:
            continue
        prefix = reindex_prefix_variables([str(token) for token in prefix])
        if not any(token in NODE_VARS or token in EDGE_VARS for token in prefix):
            continue  # constant-only formulas carry no dynamics
        views = formula_views(prefix)
        if not views["valid"]:
            continue
        key = views["canonical_expr"]
        if key in seen:
            continue
        seen.add(key)
        out.append(
            {
                "system_id": f"pretrain_{len(out):04d}",
                "root_type": root_type,
                "prefix": prefix,
                "vars_node": [v for v in NODE_VARS if v in prefix],
                "vars_edge": [e for e in EDGE_VARS if e in prefix],
                "sample_attempts": attempts,
            }
        )
    return out


def generate_official_data(
    prefix: Sequence[str],
    *,
    seed: int,
    root_type: str = "node",
    n_nodes: int | None = None,
    n_edges: int | None = None,
    n_time: int | None = None,
    min_finite_rate: float = 0.9,
    max_abs: float = 1e6,
    max_attempts: int = 5,
) -> dict[str, Any] | None:
    """Generate network + activities with the official ND2 ``Generator``.

    Returns ``None`` (rather than silently substituting random noise) when the
    formula cannot be evaluated to a usable target on any attempt.
    """
    from gpu_run3_runtime import install_nd2_path

    install_nd2_path()
    from ND2.dataset.generator import Generator

    tokens = [str(t) for t in prefix]
    kwargs: dict[str, Any] = {}
    if n_nodes is not None:
        kwargs.update(min_node_num=int(n_nodes), max_node_num=int(n_nodes) + 1)
    if n_edges is not None:
        kwargs.update(min_edge_num=int(n_edges), max_edge_num=int(n_edges) + 1)
    if n_time is not None:
        kwargs.update(min_data_num=int(n_time), max_data_num=int(n_time))
    generator = Generator(**kwargs)
    for attempt in range(int(max_attempts)):
        np.random.seed((int(seed) * 7919 + attempt * 104729) % (2**31 - 1))
        try:
            var_dict = generator.generate_data(tokens, root_type)
        except Exception:
            continue
        out = np.asarray(var_dict.get("out"), dtype=float)
        if out.ndim != 2 or out.size == 0:
            continue
        finite = np.isfinite(out)
        if finite.mean() < float(min_finite_rate):
            continue
        if np.abs(out[finite]).max(initial=0.0) > float(max_abs):
            continue
        if float(np.nanstd(out[finite])) <= 0.0:
            continue  # constant target carries no signal
        A = np.asarray(var_dict["A"]).astype(int)
        G = np.asarray(var_dict["G"]).astype(int)
        Xv = {name: np.asarray(var_dict[name], dtype=float) for name in NODE_VARS if name in var_dict}
        Xe = {name: np.asarray(var_dict[name], dtype=float) for name in EDGE_VARS if name in var_dict}
        return {
            "A": A,
            "G": G,
            "Xv": Xv,
            "Xe": Xe,
            "Y": out,
            "n_nodes": int(A.shape[0]),
            "n_edges": int(G.shape[0]),
            "n_time": int(out.shape[0]),
            "finite_rate": float(finite.mean()),
            "data_attempts": attempt + 1,
        }
    return None


def build_analysis_corpus(
    *,
    seed: int,
    fractions: tuple[float, float, float] = (0.6, 0.2, 0.2),
    n_formulas: int = 12,
    n_nodes: int | None = None,
    n_edges: int | None = None,
    n_time: int | None = None,
    length_range: tuple[int, int] = (5, 16),
    root_type: str = "node",
    formulas: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build the ``analysis_train`` / ``analysis_validation`` / ``analysis_test`` corpus.

    Splits are assigned per canonical formula, so network / activity / prefix
    variants of one formula never straddle two splits.
    """
    items = formulas or sample_official_prefixes(
        n_formulas,
        seed=seed,
        root_type=root_type,
        length_range=length_range,
    )
    formula_ids = []
    prepared = []
    for row in items:
        prefix = list(row["prefix"])
        fid = _formula_id(prefix)
        formula_ids.append(fid)
        prepared.append({**row, "formula_id": fid, "views": formula_views(prefix)})
    assignment = split_formula_ids(formula_ids, seed=seed, fractions=fractions)
    records = []
    failures = []
    for index, item in enumerate(prepared):
        data = generate_official_data(
            item["prefix"],
            seed=int(seed) * 1000 + index,
            root_type=item.get("root_type", root_type),
            n_nodes=n_nodes,
            n_edges=n_edges,
            n_time=n_time,
        )
        if data is None:
            failures.append(
                {
                    "formula_id": item["formula_id"],
                    "prefix": item["prefix"],
                    "failure_reason": "NaN",
                    "stage": "data_generation",
                }
            )
            continue
        steps = teacher_forcing_steps(item["prefix"], item.get("root_type", root_type))
        usable = [step for step in steps if step.get("target")]
        if not usable:
            failures.append(
                {
                    "formula_id": item["formula_id"],
                    "prefix": item["prefix"],
                    "failure_reason": steps[-1].get("failure_reason") if steps else "InvalidPrefix",
                    "stage": "teacher_forcing",
                }
            )
            continue
        records.append(
            {
                "problem_id": f"{item['formula_id']}_{index:03d}",
                "formula_id": item["formula_id"],
                "system_id": item["system_id"],
                "split": assignment[item["formula_id"]],
                "root_type": item.get("root_type", root_type),
                "prefix": item["prefix"],
                "vars_node": list(data["Xv"]),
                "vars_edge": list(data["Xe"]),
                "n_teacher_forcing": len(usable),
                "teacher_forcing": steps,
                **data,
                **item["views"],
            }
        )
    return {
        "seed": int(seed),
        "assignment": assignment,
        "records": records,
        "failures": failures,
        "n_formulas_requested": int(n_formulas) if formulas is None else len(items),
        "n_formulas": len(set(row["formula_id"] for row in records)),
        "n_records": len(records),
        "n_failures": len(failures),
        "split_counts": {
            name: sum(1 for row in records if row["split"] == name)
            for name in ("analysis_train", "analysis_validation", "analysis_test")
        },
    }


def corpus_kwargs_from_budget(budget: dict[str, Any]) -> dict[str, Any]:
    """Translate a smoke/full budget block into ``build_analysis_corpus`` kwargs.

    The corpus keys are deliberately separate from the ``n_nodes`` / ``n_edges`` /
    ``simulate_steps`` keys used for the official synthetic benchmark, so bounding
    the layer-analysis corpus never silently shrinks the ND2 reproduction.
    """
    kwargs: dict[str, Any] = {"n_formulas": int(budget.get("n_formulas", 12))}
    for key, name in (("corpus_nodes", "n_nodes"), ("corpus_edges", "n_edges"), ("corpus_time", "n_time")):
        value = budget.get(key)
        if value is not None:
            kwargs[name] = int(value)
    length_range = budget.get("corpus_length_range")
    if length_range:
        kwargs["length_range"] = (int(length_range[0]), int(length_range[1]))
    return kwargs


def select_fixed_panel(records: list[dict[str, Any]], *, split: str, n: int) -> list[dict[str, Any]]:
    """Deterministic panel: split filter, ID order, prefix cut. Never success-filtered."""
    selected = [row for row in records if row["split"] == split]
    selected.sort(key=lambda row: row["problem_id"])
    return selected[: int(n)] if n and n > 0 else selected
