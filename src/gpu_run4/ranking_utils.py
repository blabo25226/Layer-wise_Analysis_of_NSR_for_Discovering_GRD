"""Layer ranking helpers for GPU_RUN4."""

from __future__ import annotations

from typing import Mapping, Sequence


def rank_from_scores(scores: Mapping[str, float], *, higher_is_better: bool) -> list[str]:
    def key(name: str) -> tuple[int, float, str]:
        value = float(scores.get(name, float("nan")))
        if value != value:
            return (1, 0.0, name)
        return (0, -value if higher_is_better else value, name)

    return sorted(scores, key=key)


def topk_overlap(left: Sequence[str], right: Sequence[str], k: int) -> float:
    if k <= 0:
        return float("nan")
    a = set(left[:k])
    b = set(right[:k])
    return float(len(a & b) / k)
