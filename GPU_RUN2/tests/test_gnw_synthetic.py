"""GNW synthetic benchmark: formulas, 240 problems, noise pairing, domain ranges."""

from __future__ import annotations

import inspect
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from data import gnw_synthetic as gnw  # noqa: E402
from data.gnw_synthetic import (  # noqa: E402
    FAMILY_IDS,
    FAMILY_SPECS,
    build_paired_noise_problems,
    define_gnw_problems,
    evaluate_family,
    module_activation,
    sample_problem_points,
)


def test_gnw_source_does_not_use_finite_difference():
    source = inspect.getsource(gnw)
    assert "finite_diff" not in source
    assert "np.gradient" not in source
    assert "dream4" not in source.lower()
    assert "from GitHubSourceCode" not in source
    assert "import GitHubSourceCode" not in source


def test_independent_and_complex_activation_match_gnw_formulas():
    x = np.array([0.5, 1.2])
    k = np.array([0.8, 1.1])
    n = np.array([2.0, 3.0])
    xi = (x / k) ** n
    independent = module_activation(
        x,
        activators=["a", "b"],
        deactivators=[],
        k=k,
        n=n,
        binds_as_complex=False,
    )
    expected_ind = (xi[0] * xi[1]) / ((1 + xi[0]) * (1 + xi[1]))
    np.testing.assert_allclose(independent, expected_ind)
    complex_m = module_activation(
        x,
        activators=["a", "b"],
        deactivators=[],
        k=k,
        n=n,
        binds_as_complex=True,
    )
    expected_c = (xi[0] * xi[1]) / (1 + xi[0] * xi[1])
    np.testing.assert_allclose(complex_m, expected_c)
    act_deact = module_activation(
        x,
        activators=["a"],
        deactivators=["d"],
        k=k,
        n=n,
        binds_as_complex=False,
    )
    expected_ad = xi[0] / ((1 + xi[0]) * (1 + xi[1]))
    np.testing.assert_allclose(act_deact, expected_ad)


def test_full_catalogue_has_240_problems_and_fixed_splits():
    specs = define_gnw_problems()
    assert len(specs) == 240
    for family_id in FAMILY_IDS:
        members = [s for s in specs if s.family_id == family_id]
        assert len(members) == 30
        assert [s.variant_index for s in members] == list(range(30))
        splits = {s.main_split for s in members}
        assert splits == {"train", "validation", "test"}
        assert sum(s.main_split == "train" for s in members) == 18
        assert sum(s.main_split == "validation" for s in members) == 6
        assert sum(s.main_split == "test" for s in members) == 6
    assert all(s.structure_split == "train" for s in specs if s.family_id in {"G01", "G02", "G03", "G04", "G05"})
    assert all(s.structure_split == "validation" for s in specs if s.family_id == "G06")
    assert all(s.structure_split == "test" for s in specs if s.family_id in {"G07", "G08"})


def test_analytic_target_matches_canonical_expression_and_domain_boxes():
    specs = define_gnw_problems(n_variants_per_family=1)
    spec = next(s for s in specs if s.family_id == "G05")
    sampled = sample_problem_points(
        spec,
        data_seed=101,
        noise=0.0,
        n_train=32,
        n_eval=16,
    )
    y_eval = evaluate_family(spec.family_id, sampled.X_train, spec.parameters)
    np.testing.assert_allclose(sampled.y_train_clean, y_eval, rtol=1e-8, atol=1e-8)
    np.testing.assert_allclose(sampled.y_train, sampled.y_train_clean)
    assert sampled.X_train.min() >= 0.1 - 1e-12
    assert sampled.X_train.max() <= 2.0 + 1e-12
    assert sampled.X_id.min() >= 0.1 - 1e-12
    assert sampled.X_id.max() <= 2.0 + 1e-12
    assert sampled.X_ood.min() >= 0.05 - 1e-12
    assert sampled.X_ood.max() <= 2.5 + 1e-12
    # OOD box is strictly wider, so some OOD points should leave the ID box.
    outside = np.any((sampled.X_ood < 0.1) | (sampled.X_ood > 2.0), axis=1)
    assert outside.any()


def test_noise_conditions_share_clean_inputs():
    specs = define_gnw_problems(n_variants_per_family=1)
    paired = build_paired_noise_problems(specs[:1], data_seed=202, noises=(0.0, 0.1), n_train=64, n_eval=16)
    clean, noisy = paired
    assert clean.noise == 0.0
    assert noisy.noise == 0.1
    np.testing.assert_allclose(clean.X_train, noisy.X_train)
    np.testing.assert_allclose(clean.X_id, noisy.X_id)
    np.testing.assert_allclose(clean.X_ood, noisy.X_ood)
    np.testing.assert_allclose(clean.y_train_clean, noisy.y_train_clean)
    assert not np.allclose(clean.y_train, noisy.y_train)
    expected_std = 0.1 * (np.std(clean.y_train_clean) + 1e-8)
    np.testing.assert_allclose(noisy.noise_std, expected_std)


@pytest.mark.parametrize("family_id", FAMILY_IDS)
def test_each_family_template_evaluates_finite(family_id):
    specs = [s for s in define_gnw_problems(n_variants_per_family=1) if s.family_id == family_id]
    assert len(specs) == 1
    sampled = sample_problem_points(specs[0], data_seed=303, noise=0.0, n_train=20, n_eval=8)
    assert np.all(np.isfinite(sampled.y_train))
    assert np.all(np.isfinite(sampled.y_id))
    assert np.all(np.isfinite(sampled.y_ood))
    n_hill = [v for k, v in specs[0].parameters.items() if k.startswith("n_")]
    assert all(int(v) in {1, 2, 3, 4, 5} for v in n_hill)
    family = FAMILY_SPECS[family_id]
    assert specs[0].oracle_inputs[0] == "x_1"
    assert set(specs[0].oracle_regulators) <= set(family.oracle_regulators)
    extra = set(specs[0].oracle_inputs) - {"x_1"} - set(family.oracle_regulators)
    assert not extra
