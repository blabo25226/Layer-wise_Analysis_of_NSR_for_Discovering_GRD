"""Tests for GPU_RUN4 Phases 2–9 helpers (CPU, no checkpoint)."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from gpu_run4.aggregation import student_t_ci, summarize_records
from gpu_run4.ranking_utils import rank_from_scores
from gpu_run4.trajectories import QUALITATIVE_PANEL_IDS, corrupt_trajectory, r2_score


def test_paired_corruption_is_seeded() -> None:
    times = np.linspace(0, 10, 40)
    traj = np.stack([np.sin(times), np.cos(times)], axis=1)
    a_t, a_y = corrupt_trajectory(times, traj, sigma=0.05, rho=0.5, seed=7)
    b_t, b_y = corrupt_trajectory(times, traj, sigma=0.05, rho=0.5, seed=7)
    assert a_t.shape == b_t.shape
    assert np.allclose(a_y, b_y)
    assert len(a_t) < len(times)


def test_r2_perfect_is_one() -> None:
    y = np.arange(12, dtype=float).reshape(6, 2)
    assert abs(r2_score(y, y) - 1.0) < 1e-9


def test_student_t_ci_n1_collapses() -> None:
    stats = student_t_ci([1.5])
    assert stats["n"] == 1
    assert stats["mean"] == 1.5
    assert stats["ci_low"] == stats["ci_high"]


def test_summarize_records_keeps_failures() -> None:
    rows = [
        {"valid": True, "reconstruction_r2": 0.95, "failure_reason": None},
        {"valid": False, "reconstruction_r2": None, "failure_reason": "ParseError"},
    ]
    out = summarize_records(rows, keys=("reconstruction_r2",))
    assert out["n"] == 2
    assert out["n_valid"] == 1
    assert out["failures"]["ParseError"] == 1


def test_rank_from_scores_puts_nan_last() -> None:
    ranked = rank_from_scores({"a": 0.2, "b": float("nan"), "c": 0.9}, higher_is_better=True)
    assert ranked[0] == "c"
    assert ranked[-1] == "b"


def test_qualitative_panel_ids_are_odebench() -> None:
    from gpu_run4_runtime import load_odebench_equations

    ids = {int(item["id"]) for item in load_odebench_equations()}
    assert set(QUALITATIVE_PANEL_IDS) <= ids


def test_phase_scripts_importable() -> None:
    sys.path.insert(0, str(ROOT / "scripts" / "phases"))
    for name in (
        "gpu_run4_phase2_repro",
        "gpu_run4_phase3_beam",
        "gpu_run4_phase4_corpus",
        "gpu_run4_phase5_observational",
        "gpu_run4_phase6_causal",
        "gpu_run4_phase7_iole",
        "gpu_run4_phase8_selective",
        "gpu_run4_phase9_final",
    ):
        module = __import__(name)
        assert callable(module.main)
