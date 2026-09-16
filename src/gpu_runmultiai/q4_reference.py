"""Audit-owned Q4 decimal round reference (preregistration v16 §3.4)."""

from __future__ import annotations

import signal
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any

import sympy as sp
from sympy.core.function import UndefinedFunction
from sympy.core.numbers import Float, Integer, Rational
from sympy.core.symbol import Symbol
from sympy.parsing.sympy_parser import parse_expr
from sympy.simplify.simplify import Transform

ALL_OPERATORS: dict[str, int] = {
    "add": 2,
    "sub": 2,
    "mul": 2,
    "div": 2,
    "abs": 1,
    "inv": 1,
    "sqrt": 1,
    "log": 1,
    "exp": 1,
    "sin": 1,
    "arcsin": 1,
    "cos": 1,
    "arccos": 1,
    "tan": 1,
    "arctan": 1,
    "pow2": 1,
    "pow3": 1,
    "id": 1,
    "pow": 2,
}

SYMPY_OPERATORS = {
    sp.Add: "add",
    sp.Mul: "mul",
    sp.Pow: "pow",
    sp.Abs: "abs",
    sp.sign: "sign",
    sp.Heaviside: "step",
    sp.exp: "exp",
    sp.log: "log",
    sp.sin: "sin",
    sp.cos: "cos",
    sp.tan: "tan",
    sp.asin: "arcsin",
    sp.acos: "arccos",
    sp.atan: "arctan",
}


class InvalidPrefixExpression(ValueError):
    pass


class Q4ContractError(RuntimeError):
    """Frozen Q4 dialect violation requiring global abort."""


@dataclass
class Q4Result:
    q4_construction_completed: bool
    q4_emitted_prefix: str | None = None
    q4_emitted_infix: str | None = None
    q4_sympy_expr_canonical: str | None = None
    q4_construction_failure_reason: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "q4_construction_completed": self.q4_construction_completed,
            "q4_emitted_prefix": self.q4_emitted_prefix,
            "q4_emitted_infix": self.q4_emitted_infix,
            "q4_sympy_expr_canonical": self.q4_sympy_expr_canonical,
            "q4_construction_failure_reason": self.q4_construction_failure_reason,
        }


def frozen_q4_local_dict(dimension: int = 10) -> dict[str, Any]:
    local: dict[str, Any] = {
        "n": Symbol("n", real=True, nonzero=True, positive=True, integer=True),
        "e": sp.E,
        "pi": sp.pi,
        "euler_gamma": sp.EulerGamma,
        "arcsin": sp.asin,
        "arccos": sp.acos,
        "arctan": sp.atan,
        "step": sp.Heaviside,
        "sign": sp.sign,
    }
    for index in range(max(1, dimension)):
        local[f"x_{index}"] = Symbol(f"x_{index}", real=True, integer=False)
    return local


def write_infix(token: str, args: list[str]) -> str:
    if token == "add":
        return f"({args[0]})+({args[1]})"
    if token == "sub":
        return f"({args[0]})-({args[1]})"
    if token == "mul":
        return f"({args[0]})*({args[1]})"
    if token == "div":
        return f"({args[0]})/({args[1]})"
    if token == "pow":
        return f"({args[0]})**({args[1]})"
    if token == "abs":
        return f"Abs({args[0]})"
    if token == "id":
        return args[0]
    if token == "inv":
        return f"1/({args[0]})"
    if token == "pow2":
        return f"({args[0]})**2"
    if token == "pow3":
        return f"({args[0]})**3"
    if token in {"sqrt", "log", "exp", "sin", "arcsin", "cos", "arccos", "tan", "arctan"}:
        return f"{token}({args[0]})"
    raise InvalidPrefixExpression(f"unknown operator token for write_infix: {token}")


def _prefix_to_sympy_compatible_infix(expr: list[str]) -> tuple[str, list[str]]:
    if len(expr) == 0:
        raise InvalidPrefixExpression("Empty prefix list.")
    token = expr[0]
    if token in ALL_OPERATORS:
        args: list[str] = []
        remainder = expr[1:]
        for _ in range(ALL_OPERATORS[token]):
            child, remainder = _prefix_to_sympy_compatible_infix(remainder)
            args.append(child)
        return write_infix(token, args), remainder
    try:
        float(token)
        leaf = str(token)
    except ValueError:
        leaf = token
    return leaf, expr[1:]


def prefix_to_sympy_infix(prefix: str | list[str]) -> str:
    if isinstance(prefix, str):
        tokens = [part for part in prefix.split(",") if part]
    else:
        tokens = [str(part) for part in prefix if str(part)]
    infix, remainder = _prefix_to_sympy_compatible_infix(tokens)
    if remainder:
        raise InvalidPrefixExpression(f'Incorrect prefix expression "{tokens}". "{remainder}" was not parsed.')
    return f"({infix})"


def audit_round_float_atoms(expr: sp.Expr, decimals: int = 4) -> sp.Expr:
    return expr.xreplace(
        Transform(
            lambda x: x.round(decimals),
            lambda x: isinstance(x, Float),
        )
    )


def audit_sympy_to_prefix_nary_fold(op: str, expr: sp.Basic) -> list[str]:
    n_args = len(expr.args)
    parse_list: list[str] = []
    for index in range(n_args):
        if index == 0 or index < n_args - 1:
            parse_list.append(op)
        parse_list += audit_sympy_to_prefix(expr.args[index])
    return parse_list


def audit_sympy_to_prefix(expr: sp.Basic) -> list[str]:
    if isinstance(expr, Symbol):
        return [str(expr)]
    if isinstance(expr, Integer):
        return [str(expr)]
    if isinstance(expr, Float):
        return [str(expr)]
    if isinstance(expr, Rational):
        return ["mul", str(expr.p), "pow", str(expr.q), "-1"]
    if expr == sp.EulerGamma:
        return ["euler_gamma"]
    if expr == sp.E:
        return ["e"]
    if expr == sp.pi:
        return ["pi"]
    for sympy_type, op_name in SYMPY_OPERATORS.items():
        if isinstance(expr, sympy_type):
            return audit_sympy_to_prefix_nary_fold(op_name, expr)
    raise InvalidPrefixExpression(f"unsupported SymPy atom for audit_sympy_to_prefix: {expr!r}")


def verify_q4_emitted_prefix(prefix: str) -> None:
    try:
        prefix_to_sympy_infix(prefix)
    except InvalidPrefixExpression as exc:
        raise Q4ContractError(str(exc)) from exc


@contextmanager
def _q4_timeout(seconds: float):
    if seconds <= 0:
        yield
        return

    def _handler(signum, frame):
        raise TimeoutError("q4 timeout")

    previous = signal.signal(signal.SIGALRM, _handler)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


def audit_q4_decimal_round_reference(
    e1_prefix: str,
    *,
    dimension: int = 10,
    timeout_sec: float = 10.0,
    verify_contract: bool = True,
) -> Q4Result:
    try:
        with _q4_timeout(timeout_sec):
            infix = prefix_to_sympy_infix(e1_prefix)
            local_dict = frozen_q4_local_dict(dimension)
            expr = parse_expr(infix, evaluate=True, local_dict=local_dict)
            if expr.is_finite is False:
                return Q4Result(False, q4_construction_failure_reason="NonFinite")
            rounded = audit_round_float_atoms(expr, decimals=4)
            if rounded.is_finite is False:
                return Q4Result(False, q4_construction_failure_reason="NonFinite")
            emitted_prefix = ",".join(audit_sympy_to_prefix(rounded))
            emitted_infix = prefix_to_sympy_infix(emitted_prefix)
            if verify_contract:
                verify_q4_emitted_prefix(emitted_prefix)
            return Q4Result(
                True,
                q4_emitted_prefix=emitted_prefix,
                q4_emitted_infix=emitted_infix,
                q4_sympy_expr_canonical=str(rounded),
            )
    except Q4ContractError:
        raise
    except TimeoutError:
        return Q4Result(False, q4_construction_failure_reason="Timeout")
    except InvalidPrefixExpression as exc:
        return Q4Result(False, q4_construction_failure_reason=str(exc))
    except Exception as exc:
        return Q4Result(False, q4_construction_failure_reason=type(exc).__name__)


def e1_not_equivalent_to_q4(
    e1_component_prefix: str,
    q4_sympy_expr_canonical: str | None,
    *,
    dimension: int,
    timeout_sec: float = 10.0,
) -> bool:
    """§3.4.10 canonical oracle: is E1 non-equivalent to Q4(E1) at SymPy expression level?

    Uses the frozen Q4 local dictionary and the frozen external Q4 timeout; never the
    production simplifier tree or E2.
    """
    if not q4_sympy_expr_canonical:
        return False
    local_dict = frozen_q4_local_dict(dimension)
    with _q4_timeout(timeout_sec):
        e1_expr = parse_expr(
            prefix_to_sympy_infix(e1_component_prefix),
            evaluate=True,
            local_dict=local_dict,
        )
        q4_expr = parse_expr(q4_sympy_expr_canonical, evaluate=True, local_dict=local_dict)
        return bool(sp.simplify(sp.expand(e1_expr - q4_expr)) != 0)


C_Q4_FIXTURES: list[dict[str, Any]] = [
    {
        "fixture_id": "q4_fixture_01",
        "e1_prefix_input": "mul,0.04598,x_0",
        "expected_emit_token": "0.0460",
    },
    {
        "fixture_id": "q4_fixture_02",
        "e1_prefix_input": "mul,10.0,x_0",
        "expected_emit_token": "10.0",
    },
    {
        "fixture_id": "q4_fixture_03",
        "e1_prefix_input": "add,add,x_0,x_1,x_2",
        "expected_emit_prefix": "add,x_0,add,x_1,x_2",
    },
    {
        "fixture_id": "q4_fixture_04",
        "e1_prefix_input": "mul,mul,2,x_0,x_1",
        "expected_emit_prefix": "mul,2,mul,x_0,x_1",
    },
    {
        "fixture_id": "q4_fixture_05",
        "e1_prefix_input": "pow2,div,mul,10.0,x_0,10.0",
        "require_construction": True,
    },
    {
        "fixture_id": "q4_fixture_06",
        "e1_prefix_input": "mul,0.33333,x_0",
        "expected_emit_token": "0.3333",
    },
    {
        "fixture_id": "q4_fixture_07",
        "e1_prefix_input": "mul,div,1,3,x_0",
        "expected_emit_prefix": "mul,mul,1,pow,3,-1,x_0",
        "require_rational": True,
    },
]


def evaluate_c_q4_fixture(fixture: dict[str, Any], *, timeout_sec: float = 10.0) -> dict[str, Any]:
    result = audit_q4_decimal_round_reference(
        fixture["e1_prefix_input"],
        timeout_sec=timeout_sec,
    )
    row = {
        "fixture_id": fixture["fixture_id"],
        "e1_prefix_input": fixture["e1_prefix_input"],
        **result.as_dict(),
    }
    assertions_pass = bool(result.q4_construction_completed)
    if assertions_pass and fixture.get("expected_emit_token"):
        assertions_pass = fixture["expected_emit_token"] in (result.q4_emitted_prefix or "")
    if assertions_pass and fixture.get("expected_emit_prefix"):
        assertions_pass = result.q4_emitted_prefix == fixture["expected_emit_prefix"]
    if assertions_pass and fixture.get("require_rational"):
        canonical = result.q4_sympy_expr_canonical or ""
        assertions_pass = "0.3333" not in canonical and "/3" in canonical.replace(" ", "")
    row["fixture_specific_assertions_pass"] = assertions_pass
    row["fixture_pass"] = bool(result.q4_construction_completed and assertions_pass)
    row["terminal_outcome"] = "fixture_pass" if row["fixture_pass"] else "fixture_failure"
    return row
