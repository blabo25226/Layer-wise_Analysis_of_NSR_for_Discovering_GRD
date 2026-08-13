"""GPU_RUN2 Phase 4 ranking helpers. Pure functions; no Phase execution."""

from __future__ import annotations

from typing import Any, Iterable, Mapping, Sequence

from evaluation.layer_contribution import (
    compute_contributions,
    rank_agreement_table,
    rank_by_contribution,
)
from interpretability.interventions import intervention_delta
from training.selective_layers import build_gpu_run2_conditions


def iole_ranking(
    layer_scores: Mapping[str, float],
    candidates: Sequence[str],
) -> tuple[list[str], dict[str, float]]:
    contrib = compute_contributions(
        layer_scores, higher_is_better=False, require_full_improvement=True
    )
    ranked = [name for name, value in rank_by_contribution(contrib) if value == value]
    if not ranked:
        ranked = sorted(
            [name for name in candidates if name in layer_scores],
            key=lambda name: float(layer_scores[name]),
        )
    return ranked, dict(contrib)


def ablation_ranking(
    ablation_scores: Mapping[str, float],
    candidates: Sequence[str],
) -> list[str]:
    return sorted(candidates, key=lambda name: float(ablation_scores.get(name, float("inf"))))


def intervention_ranking(
    intervention_scores: Mapping[str, float],
    candidates: Sequence[str],
) -> list[str]:
    base = float(intervention_scores.get("pretrained", 0.0))
    return sorted(
        candidates,
        key=lambda name: intervention_delta(
            base,
            float(intervention_scores.get(name, 0.0)),
            higher_is_better=False,
        ),
        reverse=True,
    )


def phase4_agreement(
    *,
    iole: Sequence[str],
    ablation: Sequence[str],
    intervention: Sequence[str],
    probe: Sequence[str] | None = None,
    decoder_lens: Sequence[str] | None = None,
) -> dict[str, Any]:
    rankings: dict[str, Sequence[str]] = {
        "iole": list(iole),
        "ablation": list(ablation),
        "intervention": list(intervention),
    }
    if probe:
        rankings["probe"] = list(probe)
    if decoder_lens:
        rankings["decoder_lens"] = list(decoder_lens)
    return rank_agreement_table(rankings)


def phase4_conditions(
    iole_rank: Sequence[str],
    *,
    random_seed: int,
    candidate_layers: Sequence[str],
) -> dict[str, list[str] | None]:
    return build_gpu_run2_conditions(
        list(iole_rank) or list(candidate_layers),
        random_seed=int(random_seed),
        candidate_layers=list(candidate_layers),
    )


def mean_nmse_for_families(
    records: Sequence[Mapping[str, Any]],
    *,
    families: Iterable[str] | None = None,
    key: str = "nmse",
) -> float:
    import numpy as np

    allowed = None if families is None else {str(name) for name in families}
    values = []
    for row in records:
        family = str(row.get("motif") or row.get("family_id") or "")
        if allowed is not None and family not in allowed:
            continue
        value = float(row.get(key, float("inf")))
        if np.isfinite(value):
            values.append(value)
    return float(np.mean(values)) if values else float("inf")
