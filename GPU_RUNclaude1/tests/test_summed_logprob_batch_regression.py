"""The batched, cached-encoder scoring path's regression test (v2 §8.2 step
2/3). ``gpu_run4.training.teacher_forced_summed_logprob_batch`` is additive
beside both ``teacher_forcing_loss`` and ``teacher_forced_summed_logprob``
(never modifies either): it must reproduce
``teacher_forced_summed_logprob``'s result for every sequence it scores,
whether the batch holds one sequence or several, since the only difference
is that the encoder pass is run once and reused rather than once per
sequence.

This test scores GT-mult sequences only (the same fixed examples
``test_summed_logprob_regression.py`` already uses) -- it does not score any
GPU_RUN5 beam candidate, so it is not a Part C "candidate scoring" pass; it
is a wiring regression check for the new caching primitive, structurally
identical to the already-accepted GT-only regression test this file sits
beside. Skipped (not failed) if the ODEFormer checkpoint is not present,
mirroring that file's pattern.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
CHECKPOINT_PATH = REPO_ROOT / "assets" / "odeformer" / "weights" / "odeformer.pt"
GPU_RUN5_SOURCE_RUN = REPO_ROOT / "results" / "runs" / "gpu_run5_20260823_ddd267b0"

pytestmark = pytest.mark.skipif(
    not CHECKPOINT_PATH.is_file() or not GPU_RUN5_SOURCE_RUN.is_dir(),
    reason="ODEFormer checkpoint or GPU_RUN5 source run not present in this environment",
)

FIXED_CELL_RELATIVE_PATHS = (
    "phase3/cells/R01_validation_d101_000_b0_n0_r0.json",
    "phase3/cells/R02_validation_d101_000_b0_n0_r0.json",
)


@pytest.fixture(scope="module")
def loaded_model():
    import torch

    from gpu_run4_runtime import load_odeformer_model, select_device

    device = select_device(allow_cpu=not torch.cuda.is_available())
    model = load_odeformer_model(CHECKPOINT_PATH, device=device)
    return model


def _load_fixed_example(relative_path: str):
    import numpy as np

    cell = json.loads((GPU_RUN5_SOURCE_RUN / relative_path).read_text(encoding="utf-8"))
    validation = json.loads((GPU_RUN5_SOURCE_RUN / "phase2" / "validation.json").read_text(encoding="utf-8"))
    row = next(r for r in validation if r["system_id"] == cell["system_id"])
    input_obs = cell["observations"]["input"][0]
    times = np.asarray(input_obs["times"], dtype=float)
    trajectory = np.asarray(input_obs["observed_trajectory"], dtype=float)
    tree_encoded = row["tree_encoded"]
    return times, trajectory, tree_encoded


@pytest.mark.parametrize("relative_path", FIXED_CELL_RELATIVE_PATHS)
def test_batch_of_one_matches_the_per_sequence_function(loaded_model, relative_path):
    import torch

    from gpu_run4.training import teacher_forced_summed_logprob, teacher_forced_summed_logprob_batch

    times, trajectory, tree_encoded = _load_fixed_example(relative_path)
    with torch.no_grad():
        single_sum, single_n, single_per_token = teacher_forced_summed_logprob(loaded_model, times, trajectory, tree_encoded)
        batch_result = teacher_forced_summed_logprob_batch(loaded_model, times, trajectory, [tree_encoded])

    assert len(batch_result) == 1
    batch_sum, batch_n, batch_per_token, batch_ranks, batch_ids = batch_result[0]
    assert batch_ranks is None  # compute_ranks defaults False
    assert batch_n == single_n
    assert abs(batch_sum - single_sum) < 1e-4
    assert len(batch_per_token) == len(single_per_token)
    assert max(abs(a - b) for a, b in zip(batch_per_token, single_per_token)) < 1e-4
    assert len(batch_ids) == single_n


def test_batch_of_several_identical_sequences_are_mutually_consistent(loaded_model):
    """The actual Part C use case: several sequences scored against the SAME
    cached encoder pass in one call. Using the same GT sequence twice isolates
    whether caching introduces any cross-sequence leakage -- both entries
    must be identical to each other and to the single-call function.
    """
    import torch

    from gpu_run4.training import teacher_forced_summed_logprob, teacher_forced_summed_logprob_batch

    times, trajectory, tree_encoded = _load_fixed_example(FIXED_CELL_RELATIVE_PATHS[0])
    with torch.no_grad():
        single_sum, single_n, _single_per_token = teacher_forced_summed_logprob(loaded_model, times, trajectory, tree_encoded)
        batch_result = teacher_forced_summed_logprob_batch(
            loaded_model, times, trajectory, [tree_encoded, tree_encoded], compute_ranks=True
        )

    assert len(batch_result) == 2
    for sum_lp, n_tok, per_token, ranks, token_ids in batch_result:
        assert n_tok == single_n
        assert abs(sum_lp - single_sum) < 1e-4
        assert ranks is not None
        assert len(ranks) == n_tok
        assert all(r >= 0 for r in ranks)
        assert len(token_ids) == n_tok
    first_sum = batch_result[0][0]
    second_sum = batch_result[1][0]
    assert abs(first_sum - second_sum) < 1e-9
