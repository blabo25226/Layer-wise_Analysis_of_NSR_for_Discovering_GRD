"""Rewrite and N1 negative-control templates."""

from __future__ import annotations

from gpu_run4.formulas import split_components

from gpu_runmultiai.ids import negative_id_for, rewrite_id_for
from gpu_runmultiai.oracle import oracle_equivalence, prefix_to_infix_component


def build_rewrite_prefix(truth_prefix: str, r: int) -> str:
    return f"div,mul,{r},{truth_prefix},{r}"


def build_rewrite_infix(truth_infix: str, r: int) -> str:
    return f"(({r}*({truth_infix}))/{r})"


def build_negative_prefix(truth_prefix: str, c: int) -> str:
    return f"add,{truth_prefix},{c}"


def build_negative_infix(truth_infix: str, c: int) -> str:
    return f"(({truth_infix})+({c}))"


def rewrite_registration(
    system_id: str,
    component_idx: int,
    truth_prefix: str,
    truth_infix: str,
    *,
    oracle_timeout_sec: float,
) -> dict:
    rewrite_id, selected_r, canonical_key = rewrite_id_for(system_id, component_idx)
    rewrite_prefix = build_rewrite_prefix(truth_prefix, selected_r)
    rewrite_infix = build_rewrite_infix(truth_infix, selected_r)
    lexical_non_identity = rewrite_prefix != truth_prefix and rewrite_infix != truth_infix
    oracle = oracle_equivalence(
        truth_infix,
        rewrite_infix,
        component_idx=0,
        timeout_sec=oracle_timeout_sec,
    )
    valid = lexical_non_identity and oracle.completed and oracle.equivalent
    return {
        "rewrite_id": rewrite_id,
        "canonical_key": canonical_key,
        "selected_r": selected_r,
        "rewrite_prefix": rewrite_prefix,
        "rewrite_infix": rewrite_infix,
        "lexical_non_identity": lexical_non_identity,
        "oracle": oracle.as_dict(),
        "valid": valid,
    }


def negative_control_row(
    system_id: str,
    component_idx: int,
    truth_prefix: str,
    truth_infix: str,
    *,
    oracle_timeout_sec: float,
) -> dict:
    negative_id, selected_c, canonical_key = negative_id_for(system_id, component_idx)
    negative_prefix = build_negative_prefix(truth_prefix, selected_c)
    negative_infix = build_negative_infix(truth_infix, selected_c)
    oracle = oracle_equivalence(
        truth_infix,
        negative_infix,
        component_idx=0,
        timeout_sec=oracle_timeout_sec,
    )
    return {
        "negative_id": negative_id,
        "canonical_key": canonical_key,
        "selected_c": selected_c,
        "negative_prefix": negative_prefix,
        "negative_infix": negative_infix,
        "oracle": oracle.as_dict(),
        "valid": bool(oracle.completed and not oracle.equivalent),
    }


def truth_component_infix(record: dict, component_idx: int) -> tuple[str, str]:
    prefixes = split_components(record["teacher_prefix"])
    prefix = prefixes[component_idx]
    return prefix, prefix_to_infix_component(prefix)
