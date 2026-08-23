from __future__ import annotations

import torch

from gpu_run5.observational import _pool_sequence, formula_depth, token_category


def test_odeformer_sequence_pool_uses_sequence_axis() -> None:
    hidden = torch.arange(1 * 3 * 2, dtype=torch.float32).reshape(1, 3, 2)
    assert _pool_sequence(hidden).tolist() == [2.0, 3.0]


def test_formula_depth_and_token_categories() -> None:
    assert formula_depth("x_0 + x_1**2") >= 3
    assert token_category("x_0") == "variable"
    assert token_category("inv") == "inv"
    assert token_category("pow2") == "integer_power"
    assert token_category("mul") == "multiplication"
    assert token_category("<EOS>") == "eos"
    assert token_category("|") == "separator"
    assert token_category("N1234") == "constant"
