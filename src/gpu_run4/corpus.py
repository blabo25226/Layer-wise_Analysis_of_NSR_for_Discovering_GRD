"""Independent synthetic corpus from the official ODEFormer generator."""

from __future__ import annotations

import hashlib
from typing import Any

import numpy as np

from gpu_run4.formulas import formula_views
from gpu_run4_runtime import install_odeformer_path, seed_everything


def _formula_key(sample: dict[str, Any]) -> str:
    tree = sample.get("tree")
    if tree is not None and hasattr(tree, "infix"):
        text = str(tree.infix())
    else:
        text = str(sample.get("tree_encoded") or "")
    views = formula_views(text)
    skeleton = views.get("true_formula_skeleton") or text
    return hashlib.sha256(skeleton.encode("utf-8")).hexdigest()


def generate_one(env: Any, *, train: bool = True) -> dict[str, Any] | None:
    from gpu_run4.ted import TedTimeout, time_limit

    try:
        with time_limit(8.0):
            sample, _errors = env.gen_expr(train)
    except TedTimeout:
        return None
    except Exception:
        return None
    if not sample:
        return None
    times = np.asarray(sample["times"], dtype=float)
    traj = np.asarray(sample["trajectory"], dtype=float)
    if times.ndim != 1 or traj.ndim != 2 or not np.isfinite(traj).all():
        return None
    tree = sample.get("tree")
    infix = str(tree.infix()) if tree is not None and hasattr(tree, "infix") else ""
    prefix = []
    if tree is not None and hasattr(tree, "prefix"):
        try:
            prefix = list(tree.prefix())
        except Exception:
            prefix = []
    views = formula_views(infix)
    encoded = sample.get("tree_encoded")
    return {
        "times": times,
        "trajectory": traj,
        "infix": infix,
        "prefix": prefix if prefix else encoded,
        "tree_encoded": encoded,
        "skeleton_tree_encoded": sample.get("skeleton_tree_encoded"),
        "dimension": int(traj.shape[1]),
        "n_points": int(traj.shape[0]),
        "canonical": views.get("true_formula_canonical"),
        "skeleton": views.get("true_formula_skeleton"),
        "complexity": views.get("complexity"),
        "valid": bool(views.get("valid")),
        "formula_key": _formula_key(sample),
        "infos": dict(sample.get("infos") or {}),
    }


def build_analysis_corpus(
    model: Any,
    *,
    n_train: int,
    n_validation: int,
    n_test: int,
    seed: int,
    max_attempts: int | None = None,
) -> dict[str, Any]:
    """Formula-level split with skeleton-leakage audit. ODEBench is not used."""
    install_odeformer_path()
    seed_everything(seed)
    env = getattr(model, "env", None)
    if env is None:
        raise RuntimeError("OfficialConfigMismatch: loaded ODEFormer has no env generator")
    env.rng = np.random.RandomState(int(seed))
    needed = n_train + n_validation + n_test
    attempts = int(max_attempts or max(needed * 20, needed + 10))
    unique: dict[str, dict[str, Any]] = {}
    failures = 0
    for _ in range(attempts):
        if len(unique) >= needed:
            break
        row = generate_one(env, train=True)
        if row is None or not row["valid"]:
            failures += 1
            continue
        unique.setdefault(row["formula_key"], row)
    rows = list(unique.values())
    if len(rows) < needed:
        raise RuntimeError(
            f"OfficialConfigMismatch: generated {len(rows)} unique formulas, need {needed} (failures={failures})"
        )
    rng = np.random.default_rng(int(seed))
    rng.shuffle(rows)
    train = rows[:n_train]
    validation = rows[n_train : n_train + n_validation]
    test = rows[n_train + n_validation : n_train + n_validation + n_test]
    keys = {
        "analysis_train": {row["formula_key"] for row in train},
        "analysis_validation": {row["formula_key"] for row in validation},
        "analysis_test": {row["formula_key"] for row in test},
    }
    leakage = {
        "train_val": sorted(keys["analysis_train"] & keys["analysis_validation"]),
        "train_test": sorted(keys["analysis_train"] & keys["analysis_test"]),
        "val_test": sorted(keys["analysis_validation"] & keys["analysis_test"]),
    }
    for split, items in (
        ("analysis_train", train),
        ("analysis_validation", validation),
        ("analysis_test", test),
    ):
        for index, row in enumerate(items):
            row["split"] = split
            row["problem_id"] = f"{split}_{index}"
    fingerprint = hashlib.sha256(
        "".join(row["formula_key"] for row in train + validation + test).encode("utf-8")
    ).hexdigest()
    return {
        "records": train + validation + test,
        "n_train": len(train),
        "n_validation": len(validation),
        "n_test": len(test),
        "n_failures": failures,
        "skeleton_leakage": {k: len(v) for k, v in leakage.items()},
        "leakage_keys": leakage,
        "fingerprint": fingerprint,
        "seed": int(seed),
    }


def select_fixed_panel(records: list[dict[str, Any]], n: int, *, seed: int) -> list[dict[str, Any]]:
    """Deterministic panel: sort by problem_id, then take n. No cherry-picking."""
    ordered = sorted(records, key=lambda row: str(row.get("problem_id")))
    rng = np.random.default_rng(int(seed))
    if n >= len(ordered):
        return list(ordered)
    indices = np.sort(rng.choice(len(ordered), int(n), replace=False))
    return [ordered[int(i)] for i in indices]
