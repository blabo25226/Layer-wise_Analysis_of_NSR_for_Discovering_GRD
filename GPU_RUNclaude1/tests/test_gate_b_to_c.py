"""Gate B->C must be mechanical, not a matter of operator discipline.

v2.1 specifies that Part C is not run when Part A confirms a
matcher-attributable gain, and requires at least 30 in-support systems. The
supervisor found on 2026-09-09 that neither condition was implemented in
``gpu_runclaude1_c0001_phase3_partc.py``; these tests pin the fix.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

_SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "phases" / "gpu_runclaude1_c0001_phase3_partc.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("c0001_phase3", _SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def phase3():
    return _load_module()


def _write(run_root: Path, verdict: str | None, n_in_support: object) -> None:
    (run_root / "phase1").mkdir(parents=True, exist_ok=True)
    (run_root / "phase2").mkdir(parents=True, exist_ok=True)
    if verdict is not None:
        (run_root / "phase1" / "partA_endpoints.json").write_text(
            json.dumps({"primary": {"verdict": verdict}}), encoding="utf-8"
        )
    if n_in_support is not None:
        (run_root / "phase2" / "partB_in_support_systems.json").write_text(
            json.dumps({"n_in_support": n_in_support}), encoding="utf-8"
        )


def test_gate_passes_on_a_null_verdict_with_enough_in_support_systems(phase3, tmp_path):
    _write(tmp_path, "no_gain_observed_bound_only", 60)
    gate = phase3.gate_b_to_c(tmp_path)
    assert gate["ok"] is True
    assert gate["reasons"] == []
    assert gate["part_a_verdict"] == "no_gain_observed_bound_only"
    assert gate["n_in_support"] == 60


def test_gate_refuses_when_part_a_confirmed_a_gain(phase3, tmp_path):
    """A confirmed gain redirects the cycle to replication, so Part C must not run."""
    _write(tmp_path, "matcher_attributable_gain_confirmed", 60)
    gate = phase3.gate_b_to_c(tmp_path)
    assert gate["ok"] is False
    assert any("replication" in r for r in gate["reasons"])


def test_gate_allows_a_weak_gain(phase3, tmp_path):
    """weak_gain is a claim revision, not a redirection; Part C still runs."""
    _write(tmp_path, "weak_gain", 60)
    assert phase3.gate_b_to_c(tmp_path)["ok"] is True


def test_gate_refuses_below_the_power_floor(phase3, tmp_path):
    _write(tmp_path, "no_gain_observed_bound_only", phase3.PART_C_MIN_IN_SUPPORT - 1)
    gate = phase3.gate_b_to_c(tmp_path)
    assert gate["ok"] is False
    assert any("power floor" in r for r in gate["reasons"])


def test_gate_accepts_exactly_the_power_floor(phase3, tmp_path):
    _write(tmp_path, "no_gain_observed_bound_only", phase3.PART_C_MIN_IN_SUPPORT)
    assert phase3.gate_b_to_c(tmp_path)["ok"] is True


def test_missing_part_a_is_a_refusal_not_a_pass(phase3, tmp_path):
    """Part C must never run on the assumption that an unwritten gate would have passed."""
    _write(tmp_path, None, 60)
    gate = phase3.gate_b_to_c(tmp_path)
    assert gate["ok"] is False
    assert any("Part A endpoints missing" in r for r in gate["reasons"])


def test_missing_part_b_is_a_refusal_not_a_pass(phase3, tmp_path):
    _write(tmp_path, "no_gain_observed_bound_only", None)
    gate = phase3.gate_b_to_c(tmp_path)
    assert gate["ok"] is False
    assert any("in-support census missing" in r for r in gate["reasons"])


def test_both_missing_reports_both_reasons(phase3, tmp_path):
    gate = phase3.gate_b_to_c(tmp_path)
    assert gate["ok"] is False
    assert len(gate["reasons"]) == 2


def test_non_integer_in_support_is_a_refusal(phase3, tmp_path):
    _write(tmp_path, "no_gain_observed_bound_only", "sixty")
    gate = phase3.gate_b_to_c(tmp_path)
    assert gate["ok"] is False
    assert any("not an integer" in r for r in gate["reasons"])


# --- v2.1 Gate B->C item (i): "Part A is not undecidable" ------------------
#
# Supervisor finding 2026-09-09: an independent analysis established Part A's
# verdict of record is `undecidable` for the completed run
# (gpu_runclaude1_c0001_b731cdd) because the two-sided sensitivity analysis
# disagrees on the rung (`sensitivity_agrees: false`), yet the already-run
# Part C pass proceeded anyway -- `gate_b_to_c` implemented only the
# `matcher_attributable_gain_confirmed` refusal and never checked for
# `undecidable` at all. These tests pin that fix, plus item (ii)'s second
# half (in-support systems must show zero Part A component gains).


def _write_full(
    run_root: Path,
    *,
    verdict: str | None,
    sensitivity_agrees: bool | None,
    n_in_support: object,
    system_ids: list[str] | None,
    component_summary: list[dict] | None,
) -> None:
    (run_root / "phase1").mkdir(parents=True, exist_ok=True)
    (run_root / "phase2").mkdir(parents=True, exist_ok=True)
    if verdict is not None or sensitivity_agrees is not None:
        primary: dict = {}
        if verdict is not None:
            primary["verdict"] = verdict
        if sensitivity_agrees is not None:
            primary["sensitivity_agrees"] = sensitivity_agrees
        (run_root / "phase1" / "partA_endpoints.json").write_text(
            json.dumps({"primary": primary}), encoding="utf-8"
        )
    if n_in_support is not None:
        payload: dict = {"n_in_support": n_in_support}
        if system_ids is not None:
            payload["system_ids"] = system_ids
        (run_root / "phase2" / "partB_in_support_systems.json").write_text(
            json.dumps(payload), encoding="utf-8"
        )
    if component_summary is not None:
        (run_root / "phase1" / "partA_component_summary.json").write_text(
            json.dumps(component_summary), encoding="utf-8"
        )


def test_gate_refuses_when_sensitivity_disagrees_even_with_an_ordinary_verdict(phase3, tmp_path):
    """The bug: a stored ``verdict`` of an ordinary ladder rung with
    ``sensitivity_agrees: false`` beside it must still refuse -- v2.1 §10.3
    treats the disagreement itself as an ``undecidable`` criterion,
    independent of what the (possibly stale) ``verdict`` field says.
    """
    _write_full(
        tmp_path,
        verdict="no_gain_observed_bound_only",
        sensitivity_agrees=False,
        n_in_support=60,
        system_ids=None,
        component_summary=None,
    )
    gate = phase3.gate_b_to_c(tmp_path)
    assert gate["ok"] is False
    assert gate["part_a_verdict"] == "undecidable (two-sided sensitivity disagreement)"
    assert any("undecidable" in r for r in gate["reasons"])


def test_gate_passes_when_sensitivity_agrees_is_true(phase3, tmp_path):
    _write_full(
        tmp_path,
        verdict="no_gain_observed_bound_only",
        sensitivity_agrees=True,
        n_in_support=60,
        system_ids=None,
        component_summary=None,
    )
    gate = phase3.gate_b_to_c(tmp_path)
    assert gate["ok"] is True


def test_gate_refuses_an_explicit_undecidable_verdict_without_sensitivity_field(phase3, tmp_path):
    """Any ``undecidable`` verdict variant refuses, not only the
    sensitivity-disagreement path -- e.g. a PC4 failure.
    """
    _write_full(
        tmp_path,
        verdict="undecidable (gain indicator not demonstrated)",
        sensitivity_agrees=None,
        n_in_support=60,
        system_ids=None,
        component_summary=None,
    )
    gate = phase3.gate_b_to_c(tmp_path)
    assert gate["ok"] is False
    assert any("Gate B->C item (i)" in r for r in gate["reasons"])


def test_gate_refuses_when_component_summary_missing_but_system_ids_present(phase3, tmp_path):
    """Item (ii)'s second half needs the per-component gain data; a missing
    artifact is a refusal, never an assumed pass.
    """
    _write_full(
        tmp_path,
        verdict="no_gain_observed_bound_only",
        sensitivity_agrees=True,
        n_in_support=30,
        system_ids=["sys_a", "sys_b"],
        component_summary=None,
    )
    gate = phase3.gate_b_to_c(tmp_path)
    assert gate["ok"] is False
    assert any("component summary missing" in r for r in gate["reasons"])


def test_gate_refuses_when_an_in_support_system_has_a_nonzero_gain(phase3, tmp_path):
    _write_full(
        tmp_path,
        verdict="no_gain_observed_bound_only",
        sensitivity_agrees=True,
        n_in_support=30,
        system_ids=["sys_a", "sys_b"],
        component_summary=[
            {"system_id": "sys_a", "gain": 0},
            {"system_id": "sys_b", "gain": 1},
            {"system_id": "sys_out_of_support", "gain": 1},  # must not count: not in-support
        ],
    )
    gate = phase3.gate_b_to_c(tmp_path)
    assert gate["ok"] is False
    assert gate["component_gain_violations"] == ["sys_b"]
    assert any("Gate B->C item (ii)" in r for r in gate["reasons"])


def test_gate_passes_when_all_in_support_systems_have_zero_gain(phase3, tmp_path):
    _write_full(
        tmp_path,
        verdict="no_gain_observed_bound_only",
        sensitivity_agrees=True,
        n_in_support=30,
        system_ids=["sys_a", "sys_b"],
        component_summary=[
            {"system_id": "sys_a", "gain": 0},
            {"system_id": "sys_b", "gain": 0},
            {"system_id": "sys_b", "gain": 0},  # a second component, still zero
        ],
    )
    gate = phase3.gate_b_to_c(tmp_path)
    assert gate["ok"] is True
    assert gate["component_gain_violations"] == []
