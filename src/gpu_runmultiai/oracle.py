"""Independent equivalence oracle with audit_rational_parse."""

from __future__ import annotations

import itertools
import re
import signal
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any

import sympy as sp

from gpu_run4.formulas import split_components, tree_to_infix
from gpu_run4.ted import BINARY_OPS, UNARY_OPS, Tree, prefix_to_tree, tree_to_prefix

from gpu_runmultiai.constants import ORACLE_ATOL, ORACLE_RTOL, ORACLE_T_GRID, ORACLE_X_GRID

_NUMERIC_TOKEN_RE = re.compile(r"(?<![A-Za-z_])\d+\.\d+|\d+")


def collect_pre_rational_tokens(*texts: str) -> dict[str, str]:
    """Capture original numeric tokens before audit rationalization."""
    tokens: dict[str, str] = {}
    for text in texts:
        for match in _NUMERIC_TOKEN_RE.findall(str(text)):
            if audit_rational_parse(match) is not None:
                tokens[match] = match
    return tokens


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
    """Parse a raw numeric token directly to sympy.Rational without float intermediates."""
    text = str(token).strip()
    if not text:
        return None
    try:
        return sp.Rational(text)
    except Exception:
        return None


def _normalize_operator_tree(tree: Tree | None) -> Tree | None:
    if tree is None:
        return None
    label, children = tree
    if not children:
        return tree
    rebuilt = tuple(_normalize_operator_tree(child) for child in children)
    if any(child is None for child in rebuilt):
        return None
    if label == "pow2" and len(rebuilt) == 1:
        return ("pow", (rebuilt[0], ("2", ())))
    if label == "pow3" and len(rebuilt) == 1:
        return ("pow", (rebuilt[0], ("3", ())))
    if label == "pow4" and len(rebuilt) == 1:
        return ("pow", (rebuilt[0], ("4", ())))
    return (label, rebuilt)


def _tree_with_rational_leaves(tree: Tree | None) -> Tree | None:
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
    if any(child is None for child in rebuilt):
        return None
    return (label, rebuilt)


ORACLE_OPERATOR_ARITY: dict[str, int] = {
    "add": 2,
    "sub": 2,
    "mul": 2,
    "div": 2,
    "pow": 2,
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
    "pow4": 1,
    "id": 1,
    "neg": 1,
}


def _parse_prefix_subtree(tokens: list[str], index: int = 0) -> tuple[Tree | None, int]:
    if index >= len(tokens):
        return None, index
    token = tokens[index]
    if token in ORACLE_OPERATOR_ARITY:
        children: list[Tree] = []
        next_index = index + 1
        for _ in range(ORACLE_OPERATOR_ARITY[token]):
            child, next_index = _parse_prefix_subtree(tokens, next_index)
            if child is None:
                return None, index
            children.append(child)
        return (token, tuple(children)), next_index
    return (token, ()), index + 1


def _normalize_prefix_tokens(tokens: list[str]) -> list[str] | None:
    tree, remainder = _parse_prefix_subtree(tokens, 0)
    if tree is None or remainder != len(tokens):
        return None
    normalized = _normalize_operator_tree(tree)
    if normalized is None:
        return None
    return tree_to_prefix(normalized)


def audit_parse_prefix_component(prefix: str | list[str]) -> Tree | None:
    if isinstance(prefix, str):
        tokens = [tok for tok in prefix.split(",") if tok]
    else:
        tokens = [str(tok) for tok in prefix if str(tok)]
    normalized = _normalize_prefix_tokens(tokens)
    if normalized is None:
        return None
    tree = prefix_to_tree(normalized)
    return _tree_with_rational_leaves(tree)


def _sympy_local_dict() -> dict[str, Any]:
    local: dict[str, Any] = {
        "e": sp.E,
        "pi": sp.pi,
    }
    for index in range(24):
        local[f"x_{index}"] = sp.Symbol(f"x_{index}", real=True)
    return local


def audit_parse_infix_component(expr: str) -> Tree | None:
    text = str(expr).strip()
    if not text:
        return None
    if "," in text and " " not in text and any(tok in UNARY_OPS or tok in BINARY_OPS for tok in text.split(",")):
        return audit_parse_prefix_component(text)
    from sympy.parsing.sympy_parser import parse_expr

    prepared = text.replace("^", "**").replace(" ", "")
    try:
        parsed = parse_expr(prepared, local_dict=_sympy_local_dict(), evaluate=False)
        return _tree_with_rational_leaves(_sympy_tree_from_sympy(parsed))
    except Exception:
        return None


def _sympy_tree_from_sympy(expr: Any) -> Tree | None:
    if expr is None:
        return None
    if expr.is_Number:
        return (str(sp.Rational(str(expr))), ())
    if expr.is_Symbol:
        return (str(expr), ())
    if expr.is_Add:
        args = list(expr.args)
        if len(args) < 2:
            return _sympy_tree_from_sympy(args[0]) if args else None
        left = _sympy_tree_from_sympy(args[0])
        for arg in args[1:]:
            right = _sympy_tree_from_sympy(arg)
            if left is None or right is None:
                return None
            left = ("add", (left, right))
        return left
    if expr.is_Mul:
        args = list(expr.args)
        if len(args) < 2:
            return _sympy_tree_from_sympy(args[0]) if args else None
        left = _sympy_tree_from_sympy(args[0])
        for arg in args[1:]:
            right = _sympy_tree_from_sympy(arg)
            if left is None or right is None:
                return None
            left = ("mul", (left, right))
        return left
    if expr.is_Pow:
        base = _sympy_tree_from_sympy(expr.base)
        exponent = _sympy_tree_from_sympy(expr.exp)
        if base is None or exponent is None:
            return None
        return ("pow", (base, exponent))
    if expr.is_Function:
        name = str(expr.func)
        if name in {"sin", "cos", "exp", "log", "tan", "sqrt"} and len(expr.args) == 1:
            child = _sympy_tree_from_sympy(expr.args[0])
            if child is None:
                return None
            return (name, (child,))
    return None


def audit_parse_system(text: str) -> dict[str, Any]:
    raw = str(text)
    parts = split_components(raw)
    trees: list[Tree | None] = []
    failure = None
    for part in parts:
        tree = audit_parse_infix_component(part)
        if tree is None:
            failure = "ParseError"
        trees.append(tree)
    if not parts:
        failure = "ParseError"
    return {
        "raw": raw,
        "components_raw": parts,
        "components": trees,
        "dimension": len(parts),
        "valid": failure is None and all(tree is not None for tree in trees),
        "failure_reason": failure,
    }


def _collect_rational_evidence(tree: Tree | None) -> tuple[dict[str, str], dict[str, str]]:
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


def _sympy_expr_from_component(tree: Tree | None, symbols: dict[str, sp.Symbol]) -> sp.Expr | None:
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
    if label == "pow4":
        return args[0] ** 4
    return None


def _collect_variable_names_from_tree(tree: Tree | None) -> list[str]:
    names: list[str] = []
    if tree is None:
        return names
    for label, children in _walk(tree):
        if not children and str(label).startswith("x_") and label not in names:
            names.append(str(label))
    return sorted(names, key=lambda name: int(name.split("_")[1]))


def _collect_variable_names(text: str) -> list[str]:
    parsed = audit_parse_system(text)
    names: list[str] = []
    for tree in parsed["components"]:
        names.extend(_collect_variable_names_from_tree(tree))
    return sorted(set(names), key=lambda name: int(name.split("_")[1]))


def _walk(tree: Tree):
    yield tree
    for child in tree[1]:
        yield from _walk(child)


def extract_component_infix(system_text: str, component_idx: int) -> str:
    parsed = audit_parse_system(system_text)
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


def _oracle_from_trees(
    truth_tree: Tree,
    cand_tree: Tree,
    *,
    timeout_sec: float,
    rational_tokens: dict[str, str] | None = None,
) -> OracleResult:
    tree_tokens, tree_parsed = _collect_rational_evidence(truth_tree)
    cand_tokens, cand_parsed = _collect_rational_evidence(cand_tree)
    tokens = dict(rational_tokens or {})
    tokens.update(tree_tokens)
    tokens.update(cand_tokens)
    parsed_rationals = dict(tree_parsed)
    parsed_rationals.update(cand_parsed)
    var_names = sorted(
        set(_collect_variable_names_from_tree(truth_tree) + _collect_variable_names_from_tree(cand_tree)),
        key=lambda name: int(name.split("_")[1]),
    )
    symbols = {name: sp.Symbol(name, real=True) for name in var_names}
    truth_expr = _sympy_expr_from_component(truth_tree, symbols)
    cand_expr = _sympy_expr_from_component(cand_tree, symbols)
    if truth_expr is None or cand_expr is None:
        return OracleResult(
            False,
            False,
            False,
            False,
            "ParseError",
            rational_tokens=tokens,
            parsed_rationals=parsed_rationals,
        )
    analytic = bool(sp.simplify(sp.expand(truth_expr - cand_expr)) == 0)
    grid_points = []
    for values in itertools.product(ORACLE_X_GRID, repeat=len(var_names)):
        mapping = {symbols[name]: value for name, value in zip(var_names, values)}
        for t_value in ORACLE_T_GRID:
            subs = dict(mapping)
            subs[sp.Symbol("t", real=True)] = t_value
            truth_val = float(truth_expr.subs(subs))
            cand_val = float(cand_expr.subs(subs))
            if not (abs(truth_val) < float("inf") and abs(cand_val) < float("inf")):
                return OracleResult(
                    False,
                    analytic,
                    False,
                    False,
                    "NonFinite",
                    rational_tokens=tokens,
                    parsed_rationals=parsed_rationals,
                )
            if abs(truth_val - cand_val) > ORACLE_ATOL + ORACLE_RTOL * abs(truth_val):
                return OracleResult(
                    True,
                    analytic,
                    False,
                    False,
                    None,
                    rational_tokens=tokens,
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
        rational_tokens=tokens,
        parsed_rationals=parsed_rationals,
    )


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
            truth_parsed = audit_parse_system(truth_text)
            cand_parsed = audit_parse_system(candidate_text)
            if not truth_parsed["valid"] or not cand_parsed["valid"]:
                return OracleResult(False, False, False, False, "ParseError")
            if truth_idx >= len(truth_parsed["components"]) or cand_idx >= len(cand_parsed["components"]):
                return OracleResult(False, False, False, False, "ParseError")
            truth_tree = truth_parsed["components"][truth_idx]
            cand_tree = cand_parsed["components"][cand_idx]
            if truth_tree is None or cand_tree is None:
                return OracleResult(False, False, False, False, "ParseError")
            rational_tokens = collect_pre_rational_tokens(truth_text, candidate_text)
            return _oracle_from_trees(
                truth_tree,
                cand_tree,
                timeout_sec=timeout_sec,
                rational_tokens=rational_tokens,
            )
    except TimeoutError:
        return OracleResult(False, False, False, False, "Timeout")
    except Exception as exc:
        return OracleResult(False, False, False, False, type(exc).__name__)


def oracle_equivalence_prefix(
    truth_prefix: str,
    candidate_prefix: str,
    *,
    timeout_sec: float,
) -> OracleResult:
    truth_tree = audit_parse_prefix_component(truth_prefix)
    cand_tree = audit_parse_prefix_component(candidate_prefix)
    if truth_tree is None or cand_tree is None:
        return OracleResult(False, False, False, False, "ParseError")
    try:
        with _oracle_timeout(timeout_sec):
            return _oracle_from_trees(truth_tree, cand_tree, timeout_sec=timeout_sec)
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
    truth_component_prefix: str | None = None,
    candidate_component_prefix: str | None = None,
) -> OracleResult:
    if truth_component_prefix is not None and candidate_component_prefix is not None:
        return oracle_equivalence_prefix(
            truth_component_prefix,
            candidate_component_prefix,
            timeout_sec=timeout_sec,
        )
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
    tree = audit_parse_prefix_component(prefix)
    if tree is None:
        raise ValueError(f"failed to parse prefix component: {prefix}")
    return tree_to_infix(tree)
