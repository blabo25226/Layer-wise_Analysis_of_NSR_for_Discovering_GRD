"""The Part C instrument regression test (v2 §8.2 step 3, NC1).

`gpu_run4.training.teacher_forced_summed_logprob` is additive beside
`teacher_forcing_loss` (never modifies it). The frozen regression identity
`sum_logprob / n_scored_tokens == -teacher_forcing_loss(...)` must hold to
1e-5 on >= 5 fixed examples. Skipped (not failed) if the ODEFormer checkpoint
is not present in this environment, mirroring the DREAM4-archive skip
pattern already used elsewhere in this repository's default test suite.
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

# Five fixed, real validation cells spanning three families and both
# dimension-1 and dimension-2 systems, chosen once and never re-picked after
# looking at any outcome.
FIXED_CELL_RELATIVE_PATHS = (
    "phase3/cells/R01_validation_d101_000_b0_n0_r0.json",
    "phase3/cells/R01_validation_d101_000_b0_n0_r0p5.json",
    "phase3/cells/R02_validation_d101_000_b0_n0_r0.json",
    "phase3/cells/R04_validation_d101_000_b0_n0_r0.json",
    "phase3/cells/R06_validation_d101_000_b0_n0_r0.json",
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
def test_sum_over_n_equals_negative_mean_ce(loaded_model, relative_path):
    import torch

    from gpu_run4.training import teacher_forced_summed_logprob, teacher_forcing_loss

    times, trajectory, tree_encoded = _load_fixed_example(relative_path)
    with torch.no_grad():
        loss = teacher_forcing_loss(loaded_model, times, trajectory, tree_encoded)
        sum_logprob, n_scored_tokens, per_token_logprobs = teacher_forced_summed_logprob(
            loaded_model, times, trajectory, tree_encoded
        )

    assert n_scored_tokens > 0
    assert len(per_token_logprobs) == n_scored_tokens
    assert abs(sum(per_token_logprobs) - sum_logprob) < 1e-4

    mean_ce = float(loss)
    identity_error = abs((sum_logprob / n_scored_tokens) - (-mean_ce))
    assert identity_error < 1e-5, (
        f"sum_logprob/n ({sum_logprob / n_scored_tokens}) != -teacher_forcing_loss "
        f"({-mean_ce}) for {relative_path}"
    )


def _called_function_names(func) -> set[str]:
    """Names of every function this function's *body* calls -- excluding its
    docstring, which may mention the other function's name in prose.
    """
    import ast
    import inspect

    source = inspect.getsource(func)
    tree = ast.parse(source)
    func_def = tree.body[0]
    body_without_docstring = func_def.body[1:] if ast.get_docstring(func_def) else func_def.body
    names = set()
    for node in ast.walk(ast.Module(body=body_without_docstring, type_ignores=[])):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            names.add(node.func.id)
    return names


def test_teacher_forcing_loss_is_unmodified_by_the_additive_function():
    """Static guard: the additive function must never be implemented by
    calling into (or monkeypatching) teacher_forcing_loss, and vice versa --
    they are two independent, side-by-side call sequences (v2 §8.2 step 3:
    "does not modify the existing one, which other phases depend on").
    """
    import inspect

    from gpu_run4 import training as training_module

    assert "teacher_forcing_loss" not in _called_function_names(training_module.teacher_forced_summed_logprob)
    assert "teacher_forced_summed_logprob" not in _called_function_names(training_module.teacher_forcing_loss)

    summed_source = inspect.getsource(training_module.teacher_forced_summed_logprob)
    loss_source = inspect.getsource(training_module.teacher_forcing_loss)
    # get_scores must differ between the two call sequences: the additive
    # function needs per-token scores, the original only needs the loss.
    assert "get_scores=True" in summed_source
    assert "get_scores=False" in loss_source
