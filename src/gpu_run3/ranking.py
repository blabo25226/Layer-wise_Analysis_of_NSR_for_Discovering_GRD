"""Layer ranking agreement for GPU_RUN3 (validation only)."""

from __future__ import annotations

from typing import Mapping, Sequence

from evaluation.layer_contribution import rank_agreement_table, rank_correlations


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
    if not a and not b:
        return float("nan")
    return float(len(a & b) / k)


def compare_rankings(rankings: dict[str, Sequence[str]], *, k: int = 3) -> dict[str, object]:
    agreement = rank_agreement_table(rankings)
    pairwise = {}
    names = list(rankings)
    for i, left in enumerate(names):
        for right in names[i + 1 :]:
            scores_l = {name: -rank for rank, name in enumerate(rankings[left])}
            scores_r = {name: -rank for rank, name in enumerate(rankings[right])}
            corr = rank_correlations(scores_l, scores_r)
            pairwise[f"{left}_vs_{right}"] = {
                **corr,
                "topk_overlap": topk_overlap(list(rankings[left]), list(rankings[right]), k),
            }
    return {"agreement": agreement, "pairwise": pairwise, "rankings": {k: list(v) for k, v in rankings.items()}}
