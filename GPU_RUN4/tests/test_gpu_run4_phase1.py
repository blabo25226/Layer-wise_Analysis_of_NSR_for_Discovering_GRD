"""GPU_RUN4 Phase 1 tests: canonicalization, TED, component order, failures."""

from __future__ import annotations

import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from gpu_run4.formulas import (
    compare_formulas,
    evaluate_gold_cases,
    instantiate_odebench_item,
    numeric_equivalent,
    parse_system,
    singularity_probe,
    timeout_probe,
)
from gpu_run4.ted import TedTimeout, time_limit
from gpu_run4_runtime import load_odebench_equations


def test_commutative_add_is_canonical_exact() -> None:
    result = compare_formulas("x_0 + x_1", "x_1 + x_0")
    assert result["canonical_exact"] == 1.0
    assert result["symbolic_equivalent"] == 1.0
    assert result["ted_raw"] == 0.0
    assert result["normalized_ted"] == 0.0


def test_reciprocal_matches_division() -> None:
    result = compare_formulas("x_0 / x_1", "x_0 * (1 / x_1)")
    assert result["canonical_exact"] == 1.0
    assert result["symbolic_equivalent"] == 1.0


def test_negative_constant_matches_neg() -> None:
    result = compare_formulas("-x_0", "(-1) * x_0")
    assert result["canonical_exact"] == 1.0
    assert result["symbolic_equivalent"] == 1.0


def test_component_order_is_not_permuted() -> None:
    result = compare_formulas("x_0 | x_1", "x_1 | x_0")
    assert result["component_count_match"] is True
    assert result["canonical_exact"] == 0.0
    assert result["symbolic_equivalent"] == 0.0
    assert result["ted_raw"] > 0


def test_intentionally_different_formulas_do_not_match() -> None:
    result = compare_formulas("x_0 + x_1", "x_0 - x_1")
    assert result["canonical_exact"] == 0.0
    assert result["symbolic_equivalent"] == 0.0


def test_skeleton_ignores_numeric_constants() -> None:
    result = compare_formulas("2 * x_0", "3 * x_0")
    assert result["skeleton_exact"] == 1.0
    assert result["canonical_exact"] == 0.0
    assert result["symbolic_equivalent"] == 0.0


def test_parse_failure_is_recorded() -> None:
    result = compare_formulas("x_0", "this is not an ode )))")
    assert result["valid"] is False
    assert result["failure_reason"] == "ParseError"


def test_gold_suite_passes() -> None:
    rows = evaluate_gold_cases()
    failed = [row["name"] for row in rows if not row["ok"]]
    assert failed == []


def test_ted_timeout_guard() -> None:
    with pytest.raises(TedTimeout):
        with time_limit(0.05):
            time.sleep(1.0)
    probe = timeout_probe(seconds=0.05)
    assert probe["ok"] is True
    assert probe["failure_reason"] == "TEDTimeout"


def test_singularity_is_not_forced_equivalent() -> None:
    probe = singularity_probe()
    assert probe["ok"] is True
    assert probe["failure_reason"] in {"Inf", "NaN"}
    assert probe["equivalent"] is False


def test_numeric_finite_points_can_still_match() -> None:
    views = parse_system("x_0 + x_1")
    numeric = numeric_equivalent(views["components"], views["components"])
    assert numeric["equivalent"] is True
    assert numeric["finite_points"] > 0
    assert numeric["failure_reason"] is None


def test_odebench_true_equations_parse() -> None:
    equations = load_odebench_equations()
    assert len(equations) == 63
    failures = []
    for item in equations:
        parsed = instantiate_odebench_item(item)
        if not parsed["valid"]:
            failures.append((parsed["id"], parsed["failure_reason"], parsed["true_formula_raw"]))
        identity = compare_formulas(parsed["true_formula_instantiated"], parsed["true_formula_instantiated"])
        if parsed["valid"] and identity["canonical_exact"] != 1.0:
            failures.append((parsed["id"], "identity_ted", identity["ted_raw"]))
    assert failures == []


def test_phase1_script_importable() -> None:
    sys.path.insert(0, str(ROOT / "scripts" / "phases"))
    module = __import__("gpu_run4_phase1_eval")
    assert callable(module.main)
