"""GPU_RUN2 operator allowlist, power-exponent filter, and division safety."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import numpy as np
import sympy as sp

DEFAULT_ALLOWED_POW_EXPONENTS = frozenset({2, 3, 4, 5})
DEFAULT_DENOMINATOR_MARGIN = 1e-6
DISALLOWED_FUNCTION_NAMES = frozenset(
    {
        "sin",
        "cos",
        "tan",
        "asin",
        "acos",
        "atan",
        "sinh",
        "cosh",
        "tanh",
        "coth",
        "exp",
        "ln",
        "log",
        "sqrt",
        "abs",
    }
)
NESYMRES_ALLOWED_TOKENS = frozenset({"add", "sub", "mul", "div", "pow"})
PYSR_BINARY_OPERATORS = ("+", "-", "*", "/")
PYSR_UNARY_OPERATORS = (
    "square(x) = x^2",
    "cube(x) = x^3",
    "pow4(x) = x^4",
    "pow5(x) = x^5",
)
_TOKEN_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


class DisallowedPowerExponent(ValueError):
    """Raised when a candidate uses a power exponent outside literal 2–5."""


class DisallowedOperator(ValueError):
    """Raised when a candidate uses a function outside the GPU_RUN2 allowlist."""


class UnsafeDivision(ValueError):
    """Raised when a candidate denominator is too small or non-finite."""


def load_operator_config(path: Path | None = None) -> dict[str, Any]:
    if path is None:
        from gpu_run2_runtime import GPU_RUN2_CONFIG_DIR, load_yaml_mapping

        path = GPU_RUN2_CONFIG_DIR / "operators.yaml"
    from gpu_run2_runtime import load_yaml_mapping

    return load_yaml_mapping(path)


def allowed_pow_exponents(config: Mapping[str, Any] | None = None) -> frozenset[int]:
    if not config:
        return DEFAULT_ALLOWED_POW_EXPONENTS
    values = config.get("allowed_pow_exponents") or config.get("nesymres", {}).get(
        "allowed_pow_exponents"
    )
    if not values:
        return DEFAULT_ALLOWED_POW_EXPONENTS
    return frozenset(int(v) for v in values)


def nesymres_disallowed_token_ids(
    word2id: Mapping[str, int],
    *,
    config: Mapping[str, Any] | None = None,
) -> dict[str, int]:
    """Token ids that must not be emitted during GPU_RUN2 decode."""
    cfg = dict(config or {})
    names = cfg.get("nesymres", {}).get("disallowed_tokens") or sorted(DISALLOWED_FUNCTION_NAMES)
    return {name: int(word2id[name]) for name in names if name in word2id}


def nesymres_allowed_token_ids(
    word2id: Mapping[str, int],
    *,
    config: Mapping[str, Any] | None = None,
) -> set[int]:
    """Ids that remain legal after masking disallowed functions."""
    banned = set(nesymres_disallowed_token_ids(word2id, config=config).values())
    return {int(i) for i in word2id.values() if int(i) not in banned}


def pysr_operator_kwargs(config: Mapping[str, Any] | None = None) -> dict[str, Any]:
    cfg = (config or {}).get("pysr", {}) if config else {}
    binary = list(cfg.get("binary_operators") or PYSR_BINARY_OPERATORS)
    unary_names = list(cfg.get("unary_operators") or ["square", "cube", "pow4", "pow5"])
    unary = []
    mapping = {
        "square": "square(x) = x^2",
        "cube": "cube(x) = x^3",
        "pow4": "pow4(x) = x^4",
        "pow5": "pow5(x) = x^5",
    }
    for name in unary_names:
        unary.append(mapping.get(str(name), str(name)))
    if "^" in binary or "**" in binary:
        raise ValueError("GPU_RUN2 PySR must not use binary exponentiation")
    return {
        "binary_operators": binary,
        "unary_operators": unary,
    }


def expression_tokens(expr: str) -> set[str]:
    return set(_TOKEN_RE.findall(expr or ""))


def check_disallowed_functions(expr: str) -> str | None:
    tokens = {tok.lower() for tok in expression_tokens(expr)}
    banned = tokens & DISALLOWED_FUNCTION_NAMES
    if banned:
        return f"DisallowedOperator:{sorted(banned)[0]}"
    return None


def check_power_exponents(
    expr: str,
    *,
    allowed: Iterable[int] = DEFAULT_ALLOWED_POW_EXPONENTS,
) -> str | None:
    """Return a failure reason if any Pow exponent is outside literal integers 2–5."""
    text = (expr or "").strip()
    if not text:
        return None
    try:
        parsed = sp.sympify(text.replace("^", "**"), evaluate=False)
    except Exception:
        try:
            parsed = sp.sympify(text.replace("^", "**"))
        except Exception:
            return None
    allowed_set = {int(v) for v in allowed}

    def _walk(node: sp.Expr) -> str | None:
        if isinstance(node, sp.Pow):
            exponent = node.exp
            # SymPy encodes a/b as a * b**(-1). That is division, not integer pow.
            if exponent == -1:
                return _walk(node.base)
            if exponent == 1:
                return _walk(node.base)
            if exponent.is_Integer and int(exponent) in allowed_set:
                return _walk(node.base)
            return "DisallowedPowerExponent"
        for arg in getattr(node, "args", ()):
            reason = _walk(arg)
            if reason:
                return reason
        return None

    return _walk(parsed)


def denominator_values(
    expr: str,
    X: np.ndarray,
    variable_names: Sequence[str],
) -> np.ndarray | None:
    text = (expr or "").strip()
    if not text:
        return None
    try:
        parsed = sp.sympify(text.replace("^", "**"))
        denominator = sp.denom(sp.together(parsed))
        if denominator == 1:
            return np.ones(len(X), dtype=float)
        env = {}
        for i, name in enumerate(variable_names):
            if i < np.asarray(X).shape[1]:
                env[sp.Symbol(name)] = np.asarray(X[:, i], dtype=float)
        missing = [sym for sym in denominator.free_symbols if sym not in env]
        for sym in missing:
            env[sym] = np.ones(len(X), dtype=float)
        fn = sp.lambdify(list(env), denominator, modules=["numpy"])
        with np.errstate(all="ignore"):
            values = np.asarray(fn(*env.values()), dtype=float)
        return np.broadcast_to(values, (len(X),)).ravel()
    except Exception:
        return None


def check_division_safety(
    expr: str,
    point_sets: Mapping[str, tuple[np.ndarray, Sequence[str]]],
    *,
    margin: float = DEFAULT_DENOMINATOR_MARGIN,
) -> str | None:
    """Inspect train / validation / domain-ID / domain-OOD denominators."""
    text = (expr or "").strip()
    if not text:
        return "empty_expression"
    for split_name, (X, names) in point_sets.items():
        if X is None or len(X) == 0:
            continue
        values = denominator_values(text, np.asarray(X, dtype=float), names)
        if values is None:
            if "/" in text or "div" in text.lower():
                return f"UnsafeDivision:{split_name}:unparseable_denominator"
            continue
        if not np.all(np.isfinite(values)):
            return f"UnsafeDivision:{split_name}:nonfinite"
        if float(np.min(np.abs(values))) < float(margin):
            return f"UnsafeDivision:{split_name}:margin"
    return None


def validate_candidate_expression(
    expr: str,
    *,
    point_sets: Mapping[str, tuple[np.ndarray, Sequence[str]]] | None = None,
    margin: float = DEFAULT_DENOMINATOR_MARGIN,
    allowed_exponents: Iterable[int] = DEFAULT_ALLOWED_POW_EXPONENTS,
) -> tuple[bool, str | None]:
    """Return ``(ok, failure_reason)`` for a GPU_RUN2 candidate equation."""
    reason = check_disallowed_functions(expr)
    if reason:
        return False, reason
    reason = check_power_exponents(expr, allowed=allowed_exponents)
    if reason:
        return False, reason
    if point_sets:
        reason = check_division_safety(expr, point_sets, margin=margin)
        if reason:
            return False, reason
    return True, None


def filter_prefix_tokens(
    token_names: Sequence[str],
    *,
    allowed_exponents: Iterable[int] = DEFAULT_ALLOWED_POW_EXPONENTS,
) -> tuple[bool, str | None]:
    """Validate a NeSymReS prefix token sequence, including pow exponent children."""
    allowed = {str(int(v)) for v in allowed_exponents}
    names = [str(tok) for tok in token_names]
    for index, name in enumerate(names):
        lowered = name.lower()
        if lowered in DISALLOWED_FUNCTION_NAMES:
            return False, f"DisallowedOperator:{lowered}"
        if lowered == "pow":
            if index + 2 >= len(names):
                return False, "DisallowedPowerExponent"
            exponent_token = names[index + 2]
            if exponent_token not in allowed:
                return False, "DisallowedPowerExponent"
    return True, None
