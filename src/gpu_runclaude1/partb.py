"""Part B -- generator-support accounting (v2 §8.1): U_mult, U_affine, U_min, in_support.

All structural counting (``U_mult``, ``realized_hill_exponents``, the
generator-constraint checks) is done on the **raw, uncanonicalized** prefix
tree parsed straight from ``teacher_components_prefix`` (via
``gpu_run4.ted.prefix_to_tree``, never
``gpu_run4.formulas.canonicalize_tree``). This matters: ``canonicalize_tree``
folds the generator's own ``pow2``/``pow3`` unary tokens into a binary
``pow(base, 2|3)`` node (v2's Hill-4 example, ``pow2,pow2,x_i`` -> nested
canonical ``pow,pow,x_i,2,2``, still present as *two* pow nodes -- but
``U_mult`` must count non-identity unary nodes **as the generator's own
operator budget counts them**, i.e. one ``pow2`` token per application, not a
`pow` binary node the generator's vocabulary does not itself expose). Rule R1
forbids detecting the realized exponent by searching a canonicalized string
for a surface token; this module always walks the parsed tree.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional, Sequence

from gpu_run4.formulas import numeric_equivalent, parse_infix_component, tree_to_infix
from gpu_run4.ted import BINARY_OPS, Tree, UNARY_OPS, canonicalize_tree, tree_size

from gpu_runclaude1.constants import (
    MAX_BINARY_OPS_PER_DIM,
    MAX_UNARY_DEPTH,
    MAX_UNARY_OPS_PER_DIM,
    NUMERIC_EQUIVALENT_SEED,
    REWRITE_CAP_PER_COMPONENT,
)
from gpu_runclaude1.tree_rewrite import contains_variable, raw_prefix_tree

_NON_IDENTITY_UNARY = UNARY_OPS - {"id"}
_ALLOWED_OPERATORS = frozenset({"sin", "inv", "pow2", "id", "add", "mul"})


def _walk(tree: Tree | None):
    if tree is None:
        return
    yield tree
    for child in tree[1]:
        yield from _walk(child)


def count_non_identity_unary(tree: Tree | None) -> int:
    """U_mult: non-identity unary nodes (inv, pow2, sin, abs, sqrt, log, exp,
    pow3, arcsin, arccos, arctan, neg) on the raw prefix tree.
    """
    return sum(1 for node in _walk(tree) if node[0] in _NON_IDENTITY_UNARY)


def count_binary_ops(tree: Tree | None) -> int:
    return sum(1 for node in _walk(tree) if node[0] in BINARY_OPS)


def _implied_pow2_applications(exponent_value: int) -> int:
    """How many nested ``pow2``/``pow3`` unary applications the generator's
    own vocabulary would need to spell a variable raised to this integer
    exponent (no general binary ``pow`` with a free exponent is in
    ``operators_to_use``). Exact for {1, 2, 3, 4}; a defensive
    ``ceil(log2(n))`` fallback for anything else, since this corpus's
    ``hill_exponents`` config is only ``[1, 2, 4]``.
    """
    if exponent_value <= 1:
        return 0
    if exponent_value in (2, 3):
        return 1
    if exponent_value == 4:
        return 2
    import math

    return max(1, math.ceil(math.log2(exponent_value)))


#: "neg" is never a raw generator token -- decay is spelled with a literal
#: signed constant via "mul" (P4), and B-R4 makes any SymPy-introduced "neg"
#: free by trading it for a binary "mul(-1, X)". It is excluded from the
#: generator-equivalent tally so that a subtraction introduced purely by the
#: B-R1 rewrite's own algebra is not double-charged as a unary op the
#: generator never actually has to spend (matching v2's own worked example,
#: §8.1: "U_mult = 5, rescued by B-R1 to 3").
_GENERATOR_EQUIVALENT_UNARY = _NON_IDENTITY_UNARY - {"neg"}


def count_non_identity_unary_generator_equivalent(tree: Tree | None) -> int:
    """Unary-op budget cost of a **SymPy-derived** (infix-parsed or
    affine-rewritten) tree, expressed in the generator's own vocabulary.

    SymPy folds nested integer powers into a single binary ``pow(base, n)``
    node during ``parse_expr(..., evaluate=True)`` (v2's own worked example:
    ``((x_i)**2)**2`` parses straight to ``pow(x_i, 4)``, not the nested
    ``pow2(pow2(x_i))`` the *prefix* derivation keeps). Counting such a node
    as zero unary cost would silently undercount ``U_affine`` relative to
    ``U_mult`` (which is counted on the raw, un-evaluated prefix tree) and
    bias Part B's out-of-support rate anti-conservatively -- the direction
    v2 explicitly forbids (§14 item 3: any fallback must over-report
    out-of-support, never under-report it). This function restores parity by
    charging a ``pow(base, n)`` node over a variable-containing base the same
    unary-op cost the raw generator vocabulary would have paid.
    """
    total = 0
    for node in _walk(tree):
        label, children = node
        if label in _GENERATOR_EQUIVALENT_UNARY:
            total += 1
        elif label == "pow" and len(children) == 2 and contains_variable(children[0]):
            try:
                exponent_value = float(children[1][0])
            except ValueError:
                continue
            if exponent_value == int(exponent_value):
                total += _implied_pow2_applications(int(exponent_value))
    return total


def max_unary_chain_depth(tree: Tree | None) -> int:
    """Longest run of consecutive non-identity unary nodes on any root-to-leaf path."""
    if tree is None:
        return 0
    label, children = tree
    child_depths = [max_unary_chain_depth(child) for child in children]
    own = 1 if label in _NON_IDENTITY_UNARY else 0
    if not child_depths:
        return own
    if label in _NON_IDENTITY_UNARY:
        return own + max(child_depths)
    return max(child_depths)


def uses_only_in_support_operators(tree: Tree | None) -> bool:
    """Every operator node's own label is in the checkpoint's declared
    ``operators_to_use`` vocabulary (plus the always-present add/mul); a leaf
    (variable or numeric constant) is never itself an operator and always
    passes.
    """
    return all(
        node[0] in _ALLOWED_OPERATORS or node[0] not in (UNARY_OPS | BINARY_OPS)
        for node in _walk(tree)
    )


def realized_hill_exponents(tree: Tree | None) -> list[int]:
    """Every variable-containing power realized via nested pow2/pow3 wrapping
    on the raw tree (depth 1 pow2 -> exponent 2, depth 2 -> exponent 4, ...).
    Never detected by searching a canonicalized string for a surface token
    (rule R1): this always walks the parsed tree structure.

    Each nesting *chain* is reported exactly once, at its outermost node --
    walking every node individually would also revisit the inner ``pow2`` of
    a ``pow2(pow2(x_i))`` chain and wrongly report an extra bare exponent-2
    site that is not a separate operator application.
    """
    if tree is None:
        return []

    def base_and_exponent(node: Tree) -> tuple[Tree, int]:
        label, children = node
        if label in ("pow2", "pow3") and len(children) == 1:
            base, exponent = base_and_exponent(children[0])
            return base, exponent * (2 if label == "pow2" else 3)
        return node, 1

    found: list[int] = []

    def visit(node: Tree) -> None:
        label, children = node
        if label in ("pow2", "pow3") and len(children) == 1:
            base, exponent = base_and_exponent(node)
            if exponent > 1 and contains_variable(base):
                found.append(exponent)
            visit(base)
            return
        for child in children:
            visit(child)

    visit(tree)
    return found


@dataclass(frozen=True)
class GeneratorConstraintCheck:
    u_mult: int
    unary_depth: int
    binary_ops: int
    uses_only_in_support_operators: bool
    realized_hill_exponents: tuple


def analyze_raw_component(component_prefix_csv: str) -> GeneratorConstraintCheck:
    tree = raw_prefix_tree(component_prefix_csv)
    return GeneratorConstraintCheck(
        u_mult=count_non_identity_unary(tree),
        unary_depth=max_unary_chain_depth(tree),
        binary_ops=count_binary_ops(tree),
        uses_only_in_support_operators=uses_only_in_support_operators(tree),
        realized_hill_exponents=tuple(realized_hill_exponents(tree)),
    )


# ---------------------------------------------------------------------------
# Affine-decomposition rewrite set B-R1..B-R4 (v2 §8.1), operating on the
# infix-derived (SymPy-evaluated) tree so it can be numerically verified with
# `gpu_run4.formulas.numeric_equivalent` and re-encoded through the same path
# PC2b feeds into `score_pair` with.
# ---------------------------------------------------------------------------


def _is_variable_label(label: str) -> bool:
    return label.startswith("x_") and label[2:].isdigit()


def _flatten_mul(tree: Tree) -> list[Tree]:
    label, children = tree
    if label == "mul" and len(children) == 2:
        return _flatten_mul(children[0]) + _flatten_mul(children[1])
    return [tree]


def _mul_fold(factors: Sequence[Tree]) -> Tree:
    if not factors:
        return ("1", ())
    node = factors[0]
    for factor in factors[1:]:
        node = ("mul", (node, factor))
    return node


def _hill_inv_factor(factor: Tree) -> Optional[tuple[Tree, Tree]]:
    """If ``factor`` is ``inv(add(K, A^n))`` (K constant-ish, A^n containing a
    variable), return (K, A^n_tree); else None.
    """
    label, children = factor
    if label != "inv" or len(children) != 1:
        return None
    denom = children[0]
    if denom[0] != "add" or len(denom[1]) != 2:
        return None
    left, right = denom[1]
    for k_side, a_side in ((left, right), (right, left)):
        if contains_variable(a_side) and not contains_variable(k_side):
            return k_side, a_side
    return None


def _try_rewrite_b_r1(tree: Tree) -> tuple[Tree, bool]:
    """Bottom-up single-application search for ``a * A^n * inv(K + A^n) ->
    a - a*K*inv(K + A^n)`` (B-R1), anywhere in the tree.
    """
    label, children = tree
    if label == "mul":
        factors = _flatten_mul(tree)
        for index, factor in enumerate(factors):
            hit = _hill_inv_factor(factor)
            if hit is None:
                continue
            k_side, a_power = hit
            for other_index, other in enumerate(factors):
                if other_index == index or other != a_power:
                    continue
                remaining = [f for idx, f in enumerate(factors) if idx not in (index, other_index)]
                a_coeff = _mul_fold(remaining) if remaining else ("1", ())
                term2 = ("neg", (("mul", (("mul", (a_coeff, k_side)), factor)),))
                return ("add", (a_coeff, term2)), True
    new_children = []
    changed = False
    for child in children:
        if not changed:
            new_child, did = _try_rewrite_b_r1(child)
            if did:
                changed = True
                new_children.append(new_child)
                continue
        new_children.append(child)
    return (label, tuple(new_children)), changed


def _try_rewrite_b_r4(tree: Tree) -> tuple[Tree, bool]:
    """``neg(X) -> mul(-1, X)`` (B-R4): trades one unary ``neg`` node for a
    binary ``mul``, which strictly lowers the non-identity unary count.
    """
    label, children = tree
    if label == "neg" and len(children) == 1:
        return ("mul", (("-1", ()), children[0])), True
    new_children = []
    changed = False
    for child in children:
        if not changed:
            new_child, did = _try_rewrite_b_r4(child)
            if did:
                changed = True
                new_children.append(new_child)
                continue
        new_children.append(child)
    return (label, tuple(new_children)), changed


@dataclass(frozen=True)
class RewriteAttempt:
    rule: str
    accepted: bool
    verification: dict
    tree_before_size: int
    tree_after_size: int


def affine_rewrite_component(component_infix: str, *, cap: int = REWRITE_CAP_PER_COMPONENT) -> tuple[Optional[Tree], list[RewriteAttempt]]:
    """Bottom-up B-R1/B-R4 rewrite search, each accepted rewrite verified by
    ``numeric_equivalent(seed=0)`` and discarded+logged on failure (v2 §8.1).
    B-R2 (constant folding) is applied implicitly by re-canonicalizing after
    every accepted rewrite; B-R3 (distribute-if-it-helps) is not attempted by
    this engine -- the one-sidedness this omission adds is explicitly
    preregistered (``U_affine`` is a documented upper bound under the
    rewrite set actually run, v2 §8.1).
    """
    tree = parse_infix_component(component_infix)
    if tree is None:
        return None, []
    attempts: list[RewriteAttempt] = []
    current = tree
    for _ in range(cap):
        candidate, applied_r1 = _try_rewrite_b_r1(current)
        rule = "B-R1"
        if not applied_r1:
            candidate, applied_r4 = _try_rewrite_b_r4(current)
            rule = "B-R4"
            if not applied_r4:
                break
        verification = numeric_equivalent([current], [candidate], seed=NUMERIC_EQUIVALENT_SEED)
        accepted = bool(verification.get("equivalent"))
        attempts.append(
            RewriteAttempt(
                rule=rule,
                accepted=accepted,
                verification=verification,
                tree_before_size=tree_size(current),
                tree_after_size=tree_size(candidate),
            )
        )
        if not accepted:
            break
        current = canonicalize_tree(candidate)
        if current is None:
            break
    return current, attempts


def rewrite_b_r1_affine_infix(component_infix: str) -> tuple[str, bool]:
    """PC2b's rewrite: apply B-R1 once (the affine decomposition itself, not
    the full bottom-up U_affine search), returning (new_infix, applied).
    """
    tree = parse_infix_component(component_infix)
    if tree is None:
        return component_infix, False
    candidate, applied = _try_rewrite_b_r1(tree)
    if not applied:
        return component_infix, False
    return tree_to_infix(candidate), True


@dataclass(frozen=True)
class ComponentSupportRecord:
    system_id: str
    component_index: int
    u_mult: int
    u_affine: Optional[int]
    u_min: int
    in_support: bool
    realized_hill_exponents: tuple
    unary_depth: int
    binary_ops_per_dim: int
    uses_only_in_support_operators: bool
    affine_available: bool
    rewrite_attempts: tuple


def analyze_component(system_id: str, component_index: int, component_prefix_csv: str, component_infix: str) -> ComponentSupportRecord:
    raw = analyze_raw_component(component_prefix_csv)
    affine_tree, attempts = affine_rewrite_component(component_infix)
    affine_available = affine_tree is not None
    u_affine = count_non_identity_unary_generator_equivalent(affine_tree) if affine_available else None
    u_min = min(raw.u_mult, u_affine) if u_affine is not None else raw.u_mult
    return ComponentSupportRecord(
        system_id=system_id,
        component_index=component_index,
        u_mult=raw.u_mult,
        u_affine=u_affine,
        u_min=u_min,
        in_support=u_min <= MAX_UNARY_OPS_PER_DIM,
        realized_hill_exponents=raw.realized_hill_exponents,
        unary_depth=raw.unary_depth,
        binary_ops_per_dim=raw.binary_ops,
        uses_only_in_support_operators=raw.uses_only_in_support_operators,
        affine_available=affine_available,
        rewrite_attempts=tuple(attempts),
    )


def analyze_system(row: dict[str, Any]) -> list[ComponentSupportRecord]:
    prefixes = row["teacher_components_prefix"]
    infixes = row["teacher_components_infix"]
    return [
        analyze_component(row["system_id"], index, prefixes[index], infixes[index])
        for index in range(len(prefixes))
    ]
