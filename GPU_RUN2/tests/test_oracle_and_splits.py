"""Oracle inputs, main split, structure-OOD split, and seed bundles."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from data.gnw_synthetic import (  # noqa: E402
    define_gnw_problems,
    filter_by_main_split,
    filter_by_structure_split,
    oracle_metadata_from_expression,
    phase4_validation_panel,
    structure_regime_for,
)
from data.splits import assert_problem_splits_disjoint, structure_holdout_split  # noqa: E402
from gpu_run2_runtime import load_gpu_run2_configs, seed_bundles  # noqa: E402


def test_oracle_inputs_are_target_then_sorted_regulators():
    meta = oracle_metadata_from_expression(
        "0.3*x_3**2/(1 + x_2) - 0.2*x_1",
        family_regulators=("x_2", "x_3"),
    )
    assert meta["target_variable"] == "x_1"
    assert meta["oracle_regulators"] == ["x_2", "x_3"]
    assert meta["oracle_inputs"] == ["x_1", "x_2", "x_3"]
    assert meta["variable_order"] == meta["oracle_inputs"]


def test_cancelled_regulator_is_dropped_from_oracle():
    meta = oracle_metadata_from_expression(
        "1 - x_1",
        family_regulators=("x_2",),
    )
    assert meta["oracle_regulators"] == []
    assert meta["oracle_inputs"] == ["x_1"]


def test_all_methods_would_see_identical_oracle_arrays():
    specs = define_gnw_problems(n_variants_per_family=2)
    for spec in specs:
        for method in ("nesymres", "pysr"):
            assert spec.oracle_inputs == spec.variable_order
            assert spec.oracle_inputs[0] == spec.target_variable == "x_1"
            assert spec.oracle_source_equation_id == spec.eq_id


def test_main_and_structure_splits_are_problem_level_and_disjoint():
    specs = define_gnw_problems()
    assert_problem_splits_disjoint(specs)
    train = filter_by_main_split(specs, "train")
    val = filter_by_main_split(specs, "validation")
    test = filter_by_main_split(specs, "test")
    ids = {s.eq_id for s in train} | {s.eq_id for s in val} | {s.eq_id for s in test}
    assert len(ids) == 240
    assert not ({s.eq_id for s in train} & {s.eq_id for s in val})
    assert not ({s.eq_id for s in train} & {s.eq_id for s in test})
    assert not ({s.eq_id for s in val} & {s.eq_id for s in test})
    structure_test = filter_by_structure_split(specs, "test")
    assert {s.family_id for s in structure_test} == {"G07", "G08"}
    assert len(structure_test) == 60
    for spec in specs:
        assert structure_holdout_split(spec.family_id) == spec.structure_split


def test_phase4_panel_is_two_smallest_validation_variants_per_family():
    specs = define_gnw_problems()
    panel = phase4_validation_panel(specs)
    assert len(panel) == 16
    by_family = {}
    for spec in panel:
        by_family.setdefault(spec.family_id, []).append(spec.variant_index)
        assert spec.main_split == "validation"
    for family_id, variants in by_family.items():
        assert variants == [18, 19], family_id


def test_structure_regime_depends_on_view_not_bare_ood_label():
    assert structure_regime_for("main", "G08") == "id"
    assert structure_regime_for("structure_holdout", "G05") == "id"
    assert structure_regime_for("structure_holdout", "G07") == "ood"
    assert structure_regime_for("structure_holdout", "G08") == "ood"


def test_seed_bundles_are_three_paired_tuples():
    bundles = seed_bundles()
    assert bundles == [
        {"data_seed": 101, "model_seed": 0},
        {"data_seed": 202, "model_seed": 1},
        {"data_seed": 303, "model_seed": 2},
    ]
    config = load_gpu_run2_configs()
    assert config["decode_timeout_sec"] == 30
    assert config["noises"] == [0.0, 0.1]
