from __future__ import annotations

import pytest

from scripts.phases.gpu_run5_phase5 import (
    _candidate_audit,
    _cell_identity,
    _coverage_audit,
    _decode_cell,
    _failure_funnel,
    _layer_effects,
    _paired_candidate_seed,
)


def _cell(condition: str, bundle: int, *, exact: float, ted: float, valid: float, gen: float):
    return {
        "system_id": "R01_validation_000",
        "bundle_index": bundle,
        "condition": condition,
        "dimension": 1,
        "n_candidates": 1,
        "beam_size": 50,
        "selected": {
            "valid": bool(valid),
            "failure_reason": None if valid else "ParseError",
            "component_exponent_aware_skeleton_exact": [exact],
            "component_normalized_variable_aware_ted": [ted],
            "component_valid": [bool(valid)],
        },
        "trajectory_metrics": {"generalization_r2_failure_aware": [gen]},
    }


def test_layer_effects_are_paired_and_support_zero_method_without_ce() -> None:
    cells = [
        _cell("baseline", 0, exact=1, ted=0, valid=1, gen=0.8),
        _cell("interpolation:encoder_0", 0, exact=0, ted=1, valid=0, gen=-10),
    ]
    ce = [
        {"system_id": "R01_validation_000", "condition": "baseline", "layer": None, "ce": 1.0},
        {"system_id": "R01_validation_000", "condition": "interpolation", "layer": "encoder_0", "ce": 1.4},
    ]
    effect = _layer_effects(cells, ce, ["encoder_0"])["encoder_0"]
    assert effect["damage_ce"] == pytest.approx(0.4)
    assert effect["component_exact_loss"] == 1.0
    assert effect["failure_aware_ted_increase"] == 1.0
    assert effect["component_valid_loss"] == 1.0
    assert effect["generalization_r2_loss"] == pytest.approx(10.8)

    zero = [cells[0], _cell("zero:encoder_0", 0, exact=0, ted=0.5, valid=1, gen=0.0)]
    zero_effect = _layer_effects(
        zero, ce, ["encoder_0"], condition_method="zero", include_ce=False
    )["encoder_0"]
    assert zero_effect["damage_ce"] is None
    assert zero_effect["failure_aware_ted_increase"] == 0.5


def test_failure_funnel_retains_invalid_and_shortfall_cells() -> None:
    rows = [
        _cell("baseline", 0, exact=1, ted=0, valid=1, gen=1),
        _cell("baseline", 1, exact=0, ted=1, valid=0, gen=-10),
    ]
    rows[1]["n_candidates"] = 0
    result = _failure_funnel(rows)
    assert result["n_cells"] == 2
    assert result["empty_beam"] == 1
    assert result["beam_shortfall"] == 2
    assert result["selected_valid_rate"] == 0.5
    assert result["selected_failure_reasons"]["ParseError"] == 1


def test_coverage_audit_rejects_duplicate_or_wrong_beam(monkeypatch) -> None:
    row = {
        "system_id": "R01_validation_000",
        "trajectories": [{"role": "input", "role_index": 0, "checksum": "input-hash"}],
    }
    monkeypatch.setattr(
        "scripts.phases.gpu_run5_phase5._paired_candidate_seed", lambda *_args: 123
    )
    cell = {
        "system_id": row["system_id"], "bundle_index": 0, "condition": "baseline",
        "candidate_seed": 123, "beam_size": 50, "input_trajectory_checksum": "input-hash",
    }
    good = _coverage_audit(
        [cell], [row], ["baseline"], n_bundles=1, beam_size=50, config={}
    )
    assert good["pass"] is True
    duplicate = _coverage_audit(
        [cell, cell], [row], ["baseline"], n_bundles=1, beam_size=50, config={}
    )
    assert duplicate["pass"] is False
    wrong_beam = _coverage_audit(
        [{**cell, "beam_size": 8}], [row], ["baseline"],
        n_bundles=1, beam_size=50, config={},
    )
    assert wrong_beam["pass"] is False


def test_candidate_audit_recomputes_ordered_formula_hash() -> None:
    from scripts.phases.gpu_run5_phase5 import _candidate_hash

    candidates = [
        {"candidate_index": 0, "candidate_formula_raw": "x_0",
         "candidate_formula_canonical": "x_0", "candidate_exponent_aware_skeleton": "x_0",
         "valid": True, "failure_reason": None},
        {"candidate_index": 1, "candidate_formula_raw": "",
         "candidate_formula_canonical": "", "candidate_exponent_aware_skeleton": "",
         "valid": False, "failure_reason": "ParseError"},
    ]
    cell = {
        "n_candidates": 2, "candidates": candidates,
        "candidate_set_hash": _candidate_hash(["x_0", ""]),
    }
    assert _candidate_audit([cell], candidates)["pass"] is True
    cell["candidate_set_hash"] = "wrong"
    assert _candidate_audit([cell], candidates)["pass"] is False


def test_decode_cell_records_generation_failure_but_reraises_oom(monkeypatch) -> None:
    row = {
        "system_id": "R01_validation_000", "family": "R01", "dimension": 1,
        "teacher_infix": "x_0", "teacher_prefix": "x_0", "tree_encoded": ["x_0"],
        "variable_to_gene": {"x_0": "gene_0"},
        "trajectories": [
            {"role": "input", "role_index": 0, "checksum": "in", "times": [0, 1],
             "trajectory": [[1.0], [1.0]], "initial_condition": [1.0]},
            {"role": "generalization", "role_index": 0, "checksum": "gen", "times": [0, 1],
             "trajectory": [[1.0], [1.0]], "initial_condition": [1.0]},
        ],
    }
    config = {"seed_bundles": [{"candidate_seed": 31}]}
    seed = _paired_candidate_seed(row, config, 0)
    identity = _cell_identity({"beam_size": 8}, row, 0, "baseline", seed)

    def fail(*_args, **_kwargs):
        raise ValueError("decode failed")

    monkeypatch.setattr("scripts.phases.gpu_run5_phase5._decode_infixes", fail)
    cell = _decode_cell(
        row, model=object(), config=config, means={}, alpha=1.0, condition="baseline",
        bundle_index=0, beam_size=8, r2_penalty=-10, nrmse_penalty=10,
        cache_identity=identity,
    )
    assert cell["n_candidates"] == 0
    assert cell["generation_failure"] == "ValueError:decode failed"
    assert cell["selected"]["failure_reason"] == "ValueError:decode failed"

    def oom(*_args, **_kwargs):
        import torch
        raise torch.cuda.OutOfMemoryError("CUDA out of memory")

    monkeypatch.setattr("scripts.phases.gpu_run5_phase5._decode_infixes", oom)
    import torch
    with pytest.raises(torch.cuda.OutOfMemoryError):
        _decode_cell(
            row, model=object(), config=config, means={}, alpha=1.0, condition="baseline",
            bundle_index=0, beam_size=8, r2_penalty=-10, nrmse_penalty=10,
            cache_identity=identity,
        )
