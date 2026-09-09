"""The re-encoding round trip itself (v2 §8.2 step 4): ``encode(parse(raw))
-> decode -> canonicalize``, through the model's *own* vocabulary (mantissa /
exponent expansion, lossy at the frozen ``FLOAT_PRECISION``), then re-run
through this repository's own canonicalization pipeline
(:mod:`gpu_run4.formulas`, :mod:`gpu_run4.ted`) so the result is comparable,
term for term, to the stored ``candidate_formula_canonical`` field that the
same canonicalization pipeline originally produced.

This module needs a loaded model's ``env`` object (odeformer's
``environment.CharSPEnvironment`` or equivalent) but never touches a torch
tensor itself and performs no GPU work -- :mod:`gpu_runclaude1.partc` stays
strictly torch-free and model-free; this module is CPU-only but model-aware,
a distinct middle tier between the two.

No runtime dependency on ``GitHubSourceCode/``: this module only ever
receives an already-loaded ``env`` from
``gpu_run4_runtime.load_odeformer_model`` (which installs the vendored
``third_party/odeformer`` package, never the survey tree) and imports only
``sympy`` plus this repository's own parsing/canonicalization utilities.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from gpu_run4.formulas import (
    _sympy_local_dict,  # noqa: SLF001 -- deliberate reuse, not a private reimplementation
    join_canonical_system,
    parse_prefix_component,
    parse_system,
)


@dataclass(frozen=True)
class ReencodeResult:
    canonical: Optional[str]
    failure_reason: Optional[str]


def reencode_infix_via_model(env: Any, raw_infix: str) -> ReencodeResult:
    """Round-trip ``raw_infix`` through the model's own tokenizer and back.

    Splits multi-component systems on the frozen ``|`` / ``,|,`` separator
    (:func:`gpu_run4.formulas.parse_system`), so a dimension > 1 system is
    handled component-by-component and rejoined with the same frozen
    ``join_canonical_system`` used to build the stored
    ``candidate_formula_canonical`` field in the first place. A failure on
    any single component fails the whole candidate (a system's log-prob is
    not comparable if one of its components would silently vanish).
    """
    import sympy as sp

    parsed = parse_system(raw_infix)
    if not parsed["valid"] or not parsed["components_raw"]:
        return ReencodeResult(None, "SkeletonParseFailure")

    local = _sympy_local_dict()
    decoded_trees = []
    for component_raw in parsed["components_raw"]:
        prepared = component_raw.replace("^", "**").strip()
        try:
            expr = sp.sympify(prepared, locals=local, evaluate=True)
            node_tree = env.simplifier.sympy_expr_to_tree(expr)
            if node_tree is None:
                return ReencodeResult(None, "SkeletonEvaluationFailure")
            tokens = env.equation_encoder.encode(node_tree)
            if not tokens:
                return ReencodeResult(None, "SkeletonEvaluationFailure")
            decoded_node = env.equation_encoder.decode(tokens)
            if decoded_node is None:
                return ReencodeResult(None, "SkeletonEvaluationFailure")
            decoded_prefix_str = decoded_node.prefix()
        except Exception:
            return ReencodeResult(None, "SkeletonEvaluationFailure")
        decoded_tree = parse_prefix_component(decoded_prefix_str)
        if decoded_tree is None:
            return ReencodeResult(None, "SkeletonEvaluationFailure")
        decoded_trees.append(decoded_tree)

    canonical = join_canonical_system(decoded_trees)
    return ReencodeResult(canonical, None)


def infix_to_model_tokens(env: Any, raw_infix: str) -> tuple[Optional[list[str]], Optional[str]]:
    """``parse(raw) -> encode``: the model-vocabulary token stream for
    ``raw_infix``, usable directly with ``env.word_to_idx`` /
    ``teacher_forced_summed_logprob`` (v2 §8.2 step 3). Returns
    ``(tokens, failure_reason)``; multi-component systems are joined with the
    literal ``"|"`` token, matching the stored ``tree_encoded`` convention.
    """
    import sympy as sp

    parsed = parse_system(raw_infix)
    if not parsed["valid"] or not parsed["components_raw"]:
        return None, "SkeletonParseFailure"

    local = _sympy_local_dict()
    all_tokens: list[str] = []
    for index, component_raw in enumerate(parsed["components_raw"]):
        prepared = component_raw.replace("^", "**").strip()
        try:
            expr = sp.sympify(prepared, locals=local, evaluate=True)
            node_tree = env.simplifier.sympy_expr_to_tree(expr)
            if node_tree is None:
                return None, "SkeletonEvaluationFailure"
            tokens = env.equation_encoder.encode(node_tree)
            if not tokens:
                return None, "SkeletonEvaluationFailure"
        except Exception:
            return None, "SkeletonEvaluationFailure"
        if index > 0:
            all_tokens.append("|")
        all_tokens.extend(tokens)
    return all_tokens, None
