"""Tree-edit-distance metrics for ND2 prefix formulas."""

from __future__ import annotations

import itertools
import math
import os
import signal
from contextlib import contextmanager
from typing import Any, Sequence

from gpu_run3_runtime import install_nd2_path

# plan section 16.1 requires a TED timeout. Without one, sympy's equals()/simplify()
# on a degenerate 30-token rollout formula can run effectively forever: one such
# formula stalled a Phase 5 run for over eight hours with no output.
TED_TIMEOUT_SEC = float(os.environ.get("LANSR_TED_TIMEOUT_SEC", "10"))
SYMPY_MAX_TOKENS = int(os.environ.get("LANSR_SYMPY_MAX_TOKENS", "24"))


class TedTimeout(Exception):
    """Raised when a structural comparison exceeds its time budget."""


@contextmanager
def _time_limit(seconds: float):
    """Wall-clock guard around an unbounded symbolic computation.

    SIGALRM only works on the main thread; elsewhere this degrades to no limit
    rather than raising, so callers still get an answer.
    """
    if seconds <= 0:
        yield
        return
    try:
        previous = signal.getsignal(signal.SIGALRM)
    except (ValueError, AttributeError):
        yield
        return

    def _handler(_signum, _frame):
        raise TedTimeout(f"exceeded {seconds}s")

    try:
        signal.signal(signal.SIGALRM, _handler)
        signal.setitimer(signal.ITIMER_REAL, float(seconds))
    except ValueError:
        # Not the main thread.
        yield
        return
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0.0)
        signal.signal(signal.SIGALRM, previous)

NETWORK_OPS = frozenset({"aggr", "rgga", "sour", "targ"})
COMMUTATIVE = frozenset({"add", "mul"})

# Constants recovered by BFGS never land exactly on the literal in the ground-truth
# formula, and MCTS routinely emits identity terms such as `0 + x` or `1 * x`.
# Canonicalization therefore folds numeric identities and compares numeric leaves
# at 4 significant digits. Fixed before any test-split evaluation (plan 11).
NUMERIC_SIGNIFICANT_DIGITS = 4
IDENTITY_ATOL = 1e-4

_NAMED_CONSTANTS = {"(1/2)": 0.5, "(1/3)": 1.0 / 3.0, "(1/4)": 0.25, "(1/5)": 0.2}


def _is_float_token(token: str) -> bool:
    try:
        float(token)
    except (TypeError, ValueError):
        return False
    return token not in {"inf", "nan", "+inf", "-inf"}


def numeric_value(label: str) -> float | None:
    """Numeric value of a leaf label, or None when it is not a literal."""
    if label in _NAMED_CONSTANTS:
        return _NAMED_CONSTANTS[label]
    if _is_float_token(label):
        return float(label)
    return None


def _quantize(label: str) -> str:
    value = numeric_value(label)
    if value is None:
        return label
    return f"{value:.{NUMERIC_SIGNIFICANT_DIGITS}g}"


def _leaf_number(node: tuple[str, tuple]) -> float | None:
    label, children = node
    return numeric_value(label) if not children else None


def _close(value: float | None, target: float) -> bool:
    return value is not None and abs(value - target) <= IDENTITY_ATOL


def _normalize_signs(label: str, children: tuple) -> tuple[str, tuple]:
    """Put subtraction and negation into one form: `a - b` and `-1 * b` become `a + neg(b)`.

    plan section 11 requires the treatment of signs to be fixed before evaluation.
    Without this, `aggr(sour(regular(x,2))) - x` and `(-1*x) + aggr(sour(regular(x,2)))`
    -- the same expression -- score as a structural miss.
    """
    if label == "sub" and len(children) == 2:
        left, right = children
        return "add", (left, ("neg", (right,)))
    if label == "mul" and len(children) == 2:
        left, right = children
        if _close(_leaf_number(left), -1.0):
            return "neg", (right,)
        if _close(_leaf_number(right), -1.0):
            return "neg", (left,)
    if label == "neg" and len(children) == 1:
        inner_label, inner_children = children[0]
        if inner_label == "neg" and len(inner_children) == 1:
            return inner_children[0]  # neg(neg(x)) -> x
        if inner_label == "add" and len(inner_children) == 2:
            # Distribute over addition only: neg(a+b) -> neg(a)+neg(b). Without this,
            # `-(y+z)` and `(-1*z)-y` -- the same expression -- stay structurally apart.
            # Never distribute over mul/div, where one negation is not two.
            return "add", tuple(canonicalize_tree(("neg", (child,))) for child in inner_children)
        value = _leaf_number(children[0])
        if value is not None:
            return _quantize(str(-value)), ()
    return label, children


def _fold_identities(label: str, children: tuple) -> tuple[str, tuple]:
    """Remove arithmetic identity terms so `0 + x` and `1 * x` match `x`."""
    if label == "add" and len(children) == 2:
        # `a + neg(0)` still carries a redundant term after sign normalization.
        left, right = children
        for first, second in ((left, right), (right, left)):
            if first == ("neg", (("0", ()),)) or _close(_leaf_number(first), 0.0):
                return second
    if len(children) == 2:
        left, right = children
        left_value = _leaf_number(left)
        right_value = _leaf_number(right)
        if label == "add":
            if _close(left_value, 0.0):
                return right
            if _close(right_value, 0.0):
                return left
        elif label == "sub":
            if _close(right_value, 0.0):
                return left
        elif label == "mul":
            if _close(left_value, 1.0):
                return right
            if _close(right_value, 1.0):
                return left
            if _close(left_value, 0.0) or _close(right_value, 0.0):
                return ("0", ())
        elif label in {"div", "pow"}:
            if _close(right_value, 1.0):
                return left
    return (label, children)


def prefix_to_tree(prefix: Sequence[str]) -> tuple[str, tuple] | None:
    """Convert a prefix token list to a nested tuple tree. None if parse fails."""
    install_nd2_path()
    from ND2.GDExpr import GDExpr

    tokens = [str(t) for t in prefix]
    if not tokens:
        return None

    def parse(index: int) -> tuple[tuple[str, tuple] | None, int]:
        if index >= len(tokens):
            return None, index
        item = tokens[index]
        index += 1
        if item in GDExpr.operator.unary:
            child, index = parse(index)
            if child is None:
                return None, index
            return (item, (child,)), index
        if item in GDExpr.operator.binary:
            left, index = parse(index)
            right, index = parse(index)
            if left is None or right is None:
                return None, index
            return (item, (left, right)), index
        return (item, ()), index

    tree, rest = parse(0)
    if tree is None or rest != len(tokens):
        return None
    return tree


def canonicalize_tree(tree: tuple[str, tuple] | None) -> tuple[str, tuple] | None:
    if tree is None:
        return None
    label, children = tree
    canon_children = tuple(canonicalize_tree(child) for child in children)
    if any(child is None for child in canon_children):
        return None
    if not canon_children:
        return (_quantize(label), ())
    label, canon_children = _normalize_signs(label, canon_children)
    if not canon_children:
        return (label, ())
    folded_label, folded_children = _fold_identities(label, canon_children)
    if folded_label != label or folded_children is not canon_children:
        # Folding can expose a further identity, e.g. `1 * (0 + x)`.
        if not folded_children:
            return (folded_label, ())
        label, canon_children = folded_label, folded_children
    if label in COMMUTATIVE and len(canon_children) == 2:
        canon_children = tuple(sorted(canon_children, key=lambda item: repr(item)))
    return (label, canon_children)


def skeletonize_tree(tree: tuple[str, tuple] | None) -> tuple[str, tuple] | None:
    if tree is None:
        return None
    label, children = tree
    if _is_float_token(label) or label in {"<C>", "<Cv>", "<Ce>"}:
        label = "CONST"
    return (label, tuple(skeletonize_tree(child) for child in children))


def tree_to_zss(tree: tuple[str, tuple]):
    from zss import Node

    node = Node(tree[0])
    for child in tree[1]:
        node.addkid(tree_to_zss(child))
    return node


def tree_edit_distance(left: tuple[str, tuple] | None, right: tuple[str, tuple] | None) -> float:
    if left is None or right is None:
        return float("nan")
    from zss import simple_distance

    return float(simple_distance(tree_to_zss(left), tree_to_zss(right)))


def ted_metrics(
    true_prefix: Sequence[str],
    pred_prefix: Sequence[str],
    *,
    variable_aware: bool = True,
    max_variable_permutations: int = 24,
) -> dict[str, Any]:
    """Compute ted_raw / ted_skeleton / optional variable-aware TED.

    Parse failures are not dropped: they are recorded as TEDParseError with NaN distances.
    """
    true_tree = canonicalize_tree(prefix_to_tree(true_prefix))
    pred_tree = canonicalize_tree(prefix_to_tree(pred_prefix))
    failure = None
    if true_tree is None or pred_tree is None:
        failure = "TEDParseError"
    raw = tree_edit_distance(true_tree, pred_tree)
    skeleton = tree_edit_distance(skeletonize_tree(true_tree), skeletonize_tree(pred_tree))
    variable = float("nan")
    variable_status = "skipped"
    if variable_aware and true_tree is not None and pred_tree is not None:
        try:
            with _time_limit(TED_TIMEOUT_SEC):
                variable, variable_status = _variable_aware_ted(
                    true_tree, pred_tree, max_variable_permutations
                )
        except TedTimeout:
            variable, variable_status = float("nan"), "TEDTimeout"
            failure = failure or "TEDTimeout"
    return {
        "ted_raw": raw,
        "ted_skeleton": skeleton,
        "ted_variable_aware": variable,
        "ted_variable_aware_status": variable_status,
        "failure_reason": failure,
        "true_tree": true_tree,
        "pred_tree": pred_tree,
        "exact": float(true_tree == pred_tree) if true_tree is not None and pred_tree is not None else 0.0,
        "skeleton": (
            float(skeletonize_tree(true_tree) == skeletonize_tree(pred_tree))
            if true_tree is not None and pred_tree is not None
            else 0.0
        ),
    }


def _collect_variables(tree: tuple[str, tuple]) -> list[str]:
    install_nd2_path()
    from ND2.GDExpr import GDExpr

    found: list[str] = []

    def walk(node: tuple[str, tuple]) -> None:
        label, children = node
        is_op = label in GDExpr.operator.unary or label in GDExpr.operator.binary
        if (not is_op) and (not _is_float_token(label)) and label not in {"CONST", "<C>", "<Cv>", "<Ce>", "node", "edge"}:
            if label not in found:
                found.append(label)
        for child in children:
            walk(child)

    walk(tree)
    return found


def _relabel(tree: tuple[str, tuple], mapping: dict[str, str]) -> tuple[str, tuple]:
    label, children = tree
    return (mapping.get(label, label), tuple(_relabel(child, mapping) for child in children))


def _variable_aware_ted(
    true_tree: tuple[str, tuple],
    pred_tree: tuple[str, tuple],
    max_permutations: int,
) -> tuple[float, str]:
    true_vars = _collect_variables(true_tree)
    pred_vars = _collect_variables(pred_tree)
    if not true_vars or not pred_vars:
        return tree_edit_distance(true_tree, pred_tree), "no_variables"
    if len(pred_vars) > 5 or math.factorial(len(pred_vars)) > max_permutations:
        return tree_edit_distance(true_tree, pred_tree), "retrieved_nearest_ted"
    best = float("inf")
    for perm in itertools.islice(itertools.permutations(true_vars), max_permutations):
        mapping = {src: dst for src, dst in zip(pred_vars, perm)}
        relabeled = canonicalize_tree(_relabel(pred_tree, mapping))
        distance = tree_edit_distance(true_tree, relabeled)
        if distance < best:
            best = distance
    return float(best), "variable_permutation"


def prefixes_symbolically_equivalent(true_prefix: Sequence[str], pred_prefix: Sequence[str]) -> float:
    """Conservative equivalence: canonical prefix match, else sympy if no network ops.

    The sympy branch is both size-capped and wall-clock capped. Exceeding either
    yields 0.0 (not equivalent as far as we could determine) rather than blocking;
    canonical-match and skeleton results above are unaffected.
    """
    metrics = ted_metrics(true_prefix, pred_prefix, variable_aware=False)
    if metrics["exact"] == 1.0:
        return 1.0
    true_tokens = [str(t) for t in true_prefix]
    pred_tokens = [str(t) for t in pred_prefix]
    if NETWORK_OPS.intersection(true_tokens) or NETWORK_OPS.intersection(pred_tokens):
        return float(metrics["skeleton"] == 1.0 and metrics["exact"] == 1.0)
    if max(len(true_tokens), len(pred_tokens)) > SYMPY_MAX_TOKENS:
        return 0.0
    try:
        install_nd2_path()
        from ND2.GDExpr import GDExpr

        with _time_limit(TED_TIMEOUT_SEC):
            true_expr = GDExpr.parse_expr(GDExpr.prefix2str(list(true_prefix)))
            pred_expr = GDExpr.parse_expr(GDExpr.prefix2str(list(pred_prefix)))
            return float(bool(true_expr.equals(pred_expr) or (true_expr - pred_expr).simplify() == 0))
    except TedTimeout:
        return 0.0
    except Exception:
        return 0.0
