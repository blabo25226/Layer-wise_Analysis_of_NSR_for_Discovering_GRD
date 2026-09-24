"""Reachability evidence builders for G_impl (preregistration v16 §3.8).

Every row is derived from an executed check: expression oracles, the real classifier,
the production rescale early-return path, or a full pass through
``evaluate_validity_gates`` + ``evaluate_primary_decision``.  No row asserts its own
desired outcome.

These calls are preflight fixtures and are excluded from the counted-call ledger (§8.1).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from evaluation.gpu_run5_structure import classify_formula

from gpu_runmultiai.constants import (
    CONFIRMATORY_CALL_CEILING,
    FULL_RUN_CALL_CEILING,
    PRIMARY_SCALES,
    Q4_TIMEOUT_SEC,
    SIMPLIFIER_SUBPROCESS_TIMEOUT_SEC,
)
from gpu_runmultiai.contract_evidence import F_ACCEPTANCE_IDS, G_CONTRACT_CHECK_KEYS
from gpu_runmultiai.controls import evaluate_validity_gates
from gpu_runmultiai.invariants import GateAbortError
from gpu_runmultiai.odeformer_runtime import MULTI_COMPONENT_SEPARATOR, component_prefix_list_from_raw
from gpu_runmultiai.outcomes import build_outcome_row, evaluate_primary_decision
from gpu_runmultiai.oracle import oracle_equivalence, oracle_single_component
from gpu_runmultiai.pipeline import detect_e2_identity_fallback_candidate
from gpu_runmultiai.q4_reference import audit_q4_decimal_round_reference

PRIMARY_PAIR_COUNT = 1320

REACHABILITY_FIXTURE_IDS: tuple[str, ...] = (
    "REACH-POW-COMP-1",
    "REACH-SFN-1",
    "REACH-PRESERVED-1",
    "REACH-UNS-1",
    "REACH-SUP-1",
    "REACH-DRIFT-E2",
    "REACH-Q4FAIL-1",
    "REACH-IDENT-FALLBACK-1",
    "REACH-PARSE-1",
    "REACH-RESCALE-1",
)


def reachability_evidence_passes(rows: list[dict[str, Any]]) -> bool:
    """True when §3.8 rows match the frozen ten-fixture set and all passed."""
    if len(rows) != len(REACHABILITY_FIXTURE_IDS):
        return False
    by_id = {row.get("fixture_id") for row in rows}
    if by_id != set(REACHABILITY_FIXTURE_IDS):
        return False
    return all(bool(row.get("passed")) for row in rows)


def _reachability_row(fixture_id: str, evidence_type: str, passed: bool, details: str) -> dict[str, Any]:
    return {
        "fixture_id": fixture_id,
        "evidence_type": evidence_type,
        "passed": bool(passed),
        "details": details,
    }


def _hill_form_from_classifier(infix: str) -> tuple[bool, bool]:
    """Return (classifier_valid, hill_form) from the real production classifier."""
    classified = classify_formula(infix)
    if not classified["valid"] or not classified["component_flags"]:
        return False, False
    return True, bool(classified["component_flags"][0]["hill_form"])


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
    classifier_valid, hill_form = _hill_form_from_classifier(e2_readout)
    row = build_outcome_row(
        condition="B0",
        eligibility_layer="strict_hill_primary",
        pair_id="pair_sha256:reach_sfn_1",
        q4_construction_completed=q4.q4_construction_completed,
        e1_oracle_completed=e1_oracle.completed,
        e1_oracle_equivalent=e1_oracle.equivalent,
        e2_oracle_completed=e2_oracle.completed,
        e2_oracle_equivalent=e2_oracle.equivalent,
        classifier_parse_valid=classifier_valid,
        formula_metrics_valid=classifier_valid,
        hill_form=hill_form,
    )
    passed = row["outcome_category"] == "structural_false_negative"
    return _reachability_row(
        "REACH-SFN-1",
        "hand_algebraic",
        passed,
        f"outcome={row['outcome_category']} e1={e1_oracle.equivalent} "
        f"q4={q4.q4_construction_completed} e2={e2_oracle.equivalent} hill={hill_form}",
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
    classifier_valid, hill_form = _hill_form_from_classifier(truth)
    row = build_outcome_row(
        condition="B0",
        eligibility_layer="strict_hill_primary",
        pair_id="pair_sha256:reach_preserved_1",
        q4_construction_completed=q4.q4_construction_completed,
        e1_oracle_completed=e1_oracle.completed,
        e1_oracle_equivalent=e1_oracle.equivalent,
        e2_oracle_completed=e2_oracle.completed,
        e2_oracle_equivalent=e2_oracle.equivalent,
        classifier_parse_valid=classifier_valid,
        formula_metrics_valid=classifier_valid,
        hill_form=hill_form,
    )
    passed = row["outcome_category"] == "preserved"
    return _reachability_row(
        "REACH-PRESERVED-1",
        "hand_algebraic",
        passed,
        f"outcome={row['outcome_category']} e1={e1_oracle.equivalent} "
        f"q4={q4.q4_construction_completed} e2={e2_oracle.equivalent} hill={hill_form}",
    )


def _synthetic_primary_rows(*, sfn_count: int) -> list[dict[str, Any]]:
    """Synthetic decision grid: exactly 1,320 unique fully diagnostic strict-Hill pairs."""
    rows: list[dict[str, Any]] = []
    for index in range(PRIMARY_PAIR_COUNT):
        hill_form = index >= sfn_count
        rows.append(
            build_outcome_row(
                condition="B0",
                eligibility_layer="strict_hill_primary",
                partition_scope="primary",
                pair_id=f"pair_sha256:{index:064x}",
                q4_construction_completed=True,
                e1_oracle_completed=True,
                e1_oracle_equivalent=True,
                e2_oracle_completed=True,
                e2_oracle_equivalent=True,
                classifier_parse_valid=True,
                formula_metrics_valid=True,
                rescale_incomplete=False,
                e2_identity_fallback_candidate=False,
                hill_form=hill_form,
                quantization_stratum="quantization_neutral"
                if index >= 184
                else "quantization_active",
            )
        )
    return rows


def _synthetic_gate_state(primary_rows: list[dict[str, Any]]) -> dict[str, Any]:
    from gpu_runmultiai.calls import expected_confirmatory_calls

    quantization_rows = [
        {
            "component_id": f"component_sha256:{index:064x}",
            "eligibility_layer": "strict_hill_primary",
            "quantization_stratum": "quantization_active" if index < 46 else "quantization_neutral",
        }
        for index in range(330)
    ]
    b1_rows = [
        build_outcome_row(
            condition="B1",
            eligibility_layer="strict_hill_primary",
            pair_id=f"pair_sha256:b1{index:062x}",
            q4_construction_completed=True,
            e1_oracle_completed=True,
            e1_oracle_equivalent=True,
            e2_oracle_completed=True,
            e2_oracle_equivalent=True,
            classifier_parse_valid=True,
            formula_metrics_valid=True,
        )
        for index in range(510)
    ]
    return {
        "g_corpus_pass": True,
        "eligibility_counts": {
            "strict_hill": 330,
            "non_strict_hill": 60,
            "linear": 120,
            "other": 0,
        },
        "quantization_rows": quantization_rows,
        "scaler_asserts": {
            "time_scale": 9,
            "time_shift": 1,
            "a_t": 0.9,
            "b_t": 1.0,
            "rescale_features": True,
        },
        "access_attempts": 0,
        "total_calls": CONFIRMATORY_CALL_CEILING,
        "call_ceiling": expected_confirmatory_calls(),
        "grand_calls": FULL_RUN_CALL_CEILING,
        "grand_call_ceiling": FULL_RUN_CALL_CEILING,
        "descriptive_calls": FULL_RUN_CALL_CEILING - CONFIRMATORY_CALL_CEILING,
        "negative_controls": [
            {"oracle_completed": True, "oracle_equivalent": False} for _ in range(100)
        ],
        "b1_rows": b1_rows,
        "c_q4_rows": [
            {"fixture_id": f"q4_fixture_{index + 1:02d}", "fixture_pass": True}
            for index in range(7)
        ],
        "b4_rows": [{"valid": True, "canonical_exact": 1} for _ in range(510)],
        "linear_rows": [
            {
                "classifier_parse_valid": True,
                "formula_metrics_valid": True,
                "hill_form": False,
                "canonical_exact": 1,
            }
            for _ in range(480)
        ],
        "strict_rows": primary_rows,
        "g_contract_evidence": {key: True for key in G_CONTRACT_CHECK_KEYS},
        "f_acceptance": {key: True for key in F_ACCEPTANCE_IDS},
        "reachability_evidence": [
            {"fixture_id": fixture_id, "passed": True} for fixture_id in REACHABILITY_FIXTURE_IDS
        ],
    }


def _decision_grid_row(fixture_id: str, *, sfn_count: int, expected_decision: str) -> dict[str, Any]:
    primary_rows = _synthetic_primary_rows(sfn_count=sfn_count)
    gates = evaluate_validity_gates(_synthetic_gate_state(primary_rows))
    failed = sorted(name for name, value in gates.items() if not value)
    decision = evaluate_primary_decision(primary_rows, validity_gate_failed=bool(failed))
    pair_ids = {row["pair_id"] for row in primary_rows}
    diagnostic = sum(1 for row in primary_rows if row["is_fully_diagnostic"])
    observed_sfn = sum(
        1 for row in primary_rows if row["outcome_category"] == "structural_false_negative"
    )
    passed = (
        not failed
        and decision == expected_decision
        and len(primary_rows) == PRIMARY_PAIR_COUNT
        and len(pair_ids) == PRIMARY_PAIR_COUNT
        and diagnostic == PRIMARY_PAIR_COUNT
        and observed_sfn == sfn_count
    )
    return _reachability_row(
        fixture_id,
        "primary_decision_grid",
        passed,
        f"decision={decision} rows={len(primary_rows)} unique={len(pair_ids)} "
        f"fully_diagnostic={diagnostic} sfn={observed_sfn} failed_gates={failed}",
    )


def _reach_uns_1() -> dict[str, Any]:
    return _decision_grid_row("REACH-UNS-1", sfn_count=0, expected_decision="H0001 unsupported")


def _reach_sup_1() -> dict[str, Any]:
    return _decision_grid_row("REACH-SUP-1", sfn_count=1, expected_decision="H0001 supported")


def _reach_drift_e2() -> dict[str, Any]:
    """E2 not equivalent to Q4(E1) while E1 matches truth: derived from real oracle calls."""
    truth = "x_0**2/(1+x_0**2)"
    drifted_e2 = "x_0**2/(2+x_0**2)"
    e1_oracle = oracle_equivalence(truth, truth, component_idx=0, timeout_sec=30.0)
    q4 = audit_q4_decimal_round_reference("div,pow2,x_0,add,1,pow2,x_0")
    e2_oracle = oracle_single_component(
        q4.q4_emitted_infix or "",
        drifted_e2,
        candidate_component_idx=0,
        timeout_sec=30.0,
    )
    classifier_valid, hill_form = _hill_form_from_classifier(drifted_e2)
    row = build_outcome_row(
        condition="B0",
        eligibility_layer="strict_hill_primary",
        pair_id="pair_sha256:reach_drift_e2",
        q4_construction_completed=q4.q4_construction_completed,
        e1_oracle_completed=e1_oracle.completed,
        e1_oracle_equivalent=e1_oracle.equivalent,
        e2_oracle_completed=e2_oracle.completed,
        e2_oracle_equivalent=e2_oracle.equivalent,
        classifier_parse_valid=classifier_valid,
        formula_metrics_valid=classifier_valid,
        hill_form=hill_form,
    )
    return _reachability_row(
        "REACH-DRIFT-E2",
        "synthetic",
        row["outcome_category"] == "semantic_drift",
        f"outcome={row['outcome_category']} e2_completed={e2_oracle.completed} "
        f"e2_equivalent={e2_oracle.equivalent}",
    )


def _reach_q4fail_1() -> dict[str, Any]:
    """Q4 construction failure produced by an arity-deficient E1 prefix."""
    q4 = audit_q4_decimal_round_reference("mul,x_0", timeout_sec=Q4_TIMEOUT_SEC)
    row = build_outcome_row(
        condition="B0",
        eligibility_layer="strict_hill_primary",
        pair_id="pair_sha256:reach_q4fail_1",
        q4_construction_completed=q4.q4_construction_completed,
        q4_construction_failure_reason=q4.q4_construction_failure_reason,
        classifier_parse_valid=True,
        formula_metrics_valid=True,
    )
    return _reachability_row(
        "REACH-Q4FAIL-1",
        "synthetic",
        row["outcome_category"] == "execution_failure" and not q4.q4_construction_completed,
        f"outcome={row['outcome_category']} q4_completed={q4.q4_construction_completed} "
        f"reason={q4.q4_construction_failure_reason}",
    )


# Frozen §3.8 synthetic inputs: q4_fixture_01 five-decimal leaf + neutral second component (d>=2).
_IDENT_FALLBACK_SYNTHETIC_COMPONENT_0 = "mul,0.04598,x_0"
_IDENT_FALLBACK_SYNTHETIC_COMPONENT_1 = "x_1"
_IDENT_FALLBACK_SYNTHETIC_DIMENSION = 2

# Live production observation: bounded auxiliary run_b0_pair probes (excluded from §8.1 ledger).
LIVE_IDENT_FALLBACK_RUN_B0_PAIR_BUDGET = 8


def _reconcile_orphan_child_process_guard_side_channel(guard: Any) -> None:
    """Merge worker-side-channel rows left behind when simplify subprocess aborts early.

    Malformed durable lines fail closed: they cannot be downgraded to ``error_isolated=true``.
    """
    from gpu_runmultiai.guard_side_channel import child_side_channel_path, load_guard_attempts
    from gpu_runmultiai.invariants import AuditInvariantError

    path = child_side_channel_path()
    if not path.is_file():
        return
    try:
        if path.stat().st_size == 0:
            return
    except OSError:
        return
    try:
        attempts = load_guard_attempts(path)
    except AuditInvariantError as exc:
        raise GateAbortError(
            "auxiliary live probe cannot certify: malformed child guard side channel "
            f"at {path}"
        ) from exc
    if attempts:
        guard.extend_child_attempts(attempts)


def _finalize_auxiliary_live_probe_guard(
    guard: Any,
    auxiliary_guard_sink: list[dict[str, str]] | None,
) -> tuple[int, int, int]:
    """Account child subprocess guard rows on an auxiliary channel; fail-closed if unrecorded."""
    from gpu_runmultiai.invariants import GateAbortError

    direct = guard.direct_attempt_count()
    child_count = len(guard.child_attempts)
    total = guard.attempt_count()
    if child_count == 0:
        return direct, child_count, total
    if auxiliary_guard_sink is None:
        raise GateAbortError(
            "auxiliary live ident-fallback probe recorded sealed-path child attempts "
            f"without auxiliary side-channel sink: child_attempts={child_count}"
        )
    seen = {
        (
            row["attempted_operation"],
            row["attempted_path_norm"],
            row["attempted_path_real"],
        )
        for row in auxiliary_guard_sink
    }
    for attempt in guard.child_attempts:
        row = {
            "attempted_operation": f"auxiliary_live_probe:{attempt.attempted_operation}",
            "attempted_path_norm": attempt.attempted_path_norm,
            "attempted_path_real": attempt.attempted_path_real,
        }
        key = (row["attempted_operation"], row["attempted_path_norm"], row["attempted_path_real"])
        if key in seen:
            continue
        seen.add(key)
        auxiliary_guard_sink.append(row)
    return direct, child_count, total


def _auxiliary_guard_attempt_fields(
    guard: Any,
    auxiliary_guard_sink: list[dict[str, str]] | None,
    finalized: list[bool],
) -> tuple[int, int, int, bool]:
    finalized.append(True)
    direct, child_count, total = _finalize_auxiliary_live_probe_guard(guard, auxiliary_guard_sink)
    return direct, child_count, total, child_count > 0 and auxiliary_guard_sink is not None


def _live_ident_fallback_b0_pair_trials(corpus: dict[str, Any]) -> list[tuple[dict[str, Any], int, str]]:
    """Deterministic first-N (record, component_idx, scale) trials in sorted corpus order."""
    candidates = sorted(
        (record for record in corpus["train_records"] if int(record["dimension"]) >= 2),
        key=lambda row: row["system_id"],
    )
    trials: list[tuple[dict[str, Any], int, str]] = []
    for record in candidates:
        dimension = int(record["dimension"])
        for component_idx in range(dimension):
            for scale in PRIMARY_SCALES:
                trials.append((record, component_idx, scale))
                if len(trials) >= LIVE_IDENT_FALLBACK_RUN_B0_PAIR_BUDGET:
                    return trials
    return trials


def _reach_ident_fallback_1_synthetic() -> tuple[bool, str]:
    """§3.8 synthetic decision-rule fixture; E2 is explicit injection equal to E1 raw."""
    from gpu_runmultiai.odeformer_runtime import canonical_system_prefix_raw
    from gpu_runmultiai.oracle import oracle_equivalence_prefix
    from gpu_runmultiai.q4_reference import e1_not_equivalent_to_q4

    oracle_timeout_sec = 30.0
    e1_component_prefix = _IDENT_FALLBACK_SYNTHETIC_COMPONENT_0
    e1_prefix_raw = canonical_system_prefix_raw(
        _IDENT_FALLBACK_SYNTHETIC_COMPONENT_0
        + MULTI_COMPONENT_SEPARATOR
        + _IDENT_FALLBACK_SYNTHETIC_COMPONENT_1
    )
    e2_prefix_raw = e1_prefix_raw
    dimension = _IDENT_FALLBACK_SYNTHETIC_DIMENSION
    q4 = audit_q4_decimal_round_reference(
        e1_component_prefix,
        dimension=dimension,
        timeout_sec=Q4_TIMEOUT_SEC,
    )
    if not q4.q4_construction_completed or not q4.q4_sympy_expr_canonical:
        return False, (
            "synthetic_fixture_failed "
            f"q4_completed={q4.q4_construction_completed} "
            f"reason={q4.q4_construction_failure_reason}"
        )
    q4_prefix_parts = component_prefix_list_from_raw(q4.q4_emitted_prefix or "")
    e2_component_prefix = component_prefix_list_from_raw(e1_prefix_raw)[0]
    if not q4_prefix_parts:
        return False, "synthetic_fixture_failed q4_emitted_prefix_empty"
    q4_component_prefix = q4_prefix_parts[0]
    e1_neq_q4 = e1_not_equivalent_to_q4(
        e1_component_prefix,
        q4.q4_sympy_expr_canonical,
        dimension=dimension,
        timeout_sec=Q4_TIMEOUT_SEC,
    )
    # Corpus truth matches the five-decimal E1 leaf (q4_fixture_01); oracle is production-independent.
    e1_oracle = oracle_equivalence_prefix(
        e1_component_prefix,
        e1_component_prefix,
        timeout_sec=oracle_timeout_sec,
    )
    e2_oracle = oracle_single_component(
        q4.q4_emitted_infix or "",
        "",
        candidate_component_idx=0,
        timeout_sec=oracle_timeout_sec,
        truth_component_prefix=q4_component_prefix,
        candidate_component_prefix=e2_component_prefix,
    )
    fallback = detect_e2_identity_fallback_candidate(
        e1_prefix_raw=e1_prefix_raw,
        e2_prefix_raw=e2_prefix_raw,
        e1_component_prefix=e1_component_prefix,
        q4_sympy_expr_canonical=q4.q4_sympy_expr_canonical,
        dimension=dimension,
        q4_timeout_sec=Q4_TIMEOUT_SEC,
    )
    outcome_row = build_outcome_row(
        condition="B0",
        eligibility_layer="strict_hill_primary",
        pair_id="pair_sha256:reach_ident_fallback_1",
        q4_construction_completed=True,
        q4_sympy_expr_canonical=q4.q4_sympy_expr_canonical,
        e1_prefix_raw=e1_prefix_raw,
        e2_prefix_raw=e2_prefix_raw,
        e2_identity_fallback_candidate=fallback,
        e1_oracle_completed=e1_oracle.completed,
        e1_oracle_equivalent=e1_oracle.equivalent,
        e2_oracle_completed=e2_oracle.completed,
        e2_oracle_equivalent=e2_oracle.equivalent,
        classifier_parse_valid=True,
        formula_metrics_valid=True,
        hill_form=True,
    )
    no_fallback_row = build_outcome_row(
        condition="B0",
        eligibility_layer="strict_hill_primary",
        pair_id="pair_sha256:reach_ident_fallback_1_no_fallback",
        q4_construction_completed=True,
        q4_sympy_expr_canonical=q4.q4_sympy_expr_canonical,
        e1_prefix_raw=e1_prefix_raw,
        e2_prefix_raw=e2_prefix_raw,
        e2_identity_fallback_candidate=False,
        e1_oracle_completed=e1_oracle.completed,
        e1_oracle_equivalent=e1_oracle.equivalent,
        e2_oracle_completed=e2_oracle.completed,
        e2_oracle_equivalent=e2_oracle.equivalent,
        classifier_parse_valid=True,
        formula_metrics_valid=True,
        hill_form=True,
    )
    passed = bool(
        e1_neq_q4
        and e2_prefix_raw == e1_prefix_raw
        and e1_oracle.completed
        and e1_oracle.equivalent
        and e2_oracle.completed
        and not e2_oracle.equivalent
        and fallback
        and outcome_row["outcome_category"] == "execution_failure"
        and no_fallback_row["outcome_category"] == "semantic_drift"
    )
    detail = (
        "synthetic_fixture "
        f"e1_component0={e1_component_prefix} "
        f"e1_prefix_raw={e1_prefix_raw} "
        f"e2_prefix_raw={e2_prefix_raw} "
        f"e2_source=synthetic_injection_not_production "
        f"e1_neq_q4={e1_neq_q4} "
        f"q4_canonical={q4.q4_sympy_expr_canonical} "
        f"e1_oracle_equivalent={e1_oracle.equivalent} "
        f"e2_oracle_equivalent={e2_oracle.equivalent} "
        f"no_fallback_outcome={no_fallback_row['outcome_category']} "
        f"fallback_candidate={fallback} "
        f"outcome={outcome_row['outcome_category']}"
    )
    return passed, detail


def _reach_ident_fallback_1_live_production_observation(
    *,
    auxiliary_guard_sink: list[dict[str, str]] | None = None,
) -> str:
    """Record run_b0_pair identity-fallback reachability without substituting production E2.

    Auxiliary pre-closure observation only: uses a dedicated CallLogger excluded from the
    confirmatory audit ledger and must not share the full-run ResourceMonitor.
    """
    from gpu_runmultiai.odeformer_runtime import ODEFormerUnavailable, require_odeformer

    try:
        require_odeformer()
    except ODEFormerUnavailable as exc:
        return f"live_production_observation odeformer_unavailable:{exc}"

    try:
        return _reach_ident_fallback_1_live_production_observation_body(
            auxiliary_guard_sink=auxiliary_guard_sink
        )
    except GateAbortError:
        # Unrecorded auxiliary child guard attempts are an evidence-integrity failure and
        # must fail closed rather than be papered over as a benign observation string.
        raise
    except Exception as exc:  # must not abort acceptance after counted work completes
        return (
            "live_production_observation error_isolated=true "
            f"error={type(exc).__name__}:{exc}"
        )


def _reach_ident_fallback_1_live_production_observation_body(
    *,
    auxiliary_guard_sink: list[dict[str, str]] | None = None,
) -> str:
    """Run the bounded live scan; child guard attempts are always flushed to the sink.

    Normal return paths finalize inside the scan. If the scan raises after any child call
    (run_b0_pair internals or the match-path simplifier), ``finally`` still flushes collected
    child attempts, and a missing sink raises GateAbortError instead of losing them.
    """
    from gpu_runmultiai.guard_side_channel import child_side_channel_path
    from gpu_runmultiai.sealed_guard import SealedPathGuard

    stale_child_channel = child_side_channel_path()
    if stale_child_channel.is_file():
        stale_child_channel.unlink()

    guard = SealedPathGuard(output_root_abs=Path("/nonexistent/results/runs"))
    finalized: list[bool] = []
    try:
        return _reach_ident_fallback_1_live_probe_scan(
            guard=guard,
            auxiliary_guard_sink=auxiliary_guard_sink,
            finalized=finalized,
        )
    finally:
        child_attempts_before_reconcile = len(guard.child_attempts)
        _reconcile_orphan_child_process_guard_side_channel(guard)
        if finalized and len(guard.child_attempts) > child_attempts_before_reconcile:
            raise GateAbortError(
                "auxiliary live probe cannot certify: orphan child guard rows appeared after finalize"
            )
        if not finalized:
            _finalize_auxiliary_live_probe_guard(guard, auxiliary_guard_sink)


def _reach_ident_fallback_1_live_probe_scan(
    *,
    guard: Any,
    auxiliary_guard_sink: list[dict[str, str]] | None,
    finalized: list[bool],
) -> str:
    from gpu_runmultiai.calls import CallLogger
    from gpu_runmultiai.corpus import load_frozen_corpus
    from gpu_runmultiai.odeformer_runtime import (
        canonical_system_prefix_raw,
        simplify_tree_subprocess,
    )
    from gpu_runmultiai.pipeline import run_b0_pair
    from gpu_runmultiai.q4_reference import audit_q4_decimal_round_reference, e1_not_equivalent_to_q4
    from gpu_runmultiai.rewrites import rewrite_registration, truth_component_infix

    corpus = load_frozen_corpus()
    trials = _live_ident_fallback_b0_pair_trials(corpus)
    budget = LIVE_IDENT_FALLBACK_RUN_B0_PAIR_BUDGET
    auxiliary_logger = CallLogger()
    run_b0_pair_calls = 0
    for record, component_idx, scale in trials:
        dimension = int(record["dimension"])
        truth_prefix, truth_infix = truth_component_infix(record, component_idx)
        rewrite = rewrite_registration(
            record["system_id"],
            component_idx,
            truth_prefix,
            truth_infix,
            oracle_timeout_sec=30.0,
        )
        row = run_b0_pair(
            corpus_hash=corpus["corpus_hash"],
            record=record,
            component_idx=component_idx,
            scale=scale,
            rewrite_row=rewrite,
            oracle_timeout_sec=30.0,
            q4_timeout_sec=Q4_TIMEOUT_SEC,
            simplifier_timeout_sec=SIMPLIFIER_SUBPROCESS_TIMEOUT_SEC,
            call_logger=auxiliary_logger,
            runtime_available=True,
            guard=guard,
        )
        run_b0_pair_calls += 1
        e1_prefix_raw = row.get("e1_prefix_raw") or ""
        production_e2_prefix_raw = row.get("e2_prefix_raw") or ""
        if MULTI_COMPONENT_SEPARATOR not in e1_prefix_raw:
            continue
        if production_e2_prefix_raw != e1_prefix_raw:
            continue
        e1_component_prefix = component_prefix_list_from_raw(e1_prefix_raw)[component_idx]
        q4 = audit_q4_decimal_round_reference(
            e1_component_prefix,
            dimension=dimension,
            timeout_sec=Q4_TIMEOUT_SEC,
        )
        if not q4.q4_construction_completed or not q4.q4_sympy_expr_canonical:
            continue
        if not e1_not_equivalent_to_q4(
            e1_component_prefix,
            q4.q4_sympy_expr_canonical,
            dimension=dimension,
            timeout_sec=Q4_TIMEOUT_SEC,
        ):
            continue
        simplified = simplify_tree_subprocess(
            component_prefix_list_from_raw(e1_prefix_raw),
            timeout_sec=SIMPLIFIER_SUBPROCESS_TIMEOUT_SEC,
        )
        if simplified.get("child_guard_accounting_uncertain"):
            raise GateAbortError(
                "auxiliary live probe cannot certify: simplifier child guard accounting incomplete"
            )
        if simplified.get("guard_attempts"):
            guard.extend_child_attempts(simplified["guard_attempts"])
        simplifier_output_raw = ""
        if simplified.get("ok"):
            simplifier_output_raw = canonical_system_prefix_raw(simplified.get("prefix") or "")
        production_fallback_flag = bool(row.get("e2_identity_fallback_candidate"))
        fallback = detect_e2_identity_fallback_candidate(
            e1_prefix_raw=e1_prefix_raw,
            e2_prefix_raw=production_e2_prefix_raw,
            e1_component_prefix=e1_component_prefix,
            q4_sympy_expr_canonical=q4.q4_sympy_expr_canonical,
            dimension=dimension,
            q4_timeout_sec=Q4_TIMEOUT_SEC,
        )
        outcome_row = build_outcome_row(
            condition="B0",
            eligibility_layer="strict_hill_primary",
            pair_id="pair_sha256:reach_ident_fallback_1_live",
            q4_construction_completed=row.get("q4_construction_completed"),
            e1_prefix_raw=e1_prefix_raw,
            e2_prefix_raw=production_e2_prefix_raw,
            e2_identity_fallback_candidate=fallback,
            e1_oracle_completed=row.get("e1_oracle_completed"),
            e1_oracle_equivalent=row.get("e1_oracle_equivalent"),
            e2_oracle_completed=row.get("e2_oracle_completed"),
            e2_oracle_equivalent=row.get("e2_oracle_equivalent"),
            classifier_parse_valid=row.get("classifier_parse_valid"),
            formula_metrics_valid=row.get("formula_metrics_valid"),
            hill_form=row.get("hill_form"),
        )
        if fallback and outcome_row["outcome_category"] == "execution_failure":
            direct, child_count, total, child_persisted = _auxiliary_guard_attempt_fields(
                guard, auxiliary_guard_sink, finalized
            )
            return (
                "live_production_observation bounded_match=true "
                f"observation_scope=first_{budget}_sorted_trials "
                f"run_b0_pair_budget={budget} run_b0_pair_calls={run_b0_pair_calls} "
                f"auxiliary_call_logger_grand_calls={auxiliary_logger.total()} "
                f"auxiliary_guard_direct_attempts={direct} "
                f"auxiliary_guard_child_attempts={child_count} "
                f"auxiliary_guard_total_attempts={total} "
                f"auxiliary_guard_child_persisted={child_persisted} "
                f"system_id={record['system_id']} component_idx={component_idx} "
                f"scale={scale} dimension={dimension} "
                f"production_e1_raw==e2_raw=True production_e2_unchanged=True "
                f"simplifier_subprocess_rerun_not_production_e2="
                f"{simplifier_output_raw == e1_prefix_raw} "
                f"production_fallback_flag={production_fallback_flag} "
                f"fallback_recomputed={fallback} "
                f"fallback_flags_match={production_fallback_flag == fallback} "
                f"fallback_candidate={fallback} outcome={outcome_row['outcome_category']} "
                f"q4_canonical={q4.q4_sympy_expr_canonical}"
            )
    bounded_scan_exhausted = run_b0_pair_calls >= len(trials)
    direct, child_count, total, child_persisted = _auxiliary_guard_attempt_fields(
        guard, auxiliary_guard_sink, finalized
    )
    return (
        "live_production_observation bounded_no_match_within_budget=true "
        f"observation_scope=first_{budget}_sorted_trials "
        f"run_b0_pair_budget={budget} run_b0_pair_calls={run_b0_pair_calls} "
        f"bounded_scan_exhausted={bounded_scan_exhausted} "
        f"auxiliary_call_logger_grand_calls={auxiliary_logger.total()} "
        f"auxiliary_guard_direct_attempts={direct} "
        f"auxiliary_guard_child_attempts={child_count} "
        f"auxiliary_guard_total_attempts={total} "
        f"auxiliary_guard_child_persisted={child_persisted} "
        "not_global_corpus_absence production_e2_unchanged=True"
    )


def _reach_ident_fallback_1(
    *,
    include_live_observation: bool = False,
    auxiliary_guard_sink: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    """§3.8 synthetic fixture; optional auxiliary live observation (pre-closure only)."""
    synthetic_passed, synthetic_detail = _reach_ident_fallback_1_synthetic()
    detail = synthetic_detail
    if include_live_observation:
        try:
            live_detail = _reach_ident_fallback_1_live_production_observation(
                auxiliary_guard_sink=auxiliary_guard_sink
            )
        except GateAbortError:
            raise
        except Exception as exc:
            live_detail = (
                "live_production_observation error_isolated=true "
                f"error={type(exc).__name__}:{exc}"
            )
        detail = f"{synthetic_detail}; {live_detail}"
    return _reachability_row(
        "REACH-IDENT-FALLBACK-1",
        "synthetic",
        synthetic_passed,
        detail,
    )


def _reach_parse_1() -> dict[str, Any]:
    """classifier_parse_valid=false taken from the real classifier on an unparseable readout."""
    classifier_valid, hill_form = _hill_form_from_classifier("((")
    row = build_outcome_row(
        condition="B0",
        eligibility_layer="strict_hill_primary",
        pair_id="pair_sha256:reach_parse_1",
        q4_construction_completed=True,
        e1_oracle_completed=True,
        e1_oracle_equivalent=True,
        e2_oracle_completed=True,
        e2_oracle_equivalent=True,
        classifier_parse_valid=classifier_valid,
        hill_form=hill_form,
    )
    return _reachability_row(
        "REACH-PARSE-1",
        "synthetic",
        row["outcome_category"] == "execution_failure" and not classifier_valid,
        f"outcome={row['outcome_category']} classifier_parse_valid={classifier_valid}",
    )


def _reach_rescale_1() -> dict[str, Any]:
    """rescale_incomplete from the production early return `rescaled_tree is input_tree` (§5.2)."""
    from gpu_runmultiai.odeformer_runtime import (
        build_identity_scaler,
        decode_system_tree,
        get_env,
        rescale_system,
    )

    evidence = "live_production_rescale"
    try:
        env = get_env()
        scaler, _ = build_identity_scaler(1)
        # Two components against len(scale)=1 is §5.2 condition 1.
        tree = decode_system_tree(env, ["x_0", "x_0"])
        _, rescale_incomplete, proof = rescale_system(env, scaler, tree)
        detail = (
            f"proof={proof['rescale_callable_module']}.{proof['rescale_callable_qualname']} "
            f"input_nodes={proof['input_node_count']} scale_len={len(proof['scale'])}"
        )
    except Exception as exc:  # evidence records its own failure instead of aborting
        return _reachability_row(
            "REACH-RESCALE-1",
            "synthetic",
            False,
            f"production rescale early return not reached: {type(exc).__name__}: {exc}",
        )
    row = build_outcome_row(
        condition="B0",
        eligibility_layer="strict_hill_primary",
        pair_id="pair_sha256:reach_rescale_1",
        rescale_incomplete=rescale_incomplete,
        q4_construction_completed=True,
        classifier_parse_valid=True,
        formula_metrics_valid=True,
    )
    return _reachability_row(
        "REACH-RESCALE-1",
        evidence,
        row["outcome_category"] == "execution_failure" and rescale_incomplete,
        f"outcome={row['outcome_category']} rescale_incomplete={rescale_incomplete} {detail}",
    )


def _reach_pow_comp_1() -> dict[str, Any]:
    pow_comp = audit_q4_decimal_round_reference("pow2,div,mul,10.0,x_0,10.0", timeout_sec=Q4_TIMEOUT_SEC)
    return _reachability_row(
        "REACH-POW-COMP-1",
        "prefix_q4_construction",
        pow_comp.q4_construction_completed,
        pow_comp.q4_emitted_prefix or pow_comp.q4_construction_failure_reason or "",
    )


def _reachability_fixture_failed_row(fixture_id: str, exc: BaseException) -> dict[str, Any]:
    return _reachability_row(
        fixture_id,
        "synthetic",
        False,
        f"fixture_execution_error error_isolated=true error={type(exc).__name__}:{exc}",
    )


def _run_reachability_fixture(
    fixture_id: str,
    builder: Any,
    *,
    include_live_ident_fallback_observation: bool = False,
    auxiliary_guard_sink: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    try:
        if fixture_id == "REACH-IDENT-FALLBACK-1":
            row = builder(
                include_live_observation=include_live_ident_fallback_observation,
                auxiliary_guard_sink=auxiliary_guard_sink,
            )
        else:
            row = builder()
    except GateAbortError:
        # Evidence-integrity fail-closed signal (e.g. unrecorded auxiliary child guard
        # attempts): must propagate to the acceptance entrypoint, not become a fixture row.
        raise
    except Exception as exc:  # must not abort confirmatory work after counted primitives
        return _reachability_fixture_failed_row(fixture_id, exc)
    if row.get("fixture_id") != fixture_id:
        return _reachability_row(
            fixture_id,
            str(row.get("evidence_type") or "synthetic"),
            False,
            f"fixture_id_mismatch expected={fixture_id} got={row.get('fixture_id')}",
        )
    return row


def build_reachability_evidence(
    resource_monitor: Any | None = None,
    *,
    include_live_ident_fallback_observation: bool = False,
    auxiliary_guard_sink: list[dict[str, str]] | None = None,
) -> list[dict[str, Any]]:
    """Build §3.8 reachability rows (§8.1 excluded from counted-call ledger).

    ``resource_monitor`` is accepted for API compatibility but ignored: reachability probes
    must not attach to the confirmatory audit monitor. Live identity-fallback observation
    runs only when ``include_live_ident_fallback_observation`` is True (implementation
    acceptance / pre-closure preflight). Child-process sealed-path attempts from that probe
    are appended to ``auxiliary_guard_sink`` when provided; otherwise any child attempt
    fail-closes before counted work.

    Fixture builders are error-isolated: an exception becomes a fail-closed row instead of
    aborting the audit process.
    """
    _ = resource_monitor
    builders: list[tuple[str, Any]] = [
        ("REACH-POW-COMP-1", _reach_pow_comp_1),
        ("REACH-SFN-1", _reach_sfn_1),
        ("REACH-PRESERVED-1", _reach_preserved_1),
        ("REACH-UNS-1", _reach_uns_1),
        ("REACH-SUP-1", _reach_sup_1),
        ("REACH-DRIFT-E2", _reach_drift_e2),
        ("REACH-Q4FAIL-1", _reach_q4fail_1),
        ("REACH-IDENT-FALLBACK-1", _reach_ident_fallback_1),
        ("REACH-PARSE-1", _reach_parse_1),
        ("REACH-RESCALE-1", _reach_rescale_1),
    ]
    return [
        _run_reachability_fixture(
            fixture_id,
            fn,
            include_live_ident_fallback_observation=include_live_ident_fallback_observation,
            auxiliary_guard_sink=auxiliary_guard_sink,
        )
        for fixture_id, fn in builders
    ]
