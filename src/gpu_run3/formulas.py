"""ND2 prefix helpers: parse, eval, skeleton strings, teacher-forcing decomposition."""

from __future__ import annotations

from typing import Any, Sequence

from gpu_run3_runtime import install_nd2_path
from gpu_run3.ted import canonicalize_tree, prefix_to_tree, prefixes_symbolically_equivalent, skeletonize_tree, ted_metrics


def parse_to_prefix(expr: str, root_type: str = "node") -> list[str]:
    install_nd2_path()
    from ND2.GDExpr import GDExpr

    parsed = GDExpr.parse_expr(expr)
    return list(GDExpr.sympy2prefix(parsed, root_type, reindex=False, keep_coeff=True))


def prefix_to_string(prefix: Sequence[str]) -> str:
    install_nd2_path()
    from ND2.GDExpr import GDExpr

    return str(GDExpr.prefix2str(list(prefix)))


def tree_to_prefix_tokens(tree: tuple[str, tuple] | None) -> list[str]:
    if tree is None:
        return []
    label, children = tree
    tokens = [label]
    for child in children:
        tokens.extend(tree_to_prefix_tokens(child))
    return tokens


def formula_views(prefix: Sequence[str]) -> dict[str, Any]:
    raw = list(prefix)
    tree = canonicalize_tree(prefix_to_tree(raw))
    skeleton = skeletonize_tree(tree)
    failure = None if tree is not None else "ParseError"
    try:
        raw_str = prefix_to_string(raw)
    except Exception as exc:
        raw_str = " ".join(raw)
        failure = failure or f"ParseError:{type(exc).__name__}"
    return {
        "raw_expr": raw_str,
        "parsed_expr": raw_str if tree is not None else "",
        "canonical_expr": ",".join(tree_to_prefix_tokens(tree)),
        "skeleton_expr": ",".join(tree_to_prefix_tokens(skeleton)),
        "canonical_prefix": tree_to_prefix_tokens(tree),
        "skeleton_prefix": tree_to_prefix_tokens(skeleton),
        "expression_tree": tree,
        "complexity": len(raw),
        "failure_reason": failure,
        "valid": tree is not None,
    }


def compare_formulas(true_prefix: Sequence[str], pred_prefix: Sequence[str]) -> dict[str, Any]:
    true_views = formula_views(true_prefix)
    pred_views = formula_views(pred_prefix)
    metrics = ted_metrics(true_prefix, pred_prefix)
    symbolic = prefixes_symbolically_equivalent(true_prefix, pred_prefix)
    failure = pred_views["failure_reason"] or metrics["failure_reason"]
    return {
        **{f"true_{k}": v for k, v in true_views.items() if k != "expression_tree"},
        **{f"pred_{k}": v for k, v in pred_views.items() if k != "expression_tree"},
        "exact": metrics["exact"],
        "skeleton": metrics["skeleton"],
        "symbolic_equivalent": symbolic,
        "ted_raw": metrics["ted_raw"],
        "ted_skeleton": metrics["ted_skeleton"],
        "ted_variable_aware": metrics["ted_variable_aware"],
        "valid": bool(pred_views["valid"]),
        "failure_reason": failure,
        "complexity": pred_views["complexity"],
    }


def teacher_forcing_steps(prefix: Sequence[str], root_type: str = "node") -> list[dict[str, Any]]:
    """Official ND2 Dataset-style reverse decomposition into next-symbol examples."""
    install_nd2_path()
    from copy import deepcopy

    from ND2.GDExpr import GDExpr

    current = deepcopy(list(prefix))
    steps: list[dict[str, Any]] = []
    original_len = len(current)
    for _ in range(original_len):
        try:
            incomplete, policy, index = GDExpr.decompose(current, root_type)
        except Exception as exc:
            steps.append(
                {
                    "prefix": list(current),
                    "target": None,
                    "index": None,
                    "failure_reason": f"InvalidPrefix:{type(exc).__name__}:{exc}",
                }
            )
            break
        steps.append(
            {
                "prefix": list(incomplete),
                "target": policy,
                "index": int(index),
                "failure_reason": None,
            }
        )
        current = incomplete
        if GDExpr.find_first_placeholder(current) < 0:
            break
    return steps


def vocabulary_inventory() -> dict[str, Any]:
    install_nd2_path()
    from ND2.GDExpr import GDExpr

    return {
        "n_words_table": len(GDExpr.word2id),
        "word2id": dict(GDExpr.word2id),
        "id2word": {int(k): v for k, v in GDExpr.id2word.items()},
        "special": dict(GDExpr.special),
        "placeholder": dict(GDExpr.placeholder),
        "variable_node": dict(GDExpr.variable.node),
        "variable_edge": dict(GDExpr.variable.edge),
        "constant": dict(GDExpr.constant),
        "coefficient": GDExpr.coeff_token,
        "operator_binary": dict(GDExpr.operator.binary),
        "operator_unary": dict(GDExpr.operator.unary),
        "network_operators": ["aggr", "sour", "targ", "rgga", "regular"],
    }
