from __future__ import annotations

import copy

import numpy as np
import pytest
import torch

from gpu_run5.training import (
    adapt_input_training_records,
    apply_delta_checkpoint,
    deterministic_random_layer_sets,
    formula_score_vector,
    load_delta_checkpoint,
    make_delta_checkpoint,
    model_state_sha256,
    pairwise_rank_stability,
    rank_correlations,
    save_delta_checkpoint,
    select_formula_candidate,
    tie_aware_vector_ranking,
    train_adam_with_snapshots,
    training_order,
)


def _grn_record(name: str, value: float) -> dict:
    trajectory = [[value], [value + 1.0]]
    return {
        "system_id": name,
        "tree_encoded": ["add", "x_0", "1"],
        "trajectories": [
            {"role": "selection", "role_index": 0, "times": [0, 1], "trajectory": [[99], [99]]},
            {"role": "input", "role_index": 0, "times": [0, 1], "trajectory": trajectory, "checksum": name},
            {"role": "generalization", "role_index": 0, "times": [0, 1], "trajectory": [[88], [88]]},
        ],
    }


def test_input_adapter_and_order_are_condition_independent() -> None:
    source = [_grn_record("b", 2.0), _grn_record("a", 1.0)]
    adapted = adapt_input_training_records(source)
    assert [row["record_id"] for row in adapted] == ["a", "b"]
    assert adapted[0]["source_role"] == "input"
    assert np.asarray(adapted[0]["trajectory"])[:, 0].tolist() == [1.0, 2.0]

    first = training_order(adapted, steps=9, seed=101)
    second = training_order(adapt_input_training_records(list(reversed(source))), steps=9, seed=101)
    assert first["record_ids"] == second["record_ids"]
    assert first["order_sha256"] == second["order_sha256"]
    assert training_order(adapted, steps=9, seed=202)["order_sha256"] != first["order_sha256"]
    changed = adapt_input_training_records([_grn_record("a", 7.0), _grn_record("b", 2.0)])
    assert training_order(changed, steps=9, seed=101)["order_sha256"] != first["order_sha256"]

    invalid = _grn_record("bad", 0.0)
    invalid["trajectories"] = [item for item in invalid["trajectories"] if item["role"] != "input"]
    with pytest.raises(ValueError, match="exactly one input"):
        adapt_input_training_records([invalid])


class _ToyRegressor(torch.nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.linear = torch.nn.Linear(1, 1)

    def forward(self, value: torch.Tensor) -> torch.Tensor:
        return self.linear(value)


def _configure_all(model: torch.nn.Module, _layers) -> None:
    for parameter in model.parameters():
        parameter.requires_grad = True


def _toy_loss(model: _ToyRegressor, row: dict) -> torch.Tensor:
    x = torch.tensor([[float(row["trajectory"][0, 0])]], dtype=torch.float32)
    target = 2.0 * x
    return torch.mean((model(x) - target) ** 2)


def test_adam_snapshots_are_exact_and_nonfinite_is_visible() -> None:
    records = [_grn_record("a", 1.0), _grn_record("b", 2.0)]
    torch.manual_seed(9)
    first_model = _ToyRegressor()
    initial = copy.deepcopy(first_model.state_dict())
    result = train_adam_with_snapshots(
        first_model,
        records,
        trainable_layers=None,
        lr=0.01,
        max_steps=7,
        snapshot_steps=(2, 4, 7),
        data_order_seed=101,
        model_seed=7,
        loss_fn=_toy_loss,
        configure_trainable=_configure_all,
    )
    assert result["status"] == "complete"
    assert result["snapshot_steps_completed"] == [2, 4, 7]
    assert len(result["losses"]) == 7
    assert result["determinism"] == {
        "deterministic_algorithms": True,
        "cudnn_benchmark": False,
        "cudnn_deterministic": True,
        "cublas_workspace_config": ":4096:8",
    }
    assert len(result["training_corpus_sha256"]) == 64
    assert not torch.equal(result["snapshots"][2]["linear.weight"], result["snapshots"][7]["linear.weight"])

    second_model = _ToyRegressor()
    second_model.load_state_dict(initial)
    second = train_adam_with_snapshots(
        second_model,
        records,
        trainable_layers=None,
        lr=0.01,
        max_steps=7,
        snapshot_steps=(2, 4, 7),
        data_order_seed=101,
        model_seed=7,
        loss_fn=_toy_loss,
        configure_trainable=_configure_all,
    )
    assert second["order_sha256"] == result["order_sha256"]
    assert torch.equal(second["snapshots"][7]["linear.weight"], result["snapshots"][7]["linear.weight"])

    calls = 0

    def exploding_loss(model, row):
        nonlocal calls
        calls += 1
        return torch.tensor(float("nan"), requires_grad=True) if calls == 3 else _toy_loss(model, row)

    failed_model = _ToyRegressor()
    failed = train_adam_with_snapshots(
        failed_model,
        records,
        trainable_layers=None,
        lr=0.01,
        max_steps=5,
        snapshot_steps=(2, 5),
        data_order_seed=101,
        model_seed=7,
        loss_fn=exploding_loss,
        configure_trainable=_configure_all,
    )
    assert failed["status"] == "failed"
    assert failed["failure_reason"] == "NonFiniteLoss"
    assert failed["completed_steps"] == 2
    assert failed["snapshot_steps_completed"] == [2]
    with pytest.raises(ValueError, match="snapshot_callback"):
        train_adam_with_snapshots(
            _ToyRegressor(), records, trainable_layers=None, lr=0.01,
            max_steps=2, snapshot_steps=(2,), data_order_seed=1, model_seed=1,
            loss_fn=_toy_loss, configure_trainable=_configure_all,
            keep_snapshots=False,
        )


def test_delta_checkpoint_allowlist_hash_and_output_roundtrip(tmp_path) -> None:
    torch.manual_seed(4)
    base = _ToyRegressor()
    adapted = copy.deepcopy(base)
    for parameter in adapted.parameters():
        parameter.requires_grad = True
    with torch.no_grad():
        adapted.linear.weight.add_(0.5)
        adapted.linear.bias.sub_(0.25)
    keys = sorted(name for name, parameter in adapted.named_parameters() if parameter.requires_grad)
    identity = {"base_checkpoint_sha256": "abc", "condition": "toy"}
    base_sha = model_state_sha256(base)
    payload = make_delta_checkpoint(
        adapted,
        allowed_parameter_keys=keys,
        identity=identity,
        trainable_layers=None,
        base_model_state_sha256=base_sha,
    )
    path = tmp_path / "delta.pt"
    saved = save_delta_checkpoint(path, payload)
    loaded = load_delta_checkpoint(path, expected_file_sha256=saved["file_sha256"])

    restored = copy.deepcopy(base)
    apply_delta_checkpoint(
        restored,
        loaded,
        allowed_parameter_keys=keys,
        expected_identity=identity,
    )
    x = torch.tensor([[1.5]])
    assert torch.equal(restored(x), adapted(x))

    tampered = copy.deepcopy(loaded)
    tampered["parameter_state"][keys[0]] = tampered["parameter_state"][keys[0]] + 1
    with pytest.raises(ValueError, match="tensor hash"):
        apply_delta_checkpoint(
            copy.deepcopy(base), tampered,
            allowed_parameter_keys=keys, expected_identity=identity,
        )
    with pytest.raises(ValueError, match="allowlist"):
        apply_delta_checkpoint(
            copy.deepcopy(base), loaded,
            allowed_parameter_keys=keys[:-1], expected_identity=identity,
        )
    wrong_base = copy.deepcopy(base)
    with torch.no_grad():
        wrong_base.linear.weight.add_(1.0)
    with pytest.raises(ValueError, match="base model state mismatch"):
        apply_delta_checkpoint(
            wrong_base, loaded, allowed_parameter_keys=keys, expected_identity=identity
        )
    metadata_tampered = copy.deepcopy(loaded)
    metadata_tampered["trainable_layers"] = ["not_the_saved_condition"]
    with pytest.raises(ValueError, match="metadata hash"):
        apply_delta_checkpoint(
            copy.deepcopy(base),
            metadata_tampered,
            allowed_parameter_keys=keys,
            expected_identity=identity,
        )


def _score_row(system: str, seed: int, exact: float, ted: float, valid: bool) -> dict:
    return {
        "system_id": system,
        "bundle_index": seed,
        "dimension": 1,
        "component_exponent_aware_skeleton_exact": [exact],
        "component_normalized_variable_aware_ted": [ted],
        "component_valid": [valid],
    }


def test_formula_score_is_failure_aware_macro_and_ce_is_last_tie_break() -> None:
    rows = [
        _score_row("a", 0, 1, 0.0, True),
        _score_row("a", 0, 0, 0.2, True),
        _score_row("b", 0, 1, 0.0, True),
        _score_row("a", 1, 1, 0.0, True),
        _score_row("b", 1, 1, 0.0, False),  # supplied exact/TED are penalized by invalid
    ]
    for index, row in enumerate(rows):
        row["cell_id"] = f"cell-{index}"
    vector = formula_score_vector(
        rows, validation_ce=2.0,
        expected_cell_ids=[f"cell-{index}" for index in range(len(rows))],
    )
    assert vector == pytest.approx((0.625, -0.275, 0.75, -2.0))
    ce_rows = [
        {**_score_row("a", 0, 1, 0, True), "ce": 1.0},
        {**_score_row("a", 0, 1, 0, True), "ce": 3.0},
        {**_score_row("b", 0, 1, 0, True), "ce": 6.0},
        {**_score_row("a", 1, 1, 0, True), "ce": 2.0},
        {**_score_row("b", 1, 1, 0, True), "ce": 4.0},
    ]
    # seed0: ((1+3)/2 + 6)/2 = 4; seed1: (2+4)/2 = 3; macro seed CE = 3.5
    for index, row in enumerate(ce_rows):
        row["cell_id"] = f"ce-{index}"
    assert formula_score_vector(
        ce_rows, expected_cell_ids=[f"ce-{index}" for index in range(len(ce_rows))]
    )[-1] == pytest.approx(-3.5)

    with pytest.raises(ValueError, match="coverage mismatch"):
        formula_score_vector(rows[:-1], validation_ce=2.0, expected_cell_ids=[f"cell-{index}" for index in range(len(rows))])

    trial_identity = {
        "condition": "full", "view": "main", "bundle_indices": [0],
        "base_model_state_sha256": "base", "training_corpus_sha256": "corpus",
        "training_order_sha256": "order", "validation_panel_sha256": "panel",
        "model_seed": 0, "candidate_seed_map_sha256": "decode-seeds",
    }
    candidates = []
    for index, (lr, steps) in enumerate(
        (lr, steps) for lr in (1e-6, 1e-5, 1e-4) for steps in (50, 200, 1000)
    ):
        candidates.append({
            "config": {"lr": lr, "steps": steps}, "status": "complete",
            "validation_cell_ids": ["a:0", "b:0"],
            "trial_identity": trial_identity,
            "score_vector": [0.0, -0.5, 1.0, -float(9 - index)],
        })
    candidates[0]["score_vector"] = [0.1, -1.0, 0.0, -1000.0]
    selected = select_formula_candidate(candidates, expected_validation_cell_ids=["a:0", "b:0"])
    assert selected["selected_index"] == 0  # exact beats every later metric
    assert len(selected["trials"]) == 9
    assert sum(row["selected"] for row in selected["trials"]) == 1

    tied = copy.deepcopy(candidates)
    for index, row in enumerate(tied):
        row["score_vector"] = [0.0, -0.5, 1.0, -float(9 - index)]
    assert select_formula_candidate(tied, expected_validation_cell_ids=["a:0", "b:0"])["selected_index"] == 8  # CE breaks the full tie

    reversed_selection = select_formula_candidate(list(reversed(candidates)), expected_validation_cell_ids=["a:0", "b:0"])
    assert reversed_selection["selected"]["config"] == selected["selected"]["config"]
    missing = copy.deepcopy(candidates)
    missing[-1]["validation_cell_ids"] = ["a:0"]
    with pytest.raises(ValueError, match="validation coverage mismatch"):
        select_formula_candidate(missing, expected_validation_cell_ids=["a:0", "b:0"])
    duplicate = copy.deepcopy(candidates)
    duplicate[-1]["config"] = dict(duplicate[0]["config"])
    with pytest.raises(ValueError, match="duplicate hyperparameter"):
        select_formula_candidate(duplicate, expected_validation_cell_ids=["a:0", "b:0"])

    near_tie = copy.deepcopy(tied)
    near_tie[0]["score_vector"][0] = 4e-13
    quantized = select_formula_candidate(near_tie, expected_validation_cell_ids=["a:0", "b:0"])
    assert quantized["selected_index"] == 8

    all_failed = copy.deepcopy(candidates)
    for row in all_failed:
        row["status"] = "failed"
        row["failure_reason"] = "NonFiniteLoss"
        row["validation_cell_ids"] = []
        row["score_vector"] = [0.0, -1.0, 0.0, -float("inf")]
    with pytest.raises(ValueError, match="all hyperparameter candidates failed"):
        select_formula_candidate(all_failed, expected_validation_cell_ids=["a:0", "b:0"])

    invalid_score = copy.deepcopy(candidates)
    invalid_score[0]["score_vector"] = [float("inf"), 0.0, 1.0, 0.0]
    with pytest.raises(ValueError, match="outside its valid range"):
        select_formula_candidate(invalid_score, expected_validation_cell_ids=["a:0", "b:0"])

    unpaired = copy.deepcopy(candidates)
    unpaired[-1]["trial_identity"] = {
        **unpaired[-1]["trial_identity"], "model_seed": 9999,
    }
    with pytest.raises(ValueError, match="trial identity is not paired"):
        select_formula_candidate(unpaired, expected_validation_cell_ids=["a:0", "b:0"])


def test_random_sets_are_deterministic_distinct_and_may_overlap() -> None:
    layers = [f"encoder_{index}" for index in range(4)] + [f"decoder_{index}" for index in range(12)]
    first = deterministic_random_layer_sets(layers)
    second = deterministic_random_layer_sets(list(reversed(layers)))
    assert first == second
    assert len(first) == len({tuple(values) for values in first}) == 5
    assert all(len(values) == len(set(values)) == 3 for values in first)
    assert any(set(left) & set(right) for i, left in enumerate(first) for right in first[i + 1 :])
    with pytest.raises(ValueError, match="frozen 16-layer registry"):
        deterministic_random_layer_sets(layers[:-1])


def test_tie_aware_ranks_and_constant_stability_are_not_spurious() -> None:
    ranking = tie_aware_vector_ranking(
        {"b": [1.0, 0.0], "a": [1.0, 4e-13], "c": [0.5, 1.0]}
    )
    assert ranking["ranking"][:2] == ["a", "b"]
    assert ranking["rows"][0]["tie_group"] == ranking["rows"][1]["tie_group"]
    assert ranking["rows"][0]["average_rank"] == ranking["rows"][1]["average_rank"] == 1.5

    constant = rank_correlations({"a": 1.0, "b": 1.0}, {"a": 1.0, "b": 2.0})
    assert constant["spearman"] is None
    assert constant["kendall_tau_b"] is None
    assert constant["reason"] == "constant_rank"

    stable = pairwise_rank_stability(
        {
            0: {"a": [2.0], "b": [1.0], "c": [0.0]},
            1: {"a": [2.0], "b": [1.0], "c": [0.0]},
            2: {"a": [0.0], "b": [1.0], "c": [2.0]},
        }
    )
    assert len(stable["pairs"]) == 3
    assert stable["pairs"][0]["spearman"] == pytest.approx(1.0)
    assert any(row["spearman"] == pytest.approx(-1.0) for row in stable["pairs"])
    with pytest.raises(ValueError, match="identical layer registry"):
        pairwise_rank_stability({0: {"a": [1.0], "b": [0.0]}, 1: {"a": [1.0]}})
