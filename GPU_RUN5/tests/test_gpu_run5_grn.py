import numpy as np

from gpu_run5.grn import FAMILIES, generate_corpus, system_definition


def test_all_families_have_matching_rhs_and_teacher_dimensions():
    params = {"a1": 1.2, "a2": 1.3, "a3": 1.4, "k1": 0.8, "k2": 0.9, "k3": 1.0,
              "b1": 0.5, "b2": 0.6, "b3": 0.7, "basal": 0.1, "n": 4}
    for family, spec in FAMILIES.items():
        rhs, teacher = system_definition(family, params)
        value = rhs(0.0, np.ones(spec.dimension))
        assert value.shape == (spec.dimension,)
        assert np.isfinite(value).all()
        assert len(teacher) == spec.dimension
        assert any("pow2,pow2" in item for item in teacher)


def test_corpus_keeps_trajectory_roles_together_and_distinct():
    corpus = generate_corpus(
        variants={"train": 1, "validation": 1, "test": 1}, n_points=20, t_span=(0.0, 2.0), seed=13,
        rtol=1e-8, atol=1e-10, minimum_variance=1e-8, maximum_abs_state=100.0,
    )
    assert corpus["records"]
    for row in corpus["records"]:
        roles = [item["role"] for item in row["trajectories"]]
        assert roles.count("input") == 1
        assert roles.count("selection") == 2
        assert roles.count("generalization") == 2
        checksums = [item["checksum"] for item in row["trajectories"]]
        assert len(set(checksums)) == 5
