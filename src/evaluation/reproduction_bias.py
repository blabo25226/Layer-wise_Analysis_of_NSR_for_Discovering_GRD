"""CTC_NSR-style template canonicalization and reproduced / novel rates.

GPU_RUN2 measures reproduction against the **fine-tuning corpus**, not the
unknown NeSymReS 100M pretraining template set. Membership is recorded at three
levels: exact string, constant-stripped skeleton, and symbolic equivalence.
"""

from __future__ import annotations

import signal
import threading
from contextlib import contextmanager
from typing import Any, Iterable, Mapping, Sequence

import sympy as sp


PLACEHOLDER = sp.Symbol("c")
REPRODUCTION_SYMPY_TIMEOUT_SEC = 0.1


class _ReproductionSympyTimeout(Exception):
    """Raised when a reproduction-only symbolic operation exceeds its budget."""


@contextmanager
def _sympy_time_limit(seconds: float):
    """Bound pathological SymPy work on the POSIX main thread.

    Phase 5 runs this aggregation on the main thread.  The fallback remains
    best-effort on platforms without ``SIGALRM`` so the module stays portable.
    """
    if (
        seconds <= 0
        or not hasattr(signal, "SIGALRM")
        or threading.current_thread() is not threading.main_thread()
    ):
        yield
        return

    def _handler(signum, frame):
        raise _ReproductionSympyTimeout()

    old_handler = signal.signal(signal.SIGALRM, _handler)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, old_handler)


def _rewrite(node: sp.Expr) -> sp.Expr:
    if isinstance(node, sp.Pow) and node.exp.is_Integer:
        return sp.Pow(_rewrite(node.base), node.exp)
    if isinstance(node, sp.Number):
        return PLACEHOLDER
    if isinstance(node, (sp.Add, sp.Mul)):
        children = [_rewrite(arg) for arg in node.args]
        children = sorted(children, key=lambda child: sp.srepr(child))
        return node.func(*children)
    if node.args:
        return node.func(*(_rewrite(arg) for arg in node.args))
    return node


def _canonical_prefix_tree_with_status(
    expr: str,
    *,
    timeout_sec: float = REPRODUCTION_SYMPY_TIMEOUT_SEC,
) -> tuple[str | None, bool]:
    """Return a canonical tree and whether algebraic simplification timed out."""
    text = (expr or "").strip()
    if not text:
        return None, False
    try:
        with _sympy_time_limit(timeout_sec):
            parsed = sp.sympify(text.replace("^", "**"))
            structural = _rewrite(parsed)
        try:
            with _sympy_time_limit(timeout_sec):
                rewritten = sp.simplify(structural)
                serialized = sp.srepr(_rewrite(rewritten))
            return serialized, False
        except _ReproductionSympyTimeout:
            # Structural normalization is deterministic and conservative.  It
            # avoids expanding pathological nested powers while still allowing
            # exact skeleton membership checks.
            try:
                with _sympy_time_limit(timeout_sec):
                    return sp.srepr(structural), True
            except _ReproductionSympyTimeout:
                return None, True
    except _ReproductionSympyTimeout:
        return None, True
    except Exception:
        return None, False


def canonical_prefix_tree(
    expr: str,
    *,
    timeout_sec: float = REPRODUCTION_SYMPY_TIMEOUT_SEC,
) -> str | None:
    """Serialize a commutative-normalized, constant-stripped expression."""
    tree, _ = _canonical_prefix_tree_with_status(expr, timeout_sec=timeout_sec)
    return tree


def skeleton_string(expr: str) -> str | None:
    tree = canonical_prefix_tree(expr)
    return tree


def template_fingerprint(expr: str) -> str | None:
    return canonical_prefix_tree(expr)


def corpus_fingerprint(expressions: Sequence[str]) -> dict[str, Any]:
    templates = []
    seen = set()
    for expr in expressions:
        tree = canonical_prefix_tree(expr)
        if tree is None:
            continue
        if tree not in seen:
            seen.add(tree)
            templates.append(tree)
    templates.sort()
    from gpu_run2_runtime import fingerprint_json

    return {
        "n_expressions": len(expressions),
        "n_unique_templates": len(templates),
        "templates": templates,
        "fingerprint": fingerprint_json(templates),
    }


def classify_reproduction(
    predicted_expr: str,
    *,
    train_templates: Iterable[str],
    train_exact: Iterable[str] | None = None,
    true_expr: str = "",
    _template_set: set[str] | None = None,
    _exact_set: set[str] | None = None,
    _canonical_cache: dict[str, tuple[str | None, bool]] | None = None,
    _allow_symbolic_check: bool = True,
    _known_symbolic_member: bool | None = None,
) -> dict[str, Any]:
    """Compare one prediction against the fine-tuning template corpus."""
    def canonical(text: str) -> tuple[str | None, bool]:
        if _canonical_cache is None:
            return _canonical_prefix_tree_with_status(text)
        if text not in _canonical_cache:
            _canonical_cache[text] = _canonical_prefix_tree_with_status(text)
        return _canonical_cache[text]

    pred_tree, pred_timed_out = canonical(predicted_expr)
    if true_expr:
        true_tree, true_timed_out = canonical(true_expr)
    else:
        true_tree, true_timed_out = None, False
    if _template_set is None:
        template_set = {canonical_prefix_tree(item) or item for item in train_templates}
        template_set.discard(None)
    else:
        template_set = _template_set
    if _exact_set is None:
        exact_set = {
            str(item).strip() for item in (train_exact or []) if str(item).strip()
        }
    else:
        exact_set = _exact_set
    pred_text = (predicted_expr or "").strip()
    exact_member = bool(pred_text) and pred_text in exact_set
    skeleton_member = bool(pred_tree) and pred_tree in template_set
    symbolic_member = False
    symbolic_timed_out = False
    if pred_tree and pred_tree in template_set:
        symbolic_member = True
    elif _known_symbolic_member is not None:
        # Phase records already contain a bounded symbolic-equivalence check.
        # Reuse it instead of repeating an expensive unbounded-looking SymPy
        # comparison during post-hoc reproduction aggregation.
        symbolic_member = _known_symbolic_member
    elif (
        _allow_symbolic_check
        and pred_text
        and true_expr
        and not pred_timed_out
        and not true_timed_out
    ):
        try:
            with _sympy_time_limit(REPRODUCTION_SYMPY_TIMEOUT_SEC):
                symbolic_member = bool(
                    sp.simplify(sp.sympify(pred_text) - sp.sympify(true_expr)) == 0
                )
        except _ReproductionSympyTimeout:
            symbolic_member = False
            symbolic_timed_out = True
        except Exception:
            symbolic_member = False
    reproduced = bool(skeleton_member or exact_member)
    return {
        "pred_template": pred_tree,
        "true_template": true_tree,
        "exact_membership": exact_member,
        "skeleton_membership": skeleton_member,
        "symbolic_membership": symbolic_member,
        "reproduced": reproduced,
        "novel": bool(pred_text) and not reproduced,
        "canonicalization_timed_out": bool(pred_timed_out or true_timed_out),
        "symbolic_check_timed_out": symbolic_timed_out,
    }


def aggregate_reproduction(
    rows: Sequence[Mapping[str, Any]],
    *,
    pred_key: str = "pred_simplified",
    true_key: str = "true_canonical",
    train_templates: Sequence[str],
) -> dict[str, Any]:
    template_set = {canonical_prefix_tree(item) or item for item in train_templates}
    template_set.discard(None)
    exact_set = {str(item).strip() for item in train_templates if str(item).strip()}
    canonical_cache: dict[str, tuple[str | None, bool]] = {}
    classified = []
    for row in rows:
        info = classify_reproduction(
            str(row.get(pred_key) or row.get("pred_raw") or ""),
            train_templates=train_templates,
            train_exact=train_templates,
            true_expr=str(row.get(true_key) or row.get("true_expr") or ""),
            _template_set=template_set,
            _exact_set=exact_set,
            _canonical_cache=canonical_cache,
            _allow_symbolic_check=float(row.get("valid_pred", 0.0) or 0.0) == 1.0,
            _known_symbolic_member=bool(
                row.get("sym_equiv", row.get("symbolic_equivalent", 0.0)) or 0.0
            ),
        )
        classified.append({**dict(row), **info})
    n = len(classified)
    n_valid = sum(1 for row in classified if float(row.get("valid_pred", 0.0)) == 1.0)
    n_reproduced = sum(1 for row in classified if row.get("reproduced"))
    n_novel = sum(1 for row in classified if row.get("novel"))
    n_novel_recovery = sum(
        1
        for row in classified
        if row.get("novel") and float(row.get("sym_recovery", row.get("skeleton", 0.0)) or 0.0) > 0.0
    )
    n_canonicalization_timeouts = sum(
        1 for row in classified if row.get("canonicalization_timed_out")
    )
    n_symbolic_check_timeouts = sum(
        1 for row in classified if row.get("symbolic_check_timed_out")
    )
    return {
        "n_total": n,
        "n_valid": n_valid,
        "reproduced_rate": n_reproduced / n if n else 0.0,
        "novel_rate": n_novel / n if n else 0.0,
        "novel_recovery_rate": n_novel_recovery / n if n else 0.0,
        "canonicalization_timeout_count": n_canonicalization_timeouts,
        "symbolic_check_timeout_count": n_symbolic_check_timeouts,
        "reproduced_exact_rate": _rate(classified, reproduced=True, key="exact"),
        "reproduced_skeleton_rate": _rate(classified, reproduced=True, key="skeleton"),
        "novel_exact_rate": _rate(classified, reproduced=False, key="exact"),
        "novel_skeleton_rate": _rate(classified, reproduced=False, key="skeleton"),
        "rows": classified,
    }


def _rate(rows: Sequence[Mapping[str, Any]], *, reproduced: bool, key: str) -> float:
    subset = [row for row in rows if bool(row.get("reproduced")) == reproduced]
    if not subset:
        return 0.0
    hits = 0
    for row in subset:
        value = row.get(key)
        if value is None:
            value = row.get(f"sym_{key}")
        try:
            hits += float(value or 0.0) > 0.0
        except (TypeError, ValueError):
            continue
    return hits / len(subset)
