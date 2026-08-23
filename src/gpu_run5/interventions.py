"""Failure-aware activation-intervention helpers for GPU_RUN5 Phase 5.

The functions in this module deliberately contain no experiment I/O.  Phase
scripts can therefore record the raw paired cells and apply the same fixed
selection and ranking rules when resuming or auditing a run.
"""

from __future__ import annotations

from contextlib import contextmanager
import math
from statistics import median
from typing import Any, Iterator, Mapping, Sequence

import numpy as np
import torch
from torch import nn

from gpu_run4.architecture import resolve_layer_module


DEFAULT_INTERPOLATION_ALPHAS = (1.0, 0.75, 0.5, 0.25)
DEFAULT_CE_TIE_TOLERANCE = 1e-6
CAUSAL_SCORE_KEYS = (
    "component_exact_loss",
    "failure_aware_ted_increase",
    "component_valid_loss",
)
DIAGNOSTIC_EFFECT_KEYS = ("generalization_r2_loss",)


def _activation_tensor(output: Any) -> torch.Tensor:
    value = output[0] if isinstance(output, tuple) else output
    if not isinstance(value, torch.Tensor):
        raise TypeError(f"expected tensor activation, got {type(value)!r}")
    return value


def make_post_block_mean_hook(
    mean_activation: torch.Tensor | np.ndarray | Sequence[float],
    *,
    alpha: float,
):
    """Build a post-block hook implementing ``(1-alpha)h + alpha*mean``.

    The corpus mean is normalized to ``[1, 1, hidden]`` and broadcast over
    batch and position.  If a module returns a tuple, only its activation is
    changed; attention weights or other tuple-tail metadata are preserved.
    """
    strength = float(alpha)
    if not math.isfinite(strength) or not 0.0 <= strength <= 1.0:
        raise ValueError(f"alpha must be finite and in [0, 1], got {alpha!r}")
    stored_mean = torch.as_tensor(mean_activation).detach()
    if stored_mean.ndim == 1:
        stored_mean = stored_mean.reshape(1, 1, -1)
    elif stored_mean.ndim == 2 and stored_mean.shape[0] == 1:
        stored_mean = stored_mean.reshape(1, 1, -1)
    elif stored_mean.ndim != 3 or tuple(stored_mean.shape[:2]) != (1, 1):
        raise ValueError(
            "mean activation must have shape [hidden], [1, hidden], or [1, 1, hidden]"
        )

    def hook(_module: nn.Module, _inputs: Any, output: Any) -> Any:
        hidden = _activation_tensor(output)
        if hidden.ndim != 3:
            raise ValueError(f"post-block activation must be rank 3, got {tuple(hidden.shape)}")
        if hidden.shape[-1] != stored_mean.shape[-1]:
            raise ValueError(
                "hidden size does not match corpus mean: "
                f"{hidden.shape[-1]} != {stored_mean.shape[-1]}"
            )
        if strength == 0.0:
            replaced = hidden
        else:
            target = stored_mean.to(device=hidden.device, dtype=hidden.dtype)
            replaced = target.expand_as(hidden) if strength == 1.0 else torch.lerp(hidden, target, strength)
        if isinstance(output, tuple):
            return (replaced, *output[1:])
        return replaced

    return hook


@contextmanager
def post_block_mean_intervention(
    model: Any,
    layer_name: str,
    mean_activation: torch.Tensor | np.ndarray | Sequence[float],
    *,
    alpha: float,
) -> Iterator[None]:
    """Apply mean replacement/interpolation to one ranking block's output."""
    module = resolve_layer_module(model, layer_name)
    handle = module.register_forward_hook(
        make_post_block_mean_hook(mean_activation, alpha=alpha)
    )
    try:
        yield
    finally:
        handle.remove()


def _finite_median(value: float | Sequence[float]) -> float:
    if isinstance(value, (str, bytes)) or np.isscalar(value):
        return float(value)
    values = [float(item) for item in value]
    if not values or not all(math.isfinite(item) for item in values):
        return float("nan")
    return float(median(values))


def _tolerance_groups(values: Mapping[str, float], tolerance: float) -> list[list[str]]:
    """Group sorted finite values using a fixed, non-chaining anchor rule."""
    ordered = sorted(values.items(), key=lambda item: (item[1], item[0]))
    groups: list[list[str]] = []
    anchors: list[float] = []
    for name, value in ordered:
        if not groups or abs(value - anchors[-1]) > tolerance:
            groups.append([name])
            anchors.append(value)
        else:
            groups[-1].append(name)
    return groups


def select_interpolation_strength(
    ce_by_alpha: Mapping[float | str, Mapping[str, float | Sequence[float]]],
    *,
    baseline_median_ce: float,
    vocab_size: int,
    alphas: Sequence[float] = DEFAULT_INTERPOLATION_ALPHAS,
    tie_tolerance: float = DEFAULT_CE_TIE_TOLERANCE,
    min_tie_groups: int = 8,
    expected_layer_count: int = 16,
    range_relative_to_baseline: float = 0.01,
    range_in_tolerances: float = 10.0,
) -> dict[str, Any]:
    """Choose the first admissible interpolation strength in fixed strong-first order.

    A candidate is admissible only if every layer CE is finite and below the
    uniform-token CE, enough layer groups remain distinguishable, and its
    across-layer CE range clears the preregistered baseline-relative floor.
    """
    baseline = float(baseline_median_ce)
    tolerance = float(tie_tolerance)
    if not math.isfinite(baseline):
        raise ValueError("baseline_median_ce must be finite")
    if int(vocab_size) <= 1:
        raise ValueError("vocab_size must be greater than one")
    if tolerance < 0.0 or not math.isfinite(tolerance):
        raise ValueError("tie_tolerance must be finite and non-negative")
    if int(min_tie_groups) < 1:
        raise ValueError("min_tie_groups must be positive")
    if int(expected_layer_count) < int(min_tie_groups):
        raise ValueError("expected_layer_count must be at least min_tie_groups")

    normalized_ce: dict[float, Mapping[str, float | Sequence[float]]] = {}
    for key, value in ce_by_alpha.items():
        numeric_key = float(key)
        if numeric_key in normalized_ce:
            raise ValueError(f"duplicate interpolation strength after normalization: {numeric_key}")
        normalized_ce[numeric_key] = value

    random_ce = math.log(int(vocab_size))
    relative = float(range_relative_to_baseline)
    tolerance_multiple = float(range_in_tolerances)
    if relative < 0.0 or tolerance_multiple < 0.0:
        raise ValueError("range thresholds must be non-negative")
    required_range = max(tolerance_multiple * tolerance, relative * baseline)
    diagnostics: list[dict[str, Any]] = []
    selected: float | None = None
    for alpha in (float(value) for value in alphas):
        raw = normalized_ce.get(alpha)
        medians = {str(layer): _finite_median(value) for layer, value in (raw or {}).items()}
        layer_count_ok = len(medians) == int(expected_layer_count)
        all_finite = bool(medians) and all(math.isfinite(value) for value in medians.values())
        below_random = all_finite and all(value < random_ce for value in medians.values())
        groups = _tolerance_groups(medians, tolerance) if all_finite else []
        ce_range = float(max(medians.values()) - min(medians.values())) if all_finite else None
        admissible = bool(
            all_finite
            and layer_count_ok
            and below_random
            and len(groups) >= int(min_tie_groups)
            and ce_range is not None
            and ce_range >= required_range
        )
        diagnostics.append(
            {
                "alpha": alpha,
                "all_finite": all_finite,
                "layer_count": len(medians),
                "expected_layer_count": int(expected_layer_count),
                "layer_count_ok": layer_count_ok,
                "all_layer_medians_below_log_vocab": below_random,
                "log_vocab": random_ce,
                "tie_group_count": len(groups),
                "tie_groups": groups,
                "ce_range": ce_range,
                "required_ce_range": required_range,
                "admissible": admissible,
            }
        )
        if selected is None and admissible:
            selected = alpha
    return {
        "selected_alpha": selected,
        "admissible": selected is not None,
        "selection_order": [float(value) for value in alphas],
        "tie_tolerance": tolerance,
        "min_tie_groups": int(min_tie_groups),
        "expected_layer_count": int(expected_layer_count),
        "range_relative_to_baseline": relative,
        "range_in_tolerances": tolerance_multiple,
        "diagnostics": diagnostics,
    }


def check_mean_alpha_one_equivalence(
    mean_ce: Mapping[str, float],
    alpha_one_ce: Mapping[str, float],
    *,
    tolerance: float = DEFAULT_CE_TIE_TOLERANCE,
) -> dict[str, Any]:
    """Check the preregistered mean-replacement versus alpha=1 control."""
    names = sorted(set(mean_ce) | set(alpha_one_ce))
    missing = [name for name in names if name not in mean_ce or name not in alpha_one_ce]
    differences = {
        name: abs(float(mean_ce[name]) - float(alpha_one_ce[name]))
        for name in names
        if name not in missing
    }
    all_finite = bool(differences) and all(math.isfinite(value) for value in differences.values())
    max_difference = max(differences.values()) if differences and all_finite else None
    equivalent = bool(
        not missing
        and all_finite
        and max_difference is not None
        and max_difference <= float(tolerance)
    )
    return {
        "equivalent": equivalent,
        "tolerance": float(tolerance),
        "n_compared": len(differences),
        "missing_layers": missing,
        "all_finite": all_finite,
        "max_abs_difference": max_difference,
        "absolute_differences": differences,
    }


def failure_aware_metric(
    value: Any,
    *,
    valid: bool,
    failure_value: float,
) -> float:
    """Return a finite metric or its explicit failure penalty."""
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        numeric = float("nan")
    return numeric if bool(valid) and math.isfinite(numeric) else float(failure_value)


def paired_layer_effects(
    pairs: Sequence[Mapping[str, Any]],
    *,
    layer_key: str = "layer",
    failed_ted: float = 1.0,
    failed_r2: float = -1.0,
) -> dict[str, dict[str, Any]]:
    """Aggregate paired baseline/intervention formula damage by layer.

    Expected fields are ``baseline_*`` and ``intervention_*`` for ``ce``,
    ``exact``, ``ted``, ``valid``, and ``gen_r2``.  Invalid TED and R2 values
    receive explicit penalties, so failed decodes cannot disappear from the
    median.  CE must be finite because teacher forcing has no decode fallback.
    """
    grouped: dict[str, list[dict[str, float]]] = {}
    for pair in pairs:
        layer = str(pair[layer_key])
        baseline_ce = float(pair["baseline_ce"])
        intervention_ce = float(pair["intervention_ce"])
        if not math.isfinite(baseline_ce) or not math.isfinite(intervention_ce):
            raise ValueError(f"non-finite paired CE for layer {layer}")
        baseline_valid = bool(pair.get("baseline_valid", False))
        intervention_valid = bool(pair.get("intervention_valid", False))
        baseline_ted = failure_aware_metric(
            pair.get("baseline_ted"), valid=baseline_valid, failure_value=failed_ted
        )
        intervention_ted = failure_aware_metric(
            pair.get("intervention_ted"), valid=intervention_valid, failure_value=failed_ted
        )
        baseline_r2 = failure_aware_metric(
            pair.get("baseline_gen_r2"), valid=baseline_valid, failure_value=failed_r2
        )
        intervention_r2 = failure_aware_metric(
            pair.get("intervention_gen_r2"), valid=intervention_valid, failure_value=failed_r2
        )
        grouped.setdefault(layer, []).append(
            {
                "damage_ce": intervention_ce - baseline_ce,
                "component_exact_loss": (
                    float(pair.get("baseline_exact", 0.0)) if baseline_valid else 0.0
                ) - (
                    float(pair.get("intervention_exact", 0.0)) if intervention_valid else 0.0
                ),
                "failure_aware_ted_increase": intervention_ted - baseline_ted,
                "component_valid_loss": float(baseline_valid) - float(intervention_valid),
                "generalization_r2_loss": baseline_r2 - intervention_r2,
            }
        )

    result: dict[str, dict[str, Any]] = {}
    for layer, rows in sorted(grouped.items()):
        result[layer] = {
            key: float(median(row[key] for row in rows))
            for key in ("damage_ce", *CAUSAL_SCORE_KEYS, *DIAGNOSTIC_EFFECT_KEYS)
        }
        result[layer]["n_pairs"] = len(rows)
    return result


def p5_damage_spearman(
    layer_effects: Mapping[str, Mapping[str, Any]],
    *,
    threshold: float = 0.5,
    expected_layer_count: int = 16,
) -> dict[str, Any]:
    """Evaluate P5 using average-rank Spearman on CE and TED damage.

    Higher values mean more damage for both measures.  Missing/non-finite
    layers are excluded, while fewer than two layers or either constant vector
    makes the result indeterminate and never supportive.
    """
    layers = sorted(
        layer
        for layer, values in layer_effects.items()
        if math.isfinite(float(values.get("damage_ce", float("nan"))))
        and math.isfinite(float(values.get("failure_aware_ted_increase", float("nan"))))
    )
    ce = np.asarray([float(layer_effects[layer]["damage_ce"]) for layer in layers])
    ted = np.asarray(
        [float(layer_effects[layer]["failure_aware_ted_increase"]) for layer in layers]
    )
    reason = None
    rho: float | None = None
    p_value: float | None = None
    if len(layers) != int(expected_layer_count):
        reason = "missing_or_non_finite_layer_damage"
    elif np.all(ce == ce[0]) or np.all(ted == ted[0]):
        reason = "constant_damage_vector"
    else:
        from scipy.stats import spearmanr

        result = spearmanr(ce, ted, alternative="two-sided")
        rho = float(result.statistic)
        p_value = float(result.pvalue)
        if not math.isfinite(rho):
            rho = None
            p_value = None
            reason = "non_finite_correlation"
    determinate = rho is not None
    return {
        "rho": rho,
        "p_value_two_sided": p_value,
        "threshold": float(threshold),
        "supported": bool(determinate and rho <= float(threshold)),
        "determinate": determinate,
        "reason": reason,
        "n_layers": len(layers),
        "expected_layer_count": int(expected_layer_count),
        "layers": layers,
        "orientation": "higher_is_more_damage_for_both",
    }


def rank_causal_formula_damage(
    layer_effects: Mapping[str, Mapping[str, Any]],
    *,
    quantization_digits: int = 12,
) -> dict[str, Any]:
    """Lexicographically rank causal formula damage, with fixed-name ties.

    Each score component is rounded to 12 decimals before sorting and assigning
    tie groups.  Larger loss/damage is ranked first.  Non-finite vectors are
    retained after all finite layers and never share a finite tie group.
    """
    digits = int(quantization_digits)
    prepared: list[tuple[str, tuple[float, ...] | None]] = []
    for layer, values in layer_effects.items():
        raw = tuple(float(values.get(key, float("nan"))) for key in CAUSAL_SCORE_KEYS)
        vector = tuple(round(value, digits) for value in raw) if all(map(math.isfinite, raw)) else None
        prepared.append((str(layer), vector))
    prepared.sort(
        key=lambda item: (
            item[1] is None,
            tuple(-value for value in item[1]) if item[1] is not None else (),
            item[0],
        )
    )

    rows: list[dict[str, Any]] = []
    previous: tuple[float, ...] | None | object = object()
    group = 0
    for rank, (layer, vector) in enumerate(prepared, start=1):
        # All non-finite vectors are auditably grouped together; layer name is
        # still the deterministic order within that last group.
        if rank == 1 or vector != previous:
            group += 1
        rows.append(
            {
                "layer": layer,
                "rank": rank,
                "tie_group": group,
                "quantized_score_vector": list(vector) if vector is not None else None,
                **{
                    key: layer_effects[layer].get(key)
                    for key in (*CAUSAL_SCORE_KEYS, *DIAGNOSTIC_EFFECT_KEYS)
                },
            }
        )
        previous = vector
    return {
        "ranking": [row["layer"] for row in rows],
        "rows": rows,
        "score_order": list(CAUSAL_SCORE_KEYS),
        "diagnostic_not_used_for_ranking": list(DIAGNOSTIC_EFFECT_KEYS),
        "higher_is_more_damage": True,
        "quantization_digits": digits,
        "tie_group_count": group,
    }
