"""GPU_RUN3 unit tests for TED, records, and phase CLI wiring."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from gpu_run3.records import GPU_RUN3_REQUIRED_FIELDS, dummy_formula_record, missing_required_fields
from gpu_run3.ted import prefix_to_tree, ted_metrics
from gpu_run3.cli import common_parser
from gpu_run3.formulas import compare_formulas, parse_to_prefix


def test_formula_record_schema() -> None:
    record = dummy_formula_record("unit")
    assert missing_required_fields(record) == []
    assert GPU_RUN3_REQUIRED_FIELDS <= set(record)
    assert record["campaign"] == "GPU_RUN3"


def test_ted_identical_and_commutative_add() -> None:
    left = ["add", "x", "omega"]
    right = ["add", "omega", "x"]
    metrics = ted_metrics(left, right)
    assert metrics["failure_reason"] is None
    assert metrics["ted_raw"] == 0.0
    assert metrics["exact"] == 1.0


def test_ted_parse_failure_is_recorded() -> None:
    metrics = ted_metrics(["add", "x"], ["this_token_is_not_a_complete_tree", "???"])
    assert metrics["failure_reason"] == "TEDParseError"
    assert metrics["ted_raw"] != metrics["ted_raw"]  # NaN


def test_kuramoto_prefix_roundtrip() -> None:
    prefix = parse_to_prefix("omega + aggr(sin(sour(x)-targ(x)))")
    assert prefix[0] == "add"
    assert "aggr" in prefix and "sour" in prefix and "targ" in prefix
    comparison = compare_formulas(prefix, prefix)
    assert comparison["exact"] == 1.0
    assert comparison["ted_raw"] == 0.0


def test_phase_cli_flags() -> None:
    parser = common_parser("unit")
    args = parser.parse_args(["--dry-run", "--smoke", "--allow-cpu", "--run-id", "x"])
    assert args.dry_run and args.smoke and args.allow_cpu
    assert args.run_id == "x"


def test_phase_scripts_importable() -> None:
    root = ROOT / "scripts" / "phases"
    names = [
        "gpu_run3_phase0_preflight",
        "gpu_run3_phase1_policy",
        "gpu_run3_phase2_pipeline",
        "gpu_run3_phase3_benchmark",
        "gpu_run3_phase4_probes",
        "gpu_run3_phase5_decoderlens",
        "gpu_run3_phase6_causal",
        "gpu_run3_phase7_selective_ft",
        "gpu_run3_phase8_test",
        "gpu_run3_phase9_pretrain_dist",
    ]
    sys.path.insert(0, str(root))
    for name in names:
        __import__(name)
