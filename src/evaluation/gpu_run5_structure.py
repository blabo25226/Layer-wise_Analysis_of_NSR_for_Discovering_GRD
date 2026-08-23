"""Frozen structural flags and exponent-aware skeletons for GPU_RUN5."""

from __future__ import annotations

import re
from typing import Any, Iterable

from gpu_run4.formulas import parse_system, tree_to_prefix

Tree = tuple[str, tuple["Tree", ...]]
TRANSCENDENTAL = {"exp", "log", "ln", "sin", "cos", "tan", "cot", "sqrt", "arcsin", "arccos", "arctan"}


def _walk(tree: Tree | None) -> Iterable[Tree]:
    if tree is None:
        return
    yield tree
    for child in tree[1]:
        yield from _walk(child)


def _has_variable(tree: Tree | None) -> bool:
    return any(re.fullmatch(r"x_\d+", node[0]) for node in _walk(tree))


def _denominators(tree: Tree | None) -> list[Tree]:
    out: list[Tree] = []
    for label, children in _walk(tree):
        if label == "inv" and len(children) == 1:
            out.append(children[0])
        elif label == "div" and len(children) == 2:
            out.append(children[1])
    return out


def _algebraically_rational(tree: Tree | None) -> bool:
    if tree is None:
        return False
    for label, children in _walk(tree):
        if label in TRANSCENDENTAL:
            return False
        if label == "pow" and len(children) == 2:
            exponent = children[1][0]
            try:
                if float(exponent).is_integer() is False:
                    return False
            except ValueError:
                return False
    return True


def _contains_exp(tree: Tree) -> bool:
    return any(node[0] == "exp" for node in _walk(tree))


def _is_constant_leaf(tree: Tree) -> bool:
    label, children = tree
    if children:
        return False
    if re.fullmatch(r"c_?\d+", label):
        return True
    try:
        float(label)
        return True
    except ValueError:
        return False


def _positive_integer_power(tree: Tree) -> tuple[str, int] | None:
    label, children = tree
    if re.fullmatch(r"x_\d+", label) and not children:
        return label, 1
    if label in {"pow2", "pow3"} and len(children) == 1:
        base = _positive_integer_power(children[0])
        if base:
            return base[0], base[1] * int(label[-1])
    if label == "pow" and len(children) == 2 and re.fullmatch(r"x_\d+", children[0][0]):
        try:
            exponent = int(float(children[1][0]))
        except ValueError:
            return None
        return (children[0][0], exponent) if exponent > 0 else None
    return None


def _constant_expression(tree: Tree) -> bool:
    return not _has_variable(tree) and not any(node[0] in TRANSCENDENTAL for node in _walk(tree))


def _strict_hill_denominator(denominator: Tree) -> tuple[str, int] | None:
    label, children = denominator
    if label != "add" or len(children) != 2:
        return None
    for power, constant in ((children[0], children[1]), (children[1], children[0])):
        identified = _positive_integer_power(power)
        if identified and _constant_expression(constant):
            return identified
    return None


def _flatten_mul(tree: Tree) -> list[Tree]:
    if tree[0] == "mul" and len(tree[1]) == 2:
        return _flatten_mul(tree[1][0]) + _flatten_mul(tree[1][1])
    if tree[0] == "neg" and len(tree[1]) == 1:
        return [("-1", ())] + _flatten_mul(tree[1][0])
    return [tree]


def _flatten_add(tree: Tree) -> list[Tree]:
    if tree[0] == "add" and len(tree[1]) == 2:
        return _flatten_add(tree[1][0]) + _flatten_add(tree[1][1])
    return [tree]


def _hill_flags(tree: Tree) -> tuple[bool, bool]:
    strict = False
    modulated = False
    for node in _flatten_add(tree):
        factors = _flatten_mul(node)
        for index, factor in enumerate(factors):
            if factor[0] != "inv" or len(factor[1]) != 1:
                continue
            identified = _strict_hill_denominator(factor[1][0])
            if not identified:
                continue
            variable, exponent = identified
            remaining = factors[:index] + factors[index + 1 :]
            nonconstant = [item for item in remaining if not _constant_expression(item)]
            activation = len(nonconstant) == 1 and _positive_integer_power(nonconstant[0]) == (variable, exponent)
            repression = len(nonconstant) == 0
            strict |= activation or repression
            modulated |= bool(nonconstant) and not activation
    return strict, modulated


def _polynomial_degree(tree: Tree) -> int | None:
    label, children = tree
    if re.fullmatch(r"x_\d+", label) and not children:
        return 1
    if _constant_expression(tree):
        return 0
    if label in {"add", "sub"} and len(children) == 2:
        degrees = [_polynomial_degree(child) for child in children]
        return max(degrees) if all(value is not None for value in degrees) else None
    if label == "mul" and len(children) == 2:
        degrees = [_polynomial_degree(child) for child in children]
        return sum(degrees) if all(value is not None for value in degrees) else None
    if label == "neg" and len(children) == 1:
        return _polynomial_degree(children[0])
    return None


def _strict_sigmoid(tree: Tree) -> bool:
    for node in _flatten_add(tree):
        factors = _flatten_mul(node)
        for index, factor in enumerate(factors):
            if factor[0] != "inv" or len(factor[1]) != 1:
                continue
            denominator = factor[1][0]
            if denominator[0] != "add" or len(denominator[1]) != 2:
                continue
            matched = False
            for constant, exponential in ((denominator[1][0], denominator[1][1]), (denominator[1][1], denominator[1][0])):
                if _constant_expression(constant) and exponential[0] == "exp" and len(exponential[1]) == 1:
                    degree = _polynomial_degree(exponential[1][0])
                    matched = degree is not None and degree <= 1
            remaining = factors[:index] + factors[index + 1 :]
            if matched and all(_constant_expression(item) for item in remaining):
                return True
    return False


def _exponent_skeleton(tree: Tree | None, *, exponent_context: bool = False) -> Tree | None:
    if tree is None:
        return None
    label, children = tree
    is_number = False
    try:
        float(label)
        is_number = True
    except ValueError:
        pass
    is_constant_symbol = bool(re.fullmatch(r"c_?\d+", label))
    if (is_number or is_constant_symbol) and not exponent_context:
        label = "CONST"
    next_children = []
    for index, child in enumerate(children):
        keep = label == "pow" and index == 1
        next_children.append(_exponent_skeleton(child, exponent_context=keep))
    return label, tuple(next_children)  # type: ignore[arg-type]


def classify_formula(text: str) -> dict[str, Any]:
    parsed = parse_system(text)
    component_flags = []
    component_skeletons = []
    for tree in parsed["components"]:
        denominators = _denominators(tree)
        variable_denominator = any(_has_variable(item) for item in denominators)
        rational = _algebraically_rational(tree)
        strict_hill, modulated_hill = _hill_flags(tree)
        sigmoid = _strict_sigmoid(tree)
        flags = {
            "variable_denominator_form": variable_denominator,
            "algebraically_rational": rational,
            "rational_with_variable_denominator": variable_denominator and rational,
            "hill_form": strict_hill,
            "modulated_hill_form": modulated_hill,
            "sigmoid_saturating_form": sigmoid,
        }
        component_flags.append(flags)
        skeleton = _exponent_skeleton(tree)
        component_skeletons.append(",".join(tree_to_prefix(skeleton)) if skeleton is not None else "")
    keys = component_flags[0].keys() if component_flags else (
        "variable_denominator_form",
        "algebraically_rational",
        "rational_with_variable_denominator",
        "hill_form",
        "modulated_hill_form",
        "sigmoid_saturating_form",
    )
    return {
        "valid": bool(parsed["valid"]),
        "failure_reason": parsed["failure_reason"],
        "component_flags": component_flags,
        **{key: any(row[key] for row in component_flags) for key in keys},
        "exponent_aware_skeleton": " | ".join(component_skeletons),
    }
