"""Audit pipeline primitives and condition runners."""

from __future__ import annotations

import json
import subprocess
from typing import Any

from evaluation.gpu_run5_structure import classify_formula
from gpu_run4.formulas import compare_formulas, split_components
from gpu_run5.evaluation import formula_metrics

from gpu_runmultiai.constants import (
    B3_PAIR_COUNT,
    CAS_TIMEOUT_SEC,
    IDENTITY_REWRITE_ID,
    IDENTITY_SCALE,
    N1_COUNT,
    Q4_TIMEOUT_SEC,
    TRUTH_COPY_REWRITE_ID,
)
from gpu_runmultiai.ids import component_id_for, negative_id_for, pair_id_for
from gpu_run4.ted import time_limit
from gpu_runmultiai.invariants import AuditInvariantError
from gpu_runmultiai.quantization import assign_quantization_stratum
from gpu_runmultiai.odeformer_runtime import (
    ODEFormerUnavailable,
    build_identity_scaler,
    build_production_scaler,
    canonical_system_prefix_raw,
    component_prefix_list_from_raw,
    decode_system_tree,
    forward_scale_system,
    full_system_infix_from_record,
    get_env,
    replace_component_prefixes,
    rescale_system,
    simplify_tree_subprocess,
    tree_to_prefix_list,
    tree_to_system_infix,
    truth_system_prefixes,
)
from gpu_runmultiai.serialization import json_safe_stage_payload
from gpu_runmultiai.oracle import (
    extract_component_infix,
    oracle_equivalence,
    oracle_single_component,
    prefix_to_infix_component,
)
from gpu_runmultiai.invariants import ResumeCacheMissError
from gpu_runmultiai.stage_cache import append_stage_cache, cache_key
from gpu_runmultiai.outcomes import build_outcome_row
from gpu_runmultiai.rewrites import (
    negative_control_row,
    rewrite_registration,
    truth_component_infix,
)
from gpu_runmultiai.q4_reference import (
    C_Q4_FIXTURES,
    Q4ContractError,
    audit_q4_decimal_round_reference,
    e1_not_equivalent_to_q4,
    evaluate_c_q4_fixture,
)
from gpu_runmultiai.strata import component_stratum, is_linear_component, is_strict_hill_component
from gpu_runmultiai.constants import ORACLE_X_GRID


def _compute_original_vs_q4_numeric_max_abs_error(
    truth_infix: str,
    q4_emitted_infix: str | None,
    *,
    dimension: int,
) -> float | None:
    if not q4_emitted_infix:
        return None
    import itertools

    import sympy as sp

    from gpu_runmultiai.oracle import audit_parse_infix_component

    truth_tree = audit_parse_infix_component(truth_infix)
    q4_tree = audit_parse_infix_component(q4_emitted_infix)
    if truth_tree is None or q4_tree is None:
        return None
    from gpu_runmultiai.oracle import _collect_variable_names_from_tree, _sympy_expr_from_component

    var_names = sorted(
        set(_collect_variable_names_from_tree(truth_tree) + _collect_variable_names_from_tree(q4_tree)),
        key=lambda name: int(name.split("_")[1]),
    )
    symbols = {name: sp.Symbol(name, real=True) for name in var_names[:dimension]}
    truth_expr = _sympy_expr_from_component(truth_tree, symbols)
    q4_expr = _sympy_expr_from_component(q4_tree, symbols)
    if truth_expr is None or q4_expr is None:
        return None
    max_error = 0.0
    for values in itertools.product(ORACLE_X_GRID, repeat=len(symbols)):
        mapping = {symbols[name]: value for name, value in zip(symbols, values)}
        truth_val = float(truth_expr.subs(mapping))
        q4_val = float(q4_expr.subs(mapping))
        max_error = max(max_error, abs(truth_val - q4_val))
    return max_error


def _q4_component_prefix(q4_prefix_raw: str, component_idx: int) -> str:
    parts = component_prefix_list_from_raw(q4_prefix_raw)
    return parts[component_idx] if component_idx < len(parts) else q4_prefix_raw


def detect_e2_identity_fallback_candidate(
    *,
    e1_prefix_raw: str,
    e2_prefix_raw: str,
    e1_component_prefix: str,
    q4_sympy_expr_canonical: str | None,
    dimension: int,
    q4_timeout_sec: float,
) -> bool:
    """§2.2 / §3.4.10: byte-identical stored prefixes in the frozen ,|, dialect."""
    if e1_prefix_raw != e2_prefix_raw:
        return False
    return e1_not_equivalent_to_q4(
        e1_component_prefix,
        q4_sympy_expr_canonical,
        dimension=dimension,
        timeout_sec=q4_timeout_sec,
    )


def _cached_call(
    call_logger,
    stage_cache: dict[str, Any],
    cache_path,
    *,
    primitive: str,
    condition: str,
    stage: str,
    unit_type: str,
    unit_id: str,
    executor,
    status_for_result=None,
    rewrite_id_for_result=None,
):
    key = cache_key(
        primitive=primitive,
        condition=condition,
        stage=stage,
        unit_type=unit_type,
        unit_id=unit_id,
    )
    executed, result = call_logger.execute_or_record(
        primitive=primitive,
        condition=condition,
        stage=stage,
        unit_type=unit_type,
        unit_id=unit_id,
        executor=executor,
        status_for_result=status_for_result,
        rewrite_id_for_result=rewrite_id_for_result,
    )
    if not executed:
        if key not in stage_cache:
            raise ResumeCacheMissError(f"resume cache miss for counted call: {key}")
        return stage_cache[key]
    safe_result = json_safe_stage_payload(result)
    stage_cache[key] = safe_result
    if cache_path is not None:
        append_stage_cache(cache_path, cache_key_value=key, payload=safe_result)
    return result


def registration_rows(
    corpus_hash: str,
    component_index: list[dict[str, Any]],
    *,
    oracle_timeout_sec: float,
    call_logger,
    stage_cache: dict[str, Any],
    cache_path,
    limit: int | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    truth_rows = []
    rewrite_rows = []
    for item in component_index[:limit]:
        system_id = item["system_id"]
        component_idx = item["component_idx"]
        record = item["record"]
        truth_prefix, truth_infix = truth_component_infix(record, component_idx)
        component_id, _ = component_id_for(corpus_hash, system_id, component_idx)

        def _truth_row():
            classified = classify_formula(truth_infix)
            return {
                "component_id": component_id,
                "system_id": system_id,
                "component_idx": component_idx,
                "truth_prefix": truth_prefix,
                "truth_infix": truth_infix,
                "classifier_parse_valid": bool(classified["valid"]),
                "hill_form": bool(classified["component_flags"][0]["hill_form"]),
                "component_flags": list(classified["component_flags"]),
            }

        truth_row = _cached_call(
            call_logger,
            stage_cache,
            cache_path,
            primitive="truth_register_classify",
            condition="registration",
            stage="truth",
            unit_type="component",
            unit_id=component_id,
            executor=_truth_row,
        )
        stratum_layer = {
            "strict_hill": "strict_hill_primary",
            "non_strict_hill": "non_strict_hill_secondary",
            "linear": "linear_control",
        }[component_stratum(record["family"], component_idx)]

        def _quantization_row():
            return {
                "component_id": component_id,
                "quantization_stratum": assign_quantization_stratum(truth_prefix),
            }

        quantization_row = _cached_call(
            call_logger,
            stage_cache,
            cache_path,
            primitive="quantization_stratum_assign",
            condition="registration",
            stage="quantization",
            unit_type="component",
            unit_id=component_id,
            executor=_quantization_row,
        )
        truth_rows.append(
            {
                **truth_row,
                "eligibility_layer": stratum_layer,
                "quantization_stratum": quantization_row["quantization_stratum"],
            }
        )

        def _rewrite_row():
            rewrite = rewrite_registration(
                system_id,
                component_idx,
                truth_prefix,
                truth_infix,
                oracle_timeout_sec=oracle_timeout_sec,
            )
            return {"component_id": component_id, **rewrite}

        rewrite_row = _cached_call(
            call_logger,
            stage_cache,
            cache_path,
            primitive="rewrite_oracle_precheck",
            condition="registration",
            stage="rewrite",
            unit_type="component",
            unit_id=component_id,
            executor=_rewrite_row,
            status_for_result=lambda row: "completed" if row["valid"] else "failed",
            rewrite_id_for_result=lambda row: row["rewrite_id"],
        )
        rewrite_rows.append(rewrite_row)
    return truth_rows, rewrite_rows


def _stage_flags(
    *,
    construction_incomplete: bool = False,
    execution_failure: bool = False,
    semantic_drift: bool = False,
    e1_oracle: dict[str, Any] | None = None,
    e2_oracle: dict[str, Any] | None = None,
    hill_form: bool | None = None,
    classifier_parse_valid: bool = False,
    classifier_parse_failure_reason: str | None = None,
) -> dict[str, Any]:
    e1 = e1_oracle or {}
    e2 = e2_oracle or {}
    return {
        "construction_incomplete": construction_incomplete,
        "execution_failure": execution_failure,
        "semantic_drift": semantic_drift,
        "e1_oracle_completed": bool(e1.get("completed")),
        "e1_oracle_equivalent": bool(e1.get("equivalent")),
        "e1_analytic_equivalent": bool(e1.get("analytic_equivalent")),
        "e1_numeric_equivalent": bool(e1.get("numeric_equivalent")),
        "e1_oracle_failure_reason": e1.get("failure_reason"),
        "e1_rational_tokens": e1.get("rational_tokens", {}),
        "e1_parsed_rationals": e1.get("parsed_rationals", {}),
        "e2_oracle_completed": bool(e2.get("completed")),
        "e2_oracle_equivalent": bool(e2.get("equivalent")),
        "e2_analytic_equivalent": bool(e2.get("analytic_equivalent")),
        "e2_numeric_equivalent": bool(e2.get("numeric_equivalent")),
        "e2_oracle_failure_reason": e2.get("failure_reason"),
        "e2_rational_tokens": e2.get("rational_tokens", {}),
        "e2_parsed_rationals": e2.get("parsed_rationals", {}),
        "hill_form": bool(hill_form),
        "classifier_parse_valid": classifier_parse_valid,
        "classifier_parse_failure_reason": classifier_parse_failure_reason,
    }


def _oracle_call_condition(condition: str, stage: str) -> str:
    if condition == "B0":
        return f"B0_{stage}"
    return condition


def _component_metrics(
    record: dict[str, Any],
    predicted_infix: str,
    component_idx: int,
) -> dict[str, Any]:
    truth_full = full_system_infix_from_record(record)
    metrics = formula_metrics(truth_full, predicted_infix)
    truth_component = extract_component_infix(truth_full, component_idx)
    pred_component = extract_component_infix(predicted_infix, component_idx)
    comparison = compare_formulas(truth_component, pred_component, skip_cas=True)
    component_valid = metrics.get("component_valid", [])
    valid = component_idx < len(component_valid) and bool(component_valid[component_idx])
    component_skeleton = metrics.get("component_exponent_aware_skeleton_exact", [])
    skeleton_exact = (
        component_idx < len(component_skeleton) and bool(component_skeleton[component_idx])
    )
    return {
        "valid": valid,
        "canonical_exact": comparison.get("canonical_exact"),
        "exponent_aware_skeleton_exact": float(skeleton_exact),
        "formula_metrics_valid": valid,
    }


def _execute_chain(
    *,
    corpus_hash: str,
    record: dict[str, Any],
    component_idx: int,
    scale: str,
    rewrite_row: dict[str, Any] | None,
    use_identity: bool,
    skip_simplifier: bool,
    run_oracles: bool,
    oracle_timeout_sec: float,
    q4_timeout_sec: float,
    simplifier_timeout_sec: float,
    call_logger,
    condition: str,
    pair_id: str,
    runtime_available: bool,
    guard,
    stage_cache: dict[str, Any] | None = None,
    cache_path=None,
) -> dict[str, Any]:
    system_id = record["system_id"]
    family = record["family"]
    component_id, _ = component_id_for(corpus_hash, system_id, component_idx)
    truth_prefix, truth_component = truth_component_infix(record, component_idx)
    rewrite_id = rewrite_row["rewrite_id"] if rewrite_row else IDENTITY_REWRITE_ID
    stratum = component_stratum(family, component_idx)

    base = {
        "condition": condition,
        "pair_id": pair_id,
        "component_id": component_id,
        "system_id": system_id,
        "component_idx": component_idx,
        "scale": scale,
        "rewrite_id": rewrite_id,
        "stratum": stratum,
        "truth_infix": truth_component,
    }

    if rewrite_row is not None and not rewrite_row.get("valid"):
        return build_outcome_row(**base, construction_incomplete=True, e0_status="construction_incomplete")
    if not runtime_available:
        return build_outcome_row(
            **base,
            execution_failure=True,
            failure_reason="ODEFormerUnavailable",
            e0_status="execution_failure",
        )

    e0_construct_primitive = "e0_identity_construct" if use_identity else "e0_analytic_construct"
    current_stage = "E0"
    e0_prefix_raw = None
    e1_prefix_raw = None
    e0_infix = None
    e1_infix = None
    stage_cache = stage_cache or {}
    try:
        env = get_env()
        if use_identity:
            prefixes = truth_system_prefixes(record)
            scaler, _ = build_identity_scaler(int(record["dimension"]))
        else:
            prefixes = replace_component_prefixes(record, component_idx, rewrite_row["rewrite_prefix"])
            scaler, _ = build_production_scaler(float(scale), int(record["dimension"]))
        base_tree = decode_system_tree(env, prefixes)
        e0_tree = forward_scale_system(env, base_tree, scaler)
        _cached_call(
            call_logger,
            stage_cache,
            cache_path,
            primitive=e0_construct_primitive,
            condition=condition,
            stage="E0",
            unit_type="pair",
            unit_id=pair_id,
            executor=lambda: e0_tree,
        )
        e0_prefix_raw = canonical_system_prefix_raw(e0_tree)
        e0_infix = tree_to_system_infix(e0_tree)
        current_stage = "E1"
        e1_tree, rescale_incomplete, rescale_proof = rescale_system(env, scaler, e0_tree)
        _cached_call(
            call_logger,
            stage_cache,
            cache_path,
            primitive="scaler_rescale_function",
            condition=condition,
            stage="E1",
            unit_type="pair",
            unit_id=pair_id,
            executor=lambda: rescale_proof,
            status_for_result=lambda _: "completed" if not rescale_incomplete else "failed",
        )
        if rescale_incomplete:
            return build_outcome_row(
                **base,
                execution_failure=True,
                rescale_incomplete=True,
                rescale_call_proof=rescale_proof,
                e0_status="completed",
                e1_status="execution_failure",
                e0_prefix_raw=e0_prefix_raw,
                e0_infix=e0_infix,
            )
        e1_prefix_raw = canonical_system_prefix_raw(e1_tree)
        e1_infix = tree_to_system_infix(e1_tree)
        e1_component_prefix = tree_to_prefix_list(e1_tree)[component_idx]

        def _run_q4():
            q4_prefix = e1_component_prefix
            return audit_q4_decimal_round_reference(
                q4_prefix,
                dimension=int(record["dimension"]),
                timeout_sec=q4_timeout_sec,
            ).as_dict()

        q4_result = _cached_call(
            call_logger,
            stage_cache,
            cache_path,
            primitive="q4_decimal_round_reference",
            condition=condition,
            stage="Q4",
            unit_type="pair" if condition != "B1" else "pair",
            unit_id=pair_id,
            executor=_run_q4,
            status_for_result=lambda row: "completed" if row["q4_construction_completed"] else "failed",
        )
        q4_completed = bool(q4_result.get("q4_construction_completed"))
        q4_emitted_infix = q4_result.get("q4_emitted_infix")
        q4_emitted_prefix = q4_result.get("q4_emitted_prefix")
        q4_sympy_expr_canonical = q4_result.get("q4_sympy_expr_canonical")
        q4_failure_reason = q4_result.get("q4_construction_failure_reason")

        e1_oracle = {"completed": False, "equivalent": False}
        e2_oracle = {"completed": False, "equivalent": False}
        if run_oracles:
            def _run_e1_oracle():
                return oracle_single_component(
                    truth_component,
                    e1_infix,
                    candidate_component_idx=component_idx,
                    timeout_sec=oracle_timeout_sec,
                    truth_component_prefix=truth_prefix,
                    candidate_component_prefix=e1_component_prefix,
                ).as_dict()

            e1_oracle = _cached_call(
                call_logger,
                stage_cache,
            cache_path,
                primitive="oracle_equivalence",
                condition=_oracle_call_condition(condition, "E1"),
                stage="E1",
                unit_type="pair",
                unit_id=pair_id,
                executor=_run_e1_oracle,
                status_for_result=lambda row: "completed" if row["completed"] else "failed",
            )
        if not q4_completed:
            return build_outcome_row(
                **base,
                q4_construction_completed=False,
                q4_construction_failure_reason=q4_failure_reason,
                rescale_incomplete=False,
                rescale_call_proof=rescale_proof,
                e0_status="completed",
                e1_status="completed",
                e0_prefix_raw=e0_prefix_raw,
                e1_prefix_raw=e1_prefix_raw,
                e0_infix=e0_infix,
                e1_infix=e1_infix,
                **_stage_flags(
                    execution_failure=True,
                    e1_oracle=e1_oracle if run_oracles else None,
                ),
            )
        e2_infix = e1_infix
        e2_prefix_raw = e1_prefix_raw
        e2_status = "skipped"
        e2_identity_fallback_candidate = False
        current_stage = "E2"
        if not skip_simplifier:
            def _run_simplifier():
                simplified_local = simplify_tree_subprocess(
                    tree_to_prefix_list(e1_tree),
                    timeout_sec=simplifier_timeout_sec,
                )
                if simplified_local.get("guard_attempts"):
                    guard.extend_child_attempts(simplified_local["guard_attempts"])
                return simplified_local

            simplified = _cached_call(
                call_logger,
                stage_cache,
                cache_path,
                primitive="simplifier_subprocess",
                condition=condition,
                stage="E2",
                unit_type="pair",
                unit_id=pair_id,
                executor=_run_simplifier,
                status_for_result=lambda row: "completed" if row.get("ok") else "failed",
            )
            if not simplified.get("ok"):
                return build_outcome_row(
                    **base,
                    rescale_incomplete=False,
                    rescale_call_proof=rescale_proof,
                    e0_status="completed",
                    e1_status="completed",
                    e2_status="execution_failure",
                    e0_prefix_raw=e0_prefix_raw,
                    e1_prefix_raw=e1_prefix_raw,
                    e0_infix=e0_infix,
                    e1_infix=e1_infix,
                    **_stage_flags(
                        execution_failure=True,
                        e1_oracle=e1_oracle if run_oracles else None,
                    ),
                )
            e2_infix = simplified["infix"]
            child_prefix = simplified.get("prefix")
            e2_prefix_raw = canonical_system_prefix_raw(child_prefix) if child_prefix else None
            e2_status = "completed"
            if run_oracles:
                def _run_e2_oracle():
                    prefix_blob = simplified.get("prefix") or ""
                    e2_component_prefix = (
                        split_components(prefix_blob)[component_idx]
                        if prefix_blob
                        else tree_to_prefix_list(e1_tree)[component_idx]
                    )
                    q4_component_prefix = _q4_component_prefix(q4_emitted_prefix or "", component_idx)
                    return oracle_single_component(
                        q4_emitted_infix or "",
                        e2_infix,
                        candidate_component_idx=component_idx,
                        timeout_sec=oracle_timeout_sec,
                        truth_component_prefix=q4_component_prefix,
                        candidate_component_prefix=e2_component_prefix,
                    ).as_dict()

                e2_oracle = _cached_call(
                    call_logger,
                    stage_cache,
                    cache_path,
                    primitive="oracle_equivalence",
                    condition=_oracle_call_condition(condition, "E2"),
                    stage="E2",
                    unit_type="pair",
                    unit_id=pair_id,
                    executor=_run_e2_oracle,
                    status_for_result=lambda row: "completed" if row["completed"] else "failed",
                )
        e2_identity_fallback_candidate = False
        if run_oracles and not skip_simplifier and e2_prefix_raw is not None:
            e2_identity_fallback_candidate = detect_e2_identity_fallback_candidate(
                e1_prefix_raw=e1_prefix_raw,
                e2_prefix_raw=e2_prefix_raw,
                e1_component_prefix=e1_component_prefix,
                q4_sympy_expr_canonical=q4_sympy_expr_canonical,
                dimension=int(record["dimension"]),
                q4_timeout_sec=q4_timeout_sec,
            )
        q4_numeric_error = None
        if q4_completed and q4_emitted_infix:
            q4_numeric_error = _compute_original_vs_q4_numeric_max_abs_error(
                truth_component,
                q4_emitted_infix,
                dimension=int(record["dimension"]),
            )
        score_infix = e2_infix if not skip_simplifier else e1_infix
        classified = classify_formula(score_infix)
        parse_valid = bool(classified["valid"])
        parse_reason = classified.get("failure_reason")
        hill_form = False
        if parse_valid and component_idx < len(classified["component_flags"]):
            hill_form = bool(classified["component_flags"][component_idx]["hill_form"])
        classify_stage = "E2" if not skip_simplifier else "E1"
        _cached_call(
            call_logger,
            stage_cache,
            cache_path,
            primitive="classify_component_flags",
            condition=condition,
            stage=classify_stage,
            unit_type="pair",
            unit_id=pair_id,
            executor=lambda: (parse_valid, parse_reason, hill_form),
            status_for_result=lambda _: "completed" if parse_valid else "failed",
        )
        metrics = _component_metrics(record, score_infix, component_idx)
        _cached_call(
            call_logger,
            stage_cache,
            cache_path,
            primitive="formula_metrics_pair",
            condition=condition,
            stage=classify_stage,
            unit_type="pair",
            unit_id=pair_id,
            executor=lambda: metrics,
            status_for_result=lambda row: "completed" if row["formula_metrics_valid"] else "failed",
        )
        flags = _stage_flags(
            construction_incomplete=False,
            execution_failure=not parse_valid
            or e2_identity_fallback_candidate
            or (
                run_oracles
                and not (e1_oracle.get("completed") and (skip_simplifier or e2_oracle.get("completed")))
            ),
            semantic_drift=bool(
                run_oracles
                and not e2_identity_fallback_candidate
                and (
                    (e1_oracle.get("completed") and not e1_oracle.get("equivalent"))
                    or (
                        not skip_simplifier
                        and e2_oracle.get("completed")
                        and not e2_oracle.get("equivalent")
                    )
                )
            ),
            e1_oracle=e1_oracle if run_oracles else None,
            e2_oracle=e2_oracle if run_oracles and not skip_simplifier else None,
            hill_form=hill_form,
            classifier_parse_valid=parse_valid,
            classifier_parse_failure_reason=parse_reason,
        )
        return build_outcome_row(
            **base,
            e2_infix_pre_classifier=score_infix if not skip_simplifier else None,
            e0_prefix_raw=e0_prefix_raw,
            e1_prefix_raw=e1_prefix_raw,
            e2_prefix_raw=e2_prefix_raw if not skip_simplifier else None,
            e0_infix=e0_infix,
            e1_infix=e1_infix,
            e2_infix=e2_infix if not skip_simplifier else None,
            e0_status="completed",
            e1_status="completed",
            e2_status=e2_status,
            q4_construction_completed=q4_completed,
            q4_emitted_prefix=q4_emitted_prefix,
            q4_emitted_infix=q4_emitted_infix,
            q4_sympy_expr_canonical=q4_sympy_expr_canonical,
            q4_construction_failure_reason=q4_failure_reason,
            rescale_incomplete=False,
            rescale_call_proof=rescale_proof,
            e2_identity_fallback_candidate=e2_identity_fallback_candidate,
            original_vs_q4_numeric_max_abs_error=q4_numeric_error,
            quantization_stratum=assign_quantization_stratum(truth_prefix),
            canonical_exact=metrics.get("canonical_exact"),
            exponent_aware_skeleton_exact=metrics.get("exponent_aware_skeleton_exact"),
            formula_metrics_valid=metrics.get("formula_metrics_valid"),
            **flags,
        )
    except Q4ContractError:
        raise
    except AuditInvariantError:
        raise
    except (ODEFormerUnavailable, ValueError, TypeError, IndexError, json.JSONDecodeError, subprocess.TimeoutExpired) as exc:
        stage = locals().get("current_stage", "E0")
        status_map = {
            "E0": ("execution_failure", None, None),
            "E1": ("completed", "execution_failure", None),
            "E2": ("completed", "completed", "execution_failure"),
        }
        e0_status, e1_status, e2_status = status_map.get(stage, ("execution_failure", None, None))
        return build_outcome_row(
            **base,
            execution_failure=True,
            failure_reason=type(exc).__name__,
            e0_status=e0_status,
            e1_status=e1_status,
            e2_status=e2_status,
            e0_prefix_raw=locals().get("e0_prefix_raw"),
            e1_prefix_raw=locals().get("e1_prefix_raw"),
            e0_infix=locals().get("e0_infix"),
            e1_infix=locals().get("e1_infix"),
        )
    except Exception as exc:
        return build_outcome_row(
            **base,
            execution_failure=True,
            failure_reason=type(exc).__name__,
            e0_status="execution_failure",
        )


def run_b0_pair(
    *,
    corpus_hash: str,
    record: dict[str, Any],
    component_idx: int,
    scale: str,
    rewrite_row: dict[str, Any],
    oracle_timeout_sec: float,
    q4_timeout_sec: float,
    simplifier_timeout_sec: float,
    call_logger,
    runtime_available: bool,
    guard,
    pair_cache: dict[str, dict[str, Any]] | None = None,
    stage_cache: dict[str, Any] | None = None,
    cache_path=None,
) -> dict[str, Any]:
    pair_id, _ = pair_id_for(corpus_hash, record["system_id"], component_idx, scale, rewrite_row["rewrite_id"])
    cache_key = ("B0", pair_id)
    if pair_cache is not None and cache_key in pair_cache:
        return pair_cache[cache_key]
    row = _execute_chain(
        corpus_hash=corpus_hash,
        record=record,
        component_idx=component_idx,
        scale=scale,
        rewrite_row=rewrite_row,
        use_identity=False,
        skip_simplifier=False,
        run_oracles=True,
        oracle_timeout_sec=oracle_timeout_sec,
        q4_timeout_sec=q4_timeout_sec,
        simplifier_timeout_sec=simplifier_timeout_sec,
        call_logger=call_logger,
        condition="B0",
        pair_id=pair_id,
        runtime_available=runtime_available,
        guard=guard,
        stage_cache=stage_cache,
        cache_path=cache_path,
    )
    if pair_cache is not None:
        pair_cache[cache_key] = row
    return row


def run_b1_pair(
    *,
    corpus_hash: str,
    record: dict[str, Any],
    component_idx: int,
    oracle_timeout_sec: float,
    q4_timeout_sec: float,
    simplifier_timeout_sec: float,
    call_logger,
    runtime_available: bool,
    guard,
    pair_cache: dict[str, dict[str, Any]] | None = None,
    stage_cache: dict[str, Any] | None = None,
    cache_path=None,
) -> dict[str, Any]:
    pair_id, _ = pair_id_for(
        corpus_hash,
        record["system_id"],
        component_idx,
        IDENTITY_SCALE,
        IDENTITY_REWRITE_ID,
    )
    cache_key = ("B1", pair_id)
    if pair_cache is not None and cache_key in pair_cache:
        return pair_cache[cache_key]
    row = _execute_chain(
        corpus_hash=corpus_hash,
        record=record,
        component_idx=component_idx,
        scale=IDENTITY_SCALE,
        rewrite_row={"rewrite_id": IDENTITY_REWRITE_ID, "valid": True},
        use_identity=True,
        skip_simplifier=False,
        run_oracles=True,
        oracle_timeout_sec=oracle_timeout_sec,
        q4_timeout_sec=q4_timeout_sec,
        simplifier_timeout_sec=simplifier_timeout_sec,
        call_logger=call_logger,
        condition="B1",
        pair_id=pair_id,
        runtime_available=runtime_available,
        guard=guard,
        stage_cache=stage_cache,
        cache_path=cache_path,
    )
    if pair_cache is not None:
        pair_cache[cache_key] = row
    return row


B2_INHERITED_E1_FIELDS = (
    "construction_incomplete",
    "q4_construction_completed",
    "q4_emitted_prefix",
    "q4_emitted_infix",
    "q4_sympy_expr_canonical",
    "q4_construction_failure_reason",
    "rescale_incomplete",
    "e1_oracle_completed",
    "e1_oracle_equivalent",
    "e1_analytic_equivalent",
    "e1_numeric_equivalent",
    "e1_oracle_failure_reason",
    "e1_prefix_raw",
    "e1_status",
    "quantization_stratum",
    "original_vs_q4_numeric_max_abs_error",
)

B2_FORBIDDEN_INHERITED_FIELDS = (
    "e2_oracle_completed",
    "e2_oracle_equivalent",
    "e2_analytic_equivalent",
    "e2_numeric_equivalent",
    "e2_identity_fallback_candidate",
    "e2_infix",
    "e2_infix_pre_classifier",
    "e2_prefix_raw",
    "hill_form",
    "classifier_parse_valid",
    "formula_metrics_valid",
    "canonical_exact",
    "exponent_aware_skeleton_exact",
    "outcome_category",
)


def _b2_identity_fields(
    *,
    pair_id: str,
    component_id: str,
    system_id: str,
    component_idx: int,
    scale: str,
    rewrite_id: str,
    stratum: str,
) -> dict[str, Any]:
    return {
        "condition": "B2",
        "pair_id": pair_id,
        "component_id": component_id,
        "system_id": system_id,
        "component_idx": component_idx,
        "scale": scale,
        "rewrite_id": rewrite_id,
        "stratum": stratum,
    }


def b2_inherited_e1_fields(b0_row: dict[str, Any]) -> dict[str, Any]:
    """F7: carry only E1-stage / pre-simplifier fields from the originating B0 row."""
    inherited = {
        key: b0_row.get(key) for key in B2_INHERITED_E1_FIELDS if key in b0_row
    }
    leaked = sorted(set(inherited) & set(B2_FORBIDDEN_INHERITED_FIELDS))
    if leaked:
        raise AuditInvariantError(f"F7 FAIL: B2 inheritance leaked E2 fields {leaked}")
    return inherited


def run_b2_pair(
    *,
    pair_id: str,
    component_id: str,
    system_id: str,
    component_idx: int,
    scale: str,
    rewrite_id: str,
    stratum: str,
    e1_infix: str,
    record: dict[str, Any],
    call_logger,
    e1_fields: dict[str, Any] | None = None,
    stage_cache: dict[str, Any] | None = None,
    cache_path=None,
    result_cache: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    if result_cache is not None and pair_id in result_cache:
        return result_cache[pair_id]
    stage_cache = stage_cache or {}
    inherited = dict(e1_fields or {})
    leaked = sorted(set(inherited) & set(B2_FORBIDDEN_INHERITED_FIELDS))
    if leaked:
        raise AuditInvariantError(f"F7 FAIL: B2 inheritance leaked E2 fields {leaked}")
    try:
        score_infix = e1_infix or ""

        def _classify():
            classified = classify_formula(score_infix)
            parse_valid = bool(classified["valid"])
            parse_reason = classified.get("failure_reason")
            hill_form = False
            if parse_valid and component_idx < len(classified["component_flags"]):
                hill_form = bool(classified["component_flags"][component_idx]["hill_form"])
            return parse_valid, parse_reason, hill_form

        parse_valid, parse_reason, hill_form = _cached_call(
            call_logger,
            stage_cache,
            cache_path,
            primitive="classify_component_flags",
            condition="B2",
            stage="E1",
            unit_type="pair",
            unit_id=pair_id,
            executor=_classify,
            status_for_result=lambda result: "completed" if result[0] else "failed",
        )
        metrics = _cached_call(
            call_logger,
            stage_cache,
            cache_path,
            primitive="formula_metrics_pair",
            condition="B2",
            stage="E1",
            unit_type="pair",
            unit_id=pair_id,
            executor=lambda: _component_metrics(record, score_infix, component_idx),
            status_for_result=lambda row: "completed" if row["formula_metrics_valid"] else "failed",
        )
        row = build_outcome_row(
            **{
                **_b2_identity_fields(
                    pair_id=pair_id,
                    component_id=component_id,
                    system_id=system_id,
                    component_idx=component_idx,
                    scale=scale,
                    rewrite_id=rewrite_id,
                    stratum=stratum,
                ),
                **inherited,
                "e1_status": inherited.get("e1_status") or "completed",
                "e1_infix": e1_infix,
                "classifier_parse_valid": parse_valid,
                "classifier_parse_failure_reason": parse_reason,
                "hill_form": hill_form,
                "canonical_exact": metrics.get("canonical_exact"),
                "exponent_aware_skeleton_exact": metrics.get("exponent_aware_skeleton_exact"),
                "formula_metrics_valid": metrics.get("formula_metrics_valid"),
            }
        )
    except AuditInvariantError:
        raise
    except Exception as exc:
        row = build_outcome_row(
            **{
                **_b2_identity_fields(
                    pair_id=pair_id,
                    component_id=component_id,
                    system_id=system_id,
                    component_idx=component_idx,
                    scale=scale,
                    rewrite_id=rewrite_id,
                    stratum=stratum,
                ),
                **inherited,
                "execution_failure": True,
                "failure_reason": type(exc).__name__,
                "e1_status": "execution_failure",
            }
        )
    if result_cache is not None:
        result_cache[pair_id] = row
    return row


def run_b4_row(
    *,
    corpus_hash: str,
    record: dict[str, Any],
    component_idx: int,
    call_logger,
    stage_cache: dict[str, Any] | None = None,
    cache_path=None,
    result_cache: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    system_id = record["system_id"]
    component_id, _ = component_id_for(corpus_hash, system_id, component_idx)
    pair_id, _ = pair_id_for(
        corpus_hash,
        system_id,
        component_idx,
        IDENTITY_SCALE,
        TRUTH_COPY_REWRITE_ID,
    )
    if result_cache is not None and pair_id in result_cache:
        return result_cache[pair_id]
    stage_cache = stage_cache or {}
    truth_full = full_system_infix_from_record(record)
    try:
        def _classify_truth():
            classified = classify_formula(truth_full)
            return classified

        classified = _cached_call(
            call_logger,
            stage_cache,
            cache_path,
            primitive="classify_component_flags",
            condition="B4",
            stage="truth_copy",
            unit_type="pair",
            unit_id=pair_id,
            executor=_classify_truth,
            status_for_result=lambda _: "completed",
        )
        metrics = _cached_call(
            call_logger,
            stage_cache,
            cache_path,
            primitive="formula_metrics_pair",
            condition="B4",
            stage="truth_copy",
            unit_type="pair",
            unit_id=pair_id,
            executor=lambda: _component_metrics(record, truth_full, component_idx),
            status_for_result=lambda _: "completed",
        )
        row = {
            "pair_id": pair_id,
            "component_id": component_id,
            "system_id": system_id,
            "component_idx": component_idx,
            "truth_infix": extract_component_infix(truth_full, component_idx),
            "valid": bool(metrics["formula_metrics_valid"]),
            "canonical_exact": metrics.get("canonical_exact"),
            "exponent_aware_skeleton_exact": metrics.get("exponent_aware_skeleton_exact"),
            "classifier_parse_valid": bool(classified["valid"]),
            "classifier_parse_failure_reason": classified.get("failure_reason"),
            "hill_form": bool(classified["component_flags"][component_idx]["hill_form"]),
            "formula_metrics_valid": metrics.get("formula_metrics_valid"),
        }
    except AuditInvariantError:
        raise
    except Exception as exc:
        row = {
            "pair_id": pair_id,
            "component_id": component_id,
            "system_id": system_id,
            "component_idx": component_idx,
            "valid": False,
            "execution_failure": True,
            "failure_reason": type(exc).__name__,
        }
    if result_cache is not None:
        result_cache[pair_id] = row
    return row


def run_negative_controls(
    component_index: list[dict[str, Any]],
    *,
    oracle_timeout_sec: float,
    call_logger,
    corpus_hash: str | None = None,
    stage_cache: dict[str, Any] | None = None,
    cache_path=None,
    limit: int = N1_COUNT,
) -> list[dict[str, Any]]:
    from gpu_runmultiai.ids import negative_canonical_key, sha256_hex

    rows = []
    stage_cache = stage_cache or {}
    ordered = sorted(
        component_index,
        key=lambda item: sha256_hex(negative_canonical_key(item["system_id"], item["component_idx"])),
    )[:limit]
    for item in ordered:
        record = item["record"]
        system_id = item["system_id"]
        component_idx = item["component_idx"]
        truth_prefix, truth_infix = truth_component_infix(record, component_idx)
        negative_id, _, _ = negative_id_for(system_id, component_idx)

        def _negative_row():
            return negative_control_row(
                system_id,
                component_idx,
                truth_prefix,
                truth_infix,
                oracle_timeout_sec=oracle_timeout_sec,
            )

        row = _cached_call(
            call_logger,
            stage_cache,
            cache_path,
            primitive="oracle_equivalence",
            condition="N1",
            stage="negative",
            unit_type="negative",
            unit_id=negative_id,
            executor=_negative_row,
            status_for_result=lambda payload: "completed" if payload["valid"] else "failed",
        )
        if corpus_hash is not None:
            component_id, _ = component_id_for(corpus_hash, system_id, component_idx)
            row = {**row, "component_id": component_id}
        rows.append(row)
    return rows


def select_b3_pairs(pair_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    strict = [
        row
        for row in pair_rows
        if row.get("eligibility_layer") == "strict_hill_primary" and row.get("condition") == "B0"
    ]
    ordered = sorted(strict, key=lambda row: row["pair_id"].split(":", 1)[1])
    return ordered[:B3_PAIR_COUNT]


def run_b3_pairs(
    selected: list[dict[str, Any]],
    *,
    call_logger,
    stage_cache: dict[str, Any] | None = None,
    cache_path=None,
    result_cache: dict[str, dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    rows = []
    stage_cache = stage_cache or {}
    for row in selected:
        pair_id = row["pair_id"]
        if result_cache is not None and pair_id in result_cache:
            rows.append(result_cache[pair_id])
            continue
        component_idx = int(row["component_idx"])
        truth = row.get("truth_infix") or ""
        pred_system = row.get("e2_infix_pre_classifier") or row.get("e2_infix") or ""

        def _b3_payload(
            *,
            cas_compare_completed: bool,
            cas_compare_valid: bool,
            canonical_exact: Any,
            failure_reason: str | None,
        ) -> dict[str, Any]:
            # §2.5.4: terminal is a conjunct of B0-row classifier/metric flags and the
            # executed CAS result; `cas_compare_completed` reflects execution, not key presence.
            classifier_parse_valid = bool(row.get("classifier_parse_valid"))
            formula_metrics_valid = bool(row.get("formula_metrics_valid"))
            diagnostic_complete = bool(
                classifier_parse_valid
                and formula_metrics_valid
                and cas_compare_completed
                and cas_compare_valid
            )
            return {
                "pair_id": pair_id,
                "component_id": row.get("component_id"),
                "condition": "B3",
                "partition_scope": "diagnostic",
                "classifier_parse_valid": classifier_parse_valid,
                "formula_metrics_valid": formula_metrics_valid,
                "cas_compare_completed": cas_compare_completed,
                "cas_compare_valid": bool(cas_compare_valid),
                "canonical_exact": canonical_exact,
                # Exponent-aware skeleton comes from the B0 formula_metrics call; the CAS
                # comparison only contributes canonical/symbolic equivalence.
                "exponent_aware_skeleton_exact": row.get("exponent_aware_skeleton_exact"),
                "failure_reason": failure_reason,
                "valid": bool(cas_compare_valid),
                "terminal_outcome": "diagnostic_complete" if diagnostic_complete else "diagnostic_failed",
            }

        def _record_failed_b3(failure_reason: str) -> dict[str, Any]:
            if not call_logger.is_recorded(
                primitive="compare_formulas_cas",
                condition="B3",
                stage="CAS",
                unit_type="pair",
                unit_id=pair_id,
            ):
                call_logger.assert_pre_call_ceiling("B3")
                call_logger.record(
                    primitive="compare_formulas_cas",
                    condition="B3",
                    stage="CAS",
                    unit_type="pair",
                    unit_id=pair_id,
                    status="failed",
                    duration_sec=0.0,
                )
                key = cache_key(
                    primitive="compare_formulas_cas",
                    condition="B3",
                    stage="CAS",
                    unit_type="pair",
                    unit_id=pair_id,
                )
                payload_cache = {
                    "cas_compare_completed": False,
                    "failure_reason": failure_reason,
                }
                stage_cache[key] = payload_cache
                if cache_path is not None:
                    append_stage_cache(cache_path, cache_key_value=key, payload=payload_cache)
            return _b3_payload(
                cas_compare_completed=False,
                cas_compare_valid=False,
                canonical_exact=None,
                failure_reason=failure_reason,
            )

        try:
            def _compare():
                parts = split_components(pred_system)
                if component_idx < len(parts):
                    pred = extract_component_infix("|".join(parts), component_idx)
                else:
                    pred = pred_system
                with time_limit(CAS_TIMEOUT_SEC):
                    comparison = compare_formulas(truth, pred, skip_cas=False)
                return {"cas_compare_completed": True, "comparison": comparison}

            cas_result = _cached_call(
                call_logger,
                stage_cache,
                cache_path,
                primitive="compare_formulas_cas",
                condition="B3",
                stage="CAS",
                unit_type="pair",
                unit_id=pair_id,
                executor=_compare,
                status_for_result=lambda result: "completed"
                if result.get("cas_compare_completed")
                else "failed",
            )
            if not cas_result.get("cas_compare_completed"):
                payload = _b3_payload(
                    cas_compare_completed=False,
                    cas_compare_valid=False,
                    canonical_exact=None,
                    failure_reason=cas_result.get("failure_reason"),
                )
            else:
                comparison = cas_result.get("comparison", {})
                payload = _b3_payload(
                    cas_compare_completed=True,
                    cas_compare_valid=bool(comparison.get("valid")),
                    canonical_exact=comparison.get("canonical_exact"),
                    failure_reason=comparison.get("failure_reason"),
                )
        except AuditInvariantError:
            raise
        except Exception as exc:
            payload = _record_failed_b3(type(exc).__name__)
        if result_cache is not None:
            result_cache[pair_id] = payload
        rows.append(payload)
    return rows


def run_d2_pair(
    *,
    corpus_hash: str,
    record: dict[str, Any],
    component_idx: int,
    rewrite_row: dict[str, Any],
    oracle_timeout_sec: float,
    q4_timeout_sec: float,
    simplifier_timeout_sec: float,
    call_logger,
    runtime_available: bool,
    guard,
    pair_cache: dict[str, dict[str, Any]] | None = None,
    stage_cache: dict[str, Any] | None = None,
    cache_path=None,
) -> dict[str, Any]:
    pair_id, _ = pair_id_for(
        corpus_hash,
        record["system_id"],
        component_idx,
        "5.0",
        rewrite_row["rewrite_id"],
    )
    cache_key = ("D2", pair_id)
    if pair_cache is not None and cache_key in pair_cache:
        return pair_cache[cache_key]
    row = _execute_chain(
        corpus_hash=corpus_hash,
        record=record,
        component_idx=component_idx,
        scale="5.0",
        rewrite_row=rewrite_row,
        use_identity=False,
        skip_simplifier=False,
        run_oracles=True,
        oracle_timeout_sec=oracle_timeout_sec,
        q4_timeout_sec=q4_timeout_sec,
        simplifier_timeout_sec=simplifier_timeout_sec,
        call_logger=call_logger,
        condition="D2",
        pair_id=pair_id,
        runtime_available=runtime_available,
        guard=guard,
        stage_cache=stage_cache,
        cache_path=cache_path,
    )
    if pair_cache is not None:
        pair_cache[cache_key] = row
    return row


def run_c_q4_fixtures(
    *,
    call_logger,
    q4_timeout_sec: float = Q4_TIMEOUT_SEC,
    stage_cache: dict[str, Any] | None = None,
    cache_path=None,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    stage_cache = stage_cache or {}
    for fixture in C_Q4_FIXTURES:
        fixture_id = fixture["fixture_id"]

        def _executor(current_fixture=fixture):
            return evaluate_c_q4_fixture(current_fixture, timeout_sec=q4_timeout_sec)

        row = _cached_call(
            call_logger,
            stage_cache,
            cache_path,
            primitive="q4_decimal_round_reference",
            condition="C_q4",
            stage="Q4",
            unit_type="fixture",
            unit_id=fixture_id,
            executor=_executor,
            status_for_result=lambda payload: "completed" if payload.get("fixture_pass") else "failed",
        )
        rows.append(row)
    return rows
