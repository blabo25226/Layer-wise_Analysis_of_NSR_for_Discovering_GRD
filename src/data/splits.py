"""Leakage-resistant dataset splitting helpers."""

from __future__ import annotations

from collections import defaultdict
from typing import Callable, List, Sequence, Tuple, TypeVar

import numpy as np

T = TypeVar("T")


def grouped_train_validation_split(
    items: Sequence[T],
    *,
    validation_fraction: float = 0.2,
    seed: int = 1729,
    group_key: Callable[[T], str],
) -> Tuple[List[T], List[T]]:
    """Split whole groups so related equations never cross train/validation."""
    if not 0.0 < validation_fraction < 1.0:
        raise ValueError("validation_fraction must be between 0 and 1")
    if not items:
        raise ValueError("cannot split an empty sequence")
    groups = defaultdict(list)
    for item in items:
        groups[str(group_key(item))].append(item)
    names = sorted(groups)
    if len(names) < 2:
        raise ValueError("grouped split requires at least two distinct groups")
    rng = np.random.default_rng(seed)
    shuffled = list(np.asarray(names, dtype=object)[rng.permutation(len(names))])
    n_val = min(len(names) - 1, max(1, round(len(names) * validation_fraction)))
    val_names = set(shuffled[:n_val])
    train = [item for name in names if name not in val_names for item in groups[name]]
    validation = [item for name in names if name in val_names for item in groups[name]]
    return train, validation


def split_synthetic_train_validation(
    problems: Sequence[T],
    *,
    validation_fraction: float = 0.2,
    seed: int = 1729,
) -> Tuple[List[T], List[T]]:
    """Group synthetic equations by motif before splitting."""
    return grouped_train_validation_split(
        problems,
        validation_fraction=validation_fraction,
        seed=seed,
        group_key=lambda problem: problem.spec.motif or problem.spec.family,
    )


def assign_fixed_problem_split(
    *,
    variant_index: int,
    train_indices: Sequence[int],
    validation_indices: Sequence[int],
    test_indices: Sequence[int],
) -> str:
    """Map a variant index onto a predeclared problem-level split."""
    if variant_index in set(train_indices):
        return "train"
    if variant_index in set(validation_indices):
        return "validation"
    if variant_index in set(test_indices):
        return "test"
    raise ValueError(f"variant_index {variant_index} is not in any declared split")


def structure_holdout_split(family_id: str) -> str:
    """CTC_NSR view: G01–G05 train, G06 validation, G07–G08 structure-OOD test."""
    if family_id in {"G01", "G02", "G03", "G04", "G05"}:
        return "train"
    if family_id == "G06":
        return "validation"
    if family_id in {"G07", "G08"}:
        return "test"
    raise KeyError(f"unknown GNW family for structure-holdout: {family_id}")


def assert_problem_splits_disjoint(rows: Sequence[object], *, id_attr: str = "eq_id") -> None:
    """Refuse any eq_id that appears in more than one main split."""
    seen: dict[str, str] = {}
    for row in rows:
        eq_id = str(getattr(row, id_attr, None) or row[id_attr])  # type: ignore[index]
        split = str(getattr(row, "main_split", None) or row["main_split"])  # type: ignore[index]
        previous = seen.get(eq_id)
        if previous is None:
            seen[eq_id] = split
            continue
        if previous != split:
            raise RuntimeError(
                f"eq_id {eq_id} appears in both {previous!r} and {split!r}"
            )
