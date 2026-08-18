"""Parse, instantiate, canonicalize, and compare ODEFormer / ODEBench formulas."""

from __future__ import annotations

import math
import re
from typing import Any, Sequence

from gpu_run4.ted import (
    BINARY_OPS,
    CONST_PLACEHOLDER,
    SYMPY_EQUIV_TIMEOUT_SEC,
    SYMPY_MAX_NODES,
    TedTimeout,
    Tree,
    UNARY_OPS,
    canonicalize_tree,
    is_float_token,
    prefix_to_tree,
    quantize_number,
    skeletonize_tree,
    system_ted,
    time_limit,
    tree_size,
    tree_to_prefix,
)

COMPONENT_SEP = "|"
PREFIX_SEP = ",|,"

_SYMPY_FN = {
    "sin": "sin",
    "cos": "cos",
    "exp": "exp",
    "log": "log",
    "tan": "tan",
    "abs": "abs",
    "sqrt": "sqrt",
    "asin": "arcsin",
    "acos": "arccos",
    "atan": "arctan",
}


def split_components(text: str) -> list[str]:
    """Split a system on `|` without reordering components."""
    if text is None:
        return []
    raw = str(text).strip()
    if not raw:
        return []
    if PREFIX_SEP in raw and "," in raw:
        parts = raw.split(PREFIX_SEP)
    else:
        parts = raw.split(COMPONENT_SEP)
    return [part.strip().strip(",") for part in parts if part.strip().strip(",")]


def join_prefix_system(components: Sequence[Sequence[str]]) -> str:
    return PREFIX_SEP.join(",".join(part) for part in components)


def tree_to_infix(tree: Tree | None) -> str:
    if tree is None:
        return ""
    label, children = tree
    if not children:
        return label
    args = [tree_to_infix(child) for child in children]
    if label == "add":
        return f"({args[0]} + {args[1]})"
    if label == "mul":
        return f"({args[0]} * {args[1]})"
    if label == "sub":
        return f"({args[0]} - {args[1]})"
    if label == "div":
        return f"({args[0]} / {args[1]})"
    if label == "pow":
        return f"({args[0]} ** {args[1]})"
    if label == "neg":
        return f"(-{args[0]})"
    if label == "inv":
        return f"(1 / {args[0]})"
    if len(args) == 1:
        return f"{label}({args[0]})"
    return f"{label}({', '.join(args)})"


def join_infix_system(components: Sequence[Tree | None]) -> str:
    return f" {COMPONENT_SEP} ".join(tree_to_infix(tree) for tree in components)


def join_canonical_system(components: Sequence[Tree | None]) -> str:
    rendered = []
    for tree in components:
        rendered.append(",".join(tree_to_prefix(tree)) if tree is not None else "")
    return PREFIX_SEP.join(rendered)


def instantiate_constants(eq: str, consts: Sequence[float] | None) -> str:
    if not consts:
        return eq
    out = eq
    for index in sorted(range(len(consts)), reverse=True):
        out = re.sub(rf"\bc_{index}\b", quantize_number(float(consts[index])), out)
    return out


def _prepare_infix(expr: str) -> str:
    text = expr.replace("^", "**")
    text = text.replace(" ", "")
    return text


def _sympy_local_dict():
    import sympy as sp

    local: dict[str, Any] = {
        "e": sp.E,
        "pi": sp.pi,
        "Abs": sp.Abs,
        "abs": sp.Abs,
        "log": sp.log,
        "ln": sp.log,
        "exp": sp.exp,
        "sin": sp.sin,
        "cos": sp.cos,
        "tan": sp.tan,
        "cot": sp.cot,
        "sec": sp.sec,
        "csc": sp.csc,
        "sqrt": sp.sqrt,
        "asin": sp.asin,
        "acos": sp.acos,
        "atan": sp.atan,
    }
    for index in range(24):
        local[f"x_{index}"] = sp.Symbol(f"x_{index}", real=True)
        local[f"c_{index}"] = sp.Symbol(f"c_{index}", real=True)
    return local


def _sympy_to_tree(expr: Any) -> Tree:
    import sympy as sp

    if expr is None:
        raise ValueError("empty sympy expression")
    if expr.is_Number:
        if expr.is_infinite:
            raise ValueError("Inf")
        if expr.has(sp.nan):
            raise ValueError("NaN")
        return (quantize_number(float(expr)), ())
    if expr.is_Symbol:
        return (str(expr), ())
    if expr.func == sp.Add:
        args = [_sympy_to_tree(arg) for arg in expr.args]
        tree: Tree = args[0]
        for arg in args[1:]:
            tree = ("add", (tree, arg))
        return tree
    if expr.func == sp.Mul:
        args = list(expr.args)
        sign = 1
        rest = []
        for arg in args:
            if arg == -1:
                sign *= -1
                continue
            rest.append(_sympy_to_tree(arg))
        if not rest:
            return (quantize_number(float(sign)), ())
        tree = rest[0]
        for arg in rest[1:]:
            tree = ("mul", (tree, arg))
        if sign < 0:
            tree = ("neg", (tree,))
        return tree
    if expr.func == sp.Pow:
        base, exp = expr.args
        if exp == -1:
            return ("inv", (_sympy_to_tree(base),))
        if base == sp.E:
            return ("exp", (_sympy_to_tree(exp),))
        if exp == sp.Rational(1, 2):
            return ("sqrt", (_sympy_to_tree(base),))
        return ("pow", (_sympy_to_tree(base), _sympy_to_tree(exp)))
    if expr.func == sp.exp:
        return ("exp", (_sympy_to_tree(expr.args[0]),))
    if expr.func == sp.log:
        return ("log", (_sympy_to_tree(expr.args[0]),))
    if expr.func == sp.sin:
        return ("sin", (_sympy_to_tree(expr.args[0]),))
    if expr.func == sp.cos:
        return ("cos", (_sympy_to_tree(expr.args[0]),))
    if expr.func == sp.tan:
        return ("tan", (_sympy_to_tree(expr.args[0]),))
    if expr.func == sp.Abs:
        return ("abs", (_sympy_to_tree(expr.args[0]),))
    if expr.func == sp.sqrt:
        return ("sqrt", (_sympy_to_tree(expr.args[0]),))
    if expr.func == sp.asin:
        return ("arcsin", (_sympy_to_tree(expr.args[0]),))
    if expr.func == sp.acos:
        return ("arccos", (_sympy_to_tree(expr.args[0]),))
    if expr.func == sp.atan:
        return ("arctan", (_sympy_to_tree(expr.args[0]),))
    if expr.func == sp.cot:
        arg = _sympy_to_tree(expr.args[0])
        return ("mul", (("cos", (arg,)), ("inv", (("sin", (arg,)),))))
    if expr.func == sp.sec:
        return ("inv", (("cos", (_sympy_to_tree(expr.args[0]),)),))
    if expr.func == sp.csc:
        return ("inv", (("sin", (_sympy_to_tree(expr.args[0]),)),))
    raise ValueError(f"unsupported sympy node: {expr.func}")


def parse_infix_component(expr: str) -> Tree | None:
    if not str(expr).strip():
        return None
    from sympy.parsing.sympy_parser import parse_expr

    prepared = _prepare_infix(expr)
    try:
        with time_limit(SYMPY_EQUIV_TIMEOUT_SEC):
            parsed = parse_expr(prepared, local_dict=_sympy_local_dict(), evaluate=True)
            return canonicalize_tree(_sympy_to_tree(parsed))
    except TedTimeout:
        return None
    except Exception:
        try:
            with time_limit(SYMPY_EQUIV_TIMEOUT_SEC):
                parsed = parse_expr(prepared, local_dict=_sympy_local_dict(), evaluate=False)
                return canonicalize_tree(_sympy_to_tree(parsed))
        except Exception:
            return None


def parse_prefix_component(prefix: Sequence[str] | str) -> Tree | None:
    if isinstance(prefix, str):
        tokens = [tok for tok in prefix.split(",") if tok]
    else:
        tokens = list(prefix)
    return canonicalize_tree(prefix_to_tree(tokens))


def parse_system(text: str, *, as_prefix: bool | None = None) -> dict[str, Any]:
    """Parse a possibly multi-component ODE. Component order is preserved."""
    raw = str(text)
    if as_prefix is not None:
        looks_prefix = bool(as_prefix)
    else:
        tokens = [tok for tok in raw.split(",") if tok]
        looks_prefix = PREFIX_SEP in raw or (
            "," in raw and " " not in raw and any(tok in UNARY_OPS or tok in BINARY_OPS for tok in tokens)
        )
    parts = split_components(raw)
    trees: list[Tree | None] = []
    failure = None
    for part in parts:
        tree = parse_prefix_component(part) if looks_prefix and "," in part else parse_infix_component(part)
        if tree is None:
            failure = "ParseError"
        trees.append(tree)
    if not parts:
        failure = "ParseError"
    return {
        "raw": raw,
        "components_raw": parts,
        "components": trees,
        "prefix": [tree_to_prefix(tree) if tree is not None else [] for tree in trees],
        "infix": join_infix_system(trees),
        "canonical": join_canonical_system(trees),
        "skeleton": join_canonical_system([skeletonize_tree(tree) for tree in trees]),
        "dimension": len(parts),
        "valid": failure is None and all(tree is not None for tree in trees),
        "failure_reason": failure,
        "complexity": sum(tree_size(tree) for tree in trees),
    }


def formula_views(text: str, *, as_prefix: bool | None = None) -> dict[str, Any]:
    parsed = parse_system(text, as_prefix=as_prefix)
    return {
        "raw_expr": parsed["raw"],
        "true_formula_raw": parsed["raw"],
        "true_formula_infix": parsed["infix"],
        "true_formula_prefix": join_prefix_system(parsed["prefix"]),
        "true_formula_canonical": parsed["canonical"],
        "true_formula_skeleton": parsed["skeleton"],
        "dimension": parsed["dimension"],
        "complexity": parsed["complexity"],
        "valid": parsed["valid"],
        "failure_reason": parsed["failure_reason"],
        "components": parsed["components"],
        "components_raw": parsed["components_raw"],
    }


def _collect_symbols(tree: Tree | None) -> list[str]:
    found: list[str] = []

    def walk(node: Tree) -> None:
        label, children = node
        if not children and not is_float_token(label) and label not in {CONST_PLACEHOLDER, "CONSTANT"}:
            if label not in found:
                found.append(label)
        for child in children:
            walk(child)

    if tree is not None:
        walk(tree)
    return found


def _eval_tree(tree: Tree, values: dict[str, float]) -> float:
    label, children = tree
    if not children:
        if is_float_token(label):
            return float(label)
        if label not in values:
            raise KeyError(label)
        return float(values[label])
    try:
        args = [_eval_tree(child, values) for child in children]
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
            return 1.0 / args[0]
        if label == "sin":
            return math.sin(args[0])
        if label == "cos":
            return math.cos(args[0])
        if label == "exp":
            return math.exp(args[0])
        if label == "log":
            return math.log(args[0])
        if label == "tan":
            return math.tan(args[0])
        if label == "abs":
            return abs(args[0])
        if label == "sqrt":
            return math.sqrt(args[0])
    except ZeroDivisionError:
        return float("inf")
    except (ValueError, OverflowError, ArithmeticError):
        return float("nan")
    raise ValueError(f"unsupported eval op: {label}")


def numeric_equivalent(
    true_components: Sequence[Tree | None],
    pred_components: Sequence[Tree | None],
    *,
    n_points: int = 32,
    seed: int = 0,
    rtol: float = 1e-5,
    atol: float = 1e-6,
    points: Sequence[dict[str, float]] | None = None,
) -> dict[str, Any]:
    """Safe-domain numeric check. Singular / non-finite points are recorded, not forced equal."""
    import numpy as np

    if len(true_components) != len(pred_components):
        return {"equivalent": False, "finite_points": 0, "failure_reason": "ParseError"}
    if any(tree is None for tree in (*true_components, *pred_components)):
        return {"equivalent": False, "finite_points": 0, "failure_reason": "ParseError"}
    symbols: list[str] = []
    for tree in true_components:
        for name in _collect_symbols(tree):
            if name not in symbols:
                symbols.append(name)
    rng = np.random.default_rng(int(seed))
    finite = 0
    matched = 0
    nan_or_inf = 0
    samples: list[dict[str, float]]
    if points is not None:
        samples = [dict(point) for point in points]
    else:
        samples = [{name: float(rng.uniform(0.2, 1.8)) for name in symbols} for _ in range(n_points)]
    try:
        for values in samples:
            true_vals = [_eval_tree(tree, values) for tree in true_components]  # type: ignore[arg-type]
            pred_vals = [_eval_tree(tree, values) for tree in pred_components]  # type: ignore[arg-type]
            if not np.all(np.isfinite(true_vals)) or not np.all(np.isfinite(pred_vals)):
                nan_or_inf += 1
                continue
            finite += 1
            if all(abs(a - b) <= atol + rtol * abs(a) for a, b in zip(true_vals, pred_vals)):
                matched += 1
    except Exception as exc:
        return {
            "equivalent": False,
            "finite_points": finite,
            "matched_points": matched,
            "nan_or_inf": nan_or_inf,
            "failure_reason": "NaN" if "division" in str(exc).lower() else type(exc).__name__,
        }
    if finite == 0:
        return {
            "equivalent": False,
            "finite_points": 0,
            "matched_points": 0,
            "nan_or_inf": nan_or_inf,
            "failure_reason": "Inf" if nan_or_inf else "ParseError",
        }
    return {
        "equivalent": matched == finite,
        "finite_points": finite,
        "matched_points": matched,
        "nan_or_inf": nan_or_inf,
        "failure_reason": None,
    }


def _sympy_components_equal(true_components: Sequence[Tree | None], pred_components: Sequence[Tree | None]) -> tuple[float, str | None]:
    if len(true_components) != len(pred_components):
        return 0.0, None
    import sympy as sp

    local = _sympy_local_dict()
    nodes = sum(tree_size(tree) for tree in true_components) + sum(tree_size(tree) for tree in pred_components)
    if nodes > SYMPY_MAX_NODES:
        return 0.0, None
    try:
        with time_limit(SYMPY_EQUIV_TIMEOUT_SEC):
            for true_tree, pred_tree in zip(true_components, pred_components):
                if true_tree is None or pred_tree is None:
                    return 0.0, "ParseError"
                true_infix = _tree_to_sympy_infix(true_tree)
                pred_infix = _tree_to_sympy_infix(pred_tree)
                true_expr = sp.sympify(true_infix, locals=local)
                pred_expr = sp.sympify(pred_infix, locals=local)
                diff = sp.simplify(true_expr - pred_expr)
                if diff != 0 and not true_expr.equals(pred_expr):
                    return 0.0, None
        return 1.0, None
    except TedTimeout:
        return 0.0, "SymbolicEquivalenceTimeout"
    except Exception:
        return 0.0, None


def _tree_to_sympy_infix(tree: Tree) -> str:
    label, children = tree
    if not children:
        return label
    args = [_tree_to_sympy_infix(child) for child in children]
    if label == "add":
        return f"({args[0]})+({args[1]})"
    if label == "mul":
        return f"({args[0]})*({args[1]})"
    if label == "sub":
        return f"({args[0]})-({args[1]})"
    if label == "div":
        return f"({args[0]})/({args[1]})"
    if label == "pow":
        return f"({args[0]})**({args[1]})"
    if label == "neg":
        return f"-({args[0]})"
    if label == "inv":
        return f"1/({args[0]})"
    if label in _SYMPY_FN:
        return f"{_SYMPY_FN[label]}({args[0]})"
    raise ValueError(label)


def compare_formulas(
    true_text: str,
    pred_text: str,
    *,
    as_prefix: bool | None = None,
    true_as_prefix: bool | None = None,
    pred_as_prefix: bool | None = None,
) -> dict[str, Any]:
    true_views = formula_views(true_text, as_prefix=true_as_prefix if true_as_prefix is not None else as_prefix)
    pred_views = formula_views(pred_text, as_prefix=pred_as_prefix if pred_as_prefix is not None else as_prefix)
    metrics = system_ted(true_views["components"], pred_views["components"])
    symbolic = 0.0
    symbolic_failure = None
    if metrics["canonical_exact"] == 1.0:
        symbolic = 1.0
    else:
        symbolic, symbolic_failure = _sympy_components_equal(true_views["components"], pred_views["components"])
        if symbolic != 1.0 and symbolic_failure is None:
            numeric = numeric_equivalent(true_views["components"], pred_views["components"])
            if numeric["equivalent"]:
                symbolic = 1.0
            elif numeric.get("failure_reason") in {"Inf", "NaN"}:
                symbolic_failure = numeric["failure_reason"]
    failure = pred_views["failure_reason"] or metrics["failure_reason"] or symbolic_failure
    return {
        "true_formula_raw": true_views["true_formula_raw"],
        "true_formula_prefix": true_views["true_formula_prefix"],
        "true_formula_canonical": true_views["true_formula_canonical"],
        "true_formula_skeleton": true_views["true_formula_skeleton"],
        "pred_formula_raw": pred_views["raw_expr"],
        "pred_formula_prefix": pred_views["true_formula_prefix"],
        "pred_formula_canonical": pred_views["true_formula_canonical"],
        "pred_formula_skeleton": pred_views["true_formula_skeleton"],
        "canonical_exact": metrics["canonical_exact"],
        "skeleton_exact": metrics["skeleton_exact"],
        "symbolic_equivalent": symbolic,
        "ted_raw": metrics["ted_raw"],
        "ted_skeleton": metrics["ted_skeleton"],
        "normalized_ted": metrics["normalized_ted"],
        "complexity": pred_views["complexity"],
        "valid": bool(pred_views["valid"]),
        "failure_reason": failure,
        "dimension_true": true_views["dimension"],
        "dimension_pred": pred_views["dimension"],
        "component_count_match": metrics["component_count_match"],
    }


def instantiate_odebench_item(item: dict[str, Any]) -> dict[str, Any]:
    raw = str(item["eq"])
    consts = list((item.get("consts") or [[]])[0])
    instantiated = instantiate_constants(raw, consts)
    views = formula_views(instantiated)
    structural = formula_views(raw)
    return {
        "id": int(item["id"]),
        "system_name": str(item.get("eq_description") or item["id"]),
        "dimension": int(item["dim"]),
        "true_formula_raw": raw,
        "true_formula_instantiated": instantiated,
        "true_formula_infix": views["true_formula_infix"],
        "true_formula_prefix": views["true_formula_prefix"],
        "true_formula_canonical": views["true_formula_canonical"],
        "true_formula_skeleton": views["true_formula_skeleton"],
        "structural_canonical": structural["true_formula_canonical"],
        "structural_skeleton": structural["true_formula_skeleton"],
        "n_init": len(item.get("init") or []),
        "valid": views["valid"] and structural["valid"],
        "failure_reason": views["failure_reason"] or structural["failure_reason"],
        "complexity": views["complexity"],
        "source": item.get("source"),
    }


GOLD_CASES: list[dict[str, Any]] = [
    {
        "name": "commutative_add",
        "true": "x_0 + x_1",
        "pred": "x_1 + x_0",
        "expect_equivalent": True,
        "expect_canonical_exact": True,
        "expect_different": False,
    },
    {
        "name": "commutative_mul",
        "true": "c_0 * x_0",
        "pred": "x_0 * c_0",
        "expect_equivalent": True,
        "expect_canonical_exact": True,
        "expect_different": False,
    },
    {
        "name": "associative_add",
        "true": "(x_0 + x_1) + x_2",
        "pred": "x_0 + (x_1 + x_2)",
        "expect_equivalent": True,
        "expect_canonical_exact": True,
        "expect_different": False,
    },
    {
        "name": "reciprocal_as_inv",
        "true": "x_0 / x_1",
        "pred": "x_0 * (1 / x_1)",
        "expect_equivalent": True,
        "expect_canonical_exact": True,
        "expect_different": False,
    },
    {
        "name": "negative_constant",
        "true": "-x_0",
        "pred": "(-1) * x_0",
        "expect_equivalent": True,
        "expect_canonical_exact": True,
        "expect_different": False,
    },
    {
        "name": "sub_as_add_neg",
        "true": "x_0 - x_1",
        "pred": "x_0 + (-x_1)",
        "expect_equivalent": True,
        "expect_canonical_exact": True,
        "expect_different": False,
    },
    {
        "name": "component_order_preserved",
        "true": "x_0 | x_1",
        "pred": "x_1 | x_0",
        "expect_equivalent": False,
        "expect_canonical_exact": False,
        "expect_different": True,
        "expect_component_count_match": True,
    },
    {
        "name": "intentionally_different_sign",
        "true": "x_0 + x_1",
        "pred": "x_0 - x_1",
        "expect_equivalent": False,
        "expect_canonical_exact": False,
        "expect_different": True,
    },
    {
        "name": "intentionally_different_variable",
        "true": "c_0 * x_0",
        "pred": "c_0 * x_1",
        "expect_equivalent": False,
        "expect_canonical_exact": False,
        "expect_different": True,
    },
    {
        "name": "skeleton_ignores_constant",
        "true": "2 * x_0",
        "pred": "3 * x_0",
        "expect_equivalent": False,
        "expect_skeleton_exact": True,
        "expect_different": True,
    },
    {
        "name": "parse_failure_recorded",
        "true": "x_0",
        "pred": "this is not an ode )))",
        "expect_equivalent": False,
        "expect_valid": False,
        "expect_failure": "ParseError",
        "expect_different": True,
    },
]


def evaluate_gold_cases(cases: Sequence[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    rows = []
    for case in cases or GOLD_CASES:
        comparison = compare_formulas(case["true"], case["pred"])
        ok = True
        reasons: list[str] = []
        if "expect_equivalent" in case and bool(comparison["symbolic_equivalent"]) != bool(case["expect_equivalent"]):
            ok = False
            reasons.append("symbolic_equivalent")
        if "expect_canonical_exact" in case and bool(comparison["canonical_exact"]) != bool(case["expect_canonical_exact"]):
            ok = False
            reasons.append("canonical_exact")
        if "expect_skeleton_exact" in case and bool(comparison["skeleton_exact"]) != bool(case["expect_skeleton_exact"]):
            ok = False
            reasons.append("skeleton_exact")
        if "expect_valid" in case and bool(comparison["valid"]) != bool(case["expect_valid"]):
            ok = False
            reasons.append("valid")
        if "expect_failure" in case and comparison["failure_reason"] != case["expect_failure"]:
            ok = False
            reasons.append("failure_reason")
        if case.get("expect_component_count_match") is True and not comparison["component_count_match"]:
            ok = False
            reasons.append("component_count_match")
        if case.get("expect_different") and comparison["canonical_exact"] == 1.0 and comparison["symbolic_equivalent"] == 1.0:
            ok = False
            reasons.append("false_positive")
        rows.append({"name": case["name"], "ok": ok, "failed_checks": reasons, **comparison})
    return rows


def timeout_probe(*, seconds: float = 0.05) -> dict[str, Any]:
    """Confirm the SIGALRM guard records a timeout instead of hanging."""
    import time

    started = time.perf_counter()
    try:
        with time_limit(seconds):
            time.sleep(float(seconds) + 1.0)
        triggered = False
        reason = None
    except TedTimeout:
        triggered = True
        reason = "TEDTimeout"
    elapsed = time.perf_counter() - started
    return {
        "triggered": triggered,
        "failure_reason": reason,
        "budget_sec": seconds,
        "elapsed_sec": elapsed,
        "ok": triggered and reason == "TEDTimeout" and elapsed < float(seconds) + 0.5,
    }


def singularity_probe() -> dict[str, Any]:
    """1/x at x=0 must be recorded as Inf/NaN, not forced equivalent."""
    views = parse_system("1 / x_0")
    numeric = numeric_equivalent(
        views["components"],
        views["components"],
        points=[{"x_0": 0.0}],
    )
    ok = (
        numeric.get("equivalent") is False
        and numeric.get("finite_points") == 0
        and numeric.get("failure_reason") in {"Inf", "NaN"}
        and numeric.get("nan_or_inf", 0) >= 1
    )
    return {
        "ok": ok,
        "formula": "1 / x_0",
        "point": {"x_0": 0.0},
        **numeric,
    }
