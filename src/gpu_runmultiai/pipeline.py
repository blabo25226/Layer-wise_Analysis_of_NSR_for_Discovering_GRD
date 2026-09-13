"""Audit pipeline primitives and condition runners."""

from __future__ import annotations

from typing import Any, Callable

from evaluation.gpu_run5_structure import classify_formula
from gpu_run4.formulas import compare_formulas
from gpu_run5.evaluation import formula_metrics

from gpu_runmultiai.constants import (
    B3_PAIR_COUNT,
    IDENTITY_REWRITE_ID,
    IDENTITY_SCALE,
    N1_COUNT,
    PRIMARY_SCALES,
    TRUTH_COPY_REWRITE_ID,
)
from gpu_runmultiai.ids import component_id_for, pair_id_for
from gpu_runmultiai.odeformer_runtime import (
    ODEFormerUnavailable,
    build_production_scaler,
    decode_system_tree,
    get_env,
    replace_component_prefixes,
    rescale_system,
    simplify_tree_subprocess,
    tree_to_system_infix,
)
from gpu_runmultiai.oracle import oracle_equivalence
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
                "hill_form": bool(classified["component_flags"][component_idx]["hill_form"]),
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
    }


def run_b0_pair(
    *,
    corpus_hash: str,
    record: dict[str, Any],
    component_idx: int,
    scale: str,
    rewrite_row: dict[str, Any],
    oracle_timeout_sec: float,
    call_logger,
    runtime_available: bool,
) -> dict[str, Any]:
    system_id = record["system_id"]
    family = record["family"]
    rewrite_id = rewrite_row["rewrite_id"]
    pair_id, _ = pair_id_for(corpus_hash, system_id, component_idx, scale, rewrite_id)
    component_id, _ = component_id_for(corpus_hash, system_id, component_idx)
    truth_prefix, truth_infix = truth_component_infix(record, component_idx)
    if not rewrite_row.get("valid"):
        return build_outcome_row(
            condition="B0",
            pair_id=pair_id,
            component_id=component_id,
            system_id=system_id,
            component_idx=component_idx,
            scale=scale,
            rewrite_id=rewrite_id,
            stratum=component_stratum(family, component_idx),
            construction_incomplete=True,
        )
    if not runtime_available:
        return build_outcome_row(
            condition="B0",
            pair_id=pair_id,
            component_id=component_id,
            system_id=system_id,
            component_idx=component_idx,
            scale=scale,
            rewrite_id=rewrite_id,
            stratum=component_stratum(family, component_idx),
            execution_failure=True,
            failure_reason="ODEFormerUnavailable",
        )
    try:
        env = get_env()
        prefixes = replace_component_prefixes(record, component_idx, rewrite_row["rewrite_prefix"])
        call_logger.record(
            primitive="e0_analytic_construct",
            condition="B0",
            stage="E0",
            unit_type="pair",
            unit_id=pair_id,
            status="completed",
        )
        e0_tree = decode_system_tree(env, prefixes)
        e0_infix = tree_to_system_infix(e0_tree)
        scaler, _ = build_production_scaler(float(scale), int(record["dimension"]))
        e1_tree, rescale_incomplete = rescale_system(env, scaler, e0_tree)
        call_logger.record(
            primitive="scaler_rescale_function",
            condition="B0",
            stage="E1",
            unit_type="pair",
            unit_id=pair_id,
            status="completed" if not rescale_incomplete else "failed",
        )
        if rescale_incomplete:
            return build_outcome_row(
                condition="B0",
                pair_id=pair_id,
                component_id=component_id,
                system_id=system_id,
                component_idx=component_idx,
                scale=scale,
                rewrite_id=rewrite_id,
                stratum=component_stratum(family, component_idx),
                execution_failure=True,
                rescale_incomplete=True,
            )
        e1_infix = tree_to_system_infix(e1_tree)
        simplified = simplify_tree_subprocess(prefixes)
        call_logger.record(
            primitive="simplifier_subprocess",
            condition="B0",
            stage="E2",
            unit_type="pair",
            unit_id=pair_id,
            status="completed" if simplified.get("ok") else "failed",
        )
        if not simplified.get("ok"):
            return build_outcome_row(
                condition="B0",
                pair_id=pair_id,
                component_id=component_id,
                system_id=system_id,
                component_idx=component_idx,
                scale=scale,
                rewrite_id=rewrite_id,
                stratum=component_stratum(family, component_idx),
                execution_failure=True,
            )
        e2_infix = simplified["infix"]
        e1_oracle = oracle_equivalence(
            truth_infix, e1_infix, component_idx=component_idx, timeout_sec=oracle_timeout_sec
        ).as_dict()
        e2_oracle = oracle_equivalence(
            truth_infix, e2_infix, component_idx=component_idx, timeout_sec=oracle_timeout_sec
        ).as_dict()
        for stage, oracle in (("E1", e1_oracle), ("E2", e2_oracle)):
            call_logger.record(
                primitive="oracle_equivalence",
                condition="B0",
                stage=stage,
                unit_type="pair",
                unit_id=pair_id,
                status="completed" if oracle["completed"] else "failed",
            )
        classified = classify_formula(e2_infix)
        hill_form = bool(classified["component_flags"][component_idx]["hill_form"])
        call_logger.record(
            primitive="classify_component_flags",
            condition="B0",
            stage="E2",
            unit_type="pair",
            unit_id=pair_id,
            status="completed",
        )
        metrics = formula_metrics(truth_infix, e2_infix)
        call_logger.record(
            primitive="formula_metrics_pair",
            condition="B0",
            stage="E2",
            unit_type="pair",
            unit_id=pair_id,
            status="completed",
        )
        flags = _stage_flags(
            construction_incomplete=False,
            execution_failure=not (e1_oracle["completed"] and e2_oracle["completed"]),
            semantic_drift=bool(
                (e1_oracle.get("completed") and not e1_oracle.get("equivalent"))
                or (e2_oracle.get("completed") and not e2_oracle.get("equivalent"))
            ),
            e1_oracle=e1_oracle,
            e2_oracle=e2_oracle,
            hill_form=hill_form,
            classifier_parse_valid=bool(classified["valid"]),
        )
        return build_outcome_row(
            condition="B0",
            pair_id=pair_id,
            component_id=component_id,
            system_id=system_id,
            component_idx=component_idx,
            scale=scale,
            rewrite_id=rewrite_id,
            stratum=component_stratum(family, component_idx),
            e2_infix_pre_classifier=e2_infix,
            e0_infix=e0_infix,
            e1_infix=e1_infix,
            canonical_exact=metrics.get("canonical_exact"),
            exponent_aware_skeleton_exact=metrics.get("exponent_aware_skeleton_exact"),
            **flags,
        )
    except ODEFormerUnavailable:
        return build_outcome_row(
            condition="B0",
            pair_id=pair_id,
            component_id=component_id,
            system_id=system_id,
            component_idx=component_idx,
            scale=scale,
            rewrite_id=rewrite_id,
            stratum=component_stratum(family, component_idx),
            execution_failure=True,
            failure_reason="ODEFormerUnavailable",
        )


def run_b4_row(
    *,
    corpus_hash: str,
    record: dict[str, Any],
    component_idx: int,
    call_logger,
) -> dict[str, Any]:
    system_id = record["system_id"]
    component_id, _ = component_id_for(corpus_hash, system_id, component_idx)
    truth_prefix, truth_infix = truth_component_infix(record, component_idx)
    metrics = formula_metrics(truth_infix, truth_infix)
    classified = classify_formula(truth_infix)
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
    cas_timeout_sec: float,
) -> list[dict[str, Any]]:
    rows = []
    for row in selected:
        truth = row.get("truth_infix") or ""
        pred = row.get("e2_infix_pre_classifier") or truth
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
