"""Audit pipeline primitives and condition runners."""

from __future__ import annotations

from typing import Any

from evaluation.gpu_run5_structure import classify_formula
from gpu_run4.formulas import compare_formulas, parse_system
from gpu_run5.evaluation import formula_metrics

from gpu_runmultiai.constants import (
    B3_PAIR_COUNT,
    IDENTITY_REWRITE_ID,
    IDENTITY_SCALE,
    N1_COUNT,
)
from gpu_runmultiai.ids import component_id_for, pair_id_for
from gpu_runmultiai.odeformer_runtime import (
    ODEFormerUnavailable,
    build_identity_scaler,
    build_production_scaler,
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
from gpu_runmultiai.oracle import oracle_equivalence, oracle_single_component, prefix_to_infix_component
from gpu_runmultiai.outcomes import build_outcome_row
from gpu_runmultiai.rewrites import (
    negative_control_row,
    rewrite_registration,
    truth_component_infix,
)
from gpu_runmultiai.strata import component_stratum, is_linear_component, is_strict_hill_component


def registration_rows(
    corpus_hash: str,
    component_index: list[dict[str, Any]],
    *,
    oracle_timeout_sec: float,
    call_logger,
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
        classified = classify_formula(truth_infix)
        truth_rows.append(
            {
                "component_id": component_id,
                "system_id": system_id,
                "component_idx": component_idx,
                "truth_prefix": truth_prefix,
                "truth_infix": truth_infix,
                "classifier_parse_valid": bool(classified["valid"]),
                "hill_form": bool(classified["component_flags"][0]["hill_form"]),
            }
        )
        call_logger.record(
            primitive="truth_register_classify",
            condition="registration",
            stage="truth",
            unit_type="component",
            unit_id=component_id,
            status="completed",
        )
        rewrite = rewrite_registration(
            system_id,
            component_idx,
            truth_prefix,
            truth_infix,
            oracle_timeout_sec=oracle_timeout_sec,
        )
        rewrite_rows.append({"component_id": component_id, **rewrite})
        call_logger.record(
            primitive="rewrite_oracle_precheck",
            condition="registration",
            stage="rewrite",
            unit_type="component",
            unit_id=component_id,
            status="completed" if rewrite["valid"] else "failed",
            rewrite_id=rewrite["rewrite_id"],
        )
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
        "e2_oracle_completed": bool(e2.get("completed")),
        "e2_oracle_equivalent": bool(e2.get("equivalent")),
        "e2_analytic_equivalent": bool(e2.get("analytic_equivalent")),
        "e2_numeric_equivalent": bool(e2.get("numeric_equivalent")),
        "hill_form": bool(hill_form),
        "classifier_parse_valid": classifier_parse_valid,
        "classifier_parse_failure_reason": classifier_parse_failure_reason,
    }


def _component_metrics(
    record: dict[str, Any],
    predicted_infix: str,
    component_idx: int,
) -> dict[str, Any]:
    truth_full = full_system_infix_from_record(record)
    metrics = formula_metrics(truth_full, predicted_infix)
    component_valid = metrics.get("component_valid", [])
    valid = component_idx < len(component_valid) and bool(component_valid[component_idx])
    return {
        "valid": valid,
        "canonical_exact": metrics.get("canonical_exact"),
        "exponent_aware_skeleton_exact": metrics.get("exponent_aware_skeleton_exact"),
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
    simplifier_timeout_sec: float,
    call_logger,
    condition: str,
    pair_id: str,
    runtime_available: bool,
    guard,
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
    try:
        env = get_env()
        if use_identity:
            prefixes = truth_system_prefixes(record)
            scaler, _ = build_identity_scaler(int(record["dimension"]))
        else:
            prefixes = replace_component_prefixes(record, component_idx, rewrite_row["rewrite_prefix"])
            scaler, _ = build_production_scaler(float(scale), int(record["dimension"]))
        base_tree = decode_system_tree(env, prefixes)
        call_logger.record(
            primitive=e0_construct_primitive,
            condition=condition,
            stage="E0",
            unit_type="pair",
            unit_id=pair_id,
            status="completed",
        )
        e0_tree = forward_scale_system(env, base_tree, scaler)
        e0_prefix_raw = "|".join(tree_to_prefix_list(e0_tree))
        e0_infix = tree_to_system_infix(e0_tree)
        e1_tree, rescale_incomplete = rescale_system(env, scaler, e0_tree)
        call_logger.record(
            primitive="scaler_rescale_function",
            condition=condition,
            stage="E1",
            unit_type="pair",
            unit_id=pair_id,
            status="completed" if not rescale_incomplete else "failed",
        )
        if rescale_incomplete:
            return build_outcome_row(
                **base,
                execution_failure=True,
                rescale_incomplete=True,
                e0_status="completed",
                e1_status="execution_failure",
                e0_prefix_raw=e0_prefix_raw,
                e0_infix=e0_infix,
            )
        e1_prefix_raw = "|".join(tree_to_prefix_list(e1_tree))
        e1_infix = tree_to_system_infix(e1_tree)
        e1_oracle = {"completed": False, "equivalent": False}
        e2_oracle = {"completed": False, "equivalent": False}
        if run_oracles:
            e1_oracle = oracle_single_component(
                truth_component,
                e1_infix,
                candidate_component_idx=component_idx,
                timeout_sec=oracle_timeout_sec,
            ).as_dict()
            call_logger.record(
                primitive="oracle_equivalence",
                condition="B0_E1" if condition in {"B0", "D2"} else condition,
                stage="E1",
                unit_type="pair",
                unit_id=pair_id,
                status="completed" if e1_oracle["completed"] else "failed",
            )
        e2_infix = e1_infix
        e2_prefix_raw = e1_prefix_raw
        e2_status = "skipped"
        if not skip_simplifier:
            simplified = simplify_tree_subprocess(
                tree_to_prefix_list(e1_tree),
                timeout_sec=simplifier_timeout_sec,
            )
            if simplified.get("guard_attempts"):
                guard.extend_child_attempts(simplified["guard_attempts"])
            call_logger.record(
                primitive="simplifier_subprocess",
                condition=condition,
                stage="E2",
                unit_type="pair",
                unit_id=pair_id,
                status="completed" if simplified.get("ok") else "failed",
            )
            if not simplified.get("ok"):
                return build_outcome_row(
                    **base,
                    execution_failure=True,
                    e0_status="completed",
                    e1_status="completed",
                    e2_status="execution_failure",
                    e0_prefix_raw=e0_prefix_raw,
                    e1_prefix_raw=e1_prefix_raw,
                    e0_infix=e0_infix,
                    e1_infix=e1_infix,
                    **_stage_flags(e1_oracle=e1_oracle if run_oracles else None),
                )
            e2_infix = simplified["infix"]
            e2_prefix_raw = simplified.get("prefix") or "|".join(tree_to_prefix_list(e1_tree))
            e2_status = "completed"
            if run_oracles:
                e2_oracle = oracle_single_component(
                    truth_component,
                    e2_infix,
                    candidate_component_idx=component_idx,
                    timeout_sec=oracle_timeout_sec,
                ).as_dict()
                call_logger.record(
                    primitive="oracle_equivalence",
                    condition="B0_E2" if condition in {"B0", "D2"} else condition,
                    stage="E2",
                    unit_type="pair",
                    unit_id=pair_id,
                    status="completed" if e2_oracle["completed"] else "failed",
                )
        score_infix = e2_infix if not skip_simplifier else e1_infix
        classified = classify_formula(score_infix)
        parse_valid = bool(classified["valid"])
        parse_reason = classified.get("failure_reason")
        hill_form = False
        if parse_valid and component_idx < len(classified["component_flags"]):
            hill_form = bool(classified["component_flags"][component_idx]["hill_form"])
        call_logger.record(
            primitive="classify_component_flags",
            condition=condition,
            stage="E2" if not skip_simplifier else "E1",
            unit_type="pair",
            unit_id=pair_id,
            status="completed" if parse_valid else "failed",
        )
        metrics = _component_metrics(record, score_infix, component_idx)
        call_logger.record(
            primitive="formula_metrics_pair",
            condition=condition,
            stage="E2" if not skip_simplifier else "E1",
            unit_type="pair",
            unit_id=pair_id,
            status="completed" if metrics["formula_metrics_valid"] else "failed",
        )
        flags = _stage_flags(
            construction_incomplete=False,
            execution_failure=not parse_valid
            or (
                run_oracles
                and not (e1_oracle.get("completed") and (skip_simplifier or e2_oracle.get("completed")))
            ),
            semantic_drift=bool(
                run_oracles
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
            canonical_exact=metrics.get("canonical_exact"),
            exponent_aware_skeleton_exact=metrics.get("exponent_aware_skeleton_exact"),
            formula_metrics_valid=metrics.get("formula_metrics_valid"),
            **flags,
        )
    except ODEFormerUnavailable:
        return build_outcome_row(
            **base,
            execution_failure=True,
            failure_reason="ODEFormerUnavailable",
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
    simplifier_timeout_sec: float,
    call_logger,
    runtime_available: bool,
    guard,
) -> dict[str, Any]:
    pair_id, _ = pair_id_for(corpus_hash, record["system_id"], component_idx, scale, rewrite_row["rewrite_id"])
    return _execute_chain(
        corpus_hash=corpus_hash,
        record=record,
        component_idx=component_idx,
        scale=scale,
        rewrite_row=rewrite_row,
        use_identity=False,
        skip_simplifier=False,
        run_oracles=True,
        oracle_timeout_sec=oracle_timeout_sec,
        simplifier_timeout_sec=simplifier_timeout_sec,
        call_logger=call_logger,
        condition="B0",
        pair_id=pair_id,
        runtime_available=runtime_available,
        guard=guard,
    )


def run_b1_pair(
    *,
    corpus_hash: str,
    record: dict[str, Any],
    component_idx: int,
    oracle_timeout_sec: float,
    simplifier_timeout_sec: float,
    call_logger,
    runtime_available: bool,
    guard,
) -> dict[str, Any]:
    pair_id, _ = pair_id_for(
        corpus_hash,
        record["system_id"],
        component_idx,
        IDENTITY_SCALE,
        IDENTITY_REWRITE_ID,
    )
    return _execute_chain(
        corpus_hash=corpus_hash,
        record=record,
        component_idx=component_idx,
        scale=IDENTITY_SCALE,
        rewrite_row={"rewrite_id": IDENTITY_REWRITE_ID, "valid": True},
        use_identity=True,
        skip_simplifier=False,
        run_oracles=False,
        oracle_timeout_sec=oracle_timeout_sec,
        simplifier_timeout_sec=simplifier_timeout_sec,
        call_logger=call_logger,
        condition="B1",
        pair_id=pair_id,
        runtime_available=runtime_available,
        guard=guard,
    )


def run_b2_pair(
    *,
    b0_row: dict[str, Any],
    record: dict[str, Any],
    call_logger,
) -> dict[str, Any]:
    pair_id = b0_row["pair_id"]
    component_idx = b0_row["component_idx"]
    score_infix = b0_row.get("e1_infix") or ""
    classified = classify_formula(score_infix)
    parse_valid = bool(classified["valid"])
    parse_reason = classified.get("failure_reason")
    hill_form = False
    if parse_valid and component_idx < len(classified["component_flags"]):
        hill_form = bool(classified["component_flags"][component_idx]["hill_form"])
    call_logger.record(
        primitive="classify_component_flags",
        condition="B2",
        stage="E1",
        unit_type="pair",
        unit_id=pair_id,
        status="completed" if parse_valid else "failed",
    )
    metrics = _component_metrics(record, score_infix, component_idx)
    call_logger.record(
        primitive="formula_metrics_pair",
        condition="B2",
        stage="E1",
        unit_type="pair",
        unit_id=pair_id,
        status="completed" if metrics["formula_metrics_valid"] else "failed",
    )
    return {
        **b0_row,
        "condition": "B2",
        "classifier_parse_valid": parse_valid,
        "classifier_parse_failure_reason": parse_reason,
        "hill_form": hill_form,
        "canonical_exact": metrics.get("canonical_exact"),
        "exponent_aware_skeleton_exact": metrics.get("exponent_aware_skeleton_exact"),
        "formula_metrics_valid": metrics.get("formula_metrics_valid"),
    }


def run_b4_row(
    *,
    corpus_hash: str,
    record: dict[str, Any],
    component_idx: int,
    call_logger,
) -> dict[str, Any]:
    system_id = record["system_id"]
    component_id, _ = component_id_for(corpus_hash, system_id, component_idx)
    truth_full = full_system_infix_from_record(record)
    metrics = formula_metrics(truth_full, truth_full)
    classified = classify_formula(truth_full)
    call_logger.record(
        primitive="classify_component_flags",
        condition="B4",
        stage="truth_copy",
        unit_type="component",
        unit_id=component_id,
        status="completed",
    )
    call_logger.record(
        primitive="formula_metrics_pair",
        condition="B4",
        stage="truth_copy",
        unit_type="component",
        unit_id=component_id,
        status="completed",
    )
    return {
        "component_id": component_id,
        "valid": bool(metrics["valid"]),
        "canonical_exact": metrics.get("canonical_exact"),
        "classifier_parse_valid": bool(classified["valid"]),
        "hill_form": bool(classified["component_flags"][component_idx]["hill_form"]),
    }


def run_negative_controls(
    component_index: list[dict[str, Any]],
    *,
    oracle_timeout_sec: float,
    call_logger,
    limit: int = N1_COUNT,
) -> list[dict[str, Any]]:
    from gpu_runmultiai.ids import negative_canonical_key, sha256_hex

    rows = []
    ordered = sorted(
        component_index,
        key=lambda item: sha256_hex(negative_canonical_key(item["system_id"], item["component_idx"])),
    )[:limit]
    for item in ordered:
        record = item["record"]
        system_id = item["system_id"]
        component_idx = item["component_idx"]
        truth_prefix, truth_infix = truth_component_infix(record, component_idx)
        row = negative_control_row(
            system_id,
            component_idx,
            truth_prefix,
            truth_infix,
            oracle_timeout_sec=oracle_timeout_sec,
        )
        call_logger.record(
            primitive="oracle_equivalence",
            condition="N1",
            stage="negative",
            unit_type="negative",
            unit_id=row["negative_id"],
            status="completed" if row["valid"] else "failed",
        )
        rows.append(row)
    return rows


def select_b3_pairs(pair_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    strict = [row for row in pair_rows if row.get("stratum") == "strict_hill" and row.get("condition") == "B0"]
    ordered = sorted(strict, key=lambda row: row["pair_id"].split(":", 1)[1])
    return ordered[:B3_PAIR_COUNT]


def run_b3_pairs(
    selected: list[dict[str, Any]],
    *,
    call_logger,
) -> list[dict[str, Any]]:
    rows = []
    for row in selected:
        component_idx = int(row["component_idx"])
        truth = row.get("truth_infix") or ""
        pred_system = row.get("e2_infix_pre_classifier") or row.get("e2_infix") or ""
        from gpu_runmultiai.oracle import extract_component_infix

        try:
            pred = extract_component_infix(pred_system, component_idx) if " | " in pred_system else pred_system
        except IndexError:
            pred = pred_system
        comparison = compare_formulas(truth, pred, skip_cas=False)
        call_logger.record(
            primitive="compare_formulas_cas",
            condition="B3",
            stage="CAS",
            unit_type="pair",
            unit_id=row["pair_id"],
            status="completed",
        )
        rows.append({"pair_id": row["pair_id"], **comparison})
    return rows


def run_d2_pair(
    *,
    corpus_hash: str,
    record: dict[str, Any],
    component_idx: int,
    rewrite_row: dict[str, Any],
    oracle_timeout_sec: float,
    simplifier_timeout_sec: float,
    call_logger,
    runtime_available: bool,
    guard,
) -> dict[str, Any]:
    pair_id, _ = pair_id_for(
        corpus_hash,
        record["system_id"],
        component_idx,
        "5.0",
        rewrite_row["rewrite_id"],
    )
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
        simplifier_timeout_sec=simplifier_timeout_sec,
        call_logger=call_logger,
        condition="D2",
        pair_id=pair_id,
        runtime_available=runtime_available,
        guard=guard,
    )
    return row
