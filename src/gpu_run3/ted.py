"""Tree-edit-distance metrics for ND2 prefix formulas."""

from __future__ import annotations

import itertools
import math
from typing import Any, Sequence

from gpu_run3_runtime import install_nd2_path

NETWORK_OPS = frozenset({"aggr", "rgga", "sour", "targ"})
COMMUTATIVE = frozenset({"add", "mul"})


def _is_float_token(token: str) -> bool:
    try:
        float(token)
    except (TypeError, ValueError):
        return False
    return token not in {"inf", "nan", "+inf", "-inf"}


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
        variable, variable_status = _variable_aware_ted(true_tree, pred_tree, max_variable_permutations)
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
    """Conservative equivalence: canonical prefix match, else sympy if no network ops."""
    metrics = ted_metrics(true_prefix, pred_prefix, variable_aware=False)
    if metrics["exact"] == 1.0:
        return 1.0
    true_tokens = [str(t) for t in true_prefix]
    pred_tokens = [str(t) for t in pred_prefix]
    if NETWORK_OPS.intersection(true_tokens) or NETWORK_OPS.intersection(pred_tokens):
        return float(metrics["skeleton"] == 1.0 and metrics["exact"] == 1.0)
    try:
        install_nd2_path()
        from ND2.GDExpr import GDExpr

        true_expr = GDExpr.parse_expr(GDExpr.prefix2str(list(true_prefix)))
        pred_expr = GDExpr.parse_expr(GDExpr.prefix2str(list(pred_prefix)))
        return float(bool(true_expr.equals(pred_expr) or (true_expr - pred_expr).simplify() == 0))
    except Exception:
        return 0.0
