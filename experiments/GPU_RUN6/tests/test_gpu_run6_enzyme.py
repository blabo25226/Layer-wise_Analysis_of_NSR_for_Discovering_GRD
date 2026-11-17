"""GPU_RUN6 data generation and structural-class tests (CPU, no model weights needed)."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

from gpu_run6 import enzyme  # noqa: E402
from gpu_run6.layers import token_category  # noqa: E402


@pytest.mark.parametrize(
    "infix, expected",
    [
        ("-0.25 * x_0 * 1/(0.5 + x_0)", "R[1/1]"),
        ("-0.5*x_0/(1 + 2*x_0)", "R[1/1]"),  # same law, different parameterisation
        ("-1*x_0 * 1/(0.3 + x_0 + 2*x_0**2)", "R[1/2]"),
        ("-2*(x_0)**2 / (0.1 + (x_0)**2)", "R[2/2]"),
        ("-0.3*x_0", "P[1]"),
        ("-0.3*x_0 + 0.1*(x_0)**2", "P[2]"),
        ("-0.3*x_0 + 1e-9*(x_0)**2", "P[1]"),  # negligible coefficient dropped
        ("sin(x_0)", "OTHER"),
        ("x_0*x_1", "OTHER"),
        ("", "INVALID"),
    ],
)
def test_structural_class(infix, expected):
    assert enzyme.structural_class(infix) == expected


def test_true_laws_have_their_declared_class():
    for family in enzyme.FAMILIES_1D + ("MA_S",):
        for index in range(3):
            row = enzyme.make_problem(family, seed=9, index=index)
            infix = _prefix_to_infix(row["true_prefix"])
            assert enzyme.class_match(family, infix), (family, infix)


def test_mass_action_support():
    row = enzyme.make_problem("MA_SC", seed=9, index=0)
    assert enzyme.class_match("MA_SC", _prefix_to_infix(row["true_prefix"]))
    assert not enzyme.class_match("MA_SC", "-x_0 | x_1")


def test_native_frame_and_determinism():
    a = enzyme.make_problem("MM_S", seed=5, index=2)
    b = enzyme.make_problem("MM_S", seed=5, index=2)
    assert a["checksum"] == b["checksum"]
    t = np.asarray(a["times"])
    x = np.asarray(a["trajectory"])
    assert t[0] == 1.0 and t[-1] == 10.0 and len(t) == enzyme.N_POINTS
    assert abs(x[0, 0] - 1.0) < 1e-12
    assert abs(x[-1, 0] - a["params"]["end"]) < 1e-3  # depletion calibration
    p = enzyme.make_problem("MM_P", seed=5, index=2)
    assert abs(np.asarray(p["trajectory"])[0, 0]) < 1e-12


def test_true_trajectory_solves_true_law():
    row = enzyme.make_problem("SI", seed=3, index=1)
    t = np.asarray(row["times"])
    x = np.asarray(row["trajectory"])[:, 0]
    V, K, Ki = row["params"]["V"], row["params"]["K"], row["params"]["Ki"]
    rhs = -V * x / (K + x + x**2 / Ki)
    assert np.max(np.abs(np.gradient(x, t) - rhs)) < 5e-3


def test_different_seeds_do_not_collide():
    a = {enzyme.make_problem("QUAD", 1101, i)["checksum"] for i in range(20)}
    b = {enzyme.make_problem("QUAD", 1606, i)["checksum"] for i in range(20)}
    assert not a & b


def test_token_category():
    assert token_category("inv") == "inv"
    assert token_category("pow2") == "operator"
    assert token_category("x_0") == "variable"
    assert token_category("N2500") == "constant"
    assert token_category("E-4") == "constant"


def _prefix_to_infix(prefix: str) -> str:
    """Minimal prefix -> infix for the token set used by the generators."""
    components = prefix.split(",|,")
    out = []
    for comp in components:
        tokens = comp.split(",")

        def parse(i):
            tok = tokens[i]
            if tok in ("add", "mul"):
                a, j = parse(i + 1)
                b, j = parse(j)
                return (f"({a} + {b})" if tok == "add" else f"({a} * {b})"), j
            if tok == "inv":
                a, j = parse(i + 1)
                return f"(1/{a})", j
            if tok == "pow2":
                a, j = parse(i + 1)
                return f"({a})**2", j
            return tok, i + 1

        expr, consumed = parse(0)
        assert consumed == len(tokens)
        out.append(expr)
    return " | ".join(out)
