"""Independent equivalence oracle with audit_rational_parse."""

from __future__ import annotations

import itertools
import signal
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any

import sympy as sp

from gpu_run4.formulas import parse_system, split_components, tree_to_infix
from gpu_run4.ted import prefix_to_tree

from gpu_runmultiai.constants import ORACLE_ATOL, ORACLE_RTOL, ORACLE_T_GRID, ORACLE_X_GRID


@dataclass
class OracleResult:
    completed: bool
    analytic_equivalent: bool
    numeric_equivalent: bool
    equivalent: bool
    failure_reason: str | None = None
    rational_tokens: dict[str, str] = field(default_factory=dict)
    parsed_rationals: dict[str, str] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "completed": self.completed,
            "analytic_equivalent": self.analytic_equivalent,
            "numeric_equivalent": self.numeric_equivalent,
            "equivalent": self.equivalent,
            "failure_reason": self.failure_reason,
            "rational_tokens": dict(self.rational_tokens),
            "parsed_rationals": dict(self.parsed_rationals),
        }


def audit_rational_parse(token: str) -> sp.Rational | None:
    try:
        return sp.Rational(str(token))
    except Exception:
        return None


def _normalize_operator_tree(tree):
    if tree is None:
        return None
    label, children = tree
    if not children:
        return tree
    rebuilt = tuple(_normalize_operator_tree(child) for child in children)
    if label == "pow2" and len(rebuilt) == 1:
        return ("pow", rebuilt[0], ("2", ()))
    if label == "pow3" and len(rebuilt) == 1:
        return ("pow", rebuilt[0], ("3", ()))
    if label == "pow4" and len(rebuilt) == 1:
        return ("pow", rebuilt[0], ("4", ()))
    return (label, rebuilt)


def _collect_rational_evidence(tree) -> tuple[dict[str, str], dict[str, str]]:
    tokens: dict[str, str] = {}
    parsed: dict[str, str] = {}
    if tree is None:
        return tokens, parsed
    for label, children in _walk(tree):
        if children:
            continue
        raw = str(label)
        rational = audit_rational_parse(raw)
        if rational is not None:
            tokens[raw] = raw
            parsed[raw] = str(rational)
    return tokens, parsed


def _tree_with_rational_leaves(tree):
    tree = _normalize_operator_tree(tree)
    if tree is None:
        return None
    label, children = tree
    if not children:
        parsed = audit_rational_parse(label)
        if parsed is not None:
            return (str(parsed), ())
        return tree
    rebuilt = tuple(_tree_with_rational_leaves(child) for child in children)
    return (label, rebuilt)


def _sympy_expr_from_component(tree, symbols: dict[str, sp.Symbol]) -> sp.Expr | None:
    if tree is None:
        return None
    label, children = tree
    if not children:
        if label in symbols:
            return symbols[label]
        parsed = audit_rational_parse(label)
        if parsed is not None:
            return sp.Rational(parsed)
        try:
            return sp.sympify(label)
        except Exception:
            return None
    args = [_sympy_expr_from_component(child, symbols) for child in children]
    if any(arg is None for arg in args):
        return None
    if label == "add":
        return args[0] + args[1]
    if label == "mul":
        return args[0] * args[1]
    if label == "sub":
        return args[0] - args[1]
    if label == "div":
        return args[0] / args[1]
    if label == "pow":
        return args[0] ** args[1]
    if label == "neg":
        return -args[0]
    if label == "inv":
        return 1 / args[0]
    if label == "pow2":
        return args[0] ** 2
    if label == "pow3":
        return args[0] ** 3
    return None


def _collect_variable_names(text: str) -> list[str]:
    parsed = parse_system(text)
    names: list[str] = []
    for tree in parsed["components"]:
        if tree is None:
            continue
        for label, children in _walk(tree):
            if not children and str(label).startswith("x_"):
                if label not in names:
                    names.append(label)
    return sorted(names, key=lambda name: int(name.split("_")[1]))


def _walk(tree):
    if tree is None:
        return
    yield tree
    for child in tree[1]:
        yield from _walk(child)


def extract_component_infix(system_text: str, component_idx: int) -> str:
    parsed = parse_system(system_text)
    if component_idx >= len(parsed["components"]):
        raise IndexError(f"component_idx {component_idx} out of range")
    tree = parsed["components"][component_idx]
    return tree_to_infix(tree)


@contextmanager
def _oracle_timeout(seconds: float):
    if seconds <= 0:
        yield
        return

    def _handler(signum, frame):
        raise TimeoutError("oracle timeout")

    previous = signal.signal(signal.SIGALRM, _handler)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


def oracle_equivalence(
    truth_text: str,
    candidate_text: str,
    *,
    component_idx: int = 0,
    timeout_sec: float,
    truth_component_idx: int | None = None,
    candidate_component_idx: int | None = None,
) -> OracleResult:
    """Compare truth and candidate expressions at the requested component indices."""
    truth_idx = 0 if truth_component_idx is None else truth_component_idx
    cand_idx = 0 if candidate_component_idx is None else candidate_component_idx
    if truth_component_idx is None and candidate_component_idx is None:
        truth_idx = cand_idx = component_idx
    try:
        with _oracle_timeout(timeout_sec):
            truth_parsed = parse_system(truth_text)
            cand_parsed = parse_system(candidate_text)
            if not truth_parsed["valid"] or not cand_parsed["valid"]:
                return OracleResult(False, False, False, False, "ParseError")
            if truth_idx >= len(truth_parsed["components"]) or cand_idx >= len(cand_parsed["components"]):
                return OracleResult(False, False, False, False, "ParseError")
            truth_tree = _tree_with_rational_leaves(truth_parsed["components"][truth_idx])
            cand_tree = _tree_with_rational_leaves(cand_parsed["components"][cand_idx])
            if truth_tree is None or cand_tree is None:
                return OracleResult(False, False, False, False, "ParseError")
            rational_tokens, parsed_rationals = _collect_rational_evidence(truth_tree)
            cand_tokens, cand_parsed_rationals = _collect_rational_evidence(cand_tree)
            rational_tokens.update(cand_tokens)
            parsed_rationals.update(cand_parsed_rationals)
            var_names = _collect_variable_names(truth_text) or _collect_variable_names(candidate_text)
            symbols = {name: sp.Symbol(name, real=True) for name in var_names}
            t_sym = sp.Symbol("t", real=True)
            truth_expr = _sympy_expr_from_component(truth_tree, symbols)
            cand_expr = _sympy_expr_from_component(cand_tree, symbols)
            if truth_expr is None or cand_expr is None:
                return OracleResult(
                    False,
                    False,
                    False,
                    False,
                    "ParseError",
                    rational_tokens=rational_tokens,
                    parsed_rationals=parsed_rationals,
                )
            analytic = bool(sp.simplify(sp.expand(truth_expr - cand_expr)) == 0)
            grid_points = []
            for values in itertools.product(ORACLE_X_GRID, repeat=len(var_names)):
                mapping = {symbols[name]: value for name, value in zip(var_names, values)}
                for t_value in ORACLE_T_GRID:
                    subs = dict(mapping)
                    subs[t_sym] = t_value
                    truth_val = float(truth_expr.subs(subs))
                    cand_val = float(cand_expr.subs(subs))
                    if not (abs(truth_val) < float("inf") and abs(cand_val) < float("inf")):
                        return OracleResult(
                            False,
                            analytic,
                            False,
                            False,
                            "NonFinite",
                            rational_tokens=rational_tokens,
                            parsed_rationals=parsed_rationals,
                        )
                    if abs(truth_val - cand_val) > ORACLE_ATOL + ORACLE_RTOL * abs(truth_val):
                        return OracleResult(
                            True,
                            analytic,
                            False,
                            False,
                            None,
                            rational_tokens=rational_tokens,
                            parsed_rationals=parsed_rationals,
                        )
                    grid_points.append((truth_val, cand_val))
            numeric = bool(grid_points)
            equivalent = analytic and numeric
            return OracleResult(
                True,
                analytic,
                numeric,
                equivalent,
                None,
                rational_tokens=rational_tokens,
                parsed_rationals=parsed_rationals,
            )
    except TimeoutError:
        return OracleResult(False, False, False, False, "Timeout")
    except Exception as exc:
        return OracleResult(False, False, False, False, type(exc).__name__)


def oracle_single_component(
    truth_component_infix: str,
    candidate_system_infix: str,
    *,
    candidate_component_idx: int,
    timeout_sec: float,
) -> OracleResult:
    candidate_component = extract_component_infix(candidate_system_infix, candidate_component_idx)
    return oracle_equivalence(
        truth_component_infix,
        candidate_component,
        component_idx=0,
        truth_component_idx=0,
        candidate_component_idx=0,
        timeout_sec=timeout_sec,
    )


def prefix_to_infix_component(prefix: str) -> str:
    tree = prefix_to_tree(prefix.split(","))
    return tree_to_infix(tree)


def component_prefixes_from_system_prefixes(prefixes: list[str]) -> list[str]:
    return list(prefixes)
