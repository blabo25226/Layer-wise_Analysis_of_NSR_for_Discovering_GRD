from gpu_run5.seeding import stable_problem_seed


def test_problem_seed_is_stable_and_problem_scoped():
    kwargs = dict(system_id="R01_validation_d101_000", condition="frozen", noise_sigma=0.0, subsample_rho=0.0)
    first = stable_problem_seed(3101, **kwargs)
    assert first == stable_problem_seed(3101, **kwargs)
    assert first != stable_problem_seed(3202, **kwargs)
    assert first != stable_problem_seed(3101, **{**kwargs, "system_id": "R01_validation_d101_001"})
    assert first != stable_problem_seed(3101, **{**kwargs, "noise_sigma": 0.05})


def test_condition_can_be_shared_for_paired_candidate_sets():
    common = dict(system_id="R03_validation_d101_000", condition="paired_base", noise_sigma=0.05, subsample_rho=0.5)
    assert stable_problem_seed(3101, **common) == stable_problem_seed(3101, **common)
