"""Reachability evidence builders for G_impl (preregistration v16 §3.8)."""

from __future__ import annotations

from typing import Any

from evaluation.gpu_run5_structure import classify_formula
from gpu_runmultiai.outcomes import build_outcome_row, evaluate_primary_decision
from gpu_runmultiai.oracle import oracle_equivalence, oracle_single_component
from gpu_runmultiai.q4_reference import audit_q4_decimal_round_reference


def _reachability_row(fixture_id: str, evidence_type: str, passed: bool, details: str) -> dict[str, Any]:
    return {
        "fixture_id": fixture_id,
        "evidence_type": evidence_type,
        "passed": passed,
        "details": details,
    }


def _reach_sfn_1() -> dict[str, Any]:
    truth = "2*x_0**2/(1+x_0**2)"
    e2_readout = "4*x_0**2/(2+2*x_0**2)"
    e1_oracle = oracle_equivalence(truth, truth, component_idx=0, timeout_sec=30.0)
    q4 = audit_q4_decimal_round_reference("div,mul,2,pow2,x_0,add,1,pow2,x_0")
    e2_oracle = oracle_single_component(
        q4.q4_emitted_infix or "",
        e2_readout,
        candidate_component_idx=0,
        timeout_sec=30.0,
    )
    classified = classify_formula(e2_readout)
    hill_form = bool(classified["component_flags"][0]["hill_form"]) if classified["valid"] else True
    passed = (
        e1_oracle.completed
        and e1_oracle.equivalent
        and q4.q4_construction_completed
        and e2_oracle.completed
        and e2_oracle.equivalent
        and not hill_form
    )
    return _reachability_row(
        "REACH-SFN-1",
        "hand_algebraic",
        passed,
        f"e1={e1_oracle.equivalent} q4={q4.q4_construction_completed} e2={e2_oracle.equivalent} hill={hill_form}",
    )


def _reach_preserved_1() -> dict[str, Any]:
    truth = "x_0**2/(1+x_0**2)"
    e1_oracle = oracle_equivalence(truth, truth, component_idx=0, timeout_sec=30.0)
    q4 = audit_q4_decimal_round_reference("div,pow2,x_0,add,1,pow2,x_0")
    e2_oracle = oracle_single_component(
        q4.q4_emitted_infix or "",
        truth,
        candidate_component_idx=0,
        timeout_sec=30.0,
    )
    classified = classify_formula(truth)
    hill_form = bool(classified["component_flags"][0]["hill_form"]) if classified["valid"] else False
    passed = (
        e1_oracle.completed
        and e1_oracle.equivalent
        and q4.q4_construction_completed
        and e2_oracle.completed
        and e2_oracle.equivalent
        and hill_form
    )
    return _reachability_row(
        "REACH-PRESERVED-1",
        "hand_algebraic",
        passed,
        f"e1={e1_oracle.equivalent} q4={q4.q4_construction_completed} e2={e2_oracle.equivalent} hill={hill_form}",
    )


def _reach_uns_1() -> dict[str, Any]:
    unsupported_rows = [
        {
            "condition": "B0",
            "eligibility_layer": "strict_hill_primary",
            "pair_id": f"pair_sha256:{index:064x}",
            "outcome_category": "preserved",
            "is_fully_diagnostic": True,
            "hill_form": True,
        }
        for index in range(1320)
    ]
    gates = {name: True for name in (
        "G_corpus", "G_eligibility", "G_stratum", "G0", "G4", "G1", "G_grand",
        "G_contract", "G_impl", "G_q4ref", "G_n1", "G_b1", "G_b4",
        "G_ctrl_cov", "G_ctrl_fp", "G_ctrl_lin", "G_term", "G_inc",
    )}
    decision = evaluate_primary_decision(unsupported_rows, validity_gate_failed=False)
    return _reachability_row(
        "REACH-UNS-1",
        "primary_decision_grid",
        decision == "H0001 unsupported" and len(unsupported_rows) == 1320,
        decision,
    )


def _reach_sup_1() -> dict[str, Any]:
    supported_rows = [
        {
            "condition": "B0",
            "eligibility_layer": "strict_hill_primary",
            "pair_id": f"pair_sha256:{index:064x}",
            "outcome_category": "preserved",
            "is_fully_diagnostic": True,
            "hill_form": True,
        }
        for index in range(1320)
    ]
    supported_rows[0] = {
        **supported_rows[0],
        "outcome_category": "structural_false_negative",
        "hill_form": False,
    }
    decision = evaluate_primary_decision(supported_rows, validity_gate_failed=False)
    return _reachability_row(
        "REACH-SUP-1",
        "primary_decision_grid",
        decision == "H0001 supported",
        decision,
    )


def _reach_drift_e2() -> dict[str, Any]:
    row = build_outcome_row(
        condition="B0",
        semantic_drift=True,
        e1_oracle_equivalent=True,
        e2_oracle_equivalent=False,
        e1_oracle_completed=True,
        e2_oracle_completed=True,
        classifier_parse_valid=True,
        formula_metrics_valid=True,
        hill_form=True,
    )
    return _reachability_row(
        "REACH-DRIFT-E2",
        "synthetic",
        row["outcome_category"] == "semantic_drift",
        row["outcome_category"],
    )


def _reach_q4fail_1() -> dict[str, Any]:
    row = build_outcome_row(
        condition="B0",
        q4_construction_completed=False,
        execution_failure=True,
        classifier_parse_valid=True,
    )
    return _reachability_row(
        "REACH-Q4FAIL-1",
        "synthetic",
        row["outcome_category"] == "execution_failure",
        row["outcome_category"],
    )


def _reach_ident_fallback_1() -> dict[str, Any]:
    row = build_outcome_row(
        condition="B0",
        e2_identity_fallback_candidate=True,
        execution_failure=True,
        e1_oracle_equivalent=True,
        e2_oracle_equivalent=True,
        classifier_parse_valid=True,
        formula_metrics_valid=True,
        hill_form=True,
    )
    return _reachability_row(
        "REACH-IDENT-FALLBACK-1",
        "synthetic",
        row["outcome_category"] == "execution_failure",
        row["outcome_category"],
    )


def _reach_parse_1() -> dict[str, Any]:
    row = build_outcome_row(
        condition="B0",
        classifier_parse_valid=False,
        classifier_parse_failure_reason="ParseError",
        e1_oracle_equivalent=True,
        e2_oracle_equivalent=True,
        hill_form=False,
    )
    return _reachability_row(
        "REACH-PARSE-1",
        "synthetic",
        row["outcome_category"] == "execution_failure",
        row["outcome_category"],
    )


def _reach_rescale_1() -> dict[str, Any]:
    row = build_outcome_row(
        condition="B0",
        rescale_incomplete=True,
        execution_failure=True,
    )
    return _reachability_row(
        "REACH-RESCALE-1",
        "synthetic",
        row["outcome_category"] == "execution_failure",
        row["outcome_category"],
    )


def build_reachability_evidence() -> list[dict[str, Any]]:
    pow_comp = audit_q4_decimal_round_reference("pow2,div,mul,10.0,x_0,10.0")
    rows = [
        _reachability_row(
            "REACH-POW-COMP-1",
            "prefix_q4_construction",
            pow_comp.q4_construction_completed,
            pow_comp.q4_emitted_prefix or pow_comp.q4_construction_failure_reason or "",
        ),
        _reach_sfn_1(),
        _reach_preserved_1(),
        _reach_uns_1(),
        _reach_sup_1(),
        _reach_drift_e2(),
        _reach_q4fail_1(),
        _reach_ident_fallback_1(),
        _reach_parse_1(),
        _reach_rescale_1(),
    ]
    return rows
