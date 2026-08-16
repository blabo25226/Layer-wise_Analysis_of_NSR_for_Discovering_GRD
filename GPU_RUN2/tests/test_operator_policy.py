"""Restricted pow, division safety, and NeSymReS / PySR operator mapping."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from evaluation.operator_policy import (  # noqa: E402
    check_power_exponents,
    filter_prefix_tokens,
    pysr_operator_kwargs,
    validate_candidate_expression,
)
from models.nesymres_adapter import predict_equation  # noqa: E402
from nesymres.architectures.model import (  # noqa: E402
    _gpu_run2_mask_scores,
    _gpu_run2_prefix_state,
)


def test_integer_pow_2_to_5_allowed_variable_exponent_rejected():
    assert check_power_exponents("x_1**2 + x_2**5") is None
    assert check_power_exponents("x_1**3 / (1 + x_2**4)") is None
    assert check_power_exponents("x_2**2 / (1 + x_2**2)") is None
    assert check_power_exponents("x_1**x_2") == "DisallowedPowerExponent"
    assert check_power_exponents("x_1**0.7") == "DisallowedPowerExponent"
    assert check_power_exponents("x_1**(-2)") == "DisallowedPowerExponent"
    ok, reason = validate_candidate_expression("tan(x_1)")
    assert not ok and str(reason).startswith("DisallowedOperator")


def test_nesymres_prefix_pow_child_must_be_literal_2_to_5():
    ok, reason = filter_prefix_tokens(["mul", "x_1", "pow", "x_2", "3"])
    assert ok and reason is None
    bad, bad_reason = filter_prefix_tokens(["pow", "x_1", "x_2"])
    assert not bad and bad_reason == "DisallowedPowerExponent"
    trig, trig_reason = filter_prefix_tokens(["sin", "x_1"])
    assert not trig and str(trig_reason).startswith("DisallowedOperator")


def test_division_safety_flags_near_zero_denominator():
    X_ok = np.array([[1.0, 1.5], [1.2, 1.8]])
    X_bad = np.array([[1.0, 0.0], [1.2, 1e-12]])
    ok, reason = validate_candidate_expression(
        "x_1 / (x_2 + 1)",
        point_sets={"train": (X_ok, ["x_1", "x_2"])},
        margin=1e-6,
    )
    assert ok and reason is None
    bad, bad_reason = validate_candidate_expression(
        "x_1 / x_2",
        point_sets={"domain_id": (X_bad, ["x_1", "x_2"])},
        margin=1e-6,
    )
    assert not bad
    assert str(bad_reason).startswith("UnsafeDivision")


def test_pysr_mapping_has_no_binary_power():
    kwargs = pysr_operator_kwargs()
    assert kwargs["binary_operators"] == ["+", "-", "*", "/"]
    assert "^" not in kwargs["binary_operators"]
    joined = " ".join(kwargs["unary_operators"])
    assert "square" in joined and "cube" in joined
    assert "pow4" in joined and "pow5" in joined


def test_nesymres_decode_mask_enforces_prefix_grammar_and_oracle_variables():
    word2id = {
        "P": 0,
        "S": 1,
        "F": 2,
        "c": 3,
        "x_1": 4,
        "x_2": 5,
        "add": 6,
        "mul": 7,
        "div": 8,
        "pow": 9,
        "sin": 10,
        "2": 11,
        "3": 12,
    }

    class Params:
        pass

    params = Params()
    params.word2id = word2id
    params.id2word = {value: key for key, value in word2id.items()}
    params.allowed_token_ids = set(word2id.values()) - {word2id["sin"]}
    params.allowed_pow_exponent_ids = {word2id["2"], word2id["3"]}
    params.allowed_variable_ids = {word2id["x_1"]}

    assert _gpu_run2_prefix_state(
        [word2id["S"], word2id["pow"], word2id["x_1"]], params
    ) == "pow_exponent"
    generated = torch.tensor(
        [[word2id["S"], word2id["pow"], word2id["x_1"], 0]]
    )
    scores = torch.zeros((1, len(word2id)))
    masked = _gpu_run2_mask_scores(scores, generated, 3, params)
    finite_ids = set(torch.where(torch.isfinite(masked[0]))[0].tolist())
    assert finite_ids == {word2id["2"], word2id["3"]}

    root_scores = torch.zeros((1, len(word2id)))
    root = _gpu_run2_mask_scores(
        root_scores,
        torch.tensor([[word2id["S"], 0, 0, 0]]),
        1,
        params,
    )
    assert not torch.isfinite(root[0, word2id["sin"]])
    assert not torch.isfinite(root[0, word2id["x_2"]])
    assert not torch.isfinite(root[0, word2id["F"]])


def test_nesymres_adapter_accepts_scalar_bfgs_loss():
    class Model:
        def fitfunc(self, _x, _y, *, cfg_params):
            assert cfg_params is not None
            return {"best_bfgs_preds": ["x_1"], "best_bfgs_loss": 0.25}

    result = predict_equation(
        Model(), object(), np.ones((3, 1)), np.ones(3), quiet=True
    )
    assert result["equation"] == "x_1"
    assert result["bfgs_loss"] == 0.25
