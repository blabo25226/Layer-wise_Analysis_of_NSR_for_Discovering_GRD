"""Deterministic tree rewrites shared by Part B (§8.1) and the Part A control battery (§7.7).

All rewrites operate on the canonicalized ``(label, children)`` tree
representation from ``src/gpu_run4/ted.py`` (via
``gpu_run4.formulas.parse_infix_component`` / ``parse_prefix_component``),
never on a canonicalized *string* searched for a surface token (rule R1).
"""

from __future__ import annotations

import re
from typing import Optional

from gpu_run4.formulas import join_infix_system, numeric_equivalent, parse_infix_component, tree_to_infix
from gpu_run4.ted import Tree, prefix_to_tree, tree_size

_VARIABLE = re.compile(r"^x_(\d+)$")


def _is_variable(label: str) -> Optional[int]:
    match = _VARIABLE.fullmatch(label)
    return int(match.group(1)) if match else None


def _walk(tree: Tree | None):
    if tree is None:
        return
    yield tree
    for child in tree[1]:
        yield from _walk(child)


def contains_variable(tree: Tree | None) -> bool:
    return any(_is_variable(node[0]) is not None for node in _walk(tree))


# ---------------------------------------------------------------------------
# PC2a: -1 * k * x_i -> (-k) * x_i, the exact P4 asymmetry, in the model's own
# spelling. A textual rewrite by design (v2 frames it as a spelling change,
# not a tree transform): "-1 * k * x_i" is how the generator writes decay;
# "(-k) * x_i" is how ODEFormer must, because sub/div have zero generation
# probability.
# ---------------------------------------------------------------------------
_NEG_ONE_TIMES_CONST_TIMES_VAR = re.compile(
    r"-\s*1(?:\.0+)?\s*\*\s*([0-9]+\.[0-9]+|[0-9]+)\s*\*\s*(x_\d+)"
)


def rewrite_neg_one_decay(text: str) -> tuple[str, int]:
    """Rewrite every ``-1 * k * x_i`` to ``(-k) * x_i``. Returns (rewritten, n_rewrites)."""

    count = 0

    def _sub(match: re.Match) -> str:
        nonlocal count
        count += 1
        constant, variable = match.group(1), match.group(2)
        return f"(-{constant}) * {variable}"

    rewritten = _NEG_ONE_TIMES_CONST_TIMES_VAR.sub(_sub, text)
    return rewritten, count


# ---------------------------------------------------------------------------
# PC2c / PC2d: commutation. Render the canonicalized tree back to infix with
# every add / mul node's two children swapped in the rendered text.
# ---------------------------------------------------------------------------
def render_with_commutation_swap(tree: Tree | None, *, swap_add: bool, swap_mul: bool) -> str:
    if tree is None:
        return ""
    label, children = tree
    if not children:
        return label
    args = [render_with_commutation_swap(child, swap_add=swap_add, swap_mul=swap_mul) for child in children]
    if label == "add" and swap_add and len(args) == 2:
        args = [args[1], args[0]]
    if label == "mul" and swap_mul and len(args) == 2:
        args = [args[1], args[0]]
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


def commute_infix(component_infix: str, *, swap_add: bool, swap_mul: bool) -> str:
    tree = parse_infix_component(component_infix)
    if tree is None:
        return component_infix
    return render_with_commutation_swap(tree, swap_add=swap_add, swap_mul=swap_mul)


# ---------------------------------------------------------------------------
# PC3a: alter one realized Hill exponent (4 -> 2, or 2 -> 1) on the parsed
# tree. Never a surface-token search (rule R1): walks `pow` nodes whose base
# subtree contains a variable.
# ---------------------------------------------------------------------------
def _pow_exponent_value(tree: Tree) -> Optional[float]:
    label, children = tree
    if label != "pow" or len(children) != 2:
        return None
    try:
        return float(children[1][0])
    except ValueError:
        return None


def _find_first_pow_base(tree: Tree, exponent_value: float) -> Optional[Tree]:
    if _pow_exponent_value(tree) == exponent_value and contains_variable(tree[1][0]):
        return tree[1][0]
    for child in tree[1]:
        found = _find_first_pow_base(child, exponent_value)
        if found is not None:
            return found
    return None


def _replace_all_pow_with_base(tree: Tree, exponent_value: float, base: Tree, new_exponent: Optional[str]) -> Tree:
    """Replace every ``pow(base, exponent_value)`` node (matched by exact
    structural equality of the base subtree) with ``pow(base, new_exponent)``,
    or with ``base`` itself when ``new_exponent`` is ``None``.

    Rewriting *every* occurrence -- not just the first node found -- matters
    because a single Hill term repeats its ``A^n`` subtree in both the
    numerator and the denominator (``a * A^n * inv(K + A^n)``); altering only
    one occurrence would produce a expression that is neither the original
    nor a consistently-lower-exponent Hill term.
    """
    label, children = tree
    if _pow_exponent_value(tree) == exponent_value and children[0] == base:
        return base if new_exponent is None else (label, (base, (new_exponent, ())))
    return (label, tuple(_replace_all_pow_with_base(child, exponent_value, base, new_exponent) for child in children))


def alter_one_hill_exponent(tree: Tree) -> Optional[Tree]:
    """4 -> 2, or else 2 -> 1, on the parsed (infix-derivation) tree.

    Infix parsing evaluates ``((x_i)**2)**2`` straight to a single
    ``pow(x_i, 4)`` node (SymPy folds nested integer powers during
    ``parse_expr(..., evaluate=True)``); it does **not** preserve the nested
    ``pow2,pow2`` shape the *prefix* derivation keeps (see
    ``gpu_runclaude1.partb`` for that path). Because PC3a's altered truth
    must be fed through the same infix-only M0/M1/M3 cascade as everything
    else in Part A (rule R1), this walks the tree by exponent *value*
    (4 or 2) over a variable-containing base, never by assuming a nesting
    depth that this derivation path does not have, and rewrites every
    occurrence of that same base's power so the numerator and denominator of
    one Hill term change consistently. Returns ``None`` if neither exponent
    is present (not in PC3a's eligible set).
    """
    base4 = _find_first_pow_base(tree, 4.0)
    if base4 is not None:
        return _replace_all_pow_with_base(tree, 4.0, base4, "2")
    base2 = _find_first_pow_base(tree, 2.0)
    if base2 is not None:
        return _replace_all_pow_with_base(tree, 2.0, base2, None)
    return None


def alter_one_hill_exponent_infix(component_infix: str) -> Optional[str]:
    tree = parse_infix_component(component_infix)
    if tree is None:
        return None
    altered = alter_one_hill_exponent(tree)
    if altered is None:
        return None
    return tree_to_infix(altered)


# ---------------------------------------------------------------------------
# PC3b: swap two variable indices within one component (dimension >= 2 only).
# A pure text substitution via a single-pass transposition so "x_0"/"x_1"
# never collide mid-rewrite.
# ---------------------------------------------------------------------------
def swap_variables_infix(component_infix: str, var_a: str, var_b: str) -> str:
    placeholder = "__GPU_RUNCLAUDE1_SWAP__"
    text = re.sub(rf"\b{re.escape(var_a)}\b", placeholder, component_infix)
    text = re.sub(rf"\b{re.escape(var_b)}\b", var_a, text)
    text = text.replace(placeholder, var_b)
    return text


# ---------------------------------------------------------------------------
# Part B rewrite set B-R1..B-R4 (v2 §8.1), operating on the RAW (uncanonical-
# ized) prefix tree so unary op tokens (pow2, pow3, ...) are counted exactly
# as the generator emits them, never as `canonicalize_tree` renders them
# (which folds pow2/pow3 into a binary `pow` node -- see
# gpu_runclaude1.partb for why that distinction matters).
# ---------------------------------------------------------------------------
def raw_prefix_tree(tokens_csv: str) -> Tree | None:
    tokens = [tok for tok in str(tokens_csv).split(",") if tok]
    return prefix_to_tree(tokens)


def raw_tree_to_prefix_tokens(tree: Tree | None) -> list[str]:
    if tree is None:
        return []
    tokens = [tree[0]]
    for child in tree[1]:
        tokens.extend(raw_tree_to_prefix_tokens(child))
    return tokens


# ---------------------------------------------------------------------------
# Rewrite/alteration verification (v2.1 §7.7.0 rules 1-2): every positive
# control's rewrite must be verified function-preserving, and every negative
# control's alteration must be verified function-changing. A control tests
# the matcher only on instances where this holds; otherwise it is
# ``ineligible_rewrite_unverified`` / ``ineligible_alteration_is_noop``.
# ---------------------------------------------------------------------------
def verify_function_preserving(true_infix: str, candidate_infix: str) -> dict:
    """Is ``candidate_infix`` provably the same function as ``true_infix``?

    Two-stage: fast floating-point sampling first
    (``gpu_run4.formulas.numeric_equivalent``); on a negative result, a
    fallback via ``sympy.nsimplify(..., rational=True)`` plus symbolic
    ``simplify`` of the difference, evaluated over **exact rationals**. This
    matters because ``ted.py``'s 4-significant-digit quantization
    (``NUMERIC_SIGNIFICANT_DIGITS``) plus a tight ``rtol=1e-5`` on the
    numeric check produces false negatives when a rewrite recombines two
    quantized constants into one differently-rounded constant (a genuine
    algebraic identity, defeated only by rounding noise, not by the identity
    being false). The fallback is exact, so it cannot introduce a false
    *positive* -- it can only rescue a numeric false negative.
    """
    true_tree = parse_infix_component(true_infix)
    cand_tree = parse_infix_component(candidate_infix)
    if true_tree is None or cand_tree is None:
        return {"verified": False, "method": "parse_failure"}
    numeric = numeric_equivalent([true_tree], [cand_tree])
    if numeric.get("equivalent"):
        return {"verified": True, "method": "numeric_equivalent", "numeric": numeric}
    try:
        import sympy as sp

        from gpu_run4.formulas import _prepare_infix, _sympy_local_dict

        local = _sympy_local_dict()
        true_expr = sp.nsimplify(sp.sympify(_prepare_infix(true_infix), locals=local), rational=True)
        cand_expr = sp.nsimplify(sp.sympify(_prepare_infix(candidate_infix), locals=local), rational=True)
        diff = sp.simplify(true_expr - cand_expr)
        if diff == 0:
            return {"verified": True, "method": "nsimplify_rational", "numeric": numeric}
    except Exception as exc:  # pragma: no cover -- defensive, reported not silently swallowed
        return {"verified": False, "method": "nsimplify_rational_error", "error": type(exc).__name__, "numeric": numeric}
    return {"verified": False, "method": "not_verified", "numeric": numeric}


# ---------------------------------------------------------------------------
# PC4b (v2.1 §7.7): a * X * inv(K + X) -> a * inv(K * inv(X) + 1) (divide the
# numerator and denominator of the Hill fraction by X). Bottom-up, one
# rewrite per component, verified function-preserving.
# ---------------------------------------------------------------------------
def _flatten_mul_operands(tree: Tree) -> list:
    label, children = tree
    if label == "mul" and len(children) == 2:
        return _flatten_mul_operands(children[0]) + _flatten_mul_operands(children[1])
    return [tree]


def _mul_fold_operands(factors) -> Tree:
    if not factors:
        return ("1", ())
    node = factors[0]
    for factor in factors[1:]:
        node = ("mul", (node, factor))
    return node


def _hill_inv_denominator(factor: Tree):
    """If ``factor`` is ``inv(add(K, X))`` with K constant-ish and X
    variable-containing, return (K, X); else None.
    """
    label, children = factor
    if label != "inv" or len(children) != 1:
        return None
    denom = children[0]
    if denom[0] != "add" or len(denom[1]) != 2:
        return None
    left, right = denom[1]
    for k_side, x_side in ((left, right), (right, left)):
        if contains_variable(x_side) and not contains_variable(k_side):
            return k_side, x_side
    return None


def _try_rewrite_pc4b(tree: Tree) -> tuple[Tree, bool]:
    label, children = tree
    if label == "mul":
        factors = _flatten_mul_operands(tree)
        for index, factor in enumerate(factors):
            hit = _hill_inv_denominator(factor)
            if hit is None:
                continue
            k_side, x_side = hit
            for other_index, other in enumerate(factors):
                if other_index == index or other != x_side:
                    continue
                remaining = [f for idx, f in enumerate(factors) if idx not in (index, other_index)]
                a_coeff = _mul_fold_operands(remaining) if remaining else ("1", ())
                new_denominator = ("add", (("mul", (k_side, ("inv", (x_side,)))), ("1", ())))
                replacement = ("mul", (a_coeff, ("inv", (new_denominator,))))
                return replacement, True
    new_children = []
    changed = False
    for child in children:
        if not changed:
            new_child, did = _try_rewrite_pc4b(child)
            if did:
                changed = True
                new_children.append(new_child)
                continue
        new_children.append(child)
    return (label, tuple(new_children)), changed


def rewrite_pc4b_infix(component_infix: str) -> tuple[str, bool]:
    """Apply the PC4b rewrite once; returns (new_infix, applied)."""
    tree = parse_infix_component(component_infix)
    if tree is None:
        return component_infix, False
    candidate, applied = _try_rewrite_pc4b(tree)
    if not applied:
        return component_infix, False
    return tree_to_infix(candidate), True


def verify_function_changing(true_infix: str, altered_infix: str) -> dict:
    """The negative-control counterpart of :func:`verify_function_preserving`:
    an alteration is eligible only if it is verified to **change** the
    function. Uses the same two-stage (numeric, then exact-rational)
    machinery so it shares the same false-negative-rescue property -- here
    that matters for excluding a genuine no-op from a specificity control's
    eligible set (v2.1 §7.7.0 rule 2), not for admitting one.
    """
    preserving = verify_function_preserving(true_infix, altered_infix)
    return {
        "changed": not preserving["verified"],
        "verification_method": preserving["method"],
        "numeric": preserving.get("numeric"),
    }
