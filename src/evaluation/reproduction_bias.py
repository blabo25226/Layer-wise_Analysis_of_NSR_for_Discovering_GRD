"""CTC_NSR-style template canonicalization and reproduced / novel rates.

GPU_RUN2 measures reproduction against the **fine-tuning corpus**, not the
unknown NeSymReS 100M pretraining template set. Membership is recorded at three
levels: exact string, constant-stripped skeleton, and symbolic equivalence.
"""

from __future__ import annotations

from typing import Any, Iterable, Mapping, Sequence

import sympy as sp


PLACEHOLDER = sp.Symbol("c")


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


def canonical_prefix_tree(expr: str) -> str | None:
    """Serialize a commutative-normalized, constant-stripped expression."""
    text = (expr or "").strip()
    if not text:
        return None
    try:
        parsed = sp.sympify(text.replace("^", "**"))
        rewritten = sp.simplify(_rewrite(parsed))
        return sp.srepr(_rewrite(rewritten))
    except Exception:
        return None


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
) -> dict[str, Any]:
    """Compare one prediction against the fine-tuning template corpus."""
    pred_tree = canonical_prefix_tree(predicted_expr)
    true_tree = canonical_prefix_tree(true_expr) if true_expr else None
    template_set = {canonical_prefix_tree(item) or item for item in train_templates}
    template_set.discard(None)
    exact_set = {str(item).strip() for item in (train_exact or []) if str(item).strip()}
    pred_text = (predicted_expr or "").strip()
    exact_member = bool(pred_text) and pred_text in exact_set
    skeleton_member = bool(pred_tree) and pred_tree in template_set
    symbolic_member = False
    if pred_tree and pred_tree in template_set:
        symbolic_member = True
    elif pred_text and true_expr:
        try:
            symbolic_member = bool(sp.simplify(sp.sympify(pred_text) - sp.sympify(true_expr)) == 0)
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
    }


def aggregate_reproduction(
    rows: Sequence[Mapping[str, Any]],
    *,
    pred_key: str = "pred_simplified",
    true_key: str = "true_canonical",
    train_templates: Sequence[str],
) -> dict[str, Any]:
    classified = []
    for row in rows:
        info = classify_reproduction(
            str(row.get(pred_key) or row.get("pred_raw") or ""),
            train_templates=train_templates,
            train_exact=train_templates,
            true_expr=str(row.get(true_key) or row.get("true_expr") or ""),
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
    return {
        "n_total": n,
        "n_valid": n_valid,
        "reproduced_rate": n_reproduced / n if n else 0.0,
        "novel_rate": n_novel / n if n else 0.0,
        "novel_recovery_rate": n_novel_recovery / n if n else 0.0,
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
