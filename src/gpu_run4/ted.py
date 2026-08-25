"""Tree-edit distance, canonicalization, and timed symbolic equivalence for ODE systems."""

from __future__ import annotations

import os
import signal
import time
from contextlib import contextmanager
from typing import Any, Sequence

NUMERIC_SIGNIFICANT_DIGITS = 4
IDENTITY_ATOL = 1e-9
TED_TIMEOUT_SEC = float(os.environ.get("LANSR_TED_TIMEOUT_SEC", "10"))
SYMPY_EQUIV_TIMEOUT_SEC = float(os.environ.get("LANSR_SYMPY_TIMEOUT_SEC", "10"))
SYMPY_MAX_NODES = int(os.environ.get("LANSR_SYMPY_MAX_NODES", "40"))

UNARY_OPS = frozenset(
    {
        "sin",
        "cos",
        "exp",
        "log",
        "tan",
        "abs",
        "sqrt",
        "inv",
        "neg",
        "arcsin",
        "arccos",
        "arctan",
        "pow2",
        "pow3",
        "id",
    }
)
BINARY_OPS = frozenset({"add", "mul", "sub", "div", "pow"})
COMMUTATIVE = frozenset({"add", "mul"})
CONST_PLACEHOLDER = "CONST"

Tree = tuple[str, tuple]


class TedTimeout(Exception):
    """Raised when a structural comparison exceeds its time budget."""


@contextmanager
def time_limit(seconds: float):
    """Nested-safe wall-clock guard. SIGALRM works only on the main thread."""
    if seconds <= 0:
        yield
        return
    try:
        previous = signal.getsignal(signal.SIGALRM)
        previous_delay, previous_interval = signal.getitimer(signal.ITIMER_REAL)
    except (ValueError, AttributeError):
        yield
        return

    def _handler(_signum, _frame):
        raise TedTimeout(f"exceeded {seconds}s")

    started = time.monotonic()
    effective_seconds = min(
        float(seconds),
        previous_delay if previous_delay > 0.0 else float(seconds),
    )
    handler_installed = False
    try:
        signal.signal(signal.SIGALRM, _handler)
        handler_installed = True
        signal.setitimer(signal.ITIMER_REAL, effective_seconds)
    except ValueError:
        if handler_installed:
            try:
                signal.signal(signal.SIGALRM, previous)
            except ValueError:
                pass
        yield
        return
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0.0)
        signal.signal(signal.SIGALRM, previous)
        if previous_delay > 0.0:
            elapsed = time.monotonic() - started
            signal.setitimer(
                signal.ITIMER_REAL,
                max(previous_delay - elapsed, 1.0e-6),
                previous_interval,
            )


def is_float_token(token: str) -> bool:
    try:
        float(token)
    except (TypeError, ValueError):
        return False
    return token.lower() not in {"inf", "nan", "+inf", "-inf"}


def quantize_number(value: float) -> str:
    return f"{float(value):.{NUMERIC_SIGNIFICANT_DIGITS}g}"


def numeric_value(label: str) -> float | None:
    if is_float_token(label):
        return float(label)
    return None


def tree_size(tree: Tree | None) -> int:
    if tree is None:
        return 0
    return 1 + sum(tree_size(child) for child in tree[1])


def tree_to_prefix(tree: Tree | None) -> list[str]:
    if tree is None:
        return []
    tokens = [tree[0]]
    for child in tree[1]:
        tokens.extend(tree_to_prefix(child))
    return tokens


def prefix_to_tree(prefix: Sequence[str]) -> Tree | None:
    tokens = [str(t) for t in prefix if str(t) != ""]
    if not tokens:
        return None

    def parse(index: int) -> tuple[Tree | None, int]:
        if index >= len(tokens):
            return None, index
        item = tokens[index]
        index += 1
        if item in UNARY_OPS:
            child, index = parse(index)
            if child is None:
                return None, index
            return (item, (child,)), index
        if item in BINARY_OPS:
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


def _leaf_number(node: Tree) -> float | None:
    label, children = node
    return numeric_value(label) if not children else None


def _close(value: float | None, target: float) -> bool:
    return value is not None and abs(value - target) <= IDENTITY_ATOL


def _flatten(op: str, children: tuple[Tree, ...]) -> list[Tree]:
    out: list[Tree] = []
    for child in children:
        if child[0] == op:
            out.extend(_flatten(op, child[1]))
        else:
            out.append(child)
    return out


def _binary_fold(op: str, nodes: Sequence[Tree]) -> Tree:
    current = nodes[0]
    for node in nodes[1:]:
        current = (op, (current, node))
    return current


def _normalize_signs(label: str, children: tuple[Tree, ...]) -> Tree:
    if label == "sub" and len(children) == 2:
        left, right = children
        return ("add", (left, ("neg", (right,))))
    if label == "div" and len(children) == 2:
        left, right = children
        return ("mul", (left, ("inv", (right,))))
    if label == "pow2" and len(children) == 1:
        return ("pow", (children[0], ("2", ())))
    if label == "pow3" and len(children) == 1:
        return ("pow", (children[0], ("3", ())))
    if label == "id" and len(children) == 1:
        return children[0]
    if label == "mul" and len(children) == 2:
        left, right = children
        if _close(_leaf_number(left), -1.0):
            return ("neg", (right,))
        if _close(_leaf_number(right), -1.0):
            return ("neg", (left,))
    if label == "pow" and len(children) == 2 and _close(_leaf_number(children[1]), -1.0):
        return ("inv", (children[0],))
    if label == "neg" and len(children) == 1:
        inner_label, inner_children = children[0]
        if inner_label == "neg" and len(inner_children) == 1:
            return inner_children[0]
        if inner_label == "add":
            return ("add", tuple(("neg", (child,)) for child in inner_children))
        value = _leaf_number(children[0])
        if value is not None:
            return (quantize_number(-value), ())
    return (label, children)


def _fold_identities(label: str, children: tuple[Tree, ...]) -> Tree:
    if label == "add":
        kept = [child for child in children if not _close(_leaf_number(child), 0.0)]
        if not kept:
            return ("0", ())
        if len(kept) == 1:
            return kept[0]
        return (label, tuple(kept))
    if label == "mul":
        if any(_close(_leaf_number(child), 0.0) for child in children):
            return ("0", ())
        kept = [child for child in children if not _close(_leaf_number(child), 1.0)]
        if not kept:
            return ("1", ())
        if len(kept) == 1:
            return kept[0]
        return (label, tuple(kept))
    if label == "inv" and len(children) == 1:
        inner = children[0]
        if inner[0] == "inv" and len(inner[1]) == 1:
            return inner[1][0]
        if _close(_leaf_number(inner), 1.0):
            return ("1", ())
    return (label, children)


def canonicalize_tree(tree: Tree | None) -> Tree | None:
    if tree is None:
        return None
    label, children = tree
    canon_children = tuple(canonicalize_tree(child) for child in children)
    if any(child is None for child in canon_children):
        return None
    if not canon_children:
        value = numeric_value(label)
        return (quantize_number(value), ()) if value is not None else (label, ())

    normalized = _normalize_signs(label, canon_children)
    if normalized != (label, canon_children):
        return canonicalize_tree(normalized)

    if label in COMMUTATIVE:
        flat = tuple(_flatten(label, canon_children))
        folded = _fold_identities(label, flat)
        if folded != (label, flat):
            return canonicalize_tree(folded)
        ordered = tuple(sorted(flat, key=lambda item: repr(item)))
        return _binary_fold(label, ordered)

    folded = _fold_identities(label, canon_children)
    if folded != (label, canon_children):
        return canonicalize_tree(folded)
    return label, canon_children


def skeletonize_tree(tree: Tree | None) -> Tree | None:
    if tree is None:
        return None
    label, children = tree
    if numeric_value(label) is not None or label in {CONST_PLACEHOLDER, "CONSTANT"} or label.startswith("c_"):
        label = CONST_PLACEHOLDER
    return (label, tuple(skeletonize_tree(child) for child in children))  # type: ignore[misc]


def tree_to_zss(tree: Tree):
    from zss import Node

    node = Node(tree[0])
    for child in tree[1]:
        node.addkid(tree_to_zss(child))
    return node


def tree_edit_distance(left: Tree | None, right: Tree | None) -> float:
    if left is None or right is None:
        return float("nan")
    from zss import simple_distance

    try:
        with time_limit(TED_TIMEOUT_SEC):
            return float(simple_distance(tree_to_zss(left), tree_to_zss(right)))
    except TedTimeout:
        return float("nan")


def normalized_ted(distance: float, left: Tree | None, right: Tree | None) -> float:
    if distance != distance:  # NaN
        return float("nan")
    denom = tree_size(left) + tree_size(right)
    return float(distance / denom) if denom else 0.0


def _pad_components(left: Sequence[Tree | None], right: Sequence[Tree | None]) -> tuple[list[Tree | None], list[Tree | None]]:
    n = max(len(left), len(right))
    return list(left) + [None] * (n - len(left)), list(right) + [None] * (n - len(right))


def system_ted(
    true_components: Sequence[Tree | None],
    pred_components: Sequence[Tree | None],
) -> dict[str, Any]:
    """Index-aligned TED. Component order is never permuted."""
    left, right = _pad_components(true_components, pred_components)
    raw_parts: list[float] = []
    skel_parts: list[float] = []
    failure = None
    for true_tree, pred_tree in zip(left, right):
        if true_tree is None or pred_tree is None:
            failure = failure or "TEDParseError"
            size = tree_size(true_tree) + tree_size(pred_tree)
            raw_parts.append(float(size if size else 1))
            skel_parts.append(float(size if size else 1))
            continue
        dist = tree_edit_distance(true_tree, pred_tree)
        if dist != dist:
            failure = failure or "TEDTimeout"
            size = tree_size(true_tree) + tree_size(pred_tree)
            raw_parts.append(float(size if size else 1))
        else:
            raw_parts.append(dist)
        skel = tree_edit_distance(skeletonize_tree(true_tree), skeletonize_tree(pred_tree))
        if skel != skel:
            failure = failure or "TEDTimeout"
            size = tree_size(true_tree) + tree_size(pred_tree)
            skel_parts.append(float(size if size else 1))
        else:
            skel_parts.append(skel)
    raw = float(sum(raw_parts))
    skeleton = float(sum(skel_parts))
    true_join = _join_system(true_components)
    pred_join = _join_system(pred_components)
    exact = float(true_join is not None and pred_join is not None and true_join == pred_join)
    skel_exact = float(
        all(
            true_tree is not None
            and pred_tree is not None
            and skeletonize_tree(true_tree) == skeletonize_tree(pred_tree)
            for true_tree, pred_tree in zip(left, right)
        )
        and len(true_components) == len(pred_components)
        and bool(true_components)
    )
    return {
        "ted_raw": raw,
        "ted_skeleton": skeleton,
        "normalized_ted": normalized_ted(raw, true_join, pred_join),
        "canonical_exact": exact,
        "skeleton_exact": skel_exact,
        "n_true_components": len(true_components),
        "n_pred_components": len(pred_components),
        "component_count_match": len(true_components) == len(pred_components),
        "failure_reason": failure,
        "component_ted_raw": raw_parts,
        "component_ted_skeleton": skel_parts,
    }


def _join_system(components: Sequence[Tree | None]) -> Tree | None:
    if not components or any(item is None for item in components):
        return None
    if len(components) == 1:
        return components[0]
    return ("system", tuple(components))  # type: ignore[arg-type]
