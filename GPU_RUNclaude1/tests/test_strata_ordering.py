"""Tests for the write-before-match integrity ordering (v2 §7.2 step 3, §14 item 8).

The component strata and the realized-|H| ladder must be written and hashed
to disk before any Part A match indicator is computed. This is enforced
mechanically by gpu_runclaude1.partA_driver.score_cell requiring a
StrataFrozenToken, obtainable only from require_strata_frozen.
"""

from __future__ import annotations

import json

import pytest

from gpu_runclaude1.ladder import build_ladder_realized_artifact
from gpu_runclaude1.matcher import score_pair
from gpu_runclaude1.partA_driver import demonstrate_timeout_inside_worker, score_cell, score_cells_parallel
from gpu_runclaude1.strata import (
    STRATUM_H,
    STRATUM_L,
    StrataIntegrityError,
    assign_strata,
    component_stratum,
    require_strata_frozen,
    write_component_strata,
)

# A tiny two-system, three-component synthetic corpus: a Hill/variable-
# denominator component (H) and two plain linear components (L).
SYNTHETIC_ROWS = [
    {
        "system_id": "SYS_A",
        "family": "FAM1",
        "dimension": 1,
        "teacher_components_infix": ["0.5 + 0.8 * x_0 * 1/(0.3 + x_0) + -1 * 0.2 * x_0"],
    },
    {
        "system_id": "SYS_B",
        "family": "FAM1",
        "dimension": 2,
        "teacher_components_infix": ["0.1 + -1 * 0.4 * x_0", "0.2 + -1 * 0.5 * x_1"],
    },
]


def _write_frozen_artifacts(tmp_path):
    records = assign_strata(SYNTHETIC_ROWS)
    strata_path = tmp_path / "component_strata.json"
    strata_payload = write_component_strata(strata_path, records)
    ladder_path = tmp_path / "partA_ladder_realized.json"
    ladder_payload = build_ladder_realized_artifact(strata_payload["n_h"], strata_payload["sha256_of_component_assignment"])
    ladder_path.write_text(json.dumps(ladder_payload, indent=2), encoding="utf-8")
    return strata_path, ladder_path, strata_payload


def test_component_stratum_classifies_hill_vs_linear():
    hill = "0.5 + 0.8 * x_0 * 1/(0.3 + x_0)"
    linear = "-1 * 0.4 * x_0"
    assert component_stratum(hill) == STRATUM_H
    assert component_stratum(linear) == STRATUM_L


def test_assign_strata_over_synthetic_corpus():
    records = assign_strata(SYNTHETIC_ROWS)
    assert len(records) == 3
    strata_by_key = {(r.system_id, r.component_index): r.stratum for r in records}
    assert strata_by_key[("SYS_A", 0)] == STRATUM_H
    assert strata_by_key[("SYS_B", 0)] == STRATUM_L
    assert strata_by_key[("SYS_B", 1)] == STRATUM_L


def test_score_cell_refuses_to_run_without_a_strata_token():
    fake_cell = {"true_formula": "x_0", "candidates": [{"candidate_formula_raw": "x_0"}]}
    with pytest.raises(TypeError):
        score_cell(fake_cell, strata_token=None)
    with pytest.raises(TypeError):
        score_cell(fake_cell, strata_token={"n_h": 1})  # a plain dict is not a StrataFrozenToken


def test_require_strata_frozen_raises_if_artifacts_are_missing(tmp_path):
    strata_path = tmp_path / "component_strata.json"
    ladder_path = tmp_path / "partA_ladder_realized.json"
    with pytest.raises(StrataIntegrityError):
        require_strata_frozen(strata_path, ladder_path)


def test_require_strata_frozen_raises_if_only_strata_written(tmp_path):
    records = assign_strata(SYNTHETIC_ROWS)
    strata_path = tmp_path / "component_strata.json"
    write_component_strata(strata_path, records)
    ladder_path = tmp_path / "partA_ladder_realized.json"  # never written
    with pytest.raises(StrataIntegrityError):
        require_strata_frozen(strata_path, ladder_path)


def test_require_strata_frozen_raises_if_strata_file_tampered_after_hashing(tmp_path):
    strata_path, ladder_path, _ = _write_frozen_artifacts(tmp_path)
    payload = json.loads(strata_path.read_text(encoding="utf-8"))
    payload["n_h"] = payload["n_h"] + 1  # tamper post-hoc, hash now stale
    strata_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    with pytest.raises(StrataIntegrityError):
        require_strata_frozen(strata_path, ladder_path)


def test_require_strata_frozen_raises_if_ladder_not_derived_from_this_strata_file(tmp_path):
    strata_path, ladder_path, _ = _write_frozen_artifacts(tmp_path)
    ladder_payload = json.loads(ladder_path.read_text(encoding="utf-8"))
    ladder_payload["sha256_of_component_strata_input"] = "0" * 64  # a different, unrelated hash
    ladder_path.write_text(json.dumps(ladder_payload, indent=2), encoding="utf-8")
    with pytest.raises(StrataIntegrityError):
        require_strata_frozen(strata_path, ladder_path)


def test_correctly_ordered_writes_unlock_matching(tmp_path):
    strata_path, ladder_path, strata_payload = _write_frozen_artifacts(tmp_path)
    token = require_strata_frozen(strata_path, ladder_path)
    assert token.n_h == strata_payload["n_h"]
    assert token.n_l == strata_payload["n_l"]
    assert token.component_lookup[("SYS_A", 0)] == STRATUM_H

    cell = {
        "true_formula": SYNTHETIC_ROWS[0]["teacher_components_infix"][0],
        "candidates": [{"candidate_formula_raw": SYNTHETIC_ROWS[0]["teacher_components_infix"][0]}],
    }
    results = score_cell(cell, token)  # does not raise: the token is genuine
    assert len(results) == 1
    assert results[0].m3_system == 1.0  # identity candidate must match under M3


def test_score_pair_itself_is_ungated_low_level_primitive():
    """score_pair is the pure per-pair primitive used by controls/tests and
    is intentionally NOT gated (the gate lives at partA_driver.score_cell,
    the entry point that runs over the *stored corpus*). This is documented
    behavior, verified here so the boundary does not drift silently.
    """
    result = score_pair("x_0", "x_0")
    assert result.m3_system == 1.0


def test_score_cells_parallel_also_requires_a_strata_token(tmp_path):
    with pytest.raises(TypeError):
        score_cells_parallel([{"true_formula": "x_0", "candidates": []}], strata_token=None)


def test_score_cells_parallel_matches_sequential_scoring(tmp_path):
    strata_path, ladder_path, _ = _write_frozen_artifacts(tmp_path)
    token = require_strata_frozen(strata_path, ladder_path)
    cells = [
        {"true_formula": SYNTHETIC_ROWS[0]["teacher_components_infix"][0], "candidates": [{"candidate_formula_raw": "x_0"}]},
        {"true_formula": SYNTHETIC_ROWS[1]["teacher_components_infix"][0], "candidates": [{"candidate_formula_raw": "x_0"}]},
    ]
    sequential = [score_cell(cell, token) for cell in cells]
    parallel = score_cells_parallel(cells, token, n_workers=2)
    assert len(parallel) == len(sequential)
    for seq_result, par_result in zip(sequential, parallel):
        assert seq_result[0].m3_system == par_result[0].m3_system
        assert seq_result[0].m0_system == par_result[0].m0_system


def test_timeout_fires_inside_a_worker_process_not_only_the_main_thread():
    """v2 §3: thread-based parallelism is forbidden because `_time_limit`
    silently no-ops off the main thread; process-based parallelism must be
    used instead because a worker *process* has its own genuine main
    thread, where the SIGALRM guard fires normally. This is the Gate 0 /
    Stage-6 smoke assertion v2 §10.1 item 7 requires.
    """
    result = demonstrate_timeout_inside_worker()
    assert result["ok"] is True
    assert result["triggered"] is True
    assert result["elapsed_sec"] < 2.0  # bounded by the 1s guard, not the 5s sleep it interrupted
