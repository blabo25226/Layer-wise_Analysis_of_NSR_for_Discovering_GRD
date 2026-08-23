"""Focused tests for GPU_RUN5 Phase 5 intervention helpers."""

from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest
import torch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from gpu_run5.interventions import (  # noqa: E402
    check_mean_alpha_one_equivalence,
    make_post_block_mean_hook,
    p5_damage_spearman,
    paired_layer_effects,
    rank_causal_formula_damage,
    select_interpolation_strength,
)


def test_post_block_hook_broadcasts_mean_and_preserves_tuple_tail():
    hidden = torch.arange(24, dtype=torch.float32).reshape(2, 3, 4)
    tail = {"attention": "untouched"}
    mean = torch.tensor([10.0, 20.0, 30.0, 40.0])
    output = make_post_block_mean_hook(mean, alpha=0.5)(None, (), (hidden, tail))
    expected = 0.5 * hidden + 0.5 * mean.reshape(1, 1, 4)
    assert torch.equal(output[0], expected)
    assert output[1] is tail
    assert output[0].shape == hidden.shape

    identity = make_post_block_mean_hook(mean, alpha=0.0)(None, (), hidden)
    assert identity is hidden

    full = make_post_block_mean_hook(mean, alpha=1.0)(None, (), hidden)
    full.mul_(torch.tensor([[[1.0], [0.0], [1.0]], [[0.0], [1.0], [0.0]]]))
    assert torch.equal(full[0, 0], mean)
    assert torch.equal(full[0, 1], torch.zeros_like(mean))


def _ce_grid(alpha_one_offset: float = 0.0):
    return {
        1.0: {f"decoder_{index}": 1.0 + index * 0.02 + alpha_one_offset for index in range(16)},
        0.75: {f"decoder_{index}": 1.0 for index in range(16)},
        0.5: {f"decoder_{index}": 1.0 + index * 0.01 for index in range(16)},
        0.25: {f"decoder_{index}": 1.0 + index * 0.005 for index in range(16)},
    }


def test_strength_selector_uses_fixed_order_and_reports_failures():
    selected = select_interpolation_strength(
        _ce_grid(), baseline_median_ce=2.0, vocab_size=100
    )
    assert selected["selected_alpha"] == 1.0
    assert selected["diagnostics"][0]["tie_group_count"] == 16

    grid = _ce_grid()
    grid[1.0]["decoder_0"] = float("nan")
    selected = select_interpolation_strength(grid, baseline_median_ce=2.0, vocab_size=100)
    assert selected["selected_alpha"] == 0.5
    assert selected["diagnostics"][0]["all_finite"] is False
    assert selected["diagnostics"][1]["tie_group_count"] == 1

    flat = {alpha: {f"layer_{index}": 1.0 for index in range(16)} for alpha in (1, .75, .5, .25)}
    rejected = select_interpolation_strength(flat, baseline_median_ce=2.0, vocab_size=100)
    assert rejected["selected_alpha"] is None
    assert rejected["admissible"] is False


def test_strength_selector_rejects_random_ce_and_mean_equivalence_is_paired():
    grid = _ce_grid()
    grid[1.0]["decoder_15"] = math.log(100)
    result = select_interpolation_strength(grid, baseline_median_ce=2.0, vocab_size=100)
    assert result["selected_alpha"] == 0.5
    assert result["diagnostics"][0]["all_layer_medians_below_log_vocab"] is False

    equivalent = check_mean_alpha_one_equivalence(
        {"encoder_0": 1.0, "decoder_0": 2.0},
        {"encoder_0": 1.0 + 5e-7, "decoder_0": 2.0},
    )
    assert equivalent["equivalent"] is True
    assert equivalent["max_abs_difference"] == pytest.approx(5e-7)
    assert not check_mean_alpha_one_equivalence(
        {"encoder_0": 1.0}, {"encoder_0": 1.0 + 2e-6}
    )["equivalent"]


def test_paired_effect_damage_signs_and_failure_penalties():
    rows = [
        {
            "layer": "encoder_0",
            "baseline_ce": 1.0,
            "intervention_ce": 1.4,
            "baseline_exact": 1,
            "intervention_exact": 0,
            "baseline_ted": 0.0,
            "intervention_ted": None,
            "baseline_valid": True,
            "intervention_valid": False,
            "baseline_gen_r2": 0.8,
            "intervention_gen_r2": None,
        },
        {
            "layer": "encoder_0",
            "baseline_ce": 1.2,
            "intervention_ce": 1.4,
            "baseline_exact": 0,
            "intervention_exact": 0,
            "baseline_ted": 0.4,
            "intervention_ted": 0.6,
            "baseline_valid": True,
            "intervention_valid": True,
            "baseline_gen_r2": 0.4,
            "intervention_gen_r2": 0.1,
        },
    ]
    effect = paired_layer_effects(rows)["encoder_0"]
    assert effect["damage_ce"] == pytest.approx(0.3)
    assert effect["component_exact_loss"] == pytest.approx(0.5)
    assert effect["failure_aware_ted_increase"] == pytest.approx(0.6)
    assert effect["component_valid_loss"] == pytest.approx(0.5)
    assert effect["generalization_r2_loss"] == pytest.approx(1.05)
    assert effect["n_pairs"] == 2


def test_p5_spearman_uses_damage_orientation_and_constant_is_indeterminate():
    effects = {
        "a": {"damage_ce": 1.0, "failure_aware_ted_increase": 3.0},
        "b": {"damage_ce": 2.0, "failure_aware_ted_increase": 2.0},
        "c": {"damage_ce": 3.0, "failure_aware_ted_increase": 1.0},
    }
    result = p5_damage_spearman(effects, expected_layer_count=3)
    assert result["rho"] == pytest.approx(-1.0)
    assert math.isfinite(result["p_value_two_sided"])
    assert result["supported"] is True
    assert result["orientation"] == "higher_is_more_damage_for_both"

    constant = p5_damage_spearman(
        {name: {"damage_ce": 1.0, "failure_aware_ted_increase": value}
         for name, value in zip("abc", (1.0, 2.0, 3.0))},
        expected_layer_count=3,
    )
    assert constant["rho"] is None
    assert constant["p_value_two_sided"] is None
    assert constant["determinate"] is False
    assert constant["supported"] is False

    incomplete = p5_damage_spearman(effects, expected_layer_count=4)
    assert incomplete["determinate"] is False
    assert incomplete["reason"] == "missing_or_non_finite_layer_damage"


def test_causal_formula_rank_is_lexicographic_tie_aware_and_name_stable():
    effects = {
        "decoder_2": {
            "component_exact_loss": 0.5,
            "failure_aware_ted_increase": 0.2,
            "component_valid_loss": 0.0,
            "generalization_r2_loss": 0.1,
        },
        "decoder_1": {
            "component_exact_loss": 0.5,
            "failure_aware_ted_increase": 0.2,
            "component_valid_loss": 0.0,
            "generalization_r2_loss": 0.1 + 4e-13,
        },
        "encoder_0": {
            "component_exact_loss": 0.4,
            "failure_aware_ted_increase": 0.9,
            "component_valid_loss": 1.0,
            "generalization_r2_loss": 2.0,
        },
    }
    ranked = rank_causal_formula_damage(effects)
    assert ranked["ranking"] == ["decoder_1", "decoder_2", "encoder_0"]
    assert ranked["rows"][0]["tie_group"] == ranked["rows"][1]["tie_group"]
    assert ranked["rows"][2]["tie_group"] != ranked["rows"][1]["tie_group"]
    assert ranked["score_order"] == [
        "component_exact_loss", "failure_aware_ted_increase", "component_valid_loss"
    ]
    assert ranked["diagnostic_not_used_for_ranking"] == ["generalization_r2_loss"]
