"""Canonical, JSON-safe records for symbolic-regression outputs."""

from __future__ import annotations

from typing import Any, Mapping, Optional, Sequence


def simplify_expression(expression: str) -> tuple[str, Optional[str]]:
    """Return a deterministic SymPy simplification and an optional parse error."""
    text = (expression or "").strip()
    if not text:
        return "", None
    try:
        import sympy as sp

        parsed = sp.sympify(text.replace("^", "**"))
        return str(sp.simplify(parsed)), None
    except Exception as exc:
        return text, f"{type(exc).__name__}: {exc}"


def variable_mapping(
    variable_names: Sequence[str],
    *,
    column_indices: Optional[Sequence[Optional[int]]] = None,
    source_names: Optional[Sequence[str]] = None,
) -> list[dict[str, Any]]:
    """Map local SR symbols to source columns and, when known, gene names."""
    rows: list[dict[str, Any]] = []
    for position, symbol in enumerate(variable_names):
        source_index = None
        if column_indices is not None and position < len(column_indices):
            source_index = column_indices[position]
        source_name = str(symbol)
        if source_index is not None and source_names is not None:
            idx = int(source_index)
            if 0 <= idx < len(source_names):
                source_name = str(source_names[idx])
        rows.append(
            {
                "symbol": str(symbol),
                "input_position": position,
                "source_index": None if source_index is None else int(source_index),
                "source_name": source_name,
            }
        )
    return rows


def dataset_variable_mapping(dataset, source_names: Optional[Sequence[str]] = None):
    """Build a mapping from an EquationSpec's gene_col_* metadata."""
    params = getattr(dataset.spec, "parameters", {}) or {}
    indices = []
    for position, _ in enumerate(dataset.spec.variable_names):
        value = params.get(f"gene_col_{position}")
        indices.append(None if value is None else int(value))
    return variable_mapping(
        dataset.spec.variable_names,
        column_indices=indices,
        source_names=source_names,
    )


def make_equation_record(
    *,
    eq_id: str,
    predicted_expr: str,
    variable_names: Sequence[str],
    scores: Mapping[str, Any],
    true_expr: str = "",
    mapping: Optional[Sequence[Mapping[str, Any]]] = None,
    candidate_expressions: Optional[Sequence[str]] = None,
    decoder: str,
    failure_reason: Optional[str] = None,
    decoder_metadata: Optional[Mapping[str, Any]] = None,
    **extra: Any,
) -> dict[str, Any]:
    """Create the required per-problem equation record used by Phases 4--8."""
    raw = (predicted_expr or "").strip()
    simplified, simplify_error = simplify_expression(raw)
    candidates = [str(x) for x in (candidate_expressions or []) if str(x).strip()]
    if raw and raw not in candidates:
        candidates.insert(0, raw)

    valid = bool(scores.get("valid_pred", 0.0))
    reason = failure_reason
    if not reason and not raw:
        reason = "decoder_returned_no_expression"
    elif not reason and not valid:
        reason = "expression_evaluation_failed"

    record = {
        "eq_id": str(eq_id),
        "true": true_expr,
        "true_expr": true_expr,
        "pred": raw,
        "pred_raw": raw,
        "pred_simplified": simplified,
        "candidate_expressions": candidates,
        "variable_names": [str(x) for x in variable_names],
        "variable_mapping": list(mapping or variable_mapping(variable_names)),
        "decoder": decoder,
        "decoder_metadata": dict(decoder_metadata or {}),
        "simplification_error": simplify_error,
        "failure_reason": reason,
        **dict(scores),
        **extra,
    }
    return record


GPU_RUN2_REQUIRED_FIELDS = frozenset(
    {
        "eq_id",
        "motif",
        "split",
        "split_view",
        "noise",
        "data_seed",
        "training_seed",
        "condition",
        "domain_regime",
        "structure_regime",
        "parameter_split",
        "target_variable",
        "oracle_regulators",
        "oracle_inputs",
        "variable_order",
        "oracle_source_equation_id",
        "true_raw",
        "true_canonical",
        "true_skeleton",
        "true_expr",
        "pred_raw",
        "pred_simplified",
        "pred_canonical",
        "pred_skeleton",
        "candidate_expressions",
        "exact",
        "skeleton",
        "symbolic_equivalent",
        "domain_id_nmse",
        "domain_ood_nmse",
        "complexity",
        "valid_pred",
        "failure_reason",
        "search_seconds",
        "process_seconds",
        "n_candidate_evals",
        "timeout",
        "timeout_budget_sec",
    }
)


def make_gpu_run2_equation_record(
    *,
    eq_id: str,
    predicted_expr: str,
    variable_names: Sequence[str],
    scores: Mapping[str, Any],
    true_expr: str = "",
    true_raw: str = "",
    true_canonical: str = "",
    true_skeleton: str = "",
    pred_canonical: str = "",
    pred_skeleton: str = "",
    motif: str,
    split: str,
    split_view: str,
    noise: float,
    data_seed: int,
    training_seed: int,
    condition: str,
    domain_regime: str,
    structure_regime: str,
    parameter_split: str,
    target_variable: str,
    oracle_regulators: Sequence[str],
    oracle_inputs: Sequence[str],
    variable_order: Sequence[str],
    oracle_source_equation_id: str,
    decoder: str,
    failure_reason: Optional[str] = None,
    candidate_expressions: Optional[Sequence[str]] = None,
    mapping: Optional[Sequence[Mapping[str, Any]]] = None,
    search_seconds: float = 0.0,
    process_seconds: float = 0.0,
    n_candidate_evals: int = 0,
    timeout: bool = False,
    timeout_budget_sec: float = 30.0,
    decoder_metadata: Optional[Mapping[str, Any]] = None,
    **extra: Any,
) -> dict[str, Any]:
    """GPU_RUN2 problem record with domain / structure axes and oracle metadata."""
    if domain_regime not in {"id", "ood"}:
        raise ValueError(f"domain_regime must be 'id' or 'ood', got {domain_regime!r}")
    if structure_regime not in {"id", "ood"}:
        raise ValueError(f"structure_regime must be 'id' or 'ood', got {structure_regime!r}")
    simplified, _simplify_error = simplify_expression(predicted_expr)
    record = make_equation_record(
        eq_id=eq_id,
        predicted_expr=predicted_expr,
        variable_names=variable_names,
        scores=scores,
        true_expr=true_expr or true_canonical or true_raw,
        mapping=mapping or variable_mapping(variable_order or variable_names),
        candidate_expressions=candidate_expressions,
        decoder=decoder,
        failure_reason=failure_reason,
        decoder_metadata=decoder_metadata,
        motif=str(motif),
        split=str(split),
        split_view=str(split_view),
        noise=float(noise),
        data_seed=int(data_seed),
        training_seed=int(training_seed),
        condition=str(condition),
        domain_regime=str(domain_regime),
        structure_regime=str(structure_regime),
        parameter_split=str(parameter_split),
        target_variable=str(target_variable),
        oracle_regulators=[str(x) for x in oracle_regulators],
        oracle_inputs=[str(x) for x in oracle_inputs],
        variable_order=[str(x) for x in variable_order],
        oracle_source_equation_id=str(oracle_source_equation_id),
        true_raw=str(true_raw or true_expr),
        true_canonical=str(true_canonical or true_expr),
        true_skeleton=str(true_skeleton),
        pred_canonical=str(pred_canonical or simplified),
        pred_skeleton=str(pred_skeleton),
        exact=float(scores.get("sym_exact", scores.get("exact", 0.0))),
        skeleton=float(scores.get("sym_skeleton", scores.get("skeleton", 0.0))),
        symbolic_equivalent=float(scores.get("sym_equiv", scores.get("equiv", 0.0))),
        domain_id_nmse=float(scores.get("domain_id_nmse", scores.get("nmse", float("inf")))),
        domain_ood_nmse=float(scores.get("domain_ood_nmse", float("nan"))),
        search_seconds=float(search_seconds),
        process_seconds=float(process_seconds),
        n_candidate_evals=int(n_candidate_evals),
        timeout=bool(timeout),
        timeout_budget_sec=float(timeout_budget_sec),
        **extra,
    )
    missing = sorted(GPU_RUN2_REQUIRED_FIELDS - set(record))
    if missing:
        raise KeyError(f"GPU_RUN2 equation record missing fields: {missing}")
    return record


def timing_payload(
    *,
    search_seconds: float,
    process_seconds: float,
    n_candidate_evals: int,
    timeout: bool,
    timeout_budget_sec: float = 30.0,
) -> dict[str, Any]:
    return {
        "search_seconds": float(search_seconds),
        "process_seconds": float(process_seconds),
        "n_candidate_evals": int(n_candidate_evals),
        "timeout": bool(timeout),
        "timeout_budget_sec": float(timeout_budget_sec),
    }
